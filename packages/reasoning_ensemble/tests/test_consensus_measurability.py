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
    degenerate_voters,
    TIER_UNMEASURED,
    classify_tier,
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
    # 3 voters = 3 distinct pairs, 2 of them below threshold. This asserted 4
    # while the loop walked both (i,j) and (j,i) -- the test encoded the double
    # count rather than catching it.
    assert diagnostics["pair_count"] == 3
    assert diagnostics["pairs_below_threshold"] == 2


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


# ---------------------------------------------------------------------------
# A response can be present, long, and carry no position at all.
# ---------------------------------------------------------------------------


def _resp(voter_id: str, text: str, **kw) -> VoterResponse:
    return VoterResponse(
        voter_id=voter_id,
        model=f"m/{voter_id}",
        family=voter_id,
        response=text,
        response_hash=voter_id,
        response_embedding=[1.0],
        duration_seconds=1.0,
        **kw,
    )


def test_an_unclosed_reasoning_block_is_not_an_answer():
    """Measured: one voter did this in 5 of 5 runs and counted as converged.

    It also defeats the "shorter response = non-answer" heuristic -- in one run
    it was the SECOND-LONGEST response in the file.
    """
    flagged = degenerate_voters(
        [
            _resp("thinker", "<think>The user is asking me to " + "restate. " * 60),
            _resp("real-a", "The answer is Substrate. Override forbidden."),
            _resp("real-b", "The answer is System, for these reasons."),
        ]
    )
    assert set(flagged) == {"thinker"}
    assert "restatement" in flagged["thinker"]


def test_a_truncated_fragment_is_not_an_answer():
    """Measured: one voter was cut mid-sentence in 5 of 5 runs, 212-1466 chars."""
    flagged = degenerate_voters(
        [
            _resp("cut", "The blast radius should probably be"),
            _resp("real-a", "The answer is Substrate. " * 20),
            _resp("real-b", "The answer is System. " * 20),
        ]
    )
    assert set(flagged) == {"cut"}
    assert "mid-sentence" in flagged["cut"]


def test_a_short_but_finished_answer_is_not_flagged():
    """Brevity is not a defect. Only an unfinished sentence is."""
    flagged = degenerate_voters(
        [
            _resp("terse", "Substrate."),
            _resp("verbose-a", "The answer is Substrate, because " * 20 + "yes."),
            _resp("verbose-b", "The answer is Substrate, given " * 20 + "so."),
        ]
    )
    assert flagged == {}


def test_a_closed_reasoning_block_is_fine():
    flagged = degenerate_voters(
        [
            _resp("thinker", "<think>weighing it</think> The answer is Substrate."),
            _resp("real-a", "The answer is Substrate. Override forbidden."),
            _resp("real-b", "The answer is System, for these reasons."),
        ]
    )
    assert flagged == {}


def test_errored_and_empty_voters_are_not_double_reported():
    """They are already named in the dropped-voter line; do not flag them twice."""
    flagged = degenerate_voters(
        [
            _resp("dead", "", error="TimeoutError: timed out"),
            _resp("real-a", "The answer is Substrate. " * 10),
            _resp("real-b", "The answer is System. " * 10),
        ]
    )
    assert flagged == {}


def test_the_writeup_names_voters_that_were_dispatched_but_not_counted():
    """Headers read "Voters: 5" while voter_count said 6, and nothing said why."""
    counted = [
        _resp("alpha", "Alpha says the bridge is fine. It is fine."),
        _resp("beta", "Beta says the bridge is fine too. It is fine. Longer."),
    ]
    dropped = VoterResponse(
        voter_id="gamma",
        model="m/gamma",
        family="gamma",
        response="",
        response_hash="",
        response_embedding=None,
        duration_seconds=90.0,
        error="ReadTimeout: timed out",
    )
    text = write_synthesis(
        "does the bridge work?",
        counted,
        _tier1(
            separation_diagnostics(
                [[1.0, 0.9, 0.3], [0.9, 1.0, 0.31], [0.3, 0.31, 1.0]],
                CLUSTER_SIMILARITY_THRESHOLD,
            )
        ),
        all_responses=counted + [dropped],
    )

    assert "Dispatched but not counted:** 1 of 3" in text
    assert "gamma" in text
    assert "ReadTimeout" in text


def test_the_writeup_says_when_counted_voters_took_no_position():
    counted = [
        _resp("thinker", "<think>The user is asking me to " + "restate. " * 60),
        _resp("real-a", "The answer is Substrate. Override forbidden."),
        _resp("real-b", "The answer is System, for these reasons here."),
    ]
    tier = TierClassification(
        tier="tier1",
        cluster_assignments={"thinker": 0, "real-a": 0, "real-b": 0},
        cluster_sizes={0: 3},
        largest_cluster_id=0,
        largest_cluster_fraction=1.0,
        minority_coherent_voters=[],
        similarity_matrix=[],
        separation=separation_diagnostics(
            [[1.0, 0.9, 0.3], [0.9, 1.0, 0.31], [0.3, 0.31, 1.0]],
            CLUSTER_SIMILARITY_THRESHOLD,
        ),
    )
    text = write_synthesis("what is the blast radius?", counted, tier)

    assert "no position" in text
    assert "`thinker`" in text
    assert "agrees with nothing" in text


def test_each_symmetric_pair_is_counted_once():
    """The matrix is symmetric; walking all of it doubles every count.

    pair_count and pairs_below_threshold are persisted and read as experimental
    diagnostics, so a factor of two was wrong everywhere they were consumed.
    """
    for k in (2, 3, 4, 6):
        matrix = [[1.0 if i == j else 0.5 for j in range(k)] for i in range(k)]
        diagnostics = separation_diagnostics(matrix, CLUSTER_SIMILARITY_THRESHOLD)
        assert diagnostics["pair_count"] == k * (k - 1) // 2, k


def test_a_negative_cosine_is_a_measurement_not_a_missing_embedding():
    """Dropping non-positive values hid the only pairs that separated anyone.

    `pairwise_similarity_matrix` writes 0.0 for a voter with no embedding, and
    the filter was `value > 0.0` -- so a genuine negative cosine was discarded as
    "missing". A panel whose only separating pairs were negative reported that
    every scored pair converged and separation was impossible, while the
    clustering used those same negatives and split the voters.
    """
    matrix = [
        [1.0, 0.92, -0.30],
        [0.92, 1.0, -0.25],
        [-0.30, -0.25, 1.0],
    ]
    embedded = [True, True, True]

    diagnostics = separation_diagnostics(
        matrix, CLUSTER_SIMILARITY_THRESHOLD, embedded=embedded
    )
    assert diagnostics["pair_count"] == 3, "the negative pairs are measurements"
    assert diagnostics["min"] < 0
    assert diagnostics["discriminative"] is True, (
        "the threshold sits inside the observed spread; this panel DID separate"
    )


def test_a_voter_with_no_embedding_is_reported_separately():
    matrix = [
        [1.0, 0.9, 0.0],
        [0.9, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    diagnostics = separation_diagnostics(
        matrix, CLUSTER_SIMILARITY_THRESHOLD, embedded=[True, True, False]
    )
    assert diagnostics["pair_count"] == 1, "only the embedded pair is scored"
    assert diagnostics["pairs_missing_embeddings"] == 2


def test_an_unmeasured_run_does_not_export_tier1():
    """The tier is what machines read; the prose warning is what they ignore.

    `tier1` means unanimous consensus in the spec, and the staged JSON, the
    activity action and the deliberate() MCP response all export it verbatim. A
    run whose clustering could not have separated anything was still labelled
    tier1, so every automated consumer treated an explicitly unmeasured result
    as corroboration while the caveat sat in human-readable prose.
    """
    responses = [
        _resp("alpha", "Alpha says the bridge is fine. It is fine."),
        _resp("beta", "Beta says the bridge is broken. It is broken."),
        _resp("gamma", "Gamma says something else entirely, at length."),
    ]
    # every pair above threshold: separation is impossible
    similarity = [
        [1.0, 0.91, 0.88],
        [0.91, 1.0, 0.90],
        [0.88, 0.90, 1.0],
    ]
    assignments = {"alpha": 0, "beta": 0, "gamma": 0}
    tier = classify_tier(responses, similarity, assignments)

    assert tier.tier == TIER_UNMEASURED
    assert tier.tier != "tier1"
    assert tier.consensus_was_measurable is False
    # and it still reaches the writeup, so a human sees it too
    assert "unmeasured" in write_synthesis("q?", responses, tier).lower()


def test_a_measurable_unanimous_run_is_still_tier1():
    """The guard must not relabel every unanimous panel."""
    responses = [
        _resp("alpha", "The bridge is fine. It is fine."),
        _resp("beta", "The bridge is fine too. Agreed."),
        _resp("gamma", "Also fine, for the same reason."),
    ]
    similarity = [
        [1.0, 0.91, 0.30],
        [0.91, 1.0, 0.31],
        [0.30, 0.31, 1.0],
    ]
    tier = classify_tier(responses, similarity, {"alpha": 0, "beta": 0, "gamma": 0})
    assert tier.tier == "tier1"
    assert tier.consensus_was_measurable is True


def test_an_unmeasured_run_is_not_rendered_as_tier4_divergence():
    """The reclassification dropped into the tier4 `else` branch.

    The artifact then said consensus was unmeasured and, three lines later,
    claimed "Tier-4 divergence preserved" and "No single cluster carried the
    majority" — about a run that had exactly ONE cluster. A reader could believe
    either half.
    """
    responses = [
        _resp("alpha", "Alpha says the bridge is fine. It is fine."),
        _resp("beta", "Beta says the bridge is broken. It is broken."),
        _resp("gamma", "Gamma says something else entirely, at length."),
    ]
    similarity = [
        [1.0, 0.91, 0.88],
        [0.91, 1.0, 0.90],
        [0.88, 0.90, 1.0],
    ]
    tier = classify_tier(responses, similarity, {"alpha": 0, "beta": 0, "gamma": 0})
    assert tier.tier == TIER_UNMEASURED

    text = write_synthesis("does the bridge work?", responses, tier)
    assert "Tier-4 divergence" not in text
    assert "carried the majority" not in text
    assert "Consensus not measured" in text
    # every response is present, none promoted as representative
    for voter in ("alpha", "beta", "gamma"):
        assert voter in text
    assert "Representative voter" not in text
