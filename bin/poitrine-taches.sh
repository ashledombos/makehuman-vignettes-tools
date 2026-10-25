#!/bin/sh
# Essai : la tache bleue des vignettes d'asymetrie, posee sur la famille
# POITRINE sans rien changer d'autre. Meme pose, meme eclairage, meme peau,
# meme decoupe en deux moitiees : on ajoute seulement la zone que la cible
# deplace, peinte par-dessus chaque bout avant l'assemblage.
A=/var/home/soleil/travail-makehuman
. $A/bin/vignettes-presets.sh
TB=$HOME/.var/app/org.blender.Blender/config/blender/5.2/extensions/user_default/mpfb/data/targets/breast
O=$A/essai-poitrine-taches; rm -rf $O; mkdir -p $O; LOG=$O/rendu.log
BLEU="#0072B2"

rendre() {  # dossier | cibleA | cibleB | vue | largeur | eclairage
    mkdir -p "$O/$1"
    case "$6" in
        face) L="$LUM_FACE"; M=$MONDE_FACE ;;
        *)    L="$LUM_PROFIL"; M=$MONDE_PROFIL ;;
    esac
    flatpak run --command=blender org.blender.Blender -b $A/studio_base.blend \
        -P $A/bin/rendertargetthumbs.py -- \
        --target $TB/$2.target.gz --target $TB/$3.target.gz \
        $COMMUN $4 --width $5 --lights "$L" --world $M \
        --skin-tune "$PEAU_GRISE" --zone-tune "$ZONE_AREOLE" \
        --region --region-graded --amounts 1.0 --after-only \
        --out "$O/$1" >> $LOG 2>&1
}

# La tache, posee comme sur les asym : la couleur garde la luminance du corps
# puis la zone est assombrie d'un cinquieme.
teinter() {  # image | masque | sortie
    magick "$1" -background black -alpha remove -alpha off $O/_b.png
    magick $O/_b.png -fill "$BLEU" -colorize 100 $O/_a.png
    magick $O/_b.png $O/_a.png -compose Colorize -composite \
        -evaluate multiply 0.78 $O/_col.png
    magick $O/_b.png $O/_col.png "$2" -alpha off -composite "$3"
}

assembler() {  # dossier | cibleA | cibleB | axe | nom
    d=$O/$1
    teinter "$d/$2.png" "$d/$2-region.png" "$d/T-$2.png"
    teinter "$d/$3.png" "$d/$3-region.png" "$d/T-$3.png"
    python3 $A/bin/composesplit.py "$d/T-$2.png" "$d/T-$3.png" \
        "$O/$5.png" --axis "$4" --stack >> $LOG 2>&1
    magick "$O/$5.png" -background black -alpha remove -alpha off "$O/$5.png"
    echo "$5 fait"
}

# --- « la paire », coupe horizontale ---------------------------------------
rendre ecartement breast-dist-decr breast-dist-incr "$VUE_PAIRE" 0.26 face
assembler ecartement breast-dist-decr breast-dist-incr horizontal breast-dist-decr-incr
rendre areole nipple-size-decr nipple-size-incr "$VUE_PAIRE" 0.26 face
assembler areole nipple-size-decr nipple-size-incr horizontal nipple-size-decr-incr
rendre saillie nipple-point-decr nipple-point-incr "$VUE_PAIRE" 0.26 face
assembler saillie nipple-point-decr nipple-point-incr horizontal nipple-point-decr-incr

# --- « la silhouette », coupe verticale -------------------------------------
rendre pointe breast-point-decr breast-point-incr "$VUE_SILHOUETTE" 0.15 profil
assembler pointe breast-point-decr breast-point-incr vertical breast-point-decr-incr
rendre hauteur breast-trans-down breast-trans-up "$VUE_SILHOUETTE" 0.20 profil
assembler hauteur breast-trans-down breast-trans-up vertical breast-trans-down-up

# --- « le gros plan » : la sixieme portait un double TRAIT, pas une coupe.
# Ici la tache remplace le trait, donc elle se pose comme les cinq autres.
rendre repartition breast-volume-vert-down breast-volume-vert-up "$VUE_GROS_PLAN --portrait" 0.20 profil
assembler repartition breast-volume-vert-down breast-volume-vert-up vertical breast-volume-vert-down-up

magick montage -label '%t' $O/breast-*.png $O/nipple-*.png -tile 3x2 \
  -geometry 240x240+5+5 -background '#222' -fill white -pointsize 11 $O/planche.png

ls -la $O/*.png
echo POITRINE-TACHES-FINI
