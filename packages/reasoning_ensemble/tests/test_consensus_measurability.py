"""The clustering must admit when it could not have separated anything.

Background, measured 2026-08-25 over every synthesis this repository has
produced (`.agent-surface/reasoning/ensemble/`, six runs): all six report
`largest_cluster_fraction = 1.0` with an empty minority set. Four of the six
prompts were written specifically to provoke disagreement -- three adversarial
LENS audits and one that opened "Attack it. Do not summarize or agree." The
lowest off-diagonal cosine similarity anywhere in the corpus is 0.791, against a
clustering threshold of 0.75.

So the panel never disagreed, six times running, under adversarial instruction.
The likelier reading is that whole-response cosine similarity does not measure
agreement at all: six models answering the same question about the same repo
name the same files in the same register and land near 0.9 whatever they
conclude. A single cluster was the only outcome the metric could reach.

These tests do not fix that -- extraction-level agreement is a different design.
They stop the artifact being reported as a finding.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.reasoning_ensemble.synthesizer import (  # noqa: E402
    CLUSTER_SIMILARITY_THRESHOLD,
    CONSENSUS_NOT_MEASURED,
    SIMILARITY_FLOOR_OBSERVED,
    TierClassification,
    separation_diagnostics,
    write_synthesis,
)
from packages.reasoning_ensemble.synthesizer import VoterResponse  # noqa: E402


def _matrix(values: list[list[float]]) -> list[list[float]]:
    return values


def test_everything_above_threshold_is_not_a_measurement():
    """The observed corpus shape: no pair could have been separated."""

    similarity = _matrix(
        [
            [1.0, 0.85, 0.91],
            [0.85, 1.0, 0.88],
            [0.91, 0.88, 1.0],
        ]
    )
    diagnostics = separation_diagnostics(similarity, CLUSTER_SIMILARITY_THRESHOLD)

    assert diagnostics["discriminative"] is False
    assert CONSENSUS_NOT_MEASURED in str(diagnostics["reason"])
    assert diagnostics["pairs_below_threshold"] == 0
    assert diagnostics["min"] == 0.85


def test_the_real_corpus_floor_would_be_flagged():
    """0.791 is the lowest pair ever observed; 0.75 sits underneath all of it."""

    assert SIMILARITY_FLOOR_OBSERVED > CLUSTER_SIMILARITY_THRESHOLD, (
        "if the observed floor ever drops below the threshold, the metric has "
        "started separating things and this whole guard needs revisiting"
    )
    similarity = _matrix(
        [
            [1.0, SIMILARITY_FLOOR_OBSERVED],
            [SIMILARITY_FLOOR_OBSERVED, 1.0],
        ]
    )
    assert (
        separation_diagnostics(similarity, CLUSTER_SIMILARITY_THRESHOLD)[
            "discriminative"
        ]
        is False
    )


def test_a_genuinely_split_panel_is_discriminative():
    """The guard must not be a constant False dressed up as a diagnostic."""

    similarity = _matrix(
        [
            [1.0, 0.91, 0.40],
            [0.91, 1.0, 0.38],
            [0.40, 0.38, 1.0],
        ]
    )
    diagnostics = separation_diagnostics(similarity, CLUSTER_SIMILARITY_THRESHOLD)

    assert diagnostics["discriminative"] is True
    assert "reason" not in diagnostics
    assert diagnostics["pairs_below_threshold"] == 4


def test_everything_below_threshold_is_equally_unmeasured():
    """All-singletons is not maximal dissent; it is the same blindness inverted."""

    similarity = _matrix(
        [
            [1.0, 0.20, 0.11],
            [0.20, 1.0, 0.19],
            [0.11, 0.19, 1.0],
        ]
    )
    diagnostics = separation_diagnostics(similarity, CLUSTER_SIMILARITY_THRESHOLD)

    assert diagnostics["discriminative"] is False
    assert "ceiling" in str(diagnostics["reason"])


def test_no_scored_pairs_is_not_consensus():
    assert separation_diagnostics([], CLUSTER_SIMILARITY_THRESHOLD)[
        "discriminative"
    ] is False
    assert separation_diagnostics([[1.0]], CLUSTER_SIMILARITY_THRESHOLD)[
        "discriminative"
    ] is False


def _voter(voter_id: str, text: str) -> VoterResponse:
    return VoterResponse(
        voter_id=voter_id,
        model=f"model/{voter_id}",
        family=voter_id,
        response=text,
        response_hash=voter_id,
        response_embedding=[1.0, 0.0],
        duration_seconds=1.0,
    )


def _tier1(separation: dict) -> TierClassification:
    return TierClassification(
        tier="tier1",
        cluster_assignments={"alpha": 0, "beta": 0},
        cluster_sizes={0: 2},
        largest_cluster_id=0,
        largest_cluster_fraction=1.0,
        minority_coherent_voters=[],
        similarity_matrix=[[1.0, 0.9], [0.9, 1.0]],
        separation=separation,
    )


def test_writeup_refuses_the_word_unanimous_when_nothing_was_measured():
    responses = [
        _voter("alpha", "Alpha says the bridge is fine. It is fine."),
        _voter("beta", "Beta says the bridge is broken. It is broken. Longer text."),
    ]
    unmeasured = _tier1(
        separation_diagnostics([[1.0, 0.9], [0.9, 1.0]], CLUSTER_SIMILARITY_THRESHOLD)
    )
    text = write_synthesis("does the bridge work?", responses, unmeasured)

    assert "Unanimous consensus" not in text
    assert "This run did not measure consensus" in text
    assert "Do not cite this run as corroboration" in text
    assert "voter_responses[]" in text, (
        "a reader told the panel proved nothing needs to be told where the "
        "disagreement, if any, still lives"
    )


def test_writeup_still_reports_unanimity_when_it_was_measurable():
    responses = [
        _voter("alpha", "Alpha says the bridge is fine. It is fine."),
        _voter("beta", "Beta agrees the bridge is fine. It is fine. Longer text."),
    ]
    measured = _tier1(
        separation_diagnostics(
            [[1.0, 0.9, 0.3], [0.9, 1.0, 0.31], [0.3, 0.31, 1.0]],
            CLUSTER_SIMILARITY_THRESHOLD,
        )
    )
    text = write_synthesis("does the bridge work?", responses, measured)

    assert "Unanimous consensus" in text
    assert "did not measure consensus" not in text
