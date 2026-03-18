"""Editorial fetcher: official Codeforces editorial scraping + LLM fallback.

Also provides LLM-powered enhancements:
  - extract_problem_keypoints: extract key points from problem statement
  - explain_editorial_detail: produce a more detailed explanation of the editorial
"""

import re
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CF_CONTEST_URL = "https://codeforces.com/contest/{contest_id}"
CF_BLOG_URL = "https://codeforces.com/blog/entry/{blog_id}"


# ---------------------------------------------------------------------------
# Internal: common LLM call helper
# ---------------------------------------------------------------------------

def _call_llm(llm_cfg: dict, system_prompt: str, user_prompt: str) -> str | None:
    """Send a chat completion request to an OpenAI-compatible API."""
    api_base = llm_cfg.get("api_base", "").rstrip("/")
    api_key = llm_cfg.get("api_key", "")
    model = llm_cfg.get("model", "gpt-4o-mini")

    if not api_key:
        logger.warning("LLM API key not configured, skipping")
        return None

    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return None


def _find_editorial_blog_id(contest_id: int) -> int | None:
    """Try to find the editorial blog entry ID from the contest materials page."""
    url = f"https://codeforces.com/blog/entry/{contest_id}"
    # Codeforces editorial links are usually posted on contest announcement
    # or linked from contest page. Try common patterns.
    materials_url = f"https://codeforces.com/contest/{contest_id}"
    try:
        resp = requests.get(materials_url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    # Look for links containing "editorial" or "Tutorial" or "разбор"
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True).lower()
        if any(kw in text for kw in ("editorial", "tutorial", "разбор", "题解")):
            m = re.search(r"/blog/entry/(\d+)", href)
            if m:
                return int(m.group(1))
    return None


def _scrape_blog_content(blog_id: int) -> str | None:
    """Scrape the content of a Codeforces blog entry."""
    url = f"https://codeforces.com/blog/entry/{blog_id}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Failed to fetch blog %d: %s", blog_id, e)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    content_div = soup.find("div", class_="ttypography")
    if not content_div:
        return None
    return content_div.get_text(separator="\n", strip=True)


def _extract_problem_editorial(full_text: str, problem_index: str) -> str:
    """Try to extract the section for a specific problem from the full editorial."""
    # Common patterns: "Problem A", "A.", "A —", "Problem A."
    patterns = [
        rf"(?:Problem\s+)?{re.escape(problem_index)}\s*[\.\—\-\:]",
        rf"\b{re.escape(problem_index)}\b\s*[\.\—\-\:]",
    ]
    lines = full_text.split("\n")
    capturing = False
    result = []
    next_index = chr(ord(problem_index[0]) + 1) if len(problem_index) == 1 else None

    for line in lines:
        if not capturing:
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    capturing = True
                    result.append(line)
                    break
        else:
            # Stop if we hit the next problem section
            if next_index:
                stop_patterns = [
                    rf"(?:Problem\s+)?{re.escape(next_index)}\s*[\.\—\-\:]",
                ]
                if any(re.search(sp, line, re.IGNORECASE) for sp in stop_patterns):
                    break
            result.append(line)

    return "\n".join(result).strip() if result else full_text


def fetch_official_editorial(contest_id: int, problem_index: str) -> str | None:
    """Fetch official editorial for a specific problem."""
    blog_id = _find_editorial_blog_id(contest_id)
    if blog_id is None:
        logger.info("No editorial blog found for contest %d", contest_id)
        return None

    full_text = _scrape_blog_content(blog_id)
    if not full_text:
        return None

    editorial = _extract_problem_editorial(full_text, problem_index)
    return editorial if editorial else None


def generate_llm_editorial(problem: dict, llm_cfg: dict) -> str | None:
    """Use LLM to generate an editorial in Chinese."""
    problem_name = problem.get("name", "Unknown")
    contest_id = problem.get("contestId", "")
    index = problem.get("index", "")
    tags = ", ".join(problem.get("tags", []))
    rating = problem.get("rating", "?")
    problem_url = f"https://codeforces.com/contest/{contest_id}/problem/{index}"

    user_prompt = (
        f"请为以下 Codeforces 题目提供一份中文题解，包括思路分析和关键步骤：\n\n"
        f"题目: {problem_name}\n"
        f"链接: {problem_url}\n"
        f"难度: {rating}\n"
        f"标签: {tags}\n\n"
        f"要求:\n"
        f"1. 用中文撰写\n"
        f"2. 先简述题意\n"
        f"3. 分析解题思路\n"
        f"4. 给出关键步骤或伪代码\n"
        f"5. 分析时间复杂度"
    )
    return _call_llm(
        llm_cfg,
        "你是一个竞赛编程专家，擅长分析算法题目并用中文撰写清晰的题解。",
        user_prompt,
    )


def get_editorial(problem: dict, editorial_cfg: dict, llm_cfg: dict) -> str:
    """Get editorial for a problem, trying official first, then LLM fallback."""
    contest_id = problem.get("contestId")
    problem_index = problem.get("index", "A")
    editorial = None

    # Try official editorial
    if editorial_cfg.get("official", True):
        editorial = fetch_official_editorial(contest_id, problem_index)
        if editorial:
            logger.info("Found official editorial for %d%s", contest_id, problem_index)
            return f"[官方题解]\n{editorial}"

    # LLM fallback
    if editorial_cfg.get("llm_fallback", False):
        editorial = generate_llm_editorial(problem, llm_cfg)
        if editorial:
            logger.info("Generated LLM editorial for %d%s", contest_id, problem_index)
            return f"[AI 生成题解]\n{editorial}"

    return "暂无题解"


# ---------------------------------------------------------------------------
# LLM enhancements
# ---------------------------------------------------------------------------

def _scrape_problem_statement(contest_id: int, problem_index: str) -> str | None:
    """Scrape the problem statement text from Codeforces."""
    url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_index}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Failed to fetch problem page %d%s: %s", contest_id, problem_index, e)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    statement_div = soup.find("div", class_="problem-statement")
    if not statement_div:
        return None
    return statement_div.get_text(separator="\n", strip=True)


def extract_problem_keypoints(problem: dict, llm_cfg: dict) -> str | None:
    """Use LLM to extract key points from the problem statement.

    Returns a concise Chinese summary covering:
      - 题意概述
      - 输入/输出含义
      - 关键约束条件
      - 需要特别注意的边界/陷阱
    """
    contest_id = problem.get("contestId")
    index = problem.get("index", "A")
    statement = _scrape_problem_statement(contest_id, index)
    if not statement:
        logger.warning("Cannot scrape problem statement for %d%s, skipping keypoints", contest_id, index)
        return None

    user_prompt = (
        f"以下是一道 Codeforces 题目的完整题面：\n\n"
        f"{statement}\n\n"
        f"请用中文提取并整理这道题的要点，包括：\n"
        f"1. 一句话概括题意\n"
        f"2. 输入/输出各字段的含义\n"
        f"3. 关键约束条件（数据范围、特殊限制）\n"
        f"4. 容易忽略的边界情况或陷阱\n\n"
        f"要求简洁清晰，使用列表格式。"
    )
    return _call_llm(
        llm_cfg,
        "你是一个竞赛编程专家，擅长从英文题面中快速提炼关键信息并用中文呈现。",
        user_prompt,
    )


def explain_editorial_detail(problem: dict, editorial: str, llm_cfg: dict) -> str | None:
    """Use LLM to produce a more detailed explanation of the editorial.

    Takes the existing editorial and expands it with:
      - 更详细的推导过程
      - 具体例子辅助理解
      - 为什么这样做是对的（正确性论证）
      - 常见错误写法提示
    """
    problem_name = problem.get("name", "Unknown")
    contest_id = problem.get("contestId", "")
    index = problem.get("index", "")
    rating = problem.get("rating", "?")
    tags = ", ".join(problem.get("tags", []))

    user_prompt = (
        f"题目: {contest_id}{index} - {problem_name} (难度 {rating}, 标签: {tags})\n\n"
        f"以下是这道题的题解：\n\n"
        f"{editorial}\n\n"
        f"请基于上述题解，用中文给出一份更详细的解释，包括：\n"
        f"1. 逐步推导思路的来源（为什么会想到这个方法）\n"
        f"2. 用具体的小例子辅助说明关键步骤\n"
        f"3. 正确性论证（为什么这样做是对的）\n"
        f"4. 常见的错误写法或容易踩的坑\n"
        f"5. 如果有优化空间，简要提及\n\n"
        f"要求语言通俗易懂，适合正在学习算法的人阅读。"
    )
    return _call_llm(
        llm_cfg,
        "你是一个竞赛编程教练，擅长把题解讲解得通俗易懂，善于用例子帮助理解。",
        user_prompt,
    )
