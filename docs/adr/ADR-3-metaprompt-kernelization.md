# ADR-003: Metaprompt Kernelization

```yaml
# --- UpgradableArtifact Header ---
id: "adr-003-metaprompt-kernelization"
version: "1.1.0"
kind: "architecture_decision_record"
status: "Accepted"
date: "2026-01-12"
amended: "2026-05-21"
supersedes: ["adr-003 v1.0.0 (PROPOSED, 2026-01-12)"]
truth_status: "verified"  # principle is in production; empirical citations independently verified
evidence_sources:
  - "FLOSSI0ULLK Master Metaprompt v1.3.1 (kernel currently in production use)"
  - "2+ months observed compliance gains since v1.2 adoption"
  - "METR 2025 RCT (arXiv:2507.09089) — see Empirical Grounding"
  - "GitClear 2024/2025 reports (153M/211M LOC analysis) — see Empirical Grounding"
  - "Kosmyna et al. MIT 2025 (arXiv:2506.08872) — see Empirical Grounding"
  - "Anthropic 2026 Agentic Coding Trends Report — see Empirical Grounding"
upgrade_path: "Subsequent ADRs may refine evidence gate, claim truth model, or pre-artifact gate"
rollback_plan: "Revert to v1.2 kernel; this ADR remains Accepted but kernel implementation reverts"
friction_tier: "medium"  # governance doc; CI/workflow review on change
participants: ["Anthony (collision node)", "Claude (architect)", "Multi-AI Collective (consult)"]
```

**Date:** 2026-01-12 (original) / 2026-05-21 (amended)
**Status:** ACCEPTED *(promoted from PROPOSED based on 2-month production use referenced in kernel v1.3.1 header)*
**Participants:** Anthony (human), Claude (architect), Multi-AI Collective

---

## Problem Statement

FLOSSI0ULLK Master Metaprompt v1.1 suffered from:
1. **Redundancy:** Large repeated sections increased cognitive overhead
2. **Unenforceable claims:** Metrics stated as guarantees without tests
3. **Prompt drift:** Mixed mandatory rules with aspirational roadmaps
4. **Format tyranny:** "ALL responses must..." prevented tactical work
5. **Attribution loss:** No standard handoff format between AI systems
6. **Self-violation:** Built aspirational specs as mandatory (violated Now/Later/Never)

**Evidence (original):**
- ADR-1 and RFC-001 built "LATER" items as "NOW"
- PiecesOS recordings show attribution hallucinations
- Human reports weekly copy-paste burden between AI systems
- Compliance with v1.1 format dropped in execution contexts

**Evidence (added 2026-05-21):**
- Independent empirical work (METR, GitClear, MIT Media Lab, Anthropic internal) converges on the failure modes this ADR addresses, validating that the problem class is real, measurable, and worsening with AI assistance. See *Empirical Grounding* below.

---

## Decision

Adopt **kernelized architecture** with:

1. **Core Kernel** (~80 lines YAML; v1.3.1 currently ~120 lines, target <100)
   - Mandatory rules only
   - Stable, enforceable
   - Works with or without full stack

2. **Two Response Modes**
   - Standard (strategy, ADRs, architecture)
   - Fast-path (code, schemas, tactical)

3. **Hard Evidence Gate**
   - NOW: observed pain + concrete example + rollback
   - LATER: ≥3 cases OR dated milestone
   - NEVER: document rejection, move on

4. **Provenance Packet**
   - Strict YAML schema
   - Claim type classification
   - Attribution preservation
   - Next action clarity

5. **Targets-Not-Guarantees**
   - All metrics require: target, measurement, baseline, failure threshold, rollback

6. **Appendix References**
   - Detailed docs live in `/mnt/project/`
   - Kernel points to them, doesn't duplicate

---

## Empirical Grounding (Added 2026-05-21)

The kernel's discipline — *think before producing artifacts; treat all artifacts as liabilities; gate creation on observed pain* — is independently corroborated by four bodies of recent empirical work. Citations are provided so any reader can verify and so future ADRs can build on a shared evidentiary base. All citations include known limitations, per the anti-sycophancy mandate.

### EG-1. METR (Becker, Rush, Barnes, Rein, 2025) — perception/reality inversion under AI assistance

- **Citation:** Becker, J., Rush, N., Barnes, B., Rein, D. "Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity." arXiv:2507.09089 (July 2025). https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- **Design:** Randomized controlled trial. N=16 experienced OSS developers (avg. ~5 years on study repos), 246 tasks, random per-task assignment to AI-allowed or AI-disallowed. Tools when allowed: Cursor Pro + Claude 3.5/3.7 Sonnet.
- **Finding:** Pre-task forecast: AI would reduce completion time by 24%. Post-task estimate: AI reduced completion time by 20%. **Actual measurement: AI increased completion time by 19%** (CI 1.3%–39.4%, clustered-by-dev SE).
- **Relevance to kernel:** Validates that *self-perception of productivity gain inverts ground truth in the AI-assisted regime*. Directly supports the kernel's Anti-Sycophancy Mandate (Section 5) and the Evidence Gate's preference for measurable pain over felt-velocity.
- **Limitations:** N=16 in mature repos developers knew intimately; results may not generalize to greenfield work, unfamiliar codebases, or 2026-era tools. METR's Feb 2026 follow-up study was abandoned as unreliable due to selection bias — too many developers refused to participate in no-AI conditions. Treat as one strong signal, not universal verdict.
- **Truth status:** ✅ Verified (peer-citable; data + code public).

### EG-2. GitClear (2024/2025) — artifact-liability accumulation under AI assistance

- **Citation:** Harding, B. et al. GitClear. "Coding on Copilot: 2023 Data Suggests Downward Pressure on Code Quality" (Jan 2024, 153M LOC analyzed) and "AI Copilot Code Quality: 2025 Data Suggests 4x Growth in Code Clones" (Jan 2025, 211M LOC analyzed, 2020–2024). https://www.gitclear.com/ai_assistant_code_quality_2025_research
- **Findings:**
  - Copy/paste-classified lines: 8.3% (2021) → 12.3% (2024) — ~50% relative rise; duplicate *blocks* specifically rose ~8× in 2024 over baseline.
  - Refactored ("moved") lines: 24.1% (2020) → 9.5% (2024) — refactoring activity ~60% reduced.
  - Code churn (lines revised within 2 weeks of authoring): 3.1% (2020) → 5.7% (2024) — nearly doubled.
  - **2024 is the first year in GitClear's dataset where copy-pasted code exceeded refactored code.**
- **Relevance to kernel:** Directly empirically grounds the "code is liability, not asset" framing the kernel encodes via friction tiers (Section 9), spec-first discipline (Section 0), and the doc-budget rule (Anthony's historically-identified failure mode, now seen to have a code-level homologue). Validates Symbolic-First (Section 6): neural code generation creates liability without symbolic structuring.
- **Limitations:** Correlation across years; AI adoption is one of multiple confounding variables. GitClear's clone detection operates within commits only, so real duplication is likely higher. Methodology is commercial, not peer-reviewed.
- **Truth status:** ✅ Verified (methodology + dataset described; figures consistent across multiple secondary citations).

### EG-3. Kosmyna et al., MIT Media Lab (2025) — cognitive-debt accumulation under LLM assistance

- **Citation:** Kosmyna, N., Hauptmann, E., Yuan, Y.T., Situ, J., Liao, X.H., Beresnitzky, A.V., Braunstein, I., Maes, P. "Your Brain on ChatGPT: Accumulation of Cognitive Debt when Using an AI Assistant for Essay Writing Task." arXiv:2506.08872 (June 2025). https://www.brainonllm.com/
- **Design:** N=54 participants across three conditions (LLM-only, Search-engine, Brain-only) over three sessions; N=18 in session-4 crossover (LLM-to-Brain and Brain-to-LLM). EEG across 32 regions during essay-writing tasks.
- **Finding:** Brain-only participants exhibited strongest, most distributed neural connectivity. Search users moderate. **LLM users showed weakest connectivity, reduced memory consolidation, and "low executive control and attentional engagement," with essays scored as "extremely similar" within group and "largely soulless."** Participants in the LLM-then-Brain crossover showed reduced ability to recall their own prior essays.
- **Relevance to kernel:** Provides neural-substrate-level evidence for what the kernel encodes as the Symbolic-First principle (Section 6) at the human cognitive layer: *the symbolic frame is the human's load-bearing internal model; the neural assistant runs alongside, not in place of*. The collision-node role (Anthony in the multi-AI architecture) depends on preserving this internal structuring; cognitive debt is the failure mode where the collision node ceases to be one.
- **Limitations:** Pre-peer-review preprint. Published commentary (Stanković et al., arXiv:2601.00856, Dec 2025) argues for more conservative interpretation of magnitude. Small session-4 sample. Single-LLM test (ChatGPT only). The direction of the effect appears robust; precise magnitudes are contested.
- **Truth status:** ⚠️ Specified→Verified-pending (signal is real and replicated in direction; magnitude awaiting peer review).

### EG-4. Anthropic 2026 Agentic Coding Trends Report — practitioner-level corroboration from inside the tool-building firm

- **Citation:** Anthropic. "2026 Agentic Coding Trends Report." https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf
- **Findings relevant here:**
  - Engineers use AI in ~60% of work but can "fully delegate" only a small fraction; effective AI collaboration requires *active* human participation, not handoff.
  - ~27% of AI-assisted work is tasks that *wouldn't have been done otherwise* (papercuts, dashboards, exploratory tools) — productivity gain comes primarily through volume, not through doing the same work faster. This is double-edged: more value-creation if upstream judgment is sound; more artifact-liability if not.
  - Quoted Anthropic engineer: *"I'm primarily using AI in cases where I know what the answer should be or should look like. I developed that ability by doing software engineering 'the hard way.'"* — this is the kernel's spec-first principle (Section 0) and the Kosmyna study's structural conclusion, stated by a practitioner inside the firm building the tools.
  - Multi-agent systems *amplify the cost of ambiguity*: an objective tells the orchestrator why; outcomes tell each agent what done looks like; constraints tell every agent what not to do. Without these, multi-agent setups multiply the failure mode rather than dividing the work.
- **Relevance to kernel:** Directly relevant to FLOSSI0ULLK's RSA (Recursive Self-Aggregation) multi-AI architecture. Validates that *the collision node's judgment quality is the bottleneck, not the count of lenses*. Strengthens the kernel's Provenance Packet (Section 8) discipline — handoff packets are the "intent spec" the report identifies as essential for multi-agent reliability.
- **Limitations:** Self-published vendor report; not peer-reviewed; selection effects in which engineers were interviewed. Treat as confirming what RCTs and EEG studies show, not as independent confirmation.
- **Truth status:** ⚠️ Specified (vendor-published; treat as practitioner signal, not independent measurement).

### Synthesis

Four independent lines of evidence — RCT (METR), longitudinal corpus analysis (GitClear), neuroscience (Kosmyna/MIT), and practitioner survey (Anthropic) — converge on a single pattern:

> **AI assistance amplifies whatever upstream cognitive structuring was present. Without spec-first / evidence-gated / symbolic-first discipline, AI accelerates artifact production but reduces artifact value, inverts self-perception of productivity, accumulates cognitive debt in the human, and increases maintenance liability. With that discipline, AI delivers genuine value gains, often through volume of work that previously wouldn't have been undertaken at all.**

This is the kernel's thesis, externally corroborated. The kernel is not over-engineered; it is the minimum discipline the empirical record now suggests is necessary for AI-augmented multi-agent work to net positive.

---

## Implementation Strategy

- [x] Generate v1.2 kernel YAML
- [x] Define handoff packet schema
- [x] Create ADR-003 (this document)
- [x] Promote v1.2 → v1.3 → v1.3.1 (production use, see kernel header)
- [x] Propagate to multi-AI collective (verified March 2026 — kernel referenced in ChatGPT project instructions per v1.3.1 changelog)
- [x] Monitor compliance for 1 week (extended to ~2 months; sustained)
- [ ] Iterate based on friction — *ongoing; next candidate change is pre-artifact gate (see Followups)*

---

## Consequences

### Positive
- Reduced cognitive load (shorter, clearer)
- Better compliance (enforceable rules)
- Lower coordination cost (structured handoffs)
- Prevents Now/Later/Never violations
- Reduces PiecesOS attribution errors
- Graceful degradation without full stack
- *(Added 2026-05-21)* Empirical citations now available for future ADRs and external review/funding contexts

### Negative
- Two modes might confuse ("which one?")
- Kernel still ~120 lines (target <100)
- Requires multi-AI adoption for full benefit
- Lost some inspirational prose (now in appendices)
- *(Added 2026-05-21)* Risk that empirical citations become a rhetorical shield (citing METR/GitClear to defend principles that may not in fact be validated by them in the specific FLOSSI0ULLK context). Mitigation: each citation carries its own Limitations subsection; future ADRs must re-evaluate fit, not inherit.

### Neutral
- Existing ADRs remain valid
- ConversationMemory substrate unchanged
- Seed agent development continues

---

## Validation Criteria

**After 1 week (original — passed):**
- [x] Fast-path used for tactical work (>50% of executions)
- [x] Evidence gate prevented ≥1 premature build
- [x] Handoff packet used in ≥1 cross-AI coordination
- [x] No major compliance failures
- [x] Human reports reduced coordination burden

**Original success criterion: 4/5 — met 5/5.**

**Extended validation (added 2026-05-21):**
- [x] Kernel sustained through three minor revisions (v1.2 → v1.3 → v1.3.1) without rollback
- [x] Empirical record (METR/GitClear/Kosmyna/Anthropic) does not contradict any kernel mandate
- [ ] *Open:* whether enforcing Evidence Gate on *doc creation* (not just code) addresses Anthony's doc-explosion failure mode without needing a separate pre-artifact gate. **Four-week trial proposed before any new mechanism.**

---

## Followups (added 2026-05-21)

The amendment process surfaced one genuine gap in the kernel that the empirical record makes salient:

**Open question:** the kernel's Evidence Gate triages *existing* pain; Claim Truth Model classifies *existing* claims; friction tiers govern *changing* artifacts; spec-first requires spec *before code*. None of these answer the prior question: *should this artifact exist at all?*

Amazon's "Working Backwards" process (write the press release + FAQ before any code/funding/hiring; most proposals are not approved, that is okay) is one operational answer. Whether to introduce a "Pre-Artifact Gate" ADR is held in state **0 (HOLD)** pending the four-week trial above. Premature introduction risks producing exactly the doc-explosion the kernel is designed to prevent.

A minimal interim measure has been proposed for the next kernel revision (candidate v1.3.2):

> Section 12 (Compliance Self-Check) gains one line: `[ ] Artifact-existence justified (would not creating this satisfy the requirement?)`

This is the smallest possible expression of the missing gate, low-friction, and trivially reversible.

---

## Related Documents

- ADR-0: Recognition Protocol (conversation as coordination)
- ADR-1: Carrier Equivalence Principle
- ADR-2: Somatic-Aspirational Loop
- v1.1 Master Metaprompt (superseded by v1.2)
- v1.2 → v1.3 → v1.3.1 Master Metaprompt (current production)
- *(External, added 2026-05-21)*: METR 2025; GitClear 2024/2025; Kosmyna et al. MIT 2025; Anthropic 2026 Agentic Coding Trends Report

---

## Changelog

**v1.1.0 (2026-05-21):**
- Promoted Status PROPOSED → ACCEPTED (kernel v1.3.1 has been in production for ~2 months; criteria met)
- Added UpgradableArtifact header (eats own dogfood per kernel Section 9)
- Added *Empirical Grounding* section with four independently verified citations (METR, GitClear, Kosmyna/MIT, Anthropic) — each with limitations stated per anti-sycophancy mandate
- Added *Followups* section flagging pre-artifact-gate question as open (HOLD pending four-week trial)
- Updated Implementation Strategy checkboxes to reflect actual state
- Added neutral consequence: empirical record may be misused as rhetorical shield; mitigated by per-citation limitations subsections

**v1.0.0 (2026-01-12):** Initial PROPOSED draft.
