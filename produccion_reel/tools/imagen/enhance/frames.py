import sys
sys.path.insert(0, sys.argv[1] + '/tools')
from preview import gradient
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
W = sys.argv[1]; V = sys.argv[2]

def frame(f, left, top, w, h):
    bg = gradient(1080, 1920)
    im = Image.open(f).convert('RGBA')
    if w == 0: w = int(round(im.width * h / im.height))
    if h == 0: h = int(round(im.height * w / im.width))
    obj = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(obj)[..., 3].astype(np.float32) / 255
    P = 200
    sh = np.zeros((1920 + 2 * P + 3000, 1080 + 2 * P + 3000), np.float32)
    sh[top + P + 30:top + P + 30 + h, left + P:left + P + w] = a * 0.55
    sh = Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(20)).crop((P, P, P + 1080, P + 1920))
    s = Image.new('RGBA', (1080, 1920), (8, 24, 60, 0)); s.putalpha(sh)
    bg.alpha_composite(s)
    big = Image.new('RGBA', (1080 + 2 * P + 3000, 1920 + 2 * P + 3000), (0, 0, 0, 0))
    big.alpha_composite(obj, (left + P, top + P))
    bg.alpha_composite(big.crop((P, P, P + 1080, P + 1920)))
    return bg.convert('RGB')

scenes = [
    ('detail', ('user_detail.png', 185, 594, 2226, 0), (V + '/detail_x.png', 185, 594, 2226, 486)),
    ('inst0', ('user_inst0_v.png', 446, 190, 0, 1546), (V + '/inst0_v_x.png', 426, 190, 228, 1546)),
    ('inst1', ('user_inst1_v.png', 440, 230, 0, 1474), (V + '/inst1_v_x.png', 420, 230, 240, 1474)),
    ('hero', ('user_hero.png', -5, 230, 1091, 0), (V + '/hero_x.png', -5, 230, 1091, 478)),
]
for name, new, old in scenes:
    a = frame(W + '/' + new[0], *new[1:]); b = frame(old[0], *old[1:])
    c = Image.new('RGB', (2170, 1920), 'red'); c.paste(a, (0, 0)); c.paste(b, (1090, 0))
    d = ImageDraw.Draw(c); d.text((20, 20), 'NEW (user photo, Real-ESRGAN + BiRefNet)', fill='white'); d.text((1110, 20), 'OLD cutout', fill='white')
    c.save(W + f'/previews/frame_{name}_new_vs_old.png')
# all-in-one side by side (half-size frames)
ims = [Image.open(W + f'/previews/frame_{n}_new_vs_old.png').resize((1085, 960), Image.LANCZOS) for n, _, _ in scenes]
o = Image.new('RGB', (1085 * 2 + 10, 960 * 2 + 10), 'red')
for i, im in enumerate(ims):
    o.paste(im, ((i % 2) * 1095, (i // 2) * 970))
o.save(W + '/previews/ALL_new_vs_old.png')
print('ok')
