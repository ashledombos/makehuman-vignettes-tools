#!/bin/bash
# Les 31 curseurs d'asymetrie, convention v4, arretee par Raphael le 16-09-2026.
#
# Vue de FACE, cadre serre tenant les deux instances du trait, aucun contour,
# et une amplitude DOSEE PAR FAMILLE : une asymetrie se lit par comparaison
# interne, et a 1,0 le deplacement fait un ou deux millimetres, invisibles.
#   x3   traits fins (sourcil, tempe, sommet du crane)
#   x1.5 yeux, qui se deforment vite et donnent une paupiere abimee a x3
#   x2   tout le reste
#
# ⚠ Quatre visees sont IMPOSEES : la sonde --refine remonte sur le front et
# sortait un dome nu sans repere. Leurs valeurs viennent du journal de la
# sonde (framing.json), abaissees pour faire entrer un repere dans le cadre.
# ⚠⚠ Le repere de --look-at n'est PAS celui de matrix_world : l'oeil y est a
# z=1.488 quand la mesure du maillage dit 1.563, sept centimetres plus haut.
# Une premiere reprise calee sur la mesure de sommets a sorti quatre images
# vides. Partir du journal de la sonde, jamais d'une mesure du maillage.
#
# ⚠ Le rendu sort avec son canal alpha : l'aplatir sur noir est une etape de
# LIVRAISON, pas une option du moteur. Cinquieme occurrence du meme defaut.
set -u
A=/var/home/soleil/travail-makehuman
. $A/bin/vignettes-presets.sh
C=${CIBLES:-$HOME/.var/app/org.blender.Blender/config/blender/5.2/extensions/user_default/mpfb/data/targets/asym}
OUT=${SORTIE:-$A/vignettes-cibles/asym-v4}
BRUT=$OUT/brut
mkdir -p "$BRUT"; LOG=$OUT/rendu.log

reglage_de() {   # curseur -> "largeur amplitude visee"  (visee vide = sonde)
    case "$1" in
        asym-brown-2) echo "0.14 3.0 0.0,-0.1049,1.515" ;;
        asym-nose-4)  echo "0.10 2.0 0.0,-0.1496,1.478" ;;
        asym-top-1)   echo "0.26 3.0 0.0,-0.0735,1.520" ;;
        asym-top-2)   echo "0.26 3.0 0.0,-0.0569,1.520" ;;
        *-brown-*)    echo "0.10 3.0 -" ;;
        *-temple-*)   echo "0.15 3.0 -" ;;
        *-top-*)      echo "0.16 3.0 -" ;;
        *-eye-*)      echo "0.11 1.5 -" ;;
        *-nose-*)     echo "0.06 2.0 -" ;;
        *-mouth-*)    echo "0.09 2.0 -" ;;
        *-cheek-*)    echo "0.13 2.0 -" ;;
        *-jaw-*)      echo "0.16 2.0 -" ;;
        *-ear-*)      echo "0.16 2.0 -" ;;
        *breast*)     echo "0.26 2.0 -" ;;
        *trunk*)      echo "0.40 2.0 -" ;;
        *)            echo "0.14 2.0 -" ;;
    esac
}

for curseur in $(ls "$C" | sed 's/\.target.*//' | sed 's/-[lr]$//' | sort -u); do
    read -r largeur amplitude visee <<< "$(reglage_de "$curseur")"
    [ -f "$OUT/$curseur-l-r.png" ] && continue
    if [ "$visee" = "-" ]; then CADRE="--refine"; else CADRE="--look-at $visee"; fi
    flatpak run --command=blender org.blender.Blender -b "$A/studio_base.blend" \
        -P "$A/bin/rendertargetthumbs.py" -- \
        --target "$C/$curseur-l.target.gz" \
        --who female --size 256 --hide-inner --fstop 0 --samples 512 \
        --width "$largeur" --azimuth 0 --on-axis $CADRE \
        --lights "$LUM_FACE" --world $MONDE_FACE --skin-tune "$PEAU_CLAIRE" \
        --amounts "$amplitude" --after-only --out "$BRUT" >> $LOG 2>&1
    # Le nom de sortie du moteur porte l'amplitude ; le nom livre est celui du
    # curseur, comme les 185 icones de MPFB.
    src=$(ls "$BRUT/$curseur-l@"*.png 2>/dev/null | head -1)
    if [ -n "$src" ]; then
        convert "$src" -background black -alpha remove -alpha off "$OUT/$curseur-l-r.png"
        echo "RENDU $curseur cadre $largeur x$amplitude visee $visee" >> $OUT/journal.log
    else
        echo "ECHEC $curseur" >> $OUT/journal.log
    fi
done

cd "$OUT"
opaques=$(identify -format '%[opaque]\n' *-l-r.png | grep -c True)
echo "OPACITE $opaques/$(ls *-l-r.png | wc -l)" >> journal.log
montage -label '%t' $(ls *-l-r.png | sort) -tile 6x6 -geometry 200x200+5+5 \
    -background '#222' -fill white -pointsize 12 planche-v4.png
echo "V4-FINI $(ls *-l-r.png | wc -l)" >> journal.log
