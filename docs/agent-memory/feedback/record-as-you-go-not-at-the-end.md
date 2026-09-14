---
id: feedback-record-as-you-go-not-at-the-end
type: feedback
created: '2026-08-21'
status: active
applies_to:
- any-agent
source: operator_check_2026_08_21
title: Record insights and invoke skills during the work, not after the operator asks
---

The operator asked, mid-session, whether insights were being written to durable memory
and whether the available skills were being used. Checked instead of asserting. The
answer was **no** on all three counts:

- **agentmemory: zero writes.** `memory_recall` on the session's own work returned
  nothing newer than 2026-07-26.
- **Work board: zero entries.** Grep for the session's own PR numbers returned empty.
  The only work-board commit pushed was an earlier entry cherry-picked forward.
- **Skills: 1 invoked out of 29 available**, and only when the operator asked a
  "what next" question. `systematic-debugging`, `brainstorming`,
  `flossi0ullk-shared-surface`, `verification-before-completion`, and
  `receiving-code-review` all plainly applied and were skipped.

Also zero consensus claims, on changes that were Module-to-System class.

**Why:** this is a verbatim repeat of the failure already documented in the work board at
A.0000000 — *"the 8-phase consolidation pass ran with 0 Skill invocations, 0 consensus
claims, 0 agentmemory writes, while making System/Substrate-class changes."* The
reminder infrastructure built after that audit did not prevent the recurrence. Producing
good work is not a defence: undocumented good work is precisely the "future selves
stumble on undocumented obtuse bs" cost the operator has named repeatedly, and quality
of output makes the omission *more* expensive, not less, because more is lost.

**How to apply:** treat recording as part of the work item, not a closing ritual.
Concretely — when a finding is reproduced, write the memory then; when a PR is pushed,
update the work board in the same push; check for an applicable skill before starting a
task, not after being asked. If a session ends without a durable write, that is a defect
in the session regardless of what shipped.

Related: [[feedback-record-high-leverage-takeaways]],
[[feedback-durable-provenance-required]], [[feedback-no-unauthorized-modifications]],
[[feedback-personal-meta-harness]].
