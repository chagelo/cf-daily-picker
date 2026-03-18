"""Telegram push via Bot API."""

import logging

import requests

logger = logging.getLogger(__name__)


def send(cfg: dict, markdown_text: str) -> bool:
    """Send message to Telegram via Bot API.

    cfg should contain: bot_token, chat_id
    """
    bot_token = cfg.get("bot_token", "")
    chat_id = cfg.get("chat_id", "")

    if not bot_token or not chat_id:
        logger.warning("Telegram not configured, skipping")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Telegram has a 4096 char limit per message, split if needed
    chunks = _split_message(markdown_text, 4000)
    success = True
    for chunk in chunks:
        try:
            resp = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                logger.error("Telegram API error: %s", data.get("description"))
                success = False
        except Exception as e:
            logger.error("Telegram send failed: %s", e)
            success = False

    return success


def _split_message(text: str, max_len: int) -> list[str]:
    """Split long text into chunks."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split at last newline before max_len
        idx = text.rfind("\n", 0, max_len)
        if idx == -1:
            idx = max_len
        chunks.append(text[:idx])
        text = text[idx:].lstrip("\n")
    return chunks
