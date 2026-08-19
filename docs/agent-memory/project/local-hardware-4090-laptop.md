---
id: project-local-hardware-4090-laptop
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_local_hardware_4090_laptop.md
title: User's local hardware — RTX 4090 Laptop, Ollama-ready for local model orchestration
legacy_description: Confirmed 2026-05-17 — MSI laptop with NVIDIA RTX 4090 Laptop
  GPU (16GB VRAM), Ollama 0.9.6 installed (server not yet started). Hardware comfortably
  supports up-to-32B-class models for local inference. Use for the inline reasoning
  ensemble Router role per 2026-05-17-inline-reasoning-ensemble.md.
origin_session_id: a04c9df9-7bf3-4c48-8305-871bc29b680d
---

Hardware confirmed via `nvidia-smi` on 2026-05-17:

| Component | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 4090 Laptop GPU |
| VRAM total | 16376 MiB (16 GB) |
| VRAM free at idle | ~11000 MiB (~11 GB) |
| NVIDIA driver | 596.36 |
| iGPU also present | Intel UHD Graphics (~2 GB) — normal for laptop, fine to ignore for inference |
| Ollama | 0.9.6 client installed at user level; server NOT running at the time of check (start with `ollama serve` or via Windows Service) |

**Why:** The user explicitly stated 2026-05-17 they want to set up a local model to orchestrate the inline reasoning ensemble (see `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md` §4 Local orchestrator). Earlier session-context notes (session_summary_2026-05-04 §A.3) mentioned "32GB RAM, discrete GPU, multiple disassemblies, Peltier cooling prototype" — that's now concretely specified as 4090 Laptop with 16GB VRAM. The Win32 `AdapterRAM` field returns capped 4GB due to uint32 truncation; `nvidia-smi` is the source of truth for VRAM on Windows.

**How to apply:**
- **Practical local-model size ceiling at this hardware:** ~14B at Q4_K_M comfortably (≈9 GB VRAM, fast); 32B at Q3_K_M is feasible but tight (≈14 GB VRAM, leaves little room for context). 70B is offload-only territory — works in Ollama but slow.
- **Recommended Router model:** Qwen3-14B Q4_K_M (or Qwen3-Coder-14B for code-heavy reasoning) — sweet spot for hardware. Install via `ollama pull qwen3:14b` or `ollama pull qwen3-coder:14b` (~9 GB download).
- **Occasional voter at 32B:** Qwen3-32B Q3_K_M can run as a local voter when VRAM is available, but don't make it the always-on Router — too tight on memory headroom for sustained use.
- **Ollama is already installed** — no install step needed, just `ollama serve` to start the server (or wire as a Windows Service via Servy following the same pattern as the heartbeat — see working-todo §A.1).
- **If hardware ever upgrades** (eGPU, desktop with bigger GPU), the model-size ceiling moves up correspondingly; revisit this memory at that point.
- **CPU + system RAM**: Win32 RAM query failed during the check; not measured. Likely 32 GB (per session_summary §A.3 claim). Confirm via `Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory` when relevant — affects Ollama's ability to offload layers to CPU for models exceeding VRAM.
