export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Target: https://codeforces.com/...
    const target = "https://codeforces.com" + url.pathname + url.search;

    try {
      const resp = await fetch(target, {
        method: request.method,
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
          Accept: "text/html,application/json",
          "Accept-Language": "en-US,en;q=0.9",
        },
        redirect: "follow",
      });

      const body = await resp.text();

      // Forward the original status and content-type
      return new Response(body, {
        status: resp.status,
        headers: {
          "Content-Type": resp.headers.get("Content-Type") || "application/json",
          "Access-Control-Allow-Origin": "*",
          "X-Proxy-Status": resp.status.toString(),
        },
      });
    } catch (err) {
      return new Response(
        JSON.stringify({ error: "proxy_fetch_failed", message: err.message }),
        {
          status: 502,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
    }
  },
};
