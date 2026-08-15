#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

USERNAME = "lianeheidemann"
ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "assets" / "image" / "github-stats.svg"
SVG_LIGHT_PATH = ROOT / "assets" / "image" / "github-stats-light.svg"
README_PATHS = sorted(ROOT.glob("README*.md"))
TOKEN = os.getenv("GITHUB_TOKEN", "")

# GitHub counts contributions in the profile's local timezone. Belem (UTC-03,
# no DST) keeps the year and the calendar window aligned with what the profile
# page shows, instead of flipping early on UTC new year's eve.
LOCAL_TZ = dt.timezone(dt.timedelta(hours=-3))

PLACEHOLDER = "—"
PLACEHOLDER_CACHE_KEY = "na"

DARK_THEME = {
    "title_suffix": "",
    "bg_start": "#040817",
    "bg_middle": "#091224",
    "bg_end": "#0b1020",
    "card": "#071426",
    "value": "#f8fafc",
    "micro": "#8be9f5",
    "meta": "#718096",
    "cyan": "#67e8f9",
    "blue": "#93c5fd",
    "violet": "#c4b5fd",
}

LIGHT_THEME = {
    "title_suffix": " — light theme",
    "bg_start": "#F8FBFF",
    "bg_middle": "#EEF4FF",
    "bg_end": "#E8F0FC",
    "card": "#FFFFFF",
    "value": "#0F172A",
    "micro": "#0E7490",
    "meta": "#64748B",
    "cyan": "#0E7490",
    "blue": "#2563EB",
    "violet": "#7C3AED",
}


def request_json(url: str, *, data: dict | None = None, attempts: int = 3) -> dict | list:
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

    last_error: Exception | None = None
    for attempt in range(attempts):
        req = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt == attempts - 1:
                break
            time.sleep(2 ** attempt)

    raise RuntimeError(f"GitHub request failed for {url}: {last_error}") from last_error


def get_user() -> dict:
    user = request_json(f"https://api.github.com/users/{USERNAME}")
    if not isinstance(user, dict):
        raise RuntimeError("Unexpected GitHub user response")
    return user


def get_public_repositories() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        # sort=full_name keeps the ordering stable across pages; sorting by
        # "updated" can shuffle repos between requests and make the star sum
        # skip or double-count a repository.
        batch = request_json(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?type=owner&sort=full_name&direction=asc&per_page=100&page={page}"
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
        print("No GITHUB_TOKEN available; contributions will be rendered as a placeholder.")
        return PLACEHOLDER

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
        "from": f"{year}-01-01T00:00:00-03:00",
        "to": f"{year}-12-31T23:59:59-03:00",
    }
    result = request_json(
        "https://api.github.com/graphql",
        data={"query": query, "variables": variables},
    )
    try:
        return int(
            result["data"]["user"]["contributionsCollection"]
            ["contributionCalendar"]["totalContributions"]
        )
    except (KeyError, TypeError, ValueError) as error:
        # Failing here keeps the last committed values on the profile, which is
        # better than publishing a placeholder over real numbers.
        raise RuntimeError(f"Unexpected contributions response: {result}") from error


def render_svg(
    *,
    public_repos: int,
    stars: int,
    followers: int,
    contributions: int | str,
    year: int,
    theme: dict[str, str],
) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="190" viewBox="0 0 1200 190" role="img" aria-labelledby="title description">
  <title id="title">Liane Heidemann GitHub live stats{theme["title_suffix"]}</title>
  <desc id="description">Automatically updated GitHub statistics: public repositories, stars earned, followers and {year} contributions.</desc>

  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1200" y2="190" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{theme["bg_start"]}"/>
      <stop offset="0.5" stop-color="{theme["bg_middle"]}"/>
      <stop offset="1" stop-color="{theme["bg_end"]}"/>
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
      <stop offset="1" stop-color="{theme["bg_start"]}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">
      <path d="M36 0H0V36" fill="none" stroke="{theme["cyan"]}" stroke-opacity="0.055">
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

  <rect width="1200" height="190" rx="24" fill="url(#background)"/>
  <rect width="1200" height="190" rx="24" fill="url(#grid)"/>
  <ellipse cx="600" cy="92" rx="360" ry="118" fill="url(#core)">
    <animate attributeName="rx" values="350;390;350" dur="10s" repeatCount="indefinite"/>
  </ellipse>

  <rect x="8" y="8" width="1184" height="174" rx="20" fill="none" stroke="url(#flow)" stroke-width="2" stroke-opacity="0.76" stroke-dasharray="500 110" stroke-linecap="round">
    <animate attributeName="stroke-dashoffset" from="0" to="-610" dur="20s" repeatCount="indefinite"/>
  </rect>

  <g font-family="'Segoe UI',Arial,sans-serif" text-anchor="middle">
    <text x="600" y="27" class="micro" fill="{theme["micro"]}">GITHUB // LIVE METRICS</text>
  </g>

  <g fill="none" stroke="url(#flow)" stroke-linecap="round" filter="url(#glow)">
    <path d="M105 42H1095" stroke-width="2" stroke-opacity="0.72"/>
  </g>

  <g font-family="'Segoe UI',Arial,sans-serif" text-anchor="middle">
    <g transform="translate(72 50)">
      <rect width="246" height="96" rx="17" fill="{theme["card"]}" fill-opacity="0.86" stroke="#22d3ee" stroke-opacity="0.52"/>
      <circle cx="123" cy="18" r="4" fill="#22d3ee" filter="url(#glow)"><animate attributeName="opacity" values="0.45;1;0.45" dur="3.2s" repeatCount="indefinite"/></circle>
      <text x="123" y="57" class="value" fill="{theme["value"]}">{public_repos}</text>
      <text x="123" y="82" class="label" fill="{theme["cyan"]}">PUBLIC REPOS</text>
    </g>

    <g transform="translate(342 50)">
      <rect width="246" height="96" rx="17" fill="{theme["card"]}" fill-opacity="0.86" stroke="#60a5fa" stroke-opacity="0.52"/>
      <path d="M123 7l2.4 4.9 5.4.8-3.9 3.8.9 5.4-4.8-2.6-4.8 2.6.9-5.4-3.9-3.8 5.4-.8z" fill="{theme["blue"]}" opacity="0.9"/>
      <text x="123" y="57" class="value" fill="{theme["value"]}">{stars}</text>
      <text x="123" y="82" class="label" fill="{theme["blue"]}">STARS EARNED</text>
    </g>

    <g transform="translate(612 50)">
      <rect width="246" height="96" rx="17" fill="{theme["card"]}" fill-opacity="0.86" stroke="#8b5cf6" stroke-opacity="0.56"/>
      <circle cx="123" cy="12" r="5" fill="none" stroke="{theme["violet"]}" stroke-width="2"/>
      <path d="M114 27c2.5-5.5 15.5-5.5 18 0" fill="none" stroke="{theme["violet"]}" stroke-width="2" stroke-linecap="round"/>
      <text x="123" y="57" class="value" fill="{theme["value"]}">{followers}</text>
      <text x="123" y="82" class="label" fill="{theme["violet"]}">FOLLOWERS</text>
    </g>

    <g transform="translate(882 50)">
      <rect width="246" height="96" rx="17" fill="{theme["card"]}" fill-opacity="0.86" stroke="#22d3ee" stroke-opacity="0.52"/>
      <path d="M113 18h20M123 8v20" stroke="{theme["cyan"]}" stroke-width="2.2" stroke-linecap="round" filter="url(#glow)"/>
      <text x="123" y="57" class="value" fill="{theme["value"]}">{contributions}</text>
      <text x="123" y="82" class="label" fill="{theme["cyan"]}">CONTRIBUTIONS {year}</text>
    </g>
  </g>

  <g font-family="'Segoe UI',Arial,sans-serif" text-anchor="middle">
    <text x="600" y="171" class="meta" fill="{theme["meta"]}">AUTO-SYNC · GITHUB ACTIONS</text>
  </g>
</svg>
'''


def update_readme_cache_keys(cache_key: str) -> list[Path]:
    # Matches both cards on any path (assets/image/... today) so a file move no
    # longer silently disables cache busting.
    pattern = re.compile(r"(github-stats(?:-light)?\.svg\?v=)[^\"') >]+")
    updated: list[Path] = []
    for readme_path in README_PATHS:
        readme = readme_path.read_text(encoding="utf-8")
        new_readme, hits = pattern.subn(rf"\g<1>{cache_key}", readme)
        if hits and new_readme != readme:
            readme_path.write_text(new_readme, encoding="utf-8")
            updated.append(readme_path)
    return updated


def main() -> None:
    now = dt.datetime.now(LOCAL_TZ)
    year = now.year

    user = get_user()
    repos = get_public_repositories()

    public_repos = int(user["public_repos"])
    followers = int(user["followers"])
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos if not repo.get("fork", False))
    contributions = get_year_contributions(year)

    for path, theme in ((SVG_PATH, DARK_THEME), (SVG_LIGHT_PATH, LIGHT_THEME)):
        path.write_text(
            render_svg(
                public_repos=public_repos,
                stars=stars,
                followers=followers,
                contributions=contributions,
                year=year,
                theme=theme,
            ),
            encoding="utf-8",
        )

    contributions_key = PLACEHOLDER_CACHE_KEY if contributions == PLACEHOLDER else contributions
    cache_key = f"{public_repos}-{stars}-{followers}-{contributions_key}-{year}"
    updated = update_readme_cache_keys(cache_key)

    print(
        f"Updated stats: repos={public_repos}, stars={stars}, "
        f"followers={followers}, contributions={contributions}, year={year}"
    )
    print(f"Cache key {cache_key} applied to: {', '.join(p.name for p in updated) or 'no README'}")


if __name__ == "__main__":
    main()
