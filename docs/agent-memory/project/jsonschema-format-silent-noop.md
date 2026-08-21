---
id: project-jsonschema-format-silent-noop
type: project
created: '2026-08-21'
status: active
applies_to:
- any-agent
source: ci_first_run_2026_08_21
title: jsonschema format validation is a silent no-op without an RFC-3339 backend
---

`jsonschema.FormatChecker()` only validates the `date-time` format when an RFC-3339
backend is installed. With bare `jsonschema`, `format: date-time` **silently accepts
anything** — no error, no warning, the checker just has no checker registered for that
format.

Found the hard way: the first run of the new `green-set` gate failed with

```
FAILED tests/test_pr38_review_cleanup.py::test_capability_schema_rejects_malformed_issued_at
Failed: DID NOT RAISE ValidationError
```

Locally `rfc3339-validator` was present transitively, so the test had always passed and
nobody saw it. A clean environment does not have it.

**What this means beyond the test:** the capability schema's `issued_at` validation only
does anything if an undeclared optional dependency happens to be installed. Any
provenance or capability check that leans on a `format` keyword has the same exposure.

Fixed for CI in `requirements-ci.txt` with `jsonschema[format-nongpl]` — `nongpl` rather
than `format` avoids the GPL-licensed `rfc3987` while still providing the RFC-3339
backend, which is the part that matters.

**Still open:** `jsonschema` is not declared in `ARF/requirements.txt` at all, despite
`scripts/` and `packages/` importing it. Runtime environments carry the same exposure.

Check with:

```python
import jsonschema
print('date-time' in jsonschema.FormatChecker().checkers)
```

Related: [[project-provenance-audit-doctor]], [[feedback-durable-provenance-required]].
