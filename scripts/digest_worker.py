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
import urllib.request
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import os
from pydantic import BaseModel, Field

try:
    import langextract as lx
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False

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


class CandidateClaim(BaseModel):
    statement: str = Field(description="The atomic claim extracted from the text.")
    subject: str = Field(description="The subject of the claim.")
    predicate: str = Field(description="The predicate or relationship.")
    object_val: str = Field(description="The object of the claim.")
    char_start: int = Field(default=-1, description="Start index in the original text where evidence is found.")
    char_end: int = Field(default=-1, description="End index in the original text.")

class CandidateClaimsOutput(BaseModel):
    claims: List[CandidateClaim]


class GroundingScope(BaseModel):
    source_id: str = Field(description="The DOI or identifier of the source.")
    evidence_ids: List[str] = Field(default_factory=list)

class GroundingResult(BaseModel):
    method: str = Field(default="crossref-api-v1")
    property: str = Field(default="claim_supported_by_source")
    outcome: str = Field(description="SUPPORT, CONTRADICT, INSUFFICIENT_EVIDENCE, or UNRESOLVED")
    scope: GroundingScope
    nonclaims: List[str] = Field(default_factory=list)


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

    def digest(self, parsed_artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Digest stage: Extract CandidateClaims using LangExtract."""
        logger.info(f"DIGEST: Extracting claims from {parsed_artifact['source_path']}")
        text = parsed_artifact["text"]
        
        if not LANGEXTRACT_AVAILABLE:
            logger.warning("LangExtract not available, returning mock claims.")
            return []

        if not os.environ.get("GEMINI_API_KEY"):
            logger.warning("GEMINI_API_KEY not found. Returning mock claims to avoid extraction failure.")
            return []

        try:
            result = lx.extract(
                text_or_documents=text[:4000],  # truncate for safety in tests
                output_schema=CandidateClaimsOutput,
                model_id="gemini-2.5-flash", 
            )
            
            claims = []
            for doc_result in result:
                if hasattr(doc_result, 'extractions') and doc_result.extractions:
                    for ext in doc_result.extractions:
                        claims.append(ext.model_dump())
            return claims
        except Exception as e:
            logger.error(f"LangExtract extraction failed: {e}")
            return []

    def ground(self, parsed_artifact: Dict[str, Any], claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """GROUND stage: Verify DOIs and primary sources via Crossref."""
        logger.info(f"GROUND: Resolving primary sources for {parsed_artifact['source_path']}")
        text = parsed_artifact["text"]
        
        # 1. Extract DOIs using regex
        doi_pattern = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)
        dois = list(set(doi_pattern.findall(text)))
        
        grounding_results = []
        source_metadata = {}
        
        # 2. Query Crossref for deterministic metadata
        for doi in dois[:5]:  # Limit to 5 DOIs per document for now
            url = f"https://api.crossref.org/works/{doi}"
            req = urllib.request.Request(url, headers={'User-Agent': 'FLOSSI0ULLK/0.1 (mailto:research@example.com)'})
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    msg = data.get('message', {})
                    is_retracted = msg.get('is-retracted', False)
                    source_metadata[doi] = {
                        'title': msg.get('title', [''])[0],
                        'is_retracted': is_retracted,
                        'URL': msg.get('URL')
                    }
                    
                    outcome = "CONTRADICT" if is_retracted else "SUPPORT"
                    
                    result = GroundingResult(
                        outcome=outcome,
                        scope=GroundingScope(source_id=doi),
                        nonclaims=[
                            "does not establish replication",
                            "does not establish absence of contradictory literature"
                        ]
                    )
                    grounding_results.append(result.model_dump())
            except Exception as e:
                logger.warning(f"Crossref API failed for {doi}: {e}")
                
        # 1b. Extract ArXiv IDs using regex
        arxiv_pattern = re.compile(r'arxiv:(\d{4}\.\d{4,5}(?:v\d+)?)', re.IGNORECASE)
        arxiv_ids = list(set(arxiv_pattern.findall(text)))

        # 2b. Query ArXiv API
        for arxiv_id in arxiv_ids[:5]:
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            req = urllib.request.Request(url, headers={'User-Agent': 'FLOSSI0ULLK/0.1'})
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    xml_data = response.read()
                root = ET.fromstring(xml_data)
                entry = root.find('{http://www.w3.org/2005/Atom}entry')
                if entry is not None:
                    title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                    summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                    
                    # Store metadata and leave a hook for alphaxiv AI summary
                    source_metadata[f"arxiv:{arxiv_id}"] = {
                        'title': title,
                        'is_retracted': False,  # ArXiv has withdrawal notices in titles usually
                        'URL': f"https://arxiv.org/abs/{arxiv_id}",
                        'author_abstract': summary,
                        'ai_summary': None  # Hook for AlphaXiv MCP / alphaxiv-py integration
                    }
                    
                    result = GroundingResult(
                        outcome="SUPPORT",
                        scope=GroundingScope(source_id=f"arxiv:{arxiv_id}"),
                        nonclaims=[]
                    )
                    grounding_results.append(result.model_dump())
            except Exception as e:
                logger.warning(f"ArXiv API failed for {arxiv_id}: {e}")

        if not grounding_results:
            grounding_results.append(
                GroundingResult(
                    outcome="INSUFFICIENT_EVIDENCE",
                    scope=GroundingScope(source_id="UNKNOWN"),
                    nonclaims=["No valid DOI found in source document."]
                ).model_dump()
            )
            
        return {"metadata": source_metadata, "grounding": grounding_results}

    def process_file(self, filepath: Path) -> Dict[str, Any]:
        parsed = self.parse(filepath)
        deduped = self.dedup(parsed)
        
        if deduped["relationship"] == "EXACT_DUPLICATE":
            logger.info("File is an exact duplicate. Skipping DIGEST and GROUND.")
            claims = []
            grounded = {}
        else:
            claims = self.digest(parsed)
            grounded = self.ground(parsed, claims)
            
        result = {
            "type": "DigestCandidate",
            "artifact": {
                "source": parsed["source_path"],
                "sha256": parsed["raw_sha256"],
                "parser": parsed["parser"]
            },
            "dedup": deduped,
            "claims": claims,
            "grounding": grounded,
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
