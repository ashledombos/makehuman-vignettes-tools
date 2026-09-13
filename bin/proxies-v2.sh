#!/bin/sh
# Les vignettes de proxies, formule arretee le 13-09-2026 et validee a l'oeil
# par Raphael sur planche. Detail et mesures : makehuman-vignettes-CANON.md,
# section 1.23. Planches : makehuman-planches-2026-09-13/.
#
#   sh proxies-v2.sh <pack> mesurer          # les trois nombres, sans rendre
#   sh proxies-v2.sh <pack> global  [assets] # neufs > 90 %
#   sh proxies-v2.sh <pack> local   [assets] # etendue < 35 %
#   sh proxies-v2.sh <pack> disperse [assets] # ni l'un ni l'autre
#
# ⚠⚠ LE CLASSEMENT NE SE DEVINE PAS : lancer `mesurer` d'abord et lire la
#    ligne « -- ZONES » de chaque asset, qui donne neufs / grappes / etendue et
#    conclut GLOBAL, LOCAL ou DISPERSE. Un proxy PARTIEL (qui retire de la
#    geometrie) fait exception avant tout classement : ses sommets neufs sont
#    le BORD DE COUPE, pas son travail.
#
# Le decor est commun aux trois, et chaque valeur est payee d'une mesure :
#   --albedo 0.92   corps porcelaine a 216/255, zero pixel brule
#   --exposure 0.7  le corps monte a 216 ET l'ecart du low poly monte aussi
#   la face          bat le lisere sur fond noir, corps 198 contre 158
#   --azimuth 34    ⚠⚠ POSITIF = regard a gauche SUR CE SCRIPT, l'inverse de
#                   rendertargetthumbs.py. Verifie a l'oeil, jamais recopie
#   --true-edges    ⚠⚠ SANS LUI le noeud Wireframe triangule les quads
#   encre_bleue     une seule couleur pour tout ce qui parle du maillage
#
# ⚠ Le rendu sort avec un fond TRANSPARENT ; l'aplatir sur noir a la livraison
#   (convert x.png -background black -alpha remove -alpha off y.png), le fond
#   noir opaque etant la convention arretee le 12-09.
# 🪤 Rendre en parallele epuise la carte de clairdelune : « Out of memory in
#   CUDA queue ». En serie, toujours.
set -e
A=/var/home/soleil/travail-makehuman/staging
PACK=${1:?pack attendu, par exemple proxies01_cc0}
MODE=${2:?mode attendu : mesurer, global, local ou disperse}
shift 2
OUT=${OUT:-/var/home/soleil/travail-makehuman/vignettes/$PACK-$MODE}
LUM="key=1.1,fill=0.9,rim=4.0,spot=0.05"
COMMUN="--force --samples 192 --subdiv 0 --albedo 0.92 --exposure 0.7 \
--azimuth 34 --lights $LUM --world 0.55"

case "$MODE" in
mesurer)
    # ⚠ --force est indispensable : sans lui les assets deja rendus sont
    # sautes et la mesure ne sort pour personne.
    flatpak run --command=blender org.blender.Blender -b \
        $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" --force --measure-only "$@"
    ;;
global)
    # Tout le maillage en bleu, cadre sur la tete et les epaules.
    mkdir -p "$OUT"
    flatpak run --command=blender org.blender.Blender -b \
        $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" $COMMUN \
        --flat --grey --true-edges --wire-colour encre_bleue \
        --top 0.20 --out "$OUT" "$@"
    ;;
local)
    # Fil BICOLORE : le maillage en gris clair 0,85, la seule zone
    # retravaillee en bleu, zoom maximal dessus.
    # ⚠ Le gris doit etre CLAIR : un fil sombre fait ressortir tout le
    #   maillage et l'oeil ne va nulle part.
    # ⚠ --margin 1.3 est le zoom maximal demande ; sans lui la marge
    #   automatique plafonne a 2,2, ce qui garde plus de contexte.
    mkdir -p "$OUT"
    flatpak run --command=blender org.blender.Blender -b \
        $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" $COMMUN \
        --flat --grey --true-edges --wire-colour encre_bleue \
        --frame-new --margin 1.3 --out "$OUT" "$@"
    ;;
disperse)
    # La zone en aplat du MEME bleu, cadre sur l'enveloppe des zones avec une
    # marge relative a leur etendue.
    mkdir -p "$OUT"
    flatpak run --command=blender org.blender.Blender -b \
        $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" $COMMUN \
        --paint-new --highlight encre_bleue --out "$OUT" "$@"
    ;;
*)
    echo "mode inconnu : $MODE (mesurer, global, local, disperse)" >&2
    exit 1
    ;;
esac
