---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---

# Verification Before Completion

## Overview

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. SCOPE: What did the run actually cover? (population, inputs, paths)
   - State the coverage with the result; if the tool does not report it, derive it or say "coverage unknown"
6. STILL TRUE: Does this hold NOW, or only when I first checked it?
7. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |
| Validator / gate / linter passed | Result plus what it covered | Unqualified pass from a tool with opt-in scope |
| "N items" / "none found" | Whole population enumerated, or the number reported as a floor | Count from one page or window of results |
| System does X at runtime | Evidence from the artifact that executes | Manifest, lockfile, schema, or plan that declares X |
| Property holds (diversity, quorum, freshness) | Re-derived now, by the function that enforced it | Inherited from admission time |
| Automated verdict is real | Inputs inspected: how many evaluators returned a result | Verdict taken at face value |

## Evidence Quality

A passing result is a claim about what the run covered. Check the scope before relying on it.

**Coverage, not just pass.** When citing a gate, linter, validator, or test run as evidence, include what it covered. An unqualified pass from a tool with opt-in scope says nothing about the population. When a validator over a corpus fails, its message does not scope the problem: re-run collecting ALL failures before saying how much is broken. When writing such a validator, report every failure alongside the examined count, so the output distinguishes "one item is bad" from "this surface is not running".

**Whole population.** A count from a paginated or windowed source is valid only if the query enumerated everything. Paginate to exhaustion, or report the number as a floor. The tell is cheap: if the source reports a total and your enumeration is smaller, you counted a slice.

**Executing artifact, not declaring artifact.** Evidence for a runtime claim must come from what executes, not what declares: manifest vs generated config, lockfile vs installed packages, schema vs stored rows, plan vs applied state. One question before reporting: if this declaration were never applied, would my evidence look any different?

**Properties decay.** Properties of a working set (diversity, quorum, exclusivity, freshness) are broken by ordinary failures during the work. Re-derive the property from the surviving state, calling the SAME function that enforced it originally. A second implementation of the same property is how two views of one system disagree.

**Absence is not zero.** Read an automated verdict's inputs before acting on it: how many evaluators returned a real result, and how many absences were recorded as values? A missing measurement is excluded from the denominator and reported as absent, never imputed as neutral, because neutral is a real position and absence is not. The tell: a result inconsistent with every individual input that exists.

**Unsatisfiable is not unmet.** When blocked on a required condition, attempt to satisfy it once and verify the attempt changed state. A request that returns success while changing nothing is the signature of an unsatisfiable requirement. That changes who owns the fix: from the person doing the work to whoever owns the configuration.

**A described limitation is not a resolved one.** Before writing "narrows but does not close", "best-effort", "advisory", or "known limitation" into a fix you are offering, ask whether the real fix is out of reach or merely less convenient. If reachable, the honest comment is a way of feeling rigorous while shipping the gap. If truly out of reach, record it in the tracker as an open item, not only in a docstring that dies when the thread resolves.

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Citing a pass without saying what it covered
- Writing "best-effort" or "known limitation" into a fix you are offering
- Reporting a count from a single page or window
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "It passed" | Passed over what? State the coverage |
| "I documented the limitation" | A description is not a resolution |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness
