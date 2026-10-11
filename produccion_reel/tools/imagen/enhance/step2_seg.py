import sys, os, time
from PIL import Image
import rembg

WK = './trabajo/wf_enhance/work'
model = sys.argv[1]
tag = sys.argv[2]
names = sys.argv[3:]
s = rembg.new_session(model)
for n in names:
    t = time.time()
    im = Image.open(os.path.join(WK, f'{n}_sr_{tag}.png')).convert('RGB')
    m = rembg.remove(im, session=s, only_mask=True)
    m.save(os.path.join(WK, f'{n}_mask_{model}.png'))
    print(n, im.size, m.size, f'{time.time()-t:.1f}s', flush=True)
