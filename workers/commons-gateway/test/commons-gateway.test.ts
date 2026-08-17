import { env } from "cloudflare:workers";
import {
  createExecutionContext,
  waitOnExecutionContext
} from "cloudflare:test";
import { describe, expect, it } from "vitest";

import worker from "../src/index";
import { commonsManifest } from "../src/manifest";

const IncomingRequest = Request;

const expectedPublicLinks = [
  {
    path: "README.md",
    href: "https://github.com/G-0-B/FLOSS/blob/main/README.md"
  },
  {
    path: "CLAUDE.md",
    href: "https://github.com/G-0-B/FLOSS/blob/main/CLAUDE.md"
  },
  {
    path: "docs/specs/provenance-packet.spec.md",
    href: "https://github.com/G-0-B/FLOSS/blob/main/docs/specs/provenance-packet.spec.md"
  },
  {
    path: "docs/superpowers/specs/2026-06-16-cloudflare-commons-gateway-design.md",
    href: "https://github.com/G-0-B/FLOSS/blob/main/docs/superpowers/specs/2026-06-16-cloudflare-commons-gateway-design.md"
  }
] as const;

async function fetchGateway(path: string, init?: RequestInit): Promise<Response> {
  const request = new IncomingRequest(`https://commons.example${path}`, init);
  const ctx = createExecutionContext();
  const response = await worker.fetch(request, env, ctx);
  await waitOnExecutionContext(ctx);
  return response;
}

function expectSecurityHeaders(response: Response): void {
  expect(response.headers.get("x-content-type-options")).toBe("nosniff");
  expect(response.headers.get("referrer-policy")).toBe("no-referrer");
  expect(response.headers.get("permissions-policy")).toContain("camera=()");
  expect(response.headers.get("content-security-policy")).toContain(
    "default-src 'none'"
  );
}

describe("commons gateway worker", () => {
  it("returns a healthy read-only status", async () => {
    const response = await fetchGateway("/health");

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe(
      "application/json; charset=utf-8"
    );
    expectSecurityHeaders(response);

    await expect(response.json()).resolves.toMatchObject({
      status: "ok",
      read_only: true
    });
  });

  it("returns a machine-readable manifest with authority boundaries", async () => {
    const response = await fetchGateway("/manifest");

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe(
      "application/json; charset=utf-8"
    );
    expectSecurityHeaders(response);

    const manifest = await response.json();
    expect(manifest).toMatchObject({
      name: "FLOSSI0ULLK Public Commons Gateway",
      project: "FLOSSI0ULLK",
      truth_status: "specified",
      authority: {
        worker_role: "public read-only orientation gateway"
      }
    });
    expect(manifest.authority.not_authority).toContain("canonical truth");
    expect(manifest.authority.truth_status).toBe("specified");
    expect(manifest.authority.evidence.map((entry: { path: string }) => entry.path)).toEqual([
      "CLAUDE.md",
      "docs/specs/provenance-packet.spec.md",
      "docs/superpowers/specs/2026-06-16-cloudflare-commons-gateway-design.md"
    ]);
  });

  it.each(expectedPublicLinks)(
    "publishes the repository path and URL for $path",
    ({ path, href }) => {
      const link = commonsManifest.links.find((entry) => entry.path === path);

      expect(link).toBeDefined();
      expect(link).toMatchObject({ path, href, truth_status: "verified" });
    }
  );

  it("publishes exactly the expected public repository links", () => {
    expect(commonsManifest.links).toHaveLength(expectedPublicLinks.length);
    expect(commonsManifest.links.map(({ path, href }) => ({ path, href }))).toEqual(
      expectedPublicLinks
    );
  });

  it("renders the public HTML entrypoint without requiring JavaScript", async () => {
    const response = await fetchGateway("/");
    const html = await response.text();

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe(
      "text/html; charset=utf-8"
    );
    expectSecurityHeaders(response);
    expect(html).toContain("FLOSSI0ULLK");
    expect(html).toContain("Logic validates, neural assists.");
    expect(html).toContain('href="/manifest"');
    expect(html).not.toContain("<script");
  });

  it("returns headers without a body for HEAD /manifest", async () => {
    const response = await fetchGateway("/manifest", { method: "HEAD" });

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe(
      "application/json; charset=utf-8"
    );
    expectSecurityHeaders(response);
    expect(await response.text()).toBe("");
  });

  it("returns 404 for unknown paths", async () => {
    const response = await fetchGateway("/not-here");

    expect(response.status).toBe(404);
    expectSecurityHeaders(response);
    await expect(response.json()).resolves.toMatchObject({
      error: "not_found"
    });
  });

  it("rejects write methods with 405 and an Allow header", async () => {
    const response = await fetchGateway("/manifest", {
      body: JSON.stringify({ attempt: "write" }),
      method: "POST"
    });

    expect(response.status).toBe(405);
    expect(response.headers.get("allow")).toBe("GET, HEAD");
    expectSecurityHeaders(response);
    await expect(response.json()).resolves.toMatchObject({
      error: "method_not_allowed",
      read_only: true
    });
  });

  it("serves a minimal robots policy", async () => {
    const response = await fetchGateway("/robots.txt");
    const text = await response.text();

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe(
      "text/plain; charset=utf-8"
    );
    expectSecurityHeaders(response);
    expect(text).toContain("User-agent: *");
    expect(text).toContain("Allow: /");
  });
});
