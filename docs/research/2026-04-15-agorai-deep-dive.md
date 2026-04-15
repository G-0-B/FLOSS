# Agorai Deep Dive --- 2026-04-15

> Source: [github.com/StevenJohnson998/Agorai](https://github.com/StevenJohnson998/Agorai)

**Agorai** ("Where Minds Meet") is an open-source multi-agent AI collaboration platform.

| **npm packages** | `agorai` (bridge+debate) + `agorai-connect` (stdio-to-HTTP proxy) |
| **Author** | Steven Johnson (same author as AIngram) |

Agorai and FLOSS occupy *complementary* niches:
- **Agorai** = *ephemeral multi-agent collaboration*. Agents debate, disagree, and converge in real-time conversations. Knowledge persists in shared memory and skills but the debate process itself is session-scoped and informal.
- **FLOSS** = *persistent consensus gate*. 

The natural integration: Agorai serves as the **"debate layer"** (pre-consensus exploration), and FLOSS serves as the **"consensus gate"** (post-consensus formal validation). Agents argue freely in Agorai, then the best-converged result passes through FLOSS's consensus validator for permanent inscription.

Agorai has a two-layer architecture: a **Bridge** (collaboration infrastructure) and a **Debate Engine** (structured multi-agent debates).

### Keryx Orchestrator
Keryx is Agorai's built-in discussion manager --- a **rule-based orchestrator** with zero LLM dependency. It manages *process*, never generates *content*. It registers as agent type `orchestrator` with `restricted` clearance.

| Dimension | Keryx (Agorai) | FLOSS Consensus Gate |
| --------- | -------------- | -------------------- |
| Role | Ephemeral process manager | Persistent truth validation |

| Agorai Feature | Version | Description | FLOSS Relevance | Priority |
| -------------- | ------- | ----------- | --------------- | -------- |
| **agorai-connect** | v0.0.8 | stdio-to-HTTP proxy, 5 commands, zero deps | HIGH --- the bridge mechanism for MCP clients | P1 |

Agorai can serve as the **ephemeral collaboration layer** feeding into FLOSS's **persistent consensus gate**:

                    AGORAI (Ephemeral)                    FLOSS (Persistent)
  Human/Agent -----> Agorai Bridge -----> Keryx rounds -----> Converged result

### 6.2 Bridge Mechanism: agorai-connect
`agorai-connect` is the key integration piece. It's a zero-dependency npm package that proxies stdio MCP (used by Claude Desktop, Claude Code) to Agorai's HTTP bridge.

1. FLOSS's metacoordinator_mcp starts as an MCP server
2. `agorai-connect proxy` bridges it to Agorai's HTTP bridge
3. FLOSS agents appear as participants in Agorai conversations

agorai-connect proxy (stdio --> HTTP)
Agorai Bridge (127.0.0.1:3100)
    +---> Claude agent (via agorai-connect)

### 6.4 Data Flow for a FLOSS-Agorai Consensus Cycle
1. **Initiation**: FLOSS metacoordinator creates an Agorai project + conversation
- **Model diversity**: Agorai connects any model; FLOSS doesn't need its own adapter layer
- **Ephemeral debate**: Agorai handles the messy, exploratory phase; FLOSS stays clean
- **Visibility gating**: Agorai's 4-level visibility maps naturally to FLOSS trust tiers

| Dimension | Agorai | FLOSS metacoordinator_mcp | Codex bridge |
| --------- | ------ | ------------------------- | ------------ |
| Focus | Ephemeral debate | Persistent truth | Execution context |

### Integration Action Plan

1. **Clone and run Agorai locally**
   ```bash
   npm install -g agorai
   agorai init
   agorai serve --gui
   ```

2. **Register agents**
   - Register Claude via `agorai agent add claude --type cli`
   - Register a DeepSeek or Ollama model via `agorai agent add deepseek --type openai-compat`

3. **Handle Licensing (ADR-7)**
   - If FLOSS integrates Agorai as a dependency, the AGPL copyleft may propagate
   - Options: (a) accept AGPL for the integration layer, (b) negotiate dual-license with Steven Johnson, (c) use Agorai as a separate service (AGPL only applies to the service itself, not callers via API/MCP)
   - **Recommendation**: option (c) --- run Agorai as a standalone bridge service, communicate via MCP. This avoids AGPL propagation.

4. **Wire agorai-connect into FLOSS MCP server**
   - Run `agorai-connect proxy` as a subprocess from FLOSS metacoordinator
   - Or use `agorai-connect setup code` to inject into Claude Code's MCP config
   - Test end-to-end: FLOSS metacoordinator -> agorai-connect -> Agorai bridge -> multi-agent debate -> result back to FLOSS

5. **Advanced Topics**
   - Subscribe to Agorai conversations from FLOSS metacoordinator
   - Agorai's meta-tool pattern (planned) aligns with FLOSS's context-efficiency goals
   - A2A interop facade (planned v1.0) could bridge Agorai and FLOSS at protocol level