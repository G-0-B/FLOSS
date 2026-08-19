# High-Throughput Inference Architectures: Validating the 14,400 Daily Request Paradigm on Specialized Silicon

**Date:** February 2026
**Source:** External research report, pasted by Anthony into Claude Code session 2026-04-12
**Status:** Research reference — NOT YET IMPLEMENTED in FLOSSIØULLK
**Relates to:** `ADR-MCP-ORCHESTRATOR.md` (the LiteLLM layer this document describes is the missing piece), `Automated-Agent-Orchestration-Report_v2.0.0.md`
**Known paste artifacts:** Code samples contain OCR-style errors (`response.choices.message.content` should be `response.choices[0].message.content`; `os.environ = "gsk_..."` should be `os.environ["GROQ_API_KEY"] = "gsk_..."`). Preserved verbatim below; fix when implementing.

---

## 1. The Inference Landscape of Early 2026

The computational landscape for Artificial Intelligence in February 2026 is defined by a distinct bifurcation in hardware philosophy. For the better part of the previous decade, the Graphics Processing Unit (GPU), specifically architectures developed by NVIDIA, served as the uncontested engine of the AI revolution. From the H100 to the B200, these general-purpose parallel processors were the bedrock of both training and inference. However, as Large Language Models (LLMs) transitioned from research curiosities to ubiquitous utility layers, the economic and latency constraints of General Purpose GPUs (GPGPUs) became increasingly apparent. The user query regarding the "14,400 Requests/Day" paradigm highlights a critical market correction: the rise of specialized inference-only architectures — specifically the Language Processing Unit (LPU) developed by Groq and the Wafer-Scale Engine (WSE-3) developed by Cerebras.

This report provides an exhaustive technical analysis of the strategy to bypass traditional, rate-limited API aggregators like OpenRouter in favor of direct, high-throughput integration with Groq and Cerebras. The central thesis being examined is whether a zero-cost infrastructure can genuinely support enterprise-grade volumes — claimed to be 14,400 requests per day (RPD) with generation speeds exceeding 500 tokens per second (TPS). Our analysis confirms that not only are these figures accurate, but they also represent a fleeting "Golden Era" of subsidized inference, driven by the unique loss-leader economics of specialized hardware vendors seeking to capture developer mindshare from the CUDA ecosystem.

### 1.1 The Shift from GPU to Specialized Silicon

To understand the viability of this high-throughput architecture, one must first dissect the physical limitations it seeks to overcome. The primary bottleneck in LLM inference on traditional GPUs is not compute (FLOPS), but memory bandwidth. The auto-regressive nature of Generative Pre-trained Transformers (GPT) requires that for every token generated, the entire model's weights must be loaded from High Bandwidth Memory (HBM) into the compute cores. On an NVIDIA H100 with approximately 3.35 TB/s of bandwidth, this imposes a hard physical limit on token generation speed, typically capping single-stream performance between 100 and 200 tokens per second for large models, coupled with significant queuing latency in multi-tenant environments.

Groq and Cerebras address this "Memory Wall" through radically different architectural decisions. Groq's LPU abandons the complex caching hierarchies and dynamic schedulers of GPUs in favor of a deterministic, compiler-driven execution model. By utilizing massive amounts of on-chip SRAM, Groq eliminates the HBM bottleneck entirely for models that fit within its distributed memory fabric. This results in the "500 Tokens/Sec" performance characteristic cited in the user guide, a figure that is actually conservative for smaller models like Llama 3.1 8B, which often run at speeds approaching 1,000 TPS on LPU clusters.

Conversely, Cerebras approaches the problem with brute force integration. Rather than dicing a silicon wafer into hundreds of individual chips, Cerebras manufactures a single, wafer-scale chip (WSE-3). This monolithic architecture provides on-chip memory bandwidth measured in Petabytes per second — orders of magnitude higher than any GPU cluster. This allows Cerebras to keep massive models, such as the 70-billion parameter Llama 3.3, entirely resident on the wafer, enabling concurrent processing of thousands of requests with minimal latency degradation.

### 1.2 The "Free Tier" Economy as a Strategic Lever

The existence of a "Free Tier" offering 14,400 requests per day in 2026 is an anomaly in the cloud computing market, where compute cycles are generally commoditized and priced strictly. However, for Groq and Cerebras, these tiers serve a strategic engineering purpose. Unlike OpenAI or Anthropic, whose primary product is the model intelligence, Groq and Cerebras sell infrastructure.

The "Free Tier" acts as a massive-scale stress test for their compilers and interconnects. By allowing developers to flood their systems with diverse prompt structures (from code generation to creative writing), these companies gather invaluable telemetry on compiler edge cases, kernel utilization, and interconnect stability. This "loss leader" strategy explains why the rate limits are set so high compared to aggregators. While OpenRouter must pay for every token routed to backend providers, Groq and Cerebras own the silicon, making the marginal cost of serving a free request negligible compared to the value of the optimization data gained. This economic alignment provides the stability assurance required to recommend this setup for production-grade prototypes.

---

## 2. Technical Validation: Rate Limits and Throughput Analysis

The core of the proposed strategy relies on stacking the free tier quotas of Groq and Cerebras to achieve a combined throughput of 28,800 requests per day (or 14,400 per provider). We have rigorously verified these limits against the active system headers and documentation as of February 12, 2026.

### 2.1 Groq LPU: Precision and Constraints

Groq's API architecture is designed for speed and determinism. Upon analyzing the API response headers `x-ratelimit-limit-requests` and `x-ratelimit-limit-tokens`, we can confirm the exact operational envelope of the free tier.

**Daily Request Volume:**
The Groq API explicitly returns a header value of `14400` for `x-ratelimit-limit-requests`. This confirms the user's "14,400 Requests/Day" claim is precise. This limit resets daily at 00:00 UTC. It is crucial to note that this is a hard cap; once exhausted, the API will return a 429 status code until the reset window.

**The Token Bottleneck:**
While the request count is generous, the Tokens Per Minute (TPM) limit is the primary constraint for high-context applications. Groq sets this limit at **18,000 TPM**. In the context of the "500 Tokens/Sec" speed claim, this creates a significant synchronization challenge. At a generation speed of 500 tokens per second, a single concurrent request could theoretically consume 30,000 tokens in one minute — exceeding the rate limit by nearly double.

- **Implication:** The LPU architecture is so fast that a single user can inadvertently DDoS their own rate limit in seconds.
- **Operational Constraint:** To stay within the 18,000 TPM limit, a user can only sustain an average throughput of 300 tokens per second across the entire minute. Bursts are allowed, but sustained high-speed generation will trigger rate limiting rapidly. This makes Groq ideal for short, chat-based interactions or code completion, but less suitable for heavy document summarization or long-context RAG (Retrieval Augmented Generation) without sophisticated throttling.

### 2.2 Cerebras Wafer-Scale Cloud: The Capacity Heavyweight

Cerebras positions its developer tier as the high-capacity alternative, leveraging the massive memory bandwidth of the WSE-3.

**Daily and Minute Limits:**
Cerebras matches the 14,400 RPD limit found on Groq, effectively doubling the user's capacity when both are used in tandem. However, the critical differentiator lies in the TPM limit. Cerebras offers a **60,000 TPM** limit on its free tier.

- **Comparative Advantage:** This is more than 3x the capacity of Groq.
- **Burst Tolerance:** The higher TPM allows for significantly larger context windows or more aggressive parallelization. For a RAG application sending 4,000 tokens of context per request, Cerebras can handle approximately 15 requests per minute, whereas Groq would be limited to 4.

**The Daily Token Cap:**
Unlike Groq, which has an implicit daily token limit derived from its minute limits (18,000 * 60 * 24 ≈ 25.9 million), Cerebras imposes an explicit **1,000,000 Daily Token cap**. This is a critical nuance: while Cerebras allows faster bursts (60k TPM), its total daily volume is capped much lower than Groq's theoretical maximum. This necessitates a routing strategy that uses Cerebras for bursty, high-context tasks but switches to Groq for sustained, lower-context volume.

### 2.3 OpenRouter: The Aggregator Bottleneck

To validate the "Ditch Slow Free AI APIs" component of the user's premise, we must contrast these direct limits with OpenRouter's free tier. OpenRouter acts as an aggregator, routing requests to various providers (including potentially Groq and Cerebras themselves, as well as others like Lepton or DeepInfra).

**The "Slow" Reality:** OpenRouter's free tier is subject to significant aggressive rate limiting and prioritization queuing.

- **Rate Limits:** Typically capped at 20 requests per minute and 50 to 1,000 requests per day, depending on whether the user has a positive credit balance.
- **Queue Latency:** Users frequently report "failed attempts" or long wait times as their requests are deprioritized behind paid traffic.
- **Throughput:** Even when requests are served, the routing overhead and the use of lower-tier providers often result in significantly lower token-per-second speeds compared to direct LPU/WSE access.

**Conclusion on Verification:** The guide is factually correct. Direct access to Groq and Cerebras offers a combined capacity of 28,800 requests per day with superior latency and burst capability, whereas OpenRouter's free tier offers <1,000 requests per day with variable performance.

---

## 3. Architectural Setup: The Unified Inference Gateway

Achieving the seamless integration of these two distinct providers requires a robust orchestration layer. The industry standard for this in 2026 is **LiteLLM**, a lightweight Python-based proxy that standardizes the API surface area to match the OpenAI specification. This allows the user's application to remain agnostic to the underlying provider while the proxy handles authentication, routing, and failover.

### 3.1 The LiteLLM Orchestration Layer

The "Setup" phase of the guide involves configuring LiteLLM to act as a local load balancer. The goal is to maximize the utilization of the high-TPM provider (Cerebras) while maintaining the high-reliability provider (Groq) as a failover target.

**Configuration Logic:** The configuration utilizes a "Priority Routing" strategy. By assigning a priority order, we ensure that the system always attempts to utilize the provider with the highest burst capacity first. If that provider rejects the request (due to a 429 Rate Limit error or 5xx Server Error), the router automatically degrades to the next provider in the chain.

#### 3.1.1 Implementation Details (YAML)

The following `config.yaml` represents the optimal configuration for this specific "14,400 RPD" strategy. It bonds the Cerebras and Groq endpoints into a single virtual model (e.g., `llama-3.1-70b`).

```yaml
model_list:
  # Primary Route: Cerebras
  # Selected for: High TPM (60k) and massive context handling.
  - model_name: llama-3.1-70b
    litellm_params:
      model: cerebras/llama3.1-70b
      api_key: os.environ/CEREBRAS_API_KEY
      rpm: 30
      tpm: 60000
      order: 1  # Priority 1: Attempt this first

  # Failover Route: Groq
  # Selected for: High reliability and deterministic latency.
  - model_name: llama-3.1-70b
    litellm_params:
      model: groq/llama-3.1-70b-versatile
      api_key: os.environ/GROQ_API_KEY
      rpm: 30
      tpm: 18000
      order: 2  # Priority 2: Use if Cerebras fails/limits
```

**Operational Mechanics:**

1. **Request Ingestion:** The application sends a standard OpenAI-format request to `http://localhost:4000/v1/chat/completions`.
2. **Router Decision:** LiteLLM checks the health and local rate limit tracking for the Priority 1 provider (Cerebras).
3. **Burst Handling:** If the request is large (e.g., 3,000 tokens), Cerebras is prioritized because its 60k TPM limit can absorb the load without triggering a 429 error.
4. **Failover Execution:** If Cerebras returns a rate limit error (or if the daily 1M token cap is hit), LiteLLM seamlessly retries the request against Groq.
5. **Response Streaming:** The first successful token stream is returned to the user, preserving the "500 Tokens/Sec" experience.

### 3.2 Key Management and Security

Direct integration requires managing API keys (`GROQ_API_KEY` and `CEREBRAS_API_KEY`). Unlike aggregators where a single key grants access to all models, this "sovereign" setup requires rotating keys individually.

- **Security Posture:** Keys should never be hardcoded. They must be injected via environment variables (`os.environ`).
- **Monitoring:** The LiteLLM proxy provides a standardized logging interface, allowing the user to inspect which provider served which request — a crucial feature for auditing the "free tier" usage and verifying that the load balancing logic is functioning as intended.

---

## 4. The Model Ecosystem of February 2026: Navigating Deprecations and Innovations

Hardware is only as useful as the models it serves. The AI model landscape in February 2026 is in a state of rapid transition, characterized by the deprecation of established workhorses and the arrival of "System 2" reasoning models and Mixture-of-Experts (MoE) architectures.

### 4.1 The Immediate Crisis: Llama 3.3 Deprecation

A critical finding in our research is the imminent deprecation of Llama 3.3 70B. As noted in the Cerebras documentation, this model is scheduled for removal on **February 16, 2026**.

- **Operational Risk:** Any setup strictly relying on `llama-3.3-70b` will experience catastrophic failure within days of this report's timeline.
- **Mitigation Strategy:** Users must immediately transition their configurations to Llama 3.1 8B, which remains supported, or verify the availability of the newer Llama 4 models. This deprecation highlights the volatility of "Free Tier" offerings, where providers aggressively cull older models to free up wafer space for state-of-the-art architectures.

### 4.2 Llama 4: The MoE Revolution

Released in April 2025, the Llama 4 family represents Meta's shift toward sparse Mixture-of-Experts architectures.

- **Llama 4 Scout:** This model features 17 billion active parameters during inference, despite a larger total parameter count of roughly 109 billion. It utilizes 16 experts.
- **Llama 4 Maverick:** A larger variant with 400 billion total parameters but maintaining the efficient 17 billion active parameter count per token.
- **Hardware Synergy:** These MoE models are exceptionally well-suited for Groq and Cerebras. Since only a fraction of parameters are active per token, the memory bandwidth requirements are reduced relative to model size, allowing for extremely high inference speeds. The "Scout" model, with its 10 million token context window, is particularly powerful on Cerebras, which can leverage its massive on-chip memory to store large KV caches that would overwhelm standard GPUs.

### 4.3 DeepSeek R1 and the Rise of "Reasoning" Models

By February 2026, the industry focus has shifted from simple token generation to "Reasoning" or "System 2" thinking. DeepSeek R1 and its distilled variants (e.g., `deepseek-r1-distill-llama-70b`) are the vanguard of this shift.

- **The "Thinking" Overhead:** These models generate a "Chain of Thought" (CoT) trace — often thousands of tokens of internal monologue — before outputting the final answer.
- **Impact on Infrastructure:** A single query to DeepSeek R1 might generate 2,000 "thought" tokens and 100 "answer" tokens. On a standard GPU, this 2,100-token generation could take 40+ seconds. On Groq's LPU running at 300-500 TPS, this latency is reduced to ~4-6 seconds.
- **Rate Limit Implications:** This "reasoning overhead" places immense pressure on the TPM limits. A user running DeepSeek R1 on Groq will hit the 18,000 TPM limit with just 9 requests per minute (assuming 2k tokens per request). This makes the 14,400 RPD quota mathematically unreachable for reasoning tasks unless utilizing the higher TPM limits of Cerebras.

---

## 5. Advanced Optimization: Squeezing the Free Tier

To make the "14,400 Requests/Day" claim a reality for complex, token-heavy workloads, raw bandwidth is not enough. One must employ advanced algorithmic optimizations to reduce the token footprint of each request. The guide implies the use of two specific technologies: **Prompt Compression** and **Semantic Caching**.

### 5.1 LLMLingua-2: Algorithmic Token Reduction

LLMLingua-2 is a prompt compression framework that addresses the TPM bottleneck directly. It utilizes a small, efficient model (like XLM-RoBERTa-large) to analyze the information entropy of a prompt and remove non-essential tokens while preserving the semantic core.

- **Mechanism:** In a RAG workflow, a user might retrieve 5 documents totaling 4,000 tokens. LLMLingua-2 can compress this context by up to 20x, reducing the input to ~200 tokens.
- **Economic Impact:**
  - Without Compression: A 4,000-token request consumes ~22% of Groq's per-minute quota.
  - With Compression: The same request (compressed to 200 tokens) consumes only ~1% of the quota.
- **Throughput Multiplier:** This technology effectively increases the "functional" TPM limit of the free tier by an order of magnitude, allowing the user to fit significantly more logical requests into the hardware constraints.

### 5.2 GPTCache: The Zero-Latency Layer

While LLMLingua-2 optimizes novel requests, GPTCache eliminates the cost of repetitive ones.

- **Architecture:** GPTCache sits as a middleware layer before the LiteLLM proxy. It computes a vector embedding of the incoming user query.
- **Semantic Matching:** Instead of exact string matching, it checks a local vector store (e.g., ChromaDB, FAISS) for semantically similar past queries. If a match is found (e.g., "How do I install Python?" matches "Python installation guide"), the cached response is returned immediately.
- **Benefits:**
  - Zero Latency: No API call is made.
  - Zero Token Usage: The request never hits Groq or Cerebras, preserving the TPM/RPD quotas for novel tasks.
- **Implementation:** The integration requires minimal code changes in the Python application, utilizing the `gptcache` library to wrap the OpenAI API call.

---

## 6. Competitive Analysis and Future Outlook

The landscape of February 2026 is dynamic. While Groq and Cerebras currently lead the "Free Tier" market, competitors are adjusting their strategies.

### 6.1 The Decline of Other Free Tiers

- **SambaNova**, which previously offered a competitive free tier, has transitioned to a "Developer Tier" model as of early 2026. The Trend: This signals a broader market shift. As hardware providers mature from "tech demos" to "enterprise platforms," the generous free tiers are often curtailed. The transition involves moving from unlimited/high-limit free access to a pay-as-you-go model with a small monthly credit (e.g., $5/month).
- **Cloudflare Workers AI** offers a different model based on "Neurons," with a free tier of 10,000 neurons per day. While useful for edge functions, this limit is significantly lower than the 14,400 RPD offered by Groq/Cerebras for large LLMs.
- **Hyperbolic**, a decentralized AI computing platform, also offers free credits but imposes rate limits of roughly 60 requests per minute for basic users.

### 6.2 The Sustainability of 14,400 RPD

The question remains: How long will Groq and Cerebras sustain these limits?

- **The "Loss Leader" Thesis:** As long as these companies are in the "Customer Acquisition" and "Compiler Optimization" phases, the free tiers will likely remain. They need the diverse, high-volume traffic to validate their hardware against NVIDIA's entrenched position.
- **Signaling:** Cerebras's explicitly defined "Developer" vs. "Enterprise" tiers suggest a stable roadmap where the free tier acts as a funnel. Groq's documentation emphasizes that the free tier is for "experimentation," implying potential future restrictions for production-level traffic.

### 6.3 Data Privacy and Sovereignty

For users in the European Union (EEA) and UK, reliance on US-based hardware providers (Groq, Cerebras) raises GDPR concerns.

- **Mistral AI:** Remains the gold standard for EU compliance, hosting models exclusively within the EU.
- **Groq/Cerebras:** Data sent to these APIs is processed on US servers. The terms of service for free tiers often grant the provider rights to use data for "service improvement" (i.e., debugging the compiler or hardware).
- **Recommendation:** This "Free Tier" stack is recommended for development, prototyping, and non-sensitive workloads. For regulated industries (healthcare, finance) in the EU, a paid contract with a DPA (Data Processing Agreement) or self-hosting on Mistral's platform is required.

---

## 7. Conclusion: The "Sovereign Inference" Stack

The guide "Ditch Slow Free AI APIs — 14,400 Requests/Day at 500 Tokens/Sec" outlines a technically sound and highly effective strategy for the AI landscape of February 2026. Our analysis validates the core claims: Groq and Cerebras indeed offer a combined capacity of 28,800 requests per day, and their specialized hardware delivers the promised sub-latency speeds.

However, the implementation is not without nuance. The strict 18,000 TPM limit on Groq and the 1M daily token cap on Cerebras require a sophisticated routing strategy. By leveraging LiteLLM for priority routing, LLMLingua-2 for prompt compression, and GPTCache for semantic caching, developers can overcome these bottlenecks and achieve enterprise-grade performance at zero marginal cost.

**Strategic Recommendations:**

1. **Immediate Migration:** Users relying on Llama 3.3 70B must migrate to Llama 3.1 8B or Llama 4 Scout immediately to avoid the February 16, 2026 deprecation.
2. **Hybrid Routing:** Configure LiteLLM to route high-context (RAG) and reasoning (DeepSeek R1) tasks to Cerebras to utilize its 60k TPM limit, while routing standard chat traffic to Groq.
3. **Algorithmic Efficiency:** Treat tokens as a scarce resource. Implement compression and caching not just for performance, but to maximize the utility of the free tier quotas.

By adopting this "Sovereign Inference" stack, developers can effectively bypass the congestion of the aggregator economy, securing a high-speed, high-volume inference cluster that rivals paid enterprise endpoints.

---

## 8. Detailed Guide to Setup and Configuration

This section provides the specific technical steps required to implement the architecture described above.

### 8.1 Environment Preparation

The setup presumes a Python environment. The core dependency is `litellm`.

```bash
pip install litellm gptcache llmlingua
```

### 8.2 LiteLLM Configuration (config.yaml)

Create a file named `config.yaml`. This file defines the routing logic.

```yaml
model_list:
  # ------------------------------------------------------------------
  # VIRTUAL MODEL: llama-3.1-70b
  # Strategies: Priority Routing (Cerebras First -> Groq Second)
  # ------------------------------------------------------------------

  # PRIORITY 1: Cerebras
  # Reason: Highest TPM (60k) allows for larger bursts/context.
  - model_name: llama-3.1-70b
    litellm_params:
      model: cerebras/llama3.1-70b
      api_key: os.environ/CEREBRAS_API_KEY
      rpm: 30
      tpm: 60000
      max_tokens: 8192
      order: 1

  # PRIORITY 2: Groq
  # Reason: High consistency, but lower TPM (18k). Good failover.
  - model_name: llama-3.1-70b
    litellm_params:
      model: groq/llama-3.1-70b-versatile
      api_key: os.environ/GROQ_API_KEY
      rpm: 30
      tpm: 18000
      max_tokens: 8192
      order: 2

  # ------------------------------------------------------------------
  # VIRTUAL MODEL: deepseek-r1 (Reasoning)
  # Note: DeepSeek R1 generates massive output tokens.
  # ------------------------------------------------------------------

  - model_name: deepseek-r1
    litellm_params:
      model: groq/deepseek-r1-distill-llama-70b
      api_key: os.environ/GROQ_API_KEY
      rpm: 10 # Artificially lower RPM to account for high token usage
      tpm: 18000

router_settings:
  # Critical for 'order' parameter to work
  enable_pre_call_checks: true
  # Fallback strategy
  fallbacks: [{"cerebras/llama3.1-70b": ["groq/llama-3.1-70b-versatile"]}]
```

### 8.3 Application Logic with Caching and Compression

The following Python code demonstrates how to integrate GPTCache and LLMLingua-2 before hitting the LiteLLM proxy.

> **Note:** This code block as pasted contains transcription errors (`response.choices.message.content` missing the `[0]` index; `os.environ = "gsk_..."` missing the key name). These must be fixed when implementing. Preserved verbatim below per the "save as-is" rule.

```python
import os
from litellm import completion
from gptcache import cache
from gptcache.adapter.api import init_similar_cache
from llmlingua import PromptCompressor

# 1. Initialize Prompt Compressor (LLMLingua-2)
# Uses a small local model to compress prompts
compressor = PromptCompressor(model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank")

# 2. Initialize Semantic Cache (GPTCache)
# This intercepts requests. If a similar request was made, it returns the cached answer.
init_similar_cache(cache_obj=cache, data_manager=get_data_manager())

def robust_inference(user_query, context_documents):
    """
    Executes the full pipeline: Compression -> Caching -> Inference
    """

    # Step A: Context Compression
    # Compresses long context documents to fit within TPM limits
    compressed_context = compressor.compress_prompt(
        context_documents,
        instruction=user_query,
        rate=0.5,
        target_token=500
    )

    full_prompt = f"Context: {compressed_context}\nQuestion: {user_query}"

    # Step B: Inference with Caching via LiteLLM
    # LiteLLM handles the routing between Cerebras and Groq based on config.yaml
    response = completion(
        model="llama-3.1-70b",
        messages=[{"role": "user", "content": full_prompt}],
        metadata={"generation_name": "production_inference"}
    )

    return response.choices.message.content

# Example Usage
if __name__ == "__main__":
    # Ensure keys are set
    # os.environ = "gsk_..."
    # os.environ = "csk_..."

    result = robust_inference("Explain the LPU architecture", "Groq LPU uses deterministic... [long text]")
    print(result)
```

---

## 9. Hardware Architecture Deep Dive

To fully appreciate why this setup works, one must understand the underlying hardware. The performance is not magic; it is physics.

### 9.1 Groq LPU: The Deterministic Stream

The Language Processing Unit (LPU) is a single-core architecture. Unlike a GPU, which has thousands of cores managed by a scheduler, the LPU has functional units (Matrix Multiplication, Vector, Switch) that are orchestrated by the compiler.

- **Instruction Set:** The compiler explicitly schedules the movement of every byte of data for every clock cycle. It knows exactly when a tensor will arrive at a functional unit.
- **Latency Elimination:** This removes the need for caches (L1/L2/L3) and branch prediction logic, which consume significant silicon area on CPUs and GPUs. Instead, that area is used for more arithmetic units and SRAM.
- **SRAM vs. HBM:** By using SRAM (Static Random Access Memory), Groq achieves bandwidths of roughly 80 TB/s inside the chip, compared to ~3 TB/s for HBM on GPUs. This is why it can decode tokens at 500+ Hz.

### 9.2 Cerebras WSE-3: The Megachip

The Wafer-Scale Engine (WSE-3) is the largest chip ever built.

- **Scale:** It is a 46,225 mm² square of silicon (an NVIDIA H100 is ~814 mm²).
- **Cores:** It contains 4 million sparse linear algebra cores.
- **Memory:** 44 GB of on-chip SRAM.
- **The Advantage:** A model like Llama 3 70B fits entirely within the on-chip memory of a single WSE-3 system (CS-3). On a GPU cluster, this model would be split across 4-8 GPUs, requiring data to travel over PCIe or NVLink cables (interconnect bottleneck). On Cerebras, the data travels over silicon wires at nanosecond speeds. This architectural difference allows for the 60,000 TPM limit — the system processes data so fast that it clears the queue almost instantly, allowing for higher volume allowance.

---

## 10. Summary of Key Findings

| Feature | Groq Free Tier | Cerebras Free Tier | OpenRouter Free |
|---|---|---|---|
| Requests/Day | 14,400 | 14,400 | < 1,000 |
| Tokens/Minute | 18,000 | 60,000 | Variable / Low |
| Daily Token Cap | Implicit (~25M) | 1,000,000 | Low |
| Speed (70B Model) | ~300-500 T/s | ~450 T/s | ~20-50 T/s |
| Primary Use Case | Low-latency Chat | High-throughput RAG | Discovery / Testing |
| Model Availability | Llama 3, Mixtral, DeepSeek | Llama 3.1, Qwen (Llama 3.3 Deprecating) | All Models |

This comparison definitively proves the superiority of the direct-access method. By combining the 14,400 RPD of both providers, the user constructs a robust, high-performance inference engine capable of handling significant workloads — all without swiping a credit card.

---

## Implementation status (as of 2026-04-12)

**NOT STARTED.** This document describes the architecture. To make it real:

1. Sign up for Groq free tier at https://console.groq.com → obtain `GROQ_API_KEY`
2. Sign up for Cerebras free tier at https://cloud.cerebras.ai → obtain `CEREBRAS_API_KEY`
3. `pip install litellm gptcache llmlingua` (into the Python 3.13 env that already has `mcp`)
4. Create `FLOSS/config/litellm-router.yaml` based on §8.2
5. Export the two keys as environment variables (do NOT commit them; add a `.env.example` with placeholders)
6. Test a single call with `litellm --config config/litellm-router.yaml` then `curl -X POST http://localhost:4000/v1/chat/completions ...`
7. Once a single call works, wire `make_litellm_voter(config)` into `packages/metacoordinator_mcp/` so the MCP gateway can actively invoke Cerebras/Groq as voters — this is the piece that currently doesn't exist and is the reason every session re-burns Claude tokens to do work these free tiers could do instead.

See also:
- `FLOSS/docs/adr/ADR-MCP-ORCHESTRATOR.md` — the architecture this integrates into
- `FLOSS/docs/research/Automated-Agent-Orchestration-Report_v2.0.0.md` — broader orchestration landscape context
- `FLOSS/docs/research/openrouter-llms-full.txt` — OpenRouter reference (for completeness, though this guide is explicitly arguing *against* OpenRouter)
