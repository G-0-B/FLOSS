
# Universal Operating Procedure (UOP) — External Reality Scout / FLOSSI0ULLK v2.1
*Distilled from the multi-session process audit of G-0-B/FLOSS[cite:22][cite:27][cite:30][cite:31], reconciling the designed 0–8 gate loop with observed execution gaps and the cross-verification failures both parties made (scope-blind search, branch divergence, unfounded past-tense claims).*

## 0. Prime Rule

**No claim, no artifact, no action survives compaction unless it is written to a file that outlives the context window.** Every other rule below exists to enforce this one. A plan in prose is not a plan. A "done" without a citable line is not done.

---

## 1. The Nine-Gate Loop (canonical, enforced)

| # | Gate | Enforcement mechanism (not just intent) |
|---|------|------------------------------------------|
| 0 | ORIENT | probe → CONTEXT_L0 → router; must name default frame (e.g. Western-technical) before proceeding |
| 1 | RECALL | agentmemory + session_search run **before** any plan is drafted — blocked if skipped |
| 2 | REUSE GATE | ADR-18 adopt→extend→compose→build; check Risk Register; must produce a Y/N adopt-vs-build line |
| 3 | PLAN | Written to a durable path (`.hermes/plans/` or repo `docs/superpowers/plans/`) *before* any Execute step — refusal rule: no Execute without a plan-file path in the ledger |
| 4 | CLASSIFY | Blast radius (Local/Module/System) stated explicitly with evidence; misclassification is expected to be caught by Gate 5, not silently corrected later |
| 5 | CONSENSUS | Runs **before** System/Substrate changes, never after — evidence packet must include (a) the plan file, (b) recon data, (c) **push/branch-divergence state** so voters aren't judging a stale world |
| 6 | EXECUTE | Subagent-driven-development: workdir + brief file + report file + **explicit model name** + ledger line per task; no prose-only dispatch |
| 7 | VERIFY | Environment stated (interpreter version, host, branch SHA); artifact attached; reproduce-before-fix for any bug claim |
| 8 | TRACE | Commit + provenance packet + agentmemory save + ledger closed — past-tense claims require a ledger citation or they are disallowed |

---

## 2. Claim Truth Model (mandatory on every load-bearing statement)

- **[Verified]** — retrieved this session from a primary source, with **stated scope** (which branch, which repo, which environment).
- **[Specified]** — stated intent/design, not yet observed directly.
- **[Aspirational]** — roadmap/goal language from a source.
- **[Unverified]** — encountered, unchecked — never appears in a +1/NOW decision.

**Critical addendum (from this session's failures):** a "[Verified: not found]" claim is only as good as the search scope. Every negative result must state *what was searched* (e.g., "GitHub code search across all pushed branches") so a reader can immediately identify blind spots (local unpushed commits, workspace-local scratch dirs, private logs).

---

## 3. Cross-Verification Protocol (new — closes the gap this session exposed)

Before accepting or issuing any "not found" / "doesn't exist" claim:

1. State the exact surface searched (repo, branch, index type — code search vs. full-text vs. local filesystem).
2. Name at least one plausible reason the surface could be incomplete (unpushed commits, gitignored paths, private CI logs, workspace-local dirs like `.hermes/`).
3. If the claim is going into a consensus packet or a decision gate, treat "not found on surface X" as [Unverified] for reality, not [Verified] for absence, until the author confirms.
4. Flag branch/push divergence explicitly whenever a PR or branch is being reviewed by an external verifier — divergence itself is a risk to log, not just a caveat.

---

## 4. Multi-Lens Analysis (structural, per non-trivial decision)

Run at least three: **Practical** (does it work mechanically), **Critical** (who benefits, process-theater risk), **Systems** (feedback loops — e.g., chat-plan→incident→meta-audit→more docs), **Two-Eyed Seeing** (technical fix vs. relational trust rupture), **Standpoint** (maintainer vs. executor-agent vs. downstream reviewer). Name which lenses were run; do not bury them in an appendix.

---

## 4b. The Four-Artifact Request Rule (Gates 3–7, compressed to one check)

Gates PLAN → VERIFY are correct but slow to apply mid-flight. This is the same discipline as a single pass over any request for implementation work, incoming or outgoing.

**A well-formed request carries four artifacts. Name all four, or say why one is unnecessary.**

| # | Artifact | The question it answers |
|---|---|---|
| 1 | **Decision / boundary** | Which ADR, canon doc, or operator instruction governs this? |
| 2 | **Contract** | What spec, schema, or explicitly-stated current behaviour defines correct? |
| 3 | **Mechanism** | What is the *smallest* code neighbourhood that implements it? |
| 4 | **Evidence** | Which focused test or eval exercises it, and what is the exact command? |

**The diagnostic, which is the useful half:** if a request asks only for architecture prose before changing code, or only for code without its contract and test, ask why the omitted layer is unnecessary. A request missing artifact 1 tends to relitigate settled decisions. Missing 2 produces work that cannot be judged correct. Missing 3 produces sprawl. Missing 4 produces claims that cannot graduate past `Specified`.

This composes with, and does not replace, the truth model in §2 and the cross-verification protocol in §3 — artifact 4 is what lets a claim be labelled `Verified` rather than asserted.

> **Provenance:** adapted 2026-08-12 from the "cross-domain request rule" in the Codex-generated repository atlas (`.toilet/2026-08-11-flossi0ullk-repo-atlas/DOMAINS.md`), which stated the shape more compactly than our own gates did. Idea only — no material was copied. Logged in `docs/research/reuse-ledger-seed.yaml` entry `0073`.

---

## 5. Refusal Rules (the actual enforcement layer)

- No Execute step without an existing plan-file path.
- No subagent dispatch without brief file + report file + explicit model + workdir.
- No past-tense completion claim ("done," "fixed," "removed ✅") without a ledger-line citation.
- No System/Substrate change without a pre-work consensus claim citing branch-divergence state.
- No "not found" claim treated as ground truth without stated search scope.

---

## 6. 5-Box Compliance Self-Check (append to every substantive output)

1. Intent echoed?
2. Evidence gate applied — truth labels + search scope stated?
3. Anti-sycophancy — explicit counter-argument or red flag surfaced?
4. Clarification sought if ambiguous?
5. Existing work searched (agentmemory, prior sessions, prior audits) before acting?

---

## 7. Minimal Viable Test of This UOP

Run it end-to-end on one bounded, Local-radius task (e.g., the issue #28 gap-matrix extraction) before trusting it on a System-radius task (e.g., OmniRoute reconfiguration). If the loop holds under a small, low-stakes case — plan file written, ledger populated, no unfounded claims — promote it to System-radius work with confidence; if it breaks even there, the enforcement layer (not the design) needs rework.

---

## 8. Provenance Packet Template (attach to every decision)

```yaml
provenance_packet:
  claim_type: ""
  payload:
    summary: ""
    search_scope_stated: true/false
    branch_divergence_checked: true/false
  truth_status:
    key_claim_1: "Verified|Specified|Aspirational|Unverified"
  next_action: ""
```
