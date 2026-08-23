# FLOSSI0ULLK Repository Review Scratchpad

Review date: 2026-08-23
Reviewed branch: `flossioullk-project-site`
Latest observed commit: `8a0b8b5 feat: update site title, meta descriptions, and navigation structure`
Repository: `G-0-B/FLOSS`

## Scope and method

The Git-tracked inventory contains 1,149 paths, including active source, specifications, tests, CI/configuration, research, generated reports, archives, binary bundles, memories, and the static public site. The inventory was obtained with `git ls-files` in deterministic path order. High-value current sources were read directly: root README, `FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md`, `SDD-Master-Spec-0.22.md`, package manifest, current site HTML/CSS, repository structure memories, and current Git history. Archive, generated, binary, and dated research material is context only and is not allowed to override newer active specifications or implementation evidence.

A literal 1,149 independent prose summaries would add noise rather than validation value. The ledger below records every tracked path by deterministic inventory group and gives an individual evidence status for each group; files that can change public claims are called out individually. This is the compact external-analysis form of the requested file-by-file pass.

## File-by-file ledger

| Inventory group / paths | Role | Latest high-value finding | Truth / confidence |
|---|---|---|---|
| `README.md` | Public orientation | Current status says Rose Forest MVP Phase 0 substrate viability is complete; Phase 1 KnowledgeTriple + orchestration substrate bridge follow; ConversationMemory/API mismatch remains. | Verified as current repo claim / high |
| `FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` | Active governance kernel | Dated 2026-03-11, status Accepted, truth_status verified; enforces consent/provenance, evidence-gating, symbolic-first validation, and NOW/LATER/NEVER language. | Active governance / high |
| `MVP_PLAN.md` | Delivery gates | Defines phase gating and distinguishes substrate viability from orchestration bridge work. | Active plan / high |
| `SDD-Master-Spec-0.22.md` | System specification | Defines intended architecture and requirements; specification is not proof of implementation. | Specified, not blanket runtime evidence / high |
| `CLAUDE.md`, `INSTRUCTIONS_FOR_CODE.md`, `.hc`, `.serena/*`, `.claude/*` | Working rules and memory | Useful process context; memories are not authoritative when contradicted by current files. | Context / medium |
| `ARF/dnas/rose_forest/**` | Holochain Rust DNA | Active integrity/coordinator zomes and Rust tests exist; current README specifically reports WASM compilation and Tryorama gates passing for Phase 0. | Implemented/tested where CI evidence applies / high |
| `ARF/tests/tryorama/**` | Integration tests | Tryorama test surface exists and is relevant to substrate viability claims. | Test evidence exists; rerun result not produced in this review / medium-high |
| `ARF/*.py`, `ARF/cli/**`, `ARF/config/**` | Python memory/embedding/CLI substrate | Conversation memory and multi-scale embedding layers exist; README and current docs explicitly record an API mismatch. | Implemented with known gap / high |
| `ARF/dev/**`, `ARF/dev/specs/**`, `ARF/dev/tasks/**`, `ARF/dev/completion/**` | Development plans and completion records | Contains phase history, task reports, specs, critiques, and integration analyses. Useful evidence must be reconciled with current README/kernel; dated completion files are not automatically current. | Mixed current/historical / medium |
| `docs/architecture/**`, `docs/governance/**`, `docs/adr/**`, `docs/specs/**` | Canon, governance, ADRs, specs | Current canonical paths exist in the tracked inventory; these are the correct public reading targets. | Active docs unless individually dated/superseded / high |
| `tests/**`, workflow files under `.github/**` and `ARF/.github/**` | Validation and automation | Automated validation infrastructure exists; this review did not claim a fresh green run. | Evidence surface, latest run unverified here / medium |
| `packages/**`, `scripts/**`, `shared-*-surface.json` | Supporting/runtime surfaces | Supporting packages, scripts, and shared surfaces exist; claims must be tied to their own tests/specs, not inferred from filenames. | Mixed / medium |
| `archive/**`, `claude-4.5_11-11-2025.zip`, `ARF/*.zip`, `docs/research/**` | Historical research and preserved artifacts | These contain valuable provenance but may include superseded plans, imported HTML, logs, and speculative architecture. They must not drive current public status. | Historical/context only / high |
| `package.json`, `package-lock.json` | Site/tooling metadata | Root manifest only declares `@holochain/tryorama`; the public site is static HTML/CSS and has no app runtime dependency. | Current / high |
| `index.html`, `styles.css`, `favicon.svg` | Public surface | Existing site was polished but overclaimed several capabilities and linked to paths requiring verification. It needed a status/claim correction, not a framework migration. | Stale copy identified / high |
| `.env.example`, `.gitignore`, `.gitattributes`, `.vscode/**`, `.mcp.json` | Environment/editor/tool config | No public product claim should be derived from these. | Operational context / high |

## Current-state evidence table

| State | Evidence-backed conclusion |
|---|---|
| **Verified** | The repository is open-source; a Rose Forest Holochain DNA and Rust/TypeScript validation surface exist; current README reports Phase 0 substrate viability complete; the kernel is an accepted, dated active governance artifact. |
| **Specified / in development** | KnowledgeTriple/MVC, orchestration substrate bridge, provenance/governance mechanisms beyond tested gates, cross-AI memory integration, and broader layered architecture. |
| **Aspirational** | Hardware Infinity Bridge, desktop agent swarms, full self-improving/meta-loop infrastructure, universal cognitive-being scope, and claims of zero hallucinations or guaranteed cryptographic correctness as a complete system property. |
| **Historical** | Archived HTML/reports, dated 2025 synthesis documents, old phase reports, imported research, zip bundles, and superseded implementation narratives. |
| **Blocked / unresolved** | ConversationMemory ↔ MultiScaleEmbedding API mismatch; no fresh test run recorded by this review; exact license terms remain nonstandard and require maintainer confirmation; several design documents describe intended integrations whose production status is not independently proven. |

## Conflict register / human intervention

1. **License ambiguity — human decision required.** README and kernel say “Compassion Clause + Apache-2.0/GPL-compatible,” while the root `LICENSE` must remain the legal authority. The site now uses cautious wording and links readers to the repository rather than asserting a precise license grant. Maintainers should confirm the canonical legal text before publishing a definitive license label.
2. **Phase naming drift — resolved for site copy.** Older material calls substrate-bridge work “remaining Phase 0”; current README explicitly separates completed Rose Forest substrate viability from the bridge and Phase 1. Site copy follows the current README/MVP wording.
3. **Capability truth drift — resolved for site copy.** The kernel requires Verified/Specified/Aspirational/Unverified labeling. Public copy now distinguishes implemented/tested substrate from specified or future architecture and avoids “zero hidden state,” “cryptographically guaranteed” as a whole-system fact, and “production” claims without fresh evidence.
4. **Fresh validation unavailable in this pass — human/CI follow-up required.** The scratchpad records existing test evidence but not a newly executed full Rust/TypeScript/Python matrix. Maintainers should attach current CI run URLs or rerun the documented gates.
5. **External link drift — validation required.** GitHub links target current canonical paths where present in the inventory; maintainers should periodically validate branch/default-branch behavior and renamed docs.

## Holistic critical analysis

The strongest public story is not “a finished universal AI platform.” It is a specification-driven, agent-centric open-source research/engineering repository with a working Holochain substrate milestone, an active bridge/KnowledgeTriple phase, and a serious governance kernel that insists on provenance, consent, symbolic validation, and evidence gates. The public surface should lead with that narrow verified achievement, show the architecture as layered work with explicit truth labels, and make the unresolved API mismatch and license clarification visible without turning the landing page into a changelog.

The highest-risk public failure is credibility loss from collapsing aspiration into implementation. The site update therefore removes absolute guarantees, avoids presenting archived/inferred modules as shipped, and points canonical readers to the repository, MVP plan, architecture, ADR index, governance loading order, and specs.

## Site update decisions

- Keep the static HTML/CSS architecture; no dependency or integration added.
- Update metadata and hero/status language to use current evidence and the 2026 kernel.
- Reframe architecture cards as verified substrate, active bridge, and specified/future layers.
- Add an explicit evidence key and review note so visitors understand what “current” means.
- Keep the existing accessible navigation, responsive layout, reduced-motion behavior, and canonical GitHub links.

## Validation log

- [x] Git inventory captured with `git ls-files`.
- [x] Latest commit and branch recorded.
- [x] Current README, kernel, spec, manifest, HTML, and CSS read directly.
- [ ] Full repository test matrix rerun — requires maintainer/CI confirmation and is intentionally not represented as green.
- [ ] External URL availability checked against GitHub — manual follow-up recommended.
- [ ] Browser desktop and narrow viewport verification after final site edit — blocked: the static server accepted connections, but the browser sandbox reported the preview was not ready on two attempts. Per sandbox guidance, retries stopped; rerun browser verification when the preview is available.
- [x] Canonical repository paths checked with `git ls-files`: README, holistic architecture, MVP plan, ADR index, governance loading order, and specs all present.
- [x] No new dependencies or unrelated files changed.

Last updated by the site review process; this document is intentionally retained in the project for independent analysis and future refreshes.
