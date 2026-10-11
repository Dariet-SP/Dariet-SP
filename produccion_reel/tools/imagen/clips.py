import sys, glob, os
import numpy as np
from PIL import Image, ImageFilter
def polybg(a, valid):
    H,W,_=a.shape
    ys,xs=np.mgrid[0:H:4,0:W:4]; sub=a[::4,::4]; v=valid[::4,::4].copy()
    X=xs/W-0.5; Y=ys/H-0.5
    A=np.stack([np.ones_like(X),X,Y,X*X,Y*Y,X*Y,X**3,Y**3,X*X*Y,X*Y*Y],-1)
    lum=sub.mean(-1)
    v&= lum > np.percentile(lum[v],30)
    for it in range(3):
        coef=[np.linalg.lstsq(A[v],sub[...,c][v],rcond=None)[0] for c in range(3)]
        fit=np.stack([A@cf for cf in coef],-1)
        v&= np.abs(lum-fit.mean(-1)) < 0.06*fit.mean(-1)
    Y2,X2=np.mgrid[0:H,0:W]; X2=X2/W-0.5; Y2=Y2/H-0.5
    A2=np.stack([np.ones_like(X2),X2,Y2,X2*X2,Y2*Y2,X2*Y2,X2**3,Y2**3,X2*X2*Y2,X2*Y2*Y2],-1)
    return np.stack([A2@cf for cf in coef],-1)
def clean(path,out):
    im=Image.open(path).convert('RGB'); a=np.asarray(im).astype(float); H,W,_=a.shape
    wood=((a[...,0]-a[...,2])>35)&(a[...,0]>50)
    m=np.zeros((H,W),bool)
    for x in range(W):
        top=np.nonzero(wood[:int(H*.6),x])[0]
        if len(top): m[:top.max()+8,x]=True
        bot=np.nonzero(wood[int(H*.6):,x])[0]
        if len(bot): m[int(H*.6)+bot.min()-8:,x]=True
    bg=polybg(a,~m)
    C=np.array([238,242,248.]); r=a.mean(-1,keepdims=True)/np.maximum(bg.mean(-1,keepdims=True),1)
    o=(a/np.maximum(a.mean(-1,keepdims=True),1))*np.clip(r,0,2)**1.12*C
    lum=o.mean(-1,keepdims=True)/C.mean(); w=np.clip((np.abs(lum-1)-0.035)/0.06,0,1)
    o=C+w*(o-C)
    f=Image.fromarray(np.clip(o,0,255).astype('uint8'))
    mk=Image.fromarray((m*255).astype('uint8')).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(5))
    Image.composite(Image.new('RGB',im.size,(238,242,248)),f,mk).save(out,quality=92)
for c in 'B':
    for p in sorted(glob.glob(f'raw/{c}/*.png')):
        clean(p,f'assets/clip{c}/'+os.path.basename(p).replace('.png','.jpg'))
