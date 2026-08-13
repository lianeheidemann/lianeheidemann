#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

USERNAME = "lianeheidemann"
ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "assets" / "github-stats.svg"
README_PATH = ROOT / "README.md"
TOKEN = os.getenv("GITHUB_TOKEN", "")


def request_json(url: str, *, data: dict | None = None) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "lianeheidemann-profile-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    payload = None
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_public_repositories() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        batch = request_json(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?type=owner&sort=updated&per_page=100&page={page}"
        )
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected GitHub repositories response")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def get_year_contributions(year: int) -> int | str:
    if not TOKEN:
        return "—"

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar { totalContributions }
        }
      }
    }
    """
    variables = {
        "login": USERNAME,
        "from": f"{year}-01-01T00:00:00Z",
        "to": f"{year}-12-31T23:59:59Z",
    }
    try:
        result = request_json(
            "https://api.github.com/graphql",
            data={"query": query, "variables": variables},
        )
        return int(
            result["data"]["user"]["contributionsCollection"]
            ["contributionCalendar"]["totalContributions"]
        )
    except (KeyError, TypeError, ValueError, urllib.error.URLError):
        return "—"


def render_svg(*, public_repos: int, stars: int, followers: int, contributions: int | str, year: int) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-labelledby="title description">
  <title id="title">Liane Heidemann GitHub live stats</title>
  <desc id="description">Automatically updated GitHub statistics: public repositories, stars earned, followers and {year} contributions.</desc>

  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1200" y2="300" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#040817"/>
      <stop offset="0.5" stop-color="#091224"/>
      <stop offset="1" stop-color="#0b1020"/>
    </linearGradient>
    <linearGradient id="flow" x1="0" y1="0" x2="1200" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#22d3ee"/>
      <stop offset="0.4" stop-color="#38bdf8"/>
      <stop offset="0.68" stop-color="#8b5cf6"/>
      <stop offset="1" stop-color="#22d3ee"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-160 0;160 0;-160 0" dur="9s" repeatCount="indefinite"/>
    </linearGradient>
    <radialGradient id="core" cx="50%" cy="45%" r="58%">
      <stop offset="0" stop-color="#22d3ee" stop-opacity="0.18"/>
      <stop offset="0.52" stop-color="#3b82f6" stop-opacity="0.08"/>
      <stop offset="1" stop-color="#040817" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">
      <path d="M36 0H0V36" fill="none" stroke="#67e8f9" stroke-opacity="0.055">
        <animateTransform attributeName="transform" type="translate" values="0 0;36 36;0 0" dur="24s" repeatCount="indefinite"/>
      </path>
    </pattern>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3.5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      .micro {{ font: 700 11px 'Segoe UI', Arial, sans-serif; letter-spacing: 4px; }}
      .value {{ font: 800 34px 'Segoe UI', Arial, sans-serif; }}
      .label {{ font: 700 11px 'Segoe UI', Arial, sans-serif; letter-spacing: 1.8px; }}
      .meta {{ font: 600 11px 'Segoe UI', Arial, sans-serif; letter-spacing: 1.2px; }}
    </style>
  </defs>

  <rect width="1200" height="300" rx="30" fill="url(#background)"/>
  <rect width="1200" height="300" rx="30" fill="url(#grid)"/>
  <ellipse cx="600" cy="145" rx="360" ry="190" fill="url(#core)">
    <animate attributeName="rx" values="350;390;350" dur="10s" repeatCount="indefinite"/>
  </ellipse>

  <rect x="8" y="8" width="1184" height="284" rx="26" fill="none" stroke="url(#flow)" stroke-width="2" stroke-opacity="0.76" stroke-dasharray="500 110" stroke-linecap="round">
    <animate attributeName="stroke-dashoffset" from="0" to="-610" dur="20s" repeatCount="indefinite"/>
  </rect>

  <g font-family="'Segoe UI',Arial,sans-serif" text-anchor="middle">
    <text x="600" y="52" class="micro" fill="#8be9f5">GITHUB // LIVE METRICS</text>
  </g>

  <g fill="none" stroke="url(#flow)" stroke-linecap="round" filter="url(#glow)">
    <path d="M105 82H1095" stroke-width="2" stroke-opacity="0.72"/>
  </g>

  <g font-family="'Segoe UI',Arial,sans-serif" text-anchor="middle">
    <g transform="translate(72 104)">
      <rect width="246" height="116" rx="20" fill="#071426" fill-opacity="0.86" stroke="#22d3ee" stroke-opacity="0.52"/>
      <circle cx="123" cy="27" r="5" fill="#22d3ee" filter="url(#glow)"><animate attributeName="opacity" values="0.45;1;0.45" dur="3.2s" repeatCount="indefinite"/></circle>
      <text x="123" y="68" class="value" fill="#f8fafc">{public_repos}</text>
      <text x="123" y="94" class="label" fill="#67e8f9">PUBLIC REPOS</text>
    </g>

    <g transform="translate(342 104)">
      <rect width="246" height="116" rx="20" fill="#071426" fill-opacity="0.86" stroke="#60a5fa" stroke-opacity="0.52"/>
      <path d="M123 18l3.3 6.7 7.4 1.1-5.4 5.2 1.3 7.4-6.6-3.5-6.6 3.5 1.3-7.4-5.4-5.2 7.4-1.1z" fill="#93c5fd" opacity="0.9"/>
      <text x="123" y="68" class="value" fill="#f8fafc">{stars}</text>
      <text x="123" y="94" class="label" fill="#93c5fd">STARS EARNED</text>
    </g>

    <g transform="translate(612 104)">
      <rect width="246" height="116" rx="20" fill="#071426" fill-opacity="0.86" stroke="#8b5cf6" stroke-opacity="0.56"/>
      <circle cx="123" cy="23" r="7" fill="none" stroke="#c4b5fd" stroke-width="2"/>
      <path d="M111 39c3-7 21-7 24 0" fill="none" stroke="#c4b5fd" stroke-width="2" stroke-linecap="round"/>
      <text x="123" y="68" class="value" fill="#f8fafc">{followers}</text>
      <text x="123" y="94" class="label" fill="#c4b5fd">FOLLOWERS</text>
    </g>

    <g transform="translate(882 104)">
      <rect width="246" height="116" rx="20" fill="#071426" fill-opacity="0.86" stroke="#22d3ee" stroke-opacity="0.52"/>
      <path d="M113 23h20M123 13v20" stroke="#67e8f9" stroke-width="2.2" stroke-linecap="round" filter="url(#glow)"/>
      <text x="123" y="68" class="value" fill="#f8fafc">{contributions}</text>
      <text x="123" y="94" class="label" fill="#67e8f9">CONTRIBUTIONS {year}</text>
    </g>
  </g>

  <g font-family="'Segoe UI',Arial,sans-serif" text-anchor="middle">
    <text x="600" y="267" class="meta" fill="#718096">AUTO-SYNC · GITHUB ACTIONS</text>
  </g>
</svg>
'''


def main() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    year = now.year

    user = request_json(f"https://api.github.com/users/{USERNAME}")
    repos = get_public_repositories()

    public_repos = int(user["public_repos"])
    followers = int(user["followers"])
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos if not repo.get("fork", False))
    contributions = get_year_contributions(year)

    SVG_PATH.write_text(
        render_svg(
            public_repos=public_repos,
            stars=stars,
            followers=followers,
            contributions=contributions,
            year=year,
        ),
        encoding="utf-8",
    )

    cache_key = f"{public_repos}-{stars}-{followers}-{contributions}-{year}"
    readme = README_PATH.read_text(encoding="utf-8")
    readme = re.sub(
        r"(assets/github-stats\.svg\?v=)[^\"') >]+",
        rf"\g<1>{cache_key}",
        readme,
    )
    README_PATH.write_text(readme, encoding="utf-8")

    print(
        f"Updated stats: repos={public_repos}, stars={stars}, "
        f"followers={followers}, contributions={contributions}, year={year}"
    )


if __name__ == "__main__":
    main()
