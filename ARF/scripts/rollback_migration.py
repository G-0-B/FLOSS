#!/usr/bin/env python3
"""
Rollback migration to pre-symbolic state.

This script restores conversation memory from backup taken before migration.
It provides a safety net in case migration causes issues.

Usage:
    python rollback_migration.py
"""

import json
import shutil
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_backup(source_dir: Path, backup_dir: Path) -> bool:
    """
    Create a backup of memory stores before migration.

    Args:
        source_dir: Directory to backup
        backup_dir: Where to store backup

    Returns:
        True if backup created successfully
    """
    try:
        if backup_dir.exists():
            logger.warning(f"Backup already exists at {backup_dir}")
            response = input("Overwrite existing backup? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Backup cancelled")
                return False
            shutil.rmtree(backup_dir)

        if source_dir.exists():
            shutil.copytree(source_dir, backup_dir)
            logger.info(f"Backup created at {backup_dir}")
            return True
        else:
            logger.warning(f"Source directory {source_dir} does not exist")
            return False
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        return False


def rollback(backup_dir: Path, target_dir: Path) -> bool:
    """
    Restore from backup.

    Args:
        backup_dir: Where backup is stored
        target_dir: Where to restore to

    Returns:
        True if rollback successful
    """
    try:
        if not backup_dir.exists():
            logger.error(f"No backup found at {backup_dir}")
            return False

        # Confirm rollback
        logger.warning(f"This will replace {target_dir} with backup from {backup_dir}")
        response = input("Continue with rollback? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Rollback cancelled")
            return False

        # Remove current directory
        if target_dir.exists():
            shutil.rmtree(target_dir)
            logger.info(f"Removed current directory: {target_dir}")

        # Restore from backup
        shutil.copytree(backup_dir, target_dir)
        logger.info(f"Restored from backup: {target_dir}")

        return True
    except Exception as e:
        logger.error(f"Error during rollback: {e}", exc_info=True)
        return False


def main():
    """Main rollback entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Backup or rollback conversation memory")
    parser.add_argument(
        'action',
        choices=['backup', 'rollback'],
        help="Action to perform"
    )
    parser.add_argument(
        '--source',
        type=Path,
        default=Path.home() / ".flossi0ullk",
        help="Source directory (default: ~/.flossi0ullk)"
    )
    parser.add_argument(
        '--backup-dir',
        type=Path,
        default=Path.home() / ".flossi0ullk_backup",
        help="Backup directory (default: ~/.flossi0ullk_backup)"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"Conversation Memory {args.action.upper()}")
    logger.info("=" * 60)

    if args.action == 'backup':
        # Also check local memory directory
        local_memory = Path(__file__).parent.parent / "memory"
        if not args.source.exists() and local_memory.exists():
            logger.info("Using local memory directory for backup")
            args.source = local_memory
            args.backup_dir = Path(__file__).parent.parent / "memory_backup"

        success = create_backup(args.source, args.backup_dir)
        if success:
            logger.info("✅ Backup completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Backup failed")
            sys.exit(1)

    elif args.action == 'rollback':
        # Check for local backup if main backup doesn't exist
        local_backup = Path(__file__).parent.parent / "memory_backup"
        if not args.backup_dir.exists() and local_backup.exists():
            logger.info("Using local memory backup")
            args.backup_dir = local_backup
            args.source = Path(__file__).parent.parent / "memory"

        success = rollback(args.backup_dir, args.source)
        if success:
            logger.info("✅ Rollback completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Rollback failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
