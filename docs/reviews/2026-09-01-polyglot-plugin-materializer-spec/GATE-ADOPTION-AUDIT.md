CONTEXT_CONTINUATION_PACKET_2026-09-01_gate-adoption-audit

Kind: Plane A recurring-defect audit (read-only measurement; nothing enforced, nothing registered).
Subject: why accepted gates in this repo do not fire, measured rather than asserted.
Author: Claude Opus 5 / Claude Code session 1af99060
Human collision node: Anthony / kalisam
Created: 2026-09-01
Truth status: [Verified] for every count and command below, reproduced on branch
feat/coordination-room at 2026-09-01. [Specified] for the diagnosis and remedies.
Consensus gateway ready: false. Consent ref: none. Nothing was changed by this audit.

THE OPERATOR'S THESIS, WHICH THIS AUDIT CONFIRMS
Stated 2026-09-01: "we have too much surface and are trying to do everything with
everything. we already have so much we keep forgetting to use them by repeatedly
remembering to use another thing we have set up."

The measurement below supports it. The correct response is NOT another reminder
surface. Every remedy in this packet either deletes a surface, moves an existing
check to a place that runs without being remembered, or does nothing.

THE MEASUREMENT
ADR-18 (Prior-Art and Reuse Gate) is Accepted, operator-approved 2026-07-16, and
genuinely implemented: scripts/spec_gate.py:206 fails closed when a registry entry
carries "tier": 1 or 2 and has no reuse block. The code is real and it works.

Its scope, measured against docs/specs/spec-registry.json:

  registered artifacts .................. 109
  carrying tier 1 ....................... 6
  carrying tier 2 ....................... 3
  carrying NO tier ...................... 100
    of which grandfathered .............. 43
    of which untiered, not grandfathered  57
  carrying a reuse block ................ 9

So the reuse gate fires on 9 of 109 registered artifacts. Eight percent. On
unregistered artifacts it fires on zero, because the registry is the thing that
carries the tier.

This is not a bug in spec_gate. Its own failure message states the rule plainly:
"an omitted tier is an exemption, not a default". The gate is fail-closed inside
its scope and its scope is opt-in. Fail-closed centre, fail-open boundary.

THE SHARPEST INSTANCE
FLOSS/docs/adr/ADR-18-prior-art-reuse-gate.md is itself registered in
spec-registry.json WITHOUT a tier. The prior-art gate is exempt from the
prior-art gate. So are ADR-13, 14, 15, 16, 17 and 19.

SECOND INSTANCE, WITH A COST
py-filelock 3.18.0 is installed at C:/Python313/Lib/site-packages/filelock/ and is
declared in no requirements file. packages/activity_log/filelock.py was
hand-written with msvcrt and fcntl branches, reviewed across roughly forty review
rounds on the PR41 lineage, and produced a documented long tail of findings.
The library was on the machine the whole time. ADR-18 exists precisely to catch
this and did not fire, because the capability was never registered with a tier.

Caveat that must travel with this instance: py-filelock is the right reuse target
for process-lifetime locks (materializer transaction, anchor publish). It is the
WRONG tool for the daemon claim, which must outlive its process — an OS lock is
released on process death by definition. Reuse verdicts here are per-surface, not
per-repo. An undifferentiated adopt would break the daemon claim.

THIRD INSTANCE, SAME SHAPE, DIFFERENT GATE
spec_gate --check currently exits 1 on this branch: two unregistered gated
artifacts (hooks/grok_pretool_st.py, hooks/grok_session_register.py) and one
stale entry (scripts/research_log.py, registered but absent). The gate is red and
work continued. A gate that is habitually red is a gate that has been demoted to
a log line.

THE GENERALISED DEFECT
Name: gates are exempt by default, so adoption decays silently while the gate
still reports green.

Three properties make it invisible:
  1. The gate is genuinely fail-closed, so running it feels like compliance.
  2. Scope is opt-in via a field (tier) whose absence is an exemption.
  3. Nothing measures coverage. The gate reports pass/fail on what it saw. It
     never reports how little it saw.

This is the same shape as project-installation-not-adoption (2026-05-19), which
already established the standing rule that installation is not adoption and that
a gate needs a logged invocation producing project value. That rule was written
about the reuse-ledger's adapter_test gate. It was never applied to our own gates.
We recorded the lesson and then exempted ourselves from it.

It is also the same shape as the fail-fast finding in the companion review packet:
one bad input aborts a run, the run reports one problem, and the reader infers a
one-file problem instead of a dead surface. In both cases the artefact under-reports
its own blindness.

REMEDIES, RANKED, ALL SUBTRACTIVE OR RELOCATING
Deliberately no new skill, no new hook surface, no new doc type. Each item either
removes surface, or adds a number to an artefact that already runs.

R1. Make spec_gate --check print coverage, not just verdict.
    One line: "reuse gate active on 9/109 registered artifacts (8%); 57 untiered
    and not grandfathered". No new tool, no new file, no new policy. Turns an
    invisible boundary into a number that appears every time the gate already
    runs. Highest value per byte in this packet.

R2. Make untiered NOT mean exempt for new entries.
    Grandfather the existing 43 explicitly (already done) and the 57 by a dated
    one-time sweep, then require tier on every entry added after that date.
    Changes the default from exempt to must-decide. No new machinery; spec_gate
    already reads the field.

R3. Give the aggregate materializers all-failures reporting.
    materialize_shared_agent_memory.py:199 is the proven case. Collect and report
    every invalid file rather than raising on the first. Same change pattern in
    each materializer that validates a corpus.

R4. Register the lock capability under ADR-18 with a tier and record the
    per-surface verdict (adopt py-filelock for process-lifetime locks; build for
    the daemon claim, with the outlives-the-process reason stated as the
    irreducible delta). Declare the dependency.

R5. Do nothing else. Specifically: do not add a skill, a reminder hook, an
    overwatch agent, or a checklist doc for any of the above. Those are the
    surface whose proliferation is the defect being fixed. ADR-18 already
    specifies its own falsifiers and retirement path; honour them.

WHAT WAS NOT DONE
No registry entry added. No tier assigned. No dependency declared. No script
modified. spec_gate is still red. All four are proposals awaiting an operator
decision, and R2 is convention-establishing so it needs explicit consent.

NEXT THREAD SHOULD
Take R1 alone if it takes only one. It is small, subtractive of ignorance rather
than additive of surface, and it makes R2 through R4 self-evidencing afterwards.
