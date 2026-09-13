#!/usr/bin/env python3
"""⛔ ESSAI CONSIGNE, NON RETENU, gardé pour ne pas le réinventer.

Composer l'overview + les cellules d'un polyptyque en une seule image.

Le polyptyque (vue d'ensemble à gauche, un gros plan par grappe à droite) a
été construit puis **écarté le 13-09-2026** : « ça rend moins bien ». Sur la
sirène et les membres isolés, retour au cadrage `disperse` simple, les gens
devinant la modification sans zoom ; sur l'asset à deux foyers éloignés, c'est
le **diptyque empilé** qui a été retenu (`composer-diptyque-empile.py`).

    python3 composer-polyptyque.py <dossier> <nom> [<sortie>]

Cherche `<nom>-overview.png` et `<nom>-cellN.png` dans <dossier>, et produit
une image : l'overview a gauche (pleine hauteur), la grille des cellules a
droite. Demande de Raphael, 13-09-2026 : garder l'overview pour qu'on voie
que c'est un corps (la queue, les membres isoles), et zoomer separement sur
chaque zone distante que l'overview seul ne montre pas assez.
"""
import glob
import math
import os
import subprocess
import sys


def composer(dossier, nom, sortie=None):
    overview = os.path.join(dossier, nom + "-overview.png")
    cellules = sorted(
        glob.glob(os.path.join(dossier, nom + "-cell*.png")),
        key=lambda p: int(p.rsplit("cell", 1)[1].split(".")[0]))
    if not os.path.exists(overview) or not cellules:
        sys.exit("overview ou cellules manquantes pour %s dans %s" % (nom, dossier))
    if sortie is None:
        sortie = os.path.join(dossier, nom + "-polyptyque.png")

    n = len(cellules)
    colonnes = 2 if n > 2 else 1
    lignes = math.ceil(n / colonnes)

    grille = "/tmp/_grille_%s.png" % nom
    subprocess.run(["montage"] + cellules
                   + ["-tile", "%dx%d" % (colonnes, lignes), "-geometry", "+3+3",
                      "-background", "black", grille], check=True)

    # ⚠ Les deux panneaux doivent avoir la MEME hauteur, sinon l'assemblage
    # cote a cote laisse une bande noire ou etire l'un des deux.
    hauteur = subprocess.run(["identify", "-format", "%h", grille],
                             capture_output=True, check=True).stdout.decode().strip()
    overview_redim = "/tmp/_overview_%s.png" % nom
    subprocess.run(["convert", overview, "-resize", "x" + hauteur,
                    "-background", "black", "-gravity", "center",
                    "-extent", "x" + hauteur, overview_redim], check=True)

    subprocess.run(["convert", overview_redim, grille, "+append",
                    "-background", "black", "-bordercolor", "black",
                    "-border", "4", sortie], check=True)
    os.remove(grille)
    os.remove(overview_redim)
    print("compose :", sortie)


if __name__ == "__main__":
    composer(*sys.argv[1:])
