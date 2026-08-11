"""
GatewayTools — the 5 MCP tool handlers for the FLOSSIØULLK consensus gateway.

The gateway is a router, not a controller (spec §5). It:
  - Accepts Claims and Votes from any agent
  - Reads the cell source chain to provide context to voters
  - Does NOT decide outcomes, command voters, or hold state outside the cell dir

Each public method returns a JSON string — the MCP wire format for tool results.
Errors are returned as {"error": "<message>"} rather than raised, so callers
(LLM agents reading tool results) always receive parseable output.
"""

from __future__ import annotations

import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.orchestrator.claim_schema import (  # noqa: E402
    BlastRadius,
    Claim,
    Decision,
    EvidenceRef,
    Outcome,
    ProposalType,
    TruthStatus,
    Vote,
)
from packages.orchestrator.consensus_gate import tally  # noqa: E402
from packages.source_chain.cell import CellDirectory  # noqa: E402

# Deferred type — avoids importing voters.py (and LiteLLM) at module load.
# Tests that never call run_consensus_round should never touch the network.
VoterFactory = Callable[[], list[Callable[..., Vote]]]


def _claim_from_chain_entry(entry_content: dict[str, Any]) -> Claim:
    """Reconstruct a Claim dataclass from its to_dict() form on the source chain.

    Enums come back as strings; we parse them back to their Enum members so
    downstream validation and tally logic work against the typed API.
    """
    evidence = [
        EvidenceRef(type=e["type"], ref=e["ref"], sha256=e.get("sha256"))
        for e in entry_content.get("evidence", [])
    ]
    return Claim(
        proposer=entry_content["proposer"],
        proposal_type=ProposalType(entry_content["proposal_type"]),
        summary=entry_content["summary"],
        body=entry_content["body"],
        blast_radius=BlastRadius(entry_content["blast_radius"]),
        evidence=evidence,
        truth_status=TruthStatus(entry_content.get("truth_status", "Unverified")),
        id=entry_content["id"],
        submitted_at=entry_content["submitted_at"],
    )


def _ok(data: Any) -> str:
    """Serialize a successful tool result into the compact JSON wire format."""
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _err(msg: str) -> str:
    """Serialize a tool error so MCP callers always receive parseable JSON."""
    return json.dumps({"error": msg}, separators=(",", ":"))


def _vote_from_chain_entry(entry_content: dict[str, Any]) -> Vote:
    """Reconstruct and validate a Vote dataclass from persisted source-chain content."""
    vote = Vote(
        voter=entry_content["voter"],
        weight=float(entry_content["weight"]),
        rationale=entry_content["rationale"],
        voted_at=entry_content["voted_at"],
    )
    vote.validate()
    return vote


def _decision_outcome(entry_content: dict[str, Any]) -> Outcome:
    """Parse the Outcome enum from a persisted Decision payload."""
    return Outcome(entry_content["outcome"])


def _known_voter_name(voter: Callable[..., Vote]) -> Optional[str]:
    """Return the configured voter name when inference is purely local."""
    name = getattr(voter, "__name__", "")
    for prefix in (
        "litellm_voter_",
        "flowith_voter_",
        "omo_momus_voter_",
        "omo_critic_voter_",
    ):
        if name.startswith(prefix):
            return name[len(prefix) :]
    return None


def _is_governed_claim(proposal_type: ProposalType, blast_radius: BlastRadius) -> bool:
    """Return True for the v1 provenance hard-block boundary."""

    return blast_radius in {
        BlastRadius.SYSTEM,
        BlastRadius.SUBSTRATE,
    } and proposal_type in {
        ProposalType.ADR_CHANGE,
        ProposalType.CONFIG_CHANGE,
        ProposalType.SPEC_CHANGE,
    }


def _find_claim_entry(
    entries: list[dict[str, Any]], claim_id: str
) -> Optional[dict[str, Any]]:
    """Return the persisted claim entry for `claim_id`, if present."""
    for entry in entries:
        if (
            entry.get("type") == "claim"
            and entry.get("content", {}).get("id") == claim_id
        ):
            return entry
    return None


def _latest_decision_for_claim(
    entries: list[dict[str, Any]], claim_id: str
) -> Optional[dict[str, Any]]:
    """Return the newest persisted decision content for `claim_id`, if present."""
    for entry in entries:
        if (
            entry.get("type") == "decision"
            and entry.get("content", {}).get("claim_id") == claim_id
        ):
            return entry["content"]
    return None


def _terminal_decision_error(
    claim_id: str, latest_decision: Optional[dict[str, Any]]
) -> Optional[str]:
    """Return a JSON error when a claim already has a terminal decision."""
    if latest_decision is None:
        return None
    try:
        latest_outcome = _decision_outcome(latest_decision)
    except (KeyError, ValueError) as exc:
        return _err(f"E_DECISION_MALFORMED: {exc}")
    if latest_outcome != Outcome.DEFERRED:
        return _err(
            "E_ALREADY_DECIDED: claim "
            f"{claim_id} already has a terminal decision "
            f"({latest_outcome.value})"
        )
    return None


def _existing_votes_by_voter(
    entries: list[dict[str, Any]], claim_id: str
) -> dict[str, Vote]:
    """Load prior source-chain votes for `claim_id`, keyed by voter id."""
    votes: dict[str, Vote] = {}
    for entry in entries:
        if (
            entry.get("type") != "vote"
            or entry.get("content", {}).get("claim_id") != claim_id
        ):
            continue
        vote = _vote_from_chain_entry(entry["content"])
        votes.setdefault(vote.voter, vote)
    return votes


def _resolve_voter_factory(factory: Optional[VoterFactory]) -> VoterFactory:
    """Resolve the active voter factory without importing provider code eagerly."""
    if factory is not None:
        return factory

    from packages.metacoordinator_mcp.voters import build_default_voters

    return build_default_voters


def _call_voter(
    voter: Callable[..., Vote], claim: Claim, context: str
) -> Vote:
    """Invoke a voter with (claim, context); fall back to legacy 1-arg voters.

    PR38 review thread PRRT_kwDOPkAi3s6UUuKj: voters gained a `context`
    parameter so they can see the validated provenance_packet metadata
    (digest + consent decision hash + nested non-packet evidence roots)
    that the hard gate already accepted. Old test harnesses that supplied
    a 1-arg voter must keep working, so we introspect the callable and
    dispatch based on how many positional parameters it accepts. A blind
    ``except TypeError`` would silently swallow errors raised INSIDE the
    voter body; we avoid that by pre-checking arity.
    """
    try:
        params = inspect.signature(voter).parameters
    except (TypeError, ValueError):
        # Builtins or C-implemented callables — try the wider signature first.
        try:
            return voter(claim, context)
        except TypeError:
            return voter(claim)
    positional = [
        p
        for p in params.values()
        if p.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    accepts_var_args = any(
        p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values()
    )
    if accepts_var_args or len(positional) >= 2:
        return voter(claim, context)
    return voter(claim)


def _collect_new_votes(
    voters: list[Callable[..., Vote]],
    claim: Claim,
    existing_votes_by_voter: dict[str, Vote],
    context: str = "(none)",
) -> list[Vote]:
    """Run voters and keep only newly contributed, validated votes."""
    new_votes: list[Vote] = []
    seen_voters = set(existing_votes_by_voter)
    for voter in voters:
        known_name = _known_voter_name(voter)
        wrapper_name = getattr(voter, "__name__", "")
        if (
            (known_name and known_name in seen_voters)
            or wrapper_name in seen_voters
        ):
            continue
        vote = _call_voter(voter, claim, context)
        vote.validate()
        if vote.voter in seen_voters:
            continue
        seen_voters.add(vote.voter)
        new_votes.append(vote)
    return new_votes


def _write_round_results(
    cell: CellDirectory,
    claim_id: str,
    new_votes: list[Vote],
    decision: Decision,
) -> None:
    """Append new votes first, then append the aggregate decision entry."""
    for vote in new_votes:
        cell.append_entry(
            entry_type="vote",
            author_did=vote.voter,
            content={"claim_id": claim_id, **vote.to_dict()},
        )

    cell.append_entry(
        entry_type="decision",
        author_did="metacoordinator",
        content=decision.to_dict(),
    )


class GatewayTools:
    """Stateless tool handlers. All state lives in the cell directory on disk."""

    def __init__(
        self,
        base_dir: Path,
        dna_hash: str,
        *,
        voter_factory: Optional[VoterFactory] = None,
        workspace_root: Path | str | None = None,
    ) -> None:
        self._cell = CellDirectory(base_dir=base_dir, dna_hash=dna_hash)
        # voter_factory is lazy: default stays None so test harnesses that
        # don't exercise run_consensus_round never import voters.py / litellm.
        self._voter_factory: Optional[VoterFactory] = voter_factory
        self._workspace_root = (
            Path(workspace_root) if workspace_root is not None else _REPO_ROOT.parent
        )

    def _validate_provenance_evidence(
        self, evidence: list[EvidenceRef]
    ) -> tuple[bool, bool, list[str]]:
        """Validate packet evidence and report whether any valid packet has consent."""

        has_valid_packet, has_consent, errors, _packets = (
            self._collect_provenance_state(evidence)
        )
        return has_valid_packet, has_consent, errors

    def _collect_provenance_state(
        self, evidence: list[EvidenceRef]
    ) -> tuple[bool, bool, list[str], list[tuple[dict, Path]]]:
        """Validate packets and additionally return each packet and resolved path.

        Used by both ``submit_claim`` (via the 3-tuple wrapper above) and
        ``_render_voter_context`` — the latter needs the packet payloads to
        surface digest, consent decision hash, and nested non-packet
        evidence roots to voters.
        """
        from packages.activity_log import provenance

        has_valid_packet = False
        has_consent = False
        errors: list[str] = []
        validated_packets: list[tuple[dict, Path]] = []
        for ref in evidence:
            if ref.type != "provenance_packet":
                continue
            packet_path = Path(ref.ref)
            if not packet_path.is_absolute():
                packet_path = self._workspace_root / ref.ref
            if not packet_path.exists():
                errors.append("E_PROVENANCE_PACKET_NOT_FOUND")
                continue
            if (
                ref.sha256 is not None
                and provenance.sha256_file(packet_path) != ref.sha256
            ):
                errors.append("E_PROVENANCE_SHA256_MISMATCH")
                continue
            result = provenance.validate_packet(
                packet_path,
                workspace_root=self._workspace_root,
            )
            if not result.ok:
                errors.extend(result.errors)
                continue
            has_valid_packet = True
            packet = result.packet or {}
            has_consent = has_consent or provenance.packet_has_consent(packet)
            if packet:
                validated_packets.append((packet, packet_path))
        return has_valid_packet, has_consent, errors, validated_packets

    def _render_voter_context(self, claim: Claim) -> str:
        """Compose the voter-visible context string from validated packet metadata.

        PR38 review thread PRRT_kwDOPkAi3s6UUuKj: the hard gate on
        ``submit_claim`` verifies every ``provenance_packet`` evidence ref
        (digest, signature, consent, nested non-packet evidence root) but
        the voter prompt only rendered the top-level ``[provenance_packet]``
        ref and a literal ``(none)`` context. Governed System/Substrate
        claims then looked identical to broken ones from the voter's seat,
        and the calibrated checklist forced non-positive votes even when
        the submission was fully valid.

        This method rebuilds a compact context digest voters can read:
        one line per validated packet naming its digest, whether a
        consent decision reference is attached, and the nested non-packet
        evidence refs the packet transports. Non-packet evidence stays in
        the ``Evidence:`` field of the prompt; only packet-derived context
        goes here.
        """
        if not any(ref.type == "provenance_packet" for ref in claim.evidence):
            return "(none)"
        from packages.activity_log import provenance

        try:
            _has_packet, _has_consent, _errors, packets = (
                self._collect_provenance_state(claim.evidence)
            )
        except Exception:  # noqa: BLE001
            # Never let context rendering block a round; voters will see the
            # default "(none)" and reason from the top-level Evidence field.
            return "(none)"
        if not packets:
            return "(none)"
        packet_contexts: list[tuple[str, list[str]]] = []
        rendered_refs: set[tuple[str, str, str]] = set()
        rendered_count = 0
        truncated = False
        per_value_overflow = "[packet metadata exceeds per-value voter context limit]"
        mandatory_exactness_failure = (
            "[packet mandatory metadata cannot be represented exactly in voter context]"
        )

        def sanitize(value: object) -> str:
            return re.sub(
                r"\s+",
                " ",
                str(value)
                .replace("\r", " ")
                .replace("\n", " ")
                .replace("\t", " "),
            ).strip()

        for packet, packet_path in packets:
            raw_digest = packet.get("d") or "(no-digest)"
            digest = sanitize(raw_digest)
            if (
                not isinstance(raw_digest, str)
                or not raw_digest.isprintable()
                or digest != raw_digest
            ):
                return mandatory_exactness_failure
            if len(digest) > 96:
                return per_value_overflow
            consent_hash: Optional[str] = None
            for entry in packet.get("a", []) or []:
                if provenance.entry_has_consent(entry):
                    consent_ref = entry.get("consent_ref") or {}
                    decision = consent_ref.get("decision_action_hash")
                    if isinstance(decision, str) and decision.strip():
                        consent_hash = consent_hash or decision
            nested_refs: list[str] = []
            try:
                metadata_refs, packet_truncated = (
                    provenance.validated_non_packet_evidence_refs(
                        packet_path,
                        workspace_root=self._workspace_root,
                        max_refs=32,
                    )
                )
                truncated = truncated or packet_truncated
                for metadata in metadata_refs:
                    key = (
                        metadata["type"],
                        metadata["ref"],
                        metadata.get("sha256", ""),
                    )
                    if key in rendered_refs:
                        continue
                    if rendered_count >= 32:
                        truncated = True
                        break
                    rendered_refs.add(key)
                    rendered_count += 1
                    nested_refs.append(
                        f"[{sanitize(metadata['type'])[:48]}] "
                        f"{sanitize(metadata['ref'])[:240]}"
                    )
            except ValueError:
                # The top-level packet remains validated for submission, but a
                # changed or otherwise invalid child DAG contributes no context.
                nested_refs = []
            consent_str = sanitize(consent_hash) if consent_hash else "(none)"
            if consent_hash is not None and (
                not consent_hash.isprintable() or consent_str != consent_hash
            ):
                return mandatory_exactness_failure
            if len(consent_str) > 160:
                return per_value_overflow
            packet_contexts.append(
                (
                    f"packet digest={digest} consent_ref={consent_str} "
                    "nested_evidence=",
                    nested_refs,
                )
            )
        context_limit = 4096
        truncated_marker = " [truncated]"
        full_lines = [
            f"{header}{'; '.join(nested_refs) if nested_refs else '(none)'}"
            for header, nested_refs in packet_contexts
        ]
        full_context = " | ".join(full_lines)
        if not truncated and len(full_context) <= context_limit:
            return full_context

        mandatory_length = sum(len(header) for header, _refs in packet_contexts)
        mandatory_length += len(" | ") * (len(packet_contexts) - 1)
        if mandatory_length + len(truncated_marker) > context_limit:
            return "[packet metadata exceeds 4096-character voter context limit]"

        optional_budget = context_limit - mandatory_length - len(truncated_marker)
        bounded_lines: list[str] = []
        optional_open = True
        for header, nested_refs in packet_contexts:
            line = header
            optional_values = nested_refs if nested_refs else ["(none)"]
            if optional_open:
                for index, value in enumerate(optional_values):
                    value_separator = "; " if index else ""
                    segment = f"{value_separator}{value}"
                    if len(segment) > optional_budget:
                        optional_open = False
                        break
                    line += segment
                    optional_budget -= len(segment)
            bounded_lines.append(line)
        return f"{' | '.join(bounded_lines)}{truncated_marker}"

    # ------------------------------------------------------------------
    # Tool 1 — submit_claim
    # ------------------------------------------------------------------

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

        Returns JSON: {"entry_hash": "<64-hex>", "claim_id": "<uuid>"}
        On validation error: {"error": "<message>"}
        """
        try:
            br = BlastRadius(blast_radius)
            pt = ProposalType(proposal_type)
        except ValueError as exc:
            return _err(f"E_SUBMIT_CLAIM_INVALID: {exc}")

        ev_refs: list[EvidenceRef] = []
        for item in evidence or []:
            if not isinstance(item, dict):
                return _err(
                    "E_SUBMIT_CLAIM_INVALID_EVIDENCE: "
                    "evidence items must be objects with 'type' and 'ref'"
                )
            try:
                ref = EvidenceRef(
                    type=item["type"],
                    ref=item["ref"],
                    sha256=item.get("sha256"),
                )
                ref.validate()
                ev_refs.append(ref)
            except (KeyError, TypeError, ValueError) as exc:
                return _err(f"E_SUBMIT_CLAIM_INVALID_EVIDENCE: {exc}")

        # Only validate provenance when a provenance_packet ref is actually
        # present. A non-governed Local/CodeChange claim carrying only ordinary
        # refs (test/spec/commit) must not trigger _validate_provenance_evidence,
        # which imports the provenance extras (blake3/jcs/nacl) that may be absent
        # in lean gateway installs. Governed claims still fail closed below,
        # because has_packet/has_consent stay False without a valid packet.
        if any(ref.type == "provenance_packet" for ref in ev_refs):
            has_packet, has_consent, provenance_errors = (
                self._validate_provenance_evidence(ev_refs)
            )
        else:
            has_packet, has_consent, provenance_errors = False, False, []
        if provenance_errors:
            return _err(
                "E_SUBMIT_CLAIM_INVALID_PROVENANCE: "
                + ";".join(sorted(set(provenance_errors)))
            )
        if _is_governed_claim(pt, br) and (not has_packet or not has_consent):
            return _err(
                "E_GOVERNED_PROVENANCE_REQUIRED: System/Substrate "
                "AdrChange/SpecChange/ConfigChange claims require valid "
                "provenance_packet evidence with consent_ref"
            )

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

    # ------------------------------------------------------------------
    # Tool 2 — cast_vote
    # ------------------------------------------------------------------

    def cast_vote(
        self,
        claim_id: str,
        voter: str,
        weight: float,
        rationale: str,
    ) -> str:
        """Append a Vote entry for a given claim_id.

        weight must be a float in [-CERTAINTY_LIMIT, CERTAINTY_LIMIT].
        Returns JSON: {"entry_hash": "<64-hex>"}
        On validation error: {"error": "<message>"}
        """
        try:
            vote = Vote(voter=voter, weight=weight, rationale=rationale)
            vote.validate()
        except (ValueError, TypeError) as exc:
            return _err(f"E_CAST_VOTE_INVALID: {exc}")

        entries = self._cell.read_chain(limit=None)
        if not any(
            entry.get("type") == "claim"
            and entry.get("content", {}).get("id") == claim_id
            for entry in entries
        ):
            return _err(f"E_CLAIM_NOT_FOUND: no claim with id {claim_id}")
        latest_decision = _latest_decision_for_claim(entries, claim_id)
        decision_error = _terminal_decision_error(claim_id, latest_decision)
        if decision_error is not None:
            return decision_error

        content = {"claim_id": claim_id, **vote.to_dict()}
        h = self._cell.append_entry(
            entry_type="vote",
            author_did=voter,
            content=content,
        )
        return _ok({"entry_hash": h})

    # ------------------------------------------------------------------
    # Tool 3 — get_chain_context
    # ------------------------------------------------------------------

    def get_chain_context(self, limit: int = 20) -> str:
        """Return the most recent source chain entries as a JSON list, newest first.

        Bounded by `limit` to fit within LLM context windows. For Phase 0,
        callers should use limit=20–50. Pagination is a Phase 1 concern.
        """
        entries = self._cell.read_chain(limit=limit)
        return _ok(entries)

    # ------------------------------------------------------------------
    # Tool 4 — get_decision
    # ------------------------------------------------------------------

    def get_decision(self, claim_id: str) -> str:
        """Return the Decision entry content for a given claim_id, or null.

        Scans the chain for the most recent entry of type "decision" whose
        content.claim_id matches. Returns null JSON if not yet decided.
        """
        entries = self._cell.read_chain(limit=None)
        for entry in entries:
            if (
                entry.get("type") == "decision"
                and entry.get("content", {}).get("claim_id") == claim_id
            ):
                return _ok(entry["content"])
        return _ok(None)

    # ------------------------------------------------------------------
    # Tool 5 — list_pending
    # ------------------------------------------------------------------

    def list_pending(self) -> str:
        """Return Claims whose latest Decision is absent or still DEFERRED.

        Returns JSON list of {"claim_id": "<uuid>", "summary": "<text>"}.
        """
        entries = self._cell.read_chain(limit=None)
        latest_outcome_by_claim: dict[str, str] = {}
        for entry in entries:
            if entry.get("type") != "decision":
                continue
            claim_id = entry.get("content", {}).get("claim_id")
            if claim_id and claim_id not in latest_outcome_by_claim:
                latest_outcome_by_claim[claim_id] = entry["content"].get("outcome", "")
        pending = [
            {
                "claim_id": e["content"]["id"],
                "summary": e["content"].get("summary", ""),
                "blast_radius": e["content"].get("blast_radius", ""),
            }
            for e in entries
            if e.get("type") == "claim"
            and latest_outcome_by_claim.get(e.get("content", {}).get("id"))
            in (None, Outcome.DEFERRED.value)
        ]
        return _ok(pending)

    # ------------------------------------------------------------------
    # Tool 6 — run_consensus_round
    #
    # The loop-closer: looks up a pending Claim by id, runs the configured
    # voters against it (default = env-resolved balanced roster),
    # appends every Vote to the chain, then appends the Decision.
    #
    # submit_claim stays passive (spec §5 — router not controller). This
    # tool is where controllability lives, and it is invoked explicitly.
    # ------------------------------------------------------------------

    def run_consensus_round(self, claim_id: str) -> str:
        """Run the active voter roster, folding prior on-chain votes into the tally.

        Looks up the Claim on the source chain by id, refuses to re-run if a
        non-deferred Decision already exists for it, calls the voters from
        `self._voter_factory` (or the LiteLLM default), merges those new votes
        with any existing source-chain votes for the same claim, writes only the
        newly collected Vote entries, then writes the Decision under the
        "metacoordinator" system DID. Claims whose latest Decision is DEFERRED
        may be re-run so additional votes can progress them.

        Returns JSON: the full Decision.to_dict() (outcome, votes, tally_mean,
        tally_variance, etc.). On lookup or validation failure: {"error": ...}.
        """
        entries = self._cell.read_chain(limit=None)
        claim_entry = _find_claim_entry(entries, claim_id)
        if claim_entry is None:
            return _err(f"E_CLAIM_NOT_FOUND: no claim with id {claim_id}")
        latest_decision = _latest_decision_for_claim(entries, claim_id)
        decision_error = _terminal_decision_error(claim_id, latest_decision)
        if decision_error is not None:
            return decision_error

        try:
            claim = _claim_from_chain_entry(claim_entry["content"])
        except (KeyError, ValueError) as exc:
            return _err(f"E_CLAIM_MALFORMED: {exc}")

        try:
            existing_votes_by_voter = _existing_votes_by_voter(entries, claim_id)
        except (KeyError, TypeError, ValueError) as exc:
            return _err(f"E_VOTE_MALFORMED: {exc}")

        try:
            voters = _resolve_voter_factory(self._voter_factory)()
        except Exception as exc:  # noqa: BLE001
            return _err(f"E_VOTER_BUILD_FAILED: {type(exc).__name__}: {exc}")

        try:
            new_votes = _collect_new_votes(
                voters,
                claim,
                existing_votes_by_voter,
                context=self._render_voter_context(claim),
            )
        except Exception as exc:  # noqa: BLE001
            return _err(f"E_CONSENSUS_FAILED: {type(exc).__name__}: {exc}")

        all_votes = [*existing_votes_by_voter.values(), *new_votes]
        if (
            not new_votes
            and latest_decision is not None
            and latest_decision.get("votes") == [vote.to_dict() for vote in all_votes]
        ):
            return _ok(latest_decision)
        outcome, mean, variance = tally(claim, all_votes)
        decision = Decision(
            claim_id=claim.id,
            blast_radius=claim.blast_radius,
            outcome=outcome,
            votes=all_votes,
            tally_mean=mean,
            tally_variance=variance,
        )

        # Append each vote under the voter's identity, then the decision
        # under the system author. If a chain write fails mid-way we accept
        # a partial record — the next list_pending call will see it as
        # still-pending because the decision entry is the last to land.
        try:
            _write_round_results(self._cell, claim_id, new_votes, decision)
        except Exception as exc:  # noqa: BLE001
            return _err(f"E_CHAIN_WRITE_FAILED: {type(exc).__name__}: {exc}")

        return _ok(decision.to_dict())
