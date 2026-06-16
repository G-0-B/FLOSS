# What To Do When a Task is Completed

1. **Verify tests pass** — run relevant test suite (pytest for Python, cargo test for Rust, npx vitest for Tryorama)
2. **Check for lint/format issues** — black + ruff (Python), cargo fmt + clippy (Rust)
3. **Review against spec** — ensure implementation matches JSON Schema specs in `docs/specs/`
4. **Follow SDD ordering** — author spec, get spec review, write test plan, get test-plan review, write tests, then implement
5. **Check for removed wheel-reinvention** — don't duplicate what Holochain provides natively (DHT distribution, source chain versioning, validation callbacks)
6. **Update/Create ADR for major decisions** — include: Problem Statement, Decision, Implementation Strategy, Consequences (Positive/Negative/Neutral), Validation Criteria, Related Documents
7. **Clarification protocol for ambiguous specs** — return Decision [0 hold], list missing fields, and require clarification before implementation when the spec is materially ambiguous
8. **No secrets in commits** — check for OAuth tokens, API keys, .env files
9. **Commit message**: concise, explains "why", uses heredoc format
10. **Don't push to main** — use feature branches, create PR
11. **Apply Now/Later/Never filter before PR** — record the scope decision and rationale in the PR description
