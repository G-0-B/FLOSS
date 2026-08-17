"""Major Consolidation Sweep Script

This script reads all disparate markdown documents (intake_raw, archive, context packets),
analyzes them methodically using an LLM (Llama 3.3 70B), and synthesizes them into 
a living, evolving reference corpus `docs/research/Holistic_Vision.md`.

It tracks alignment, contradictions, assumptions, and citations.
"""

import os
import glob
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
import litellm

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
ENV_PATH = REPO_ROOT / ".env"
VISION_DOC = REPO_ROOT / "docs" / "research" / "Holistic_Vision.md"
PROCESSED_LOG = REPO_ROOT / "docs" / "research" / "consolidation_processed.txt"


class ExtractionStatus(Enum):
    SUCCESS = "success"
    FILE_READ_FAILURE = "file_read_failure"
    LLM_FAILURE = "llm_failure"
    RATE_LIMIT_FAILURE = "rate_limit_failure"


@dataclass(frozen=True)
class ExtractionResult:
    status: ExtractionStatus
    insights: str


def configure_togetherai_api_key() -> None:
    """Preserve the canonical key, falling back only to a non-empty legacy key."""
    if "TOGETHERAI_API_KEY" not in os.environ:
        legacy_key = os.environ.get("togetherai_API_key")
        if legacy_key:
            os.environ["TOGETHERAI_API_KEY"] = legacy_key

def load_processed_files() -> set[str]:
    if not PROCESSED_LOG.exists():
        return set()
    return set(PROCESSED_LOG.read_text(encoding="utf-8").splitlines())

def mark_processed(filepath: str):
    with PROCESSED_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{filepath}\n")

def get_target_files() -> list[Path]:
    target_dirs = [
        WORKSPACE_ROOT / "FLOSSI0ULLK_Context_Continuation_Packet_*.md",
        REPO_ROOT / "docs" / "research" / "intake_raw" / "**" / "*.md",
        REPO_ROOT / "archive" / "intake_raw" / "**" / "*.md",
        REPO_ROOT / "docs" / "architecture" / "*.md",
    ]
    files = []
    for pattern in target_dirs:
        for match in glob.glob(str(pattern), recursive=True):
            files.append(Path(match))
    return sorted(list(set(files)))

def extract_and_synthesize(file_path: Path, model: str) -> ExtractionResult:
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return ExtractionResult(
            ExtractionStatus.FILE_READ_FAILURE,
            f"Error reading file: {e}",
        )

    chunk_size = 14000
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
    if not chunks:
        return ExtractionResult(ExtractionStatus.SUCCESS, "No content found.")

    all_insights = []
    status = ExtractionStatus.SUCCESS
    for idx, chunk in enumerate(chunks):
        prompt = f"""You are the FLOSSI0ULLK Consolidator AI.
Analyze the following document chunk and extract knowledge for the holistic overarching vision.

Target Document: {file_path.name} (Chunk {idx + 1} of {len(chunks)})

Your task is to extract:
1. Core Paradigms & Alignments (Where does this align with the overarching CCES / Holochain / Biomimetic vision?)
2. Competing Architectures & Contradictions
3. Unknowns & Assumptions (Be completely honest)
4. Key Citations / Mentions

Be highly dense and structured.

---
DOCUMENT CONTENT CHUNK:
{chunk}
"""
        try:
            if os.environ.get("FLOSS_MODEL_BACKEND", "litellm") == "omniroute":
                from packages.omniroute_client import completion as _omni

                text = _omni(model, [{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.1)
            else:
                response = litellm.completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000,
                )
                text = response.choices[0].message.content.strip()
            all_insights.append(text)
        except Exception as e:
            all_insights.append(f"LLM Extraction Failed for chunk {idx + 1}: {e}")
            is_rate_limit = (
                type(e).__name__ == "RateLimitError"
                or getattr(e, "status_code", None) == 429
            )
            if is_rate_limit:
                return ExtractionResult(
                    ExtractionStatus.RATE_LIMIT_FAILURE,
                    "\n\n".join(all_insights),
                )
            elif status is ExtractionStatus.SUCCESS:
                status = ExtractionStatus.LLM_FAILURE

        if idx < len(chunks) - 1:
            time.sleep(3) # Groq rate limits

    return ExtractionResult(status, "\n\n".join(all_insights))

def append_to_vision(file_path: Path, insights: str):
    header = f"## Analysis of `{file_path.name}`\n**Path:** `{file_path.relative_to(WORKSPACE_ROOT)}`\n\n"
    mode = "a" if VISION_DOC.exists() else "w"
    
    if mode == "w":
        init_header = "# FLOSSI0ULLK Holistic Vision Synthesis\n\n*A living reference corpus of always evolving information.* \n\n"
        with VISION_DOC.open(mode, encoding="utf-8") as f:
            f.write(init_header)
            
    with VISION_DOC.open("a", encoding="utf-8") as f:
        f.write(header + insights + "\n\n---\n\n")

def main():
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
        
    configure_togetherai_api_key()
    model = "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo"
    all_files = get_target_files()
    processed = load_processed_files()
    
    pending = [f for f in all_files if str(f.resolve()) not in processed]
    
    print(f"Total files found: {len(all_files)}")
    print(f"Already processed: {len(processed)}")
    print(f"Pending to process: {len(pending)}")
    
    if not pending:
        print("All caught up!")
        return
        
    limit = len(pending)
    to_process = pending[:limit]
    
    for fp in to_process:
        print(f"Processing: {fp.name} ...")
        result = extract_and_synthesize(fp, model)
        
        if result.status is ExtractionStatus.RATE_LIMIT_FAILURE:
            print("Rate limit hit. Waiting 60s...")
            time.sleep(60)
            result = extract_and_synthesize(fp, model)
            if result.status is not ExtractionStatus.SUCCESS:
                print(f"Skipping {fp.name} after failed retry.")
                continue
        elif result.status is not ExtractionStatus.SUCCESS:
            print(f"Skipping {fp.name} due to extraction failure.")
            continue
                
        append_to_vision(fp, result.insights)
        mark_processed(str(fp.resolve()))
        print(f"Successfully processed and appended {fp.name} to Holistic Vision.")
        time.sleep(5) # Delay between files

if __name__ == "__main__":
    main()
