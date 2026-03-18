"""入流 push via webhook."""

import logging

import requests

logger = logging.getLogger(__name__)


def send(cfg: dict, markdown_text: str) -> bool:
    """Send message to 入流 via webhook.

    cfg should contain: webhook_url
    The payload format follows common webhook bot conventions.
    Adjust the payload structure if 入流's API differs.
    """
    webhook_url = cfg.get("webhook_url", "")
    if not webhook_url:
        logger.warning("入流 not configured, skipping")
        return False

    # Generic webhook payload — adjust to match 入流 actual API
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "CF 每日练习",
            "text": markdown_text,
        },
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode", 0) != 0:
            logger.error("入流 API error: %s", data.get("errmsg"))
            return False
        return True
    except Exception as e:
        logger.error("入流 send failed: %s", e)
        return False
