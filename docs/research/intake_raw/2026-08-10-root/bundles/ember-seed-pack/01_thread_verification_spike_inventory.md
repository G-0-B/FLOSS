# Thread packet: OVCA verification → ObjectGraph spike → metaharness inventory → spec-gate

```yaml
id: "ccp-websession-2026-06-09-verification-spike-inventory"
version: "1.0.0"
kind: "context_continuation_packet"
status: "Accepted"
updated: "2026-06-09"
origin: "claude.ai web session, 2026-06-09 (no repo access; scripts seen via upload only)"
thread_arc: "Perplexity OVCA report audit → primary-source verification → ObjectGraph
  spike (paused) → co-evolution cluster verification → 20-script metaharness inventory →
  spec-gate ('-1 layer') design discussion"
truth_status: "Decision log Verified (origin session); repo-structure claims [VERIFY]"
```

## 1. Decision log (ternary + truth status)

| # | Decision | State | Status | Notes |
|---|---|---|---|---|
| D1 | OVCA (Perplexity report's 5-layer artifact stack) as integration target | **−1 reject** | V | Aspirational by its own Gap 1; maximalist vs doc-discipline; media-provenance (C2PA/watermark) category-stretched onto text/knowledge; Part VII = self-validation loop |
| D2 | Mine 3 primitives concept-not-import: ObjectGraph traversal/progressive-disclosure; MAIF Cryptographic Semantic Binding (hash-commit embedding↔source, blocks semantic injection); SCP attribution-by-default envelope → re-expressed as capability tokens | **+1 cond.** | V | Each re-implemented Holochain-native; none imported as-is |
| D3 | Report's citation spine verified at primaries — see §2 | done | V | Key: most refs REAL; failure mode is framing, not fabrication |
| D4 | Co-evolution cluster verified — see §3 | done | V | Confirms SRP v2 spine; names report Part VII as the anti-pattern |
| D5 | ObjectGraph spike (one-pager, .og node model as typed projection over DHT) | **0 hold/paused** | S | Delivered in-session; PAUSED pending script-layer re-inventory (D6). Resume gated on N1–N3 below |
| D6 | Metaharness script layer: 0/hold on ALL new infra; +1 one consolidation pass (inventory → existing canon; merge review-queue redundancy) | **+1** | V(code) | 13 of 20 scripts read directly from uploads; 7 inferred — see §4 |
| D7 | Spec-gate ("-1 layer"): model it as a distributed validation rule (fail-closed check at artifact creation), NOT a resonance channel and NOT central routing; Holochain validation is the precedent that dissolves the P5 tension | proposed | S | Smallest version: "no new script/doc without a one-line spec stub in its registry, or --check fails"; wire into existing materializer --check + post-write hook |

**Origin's own logged corrections (carry these; they bound trust in origin):**
(a) claimed ObjectGraph report "invented a 60–95% floor" — WRONG, the paper itself uses
60–95% (abstract best-case 95.3%, RQ1 mean 92.0%); (b) claimed `context_router.py` ≈
ObjectGraph `search_index` — overclaim: router is corpus-granular deterministic
keyword-scorer, not node-granular LLM-router; (c) assumed CONTEXT_L0/L1 hand-maintained —
they are generated projections.

## 2. Primary-source verification results (OVCA report spine)

| Source | Verdict | Load-bearing detail |
|---|---|---|
| MAIF arXiv 2511.15097 (Narajala et al., OWASP/Cisco/SAP) | Real; abstract walked back by own tables | Table III: 64.21× avg / 480× best = **plain Brotli**, not novel algos; "225×" in prose only; HSC (the semantic compressor) = Phase 2, TRL 4–6, **not built** (Table VI); 2,720 MB/s = mmap on i9-13900K, hardware property. Self-run, unreproduced |
| ObjectGraph arXiv 2604.27820 (Dubey + "Open Gigantic" — pseudonym) | Real; eval better than provenance | 240 docs, 8 task types, 5 runs w/ 95% CI, 3 models, 3 baselines, ablation, 18-person authoring study. Mean 92.0% token reduction; accuracy 90.1 vs MD 76.0, wins 7/8. **One loss: cross-node reasoning 77.9 vs 82.1** (synthesis-heavy work = our exposure). No code/data released; v1; zero citations. Six properties P1–P6 are NOT cryptographic — report fused its own desiderata onto the theorem. Paper's stated open problem (cross-file federation, "distributed knowledge graph… agentic web") **is FLOSSI0ULLK's premise** |
| SCP-Sovereign arXiv 2603.27094 | Real; most honest of batch | 6 methods, license envelope, 5-class threat model, log-proportional revenue model; explicitly "preliminary." BUT centralized: API-key auth, server-issued licenses — same mismatch as Atomic Server HOLD. Concepts yes, mechanism no |
| π-tuple arXiv 2605.21002 | Real, misframed | Courtroom/military-law evidence-admissibility paper transplanted into a data-structure spec |
| d3cipher / "LockStock" (report ref ^16) | **NOT FOUND anywhere** | Cited from a Reddit cofounder-recruitment post; laundered into Layer 3 as an established primitive. DROP. Real adjacent literature: zkVM agent identity 2512.17538, 2505.19301 |
| NOVA arXiv 2605.15219 (Avestimehr/Duffy/Médard) | Real; strongest paper in either batch | See §3 — report cherry-picked its pro-human line and omitted the contamination trap |

## 3. Co-evolution cluster verdict (the report's METHODOLOGY layer)

- **NOVA**: information-theoretic analysis of generate-verify-accumulate-retrain.
  **Contamination trap**: under imperfect verification, as easy/genuine knowledge is
  exhausted, even small false-positive rates let invalid artifacts enter the knowledge base
  FASTER than real discoveries. Failure taxonomy: contamination / forgetting / exploration
  failure / acceptance failure. Report cited only "human guidance expands the reachable set."
- **CoEvoSkills 2604.01687** (renamed from EvoSkills; Philip S. Yu group): surrogate
  verifier = separate LLM session; headline numbers (71.1%, +36–44pp transfer) measured
  vs **ground-truth oracle**. Legitimate ONLY because skills are executable. Pattern usable
  for FLOSS **code path** (DHT validation + CI = the oracle).
- **Multi-Agent Evolve 2510.23595**: Proposer/Solver/Judge from ONE model, self-rewarding,
  no external ground truth — IS the self-validation loop; modest +4.54% on a 3B model.
- **Synthesis**: report Part VII ("Surrogate Verifier accepts deltas," LLM-judge quality
  gate) = the anti-pattern SRP v2 exists to prevent. Knowledge/ontology artifacts need
  human or genuinely independent (not same-distribution) grounding. Independent
  corroboration: arXiv 2605.02010 (Knowledge Objects position paper).
- **Verified-from-code affirmation**: `autonomous_synthesis_loop.py` already implements the
  NOVA-correct pattern (LLM proposes → human-gated staging → chain commit; docstring names
  hallucination-pollution as the rationale). This was checked against the actual code.

## 4. Metaharness inventory (20 scripts; [read] = seen in full, [inf] = inferred)

A **Materializers** (canonical JSON → registry + index + per-client projections; shared
template w/ --check/--dry-run drift detection): skill[read], hook[read], context[inf],
agent[inf], ai_roster[inf], agent_memory[inf]
B **Intake**: watch_intake[read] (polls roots → IntakeEvents), process_intake_events[read]
(classify → queue summary). Self-described walking skeleton.
C **Consensus gateway** (advisory, never auto-escalates): hook_post_write[read]
(packages/**/*.{py,rs,toml} edits → Claim + provenance packet + detached bg round),
poll_high_roi_actions[read] (slate → voter roster → chain; profiles balanced/diverse/
diverse-max; consumes heartbeat next_slate.json)
D **Heartbeat**: heartbeat[inf], heartbeat_slate[inf]
E **Synthesis/harvest** (human-gated): autonomous_synthesis_loop[read],
harvest_reuse_ledger[inf] + harvest_batch.sh[read] (anti-accumulation guard REMOVED
intentionally per Anthony 2026-05-17)
F **Review roll-ups**: review_queue[read] + triage_review_queue[read] — **REDUNDANT PAIR,
merge candidate**
G **Provenance audit**: audit_provenance_packets[read] (valid/superseded/invalid)
H **Session bootstrap**: session_start_inject[read] (STARTUP_CONTRACT.md @ SessionStart)

**Named risks** (from code, not vibes): (i) default poll profile `balanced` + 8–32B voters
→ possibly correlated same-distribution consensus = NOVA's warned bias; safe today only
because nothing auto-promotes on tally_mean; (ii) review-queue pressure is unbounded by
design while orientation/spec docs lag — cognitive-debt pool; (iii) sprawl itself =
Anthony's #1 named failure mode at the script layer. Anthony's own framing of root cause:
not memory capacity — **artifacts were built before being spec'd/committed as deliberate
artifacts**; spec-driven development intended but the -1 layer (plan/research/spec before
build) is not yet enforced.

## 5. Next-action queue for the local instance (in order)

| N | Action | Why first | Self-answerable? |
|---|---|---|---|
| N1 | Fold script inventory (§4) into existing canon — CONTEXT_L0.md or INDEX.md, NOT a new file | converts this packet's main payload into durable orientation; one layer absorbs | needs canon read; consent to edit granted in principle 2026-06-09 ("green for everything") — confirm scope at point of edit |
| N2 | Read `materialize_shared_context_surface.py` → close ObjectGraph-spike Step 1 (what L0/L1 emission actually looks like) | the single spike-critical unread file | yes |
| N3 | Read `materialize_shared_ai_roster.py` + voters module → is default roster actually provider-diverse? If not: flip default to `diverse` or document why not | closes risk (i) | yes |
| N4 | Merge review_queue/triage_review_queue (or document why both) | closes the one concrete redundancy | yes, small |
| N5 | Decide spec-gate D7: adopt registry spec-stub fail-closed check? where wired (materializer --check vs post-write hook vs both)? | the structural fix for the root cause in §4 | needs Anthony |
| N6 | Resume ObjectGraph spike build (gated on N1–N3): pilot ONE corpus (skill-corpus), typed nodes + node-level ::index, read-only resolve_context as DHT projection; probe the 2 known risks FIRST (cross-node synthesis regression; adversarial routing → NormKernel/validation gate) | highest-value new capability, but only after inventory lands | needs Anthony go |

## 6. Open questions (re-ask; accept piecemeal answers)

1. N5 spec-gate adoption + wiring point (Anthony)
2. N6 spike resume go/no-go after N1–N3 (Anthony)
3. From TAME thread (see file 02): are P1–P5 goal-scope or structural-resonance properties? Is the paper's second half (evolution/consciousness) needed pre-integration? (Anthony)
4. Orient-packet decisions #9/#10 (pytest suite; CI canary) still unanswered — re-ask (Anthony)
5. SRP v2 T2 blocker: seven-country citation — replace with verified Savolainen/Schimmelpfennig/Folk triangulation? (Anthony; from 2026-05-14 thread)
