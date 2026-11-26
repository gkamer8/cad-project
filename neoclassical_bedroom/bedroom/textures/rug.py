"""Procedural artwork for the Aubusson-style rug (R-1): crimson field, Greek-key border,
laurel medallion, corner spandrels and a gilt diaper of rosettes.

Image u runs along the rug length (room x), v along its width (room y).
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PX_PER_IN = 20
SS = 2  # supersampling factor
LENGTH_IN, WIDTH_IN = 120, 96

CRIMSON = (132, 22, 30)
DEEP = (96, 14, 22)
IVORY = (226, 212, 186)
GOLD = (190, 148, 72)
BLACK = (30, 20, 18)

KEY_HOOK = [(0, 0), (0, 4), (3, 4), (3, 1), (1, 1), (1, 3), (2, 3)]  # Greek-key hook, grid units


def _p(inches: float) -> int:
    return int(round(inches * PX_PER_IN * SS))


def _leaf(cx: float, cy: float, length: float, width: float, angle: float) -> list:
    t = np.linspace(0, np.pi, 12)
    half = np.c_[length / 2 * np.cos(t), width / 2 * np.sin(t)]
    pts = np.vstack([half, half[::-1] * [1, -1]])
    rot = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    return [tuple(p) for p in pts @ rot.T + [cx, cy]]


def _rosette(d: ImageDraw.ImageDraw, cx, cy, radius, petals: int, fill, eye):
    for k in range(petals):
        a = 2 * np.pi * k / petals
        d.polygon(_leaf(cx + radius * 0.5 * np.cos(a), cy + radius * 0.5 * np.sin(a), radius, radius * 0.42, a),
                  fill=fill)
    d.ellipse([cx - radius * 0.22, cy - radius * 0.22, cx + radius * 0.22, cy + radius * 0.22], fill=eye)


def _laurel_ring(d, cx, cy, radius, count: int, size, fill, arc: tuple[float, float]):
    """Pairs of laurel leaves along an arc (radians), each pair splayed off the stem."""
    for a in np.linspace(arc[0], arc[1], count):
        for side in (-1, 1):
            spread = a + side * 0.09
            x, y = cx + (radius + side * size * 0.28) * np.cos(spread), cy + (radius + side * size * 0.28) * np.sin(spread)
            d.polygon(_leaf(x, y, size, size * 0.36, a + np.pi / 2 + side * 0.5), fill=fill)


def _key_run(d, x0, y0, length, unit, stroke, horizontal: bool, fill):
    """Greek-key hooks along a straight band starting at (x0, y0)."""
    periods = int(length // (4 * unit))
    start = (length - periods * 4 * unit) / 2
    for k in range(periods):
        base = start + k * 4 * unit
        pts = [(base + gx * unit, gy * unit) for gx, gy in KEY_HOOK]
        pts = [(x0 + a, y0 + b) if horizontal else (x0 + b, y0 + a) for a, b in pts]
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            d.rectangle([min(ax, bx) - stroke / 2, min(ay, by) - stroke / 2,
                         max(ax, bx) + stroke / 2, max(ay, by) + stroke / 2], fill=fill)


def _frame(d, inset, width_px, fill, w, h):
    d.rectangle([inset, inset, w - inset, h - inset], outline=fill, width=width_px)


def draw_rug(path: Path) -> None:
    w, h = _p(LENGTH_IN), _p(WIDTH_IN)
    img = Image.new("RGB", (w, h), CRIMSON)
    d = ImageDraw.Draw(img)
    # borders, outside in
    d.rectangle([0, 0, w, h], fill=IVORY)
    _frame(d, _p(1.2), _p(0.35), BLACK, w, h)
    border_in, border_out = _p(11.0), _p(1.8)
    d.rectangle([border_in, border_in, w - border_in, h - border_in], fill=CRIMSON)
    _frame(d, border_in - _p(0.9), _p(0.6), GOLD, w, h)
    _frame(d, border_in - _p(1.6), _p(0.25), BLACK, w, h)
    unit, stroke = _p(1.45), _p(0.55)
    band = 5 * unit
    y_top = border_out + (border_in - _p(1.6) - border_out - band) / 2 + unit / 2
    corner = border_in
    for horizontal, length, origins in (
        (True, w - 2 * corner, [(corner, y_top), (corner, h - y_top - 4 * unit)]),
        (False, h - 2 * corner, [(y_top, corner), (w - y_top - 4 * unit, corner)]),
    ):
        for x0, y0 in origins:
            _key_run(d, x0, y0, length, unit, stroke, horizontal, CRIMSON)
    c = (corner + border_out) / 2
    for sx, sy in ((c, c), (w - c, c), (c, h - c), (w - c, h - c)):
        _rosette(d, sx, sy, _p(3.2), 8, CRIMSON, GOLD)
    # field: inner gilt frame, diaper of rosettes, corner spandrels, central medallion
    _frame(d, border_in + _p(4.0), _p(0.3), GOLD, w, h)
    rng = np.random.default_rng(7)
    step = _p(8.0)
    lattice = [(x, y)
               for i, x in enumerate(np.arange(border_in + _p(10), w - border_in - _p(6), step))
               for y in np.arange(border_in + _p(10) + (i % 2) * step / 2, h - border_in - _p(6), step)]
    for x, y in lattice:
        outside_medallion = ((x - w / 2) / _p(26)) ** 2 + ((y - h / 2) / _p(22)) ** 2 > 1.0
        outside_spandrels = min(np.hypot(x - sx, y - sy) for sx in (border_in, w - border_in)
                                for sy in (border_in, h - border_in)) > _p(15.5)
        if outside_medallion and outside_spandrels:
            _rosette(d, x, y, _p(1.1), 4, GOLD, DEEP)
    for sx, sy, a0 in ((border_in, border_in, 0), (w - border_in, border_in, 90),
                       (w - border_in, h - border_in, 180), (border_in, h - border_in, 270)):
        r = _p(14)
        d.pieslice([sx - r, sy - r, sx + r, sy + r], a0, a0 + 90, fill=DEEP, outline=GOLD, width=_p(0.4))
        _laurel_ring(d, sx, sy, r * 0.7, 9, _p(2.0), GOLD, (np.radians(a0 + 8), np.radians(a0 + 82)))
    cx, cy = w / 2, h / 2
    for radius, fill in ((_p(21), GOLD), (_p(20.4), DEEP), (_p(16.2), GOLD), (_p(15.7), CRIMSON)):
        d.ellipse([cx - radius * 1.25, cy - radius, cx + radius * 1.25, cy + radius], fill=fill)
    ring = Image.new("L", img.size, 0)
    _laurel_ring(ImageDraw.Draw(ring), cx, cy, _p(18.3), 44, _p(2.3), 255, (0, 2 * np.pi))
    ring = ring.transform(img.size, Image.AFFINE, (1 / 1.25, 0, cx - cx / 1.25, 0, 1, 0))
    img.paste(GOLD, mask=ring)
    _rosette(d, cx, cy, _p(10.0), 16, GOLD, GOLD)
    _rosette(d, cx, cy, _p(7.5), 12, IVORY, GOLD)
    _rosette(d, cx, cy, _p(3.6), 8, GOLD, CRIMSON)
    for k in range(4):
        a = np.pi / 2 * k
        _rosette(d, cx + _p(12.5) * 1.25 * np.cos(a), cy + _p(12.5) * np.sin(a), _p(2.2), 6, GOLD, CRIMSON)
    # wool character: abrash (slow tone drift), fibre noise, slight softening
    small = img.resize((w // SS, h // SS), Image.LANCZOS)
    arr = np.asarray(small).astype(float)
    yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]
    abrash = 1.0 + 0.05 * np.sin(xx / 140.0 + 1.3) * np.sin(yy / 210.0) + 0.03 * np.sin(xx / 37.0 + yy / 53.0)
    fibre = 1.0 + rng.normal(0.0, 0.045, arr.shape[:2])
    arr = np.clip(arr * (abrash * fibre)[..., None], 0, 255).astype(np.uint8)
    out = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(0.7))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)
