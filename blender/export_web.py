"""Export a compressed, web-ready glTF of the exterior for the browser viewer.

Run after build_exterior.py:
    blender -b assets/house_exterior.blend -P blender/export_web.py
Output: web/public/models/house.glb  (Draco meshes, WebP textures <= 1024 px)

- drops the hidden model library, cameras and helper objects
- procedural-only material inputs (which glTF can't carry) are replaced by their flat colour
- textures are downscaled to MAX_TEX and stored as WebP
"""
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "public", "models", "house.glb")
MAX_TEX = 1024


def strip_hidden():
    lib = bpy.data.collections.get("Library")
    if lib:
        for o in list(lib.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in list(bpy.data.objects):
        if o.type in {"CAMERA", "LIGHT", "EMPTY"} and not o.children:
            bpy.data.objects.remove(o, do_unlink=True)


def flatten_procedural():
    """glTF only understands image textures wired into the Principled BSDF."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not bsdf:
            continue
        for name in ("Base Color", "Roughness", "Metallic", "Normal", "Alpha"):
            sock = bsdf.inputs.get(name)
            if not sock or not sock.links:
                continue
            src = sock.links[0].from_node
            if _has_image(src):
                continue
            if name == "Base Color":
                col = _representative_colour(src)
                if col:
                    sock.default_value = col
            nt.links.remove(sock.links[0])


def _has_image(node, depth=0):
    if node.type == "TEX_IMAGE":
        return True
    if depth > 6:
        return False
    return any(_has_image(l.from_node, depth + 1) for i in node.inputs for l in i.links)


def _representative_colour(node):
    for key in ("A", "Color1", "Color"):
        s = node.inputs.get(key) if hasattr(node, "inputs") else None
        if s is not None and not s.is_linked and len(getattr(s, "default_value", ())) == 4:
            return tuple(s.default_value)
    return None


def shrink_images():
    for img in bpy.data.images:
        if img.size[0] > MAX_TEX or img.size[1] > MAX_TEX:
            s = MAX_TEX / max(img.size)
            img.scale(max(1, int(img.size[0] * s)), max(1, int(img.size[1] * s)))


def main():
    strip_hidden()
    flatten_procedural()
    shrink_images()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUT, export_format="GLB", export_apply=True, use_visible=False,
        export_image_format="WEBP", export_image_quality=80,
        export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
        export_extras=True, export_cameras=False, export_lights=False,
    )
    print("web export:", OUT, round(os.path.getsize(OUT) / 1e6, 1), "MB")


main()
