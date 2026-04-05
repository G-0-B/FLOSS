# What To Do When a Task is Completed

1. **Verify tests pass** — run relevant test suite (pytest for Python, cargo test for Rust, npx vitest for Tryorama)
2. **Check for lint/format issues** — black + ruff (Python), cargo fmt + clippy (Rust)
3. **Review against spec** — ensure implementation matches JSON Schema specs in `docs/specs/`
4. **Check for removed wheel-reinvention** — don't duplicate what Holochain provides natively (DHT distribution, source chain versioning, validation callbacks)
5. **Update/Create ADR for major decisions** — include: Problem Statement, Decision, Implementation Strategy, Consequences (Positive/Negative/Neutral), Validation Criteria, Related Documents
6. **No secrets in commits** — check for OAuth tokens, API keys, .env files
7. **Commit message**: concise, explains "why", uses heredoc format
8. **Don't push to main** — use feature branches, create PR
