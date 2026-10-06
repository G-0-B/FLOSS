# ADR-7: Embracing AGPL-3.0 Copyleft Cascade

## Status
Accepted (2026-04-15)

## Context
The FLOSSI0ULLK architecture (Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge) is fundamentally a commons. Integrating with AGPL-3.0 licensed external services (like AIngram and Agorai) by porting their code would trigger the AGPL copyleft clause, forcing the derived FLOSSI0ULLK codebase to adopt the AGPL license.

Initially, we considered isolating these services behind MCP/API boundaries to avoid this cascade and maintain a looser Apache-2.0 / GPL-compatible posture. However, this defensive posture fundamentally misaligns with the core philosophy of the project. 

AGPL-3.0 is the strongest copyleft license available, specifically designed to close the SaaS loophole. It dictates that anyone running this software over a network and modifying it must share those modifications back to the commons. This cascade is a feature, not a bug. It is the legal embodiment of the "Voluntary Convergence Manifesto" and consent-based governance. It ensures that downstream users who benefit from the orchestrator must contribute back to the provenance substrate.

## Decision
We explicitly accept and embrace the AGPL-3.0 copyleft cascade for the FLOSSI0ULLK core orchestration and consensus layers.

1. **License Adoption:** The core FLOSSI0ULLK orchestrator and consensus gateway (`metacoordinator_mcp`, `ARF`, etc.) will be licensed under AGPL-3.0 (or later).
2. **Direct Integration Allowed:** We are no longer artificially constrained to MCP/API boundaries for integrating AIngram, Agorai, or other AGPL-licensed domain logic. We may port their code directly into our Python/Rust codebases where it makes architectural sense.
3. **Stewardship Carve-Out (Dual-Licensing):** We recognize that strict AGPL may exclude certain high-value, alignment-positive collaborators (e.g., hospitals, educational institutions, or humanitarian organizations that cannot open-source their proprietary patient/student data systems). We reserve the right to offer dual-licensing exceptions or specific carve-outs via a formal Steward Vote for use cases where the spirit of universal flourishing is served, even if the letter of strict open-sourcing cannot be met.

## Consequences
- **Positive:** Absolute ideological integrity. The legal framework now perfectly mirrors the architectural and philosophical framework (Layer 0 sovereignty, 1=NONE ALONE ALLONE).
- **Positive:** Unblocks direct code porting from AIngram (e.g., formal vote lifecycle, trust math) into the Python orchestrator, removing the need for a runtime Docker dependency just to access consensus logic.
- **Positive:** Provides a mechanism (steward vote) to grant exceptions for medical, academic, and humanitarian use cases, ensuring the license protects the commons without blocking genuine flourishing.
- **Negative:** Commercial entities building closed-source SaaS platforms on top of FLOSSI0ULLK will be legally prohibited from doing so without a dual-license agreement. This is an intended consequence, but will reduce adoption among proprietary software developers.
## Execution Record

**Truth Status: Verified (2026-08-12).** Previously *Specified* — decided but not executed. Closed as follows.

| Surface | Before | After |
|---|---|---|
| `FLOSS/LICENSE` | 674-line GPL-3.0 text | `SPDX-License-Identifier: AGPL-3.0-or-later` (42 B, byte-identical to `FLOSSI_U/LICENSE`, sha256 `de247d96a16b`) |
| `FLOSSI_U/LICENSE` | already AGPL SPDX | unchanged |
| Kernel header `license:` | `"Compassion Clause + Apache-2.0/GPL-compatible"` | `"AGPL-3.0-or-later"` |
| `FLOSS/README.md` §License | `Compassion Clause + Apache-2.0/GPL-compatible (per Kernel v1.2)` | AGPL-3.0-or-later, with the §3 carve-out stated |
| `docs/adr/INDEX.md:34` | Truth Status `Specified` | `Verified` |

Superseded GPL-3.0 text archived at `archive/LICENSE_GPL-3.0_superseded-by-ADR-7_2026-08-12.txt` — never deleted, per standing doctrine.

**Why this sat unexecuted for ~4 months.** The decision landed 2026-04-15 and propagated to `FLOSSI_U/`, the reuse ledger (`entry 0068`: *"compatible with AGPL-3 cascade per ADR-7"*), and `RESEARCH-REGISTER.md`. It never reached `FLOSS/LICENSE`. The 2026-08-12 `.toilet` reuse sweep surfaced the gap in the worst possible way: an agent read `LICENSE` and `RESEARCH-REGISTER.md`, found them contradictory, trusted the file it had opened, and concluded the project was GPL-3.0 — which would have *blocked* the AIngram/Agorai porting that §2 of this ADR exists to *unblock*.

**Standing lesson, recorded here because this is where it will be read:** when two surfaces disagree about a decision, look for the governing ADR before treating the conflict as unresolved. The kernel's §11b source-authority ladder ranks repo docs above conversation and memory; `adr/INDEX.md` had carried the correct `Specified` label the entire time.

**Still open under §3:** the dual-licensing / Steward Vote carve-out has no procedure yet. AGPL is now the default grant; there is no defined path for a hospital or school to request an exception. That is a governance gap, not a licensing one.

**SUL-1.0 contamination — RESOLVED 2026-08-12.** `packages/metacoordinator_mcp/voters.py` carried `MOMUS_PERSONA_SYSTEM`, adapted from oh-my-opencode v4.0.0 (**SUL-1.0**, source-available, not OSI). SUL-1.0 is incompatible with AGPL-3.0 exactly as it was with GPL-3.0, so executing this ADR did not by itself resolve it.

Fixed by clean-room rewrite, operator-directed: the prompt is now `EXECUTABILITY_REVIEWER_SYSTEM`, written from this repo's own consensus schema rather than the upstream text. `make_omo_momus_voter` → `make_executability_voter` (old name aliased), registry keys `omo-momus-*` → `exec-review-*` (old prefix still routes). No SUL-1.0-derived text remains under `packages/`; the only surviving mention is the comment recording that it was removed. 162 tests pass.

`CRITIC_PERSONA_SYSTEM` was never affected — original FLOSSI0ULLK text encoding the UTN constraint; only its `omo-critic-` name prefix was borrowed, which carries no licence implication.

Per ADR-12, voter persona prompts are *Governed* and a change requires explicit binding; the operator instruction of 2026-08-12 is that binding. The replacement persona is ⚠️ **Specified** — consensus round `019e1d61` validated the persona it replaces, not this one.
