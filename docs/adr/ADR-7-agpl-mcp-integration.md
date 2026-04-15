# ADR-7: AGPL Integration via MCP

## Status
Accepted (2026-04-15)

## Context
The FLOSSI0ULLK architecture envisions multi-agent collaboration and governance utilizing powerful complementary tools like AIngram and Agorai. Both of these projects are licensed under the AGPL-3.0 (GNU Affero General Public License). FLOSSI0ULLK itself aims for an Apache-2.0 / GPL-compatible posture (with the Compassion Clause).

Directly porting or tightly coupling AGPL-3.0 code into the core FLOSSI0ULLK Python/Rust packages (`metacoordinator_mcp`, `ARF`, etc.) would trigger the AGPL copyleft clause, forcing the entire derived codebase to adopt the AGPL license. This presents a potential misalignment with the broader interoperability goals of the project.

## Decision
We will integrate with AGPL-licensed external services (specifically AIngram and Agorai) **strictly over the Model Context Protocol (MCP)** or standard HTTP APIs, running them as standalone, isolated bridge services or satellite contributors.

1. **No Code Porting:** We will not port AIngram's domain modules (like its formal vote lifecycle logic) directly into the FLOSS Python codebase.
2. **Satellite Architecture:** We will stand up AIngram and Agorai locally (via Docker or local npm global installs) and configure our `metacoordinator_mcp` gateway to treat them as independent agents/services on the network.
3. **Boundary:** Communication between FLOSSI0ULLK and AGPL services must remain strictly at arm's length (API/MCP borders). This architectural boundary insulates FLOSS from AGPL propagation, as connecting to an AGPL service over a network API does not trigger the copyleft provisions on the caller.

## Consequences
- **Positive:** We can leverage 60+ migrations of production-grade governance and multi-agent debate logic (AIngram/Agorai) immediately without polluting the FLOSS license posture.
- **Positive:** Maintains the modular, agent-centric philosophy of the system (Layer 4 RSA).
- **Negative:** Adds a runtime dependency (Docker/npm) to utilize these features, introducing more surface area for ops overhead in local developer environments.
- **Negative:** Substrate philosophy mismatch (AIngram relies on PostgreSQL rather than Holochain) must be navigated at the data boundary; FLOSS will remain Holochain-native, treating AIngram merely as a contributor or specialized oracle.