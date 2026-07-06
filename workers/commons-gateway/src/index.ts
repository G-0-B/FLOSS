import { commonsManifest, healthPayload } from "./manifest";
import {
  htmlResponse,
  jsonResponse,
  methodNotAllowedResponse,
  notFoundResponse,
  renderHomePage,
  stripBodyForHead,
  textResponse
} from "./responses";

export interface Env {}

const READ_METHODS = new Set(["GET", "HEAD"]);
const ROBOTS_TXT = `User-agent: *
Allow: /
`;

function route(request: Request): Response {
  const url = new URL(request.url);

  switch (url.pathname) {
    case "/":
      return htmlResponse(renderHomePage(commonsManifest));
    case "/health":
      return jsonResponse(healthPayload, 200, { "Cache-Control": "no-store" });
    case "/manifest":
      return jsonResponse(commonsManifest);
    case "/robots.txt":
      return textResponse(ROBOTS_TXT);
    default:
      return notFoundResponse(url.pathname);
  }
}

export default {
  async fetch(
    request: Request,
    _env: Env,
    _ctx: ExecutionContext
  ): Promise<Response> {
    if (!READ_METHODS.has(request.method)) {
      return methodNotAllowedResponse(request.method);
    }

    const response = route(request);
    if (request.method === "HEAD") {
      return stripBodyForHead(response);
    }

    return response;
  }
} satisfies ExportedHandler<Env>;
