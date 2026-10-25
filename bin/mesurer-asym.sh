#!/bin/sh
# How much of a thumbnail actually changes: the share of the SUBJECT's pixels
# that differ between the neutral state and the slider pushed all the way.
#
# ⚠ Both images are compared FLATTENED ON BLACK: the renders come out with a
# transparent background, and comparing alpha mixes background into subject.
# ⚠ DO NOT go through `compare -metric AE`: its metric goes to stderr next to
# possible warnings, and parsing it gave 18 million changed pixels on a 65 536
# pixel image, i.e. 43 595 % of the subject. Compositing the difference and
# thresholding it needs no parsing at all.
#
#   sh mesurer-asym.sh <neutral.png> <pushed.png>  ->  "changed subject share"
set -u
N=$1
P=$2
T=$(mktemp -d)
magick "$N" -background black -alpha remove -alpha off "$T/n.png"
magick "$P" -background black -alpha remove -alpha off "$T/p.png"
sujet=$(magick "$N" -alpha extract -threshold 50% -format '%[fx:mean*w*h]' info:)
change=$(magick "$T/n.png" "$T/p.png" -compose difference -composite \
    -colorspace Gray -threshold 3% -format '%[fx:mean*w*h]' info:)
rm -rf "$T"
sujet=${sujet%%.*}
change=${change%%.*}
[ "${sujet:-0}" -eq 0 ] && sujet=1
part=$(awk "BEGIN{printf \"%.2f\", 100*$change/$sujet}")
echo "$change $sujet $part"
