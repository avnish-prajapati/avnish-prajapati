"""
Makes contributions.svg  (terminal-style heatmap card, animated, blue theme)
Reads PUBLIC data from  https://github.com/users/<USER>/contributions  (no token needed).

Run:     python make_contrib.py avnish-prajapati
Preview: python make_contrib.py --demo        (fake random data, only to see the design)
Needs:   Python 3 only (no pip install).
"""
import re, sys, random, datetime as dt
from html import escape
from urllib.request import Request, urlopen

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
LEVELS = ["#161b22", "#0c2d6b", "#1158c7", "#388bfd", "#79c0ff"]   # less -> more (blue theme)
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
        '<style>@keyframes pop{0%{opacity:0;transform:scale(.4)}100%{opacity:1;transform:scale(1)}}'
        '.c{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .35s ease-out both}'
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
    # cells
    for ci, col in enumerate(cols):
        for ri, c in enumerate(col):
            if not c:
                continue
            d, count, level = c
            delay = ci * 0.012
            tip = f'{count} contribution{"s" if count != 1 else ""} on {d.isoformat()}'
            p.append(f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{GX + ci*PITCH}" y="{GY + ri*PITCH}" '
                     f'width="{CELL}" height="{CELL}" rx="3" fill="{LEVELS[level]}"><title>{tip}</title></rect>')
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


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--demo" in sys.argv:
        build(demo_days(), "demo-user", "contributions-demo.svg")
    elif args:
        build(fetch_days(args[0]), args[0])
    else:
        print("Usage: python make_contrib.py avnish-prajapati")
