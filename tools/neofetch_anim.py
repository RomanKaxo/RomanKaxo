"""Animovaná neofetch karta pro GitHub profil: vlevo se střídají ASCII loga technologií a každé se otočí kolem svislé osy
(SVG + SMIL, GitHub ho v <img> přehraje bez skriptů), vpravo výpis jako v terminálu. Loga: Simple Icons (CC0)."""
import sys, html, math
from PIL import Image
SI, OUT = sys.argv[1], sys.argv[2]
LOGOS = [('javascript', 'JavaScript', 'F7DF1E'), ('typescript', 'TypeScript', '3178C6'), ('react', 'React', '61DAFB'), ('nodedotjs', 'Node.js', '5FA04E'),
         ('php', 'PHP', '777BB4'), ('laravel', 'Laravel', 'FF2D20'), ('html5', 'HTML5', 'E34F26'), ('css3', 'CSS3', '1572B6'), ('tailwindcss', 'Tailwind CSS', '06B6D4'),
         ('wordpress', 'WordPress', '3D9AD1'), ('mysql', 'MySQL', '4479A1'), ('git', 'Git', 'F05032'), ('archlinux', 'Arch Linux', '1793D1')]
COLS, ROWS = 56, 28            # znaků na logo
FPS = 24                        # snímků otočky za sekundu
FADE_IN, HOLD1, SPIN_S, HOLD2, FADE_OUT = .45, 1.1, 1.5, .5, .45   # časy jednoho loga v s
SPIN = int(SPIN_S * FPS)        # snímků otočky
RAMP = " .:-=+*#%@"
def frame(img, ang):
    c = math.cos(ang)
    w = max(1, int(img.width * abs(c)))
    im = img.resize((w, img.height), Image.LANCZOS)
    if c < 0: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    canvas = Image.new('RGBA', (img.width, img.height), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((img.width - w) // 2, 0))
    small = canvas.resize((COLS, ROWS), Image.LANCZOS)
    rows = []
    for y in range(ROWS):
        rows.append(''.join(' ' if (a := small.getpixel((x, y))[3]) < 40 else RAMP[min(9, max(1, int(a / 255 * 9 + .5)))] for x in range(COLS)))
    return rows
ease = lambda t: .5 - .5 * math.cos(math.pi * t)   # plynulý rozjezd i dojezd otáčky
per = FADE_IN + HOLD1 + SPIN_S + HOLD2 + FADE_OUT
total = per * len(LOGOS)
CW, LH, X0, Y0 = 8.4, 15.6, 40, 58
CX, CY = X0 + COLS * CW / 2, Y0 + ROWS * LH / 2
k = lambda t: f'{max(0, min(1, t / total)):.5f}'
def anim(points):
    """points = [(čas s, opacity)], lineárně mezi nimi, jinak 0."""
    pts = [(0, 0)] + points + [(total, 0)]
    pts = sorted({round(t, 4): v for t, v in pts}.items())
    return (f'<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="{";".join(k(t) for t, _ in pts)}" values="{";".join(f"{v:g}" for _, v in pts)}"/>')
def text(rows):
    return ''.join(f'<text x="{X0}" y="{Y0 + i * LH:.1f}" xml:space="preserve">{html.escape(r)}</text>' for i, r in enumerate(rows) if r.strip())
groups = []
for li, (slug, name, hexc) in enumerate(LOGOS):
    img = Image.open(f'{SI}/{slug}.png').convert('RGBA').resize((280, 280), Image.LANCZOS)
    pad = Image.new('RGBA', (280, 280), (0, 0, 0, 0)); pad.alpha_composite(img)
    t0 = li * per
    ts = t0 + FADE_IN + HOLD1               # začátek otočky
    te = ts + SPIN_S                        # konec otočky
    tend = t0 + per
    eps = .5 / FPS                          # krátké prolnutí sousedních snímků = měkčí pohyb
    # čelní snímek: nástup (prolnutí + mírné zvětšení), stání, pak znovu po otočce, stání, odchod
    front = text(frame(pad, 0))
    scale = (f'<animateTransform attributeName="transform" type="scale" additive="sum" dur="{total:.2f}s" repeatCount="indefinite" calcMode="spline" '
             f'keyTimes="0;{k(t0)};{k(t0 + FADE_IN)};{k(tend - FADE_OUT)};{k(tend)};1" values="1;.9;1;1;1.06;1" '
             f'keySplines="0 0 1 1;.2 .8 .3 1;0 0 1 1;.6 0 .8 .4;0 0 1 1"/>')
    groups.append(f'<g transform="translate({CX:.1f} {CY:.1f})"><g fill="#{hexc}">{anim([(t0, 0), (t0 + FADE_IN, 1), (ts, 1), (ts + eps, 0), (te - eps, 0), (te, 1), (tend - FADE_OUT, 1), (tend, 0)])}'
                  f'{scale}<g transform="translate({-CX:.1f} {-CY:.1f})">{front}</g></g></g>')
    for fi in range(1, SPIN):
        ang = 2 * math.pi * ease(fi / SPIN)
        a = ts + fi / FPS
        groups.append(f'<g fill="#{hexc}">{anim([(a - eps, 0), (a, 1), (a + 1 / FPS, 1), (a + 1 / FPS + eps, 0)])}{text(frame(pad, ang))}</g>')
    groups.append(f'<g>{anim([(t0, 0), (t0 + FADE_IN, 1), (tend - FADE_OUT, 1), (tend, 0)])}'
                  f'<text x="{CX:.0f}" y="{Y0 + ROWS * LH + 22:.0f}" text-anchor="middle" font-size="18" fill="#{hexc}">{html.escape(name)}</text></g>')
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
H = max(Y0 + ROWS * LH + 50, iy + 80)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{H:.0f}" viewBox="0 0 1200 {H:.0f}" role="img" aria-labelledby="t">
<title id="t">roman@kaco: technologie, se kterými pracuji ({", ".join(n for _, n, _ in LOGOS)})</title>
<rect width="1200" height="{H:.0f}" rx="16" fill="#0d0d11"/><rect x=".5" y=".5" width="1199" height="{H - 1:.0f}" rx="16" fill="none" stroke="#27272a"/>
<g font-family="JetBrains Mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="14">{"".join(groups)}</g>
<g font-family="JetBrains Mono,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">{"".join(out)}</g>
</svg>'''
open(OUT, 'w').write(svg)
print(f'ok {len(svg) // 1024} kB, smyčka {total:.1f} s, výška {H:.0f}')
