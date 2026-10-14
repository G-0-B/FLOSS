"""Throwaway probes of Codex's app-server protocol (draft spec Q1 to Q6), 2026-10-14.

Run at the operator's request ("yes run the probes on a throwaway session").

What it does, and nothing else:
- starts its own `codex app-server` over stdio, in a temporary git repository;
- lists threads only to count them (no titles, previews, names, paths or cwds are logged);
- creates ONE new thread, names it as a probe, runs at most three tiny turns in it
  (a one-word reply, a detached review of a one-line change, one queued message);
- refuses every approval or input request the server sends;
- archives the thread(s) it created, stops its server, removes the temporary repository.

It never resumes, reads or writes any other session.
Output: <out>/transcript.jsonl (JSON-RPC, redacted for listings), <out>/summary.json.
"""

from __future__ import annotations

import collections
import json
import pathlib
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid

CODEX = r"C:\Program Files\WindowsApps\OpenAI.Codex_26.1007.9446.0_x64__2p2nqsd0c76g0\app\resources\codex.exe"
OUT = pathlib.Path(sys.argv[1])
STEPS = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else {"q1", "q2", "q3", "q4"}
OUT.mkdir(parents=True, exist_ok=True)
TRANSCRIPT = open(OUT / "transcript.jsonl", "w", encoding="utf-8")
SUMMARY: dict = {"started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
LISTING_METHODS = {"thread/list", "thread/loaded/list"}


def log(direction: str, msg) -> None:
    TRANSCRIPT.write(json.dumps({"t": round(time.time(), 3), "dir": direction, "msg": msg}) + "\n")
    TRANSCRIPT.flush()


def redact_listing(result: dict) -> dict:
    """Keep only what the probe needs from a listing: counts, statuses, sources, originators."""
    rows = result.get("data", []) if isinstance(result, dict) else []
    out = []
    for row in rows:
        if isinstance(row, dict):
            out.append({
                "id": str(row.get("id", ""))[:8] + "...",
                "status": (row.get("status") or {}).get("type") if isinstance(row.get("status"), dict) else row.get("status"),
                "source": row.get("source") if not isinstance(row.get("source"), dict) else row["source"].get("type", "object"),
                "originator": row.get("originator"),
                "ephemeral": row.get("ephemeral"),
            })
        else:
            out.append({"id": str(row)[:8] + "..."})
    return {"data": out, "redacted": True}


class _Skip(Exception):
    pass


class Client:
    def __init__(self, cwd: str):
        self.proc = subprocess.Popen(
            [CODEX, "app-server"], cwd=cwd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=open(OUT / "server-stderr.txt", "w", encoding="utf-8"),
            text=True, encoding="utf-8", bufsize=1,
        )
        self.next_id = 1
        self.pending: dict[int, queue.Queue] = {}
        self.methods: dict[int, str] = {}
        self.notes: list[dict] = []
        self.notes_lock = threading.Condition()
        self.refused: list[dict] = []
        threading.Thread(target=self._read, daemon=True).start()

    def _send(self, msg: dict) -> None:
        log("out", msg)
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _read(self) -> None:
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                log("in-raw", line[:2000])
                continue
            if "id" in msg and ("result" in msg or "error" in msg) and "method" not in msg:
                method = self.methods.pop(msg["id"], "")
                log("in", {**msg, "result": redact_listing(msg.get("result"))} if method in LISTING_METHODS else msg)
                box = self.pending.pop(msg["id"], None)
                if box:
                    box.put(msg)
            elif "id" in msg and "method" in msg:
                log("in", msg)
                self._refuse(msg)
            else:
                log("in", msg)
                with self.notes_lock:
                    self.notes.append(msg)
                    self.notes_lock.notify_all()

    def _refuse(self, req: dict) -> None:
        """Every server request is answered with a refusal. There is no accepting path."""
        method = req["method"]
        refusals = {
            "item/commandExecution/requestApproval": {"decision": "decline"},
            "item/fileChange/requestApproval": {"decision": "decline"},
            "mcpServer/elicitation/request": {"action": "decline"},
        }
        if method in refusals:
            reply = {"jsonrpc": "2.0", "id": req["id"], "result": refusals[method]}
        else:
            reply = {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32000, "message": "refused by the FLOSS probe client"}}
        self.refused.append({"method": method, "reply": reply.get("result") or "error"})
        self._send(reply)

    def call(self, method: str, params: dict, timeout: float = 60.0) -> dict:
        rid = self.next_id
        self.next_id += 1
        box: queue.Queue = queue.Queue()
        self.pending[rid] = box
        self.methods[rid] = method
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        try:
            msg = box.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(f"{method}: no reply in {timeout}s")
        if "error" in msg:
            raise RuntimeError(f"{method}: {json.dumps(msg['error'])[:500]}")
        return msg["result"]

    def notify(self, method: str, params: dict | None = None) -> None:
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def wait(self, pred, timeout: float, start: int = 0):
        deadline = time.time() + timeout
        with self.notes_lock:
            while True:
                for i in range(start, len(self.notes)):
                    if pred(self.notes[i]):
                        return i, self.notes[i]
                left = deadline - time.time()
                if left <= 0:
                    return None, None
                self.notes_lock.wait(timeout=min(left, 1.0))

    def notes_since(self, start: int) -> list[dict]:
        with self.notes_lock:
            return list(self.notes[start:])

    def close(self) -> None:
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def agent_text(notes: list[dict], turn_id: str) -> str:
    texts = []
    for n in notes:
        if n.get("method") == "item/completed" and n["params"].get("turnId") == turn_id:
            item = n["params"].get("item", {})
            if item.get("type") == "agentMessage":
                texts.append(str(item.get("text", "")))
    return "\n".join(texts)


def run_turn(c: Client, thread_id: str, params: dict, label: str, timeout: float = 240.0) -> dict:
    mark = len(c.notes)
    started = c.call("turn/start", {"threadId": thread_id, **params})
    turn_id = started["turn"]["id"]
    _, done = c.wait(lambda m: m.get("method") == "turn/completed" and m["params"]["turn"]["id"] == turn_id, timeout, mark)
    seen = c.notes_since(mark)
    return {
        "label": label,
        "turn_id": turn_id,
        "status": done["params"]["turn"]["status"] if done else "no turn/completed in time",
        "answer": agent_text(seen, turn_id)[:500],
        "settings_notifications": [n["params"].get("threadSettings") for n in seen if n.get("method") == "thread/settings/updated"],
        "methods_seen": sorted(collections.Counter(n.get("method") for n in seen).items()),
    }


def git(repo: str, *args: str) -> None:
    subprocess.run(["git", "-C", repo, "-c", "user.name=probe", "-c", "user.email=probe@example.invalid", *args],
                   check=True, capture_output=True)


def main() -> None:
    SUMMARY["codex_version"] = subprocess.run([CODEX, "--version"], capture_output=True, text=True).stdout.strip()
    repo = tempfile.mkdtemp(prefix="floss-codex-probe-")
    created: list[str] = []
    c = Client(repo)
    try:
        pathlib.Path(repo, "probe.txt").write_text("one\n", encoding="utf-8")
        git(repo, "init", "-q")
        git(repo, "add", "probe.txt")
        git(repo, "commit", "-q", "-m", "probe: initial")
        pathlib.Path(repo, "probe.txt").write_text("one\ntwo\n", encoding="utf-8")   # an uncommitted change to review

        init = c.call("initialize", {"clientInfo": {"name": "floss-probe", "title": "FLOSS throwaway probe", "version": "0.1"}})
        c.notify("initialized")
        SUMMARY["initialize_keys"] = sorted(init.keys()) if isinstance(init, dict) else str(type(init))

        # Q1: what does a separate app-server see of other sessions?
        listing = c.call("thread/list", {"limit": 50})
        rows = redact_listing(listing)["data"]
        loaded = c.call("thread/loaded/list", {})
        SUMMARY["q1"] = {
            "thread_list_count_first_page": len(rows),
            "more_pages": bool(listing.get("nextCursor")),
            "statuses": dict(collections.Counter(str(r.get("status")) for r in rows)),
            "sources": dict(collections.Counter(str(r.get("source")) for r in rows)),
            "originators": dict(collections.Counter(str(r.get("originator")) for r in rows)),
            "loaded_in_this_server_before": len(loaded.get("data", [])),
        }

        # The throwaway thread. Base settings deliberately differ from the per-turn ones (Q2).
        started = c.call("thread/start", {
            "cwd": repo, "sandbox": "workspace-write", "approvalPolicy": "on-request", "approvalsReviewer": "user",
            "ephemeral": False,
            "developerInstructions": "This thread is a throwaway protocol probe. Do not run commands or edit files. Answer in one word.",
        })
        tid = started["thread"]["id"]
        created.append(tid)
        c.call("thread/name/set", {"threadId": tid, "name": "FLOSS throwaway probe 2026-10-14 (safe to archive)"})
        SUMMARY["throwaway"] = {
            "thread_id": tid,
            "start_response_settings": {k: started.get(k) for k in ("approvalPolicy", "approvalsReviewer", "sandbox", "model")},
            "history_mode": started["thread"].get("historyMode"),
        }
        after_loaded = c.call("thread/loaded/list", {})
        SUMMARY["q1"]["loaded_in_this_server_after_start"] = len(after_loaded.get("data", []))

        # Q2: do per-turn sandbox and approval settings stay on the thread?
        if "q2" in STEPS:
            try:
                t1 = run_turn(c, tid, {
                    "input": [{"type": "text", "text": "Reply with exactly the word PONG and nothing else.", "text_elements": []}],
                    "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
                    "approvalPolicy": "never", "approvalsReviewer": "user",
                    "clientUserMessageId": str(uuid.uuid4()),
                }, "q2-turn")
                resumed = c.call("thread/resume", {"threadId": tid, "excludeTurns": True})
                SUMMARY["q2"] = {
                    "turn": t1,
                    "settings_after_turn_via_resume": {k: resumed.get(k) for k in ("approvalPolicy", "approvalsReviewer", "sandbox")},
                }
            except Exception as exc:
                SUMMARY["q2"] = {"error": f"{type(exc).__name__}: {exc}"}

        # Q3: what does a review do to the target thread? Detached first, then inline.
        if "q3" in STEPS:
            SUMMARY["q3"] = {}
            for delivery in ("detached", "inline"):
                try:
                    before = len(c.call("thread/read", {"threadId": tid, "includeTurns": True})["thread"]["turns"])
                    mark = len(c.notes)
                    review = c.call("review/start", {"threadId": tid, "target": {"type": "uncommittedChanges"}, "delivery": delivery})
                    review_tid, review_turn = review["reviewThreadId"], review["turn"]["id"]
                    if review_tid != tid and review_tid not in created:
                        created.append(review_tid)
                    _, done = c.wait(lambda m: m.get("method") == "turn/completed" and m["params"]["turn"]["id"] == review_turn, 300, mark)
                    seen = c.notes_since(mark)
                    after = len(c.call("thread/read", {"threadId": tid, "includeTurns": True})["thread"]["turns"])
                    SUMMARY["q3"][delivery] = {
                        "review_thread_is_separate": review_tid != tid,
                        "review_status": done["params"]["turn"]["status"] if done else "no turn/completed in time",
                        "original_thread_turns_before": before,
                        "original_thread_turns_after": after,
                        "review_output_preview": agent_text(seen, review_turn)[:400],
                        "thread_started_notifications": sum(1 for n in seen if n.get("method") == "thread/started"),
                        "methods_seen": sorted(collections.Counter(n.get("method") for n in seen).items()),
                    }
                    break   # one completed review is enough
                except Exception as exc:
                    SUMMARY["q3"][delivery] = {"error": f"{type(exc).__name__}: {exc}"}

        # Q4: does `codex queue` reach a thread that another app-server has loaded and idle?
        if "q4" in STEPS:
            try:
                mark = len(c.notes)
                q = subprocess.run([CODEX, "queue", "--thread", tid, "--message", "Reply with exactly the word QUEUED and nothing else."],
                                   capture_output=True, text=True, timeout=90, cwd=repo)
                _, qchanged = c.wait(lambda m: m.get("method") == "thread/queue/changed" and m["params"].get("threadId") == tid, 60, mark)
                _, qturn = c.wait(lambda m: m.get("method") == "turn/started" and m["params"].get("threadId") == tid, 60, mark)
                qdone = None
                if qturn:
                    qid = qturn["params"]["turn"]["id"]
                    _, qdone = c.wait(lambda m: m.get("method") == "turn/completed" and m["params"]["turn"]["id"] == qid, 180, mark)
                seen = c.notes_since(mark)
                SUMMARY["q4"] = {
                    "cli_exit": q.returncode,
                    "cli_stdout_tail": q.stdout[-600:],
                    "cli_stderr_tail": q.stderr[-600:],
                    "queue_changed_seen_by_loading_server": bool(qchanged),
                    "turn_started_by_queue": bool(qturn),
                    "queued_turn_status": qdone["params"]["turn"]["status"] if qdone else None,
                    "queued_answer": agent_text(seen, qturn["params"]["turn"]["id"])[:200] if qturn else None,
                    "methods_seen": sorted(collections.Counter(n.get("method") for n in seen).items()),
                }
            except Exception as exc:
                SUMMARY["q4"] = {"error": f"{type(exc).__name__}: {exc}"}
    except Exception as exc:  # record and fall through to cleanup
        SUMMARY["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        archived = {}
        for thread_id in created:
            try:
                c.call("thread/archive", {"threadId": thread_id})
                archived[thread_id] = "archived"
            except Exception as exc:
                archived[thread_id] = f"archive failed: {exc}"
        SUMMARY["cleanup"] = {"archived": archived, "approval_or_input_requests_refused": c.refused}
        c.close()
        shutil.rmtree(repo, ignore_errors=True)
        SUMMARY["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        (OUT / "summary.json").write_text(json.dumps(SUMMARY, indent=2), encoding="utf-8")
        TRANSCRIPT.close()
        print(json.dumps(SUMMARY, indent=2)[:6000])


if __name__ == "__main__":
    main()
