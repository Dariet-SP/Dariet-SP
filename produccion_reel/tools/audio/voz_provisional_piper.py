import sherpa_onnx, soundfile as sf, numpy as np, json, glob, difflib, unicodedata, re
d='vits-piper-es_MX-claude-high'
tts=sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=glob.glob(d+'/*.onnx')[0],tokens=d+'/tokens.txt',data_dir=d+'/espeak-ng-data',noise_scale=0.5,noise_scale_w=0.6),num_threads=4)))
w='sherpa-onnx-whisper-base/'
asr=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=w+'base-encoder.onnx',decoder=w+'base-decoder.onnx',tokens=w+'base-tokens.txt',language='es',task='transcribe')
def norm(s):
    s=unicodedata.normalize('NFD',s.lower()); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return re.sub(r'[^a-z0-9 ]','',s.replace('.',' '))
L=json.load(open('lines.json')); E=json.load(open('expect.json'))
for k,txt in L.items():
    best=None
    for i in range(8):
        a=tts.generate(txt,sid=0,speed=1.0); x=np.array(a.samples)
        s=asr.create_stream(); s.accept_waveform(a.sample_rate,x.astype('float32')); asr.decode_stream(s)
        sc=difflib.SequenceMatcher(None,norm(s.result.text),norm(E[k])).ratio()
        if best is None or sc>best[0]: best=(sc,x,a.sample_rate,s.result.text)
        if sc>0.97: break
    sc,x,sr,t=best; e=np.abs(x)>0.01; i0=np.argmax(e); j=len(x)-np.argmax(e[::-1])
    x=x[max(0,i0-int(.03*sr)):j+int(.08*sr)]; sf.write(f'vo_{k}.wav',x,sr)
    print(k, round(sc,2), round(len(x)/sr,2), '|', t)
