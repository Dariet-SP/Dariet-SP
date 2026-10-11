import numpy as np
from PIL import Image, ImageFilter, ImageDraw
C=np.array([238,242,248.])
def flatfield(im, k=4, gain=1.0):
    im = im.convert('RGB'); W,H = im.size
    small = im.resize((W//4, H//4), Image.BILINEAR)
    for _ in range(k): small = small.filter(ImageFilter.MaxFilter(9))
    small = small.filter(ImageFilter.GaussianBlur(8))
    bg = np.asarray(small.resize((W,H), Image.BILINEAR)).astype(float)
    a = np.asarray(im).astype(float)
    # use luminance of bg so color cast of paper also neutralised
    r = a.mean(-1,keepdims=True) / np.maximum(bg.mean(-1,keepdims=True), 1)
    o = (a/np.maximum(a.mean(-1,keepdims=True),1)) * r**1.12 * C
    return Image.fromarray(np.clip(o,0,255).astype('uint8'))
def whiten_poly(im, poly):
    im = im.copy(); d = ImageDraw.Draw(im); d.polygon(poly, fill=(238,242,248)); return im
