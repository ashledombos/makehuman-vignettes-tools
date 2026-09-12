#!/bin/sh
# Les vignettes de proxies : montrer la TOPOLOGIE, pas la silhouette.
# Formule arretee dans la nuit du 05 au 06-09-2026, sur 21 combinaisons.
#
#   sh bin/proxies.sh proxies01_cc0
#
# ⚠⚠ --subdiv 0 est obligatoire : le script subdivise par defaut, ce qui lisse
#    le maillage et fait disparaitre le sujet meme de la vignette.
# ⚠  --flat : sans cela un corps a 412 faces est aussi rond qu'un corps a 14 000.
# ⚠  --wire 0.09 : une FRACTION de l'arete moyenne, jamais une valeur fixe.
#    A 12 % le trait se congestionne autour des yeux sur un maillage dense.
# ⚠  --wire-colour sombre : l'encre distingue le mieux (15,3 contre 11,8 pour le
#    bleu, 10,8 pour le blanc) et ne maquille pas le visage, alors que les
#    couleurs vives se logent dans les creux ou les aretes se resserrent.
# ⚠  --top 0.20 : en pied les aretes s'ecrasent en moire ; plus serre, on perd
#    le contexte du corps.
#
# ⚠⚠ LIMITE CONNUE : ce cadrage distingue par la DENSITE et rend aveugle au
#    reste. Deux proxies qui ne different que par le torse donnent la meme
#    image, leurs tetes etant identiques au sommet pres. La suite est de cadrer
#    la ou le proxy s'ecarte du corps de base.
# ⭐⭐ DEUX DISPOSITIFS, et le critere pour choisir :
#   - vignette simple au trait d'encre quand c'est la DENSITE qui distingue ;
#   - comparaison au corps de base quand c'est la FORME.
# Le second, --compare, rend deux prises au meme cadre, en DEMI-FORMAT pour que
# l'assemblage soit carre, et cadre la ou le proxy s'ecarte du corps, avec une
# marge relative a l'etendue de cet ecart. Mesure sur les quinze : distance
# mediane 58,0 contre 15,5 pour la vignette simple.
#
#   sh bin/proxies.sh proxies01_cc0            # vignette simple
#   sh bin/proxies.sh proxies01_cc0 compare    # comparaison
A=/var/home/soleil/travail-makehuman/staging
PACK=${1:-proxies01_cc0}
MODE=${2:-simple}
# ⭐⭐ TROIS DISPOSITIFS, un par besoin :
#   simple   : retrouver l'asset dans une grille. Trait d'encre, cadre sur la
#              tete. C'est la vignette de catalogue.
#   compare  : un proxy PARTIEL, qui retire de la geometrie. Paire lisse contre
#              maille, sur l'objet.
#   zone     : comprendre CE QUE l'asset modifie. La zone qui s'ecarte du corps
#              passe au vermillon, le cadre colle a l'enveloppe de ces zones,
#              donc la tete et les pieds sortent du champ s'ils ne changent pas.
#              Idee de Raphael, 06-09.
# ⚠ La zone en couleur informe mais ne distingue pas : sur deux corps qui ne
#   different que par un motif de taches reparties, la distance a 120 px reste a
#   1,1 contre 15 a 30 ailleurs. Limite de resolution, pas de conception.
# ⭐ Le gris du studio et le lisere des vignettes de cibles, pour que les deux
# familles sortent du meme studio. Mesure : l'ecart de teinte entre vignettes
# tombe de 89 a 49, et l'exposition du sujet de 173 a 122, soit la bande des
# cibles qui tournent a 135.
LUM="key=0.7,fill=0.6,rim=2.0,spot=0.05"
if [ "$MODE" = zone ]; then
    flatpak run --command=blender org.blender.Blender -b $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" --force --samples 192 \
        --subdiv 0 --paint --highlight rouge --wire 0.09 --wire-colour sombre \
        --compare --lights "$LUM" --world 0.4
    exit 0
fi
if [ "$MODE" = compare ]; then
    flatpak run --command=blender org.blender.Blender -b $A/thumbnail_production/studio_base.blend \
        -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" --force --samples 192 \
        --subdiv 0 --flat --grey --wire 0.09 --wire-colour sombre \
        --lights "$LUM" --world 0.4 --top 0.20 --compare --mesh-pair
    echo "Assembler ensuite chaque paire :"
    echo "  python3 bin/composesplit.py <nom>-base.png <nom>-proxy.png <nom>.png \\"
    echo "      --axis vertical --stack --no-arrow"
    exit 0
fi
flatpak run --command=blender org.blender.Blender -b $A/thumbnail_production/studio_base.blend \
    -P $A/bin/rendermeshthumbs.py -- --pack "$PACK" --force --samples 192 \
    --subdiv 0 --flat --grey --wire 0.09 --wire-colour sombre --top 0.20 \
    --lights "$LUM" --world 0.4
