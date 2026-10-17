"""
FLOSSI0ULLK Benchmark Dataset Staging & Projection Module.
Acquires lossless native records for SciFact and Re-DocRED, verifies provenance hashes,
and generates governed candidate FLOSS projections (marked mapping_status='candidate' pending human review).
Part of Phase 3 (Benchmark Track Staging) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any, Optional
import httpx

EVALS_DIR = Path(__file__).resolve().parent.parent / "evals"

SCIFACT_URL = "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz"
REDOCRED_DEV_URL = "https://raw.githubusercontent.com/tonytan48/Re-DocRED/master/data/dev_revised.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def stage_scifact(evals_base: Path = EVALS_DIR) -> dict[str, Any]:
    """Downloads SciFact archive, extracts native JSONL splits, and records provenance."""
    scifact_dir = evals_base / "entailment" / "scifact_native"
    scifact_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching SciFact archive from {SCIFACT_URL}...")
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        res = client.get(SCIFACT_URL)
        res.raise_for_status()
        tar_bytes = res.content

    tar_sha = sha256_bytes(tar_bytes)
    print(f"Downloaded SciFact archive ({len(tar_bytes)} bytes, sha256: {tar_sha[:16]}...)")

    extracted_files = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            base_name = Path(member.name).name
            if base_name in ("claims_dev.jsonl", "claims_train.jsonl", "corpus.jsonl"):
                f = tar.extractfile(member)
                if f:
                    content = f.read()
                    out_path = scifact_dir / base_name
                    out_path.write_bytes(content)
                    count = len([line for line in content.splitlines() if line.strip()])
                    extracted_files[base_name] = {
                        "path": str(out_path.relative_to(evals_base.parent)),
                        "sha256": sha256_bytes(content),
                        "size_bytes": len(content),
                        "record_count": count,
                    }
                    print(f"  Extracted {base_name}: {count} records")

    manifest = {
        "dataset": "SciFact",
        "license": "CC-BY-NC-2.0",
        "upstream_source_url": SCIFACT_URL,
        "archive_sha256": tar_sha,
        "files": extracted_files,
    }
    manifest_path = scifact_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def stage_redocred(evals_base: Path = EVALS_DIR) -> dict[str, Any]:
    """Downloads Re-DocRED dev_revised.json, extracts records, and records provenance."""
    redocred_dir = evals_base / "document_relation" / "redocred_native"
    redocred_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching Re-DocRED dev_revised.json from {REDOCRED_DEV_URL}...")
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        res = client.get(REDOCRED_DEV_URL)
        res.raise_for_status()
        content = res.content

    dev_sha = sha256_bytes(content)
    out_path = redocred_dir / "dev_revised.json"
    out_path.write_bytes(content)

    data = json.loads(content.decode("utf-8"))
    record_count = len(data) if isinstance(data, list) else 0
    print(f"Downloaded Re-DocRED dev_revised.json ({record_count} documents, sha256: {dev_sha[:16]}...)")

    manifest = {
        "dataset": "Re-DocRED",
        "license": "CC-BY-SA-4.0",
        "upstream_source_url": REDOCRED_DEV_URL,
        "file": {
            "path": str(out_path.relative_to(evals_base.parent)),
            "sha256": dev_sha,
            "size_bytes": len(content),
            "document_count": record_count,
        }
    }
    manifest_path = redocred_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def project_scifact_candidates(limit: int = 50, evals_base: Path = EVALS_DIR) -> int:
    """
    Projects native SciFact claims into candidate FLOSS ClaimVersion and EvidenceSet records.
    Every record is explicitly flagged as mapping_status='candidate' per ADR split governance.
    """
    native_dir = evals_base / "entailment" / "scifact_native"
    proj_dir = evals_base / "entailment" / "floss_projection"
    proj_dir.mkdir(parents=True, exist_ok=True)

    claims_file = native_dir / "claims_dev.jsonl"
    corpus_file = native_dir / "corpus.jsonl"

    if not claims_file.is_file() or not corpus_file.is_file():
        raise FileNotFoundError("Native SciFact files missing. Run stage_scifact() first.")

    # Load corpus index: doc_id -> {title, abstract_sentences}
    corpus = {}
    with open(corpus_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                corpus[row["doc_id"]] = {
                    "title": row.get("title", ""),
                    "sentences": row.get("abstract", [])
                }

    projected_records = []
    with open(claims_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if limit and idx >= limit:
                break
            if not line.strip():
                continue
            claim_row = json.loads(line)
            cid = claim_row.get("id")
            statement = claim_row.get("claim", "")
            evidence_map = claim_row.get("evidence", {})

            # Map stances: SUPPORT -> SUPPORTED, CONTRADICT -> CONTRADICTED, NO_INFO -> INSUFFICIENT
            # SciFact evidence is {doc_id: [{"sentences": [s_idx], "label": "SUPPORT" | "CONTRADICT"}]}
            atoms = []
            claim_stance = "INSUFFICIENT"
            support_flag = False
            refutation_flag = False

            for doc_id_str, items in evidence_map.items():
                doc_id = int(doc_id_str)
                doc_info = corpus.get(doc_id, {"sentences": [], "title": ""})
                sents = doc_info["sentences"]

                for item in items:
                    label = item.get("label", "NOT_ENOUGH_INFO")
                    if label == "SUPPORT":
                        support_flag = True
                    elif label == "CONTRADICT":
                        refutation_flag = True

                    sentence_indices = item.get("sentences", [])
                    quote = " ".join(sents[i] for i in sentence_indices if i < len(sents))
                    atoms.append({
                        "atom_id": f"atom-{doc_id}-{'-'.join(str(s) for s in sentence_indices)}",
                        "atom_type": "text_span",
                        "grounding_class": "SOURCE_TEXT_EXACT",
                        "source_ref": f"scifact:doc:{doc_id}",
                        "literal_content": quote,
                        "metadata": {"doc_id": doc_id, "sentences": sentence_indices, "native_label": label}
                    })

            if support_flag and not refutation_flag:
                claim_stance = "SUPPORTED"
            elif not support_flag and refutation_flag:
                claim_stance = "CONTRADICTED"
            elif support_flag and refutation_flag:
                claim_stance = "CONFLICTING"
            else:
                claim_stance = "INSUFFICIENT"

            record = {
                "claim_id": f"scifact-claim-{cid}",
                "statement": statement,
                "evidence_atoms": atoms,
                "projected_stance": claim_stance,
                "support": support_flag,
                "refutation": refutation_flag,
                "governance": {
                    "mapping_status": "candidate",
                    "mapping_rule_version": "v1.0.0-scifact-stance",
                    "annotator_ids": [],
                    "adjudication_id": None,
                    "upstream_record_hash": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                    "license_snapshot": "CC-BY-NC-2.0"
                }
            }
            projected_records.append(record)

    out_file = proj_dir / "projected_claims_dev.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for r in projected_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Generated {len(projected_records)} candidate SciFact projections into {out_file.name}")
    return len(projected_records)


def project_redocred_candidates(limit: int = 20, evals_base: Path = EVALS_DIR) -> int:
    """
    Projects native Re-DocRED document relations into candidate FLOSS document relation records.
    Every record is explicitly flagged as mapping_status='candidate' per ADR split governance.
    """
    native_dir = evals_base / "document_relation" / "redocred_native"
    proj_dir = evals_base / "document_relation" / "floss_projection"
    proj_dir.mkdir(parents=True, exist_ok=True)

    native_file = native_dir / "dev_revised.json"
    if not native_file.is_file():
        raise FileNotFoundError("Native Re-DocRED file missing. Run stage_redocred() first.")

    with open(native_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    projected_docs = []
    for idx, doc in enumerate(data):
        if limit and idx >= limit:
            break

        title = doc.get("title", "")
        sents = doc.get("sents", [])
        vertex_set = doc.get("vertexSet", [])
        labels = doc.get("labels", [])

        # Flatten sentences into continuous text with sentence block ranges
        blocks = []
        char_offset = 0
        doc_text_parts = []
        for s_idx, sent_words in enumerate(sents):
            sent_str = " ".join(sent_words)
            sent_len = len(sent_str)
            doc_text_parts.append(sent_str)
            blocks.append({
                "block_id": f"s-{s_idx:03d}",
                "char_range": [char_offset, char_offset + sent_len],
                "text": sent_str
            })
            char_offset += sent_len + 1

        full_doc_text = " ".join(doc_text_parts)

        # Convert relations
        relation_candidates = []
        for l_idx, l in enumerate(labels):
            h_idx = l.get("h")
            t_idx = l.get("t")
            r_type = l.get("r")
            evidence_sents = l.get("evidence", [])

            h_names = [v.get("name") for v in vertex_set[h_idx]] if h_idx < len(vertex_set) else ["unknown"]
            t_names = [v.get("name") for v in vertex_set[t_idx]] if t_idx < len(vertex_set) else ["unknown"]

            relation_candidates.append({
                "relation_id": f"rel-{idx:03d}-{l_idx:03d}",
                "subject_surface": h_names[0],
                "relation_surface": r_type,
                "object_surface": t_names[0],
                "evidence_sentence_indices": evidence_sents,
            })

        projected_doc = {
            "document_id": f"redocred-doc-{idx:03d}",
            "title": title,
            "document_text_len": len(full_doc_text),
            "sentence_count": len(sents),
            "relation_count": len(relation_candidates),
            "relations": relation_candidates,
            "governance": {
                "mapping_status": "candidate",
                "mapping_rule_version": "v1.0.0-redocred-relations",
                "annotator_ids": [],
                "adjudication_id": None,
                "upstream_record_hash": hashlib.sha256(json.dumps(doc, sort_keys=True).encode("utf-8")).hexdigest(),
                "license_snapshot": "CC-BY-SA-4.0"
            }
        }
        projected_docs.append(projected_doc)

    out_file = proj_dir / "projected_dev.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for d in projected_docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"Generated {len(projected_docs)} candidate Re-DocRED projections into {out_file.name}")
    return len(projected_docs)


def main():
    print("=== Staging Native Benchmark Datasets ===")
    stage_scifact()
    stage_redocred()
    print("\n=== Generating Candidate FLOSS Projections ===")
    project_scifact_candidates(limit=50)
    project_redocred_candidates(limit=20)
    print("\nBenchmark track staging complete. All projections recorded with mapping_status='candidate'.")


if __name__ == "__main__":
    main()
