/**
 * Consent Gate integration tests.
 *
 * Covers ADR-12's first substrate loop:
 *   ConsentPayload create -> ConsentDecision create -> retrieve linked decisions.
 *
 * Run from C:\~shit\FLOSS\ARF\tests\tryorama after packing workdir/rose_forest.happ.
 */
import { assert, describe, test } from "vitest";
import {
  getZomeCaller,
  runScenario,
  Scenario,
} from "@holochain/tryorama";
import type { ActionHash } from "@holochain/client";
import path from "node:path";
import { fileURLToPath } from "node:url";

const hAppPath = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../workdir/rose_forest.happ"
);

const ZOME = "consent";

function validConsentPayload() {
  return {
    payload_id: "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0101",
    pattern_id: "ADR-12",
    pattern_type: "Adr",
    pattern_hash: "a".repeat(64),
    proposer_did: "did:floss:alice",
    recipient_did: "did:floss:bob",
    blast_radius: "System",
    consent_scope: ["ReadOnly", "Integrate"],
    refusal_modes: null,
    refusable_until: null,
    parent_consent_id: null,
    rationale: "Tryorama coverage for ADR-12 consent records",
    submitted_at: null,
  };
}

describe("Consent Gate", () => {
  test("creates a ConsentPayload, creates a bounded ConsentDecision, and lists linked decisions", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      const payloadHash = await call<ActionHash>(
        "create_consent_payload",
        validConsentPayload()
      );
      assert.ok(payloadHash, "create_consent_payload should return an ActionHash");

      const payload = await call<any>("get_consent_payload", payloadHash);
      assert.equal(payload.pattern_id, "ADR-12");
      assert.deepEqual(payload.consent_scope, ["ReadOnly", "Integrate"]);

      const decisionHash = await call<ActionHash>("create_consent_decision", {
        decision_id: "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0102",
        payload_action_hash: payloadHash,
        decider_did: "did:floss:bob",
        outcome: "BoundedAccept",
        scope_granted: ["ReadOnly"],
        rationale: "Read-only inspection is acceptable; integration remains gated.",
        counter_frame_ref: null,
        expires_at: null,
        decided_at: null,
      });
      assert.ok(decisionHash, "create_consent_decision should return an ActionHash");

      const decision = await call<any>("get_consent_decision", decisionHash);
      assert.equal(decision.outcome, "BoundedAccept");
      assert.deepEqual(decision.scope_granted, ["ReadOnly"]);

      const linked = await call<Array<[ActionHash, any]>>(
        "get_consent_decisions_for_payload",
        payloadHash
      );
      assert.equal(linked.length, 1);
      assert.deepEqual(linked[0][0], decisionHash);
      assert.equal(linked[0][1].decision_id, "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0102");
    });
  });

  test("rejects a ConsentDecision that grants scope not requested by the payload", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      const payloadHash = await call<ActionHash>(
        "create_consent_payload",
        validConsentPayload()
      );

      try {
        await call<ActionHash>("create_consent_decision", {
          decision_id: "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0103",
          payload_action_hash: payloadHash,
          decider_did: "did:floss:bob",
          outcome: "Accepted",
          scope_granted: ["Bind"],
          rationale: null,
          counter_frame_ref: null,
          expires_at: null,
          decided_at: null,
        });
        assert.fail("Decision should reject unrequested Bind scope");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_SCOPE_NOT_REQUESTED"),
          `Error should mention E_SCOPE_NOT_REQUESTED, got: ${e}`
        );
      }
    });
  });
});
