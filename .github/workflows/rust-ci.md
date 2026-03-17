name: Rust CI + clippy analyze

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]
  # Once a month at 05:00 UTC on the 1st day
  schedule:
    - cron: "0 5 1 * *"
  workflow_dispatch:

env:
  CARGO_TERM_COLOR: always

jobs:
  lint:
    name: Lint (fmt + clippy)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Cache cargo registry + build
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
          restore-keys: |
            ${{ runner.os }}-cargo-

      - name: Set up Rust toolchain (stable + clippy)
        uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy

      - name: Cargo fmt (check only)
        run: |
          cargo fmt --all -- --check

      - name: Cargo clippy (deny warnings)
        run: |
          cargo clippy --all-targets --all-features -- -D warnings

  test:
    name: Test (all features)
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Cache cargo registry + build
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
          restore-keys: |
            ${{ runner.os }}-cargo-

      - name: Set up Rust toolchain (stable)
        uses: dtolnay/rust-toolchain@stable

      - name: Cargo test (all features)
        run: |
          cargo test --all-features

  clippy-sarif-analyze:
    name: Clippy SARIF analysis (advisory)
    runs-on: ubuntu-latest
    needs: lint  # ensure code at least passes fmt+clippy first

    permissions:
      contents: read
      security-events: write
      actions: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Cache cargo registry + build
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
          restore-keys: |
            ${{ runner.os }}-cargo-

      - name: Set up Rust toolchain (stable + clippy)
        uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy

      - name: Install SARIF tools
        run: |
          cargo install clippy-sarif sarif-fmt

      - name: Run rust-clippy and produce SARIF
        run: |
          cargo clippy --all-features --message-format=json \
            | clippy-sarif \
            | tee rust-clippy-results.sarif \
            | sarif-fmt
        # Advisory mode: do NOT fail the whole workflow on clippy here.
        continue-on-error: true

      - name: Upload analysis results to GitHub
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: rust-clippy-results.sarif
          wait-for-processing: true
