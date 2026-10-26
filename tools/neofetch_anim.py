"""Animovaná neofetch karta pro GitHub profil: vlevo se střídají ASCII loga technologií a každé se otočí kolem svislé osy
(SVG + SMIL, GitHub ho v <img> přehraje bez skriptů), vpravo výpis jako v terminálu. Loga: Simple Icons (CC0)."""
import sys, html, math
from PIL import Image
SI, OUT = sys.argv[1], sys.argv[2]
LOGOS = [('javascript', 'JavaScript', 'F7DF1E'), ('typescript', 'TypeScript', '3178C6'), ('react', 'React', '61DAFB'), ('nodedotjs', 'Node.js', '5FA04E'),
         ('php', 'PHP', '777BB4'), ('laravel', 'Laravel', 'FF2D20'), ('html5', 'HTML5', 'E34F26'), ('tailwindcss', 'Tailwind CSS', '06B6D4'),
         ('git', 'Git', 'F05032'), ('archlinux', 'Arch Linux', '1793D1')]
COLS, ROWS = 56, 28                  # znaků na logo
FADE_IN, HOLD1, SPIN_S, HOLD2, FADE_OUT = .7, 1.8, 2.8, .9, .7   # pomalejší tempo jednoho loga (s)
SPIN = 48                             # snímků otočky (~17 fps), úhel s plynulým rozjezdem a dojezdem
RAMP = " .:-=+*#%@"
def frame(img, ang):
    c = math.cos(ang)
    w = max(1, int(img.width * abs(c)))
    im = img.resize((w, img.height), Image.LANCZOS)
    if c < 0: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    canvas = Image.new('RGBA', (img.width, img.height), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((img.width - w) // 2, 0))
    small = canvas.resize((COLS, ROWS), Image.LANCZOS)
    return [''.join(' ' if (a := small.getpixel((x, y))[3]) < 40 else RAMP[min(9, max(1, int(a / 255 * 9 + .5)))] for x in range(COLS)) for y in range(ROWS)]
ease = lambda t: .5 - .5 * math.cos(math.pi * t)
per = FADE_IN + HOLD1 + SPIN_S + HOLD2 + FADE_OUT
total = per * len(LOGOS)
CW, LH, X0, Y0 = 8.4, 15.6, 40, 58
FH = ROWS * LH + 40                    # výška jednoho snímku ve „filmovém pásu“
CX, CY = X0 + COLS * CW / 2, Y0 + ROWS * LH / 2
k = lambda t: f'{max(0, min(1, t / total)):.5f}'
def text(rows, dy):
    # jeden <text> na snímek, řádky jako <tspan>: o řád méně prvků než text na řádek
    return (f'<text y="{Y0 + dy:.1f}" xml:space="preserve">' +
            ''.join(f'<tspan x="{X0}" dy="{0 if i == 0 else LH}">{html.escape(r) if r.strip() else " "}</tspan>' for i, r in enumerate(rows)) + '</text>')
groups = []
SAMPLES = 64                           # vzorků otočky; mezi nimi prohlížeč interpoluje v každém snímku displeje (60 fps)
def spin_values(sign):
    """Měřítko X přední (sign=1) nebo zadní (sign=-1) strany v průběhu otočky: max(0, sign·cos θ), θ s plynulým rozjezdem."""
    return [max(0.0, sign * math.cos(2 * math.pi * ease(i / SAMPLES))) for i in range(SAMPLES + 1)]
def side(rows, hexc, sign, t0, ts, te, tend):
    keys = ['0', k(ts)] + [k(ts + i * SPIN_S / SAMPLES) for i in range(1, SAMPLES)] + [k(te), '1']
    sv = spin_values(sign)
    base = 1.0 if sign > 0 else 0.0
    vals = [f'{base:.3f} 1', f'{sv[0]:.3f} 1'] + [f'{max(sv[i], .001):.3f} 1' if sv[i] > 0 else '0.001 1' for i in range(1, SAMPLES)] + [f'{base:.3f} 1', f'{base:.3f} 1']
    sc = (f'<animateTransform attributeName="transform" type="scale" dur="{total:.2f}s" repeatCount="indefinite" calcMode="linear" '
          f'keyTimes="{";".join(keys)}" values="{";".join(vals)}"/>')
    body = (f'<text y="{Y0:.1f}" xml:space="preserve">' +
            ''.join(f'<tspan x="{X0}" dy="{0 if i == 0 else LH}">{html.escape(r) if r.strip() else " "}</tspan>' for i, r in enumerate(rows)) + '</text>')
    return f'<g transform="translate({CX:.1f} 0)"><g>{sc}<g transform="translate({-CX:.1f} 0)" fill="#{hexc}"{"" if sign > 0 else " opacity=\".78\""}>{body}</g></g></g>'
for li, (slug, name, hexc) in enumerate(LOGOS):
    img = Image.open(f'{SI}/{slug}.png').convert('RGBA').resize((280, 280), Image.LANCZOS)
    t0 = li * per; ts = t0 + FADE_IN + HOLD1; te = ts + SPIN_S; tend = t0 + per
    front, back = frame(img, 0), frame(img, math.pi)
    fade = (f'<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="0;{k(t0)};{k(t0 + FADE_IN)};{k(tend - FADE_OUT)};{k(tend)};1" values="0;0;1;1;0;0" '
            f'keySplines="0 0 1 1;.25 .1 .25 1;0 0 1 1;.42 0 .58 1;0 0 1 1"/>')
    zoom = (f'<animateTransform attributeName="transform" type="scale" dur="{total:.2f}s" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="0;{k(t0)};{k(t0 + FADE_IN)};{k(tend - FADE_OUT)};{k(tend)};1" values="1;.9;1;1;1.06;1" '
            f'keySplines="0 0 1 1;.22 1 .36 1;0 0 1 1;.64 0 .78 0;0 0 1 1"/>')
    groups.append(f'<g opacity="0">{fade}<g transform="translate({CX:.1f} {CY:.1f})"><g>{zoom}<g transform="translate({-CX:.1f} {-CY:.1f})">'
                  f'{side(front, hexc, 1, t0, ts, te, tend)}{side(back, hexc, -1, t0, ts, te, tend)}'
                  f'<text x="{CX:.0f}" y="{Y0 + ROWS * LH + 22:.0f}" text-anchor="middle" font-size="18" fill="#{hexc}">{html.escape(name)}</text></g></g></g></g>')
# jemné plynulé pohupování celého loga (běží stále, interpoluje prohlížeč)
groups = [f'<g><animateTransform attributeName="transform" type="translate" dur="4s" repeatCount="indefinite" calcMode="spline" values="0 0;0 -6;0 0" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>'] + groups + ['</g>']
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
