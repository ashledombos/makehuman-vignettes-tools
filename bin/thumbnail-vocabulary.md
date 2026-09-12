# Thumbnail vocabulary

*A short glossary for the target and asset thumbnails, with one example each.
Written so that a device can be named in three words instead of described from
scratch every time.*

A thumbnail is always **a view** plus **an effect**. The view says where the
camera is and how tight the frame is; the effect says what is added to the
image.

⚠ **The split and the diptych each come in two orientations**, and the
orientation is measured, not chosen: the changing zone is projected on the
camera axes and its two extents compared. A wider-than-tall zone gives a
**horizontal** cut and two landscape shots; a taller-than-wide zone gives a
**vertical** cut and two portrait shots. Verified: an erect penis comes out
horizontal, a flaccid one vertical.

⚠ The orientation also fixes the **shape of each shot**, since two halves must
assemble into a square: 256 x 128 for a horizontal cut, 128 x 256 for a
vertical one. Two square shots side by side make a 512 x 256 rectangle, not an
icon — a mistake made on 06-09 and now refused by the compositing guard, which
tests the **result** and no longer the shape of the input.

Example sheet: `effects.png` — one exemplar per effect, in the same order as
below.

---

## The six effects

### The split

The two ends of a slider, side by side, separated by a dotted line. Each half is
a half-format shot, so the assembled thumbnail is square.

*Example: breast height. Left the low end, right the high end.*

Use it when the change does **not** move the outline: contour displacement below
about 5 % of the subject.

### The two lines

The **middle** state of the slider rendered solid, with both ends traced over it
as dotted curves — yellow `#F0E442` and sky blue `#56B4E9`, 3 px. One image, no
split.

*Example: breast volume distribution. The two curves part over the upper slope.*

Use it when the change **does** move the outline: contour displacement above
about 5 %. Below that the two curves lie on top of each other and say nothing.

⚠ Both colours are from the Okabe-Ito palette. A pink/cyan pair looks better to
normal vision and is unusable: simulated for deuteranopia its distance drops
from 215 to 55, i.e. two lines of the same colour.

### The diptych

Two halves of the **same** object: on the left the render — studio grey, rim
light; on the right the mesh — ink lines on technical white, exposure raised by
0.9 stop. What it looks like, and what it is made of.

*Example: an added penis proxy.*

Use it for an asset whose addition is **local**, or for a **partial** proxy such
as a head-only mesh.

⚠ The white half cannot be obtained from the material alone. Raising albedo from
0.62 to 0.92, i.e. by 48 %, changes the image by only 8 %, because the view
transform compresses highlights. It takes exposure.

### The blueprint

One image: the mesh drawn on a very light body, flat shading, subdivision off.
A technical drawing.

*Example: a 412-face game proxy.*

Use it for a **retopology**, whether low-poly or at equal density. That is what
such an asset sells: its topology, not its shape.

⚠ Subdivision must be off. It is on by default and it erases the very subject of
the thumbnail. And smooth shading must be off too, otherwise a 412-face body
looks as round as a 14 000-face one.

⚠ Line thickness is a **fraction of the mean edge length** (0.09), never a fixed
value: the thickness that draws a 412-face mesh cleanly drowns a 14 000-face one
in a solid mass.

### The map

One image: the body in studio grey, smooth, with the zones that depart from the
base body painted in **vermillion**. It says **where** the asset changes
something.

*Example: a muscular proxy. Shoulders, arms and thighs light up.*

Use it for a **shape change without retopology**, where the title alone
("female muscular") leaves the user guessing which parts are affected.

⚠ The frame hugs the envelope of the painted zones, margin 1.02. Head and lower
legs leave the frame when nothing touches them. A wide margin would bring the
head back in, and here the context is exactly what should be excluded.

⚠ It informs but does not distinguish. Two proxies differing only by a pattern
of small patches stay 1.1 apart at display size, against 15 to 30 for the other
thumbnails. That is a resolution limit, not a design failure.

### The portrait

One image, nothing added. For what is recognisable on its own.

*Example: a skeleton proxy.*

Use it when the whole silhouette is other: a skeleton, a mermaid tail. A colour
overlay there would be noise.

---

## The views

### Targets

| name | framing |
|---|---|
| **the pair** | three-quarter at 25°, landscape, horizontal split. Both breasts visible, both areolae acting as landmarks. |
| **the silhouette** | three-quarter at 70°, portrait, aim raised 6 cm to keep the chin in frame. |
| **the close-up** | square, arms down, no face. For a change that is **internal** to the shape. |

⚠ A thumbnail must also be **recognisable**, not only show its change. The
measured aim lands on what moves, which is correct and insufficient: without a
landmark the frame shows an arm and a belly. Raising the aim by 6 cm keeps the
chin and the neck; at 10 cm the mouth and nose come in and the eye leaves the
subject.

### Assets

| name | framing |
|---|---|
| **the head** | the top fifth of the subject. For the blueprint, where the subject is mesh density. |
| **the departure** | the zone that departs from the body, margin relative to its extent. For the diptych. |
| **the envelope** | the painted zones, frame hugging them at 2 %. For the map. |
| **the whole** | the entire object. For the portrait. |

---

## Lighting

| name | values |
|---|---|
| **the rim** | `key=0.7, fill=0.6, rim=2.0, spot=0.05`, world 0.4. For profiles and close-ups. |
| **the front** | `key=1.1, fill=0.9, rim=4.0, spot=0.05`, world 0.55. For views near 25°. |

⚠ **Lighting is set per view angle, never copied as fixed numbers.** At 25° the
back light sits behind the subject and grazes almost nothing visible; at 70° it
skims the visible surface. With identical settings, mean luminance is 121 at 25°
against 158-184 at 70°. The same applies to the rim light itself: at 25° it takes
4.0 to draw the edge that 2.0 draws at 70°.

⚠ Two retired settings, kept on record so they are not reinvented:
`key=0.8, fill=0.2, rim=4`, world 0.2 — good modelling, but it **plates** the
front of the torso in blown white with black in front. It is not the back light
alone that does this, it is its combination with a low fill and a low ambient.
And `key=0.4, fill=2.0, rim=0.2`, world 0.6 — the only way to light the bottom
of a funnel, no longer needed.

---

## Materials

| name | values |
|---|---|
| **studio grey** | `colorMixIn=0.5, colorMixInStrength=0.6`; `0.62` linear for an asset |
| **fine grain** | as above plus `pore_strength=0.10, pore_scale=6000`. For close-ups. |
| **areola delta** | `nipple:colorMixIn=0.15, colorMixInStrength=0.6` |
| **technical white** | `0.92` **and** exposure +0.9 stop. The material alone is not enough. |

⚠ Grey, not white. Grey is the only value that holds whichever theme the user
runs: 6 points of difference between light and dark themes, against 48 for
white. It is not a compromise, it is independence from the theme.

⚠ The **grain must follow the frame scale**. Pores tuned for a whole body become
craters in a close-up, and the texture takes over from the form.

⚠ The **areola delta compensates for the lighting**. Brighter light drowns
pigment: contrast 37 at 0.20/0.4, 45 at 0.15/0.6.

---

## How a thumbnail is named

> "the silhouette in rim light, split" — breast height
> "the close-up, two lines" — breast volume distribution
> "the departure, diptych" — an added penis
> "the head, blueprint" — a game proxy
> "the envelope, map" — a muscular proxy
> "the whole, portrait" — a skeleton

---

## Choosing the effect for an asset, measured

Four numbers per asset, all computed from the proxy and the base body. The
**order** of the rules matters as much as the thresholds.

| measure | what it is |
|---|---|
| `density` | mean edge length of the proxy over that of the body |
| `shape` | 99th percentile of the distance to the body, over the mean edge length |
| `max` | largest distance to the body, in metres |
| `far` | share of vertices more than 10 mm from the body |

1. `density > 1.5` → **blueprint**. A game mesh, whatever else it does.
2. proxy height `< 0.9 m` → **diptych**. A partial object, a head alone.
3. `max > 0.30` → **portrait**. A limb replaced: the mermaid.
4. `far > 0.25` → **portrait**. The whole mesh elsewhere: the skeleton.
5. `max > 0.06` → **diptych**. A local addition: a penis.
6. `shape < 0.30` → **blueprint**. A resampling of the same surface.
7. otherwise → **map**. A real shape change: musculature.

⚠ Rule 1 must come first: a 412-face mesh departs from the body on 47 % of its
vertices by **faceting alone**, so rule 4 would otherwise catch it. And rule 3
must come before rule 4: only 5 % of the mermaid's vertices depart, but they
depart by 74 cm.

⚠ Threshold 0.30 in rule 6 is read from the data, not from first principles. My
reasoning was that a retopology departs from the body by at most **one edge
length**, which is true — but the real shape changes in this pack are **also**
below one edge length: 0.58 for a musculature. They still sit five to seven
times above the true retopologies, measured at 0.00, 0.08 and 0.11. A MakeHuman
musculature is a change **finer than the mesh resolution**, which is why it
resists every device.

Applied to `proxies01_cc0`, 15 assets: **7 blueprints, 4 diptychs, 2 portraits,
2 maps**. No case hand-coded.

| asset | density | shape | max | far | effect |
|---|---|---|---|---|---|
| verylowpoly | **7.90** | 0.46 | 0.035 | 47 % | blueprint |
| uni1228 | **3.67** | 0.22 | 0.012 | 0 % | blueprint |
| gamebody | **2.98** | 0.32 | 0.010 | 0 % | blueprint |
| ear_skin | 1.01 | **0.11** | 0.007 | 0 % | blueprint |
| sr_anime_topo_01 | 0.99 | **0.00** | 0.001 | 0 % | blueprint |
| female_generic | 1.00 | **0.08** | 0.011 | 0 % | blueprint |
| female_generic_fixed | 1.00 | **0.08** | 0.011 | 0 % | blueprint |
| head_only | 0.61 | 2.99 | 0.030 | 2 % | diptych (22 cm tall) |
| simple_penis | 0.99 | 3.97 | **0.066** | 2 % | diptych |
| proxytest_penis | 0.98 | 1.92 | **0.066** | 2 % | diptych |
| Male_Gen-Heal1 | 0.98 | 20.71 | **0.193** | 7 % | diptych |
| Snek | 1.25 | 30.19 | **0.741** | 5 % | portrait |
| culeverita | 0.49 | 15.36 | 0.095 | **44 %** | portrait |
| female_muscular | 1.01 | **0.58** | 0.013 | 0 % | map |
| female_less_muscular | 1.01 | **0.60** | 0.013 | 0 % | map |

⚠ `female_generic` and `female_generic_fixed` are **the same file**, identical
checksum, 44 021 lines. The pack ships the same mesh twice.
