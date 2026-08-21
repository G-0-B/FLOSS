"""Spec-gate — the "-1 layer" check (decision D7, adopted by Anthony 2026-06-12).

Root cause being fixed (metaharness inventory §4, 2026-06-09): artifacts were
built before being spec'd/committed as deliberate artifacts. This gate makes
that visible: every artifact on a GATED surface must carry a one-line spec
stub in the registry, or `--check` fails closed.

Scope (v0.1) — friction lands ONLY where canon status is claimed:
    GATED:  FLOSS/scripts/*, FLOSS/hooks/*, FLOSS/docs/specs/*, FLOSS/docs/adr/*
    EXEMPT: workspace root, docs/research/ (incl. intake_raw), docs/agent-memory/,
            .agent-surface/, tests/, caches — intake mouths and continuation/seed
            artifacts are definitionally pre-spec and NEVER gated.

Registry: FLOSS/docs/specs/spec-registry.json (hand-edited source of truth).

Reuse gate (ADR-18, operator-approved 2026-07-16, shape B+C): entries carrying
`"tier": 1|2` must also carry a `reuse` block (adopt/extend/compose/build
evidence per docs/specs/reuse-gate.schema.json); `--check` fails closed on
missing/stale/invalid blocks. `"emergency": true` downgrades to a warning
until promotion. Tier-2 compose/build verdicts require >=1 direct probe.

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
    --add <p> --spec "…"  register an artifact [--spec-ref <doc>] [--tier 1|2]
    --list                dump registry entries
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "docs" / "specs" / "spec-registry.json"
CANONICAL_REPO_PREFIX = "FLOSS"

# Keep in sync with `gated_surfaces` in FLOSS/docs/specs/spec-registry.json.
# That field is documentation; THIS tuple is what --check actually walks. They
# drifted once already: hooks moved out of scripts/ in cc216f8 (2026-07-26) and
# their four registry entries went silently unenforced until 2026-08-10.
GATED_SURFACES = (
    "FLOSS/scripts",
    "FLOSS/hooks",
    "FLOSS/docs/specs",
    "FLOSS/docs/adr",
)
EXEMPT_SEGMENTS = (
    "/__pycache__/",
    "/scripts/tests/",
    "/.venv/",
    "/venv/",
    "/archive/",
)
EXEMPT_NAMES = ("INDEX.md", ".gitignore", "__init__.py")

# ADR-18 Prior-Art & Reuse Gate (shape B+C, operator-approved 2026-07-16).
# Schema: docs/specs/reuse-gate.schema.json · Spec: docs/specs/reuse-gate.spec.md
EVIDENCE_WINDOW_DAYS = 120  # operator-set 2026-07-16
REUSE_REQUIRED_KEYS = (
    "capability",
    "search_date",
    "candidates",
    "verdict",
    "irreducible_delta",
)
REUSE_VERDICTS = ("adopt", "extend", "compose", "build")


def _normalize(path_str: str | Path) -> str | None:
    """Return a canonical FLOSS-prefixed path for a file inside this worktree."""
    canonical_parts = PurePosixPath(str(path_str).replace("\\", "/")).parts
    try:
        if canonical_parts and canonical_parts[0] == CANONICAL_REPO_PREFIX:
            physical_path = _physical_path("/".join(canonical_parts))
            if physical_path is None:
                return None
            resolved = physical_path.resolve()
        else:
            candidate = Path(path_str)
            resolved = (candidate if candidate.is_absolute() else REPO_ROOT / candidate).resolve()
    except OSError:
        return None
    try:
        relative = resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return None
    return f"{CANONICAL_REPO_PREFIX}/{relative}"


def _physical_path(canonical_path: str) -> Path | None:
    """Resolve a canonical registry key inside the current physical worktree."""
    parts = PurePosixPath(canonical_path).parts
    if not parts or parts[0] != CANONICAL_REPO_PREFIX:
        return None
    return REPO_ROOT.joinpath(*parts[1:])


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
        entry = registry.get("entries", {}).get(rel)
        if entry is not None:
            tier = entry.get("tier")
            if tier in (1, 2) and "reuse" not in entry and not entry.get("emergency"):
                return (
                    f"reuse-gate (ADR-18): `{rel}` is tier {tier} but carries no "
                    f"reuse block — record adopt/extend/compose/build evidence in "
                    f"spec-registry.json (schema: docs/specs/reuse-gate.schema.json)"
                )
            return None
        script_path = Path(__file__).resolve()
        return (
            f"spec-gate: `{rel}` is on a gated surface but has no spec stub in "
            f"docs/specs/spec-registry.json — register it before it ossifies: "
            f'python "{script_path}" --add "{rel}" --spec "<one-line intent>"'
        )
    except Exception:  # noqa: BLE001 — advisory must never break a hook
        return None


def _gated_artifacts() -> list[str]:
    found: list[str] = []
    for surface in GATED_SURFACES:
        root = _physical_path(surface)
        if root is None:
            continue
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and is_gated(path):
                rel = _normalize(path)
                if rel:
                    found.append(rel)
    return found


def _reuse_problems(rel: str, entry: dict) -> tuple[list[str], list[str]]:
    """Validate an entry's reuse block (ADR-18). Returns (fails, warns)."""
    tier = entry.get("tier")
    if tier not in (1, 2):
        return [], []
    reuse = entry.get("reuse")
    if not isinstance(reuse, dict):
        if entry.get("emergency"):
            return [], [
                f"{rel}: emergency artifact without reuse record — retrospective "
                f"audit required before promotion/generalization"
            ]
        return [f"{rel}: tier {tier} artifact has no reuse block"], []
    fails: list[str] = []
    missing_keys = [k for k in REUSE_REQUIRED_KEYS if k not in reuse]
    if missing_keys:
        fails.append(f"{rel}: reuse block missing keys: {', '.join(missing_keys)}")
    verdict = reuse.get("verdict")
    if verdict is not None and verdict not in REUSE_VERDICTS:
        fails.append(f"{rel}: verdict {verdict!r} not in {'/'.join(REUSE_VERDICTS)}")
    raw_date = str(reuse.get("search_date", ""))
    try:
        age = (_dt.date.today() - _dt.date.fromisoformat(raw_date)).days
    except ValueError:
        fails.append(f"{rel}: reuse search_date {raw_date!r} is not YYYY-MM-DD")
    else:
        window = int(reuse.get("evidence_window_days", EVIDENCE_WINDOW_DAYS))
        if age > window:
            fails.append(
                f"{rel}: reuse evidence stale ({age}d > {window}d window) — "
                f"re-run the scan"
            )
    if tier == 2 and rel not in REVIEWER_GRANDFATHERED:
        # ADR-18 / reuse-gate.spec.md require an INDEPENDENT reuse review for
        # every tier-2 entry, not only for compose/build. Nothing enforced it,
        # and the registry demonstrated the bypass: the one entry carrying a
        # reuse block had `"reviewer": "pending first reuse-review poll..."`
        # while run_check reported 0 reuse violations. A placeholder that
        # satisfies a gate is worse than an empty field, because it reads as
        # done.
        reviewer = str(reuse.get("reviewer") or "").strip()
        if not reviewer:
            fails.append(
                f"{rel}: tier 2 requires an independent reuse review "
                f"(`reuse.reviewer`), ADR-18"
            )
        elif any(
            marker in reviewer.lower()
            for marker in ("pending", "tbd", "todo", "not_reviewed", "placeholder")
        ):
            fails.append(
                f"{rel}: tier 2 `reuse.reviewer` is a placeholder ({reviewer!r}); "
                f"run the reuse-review poll (>=3 provider surfaces, >=4 model "
                f"families) and record its outcome, ADR-18"
            )
    if tier == 2 and verdict in ("compose", "build"):
        candidates = reuse.get("candidates") or []
        probed = [
            c
            for c in candidates
            if isinstance(c, dict)
            and c.get("probe")
            and not str(c["probe"]).strip().lower().startswith("not_probed")
        ]
        if not probed:
            fails.append(
                f"{rel}: tier 2 {verdict!r} verdict requires >=1 direct probe "
                f"(anti-gaming, ADR-18)"
            )
    return fails, []


# Entries that predate reviewer enforcement (added 2026-08-21 after PR41 review
# found the requirement stated but unchecked). Fail-closed for everything NEW,
# grandfathered here for what already existed -- the same ratchet the CI green
# set uses. This list only ever shrinks.
#
# A first reuse-review poll WAS attempted for this entry on 2026-08-21 (claim
# 01a02666-ad63-71db-a187-4968e67699fa, profile-equivalent 4 surfaces / 4
# families). It came back REJECTED, mean -0.5375, variance 0.0092 -- but all
# four voters rejected on the same procedural ground, an empty evidence list,
# and none engaged the substantive verdict question. A governed SpecChange needs
# provenance packets, which the claim did not carry. That is a valid negative on
# procedure, not a reuse review, so it is NOT recorded as one.
#
# To clear this entry: re-run the poll with provenance evidence attached, then
# record the outcome in `reuse.reviewer` and delete the line below.
REVIEWER_GRANDFATHERED = {
    "FLOSS/docs/specs/reuse-gate.spec.md",
}


def run_check() -> int:
    registry = load_registry()
    if "load_error" in registry:
        print(f"SPEC-GATE FAIL: registry unreadable: {registry['load_error']}")
        return 1
    entries = registry.get("entries", {})
    missing = [rel for rel in _gated_artifacts() if rel not in entries]
    # PR38's worktree-aware resolution: _physical_path handles registry keys that
    # do not map into this checkout, which WORKSPACE_ROOT / rel mis-resolved.
    stale = [rel for rel in entries if (path := _physical_path(rel)) is None or not path.exists()]
    reuse_fails: list[str] = []
    reuse_warns: list[str] = []
    for rel, entry in entries.items():
        fails, warns = _reuse_problems(rel, entry)
        reuse_fails.extend(fails)
        reuse_warns.extend(warns)
    for rel in missing:
        print(f"SPEC-GATE MISSING {rel}")
    for rel in stale:
        print(f"SPEC-GATE STALE   {rel} (registered but absent — prune or restore)")
    for msg in reuse_warns:
        print(f"SPEC-GATE REUSE-WARN {msg}")
    for msg in reuse_fails:
        print(f"SPEC-GATE REUSE-FAIL {msg}")
    if missing or reuse_fails:
        parts = []
        if missing:
            parts.append(
                f"{len(missing)} unregistered gated artifact(s) — register with: "
                f'python FLOSS/scripts/spec_gate.py --add <path> --spec "<one-liner>"'
            )
        if reuse_fails:
            parts.append(
                f"{len(reuse_fails)} reuse-gate violation(s) (ADR-18) — see "
                f"docs/specs/reuse-gate.spec.md"
            )
        print("\nSPEC-GATE FAIL: " + "; ".join(parts))
        return 1
    print(
        f"SPEC-GATE OK: {len(entries)} registered, 0 missing, 0 reuse violations"
        + (f", {len(stale)} stale (non-fatal)" if stale else "")
        + (f", {len(reuse_warns)} emergency reuse warning(s)" if reuse_warns else "")
    )
    return 0


def run_add(
    path_str: str, spec: str, spec_ref: str | None, tier: int | None = None
) -> int:
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
    if tier is not None:
        entry["tier"] = tier
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
    parser.add_argument(
        "--tier",
        type=int,
        choices=(1, 2),
        help="Reuse-gate tier for --add (ADR-18): 1 = evidence record, 2 = + review",
    )
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
        return run_add(args.add, args.spec, args.spec_ref, args.tier)
    if args.list:
        registry = load_registry()
        for rel, entry in registry.get("entries", {}).items():
            ref = f"  [{entry['spec_ref']}]" if "spec_ref" in entry else ""
            print(f"{rel}: {entry.get('spec', '?')}{ref}")
        return 0
    return run_check()


if __name__ == "__main__":
    raise SystemExit(main())
