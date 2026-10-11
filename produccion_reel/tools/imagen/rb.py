import sys, numpy as np
from PIL import Image
from rembg import new_session, remove
s=new_session(sys.argv[1])
for src,dst in zip(sys.argv[2::2],sys.argv[3::2]):
    im=Image.open(src).convert('RGB')
    m=remove(im,session=s,only_mask=True,post_process_mask=True)
    o=im.copy(); o.putalpha(m); o.save(dst)
