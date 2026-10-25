#!/bin/bash
# Planche de comparaison des TROIS dispositifs en lice pour les vignettes asym,
# sur six curseurs de six familles : trois ou la silhouette bouge (oreille,
# machoire, sommet du crane) et trois ou elle ne bouge pas (sourcil, paupiere,
# nez). Meme amplitude pour les trois dispositifs d'un meme curseur : la
# planche doit comparer des DISPOSITIFS, pas des dosages.
#
# D1 corps seul, amplitude etalonnee, eclairage symetrique (--mirror-lights)
# D2 les deux bouts, l'extreme -l en dur et l'extreme -r en pointilles bleus
# D3 la zone graduee, --region --region-graded, peinte sur le corps neutre
set -u
A=$A
. $A/bin/vignettes-presets.sh
C=$HOME/.var/app/org.blender.Blender/config/blender/5.2/extensions/user_default/mpfb/data/targets/asym
OUT=$A/essai-trois; rm -rf "$OUT"; mkdir -p "$OUT/brut"; LOG=$OUT/rendu.log; : > $LOG
: > $OUT/journal.log
BLEU="#0072B2"
LUM="key=0.55,fill=0.45,rim=2.0,spot=0.025"

cadre_de() { [ "$1" = "-" ] && echo "--refine" || echo "--look-at $1"; }

rendre() {  # curseur cote largeur amplitude visee extra...
  local curseur=$1 cote=$2 largeur=$3 amplitude=$4 visee=$5; shift 5
  flatpak run --command=blender org.blender.Blender -b "$A/studio_base.blend" \
    -P "$A/bin/rendertargetthumbs.py" -- \
    --target "$C/$curseur-$cote.target.gz" \
    --who female --size 256 --hide-inner --fstop 0 --samples 512 \
    --width "$largeur" --azimuth 0 --on-axis $(cadre_de "$visee") \
    --mirror-lights --lights "$LUM" --world $MONDE_FACE \
    --skin-tune "$PEAU_CLAIRE" --amounts "$amplitude" \
    "$@" --out "$OUT/brut" >> $LOG 2>&1
}

while read -r curseur largeur amplitude visee; do
  # --- D1 : le corps seul ---------------------------------------------------
  rendre "$curseur" l "$largeur" "$amplitude" "$visee" --after-only
  src=$(ls "$OUT/brut/$curseur-l@"*.png 2>/dev/null | head -1)
  [ -n "$src" ] \
    && magick "$src" -background black -alpha remove -alpha off "$OUT/D1-$curseur.png" \
    && echo "D1 $curseur x$amplitude" >> $OUT/journal.log \
    || echo "D1 ECHEC $curseur" >> $OUT/journal.log
  rm -f "$OUT/brut/$curseur-l@"*.png

  # --- D3 : la zone graduee (rend aussi le neutre -before) ------------------
  rendre "$curseur" l "$largeur" "$amplitude" "$visee" --region --region-graded
  corps=$OUT/brut/$curseur-l-before.png
  zone=$(ls "$OUT/brut/$curseur-l@"*-region.png 2>/dev/null | head -1)
  if [ -f "$corps" ] && [ -n "$zone" ]; then
    magick "$zone" -alpha off -colorspace gray -evaluate multiply 0.65 "$OUT/_m.png"
    magick "$corps" -background black -alpha remove -alpha off "$OUT/_b.png"
    magick "$OUT/_b.png" \( "$OUT/_b.png" -fill "$BLEU" -colorize 100 \) "$OUT/_m.png" \
      -composite "$OUT/D3-$curseur.png"
    echo "D3 $curseur" >> $OUT/journal.log
  else
    echo "D3 ECHEC $curseur corps=$corps zone=$zone" >> $OUT/journal.log
  fi

  # --- D2 : deja rendu le 16-09 au soir, meme moteur et memes reglages ------
  if [ -f "$A/essai-extremes/$curseur.png" ]; then
    cp "$A/essai-extremes/$curseur.png" "$OUT/D2-$curseur.png"
    echo "D2 $curseur (repris de essai-extremes)" >> $OUT/journal.log
  else
    rendre "$curseur" l "$largeur" "$amplitude" "$visee" --after-only
    rendre "$curseur" r "$largeur" "$amplitude" "$visee" --after-only
    g=$(ls "$OUT/brut/$curseur-l@"*.png 2>/dev/null | head -1)
    d=$(ls "$OUT/brut/$curseur-r@"*.png 2>/dev/null | head -1)
    [ -n "$g" ] && [ -n "$d" ] \
      && python3 "$A/bin/outlineoverlay.py" "$g" "$d" "$OUT/D2-$curseur.png" \
           --width 2 --colour "$BLEU" >> $LOG 2>&1 \
      && magick "$OUT/D2-$curseur.png" -background black -alpha remove -alpha off \
           "$OUT/D2-$curseur.png" \
      && echo "D2 $curseur (rendu)" >> $OUT/journal.log \
      || echo "D2 ECHEC $curseur" >> $OUT/journal.log
  fi
done <<'LISTE'
asym-ear-1 0.16 2.0 -
asym-jaw-2 0.16 2.0 -
asym-top-2 0.26 1.0 0.0,-0.0569,1.520
asym-brown-1 0.10 3.0 -
asym-eye-3 0.11 3.0 -
asym-nose-2 0.06 3.0 -
LISTE

cd "$OUT"; rm -f _m.png _b.png
# Une ligne par dispositif, une colonne par curseur, dans l'ordre de la liste :
# les trois a silhouette mobile d'abord, les trois immobiles ensuite.
ORDRE="asym-ear-1 asym-jaw-2 asym-top-2 asym-brown-1 asym-eye-3 asym-nose-2"
for d in D1 D2 D3; do
  fichiers=""
  for c in $ORDRE; do fichiers="$fichiers $d-$c.png"; done
  magick montage -label '%t' $fichiers -tile 6x1 -geometry 220x220+4+4 \
    -background '#222' -fill white -pointsize 12 "ligne-$d.png"
done
magick montage ligne-D1.png ligne-D2.png ligne-D3.png -tile 1x3 -geometry +0+0 \
  -background '#222' "$OUT/planche-trois-dispositifs.png"
echo "TROIS-FINI $(ls D?-*.png | wc -l)/18" >> journal.log
