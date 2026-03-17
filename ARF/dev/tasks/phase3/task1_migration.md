# Task 3.1: Vector Database Migration with Triple Linkage

**Phase**: 3 (Integration)
**Estimated Time**: 10 hours
**Complexity**: MEDIUM-HIGH
**Dependencies**: Phase 2 complete (ontology validation working)
**Parallelizable**: Yes (with Task 3.2)

---

## 🎯 Objective

Migrate existing vector embeddings to the symbolic-first architecture by extracting triples, validating them, and linking validated triples to embeddings. Target: ≥80% migration success rate.

---

## 📍 Context

From ACTION_PLAN (Week 4):
> "Audit existing vector database. For each embedding: extract content, LLM proposes triple, committee validates, link triple ↔ embedding."

This task bridges the old neural-only approach with the new neurosymbolic architecture.

---

## ✅ Acceptance Criteria

1. **Audit existing data**
   - Count total embeddings in system
   - Identify which already have triples vs. need extraction
   - Generate migration report

2. **Implement migration script**
   - Read all existing ConversationMemory instances
   - For each understanding without triple: extract triple
   - Validate extracted triple
   - Link triple to embedding
   - Track success/failure statistics

3. **Handle migration failures gracefully**
   - Log which understandings couldn't be migrated
   - Preserve original data (no destructive operations)
   - Provide manual review list for failed migrations

4. **Update data format**
   - Add `triple` field to all understanding records
   - Add `validated` flag indicating validation status
   - Add `migration_metadata` with extraction details

5. **Create migration report**
   - Total understandings processed
   - Successfully migrated count (target: ≥80%)
   - Failed migrations with reasons
   - Statistics by failure type

6. **Tests**
   - Migration script runs without errors
   - Migrated data format correct
   - Original data preserved
   - Statistics accurate
   - Coverage ≥80%

---

## 🔧 Implementation Guidance

### Step 1: Create Migration Script

Create `ARF/scripts/migrate_to_symbolic.py`:

```python
#!/usr/bin/env python3
"""
Migrate existing conversation memory to symbolic-first architecture.

This script:
1. Scans all existing ConversationMemory storage
2. Extracts triples from understandings
3. Validates triples against ontology
4. Links triples to embeddings
5. Generates migration report
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import sys

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MigrationStats:
    """Statistics for migration process."""
    total_agents: int = 0
    total_understandings: int = 0
    already_migrated: int = 0
    successfully_migrated: int = 0
    migration_failed: int = 0
    no_triple_extracted: int = 0
    validation_failed: int = 0

    def success_rate(self) -> float:
        """Calculate migration success rate."""
        if self.total_understandings == 0:
            return 0.0
        return self.successfully_migrated / self.total_understandings


def find_all_memory_stores(base_path: Path = None) -> List[Path]:
    """Find all ConversationMemory storage directories."""
    if base_path is None:
        base_path = Path.home() / ".flossi0ullk"

    if not base_path.exists():
        logger.warning(f"No memory stores found at {base_path}")
        return []

    stores = [d for d in base_path.iterdir() if d.is_dir()]
    logger.info(f"Found {len(stores)} memory stores")
    return stores


def migrate_understanding(
    understanding: Dict,
    memory: ConversationMemory
) -> Tuple[bool, str]:
    """
    Migrate a single understanding to symbolic-first format.

    Args:
        understanding: Understanding dict to migrate
        memory: ConversationMemory instance for triple extraction

    Returns:
        (success, message) tuple
    """
    # Check if already migrated
    if 'triple' in understanding and understanding['triple'] is not None:
        return (True, "Already migrated")

    # Extract triple
    triple = memory._extract_triple(understanding['understanding'])
    if triple is None:
        return (False, "Could not extract triple")

    # Validate triple
    is_valid, error_msg = memory._validate_triple(triple)
    if not is_valid:
        return (False, f"Validation failed: {error_msg}")

    # Add triple to understanding
    understanding['triple'] = {
        'subject': triple[0],
        'predicate': triple[1],
        'object': triple[2],
    }
    understanding['validated'] = True
    understanding['migration_metadata'] = {
        'migrated_at': time.time(),
        'extraction_method': 'pattern_matching',
        'validation_status': 'passed',
    }

    return (True, "Migrated successfully")


def migrate_memory_store(store_path: Path, stats: MigrationStats) -> List[Dict]:
    """
    Migrate a single memory store.

    Args:
        store_path: Path to memory store
        stats: MigrationStats to update

    Returns:
        List of failed migrations for manual review
    """
    agent_id = store_path.name
    logger.info(f"Migrating memory store for agent: {agent_id}")

    stats.total_agents += 1

    # Load memory (with validation disabled initially)
    memory = ConversationMemory(
        agent_id=agent_id,
        storage_path=store_path,
        validate_ontology=False  # Don't validate on load
    )

    failed_migrations = []

    for understanding in memory.understandings:
        stats.total_understandings += 1

        success, message = migrate_understanding(understanding, memory)

        if success:
            if message == "Already migrated":
                stats.already_migrated += 1
            else:
                stats.successfully_migrated += 1
        else:
            stats.migration_failed += 1
            failed_migrations.append({
                'agent_id': agent_id,
                'understanding': understanding,
                'error': message,
            })

            if "Could not extract" in message:
                stats.no_triple_extracted += 1
            elif "Validation failed" in message:
                stats.validation_failed += 1

    # Save migrated memory
    memory._save()

    logger.info(f"  Processed {len(memory.understandings)} understandings")
    logger.info(f"  Success rate: {stats.success_rate()*100:.1f}%")

    return failed_migrations


def generate_migration_report(stats: MigrationStats, failed: List[Dict], output_path: Path):
    """Generate detailed migration report."""
    report = f"""
# Conversation Memory Migration Report

## Summary Statistics

- **Total Agents**: {stats.total_agents}
- **Total Understandings**: {stats.total_understandings}
- **Already Migrated**: {stats.already_migrated}
- **Successfully Migrated**: {stats.successfully_migrated}
- **Migration Failed**: {stats.migration_failed}
- **Success Rate**: {stats.success_rate()*100:.1f}%

## Failure Breakdown

- **No Triple Extracted**: {stats.no_triple_extracted}
- **Validation Failed**: {stats.validation_failed}

## Failed Migrations ({len(failed)})

"""

    for i, failure in enumerate(failed[:50], 1):  # Show first 50
        report += f"""
### Failure {i}
- **Agent**: {failure['agent_id']}
- **Error**: {failure['error']}
- **Content**: {failure['understanding'].get('understanding', {}).get('content', 'N/A')[:200]}
---
"""

    if len(failed) > 50:
        report += f"\n... and {len(failed) - 50} more failures (see JSON for full list)\n"

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)

    # Write JSON with full details
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump({
            'stats': asdict(stats),
            'failed_migrations': failed,
        }, f, indent=2, default=str)

    logger.info(f"Report written to {output_path}")
    logger.info(f"Full data written to {json_path}")


def main():
    """Main migration entry point."""
    import time
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("Starting Conversation Memory Migration")
    logger.info("=" * 60)

    stats = MigrationStats()
    all_failed = []

    # Find all memory stores
    stores = find_all_memory_stores()

    # Migrate each store
    for store_path in stores:
        try:
            failed = migrate_memory_store(store_path, stats)
            all_failed.extend(failed)
        except Exception as e:
            logger.error(f"Error migrating {store_path}: {e}", exc_info=True)
            stats.migration_failed += 1

    # Generate report
    report_path = Path(__file__).parent.parent / "dev" / "reports" / "migration_report.md"
    generate_migration_report(stats, all_failed, report_path)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"Migration complete in {elapsed:.2f}s")
    logger.info(f"Success rate: {stats.success_rate()*100:.1f}%")
    logger.info(f"Target: ≥80% - {'✅ PASS' if stats.success_rate() >= 0.8 else '❌ FAIL'}")
    logger.info("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if stats.success_rate() >= 0.8 else 1)


if __name__ == "__main__":
    main()
```

### Step 2: Test Migration Script

```bash
cd /home/user/FLOSS/ARF
python scripts/migrate_to_symbolic.py
```

### Step 3: Create Rollback Capability

Create `ARF/scripts/rollback_migration.py`:

```python
#!/usr/bin/env python3
"""Rollback migration to pre-symbolic state."""

import json
import shutil
from pathlib import Path

def rollback():
    """Restore from backup."""
    backup_dir = Path.home() / ".flossi0ullk_backup"
    target_dir = Path.home() / ".flossi0ullk"

    if not backup_dir.exists():
        print("No backup found!")
        return

    if target_dir.exists():
        shutil.rmtree(target_dir)

    shutil.copytree(backup_dir, target_dir)
    print("Rollback complete")

if __name__ == "__main__":
    rollback()
```

---

## 🧪 Testing Checklist

### Test 1: Migration Script Runs
```bash
# Create test data
python -c "
from conversation_memory import ConversationMemory
m = ConversationMemory('test-agent')
m.transmit({'content': 'GPT-4 is a LLM'})
m.transmit({'content': 'Claude improves Sonnet-4'})
"

# Run migration
python ARF/scripts/migrate_to_symbolic.py

# Check report
cat ARF/dev/reports/migration_report.md
```

### Test 2: Success Rate ≥80%
```python
def test_migration_success_rate():
    # Run migration
    result = subprocess.run(['python', 'scripts/migrate_to_symbolic.py'], capture_output=True)

    # Parse report
    report_path = Path('dev/reports/migration_report.json')
    with open(report_path) as f:
        data = json.load(f)

    stats = data['stats']
    success_rate = stats['successfully_migrated'] / stats['total_understandings']

    assert success_rate >= 0.8, f"Success rate {success_rate} below 80%"
```

---

## 📝 Completion Checklist

- [ ] Migration script implemented
- [ ] Audit function finds all memory stores
- [ ] Triple extraction works for existing data
- [ ] Validation applied to extracted triples
- [ ] Migration statistics tracked
- [ ] Report generated with detailed breakdown
- [ ] Rollback script created
- [ ] ≥80% success rate achieved
- [ ] Failed migrations listed for manual review
- [ ] All tests pass
- [ ] Completion report created

---

## 🚫 Out of Scope

- ❌ LLM-based triple extraction (use patterns only)
- ❌ Automatic fixing of failed migrations
- ❌ Real-time migration (batch processing only)
- ❌ Distributed migration across multiple machines

---

## 📋 Files to Create

- `ARF/scripts/migrate_to_symbolic.py` - Main migration script
- `ARF/scripts/rollback_migration.py` - Rollback capability
- `ARF/tests/test_migration.py` - Migration tests
- `ARF/dev/reports/migration_report.md` - Generated report
- `ARF/dev/completion/phase3_task1.md` - Completion report

---

## 🎓 Success Metrics

1. ✅ **≥80% migration success rate**
2. ✅ All migrated data has valid triples
3. ✅ Original data preserved (no data loss)
4. ✅ Clear report of what failed and why
5. ✅ Rollback capability works

---

**Requires Phase 2 complete before starting! Can run in parallel with Task 3.2! 🚀**
