# Specification: Cloudflare Public Commons Gateway Worker

**Version:** 0.1  
**Date:** 2026-06-16  
**Status:** Draft for user review; concept approved for implementation planning  
**Authors:** kalisam + Codex session

---

## 1. Context & Motivation

FLOSSI0ULLK needs public cultivation surfaces that can be reached from ordinary
web clients without asking visitors to run the full local agent stack. A
Cloudflare Worker is a good first edge surface because it can serve small public
HTTP responses globally while leaving project truth and consent authority inside
the existing FLOSSI0ULLK substrate.

Truth-status notes for this design:

- ✅ Verified: FLOSSI0ULLK's current authority model is symbolic-first and
  Holochain/source-chain oriented. Evidence: `INDEX.md`,
  `FLOSS/CLAUDE.md`, `FLOSS/docs/specs/provenance-packet.spec.md`.
- ✅ Verified: the current repository has no Cloudflare Worker scaffold under
  `FLOSS/`; current package surfaces are `FLOSS/package.json` and
  `FLOSS/packages/*`. Evidence: `FLOSS/package.json`, `FLOSS/packages/`.
- ⚠️ Specified: the first Cloudflare Worker will be a public read-only gateway,
  not an authoritative validation substrate.

## 2. Goal

Create the first Cloudflare Worker in the FLOSS repo as a public, open-source,
read-only gateway for FLOSSI0ULLK orientation.

The Worker should answer:

- What is this commons?
- What are the current authority boundaries?
- Where should a human, AI, synthetic, hybrid, ecosystemic, or future agent go
  next?
- Is the Worker itself healthy?

It should not decide truth, accept governed writes, mint consensus, or bypass
Holochain/source-chain validation.

## 3. Scope

Add a new Worker package at this repository-relative path (workspace-relative:
`FLOSS/workers/commons-gateway/`):

```text
workers/commons-gateway/
```

Initial endpoints:

| Method | Path | Response | Purpose |
|---|---|---|---|
| `GET` / `HEAD` | `/` | HTML | Human-readable public commons entrypoint. |
| `GET` / `HEAD` | `/manifest` | JSON | Machine-readable project gateway manifest. |
| `GET` / `HEAD` | `/health` | JSON | Runtime health check for Cloudflare and local dev. |
| `GET` / `HEAD` | `/robots.txt` | text | Minimal crawler policy for public discovery. |
| `GET` / `HEAD` | unknown path | JSON `404` with `{"error":"not_found"}` | Deterministic not-found response. |

First-pass files:

```text
workers/commons-gateway/
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── wrangler.jsonc
├── src/
│   ├── index.ts
│   ├── manifest.ts
│   ├── responses.ts
│   └── security.ts
└── test/
    └── commons-gateway.test.ts
```

The package should be independently installable/testable from its own directory.
It should not require the Python ARF environment, Holochain CLI, or the local
MCP gateway to run basic tests.

## 4. Non-Goals

This first Worker will not:

- Modify or validate Holochain integrity zome logic.
- Write to `FLOSS/packages/metacoordinator_mcp/` or alter consensus-gateway
  behavior.
- Read local `agentmemory` or expose private local memory over the public web.
- Accept POST/PUT/PATCH/DELETE intake.
- Store user data, set cookies, or add analytics.
- Use Cloudflare Workers AI, D1, KV, R2, Durable Objects, Queues, or Workflows.
- Promote any document to canonical status.
- Modify ADRs or hard-stop configuration files.

These are future slices only after the public gateway proves useful and its
authority boundaries are visible.

## 5. Architecture

The Worker is a small TypeScript module with explicit routing and no framework.
That keeps the first edge surface auditable and avoids bringing a full frontend
framework into the repo before the project needs one.

Request flow:

```text
HTTP request
  -> method/path router
  -> endpoint handler
  -> shared security headers
  -> HTML/JSON/text response
```

Module responsibilities:

| Module | Responsibility |
|---|---|
| `src/index.ts` | Worker `fetch` entrypoint and route dispatch. |
| `src/manifest.ts` | Static, typed manifest describing public project orientation and authority boundaries. |
| `src/responses.ts` | Response builders, content negotiation, 404/405 handling. |
| `src/security.ts` | Shared security and cache headers. |
| `test/commons-gateway.test.ts` | Endpoint behavior tests using Cloudflare's Worker test runtime. |

Cloudflare configuration:

- `main`: `src/index.ts`
- `compatibility_date`: `2026-06-16`
- `compatibility_flags`: `["nodejs_compat"]`
- No bindings in the first pass.

⚠️ Specified implementation assumption: use an explicit Wrangler config, keep
the compatibility date current, enable `nodejs_compat`, and generate Worker
binding types with `wrangler types`. Implementation must re-check Cloudflare
docs before finalizing dependency versions or deploy commands.

## 6. Manifest Contract

`GET /manifest` returns JSON with this shape:

```json
{
  "name": "FLOSSI0ULLK Public Commons Gateway",
  "project": "FLOSSI0ULLK",
  "truth_status": "specified",
  "authority": {
    "principle": "Logic validates, neural assists.",
    "worker_role": "public read-only orientation gateway",
    "not_authority": [
      "canonical truth",
      "consensus decision",
      "Holochain validation",
      "consent decision"
    ]
  },
  "links": [
    {
      "label": "Project README",
      "description": "Repository introduction and project orientation.",
      "path": "README.md",
      "href": "https://github.com/G-0-B/FLOSS/blob/main/README.md",
      "truth_status": "verified"
    },
    {
      "label": "Project orientation",
      "description": "Current agent-facing operating notes for FLOSS.",
      "path": "CLAUDE.md",
      "href": "https://github.com/G-0-B/FLOSS/blob/main/CLAUDE.md",
      "truth_status": "verified"
    },
    {
      "label": "Provenance packet spec",
      "description": "Repository specification for provenance packet evidence.",
      "path": "docs/specs/provenance-packet.spec.md",
      "href": "https://github.com/G-0-B/FLOSS/blob/main/docs/specs/provenance-packet.spec.md",
      "truth_status": "verified"
    },
    {
      "label": "Gateway design spec",
      "description": "Design boundary for this first Worker slice.",
      "path": "docs/superpowers/specs/2026-06-16-cloudflare-commons-gateway-design.md",
      "href": "https://github.com/G-0-B/FLOSS/blob/main/docs/superpowers/specs/2026-06-16-cloudflare-commons-gateway-design.md",
      "truth_status": "verified"
    }
  ],
  "mediums": [
    "web",
    "json",
    "open-source repository"
  ]
}
```

Every load-bearing project claim in the manifest must carry either:

- `truth_status: "verified"` with an evidence path in the repository, or
- `truth_status: "specified"` when it is design intent, not observed runtime
  fact.

The initial Worker may use static data from `src/manifest.ts`. Later Workers can
generate this from repository artifacts, provenance packets, or Holochain
queries after those paths are designed and approved.

## 7. HTML Contract

`GET /` renders a plain, accessible HTML page derived from the same manifest.
The page should be useful without JavaScript.

Required visible sections:

- Project name and expanded name.
- One-paragraph purpose.
- Authority boundary: the Worker is not the source of truth.
- Links to current repo-facing entrypoints.
- Machine-readable manifest link.

The first page is a working public surface, not a marketing landing page. It
should be sober, readable, and exact.

## 8. Security, Privacy, And Consent

First-pass posture:

- Only `GET` and `HEAD` are supported.
- No cookies.
- No request body processing.
- No IP/user-agent logging in application code.
- No public path exposes local files directly.
- JSON responses use `application/json; charset=utf-8`.
- HTML responses use `text/html; charset=utf-8`.
- Security headers include at least:
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: no-referrer`
  - `Permissions-Policy` with unnecessary browser capabilities disabled
  - a restrictive `Content-Security-Policy`

Consent-sensitive intake, comments, identity, provenance upload, or voting are
out of scope until there is an explicit design that preserves the source-chain
and Holochain validation boundaries.

## 9. Error Handling

- Unsupported methods return `405 Method Not Allowed` and an `Allow: GET, HEAD`
  header.
- Unknown paths return `404 Not Found` as JSON
  `{"error":"not_found"}` with `Content-Type: application/json; charset=utf-8`
  and the same security headers as normal responses.
- Invalid content negotiation should still return a useful default response;
  the gateway should not fail merely because a client sends a broad `Accept`
  header.

## 10. Test Plan

TDD applies to implementation.

Required tests before production code:

- `/health` returns `200`, JSON, and `status: "ok"`.
- `/manifest` returns `200`, JSON, project name, authority boundary, and
  truth-status fields.
- `/` returns `200`, HTML, project name, and manifest link.
- `HEAD /manifest` returns headers without a response body.
- Unknown path returns `404`.
- Unsupported method returns `405` and `Allow: GET, HEAD`.
- Security headers are present on success and error responses.

Verification commands from repository-relative `workers/commons-gateway/`
(workspace-relative `FLOSS/workers/commons-gateway/`):

```bash
npm test
npm run typecheck
npm run cf:typegen
npm run dev
```

Deployment is a later human action:

```bash
npm run deploy
```

## 11. Future Slices

After this gateway is implemented and tested, possible next slices are:

1. Static media/research garden backed by Cloudflare Assets or R2.
2. Provenance packet intake relay with signature verification and no privileged
   verifier path.
3. Read-only source-chain mirror for public claims already validated elsewhere.
4. Worker-triggered background checks using Queues or Workflows.
5. Optional Cloudflare AI helper surfaces that summarize verified public
   artifacts while preserving "logic validates, neural assists."

Each future slice needs its own spec because the authority and consent risks are
different.

## 12. Implementation Boundary

Implementation may create and edit only the new
`FLOSS/workers/commons-gateway/` package and, if necessary, minimal parent
workspace package metadata for discoverability.

Implementation must not modify:

- `FLOSS/docs/adr/`
- `FLOSS/ARF/dnas/*/zomes/integrity/`
- `FLOSS/packages/metacoordinator_mcp/`
- `.mcp.json`
- `.claude/settings.json`
- JanuScope lens files
- `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`

If the implementation appears to need any of those surfaces, stop and ask for
explicit human confirmation.
