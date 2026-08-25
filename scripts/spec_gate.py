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
from typing import Any

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
# Mirrors the `truth_status` enum in docs/specs/reuse-gate.schema.json, which is
# the project's own truth-label vocabulary minus Blocked (a blocked candidate is
# not prior art you evaluated, it is one you could not).
REUSE_TRUTH_STATUSES = ("Verified", "Specified", "Unverified")


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
            resolved = (
                candidate if candidate.is_absolute() else REPO_ROOT / candidate
            ).resolve()
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


REVIEWER_REQUIRED_KEYS = ("surfaces", "families", "record", "outcome", "date")
# From docs/specs/reuse-gate.spec.md. Same numbers the consensus gateway's
# independence rule uses: same-family endpoints do not count as independence.
REVIEWER_MIN_SURFACES = 3
REVIEWER_MIN_FAMILIES = 4


def _reviewer_problems(rel: str, reviewer: Any) -> list[str]:
    """Validate tier-2 independent-review evidence (ADR-18).

    A string is no longer accepted. The review either happened -- in which case
    naming the surfaces, the families, the outcome, the date, and a record that
    exists on disk costs nothing -- or it did not, in which case the entry
    should fail rather than read as done.
    """
    if reviewer is None or (isinstance(reviewer, str) and not reviewer.strip()):
        return [
            f"{rel}: tier 2 requires an independent reuse review "
            f"(`reuse.reviewer`), ADR-18"
        ]
    if not isinstance(reviewer, dict):
        return [
            f"{rel}: tier 2 `reuse.reviewer` must be an object with "
            f"{', '.join(REVIEWER_REQUIRED_KEYS)} — prose does not establish "
            f"that a >={REVIEWER_MIN_SURFACES}-surface / "
            f">={REVIEWER_MIN_FAMILIES}-family review happened, ADR-18"
        ]
    problems: list[str] = []
    missing = [k for k in REVIEWER_REQUIRED_KEYS if k not in reviewer]
    if missing:
        problems.append(f"{rel}: reuse.reviewer missing keys: {', '.join(missing)}")
    for key, minimum in (
        ("surfaces", REVIEWER_MIN_SURFACES),
        ("families", REVIEWER_MIN_FAMILIES),
    ):
        if key not in reviewer:
            continue
        values = reviewer.get(key)
        if not isinstance(values, list) or not all(
            isinstance(v, str) and v.strip() for v in values
        ):
            problems.append(f"{rel}: reuse.reviewer.{key} must be a list of names")
            continue
        distinct = {v.strip().lower() for v in values}
        if len(distinct) < minimum:
            problems.append(
                f"{rel}: reuse.reviewer.{key} has {len(distinct)} distinct, "
                f"needs >={minimum} (ADR-18 independence rule)"
            )
    # Typed, not stringified. This is the same defect as the candidate fields
    # one function above, repeated while fixing them: `str(7).strip()` is
    # non-empty, so `{"outcome": 7, "date": 20260825}` cleared a check whose
    # entire purpose is establishing that a review happened.
    if "outcome" in reviewer:
        outcome = reviewer.get("outcome")
        if not isinstance(outcome, str) or not outcome.strip():
            problems.append(f"{rel}: reuse.reviewer.outcome must be a non-empty string")
    if "date" in reviewer:
        raw_date = reviewer.get("date")
        if not isinstance(raw_date, str):
            problems.append(f"{rel}: reuse.reviewer.date must be a YYYY-MM-DD string")
        else:
            try:
                _dt.date.fromisoformat(raw_date.strip())
            except ValueError:
                problems.append(
                    f"{rel}: reuse.reviewer.date {raw_date!r} is not YYYY-MM-DD"
                )
    if "record" in reviewer:
        record = reviewer.get("record")
        if not isinstance(record, str) or not record.strip():
            problems.append(f"{rel}: reuse.reviewer.record must be a path or ref")
        else:
            problems.extend(_record_problems(rel, record))
    return problems


PROBE_POSITIVE_PREFIX = "probed:"


def _is_direct_probe(candidate: Any) -> bool:
    """True only for POSITIVE evidence that a probe actually ran.

    The old test was negative -- any truthy string not literally beginning with
    `not_probed` counted -- so `"probe": "done"`, `"pending"`, `"TBD"` and even
    `"not probed: unavailable"` (a space instead of the underscore) all
    satisfied the tier-2 anti-gaming requirement. A rule that can be passed by
    typing a word is not an anti-gaming rule.

    Two accepted shapes, both asserting rather than merely failing to deny:

      {"probe": "probed: ran --check live 2026-08-25, fail-closed verified"}
      {"probe": {"status": "passed", "detail": "...", "date": "2026-08-25"}}

    Everything else, including every honest `not_probed:` declaration, is a
    candidate that was reasoned about rather than exercised. Those belong in the
    block -- ADR-18 wants the rejected alternatives recorded -- they just do not
    discharge the compose/build probe obligation.
    """
    if not isinstance(candidate, dict):
        return False
    probe = candidate.get("probe")
    if isinstance(probe, dict):
        return str(probe.get("status", "")).strip().lower() == "passed"
    if not isinstance(probe, str):
        return False
    return probe.strip().lower().startswith(PROBE_POSITIVE_PREFIX)


def _record_problems(rel: str, record: str) -> list[str]:
    """A reviewer record must be a regular file inside this repository.

    Checking `exists()` alone accepted `.` (a directory that exists) and
    `/etc/passwd` (a file that exists and is not a poll record). Absolute paths
    and `..` traversal both escaped the checkout, because joining an absolute
    path onto REPO_ROOT discards REPO_ROOT entirely. An evidence pointer that
    can resolve to any of those is a truthy string with extra steps.
    """
    candidate = record.strip()
    if PurePosixPath(candidate.replace("\\", "/")).is_absolute() or (
        len(candidate) > 1 and candidate[1] == ":"
    ):
        return [f"{rel}: reuse.reviewer.record {record!r} must be repository-relative"]
    try:
        resolved = (_physical_path(candidate) or (REPO_ROOT / candidate)).resolve()
        root = REPO_ROOT.resolve()
    except (OSError, ValueError):
        return [f"{rel}: reuse.reviewer.record {record!r} is not a usable path"]
    if root not in resolved.parents:
        return [
            f"{rel}: reuse.reviewer.record {record!r} resolves outside the "
            f"repository — evidence must live in the repository it governs"
        ]
    if not resolved.exists():
        return [
            f"{rel}: reuse.reviewer.record {record!r} does not exist — "
            f"an unresolvable record is not evidence"
        ]
    if not resolved.is_file():
        return [
            f"{rel}: reuse.reviewer.record {record!r} is not a regular file — "
            f"a directory identifies no poll record"
        ]
    return []


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
    # Key PRESENCE is not evidence. `{"capability": "", "candidates": [],
    # "irreducible_delta": ""}` satisfied the check above while violating
    # reuse-gate.schema.json, which requires a non-empty candidate array and
    # `name`/`truth_status` on each candidate. A gate that accepts an empty
    # reuse block enforces paperwork, not prior art.
    #
    # These constraints are restated here rather than validated with a
    # jsonschema library on purpose: adding a runtime dependency to the gate
    # that enforces ADR-18 would itself need to clear ADR-18, and this repo has
    # already been bitten by jsonschema `format` keywords silently no-opping
    # without the format extra installed. The authority is still
    # docs/specs/reuse-gate.schema.json; keep the two in step.
    for key in ("capability", "irreducible_delta"):
        value = reuse.get(key)
        if key in reuse and (not isinstance(value, str) or not value.strip()):
            fails.append(f"{rel}: reuse.{key} must be a non-empty string")
    if "candidates" in reuse:
        candidates = reuse.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            fails.append(
                f"{rel}: reuse.candidates must list >=1 prior-art candidate "
                f"(reuse-gate.schema.json minItems: 1) — an empty search is not "
                f"a search, ADR-18"
            )
        else:
            for position, candidate in enumerate(candidates):
                if not isinstance(candidate, dict):
                    fails.append(
                        f"{rel}: reuse.candidates[{position}] is not an object"
                    )
                    continue
                # Types and the enum, not just presence. Stringifying first
                # meant {"name": 7, "truth_status": "Trusted"} passed: 7 has a
                # non-empty str() and "Trusted" is not one of the three truth
                # labels this project actually uses. Malformed prior-art
                # evidence that type-checks as present is still not evidence.
                name = candidate.get("name")
                if not isinstance(name, str) or not name.strip():
                    fails.append(
                        f"{rel}: reuse.candidates[{position}].name must be a "
                        f"non-empty string"
                    )
                truth_status = candidate.get("truth_status")
                if truth_status not in REUSE_TRUTH_STATUSES:
                    fails.append(
                        f"{rel}: reuse.candidates[{position}].truth_status "
                        f"{truth_status!r} not in "
                        f"{'/'.join(REUSE_TRUTH_STATUSES)}"
                    )
                for field in (
                    "version",
                    "license",
                    "maintenance",
                    "platform_fit",
                    "probe",
                ):
                    if field in candidate and not isinstance(candidate[field], str):
                        fails.append(
                            f"{rel}: reuse.candidates[{position}].{field} must "
                            f"be a string"
                        )
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
        if age < 0:
            # A future date produces a negative age, which can never exceed the
            # window until that date arrives -- `2099-01-01` would keep the
            # evidence classified as fresh for decades. Freshness has to be
            # bounded on both sides.
            fails.append(
                f"{rel}: reuse search_date {raw_date!r} is in the future "
                f"({-age}d ahead); evidence cannot predate its own search"
            )
        elif age > window:
            fails.append(
                f"{rel}: reuse evidence stale ({age}d > {window}d window) — "
                f"re-run the scan"
            )
    if tier == 2 and not _is_reviewer_grandfathered(rel):
        # ADR-18 / reuse-gate.spec.md require an INDEPENDENT reuse review for
        # every tier-2 entry, not only for compose/build. Nothing enforced it,
        # and the registry demonstrated the bypass: the one entry carrying a
        # reuse block had `"reviewer": "pending first reuse-review poll..."`
        # while run_check reported 0 reuse violations. A placeholder that
        # satisfies a gate is worse than an empty field, because it reads as
        # done.
        # Prose is not evidence. Rejecting a list of placeholder words left
        # `"reviewer": "done"` passing a gate that claims to enforce a
        # >=3-surface / >=4-family independent review -- it names no reviewing
        # surface, no family, no poll, no outcome. Structured evidence is
        # required instead, and the `record` must actually resolve on disk, so
        # the claim is checkable rather than merely well-worded.
        fails.extend(_reviewer_problems(rel, reuse.get("reviewer")))
    if tier == 2 and verdict in ("compose", "build"):
        candidates = reuse.get("candidates") or []
        probed = [c for c in candidates if _is_direct_probe(c)]
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
#
# PINNED TO CONTENT. A path-only exemption covers the artifact forever, so any
# future rewrite of reuse-gate.spec.md would inherit an exemption granted to
# text nobody has read. The hash is the version that was grandfathered; edit the
# file and the exemption lapses, which is the correct moment to require the
# review that was deferred.
REVIEWER_GRANDFATHERED = {
    "FLOSS/docs/specs/reuse-gate.spec.md": (
        "f76512e63dd6ff6975424aa37c7aa0580ab4940844d01824542bf417e778b06e"
    ),
}


def _is_reviewer_grandfathered(rel: str) -> bool:
    """True only while the artifact still hashes to the grandfathered version."""
    expected = REVIEWER_GRANDFATHERED.get(rel)
    if expected is None:
        return False
    physical = _physical_path(rel)
    if physical is None or not physical.exists():
        return False
    import hashlib

    digest = hashlib.sha256(physical.read_bytes()).hexdigest()
    return digest == expected


def run_check() -> int:
    registry = load_registry()
    if "load_error" in registry:
        print(f"SPEC-GATE FAIL: registry unreadable: {registry['load_error']}")
        return 1
    entries = registry.get("entries", {})
    missing = [rel for rel in _gated_artifacts() if rel not in entries]
    # PR38's worktree-aware resolution: _physical_path handles registry keys that
    # do not map into this checkout, which WORKSPACE_ROOT / rel mis-resolved.
    stale = [
        rel
        for rel in entries
        if (path := _physical_path(rel)) is None or not path.exists()
    ]
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
    if tier is None:
        # Omitting --tier used to register the artifact as untiered, and
        # _reuse_problems returns immediately for anything not tier 1 or 2 --
        # so the omission silently exempted the entry from ADR-18 entirely.
        # 106 of the 107 entries already in the registry are untiered, which is
        # why `--check` reports 0 reuse violations across the whole surface.
        #
        # Fail closed for anything NEW. The existing 106 are not retroactively
        # broken -- see REUSE_TIER_GRANDFATHERED below -- but nothing else joins
        # them.
        print(
            f"spec-gate: {rel} needs an explicit --tier (1 = evidence record, "
            "2 = + independent reuse review). ADR-18 has no untiered category; "
            "an omitted tier is an exemption, not a default."
        )
        return 1
    entry: dict = {"spec": spec.strip()}
    if spec_ref:
        entry["spec_ref"] = spec_ref
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
    parser.add_argument(
        "--check", action="store_true", help="Fail-closed audit (default)"
    )
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
            print('spec-gate: --add requires --spec "<one-line intent>"')
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
