"""Torch-free conversion of Real-ESRGAN .pth checkpoints to ONNX.

Reads the zip-format torch checkpoint with a restricted unpickler (only the
handful of torch rebuild functions needed), then builds the network graph
(RRDBNet for RealESRGAN_x4plus, SRVGGNetCompact for realesr-general-x4v3)
with onnx.helper.
"""
import sys, zipfile, pickle, collections
import numpy as np
import onnx
from onnx import helper, TensorProto, numpy_helper

DT = {
    'FloatStorage': np.float32, 'HalfStorage': np.float16,
    'DoubleStorage': np.float64, 'LongStorage': np.int64, 'IntStorage': np.int32,
}


class _Storage:
    def __init__(self, name):
        self.name = name


def load_pth(path):
    zf = zipfile.ZipFile(path)
    names = zf.namelist()
    pkl = [n for n in names if n.endswith('data.pkl')][0]
    prefix = pkl[:-len('data.pkl')]

    def rebuild_tensor_v2(storage, offset, size, stride, *args):
        dtype, key = storage
        raw = zf.read(prefix + 'data/' + key)
        arr = np.frombuffer(raw, dtype=dtype)
        n = int(np.prod(size)) if len(size) else 1
        if len(size) == 0:
            return arr[offset:offset + 1].reshape(()).copy()
        itemsize = arr.itemsize
        out = np.lib.stride_tricks.as_strided(
            arr[offset:], shape=tuple(size), strides=tuple(s * itemsize for s in stride))
        return np.ascontiguousarray(out).copy()

    class U(pickle.Unpickler):
        def find_class(self, mod, name):
            if mod == 'torch._utils' and name == '_rebuild_tensor_v2':
                return rebuild_tensor_v2
            if mod == 'torch' and name in DT:
                return _Storage(name)
            if mod == 'collections' and name == 'OrderedDict':
                return collections.OrderedDict
            raise pickle.UnpicklingError(f'blocked {mod}.{name}')

        def persistent_load(self, pid):
            # ('storage', storage_type, key, location, numel)
            typ, st, key, loc, numel = pid
            return (DT[st.name], key)

    with zf.open(pkl) as f:
        obj = U(f).load()
    return obj


class G:
    def __init__(self, sd):
        self.sd = sd
        self.nodes = []
        self.inits = []
        self.k = 0
        self.used = set()

    def name(self, p='t'):
        self.k += 1
        return f'{p}{self.k}'

    def const(self, arr, nm=None):
        nm = nm or self.name('c')
        self.inits.append(numpy_helper.from_array(np.asarray(arr), nm))
        return nm

    def conv(self, x, key, pad=1):
        w = self.sd[key + '.weight'].astype(np.float32)
        b = self.sd[key + '.bias'].astype(np.float32)
        self.used.update([key + '.weight', key + '.bias'])
        wn = self.const(w, key + '.weight')
        bn = self.const(b, key + '.bias')
        y = self.name()
        k = w.shape[2]
        self.nodes.append(helper.make_node('Conv', [x, wn, bn], [y], pads=[k // 2] * 4,
                                           kernel_shape=[k, k]))
        return y

    def lrelu(self, x, a=0.2):
        y = self.name()
        self.nodes.append(helper.make_node('LeakyRelu', [x], [y], alpha=a))
        return y

    def prelu(self, x, key):
        w = self.sd[key + '.weight'].astype(np.float32).reshape(-1, 1, 1)
        self.used.add(key + '.weight')
        wn = self.const(w, key + '.weight')
        y = self.name()
        self.nodes.append(helper.make_node('PRelu', [x, wn], [y]))
        return y

    def op(self, t, ins, **kw):
        y = self.name()
        self.nodes.append(helper.make_node(t, ins, [y], **kw))
        return y

    def scale(self, x, s):
        return self.op('Mul', [x, self.const(np.array(s, np.float32))])

    def up_nearest(self, x, f):
        sc = self.const(np.array([1, 1, f, f], np.float32))
        return self.op('Resize', [x, '', sc], mode='nearest',
                       coordinate_transformation_mode='asymmetric', nearest_mode='floor')


def build_rrdb(sd, nb=23):
    g = G(sd)
    x = 'input'
    fea = g.conv(x, 'conv_first')
    body = fea
    for i in range(nb):
        rin = body
        h = rin
        for r in (1, 2, 3):
            pre = f'body.{i}.rdb{r}'
            feats = [h]
            for c in range(1, 5):
                cat = g.op('Concat', feats, axis=1) if len(feats) > 1 else feats[0]
                feats.append(g.lrelu(g.conv(cat, f'{pre}.conv{c}')))
            cat = g.op('Concat', feats, axis=1)
            x5 = g.conv(cat, f'{pre}.conv5')
            h = g.op('Add', [g.scale(x5, 0.2), h])
        body = g.op('Add', [g.scale(h, 0.2), rin])
    body = g.conv(body, 'conv_body')
    fea = g.op('Add', [fea, body])
    fea = g.lrelu(g.conv(g.up_nearest(fea, 2), 'conv_up1'))
    fea = g.lrelu(g.conv(g.up_nearest(fea, 2), 'conv_up2'))
    out = g.conv(g.lrelu(g.conv(fea, 'conv_hr')), 'conv_last')
    return g, out


def build_srvgg(sd, upscale=4):
    g = G(sd)
    x = 'input'
    idx = sorted({int(k.split('.')[1]) for k in sd if k.startswith('body.')})
    h = x
    for i in idx:
        k = f'body.{i}'
        w = sd[k + '.weight']
        if w.ndim == 4:
            h = g.conv(h, k)
        else:
            h = g.prelu(h, k)
    h = g.op('DepthToSpace', [h], blocksize=upscale, mode='CRD')
    base = g.up_nearest(x, upscale)
    out = g.op('Add', [h, base])
    return g, out


def main(src, dst, kind):
    ck = load_pth(src)
    sd = ck.get('params_ema') or ck.get('params') or ck
    if kind == 'rrdb':
        g, out = build_rrdb(sd)
    else:
        g, out = build_srvgg(sd)
    missing = set(sd) - g.used
    if missing:
        print('UNUSED keys:', sorted(missing)[:10])
    g.nodes.append(helper.make_node('Identity', [out], ['output']))
    graph = helper.make_graph(
        g.nodes, 'sr',
        [helper.make_tensor_value_info('input', TensorProto.FLOAT, [1, 3, 'h', 'w'])],
        [helper.make_tensor_value_info('output', TensorProto.FLOAT, [1, 3, 'H', 'W'])],
        g.inits)
    m = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 17)])
    m.ir_version = 8
    onnx.checker.check_model(m)
    onnx.save(m, dst)
    print('saved', dst, len(g.nodes), 'nodes')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
