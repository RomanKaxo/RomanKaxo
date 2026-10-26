"""Animovaná neofetch karta pro GitHub profil: vlevo se střídají ASCII loga technologií a každé se otočí kolem svislé osy
(SVG + SMIL, GitHub ho v <img> přehraje bez skriptů), vpravo výpis jako v terminálu. Loga: Simple Icons (CC0)."""
import sys, html, math
from PIL import Image
SI, OUT = sys.argv[1], sys.argv[2]
LOGOS = [('javascript', 'JavaScript', 'F7DF1E'), ('typescript', 'TypeScript', '3178C6'), ('react', 'React', '61DAFB'), ('nodedotjs', 'Node.js', '5FA04E'),
         ('php', 'PHP', '777BB4'), ('laravel', 'Laravel', 'FF2D20'), ('html5', 'HTML5', 'E34F26'), ('tailwindcss', 'Tailwind CSS', '06B6D4'),
         ('git', 'Git', 'F05032'), ('archlinux', 'Arch Linux', '1793D1')]
COLS, ROWS = 56, 28                  # znaků na logo
T_IN, T_HOLD, T_OUT = 1.3, 3.4, 1.3         # poskládání, stání, rozplynutí (s)
STAGES = 7                            # mezistavů rozplynutí; mezi nimi plynulé prolnutí (obrázky = levné pro prohlížeč)
RAMP = " .:-=+*#%@"
FONT = '/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Regular.ttf'
CW, LH, X0, Y0 = 8.4, 15.6, 40, 46
AW, AH = COLS * CW, ROWS * LH
import random, io, base64
from PIL import ImageDraw, ImageFont
SC = 1.0
FNT = ImageFont.truetype(FONT, int(14 * SC))
def ascii_rows(img):
    small = img.resize((COLS, ROWS), Image.LANCZOS)
    return [''.join(' ' if (a := small.getpixel((x, y))[3]) < 40 else RAMP[min(9, max(1, int(a / 255 * 9 + .5)))] for x in range(COLS)) for y in range(ROWS)]
def stage_png(rows, hexc, thr, p):
    """Mezistav rozplynutí p ∈ <0,1>: znak s prahem pod p už zmizel, znaky těsně nad prahem blednou, stoupají a mění se na lehčí."""
    im = Image.new('RGBA', (int(AW * SC), int(AH * SC) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); col = tuple(int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == ' ': continue
            t = thr[y][x]
            if t < p: continue
            near = max(0.0, 1 - (t - p) / .22)          # 1 = právě se rozpouští
            a = int(255 * (1 - .75 * near))
            c = RAMP[max(1, RAMP.index(ch) - int(near * 5))]   # lehčí znak = „řídne“
            d.text((x * CW * SC, (y * LH - near * 14) * SC + 20), c, font=FNT, fill=col + (a,))
    buf = io.BytesIO(); im.quantize(colors=8, method=Image.Quantize.FASTOCTREE).save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
per = T_IN + T_HOLD + T_OUT
total = per * len(LOGOS)
k = lambda t: f'{max(0, min(1, t / total)):.5f}'
def anim(attr, pts, spline=None):
    pts = sorted(set((round(t, 4), v) for t, v in pts))
    keys = ';'.join('0' if t <= 0 else '1' if t >= total else k(t) for t, _ in pts)
    vals = ';'.join(f'{v:g}' for _, v in pts)
    sp = f' calcMode="spline" keySplines="{";".join([spline] * (len(pts) - 1))}"' if spline else ''
    return f'<animate attributeName="{attr}" dur="{total:.2f}s" repeatCount="indefinite" keyTimes="{keys}" values="{vals}"{sp}/>'
def bump(c, w):
    """průhlednost mezistavu: vrchol v čase c, lineárně ±w (sousední mezistavy se prolínají)."""
    return [(0, 0), (max(0, c - w), 0), (c, 1), (min(total, c + w), 0), (total, 0)]
groups = []
rnd = random.Random(7)
for li, (slug, name, hexc) in enumerate(LOGOS):
    img = Image.open(f'{SI}/{slug}.png').convert('RGBA').resize((280, 280), Image.LANCZOS)
    rows = ascii_rows(img)
    # práh rozplynutí: náhoda + mírně shora dolů, ať to působí jako kouř stoupající vzhůru
    thr = [[min(.999, .65 * rnd.random() + .35 * (y / ROWS)) for x in range(COLS)] for y in range(ROWS)]
    t0 = li * per; ti = t0 + T_IN; th = ti + T_HOLD; tend = th + T_OUT
    step_in, step_out = T_IN / STAGES, T_OUT / STAGES
    for si in range(STAGES + 1):
        p = 1 - si / STAGES                         # 1 = nic, 0 = celé logo
        png = stage_png(rows, hexc, thr, p * 1.0 if si < STAGES else -1)
        if si == STAGES:                            # celé logo: nástup, stání, začátek odchodu
            op = [(0, 0), (max(0, ti - step_in), 0), (ti, 1), (th, 1), (min(total, th + step_out), 0), (total, 0)]
        else:
            c_in = t0 + si * step_in                # při skládání roste
            c_out = tend - si * step_out            # při rozplývání ubývá (stejné mezistavy obráceně)
            op = sorted(set(bump(c_in, step_in) + bump(c_out, step_out)))
            op = [(t, v) for t, v in op if not (t in (0, total) and v)] 
        groups.append(f'<image x="{X0}" y="{Y0 - 20 / SC:.1f}" width="{AW:.0f}" height="{AH + 40 / SC:.0f}" href="{png}" opacity="0">{anim("opacity", op)}</image>')
    groups.append(f'<text x="{X0 + AW / 2:.0f}" y="{Y0 + AH + 26:.0f}" text-anchor="middle" font-size="18" fill="#{hexc}" opacity="0">'
                  f'{anim("opacity", [(0, 0), (max(0, ti - .4), 0), (ti, 1), (th, 1), (th + .5, 0), (total, 0)], ".4 0 .2 1")}{html.escape(name)}</text>')
A, K, M, T = '#ff5a4a', '#7dd3fc', '#8b8b95', '#f4f4f5'
info = [('k', 'Škola', 'SOŠ EDUCAnet Brno · IT, 4. ročník'), ('k', 'Město', 'Brno'), ('k', 'OS', 'Arch Linux'), ('s',),
        ('k', 'Frontend', 'HTML · CSS · JavaScript · TypeScript · React'), ('k', 'Backend', 'Node.js · PHP · Laravel · MySQL · C#'),
        ('k', 'Web', 'WordPress · Tailwind · Vite'), ('k', 'AI', 'Claude Code · Codex · Ollama'), ('k', 'Video', 'Remotion · ffmpeg'), ('s',),
        ('k', 'Dělám', 'Elaris, harness pro LLM agenty'), ('k', 'Klienti', 'Tři Mistři · Wash&amp;Wrap · OKRiders'), ('k', 'Mail', 'romanek8888@email.cz')]
IX, iy = 560, 84
out = [f'<text x="{IX}" y="{iy}" font-size="21" font-weight="700"><tspan fill="{A}">roman</tspan><tspan fill="{T}">@</tspan><tspan fill="{A}">kaco</tspan></text>',
       f'<text x="{IX}" y="{iy + 16}" fill="#3f3f46" font-size="15">{"─" * 38}</text>']
iy += 50
for row in info:
    if row[0] == 's': iy += 10; continue
    out.append(f'<text x="{IX}" y="{iy}" font-size="16" xml:space="preserve"><tspan fill="{K}" font-weight="700">{row[1]}</tspan><tspan fill="{M}">: </tspan><tspan fill="{T}">{row[2]}</tspan></text>')
    iy += 28
cols = ['#18181b', '#ff5a4a', '#4ade80', '#facc15', '#60a5fa', '#c084fc', '#22d3ee', '#f4f4f5']
out.append(''.join(f'<rect x="{IX + i * 30}" y="{iy}" width="30" height="18" fill="{c}"/>' for i, c in enumerate(cols)))
# blikající kurzor
out.append(f'<rect x="{IX}" y="{iy + 40}" width="11" height="19" fill="{T}"><animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite" calcMode="discrete"/></rect>')
H = max(Y0 + AH + 50, iy + 80)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{H:.0f}" viewBox="0 0 1200 {H:.0f}" role="img" aria-labelledby="t">
<title id="t">roman@kaco: technologie, se kterými pracuji ({", ".join(n for _, n, _ in LOGOS)})</title>
<rect width="1200" height="{H:.0f}" rx="16" fill="#0d0d11"/><rect x=".5" y=".5" width="1199" height="{H - 1:.0f}" rx="16" fill="none" stroke="#27272a"/>
<g font-family="JetBrains Mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="14">{"".join(groups)}</g>
<g font-family="JetBrains Mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">{"".join(out)}</g>
</svg>'''
open(OUT, 'w').write(svg)
print(f'ok {len(svg) // 1024} kB, smyčka {total:.1f} s, výška {H:.0f}')
