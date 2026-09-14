#!/bin/sh
# L'assemblage de la famille poitrine : six carres de 256, a partir des deux
# bouts que `poitrine.sh` rend separement.
#
#   sh bin/assembler-poitrine.sh clair    (ou sans argument pour l'ancien gris)
#
# ⭐ POURQUOI UN SCRIPT A PART. Le rendu demande Blender et des minutes ; la
# composition ne demande qu'ImageMagick et deux secondes. Les separer permet de
# rejouer un trait ou une couleur sans repasser par le GPU. `poitrine.sh`
# appelle celui-ci a la fin, donc un seul geste produit toujours la famille.
#
# ⚠ LES NOMS DE SORTIE SONT CEUX DE MPFB, pas les noms de travail : une image
# de curseur s'appelle `<cible-basse>-<suffixe-haut>.png` et vit dans
# `data/targets/_images/`. Verifie contre les 216 images de l'extension
# installee le 13-09-2026 ; six des noms ci-dessous y existent deja.

# ⚠ `ATELIER` surcharge le dossier de travail, comme dans `poitrine.sh` : c'est
# ce qui permet de rejouer l'assemblage dans un dossier neuf et de comparer les
# pixels aux vignettes validees.
A=${ATELIER:-/var/home/soleil/travail-makehuman}
. $A/bin/vignettes-presets.sh
MATIERE=${1:-gris}
SUFFIXE=""
[ "$MATIERE" = clair ] && SUFFIXE="-clair"
V=$A/vignettes
OUT=$V/poitrine-final$SUFFIXE
TRAVAIL=$OUT/.travail
mkdir -p "$TRAVAIL"

# ⚠⚠ Le rendu sort avec un fond TRANSPARENT ; le fond noir OPAQUE est la
# convention arretee le 12-09, et il s'applique a la LIVRAISON, apres le trace.
# L'aplatir plus tot ne changerait pas l'image mais ferait mentir les scripts
# de trace, qui cherchent leur region dans la difference des deux etats.
#
# 🪤 ImageMagick ecrit L'HEURE dans chaque PNG. Deux passes identiques sortent
# donc des fichiers de sha256 differents alors que les pixels sont les memes :
# une comparaison par somme de controle y voit une regression qui n'existe pas,
# et un depot git enregistre un diff a chaque regeneration. Les deux `+set`
# retirent ces champs ; la verification d'egalite, elle, se fait sur les
# PIXELS (`compare -metric AE`), jamais sur la somme du fichier.
noircir() {   # entree | sortie
    magick "$1" -background black -alpha remove -alpha off \
        +set date:create +set date:modify +set date:timestamp "$2"
}

# --- les cinq coupes --------------------------------------------------------
#
# ⚠ Le format de la prise commande l'axe : une prise couchee (256x128) s'empile
# en coupe horizontale, une prise debout (128x256) se pose en coupe verticale.
# `composesplit.py` refuse la combinaison inverse plutot que de sortir un
# 128x512, mais autant ne pas l'y amener.
coupe() {     # dossier | avant | apres | axe | nom livre
    python3 $A/bin/composesplit.py \
        "$V/$1$SUFFIXE/$2.png" "$V/$1$SUFFIXE/$3.png" \
        "$TRAVAIL/$5.png" --axis "$4" --stack > /dev/null
    noircir "$TRAVAIL/$5.png" "$OUT/$5.png"
    echo "coupe   $5"
}

coupe ecartement breast-dist-decr  breast-dist-incr  horizontal breast-dist-decr-incr
coupe areole     nipple-size-decr  nipple-size-incr  horizontal nipple-size-decr-incr
coupe saillie    nipple-point-decr nipple-point-incr horizontal nipple-point-decr-incr
coupe pointe     breast-point-decr breast-point-incr vertical   breast-point-decr-incr
coupe hauteur    breast-trans-down breast-trans-up   vertical   breast-trans-down-up

# --- la repartition, au double trait ----------------------------------------
#
# Le changement est INTERIEUR a la silhouette : deux moities se ressembleraient.
# On montre donc l'etat median en dur et les deux bouts en pointilles par
# dessus, chaud pour le haut, froid pour le bas.
#
# ⚠ L'etat median vient du rendu SANS `--after-only` : c'est le fichier
# `-before`, celui de l'amplitude 0. Les deux `-before` sont identiques, l'un
# ou l'autre fait l'affaire.
#
# ⚠ Les couleurs sont celles de `vignettes-presets.sh`, Okabe-Ito, et non le
# vermillon et le bleu de `breastthumbs.sh` : le couple vermillon/bleu se
# referme en vision deficiente, c'est ce qui l'a fait remplacer.
R=$V/repartition$SUFFIXE
python3 $A/bin/outlineoverlay.py \
    "$R/breast-volume-vert-up-before.png" \
    "$R/breast-volume-vert-up.png" \
    "$TRAVAIL/breast-volume-vert-down-up.png" \
    --also "$R/breast-volume-vert-down.png" \
    --width $TRAIT_EPAISSEUR \
    --colour "$TRAIT_CHAUD" --colour2 "$TRAIT_FROID" > /dev/null
noircir "$TRAVAIL/breast-volume-vert-down-up.png" \
        "$OUT/breast-volume-vert-down-up.png"
echo "trait   breast-volume-vert-down-up"

echo "ASSEMBLAGE-FINI, six vignettes dans $OUT"
