import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import sr

I = './fotos_originales'
WK = './trabajo/wf_enhance/work'

JOBS = {
    # name: (photo, crop box)
    'inst0': ('3.jpg', (110, 465, 900, 620)),
    'inst1': ('3.jpg', (120, 585, 900, 732)),
    'detail': ('2.jpg', (150, 690, 1200, 950)),
    'hero': ('1.jpg', (60, 280, 1200, 800)),
    'head': ('2.jpg', (165, 785, 610, 955)),
}

model = sys.argv[1] if len(sys.argv) > 1 else 'general_dn05'
which = sys.argv[2:] or list(JOBS)
for n in which:
    ph, box = JOBS[n]
    crop = Image.open(os.path.join(I, ph)).convert('RGB').crop(box)
    crop.save(os.path.join(WK, f'{n}_src.png'))
    out = sr.upscale(crop, model)
    out.save(os.path.join(WK, f'{n}_sr_{model}.png'))
    print(n, crop.size, '->', out.size, flush=True)
