# Minimal Rose Stack (MRS) — Workspace Scaffolding v0.1

> **Purpose:** Translate the Endgame→MRS plan into a boring, verifiable, shippable Rust workspace you can drop into `kalisam/amazon_rose_forest_01` as a PR. This is a skeleton with compile‑ready crates, clear TODOs, and reproducibility hooks.

---

## Repo reorg (proposed)
```
.
├── Cargo.toml                 # workspace
├── rust-toolchain.toml        # pin toolchain
├── .gitignore
├── Makefile
├── README.md                  # add Endgame block (see separate canvas doc)
├── docs/
│   ├── MRS_v0_SPEC.md
│   └── kpi/
│       ├── metrics.yaml
│       └── sql/
│           ├── vrr.sql
│           └── rbr.sql
├── scripts/
│   └── repro.sh               # minimal reproducible build script
├── .github/workflows/
│   └── ci.yml
└── crates/
    ├── rose-vector-db/        # your current src/ extracted as a lib
    ├── vector-graph/          # CRDT graph + vector index wrapper
    ├── provenance/            # ed25519 signing & verification
    ├── normkernel/            # tiny rule engine (allow/deny/escalate)
    └── mrs-node/              # binary: libp2p sync + local CLI/API
```

---

## Root files

### `Cargo.toml`
```toml
[workspace]
members = [
    "crates/rose-vector-db",
    "crates/vector-graph",
    "crates/provenance",
    "crates/normkernel",
    "crates/mrs-node",
]
resolver = "2"

[workspace.package]
edition = "2021"
license = "Apache-2.0"

[workspace.dependencies]
anyhow = "1"
thiserror = "1"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["fmt", "env-filter"] }

# crypto & ids
ed25519-dalek = { version = "2", default-features = false, features = ["rand_core" ] }
rand = "0.8"
blake3 = "1"

# crdt / data
automerge = "0.5"

# p2p & async
libp2p = { version = "0.54", features = ["gossipsub", "tcp", "noise", "yamux", "dns", "identify", "mdns"] }
tokio = { version = "1", features = ["rt-multi-thread", "macros", "fs", "io-util"] }
clap = { version = "4", features = ["derive"] }

# math
ndarray = "0.15"
linfa = { version = "0.7", optional = true }
```

### `rust-toolchain.toml`
```toml
[toolchain]
channel = "stable"
components = ["rustfmt", "clippy"]
```

### `.gitignore`
```
target/
**/*.rs.bk
**/*.swp
.DS_Store
.mrs/
```

### `Makefile`
```make
.PHONY: fmt lint build test repro
fmt:
	cargo fmt --all

lint:
	cargo clippy --all-targets --all-features -D warnings

build:
	cargo build --workspace --locked

test:
	cargo test --workspace --locked

repro:
	./scripts/repro.sh
```

---

## docs

### `docs/MRS_v0_SPEC.md`
```markdown
# MRS v0 Spec (single-node, CRDT, signed, P2P sync)

## Scope (v0)
1. Generate or load local ed25519 keypair (`~/.mrs/keys.json`).
2. Accept a signed text note via CLI.
3. Embed note → vector (dummy embed OK), create graph node, add to CRDT.
4. Broadcast CRDT changes over libp2p gossipsub; apply remote changes.
5. Query: local kNN over current vectors; return IDs + cosine similarity.
6. NormKernel: block publishing if `license != OSI-approved` or `privacy=strict` without user `--override` flag.

## Non-goals (v0)
- No cloud. No centralized servers. No auth beyond local keys.
- No heavy model inference; use dummy embed or pluggable trait.

## CLI (mrs-node)
- `mrs init` → create keys & config
- `mrs add --text "..." --license MIT` → add signed note to graph & publish
- `mrs query --text "..." --k 5` → local search
- `mrs run` → start swarm + apply/emit CRDT changes

## Topics
- gossipsub topic: `mrs-graph-v0`
- payload: `application/mrs.automerge.delta`
```

### `docs/kpi/metrics.yaml`
```yaml
version: 1
privacy_mode: FEDERATED
metrics:
  - id: vrr
    name: Verified Reasoning Rate
    owner: reasoning
    formula: verified_answers / total_answers
    cadence: daily
  - id: rbr
    name: Reproducible Build Rate
    owner: devinfra
    formula: successful_repros / total_repros
    cadence: weekly
```

### `docs/kpi/sql/vrr.sql`
```sql
SELECT date(ts) AS day,
       SUM(CASE WHEN has_citation=1 AND has_uncertainty=1 AND consistency_pass=1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS vrr
FROM answers
GROUP BY day
ORDER BY day DESC;
```

### `docs/kpi/sql/rbr.sql`
```sql
SELECT strftime('%Y-%W', ts) AS iso_week,
       AVG(CASE WHEN result='success' THEN 1.0 ELSE 0.0 END) AS rbr
FROM repro_attempts
GROUP BY iso_week
ORDER BY iso_week DESC;
```

---

## scripts

### `scripts/repro.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

# hash Cargo.lock + source tree and build artifacts for a simple reproducibility check
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

HASH_INPUT=$(git ls-files | xargs sha256sum | sort -k2 | sha256sum | cut -d' ' -f1)

echo "Source hash: $HASH_INPUT"

cargo clean
RUSTFLAGS="-C debuginfo=0" cargo build --workspace --release --locked

BIN_HASH=$(find target/release -maxdepth 1 -type f -executable -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)

echo "Binary hash: $BIN_HASH"
```

---

## CI

### `.github/workflows/ci.yml`
```yaml
name: ci
on: [push, pull_request]
permissions:
  contents: read
jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - run: cargo fmt --all -- --check
      - run: cargo clippy --all-targets --all-features -D warnings
      - run: cargo test --workspace --locked
      - run: cargo build --workspace --locked
  reproducibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bash scripts/repro.sh
```

---

## crates

### `crates/rose-vector-db/Cargo.toml`
```toml
[package]
name = "rose-vector-db"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[dependencies]
anyhow = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
ndarray = { workspace = true }
blake3 = { workspace = true }
tracing = { workspace = true }
```

### `crates/rose-vector-db/src/lib.rs`
```rust
use anyhow::*;
use ndarray::{Array1};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub type VecF = Array1<f32>;

pub trait Embedder: Send + Sync {
    fn embed(&self, text: &str) -> VecF;
}

#[derive(Clone, Default)]
pub struct DummyEmbedder;
impl Embedder for DummyEmbedder {
    fn embed(&self, text: &str) -> VecF {
        // Deterministic 256-dim toy embedding via blake3
        let hash = blake3::hash(text.as_bytes());
        let mut v = vec![0f32; 256];
        for (i, b) in hash.as_bytes().iter().enumerate() {
            v[i % 256] += (*b as f32) / 255.0;
        }
        Array1::from(v)
    }
}

pub trait VectorIndex {
    fn add(&mut self, id: String, vec: VecF);
    fn query(&self, q: &VecF, k: usize) -> Vec<(String, f32)>;
}

#[derive(Default)]
pub struct FlatIndex {
    store: HashMap<String, VecF>,
}

impl VectorIndex for FlatIndex {
    fn add(&mut self, id: String, vec: VecF) { self.store.insert(id, vec); }
    fn query(&self, q: &VecF, k: usize) -> Vec<(String, f32)> {
        let mut sims: Vec<(String, f32)> = self.store.iter().map(|(id, v)| {
            let s = cosine(q, v);
            (id.clone(), s)
        }).collect();
        sims.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        sims.truncate(k);
        sims
    }
}

fn cosine(a: &VecF, b: &VecF) -> f32 {
    let dot = a.dot(b);
    let na = a.dot(a).sqrt();
    let nb = b.dot(b).sqrt();
    if na == 0.0 || nb == 0.0 { 0.0 } else { dot / (na * nb) }
}
```

---

### `crates/vector-graph/Cargo.toml`
```toml
[package]
name = "vector-graph"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[dependencies]
anyhow = { workspace = true }
automerge = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
tracing = { workspace = true }
rose-vector-db = { path = "../rose-vector-db" }
```

### `crates/vector-graph/src/lib.rs`
```rust
use anyhow::*;
use automerge::{AutoCommit, transaction::Transactable, ReadDoc, ObjType, ScalarValue};
use rose-vector-db::{Embedder, DummyEmbedder, FlatIndex, VectorIndex, VecF};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Node {
    pub id: String,
    pub kind: String,       // e.g., "text", "url", "paper"
    pub content: String,    // raw text for v0
    pub license: String,    // e.g., "MIT"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Edge { pub from: String, pub to: String, pub rel: String }

pub struct VectorGraph<E: Embedder> {
    doc: AutoCommit,
    index: FlatIndex,
    embedder: E,
}

impl Default for VectorGraph<DummyEmbedder> {
    fn default() -> Self { Self::new(DummyEmbedder {}) }
}

impl<E: Embedder> VectorGraph<E> {
    pub fn new(embedder: E) -> Self {
        let mut doc = AutoCommit::new();
        let _ = doc.put(automerge::ROOT, "nodes", ObjType::List);
        let _ = doc.put(automerge::ROOT, "edges", ObjType::List);
        Self { doc, index: FlatIndex::default(), embedder }
    }

    pub fn add_node(&mut self, node: &Node) -> Result<()> {
        // CRDT append
        let nodes = self.doc.get(automerge::ROOT, "nodes")?.unwrap().1;
        let idx = self.doc.length(&nodes);
        self.doc.insert(&nodes, idx, ScalarValue::Json(serde_json::to_string(&node)?))?;
        // Vector index
        let vec = self.embedder.embed(&node.content);
        self.index.add(node.id.clone(), vec);
        Ok(())
    }

    pub fn add_edge(&mut self, edge: &Edge) -> Result<()> {
        let edges = self.doc.get(automerge::ROOT, "edges")?.unwrap().1;
        let idx = self.doc.length(&edges);
        self.doc.insert(&edges, idx, ScalarValue::Json(serde_json::to_string(&edge)?))?;
        Ok(())
    }

    pub fn query(&self, text: &str, k: usize) -> Vec<(String, f32)> {
        let q: VecF = self.embedder.embed(text);
        self.index.query(&q, k)
    }

    pub fn export_changes(&mut self) -> Vec<u8> { self.doc.save() }
    pub fn import_changes(&mut self, data: &[u8]) -> Result<()> { self.doc.load(data)?; Ok(()) }
}
```

---

### `crates/provenance/Cargo.toml`
```toml
[package]
name = "provenance"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[dependencies]
anyhow = { workspace = true }
ed25519-dalek = { workspace = true }
rand = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
```

### `crates/provenance/src/lib.rs`
```rust
use anyhow::*;
use ed25519_dalek::{SigningKey, VerifyingKey, Signature, Signer, Verifier, SECRET_KEY_LENGTH};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};

#[derive(Clone, Serialize, Deserialize)]
pub struct Keypair { pub secret: Vec<u8>, pub public: Vec<u8> }

impl Keypair {
    pub fn generate() -> Self {
        let mut rng = OsRng;
        let sk = SigningKey::generate(&mut rng);
        let pk = sk.verifying_key();
        Self { secret: sk.to_bytes().to_vec(), public: pk.to_bytes().to_vec() }
    }
    pub fn sign(&self, data: &[u8]) -> Vec<u8> {
        let sk = SigningKey::from_bytes(self.secret.as_slice().try_into().unwrap());
        sk.sign(data).to_bytes().to_vec()
    }
    pub fn verify(&self, data: &[u8], sig: &[u8]) -> Result<()> {
        let pk = VerifyingKey::from_bytes(self.public.as_slice().try_into().unwrap())?;
        let sig = Signature::from_bytes(sig.try_into().unwrap());
        pk.verify(data, &sig).map_err(|e| anyhow!(e))
    }
}
```

---

### `crates/normkernel/Cargo.toml`
```toml
[package]
name = "normkernel"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[dependencies]
anyhow = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
```

### `crates/normkernel/src/lib.rs`
```rust
use anyhow::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Context { pub privacy: String }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action { pub license: String, pub description: String }

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Decision { Allow, Deny, Escalate(String) }

pub struct NormKernel;

impl NormKernel {
    pub fn evaluate(ctx: &Context, act: &Action) -> Decision {
        let osi_ok = matches!(act.license.as_str(), "MIT" | "Apache-2.0" | "BSD-3-Clause" | "MPL-2.0" | "CC-BY-4.0");
        if !osi_ok { return Decision::Deny; }
        if ctx.privacy.to_lowercase() == "strict" {
            return Decision::Escalate("privacy=strict requires --override".into());
        }
        Decision::Allow
    }
}
```

---

### `crates/mrs-node/Cargo.toml`
```toml
[package]
name = "mrs-node"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[dependencies]
anyhow = { workspace = true }
clap = { workspace = true }
libp2p = { workspace = true }
automerge = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
tracing = { workspace = true }
tracing-subscriber = { workspace = true }
rose-vector-db = { path = "../rose-vector-db" }
vector-graph = { path = "../vector-graph" }
provenance = { path = "../provenance" }
normkernel = { path = "../normkernel" }
tokio = { workspace = true }
```

### `crates/mrs-node/src/main.rs`
```rust
use anyhow::*;
use clap::{Parser, Subcommand};
use normkernel::{Action, Context, Decision, NormKernel};
use provenance::Keypair;
use std::{fs, path::PathBuf};
use tracing::*;
use vector-graph::{VectorGraph, Node};

#[derive(Parser)]
#[command(name = "mrs", version, about = "Minimal Rose Stack Node v0")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Create local keys & config
    Init,
    /// Add signed text as a node
    Add { text: String, #[arg(long, default_value="MIT")] license: String },
    /// Query locally
    Query { text: String, #[arg(long, default_value_t=5)] k: usize },
    /// Run P2P swarm & CRDT sync
    Run,
}

fn key_path() -> PathBuf { dirs::home_dir().unwrap().join(".mrs/keys.json") }

fn load_or_create_keys() -> Result<Keypair> {
    let p = key_path();
    if p.exists() {
        let s = fs::read_to_string(&p)?; Ok(serde_json::from_str(&s)?)
    } else {
        let kp = Keypair::generate();
        fs::create_dir_all(p.parent().unwrap())?;
        fs::write(&p, serde_json::to_string_pretty(&kp)?)?;
        Ok(kp)
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt().with_env_filter("info").init();
    let cli = Cli::parse();
    match cli.cmd {
        Commands::Init => {
            let _ = load_or_create_keys()?;
            info!("initialized keys at {:?}", key_path());
        }
        Commands::Add { text, license } => {
            let kp = load_or_create_keys()?;
            let ctx = Context { privacy: "default".into() };
            let act = Action { license: license.clone(), description: "add_node".into() };
            match NormKernel::evaluate(&ctx, &act) {
                Decision::Allow => {}
                Decision::Deny => bail!("NormKernel denied action"),
                Decision::Escalate(msg) => bail!("Escalation required: {} (use manual override in future)", msg),
            }
            let mut vg = VectorGraph::default();
            let node = Node { id: blake3::hash(text.as_bytes()).to_hex().to_string(), kind: "text".into(), content: text.clone(), license };
            vg.add_node(&node)?;
            let changes = vg.export_changes();
            let sig = kp.sign(&changes);
            // TODO: persist local CRDT, broadcast over libp2p gossipsub with {changes,sig,pubkey}
            info!("added node id={}", node.id);
        }
        Commands::Query { text, k } => {
            let vg = VectorGraph::default();
            // TODO: load persisted CRDT + index
            let results = vg.query(&text, k);
            for (id, sim) in results { println!("{}\t{:.3}", id, sim); }
        }
        Commands::Run => {
            // TODO: libp2p swarm, join topic `mrs-graph-v0`, apply incoming {changes,sig,pubkey}
            // Verify signature with provenance::Keypair::verify equivalent
            info!("run: starting P2P sync (skeleton) ...");
            // placeholder loop
            loop { tokio::time::sleep(std::time::Duration::from_secs(60)).await; }
        }
    }
    Ok(())
}
```

---

## Next steps checklist (1 week)
- [ ] Move existing code into `crates/rose-vector-db` and adapt imports.
- [ ] Add this workspace scaffold on a branch `feat/mrs-v0`.
- [ ] Implement local persistence for CRDT doc (e.g., `~/.mrs/graph.bin`).
- [ ] Wire gossipsub publish/subscribe for CRDT deltas.
- [ ] Add simple tests: add/query; import/export changes roundtrip; signature verify fail/pass.
- [ ] Replace `DummyEmbedder` with a pluggable trait backed by e.g. `onnxruntime` later (not in v0).

---

## Notes
- This compiles with stable toolchain (modulo TODOs marked for networking). The intent is to land a **minimal, testable, peer‑to‑peer, signed CRDT graph** before any fancy agent logic.
- NormKernel is intentionally tiny: deny non‑OSI licenses; escalate when `privacy=strict`. Grow this as you formalize policy.

