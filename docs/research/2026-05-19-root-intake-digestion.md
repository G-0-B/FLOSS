# 2026-05-19 Root Intake Digestion Map

```yaml
id: "2026-05-19-root-intake-digestion"
status: "Relocated raw intake; semantic digestion pending"
truth_status:
  relocation: "Verified"
  canon_promotion: "Not performed"
  semantic_distillation: "Specified"
move_log: ".agent-surface/intake/root-intake-moves-2026-05-19.json"
directory_move_log: ".agent-surface/intake/root-intake-directory-moves-2026-05-19.json"
raw_holding_area: "FLOSS/docs/research/intake_raw/2026-05-19-root/"
```

## What Changed

The workspace root had accumulated a mixed intake pile of reports, continuation
packets, raw research PDFs, HTML articles, and code/archive bundles. On
2026-05-19, 49 top-level intake files plus one extracted intake directory
(`sitegeist/`) were relocated into a dated raw holding area. File moves have
SHA-256 hashes recorded in `.agent-surface/intake/root-intake-moves-2026-05-19.json`;
the extracted directory has a deterministic tree hash recorded in
`.agent-surface/intake/root-intake-directory-moves-2026-05-19.json`.

This pass is a placement and provenance pass, not a claim that all contents are
now canonical. Root intake moved forward into `FLOSS/docs/research/` rather than
`archive/`, preserving the project convention that archive is for superseded
canonical material, not fresh raw intake.

## Buckets

| Bucket | Path | Count | Meaning |
|---|---:|---:|---|
| Architecture intake | `FLOSS/docs/architecture/FLOSSI0ULLK-Architecture-Spec-v0.1.md` | 1 | Historical architecture spec with supersession banners; useful evidence, not sole current canon |
| Reports | `FLOSS/docs/research/intake_raw/2026-05-19-root/reports/` | 35 | Continuation packets, strategic memos, prior analyses, HTML articles, and agent-alignment artifacts |
| Reference | `FLOSS/docs/research/intake_raw/2026-05-19-root/reference/` | 8 | PDFs/DOCX that need later paper-style distillation before influencing canon |
| Bundles | `FLOSS/docs/research/intake_raw/2026-05-19-root/bundles/` | 5 archives + 1 extracted dir | ZIP/TAR artifacts and paired extracted `sitegeist_extracted/` directory needing separate inspect pass |

Root files intentionally left in place: workspace config/orientation files,
OpenClaw-style agent workspace files (`HEARTBEAT.md`, `IDENTITY.md`, `USER.md`,
`TOOLS.md`, `SOUL.md`), `AGENTMEMORY.md`, `opencode.jsonc`, `vibe-floss.ps1`, and the
`floss_plane_rewritten_bootstrap.tar.gz.terabox.uploading.cfg` uploader-state
file.

Root directories intentionally left in place: `FLOSS/` main project,
`FLOSSI_U/` sibling project, `_reference/` read-only library, `data/` runtime
state, `node_modules/`, and agent/tool config directories such as
`.agent-surface/`, `.claude/`, `.gemini/`, `.mcp/`, `.vibe/`, `opworkers/`, and
`plugins/`.

## High-ROI Digestion Order

1. **Sycophancy protocol pair**:
   `Sycophancy resistance protocol 2.0_chatgpt.md` plus
   `Sycophancy resistance protocol 2.0_AUDIT_claude_opus4.7.md`. Extract only
   operational anti-sycophancy checks that strengthen ADR-3 / ADR-12 / voter
   calibration. Preserve the corrected history: this pair is contextually
   related to anti-sycophancy, but it is not the causal source of CFIS.
2. **Harness/memory articles**:
   the two Yanli Liu HTML articles on harness engineering and agent memory.
   Distill into the Context Daemon / Reasoning Ensemble / operator-primer
   surfaces if they add concrete mechanisms rather than generic vocabulary.
3. **Agentic security and persuasion references**:
   OWASP Agentic Applications, `Persuading AI to Comply with Objectionable
   Requests.pdf`, and the sycophancy pair should be read together for a
   practical hardening checklist.
4. **Leverage and memetics references**:
   `Leverage_Points.pdf` and `FromGenestoTemes-...pdf` are likely useful for
   governance/framing, but should not preempt substrate-bridge work.
5. **Bundles**:
   inspect `metaclaw-plugin.zip`, `awesome-openclaw-agents-2.0.zip`,
   `sitegeist.zip` / `sitegeist_extracted/`, and the `floss_plane*.tar.gz`
   artifacts in an isolated scratch directory before any promotion.

## Routing Rules For Future Agents

- Treat this document as the index for the 2026-05-19 raw intake bucket.
- Load the move log for exact file hashes and source-to-destination mapping.
- Do not cite files in `intake_raw/` as canonical evidence without a distillation
  doc, ADR, spec, consensus claim, or explicit working-todo entry.
- If a raw intake file changes a load-bearing architectural claim, promote that
  change through the normal SDD path: spec or ADR first, implementation/tests
  second, shared surfaces last.
- If adding new root drops later, either run the watcher/event path or create a
  new dated intake bucket; do not mix new intake into this 2026-05-19 batch.
