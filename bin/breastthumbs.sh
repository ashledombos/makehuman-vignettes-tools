#!/usr/bin/env bash
#
# Produit les vignettes des quatre curseurs de poitrine de MPFB, dans la
# convention arbitrée le 04-09.
#
# Deux recettes, et l'angle décide :
#
#   - volume, pointe et hauteur se lisent **en silhouette**, donc de profil, et
#     l'on y trace les deux contours, vermillon pour le bout haut et bleu pour
#     le bout bas, sur l'état moyen ;
#   - l'écartement ne se lit **que de face**, où le sein n'a aucun contour :
#     ses normales ne deviennent jamais perpendiculaires au regard, donc il n'y
#     a de ligne ni dans l'alpha, ni dans l'ombrage, ni dans les normales. On
#     revient là à la coupe, deux prises couchées empilées entre les deux bouts
#     du curseur.
#
# Trois tentatives de tracé de face ont été mesurées et écartées avant d'en
# venir là : le bord du canal alpha ne dessine que le bras, un contour cherché
# dans l'ombrage ne rend que des tirets épars, et le bord de la région déplacée
# cerne une aire bien plus large que le sein.
#
# ⚠ Les cibles de poitrine se rendent sur le corps **féminin** du studio. Sur
# le corps neutre, une cible qui déplace un sein n'a presque rien à déplacer :
# l'écart se mesure mais ne se lit pas.

set -u
ATELIER=${ATELIER:-/var/home/soleil/travail-makehuman}
CIBLES=${CIBLES:-$HOME/.var/app/org.blender.Blender/config/blender/5.2/extensions/user_default/mpfb/data/targets/breast}
SORTIE=${SORTIE:-$ATELIER/vignettes-cibles/breast}
ECHANTILLONS=${ECHANTILLONS:-640}

VERMILLON="#D55E00"
BLEU="#0072B2"

# curseur:bas:haut:angle:largeur
PROFIL="volume-vert:down:up point:decr:incr trans:down:up"
LARGEUR_PROFIL=0.36

mkdir -p "$SORTIE"

rendre() {
    local sortie=$1 azimut=$2 largeur=$3 format=$4
    shift 4
    flatpak run --command=blender org.blender.Blender -b \
        "$ATELIER/studio_base.blend" -P "$ATELIER/bin/rendertargetthumbs.py" -- \
        "$@" --who female --size 256 $format --width "$largeur" \
        --azimuth "$azimut" --refine --on-axis --amounts 0.0,1.0 \
        --after-only --out "$sortie" --samples "$ECHANTILLONS" >/dev/null 2>&1
}

for entree in $PROFIL; do
    curseur=${entree%%:*}; reste=${entree#*:}
    bas=${reste%%:*}; haut=${reste#*:}
    travail="$SORTIE/.$curseur"; mkdir -p "$travail"
    rendre "$travail" 90 "$LARGEUR_PROFIL" "" \
        --target "$CIBLES/breast-$curseur-$bas.target.gz" \
        --target "$CIBLES/breast-$curseur-$haut.target.gz"
    python3 "$ATELIER/bin/outlineoverlay.py" \
        "$travail/breast-$curseur-$haut@0.png" \
        "$travail/breast-$curseur-$haut@100.png" \
        "$SORTIE/breast-$curseur-$bas-$haut.png" \
        --also "$travail/breast-$curseur-$bas@100.png" \
        --width 3 --colour "$VERMILLON" --colour2 "$BLEU" >/dev/null
    echo "profil  breast-$curseur-$bas-$haut"
done

# L'écartement, de face, en coupe. Trois-quarts à 35° : la mesure préférait le
# frontal pour l'écartement seul, mais l'angle garde le galbe lisible et c'est
# lui qui a été retenu sur planche.
travail="$SORTIE/.dist"; mkdir -p "$travail"
rendre "$travail" 35 0.36 "--rect" \
    --target "$CIBLES/breast-dist-decr.target.gz" \
    --target "$CIBLES/breast-dist-incr.target.gz"
python3 "$ATELIER/bin/composesplit.py" \
    "$travail/breast-dist-decr@100.png" \
    "$travail/breast-dist-incr@100.png" \
    "$SORTIE/breast-dist-decr-incr.png" --axis horizontal --stack >/dev/null
echo "coupe   breast-dist-decr-incr"
echo "TERMINE, vignettes dans $SORTIE"
