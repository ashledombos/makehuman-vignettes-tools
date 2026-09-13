# Proxy thumbnails — contact sheets

Two contact sheets, one per pack, 29 proxies in total. Rendered
2026-09-13 with `bin/proxies-v2.sh`, which is in this repository, so any of
these can be regenerated or changed with one command line.

| pack | sheet |
|---|---|
| `proxies01_cc0` (CC0, 15 proxies) | [`proxies01_cc0-contact-sheet.png`](proxies01_cc0-contact-sheet.png) |
| `proxies02_ccby` (CC-BY, 14 proxies) | [`proxies02_ccby-contact-sheet.png`](proxies02_ccby-contact-sheet.png) |

## Why they look the way they do

Following your remark that the selling point of a proxy is its **topology**,
the thumbnails are wireframe-first: black background, near-white body, a
single blue used for everything that talks about the mesh, and the real mesh
edges rather than the Wireframe node (that node draws the engine's
triangulation, which would claim a wrong topology for a quad mesh).

A proxy is then framed by **what it actually changes**, measured rather than
judged. For each asset the script counts the vertices that the base mesh does
not have, how many separate clusters they form, and how far apart those
clusters spread:

| regime | test | thumbnail |
|---|---|---|
| **global** | more than 90 % of vertices are new | blueprint of the whole mesh, framed on head and shoulders |
| **local** | the new vertices span less than 35 % of the height | mesh in light grey, the reworked area alone in blue, zoomed on it |
| **spread** | neither | the areas painted in the same blue, framed on their envelope |

On the CC0 sheet that gives 4 global, 4 local and 7 spread; on the CC-BY
sheet, 7 local and 6 spread, with one exception (below).

The criterion is topological, not geometric, and that turned out to matter: a
retopologised ear sits on the same surface as the original one, so no distance
measurement can see it, while "this vertex does not exist in the base mesh"
sees it immediately.

## One exception

`jujube_proxy_with_helpers_test` changes two areas far apart, an added
anatomy at the pelvis and the face (the mouth and the four eyelids). No single
frame serves both: wide, the eyelids are invisible; tight, you must pick one.
It is therefore a **stacked diptych**, face on top, anatomy below, two
half-format shots making one square. It is the only proxy rendered on the male
body; all others use the neutral one.

## Colour

The blue was checked against the three forms of colour blindness (simulated,
not eyeballed). It keeps its whole area in all three, where the orange we used
before drops to 0,01 % of distinguishable pixels under tritanopia.

Nothing here is fixed. Every value is a command-line option, so if you prefer
another framing, another colour or another light, say which and I regenerate
the set.
