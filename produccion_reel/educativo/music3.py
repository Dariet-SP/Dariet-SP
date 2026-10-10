import numpy as np, wave, sys
D=float(sys.argv[1]) if len(sys.argv)>1 else 36.2
PRICE=30.15; END=32.1; MAIN=10.4
sr=44100; N=int(sr*D); t=np.arange(N)/sr; rng=np.random.default_rng(5)
out=np.zeros((N,2)); bpm=88; beat=60/bpm
def add(sig,i0,pan=.5,g=1.):
    if i0>=N: return
    i1=min(N,i0+len(sig)); s=sig[:i1-i0]*g; out[i0:i1,0]+=s*(1-pan); out[i0:i1,1]+=s*pan
hz=lambda m:440*2**((m-69)/12)
chords=[[48,60,64,67,71],[45,57,60,64,67],[41,57,60,64,69],[43,55,59,62,67]]  # Cmaj7 Am7 Fmaj7 G
bar=4*beat
for b in range(int(D/bar)+2):
    st=b*bar; ch=chords[b%4]; n=int(bar*1.2*sr); pt=np.arange(n)/sr
    env=np.clip(pt/0.9,0,1)*np.clip((bar*1.2-pt)/1.0,0,1)
    for m in ch[1:]:
        for det,pan in((-.12,.3),(.12,.7)):
            add((np.sin(2*np.pi*(hz(m)+det)*pt+rng.random()*6)+.15*np.sin(4*np.pi*(hz(m)+det)*pt))*env*.04,int(st*sr),pan)
    f=hz(ch[0]-12); add(np.sin(2*np.pi*f*pt)*env*.07,int(st*sr))
# soft pulse (felt-piano like) on beats, gentle before MAIN, fuller after
for k in range(int(D/beat)+1):
    st=k*beat; ch=chords[int(st/bar)%4]; m=ch[1+(k%4)]+12; at=np.arange(int(.9*sr))/sr
    s=(np.sin(2*np.pi*hz(m)*at)+.3*np.sin(4*np.pi*hz(m)*at)*np.exp(-at*6))*np.exp(-at*4.5)
    add(s,int(st*sr),.35+.3*(k%2),.035 if st<MAIN else .055)
    if st>=MAIN and st<END:
        kt=np.arange(int(.25*sr))/sr; kick=np.sin(2*np.pi*(45+50*np.exp(-kt*25))*kt)*np.exp(-kt*10)
        if k%2==0: add(kick,int(st*sr),.5,.25)
        ht=np.arange(int(.05*sr))/sr; hat=np.diff(rng.standard_normal(len(ht)),prepend=0)*np.exp(-ht*80)
        add(hat,int((st+beat/2)*sr),.6,.035)
# price shimmer: rising sparkle + bell cluster + sub swell
for i,m in enumerate([84,88,91,96]):
    at=np.arange(int(2.0*sr))/sr; s=np.sin(2*np.pi*hz(m)*at)*np.exp(-at*1.6)*np.clip(at/.005,0,1)
    add(s,int((PRICE+i*.06)*sr),.3+.13*i,.06)
rt=np.arange(int(.8*sr))/sr; sw=rng.standard_normal(len(rt))*(rt/.8)**2*.03; add(np.diff(sw,prepend=0),int((PRICE-.8)*sr))
ct=np.arange(int(2.2*sr))/sr; add(np.sin(2*np.pi*(42+30*np.exp(-ct*7))*ct)*np.exp(-ct*2)*.35,int(PRICE*sr))
add(np.sin(2*np.pi*(40+30*np.exp(-ct*7))*ct)*np.exp(-ct*2)*.3,int(END*sr))
def rev(x,seed):
    r=np.random.default_rng(seed); n=int(sr*2.6); ir=r.standard_normal(n)*np.exp(-np.arange(n)/sr/.7); ir/=np.sqrt((ir**2).sum())
    F=1<<int(np.ceil(np.log2(len(x)+n))); return np.fft.irfft(np.fft.rfft(x,F)*np.fft.rfft(ir,F),F)[:len(x)]
for c in range(2): out[:,c]=.8*out[:,c]+.4*rev(out[:,c],c+11)
out*=(np.clip((D-t)/2.2,0,1)*np.clip(t/.4,0,1))[:,None]; out*=.75/np.abs(out).max()
w=wave.open('music3.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out*32767).astype('<i2').tobytes()); w.close()
