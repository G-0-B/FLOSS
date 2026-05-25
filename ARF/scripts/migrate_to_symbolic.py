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
import time
import argparse
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
    committee_validations: int = 0  # New: count of committee validations used
    committee_rejections: int = 0  # New: count of committee rejections
    holochain_synced: int = 0  # New: count of items synced to Holochain

    def success_rate(self) -> float:
        """Calculate migration success rate."""
        if self.total_understandings == 0:
            return 0.0
        return self.successfully_migrated / self.total_understandings

    def committee_false_positive_rate(self) -> float:
        """Calculate estimated false positive rate based on committee rejections."""
        if self.committee_validations == 0:
            return 0.0
        return self.committee_rejections / self.committee_validations


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
    understanding_dict: Dict, memory: ConversationMemory
) -> Tuple[bool, str]:
    """
    Migrate a single understanding to symbolic-first format.

    Args:
        understanding_dict: Understanding dict to migrate
        memory: ConversationMemory instance for triple extraction

    Returns:
        (success, message) tuple
    """
    # Check if already migrated
    if "triple" in understanding_dict and understanding_dict["triple"] is not None:
        return (True, "Already migrated")

    # Extract triple from the understanding content
    content = understanding_dict.get("content", "")
    if not content:
        return (False, "No content to extract triple from")

    # Create a minimal dict for extraction
    extraction_dict = {"content": content}
    triple = memory._extract_triple(extraction_dict)
    if triple is None:
        return (False, "Could not extract triple")

    # Validate triple
    context = understanding_dict.get("context", content)
    is_valid, error_msg, committee_result = memory._validate_triple(triple, context)
    if not is_valid:
        return (False, f"Validation failed: {error_msg}")

    # Add triple to understanding
    understanding_dict["triple"] = {
        "subject": triple[0],
        "predicate": triple[1],
        "object": triple[2],
    }
    understanding_dict["validated"] = True
    understanding_dict["migration_metadata"] = {
        "migrated_at": time.time(),
        "extraction_method": "pattern_matching",
        "validation_status": "passed",
    }

    # Add committee validation result if available
    if committee_result:
        understanding_dict["migration_metadata"][
            "committee_validation"
        ] = committee_result

    return (True, "Migrated successfully")


def migrate_memory_store(
    store_path: Path,
    stats: MigrationStats,
    backend: str = "file",
    use_committee: bool = False,
    committee_use_mock: bool = True,
) -> List[Dict]:
    """
    Migrate a single memory store.

    Args:
        store_path: Path to memory store
        stats: MigrationStats to update
        backend: Target backend ('file' or 'holochain')
        use_committee: Use committee validation (default: False)
        committee_use_mock: Use mock LLM for committee (default: True)
    """
    agent_id = store_path.name
    logger.info(f"Migrating memory store for agent: {agent_id}")
    if use_committee:
        logger.info("Committee validation ENABLED")

    stats.total_agents += 1

    # Load understandings file directly (to avoid re-validation on load)
    understandings_file = store_path / "understandings.json"
    if not understandings_file.exists():
        logger.warning(f"No understandings file found for {agent_id}")
        return []

    with open(understandings_file, "r") as f:
        understandings_data = json.load(f)

    # Create a temporary memory instance for triple extraction/validation
    memory = ConversationMemory(
        agent_id=agent_id,
        storage_path=store_path,
        validate_ontology=True,
        backend=backend,
        use_committee_validation=use_committee,
        committee_use_mock=committee_use_mock,
    )

    failed_migrations = []

    for understanding_dict in understandings_data:
        stats.total_understandings += 1

        success, message = migrate_understanding(understanding_dict, memory)

        # Extra step for Holochain backend
        if success and backend == "holochain":
            if not understanding_dict.get("synced_to_holochain"):
                try:
                    # Transmit to Holochain
                    action_hash = memory.transmit(understanding_dict)

                    if action_hash:
                        understanding_dict["synced_to_holochain"] = True
                        understanding_dict["holochain_action_hash"] = action_hash
                        stats.holochain_synced += 1
                        if message == "Already migrated":
                            message = "Locally migrated, now synced to Holochain"
                            # Move from already_migrated to successfully_migrated if we just did work?
                            # Or just track holochain_synced separately.
                    else:
                        success = False
                        message = "Holochain transmission failed (returned None)"
                except Exception as e:
                    success = False
                    message = f"Holochain transmission error: {e}"
            else:
                if message == "Already migrated":
                    message = "Already migrated and synced"

        if success:
            if message in ("Already migrated", "Already migrated and synced"):
                stats.already_migrated += 1
            else:
                stats.successfully_migrated += 1
                # Track committee validations
                if "migration_metadata" in understanding_dict:
                    metadata = understanding_dict["migration_metadata"]
                    if "committee_validation" in metadata:
                        stats.committee_validations += 1
        else:
            stats.migration_failed += 1
            failed_migrations.append(
                {
                    "agent_id": agent_id,
                    "understanding": understanding_dict,
                    "error": message,
                }
            )

            if "Could not extract" in message:
                stats.no_triple_extracted += 1
            elif "Validation failed" in message:
                stats.validation_failed += 1
                # Track committee rejections
                if "Committee validation rejected" in message:
                    stats.committee_rejections += 1

    # Save migrated understandings back to file
    with open(understandings_file, "w") as f:
        json.dump(understandings_data, f, indent=2)

    logger.info(f"  Processed {len(understandings_data)} understandings")
    if stats.total_understandings > 0:
        current_rate = (
            stats.successfully_migrated + stats.already_migrated
        ) / stats.total_understandings
        logger.info(f"  Success rate: {current_rate*100:.1f}%")

    return failed_migrations


def generate_migration_report(
    stats: MigrationStats, failed: List[Dict], output_path: Path
):
    """Generate detailed migration report."""
    # Committee validation section (if used)
    committee_section = ""
    if stats.committee_validations > 0:
        fpr = stats.committee_false_positive_rate() * 100
        committee_section = f"""
## Committee Validation Metrics

- **Committee Validations**: {stats.committee_validations}
- **Committee Rejections**: {stats.committee_rejections}
- **Estimated False Positive Rate**: {fpr:.1f}%
- **Target**: <5.0%
- **Status**: {'✅ PASS' if fpr < 5.0 else '❌ FAIL'}

"""

    report = f"""
# Conversation Memory Migration Report

## Summary Statistics

- **Total Agents**: {stats.total_agents}
- **Total Understandings**: {stats.total_understandings}
- **Already Migrated**: {stats.already_migrated}
- **Successfully Migrated**: {stats.successfully_migrated}
- **Holochain Synced**: {stats.holochain_synced}
- **Migration Failed**: {stats.migration_failed}
- **Success Rate**: {stats.success_rate()*100:.1f}%

{committee_section}
## Failure Breakdown

- **No Triple Extracted**: {stats.no_triple_extracted}
- **Validation Failed**: {stats.validation_failed}

## Failed Migrations ({len(failed)})

"""

    for i, failure in enumerate(failed[:50], 1):  # Show first 50
        content = failure["understanding"].get("content", "N/A")
        if len(content) > 200:
            content = content[:200] + "..."
        report += f"""
### Failure {i}
- **Agent**: {failure['agent_id']}
- **Error**: {failure['error']}
- **Content**: {content}
---
"""

    if len(failed) > 50:
        report += (
            f"\n... and {len(failed) - 50} more failures (see JSON for full list)\n"
        )

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)

    # Write JSON with full details
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(
            {
                "stats": asdict(stats),
                "failed_migrations": failed,
            },
            f,
            indent=2,
            default=str,
        )

    logger.info(f"Report written to {output_path}")
    logger.info(f"Full data written to {json_path}")


def main():
    """Main migration entry point."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Migrate conversation memory to symbolic-first architecture"
    )
    parser.add_argument(
        "--committee",
        action="store_true",
        help="Enable committee-based LLM validation (reduces false positives)",
    )
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Use real LLM for committee validation (default: mock)",
    )
    parser.add_argument(
        "--backend",
        choices=["file", "holochain"],
        default="file",
        help="Storage backend to migrate to (default: file)",
    )
    args = parser.parse_args()

    start_time = time.time()

    logger.info("=" * 60)
    logger.info("Starting Conversation Memory Migration")
    if args.committee:
        logger.info("Committee Validation: ENABLED")
        logger.info(f"LLM Mode: {'REAL' if args.real_llm else 'MOCK'}")
    logger.info(f"Target Backend: {args.backend.upper()}")
    logger.info("=" * 60)

    stats = MigrationStats()
    all_failed = []

    # Find all memory stores
    stores = find_all_memory_stores()

    if not stores:
        logger.warning("No memory stores found. Creating test data...")
        # For testing, also check ./memory directory
        local_memory_path = Path(__file__).parent.parent / "memory"
        if local_memory_path.exists():
            stores = [d for d in local_memory_path.iterdir() if d.is_dir()]
            logger.info(
                f"Found {len(stores)} memory stores in local ./memory directory"
            )

    if not stores:
        logger.warning("No memory stores found to migrate.")
        logger.info("This is expected if running for the first time.")
        stats.total_agents = 0

    # Migrate each store
    for store_path in stores:
        try:
            failed = migrate_memory_store(
                store_path,
                stats,
                backend=args.backend,
                use_committee=args.committee,
                committee_use_mock=not args.real_llm,
            )
            all_failed.extend(failed)
        except Exception as e:
            logger.error(f"Error migrating {store_path}: {e}", exc_info=True)
            stats.migration_failed += 1

    # Generate report
    report_path = (
        Path(__file__).parent.parent / "dev" / "reports" / "migration_report.md"
    )
    generate_migration_report(stats, all_failed, report_path)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"Migration complete in {elapsed:.2f}s")
    logger.info(f"Success rate: {stats.success_rate()*100:.1f}%")

    # Calculate overall success rate including already migrated
    if stats.total_understandings > 0:
        overall_rate = (
            stats.successfully_migrated + stats.already_migrated
        ) / stats.total_understandings
        logger.info(f"Overall coverage: {overall_rate*100:.1f}%")
        target_met = overall_rate >= 0.8
    else:
        logger.info("No understandings found to migrate")
        target_met = True  # No data is not a failure

    logger.info(f"Target: ≥80% - {'✅ PASS' if target_met else '❌ FAIL'}")
    logger.info("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if target_met else 1)


if __name__ == "__main__":
    main()
