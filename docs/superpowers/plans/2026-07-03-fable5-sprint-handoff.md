# Fable 5 Sprint — Claude Code Handoff Packet

```yaml
# --- UpgradableArtifact Header ---
id: "fable5-sprint-handoff"
version: "1.0.0"
kind: "handoff_packet"
status: "Proposed"
updated: "2026-07-03"
supersedes: []
truth_status: "Specified"   # plan, not results
evidence_sources:
  - "Fable 5 research report: model-improves-model survey (claude.ai session, 2026-07)"
  - "FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md"
  - "Anthropic Usage Policy non-compete carve-out (verified in research report)"
upgrade_path: "Claude Code amends via PR; bump minor per WS completed"
rollback_plan: "git revert; all outputs are additive files"
license: "Compassion Clause + Apache-2.0/GPL-compatible"
friction_tier: "low"        # docs + eval data; no runtime/identity changes
suggested_repo_path: "FLOSS/docs/superpowers/plans/2026-07-03-fable5-sprint-handoff.md"
```

## 0. Provenance Packet

```yaml
timestamp: "2026-07-03T00:00:00Z"
author_agent: "Claude Fable 5 (claude.ai, adversarial/verification layer)"
human_collision_node: "Anthony (kalisam)"
source_systems: ["claude.ai project session", "extended research task", "web_search (Pioneer/Fastino verification)"]
claim_type: ["proposal"]
payload:
  summary: >
    Fable 5 subscription access ends in ~6 days (from 2026-07-03), then moves to
    pay-per-credit. Strategy: front-load COMPILE-TIME uses (durable artifacts:
    evals, prompts, specs, reviews) into the window; convert Fable 5 to a
    credit-metered ESCALATION target afterward. Five workstreams below, each a
    bounded artifact with success criterion and rollback.
  evidence:
    - "Research report finding: harness-level improvement is high-ROI and ToS-clean; distilling frontier outputs into competing general models is prohibited"
    - "Verified: Pioneer (Fastino Labs, launched 2026-04) fine-tunes open SLMs (Qwen/Gemma/Llama/GLiNER); adaptive inference retrains on live traffic; Pro tier allows weight download"
    - "Anthropic carve-out: narrow non-competing models (classifiers, extractors, categorizers) explicitly permitted"
  risks:
    - "-1: feeding Claude-origin outputs into Pioneer's general fine-tuning or adaptive-inference loop (ToS violation path)"
    - "-1: burning the window on infra buildout instead of artifact extraction"
    - "-1: doc-explosion — this sprint could spawn 20 docs; caps below prevent it"
  benefits:
    - "+1: Fable-5-quality evals/rubrics/prompts persist forever on cheap models"
    - "+1: KnowledgeTriple extractor seed feeds Phase 1 directly"
next_action: "Claude Code: execute WS0, report findings, then proceed WS1→WS5 in order"
```

## 1. Ground Rules (pointers, not duplication)

1. **Orient first.** Follow `flossi0ullk-orient` skill: run `python FLOSS/scripts/orient_probe.py --query "fable5 sprint <WS>"` before reading anything. Respect token tiers.
2. **Kernel governs.** `FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` — evidence gate, claim truth model, ternary decisions, precedence (Section 11).
3. **Source authority:** repo branch > CURRENT_STATE > repo docs > project uploads > conversation > memory. **This packet is conversation-tier.** Where WS0 findings contradict this packet, the repo wins — flag, don't blend.
4. **Compose, don't greenfield.** Before creating any file, check INDEX.md / context router for an existing home. Several subsystems have silent predecessors.
5. **Doc budget (hard cap):** ≤ 6 new markdown docs across the entire sprint. Eval/seed *data* files (JSONL etc.) are exempt but must each live under a single directory. Exceeding the cap = stop and ask.
6. **Every artifact** gets an UpgradableArtifact header with `truth_status` and provenance (`generator: claude-fable-5`, date, hash into agentmemory if the bus is reachable).

## 2. Window Economics (why this order)

Subscription access = flat-rate but **rate-capped**; assume the window can be exhausted early. Execute workstreams in priority order, not in parallel. WS0 gates everything. WS1 gates WS2/WS3 (they need the eval sets as fitness/acceptance targets). WS4/WS5 can interleave if quota allows.

Post-window policy (formalized in WS5): Fable 5 is invoked **only** on escalation criteria; the next-best retained model inherits the adversarial/verification role by default.

---

## WS0 — Orient + Repo-State Verification  `[NOW — gate]`

**Pain:** conversation/memory state is stale; known unresolved contradictions.
**Do:**
- Run orient probe; read CONTEXT_L0 / INDEX.md / FLOSS/CLAUDE.md per skill tiers.
- Verify against live repo (`kalisam/FLOSS`, `kalisam/Amazon_Rose_Forest_01`):
  - PR #25 state (open/merged/conflicted) and contents (ADR-5, ADR-6, consensus-gate work).
  - Phase 0 claim: does Rose Forest DNA actually compile to WASM with Tryorama tests passing on the current default branch? (Memory says yes via PR #21; verify, don't trust.)
  - Consensus gateway test status (claimed 32/32).
  - ADR numbering conflict between Kernel references and `FLOSS/docs/adr/` — enumerate the actual conflict.
  - Current Holochain version pin (claimed 0.6.1 baseline).
**Output:** update or create `CURRENT_STATE` entry (existing file per source-authority chain — find it; do not create a parallel one). One doc max, and it should be an update, not new.
**Success criterion:** every claim above marked Verified/Refuted with commit/file evidence.
**Rollback:** git revert.
**Stop condition:** if Phase 0 claim is refuted, report before proceeding — WS1 module choices depend on it.

## WS1 — Eval Golden Sets + Rubrics  `[NOW]`

**Pain:** no versioned fitness function; every downstream optimization (prompt sweep, Pioneer, consensus jury, regression detection) lacks a target.
**Do:**
- Pick 2–3 highest-value modules (candidates pending WS0: KnowledgeTriple extraction, consensus-gate claim verification, provenance-packet validation). Confirm choice with Anthony if WS0 changes the picture.
- Author per module: 20–50 eval items (input, golden output, rationale), a grading rubric a *weaker* model can apply, and a held-out split (never shown to any optimizer, including Pioneer).
- Each item provenance-tagged: `generator: claude-fable-5`, date, source (synthetic vs derived-from-repo).
**Output:** one directory (e.g., `FLOSS/evals/<module>/` — confirm location against INDEX.md first), JSONL data + 1 README doc covering all modules.
**Success criterion:** a retained model (not Fable 5) can apply each rubric to a sample and agree with golden labels ≥80%; below that, rubric is ambiguous — revise.
**Rollback:** delete directory.

## WS2 — Meta-Prompting Sweep  `[NOW]`

**Pain:** per-model system prompts (LiteLLM roster, OpenClaw daemon, Perplexity Space v2.0, consensus voter prompts) were hand-written; weakest modules underperform.
**Do:**
- Collect current prompts + 3–5 real failure examples per module (Anthony supplies or WS0 finds in logs).
- Fable 5 rewrites each: tightened role, explicit output contracts, failure-mode guards. Weakest module first.
- Score before/after on WS1 dev split (never the held-out split).
**Output:** revised prompt files in their existing config locations + 1 delta doc (before/after scores, what changed, why).
**Success criterion:** measurable improvement on ≥1 module's dev split, or a documented finding that prompts weren't the bottleneck (that's a valid result — it redirects credit spend later).
**Rollback:** prior prompts preserved in git history; revert per module.
**Deliberately excluded:** DSPy/GEPA pipeline buildout. Infra can be built post-window with cheap models; only Fable-5-as-proposer runs need the window, and manual meta-prompting captures most of the value now. GEPA on the single weakest module = `[LATER]`, bounded credit spend, logged in WS5 policy.

## WS3 — KnowledgeTriple Extraction Seed for Pioneer  `[NOW]`

**Pain:** Phase 1 primary deliverable needs an extractor; frontier-model extraction per-call is slow/costly; Pioneer subscription is idle capacity.
**Do:**
- Conform to the existing spec (`knowledge-triple_spec.md` — locate the repo-canonical version first; the project-upload copy is upload-tier authority). Extend only via PR if the spec is insufficient — do not fork it.
- Fable 5 authors: annotation guidelines (1 doc), 50 golden extraction examples now (target 150–300 total; remainder can be generated post-window by retained models *following* the guidelines), eval split (reuse WS1 module if same), and the Pioneer task prompt.
**ToS constraints (hard):**
- Target = narrow extractor (GLiNER2/Qwen class). This is inside Anthropic's explicit non-competing carve-out (classifiers/extraction). **Verified in research report against Anthropic's published terms.**
- Do NOT include general collective conversation logs in any Pioneer training set.
- Do NOT enable Pioneer's adaptive-inference loop until Fastino confirms training-data filtering/exclusion by provenance tag — Claude-origin outputs flowing through live traffic into silent retraining is the prohibited path. `[0 — hold pending verification]`
- Prefer Apache-2.0 base (Qwen) for weight sovereignty; requires Pioneer Pro tier for weight download (**tier unconfirmed — ask Anthony**).
**Output:** 1 guidelines doc + seed JSONL under the WS1 eval directory structure.
**Success criterion:** Pioneer fine-tune achieves ≥ parity with the best retained API model on the held-out split at materially lower latency/cost; else document gap and hold.
**Rollback:** don't deploy the fine-tune; artifacts remain useful as evals.

## WS4 — Adversarial Review Sweep  `[NOW]`

**Pain:** load-bearing artifacts have never had a full frontier-model adversarial pass; post-window this costs credits.
**Do:** Fable 5 reviews, in one consolidated document: Kernel v1.3.1, Project Spine v0.5, SDD v0.22, consensus gateway design + ADR-10 v2.0, Holochain 0.6.1 migration mapping, PR #25 diff, and the WS0 contradiction findings. Per item: concrete defect or risk, severity, smallest fix, ternary recommendation.
**Output:** exactly 1 doc: `2026-07-fable5-adversarial-review.md` (suggested home: same plans/ directory as this packet).
**Success criterion:** ≥ 5 actionable findings with smallest-fix proposals; zero new architecture proposed (findings may *recommend* ADRs, not write them).
**Rollback:** it's a review doc; git revert.

## WS5 — Successor Handoff + Credit Escalation Policy  `[NOW]`

**Pain:** day 7 arrives regardless; without an explicit policy, either quality silently degrades or credits burn on routine calls.
**Do:** Fable 5 authors:
- Verifier prompts tuned for the next-best retained model to inherit the adversarial/verification role in the consensus gateway (voter roster change is config, not architecture).
- Escalation criteria: what earns a Fable 5 credit spend (e.g., consensus deadlock at |vote| < threshold, security-sensitive diff, ADR-tier decision, WS1 regression > X%), with per-week credit budget placeholder for Anthony to set.
**Output:** 1 doc + gateway voter-config stub (config change only).
**Success criterion:** gateway runs one full consensus round post-window with successor verifier and zero Fable 5 calls; escalation fires only on defined triggers.
**Rollback:** revert voter config to current roster.

---

## Stop Conditions (return to Anthony, Decision = 0)

- WS0 refutes a load-bearing claim (Phase 0, PR #25, gateway tests).
- Any WS wants to exceed the 6-doc budget or create a new subsystem.
- Any WS requires an ADR-tier change to shared invariants (propose, don't implement — kernel §11, orient skill rules).
- Pioneer data path can't be provenance-filtered (WS3 hold stands).
- Quota exhaustion mid-WS: commit partial artifacts with `truth_status: Specified` and a TODO block; partial evals > no evals.

## Definition of Done (sprint)

- [ ] WS0 verification block committed; contradictions enumerated
- [ ] ≥ 2 modules with golden sets + rubrics + held-out splits
- [ ] ≥ 1 module with measured prompt improvement (or documented null result)
- [ ] KnowledgeTriple guidelines + ≥ 50 provenance-tagged seed examples
- [ ] 1 consolidated adversarial review
- [ ] Successor config + escalation policy committed; one gateway round validated
- [ ] Doc count ≤ 6; every artifact headered + provenance-tagged
- [ ] Orient-skill self-audit answered at each WS close

*Simplicity now. Seams for later. Delete the rest.*
