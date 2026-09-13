# Proxy thumbnails: contact sheets

Rendered 2026-09-13 with `bin/proxies-v2.sh`. 29 proxies, two packs.

| pack | licence | proxies | sheet |
|---|---|---|---|
| `proxies01_cc0` | CC0 | 15 | [contact sheet](proxies01_cc0-contact-sheet.png) |
| `proxies02_ccby` | CC-BY | 14 | [contact sheet](proxies02_ccby-contact-sheet.png) |

## Measured framing

Three numbers per proxy: **new vertices** (absent from the base mesh),
**clusters** they form, **spread** of those clusters in height.

| regime | test | thumbnail | CC0 | CC-BY |
|---|---|---|---|---|
| **global** | new > 90 % | whole mesh, framed on head and shoulders | 4 | 0 |
| **local** | spread < 35 % | grey mesh, reworked area alone in blue, zoomed | 4 | 7 |
| **spread** | in between | areas painted, framed on their envelope | 7 | 6 |

**The test is topological.** It asks whether a vertex exists in the base mesh.
A retopologised ear sits on the same surface as the original one, so distance
alone stays blind to it.

## Fixed settings

| | |
|---|---|
| background | black, opaque |
| body | near-white. Neutral by default, **female or male when the asset is sex-specific** (8 of the 29, read from name, title and catalogue category) |
| colour | one blue for everything mesh-related |
| edges | the real mesh edges, so quads stay quads. The Wireframe node would draw the engine's triangulation instead |
| colour blindness | blue keeps its full area under all three forms; the previous orange dropped to 0,01 % under tritanopia |

## Exception

`jujube_proxy_with_helpers_test` changes two areas far apart (pelvis, face).
A single frame serves one or the other, so it is a **stacked diptych**, face
above, anatomy below.

## Regenerate

```
sh bin/proxies-v2.sh <pack> mesurer            # classify
sh bin/proxies-v2.sh <pack> global|local|disperse [assets]
```

Every setting is a command-line option.
