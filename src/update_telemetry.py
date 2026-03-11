import base64
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


def get_json(url: str, headers: dict[str, str] | None = None):
    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")


def generate_svg(data: dict, total: str, daily_avg: str, repo_stats: dict) -> str:
    """Generates a Cyberpunk-themed SVG dashboard."""

    # Colors
    bg_color = "#0D1117"  # GitHub Dark Dimmed
    border_color = "#30363D"
    text_color = "#C9D1D9"
    accent_cyan = "#00EBC0"
    accent_magenta = "#FF4FD8"
    accent_blue = "#7C8CFF"
    bar_bg = "#21262D"

    # Font Styles (Inlined for better compatibility)
    font_family = "'Consolas', 'Courier New', monospace"
    s_text = f"font-family: {font_family}; font-size: 14px; fill: {text_color};"
    s_header = f"font-family: {font_family}; font-size: 16px; font-weight: bold; fill: {accent_cyan};"
    s_label = f"font-family: {font_family}; font-size: 14px; font-weight: bold; fill: {accent_magenta};"
    s_value = f"font-family: {font_family}; font-size: 14px; font-weight: bold; fill: {accent_blue};"
    s_dim = f"font-family: {font_family}; font-size: 14px; fill: #8B949E;"

    # SVG Header with XML declaration
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="340" viewBox="0 0 800 340" fill="none" xmlns="http://www.w3.org/2000/svg">

    <!-- Background Terminal Window -->
    <rect x="0" y="0" width="800" height="340" rx="10" fill="{bg_color}" stroke="{border_color}" stroke-width="2"/>

    <!-- Window Controls -->
    <circle cx="25" cy="20" r="6" fill="#FF5F56"/>
    <circle cx="45" cy="20" r="6" fill="#FFBD2E"/>
    <circle cx="65" cy="20" r="6" fill="#27C93F"/>

    <!-- Header Title -->
    <text x="320" y="25" style="{s_header}">NEON TELEMETRY // ONLINE</text>

    <!-- Divider -->
    <line x1="0" y1="45" x2="800" y2="45" stroke="{border_color}" stroke-width="2"/>

    <!-- Stats Header -->
    <text x="40" y="80" style="{s_label}">UPTIME (7d):</text>
    <text x="150" y="80" style="{s_value}">{escape_xml(total)}</text>

    <text x="450" y="80" style="{s_label}">DAILY FLUX:</text>
    <text x="560" y="80" style="{s_value}">{escape_xml(daily_avg)}</text>
    '''

    # Language Bars
    y_pos = 120
    for lang in (data.get("languages") or [])[:5]:
        name = lang.get("name", "Unknown")
        text = lang.get("text", "0 mins")
        pct = float(lang.get("percent", 0.0))

        # Calculate bar width (max 300px)
        bar_width = int((pct / 100) * 300)

        svg += f'''
    <!-- {name} Row -->
    <text x="40" y="{y_pos + 12}" style="{s_text}">{escape_xml(name)}</text>

    <!-- Progress Bar Background -->
    <rect x="180" y="{y_pos}" width="300" height="16" rx="4" fill="{bar_bg}"/>
    <!-- Progress Bar Fill -->
    <rect x="180" y="{y_pos}" width="{bar_width}" height="16" rx="4" fill="{accent_cyan}">
        <animate attributeName="width" from="0" to="{bar_width}" dur="1s" fill="freeze" />
    </rect>

    <text x="500" y="{y_pos + 12}" style="{s_text}">{pct:.1f}%</text>
    <text x="600" y="{y_pos + 12}" style="{s_dim}">{escape_xml(text)}</text>
    '''
        y_pos += 35

    # Bottom Divider
    svg += f'''
    <line x1="40" y1="{y_pos + 10}" x2="760" y2="{y_pos + 10}" stroke="{border_color}" stroke-width="1"/>
    '''

    # Repo Stats Footer
    y_footer = y_pos + 35

    repo_count = repo_stats.get('public_repos', 0)
    stars = repo_stats.get('stars', 0)
    forks = repo_stats.get('forks', 0)
    followers = repo_stats.get('followers', 0)

    svg += f'''
    <text x="80" y="{y_footer}" style="{s_label}">REPOS:</text>
    <text x="140" y="{y_footer}" style="{s_value}">{repo_count}</text>

    <text x="240" y="{y_footer}" style="{s_label}">STARS:</text>
    <text x="300" y="{y_footer}" style="{s_value}">{stars}</text>

    <text x="400" y="{y_footer}" style="{s_label}">FORKS:</text>
    <text x="460" y="{y_footer}" style="{s_value}">{forks}</text>

    <text x="560" y="{y_footer}" style="{s_label}">FOLLOWERS:</text>
    <text x="650" y="{y_footer}" style="{s_value}">{followers}</text>
    '''

    svg += '</svg>'
    return svg


def generate_profile_svg() -> str:
    """Generates the static Profile/Bio SVG."""

    # Colors
    bg_color = "#0D1117"
    border_color = "#30363D"
    text_color = "#C9D1D9"
    dim_text = "#8B949E"
    accent_cyan = "#00EBC0"
    accent_magenta = "#FF4FD8"
    accent_blue = "#7C8CFF"
    tag_bg = "#21262D"

    # Font Styles
    font_family = "'Consolas', 'Courier New', monospace"
    s_text = f"font-family: {font_family}; font-size: 14px; fill: {text_color};"
    s_header = f"font-family: {font_family}; font-size: 16px; font-weight: bold; fill: {accent_cyan};"
    s_subheader = f"font-family: {font_family}; font-size: 14px; font-weight: bold; fill: {accent_magenta};"
    s_tag = f"font-family: {font_family}; font-size: 12px; fill: {accent_cyan};"
    s_tag_blue = f"font-family: {font_family}; font-size: 12px; fill: {accent_blue};"
    s_tag_magenta = f"font-family: {font_family}; font-size: 12px; fill: {accent_magenta};"
    s_dim = f"font-family: {font_family}; font-size: 14px; fill: {dim_text};"
    s_dim_small = f"font-family: {font_family}; font-size: 10px; fill: {dim_text};"

    # SVG Header with XML declaration
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="400" viewBox="0 0 800 400" fill="none" xmlns="http://www.w3.org/2000/svg">

    <!-- Background Terminal Window -->
    <rect x="0" y="0" width="800" height="400" rx="10" fill="{bg_color}" stroke="{border_color}" stroke-width="2"/>

    <!-- Window Controls -->
    <circle cx="25" cy="20" r="6" fill="#FF5F56"/>
    <circle cx="45" cy="20" r="6" fill="#FFBD2E"/>
    <circle cx="65" cy="20" r="6" fill="#27C93F"/>

    <!-- Header Title -->
    <text x="320" y="25" style="{s_header}">NEON PROFILE // IDENTITY</text>

    <!-- Divider -->
    <line x1="0" y1="45" x2="800" y2="45" stroke="{border_color}" stroke-width="2"/>

    <!-- Left Column: Bio & Focus -->
    <text x="40" y="80" style="{s_subheader}">>> IDENTITY_MATRIX</text>
    <text x="40" y="110" style="{s_text}">Role: Compiler Engineer | VM Builder</text>
    <text x="40" y="135" style="{s_dim}">"Turning low-level complexity into systems</text>
    <text x="40" y="155" style="{s_dim}"> that feel fast, clear, and elegant."</text>

    <text x="40" y="200" style="{s_subheader}">>> CURRENT_FOCUS</text>
    <rect x="40" y="215" width="160" height="24" rx="4" fill="{tag_bg}" stroke="{accent_magenta}" stroke-width="1"/>
    <text x="50" y="231" style="{s_tag_magenta}">VM Infra + Tooling</text>

    <text x="40" y="270" style="{s_subheader}">>> DOMAINS</text>
    <rect x="40" y="285" width="130" height="24" rx="4" fill="{tag_bg}"/>
    <text x="50" y="301" style="{s_tag}">Language Design</text>

    <rect x="180" y="285" width="160" height="24" rx="4" fill="{tag_bg}"/>
    <text x="190" y="301" style="{s_tag}">Compiler Engineering</text>

    <rect x="350" y="285" width="100" height="24" rx="4" fill="{tag_bg}"/>
    <text x="360" y="301" style="{s_tag}">WebAssembly</text>

    <!-- Vertical Divider -->
    <line x1="480" y1="60" x2="480" y2="380" stroke="{border_color}" stroke-width="1"/>

    <!-- Right Column: Tech Stack -->
    <text x="520" y="80" style="{s_subheader}">>> TECH_STACK</text>

    <!-- Languages -->
    <text x="520" y="110" style="{s_dim}">Languages:</text>
    <rect x="520" y="125" width="60" height="24" rx="4" fill="{tag_bg}" stroke="{accent_blue}" stroke-width="1"/>
    <text x="535" y="141" style="{s_tag_blue}">C++</text>

    <rect x="590" y="125" width="40" height="24" rx="4" fill="{tag_bg}" stroke="{accent_blue}" stroke-width="1"/>
    <text x="605" y="141" style="{s_tag_blue}">C</text>

    <rect x="640" y="125" width="100" height="24" rx="4" fill="{tag_bg}" stroke="{accent_blue}" stroke-width="1"/>
    <text x="650" y="141" style="{s_tag_blue}">TypeScript</text>

    <!-- Runtime -->
    <text x="520" y="180" style="{s_dim}">Runtime &amp; Build:</text>
    <rect x="520" y="195" width="100" height="24" rx="4" fill="{tag_bg}"/>
    <text x="530" y="211" style="{s_tag}">WebAssembly</text>

    <rect x="630" y="195" width="60" height="24" rx="4" fill="{tag_bg}"/>
    <text x="640" y="211" style="{s_tag}">CMake</text>

    <rect x="700" y="195" width="60" height="24" rx="4" fill="{tag_bg}"/>
    <text x="710" y="211" style="{s_tag}">LLVM</text>

    <!-- Infra -->
    <text x="520" y="250" style="{s_dim}">Infrastructure:</text>
    <rect x="520" y="265" width="60" height="24" rx="4" fill="{tag_bg}"/>
    <text x="530" y="281" style="{s_tag}">Linux</text>

    <rect x="590" y="265" width="70" height="24" rx="4" fill="{tag_bg}"/>
    <text x="600" y="281" style="{s_tag}">Docker</text>

    <rect x="670" y="265" width="50" height="24" rx="4" fill="{tag_bg}"/>
    <text x="680" y="281" style="{s_tag}">GCP</text>

    <!-- Footer decoration -->
    <text x="520" y="360" style="{s_dim_small}">SYSTEM_ID: ZZZODE-VM-01</text>
    <text x="680" y="360" style="{s_dim_small}">STATUS: OPERATIONAL</text>
    '''

    svg += '</svg>'
    return svg


def main():
    waka_key = os.getenv("WAKATIME_API_KEY", "").strip()
    gh_token = os.getenv("GH_TOKEN", "").strip()
    owner = os.getenv("REPO_OWNER", "").strip()

    # Ensure assets directory exists
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)

    # 1. Fetch WakaTime Data
    waka_data = {}
    total = "N/A"
    daily_avg = "N/A"

    if waka_key:
        auth = base64.b64encode(f"{waka_key}:".encode("utf-8")).decode("utf-8")
        try:
            waka = get_json(
                "https://wakatime.com/api/v1/users/current/stats/last_7_days",
                headers={"Authorization": f"Basic {auth}"},
            )
            waka_data = waka.get("data", {})
            total = waka_data.get("human_readable_total_including_other_language") or waka_data.get("human_readable_total") or "N/A"
            daily_avg = waka_data.get("human_readable_daily_average_including_other_language") or waka_data.get("human_readable_daily_average") or "N/A"
        except HTTPError as e:
            print(f"Error fetching WakaTime: {e}")

    # 2. Fetch GitHub Data
    repo_stats = {'public_repos': 0, 'stars': 0, 'forks': 0, 'followers': 0}
    if owner:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if gh_token:
            headers["Authorization"] = f"Bearer {gh_token}"
        try:
            user = get_json(f"https://api.github.com/users/{owner}", headers=headers)
            repo_stats['public_repos'] = user.get('public_repos', 0)
            repo_stats['followers'] = user.get('followers', 0)

            repos = []
            page = 1
            while True:
                query = urlencode({"per_page": 100, "type": "owner", "page": page})
                batch = get_json(f"https://api.github.com/users/{owner}/repos?{query}", headers=headers)
                if not batch: break
                repos.extend(batch)
                if len(batch) < 100: break
                page += 1

            repo_stats['stars'] = sum(r.get("stargazers_count", 0) for r in repos)
            repo_stats['forks'] = sum(r.get("forks_count", 0) for r in repos)
        except HTTPError as e:
            print(f"Error fetching GitHub: {e}")

    # 3. Generate SVG
    # If API calls failed (e.g. locally without secrets), use fallback/mock data for preview
    if total == "N/A" and repo_stats['public_repos'] == 0:
        print("⚠️ No API data found (missing secrets?). Using fallback data for preview.")
        total = "28 hrs 44 mins"
        daily_avg = "4 hrs 6 mins"
        waka_data = {
            "languages": [
                {"name": "C++", "text": "9h 6m", "percent": 31.7},
                {"name": "Markdown", "text": "4h 28m", "percent": 15.6},
                {"name": "JSON", "text": "3h 49m", "percent": 13.3},
                {"name": "TrafficScript", "text": "2h 9m", "percent": 7.5},
                {"name": "CMake", "text": "1h 45m", "percent": 6.1},
            ]
        }
        repo_stats = {'public_repos': 62, 'stars': 10, 'forks': 5, 'followers': 10}

    svg_content = generate_svg(waka_data, total, daily_avg, repo_stats)

    # 4. Write SVG to file
    (assets_dir / "telemetry.svg").write_text(svg_content, encoding="utf-8")
    print("Generated assets/telemetry.svg")

    # 5. Generate Profile SVG
    profile_svg = generate_profile_svg()
    (assets_dir / "profile.svg").write_text(profile_svg, encoding="utf-8")
    print("Generated assets/profile.svg")


if __name__ == "__main__":
    main()
