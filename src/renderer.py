"""Render problem cards as an HTML file with KaTeX support."""

import re
import html
import os
from datetime import datetime


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
TEMPLATE_FILE = os.path.join(TEMPLATE_DIR, "daily.html")

CARD_HTML = """\
<div class="card">
  <div class="card-header">
    <h2 class="card-title"><a href="{url}" target="_blank">{title}</a></h2>
    <span class="rating-badge">Rating {rating}</span>
  </div>
  <div class="tags">{tags}</div>
  {sections}
</div>
"""


def _load_template() -> str:
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _md_to_html_simple(text: str) -> str:
    """Minimal Markdown to HTML conversion.

    Handles headings, bold, italic, code blocks, inline code, and lists.
    Preserves LaTeX $...$ and $$...$$ for KaTeX.
    """
    lines = text.split("\n")
    result = []
    in_code_block = False
    in_list = False

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                result.append("</code></pre>")
                in_code_block = False
            else:
                lang = line.strip()[3:].strip()
                result.append(f"<pre><code class=\"language-{html.escape(lang)}\">")
                in_code_block = True
            continue

        if in_code_block:
            result.append(html.escape(line))
            continue

        # Close list if needed
        if in_list and not line.strip().startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            result.append("</ul>")
            in_list = False

        stripped = line.strip()

        # Empty line
        if not stripped:
            result.append("<br>")
            continue

        # Headings
        if stripped.startswith("#### "):
            result.append(f"<h4>{_inline_md(stripped[5:])}</h4>")
        elif stripped.startswith("### "):
            result.append(f"<h3>{_inline_md(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            result.append(f"<h3>{_inline_md(stripped[3:])}</h3>")
        elif stripped.startswith("# "):
            result.append(f"<h2>{_inline_md(stripped[2:])}</h2>")
        # List items
        elif stripped.startswith(("- ", "* ")):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{_inline_md(stripped[2:])}</li>")
        elif re.match(r"^\d+\.\s", stripped):
            if not in_list:
                result.append("<ul>")
                in_list = True
            text_part = re.sub(r"^\d+\.\s", "", stripped)
            result.append(f"<li>{_inline_md(text_part)}</li>")
        else:
            result.append(f"<p>{_inline_md(stripped)}</p>")

    if in_list:
        result.append("</ul>")
    if in_code_block:
        result.append("</code></pre>")

    return "\n".join(result)


def _inline_md(text: str) -> str:
    """Convert inline Markdown (bold, italic, code) to HTML, preserving LaTeX."""
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\$)\*(.+?)\*(?!\$)", r"<em>\1</em>", text)
    return text


def _build_card(card: dict) -> str:
    """Build HTML for a single problem card."""
    sections = []

    if card.get("keypoints"):
        sections.append(
            f'<div class="section">'
            f'<div class="section-title">题面要点</div>'
            f'<div class="section-content">{_md_to_html_simple(card["keypoints"])}</div>'
            f'</div>'
        )

    if card.get("editorial"):
        sections.append(
            f'<div class="section">'
            f'<div class="section-title">题解</div>'
            f'<div class="section-content">{_md_to_html_simple(card["editorial"])}</div>'
            f'</div>'
        )

    if card.get("detailed_explanation"):
        sections.append(
            f'<div class="section">'
            f'<div class="section-title">详细解析</div>'
            f'<div class="section-content">{_md_to_html_simple(card["detailed_explanation"])}</div>'
            f'</div>'
        )

    tags_html = " ".join(
        f'<span class="tag">{html.escape(t)}</span>' for t in card.get("tags", [])
    ) or '<span class="tag">无</span>'

    return CARD_HTML.format(
        title=html.escape(card.get("title", "")),
        url=html.escape(card.get("url", "")),
        rating=card.get("rating", "?"),
        tags=tags_html,
        sections="\n".join(sections),
    )


def render_html(cards: list[dict]) -> str:
    """Render cards as a complete HTML page with KaTeX."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    template = _load_template()

    cards_html = "\n<hr class=\"divider\">\n".join(
        _build_card(card) for card in cards
    )

    return template.replace("{{date}}", date_str).replace("{{cards_html}}", cards_html)
