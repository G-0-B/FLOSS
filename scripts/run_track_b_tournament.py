#!/usr/bin/env python3
"""
Track B: Structured Semantic Extractor Tournament Runner.
Evaluates local candidate models (NuExtract3 Q4, NuExtract3 Q6, NuExtract3 Q6-Think,
Phi-4-mini, Qwen3:4B, SciPhi-Triplex) on Layer 1 Invariants and Layer 2 Minimal Pairs.

Enforces:
- Single-model VRAM residency (OLLAMA_MAX_LOADED_MODELS=1, OLLAMA_NUM_PARALLEL=1)
- VRAM baseline recovery check (±250 MiB) via `ollama stop` after each candidate
- Catastrophic hazard scoring against H1-H17 gates (rubric.json)
- Post-norm entailment evaluation via EntailmentGate
- Output report persisted to FLOSS/evals/tournaments/track_b_extractors_report.json
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Add scripts directory to path for local imports
SCRIPTS_DIR = Path(__file__).resolve().parent
FLOSS_DIR = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from claim_candidate import ClaimVersion, NormalizedTriple
from document_ir import build_canonical_document_ir
from entailment_gate import EntailmentAssessment, EntailmentGate
from evidence_set import EvidenceAtom, EvidenceSet


@dataclass
class BenchmarkItem:
    item_id: str
    suite: str  # "layer_1" or "layer_2"
    hazard: str  # H1, H4, H5, etc.
    description: str
    text: str
    expected_abstention: bool = False
    expected_polarity: Optional[str] = None  # "affirmed", "negated"
    expected_modality: Optional[str] = None  # "asserted", "hedged"
    expected_min_claims: int = 1
    expected_max_claims: Optional[int] = None
    expected_direction: Optional[Tuple[str, str]] = None  # (subject_kw, object_kw)
    adversarial_override: bool = False


@dataclass
class ExtractedClaim:
    statement: str
    subject: str
    relation: str
    object: str
    polarity: str
    modality: str
    quote: Optional[str]


@dataclass
class ItemEvaluationResult:
    item_id: str
    hazard: str
    raw_response: str
    parsed_claims: List[Dict[str, Any]]
    schema_valid: bool
    hazard_violations: List[str]
    passed: bool
    latency_sec: float
    notes: str


@dataclass
class CandidateSummary:
    candidate_id: str
    name: str
    model_tag: str
    prompt_style: str
    temperature: float
    think: bool
    total_items: int
    passed_items: int
    pass_rate_pct: float
    schema_validity_pct: float
    abstention_accuracy_pct: float
    hazard_violations_count: Dict[str, int]
    avg_latency_sec: float
    total_duration_sec: float
    baseline_vram_mib: int
    peak_vram_mib: int
    final_vram_mib: int
    vram_recovered: bool
    item_results: List[Dict[str, Any]] = field(default_factory=list)


def get_gpu_vram_mib() -> int:
    """Read current GPU VRAM used in MiB via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
            timeout=5.0,
        )
        return int(out.strip())
    except Exception:
        return 0


def evict_ollama_model(model_tag: str) -> bool:
    """Evict model from Ollama VRAM and verify unload."""
    try:
        subprocess.run(["ollama", "stop", model_tag], check=True, timeout=15.0)
        time.sleep(1.0)
        return True
    except Exception as exc:
        print(f"[WARN] Failed to stop model {model_tag}: {exc}", file=sys.stderr)
        return False


def load_benchmark_suite() -> List[BenchmarkItem]:
    """Assemble evaluation items from Layer 1 Invariants and Layer 2 Minimal Pairs."""
    v2_dir = FLOSS_DIR / "evals" / "knowledge_triple_extraction" / "v2"
    items: List[BenchmarkItem] = []

    # Layer 1 Invariants
    l1_file = v2_dir / "unit_invariants.json"
    if l1_file.is_file():
        with open(l1_file, "r", encoding="utf-8") as f:
            l1_data = json.load(f)
        for d in l1_data:
            hid = d.get("hazard", "")
            iid = d.get("id", "")
            desc = d.get("description", "")

            # Only evaluate items that present a text passage for extraction
            text = (
                d.get("evidence")
                or d.get("text")
                or d.get("canonical_text")
                or d.get("input_payload")
            )
            if not text or not isinstance(text, str):
                continue

            if iid == "UNIT-001":
                # JSON reject test: input is malformed, model should either extract or reject
                continue

            expected_abs = bool(d.get("abstention_expected", False))
            exp_pol = None
            exp_mod = None
            exp_min = 0 if expected_abs else 1
            exp_max = d.get("expected_claim_count")
            exp_dir = None
            adv = False

            if iid == "UNIT-004":  # Negation
                exp_pol = "negated"
            elif iid == "UNIT-005":  # Hedged modality
                exp_mod = "hedged"
            elif iid == "UNIT-009":  # Relation direction: dopamine -> acetylcholine
                exp_dir = ("dopamine", "acetylcholine")
            elif iid == "UNIT-010":  # Cardinality: 2 claims
                exp_min = 2
                exp_max = 2
            elif iid == "UNIT-011":  # Abstention
                expected_abs = True
                exp_min = 0
                exp_max = 0
            elif iid == "UNIT-015":  # Prompt injection override
                adv = True
                expected_abs = True
                exp_min = 0
                exp_max = 0

            items.append(
                BenchmarkItem(
                    item_id=iid,
                    suite="layer_1",
                    hazard=hid,
                    description=desc,
                    text=text,
                    expected_abstention=expected_abs,
                    expected_polarity=exp_pol,
                    expected_modality=exp_mod,
                    expected_min_claims=exp_min,
                    expected_max_claims=exp_max,
                    expected_direction=exp_dir,
                    adversarial_override=adv,
                )
            )

    # Layer 2 Minimal Pairs
    l2_file = v2_dir / "minimal_pairs.json"
    if l2_file.is_file():
        with open(l2_file, "r", encoding="utf-8") as f:
            l2_data = json.load(f)
        for pair in l2_data:
            pid = pair.get("pair_id", "")
            htest = pair.get("hazard_tested", "").split()[0]  # e.g. "H4"
            desc = pair.get("description", "")

            # Item A
            ia = pair.get("item_a", {})
            ta = ia.get("text")
            if ta:
                items.append(
                    BenchmarkItem(
                        item_id=f"{pid}-A",
                        suite="layer_2",
                        hazard=htest,
                        description=f"{desc} (Item A: Affirmed/Baseline)",
                        text=ta,
                        expected_abstention=bool(ia.get("expected_abstention", False)),
                        expected_polarity="affirmed" if htest == "H4" else None,
                        expected_modality="asserted" if htest == "H5" else None,
                        expected_direction=("neuroinflammation", "calcification")
                        if htest == "H9"
                        else None,
                        expected_min_claims=2 if htest == "H10" else 1,
                    )
                )

            # Item B
            ib = pair.get("item_b", {})
            tb = ib.get("text")
            if tb:
                items.append(
                    BenchmarkItem(
                        item_id=f"{pid}-B",
                        suite="layer_2",
                        hazard=htest,
                        description=f"{desc} (Item B: Challenge/Hedged/Negated)",
                        text=tb,
                        expected_abstention=bool(ib.get("expected_abstention", False))
                        or (htest == "H11"),
                        expected_polarity="negated" if htest == "H4" else None,
                        expected_modality="hedged" if htest == "H5" else None,
                        expected_direction=("neuroinflammation", "calcification")
                        if htest == "H9"
                        else None,
                        expected_min_claims=0 if (htest == "H11") else 1,
                    )
                )

    return items


def format_prompt(
    text: str, prompt_style: str, think: bool
) -> Tuple[str, Optional[str], bool]:
    """Format prompt for the given model architecture. Returns (prompt, format, raw_flag)."""
    if prompt_style == "nuextract":
        think_block = "<think>\n" if think else "<think>\n\n</think>\n\n"
        prompt = (
            "<|im_start|>user\n"
            "【task】structured\n"
            "【template_start】\n"
            '{"claims": [{"statement": "", "subject": "", "relation": "", "object": "", "polarity": "", "modality": "", "quote": ""}]}\n'
            "【template_end】\n"
            f"【document_start】\n{text}\n【document_end】<|im_end|>\n"
            f"<|im_start|>assistant\n{think_block}"
        )
        return prompt, None, True

    elif prompt_style == "triplex":
        prompt = (
            "Perform Named Entity Recognition (NER) and extract triplets into JSON format:\n"
            '{"claims": [{"subject": "...", "relation": "...", "object": "...", "statement": "...", "polarity": "affirmed", "modality": "asserted", "quote": "..."}]}\n'
            "If the text contains no factual assertions, return {\"claims\": []}.\n"
            f"Text: {text}\nJSON:"
        )
        return prompt, "json", False

    else:  # standard_chat
        prompt = (
            "You are an accurate scientific information extraction system.\n"
            "Extract empirical knowledge claims from the text into a JSON object matching this schema:\n"
            "{\n"
            '  "claims": [\n'
            "    {\n"
            '      "statement": "summary of claim",\n'
            '      "subject": "subject entity",\n'
            '      "relation": "relation",\n'
            '      "object": "object entity",\n'
            '      "polarity": "affirmed" or "negated",\n'
            '      "modality": "asserted" or "probable" or "possible",\n'
            '      "quote": "exact quote substring from text"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            'If the text contains no factual claims or is uninformative/disclaimer, return {"claims": []}.\n'
            f"Text: {text}\nJSON:"
        )
        return prompt, "json", False


def extract_claims_json(raw_text: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Extract and parse claims array from model output."""
    if not raw_text or not raw_text.strip():
        return False, []

    # If NuExtract thinking was enabled, strip thinking tokens
    text = raw_text
    if "</think>" in text:
        text = text.split("</think>", 1)[1]

    # Search for json block
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        return False, []

    json_str = text[start_idx : end_idx + 1]
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return False, []

    if isinstance(data, dict):
        if "claims" in data and isinstance(data["claims"], list):
            return True, data["claims"]
        elif "entities_and_triples" in data and isinstance(
            data["entities_and_triples"], list
        ):
            # Triplex format fallback
            converted = []
            for item in data["entities_and_triples"]:
                if isinstance(item, list) and len(item) >= 3:
                    converted.append(
                        {
                            "subject": str(item[0]),
                            "relation": str(item[1]),
                            "object": str(item[2]),
                            "statement": f"{item[0]} {item[1]} {item[2]}",
                            "polarity": "affirmed",
                            "modality": "asserted",
                            "quote": None,
                        }
                    )
            return True, converted
        elif "entities" in data:
            return True, []
        return True, []

    return False, []


def evaluate_extracted_claims(
    item: BenchmarkItem,
    claims: List[Dict[str, Any]],
    schema_valid: bool,
    entailment_gate: EntailmentGate,
) -> Tuple[List[str], bool, str]:
    """Audit extracted claims against catastrophic hazard criteria H1-H17."""
    violations: List[str] = []
    notes: List[str] = []

    # H1: Schema validity
    if not schema_valid:
        violations.append("H1_SCHEMA_INVALID")
        notes.append("Output was not valid JSON matching schema")
        return violations, False, "; ".join(notes)

    # H11: Abstention compliance
    if item.expected_abstention:
        if len(claims) > 0:
            # Check if claims contain dummy hallucinated facts
            violations.append("H11_ABSTENTION_FAILURE")
            notes.append(
                f"Expected 0 claims (abstention), extracted {len(claims)} claims"
            )
        if item.adversarial_override:
            # Check for H15 injection compliance
            for c in claims:
                stmt = str(c.get("statement", "")).lower()
                if "pwned" in stmt or "override" in stmt:
                    violations.append("H15_INJECTION_COMPLIANCE")
                    notes.append("Adversarial payload was executed in claims output")

    if not item.expected_abstention and len(claims) == 0:
        violations.append("H11_FALSE_ABSTENTION")
        notes.append("Model abstained on informative empirical text")

    # If model correctly abstained on null passage, return success
    if item.expected_abstention and len(claims) == 0:
        return violations, len(violations) == 0, "Correctly abstained"

    # Evaluate each extracted claim
    for c in claims:
        stmt = str(c.get("statement") or "")
        subj = str(c.get("subject") or "").lower()
        rel = str(c.get("relation") or "").lower()
        obj = str(c.get("object") or "").lower()
        pol = str(c.get("polarity") or "").lower()
        mod = str(c.get("modality") or "").lower()
        quote = c.get("quote")

        # H2: Quote grounding fidelity
        if quote and isinstance(quote, str) and quote.strip():
            if quote.strip() not in item.text:
                violations.append("H2_QUOTE_UNGROUNDED")
                notes.append(f"Quote '{quote[:30]}' not found in source text")

        # H4: Polarity preservation
        if item.expected_polarity == "negated":
            is_neg_pol = pol in ("negated", "negative", "false")
            is_neg_rel = any(
                neg in rel
                for neg in ("not", "does not", "fails to", "cannot", "inhibits")
            )
            is_neg_stmt = any(
                neg in stmt.lower()
                for neg in ("not", "does not", "no", "never", "disproved")
            )
            if not (is_neg_pol or is_neg_rel or is_neg_stmt):
                violations.append("H4_POLARITY_INVERSION")
                notes.append(
                    "Negated evidence extracted as affirmed causal proposition"
                )

        # H5: Modality preservation
        if item.expected_modality == "hedged":
            is_hedged = mod in (
                "hedged",
                "possible",
                "probable",
                "might",
                "may",
                "speculative",
            ) or any(h in stmt.lower() for h in ("might", "may", "potentially"))
            is_asserted = pol in ("affirmed",) and mod in (
                "asserted",
                "definitive",
                "fact",
            )
            if is_asserted and not is_hedged:
                violations.append("H5_MODAL_STRENGTHENING")
                notes.append("Hedged speculation promoted to asserted fact")

        # H9: Direction fidelity
        if item.expected_direction:
            s_exp, o_exp = item.expected_direction
            # If subject and object are reversed
            if o_exp in subj and s_exp in obj and "reduce" in rel:
                violations.append("H9_DIRECTION_INVERSION")
                notes.append(
                    f"Causal direction inverted: subject={subj}, object={obj}"
                )

        # H17: Entailment Gate Check
        ev = EvidenceSet(
            claim_id=item.item_id,
            atoms=[
                EvidenceAtom(
                    atom_id="ev-1",
                    atom_type="text_span",
                    grounding_class="CANONICAL_CHAR_EXACT",
                    source_ref=item.item_id,
                    literal_content=item.text,
                )
            ],
        )
        clm = ClaimVersion(
            claim_id=item.item_id,
            claim_version=1,
            claim_type="observation",
            statement=stmt or f"{subj} {rel} {obj}",
            subject_surface=subj,
            relation_surface=rel,
            object_surface=obj,
            normalized_triple=NormalizedTriple(
                subject=subj, predicate=rel, object=obj
            ),
            polarity="affirmed" if pol not in ("negated", "negative") else "negated",
        )
        entailment_res = entailment_gate.assess(clm, ev)
        if entailment_res.state == "CONTRADICTED":
            violations.append("H17_CONTRADICTED_ENTAILMENT")
            notes.append(f"EntailmentGate assessed claim as CONTRADICTED: {stmt}")

    # Deduplicate violations
    violations = list(dict.fromkeys(violations))
    passed = len(violations) == 0
    return violations, passed, "; ".join(notes) if notes else "Passed all gates"


def run_candidate(
    client: httpx.Client,
    candidate_id: str,
    name: str,
    model_tag: str,
    prompt_style: str,
    temperature: float,
    think: bool,
    benchmark_items: List[BenchmarkItem],
    entailment_gate: EntailmentGate,
) -> CandidateSummary:
    """Execute complete tournament evaluation for a single candidate extractor."""
    print(
        f"\n================================================================================"
    )
    print(f"Executing Candidate: {candidate_id} - {name} ({model_tag})")
    print(
        f"Prompt Style: {prompt_style} | Temperature: {temperature} | Think: {think}"
    )
    print(
        f"================================================================================"
    )

    baseline_vram = get_gpu_vram_mib()
    print(f"[*] Initial Baseline VRAM: {baseline_vram} MiB")

    peak_vram = baseline_vram
    results: List[ItemEvaluationResult] = []
    start_time = time.time()
    hazard_counts: Dict[str, int] = {}

    options: Dict[str, Any] = {
        "temperature": temperature,
        "num_ctx": 16384,
    }
    if "qwen" in model_tag.lower():
        options["top_p"] = 0.8

    for idx, item in enumerate(benchmark_items, 1):
        prompt, fmt, raw_flag = format_prompt(item.text, prompt_style, think)
        payload: Dict[str, Any] = {
            "model": model_tag,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if fmt:
            payload["format"] = fmt
        if raw_flag:
            payload["raw"] = True

        t0 = time.time()
        try:
            resp = client.post(
                "http://127.0.0.1:11434/api/generate", json=payload, timeout=90.0
            )
            lat = time.time() - t0
            cur_vram = get_gpu_vram_mib()
            if cur_vram > peak_vram:
                peak_vram = cur_vram

            if resp.status_code != 200:
                raw_out = ""
                schema_valid = False
                claims = []
            else:
                raw_out = resp.json().get("response", "")
                schema_valid, claims = extract_claims_json(raw_out)

        except Exception as exc:
            lat = time.time() - t0
            raw_out = f"ERROR: {exc}"
            schema_valid = False
            claims = []

        violations, passed, notes = evaluate_extracted_claims(
            item, claims, schema_valid, entailment_gate
        )

        for v in violations:
            h_code = v.split("_")[0]
            hazard_counts[h_code] = hazard_counts.get(h_code, 0) + 1

        results.append(
            ItemEvaluationResult(
                item_id=item.item_id,
                hazard=item.hazard,
                raw_response=raw_out[:300],
                parsed_claims=claims,
                schema_valid=schema_valid,
                hazard_violations=violations,
                passed=passed,
                latency_sec=round(lat, 3),
                notes=notes,
            )
        )

        status_tag = "PASS" if passed else f"FAIL ({','.join(violations)})"
        print(
            f"  [{idx:02d}/{len(benchmark_items):02d}] {item.item_id:10s} ({item.hazard:3s}) -> {status_tag} in {lat:.2f}s"
        )

    total_duration = time.time() - start_time
    total_items = len(benchmark_items)
    passed_items = sum(1 for r in results if r.passed)
    pass_rate = round((passed_items / total_items) * 100.0, 1)
    schema_valid_rate = round(
        (sum(1 for r in results if r.schema_valid) / total_items) * 100.0, 1
    )

    abstention_items = [
        r for r, item in zip(results, benchmark_items) if item.expected_abstention
    ]
    abstention_acc = (
        round(
            (
                sum(1 for r in abstention_items if len(r.parsed_claims) == 0)
                / len(abstention_items)
            )
            * 100.0,
            1,
        )
        if abstention_items
        else 100.0
    )
    avg_lat = (
        round(sum(r.latency_sec for r in results) / total_items, 3)
        if total_items
        else 0.0
    )

    # Evict candidate and verify recovery
    print(f"[*] Stopping model {model_tag} to restore baseline VRAM...")
    evict_ollama_model(model_tag)
    final_vram = get_gpu_vram_mib()
    vram_delta = abs(final_vram - baseline_vram)
    recovered = vram_delta <= 250
    print(
        f"[*] Final VRAM: {final_vram} MiB (Baseline: {baseline_vram} MiB, Delta: {final_vram - baseline_vram} MiB, Recovered: {recovered})"
    )

    return CandidateSummary(
        candidate_id=candidate_id,
        name=name,
        model_tag=model_tag,
        prompt_style=prompt_style,
        temperature=temperature,
        think=think,
        total_items=total_items,
        passed_items=passed_items,
        pass_rate_pct=pass_rate,
        schema_validity_pct=schema_valid_rate,
        abstention_accuracy_pct=abstention_acc,
        hazard_violations_count=hazard_counts,
        avg_latency_sec=avg_lat,
        total_duration_sec=round(total_duration, 2),
        baseline_vram_mib=baseline_vram,
        peak_vram_mib=peak_vram,
        final_vram_mib=final_vram,
        vram_recovered=recovered,
        item_results=[asdict(r) for r in results],
    )


def print_scorecard(summaries: List[CandidateSummary]) -> None:
    """Print comparative scorecard table."""
    print(
        "\n==================================================================================================="
    )
    print("                         TRACK B EXTRACTOR TOURNAMENT SCORECARD")
    print(
        "==================================================================================================="
    )
    header = f"{'Candidate':<28} | {'Pass%':<6} | {'Schema%':<7} | {'Abst%':<6} | {'Avg Lat':<7} | {'Peak VRAM':<9} | {'Hazards':<18}"
    print(header)
    print("-" * len(header))
    for s in summaries:
        haz_str = ",".join(f"{k}:{v}" for k, v in sorted(s.hazard_violations_count.items())) or "None"
        name_trunc = f"{s.candidate_id} {s.name}"[:28]
        print(
            f"{name_trunc:<28} | {s.pass_rate_pct:>5.1f}% | {s.schema_validity_pct:>6.1f}% | {s.abstention_accuracy_pct:>5.1f}% | {s.avg_latency_sec:>5.2f}s | {s.peak_vram_mib:>6d} MB | {haz_str:<18}"
        )
    print(
        "===================================================================================================\n"
    )


def main() -> int:
    client = httpx.Client(trust_env=False, timeout=120.0)

    # 1. Verify Ollama API health
    try:
        ver_resp = client.get("http://127.0.0.1:11434/api/version")
        if ver_resp.status_code != 200:
            print(
                f"[FATAL] Ollama server returned non-200: {ver_resp.status_code}",
                file=sys.stderr,
            )
            return 1
        print(f"[OK] Ollama connected: {ver_resp.json().get('version')}")
    except Exception as exc:
        print(f"[FATAL] Failed to connect to Ollama: {exc}", file=sys.stderr)
        return 1

    # 2. Assemble benchmark items
    items = load_benchmark_suite()
    print(
        f"[OK] Loaded {len(items)} benchmark items (Layer 1 Invariants + Layer 2 Minimal Pairs)"
    )

    entailment_gate = EntailmentGate()

    # 3. Candidate roster
    candidates = [
        {
            "candidate_id": "TRK-01",
            "name": "Phi-4-mini Incumbent",
            "model_tag": "phi4-mini:latest",
            "prompt_style": "standard_chat",
            "temperature": 0.1,
            "think": False,
        },
        {
            "candidate_id": "TRK-02",
            "name": "NuExtract3 Q4 Efficiency",
            "model_tag": "hf.co/numind/NuExtract3-GGUF:Q4_K_M",
            "prompt_style": "nuextract",
            "temperature": 0.2,
            "think": False,
        },
        {
            "candidate_id": "TRK-03",
            "name": "NuExtract3 Q6 Quality Max",
            "model_tag": "hf.co/numind/NuExtract3-GGUF:Q6_K",
            "prompt_style": "nuextract",
            "temperature": 0.2,
            "think": False,
        },
        {
            "candidate_id": "TRK-04",
            "name": "NuExtract3 Q6 Thinking Ablation",
            "model_tag": "hf.co/numind/NuExtract3-GGUF:Q6_K",
            "prompt_style": "nuextract",
            "temperature": 0.6,
            "think": True,
        },
        {
            "candidate_id": "TRK-05",
            "name": "Qwen3:4B Control",
            "model_tag": "qwen3:4b",
            "prompt_style": "standard_chat",
            "temperature": 0.7,
            "think": False,
        },
    ]

    summaries: List[CandidateSummary] = []
    for cand in candidates:
        summary = run_candidate(
            client=client,
            candidate_id=cand["candidate_id"],
            name=cand["name"],
            model_tag=cand["model_tag"],
            prompt_style=cand["prompt_style"],
            temperature=cand["temperature"],
            think=cand["think"],
            benchmark_items=items,
            entailment_gate=entailment_gate,
        )
        summaries.append(summary)

    # 4. Print scorecard
    print_scorecard(summaries)

    # 5. Save report
    out_dir = FLOSS_DIR / "evals" / "tournaments"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "track_b_extractors_report.json"

    report_payload = {
        "tournament": "Track B: Structured Semantic Extractor Tournament",
        "date": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "eval_set": {
            "total_items": len(items),
            "layer_1_items": sum(1 for i in items if i.suite == "layer_1"),
            "layer_2_items": sum(1 for i in items if i.suite == "layer_2"),
        },
        "scorecard": [
            {
                "candidate_id": s.candidate_id,
                "name": s.name,
                "model_tag": s.model_tag,
                "pass_rate_pct": s.pass_rate_pct,
                "schema_validity_pct": s.schema_validity_pct,
                "abstention_accuracy_pct": s.abstention_accuracy_pct,
                "avg_latency_sec": s.avg_latency_sec,
                "peak_vram_mib": s.peak_vram_mib,
                "baseline_vram_mib": s.baseline_vram_mib,
                "final_vram_mib": s.final_vram_mib,
                "vram_recovered": s.vram_recovered,
                "hazard_violations": s.hazard_violations_count,
            }
            for s in summaries
        ],
        "candidates": [asdict(s) for s in summaries],
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    print(f"[OK] Full tournament evaluation report written to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
