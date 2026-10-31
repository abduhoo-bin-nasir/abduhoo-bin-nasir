#!/usr/bin/env python3
"""
Rebuilds assets/subject-file.svg (the photo + info card at the top of the README).

Change the photo:
    pip install pillow
    python scripts/make_card.py path/to/new-photo.jpg
    # optional: pick the crop yourself (x0,y0,x1,y1 in pixels of YOUR photo, keep it 4:5 portrait)
    python scripts/make_card.py photo.jpg --crop 140,170,800,995
    # photo already edited/graded? keep its own colours instead of the green tint
    python scripts/make_card.py photo.jpg --keep-color

Change the text: edit ROWS / PROMPT below and run it again.
Then:  git add -A && git commit -m "Update card" && git push
"""
import argparse, base64, io, random, sys
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter

# ---------------- editable text ----------------
PROMPT_USER = 'abduhoo@dev'
PROMPT_CMD  = 'whoami'
CAM_LABEL   = 'CAM 04 // SUBLEVEL 2'
STAMP_TOP   = 'SUBJECT 042'
STAMP_SUB   = 'OBSERVED // 02:14'
ROWS = [  # (label, value)   value None = the blinking red status line
    ('SUBJECT',     'Abduhoo Bin Nasir'),
    ('STATUS',      None),
    ('INSTITUTION', 'Institute of Space Technology'),
    ('PROGRAM',     'BS Computer Science, 2025-2029'),
    ('ROLES',       'Game Dev Lead @ DevCore'),
    ('',            'Teaching Assistant (OOP)'),
    ('LANGUAGES',   'C++  Kotlin  GDScript  PHP  JS'),
    ('FOCUS',       'Game engines, multiplayer, raycasting'),
    ('INTERESTS',   'Game dev, GUI apps, Android dev'),
    ('EDITOR',      'VS Code'),
    ('OS',          'Windows'),
    ('LAST SEEN',   'Debugging, 2 AM'),
]
# ------------------------------------------------

BG='#0c0a0a'; GREEN='#8fb89a'; BONE='#d8d0bd'; RED='#d23a32'; DIM='#5f564c'; LINE='#2a2222'
FONT="'Courier New', Courier, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
W, H = 340, 425

def prep_photo(path, crop, keep_color=False):
    im = Image.open(path).convert('RGB')
    if crop:
        im = im.crop(crop)
    else:  # 4:5 portrait, centred, slightly biased to the top (heads live there)
        w, h = im.size
        cw = min(w, int(h * 0.8)); ch = int(cw / 0.8)
        x0 = (w - cw) // 2; y0 = int((h - ch) * 0.15)
        im = im.crop((x0, y0, x0 + cw, y0 + ch))
    im = im.resize((W, H), Image.LANCZOS)
    if keep_color:   # photo is already graded the way you like it: keep its colours
        t = im.point(lambda v: int(255 * (v / 255) ** 0.72))      # lift the shadows a little so faces stay visible
        t = ImageEnhance.Contrast(t).enhance(1.05)
    else:            # default: green CCTV look
        g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
        g = ImageEnhance.Brightness(ImageEnhance.Contrast(g).enhance(1.25)).enhance(1.05)
        t = ImageOps.colorize(g, black='#050807', mid='#42604d', white='#d7eadc')
    vig = Image.new('L', (W, H), 0)
    ImageDraw.Draw(vig).ellipse((-W*0.25, -H*0.15, W*1.25, H*1.15), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(60))
    t = Image.composite(t, Image.new('RGB', (W, H), '#050807'), vig)
    random.seed(7); px = t.load()
    for y in range(H):
        for x in range(W):
            r, gc, b = px[x, y]; n = random.randint(-9, 9); k = 0.82 if y % 3 == 0 else 1.0
            px[x, y] = tuple(max(0, min(255, int((v + n) * k))) for v in (r, gc, b))
    buf = io.BytesIO(); t.save(buf, 'JPEG', quality=72, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

def build_svg(b64):
    rx, vx, y0, step = 404, 534, 114, 28
    rows = ''
    for i, (l, v) in enumerate(ROWS):
        y = y0 + i * step
        if l: rows += f'<text x="{rx}" y="{y}" font-size="14" fill="{GREEN}" letter-spacing="1">{l}</text>\n'
        if v is None:
            rows += (f'<circle class="blink" cx="{vx+5}" cy="{y-5}" r="4.5" fill="{RED}"/>'
                     f'<text x="{vx+17}" y="{y}" font-size="14" fill="{RED}" letter-spacing="1">ACTIVE // OBSERVED</text>\n')
        else:
            rows += f'<text x="{vx}" y="{y}" font-size="14" fill="{BONE}">{v}</text>\n'
    last_y = y0 + len(ROWS) * step + 6
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="500" viewBox="0 0 900 500" role="img" aria-label="Profile card for Abduhoo Bin Nasir">
<style>
  text{{font-family:{FONT};}}
  .blink{{animation:blink 1.1s steps(1) infinite}}
  @keyframes blink{{0%,60%{{opacity:1}}61%,100%{{opacity:0}}}}
  .sweep{{animation:sweep 4.5s linear infinite}}
  @keyframes sweep{{from{{transform:translateY(-70px)}}to{{transform:translateY(430px)}}}}
  .flick{{animation:flick 6s steps(1) infinite}}
  @keyframes flick{{0%,93%,96%,100%{{opacity:1}}94%{{opacity:.82}}95%{{opacity:.93}}}}
  @media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
</style>
<defs>
  <clipPath id="ph"><rect x="28" y="28" width="{W}" height="{H}"/></clipPath>
  <linearGradient id="sw" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset=".5" stop-color="{GREEN}" stop-opacity=".22"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect width="900" height="500" rx="10" fill="{BG}" stroke="{LINE}"/>
<g class="flick">
  <image x="28" y="28" width="{W}" height="{H}" href="data:image/jpeg;base64,{b64}" preserveAspectRatio="xMidYMid slice"/>
  <g clip-path="url(#ph)"><rect class="sweep" x="28" y="28" width="{W}" height="70" fill="url(#sw)"/></g>
</g>
<rect x="28" y="28" width="{W}" height="{H}" fill="none" stroke="{LINE}"/>
<g stroke="{GREEN}" stroke-width="2" fill="none" opacity=".9">
  <path d="M40 58V40H58"/><path d="M{28+W-12} 58V40H{28+W-30}"/>
  <path d="M40 {28+H-30}V{28+H-12}H58"/><path d="M{28+W-12} {28+H-30}V{28+H-12}H{28+W-30}"/>
</g>
<rect x="40" y="52" width="178" height="22" fill="{BG}" fill-opacity=".72"/>
<rect x="{28+W-84}" y="52" width="62" height="22" fill="{BG}" fill-opacity=".72"/>
<rect x="40" y="{28+H-40}" width="106" height="22" fill="{BG}" fill-opacity=".72"/>
<text x="46" y="68" font-size="12" fill="{GREEN}" letter-spacing="1">{CAM_LABEL}</text>
<circle class="blink" cx="{28+W-70}" cy="63" r="4.5" fill="{RED}"/>
<text x="{28+W-60}" y="68" font-size="12" fill="{RED}" letter-spacing="1">REC</text>
<text x="46" y="{28+H-20}" font-size="12" fill="{GREEN}" letter-spacing="1">TC 02:14:07</text>
<g transform="rotate(-8 120 372)">
  <rect x="44" y="346" width="190" height="46" fill="{BG}" fill-opacity=".72" stroke="{RED}" stroke-width="2" stroke-dasharray="6 4"/>
  <text x="58" y="368" font-size="18" fill="{RED}" letter-spacing="2">{STAMP_TOP}</text>
  <text x="58" y="385" font-size="12" fill="{GREEN}" letter-spacing="2">{STAMP_SUB}</text>
</g>
<text x="28" y="{28+H+22}" font-size="11" fill="{DIM}" letter-spacing="1">FIG. 1 // CAM 04 STILL</text>

<text x="{rx}" y="52" font-size="15"><tspan fill="{GREEN}">{PROMPT_USER}</tspan><tspan fill="{DIM}">:~$ </tspan><tspan fill="{BONE}">{PROMPT_CMD}</tspan></text>
<line x1="{rx}" y1="72" x2="872" y2="72" stroke="{DIM}" stroke-dasharray="3 5"/>
{rows}
<text x="{rx}" y="{last_y+22}" font-size="15"><tspan fill="{GREEN}">{PROMPT_USER}</tspan><tspan fill="{DIM}">:~$ </tspan><tspan class="blink" fill="{BONE}">&#9608;</tspan></text>
</svg>'''

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Rebuild assets/subject-file.svg from a photo')
    ap.add_argument('photo'); ap.add_argument('--crop', help='x0,y0,x1,y1 in photo pixels')
    ap.add_argument('--out', default='assets/subject-file.svg')
    ap.add_argument('--keep-color', action='store_true', help="don't tint the photo green")
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(',')) if a.crop else None
    svg = build_svg(prep_photo(a.photo, crop, a.keep_color))
    open(a.out, 'w', encoding='utf-8').write(svg)
    print('wrote', a.out, f'({len(svg)//1024} KB)')
