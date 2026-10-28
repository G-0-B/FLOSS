---
id: project-hash-pins-need-repin-discipline
type: project
created: '2026-08-21'
status: active
applies_to:
- any-agent
source: reproduced_2026_08_21
title: A sha256 pin only holds if sweeps re-pin — one didn't, and the contract sat red
---

`tests/test_shared_orient_skill_contract.py` pins a sha256 on the reviewed evidence copy
of `skill-corpus/flossi0ullk-orient/SKILL.md`, so the skill cannot drift silently. An
edit is supposed to require a deliberate new pin.

A sweep got through anyway. The pin came from `5de8bb0` ("promote orient skill v0.3.4").
Then `e648c7a` ("rename the canonical kernel to match its version, v1.3.1 -> v1.4.0")
changed two lines of the pinned file and did not re-pin. The contract has been red on
that line ever since — verified identical at `c96b2a2`, at HEAD, and on
`feat/preservation-spine`, so it was nobody's recent regression.

**The method matters more than the fix.** Before changing the constant:

1. Diffed the pinned commit against current — exactly the two kernel-filename references,
   nothing else.
2. Confirmed `FLOSSI0ULLK_Master_Metaprompt_v1_4_0_Kernel.md` is the file that actually
   exists, so the rename was correct and the skill would otherwise point at a dead path.
3. Confirmed all eight content assertions still pass on the current file.

Only then re-pinned. **Never update a pin to make a test green without establishing what
changed and that the change was right** — that converts a drift detector into a rubber
stamp, which is worse than not having it.

Re-pin one-liner is recorded at the constant in that test file.

Related: [[project-truth-label-canon]], [[feedback-no-unauthorized-modifications]].
