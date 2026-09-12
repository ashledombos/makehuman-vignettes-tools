#!/usr/bin/python3

"""Compose a diptych: one object, its render and its mesh, in one square.

    python3 bin/composediptyque.py render.png mesh.png out.png

⚠ This is **not** `composesplit.py`. That script composes the two ends of a
slider and draws an arrow from before to after; here the two halves are the
same object seen two ways, so an arrow would assert a change that does not
exist. The separator is therefore a plain thin rule, no arrow, no direction.

The orientation is not a parameter: it is read from the halves. Two landscape
halves stack vertically, two portrait halves sit side by side, and either way
the result is square. ⚠ The check is on the **result**, never on the shape of
the input: two square halves joined give a 512 x 256 rectangle, which is not an
icon. That mistake was made on 06-09 and caught by eye, not by the code.

The rule is grey rather than the orange of `composesplit.py`, and deliberately
so: orange means "before and after" in this catalogue, and a diptych means
"what it looks like, what it is made of". Two different statements should not
share a colour.
"""

import argparse
import os
import subprocess
import sys

REGLE = "#8a8a8a"
EPAISSEUR = 2


def taille(chemin):
    sortie = subprocess.run(["identify", "-format", "%w %h", chemin],
                            capture_output=True, check=True, text=True).stdout
    largeur, hauteur = sortie.split()
    return int(largeur), int(hauteur)


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("render")
    a.add_argument("mesh")
    a.add_argument("out")
    o = a.parse_args()

    for chemin in (o.render, o.mesh):
        if not os.path.exists(chemin):
            sys.exit("absent : %s" % chemin)

    lr, hr = taille(o.render)
    lm, hm = taille(o.mesh)
    if (lr, hr) != (lm, hm):
        sys.exit("les deux moities n'ont pas la meme taille : %dx%d et %dx%d"
                 % (lr, hr, lm, hm))

    # Une moitie large s'empile, une moitie haute se juxtapose.
    empile = lr > hr
    resultat = (lr, hr * 2) if empile else (lr * 2, hr)
    if resultat[0] != resultat[1]:
        sys.exit("l'assemblage donnerait %dx%d, qui n'est pas un carre ; "
                 "des moities de %dx%d ne composent pas une vignette"
                 % (resultat[0], resultat[1], lr, hr))

    jonction = "-append" if empile else "+append"
    subprocess.run(["convert", o.render, o.mesh, jonction, "+repage",
                    o.out], check=True)

    # La regle se trace apres l'assemblage, sur la couture.
    if empile:
        trait = "line 0,%d %d,%d" % (hr, resultat[0], hr)
    else:
        trait = "line %d,0 %d,%d" % (lr, lr, resultat[1])
    subprocess.run(["convert", o.out, "-stroke", REGLE,
                    "-strokewidth", str(EPAISSEUR), "-draw", trait,
                    o.out], check=True)
    print("%s : %dx%d, %s" % (o.out, resultat[0], resultat[1],
                              "empile" if empile else "juxtapose"))


if __name__ == "__main__":
    main()
