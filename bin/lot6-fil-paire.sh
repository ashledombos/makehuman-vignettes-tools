#!/bin/sh
# Tache fil de fer sur les DEUX etats, generique (17-10-2026, tire de
# lot6-teton-homme-fil.sh). Passage 1 : etat modifie, visee mesuree sur un
# seul cote (--one-side --aim geo) ou imposee par VISEE ; passage 2 : neutre a
# la visee relevee, sans --refine. Prise carree 1024 rognee en prise debout,
# diptyque vertical 512x512, neutre a gauche.
#   FAMILLE=face04 AZ="90 25" LARGEUR=0.14 [QUI=female] [VISEE=x,y,z] [SORTIE=nom] \
#     sh bin/lot6-fil-paire.sh cible...
# Une largeur par cible : cible:largeur.
# SEUL=1 : etat modifie seul (changement evident), un seul passage, ni neutre ni
# composesplit ; prise carree entiere 512x512, sortie $O/cible-azNN.png.
# VISOPT remplace la visee mesuree (ex. "--refine" pour une zone sur l axe) ;
# XRAY=noir : corps en fil occulte par une peau noire + conduit en transparence. MOITIE=1 (avec XRAY=ghost) ne garde du corps que la moitie cote camera ; XRAY=1 ajoute en pourpre les mailles cachees (cibles deep, avec FIT) ; PILE=h empile deux prises couchees ; FIT=chemin.proxy ajuste un proxy (cibles d anatomie) ; EXTRA, options en plus.
A=/var/home/soleil/travail-makehuman
. $A/bin/vignettes-presets.sh
CIB=$A/cibles-communaute/$FAMILLE
O=$A/vignettes/lot6-${SORTIE:-$FAMILLE}-fil
COM=$(echo "$COMMUN" | sed "s/--size 256/--size 1024/; s/--who female/--who ${QUI:-female}/; s/--refine//")
BLEU="#0072B2"; POURPRE="#CC79A7"; CIEL="#56B4E9"
# FLECHE=" " garde la fleche (cible a sens unique, neutre vers 1). PILE=h : prises couchees empilees (neutre en haut), sinon prises debout cote a cote.
if [ "$PILE" = h ]; then ROGNE=100%x50%; DEMI=512x256; AXE=horizontal; else ROGNE=50%x100%; DEMI=256x512; AXE=vertical; fi
[ -n "$SEUL" ] && { ROGNE=100%x100%; DEMI=512x512; }
RG=--region-graded; [ -n "$BINAIRE" ] && RG=""  # BINAIRE=1 : pochoir plein, sans degrade (pied entier qui bouge)
VIS="${VISOPT:---refine --one-side --aim geo}"; [ -n "$VISEE" ] && VIS="--look-at=$VISEE"
habiller() {  # entree fil region sortie
    for f in "$1" "$2" "$3"; do cp "$f" _in.png; magick _in.png -gravity center -crop $ROGNE+0+0 +repage "_r-$(basename $f)"; done
    magick "_r-$(basename $2)" -colorspace gray -resize $DEMI! _f.png
    magick "_r-$(basename $3)" -background black -alpha remove -alpha off -colorspace gray -resize $DEMI! _z.png
    magick _f.png _z.png -compose multiply -composite _fz.png
    magick "_r-$(basename $1)" -background black -alpha remove -alpha off -resize $DEMI! _c.png
    magick _c.png \( _c.png -fill "$BLEU" -colorize 100 \) _fz.png -alpha off -composite $4
    # XRAY=1 : les mailles CACHEES de la zone deplacee (passe --wire-xray), en
    # pourpre, moins ce que le fil ordinaire montre deja (dilate de 2 px).
    # XRAY=ghost : tout en fil de fer, sans peau. Le proxy entier en gris
    # faible, transparent, et la zone deplacee entiere en couleur vive.
    # XRAY=noir : comme ghost, mais le corps en fil de fer OCCULTE par une
    # peau noire (passe --wire ordinaire, $2) au lieu d'une coupe : on ne voit
    # que les mailles du cote camera, sans bord de coupe. Le conduit reste en
    # transparence par-dessus.
    if [ "$XRAY" = noir ] && [ -f "$5" ]; then
        cp "$2" _in.png; magick _in.png -gravity center -crop $ROGNE+0+0 +repage -background black -alpha remove -alpha off -colorspace gray -resize $DEMI! -evaluate multiply 0.45 _g.png
        cp "$5" _in.png; magick _in.png -gravity center -crop $ROGNE+0+0 +repage -background black -alpha remove -alpha off -colorspace gray -resize $DEMI! _x.png
        magick _g.png -colorspace sRGB \( -size $DEMI xc:"$CIEL" \) _x.png -composite $4
        return
    fi
    if [ "$XRAY" = ghost ] && [ -f "$5" ]; then
        g=$(echo "$5" | sed s/-xray.png/-ghost.png/)
        cp "$g" _in.png; magick _in.png -gravity center -crop $ROGNE+0+0 +repage -background black -alpha remove -alpha off -colorspace gray -resize $DEMI! -evaluate multiply 0.45 _g.png
        cp "$5" _in.png; magick _in.png -gravity center -crop $ROGNE+0+0 +repage -background black -alpha remove -alpha off -colorspace gray -resize $DEMI! _x.png
        magick _g.png -colorspace sRGB \( -size $DEMI xc:"$CIEL" \) _x.png -composite $4
        return
    fi
    if [ -n "$XRAY" ] && [ -f "$5" ]; then
        cp "$5" _in.png; magick _in.png -gravity center -crop $ROGNE+0+0 +repage -background black -alpha remove -alpha off -colorspace gray -resize $DEMI! _x.png
        magick _f.png -morphology Dilate Disk:2 -negate _fn.png
        magick _x.png _fn.png -compose multiply -composite _h.png
        magick $4 \( $4 -fill "$POURPRE" -colorize 100 \) _h.png -alpha off -composite $4
    fi
}
for arg in "$@"; do
  c=${arg%%:*}; W=${LARGEUR:-0.14}; [ "$arg" != "$c" ] && W=${arg#*:}
  EP=$(python3 -c "print(f'{0.00016*$W/0.048:.6f}')"); [ "$XRAY" = ghost -o "$XRAY" = noir ] && EP=$(python3 -c "print(f'{0.00008*$W/0.048:.6f}')")
  for az in ${AZ:-90}; do
    if [ $az -lt 60 ]; then L="$LUM_FACE"; M=$MONDE_FACE; else L="$LUM_PROFIL"; M=$MONDE_PROFIL; fi
    D=$O/$c/az$az; rm -rf $D; mkdir -p $D/neutre
    flatpak run --command=blender org.blender.Blender -b $A/studio_base.blend \
      -P $A/bin/rendertargetthumbs.py -- --target $CIB/$c.target $COM $VIS ${FIT:+--fit $FIT} $EXTRA \
      --azimuth $az --width $W --lights "$L" --world $M \
      --skin-tune "$PEAU_CLAIRE_GROS_PLAN" --amounts 1.0 --after-only \
      --wire ${XRAY:+--wire-xray} ${MOITIE:+--wire-ghost-half} --wire-thickness $EP --region $RG --out $D > $D/rendu.log 2>&1
    LA=$(grep -o 'look_at=\[[^]]*\]' $D/rendu.log | tail -1 | tr -d '[] ' | sed 's/look_at=//')
    [ -n "$LA" ] || { echo "ECHEC $c az$az (passage 1)"; continue; }
    if [ -n "$SEUL" ]; then
      cd $D
      [ -f $c-fil.png ] || { echo "ECHEC $c az$az"; continue; }
      habiller $c.png $c-fil.png $c-region.png $O/$c-az$az.png $c-xray.png
      magick $O/$c-az$az.png -background black -alpha remove -alpha off $O/$c-az$az.png
      echo "$c az$az fait (seul), visee $LA, largeur $W"
      continue
    fi
    flatpak run --command=blender org.blender.Blender -b $A/studio_base.blend \
      -P $A/bin/rendertargetthumbs.py -- --target $CIB/$c.target $COM \
      --look-at=$LA ${FIT:+--fit $FIT} $EXTRA --azimuth $az --width $W --lights "$L" --world $M \
      --skin-tune "$PEAU_CLAIRE_GROS_PLAN" --amounts 0.0001 --after-only \
      --wire ${XRAY:+--wire-xray} ${MOITIE:+--wire-ghost-half} --wire-thickness $EP --region $RG --out $D/neutre > $D/neutre/rendu.log 2>&1
    for f in $D/neutre/$c@0*; do [ -f "$f" ] && mv "$f" "$(echo $f | sed s/@0//)"; done
    cd $D
    [ -f $c-fil.png ] && [ -f neutre/$c-fil.png ] || { echo "ECHEC $c az$az"; continue; }
    habiller neutre/$c.png neutre/$c-fil.png neutre/$c-region.png T-a.png neutre/$c-xray.png
    habiller $c.png $c-fil.png $c-region.png T-b.png $c-xray.png
    python3 $A/bin/composesplit.py --stack --axis $AXE ${FLECHE:---no-arrow} T-a.png T-b.png $O/$c-az$az.png > /dev/null
    magick $O/$c-az$az.png -background black -alpha remove -alpha off $O/$c-az$az.png
    B=$(magick _r-$c-region.png -background black -alpha remove -alpha off -colorspace gray -threshold 5% -format '%@ sur %wx%h' info:)
    echo "$c az$az fait, visee $LA, largeur $W, boite $B"
  done
done
echo FIL-PAIRE-FINI
