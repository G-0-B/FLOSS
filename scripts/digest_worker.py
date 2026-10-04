#!/usr/bin/env python3
"""
Digest Worker: First stage of the FLOSSI0ULLK digestive tract.
Handles INGEST -> OBSERVE -> DEDUP -> DIGEST -> GROUND -> PROPOSE.
Currently implements PARSE and DEDUP (exact SHA-256 + MinHash).
"""

import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from datasketch import MinHash
    MINHASH_AVAILABLE = True
except ImportError:
    MINHASH_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_minhash(text: str, num_perm: int = 128) -> Optional['MinHash']:
    if not MINHASH_AVAILABLE:
        return None
    m = MinHash(num_perm=num_perm)
    # Simple whitespace tokenizer for demo
    for word in text.lower().split():
        m.update(word.encode("utf-8"))
    return m


def jaccard_similarity(m1: 'MinHash', m2: 'MinHash') -> float:
    if not MINHASH_AVAILABLE or not m1 or not m2:
        return 0.0
    return m1.jaccard(m2)


class DigestWorker:
    def __init__(self, corpus_root: Path):
        self.corpus_root = corpus_root
        self.corpus_records: Dict[str, Dict[str, Any]] = {}
        self._load_corpus()

    def _load_corpus(self):
        """Loads the existing corpus to deduplicate against."""
        logger.info(f"Loading corpus from {self.corpus_root}")
        if not self.corpus_root.exists():
            return

        for filepath in self.corpus_root.rglob("*.md"):
            try:
                content = filepath.read_bytes()
                sha = compute_sha256(content)
                text = content.decode("utf-8", errors="ignore")
                
                self.corpus_records[str(filepath)] = {
                    "sha256": sha,
                    "minhash": compute_minhash(text)
                }
            except Exception as e:
                logger.warning(f"Could not load {filepath}: {e}")
        
        logger.info(f"Loaded {len(self.corpus_records)} records into corpus.")

    def parse(self, filepath: Path) -> Dict[str, Any]:
        """Parse stage using generic text reading (stub for Docling/GROBID)."""
        logger.info(f"PARSING: {filepath}")
        content = filepath.read_bytes()
        text = content.decode("utf-8", errors="ignore")
        
        parsed_artifact = {
            "source_path": str(filepath),
            "raw_sha256": compute_sha256(content),
            "parser": "python-utf8-decoder", # stub
            "text": text,
        }
        return parsed_artifact

    def dedup(self, parsed_artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Dedup stage checking SHA256 and MinHash against corpus."""
        logger.info(f"DEDUP: Checking {parsed_artifact['source_path']} against corpus...")
        
        target_sha = parsed_artifact["raw_sha256"]
        target_mh = compute_minhash(parsed_artifact["text"])
        
        exact_matches = []
        near_matches = []
        
        for corpus_path, record in self.corpus_records.items():
            # Skip self
            if corpus_path == parsed_artifact["source_path"]:
                continue
                
            if record["sha256"] == target_sha:
                exact_matches.append(corpus_path)
            elif target_mh and record["minhash"]:
                sim = jaccard_similarity(target_mh, record["minhash"])
                if sim > 0.8:  # 80% similarity threshold
                    near_matches.append({"path": corpus_path, "similarity": sim})

        dedup_result = {
            "exact_matches": exact_matches,
            "near_matches": sorted(near_matches, key=lambda x: x["similarity"], reverse=True),
            "relationship": "UNKNOWN"
        }
        
        if exact_matches:
            dedup_result["relationship"] = "EXACT_DUPLICATE"
        elif near_matches:
            dedup_result["relationship"] = "NEAR_DUPLICATE"
        else:
            dedup_result["relationship"] = "NEW_KNOWLEDGE"

        return dedup_result

    def process_file(self, filepath: Path) -> Dict[str, Any]:
        parsed = self.parse(filepath)
        deduped = self.dedup(parsed)
        
        # Combine into a GroundingAttempt / Candidate
        result = {
            "type": "DigestCandidate",
            "artifact": {
                "source": parsed["source_path"],
                "sha256": parsed["raw_sha256"],
                "parser": parsed["parser"]
            },
            "dedup": deduped,
            "status": "PROCESSED"
        }
        return result


def main():
    parser = argparse.ArgumentParser(description="FLOSS Digest Worker")
    parser.add_argument("file", help="File to digest")
    parser.add_argument("--corpus", default="FLOSS/docs/research", help="Corpus root directory to dedup against")
    args = parser.parse_args()

    target_file = Path(args.file)
    corpus_root = Path(args.corpus)

    if not target_file.exists():
        logger.error(f"File {target_file} does not exist.")
        return 1

    worker = DigestWorker(corpus_root)
    result = worker.process_file(target_file)
    
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    exit(main())
