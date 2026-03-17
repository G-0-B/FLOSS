# Issues Directory

This directory contains issue reports when tasks get blocked.

## Issue Format

When a Claude instance encounters a blocker:
- `phase{N}_task{M}_blocked.md`

Should include:
- What was attempted
- Why it failed
- Error messages
- Suggested next steps

## Example

```markdown
# Task 1.2 Blocked: Missing Dependency

## Problem
Cannot import sentence-transformers library.

## Error
```
ImportError: No module named 'sentence_transformers'
```

## Attempted Solutions
1. pip install sentence-transformers - Failed (network error)
2. pip install --user sentence-transformers - Failed

## Suggested Fix
Coordinator should install dependency manually or check network connection.

## Status
BLOCKED - Awaiting manual intervention
```

## Resolution

When issue is resolved, mark as `RESOLVED` and note solution.
