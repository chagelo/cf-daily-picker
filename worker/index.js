export default {
  async fetch(request) {
    const url = new URL(request.url);

    // Build target URL on codeforces.com
    const targetUrl = "https://codeforces.com" + url.pathname + url.search;

    const init = {
      method: request.method,
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        Accept: "text/html,application/json",
        "Accept-Language": "en-US,en;q=0.9",
      },
      redirect: "follow",
    };

    try {
      // Use new Request to avoid recursive fetch in Workers
      const targetReq = new Request(targetUrl, init);
      const resp = await fetch(targetReq);

      const body = await resp.text();

      return new Response(body, {
        status: resp.status,
        headers: {
          "Content-Type": resp.headers.get("Content-Type") || "application/json",
          "Access-Control-Allow-Origin": "*",
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
