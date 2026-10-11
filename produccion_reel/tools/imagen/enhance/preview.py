"""Composite cutouts on the reel gradient (with the CSS drop shadow) at display size.

python preview.py OUT.png DISPW DISPH ZOOMBOX(x0,y0,x1,y1 in display px) new.png [old.png]
Writes OUT.png: [new | old] at display size on top, and 2x zooms of ZOOMBOX below.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def gradient(w, h):
    # linear-gradient(170deg, #6a9ad6 0%, #3a6db3 50%, #24508f 100%) ~ vertical
    t = np.linspace(0, 1, h)[:, None, None] * np.ones((1, w, 1))
    c0 = np.array([0x6a, 0x9a, 0xd6], np.float32); c1 = np.array([0x3a, 0x6d, 0xb3], np.float32)
    c2 = np.array([0x24, 0x50, 0x8f], np.float32)
    a = np.where(t < .5, c0 + (c1 - c0) * (t / .5), c1 + (c2 - c1) * ((t - .5) / .5))
    return Image.fromarray(a.astype(np.uint8)).convert('RGBA')


def place(im, dw, dh, margin=60):
    if dw == 0:
        dw = int(round(im.width * dh / im.height))
    if dh == 0:
        dh = int(round(im.height * dw / im.width))
    W, H = dw + 2 * margin, dh + 2 * margin + 40
    bg = gradient(W, H)
    obj = im.resize((dw, dh), Image.LANCZOS)
    a = np.asarray(obj)[..., 3].astype(np.float32) / 255
    sh = np.zeros((H, W), np.float32)
    sh[margin + 30:margin + 30 + dh, margin:margin + dw] = a * 0.55
    sh = Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(20))
    shadow = Image.new('RGBA', (W, H), (8, 24, 60, 0))
    shadow.putalpha(sh)
    bg.alpha_composite(shadow)
    bg.alpha_composite(obj, (margin, margin))
    return bg, margin


if __name__ == '__main__':
    out, dw, dh, zb = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    files = sys.argv[5:]
    zb = [int(v) for v in zb.split(',')]
    panels = []
    zooms = []
    for f in files:
        im = Image.open(f).convert('RGBA')
        p, mg = place(im, dw if len(files) == 1 or True else dw, dh)
        d = ImageDraw.Draw(p)
        d.text((10, 8), f.split('/')[-1], fill=(255, 255, 255, 255))
        panels.append(p)
        z = p.crop((zb[0] + mg, zb[1] + mg, zb[2] + mg, zb[3] + mg))
        z = z.resize((z.width * 2, z.height * 2), Image.LANCZOS)
        zooms.append(z)
    pw = sum(p.width for p in panels) + 10 * (len(panels) - 1)
    zw = sum(z.width for z in zooms) + 10 * (len(zooms) - 1)
    W = max(pw, zw)
    H = max(p.height for p in panels) + 10 + max(z.height for z in zooms)
    c = Image.new('RGBA', (W, H), (255, 0, 0, 255))
    x = 0
    for p in panels:
        c.alpha_composite(p, (x, 0)); x += p.width + 10
    x = 0; y = max(p.height for p in panels) + 10
    for z in zooms:
        c.alpha_composite(z, (x, y)); x += z.width + 10
    c.convert('RGB').save(out)
    print(out, c.size)
