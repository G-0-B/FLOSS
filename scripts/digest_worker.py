#!/usr/bin/env python3
"""
FLOSSI0ULLK Digest Worker v0.4.1
Nonauthoritative candidate-generation pipeline for unverified markdown/text.
Follows SDD specification: FLOSS/docs/specs/digest-worker.spec.md (v0.4.1)

Stages: PARSE -> DEDUP -> DIGEST -> RESOLVE_AND_ASSESS -> STAGE
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

# Prevent OpenBLAS/MKL thread pool contention in sub-process / worker loops
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

# Optional LangExtract import
try:
    import langextract as lx

    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False

# Optional datasketch MinHash
try:
    from datasketch import MinHash

    MINHASH_AVAILABLE = True
except ImportError:
    MINHASH_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("digest_worker")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS_ROOT = REPO_ROOT / "docs" / "research"
DEFAULT_CACHE_DIR = REPO_ROOT / ".agent-surface" / "cache"


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_minhash(text: str, num_perm: int = 128) -> Optional[MinHash]:
    """Compute MinHash using word 3-grams (shingles) to preserve local word order."""
    if not MINHASH_AVAILABLE:
        return None
    m = MinHash(num_perm=num_perm)
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return None
    if len(words) < 3:
        shingles = [" ".join(words)]
    else:
        shingles = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]
    for shingle in shingles:
        m.update(shingle.encode("utf-8"))
    return m


def jaccard_similarity(m1: Optional[MinHash], m2: Optional[MinHash]) -> float:
    if not MINHASH_AVAILABLE or not m1 or not m2:
        return 0.0
    return m1.jaccard(m2)


class CandidateClaim(BaseModel):
    statement: str = Field(description="The atomic claim extracted from the text.")
    subject: str = Field(description="The subject of the claim.")
    predicate: str = Field(description="The predicate or relationship.")
    object_val: str = Field(description="The object of the claim.")
    source_quote: Optional[str] = Field(default=None, description="Verbatim supporting quote from the source text.")
    char_start: Optional[int] = Field(default=None, description="Start index in original text where evidence begins.")
    char_end: Optional[int] = Field(default=None, description="End index in original text where evidence ends.")
    alignment: str = Field(default="UNALIGNED", description="Alignment status: EXACT, AMBIGUOUS, FUZZY, or UNALIGNED.")
    source_ref: Optional[str] = Field(default=None, description="Optional explicit DOI/arXiv ID referenced by claim.")


class CandidateClaimsOutput(BaseModel):
    claims: List[CandidateClaim]


class GroundingScope(BaseModel):
    source_id: Optional[str] = Field(default=None, description="The DOI or identifier of the source, or None if ungrounded.")
    evidence_ids: List[str] = Field(default_factory=list)


class GroundingResult(BaseModel):
    method: str = Field(default="crossref-api-v1")
    property: str = Field(default="bibliographic_existence_verified")
    outcome: str = Field(description="SUPPORT, CONTRADICT, RETRACTED_SOURCE, INSUFFICIENT_EVIDENCE, UNRESOLVED, or BIBLIOGRAPHIC_VERIFIED")
    scope: GroundingScope
    nonclaims: List[str] = Field(default_factory=list)


class DigestWorker:
    def __init__(
        self,
        corpus_root: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
        cell_directory: Optional[Any] = None,
        backend: Optional[str] = None,
        model_id: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.corpus_root = Path(corpus_root) if corpus_root else DEFAULT_CORPUS_ROOT
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.cell_directory = cell_directory
        self.backend = backend
        self.model_id = model_id
        self.endpoint_url = endpoint_url
        self.corpus_records: Dict[str, Dict[str, Any]] = {}
        self._load_corpus()

    def _get_cache_file(self) -> Path:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / "digest_corpus_cache.json"

    def _load_corpus(self):
        """Loads the corpus with mtime-keyed persistent disk caching."""
        logger.info(f"Loading corpus from {self.corpus_root}")
        if not self.corpus_root.exists():
            logger.warning(f"Corpus root does not exist: {self.corpus_root}")
            return

        cache_file = self._get_cache_file()
        disk_cache: Dict[str, Any] = {}
        if cache_file.exists():
            try:
                disk_cache = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to read corpus cache: {e}")

        updated_cache: Dict[str, Any] = {}
        for filepath in self.corpus_root.rglob("*.md"):
            try:
                stat = filepath.stat()
                f_key = str(filepath.resolve())
                cached = disk_cache.get(f_key)

                if (
                    cached
                    and cached.get("mtime_ns") == stat.st_mtime_ns
                    and cached.get("size") == stat.st_size
                ):
                    sha = cached["sha256"]
                    mh = None
                    if MINHASH_AVAILABLE and "hashvalues" in cached:
                        import numpy as np

                        scheme = cached.get("scheme")
                        if isinstance(scheme, (list, tuple)):
                            scheme = "".join(scheme)
                        mh = MinHash(
                            num_perm=len(cached["hashvalues"]),
                            hashvalues=np.array(cached["hashvalues"], dtype=np.uint64),
                            scheme=scheme if scheme in ("affine32", "affine64", "legacy") else None,
                        )
                    self.corpus_records[f_key] = {"sha256": sha, "minhash": mh}
                    updated_cache[f_key] = cached
                else:
                    content = filepath.read_bytes()
                    sha = compute_sha256(content)
                    text = content.decode("utf-8", errors="ignore")
                    mh = compute_minhash(text)
                    self.corpus_records[f_key] = {"sha256": sha, "minhash": mh}

                    entry = {
                        "mtime_ns": stat.st_mtime_ns,
                        "size": stat.st_size,
                        "sha256": sha,
                    }
                    if mh is not None:
                        entry["hashvalues"] = [int(v) for v in mh.hashvalues]
                        entry["scheme"] = getattr(mh, "scheme", None)
                    updated_cache[f_key] = entry
            except Exception as e:
                logger.warning(f"Failed to process corpus file {filepath}: {e}")

        try:
            cache_file.write_text(json.dumps(updated_cache), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to persist corpus cache: {e}")

    def parse(self, filepath: Path) -> Dict[str, Any]:
        """Parse stage: reads markdown/text, parses frontmatter metadata, computes SHA256."""
        logger.info(f"PARSE: Reading {filepath}")
        content = filepath.read_bytes()
        text = content.decode("utf-8", errors="ignore")

        frontmatter = {}
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if fm_match:
            raw_fm = fm_match.group(1)
            for line in raw_fm.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                colon_idx = line.find(":")
                if colon_idx != -1:
                    key = line[:colon_idx].strip().lower()
                    val = line[colon_idx + 1:].strip()
                    val = re.sub(r"^['\"]|['\"]$", "", val)
                    frontmatter[key] = val

        primary_id = None
        if "doi" in frontmatter:
            primary_id = frontmatter["doi"]
        elif "arxiv" in frontmatter:
            primary_id = f"arxiv:{frontmatter['arxiv']}"
        elif "id" in frontmatter:
            primary_id = frontmatter["id"]
        else:
            header = text[:1000]
            doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", header, re.IGNORECASE)
            arxiv_match = re.search(r"arxiv:(\d{4}\.\d{4,5}(?:v\d+)?)", header, re.IGNORECASE)
            if doi_match:
                primary_id = doi_match.group(0)
            elif arxiv_match:
                primary_id = f"arxiv:{arxiv_match.group(1)}"

        return {
            "source_path": str(filepath.resolve()),
            "raw_sha256": compute_sha256(content),
            "parser": "python-utf8-decoder",
            "text": text,
            "frontmatter": frontmatter,
            "primary_id": primary_id,
        }

    def dedup(self, parsed_artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Dedup stage checking SHA256 and shingled MinHash against corpus."""
        logger.info(f"DEDUP: Checking {parsed_artifact['source_path']} against corpus...")

        target_sha = parsed_artifact["raw_sha256"]
        target_mh = compute_minhash(parsed_artifact["text"])

        exact_matches = []
        near_matches = []

        for corpus_path, record in self.corpus_records.items():
            if corpus_path == parsed_artifact["source_path"]:
                continue

            if record["sha256"] == target_sha:
                exact_matches.append(corpus_path)
            elif target_mh and record["minhash"]:
                sim = jaccard_similarity(target_mh, record["minhash"])
                if sim > 0.8:
                    near_matches.append({"path": corpus_path, "similarity": sim})

        dedup_result = {
            "exact_matches": exact_matches,
            "near_matches": sorted(near_matches, key=lambda x: x["similarity"], reverse=True),
            "relationship": "UNKNOWN",
        }

        if exact_matches:
            dedup_result["relationship"] = "EXACT_DUPLICATE"
        elif near_matches:
            dedup_result["relationship"] = "NEAR_DUPLICATE"
        else:
            dedup_result["relationship"] = "NEW_KNOWLEDGE"

        return dedup_result

    def align_evidence_spans(self, text: str, claims_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aligns claims with exact character spans in the source text based on source_quote (or statement fallback).
        - Unique occurrence -> alignment='EXACT', char_start, char_end.
        - Multiple occurrences -> alignment='AMBIGUOUS', char_start=None, char_end=None.
        - Absent -> alignment='UNALIGNED', char_start=None, char_end=None.
        """
        aligned = []
        for c in claims_raw:
            c_copy = dict(c)
            target_str = c_copy.get("source_quote") or c_copy.get("statement") or ""
            if target_str:
                matches = [m.start() for m in re.finditer(re.escape(target_str), text, flags=re.IGNORECASE)]
                if len(matches) == 1:
                    c_copy["char_start"] = matches[0]
                    c_copy["char_end"] = matches[0] + len(target_str)
                    c_copy["alignment"] = "EXACT"
                elif len(matches) > 1:
                    c_copy["char_start"] = None
                    c_copy["char_end"] = None
                    c_copy["alignment"] = "AMBIGUOUS"
                else:
                    c_copy["char_start"] = None
                    c_copy["char_end"] = None
                    c_copy["alignment"] = "UNALIGNED"
            else:
                c_copy["char_start"] = None
                c_copy["char_end"] = None
                c_copy["alignment"] = "UNALIGNED"
            aligned.append(c_copy)
        return aligned

    def digest(self, parsed_artifact: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Digest stage: Extract CandidateClaims using LangExtract or local inference.
        Returns (claims, extraction_metadata).
        """
        logger.info(f"DIGEST: Extracting claims from {parsed_artifact['source_path']}")
        text = parsed_artifact["text"]

        # Resolve backend
        backend = self.backend or "auto"
        if backend == "auto":
            if os.environ.get("GEMINI_API_KEY") and LANGEXTRACT_AVAILABLE:
                backend = "gemini"
            else:
                backend = "ollama"

        max_extract_chars = 6000 if backend in ("ollama", "omniroute") else 32000
        is_truncated = len(text) > max_extract_chars
        extract_slice = text[:max_extract_chars]

        metadata: Dict[str, Any] = {
            "truncated": is_truncated,
            "original_length": len(text),
            "extracted_length": len(extract_slice),
            "backend": backend,
            "model_id": self.model_id,
            "status": "UNKNOWN",
            "error": None,
        }

        if is_truncated:
            logger.warning(
                f"Source text ({len(text)} chars) exceeded extraction threshold ({max_extract_chars} chars); "
                f"truncating for digest pass."
            )

        if backend == "gemini":
            if not os.environ.get("GEMINI_API_KEY"):
                logger.warning("GEMINI_API_KEY not found in environment; extraction skipped.")
                metadata["status"] = "NO_API_KEY"
                metadata["error"] = "GEMINI_API_KEY environment variable is not set."
                return [], metadata

            if not LANGEXTRACT_AVAILABLE:
                logger.warning("LangExtract not installed; extraction skipped.")
                metadata["status"] = "NO_BACKEND"
                metadata["error"] = "langextract package is not available."
                return [], metadata

            model_name = self.model_id or "gemini-1.5-flash"
            metadata["model_id"] = model_name
            try:
                result = lx.extract(
                    text_or_filepaths=extract_slice,
                    schema=CandidateClaimsOutput,
                    model_id=model_name,
                )
                metadata["status"] = "EXTRACTED"
                claims = []
                if hasattr(result, "claims"):
                    for c in result.claims:
                        cd = c.model_dump()
                        if not cd.get("source_quote"):
                            cd["source_quote"] = cd.get("statement")
                        claims.append(cd)
                aligned_claims = self.align_evidence_spans(text, claims)
                return aligned_claims, metadata
            except Exception as e:
                logger.error(f"LangExtract execution failed: {e}")
                metadata["status"] = "EXTRACTION_FAILED"
                metadata["error"] = str(e)
                return [], metadata

        elif backend in ("ollama", "omniroute"):
            endpoint = self.endpoint_url
            if not endpoint:
                if backend == "ollama":
                    endpoint = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
                else:
                    endpoint = os.environ.get("OMNIROUTE_BASE_URL", "http://127.0.0.1:8000/v1")

            model_name = self.model_id
            if not model_name:
                model_name = os.environ.get("OLLAMA_MODEL", "llama3.2:3b-instruct-q4_K_S") if backend == "ollama" else "default"
            metadata["model_id"] = model_name

            system_prompt = (
                "You are an expert scientific knowledge extractor. Your task is to read the provided text "
                "and extract 1 to 5 atomic scientific or conceptual claims as structured triples.\n"
                "You MUST return ONLY valid JSON matching this schema:\n"
                "[\n"
                "  {\n"
                '    "statement": "Normalized atomic claim sentence",\n'
                '    "subject": "Subject entity/concept",\n'
                '    "predicate": "Relationship verb/predicate",\n'
                '    "object_val": "Object entity/value",\n'
                '    "source_quote": "Verbatim excerpt sentence directly from the text supporting this claim",\n'
                '    "source_ref": "Optional DOI or arXiv ID if explicitly cited in text, else null"\n'
                "  }\n"
                "]"
            )

            user_prompt = f"Text to extract claims from:\n\n{extract_slice}"

            try:
                resp = httpx.post(
                    f"{endpoint}/chat/completions",
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 4000,
                        "options": {"num_ctx": 16384},
                    },
                    timeout=120.0,
                )
                if resp.status_code >= 400:
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

                msg = resp.json()["choices"][0]["message"]
                content = (msg.get("content") or "").strip()
                if not content:
                    content = (msg.get("reasoning") or msg.get("reasoning_content") or "").strip()

                cleaned = re.sub(r"<think\b[^>]*>.*?</think\s*>", "", content, flags=re.IGNORECASE | re.DOTALL).strip()
                search_pool = cleaned if cleaned else content

                fence_match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", search_pool, re.DOTALL)
                if fence_match:
                    candidate = fence_match.group(1).strip()
                else:
                    arr_match = re.search(r"(\{\s*\"claims\"\s*:\s*\[.*?\]\s*\}|\[\s*\{.*?\}\s*\])", search_pool, re.DOTALL)
                    candidate = arr_match.group(1).strip() if arr_match else search_pool.strip()

                raw_claims = []
                try:
                    parsed_data = json.loads(candidate)
                    raw_claims = parsed_data.get("claims", []) if isinstance(parsed_data, dict) else parsed_data
                except json.JSONDecodeError:
                    last_brace = candidate.rfind("}")
                    if last_brace != -1:
                        truncated = candidate[:last_brace + 1].strip()
                        first_bracket = truncated.find("[")
                        if first_bracket != -1:
                            try:
                                repaired = truncated[first_bracket:] + "\n]"
                                parsed_data = json.loads(repaired)
                                raw_claims = parsed_data if isinstance(parsed_data, list) else []
                            except json.JSONDecodeError:
                                pass
                    if not raw_claims:
                        raise

                claims = []
                if isinstance(raw_claims, list):
                    for item in raw_claims:
                        if isinstance(item, dict) and "statement" in item:
                            quote = item.get("source_quote") or item.get("statement")
                            c = CandidateClaim(
                                statement=str(item.get("statement", "")),
                                subject=str(item.get("subject", "")),
                                predicate=str(item.get("predicate", "")),
                                object_val=str(item.get("object_val", "")),
                                source_quote=str(quote) if quote else None,
                                source_ref=item.get("source_ref"),
                            )
                            claims.append(c.model_dump())
                metadata["status"] = "EXTRACTED"
                aligned_claims = self.align_evidence_spans(text, claims)
                return aligned_claims, metadata
            except Exception as e:
                logger.error(f"Local inference extraction failed: {e}")
                metadata["status"] = "EXTRACTION_FAILED"
                metadata["error"] = str(e)
                return [], metadata
        else:
            metadata["status"] = "NO_BACKEND"
            metadata["error"] = f"Unknown backend: {backend}"
            return [], metadata

    def _is_crossref_retracted(self, msg: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Directional retraction check:
        Only 'updated-by' relationships (where this article was updated by a retraction notice)
        indicate that THIS article was retracted.
        Returns (is_retracted, notice_doi).
        """
        updates = msg.get("updated-by", [])
        if isinstance(updates, list):
            for u in updates:
                if isinstance(u, dict) and u.get("type", "").lower() == "retraction":
                    notice_doi = u.get("doi") or u.get("DOI")
                    return True, str(notice_doi) if notice_doi else None
        return False, None

    def ground(self, parsed_artifact: Dict[str, Any], claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        GROUND stage: Establishes bibliographic grounding and publication status.
        Decouples publication status (RETRACTED, ACTIVE) from proposition truth value.
        Retracted publications return RETRACTED_SOURCE.
        Non-retracted DOIs/arXiv preprints return UNRESOLVED (+0.100).
        """
        logger.info(f"GROUND: Resolving primary sources for {parsed_artifact['source_path']}")
        text = parsed_artifact["text"]

        doi_pattern = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
        dois = list(set(doi_pattern.findall(text)))

        primary_id = parsed_artifact.get("primary_id")
        if primary_id and primary_id.startswith("10.") and primary_id not in dois:
            dois.insert(0, primary_id)

        grounding_results = []
        source_metadata = {}

        # 1. Query Crossref
        for doi in dois[:5]:
            url = f"https://api.crossref.org/works/{doi}"
            req = urllib.request.Request(
                url, headers={"User-Agent": "FLOSSI0ULLK/0.1 (mailto:research@example.com)"}
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    msg = data.get("message", {})
                    is_retracted, notice_ref = self._is_crossref_retracted(msg)
                    abstract = msg.get("abstract", "")

                    pub_status = "RETRACTED" if is_retracted else "ACTIVE"
                    source_metadata[doi] = {
                        "title": msg.get("title", [""])[0],
                        "publication_status": pub_status,
                        "is_retracted": is_retracted,
                        "notice_ref": notice_ref,
                        "URL": msg.get("URL"),
                        "abstract": abstract,
                    }

                    outcome = "RETRACTED_SOURCE" if is_retracted else "UNRESOLVED"
                    prop = "source_retracted" if is_retracted else "bibliographic_existence_verified"

                    result = GroundingResult(
                        outcome=outcome,
                        property=prop,
                        scope=GroundingScope(source_id=doi),
                        nonclaims=[
                            "bibliographic presence verified; semantic claim support deferred to verified NLI model",
                            "source retraction noted as publication metadata; proposition remains unassessed (confidence 0.0)",
                        ],
                    )
                    grounding_results.append(result.model_dump())
            except Exception as e:
                logger.warning(f"Crossref API failed for {doi}: {e}")

        # 2. Query ArXiv API
        arxiv_pattern = re.compile(r"arxiv:(\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE)
        arxiv_ids = list(set(arxiv_pattern.findall(text)))
        if primary_id and primary_id.startswith("arxiv:"):
            raw_arid = primary_id[6:]
            if raw_arid not in arxiv_ids:
                arxiv_ids.insert(0, raw_arid)

        for arxiv_id in arxiv_ids[:5]:
            time.sleep(0.5)
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            req = urllib.request.Request(url, headers={"User-Agent": "FLOSSI0ULLK/0.1"})
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    xml_data = response.read()
                root = ET.fromstring(xml_data)
                entry = root.find("{http://www.w3.org/2005/Atom}entry")
                if entry is not None:
                    title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                    summary_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    summary = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""

                    source_metadata[f"arxiv:{arxiv_id}"] = {
                        "title": title,
                        "publication_status": "ACTIVE",
                        "is_retracted": False,
                        "URL": f"https://arxiv.org/abs/{arxiv_id}",
                        "author_abstract": summary,
                        "ai_summary": None,
                    }

                    result = GroundingResult(
                        outcome="UNRESOLVED",
                        property="bibliographic_existence_verified",
                        scope=GroundingScope(source_id=f"arxiv:{arxiv_id}"),
                        nonclaims=["preprint existence verified; semantic claim support deferred to verified NLI model"],
                    )
                    grounding_results.append(result.model_dump())
            except Exception as e:
                logger.warning(f"ArXiv API failed for {arxiv_id}: {e}")

        if not grounding_results:
            grounding_results.append(
                GroundingResult(
                    outcome="INSUFFICIENT_EVIDENCE",
                    property="unreferenced",
                    scope=GroundingScope(source_id=primary_id),
                    nonclaims=["No valid DOI or preprint ID found in source document."],
                ).model_dump()
            )

        return {"metadata": source_metadata, "grounding": grounding_results}

    def propose(
        self,
        claim: CandidateClaim,
        grounding: GroundingResult,
        cell_directory: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Translates a grounded CandidateClaim into a staged proposal artifact (StagedCandidate).
        Does NOT publish to CellDirectory source chain (authority boundary protection per Spec v0.4.1).
        Maps grounding states to signed analog confidence in [-0.999, +0.999].
        """
        outcome = grounding.outcome.upper()
        assessed = True
        if outcome == "RETRACTED_SOURCE":
            confidence = 0.0
            assessed = False
        elif outcome in ["CONTRADICT", "RETRACTED"]:
            confidence = -0.900
        elif outcome == "INSUFFICIENT_EVIDENCE":
            confidence = -0.300
        elif outcome in ["UNRESOLVED", "BIBLIOGRAPHIC_VERIFIED"]:
            confidence = 0.100
        elif outcome == "SUPPORT":
            confidence = 0.850
        else:
            confidence = 0.0
            assessed = False

        ref_status = "RETRACTED" if outcome == "RETRACTED_SOURCE" else "RESOLVED"
        knowledge_triple = {
            "subject": claim.subject,
            "predicate": claim.predicate,
            "object": claim.object_val,
            "confidence": confidence,
            "assessed": assessed,
            "provenance": {
                "source_type": "LlmExtraction",
                "source_id": grounding.scope.source_id,
                "reference_status": ref_status,
                "grounding_method": grounding.method,
                "grounding_outcome": grounding.outcome,
                "source_quote": claim.source_quote,
                "char_start": claim.char_start,
                "char_end": claim.char_end,
                "alignment": claim.alignment,
            },
            "staged": True,
            "entry_hash": None,
        }

        return knowledge_triple

    def _get_cell_directory(self) -> Optional[Any]:
        if self.cell_directory is not None:
            return self.cell_directory

        dna_hash = os.environ.get("FLOSS_DNA_HASH")
        if not dna_hash:
            logger.info("FLOSS_DNA_HASH unset; cell directory not initialized (fail closed).")
            return None

        try:
            from packages.source_chain.cell import CellDirectory

            base_dir = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
            return CellDirectory(base_dir=base_dir, dna_hash=dna_hash)
        except Exception as e:
            logger.warning(f"CellDirectory unavailable: {e}")
            return None

    def process_file(self, filepath: Path) -> Dict[str, Any]:
        """Executes full pipeline: PARSE -> DEDUP -> DIGEST -> GROUND -> STAGE (PROPOSE)."""
        parsed = self.parse(filepath)
        deduped = self.dedup(parsed)

        proposals = []
        if deduped["relationship"] == "EXACT_DUPLICATE":
            logger.info("File is an exact duplicate. Skipping DIGEST, GROUND, and STAGE.")
            result = {
                "type": "DigestCandidate",
                "artifact": {
                    "source": parsed["source_path"],
                    "sha256": parsed["raw_sha256"],
                    "parser": parsed["parser"],
                },
                "dedup": deduped,
                "extraction_metadata": {
                    "truncated": False,
                    "original_length": len(parsed["text"]),
                    "extracted_length": 0,
                    "model_id": None,
                    "status": "SKIPPED_DUPLICATE",
                    "error": None,
                },
                "claims": [],
                "grounding": {},
                "proposals": [],
                "status": "EXACT_DUPLICATE_SKIPPED",
            }
            inv_dict = {
                "source_sha256": parsed["raw_sha256"],
                "parser": parsed["parser"],
                "schema_version": "0.4.1",
                "backend": self.backend or "auto",
                "model_id": self.model_id or "default",
            }
            result["invocation_key"] = hashlib.sha256(json.dumps(inv_dict, sort_keys=True).encode("utf-8")).hexdigest()
            output_bytes = json.dumps(result, sort_keys=True, indent=2).encode("utf-8")
            result["output_artifact_hash"] = hashlib.sha256(output_bytes).hexdigest()
            return result

        claims, extraction_meta = self.digest(parsed)
        grounded = self.ground(parsed, claims)

        cell_dir = self._get_cell_directory()
        grounding_list = grounded.get("grounding", [])

        # Claim-to-grounding pairing policy per Spec v0.4.1 (fail-closed attribution)
        primary_id = parsed.get("primary_id")
        for claim_dict in claims:
            claim_obj = CandidateClaim(**claim_dict)

            matched_grounding = None
            ref_status = "GROUNDED"

            if claim_obj.source_ref:
                # Explicit reference cited by the claim
                for g in grounding_list:
                    if g.get("scope", {}).get("source_id") == claim_obj.source_ref:
                        matched_grounding = GroundingResult(**g)
                        break
                if not matched_grounding:
                    # Explicit reference NOT found among resolved references: FAIL CLOSED
                    ref_status = "UNMATCHED"
                    matched_grounding = GroundingResult(
                        outcome="INSUFFICIENT_EVIDENCE",
                        property="unmatched_reference",
                        scope=GroundingScope(source_id=None),
                        nonclaims=["Claim specified a source_ref that could not be resolved from cited references."],
                    )
            else:
                # No explicit reference: general claim from document
                if primary_id:
                    for g in grounding_list:
                        if g.get("scope", {}).get("source_id") == primary_id:
                            matched_grounding = GroundingResult(**g)
                            break
                if not matched_grounding:
                    ref_status = "UNGROUNDED"
                    matched_grounding = GroundingResult(
                        outcome="INSUFFICIENT_EVIDENCE",
                        property="ungrounded_claim",
                        scope=GroundingScope(source_id=None),
                        nonclaims=["Claim does not cite an explicit reference, and no primary document ID was resolved."],
                    )

            proposal = self.propose(claim_obj, matched_grounding, cell_dir)
            if ref_status != "GROUNDED":
                proposal["provenance"]["reference_status"] = ref_status
                proposal["provenance"]["source_id"] = None
            proposals.append(proposal)

        # Truthful status reporting per Spec §4.5
        if not claims:
            if extraction_meta.get("status") == "EXTRACTED":
                status = "PROCESSED_NO_CLAIMS"
            else:
                status = "PROCESSED_NO_EXTRACTION"
        else:
            status = "PROCESSED"

        inv_dict = {
            "source_sha256": parsed["raw_sha256"],
            "parser": parsed["parser"],
            "schema_version": "0.4.1",
            "backend": self.backend or "auto",
            "model_id": self.model_id or "default",
        }
        invocation_key = hashlib.sha256(json.dumps(inv_dict, sort_keys=True).encode("utf-8")).hexdigest()

        result = {
            "type": "DigestCandidate",
            "invocation_key": invocation_key,
            "artifact": {
                "source": parsed["source_path"],
                "sha256": parsed["raw_sha256"],
                "parser": parsed["parser"],
            },
            "dedup": deduped,
            "extraction_metadata": extraction_meta,
            "claims": claims,
            "grounding": grounded,
            "proposals": proposals,
            "status": status,
        }

        output_bytes = json.dumps(result, sort_keys=True, indent=2).encode("utf-8")
        result["output_artifact_hash"] = hashlib.sha256(output_bytes).hexdigest()
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="FLOSSI0ULLK Digest Worker (Candidate Pipeline)")
    parser.add_argument("file", help="Path to markdown/text file to process")
    parser.add_argument(
        "--corpus",
        default=str(DEFAULT_CORPUS_ROOT),
        help="Corpus root directory to dedup against (default: FLOSS/docs/research)",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help="Directory to persist the corpus index cache",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "gemini", "ollama", "omniroute"],
        default="auto",
        help="Inference backend for DIGEST claim extraction (default: auto)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model ID to use for inference",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Custom base endpoint URL for OpenAI-compatible inference",
    )
    args = parser.parse_args()

    target_file = Path(args.file)
    if not target_file.is_absolute():
        if target_file.exists():
            target_file = target_file.resolve()
        else:
            target_file = (REPO_ROOT / target_file).resolve()

    corpus_root = Path(args.corpus)
    if not corpus_root.is_absolute():
        if corpus_root.exists():
            corpus_root = corpus_root.resolve()
        else:
            corpus_root = (REPO_ROOT / corpus_root).resolve()

    cache_dir = Path(args.cache_dir)
    if not cache_dir.is_absolute():
        if cache_dir.exists():
            cache_dir = cache_dir.resolve()
        else:
            cache_dir = (REPO_ROOT / cache_dir).resolve()

    if not target_file.exists():
        logger.error(f"File {target_file} does not exist.")
        return 1

    worker = DigestWorker(
        corpus_root=corpus_root,
        cache_dir=cache_dir,
        backend=args.backend,
        model_id=args.model,
        endpoint_url=args.endpoint,
    )
    result = worker.process_file(target_file)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
