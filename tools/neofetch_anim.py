"""Animovaná neofetch karta pro GitHub profil: vlevo se střídají ASCII loga technologií a každé se otočí kolem svislé osy
(SVG + SMIL, GitHub ho v <img> přehraje bez skriptů), vpravo výpis jako v terminálu. Loga: Simple Icons (CC0)."""
import sys, html, math
from PIL import Image
SI, OUT = sys.argv[1], sys.argv[2]
LOGOS = [('javascript', 'JavaScript', 'F7DF1E'), ('typescript', 'TypeScript', '3178C6'), ('react', 'React', '61DAFB'), ('nodedotjs', 'Node.js', '5FA04E'),
         ('php', 'PHP', '777BB4'), ('laravel', 'Laravel', 'FF2D20'), ('html5', 'HTML5', 'E34F26'), ('tailwindcss', 'Tailwind CSS', '06B6D4'),
         ('git', 'Git', 'F05032'), ('archlinux', 'Arch Linux', '1793D1')]
COLS, ROWS = 56, 28                  # znaků na logo
PRINT, HOLD, FADE = 1.6, 3.2, .8      # vypsání řádek po řádku, stání, prolnutí do dalšího loga (s)
RAMP = " .:-=+*#%@"
FONT = '/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Regular.ttf'
CW, LH, X0, Y0 = 8.4, 15.6, 40, 46
AW, AH = COLS * CW, ROWS * LH
def ascii_rows(img):
    small = img.resize((COLS, ROWS), Image.LANCZOS)
    return [''.join(' ' if (a := small.getpixel((x, y))[3]) < 40 else RAMP[min(9, max(1, int(a / 255 * 9 + .5)))] for x in range(COLS)) for y in range(ROWS)]
def ascii_png(rows, hexc, scale=2):
    """ASCII předkreslené do PNG: prohlížeč pak animuje jen obrázek (ořez, průhlednost), ne tisíce znaků."""
    from PIL import ImageDraw, ImageFont
    import io, base64
    f = ImageFont.truetype(FONT, int(14 * scale))
    im = Image.new('RGBA', (int(AW * scale), int(AH * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); col = tuple(int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    for i, r in enumerate(rows):
        d.text((0, i * LH * scale), r, font=f, fill=col + (255,))
    buf = io.BytesIO(); im.quantize(colors=16, method=Image.Quantize.FASTOCTREE).save(buf, 'PNG', optimize=True)  # 16 barev stačí (jedna barva + průhlednost)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
per = PRINT + HOLD + FADE
total = per * len(LOGOS)
k = lambda t: f'{max(0, min(1, (t % total) / total)):.5f}'
def anim(attr, pts, spline=None):
    """pts = [(čas, hodnota)] v rámci smyčky; mezi nimi lineárně nebo podle křivky."""
    pts = sorted(pts)
    keys = ';'.join(k(t) if 0 < t < total else ('0' if t <= 0 else '1') for t, _ in pts)
    vals = ';'.join(str(v) for _, v in pts)
    sp = f' calcMode="spline" keySplines="{";".join([spline] * (len(pts) - 1))}"' if spline else ''
    return f'<animate attributeName="{attr}" dur="{total:.2f}s" repeatCount="indefinite" keyTimes="{keys}" values="{vals}"{sp}/>'
groups, defs = [], []
for li, (slug, name, hexc) in enumerate(LOGOS):
    img = Image.open(f'{SI}/{slug}.png').convert('RGBA').resize((280, 280), Image.LANCZOS)
    png = ascii_png(ascii_rows(img), hexc)
    t0 = li * per; tp = t0 + PRINT; th = tp + HOLD; tend = th + FADE
    # tisk shora dolů = výška ořezu roste po celých řádcích; jemná křivka, ať to „dojede“
    rows_h = [(t0 + PRINT * i / ROWS, round(i * LH, 1)) for i in range(ROWS + 1)]
    clip_h = [(0, 0)] + ([(t0 - .001, 0)] if t0 > 0 else []) + rows_h + [(tend, AH), (tend + .001, 0), (total, 0)]
    defs.append(f'<clipPath id="c{li}"><rect x="{X0 - 4}" y="{Y0}" width="{AW + 8:.0f}" height="0">{anim("height", clip_h)}</rect></clipPath>')
    op = [(0, 0)] + ([(t0 - .001, 0)] if t0 > 0 else []) + [(t0, 1), (th, 1), (tend, 0), (total, 0)]
    cur_y = [(0, Y0)] + ([(t0 - .001, Y0)] if t0 > 0 else []) + [(t0 + PRINT * i / ROWS, round(Y0 + i * LH, 1)) for i in range(ROWS + 1)] + [(total, Y0)]
    cur_op = [(0, 0)] + ([(t0 - .001, 0)] if t0 > 0 else []) + [(t0, 1), (tp, 1), (tp + .25, 0), (total, 0)]
    label_w = [(0, 0)] + ([(t0 - .001, 0)] if t0 > 0 else []) + [(tp, 0), (tp + .6, 260), (tend, 260), (tend + .001, 0), (total, 0)]
    defs.append(f'<clipPath id="n{li}"><rect x="{X0 + AW / 2 - 130:.0f}" y="{Y0 + AH + 2:.0f}" width="0" height="30">{anim("width", label_w)}</rect></clipPath>')
    groups.append(f'<g opacity="0">{anim("opacity", op, ".4 0 .2 1")}'
                  f'<image x="{X0}" y="{Y0}" width="{AW:.0f}" height="{AH:.0f}" href="{png}" clip-path="url(#c{li})"/>'
                  f'<rect x="{X0}" width="{AW:.0f}" height="3" fill="#{hexc}" opacity="0">{anim("y", cur_y)}{anim("opacity", cur_op)}</rect>'
                  f'<text x="{X0 + AW / 2:.0f}" y="{Y0 + AH + 24:.0f}" text-anchor="middle" font-size="18" fill="#{hexc}" clip-path="url(#n{li})">{html.escape(name)}</text></g>')
groups = [f'<defs>{"".join(defs)}</defs>'] + groups
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
