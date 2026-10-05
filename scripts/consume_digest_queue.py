#!/usr/bin/env python3
import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
EVENT_ROOT = REPO_ROOT.parent / ".agent-surface" / "events"
DIGEST_OUTPUT_DIR = REPO_ROOT.parent / ".agent-surface" / "knowledge_log" / "digests"

def main() -> int:
    processed_dir = EVENT_ROOT / "processed"
    if not processed_dir.exists():
        logger.info(f"No processed events dir: {processed_dir}")
        return 0

    DIGEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    events_to_digest = []
    for filepath in sorted(processed_dir.glob("*.json"), reverse=True):
        try:
            event = json.loads(filepath.read_text(encoding="utf-8"))
            actions = event.get("recommended_actions", [])
            abs_path = event.get("abs_path")
            
            if "digest_artifact" in actions and abs_path and Path(abs_path).exists():
                # Check if already digested
                event_id = event.get("event_id", filepath.stem)
                digest_file = DIGEST_OUTPUT_DIR / f"{event_id}_digest.json"
                if not digest_file.exists():
                    events_to_digest.append((event, filepath, digest_file))
        except Exception as e:
            logger.warning(f"Error reading {filepath}: {e}")
            continue

    if not events_to_digest:
        logger.info("No new artifacts to digest.")
        return 0

    # Process up to 3 artifacts per heartbeat tick to prevent unbounded load
    processed_count = 0
    for event, event_filepath, digest_file in events_to_digest[:3]:
        abs_path = event["abs_path"]
        logger.info(f"Digesting {abs_path}")
        
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "digest_worker.py"), abs_path],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True
        )
        
        if proc.returncode == 0:
            logger.info(f"Successfully digested {abs_path}")
            digest_file.write_text(proc.stdout, encoding="utf-8")
        else:
            logger.error(f"Failed to digest {abs_path}: {proc.stderr}")
            
        processed_count += 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
