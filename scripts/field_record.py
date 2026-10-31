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
    bars = ''
    for i, (name, val) in enumerate(top):
        y = 76 + i * 26; pct = val * 100 / total
        bars += (f'<text x="500" y="{y}" font-size="13" fill="{BONE}">{name[:14]}</text>'
                 f'<rect x="620" y="{y-11}" width="190" height="12" fill="{TRACK}"/>'
                 f'<rect x="620" y="{y-11}" width="{max(3, pct*1.9):.0f}" height="12" fill="{RED if i == 0 else GREEN}"/>'
                 f'<text x="872" y="{y}" font-size="13" fill="{GREEN}" text-anchor="end">{pct:.0f}%</text>\n')
    def stat(x, num, label):
        return (f'<text x="{x}" y="100" font-size="46" font-weight="bold" fill="{BONE}">{num}</text>'
                f'<text x="{x}" y="126" font-size="12" fill="{GREEN}" letter-spacing="2">{label}</text>\n')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="200" viewBox="0 0 900 200" role="img" aria-label="GitHub record: {d['repos']} public repositories, {d['stars']} stars.">
<style>text{{font-family:{FONT};}}</style>
<rect width="900" height="200" rx="8" fill="{BG}" stroke="{LINE}"/>
{stat(40, d['repos'], 'PUBLIC REPOS')}{stat(220, d['stars'], 'STARS')}{stat(350, len(d['langs']), 'LANGUAGES')}
<line x1="470" y1="26" x2="470" y2="174" stroke="{LINE}"/>
<text x="500" y="46" font-size="12" fill="{RED}" letter-spacing="3">TOP LANGUAGES</text>
{bars}<text x="40" y="176" font-size="11" fill="{DIM}" letter-spacing="1">SYNCED {stamp} // PUBLIC REPOS ONLY</text>
</svg>'''

if __name__ == '__main__':
    try:
        data = collect()
    except Exception as e:
        print('Could not reach GitHub, keeping existing card:', e); sys.exit(0)
    open(OUT, 'w', encoding='utf-8').write(render(data, datetime.date.today().isoformat()))
    print('wrote', OUT, data['repos'], 'repos,', data['stars'], 'stars,', len(data['langs']), 'languages')
