import sys
import numpy as np
from PIL import Image
# overlay: show image where mask, tinted magenta where bg
img, mask, out = sys.argv[1], sys.argv[2], sys.argv[3]
box = tuple(int(v) for v in sys.argv[4].split(',')) if len(sys.argv) > 4 else None
scale = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
I = np.asarray(Image.open(img).convert('RGB'), np.float32)
m = np.asarray(Image.open(mask).convert('L'), np.float32)[..., None] / 255
mag = np.array([255, 0, 200], np.float32)
o = I * m + (0.5 * I + 0.5 * mag) * (1 - m)
im = Image.fromarray(o.astype('uint8'))
if box: im = im.crop(box)
if scale != 1: im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
im.save(out)
