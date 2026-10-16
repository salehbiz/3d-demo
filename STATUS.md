# Project status & handoff

Goal: realistic 3D model of 1159 Diamond St (Pacific Beach) from the property video, plus a
Planpoint-style web viewer (exterior orbit, floor plan view, walkthrough, clickable rooms).

## Done
- `PLAN.md`: overall plan.
- `source/video.mp4`: the property video.
- `frames/`: 55 labelled key frames (exterior/interior), contact sheets, survey notes
  (`frames/README.md`), approved site plan (`frames/generated/01_site-plan.webp`).
- `plan/ground_floor.json` + `plan/render_plan.py`: first ground-floor layout. The user said it is
  still wrong; it is parked until the exterior is final (decision: exterior first, then interior).
- Exterior model (shape approved by the user):
  - `blender/build_exterior.py` builds everything from dimension tables; lot is 15.3 x 38.4 m
    (6,300 sq ft public record).
  - `blender/fetch_textures.py` downloads the Poly Haven CC0 textures, models and HDRI.
    These are not in git; run it first.
  - `assets/house_exterior.blend` / `.glb` are the base model, without the polish modules yet.
  - `renders/compare/` has video-vs-model side-by-sides from 5 matched cameras.
- Polish modules `blender/polish/{tower,planting,courtyard,pool,front}.py`: first build done for
  all 5. An independent critique pass was running when the session ended, and the revision pass
  never ran. Current previews are in `renders/polish_preview/<area>/`.

## To do next (in order)
1. Restore assets: `python3 blender/fetch_textures.py`.
   - Install Blender 4.2 LTS if it is missing:
     download.blender.org/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz
2. Combine all polish modules and render:
   `blender -b -P blender/build_exterior.py -- --render`
   - This applies every module in `blender/polish/` and writes the `.blend`, `.glb` and `renders/`.
   - Then make comparisons with `blender/tools/compare.sh`.
   - Check for clashes between modules: planting vs courtyard beds along the side walls,
     front vs planting along the fence.
3. Optional: one critique and revision pass per area, comparing the module renders with the
   frames listed in each module's docstring.
4. Compress the `.glb` for the web; it is 33 MB with textures embedded.
   Use Draco + KTX2/WebP and target under 15 MB.
5. Build the web viewer (Next.js + React Three Fiber, deploy on Vercel):
   - exterior orbit
   - top-down floor-plan mode
   - first-person walkthrough
   - clickable room and feature hotspots with video frames
6. Interior: fit rooms behind the exterior's windows and doors, floor by floor, verifying each
   against `frames/interior/`. Then add the interiors to the viewer.

## Preview loop (one module, no shared-file writes)
`blender -b -P blender/build_exterior.py -- --render --no-save --polish <area> --cams <cam> --res 640x360 --samples 24 --out renders/wip/<area>`
