# Suggested Commands

## System (Windows + Git Bash)

- `ls`, `cd`, `grep`, `find` — standard Unix commands via Git Bash
- `git` — version control
- `curl` — HTTP requests
- `gh` — GitHub CLI (installed via `winget install --id GitHub.cli`, path: `/c/Program Files/GitHub CLI/gh.exe`)

## Python

```bash
cd ARF && pip install -e .
pytest                                    # All Python tests
pytest tests/test_committee_validation.py -v  # Specific test
pytest -k "memory"                       # Pattern match
python -m pytest --cov=. --cov-report=html  # Coverage
```

## Rust / Holochain (requires WSL2 + Nix)

```bash
# Enter Nix dev shell (inside WSL2)
cd ARF && nix develop
cargo test --lib                          # Rust unit tests
cargo build --release --target wasm32-unknown-unknown  # WASM build
hc dna pack workdir/dna                  # Pack DNA
hc app pack workdir/                     # Pack hApp
```

## Tryorama Integration Tests (inside WSL2 Nix shell)

```bash
cd ARF/tests/tryorama
npm install                              # Installs deps + runs postinstall fix
npx vitest run                           # Run all integration tests
npx vitest run spec_compliance.test.ts   # Specific test file
```

## Git

```bash
git status                               # Check state
git log --oneline -20                    # Recent history
git diff                                 # Unstaged changes
git fetch origin                         # Fetch remote
```

## Formatting/Linting

```bash
# Python
black .
ruff check .

# Rust (in WSL2)
cargo fmt
cargo clippy
```
