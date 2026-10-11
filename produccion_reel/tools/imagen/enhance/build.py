"""Build final RGBA cutouts from SR image + coarse BiRefNet mask.

python build.py NAME
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import refine as R
from pymatting import estimate_foreground_ml

ROOT = './trabajo/wf_enhance'
WK = ROOT + '/work'
OUT = ROOT

CFG = {
    'inst0': dict(sr='inst0_sr_general_dn05.png', mask='inst0_mask_birefnet-general.png',
                  seeds=[(288, 1600)], rotate='vertical_left_up', out='user_inst0_v.png',
                  target=('h', 1700)),
    'inst1': dict(sr='inst1_sr_general_dn05.png', mask='inst1_mask_birefnet-general.png',
                  seeds=[(292, 1460)], rotate='vertical_left_up', out='user_inst1_v.png',
                  target=('h', 1700)),
    'detail': dict(sr='detail_sr_general_dn05.png', mask='detail_mask_birefnet-general.png',
                   seeds=[(540, 2040)], rotate=None, out='user_detail.png', target=('w', 2400)),
    'hero': dict(sr='hero_sr_general_dn05.png', mask='hero_mask_b.png',
                 seeds=[(640, 2360), (1400, 2280)], rotate=None, out='user_hero.png',
                 target=('w', 2400)),
    'head': dict(sr='head_sr_general_dn05.png', mask='head_mask_b.png',
                 seeds=[(300, 540)], rotate=None, out='user_head_macro.png', target=('w', 1400)),
}


def log(*a):
    print(*a, flush=True)


def principal_angle(a):
    ys, xs = np.nonzero(a > 0.5)
    xs = xs - xs.mean(); ys = ys - ys.mean()
    cov = np.cov(np.stack([xs, ys]))
    w, v = np.linalg.eigh(cov)
    vx, vy = v[:, -1]
    ang = np.degrees(np.arctan2(vy, vx))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    return ang  # angle of long axis w.r.t. +x, image coords (y down)


def build(name, gf_r=8, gf_eps=2e-4, erode_px=1.5, smooth=1.8, erode_lo=0.6, rim_sigma=1.3, debug=True):
    c = CFG[name]
    t0 = time.time()
    I = np.asarray(Image.open(os.path.join(WK, c['sr'])).convert('RGB'), np.float32) / 255
    m = np.asarray(Image.open(os.path.join(WK, c['mask'])).convert('L'), np.float32) / 255
    H, W = m.shape

    # 1. keep only the wanted instrument(s)
    keep = R.keep_components(m > 0.5, c['seeds'])
    region = ndi.binary_dilation(keep, iterations=24)
    m = m * region

    # 2. guided-filter refinement at 4x: snap alpha to the real image edges
    q = R.guided_filter_color(I, m, gf_r, gf_eps)
    q = np.clip(q, 0, 1) * region
    a = R.sharpen_alpha(q, 0.2, 0.8)

    # 3. fill pinholes, drop tiny islands (paper / shadow blobs)
    a = R.fill_holes_small(a, max_area=1500)
    a = R.remove_small_islands(a, min_area=4000)

    # 4. contour smoothing + sub-pixel erosion in one staircase-free step:
    #    blur the alpha and re-threshold above 0.5 -> edge moves ~1.4px inward
    #    (drops the paper fringe) and small wiggles from JPEG/SR noise vanish.
    b = ndi.gaussian_filter(a, smooth)
    a = R.sharpen_alpha(b, erode_lo, 0.97)
    log(f'  alpha done {time.time()-t0:.1f}s')

    # 5. rotation (at 4x, before downsampling)
    ang = principal_angle(a)
    rot = 0.0
    if c['rotate'] == 'vertical_left_up':
        # long axis -> vertical, with the original LEFT end on top
        # PIL rotate(deg) is counter-clockwise; image y is down so a bar at
        # angle `ang` (clockwise-positive) is levelled by rotate(ang)... then
        # rotate(-90) brings the left end to the top.
        rot = ang - 90
    if rot:
        Ii = Image.fromarray((I * 255 + 0.5).astype(np.uint8))
        Ai = Image.fromarray(a.astype(np.float32), mode='F')
        Ii = Ii.rotate(rot, resample=Image.BICUBIC, expand=True, fillcolor=(128, 128, 128))
        Ai = Ai.rotate(rot, resample=Image.BICUBIC, expand=True, fillcolor=0)
        I = np.asarray(Ii, np.float32) / 255
        a = np.clip(np.asarray(Ai, np.float32), 0, 1)
    log(f'  angle {ang:.2f} rot {rot}')

    # 6. crop to bbox with margin
    ys, xs = np.nonzero(a > 0.004)
    mg = 24
    y0, y1 = max(ys.min() - mg, 0), min(ys.max() + mg + 1, a.shape[0])
    x0, x1 = max(xs.min() - mg, 0), min(xs.max() + mg + 1, a.shape[1])
    I = I[y0:y1, x0:x1]; a = a[y0:y1, x0:x1]

    # 7. downscale to target (premultiplied-free: we resample colour & alpha
    #    separately, then decontaminate with ML foreground estimation)
    dim, val = c['target']
    s = val / (a.shape[0] if dim == 'h' else a.shape[1])
    nw, nh = int(round(a.shape[1] * s)), int(round(a.shape[0] * s))
    Ii = Image.fromarray((I * 255 + 0.5).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    Ai = Image.fromarray(a.astype(np.float32), mode='F').resize((nw, nh), Image.LANCZOS)
    Is = np.asarray(Ii, np.float64) / 255
    As = np.clip(np.asarray(Ai, np.float64), 0, 1)
    As[As < 0.003] = 0
    As[As > 0.997] = 1

    # 8. colour decontamination of edge pixels
    F = estimate_foreground_ml(Is, As)
    F = np.clip(F, 0, 1)
    # smooth the rim colour along the contour (kills SR sawtooth on dark edge lines)
    if rim_sigma > 0:
        band = (As > 0.01) & (As < 0.99)
        band = ndi.binary_dilation(band, iterations=2)
        wA = ndi.gaussian_filter(As, rim_sigma)
        Fb = np.stack([ndi.gaussian_filter(F[..., k] * As, rim_sigma) for k in range(3)], -1) / np.maximum(wA, 1e-4)[..., None]
        bw = ndi.gaussian_filter(band.astype(np.float64), 0.8)[..., None]
        F = np.clip(F * (1 - bw) + Fb * bw, 0, 1)
    rgba = np.dstack([F, As])
    out = Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), 'RGBA')
    p = os.path.join(OUT, c['out'])
    out.save(p, optimize=True)
    log(f'{name}: saved {p} {out.size} in {time.time()-t0:.1f}s (scale {s:.3f} of 4x)')
    return p


if __name__ == '__main__':
    for n in sys.argv[1:]:
        build(n)
