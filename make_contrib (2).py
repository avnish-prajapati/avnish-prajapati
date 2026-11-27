"""
Makes contributions.svg  (terminal-style heatmap card, animated, blue theme)
Reads PUBLIC data from  https://github.com/users/<USER>/contributions  (no token needed).

Run:     python make_contrib.py avnish-prajapati
Preview: python make_contrib.py --demo        (fake random data, only to see the design)
Needs:   Python 3 only (no pip install).
"""
import re, sys, os, json, random, datetime as dt
from html import escape
from urllib.request import Request, urlopen

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
LEVELS = ["#161b22", "#0c2d6b", "#1158c7", "#388bfd", "#79c0ff"]   # less -> more (blue, same as the info card)
BG, BORDER, DIM, TEXT, ACCENT, PURPLE = "#0d1117", "#30363d", "#8b949e", "#e6edf3", "#58a6ff", "#d2a8ff"


# ---------------------------------------------------------------- 1) get data
def fetch_days(user):
    url = f"https://github.com/users/{user}/contributions"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    return parse_days(html)


def parse_days(html):
    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*?for="([^"]+)"[^>]*>(.*?)</tool-tip>', html, re.S):
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        n = re.match(r"(\d+)\s+contribution", text)
        tips[m.group(1)] = int(n.group(1)) if n else 0
    days = []
    for tag in re.findall(r"<td\b[^>]*ContributionCalendar-day[^>]*>", html):
        d = re.search(r'data-date="([\d-]+)"', tag)
        lv = re.search(r'data-level="(\d)"', tag)
        i = re.search(r'\bid="([^"]+)"', tag)
        if not d:
            continue
        level = int(lv.group(1)) if lv else 0
        count = tips.get(i.group(1), level) if i else level   # fallback: level (approx)
        days.append((dt.date.fromisoformat(d.group(1)), count, level))
    days.sort()
    return days


def demo_days():
    random.seed(7)
    end = dt.date.today()
    out = []
    for k in range(371):
        d = end - dt.timedelta(days=370 - k)
        c = random.choice([0, 0, 0, 1, 2, 3, 5, 8, 12]) if random.random() < 0.55 else 0
        out.append((d, c, 0 if c == 0 else 1 if c < 3 else 2 if c < 6 else 3 if c < 10 else 4))
    return out


# ---------------------------------------------------------------- 2) stats
def stats(days):
    total = sum(c for _, c, _ in days)
    active = sum(1 for _, c, _ in days if c > 0)
    best = max(days, key=lambda x: x[1])
    longest = run = 0
    for _, c, _ in days:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    cur = 0
    seq = list(days)
    if seq and seq[-1][1] == 0:       # today may not be finished yet -> start from yesterday
        seq = seq[:-1]
    for _, c, _ in reversed(seq):
        if c > 0: cur += 1
        else: break
    return total, active, best, cur, longest


# ---------------------------------------------------------------- 3) draw
def build(days, user, out="contributions.svg"):
    CELL, PITCH = 11, 14
    GX, GY = 64, 76
    # put days into week columns (week starts Sunday, like GitHub)
    first = days[0][0]
    lead = (first.weekday() + 1) % 7            # Mon=0 -> Sun=0 index
    cells = [None] * lead + list(days)
    cols = [cells[i:i + 7] for i in range(0, len(cells), 7)]
    W = GX + len(cols) * PITCH + 24
    H = 300
    total, active, best, cur, longest = stats(days)
    asof = days[-1][0].isoformat()

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<title>{escape(user)} public activity</title>'
        '<style>@keyframes rise{0%{opacity:0}100%{opacity:1}}'
        '.c{opacity:0;animation:rise .4s ease-out both}'
        '@media (prefers-reduced-motion:reduce){.c{animation:none!important;opacity:1!important}}</style>'
        f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="{BG}" stroke="{BORDER}"/>'
        f'<path d="M0 36.5H{W}" stroke="{BORDER}"/>'
        f'<rect x="22" y="14" width="7" height="7" rx="2" fill="{ACCENT}"/>'
        f'<text x="40" y="22" fill="{DIM}" font-family="{MONO}" font-size="11">public activity · {len(cols)} weeks</text>'
        f'<text x="{W-24}" y="22" fill="{DIM}" text-anchor="end" font-family="{MONO}" font-size="11">as of {asof}</text>'
    ]
    # weekday labels
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        p.append(f'<text x="24" y="{GY + row*PITCH + 9}" fill="{DIM}" font-family="{MONO}" font-size="10">{name}</text>')
    # month labels
    last_m, last_x = None, -99
    for ci, col in enumerate(cols):
        d = next((c[0] for c in col if c), None)
        if d and d.month != last_m:
            if ci - last_x >= 3:
                p.append(f'<text x="{GX + ci*PITCH}" y="{GY - 10}" fill="{DIM}" font-family="{MONO}" font-size="10">{d.strftime("%b")}</text>')
                last_x = ci
            last_m = d.month
    # cells (one animated group per week column, starts after the face card has finished drawing)
    START = 3.6
    for ci, col in enumerate(cols):
        p.append(f'<g class="c" style="animation-delay:{START + ci * 0.025:.3f}s">')
        for ri, c in enumerate(col):
            if not c:
                continue
            d, count, level = c
            tip = f'{count} contribution{"s" if count != 1 else ""} on {d.isoformat()}'
            p.append(f'<rect x="{GX + ci*PITCH}" y="{GY + ri*PITCH}" '
                     f'width="{CELL}" height="{CELL}" rx="3" fill="{LEVELS[level]}"><title>{tip}</title></rect>')
        p.append('</g>')
    # legend
    ly = GY + 7 * PITCH + 14
    lx = W - 24
    p.append(f'<text x="{lx}" y="{ly+9}" fill="{DIM}" text-anchor="end" font-family="{MONO}" font-size="10">more</text>')
    x = lx - 34
    for lv in reversed(range(5)):
        x -= 15
        p.append(f'<rect x="{x}" y="{ly}" width="{CELL}" height="{CELL}" rx="3" fill="{LEVELS[lv]}"/>')
    p.append(f'<text x="{x-8}" y="{ly+9}" fill="{DIM}" text-anchor="end" font-family="{MONO}" font-size="10">less</text>')
    # footer stats
    fy = ly + 28
    p.append(f'<path d="M24 {fy-10}.5H{W-24}" stroke="{BORDER}"/>')
    p.append(f'<text x="24" y="{fy+16}" fill="{DIM}" font-family="{MONO}" font-size="13">'
             f'<tspan fill="{ACCENT}" font-weight="700">{total:,}</tspan> contributions · {active} active days</text>')
    p.append(f'<text x="{W-24}" y="{fy+16}" fill="{DIM}" text-anchor="end" font-family="{MONO}" font-size="13">'
             f'best <tspan fill="{TEXT}" font-weight="700">{best[1]}</tspan> · {best[0].isoformat()}</text>')
    p.append(f'<text x="24" y="{fy+40}" fill="{DIM}" font-family="{MONO}" font-size="13">'
             f'current streak <tspan fill="{PURPLE}">{cur}d</tspan> · longest <tspan fill="{PURPLE}">{longest}d</tspan></text>')
    p.append(f'<text x="{W-24}" y="{fy+40}" fill="{DIM}" text-anchor="end" font-family="{MONO}" font-size="11">generated by Python · public data</text>')
    p.append('</svg>')
    open(out, "w", encoding="utf-8").write("".join(p))
    print("saved", out, f"({total} contributions, {active} active days)")


# ---------------------------------------------------------------- 4) stats card (repos, stars, top languages)
STATS_THEMES = {   # the stats card switches light / dark by itself (one file)
    "light": dict(bg="#ffffff", line="#d9d0c5", text="#3d2e24", dim="#7d6e62", label="#b7791f", head="#d1613d",
                  track="#f0e8de", bars=["#b7791f", "#d1613d", "#a83f3f", "#5f7d2f", "#b0507a", "#8b5e3c"]),
    "dark":  dict(bg="#0d1117", line="#30363d", text="#f1e6d8", dim="#a8978a", label="#e8b04a", head="#f2a98c",
                  track="#21262d", bars=["#e8b04a", "#f2a98c", "#e07a5f", "#a9c27a", "#d98fa0", "#c9b8a6"]),
}


def stats_css():
    def block(t):
        css = (f'.bg{{fill:{t["bg"]};stroke:{t["line"]}}}.ln{{stroke:{t["line"]};fill:none}}.tx{{fill:{t["text"]}}}'
               f'.dm{{fill:{t["dim"]}}}.lb{{fill:{t["label"]}}}.hd{{fill:{t["head"]}}}.tr{{fill:{t["track"]}}}')
        return css + ''.join(f'.b{i}{{fill:{col}}}' for i, col in enumerate(t["bars"]))
    return f'<style>{block(STATS_THEMES["light"])}@media (prefers-color-scheme:dark){{{block(STATS_THEMES["dark"])}}}</style>'


def api(path):
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN")          # the GitHub robot gives this automatically
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return json.loads(urlopen(Request("https://api.github.com" + path, headers=h), timeout=30).read().decode())


def fetch_repo_stats(user):
    u = api(f"/users/{user}")
    repos = api(f"/users/{user}/repos?per_page=100&type=owner&sort=pushed")
    langs, stars = {}, 0
    for r in repos:
        stars += r.get("stargazers_count", 0)
        if r.get("fork"):
            continue
        try:
            for k, v in api(f"/repos/{user}/{r['name']}/languages").items():
                langs[k] = langs.get(k, 0) + v
        except Exception:
            pass
    return {"repos": u.get("public_repos", len(repos)), "stars": stars, "langs": langs}


def demo_repo_stats():
    return {"repos": 14, "stars": 6, "langs": {"JavaScript": 61000, "TypeScript": 22000, "CSS": 14000,
                                              "HTML": 9000, "Python": 7000, "C++": 3000}}


def build_stats(info, days, user, out="stats.svg"):
    W, H = 830, 300
    total, active, best, cur, longest = stats(days)
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<title>{escape(user)} github stats</title>' + stats_css() +
        f'<rect class="bg" x=".5" y=".5" width="{W-1}" height="{H-1}" rx="6"/>'
        f'<path class="ln" d="M0 36.5H{W}"/>'
        '<rect class="lb" x="22" y="14" width="7" height="7" rx="2"/>'
        f'<text class="dm" x="40" y="22" font-family="{MONO}" font-size="11">github stats · public data</text>'
        f'<text class="dm" x="{W-24}" y="22" text-anchor="end" font-family="{MONO}" font-size="11">as of {days[-1][0].isoformat()}</text>'
    ]
    rows = [("repos", f'{info["repos"]}'), ("stars", f'{info["stars"]}'), ("contributions", f"{total:,}"),
            ("active days", f"{active}"), ("longest streak", f"{longest}d")]
    for i, (label, val) in enumerate(rows):
        y = 84 + i * 32
        p.append(f'<text class="lb" x="24" y="{y}" font-family="{MONO}" font-size="11">{label}</text>')
        p.append(f'<text class="tx" x="150" y="{y}" font-family="{MONO}" font-size="15" font-weight="700">{val}</text>')
    p.append('<path class="ln" d="M300.5 56V236"/>')
    langs = sorted(info["langs"].items(), key=lambda kv: -kv[1])[:6]
    tot = sum(v for _, v in info["langs"].items()) or 1
    p.append(f'<text class="hd" x="330" y="62" font-family="{MONO}" font-size="11" font-weight="700">top languages</text>')
    if not langs:
        p.append(f'<text class="dm" x="330" y="96" font-family="{MONO}" font-size="12">no public code yet</text>')
    for i, (name, v) in enumerate(langs):
        y = 92 + i * 27
        pct = v * 100 / tot
        p.append(f'<text class="tx" x="330" y="{y}" font-family="{MONO}" font-size="12">{escape(name)}</text>')
        p.append(f'<rect class="tr" x="450" y="{y-9}" width="270" height="9" rx="4.5"/>')
        p.append(f'<rect class="b{i}" x="450" y="{y-9}" width="{max(4, 270*pct/100):.1f}" height="9" rx="4.5"/>')
        p.append(f'<text class="dm" x="{W-24}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="12">{pct:.1f}%</text>')
    p.append(f'<path class="ln" d="M24 256.5H{W-24}"/>')
    p.append(f'<text class="dm" x="24" y="280" font-family="{MONO}" font-size="10">languages counted from public, non-fork repos</text>')
    p.append(f'<text class="dm" x="{W-24}" y="280" text-anchor="end" font-family="{MONO}" font-size="10">generated by Python · public data</text></svg>')
    open(out, "w", encoding="utf-8").write("".join(p))
    print("saved", out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--demo" in sys.argv:
        d = demo_days()
        build(d, "demo-user", "contributions-demo.svg")
        build_stats(demo_repo_stats(), d, "demo-user", "stats-demo.svg")
    elif args:
        d = fetch_days(args[0])
        build(d, args[0])
        try:
            build_stats(fetch_repo_stats(args[0]), d, args[0])
        except Exception as e:                       # the heatmap still works if this part fails
            print("stats card skipped:", e)
    else:
        print("Usage: python make_contrib.py avnish-prajapati")
