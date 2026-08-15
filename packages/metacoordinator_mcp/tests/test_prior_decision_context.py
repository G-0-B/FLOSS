"""Regressions for bounded prior terminal-decision voter context."""

from __future__ import annotations

import builtins
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from packages.metacoordinator_mcp.tools import GatewayTools
from packages.orchestrator.claim_schema import (
    BlastRadius,
    Claim,
    EvidenceRef,
    ProposalType,
    Vote,
)


DNA_HASH = "d" * 64


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _action_digest(summary: str, body: str) -> str:
    serialized = _canonical_json({"body": body, "summary": summary})
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _claim(
    summary: str,
    body: str,
    *,
    proposer: str = "prior-proposer",
    proposal_type: ProposalType = ProposalType.CODE_CHANGE,
    blast_radius: BlastRadius = BlastRadius.LOCAL,
    evidence: list[EvidenceRef] | None = None,
) -> Claim:
    return Claim(
        proposer=proposer,
        proposal_type=proposal_type,
        summary=summary,
        body=body,
        blast_radius=blast_radius,
        evidence=evidence or [],
    )


def _claim_entry(claim: Claim) -> dict:
    return {"type": "claim", "content": claim.to_dict()}


def _decision_entry(claim_id: str, outcome: str, **extra: object) -> dict:
    return {
        "type": "decision",
        "content": {"claim_id": claim_id, "outcome": outcome, **extra},
    }


def _gateway(tmp_path: Path) -> GatewayTools:
    return GatewayTools(base_dir=tmp_path, dna_hash=DNA_HASH)


def _prior_payload(context: str) -> tuple[str, dict]:
    assert context.startswith("prior_decisions=")
    serialized = context.removeprefix("prior_decisions=")
    payload = json.loads(serialized)
    assert serialized == _canonical_json(payload)
    return serialized, payload


def _packet_evidence(
    workspace_root: Path, nested_refs: list[dict]
) -> tuple[EvidenceRef, dict, str]:
    from packages.activity_log import provenance

    artifact = workspace_root / "FLOSS" / "docs" / "specs" / "packet-artifact.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("packet artifact", encoding="utf-8")
    consent_hash = "uhCAk" + ("c" * 32)
    packet_entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-08-15T00:00:00Z",
        "human_collision_node": "operator",
        "artifact_refs": [
            provenance.artifact_ref(artifact, workspace_root=workspace_root)
        ],
        "evidence_refs": nested_refs,
        "risks": [],
        "benefits": [],
        "next_action": "submit claim",
        "consent_ref": {"decision_action_hash": consent_hash},
    }
    packet, packet_path = provenance.create_packet(
        [packet_entry],
        identity_dir=workspace_root / "identity",
        output_root=workspace_root / ".agent-surface" / "provenance",
    )
    evidence = EvidenceRef(
        type="provenance_packet",
        ref=str(packet_path.relative_to(workspace_root).as_posix()),
        sha256=provenance.sha256_file(packet_path),
    )
    return evidence, packet, consent_hash


def test_exact_action_resubmission_receives_prior_approved_decision(tmp_path):
    """A new claim ID must not make an already-approved action look history-free."""
    captured_contexts: list[str] = []

    def approving_voter(claim, context="(none)"):
        captured_contexts.append(context)
        return Vote(
            voter="context-capture",
            weight=0.8,
            rationale=f"Approve {claim.id}",
        )

    gateway = GatewayTools(
        base_dir=Path(tmp_path),
        dna_hash=DNA_HASH,
        voter_factory=lambda: [approving_voter],
    )
    summary = "Apply the bounded duplicate-action correction"
    body = "Route exact-action decision evidence to voters."
    prior = json.loads(
        gateway.submit_claim(
            proposer="first-proposer",
            proposal_type="CodeChange",
            summary=summary,
            body=body,
            blast_radius="Local",
        )
    )
    first_decision = json.loads(gateway.run_consensus_round(prior["claim_id"]))
    current = json.loads(
        gateway.submit_claim(
            proposer="second-proposer",
            proposal_type="CodeChange",
            summary=summary,
            body=body,
            blast_radius="Local",
        )
    )
    second_decision = json.loads(gateway.run_consensus_round(current["claim_id"]))

    assert first_decision["outcome"] == "APPROVED"
    assert second_decision["outcome"] == "APPROVED"
    assert captured_contexts[0] == "(none)"
    context = captured_contexts[1]
    assert context.startswith("prior_decisions=")
    serialized_payload = context.removeprefix("prior_decisions=")
    payload = json.loads(serialized_payload)
    assert serialized_payload == _canonical_json(payload)
    assert payload["action_sha256"] == _action_digest(summary, body)
    assert payload["truncated"] is False
    assert [match["claim_id"] for match in payload["matches"]] == [
        prior["claim_id"]
    ]
    assert payload["matches"][0]["outcome"] == "APPROVED"
    assert current["claim_id"] not in serialized_payload


def test_prior_context_includes_each_terminal_outcome_but_not_deferred(tmp_path):
    summary = "Terminal outcome coverage"
    body = "The proposed action is byte-identical."
    current = _claim(summary, body, proposer="current")
    outcomes = ["APPROVED", "REJECTED", "CONFLICT", "OVERRIDDEN", "DEFERRED"]
    priors = [_claim(summary, body, proposer=outcome) for outcome in outcomes]
    entries = [_claim_entry(current)]
    for prior, outcome in zip(priors, outcomes, strict=True):
        entries.extend([_decision_entry(prior.id, outcome), _claim_entry(prior)])

    _serialized, payload = _prior_payload(
        _gateway(tmp_path)._render_voter_context(current, entries=entries)
    )

    assert {match["outcome"] for match in payload["matches"]} == {
        "APPROVED",
        "REJECTED",
        "CONFLICT",
        "OVERRIDDEN",
    }
    assert priors[-1].id not in {match["claim_id"] for match in payload["matches"]}


def test_prior_context_uses_only_each_claims_newest_decision(tmp_path):
    summary = "Newest decision wins"
    body = "Do not fall back to an older terminal record."
    current = _claim(summary, body, proposer="current")
    latest_terminal = _claim(summary, body, proposer="latest-terminal")
    latest_deferred = _claim(summary, body, proposer="latest-deferred")
    entries = [
        _claim_entry(current),
        _decision_entry(latest_terminal.id, "REJECTED"),
        _decision_entry(latest_terminal.id, "APPROVED"),
        _claim_entry(latest_terminal),
        _decision_entry(latest_deferred.id, "DEFERRED"),
        _decision_entry(latest_deferred.id, "APPROVED"),
        _claim_entry(latest_deferred),
    ]

    _serialized, payload = _prior_payload(
        _gateway(tmp_path)._render_voter_context(current, entries=entries)
    )

    assert [(match["claim_id"], match["outcome"]) for match in payload["matches"]] == [
        (latest_terminal.id, "REJECTED")
    ]


def test_raw_action_match_ignores_other_metadata_but_not_text_changes(tmp_path):
    summary = "Preserve raw action identity"
    body = "Whitespace and case remain significant."
    current = _claim(summary, body, proposer="current")
    changed_metadata = _claim(
        summary,
        body,
        proposer="different-proposer",
        proposal_type=ProposalType.SPEC_CHANGE,
        blast_radius=BlastRadius.SYSTEM,
    )
    changed_body = _claim(summary, body + " ")
    changed_summary = _claim(summary.lower(), body)
    entries = [_claim_entry(current)]
    for prior in (changed_metadata, changed_body, changed_summary):
        entries.extend([_decision_entry(prior.id, "APPROVED"), _claim_entry(prior)])

    _serialized, payload = _prior_payload(
        _gateway(tmp_path)._render_voter_context(current, entries=entries)
    )

    assert payload["matches"] == [
        {
            "blast_radius": "System",
            "claim_id": changed_metadata.id,
            "outcome": "APPROVED",
            "proposal_type": "SpecChange",
            "submitted_at": changed_metadata.submitted_at,
        }
    ]


def test_prior_context_keeps_matching_claims_in_newest_first_chain_order(tmp_path):
    summary = "Newest-first ordering"
    body = "Chain position establishes context order."
    current = _claim(summary, body, proposer="current")
    older = _claim(summary, body, proposer="older")
    newer = _claim(summary, body, proposer="newer")
    entries = [
        _claim_entry(current),
        _decision_entry(newer.id, "CONFLICT"),
        _claim_entry(newer),
        _decision_entry(older.id, "REJECTED"),
        _claim_entry(older),
    ]

    _serialized, payload = _prior_payload(
        _gateway(tmp_path)._render_voter_context(current, entries=entries)
    )

    assert [match["claim_id"] for match in payload["matches"]] == [
        newer.id,
        older.id,
    ]


def test_prior_context_bounds_match_count_and_drops_oldest_first(tmp_path):
    summary = "Bound the match set"
    body = "Many exact prior actions must not consume unbounded context."
    current = _claim(summary, body, proposer="current")
    priors_oldest_first = [
        _claim(summary, body, proposer=f"prior-{index}") for index in range(10)
    ]
    newest_first = list(reversed(priors_oldest_first))
    entries = [_claim_entry(current)]
    for prior in newest_first:
        entries.extend([_decision_entry(prior.id, "APPROVED"), _claim_entry(prior)])

    _serialized, payload = _prior_payload(
        _gateway(tmp_path)._render_voter_context(current, entries=entries)
    )

    rendered_ids = [match["claim_id"] for match in payload["matches"]]
    assert 0 < len(rendered_ids) <= 8
    assert rendered_ids == [prior.id for prior in newest_first[: len(rendered_ids)]]
    assert priors_oldest_first[0].id not in rendered_ids
    assert payload["truncated"] is True


def test_prior_context_is_bounded_and_never_echoes_free_form_text(tmp_path):
    summary = "SECRET SUMMARY must remain digest-only"
    body = "SECRET BODY must remain digest-only " + ("x" * 400)
    rationale = "SECRET DECISION RATIONALE must not reach voters"
    current = _claim(summary, body, proposer="current")
    priors = [_claim(summary, body, proposer=f"prior-{index}") for index in range(8)]
    entries = [_claim_entry(current)]
    for prior in reversed(priors):
        entries.extend(
            [
                _decision_entry(
                    prior.id,
                    "APPROVED",
                    votes=[{"rationale": rationale}],
                ),
                _claim_entry(prior),
            ]
        )

    context = _gateway(tmp_path)._render_voter_context(current, entries=entries)
    serialized, payload = _prior_payload(context)

    assert len(context) <= 1024
    assert payload["truncated"] is True
    assert set(payload) == {"action_sha256", "matches", "truncated"}
    assert set(payload["matches"][0]) == {
        "blast_radius",
        "claim_id",
        "outcome",
        "proposal_type",
        "submitted_at",
    }
    assert summary not in serialized
    assert body not in serialized
    assert rationale not in serialized


def test_malformed_prior_records_are_omitted_without_hiding_valid_match(tmp_path):
    summary = "Malformed records fail locally"
    body = "A malformed neighbor must not hide a valid prior decision."
    current = _claim(summary, body, proposer="current")
    valid = _claim(summary, body, proposer="valid")
    malformed_claim = _claim(summary, body, proposer="malformed-claim")
    malformed_latest_decision = _claim(
        summary, body, proposer="malformed-latest-decision"
    )
    malformed_content = malformed_claim.to_dict()
    del malformed_content["proposal_type"]
    entries = [
        _claim_entry(current),
        _decision_entry(valid.id, "APPROVED"),
        _claim_entry(valid),
        _decision_entry(malformed_claim.id, "REJECTED"),
        {"type": "claim", "content": malformed_content},
        _decision_entry(malformed_latest_decision.id, "NOT_AN_OUTCOME"),
        _decision_entry(malformed_latest_decision.id, "CONFLICT"),
        _claim_entry(malformed_latest_decision),
        {"type": "decision", "content": {"outcome": "APPROVED"}},
    ]

    _serialized, payload = _prior_payload(
        _gateway(tmp_path)._render_voter_context(current, entries=entries)
    )

    assert [match["claim_id"] for match in payload["matches"]] == [valid.id]


def test_no_history_ordinary_context_remains_none(tmp_path):
    current = _claim("No prior action", "This action has no history.")

    context = _gateway(tmp_path)._render_voter_context(
        current, entries=[_claim_entry(current)]
    )

    assert context == "(none)"


def test_packet_only_context_remains_byte_for_byte_unchanged(tmp_path):
    evidence, _packet, _consent_hash = _packet_evidence(
        tmp_path, [{"type": "spec", "ref": "bounded-context.spec.md"}]
    )
    current = _claim(
        "Packet-only action",
        "No exact prior action exists.",
        proposal_type=ProposalType.SPEC_CHANGE,
        blast_radius=BlastRadius.SYSTEM,
        evidence=[evidence],
    )
    gateway = GatewayTools(
        base_dir=tmp_path / "cell",
        dna_hash=DNA_HASH,
        workspace_root=tmp_path,
    )

    legacy_context = gateway._render_voter_context(current)
    history_aware_context = gateway._render_voter_context(
        current, entries=[_claim_entry(current)]
    )

    assert history_aware_context == legacy_context


def test_packet_and_prior_context_preserve_mandatory_metadata_with_total_bound(
    tmp_path,
):
    nested_refs = [
        {"type": "spec", "ref": f"doc-{index}-" + ("x" * 220) + ".md"}
        for index in range(33)
    ]
    evidence, packet, consent_hash = _packet_evidence(tmp_path, nested_refs)
    summary = "Governed exact-action resubmission"
    body = "Carry both packet and prior terminal-decision evidence."
    current = _claim(
        summary,
        body,
        proposer="current",
        proposal_type=ProposalType.SPEC_CHANGE,
        blast_radius=BlastRadius.SYSTEM,
        evidence=[evidence],
    )
    prior = _claim(
        summary,
        body,
        proposer="prior",
        proposal_type=ProposalType.CODE_CHANGE,
        blast_radius=BlastRadius.LOCAL,
    )
    entries = [
        _claim_entry(current),
        _decision_entry(prior.id, "APPROVED"),
        _claim_entry(prior),
    ]
    gateway = GatewayTools(
        base_dir=tmp_path / "cell",
        dna_hash=DNA_HASH,
        workspace_root=tmp_path,
    )

    context = gateway._render_voter_context(current, entries=entries)

    assert len(context) <= 4096
    assert "prior_decisions=" in context
    assert " | " in context
    assert "[truncated]" in context
    assert f"packet digest={packet['d']}" in context
    assert f"consent_ref={consent_hash}" in context
    _serialized, payload = _prior_payload(
        "prior_decisions=" + context.rsplit("prior_decisions=", 1)[1]
    )
    assert [match["claim_id"] for match in payload["matches"]] == [prior.id]


def test_ordinary_history_context_does_not_import_optional_provenance(tmp_path):
    real_import = builtins.__import__
    captured_contexts: list[str] = []

    def fail_provenance_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "packages.activity_log" and "provenance" in fromlist:
            raise ModuleNotFoundError("No module named 'blake3'", name="blake3")
        return real_import(name, globals, locals, fromlist, level)

    def approving_voter(claim, context="(none)"):
        captured_contexts.append(context)
        return Vote(
            voter="lean-context-capture",
            weight=0.8,
            rationale=f"Approve {claim.id}",
        )

    gateway = GatewayTools(
        base_dir=tmp_path,
        dna_hash=DNA_HASH,
        voter_factory=lambda: [approving_voter],
    )
    prior = json.loads(
        gateway.submit_claim(
            proposer="first",
            proposal_type="CodeChange",
            summary="Lean duplicate action",
            body="No provenance packet is needed.",
            blast_radius="Local",
        )
    )
    with patch("builtins.__import__", side_effect=fail_provenance_import):
        first_decision = json.loads(gateway.run_consensus_round(prior["claim_id"]))
        current = json.loads(
            gateway.submit_claim(
                proposer="second",
                proposal_type="CodeChange",
                summary="Lean duplicate action",
                body="No provenance packet is needed.",
                blast_radius="Local",
            )
        )
        second_decision = json.loads(
            gateway.run_consensus_round(current["claim_id"])
        )

    assert first_decision["outcome"] == "APPROVED"
    assert second_decision["outcome"] == "APPROVED"
    assert captured_contexts[0] == "(none)"
    assert captured_contexts[1].startswith("prior_decisions=")
