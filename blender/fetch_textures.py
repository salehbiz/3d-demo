"""Download CC0 PBR textures, models + HDRI from Poly Haven into assets/textures/.

Run: python3 blender/fetch_textures.py
"""
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures")
RES = "1k"

TEXTURES = [
    "white_plaster_rough_01", "box_profile_metal_sheet", "black_painted_planks", "wood_floor_deck",
    "leafy_grass", "precast_stone_paving", "stone_pathway", "pebble_cemented_floor", "asphalt_02",
    "concrete_floor_02",
    # added by polish modules (see POLYHAVEN_ASSETS in blender/polish/*.py)
    "teak_veneer", "rough_wood", "rock_boulder_dry", "black_oak_veneer",
]
MAPS = {"Diffuse": "diff", "nor_gl": "nor", "Rough": "rough"}
MODELS = ["shrub_02", "shrub_04", "outdoor_table_chair_set_01"]
HDRI = ("kloofendal_48d_partly_cloudy_puresky", "2k")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "3d-demo-builder"})
    return urllib.request.urlopen(req).read()


def main():
    for name in TEXTURES:
        files = json.loads(get(f"https://api.polyhaven.com/files/{name}"))
        os.makedirs(os.path.join(OUT, name), exist_ok=True)
        for key, short in MAPS.items():
            dst = os.path.join(OUT, name, f"{short}.jpg")
            if os.path.exists(dst):
                continue
            url = files[key][RES]["jpg"]["url"]
            open(dst, "wb").write(get(url))
            print("got", name, short)
    for name in MODELS:
        g = json.loads(get(f"https://api.polyhaven.com/files/{name}"))["gltf"][RES]["gltf"]
        base = os.path.join(ROOT, "assets", "models", name)
        os.makedirs(base, exist_ok=True)
        files = {f"{name}.gltf": g["url"], **{k: v["url"] for k, v in g.get("include", {}).items()}}
        for rel, url in files.items():
            dst = os.path.join(base, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst):
                open(dst, "wb").write(get(url))
        print("got model", name)
    name, res = HDRI
    dst = os.path.join(OUT, "sky.hdr")
    if not os.path.exists(dst):
        files = json.loads(get(f"https://api.polyhaven.com/files/{name}"))
        open(dst, "wb").write(get(files["hdri"][res]["hdr"]["url"]))
        print("got hdri", name)


main()
