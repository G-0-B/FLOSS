---
id: project-adr19-ratification-deferred-to-consent-gate
type: project
created: '2026-07-26'
status: active
applies_to:
- any-agent
source: operator_decision
title: ADR-19 consensus ratification is deferred until the consent gate exists — do not re-attempt
---

**Do not submit a consensus claim to ratify ADR-19.** The operator decided on 2026-07-26 to defer ratification until the consent gate (ADR-12) exists. ADR-19 stands as **Accepted (operator-consented)** and is fully live — daemons on :7331/:7332, `FLOSS_MODEL_BACKEND=omniroute` is the default in `FLOSS/.env`.

**Why it is blocked, so the wall is not rediscovered:** a System-radius `AdrChange` claim fails closed with `E_GOVERNED_PROVENANCE_REQUIRED` unless its evidence includes a `provenance_packet` carrying `consent_ref.decision_action_hash`. There is no convention for that field — 0 of 105 packets under `.agent-surface/provenance/` carry a `consent_ref`. Worse, `entry_has_consent()` in `packages/activity_log/provenance.py` only checks the value is a non-empty string; it never resolves it. So the gate can be passed with any invented value, and that is exactly why it must not be.

Deciding what `decision_action_hash` anchors to *is* consent-gate design. ADR-5's standing rule forbids starting that silently, and see [[project-adr-suite-v2-canonical]] — ADR-12 is named there as the most important unresolved item in the suite.

**How to apply:**
- If asked to "submit the ADR-19 claim" or to clear the consensus-pending status, cite this decision instead of attempting it.
- Do not satisfy `consent_ref` with a git commit SHA, a session id, or any placeholder. The field means a source-chain action hash; putting anything else there bakes a type confusion into permanent provenance.
- The claim body and its evidence are already verified and ready — only the consent anchor is missing. Stage 3.5 (equivalence) was closed 2026-07-26: litellm and omniroute produced identical weights (−0.400 ×3), identical mean/variance, both PASS.
- When ADR-12 lands and defines how consent decisions are recorded, this claim becomes submittable as-is.
