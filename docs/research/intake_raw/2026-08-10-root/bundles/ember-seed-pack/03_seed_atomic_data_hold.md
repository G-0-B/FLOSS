# Seed: Atomic Data — HOLD/conditional-adopt decision record

```yaml
id: "ccp-seed-atomic-hold"
version: "1.0.0"
status: "Accepted"
updated: "2026-06-09"
origin_thread: "claude.ai chat a983acaa-ba2a-4283-a1d3-aaa07f39de1e (2026-05-28)"
gate: "Open when interchange-format or MCP-frontend work resumes; not before."
```

**Decision (standing):** ADOPT Atomic Schema + Atomic Commits + JSON-AD as interchange
format over the Holochain DHT (Commits ↔ source-chain entries: both append-only,
agent-signed, keypair-authored). REJECT Atomic Server's hierarchy-ACL trust model —
incompatible with DHT-wide shared validation + capability-token membrane access.
MCP flagged as centralization-by-default chokepoint; long-term want is a DHT-native
tool protocol.

**Gated next actions (unexecuted as of 2026-06-09):**
1. Evaluate Atomic Schema/JSON-AD over DHT (spike-sized)
2. Capability-token gate on any MCP frontend
3. Prototype Collection→DHT-links translation
4. Reconcile provenance representations (Atomic Commit chain ↔ DKVP/provenance packets)

**Cross-link:** SCP-Sovereign (file 01 §2) failed on the SAME centralization axis —
this HOLD is now a 2-case pattern; one more and the evidence gate (≥3-case) makes
"centralized-trust adapters rejected, concepts re-expressed as capability tokens" a
documentable doctrine rather than ad-hoc taste.
