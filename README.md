# Outils de rendu des vignettes MakeHuman/MPFB2

Scripts personnels utilisés pour produire les vignettes de cibles (asym,
poitrine) et de proxies du projet MakeHuman/MPFB2. Ils tournent en headless
Blender contre le dépôt `makehumancommunity/asset_packs_staging`.

Ils ne sont pas encore documentés pour un usage tiers, ni stabilisés : ils
changent au fil du chantier. Ce dépôt existe pour ne pas les mêler au dépôt
communautaire tant qu'ils n'ont pas de forme figée.

- `bin/proxies.sh` : vignettes fil de fer / zone des proxies.
- `bin/poitrine.sh`, `bin/asymthumbs.sh`, `bin/breastthumbs.sh` : vignettes de
  cibles (destinées à une PR sur `mpfb2`, pas à `asset_packs_staging`).
- `bin/rendertargetthumbs.py` : le moteur de rendu des cibles.
- `bin/vignettes-presets.sh` : réglages nommés (éclairage, trait…).
- `bin/composesplit.py`, `bin/composediptyque.py`, `bin/drawoutline.py`,
  `bin/outlineoverlay.py`, `bin/keyline.py` : composition et traçage des
  vignettes.
- `bin/thumbnail-vocabulary.md`, `bin/vignettes-vocabulaire.md` : le nom de
  chaque effet/vue/éclairage.
