What’s in the request/response path today

Server layer (src/server)

mod.rs: warp-based HTTP server with:

/api routes (uses JSON), /metrics (Prometheus TextEncoder), /health.

WebSocket endpoint for streaming search results (broadcast channel fan-out).

Uses tokio concurrency and Arc<RwLock> guards; captures start time, supports start/stop.

api.rs: API types and helpers:

Requests: CreateShardRequest, CreateIndexRequest, AddVectorRequest, SearchVectorsRequest.

Responses: CreateShardResponse, CreateIndexResponse, AddVectorResponse, SearchVectorsResponse.

Helpers: parse_distance_metric() (maps "euclidean"|"cosine"|"manhattan"|"hamming" to enum), convert_search_results(), and create_vector().

Metrics endpoint uses a MetricsCollector from core::metrics.

Sharding & Indexing (src/sharding)

mod.rs exposes: hilbert, manager, migration, vector_index.

vector_index.rs: the per-shard index (stores vectors + metadata; supports the distance metrics above). Provides search & stats (e.g., IndexStats). (From the API glue and naming, this is currently in-memory.)

manager.rs: ShardManager (creates shards/indices, routes add/search by Uuid).

hilbert.rs: HilbertCurve util (multi-dimensional → 1-D ordering). Has tests marked #[ignore]. Not yet clearly connected to VectorIndex routing—present but unused in the primary flow.

migration.rs: scaffold for future index/schema migrations.

Core vector/ML utilities (src/core)

vector.rs: a simple Vector type + operations; used to convert API Vec<f32> into internal vectors.

centroid.rs: centroid computation for clusters.

hierarchical.rs: early clustering utilities (Cluster and cluster_vectors) to group vectors by distance thresholds. Looks WIP; not wired into VectorIndex yet.

metrics.rs: MetricsCollector wrapper tied into Prometheus/Registry; plugged into the server.

Utilities & external hooks

src/utils/config.rs: layered JSON config with sane defaults for node/network/storage/sharding; Config::load() reads from path or falls back.

src/ipfs.rs: minimal IPFS manager with add() and get() using reqwest to an IPFS HTTP API.

src/ad4m.rs: AD4M integration stub (GraphQL client scaffolding).

src/llm.rs: LLM adapter scaffold (no concrete provider integrated).

Scaffolding / future layers

src/nerv/*: runtime/replication/synchrony/versioning scaffolds. Not on the critical path yet.

src/darwin/*: ambitious self-improvement orchestration (agents, exploration, validation, reality/ritual, consciousness metrics). These are largely conceptual/scaffold code today; not called by the server path.

dnas/value_flow: Holochain DNA and zome skeletons (structure exists; not integrated into the server/search path yet).

Data flow (operational path)

Client hits /api:

CreateShard → ShardManager creates a shard (id = Uuid).

CreateIndex → per-shard index with dimension + distance metric.

AddVector → vector + optional metadata stored in the shard’s index.

SearchVectors (HTTP or WS) → query vector → VectorIndex → top-k results mapped to API type and optionally streamed over WS.

Metrics:

/metrics exposes Prometheus counters/gauges collected via MetricsCollector.

Concurrency:

tokio runtime; broadcast channel to fan out WS search results.

Shared state behind Arc<RwLock>.

What’s implemented vs. planned

Implemented & used

HTTP/WS server, JSON API, Prometheus metrics.

Shard + in-memory index with selectable distance metrics.

Basic vector utilities; config loader; IPFS helper (callable but not on the critical search path).

Present but not wired into the hot path

Hilbert mapping (likely to inform spatial sharding later).

Hierarchical clustering and centroids (foundation for multi-level routing/HNSW-like structure).

NERV (replication/synchrony/versioning).

DARWIN (self-improvement + governance/ritual semantics).

Holochain DNA/zomes.

Notable gaps / stubs

Persistence: Index appears in-memory. No durable store enabled yet (IPFS present but not bound to index storage; Holochain DNA present but not integrated).

Hilbert → Shard routing: Utility exists; not yet connected to actual placement/routing of vectors/queries.

Clustering → ANN: Hierarchical clustering exists as utilities; there’s no wired approximate search structure (e.g., HNSW graph, IVF-PQ) in the query path yet.

NERV/DARWIN: Substantial conceptual scaffolding; not gating the server’s main operations.

Testing: Sparse; some tests are #[ignore]. Benchmarks exist (benches/vector_operations.rs, index_performance.rs), but CI is unclear here.

Error handling: API returns simple error strings; common error taxonomy and conversion (thiserror/anyhow mapping) could be tightened.

Auth/quotas/rate-limits: Not present in server routes.

0) Goals & constraints (assumptions)

Latency: interactive top-K in 10–150 ms (in-cluster); WAN queries degrade gracefully via shard prefiltering.

Scale: 10^9–10^11 vectors across many peers; heterogeneous hardware.

Consistency: eventual cluster-wide; per-ID monotonicity (no stale read after your write).

Trust: identity is agent-centric; capability-based access; encrypted payloads.

Extensibility: ANN engine pluggable (HNSW, IVF-PQ), routing pluggable (Hilbert, k-means, LSH).



Separation of planes

Data plane: Shard Services with per-shard ANN indexes + local KV; hot path for reads/writes.

Control plane: Holochain handles identity, capabilities, metadata catalog, replication sets, neighborhood discovery, re-sharding plans, audited logs.

2) Data model & consistency

Objects: {id, vector: Vec<f32>, metadata: Map, tenant, version}.

Index keys:

Coarse key via quantizer: (k-means centroid id) or Hilbert (space-filling mapping from normalized u64 coords).

Fine index: per-shard HNSW by default; plug-in options (IVF-PQ, DiskANN).

Writes: append-only WAL → local KV → ANN build queue; Lamport timestamp + author signature. Conflicts resolved with LWW+causal (monotonic per-ID).

Reads: router picks top-M shards from coarse index (centroid/LSH/Hilbert neighborhood), then parallel shard queries, aggregator merges/reranks.

3) Sharding & routing

Coarse routing (choose one; make it pluggable)

K-means centroids: maintain K global centroids in control plane; each centroid maps to a replication set (R peers). Great locality, easy re-shard.

Hilbert curve: quantize each dimension to bits_per_dim, compute Hilbert index (u64), then range-partition. Very stable keys; friendly to scans.

LSH (SimHash/Hyperplane): for very high dims, robust to variance; multiple tables increase recall.

Replication

Each shard has R replicas (e.g., R=3). Writes go to primary quorum; replicas pull WAL via gossip. Holochain coordinates who is in the set.

4) Query & write paths (step-by-step)

Query (top-K)

Normalize query vector; compute coarse key(s).

Router selects top-M shards (e.g., M=3–8) by centroid distance / Hilbert range / LSH buckets.

Stream query to shards (gRPC/QUIC). Shards:

search ANN (ef_search, ef_construction configs exposed),

return (id, score, meta) candidates.

Aggregator merges (min-heap), optional rerank (exact cosine/L2 on the raw vectors), returns K and streams partials via WS.

Write (upsert)

Assign to shard set from coarse key.

Append WAL (local); respond ACK after WAL + KV commit (fsync policy configurable).

Place ANN update into background builder (micro-batches). Ensure read-your-write via per-ID bypass cache until ANN updated.

Replicate WAL to peers; repair is automatic.

5) Persistence & durability

Local KV: RocksDB/LMDB for vectors+meta and ANN graph on disk (mmapped).

Snapshots: periodic shard snapshots to IPFS/S3; manifest stored in Holochain catalog with content hash.

Upgrades: dual-write to new index version; read-side can fan out until cut-over; background compaction cleans old.

6) Security & multi-tenancy

Identity: Holochain agent keys.

AuthZ: capability tokens (cap-grants) bound to routes (read/search/write/admin).

Isolation: tenant_id stamped into catalogs and shard placement; row-level encryption at rest (per-tenant keys).

Transport: mTLS between nodes; QUIC preferred.

7) Observability & ops

Metrics: OpenTelemetry → Prometheus. Key series: p50/p95 latency (route/shard/merge), recall@K, build lag, WAL lag, replica health.

Tracing: W3C trace context from API → router → shards → aggregator.

Health: /healthz, /readyz per shard; repair jobs visible in control plane.

Chaos: fault injection hooks (packet loss, slow disk, kill ANN thread) + invariants.

8) ANN & routing choices (pluggable)

Default: Coarse k-means (K≈1–4K) + HNSW per shard.

Alt: Hilbert for deterministic partitioning, especially when dimensionality is moderate and normalized.

Disk-heavy: IVF-PQ (FAISS-style) per shard to bound RAM.

GPU nodes: optional shard type; scheduler prefers GPU shards for large batch queries.

9) Control plane (Holochain) responsibilities

Catalog: shards, replicas, schemas, distance metrics, quantizer params, ANN versions.

Membership: node join/leave with attestations; resource offers (CPU/RAM/GPU).

Placement: compute re-shard plans; write them as entries, signed & auditable.

Governance hooks: proposals for migrations; ValueFlow/Holo-REA events (credits/usage).

Audit: append-only logs with hash chains (source-chains).

10) Testing strategy (what “done right” looks like)

Correctness: property tests for routing (query must reach shard containing golden neighbor), CRDT merge for updates/deletes.

Recall: deterministic corpora (e.g., SIFT1M, GIST) in CI; track recall@K, latency budgets.

Chaos: partition, node churn, partial data loss → recall degradation bounded; automatic repair proves invariants.

Perf: microbench ANN (HNSW params sweep), macrobench end-to-end with OpenTelemetry spans.

11) Project structure (clean, contributor-friendly)
/api        # protobuf/OpenAPI; single truth for clients
/router     # coarse index, shard selection
/shard      # shard service, ANN engines, WAL, snapshots
/engine     # ANN implementations (hnsw, ivfpq, lsh)
/control    # Holochain zomes: catalog, membership, placement, policy
/storage    # KV abstraction, snapshot backends (IPFS/S3/Fs)
/security   # caps, keys, tenant isolation, crypto utils
/ops        # metrics, tracing, health, chaos, admin tools
/cli        # admin + benchmarking
/docs       # ADRs/RFCs, architecture diagrams, runbooks

ADRs/RFCs for big changes.

Contrib tests: single make dev runs a 3-node local cluster with fake WAN.

12) Mapping from current repo → ideal (concrete next steps)

Short term (2–4 weeks)

Stabilize per-shard ANN: extract current in-mem index into /engine/hnsw with config (M, ef_search), add per-shard WAL+KV.

Coarse router v1: pick k-means; maintain centroids in control plane; implement router with top-M shard selection.

Replication v1: R=2/3 using WAL shipping; Holochain holds replica set; add repair worker.

API freeze: protobuf/OpenAPI; enable streaming search (already in WS) also via gRPC.

Observability: OTLP traces + Prometheus; expose recall/latency gauges from aggregator.

Mid term (4–10 weeks)

Hilbert plugin alongside k-means; add LSH option.

Snapshots to IPFS/S3; rolling upgrade path (dual index).

Security: cap-grants enforced at API gateway; per-tenant encryption.

Bench harness: ANN-Benchmarks-style runner in /cli.

Later

NERV: replication/synchrony/versioning hardening replaces ad-hoc WAL shipping.

DARWIN: self-tuning of ANN params, auto-recluster/re-shard under drift; decisions logged with 1/0/-1 trinary outcomes (apply/hold/reject) and justifications.

13) Trade-offs (no fairy dust)

K-means vs Hilbert: k-means adapts to data but needs recompute; Hilbert is simple, stable, slightly worse recall at shard boundary unless over-sampling M.

HNSW: great recall/latency in RAM; needs careful memory planning; for disk-heavy workloads adopt IVF-PQ or DiskANN per shard.

Holochain control plane: strong for identity/audit, but you’ll need a thin scheduler layer for placement that’s efficient; keep it deterministic and signed.

14) Minimal config knobs (exposed to operators)

K (coarse centroids); M_shards per query; R replication; M/ef_search (HNSW); wal_fsync=always|batch; snapshot_period; recall_target (router widens until met).

Bottom line

Build pluggable coarse routing + per-shard ANN with Holochain-backed control plane, add durable WAL+KV, and make observability first-class. Then layer replication, snapshots, and adaptive re-sharding. Keep governance and self-improvement (DARWIN) out of the hot path but wired through auditable decisions so it can tune the system over time without risking correctness.