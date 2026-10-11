"""Tiled x4 super-resolution with the converted Real-ESRGAN ONNX models."""
import os, sys, time
import numpy as np
import onnxruntime as ort
from PIL import Image

MD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
_sess = {}


def session(name):
    if name not in _sess:
        so = ort.SessionOptions()
        so.intra_op_num_threads = os.cpu_count()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _sess[name] = ort.InferenceSession(os.path.join(MD, name + '.onnx'), so,
                                           providers=['CPUExecutionProvider'])
    return _sess[name]


def upscale(img, model='x4plus', tile=256, pad=16, scale=4):
    """img: PIL RGB. returns PIL RGB x4."""
    s = session(model)
    a = np.asarray(img.convert('RGB'), np.float32) / 255.0
    H, W, _ = a.shape
    # reflect-pad the whole image so tiles at borders have context
    ap = np.pad(a, ((pad, pad), (pad, pad), (0, 0)), mode='reflect')
    out = np.zeros((H * scale, W * scale, 3), np.float32)
    t0 = time.time()
    for y in range(0, H, tile):
        for x in range(0, W, tile):
            h = min(tile, H - y); w = min(tile, W - x)
            patch = ap[y:y + h + 2 * pad, x:x + w + 2 * pad]
            inp = patch.transpose(2, 0, 1)[None].copy()
            res = s.run(None, {'input': inp})[0][0].transpose(1, 2, 0)
            out[y * scale:(y + h) * scale, x * scale:(x + w) * scale] = \
                res[pad * scale:(pad + h) * scale, pad * scale:(pad + w) * scale]
    print(f'  SR {model} {W}x{H} -> {W*scale}x{H*scale} in {time.time()-t0:.1f}s', flush=True)
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


if __name__ == '__main__':
    src, dst, model = sys.argv[1], sys.argv[2], sys.argv[3]
    upscale(Image.open(src), model).save(dst)
