#!/usr/bin/python3

"""Draw a thin ring just outside the silhouette, so it survives any theme.

    python3 bin/keyline.py in.png out.png [--width 1] [--colour "#b0b0b0"]

⚠ Why this exists. These thumbnails ship with a transparent background, so the
user's theme shows through, and Blender's default theme is dark, about 48/255.
A subject lit from one side then has a shadowed edge at roughly that same
luminance, and the silhouette dissolves into the background along that edge.
Measured on 06-09: the low decile of the contour sat at 34 and 48 for a grey
blueprint, i.e. exactly background level.

⚠ Raising the world ambient does NOT fix it: from 0.4 to 0.7, that is 75 % more
light, the contour gains 3 points where 22 are missing, and the modelling loses
0.9. The two measures move in opposite directions, so it is not an improvement.

⭐ A ring drawn from the ALPHA channel does not depend on the lighting at all,
which is the whole point. It sits **outside** the silhouette so that it never
eats into the subject, and it is mid-grey rather than white or black, so it
reads against a dark theme and against a light one alike. That is the same
reasoning that made the studio grey rather than white.

⚠ This is not the stylised outline that was tried and rejected in September:
that one traced a displaced REGION on the body and read as a selection marquee.
This traces only the outer silhouette, which is what a keyline is.
"""

import argparse
import os
import subprocess
import sys

GRIS_LISERE = "#b0b0b0"


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("entree")
    a.add_argument("sortie")
    a.add_argument("--width", type=int, default=1,
                   help="epaisseur du lisere en pixels")
    a.add_argument("--colour", default=GRIS_LISERE)
    o = a.parse_args()

    if not os.path.exists(o.entree):
        sys.exit("absent : %s" % o.entree)

    # ⚠⚠ `-compose minus` rendait un anneau ENTIEREMENT NOIR : l'ordre de ses
    # operandes est l'inverse de celui qu'on croit lire. `difference`, qui est
    # une valeur absolue, s'en moque et donne le meme anneau dans les deux
    # sens. Vu le 06-09, et la panne etait muette : le script annoncait son
    # lisere, les mesures de contour sortaient rigoureusement identiques.
    #
    # ⚠ Et l'anneau se DURCIT au seuil avant de servir d'alpha. Sans cela il
    # herite de l'anticrenelage de la silhouette, donc il est a demi
    # transparent sur toute sa longueur et ne porte presque rien.
    anneau = o.sortie + ".anneau.png"
    couche = o.sortie + ".couche.png"
    subprocess.run(["convert", o.entree, "-alpha", "extract",
                    "(", "+clone", "-morphology", "Dilate",
                    "Octagon:%d" % o.width, ")",
                    "-compose", "difference", "-composite",
                    "-threshold", "25%", anneau], check=True)
    largeur, hauteur = subprocess.run(
        ["identify", "-format", "%w %h", o.entree], capture_output=True,
        check=True, text=True).stdout.split()
    subprocess.run(["convert", "-size", "%sx%s" % (largeur, hauteur),
                    "xc:" + o.colour, anneau, "-alpha", "off",
                    "-compose", "copy_opacity", "-composite", couche],
                   check=True)
    subprocess.run(["convert", couche, o.entree, "-compose", "over",
                    "-composite", "+repage", o.sortie], check=True)
    # ⚠ Verifier l'EFFET, non l'intention : un anneau vide passerait sans
    # bruit, et c'est exactement ce qui est arrive.
    change = subprocess.run(["compare", "-metric", "AE", o.entree, o.sortie,
                             "null:"], capture_output=True, text=True)
    touches = (change.stderr or change.stdout).strip()
    if touches in ("0", "0 (0)"):
        sys.exit("le lisere n'a touche aucun pixel : anneau vide")

    for reste in (o.sortie + ".anneau.png", o.sortie + ".couche.png"):
        os.remove(reste)
    print("%s : lisere de %d px en %s" % (o.sortie, o.width, o.colour))


if __name__ == "__main__":
    main()
