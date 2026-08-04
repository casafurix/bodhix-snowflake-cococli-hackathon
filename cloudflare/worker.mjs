const ALLOWED_METHODS = new Set(["GET", "HEAD", "POST", "OPTIONS"]);
const MAX_REQUEST_BYTES = 512 * 1024;
const SECURITY_HEADERS = {
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

function jsonResponse(body, status, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...SECURITY_HEADERS,
      ...extraHeaders,
    },
  });
}

function clientKey(request) {
  return request.headers.get("CF-Connecting-IP") || "unknown-client";
}

async function withinLimit(limiter, key) {
  const result = await limiter.limit({ key });
  return result.success;
}

async function proxyApi(request, env) {
  if (!ALLOWED_METHODS.has(request.method)) {
    return jsonResponse({ detail: "Method not allowed" }, 405, { Allow: "GET, HEAD, POST, OPTIONS" });
  }

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: SECURITY_HEADERS });
  }

  const contentLength = Number(request.headers.get("Content-Length") || "0");
  if (!Number.isFinite(contentLength) || contentLength > MAX_REQUEST_BYTES) {
    return jsonResponse({ detail: "Request body is too large" }, 413);
  }

  let requestBody;
  if (request.method === "POST") {
    requestBody = await request.arrayBuffer();
    if (requestBody.byteLength > MAX_REQUEST_BYTES) {
      return jsonResponse({ detail: "Request body is too large" }, 413);
    }
  }

  const url = new URL(request.url);
  const client = clientKey(request);
  if (!(await withinLimit(env.API_RATE_LIMITER, client))) {
    return jsonResponse({ detail: "Too many requests. Please retry shortly." }, 429, { "Retry-After": "60" });
  }

  if (request.method === "POST") {
    if (!(await withinLimit(env.MUTATION_RATE_LIMITER, client))) {
      return jsonResponse({ detail: "Too many changes. Please retry shortly." }, 429, { "Retry-After": "60" });
    }

    if (url.pathname === "/api/copilot/query" && !(await withinLimit(env.COPILOT_RATE_LIMITER, client))) {
      return jsonResponse({ detail: "Copilot demo limit reached. Please retry in one minute." }, 429, { "Retry-After": "60" });
    }
  }

  const upstreamBase = new URL(env.SNOWFLAKE_ORIGIN);
  const upstreamUrl = new URL(`${url.pathname}${url.search}`, upstreamBase);
  const headers = new Headers({
    Accept: request.headers.get("Accept") || "application/json",
    Authorization: `Snowflake Token="${env.SNOWFLAKE_PAT}"`,
    "User-Agent": "ATLAS-Cloudflare-Gateway/1.0",
  });
  const contentType = request.headers.get("Content-Type");
  if (contentType) headers.set("Content-Type", contentType);

  let upstream;
  try {
    upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: requestBody,
      redirect: "manual",
    });
  } catch {
    return jsonResponse(
      { detail: "ATLAS is temporarily unable to reach its governed Snowflake service." },
      502,
    );
  }

  const responseHeaders = new Headers();
  const responseContentType = upstream.headers.get("Content-Type");
  if (responseContentType) responseHeaders.set("Content-Type", responseContentType);
  responseHeaders.set("Cache-Control", "no-store");
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) responseHeaders.set(name, value);

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api" || url.pathname.startsWith("/api/")) {
      return proxyApi(request, env);
    }

    const response = await env.ASSETS.fetch(request);
    const headers = new Headers(response.headers);
    for (const [name, value] of Object.entries(SECURITY_HEADERS)) headers.set(name, value);
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
