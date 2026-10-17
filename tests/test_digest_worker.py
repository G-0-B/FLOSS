import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the root FLOSS directory is in path so scripts and packages can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.digest_worker import (
    DigestWorker,
    CandidateClaim,
    GroundingResult,
    GroundingScope,
    compute_minhash,
    jaccard_similarity,
    REPO_ROOT,
)

@pytest.fixture
def mock_cell_directory():
    with patch("packages.source_chain.cell.CellDirectory") as MockCellDir:
        mock_cell = MockCellDir.return_value
        mock_cell.append_entry.return_value = "mock_hash_123"
        yield mock_cell

def test_shingled_minhash_differentiation():
    """Word 3-gram shingling must not falsely match different texts with common vocabulary."""
    text1 = "The study of distributed intelligence requires formal verification and proof of provenance."
    text2 = "Formal verification of distributed provenance requires intelligence and proof in this study."
    
    mh1 = compute_minhash(text1)
    mh2 = compute_minhash(text2)
    
    assert mh1 is not None and mh2 is not None
    sim = jaccard_similarity(mh1, mh2)
    assert sim < 0.6

def test_unverified_digest_never_publishes_to_source_chain(tmp_path, mock_cell_directory):
    """
    P0 Invariant: Untrusted digestion must NEVER publish directly to the source chain.
    propose() and process_file() must never invoke cell_directory.append_entry().
    """
    test_file = tmp_path / "paper.md"
    test_file.write_text("Agents coordinate through stigmergy in decentralized networks.", encoding="utf-8")
    
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path, cell_directory=mock_cell_directory)
    
    mock_claim = CandidateClaim(
        statement="Agents coordinate through stigmergy",
        subject="Agents",
        predicate="coordinate through",
        object_val="stigmergy",
        source_quote="Agents coordinate through stigmergy",
        char_start=0,
        char_end=35,
        alignment="EXACT"
    ).model_dump()
    
    with patch.object(worker, "digest", return_value=([mock_claim], {"status": "EXTRACTED", "truncated": False})):
        result = worker.process_file(test_file)
        
        # Verify cell_directory.append_entry was NEVER called
        mock_cell_directory.append_entry.assert_not_called()
        assert result["status"] == "PROCESSED"
        assert len(result["proposals"]) == 1
        assert result["proposals"][0]["staged"] is True
        assert result["proposals"][0]["entry_hash"] is None

def test_retracted_source_sets_unassessed_zero_confidence(tmp_path):
    """
    P0 Invariant: Retraction of a source indicates publication status, NOT propositional negation.
    Retracted publication maps to reference_resolution.status='RETRACTED', but proposition confidence
    must be 0.0 with assessed=False, not -0.100 or -0.900.
    """
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path)
    
    parsed = {
        "source_path": str(tmp_path / "test.md"),
        "raw_sha256": "abc",
        "text": "See reference DOI: 10.1000/active and retracted DOI: 10.1000/retracted",
        "frontmatter": {}
    }
    
    def mock_urlopen(req, timeout=5):
        url = req.full_url
        mock_cm = MagicMock()
        if "retracted" in url:
            payload = json.dumps({
                "message": {
                    "title": ["Retracted Paper"],
                    "URL": url,
                    "updated-by": [{"type": "retraction", "doi": "10.1000/retraction-notice"}]
                }
            }).encode("utf-8")
        else:
            payload = json.dumps({
                "message": {"title": ["Active Paper"], "URL": url}
            }).encode("utf-8")
        mock_cm.read.return_value = payload
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_cm
        return mock_ctx

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        claims = [
            CandidateClaim(
                statement="Claims statement", subject="S", predicate="P", object_val="O", source_ref="10.1000/retracted"
            ).model_dump()
        ]
        grounded = worker.ground(parsed, claims)
        
        outcomes = {g["scope"]["source_id"]: g["outcome"] for g in grounded["grounding"]}
        assert outcomes.get("10.1000/active") == "UNRESOLVED"
        assert outcomes.get("10.1000/retracted") == "RETRACTED_SOURCE"
        assert outcomes.get("10.1000/retracted") != "CONTRADICT"

        # Now verify proposal confidence contract for retracted source
        claim_obj = CandidateClaim(**claims[0])
        retracted_grounding = GroundingResult(
            **next(g for g in grounded["grounding"] if g["scope"]["source_id"] == "10.1000/retracted")
        )
        proposal = worker.propose(claim_obj, retracted_grounding)
        
        assert proposal["confidence"] == 0.0
        assert proposal["assessed"] is False
        assert proposal["provenance"]["reference_status"] == "RETRACTED"

def test_crossref_updated_by_vs_update_to_directionality(tmp_path):
    """
    P0 Invariant: Crossref retraction detection inspects updated-by directionally.
    - An article with updated-by=[type: retraction] is RETRACTED.
    - An update notice with update-to=[type: retraction] is an active notice record (ACTIVE).
    """
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path)
    
    parsed = {
        "source_path": str(tmp_path / "test.md"),
        "raw_sha256": "abc",
        "text": "Paper DOI: 10.1000/article and Notice DOI: 10.1000/notice",
        "frontmatter": {}
    }
    
    def mock_urlopen(req, timeout=5):
        url = req.full_url
        mock_cm = MagicMock()
        if "article" in url:
            payload = json.dumps({
                "message": {
                    "title": ["Original Article"],
                    "URL": url,
                    "updated-by": [{"type": "retraction", "doi": "10.1000/notice"}]
                }
            }).encode("utf-8")
        else:
            payload = json.dumps({
                "message": {
                    "title": ["Retraction Notice For Original Article"],
                    "URL": url,
                    "update-to": [{"type": "retraction", "updated": {"date-parts": [[2025, 5, 1]]}}]
                }
            }).encode("utf-8")
        mock_cm.read.return_value = payload
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_cm
        return mock_ctx
    
    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        grounded = worker.ground(parsed, [])
        meta = grounded["metadata"]
        
        # Original article is retracted
        assert meta["10.1000/article"]["publication_status"] == "RETRACTED"
        
        # The notice itself is an active record, not a retracted notice
        assert meta["10.1000/notice"]["publication_status"] == "ACTIVE"

def test_unmatched_reference_fails_closed_without_primary_fallback(tmp_path):
    """
    P1 Invariant: A claim specifying a source_ref that does NOT match any cited reference
    must NOT fall back to an unrelated primary DOI or arbitrary citation. It must fail closed
    with source_ref=None and reference_status='UNMATCHED'.
    """
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path)
    
    test_file = tmp_path / "paper.md"
    test_file.write_text(
        "---\ndoi: 10.9999/primary-unrelated\n---\nBody text citing 10.1111/cited-ref",
        encoding="utf-8"
    )
    
    parsed = worker.parse(test_file)
    
    claim_with_bad_ref = CandidateClaim(
        statement="A claim citing non-existent reference",
        subject="S",
        predicate="P",
        object_val="O",
        source_ref="10.404/not-in-document"
    ).model_dump()
    
    with patch.object(worker, "ground", return_value={
        "metadata": {},
        "grounding": [
            {"outcome": "UNRESOLVED", "scope": {"source_id": "10.1111/cited-ref"}},
            {"outcome": "UNRESOLVED", "scope": {"source_id": "10.9999/primary-unrelated"}},
        ]
    }):
        with patch.object(worker, "digest", return_value=([claim_with_bad_ref], {"status": "EXTRACTED", "truncated": False})):
            result = worker.process_file(test_file)
            proposal = result["proposals"][0]
            # Must NOT attribute to primary or first citation
            assert proposal["provenance"]["source_id"] is None
            assert proposal["provenance"]["reference_status"] == "UNMATCHED"

def test_evidence_spans_bind_source_quote_and_detect_ambiguity(tmp_path):
    """
    P1 Invariant: Evidence spans must bind to the verbatim source_quote rather than
    paraphrased statement.
    - Unique occurrence -> alignment='EXACT', valid offsets.
    - Multiple occurrences -> alignment='AMBIGUOUS', char_start=None, char_end=None.
    - Not in text -> alignment='UNALIGNED', char_start=None, char_end=None.
    """
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path)
    text = (
        "Consensus requires fault tolerance. In distributed networks, "
        "consensus requires fault tolerance under adversarial pressure."
    )
    
    claims_raw = [
        {
            "statement": "Networks require fault tolerance to achieve consensus.",  # Paraphrase
            "subject": "Networks",
            "predicate": "require",
            "object_val": "fault tolerance",
            "source_quote": "In distributed networks, consensus requires fault tolerance"  # Unique excerpt
        },
        {
            "statement": "Fault tolerance is essential.",
            "subject": "Fault tolerance",
            "predicate": "is",
            "object_val": "essential",
            "source_quote": "consensus requires fault tolerance"  # Ambiguous: appears twice
        },
        {
            "statement": "Quantum entanglement stabilizes state.",
            "subject": "Quantum entanglement",
            "predicate": "stabilizes",
            "object_val": "state",
            "source_quote": "quantum entanglement stabilizes p2p nodes"  # Absent
        }
    ]
    
    aligned = worker.align_evidence_spans(text, claims_raw)
    assert len(aligned) == 3
    
    # 1. Unique occurrence
    c1 = aligned[0]
    assert c1["alignment"] == "EXACT"
    assert c1["char_start"] == text.find(c1["source_quote"])
    assert c1["char_end"] == c1["char_start"] + len(c1["source_quote"])
    
    # 2. Ambiguous repeated occurrence
    c2 = aligned[1]
    assert c2["alignment"] == "AMBIGUOUS"
    assert c2["char_start"] is None
    assert c2["char_end"] is None
    
    # 3. Unaligned (not found)
    c3 = aligned[2]
    assert c3["alignment"] == "UNALIGNED"
    assert c3["char_start"] is None
    assert c3["char_end"] is None

def test_dual_content_addressed_identities(tmp_path):
    """
    P1 Invariant: Output artifact must record two distinct content-addressed hashes:
    - invocation_key: identifies configuration and processing parameters
    - output_artifact_hash: identifies canonical output bytes
    """
    test_file = tmp_path / "paper.md"
    test_file.write_text("Unique atomic claim about formal zome verification.", encoding="utf-8")
    
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path)
    
    with patch.object(worker, "digest", return_value=([], {"status": "EXTRACTED", "truncated": False})):
        result = worker.process_file(test_file)
        
        assert "invocation_key" in result
        assert "output_artifact_hash" in result
        assert len(result["invocation_key"]) == 64
        assert len(result["output_artifact_hash"]) == 64
        assert result["invocation_key"] != result["output_artifact_hash"]

def test_grounding_never_generates_false_support_on_lexical_overlap(tmp_path):
    """
    Superficial lexical overlap (even negation/contradiction) must NOT generate false SUPPORT.
    Active sources ceiling is UNRESOLVED (+0.100) until verified NLI model is integrated.
    """
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path)
    
    parsed = {
        "source_path": str(tmp_path / "test.md"),
        "raw_sha256": "abc",
        "text": "See reference DOI: 10.1000/consensus",
        "frontmatter": {}
    }
    
    mock_crossref_resp = json.dumps({
        "message": {
            "title": ["Consensus in Distributed Networks"],
            "abstract": "Our consensus protocols handle failures gracefully under heavy load.",
            "URL": "http://dx.doi.org/10.1000/consensus"
        }
    }).encode("utf-8")
    
    with patch("urllib.request.urlopen") as mock_open:
        mock_cm = MagicMock()
        mock_cm.read.return_value = mock_crossref_resp
        mock_open.return_value.__enter__.return_value = mock_cm
        
        claims = [
            CandidateClaim(
                statement="Distributed consensus fails under Byzantine conditions.",
                subject="distributed consensus",
                predicate="fails",
                object_val="Byzantine conditions"
            ).model_dump()
        ]
        grounded = worker.ground(parsed, claims)
        
        outcome = grounded["grounding"][0]["outcome"]
        assert outcome == "UNRESOLVED"
        assert outcome != "SUPPORT"

def test_propose_signed_gradient_mapping(tmp_path):
    """
    PROPOSE maps outcomes to signed gradients in [-0.999, +0.999]:
    - RETRACTED_SOURCE -> 0.0 with assessed=False (unassessed, not contradicted)
    - CONTRADICT -> -0.900 with assessed=True (requires formal verification)
    - INSUFFICIENT_EVIDENCE -> -0.300 with assessed=True
    - UNRESOLVED -> +0.100 with assessed=True (bibliographic verified)
    - SUPPORT -> +0.850 with assessed=True (reserved)
    """
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path)
    
    claim = CandidateClaim(statement="Claim A", subject="S", predicate="P", object_val="O")
    
    # 1. Retracted source
    p_retracted = worker.propose(
        claim, GroundingResult(outcome="RETRACTED_SOURCE", scope=GroundingScope(source_id="10.1/r"))
    )
    assert p_retracted["confidence"] == 0.0
    assert p_retracted["assessed"] is False
    
    # 2. Contradicted (formal NLI)
    p_contradict = worker.propose(
        claim, GroundingResult(outcome="CONTRADICT", scope=GroundingScope(source_id="10.1/c"))
    )
    assert p_contradict["confidence"] == -0.900
    assert p_contradict["assessed"] is True
    
    # 3. Insufficient evidence
    p_insufficient = worker.propose(
        claim, GroundingResult(outcome="INSUFFICIENT_EVIDENCE", scope=GroundingScope(source_id="none"))
    )
    assert p_insufficient["confidence"] == -0.300
    assert p_insufficient["assessed"] is True
    
    # 4. Unresolved (bibliographic presence only)
    p_unresolved = worker.propose(
        claim, GroundingResult(outcome="UNRESOLVED", scope=GroundingScope(source_id="10.1/a"))
    )
    assert p_unresolved["confidence"] == 0.100
    assert p_unresolved["assessed"] is True

    # 5. Support (reserved contract)
    p_support = worker.propose(
        claim, GroundingResult(outcome="SUPPORT", scope=GroundingScope(source_id="10.1/s"))
    )
    assert p_support["confidence"] == 0.850
    assert p_support["assessed"] is True

def test_propose_module_never_references_gateway():
    """Spec invariant: digest_worker module at rest never references or imports GatewayTools."""
    import inspect
    import scripts.digest_worker as dw
    src = inspect.getsource(dw)
    assert "submit_claim" not in src
    assert "GatewayTools" not in src

def test_extraction_metadata_records_truncation_and_api_key_status(tmp_path, monkeypatch):
    """
    DIGEST must return explicit extraction_metadata with truncation details,
    error field, and status.
    """
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path, backend="gemini")
    
    long_text = "word " * 10000  # 50,000 chars, exceeds 32,000 threshold
    parsed = {
        "source_path": str(tmp_path / "long.md"),
        "raw_sha256": "xyz",
        "text": long_text,
        "frontmatter": {}
    }
    
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    claims, meta = worker.digest(parsed)
    assert claims == []
    assert meta["status"] == "NO_API_KEY"
    assert meta["truncated"] is True
    assert meta["original_length"] == len(long_text)
    assert meta["extracted_length"] == 32000
    assert "error" in meta

def test_processed_no_claims_status(tmp_path):
    """When extraction runs successfully but extracts 0 claims, status must be PROCESSED_NO_CLAIMS."""
    test_file = tmp_path / "paper.md"
    test_file.write_text("Empty paper with no atomic claims.", encoding="utf-8")
    
    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path)
    
    with patch.object(worker, "digest", return_value=([], {"status": "EXTRACTED", "truncated": False})):
        result = worker.process_file(test_file)
        assert result["status"] == "PROCESSED_NO_CLAIMS"
        assert result["proposals"] == []

def test_corpus_disk_cache_scheme_and_jaccard_fidelity(tmp_path):
    """
    Corpus disk cache must preserve bit-identical MinHash Jaccard similarities
    between cold and warm loads.
    """
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    
    doc1 = corpus_dir / "doc1.md"
    doc1.write_text("Decentralized knowledge commons and biomimetic distributed intelligence.", encoding="utf-8")
    doc2 = corpus_dir / "doc2.md"
    doc2.write_text("Decentralized knowledge commons and agentic coordination networks.", encoding="utf-8")
    
    worker_cold = DigestWorker(corpus_root=corpus_dir, cache_dir=cache_dir)
    sim_cold = jaccard_similarity(
        worker_cold.corpus_records[str(doc1.resolve())]["minhash"],
        worker_cold.corpus_records[str(doc2.resolve())]["minhash"]
    )
    
    worker_warm = DigestWorker(corpus_root=corpus_dir, cache_dir=cache_dir)
    sim_warm = jaccard_similarity(
        worker_warm.corpus_records[str(doc1.resolve())]["minhash"],
        worker_warm.corpus_records[str(doc2.resolve())]["minhash"]
    )
    
    assert sim_cold > 0.0
    assert sim_cold == sim_warm

def test_cli_path_resolution_foreign_cwd(tmp_path):
    """
    Running digest_worker from a foreign working directory with relative --corpus
    must resolve relative to REPO_ROOT and log the expected corpus path.
    """
    foreign_dir = tmp_path / "foreign"
    foreign_dir.mkdir()
    
    test_paper = tmp_path / "paper.md"
    test_paper.write_text("Document for test.", encoding="utf-8")
    
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "digest_worker.py"),
            str(test_paper),
            "--corpus", "docs/research"
        ],
        cwd=str(foreign_dir),
        capture_output=True,
        text=True
    )
    
    assert proc.returncode == 0
    expected_corpus_str = str((REPO_ROOT / "docs" / "research").resolve())
    assert f"Loading corpus from {expected_corpus_str}" in proc.stderr
    data = json.loads(proc.stdout)
    assert data["type"] == "DigestCandidate"

def test_digest_local_backend_extracts_claims(tmp_path, monkeypatch):
    """
    When backend is set to 'ollama', worker.digest() must call the OpenAI-compatible
    endpoint, parse structured JSON claims, and record backend in extraction_metadata.
    """
    from scripts.digest_worker import DigestWorker

    test_file = tmp_path / "paper.md"
    test_file.write_text("Integrity zomes enforce formal ontology rules in Holochain.", encoding="utf-8")

    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path, backend="ollama", model_id="test-model")
    parsed = worker.parse(test_file)

    sample_json = json.dumps([
        {
            "statement": "Integrity zomes enforce formal ontology rules in Holochain.",
            "subject": "Integrity zomes",
            "predicate": "enforce",
            "object_val": "formal ontology rules in Holochain",
            "source_quote": "Integrity zomes enforce formal ontology rules in Holochain.",
            "source_ref": None
        }
    ])

    class FakeResp:
        status_code = 200
        text = sample_json
        def json(self):
            return {"choices": [{"message": {"content": sample_json}}]}

    monkeypatch.setattr("httpx.post", lambda *a, **kw: FakeResp())

    claims, metadata = worker.digest(parsed)

    assert len(claims) == 1
    assert claims[0]["subject"] == "Integrity zomes"
    assert claims[0]["predicate"] == "enforce"
    assert metadata["backend"] == "ollama"
    assert metadata["model_id"] == "test-model"
    assert metadata["status"] == "EXTRACTED"

def test_digest_local_backend_handles_markdown_fences(tmp_path, monkeypatch):
    """
    Local models frequently wrap JSON outputs in markdown code blocks.
    digest() must strip code fences and extract valid CandidateClaims.
    """
    from scripts.digest_worker import DigestWorker

    test_file = tmp_path / "paper.md"
    test_file.write_text("Agents coordinate through stigmergy.", encoding="utf-8")

    worker = DigestWorker(corpus_root=tmp_path, cache_dir=tmp_path, backend="ollama", model_id="test-model")
    parsed = worker.parse(test_file)

    fenced_output = "```json\n[\n  {\n    \"statement\": \"Agents coordinate through stigmergy.\",\n    \"subject\": \"Agents\",\n    \"predicate\": \"coordinate through\",\n    \"object_val\": \"stigmergy\",\n    \"source_quote\": \"Agents coordinate through stigmergy.\"\n  }\n]\n```"

    class FakeResp:
        status_code = 200
        text = fenced_output
        def json(self):
            return {"choices": [{"message": {"content": fenced_output}}]}

    monkeypatch.setattr("httpx.post", lambda *a, **kw: FakeResp())

    claims, metadata = worker.digest(parsed)

    assert len(claims) == 1
    assert claims[0]["subject"] == "Agents"
    assert metadata["status"] == "EXTRACTED"
