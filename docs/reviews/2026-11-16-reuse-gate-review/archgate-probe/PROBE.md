# archgate probe against the real registry and tree

Run 2026-11-16 (machine clock) by Claude Fable 5.2 (self-reported), on the
operator's go-ahead. Truth status: the runs below are **Verified** (executed
on this machine, output read). The reading of them is the proposer's and is
**Specified** until a reviewer accepts it.

Why: a round-3 reviewer (Muse Spark 1.3, self-reported) probed archgate on
toy fixtures and found it can hash a record file and walk the tree, the two
things the conftest probe showed conftest cannot do. That made archgate, not
conftest, the strongest replacement, and it had been listed here as "not
evaluated". This probe repeats the test on the real registry and tree.

## Setup

- `archgate==0.50.0` from PyPI into a scratch virtualenv (Apache-2.0 per its
  package metadata). The PyPI package is a launcher: on first run it
  downloaded a 106 MB binary to `~/.archgate/bin/` and wrote
  `~/.archgate/config.json` with an install id. Both are outside the scratch
  directory. Telemetry was disabled before any check ran. The binary reports
  Bun 1.3.14 as its runtime.
- Tree: `git archive` of PR 92's branch at `6a17676`, extracted to a scratch
  directory and committed there. The repository itself was not touched.
- `archgate init` in the scratch copy added `.archgate/`, three lines to
  `.gitignore`, and editor settings under `.claude/`.
- Rules: `GATE-001-reuse-gate.rules.ts` beside this file (108 lines,
  TypeScript) and its ADR stub `GATE-001-reuse-gate.md`. Five rules port the
  gate's surface walk with exemptions, the tier-2 reviewer rule, the 120-day
  window, the LF-normalised record digest, and the two grandfathering limits.

## Runs

| Run | What | archgate | `spec_gate.py` on the same tree |
|---|---|---|---|
| 1 | Real tree, real registry | Walked 179 gated files, 0 unregistered; fired on the one tier-2 entry with a string reviewer; counted 72 grandfathered; 0.86 s wall | 180 registered, 0 missing (1 registered path is absent from this branch) |
| 2 | Four planted files: tracked, untracked, dotfile, gitignored | Caught three. **Missed the gitignored one** | Caught all four |
| 3 | Record digest on the three entries that carry a reviewer record | Digests equal to `spec_gate.record_digest`; unchanged after converting a record to CRLF; mismatch reported after tampering | same |
| 4 | Touch rule: modify a grandfathered file | Fired when uncommitted, and when committed with `--base HEAD~1`; **did not fire when committed with no `--base`** (`changedFiles` was empty) | `--changed-from HEAD~1` fired |
| 5 | `search_date` set 139 days back | Fired | Fired |
| 6 | ADR header with a misspelt `id` key | **`pass: true`, `total: 0`, exit 0** | not applicable |
| 7 | A rule that throws | `ruleErrors: 5`, exit 2 | not applicable |
| 8 | Registry file removed | exit 2 | fails closed |

## What this shows

- archgate can host every check that was ported, against the real data, in
  one command. The earlier statement that "the custom script cannot be
  removed" is false. The conftest probe answered the wrong candidate.
- What archgate supplies is the host: the runner, the file listing, the
  changed-file set, JSON and CI output. It ships no prior-art or reuse rule.
  Each check still has to be written, here in TypeScript where it is now in
  Python. `spec_gate.py` is about 950 lines, most of it rules that exist
  because an earlier version could be passed by a typo, and 91 tests pin
  them. Those rules are the custom work under either host.
- Three behaviours differ from the current gate and matter:
  1. **Run 6 is a fail-open.** A malformed ADR header makes archgate skip the
     rules and exit 0. The current gate has no equivalent way to pass by
     breaking its own configuration. A wrapper asserting `total > 0` would
     close it, which is again custom code.
  2. **Run 2:** `ctx.glob` skips gitignored files; the current gate walks
     the file system. A rule can import `node:fs` and walk by hand, which
     gives up the part of archgate being adopted.
  3. **Run 4:** the touch rule depends on the caller passing `--base`, the
     same dependency as `--changed-from`.
- Costs not present today: a 106 MB binary on every runner and workstation,
  fetched by the launcher at first run; a second language for gate logic; an
  `init` step that writes editor settings; a per-machine install id.

## What this does not show

- Only five of the gate's rule groups were ported. The probe-shape rules,
  date typing, tier typing, emergency handling, reviewer distinctness and the
  content-pinned exemption were not. Nothing found suggests they cannot be
  written; none was tried.
- archgate was not run in CI, and its source and maintenance history were
  not read. Version 0.50.0 was probed because the registry entry names it;
  the reviewer who ran the toy probe saw 0.60.1 as latest.
- Whether a rule may be prevented from importing Node modules, which would
  matter if rules were ever taken from an untrusted source.

## Reading (proposer's, not a ruling)

The honest form of the verdict is no longer "nothing else can do this". It
is a choice between two hosts for the same custom rules: the in-repo Python
script that exists, is standard-library only and is tested, or archgate,
which is maintained by someone else and brings CI annotations and a
changed-file model, at the cost of a large binary, a rewrite of working
rules, and a fail-open that needs guarding. On the ladder that is `extend`
in both cases; the question is what is being extended. The repository states
no requirement that decides it. ADR-18's "adding no new machinery" is the
nearest, and whether a third-party binary counts as new machinery is the
operator's to say.
