"""Recessed beach-entry pool + roof-deck spa (polish module "pool"; owns Pool_*, Spa*).

What the video shows (frames/exterior/...):
- 15 top-down (night, near-orthographic; rectified with the lot walls and the terrace step lights):
  the outline. A ~4.1 x 4.1 m deep-end rectangle with straight north (pavilion-side) and west
  (deck-side) walls, then a free-form beach lobe sweeping north-east toward the pavilion and east to
  ~1.8 m from the east boundary; a concave "waist" on the south side; ~0.4 m coping all round;
  wall / floor lights at the deep end and in the east beach.
- 09 aerial (day): the finish. Deep turquoise rectangle, aqua mid-depth, pale sand-coloured pebble
  beach on the NE, S and SW sides; dark-pebble "river" lines - a Y in the deep end (one arm from the
  north wall, one from the west wall) running south, splitting to the south coping and east along
  the beach to the east tip; thin dark concentric arcs on the NE lobe and on the SW lobe; a dark
  pebble patch where the north wall meets the beach; cream rounded coping flush with the turf.
- 17 / 11 (day, low): coping and beach close up - cream exposed aggregate, glittering ripples,
  dark contour line across the shallow beach, a floor light in the beach.
- 16 / 12 (dusk): lights in the deep-end walls.  21 aerial: deep end beside the west deck.
- 20 rooftop: raised spa - reddish timber sides on a beige plinth, wide tan coping, foaming water.

Construction (all final geometry, no modifiers):
- Pool_coping: profile swept along the outline (rounded bullnose overhanging the water).
- Pool_shell_floor / Pool_shell_walls: radial floor mesh whose depth comes from a smooth field
  (1.8 m deep core -> 0 at the beach shoreline) and vertical walls. One generated, packed texture
  (floor region + a wall atlas strip) holds the finish as seen through the water: depth tint,
  pebble aggregate detail (Poly Haven pebble_cemented_floor) and the dark contour lines - so the
  glTF export looks like the Cycles render.
- Pool_water: Principled transmission/IOR water with a generated tileable ripple normal map;
  it casts no Cycles shadow so sunlight reaches the floor (glTF unaffected).
- The ground slabs (turf / lot ground) get a boolean hole under the coping, applied in place.
- Spa_*: rebuilt roof-deck spa (frame 15 position, frame 20 materials) with foam texture.
After building, G.POOL is moved to the new outline centre and G.POOL_OUTLINE / G.POOL_COPING
(absolute xy lists) are published for modules that run later.

Review cameras added to G.SHOTS: pool_top <-> 15 (rectified crop), pool_aerial <-> 09,
pool_beach <-> 17, pool_east <-> 11, spa_close <-> 20.
"""
import math
import os
import tempfile

import numpy as np

POLYHAVEN_ASSETS = []          # only already-fetched textures are used (pebble, deck, concrete)

# ------------------------------------------------------------------ outline (water edge, metres)
# Control points traced from the rectified top-down frame 15 (cross-checked on 09 with a homography
# through the north wall, the palm base and the south coping). Closely spaced pairs keep the
# deep-end corners tight under the centripetal Catmull-Rom smoothing.
WATER_CTRL = [
    (4.40, 28.30), (4.48, 28.46), (4.65, 28.50), (6.50, 28.50), (8.35, 28.50), (8.55, 28.52),
    (8.72, 28.62), (9.10, 28.88), (9.60, 29.15), (10.20, 29.36), (10.85, 29.45), (11.55, 29.40),
    (12.15, 29.17), (12.62, 28.75), (13.02, 28.15), (13.32, 27.50), (13.50, 26.80), (13.52, 26.05),
    (13.40, 25.30), (13.12, 24.70), (12.68, 24.30), (12.05, 24.10), (11.20, 24.08), (10.35, 24.10),
    (9.60, 23.98), (8.95, 23.72), (8.40, 23.35), (7.80, 23.00), (7.05, 22.86), (6.25, 22.90),
    (5.45, 23.03), (4.90, 23.30), (4.56, 23.75), (4.43, 24.40), (4.40, 25.50), (4.40, 26.50),
    (4.40, 27.50),
]
STEP = 0.12                    # outline resampling (m)
CENTRE = (8.7, 26.1)           # radial-mesh hub (the outline is star-shaped about it)
COPING_W = 0.42                # frames 09 / 15: ~0.4 m cream band
COPING_TOP = 0.045             # 1.5 cm proud of the 3 cm turf
WATER_Z = -0.05                # water line just under the bullnose
D_DEEP = 1.8                   # deep end (task brief)
SHELF = 0.72                   # depth fraction kept after the deep-end "break"
T_BREAK = 0.3                  # ... reached this far (0..1) from the deep core toward the shore
SHORE_Z = WATER_Z + 0.015      # beach floor rises 1.5 cm above the water at the coping
DEEP_WALLS = lambda x, y: (y > 27.6 and x < 8.6) or (x < 4.9 and y > 24.6)   # N + W walls
# deep core (full depth inside; extends past the walls so the N / W walls stay full height)
CORE = [(3.6, 29.2), (7.9, 29.2), (8.1, 27.9), (8.3, 26.9), (7.8, 26.2), (6.6, 25.95), (5.2, 25.75), (3.6, 25.7)]
# sun shelves (polygon, max depth, soft edge m): the dark river lines are the hard edges of the S and
# SW shelves (09: pale sand south of the SE/SW branches, pale aqua SW lobe); the NE lobe shoals
# gradually across its concentric arcs to a sand-coloured beach (09, 11, 17).
SHELVES = [
    ([(13.7, 26.05), (12.8, 26.12), (12.03, 26.02), (11.31, 25.78), (10.25, 25.56), (9.52, 25.34),
      (8.62, 25.02), (7.98, 24.78), (7.58, 24.35), (7.02, 23.85), (6.67, 23.47), (6.45, 22.70),
      (6.4, 22.0), (14.5, 22.0), (14.5, 26.05)], 0.32, 0.0),
    ([(6.45, 22.70), (6.67, 23.47), (7.02, 23.85), (7.58, 24.35), (7.98, 24.78), (7.99, 25.0),
      (7.63, 25.23), (7.6, 25.54), (7.28, 25.93), (6.95, 26.07), (6.26, 25.98), (5.8, 25.92),
      (5.49, 25.84), (4.98, 25.72), (4.3, 25.7), (3.5, 25.7), (3.5, 22.0), (6.4, 22.0)], 0.5, 0.0),
    ([(8.5, 28.7), (8.2, 27.6), (8.3, 26.9), (9.05, 26.55), (10.1, 26.6), (11.0, 26.6), (12.0, 26.3),
      (12.8, 26.25), (14.5, 26.2), (14.5, 30.5), (8.5, 30.5)], 0.26, 0.9),
]

# depth -> apparent colour seen through the water (linear RGB), tuned against frames 09 / 17
PALETTE = [
    (0.00, (0.40, 0.34, 0.20)),      # wet sand-coloured pebble at the shoreline (09 NE beach, 17)
    (0.15, (0.31, 0.32, 0.19)),
    (0.35, (0.18, 0.36, 0.25)),      # pale aqua shallows (09 SW lobe)
    (0.70, (0.06, 0.42, 0.30)),      # aqua-teal mid depth (09 centre, right of the river)
    (1.10, (0.03, 0.47, 0.33)),
    (1.80, (0.01, 0.52, 0.36)),      # deep end: bright turquoise in sun (09)
]

# dark pebble contour lines (frame 09, mapped through a homography; NE arcs checked on frame 15)
RIVERS = [  # (points, half-width m)
    ([(6.25, 28.62), (6.12, 27.40), (5.93, 26.84), (5.82, 26.34), (5.80, 25.92)], 0.09),
    ([(4.30, 25.70), (4.98, 25.72), (5.49, 25.84), (5.80, 25.92)], 0.08),
    ([(5.80, 25.92), (6.26, 25.98), (6.95, 26.07), (7.28, 25.93), (7.60, 25.54), (7.63, 25.23),
      (7.99, 25.00), (7.98, 24.78)], 0.10),
    ([(7.98, 24.78), (7.58, 24.35), (7.02, 23.85), (6.67, 23.47), (6.45, 22.70)], 0.12),
    ([(7.98, 24.78), (8.62, 25.02), (9.52, 25.34), (10.25, 25.56), (11.31, 25.78), (12.03, 26.02),
      (12.80, 26.12), (13.70, 26.05)], 0.14),
    ([(8.40, 28.40), (8.62, 28.48), (8.85, 28.62)], 0.16),      # patch where the N wall meets the beach
]
ARCS = [  # thin concentric lines on the NE and SW beach lobes
    [(8.60, 28.35), (8.94, 27.95), (9.70, 27.88), (10.69, 28.10), (11.45, 28.45), (11.95, 28.85)],
    [(7.95, 27.80), (8.25, 27.22), (8.85, 26.97), (9.64, 26.97), (10.73, 27.22), (11.60, 27.60),
     (12.30, 28.15)],
    [(7.95, 26.66), (8.30, 26.40), (9.05, 26.36), (10.10, 26.55), (10.85, 26.85), (11.45, 27.15)],
    [(5.23, 24.68), (5.82, 24.61), (6.38, 24.41), (6.60, 24.23)],
    [(5.12, 24.30), (5.54, 24.13), (5.83, 23.80)],
    [(6.39, 25.05), (6.92, 24.93), (7.50, 24.51)],
]
ARC_W = 0.03
MOUTH = dict(at=(13.7, 26.05), half_len=0.5, rings=(0.03, 0.12, 0.22, 0.32, COPING_W - 0.035))

# ------------------------------------------------------------------ texture atlas
TEX = 2048
FLOOR_X0, FLOOR_Y0, FLOOR_L = 4.0, 22.4, 10.0      # floor region: u = (x-X0)/L, v = 0.25 + (y-Y0)/L
FLOOR_V0 = 0.25
WALL_ROWS = [(0.012, 0.113), (0.132, 0.233)]       # v ranges of the two wall strips
WALL_SPAN = 1.95                                   # metres of wall depth per strip height
PEBBLE_TILE = 1.56                                 # Poly Haven pebble_cemented_floor real size
RIPPLE_TILE = 3.0

# ------------------------------------------------------------------ lights (frames 15, 16, 12, 17)
LIGHTS = [  # (x, y, kind, z or None)
    (8.05, 28.5, "wall", -0.55),
    (4.40, 26.9, "wall", -0.55),
    (7.45, 26.30, "floor", None),
    (12.85, 26.55, "floor", None),
]

# ------------------------------------------------------------------ spa (frames 15, 20)
SPA = dict(cx=9.95, cy=17.25, size=2.3, base=6.2, plinth=0.12, top=7.02, coping=0.38, depth=0.72)


# ==================================================================================================
def apply(G):
    bpy = G.bpy
    G.remove("Pool_")
    G.remove("Spa")
    outline = closed_outline()
    normals = outward_normals(outline, smooth=3)
    star_check(outline)

    mats = materials(G)
    floor_z = lambda x, y: SHORE_Z - depth_field(x, y, outline)

    # --- coping
    cop = coping_mesh(outline, normals)
    fold_check(outline, normals)
    o = G.mesh("Pool_coping", cop[0], cop[1], "pool_coping", "Courtyard")
    smooth(o)

    # --- floor + walls (own UVs into the generated atlas)
    fv, ff, fuv = floor_mesh(outline, floor_z)
    o = G.mesh("Pool_shell_floor", fv, ff, "pool_shell", "Courtyard")
    set_uv(o, fuv)
    smooth(o)
    edge_depth = -np.array([floor_z(x, y) for x, y in outline]) + WATER_Z    # water depth at walls
    wall_info = wall_meshes(G, outline, floor_z)

    # --- water
    wv, wf = fan(outline + normals * 0.015, WATER_Z)
    w = G.mesh("Pool_water", wv, wf, "pool_water", "Courtyard")
    set_uv(w, [(x / RIPPLE_TILE, y / RIPPLE_TILE) for x, y, _ in wv])
    no_shadow(w)

    # --- dark pebble "river mouth" across the coping where the SE river meets the east tip (09, 17)
    pebble_mouth(G, outline, normals)

    # --- lights
    lights(G, outline, normals, floor_z)

    # --- the generated finish texture
    finish_texture(G, mats["pool_shell"], outline, wall_info, edge_depth)

    # --- hole in the ground slabs under the coping
    cut_ground(G, outline + normals * (COPING_W - 0.03))

    spa(G)

    cx, cy = outline.mean(axis=0)
    G.POOL = dict(cx=float(cx), cy=float(cy))
    G.POOL_OUTLINE = [tuple(map(float, p)) for p in outline]
    G.POOL_COPING = [tuple(map(float, p)) for p in outline + normals * COPING_W]
    warn_overlaps(G, outline + normals * COPING_W)

    G.SHOTS.update({
        "pool_top": ((8.75, 26.25, 40.0), (8.75, 26.25, 0.0), 85),          # exterior/15 (rectified crop)
        "pool_aerial": ((16.0, 18.5, 17.0), (8.6, 26.6, 0.0), 32),          # exterior/09
        "pool_beach": ((11.6, 22.0, 1.5), (5.5, 31.0, 0.8), 15),            # exterior/17
        "pool_east": ((11.6, 30.2, 1.5), (6.5, 19.5, 1.8), 16),             # exterior/11
        "spa_close": ((10.9, 8.8, 9.7), (9.9, 17.5, 6.7), 20),              # exterior/20
    })


# ================================================================================ outline helpers
def cr_open(pts, per_m=40):
    """Centripetal Catmull-Rom through pts (open; end points duplicated)."""
    P = [np.array(p, float) for p in pts]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        n = max(2, int(np.linalg.norm(P[i + 1] - P[i]) * per_m))
        out += cr_segment(P[i - 1], P[i], P[i + 1], P[i + 2], n)
    out.append(P[-2])
    return np.array(out)


def cr_segment(p0, p1, p2, p3, n, alpha=0.5):
    def tj(ti, a, b):
        return ti + max(np.linalg.norm(b - a), 1e-6) ** alpha
    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)
    out = []
    for t in np.linspace(t1, t2, n, endpoint=False):
        a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
        a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
        a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
        b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
        out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    return out


def resample_closed(dense, step):
    seg = np.linalg.norm(np.roll(dense, -1, 0) - dense, axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    n = max(8, int(round(L / step)))
    t = np.linspace(0, L, n, endpoint=False)
    ext = np.vstack([dense, dense[:1]])
    return np.stack([np.interp(t, s, ext[:, 0]), np.interp(t, s, ext[:, 1])], axis=1)


def closed_outline():
    P = [np.array(p, float) for p in WATER_CTRL]
    dense = []
    for i in range(len(P)):
        dense += cr_segment(P[i - 1], P[i], P[(i + 1) % len(P)], P[(i + 2) % len(P)], 24)
    pts = resample_closed(np.array(dense), STEP)
    area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    return pts if area > 0 else pts[::-1].copy()            # counter-clockwise


def outward_normals(pts, smooth=0):
    d = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    n = np.stack([d[:, 1], -d[:, 0]], axis=1)                # right of a CCW tangent = outward
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    for _ in range(smooth):
        n = n + 0.5 * (np.roll(n, 1, 0) + np.roll(n, -1, 0))
        n /= np.linalg.norm(n, axis=1, keepdims=True)
    return n


def star_check(pts):
    a = np.unwrap(np.arctan2(pts[:, 1] - CENTRE[1], pts[:, 0] - CENTRE[0]))
    if np.any(np.diff(a) <= 0):
        print("pool: WARNING outline is not star-shaped about CENTRE; floor fan may fold")


# ================================================================================ depth field
def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-12), 0, 1)
    return np.hypot(px - ax - t * dx, py - ay - t * dy)


def poly_dist(px, py, poly, closed=True, mask=None):
    poly = np.asarray(poly, float)
    d = np.full(np.shape(px), np.inf)
    n = len(poly) if closed else len(poly) - 1
    for i in range(n):
        if mask is not None and not mask[i]:
            continue
        a, b = poly[i], poly[(i + 1) % len(poly)]
        d = np.minimum(d, seg_dist(px, py, a[0], a[1], b[0], b[1]))
    return d


def inside(px, py, poly):
    poly = np.asarray(poly, float)
    res = np.zeros(np.shape(px), bool)
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[i - 1]
        cond = (ay > py) != (by > py)
        xin = (bx - ax) * (py - ay) / np.where(by - ay == 0, 1e-12, by - ay) + ax
        res ^= cond & (px < xin)
    return res


_SHORE = {}


def depth_field(x, y, outline):
    """Water depth of the floor (m): D_DEEP in the core, steep break, long beach slope to 0."""
    key = id(outline)
    if key not in _SHORE:
        flags = np.array([not DEEP_WALLS(px, py) for px, py in outline])
        _SHORE.clear()
        _SHORE[key] = flags & np.roll(flags, -1)             # segment i..i+1 is shoreline
    x, y = np.asarray(x, float), np.asarray(y, float)
    d_shore = poly_dist(x, y, outline, True, _SHORE[key])
    d_core = np.where(inside(x, y, CORE), 0.0, poly_dist(x, y, CORE))
    t = d_core / (d_core + d_shore + 1e-6)
    brk = 1 - np.clip(t / T_BREAK, 0, 1)
    brk = brk * brk * (3 - 2 * brk)
    prof = (1 - t) * (SHELF + (1 - SHELF) * brk)
    depth = D_DEEP * prof
    for poly, dmax, soft in SHELVES:
        shelf = np.minimum(depth, dmax * np.clip(d_shore / 1.1, 0, 1) ** 0.8)
        w = inside(x, y, poly).astype(float)
        if soft > 0:
            w = w * np.clip(poly_dist(x, y, poly) / soft, 0, 1)
            w = w * w * (3 - 2 * w)
        depth = depth + (shelf - depth) * w
    return depth


def palette(depth):
    d = np.clip(depth, 0, None)
    ks = np.array([k for k, _ in PALETTE])
    cs = np.array([c for _, c in PALETTE])
    return np.stack([np.interp(d, ks, cs[:, i]) for i in range(3)], axis=-1)


# ================================================================================ geometry
def coping_mesh(outline, normals):
    W = COPING_W
    prof = [(0.0, -0.075), (-0.03, -0.068), (-0.045, -0.04), (-0.044, -0.005), (-0.034, 0.024),
            (-0.014, 0.041), (0.02, COPING_TOP), (W - 0.03, COPING_TOP), (W - 0.004, COPING_TOP - 0.006),
            (W + 0.004, -0.12)]
    n = len(outline)
    verts = []
    for d, z in prof:
        for (x, y), (nx, ny) in zip(outline, normals):
            verts.append((x + nx * d, y + ny * d, z))
    faces = []
    for j in range(len(prof) - 1):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n
            faces.append((a, a + n, b + n, b))
    return verts, faces


def fold_check(outline, normals):
    outer = outline + normals * COPING_W
    t_in = np.roll(outline, -1, 0) - outline
    t_out = np.roll(outer, -1, 0) - outer
    bad = np.sum(t_in * t_out, axis=1) <= 0
    if bad.any():
        print("pool: WARNING coping folds at", outline[bad].round(2).tolist())


def floor_mesh(outline, floor_z, K=18):
    cx, cy = CENTRE
    n = len(outline)
    ts = [1 - (1 - k / K) ** 1.5 for k in range(1, K + 1)]
    verts = [(cx, cy)]
    for t in ts:
        for x, y in outline:
            verts.append((cx + (x - cx) * t, cy + (y - cy) * t))
    verts = np.array(verts)
    z = floor_z(verts[:, 0], verts[:, 1])
    faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    for k in range(K - 1):
        for i in range(n):
            a, b = 1 + k * n + i, 1 + k * n + (i + 1) % n
            faces.append((a, a + n, b + n, b))
    uv = [floor_uv(x, y) for x, y in verts]
    return [(x, y, zz) for (x, y), zz in zip(verts, z)], faces, uv


def floor_uv(x, y):
    return ((x - FLOOR_X0) / FLOOR_L, FLOOR_V0 + (y - FLOOR_Y0) / FLOOR_L)


def wall_meshes(G, outline, floor_z):
    """Two vertical strips (one per atlas row) from under the coping down to the floor edge."""
    n = len(outline)
    seg = np.linalg.norm(np.roll(outline, -1, 0) - outline, axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    half = n // 2
    rows = [list(range(0, half + 1)), list(range(half, n)) + [0]]
    info = []
    for r, idx in enumerate(rows):
        s0 = s[idx[0]]
        s_vals = [(s[i] if i != 0 or k == 0 else s[-1]) - s0 for k, i in enumerate(idx)]
        length = s_vals[-1]
        v0, v1 = WALL_ROWS[r]
        verts, uvs = [], []
        for k, i in enumerate(idx):
            x, y = outline[i]
            zb = min(float(floor_z(x, y)), -0.005)
            u = 0.01 + 0.98 * s_vals[k] / length
            verts += [(x, y, 0.0), (x, y, zb)]
            uvs += [(u, v0), (u, v0 + (v1 - v0) * (-zb) / WALL_SPAN)]
        faces = [(2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1) for k in range(len(idx) - 1)]
        o = G.mesh(f"Pool_shell_walls_{r}", verts, faces, "pool_shell", "Courtyard")
        set_uv(o, uvs)
        smooth(o)
        info.append(dict(idx=idx, s=np.array(s_vals), length=length, v0=v0, v1=v1))
    return info


def fan(pts, z):
    cx, cy = CENTRE
    verts = [(cx, cy, z)] + [(x, y, z) for x, y in pts]
    n = len(pts)
    return verts, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]


def set_uv(o, uvs):
    """Per-vertex UVs (list indexed like the mesh vertices)."""
    me = o.data
    lay = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers.active
    data = lay.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            data[li].uv = uvs[me.loops[li].vertex_index]


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True


def no_shadow(o):
    o.visible_shadow = False              # Cycles: sun reaches the floor through the water


# ================================================================================ materials
def materials(G):
    bpy = G.bpy
    M = {}
    G.mat("pool_coping", (0.74, 0.70, 0.60), 0.7)
    G.pbr("pool_coping", "pebble_cemented_floor", PEBBLE_TILE, (0.90, 0.80, 0.60), 0.2)   # 11 / 17 / 09
    M["pool_coping"] = G.MAT["pool_coping"]

    # shell: base colour = generated atlas, pebble normal tiled through a Mapping node
    m = G.mat("pool_shell", (0.4, 0.6, 0.55), 0.6)
    nt = m.node_tree
    n, ln = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    bsdf.inputs["Specular IOR Level"].default_value = 0.12    # under water: plaster/water IOR ratio ~1.1
    tex = n.new("ShaderNodeTexImage")
    tex.name = "finish"
    ln.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    uvn = n.new("ShaderNodeUVMap")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (FLOOR_L / PEBBLE_TILE, FLOOR_L / PEBBLE_TILE, 1)
    ln.new(uvn.outputs["UV"], mp.inputs["Vector"])
    nrm = n.new("ShaderNodeTexImage")
    nrm.image = bpy.data.images.load(os.path.join(G.TEX_DIR, "pebble_cemented_floor", "nor.jpg"),
                                     check_existing=True)
    nrm.image.colorspace_settings.name = "Non-Color"
    ln.new(mp.outputs["Vector"], nrm.inputs["Vector"])
    nm = n.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.6
    ln.new(nrm.outputs["Color"], nm.inputs["Color"])
    ln.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    M["pool_shell"] = m

    # water: clear, slightly aqua transmission + ripple normals
    m = G.mat("pool_water", (0.86, 0.97, 0.95), 0.03, transmission=1.0)
    nt = m.node_tree
    n, ln = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    bsdf.inputs["IOR"].default_value = 1.333
    for k in [l for l in nt.links if l.to_socket in (bsdf.inputs["Base Color"], bsdf.inputs["Normal"])]:
        ln.remove(k)
    rip = n.new("ShaderNodeTexImage")
    rip.image = packed_image(bpy, "pool_ripple_normal", ripple_normal(512), colour=False)
    nm = n.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.0
    ln.new(rip.outputs["Color"], nm.inputs["Color"])
    ln.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    M["pool_water"] = m

    G.mat("pool_light_lens", (0.9, 0.95, 1.0), 0.15, emit=((0.75, 0.9, 1.0), 2.5))
    G.mat("pool_light_ring", (0.85, 0.85, 0.86), 0.25, 1.0)
    return M


def packed_image(bpy, name, arr, colour=True, fmt="JPEG"):
    """arr: (H, W, 3) display-space floats (row 0 = bottom). Packed into the .blend / glTF."""
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=False)
    im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    px = np.ones((h, w, 4), np.float32)
    px[..., :3] = np.clip(arr, 0, 1)
    im.pixels.foreach_set(px.ravel())
    ext = "jpg" if fmt == "JPEG" else "png"
    tmp = os.path.join(tempfile.gettempdir(), f"{name}_{os.getpid()}.{ext}")
    im.filepath_raw = tmp
    im.file_format = fmt
    im.save(quality=92) if fmt == "JPEG" else im.save()
    im.pack()
    im.filepath_raw = f"//{name}.{ext}"
    os.remove(tmp)
    return im


def to_srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)


def to_lin(s):
    return np.where(s <= 0.04045, s / 12.92, np.power((s + 0.055) / 1.055, 2.4))


def value_noise(shape, cells, rng):
    cy, cx = cells
    g = rng.standard_normal((cy + 2, cx + 2)).astype(np.float32)
    H, W = shape
    y = np.linspace(0, cy, H, endpoint=False)
    x = np.linspace(0, cx, W, endpoint=False)
    yi, xi = y.astype(int), x.astype(int)
    fy, fx = (y - yi)[:, None], (x - xi)[None, :]
    sy, sx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b = g[yi][:, xi], g[yi][:, xi + 1]
    c, d = g[yi + 1][:, xi], g[yi + 1][:, xi + 1]
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy


def ripple_normal(res, seed=7):
    """Tileable wind-ripple normal map (RIPPLE_TILE metres), RMS slope ~0.05."""
    rng = np.random.default_rng(seed)
    u = np.arange(res) / res
    U, V = np.meshgrid(u, u)
    sx = np.zeros((res, res))
    sy = np.zeros((res, res))
    for _ in range(48):
        kx, ky = rng.integers(-16, 17, 2)
        kk = math.hypot(kx, ky)
        if kk < 3:
            continue
        a = rng.uniform(0.4, 1.0) / kk ** 1.6
        arg = 2 * math.pi * (kx * U + ky * V) + rng.uniform(0, 2 * math.pi)
        c = np.cos(arg)
        sx += a * kx * c
        sy += a * ky * c
    rms = math.sqrt(float(np.mean(sx * sx + sy * sy)))
    sx *= 0.05 / rms
    sy *= 0.05 / rms
    nz = 1 / np.sqrt(1 + sx * sx + sy * sy)
    return np.stack([(-sx * nz) * 0.5 + 0.5, (-sy * nz) * 0.5 + 0.5, nz * 0.5 + 0.5], axis=-1)


# ================================================================================ finish texture
def load_pebble(bpy, tex_dir):
    im = bpy.data.images.load(os.path.join(tex_dir, "pebble_cemented_floor", "diff.jpg"), check_existing=True)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    a = to_lin(a.reshape(h, w, 4)[..., :3])
    a = 0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])    # 2x box filter
    return a / a.mean(axis=(0, 1))


def sample_tile(src, xm, ym, tile):
    """Bilinear, wrapping sample of a tiling texture at metric coords."""
    h, w = src.shape[:2]
    fx = (xm / tile % 1.0) * w
    fy = (ym / tile % 1.0) * h
    x0, y0 = np.floor(fx).astype(int) % w, np.floor(fy).astype(int) % h
    x1, y1 = (x0 + 1) % w, (y0 + 1) % h
    tx, ty = (fx - np.floor(fx))[..., None], (fy - np.floor(fy))[..., None]
    return (src[y0, x0] * (1 - tx) * (1 - ty) + src[y0, x1] * tx * (1 - ty)
            + src[y1, x0] * (1 - tx) * ty + src[y1, x1] * tx * ty)


def upsample(a, H, W):
    h, w = a.shape
    ys = np.linspace(0, h - 1, H)
    xs = np.linspace(0, w - 1, W)
    tmp = np.stack([np.interp(xs, np.arange(w), row) for row in a])
    return np.stack([np.interp(ys, np.arange(h), col) for col in tmp.T], axis=1)


def rasterize_lines(mask, lines, px_per_m, origin, rng, noise, taper=False):
    """Max-accumulate soft coverage of variable-width polylines into mask (H, W)."""
    H, W = mask.shape
    ox, oy = origin
    for pts, hw in lines:
        P = cr_open(pts, per_m=30)
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        wob = value_noise((1, len(P)), (1, max(2, int(L[-1] / 0.35))), rng)[0]
        widths = hw * (1 + 0.35 * wob)
        if taper:
            e = np.clip(np.minimum(L, L[-1] - L) / 0.25, 0, 1)
            widths = widths * (0.35 + 0.65 * e)
        for i in range(len(P) - 1):
            (ax, ay), (bx, by) = P[i], P[i + 1]
            wm = max(widths[i], widths[i + 1])
            r = (wm * 1.5 + 0.02) * px_per_m
            c0 = int(max(0, min(ax, bx) * px_per_m - ox - r))
            c1 = int(min(W, max(ax, bx) * px_per_m - ox + r + 1))
            r0 = int(max(0, min(ay, by) * px_per_m - oy - r))
            r1 = int(min(H, max(ay, by) * px_per_m - oy + r + 1))
            if c0 >= c1 or r0 >= r1:
                continue
            cc, rr = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
            xm, ym = (cc + 0.5 + ox) / px_per_m, (rr + 0.5 + oy) / px_per_m
            d = seg_dist(xm, ym, ax, ay, bx, by)
            ww = 0.5 * (widths[i] + widths[i + 1]) * (1 + 0.45 * noise[r0:r1, c0:c1])
            cov = np.clip((ww - d) * px_per_m / 1.5 + 0.5, 0, 1)
            mask[r0:r1, c0:c1] = np.maximum(mask[r0:r1, c0:c1], cov)


def finish_texture(G, mat, outline, wall_info, edge_depth):
    """Bake the finish as seen through the water into one atlas (floor region + wall strips)."""
    bpy = G.bpy
    rng = np.random.default_rng(1159)
    pebble = load_pebble(bpy, G.TEX_DIR)
    out = np.zeros((TEX, TEX, 3), np.float32)

    # ---- floor region: depth on a coarse grid, upsampled
    ppm = TEX / FLOOR_L
    r0 = int(FLOOR_V0 * TEX)
    Hf = TEX - r0
    gs = 256
    gx = FLOOR_X0 + (np.arange(gs) + 0.5) / gs * FLOOR_L
    gy = FLOOR_Y0 + (np.arange(gs) + 0.5) / gs * (Hf / ppm)
    GX, GY = np.meshgrid(gx, gy)
    dep = depth_field(GX, GY, outline)
    dep = upsample(dep, Hf, TEX)
    cols = np.arange(TEX)
    rows = np.arange(Hf)
    XM = FLOOR_X0 + (cols[None, :] + 0.5) / ppm + 0 * rows[:, None]
    YM = FLOOR_Y0 + (rows[:, None] + 0.5) / ppm + 0 * cols[None, :]
    mott = value_noise((Hf, TEX), (int(Hf / ppm / 0.8), int(FLOOR_L / 0.8)), rng)
    base = palette(dep) * (1 + 0.05 * mott[..., None])
    det = sample_tile(pebble, XM, YM, PEBBLE_TILE)
    k = np.interp(dep, [0.0, 0.5, 1.8], [0.95, 0.7, 0.5])[..., None]
    col = base * np.power(np.clip(det, 0.05, None), k)
    # contour lines
    noise = value_noise((Hf, TEX), (int(Hf / ppm / 0.12), int(FLOOR_L / 0.12)), rng)
    river = np.zeros((Hf, TEX), np.float32)
    arcs = np.zeros((Hf, TEX), np.float32)
    origin = (FLOOR_X0 * ppm, FLOOR_Y0 * ppm)
    rasterize_lines(river, RIVERS, ppm, origin, rng, noise)
    rasterize_lines(arcs, [(a, ARC_W) for a in ARCS], ppm, origin, rng, 0.4 * noise, taper=True)
    dark = np.array([0.06, 0.05, 0.035]) * np.power(np.clip(det, 0.05, None), 1.5) + 0.08 * base
    col = col * (1 - river[..., None]) + dark * river[..., None]
    col = col * (1 - 0.75 * arcs[..., None])
    out[r0:] = col

    # ---- wall strips: depth gradient + pebble, colour keyed to the floor depth at the edge
    for info in wall_info:
        v0, v1 = info["v0"], info["v1"]
        ra, rb = int(v0 * TEX), int(math.ceil(v1 * TEX))
        rr = np.arange(ra, rb)
        zd = (rr + 0.5) / TEX - v0
        zd = np.clip(zd / (v1 - v0), 0, None) * WALL_SPAN                         # m below z=0
        u = (cols + 0.5) / TEX
        sv = np.clip((u - 0.01) / 0.98, 0, 1) * info["length"]
        idx = np.array(info["idx"])
        ed = np.interp(sv, info["s"], edge_depth[idx])                             # floor depth at edge
        wd = np.minimum(np.maximum(zd[:, None] + WATER_Z, 0.0), ed[None, :])
        base = palette(wd)
        det = sample_tile(pebble, sv[None, :] + 0 * zd[:, None], zd[:, None] + 0 * sv[None, :], PEBBLE_TILE)
        kk = np.interp(wd, [0.0, 0.5, 1.8], [0.9, 0.65, 0.5])[..., None]
        out[ra:rb] = base * np.power(np.clip(det, 0.05, None), kk)

    img = packed_image(bpy, "pool_finish", to_srgb(out), colour=True)
    mat.node_tree.nodes["finish"].image = img


# ================================================================================ lights
def lights(G, outline, normals, floor_z):
    bpy = G.bpy
    lens = disc_mesh(bpy, "Pool_light_lens_mesh", 0.11, 0.012, G.MAT["pool_light_lens"])
    ring = ring_mesh(bpy, "Pool_light_ring_mesh", 0.11, 0.15, 0.016, G.MAT["pool_light_ring"])
    from mathutils import Vector
    for i, (x, y, kind, z) in enumerate(LIGHTS):
        if kind == "wall":
            j = int(np.argmin(np.hypot(outline[:, 0] - x, outline[:, 1] - y)))
            px, py = outline[j]
            nx, ny = -normals[j]
            zb = float(floor_z(px, py))
            z = max(z, zb + 0.25)
            loc = Vector((px + nx * 0.003, py + ny * 0.003, z))
            nrm = Vector((nx, ny, 0.0))
        else:
            e = 0.05
            zc = float(floor_z(x, y))
            gx = (float(floor_z(x + e, y)) - float(floor_z(x - e, y))) / (2 * e)
            gy = (float(floor_z(x, y + e)) - float(floor_z(x, y - e))) / (2 * e)
            nrm = Vector((-gx, -gy, 1.0)).normalized()
            loc = Vector((x, y, zc)) + nrm * 0.003
        rot = Vector((0, 0, 1)).rotation_difference(nrm).to_euler()
        for nm, me in (("lens", lens), ("ring", ring)):
            o = bpy.data.objects.new(f"Pool_light_{i}_{nm}", me)
            o.location = loc
            o.rotation_euler = rot
            bpy.context.scene.collection.objects.link(o)
            G.link(o, "Courtyard")


def disc_mesh(bpy, name, r, h, mat, seg=20):
    verts = [(0, 0, h)] + [(r * math.cos(a), r * math.sin(a), h) for a in np.linspace(0, 2 * math.pi, seg, endpoint=False)]
    verts += [(r * math.cos(a), r * math.sin(a), 0) for a in np.linspace(0, 2 * math.pi, seg, endpoint=False)]
    faces = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    faces += [(1 + i, 1 + seg + i, 1 + seg + (i + 1) % seg, 1 + (i + 1) % seg) for i in range(seg)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(mat)
    return me


def ring_mesh(bpy, name, r0, r1, h, mat, seg=20):
    A = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    verts = [(r0 * math.cos(a), r0 * math.sin(a), h) for a in A] + [(r1 * math.cos(a), r1 * math.sin(a), h * 0.4) for a in A]
    verts += [(r1 * math.cos(a), r1 * math.sin(a), 0) for a in A]
    faces = [(i, seg + i, seg + (i + 1) % seg, (i + 1) % seg) for i in range(seg)]
    faces += [(seg + i, 2 * seg + i, 2 * seg + (i + 1) % seg, seg + (i + 1) % seg) for i in range(seg)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return me


def pebble_mouth(G, outline, normals):
    """Irregular brown pebble patch laid flush on the coping top at the SE river's end."""
    x, y = MOUTH["at"]
    j = int(np.argmin(np.hypot(outline[:, 0] - x, outline[:, 1] - y)))
    n = len(outline)
    step = float(np.mean(np.linalg.norm(np.roll(outline, -1, 0) - outline, axis=1)))

    def at(ds, d):                                  # point ds metres along the edge, d out from it
        f = j + ds / step
        i0 = int(math.floor(f))
        t = f - i0
        p = outline[i0 % n] * (1 - t) + outline[(i0 + 1) % n] * t
        q = normals[i0 % n] * (1 - t) + normals[(i0 + 1) % n] * t
        return p + q / np.linalg.norm(q) * d

    rng = np.random.default_rng(3)
    cols = 9
    verts, faces = [], []
    for r, d in enumerate(MOUTH["rings"]):
        hl = MOUTH["half_len"] * (1 - 0.5 * (d / COPING_W) ** 2) * rng.uniform(0.8, 1.05)
        for c in range(cols):
            px, py = at(hl * (2 * c / (cols - 1) - 1), d)
            verts.append((px, py, COPING_TOP + 0.002))
        if r:
            a, b = (r - 1) * cols, r * cols
            faces += [(a + c, b + c, b + c + 1, a + c + 1) for c in range(cols - 1)]
    G.mat("pool_pebble_dark", (0.30, 0.24, 0.17), 0.8)
    G.pbr("pool_pebble_dark", "pebble_cemented_floor", PEBBLE_TILE, (0.62, 0.50, 0.36), 1.0)
    G.mesh("Pool_pebble_mouth", verts, faces, "pool_pebble_dark", "Courtyard")


# ================================================================================ ground hole
def cut_ground(G, hole):
    """Boolean the coping footprint out of every flat ground slab (turf, lot ground) under it."""
    bpy = G.bpy
    n = len(hole)
    verts = [(x, y, -1.0) for x, y in hole] + [(x, y, 1.0) for x, y in hole]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    cutter = G.mesh("Pool_cutter", verts, faces, "pool_coping")
    hx0, hy0 = hole.min(axis=0)
    hx1, hy1 = hole.max(axis=0)
    for o in list(bpy.data.objects):
        if o.type != "MESH" or o.name.startswith(("Pool_", "Spa")) or o.data.users > 1:
            continue
        bb = [o.matrix_world @ G.Vector(c) for c in o.bound_box]
        x0, x1 = min(p.x for p in bb), max(p.x for p in bb)
        y0, y1 = min(p.y for p in bb), max(p.y for p in bb)
        z0, z1 = min(p.z for p in bb), max(p.z for p in bb)
        if x1 < hx0 or x0 > hx1 or y1 < hy0 or y0 > hy1:
            continue
        flat = z1 <= 0.06 and z0 >= -0.3
        covers = (min(x1, hx1) - max(x0, hx0)) * (min(y1, hy1) - max(y0, hy0)) > 0.5 * (hx1 - hx0) * (hy1 - hy0)
        if not (flat and covers):
            continue
        mod = o.modifiers.new("pool_hole", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = cutter
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        print("pool: cut pool hole in", o.name)
    me = cutter.data
    bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.data.meshes.remove(me)


def warn_overlaps(G, coping):
    """Report other modules' objects standing inside the pool footprint (for integration)."""
    bpy = G.bpy
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.startswith(("Pool_", "Spa")) or not o.visible_get():
            continue
        if o.users_collection and o.users_collection[0].name == "Library":
            continue
        bb = [o.matrix_world @ G.Vector(c) for c in o.bound_box]
        z0 = min(p.z for p in bb)
        if z0 > 0.5 or max(p.z for p in bb) < 0.0:
            continue
        if max(p.x for p in bb) - min(p.x for p in bb) > 12 or max(p.y for p in bb) - min(p.y for p in bb) > 12:
            continue                                            # ground slabs (already cut)
        cx = sum(p.x for p in bb) / 8
        cy = sum(p.y for p in bb) / 8
        if inside(np.array([cx]), np.array([cy]), coping)[0]:
            print("pool: WARNING", o.name, "stands inside the pool footprint")


# ================================================================================ spa
def spa(G):
    """Raised roof-deck spa: beige plinth, reddish timber sides, wide tan coping, foaming water."""
    bpy = G.bpy
    S = SPA
    h = S["size"] / 2
    x0, x1, y0, y1 = S["cx"] - h, S["cx"] + h, S["cy"] - h, S["cy"] + h
    G.mat("spa_timber", (0.30, 0.14, 0.08), 0.6)
    G.pbr("spa_timber", "wood_floor_deck", 1.6, (0.30, 0.13, 0.07), 0.7)
    G.mat("spa_stone", (0.62, 0.54, 0.42), 0.75)
    G.pbr("spa_stone", "concrete_floor_02", 2.0, (0.64, 0.55, 0.42), 0.4)
    G.mat("spa_plaster", (0.30, 0.55, 0.55), 0.5)
    top, cop = S["top"], S["coping"]
    zb = S["base"] + S["plinth"]
    G.box("Spa_plinth", x0 - 0.06, y0 - 0.06, S["base"], x1 + 0.06, y1 + 0.06, zb, "spa_stone", "RoofDeck")
    t = 0.06                                                    # timber skin
    ct = 0.07                                                   # coping slab thickness
    for nm, b in {"s": (x0, y0, x1, y0 + t), "n": (x0, y1 - t, x1, y1),
                  "w": (x0, y0 + t, x0 + t, y1 - t), "e": (x1 - t, y0 + t, x1, y1 - t)}.items():
        G.box(f"Spa_side_{nm}", b[0], b[1], zb, b[2], b[3], top - ct, "spa_timber", "RoofDeck")
    o = 0.04                                                    # coping overhang
    ix0, ix1, iy0, iy1 = x0 + cop, x1 - cop, y0 + cop, y1 - cop
    for nm, b in {"s": (x0 - o, y0 - o, x1 + o, iy0), "n": (x0 - o, iy1, x1 + o, y1 + o),
                  "w": (x0 - o, iy0, ix0, iy1), "e": (ix1, iy0, x1 + o, iy1)}.items():
        G.box(f"Spa_coping_{nm}", b[0], b[1], top - ct, b[2], b[3], top, "spa_stone", "RoofDeck")
    # basin: inward-facing walls + floor (+ bench ledge)
    zf = top - S["depth"]
    v = [(ix0, iy0, zf), (ix1, iy0, zf), (ix1, iy1, zf), (ix0, iy1, zf),
         (ix0, iy0, top - ct), (ix1, iy0, top - ct), (ix1, iy1, top - ct), (ix0, iy1, top - ct)]
    f = [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    G.mesh("Spa_basin", v, f, "spa_plaster", "RoofDeck")
    b = 0.38
    G.box("Spa_bench", ix0, iy0, zf, ix1, iy0 + b, zf + 0.38, "spa_plaster", "RoofDeck")
    # water with jet foam
    m = bpy.data.materials.get("spa_water")
    if m is None:
        m = G.mat("spa_water", (0.6, 0.85, 0.85), 0.08, transmission=1.0)
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["IOR"].default_value = 1.333
        col, trans = spa_foam(128)
        tc = nt.nodes.new("ShaderNodeTexImage")
        tc.image = packed_image(bpy, "spa_foam_color", col)
        nt.links.new(tc.outputs["Color"], bsdf.inputs["Base Color"])
        tt = nt.nodes.new("ShaderNodeTexImage")
        tt.image = packed_image(bpy, "spa_foam_transmission", trans, colour=False)
        nt.links.new(tt.outputs["Color"], bsdf.inputs["Transmission Weight"])
    zw = top - 0.1
    e = 0.01
    w = G.mesh("Spa_water", [(ix0 - e, iy0 - e, zw), (ix1 + e, iy0 - e, zw), (ix1 + e, iy1 + e, zw),
                             (ix0 - e, iy1 + e, zw)], [(0, 1, 2, 3)], "spa_water", "RoofDeck")
    set_uv(w, [(0, 0), (1, 0), (1, 1), (0, 1)])
    no_shadow(w)


def spa_foam(res, seed=20):
    rng = np.random.default_rng(seed)
    f = sum(value_noise((res, res), (c, c), rng) * a for c, a in ((3, 1.0), (7, 0.5), (15, 0.3), (31, 0.15)))
    u = (np.arange(res) + 0.5) / res
    U, V = np.meshgrid(u, u)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    jets = np.exp(-((edge - 0.12) / 0.08) ** 2)                 # foam boils up along the seat jets
    foam = np.clip((f * 0.6 + jets * 0.9 - 0.28) * 2.2, 0, 1)
    water = np.array(to_srgb(np.array([0.30, 0.55, 0.56])))
    white = np.array([0.93, 0.95, 0.95])
    col = water * (1 - foam[..., None]) + white * foam[..., None]
    trans = np.repeat((1 - 0.92 * foam)[..., None], 3, axis=2)
    return col, trans
