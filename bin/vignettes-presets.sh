#!/bin/sh
# Les reglages nommes des vignettes de cibles MPFB.
#
# ⭐ POURQUOI DES NOMS. Un chiffre isole ne se retrouve pas : « rim=4 » ne dit
# ni pour quel angle ni contre quel defaut il a ete choisi. Chaque preset
# ci-dessous porte donc un nom, sa raison, et la mesure qui l'a departage.
# Un script de famille se contente de les citer.
#
# Arrete le 05-09-2026 avec Raphael, sur la famille poitrine.
# Dossier : ~/dev/admin/makehuman-vignettes-cibles-2026-09-03.md

# ---------------------------------------------------------------- ECLAIRAGES
#
# ⚠⚠ REGLE GENERALE : l'eclairage se regle PAR ANGLE DE VUE, jamais recopie en
# chiffres fixes. A 25 degres la lampe arriere est derriere le sujet et
# n'eclaire presque rien de visible ; a 70 elle frise la surface. Mesure : a
# reglages identiques, 121 de moyenne a 25 degres contre 158-184 a 70.

# Pour les vues proches de la face (azimut <= 40 degres).
# Le contre-jour doit y etre fort : a 2,0 le lisere disparait (bord contre
# fond 146,7), a 4,0 il est franc (167,5), a 6,0 il commence a bruler.
LUM_FACE="key=1.1,fill=0.9,rim=4.0,spot=0.05"
MONDE_FACE=0.55

# Pour les vues de profil et les gros plans (azimut >= 70 degres).
# ⚠ Le contre-jour a 4 ici PLAQUE l'avant du buste en blanc avec du noir
# devant, « comme un flash » : ce n'est pas le contre-jour seul qui nuit, c'est
# sa combinaison avec un remplissage et une ambiante bas. Preference de
# Raphael entre 1,5 et 2,5.
LUM_PROFIL="key=0.7,fill=0.6,rim=2.0,spot=0.05"
MONDE_PROFIL=0.4

# ⚠ RETIRES, gardes pour memoire :
#   volumineux  key=0.8,fill=0.2,rim=4,spot=0.05 monde 0.2
#               le premier eclairage du chantier ; beau modele mais plaquage.
#   plat        key=0.4,fill=2.0,rim=0.2,spot=0.4 monde 0.6
#               seul moyen d'eclairer le fond de l'entonnoir de nipple-point ;
#               inutile depuis que la pigmentation le masque.

# -------------------------------------------------------------------- PEAUX
#
# Gris et non blanc : le gris est le seul stable quel que soit le theme de
# l'usager, 6 points d'ecart entre theme clair et sombre contre 48 pour le
# blanc. Ce n'est pas un compromis, c'est une independance.
PEAU_GRISE="colorMixIn=0.5,colorMixInStrength=0.6"

# ⚠ En gros plan, le grain de pores regle pour un corps entier devient un
# relief lunaire : la texture prend le pas sur la forme. Le grain doit suivre
# l'echelle du cadre.
PEAU_GROS_PLAN="colorMixIn=0.5,colorMixInStrength=0.6,pore_strength=0.10,pore_scale=6000"

# ⭐ Le delta d'areole est le repere qui dit OU REGARDER. Un eclairage clair le
# noie : il faut donc le remonter d'autant. Contraste areole/peau mesure :
# 0,20/0,4 -> 37 ; 0,15/0,6 -> 45 ; 0,10/0,8 -> 57 ; 0,05/1,0 -> 95 mais
# l'areole devient une pastille noire. Raphael a tranche pour 0,15.
ZONE_AREOLE="nipple:colorMixIn=0.15,colorMixInStrength=0.6"

# -------------------------------------------------------------------- COULEURS
#
# ⚠⚠ Le couple le plus lisible a l'oeil, rose et cyan, est le SEUL a se
# refermer en vision deficiente : sa distance tombe de 215 a 55. Une couleur
# ne se choisit pas a l'oeil, elle se simule.
TRAIT_CHAUD="#F0E442"   # jaune Okabe-Ito
TRAIT_FROID="#56B4E9"   # bleu ciel Okabe-Ito
TRAIT_EPAISSEUR=3

# ---------------------------------------------------------------------- VUES
#
# « LA PAIRE » : trois-quarts a 25 degres, format couche, coupe horizontale.
# Les deux seins visibles, les deux mamelons assombris servant de reperes.
VUE_PAIRE="--rect --azimuth 25 --on-axis"
# « LA SILHOUETTE » : trois-quarts a 70 degres, format debout, coupe verticale.
# Le sein proche se dessine sur le fond, l'eloigne apparait de trois-quarts.
# ⚠ Remonter la visee de 6 cm : a 10 on attrape la bouche et le nez et l'oeil
# part sur le visage ; a 6 il reste le menton et le cou, qui donnent l'echelle.
VUE_SILHOUETTE="--portrait --azimuth 70 --lift 0.06"
# « LE GROS PLAN » : carre, bras tendus, aucun visage. Pour ce dont le
# changement est INTERIEUR a la forme : tout pixel qui n'est pas le sujet
# dilue le signal.
VUE_GROS_PLAN="--azimuth 70 --lift 0.02 --arms-down 0"

# ------------------------------------------------------------- DISPOSITIFS
#
# ⭐⭐ LE CRITERE QUI DECIDE : mesurer l'aire ou l'ALPHA differe entre les deux
# bouts du curseur, rapportee au sujet, c'est le DEPLACEMENT DE CONTOUR.
#   au-dessus de ~5 % -> DOUBLE TRAIT (le contour bouge, il y a a tracer)
#   en dessous        -> COUPE avant/apres
# Mesure sur la poitrine : hauteur 18,3 %, pointe 10,1 %, repartition 7,0 %
# contre ecartement 3,6 % et saillie 0,47 %.
#
# ⚠ Ce seuil juge un CADRAGE, pas une cible : le meme teton passe de 0,47 % en
# vue trois-quarts a 5,70 % en gros plan de profil.
#
# ⚠ Et il faut que le sujet TIENNE LA SILHOUETTE : bras en pose de repos, c'est
# le bras qui la tient et le trace devient faux (2,35 % contre 7,0 %).

# -------------------------------------------------------- COMMUNS A TOUT
COMMUN="--who female --size 256 --refine --hide-inner --fstop 0 --samples 512"
