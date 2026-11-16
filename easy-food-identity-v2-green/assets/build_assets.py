from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
import json, subprocess, sys, tempfile, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
FOREST, LIME, CREAM, INK = '#146B45', '#DDF45B', '#FFF8EA', '#17251C'
font = instantiateVariableFont(TTFont(ROOT / 'fonts/Manrope-Variable.ttf'), {'wght': 800})
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
upm = font['head'].unitsPerEm

def outlined(text, x, baseline, size, color, spacing=0):
    scale = size / upm
    parts = []
    for ch in text:
        name = cmap[ord(ch)]
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        parts.append(f'<path d="{pen.getCommands()}" transform="translate({x:.3f} {baseline:.3f}) scale({scale:.6f} {-scale:.6f})"/>')
        x += glyphs[name].width * scale + spacing
    return f'<g fill="{color}">'+''.join(parts)+'</g>', x

def grain(color, x=0, y=0, scale=1):
    return f'<g transform="translate({x} {y}) scale({scale})" stroke="{color}" stroke-width="17" stroke-linecap="round"><path d="M9 64 L36 10"/><path d="M45 64 L72 10"/><path d="M81 64 L108 10"/></g>'

def svg(w, h, body, background=None, title='Easy Food brand asset'):
    bg = f'<rect width="{w}" height="{h}" fill="{background}"/>' if background else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{title}</title>{bg}{body}</svg>'

def horizontal(color, tagline=False):
    easy, end = outlined('easy', 294, 255, 248, color, -8)
    food, _ = outlined('FOOD', 302, 321, 41, color, 15)
    parts = grain(color,105,151,1.32)+easy+food
    if tagline:
        tag, _ = outlined('Eat smart. Live easy.', 302, 376, 24, color, .2)
        parts += tag
    return parts

def stacked(color):
    easy, end = outlined('easy', 35, 350, 235, color, -7)
    food, _ = outlined('FOOD', 213, 427, 40, color, 13)
    return grain(color,221,64,1.35)+easy+food

logos = ROOT / 'logos'; icons = ROOT / 'icons'; patterns = ROOT / 'patterns'
for directory in [logos,icons,patterns]: directory.mkdir(exist_ok=True)
variants = {'forest':FOREST, 'black':'#000000', 'white':'#FFFFFF', 'cream':CREAM}
for name,color in variants.items():
    (logos/f'logo-horizontal-{name}.svg').write_text(svg(1060,400,horizontal(color)),encoding='utf-8')
    (logos/f'logo-stacked-{name}.svg').write_text(svg(600,500,stacked(color)),encoding='utf-8')
    (logos/f'symbol-{name}.svg').write_text(svg(640,480,grain(color,84,100,4)),encoding='utf-8')
(logos/'logo-primary-cream.svg').write_text(svg(1060,400,horizontal(FOREST),CREAM),encoding='utf-8')
(logos/'logo-reversed-forest.svg').write_text(svg(1060,400,horizontal(CREAM),FOREST),encoding='utf-8')
(logos/'logo-slogan-forest.svg').write_text(svg(1060,430,horizontal(FOREST,True)),encoding='utf-8')
reference_body = '<g transform="translate(50 190) scale(1.42)">'+horizontal(FOREST,True)+'</g>'
(ROOT/'logo-reference.svg').write_text(svg(1600,1000,reference_body,CREAM),encoding='utf-8')

def icon(paths,name):
    (icons/f'{name}.svg').write_text(svg(120,120,f'<g fill="none" stroke="{FOREST}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">{paths}</g>',None,name),encoding='utf-8')
icon('<path d="M20 59h80c-2 27-15 40-40 40S22 86 20 59Z"/><path d="M34 101h52M31 52c2-15 14-24 29-24s27 9 29 24"/><path d="M41 42l6-7m11 10 5-8m10 7 5-6M46 20l4-8m15 8 4-8"/>','easy-rice')
icon('<path d="M31 28 91 46 68 104 40 96Z"/><path d="m38 57 44 14M40 96l29-19M39 29c4-16 13-18 21-8 7-9 17-6 19 6 11-1 17 8 12 19"/><path d="m44 39 8 4m12 1 7 3m5 9 6 2"/>','easy-wrap')
icon('<path d="M19 61h82c-3 26-17 39-41 39S22 87 19 61Z"/><path d="M31 54c-9-9-4-22 8-21-1-15 15-22 24-11 12-12 28-1 23 13 13 0 18 14 9 23"/><path d="m41 36 17 22m13-25-9 24M35 101h50"/><circle cx="48" cy="49" r="5"/><path d="m77 45 8 5"/>','easy-salad')

tile = '<pattern id="grains" width="180" height="150" patternUnits="userSpaceOnUse">'+grain(FOREST,22,33,.7)+'</pattern>'
(patterns/'grain-pattern-cream.svg').write_text(svg(900,600,f'<defs>{tile}</defs><rect width="900" height="600" fill="url(#grains)"/>',CREAM),encoding='utf-8')
tile2 = '<pattern id="grains" width="180" height="150" patternUnits="userSpaceOnUse">'+grain(LIME,22,33,.7)+'</pattern>'
(patterns/'grain-pattern-forest.svg').write_text(svg(900,600,f'<defs>{tile2}</defs><rect width="900" height="600" fill="url(#grains)"/>',FOREST),encoding='utf-8')

tokens = {'name':'Easy Food','version':'2.0','colors':{'forest':FOREST,'lime':LIME,'cream':CREAM,'ink':INK,'white':'#FFFFFF'},'typography':{'latin':'Manrope','arabic':'Cairo','logoWeight':800},'slogan':'Eat smart. Live easy.'}
(ROOT/'design-tokens.json').write_text(json.dumps(tokens,indent=2),encoding='utf-8')
(ROOT/'design-tokens.css').write_text('''@font-face{font-family:Manrope;src:url('./fonts/Manrope-Variable.ttf') format('truetype');font-weight:200 800;font-display:swap;}\n@font-face{font-family:Cairo;src:url('./fonts/Cairo-Variable.ttf') format('truetype');font-weight:200 1000;font-display:swap;}\n:root{--ef-forest:#146B45;--ef-lime:#DDF45B;--ef-cream:#FFF8EA;--ef-ink:#17251C;--ef-white:#FFFFFF;--ef-font-latin:'Manrope',sans-serif;--ef-font-arabic:'Cairo',sans-serif;}\n''',encoding='utf-8')
(ROOT/'FONT-SOURCES.md').write_text('''# Font sources\n\nBoth families are distributed under the SIL Open Font License 1.1. Full license text is included next to each font.\n\n- Manrope variable, weight axis 200–800: https://github.com/google/fonts/tree/main/ofl/manrope\n- Cairo variable: https://github.com/google/fonts/tree/main/ofl/cairo\n- Retrieved 2026-11-13 from the official Google Fonts repository.\n- Logo letterforms use Manrope weight 800 and are converted to editable SVG outlines; no installed font is needed to display the logos.\n- Cairo is supplied for Arabic menu, signage, and brand-guide text; it is not the English logo font.\n\nSVG logos are native vector assets. PNG files are raster exports. Mockups elsewhere in this package are visual concepts and not packaging dielines.\n''',encoding='utf-8')

for file in ROOT.rglob('*.svg'): ET.parse(file)
print('SVG assets created and XML parsed:', len(list(ROOT.rglob('*.svg'))))

chrome = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
render_temp = tempfile.TemporaryDirectory(prefix='easy-food-render-')
profile = Path(render_temp.name) / 'chrome-profile'
def render(source,dest,w,h,transparent=False):
    args=[str(chrome),'--headless=new','--disable-gpu','--no-sandbox','--hide-scrollbars','--force-device-scale-factor=1',f'--user-data-dir={profile}',f'--window-size={w},{h}',f'--screenshot={dest.resolve()}']
    if transparent: args.append('--default-background-color=00000000')
    args.append(source.resolve().as_uri())
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=40)
    if not dest.exists(): raise RuntimeError(result.stderr.decode(errors='replace'))
if '--stacked-only' not in sys.argv:
    render(ROOT/'logo-reference.svg',ROOT/'logo-reference.png',1600,1000)
    print('REFERENCE_READY',ROOT/'logo-reference.png',flush=True)
for name in ['forest','black','white','cream']:
    if '--stacked-only' not in sys.argv:
        render(logos/f'logo-horizontal-{name}.svg',logos/f'logo-horizontal-{name}.png',1060,400,True)
        render(logos/f'symbol-{name}.svg',logos/f'symbol-{name}.png',640,480,True)
    render(logos/f'logo-stacked-{name}.svg',logos/f'logo-stacked-{name}.png',600,500,True)
print('PNG exports ready')
from PIL import Image
for file in logos.glob('*.png'):
    exported = Image.open(file)
    assert exported.mode == 'RGBA', f'PNG lacks alpha: {file.name}'
    assert exported.getchannel('A').getbbox(), f'Empty PNG: {file.name}'
    assert exported.getchannel('A').getextrema() == (0,255), f'PNG not transparent: {file.name}'
    left,top,right,bottom=exported.getchannel('A').getbbox()
    assert left>0 and top>0 and right<exported.width and bottom<exported.height, f'Clipped PNG: {file.name}'
print('All PNG exports verified: nonempty transparent RGBA.')
try:
    render_temp.cleanup()
except PermissionError:
    print('Chrome is still releasing its temporary profile in the OS temporary folder.')
