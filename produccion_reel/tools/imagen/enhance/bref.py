"""Lean BiRefNet-general runner (same pre/post-processing as rembg), lower memory.

usage: python bref.py in.png out_mask.png [tiles]
  tiles: optional 'tile:SIZE:OVERLAP' to run on overlapping square tiles and blend
         (higher effective mask resolution for long thin objects).
"""
import os, sys, time
import numpy as np
import onnxruntime as ort
from PIL import Image

MP = os.path.expanduser('~/.u2net/birefnet-general.onnx')


def make_session():
    so = ort.SessionOptions()
    so.enable_cpu_mem_arena = False
    so.enable_mem_pattern = False
    so.intra_op_num_threads = 4
    return ort.InferenceSession(MP, so, providers=['CPUExecutionProvider'])


def predict(sess, img):
    im = img.convert('RGB').resize((1024, 1024), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a = a / max(a.max(), 1e-6)
    mean = np.array([0.485, 0.456, 0.406], np.float32)
    std = np.array([0.229, 0.224, 0.225], np.float32)
    a = ((a - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)
    name = sess.get_inputs()[0].name
    out = sess.run(None, {name: a})[0][0, 0]
    p = 1 / (1 + np.exp(-out))
    # NOTE: no min/max renormalisation for tiles (keeps tiles comparable)
    return p


def to_size(p, size):
    m = Image.fromarray(np.clip(p, 0, 1).astype(np.float32), mode='F').resize(size, Image.BILINEAR)
    return np.asarray(m, np.float32)


def run_full(sess, img):
    p = predict(sess, img)
    p = (p - p.min()) / max(p.max() - p.min(), 1e-6)
    return to_size(p, img.size)


def run_tiles(sess, img, T, O):
    W, H = img.size
    acc = np.zeros((H, W), np.float32)
    wsum = np.zeros((H, W), np.float32)
    T = min(T, max(W, H))
    xs = list(range(0, max(W - T, 0) + 1, T - O))
    if xs[-1] + T < W:
        xs.append(W - T)
    ys = list(range(0, max(H - T, 0) + 1, T - O))
    if ys[-1] + T < H:
        ys.append(H - T)
    for y in ys:
        for x in xs:
            box = (max(x, 0), max(y, 0), min(x + T, W), min(y + T, H))
            tile = img.crop(box)
            p = to_size(predict(sess, tile), tile.size)
            th, tw = p.shape
            # feather weights so seams blend
            wy = np.minimum(np.arange(th) + 1, th - np.arange(th)).astype(np.float32)
            wx = np.minimum(np.arange(tw) + 1, tw - np.arange(tw)).astype(np.float32)
            w = np.minimum(wy[:, None], wx[None, :])
            w = np.minimum(w / (O / 2 + 1e-6), 1.0) + 1e-3
            acc[box[1]:box[3], box[0]:box[2]] += p * w
            wsum[box[1]:box[3], box[0]:box[2]] += w
            print('   tile', box, flush=True)
    return acc / np.maximum(wsum, 1e-6)


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'full'
    t = time.time()
    sess = make_session()
    img = Image.open(src).convert('RGB')
    if mode == 'full':
        p = run_full(sess, img)
    else:
        _, T, O = mode.split(':')
        p = run_tiles(sess, img, int(T), int(O))
    np.save(dst.replace('.png', '.npy'), p.astype(np.float16))
    Image.fromarray((np.clip(p, 0, 1) * 255 + 0.5).astype(np.uint8)).save(dst)
    print(src.split('/')[-1], img.size, mode, f'{time.time()-t:.1f}s', flush=True)
