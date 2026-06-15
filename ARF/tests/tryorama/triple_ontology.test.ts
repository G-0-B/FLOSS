/**
 * Phase 1: Knowledge Triple & Ontology Tests
 *
 * Proves:
 *   1. KnowledgeTriple payloads validate against JSON Schema
 *   2. assert_triple creates triples with ontology validation
 *   3. query_triples retrieves by subject and predicate
 *   4. Domain/range constraints are enforced
 *   5. Invalid predicates are rejected
 *   6. Budget is consumed per triple assertion
 *   7. get_predicates returns the registered ontology
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
import { readFileSync } from "node:fs";
import Ajv from "ajv/dist/2020.js";

// ── Setup ────────────────────────────────────────────
const hAppPath = path.resolve(
  fileURLToPath(import.meta.url),
  "../../workdir/rose_forest.happ"
);

const ZOME = "rose_forest";

const specsDir = path.resolve(
  fileURLToPath(import.meta.url),
  "../../../../docs/specs"
);

const knowledgeTripleSchema = JSON.parse(
  readFileSync(path.join(specsDir, "knowledge-triple.schema.json"), "utf-8")
);

const ajv = new Ajv({ strict: false });
const validateKnowledgeTriple = ajv.compile(knowledgeTripleSchema);

// ─────────────────────────────────────────────────────
// Suite 1: Schema validation (offline, no Holochain)
// ─────────────────────────────────────────────────────
describe("KnowledgeTriple Schema Validation (offline)", () => {
  test("valid KnowledgeTriple payload passes schema", () => {
    const payload = {
      subject: "Claude-Sonnet-4",
      predicate: "capable_of",
      object: "coding_capability",
      confidence: 0.95,
      source: "uhCAkAgentPubKeyHere",
      created_at: [1710000000, 0],
    };
    const valid = validateKnowledgeTriple(payload);
    assert.ok(valid, `Schema errors: ${JSON.stringify(validateKnowledgeTriple.errors)}`);
  });

  test("KnowledgeTriple with invalid predicate fails schema", () => {
    const payload = {
      subject: "entity_a",
      predicate: "INVENTED_RELATION",
      object: "entity_b",
      confidence: 0.5,
      source: "uhCAkAgent",
      created_at: [1710000000, 0],
    };
    assert.ok(!validateKnowledgeTriple(payload), "Should fail on invalid predicate");
  });

  test("KnowledgeTriple with out-of-range confidence fails schema (above)", () => {
    const payload = {
      subject: "entity_a",
      predicate: "is_a",
      object: "Entity",
      confidence: 1.5,
      source: "uhCAkAgent",
      created_at: [1710000000, 0],
    };
    assert.ok(!validateKnowledgeTriple(payload), "Should fail on confidence > 1.0");
  });

  test("KnowledgeTriple with out-of-range confidence fails schema (below)", () => {
    const payload = {
      subject: "entity_a",
      predicate: "is_a",
      object: "Entity",
      confidence: -1.5,
      source: "uhCAkAgent",
      created_at: [1710000000, 0],
    };
    assert.ok(!validateKnowledgeTriple(payload), "Should fail on confidence < -1.0");
  });

  test("KnowledgeTriple with negative confidence is valid (signed gradient)", () => {
    const payload = {
      subject: "entity_a",
      predicate: "contradicts",
      object: "entity_b",
      confidence: -0.8,
      source: "uhCAkAgent",
      created_at: [1710000000, 0],
    };
    assert.ok(validateKnowledgeTriple(payload), "Negative confidence should be valid in [-1,+1]");
  });

  test("KnowledgeTriple with empty subject fails schema", () => {
    const payload = {
      subject: "",
      predicate: "is_a",
      object: "Entity",
      confidence: 0.5,
      source: "uhCAkAgent",
      created_at: [1710000000, 0],
    };
    assert.ok(!validateKnowledgeTriple(payload), "Should fail on empty subject");
  });

  test("all 15 predicates are valid", () => {
    const predicates = [
      "is_a", "part_of", "related_to", "has_property",
      "trained_on", "improves_upon", "capable_of", "evaluated_on",
      "relates_to", "supports", "contradicts",
      "heals", "releases", "neutralizes", "recalibrates",
    ];
    for (const pred of predicates) {
      const payload = {
        subject: "test_entity",
        predicate: pred,
        object: "other_entity",
        confidence: 0.8,
        source: "uhCAkAgent",
        created_at: [1710000000, 0],
      };
      const valid = validateKnowledgeTriple(payload);
      assert.ok(valid, `Predicate '${pred}' should be valid: ${JSON.stringify(validateKnowledgeTriple.errors)}`);
    }
  });
});

// ─────────────────────────────────────────────────────
// Suite 2: Holochain integration tests
// ─────────────────────────────────────────────────────
describe("KnowledgeTriple Holochain Integration", () => {
  test("assert_triple creates and query_triples retrieves by subject", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // Assert a triple
      const hash = await call<ActionHash>("assert_triple", {
        subject: "Claude-Sonnet-4",
        predicate: "capable_of",
        object: "coding_capability",
        confidence: 0.95,
      });
      assert.ok(hash, "assert_triple should return ActionHash");

      // Query by subject
      const results = await call<Array<{
        hash: ActionHash;
        subject: string;
        predicate: string;
        object: string;
        confidence: number;
      }>>("query_triples", {
        subject: "Claude-Sonnet-4",
      });

      assert.equal(results.length, 1, "Should find one triple for subject");
      assert.equal(results[0].subject, "Claude-Sonnet-4");
      assert.equal(results[0].predicate, "capable_of");
      assert.equal(results[0].object, "coding_capability");
      assert.ok(results[0].confidence > 0.9, "Confidence preserved");
    });
  });

  test("assert_triple accepts negative confidence in signed range", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      await call<ActionHash>("assert_triple", {
        subject: "entity_a",
        predicate: "contradicts",
        object: "entity_b",
        confidence: -0.8,
      });

      const results = await call<Array<{
        hash: ActionHash;
        subject: string;
        predicate: string;
        object: string;
        confidence: number;
        author: unknown;
        created_at: unknown;
      }>>("query_triples", {
        subject: "entity_a",
      });

      assert.equal(results.length, 1, "Should retrieve one signed-negative triple");
      assert.equal(results[0].confidence, -0.8, "Negative confidence should round-trip exactly");

      const schemaPayload = {
        subject: results[0].subject,
        predicate: results[0].predicate,
        object: results[0].object,
        confidence: results[0].confidence,
        source: results[0].author,
        created_at: results[0].created_at,
      };
      assert.ok(
        validateKnowledgeTriple(schemaPayload),
        `Retrieved triple should still satisfy schema: ${JSON.stringify(validateKnowledgeTriple.errors)}`
      );
    });
  });

  test("query_triples retrieves by predicate", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // Assert two triples with same predicate
      await call<ActionHash>("assert_triple", {
        subject: "Claude-Sonnet-4",
        predicate: "improves_upon",
        object: "Claude-Sonnet-3.5_model",
        confidence: 0.9,
      });
      await call<ActionHash>("assert_triple", {
        subject: "GPT-4",
        predicate: "improves_upon",
        object: "GPT-3.5_model",
        confidence: 0.85,
      });

      // Query by predicate
      const results = await call<Array<{
        hash: ActionHash;
        subject: string;
        predicate: string;
        object: string;
        confidence: number;
      }>>("query_triples", {
        predicate: "improves_upon",
      });

      assert.equal(results.length, 2, "Should find two triples for predicate");
      const subjects = results.map((r) => r.subject).sort();
      assert.deepEqual(subjects, ["Claude-Sonnet-4", "GPT-4"]);
    });
  });

  test("assert_triple rejects unknown predicate", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      try {
        await call<ActionHash>("assert_triple", {
          subject: "entity_a",
          predicate: "MADE_UP_RELATION",
          object: "entity_b",
          confidence: 0.5,
        });
        assert.fail("Should reject unknown predicate");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_TRIPLE_PREDICATE"),
          `Error should mention predicate: ${e}`
        );
      }
    });
  });

  test("assert_triple consumes budget (2 RU per triple)", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // Check initial budget
      const before = await call<{ remaining_ru: number }>("budget_status", null);
      assert.equal(before.remaining_ru, 100, "Fresh budget should be 100 RU");

      // Assert a triple (costs 2 RU)
      await call<ActionHash>("assert_triple", {
        subject: "test_entity",
        predicate: "is_a",
        object: "Entity",
        confidence: 0.8,
      });

      const after = await call<{ remaining_ru: number }>("budget_status", null);
      assert.equal(after.remaining_ru, 98, "Should have consumed 2 RU");
    });
  });

  test("get_predicates returns all registered predicates", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      const predicates = await call<Array<{ name: string; category: string }>>(
        "get_predicates",
        null
      );

      assert.equal(predicates.length, 15, "Should have 15 registered predicates");

      const baseCount = predicates.filter((p) => p.category === "base").length;
      const aiMlCount = predicates.filter((p) => p.category === "ai_ml").length;
      const knowledgeCount = predicates.filter((p) => p.category === "knowledge").length;

      assert.equal(baseCount, 4, "4 base predicates");
      assert.equal(aiMlCount, 4, "4 AI/ML predicates");
      assert.equal(knowledgeCount, 7, "7 knowledge predicates");
    });
  });

  test("domain/range violation is rejected by coordinator", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const call = getZomeCaller(alice.cells[0], ZOME);

      // "trained_on" requires subject=AIModel, object=Dataset
      // Using a non-model subject should fail domain check
      try {
        await call<ActionHash>("assert_triple", {
          subject: "some_random_entity",
          predicate: "trained_on",
          object: "some_dataset",
          confidence: 0.8,
        });
        assert.fail("Should reject domain violation");
      } catch (e: any) {
        assert.ok(
          String(e).includes("E_ONTOLOGY_VIOLATION"),
          `Error should mention ontology violation: ${e}`
        );
      }
    });
  });
});
