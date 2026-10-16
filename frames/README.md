# Reference frames — 1159 Diamond St, Pacific Beach, San Diego

Source: `source/video.mp4` (1920×1080, 30 fps, 100 s). Frames re-exportable with the
timestamps in `keyframes.tsv` (`time  folder  name`).

- `sheets/` — 1 fps contact sheets with timecodes (whole video at a glance)
- `exterior/` — 22 key frames · `interior/` — 33 key frames

## What the video tells us (survey notes)

**Site (see `exterior/15_top-down-site-plan-night.jpg`, near-orthographic):**
long narrow lot. Main house at the street end, detached flat-roof **pavilion** at the
back, **courtyard** between them with freeform beach-entry pool (pebble-finish shallow
shelf), artificial lawn, deck strip with lounge/umbrellas, macramé cabanas.
Side yard (west) with circular flagstone patio, stepping stones and tropical planting.

**Main house — 3 storeys:**
- Exterior: white smooth stucco, black standing-seam metal hip roofs, black window frames,
  a **dark charred-wood (shou sugi ban) clad tower** with round porthole window,
  wood-slat front fence + gate, palms. Black glass balustrades on balconies.
- Roof deck: artificial turf, **spa**, outdoor kitchen/BBQ pergola, long teak dining
  table, lounge seating, ocean views (`exterior/18–20`).
- Ground: entry with pivot glass door + stone planter → open-plan **great room**
  (kitchen with black cabinets and Panda-marble waterfall island, 4 wood stools; dining
  with glass table + banquette; living room with sectional + coral-branch wall art).
  Floating oak stair with glass rail, pebble/plant atrium under stair, rattan pendants and
  skylight above. Full-width sliding glass wall opens to courtyard/pool.
- Upper floors: primary suite (chandelier, black accent wall, free-standing grey tub,
  walk-in shower), 3 further bedrooms each with en-suite, media room, powder room,
  wellness/yoga room, salt-wall infrared sauna.
- Floors: light wide-plank oak throughout; walls warm white / limewash plaster.

**Pavilion:** flat white roof, folding glass wall to the pool, kitchenette inside
(`interior/33`), garage/car display on street side (Lamborghini Urus at 1:22).

## Gaps the video doesn't cover (→ generate with ChatGPT)
No straight-on elevations, no rear/side elevation of the house, no floor plans,
no clean empty-room views, no clear view of the second floor hallway.

## ChatGPT image prompts

Upload the listed frames as references with each prompt.

**1. Site plan (refs: exterior/15, 09, 21)**
> Using the attached drone photos of the same property, create a clean architectural
> top-down site plan in daylight, orthographic, north up, no perspective. Show lot
> boundary, main 3-storey house footprint at the street end, detached flat-roof pavilion
> at the rear, freeform pool with beach entry between them, lawn, deck, side-yard
> circular patio. Flat colours, thin black outlines, labels for each area. Keep exact
> proportions and positions from the photos; do not invent extra structures.

**2. Front elevation (refs: exterior/05, 06, 14)**
> From the attached photos, draw a straight-on orthographic front elevation of this house
> in daylight. White smooth stucco, black standing-seam metal hip roofs, black-framed
> windows, dark charred-wood clad tower with a round porthole window, black glass
> balcony rails, wood-slat front fence and gate. Neutral sky, no people, no cars, no
> perspective distortion. Keep window count and placement exactly as in the photos.

**3. Rear elevation facing courtyard (refs: exterior/11, 12, 13, interior/01)**
> Same house as attached. Orthographic rear elevation facing the pool courtyard,
> daylight: full-width sliding glass wall on the ground floor, balconies with black glass
> rails above, roof deck with pergola on top. Match materials and window layout exactly.

**4. Side elevations (refs: exterior/07, 14, 21, 22)** — same wording, "left/right side
elevation", note the tower position.

**5. Pavilion elevation (refs: exterior/16, 17, interior/33)**
> Orthographic front elevation of the flat-roof white pavilion facing the pool: folding
> black-framed glass wall, warm wood ceiling, kitchenette visible inside.

**6. Ground floor plan (refs: interior/01–13)**
> Architectural 2D floor plan of the ground floor of this house, derived from the attached
> interior photos: entry with pivot door, open-plan kitchen with large waterfall island,
> dining area with banquette, living area with sectional, floating open stair with
> planted pebble atrium beneath, full-width sliding glass wall to the rear courtyard.
> Black lines on white, wall thickness shown, door swings, furniture outlines, room
> labels, approximate dimensions in metres. Lot width approx. 12–15 m.

**7. Upper floor plans (refs: interior/14–32)** — same style; list rooms: primary suite
with bath + tub, bedrooms 2–4 each with en-suite, media room, wellness room, sauna, powder.

**8. Material swatches (any interior frame)**
> Seamless tileable square texture, flat lighting, no shadows, of: [light wide-plank white
> oak floor | Panda white marble with bold black veining | warm limewash plaster wall |
> black matte cabinet | charred black vertical wood cladding | pebble-finish pool floor].

Generated images go in `frames/generated/` with the same name as the prompt number.
