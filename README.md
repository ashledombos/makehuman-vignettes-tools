# Outils de rendu des vignettes MakeHuman / MPFB2

Scripts personnels qui produisent les vignettes de **cibles** (les curseurs de
MPFB : poitrine, asym) et d'**assets** (les proxies de
`makehumancommunity/asset_packs_staging`). Tout tourne en Blender headless.

Ils ne sont pas stabilisés pour un usage tiers : ce dépôt existe pour ne pas les
mêler au dépôt communautaire tant qu'ils changent.

## Par où commencer

**`docs/specification-vignettes.md` fait foi.** C'est la table de décision : à
quoi sert chaque dispositif, quel éclairage pour quel angle, quel cadrage pour
quel sujet, et la règle qui choisit. Les valeurs y portent toutes un **nom**
(« la paire », « le liseré », « le porcelaine », « le double trait »), et une
recette se relit en citant ces noms plutôt qu'en rouvrant le script.

`docs/planches/` montre le résultat sur les 29 proxies des deux paquets, avec un
README en anglais qui explique la logique des trois régimes.

## Les deux recettes exécutables

```sh
# Les proxies : mesurer d'abord, le classement ne se devine pas.
sh bin/proxies-v2.sh <pack> mesurer
sh bin/proxies-v2.sh <pack> {global|local|disperse} [assets…]

# La famille poitrine : six curseurs, six vignettes, un geste.
ATELIER=… CIBLES=… sh bin/poitrine.sh clair
ATELIER=… sh bin/assembler-poitrine.sh clair   # l'assemblage seul, sans GPU
```

Détail de la poitrine au §2.9 de la spécification, des proxies au §2.7.

## Prérequis

| il faut | pourquoi |
|---|---|
| Blender 5.2 headless | le moteur de rendu |
| l'extension MPFB installée | les `.target.gz` et le maillage de base, qui n'ont pas leur place ici |
| `studio_base.blend` | le studio : deux jeux de lampes autour d'une empty visée, 200 mm à 4,12 m. Binaire, donc hors dépôt |
| ImageMagick | toute la composition (coupe, trait, fond noir) |

`ATELIER` désigne le dossier qui contient `bin/`, `studio_base.blend` et
`vignettes/` ; `CIBLES` le dossier des `.target.gz` dans l'extension installée.
Les deux ont une valeur par défaut qui pointe vers la machine de travail.

## Reproductibilité

**Mesurée le 13-09-2026 sur la famille poitrine**, en rejouant depuis ce dépôt
seul, dans un `ATELIER` neuf, et en comparant les pixels aux vignettes validées.
La colonne témoin rejoue la même chose avec **un degré d'azimut** d'écart : elle
ne prouve rien sur la recette, elle prouve que le test est assez **sensible**
pour que la première colonne veuille dire quelque chose.

| vignette | rejouée depuis le dépôt | témoin, 1° d'azimut |
|---|---|---|
| `breast-dist-decr-incr` | 6 px | 55 936 px |
| `nipple-size-decr-incr` | 4 px | 59 073 px |
| `nipple-point-decr-incr` | 5 px | 60 453 px |
| `breast-point-decr-incr` | 3 px | 32 950 px |
| `breast-trans-down-up` | 23 px | 34 272 px |
| `breast-volume-vert-down-up` | 8 199 px | 34 999 px |

*Pixels différents sur les 65 536 d'une vignette de 256.*

⚠ **La répartition est la seule à bouger visiblement en compte**, et son écart
est pourtant invisible : l'amplitude moyenne vaut 0,066 sur 255 contre 8,16 pour
le témoin, soit 123 fois moins, et les deux images sont indiscernables à l'œil.
La cause est son grain de pores en gros plan (`pore_scale=6000`), que le
débruiteur ne retrouve pas à l'identique. Compter les pixels ne suffit donc pas :
il faut lire aussi l'amplitude.

🪤 **Ne pas comparer deux PNG par `sha256`** : ImageMagick écrit l'heure dans le
fichier, donc deux passes identiques sortent des sommes différentes pour zéro
pixel d'écart. Comparer les **pixels**.

## Inventaire

**Moteurs de rendu**
- `bin/rendertargetthumbs.py` : les cibles (curseurs).
- `bin/rendermeshthumbs.py` : les assets (proxies). ⚠ La copie du dépôt
  communautaire est celle de Joël et n'expose pas les mêmes options.

**Recettes**
- `bin/proxies-v2.sh` : les proxies, trois régimes, arrêtée le 13-09-2026.
- `bin/poitrine.sh` et `bin/assembler-poitrine.sh` : la famille poitrine.
- `bin/proxies.sh`, `bin/asymthumbs.sh`, `bin/breastthumbs.sh` : état antérieur,
  gardés pour la genèse. ⚠ `breastthumbs.sh` trace encore au vermillon et au
  bleu, couple écarté depuis pour cause de vision déficiente.

**Réglages**
- `bin/vignettes-presets.sh` : les réglages nommés, chacun avec sa raison et la
  mesure qui l'a départagé.
- `bin/thumbnail-vocabulary.md`, `bin/vignettes-vocabulaire.md` : le nom de
  chaque effet, vue et éclairage.

**Composition**
- `bin/composesplit.py` : la coupe, deux prises en un carré.
- `bin/outlineoverlay.py`, `bin/drawoutline.py`, `bin/keyline.py` : les tracés.
- `bin/composediptyque.py`, `bin/composer-diptyque-empile.py` : les diptyques.
- `bin/epaissir-zone.py` : épaissit une zone colorée dans l'image.
- `bin/composer-polyptyque.py` : essai consigné, non retenu.

**Mesures**
- `bin/mesurer.py` : contraste corps contre encre.
- `bin/daltonisme.py` : simulation des trois daltonismes. Une couleur se simule,
  elle ne se choisit pas à l'œil.
- `bin/morceaux.py` : les morceaux séparés d'un proxy.
