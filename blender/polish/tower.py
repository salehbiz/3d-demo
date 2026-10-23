"""Charred-wood tower + white stair bulkhead (polish module "tower"; owns Tower*, Bulkhead*).

What the video shows (frames/exterior/...):
- 04 close-up: ~14 cm vertical shou-sugi-ban boards (about 19 across the porthole face) with thin
  dark cathedral grain on a warm grey char, black gaps, only occasional butt joints; a projecting
  bronze-grey band whose top sits ~0.35 m below the tower top, boards continuing above it; the
  porthole is a thick rounded black bead, a thin light reveal and pale sky-mirroring glass.
- 05 / 06 street views: two dark faces meet in a convex corner. The left face (facing south-west,
  ~44 deg) carries the porthole with its top at the hip-roof eave; the right (south) face has a tall
  narrow stair window whose top is a little above the porthole's; a white chimney with a cross-shaped
  crown (a cap band level with the tower band, a narrower flue up to the tower top) stands at the
  south face's east end.
- 14 / 22 aerials: the south face is flush with the roof-deck block and the lower front roofs run in
  front of its base; the porthole is ~0.38 of the SW face's width, centred; the top reads white from
  above (coping + membrane) and the band end projects past the prow corner.
- 15 top-down: tower + bulkhead form one outline - a prow whose SW and NW faces are about equal and
  square to each other, straight bulkhead walls the width of the south face, and a flattened round
  end toward the spa ~55 % of the way back along the deck block.
- 20 rooftop: bulkhead in white stucco, thick rounded coping, grey membrane roof, black-framed door
  on the east wall just before the rounded end.

Placement (house_fronts(), measured at upper-storey height): the prow tip sits on the hip-roof
wing's front wall, the south face on the roof-deck block's front wall, the bulkhead east wall on the
turf edge. The video has the wing's upper storey set back ~1.8 m behind the block; the base model has
both at y 7.0, so until the wing is set back the tower stands PROW_DEPTH in front of the block over
the lower roofs (and the wing's upstairs window runs into the SW face: Tower_wing_window_jamb gives
it a frame there). Owned Tower_flashing seals every wall/roof junction it finds by ray casting,
wherever the roofs end up.

Geometry is built directly (no modifiers): backing shells, individual board meshes with real gaps
(one joined mesh, dark end grain at the butt joints), sweeps for band / caps / coping, and explicit
porthole, window and door assemblies. The cladding texture is generated here (procedural cathedral
growth rings + Poly Haven veneer micro detail) into packed JPEG images, so it renders in Cycles and
exports to glTF as plain image textures.
"""
import math
import os
import random
import tempfile

import numpy as np

POLYHAVEN_ASSETS = ["black_oak_veneer"]   # micro grain blended into the generated cladding maps

# ---------------------------------------------------------------- plan (metres, see docstring)
SOUTH_W = 2.3          # S face = bulkhead width, west from the turf edge (DECK x0): frame 05 ~2.1,
                       # frame 15 ~0.49 of the turf width beside it, frame 22 / 06 SW:S ~1.15-1.3
PROW_DX = 1.9          # prow tip this far west of the SW corner ...
PROW_DEPTH = 1.8       # ... and this far behind the S face: SW face 2.62 m at ~43 deg (04, 14, 15)
REAR_FROM_BLOCK = 6.4  # round-end tip behind the deck block's front wall (frame 15: ~2.7x SOUTH_W)
REAR_DEPTH = 0.85      # flattened half-ellipse round end (frame 15: ~0.74 of the half-width)
ARC_SEG = 24

# ---------------------------------------------------------------- heights
Z_BASE = 3.2           # top of the single-storey front projection the tower stands on
ROOF_Z = 6.2           # main roof / roof-deck level (bulkhead walls start here)
TOP = 9.2              # flat top of tower + bulkhead, 3 m above the deck (frames 05, 06, 14)
PAR_W = 0.22           # parapet / coping width
MEMB_Z = TOP - 0.2     # membrane roof inside the parapet (frame 20)
BAND_Z = (TOP - 0.65, TOP - 0.35)   # bronze band: boards continue above it (frames 04, 14, 22)
BAND_OUT = 0.06        # band projection beyond the board face

# ---------------------------------------------------------------- cladding
BOARD_PITCH = 0.14     # board width incl. gap (frame 04: ~14 cm boards)
BOARD_GAP = 0.008
BOARD_T = 0.022        # board thickness proud of the backing
SEG_MAX = 4.8          # longest board before a butt joint (at most one joint per board) ...
JOINT_SKIP = 0.5       # ... and about half the boards run full height (frame 04)
JOINT_GAP = 0.001
TEX_W, TEX_H = 1024, 512  # generated cladding maps: columns run along the grain, rows across boards
TEX_STRIPS = 8         # the rows hold 8 independent board-width strips
TEX_MARGIN = 2         # texels kept clear at each strip edge
TEX_ALONG = 2.8        # metres of grain along one texture width
CHAR_RGB = (0.036, 0.032, 0.027)   # linear albedo of the brushed char: warm grey (frame 04)

# ---------------------------------------------------------------- openings
PORTHOLE_Z = 5.5       # centre height: top just under the wing's eave (frames 05, 06, 22)
PORTHOLE_R_OUT = 0.53  # bead outer radius: ~1.06 m overall, ~0.4 of the SW face (04, 05, 14, 22)
BEAD_R = 0.05          # rounded black bead, half-torus standing BEAD_R proud (frame 04)
PORTHOLE_R_IN = PORTHOLE_R_OUT - 2 * BEAD_R   # reveal / glass radius
PORTHOLE_R_CUT = PORTHOLE_R_OUT - BEAD_R      # boards stop here (hidden under the bead)
PORTHOLE_DEPTH = 0.06  # glass recess behind the backing plane: only a thin reveal shows (frame 04)
PORTHOLE_S = 0.53      # position along the SW face (0 = prow tip, 1 = south corner)
WINDOW_FRAC = (0.46, 0.68)  # tall stair window across the S face, snapped to board columns (05, 06)
WINDOW_Z = (4.1, 6.25)      # top a little above the porthole top, slot runs down to the roof (05, 06)
DOOR_W, DOOR_GAP = 0.9, 0.35  # bulkhead door on the east wall, just before the round end (frame 20)
DOOR_Z = (ROOF_Z + 0.07, ROOF_Z + 2.4)   # threshold above the turf; ~0.5 m of wall over the head
CHIMNEY_W = 0.32       # white stack at the S face's east end (frames 05, 06, 14, 22) ...
CHIMNEY_FRONT = 0.30   # ... standing this far proud of the S face, 0.5 m deep
CHIMNEY_CAP = (BAND_Z[0] - 0.05, BAND_Z[1] + 0.01, 0.07)  # crown band z0, z1, overhang (in line with the band)
CHIMNEY_FLUE = 0.22    # flue width; its top is level with TOP (frame 14)

# ---------------------------------------------------------------- flashing
FLASH_H = 0.12         # metal upstand where a roof meets a tower / bulkhead wall
FLASH_STEP = 0.08      # sampling step along the wall
ROOF_TARGETS = ("Roof_", "House_front_projection")
RAY_STOP = ("House_", "Deck_", "Spa", "Front_", "Rear_", "Pergola", "BBQ")


def apply(G):
    for prefix in ("Tower", "Bulkhead"):
        G.remove(prefix)
    rnd = random.Random(1159)

    materials(G)
    wing_y, block_y = house_fronts(G)
    east_x = G.DECK["x0"]
    west_x = east_x - SOUTH_W
    front_y = min(block_y, wing_y - PROW_DEPTH)
    rear_y = block_y + REAR_FROM_BLOCK
    V1 = (west_x - PROW_DX, front_y + PROW_DEPTH)          # prow tip
    V2 = (west_x, front_y)
    V3 = (east_x, front_y)
    V4 = (west_x, V1[1] + PROW_DX * PROW_DX / PROW_DEPTH)   # NW face square to the SW face
    cy = max(rear_y - REAR_DEPTH, V4[1] + 0.5)
    cx, ax = (west_x + east_x) / 2, (east_x - west_x) / 2
    arc = [(cx + ax * math.cos(math.pi * i / ARC_SEG), cy + REAR_DEPTH * math.sin(math.pi * i / ARC_SEG))
           for i in range(ARC_SEG + 1)]
    # closed CCW outline; each point carries the tag of the edge that starts there
    ring = [(V2, "S")]
    ring += [(V3, "E"), ((east_x, block_y), "EAST")] if block_y - front_y > 0.05 else [(V3, "EAST")]
    ring += [(p, "ARC") for p in arc[:-1]] + [(arc[-1], "WEST"), (V4, "NW"), (V1, "SW")]
    outline = [p for p, _ in ring]
    n_out = len(outline)
    nw_z0 = Z_BASE if V1[1] < wing_y - 0.05 else ROOF_Z - 0.1   # NW face hidden in the wing below
    faces = []
    for i, (a, tag) in enumerate(ring):
        b = outline[(i + 1) % n_out]
        faces.append(dict(a=a, b=b, L=math.dist(a, b), tag=tag, clad=tag in ("NW", "SW", "S"),
                          z0={"S": Z_BASE, "SW": Z_BASE, "E": Z_BASE, "NW": nw_z0}.get(tag, ROOF_Z)))
    F = {f["tag"]: f for f in faces if f["tag"] != "ARC"}
    for i, f in enumerate(faces):   # outer board faces meet at the convex clad corners
        prv, nxt = faces[i - 1], faces[(i + 1) % n_out]
        f["ext0"] = miter_ext(prv, f) if f["clad"] and prv["clad"] else 0.0
        f["ext1"] = miter_ext(f, nxt) if f["clad"] and nxt["clad"] else 0.0

    S, SW, EAST = F["S"], F["SW"], F["EAST"]
    n_s = round(S["L"] / BOARD_PITCH)
    p_s = S["L"] / n_s
    win = (round(WINDOW_FRAC[0] * n_s) * p_s, round(WINDOW_FRAC[1] * n_s) * p_s, *WINDOW_Z)
    S["holes"] = [win]
    sc = SW["L"] * PORTHOLE_S
    SW["holes"] = [(sc - PORTHOLE_R_OUT, sc + PORTHOLE_R_OUT,
                    PORTHOLE_Z - PORTHOLE_R_OUT, PORTHOLE_Z + PORTHOLE_R_OUT)]
    d1 = EAST["L"] - DOOR_GAP
    door = (d1 - DOOR_W, d1, *DOOR_Z)
    EAST["holes"] = [door]

    # roofs meeting the walls: measured before any of this module's geometry exists
    flash = [(f, roof_line(G, f)) for f in faces if f["tag"] != "ARC"]

    # --- backing / walls: one quad strip per outline edge, with holes for openings
    wall_top = TOP - 0.06
    stucco_v, stucco_f, back_v, back_f = [], [], [], []
    for f in faces:
        tgt = (back_v, back_f) if f["clad"] else (stucco_v, stucco_f)
        wall_grid(tgt, f, f["z0"], TOP - 0.01 if f["clad"] else wall_top, f.get("holes", []))
    walls = G.mesh("Bulkhead_walls", stucco_v, stucco_f, "stucco", "House")
    smooth_by_angle(walls, 35)
    G.mesh("Tower_backing", back_v, back_f, "tower_backing", "House")

    # --- boards (joint / cut end grain on a second, near-black material slot)
    bv, bf, buv, bm = [], [], [], []
    for f in (F["NW"], SW, S):
        circle = (sc, PORTHOLE_Z, PORTHOLE_R_CUT) if f is SW else None
        rect = win if f is S else None
        boards_on_face(bv, bf, buv, bm, f, rnd, circle, rect)
    boards = G.mesh("Tower_boards", bv, bf, "tower_cladding", "House")
    boards.data.materials.append(G.MAT["tower_backing"])
    boards.data.polygons.foreach_set("material_index", bm)
    set_uvs(boards, buv)

    # --- band, white top over the clad faces, rounded coping over the stucco walls, membrane
    i4, i3 = outline.index(V4), outline.index(V3)
    clad_path = [V4, V1, V2, V3]
    b0, b1 = BAND_Z
    bo = BOARD_T + BAND_OUT
    band_prof = [(BOARD_T - 0.004, b0), (bo, b0), (bo, b1 - 0.012), (bo - 0.015, b1), (BOARD_T - 0.004, b1)]
    v, f_ = sweep(clad_path, band_prof, prev=outline[i4 - 1])     # dies into the west wall at V4
    G.mesh("Tower_band", v, f_, "tower_band", "House")
    top_prof = [(BOARD_T + 0.003, TOP - 0.008), (BOARD_T + 0.003, TOP), (-PAR_W, TOP), (-PAR_W, MEMB_Z)]
    v, f_ = sweep(clad_path, top_prof, prev=outline[i4 - 1], nxt=outline[i3 + 1])
    G.mesh("Tower_top", v, f_, "stucco", "House")
    r = 0.07
    cop_prof = [(0.0, wall_top), (0.022, wall_top), (0.022, TOP - 0.035)]
    cop_prof += [(0.022 - r + r * math.cos(a), TOP - r + r * math.sin(a))
                 for a in (math.radians(d) for d in (30, 60, 90))]
    cop_prof += [(-PAR_W + r - r * math.cos(math.radians(d)), TOP - r + r * math.sin(math.radians(d)))
                 for d in (90, 60, 30)]
    cop_prof += [(-PAR_W, TOP - 0.05), (-PAR_W, MEMB_Z)]
    v, f_ = sweep(outline[i3:i4 + 1], cop_prof, prev=V2, nxt=V1)
    coping = G.mesh("Bulkhead_coping", v, f_, "stucco", "House")
    smooth_by_angle(coping, 35)
    miters = miter_vectors(outline, True)
    memb = [(x + mx * -PAR_W, y + my * -PAR_W, MEMB_Z) for (x, y), (mx, my) in zip(outline, miters)]
    G.mesh("Bulkhead_roof", memb, [tuple(range(len(memb)))], "bulkhead_membrane", "House")

    # --- porthole: rounded black bead, light reveal, recessed pale glass
    porthole(G, SW, sc)
    # --- tall stair window on the south face (warm interior read through the glass)
    rect_opening(G, "Tower_window", S, win, BOARD_T + 0.03, -0.08, 0.05, pane="tower_window_glass")
    # --- bulkhead door (east wall)
    rect_opening(G, "Bulkhead_door", EAST, door, 0.03, -0.06, 0.05, pane="bulkhead_door_leaf", handle=True)
    # --- metal flashing along every roof / wall junction
    flashing(G, flash)
    # --- black jamb where a wing window runs into the SW face (until the wing is set back)
    window_jambs(G, SW)

    # --- chimney: shaft, crown band in line with the tower band, flue up to TOP (frames 05, 06, 14)
    x0, x1 = east_x, east_x + CHIMNEY_W
    y0, y1 = front_y - CHIMNEY_FRONT, front_y + 0.2
    c0, c1, co = CHIMNEY_CAP
    G.box("Tower_chimney", x0, y0, Z_BASE, x1, y1, c0, "stucco", "House")
    G.box("Tower_chimney_cap", x0 - co, y0 - co, c0, x1 + co, y1, c1, "stucco", "House")
    fx = (x0 + x1 - CHIMNEY_FLUE) / 2
    G.box("Tower_chimney_flue", fx, y0 + 0.04, c1, fx + CHIMNEY_FLUE, y0 + 0.36, TOP, "stucco", "House")

    # review cameras for this area (frame each one is matched to in the comment)
    pc = world(SW, sc, BOARD_T, 0.0)
    dn, nn = frame_of(SW)
    at = lambda out, along, z: (pc[0] + nn[0] * out + dn[0] * along,   # noqa: E731
                                pc[1] + nn[1] * out + dn[1] * along, z)
    mid_y = (front_y + rear_y) / 2
    door_y = EAST["a"][1] + d1 - DOOR_W / 2
    G.SHOTS.update({
        "tower_close": (at(2.4, 0.7, 4.3), at(0.0, -0.5, 7.0), 20),       # exterior/04
        "porthole_detail": (at(2.8, 0.1, 5.1), at(0.0, 0.0, 5.6), 50),   # exterior/04 (porthole crop)
        "tower_street": ((6.2, -15.5, 1.7), (7.2, front_y + 1.0, 6.9), 70),   # exterior/06 (crop)
        "tower_sw": (at(18.0, 10.0, 13.0), at(0.0, 0.3, 6.6), 60),       # exterior/22 (from SSW; Palm_0 blocks the face-on view)
        "bulkhead_roof": ((10.6, front_y + 1.6, 10.2), (9.6, rear_y + 2.0, 7.0), 20),   # exterior/20
        "tower_top": ((7.8, mid_y, 32.0), (7.8, mid_y, 0.0), 45),         # exterior/15 (rotated crop)
        "tower_rear": ((1.0, 24.0, 15.0), (7.0, 10.0, 7.5), 40),          # junction check (no frame)
        "tower_base": (at(4.5, 2.5, 7.5), at(0.0, 1.6, 4.2), 28),         # roof flashing check (no frame)
        "bulkhead_door": ((12.5, door_y - 2.3, 8.0), (east_x, door_y, 7.3), 30),   # exterior/20 (door)
    })


def house_fronts(G):
    """Upper-storey front wall planes (min y above the front projection) of the hip-roof wing and of
    the roof-deck block, so a wing whose upper storey is set back is measured at that storey."""
    def front(prefix):
        return min(((o.matrix_world @ v.co).y for o in G.bpy.data.objects
                    if o.name.startswith(prefix) and o.type == "MESH"
                    for v in o.data.vertices if (o.matrix_world @ v.co).z > Z_BASE + 0.5),
                   default=G.HOUSE["y0"])
    return front("House_left_wing"), front("House_right_block")


# ======================================================================= materials
def materials(G):
    bpy = G.bpy
    G.mat("tower_backing", (0.006, 0.006, 0.006), 0.95)       # also the boards' end grain / gaps
    G.mat("tower_band", (0.06, 0.051, 0.043), 0.62, 0.15)      # weathered bronze-grey band (frame 04)
    G.mat("bulkhead_membrane", (0.56, 0.56, 0.54), 0.8)        # light grey TPO roof (frame 20)
    G.mat("tower_porthole_glass", (0.60, 0.61, 0.62), 0.06, 0.5)    # pale, mirrors sky (04, 05, 22)
    G.mat("tower_reveal", (0.50, 0.48, 0.44), 0.6)             # painted porthole sleeve (frame 04)
    G.mat("tower_window_glass", (0.16, 0.14, 0.11), 0.04,       # glass over a lit, warm-white stair
          emit=((1.0, 0.8, 0.55), 0.11))                        # (frame 05 day sliver, 06 dusk glow)
    G.mat("bulkhead_door_leaf", (0.8, 0.8, 0.78), 0.45)        # white painted door (frame 20)
    for name, spec in (("tower_porthole_glass", 0.8), ("tower_window_glass", 0.9)):
        G.MAT[name].node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = spec
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
    nm.inputs["Strength"].default_value = 0.35     # grain reads as tone, not embossed relief
    ln.new(nn.outputs["Color"], nm.inputs["Color"])
    ln.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.7           # matte brushed char, faint sheen
    bsdf.inputs["Specular IOR Level"].default_value = 0.38
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
    form the long cathedral arches seen in frame 04; latewood lines are thin and dark.
    """
    sh = TEX_H // TEX_STRIPS
    board_m = BOARD_PITCH * sh / (sh - 2 * TEX_MARGIN)
    s = (np.arange(sh) / sh - 0.5) * board_m
    out = np.zeros((TEX_H, TEX_W), np.float32)
    for k in range(TEX_STRIPS):
        r2 = np.random.default_rng(seed * 100 + k)
        sp = r2.uniform(0.012, 0.022)                              # ring spacing
        s0 = r2.uniform(-0.07, 0.07) + 0.025 * value_noise((1, TEX_W), (1, 3), r2)[0]
        d = 0.02 + r2.uniform(0.0, 0.05) + 0.06 * np.abs(value_noise((1, TEX_W), (1, 4), r2)[0])
        warp = 0.003 * value_noise((sh, TEX_W), (2, 14), r2) + 0.0008 * value_noise((sh, TEX_W), (6, 90), r2)
        r = np.sqrt(d[None, :] ** 2 + (s[:, None] - s0[None, :]) ** 2) + warp
        f = (r / sp) % 1.0
        width = np.clip(0.09 + 0.03 * value_noise((sh, TEX_W), (2, 12), r2), 0.04, None)
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
    shade = (1 + 0.12 * blot) * (1 - 0.7 * rings) * (1 + 0.10 * detail)
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


def miter_ext(f0, f1):
    """Extra length the outer board face needs to meet the neighbouring clad face at a convex corner."""
    d0, _ = frame_of(f0)
    d1, _ = frame_of(f1)
    cross = d0[0] * d1[1] - d0[1] * d1[0]
    if cross <= 0:     # only a left turn on a CCW outline is a convex corner
        return 0.0
    turn = math.atan2(cross, d0[0] * d1[0] + d0[1] * d1[1])
    return BOARD_T * math.tan(turn / 2)


def boards_on_face(verts, faces, uvs, mats, f, rnd, circle=None, rect=None):
    """Vertical boards, about half with one butt joint; circle (sc, zc, r) / rect (s0, s1, z0, z1)
    are cut out."""
    L = f["L"]
    n = max(1, round(L / BOARD_PITCH))
    p = L / n
    z_lo = f["z0"] + 0.02
    z_hi = TOP - 0.006            # up under the white top's lip; the band sits over the boards
    holes_z = []
    if circle:
        holes_z.append((circle[1] - circle[2] - 0.15, circle[1] + circle[2] + 0.15))
    if rect:
        holes_z.append((rect[2] - 0.15, rect[3] + 0.15))
    holes_z.append((BAND_Z[0] - 0.1, BAND_Z[1] + 0.1))   # a joint under the band would be wasted
    for c in range(n):
        s0 = c * p + (0 if c == 0 else BOARD_GAP / 2)
        s1 = (c + 1) * p - (0 if c == n - 1 else BOARD_GAP / 2)
        e0 = f.get("ext0", 0.0) if c == 0 else 0.0
        e1 = f.get("ext1", 0.0) if c == n - 1 else 0.0
        H = z_hi - z_lo
        nseg = 1 if rnd.random() < JOINT_SKIP else max(1, math.ceil(H / SEG_MAX))
        cuts = []
        for k in range(1, nseg):
            zc = z_lo + H * k / nseg + rnd.uniform(-0.45, 0.45) * (H / nseg - 0.6)
            for lo, hi in holes_z:
                if lo < zc < hi:
                    zc = lo if zc - lo < hi - zc else hi
            cuts.append(zc)
        zs = [z_lo] + sorted(cuts) + [z_hi]
        for k in range(len(zs) - 1):
            za = zs[k] + (JOINT_GAP if k else 0)
            zb = zs[k + 1] - (JOINT_GAP if k < len(zs) - 2 else 0)
            if zb - za < 0.05:
                continue
            pieces = cut_piece(s0, s1, za, zb, circle, rect)
            seg_len = zb - za
            u0 = rnd.uniform(0.01, max(0.011, 0.99 - seg_len / TEX_ALONG))
            strip = rnd.randrange(TEX_STRIPS)
            depth = BOARD_T + rnd.uniform(-0.0015, 0.0015)
            for ss, bot, top in pieces:
                board_piece(verts, faces, uvs, mats, f, ss, bot, top, depth, e0, e1, s0, s1, za, u0, strip)


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


def board_piece(verts, faces, uvs, mats, f, ss, bot, top, depth, e0, e1, bs0, bs1, za, u0, strip):
    """Board strip with front, end and side faces (back face omitted: it sits on the backing).
    End faces (joints, cuts) get material slot 1 so joints read as dark hairlines."""
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

    def quad(pts, uvq, m=0):
        b = len(verts)
        verts.extend(pts)
        faces.append((b, b + 1, b + 2, b + 3))
        uvs.extend(uvq)
        mats.append(m)

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
              uv(ss[k + 1], bot[k + 1]), uv(ss[k], bot[k])], 1)
        # top end
        quad([world(f, so[k], depth, top[k]), world(f, so[k + 1], depth, top[k + 1]),
              world(f, ss[k + 1], 0, top[k + 1]), world(f, ss[k], 0, top[k])],
             [uv(ss[k], top[k]), uv(ss[k + 1], top[k + 1]),
              uv(ss[k + 1], top[k + 1] + depth), uv(ss[k], top[k] + depth)], 1)
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


def sweep(path, profile, closed=False, prev=None, nxt=None):
    """Sweep a 2D (outward offset, z) profile along a path with mitred corners. For an open path,
    prev / nxt are the outline's neighbouring points, so the end cuts are mitred against them."""
    ext = ([prev] if prev else []) + list(path) + ([nxt] if nxt else [])
    mit = miter_vectors(ext, closed)
    mit = mit[1 if prev else 0:len(mit) - (1 if nxt else 0)]
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


def revolve(f, sc, zc, profile, seg=48):
    """Surface of revolution about the axis through (sc, zc) normal to face f; profile = [(r, out)]."""
    verts, faces = [], []
    P = len(profile)
    for k in range(seg):
        a = 2 * math.pi * k / seg
        c, s = math.cos(a), math.sin(a)
        verts += [world(f, sc + r * c, out, zc + r * s) for r, out in profile]
    for k in range(seg):
        k2 = (k + 1) % seg
        for j in range(P - 1):
            faces.append((k * P + j, k2 * P + j, k2 * P + j + 1, k * P + j + 1))
    return verts, faces


def porthole(G, f, sc):
    zc = PORTHOLE_Z
    rc = PORTHOLE_R_OUT - BEAD_R
    # half-torus bead on the board face, plus a skirt back to the backing behind its outer edge
    prof = [(rc + BEAD_R * math.cos(t), BOARD_T + BEAD_R * math.sin(t))
            for t in (math.pi * (1 - i / 8) for i in range(9))]
    prof += [(PORTHOLE_R_OUT, -0.002)]
    v, fa = revolve(f, sc, zc, prof)
    smooth_by_angle(G.mesh("Tower_porthole_frame", v, fa, "frame_black", "House"), 50)
    # light reveal sleeve from the bead's inner edge back to the glass
    v, fa = revolve(f, sc, zc, [(PORTHOLE_R_IN, BOARD_T), (PORTHOLE_R_IN, -PORTHOLE_DEPTH)])
    smooth_by_angle(G.mesh("Tower_porthole_reveal", v, fa, "tower_reveal", "House"), 30)
    seg = 48
    gv = [world(f, sc + PORTHOLE_R_IN * math.cos(2 * math.pi * k / seg), -PORTHOLE_DEPTH,
                zc + PORTHOLE_R_IN * math.sin(2 * math.pi * k / seg)) for k in range(seg)]
    G.mesh("Tower_porthole_glass", gv, [tuple(range(seg))], "tower_porthole_glass", "House")
    # flange: closes the square hole in the backing around the bead (only seen through board gaps)
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


def rect_opening(G, name, f, rect, front, back, fw, pane="glass", handle=False):
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
    # jambs from the frame's inner edge back to the pane
    quad([W(i0, j0), W(i1, j0), W(i1, j0, back), W(i0, j0, back)])
    quad([W(i1, j0), W(i1, j1), W(i1, j1, back), W(i1, j0, back)])
    quad([W(i1, j1), W(i0, j1), W(i0, j1, back), W(i1, j1, back)])
    quad([W(i0, j1), W(i0, j0), W(i0, j0, back), W(i0, j1, back)])
    if handle:   # black lever handle on a door leaf
        hs, hz = i1 - 0.07, z0 + 1.0
        quad([W(hs - 0.13, hz, back + 0.05), W(hs, hz, back + 0.05),
              W(hs, hz + 0.025, back + 0.05), W(hs - 0.13, hz + 0.025, back + 0.05)])
    G.mesh(name + "_frame", verts, faces, "frame_black", "House")
    G.mesh(name + ("_leaf" if handle else "_glass"),
           [W(i0, j0, back), W(i1, j0, back), W(i1, j1, back), W(i0, j1, back)],
           [(0, 1, 2, 3)], pane, "House")


# ======================================================================= roof flashing
def roof_line(G, f):
    """Height of the roof surface just outside wall face f, sampled along it ([(s, z | None)]).
    Only metal roofs / the flat front-projection roof count; vegetation etc. is looked through."""
    bpy, V = G.bpy, G.Vector
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    base = BOARD_T if f["clad"] else 0.0
    s_a, s_b = -f.get("ext0", 0.0), f["L"] + f.get("ext1", 0.0)
    n = max(2, round((s_b - s_a) / FLASH_STEP))
    out = []
    for k in range(n + 1):
        s = s_a + (s_b - s_a) * k / n
        x, y, _ = world(f, min(max(s, 0.01), f["L"] - 0.01), base + 0.04, 0.0)
        origin, h = V((x, y, TOP - 0.4)), None
        for _ in range(8):
            hit, loc, _nrm, _i, obj, _m = scene.ray_cast(dg, origin, V((0.0, 0.0, -1.0)), distance=TOP)
            if not hit:
                break
            if obj.name.startswith(ROOF_TARGETS):
                h = loc.z
                break
            if obj.name.startswith(RAY_STOP):
                break
            origin = loc + V((0.0, 0.0, -0.002))
        out.append((s, h if h is not None and h > f["z0"] - 0.05 else None))
    return out


def flashing(G, lines):
    """Dark metal upstand along each roof/wall junction: runs of samples, split where the roof
    height jumps (an eave edge) so no strip bridges two roofs."""
    verts, faces = [], []
    for f, samples in lines:
        base = BOARD_T if f["clad"] else 0.0
        prof = [(base + 0.006, -0.03), (base + 0.006, FLASH_H), (base - 0.004, FLASH_H + 0.01)]
        runs, cur = [], []
        for s, h in samples:
            if h is None or (cur and abs(h - cur[-1][1]) > 0.2):
                if len(cur) > 1:
                    runs.append(cur)
                cur = [] if h is None else [(s, h)]
            else:
                cur.append((s, h))
        if len(cur) > 1:
            runs.append(cur)
        for run in runs:
            b = len(verts)
            verts += [world(f, s, o, h + dz) for s, h in run for o, dz in prof]
            P = len(prof)
            for i in range(len(run) - 1):
                for j in range(P - 1):
                    faces.append((b + i * P + j, b + (i + 1) * P + j, b + (i + 1) * P + j + 1, b + i * P + j + 1))
    if faces:
        G.mesh("Tower_flashing", verts, faces, "roof_metal", "House")


def window_jambs(G, f):
    """Facade windows (glass on another owner's wall) that run into the SW face get a black jamb on
    the board face where the glass disappears, so the glass ends in a frame, not in the boards."""
    d, n = frame_of(f)
    verts, faces = [], []
    for o in G.bpy.data.objects:
        if o.type != "MESH" or o.name.startswith(("Tower", "Bulkhead")) or not o.data.materials \
                or o.data.materials[0].name != "glass":
            continue
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
        y0, y1 = min(p.y for p in pts), max(p.y for p in pts)
        z0, z1 = min(p.z for p in pts), max(p.z for p in pts)
        if y1 - y0 > 0.2 or z1 < f["z0"] or z0 > TOP:
            continue
        # where the glass's front plane (y0) crosses the board face: (p - a).n = BOARD_T
        if abs(n[0]) < 1e-6:
            continue
        x = f["a"][0] + (BOARD_T - (y0 - f["a"][1]) * n[1]) / n[0]
        s = (x - f["a"][0]) * d[0] + (y0 - f["a"][1]) * d[1]
        if not (x0 < x < x1 and -0.05 < s < f["L"]):
            continue
        b = len(verts)
        for ss in (s - 0.035, s + 0.035):
            for o_ in (0.0, BOARD_T + 0.03):
                verts += [world(f, ss, o_, z0 - 0.06), world(f, ss, o_, z1 + 0.06)]
        # vertex order: (s-, in, bot/top), (s-, out, bot/top), (s+, in, ..), (s+, out, ..)
        faces += [(b + 2, b + 6, b + 7, b + 3), (b + 0, b + 2, b + 3, b + 1), (b + 6, b + 4, b + 5, b + 7),
                  (b + 1, b + 3, b + 7, b + 5), (b + 0, b + 4, b + 6, b + 2)]
    if faces:
        G.mesh("Tower_wing_window_jamb", verts, faces, "frame_black", "House")
