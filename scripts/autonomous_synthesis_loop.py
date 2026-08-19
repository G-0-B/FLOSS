"""Autonomous Knowledge Synthesis Loop (Human-in-the-Loop).

This background daemon scans `docs/research/`, `docs/vision/`, and `_reference/`
for unprocessed markdown files. It uses an LLM to perform "Fractal Semantic Extraction".

To prevent LLM hallucinations from polluting the immutable source chain, this script
operates in two phases:
1. Extraction Mode (Default): Writes insights to `docs/knowledge_log/staging/` for human review.
2. Commit Mode (`--commit`): Reads verified drafts from `staging/`, appends them to the 
   local Holochain source chain, and regenerates the `APPEND_ONLY_KNOWLEDGE_LOG.md`.

Usage:
    python FLOSS/scripts/autonomous_synthesis_loop.py [--dry-run] [--model groq/llama-3.1-8b-instant]
    python FLOSS/scripts/autonomous_synthesis_loop.py --commit
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

import litellm

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
ENV_PATH = REPO_ROOT / ".env"
LOG_DIR = REPO_ROOT / "docs" / "knowledge_log"
STAGING_DIR = LOG_DIR / "staging"
LOG_FILE = LOG_DIR / "APPEND_ONLY_KNOWLEDGE_LOG.md"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import Action, append_action  # noqa: E402
from packages.source_chain.cell import CellDirectory


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _get_files_to_process() -> list[Path]:
    """Gather all markdown files from the target directories."""
    target_dirs = [
        REPO_ROOT / "docs" / "research",
        REPO_ROOT / "docs" / "vision",
        WORKSPACE_ROOT / "_reference",
    ]
    files = []
    for d in target_dirs:
        if d.exists() and d.is_dir():
            files.extend(d.rglob("*.md"))
    return sorted(files)


def _get_processed_files(cell: CellDirectory) -> set[str]:
    """Read the source chain to find all files already processed."""
    processed = set()
    entries = cell.read_chain(limit=None)
    for entry in entries:
        if entry.get("type") == "knowledge_distillation":
            file_path = entry.get("content", {}).get("file_path")
            if file_path:
                processed.add(file_path)
    return processed


def extract_semantics(file_path: Path, model: str) -> str:
    """Use LiteLLM to extract high-ROI fractal semantics from the file in chunks."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"

    chunk_size = 12000
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
    if not chunks:
        return "No content found."

    all_insights = []

    for idx, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"  -> Processing chunk {idx + 1}/{len(chunks)}...")

        prompt = f"""You are the FLOSSI0ULLK Semantic Extraction node.
Analyze the following document chunk and extract the highest-leverage insights.

Target Document: {file_path.name} (Chunk {idx + 1} of {len(chunks)})

Perform a "Fractal Semantic Extraction":
1. Key Paradigm Shifts / Vision
2. Architectural Constraints or Invariants
3. Missing links or open contradictions

Format your response in concise Markdown. Be brief but highly dense with information.

---
DOCUMENT CONTENT CHUNK:
{chunk}
"""
        try:
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500,
            )
            all_insights.append(f"### Chunk {idx + 1}/{len(chunks)}\n{response.choices[0].message.content.strip()}")
        except Exception as e:
            all_insights.append(f"LLM Extraction Failed for chunk {idx + 1}: {e}")

        # Strict rate limit backoff between chunks for Groq, faster for others
        if idx < len(chunks) - 1:
            if "groq/" in model.lower():
                time.sleep(25)
            else:
                time.sleep(3)

    return "\n\n---\n\n".join(all_insights)


def stage_draft(file_path: Path, model: str, insights: str) -> Path:
    """Write the extraction to the staging directory for human review."""
    started_at = datetime.now(timezone.utc).isoformat()
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create a safe filename for the draft
    safe_name = file_path.name.replace(" ", "_").replace(".md", "")
    draft_path = STAGING_DIR / f"{safe_name}_draft.json"
    
    payload = {
        "file_path": str(file_path.resolve()),
        "model": model,
        "staged_at": utc_stamp(),
        "insights": insights
    }
    
    draft_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Staged draft for review: {draft_path}")
    ended_at = datetime.now(timezone.utc).isoformat()
    try:
        duration = (
            datetime.fromisoformat(ended_at) - datetime.fromisoformat(started_at)
        ).total_seconds()
    except ValueError:
        duration = 0.0
    append_action(Action(
        action_id=f"synthesis-{safe_name}-{payload['staged_at']}",
        kind="knowledge_synthesis",
        harness="autonomous_synthesis_loop.py",
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=round(duration, 3),
        success=True,
        inputs={
            "source_file": str(file_path.resolve()),
            "model": model,
        },
        outputs={
            "draft_path": str(draft_path),
            "insights_chars": len(insights),
        },
        llm_calls=[{
            "model": model,
            "provider": "litellm",
            "prompt_hash": "",
            "response_hash": "",
            "duration_seconds": 0.0,
            "error": None,
        }],
        staging_paths=[str(draft_path)],
    ))
    return draft_path


def commit_staged_drafts(cell: CellDirectory, dry_run: bool) -> None:
    """Read verified drafts from staging, append to source chain, and clean up."""
    if not STAGING_DIR.exists():
        print("Staging directory does not exist. Nothing to commit.")
        return
        
    draft_files = list(STAGING_DIR.glob("*_draft.json"))
    if not draft_files:
        print("No drafts found in staging. Nothing to commit.")
        return
        
    print(f"Found {len(draft_files)} drafts in staging.")
    
    for draft_path in draft_files:
        print(f"\nCommitting: {draft_path.name}")
        try:
            payload = json.loads(draft_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Failed to read draft {draft_path.name}: {e}")
            continue
            
        if dry_run:
            print("[DRY RUN] Would commit draft to source chain and delete draft file.")
            continue
            
        entry_hash = cell.append_entry(
            entry_type="knowledge_distillation",
            author_did="did:key:synthesis-loop",
            content=payload
        )
        print(f"Appended entry: {entry_hash}")
        
        # Delete the draft after successful commit
        draft_path.unlink()
        print(f"Deleted staged draft: {draft_path.name}")
        
    if not dry_run:
        regenerate_markdown_log(cell)


def regenerate_markdown_log(cell: CellDirectory) -> None:
    """Regenerate the human-readable APPEND_ONLY_KNOWLEDGE_LOG.md from the chain."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    entries = cell.read_chain(limit=None)
    # Filter for knowledge_distillation and reverse to chronological order
    distillations = [e for e in entries if e.get("type") == "knowledge_distillation"]
    distillations.reverse()
    
    lines = [
        "# Continuous Knowledge Distillation Log",
        "",
        "> [!NOTE]",
        "> This log is auto-generated by `autonomous_synthesis_loop.py`.",
        "> It reads from the immutable Holochain source chain. Do not edit manually.",
        "",
        f"**Last Updated:** {utc_stamp()}",
        f"**Total Extractions:** {len(distillations)}",
        "",
        "---",
        "",
    ]
    
    for entry in distillations:
        content = entry.get("content", {})
        file_path = content.get("file_path", "Unknown")
        model = content.get("model", "Unknown")
        insights = content.get("insights", "No insights recorded.")
        timestamp = entry.get("timestamp", "Unknown time")
        
        lines.extend([
            f"## File: `{Path(file_path).name}`",
            f"- **Timestamp:** {timestamp}",
            f"- **Extracted by:** `{model}`",
            f"- **Source Path:** `{file_path}`",
            "",
            insights,
            "",
            "---",
            ""
        ])
        
    LOG_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nRegenerated {LOG_FILE}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Continuous Knowledge Synthesis Loop")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without modifying chain")
    parser.add_argument("--commit", action="store_true", help="Commit verified drafts from staging to the source chain")
    parser.add_argument("--model", default="groq/llama-3.1-8b-instant", help="LiteLLM model to use")
    parser.add_argument("--limit", type=int, default=5, help="Max files to process per run")
    args = parser.parse_args()

    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)

    # Map custom user API keys to LiteLLM standard environment variables
    if "aistudio_gemini_api_key" in os.environ and "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = os.environ["aistudio_gemini_api_key"]
    if "openai_omi_api_key" in os.environ and "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = os.environ["openai_omi_api_key"]
    if "togetherai_API_key" in os.environ and "TOGETHERAI_API_KEY" not in os.environ:
        os.environ["TOGETHERAI_API_KEY"] = os.environ["togetherai_API_key"]
    if "xAI_api_key" in os.environ and "XAI_API_KEY" not in os.environ:
        os.environ["XAI_API_KEY"] = os.environ["xAI_api_key"]

    dna_hash = os.environ.get("FLOSS_DNA_HASH", "0" * 64)
    base_dir = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
    cell = CellDirectory(base_dir=base_dir, dna_hash=dna_hash)

    if args.commit:
        commit_staged_drafts(cell, args.dry_run)
        return 0

    all_files = _get_files_to_process()
    processed_files = _get_processed_files(cell)
    
    # Also ignore files that are currently in staging
    staged_files = set()
    if STAGING_DIR.exists():
        for draft in STAGING_DIR.glob("*_draft.json"):
            try:
                payload = json.loads(draft.read_text(encoding="utf-8"))
                staged_files.add(payload.get("file_path"))
            except:
                pass

    pending_files = [f for f in all_files if str(f.resolve()) not in processed_files and str(f.resolve()) not in staged_files]
    
    print(f"Found {len(all_files)} total markdown files.")
    print(f"Already processed in source chain: {len(processed_files)}")
    print(f"Currently in staging: {len(staged_files)}")
    print(f"Pending processing: {len(pending_files)}")
    
    if not pending_files:
        print("No new files to process. Exiting.")
        return 0

    to_process = pending_files[:args.limit]
    print(f"\nProcessing batch of {len(to_process)} files using {args.model}...")

    for file_path in to_process:
        print(f"\nProcessing: {file_path.name}")
        if args.dry_run:
            print("[DRY RUN] Would extract semantics and write to staging.")
            continue
            
        insights = extract_semantics(file_path, args.model)
        
        if "LLM Extraction Failed" in insights:
            if "RateLimitError" in insights or "rate_limit_exceeded" in insights:
                print(f"Rate limit hit. Waiting 45 seconds before retrying...")
                time.sleep(45)
                insights = extract_semantics(file_path, args.model)
                if "LLM Extraction Failed" in insights:
                    print(f"Skipping due to persistent LLM error: {insights}")
                    continue
            else:
                print(f"Skipping due to LLM error: {insights}")
                continue

        stage_draft(file_path, args.model, insights)
        
        # Dynamic sleep between files
        if "groq/" in args.model.lower():
            time.sleep(20)
        else:
            time.sleep(3)

    if not args.dry_run:
        print("\nExtraction complete. Review the drafts in docs/knowledge_log/staging/")
        print("When verified, run with --commit to append them to the source chain.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
