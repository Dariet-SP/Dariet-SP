# duck.py music.wav voice.wav out.wav [bed_gain_db] [duck_db]
import sys, os, tempfile, numpy as np, soundfile as sf, subprocess
mus, voi, out = sys.argv[1:4]; bed=float(sys.argv[4]) if len(sys.argv)>4 else -4; dk=float(sys.argv[5]) if len(sys.argv)>5 else -16
TMP=os.path.join(tempfile.gettempdir(),'_duck_tmp.wav')
def load(p):
    subprocess.run(['ffmpeg','-v','error','-y','-i',p,'-ar','44100','-ac','2',TMP],check=True)
    x,_=sf.read(TMP); return x
m=load(mus); v=load(voi); n=min(len(m),len(v)); m=m[:n]; v=v[:n]; sr=44100
hop=441; e=np.sqrt(np.convolve((v.mean(1))**2,np.ones(hop)/hop,'same'))[::hop]
act=e>0.01
pre,post=int(.18*100),int(.40*100)
a2=act.copy()
for i in np.nonzero(act)[0]: a2[max(0,i-pre):i+post]=True
g_db=np.where(a2,bed+dk,bed).astype(float)
k=np.ones(9)/9; g_db=np.convolve(np.pad(g_db,4,mode='edge'),k,'valid')   # ~90 ms smoothing
g=10**(np.interp(np.arange(n)/hop,np.arange(len(g_db)),g_db)/20)
mix=v+m*g[:,None]; sf.write(out.replace('.wav','_raw.wav'),mix,sr)
sf.write(out.replace('.wav','_music.wav'),m*g[:,None],sr); sf.write(out.replace('.wav','_voice.wav'),v,sr)
subprocess.run(['ffmpeg','-v','error','-y','-i',out.replace('.wav','_raw.wav'),'-af','loudnorm=I=-14:TP=-1.5:LRA=11','-ar','44100',out],check=True)
