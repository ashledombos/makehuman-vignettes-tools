#!/bin/sh
# La famille poitrine : six vignettes, recette arretee le 05-09-2026.
# Les reglages sont NOMMES dans bin/vignettes-presets.sh, qui porte aussi
# la raison et la mesure de chacun. Ce fichier ne fait que les citer.
#
#   sh bin/poitrine.sh      (a jouer sur soleil, ou le studio est installe)

# ⚠ LES DEUX CHEMINS SE SURCHARGENT, et c'est ce qui rend la recette
# verifiable : `ATELIER=/tmp/neuf sh bin/poitrine.sh clair` rejoue la famille
# ailleurs, donc on peut prouver qu'un dossier neuf redonne les memes pixels.
# Un chemin en dur ne se teste pas, il se croit.
#   ATELIER  le dossier de travail : bin/, studio_base.blend, vignettes/
#   CIBLES   les .target.gz de poitrine, dans l'extension MPFB installee
A=${ATELIER:-/var/home/soleil/travail-makehuman}
. $A/bin/vignettes-presets.sh
MATIERE=${1:-gris}
SUFFIXE=""
[ "$MATIERE" = clair ] && SUFFIXE="-clair"
TB=${CIBLES:-$HOME/.var/app/org.blender.Blender/config/blender/5.2/extensions/user_default/mpfb/data/targets/breast}

rendre() {   # nom | cibleA | cibleB | vue | largeur | eclairage | peau | extra
    OUT=$A/vignettes/$1$SUFFIXE
    mkdir -p "$OUT"
    case "$6" in
        face)   L="$LUM_FACE";   M=$MONDE_FACE ;;
        *)      L="$LUM_PROFIL"; M=$MONDE_PROFIL ;;
    esac
    # ⭐ Deux conventions de matiere, 13-09-2026. Sans argument, le gris du
    # studio, celui des six vignettes que Joel a validees le 08-09. Avec
    # `porcelaine` en premier argument du script, la matiere claire des
    # proxies, pour que les deux familles sortent du meme studio.
    # ⚠ Les angles, cadrages et eclairages ne changent PAS : ils sont valides.
    if [ "$MATIERE" = clair ]; then
        case "$7" in
            grosplan) P="$PEAU_CLAIRE_GROS_PLAN" ;;
            *)        P="$PEAU_CLAIRE" ;;
        esac
    else
        case "$7" in
            grosplan) P="$PEAU_GROS_PLAN" ;;
            *)        P="$PEAU_GRISE" ;;
        esac
    fi
    flatpak run --command=blender org.blender.Blender -b $A/studio_base.blend \
        -P $A/bin/rendertargetthumbs.py -- \
        --target $TB/$2.target.gz --target $TB/$3.target.gz \
        $COMMUN $4 --width $5 --lights "$L" --world $M \
        --skin-tune "$P" --zone-tune "$ZONE_AREOLE" \
        --amounts 1.0 $8 --out "$OUT" > "$OUT/rendu.log" 2>&1
    echo "$1 fait"
}

# --- « la paire », coupe horizontale ---------------------------------------
rendre ecartement  breast-dist-decr  breast-dist-incr  "$VUE_PAIRE" 0.26 face peau --after-only
rendre areole      nipple-size-decr  nipple-size-incr  "$VUE_PAIRE" 0.26 face peau --after-only
# ⚠ La saillie est une JUMELLE de l'areole a 120 px (distance 9,2 contre 17,1
# pour la paire suivante). Arbitrage de Raphael : la coherence de vue prime.
# Variante distincte si l'on revient dessus : gros plan de profil au double
# trait, azimut 90, carre 0,09 m, --one-side --far-side --aim geo.
rendre saillie     nipple-point-decr nipple-point-incr "$VUE_PAIRE" 0.26 face peau --after-only

# --- « la silhouette », coupe verticale -------------------------------------
rendre pointe      breast-point-decr breast-point-incr "$VUE_SILHOUETTE" 0.15 profil peau --after-only
rendre hauteur     breast-trans-down breast-trans-up   "$VUE_SILHOUETTE" 0.20 profil peau --after-only

# --- « le gros plan », double trait -----------------------------------------
# ⚠ Sans --after-only : le trait a besoin de l'etat MEDIAN en plus des bouts.
rendre repartition breast-volume-vert-down breast-volume-vert-up "$VUE_GROS_PLAN" 0.20 profil peau ""

# --- l'assemblage ------------------------------------------------------------
# Les rendus ci-dessus sont les BOUTS, pas les vignettes. La composition est un
# script a part, qui ne demande pas Blender et se rejoue en deux secondes ;
# il est appele ici pour qu'un seul geste produise toujours la famille entiere.
ATELIER=$A sh $A/bin/assembler-poitrine.sh "$MATIERE"
echo POITRINE-FINI
