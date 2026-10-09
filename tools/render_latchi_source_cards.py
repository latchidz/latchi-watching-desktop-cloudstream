#!/usr/bin/env python3
"""Render LATCHI's 3:1 source cards and multi-resolution launcher icon.
Provider marks are fetched from the public extension manifest; unavailable marks
use a clearly documented typographic fallback. No plugin code is bundled here.
"""
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
import hashlib
import json
import math
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'linux-native/assets/latchi-sources'
MANIFEST = 'https://raw.githubusercontent.com/Abodabodd/re-3arabi/refs/heads/builds/plugins.json'
REPOSITORY = 'https://raw.githubusercontent.com/Abodabodd/re-3arabi/refs/heads/main/repo'
SOURCES = [
    ('3isk', 'قصة عشق ١', '3isk', 'qissat-eshq-1', '#ed6379'),
    ('eseek', 'قصة عشق ٢', 'Eshek', 'qissat-eshq-2', '#f1af6c'),
    ('Krmzy', 'قرمزي', 'Krmzy', 'krmzy', '#bc83f8'),
    ('MyCimaProvider', 'ماي سيما', 'MyCima', 'mycima', '#69cdc3'),
    ('Topcinema', 'توب سينما', 'TopCinema', 'topcinema', '#74b6ff'),
    ('TukTukcima', 'توك توك سيما', 'TukTukcima', 'tuktukcima', '#f1d075'),
    ('Tuniflix', 'تونيفليكس', 'Tuniflix', 'tuniflix', '#b398fa'),
    ('Wecima', 'وي سيما', 'WeCima', 'wecima', '#f490bb'),
]
FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
BOLD = FONT.with_name('DejaVuSans-Bold.ttf')

def font(size, bold=False):
    path = BOLD if bold else FONT
    if not path.exists():
        raise RuntimeError('Install DejaVu Sans and Pillow with RAQM for Arabic shaping.')
    return ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.RAQM)

def rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))

def fetch_mark(item):
    name, plugin = item
    url = plugin.get('iconUrl', '')
    result = {'url': url, 'available': False}
    if not url.startswith('https://'):
        return name, None, result
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 LATCHI/1.0'})
        with urllib.request.urlopen(request, timeout=12) as response:
            data = response.read(4 * 1024 * 1024 + 1)
        if len(data) > 4 * 1024 * 1024:
            raise ValueError('Logo exceeds size limit')
        image = Image.open(BytesIO(data))
        image.load()
        image = image.convert('RGBA')
        image.save(ASSETS / 'marks' / (name + '.png'))
        result.update(available=True, sha256=hashlib.sha256(data).hexdigest(), original_size=list(image.size))
        return name, image, result
    except Exception as error:
        result['fallback_reason'] = type(error).__name__
        return name, None, result

def card(source, mark):
    ident, arabic, english, filename, accent = source
    color = rgb(accent)
    image = Image.new('RGBA', (1800, 600))
    pixels = image.load()
    for y in range(600):
        for x in range(1800):
            glow = max(0, 1 - math.hypot((x - 265) / 900, (y - 250) / 710))
            right = x / 1800
            pixels[x, y] = tuple(int((10, 15, 27)[i] + color[i] * glow * .18 + right * 5) for i in range(3)) + (255,)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, 1797, 597), radius=44, outline=tuple(int(v * .38) for v in color) + (255,), width=3)
    draw.line((600, 56, 1040, 540), fill=(255, 255, 255, 12), width=2)
    draw.line((690, 56, 1130, 540), fill=(*color, 30), width=2)
    draw.rounded_rectangle((91, 111, 481, 501), radius=68, fill=(10, 15, 26, 220), outline=(*color, 95), width=2)
    if mark is not None:
        mark = mark.copy()
        factor = min(245 / mark.width, 245 / mark.height)
        mark = mark.resize((max(1, round(mark.width * factor)), max(1, round(mark.height * factor))), Image.Resampling.LANCZOS)
        image.alpha_composite(mark, (286 - mark.width // 2, 306 - mark.height // 2))
    else:
        initials = {'3isk': '3', 'eseek': 'E', 'Krmzy': 'K', 'MyCimaProvider': 'MC', 'Topcinema': 'TC', 'TukTukcima': 'TT', 'Tuniflix': 'TF', 'Wecima': 'WC'}[ident]
        draw.text((286, 302), initials, font=font(114, True), fill=(*color, 255), anchor='mm')
    draw.text((1684, 68), 'LATCHI WATCHING  /  SOURCES', font=font(29, True), fill=(147, 158, 180), anchor='ra')
    draw.text((1688, 154), arabic, font=font(82, True), fill=(247, 249, 255), anchor='ra', direction='rtl', language='ar')
    draw.text((1684, 285), english, font=font(58, True), fill=(*color, 255), anchor='ra')
    draw.text((1684, 408), 'أفلام · مسلسلات', font=font(50), fill=(180, 192, 211), anchor='ra', direction='rtl', language='ar')
    draw.rounded_rectangle((1470, 508, 1687, 556), radius=24, fill=tuple(int(v * .17 + 22 * .83) for v in color) + (255,))
    draw.text((1578, 532), 'CLOUDSTREAM', font=font(23, True), fill=(*color, 255), anchor='mm')
    draw.ellipse((568, 263, 638, 333), outline=(*color, 115), width=2)
    draw.polygon(((614, 285), (614, 311), (594, 298)), fill=(*color, 235))
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 1799, 599), radius=46, fill=255)
    image.putalpha(mask)
    return image

def launcher():
    image = Image.new('RGBA', (1024, 1024))
    px = image.load()
    for y in range(1024):
        for x in range(1024):
            t = (x + y) / 2048
            px[x, y] = (int(108 - 62 * t), int(83 + 27 * t), int(240 - 33 * t), 255)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((42, 42, 982, 982), radius=237, outline=(255, 255, 255, 55), width=8)
    draw.line(((226, 265), (226, 734), (560, 734)), fill=(255, 255, 255), width=95, joint='curve')
    draw.polygon(((437, 260), (437, 635), (779, 447)), fill=(255, 255, 255))
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 1023, 1023), radius=258, fill=255)
    image.putalpha(mask)
    image.save(ROOT / 'linux-native/assets/latchi-launcher.png')
    image.save(ROOT / 'packaging/latchi-watching.ico', sizes=[(n, n) for n in [16, 24, 32, 48, 64, 128, 256]])


def main():
    (ASSETS / 'cards').mkdir(parents=True, exist_ok=True)
    (ASSETS / 'marks').mkdir(exist_ok=True)
    with urllib.request.urlopen(MANIFEST, timeout=30) as response:
        plugins = json.load(response)
    chosen = {x['internalName']: x for x in plugins if x.get('internalName') in {s[0] for s in SOURCES}}
    if len(chosen) != len(SOURCES):
        raise RuntimeError('One of the eight required provider IDs is missing from the manifest.')
    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for ident, mark, provenance in pool.map(fetch_mark, chosen.items()):
            results[ident] = (mark, provenance)
    output = []
    for source in SOURCES:
        ident, arabic, english, filename, accent = source
        mark, provenance = results[ident]
        card(source, mark).save(ASSETS / 'cards' / (filename + '.png'), optimize=True)
        output.append({'id': ident, 'arabic': arabic, 'english': english, 'card': filename + '.png', 'accent': accent, 'logo': provenance})
        print(ident, 'logo' if mark is not None else 'documented typographic fallback')
    (ASSETS / 'sources.json').write_text(json.dumps({'repository': REPOSITORY, 'manifest': MANIFEST, 'sources': output}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ASSETS / 'plugins.snapshot.json').write_text(json.dumps([chosen[s[0]] for s in SOURCES], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    launcher()

if __name__ == '__main__':
    main()
