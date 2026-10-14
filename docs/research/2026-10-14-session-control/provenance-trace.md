# Why the consensus gate rejects every post-write claim: provenance trace

**Kind:** research note, 2026-10-14. Read-only investigation, asked for by the operator ("yes trace the provenance writers"). Nothing was changed.
**Corrects:** the guess in `reading-notes.md` ("several writers share one identity without sharing its chain head"). Several harnesses do share one identity, but that is not what breaks the gate.

## Answer

Since 2026-08-25 every claim from the post-write hook fails with `E_PROVENANCE_SEQUENCE_DISCONTINUOUS`, because the hook's identity has a fork near the very start of its chain, and the validator walks the whole ancestry.

- **The identity.** The hook signs with the machine identity `DkuYPguG98HM2nyRTGm1iSyaNhocBmlsbnkxfN89msG0` (`~/.floss_agent/identity`, key created 2026-05-24). Every harness that runs the hook shares it:

  | Harness | Packets |
  |---|---|
  | Claude Code | 140 |
  | Antigravity | 12 |
  | Codex (`codex-local`) | 5 |
  | Gemini CLI | 1 |
  | other | 2 |

  The hook config that runs it lives in `~/.claude/settings.json`, `C:/~shit/.codex/hooks.json` and `C:/~shit/.gemini/settings.json`, all pointing at `C:/~shit/FLOSS/hooks/hook_post_write.py` in the primary checkout.
- **The fork.** On 2026-05-25 (`codex-local` packets, the second day of the chain):
  - s=2 names s=0 as its prior although s=1 exists;
  - s=3 is missing;
  - s=4 and s=5 have no prior at all.
- **The validator.** Run here on the stored packets: s=0 and s=1 pass; s=2, 4, 5, 6, 7, 20, 35, 38, 41, 60, 98, 99 and the current head s=163 all fail with `E_PROVENANCE_SEQUENCE_DISCONTINUOUS`. Every later packet inherits the break through its ancestry.
- **When it started.** The hook log's first `SEQUENCE_DISCONTINUOUS` follows packet s=99, created 2026-08-25 14:50 UTC; the last claim that landed is just before it. On 2026-08-25 the validator gained stricter chain checks ("fork needs a valid occupant", "every slot occupant is kept"; commits `f929d61`, `23d8c93`, `440c70d`, `32577b8`). The hook runs the primary checkout's working tree, so the checks applied before they were committed.

The checks are right. A fork is a fork. They began enforcing a property this chain had lost three months earlier.

## Other things found on the way

None of these is what fails the gate today.

1. **93 throwaway identities in the real store.** `scripts/tests/test_hook_post_write_memory_wiring.py`:
   - It was added 2026-07-26 (`0b091fe`) and ran the real hook with a fresh temporary identity (`AGENT_DIR` pinned).
   - It did not pin `REPO_ROOT` until 2026-08-23 (`db80571`), so until then every run wrote packets into `C:/~shit/.agent-surface/provenance`, under a new identity each time.
   - The bursts (4 to 20 packets an hour, 2026-07-26 to 2026-08-23) stop when the pin landed.
   - The store is `.gitignore`d (root `.gitignore` line 87) and has no history.
2. **The backfill identity `DVpMe-BCIvQy_n4OepTmwKQ_8r-7_H-Fl0dpsCLDk5yA`** is `scripts/backfill_stabilization_provenance.py`'s own (`.agent-surface/identity/stabilization-2026-05-25`). That script passes `prior_digest=None` for every packet, so its 46 packets restart the chain each time by design (31 have no prior; 6 sequence numbers occur twice). A one-off from 2026-05-25 and 26.
3. **Three packets signed with the machine key are nowhere.** The machine chain's own state file advanced past s=36, 37 and 39 (between 2026-07-17 and 2026-07-30), but those packets are not in the store and the hook never logged them. The only non-test caller of `create_packet` that uses the machine identity is the hook, which logs every packet. Something else used the machine key in that window: a test, a script, or another checkout's hook with its own log. Unexplained. The validator reports these gaps as warnings (`E_PROVENANCE_CHAIN_GAP:36,37,39`), not errors.
4. **Other session-scoped identities** live under `C:/~shit/.agent-surface/identity/`. They follow a per-session pattern already used by hand:
   - `codex-yumeichan-alignment-2026-07-05`
   - `coevolution-continuation-2026-08-14`
   - `coevolution-harness-continuation-2026-08-15`
   - `digestion-2026-08-31`
   - `grok-computer-use-2026-08-25`
   - one more at the folder's root.

## What would fix it (for the operator to choose; nothing done)

1. **Re-anchor the hook's identity.** Move `~/.floss_agent/identity` aside (never delete it) so the next packet starts a new, clean chain under a new key. Record the old identity, the break at s=2, and why. The old chain stays verifiable as history, and new claims stop inheriting the fork. A KERI-style rotation event that links the two keys would carry continuity over formally; a plain restart is simpler and honest if recorded.
2. **One writer per chain.** Give each harness, or better each session, its own identity, delegated from one root the operator holds. One harness's bug then breaks its own chain, not every harness's. Five harnesses currently share one chain.
3. **Tests never touch the real store or the real identity.**
   - Let the hook take its output root from the environment, as it already does for `FLOSS_AGENT_DIR`.
   - Add a test that fails if any test writes under the workspace's `.agent-surface/provenance` or `~/.floss_agent/identity`.
4. **The backfill script** should chain its packets (`_AUTO_PRIOR`), or mark them as a backfill kind the gate never walks.
5. **Find out what used the machine key between 2026-07-17 and 2026-07-30**, before trusting any chain that key signs.
