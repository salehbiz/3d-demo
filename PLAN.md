# 3D House Demo — Plan

Goal: a web app like planpoint-next3d (interactive 3D property viewer) for the house in
https://vimeo.com/1206240401 — exterior orbit view, walkable interior, clickable rooms/hotspots
with info panels, all built from a Blender model reconstructed from the video.

## Phase 0 — Unblock access (needed before anything else)
- This cloud environment's network policy currently **blocks vimeo.com and planpoint-next3d.vercel.app**.
  Either allow those hosts (plus `*.vimeocdn.com`, `pypi.org`, `download.blender.org`) in the
  environment's network settings, or upload the video file (MP4) into the repo / session.
- If the Vimeo video is private, a download-enabled link or the raw file is needed.

## Phase 1 — Frame extraction & survey
1. Download video (`yt-dlp`), extract frames with `ffmpeg` (scene-change detection + 1 fps).
2. De-duplicate (perceptual hash), keep sharpest frame per shot.
3. Tag every kept frame: exterior (front / sides / rear / roof / garden) or interior room.
4. Produce a contact sheet (`docs/frames/`) and a room inventory: room name, adjacency, doors,
   windows, materials, fixtures, furniture.

## Phase 2 — Floor plan & measurements
1. Sketch the floor plan(s) from walkthrough continuity (which door leads where).
2. Estimate scale from known references: doors ≈ 2.03 m × 0.82 m, ceiling ≈ 2.4–2.7 m,
   counter height 0.9 m, stair riser ≈ 0.18 m.
3. Optional: run COLMAP / photogrammetry on frames for camera poses + sparse point cloud
   to validate proportions (works best on exterior orbit shots).
4. Output: `plan/floorplan.json` (walls, openings, rooms as polygons) — single source of truth.

## Phase 3 — Blender model (scripted, reproducible)
- Install Blender headless (4.x) in the environment; build entirely via Python (`blender/build.py`)
  that reads `floorplan.json`, so changes to the plan regenerate the model.
- Exterior: walls, roof, facade materials, windows/doors, terrain, landscaping.
- Interior: walls, floors, ceilings, stairs, kitchen/bath fixtures, key furniture.
- Materials: PBR textures (Poly Haven / ambientCG, CC0) matched to colours in the frames.
- Lighting: HDRI sky + baked lightmaps (Cycles bake) so the web view looks realistic at low cost.
- Each room is a named collection (`Room_Kitchen`, …) → becomes clickable in the web app.
- Export: `house.glb` (Draco-compressed, KTX2 textures), target < 30 MB.

## Phase 4 — Web viewer (the "Planpoint"-style tool)
Stack: Next.js + React Three Fiber + drei, deployed on Vercel.
- **Exterior mode**: orbit camera, time-of-day toggle, floor "explode"/cut-away to see inside.
- **Floor plan mode**: top-down view, hover/click rooms → info card (name, area m², photos
  from the video, features).
- **Walkthrough mode**: first-person (WASD + mouse / touch joystick), collision against walls,
  stairs, teleport hotspots between rooms.
- **Hotspots**: clickable markers on fixtures (kitchen, fireplace, etc.) showing the matching
  video frame + notes.
- Side panel UI: room list, measurements tool, screenshot, fullscreen.
- Performance: lazy-load per floor, LODs, baked lighting, mobile support.

## Phase 5 — Polish & validation
- Side-by-side compare renders vs. video frames from matching camera angles; iterate.
- Lighthouse / FPS check on desktop + mobile; deploy preview.

## Deliverables in this repo
```
docs/frames/        extracted reference frames + contact sheet
plan/floorplan.json reconstructed plan
blender/build.py    scripted model generation → assets/house.glb
web/                Next.js viewer
```

## Honest expectations
"Perfect" accuracy from a single video is not possible without real measurements; expect
correct layout, proportions within ~10–15 %, and look-alike materials. A floor plan or a few
measurements from the owner would greatly improve accuracy.
