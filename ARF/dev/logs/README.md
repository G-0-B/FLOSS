# Logs Directory

This directory contains logs from parallel Claude Code task execution.

## Log Files

Naming convention: `phase{N}_task{M}_{type}.log`

Types:
- `progress.log` - Progress updates during execution
- `error.log` - Error messages and stack traces
- `debug.log` - Detailed debugging information

## Example

```
logs/
├── phase1_task1_progress.log
├── phase1_task2_progress.log
├── phase1_task3_progress.log
└── README.md
```

## Retention

Logs are kept for reference during development. Can be cleaned up after successful merge.
