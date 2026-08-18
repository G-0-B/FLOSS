# KnowledgeTriple Extraction — Annotation Guidelines + Pioneer Contract (WS3)

```yaml
# --- UpgradableArtifact Header ---
id: "fable5-ws3-kt-annotation-guidelines"
version: "1.0.0"
kind: "annotation_guidelines"
status: "Accepted"
updated: "2026-07-04"
supersedes: []
truth_status: "Specified"   # guidelines + seed authored & machine-checked; fine-tune parity gate not yet run
evidence_sources:
  - "FLOSS/docs/specs/knowledge-triple.spec.md v1.0.0 (canonical; docs/architecture copy is a duplicate — WS4 F8a)"
  - "FLOSS/evals/knowledge_triple_extraction/pioneer_seed.jsonl (52 items, machine-validated, zero eval contamination)"
  - "Operator confirmations 2026-07-04: Pioneer Pro tier (weight download) + per-call learn-flag on API calls"
generator: "claude-fable-5"
sprint: "2026-07-03-fable5-sprint-handoff.md (WS3)"
upgrade_path: "Extend seed to 150-300 items post-window: retained models generate candidates FOLLOWING these guidelines; every candidate passes the §6 QA gate before earning learn_flag"
rollback_plan: "Do not deploy the fine-tune; seed remains useful as additional eval data"
friction_tier: "low"
```

## 1. Task definition

Input: a short natural-language text + a **registered predicate allowlist**.
Output: JSON `{"triples": [{"subject", "predicate", "object", "confidence"}]}` —
the set of `KnowledgeTriple`s the text *positively asserts*, conforming to
`knowledge-triple.spec.md` v1.0.0. The extractor is a **narrow model**: it
extracts; it never invents, infers across texts, or validates ontology
registration (the symbolic layer does that — logic validates, neural assists).

## 2. Decision rules (annotate by these; the model learns these)

| # | Rule | Consequence |
|---|---|---|
| R1 | **Positive assertion only.** Negated ("does not depend"), conditional ("if the vote passes"), future ("will supersede"), and generic/class-level ("most nodes...") statements produce **nothing** | Empty output is a first-class correct answer — ~20% of the seed set is empty-golden |
| R2 | **Allowlist discipline.** A fact whose relation has no registered predicate is **skipped**, never shoehorned into a neighboring predicate (marriage ≠ foaf:knows) | Partial extraction from multi-fact sentences is normal |
| R3 | **Entities → URIs, values → literals.** Named entities: `urn:entity:<kebab-slug>`. Unnamed-but-asserted actors: blank node `_:<slug>`. Dates/numbers/names/licenses: plain string literals, quotes stripped, no invented units | INV-001 |
| R4 | **Confidence mirrors the text, capped < 1.0** (LlmExtraction, INV-006): clean assertion 0.85–0.9 · attributed/indirect 0.6–0.8 · single hedge 0.5–0.65 · double hedge 0.4–0.5 · ambiguous antecedent −0.2 to −0.3 penalty | Never 1.0, even for "water is H2O" |
| R5 | **Dedup** (INV-010): restatement, active/passive flips, and emphasis produce one triple | |
| R6 | **Self-contradiction → empty.** If the text asserts and retracts within itself, extract neither direction | |
| R7 | **Direction-flipping predicates:** "X acquired Y" → `Y acquiredBy X`; "A authored B" → `B creator A`. Follow the predicate's meaning, not surface order | |
| R8 | **Coreference resolves within the text only.** Pronouns bind to the most salient in-text antecedent; if genuinely ambiguous, extract the most salient reading at reduced confidence (R4) or skip | |

## 3. Seed data

`FLOSS/evals/knowledge_triple_extraction/pioneer_seed.jsonl` — **52 items,
split "train"**, provenance-tagged per item (`generator: claude-fable-5`,
date, `source: synthetic|derived-from-repo`, `learn_flag: true`,
QA note). Composition: ~40% clean single/multi-fact, ~20% empty-golden traps
(R1/R6), ~15% allowlist discipline (R2), plus dedup, blank-node, coreference,
noise-robustness, literal-format, and 8 derived-from-repo items using real
FLOSSI0ULLK doc sentences.

**Split discipline (hard):**
- `pioneer_seed.jsonl` (train) → Pioneer fine-tuning. ✅
- `dev.jsonl` → prompt/hyperparameter iteration. Never into training data.
- `heldout.jsonl` → **final parity gate only.** Never seen by Pioneer, any
  optimizer, or any human-in-the-loop selection step. Contamination burns the split.
- Machine-checked: seed generator refuses to emit any item whose text matches an eval item.

**Growth path to 150–300:** retained models (successor roster) generate
candidate items *following this document*; each candidate passes §6 QA before
inclusion. Fable 5 is not required for expansion — that is the point of
writing the rules down.

## 4. Pioneer task prompt (fine-tune + inference contract)

System prompt for the extractor (train and serve with the same one):

```text
You are a KnowledgeTriple extractor for the FLOSSI0ULLK knowledge commons.
Given TEXT and REGISTERED_PREDICATES, output exactly one JSON object:
{"triples": [{"subject": "...", "predicate": "...", "object": "...", "confidence": 0.0-0.999}]}
Rules: extract only facts the text positively asserts about specific entities;
use only predicates from REGISTERED_PREDICATES (skip facts that fit none);
entities are urn:entity:<slug> URIs or _:<slug> blank nodes, values are plain
strings; confidence mirrors the text's certainty and is always < 1.0; negated,
conditional, future, generic, and self-contradicted statements produce nothing;
state each fact once. If no facts qualify: {"triples": []}.
Output the JSON object and nothing else.
```

**Base model:** Qwen-class, Apache-2.0 (weight sovereignty; **Pro tier
confirmed 2026-07-04** — download weights after each fine-tune and archive the
checkpoint hash alongside the seed-set version that produced it).

## 5. ToS + learn-flag discipline (hard constraints)

1. **Policy hold (corrected 2026-08-11).** Anthropic's current
   [Commercial Terms](https://www.anthropic.com/legal/commercial-terms) §D.4
   do not expose the previously claimed classifier/extractor carve-out. Do not
   fine-tune a third-party model on Claude-origin output without express written
   approval. Narrow task scope alone does not satisfy this gate.
2. **No general conversation logs** in any Pioneer training set. Only items
   from this seed lineage (or its QA-gated extensions).
3. **Per-call learn-flag proposal** (operator-reported mechanism, 2026-07-04):
   - Default for ALL API traffic: **no-learn**. Especially: any call whose
     content originates from Claude/frontier-model sessions.
   - Learn-flag is set **only** on calls whose payload is a QA-passed,
     provenance-tagged item from this lineage (`learn_flag: true` in the item).
   - `learn_flag` in repository data is metadata, not machine enforcement. The
     WS3 adaptive-inference hold therefore **remains active** until policy
     approval and a fail-closed ingestion boundary are independently verified.
4. **Provenance survives the pipeline:** checkpoint metadata records seed-set
   file + sha256, item count, and date, so any future audit can walk model → data → generator.

## 6. QA gate for new items (post-window expansion)

An item earns `learn_flag: true` only if ALL pass:
- [ ] Machine validation: URI shapes, allowlist membership, confidence ∈ (0,1), per-item dedup (the seed generator's validator, or equivalent).
- [ ] Zero text overlap with `dev.jsonl` / `heldout.jsonl`.
- [ ] A retained model applying the WS1 KTE rubric to the item's golden agrees it is correct (spot disagreement → human review, not silent inclusion).
- [ ] Rationale note present (one line: which rule(s) the item exercises).

## 7. Acceptance gate for the fine-tune (from sprint packet)

> ⚠️ **HOLD added 2026-07-04 (F10):** do not *launch* the fine-tune until the
> KnowledgeTriple contract divergence is reconciled (spec.md URI predicates +
> [0,1] confidence vs schema.json/zome enum predicates + [-1,+1] signed
> gradient — see the banner in `docs/specs/knowledge-triple.spec.md` and F10 in
> the adversarial review). Seed data remains valid: confidences embed into
> [0,1] ⊂ [-1,+1] unchanged; predicates remap by table if the enum side wins.
> Authoring/expansion under these guidelines continues unaffected.

Deploy only if: Pioneer fine-tune ≥ parity with the best retained API model on
`heldout.jsonl` at materially lower latency/cost. Below parity → document the
gap, keep the artifacts (they remain evals), do not deploy. Either result is
logged as a source-chain claim with the eval numbers as evidence.

## 8. Sprint bookkeeping

Doc **5 of 6**. Data files exempt (seed JSONL lives in the existing eval
directory). Orient self-audit: T1 reads only (spec already in context from
WS1; operator answers from conversation); no `_reference/`; no ADR-governed
change; source chain untouched.
