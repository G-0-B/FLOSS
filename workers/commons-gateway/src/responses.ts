import type { CommonsManifest } from "./manifest";
import { withSecurityHeaders } from "./security";

const JSON_CONTENT_TYPE = "application/json; charset=utf-8";
const HTML_CONTENT_TYPE = "text/html; charset=utf-8";
const TEXT_CONTENT_TYPE = "text/plain; charset=utf-8";

export function jsonResponse(
  payload: unknown,
  status = 200,
  init?: HeadersInit
): Response {
  const headers = responseHeaders(JSON_CONTENT_TYPE, init);
  return new Response(`${JSON.stringify(payload, null, 2)}\n`, {
    headers,
    status
  });
}

export function htmlResponse(html: string, status = 200): Response {
  return new Response(html, {
    headers: responseHeaders(HTML_CONTENT_TYPE),
    status
  });
}

export function textResponse(text: string, status = 200): Response {
  return new Response(text, {
    headers: responseHeaders(TEXT_CONTENT_TYPE),
    status
  });
}

export function methodNotAllowedResponse(method: string): Response {
  return jsonResponse(
    {
      error: "method_not_allowed",
      message: `${method} is not supported by this read-only gateway.`,
      read_only: true
    },
    405,
    { Allow: "GET, HEAD", "Cache-Control": "no-store" }
  );
}

export function notFoundResponse(pathname: string): Response {
  return jsonResponse(
    {
      error: "not_found",
      message: `No read-only commons gateway route exists for ${pathname}.`
    },
    404,
    { "Cache-Control": "no-store" }
  );
}

export function stripBodyForHead(response: Response): Response {
  return new Response(null, {
    headers: response.headers,
    status: response.status,
    statusText: response.statusText
  });
}

export function renderHomePage(manifest: CommonsManifest): string {
  const links = manifest.links
    .map(
      (link) => `<li>
        <a href="${escapeHtml(link.href)}">${escapeHtml(link.label)}</a>
        <span>${escapeHtml(link.description)}</span>
        <code>${escapeHtml(link.path)}</code>
        <small>${escapeHtml(link.truth_status)}</small>
      </li>`
    )
    .join("");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(manifest.name)}</title>
  <style>
    :root {
      color-scheme: light dark;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }
    body {
      margin: 0;
      background: Canvas;
      color: CanvasText;
    }
    main {
      max-width: 58rem;
      padding: 4rem 1.25rem;
      margin: 0 auto;
    }
    h1 {
      margin: 0 0 0.5rem;
      font-size: clamp(2rem, 8vw, 4rem);
      line-height: 1;
      letter-spacing: 0;
    }
    h2 {
      margin-top: 2.25rem;
      font-size: 1rem;
      text-transform: uppercase;
      letter-spacing: 0;
    }
    p {
      max-width: 48rem;
      font-size: 1.05rem;
    }
    ul {
      display: grid;
      gap: 0.75rem;
      padding: 0;
      list-style: none;
    }
    li {
      display: grid;
      gap: 0.2rem;
      padding-block: 0.75rem;
      border-block-end: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
    }
    a {
      color: LinkText;
      font-weight: 650;
    }
    code,
    small {
      overflow-wrap: anywhere;
    }
  </style>
</head>
<body>
  <main>
    <h1>${escapeHtml(manifest.project)}</h1>
    <p><strong>${escapeHtml(manifest.expanded_name)}</strong></p>
    <p>${escapeHtml(manifest.purpose.statement)}</p>

    <h2>Authority Boundary</h2>
    <p>${escapeHtml(manifest.authority.principle)} This Worker is a ${escapeHtml(
      manifest.authority.worker_role
    )}; it is not canonical truth, consensus, Holochain validation, consent, or governed write intake.</p>

    <h2>Entry Points</h2>
    <ul>${links}</ul>

    <h2>Machine Readable</h2>
    <p><a href="/manifest">Open the gateway manifest</a></p>
  </main>
</body>
</html>
`;
}

function responseHeaders(contentType: string, init?: HeadersInit): Headers {
  const headers = withSecurityHeaders(init);

  headers.set("Content-Type", contentType);
  if (!headers.has("Cache-Control")) {
    headers.set("Cache-Control", "public, max-age=300");
  }

  return headers;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => {
    switch (char) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case '"':
        return "&quot;";
      case "'":
        return "&#39;";
      default:
        return char;
    }
  });
}
