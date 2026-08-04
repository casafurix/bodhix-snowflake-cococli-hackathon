import assert from "node:assert/strict";
import test from "node:test";

import worker from "./worker.mjs";

function env(overrides = {}) {
  const allow = { limit: async () => ({ success: true }) };
  return {
    SNOWFLAKE_ORIGIN: "https://snowflake.example",
    SNOWFLAKE_PAT: "server-side-secret",
    API_RATE_LIMITER: allow,
    MUTATION_RATE_LIMITER: allow,
    COPILOT_RATE_LIMITER: allow,
    ASSETS: { fetch: async () => new Response("asset") },
    ...overrides,
  };
}

test("proxies API calls with the server-side Snowflake token", async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });

  globalThis.fetch = async (url, init) => {
    assert.equal(url.toString(), "https://snowflake.example/api/health?full=true");
    assert.equal(init.headers.get("Authorization"), 'Snowflake Token="server-side-secret"');
    assert.equal(init.headers.get("Sf-Context-Current-User"), null);
    return new Response(JSON.stringify({ status: "ok" }), {
      headers: { "Content-Type": "application/json" },
    });
  };

  const response = await worker.fetch(
    new Request("https://atlas.example/api/health?full=true", {
      headers: {
        Authorization: "attacker-token",
        "Sf-Context-Current-User": "spoofed-user",
      },
    }),
    env(),
  );

  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: "ok" });
  assert.equal(response.headers.get("Cache-Control"), "no-store");
});

test("rate limits requests before contacting Snowflake", async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  globalThis.fetch = async () => {
    throw new Error("upstream should not be called");
  };

  const response = await worker.fetch(
    new Request("https://atlas.example/api/dashboard", {
      headers: { "CF-Connecting-IP": "203.0.113.10" },
    }),
    env({ API_RATE_LIMITER: { limit: async () => ({ success: false }) } }),
  );

  assert.equal(response.status, 429);
  assert.equal(response.headers.get("Retry-After"), "60");
});

test("rejects oversized streamed request bodies", async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  globalThis.fetch = async () => {
    throw new Error("upstream should not be called");
  };

  const response = await worker.fetch(
    new Request("https://atlas.example/api/cohorts/import", {
      method: "POST",
      body: "x".repeat(512 * 1024 + 1),
    }),
    env(),
  );

  assert.equal(response.status, 413);
});

test("serves non-API routes from static assets", async () => {
  const response = await worker.fetch(
    new Request("https://atlas.example/trials"),
    env({ ASSETS: { fetch: async () => new Response("ATLAS SPA") } }),
  );

  assert.equal(response.status, 200);
  assert.equal(await response.text(), "ATLAS SPA");
  assert.equal(response.headers.get("X-Frame-Options"), "DENY");
});

test("fetches a ClinicalTrials.gov record before sending it to Snowflake", async (t) => {
  const originalFetch = globalThis.fetch;
  t.after(() => { globalThis.fetch = originalFetch; });
  const publicRecord = {
    protocolSection: {
      identificationModule: { nctId: "NCT00749190", briefTitle: "Public trial" },
    },
  };
  let calls = 0;
  globalThis.fetch = async (url, init) => {
    calls += 1;
    if (calls === 1) {
      assert.equal(url, "https://clinicaltrials.gov/api/v2/studies/NCT00749190");
      return Response.json(publicRecord);
    }
    assert.equal(url.toString(), "https://snowflake.example/api/trials/sync-record");
    assert.deepEqual(JSON.parse(init.body), { source: "NCT00749190", payload: publicRecord });
    return Response.json({ protocol_id: "NCT00749190", processing_state: "PENDING_EXTRACTION" }, { status: 201 });
  };

  const response = await worker.fetch(
    new Request("https://atlas.example/api/trials/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: "NCT00749190" }),
    }),
    env(),
  );

  assert.equal(response.status, 201);
  assert.equal((await response.json()).protocol_id, "NCT00749190");
  assert.equal(calls, 2);
});

test("does not expose the trusted trial-record intake route publicly", async () => {
  const response = await worker.fetch(
    new Request("https://atlas.example/api/trials/sync-record", {
      method: "POST",
      body: "{}",
    }),
    env(),
  );
  assert.equal(response.status, 404);
});
