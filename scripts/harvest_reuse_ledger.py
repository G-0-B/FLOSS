"""
Reuse-Ledger Harvest Primer — delegate per-fork research to Gemini CLI.

This is the operational implementation of the External FLOSS Harvest task
(working-todo §A.5). One subprocess invocation = one ledger-entry-draft, written
to a staging directory under .agent-surface/harvest/staging/ for human review
BEFORE integration into FLOSS/docs/research/reuse-ledger-seed.yaml.

Plane A only:
  - Writes only to .agent-surface/harvest/staging/ (review queue)
  - Never modifies the canonical reuse-ledger directly
  - Human steward gates promotion of any draft to the ledger
  - Honors the same intake doctrine as the heartbeat (filter-through-not-out)

Per CLAUDE.md doc-budget discipline: single file at FLOSS/scripts/, no new docs.
Per plan §1 evidence gate: every harvested entry must include all 5 gate fields
(license, adapter_test, provenance, rollback, contact) populated explicitly.
Per plan §9 anti-pattern guard: do not run this faster than humans can triage.

Usage:
    # One fork at a time (recommended):
    python FLOSS/scripts/harvest_reuse_ledger.py https://github.com/owner/repo

    # By (owner, repo) pair:
    python FLOSS/scripts/harvest_reuse_ledger.py --owner tinyhumansai --repo openhuman

    # With explicit candidate-id (else: next available 0016+):
    python FLOSS/scripts/harvest_reuse_ledger.py --id 0016 https://github.com/owner/repo

    # Dry-run (assemble prompt + print, do not invoke gemini):
    python FLOSS/scripts/harvest_reuse_ledger.py --dry-run https://github.com/owner/repo

Outputs:
    .agent-surface/harvest/staging/<id>_<owner>_<repo>_draft.yaml
    .agent-surface/harvest/staging/<id>_<owner>_<repo>_provenance.json

Exit codes:
    0  draft written
    1  configuration error (no gemini CLI, no gh CLI, no network)
    2  gemini subprocess failed
    3  output validation failed (response not parseable as ledger entry)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
HARVEST_DIR = WORKSPACE_ROOT / ".agent-surface" / "harvest"
STAGING_DIR = HARVEST_DIR / "staging"
ACTIVITY_LOG = HARVEST_DIR / "activity.jsonl"  # append-only, durable, future-agent-readable
LEDGER_FILE = REPO_ROOT / "docs" / "research" / "reuse-ledger-seed.yaml"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import Action, append_action  # noqa: E402


def _safe_id_part(value: object) -> str:
    text = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-") or "unknown"


def _emit_harvest_action(entry: dict) -> None:
    """Tee terminal harvest events into the global Action log."""
    event_type = entry.get("event")
    if event_type not in {"harvest_success", "harvest_fail"}:
        return

    timestamp = str(entry.get("timestamp", utc_iso()))
    try:
        duration = float(entry.get("duration_seconds", 0.0) or 0.0)
    except (TypeError, ValueError):
        duration = 0.0

    success = event_type == "harvest_success"
    draft_path = entry.get("draft_path")
    staging_paths = [str(draft_path)] if draft_path else []
    append_action(Action(
        action_id=(
            f"harvest-{_safe_id_part(entry.get('entry_id'))}-"
            f"{_safe_id_part(entry.get('target'))}"
        ),
        kind="harvest_review",
        harness="harvest_reuse_ledger.py",
        started_at=timestamp,
        ended_at=timestamp,
        duration_seconds=round(duration, 3),
        success=success,
        inputs={
            "target": entry.get("target"),
            "entry_id": entry.get("entry_id"),
            "model": entry.get("model"),
            "url": entry.get("url"),
        },
        outputs={
            "event": event_type,
            "draft_path": draft_path,
            "license_from_metadata": entry.get("license_from_metadata"),
            "reason": entry.get("reason"),
            "gemini_rc": entry.get("gemini_rc"),
            "validation_error": entry.get("validation_error"),
        },
        llm_calls=[{
            "model": entry.get("model", GEMINI_MODEL),
            "provider": "gemini-cli",
            "prompt_hash": "",
            "response_hash": "",
            "duration_seconds": duration,
            "error": None if success else entry.get("reason"),
        }],
        provenance_path=entry.get("provenance_path"),
        staging_paths=staging_paths,
        error=None if success else str(entry.get("reason", event_type)),
    ))


def append_activity(event_type: str, **fields) -> None:
    """Append-only activity log. One JSON object per line. Survives sessions.

    Purpose: durable cross-agent provenance trail. Any future agent (human, AI,
    hybrid) can `cat activity.jsonl | jq` to reconstruct what was harvested,
    when, by what model, with what outcome — without depending on session
    transcripts or chat-trail visibility.

    Never raises — logging failure must not break the actual work.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        **fields,
    }
    try:
        HARVEST_DIR.mkdir(parents=True, exist_ok=True)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
    _emit_harvest_action(entry)

# Per-invocation budget. Gemini Pro subscription handles this comfortably; the
# bound is human triage capacity, not provider quota. Anti-accumulation guard:
# do not run this faster than entries close gates.
#
# Model ID note (2026-05-17): Gemini 3.1 Pro hit GA on 2026-02-19 under id
# `gemini-3.1-pro`. However, gemini-cli v0.38.2 (current at writing) still uses
# the preview endpoint `gemini-3.1-pro-preview` — the GA id 404s on this CLI
# version. When the CLI updates to a version that knows the GA id, override via
# `FLOSS_HARVEST_GEMINI_MODEL=gemini-3.1-pro`. Free-tier fallbacks:
# `gemini-3.1-flash-lite` (free on AI Studio) or `gemini-2.5-flash` (legacy free).
GEMINI_MODEL = os.environ.get("FLOSS_HARVEST_GEMINI_MODEL", "gemini-3.1-pro-preview")
GEMINI_TIMEOUT_SECONDS = 180


@dataclass
class ForkTarget:
    owner: str
    repo: str
    url: str

    @property
    def slug(self) -> str:
        return f"{self.owner}_{self.repo}".lower().replace("-", "_")


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_url(url: str) -> ForkTarget:
    """Parse a GitHub URL into (owner, repo). Accepts:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      git@github.com:owner/repo.git
      owner/repo
    """
    if "/" in url and "://" not in url and "@" not in url:
        parts = url.strip().split("/")
        if len(parts) == 2:
            return ForkTarget(parts[0], parts[1], f"https://github.com/{url.strip()}")
    if url.startswith("git@"):
        match = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", url)
        if match:
            return ForkTarget(match.group(1), match.group(2),
                              f"https://github.com/{match.group(1)}/{match.group(2)}")
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2:
        repo = parts[1].removesuffix(".git")
        return ForkTarget(parts[0], repo,
                          f"https://github.com/{parts[0]}/{repo}")
    raise ValueError(f"Could not parse GitHub URL: {url}")


def check_prereqs() -> None:
    """Verify gh + gemini CLIs are on PATH. Bail with exit 1 if not."""
    missing = [tool for tool in ("gh", "gemini") if shutil.which(tool) is None]
    if missing:
        print(f"ERROR: missing CLI tools on PATH: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def fetch_upstream_metadata(target: ForkTarget) -> dict:
    """Use `gh api` to fetch upstream repo metadata. License, primary lang, etc."""
    fields = ("name,description,license,stargazers_count,forks_count,"
              "pushed_at,language,topics,homepage,default_branch,size")
    cmd = ["gh", "api", f"repos/{target.owner}/{target.repo}",
           "--jq", "{name, description, license: .license.spdx_id, "
                   "stars: .stargazers_count, forks: .forks_count, "
                   "pushed_at, language, topics, homepage}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    if proc.returncode != 0:
        print(f"WARN: gh api failed for {target.owner}/{target.repo}: {proc.stderr}",
              file=sys.stderr)
        return {"error": proc.stderr.strip()}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": "non-json response", "raw": proc.stdout[:500]}


def fetch_upstream_readme(target: ForkTarget, max_chars: int = 8000) -> str:
    """Best-effort README fetch — base64-decoded, truncated. Empty string on failure."""
    cmd = ["gh", "api", f"repos/{target.owner}/{target.repo}/readme",
           "--jq", ".content"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return ""
    try:
        import base64
        decoded = base64.b64decode(proc.stdout.strip()).decode("utf-8", errors="replace")
        return decoded[:max_chars]
    except Exception:
        return ""


PROMPT_TEMPLATE = """\
You are a research assistant filling out one entry in the FLOSSI0ULLK reuse-ledger.
The reuse-ledger is the canonical anti-duplication record for the FLOSSI0ULLK
project: it prevents rebuilding what already exists in usable FLOSS form.

Read the upstream repo metadata + README excerpt below and produce a SINGLE
YAML object matching the schema in FLOSSI0ULLK/docs/research/reuse-ledger-seed.yaml.

CRITICAL: Output ONLY YAML. No prose, no preamble, no markdown code fences,
no explanatory comments outside YAML comments. Start with a single `- id:` line
and end with the final field. Every field listed below MUST be present.

Fields you MUST populate:
  id:                  "reuse-ledger-{id}"    # use this exact id
  domain:              one of: agent-centric-p2p-substrate | semantic-spanning-layer
                       | portable-agent-identity | value-flow-accounting
                       | multi-agent-orchestration | sovereign-code-artifacts
                       | offline-knowledge-commons | environmental-sensing
                       | pilot-embedding-model | personal-agent-harness
                       | persistent-memory-federation | holochain-development-tooling
                       | multi-model-consensus-governance | sibling-holochain-fractal-governance
                       | OR a NEW kebab-case domain name if none of the above fit
  candidate_project:   "{name} ({owner}/{repo})"
  url:                 "{url}"
  kalisam_fork:        leave blank if unknown
  function_needed:     >  multi-line description of WHAT FLOSSI0ULLK needs that
                          this project would provide. NOT a marketing pitch.
                          Frame in FLOSSI0ULLK layer terms when possible
                          (Layer 0 storage / Layer 1 memory / Layer 2 semantic /
                          Layer 4 coordination / Layer 4.5 gateway / etc.)
  reuse_level:         one of: direct | adapter | protocol-alignment | collaboration | monitor | reject
  license_status:      "pending" UNLESS you can verify the SPDX ID from metadata,
                       in which case state it explicitly (e.g., "pending - Apache-2.0
                       per metadata; needs AGPL-3 cascade compat per ADR-7")
  maturity:            active | maintained | stale | archived
                       Use pushed_at: active if <30 days, maintained if <90,
                       stale if <365, archived otherwise.
  integration_risk:    low | medium | high  (justify in notes)
  contact_path:        github discussions URL or maintainer contact path
  gate_status:
    license: pending | pass | fail
    adapter_test: pending
    provenance: pending
    rollback: pending
    contact: pending
  decision:            adopt | adapt | collaborate | monitor | reject | investigate
                       Default to "investigate" unless there is a CLEAR shape-match
                       to a declared FLOSSI0ULLK component.
  notes: >             3-6 sentences: (a) what makes this relevant/irrelevant,
                       (b) the closest FLOSSI0ULLK analogue if one exists,
                       (c) key risks or shape-mismatches, (d) anti-pattern
                       check (vision accumulation, alignment-as-proof, etc.)
  next_action:         single concrete action item, < 200 chars
  next_action_owner:   "Tony" | "Gemini CLI delegate" | "Frame community"
  next_action_deadline: ISO date 7-14 days from today ({today})

Critical guards (apply to your output):
- Do NOT recommend `decision: adopt` based on philosophical alignment alone.
  Architectural resonance is NOT working interoperability. Default to `investigate`.
- Do NOT invent capabilities the README does not claim.
- Do NOT inflate reuse_level. `adapter` if FLOSSI0ULLK needs to write glue;
  `protocol-alignment` if only interop is the concern; `direct` only if the
  project is a near drop-in dependency.
- License gate is `fail` if the project's license is incompatible with AGPL-3
  cascade per FLOSSI0ULLK ADR-7. Apache-2.0, MIT, GPL-3.0, MPL-2.0, AGPL-3.0
  are PASS-eligible. Proprietary, no-license, BSL, SSPL, or unclear ⇒ fail.
- If the project description suggests centralized routing or single-subscription
  model gating, flag in notes as a P5 violation (no central routing) per the
  obstruction taxonomy in resonance_mechanism_v2.md §9.

Upstream metadata:
{metadata}

README excerpt (truncated to {readme_chars} chars):
---
{readme}
---

Output the single YAML object now. Begin with `- id: reuse-ledger-{id}` on the first line.
"""


def assemble_prompt(target: ForkTarget, entry_id: str,
                    metadata: dict, readme: str) -> str:
    return PROMPT_TEMPLATE.format(
        id=entry_id,
        name=metadata.get("name", target.repo),
        owner=target.owner,
        repo=target.repo,
        url=target.url,
        today=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        metadata=json.dumps(metadata, indent=2),
        readme=readme or "(README unavailable)",
        readme_chars=len(readme),
    )


def invoke_gemini(prompt: str) -> tuple[int, str, str]:
    """Run gemini CLI with the prompt. Returns (returncode, stdout, stderr).

    - Resolves gemini path via shutil.which so Windows .cmd/.bat shims are found.
      Python's subprocess on Windows does NOT auto-expand extensions for argv[0].
    - Passes the prompt via stdin (not -p arg) to avoid Windows cmd.exe's ~8KB
      command-line length cap. Gemini docs: stdin is appended to the -p prompt,
      so we pass a 1-byte -p marker to trigger headless mode and stream the
      real prompt via stdin.
    - cwd is set to a fresh temp directory. Gemini CLI does a workspace scan
      on startup to gather context. If the parent directory tree contains any
      ACL-locked subdirectory (observed 2026-05-17 with c:\\~shit\\_pr25fix\\
      .pytest_cache, created under a different Windows user account and not
      readable by the current user), the libuv-based async scanner crashes
      with `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)` and aborts
      with exit code 0xC0000409. Running with cwd=tempdir avoids the scan
      entirely. The harvest content is passed via stdin and doesn't depend on
      cwd, so this is safe.
    """
    import tempfile
    gemini_path = shutil.which("gemini")
    if gemini_path is None:
        return 127, "", "gemini CLI not found on PATH"
    cmd = [gemini_path, "-m", GEMINI_MODEL, "-p", "."]
    with tempfile.TemporaryDirectory(prefix="floss_harvest_") as tmpdir:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                              timeout=GEMINI_TIMEOUT_SECONDS, check=False,
                              shell=False, encoding="utf-8", cwd=tmpdir)
    return proc.returncode, proc.stdout, proc.stderr


def strip_code_fences(text: str) -> str:
    """Gemini sometimes wraps output in ```yaml ... ```. Strip if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first line and last line if it's a fence
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def validate_yaml_entry(yaml_text: str) -> tuple[bool, str]:
    """Lightweight validation — does the output look like a ledger entry?
    Full YAML parse would be nice but we don't want to take a yaml dependency
    at this layer. Check for required field NAMES (not values, since the model
    may quote ids/strings inconsistently)."""
    required_field_names = [
        "id:",
        "domain:",
        "candidate_project:",
        "url:",
        "function_needed:",
        "reuse_level:",
        "license_status:",
        "gate_status:",
        "decision:",
        "notes:",
        "next_action:",
        "next_action_owner:",
    ]
    missing = [m for m in required_field_names if m not in yaml_text]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    # Must look like a YAML list entry: contain `- id:` somewhere
    if not re.search(r"^\s*-\s+id\s*:", yaml_text, re.MULTILINE):
        return False, "Output does not start with `- id:` (not a YAML list entry)"
    # Must reference the reuse-ledger id namespace (quoted or unquoted)
    if "reuse-ledger-" not in yaml_text:
        return False, "Output does not reference the reuse-ledger- id namespace"
    return True, ""


def next_available_id() -> str:
    """Scan canonical ledger AND staging dir for highest id and return next.

    Without scanning staging, batch invocations all get the same id (the next
    after the canonical ledger). Scanning staging too means each draft in a
    batch gets a unique id pre-promotion, even though promotion may re-number.
    """
    all_ids: list[int] = []
    if LEDGER_FILE.exists():
        all_ids.extend(int(m) for m in re.findall(
            r"reuse-ledger-(\d{4})", LEDGER_FILE.read_text(encoding="utf-8")))
    if STAGING_DIR.exists():
        for path in STAGING_DIR.glob("*_draft.yaml"):
            all_ids.extend(int(m) for m in re.findall(
                r"reuse-ledger-(\d{4})", path.read_text(encoding="utf-8")))
    if not all_ids:
        return "0011"
    return f"{max(all_ids) + 1:04d}"


def write_outputs(target: ForkTarget, entry_id: str, yaml_text: str,
                  provenance: dict) -> tuple[Path, Path]:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    yaml_path = STAGING_DIR / f"{entry_id}_{target.slug}_draft.yaml"
    prov_path = STAGING_DIR / f"{entry_id}_{target.slug}_provenance.json"
    yaml_path.write_text(yaml_text + "\n", encoding="utf-8")
    prov_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    return yaml_path, prov_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("url", nargs="?", help="GitHub URL or owner/repo")
    parser.add_argument("--owner", help="GitHub owner (use with --repo)")
    parser.add_argument("--repo", help="GitHub repo name (use with --owner)")
    parser.add_argument("--id", help="Explicit ledger id (default: next available)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print assembled prompt and exit without invoking gemini")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.url:
        target = parse_url(args.url)
    elif args.owner and args.repo:
        target = ForkTarget(args.owner, args.repo,
                            f"https://github.com/{args.owner}/{args.repo}")
    else:
        print("ERROR: provide a URL or --owner+--repo", file=sys.stderr)
        return 1

    entry_id = args.id or next_available_id()
    check_prereqs()

    print(f"[{utc_iso()}] harvest target: {target.owner}/{target.repo} → id={entry_id}",
          file=sys.stderr)
    invocation_started = datetime.now(timezone.utc)
    append_activity("harvest_start", target=f"{target.owner}/{target.repo}",
                    url=target.url, entry_id=entry_id, model=GEMINI_MODEL)

    metadata = fetch_upstream_metadata(target)
    readme = fetch_upstream_readme(target)

    print(f"[{utc_iso()}] fetched metadata: {metadata.get('name', '?')} "
          f"stars={metadata.get('stars', '?')} license={metadata.get('license', '?')} "
          f"pushed={metadata.get('pushed_at', '?')}", file=sys.stderr)
    print(f"[{utc_iso()}] readme: {len(readme)} chars", file=sys.stderr)

    prompt = assemble_prompt(target, entry_id, metadata, readme)

    if args.dry_run:
        print("=== ASSEMBLED PROMPT (--dry-run) ===")
        print(prompt)
        return 0

    print(f"[{utc_iso()}] invoking gemini ({GEMINI_MODEL}, timeout {GEMINI_TIMEOUT_SECONDS}s)...",
          file=sys.stderr)
    rc, stdout, stderr = invoke_gemini(prompt)
    if rc != 0:
        print(f"ERROR: gemini exit={rc}\n{stderr}", file=sys.stderr)
        append_activity("harvest_fail", target=f"{target.owner}/{target.repo}",
                        entry_id=entry_id, reason="gemini_subprocess_error",
                        gemini_rc=rc, gemini_stderr_tail=stderr[-300:] if stderr else "")
        return 2

    yaml_text = strip_code_fences(stdout)
    ok, err = validate_yaml_entry(yaml_text)
    if not ok:
        print(f"ERROR: invalid output — {err}", file=sys.stderr)
        print("=== RAW OUTPUT ===", file=sys.stderr)
        print(stdout[:2000], file=sys.stderr)
        append_activity("harvest_fail", target=f"{target.owner}/{target.repo}",
                        entry_id=entry_id, reason="validation_failed",
                        validation_error=err, raw_output_head=stdout[:300])
        return 3

    provenance = {
        "timestamp": utc_iso(),
        "harvest_id": entry_id,
        "target": {"owner": target.owner, "repo": target.repo, "url": target.url},
        "upstream_metadata_snapshot": metadata,
        "readme_length_chars": len(readme),
        "gemini_model": GEMINI_MODEL,
        "gemini_timeout_seconds": GEMINI_TIMEOUT_SECONDS,
        "gemini_returncode": rc,
        "gemini_stderr_tail": stderr[-500:] if stderr else "",
        "script": str(Path(__file__).relative_to(WORKSPACE_ROOT).as_posix()),
        "script_version": "0.1.0",
        "human_review_required": True,
        "promotion_target": str(LEDGER_FILE.relative_to(WORKSPACE_ROOT).as_posix()),
    }

    yaml_path, prov_path = write_outputs(target, entry_id, yaml_text, provenance)

    print(f"[{utc_iso()}] DRAFT staged: {yaml_path.relative_to(WORKSPACE_ROOT)}")
    print(f"[{utc_iso()}] provenance:   {prov_path.relative_to(WORKSPACE_ROOT)}")
    print(f"[{utc_iso()}] NEXT: human review the draft; if good, append to {LEDGER_FILE.relative_to(WORKSPACE_ROOT)}")
    append_activity("harvest_success", target=f"{target.owner}/{target.repo}",
                    entry_id=entry_id, model=GEMINI_MODEL,
                    draft_path=str(yaml_path.relative_to(WORKSPACE_ROOT).as_posix()),
                    provenance_path=str(prov_path.relative_to(WORKSPACE_ROOT).as_posix()),
                    duration_seconds=round((datetime.now(timezone.utc) -
                                            invocation_started).total_seconds(), 2),
                    license_from_metadata=metadata.get("license", "?"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
