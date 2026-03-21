# Rose Forest — Greenfield Holochain Repo Bootstrap v0

> Start from zero. Clean, Holochain‑native. You can copy logic from prior attempts, but this is a fresh, minimal repo that **runs** and proves the loop.

_Last updated: 29 Aug 2025_

---

## 0) Quickstart

```bash
# prerequisites: rustup, cargo, node+npm, holochain CLI (hc), wasm32 target
rustup target add wasm32-unknown-unknown

# clone empty repo or mkdir new
mkdir rose_forest && cd rose_forest

# write files from this doc (or paste bootstrap.sh below and run it)

# build & pack DNA
make pack

# run a dev conductor
make run

# run smoke test (tryorama)
make test
```

---

## 1) Repo layout

```
.
├── Cargo.toml
├── rust-toolchain.toml
├── Makefile
├── README.md
├── conductor-config.yaml
├── scripts/
│   ├── pack.sh
│   └── run.sh
├── dnas/
│   └── rose_forest/
│       ├── dna.yaml
│       ├── integrity/
│       │   ├── Cargo.toml
│       │   └── src/lib.rs
│       └── coordinator/
│           ├── Cargo.toml
│           └── src/lib.rs
└── tests/
    └── tryorama/
        └── rose_forest.test.ts
```

---

## 2) Workspace `Cargo.toml`
```toml
[workspace]
members = [
  "dnas/rose_forest/integrity",
  "dnas/rose_forest/coordinator"
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

### `rust-toolchain.toml`
```toml
[toolchain]
channel = "stable"
components = ["rustfmt", "clippy"]
```

### `Makefile`
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

### `README.md`
```md
# Rose Forest (Greenfield) — Holochain Minimal Rose Stack v0

**Goal:** verifiable, peer-to-peer knowledge nodes with signed provenance, semantic sharding, and local vector search.

**MVP:** add signed text → embed → store as `RoseNode` → link to global path → discover + query.
```

---

## 3) Conductor & DNA manifests

### `conductor-config.yaml`
```yaml
environment_path: .hc
network:
  transport_pool:
    - type: webrtc
  bootstrap_service: https://bootstrap.holo.host

apps:
  - installed_app_id: rose_forest
    agent_key: ~
    dnas:
      - path: dnas/rose_forest/dna.yaml
        role_id: rose_forest
```

### `dnas/rose_forest/dna.yaml`
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

## 4) Integrity zome

### `dnas/rose_forest/integrity/Cargo.toml`
```toml
[package]
name = "rose_forest_integrity"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
hdi = "0.5" # adjust to your installed Holochain HDI
serde = { workspace = true }
serde_json = { workspace = true }
thiserror = { workspace = true }
```

### `dnas/rose_forest/integrity/src/lib.rs`
```rust
use hdi::prelude::*;
use std::collections::BTreeMap;

#[hdk_entry_helper]
#[derive(Clone)]
pub struct RoseNode {
    pub content: String,
    pub embedding: Vec<f32>,        // embedder-defined dim
    pub license: String,            // OSI id (e.g., "MIT")
    pub metadata: BTreeMap<String, String>,
}

#[hdk_entry_helper]
#[derive(Clone)]
pub struct KnowledgeEdge {
    pub from: ActionHash,
    pub to: ActionHash,
    pub relationship: String,       // "supports" | "contradicts" | "cites" | ...
    pub confidence: f32,            // 0..=1
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
    AllNodes,       // Path("rose_nodes") → RoseNode
    ShardMember,    // Path("shard.<prefix>") → RoseNode
    Edge,           // from → to
}

#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op {
        Op::StoreEntry(store) => {
            if let Entry::App(app) = store.entry {
                if let Ok(node) = RoseNode::try_from(app.clone()) {
                    let valid = matches!(node.license.as_str(), "MIT" | "Apache-2.0" | "BSD-3-Clause" | "MPL-2.0" | "CC-BY-4.0");
                    if !valid { return Ok(ValidateCallbackResult::Invalid("Non-OSI license".into())); }
                    if node.embedding.len() < 32 || node.embedding.len() > 4096 {
                        return Ok(ValidateCallbackResult::Invalid("embedding length out of bounds".into()));
                    }
                    return Ok(ValidateCallbackResult::Valid);
                }
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

---

## 5) Coordinator zome

### `dnas/rose_forest/coordinator/Cargo.toml`
```toml
[package]
name = "rose_forest_coordinator"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
hdk = "0.5"   # adjust to your installed Holochain HDK
serde = { workspace = true }
serde_json = { workspace = true }
tracing = { workspace = true }
anyhow = { workspace = true }
hex = { workspace = true }
```

### `dnas/rose_forest/coordinator/src/lib.rs`
```rust
use hdk::prelude::*;
use std::collections::BTreeMap;

pub mod integrity { pub use rose_forest_integrity::*; }

// --- Types for externs ---
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AddNodeInput { pub content: String, pub license: String, pub metadata: BTreeMap<String, String> }
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct QueryInput { pub text: String, pub k: usize }

#[hdk_extern]
pub fn init(_: ()) -> ExternResult<InitCallbackResult> { Ok(InitCallbackResult::Pass) }

// Deterministic toy embedder (replace later)
fn embed(text: &str) -> Vec<f32> {
    let h = blake3::hash(text.as_bytes());
    let mut v = vec![0.0f32; 256];
    for (i, b) in h.as_bytes().iter().enumerate() { v[i % 256] += (*b as f32) / 255.0; }
    v
}

#[hdk_extern]
pub fn add_knowledge(input: AddNodeInput) -> ExternResult<ActionHash> {
    let vec = embed(&input.content);
    let node = integrity::RoseNode { content: input.content, embedding: vec, license: input.license, metadata: input.metadata };
    let hash = create_entry(&node)?;

    // Global discovery path
    let all = Path::from("rose_nodes");
    all.ensure()?
        .and_then(|p| create_link(p.path_entry_hash()?, hash.clone(), integrity::LinkTypes::AllNodes, ()))?;

    // Semantic shard path
    let shard = shard_path_for_embedding(&node.embedding)?;
    shard.ensure()?
        .and_then(|p| create_link(p.path_entry_hash()?, hash.clone(), integrity::LinkTypes::ShardMember, ()))?;

    Ok(hash)
}

#[hdk_extern]
pub fn vector_search(input: QueryInput) -> ExternResult<Vec<(ActionHash, f32)>> {
    let q = embed(&input.text);

    // Naive: rebuild from links under global path (fast enough for v0)
    let all = Path::from("rose_nodes");
    let links = get_links(all.path_entry_hash()?, integrity::LinkTypes::AllNodes, None)?;

    let mut scored: Vec<(ActionHash, f32)> = Vec::new();
    for l in links {
        if let Some(target_hash) = l.target.into_action_hash() {
            if let Some(el) = get(target_hash.clone(), GetOptions::content())? {
                if let RecordEntry::Present(Entry::App(app)) = el.entry() {
                    if let Ok(node) = integrity::RoseNode::try_from(app.clone()) {
                        let s = cosine(&q, &node.embedding);
                        scored.push((target_hash, s));
                    }
                }
            }
        }
    }
    scored.sort_by(|a,b| b.1.partial_cmp(&a.1).unwrap());
    scored.truncate(input.k);
    Ok(scored)
}

fn shard_path_for_embedding(embedding: &[f32]) -> ExternResult<Path> {
    let bytes: Vec<u8> = embedding.iter().take(8)
        .map(|f| (f.clamp(0.0, 1.0) * 255.0) as u8)
        .collect();
    Ok(Path::from(format!("shard.{}", hex::encode(bytes))))
}

fn cosine(a: &Vec<f32>, b: &Vec<f32>) -> f32 {
    let mut dot = 0.0; let mut na = 0.0; let mut nb = 0.0;
    for (x,y) in a.iter().zip(b.iter()) { dot += x*y; na += x*x; nb += y*y; }
    if na == 0.0 || nb == 0.0 { 0.0 } else { dot / (na.sqrt()*nb.sqrt()) }
}
```

---

## 6) Scripts

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

## 7) Tryorama smoke test

### `tests/tryorama/rose_forest.test.ts`
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

> Install deps: `npm i -D @holochain/tryorama ts-node` in repo root.

---

## 8) Bootstrap script (optional convenience)

### `bootstrap.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
mkdir -p scripts dnas/rose_forest/integrity/src dnas/rose_forest/coordinator/src tests/tryorama
cat > rust-toolchain.toml <<'EOF'
[toolchain]
channel = "stable"
components = ["rustfmt", "clippy"]
EOF
cat > Cargo.toml <<'EOF'
[workspace]
members = ["dnas/rose_forest/integrity","dnas/rose_forest/coordinator"]
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
tracing-subscriber = { version = "0.3", features = ["fmt","env-filter"] }
hex = "0.4"
EOF
cat > Makefile <<'EOF'
.PHONY: fmt lint build pack run test
fmt:; cargo fmt --all
lint:; cargo clippy --all-targets --all-features -D warnings
build:; cargo build --release --target wasm32-unknown-unknown -p rose_forest_integrity -p rose_forest_coordinator
pack:; bash scripts/pack.sh
run:; bash scripts/run.sh
test:; npx ts-node tests/tryorama/rose_forest.test.ts
EOF
cat > README.md <<'EOF'
# Rose Forest (Greenfield) — Holochain Minimal Rose Stack v0
EOF
cat > conductor-config.yaml <<'EOF'
environment_path: .hc
network:
  transport_pool:
    - type: webrtc
  bootstrap_service: https://bootstrap.holo.host
apps:
  - installed_app_id: rose_forest
    agent_key: ~
    dnas:
      - path: dnas/rose_forest/dna.yaml
        role_id: rose_forest
EOF
cat > dnas/rose_forest/dna.yaml <<'EOF'
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
EOF
cat > dnas/rose_forest/integrity/Cargo.toml <<'EOF'
[package]
name = "rose_forest_integrity"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"
[lib]
crate-type = ["cdylib","rlib"]
[dependencies]
hdi = "0.5"
serde = { version = "1", features=["derive"] }
serde_json = "1"
thiserror = "1"
EOF
cat > dnas/rose_forest/integrity/src/lib.rs <<'EOF'
use hdi::prelude::*; use std::collections::BTreeMap;
#[hdk_entry_helper] #[derive(Clone)]
pub struct RoseNode{pub content:String,pub embedding:Vec<f32>,pub license:String,pub metadata:BTreeMap<String,String>}
#[hdk_entry_helper] #[derive(Clone)]
pub struct KnowledgeEdge{pub from:ActionHash,pub to:ActionHash,pub relationship:String,pub confidence:f32}
#[hdk_entry_defs]
pub enum EntryTypes{#[entry_def]RoseNode(RoseNode),#[entry_def]KnowledgeEdge(KnowledgeEdge)}
#[hdk_link_types]
pub enum LinkTypes{AllNodes,ShardMember,Edge}
#[hdk_extern]
pub fn validate(op:Op)->ExternResult<ValidateCallbackResult>{match op{Op::StoreEntry(store)=>{if let Entry::App(app)=store.entry{if let Ok(node)=RoseNode::try_from(app.clone()){let ok=matches!(node.license.as_str(),"MIT"|"Apache-2.0"|"BSD-3-Clause"|"MPL-2.0"|"CC-BY-4.0");if !ok{return Ok(ValidateCallbackResult::Invalid("Non-OSI license".into()));}if node.embedding.len()<32||node.embedding.len()>4096{return Ok(ValidateCallbackResult::Invalid("embedding length out of bounds".into()));}return Ok(ValidateCallbackResult::Valid);}if let Ok(edge)=KnowledgeEdge::try_from(app){if !(0.0..=1.0).contains(&edge.confidence){return Ok(ValidateCallbackResult::Invalid("confidence outside [0,1]".into()));}return Ok(ValidateCallbackResult::Valid);}}Ok(ValidateCallbackResult::Valid)} _=>Ok(ValidateCallbackResult::Valid)}}
EOF
cat > dnas/rose_forest/coordinator/Cargo.toml <<'EOF'
[package]
name = "rose_forest_coordinator"
version = "0.1.0"
edition = "2021"
license = "Apache-2.0"
[lib]
crate-type = ["cdylib","rlib"]
[dependencies]
hdk = "0.5"
serde = { version = "1", features=["derive"] }
serde_json = "1"
tracing = "0.1"
anyhow = "1"
hex = "0.4"
blake3 = "1"
EOF
cat > dnas/rose_forest/coordinator/src/lib.rs <<'EOF'
use hdk::prelude::*; use std::collections::BTreeMap; pub mod integrity{pub use rose_forest_integrity::*;}
#[derive(Serialize,Deserialize,Debug,Clone)] pub struct AddNodeInput{pub content:String,pub license:String,pub metadata:BTreeMap<String,String>}
#[derive(Serialize,Deserialize,Debug,Clone)] pub struct QueryInput{pub text:String,pub k:usize}
#[hdk_extern] pub fn init(_:())->ExternResult<InitCallbackResult>{Ok(InitCallbackResult::Pass)}
fn embed(s:&str)->Vec<f32>{let h=blake3::hash(s.as_bytes());let mut v=vec![0.0f32;256];for (i,b) in h.as_bytes().iter().enumerate(){v[i%256]+=(*b as f32)/255.0;}v}
#[hdk_extern] pub fn add_knowledge(input:AddNodeInput)->ExternResult<ActionHash>{let vec=embed(&input.content);let node=integrity::RoseNode{content:input.content,embedding:vec,license:input.license,metadata:input.metadata};let hash=create_entry(&node)?;let all=Path::from("rose_nodes");all.ensure()?.and_then(|p|create_link(p.path_entry_hash()?,hash.clone(),integrity::LinkTypes::AllNodes,()))?;let shard=shard_path_for_embedding(&node.embedding)?;shard.ensure()?.and_then(|p|create_link(p.path_entry_hash()?,hash.clone(),integrity::LinkTypes::ShardMember,()))?;Ok(hash)}
#[hdk_extern] pub fn vector_search(input:QueryInput)->ExternResult<Vec<(ActionHash,f32)>>{let q=embed(&input.text);let all=Path::from("rose_nodes");let links=get_links(all.path_entry_hash()?,integrity::LinkTypes::AllNodes,None)?;let mut scored=Vec::new();for l in links{if let Some(h)=l.target.into_action_hash(){if let Some(el)=get(h.clone(),GetOptions::content())?{if let RecordEntry::Present(Entry::App(app))=el.entry(){if let Ok(n)=integrity::RoseNode::try_from(app.clone()){let s=cosine(&q,&n.embedding);scored.push((h,s));}}}}}scored.sort_by(|a,b|b.1.partial_cmp(&a.1).unwrap());scored.truncate(input.k);Ok(scored)}
fn shard_path_for_embedding(e:&[f32])->ExternResult<Path>{let bytes:Vec<u8>=e.iter().take(8).map(|f|(f.clamp(0.0,1.0)*255.0) as u8).collect();Ok(Path::from(format!("shard.{}",hex::encode(bytes))))}
fn cosine(a:&Vec<f32>,b:&Vec<f32>)->f32{let(mut d,mut na,mut nb)=(0.0,0.0,0.0);for(x,y)in a.iter().zip(b.iter()){d+=x*y;na+=x*x;nb+=y*y;}if na==0.0||nb==0.0{0.0}else{d/(na.sqrt()*nb.sqrt())}}
EOF
cat > scripts/pack.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cargo build --release --target wasm32-unknown-unknown -p rose_forest_integrity -p rose_forest_coordinator
hc dna pack dnas/rose_forest -o dnas/rose_forest/rose_forest.dna
EOF
cat > scripts/run.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
hc s --piped -f conductor-config.yaml
EOF
cat > tests/tryorama/rose_forest.test.ts <<'EOF'
import { Orchestrator, Config, installApp } from "@holochain/tryorama";
const orchestrator = new Orchestrator();
orchestrator.registerScenario("add + gossip + query", async (s, t) => {
  const cfg = Config.gen();
  const [alice, bob] = await s.players([cfg, cfg]);
  const [[a]] = await alice.installAgentsHapps([installApp("rose_forest","dnas/rose_forest/rose_forest.dna")]);
  const [[b]] = await bob.installAgentsHapps([installApp("rose_forest","dnas/rose_forest/rose_forest.dna")]);
  await s.shareAllNodes([alice, bob]);
  await a.cells[0].call("rose_forest_coordinator","add_knowledge",{content:"causal inference",license:"MIT",metadata:{}});
  await s.consistency();
  const res:any = await b.cells[0].call("rose_forest_coordinator","vector_search",{text:"causal",k:3});
  t.ok(Array.isArray(res));
});
orchestrator.run();
EOF
chmod +x scripts/*.sh
echo "Done. Next: rustup target add wasm32-unknown-unknown && make pack && make run"
```

---

## 9) Porting from old attempts (copy only what helps)

- **Vector library**: If you want your previous ANN traits, add a new crate `crates/rose-vector-db/` and call it from coordinator. Keep keys as `ActionHash` (not `String`).
- **NormKernel rules**: Move any policy logic into **integrity** `validate()`; that’s globally enforced.
- **Provenance/CRDT**: **Do not** port. Holochain entries/signatures + DHT already cover them.

---

## 10) Definition of Done (v0)
- `add_knowledge` accepts text + license, stores signed entry, links to `rose_nodes` and a shard.
- Another agent gossips, can `vector_search` and retrieve the new node with top‑k cosine.
- CI (manual or GitHub Actions) can: build wasm → `hc dna pack` → run tryorama smoke.

**Trinary gate**
- **+1**: All above pass; invalid license rejected by validation.  
- **0**: Search works locally; gossip flaky (file bug).  
- **−1**: DNA fails to pack or validation isn’t enforced.

