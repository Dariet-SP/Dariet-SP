import numpy as np, wave, json, sys
TM=json.load(open('timing.json')); D=TM['total']; L=TM['lines']
sr=44100; N=int(sr*D); t=np.arange(N)/sr; rng=np.random.default_rng(3)
out=np.zeros((N,2))
bpm=96; beat=60/bpm
S1=L[1]['start']-0.3; S6=L[6]['start']-0.3
def add(sig,i0,pan=0.5,g=1.0):
    i1=min(N,i0+len(sig)); s=sig[:i1-i0]*g; out[i0:i1,0]+=s*(1-pan)*2*0.5; out[i0:i1,1]+=s*pan*2*0.5
# kick
kt=np.arange(int(.35*sr))/sr; kick=np.sin(2*np.pi*(48+90*np.exp(-kt*30))*kt)*np.exp(-kt*9)
# hat
ht=np.arange(int(.06*sr))/sr; hat=rng.standard_normal(len(ht))*np.exp(-ht*70); hat=np.diff(hat,prepend=0)
# pulse / sub per bar
chords=[[45,57,60,64,67],[41,53,57,60,64],[43,55,59,62,67],[40,52,55,59,64]]  # Am9-F-G-Em
nb=int(D/beat)+1
for b in range(nb):
    st=b*beat; i0=int(st*sr)
    if st> D-1.2: break
    main = S1<=st<S6
    if main and b%2==0: add(kick,i0,0.5,0.55)
    if st>=S1-0.01 and st<S6: add(hat,i0+int(beat/2*sr),0.65,0.10); add(hat,i0,0.35,0.05)
    if st<S1: add(hat,i0+int(beat/2*sr),0.6,0.05)
    # bass pluck on each beat
    ch=chords[(b//4)%4]; f=440*2**((ch[0]-69)/12); bt=np.arange(int(beat*sr))/sr
    bass=(np.sin(2*np.pi*f*bt)+.3*np.sin(2*np.pi*2*f*bt))*np.exp(-bt*3.5)*(0.28 if main else 0.12)
    add(bass,i0,0.5,1)
# pads per bar (4 beats)
for bar in range(int(D/(4*beat))+1):
    st=bar*4*beat; ch=chords[bar%4]; i0=int(st*sr); n=int(4*beat*sr*1.15)
    pt=np.arange(n)/sr; env=np.clip(pt/0.6,0,1)*np.clip((4*beat*1.15-pt)/0.8,0,1)
    for m in ch[1:]:
        f=440*2**((m-69)/12)
        for det,pan in ((-.15,.25),(.15,.75)):
            add(np.sin(2*np.pi*(f+det)*pt+rng.random()*6)*env*0.045,i0,pan,1)
# arp pluck sparkle in main section
for b in range(nb*2):
    st=b*beat/2
    if not (S1<=st<S6) or st>D-1: continue
    ch=chords[(int(st/beat)//4)%4]; m=ch[1+(b%4)]+12; f=440*2**((m-69)/12)
    at=np.arange(int(.5*sr))/sr; s=np.sin(2*np.pi*f*at)*np.exp(-at*7)*0.05
    add(s,int(st*sr),0.3+0.4*(b%2),1)
# riser into reveal and final hit
rt=np.arange(int(1.2*sr))/sr; riser=rng.standard_normal(len(rt))*(rt/1.2)**2*0.06
add(riser,int((S1-1.2)*sr),0.5,1)
for st in (S1,S6):
    ct=np.arange(int(2.5*sr))/sr; boom=np.sin(2*np.pi*(40+40*np.exp(-ct*8))*ct)*np.exp(-ct*2.2)*0.5
    add(boom,int(st*sr),0.5,1)
# reverb
def rev(x,seed):
    r=np.random.default_rng(seed); n=int(sr*2.4); ir=r.standard_normal(n)*np.exp(-np.arange(n)/sr/0.55); ir/=np.sqrt((ir**2).sum())
    F=1<<int(np.ceil(np.log2(len(x)+n))); return np.fft.irfft(np.fft.rfft(x,F)*np.fft.rfft(ir,F),F)[:len(x)]
for c in range(2): out[:,c]=0.8*out[:,c]+0.35*rev(out[:,c],c+7)
fade=np.clip((D-t)/2.0,0,1)*np.clip(t/0.3,0,1); out*=fade[:,None]
out*=0.75/np.abs(out).max()
w=wave.open('music2.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out*32767).astype('<i2').tobytes()); w.close()
