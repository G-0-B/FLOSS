# Rose Forest — Holochain Minimal Rose Stack (MRS) — **Holochain-Native Scaffold v0.1**

> **This replaces the prior libp2p scaffold.** Networking, provenance, and eventual consistency are delegated to **Holochain (Kitsune2 + DHT)**. Focus your code on vector/graph logic and policy.

_Last updated: 27 Aug 2025_

---

## Repo Layout (proposed)
```
.
├── Cargo.toml                     # workspace
├── rust-toolchain.toml
├── Makefile
├── README.md                      # include Endgame block
├── dnas/
│   └── rose_forest/
│       ├── dna.yaml               # DNA manifest
│       ├── integrity/
│       │   ├── Cargo.toml
│       │   └── src/lib.rs         # entries + validation (NormKernel → validate)
│       └── coordinator/
│           ├── Cargo.toml
│           └── src/lib.rs         # externs: add/query/shard; ANN index
├── crates/
│   └── rose-vector-db/            # keep: vector math/index trait
│       ├── Cargo.toml
│       └── src/lib.rs
├── conductor-config.yaml          # Kitsune2 transports, app install
├── tests/tryorama/rose_forest.test.ts   # multi-agent tests
└── scripts/
    ├── pack.sh                    # hc dna pack
    └── run.sh                     # hc launch conductor (dev)
```

> **Delete**: previous `crates/provenance`, libp2p code, and manual CRDT plumbing.  
> **Transform**: `vector-graph` → folded into zomes (entries + links); `rose-vector-db` remains a library used by the coordinator zome.

---

## Workspace `Cargo.toml`
```toml
[workspace]
members = [
  "crates/rose-vector-db",
  "dnas/rose_forest/integrity",
  "dnas/rose_forest/coordinator",
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
hex = "0.4"
```

---

## DNA Manifest `dnas/rose_forest/dna.yaml`
```yaml
manifest_version: "1"
name: rose_forest
integrity:
  zomes:
    - name: rose_forest_integrity
      bundled: ../../target/wasm32-unknown-unknown/release/rose_forest_integrity.wasm
coordinator:
  zomes:
    - name: rose_forest_coordinator
      bundled: ../../target/wasm32-unknown-unknown/release/rose_forest_coordinator.wasm
      dependencies:
        - name: rose_forest_integrity
```

---

## Integrity Zome `dnas/rose_forest/integrity/Cargo.toml`
```toml
[package]
name = "rose_forest_integrity"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
hdi = "0.5"   # adjust to your installed Holochain HDI version
serde = { workspace = true }
serde_json = { workspace = true }
thiserror = { workspace = true }
```

### Integrity Zome `src/lib.rs`
```rust
use hdi::prelude::*;
use std::collections::BTreeMap;

#[hdk_entry_helper]
#[derive(Clone)]
pub struct RoseNode {
    pub content: String,
    pub embedding: Vec<f32>,        // deterministic or declared model version elsewhere
    pub license: String,            // OSI license id (e.g., "MIT")
    pub metadata: BTreeMap<String, String>,
}

#[hdk_entry_helper]
#[derive(Clone)]
pub struct KnowledgeEdge {
    pub from: ActionHash,
    pub to: ActionHash,
    pub relationship: String,       // "supports" | "contradicts" | "cites" | ...
    pub confidence: f32,            // 0.0..=1.0
}

#[hdk_entry_defs]
pub enum EntryTypes {
    #[entry_def]
    RoseNode(RoseNode),
    #[entry_def]
    KnowledgeEdge(KnowledgeEdge),
}

#[hdk_link_types]
pub enum LinkTypes {
    Edge,           // links from -> to (edge materialization)
    ShardMember,    // agent↔shard path membership
}

// Global validation = your NormKernel v0 (license policy, basic constraints)
#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op {
        Op::StoreEntry(store) => {
            if let Entry::App(app) = store.entry {
                // Try RoseNode
                if let Ok(node) = RoseNode::try_from(app.clone()) {
                    let valid = matches!(node.license.as_str(), "MIT" | "Apache-2.0" | "BSD-3-Clause" | "MPL-2.0" | "CC-BY-4.0");
                    if !valid { return Ok(ValidateCallbackResult::Invalid("Non-OSI license".into())); }
                    // Optional: size bounds
                    if node.embedding.len() < 32 || node.embedding.len() > 4096 {
                        return Ok(ValidateCallbackResult::Invalid("embedding length out of bounds".into()));
                    }
                    return Ok(ValidateCallbackResult::Valid);
                }
                // Try KnowledgeEdge
                if let Ok(edge) = KnowledgeEdge::try_from(app) {
                    if !(0.0..=1.0).contains(&edge.confidence) {
                        return Ok(ValidateCallbackResult::Invalid("confidence outside [0,1]".into()));
                    }
                    return Ok(ValidateCallbackResult::Valid);
                }
            }
            Ok(ValidateCallbackResult::Valid)
        }
        _ => Ok(ValidateCallbackResult::Valid),
    }
}
```

> **Macro note**: If your HDK/HDI patch uses slightly different macros (`#[hdk_entry_types]`, etc.), swap accordingly. The structure remains the same.

---

## Coordinator Zome `dnas/rose_forest/coordinator/Cargo.toml`
```toml
[package]
name = "rose_forest_coordinator"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
hdk = "0.5"   # adjust to your installed Holochain HDK version
serde = { workspace = true }
serde_json = { workspace = true }
tracing = { workspace = true }
anyhow = { workspace = true }
hex = { workspace = true }
rose-vector-db = { path = "../../../crates/rose-vector-db" }
```

### Coordinator Zome `src/lib.rs`
```rust
use hdk::prelude::*;
use std::collections::BTreeMap;
use rose_vector_db::{FlatIndex, VectorIndex, DummyEmbedder, Embedder, VecF};

#[hdk_extern]
pub fn init(_: ()) -> ExternResult<InitCallbackResult> {
    Ok(InitCallbackResult::Pass)
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AddNodeInput {
    pub content: String,
    pub license: String,
    pub metadata: BTreeMap<String, String>,
}

#[hdk_extern]
pub fn add_knowledge(input: AddNodeInput) -> ExternResult<ActionHash> {
    // Embed locally (pluggable later)
    let embedder = DummyEmbedder {};
    let vec: VecF = embedder.embed(&input.content);
    let node = crate::integrity::RoseNode {
        content: input.content,
        embedding: vec.as_slice().unwrap().to_vec(),
        license: input.license,
        metadata: input.metadata,
    };

    // Create entry on source chain (integrity zome validates)
    let hash = create_entry(&node)?;

    // Optional: announce shard membership for discovery
    let path = shard_path_for_embedding(&node.embedding)?;
    create_link(
        path.path_entry_hash()?,
        hash.clone(),
        crate::integrity::LinkTypes::ShardMember,
        (),
    )?;

    Ok(hash)
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct QueryInput { pub text: String, pub k: usize }

#[hdk_extern]
pub fn vector_search(input: QueryInput) -> ExternResult<Vec<(ActionHash, f32)>> {
    let embedder = DummyEmbedder {};
    let q: VecF = embedder.embed(&input.text);

    // Naïve: rebuild index from local DHT view
    let mut index = FlatIndex::default();
    let filter = ChainQueryFilter::new().entry_type(EntryType::App(AppEntryDef {
        entry_index: EntryDefIndex(0),   // RoseNode index (keep in sync with entry order)
        zome_index: ZomeIndex(0),        // integrity zome index in DNA
        visibility: EntryVisibility::Public,
    }));
    let elements = query(filter)?;
    for el in elements {
        if let Ok(node) = crate::integrity::RoseNode::try_from(el.entry().to_app_option().unwrap().unwrap()) {
            let id = el.header_hashed().as_hash().clone();
            index.add(id.to_string(), Array1::from(node.embedding));
        }
    }
    let results = index.query(&q, input.k);
    let out = results
        .into_iter()
        .filter_map(|(id, score)| ActionHash::from_raw_32(vec_to_32(&id)).ok().map(|h| (h, score)))
        .collect();
    Ok(out)
}

fn shard_path_for_embedding(embedding: &[f32]) -> ExternResult<Path> {
    let bytes: Vec<u8> = embedding.iter().take(8).map(|f| (f.clamp(-1.0, 1.0) * 100.0) as i16)
        .flat_map(|x| x.to_le_bytes())
        .collect();
    Ok(Path::from(format!("shard.{}", hex::encode(bytes))))
}

fn vec_to_32(s: &str) -> [u8; 32] {
    // simplistic conversion from hex-ish string if you choose to store it that way later
    // TODO: wire actual ActionHash bytes instead of stringifying ids in index
    let mut out = [0u8; 32];
    let b = blake3::hash(s.as_bytes());
    out.copy_from_slice(b.as_bytes());
    out
}

// Bring integrity types into scope for serde conversions
pub mod integrity { pub use rose_forest_integrity::*; }
```

> **Note**: For performance, replace the naïve “rebuild index from query()” with:
> - Private snapshot entries for local ANN index state, or
> - A small on-agent ANN store rebuilt on `init` with incremental updates on `signal`s.

---

## Conductor Config `conductor-config.yaml`
```yaml
environment_path: .hc
network:
  transport_pool:
    - type: webrtc
  bootstrap_service: https://bootstrap.holo.host

# Install app for a single agent (dev)
apps:
  - installed_app_id: rose_forest
    agent_key: ~
    dnas:
      - path: dnas/rose_forest/dna.yaml
        role_id: rose_forest
```

---

## Scripts
### `scripts/pack.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
cargo build --release --target wasm32-unknown-unknown -p rose_forest_integrity -p rose_forest_coordinator
hc dna pack dnas/rose_forest -o dnas/rose_forest/rose_forest.dna
```

### `scripts/run.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
hc s --piped -f conductor-config.yaml
```

---

## Tryorama Test (smoke) `tests/tryorama/rose_forest.test.ts`
```ts
import { Orchestrator, Config, installApp } from "@holochain/tryorama";

const orchestrator = new Orchestrator();

orchestrator.registerScenario("add + gossip + query", async (s, t) => {
  const cfg = Config.gen();
  const [alice, bob] = await s.players([cfg, cfg]);
  const [[a]] = await alice.installAgentsHapps([installApp("rose_forest", "dnas/rose_forest/rose_forest.dna")]);
  const [[b]] = await bob.installAgentsHapps([installApp("rose_forest", "dnas/rose_forest/rose_forest.dna")]);

  await s.shareAllNodes([alice, bob]);

  const hash: any = await a.cells[0].call("rose_forest_coordinator", "add_knowledge", {
    content: "test document about causal inference",
    license: "MIT",
    metadata: {}
  });

  await s.consistency();

  const res: any = await b.cells[0].call("rose_forest_coordinator", "vector_search", { text: "causal", k: 3 });
  t.ok(Array.isArray(res));
});

orchestrator.run();
```

> Adjust imports to your tryorama version; this is a schematic.

---

## Makefile
```make
.PHONY: fmt lint build pack run test
fmt:
	cargo fmt --all

lint:
	cargo clippy --all-targets --all-features -D warnings

build:
	cargo build --release --target wasm32-unknown-unknown -p rose_forest_integrity -p rose_forest_coordinator

pack:
	bash scripts/pack.sh

run:
	bash scripts/run.sh

test:
	npx ts-node tests/tryorama/rose_forest.test.ts
```

---

## KPI Mapping (Holochain-native)
- **Provenance Coverage (PC)** → 100% (entry headers + agent keys).  
- **Reproducible Build Rate (RBR)** → deterministic WASM; `hc dna pack` CI gate.  
- **MAU Rose Nodes** → count unique agents invoking `add_knowledge` (telemetry zome or coordinator counters).  
- **Verified Reasoning Rate (VRR)** → enforce source/citation links in **integrity** validation; log denials.  
- **Offline Continuity (OC72)** → run chaos drill; measure `get` success rate across partition.

---

## Migration Checklist (1 week)
- [ ] Remove libp2p/CRDT/provenance crates; commit "switch-to-holochain".
- [ ] Add this DNA + zomes; wire `rose-vector-db` to coordinator.
- [ ] Implement `add_knowledge` / `vector_search` and shard Path creation.
- [ ] Pack DNA; run conductor; confirm two-agent gossip via tryorama.
- [ ] Add license policy to validation; test invalid license rejection.
- [ ] CI: build wasm, `hc dna pack`, and run tryorama smoke test.

---

## Notes & Trade-offs
- **Indexing**: ANN is local and fast; cross-neighborhood search composes via shards/links.
- **Privacy**: Keep sensitive content as **Private** entries if required (add a private entry type for snapshots).
- **Scaling**: For >100k agents, consider multiple DNAs by domain/topic → cross-DNA discovery via app-level registry.
- **Versioning**: Include model/version IDs in `metadata` and validate via policy.

