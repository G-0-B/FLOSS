/**
 * ADR-15 — Author/Provenance Binding (end-to-end regression)
 *
 * Scope note (read before extending):
 *   The `rose_forest` coordinator always sets provenance/source/agent to the CALLER's
 *   own key (`agent_info()?.agent_initial_pubkey`). So a forged-provenance entry is NOT
 *   reachable through the production coordinator — it requires a custom client calling
 *   `create_entry` directly. Therefore:
 *     • The forged-provenance REJECTION (provenance != author -> Invalid) is proven by the
 *       Rust unit tests in `zomes/integrity/src/lib.rs` (mod tests).
 *     • This Tryorama suite proves the complementary guarantee: the new R1–R4 binding does
 *       NOT break legitimate self-authored writes (regression guard for the 38 ontology tests).
 *   True end-to-end attacker coverage would need a test-only "attacker" extern that forges
 *   provenance and calls create_entry directly — deliberately out of scope for PR-A.
 *
 * Run:  npm test  (from tests/tryorama/) — requires the built rose_forest.happ.
 */
import { assert, test, describe } from "vitest";
import { runScenario, Scenario, getZomeCaller } from "@holochain/tryorama";
import type { ActionHash } from "@holochain/client";
import path from "node:path";
import { fileURLToPath } from "node:url";

const hAppPath = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../workdir/rose_forest.happ"
);
const ZOME = "rose_forest";

describe("ADR-15 provenance binding (regression: legitimate writes still pass)", () => {
  test("self-authored ThoughtCredential validates and commits", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // Coordinator stamps provenance = alice; the integrity zome's R3 check
      // (provenance == action author) must therefore PASS.
      const hash = await call<ActionHash>("create_thought_credential", {
        content: Array.from({ length: 64 }, () => 0.0), // dim in [32,4096]
        connotation: 0, // ADR-15 R5 (i8->f32) is deferred to PR-B; integer ternary still valid here
        resonance: [],
        impact: 0.5,
      });

      assert.ok(hash, "self-authored credential should commit");
      assert.equal(hash.length, 39, "ActionHash should be 39 bytes");
    });
  });

  test("self-authored KnowledgeTriple validates and commits", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // NOTE: subject/predicate/object must satisfy the ontology domain/range rules
      // in `coordinator/src/ontology.rs`; adjust if these specific values are rejected
      // for ontology reasons (that would be unrelated to the ADR-15 R4 source binding).
      const hash = await call<ActionHash>("assert_triple", {
        subject: "concept:rose",
        predicate: "related_to",
        object: "concept:forest",
        confidence: 0.5,
      });

      assert.ok(hash, "self-authored triple should commit (R4 source == author)");
    });
  });
});
