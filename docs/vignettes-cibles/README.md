# Thumbnails for 45 community targets

Packs `face01`, `face02`, `face03`, `face04` and `breast03` of the staging
repository, which have targets but no images. Before/after split, with the
region the target displaces painted over both halves.

Reproduce with `bin/lot6-yeux-v2.py` (eyes) and `bin/lot6-familles.py` (mouth,
ears, chest, jaw).

## Review of 25 October 2026

24 thumbnails redone, all displayed in a contact sheet.
Ears, mouth, 5 eye targets.

It uses the wireframe patch, which displays the part of mesh deformed as a blue
wireframe.

## How each frame is found

The aim is measured per target, not guessed per family: a wide probe with
`--refine` gives the centre and the spread of the region, and the final frame
follows from it. Under 5 cm wide the focal length goes to 400 mm, since the
camera cannot come closer.

**The whole region must fit in the frame.** Showing one eye when both change
alike is fine; a region running off the edge is not, since its extent is then
unreadable. The frame is `2 × spread × 1.25`, and a second pass widens it by
45 % if the patch still touches an edge.

⚠ `spread_m` is a **radius** around the centre of the region, not its width —
the engine itself frames at `2 × spread × context`. A frame set at
`spread × 1.5` was therefore about half of what was needed, and nine of the
seventeen eye targets had their region cut by the edge.

This matters. Five of the seventeen eye targets first came out with no patch at
all, because the family aim sits on the eye while their region — eye bags,
drooping corners — sits below it, outside a 5.5 cm frame. At a wide frame the
same mask reads 205 out of 255 where the tight one read 1.

**So an empty mask is a framing check, not a verdict on the target.** Measuring
it is the cheapest way to catch a frame that missed.

## Targets that do not read, and why

| target | reason |
| --- | --- |
| `jaldmic_drooped_rabbit_ears` | file returns 404 upstream, nothing to render |
| `pepo_fix_boy_eyes` | its 192 vertices move under the surface, inside the eye socket, so the region is never visible. Rendered without a patch |
| `culturalibre_ear_vertex_fix` | moves 2 vertices |
| `blindsaypatten_fix_male_nipple` | 64 vertices, 0.05 mm; now readable once the frame holds the whole region |
| `titleknown_great_soft_jelly_thing…` | transforms the whole body although it is filed under mouth; rendered wide, unreadable at icon size |
| `jujube_male_fixed_nipples` | same, filed under chest |

`culturalibre_belly_eye` is filed under eyes but works on the belly; it is
rendered on its own frame.

## Eyes: reviewed one by one

Sixteen of the seventeen eye targets were reviewed and replaced after the
first pass:

- **Nine use the wireframe patch**: the region is drawn as a blue wireframe
  over the mesh instead of a flat colour, so the skin stays readable below.
  Six of them are seen **in profile** (eye bags, wrinkle, eyebrow, eyelid
  thinning, realistic eyelids, eyebag smoothing), since their change is a
  depth the front view flattens.
- **Five are rendered without the eyeballs** (`very_large_eyes1`,
  `eyeballs_grow`, `eyeballs_shrink`, `eyes_in`, `eyes_out`), also with the
  wireframe patch. The eyeballs are attached meshes with no shape keys: they
  keep their size while the target reshapes the socket and the eyelids, and
  seem to stick out of them. What these targets change is the shape around
  the eye, so it is shown without them (`--hide-eyes`, `bin/lot6-globe-fil.py`).
  The patch runs slightly off the frame on `very_large_eyes1`; the region
  still reads.
- **`eye_outer_corner_crease` and `eyes_outer_droop`** keep the version of
  18 September.

`pepo_fix_boy_eyes` is unchanged (see above).

## Checks

35 thumbnails, all opaque: 24 at 512×512 (review of 25 October), the rest at
256×256. Contact sheet: `planche-lot6.png`.
`rendering-log.txt` gives the frame and the patch coverage of the first pass
only.
