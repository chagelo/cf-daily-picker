"""Telegram push via Bot API."""

import logging
import os
import tempfile

import requests

logger = logging.getLogger(__name__)


def send(cfg: dict, summary_text: str, html_content: str = None) -> bool:
    """Send summary message + optional HTML file to Telegram.

    cfg should contain: bot_token, chat_id
    """
    bot_token = cfg.get("bot_token", "")
    chat_id = cfg.get("chat_id", "")

    if not bot_token or not chat_id:
        logger.warning("Telegram not configured, skipping")
        return False

    success = True

    # 1. Send text summary
    msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(
            msg_url,
            json={
                "chat_id": chat_id,
                "text": summary_text,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            logger.error("Telegram sendMessage error: %s", data.get("description"))
            success = False
    except Exception as e:
        logger.error("Telegram sendMessage failed: %s", e)
        success = False

    # 2. Send HTML file as document
    if html_content:
        doc_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", prefix="cf_daily_", delete=False, encoding="utf-8"
            ) as f:
                f.write(html_content)
                tmp_path = f.name

            with open(tmp_path, "rb") as f:
                resp = requests.post(
                    doc_url,
                    data={
                        "chat_id": chat_id,
                        "caption": "CF 每日练习 - 完整题解",
                    },
                    files={"document": ("cf_daily.html", f, "text/html")},
                    timeout=30,
                )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                logger.error("Telegram sendDocument error: %s", data.get("description"))
                success = False
        except Exception as e:
            logger.error("Telegram sendDocument failed: %s", e)
            success = False
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return success
