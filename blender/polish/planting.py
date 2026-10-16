"""Dense tropical planting: ti plants, crotons, giant bird-of-paradise, clumping palms, ferns.

Replaces the base model's sparse placed shrubs ("shrub_*" in Landscape) with procedural plants
built from a generated leaf atlas (alpha-clipped cards, Principled BSDF + image texture, so
everything exports to glTF).  Each plant kind has a few variants; placements are linked
duplicates (shared mesh data) to keep the triangle count down.

Video evidence (frames/exterior/):
- 05_front-facade-day, 06_front-facade-dusk: red-mulch strip between the sidewalk and the low
  white front wall, a row of red / burgundy ti plants (Cordyline) alternating with green clumps
  (Philodendron 'Xanadu', ginger, ferns) and crotons.  Behind the stick fence: clumping areca
  palms and a giant bird-of-paradise (Strelitzia nicolai) whose paddle leaves reach the tower
  porthole.
- 14_aerial-front-3-storey: that Strelitzia clump stands where the two front hip roofs meet;
  more Strelitzia beside the entry.
- 03_entry-door-planter, 07_side-garden-stone-patio: Strelitzia trunks at the entry corner, beds
  of ferns, palms and philodendron around the circular stone patio (west front garden).
- 15_top-down-site-plan-night: lit planting strips down both side yards.
- 08_courtyard-aerial-night, 09_courtyard-aerial-day-pool, 21_courtyard-aerial-angle,
  16_pool-toward-pavilion-dusk: continuous bed along the courtyard's west boundary wall
  (areca palms, Strelitzia, grasses), palms against the pavilion's solid west bay, white pots
  with Strelitzia / philodendron near the cabanas on the east side.
- 11_courtyard-pool-pavilion-day, 12_courtyard-house-rear-dusk, 13_courtyard-lounge-dusk: raised
  white planter of ferns / philodendron / Strelitzia against the rear facade east of the
  folding doors.
- 18_rooftop-lounge, 20_rooftop-spa-courtyard: roof-deck planter of grey-green olive/rosemary.
"""
import math
import random
import zlib

import bpy
import numpy as np
from mathutils import Vector

POLYHAVEN_ASSETS = []          # nothing downloaded: geometry and textures are generated here

COLL = "Landscape"
SEED = 1159

# ---- leaf atlas (generated) -------------------------------------------------------------
TILE_PX = 512
COLS, ROWS = 4, 3
CORD_RED, CORD_DARK, CROTON, PADDLE = 0, 1, 2, 3
PHILO, PALM, FERN, OLIVE = 4, 5, 6, 7
LANCE, GRASS, BANANA, STEM = 8, 9, 10, 11
TRUNK_U = (0.03, 0.47)         # STEM tile: left half fibrous strelitzia/cordyline trunk
CANE_U = (0.53, 0.97)          # STEM tile: right half ringed green palm cane
MULCH_TILE_M = 0.9             # mulch texture repeat (metres), box-projected by uv_all()

# ---- beds (x0, y0, x1, y1) metres; mulch slab top just above sidewalk / turf -------------
BED_TOP = 0.045
GATE = (2.62, 4.58)                                  # gap in the front strip for the gate pad
BEDS = {
    "front_strip_w": (0.0, -1.15, GATE[0], 0.28),     # sidewalk side of the low front wall (05/06)
    "front_strip_e": (GATE[1], -1.15, 15.3, 0.28),
    "front_fence_w": (0.05, 0.7, 2.75, 2.2),         # inside the fence, west of the path (07)
    "front_fence_e": (4.45, 0.7, 6.3, 2.2),
    "front_yard_e": (6.3, 0.7, 15.25, 3.95),         # strelitzia + palms in front of the house
    "entry_corner": (1.0, 4.95, 2.35, 6.3),          # strelitzia beside the entry porch (07)
    "side_w": (0.05, 4.95, 1.0, 18.8),               # side yards (15)
    "side_e": (14.3, 4.05, 15.25, 18.9),
    "court_w": (0.3, 21.7, 1.4, 30.95),              # in front of the courtyard's west wall
    "court_pav": (1.4, 30.2, 4.45, 30.95),           # pavilion's solid west bay (08, 21)
    "court_e": (13.9, 21.7, 15.0, 22.95),            # east wall, clear of the cabanas
}
REAR_PLANTER = dict(x0=10.6, x1=12.9, y0=19.05, y1=19.95, h=0.55, wall=0.1)  # (11, 12, 13)
POTS = [  # (x, y, plant kind, pot scale) — white pots by the cabanas / pavilion (10, 16)
    (14.55, 25.55, "strel_pot", 1.0), (14.55, 28.75, "philo", 0.85),
    (14.45, 29.75, "strel_pot", 1.1), (9.6, 30.45, "philo", 0.75),
]

# ---- hero plants (kind, x, y, rot) ------------------------------------------------------
HEROES = [
    ("strel_front", 8.0, 2.85, 0.0),     # giant Strelitzia between the front hip roofs (05, 14)
    ("strel_med", 5.95, 3.05, 1.2),      # beside the entry, right of the front door (14)
    ("strel_med", 1.75, 5.55, 0.4),      # entry-porch corner, side garden (07)
    ("areca_tall", 0.45, 1.0, 0.0),      # feathery palm clump behind the fence, far left (05)
    ("areca_low", 6.6, 1.55, 2.0),       # low palm, centre of the front yard (05)
    ("areca_mid", 10.7, 2.0, 1.0),       # ~2.5-3 m palms before the right-hand window (05, 14)
    ("areca_mid", 9.2, 1.3, 2.2), ("areca_mid", 12.6, 1.7, 0.4), ("areca_low", 13.9, 1.2, 3.0),
    ("areca_mid", 5.3, 1.5, 4.0), ("areca_tall", 14.65, 3.3, 0.5),
    ("strel_med", 14.75, 8.6, 0.0), ("areca_tall", 14.8, 12.4, 1.0), ("strel_med", 14.75, 16.6, 2.0),
    ("areca_tall", 0.5, 8.9, 2.5), ("strel_med", 0.55, 12.6, 1.0), ("areca_tall", 0.5, 16.4, 0.3),
    ("areca_tall", 0.85, 23.5, 0.0), ("strel_med", 0.8, 24.9, 1.6),   # courtyard west bed (08, 21)
    ("areca_tall", 0.85, 26.4, 2.0), ("strel_med", 0.8, 27.9, 0.3),
    ("areca_tall", 0.9, 29.25, 1.1),
    ("areca_low", 2.3, 30.5, 0.7), ("strel_med", 3.75, 30.45, 0.0),   # pavilion west bay
    ("areca_low", 14.45, 22.3, 0.2),                                    # courtyard east corner
]

# ---- filler mixes per bed: (kind, weight), spacing m ---------------------------------------
MIXES = {
    "front_fence_w": ([("fern", 3), ("philo", 2), ("brom", 2), ("cord_dark", 1)], 0.62),
    "front_fence_e": ([("philo", 3), ("fern", 2), ("ginger", 2), ("croton", 1)], 0.66),
    "front_yard_e": ([("philo", 3), ("fern", 2), ("ginger", 2), ("areca_low", 1)], 0.62),
    "entry_corner": ([("fern", 2), ("philo", 2)], 0.6),
    "side_w": ([("philo", 3), ("fern", 3), ("brom", 1), ("areca_low", 1)], 0.62),
    "side_e": ([("philo", 3), ("fern", 2), ("ginger", 1), ("areca_low", 1), ("cord_dark", 1)], 0.62),
    "court_w": ([("grass", 2), ("fern", 2), ("philo", 2), ("areca_low", 2)], 0.5),
    "court_pav": ([("fern", 2), ("philo", 2), ("grass", 1)], 0.55),
    "court_e": ([("philo", 2), ("fern", 2), ("grass", 1)], 0.55),
}
# front strip (05): front row = reds alternating with low greens, back row = taller greens
STRIP_ROWS = dict(front_y=-0.78, back_y=-0.22, step=0.6, x0=0.3, x1=15.05)
STRIP_FRONT_GREENS = [("fern", 2), ("brom", 2), ("philo", 2), ("ginger", 1), ("croton", 1)]
STRIP_BACK_GREENS = [("philo", 2), ("ginger", 3), ("brom", 1)]

# review close-ups: name -> (location, target, lens mm, matched video frame)
CLOSEUPS = {
    "plant_front": ((1.5, -9.0, 1.4), (7.5, 4.5, 3.0), 20, "exterior/05_front-facade-day.jpg"),
    "plant_strip": ((10.6, -3.4, 1.25), (7.2, 0.4, 0.55), 26, "exterior/06_front-facade-dusk.jpg"),
    "plant_side": ((3.6, -1.8, 3.2), (1.0, 4.6, 0.4), 22, "exterior/07_side-garden-stone-patio.jpg"),
    "plant_court": ((12.6, 21.2, 1.7), (4.0, 31.0, 1.3), 20, "exterior/16_pool-toward-pavilion-dusk.jpg"),
    "plant_court_aerial": ((9.0, 26.0, 11.0), (1.0, 27.4, 0.3), 26, "exterior/21_courtyard-aerial-angle.jpg"),
    "plant_rear": ((5.0, 27.0, 1.5), (12.0, 19.5, 1.2), 22, "exterior/13_courtyard-lounge-dusk.jpg"),
    "plant_roof": ((10.4, 8.4, 8.4), (10.9, 14.4, 6.7), 26, "exterior/20_rooftop-spa-courtyard.jpg"),
}

TAU = 2 * math.pi
GOLDEN = 2.39996


# =========================================================================================
# leaf shapes: half-width (fraction of the tile half-width) along the leaf, v = 0 base, 1 tip.
# Used by the texture (alpha cut-out) and, slightly enlarged, by the card geometry.
# =========================================================================================
def _ss(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _sinp(t, a, b):
    return np.clip(np.sin(np.pi * np.clip(t, 0, 1) ** a), 0, 1) ** b


def prof_strap(v):        # cordyline / ginger: short petiole then lanceolate blade
    v = np.asarray(v, float)
    return np.maximum(0.92 * _sinp((v - 0.05) / 0.95, 0.65, 0.85), 0.11 * (1 - _ss(0.08, 0.22, v)))


def prof_croton(v):
    v = np.asarray(v, float)
    return np.maximum(0.95 * _sinp((v - 0.04) / 0.96, 0.8, 0.7), 0.08 * (1 - _ss(0.06, 0.16, v)))


def prof_paddle(v):       # Strelitzia / banana: oblong with rounded ends
    t = np.clip((np.asarray(v, float) - 0.02) / 0.98, 0, 1)
    return 0.97 * np.clip(1 - np.abs(2 * t - 1) ** 4, 0, 1) ** 0.4


def prof_philo(v):        # envelope of the lobed philodendron leaf
    return 0.97 * _sinp((np.asarray(v, float) - 0.02) / 0.98, 0.55, 0.5)


def prof_frond(v):        # palm frond envelope
    return 0.12 + 0.86 * _sinp(np.asarray(v, float) * 1.02, 0.75, 0.55)


def prof_fern(v):
    return 0.10 + 0.88 * _sinp((np.asarray(v, float) - 0.03) / 0.97, 0.8, 0.7)


def prof_grass(v):
    return 0.05 + 0.92 * np.clip(1 - np.asarray(v, float) ** 4, 0, 1) ** 0.5


def prof_full(v):
    return np.ones_like(np.asarray(v, float))


TILE_PROF = {CORD_RED: prof_strap, CORD_DARK: prof_strap, CROTON: prof_croton, PADDLE: prof_paddle,
             PHILO: prof_philo, PALM: prof_frond, FERN: prof_fern, OLIVE: prof_full,
             LANCE: prof_strap, GRASS: prof_grass, BANANA: prof_paddle, STEM: prof_full}


# =========================================================================================
# texture generation (numpy)
# =========================================================================================
def _noise(rng, cx, cy, octaves=1, n=TILE_PX):
    """Smooth value noise in [0, 1] on an n x n grid with cx x cy cells (first octave)."""
    out = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    for _ in range(octaves):
        g = rng.random((cy + 1, cx + 1))
        fy = np.linspace(0, cy, n, endpoint=False)
        fx = np.linspace(0, cx, n, endpoint=False)
        iy, ix = fy.astype(int), fx.astype(int)
        ty, tx = fy - iy, fx - ix
        ty = (ty * ty * (3 - 2 * ty))[:, None]
        tx = (tx * tx * (3 - 2 * tx))[None, :]
        a, b = g[iy][:, ix], g[iy][:, ix + 1]
        c, d = g[iy + 1][:, ix], g[iy + 1][:, ix + 1]
        out += amp * ((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty)
        tot += amp
        amp *= 0.5
        cx, cy = cx * 2, cy * 2
    return out / tot


def _mix(c0, c1, t):
    t = np.asarray(t, float)[..., None]
    return np.asarray(c0, float) * (1 - t) + np.asarray(c1, float) * t


def _grid():
    yy, xx = np.mgrid[0:TILE_PX, 0:TILE_PX].astype(float)
    v = (yy + 0.5) / TILE_PX                       # along the leaf (row 0 = base)
    s = ((xx + 0.5) / TILE_PX - 0.5) * 2           # across, midrib at 0
    return s, v


def tex_cordyline(rng, dark):
    s, v = _grid()
    a = np.abs(s)
    w = prof_strap(v)
    r = a / np.maximum(w, 1e-3)
    streak = _noise(rng, 40, 2, 2)
    blot = _noise(rng, 4, 6, 2)
    if dark:
        mid, body, edge, rib = (0.17, 0.02, 0.06), (0.33, 0.03, 0.10), (0.70, 0.08, 0.22), (0.45, 0.08, 0.14)
    else:
        mid, body, edge, rib = (0.40, 0.02, 0.08), (0.74, 0.05, 0.15), (0.96, 0.30, 0.46), (0.88, 0.32, 0.42)
    col = _mix(mid, body, _ss(0.04, 0.45, r))
    col = _mix(col, edge, _ss(0.66, 0.95, r) * (0.45 + 0.55 * streak))
    col *= (0.78 + 0.44 * streak)[..., None]
    col = _mix(col, (0.30, 0.26, 0.10), _ss(0.30, 0.02, v) * 0.8)          # bronze-green base
    if dark:
        col = _mix(col, (0.14, 0.17, 0.05), _ss(0.55, 0.8, blot) * 0.55)    # olive-bronze patches
    col = _mix(col, rib, (a < 0.025) * 0.5)
    return col, a < w


def tex_croton(rng):
    s, v = _grid()
    a = np.abs(s)
    w = prof_croton(v)
    r = a / np.maximum(w, 1e-3)
    n1 = _noise(rng, 5, 7, 3)
    n2 = _noise(rng, 9, 12, 2)
    col = _mix((0.07, 0.25, 0.05), (0.03, 0.13, 0.04), n2)
    col = _mix(col, (0.95, 0.45, 0.08), _ss(0.50, 0.60, n1 + 0.25 * (1 - v) - 0.15 * r))
    col = _mix(col, (0.72, 0.07, 0.05), _ss(0.62, 0.70, n1 + 0.30 * (1 - v)))
    col = _mix(col, (0.93, 0.82, 0.18), _ss(0.68, 0.74, n2 + 0.2 * v) * 0.9)
    q = (v - 0.30 * a) * 11.0
    vein = (np.abs(np.mod(q, 1) - 0.5) > 0.45) & (r < 0.92)
    col = _mix(col, (0.95, 0.86, 0.25), vein * 0.8 + (a < 0.03))
    return col, a < w


def tex_paddle(rng, light):
    s, v = _grid()
    a = np.abs(s)
    w = prof_paddle(v)
    r = a / np.maximum(w, 1e-3)
    blot = _noise(rng, 6, 10, 3)
    if light:
        base, dark, rib = (0.42, 0.60, 0.17), (0.28, 0.46, 0.10), (0.72, 0.76, 0.42)
    else:
        base, dark, rib = (0.22, 0.40, 0.19), (0.13, 0.28, 0.13), (0.58, 0.63, 0.38)
    col = _mix(base, dark, blot * 0.8)
    qq = v - 0.22 * a                                      # lateral veins run out toward the tip
    vein = np.abs(np.mod(qq * 85, 1) - 0.5) > 0.38
    col = col * (1 + 0.08 * vein)[..., None]
    col = _mix(col, rib, _ss(0.06, 0.02, a))
    col = _mix(col, (0.45, 0.40, 0.22), _ss(0.90, 1.0, r) * 0.45)            # dry margin
    alpha = a < w
    for _ in range(4 if light else 10):                    # wind tears along the veins
        q0, side, depth = rng.uniform(0.12, 0.92), rng.choice([-1, 1]), rng.uniform(0.35, 0.97)
        same = (np.sign(s) == side) & (r > 1 - depth)
        alpha &= ~((np.abs(qq - q0) < 0.0035) & same)
        col = _mix(col, (0.40, 0.37, 0.20), ((np.abs(qq - q0) < 0.012) & same) * 0.35)
    return col, alpha


def tex_philo(rng):
    s, v = _grid()
    a = np.abs(s)
    t = np.clip((v - 0.02) / 0.98, 0, 1)
    q = (v - 0.32 * a) * 5.2
    lobe = 1 - 0.5 * (0.5 + 0.5 * np.cos(TAU * q)) ** 5 * _ss(0.15, 0.3, t) * _ss(0.95, 0.75, t)
    w = prof_philo(v) * lobe
    r = a / np.maximum(w, 1e-3)
    n = _noise(rng, 6, 6, 3)
    col = _mix((0.05, 0.19, 0.04), (0.11, 0.31, 0.06), n)
    vein = (np.abs(np.mod(q, 1) - 0.5) < 0.035) & (r < 0.9)
    col = _mix(col, (0.32, 0.50, 0.13), vein * 0.7 + (a < 0.03) * 0.9)
    return col, a < w


def _draw_leaflet(rgb, alpha, base, direction, length, wmax, colour, bend=0.0, serr=0.0):
    """Lanceolate leaflet into tile arrays (pixel units: x across, y along)."""
    T = TILE_PX
    (bx, by), (dx, dy) = base, direction
    ex, ey = bx + dx * length, by + dy * length
    pad = wmax + abs(bend) * length + 2
    x0, x1 = int(max(0, min(bx, ex) - pad)), int(min(T, max(bx, ex) + pad))
    y0, y1 = int(max(0, min(by, ey) - pad)), int(min(T, max(by, ey) + pad))
    if x1 <= x0 or y1 <= y0:
        return
    py, px = np.mgrid[y0:y1, x0:x1] + 0.5
    rx, ry = px - bx, py - by
    tau = (rx * dx + ry * dy) / length
    d = -rx * dy + ry * dx - bend * np.clip(tau, 0, 1) ** 2 * length
    hw = wmax * np.clip(np.sin(np.pi * np.clip(tau, 0, 1) ** 0.55), 0, 1) ** 0.8
    if serr:
        hw = hw * (1 - serr * (0.5 + 0.5 * np.sin(tau * length * 0.9)))
    m = (tau > 0) & (tau < 1) & (np.abs(d) < hw)
    shade = (0.78 + 0.3 * np.clip(tau, 0, 1)) * (1 + 0.12 * (np.abs(d) < 0.9))
    sub, suba = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]
    sub[m] = (np.asarray(colour)[None, None, :] * shade[..., None])[m]
    suba |= m


def tex_frond(rng, per_side, phi_deg, wmax, c0, c1, rachis, env, start, serr=0.0, bend=0.0):
    T = TILE_PX
    rgb = np.zeros((T, T, 3))
    alpha = np.zeros((T, T), bool)
    phi = math.radians(phi_deg)
    for side in (-1, 1):
        for k in range(per_side):
            vk = start + (0.985 - start) * (k + rng.uniform(-0.25, 0.25)) / per_side
            reach = float(env(vk)) * (T / 2 - 4)
            L = reach / math.sin(phi)
            col = _mix(c0, c1, rng.random())
            _draw_leaflet(rgb, alpha, (T / 2 + side * 2, vk * T), (side * math.sin(phi), math.cos(phi)),
                          L, wmax * rng.uniform(0.85, 1.1), col, bend * side, serr)
    s, v = _grid()
    rm = np.abs(s) * T / 2 < 3.2 * (1 - 0.7 * v) + 0.8
    rgb[rm] = _mix(rachis, np.asarray(rachis) * 0.8, v)[rm]
    alpha |= rm
    return rgb, alpha


def tex_olive(rng):
    T = TILE_PX
    rgb = np.zeros((T, T, 3))
    alpha = np.zeros((T, T), bool)
    for _ in range(8):                                     # twigs fanning up from the card base
        x, y = T / 2 + rng.uniform(-60, 60), rng.uniform(5, 50)
        ang = rng.uniform(-1.0, 1.0)
        curl = rng.uniform(-0.004, 0.004)
        for step in range(int(rng.uniform(40, 70))):
            ang += curl * 6
            x, y = x + math.sin(ang) * 6, y + math.cos(ang) * 6
            if not (4 < x < T - 4 and 4 < y < T - 4):
                break
            yi, xi = int(y), int(x)
            rgb[yi - 1:yi + 2, xi - 1:xi + 2] = (0.32, 0.27, 0.21)
            alpha[yi - 1:yi + 2, xi - 1:xi + 2] = True
            if step % 2 == 0:
                la = ang + rng.choice([-1, 1]) * rng.uniform(0.35, 0.9)
                silver = rng.random() < 0.3
                col = _mix((0.52, 0.56, 0.45), (0.62, 0.65, 0.54), rng.random()) if silver else \
                    _mix((0.20, 0.27, 0.14), (0.36, 0.42, 0.25), rng.random())
                _draw_leaflet(rgb, alpha, (x, y), (math.sin(la), math.cos(la)), rng.uniform(42, 60), 6.5, col)
    return rgb, alpha


def tex_lance(rng):
    s, v = _grid()
    a = np.abs(s)
    w = prof_strap(v)
    r = a / np.maximum(w, 1e-3)
    streak = _noise(rng, 30, 3, 2)
    col = _mix((0.10, 0.31, 0.06), (0.18, 0.42, 0.08), streak)
    col *= (1 - 0.12 * (np.abs(np.mod(a * 28, 1) - 0.5) > 0.42))[..., None]
    col = _mix(col, (0.36, 0.48, 0.10), _ss(0.85, 1.0, r) * 0.5)
    col = _mix(col, (0.55, 0.62, 0.30), _ss(0.05, 0.015, a))
    return col, a < w


def tex_grass(rng):
    s, v = _grid()
    a = np.abs(s)
    streak = _noise(rng, 24, 2, 2)
    col = _mix((0.12, 0.24, 0.05), (0.46, 0.52, 0.20), v ** 1.2) * (0.85 + 0.3 * streak)[..., None]
    col = _mix(col, (0.55, 0.60, 0.30), (a < 0.06) * 0.4)
    return col, a < prof_grass(v)


def tex_stem(rng):
    s, v = _grid()
    left = s < 0
    fib = _noise(rng, 60, 4, 2)
    ring = np.abs(np.mod(v * 14 + 0.15 * _noise(rng, 8, 4), 1) - 0.5) > 0.42
    trunk = _mix((0.40, 0.35, 0.28), (0.24, 0.20, 0.16), ring * 0.8) * (0.7 + 0.5 * fib)[..., None]
    cn = _noise(rng, 8, 16, 2)
    q = np.mod(v * 9, 1)
    cane = _mix((0.33, 0.42, 0.22), (0.44, 0.50, 0.30), cn)
    cane = _mix(cane, (0.62, 0.58, 0.42), (q < 0.05) * 0.9)
    cane = _mix(cane, (0.18, 0.20, 0.12), ((q > 0.05) & (q < 0.08)) * 0.6)
    return np.where(left[..., None], trunk, cane), np.ones_like(v, bool)


def make_atlas():
    rng = np.random.default_rng(SEED)
    tiles = {
        CORD_RED: tex_cordyline(rng, False), CORD_DARK: tex_cordyline(rng, True),
        CROTON: tex_croton(rng), PADDLE: tex_paddle(rng, False),
        PHILO: tex_philo(rng),
        PALM: tex_frond(rng, 25, 62, 4.6, (0.30, 0.46, 0.09), (0.50, 0.60, 0.16), (0.62, 0.60, 0.30),
                        prof_frond, 0.12, bend=0.05),
        FERN: tex_frond(rng, 46, 70, 4.6, (0.13, 0.35, 0.05), (0.26, 0.48, 0.10), (0.22, 0.32, 0.08),
                        prof_fern, 0.06, serr=0.35),
        OLIVE: tex_olive(rng), LANCE: tex_lance(rng), GRASS: tex_grass(rng),
        BANANA: tex_paddle(rng, True), STEM: tex_stem(rng),
    }
    T = TILE_PX
    atlas = np.zeros((ROWS * T, COLS * T, 4), np.float32)
    for k, (rgb, alpha) in tiles.items():
        rgb = np.clip(rgb, 0, 1)
        if alpha.any() and not alpha.all():      # bleed leaf colour into the clear area
            rgb = np.where(alpha[..., None], rgb, rgb[alpha].mean(axis=0))
        r, c = divmod(k, COLS)
        atlas[r * T:(r + 1) * T, c * T:(c + 1) * T, :3] = rgb
        atlas[r * T:(r + 1) * T, c * T:(c + 1) * T, 3] = alpha
    return atlas


def make_mulch(n=512):
    """Seamless red-brown bark mulch (05/06 front strip)."""
    rng = np.random.default_rng(SEED + 1)
    base = _noise(rng, 8, 8, 3, n)
    rgb = _mix((0.10, 0.05, 0.03), (0.22, 0.11, 0.06), base)
    for _ in range(2600):
        cx, cy = rng.uniform(0, n, 2)
        ang = rng.uniform(0, math.pi)
        ln, wd = rng.uniform(5, 20), rng.uniform(2, 6)
        dx, dy = math.cos(ang), math.sin(ang)
        rad = int(ln / 2 + wd) + 1
        ys = np.arange(int(cy) - rad, int(cy) + rad + 1)
        xs = np.arange(int(cx) - rad, int(cx) + rad + 1)
        py, px = np.meshgrid(ys + 0.5, xs + 0.5, indexing="ij")
        rx, ry = px - cx, py - cy
        m = (np.abs(rx * dx + ry * dy) < ln / 2) & (np.abs(-rx * dy + ry * dx) < wd / 2)
        col = _mix((0.22, 0.10, 0.05), (0.55, 0.28, 0.14), rng.random())
        idx = np.ix_(ys % n, xs % n)
        shade = 0.8 + 0.35 * ((-rx * dy + ry * dx) / wd + 0.5)
        rgb[idx] = np.where(m[..., None], col * shade[..., None], rgb[idx])
    out = np.ones((n, n, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 1)
    return out


def _image(name, rgba):
    h, w = rgba.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    return img


def materials(G):
    atlas = _image("plant_leaf_atlas", make_atlas())
    m = G.mat("plant_foliage", (0.15, 0.35, 0.08), 0.5)
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    t = n.new("ShaderNodeTexImage")
    t.image = atlas
    l.new(t.outputs["Color"], b.inputs["Base Color"])
    clip = n.new("ShaderNodeMath")                 # Round = alpha clip at 0.5 (glTF alphaMode MASK)
    clip.operation = "ROUND"
    l.new(t.outputs["Alpha"], clip.inputs[0])
    l.new(clip.outputs[0], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.48
    b.inputs["Specular IOR Level"].default_value = 0.45
    m.use_backface_culling = False

    mu = G.mat("plant_mulch", (0.25, 0.12, 0.07), 0.95)
    n, l = mu.node_tree.nodes, mu.node_tree.links
    t = n.new("ShaderNodeTexImage")
    t.image = _image("plant_mulch_tex", make_mulch())
    l.new(t.outputs["Color"], n["Principled BSDF"].inputs["Base Color"])
    G.TILE["plant_mulch"] = MULCH_TILE_M          # uv_all() box-projects it like the pbr materials
    G.mat("plant_pot", (0.86, 0.85, 0.82), 0.32)
    return m


# =========================================================================================
# geometry
# =========================================================================================
def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    ln = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2) or 1.0
    return (a[0] / ln, a[1] / ln, a[2] / ln)


def _dir(az, el):
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))


def tuv(tile, u, v):
    """Tile-local (u, v) -> atlas UV."""
    c, r = tile % COLS, tile // COLS
    m = 0.004
    return ((c + m + u * (1 - 2 * m)) / COLS, (r + m + v * (1 - 2 * m)) / ROWS)


class MB:
    """Tiny mesh builder: vertices, faces with per-corner UVs and material index."""

    def __init__(self):
        self.v, self.f, self.uv, self.mi = [], [], [], []

    def add(self, pts):
        i = len(self.v)
        self.v.extend(pts)
        return i

    def face(self, idx, uvs, mi=0):
        self.f.append(tuple(idx))
        self.uv.append(tuple(uvs))
        self.mi.append(mi)

    def build(self, name, mats):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", [c for face in self.uv for uv in face for c in uv])
        me.polygons.foreach_set("material_index", self.mi)
        me.polygons.foreach_set("use_smooth", [True] * len(self.f))
        for m in mats:
            me.materials.append(m)
        me.update()
        return me


def leaf(mb, base, az, el, L, W, tile, droop=0.8, fold=0.25, segs=5, roll=0.0, bend_pow=1.5, mid=True):
    """Curved leaf card along a drooping spine; width follows the tile's leaf profile."""
    prof = TILE_PROF[tile]
    p = base
    rows = []
    for i in range(segs + 1):
        t = i / segs
        if i:
            p = _add(p, _mul(_dir(az, el - droop * ((i - 0.5) / segs) ** bend_pow), L / segs))
        d = _dir(az, el - droop * t ** bend_pow)
        side = (-math.sin(az), math.cos(az), 0.0)
        nrm = _cross(d, side)
        side = _add(_mul(side, math.cos(roll)), _mul(nrm, math.sin(roll)))
        nrm = _norm(_cross(d, side))
        pg = min(1.0, float(prof(t)) * 1.08 + 0.03)
        hw = 0.5 * W * pg
        lift = _mul(nrm, fold * hw)
        lft = _add(_add(p, _mul(side, -hw)), lift)
        rgt = _add(_add(p, _mul(side, hw)), lift)
        if mid:
            rows.append((mb.add([lft, p, rgt]), [0.5 - 0.5 * pg, 0.5, 0.5 + 0.5 * pg], t))
        else:
            rows.append((mb.add([lft, rgt]), [0.5 - 0.5 * pg, 0.5 + 0.5 * pg], t))
    k = 3 if mid else 2
    for (i0, u0, t0), (i1, u1, t1) in zip(rows, rows[1:]):
        for j in range(k - 1):
            mb.face((i0 + j, i0 + j + 1, i1 + j + 1, i1 + j),
                    (tuv(tile, u0[j], t0), tuv(tile, u0[j + 1], t0), tuv(tile, u1[j + 1], t1),
                     tuv(tile, u1[j], t1)))


def tube(mb, pts, radii, sides=5, tile=STEM, urange=CANE_U, vrange=(0.0, 1.0)):
    """Low-poly tapered tube through pts (stems, trunks, petioles)."""
    n = len(pts)
    starts = []
    for i, p in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        t = _norm((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
        ax = _norm(_cross(t, (0, 0, 1))) if abs(t[2]) < 0.98 else (1.0, 0.0, 0.0)
        bx = _cross(t, ax)
        ring = [_add(p, _mul(_add(_mul(ax, math.cos(TAU * j / sides)), _mul(bx, math.sin(TAU * j / sides))),
                             radii[i])) for j in range(sides)]
        starts.append(mb.add(ring))
    for i in range(n - 1):
        v0 = vrange[0] + (vrange[1] - vrange[0]) * i / (n - 1)
        v1 = vrange[0] + (vrange[1] - vrange[0]) * (i + 1) / (n - 1)
        for j in range(sides):
            ua = urange[0] + (urange[1] - urange[0]) * j / sides
            ub = urange[0] + (urange[1] - urange[0]) * (j + 1) / sides
            jn = (j + 1) % sides
            mb.face((starts[i] + j, starts[i] + jn, starts[i + 1] + jn, starts[i + 1] + j),
                    (tuv(tile, ua, v0), tuv(tile, ub, v0), tuv(tile, ub, v1), tuv(tile, ua, v1)))


def _rad(d):
    return math.radians(d)


# ---- plant builders (origin at the plant's base) ------------------------------------------
def build_cordyline(rng, tiles):
    mb = MB()
    for i in range(rng.choice([1, 2, 2, 3])):
        h = rng.uniform(0.55, 0.95) if i == 0 else rng.uniform(0.2, 0.6)
        bx, by = (0, 0) if i == 0 else (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15))
        top = (bx + rng.uniform(-0.08, 0.08), by + rng.uniform(-0.08, 0.08), h)
        tube(mb, [(bx, by, 0.0), top], [0.03, 0.024], 4, urange=TRUNK_U)
        n = rng.randint(14, 18)
        for k in range(n):
            age = k / (n - 1)                                 # 0 = oldest, outermost
            leaf(mb, (top[0], top[1], top[2] - 0.07 * (1 - age)), k * GOLDEN + rng.uniform(-0.2, 0.2),
                 _rad(-5 + 80 * age + rng.uniform(-6, 6)), rng.uniform(0.52, 0.70) * (0.65 + 0.35 * (1 - age)),
                 rng.uniform(0.11, 0.14), tiles[0] if rng.random() < 0.8 else tiles[1],
                 droop=_rad(25 + 70 * (1 - age)), fold=0.25, segs=5, roll=rng.uniform(-0.3, 0.3))
    return mb


def build_croton(rng):
    mb = MB()
    for _ in range(rng.randint(3, 5)):
        ang, h = rng.uniform(0, TAU), rng.uniform(0.4, 0.8)
        top = (math.cos(ang) * 0.12, math.sin(ang) * 0.12, h)
        tube(mb, [(0.0, 0.0, 0.0), top], [0.02, 0.015], 3, urange=TRUNK_U)
        n = rng.randint(8, 12)
        for k in range(n):
            age = k / (n - 1)
            leaf(mb, (top[0], top[1], top[2] - 0.18 * (1 - age)), k * GOLDEN + ang,
                 _rad(-20 + 70 * age), rng.uniform(0.24, 0.32), rng.uniform(0.09, 0.12), CROTON,
                 droop=_rad(30), fold=0.15, segs=3, roll=rng.uniform(-0.4, 0.4))
    return mb


def build_philo(rng, size=1.3):
    mb = MB()
    n = rng.randint(14, 20)
    for k in range(n):
        age = k / (n - 1)
        az = k * GOLDEN + rng.uniform(-0.3, 0.3)
        el = _rad(rng.uniform(40, 72))
        pl = rng.uniform(0.32, 0.52) * size * (0.75 + 0.25 * age)
        d = _dir(az, el)
        p0 = (0.0, 0.0, 0.02)
        p2 = _add(p0, _mul(d, pl))
        p1 = _add(_add(p0, _mul(d, pl * 0.5)), (0, 0, 0.03))
        tube(mb, [p0, p1, p2], [0.012, 0.01, 0.008], 3, tile=PHILO, urange=(0.49, 0.51), vrange=(0.1, 0.4))
        leaf(mb, p2, az, _rad(rng.uniform(-5, 30)), rng.uniform(0.32, 0.42) * size, 0.3 * size, PHILO,
             droop=_rad(50), fold=-0.08, segs=4, roll=rng.uniform(-0.3, 0.3))
    return mb


def build_fern(rng, size=1.15):
    mb = MB()
    n = rng.randint(18, 26)
    for k in range(n):
        age = k / (n - 1)
        leaf(mb, (0.0, 0.0, 0.03), k * GOLDEN + rng.uniform(-0.2, 0.2), _rad(35 + 45 * age),
             rng.uniform(0.55, 0.85) * size * (0.7 + 0.3 * (1 - age)), 0.24 * size, FERN,
             droop=_rad(70 + 50 * (1 - age)), fold=0.12, segs=5, roll=rng.uniform(-0.2, 0.2))
    return mb


def build_brom(rng):
    """Ginger / bird's-nest style rosette of broad green straps."""
    mb = MB()
    n = rng.randint(12, 16)
    for k in range(n):
        age = k / (n - 1)
        leaf(mb, (0.0, 0.0, 0.03), k * GOLDEN + rng.uniform(-0.2, 0.2), _rad(35 + 48 * age),
             rng.uniform(0.6, 0.9), rng.uniform(0.13, 0.17), LANCE,
             droop=_rad(40 + 50 * (1 - age)), fold=0.4, segs=4, roll=rng.uniform(-0.2, 0.2))
    return mb


def build_ginger(rng):
    """Upright ginger / heliconia clump: leafy canes with two ranks of lanceolate leaves (05)."""
    mb = MB()
    for _ in range(rng.randint(5, 7)):
        ang, r = rng.uniform(0, TAU), rng.uniform(0.0, 0.18)
        h = rng.uniform(0.55, 1.1)
        bx, by = r * math.cos(ang), r * math.sin(ang)
        top = (bx + math.cos(ang) * 0.12 * h, by + math.sin(ang) * 0.12 * h, h)
        tube(mb, [(bx, by, 0.0), top], [0.016, 0.012], 3, tile=LANCE, urange=(0.49, 0.51), vrange=(0.2, 0.5))
        rank = rng.uniform(0, TAU)
        n = rng.randint(5, 7)
        for k in range(n):
            f = 0.35 + 0.65 * k / (n - 1)
            p = (bx + (top[0] - bx) * f, by + (top[1] - by) * f, h * f)
            leaf(mb, p, rank + (0 if k % 2 else math.pi) + rng.uniform(-0.3, 0.3), _rad(rng.uniform(25, 55)),
                 rng.uniform(0.32, 0.48), rng.uniform(0.10, 0.13), LANCE, droop=_rad(rng.uniform(40, 80)),
                 fold=0.2, segs=4, roll=rng.uniform(-0.4, 0.4))
    return mb


def build_grass(rng):
    mb = MB()
    for _ in range(rng.randint(30, 40)):
        leaf(mb, (rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), 0.02), rng.uniform(0, TAU),
             _rad(rng.uniform(55, 85)), rng.uniform(0.5, 0.85), rng.uniform(0.025, 0.035), GRASS,
             droop=_rad(rng.uniform(60, 120)), fold=0.0, segs=3, mid=False)
    return mb


def build_strelitzia(rng, trunks, spread=0.45, fan_az=None, fan_jit=0.5, blade=(1.0, 1.5),
                     width=(0.36, 0.48), petiole=(0.7, 1.4), leaves=(5, 8), light=0.25, sideways=0.0):
    """Giant bird-of-paradise: grey trunks each topped by a flat fan of paddle leaves."""
    mb = MB()
    for h in trunks:
        if fan_az is not None:          # spread trunks along the fan plane (front clump)
            o = rng.uniform(-spread, spread)
            bx, by = math.cos(fan_az) * o, math.sin(fan_az) * o + rng.uniform(-0.15, 0.15)
        else:
            bx, by = rng.uniform(-spread, spread), rng.uniform(-spread, spread)
        top = (bx + rng.uniform(-0.12, 0.12) * h / 3, by + rng.uniform(-0.12, 0.12) * h / 3, h)
        if h > 0.25:
            midp = ((bx + top[0]) / 2, (by + top[1]) / 2, h / 2)
            tube(mb, [(bx, by, 0.0), midp, top], [0.12, 0.1, 0.085], 6, urange=TRUNK_U, vrange=(0, min(1, h / 4)))
        faz = (fan_az if fan_az is not None else rng.uniform(0, TAU)) + rng.uniform(-fan_jit, fan_jit)
        n = rng.randint(*leaves)
        for k in range(n):
            age = k / (n - 1)
            az = faz + (0 if k % 2 else math.pi) + rng.uniform(-0.25, 0.25) + sideways * rng.uniform(-1, 1)
            el = _rad(35 + 50 * age + rng.uniform(-8, 8))
            pl = rng.uniform(*petiole) * (0.7 + 0.3 * (1 - age))
            p0 = (top[0], top[1], top[2] - 0.1 * (1 - age))
            d = _dir(az, el)
            p2 = _add(p0, _mul(d, pl))
            p1 = _add(_add(p0, _mul(d, pl * 0.5)), (0, 0, 0.04))
            tube(mb, [p0, p1, p2], [0.035, 0.028, 0.022], 3, tile=PADDLE, urange=(0.49, 0.51), vrange=(0.3, 0.6))
            leaf(mb, p2, az, el - _rad(10), rng.uniform(*blade) * (0.75 + 0.25 * (1 - age)), rng.uniform(*width),
                 BANANA if rng.random() < light else PADDLE, droop=_rad(40 + 70 * (1 - age)), fold=-0.12,
                 segs=6, roll=rng.uniform(-0.6, 0.6), bend_pow=1.4)
    return mb


def build_areca(rng, canes, h, spread=0.3, fronds=(5, 8), flen=(1.1, 1.7), fw=(0.7, 0.9)):
    """Clumping (areca / king) palm: splayed ringed canes with arching pinnate fronds."""
    mb = MB()
    for _ in range(canes):
        hh = rng.uniform(*h)
        ang, r = rng.uniform(0, TAU), rng.uniform(0, spread)
        bx, by = r * math.cos(ang), r * math.sin(ang)
        lean = rng.uniform(0.08, 0.25) * hh
        top = (bx + math.cos(ang) * lean, by + math.sin(ang) * lean, hh)
        midp = (bx + math.cos(ang) * lean * 0.3, by + math.sin(ang) * lean * 0.3, hh * 0.5)
        if hh > 0.3:
            tube(mb, [(bx, by, 0.0), midp, top], [0.05, 0.042, 0.035], 5, urange=CANE_U, vrange=(0, min(1, hh / 2)))
        n = rng.randint(*fronds)
        for k in range(n):
            age = k / (n - 1)
            leaf(mb, top, ang + k * GOLDEN + rng.uniform(-0.3, 0.3), _rad(25 + 50 * age),
                 rng.uniform(*flen) * (0.75 + 0.25 * (1 - age)), rng.uniform(*fw), PALM,
                 droop=_rad(70 + 50 * (1 - age)), fold=0.45, segs=6, roll=rng.uniform(-0.3, 0.3), bend_pow=1.3)
    return mb


def build_olive(rng):
    """Grey-green olive / rosemary shrub for the roof planter (18, 20)."""
    mb = MB()
    cz = rng.uniform(0.55, 0.75)
    tube(mb, [(0.0, 0.0, 0.0), (0.02, 0.0, cz * 0.5), (0.05, 0.03, cz * 0.8)], [0.04, 0.03, 0.02], 4, urange=TRUNK_U)
    for _ in range(rng.randint(70, 85)):
        a, e = rng.uniform(0, TAU), rng.uniform(-0.6, 1.0)
        rr = rng.uniform(0.1, 1.0) ** 0.5
        c = (math.cos(a) * 0.6 * rr, math.sin(a) * 0.5 * rr, cz + math.sin(e) * 0.4 * rr)
        size = rng.uniform(0.32, 0.42)
        d = _dir(a, _rad(rng.uniform(-10, 60)))
        leaf(mb, _add(c, _mul(d, -size * 0.4)), a, _rad(rng.uniform(-10, 60)), size, size, OLIVE,
             droop=0.5, fold=0.2, segs=2, roll=rng.uniform(-0.8, 0.8))
    return mb


def build_pot(top_r=0.3, bot_r=0.23, h=0.55, sides=20):
    """White tapered planter pot with a mulch top (materials: pot, mulch)."""
    mb = MB()
    rim = h - 0.05
    rings = [(bot_r, 0.0), (top_r, h), (top_r - 0.03, h), (top_r - 0.035, rim)]
    starts = [mb.add([(r * math.cos(TAU * j / sides), r * math.sin(TAU * j / sides), z) for j in range(sides)])
              for r, z in rings]
    for a, b in zip(starts, starts[1:]):
        for j in range(sides):
            jn = (j + 1) % sides
            mb.face((a + j, a + jn, b + jn, b + j), ((0, 0),) * 4, 0)
    mb.face(tuple(range(starts[0] + sides - 1, starts[0] - 1, -1)), ((0, 0),) * sides, 0)
    rr = top_r - 0.035
    mb.face(tuple(range(starts[3], starts[3] + sides)),
            [(0.5 + 0.5 * math.cos(TAU * j / sides) * rr, 0.5 + 0.5 * math.sin(TAU * j / sides) * rr)
             for j in range(sides)], 1)
    return mb


# variants per kind: (builder(rng) -> MB, how many)
KINDS = {
    "cord_red": (lambda r: build_cordyline(r, (CORD_RED, CORD_DARK)), 3),
    "cord_dark": (lambda r: build_cordyline(r, (CORD_DARK, CORD_RED)), 2),
    "croton": (build_croton, 2),
    "philo": (build_philo, 3),
    "fern": (build_fern, 2),
    "brom": (build_brom, 2),
    "grass": (build_grass, 2),
    "ginger": (build_ginger, 2),
    "olive": (build_olive, 2),
    "strel_front": (lambda r: build_strelitzia(r, [5.0, 4.4, 3.8, 3.2, 2.6, 1.9, 1.2, 0.0, 0.0], spread=0.7,
                                               fan_az=0.0, fan_jit=0.4, blade=(1.2, 1.7), width=(0.4, 0.52),
                                               petiole=(0.9, 1.6), leaves=(7, 10)), 1),
    "strel_med": (lambda r: build_strelitzia(r, [r.uniform(1.6, 2.4), r.uniform(0.8, 1.4), 0.0], spread=0.35,
                                             blade=(0.9, 1.3), width=(0.32, 0.42), petiole=(0.6, 1.1),
                                             leaves=(5, 7)), 3),
    "strel_pot": (lambda r: build_strelitzia(r, [0.0, 0.0], spread=0.08, blade=(0.6, 0.85), width=(0.24, 0.3),
                                             petiole=(0.5, 0.85), leaves=(6, 8), light=0.4), 2),
    "areca_tall": (lambda r: build_areca(r, r.randint(6, 8), (1.6, 3.8), flen=(1.4, 2.1), fw=(0.8, 1.0)), 3),
    "areca_mid": (lambda r: build_areca(r, r.randint(4, 6), (0.7, 1.8), flen=(1.1, 1.6), fw=(0.7, 0.85)), 2),
    "areca_low": (lambda r: build_areca(r, r.randint(3, 5), (0.15, 0.9), fronds=(6, 9), flen=(0.9, 1.3),
                                        fw=(0.55, 0.7)), 2),
}


# =========================================================================================
# placement with simple collision avoidance against the built scene
# =========================================================================================
class Planter:
    def __init__(self, G, foliage):
        self.G = G
        self.rng = random.Random(SEED)
        self.variants = {}
        self.count = 0
        self.objects = []
        self.residual = []          # (name, vertices still inside a structure) for the log
        for kind, (builder, nvar) in KINDS.items():
            out = []
            for i in range(nvar):
                mb = builder(random.Random(zlib.crc32(f"{SEED}:{kind}:{i}".encode())))
                me = mb.build(f"Plant_mesh_{kind}_{i}", [foliage])
                pts = np.array(mb.v)
                out.append((me, pts[:: max(1, len(pts) // 600)]))
            self.variants[kind] = out
        self.boxes = self._obstacles()

    @staticmethod
    def _obstacles():
        """World AABBs of solid built parts (house, walls, fence, pavilion, furniture)."""
        boxes, fence = [], None
        skip = {"Site", "Context", "Library"}          # ground, neighbours, hidden model library
        for o in bpy.data.objects:
            if o.type != "MESH" or o.name.startswith(("Plant_", "Palm_", "shrub_")):
                continue
            if skip & {c.name for c in o.users_collection}:
                continue
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo = [min(p[i] for p in bb) for i in range(3)]
            hi = [max(p[i] for p in bb) for i in range(3)]
            if hi[2] - lo[2] < 0.12 and hi[2] < 0.2:
                continue                                   # flat ground: paths, turf, coping
            if o.name.startswith("Fence_"):
                fence = lo + hi if fence is None else [min(fence[0], lo[0]), min(fence[1], lo[1]),
                                                        min(fence[2], lo[2]), max(fence[3], hi[0]),
                                                        max(fence[4], hi[1]), max(fence[5], hi[2])]
                continue
            boxes.append(lo + hi)
        if fence:
            boxes.append(fence)
        return np.array(boxes) if boxes else np.zeros((0, 6))

    def _hits(self, pts, x, y, z, rot, s, boxes):
        c, sn = math.cos(rot), math.sin(rot)
        wx = x + s * (pts[:, 0] * c - pts[:, 1] * sn)
        wy = y + s * (pts[:, 0] * sn + pts[:, 1] * c)
        wz = z + s * pts[:, 2]
        e = 0.02
        inside = ((wx[:, None] > boxes[None, :, 0] + e) & (wx[:, None] < boxes[None, :, 3] - e) &
                  (wy[:, None] > boxes[None, :, 1] + e) & (wy[:, None] < boxes[None, :, 4] - e) &
                  (wz[:, None] > boxes[None, :, 2] + e) & (wz[:, None] < boxes[None, :, 5] - e))
        return int(inside.any(axis=1).sum())

    def put(self, kind, x, y, z=0.0, rot=None, scale=None, avoid=True, name=None):
        rng = self.rng
        me, pts = rng.choice(self.variants[kind])
        rot = rng.uniform(0, TAU) if rot is None else rot
        s = rng.uniform(0.85, 1.15) if scale is None else scale
        best = (x, y, rot)
        if avoid and len(self.boxes):
            reach = float(np.abs(pts[:, :2]).max()) * s + 0.7
            b = self.boxes
            near = b[(b[:, 0] < x + reach) & (b[:, 3] > x - reach) & (b[:, 1] < y + reach) & (b[:, 4] > y - reach)]
            if len(near):
                # try 8 rotations at the spot, then small offsets, then shrink: first clean fit wins
                cands = [(0.0, 0.0)] + [(r * math.cos(a), r * math.sin(a)) for r in (0.12, 0.25, 0.4)
                                        for a in np.linspace(0, TAU, 8, endpoint=False)]
                score = None
                for ss in (s, s * 0.8, s * 0.65):
                    for dx, dy in cands:
                        for k in range(8):
                            rr = rot + k * TAU / 8
                            h = self._hits(pts, x + dx, y + dy, z, rr, ss, near)
                            if score is None or h < score:
                                score, best, s_best = h, (x + dx, y + dy, rr), ss
                            if h == 0:
                                break
                        if score == 0:
                            break
                    if score == 0:
                        break
                s = s_best
        self.count += 1
        o = bpy.data.objects.new(name or f"Plant_{kind}_{self.count:03d}", me)
        if avoid and len(self.boxes) and len(near) and score:
            self.residual.append((o.name, score))
        o.location = (best[0], best[1], z)
        o.rotation_euler = (0.0, 0.0, best[2])
        o.scale = (s, s, s)
        self.G.link(o, COLL)
        self.objects.append(o)
        return o


def _weighted(rng, mix):
    tot = sum(w for _, w in mix)
    r = rng.uniform(0, tot)
    for kind, w in mix:
        r -= w
        if r <= 0:
            return kind
    return mix[-1][0]


def fill_bed(P, rect, mix, spacing, taken):
    """Jittered-grid fill of a rectangular bed, skipping spots near hero plants."""
    x0, y0, x1, y1 = rect
    rng = P.rng
    nx, ny = max(1, round((x1 - x0) / spacing)), max(1, round((y1 - y0) / spacing))
    for i in range(nx):
        for j in range(ny):
            x = x0 + (i + 0.5 + rng.uniform(-0.3, 0.3)) * (x1 - x0) / nx
            y = y0 + (j + 0.5 + rng.uniform(-0.3, 0.3)) * (y1 - y0) / ny
            if any(math.hypot(x - tx, y - ty) < tr for tx, ty, tr in taken):
                continue
            P.put(_weighted(rng, mix), x, y)


def front_strip(P):
    """05/06: red/burgundy cordylines along the sidewalk edge, taller greens against the wall."""
    R = STRIP_ROWS
    rng = P.rng
    x, i = R["x0"], 0
    while x < R["x1"]:
        if not (GATE[0] - 0.15 < x < GATE[1] + 0.15):
            jx = rng.uniform(-0.08, 0.08)
            if i % 2 == 0:       # front row
                kind = "cord_red" if (i // 2) % 2 == 0 else _weighted(rng, STRIP_FRONT_GREENS)
                if kind == "cord_red" and x < 1.5:          # video: only greens at the west end
                    kind = "fern"
                P.put(kind, x + jx, R["front_y"] + rng.uniform(-0.08, 0.08),
                      scale=rng.uniform(0.8, 0.95) if kind.startswith("cord") else rng.uniform(0.85, 1.05))
            else:                # back row against the wall
                kind = "cord_dark" if rng.random() < 0.15 else _weighted(rng, STRIP_BACK_GREENS)
                P.put(kind, x + jx, R["back_y"] + rng.uniform(-0.05, 0.05),
                      scale=rng.uniform(0.8, 0.95) if kind.startswith("cord") else rng.uniform(1.05, 1.3))
        x += R["step"] / 2 + rng.uniform(-0.04, 0.04)
        i += 1


def rear_planter(G, P):
    """Raised white planter against the rear facade, east of the folding doors (11, 12, 13)."""
    R = REAR_PLANTER
    x0, x1, y0, y1, h, t = R["x0"], R["x1"], R["y0"], R["y1"], R["h"], R["wall"]
    for nm, box in {"s": (x0, y1 - t, x1, y1), "w": (x0, y0, x0 + t, y1), "e": (x1 - t, y0, x1, y1),
                    "n": (x0, y0, x1, y0 + t)}.items():
        G.box(f"Plant_planter_rear_{nm}", box[0], box[1], 0.0, box[2], box[3], h, "stucco", COLL)
    G.box("Plant_planter_rear_fill", x0 + t, y0 + t, 0.0, x1 - t, y1 - t, h - 0.06, "plant_mulch", COLL)
    xs = np.linspace(x0 + 0.35, x1 - 0.9, 4)
    for i, x in enumerate(xs):
        P.put(["fern", "philo", "brom", "philo"][i], float(x), (y0 + y1) / 2, z=h - 0.08, avoid=False)
    P.put("strel_med", x1 - 0.4, (y0 + y1) / 2, z=h - 0.08, rot=0.0)      # Strelitzia at the east end


def roof_planter(G, P):
    """Olive / rosemary shrubs in the roof-deck planter (18, 20)."""
    pl = bpy.data.objects.get("Deck_planter")
    if pl is None:
        return
    bb = [pl.matrix_world @ Vector(c) for c in pl.bound_box]
    x0, x1 = min(p.x for p in bb), max(p.x for p in bb)
    y0, y1 = min(p.y for p in bb), max(p.y for p in bb)
    top = max(p.z for p in bb)
    G.box("Plant_roof_soil", x0 + 0.07, y0 + 0.07, top - 0.03, x1 - 0.07, y1 - 0.07, top + 0.01,
          "plant_mulch", "RoofDeck")
    n = max(2, round((x1 - x0) / 0.6))
    for i in range(n):
        for j, fy in enumerate((0.3, 0.7)):
            o = P.put("olive" if (i + j) % 3 else "grass", x0 + (x1 - x0) * (i + 0.5 + 0.25 * (j - 0.5)) / n,
                      y0 + (y1 - y0) * fy, z=top - 0.02, scale=P.rng.uniform(0.75, 0.95), avoid=False)
            G.link(o, "RoofDeck")


def pots(G, P):
    me = build_pot().build("Plant_mesh_pot", [G.MAT["plant_pot"], G.MAT["plant_mulch"]])
    for i, (x, y, kind, s) in enumerate(POTS):
        o = bpy.data.objects.new(f"Plant_pot_{i}", me)
        o.location = (x, y, 0.0)
        o.scale = (s, s, s)
        G.link(o, COLL)
        P.put(kind, x, y, z=0.5 * s, scale=0.8 * s, avoid=False)


def add_cameras(G):
    for name, (loc, target, lens, _frame) in CLOSEUPS.items():
        G.SHOTS[name] = (loc, target, lens)


def apply(G):
    landscape = bpy.data.collections.get(COLL)
    if landscape:
        for o in [o for o in landscape.objects if o.name.startswith("shrub_")]:
            bpy.data.objects.remove(o, do_unlink=True)
    foliage = materials(G)
    P = Planter(G, foliage)

    for name, rect in BEDS.items():
        G.box(f"Plant_bed_{name}", rect[0], rect[1], 0.0, rect[2], rect[3], BED_TOP, "plant_mulch", COLL)

    taken = []
    for kind, x, y, rot in HEROES:
        P.put(kind, x, y, rot=rot)
        taken.append((x, y, 1.0 if kind.startswith(("strel", "areca_tall", "areca_mid")) else 0.6))
    front_strip(P)
    for name, (mix, spacing) in MIXES.items():
        fill_bed(P, BEDS[name], mix, spacing, taken)
    rear_planter(G, P)
    roof_planter(G, P)
    pots(G, P)
    add_cameras(G)

    # foliage cards are alpha-clipped: allow enough transparent bounces through dense clumps
    cyc = getattr(bpy.context.scene, "cycles", None)
    if cyc is not None and cyc.transparent_max_bounces < 24:
        cyc.transparent_max_bounces = 24

    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in P.objects)
    uniq = len({o.data.name for o in P.objects})
    print(f"planting: {len(P.objects)} plants, {uniq} meshes, ~{tris} instanced triangles")
    if P.residual:
        print("planting: still touching structures:", P.residual)
