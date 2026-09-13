#!/bin/sh
# Les vignettes de proxies, formule arretee le 13-09-2026 et validee a l'oeil
# par Raphael sur planche. Detail et mesures : makehuman-vignettes-CANON.md,
# section 1.23. Planches : makehuman-planches-2026-09-13/.
#
#   sh proxies-v2.sh <pack> mesurer          # les trois nombres, sans rendre
#   sh proxies-v2.sh <pack> global  [assets] # neufs > 90 %
#   sh proxies-v2.sh <pack> local   [assets] # etendue < 35 %
#   sh proxies-v2.sh <pack> disperse [assets] # ni l'un ni l'autre
#   sh proxies-v2.sh <pack> diptyque-empile <asset> # exception nommee (13-09)
#
# ⚠⚠ LE CLASSEMENT NE SE DEVINE PAS : lancer `mesurer` d'abord et lire la
#    ligne « -- ZONES » de chaque asset, qui donne neufs / grappes / etendue et
#    conclut GLOBAL, LOCAL ou DISPERSE. Un proxy PARTIEL (qui retire de la
#    geometrie) fait exception avant tout classement : ses sommets neufs sont
#    le BORD DE COUPE, pas son travail.
#
# Le decor est commun aux trois, et chaque valeur est payee d'une mesure :
#   --albedo 0.92   corps porcelaine a 216/255, zero pixel brule
#   --exposure 0.7  le corps monte a 216 ET l'ecart du low poly monte aussi
#   la face          bat le lisere sur fond noir, corps 198 contre 158
#   --azimuth 34    ⚠⚠ POSITIF = regard a gauche SUR CE SCRIPT, l'inverse de
#                   rendertargetthumbs.py. Verifie a l'oeil, jamais recopie
#   --true-edges    ⚠⚠ SANS LUI le noeud Wireframe triangule les quads
#   encre_bleue     une seule couleur pour tout ce qui parle du maillage
#
# ⚠ Le rendu sort avec un fond TRANSPARENT ; l'aplatir sur noir a la livraison
#   (convert x.png -background black -alpha remove -alpha off y.png), le fond
#   noir opaque etant la convention arretee le 12-09.
# 🪤 Rendre en parallele epuise la carte de clairdelune : « Out of memory in
#   CUDA queue ». En serie, toujours.
set -e
A=/var/home/soleil/travail-makehuman/staging
PACK=${1:?pack attendu, par exemple proxies01_cc0}
MODE=${2:?mode attendu : mesurer, global, local ou disperse}
shift 2
OUT=${OUT:-/var/home/soleil/travail-makehuman/vignettes/$PACK-$MODE}
LUM="key=1.1,fill=0.9,rim=4.0,spot=0.05"
COMMUN="--force --samples 192 --subdiv 0 --albedo 0.92 --exposure 0.7 \
--azimuth 34 --lights $LUM --world 0.55"

case "$MODE" in
mesurer)
    # ⚠ --force est indispensable : sans lui les assets deja rendus sont
    # sautes et la mesure ne sort pour personne.
    flatpak run --command=blender org.blender.Blender -b \
        $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" --force --measure-only "$@"
    ;;
global)
    # Tout le maillage en bleu, cadre sur la tete et les epaules.
    mkdir -p "$OUT"
    flatpak run --command=blender org.blender.Blender -b \
        $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" $COMMUN \
        --flat --grey --true-edges --wire-colour encre_bleue \
        --top 0.20 --out "$OUT" "$@"
    ;;
local)
    # Fil BICOLORE : le maillage en gris clair 0,85, la seule zone
    # retravaillee en bleu, zoom maximal dessus.
    # ⚠ Le gris doit etre CLAIR : un fil sombre fait ressortir tout le
    #   maillage et l'oeil ne va nulle part.
    # ⚠ --margin 1.3 est le zoom maximal demande ; sans lui la marge
    #   automatique plafonne a 2,2, ce qui garde plus de contexte.
    mkdir -p "$OUT"
    flatpak run --command=blender org.blender.Blender -b \
        $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" $COMMUN \
        --flat --grey --true-edges --wire-colour encre_bleue \
        --frame-new --margin 1.3 --out "$OUT" "$@"
    ;;
disperse)
    # La zone en aplat du MEME bleu, cadre sur l'enveloppe des zones avec une
    # marge relative a leur etendue.
    mkdir -p "$OUT"
    flatpak run --command=blender org.blender.Blender -b \
        $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" $COMMUN \
        --paint-new --highlight encre_bleue --out "$OUT" "$@"
    ;;
diptyque-empile)
    # ⭐⭐⭐ Exception NOMMEE, arretee le 13-09-2026 sur
    # jujube_proxy_with_helpers_test, qui modifie DEUX foyers eloignes : une
    # anatomie ajoutee au bassin et le visage (la bouche a 0,89 de hauteur,
    # les quatre paupieres a 0,94). Deux prises en demi-format couche, le
    # visage en haut, l'anatomie en bas, empilees en un carre.
    #
    # ⚠ Le paquet de zones ne se decrete pas : `--frame-zone haut|bas` trie
    #   les grappes par hauteur et coupe au PLUS GRAND TROU. Ici 39 points de
    #   hauteur separent le sexe du visage, contre 3 entre bouche et yeux :
    #   l'asset designe lui-meme ses deux paquets.
    # ⚠ Marges arretees a l'oeil : 1,8 en haut (le visage entier reste
    #   reconnaissable) et 1,3 en bas (la trame du maillage se lit).
    # ⚠ Corps MASCULIN pour cet asset, arbitre le 13-09 : compare aux trois
    #   corps, c'est le seul ou l'anatomie ajoutee ne parait pas rapportee.
    #   Le neutre reste la regle pour les 28 autres proxies.
    # ⚠ Trait de maillage NON force : le defaut, comme partout ailleurs.
    #
    # ⛔ Deux voies essayees et ecartees le meme jour, toutes deux mesurees :
    #   - le polyptyque (vue d'ensemble + une cellule par grappe) : « ca rend
    #     moins bien » ; sur la sirene et les membres isoles, retour au
    #     cadrage disperse simple ;
    #   - la vignette UNIQUE tres resserree (`--zone-to-top`, gardee dans le
    #     moteur) : lisible, mais le diptyque donne « une certaine
    #     coherence » qu'elle n'avait pas.
    mkdir -p "$OUT"
    for zone in haut bas; do
        if [ "$zone" = haut ]; then MARGE=1.8; else MARGE=1.3; fi
        flatpak run --command=blender org.blender.Blender -b \
            $A/thumbnail_production/studio_base.blend \
            -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" $COMMUN \
            --paint-new --highlight encre_bleue --frame-zone "$zone" \
            --margin "$MARGE" --shape couche --base-force male \
            --out "$OUT/$zone" "$@"
    done
    echo "Assembler ensuite :"
    echo "  python3 composer-diptyque-empile.py \\"
    echo "      $OUT/haut/<nom>.png $OUT/bas/<nom>.png $OUT/<nom>.png"
    ;;
*)
    echo "mode inconnu : $MODE (mesurer, global, local, disperse, diptyque-empile)" >&2
    exit 1
    ;;
esac
