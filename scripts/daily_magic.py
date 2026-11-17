"""Daily magic for the ggekkos profile ✦

Runs once a day (GitHub Actions) and:
  1. picks today's Spell of the Day from spells.json
  2. draws the seasonal banner (southern hemisphere seasons)
  3. draws the contribution flower field
  4. draws stats + project cards, only when there are public repos
and rewrites the matching sections of README.md between the marker comments.

Uses only the Python standard library. Needs GITHUB_TOKEN for steps 3 and 4;
without it (e.g. running locally) those parts are left as they are.
"""
import json
import os
import random
import re
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "assets" / "generated"
README = ROOT / "README.md"
USER = os.environ.get("GH_USER", "ggekkos")
TOKEN = os.environ.get("GITHUB_TOKEN")
TODAY = datetime.now(timezone(timedelta(hours=-3))).date()  # Brazil time

SERIF = "Georgia, 'Times New Roman', serif"
JP = "'Yu Mincho', 'Hiragino Mincho ProN', 'Noto Serif JP', 'MS Mincho', serif"
STAR4 = "M0 -6 Q1 -1 6 0 Q1 1 0 6 Q-1 1 -6 0 Q-1 -1 0 -6 Z"


# ───────────────────────────── helpers ─────────────────────────────

def x(text):
    return escape(str(text), quote=True)


def write(name, svg):
    GEN.mkdir(parents=True, exist_ok=True)
    (GEN / name).write_text(svg, encoding="utf-8")
    return f"assets/generated/{name}"


def flower(rng, px, py, s, color, center="#fff6d8", stem=True, sway=True):
    petals = "".join(
        f'<circle cx="{dx*s:.1f}" cy="{dy*s:.1f}" r="{3.2*s:.1f}" fill="{color}"/>'
        for dx, dy in [(0, -4), (3.8, -1.2), (2.4, 3.2), (-2.4, 3.2), (-3.8, -1.2)])
    anim = ""
    if sway:
        dur, a = rng.uniform(3, 5.5), rng.uniform(2, 5)
        pivot = 14 * s if stem else 0
        anim = (f'<animateTransform attributeName="transform" type="rotate" '
                f'values="{-a:.1f} 0 {pivot:.1f};{a:.1f} 0 {pivot:.1f};{-a:.1f} 0 {pivot:.1f}" '
                f'dur="{dur:.1f}s" begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite"/>')
    stem_svg = (f'<line x1="0" y1="0" x2="0" y2="{14*s:.1f}" stroke="#5f9a7c" stroke-width="{1.2*s:.1f}"/>'
                if stem else "")
    return (f'<g transform="translate({px:.1f} {py:.1f})"><g>{anim}{stem_svg}{petals}'
            f'<circle r="{1.8*s:.1f}" fill="{center}"/></g></g>')


def replace_section(text, key, content):
    pattern = re.compile(rf"(<!-- {key}:START -->)(.*?)(<!-- {key}:END -->)", re.S)
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", text)


# ───────────────────────────── seasons ─────────────────────────────

SEASONS = {
    # southern hemisphere: Sep–Nov spring, Dec–Feb summer, Mar–May autumn, Jun–Aug winter
    "spring": dict(jp="春", sky=["#27306b", "#5d6cb8", "#b9a9e0", "#f7dbe6"],
                   mountains=["#9b98d4", "#8a9fd0"], hills=["#9cc7ae", "#82b597"],
                   flowers=["#7fa2ec", "#93b4f2", "#6b8de0", "#a9c3f7", "#ffffff", "#c9b8f0"], count=110),
    "summer": dict(jp="夏", sky=["#1d2459", "#3f4f9e", "#8e7fc9", "#f2b9c8"],
                   mountains=["#8d86c8", "#7b8fc8"], hills=["#8cc49a", "#6fae82"],
                   flowers=["#ffd66b", "#f6a6c1", "#7fa2ec", "#ffffff", "#ffb37a", "#c9b8f0"], count=120),
    "autumn": dict(jp="秋", sky=["#2d2350", "#7a5a9c", "#e3a07a", "#f6d3a8"],
                   mountains=["#a07fa8", "#b88a9a"], hills=["#d8b17a", "#c79a62"],
                   flowers=["#e8875a", "#d65f5f", "#f2b84b", "#b07fd0", "#f7d9a0"], count=80),
    "winter": dict(jp="冬", sky=["#1c2a52", "#4d6aa8", "#a9c4e6", "#e8f0fa"],
                   mountains=["#b8c6e4", "#c9d5ee"], hills=["#eef3fa", "#dfe8f4"],
                   flowers=["#ffffff", "#dbe7fb", "#c9d8f5"], count=30),
}


def season_of(d):
    return {9: "spring", 10: "spring", 11: "spring", 12: "summer", 1: "summer", 2: "summer",
            3: "autumn", 4: "autumn", 5: "autumn"}.get(d.month, "winter")


def banner(season):
    c = SEASONS[season]
    rng = random.Random(f"banner-{season}")
    sky = c["sky"]
    p = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 340" width="1200" height="340">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{sky[0]}"/><stop offset="0.38" stop-color="{sky[1]}"/>
      <stop offset="0.7" stop-color="{sky[2]}"/><stop offset="1" stop-color="{sky[3]}"/>
    </linearGradient>
    <linearGradient id="page" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fffdf7"/><stop offset="1" stop-color="#f3eedf"/>
    </linearGradient>
    <linearGradient id="shoot" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0"/><stop offset="1" stop-color="#ffffff"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#fff4c4"/><stop offset="1" stop-color="#fff4c4" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="fly" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#f4ffb0"/><stop offset="1" stop-color="#d8ff6b" stop-opacity="0"/>
    </radialGradient>
    <path id="star4" d="{STAR4}"/>
    <path id="leaf" d="M0 -7 C6 -4 6 4 0 7 C-6 4 -6 -4 0 -7 Z"/>
  </defs>
  <rect width="1200" height="340" fill="url(#sky)"/>
  <g fill="#ffffff">''']
    for _ in range(45):
        sx, sy = rng.uniform(0, 1200), rng.uniform(5, 150)
        if 330 < sx < 870 and 50 < sy < 250:
            continue
        d = rng.uniform(2.2, 5)
        p.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{rng.uniform(0.6, 1.6):.1f}"><animate attributeName="opacity" '
                 f'values="0.2;1;0.2" dur="{d:.1f}s" begin="-{rng.uniform(0, d):.1f}s" repeatCount="indefinite"/></circle>')
    p.append("</g>")
    for sx, sy, s, d in [(110, 60, 1.4, 3), (1080, 45, 1.6, 4), (950, 120, 1.0, 3.5), (260, 130, 1.0, 2.8)]:
        p.append(f'<g transform="translate({sx} {sy}) scale({s})"><use href="#star4" fill="#fff8dc">'
                 f'<animate attributeName="opacity" values="0.3;1;0.3" dur="{d}s" repeatCount="indefinite"/></use></g>')
    p.append('''<g opacity="0">
    <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.03;0.1;0.14;1" dur="7s" repeatCount="indefinite"/>
    <g transform="rotate(18)"><rect x="0" y="0" width="140" height="2" rx="1" fill="url(#shoot)">
      <animate attributeName="x" values="100;100;520;520" keyTimes="0;0.02;0.14;1" dur="7s" repeatCount="indefinite"/>
    </rect></g>
  </g>
  <g opacity="0">
    <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.53;0.6;0.64;1" dur="7s" repeatCount="indefinite"/>
    <g transform="translate(700 -40) rotate(22)"><rect x="0" y="0" width="110" height="1.6" rx="1" fill="url(#shoot)">
      <animate attributeName="x" values="0;0;380;380" keyTimes="0;0.52;0.64;1" dur="7s" repeatCount="indefinite"/>
    </rect></g>
  </g>''')
    m, h = c["mountains"], c["hills"]
    p.append(f'''<path d="M0 238 L90 196 L160 220 L250 170 L340 214 L420 192 L520 232 L640 200 L760 230 L860 184 L960 216 L1060 176 L1140 206 L1200 190 L1200 340 L0 340 Z" fill="{m[0]}" opacity="0.55"/>
  <path d="M0 258 L120 226 L230 248 L330 220 L470 252 L600 234 L740 256 L880 222 L1010 250 L1120 228 L1200 244 L1200 340 L0 340 Z" fill="{m[1]}" opacity="0.6"/>
  <path d="M0 282 Q200 252 420 272 T820 268 T1200 262 L1200 340 L0 340 Z" fill="{h[0]}"/>
  <path d="M0 304 Q260 280 560 298 T1200 290 L1200 340 L0 340 Z" fill="{h[1]}"/>''')
    fl = []
    for _ in range(c["count"]):
        fy = rng.uniform(276, 330)
        fl.append((fy, rng.uniform(0, 1200), 0.7 + (fy - 276) / 54 * 0.9))
    for fy, fx, s in sorted(fl):
        p.append(flower(rng, fx, fy, s, rng.choice(c["flowers"]), sway=rng.random() < 0.6))

    p.append(f'''<g>
    <rect x="352" y="58" width="496" height="182" rx="12" fill="#27306b" opacity="0.18" transform="translate(5 7)"/>
    <rect x="352" y="58" width="496" height="182" rx="12" fill="url(#page)"/>
    <rect x="364" y="70" width="472" height="158" rx="8" fill="none" stroke="#c9a961" stroke-width="1.6"/>
    <rect x="371" y="77" width="458" height="144" rx="6" fill="none" stroke="#a9b2e6" stroke-width="1" stroke-dasharray="3 5"/>
    <g fill="#c9a961">
      <use href="#star4" transform="translate(364 70) scale(1.3)"/><use href="#star4" transform="translate(836 70) scale(1.3)"/>
      <use href="#star4" transform="translate(364 228) scale(1.3)"/><use href="#star4" transform="translate(836 228) scale(1.3)"/>
    </g>
    <text x="600" y="106" text-anchor="middle" font-family="{SERIF}" font-size="15" letter-spacing="6" fill="#b08d45">✦ MAGE'S GRIMOIRE ✦</text>
    <text x="600" y="162" text-anchor="middle" font-family="{SERIF}" font-size="56" font-weight="bold" fill="#4f57a6" letter-spacing="2">{x(USER)}</text>
    <text x="600" y="191" text-anchor="middle" font-family="{SERIF}" font-size="15" font-style="italic" fill="#6a6585">collector of useless (but lovely) spells</text>
    <text x="600" y="214" text-anchor="middle" font-family="{JP}" font-size="13" letter-spacing="4" fill="#8c86b8">〜 魔法使いの旅日記 · {c["jp"]} 〜</text>
  </g>''')

    # seasonal particles
    for _ in range(18 if season != "winter" else 45):
        d = rng.uniform(5, 10)
        b = rng.uniform(0, d)
        sx = rng.uniform(10, 1190)
        timing = f'dur="{d:.1f}s" begin="-{b:.1f}s" repeatCount="indefinite"'
        if season == "spring":  # magic sparkles rising from the field
            y0, rise, drift, r = rng.uniform(270, 320), rng.uniform(120, 220), rng.uniform(-25, 25), rng.uniform(1.5, 3)
            p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;0.8;0" {timing}/>'
                     f'<animateTransform attributeName="transform" type="translate" values="{sx:.0f} {y0:.0f};{sx+drift:.0f} {y0-rise:.0f}" {timing}/>'
                     f'<circle r="{r*3:.1f}" fill="url(#glow)" opacity="0.6"/><circle r="{r:.1f}" fill="#fffbe6"/></g>')
        elif season == "summer":  # fireflies wandering over the field
            pts = ";".join(f"{sx+rng.uniform(-40, 40):.0f} {rng.uniform(200, 320):.0f}" for _ in range(4))
            first = pts.split(";")[0]
            p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;0.2;1;0" dur="{rng.uniform(2.5, 4):.1f}s" begin="-{b:.1f}s" repeatCount="indefinite"/>'
                     f'<animateTransform attributeName="transform" type="translate" values="{pts};{first}" {timing}/>'
                     f'<circle r="9" fill="url(#fly)"/><circle r="2" fill="#f7ffd1"/></g>')
        elif season == "autumn":  # falling leaves
            col = rng.choice(["#e8875a", "#d65f5f", "#f2b84b", "#c7743f"])
            p.append(f'<g><animateTransform attributeName="transform" type="translate" values="{sx:.0f} -20;{sx+rng.uniform(40, 120):.0f} 360" {timing}/>'
                     f'<use href="#leaf" fill="{col}"><animateTransform attributeName="transform" type="rotate" values="0;360" dur="{rng.uniform(3, 6):.1f}s" repeatCount="indefinite"/></use></g>')
        else:  # winter snowfall
            r = rng.uniform(1.2, 3.2)
            p.append(f'<g><animateTransform attributeName="transform" type="translate" values="{sx:.0f} -10;{sx+rng.uniform(-30, 30):.0f} 350" {timing}/>'
                     f'<circle r="{r:.1f}" fill="#ffffff" opacity="{rng.uniform(0.6, 1):.2f}"/></g>')
    p.append("</svg>\n")
    return write(f"banner-{season}.svg", "\n".join(p))


# ───────────────────────────── GitHub data ─────────────────────────────

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(first: 100, privacy: PUBLIC, isFork: false, ownerAffiliations: OWNER,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name description url stargazerCount forkCount pushedAt
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}"""


def fetch():
    if not TOKEN:
        return None
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "daily-magic"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]


# ───────────────────────────── flower field ─────────────────────────────

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def garden(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    total = cal["totalContributions"]
    rng = random.Random(f"garden-{USER}")
    cell, row = 21, 22
    x0 = (1200 - len(weeks) * cell) / 2 + cell / 2
    y0 = 92
    p = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 290" width="1200" height="290">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f4f1fb"/><stop offset="1" stop-color="#e5f1ea"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#fff4c4"/><stop offset="1" stop-color="#fff4c4" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x="1" y="1" width="1198" height="288" rx="16" fill="url(#bg)" stroke="#d9d4ef" stroke-width="1.5"/>
  <text x="40" y="46" font-family="{SERIF}" font-size="22" font-weight="bold" fill="#4f57a6">✦ Flower Field <tspan font-family="{JP}" font-size="15" font-weight="normal" fill="#8c86b8">一年の花畑</tspan></text>
  <text x="1160" y="46" text-anchor="end" font-family="{SERIF}" font-size="15" font-style="italic" fill="#6a6585">{total} contribution{"s" if total != 1 else ""} in the last year ✿</text>''']
    last_month = None
    for wi, week in enumerate(weeks):
        days = week["contributionDays"]
        mon = int(days[0]["date"][5:7])
        if mon != last_month and wi < len(weeks) - 2:
            p.append(f'<text x="{x0 + wi*cell - 8:.0f}" y="78" font-family="{SERIF}" font-size="12" fill="#8c86b8">{MONTHS[mon-1]}</text>')
            last_month = mon
        for day in days:
            wd = date.fromisoformat(day["date"]).isoweekday() % 7  # Sunday = 0
            cx, cy = x0 + wi * cell, y0 + wd * row
            lvl = LEVELS.get(day["contributionLevel"], 0)
            if lvl == 0:  # a tiny sprout
                p.append(f'<g transform="translate({cx:.1f} {cy:.1f})" opacity="0.5"><ellipse cx="-2.2" cy="1" rx="3" ry="1.4" fill="#8fbfa3" transform="rotate(-35 -2.2 1)"/>'
                         f'<ellipse cx="2.2" cy="1" rx="3" ry="1.4" fill="#8fbfa3" transform="rotate(35 2.2 1)"/></g>')
            elif lvl == 1:  # a bud
                p.append(f'<g transform="translate({cx:.1f} {cy:.1f})"><line x1="0" y1="1" x2="0" y2="6" stroke="#5f9a7c" stroke-width="1.2"/>'
                         f'<circle r="3" fill="#c9b8f0"/></g>')
            else:
                color = {2: "#a9c3f7", 3: "#7fa2ec", 4: "#5b6fd6"}[lvl]
                s = {2: 0.75, 3: 0.95, 4: 1.15}[lvl]
                if lvl == 4:
                    p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="12" fill="url(#glow)"/>')
                p.append(flower(rng, cx, cy, s, color, stem=False, sway=lvl >= 3))
    ly = y0 + 6 * row + 34
    p.append(f'<text x="40" y="{ly}" font-family="{SERIF}" font-size="13" font-style="italic" fill="#6a6585">'
             + ("every contribution makes a flower bloom ✦" if total else "the seeds are planted · the field blooms as the journey goes on ✦")
             + "</text>")
    lx = 1010
    p.append(f'<text x="{lx - 12}" y="{ly}" text-anchor="end" font-family="{SERIF}" font-size="12" fill="#8c86b8">seed</text>')
    p.append(f'<g transform="translate({lx} {ly - 4})" opacity="0.5"><ellipse cx="-2.2" cy="1" rx="3" ry="1.4" fill="#8fbfa3" transform="rotate(-35 -2.2 1)"/><ellipse cx="2.2" cy="1" rx="3" ry="1.4" fill="#8fbfa3" transform="rotate(35 2.2 1)"/></g>')
    p.append(f'<circle cx="{lx + 24}" cy="{ly - 4}" r="3" fill="#c9b8f0"/>')
    for i, (color, s) in enumerate([("#a9c3f7", 0.75), ("#7fa2ec", 0.95), ("#5b6fd6", 1.15)]):
        p.append(flower(rng, lx + 48 + i * 24, ly - 4, s, color, stem=False, sway=False))
    p.append(f'<text x="{lx + 124}" y="{ly}" font-family="{SERIF}" font-size="12" fill="#8c86b8">bloom</text>')
    p.append("</svg>\n")
    return write(f"garden-{TODAY.isoformat()}.svg", "\n".join(p))


# ───────────────────────────── stats + project cards ─────────────────────────────

def wrap(text, width):
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] = lines[1][: width - 1].rstrip() + "…"
    return lines


def repo_card(repo):
    desc = wrap(repo.get("description") or "a page of the grimoire still waiting for words…", 62)
    lang = repo.get("primaryLanguage") or {}
    p = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 590 140" width="590" height="140">
  <rect x="1" y="1" width="588" height="138" rx="12" fill="#fffdf7" stroke="#c9a961" stroke-width="1.5"/>
  <rect x="8" y="8" width="574" height="124" rx="8" fill="none" stroke="#a9b2e6" stroke-width="1" stroke-dasharray="3 5"/>
  <text x="28" y="44" font-family="{SERIF}" font-size="20" font-weight="bold" fill="#4f57a6">✦ {x(repo["name"])}</text>''']
    for i, line in enumerate(desc):
        p.append(f'<text x="28" y="{74 + i*20}" font-family="{SERIF}" font-size="14" fill="#6a6585">{x(line)}</text>')
    if lang:
        p.append(f'<circle cx="34" cy="117" r="6" fill="{x(lang.get("color") or "#a9b2e6")}"/>'
                 f'<text x="46" y="122" font-family="{SERIF}" font-size="13" fill="#6a6585">{x(lang["name"])}</text>')
    p.append(f'<text x="562" y="122" text-anchor="end" font-family="{SERIF}" font-size="13" fill="#b08d45">★ {repo["stargazerCount"]}</text>')
    p.append("</svg>\n")
    return write(f"repo-{re.sub(r'[^A-Za-z0-9_.-]', '-', repo['name'])}-{TODAY.isoformat()}.svg", "\n".join(p))


def stats_card(user, repos):
    total = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    stars = sum(r["stargazerCount"] for r in repos)
    sizes = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            sizes.setdefault(name, [0, e["node"]["color"] or "#a9b2e6"])
            sizes[name][0] += e["size"]
    langs = sorted(sizes.items(), key=lambda kv: -kv[1][0])[:6]
    whole = sum(v[0] for _, v in langs) or 1
    p = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 170" width="1200" height="170">
  <rect x="1" y="1" width="1198" height="168" rx="16" fill="#fffdf7" stroke="#c9a961" stroke-width="1.5"/>
  <text x="40" y="44" font-family="{SERIF}" font-size="20" font-weight="bold" fill="#4f57a6">✦ Mage's Stats <tspan font-family="{JP}" font-size="14" font-weight="normal" fill="#8c86b8">魔法の記録</tspan></text>''']
    for i, (num, label) in enumerate([(len(repos), "spells written (repos)"), (stars, "stars collected"), (total, "contributions this year")]):
        cx = 40 + i * 190
        p.append(f'<text x="{cx}" y="98" font-family="{SERIF}" font-size="34" font-weight="bold" fill="#5b66c2">{num}</text>'
                 f'<text x="{cx}" y="124" font-family="{SERIF}" font-size="13" fill="#6a6585">{label}</text>')
    if langs:
        bx, bw = 640, 520
        p.append(f'<text x="{bx}" y="72" font-family="{SERIF}" font-size="14" fill="#6a6585">schools of magic (languages)</text>')
        p.append(f'<clipPath id="bar"><rect x="{bx}" y="84" width="{bw}" height="12" rx="6"/></clipPath><g clip-path="url(#bar)">')
        off = bx
        for name, (size, color) in langs:
            w = bw * size / whole
            p.append(f'<rect x="{off:.1f}" y="84" width="{w + 0.5:.1f}" height="12" fill="{x(color)}"/>')
            off += w
        p.append("</g>")
        for i, (name, (size, color)) in enumerate(langs):
            lx, ly = bx + (i % 3) * 175, 124 + (i // 3) * 22
            p.append(f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{x(color)}"/>'
                     f'<text x="{lx + 16}" y="{ly}" font-family="{SERIF}" font-size="13" fill="#6a6585">{x(name)} {100*size/whole:.0f}%</text>')
    p.append("</svg>\n")
    return write(f"stats-{TODAY.isoformat()}.svg", "\n".join(p))


def grimoire(user):
    repos = [r for r in user["repositories"]["nodes"] if r["name"].lower() != USER.lower()]
    if not repos:
        return ""  # no public projects yet: the section stays hidden
    stats = stats_card(user, repos)
    top = sorted(repos, key=lambda r: (r["stargazerCount"], r["pushedAt"]), reverse=True)[:4]
    cells = [f'<a href="{x(r["url"])}"><img src="{repo_card(r)}" width="49%" alt="{x(r["name"])}"/></a>' for r in top]
    return ("<img src=\"assets/divider-frieren.svg\" width=\"100%\" alt=\"\"/>\n\n"
            "## 📚 Grimoire Pages <sub>〜 魔導書のページ</sub>\n\n"
            "<div align=\"center\">\n\n"
            f"<img src=\"{stats}\" width=\"100%\" alt=\"mage's stats\"/>\n\n"
            + "\n".join(cells) + "\n\n</div>\n")


# ───────────────────────────── spell of the day ─────────────────────────────

def spell():
    spells = json.loads((ROOT / "scripts" / "spells.json").read_text(encoding="utf-8"))
    s = spells[TODAY.toordinal() % len(spells)]
    return ("```diff\n"
            f"  ✦ SPELL OF THE DAY · {TODAY.strftime('%b %d, %Y')} ✦\n"
            f"  {s['jp']} · {s['en']}\n\n"
            f"+ effect:              {s['effect']}\n"
            f"+ use in battle:       {s['battle']}\n"
            f"+ use for happiness:   {s['joy']}\n"
            f"- side effects:        {s['side']}\n\n"
            "  cast before starting a new repository ✿\n"
            "```\n"
            "<sub>✦ a new useless spell is found every day · 毎日ひとつ、新しい魔法</sub>")


# ───────────────────────────── main ─────────────────────────────

def main():
    readme = README.read_text(encoding="utf-8")
    keep = set()

    season = season_of(TODAY)
    b = banner(season)
    keep.add(Path(b).name)
    readme = replace_section(readme, "BANNER", f'<img src="{b}" width="100%" alt="{x(USER)} · mage\'s grimoire"/>')
    readme = replace_section(readme, "SPELL", spell())

    user = fetch()
    if user is not None:
        g = garden(user)
        readme = replace_section(readme, "GARDEN", (
            f'<img src="{g}" width="100%" alt="flower field of contributions"/>\n\n'
            '<img src="assets/divider-frieren.svg" width="100%" alt=""/>\n'))
        readme = replace_section(readme, "GRIMOIRE", grimoire(user))
    # keep every generated file the README still points to, drop the rest
    keep |= set(re.findall(r"assets/generated/([^\"')\s]+)", readme))
    for f in GEN.glob("*.svg"):
        if f.name not in keep:
            f.unlink()

    README.write_text(readme, encoding="utf-8", newline="\n")
    print(f"daily magic: {TODAY} | {season} | data: {'yes' if user else 'no (no token)'}")


if __name__ == "__main__":
    main()
