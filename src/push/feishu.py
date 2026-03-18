"""Feishu (Lark) push via custom bot webhook."""

import logging

import requests

logger = logging.getLogger(__name__)


def send(cfg: dict, markdown_text: str, **kwargs) -> bool:
    """Send message to Feishu via webhook.

    cfg should contain: webhook_url
    """
    webhook_url = cfg.get("webhook_url", "")
    if not webhook_url:
        logger.warning("Feishu not configured, skipping")
        return False

    # Feishu custom bot supports rich text (post) format
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "CF 每日练习",
                },
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": markdown_text,
                }
            ],
        },
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0 and data.get("StatusCode") != 0:
            # Some webhook versions use different response formats
            if "ok" not in str(data).lower() and data.get("code") != 0:
                logger.error("Feishu API error: %s", data)
                return False
        return True
    except Exception as e:
        logger.error("Feishu send failed: %s", e)
        return False
