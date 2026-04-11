/**
 * Phase 0: Substrate Bridge Validation Tests
 *
 * Implements the 6 criteria from docs/specs/phase0-substrate-bridge.spec.md:
 *   1. PUBLISH  — Agent A creates a KnowledgeTriple and receives an ActionHash
 *   2. PROVENANCE — The entry's provenance (author, timestamp, signature) is retrievable
 *   3. VERIFY — Agent B retrieves the entry and confirms content + provenance match
 *   4. QUERY — Agent B discovers the entry via query_triples without knowing the hash
 *   5. FORK-VISIBLE — Conflicting triples from two agents both persist
 *   6. NO PRIVILEGE — Neither agent has special authority
 *
 * Requires: holochain 0.4.4, hc 0.4.4 (provided by nix dev shell)
 * Run:  npm test  (from tests/tryorama/)
 */
import { assert, test, describe } from "vitest";
import {
  runScenario,
  dhtSync,
  getZomeCaller,
  Scenario,
} from "@holochain/tryorama";
import type { ActionHash, AgentPubKey, Record as HcRecord } from "@holochain/client";
import { decode } from "@msgpack/msgpack";
import path from "node:path";
import { fileURLToPath } from "node:url";

// ── Setup ────────────────────────────────────────────
const hAppPath = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../../workdir/rose_forest.happ"
);

const ZOME = "rose_forest";

// Helper types matching coordinator structs
interface TripleResult {
  hash: ActionHash;
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
  author: AgentPubKey;
  created_at: unknown;
}

function assertTimestampLike(value: unknown, label: string): void {
  const isTimestampLike =
    typeof value === "number" ||
    typeof value === "string" ||
    (Array.isArray(value) &&
      value.length === 2 &&
      value.every((part) => typeof part === "number"));

  assert.ok(isTimestampLike, `${label} should include a timestamp-like created_at field`);
}

// ─────────────────────────────────────────────────────
// Substrate Bridge Validation (2-agent, 6 criteria)
// ─────────────────────────────────────────────────────
describe("Substrate Bridge Validation", () => {
  test("Criterion 1: PUBLISH — Agent A creates a triple and receives ActionHash", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const aliceCall = getZomeCaller(alice.cells[0], ZOME);

      const hash = await aliceCall<ActionHash>("assert_triple", {
        subject: "holochain",
        predicate: "is_a",
        object: "distributed_framework",
        confidence: 0.95,
      });

      assert.ok(hash, "assert_triple should return an ActionHash");
      assert.equal(hash.length, 39, "ActionHash should be 39 bytes");
    });
  });

  test("Criterion 2: PROVENANCE — Entry provenance (author, timestamp) is retrievable", async () => {
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const aliceCall = getZomeCaller(alice.cells[0], ZOME);
      const alicePubKey = alice.cells[0].cell_id[1];

      const hash = await aliceCall<ActionHash>("assert_triple", {
        subject: "holochain",
        predicate: "is_a",
        object: "distributed_framework",
        confidence: 0.95,
      });

      // Retrieve the full Record with provenance
      const record = await aliceCall<HcRecord | null>(
        "get_triple_record",
        hash
      );

      assert.ok(record, "get_triple_record should return a Record");

      // Verify provenance fields exist on the signed action
      const signedAction = record!.signed_action;
      assert.ok(signedAction, "Record should have signed_action");
      assert.ok(signedAction.hashed, "signed_action should have hashed content");
      assert.ok(signedAction.signature, "signed_action should have signature");

      const action = signedAction.hashed.content;
      assert.ok(action.author, "Action should have author field");
      assert.ok(action.timestamp, "Action should have timestamp field");

      // Author should be Alice's pubkey
      assert.deepEqual(
        action.author,
        alicePubKey,
        "Entry author should be Alice's agent pubkey"
      );

      // Timestamp should be recent (within 60 seconds)
      const nowMicros = Date.now() * 1000;
      const actionTimestamp =
        typeof action.timestamp === "number"
          ? action.timestamp
          : Number(action.timestamp);
      const ageSecs = Math.abs(nowMicros - actionTimestamp) / 1_000_000;
      assert.ok(
        ageSecs < 60,
        `Timestamp should be recent (within 60s), got ${ageSecs.toFixed(1)}s ago`
      );
    });
  });

  test("Criterion 3: VERIFY — Agent B retrieves entry and confirms content + provenance", async () => {
    await runScenario(async (scenario: Scenario) => {
      const [alice, bob] = await scenario.addPlayersWithApps([
        { appBundleSource: { path: hAppPath } },
        { appBundleSource: { path: hAppPath } },
      ]);

      const aliceCall = getZomeCaller(alice.cells[0], ZOME);
      const bobCall = getZomeCaller(bob.cells[0], ZOME);
      const alicePubKey = alice.cells[0].cell_id[1];

      // Alice creates a triple
      const hash = await aliceCall<ActionHash>("assert_triple", {
        subject: "flossi0ullk",
        predicate: "is_a",
        object: "coordination_protocol",
        confidence: 0.9,
      });

      // Wait for DHT propagation
      await dhtSync([alice, bob], alice.cells[0].cell_id[0]);

      // Bob retrieves the Record by hash
      const record = await bobCall<HcRecord | null>(
        "get_triple_record",
        hash
      );

      assert.ok(record, "Bob should be able to retrieve Alice's record");

      // Verify content matches what Alice wrote — decode the entry bytes
      assert.ok(record!.entry, "Record should have entry data");
      const entryVariant = (record!.entry as { Present?: { entry: Uint8Array } }).Present;
      assert.ok(entryVariant, "Entry should be Present variant (not Hidden/NotApplicable)");
      const tripleData = decode(entryVariant!.entry) as {
        subject: string;
        predicate: string;
        object: string;
        confidence: number;
      };
      assert.equal(
        tripleData.subject,
        "flossi0ullk",
        "Bob's fetched subject must match Alice's input"
      );
      assert.equal(
        tripleData.predicate,
        "is_a",
        "Bob's fetched predicate must match Alice's input"
      );
      assert.equal(
        tripleData.object,
        "coordination_protocol",
        "Bob's fetched object must match Alice's input"
      );
      assert.ok(
        Math.abs(tripleData.confidence - 0.9) < 0.001,
        `Bob's fetched confidence must match Alice's input (got ${tripleData.confidence})`
      );

      // Verify provenance points to Alice, not Bob
      const author = record!.signed_action.hashed.content.author;
      assert.deepEqual(
        author,
        alicePubKey,
        "Provenance should show Alice as author, not Bob"
      );

      const bobPubKey = bob.cells[0].cell_id[1];
      assert.notDeepEqual(
        author,
        bobPubKey,
        "Author should NOT be Bob"
      );
    });
  });

  test("Criterion 3b: VERIFY (negative) — get_triple_record returns null for non-existent hash", async () => {
    // Guards against a contract regression where get_triple_record silently
    // returns an entry from another type (or fabricates one) when asked for a
    // hash that has never been authored. If this test ever passes with a
    // non-null record, the zome's None-handling path is broken.
    await runScenario(async (scenario: Scenario) => {
      const alice = await scenario.addPlayerWithApp({ path: hAppPath });
      const aliceCall = getZomeCaller(alice.cells[0], ZOME);

      // Author one real triple so we have a valid-shape ActionHash to mutate
      const realHash = await aliceCall<ActionHash>("assert_triple", {
        subject: "negative_probe_subject",
        predicate: "is_a",
        object: "negative_probe_object",
        confidence: 0.5,
      });

      // Construct a valid-shape but non-existent ActionHash by XOR-mutating
      // the content bytes (preserving the 3-byte multihash prefix at [0..3)).
      const nonExistentHash = new Uint8Array(realHash);
      for (let i = 3; i < nonExistentHash.length - 4; i++) {
        nonExistentHash[i] = nonExistentHash[i] ^ 0xa5;
      }

      const missing = await aliceCall<HcRecord | null>(
        "get_triple_record",
        nonExistentHash
      );

      assert.equal(
        missing,
        null,
        "get_triple_record must return null (not throw, not fabricate) for a hash that was never authored"
      );

      // Sanity: the real hash still resolves (proves we didn't corrupt state)
      const present = await aliceCall<HcRecord | null>(
        "get_triple_record",
        realHash
      );
      assert.ok(present, "Real hash should still resolve after negative probe");
    });
  });

  test("Criterion 4: QUERY — Agent B discovers entry via query_triples without knowing hash", async () => {
    await runScenario(async (scenario: Scenario) => {
      const [alice, bob] = await scenario.addPlayersWithApps([
        { appBundleSource: { path: hAppPath } },
        { appBundleSource: { path: hAppPath } },
      ]);

      const aliceCall = getZomeCaller(alice.cells[0], ZOME);
      const bobCall = getZomeCaller(bob.cells[0], ZOME);

      // Alice creates a triple
      const hash = await aliceCall<ActionHash>("assert_triple", {
        subject: "rose_forest",
        predicate: "part_of",
        object: "flossi0ullk_ecosystem",
        confidence: 0.88,
      });

      // Wait for DHT propagation
      await dhtSync([alice, bob], alice.cells[0].cell_id[0]);

      // Bob queries by subject — does NOT use the hash
      const bySubject = await bobCall<TripleResult[]>("query_triples", {
        subject: "rose_forest",
      });

      assert.ok(bySubject.length > 0, "Bob should find triple by subject query");
      assert.equal(bySubject[0].subject, "rose_forest");
      assert.equal(bySubject[0].predicate, "part_of");
      assert.equal(bySubject[0].object, "flossi0ullk_ecosystem");
      assert.ok(
        Math.abs(bySubject[0].confidence - 0.88) < 0.01,
        "Confidence should be preserved"
      );
      assert.deepEqual(
        bySubject[0].author,
        alice.cells[0].cell_id[1],
        "Subject query should preserve Alice's provenance author"
      );
      assertTimestampLike(
        bySubject[0].created_at,
        "Subject query result"
      );

      // Also query by predicate
      const byPredicate = await bobCall<TripleResult[]>("query_triples", {
        predicate: "part_of",
      });

      assert.ok(
        byPredicate.length > 0,
        "Bob should find triple by predicate query"
      );
      assert.ok(
        byPredicate.some((r) => r.subject === "rose_forest"),
        "Predicate query should include Alice's triple"
      );
      const predicateMatch = byPredicate.find((r) => r.subject === "rose_forest");
      assert.ok(predicateMatch, "Predicate query should return the authored triple");
      assert.deepEqual(
        predicateMatch!.author,
        alice.cells[0].cell_id[1],
        "Predicate query should preserve Alice's provenance author"
      );
      assertTimestampLike(
        predicateMatch!.created_at,
        "Predicate query result"
      );
    });
  });

  test("Criterion 5: FORK-VISIBLE — Conflicting triples from two agents both persist", async () => {
    await runScenario(async (scenario: Scenario) => {
      const [alice, bob] = await scenario.addPlayersWithApps([
        { appBundleSource: { path: hAppPath } },
        { appBundleSource: { path: hAppPath } },
      ]);

      const aliceCall = getZomeCaller(alice.cells[0], ZOME);
      const bobCall = getZomeCaller(bob.cells[0], ZOME);

      // Alice and Bob create conflicting triples:
      // same subject + predicate, different objects
      const aliceHash = await aliceCall<ActionHash>("assert_triple", {
        subject: "flossi0ullk_nature",
        predicate: "is_a",
        object: "coordination_protocol",
        confidence: 0.9,
      });

      const bobHash = await bobCall<ActionHash>("assert_triple", {
        subject: "flossi0ullk_nature",
        predicate: "is_a",
        object: "memetic_system",
        confidence: 0.85,
      });

      // Wait for both to propagate
      await dhtSync([alice, bob], alice.cells[0].cell_id[0]);

      // Both hashes should be distinct
      assert.notDeepEqual(
        aliceHash,
        bobHash,
        "Conflicting triples should have distinct ActionHashes"
      );

      // Query should return BOTH triples — no silent overwrite
      const results = await aliceCall<TripleResult[]>("query_triples", {
        subject: "flossi0ullk_nature",
      });

      assert.equal(
        results.length,
        2,
        "Both conflicting triples should persist (no silent overwrite)"
      );

      const objects = results.map((r) => r.object).sort();
      assert.deepEqual(
        objects,
        ["coordination_protocol", "memetic_system"],
        "Both objects should be present"
      );

      // Verify they have different hashes (different provenance)
      const hashes = results.map((r) => r.hash);
      assert.notDeepEqual(
        hashes[0],
        hashes[1],
        "Conflicting triples should have different ActionHashes"
      );

      const aliceResult = results.find((r) => r.object === "coordination_protocol");
      const bobResult = results.find((r) => r.object === "memetic_system");
      assert.ok(aliceResult, "Alice's conflicting triple should be query-visible");
      assert.ok(bobResult, "Bob's conflicting triple should be query-visible");
      assert.deepEqual(
        aliceResult!.author,
        alice.cells[0].cell_id[1],
        "Alice's conflicting triple should preserve Alice as author"
      );
      assert.deepEqual(
        bobResult!.author,
        bob.cells[0].cell_id[1],
        "Bob's conflicting triple should preserve Bob as author"
      );
      assertTimestampLike(aliceResult!.created_at, "Alice conflicting result");
      assertTimestampLike(bobResult!.created_at, "Bob conflicting result");
    });
  });

  test("Criterion 6: NO PRIVILEGE — Both agents use identical zome calls, neither is prioritized", async () => {
    await runScenario(async (scenario: Scenario) => {
      const [alice, bob] = await scenario.addPlayersWithApps([
        { appBundleSource: { path: hAppPath } },
        { appBundleSource: { path: hAppPath } },
      ]);

      const aliceCall = getZomeCaller(alice.cells[0], ZOME);
      const bobCall = getZomeCaller(bob.cells[0], ZOME);

      // Both agents create triples using the exact same zome call
      const aliceHash = await aliceCall<ActionHash>("assert_triple", {
        subject: "alice_knowledge",
        predicate: "related_to",
        object: "substrate_bridge_test",
        confidence: 0.8,
      });

      const bobHash = await bobCall<ActionHash>("assert_triple", {
        subject: "bob_knowledge",
        predicate: "related_to",
        object: "substrate_bridge_test",
        confidence: 0.8,
      });

      assert.ok(aliceHash, "Alice can publish");
      assert.ok(bobHash, "Bob can publish");

      await dhtSync([alice, bob], alice.cells[0].cell_id[0]);

      // Both agents can query — same function, same results
      const aliceResults = await aliceCall<TripleResult[]>("query_triples", {
        predicate: "related_to",
      });

      const bobResults = await bobCall<TripleResult[]>("query_triples", {
        predicate: "related_to",
      });

      assert.equal(
        aliceResults.length,
        bobResults.length,
        "Both agents should see the same number of results"
      );

      assert.equal(
        aliceResults.length,
        2,
        "Both triples should be visible"
      );
      for (const result of aliceResults) {
        assert.ok(result.author, "Alice query results should include author provenance");
        assertTimestampLike(result.created_at, "Alice query result");
      }
      for (const result of bobResults) {
        assert.ok(result.author, "Bob query results should include author provenance");
        assertTimestampLike(result.created_at, "Bob query result");
      }

      // Both agents can retrieve each other's records
      const aliceReadsBob = await aliceCall<HcRecord | null>(
        "get_triple_record",
        bobHash
      );
      const bobReadsAlice = await bobCall<HcRecord | null>(
        "get_triple_record",
        aliceHash
      );

      assert.ok(aliceReadsBob, "Alice can read Bob's record");
      assert.ok(bobReadsAlice, "Bob can read Alice's record");

      // Verify provenance is correct (each record authored by original creator)
      assert.deepEqual(
        bobReadsAlice!.signed_action.hashed.content.author,
        alice.cells[0].cell_id[1],
        "Alice's record should be authored by Alice"
      );
      assert.deepEqual(
        aliceReadsBob!.signed_action.hashed.content.author,
        bob.cells[0].cell_id[1],
        "Bob's record should be authored by Bob"
      );
    });
  });
});
