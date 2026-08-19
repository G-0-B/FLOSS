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