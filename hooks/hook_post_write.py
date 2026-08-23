"""
Post-write hook for agent-native file edit tools — submit substantive edits as
Claims to the local consensus gateway and kick off a detached background
consensus round.

Invoked with hook JSON on stdin from surfaces such as:
    - Claude Code `PostToolUse` on `Write|Edit|MultiEdit`
    - Gemini CLI `AfterTool` on `write_file|replace`

Fast path (< 100 ms wall-clock):
    1. Parse stdin JSON (swallow errors)
    2. Path filter — only packages/**/*.{py,rs,toml}; skip tests/, __pycache__/
    3. Construct a Claim and submit it via GatewayTools (local file write)
    4. Spawn a DETACHED subprocess to run the consensus round in the background
    5. Log to FLOSS_AGENT_DIR/hook.log and exit 0

Guarantees:
    - Never blocks the user: exits 0 on every failure path
    - Never recurses: edits to scripts/ (including this file) are skipped
      by the path filter, so installing the hook can't trigger the hook
    - Never burns free-tier budget on routine work: the path filter is
      intentionally narrow — broaden only when we're sure we want voters
      to evaluate edits in a given directory

Spec-gate advisory (D7, adopted 2026-06-12): before the substantive filter,
mutating writes into gated surfaces (scripts/, docs/specs/, docs/adr/) get a
read-only registry check via spec_gate.advisory_note(); unregistered artifacts
surface a warning in the hook log and stdout-JSON additionalContext. Advisory
only — it submits nothing, spawns nothing, and never blocks.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
LOG_FILE = AGENT_DIR / "hook.log"
PRE_WRITE_CHECKPOINT_DIR = AGENT_DIR / "checkpoints" / "pre_write"
EMIT_STDOUT_JSON = "--stdout-json" in sys.argv[1:]

# Substantive = worth burning a consensus round on. Intentionally narrow.
#
# Two rule sets, because code and canon are substantive for different reasons.
# CODE: implementation under packages/. CANON: the three surfaces where a
# markdown/JSON edit changes what the project claims to be true — the same
# surfaces spec_gate gates. Prose elsewhere (docs/research, intake_raw, notes)
# stays out: it is pre-spec by definition and would drown the gateway.
#
# Added 2026-08-10. Before this, the 2026-08-10 root-consolidation pass made
# ~40 edits to the kernel, INDEX, ADRs, specs and manifests and fired the hook
# exactly ONCE, on the single .py file it touched. Canon drift was structurally
# invisible to the provenance spine.
SUBSTANTIVE_PATH_SEGMENTS = ("/packages/",)
SUBSTANTIVE_EXTENSIONS = (".py", ".rs", ".toml")

CANON_PATH_SEGMENTS = ("/docs/adr/", "/docs/specs/", "/docs/governance/")
CANON_EXTENSIONS = (".md", ".json")

# Even within substantive paths, skip these — they're routine noise.
SKIP_SEGMENTS = ("/tests/", "/__pycache__/", "/.venv/", "/venv/", "/archive/")
MUTATING_TOOL_NAMES = {
    # Claude Code
    "write",
    "edit",
    "multiedit",
    # Gemini
    "write_file",
    "replace",
    # Hermes. `patch` is Hermes's own file-editing tool name -- the hook
    # manifest matches `write_file|patch` for both Hermes events and was
    # confirmed against tools/file_tools.py -- but it was missing here, so every
    # Hermes patch returned immediately at is_mutating_tool(): no checkpoint, no
    # Claim, while `hermes hooks list` reported the hook installed and allowed.
    # An installed hook that silently does nothing is worse than an absent one.
    "patch",
}


def log(msg: str) -> None:
    """Best-effort append to the hook log. Never raises."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass  # logging must never break the hook


_HOOK_CONTEXT: list[str] = []


def finish() -> int:
    """Exit helper for agent CLIs that require a JSON response on stdout."""
    if EMIT_STDOUT_JSON:
        try:
            if _HOOK_CONTEXT:
                sys.stdout.write(
                    json.dumps(
                        {
                            "hookSpecificOutput": {
                                "hookEventName": "PostToolUse",
                                "additionalContext": "\n".join(_HOOK_CONTEXT),
                            }
                        }
                    )
                    + "\n"
                )
            else:
                sys.stdout.write("{}\n")
            sys.stdout.flush()
        except Exception:
            pass
    return 0


def _is_inside_repo(path_str: str) -> bool:
    """Only edits within THIS checkout may become Claims.

    The `claude_user` hook target installs this hook at user scope, so it runs
    for every Claude project on the machine -- not just this one. The path
    predicate matched on segments alone, so editing `/other-project/packages/
    foo.py` in an unrelated repository was judged substantive and submitted that
    project's path, plus bounded source snippets, into FLOSS's DURABLE Claim
    chain, and opened a consensus round on it.

    A permanent, append-only provenance chain is exactly the wrong place to
    discover a cross-project leak, so containment is checked before anything
    else. Relative paths resolve against the current directory, which is the
    project the hook actually fired in.
    """
    try:
        candidate = Path(path_str).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve()
        root = REPO_ROOT.resolve()
    except (OSError, ValueError):
        return False
    return resolved == root or root in resolved.parents


def is_substantive(path_str: str) -> bool:
    """True if this edit is worth submitting as a Claim.

    Either it is implementation code under packages/, or it is a markdown/JSON
    edit on one of the three canon surfaces (adr, specs, governance). Anything
    on an intake mouth — docs/research, intake_raw, agent-memory — is excluded
    by SKIP_SEGMENTS and by not matching either rule set.
    """
    if not path_str:
        return False
    if not _is_inside_repo(path_str):
        return False
    norm = "/" + path_str.replace("\\", "/").lstrip("/").lower()
    if any(skip in norm for skip in SKIP_SEGMENTS):
        return False
    if norm.endswith(SUBSTANTIVE_EXTENSIONS) and any(
        part in norm for part in SUBSTANTIVE_PATH_SEGMENTS
    ):
        return True
    if norm.endswith(CANON_EXTENSIONS) and any(
        part in norm for part in CANON_PATH_SEGMENTS
    ):
        return True
    return False


# Surface -> (proposal_type, blast_radius).
#
# Before this, EVERY substantive write was submitted as a CodeChange at Local.
# Local's approve threshold is 0.30; Module is 0.50 and System 0.60. So once the
# 2026-08-10 audit widened the hook to include canon surfaces, an ADR or a spec
# edit became eligible for approval at the routine-code-change bar -- a
# governance outcome that reads as legitimate and is not.
#
# Deliberately NOT mapping anything to Substrate. Substrate is override-forbidden
# at 0.85 and is for invariant-touching changes; assigning it by path alone would
# be a guess with a very expensive failure mode.
CANON_CLAIM_CLASS: tuple[tuple[str, str, str], ...] = (
    ("/docs/adr/", "AdrChange", "System"),
    ("/docs/governance/", "SpecChange", "System"),
    ("/docs/specs/", "SpecChange", "Module"),
)
GOVERNED_TYPES = frozenset({"SpecChange", "ConfigChange", "AdrChange"})
GOVERNED_RADII = frozenset({"System", "Substrate"})


def classify_change(path_str: str) -> tuple[str, str]:
    """Return (proposal_type, blast_radius) for a written path.

    Code keeps CodeChange/Local. Canon surfaces get the class their content
    actually is, so the gateway applies the threshold that matches the risk.
    """
    norm = "/" + (path_str or "").replace("\\", "/").lstrip("/").lower()
    for segment, proposal_type, radius in CANON_CLAIM_CLASS:
        if segment in norm:
            return proposal_type, radius
    return "CodeChange", "Local"


def is_mutating_tool(tool_name: str) -> bool:
    """True if the hook fired for a file-modifying tool we want to inspect."""
    return (tool_name or "").strip().lower() in MUTATING_TOOL_NAMES


def infer_surface(tool_name: str, hook_event_name: str) -> str:
    """Best-effort origin label for the claim proposer."""
    tn = (tool_name or "").strip().lower()
    event_name = (hook_event_name or "").strip()
    if tn in {"write", "edit", "multiedit"}:
        return "claude-code"
    if tn in {"write_file", "replace"} or event_name == "AfterTool":
        return "gemini-cli"
    return "agent-tool"


# Character budget per side of an edit or per Write body. Chosen so that
# a full 3-voter round on a typical edit still fits comfortably inside the
# context window of the 8B–32B models we're using AND inside Claim.body
# without being so tiny that voters can't actually see what changed.
_MAX_CHANGE_CHARS = 1500


def _trim(text: str, limit: int = _MAX_CHANGE_CHARS) -> str:
    """Truncate a block to `limit` chars with a visible marker when cut."""
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, {len(text) - limit} more chars]"


def _render_change_section(tool_name: str, tool_input: dict) -> str:
    """Build a human-readable description of the actual change.

    For Edit: show old_string → new_string (the two sides of the diff).
    For MultiEdit: show each sub-edit's before/after in order.
    For Write: show the new file content.

    Everything is bounded by `_MAX_CHANGE_CHARS` per side so a single huge
    edit can't blow out the Claim body or the voter prompt.
    """
    tn = (tool_name or "").lower()

    if tn in {"edit", "replace"}:
        old = _trim(tool_input.get("old_string", "") or "")
        new = _trim(tool_input.get("new_string", "") or "")
        return (
            f"CHANGE ({tool_name}):\n"
            "--- old ---\n"
            f"{old}\n"
            "--- new ---\n"
            f"{new}"
        )

    if tn == "multiedit":
        edits = tool_input.get("edits") or []
        if not isinstance(edits, list) or not edits:
            return "CHANGE (MultiEdit): <no edits>"
        parts = [f"CHANGE (MultiEdit, {len(edits)} sub-edits):"]
        # Cap to first 5 sub-edits to keep the Claim body bounded; a single
        # MultiEdit with 30 changes shouldn't eat 30 × 1500 chars.
        for idx, e in enumerate(edits[:5], start=1):
            old = _trim(e.get("old_string", "") or "", limit=600)
            new = _trim(e.get("new_string", "") or "", limit=600)
            parts.append(f"-- sub-edit {idx} old --\n{old}")
            parts.append(f"-- sub-edit {idx} new --\n{new}")
        if len(edits) > 5:
            parts.append(f"... [{len(edits) - 5} more sub-edits omitted]")
        return "\n".join(parts)

    if tn in {"write", "write_file"}:
        content = _trim(tool_input.get("content", "") or "")
        return f"CHANGE ({tool_name} — full new file content):\n" + content

    # Unknown tool — fall back to a serialized tool_input so voters at
    # least see *something* rather than a bare filename.
    try:
        serialized = json.dumps(tool_input, indent=2, default=str)
    except Exception:  # noqa: BLE001
        serialized = str(tool_input)
    return f"CHANGE ({tool_name}):\n" + _trim(serialized)


def spawn_background_round(claim_id: str, edit_note: str = "") -> None:
    """Fire-and-forget subprocess to run the consensus round.

    On Windows uses DETACHED_PROCESS + CREATE_NO_WINDOW so the child lives
    past the hook's exit and doesn't flash a console window. On POSIX we
    use start_new_session to detach from the hook's process group.

    `edit_note` (optional, may be empty) is a terse, already-bounded
    description of the accepted edit. It rides along as argv[2] purely so
    the DETACHED child (hook_bg_round.py) can record it to agentmemory on
    its own time -- this function itself makes no memory call and adds no
    measurable latency to the synchronous fast path: it's just one more
    string in a Popen argv list.
    """
    bg_script = REPO_ROOT / "hooks" / "hook_bg_round.py"
    if not bg_script.exists():
        log(f"[hook] bg script missing: {bg_script}")
        return
    try:
        kwargs: dict = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
            )
        else:
            kwargs["start_new_session"] = True
        argv = [sys.executable, str(bg_script), claim_id]
        if edit_note:
            argv.append(edit_note)
        subprocess.Popen(
            argv,
            **kwargs,
        )
        log(f"[hook] spawned bg round for {claim_id}")
    except Exception as exc:  # noqa: BLE001
        log(f"[hook] bg spawn failed for {claim_id}: {type(exc).__name__}: {exc}")


def main() -> int:
    try:
        payload_raw = sys.stdin.read()
        payload = json.loads(payload_raw) if payload_raw.strip() else {}
    except Exception as exc:  # noqa: BLE001
        log(f"[hook] stdin parse error: {exc}")
        return finish()

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("filePath")
        or tool_input.get("path")
        or tool_input.get("target_file")
        or ""
    )

    if not is_mutating_tool(tool_name):
        return finish()

    # Spec-gate advisory (D7): runs BEFORE the substantive filter because
    # scripts/ and docs/{specs,adr}/ are exactly the surfaces that filter
    # skips. Read-only registry lookup; advisory only; never raises.
    try:
        _scripts_dir = str(REPO_ROOT / "scripts")
        if _scripts_dir not in sys.path:
            sys.path.insert(0, _scripts_dir)
        from spec_gate import advisory_note

        _note = advisory_note(file_path)
        if _note:
            log(f"[spec-gate] {_note}")
            _HOOK_CONTEXT.append(_note)
    except Exception:  # noqa: BLE001 — advisory must never break the hook
        pass

    if not is_substantive(file_path):
        # Uncomment for verbose debugging:
        # log(f"[hook] skip {tool_name} {file_path}")
        return finish()

    # Lazy import — only reached for substantive paths, so cold-start cost
    # is paid on exactly the edits that warrant it.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    try:
        from packages.metacoordinator_mcp.hashline import (
            claim_pre_write_checkpoint,
            render_verification_section,
            verify_tool_edit,
        )
        from packages.metacoordinator_mcp.tools import GatewayTools
    except Exception:  # noqa: BLE001
        log(f"[hook] GatewayTools import failed:\n{traceback.format_exc()}")
        return finish()

    try:
        dna_hash = os.environ.get("FLOSS_DNA_HASH", "0" * 64)
        gw = GatewayTools(
            base_dir=AGENT_DIR,
            dna_hash=dna_hash,
            workspace_root=REPO_ROOT.parent,
        )
    except Exception:  # noqa: BLE001
        log(f"[hook] GatewayTools init failed:\n{traceback.format_exc()}")
        return finish()

    rel_path = file_path
    try:
        rel_path = str(Path(file_path).resolve().relative_to(REPO_ROOT.resolve()))
    except (ValueError, OSError):
        pass

    # Include the actual change in the body so voters have something real to
    # evaluate. Without this, voters get the filename and nothing else and
    # correctly abstain (0.0) because there is no content to judge — the
    # whole round becomes meaningless audit noise.
    change_section = _render_change_section(tool_name, tool_input)
    pre_checkpoint = claim_pre_write_checkpoint(
        PRE_WRITE_CHECKPOINT_DIR, file_path, tool_name, tool_input
    )
    verification = verify_tool_edit(
        file_path,
        tool_name,
        tool_input,
        pre_checkpoint=pre_checkpoint,
    )
    verification_section = render_verification_section(verification)
    surface = infer_surface(tool_name, payload.get("hook_event_name", ""))
    log(
        f"[hook] verification {verification.get('status', 'UNKNOWN')} "
        f"{rel_path}: {verification.get('reason', 'no reason')}"
    )
    if pre_checkpoint:
        log(
            f"[hook] checkpoint {pre_checkpoint.get('signature', 'unknown')} consumed for {rel_path}"
        )
    else:
        log(f"[hook] no pre-write checkpoint for {rel_path}")

    summary = (
        f"{surface}:{tool_name}:{verification.get('status', 'UNKNOWN').lower()} "
        f"→ {Path(file_path).name}"
    )[:200]
    body = (
        f"Auto-Claim from {surface} post-write hook.\n"
        f"Hook Event: {payload.get('hook_event_name', 'PostToolUse')}\n"
        f"Tool:       {tool_name}\n"
        f"Path:       {rel_path}\n"
        f"\n"
        f"{change_section}\n"
        f"\n"
        f"{verification_section}\n"
        f"\n"
        f"Evaluate whether the change preserves module invariants, matches "
        f"existing conventions in the surrounding code, and carries no "
        f"obvious security or correctness risks. Treat a verification status "
        f"other than VERIFIED as a trust reduction signal for later automation. "
        f"Blast radius is Local — the hook never auto-escalates."
    )

    evidence: list[dict] = []
    try:
        # Deferred here (not in the GatewayTools import block above) so that on
        # lean installs without the provenance extras (blake3/jcs/nacl) the
        # ImportError is caught locally and the hook still submits the Local
        # CodeChange claim with empty evidence — provenance packets are
        # best-effort and Local claims don't require them.
        from packages.activity_log import provenance

        edited_path = Path(file_path).resolve()
        if edited_path.exists():
            packet_entry = {
                "claim_type": "CodeChange",
                "truth_status": "specified",
                "source_systems": [surface, "hook_post_write.py"],
                "created_at": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "human_collision_node": os.environ.get(
                    "FLOSS_HUMAN_COLLISION_NODE", "local-operator"
                ),
                "artifact_refs": [
                    provenance.artifact_ref(
                        edited_path,
                        workspace_root=REPO_ROOT.parent,
                    )
                ],
                "evidence_refs": [
                    {
                        "type": "test",
                        "ref": f"hashline:{verification.get('status', 'UNKNOWN')}",
                    }
                ],
                "risks": [],
                "benefits": [],
                "next_action": "submit local code-change claim",
            }
            packet, packet_path = provenance.create_packet(
                [packet_entry],
                identity_dir=AGENT_DIR / "identity",
                output_root=REPO_ROOT.parent / ".agent-surface" / "provenance",
            )
            evidence.append(
                {
                    "type": "provenance_packet",
                    "ref": packet_path.resolve()
                    .relative_to(REPO_ROOT.parent.resolve())
                    .as_posix(),
                    "sha256": provenance.sha256_file(packet_path),
                }
            )
            log(f"[hook] provenance packet {packet['d']} for {rel_path}")
    except Exception as exc:  # noqa: BLE001
        log(
            f"[hook] provenance packet failed for {rel_path}: "
            f"{type(exc).__name__}: {exc}"
        )

    proposal_type, blast_radius = classify_change(rel_path)
    if (
        proposal_type in GOVERNED_TYPES
        and blast_radius in GOVERNED_RADII
        and not evidence
    ):
        # The gateway fails these closed with E_GOVERNED_PROVENANCE_REQUIRED.
        # Say so plainly instead of quietly downgrading the radius to make the
        # submit succeed -- a canon edit approved at the Local 0.30 bar is
        # exactly the misleading governance outcome this classification exists
        # to prevent. A refused claim is the correct outcome here.
        log(
            f"[hook] {rel_path} is {proposal_type}/{blast_radius} but no "
            "provenance packet was attached; the gateway will refuse this "
            "claim (E_GOVERNED_PROVENANCE_REQUIRED). Check the packet failure "
            "logged above."
        )

    try:
        result_str = gw.submit_claim(
            proposer=f"{surface}-hook",
            proposal_type=proposal_type,
            summary=summary,
            body=body,
            blast_radius=blast_radius,
            evidence=evidence,
        )
        result = json.loads(result_str)
    except Exception:  # noqa: BLE001
        log(f"[hook] submit_claim crashed:\n{traceback.format_exc()}")
        return finish()

    if "error" in result:
        log(f"[hook] submit_claim error for {rel_path}: {result['error']}")
        return finish()

    claim_id = result.get("claim_id", "")
    log(f"[hook] claimed {rel_path} → {claim_id}")

    # `summary` is already a terse, bounded (<=200 char) description of this
    # accepted substantive edit -- pass it through to the DETACHED bg round
    # so it can record a memory observation on its own time. This function
    # (hook_post_write's synchronous fast path) makes no agentmemory call
    # itself; see hook_bg_round.py for where the actual save happens.
    spawn_background_round(claim_id, summary)
    return finish()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — absolute last-resort guard
        log(f"[hook] top-level crash:\n{traceback.format_exc()}")
        sys.exit(finish())
