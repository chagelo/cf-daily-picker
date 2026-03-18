#!/usr/bin/env python3
"""CF Daily Picker — 每日自动抓取 Codeforces 题目 + 题解并推送。"""

import logging
import sys
import os

import yaml

from src.codeforces import pick_problems
from src.editorial import get_editorial, extract_problem_keypoints, translate_editorial, explain_editorial_detail
from src.storage import load_sent_ids, mark_as_sent
from src.formatter import format_problem_card, format_markdown, format_summary
from src.renderer import render_html
from src.push import telegram, feishu, wechat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(path: str = None) -> dict:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    _override_from_env(cfg)
    return cfg


def _override_from_env(cfg: dict):
    """Override sensitive config values from environment variables."""
    env_map = {
        "TG_BOT_TOKEN": ("push", "telegram", "bot_token"),
        "TG_CHAT_ID": ("push", "telegram", "chat_id"),
        "FEISHU_WEBHOOK": ("push", "feishu", "webhook_url"),
        "WECHAT_KEY": ("push", "wechat", "server_chan_key"),
        "LLM_API_KEY": ("llm", "api_key"),
    }
    for env_var, keys in env_map.items():
        val = os.environ.get(env_var)
        if val:
            d = cfg
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = val


def run(config_path: str = None):
    cfg = load_config(config_path)
    cf_cfg = cfg.get("codeforces", {})
    editorial_cfg = cfg.get("editorial", {})
    enhance_cfg = cfg.get("enhance", {})
    llm_cfg = cfg.get("llm", {})
    push_cfg = cfg.get("push", {})

    # 1. Pick problems
    exclude_ids = load_sent_ids()
    logger.info("Already sent %d problems, picking new ones...", len(exclude_ids))

    problems = pick_problems(cf_cfg, exclude_ids)
    if not problems:
        logger.warning("No suitable problems found, exiting")
        return

    logger.info("Picked %d problems:", len(problems))
    for p in problems:
        logger.info("  %d%s - %s (rating %s)", p["contestId"], p["index"], p["name"], p.get("rating"))

    # 2. Get editorials + LLM enhancements
    cards = []
    for p in problems:
        editorial = get_editorial(p, editorial_cfg, llm_cfg)

        # Always translate editorial to Chinese and fix formatting
        if editorial != "暂无题解":
            logger.info("Translating editorial for %d%s...", p["contestId"], p["index"])
            translated = translate_editorial(p, editorial, llm_cfg)
            if translated:
                editorial = f"[中文题解]\n{translated}"

        # Optional: LLM extracts key points from problem statement
        keypoints = None
        if enhance_cfg.get("extract_problem_keypoints", False):
            logger.info("Extracting keypoints for %d%s...", p["contestId"], p["index"])
            keypoints = extract_problem_keypoints(p, llm_cfg)

        # Optional: LLM explains editorial in more detail
        detailed = None
        if enhance_cfg.get("explain_editorial", False) and editorial != "暂无题解":
            logger.info("Generating detailed explanation for %d%s...", p["contestId"], p["index"])
            detailed = explain_editorial_detail(p, editorial, llm_cfg)

        card = format_problem_card(p, editorial, keypoints, detailed)
        cards.append(card)

    # 3. Format messages
    summary = format_summary(cards)
    html_content = render_html(cards)
    markdown_message = format_markdown(cards)
    logger.info("Messages formatted (summary: %d chars, html: %d chars)", len(summary), len(html_content))

    # 4. Push to enabled channels
    channels = {
        "telegram": telegram,
        "feishu": feishu,
        "wechat": wechat,
    }

    sent_any = False
    for name, module in channels.items():
        ch_cfg = push_cfg.get(name, {})
        if ch_cfg.get("enabled", False):
            logger.info("Pushing to %s...", name)
            if name == "telegram":
                ok = module.send(ch_cfg, summary, html_content)
            else:
                ok = module.send(ch_cfg, markdown_message)
            if ok:
                logger.info("  %s: success", name)
                sent_any = True
            else:
                logger.error("  %s: failed", name)

    if not sent_any:
        logger.warning("No push channel succeeded or enabled, saving locally")
        print(summary)
        # Save HTML file locally for preview
        out_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(out_dir, exist_ok=True)
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        html_path = os.path.join(out_dir, f"cf_daily_{date_str}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("HTML saved to %s", html_path)

    # 5. Mark as sent
    mark_as_sent(problems)
    logger.info("Done! Marked %d problems as sent.", len(problems))


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    run(config_path)


if __name__ == "__main__":
    main()
