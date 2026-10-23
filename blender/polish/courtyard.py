"""Courtyard furniture, macrame cabanas, umbrellas and boundary walls (polish module "courtyard").

Owns Cabana*, Umbrella*, Lounge_*, Pavilion_bench, the two outdoor_table_chair_set_01 copies (rear
terrace + roof deck, replaced) and every new Yard_* object.  Geometry is built directly as meshes (no
modifiers); repeated pieces (chairs, cushions, cabana parts) are linked duplicates of one mesh.  The
woven / macrame looks come from small textures generated here with numpy and packed into the file
(Principled BSDF + image textures, alpha-clipped where the weave is open), so it all exports to glTF.

Video evidence (frames/exterior/...):
- 15_top-down-site-plan-night (+ generated/01_site-plan): the plan; positions were scaled on the
  lot walls, the hip-roof eave and the pool's straight N / W walls (west deck) and on the bulkhead /
  spa (roof deck).  West strip, from the house: raised timber deck with lights along the pool edge;
  long white dining table under one big octagonal cantilever umbrella whose pole stands on the
  planting side; then the lounge - straight white sofa against the west bed, oval coffee table, a teak
  armchair at each end of it, small white side table.  East strip: two macrame cabanas against the
  boundary wall beside the pool's beach lobe, white poufs; low slatted timber platform before the
  pavilion's kitchen bay.  Roof: slatted table just south of the pergola (3 chairs a side + one at the
  west end); sofa east of the spa facing two round rope chairs at the east parapet, round tables.
- 08_courtyard-aerial-night, 21_courtyard-aerial-angle: concrete-top table with chamfered corners,
  teak chairs with woven backs, umbrella over the table's pavilion end; cabanas with white floor
  cushions and rattan drum bases; white boundary walls running on past the pavilion to the alley.
- 10_courtyard-from-living-doors, 13 (cabana half), 16_pool-toward-pavilion-dusk: cabana = 12-sided
  crochet / macrame cone (rise ~ radius, dense work with small holes, diamond lattice, solid bands),
  fringe, brass finial, wood pole in a rattan drum; along the wall: floor chair with a rounded back +
  flat cushion | drum | long cushion with two black / white print pillows | drum | floor chair; east
  wall ~1.8 m white stucco with a timber lattice screen on the neighbour's side.
- 11, 12, 16, 17: two honey-rattan tulip swivel chairs (drum base, bowl widening to the rim, sides
  cut down to the seat) + rattan drum table on the grass at the terrace's east end, facing the pool.
- 11_courtyard-pool-pavilion-day: dining table along the west wall (teak chairs, woven end chair,
  white slab pedestals) under the cantilever umbrella; white market umbrella over two teak sun
  loungers at the house end of the west side.  12_courtyard-house-rear-dusk: same, from the east.
- 13_courtyard-lounge-dusk: teak-framed armchairs (white cushions, dark round / print pillows), white
  oval pedestal coffee table with a bronze succulent bowl, white sofa with black/white print pillows,
  grey kubu-wicker balloon-back chair at the table's end.
- 17_pool-beach-entry-day, 09: west boundary wall with planting in front of it, deck and lounge along
  it; timber platform with two step lights across the pavilion's kitchen bay.
- 18_rooftop-lounge, 19_rooftop-deck-view: teak / rope sofa, round woven-rope lounge chairs with
  white cushions, two nesting light-wood tables; long weathered-teak slatted table with rope armchairs.
The layout follows the pool module's outline (blender/polish/pool.py, which runs later and replaces
the base kidney pool): see pool_footprint() / spa_east_x().
"""
import ast
import math
import os
import tempfile

import bpy
import numpy as np
from mathutils import Matrix, Vector

POLYHAVEN_ASSETS = ["teak_veneer"]      # furniture timber (diff/nor/rough 1k in assets/textures/)

COLL, ROOF = "Courtyard", "RoofDeck"
TAU = 2 * math.pi

# ---------------------------------------------------------------- boundary walls (08, 11, 13, 16, 21)
# From the house's rear wall past the pavilion's sides to the alley (08, 21: the walls continue
# beside the pavilion); the cap ends flush with the lot line.
WALL = dict(y0=19.0, y1=38.37, h=1.8, t=0.25, cap_h=0.06, cap_over=0.03)
LATTICE = dict(y0=21.0, y1=31.0, dx=0.34, h=0.62, tile=1.0, post=2.5)  # neighbour's side, clear of canopies

# ---------------------------------------------------------------- west deck (08, 15, 16, 17)
WDECK = dict(x0=1.45, x1_max=4.2, y0=19.0, y_terrace=21.6, y1=30.15, gap=0.1)   # top = terrace top
# Plan positions from the top-down frame 15 (scaled on the pool's straight N / W walls), order from
# the house: long dining table with the cantilever umbrella over its pavilion end (08, 13, 15) ->
# lounge (sofa on the west, two teak armchairs, oval coffee table) -> planting at the pavilion's west bay.
DINING = dict(x=2.8, y=24.0, length=3.0, width=0.95)        # long axis along y (08, 11, 15, 17)
DINING_SIDE_Y = (-0.98, -0.33, 0.33, 0.98)                   # 4 teak chairs a side (08, 17), woven at the ends
DINING_END_GAP = 0.31                                        # woven chair centre beyond the table end
# frame 15: canopy centre ~(3.5, 25.15), reaching over the deck lights; pole west of it at ~(2.0, 26.0)
CANTILEVER = dict(pole=(2.0, 26.05), aim=(3.4, 25.3), r=1.45, gap=0.25, z_edge=2.32, z_hub=2.78, z_arm=3.0)
SOFA = dict(x_back=1.5, y0=26.9, y1=29.3)                    # straight 3-seater, back to the west bed
COFFEE = (2.98, 27.85)
ARMCHAIRS = [(3.0, 26.55, math.pi / 2), (3.25, 29.15, None)]  # x, y, facing (None: face the table)
SIDE_TABLE = (2.66, 29.72, 0.2, 0.45)                        # x, y, r, h: white drum by the sofa end
DECK_LIGHT_STEP = 0.85

# ---------------------------------------------------------------- rear terrace (11, 12, 16, 17)
# Egg chairs stand on the grass in front of the terrace's east end (east of the steps), facing the
# pool, with a small rattan drum table between them (11, 12, 16, 17).
EGG_CHAIRS = [(12.44, 22.52), (13.44, 22.52)]
EGG_TABLE = (12.94, 22.9, 0.18, 0.46)                        # x, y, r, h
LOUNGERS = [(3.95, 20.35), (4.8, 20.35)]
MARKET = dict(pole=(4.375, 20.3), r=1.2, z_edge=2.15, z_top=2.6)

# ---------------------------------------------------------------- east side cabanas (09, 10, 13, 15, 16)
# Canopies ~2.3 m across, rise ~= radius (10, 13, 16), east edge just over the wall cap (15).
# Order along the wall (13, 10, 12): [pot] floor chair + flat cushion | drum A | long cushion with two
# print pillows | drum B | floor chair + flat cushion [pot], white pouf by B.  Frame 15 puts drum B
# ~0.7 m house-side of the pool's east tip and A ~2.05 m beyond it (y ~25.35 / 28.1 on the pool
# module's outline); the planting module's pots at y 25.55 / 28.75 / 29.75 (planting.py POTS) only
# leave room for the pair below.  Once planting moves its pot at y 25.55 to ~24.0 and drops the one at
# 28.75, set the y values to 25.35 / 28.1 and POUFS[1] to (13.3, 29.4) (critique.md, item 5).
CABANAS = [(14.2, 24.25, -1), (14.2, 27.3, 1)]      # x, y, outer side (-1 house, +1 pavilion): B, A
CABANA = dict(r=1.15, z_edge=1.88, z_top=3.0, fringe=0.28, sides=12, drum_r=0.29, drum_h=0.58)
SEAT_X = 14.69              # floor-seat centre line, backs against the wall (inner face x 15.05)
SEAT, SEAT_GAP = 0.62, 0.06  # square floor cushion size; gap to the drum
LONG_SEAT = 1.05            # long floor cushion between the drums (A side)
POUFS = [(13.0, 23.35), (13.5, 28.9)]

# ---------------------------------------------------------------- pavilion bench (09, 15, 17, 21)
# Low slatted timber platform across the pavilion's kitchen bay, dark kick, two step lights (17).
# West end kept clear of the planting module's pot at (9.6, 30.45).
BENCH = dict(x0=9.95, x1=14.3, depth=0.85, h=0.33, lights=(1.1, 3.25))   # lights: x from x0

# ---------------------------------------------------------------- roof deck (15, 18, 19)
# Frame 15 (roof level ~110 px/m on a 2x crop): long table just south of the pergola, 3 chairs a
# side + one at the west end; lounge east of the spa: sofa facing east, round coffee table, two round
# rope chairs against the east parapet facing west, small side table between them (also 18).
ROOF_DINING = dict(x=12.1, y=10.0, length=2.4, width=1.0)    # long axis along x
ROOF_DINING_DX = (-0.75, 0.0, 0.75)
ROOF_SOFA = dict(y=17.6, length=2.0, depth=0.78, gap=0.06)   # back sits `gap` east of the spa
ROOF_ROUND = dict(x=13.06, ys=(16.82, 18.22), scale=0.88)     # facing west
ROOF_COFFEE = dict(y=17.55, r=0.27, h=0.36)
ROOF_NEST = (12.3, 17.05, 0.22, 0.28)                         # lower nesting table (18): x, y, r, h
ROOF_SIDE = (13.36, 17.52, 0.15, 0.46)                        # x, y, r, h

# review close-ups: name -> (location, target, lens mm, matched video frame)
CLOSEUPS = {
    "yard_cabanas": ((8.6, 19.4, 1.75), (14.3, 26.0, 1.4), 34, "exterior/10_courtyard-from-living-doors.jpg"),
    "yard_cabana_close": ((3.2, 29.2, 1.3), (14.3, 25.8, 1.45), 40, "exterior/13_courtyard-lounge-dusk.jpg"),
    "yard_west": ((14.2, 21.6, 1.8), (7.0, 31.0, 0.6), 15, "exterior/17_pool-beach-entry-day.jpg"),
    "yard_aerial21": ((17.0, 23.0, 12.0), (5.5, 29.0, 0.0), 18, "exterior/21_courtyard-aerial-angle.jpg"),
    "yard_terrace": ((13.6, 30.3, 1.6), (7.0, 20.0, 2.0), 16, "exterior/11_courtyard-pool-pavilion-day.jpg"),
    "yard_lounge": ((2.55, 29.95, 1.55), (6.2, 21.5, 1.2), 17, "exterior/13_courtyard-lounge-dusk.jpg"),
    "yard_dining": ((8.4, 21.4, 7.2), (2.7, 25.6, 0.4), 24, "exterior/08_courtyard-aerial-night.jpg"),
    "yard_bench": ((11.4, 27.6, 1.6), (11.8, 30.7, 0.3), 24, "exterior/17_pool-beach-entry-day.jpg"),
    "yard_egg": ((13.4, 25.9, 1.25), (12.9, 22.5, 0.55), 35, "exterior/11_courtyard-pool-pavilion-day.jpg"),
    "yard_sofa": ((4.9, 26.4, 2.0), (2.2, 28.4, 0.5), 24, "exterior/13_courtyard-lounge-dusk.jpg"),
    "yard_plan": ((7.65, 25.0, 40.0), (7.65, 25.0, 0.0), 50, "exterior/15_top-down-site-plan-night.jpg"),
    "yard_roof_lounge": ((12.9, 13.8, 8.3), (12.0, 17.6, 6.5), 16, "exterior/18_rooftop-lounge.jpg"),
    "yard_roof_dining": ((9.7, 8.3, 7.8), (13.0, 10.9, 6.5), 18, "exterior/19_rooftop-deck-view.jpg"),
}


# =========================================================================================
# mesh building
# =========================================================================================
class MB:
    """Tiny mesh builder: vertices, faces with optional per-loop UVs, material index, smooth flag."""

    def __init__(self):
        self.v, self.f, self.uv, self.mi, self.sm = [], [], [], [], []

    def add(self, pts):
        i = len(self.v)
        self.v.extend(tuple(float(c) for c in p) for p in pts)
        return i

    def face(self, idx, mat=0, uv=None, smooth=False):
        self.f.append(tuple(idx))
        self.mi.append(mat)
        self.uv.append(uv)
        self.sm.append(smooth)

    def build(self, name, mats):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        for m in mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", self.mi)
        me.polygons.foreach_set("use_smooth", self.sm)
        if any(u is not None for u in self.uv):
            flat = []
            for poly, uv in zip(me.polygons, self.uv):
                flat.extend(c for p in (uv or [(0.0, 0.0)] * poly.loop_total) for c in p)
            me.uv_layers.new(name="UVMap").data.foreach_set("uv", flat)
        me.update()
        return me

    def tris(self):
        return sum(len(f) - 2 for f in self.f)


def T(x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0):
    """Translation then rotation (about X, Y, Z in that order) as a 4x4 matrix."""
    return (Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
            @ Matrix.Rotation(rx, 4, "X"))


def _sp(w, e):
    return math.copysign(abs(w) ** e, w)


def box(mb, x0, y0, z0, x1, y1, z1, mat=0, M=None):
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    if M is not None:
        c = [tuple(M @ Vector(p)) for p in c]
    i = mb.add(c)
    for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        mb.face([i + k for k in q], mat)


def blob(mb, half, M, mat=0, e_xy=0.2, e_z=0.35, nu=16, nv=8, uv=None):
    """Superquadric (cushion / pillow) with half sizes `half`, centred at M's origin.

    uv: optional f(x, y, z) on local coordinates -> (u, v) for printed pillows."""
    hx, hy, hz = half
    loc = [(0.0, 0.0, -hz)]
    for j in range(1, nv):
        th = -math.pi / 2 + math.pi * j / nv
        c, s = _sp(math.cos(th), e_z), _sp(math.sin(th), e_z)
        for k in range(nu):
            a = TAU * k / nu
            loc.append((hx * c * _sp(math.cos(a), e_xy), hy * c * _sp(math.sin(a), e_xy), hz * s))
    loc.append((0.0, 0.0, hz))
    i = mb.add([tuple(M @ Vector(p)) for p in loc])
    top = i + len(loc) - 1

    def U(ids):
        return [uv(*loc[k - i]) for k in ids] if uv else None
    for k in range(nu):
        kn = (k + 1) % nu
        f = (i, i + 1 + kn, i + 1 + k)
        mb.face(f, mat, U(f), True)
        for j in range(nv - 2):
            a, b = i + 1 + j * nu, i + 1 + (j + 1) * nu
            f = (a + k, a + kn, b + kn, b + k)
            mb.face(f, mat, U(f), True)
        last = i + 1 + (nv - 2) * nu
        f = (top, last + k, last + kn)
        mb.face(f, mat, U(f), True)


def lathe(mb, prof, seg=24, mat=0, M=None, sx=1.0, sy=1.0, cap0=True, cap1=True, smooth=True):
    """Surface of revolution of (r, z) pairs about local Z (optionally elliptical via sx, sy)."""
    M = M or Matrix()
    rings = []
    for r, z in prof:
        rings.append(mb.add([tuple(M @ Vector((sx * r * math.cos(TAU * k / seg),
                                                sy * r * math.sin(TAU * k / seg), z))) for k in range(seg)]))
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            kn = (k + 1) % seg
            mb.face((a + k, a + kn, b + kn, b + k), mat, None, smooth)
    if cap0:
        mb.face(tuple(rings[0] + k for k in range(seg - 1, -1, -1)), mat)
    if cap1:
        mb.face(tuple(rings[-1] + k for k in range(seg)), mat)


def tube(mb, p0, p1, r, seg=8, mat=0, caps=True):
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    a = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    u = d.cross(a).normalized()
    w = d.cross(u)
    ring = [r * (math.cos(TAU * k / seg) * u + math.sin(TAU * k / seg) * w) for k in range(seg)]
    i0 = mb.add([p0 + q for q in ring])
    i1 = mb.add([p1 + q for q in ring])
    for k in range(seg):
        kn = (k + 1) % seg
        mb.face((i0 + k, i0 + kn, i1 + kn, i1 + k), mat, None, True)
    if caps:
        mb.face(tuple(i0 + k for k in range(seg - 1, -1, -1)), mat)
        mb.face(tuple(i1 + k for k in range(seg)), mat)


def shell(mb, prof, open_fn, seg=32, thick=0.045, z_in=0.36, mat=0, M=None):
    """Woven tub / egg chair body: revolved profile, open at the front (+x) where open_fn(z) > 0.

    open_fn(z) is the half-angle of the front opening.  The inner skin starts at z_in (the seat deck)."""
    M = M or Matrix()

    def r_at(z):
        for (ra, za), (rb, zb) in zip(prof, prof[1:]):
            if za <= z <= zb:
                return ra + (rb - ra) * (z - za) / (zb - za)
        return prof[-1][0]

    def ring(r, z):
        a = open_fn(z)
        return [tuple(M @ Vector((r * math.cos(a + (TAU - 2 * a) * k / seg),
                                  r * math.sin(a + (TAU - 2 * a) * k / seg), z))) for k in range(seg + 1)]
    zs = sorted({z for _, z in prof} | {z_in})
    outer = [mb.add(ring(r_at(z), z)) for z in zs]
    j0 = zs.index(z_in)
    inner = [mb.add(ring(r_at(z) - thick, z)) for z in zs[j0:]]
    for a, b in zip(outer, outer[1:]):
        for k in range(seg):
            mb.face((a + k, a + k + 1, b + k + 1, b + k), mat, None, True)
    for a, b in zip(inner, inner[1:]):
        for k in range(seg):
            mb.face((a + k, b + k, b + k + 1, a + k + 1), mat, None, True)
    for j in range(len(inner) - 1):          # rims along both sides of the front opening
        oa, ob, ia, ib = outer[j0 + j], outer[j0 + j + 1], inner[j], inner[j + 1]
        mb.face((oa, ob, ib, ia), mat)
        mb.face((oa + seg, ia + seg, ib + seg, ob + seg), mat)
    ot, it = outer[-1], inner[-1]
    for k in range(seg):
        mb.face((ot + k, ot + k + 1, it + k + 1, it + k), mat, None, True)
    mb.face(tuple(outer[0] + k for k in range(seg, -1, -1)), mat)       # base
    mb.face(tuple(inner[0] + k for k in range(seg + 1)), mat)           # seat deck


def plane_cut(z_front, z_back, t_max=0.9):
    """Opening half-angle for shell(): the rim is the plane through z_front (front) and z_back (back).

    t_max < 1 stops short of the top so a rounded arc of back is left at the last ring."""
    def f(z):
        t = min(t_max, max(0.0, (z - z_front) / (z_back - z_front)))
        return math.acos(1.0 - 2.0 * t)
    return f


def dense(prof, step=0.035):
    """Resample an (r, z) profile so a fast-changing opening gets enough rings."""
    out = [prof[0]]
    for (ra, za), (rb, zb) in zip(prof, prof[1:]):
        n = max(1, math.ceil((zb - za) / step))
        out += [(ra + (rb - ra) * k / n, za + (zb - za) * k / n) for k in range(1, n + 1)]
    return out


def canopy(mb, R, z_edge, z_top, sides=8, rows=6, cols=6, droop=0.0, mat=0, top_t=0.96,
           fringe=None, fringe_mat=1, fringe_u=0.5, rot=math.pi / 8, fringe_clip=None):
    """Polygonal pyramid canopy; per-panel UVs (u across, v edge->apex) and an optional fringe skirt.

    fringe_clip(p) -> longest allowed fringe below edge point p (keeps it clear of the wall cap)."""
    apex = Vector((0, 0, z_top))
    cs = [Vector((R * math.cos(rot + TAU * k / sides), R * math.sin(rot + TAU * k / sides), z_edge))
          for k in range(sides)]
    for k in range(sides):
        c0, c1 = cs[k], cs[(k + 1) % sides]
        grid = []
        for i in range(rows + 1):
            t = top_t * i / rows
            row = []
            for j in range(cols + 1):
                s = j / cols
                p = (c0.lerp(c1, s)).lerp(apex, t)
                p.z -= droop * math.sin(math.pi * s) * (1 - t)
                row.append(p)
            grid.append(mb.add(row))
        for i in range(rows):
            for j in range(cols):
                f = (grid[i] + j, grid[i] + j + 1, grid[i + 1] + j + 1, grid[i + 1] + j)
                uv = [(j / cols, top_t * i / rows), ((j + 1) / cols, top_t * i / rows),
                      ((j + 1) / cols, top_t * (i + 1) / rows), (j / cols, top_t * (i + 1) / rows)]
                mb.face(f, mat, uv, True)
        if fringe:
            L, flare = fringe
            edge = [Vector(mb.v[grid[0] + j]) for j in range(cols + 1)]
            out = Vector(((c0 + c1) / 2).xy.to_3d()).normalized()
            lens = [max(0.02, min(L, fringe_clip(p))) if fringe_clip else L for p in edge]
            low = mb.add([p + out * flare * ln / L + Vector((0, 0, -ln)) for p, ln in zip(edge, lens)])
            top = mb.add([p + out * 0.004 for p in edge])
            side = (c1 - c0).length
            for j in range(cols):
                u0, u1 = side * j / cols / fringe_u, side * (j + 1) / cols / fringe_u
                v0, v1 = 1 - lens[j] / L, 1 - lens[j + 1] / L      # shortened strands are cut, not squashed
                mb.face((low + j, low + j + 1, top + j + 1, top + j), fringe_mat,
                        [(u0, v0), (u1, v1), (u1, 1.0), (u0, 1.0)])
    return cs


# =========================================================================================
# generated textures
# =========================================================================================
def _image(name, rgba, colour=True, jpeg=False):
    h, w = rgba.shape[:2]
    px = np.ones((h, w, 4), np.float32)
    px[..., :rgba.shape[2]] = np.clip(rgba, 0, 1)
    img = bpy.data.images.new(name, w, h, alpha=rgba.shape[2] == 4)
    img.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    img.pixels.foreach_set(px.ravel())
    if jpeg:     # pack as JPEG bytes so the glTF embeds a small JPEG rather than a PNG
        tmp = os.path.join(tempfile.gettempdir(), f"{name}_{os.getpid()}.jpg")
        img.filepath_raw = tmp
        img.file_format = "JPEG"
        img.save(quality=90)
        img.pack()
        img.filepath_raw = f"//{name}.jpg"
        os.remove(tmp)
    else:
        img.pack()
    return img


def _normal_from_height(h, k):
    gy, gx = np.gradient(h)
    n = np.dstack([-gx * k, -gy * k, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def tex_weave(n=1024, seed=3):
    """Rattan / rope weave, grey (tinted per material), 1 m tile: 1.6 cm weavers over 3.2 cm stakes."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    P, S = 16.0, 32.0
    row = np.floor(y / P).astype(int)
    t = (y % P) / P
    over = 0.5 + 0.5 * np.cos(TAU * (x / S + 0.5 * (row % 2)))
    h = np.sin(np.pi * t) ** 0.7 * (0.68 + 0.32 * over)
    rowvar = rng.uniform(0.84, 1.1, n // int(P) + 1)[row]
    phase = rng.uniform(0, TAU, n // int(P) + 1)[row]
    fib = 0.93 + 0.07 * np.sin(x * 0.7 + phase) * np.sin(x * 0.11 + 2 * phase)
    shade = (0.28 + 0.72 * h) * rowvar * fib
    rgb = np.dstack([shade * 0.86] * 3)
    return rgb, _normal_from_height(h, 2.2)


def tex_macrame(w=512, h=1024, K=5, L=8, F=4):
    """Crochet / macrame canopy panel (v = 0 at the canopy edge, 1 at the apex), RGBA, alpha = cord.

    Thick diamond lattice of rope with knots at the crossings, a finer crochet net (F x finer) filling
    each diamond, alternate diamonds worked solid, and solid bands at the hem, the middle and the
    crown - dense enough to read white from a distance with small holes up close (10, 16, 17)."""
    v, u = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = (u + 0.5) / w, (v + 0.5) / h

    def net(k, l, cw):
        a, b = u * k + v * l, u * k - v * l
        da, db = np.abs(a - np.round(a)), np.abs(b - np.round(b))
        return np.maximum(np.clip(1 - da / cw, 0, 1), np.clip(1 - db / cw, 0, 1)), a, b, da, db
    big, a, b, da, db = net(K, L, 0.14)
    knot = np.clip(1 - np.hypot(da, db) / 0.2, 0, 1)
    fine, *_ = net(K * F, L * F, 0.3)
    ia, ib = np.floor(a).astype(int), np.floor(b).astype(int)
    band = (v < 0.06) | ((v > 0.46) & (v < 0.53)) | (v > 0.88)
    solid = band | (((ia + ib) % 2 == 0) & (v > 0.53) & (v < 0.88))       # chequer of worked diamonds
    tex = 0.82 + 0.18 * np.abs(np.sin(u * K * F * 6.0)) * np.abs(np.sin(v * L * F * 6.0))
    shade = np.where(big > 0.05, 0.8 + 0.2 * big, np.where(solid, tex, 0.74 + 0.26 * fine))
    shade = np.maximum(shade, 0.85 * knot + 0.15)
    alpha = ((big > 0.05) | (knot > 0.2) | solid | (fine > 0.12)).astype(np.float32)
    cream = np.array([0.96, 0.93, 0.86], np.float32)
    return np.dstack([cream * shade[..., None], alpha])


def tex_fringe(w=256, h=512, pitch=4, seed=5):
    """Fringe strands (v = 0 bottom tips, 1 top knot band). RGBA."""
    rng = np.random.default_rng(seed)
    v, u = np.mgrid[0:h, 0:w].astype(np.float32)
    col = np.floor(u / pitch).astype(int)
    nc = w // pitch + 1
    phase = rng.uniform(0, TAU, nc)[col]
    xc = (col + 0.5) * pitch + 0.9 * np.sin(v / h * 7 + phase)
    d = np.abs(u - xc)
    vend = rng.uniform(0.0, 0.09, nc)[col]
    strand = (d < 1.25) & (v / h > vend)
    band = v / h > 0.88
    knots = band & ((np.sin(u / pitch * np.pi) ** 2 + np.sin((v / h - 0.88) * 60) ** 2) > 0.3)
    alpha = (strand | knots).astype(np.float32)
    shade = np.where(band, 0.82, 1.0 - 0.35 * (d / 1.25) ** 2) * (0.9 + 0.1 * rng.uniform(size=nc)[col])
    rgb = np.array([0.93, 0.90, 0.83], np.float32) * shade[..., None]
    return np.dstack([rgb, alpha])


def tex_lattice(n=256, k=7, w=0.2):
    """Diagonal timber lattice (neighbour's trellis above the east wall, 09, 10, 13). RGBA."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    a, b = (x + y) * k, (x - y) * k
    da, db = np.abs(a - np.round(a)), np.abs(b - np.round(b))
    sa, sb = da < w / 2, db < w / 2
    top = (np.floor(a) + np.floor(b)) % 2 == 0          # alternate which slat lies on top
    shade = np.where(sa & sb, np.where(top, 0.95, 0.8), np.where(sa, 0.95 - 0.5 * da / w, 0.8 - 0.5 * db / w))
    rgb = np.array([0.42, 0.34, 0.27], np.float32) * shade[..., None]
    return np.dstack([rgb, (sa | sb).astype(np.float32)])


def tex_print(n=256, seed=11):
    """Black / white abstract brush print for pillows (13)."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    f = np.zeros((n, n), np.float32)
    for _ in range(7):
        k = rng.integers(1, 5, 2)
        f += np.sin(TAU * (k[0] * x + k[1] * y) + rng.uniform(0, TAU)) * rng.uniform(0.5, 1.0)
    g = np.sin(TAU * 9 * (x + 0.15 * np.sin(TAU * 2 * y)))
    ink = (f > 1.1) | ((np.abs(f) < 0.18) & (g > 0.3))
    val = np.where(ink, 0.05, 0.88)
    return np.dstack([val, val, val * 0.97])


# =========================================================================================
# materials
# =========================================================================================
def _img_node(m, img):
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    return t


def _alpha_clip(m, tex):
    n, l = m.node_tree.nodes, m.node_tree.links
    clip = n.new("ShaderNodeMath")          # Round = alpha clip at 0.5 (glTF alphaMode MASK)
    clip.operation = "ROUND"
    l.new(tex.outputs["Alpha"], clip.inputs[0])
    l.new(clip.outputs[0], n["Principled BSDF"].inputs["Alpha"])
    m.use_backface_culling = False
    if hasattr(m, "blend_method"):
        m.blend_method = "CLIP"


def materials(G):
    M = {}
    weave_rgb, weave_nrm = tex_weave()
    w_img = _image("yard_weave_diff", weave_rgb, True, True)
    n_img = _image("yard_weave_nor", weave_nrm, False, True)
    for name, tint, rough in (("yard_rattan", (1.45, 1.0, 0.56), 0.75),      # honey rattan (11, 16, 17)
                              ("yard_rope", (0.74, 0.70, 0.64), 0.85),
                              ("yard_wicker", (0.8, 0.72, 0.6), 0.8)):        # grey kubu wicker (13)
        m = G.mat(name, tint, rough)
        n, l = m.node_tree.nodes, m.node_tree.links
        b = n["Principled BSDF"]
        mix = n.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs["B"].default_value = (*tint, 1)
        l.new(_img_node(m, w_img).outputs["Color"], mix.inputs["A"])
        l.new(mix.outputs["Result"], b.inputs["Base Color"])
        nm = n.new("ShaderNodeNormalMap")
        l.new(_img_node(m, n_img).outputs["Color"], nm.inputs["Color"])
        l.new(nm.outputs["Normal"], b.inputs["Normal"])
        G.TILE[name] = 1.0                    # uv_all() box-projects at 1 m / tile
        M[name] = m
    for name, tint, strength in (("yard_teak", (0.85, 0.76, 0.68), 1.0),
                                 ("yard_teak_dark", (0.56, 0.48, 0.43), 1.0),
                                 ("yard_teak_grey", (0.47, 0.42, 0.37), 0.4),
                                 ("yard_oak", (1.05, 1.0, 0.92), 1.0)):
        M[name] = G.mat(name, tint, 0.6)
        G.pbr(name, "teak_veneer", 1.0, tint, strength)
    M["yard_concrete"] = G.mat("yard_concrete", (0.84, 0.83, 0.80), 0.8)
    G.pbr("yard_concrete", "concrete_floor_02", 1.0, (0.85, 0.84, 0.81), 0.35)

    mac = G.mat("yard_macrame", (0.93, 0.9, 0.83), 0.95)
    t = _img_node(mac, _image("yard_macrame_tex", tex_macrame()))
    mac.node_tree.links.new(t.outputs["Color"], mac.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    _alpha_clip(mac, t)
    fr = G.mat("yard_fringe", (0.93, 0.9, 0.83), 0.95)
    t = _img_node(fr, _image("yard_fringe_tex", tex_fringe()))
    fr.node_tree.links.new(t.outputs["Color"], fr.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    _alpha_clip(fr, t)
    lt = G.mat("yard_lattice", (0.42, 0.34, 0.27), 0.8)
    t = _img_node(lt, _image("yard_lattice_tex", tex_lattice()))
    lt.node_tree.links.new(t.outputs["Color"], lt.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    _alpha_clip(lt, t)
    M["yard_lattice"] = lt
    pr = G.mat("yard_print", (0.8, 0.8, 0.8), 0.9)
    t = _img_node(pr, _image("yard_print_tex", tex_print(), True, True))
    pr.node_tree.links.new(t.outputs["Color"], pr.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    M.update(yard_macrame=mac, yard_fringe=fr, yard_print=pr)

    M["yard_cushion"] = G.mat("yard_cushion", (0.86, 0.85, 0.82), 0.9)
    M["yard_white"] = G.mat("yard_white", (0.84, 0.83, 0.80), 0.55)
    M["yard_canvas"] = G.mat("yard_canvas", (0.88, 0.87, 0.84), 0.85)
    M["yard_metal"] = G.mat("yard_metal", (0.07, 0.07, 0.07), 0.45, 0.6)
    M["yard_brass"] = G.mat("yard_brass", (0.72, 0.52, 0.24), 0.35, 0.9)
    M["yard_wood"] = G.mat("yard_wood", (0.55, 0.40, 0.26), 0.55)
    M["yard_wood_grey"] = G.mat("yard_wood_grey", (0.30, 0.25, 0.21), 0.8)
    M["yard_dark"] = G.mat("yard_dark", (0.10, 0.10, 0.11), 0.9)
    M["yard_taupe"] = G.mat("yard_taupe", (0.40, 0.35, 0.30), 0.9)
    M["yard_ceramic"] = G.mat("yard_ceramic", (0.12, 0.10, 0.08), 0.45, 0.3)     # dark bronze bowls (13)
    M["yard_succulent"] = G.mat("yard_succulent", (0.16, 0.22, 0.15), 0.7)    # dusty grey-green (13, 19)
    for k in ("stucco", "timber", "shrub", "wall_light"):
        M[k] = G.MAT[k]
    return M


# =========================================================================================
# furniture (local frame: origin on the floor, front = +x, width along y)
# =========================================================================================
def pillow_uv(x, y, z):
    return (0.5 + y * 1.6, 0.5 + z * 1.6)


def build_pillow(half=(0.07, 0.23, 0.22)):
    mb = MB()
    blob(mb, half, Matrix(), 0, e_xy=0.55, e_z=0.5, nu=14, nv=8, uv=pillow_uv)
    return mb


def build_sofa():
    """Deep white upholstered 3-seater (13, 15): long axis along y, back at -x, rounded arms."""
    mb = MB()          # 0 cushion, 1 dark plinth
    D, L = 0.95, SOFA["y1"] - SOFA["y0"]
    x0, y0, y1 = -D / 2, -L / 2, L / 2
    box(mb, x0 + 0.05, y0 + 0.05, 0.0, D / 2 - 0.05, y1 - 0.05, 0.07, 1)
    blob(mb, (D / 2, L / 2, 0.12), T(0, 0, 0.18), 0, 0.08, 0.25)                  # base
    blob(mb, (0.08, L / 2, 0.23), T(x0 + 0.08, 0, 0.5), 0, 0.12, 0.3)               # back frame
    for s in (-1, 1):                                                                # arms
        blob(mb, (D / 2, 0.1, 0.17), T(0, s * (L / 2 - 0.1), 0.45), 0, 0.15, 0.4)
    ys = np.linspace(y0 + 0.2, y1 - 0.2, 4)
    for a, b in zip(ys, ys[1:]):
        blob(mb, (0.36, (b - a) / 2 - 0.01, 0.075), T(0.08, (a + b) / 2, 0.37), 0, 0.15, 0.4)
        blob(mb, (0.1, (b - a) / 2 - 0.01, 0.2), T(-0.27, (a + b) / 2, 0.62, ry=-0.28), 0, 0.2, 0.45)
    return mb


def build_armchair():
    """Teak-framed lounge armchair, white cushions, dark round pillow (13, 15)."""
    mb = MB()          # 0 teak, 1 cushion, 2 dark
    W, D = 0.43, 0.42
    box(mb, -D, -W, 0.0, D, -W + 0.1, 0.6, 0)         # chunky slab arms
    box(mb, -D, W - 0.1, 0.0, D, W, 0.6, 0)
    box(mb, -D, -W + 0.1, 0.12, -D + 0.1, W - 0.1, 0.72, 0)
    box(mb, -D + 0.1, -W + 0.1, 0.12, D, W - 0.1, 0.27, 0)
    blob(mb, (0.33, 0.32, 0.085), T(0.06, 0, 0.35), 1, 0.15, 0.4)
    blob(mb, (0.09, 0.31, 0.2), T(-0.22, 0, 0.6, ry=-0.25), 1, 0.2, 0.45)
    blob(mb, (0.15, 0.15, 0.06), T(-0.08, 0.08, 0.6, ry=-1.25), 2, 1.0, 0.6, nu=14, nv=6)
    return mb


def build_oval_table():
    """White oval pedestal coffee table (13, 15), long axis along y."""
    mb = MB()          # 0 white
    blob(mb, (0.34, 0.6, 0.035), T(0, 0, 0.375), 0, 1.0, 0.3, nu=28, nv=6)
    lathe(mb, [(0.3, 0.0), (0.27, 0.04), (0.18, 0.16), (0.19, 0.28), (0.28, 0.345)], 24, 0, sx=0.62, sy=1.0)
    return mb


def build_bowl(r=0.17):
    """Low ceramic bowl with a succulent mound (13, 19)."""
    mb = MB()          # 0 ceramic, 1 plant
    lathe(mb, [(r * 0.45, 0.0), (r * 0.9, 0.05), (r, 0.1), (r * 0.93, 0.1)], 18, 0, cap1=False)
    blob(mb, (r * 0.85, r * 0.85, 0.07), T(0, 0, 0.1), 1, 0.8, 0.7, nu=12, nv=5)
    return mb


def build_dining_table():
    """White concrete-top table with chamfered corners on two slab pedestals (08, 12), along y."""
    mb = MB()          # 0 concrete
    L, W, ch = DINING["length"] / 2, DINING["width"] / 2, 0.12
    outline = [(W - ch, -L), (W, -L + ch), (W, L - ch), (W - ch, L), (-W + ch, L), (-W, L - ch),
               (-W, -L + ch), (-W + ch, -L)]
    n = len(outline)
    i = mb.add([(x, y, 0.7) for x, y in outline] + [(x, y, 0.76) for x, y in outline])
    mb.face(tuple(i + k for k in range(n - 1, -1, -1)))
    mb.face(tuple(i + n + k for k in range(n)))
    for k in range(n):
        mb.face((i + k, i + (k + 1) % n, i + n + (k + 1) % n, i + n + k))
    for s in (-1, 1):
        py = s * (L - 0.6)
        box(mb, -0.28, py - 0.09, 0.0, 0.28, py + 0.09, 0.7)
    return mb


def build_dining_chair():
    """Teak side chair with woven back and white seat pad (08, 12)."""
    mb = MB()          # 0 teak, 1 cushion, 2 rope
    W, D = 0.26, 0.27
    for x in (-D + 0.03, D - 0.03):
        for y in (-W + 0.03, W - 0.03):
            top = 0.9 if x < 0 else 0.44
            lean = -0.06 if x < 0 else 0.0
            i = mb.add([(x - 0.022, y - 0.022, 0), (x + 0.022, y - 0.022, 0), (x + 0.022, y + 0.022, 0),
                        (x - 0.022, y + 0.022, 0), (x - 0.022 + lean, y - 0.022, top),
                        (x + 0.022 + lean, y - 0.022, top), (x + 0.022 + lean, y + 0.022, top),
                        (x - 0.022 + lean, y + 0.022, top)])
            for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                mb.face([i + k for k in q], 0)
    box(mb, -D, -W, 0.38, D, W, 0.43, 0)
    blob(mb, (D - 0.02, W - 0.02, 0.035), T(0.0, 0, 0.465), 1, 0.15, 0.4)
    box(mb, -0.02, -W + 0.04, 0.0, 0.02, W - 0.04, 0.33, 2, T(-D + 0.04, 0, 0.5, ry=-0.12))
    return mb


def build_round_chair():
    """Wide woven-rope cuddle chair with white cushions and pillows (18)."""
    mb = MB()          # 0 rope, 1 cushion, 2 accent pillow

    def opening(z):    # closed below the seat, arms at ~0.42 m, back widening to the rim
        t = min(1.0, max(0.0, (z - 0.3) / 0.12))
        return math.radians(56) * t * t * (3 - 2 * t) + math.radians(22) * min(1.0, max(0.0, (z - 0.42) / 0.35))
    shell(mb, [(0.5, 0.0), (0.55, 0.1), (0.6, 0.28), (0.61, 0.45), (0.59, 0.62), (0.53, 0.76)], opening,
          32, 0.045, 0.32, 0)
    blob(mb, (0.53, 0.53, 0.07), T(0.02, 0, 0.42), 1, 0.8, 0.45, nu=20, nv=6)
    for c, h, m in (((-0.36, -0.2, 0.62), (0.09, 0.24, 0.19), 1), ((-0.36, 0.22, 0.62), (0.09, 0.24, 0.19), 1),
                    ((-0.18, 0.05, 0.6), (0.07, 0.17, 0.15), 2)):
        blob(mb, h, T(*c, ry=-0.3), m, 0.35, 0.5, nu=14, nv=6)
    return mb


def build_egg_chair():
    """Rattan tulip / barrel swivel chair (11, 12, 16, 17): short woven drum base, a bowl that widens
    upward to a ~0.8 m rim, back ~1.0 m high, sides cut down in one sweep to the seat at the front;
    white seat cushion and square back pillow.  Front = +x."""
    mb = MB()          # 0 rattan, 1 cushion
    lathe(mb, [(0.25, 0.0), (0.27, 0.03), (0.275, 0.2), (0.265, 0.33), (0.2, 0.35)], 24, 0)
    prof = dense([(0.265, 0.33), (0.30, 0.40), (0.35, 0.52), (0.39, 0.68), (0.405, 0.84), (0.40, 0.97),
                  (0.385, 1.02)])
    shell(mb, prof, plane_cut(0.45, 1.06, 0.9), 32, 0.04, 0.42, 0)
    blob(mb, (0.3, 0.29, 0.075), T(0.04, 0, 0.5), 1, 0.8, 0.45, nu=20, nv=6)     # front edge proud of the rim
    blob(mb, (0.075, 0.23, 0.21), T(-0.2, 0, 0.77, ry=-0.3), 1, 0.3, 0.5, nu=14, nv=6)
    return mb


def build_balloon_chair():
    """Grey kubu-wicker balloon-back dining chair (13): flared pedestal skirt, seat at the waist, tall
    rounded back, open front, white seat pad.  Front = +x."""
    mb = MB()          # 0 wicker, 1 cushion
    lathe(mb, [(0.25, 0.0), (0.245, 0.04), (0.18, 0.2), (0.165, 0.36), (0.12, 0.4)], 20, 0)
    prof = dense([(0.17, 0.38), (0.22, 0.45), (0.265, 0.6), (0.29, 0.78), (0.285, 0.93), (0.24, 1.04),
                  (0.16, 1.1)])
    shell(mb, prof, plane_cut(0.5, 1.13, 0.86), 28, 0.035, 0.43, 0)
    blob(mb, (0.21, 0.21, 0.04), T(0.02, 0, 0.47), 1, 0.8, 0.45, nu=18, nv=5)
    return mb


def build_drum(r=0.27, h=0.55):
    """Rattan drum: cabana umbrella base / side table (10, 16)."""
    mb = MB()
    lathe(mb, [(r * 0.92, 0.0), (r, 0.04), (r * 1.03, h * 0.5), (r, h - 0.03), (r * 0.94, h)], 24, 0)
    return mb


def build_pouf():
    """Low round white pouf (10, 16)."""
    mb = MB()
    blob(mb, (0.27, 0.27, 0.1), T(0, 0, 0.1), 0, 0.9, 0.3, nu=20, nv=6)
    return mb


def build_floor_chair():
    """Low white floor chair: square seat cushion and a rounded half-moon back (10, 13). Front = +x."""
    mb = MB()
    h = SEAT / 2
    blob(mb, (h, h, 0.075), T(0.0, 0, 0.075), 0, 0.15, 0.4)
    blob(mb, (0.08, h - 0.02, 0.26), T(-h + 0.07, 0, 0.36, ry=-0.2), 0, 0.85, 0.55, nu=18, nv=8)
    return mb


def build_floor_cushion(length):
    """Flat white floor cushion, `length` along local y (10, 13)."""
    mb = MB()
    blob(mb, (SEAT / 2, length / 2, 0.065), T(0, 0, 0.065), 0, 0.12, 0.35)
    return mb


def build_cabana_frame():
    """Wood pole, ribs and brass finial of a macrame cabana."""
    mb = MB()          # 0 wood, 1 brass
    C = CABANA
    tube(mb, (0, 0, 0.3), (0, 0, C["z_top"] + 0.04), 0.028, 10, 0)
    for k in range(8):
        a = TAU * k / 8
        r = 0.95 * C["r"] * math.cos(math.pi / C["sides"])
        tube(mb, (0, 0, C["z_top"] - 0.08), (r * math.cos(a), r * math.sin(a), C["z_edge"] - 0.02), 0.012, 6, 0)
    z = C["z_top"] + 0.02
    lathe(mb, [(0.03, z), (0.055, z + 0.05), (0.06, z + 0.09), (0.04, z + 0.14), (0.012, z + 0.2)], 14, 1)
    return mb


def build_cabana_canopy(wall_dx=None, cap_dz=None):
    """Macrame canopy + fringe; strands over the wall cap (local x > wall_dx) stop above it."""
    mb = MB()          # 0 macrame, 1 fringe
    C = CABANA
    clip = None
    if wall_dx is not None:
        clip = lambda p: (p.z - cap_dz - 0.03) if p.x > wall_dx - 0.06 else C["fringe"]
    canopy(mb, C["r"], C["z_edge"], C["z_top"], C["sides"], 7, 4, 0.02, 0, 0.97, (C["fringe"], 0.04), 1, 0.5,
           rot=math.pi / C["sides"], fringe_clip=clip)
    return mb


def cantilever_hub():
    """Hub position: one canopy-apothem (+ gap) from the pole, toward the aim point over the dining
    table's pavilion end (08, 13, 15)."""
    C = CANTILEVER
    px, py = C["pole"]
    ang = math.atan2(C["aim"][1] - py, C["aim"][0] - px)
    reach = C["r"] * math.cos(math.pi / 8) + C["gap"]
    return px + reach * math.cos(ang), py + reach * math.sin(ang), ang


def build_cantilever():
    """Offset umbrella: pole with cross base, arm, hub, ribs and an octagonal canopy (08, 11, 13, 15).

    The canopy is turned so a flat edge faces the pole, which stands just outside it."""
    C = CANTILEVER
    hx, hy, ang = cantilever_hub()
    dx, dy = hx - C["pole"][0], hy - C["pole"][1]
    mb = MB()          # 0 canvas, 1 metal
    cs = canopy(mb, C["r"], C["z_edge"], C["z_hub"], 8, 5, 6, 0.08, 0, 0.98, None, rot=ang + math.pi + math.pi / 8)
    for c in cs:
        tube(mb, (0, 0, C["z_hub"] - 0.06), (c.x * 0.98, c.y * 0.98, C["z_edge"] - 0.03), 0.012, 6, 1)
    tube(mb, (0, 0, C["z_hub"] - 0.25), (0, 0, C["z_arm"]), 0.035, 10, 1)
    tube(mb, (-dx, -dy, 0.0), (-dx, -dy, C["z_arm"] + 0.05), 0.045, 12, 1)
    k = 0.92
    tube(mb, (-dx, -dy, C["z_arm"]), (-dx * (1 - k), -dy * (1 - k), C["z_arm"] + 0.04), 0.03, 10, 1)
    tube(mb, (-dx * (1 - k), -dy * (1 - k), C["z_arm"] + 0.04), (0, 0, C["z_arm"]), 0.03, 10, 1)
    for a in (0.0, math.pi / 2):                                # cross base (kept on the deck)
        box(mb, -0.34, -0.04, 0.0, 0.34, 0.04, 0.06, 1, T(-dx, -dy, 0, rz=a))
    box(mb, -0.24, -0.24, 0.0, 0.24, 0.24, 0.05, 1, T(-dx, -dy, 0.0))
    return mb


def build_market_umbrella():
    """White market umbrella with short fringe on a wood pole (11, 12)."""
    U = MARKET
    mb = MB()          # 0 canvas, 1 wood, 2 fringe
    canopy(mb, U["r"], U["z_edge"], U["z_top"], 8, 4, 4, 0.03, 0, 0.97, (0.11, 0.01), 2, 0.5)
    tube(mb, (0, 0, 0.0), (0, 0, U["z_top"] + 0.08), 0.022, 10, 1)
    lathe(mb, [(0.02, U["z_top"] + 0.06), (0.045, U["z_top"] + 0.1), (0.01, U["z_top"] + 0.16)], 10, 1)
    lathe(mb, [(0.13, 0.0), (0.12, 0.05), (0.04, 0.08)], 16, 1)
    return mb


def build_lounger():
    """Teak sun lounger with white pad and raised back (11, 12); foot end at +x."""
    mb = MB()          # 0 teak, 1 cushion
    L, W = 1.0, 0.34
    for x in (-L + 0.08, L - 0.08):
        for y in (-W + 0.04, W - 0.04):
            box(mb, x - 0.03, y - 0.03, 0.0, x + 0.03, y + 0.03, 0.26, 0)
    box(mb, -L, -W, 0.22, L, W, 0.3, 0)
    blob(mb, (0.66, W - 0.02, 0.05), T(0.32, 0, 0.35), 1, 0.12, 0.4)
    th = -0.85                                    # raised back rest, leaning toward the head (-x)
    box(mb, -0.02, -W + 0.02, 0.0, 0.02, W - 0.02, 0.62, 0, T(-0.46, 0, 0.3, ry=th))
    along, front = Vector((math.sin(th), 0, math.cos(th))), Vector((math.cos(th), 0, -math.sin(th)))
    c = Vector((-0.46, 0, 0.3)) + along * 0.31 + front * 0.06
    blob(mb, (0.04, W - 0.04, 0.3), T(c.x, c.y, c.z, ry=th), 1, 0.12, 0.4)
    return mb


def build_roof_table():
    """Long slatted weathered-teak table on four chunky legs (19), long axis along y."""
    mb = MB()
    L, W = ROOF_DINING["length"] / 2, ROOF_DINING["width"] / 2
    n = 8
    sw = 2 * W / n
    for k in range(n):
        box(mb, -W + k * sw + 0.005, -L, 0.735, -W + (k + 1) * sw - 0.005, L, 0.775)
    box(mb, -W + 0.06, -L + 0.06, 0.66, W - 0.06, L - 0.06, 0.735)
    for x in (-W + 0.07, W - 0.17):
        for y in (-L + 0.07, L - 0.17):
            box(mb, x, y, 0.0, x + 0.1, y + 0.1, 0.735)
    return mb


def build_roof_chair():
    """Woven-rope dining armchair on teak legs with white seat and back cushions (19)."""
    mb = MB()          # 0 teak, 1 rope, 2 cushion
    W, D = 0.3, 0.3
    for x in (-D + 0.03, D - 0.05):
        for y in (-W + 0.03, W - 0.05):
            box(mb, x, y, 0.0, x + 0.045, y + 0.045, 0.4, 0)
    box(mb, -D, -W, 0.36, D, W, 0.42, 0)
    for s in (-1, 1):
        box(mb, -D, s * W - 0.03, 0.42, D - 0.02, s * W + 0.03, 0.66, 1)
        box(mb, -D, s * W - 0.035, 0.66, D, s * W + 0.035, 0.69, 0)
    box(mb, -D + 0.005, -W + 0.005, 0.42, -D + 0.06, W - 0.005, 0.8, 1)
    blob(mb, (D - 0.03, W - 0.05, 0.05), T(0.02, 0, 0.47), 2, 0.15, 0.4)
    blob(mb, (0.07, W - 0.06, 0.16), T(-D + 0.13, 0, 0.66, ry=-0.2), 2, 0.2, 0.45)
    return mb


def build_roof_sofa():
    """Teak and rope sofa with white seat/back cushions (18); long axis along y, front at +x."""
    mb = MB()          # 0 teak, 1 rope, 2 cushion, 3 taupe
    L, D = ROOF_SOFA["length"] / 2, ROOF_SOFA["depth"] / 2
    box(mb, -D + 0.01, -L + 0.1, 0.06, D - 0.01, L - 0.1, 0.3, 0)     # inset: no faces coplanar with the arms
    for s in (-1, 1):
        box(mb, -D, s * L - (0.1 if s > 0 else 0), 0.0, D, s * L + (0.0 if s > 0 else 0.1), 0.64, 0)
        box(mb, -D + 0.04, s * (L - 0.1) - 0.02, 0.3, D - 0.04, s * (L - 0.1) + 0.02, 0.6, 1)
    box(mb, -D, -L + 0.1, 0.3, -D + 0.09, L - 0.1, 0.7, 1)
    for s in (-1, 1):
        blob(mb, (0.3, L / 2 - 0.07, 0.08), T(0.07, s * (L / 2 - 0.05), 0.38), 2, 0.15, 0.4)
        blob(mb, (0.09, L / 2 - 0.07, 0.2), T(-0.24, s * (L / 2 - 0.05), 0.62, ry=-0.3), 2, 0.2, 0.45)
    blob(mb, (0.06, 0.2, 0.17), T(-0.12, 0.6, 0.6, ry=-0.35, rz=0.2), 3, 0.5, 0.5, nu=14, nv=6)
    return mb


def build_round_table(r, h):
    """Solid round light-wood drum table (18)."""
    mb = MB()
    lathe(mb, [(r * 0.85, 0.0), (r * 0.85, h - 0.05), (r, h - 0.045), (r, h)], 28, 0)
    return mb


def build_bench():
    """Low slatted timber platform across the pavilion's kitchen bay, dark kick, step lights (15, 17)."""
    B = BENCH
    mb = MB()          # 0 timber, 1 dark kick, 2 light
    L, D, h = (B["x1"] - B["x0"]) / 2, B["depth"] / 2, B["h"]
    box(mb, -L + 0.06, -D + 0.06, 0.0, L - 0.06, D - 0.02, 0.08, 1)
    box(mb, -L, -D, 0.08, L, D, h - 0.045, 0)
    n = 6
    sw = 2 * D / n
    for k in range(n):
        box(mb, -L, -D + k * sw + 0.006, h - 0.045, L, -D + (k + 1) * sw - 0.006, h, 0)
    for lx in B["lights"]:
        box(mb, -L + lx - 0.05, -D - 0.006, 0.13, -L + lx + 0.05, -D + 0.01, 0.17, 2)
    return mb


# =========================================================================================
# assembly
# =========================================================================================
class Kit:
    """Builds each mesh once and places linked duplicates."""

    def __init__(self, G, M):
        self.G, self.M = G, M
        self.meshes, self.objects = {}, []

    def mesh(self, key, builder, mats):
        if key not in self.meshes:
            mb = builder()
            self.meshes[key] = (mb.build(f"Yard_mesh_{key}", [self.M[m] for m in mats]), mb.tris())
        return self.meshes[key][0]

    def put(self, name, key, builder, mats, x, y, z=0.0, facing=0.0, coll=COLL, scale=1.0):
        o = bpy.data.objects.new(name, self.mesh(key, builder, mats))
        o.location = (x, y, z)
        o.rotation_euler = (0.0, 0.0, facing)
        o.scale = (scale, scale, scale)
        self.G.link(o, coll)
        self.objects.append(o)
        return o

    def tris(self):
        """(triangles as placed, triangles of unique mesh data)."""
        per = {o.data.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in self.objects}
        return sum(per[o.data.name] for o in self.objects), sum(per.values())


def top_of(name, default):
    o = bpy.data.objects.get(name)
    if o is None:
        return default
    return max((o.matrix_world @ Vector(c)).z for c in o.bound_box)


def _offset(poly, d):
    """Offset a closed xy polygon outward by d (vertex normals; fine for gently curved outlines)."""
    P = np.array(poly, float)
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    e = np.roll(P, -1, 0) - P
    n = np.stack([e[:, 1], -e[:, 0]], 1) * (1 if area > 0 else -1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    vn = n + np.roll(n, 1, 0)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True)
    return [tuple(p) for p in P + vn * d]


def _pool_literals(G):
    """WATER_CTRL / COPING_W / SPA literals of blender/polish/pool.py, parsed (never executed)."""
    out = {}
    try:
        for node in ast.parse(open(os.path.join(G.ROOT, "blender", "polish", "pool.py")).read()).body:
            name = getattr(node.targets[0], "id", None) if isinstance(node, ast.Assign) else None
            if name in ("WATER_CTRL", "COPING_W", "SPA"):
                v = node.value
                if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "dict":   # SPA = dict(...)
                    out[name] = {kw.arg: ast.literal_eval(kw.value) for kw in v.keywords}
                else:
                    out[name] = ast.literal_eval(v)
    except (OSError, SyntaxError, ValueError):
        pass
    return out


def pool_footprint(G):
    """Plan polygon of pool + coping that the west deck and cabanas must keep clear of.

    The pool module runs after this one (alphabetical order) and replaces the base kidney pool, so use
    its outline when it exists: G.POOL_COPING if already published, else the WATER_CTRL / COPING_W
    literals read (not executed) from blender/polish/pool.py.  Fallback: the base Pool_coping mesh."""
    if getattr(G, "POOL_COPING", None):
        return [tuple(p) for p in G.POOL_COPING]
    consts = _pool_literals(G)
    if "WATER_CTRL" in consts and "COPING_W" in consts:
        return _offset(consts["WATER_CTRL"], consts["COPING_W"])
    o = bpy.data.objects.get("Pool_coping")
    if o is None:
        return []
    top = max(o.data.polygons, key=lambda p: p.normal.z * len(p.vertices))
    return [tuple((o.matrix_world @ o.data.vertices[i].co).xy) for i in top.vertices]


def poly_x_range(poly, y):
    """(min x, max x) of a closed polygon on plan row y, or None where it does not reach."""
    xs = []
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        if (ay - y) * (by - y) <= 0 and ay != by:
            xs.append(ax + (y - ay) / (by - ay) * (bx - ax))
    return (min(xs), max(xs)) if xs else None


def build_walls(G, kit):
    """White stucco boundary walls with a cap along both courtyard lot lines (11, 13, 16, 21)."""
    W = WALL
    for side, (x0, x1) in (("w", (0.0, W["t"])), ("e", (G.LOT["w"] - W["t"], G.LOT["w"]))):
        G.box(f"Yard_wall_{side}", x0, W["y0"], 0.0, x1, W["y1"], W["h"], "stucco", COLL)
        o = W["cap_over"]
        cx0 = max(0.0, x0 - o) if side == "w" else x0 - o
        cx1 = x1 + o if side == "w" else min(G.LOT["w"], x1 + o)
        G.box(f"Yard_wall_cap_{side}", cx0, W["y0"] - o, W["h"], cx1, W["y1"] + o, W["h"] + W["cap_h"],
              "stucco", COLL)
    # neighbour's timber lattice screen just beyond the east wall (09, 10, 13)
    L = LATTICE
    x, z0, z1 = G.LOT["w"] + L["dx"], W["h"] + W["cap_h"], W["h"] + W["cap_h"] + L["h"]
    mb = MB()          # 0 lattice, 1 rails / posts
    n = max(1, round((L["y1"] - L["y0"]) / L["tile"]))
    for k in range(n):
        ya = L["y0"] + (L["y1"] - L["y0"]) * k / n
        yb = L["y0"] + (L["y1"] - L["y0"]) * (k + 1) / n
        i = mb.add([(x, ya, z0), (x, yb, z0), (x, yb, z1), (x, ya, z1)])
        h = L["h"] / L["tile"]
        mb.face((i, i + 1, i + 2, i + 3), 0, [(0, 0), (1, 0), (1, h), (0, h)])
    for za, zb in ((z0 - 0.02, z0 + 0.03), (z1 - 0.03, z1 + 0.02)):
        box(mb, x - 0.025, L["y0"], za, x + 0.025, L["y1"], zb, 1)
    for k in range(int((L["y1"] - L["y0"]) / L["post"]) + 1):
        y = min(L["y1"] - 0.05, L["y0"] + k * L["post"])
        box(mb, x - 0.045, y - 0.045, 0.0, x + 0.045, y + 0.045, z1 + 0.04, 1)
    o = bpy.data.objects.new("Yard_wall_lattice_e", mb.build("Yard_wall_lattice_e",
                                                              [kit.M["yard_lattice"], kit.M["yard_wood_grey"]]))
    G.link(o, COLL)
    kit.objects.append(o)


def build_west_deck(G, kit, z, pool):
    """Raised timber deck from the terrace to the pavilion, stopping at the pool coping (08, 15, 16)."""
    D = WDECK

    def edge(y):
        r = min((poly_x_range(pool, yy) or (99, 99))[0] for yy in (y - 0.1, y, y + 0.1)) if pool else 99
        return min(D["x1_max"], r - D["gap"])
    ys = list(np.arange(D["y_terrace"], D["y1"], 0.2)) + [D["y1"]]
    east = [(edge(y), y) for y in ys]
    outline = [(D["x0"], D["y0"]), (G.HOUSE["x0"], D["y0"]), (G.HOUSE["x0"], D["y_terrace"])] + east + \
              [(D["x0"], D["y1"])]
    mb = MB()
    n = len(outline)
    i = mb.add([(x, y, 0.0) for x, y in outline] + [(x, y, z) for x, y in outline])
    mb.face(tuple(i + k for k in range(n - 1, -1, -1)))
    mb.face(tuple(i + n + k for k in range(n)))
    for k in range(n):
        mb.face((i + k, i + (k + 1) % n, i + n + (k + 1) % n, i + n + k))
    o = bpy.data.objects.new("Lounge_deck", mb.build("Lounge_deck", [kit.M["timber"]]))
    G.link(o, COLL)
    kit.objects.append(o)
    # recessed deck lights along the pool edge (08, 15, 16)
    lights = MB()
    y = D["y_terrace"] + 0.4
    while y < D["y1"] - 0.2:
        x = edge(y) - 0.12
        lathe(lights, [(0.035, z - 0.004), (0.035, z + 0.004)], 12, 0, T(x, y, 0))
        y += DECK_LIGHT_STEP
    o = bpy.data.objects.new("Lounge_deck_lights", lights.build("Lounge_deck_lights", [kit.M["wall_light"]]))
    G.link(o, COLL)
    kit.objects.append(o)


def build_west_lounge(G, kit, z):
    D = DINING
    kit.put("Yard_dining_table", "dining_table", build_dining_table, ["yard_concrete"], D["x"], D["y"], z)
    bowl = ["yard_ceramic", "yard_succulent"]
    kit.put("Yard_dining_bowl", "bowl", build_bowl, bowl, D["x"], D["y"] + 0.3, z + 0.76)
    k = 0
    for side, fx in ((-1, 0.0), (1, math.pi)):
        for dy in DINING_SIDE_Y:
            kit.put(f"Yard_dining_chair_{k}", "dining_chair", build_dining_chair,
                    ["yard_teak", "yard_cushion", "yard_rope"],
                    D["x"] + side * (D["width"] / 2 + 0.24), D["y"] + dy, z, fx)
            k += 1
    for i, (s, f) in enumerate(((-1, math.pi / 2), (1, -math.pi / 2))):
        kit.put(f"Yard_dining_woven_{i}", "woven", build_balloon_chair, ["yard_wicker", "yard_cushion"],
                D["x"], D["y"] + s * (D["length"] / 2 + DINING_END_GAP), z, f)
    hx, hy, _ = cantilever_hub()
    kit.put("Umbrella_cantilever", "cantilever", build_cantilever, ["yard_canvas", "yard_metal"], hx, hy, z)
    # lounge: sofa with its back to the west planting, oval coffee table, two teak armchairs (08, 13, 15)
    S = SOFA
    sx, sy = S["x_back"] + 0.475, (S["y0"] + S["y1"]) / 2
    kit.put("Lounge_sofa", "sofa", build_sofa, ["yard_cushion", "yard_dark"], sx, sy, z, 0.0)
    for i, (dy, rz, key) in enumerate(((-0.85, 0.15, "print"), (-0.4, -0.1, "white"), (0.45, 0.1, "print"),
                                       (0.88, -0.12, "white"))):
        kit.put(f"Lounge_pillow_{i}", f"pillow_{key}", build_pillow,
                ["yard_print" if key == "print" else "yard_cushion"], sx - 0.1, sy + dy, z + 0.64, rz)
    kit.put("Lounge_coffee_table", "oval_table", build_oval_table, ["yard_white"], COFFEE[0], COFFEE[1], z)
    kit.put("Lounge_bowl", "bowl", build_bowl, bowl, COFFEE[0], COFFEE[1] + 0.1, z + 0.41)
    for i, (x, y, f) in enumerate(ARMCHAIRS):
        f = math.atan2(COFFEE[1] - y, COFFEE[0] - x) if f is None else f
        kit.put(f"Lounge_armchair_{i}", "armchair", build_armchair,
                ["yard_teak_dark", "yard_cushion", "yard_dark"], x, y, z, f)
    x, y, r, h = SIDE_TABLE
    kit.put("Lounge_side_table", "side_drum", lambda: build_round_table(r, h), ["yard_white"], x, y, z)


def build_terrace(G, kit, z, turf_z):
    for i, (x, y) in enumerate(EGG_CHAIRS):
        kit.put(f"Yard_egg_chair_{i}", "egg", build_egg_chair, ["yard_rattan", "yard_cushion"], x, y, turf_z,
                math.pi / 2 + (0.2 if i else -0.2))
    x, y, r, h = EGG_TABLE
    kit.put("Yard_egg_table", "drum_small", lambda: build_drum(r, h), ["yard_rattan"], x, y, turf_z)
    kit.put("Yard_egg_table_bowl", "bowl", build_bowl, ["yard_ceramic", "yard_succulent"], x, y, turf_z + h,
            scale=0.65)
    for i, (x, y) in enumerate(LOUNGERS):
        kit.put(f"Yard_lounger_{i}", "lounger", build_lounger, ["yard_teak", "yard_cushion"], x, y, z,
                math.pi / 2)
    kit.put("Umbrella_market", "market", build_market_umbrella, ["yard_canvas", "yard_wood", "yard_fringe"],
            MARKET["pole"][0], MARKET["pole"][1], z)


def build_cabanas(G, kit, z):
    """Two macrame cabanas against the east wall with their floor seating (09, 10, 12, 13, 15, 16)."""
    W, C = WALL, CABANA
    pillow = ["yard_print"]
    for i, (x, y, out) in enumerate(CABANAS):     # same x for both, so the clipped canopy mesh is shared
        wall_dx, cap_dz = G.LOT["w"] - W["t"] - x, W["h"] + W["cap_h"] - z
        kit.put(f"Cabana_{i}_canopy", "cabana_canopy", lambda: build_cabana_canopy(wall_dx, cap_dz),
                ["yard_macrame", "yard_fringe"], x, y, z, 0.0)
        kit.put(f"Cabana_{i}_frame", "cabana_frame", build_cabana_frame, ["yard_wood", "yard_brass"], x, y, z)
        kit.put(f"Cabana_{i}_drum", "cabana_drum", lambda: build_drum(C["drum_r"], C["drum_h"]), ["yard_rattan"],
                x, y, z)
        # outer side: rounded-back floor chair against the wall, flat cushion in front of it (10, 13)
        oy = y + out * (C["drum_r"] + SEAT_GAP + SEAT / 2)
        kit.put(f"Cabana_{i}_chair", "floor_chair", build_floor_chair, ["yard_cushion"], SEAT_X, oy, z,
                math.pi + 0.05 * out)
        kit.put(f"Cabana_{i}_seat_front", "floor_seat", lambda: build_floor_cushion(SEAT), ["yard_cushion"],
                SEAT_X - SEAT - 0.02, oy + 0.06 * out, z, math.pi - 0.1 * out)
        # inner side, toward the other drum: long cushion with two print pillows (A), short one (B)
        length = LONG_SEAT if out > 0 else SEAT
        iy = y - out * (C["drum_r"] + SEAT_GAP + length / 2)
        kit.put(f"Cabana_{i}_seat_inner", f"floor_seat_{length:.2f}", lambda: build_floor_cushion(length),
                ["yard_cushion"], SEAT_X, iy, z, math.pi)
        dys = (-0.25, 0.25) if out > 0 else (0.0,)
        for k, dy in enumerate(dys):
            kit.put(f"Cabana_{i}_pillow_{k}", "pillow_print", build_pillow, pillow, SEAT_X + 0.2, iy + dy,
                    z + 0.33, math.pi + (0.12 if k else -0.1))
    for i, (x, y) in enumerate(POUFS):
        kit.put(f"Yard_pouf_{i}", "pouf", build_pouf, ["yard_cushion"], x, y, z)


def build_bench_obj(G, kit):
    B = BENCH
    P = G.PAVILION
    kit.put("Pavilion_bench", "bench", build_bench, ["timber", "yard_dark", "wall_light"],
            (B["x0"] + B["x1"]) / 2, P["y0"] - B["depth"] / 2, 0.0)


def spa_east_x(G):
    """East face of the roof-deck spa: the pool module's SPA (it rebuilds the spa after this module
    runs), else the base Spa box."""
    spa = _pool_literals(G).get("SPA")
    if spa:
        return spa["cx"] + spa["size"] / 2 + 0.06            # + its plinth lip
    o = bpy.data.objects.get("Spa")
    return max((o.matrix_world @ Vector(c)).x for c in o.bound_box) if o else 11.1


def build_roof(G, kit):
    z = top_of("Deck_turf", G.HOUSE["roof"] + 0.05)
    R = ROOF_DINING
    chair = ["yard_teak_grey", "yard_rope", "yard_cushion"]
    kit.put("Yard_roof_table", "roof_table", build_roof_table, ["yard_teak_grey"], R["x"], R["y"], z,
            math.pi / 2, ROOF)
    for i, dx in enumerate((-0.45, 0.35)):
        kit.put(f"Yard_roof_bowl_{i}", "bowl", build_bowl, ["yard_ceramic", "yard_succulent"], R["x"] + dx,
                R["y"] + 0.05, z + 0.775, coll=ROOF, scale=0.8 if i else 1.0)
    k = 0
    for dx in ROOF_DINING_DX:
        for s, f in ((-1, math.pi / 2), (1, -math.pi / 2)):
            kit.put(f"Yard_roof_chair_{k}", "roof_chair", build_roof_chair, chair, R["x"] + dx,
                    R["y"] + s * (R["width"] / 2 + 0.3), z, f, ROOF)
            k += 1
    kit.put(f"Yard_roof_chair_{k}", "roof_chair", build_roof_chair, chair, R["x"] - R["length"] / 2 - 0.36,
            R["y"], z, 0.0, ROOF)                                    # west end only (15)
    S, C, Q = ROOF_SOFA, ROOF_ROUND, ROOF_COFFEE
    sx = spa_east_x(G) + S["gap"] + S["depth"] / 2
    kit.put("Yard_roof_sofa", "roof_sofa", build_roof_sofa, ["yard_teak_grey", "yard_rope", "yard_cushion",
                                                              "yard_taupe"], sx, S["y"], z, 0.0, ROOF)
    for i, y in enumerate(C["ys"]):
        kit.put(f"Yard_roof_round_chair_{i}", "round", build_round_chair,
                ["yard_rope", "yard_cushion", "yard_taupe"], C["x"], y, z, math.pi, ROOF, C["scale"])
    qx = (sx + S["depth"] / 2 + C["x"] - 0.62 * C["scale"]) / 2     # midway between sofa front and chairs
    kit.put("Yard_roof_coffee", "roof_coffee", lambda: build_round_table(Q["r"], Q["h"]), ["yard_oak"],
            qx, Q["y"], z, 0.0, ROOF)
    x, y, r, h = ROOF_NEST
    kit.put("Yard_roof_coffee_low", "roof_nest", lambda: build_round_table(r, h), ["yard_oak"], x, y, z, 0.0, ROOF)
    x, y, r, h = ROOF_SIDE
    kit.put("Yard_roof_side_table", "roof_side", lambda: build_round_table(r, h), ["yard_oak"], x, y, z, 0.0, ROOF)


def remove_base(G):
    for prefix in ("Cabana", "Umbrella", "Lounge_", "Pavilion_bench"):
        G.remove(prefix)
    srcs = G.LIB.get("outdoor_table_chair_set_01", [])
    datas = {s.data for s in srcs}
    for o in [o for o in bpy.data.objects if o.type == "MESH" and o.data in datas and o not in srcs]:
        bpy.data.objects.remove(o, do_unlink=True)


def apply(G):
    remove_base(G)
    M = materials(G)
    kit = Kit(G, M)
    deck_z = top_of("Terrace_deck", 0.45)
    turf_z = top_of("Courtyard_turf", 0.03) + 0.002
    build_walls(G, kit)
    pool = pool_footprint(G)
    build_west_deck(G, kit, deck_z, pool)
    build_west_lounge(G, kit, deck_z)
    build_terrace(G, kit, deck_z, turf_z)
    build_cabanas(G, kit, turf_z)
    build_bench_obj(G, kit)
    build_roof(G, kit)
    for name, (loc, target, lens, _frame) in CLOSEUPS.items():
        G.SHOTS[name] = (loc, target, lens)
    cyc = getattr(bpy.context.scene, "cycles", None)
    if cyc is not None and cyc.transparent_max_bounces < 24:
        cyc.transparent_max_bounces = 24
    placed, unique = kit.tris()
    print(f"courtyard: {len(kit.objects)} objects, {unique} unique / {placed} placed triangles")
