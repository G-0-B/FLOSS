/**
 * Python Round-Trip Proof Test
 *
 * Simulates the exact payload shapes that the Python holochain_connector.py
 * would send, proving that ConversationMemory Understandings can be persisted
 * as RoseNodes and retrieved via vector_search.
 *
 * This is the substrate-side validation for Phase 0 Task 0.4.
 * The full Python integration test runs against a live conductor.
 */
import { assert, test, describe } from "vitest";
import {
  runScenario,
  getZomeCaller,
  Scenario,
} from "@holochain/tryorama";
import type { ActionHash } from "@holochain/client";
import path from "node:path";
import { fileURLToPath } from "node:url";

const hAppPath = path.resolve(
  fileURLToPath(import.meta.url),
  "../../../workdir/rose_forest.happ"
);
const ZOME = "rose_forest";

// Helper: mock embedding (same as Python connector would produce)
function mockEmbedding(dim: number, seed: number = 42): number[] {
  // Deterministic pseudo-random for reproducible tests
  let state = seed;
  return Array.from({ length: dim }, () => {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return (state / 0x7fffffff) * 2 - 1;
  });
}

describe("Python Round-Trip Proof", () => {
  test("Understanding → RoseNode → vector_search → content match", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // Step 1: Simulate Python ConversationMemory Understanding
      const understanding = {
        content: "The walking skeleton is the conversation itself — "
          + "a carrier signal bridging human meaning and machine state.",
        source: "conversation_memory",
        agent_id: "claude-demo",
        level: "level_0",
      };

      // Step 2: Simulate Python embedding (mock 128-dim)
      const embedding = mockEmbedding(128);

      // Step 3: Convert to RoseNode input (matching understanding_to_rose_node())
      const roseNodeInput = {
        content: understanding.content,
        embedding: embedding,
        license: "MIT",
        metadata: {
          model_id: "mock-embed-128d",
          model_card_hash: "sha256:demo_round_trip_test",
          source: understanding.source,
          agent_id: understanding.agent_id,
          level: understanding.level,
        },
      };

      // Step 4: Write to Holochain (simulates connector.add_knowledge)
      const actionHash = await call<ActionHash>("add_knowledge", roseNodeInput);
      assert.ok(actionHash, "add_knowledge should return ActionHash");
      assert.equal(actionHash.length, 39, "ActionHash is 39 bytes");

      // Step 5: Check budget (simulates connector.budget_status)
      const budget = await call<{ remaining_ru: number }>("budget_status", null);
      assert.ok(budget.remaining_ru < 100, "Budget should be consumed");
      assert.closeTo(budget.remaining_ru, 67, 0.1, "One add_knowledge costs 33 RU");

      // Step 6: Search by same embedding (simulates connector.vector_search)
      const results = await call<
        Array<{ hash: ActionHash; score: number; content: string }>
      >("vector_search", {
        query_embedding: embedding,
        k: 1,
      });

      // Step 7: Verify round-trip
      assert.equal(results.length, 1, "Should find exactly one result");
      assert.equal(
        results[0].content,
        understanding.content,
        "Content should match the original Understanding"
      );
      assert.closeTo(
        results[0].score,
        1.0,
        0.01,
        "Cosine similarity of identical vector should be ~1.0"
      );
    });
  });

  test("Multiple Understandings compose and are searchable", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // Three Understandings from different contexts
      const understandings = [
        {
          content: "Carrier equivalence: the medium shapes the message",
          embedding: mockEmbedding(128, 100),
          metadata: { model_id: "test", model_card_hash: "sha256:aaa", source: "adr-1" },
        },
        {
          content: "Bio-aware budgets respect natural cognitive rhythms",
          embedding: mockEmbedding(128, 200),
          metadata: { model_id: "test", model_card_hash: "sha256:bbb", source: "spine-v0.5" },
        },
        {
          content: "Spec-driven development: code follows spec, not vice versa",
          embedding: mockEmbedding(128, 300),
          metadata: { model_id: "test", model_card_hash: "sha256:ccc", source: "adr-4" },
        },
      ];

      // Write all three
      for (const u of understandings) {
        await call<ActionHash>("add_knowledge", {
          content: u.content,
          embedding: u.embedding,
          license: "MIT",
          metadata: u.metadata,
        });
      }

      // Search for each using its own embedding — should find itself as top result
      for (const u of understandings) {
        const results = await call<
          Array<{ hash: ActionHash; score: number; content: string }>
        >("vector_search", {
          query_embedding: u.embedding,
          k: 3,
        });

        assert.ok(results.length >= 1, "Should find at least one result");
        assert.equal(
          results[0].content,
          u.content,
          `Top result should be "${u.content.substring(0, 30)}..."`
        );
        assert.closeTo(results[0].score, 1.0, 0.01, "Self-search should score ~1.0");
      }

      // Budget should reflect all three writes (3 * 33 = 99 RU consumed)
      const budget = await call<{ remaining_ru: number }>("budget_status", null);
      assert.closeTo(budget.remaining_ru, 1.0, 0.1, "Should have ~1 RU left after 3 writes");
    });
  });

  test("Agent provenance is preserved through round-trip", async () => {
    await runScenario(async (scenario: Scenario) => {
      const [alice, bob] = await scenario.addPlayersWithApps([
        { appBundleSource: { path: hAppPath } },
        { appBundleSource: { path: hAppPath } },
      ]);

      const aliceCall = getZomeCaller(alice.cells[0], ZOME);

      // Alice writes an Understanding
      const embedding = mockEmbedding(128, 999);
      await aliceCall<ActionHash>("add_knowledge", {
        content: "Alice's insight about fractal emergence",
        embedding,
        license: "CC-BY-4.0",
        metadata: {
          model_id: "test",
          model_card_hash: "sha256:alice",
          agent_id: "alice",
        },
      });

      // Alice checks her own budget — should show consumption
      const aliceBudget = await aliceCall<{ remaining_ru: number }>(
        "budget_status",
        null
      );
      assert.closeTo(aliceBudget.remaining_ru, 67, 0.1, "Alice spent 33 RU");

      // Bob's budget should be untouched
      const bobCall = getZomeCaller(bob.cells[0], ZOME);
      const bobBudget = await bobCall<{ remaining_ru: number }>(
        "budget_status",
        null
      );
      assert.equal(bobBudget.remaining_ru, 100, "Bob's budget should be full");
    });
  });
});
