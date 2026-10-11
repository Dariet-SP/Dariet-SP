import sherpa_onnx, soundfile as sf, sys, glob, numpy as np
d='sherpa-onnx-whisper-base/'
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=d+'base-encoder.int8.onnx',decoder=d+'base-decoder.int8.onnx',tokens=d+'base-tokens.txt',language='es',task='transcribe')
for f in sorted(glob.glob(sys.argv[1]+'_s*.wav')):
    a,sr=sf.read(f,dtype='float32'); s=r.create_stream(); s.accept_waveform(sr,a); r.decode_stream(s); print(f.split('_')[-1], s.result.text)
