# Local Agent Node — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the ternary `{-1, 0, +1}` consensus gate with the analog vote model (float weights) and implement the file-based cell source chain that mirrors Holochain Cell primitives exactly.

**Architecture:** The Core-Logic track (C1 → C2) is a hard gate for the Physical track (P1 → P2 → P3). C2 must pass before P1 starts because P1 writes source chain entries whose hashes depend on the analog schema being correct. Each task produces a working, independently testable change.

**Tech Stack:** Python 3.11+, dataclasses (no Pydantic), `json` / `hashlib` / `math` stdlib, `pytest`, `mcp` SDK (FastMCP) for P2, `open(path, "x")` atomic file creation for P1 (cross-platform, no `fcntl`).

**Spec:** `docs/superpowers/specs/2026-04-12-local-agent-node-design.md`

**Preconditions — verify before starting:**

```bash
# serialization.py must exist (created in session F2)
[ -f C:/~shit/FLOSS/packages/orchestrator/serialization.py ] && echo "OK: serialization.py exists" || echo "ERROR: run Task 0 (F2) first"
```

If the file does not exist, complete **Task 0 (F2)** below before proceeding to C1.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `packages/orchestrator/claim_schema.py` | Add `CERTAINTY_LIMIT`, `CONFLICT` outcome, analog `Vote.weight: float`, thresholds dict, `Decision` tally stats |
| Modify | `packages/orchestrator/consensus_gate.py` | Rewrite `tally()` for analog model; remove early-exit from `decide()`; update `override()` |
| Rewrite | `packages/orchestrator/test_consensus_gate.py` | All 32 tests → analog weights; add CONFLICT vectors; add quorum-boundary tests |
| Create | `packages/source_chain/__init__.py` | Package marker |
| Create | `packages/source_chain/cell.py` | `CellDirectory` — append, read, lock |
| Create | `packages/source_chain/tests/__init__.py` | Package marker |
| Create | `packages/source_chain/tests/test_cell.py` | Unit tests for CellDirectory |
| Create | `packages/metacoordinator_mcp/__init__.py` | Package marker |
| Create | `packages/metacoordinator_mcp/server.py` | FastMCP server wiring |
| Create | `packages/metacoordinator_mcp/tools.py` | 5 MCP tool handlers |
| Create | `packages/metacoordinator_mcp/tests/test_tools.py` | Unit tests for tool handlers |
| Create | `FLOSS/.claude/settings.json` | PostToolUse agent hook for blast-radius detection |

---

## Task 0 (F2): Canonical Serialization — Precondition for all other tasks

**Gate:** None. Must be complete before C1, C2, P1.

**Files:**
- Create: `packages/orchestrator/serialization.py`

`cell.py` (P1) imports `canonical_serialize` and `entry_hash` from this module. If it doesn't exist, P1 fails with `ModuleNotFoundError` before writing a single entry.

If `packages/orchestrator/serialization.py` already exists (verified with the precondition check above), skip this task entirely.

- [ ] **Step 1: Write the failing test**

Add to `packages/orchestrator/test_serialization.py`:

```python
"""Tests for canonical_serialize / entry_hash (spec §3.3)."""
import hashlib
import math
import pytest
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.orchestrator.serialization import canonical_serialize, entry_hash, normalize_float


def test_negative_zero_normalized():
    result = canonical_serialize({"x": -0.0})
    assert result == b'{"x":0.0}'


def test_non_finite_raises():
    with pytest.raises(ValueError, match="Non-finite"):
        canonical_serialize({"x": math.nan})


def test_sort_keys():
    result = canonical_serialize({"z": 1, "a": 2})
    assert result == b'{"a":2,"z":1}'


def test_non_ascii_raw_utf8():
    result = canonical_serialize({"k": "—"})
    assert b"\\u" not in result
    assert "—".encode("utf-8") in result


def test_float_precision():
    result = canonical_serialize({"x": 1.23456789})
    assert result == b'{"x":1.234568}'


def test_entry_hash_is_64_hex():
    h = entry_hash({"type": "genesis", "content": {}})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
cd C:/~shit/FLOSS
python -m pytest packages/orchestrator/test_serialization.py -v 2>&1 | head -10
```

- [ ] **Step 3: Create `packages/orchestrator/serialization.py`**

```python
"""
Canonical serialization for FLOSSIØULLK source chain entries.

All source chain entries MUST be serialized via canonical_serialize() before
hashing. This ensures byte-identical SHA256 digests across Python, Rust, and
TypeScript implementations.

Cross-language invariants (any implementation MUST satisfy):
  1. Reject NaN and ±Inf — raise an error, never serialize them.
  2. Normalize -0.0 to 0.0 before serialization (IEEE 754 sign-bit collapse).
  3. Round floats to exactly 6 decimal places using round-half-to-even (banker's rounding).
  4. Emit raw UTF-8 strings — do NOT escape non-ASCII code points as \\uXXXX.
  5. Sort all object keys lexicographically (byte order of UTF-8 encoded key strings).
  6. No whitespace between tokens (separators=(',', ':')).
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

FLOAT_PRECISION = 6


def normalize_float(x: float) -> float:
    if not math.isfinite(x):
        raise ValueError(
            f"Non-finite float forbidden in source chain entries: {x!r}."
        )
    return round(x + 0.0, FLOAT_PRECISION)


def _normalize_val(obj: Any) -> Any:
    if isinstance(obj, float):
        return normalize_float(obj)
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return {k: _normalize_val(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize_val(x) for x in obj]
    if obj is None:
        return obj
    raise TypeError(
        f"Unserializable type {type(obj).__name__!r} in source chain entry."
    )


def canonical_serialize(data: dict) -> bytes:
    return json.dumps(
        _normalize_val(data),
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
    ).encode('utf-8')


def entry_hash(data: dict) -> str:
    return hashlib.sha256(canonical_serialize(data)).hexdigest()
```

- [ ] **Step 4: Run tests — all pass**

```bash
cd C:/~shit/FLOSS
python -m pytest packages/orchestrator/test_serialization.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit F2**

```bash
git add packages/orchestrator/serialization.py packages/orchestrator/test_serialization.py
git commit -m "feat(F2): canonical serialization — negative-zero normalization, NaN/Inf rejection, raw UTF-8"
```

---

## Task 1 (C1): Refactor claim_schema.py for Analog Vote Model

**Gate:** None. Can start immediately.

**Files:**
- Modify: `packages/orchestrator/claim_schema.py`

### What changes and why

The existing `Vote.vote: int` field accepts only `{-1, 0, +1}`. The analog model replaces this with `weight: float ∈ (-CERTAINTY_LIMIT, CERTAINTY_LIMIT)` where `CERTAINTY_LIMIT = 0.999`. Absolute ±1.0 is asymptotically unreachable by design (spec §2, principle 3).

`Outcome` gains `CONFLICT = "CONFLICT"` — high variance (deep disagreement) is a distinct state, not a special DEFERRED. It routes to human intervention.

`Decision` gains optional `tally_mean` and `tally_variance` fields so callers can log why a decision was reached without re-running the math.

Threshold tables are added as module-level dicts so `tally()` can look them up by blast radius without `if/elif` chains.

- [ ] **Step 1: Add `CERTAINTY_LIMIT` and `CONFLICT` to claim_schema.py**

Open `packages/orchestrator/claim_schema.py`.

After the `EVIDENCE_TYPES` constant (line 73), add the analog vote constants. The existing `QUORUM_MIN` and `OVERRIDE_ALLOWED` dicts must be preserved — do NOT delete them. Add the new constants alongside them:

```python
CERTAINTY_LIMIT: float = 0.999
"""Asymptotic upper bound for vote weights.

The valid domain for Vote.weight is the CLOSED interval [-CERTAINTY_LIMIT, CERTAINTY_LIMIT].
Weights of exactly ±0.999 are permitted. Absolute ±1.0 is forbidden — it represents a
limit approached asymptotically, not a reachable state (spec §2 principle 3).
"""

# Tally thresholds per blast radius (spec §4.3, analog vote model)
APPROVE_THRESHOLD: dict[BlastRadius, float] = {
    BlastRadius.LOCAL: 0.30,
    BlastRadius.MODULE: 0.50,
    BlastRadius.SYSTEM: 0.60,
    BlastRadius.SUBSTRATE: 0.85,
}
REJECT_THRESHOLD: dict[BlastRadius, float] = {
    BlastRadius.LOCAL: -0.30,
    BlastRadius.MODULE: -0.40,
    BlastRadius.SYSTEM: -0.50,
    BlastRadius.SUBSTRATE: -0.85,
}
POLARIZATION_THRESHOLD: dict[BlastRadius, float] = {
    BlastRadius.LOCAL: 0.60,
    BlastRadius.MODULE: 0.50,
    BlastRadius.SYSTEM: 0.40,
    BlastRadius.SUBSTRATE: 0.25,
}

# Quorum minimums per blast radius — these already exist in claim_schema.py.
# PRESERVE the existing QUORUM_MIN and OVERRIDE_ALLOWED dicts; do not replace them.
# They are shown here for reference:
# QUORUM_MIN = {LOCAL: 1, MODULE: 2, SYSTEM: 3, SUBSTRATE: 3}
# OVERRIDE_ALLOWED = {LOCAL: True, MODULE: True, SYSTEM: True, SUBSTRATE: False}
```

Add `CONFLICT = "CONFLICT"` to the `Outcome` enum:

```python
class Outcome(str, Enum):
    APPROVED = "APPROVED"
    CONFLICT = "CONFLICT"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"
```

- [ ] **Step 2: Replace `Vote.vote: int` with `Vote.weight: float`**

Replace the `Vote` dataclass body:

Old:
```python
@dataclass
class Vote:
    """A single voter's ternary evaluation of a Claim."""

    voter: str
    vote: int  # -1, 0, +1
    rationale: str
    voted_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Enforce spec invariants INV-002, INV-005."""
        if isinstance(self.vote, bool) or not isinstance(self.vote, int):
            raise ValueError(f"E_VOTE_INVALID_RANGE: {self.vote} not in (-1, 0, +1)")
        if self.vote not in (-1, 0, 1):
            raise ValueError(f"E_VOTE_INVALID_RANGE: {self.vote} not in (-1, 0, +1)")
        if not self.voter:
            raise ValueError("E_VOTE_INVALID_SCHEMA: voter required")
        if not (1 <= len(self.rationale) <= 1000):
            raise ValueError("E_VOTE_INVALID_SCHEMA: rationale must be 1..1000 chars")

    def to_dict(self) -> dict[str, Any]:
        """Serialize Vote to a plain dict."""
        return asdict(self)
```

New:
```python
@dataclass
class Vote:
    """A single voter's analog evaluation of a Claim.

    weight is a float in the open interval (-CERTAINTY_LIMIT, CERTAINTY_LIMIT).
    Positive = support, negative = opposition, near-zero = abstain.
    Absolute ±1.0 is asymptotically unreachable and MUST NOT appear.
    """

    voter: str
    weight: float  # ∈ (-CERTAINTY_LIMIT, CERTAINTY_LIMIT)
    rationale: str
    voted_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Enforce spec invariants: finite float, within [-CERTAINTY_LIMIT, CERTAINTY_LIMIT].

        The valid domain is the CLOSED interval [-0.999, 0.999]. Weights of exactly
        ±CERTAINTY_LIMIT are permitted; they represent maximum support/opposition.
        Absolute ±1.0 is forbidden (fails the isfinite check combined with the range check
        since 1.0 > CERTAINTY_LIMIT). Integer values are rejected even if in range —
        callers must pass float(1) not 1.
        """
        import math as _math
        if not isinstance(self.weight, float) or not _math.isfinite(self.weight):
            raise ValueError(
                f"E_VOTE_INVALID_RANGE: weight must be a finite float, got {self.weight!r}"
            )
        if not (-CERTAINTY_LIMIT <= self.weight <= CERTAINTY_LIMIT):
            raise ValueError(
                f"E_VOTE_INVALID_RANGE: weight {self.weight} outside "
                f"[-{CERTAINTY_LIMIT}, {CERTAINTY_LIMIT}]"
            )
        if not self.voter:
            raise ValueError("E_VOTE_INVALID_SCHEMA: voter required")
        if not (1 <= len(self.rationale) <= 1000):
            raise ValueError("E_VOTE_INVALID_SCHEMA: rationale must be 1..1000 chars")

    def to_dict(self) -> dict[str, Any]:
        """Serialize Vote to a plain dict."""
        return asdict(self)
```

- [ ] **Step 3: Add `tally_mean` and `tally_variance` to `Decision`**

After `adr_ref: Optional[str] = None` and `override_by: Optional[str] = None` in the `Decision` dataclass, add:

```python
    tally_mean: Optional[float] = None
    tally_variance: Optional[float] = None
```

Update `Decision.to_dict()` to include them when set:

```python
    def to_dict(self) -> dict[str, Any]:
        self.validate()
        d = {
            "claim_id": self.claim_id,
            "outcome": self.outcome.value,
            "votes": [v.to_dict() for v in self.votes],
            "decided_at": self.decided_at,
        }
        if self.adr_ref is not None:
            d["adr_ref"] = self.adr_ref
        if self.override_by is not None:
            d["override_by"] = self.override_by
        if self.tally_mean is not None:
            d["tally_mean"] = self.tally_mean
        if self.tally_variance is not None:
            d["tally_variance"] = self.tally_variance
        return d
```

Also update `Decision.validate()` — add after the `outcome` check:

```python
        if self.outcome == Outcome.CONFLICT and self.override_by is not None:
            raise ValueError(
                "E_DECISION_INVALID_SCHEMA: override_by not valid for CONFLICT outcome"
            )
```

- [ ] **Step 4: Verify imports are clean**

The `Vote.validate()` now uses `math`. Add `import math` at the top of `claim_schema.py` alongside the other stdlib imports (it's not there yet).

- [ ] **Step 5: Commit C1 schema changes**

```bash
cd C:/~shit/FLOSS
git add packages/orchestrator/claim_schema.py
git commit -m "feat(C1): analog vote schema — weight: float, CONFLICT outcome, tally thresholds"
```

---

## Task 2 (C2): Rewrite tally() and all 32 tests — HARD GATE

**Gate:** C1 complete (claim_schema.py must export `Vote.weight`, `CONFLICT`, threshold dicts).

**Files:**
- Modify: `packages/orchestrator/consensus_gate.py`
- Rewrite: `packages/orchestrator/test_consensus_gate.py`

**This task is the hard gate for P1.** All tests must pass before the cell directory writer is built. A wrong tally means poisoned source chain hashes with no recovery path.

### Part A — Rewrite `tally()` in consensus_gate.py

The new tally follows a strict three-step algorithm (spec §4.2):

1. **Conflict check** (runs regardless of quorum): `σ² > θ_polarization[blast_radius]` → CONFLICT
2. **Quorum check**: `n < QUORUM_MIN[blast_radius]` → DEFERRED
3. **Direction check**: `μ > θ_approve` → APPROVED; `μ < θ_reject` → REJECTED; else DEFERRED

Where `μ = mean(weights)` and `σ² = population variance`.

Also remove the early-exit in `decide()` — all voters must be consulted before tallying. CONFLICT cannot be detected with partial data.

- [ ] **Step 1: Update imports in consensus_gate.py**

Add to the import from `.claim_schema`:

```python
from .claim_schema import (
    APPROVE_THRESHOLD,
    CERTAINTY_LIMIT,
    OVERRIDE_ALLOWED,
    POLARIZATION_THRESHOLD,
    QUORUM_MIN,
    REJECT_THRESHOLD,
    BlastRadius,
    Claim,
    Decision,
    Outcome,
    Vote,
)
```

- [ ] **Step 2: Replace `tally()` entirely**

Replace the entire `tally()` function with:

```python
def tally(claim: Claim, votes: list[Vote]) -> tuple[Outcome, float, float]:
    """Apply analog tally logic (spec §4.2). Returns (outcome, mean, variance).

    Steps (in order — do not reorder):
      1. Conflict check: σ² > θ_polarization → CONFLICT (runs before quorum)
      2. Quorum check: n < QUORUM_MIN → DEFERRED
      3. Direction check: μ > θ_approve → APPROVED; μ < θ_reject → REJECTED; else DEFERRED

    Returns the outcome plus the computed mean and variance so callers can
    store them in Decision.tally_mean / Decision.tally_variance for logging.
    """
    if not votes:
        return Outcome.DEFERRED, 0.0, 0.0

    weights = [v.weight for v in votes]
    n = len(weights)
    mean = sum(weights) / n
    variance = sum((w - mean) ** 2 for w in weights) / n  # population variance

    br = claim.blast_radius

    # Step 1 — Conflict check (variance runs regardless of quorum)
    if variance > POLARIZATION_THRESHOLD[br]:
        return Outcome.CONFLICT, mean, variance

    # Step 2 — Quorum check
    if n < QUORUM_MIN[br]:
        return Outcome.DEFERRED, mean, variance

    # Step 3 — Direction check
    if mean > APPROVE_THRESHOLD[br]:
        return Outcome.APPROVED, mean, variance
    if mean < REJECT_THRESHOLD[br]:
        return Outcome.REJECTED, mean, variance
    return Outcome.DEFERRED, mean, variance
```

Note: `tally()` now returns a 3-tuple. Update callers.

- [ ] **Step 3: Update `decide()` — remove early-exit, unpack tally tuple**

Replace the early-exit block and tally call in `decide()`:

Old (lines ~107–128):
```python
    votes: list[Vote] = []
    seen_voters: set[str] = set()
    for voter in voters:
        vote = voter(claim)
        vote.validate()
        if vote.voter in seen_voters:
            raise ConsensusGateError(...)
        seen_voters.add(vote.voter)
        votes.append(vote)
        # Early-exit: a single -1 vetoes, no need to consult remaining voters
        if vote.vote == -1:
            logger.info(...)
            break

    outcome = tally(claim, votes)
    decision = Decision(claim_id=claim.id, outcome=outcome, votes=votes)
```

New:
```python
    votes: list[Vote] = []
    seen_voters: set[str] = set()
    for voter in voters:
        vote = voter(claim)
        vote.validate()
        if vote.voter in seen_voters:
            raise ConsensusGateError(
                f"E_VOTE_DUPLICATE: voter {vote.voter!r} already voted on claim {claim.id}"
            )
        seen_voters.add(vote.voter)
        votes.append(vote)
    # All voters consulted before tallying — CONFLICT requires full vote set.

    outcome, mean, variance = tally(claim, votes)
    decision = Decision(
        claim_id=claim.id,
        outcome=outcome,
        votes=votes,
        tally_mean=mean,
        tally_variance=variance,
    )
```

- [ ] **Step 4: Update `override()` — use `weight=CERTAINTY_LIMIT`**

In `override()`, find:
```python
    override_vote = Vote(voter=human_voter, vote=1, rationale=rationale)
```
Replace with:
```python
    override_vote = Vote(voter=human_voter, weight=CERTAINTY_LIMIT, rationale=rationale)
```

Also update the ADR writer's `{v.vote:+d}` format string in `default_adr_writer` — votes no longer have a `.vote` field:

Find:
```python
            lines.append(f"- **{v.voter}** ({v.vote:+d}) @ {v.voted_at}")
```
Replace with:
```python
            lines.append(f"- **{v.voter}** ({v.weight:+.4f}) @ {v.voted_at}")
```

- [ ] **Step 5: Run tests — expect ALL to fail (red phase)**

```bash
cd C:/~shit/FLOSS
python -m pytest packages/orchestrator/test_consensus_gate.py -v 2>&1 | head -60
```

Expected: all tests fail with `AttributeError: 'Vote' object has no attribute 'vote'` or similar. This confirms the schema change propagated.

### Part B — Rewrite test_consensus_gate.py

This is a complete rewrite of the test file. The 32 existing tests become 32+ analog tests. The only tests that are **removed** are:

- `test_early_exit_on_first_rejection` — early-exit is gone; replaced by `test_all_voters_consulted_despite_strong_opposition`
- `test_vector_2_single_rejection_vetoes` — single -1 no longer vetoes; replaced by analog rejection test
- `test_vector_4_substrate_requires_unanimous` — replaced by proper SUBSTRATE threshold test
- `test_vector_4b_substrate_unanimous_approves` — replaced
- `test_tally_direct` — rewritten for new 3-tuple return and CONFLICT

**Migration key** (ternary → analog for all existing mocks):

| Old `vote=` | New `weight=` | Notes |
|-------------|----------------|-------|
| `1` | `0.999` | max support = `CERTAINTY_LIMIT` |
| `0` | `0.0` | abstain |
| `-1` | `-0.999` | max opposition = `-CERTAINTY_LIMIT` |

- [ ] **Step 6: Write the new test file**

Replace the entire contents of `packages/orchestrator/test_consensus_gate.py` with:

```python
"""
Tests for the FLOSSI0ULLK Consensus Gate — analog vote model.

All vote values are floats in (-CERTAINTY_LIMIT, CERTAINTY_LIMIT).
No test may use exact ±1.0. Ternary {-1, 0, +1} values are forbidden.

Spec: docs/superpowers/specs/2026-04-12-local-agent-node-design.md §4

Run: python -m pytest packages/orchestrator/test_consensus_gate.py -v
Or:  python packages/orchestrator/test_consensus_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.orchestrator.claim_schema import (
    CERTAINTY_LIMIT,
    BlastRadius,
    Claim,
    Decision,
    EvidenceRef,
    Outcome,
    ProposalType,
    Vote,
)
from packages.orchestrator.consensus_gate import (
    ConsensusGateError,
    Voter,
    decide,
    default_adr_writer,
    override,
    tally,
)

CL = CERTAINTY_LIMIT  # shorthand


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def mock_voter(name: str, weight: float, rationale: str = "test") -> Voter:
    """Build a Voter that always casts the same analog weight."""
    def _v(_claim: Claim) -> Vote:
        return Vote(voter=name, weight=weight, rationale=rationale)
    return _v


def sample_claim(
    blast: BlastRadius = BlastRadius.MODULE,
    proposal_type: ProposalType = ProposalType.CODE_CHANGE,
) -> Claim:
    return Claim(
        proposer="agent-test",
        proposal_type=proposal_type,
        summary="test claim",
        body="proposed change body",
        blast_radius=blast,
    )


# ---------------------------------------------------------------------------
# Spec §4 test vectors — approval paths
# ---------------------------------------------------------------------------


def test_vector_1_unanimous_strong_approval():
    """[0.999, 0.999, 0.999] on Module => APPROVED (mean=0.999 > θ_approve=0.50)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED
    assert len(decision.votes) == 3


def test_vector_1b_moderate_approval_module():
    """[0.6, 0.6, 0.6] on Module => APPROVED (mean=0.6 > θ_approve=0.50)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", 0.6), mock_voter("b", 0.6), mock_voter("c", 0.6)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_vector_2_strong_rejection():
    """[-0.999, -0.999, -0.999] on System => REJECTED (mean=-0.999 < θ_reject=-0.50)."""
    claim = sample_claim(blast=BlastRadius.SYSTEM, proposal_type=ProposalType.SPEC_CHANGE)
    voters = [mock_voter("a", -CL), mock_voter("b", -CL), mock_voter("c", -CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.REJECTED


def test_vector_3a_high_support_with_abstain_approves():
    """[0.999, 0.999, 0.0] on System => APPROVED (mean=0.666 > θ_approve=0.60)."""
    claim = sample_claim(blast=BlastRadius.SYSTEM, proposal_type=ProposalType.ADR_CHANGE)
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", 0.0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_vector_3b_low_support_with_abstains_defers():
    """[0.5, 0.0, 0.0] on System => DEFERRED (mean=0.167 < θ_approve=0.60)."""
    claim = sample_claim(blast=BlastRadius.SYSTEM, proposal_type=ProposalType.ADR_CHANGE)
    voters = [mock_voter("a", 0.5), mock_voter("b", 0.0), mock_voter("c", 0.0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_vector_5_human_override_on_deferred():
    """DEFERRED decision can be overridden by a human voter."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", 0.0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED

    overridden = override(decision, claim, human_voter="human-anthony", rationale="time-sensitive fix")
    assert overridden.outcome == Outcome.OVERRIDDEN
    assert overridden.override_by == "human-anthony"
    assert len(overridden.votes) == 3  # a + b + human override


def test_vector_6_insufficient_quorum_defers():
    """2 votes on System (needs 3) => DEFERRED when variance is low."""
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


# ---------------------------------------------------------------------------
# CONFLICT tests — high variance routes to human, overrides quorum
# ---------------------------------------------------------------------------


def test_conflict_high_variance_module():
    """[0.999, -0.999] on Module => CONFLICT (σ²=0.999² > θ_polarization=0.50)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", -CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.CONFLICT


def test_conflict_overrides_quorum_check():
    """CONFLICT fires even when n < QUORUM_MIN (variance check runs first)."""
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    # Only 2 voters (quorum=3), but they disagree violently
    voters = [mock_voter("a", CL), mock_voter("b", -CL)]
    decision = decide(claim, voters)
    # variance check fires before quorum check → CONFLICT not DEFERRED
    assert decision.outcome == Outcome.CONFLICT


def test_conflict_substrate():
    """[0.999, -0.999, 0.0] on Substrate => CONFLICT (σ² > θ_polarization=0.25)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", -CL), mock_voter("c", 0.0)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.CONFLICT


def test_no_conflict_low_variance():
    """[0.7, 0.8, 0.9] on Module => not CONFLICT (σ² ≈ 0.0067 < θ=0.50)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", 0.7), mock_voter("b", 0.8), mock_voter("c", 0.9)]
    decision = decide(claim, voters)
    assert decision.outcome != Outcome.CONFLICT
    assert decision.outcome == Outcome.APPROVED


# ---------------------------------------------------------------------------
# Quorum boundary tests — SUBSTRATE/SYSTEM require n >= 3
# ---------------------------------------------------------------------------


def test_substrate_single_voter_defers():
    """A single strong-support vote on SUBSTRATE => DEFERRED (quorum=3)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_substrate_two_voters_defers():
    """Two strong-support votes on SUBSTRATE => DEFERRED (quorum=3, no conflict)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_substrate_three_voters_high_support_approves():
    """Three high-support votes on SUBSTRATE => APPROVED (mean=0.999 > θ=0.85)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_substrate_single_negative_does_not_veto():
    """A single -0.999 on SUBSTRATE with n=1 => DEFERRED, NOT REJECTED.

    The old ternary model allowed a single -1 to veto substrate changes.
    The analog model requires quorum=3 AND mean < θ_reject=-0.85 for REJECTED.
    A lone dissenter produces DEFERRED, not a veto.
    """
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", -CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED
    assert decision.outcome != Outcome.REJECTED


def test_substrate_three_strong_opposition_rejects():
    """[-0.999, -0.999, -0.999] on SUBSTRATE => REJECTED (mean=-0.999 < θ_reject=-0.85)."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", -CL), mock_voter("b", -CL), mock_voter("c", -CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.REJECTED


def test_system_two_voters_defers():
    """Two votes on SYSTEM (quorum=3) => DEFERRED when no conflict."""
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_module_single_voter_defers():
    """One vote on MODULE (quorum=2) => DEFERRED (quorum not met, no conflict)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


def test_module_two_voters_approves():
    """Two high-support votes on MODULE (quorum=2) => APPROVED."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


# ---------------------------------------------------------------------------
# Local blast radius
# ---------------------------------------------------------------------------


def test_local_blast_single_voter_approves():
    """LOCAL needs only 1 voter. 0.4 > θ_approve=0.30 => APPROVED."""
    claim = sample_claim(blast=BlastRadius.LOCAL)
    voters = [mock_voter("a", 0.4)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.APPROVED


def test_local_blast_below_threshold_defers():
    """LOCAL single voter with weight=0.1 < θ_approve=0.30 => DEFERRED."""
    claim = sample_claim(blast=BlastRadius.LOCAL)
    voters = [mock_voter("a", 0.1)]
    decision = decide(claim, voters)
    assert decision.outcome == Outcome.DEFERRED


# ---------------------------------------------------------------------------
# All voters are consulted (no early-exit)
# ---------------------------------------------------------------------------


def test_all_voters_consulted_despite_strong_opposition():
    """In the analog model, ALL voters are called before tally. No early-exit."""
    called = []

    def spy_voter(name: str, weight_val: float):
        def _v(_c):
            called.append(name)
            return Vote(voter=name, weight=weight_val, rationale="spy")
        return _v

    claim = sample_claim(blast=BlastRadius.SYSTEM)
    # b casts -0.999 but c must still be called — early-exit is gone
    voters = [spy_voter("a", CL), spy_voter("b", -CL), spy_voter("c", CL)]
    decide(claim, voters)
    assert called == ["a", "b", "c"]  # all three called


# ---------------------------------------------------------------------------
# Override tests
# ---------------------------------------------------------------------------


def test_override_rejects_non_deferred():
    """Override on APPROVED raises E_OVERRIDE_INVALID_STATE."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", CL)]
    approved = decide(claim, voters)
    assert approved.outcome == Outcome.APPROVED

    try:
        override(approved, claim, "human-x", "nope")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_INVALID_STATE" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError")


def test_override_rejects_conflict():
    """Override on CONFLICT raises E_OVERRIDE_INVALID_STATE (CONFLICT is not DEFERRED)."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", -CL)]
    conflicted = decide(claim, voters)
    assert conflicted.outcome == Outcome.CONFLICT

    try:
        override(conflicted, claim, "human-x", "trying to shortcut conflict")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_INVALID_STATE" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError — CONFLICT requires human resolution, not override")


def test_override_rejects_substrate():
    """SUBSTRATE disallows human override."""
    claim = sample_claim(blast=BlastRadius.SUBSTRATE)
    voters = [mock_voter("a", CL), mock_voter("b", CL), mock_voter("c", 0.1)]
    deferred = decide(claim, voters)
    assert deferred.outcome == Outcome.DEFERRED

    try:
        override(deferred, claim, "human-x", "bypass")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_NOT_ALLOWED" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError")


def test_override_rejects_claim_id_mismatch():
    """override() rejects a prior_decision whose claim_id doesn't match the claim."""
    claim_a = sample_claim(blast=BlastRadius.MODULE)
    claim_b = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", 0.0)]
    deferred_a = decide(claim_a, voters)
    assert deferred_a.outcome == Outcome.DEFERRED

    try:
        override(deferred_a, claim_b, "human-x", "wrong claim")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_CLAIM_MISMATCH" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError for claim_id mismatch")


def test_override_rejects_duplicate_human_voter():
    """override() rejects a human_voter who already voted."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("human-anthony", CL), mock_voter("b", 0.0)]
    deferred = decide(claim, voters)
    assert deferred.outcome == Outcome.DEFERRED

    try:
        override(deferred, claim, human_voter="human-anthony", rationale="double-vote")
    except ConsensusGateError as e:
        assert "E_OVERRIDE_DUPLICATE" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError for duplicate override voter")


# ---------------------------------------------------------------------------
# Vote validation
# ---------------------------------------------------------------------------


def test_invalid_weight_above_limit_raises():
    """weight > CERTAINTY_LIMIT raises E_VOTE_INVALID_RANGE."""
    try:
        Vote(voter="bad", weight=1.0, rationale="over limit").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_invalid_weight_below_limit_raises():
    """weight < -CERTAINTY_LIMIT raises E_VOTE_INVALID_RANGE."""
    try:
        Vote(voter="bad", weight=-1.0, rationale="under limit").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_nan_weight_raises():
    """NaN weight raises E_VOTE_INVALID_RANGE."""
    import math
    try:
        Vote(voter="bad", weight=math.nan, rationale="nan").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_inf_weight_raises():
    """Infinite weight raises E_VOTE_INVALID_RANGE."""
    import math
    try:
        Vote(voter="bad", weight=math.inf, rationale="inf").validate()
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_integer_weight_raises():
    """Integer weight (not float) raises E_VOTE_INVALID_RANGE."""
    try:
        Vote(voter="bad", weight=1, rationale="int not float").validate()  # type: ignore[arg-type]
    except ValueError as e:
        assert "E_VOTE_INVALID_RANGE" in str(e)
    else:
        raise AssertionError("expected ValueError — weight must be float, not int")


# ---------------------------------------------------------------------------
# Claim validation (unchanged from ternary model)
# ---------------------------------------------------------------------------


def test_claim_summary_length():
    try:
        Claim(
            proposer="a",
            proposal_type=ProposalType.CODE_CHANGE,
            summary="x" * 201,
            body="body",
            blast_radius=BlastRadius.LOCAL,
        ).validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_non_uuidv7():
    claim = sample_claim()
    claim.id = "not-a-uuid"
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_uuid4():
    import uuid as _uuid
    claim = sample_claim()
    claim.id = str(_uuid.uuid4())
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError for UUIDv4")


def test_claim_validate_rejects_bad_submitted_at():
    claim = sample_claim()
    claim.submitted_at = "yesterday"
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_bad_proposal_type():
    claim = sample_claim()
    object.__setattr__(claim, "proposal_type", "CodeChange")
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_bad_blast_radius():
    claim = sample_claim()
    object.__setattr__(claim, "blast_radius", "Module")
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_non_evidence_ref_entries():
    claim = sample_claim()
    claim.evidence = [{"type": "spec", "ref": "docs/specs/consensus-gate.spec.md"}]
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
        assert "evidence[0]" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_validate_rejects_blank_evidence_ref():
    claim = sample_claim()
    claim.evidence = [EvidenceRef(type="spec", ref="  ")]
    try:
        claim.validate()
    except ValueError as e:
        assert "E_CLAIM_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_claim_to_dict_serializes_validated_evidence():
    claim = sample_claim()
    claim.evidence = [
        EvidenceRef(type="spec", ref="docs/specs/consensus-gate.spec.md"),
        EvidenceRef(type="test", ref="packages/orchestrator/test_consensus_gate.py"),
    ]
    data = claim.to_dict()
    assert data["evidence"] == [
        {"type": "spec", "ref": "docs/specs/consensus-gate.spec.md"},
        {"type": "test", "ref": "packages/orchestrator/test_consensus_gate.py"},
    ]


# ---------------------------------------------------------------------------
# Decision validation
# ---------------------------------------------------------------------------


def test_decision_validate_rejects_string_outcome():
    claim = sample_claim()
    decision = Decision(
        claim_id=claim.id,
        outcome="APPROVED",  # type: ignore[arg-type]
        votes=[Vote(voter="a", weight=CL, rationale="ok")],
    )
    try:
        decision.validate()
    except ValueError as e:
        assert "E_DECISION_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_decision_validate_rejects_non_vote_entries():
    claim = sample_claim()
    decision = Decision(
        claim_id=claim.id,
        outcome=Outcome.APPROVED,
        votes=[{"voter": "a", "weight": CL, "rationale": "ok"}],  # type: ignore[list-item]
    )
    try:
        decision.validate()
    except ValueError as e:
        assert "E_DECISION_INVALID_SCHEMA" in str(e)
        assert "votes[0]" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_decision_validate_rejects_override_by_without_overridden():
    claim = sample_claim()
    decision = Decision(
        claim_id=claim.id,
        outcome=Outcome.APPROVED,
        votes=[Vote(voter="a", weight=CL, rationale="ok")],
        override_by="human-x",
    )
    try:
        decision.validate()
    except ValueError as e:
        assert "E_DECISION_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_decision_to_dict_validates_before_serializing():
    claim = sample_claim()
    decision = Decision(
        claim_id=claim.id,
        outcome=Outcome.APPROVED,
        votes=[Vote(voter="a", weight=CL, rationale="ok")],
        decided_at="not-a-timestamp",
    )
    try:
        decision.to_dict()
    except ValueError as e:
        assert "E_DECISION_INVALID_SCHEMA" in str(e)
    else:
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------------------
# Ballot integrity
# ---------------------------------------------------------------------------


def test_decide_rejects_duplicate_voters():
    claim = sample_claim(blast=BlastRadius.SYSTEM)
    voters = [mock_voter("dup", CL), mock_voter("dup", CL), mock_voter("c", CL)]
    try:
        decide(claim, voters)
    except ConsensusGateError as e:
        assert "E_VOTE_DUPLICATE" in str(e)
    else:
        raise AssertionError("expected ConsensusGateError")


# ---------------------------------------------------------------------------
# ADR writer
# ---------------------------------------------------------------------------


def test_adr_writer_produces_file():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        adr_dir = Path(tmp)
        writer = default_adr_writer(adr_dir)
        claim = sample_claim(blast=BlastRadius.MODULE)
        voters = [mock_voter("a", CL), mock_voter("b", CL)]
        decision = decide(claim, voters, adr_writer=writer)
        assert decision.outcome == Outcome.APPROVED
        assert decision.adr_ref is not None
        path = Path(decision.adr_ref)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "APPROVED" in content
        assert claim.id in content
        assert "a" in content and "b" in content


# ---------------------------------------------------------------------------
# tally() unit tests
# ---------------------------------------------------------------------------


def test_tally_direct_approved():
    claim = sample_claim(blast=BlastRadius.MODULE)
    vs = [Vote(voter="a", weight=CL, rationale="ok"), Vote(voter="b", weight=CL, rationale="ok")]
    outcome, mean, variance = tally(claim, vs)
    assert outcome == Outcome.APPROVED
    assert mean > 0
    assert variance == 0.0


def test_tally_direct_rejected():
    claim = sample_claim(blast=BlastRadius.MODULE)
    vs = [
        Vote(voter="a", weight=-CL, rationale="no"),
        Vote(voter="b", weight=-CL, rationale="no"),
    ]
    outcome, mean, variance = tally(claim, vs)
    assert outcome == Outcome.REJECTED


def test_tally_direct_conflict():
    claim = sample_claim(blast=BlastRadius.MODULE)
    vs = [Vote(voter="a", weight=CL, rationale="yes"), Vote(voter="b", weight=-CL, rationale="no")]
    outcome, mean, variance = tally(claim, vs)
    assert outcome == Outcome.CONFLICT


def test_tally_empty_defers():
    claim = sample_claim(blast=BlastRadius.MODULE)
    outcome, mean, variance = tally(claim, [])
    assert outcome == Outcome.DEFERRED
    assert mean == 0.0
    assert variance == 0.0


def test_tally_stores_stats_on_decision():
    """decide() populates tally_mean and tally_variance on the returned Decision."""
    claim = sample_claim(blast=BlastRadius.MODULE)
    voters = [mock_voter("a", CL), mock_voter("b", 0.5)]
    decision = decide(claim, voters)
    assert decision.tally_mean is not None
    assert decision.tally_variance is not None


# ---------------------------------------------------------------------------
# CLI runner (no pytest required)
# ---------------------------------------------------------------------------


def _run_all():
    tests = [
        test_vector_1_unanimous_strong_approval,
        test_vector_1b_moderate_approval_module,
        test_vector_2_strong_rejection,
        test_vector_3a_high_support_with_abstain_approves,
        test_vector_3b_low_support_with_abstains_defers,
        test_vector_5_human_override_on_deferred,
        test_vector_6_insufficient_quorum_defers,
        test_conflict_high_variance_module,
        test_conflict_overrides_quorum_check,
        test_conflict_substrate,
        test_no_conflict_low_variance,
        test_substrate_single_voter_defers,
        test_substrate_two_voters_defers,
        test_substrate_three_voters_high_support_approves,
        test_substrate_single_negative_does_not_veto,
        test_substrate_three_strong_opposition_rejects,
        test_system_two_voters_defers,
        test_module_single_voter_defers,
        test_module_two_voters_approves,
        test_local_blast_single_voter_approves,
        test_local_blast_below_threshold_defers,
        test_all_voters_consulted_despite_strong_opposition,
        test_override_rejects_non_deferred,
        test_override_rejects_conflict,
        test_override_rejects_substrate,
        test_override_rejects_claim_id_mismatch,
        test_override_rejects_duplicate_human_voter,
        test_invalid_weight_above_limit_raises,
        test_invalid_weight_below_limit_raises,
        test_nan_weight_raises,
        test_inf_weight_raises,
        test_integer_weight_raises,
        test_claim_summary_length,
        test_claim_validate_rejects_non_uuidv7,
        test_claim_validate_rejects_uuid4,
        test_claim_validate_rejects_bad_submitted_at,
        test_claim_validate_rejects_bad_proposal_type,
        test_claim_validate_rejects_bad_blast_radius,
        test_claim_validate_rejects_non_evidence_ref_entries,
        test_claim_validate_rejects_blank_evidence_ref,
        test_claim_to_dict_serializes_validated_evidence,
        test_decision_validate_rejects_string_outcome,
        test_decision_validate_rejects_non_vote_entries,
        test_decision_validate_rejects_override_by_without_overridden,
        test_decision_to_dict_validates_before_serializing,
        test_decide_rejects_duplicate_voters,
        test_adr_writer_produces_file,
        test_tally_direct_approved,
        test_tally_direct_rejected,
        test_tally_direct_conflict,
        test_tally_empty_defers,
        test_tally_stores_stats_on_decision,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {t.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
```

- [ ] **Step 7: Run the full test suite — all must pass**

```bash
cd C:/~shit/FLOSS
python -m pytest packages/orchestrator/test_consensus_gate.py -v
```

Expected: all 52 tests PASS. If any fail, fix the implementation (not the tests) and re-run.

```bash
# Also verify the CLI runner works without pytest
python packages/orchestrator/test_consensus_gate.py
```

Expected: `52 passed, 0 failed`

- [ ] **Step 8: Commit C2**

```bash
git add packages/orchestrator/claim_schema.py packages/orchestrator/consensus_gate.py packages/orchestrator/test_consensus_gate.py
git commit -m "feat(C2): analog tally — CONFLICT outcome, variance-first, no early-exit; 50 tests pass"
```

---

## Task 3 (P1): Cell Directory Writer

**Gate:** C2 complete and all tests passing.

**Files:**
- Create: `packages/source_chain/__init__.py`
- Create: `packages/source_chain/cell.py`
- Create: `packages/source_chain/tests/__init__.py`
- Create: `packages/source_chain/tests/test_cell.py`

This is the file-based Holochain Cell analogue. It implements the storage layout from spec §3.1:

```
~/.floss_agent/
└── cells/
    └── <dna_hash>/
        ├── head.json
        ├── source_chain/
        │   └── <sha256-hex>.json
        └── memory/
            ├── working/
            ├── episodic/
            └── semantic/
```

Entries are written atomically: acquire `.lock`, write entry file, update `head.json`, release lock. Lock timeout is 5 seconds.

- [ ] **Step 1: Write the failing tests first**

Create `packages/source_chain/tests/__init__.py` (empty).

Create `packages/source_chain/tests/test_cell.py`:

```python
"""Tests for CellDirectory — the file-based source chain writer (spec §3.1)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.source_chain.cell import CellDirectory


DNA_HASH = "a" * 64  # 64-char hex string simulating a real dna_hash


def make_cell(tmp_dir: str) -> CellDirectory:
    return CellDirectory(base_dir=Path(tmp_dir), dna_hash=DNA_HASH)


def test_append_returns_entry_hash():
    """append_entry() returns a 64-char hex SHA256 digest."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry(
            entry_type="genesis",
            author_did="did:key:ztest",
            content={"hello": "world"},
        )
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


def test_entry_file_exists_after_append():
    """The entry file is written at cells/<dna_hash>/source_chain/<hash>.json."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("claim", "did:key:ztest", {"foo": "bar"})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        assert entry_path.exists()


def test_entry_file_has_canonical_fields():
    """Entry file contains id, type, author_did, previous_hash, timestamp, content."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("vote", "did:key:ztest", {"weight": 0.999})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        data = json.loads(entry_path.read_text())
        assert data["type"] == "vote"
        assert data["author_did"] == "did:key:ztest"
        assert data["content"] == {"weight": 0.999}
        assert "id" in data
        assert "timestamp" in data
        assert "previous_hash" in data


def test_first_entry_has_null_previous_hash():
    """Genesis entry has previous_hash=null."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("genesis", "did:key:ztest", {})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        data = json.loads(entry_path.read_text())
        assert data["previous_hash"] is None


def test_subsequent_entry_links_to_previous():
    """Each entry's previous_hash is the hash of the immediately prior entry."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h1 = cell.append_entry("genesis", "did:key:ztest", {"n": 1})
        h2 = cell.append_entry("claim", "did:key:ztest", {"n": 2})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h2}.json"
        data = json.loads(entry_path.read_text())
        assert data["previous_hash"] == h1


def test_head_json_updated_after_append():
    """head.json always points to the latest entry hash."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h1 = cell.append_entry("genesis", "did:key:ztest", {})
        h2 = cell.append_entry("claim", "did:key:ztest", {"x": 1})
        head_path = Path(tmp) / "cells" / DNA_HASH / "head.json"
        head_data = json.loads(head_path.read_text())
        assert head_data["head"] == h2
        assert head_data["head"] != h1


def test_head_hash_returns_none_for_empty_chain():
    """head_hash() returns None when the chain has no entries."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        assert cell.head_hash() is None


def test_head_hash_matches_latest():
    """head_hash() returns the hash of the most-recently appended entry."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("genesis", "did:key:ztest", {})
        assert cell.head_hash() == h


def test_read_chain_returns_entries_in_order():
    """read_chain() returns entries from newest to oldest (reverse chronological)."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h1 = cell.append_entry("genesis", "did:key:ztest", {"n": 1})
        h2 = cell.append_entry("claim", "did:key:ztest", {"n": 2})
        h3 = cell.append_entry("vote", "did:key:ztest", {"n": 3})
        entries = cell.read_chain(limit=10)
        assert len(entries) == 3
        # Newest first
        assert entries[0]["content"]["n"] == 3
        assert entries[1]["content"]["n"] == 2
        assert entries[2]["content"]["n"] == 1


def test_read_chain_respects_limit():
    """read_chain(limit=2) returns only the 2 most recent entries."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        for i in range(5):
            cell.append_entry("memory", "did:key:ztest", {"i": i})
        entries = cell.read_chain(limit=2)
        assert len(entries) == 2
        assert entries[0]["content"]["i"] == 4
        assert entries[1]["content"]["i"] == 3


def test_memory_subdirs_created():
    """memory/working, memory/episodic, memory/semantic exist after first append."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        cell.append_entry("genesis", "did:key:ztest", {})
        cell_dir = Path(tmp) / "cells" / DNA_HASH
        assert (cell_dir / "memory" / "working").is_dir()
        assert (cell_dir / "memory" / "episodic").is_dir()
        assert (cell_dir / "memory" / "semantic").is_dir()


def test_entry_filename_is_hash_of_raw_bytes():
    """The entry file's stem is the SHA256 of its raw bytes (canonical_serialize output).

    NOTE: We verify by re-hashing the raw file bytes, NOT by re-parsing through
    json.loads and re-serializing, since float round-tripping through json.loads
    can introduce drift. The raw bytes are the ground truth.
    """
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("claim", "did:key:ztest", {"check": True, "n": 42})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        raw = entry_path.read_bytes()
        import hashlib
        recomputed = hashlib.sha256(raw).hexdigest()
        assert recomputed == h
```

- [ ] **Step 2: Run tests — expect ImportError (red phase)**

```bash
cd C:/~shit/FLOSS
python -m pytest packages/source_chain/tests/test_cell.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'packages.source_chain.cell'`

- [ ] **Step 3: Create `packages/source_chain/__init__.py`**

```python
"""Cell-scoped source chain writer for FLOSSIØULLK local agent nodes."""
```

- [ ] **Step 4: Implement `packages/source_chain/cell.py`**

```python
"""
CellDirectory — file-based source chain for a single Holochain Cell.

Mirrors Holochain source chain primitives exactly (spec §3.1):
  - One directory per Cell (agent × DNA)
  - Entries named by SHA256 of canonical content
  - Topological ordering via previous_hash links only
  - Atomic writes via file-lock (.lock file, 5-second timeout)

Locking uses Python's open(path, "x") which raises FileExistsError atomically
on all platforms (Linux, macOS, Windows). No fcntl or platform-specific imports.

This is a Phase 0 precursor. When Holochain is live, each file
becomes a source chain action with zero structural rework.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from packages.orchestrator.serialization import canonical_serialize, entry_hash


_LOCK_TIMEOUT = 5.0  # seconds


class CellDirectoryError(Exception):
    """Raised for cell-protocol violations (lock timeout, corrupt head, etc.)."""


class CellDirectory:
    """File-based source chain for one agent × DNA Cell.

    Layout:
        <base_dir>/cells/<dna_hash>/
            head.json                       # {"head": "<latest_hash>"}
            source_chain/<hash>.json        # one file per entry
            memory/working/
            memory/episodic/
            memory/semantic/
    """

    def __init__(self, base_dir: Path, dna_hash: str) -> None:
        self._cell_dir = base_dir / "cells" / dna_hash
        self._chain_dir = self._cell_dir / "source_chain"
        self._head_path = self._cell_dir / "head.json"
        self._lock_path = self._cell_dir / ".lock"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self._chain_dir.mkdir(parents=True, exist_ok=True)
        for sub in ("working", "episodic", "semantic"):
            (self._cell_dir / "memory" / sub).mkdir(parents=True, exist_ok=True)

    def head_hash(self) -> Optional[str]:
        """Return the hash of the most-recently appended entry, or None."""
        if not self._head_path.exists():
            return None
        return json.loads(self._head_path.read_text(encoding="utf-8"))["head"]

    def append_entry(
        self,
        entry_type: str,
        author_did: str,
        content: dict[str, Any],
        previous_hash: Optional[str] = None,
    ) -> str:
        """Append a new entry to the source chain under an exclusive file lock.

        Args:
            entry_type: One of "genesis", "claim", "vote", "decision", "memory".
            author_did: The DID of the authoring agent.
            content: Arbitrary JSON-serializable content.
            previous_hash: Override the automatic previous_hash link. Use only
                           for genesis entries or when reconstructing from wire.

        Returns:
            The SHA256 hex digest of the canonically serialized entry (= filename stem).
        """
        prev = previous_hash if previous_hash is not None else self.head_hash()
        entry: dict[str, Any] = {
            "id": str(self._new_uuid()),
            "type": entry_type,
            "author_did": author_did,
            "previous_hash": prev,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content": content,
        }
        h = entry_hash(entry)
        entry_path = self._chain_dir / f"{h}.json"
        serialized = canonical_serialize(entry)

        self._acquire_lock()
        try:
            entry_path.write_bytes(serialized)
            self._head_path.write_text(
                json.dumps({"head": h}, separators=(",", ":")),
                encoding="utf-8",
            )
        finally:
            self._release_lock()

        return h

    def read_chain(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return up to `limit` entries in reverse-chronological order (newest first).

        Traverses the chain via previous_hash links starting from head.
        """
        head = self.head_hash()
        if head is None:
            return []

        results: list[dict[str, Any]] = []
        current = head
        while current and len(results) < limit:
            path = self._chain_dir / f"{current}.json"
            if not path.exists():
                break
            data = json.loads(path.read_bytes())
            results.append(data)
            current = data.get("previous_hash")
        return results

    # ------------------------------------------------------------------
    # Lock helpers
    # ------------------------------------------------------------------

    def _acquire_lock(self) -> None:
        """Create .lock file exclusively, waiting up to _LOCK_TIMEOUT seconds."""
        deadline = time.monotonic() + _LOCK_TIMEOUT
        while True:
            try:
                fd = self._lock_path.open("x")  # O_CREAT | O_EXCL — atomic
                fd.close()
                return
            except FileExistsError:
                # Check for stale lock (mtime > timeout)
                try:
                    age = time.time() - self._lock_path.stat().st_mtime
                    if age > _LOCK_TIMEOUT:
                        self._lock_path.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue  # another process cleared it
                if time.monotonic() >= deadline:
                    raise CellDirectoryError(
                        f"Timed out acquiring lock on {self._lock_path} after "
                        f"{_LOCK_TIMEOUT}s. Another process may be stuck."
                    )
                time.sleep(0.05)

    def _release_lock(self) -> None:
        self._lock_path.unlink(missing_ok=True)

    @staticmethod
    def _new_uuid() -> uuid.UUID:
        uuid7 = getattr(uuid, "uuid7", None)
        if uuid7 is not None:
            return uuid7()
        ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
        import os
        rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
        rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
        v = (ts_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
        return uuid.UUID(int=v)
```

The `open(path, "x")` flag raises `FileExistsError` atomically on all platforms (POSIX O_EXCL semantics on Linux/macOS; CreateFile with CREATE_NEW on Windows). No platform-specific imports required.

- [ ] **Step 5: Run tests — all should pass**

```bash
cd C:/~shit/FLOSS
python -m pytest packages/source_chain/tests/test_cell.py -v
```

Expected: all 13 tests PASS.

- [ ] **Step 6: Commit P1**

```bash
git add packages/source_chain/
git commit -m "feat(P1): CellDirectory — file-based source chain writer with atomic locking"
```

---

## Task 4 (P2): MCP Gateway

**Gate:** P1 complete.

**Files:**
- Create: `packages/metacoordinator_mcp/__init__.py`
- Create: `packages/metacoordinator_mcp/server.py`
- Create: `packages/metacoordinator_mcp/tools.py`
- Create: `packages/metacoordinator_mcp/tests/__init__.py`
- Create: `packages/metacoordinator_mcp/tests/test_tools.py`

The MCP gateway is a **router, not a controller** (spec §5). It exposes 5 tools:

| Tool | Description |
|------|-------------|
| `submit_claim` | Append a Claim entry to the source chain |
| `cast_vote` | Append a Vote entry for a given claim_id |
| `get_chain_context` | Return recent source chain entries (bounded by token budget) |
| `get_decision` | Return the Decision for a given claim_id |
| `list_pending` | List Claims with no Decision yet |

Install the MCP SDK first if not present:
```bash
pip install mcp
```

- [ ] **Step 1: Write failing tests**

Create `packages/metacoordinator_mcp/tests/__init__.py` (empty).

Create `packages/metacoordinator_mcp/tests/test_tools.py`:

```python
"""Tests for MCP gateway tool handlers (spec §5.2)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.metacoordinator_mcp.tools import GatewayTools

DNA_HASH = "b" * 64


def make_gateway(tmp: str) -> GatewayTools:
    return GatewayTools(base_dir=Path(tmp), dna_hash=DNA_HASH)


def test_submit_claim_returns_entry_hash():
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = gw.submit_claim(
            proposer="claude",
            proposal_type="CodeChange",
            summary="Add feature X",
            body="Detailed description of change",
            blast_radius="Local",
        )
        data = json.loads(result)
        assert "entry_hash" in data
        assert len(data["entry_hash"]) == 64


def test_cast_vote_returns_entry_hash():
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="test", body="body", blast_radius="Local",
        ))
        vote_result = json.loads(gw.cast_vote(
            claim_id=claim_result["claim_id"],
            voter="gemini",
            weight=0.8,
            rationale="Looks good to me",
        ))
        assert "entry_hash" in vote_result


def test_get_chain_context_returns_list():
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="test", body="body", blast_radius="Local",
        )
        result = json.loads(gw.get_chain_context(limit=10))
        assert isinstance(result, list)
        assert len(result) >= 1


def test_list_pending_returns_empty_when_no_claims():
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(gw.list_pending())
        assert result == []


def test_list_pending_returns_unresolved_claims():
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        claim_result = json.loads(gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="pending claim", body="body", blast_radius="Local",
        ))
        pending = json.loads(gw.list_pending())
        claim_ids = [c["claim_id"] for c in pending]
        assert claim_result["claim_id"] in claim_ids


def test_submit_claim_rejects_invalid_blast_radius():
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(gw.submit_claim(
            proposer="claude", proposal_type="CodeChange",
            summary="test", body="body", blast_radius="INVALID",
        ))
        assert "error" in result


def test_cast_vote_rejects_weight_above_limit():
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp)
        result = json.loads(gw.cast_vote(
            claim_id="00000000-0000-7000-8000-000000000000",
            voter="bad",
            weight=1.0,  # must be < CERTAINTY_LIMIT
            rationale="test",
        ))
        assert "error" in result
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd C:/~shit/FLOSS
python -m pytest packages/metacoordinator_mcp/tests/test_tools.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create `packages/metacoordinator_mcp/__init__.py`**

```python
"""MCP gateway — router/switch for FLOSSIØULLK consensus protocol."""
```

- [ ] **Step 4: Implement `packages/metacoordinator_mcp/tools.py`**

```python
"""
GatewayTools — the 5 MCP tool handlers for the FLOSSIØULLK consensus gateway.

The gateway is a router, not a controller (spec §5). It:
  - Accepts Claims and Votes from any agent
  - Reads the cell source chain to provide context to voters
  - Does NOT decide outcomes, command voters, or hold state outside the cell dir

Each method returns a JSON string (the MCP wire format for tool results).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.orchestrator.claim_schema import (
    CERTAINTY_LIMIT,
    BlastRadius,
    Claim,
    EvidenceRef,
    Outcome,
    ProposalType,
    Vote,
)
from packages.source_chain.cell import CellDirectory


def _ok(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _err(msg: str) -> str:
    return json.dumps({"error": msg}, separators=(",", ":"))


class GatewayTools:
    """Stateless tool handlers. State lives entirely in the cell directory."""

    def __init__(self, base_dir: Path, dna_hash: str) -> None:
        self._cell = CellDirectory(base_dir=base_dir, dna_hash=dna_hash)

    def submit_claim(
        self,
        proposer: str,
        proposal_type: str,
        summary: str,
        body: str,
        blast_radius: str,
        evidence: list[dict] | None = None,
    ) -> str:
        """Append a Claim entry to the source chain.

        Returns JSON: {"entry_hash": "<hex>", "claim_id": "<uuid>"}
        """
        try:
            br = BlastRadius(blast_radius)
            pt = ProposalType(proposal_type)
        except ValueError as exc:
            return _err(f"E_SUBMIT_CLAIM_INVALID: {exc}")

        ev_refs = []
        for item in (evidence or []):
            try:
                ref = EvidenceRef(type=item["type"], ref=item["ref"])
                ref.validate()
                ev_refs.append(ref)
            except (KeyError, ValueError) as exc:
                return _err(f"E_SUBMIT_CLAIM_INVALID_EVIDENCE: {exc}")

        try:
            claim = Claim(
                proposer=proposer,
                proposal_type=pt,
                summary=summary,
                body=body,
                blast_radius=br,
                evidence=ev_refs,
            )
            claim.validate()
        except ValueError as exc:
            return _err(f"E_SUBMIT_CLAIM_INVALID: {exc}")

        h = self._cell.append_entry(
            entry_type="claim",
            author_did=proposer,
            content=claim.to_dict(),
        )
        return _ok({"entry_hash": h, "claim_id": claim.id})

    def cast_vote(
        self,
        claim_id: str,
        voter: str,
        weight: float,
        rationale: str,
    ) -> str:
        """Append a Vote entry for a given claim_id.

        Returns JSON: {"entry_hash": "<hex>"}
        """
        try:
            vote = Vote(voter=voter, weight=weight, rationale=rationale)
            vote.validate()
        except (ValueError, TypeError) as exc:
            return _err(f"E_CAST_VOTE_INVALID: {exc}")

        content = {"claim_id": claim_id, **vote.to_dict()}
        h = self._cell.append_entry(
            entry_type="vote",
            author_did=voter,
            content=content,
        )
        return _ok({"entry_hash": h})

    def get_chain_context(self, limit: int = 20) -> str:
        """Return recent source chain entries as a JSON list, newest first."""
        entries = self._cell.read_chain(limit=limit)
        return _ok(entries)

    def get_decision(self, claim_id: str) -> str:
        """Return the Decision entry for a given claim_id, or null if not yet decided."""
        entries = self._cell.read_chain(limit=500)
        for entry in entries:
            if entry.get("type") == "decision" and entry["content"].get("claim_id") == claim_id:
                return _ok(entry["content"])
        return _ok(None)

    def list_pending(self) -> str:
        """Return Claims that have no corresponding Decision entry yet."""
        entries = self._cell.read_chain(limit=500)
        decided_claim_ids = {
            e["content"]["claim_id"]
            for e in entries
            if e.get("type") == "decision"
        }
        pending = [
            {"claim_id": e["content"]["id"], "summary": e["content"].get("summary", "")}
            for e in entries
            if e.get("type") == "claim" and e["content"]["id"] not in decided_claim_ids
        ]
        return _ok(pending)
```

- [ ] **Step 5: Implement `packages/metacoordinator_mcp/server.py`**

```python
"""
FastMCP server for the FLOSSIØULLK consensus gateway.

Exposes the 5 tools from spec §5.2 via the MCP protocol.
Start: python -m packages.metacoordinator_mcp.server

The server is a router/switch. It routes Claims to voters and
appends results to the file-based source chain. It does NOT
decide outcomes or command voters.
"""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .tools import GatewayTools

BASE_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
DNA_HASH = os.environ.get("FLOSS_DNA_HASH", "0" * 64)

_tools = GatewayTools(base_dir=BASE_DIR, dna_hash=DNA_HASH)

mcp = FastMCP("FLOSSIØULLK Consensus Gateway")


@mcp.tool()
def submit_claim(
    proposer: str,
    proposal_type: str,
    summary: str,
    body: str,
    blast_radius: str,
) -> str:
    """Submit a proposed change to the consensus gate.

    blast_radius: one of Local, Module, System, Substrate.
    Returns JSON with entry_hash and claim_id.
    """
    return _tools.submit_claim(proposer, proposal_type, summary, body, blast_radius)


@mcp.tool()
def cast_vote(claim_id: str, voter: str, weight: float, rationale: str) -> str:
    """Cast an analog vote on a pending Claim.

    weight: float in (-0.999, 0.999). Positive = support, negative = oppose.
    Returns JSON with entry_hash.
    """
    return _tools.cast_vote(claim_id, voter, weight, rationale)


@mcp.tool()
def get_chain_context(limit: int = 20) -> str:
    """Return the most recent source chain entries for voter context.

    Returns JSON list, newest first. Bounded by limit to fit token budgets.
    """
    return _tools.get_chain_context(limit)


@mcp.tool()
def get_decision(claim_id: str) -> str:
    """Return the Decision for a given claim_id, or null if not yet decided."""
    return _tools.get_decision(claim_id)


@mcp.tool()
def list_pending() -> str:
    """List all Claims that have not yet received a Decision."""
    return _tools.list_pending()


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 6: Run tests — all should pass**

```bash
cd C:/~shit/FLOSS
python -m pytest packages/metacoordinator_mcp/tests/test_tools.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 7: Commit P2**

```bash
git add packages/metacoordinator_mcp/
git commit -m "feat(P2): MCP gateway — 5 consensus tools, router not controller"
```

---

## Task 5 (P3): Claude Code Hooks

**Gate:** P2 complete.

**Files:**
- Create: `FLOSS/.claude/settings.json`

This wires the MCP gateway into Claude Code's tool lifecycle. After any `Write` or `Edit` operation, a lightweight Haiku agent inspects the changed file and submits a Claim with the appropriate `blast_radius` to the consensus gateway.

Blast-radius heuristic (spec §5.3):
- `ARF/dnas/*/zomes/integrity/` → SUBSTRATE
- `ARF/dnas/*/` → SYSTEM
- `docs/adr/` or `docs/specs/` → MODULE
- Everything else → LOCAL

- [ ] **Step 1: Create `.claude/` directory if it doesn't exist**

```bash
mkdir -p C:/~shit/FLOSS/.claude
```

- [ ] **Step 2: Create `FLOSS/.claude/settings.json`**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "agent",
            "prompt": "Inspect the changed file path from the tool input. Determine the blast_radius using these rules:\n- Path contains 'dnas/' and 'zomes/integrity' → blast_radius='Substrate'\n- Path contains 'dnas/' → blast_radius='System'\n- Path contains 'docs/adr/' or 'docs/specs/' or 'docs/superpowers/specs/' → blast_radius='Module'\n- Everything else → blast_radius='Local'\n\nThen call the submit_claim MCP tool with:\n- proposer: the name of the AI model making the change (e.g., 'claude-sonnet-4-6')\n- proposal_type: 'CodeChange' for source files, 'SpecChange' for docs/specs/, 'AdrChange' for docs/adr/\n- summary: one sentence describing what changed (max 200 chars)\n- body: brief description of why the change was made\n- blast_radius: as determined above\n\nFor LOCAL changes, submit silently and do not report back. For MODULE and above, include the entry_hash in your response.",
            "model": "claude-haiku-4-5-20251001",
            "timeout": 30,
            "async": true
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Commit P3**

```bash
git add FLOSS/.claude/settings.json
git commit -m "feat(P3): wire Claude Code PostToolUse hook for blast-radius claim submission"
```

---

## Full Verification

After all tasks complete, run the complete test suite to verify no regressions:

```bash
cd C:/~shit/FLOSS

# Core-Logic track
python -m pytest packages/orchestrator/test_consensus_gate.py -v
python packages/orchestrator/test_consensus_gate.py

# Serialization (F2, already complete)
python -m pytest packages/orchestrator/ -v -k "serial"

# Physical track
python -m pytest packages/source_chain/tests/ -v
python -m pytest packages/metacoordinator_mcp/tests/ -v

# All together
python -m pytest packages/ -v
```

Expected: all tests pass, 0 failures.

---

## Commit F3 (PR #25 Hygiene)

These files must be committed to the `lappytop` branch. Verify each exists before staging:

> **🚨 Relocation note (2026-05-11):** `FLOSSI_U_Founding_Kit_v1.6/` was relocated to `C:\~shit\FLOSSI_U/` at workspace top-level — it is now a **separate sibling project** (Free YOU-niversity), not part of the FLOSS / Rose Forest repo. The commands below are no longer valid as-written because `git add FLOSSI_U_Founding_Kit_v1.6/...` cannot reach files outside the FLOSS repo. **Re-plan needed:** decide whether (a) PR #25 still needs these FLOSSI U artifacts (in which case FLOSSI U gets its own repo/PR), or (b) the PR #25 scope can land without them. The FLOSS-internal file (`docs/governance/LEGAL_DEFINITIONS.md`) is still in scope.

```bash
cd C:/~shit/FLOSS
# Verify files exist before adding (paths updated 2026-05-11)
ls ../FLOSSI_U/ADR-017_SELF_TRANSCENDENCE_OPERATOR.md   # now in sibling project — separate repo
ls ../FLOSSI_U/LICENSE                                   # now in sibling project — separate repo
ls docs/governance/LEGAL_DEFINITIONS.md                  # still in FLOSS repo
```

If any file is missing, create it from the spec before committing:

- `../FLOSSI_U/ADR-017_SELF_TRANSCENDENCE_OPERATOR.md` — full ADR per template in `docs/superpowers/specs/2026-04-12-local-agent-node-design.md §7`. Must have: Context (3 candidate metrics), Decision (STO formula), Consequences, Validation Criteria. **Now in FLOSSI U sibling project; commit to its own repo, not FLOSS.**
- `../FLOSSI_U/LICENSE` — must contain exactly `SPDX-License-Identifier: AGPL-3.0-or-later` with no additional legal text (that goes in LEGAL_DEFINITIONS.md). **Now in FLOSSI U sibling project.**
- `docs/governance/LEGAL_DEFINITIONS.md` — Carrier Equivalence addendum text (AGPL supplement, values statement, scope clarification). Still in FLOSS repo.

```bash
# FLOSSI U artifacts now live in a separate repo at C:/~shit/FLOSSI_U/
# Commit those there once FLOSSI U has its own .git initialized.

# In FLOSS repo:
git add docs/governance/LEGAL_DEFINITIONS.md
git commit -m "fix(F3): Carrier Equivalence addendum (FLOSSI U artifacts moved to sibling project)"
```

F2 (`serialization.py`) is committed as part of Task 0. Do not include it here.
