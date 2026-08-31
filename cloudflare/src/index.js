export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);

    if (!env.ORIGIN_URL || env.ORIGIN_URL.includes("REPLACE-WITH")) {
      return new Response("Cloudflare Worker origin is not configured.", { status: 503 });
    }

    const origin = new URL(env.ORIGIN_URL);
    const target = new URL(origin.toString());
    target.pathname = incoming.pathname;
    target.search = incoming.search;

    const headers = new Headers(request.headers);
    headers.set("x-forwarded-host", incoming.host);
    headers.set("x-forwarded-proto", incoming.protocol.replace(":", ""));

    return fetch(new Request(target, {
      method: request.method,
      headers,
      body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
      redirect: "manual"
    }));
  }
};
