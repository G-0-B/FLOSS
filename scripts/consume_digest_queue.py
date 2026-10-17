#!/usr/bin/env python3
"""
FLOSSI0ULLK Consume Digest Queue v0.4.1
Processes queued intake artifacts through the Digest Worker pipeline.
Enforces workspace path containment, secret screening, parent-budget reconciliation,
and retry-safe quarantine behavior.
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
EVENT_ROOT = WORKSPACE_ROOT / ".agent-surface" / "events"
DIGEST_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "knowledge_log" / "digests"
RETRY_STATE_FILE = DIGEST_OUTPUT_DIR / "retry_state.json"

# Parent heartbeat budget is 300s; keep queue consumption within 240s to guarantee clean parent termination
TOTAL_BUDGET_SECONDS = 240.0
PER_ARTIFACT_TIMEOUT_SECONDS = 75.0
MAX_EXTRACTION_RETRIES = 3

FORBIDDEN_PATH_SUBSTRINGS = [
    ".env",
    "id_rsa",
    "credentials",
    ".pem",
    ".key",
    "secret",
    "password",
    "token",
]


def is_path_safe_and_contained(target_path_str: str) -> bool:
    """
    Validates that target path exists, is contained within the workspace root,
    does not escape via symlinks, and does not match sensitive credential patterns.
    """
    try:
        p = Path(target_path_str)
        if not p.exists():
            return False

        # Resolve symlinks and check containment
        resolved = p.resolve()
        try:
            resolved.relative_to(WORKSPACE_ROOT.resolve())
        except ValueError:
            logger.warning(f"Security: path {resolved} is outside workspace root {WORKSPACE_ROOT}")
            return False

        # Check for sensitive patterns
        lowered = str(resolved).lower()
        for forbidden in FORBIDDEN_PATH_SUBSTRINGS:
            if forbidden in lowered:
                logger.warning(f"Security: path {resolved} matches sensitive pattern '{forbidden}'")
                return False

        return True
    except Exception as e:
        logger.warning(f"Error checking path safety for {target_path_str}: {e}")
        return False


def load_retry_state() -> dict:
    if RETRY_STATE_FILE.exists():
        try:
            return json.loads(RETRY_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_retry_state(state: dict):
    try:
        RETRY_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to persist retry state: {e}")


def main() -> int:
    start_time = time.time()
    processed_dir = EVENT_ROOT / "processed"
    if not processed_dir.exists():
        logger.info(f"No processed events dir: {processed_dir}")
        return 0

    DIGEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    retry_state = load_retry_state()

    events_to_digest = []
    for filepath in sorted(processed_dir.glob("*.json"), reverse=True):
        try:
            event = json.loads(filepath.read_text(encoding="utf-8"))
            actions = event.get("recommended_actions", [])
            abs_path = event.get("abs_path")

            if "digest_artifact" in actions and abs_path:
                if not is_path_safe_and_contained(abs_path):
                    continue

                event_id = event.get("event_id", filepath.stem)
                digest_file = DIGEST_OUTPUT_DIR / f"{event_id}_digest.json"
                quarantine_file = DIGEST_OUTPUT_DIR / f"{event_id}_quarantine.json"

                if not digest_file.exists() and not quarantine_file.exists():
                    events_to_digest.append((event, filepath, digest_file, event_id, quarantine_file))
        except Exception as e:
            logger.warning(f"Error reading {filepath}: {e}")
            continue

    if not events_to_digest:
        logger.info("No new artifacts to digest.")
        return 0

    # Process up to 3 artifacts per heartbeat tick to prevent unbounded load
    for event, event_filepath, digest_file, event_id, quarantine_file in events_to_digest[:3]:
        elapsed = time.time() - start_time
        remaining_budget = TOTAL_BUDGET_SECONDS - elapsed

        if remaining_budget < PER_ARTIFACT_TIMEOUT_SECONDS:
            logger.warning(
                f"Heartbeat budget constraint: {remaining_budget:.1f}s remaining, "
                f"needs >={PER_ARTIFACT_TIMEOUT_SECONDS}s. Deferring remaining artifacts to next heartbeat tick."
            )
            break

        abs_path = event["abs_path"]
        logger.info(f"Digesting {abs_path} (remaining budget: {remaining_budget:.1f}s)")

        try:
            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "digest_worker.py"), abs_path],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=PER_ARTIFACT_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout digesting {abs_path} (exceeded {PER_ARTIFACT_TIMEOUT_SECONDS}s); will retry on next tick.")
            continue

        if proc.returncode == 0:
            try:
                parsed_json = json.loads(proc.stdout)
                status = parsed_json.get("status", "UNKNOWN")

                # Terminal success outcomes commit the digest token
                if status in ("PROCESSED", "PROCESSED_NO_CLAIMS", "EXACT_DUPLICATE_SKIPPED"):
                    digest_file.write_text(json.dumps(parsed_json, indent=2), encoding="utf-8")
                    logger.info(f"Successfully processed {abs_path} with status: {status}")
                    if event_id in retry_state:
                        del retry_state[event_id]
                elif status == "PROCESSED_NO_EXTRACTION":
                    # Track retries for failed extraction
                    retries = retry_state.get(event_id, 0) + 1
                    retry_state[event_id] = retries
                    if retries >= MAX_EXTRACTION_RETRIES:
                        logger.warning(f"Quarantining {abs_path} after {retries} failed extraction attempts.")
                        quarantine_data = {
                            "event_id": event_id,
                            "abs_path": abs_path,
                            "retries": retries,
                            "reason": "Max extraction retries exceeded without available backend.",
                            "last_output": parsed_json,
                        }
                        quarantine_file.write_text(json.dumps(quarantine_data, indent=2), encoding="utf-8")
                        del retry_state[event_id]
                    else:
                        logger.warning(
                            f"Digested {abs_path}: extraction skipped ({parsed_json.get('extraction_metadata', {}).get('status')}); "
                            f"retry {retries}/{MAX_EXTRACTION_RETRIES} recorded. Eligible for next tick."
                        )
                else:
                    logger.info(f"Digested {abs_path} with status: {status}")
            except Exception as e:
                logger.error(f"Worker output for {abs_path} failed JSON validation: {e}\nRaw output: {proc.stdout[:200]}")
        else:
            logger.error(f"Failed to digest {abs_path}: {proc.stderr}")

    save_retry_state(retry_state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
