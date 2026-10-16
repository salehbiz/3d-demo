"""Exterior massing model of 1159 Diamond St, built from video reference.

Run:  blender -b -P blender/build_exterior.py -- [--render]
Outputs: assets/house_exterior.blend, assets/house_exterior.glb,
         renders/*.png (with --render) from cameras matched to video frames.

Coordinates (metres): x = east (right when facing the house from the street),
y = toward the alley (street at y=0), z = up.  Lot 15.3 x 38.4 m
(6,300 sq ft public record).  Every dimension lives in the tables below so the
model can be corrected by editing numbers, not code.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = "--render" in sys.argv

LOT = dict(w=15.3, d=38.4)

# Main house: left wing (hip roof) + right block (flat, roof deck) + tower.
HOUSE = dict(x0=2.4, x1=13.9, y0=7.0, y1=19.0, floor1=3.2, roof=6.2)   # upper-floor box
GROUND_FRONT_Y = 4.0        # single-storey front projection starts here
LEFT_WING_X1 = 6.4          # upper-floor hip-roof wing spans x0..this
TOWER = dict(x0=6.4, x1=9.4, y0=7.0, y1=10.5, top=9.2)
BULKHEAD = dict(x0=7.0, x1=9.0, y0=10.5, y1=16.0, top=8.6)  # rounded end toward pool
HIP = dict(eave=6.2, ridge=7.4, overhang=0.5)
FRONT_ROOFS = [dict(x0=2.0, x1=7.6), dict(x0=8.4, x1=14.3)]  # hip roofs over front projection
FRONT_ROOF_Z = dict(eave=3.3, rise=0.85)
DECK = dict(x0=9.0, x1=13.9, parapet=1.0)
REAR_BALCONY = dict(x0=7.0, x1=13.9, depth=1.4, z=3.2)

POOL = dict(cx=7.6, cy=25.0)            # kidney built from two lobes
PAVILION = dict(x0=0.6, x1=14.7, y0=31.0, y1=37.8, h=3.3)
FRONT_FENCE_Y = 0.4

MAT = {}


def mat(name, color, rough=0.6, metal=0.0, emit=None, alpha=1.0, transmission=0.0):
    if name in MAT:
        return MAT[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1)
        b.inputs["Emission Strength"].default_value = emit[1]
    MAT[name] = m
    return m


def materials():
    mat("stucco", (0.92, 0.91, 0.88), 0.85)
    mat("roof_metal", (0.05, 0.055, 0.06), 0.45, 0.6)
    mat("charred_wood", (0.04, 0.035, 0.03), 0.8)
    mat("glass", (0.05, 0.07, 0.08), 0.05, 0.0)
    mat("frame_black", (0.02, 0.02, 0.02), 0.4, 0.3)
    mat("turf", (0.12, 0.35, 0.08), 0.9)
    mat("lawn_ground", (0.18, 0.32, 0.12), 0.95)
    mat("paving", (0.78, 0.74, 0.66), 0.8)
    mat("timber", (0.45, 0.28, 0.15), 0.6)
    mat("water", (0.02, 0.22, 0.42), 0.03, emit=((0.02, 0.25, 0.5), 0.15))
    mat("pool_shelf", (0.55, 0.80, 0.80), 0.3, emit=((0.4, 0.75, 0.8), 0.15))
    mat("asphalt", (0.18, 0.18, 0.19), 0.9)
    mat("concrete", (0.6, 0.6, 0.58), 0.85)
    mat("pergola_red", (0.45, 0.12, 0.1), 0.6)
    mat("macrame", (0.95, 0.93, 0.88), 0.95)
    mat("palm_trunk", (0.35, 0.28, 0.2), 0.9)
    mat("palm_leaf", (0.12, 0.30, 0.06), 0.6)
    mat("neighbour", (0.72, 0.72, 0.70), 0.9)
    mat("shrub", (0.08, 0.22, 0.05), 0.9)
    mat("wall_light", (1.0, 0.85, 0.6), 0.5, emit=((1.0, 0.8, 0.55), 6.0))
    mat("stone", (0.85, 0.83, 0.78), 0.8)
    detail("neighbour", "noise", (0.78, 0.75, 0.70), (0.70, 0.68, 0.64), scale=20, bump=0.03)
    # Poly Haven CC0 textures (blender/fetch_textures.py): material -> (asset, tile metres, tint)
    pbr("stucco", "white_plaster_rough_01", 2.0, (0.88, 0.88, 0.86), 0.25)
    pbr("roof_metal", "box_profile_metal_sheet", 1.5, (0.035, 0.037, 0.04), 0.3)
    pbr("charred_wood", "black_painted_planks", 1.2, (0.03, 0.03, 0.032), 0.5)
    pbr("timber", "wood_floor_deck", 2.0, (0.42, 0.34, 0.27), 0.6)
    pbr("turf", "leafy_grass", 1.5, (0.10, 0.32, 0.05), 0.45)
    pbr("lawn_ground", "leafy_grass", 2.0, (0.14, 0.28, 0.08), 0.5)
    pbr("paving", "precast_stone_paving", 2.0, (0.80, 0.76, 0.68), 0.5)
    pbr("stone", "stone_pathway", 2.0, (0.85, 0.83, 0.78), 0.6)
    pbr("pool_shelf", "pebble_cemented_floor", 1.0, (0.45, 0.72, 0.72), 0.5)
    pbr("asphalt", "asphalt_02", 3.0)
    pbr("concrete", "concrete_floor_02", 2.0)
    detail("water", "ripple", (0.02, 0.20, 0.40), (0.05, 0.35, 0.58), scale=3, bump=0.15)
    detail("shrub", "noise", (0.05, 0.18, 0.04), (0.14, 0.32, 0.08), scale=8, bump=0.8)
    g = MAT["glass"].node_tree.nodes["Principled BSDF"]
    g.inputs["Roughness"].default_value = 0.02
    g.inputs["Specular IOR Level"].default_value = 1.0


TEX_DIR = os.path.join(ROOT, "assets", "textures")
TILE = {}


def pbr(name, asset, tile, tint=(1, 1, 1), strength=1.0):
    """Replace a material's colour/roughness/normal with image textures; UVs come from uv_all()."""
    nt = MAT[name].node_tree
    n, l = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    for inp in ("Base Color", "Roughness", "Normal"):
        for link in list(bsdf.inputs[inp].links):
            l.remove(link)

    def img(short, colour):
        t = n.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEX_DIR, asset, f"{short}.jpg"), check_existing=True)
        t.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        return t
    diff = img("diff", True)
    # strength 1: texture colour x tint; <1: mostly flat tint with texture variation blended in
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY" if strength >= 1 else "OVERLAY"
    mix.inputs["Factor"].default_value = 1.0 if strength >= 1 else strength
    mix.inputs["A" if strength < 1 else "B"].default_value = (*tint, 1)
    l.new(diff.outputs["Color"], mix.inputs["B" if strength < 1 else "A"])
    l.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    l.new(img("rough", False).outputs["Color"], bsdf.inputs["Roughness"])
    nm = n.new("ShaderNodeNormalMap")
    l.new(img("nor", False).outputs["Color"], nm.inputs["Color"])
    l.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    TILE[name] = tile


def uv_all():
    """Box-project UVs on every textured mesh so textures tile at real-world scale."""
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.data.materials or o.data.materials[0].name not in TILE:
            continue
        tile = TILE[o.data.materials[0].name]
        me = o.data
        if not me.uv_layers:
            me.uv_layers.new()
        uv = me.uv_layers.active.data
        for poly in me.polygons:
            nx, ny, nz = (abs(c) for c in poly.normal)
            for li in poly.loop_indices:
                co = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
                if nz >= nx and nz >= ny:
                    u, v = co.x, co.y
                elif nx >= ny:
                    u, v = co.y, co.z
                else:
                    u, v = co.x, co.z
                uv[li].uv = (u / tile, v / tile)


def detail(name, kind, c1, c2, scale=1.0, bump=0.1):
    """Add a procedural pattern (colour variation + bump) to an existing material."""
    nt = MAT[name].node_tree
    n, l = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    coord = n.new("ShaderNodeTexCoord")
    if kind in ("noise", "ripple"):
        tex = n.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 6 if kind == "noise" else 2
        l.new(coord.outputs["Object"], tex.inputs["Vector"])
        fac = tex.outputs["Fac"]
    elif kind == "voronoi":
        tex = n.new("ShaderNodeTexVoronoi")
        tex.feature = "DISTANCE_TO_EDGE"
        tex.inputs["Scale"].default_value = scale
        l.new(coord.outputs["Object"], tex.inputs["Vector"])
        ramp = n.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].position = 0.04
        l.new(tex.outputs["Distance"], ramp.inputs["Fac"])
        fac = ramp.outputs["Color"]
        c1, c2 = c2, c1
    else:  # seams_x / boards_x / boards_y: periodic bands
        sep = n.new("ShaderNodeSeparateXYZ")
        l.new(coord.outputs["Object"], sep.inputs["Vector"])
        axis = "Y" if kind.endswith("_y") else "X"
        div = n.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = scale
        l.new(sep.outputs[axis], div.inputs[0])
        frac = n.new("ShaderNodeMath"); frac.operation = "FRACT"
        l.new(div.outputs[0], frac.inputs[0])
        edge = n.new("ShaderNodeMath"); edge.operation = "GREATER_THAN"
        edge.inputs[1].default_value = 0.9 if kind == "seams_x" else 0.94
        l.new(frac.outputs[0], edge.inputs[0])
        noise = n.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 3
        l.new(coord.outputs["Object"], noise.inputs["Vector"])
        mx = n.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
        l.new(edge.outputs[0], mx.inputs[0])
        mul = n.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.5
        l.new(noise.outputs["Fac"], mul.inputs[0])
        l.new(mul.outputs[0], mx.inputs[1])
        fac = mx.outputs[0]
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*c1, 1)
    mix.inputs["B"].default_value = (*c2, 1)
    l.new(fac, mix.inputs["Factor"])
    l.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bm = n.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value = bump
    bm.inputs["Distance"].default_value = 0.02
    l.new(fac, bm.inputs["Height"])
    l.new(bm.outputs["Normal"], bsdf.inputs["Normal"])


def box(name, x0, y0, z0, x1, y1, z1, material, collection=None):
    bpy.ops.mesh.primitive_cube_add(location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.object
    o.name = name
    o.scale = ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(MAT[material])
    link(o, collection)
    return o


def mesh(name, verts, faces, material, collection=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(MAT[material])
    link(o, collection)
    return o


def cyl(name, x, y, z0, z1, r, material, verts=32, collection=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=z1 - z0,
                                        location=(x, y, (z0 + z1) / 2))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(MAT[material])
    link(o, collection)
    return o


def link(o, collection):
    if not collection:
        return
    col = bpy.data.collections.get(collection)
    if col is None:
        col = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(col)
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)


def hip_roof(name, x0, y0, x1, y1, z, rise, material, collection):
    """Hip roof over rectangle; ridge runs along the longer side."""
    if (x1 - x0) >= (y1 - y0):
        inset = (y1 - y0) / 2
        ridge = [(x0 + inset, (y0 + y1) / 2, z + rise), (x1 - inset, (y0 + y1) / 2, z + rise)]
    else:
        inset = (x1 - x0) / 2
        ridge = [((x0 + x1) / 2, y0 + inset, z + rise), ((x0 + x1) / 2, y1 - inset, z + rise)]
    v = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), *ridge]
    if (x1 - x0) >= (y1 - y0):
        f = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)]
    else:
        f = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5)]
    o = mesh(name, v, f, material, collection)
    sol = o.modifiers.new("thickness", "SOLIDIFY")
    sol.thickness = 0.12
    return o


def window(name, wall, a0, a1, z0, z1, collection="Openings", depth=0.06):
    """Dark glazed panel with black frame on a facade.

    wall: ('y', value, outward_sign) for front/rear faces, ('x', value, sign) for sides.
    """
    axis, val, sign = wall
    t = depth
    if axis == "y":
        g = box(name, a0, val + sign * 0.01, z0, a1, val + sign * (0.01 + t), z1, "glass", collection)
        box(name + "_frame", a0 - 0.06, val, z0 - 0.06, a1 + 0.06, val + sign * 0.03, z1 + 0.06,
            "frame_black", collection)
    else:
        g = box(name, val + sign * 0.01, a0, z0, val + sign * (0.01 + t), a1, z1, "glass", collection)
        box(name + "_frame", val, a0 - 0.06, z0 - 0.06, val + sign * 0.03, a1 + 0.06, z1 + 0.06,
            "frame_black", collection)
    return g


def railing(name, pts, z, h=1.05, collection="House"):
    """Horizontal-bar black railing along a polyline."""
    for i in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        for k, dz in enumerate((h, h * 0.66, h * 0.33)):
            box(f"{name}_{i}_{k}", min(xa, xb) - 0.02, min(ya, yb) - 0.02, z + dz - 0.03,
                max(xa, xb) + 0.02, max(ya, yb) + 0.02, z + dz, "frame_black", collection)
        n = max(1, int(math.hypot(xb - xa, yb - ya) / 1.5))
        for j in range(n + 1):
            px, py = xa + (xb - xa) * j / n, ya + (yb - ya) * j / n
            box(f"{name}_{i}_post{j}", px - 0.025, py - 0.025, z, px + 0.025, py + 0.025, z + h,
                "frame_black", collection)


def palm(name, x, y, h=8.0, lean=(0.0, 0.0), seed=0):
    """Procedural palm: tapered trunk + arched fronds made of individual leaflets."""
    import random
    rnd = random.Random(seed)
    tx, ty = x + lean[0], y + lean[1]
    verts, faces = [], []
    # trunk: tapered tube from (x, y, 0) to (tx, ty, h)
    seg, ring = 14, 10
    for k in range(seg + 1):
        t = k / seg
        cx, cy, cz = x + (tx - x) * t * t, y + (ty - y) * t * t, h * t
        r = 0.24 - 0.09 * t
        for j in range(ring):
            a = 2 * math.pi * j / ring
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), cz))
    for k in range(seg):
        for j in range(ring):
            a0, a1 = k * ring + j, k * ring + (j + 1) % ring
            faces.append((a0, a1, a1 + ring, a0 + ring))
    trunk = mesh(name + "_trunk", verts, faces, "palm_trunk", "Landscape")
    # fronds
    verts, faces = [], []
    n = 26
    for f in range(n):
        az = 2 * math.pi * f / n + rnd.uniform(-0.15, 0.15)
        elev = math.radians(rnd.uniform(-15, 45))
        L = rnd.uniform(2.6, 3.4)
        dx, dy = math.cos(az), math.sin(az)
        px, py = -dy, dx
        steps = 18
        for k in range(1, steps + 1):
            t = k / steps
            d = L * t
            sx, sy = tx + dx * d, ty + dy * d
            sz = h + math.sin(elev) * d - 0.55 * L * t * t
            ll = 0.75 * (1 - 0.6 * t) * (0.4 if k < 3 else 1.0)
            for side in (-1, 1):
                ex = sx + px * side * ll + dx * 0.15
                ey = sy + py * side * ll + dy * 0.15
                ez = sz - 0.25 * ll
                b = len(verts)
                w = L / steps * 0.9
                verts += [(sx - dx * w, sy - dy * w, sz), (sx + dx * w * 0.3, sy + dy * w * 0.3, sz),
                          (ex, ey, ez), (ex - dx * w * 0.6, ey - dy * w * 0.6, ez - 0.05)]
                faces.append((b, b + 1, b + 2, b + 3))
    crown = mesh(name + "_fronds", verts, faces, "palm_leaf", "Landscape")
    return trunk, crown


LIB = {}


def load_model(name):
    """Import a Poly Haven glTF once; return its mesh objects (kept hidden as a library)."""
    if name in LIB:
        return LIB[name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "assets", "models", name, f"{name}.gltf"))
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in objs:
        link(o, "Library")
        o.matrix_world = o.matrix_world.copy()
        o.parent = None
    bpy.data.collections["Library"].hide_render = True
    bpy.data.collections["Library"].hide_viewport = True
    LIB[name] = objs
    return objs


def place(name, x, y, z=0.0, rot=0.0, scale=1.0, collection="Landscape"):
    """Linked-duplicate a library model at a position."""
    out = []
    for src in load_model(name):
        o = src.copy()
        o.location = (x + src.location.x * scale, y + src.location.y * scale, z + src.location.z * scale)
        o.rotation_euler = (src.rotation_euler.x, src.rotation_euler.y, src.rotation_euler.z + rot)
        o.scale = tuple(c * scale for c in src.scale)
        bpy.context.scene.collection.objects.link(o)
        link(o, collection)
        out.append(o)
    return out


def build_site():
    box("Street", -10, -12, -0.05, LOT["w"] + 10, -2.5, 0, "asphalt", "Site")
    box("Sidewalk", -10, -2.5, -0.05, LOT["w"] + 10, 0, 0.02, "concrete", "Site")
    box("Alley", -10, LOT["d"], -0.05, LOT["w"] + 10, LOT["d"] + 6, 0, "asphalt", "Site")
    box("Ground_far", -60, -60, -0.08, 75, 100, -0.06, "lawn_ground", "Site")
    box("Lot_ground", 0, 0, -0.05, LOT["w"], LOT["d"], 0, "lawn_ground", "Site")
    # neighbours (simple white/beige blocks for context)
    for i, (y0, y1, h) in enumerate([(4, 20, 6.5), (24, 34, 3.5)]):
        box(f"Neighbour_W{i}", -12.0, y0, 0, -1.5, y1, h, "neighbour", "Context")
        box(f"Neighbour_E{i}", LOT["w"] + 1.5, y0 + 2, 0, LOT["w"] + 12, y1, h + 1, "neighbour", "Context")


def build_house():
    H = HOUSE
    # ground + upper floor shell
    box("House_left_wing", H["x0"], H["y0"], 0, LEFT_WING_X1, H["y1"], H["roof"], "stucco", "House")
    box("House_right_block", LEFT_WING_X1, H["y0"], 0, H["x1"], H["y1"], H["roof"], "stucco", "House")
    # hip roof over left wing
    o = HIP["overhang"]
    hip_roof("Roof_left_hip", H["x0"] - o, H["y0"] - o, LEFT_WING_X1 + o, H["y1"] + o,
             HIP["eave"], HIP["ridge"] - HIP["eave"], "roof_metal", "House")
    # single-storey front projection with two dark hip roofs
    box("House_front_projection", H["x0"], GROUND_FRONT_Y, 0, H["x1"], H["y0"], H["floor1"], "stucco", "House")
    for i, r in enumerate(FRONT_ROOFS):
        hip_roof(f"Roof_front_{i}", r["x0"], GROUND_FRONT_Y - 0.5, r["x1"], H["y0"] + 0.3,
                 FRONT_ROOF_Z["eave"], FRONT_ROOF_Z["rise"], "roof_metal", "House")
    # tower (charred wood) with porthole
    T = TOWER
    box("Tower", T["x0"], T["y0"], 0, T["x1"], T["y1"], T["top"], "charred_wood", "House")
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.45, depth=0.08,
                                        location=(T["x0"] + 0.8, T["y0"] - 0.03, 7.4),
                                        rotation=(math.radians(90), 0, 0))
    po = bpy.context.object
    po.name = "Tower_porthole"
    po.data.materials.append(MAT["glass"])
    link(po, "House")
    # stair bulkhead on roof, rounded end toward the pool
    B = BULKHEAD
    r = (B["x1"] - B["x0"]) / 2
    box("Bulkhead", B["x0"], B["y0"], H["roof"], B["x1"], B["y1"] - r, B["top"], "stucco", "House")
    cyl("Bulkhead_round", (B["x0"] + B["x1"]) / 2, B["y1"] - r, H["roof"], B["top"], r, "stucco", 32, "House")
    # roof deck: turf, parapet, railings
    D = DECK
    box("Deck_turf", D["x0"], H["y0"], H["roof"], D["x1"], H["y1"], H["roof"] + 0.05, "turf", "RoofDeck")
    box("Deck_parapet_front", D["x0"], H["y0"], H["roof"], D["x1"], H["y0"] + 0.25, H["roof"] + D["parapet"],
        "stucco", "RoofDeck")
    box("Deck_parapet_east", D["x1"] - 0.25, H["y0"], H["roof"], D["x1"], H["y1"], H["roof"] + 0.5,
        "stucco", "RoofDeck")
    railing("Deck_rail_east", [(D["x1"] - 0.12, H["y0"]), (D["x1"] - 0.12, H["y1"])], H["roof"] + 0.5, 0.6,
            "RoofDeck")
    railing("Deck_rail_rear", [(D["x0"], H["y1"] - 0.1), (D["x1"], H["y1"] - 0.1)], H["roof"], 1.05, "RoofDeck")
    # spa (raised, at pool end), pergola + BBQ, dining table
    box("Spa", D["x0"] + 0.6, H["y1"] - 3.0, H["roof"], D["x0"] + 2.6, H["y1"] - 1.0, H["roof"] + 0.6,
        "timber", "RoofDeck")
    box("Spa_water", D["x0"] + 0.85, H["y1"] - 2.75, H["roof"] + 0.6, D["x0"] + 2.35, H["y1"] - 1.25,
        H["roof"] + 0.62, "water", "RoofDeck")
    px0, py0 = D["x1"] - 2.4, H["y0"] + 4.5
    for i, (dx, dy) in enumerate([(0, 0), (2.0, 0), (0, 1.6), (2.0, 1.6)]):
        box(f"Pergola_post{i}", px0 + dx, py0 + dy, H["roof"], px0 + dx + 0.1, py0 + dy + 0.1,
            H["roof"] + 2.4, "frame_black", "RoofDeck")
    box("Pergola_roof", px0 - 0.2, py0 - 0.2, H["roof"] + 2.4, px0 + 2.3, py0 + 1.9, H["roof"] + 2.5,
        "pergola_red", "RoofDeck")
    box("BBQ_counter", px0 + 0.1, py0 + 1.0, H["roof"], px0 + 2.0, py0 + 1.6, H["roof"] + 0.9,
        "frame_black", "RoofDeck")
    box("Deck_planter", D["x0"] + 0.8, H["y0"] + 6.5, H["roof"], D["x0"] + 3.0, H["y0"] + 8.0,
        H["roof"] + 0.6, "stucco", "RoofDeck")
    # rear balcony + exterior stair from deck down to it
    RB = REAR_BALCONY
    box("Rear_balcony", RB["x0"], H["y1"], RB["z"] - 0.2, RB["x1"], H["y1"] + RB["depth"], RB["z"],
        "stucco", "House")
    railing("Rear_balcony_rail", [(RB["x0"], H["y1"] + RB["depth"]), (RB["x1"], H["y1"] + RB["depth"])],
            RB["z"])
    steps = 16
    for i in range(steps):
        x = RB["x1"] - 0.5 - (i + 1) * 0.28
        z = H["roof"] - (i + 1) * (H["roof"] - RB["z"]) / steps
        box(f"Rear_stair_{i}", x, H["y1"] + 0.2, z - 0.05, x + 0.3, H["y1"] + 1.2, z, "timber", "House")


def build_openings():
    H = HOUSE
    fy, ry = ("y", H["y0"], -1), ("y", H["y1"], 1)
    # front, ground floor
    gy = ("y", GROUND_FRONT_Y, -1)
    window("Front_door", gy, 3.0, 4.2, 0.0, 2.7)
    window("Front_win_left", gy, 4.6, 6.6, 0.6, 2.6)
    window("Front_win_right", gy, 9.6, 13.2, 0.5, 2.6)
    # front, upper floor
    window("Front_up_left", fy, 3.6, 5.0, 3.9, 5.6)
    window("Front_up_right", fy, 10.2, 12.8, 3.9, 5.6)
    # rear
    window("Rear_slider", ry, 5.2, 10.4, 0.0, 2.8)
    window("Rear_slider_2", ry, 11.2, 13.3, 0.0, 2.8)
    window("Rear_living_door", ry, 2.9, 4.3, 0.0, 2.7)
    window("Rear_up_left", ry, 3.0, 5.6, 4.0, 5.5)
    window("Rear_up_mid", ry, 7.6, 9.4, 3.6, 5.8)
    window("Rear_up_right", ry, 10.6, 13.2, 3.6, 5.8)
    # sides
    window("East_ground", ("x", H["x1"], 1), 7.0, 10.0, 0.6, 2.6)
    window("East_up", ("x", H["x1"], 1), 12.0, 14.5, 4.0, 5.5)
    window("West_up", ("x", H["x0"], -1), 9.0, 11.0, 4.0, 5.5)
    window("West_ground", ("x", H["x0"], -1), 13.0, 16.0, 0.6, 2.6)


def kidney(name, cx, cy, material, z0, z1, lobes):
    objs = []
    for i, (dx, dy, rx, ry) in enumerate(lobes):
        o = cyl(f"{name}_{i}", cx + dx, cy + dy, z0, z1, 1.0, material, 48, "Courtyard")
        o.scale = (rx, ry, 1)
        objs.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def smooth(pts, n=6):
    """Catmull-Rom resample of a closed polygon."""
    out = []
    for i in range(len(pts)):
        p0, p1, p2, p3 = (pts[(i + k) % len(pts)] for k in (-1, 0, 1, 2))
        for t in [j / n for j in range(n)]:
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[a]) + (-p0[a] + p2[a]) * t + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * t2
                                    + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * t3) for a in (0, 1)))
    return out


def flat_poly(name, outline, grow, height, material):
    """Extruded smooth closed shape at POOL centre; grow expands it outward (metres)."""
    pts = smooth(outline)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    pts2 = []
    for x, y in pts:
        d = math.hypot(x - cx, y - cy) or 1
        pts2.append((POOL["cx"] + x + (x - cx) / d * grow, POOL["cy"] + y + (y - cy) / d * grow))
    n = len(pts2)
    verts = [(x, y, 0.0) for x, y in pts2] + [(x, y, height) for x, y in pts2]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh(name, verts, faces, material, "Courtyard")


def build_courtyard():
    H = HOUSE
    box("Terrace_deck", H["x0"], H["y1"], 0, H["x1"], H["y1"] + 2.6, 0.45, "timber", "Courtyard")
    box("Terrace_step1", 5.0, H["y1"] + 2.6, 0, 12.0, H["y1"] + 3.0, 0.30, "timber", "Courtyard")
    box("Terrace_step2", 5.0, H["y1"] + 3.0, 0, 12.0, H["y1"] + 3.4, 0.15, "timber", "Courtyard")
    box("Courtyard_turf", 0.3, H["y1"] + 2.6, 0, LOT["w"] - 0.3, PAVILION["y0"], 0.03, "turf", "Courtyard")
    # kidney outline traced from the overhead drone frame (metres, relative to POOL centre)
    outline = [(-4.2, -0.2), (-3.9, 1.6), (-2.8, 2.5), (-1.2, 2.4), (0.2, 1.7), (1.6, 2.1), (3.2, 2.6),
               (4.4, 2.0), (4.6, 0.6), (3.8, -0.8), (2.4, -1.8), (0.6, -2.4), (-1.4, -2.5), (-3.2, -1.8)]
    flat_poly("Pool_coping", outline, 0.5, 0.06, "paving")
    flat_poly("Pool_water", outline, 0.0, 0.09, "water")
    beach = [(1.4, 0.4), (2.4, 2.2), (3.6, 2.2), (4.2, 1.2), (4.0, 0.0), (3.0, -0.8), (1.9, -0.6)]
    flat_poly("Pool_beach_entry", beach, -0.1, 0.095, "pool_shelf")
    # lounge (west) and cabanas (east)
    box("Lounge_deck", 0.6, 27.0, 0, 3.6, 30.4, 0.12, "timber", "Courtyard")
    box("Lounge_sofa", 0.8, 28.6, 0.12, 3.2, 30.0, 0.8, "macrame", "Courtyard")
    cyl("Umbrella_pole", 2.6, 26.4, 0, 2.6, 0.04, "frame_black", 8, "Courtyard")
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.5, depth=0.5, location=(2.6, 26.4, 2.7))
    u = bpy.context.object
    u.name = "Umbrella"
    u.data.materials.append(MAT["macrame"])
    link(u, "Courtyard")
    for i, cy in enumerate((24.0, 27.0)):
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=1.35, radius2=0.08, depth=2.6,
                                        location=(LOT["w"] - 1.7, cy, 1.3), end_fill_type="NOTHING")
        c = bpy.context.object
        c.name = f"Cabana_{i}"
        c.data.materials.append(MAT["macrame"])
        link(c, "Courtyard")
        box(f"Cabana_bed_{i}", LOT["w"] - 2.6, cy - 0.8, 0, LOT["w"] - 0.8, cy + 0.8, 0.45, "macrame", "Courtyard")
    box("Pavilion_bench", 10.2, PAVILION["y0"] - 0.9, 0, 13.6, PAVILION["y0"] - 0.3, 0.45, "timber", "Courtyard")


def build_pavilion():
    P = PAVILION
    box("Pavilion", P["x0"], P["y0"], 0, P["x1"], P["y1"], P["h"], "stucco", "Pavilion")
    seg = (P["x1"] - P["x0"]) / 3
    for i in range(3):
        box(f"Pavilion_roof_{i}", P["x0"] + i * seg + 0.05, P["y0"], P["h"], P["x0"] + (i + 1) * seg - 0.05,
            P["y1"], P["h"] + 0.25, "stucco", "Pavilion")
    window("Pavilion_glass_front", ("y", P["y0"], -1), P["x0"] + 4.0, P["x1"] - 1.0, 0.1, 2.8, "Pavilion")
    window("Pavilion_garage", ("y", P["y1"], 1), P["x0"] + 1.0, P["x0"] + 6.0, 0.0, 2.4, "Pavilion")
    box("Pavilion_ac", P["x1"] - 2.0, P["y1"] - 1.5, P["h"] + 0.25, P["x1"] - 1.2, P["y1"] - 0.9,
        P["h"] + 0.85, "concrete", "Pavilion")


def build_landscape():
    W = LOT["w"]
    # slatted wood front fence with gate gap
    for x in [i * 0.12 for i in range(int(W / 0.12))]:
        if 2.8 < x < 4.4:
            continue
        box(f"Fence_{x:.2f}", x, FRONT_FENCE_Y, 0, x + 0.06, FRONT_FENCE_Y + 0.06, 1.3, "timber", "Landscape")
    box("Front_path", 2.9, 0, 0, 4.3, GROUND_FRONT_Y, 0.03, "paving", "Landscape")
    cyl("Side_patio", 1.4, 3.6, 0, 0.04, 1.3, "stone", 32, "Landscape")
    box("Porch_column", 2.4, GROUND_FRONT_Y - 0.1, 0, 2.8, GROUND_FRONT_Y + 0.3, 3.3, "stucco", "House")
    box("Front_planter_wall", 0, FRONT_FENCE_Y - 0.1, 0, LOT["w"], FRONT_FENCE_Y + 0.25, 0.55, "stucco", "Landscape")
    # shrubs along the fence, house front and side boundaries
    import random
    rnd = random.Random(7)
    spots = [(x, 1.4) for x in (0.8, 1.8, 6.0, 7.2, 8.6, 10.0, 11.4, 12.8, 14.2)]
    spots += [(0.5, y) for y in range(6, 30, 2)] + [(LOT["w"] - 0.5, y) for y in range(6, 30, 2)]
    for i, (x, y) in enumerate(spots):
        place(rnd.choice(["shrub_02", "shrub_04"]), x, y, rot=rnd.uniform(0, 6.28),
              scale=rnd.uniform(1.8, 2.8))
    # wall lights by the entry and on the rear facade
    for i, (x, y) in enumerate([(2.85, GROUND_FRONT_Y - 0.05), (4.4, GROUND_FRONT_Y - 0.05)]):
        box(f"Wall_light_front_{i}", x - 0.06, y - 0.08, 1.8, x + 0.06, y, 2.4, "wall_light", "Landscape")
    for i, x in enumerate((4.8, 10.8, 13.5)):
        box(f"Wall_light_rear_{i}", x - 0.06, HOUSE["y1"], 2.9, x + 0.06, HOUSE["y1"] + 0.08, 3.1,
            "wall_light", "Landscape")
    for i, (x, y, h, lx, ly) in enumerate([(1.2, 2.0, 8.5, 0.4, 0.2), (13.6, 2.4, 9.0, -0.5, 0.3),
                                           (1.0, 22.0, 7.5, 0.3, -0.2), (13.2, 21.5, 8.0, -0.4, 0.0),
                                           (0.8, 30.0, 6.5, 0.5, -0.3), (5.6, 22.2, 10.5, 0.2, 0.4)]):
        palm(f"Palm_{i}", x, y, h, (lx, ly), seed=i)
    place("outdoor_table_chair_set_01", 12.2, HOUSE["y1"] + 1.2, 0.45, collection="Courtyard")
    place("outdoor_table_chair_set_01", DECK["x0"] + 1.5, HOUSE["y0"] + 2.4, HOUSE["roof"] + 0.05,
          rot=1.57, collection="RoofDeck")


def cameras():
    """Cameras roughly matched to video frames for side-by-side review."""
    shots = {
        "front_street": ((7.5, -16.0, 1.7), (7.5, 10.0, 4.0), 30),            # exterior/05
        "aerial_front": ((12.0, -14.0, 13.0), (7.5, 12.0, 3.0), 35),          # exterior/14
        "top_down": ((7.65, 19.2, 70.0), (7.65, 19.2, 0.0), 35),              # exterior/15
        "rear_courtyard": ((3.5, 29.8, 3.2), (9.5, 18.0, 3.8), 20),           # exterior/12
        "aerial_rear": ((2.0, 46.0, 18.0), (8.0, 22.0, 2.0), 35),             # exterior/21
    }
    for name, (loc, target, lens) in shots.items():
        cam = bpy.data.cameras.new(name)
        cam.lens = lens
        o = bpy.data.objects.new("Cam_" + name, cam)
        bpy.context.scene.collection.objects.link(o)
        o.location = loc
        d = Vector(target) - Vector(loc)
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return shots


def world():
    w = bpy.data.worlds.new("Sky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(TEX_DIR, "sky.hdr"))
    nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"])
    nt.nodes["Background"].inputs["Strength"].default_value = 1.0
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(40), 0, math.radians(200)))
    bpy.context.object.data.energy = 3.0
    bpy.context.object.data.angle = math.radians(1.5)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials()
    build_site()
    build_house()
    build_openings()
    build_courtyard()
    build_pavilion()
    build_landscape()
    uv_all()
    shots = cameras()
    world()

    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "assets", "house_exterior.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, "assets", "house_exterior.glb"),
                              export_format="GLB", export_apply=True)

    if RENDER:
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 48
        sc.cycles.use_denoising = True
        sc.render.resolution_x, sc.render.resolution_y = 960, 540
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Base Contrast"
        sc.view_settings.exposure = 0.0
        out = os.path.join(ROOT, "renders")
        os.makedirs(out, exist_ok=True)
        for name in shots:
            sc.camera = bpy.data.objects["Cam_" + name]
            sc.render.filepath = os.path.join(out, name + ".png")
            bpy.ops.render.render(write_still=True)


main()
