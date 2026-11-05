#!/usr/bin/env python3
"""
Builds assets/field-record.svg from your PUBLIC GitHub repos (repo count, stars, top languages).
Runs daily through .github/workflows/field-record.yml. To run it by hand:
    GH_USER=abduhoo-bin-nasir python scripts/field_record.py
If GitHub can't be reached, the existing SVG is left untouched.
"""
import datetime, json, os, sys, urllib.request

USER  = os.environ.get('GH_USER', 'abduhoo-bin-nasir')
TOKEN = os.environ.get('GITHUB_TOKEN')
OUT   = os.environ.get('OUT', 'assets/field-record.svg')
SKIP_LANGS = {'Makefile', 'CMake', 'Dockerfile', 'Batchfile', 'Shell'}   # build files, not "languages you write"

BG='#0c0a0a'; GREEN='#8fb89a'; BONE='#d8d0bd'; RED='#d23a32'; DIM='#5f564c'; LINE='#2a2222'; TRACK='#1c1717'
FONT="'Courier New', Courier, 'DejaVu Sans Mono', 'Liberation Mono', monospace"

def api(path):
    h = {'Accept': 'application/vnd.github+json', 'User-Agent': 'field-record', 'X-GitHub-Api-Version': '2022-11-28'}
    if TOKEN: h['Authorization'] = 'Bearer ' + TOKEN
    with urllib.request.urlopen(urllib.request.Request('https://api.github.com' + path, headers=h), timeout=20) as r:
        return json.load(r)

def collect():
    repos = [r for r in api(f'/users/{USER}/repos?per_page=100&type=owner') if not r['fork']]
    langs = {}
    for r in repos:
        for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
            if k not in SKIP_LANGS: langs[k] = langs.get(k, 0) + v
    return {'repos': len(repos), 'stars': sum(r['stargazers_count'] for r in repos), 'langs': langs}

def render(d, stamp):
    total = sum(d['langs'].values()) or 1
    top = sorted(d['langs'].items(), key=lambda kv: -kv[1])[:5]
    rest = total - sum(v for _, v in top)
    if rest > 0: top.append(('Other', rest))
    cols = [RED, GREEN, BONE, '#c9a227', '#6f8f9a', DIM]
    def pct(v):
        p = v * 100 / total
        return '<1%' if 0 < p < 1 else f'{p:.0f}%'
    bx, bw = 640, 520
    bar, legend, x = '', '', bx
    for i, (name, val) in enumerate(top):
        w = max(3, bw * val / total)
        bar += f'<rect x="{x:.1f}" y="92" width="{max(1, w - 2):.1f}" height="24" fill="{cols[i]}"/>'
        x += w
        lx, ly = bx + (i % 2) * 270, 158 + (i // 2) * 28
        legend += (f'<rect x="{lx}" y="{ly - 10}" width="11" height="11" fill="{cols[i]}"/>'
                   f'<text x="{lx + 20}" y="{ly}" font-size="13" fill="{BONE}">{name[:16]}</text>'
                   f'<text x="{lx + 240}" y="{ly}" font-size="13" fill="{GREEN}" text-anchor="end">{pct(val)}</text>')
    def stat(x, num, label, sub):
        return (f'<text x="{x}" y="130" font-size="58" font-weight="bold" fill="{BONE}">{num}</text>'
                f'<text x="{x}" y="158" font-size="12" fill="{GREEN}" letter-spacing="3" font-weight="bold">{label}</text>'
                f'<text x="{x}" y="178" font-size="10" fill="{DIM}" letter-spacing="2">{sub}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="250" viewBox="0 0 1200 250" role="img" aria-label="GitHub record: {d['repos']} public repositories, {d['stars']} stars, {len(d['langs'])} languages.">
<style>text{{font-family:{FONT};}}.b{{animation:bl 1.1s steps(1) infinite}}@keyframes bl{{0%,60%{{opacity:1}}61%,100%{{opacity:0}}}}@media (prefers-reduced-motion:reduce){{.b{{animation:none}}}}</style>
<rect x=".5" y=".5" width="1199" height="249" rx="8" fill="#141010" stroke="{LINE}"/>
<path d="M1 6a5 5 0 0 1 5-5h2v247h-2a5 5 0 0 1-5-5z" fill="{GREEN}"/>
<text x="40" y="44" font-size="11" fill="{DIM}" letter-spacing="4">GITHUB RECORD // PUBLIC REPOS ONLY</text>
<circle class="b" cx="1146" cy="40" r="4" fill="{RED}"/><text x="1132" y="44" font-size="11" fill="{GREEN}" letter-spacing="3" text-anchor="end">SYNCED {stamp}</text>
<line x1="40" y1="60" x2="1160" y2="60" stroke="{LINE}"/>
{stat(40, d['repos'], 'PUBLIC REPOS', 'OWNED, NOT FORKED')}{stat(250, d['stars'], 'STARS', 'ACROSS ALL REPOS')}{stat(420, len(d['langs']), 'LANGUAGES', 'EXCLUDING BUILD FILES')}
<line x1="600" y1="80" x2="600" y2="214" stroke="{LINE}"/>
<text x="640" y="82" font-size="11" fill="{RED}" letter-spacing="4" font-weight="bold">TOP LANGUAGES</text>
<rect x="640" y="92" width="520" height="24" fill="{TRACK}"/>{bar}
{legend}
</svg>'''

if __name__ == '__main__':
    try:
        data = collect()
    except Exception as e:
        print('Could not reach GitHub, keeping existing card:', e); sys.exit(0)
    open(OUT, 'w', encoding='utf-8').write(render(data, datetime.date.today().isoformat()))
    print('wrote', OUT, data['repos'], 'repos,', data['stars'], 'stars,', len(data['langs']), 'languages')
