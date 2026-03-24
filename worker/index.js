export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Target: https://codeforces.com/...
    const target = "https://codeforces.com" + url.pathname + url.search;

    const resp = await fetch(target, {
      method: request.method,
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        Accept: "text/html,application/json",
        "Accept-Language": "en-US,en;q=0.9",
      },
    });

    // Return response with CORS headers
    const body = await resp.text();
    return new Response(body, {
      status: resp.status,
      headers: {
        "Content-Type": resp.headers.get("Content-Type") || "text/html",
        "Access-Control-Allow-Origin": "*",
      },
    });
  },
};
