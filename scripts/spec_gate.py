"""Spec-gate — the "-1 layer" check (decision D7, adopted by Anthony 2026-06-12).

Root cause being fixed (metaharness inventory §4, 2026-06-09): artifacts were
built before being spec'd/committed as deliberate artifacts. This gate makes
that visible: every artifact on a GATED surface must carry a one-line spec
stub in the registry, or `--check` fails closed.

Scope (v0.1) — friction lands ONLY where canon status is claimed:
    GATED:  FLOSS/scripts/*, FLOSS/docs/specs/*, FLOSS/docs/adr/*
    EXEMPT: workspace root, docs/research/ (incl. intake_raw), docs/agent-memory/,
            .agent-surface/, tests/, caches — intake mouths and continuation/seed
            artifacts are definitionally pre-spec and NEVER gated.

Registry: FLOSS/docs/specs/spec-registry.json (hand-edited source of truth).

Wiring (both, per Anthony 2026-06-12):
    1. Audit path  — `python FLOSS/scripts/spec_gate.py --check` (exit 1 on any
       unregistered gated artifact; run alongside materializer --check sweeps;
       CI canary candidate per orient-handoff deferred decision #10).
    2. Runtime path — hook_post_write.py calls `advisory_note()` on every
       mutating tool call into a gated surface and surfaces the warning as
       hook additionalContext. Advisory only: the hook never blocks (exit 0).

Modes:
    --check               fail-closed audit (default)
    --path <p>            print advisory for one path; always exit 0 (hook use)
    --add <p> --spec "…"  register an artifact [--spec-ref <doc>]
    --list                dump registry entries
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
REGISTRY_PATH = REPO_ROOT / "docs" / "specs" / "spec-registry.json"

GATED_SURFACES = ("FLOSS/scripts", "FLOSS/docs/specs", "FLOSS/docs/adr")
EXEMPT_SEGMENTS = (
    "/__pycache__/",
    "/scripts/tests/",
    "/.venv/",
    "/venv/",
    "/archive/",
)
EXEMPT_NAMES = ("INDEX.md", ".gitignore", "__init__.py")


def _normalize(path_str: str | Path) -> str | None:
    """Workspace-relative forward-slash path, or None if outside workspace."""
    try:
        resolved = Path(path_str).resolve()
    except OSError:
        return None
    try:
        return resolved.relative_to(WORKSPACE_ROOT.resolve()).as_posix()
    except ValueError:
        return None


def is_gated(path_str: str | Path) -> bool:
    rel = _normalize(path_str)
    if rel is None:
        return False
    norm = "/" + rel.lower() + ("/" if not rel.endswith("/") else "")
    if any(seg in norm for seg in EXEMPT_SEGMENTS):
        return False
    if Path(rel).name in EXEMPT_NAMES:
        return False
    return any(
        rel == surface or rel.startswith(surface + "/") for surface in GATED_SURFACES
    )


def load_registry() -> dict:
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"version": "missing", "entries": {}, "load_error": str(exc)}


def advisory_note(path_str: str | Path) -> str | None:
    """One-line advisory for hooks. None when the path is fine. Never raises."""
    try:
        if not is_gated(path_str):
            return None
        rel = _normalize(path_str)
        registry = load_registry()
        if "load_error" in registry:
            return f"spec-gate: registry unreadable ({registry['load_error']})"
        if rel in registry.get("entries", {}):
            return None
        return (
            f"spec-gate: `{rel}` is on a gated surface but has no spec stub in "
            f"docs/specs/spec-registry.json — register it before it ossifies: "
            f'python FLOSS/scripts/spec_gate.py --add "{rel}" --spec "<one-line intent>"'
        )
    except Exception:  # noqa: BLE001 — advisory must never break a hook
        return None


def _gated_artifacts() -> list[str]:
    found: list[str] = []
    for surface in GATED_SURFACES:
        root = WORKSPACE_ROOT / surface
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and is_gated(path):
                rel = _normalize(path)
                if rel:
                    found.append(rel)
    return found


def run_check() -> int:
    registry = load_registry()
    if "load_error" in registry:
        print(f"SPEC-GATE FAIL: registry unreadable: {registry['load_error']}")
        return 1
    entries = registry.get("entries", {})
    missing = [rel for rel in _gated_artifacts() if rel not in entries]
    stale = [rel for rel in entries if not (WORKSPACE_ROOT / rel).exists()]
    for rel in missing:
        print(f"SPEC-GATE MISSING {rel}")
    for rel in stale:
        print(f"SPEC-GATE STALE   {rel} (registered but absent — prune or restore)")
    if missing:
        print(
            f"\nSPEC-GATE FAIL: {len(missing)} unregistered gated artifact(s). "
            f"Register with: python FLOSS/scripts/spec_gate.py --add <path> --spec \"<one-liner>\""
        )
        return 1
    print(
        f"SPEC-GATE OK: {len(entries)} registered, 0 missing"
        + (f", {len(stale)} stale (non-fatal)" if stale else "")
    )
    return 0


def run_add(path_str: str, spec: str, spec_ref: str | None) -> int:
    rel = _normalize(path_str)
    if rel is None:
        print(f"spec-gate: {path_str} is outside the workspace")
        return 1
    if not is_gated(path_str):
        print(f"spec-gate: {rel} is not on a gated surface — nothing to register")
        return 1
    registry = load_registry()
    if "load_error" in registry:
        print(f"spec-gate: registry unreadable: {registry['load_error']}")
        return 1
    entry: dict = {"spec": spec.strip()}
    if spec_ref:
        entry["spec_ref"] = spec_ref
    registry.setdefault("entries", {})[rel] = entry
    registry["entries"] = dict(sorted(registry["entries"].items()))
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"spec-gate: registered {rel}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Spec-gate (-1 layer) check")
    parser.add_argument("--check", action="store_true", help="Fail-closed audit (default)")
    parser.add_argument("--path", help="Print advisory for one path; always exit 0")
    parser.add_argument("--add", help="Register a gated artifact")
    parser.add_argument("--spec", help="One-line spec stub for --add")
    parser.add_argument("--spec-ref", help="Optional pointer to a fuller spec doc")
    parser.add_argument("--list", action="store_true", help="Dump registry entries")
    args = parser.parse_args()

    if args.path:
        note = advisory_note(args.path)
        if note:
            print(note)
        return 0
    if args.add:
        if not args.spec:
            print("spec-gate: --add requires --spec \"<one-line intent>\"")
            return 1
        return run_add(args.add, args.spec, args.spec_ref)
    if args.list:
        registry = load_registry()
        for rel, entry in registry.get("entries", {}).items():
            ref = f"  [{entry['spec_ref']}]" if "spec_ref" in entry else ""
            print(f"{rel}: {entry.get('spec', '?')}{ref}")
        return 0
    return run_check()


if __name__ == "__main__":
    raise SystemExit(main())
