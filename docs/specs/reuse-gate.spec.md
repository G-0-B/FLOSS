# Reuse Gate — Prior-Art & Reuse Enforcement (ADR-18)

```yaml
id: "reuse-gate-spec"
version: "1.0.0"
kind: "spec"
status: "Active"
created: "2026-07-16"
truth_status: "Specified; --check enforcement Verified on landing"
schema: "reuse-gate.schema.json"
adr: "docs/adr/ADR-18-prior-art-reuse-gate.md"
design: "docs/research/intake_raw/2026-08-10-root/reports/2026-07-16-prior-art-reuse-gate-design-proposal.md (non-canonical; relocated from workspace root 2026-08-10)"
approval: "Operator (Anthony) 2026-07-16: shape B+C; 120-day evidence window; voter roster reuse-review profile; retrospective PR38 audit"
```

## What this is

The enforcement layer for the existing "search before building" principle (D7 spec_gate, SDD constitutional gates, `before_build_check`). Not a new registry, not a new hook: a `reuse` block on existing spec-registry entries, validated fail-closed by `spec_gate.py --check`, with adversarial cross-family review for architecture-class work.

## Tiers

- **Tier 0 (never gated):** intake, research, continuation packets, docs edits, tests, bug fixes, emergency preservation. Identical to spec_gate EXEMPT surfaces.
- **Tier 1 (`"tier": 1`):** new capability-introducing artifact on a GATED surface → entry must carry a valid `reuse` block.
- **Tier 2 (`"tier": 2`):** architecture-class (needs-an-ADR heuristic: storage/packaging formats, protocols, security/provenance mechanisms, new `FLOSS/packages/*`) → `reuse` block + independent reuse review + probe requirement for `compose`/`build` verdicts.

Emergency escape: `"emergency": true` downgrades a missing reuse block to a warning. The gate then fires at promotion/generalization time — no emergency artifact may be productized or depended on until its retrospective audit lands.

## Decision ladder

`adopt` is the default verdict. Each step rightward (`extend` → `compose` → `build`) requires showing, with per-candidate truth status, why the previous rung fails a **stated requirement** — not a preference. Tiebreaker: `artifactually bridging.md` §8 principles (open standards, maintained, federated, plural). Untested incompatibility claims are ⚠ Specified and cannot justify `build` alone.

## Tier-2 review

Run through the consensus gateway with voter profile **`reuse-review`** (aliases: `tier2`, `reuse`): ollama-gemma3-12b (Google family, local — Ollama v0.9.6 serving verified 2026-07-16), groq-qwen3-32b (Alibaba), mistral-devstral-small (Mistral). Three provider surfaces, three model families, none from the usual proposer families (Anthropic/OpenAI) — the Polly pattern as roster policy.

**Reviewer prompt (append to standard VOTER_PROMPT context):**

> You are reviewing a REUSE VERDICT, not code quality. The proposer claims existing FOSS/standards cannot cover this capability. Your job is adversarial: attempt to replace the proposed custom work with the listed candidates or ones the proposer missed. Vote NEGATIVE if: a candidate's rejection rests on an unprobed (⚠ Specified) incompatibility claim; the irreducible delta is not testable; the search predates the evidence window; or you can name a mature candidate the proposer did not list. Vote POSITIVE only if the delta would survive your best replacement attempt. State the strongest replacement you considered in your rationale.

## Guideline loop (ACON-style, operator-endorsed 2026-07-16)

This spec's search protocol and the risk register below are **optimizable guidelines in natural-language space**. Every discovered *gate miss* — duplication found after the fact — becomes a failure trace: record what search would have found it, add the capability→check-first row, refine the protocol. No weights, no new machinery; the guideline text is the optimization target (cf. ACON, arXiv 2510.00615, digested 2026-07-16).

### Search protocol (v1)

1. State the capability in one sentence, without FLOSSI0ULLK vocabulary.
2. Search: the risk register below → the relevant standards body (RFC/W3C/OCFL-style) → package ecosystems → `_reference/`.
3. Record versions, licenses, maintenance signals, platform fit **from primary sources with dates**.
4. Probe before rejecting (Tier 2): run the candidate against one real requirement.
5. Write the block; for Tier 2, request `reuse-review`.

## Reinvention Risk Register (guideline seed, v1)

| Considering building… | Check first | Status of check |
|---|---|---|
| Payload packaging / checksum manifests | BagIt (RFC 8493) | Specified (stable RFC) |
| Versioned preservation object layout | OCFL 1.1 (v2 in listening sessions) | Verified live 2026-07-16 |
| Dedup/encrypted snapshots + restore | restic 0.19.1 / BorgBackup — **Windows probe PASSED 2026-07-16**: full 8.969 GiB dirty FLOSS worktree (24,000 files) backed up in 27s (4.565 GiB stored); re-run 7s / 0 B added; restore hash-verified; `check --read-data-subset=5%` clean. FAQ performance concern does not manifest on this hardware. | ✅ Probed 2026-07-16 |
| Step attestation / authorized supply-chain steps | in-toto layouts + link metadata | Verified live 2026-07-16 |
| Git history packaging | `git bundle` (already used) | Verified in repo |
| Multi-agent orchestration | Omnigent (Apache 2.0) | Specified (composition doc) |
| Model routing / cost management | OmniRoute (MIT) | Specified (composition doc) |
| Agent discovery / identity | NANDA AgentFacts | Specified (composition doc) |
| Economic contribution tracking | hREA / Valueflows | Specified (composition doc) |
| P2P knowledge commons | Arkology Data Commons Stack | Specified (composition doc) |
| Prompt compression pipeline | OmniRoute RTK stack; ACON guideline optimization | Specified (digest 2026-07-16) |
| Adversarial review mechanism | Omnigent Polly pattern; this gate's reuse-review profile | Verified (roster live) |
| Research/provenance metadata interchange | RO-Crate 1.2 | Unverified — refresh before reliance |
| Large-data + Git provenance | DataLad + git-annex | Unverified — refresh before reliance |
| Signed claims, votes, receipts, role grants and revocation, status derived from signed records | AD4M link expressions and Flows (coasys/ad4m) | Specified — upstream docs and source read at commit `0b833087` on 2026-11-16; nothing built or run. What the read found, and what it leaves ours, belongs in the audit record and is not asserted here |
| Agent identity, keys and signing | AD4M agent DID; Holochain agent keys | Specified — source read 2026-11-16, not run |
| Peer-validated storage, source chains, validation rules | Holochain integrity zomes (already the stated substrate) | Specified — the active integrity zomes were read on 2026-11-16 in a checkout that was not `main`. Field ranges and author binding are validated there. Links are not validated in either integrity zome, and the ontology check runs in the coordinator. A file-based or custom chain needs a stated reason |
| Turning Accepted ADRs into executable checks | archgate (PyPI) | Unverified — found by search 2026-11-16, not read |

## Retrospective audit #1 — PR38 preservation capsule (gate-miss trace #1)

Recorded per operator direction 2026-07-16. The capsule run itself was legitimate emergency-tier work (✅ 22,337 files authenticated across six evidence planes; fail-closed BLOCKED verify; no projection produced). The gate applies to **generalization of `salvage_spine`**, which is now Tier 2 pending:

- `capability`: dirty-worktree preservation with semantic evidence planes, dispositions, and fail-closed publication projection.
- `candidates` (from continuation packet §5 + live refresh): BagIt ⚠, OCFL 1.1 ✅(spec live), restic 0.19.1 ✅(docs live; Windows performance un-probed ⚠), in-toto ✅(model live), git bundle ✅(in use), DataLad/Borg/RO-Crate/Archivematica/SWH/Guix ❌ Unverified (not refreshed).
- `verdict` (provisional, ⚠ Specified): **compose** — standard payload packaging + in-toto-shaped attestations + custom semantic-plane/disposition/projection layer.
- `irreducible_delta` (hypothesis to falsify, packet §6): semantic evidence planes; index/tracked/untracked/ignored preservation; disposition vocabulary; private-preservation/publication separation; fail-closed projections.
- Blocking probe: **restic on Windows — RUN AND PASSED 2026-07-16** (repo: `C:\~shit\_reuse_probes\restic-repo`; run 1: 8.969 GiB / 24,000 files in 27s; run 2 dedup: 0 B added in 7s; restore of ADR-18 file SHA-256-verified; integrity check clean). The `compose` verdict's restic leg is now ✅ Verified; candidates list updated accordingly.
- `expiry_or_retest_date`: 2026-11-13 (120 days).
- Miss lesson → protocol: "preservation/packaging" now has five register rows; any capability statement containing *manifest, fixity, snapshot, or capsule* must hit the register before design.

## Retrospective audit #2 — AD4M and the local claim/vote stack (gate-miss trace #2)

Recorded 2026-11-16. Between May and November 2026 a file-based source chain, three vote tallies, three identity schemes and a set of proposed record types were built or designed while an audit of AD4M, the intended second foundation layer, sat in `docs/research` from 2026-05-09. This gate did not fire. What a check on 2026-11-16 found:

- **The work was outside the gated surfaces.** `packages/` and `ARF/dnas/` were not gated, and design work in intake folders is exempt by definition.
- **The register had no AD4M or Holochain row.**
- **The gate had no consumer.** No workflow ran `--check`. Its own evidence went stale on 2026-11-13 and nothing reported it.
- **The gate was not on the main branch.** It existed only on this unmerged branch.

Changes made with this trace:

- Register rows for AD4M (records, identity), Holochain (storage and validation) and archgate (ADR enforcement).
- `packages/`, `ARF/dnas/`, `.github/workflows/` and the six `shared-*-surface.json` manifests are now gated surfaces. Existing files are grandfathered with a one-line statement of what each is. A new file there needs an entry and a tier.
- A CI workflow that runs `--check` on every pull request was opened against main separately.

Miss lesson → protocol: a design that proposes a new record type, store, identity scheme or protocol names, in its header, the register rows it checked. This applies in intake folders too, where registration itself is still exempt. Nothing enforces this rule yet; it is a convention until a check reads those headers. The other two findings above (no consumer, not on main) are answered by the CI workflow and by merging this branch, not by this rule.

Not done here: the grandfathered files carry no reuse block, so the gate does not judge them. They are registered, not reviewed. The gate's summary counts them apart from judged entries, so "0 reuse violations" covers only tiered entries. A grandfathered file owes a tier and, at tier 1 or 2, a reuse block in the change that next modifies it (`--check --changed-from <ref>`), and in any case by 2027-03-16, after which `--check` fails on it (operator decision 2026-11-16: both limits). No CI workflow passes `--changed-from` yet, so until one does the touch rule runs only when someone invokes it.

## Falsifiers (the gate retires to a plain checklist if…)

Fires on <5 proposals in ~6 months; verdict-changed rate ≈ 0; median Tier-1 record cost >10% of implementation effort; or hook logs show search-first already reliable without it.
