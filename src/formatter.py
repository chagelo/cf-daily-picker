"""Format messages for push channels."""

from datetime import datetime


def format_problem_card(problem: dict, editorial: str,
                        keypoints: str = None,
                        detailed_explanation: str = None) -> dict:
    """Create a structured problem card."""
    contest_id = problem.get("contestId", "")
    index = problem.get("index", "")
    name = problem.get("name", "Unknown")
    rating = problem.get("rating", "?")
    tags = problem.get("tags", [])
    url = f"https://codeforces.com/contest/{contest_id}/problem/{index}"

    return {
        "title": f"{contest_id}{index} - {name}",
        "url": url,
        "rating": rating,
        "tags": tags,
        "keypoints": keypoints,
        "editorial": editorial,
        "detailed_explanation": detailed_explanation,
    }


def format_markdown(cards: list[dict]) -> str:
    """Format cards as Markdown text."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# CF 每日练习 ({date_str})\n"]

    for i, card in enumerate(cards, 1):
        lines.append(f"## 题目 {i}: {card['title']}")
        lines.append(f"- 难度: {card['rating']}")
        lines.append(f"- 标签: {', '.join(card['tags']) if card['tags'] else '无'}")
        lines.append(f"- 链接: {card['url']}")

        if card.get("keypoints"):
            lines.append(f"\n### 题面要点\n")
            lines.append(card["keypoints"])

        lines.append(f"\n### 题解\n")
        lines.append(card["editorial"])

        if card.get("detailed_explanation"):
            lines.append(f"\n### 详细解析\n")
            lines.append(card["detailed_explanation"])

        lines.append("\n---\n")

    return "\n".join(lines)


def format_summary(cards: list[dict]) -> str:
    """Format a brief text summary for Telegram message (no editorial content)."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = [f"CF 每日练习 ({date_str})\n"]

    for i, card in enumerate(cards, 1):
        lines.append(f"题目 {i}: {card['title']}")
        lines.append(f"难度: {card['rating']}")
        tags = ", ".join(card["tags"]) if card.get("tags") else "无"
        lines.append(f"标签: {tags}")
        lines.append(f"链接: {card['url']}")
        lines.append("")

    lines.append("完整题解见附件")
    return "\n".join(lines)
    """Format cards as plain text (for channels that don't support Markdown)."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = [f"CF 每日练习 ({date_str})\n{'=' * 30}\n"]

    for i, card in enumerate(cards, 1):
        lines.append(f"[题目 {i}] {card['title']}")
        lines.append(f"难度: {card['rating']}")
        lines.append(f"标签: {', '.join(card['tags']) if card['tags'] else '无'}")
        lines.append(f"链接: {card['url']}")

        if card.get("keypoints"):
            lines.append(f"\n--- 题面要点 ---\n{card['keypoints']}")

        lines.append(f"\n--- 题解 ---\n{card['editorial']}")

        if card.get("detailed_explanation"):
            lines.append(f"\n--- 详细解析 ---\n{card['detailed_explanation']}")

        lines.append(f"\n{'=' * 30}\n")

    return "\n".join(lines)
