/**
 * Rose Forest Integration Tests
 *
 * Tests the Holochain zome functions via tryorama.
 * Requires: holochain 0.4.4, hc 0.4.4 (provided by nix dev shell)
 *
 * Run:  npm test  (from tests/tryorama/)
 */
import { assert, test, describe } from "vitest";
import {
  runScenario,
  dhtSync,
  getZomeCaller,
  Scenario,
} from "@holochain/tryorama";
import type { ActionHash } from "@holochain/client";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Path to the .happ bundle (built by: hc app pack workdir/)
const hAppPath = path.resolve(
  fileURLToPath(import.meta.url),
  "../../workdir/rose_forest.happ"
);

// Zome name matches the coordinator crate name in dna.yaml
const ZOME = "rose_forest";

// Helper: generate a random embedding of given dimension
function randomEmbedding(dim: number): number[] {
  return Array.from({ length: dim }, () => Math.random() * 2 - 1);
}

// ─────────────────────────────────────────────────────────
// Test Suite: RoseNode (add_knowledge + vector_search)
// ─────────────────────────────────────────────────────────

describe("RoseNode", () => {
  test("add_knowledge creates a node and returns an ActionHash", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      const hash = await call<ActionHash>("add_knowledge", {
        content: "The walking skeleton is the conversation itself",
        embedding: randomEmbedding(128),
        license: "MIT",
        metadata: {
          model_id: "test-embed-v1",
          model_card_hash: "sha256:abc123def456",
        },
      });

      assert.ok(hash, "add_knowledge should return a hash");
      assert.equal(hash.length, 39, "ActionHash should be 39 bytes");
    });
  });

  test("vector_search finds a node by embedding similarity", async () => {
    await runScenario(async (scenario: Scenario) => {
      const [alice, bob] = await scenario.addPlayersWithApps([
        { appBundleSource: { path: hAppPath } },
        { appBundleSource: { path: hAppPath } },
      ]);

      const aliceCall = getZomeCaller(alice.cells[0], ZOME);
      const bobCall = getZomeCaller(bob.cells[0], ZOME);

      // Alice creates a node
      const embedding = randomEmbedding(128);
      const hash = await aliceCall<ActionHash>("add_knowledge", {
        content: "Carrier equivalence principle",
        embedding,
        license: "Apache-2.0",
        metadata: {
          model_id: "test-embed-v1",
          model_card_hash: "sha256:abc123def456",
        },
      });

      // Wait for DHT propagation
      await dhtSync([alice, bob], alice.cells[0].cell_id[0]);

      // Bob searches using the same embedding (should get perfect match)
      const results = await bobCall<
        Array<{ hash: ActionHash; score: number; content: string }>
      >("vector_search", {
        query_embedding: embedding,
        k: 5,
      });

      assert.ok(results.length > 0, "Should find at least one result");
      assert.equal(results[0].content, "Carrier equivalence principle");
      // Cosine similarity of a vector with itself = 1.0
      assert.closeTo(results[0].score, 1.0, 0.01);
    });
  });

  test("validation rejects invalid license", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      try {
        await call<ActionHash>("add_knowledge", {
          content: "Should fail validation",
          embedding: randomEmbedding(128),
          license: "PROPRIETARY",
          metadata: {
            model_id: "test-embed-v1",
            model_card_hash: "sha256:abc123def456",
          },
        });
        assert.fail("Should have thrown on invalid license");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_LICENSE"),
          `Error should mention E_LICENSE, got: ${e}`
        );
      }
    });
  });

  test("validation rejects missing model_card_hash", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      try {
        await call<ActionHash>("add_knowledge", {
          content: "Should fail model card check",
          embedding: randomEmbedding(128),
          license: "MIT",
          metadata: { model_id: "test" },
        });
        assert.fail("Should have thrown on missing model_card_hash");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_MODEL_CARD_MISSING"),
          `Error should mention E_MODEL_CARD_MISSING, got: ${e}`
        );
      }
    });
  });
});

// ─────────────────────────────────────────────────────────
// Test Suite: KnowledgeEdge (link_edge)
// ─────────────────────────────────────────────────────────

describe("KnowledgeEdge", () => {
  test("link_edge connects two nodes", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // Create two nodes
      const nodeA = await call<ActionHash>("add_knowledge", {
        content: "Node A",
        embedding: randomEmbedding(128),
        license: "MIT",
        metadata: {
          model_id: "test",
          model_card_hash: "sha256:aaa",
        },
      });

      const nodeB = await call<ActionHash>("add_knowledge", {
        content: "Node B",
        embedding: randomEmbedding(128),
        license: "MIT",
        metadata: {
          model_id: "test",
          model_card_hash: "sha256:bbb",
        },
      });

      // Link them
      const edgeHash = await call<ActionHash>("link_edge", {
        from: nodeA,
        to: nodeB,
        relationship: "supports",
        confidence: 0.85,
      });

      assert.ok(edgeHash, "link_edge should return a hash");
    });
  });

  test("validation rejects invalid relationship type", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      const nodeA = await call<ActionHash>("add_knowledge", {
        content: "Node A",
        embedding: randomEmbedding(128),
        license: "MIT",
        metadata: { model_id: "test", model_card_hash: "sha256:aaa" },
      });
      const nodeB = await call<ActionHash>("add_knowledge", {
        content: "Node B",
        embedding: randomEmbedding(128),
        license: "MIT",
        metadata: { model_id: "test", model_card_hash: "sha256:bbb" },
      });

      try {
        await call<ActionHash>("link_edge", {
          from: nodeA,
          to: nodeB,
          relationship: "INVALID_TYPE",
          confidence: 0.5,
        });
        assert.fail("Should have thrown on invalid relationship");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_RELATIONSHIP"),
          `Error should mention E_RELATIONSHIP, got: ${e}`
        );
      }
    });
  });
});

// ─────────────────────────────────────────────────────────
// Test Suite: BudgetEntry (budget_status + exhaustion)
// ─────────────────────────────────────────────────────────

describe("BudgetEntry", () => {
  test("budget_status returns initial 100 RU", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      const status = await call<{
        agent: Uint8Array;
        remaining_ru: number;
        window_start: [number, number];
      }>("budget_status", null);

      assert.ok(status, "budget_status should return state");
      assert.equal(status.remaining_ru, 100.0, "Fresh budget should be 100 RU");
    });
  });

  test("add_knowledge consumes 33 RU from budget", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // Create one node (costs 33 RU)
      await call<ActionHash>("add_knowledge", {
        content: "Budget test",
        embedding: randomEmbedding(128),
        license: "MIT",
        metadata: { model_id: "test", model_card_hash: "sha256:abc" },
      });

      const status = await call<{ remaining_ru: number }>(
        "budget_status",
        null
      );
      assert.closeTo(status.remaining_ru, 67.0, 0.1, "Should have 67 RU left");
    });
  });

  test("budget exhaustion prevents further actions", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      const makeNode = (n: number) => ({
        content: `Budget exhaust node ${n}`,
        embedding: randomEmbedding(128),
        license: "MIT",
        metadata: { model_id: "test", model_card_hash: "sha256:abc" },
      });

      // Create 3 nodes (3 * 33 = 99 RU, leaving 1 RU)
      await call<ActionHash>("add_knowledge", makeNode(1));
      await call<ActionHash>("add_knowledge", makeNode(2));
      await call<ActionHash>("add_knowledge", makeNode(3));

      // 4th node should fail (needs 33 RU, only 1 left)
      try {
        await call<ActionHash>("add_knowledge", makeNode(4));
        assert.fail("Should have thrown E_BUDGET_EXCEEDED");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_BUDGET_EXCEEDED"),
          `Error should mention E_BUDGET_EXCEEDED, got: ${e}`
        );
      }
    });
  });
});

// ─────────────────────────────────────────────────────────
// Test Suite: ThoughtCredential
// ─────────────────────────────────────────────────────────

describe("ThoughtCredential", () => {
  test("create_thought_credential succeeds with valid input", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      const hash = await call<ActionHash>("create_thought_credential", {
        content: randomEmbedding(128),
        connotation: 1,
        resonance: [alice.agentPubKey],
        impact: 0.8,
      });

      assert.ok(hash, "Should return credential hash");
    });
  });

  test("validation rejects out-of-range connotation", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      try {
        await call<ActionHash>("create_thought_credential", {
          content: randomEmbedding(128),
          connotation: 5, // out of [-1, 1]
          resonance: [],
          impact: 0.5,
        });
        assert.fail("Should have thrown on invalid connotation");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_CONNOTATION"),
          `Error should mention E_CONNOTATION, got: ${e}`
        );
      }
    });
  });

  test("validation rejects embedding dimension < 32", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      try {
        await call<ActionHash>("create_thought_credential", {
          content: randomEmbedding(10), // too small
          connotation: 0,
          resonance: [],
          impact: 0.5,
        });
        assert.fail("Should have thrown on too-small embedding");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_THOUGHT_CONTENT_DIM"),
          `Error should mention E_THOUGHT_CONTENT_DIM, got: ${e}`
        );
      }
    });
  });
});
