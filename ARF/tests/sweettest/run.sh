#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f Cargo.toml || ! -d dnas/rose_forest/workdir ]]; then
    echo "run from ARF root: nix develop path:. --command ./tests/sweettest/run.sh [cargo test args]" >&2
    echo "defaults to RUST_TEST_THREADS=1; set RUST_TEST_THREADS=N to override." >&2
    exit 2
fi

cargo build --workspace --locked --release --target wasm32-unknown-unknown
hc dna pack dnas/rose_forest/workdir/
RUST_TEST_THREADS="${RUST_TEST_THREADS:-1}" \
    cargo test --manifest-path tests/sweettest/Cargo.toml --locked "$@"
