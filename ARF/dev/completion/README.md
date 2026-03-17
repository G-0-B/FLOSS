# Completion Reports Directory

This directory contains completion reports from successfully finished tasks.

## Report Format

Each task creates a completion report when finished:
- `phase{N}_task{M}.md`

See `../templates/completion_report_template.md` for the format.

## Example

```
completion/
├── phase1_task1.md
├── phase1_task2.md
├── phase1_task3.md
└── README.md
```

## Usage

The coordinator reviews these reports to verify:
- All acceptance criteria met
- Tests passing
- Ready for merge

## After Merge

Reports are archived for historical reference.
