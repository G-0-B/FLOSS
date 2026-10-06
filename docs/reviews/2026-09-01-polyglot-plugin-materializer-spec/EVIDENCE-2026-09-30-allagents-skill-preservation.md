# Evidence: does AllAgents preserve skills that changed after install?

- **Date:** 2026-09-30
- **Kind:** read-only source review. Nothing from AllAgents was installed or run.
- **Author:** Claude Sonnet 5.5, Claude Code session `9c834986-63b7-46f0-83a1-33a7c558f045`
- **Subject of the spec it bears on:**
  [`2026-09-01-polyglot-evolving-plugin-materializer-design.md`](../../superpowers/specs/2026-09-01-polyglot-evolving-plugin-materializer-design.md),
  gate row "AllAgents adapter"
- **Truth status:** ✅ Verified for the source facts and line numbers below, each
  checked against the pinned commits. ⚠️ Specified for the consequences. ❌ Blocked
  for the behavior that only a run can show (see [Limits](#limits)).
- **Requested by the operator**, 2026-09-30, after the operator's requirement
  (PR41 round 4) that no skill be overwritten if it has changed, because Hermes
  and Codex evolve skills in place.

## Answer

**No.** On every sync, AllAgents deletes each skill directory it installed on an
earlier sync and copies the skill again from its source. It never compares the
installed content with anything first, and it keeps no record that would let it.
A skill edited in place after install, or a file a harness added inside an
installed skill, is lost on the next sync. The behavior is the same in the
version the spec pins (v1.13.4) and in the current release (v1.19.0).

What survives is narrower: files and directories AllAgents never tracked. That
is the sense in which its own docstring says "preserves user-created files".

## Sources

All permalinks are immutable commit URLs. License: MIT (GitHub license API,
2026-09-30).

| Label | Git ref | Commit | Commit date (UTC) |
|---|---|---|---|
| pinned | tag `v1.13.4` | `046f26c450bc4d451c95034b4bac82bf4677419a` | 2026-07-30 06:14:05 |
| current | tag `v1.19.0`, equal to `main` when checked | `fe15473b35faa2992035b7ab7da08092a26d366b` | 2026-09-30 02:56:24 |

`v1.19.0` was committed on the day of this review. The spec recorded npm latest
as 1.13.5 on 2026-09-01, which was true then. A `v2.0.0-next.3` tag also exists
and was not read.

Files read, with the Git blob ID (verified against GitHub's own blob ID for the
same path and ref) and the SHA-256 of the copy fetched for this review:

| Ref | Path | Blob | SHA-256 of fetched copy |
|---|---|---|---|
| pinned | `src/core/sync.ts` | `24636505b4462bb6f8a092f03f7a38af9e9a10ae` | `fefb6056120f3741279fc035c66af4ce87b66c9934977e3e5466a9d0231257cc` |
| pinned | `src/core/transform.ts` | `77974d17080a0fa119a39d6511a4503a816cd5e7` | `5568315440502a2b3b10b97d36e6acdef3228cb73664f757aca5747b8696fa57` |
| pinned | `src/models/sync-state.ts` | `69dc33a7fc32f1bbdc10ff931fb484c2b7f306f3` | `b74a80e1075d2734fac2f480aa23a77cbe741a6f3817472348c323d3dd8b2e60` |
| pinned | `src/models/client-mapping.ts` | `d56b447b08a3fddbc1a61d4acbfa7beb02fc90ef` | `2ccfb5478745639ae0f908f617972f808e4da6ccc9e16b0a67a8368715a70781` |
| current | `src/core/sync.ts` | `9e5470b9567eaaaf363684d2c463525c31b9cf1d` | `9b1f5f63313108b19c16c08d40bd12e4fc01ca50c9d81b61beb7b25ad83c1726` |
| current | `src/core/transform.ts` | `398cddf5c1609d5b8f4b134add639692d35ff6b4` | `2886688683a442f9b2538a1871550a0c7677aba2262b3e620b9123c4a1550910` |
| current | `src/models/sync-state.ts` | `c547a3727f71d4cde5e0196086090eecf8239a36` | `c02d7026f36245740748afc02182a9a1ea939baf8ab92bd72fa6498c2bb2d615` |
| current | `src/models/client-mapping.ts` | `875880c3fa9c2f736c9203621f724d2aee4a1cae` | `c8cb1dcf50baa389bcde5886f50ed3a37dd8f21069cea715ceeddb20771cbb2d` |

The third-party files are not copied into this repository. The commit URLs and
blob IDs identify them exactly.

## Findings

**F1. Every tracked skill directory is deleted on every sync.**
`selectivePurgeWorkspace` runs as a step before copying. For each path recorded
by the previous sync it calls a recursive, forced `rm` on the directory.

- pinned:
  [`sync.ts` L599-L667](https://github.com/EntityProcess/allagents/blob/046f26c450bc4d451c95034b4bac82bf4677419a/src/core/sync.ts#L599-L667),
  the delete at L647
- current:
  [`sync.ts` L906-L972](https://github.com/EntityProcess/allagents/blob/fe15473b35faa2992035b7ab7da08092a26d366b/src/core/sync.ts#L906-L972),
  the delete at L952

**F2. Skills are tracked as whole directories, so any change inside one is lost.**
`collectSyncedPaths` records each installed skill as `<skillsPath><name>/`. The
source comment says the trailing slash is there "for efficient rm -rf"
([pinned `sync.ts` L983](https://github.com/EntityProcess/allagents/blob/046f26c450bc4d451c95034b4bac82bf4677419a/src/core/sync.ts#L983)).
A file added inside a tracked skill is removed with the directory.

**F3. The copy that follows is a plain recursive copy.**
`copySkills` ends in `cp(skill.sourcePath, skillDestPath, { recursive: true })`
with no comparison, no backup and no conflict handling.

- pinned:
  [`transform.ts` L444](https://github.com/EntityProcess/allagents/blob/046f26c450bc4d451c95034b4bac82bf4677419a/src/core/transform.ts#L444)
- current:
  [`transform.ts` L534](https://github.com/EntityProcess/allagents/blob/fe15473b35faa2992035b7ab7da08092a26d366b/src/core/transform.ts#L534)

**F4. It keeps no per-file or per-skill content record.**
The sync state stores the plugin's resolved Git commit and the list of synced
paths. The schema's own comment says "Per-skill content hashing was removed in
#388" because the commit already identifies the source
([pinned `models/sync-state.ts` L14](https://github.com/EntityProcess/allagents/blob/046f26c450bc4d451c95034b4bac82bf4677419a/src/models/sync-state.ts#L14),
[current L13](https://github.com/EntityProcess/allagents/blob/fe15473b35faa2992035b7ab7da08092a26d366b/src/models/sync-state.ts#L13)).
That identifies what the source was. It cannot say whether the installed copy
still matches it. Without such a record, "changed since install" cannot be
detected, so this is a design property and not an oversight to patch around.

**F5. The newer release hardens where it deletes, not what it deletes.**
v1.19.0 adds `trackedPathIsAllowed` and `assertSafeDestination` around the purge
and the copy, which stop a tracked path or a symlink from reaching outside the
write root. Neither looks at content. The "first sync with no state skips the
purge" rule is still there (`sync.ts` L913).

**F6. The first sync into an existing folder overwrites same-named files.**
With no prior state the purge is skipped, and `cp` runs into whatever is there.
Node's `fs.cp` overwrites existing files by default and keeps files that only
exist at the destination. Checked locally with a two-file fixture on Node
v26.5.1: an edited `a.txt` came back as the source's content, and the
destination-only `extra.txt` was kept. AllAgents' own runtime was not checked,
so treat this as the documented Node default confirmed in isolation.

**F7. It writes to the user-scope skill root of Hermes in the current release.**
`client-mapping.ts` at v1.19.0 L324 declares `hermes-agent` as a skills-only host
with `.hermes/skills/` at both project and user scope. The pinned v1.13.4 mapping
has no Hermes entry. Which release added it was not determined.

**F8. Source layout and install layout differ, in our favor.**
Skills may be nested below `skills/<category>/` in a plugin source
([pinned `transform.ts` L312-L324](https://github.com/EntityProcess/allagents/blob/046f26c450bc4d451c95034b4bac82bf4677419a/src/core/transform.ts#L312-L324)),
but each installs at `join(destDir, resolvedName)` (L396), which is flat. That
matches the plan to organize our source corpus by category and install flat.

## What it preserves and what it does not

| Situation | Result |
|---|---|
| File or directory AllAgents never installed, outside tracked skill directories | kept |
| Installed skill, unchanged, later resynced | replaced with identical content |
| Installed skill edited in place (for example a harness rewriting `SKILL.md`) | **lost on next sync** |
| File added inside an installed skill (for example a new `references/` file) | **lost on next sync** |
| Existing same-named folder on a first sync | source files overwrite same-named files; extra files kept (F6) |
| Skill removed from its source | deleted whether or not it had changed |

The spec's gate row asks for a projection "without clobbering unmanaged
content". Unmanaged content is the first row, and it passes. The requirement that
drove this check is the third and fourth rows, which the row's wording does not
cover and which fail.

## Consequences

⚠️ **Specified.** These are proposals until the operator accepts them.

1. AllAgents cannot be the writer for any skill root where a harness evolves its
   own skills: Hermes, Codex, or any user-scope root. Our
   `materialize_shared_skill_surface.py` already keeps such skills and reports
   them.
2. The spec's gate row is split in two, so the skill-preservation requirement has
   its own row and its own evidence. The edit is recorded in the spec's
   Amendments section, which quotes the old row.
3. Rollout step 5 of the spec tested only "unmanaged bytes". It now also requires
   a skill edited after install to survive a second sync.

## Related earlier findings

These were not changed.

- [`docs/research/reuse-ledger-seed.yaml` L2416](../../research/reuse-ledger-seed.yaml):
  "allagents itself is rejected", on a different ground: `claude-mcp.ts` writes
  the root `.mcp.json`, which collides with manifest ownership.
- [`docs/research/2026-08-12-toilet-digestion.md` L74](../../research/2026-08-12-toilet-digestion.md):
  the same MCP collision, and "ADR-18 requires ≥1 direct probe".
- [`docs/research/2026-08-29-cross-audit-learnings.md` L35](../../research/2026-08-29-cross-audit-learnings.md):
  the pinned version claim was "cited but unprobed".

The polyglot spec later lists an AllAgents adapter again. Whether that adapter is
still wanted, given a rejection on MCP ownership and a failure on skill
preservation, is an operator question this note does not settle.

## Limits

- **Not executed.** This is a reading of source at fixed commits. An install into
  an isolated temporary home, a sync, an edit of the installed skill and a
  second sync would confirm F1-F3 directly. It downloads and runs a third-party
  package, so it was not done without the operator's consent. ADR-18 counts a
  run as a probe and a reading as a search, so this note does not satisfy a probe
  requirement.
- **Only skill handling was read.** AllAgents' MCP, hook, command and agent
  projection were not reviewed here, beyond the earlier MCP-collision finding
  recorded above.
- **v2.0.0-next.3 was not read.**
- **How Hermes or Codex treat a skill directory that changes under them** was not
  tested. The finding is about what AllAgents writes.
- **Hermes support timing (F7)** was not traced to a release.

## Reproduce

Run from any directory with `gh` authenticated. Compare the printed blob IDs with
the table above.

```bash
P=046f26c450bc4d451c95034b4bac82bf4677419a
C=fe15473b35faa2992035b7ab7da08092a26d366b
for ref in $P $C; do
  for f in src/core/sync.ts src/core/transform.ts src/models/sync-state.ts src/models/client-mapping.ts; do
    echo "$ref $f $(gh api "repos/EntityProcess/allagents/contents/$f?ref=$ref" --jq .sha)"
  done
done
```

To read the lines in F1 and F3:

```bash
gh api "repos/EntityProcess/allagents/contents/src/core/sync.ts?ref=$C" --jq .content | base64 -d | sed -n '906,970p'
```
