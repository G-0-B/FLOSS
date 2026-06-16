---
id: project-root-intake-2026-05-19
type: project
created: '2026-05-19'
status: active
applies_to:
- any-agent
source: codex_session
title: Workspace root intake relocated to dated raw holding area
---

On 2026-05-19, 49 loose workspace-root intake files plus the extracted
`sitegeist/` intake directory were moved into a dated raw holding area. File
hashes are recorded at `.agent-surface/intake/root-intake-moves-2026-05-19.json`;
the extracted directory tree hash is recorded at
`.agent-surface/intake/root-intake-directory-moves-2026-05-19.json`.

Current raw holding paths:

- Architecture intake:
  `FLOSS/docs/architecture/FLOSSI0ULLK-Architecture-Spec-v0.1.md`
- Reports:
  `FLOSS/docs/research/intake_raw/2026-05-19-root/reports/`
- Reference PDFs/DOCX:
  `FLOSS/docs/research/intake_raw/2026-05-19-root/reference/`
- Bundles:
  `FLOSS/docs/research/intake_raw/2026-05-19-root/bundles/`
- Digestion map:
  `FLOSS/docs/research/2026-05-19-root-intake-digestion.md`

This was a relocation/provenance pass, not canon promotion. Do not cite raw files
from `intake_raw/` as authoritative without a distillation doc, spec/ADR,
working-todo entry, or consensus claim.

Root leftovers are intentional: config/orientation files, OpenClaw-style agent
workspace files (`HEARTBEAT.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `SOUL.md`),
`AGENTMEMORY.md`, `opencode.jsonc`, `vibe-floss.ps1`, and the
`floss_plane_rewritten_bootstrap.tar.gz.terabox.uploading.cfg` uploader-state
file. Root directories intentionally left include `FLOSS/`, `FLOSSI_U/`,
`_reference/`, `data/`, `node_modules/`, and agent/tool config directories.

Highest-leverage next distillations are the sycophancy/audit pair, the two
harness/memory HTML articles, agentic-security references, and isolated
inspection of the code/archive bundles, including `sitegeist_extracted/`.
