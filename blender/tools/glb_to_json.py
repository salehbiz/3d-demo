"""Convert a binary .glb into an equivalent self-contained glTF JSON (buffer embedded as base64).

Used for hosts that won't serve .glb (claude.ai Artifacts serve .json). three.js GLTFLoader
reads either form.   Usage: python3 blender/tools/glb_to_json.py in.glb out.json
"""
import base64
import json
import struct
import sys


def convert(src, dst):
    data = open(src, "rb").read()
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF" and version == 2, "not a glTF 2.0 binary"
    off, doc, binchunk = 12, None, b""
    while off < length:
        clen, ctype = struct.unpack_from("<I4s", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == b"JSON":
            doc = json.loads(chunk)
        elif ctype == b"BIN\x00":
            binchunk = chunk
        off += 8 + clen
    doc["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binchunk).decode()
    with open(dst, "w") as f:
        json.dump(doc, f, separators=(",", ":"))


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
