"""Codeforces problem fetcher using official API."""

import random
from typing import Union

import requests


CF_API_PROBLEMS = "https://codeforces.com/api/problemset.problems"
CF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def fetch_all_problems() -> list[dict]:
    """Fetch all problems from Codeforces API."""
    resp = requests.get(CF_API_PROBLEMS, headers=CF_HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK":
        raise RuntimeError(f"Codeforces API error: {data.get('comment', 'unknown')}")
    return data["result"]["problems"]


def resolve_rating(cfg: dict) -> tuple[int, int]:
    """Resolve rating config into (min, max) range.

    Supports:
      - single value: 1000 -> (1000, 1000)
      - range: [1000, 1400] -> (1000, 1400)
      - random mode: pick a random window within rating_random_range
    """
    if cfg.get("random_rating"):
        low, high = cfg.get("rating_random_range", [800, 1600])
        # pick a random base, window size 200
        base = random.randint(low // 100, (high - 200) // 100) * 100
        return base, base + 200

    rating = cfg.get("rating", 1000)
    if isinstance(rating, list):
        return int(rating[0]), int(rating[1])
    return int(rating), int(rating)


def filter_problems(
    problems: list[dict],
    rating_range: tuple[int, int],
    exclude_ids: set[str],
) -> list[dict]:
    """Filter problems by rating range and exclude already-sent ones."""
    rmin, rmax = rating_range
    result = []
    for p in problems:
        r = p.get("rating")
        if r is None:
            continue
        if rmin <= r <= rmax:
            pid = f"{p['contestId']}-{p['index']}"
            if pid not in exclude_ids:
                result.append(p)
    return result


def pick_problems(cfg: dict, exclude_ids: set[str]) -> list[dict]:
    """Main entry: fetch, filter, and pick N problems."""
    all_problems = fetch_all_problems()
    rating_range = resolve_rating(cfg)
    candidates = filter_problems(all_problems, rating_range, exclude_ids)

    count = cfg.get("daily_count", 2)
    if len(candidates) <= count:
        return candidates

    return random.sample(candidates, count)
