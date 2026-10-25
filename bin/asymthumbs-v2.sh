#!/bin/sh
# The 31 asymmetry slider thumbnails of MPFB, in the convention settled on
# 2026-09-14: no outline, no colour code, the slider pushed all the way on ONE
# side only, seen under a slight three-quarter profile, on an opaque black
# background, with the porcelain body shared by the proxy and breast lots.
#
# ⚠ WHY NO OUTLINE. The previous recipe (bin/asymthumbs.sh, kept for the
# record) drew a vermilion and a blue outline over a median state. It reads as
# a diagram, not as a thumbnail, and it does not match the two lots already
# delivered. One side pushed to 100 % is the whole picture now.
#
# ⚠ --on-axis IS MANDATORY. An asymmetry target pushes one side only, so the
# refining probe follows it and the frame drifts sideways, far enough to push
# an eye out of shot. The family is what is symmetric, not the target.
#
# ⚠⚠ THE SIDE IS MEASURED, NOT GUESSED. Both -l and -r are rendered and the
# one that changes more pixels of the subject wins. It is not cosmetic: on
# asym-jaw-1 at azimuth 35 the far side moves 0.17 % of the subject against
# 1.87 % for the near one, an eleven-fold gap.
#
# ⚠ The renders come out with a TRANSPARENT background; they are flattened on
# black at delivery time, black being the convention settled on 2026-09-12.
# 🪤 Rendering in parallel exhausts the GPU: "Out of memory in CUDA queue".
# Always in series.
#
#   sh asymthumbs-v2.sh            # the whole lot
#   CURSEURS="asym-nose-1" sh asymthumbs-v2.sh   # one slider
set -u
ATELIER=${ATELIER:-/var/home/soleil/travail-makehuman}
CIBLES=${CIBLES:-$HOME/.var/app/org.blender.Blender/config/blender/5.2/extensions/user_default/mpfb/data/targets/asym}
SORTIE=${SORTIE:-$ATELIER/vignettes/asym-v2}
TRAVAIL=${TRAVAIL:-$SORTIE/.rendus}
ECHANTILLONS=${ECHANTILLONS:-256}

# Lighting and skin are the named presets of bin/vignettes-presets.sh: the
# face lighting (azimuth <= 40) and the light skin of the target thumbnails.
LUM="key=1.1,fill=0.9,rim=4.0,spot=0.05"
MONDE=0.55
PEAU="colorMixIn=0.68,colorMixInStrength=0.70"

# How much body to frame, in metres, per feature. Taken over unchanged from
# the first recipe: a whole face shrinks a few millimetres of asymmetry to
# nothing, measured at 5.2 % of the frame for the nose against 15.1 % for the
# top of the skull.
largeur_de() {
    case "$1" in
        *-brown-*|*-eye-*)  echo 0.13 ;;
        *-nose-*)           echo 0.10 ;;
        *-mouth-*)          echo 0.13 ;;
        *-cheek-*)          echo 0.16 ;;
        *-jaw-*|*-temple-*) echo 0.18 ;;
        *-top-*|*-ear-*)    echo 0.20 ;;
        *breast*)           echo 0.30 ;;
        *trunk*)            echo 0.40 ;;
        *)                  echo 0.20 ;;
    esac
}

# The viewing angle, per family, measured on 2026-09-15 over one slider of
# each family at 25, 35 and 45 degrees (docs/vignettes-asym/README.md holds
# the table). 35 is the default; a family only leaves it where the measured
# amplitude gains more than a fifth.
#   ⚠ A POSITIVE azimuth turns the gaze to the LEFT of the frame here, the
#   opposite of bin/proxies-v2.sh. Checked on the image, never copied.
azimut_de() {
    case "$1" in
        *-brown-*)          echo 25 ;;   # 9.47 % against 7.10 at 35
        *-jaw-*|*-temple-*) echo 25 ;;   # 2.19 % against 1.87 at 35
        *-top-*)            echo 25 ;;   # 10.83 % against 8.22 at 35
        *-cheek-*)          echo 45 ;;   # 2.56 % against 1.48 at 35
        *)                  echo 35 ;;
    esac
}

mkdir -p "$SORTIE" "$TRAVAIL"
CURSEURS=${CURSEURS:-$(ls "$CIBLES" | sed 's/\.target.*//' | sed 's/-[lr]$//' |
    sort -u)}
total=$(echo "$CURSEURS" | wc -w)
fait=0

for curseur in $CURSEURS; do
    fait=$((fait + 1))
    W=$(largeur_de "$curseur")
    AZ=$(azimut_de "$curseur")
    D="$TRAVAIL/$curseur"
    mkdir -p "$D"

    for cote in l r; do
        # ⭐ One Blender launch renders BOTH states of a side: --amounts
        # 0.0,1.0 gives <name>@0.png and <name>@100.png in the same frame,
        # which is what makes the amplitude measurable at all.
        [ -f "$D/$curseur-$cote@100.png" ] && continue
        flatpak run --command=blender org.blender.Blender -b \
            "$ATELIER/studio_base.blend" -P "$ATELIER/bin/rendertargetthumbs.py" -- \
            --target "$CIBLES/$curseur-$cote.target.gz" \
            --who female --size 256 --refine --hide-inner --fstop 0 \
            --samples "$ECHANTILLONS" --on-axis --amounts 0.0,1.0 \
            --after-only --azimuth "$AZ" --width "$W" \
            --lights "$LUM" --world "$MONDE" --skin-tune "$PEAU" \
            --out "$D" > "$D/$cote.log" 2>&1
    done

    part_l=$(sh "$ATELIER/bin/mesurer-asym.sh" \
        "$D/$curseur-l@0.png" "$D/$curseur-l@100.png" | awk '{print $3}')
    part_r=$(sh "$ATELIER/bin/mesurer-asym.sh" \
        "$D/$curseur-r@0.png" "$D/$curseur-r@100.png" | awk '{print $3}')
    garde=$(awk "BEGIN{print ($part_l >= $part_r) ? \"l\" : \"r\"}")
    part=$(awk "BEGIN{print ($part_l >= $part_r) ? $part_l : $part_r}")

    # ⚠ The delivered name keeps the pair form <slider>-l-r.png even though a
    # single side is pushed: it names the SLIDER, which is a pair of targets.
    magick "$D/$curseur-$garde@100.png" -background black -alpha remove \
        -alpha off "$SORTIE/$curseur-l-r.png"
    opaque=$(identify -format '%[opaque]' "$SORTIE/$curseur-l-r.png")
    printf '%2d/%2d %-18s az%-3s cote %s  l %5s %%  r %5s %%  retenu %5s %%  opaque %s\n' \
        "$fait" "$total" "$curseur" "$AZ" "$garde" "$part_l" "$part_r" \
        "$part" "$opaque"
done
echo "TERMINE, vignettes dans $SORTIE"
