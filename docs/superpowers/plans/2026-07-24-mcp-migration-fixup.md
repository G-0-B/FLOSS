# MCP Migration Fixup Plan — Post-Hermes Remediation

**Date:** 2026-07-24
**Author:** Cowork (Opus-class, Dispatch session)
**Parent plan:** `docs/superpowers/plans/2026-07-17-omniroute-inference-plane-migration.md`
**Truth Status:** ✅ Verified for Fixes 1–5 (applied + smoke-tested 2026-07-24, Claude Code Fable-5 session); ⚠️ Fix 6 (ADR-19 consensus claim) still pending operator go

## Execution notes (2026-07-24)

- **Fix 1: already done before this session.** `agentmemory-mcp` (v0.9.28) and `januscope` (0.4.4) both globally installed at `C:\Users\kalis\AppData\Roaming\npm\`; agentmemory MCP connects and serves tools in live Claude Code sessions. **Follow-up 2026-07-24 (evening):** under Hermes, JanuScope failed with `spawn agentmemory-mcp ENOENT` — the global install is a Windows `.cmd` shim, and resolving those requires PATH+PATHEXT, which Hermes strips from MCP subprocess environments (Claude Code passes them, which is why it worked there). Fixed in the shared lens (`.mcp/lenses/agentmemory.yaml`): target is now absolute `C:/Program Files/nodejs/node.exe` + `.../node_modules/@agentmemory/mcp/bin.mjs` — same pattern as the serena lens's absolute `uvx.exe`, which is why serena never hit this. Verified: JanuScope-wrapped initialize handshake succeeds, and `bin.mjs` also starts under a bare `env -i` environment. One lens edit fixes all harnesses.
- **Two Hermes homes discovered:** `C:\Users\kalis\AppData\Local\hermes` (live gateway, config **already migrated** — this is where commit `e33394f`'s "fix Hermes config" work landed) and `C:\~shit\.toilet\hermes` (gateway dead, config was still on `npx -y`). Fix 2 below was applied to the `.toilet` home, mirroring the proven AppData pattern (`type: http` + `url` for consensus/ensemble, pinned `januscope` for serena/agentmemory).
- **Fix 2 applied** to `C:\~shit\.toilet\hermes\config.yaml`. Hermes supports HTTP MCP natively: `url:` = Streamable HTTP, optional `transport: sse` (verified in `hermes-agent/tools/mcp_tool.py`). No fallback needed.
- **Fix 3 applied** to `opworkers/opencode.jsonc`: consensus/ensemble → `"type": "remote"` + URL; serena/agentmemory → pinned `januscope`.
- **Fix 4 applied** to `.codex/config.toml`: ensemble URL block added. **Follow-up 2026-07-24 (evening):** a fresh Codex session then failed with `url is not supported for stdio in mcp_servers.flossiullk-consensus`. Root cause was NOT the project file or root `.mcp.json` (the plan's guess): Codex 0.128 layers the **user-level `~/.codex/config.toml`** under the project config, and the user-level file still had all four servers as `type = "stdio"` + `npx -y` — merging the project's `url` onto a stdio identity is invalid. Two-part fix: (a) migrated the four user-level entries (consensus/ensemble → `type = "streamable_http"` + daemon URL; serena/agentmemory → pinned `januscope` stdio, agentmemory env + per-tool approval modes preserved), backup at `~/.codex/config.toml.pre-mcp-migration.bak`; (b) added the required `type = "streamable_http"` discriminator to both project-level URL entries — Codex rejects a bare `url` key without it. Verified: `codex mcp list` now loads both layers cleanly, consensus/ensemble listed under streamable_http with daemon URLs. Note: Codex's own transport vocabulary is `stdio` / `streamable_http` (confirmed from binary + working user config); the plan's "supports `url` natively, already working" claim was wrong — it had never actually loaded.
- **Fix 5 PASSED** — but the invocation documented below is wrong: `hook_bg_round.py` takes a positional `<claim_id>` (no `--claim`/`--blast-radius` flags) and is silent by design (logs to `~/.floss_agent/hook.log`). Correct procedure: submit a Local claim via `GatewayTools.submit_claim`, then `FLOSS_MODEL_BACKEND=omniroute python FLOSS/scripts/hook_bg_round.py <claim_id>`. Result: claim `019f9697-734b-7b32-bf86-b81798a9cb7c`, round completed in 10.4 s, 3/3 voters parseable with distinct rationales, no `[voter error]`, OmniRoute daemon confirmed listening on :20128. (Outcome REJECTED −0.400 because the smoke claim carried no evidence — correct procedural behavior, not a failure.)
- **`voters.py` flag check is call-time** (line ~272), so the plan's import-time concern does not apply.
- **Fix 6 not yet executed** — System-radius claim held for explicit operator go, per session agreement.

### Fix 7 (unplanned): serena was the worst spawn offender — `uvx --from git+…`

Not in the original six. The serena lens did **not** use `npx`; it used `C:/Python313/Scripts/uvx.exe --from git+https://github.com/oraios/serena` — i.e. it re-resolved a **git repository** on every single spawn, strictly worse than `npx -y`. Fixed by pinning:

```powershell
uv tool install git+https://github.com/oraios/serena   # package name is serena-agent
```

Lens now targets absolute `C:/Users/kalis/.local/bin/serena.exe start-mcp-server` (a real `.exe` launcher, so it also survives Hermes env-filtering — same class of fix as Fix 1). Verified: full JanuScope-wrapped initialize handshake returns `Serena 1.28.1`. Serena no longer auto-tracks git main — refresh deliberately with `uv tool upgrade serena-agent`.

### Fix 8 (unplanned): spec-workflow MCP removed — never used

Evidence gathered before removal:
- **0** actual `tool_use` invocations across *all* Claude Code transcripts in `~/.claude/projects/` (registration lines in Hermes logs only — the server was spawned ~62 times and called zero times, plus repeated `initial connection failed … parking` entries).
- Configured in **only** the two Hermes homes; absent from `.mcp.json`, OpenCode, and both Codex config layers.
- Already `enabled: false` in the live `AppData\Local\hermes` home.
- Functionally redundant: this repo has native spec discipline (`FLOSS/scripts/spec_gate.py`, `docs/specs/spec-registry.json`, `SDD-Master-Spec-0.22.md`).

Removed from `C:\~shit\.toilet\hermes\config.yaml` (backup: `config.yaml.pre-specworkflow-removal.bak`). The AppData home was left untouched — already disabled there, and its gateway is live (PID 29536), so editing it risks clobber on shutdown.

### Open items for operator (not changed unilaterally)

- **Duplicate serena in Claude Code.** Both root `.mcp.json` serena *and* the `serena@claude-plugins-official` plugin load per session — two full Serena+LSP instances. The plugin's bundled `.mcp.json` still uses the unpinned `uvx --from git+…` form and ships **nothing else** (no skills), so disabling the plugin loses no capability and halves serena's footprint. Root `.mcp.json` is the better copy (lensed, audited, pinned).
- **Serena is `enabled: false` in the live AppData Hermes home.** It was presumably disabled while it was slow; now that it's pinned it starts fast and may be worth re-enabling.
- **`context7` in user-level Codex config** still runs `npx -y @upstash/context7-mcp` — same spawn-storm pattern, out of scope for this migration.

## Problem

Hermes executed the OmniRoute/MCP daemon migration plan (Stages 0–3.5 in FLOSS repo) correctly but left gaps in the multi-harness config propagation. Six issues remain:

1. `agentmemory-mcp` binary not installed globally (lens points at it, command doesn't exist)
2. Hermes `config.yaml` mcp_servers section never updated (still `npx -y` everywhere)
3. OpenCode `opencode.jsonc` mcp section never updated (still `npx -y januscope@latest`)
4. Codex `.codex/config.toml` only has consensus — missing ensemble, agentmemory, serena
5. Hook-path smoke test (plan Task 3.5 Step 3) never run
6. ADR-19 consensus claim never submitted

## Fix 1: Install `agentmemory-mcp` globally (~1 min)

**Root cause:** The lens was changed from `npx -y @agentmemory/mcp` to `command: agentmemory-mcp` but the package was never installed globally. Verified: `@agentmemory/mcp@0.9.28` on npm DOES register a binary named `agentmemory-mcp`.

```powershell
npm install -g @agentmemory/mcp
agentmemory-mcp --version   # verify it runs
```

**No file changes needed** — the lens (`C:/~shit/.mcp/lenses/agentmemory.yaml`) already points at `agentmemory-mcp`. The install makes it work.

**Verify:** Start a Claude Code session → agentmemory MCP connects → `memory_recall` tool available.

---

## Fix 2: Update Hermes `config.yaml` mcp_servers (~5 min)

**File:** `C:\~shit\.toilet\hermes\config.yaml`

**Current (broken):**
```yaml
mcp_servers:
  Agent Memory:
    command: npx
    args: [-y, '@agentmemory/mcp']
    env: {AGENTMEMORY_URL: 'http://localhost:3111', AGENTMEMORY_TOOLS: all}
  serena:
    command: npx
    args: [-y, januscope@latest, --config, 'C:/~shit/.mcp/lenses/serena.yaml']
  flossiullk-consensus:
    command: npx
    args: [-y, januscope@latest, --config, 'C:/~shit/.mcp/lenses/flossiullk-consensus.yaml']
  flossiullk-reasoning-ensemble:
    command: npx
    args: [-y, januscope@latest, --config, 'C:/~shit/.mcp/lenses/flossiullk-reasoning-ensemble.yaml']
```

**Target:**
```yaml
mcp_servers:
  Agent Memory:
    command: januscope
    args: [--config, 'C:/~shit/.mcp/lenses/agentmemory.yaml']
  serena:
    command: januscope
    args: [--config, 'C:/~shit/.mcp/lenses/serena.yaml']
  flossiullk-consensus:
    url: http://127.0.0.1:7331/mcp
  flossiullk-reasoning-ensemble:
    url: http://127.0.0.1:7332/mcp
  spec workflow:
    command: npx
    args: [-y, spec-workflow-mcp@latest]
  docker:
    command: docker
    args: [mcp, gateway, run, --profile, ai_coding]
    env: {LOCALAPPDATA: 'C:\Users\kalis\AppData\Local', ProgramData: 'C:\ProgramData', ProgramFiles: 'C:\Program Files'}
```

**Notes:**
- Consensus + ensemble → HTTP URLs (daemons must be running)
- Serena + agentmemory → pinned `januscope` (not `npx -y januscope@latest`)
- `spec workflow` + `docker` left as-is (not part of the migration)
- Check whether Hermes supports `url:` directly or needs a different key (e.g. `type: remote` + `url:`). If Hermes doesn't support HTTP MCP at all, keep consensus/ensemble on januscope but pinned: `command: januscope` (not `npx -y januscope@latest`)

**Fallback if Hermes doesn't support HTTP transport:**
```yaml
  flossiullk-consensus:
    command: januscope
    args: [--config, 'C:/~shit/.mcp/lenses/flossiullk-consensus.yaml']
  flossiullk-reasoning-ensemble:
    command: januscope
    args: [--config, 'C:/~shit/.mcp/lenses/flossiullk-reasoning-ensemble.yaml']
```
This still spawns via JanuScope+stdio per session, but at least it's pinned (no `npx -y` overhead).

---

## Fix 3: Update OpenCode `opencode.jsonc` (~5 min)

**File:** `C:\~shit\opworkers\opencode.jsonc`

**Current:** All servers use `npx -y januscope@latest` with `"type": "local"`.

**Target:**
```jsonc
"mcp": {
  "flossiullk-consensus": {
    "type": "remote",
    "url": "http://127.0.0.1:7331/mcp"
  },
  "serena": {
    "command": ["januscope", "--config", "C:/~shit/.mcp/lenses/serena.yaml"],
    "type": "local"
  },
  "flossiullk-reasoning-ensemble": {
    "type": "remote",
    "url": "http://127.0.0.1:7332/mcp"
  },
  "agentmemory": {
    "command": ["januscope", "--config", "C:/~shit/.mcp/lenses/agentmemory.yaml"],
    "type": "local"
  },
  // openwork-browser, chrome, openwork-ui entries unchanged
}
```

**Notes:**
- OpenCode uses `"type": "remote"` + `"url"` for HTTP servers (confirmed: it already has `"type": "remote"` for `openwork-browser` and `chrome`)
- Pin `januscope` (drop `npx -y januscope@latest`) for local servers
- Keep `openwork-browser`, `chrome`, `openwork-ui` entries untouched

---

## Fix 4: Complete Codex `.codex/config.toml` (~2 min)

**File:** `C:\~shit\.codex\config.toml`

**Current:** Only has consensus.
```toml
[mcp_servers.flossiullk-consensus]
url = "http://127.0.0.1:7331/mcp"
```

**Target:**
```toml
[mcp_servers.flossiullk-consensus]
url = "http://127.0.0.1:7331/mcp"

[mcp_servers.flossiullk-reasoning-ensemble]
url = "http://127.0.0.1:7332/mcp"
```

**Notes:**
- Codex config.toml supports `url` natively for HTTP servers (already working for consensus)
- Do NOT add serena or agentmemory here — Codex uses its own `.agents/` config and the root `.mcp.json` for those. Adding stdio servers to config.toml risks double-spawning.
- The "stdio can't be used with a url" error is likely from Codex trying to read root `.mcp.json` and choking on the `"type": "http"` entries. Adding the servers to Codex's native config.toml should make it use its own config instead of falling through to `.mcp.json`.
- If the error persists: the root `.mcp.json` may need a Codex-compatible format. Investigate which file Codex actually reads — `.mcp.json` or `.codex/config.toml` — and whether it falls through.

---

## Fix 5: Hook-path smoke test (~5 min)

Plan Task 3.5 Step 3 required verifying that `hook_bg_round.py` works through OmniRoute (the hooks import `voters.py` in-process, not via MCP).

```powershell
$env:PYTHONPATH = "C:/~shit/FLOSS"
$env:FLOSS_MODEL_BACKEND = "omniroute"
C:\Python313\python.exe C:\~shit\FLOSS\scripts\hook_bg_round.py --claim "smoke test: hook-path omniroute verification" --blast-radius Local
```

**Pass criteria:** Round completes, 3/3 voters parseable, no `[voter error]`.

**If it fails:** The in-process import path may not pick up `FLOSS_MODEL_BACKEND` correctly. Check that `voters.py`'s flag check runs at call time, not import time.

---

## Fix 6: ADR-19 consensus claim (~5 min)

ADR-19 status says "consensus-pending." The plan (Task 4.2) required a System blast-radius claim.

```
submit_claim:
  text: "ADR-19: OmniRoute Inference Plane + MCP Daemon Migration — ratify System-radius transport-plane change. Evidence: Stages 0–3.5 implemented, 70/70 tests passing, equivalence run verified (identical weights across all 3 voters via both backends), ADR committed at 7926197."
  proposal_type: AdrChange
  blast_radius: System
```

Then `run_consensus_round` → record decision ID in ADR-19.

System threshold is 0.60. If APPROVED, update ADR-19 status from "Accepted (consensus-pending)" to "Accepted (consensus APPROVED, decision <id>)".

---

## Execution order

1. **Fix 1** (npm install) — unblocks agentmemory for all harnesses immediately
2. **Fix 4** (Codex config.toml) — unblocks Codex, smallest change
3. **Fix 5** (hook-path smoke) — validates OmniRoute before touching more configs
4. **Fix 2** (Hermes config.yaml) — requires knowing Hermes's HTTP MCP support
5. **Fix 3** (OpenCode opencode.jsonc) — straightforward once pattern is confirmed
6. **Fix 6** (ADR-19 claim) — governance cleanup, do last

Fixes 1–3 can be done from this Cowork session (file edits). Fixes 4–5 need a Claude Code or Hermes session on the Windows machine. Fix 6 needs the consensus gateway running.

---

## Verification

After all fixes:
- [ ] Start fresh sessions in each harness (Claude Code, Codex, Hermes, OpenCode)
- [ ] All four see consensus + ensemble + agentmemory tools
- [ ] No `npx` processes in Task Manager for any server except `spec-workflow` and `docker`
- [ ] `hook_bg_round.py` completes via OmniRoute
- [ ] ADR-19 has a recorded consensus decision
