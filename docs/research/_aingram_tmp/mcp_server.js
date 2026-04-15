/**
 * MCP (Model Context Protocol) server — modular tool architecture with progressive disclosure.
 * Mounted in the Express app at /mcp (Streamable HTTP transport).
 *
 * Tools are organized in categories (see categories.js). Core tools are always visible.
 * Other categories are disabled by default and can be enabled per-session via the
 * enable_tools meta-tool, which uses the SDK's native enable()/disable() mechanism.
 *
 * Architecture:
 *   server.js       — orchestrator (this file): creates McpServer, delegates to modules
 *   helpers.js      — shared helpers (mcpResult, mcpError, requireAccount, etc.)
 *   categories.js   — category registry with metadata
 *   meta-tools.js   — list_capabilities + enable_tools
 *   tools/*.js      — one file per category, each exports { CATEGORY, registerTools }
 */

const { McpServer } = require('@modelcontextprotocol/sdk/server/mcp.js');
const { StreamableHTTPServerTransport } = require('@modelcontextprotocol/sdk/server/streamableHttp.js');
const { CATEGORIES } = require('./categories');
const { registerAllTools } = require('./tools/index');
const { registerMetaTools } = require('./meta-tools');
const { SECURITY_BASELINE_MCP } = require('../config/security-baseline');

/**
 * Create and configure the MCP server with progressive disclosure.
 * @param {function} getSessionAccount - (sessionId) => account | null
 */
function createMcpServer(getSessionAccount) {
  const server = new McpServer({
    name: 'aingram',
    version: '1.0.0',
    instructions: SECURITY_BASELINE_MCP,
  });

  // 1. Register all tools from all category modules
  const allTools = registerAllTools(server, getSessionAccount);

  // 2. Per-session enabled state tracking (mutable object shared with meta-tools)
  const enabledState = {};

  // 3. Register meta-tools (list_capabilities, enable_tools)
  registerMetaTools(server, allTools, enabledState);

  // 4. Disable all non-core category tools
  for (const [category, tools] of Object.entries(allTools)) {
    if (!CATEGORIES[category]?.alwaysEnabled) {
      for (const tool of Object.values(tools)) {
        tool.disable();
      }
    }
  }

  return server;
}

/**
 * Mount MCP endpoints on an Express app.
 * POST /mcp — main MCP endpoint (Streamable HTTP)
 * GET /mcp — SSE endpoint for server-initiated messages
 * DELETE /mcp — session termination
 */
const MAX_MCP_SESSIONS = 200;
const MCP_SESSION_TTL_MS = 30 * 60 * 1000; // 30 minutes

function mountMcp(app) {
  const { isInitializeRequest } = require('@modelcontextprotocol/sdk/types.js');
  const { extractAccount } = require('../middleware/auth');

  // Track active sessions: sessionId → { transport, server, lastActivity, account }
  const sessions = new Map();

  // Closure: look up account for a session
  function getSessionAccount(sessionId) {
    const entry = sessions.get(sessionId);
    return entry ? entry.account : null;
  }

  // Sweep stale sessions every 5 minutes
  setInterval(() => {
    const now = Date.now();
    for (const [id, entry] of sessions) {
      if (now - entry.lastActivity > MCP_SESSION_TTL_MS) {
        sessions.delete(id);
      }
    }
  }, 5 * 60 * 1000).unref();

  app.post('/mcp', async (req, res) => {
    try {
      const sessionId = req.headers['mcp-session-id'];
      let transport;

      if (sessionId && sessions.has(sessionId)) {
        // Reuse existing session
        const entry = sessions.get(sessionId);
        entry.lastActivity = Date.now();
        transport = entry.transport;
      } else if (!sessionId && isInitializeRequest(req.body)) {
        // New session — only allowed for initialize requests without a session ID
        if (sessions.size >= MAX_MCP_SESSIONS) {
          return res.status(503).json({ error: 'Too many active MCP sessions. Try again later.' });
        }

        // Authenticate: extract account from Bearer token (optional — read tools work without)
        let account = null;
        try {
          account = await extractAccount(req);
          if (account && account.status !== 'banned') {
            account = {
              id: account.id,
              name: account.name,
              type: account.type,
              status: account.status,
              tier: account.tier || 0,
              badgeContribution: !!account.badge_contribution,
              badgePolicing: !!account.badge_policing,
              badgeElite: !!account.badge_elite,
            };
          } else {
            account = null;
          }
        } catch (_authErr) {
          // No auth or invalid — read tools still work
        }

        transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => require('crypto').randomUUID(),
          onsessioninitialized: (sid) => {
            sessions.set(sid, { transport, server, lastActivity: Date.now(), account });
          },
        });
        transport.onclose = () => {
          if (transport.sessionId) {
            sessions.delete(transport.sessionId);
          }
        };

        // Each session needs its own McpServer instance (SDK allows one transport per server)
        const server = createMcpServer(getSessionAccount);
        await server.connect(transport);
      } else {
        // No valid session ID and not an initialization request
        return res.status(400).json({
          jsonrpc: '2.0',
          error: { code: -32000, message: 'Bad Request: No valid session ID provided' },
          id: null,
        });
      }

      await transport.handleRequest(req, res, req.body);
    } catch (err) {
      console.error('MCP POST error:', err.message);
      if (!res.headersSent) {
        res.status(500).json({ error: 'MCP server error' });
      }
    }
  });

  app.get('/mcp', async (req, res) => {
    const sessionId = req.headers['mcp-session-id'];
    const entry = sessionId && sessions.get(sessionId);
    if (!entry) {
      return res.status(400).json({ error: 'No active session. Send an initialize request first.' });
    }
    entry.lastActivity = Date.now();
    await entry.transport.handleRequest(req, res);
  });

  app.delete('/mcp', async (req, res) => {
    const sessionId = req.headers['mcp-session-id'];
    const entry = sessionId && sessions.get(sessionId);
    if (entry) {
      await entry.transport.handleRequest(req, res);
      sessions.delete(sessionId);
    } else {
      res.status(200).end();
    }
  });
}

module.exports = { createMcpServer, mountMcp };
