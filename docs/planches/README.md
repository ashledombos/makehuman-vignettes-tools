# Proxy thumbnails — contact sheets

Rendered 2026-09-13 with `bin/proxies-v2.sh`. 29 proxies, two packs.

| pack | licence | proxies | sheet |
|---|---|---|---|
| `proxies01_cc0` | CC0 | 15 | [contact sheet](proxies01_cc0-contact-sheet.png) |
| `proxies02_ccby` | CC-BY | 14 | [contact sheet](proxies02_ccby-contact-sheet.png) |

## Framing is measured, not chosen

Three numbers per proxy: **new vertices** (absent from the base mesh),
**clusters** they form, **spread** of those clusters in height.

| regime | test | thumbnail | CC0 | CC-BY |
|---|---|---|---|---|
| **global** | new > 90 % | whole mesh, framed on head and shoulders | 4 | 0 |
| **local** | spread < 35 % | grey mesh, reworked area alone in blue, zoomed | 4 | 7 |
| **spread** | neither | areas painted, framed on their envelope | 7 | 6 |

**Topological, not geometric.** A retopologised ear sits on the same surface
as the original: no distance measurement sees it, "this vertex is not in the
base mesh" does.

## Fixed settings

| | |
|---|---|
| background | black, opaque |
| body | near-white, neutral (one exception below) |
| colour | one blue for everything mesh-related |
| edges | real mesh edges — **not** the Wireframe node, which draws the engine's triangulation |
| colour blindness | blue keeps its full area under all three forms; the previous orange dropped to 0,01 % under tritanopia |

## Exception

`jujube_proxy_with_helpers_test` changes two areas far apart (pelvis, face).
No single frame serves both, so it is a **stacked diptych**, face above,
anatomy below. Only proxy rendered on the male body.

## Regenerate

```
sh bin/proxies-v2.sh <pack> mesurer            # classify
sh bin/proxies-v2.sh <pack> global|local|disperse [assets]
```

Every setting is a command-line option.
