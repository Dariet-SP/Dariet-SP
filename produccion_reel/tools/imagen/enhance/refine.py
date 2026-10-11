"""Alpha refinement helpers: background field, guided filter, carving, decontamination."""
import numpy as np
from scipy import ndimage as ndi


def box(x, r):
    return ndi.uniform_filter(x, size=2 * r + 1, mode='reflect')


def guided_filter_color(I, p, r, eps):
    """He et al. guided filter with a colour guide I (H,W,3) and input p (H,W)."""
    I = I.astype(np.float32); p = p.astype(np.float32)
    mean_I = np.stack([box(I[..., c], r) for c in range(3)], -1)
    mean_p = box(p, r)
    mean_Ip = np.stack([box(I[..., c] * p, r) for c in range(3)], -1)
    cov_Ip = mean_Ip - mean_I * mean_p[..., None]
    # covariance matrix of I
    S = np.zeros(I.shape[:2] + (3, 3), np.float32)
    for i in range(3):
        for j in range(i, 3):
            v = box(I[..., i] * I[..., j], r) - mean_I[..., i] * mean_I[..., j]
            S[..., i, j] = v; S[..., j, i] = v
    S += eps * np.eye(3, dtype=np.float32)
    a = np.linalg.solve(S, cov_Ip[..., None])[..., 0]
    b = mean_p - (a * mean_I).sum(-1)
    mean_a = np.stack([box(a[..., c], r) for c in range(3)], -1)
    mean_b = box(b, r)
    return (mean_a * I).sum(-1) + mean_b


def bg_field(I, m, sigma=30, thr=0.03, grow=6):
    """Estimate the paper colour behind the object by normalised convolution."""
    known = ndi.binary_erosion(m < thr, iterations=grow)
    w = known.astype(np.float32)
    out = np.zeros_like(I)
    den = ndi.gaussian_filter(w, sigma)
    for c in range(3):
        out[..., c] = ndi.gaussian_filter(I[..., c] * w, sigma)
    B = out / np.maximum(den, 1e-6)[..., None]
    # fill holes where den tiny with a much larger blur
    bad = den < 1e-3
    if bad.any():
        den2 = ndi.gaussian_filter(w, sigma * 4)
        for c in range(3):
            B[..., c][bad] = (ndi.gaussian_filter(I[..., c] * w, sigma * 4) / np.maximum(den2, 1e-6))[bad]
    return B, known


def keep_components(mask_bool, seeds):
    lab, n = ndi.label(mask_bool, structure=np.ones((3, 3)))
    keep = np.zeros(n + 1, bool)
    for (y, x) in seeds:
        keep[lab[y, x]] = True
    keep[0] = False
    return keep[lab]


def carve_paper(I, m, B, zones, dthr=0.07, border=True):
    """Remove paper-coloured regions inside the coarse mask that are connected
    to known background or the image border, restricted to zones (list of boxes)."""
    D = np.sqrt(((I - B) ** 2).sum(-1))
    paper = D < dthr
    zone = np.zeros(m.shape, bool)
    for (x0, y0, x1, y1) in zones:
        zone[y0:y1, x0:x1] = True
    cand = paper & zone
    bgc = (m < 0.1)
    lab, n = ndi.label(cand | (bgc & zone), structure=np.ones((3, 3)))
    touch = np.zeros(n + 1, bool)
    touch[np.unique(lab[bgc & zone])] = True
    if border:
        for edge in (lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]):
            touch[np.unique(edge)] = True
    touch[0] = False
    carved = touch[lab] & cand & (m >= 0.1)
    return carved, D


def sharpen_alpha(q, lo=0.25, hi=0.75):
    t = np.clip((q - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def fill_holes_small(a, max_area):
    """close tiny transparent pinholes fully enclosed by the object"""
    hole = a < 0.5
    lab, n = ndi.label(hole)
    if n == 0:
        return a
    sizes = ndi.sum(np.ones_like(a), lab, index=np.arange(1, n + 1))
    border_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    small = np.zeros(n + 1, bool)
    for i, s in enumerate(sizes, 1):
        if s < max_area and i not in border_labels:
            small[i] = True
    out = a.copy()
    out[small[lab]] = 1.0
    return out


def remove_small_islands(a, min_area):
    fg = a > 0.5
    lab, n = ndi.label(fg, structure=np.ones((3, 3)))
    if n <= 1:
        return a
    sizes = ndi.sum(np.ones_like(a), lab, index=np.arange(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1:] = sizes >= min_area
    region = ndi.binary_dilation(keep[lab], iterations=3)
    return a * region
