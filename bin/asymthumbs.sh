#!/usr/bin/env bash
#
# Produit les vignettes des 31 curseurs d'asymétrie de MPFB, dans la
# convention arbitrée le 04-09.
#
# Deux recettes, et c'est la **mesure** qui choisit, non le jugement : si la
# silhouette du corps bouge entre les deux bouts du curseur, on trace les deux
# contours, vermillon pour le bout droit et bleu pour le gauche, sur l'état
# moyen ; sinon aucun contour n'existe de face, et l'on cerne alors la zone que
# le curseur déplace, ce qui dit au moins de quel trait il s'agit.
#
# ⚠ Visée forcée sur l'axe du corps (--on-axis). Une cible d'asymétrie pousse
# d'un seul côté, donc la sonde d'affinage la suit et le cadre part de travers,
# au point de sortir un œil du champ. C'est la famille qui est symétrique.
#
# ⚠ Le zoom est propre au trait, quantifié en quelques niveaux. Un visage
# entier réduit une asymétrie de quelques millimètres à presque rien : mesuré,
# de 5,2 % du cadre pour le nez à 15,1 % pour le sommet du crâne.

set -u
ATELIER=${ATELIER:-/var/home/soleil/travail-makehuman}
CIBLES=${CIBLES:-$HOME/.var/app/org.blender.Blender/config/blender/5.2/extensions/user_default/mpfb/data/targets/asym}
SORTIE=${SORTIE:-$ATELIER/vignettes-cibles/asym}
ECHANTILLONS=${ECHANTILLONS:-640}

# Le seuil, en pixels, au-delà duquel on considère que la silhouette a bougé.
# Sous ce seuil, le contour du canal alpha n'a rien à tracer.
#
SEUIL_SILHOUETTE=${SEUIL_SILHOUETTE:-400}

VERMILLON="#D55E00"
BLEU="#0072B2"

# Le zoom par trait, en mètres de corps cadrés, et l'épaisseur du trait : deux
# pixels sur une petite zone, où trois cacheraient ce qu'ils désignent.
largeur_de() {
    case "$1" in
        *-brown-*|*-eye-*)  echo "0.13 2" ;;
        *-nose-*)           echo "0.10 2" ;;
        *-mouth-*)          echo "0.13 2" ;;
        *-cheek-*)          echo "0.16 3" ;;
        *-jaw-*|*-temple-*) echo "0.18 3" ;;
        *-top-*|*-ear-*)    echo "0.20 3" ;;
        *breast*)           echo "0.30 3" ;;
        *trunk*)            echo "0.40 3" ;;
        *)                  echo "0.20 3" ;;
    esac
}

mkdir -p "$SORTIE"
curseurs=$(ls "$CIBLES" | sed 's/\.target.*//' | sed 's/-[lr]$//' | sort -u)
total=$(echo "$curseurs" | wc -l)
fait=0

for curseur in $curseurs; do
    fait=$((fait + 1))
    read -r largeur epaisseur <<< "$(largeur_de "$curseur")"
    travail="$SORTIE/.$curseur"
    mkdir -p "$travail"

    flatpak run --command=blender org.blender.Blender -b \
        "$ATELIER/studio_base.blend" -P "$ATELIER/bin/rendertargetthumbs.py" -- \
        --target "$CIBLES/$curseur-l.target.gz" \
        --target "$CIBLES/$curseur-r.target.gz" \
        --who female --size 256 --width "$largeur" --azimuth 0 \
        --refine --on-axis --region --amounts 0.0,1.0 --after-only \
        --out "$travail" --samples "$ECHANTILLONS" >/dev/null 2>&1

    moyen="$travail/$curseur-l@0.png"
    gauche="$travail/$curseur-l@100.png"
    droite="$travail/$curseur-r@100.png"
    zone="$travail/$curseur-r@100-region.png"
    if [ ! -f "$moyen" ] || [ ! -f "$gauche" ] || [ ! -f "$droite" ]; then
        echo "SAUTE $curseur : rendu manquant"
        continue
    fi

    # La silhouette a-t-elle bougé ? On compare les deux canaux alpha, seuillés.
    #
    # ⚠ Le compte se **calcule**, il ne se lit pas dans la sortie de
    # `compare`. Trois pièges enchaînés, chacun payé d'un essai, et le
    # troisième est le pire parce qu'il est silencieux et plausible :
    #
    # 1. `compare` n'est pas `convert`, il **n'accepte pas** les groupes entre
    #    parenthèses : extraire les alphas à la volée dans sa ligne de commande
    #    rendait 616 pixels pour six curseurs différents, valeur sans rapport
    #    avec le sujet ;
    # 2. `compare -metric AE` écrit « 583.91707 (0.0089) », la valeur brute
    #    puis la normalisée entre parenthèses. Garder la ligne entière donne
    #    une chaîne non numérique et `[ -ge ]` échoue sans bruit ; en retirer
    #    les caractères non chiffres transforme « 4.00195 » en **400195**, si
    #    bien que toute valeur non nulle franchit n'importe quel seuil. La
    #    joue et la bouche, qui déplacent 2 et 1 pixels, sont ainsi passées
    #    pour des changements de silhouette ;
    # 3. et le format même n'est pas portable, `compare` n'imprimant pas les
    #    mêmes décimales d'une machine à l'autre.
    #
    # `%[fx:mean*w*h]` sur la différence de deux alphas binarisés donne le
    # nombre de pixels qui diffèrent, en un seul nombre et sans mise en forme.
    ecart=$(convert "$gauche" -alpha extract -threshold 50% \
        \( "$droite" -alpha extract -threshold 50% \) \
        -compose difference -composite \
        -format "%[fx:int(mean*w*h+0.5)]" info:)
    ecart=${ecart:-0}

    if [ "$ecart" -ge "$SEUIL_SILHOUETTE" ]; then
        recette=trait
        python3 "$ATELIER/bin/outlineoverlay.py" "$moyen" "$droite" \
            "$SORTIE/$curseur-l-r.png" --also "$gauche" \
            --width "$epaisseur" --colour "$VERMILLON" --colour2 "$BLEU" \
            >/dev/null
    else
        recette=zone
        python3 "$ATELIER/bin/outlineoverlay.py" "$moyen" "$droite" \
            "$SORTIE/$curseur-l-r.png" --region "$zone" \
            --width "$epaisseur" --colour "$VERMILLON" >/dev/null
    fi
    printf '%2d/%2d %-18s %-6s silhouette %6s px, cadre %s m\n' \
        "$fait" "$total" "$curseur" "$recette" "$ecart" "$largeur"
done
echo "TERMINE, vignettes dans $SORTIE"
