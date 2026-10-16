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
LEFT_WING_X1 = 6.8          # upper-floor hip-roof wing spans x0..this
TOWER = dict(x0=6.8, x1=9.2, y0=7.0, y1=10.5, top=9.2)
BULKHEAD = dict(x0=7.0, x1=9.0, y0=10.5, y1=16.0, top=8.6)  # rounded end toward pool
HIP = dict(eave=6.2, ridge=7.4, overhang=0.5)
FRONT_ROOFS = [dict(x0=2.0, x1=7.6), dict(x0=8.4, x1=14.3)]  # hip roofs over front projection
FRONT_ROOF_Z = dict(eave=3.3, rise=1.1)
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
    mat("water", (0.05, 0.45, 0.6), 0.05, emit=((0.1, 0.5, 0.7), 0.3))
    mat("pool_shelf", (0.75, 0.82, 0.78), 0.4)
    mat("asphalt", (0.18, 0.18, 0.19), 0.9)
    mat("concrete", (0.6, 0.6, 0.58), 0.85)
    mat("pergola_red", (0.45, 0.12, 0.1), 0.6)
    mat("macrame", (0.95, 0.93, 0.88), 0.95)
    mat("palm_trunk", (0.35, 0.28, 0.2), 0.9)
    mat("palm_leaf", (0.15, 0.38, 0.08), 0.8)
    mat("neighbour", (0.75, 0.72, 0.68), 0.9)


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


def palm(name, x, y, h=8.0):
    cyl(name + "_trunk", x, y, 0, h, 0.16, "palm_trunk", 10, "Landscape")
    for i in range(8):
        a = i * math.pi / 4
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.35, radius2=0.0, depth=2.6,
                                        location=(x + math.cos(a) * 1.1, y + math.sin(a) * 1.1, h - 0.3))
        o = bpy.context.object
        o.name = f"{name}_leaf{i}"
        o.rotation_euler = (math.radians(70) * math.sin(a) * -1, math.radians(70) * math.cos(a), 0)
        o.data.materials.append(MAT["palm_leaf"])
        link(o, "Landscape")


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
    box("Deck_dining", D["x0"] + 1.0, H["y0"] + 1.2, H["roof"] + 0.72, D["x0"] + 1.9, H["y0"] + 3.6,
        H["roof"] + 0.77, "timber", "RoofDeck")
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
    # wooden stair from balcony down to terrace (seen beside spa in drone frame)
    for i in range(16):
        y = H["y1"] + RB["depth"] + i * 0.0  # stair runs along x at the west end of the balcony
        x = RB["x0"] + 0.2 + i * 0.27
        z = RB["z"] - (i + 1) * RB["z"] / 16
        box(f"Rear_stair_low_{i}", x, H["y1"] + RB["depth"], z - 0.05, x + 0.3, H["y1"] + RB["depth"] + 0.9,
            z, "timber", "House")


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
    window("Rear_slider", ry, 7.6, 13.0, 0.0, 2.8)
    window("Rear_living_door", ry, 3.2, 4.8, 0.0, 2.7)
    window("Rear_up_left", ry, 3.0, 5.6, 4.0, 5.5)
    window("Rear_up_right", ry, 9.4, 11.6, 3.8, 5.8)
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


def build_courtyard():
    H = HOUSE
    box("Terrace", H["x0"], H["y1"], 0, H["x1"], H["y1"] + 2.6, 0.18, "paving", "Courtyard")
    box("Terrace_steps", 6.0, H["y1"] + 2.6, 0, 12.0, H["y1"] + 3.2, 0.09, "paving", "Courtyard")
    box("Courtyard_turf", 0.3, H["y1"] + 2.6, 0, LOT["w"] - 0.3, PAVILION["y0"], 0.03, "turf", "Courtyard")
    lobes = [(-1.6, 0.5, 2.6, 2.2), (1.4, -0.4, 2.6, 2.0), (2.6, 1.4, 1.6, 1.4)]
    kidney("Pool_coping", POOL["cx"], POOL["cy"], "paving", 0.0, 0.06,
           [(dx, dy, rx + 0.45, ry + 0.45) for dx, dy, rx, ry in lobes])
    kidney("Pool_water", POOL["cx"], POOL["cy"], "water", 0.0, 0.08, lobes)
    kidney("Pool_beach_entry", POOL["cx"] + 2.6, POOL["cy"] + 1.4, "pool_shelf", 0.0, 0.085,
           [(0.4, 0.2, 1.3, 1.1)])
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
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=(LOT["w"] - 1.6, cy, 0.4))
        c = bpy.context.object
        c.name = f"Cabana_{i}"
        c.scale = (1, 1, 1.4)
        c.data.materials.append(MAT["macrame"])
        link(c, "Courtyard")
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
    cyl("Side_patio", 1.6, 4.0, 0, 0.04, 1.6, "paving", 32, "Landscape")
    for i, (x, y, h) in enumerate([(1.2, 2.0, 8.5), (13.6, 2.4, 9.0), (1.0, 22.0, 7.5), (13.2, 21.5, 8.0),
                                   (0.8, 30.0, 6.5)]):
        palm(f"Palm_{i}", x, y, h)


def cameras():
    """Cameras roughly matched to video frames for side-by-side review."""
    shots = {
        "front_street": ((7.5, -16.0, 1.7), (7.5, 10.0, 4.0), 30),            # exterior/05
        "aerial_front": ((12.0, -14.0, 13.0), (7.5, 12.0, 3.0), 35),          # exterior/14
        "top_down": ((7.65, 19.2, 70.0), (7.65, 19.2, 0.0), 35),              # exterior/15
        "rear_courtyard": ((3.0, 33.0, 4.0), (9.0, 18.0, 3.5), 24),           # exterior/12
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
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(50)
    sky.sun_rotation = math.radians(200)
    nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"])
    nt.nodes["Background"].inputs["Strength"].default_value = 0.12
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(40), 0, math.radians(200)))
    bpy.context.object.data.energy = 2.2


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials()
    build_site()
    build_house()
    build_openings()
    build_courtyard()
    build_pavilion()
    build_landscape()
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
        sc.view_settings.look = "AgX - Medium High Contrast"
        sc.view_settings.exposure = -0.6
        out = os.path.join(ROOT, "renders")
        os.makedirs(out, exist_ok=True)
        for name in shots:
            sc.camera = bpy.data.objects["Cam_" + name]
            sc.render.filepath = os.path.join(out, name + ".png")
            bpy.ops.render.render(write_still=True)


main()
