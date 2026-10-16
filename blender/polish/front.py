"""Street front (polish module "front"): stick fence + gate on the low stucco planter wall,
stepping-stone entry path, covered entry porch with the "1159" column, alabaster wall sconces,
stone-basin fountain, circular flagstone side patio, landscape uplights and the street edge
(sidewalk, artificial-turf parkway, kerb + gutter, asphalt).

Owns: Fence_*, Front_planter_wall*, Porch_column, Front_path, Side_patio*, Wall_light_front_*,
Street*, Sidewalk*, and new Front_* objects.  Never G.remove("Front_"): Front_door / Front_win_*
belong to the facade.

Video evidence (frames/exterior/):
- 05_front-facade-day, 06_front-facade-dusk: ~0.55 m white stucco planter wall along the street;
  on top a rustic fence of peeled natural sticks (4-6 cm, ~9 cm pitch, 0.45-1.0 m above the wall,
  a few taller, slight leans, mixed tan / grey tones).  Wall stops at two thick natural-timber gate
  posts (~1.7 m); between them a ~1.6 m gate leaf of tight vertical sticks with top/bottom rails and
  a diagonal brace, standing on a large flagstone pad set in turf.  Street side: red-mulch strip
  (planting module), 1.5 m light concrete sidewalk with control joints, artificial-turf parkway with
  one big stepping stone in line with the gate, kerb and asphalt.  Dusk: uplights in the strip wash
  the wall; warm porch light.
- 02_entry-house-number: the square white porch column flush with the side wall carries a vertical
  "1159" in thin black geometric numerals (~0.3 m digits) under a white soffit + black roof edge.
- 03_entry-door-planter: rough-hewn white limestone basin with a bent copper spout in front of the
  porch; tall slim alabaster sconces with a black side bracket either side of the pivot door.
- 07_side-garden-stone-patio: circular crazy-paving patio of cream flagstones (light mortar joints)
  in turf west of the porch, stepping stones toward the porch, stick fence on the west lot line.
- 14_aerial-front-3-storey, 22_aerial-context-front, 01_aerial-neighborhood-ocean: the porch sits
  under the left front hip roof with the column at its south-west corner; continuous white wall +
  stick fence across the frontage; street parkway / sidewalk layout.
Modelling note: the base facade (door at x 3.0-4.2, y 4.0) has no recess, so the porch is built in
front of it - column at the house's west wall line, soffit + small hip roof whose eave matches the
front roofs (z 3.3) and whose back slope runs into Roof_front_0.
"""
import math
import random

import bpy
from mathutils import Vector

POLYHAVEN_ASSETS = ["rough_wood", "rock_boulder_dry"]   # stick fence / limestone basin + flagstones

COLL = "Landscape"
LOT_W = 15.3
SEED = 1159

# ---- street edge (y < 0): 05, 06, 22 -----------------------------------------------------
ROAD_X = (-10.0, 25.3)
ROAD_TOP = -0.05                    # Ground_far top is -0.06
GUTTER = (-5.45, -5.0)              # concrete gutter pan
KERB = (-5.0, -4.85, 0.07)          # y0, y1, top z: ~12 cm reveal
PARKWAY = (-4.85, -2.65, 0.045)     # artificial turf in front of the lot, lawn elsewhere
SIDEWALK = (-2.65, -1.15, 0.06)     # planting module's mulch strip runs y -1.15 .. 0.28
SIDEWALK_PANEL = 1.5                # control-joint spacing
FAR = dict(street=-16.2, gutter=-16.65, kerb=-16.8, parkway=-19.0, walk=-20.5)

# ---- front wall + fence: 05, 06, 14 --------------------------------------------------------
WALL = dict(y0=0.30, y1=0.60, h=0.58)
GATE = (2.62, 4.58)                 # wall ends = outer faces of the gate posts (planting gap)
POST = dict(r=0.075, h=1.70)
LEAF = dict(z0=0.07, h=(1.02, 1.10), r=(0.017, 0.023), pitch=0.062, rails=(0.24, 0.90))
FENCE = dict(pitch=0.08, jitter=0.02, r=(0.021, 0.033), above=(0.45, 1.0), above_w=(0.6, 1.15), tall_p=0.12,
             tall=(1.0, 1.25), lean=0.035, embed=0.12)
SIDE_FENCES = [(0.04, 0.62, 4.6), (LOT_W - 0.04, 0.62, 4.0)]   # lot-line returns (07, 14)
SIDE_ABOVE = (1.05, 1.55)
STICK_TONES = {                     # linear albedo targets: tan, weathered grey, warm (05, 06)
    "front_stick_a": (0.50, 0.40, 0.27),
    "front_stick_b": (0.44, 0.40, 0.33),
    "front_stick_c": (0.55, 0.41, 0.25),
}

# ---- entry: 02, 03, 05, 07, 14 -------------------------------------------------------------
PORCH = dict(x0=2.4, x1=4.85, y0=2.3, floor=0.08,
             roof=(1.95, 2.0, 4.95, 4.0), soffit=2.95, eave=3.3, pitch=0.447,  # pitch = front roofs
             fascia=(3.08, 3.33, 0.025))
COLUMN = dict(x0=2.4, y0=2.45, size=0.36)          # flush with the house's west wall (02)
NUMBER = dict(text="1159", h=0.30, gap=0.07, top=2.70, stroke=0.026, depth=0.014)
SCONCES = [(2.70, -1), (4.43, 1)]                  # x, side of the black bracket (03)
SCONCE = dict(w=0.11, d=0.07, z0=1.50, z1=2.25)
BASIN = dict(x=1.62, y=4.12, rx=0.44, ry=0.38, h=0.72)
CHAIRS = [(2.98, 3.3, -60), (4.32, 3.3, -120)]      # wicker bowl chairs on the porch: x, y, facing deg (03, 05, 14)
CHAIR = dict(r=0.42, seat=0.62, shell=0.035, base_r=0.2)

# ---- paths, turf, patio: 03, 05, 06, 07 ------------------------------------------------------
STONES = [  # (cx, cy, half-length, half-width, rotation, top z) irregular flagstones
    (3.62, -3.75, 0.62, 0.38, 0.12, PARKWAY[2] + 0.02),   # parkway, in line with the gate (05, 06)
    (3.60, -0.36, 0.80, 0.56, 0.0, 0.065),                 # gate pad (05, 06)
    (3.62, 1.05, 0.52, 0.31, 0.06, 0.05),                  # gate -> porch (03)
    (3.50, 1.86, 0.50, 0.29, -0.08, 0.05),
    (2.08, 2.46, 0.25, 0.19, 0.5, 0.05),                   # toward the patio (07)
]
TURF = [(0.02, 2.22, 2.4, 4.93), (2.75, 0.60, 4.45, 2.22), (2.4, 2.22, 4.85, 2.32),
        (4.45, 2.22, 6.3, 3.97)]                           # inside the fence, around path + patio
GATE_TURF = (GATE[0], SIDEWALK[1], GATE[1], WALL["y0"])
PATIO = dict(cx=1.2, cy=3.55, r=1.2, base=0.035, top=0.058, gap=0.022, spacing=0.34)
UPLIGHTS = [(0.9, -0.3), (2.35, -0.22), (4.85, -0.22), (6.9, -0.3), (9.4, -0.3),
            (11.9, -0.3), (14.4, -0.3)]                    # dusk wall wash (06)

# ---- review close-ups: name -> (location, target, lens mm, matched frame, repo-relative) -----------
CAMS = {   # 05-derived poses solved from gate / eave / wall corners (pinhole fit, ~13 mm equivalent)
    "front_view05": ((3.85, -6.13, 1.9), (7.57, 3.13, 2.5), 13, "frames/exterior/05_front-facade-day.jpg"),
    "front_gate": ((3.85, -6.13, 1.9), (2.64, 1.73, 1.05), 26, "renders/wip/front/ref/05_gate.jpg"),
    "front_fence": ((3.85, -6.13, 1.9), (9.56, -0.64, 0.81), 26, "renders/wip/front/ref/05_fence.jpg"),
    "front_entry": ((2.15, 1.05, 1.25), (2.62, 2.45, 2.2), 20, "frames/exterior/02_entry-house-number.jpg"),
    "front_door": ((4.6, 2.4, 1.35), (2.8, 4.0, 1.3), 24, "frames/exterior/03_entry-door-planter.jpg"),
    "front_patio": ((1.6, 1.15, 1.8), (1.6, 4.2, 0.2), 18, "frames/exterior/07_side-garden-stone-patio.jpg"),
    "front_entry_aerial": ((6.0, -6.0, 7.0), (3.4, 3.2, 1.6), 30, "renders/wip/front/ref/14_entry.jpg"),
}

# mean linear colour of the Poly Haven diffuse maps (for overlay tint solving)
TEX_MEAN = {"rough_wood": (0.150, 0.126, 0.099), "rock_boulder_dry": (0.398, 0.337, 0.271),
            "concrete_floor_02": (0.193, 0.162, 0.108), "leafy_grass": (0.315, 0.232, 0.103)}
TURF_TONE = (0.03, 0.11, 0.022)     # parkway + entry turf: deep artificial-grass green (05, 06, 07)


# =============================================================================================
# geometry helpers
# =============================================================================================
class Builder:
    """Accumulates verts / faces (with material index + smooth flag) for one joined mesh."""

    def __init__(self):
        self.v, self.f, self.mi, self.sm = [], [], [], []

    def verts(self, pts):
        b = len(self.v)
        self.v.extend(tuple(p) for p in pts)
        return b

    def faces(self, faces, mi=0, smooth=False):
        for face in faces:
            self.f.append(tuple(face))
            self.mi.append(mi)
            self.sm.append(smooth)

    def box(self, x0, y0, z0, x1, y1, z1, mi=0):
        b = self.verts([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
        self.faces([[b + i for i in f] for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                                                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))], mi)

    def prism(self, outline, z0, z1, mi=0):
        """Vertical extrusion of a 2D outline (top + sides; bottom sits on the ground)."""
        if area(outline) < 0:
            outline = outline[::-1]
        n = len(outline)
        b = self.verts([(x, y, z0) for x, y in outline] + [(x, y, z1) for x, y in outline])
        self.faces([[b + n + i for i in range(n)]], mi)
        self.faces([(b + i, b + (i + 1) % n, b + n + (i + 1) % n, b + n + i) for i in range(n)], mi)

    def tube(self, pts, radii, sides, mi=0, cap_end=True, cap_start=False, smooth=True,
             rnd=None, jitter=0.0, slant=0.0):
        """Sweep a circle along a 3D polyline (rotation-minimising frames)."""
        pts = [Vector(p) for p in pts]
        n = len(pts)
        tans = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
        ref = Vector((1, 0, 0)) if abs(tans[0].x) < 0.9 else Vector((0, 1, 0))
        u = tans[0].cross(ref).normalized()
        ring_pts = []
        for i in range(n):
            t = tans[i]
            if i:
                u = tans[i - 1].rotation_difference(t) @ u
                u = (u - t * u.dot(t)).normalized()
            w = t.cross(u)
            for j in range(sides):
                a = 2 * math.pi * j / sides
                r = radii[i] * (1 + (rnd.uniform(-jitter, jitter) if jitter else 0.0))
                p = pts[i] + (u * math.cos(a) + w * math.sin(a)) * r
                if i == n - 1 and slant:
                    p = p + t * slant * math.cos(a)
                ring_pts.append(p)
        b = self.verts(ring_pts)
        s = sides
        self.faces([(b + k * s + j, b + k * s + (j + 1) % s, b + (k + 1) * s + (j + 1) % s,
                     b + (k + 1) * s + j) for k in range(n - 1) for j in range(s)], mi, smooth)
        if cap_end:
            self.faces([[b + (n - 1) * s + j for j in range(s)]], mi)
        if cap_start:
            self.faces([[b + j for j in range(s - 1, -1, -1)]], mi)

    def build(self, G, name, mats, coll=COLL):
        o = G.mesh(name, self.v, self.f, mats[0], coll)
        for m in mats[1:]:
            o.data.materials.append(G.MAT[m])
        o.data.polygons.foreach_set("material_index", self.mi)
        o.data.polygons.foreach_set("use_smooth", self.sm)
        o.data.update()
        return o


def area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def clip(poly, n, c):
    """Sutherland-Hodgman: keep the part of a convex polygon with p . n <= c."""
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        dp, dq = p[0] * n[0] + p[1] * n[1] - c, q[0] * n[0] + q[1] * n[1] - c
        if dp <= 0:
            out.append(p)
        if (dp < 0) != (dq < 0) and dp != dq:
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def blob(rnd, cx, cy, a, b, rot, n=12, rough=0.09):
    """Irregular rounded flagstone outline (superellipse with jitter)."""
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        c, s = math.cos(t), math.sin(t)
        ex = 0.55                                         # squarish but rounded corners
        x = a * math.copysign(abs(c) ** ex, c) * (1 + rnd.uniform(-rough, rough))
        y = b * math.copysign(abs(s) ** ex, s) * (1 + rnd.uniform(-rough, rough))
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return pts


def overlay_tint(target, mean, f):
    """Tint for G.pbr(strength=f<1, OVERLAY) so that the textured result averages `target`."""
    out = []
    for t, m in zip(target, mean):
        a = t / (1 - f + 2 * f * m)
        if a >= 0.5:
            a = 1 - (1 - t) / (1 - f + 2 * f * (1 - m))
        out.append(min(max(a, 0.0), 1.0))
    return tuple(out)


def lamp(G, name, kind, loc, energy, color=(1.0, 0.78, 0.5), target=None, size=0.05, spot=60):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = size
    if kind == "SPOT":
        ld.spot_size = math.radians(spot)
        ld.spot_blend = 0.6
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    if target is not None:
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    G.link(o, COLL)
    return o


# =============================================================================================
# materials
# =============================================================================================
def materials(G):
    for name, target in STICK_TONES.items():
        G.mat(name, target, 0.85)
        G.pbr(name, "rough_wood", 0.45, overlay_tint(target, TEX_MEAN["rough_wood"], 0.6), 0.6)
    G.mat("front_post", (0.40, 0.30, 0.19), 0.8)
    G.pbr("front_post", "rough_wood", 0.6, overlay_tint((0.40, 0.30, 0.19), TEX_MEAN["rough_wood"], 0.6), 0.6)
    G.mat("front_flagstone", (0.66, 0.61, 0.50), 0.75)
    G.pbr("front_flagstone", "rock_boulder_dry", 1.6,
          overlay_tint((0.66, 0.61, 0.50), TEX_MEAN["rock_boulder_dry"], 0.5), 0.5)
    G.mat("front_limestone", (0.62, 0.59, 0.50), 0.85)
    G.pbr("front_limestone", "rock_boulder_dry", 0.9,
          overlay_tint((0.62, 0.59, 0.50), TEX_MEAN["rock_boulder_dry"], 0.7), 0.7)
    G.mat("front_mortar", (0.40, 0.38, 0.34), 0.9)
    G.pbr("front_mortar", "concrete_floor_02", 1.0,
          overlay_tint((0.40, 0.38, 0.34), TEX_MEAN["concrete_floor_02"], 0.4), 0.4)
    G.mat("front_sidewalk", (0.52, 0.50, 0.46), 0.85)
    G.pbr("front_sidewalk", "concrete_floor_02", 2.5,
          overlay_tint((0.52, 0.50, 0.46), TEX_MEAN["concrete_floor_02"], 0.45), 0.45)
    G.mat("front_kerb", (0.45, 0.44, 0.41), 0.85)
    G.pbr("front_kerb", "concrete_floor_02", 2.0,
          overlay_tint((0.45, 0.44, 0.41), TEX_MEAN["concrete_floor_02"], 0.4), 0.4)
    for name in ("front_flagstone", "front_mortar", "front_sidewalk", "front_kerb"):
        for nd in G.MAT[name].node_tree.nodes:                 # calmer bump on flat paving
            if nd.type == "NORMAL_MAP":
                nd.inputs["Strength"].default_value = 0.5
    G.mat("front_turf", TURF_TONE, 0.9)                       # artificial turf, deeper than "turf"
    G.pbr("front_turf", "leafy_grass", 1.2, overlay_tint(TURF_TONE, TEX_MEAN["leafy_grass"], 0.45), 0.45)
    G.mat("front_rattan", (0.40, 0.27, 0.13), 0.8)
    G.detail("front_rattan", "noise", (0.30, 0.19, 0.09), (0.50, 0.36, 0.19), scale=60, bump=0.4)
    G.mat("front_alabaster", (0.92, 0.84, 0.68), 0.35, emit=((1.0, 0.76, 0.48), 1.6))
    G.mat("front_copper", (0.45, 0.22, 0.11), 0.5, 0.65)
    G.mat("front_stream", (0.9, 0.95, 1.0), 0.05, transmission=1.0)
    G.mat("front_lens", (1.0, 0.9, 0.7), 0.3, emit=((1.0, 0.8, 0.55), 4.0))


# =============================================================================================
# street edge
# =============================================================================================
def street(G):
    x0, x1 = ROAD_X
    G.box("Street", x0, FAR["street"], -0.12, x1, GUTTER[0], ROAD_TOP, "asphalt", "Site")
    curb = Builder()
    curb.box(x0, GUTTER[0], -0.12, x1, GUTTER[1], ROAD_TOP + 0.006)
    curb.box(x0, KERB[0], -0.12, x1, KERB[1], KERB[2])
    curb.box(x0, FAR["gutter"], -0.12, x1, FAR["street"], ROAD_TOP + 0.006)
    curb.box(x0, FAR["kerb"], -0.12, x1, FAR["gutter"], KERB[2])
    curb.build(G, "Street_kerb", ["front_kerb"], "Site")
    # parkway: turf in front of this lot, lawn in front of the neighbours; lawn verges beside the strip
    y0, y1, top = PARKWAY
    G.box("Street_parkway", 0.0, y0, -0.1, LOT_W, y1, top, "front_turf", "Site")
    lawn = Builder()
    lawn.box(x0, y0, -0.1, 0.0, y1, top - 0.01)
    lawn.box(LOT_W, y0, -0.1, x1, y1, top - 0.01)
    lawn.box(x0, SIDEWALK[1], -0.1, 0.0, 0.0, 0.03)
    lawn.box(LOT_W, SIDEWALK[1], -0.1, x1, 0.0, 0.03)
    lawn.box(x0, FAR["parkway"], -0.1, x1, FAR["kerb"], top - 0.01)
    lawn.build(G, "Street_parkway_lawn", ["lawn_ground"], "Site")
    # sidewalks: panels with control joints over a slightly darker bed
    walk, bed = Builder(), Builder()
    for (ya, yb) in ((SIDEWALK[0], SIDEWALK[1]), (FAR["walk"], FAR["parkway"])):
        bed.box(x0, ya, -0.1, x1, yb, SIDEWALK[2] - 0.012)
        x = x0
        while x < x1 - 1e-6:
            xb = min(x + SIDEWALK_PANEL, x1)
            walk.box(x + 0.005, ya, -0.1, xb - 0.005, yb, SIDEWALK[2])
            x = xb
    walk.build(G, "Sidewalk", ["front_sidewalk"], "Site")
    bed.build(G, "Sidewalk_joints", ["concrete"], "Site")


# =============================================================================================
# wall, fence, gate
# =============================================================================================
def stick(B, rnd, base, length, r, lean, mi, sides=6, segs=3):
    x, y, z = base
    top = Vector((x + lean[0] * length, y + lean[1] * length, z + length))
    bend_dir = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized()
    bend = rnd.uniform(0.0, 0.022) * length
    pts = [Vector(base).lerp(top, k / segs) + bend_dir * bend * math.sin(math.pi * k / segs)
           for k in range(segs + 1)]
    radii = [r * (1.12 - 0.25 * k / segs) for k in range(segs + 1)]
    B.tube(pts, radii, sides, mi, rnd=rnd, jitter=0.07, slant=rnd.uniform(0.0, 0.8) * r)


def stick_row(B, rnd, a0, a1, fixed, along_x, zbase, above, pitch):
    a = a0 + rnd.uniform(0.0, pitch * 0.4)
    while a < a1:
        h = rnd.uniform(*FENCE["tall"]) if rnd.random() < FENCE["tall_p"] else rnd.uniform(*above)
        r = rnd.uniform(*FENCE["r"])
        off = rnd.uniform(-0.035, 0.035)
        lean = (rnd.gauss(0, FENCE["lean"]), rnd.gauss(0, FENCE["lean"] * 0.7))
        base = (a, fixed + off, zbase - FENCE["embed"]) if along_x else (fixed + off, a, zbase - FENCE["embed"])
        stick(B, rnd, base, h + FENCE["embed"], r, lean, rnd.randrange(3))
        a += pitch + rnd.uniform(-FENCE["jitter"], FENCE["jitter"])


def fence(G, rnd):
    W = WALL
    wall = Builder()
    wall.box(0.0, W["y0"], -0.03, GATE[0], W["y1"], W["h"])
    wall.box(GATE[1], W["y0"], -0.03, LOT_W, W["y1"], W["h"])
    wall.build(G, "Front_planter_wall", ["stucco"])
    yc = (W["y0"] + W["y1"]) / 2
    mats = list(STICK_TONES)
    top = Builder()                                       # sticks planted in the wall top (05, 06)
    stick_row(top, rnd, 0.05, GATE[0] - 0.06, yc, True, W["h"], FENCE["above_w"], FENCE["pitch"] * 1.1)
    stick_row(top, rnd, GATE[1] + 0.06, LOT_W - 0.04, yc, True, W["h"], FENCE["above"], FENCE["pitch"])
    top.build(G, "Fence_sticks", mats)
    side = Builder()                                      # ground-set returns on the lot lines (07, 14)
    for x, y0, y1 in SIDE_FENCES:
        stick_row(side, rnd, y0, y1, x, False, 0.0, SIDE_ABOVE, FENCE["pitch"] * 1.05)
    side.build(G, "Fence_side", mats)
    # gate posts: thick natural timber, slightly irregular (05)
    posts = Builder()
    for x in (GATE[0] + POST["r"], GATE[1] - POST["r"]):
        pts = [(x, yc, -0.05), (x + rnd.uniform(-0.01, 0.01), yc, POST["h"] * 0.5), (x, yc, POST["h"])]
        posts.tube(pts, [POST["r"] * 1.04, POST["r"], POST["r"] * 0.94], 10, 0, rnd=rnd, jitter=0.05)
    posts.build(G, "Fence_gate_posts", ["front_post"])
    # gate leaf: tight vertical sticks, street-side top/bottom rails + diagonal brace (05, 06)
    gate = Builder()
    xa, xb = GATE[0] + 2 * POST["r"] + 0.025, GATE[1] - 2 * POST["r"] - 0.025
    n = int((xb - xa) / LEAF["pitch"])
    for i in range(n + 1):
        x = xa + (xb - xa) * i / n + rnd.uniform(-0.006, 0.006)
        h = rnd.uniform(*LEAF["h"])
        stick(gate, rnd, (x, yc, LEAF["z0"]), h, rnd.uniform(*LEAF["r"]),
              (rnd.gauss(0, 0.006), rnd.gauss(0, 0.004)), rnd.randrange(3), segs=2)
    ry = yc - 0.045
    for z in LEAF["rails"]:
        gate.tube([(xa - 0.03, ry, LEAF["z0"] + z), (xb + 0.03, ry, LEAF["z0"] + z)], [0.024, 0.022], 7, 0,
                  cap_start=True)
    z0, z1 = LEAF["z0"] + LEAF["rails"][0], LEAF["z0"] + LEAF["rails"][1]
    gate.tube([(xa + 0.04, ry - 0.005, z0), (xb - 0.04, ry - 0.005, z1)], [0.021, 0.021], 7, 1, cap_start=True)
    gate.build(G, "Fence_gate", mats)


# =============================================================================================
# entry porch, house number, sconces
# =============================================================================================
DIGITS = {}


def digit_paths(ch):
    """Thin geometric (Futura-like) numerals in unit height: list of (polyline, closed)."""
    if ch == "1":
        return [([(0.0, 0.0), (0.0, 1.0)], False)]
    if ch == "5":
        p = [(0.50, 1.0), (0.06, 1.0), (0.04, 0.575)]
        c, r = (0.27, 0.315), 0.30
        a0, a1, k = 128.0, -145.0, 22
        p += [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / k)),
               c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / k))) for i in range(k + 1)]
        return [(p, False)]
    if ch == "9":
        c, r = (0.29, 0.70), 0.29
        ring = [(c[0] + r * math.cos(2 * math.pi * i / 28), c[1] + r * math.sin(2 * math.pi * i / 28))
                for i in range(28)]
        tail = [(c[0] + r * math.cos(math.radians(-20)), c[1] + r * math.sin(math.radians(-20))), (0.12, 0.0)]
        return [(ring, True), (tail, False)]
    raise ValueError(ch)


def ribbon(B, pts, half, depth, world, closed, mi=0):
    """Mitred flat stroke along a 2D polyline, extruded `depth` off a wall; world(u, v, d)->xyz."""
    n = len(pts)
    left, right = [], []
    for i in range(n):
        segs = []
        if closed or i > 0:
            p, q = pts[i - 1], pts[i]
            segs.append(((q[0] - p[0]), (q[1] - p[1])))
        if closed or i < n - 1:
            p, q = pts[i], pts[(i + 1) % n]
            segs.append(((q[0] - p[0]), (q[1] - p[1])))
        normals = []
        for dx, dy in segs:
            ln = math.hypot(dx, dy)
            normals.append((-dy / ln, dx / ln))
        mx, my = sum(nn[0] for nn in normals), sum(nn[1] for nn in normals)
        ml = math.hypot(mx, my)
        mx, my = mx / ml, my / ml
        k = half / max(mx * normals[0][0] + my * normals[0][1], 0.35)
        left.append((pts[i][0] + mx * k, pts[i][1] + my * k))
        right.append((pts[i][0] - mx * k, pts[i][1] - my * k))
    b = B.verts([world(u, v, depth) for u, v in left] + [world(u, v, depth) for u, v in right] +
                [world(u, v, 0.0) for u, v in left] + [world(u, v, 0.0) for u, v in right])
    L, R, Lb, Rb = b, b + n, b + 2 * n, b + 3 * n
    m = n if closed else n - 1
    B.faces([(L + i, R + i, R + (i + 1) % n, L + (i + 1) % n) for i in range(m)], mi)
    B.faces([(Lb + i, L + i, L + (i + 1) % n, Lb + (i + 1) % n) for i in range(m)], mi)
    B.faces([(R + i, Rb + i, Rb + (i + 1) % n, R + (i + 1) % n) for i in range(m)], mi)
    if not closed:
        B.faces([(L, Lb, Rb, R), (R + n - 1, Rb + n - 1, Lb + n - 1, L + n - 1)], mi)


def house_number(G):
    N = NUMBER
    cx = COLUMN["x0"] + COLUMN["size"] / 2
    face_y = COLUMN["y0"]
    half = N["stroke"] / 2 / N["h"]
    B = Builder()
    for i, ch in enumerate(N["text"]):
        z0 = N["top"] - N["h"] - i * (N["h"] + N["gap"])
        paths = digit_paths(ch)
        us = [u for p, _ in paths for u, _ in p]
        uc = (min(us) + max(us)) / 2

        def world(u, v, d, z0=z0, uc=uc):
            return (cx + (u - uc) * N["h"], face_y - d, z0 + v * N["h"])
        for p, closed in paths:
            ribbon(B, p, half, N["depth"], world, closed)
    B.build(G, "Front_house_number", ["frame_black"], "House")


def porch(G):
    P, C = PORCH, COLUMN
    G.box("Front_porch_floor", P["x0"], P["y0"], -0.03, P["x1"], G.GROUND_FRONT_Y, P["floor"], "stone", "House")
    G.box("Porch_column", C["x0"], C["y0"], P["floor"], C["x0"] + C["size"], C["y0"] + C["size"],
          P["soffit"], "stucco", "House")
    rx0, ry0, rx1, ry1 = P["roof"]
    G.box("Front_porch_ceiling", rx0, ry0, P["soffit"], rx1, ry1, P["eave"], "stucco", "House")
    fz0, fz1, ft = P["fascia"]
    fas = Builder()
    fas.box(rx0 - ft, ry0 - ft, fz0, rx1 + ft, ry0, fz1)
    fas.box(rx0 - ft, ry0, fz0, rx0, ry1, fz1)
    fas.box(rx1, ry0, fz0, rx1 + ft, ry1, fz1)
    fas.build(G, "Front_porch_fascia", ["frame_black"], "House")
    # small hip roof, same pitch + eave height as Roof_front_*; its back slope dives into Roof_front_0
    inset = (ry1 - ry0) / 2
    zr = P["eave"] + P["pitch"] * inset
    ym = (ry0 + ry1) / 2
    v = [(rx0, ry0, P["eave"]), (rx1, ry0, P["eave"]), (rx1, ry1, P["eave"]), (rx0, ry1, P["eave"]),
         (rx0 + inset, ym, zr), (rx1 - inset, ym, zr)]
    G.mesh("Front_porch_roof", v, [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)], "roof_metal", "House")
    # recessed downlight in the soffit (02, 06)
    cx, cy = (P["x0"] + P["x1"]) / 2 + 0.1, (C["y0"] + G.GROUND_FRONT_Y) / 2 + 0.1
    G.cyl("Front_porch_downlight", cx, cy, P["soffit"] - 0.006, P["soffit"] + 0.001, 0.055, "front_lens",
          16, "House")
    lamp(G, "Front_porch_downlight_lamp", "SPOT", (cx, cy, P["soffit"] - 0.03), 35, target=(cx, cy, 0), spot=110)
    house_number(G)
    # tall slim alabaster sconces with a black side bracket (02, 03)
    S, wy = SCONCE, G.GROUND_FRONT_Y
    for i, (x, side) in enumerate(SCONCES):
        G.box(f"Wall_light_front_{i}", x - S["w"] / 2, wy - S["d"], S["z0"], x + S["w"] / 2, wy, S["z1"],
              "front_alabaster", "House")
        bx = x + side * S["w"] / 2
        G.box(f"Wall_light_front_{i}_bracket", min(bx, bx + side * 0.022), wy - S["d"] - 0.006, S["z0"] + 0.1,
              max(bx, bx + side * 0.022), wy, S["z1"] - 0.12, "frame_black", "House")
        lamp(G, f"Wall_light_front_{i}_lamp", "POINT", (x, wy - S["d"] - 0.12, (S["z0"] + S["z1"]) / 2), 10)


def chairs(G):
    """Round wicker bowl chairs with white seat cushions (03, 05, 14); shared mesh, linked copies."""
    C = CHAIR
    R, t, M, N = C["r"], C["shell"], 8, 28
    B = Builder()
    rows = []
    for layer, rad in enumerate((R, R - t)):
        grid = []
        for i in range(M + 1):
            ring = []
            for j in range(N):
                th = 2 * math.pi * j / N
                phi_max = math.pi * (0.56 + 0.29 * (1 - math.cos(th)) / 2)     # low front, high back
                phi = 0.2 * math.pi + (phi_max - 0.2 * math.pi) * i / M
                ring.append((rad * math.sin(phi) * math.cos(th), rad * math.sin(phi) * math.sin(th),
                             C["seat"] - rad * math.cos(phi)))
            grid.append(B.verts(ring))
        rows.append(grid)
    out, inn = rows
    for i in range(M):
        B.faces([(out[i] + j, out[i] + (j + 1) % N, out[i + 1] + (j + 1) % N, out[i + 1] + j) for j in range(N)],
                0, True)
        B.faces([(inn[i] + j, inn[i + 1] + j, inn[i + 1] + (j + 1) % N, inn[i] + (j + 1) % N) for j in range(N)],
                0, True)
    B.faces([(out[M] + j, out[M] + (j + 1) % N, inn[M] + (j + 1) % N, inn[M] + j) for j in range(N)])   # rim
    B.faces([[inn[0] + j for j in range(N)]])                                                       # seat pan
    B.faces([[out[0] + j for j in range(N - 1, -1, -1)]])
    B.tube([(0, 0, 0.0), (0, 0, C["seat"] - R * math.cos(0.2 * math.pi) + 0.02)], [C["base_r"], C["base_r"] * 0.8],
           16, 0, cap_start=False)
    cz = C["seat"] - 0.22
    B.tube([(0.03, 0, cz), (0.03, 0, cz + 0.12)], [0.29, 0.28], 20, 1)                               # cushion
    proto = B.build(G, "Front_porch_chair_0", ["front_rattan", "macrame"], "House")
    for k, (x, y, face) in enumerate(CHAIRS):
        o = proto if k == 0 else proto.copy()
        if k:
            o.name = f"Front_porch_chair_{k}"
            G.link(o, "House")
        o.location = (x, y, PORCH["floor"])
        o.rotation_euler = (0, 0, math.radians(face))


# =============================================================================================
# stone basin fountain (03, 07)
# =============================================================================================
def basin(G, rnd):
    Bs = BASIN
    cx, cy, rx, ry, h = Bs["x"], Bs["y"], Bs["rx"], Bs["ry"], Bs["h"]
    prof = [(1.00, 0.00), (1.04, 0.22), (1.05, 0.50), (1.00, 0.86), (0.97, 1.00),     # outer
            (0.74, 0.97), (0.67, 0.80), (0.50, 0.68), (0.0, 0.64)]                     # inner bowl
    N = 30
    ph = [rnd.uniform(0, 2 * math.pi) for _ in range(5)]

    def wob(a):
        return 1 + 0.05 * math.sin(2 * a + ph[0]) + 0.035 * math.sin(3 * a + ph[1]) + 0.02 * math.sin(5 * a + ph[2])
    rim = [0.045 * math.sin(2 * a + ph[3]) + 0.03 * math.sin(4 * a + ph[4]) + rnd.uniform(-0.025, 0.025)
           for a in (2 * math.pi * j / N for j in range(N))]
    for j in rnd.sample(range(N), 3):                    # a few chipped notches in the rim
        rim[j] -= rnd.uniform(0.05, 0.1)
    B = Builder()
    rings = []
    for k, (rf, zf) in enumerate(prof[:-1]):
        ring = []
        for j in range(N):
            a = 2 * math.pi * j / N
            s = wob(a) * (1 + rnd.uniform(-0.025, 0.025)) * rf
            z = zf * h + (rim[j] * h if k in (4, 5) else rnd.uniform(-0.01, 0.01) * (k > 0))
            ring.append((cx + rx * s * math.cos(a), cy + ry * s * math.sin(a), z))
        rings.append(B.verts(ring))
    centre = B.verts([(cx, cy, prof[-1][1] * h)])
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        B.faces([(a + j, a + (j + 1) % N, b + (j + 1) % N, b + j) for j in range(N)])
    last = rings[-1]
    B.faces([(last + j, last + (j + 1) % N, centre) for j in range(N)])
    B.build(G, "Front_stone_basin", ["front_limestone"])
    # water surface just below the rim
    wz, wr = 0.86 * h, 0.70
    ring = [(cx + rx * wr * wob(2 * math.pi * j / N) * math.cos(2 * math.pi * j / N),
             cy + ry * wr * wob(2 * math.pi * j / N) * math.sin(2 * math.pi * j / N), wz) for j in range(N)]
    G.mesh("Front_basin_water", ring, [tuple(range(N))], "water", COLL)
    # bent copper spout rising behind the basin, pouring into it
    px, py = cx - 0.12, cy + ry * 1.08 + 0.04
    rb = 0.09
    path = [(px, py, -0.05), (px, py, 0.6), (px, py, 1.0)]
    path += [(px, py - rb + rb * math.cos(math.pi * i / 8), 1.0 + rb * math.sin(math.pi * i / 8)) for i in range(1, 9)]
    path += [(px, py - 2 * rb, 0.86)]
    sp = Builder()
    sp.tube(path, [0.019] * len(path), 8, cap_end=True)
    sp.build(G, "Front_basin_spout", ["front_copper"])
    st = Builder()
    st.tube([(px, py - 2 * rb, 0.86), (px, py - 2 * rb - 0.004, wz)], [0.007, 0.009], 6)
    st.build(G, "Front_basin_stream", ["front_stream"])


# =============================================================================================
# paths, turf, patio
# =============================================================================================
def paths(G, rnd):
    turf = Builder()
    for x0, y0, x1, y1 in TURF:
        turf.box(x0, y0, -0.03, x1, y1, 0.03)
    x0, y0, x1, y1 = GATE_TURF
    turf.box(x0, y0, -0.05, x1, y1, PARKWAY[2])
    turf.build(G, "Front_turf", ["front_turf"])
    stones = Builder()
    for cx, cy, a, b, rot, top in STONES:
        stones.prism(blob(rnd, cx, cy, a, b, rot, n=14), top - 0.06, top)
    stones.build(G, "Front_path", ["front_flagstone"])


def patio(G, rnd):
    P = PATIO
    cx, cy, R = P["cx"], P["cy"], P["r"]
    disc = [(cx + R * math.cos(2 * math.pi * k / 64), cy + R * math.sin(2 * math.pi * k / 64)) for k in range(64)]
    base = Builder()
    base.prism(disc, -0.03, P["base"])
    base.build(G, "Side_patio", ["front_mortar"])
    # crazy paving: Voronoi cells of jittered seeds, shrunk by half the joint each side (07, 15)
    seeds = []
    for _ in range(5000):
        a, rr = rnd.uniform(0, 2 * math.pi), R * math.sqrt(rnd.random())
        p = (cx + rr * math.cos(a), cy + rr * math.sin(a))
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > P["spacing"] ** 2 for q in seeds):
            seeds.append(p)
    edge = [(cx + (R - 0.03) * math.cos(2 * math.pi * k / 64), cy + (R - 0.03) * math.sin(2 * math.pi * k / 64))
            for k in range(64)]
    B = Builder()
    for i, p in enumerate(seeds):
        poly = edge[:]
        for j, q in enumerate(seeds):
            d = math.hypot(q[0] - p[0], q[1] - p[1])
            if i == j or d > 3 * P["spacing"]:
                continue
            n = ((q[0] - p[0]) / d, (q[1] - p[1]) / d)
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            poly = clip(poly, n, m[0] * n[0] + m[1] * n[1] - P["gap"] / 2)
            if len(poly) < 3:
                break
        if len(poly) >= 3 and abs(area(poly)) > 0.004:
            B.prism(poly, P["base"] - 0.01, P["top"] + rnd.uniform(-0.004, 0.004))
    B.build(G, "Side_patio_stones", ["front_flagstone"])


def uplights(G):
    B = Builder()
    for i, (x, y) in enumerate(UPLIGHTS):
        head = (x, y + 0.05, 0.16)
        B.tube([(x, y - 0.02, 0.0), (x, y + 0.02, 0.10)], [0.012, 0.012], 6, 0)          # stake
        B.tube([(x, y, 0.08), head], [0.032, 0.034], 10, 0)                              # body
        B.tube([head, (x, y + 0.051, 0.161)], [0.026, 0.026], 10, 1)                     # lens
        lamp(G, f"Front_uplight_{i}", "SPOT", (x, y + 0.08, 0.2), 14, target=(x, WALL["y0"], 1.0), spot=70)
    B.build(G, "Front_uplight_fixtures", ["frame_black", "front_lens"])


# =============================================================================================
def apply(G):
    for prefix in ("Fence_", "Front_planter_wall", "Porch_column", "Front_path", "Side_patio",
                   "Wall_light_front_", "Street", "Sidewalk"):
        G.remove(prefix)
    rnd = random.Random(SEED)
    materials(G)
    street(G)
    fence(G, rnd)
    porch(G)
    chairs(G)
    basin(G, rnd)
    paths(G, rnd)
    patio(G, rnd)
    uplights(G)
    for name, (loc, target, lens, _frame) in CAMS.items():
        G.SHOTS[name] = (loc, target, lens)
