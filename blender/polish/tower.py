"""Charred-wood tower + white stair bulkhead (polish module "tower"; owns Tower*, Bulkhead*).

What the video shows (frames/exterior/...):
- 04 close-up: narrow (~14 cm) vertical shou-sugi-ban boards with dark cathedral grain, thin black
  gaps, staggered butt joints; a flashing cap at the flat top; a thick black-ringed porthole with
  recessed glass.
- 05 / 06 street views: two dark faces meet in a convex corner. The left face is angled (~45 deg,
  facing south-west) and carries the porthole just below the hip-roof eave; the right (south) face
  has a tall narrow stair window near its east end; a white chimney stack rises at that end.
- 14 / 22 / 01 aerials: the tower stands on the lower front roofs, its SW face runs from the hip-roof
  wing's front wall to the south face, the porthole is centred on the SW face, and the white bulkhead
  behind it shares the same flat roof (white rounded coping visible behind the dark cap).
- 15 top-down: tower + bulkhead form one outline - a prow pointing west/front, a straight east wall
  flush with the roof-deck turf, and a flattened round end toward the pool ~62 % of the house depth.
- 20 rooftop: bulkhead in white stucco, thick rounded coping, grey membrane roof, black-framed glass
  door on the east side just before the rounded end.

Geometry is built directly (no modifiers): a backing shell, individual board meshes with real gaps
(one joined mesh), sweeps for the cap / coping, and explicit porthole, window and door assemblies.
The cladding texture is generated here (procedural cathedral growth rings + Poly Haven veneer micro
detail) into packed JPEG images, so it renders in Cycles and exports to glTF as plain image textures.
After building, G.TOWER / G.BULKHEAD are updated to the new footprint for modules that run later.
"""
import math
import os
import random
import tempfile

import numpy as np

POLYHAVEN_ASSETS = ["black_oak_veneer"]   # micro grain blended into the generated cladding maps

# ---------------------------------------------------------------- plan (metres, see docstring)
EAST_X = 8.9           # south face east end = bulkhead east wall (roof-deck turf starts at x 9.0)
WEST_X = 6.45          # south face west end = bulkhead west wall -> 2.45 m wide (frames 05, 14, 15)
PROW_DX = 1.75         # prow vertex lies this far west of the south-west corner (frames 15, 22)
PROW_DEPTH = 1.5       # ...and at least this far behind the south face (frame 15: ~1.5-2.0)
REAR_FROM_FRONT = 7.2  # rounded end, measured from the deck block's front wall (frame 15: ~60 %)
REAR_DEPTH = 0.75      # the round end is a flattened half-ellipse (frames 15, 20)
ARC_SEG = 24
# The prow vertex sits on the hip-roof wing's front wall and the south face is flush with the
# roof-deck block's front (frames 14, 15, 22). The base model has both fronts at y 7.0, so there the
# tower stands PROW_DEPTH proud of the facade over the lower roofs; if another module sets the wing
# back, the layout follows it (see house_fronts()).

# ---------------------------------------------------------------- heights
Z_BASE = 3.2           # top of the single-storey front projection the tower stands on
ROOF_Z = 6.2           # main roof / roof-deck level (bulkhead walls start here)
TOP = 9.2              # flat top of tower + bulkhead, 3 m above the deck (frames 05, 06, 14)
PAR_W = 0.22           # parapet / coping width
MEMB_Z = TOP - 0.2     # membrane roof inside the parapet (frame 20)
CAP_H = 0.30           # flashing cap band on the clad faces (frame 04)
CAP_OUT = 0.035        # cap projection beyond the board face

# ---------------------------------------------------------------- cladding
BOARD_PITCH = 0.14     # board width incl. gap (frame 04: ~14 cm boards)
BOARD_GAP = 0.008
BOARD_T = 0.022        # board thickness proud of the backing
SEG_MAX = 2.5          # longest board before a butt joint
TEX_W, TEX_H = 1024, 512  # generated cladding maps: columns run along the grain, rows across boards
TEX_STRIPS = 8         # the rows hold 8 independent board-width strips
TEX_MARGIN = 2         # texels kept clear at each strip edge
TEX_ALONG = 2.8        # metres of grain along one texture width
CHAR_RGB = (0.036, 0.035, 0.035)   # linear albedo of the brushed char (rings darken it)

# ---------------------------------------------------------------- openings
PORTHOLE_Z = 5.5       # centre height: top just under the wing's eave (frames 05, 06, 22)
PORTHOLE_R_OUT = 0.55  # black frame ring outer radius (~1.1 m overall, frames 04, 22)
PORTHOLE_R_IN = 0.45   # glass radius
PORTHOLE_R_CUT = 0.50  # boards stop here (hidden under the ring)
PORTHOLE_DEPTH = 0.20  # glass recess behind the board face ("deep reveal")
RING_PROUD = 0.045
PORTHOLE_S = 0.53      # position along the SW face (0 = prow, 1 = south corner)
WINDOW_BOARDS = (8, 12)  # tall stair window: board columns (of 18) on the south face, 44-67 % across
WINDOW_Z = (4.3, 6.55)   # (frames 05, 06, 14)
DOOR_W, DOOR_GAP = 0.9, 0.35  # bulkhead door on the east wall, just before the round end (frame 20)
DOOR_Z = (ROOF_Z + 0.02, ROOF_Z + 2.15)
CHIMNEY_W = 0.34       # white stack at the south face's east end (frames 05, 06, 14, 22)


def apply(G):
    for prefix in ("Tower", "Bulkhead"):
        G.remove(prefix)
    rnd = random.Random(1159)

    materials(G)
    wing_y, block_y = house_fronts(G)
    front_y = min(block_y, wing_y - PROW_DEPTH)
    rear_y = block_y + REAR_FROM_FRONT
    V1 = (WEST_X - PROW_DX, wing_y)
    V2 = (WEST_X, front_y)
    V3 = (EAST_X, front_y)
    sw = (V2[0] - V1[0], V2[1] - V1[1])
    V4 = (WEST_X, V1[1] + (WEST_X - V1[0]) * (-sw[0] / sw[1]))   # NW face square to the SW face
    cy = rear_y - REAR_DEPTH
    cx, ax = (WEST_X + EAST_X) / 2, (EAST_X - WEST_X) / 2
    arc = [(cx + ax * math.cos(math.pi * i / ARC_SEG), cy + REAR_DEPTH * math.sin(math.pi * i / ARC_SEG))
           for i in range(ARC_SEG + 1)]
    # closed CCW outline (outward normal = right-hand side of each edge)
    outline = [V2, V3, (EAST_X, block_y)] + arc + [V4, V1]
    n_out = len(outline)
    iV2, iV3, iE7 = 0, 1, 2
    iV4, iV1 = n_out - 2, n_out - 1

    # --- backing / walls: one quad strip per outline edge, with holes for openings
    clad = {(iV4, iV1): "NW", (iV1, iV2): "SW", (iV2, iV3): "S"}
    faces_info = {}
    for i in range(n_out):
        a, b = outline[i], outline[(i + 1) % n_out]
        key = (i, (i + 1) % n_out)
        L = math.dist(a, b)
        name = clad.get(key)
        if name:
            z0 = ROOF_Z - 0.1 if name == "NW" else Z_BASE
        else:
            z0 = Z_BASE if key == (iV3, iE7) else ROOF_Z
        faces_info[key] = dict(a=a, b=b, L=L, z0=z0, name=name)

    S = faces_info[(iV2, iV3)]
    SW = faces_info[(iV1, iV2)]
    n_s = round(S["L"] / BOARD_PITCH)
    p_s = S["L"] / n_s
    win = (WINDOW_BOARDS[0] * p_s, WINDOW_BOARDS[1] * p_s, *WINDOW_Z)
    S["holes"] = [win]
    sc = SW["L"] * PORTHOLE_S
    SW["holes"] = [(sc - PORTHOLE_R_OUT, sc + PORTHOLE_R_OUT,
                    PORTHOLE_Z - PORTHOLE_R_OUT, PORTHOLE_Z + PORTHOLE_R_OUT)]
    door_face = faces_info[(iE7, iE7 + 1)]
    d1 = door_face["L"] - DOOR_GAP
    door = (d1 - DOOR_W, d1, *DOOR_Z)
    door_face["holes"] = [door]

    wall_top = TOP - 0.06
    stucco_v, stucco_f, back_v, back_f = [], [], [], []
    for key, f in faces_info.items():
        tgt = (back_v, back_f) if f["name"] else (stucco_v, stucco_f)
        wall_grid(tgt, f, f["z0"], wall_top, f.get("holes", []))
    walls = G.mesh("Bulkhead_walls", stucco_v, stucco_f, "stucco", "House")
    smooth_by_angle(walls, 35)
    G.mesh("Tower_backing", back_v, back_f, "tower_backing", "House")

    # --- boards
    bv, bf, buv = [], [], []
    for (i, j), f in faces_info.items():
        if not f["name"]:
            continue
        prev_key = ((i - 1) % n_out, i)
        next_key = (j, (j + 1) % n_out)
        f["ext0"] = miter_ext(faces_info, prev_key, (i, j)) if faces_info[prev_key]["name"] else 0.0
        f["ext1"] = miter_ext(faces_info, (i, j), next_key) if faces_info[next_key]["name"] else 0.0
    for key in ((iV4, iV1), (iV1, iV2), (iV2, iV3)):
        f = faces_info[key]
        circle = (sc, PORTHOLE_Z, PORTHOLE_R_CUT) if f["name"] == "SW" else None
        rect = win if f["name"] == "S" else None
        boards_on_face(bv, bf, buv, f, rnd, circle, rect)
    boards = G.mesh("Tower_boards", bv, bf, "tower_cladding", "House")
    set_uvs(boards, buv)

    # --- flashing cap over the clad faces, coping + membrane roof
    cap_path = [V4, V1, V2, V3]
    cap_prof = [(BOARD_T - 0.004, TOP - CAP_H), (BOARD_T + CAP_OUT, TOP - CAP_H),
                (BOARD_T + CAP_OUT, TOP + 0.012), (-PAR_W - 0.004, TOP + 0.012)]
    v, f_ = sweep(cap_path, False, cap_prof)
    G.mesh("Tower_cap", v, f_, "tower_cap", "House")
    r = 0.07
    cop_prof = [(0.0, wall_top), (0.022, wall_top), (0.022, TOP - 0.035)]
    cop_prof += [(0.022 - r + r * math.cos(a), TOP - r + r * math.sin(a))
                 for a in (math.radians(d) for d in (30, 60, 90))]
    cop_prof += [(-PAR_W + r - r * math.cos(math.radians(d)), TOP - r + r * math.sin(math.radians(d)))
                 for d in (90, 60, 30)]
    cop_prof += [(-PAR_W, TOP - 0.05), (-PAR_W, MEMB_Z)]
    v, f_ = sweep(outline, True, cop_prof)
    coping = G.mesh("Bulkhead_coping", v, f_, "stucco", "House")
    smooth_by_angle(coping, 35)
    miters = miter_vectors(outline, True)
    memb = [(x + mx * -PAR_W, y + my * -PAR_W, MEMB_Z) for (x, y), (mx, my) in zip(outline, miters)]
    G.mesh("Bulkhead_roof", memb, [tuple(range(len(memb)))], "bulkhead_membrane", "House")

    # --- porthole: black ring, deep reveal, recessed glass, flange closing the backing hole
    porthole(G, SW, sc)
    # --- tall stair window on the south face
    rect_opening(G, "Tower_window", S, win, BOARD_T + 0.03, -0.12, 0.05)
    # --- bulkhead door (east wall)
    rect_opening(G, "Bulkhead_door", door_face, door, 0.03, -0.06, 0.05, pane="bulkhead_door_leaf")

    # --- chimney stack at the south face's east end
    x0, x1 = EAST_X, EAST_X + CHIMNEY_W
    y0, y1 = front_y + 0.12, max(front_y + 0.6, block_y - 0.02)
    G.box("Tower_chimney", x0, y0, Z_BASE, x1, y1, TOP - 0.02, "stucco", "House")
    G.box("Tower_chimney_cap", x0 - 0.05, y0 - 0.05, TOP - 0.02, x1 + 0.05, y1, TOP + 0.1,
          "stucco", "House")
    G.box("Tower_chimney_flue", x0 + 0.08, y0 + 0.1, TOP + 0.1, x1 - 0.08, y0 + 0.42, TOP + 0.22,
          "stucco", "House")

    # share the new footprint with modules that run later (same dict objects as the build script's)
    G.TOWER.update(x0=V1[0], x1=EAST_X, y0=front_y, y1=V4[1], top=TOP)
    G.BULKHEAD.update(x0=WEST_X, x1=EAST_X, y0=V4[1], y1=rear_y, top=TOP)

    # review cameras for this area (frame each one is matched to in the comment)
    G.SHOTS.update({
        "tower_close": ((5.6, 3.3, 4.6), (5.75, 6.3, 7.6), 20),          # exterior/04
        "tower_street": ((6.2, -15.5, 1.7), (7.0, 6.5, 6.9), 70),       # exterior/06 (crop)
        "tower_sw": ((0.5, -29.0, 16.5), (7.3, 8.0, 7.4), 75),         # exterior/22 (crop)
        "bulkhead_roof": ((11.8, 7.3, 12.5), (9.0, 17.0, 6.5), 18),     # exterior/20
        "tower_top": ((7.6, 10.2, 32.0), (7.6, 10.2, 0.0), 45),         # exterior/15 (rotated crop)
        "tower_rear": ((1.0, 24.0, 15.0), (7.0, 10.0, 7.5), 40),        # junction check (no frame)
        "porthole_detail": ((3.9, 4.0, 5.1), (5.75, 6.15, 5.6), 50),    # exterior/04 (porthole crop)
        "bulkhead_door": ((12.5, 10.0, 8.0), (8.9, 12.3, 7.3), 30),     # exterior/20 (door crop)
    })


def house_fronts(G):
    """Front wall planes (min y) of the hip-roof wing and of the roof-deck block, as built so far."""
    def front(name):
        o = G.bpy.data.objects.get(name)
        if o is None or o.type != "MESH" or not o.data.vertices:
            return G.HOUSE["y0"]
        return min((o.matrix_world @ v.co).y for v in o.data.vertices)
    return front("House_left_wing"), front("House_right_block")


# ======================================================================= materials
def materials(G):
    bpy = G.bpy
    G.mat("tower_backing", (0.006, 0.006, 0.006), 0.95)
    G.mat("tower_cap", (0.08, 0.072, 0.064), 0.5, 0.3)     # weathered dark-bronze flashing (frame 04)
    G.mat("bulkhead_membrane", (0.56, 0.56, 0.54), 0.8)      # light grey TPO roof (frame 20)
    G.mat("tower_porthole_glass", (0.16, 0.17, 0.18), 0.04, 0.7)  # mirror-like, shows sky (04, 22)
    G.mat("tower_reveal", (0.62, 0.62, 0.6), 0.6)                 # painted porthole sleeve (04)
    G.mat("bulkhead_door_leaf", (0.8, 0.8, 0.78), 0.45)           # white painted door (frame 20)
    if "tower_cladding" in G.MAT:
        return G.MAT
    alb, nrm = charred_maps(bpy, os.path.join(G.TEX_DIR, "black_oak_veneer", "diff.jpg"))
    m = bpy.data.materials.new("tower_cladding")
    m.use_nodes = True
    nt = m.node_tree
    n, ln = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]

    def img_node(name, arr, colour):
        im = bpy.data.images.new(name, TEX_W, TEX_H, alpha=False)
        im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        px = np.ones((TEX_H, TEX_W, 4), np.float32)
        px[..., :3] = arr
        im.pixels.foreach_set(px.ravel())
        # pack as JPEG bytes (via a transient temp file) so glTF export embeds a small JPEG, not a PNG
        tmp = os.path.join(tempfile.gettempdir(), f"{name}_{os.getpid()}.jpg")
        im.filepath_raw = tmp
        im.file_format = "JPEG"
        im.save(quality=92)
        im.pack()
        im.filepath_raw = f"//{name}.jpg"
        os.remove(tmp)
        node = n.new("ShaderNodeTexImage")
        node.image = im
        return node

    a = img_node("tower_cladding_albedo", alb, True)
    ln.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    nn = img_node("tower_cladding_normal", nrm, False)
    nm = n.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.8
    ln.new(nn.outputs["Color"], nm.inputs["Color"])
    ln.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.55          # soft sheen of oiled, brushed char
    bsdf.inputs["Specular IOR Level"].default_value = 0.55
    G.MAT["tower_cladding"] = m
    return G.MAT


def value_noise(shape, cells, rng):
    """Smooth 2D value noise of `shape` with (cy, cx) lattice cells."""
    cy, cx = cells
    g = rng.standard_normal((cy + 3, cx + 3)).astype(np.float32)
    H, W = shape
    y = np.linspace(0, cy, H, endpoint=False) + 1
    x = np.linspace(0, cx, W, endpoint=False) + 1
    yi, xi = y.astype(int), x.astype(int)
    fy, fx = (y - yi)[:, None], (x - xi)[None, :]
    sy, sx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b = g[yi][:, xi], g[yi][:, xi + 1]
    c, d = g[yi + 1][:, xi], g[yi + 1][:, xi + 1]
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy


def growth_rings(seed=5):
    """Flat-sawn growth rings: rows = across a board (TEX_STRIPS strips), cols = along the grain.

    Each strip is a board cut from a log whose pith wanders slowly below the face, so ring contours
    form the long cathedral arches seen in frame 04.
    """
    sh = TEX_H // TEX_STRIPS
    board_m = BOARD_PITCH * sh / (sh - 2 * TEX_MARGIN)
    s = (np.arange(sh) / sh - 0.5) * board_m
    out = np.zeros((TEX_H, TEX_W), np.float32)
    for k in range(TEX_STRIPS):
        r2 = np.random.default_rng(seed * 100 + k)
        sp = r2.uniform(0.008, 0.012)                              # ring spacing
        s0 = r2.uniform(-0.07, 0.07) + 0.025 * value_noise((1, TEX_W), (1, 3), r2)[0]
        d = 0.02 + r2.uniform(0.0, 0.05) + 0.06 * np.abs(value_noise((1, TEX_W), (1, 4), r2)[0])
        warp = 0.003 * value_noise((sh, TEX_W), (2, 14), r2) + 0.0008 * value_noise((sh, TEX_W), (6, 90), r2)
        r = np.sqrt(d[None, :] ** 2 + (s[:, None] - s0[None, :]) ** 2) + warp
        f = (r / sp) % 1.0
        width = 0.16 + 0.06 * value_noise((sh, TEX_W), (2, 12), r2)
        out[k * sh:(k + 1) * sh] = np.exp(-((f - 0.5) / width) ** 2)
    return out


def charred_maps(bpy, veneer_path):
    """Albedo (sRGB-encoded) and tangent-space normal map for the cladding, as float arrays."""
    rings = growth_rings()
    rng = np.random.default_rng(11)
    blot = value_noise(rings.shape, (8, 30), rng)
    detail = np.zeros_like(rings)
    if os.path.exists(veneer_path):                 # Poly Haven veneer: fine pores / fibre detail
        im = bpy.data.images.load(veneer_path, check_existing=True)
        w, h = im.size
        if w >= TEX_W and h >= TEX_H:
            px = np.empty(w * h * 4, np.float32)
            im.pixels.foreach_get(px)
            lum = px.reshape(h, w, 4)[:TEX_H, :TEX_W, :3] @ np.array([0.3, 0.5, 0.2], np.float32)
            detail = np.clip((lum - lum.mean()) / (lum.std() + 1e-6), -2.5, 2.5)
    shade = (1 + 0.12 * blot) * (1 - 0.55 * rings) * (1 + 0.10 * detail)
    alb_lin = np.clip(np.array(CHAR_RGB, np.float32)[None, None] * shade[..., None], 0, 1)
    alb = np.where(alb_lin <= 0.0031308, alb_lin * 12.92, 1.055 * alb_lin ** (1 / 2.4) - 0.055)
    height = 0.7 * (1 - rings) + 0.12 * detail      # latewood rings stand proud after brushing
    du = np.gradient(height, axis=1) / (TEX_ALONG / TEX_W)                      # per metre along
    dv = np.gradient(height, axis=0) / (BOARD_PITCH / (TEX_H / TEX_STRIPS))     # per metre across
    k = 0.0025
    nx, ny = -k * du, -k * dv
    inv = 1 / np.sqrt(nx * nx + ny * ny + 1)
    nrm = np.stack([nx * inv, ny * inv, inv], -1) * 0.5 + 0.5
    return alb.astype(np.float32), nrm.astype(np.float32)


# ======================================================================= geometry helpers
def frame_of(f):
    (ax, ay), (bx, by) = f["a"], f["b"]
    L = f["L"]
    d = ((bx - ax) / L, (by - ay) / L)
    n = (d[1], -d[0])
    return d, n


def world(f, s, out, z):
    d, n = frame_of(f)
    return (f["a"][0] + d[0] * s + n[0] * out, f["a"][1] + d[1] * s + n[1] * out, z)


def wall_grid(target, f, z0, z1, holes):
    """Planar wall quad from a to b, split into a grid so rectangular holes can be left open."""
    verts, faces = target
    ss = sorted({0.0, f["L"], *[h[0] for h in holes], *[h[1] for h in holes]})
    zs = sorted({z0, z1, *[h[2] for h in holes], *[h[3] for h in holes]})
    for i in range(len(ss) - 1):
        for j in range(len(zs) - 1):
            sm, zm = (ss[i] + ss[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if any(h[0] < sm < h[1] and h[2] < zm < h[3] for h in holes):
                continue
            b = len(verts)
            verts += [world(f, ss[i], 0, zs[j]), world(f, ss[i + 1], 0, zs[j]),
                      world(f, ss[i + 1], 0, zs[j + 1]), world(f, ss[i], 0, zs[j + 1])]
            faces.append((b, b + 1, b + 2, b + 3))


def miter_ext(faces_info, k0, k1):
    """Extra length the outer board face needs to meet the neighbouring clad face at a convex corner."""
    d0, _ = frame_of(faces_info[k0])
    d1, _ = frame_of(faces_info[k1])
    cross = d0[0] * d1[1] - d0[1] * d1[0]
    if cross <= 0:     # only a left turn on a CCW outline is a convex corner
        return 0.0
    turn = math.atan2(cross, d0[0] * d1[0] + d0[1] * d1[1])
    return BOARD_T * math.tan(turn / 2)


def boards_on_face(verts, faces, uvs, f, rnd, circle=None, rect=None):
    """Vertical boards with butt joints; circle (sc, zc, r) / rect (s0, s1, z0, z1) are cut out."""
    L = f["L"]
    n = max(1, round(L / BOARD_PITCH))
    p = L / n
    z_lo = f["z0"] + 0.02
    z_hi = TOP - 0.06
    holes_z = []
    if circle:
        holes_z.append((circle[1] - circle[2] - 0.15, circle[1] + circle[2] + 0.15))
    if rect:
        holes_z.append((rect[2] - 0.15, rect[3] + 0.15))
    for c in range(n):
        s0 = c * p + (0 if c == 0 else BOARD_GAP / 2)
        s1 = (c + 1) * p - (0 if c == n - 1 else BOARD_GAP / 2)
        e0 = f.get("ext0", 0.0) if c == 0 else 0.0
        e1 = f.get("ext1", 0.0) if c == n - 1 else 0.0
        # butt joints: staggered, kept out of the opening zone
        H = z_hi - z_lo
        nseg = max(1, math.ceil(H / SEG_MAX))
        cuts = []
        for k in range(1, nseg):
            zc = z_lo + H * k / nseg + rnd.uniform(-0.45, 0.45) * (H / nseg - 0.6) / max(H / nseg, 1e-3)
            for lo, hi in holes_z:
                if lo < zc < hi:
                    zc = lo if zc - lo < hi - zc else hi
            cuts.append(zc)
        zs = [z_lo] + sorted(cuts) + [z_hi]
        for k in range(len(zs) - 1):
            za, zb = zs[k] + (0.002 if k else 0), zs[k + 1] - (0.002 if k < len(zs) - 2 else 0)
            if zb - za < 0.05:
                continue
            pieces = cut_piece(s0, s1, za, zb, circle, rect)
            seg_len = zb - za
            u0 = rnd.uniform(0.01, max(0.011, 0.99 - seg_len / TEX_ALONG))
            strip = rnd.randrange(TEX_STRIPS)
            depth = BOARD_T + rnd.uniform(-0.0015, 0.0015)
            for ss, bot, top in pieces:
                board_piece(verts, faces, uvs, f, ss, bot, top, depth, e0, e1, s0, s1, za, u0, strip)


def cut_piece(s0, s1, za, zb, circle, rect):
    """Split one board segment around an opening; returns [(s_samples, z_bottom[], z_top[])]."""
    if rect and rect[0] - 1e-6 <= (s0 + s1) / 2 <= rect[1] + 1e-6 and za < rect[3] and zb > rect[2]:
        out = []
        if za < rect[2]:
            out.append(([s0, s1], [za, za], [min(zb, rect[2])] * 2))
        if zb > rect[3]:
            out.append(([s0, s1], [max(za, rect[3])] * 2, [zb, zb]))
        return out
    if circle:
        sc, zc, r = circle
        if s1 > sc - r and s0 < sc + r and zb > zc - r and za < zc + r:
            K = 8
            ss = [s0 + (s1 - s0) * k / (K - 1) for k in range(K)]
            h = [math.sqrt(max(0.0, r * r - (s - sc) ** 2)) for s in ss]
            out = []
            lo_top = [min(zb, max(za, zc - hk)) for hk in h]
            hi_bot = [max(za, min(zb, zc + hk)) for hk in h]
            if max(t - za for t in lo_top) > 0.01:
                out.append((ss, [za] * K, lo_top))
            if max(zb - b for b in hi_bot) > 0.01:
                out.append((ss, hi_bot, [zb] * K))
            return out
    return [([s0, s1], [za, za], [zb, zb])]


def board_piece(verts, faces, uvs, f, ss, bot, top, depth, e0, e1, bs0, bs1, za, u0, strip):
    """Board strip with front, end and side faces (back face omitted: it sits on the backing)."""
    K = len(ss)
    so = list(ss)
    if e0:
        so[0] -= e0
    if e1:
        so[-1] += e1
    strip_h = TEX_H / TEX_STRIPS

    def uv(s, z):
        v = (strip * strip_h + TEX_MARGIN + (strip_h - 2 * TEX_MARGIN) * (s - bs0) / (bs1 - bs0)) / TEX_H
        return (u0 + (z - za) / TEX_ALONG, v)

    def quad(pts, uvq):
        b = len(verts)
        verts.extend(pts)
        faces.append((b, b + 1, b + 2, b + 3))
        uvs.extend(uvq)

    # end and side faces map a thin, non-degenerate strip (board thickness) so tangents stay valid
    for k in range(K - 1):
        # front
        quad([world(f, so[k], depth, bot[k]), world(f, so[k + 1], depth, bot[k + 1]),
              world(f, so[k + 1], depth, top[k + 1]), world(f, so[k], depth, top[k])],
             [uv(ss[k], bot[k]), uv(ss[k + 1], bot[k + 1]), uv(ss[k + 1], top[k + 1]), uv(ss[k], top[k])])
        # bottom end (faces down / into the opening)
        quad([world(f, ss[k], 0, bot[k]), world(f, ss[k + 1], 0, bot[k + 1]),
              world(f, so[k + 1], depth, bot[k + 1]), world(f, so[k], depth, bot[k])],
             [uv(ss[k], bot[k] - depth), uv(ss[k + 1], bot[k + 1] - depth),
              uv(ss[k + 1], bot[k + 1]), uv(ss[k], bot[k])])
        # top end
        quad([world(f, so[k], depth, top[k]), world(f, so[k + 1], depth, top[k + 1]),
              world(f, ss[k + 1], 0, top[k + 1]), world(f, ss[k], 0, top[k])],
             [uv(ss[k], top[k]), uv(ss[k + 1], top[k + 1]),
              uv(ss[k + 1], top[k + 1] + depth), uv(ss[k], top[k] + depth)])
    # sides
    i0, i1 = bs0 + depth, bs1 - depth      # texture coordinate just inside the board's strip
    quad([world(f, ss[0], 0, bot[0]), world(f, so[0], depth, bot[0]),
          world(f, so[0], depth, top[0]), world(f, ss[0], 0, top[0])],
         [uv(i0, bot[0]), uv(bs0, bot[0]), uv(bs0, top[0]), uv(i0, top[0])])
    quad([world(f, so[-1], depth, bot[-1]), world(f, ss[-1], 0, bot[-1]),
          world(f, ss[-1], 0, top[-1]), world(f, so[-1], depth, top[-1])],
         [uv(bs1, bot[-1]), uv(i1, bot[-1]), uv(i1, top[-1]), uv(bs1, top[-1])])


def set_uvs(obj, uvs):
    me = obj.data
    layer = me.uv_layers.new(name="UVMap")
    flat = [c for uv in uvs for c in uv]
    # from_pydata keeps loop order = face vertex order, which matches how uvs were appended
    layer.data.foreach_set("uv", flat)


def miter_vectors(pts, closed):
    """Per-vertex offset vectors (outward for a CCW path) so that p + o*m offsets edges by o."""
    n = len(pts)
    m = n if closed else n - 1
    normals = []
    for i in range(m):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay)
        normals.append(((by - ay) / L, -(bx - ax) / L))
    out = []
    for i in range(n):
        if closed:
            e0, e1 = normals[i - 1], normals[i % m]
        else:
            e0, e1 = normals[max(i - 1, 0)], normals[min(i, m - 1)]
        d = 1 + e0[0] * e1[0] + e0[1] * e1[1]
        out.append(((e0[0] + e1[0]) / d, (e0[1] + e1[1]) / d))
    return out


def sweep(path, closed, profile):
    """Sweep a 2D (outward offset, z) profile along a path with mitred corners."""
    mit = miter_vectors(path, closed)
    verts = [(x + mx * o, y + my * o, z) for (x, y), (mx, my) in zip(path, mit) for o, z in profile]
    P, n = len(profile), len(path)
    faces = []
    for i in range(n if closed else n - 1):
        i2 = (i + 1) % n
        for j in range(P - 1):
            faces.append((i * P + j, i2 * P + j, i2 * P + j + 1, i * P + j + 1))
    if not closed:
        faces.append(tuple(range(P - 1, -1, -1)))
        faces.append(tuple((n - 1) * P + j for j in range(P)))
    return verts, faces


def smooth_by_angle(obj, deg):
    me = obj.data
    for poly in me.polygons:
        poly.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(deg))


def ring_mesh(f, sc, zc, r0, r1, out0, out1, seg=48):
    """Annulus (out0 == out1) or tube (r0 == r1) on a face's local frame around (sc, zc)."""
    verts, faces = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        c, s = math.cos(a), math.sin(a)
        verts.append(world(f, sc + r0 * c, out0, zc + r0 * s))
        verts.append(world(f, sc + r1 * c, out1, zc + r1 * s))
    for k in range(seg):
        a0, b0 = 2 * k, 2 * k + 1
        a1, b1 = 2 * ((k + 1) % seg), 2 * ((k + 1) % seg) + 1
        faces.append((a0, a1, b1, b0))
    return verts, faces


def porthole(G, f, sc):
    zc = PORTHOLE_Z
    front = BOARD_T + RING_PROUD
    ring_front = ring_mesh(f, sc, zc, PORTHOLE_R_OUT, PORTHOLE_R_IN, front, front)
    ring_side = ring_mesh(f, sc, zc, PORTHOLE_R_OUT, PORTHOLE_R_OUT, -0.002, front)
    ring_lip = ring_mesh(f, sc, zc, PORTHOLE_R_IN, PORTHOLE_R_IN, front, front - 0.05)
    verts, faces = [], []
    for v, fa in (ring_front, ring_side, ring_lip):
        b = len(verts)
        verts += v
        faces += [tuple(i + b for i in q) for q in fa]
    smooth_by_angle(G.mesh("Tower_porthole_frame", verts, faces, "frame_black", "House"), 30)
    # deep reveal sleeve behind the black ring is light (catches the sun in frame 04)
    v, fa = ring_mesh(f, sc, zc, PORTHOLE_R_IN, PORTHOLE_R_IN, front - 0.05, -PORTHOLE_DEPTH)
    smooth_by_angle(G.mesh("Tower_porthole_reveal", v, fa, "tower_reveal", "House"), 30)
    # glass disc at the back of the reveal
    seg = 48
    gv = [world(f, sc + PORTHOLE_R_IN * math.cos(2 * math.pi * k / seg), -PORTHOLE_DEPTH,
                zc + PORTHOLE_R_IN * math.sin(2 * math.pi * k / seg)) for k in range(seg)]
    G.mesh("Tower_porthole_glass", gv, [tuple(range(seg))], "tower_porthole_glass", "House")
    # flange: closes the square hole in the backing around the ring (only seen through board gaps)
    fv, ff = [], []
    R = PORTHOLE_R_OUT
    for k in range(seg):
        a = 2 * math.pi * k / seg
        c, s = math.cos(a), math.sin(a)
        m = max(abs(c), abs(s))
        fv.append(world(f, sc + R * c, -0.001, zc + R * s))
        fv.append(world(f, sc + R * c / m, -0.001, zc + R * s / m))
    for k in range(seg):
        a0, b0 = 2 * k, 2 * k + 1
        a1, b1 = 2 * ((k + 1) % seg), 2 * ((k + 1) % seg) + 1
        ff.append((a0, b0, b1, a1))
    G.mesh("Tower_porthole_flange", fv, ff, "tower_backing", "House")


def rect_opening(G, name, f, rect, front, back, fw, pane="glass"):
    """Black frame (proud of the wall) with jambs back to a recessed pane (glass, or a door leaf)."""
    s0, s1, z0, z1 = rect
    verts, faces = [], []

    def quad(p):
        b = len(verts)
        verts.extend(p)
        faces.append((b, b + 1, b + 2, b + 3))

    o0, o1 = s0 - 0.012, s1 + 0.012
    q0, q1 = z0 - 0.012, z1 + 0.012
    i0, i1, j0, j1 = s0 + fw, s1 - fw, z0 + fw, z1 - fw
    W = lambda s, z, o=front: world(f, s, o, z)   # noqa: E731
    # front face of the frame: four bars
    quad([W(o0, q0), W(o1, q0), W(i1, j0), W(i0, j0)])
    quad([W(o1, q0), W(o1, q1), W(i1, j1), W(i1, j0)])
    quad([W(o1, q1), W(o0, q1), W(i0, j1), W(i1, j1)])
    quad([W(o0, q1), W(o0, q0), W(i0, j0), W(i0, j1)])
    # outer sides back to the wall
    quad([W(o0, q0, -0.002), W(o1, q0, -0.002), W(o1, q0), W(o0, q0)])
    quad([W(o1, q0, -0.002), W(o1, q1, -0.002), W(o1, q1), W(o1, q0)])
    quad([W(o1, q1, -0.002), W(o0, q1, -0.002), W(o0, q1), W(o1, q1)])
    quad([W(o0, q1, -0.002), W(o0, q0, -0.002), W(o0, q0), W(o0, q1)])
    # jambs from the frame's inner edge back to the glass
    quad([W(i0, j0), W(i1, j0), W(i1, j0, back), W(i0, j0, back)])
    quad([W(i1, j0), W(i1, j1), W(i1, j1, back), W(i1, j0, back)])
    quad([W(i1, j1), W(i0, j1), W(i0, j1, back), W(i1, j1, back)])
    quad([W(i0, j1), W(i0, j0), W(i0, j0, back), W(i0, j1, back)])
    if pane != "glass":   # black lever handle on a door leaf
        hs, hz = i1 - 0.07, z0 + 1.0
        quad([W(hs - 0.13, hz, back + 0.05), W(hs, hz, back + 0.05),
              W(hs, hz + 0.025, back + 0.05), W(hs - 0.13, hz + 0.025, back + 0.05)])
    G.mesh(name + "_frame", verts, faces, "frame_black", "House")
    G.mesh(name + ("_glass" if pane == "glass" else "_leaf"),
           [W(i0, j0, back), W(i1, j0, back), W(i1, j1, back), W(i0, j1, back)],
           [(0, 1, 2, 3)], pane, "House")
