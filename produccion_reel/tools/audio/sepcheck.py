import soundfile as sf, numpy as np, sys
v,sr=sf.read(sys.argv[1]); m,_=sf.read(sys.argv[2])
v=v.mean(1) if v.ndim>1 else v; m=m.mean(1) if m.ndim>1 else m
n=int(.4*sr); d=[]
from numpy.fft import rfft, rfftfreq
f=rfftfreq(n,1/sr); band=(f>300)&(f<4000)
for i in range(0,min(len(v),len(m))-n,n):
    a=v[i:i+n]; b=m[i:i+n]
    if np.sqrt((a**2).mean())<0.02: continue
    A=(np.abs(rfft(a))[band]**2).sum(); B=(np.abs(rfft(b))[band]**2).sum()+1e-12
    ra=20*np.log10(np.sqrt((a**2).mean())); rb=20*np.log10(np.sqrt((b**2).mean())+1e-9)
    d.append((ra-rb,10*np.log10(A/B)))
d=np.array(d); print('speech windows',len(d),'| broadband voice-music dB: median %.1f p10 %.1f | speech-band: median %.1f p10 %.1f'%(np.median(d[:,0]),np.percentile(d[:,0],10),np.median(d[:,1]),np.percentile(d[:,1],10)))
