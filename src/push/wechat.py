"""WeChat push via Server酱 (ServerChan)."""

import logging

import requests

logger = logging.getLogger(__name__)

SERVERCHAN_URL = "https://sctapi.ftqq.com/{key}.send"


def send(cfg: dict, markdown_text: str, **kwargs) -> bool:
    """Send message to WeChat via Server酱.

    cfg should contain: server_chan_key
    """
    key = cfg.get("server_chan_key", "")
    if not key:
        logger.warning("WeChat (Server酱) not configured, skipping")
        return False

    url = SERVERCHAN_URL.format(key=key)

    # Server酱 accepts title + desp (Markdown body)
    # Split first line as title
    lines = markdown_text.strip().split("\n", 1)
    title = lines[0].strip("# ").strip()
    desp = lines[1] if len(lines) > 1 else ""

    try:
        resp = requests.post(
            url,
            data={
                "title": title,
                "desp": desp,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            logger.error("Server酱 error: %s", data.get("message"))
            return False
        return True
    except Exception as e:
        logger.error("WeChat send failed: %s", e)
        return False
