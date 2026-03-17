# Task 3.2: Port ConversationMemory to Holochain DNA

**Phase**: 3 (Integration)
**Estimated Time**: 12 hours
**Complexity**: HIGH
**Dependencies**: Phase 2 complete (ontology zome working)
**Parallelizable**: Yes (with Task 3.1)

---

## 🎯 Objective

Port the ConversationMemory Python implementation to a Holochain coordinator zome, enabling decentralized agent-centric memory storage with cryptographic provenance.

---

## 📍 Context

From INTEGRATION_MAP.md:
> "Port ConversationMemory to Holochain DNA. Enable agent-centric distributed storage. Cryptographic verification of memory provenance."

This completes the transition from centralized Python storage to decentralized Holochain DHT.

---

## ✅ Acceptance Criteria

1. **Create memory coordinator zome**
   - New Rust zome: `ARF/dnas/rose_forest/zomes/memory_coordinator/`
   - Implements transmit, recall, compose operations
   - Uses ontology_integrity zome for validation

2. **Define entry types**
   - Understanding entry (content, timestamp, agent, triple)
   - ADR (Architecture Decision Record) entry
   - MemoryComposition entry (for multi-agent composition)

3. **Implement core functions**
   - `transmit_understanding(content) -> UnderstandingHash`
   - `recall_understandings(query) -> Vec<Understanding>`
   - `compose_memories(other_agent) -> CompositionResult`
   - `get_validation_stats() -> Stats`

4. **Integrate with ontology**
   - Call ontology_integrity validation before storing
   - Only store understandings with valid triples
   - Link Understanding ↔ KnowledgeTriple

5. **Add links for queries**
   - Agent → Understandings (for recall by agent)
   - Triple → Understanding (for semantic queries)
   - ADR → Understanding (for architectural decisions)

6. **Tests**
   - Holochain scenario tests
   - Test transmit/recall cycle
   - Test validation integration
   - Test composition
   - Test DHT operations

7. **Python bridge**
   - Update ConversationMemory to optionally use Holochain backend
   - Maintain Python API compatibility

---

## 🔧 Implementation Guidance

### Step 1: Create Coordinator Zome Structure

```bash
cd /home/user/FLOSS/ARF/dnas/rose_forest/zomes
cargo new memory_coordinator --lib
cd memory_coordinator
```

Update `Cargo.toml`:
```toml
[package]
name = "memory_coordinator"
version = "0.1.0"
edition = "2021"

[dependencies]
hdk = "0.2"
serde = { version = "1.0", features = ["derive"] }
thiserror = "1.0"
ontology_integrity = { path = "../ontology_integrity" }

[lib]
crate-type = ["cdylib", "rlib"]
```

### Step 2: Define Entry Types

Create `src/lib.rs`:

```rust
use hdk::prelude::*;
use serde::{Deserialize, Serialize};
use ontology_integrity::{KnowledgeTriple, validate_triple};

/// An understanding transmitted by an agent
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Understanding {
    /// Content of the understanding
    pub content: String,

    /// Optional context
    pub context: Option<String>,

    /// Extracted knowledge triple
    pub triple: KnowledgeTriple,

    /// When this was created
    pub created_at: Timestamp,

    /// Agent who transmitted this
    pub agent: AgentPubKey,

    /// Content hash for deduplication
    pub content_hash: String,
}

/// Architecture Decision Record
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ADR {
    /// ADR identifier
    pub id: String,

    /// Title/summary
    pub title: String,

    /// Full content
    pub content: String,

    /// Status (proposed, accepted, rejected, superseded)
    pub status: String,

    /// When decided
    pub decided_at: Timestamp,

    /// Who decided
    pub decided_by: AgentPubKey,
}

/// Result of memory composition
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct MemoryComposition {
    /// Agents involved in composition
    pub agents: Vec<AgentPubKey>,

    /// Composition strategy used
    pub strategy: String,

    /// Statistics from composition
    pub stats: CompositionStats,

    /// When composed
    pub composed_at: Timestamp,
}

#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub struct CompositionStats {
    pub total_understandings: u32,
    pub new_understandings: u32,
    pub duplicate_skipped: u32,
}
```

### Step 3: Implement Transmit Function

```rust
#[hdk_extern]
pub fn transmit_understanding(input: UnderstandingInput) -> ExternResult<ActionHash> {
    // Extract triple from content
    let triple = extract_triple(&input.content)?;

    // Validate triple against ontology
    validate_triple(&triple)
        .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?;

    // Create Understanding entry
    let understanding = Understanding {
        content: input.content.clone(),
        context: input.context,
        triple: triple.clone(),
        created_at: sys_time()?,
        agent: agent_info()?.agent_latest_pubkey,
        content_hash: hash_content(&input.content),
    };

    // Commit to DHT
    let hash = create_entry(&understanding)?;

    // Create links for queries
    create_link(
        agent_info()?.agent_latest_pubkey.into(),
        hash.clone(),
        LinkTypes::AgentToUnderstanding,
        ()
    )?;

    // Link triple to understanding
    let triple_hash = create_entry(&triple)?;
    create_link(
        triple_hash,
        hash.clone(),
        LinkTypes::TripleToUnderstanding,
        ()
    )?;

    info!("Transmitted understanding with triple: {:?}", triple);

    Ok(hash)
}

#[derive(Serialize, Deserialize, Debug)]
pub struct UnderstandingInput {
    pub content: String,
    pub context: Option<String>,
}

/// Extract triple from content (simple pattern matching)
fn extract_triple(content: &str) -> ExternResult<KnowledgeTriple> {
    // Simple is_a pattern
    if let Some(captures) = regex::Regex::new(r"(\w+)\s+is\s+an?\s+(\w+)")
        .ok()
        .and_then(|re| re.captures(content))
    {
        return Ok(KnowledgeTriple {
            subject: captures[1].to_string(),
            predicate: "is_a".to_string(),
            object: captures[2].to_string(),
            confidence: 1.0,
            source: agent_info()?.agent_latest_pubkey,
            created_at: sys_time()?,
        });
    }

    // Default fallback
    Ok(KnowledgeTriple {
        subject: agent_info()?.agent_latest_pubkey.to_string(),
        predicate: "stated".to_string(),
        object: hash_content(content),
        confidence: 1.0,
        source: agent_info()?.agent_latest_pubkey,
        created_at: sys_time()?,
    })
}

fn hash_content(content: &str) -> String {
    use sha2::{Sha256, Digest};
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    format!("{:x}", hasher.finalize())
}
```

### Step 4: Implement Recall Function

```rust
#[hdk_extern]
pub fn recall_understandings(query: RecallQuery) -> ExternResult<Vec<Understanding>> {
    let mut results = vec![];

    // Query by agent
    if let Some(agent) = query.agent {
        let links = get_links(agent.into(), LinkTypes::AgentToUnderstanding, None)?;

        for link in links {
            if let Some(understanding) = get_understanding(link.target.into())? {
                // Apply filters
                if matches_query(&understanding, &query) {
                    results.push(understanding);
                }
            }
        }
    }

    // Limit results
    if let Some(limit) = query.limit {
        results.truncate(limit);
    }

    Ok(results)
}

#[derive(Serialize, Deserialize, Debug)]
pub struct RecallQuery {
    pub agent: Option<AgentPubKey>,
    pub content_contains: Option<String>,
    pub after_timestamp: Option<Timestamp>,
    pub limit: Option<usize>,
}

fn get_understanding(hash: ActionHash) -> ExternResult<Option<Understanding>> {
    let record = get(hash, GetOptions::default())?;
    match record {
        Some(rec) => Ok(rec.entry().to_app_option()?),
        None => Ok(None),
    }
}

fn matches_query(understanding: &Understanding, query: &RecallQuery) -> bool {
    if let Some(ref contains) = query.content_contains {
        if !understanding.content.contains(contains) {
            return false;
        }
    }

    if let Some(after) = query.after_timestamp {
        if understanding.created_at < after {
            return false;
        }
    }

    true
}
```

### Step 5: Implement Composition

```rust
#[hdk_extern]
pub fn compose_memories(other_agent: AgentPubKey) -> ExternResult<MemoryComposition> {
    let my_agent = agent_info()?.agent_latest_pubkey;

    // Get my understandings
    let my_understandings = recall_understandings(RecallQuery {
        agent: Some(my_agent.clone()),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    // Get other agent's understandings
    let other_understandings = recall_understandings(RecallQuery {
        agent: Some(other_agent.clone()),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    // Merge (simple: add non-duplicates)
    let mut new_count = 0;
    let mut dup_count = 0;

    for understanding in other_understandings {
        // Check if duplicate
        let is_duplicate = my_understandings.iter().any(|u|
            u.content_hash == understanding.content_hash
        );

        if !is_duplicate {
            // Import understanding
            create_entry(&understanding)?;
            new_count += 1;
        } else {
            dup_count += 1;
        }
    }

    let composition = MemoryComposition {
        agents: vec![my_agent, other_agent],
        strategy: "merge".to_string(),
        stats: CompositionStats {
            total_understandings: (my_understandings.len() + new_count) as u32,
            new_understandings: new_count as u32,
            duplicate_skipped: dup_count as u32,
        },
        composed_at: sys_time()?,
    };

    create_entry(&composition)?;

    Ok(composition)
}
```

### Step 6: Add Python Bridge

Update `ARF/conversation_memory.py`:

```python
class ConversationMemory:
    def __init__(self, agent_id, storage_path=None, backend='file'):
        """
        Initialize conversation memory.

        Args:
            agent_id: Agent identifier
            storage_path: For file backend
            backend: 'file' (default) or 'holochain'
        """
        self.backend = backend

        if backend == 'holochain':
            self.hc_client = HolochainClient()
        else:
            # File-based backend (existing code)
            ...

    def transmit(self, understanding):
        if self.backend == 'holochain':
            return self._transmit_holochain(understanding)
        else:
            return self._transmit_file(understanding)

    def _transmit_holochain(self, understanding):
        """Transmit via Holochain."""
        result = self.hc_client.call_zome(
            'memory_coordinator',
            'transmit_understanding',
            {
                'content': understanding['content'],
                'context': understanding.get('context'),
            }
        )
        return result

class HolochainClient:
    """Simple Holochain client via subprocess."""

    def call_zome(self, zome, function, payload):
        # Call hc via subprocess
        import subprocess
        result = subprocess.run(
            ['hc', 'call', zome, function, json.dumps(payload)],
            capture_output=True,
            text=True
        )
        return json.loads(result.stdout)
```

---

## 🧪 Testing Checklist

### Test 1: Holochain Scenario Test

Create `ARF/dnas/rose_forest/tests/memory_test.rs`:

```rust
#[cfg(test)]
mod tests {
    use holochain::test_utils::*;

    #[test]
    fn test_transmit_recall() {
        // Setup conductor
        let (conductor, _agent, _cell) = setup_conductor().await;

        // Transmit understanding
        let hash = conductor.call_zome(
            "memory_coordinator",
            "transmit_understanding",
            UnderstandingInput {
                content: "GPT-4 is a LLM".into(),
                context: None,
            }
        ).await;

        assert!(hash.is_ok());

        // Recall understandings
        let results = conductor.call_zome(
            "memory_coordinator",
            "recall_understandings",
            RecallQuery {
                agent: Some(agent_pub_key),
                content_contains: Some("GPT-4".into()),
                after_timestamp: None,
                limit: None,
            }
        ).await;

        assert_eq!(results.len(), 1);
    }
}
```

---

## 📝 Completion Checklist

- [ ] Memory coordinator zome created
- [ ] Entry types defined (Understanding, ADR, MemoryComposition)
- [ ] transmit_understanding implemented
- [ ] recall_understandings implemented
- [ ] compose_memories implemented
- [ ] Ontology integration working
- [ ] Links created for queries
- [ ] Holochain scenario tests pass
- [ ] Python bridge implemented
- [ ] Backward compatibility maintained
- [ ] Completion report created

---

## 🚫 Out of Scope

- ❌ Full conductor setup (use test utils)
- ❌ Production deployment
- ❌ Performance optimization
- ❌ UI for memory browsing
- ❌ Complex query language

---

## 📋 Files to Create/Modify

- `ARF/dnas/rose_forest/zomes/memory_coordinator/` (new zome)
- `ARF/dnas/rose_forest/tests/memory_test.rs` (new tests)
- `ARF/conversation_memory.py` (add Holochain backend)
- `ARF/dev/completion/phase3_task2.md` (completion report)

---

## 🎓 Success Metrics

1. ✅ Transmit/recall works via Holochain DHT
2. ✅ Validation integrated (no invalid data enters DHT)
3. ✅ Composition works across agents
4. ✅ Python API still works (backward compatible)
5. ✅ Tests pass in Holochain environment

---

**Requires Phase 2 complete! Can run in parallel with Task 3.1! 🚀**
