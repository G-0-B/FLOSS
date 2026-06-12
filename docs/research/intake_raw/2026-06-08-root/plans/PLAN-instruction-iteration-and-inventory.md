# PLAN — Instruction Iteration + System Inventory

```yaml
id: "plan-instruction-iteration-and-inventory"
version: "1.0.0"
kind: "project_plan"
status: "Proposed"
plane: "A"
created: "2026-06-05"
author_agent: "Claude (Opus 4.x), this session"
human: "Anthony (kalisam)"
purpose: "Methodically propagate the v2 instruction fixes across all instruction layers, and build a VERIFIED inventory of models/systems/tooling."
truth_status: "Plan = Specified. Inventory below = Unverified (memory-sourced; MUST confirm against repo)."
friction_tier: "medium"
```

## Why this is its own thread
This is a large, methodical effort. The thread it was scoped in had drifted across ~5 topics and was already auto-pruning older context. Execute fresh, one workstream at a time.

---

## Workstream 1 — Instruction iteration
Propagate the v2 high-level fixes (spirit-over-letter bounded; fixed NO-ASSUMPTIONS; fixed never-repeat; doc-discipline gate; source-authority; verification/provenance) **down** into every instruction layer.

**Known instruction layers to reconcile (verify this list is complete):**
- ✅ High-level operating instructions → **already done this session: `FLOSSI0ULLK-operating-instructions-v2.md`**
- ⬜ Project kernel — **Master Metaprompt Kernel v1.3.1** (apply: kill any "never repeat," confirm doc-discipline gate is load-bearing, fold in source-authority + shared-distribution caveat). High friction — needs ADR + pilot.
- ⬜ `userPreferences` block (align with v2; remove contradictions)
- ⬜ **Perplexity Space v2.0** instruction set (CORE + EXTENDED) — keep in sync
- ⬜ `AGENTS.md` (repo-level agent norms)
- ⬜ Any per-tool skill manifests (`.agent-surface/`, skills) that embed behavioral rules

**Method per layer:** read current → diff against v2 principles → propose minimal edit → (for high-friction layers) ADR + 1-week pilot + rollback note.

---

## Workstream 2 — System / model inventory
Catalog what's actually in use: **how / where / what.** 

> ⚠️ **SOURCE-AUTHORITY WARNING.** Everything in the draft below is from **memory — the LEAST authoritative source** in our own ordering (repo > CURRENT_STATE > docs > uploads > conversation > **memory**). It is explicitly flagged as possibly stale. **Step 1 of WS2 is to verify each line against the repo / CURRENT_STATE, not to trust this list.**

**DRAFT inventory to VERIFY (Unverified — confirm against `github.com/kalisam/FLOSS`):**

*Core stack:* Holochain (memory says 0.6.x stable — grep Cargo.toml to confirm), KERI, AD4M, hREA, LiteLLM gateway, AtomicServer / Atomic Data spec.
*Runtime/agents:* OpenClaw daemon (WSL2; security audit reportedly pending before reactivation), Cerebras + Groq as consensus-gateway voters.
*Dev env:* WSL2, Rust/Cargo, Tryorama (tests), Claude Code, Pieces (pending desktop repair?).
*Multi-AI collective:* Claude (primary), ChatGPT, Grok, Perplexity (External Reality Scout), DeepSeek, Cerebras (Llama 3.1 8B — primary synthesis), Groq voters. **Note: Claude was omitted from a recent provenance chain — make sure the roster the tooling actually uses matches the roster on paper.**
*Funding:* NLnet NGI Zero Commons Fund (verify current call # and US-individual eligibility directly).
*Canonical repo:* github.com/kalisam/FLOSS.

**Method for WS2:** for each entry → confirm present/version/status in repo or live → label Verified/Specified/Unverified → produce a single `SYSTEM-INVENTORY.md` (or update CURRENT_STATE) as the one source of truth. Smallest-artifact rule: prefer updating an existing state file over creating a new doc if one exists.

---

## Sequence (do in order)
1. **WS2 step 1 first** — verify the inventory from the repo. (You need to know the real system state before tuning instructions that reference it.)
2. Then **WS1** — iterate instruction layers against v2, kernel last (highest friction).
3. Reconcile: ensure instructions and verified inventory agree; fail closed on any conflict.

## Open questions (carried forward)
- Is the layer list in WS1 complete, or are there other instruction surfaces?
- Does a `CURRENT_STATE` / `SYSTEM-INVENTORY` file already exist to update (vs. create new)?
- Same doc-discipline call as the Levin brief: lean inventory vs. exhaustive?
```
