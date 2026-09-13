#!/usr/bin/env python3
"""Empiler les deux moities d'un diptyque de zones en une vignette carree.

    python3 composer-diptyque-empile.py <haut.png> <bas.png> <sortie.png>

⭐⭐ Arbitre par Raphael le 13-09-2026, apres avoir compare avec la vignette
unique tres resserree : le diptyque empile donne « une certaine coherence »
que le cadrage unique n'avait pas, chaque moitie montrant une zone sans que
l'autre la comprime.

Les deux prises sont en DEMI-FORMAT couche (256 x 128, option `--shape
couche` du moteur), pour que l'assemblage tombe juste sur un carre : deux
prises carrees donneraient un rectangle de 512 x 256, pas une icone
(CANON 1.9, piege deja paye une fois).

Un trait blanc d'un pixel separe les deux moities, comme la coupe des
vignettes de cibles.
"""
import subprocess
import sys


def empiler(haut, bas, sortie, trait=True):
    subprocess.run(["convert", haut, bas, "-append",
                    "-background", "black", "-alpha", "remove", "-alpha", "off",
                    sortie], check=True)
    if trait:
        # ⚠ Le trait se DESSINE sur la jonction, il ne s'INSERE pas : un
        # `-splice 0x1` ajoutait sa ligne a la hauteur totale et sortait une
        # image de 256 x 257, donc plus une icone carree.
        hauteur_haut = subprocess.run(
            ["identify", "-format", "%h", haut],
            capture_output=True, check=True).stdout.decode().strip()
        y = int(hauteur_haut) - 1
        subprocess.run(["convert", sortie, "-fill", "#ffffff",
                        "-draw", "rectangle 0,%d 9999,%d" % (y, y),
                        sortie], check=True)
    dimensions = subprocess.run(["identify", "-format", "%wx%h", sortie],
                                capture_output=True, check=True).stdout.decode()
    print("empile : %s (%s)" % (sortie, dimensions))


if __name__ == "__main__":
    empiler(sys.argv[1], sys.argv[2], sys.argv[3])
