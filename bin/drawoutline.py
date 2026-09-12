#!/usr/bin/python3

"""Draw stylised outlines, one colour per slider end, over one render.

    python3 bin/drawoutline.py body.png out.png \
        --curve high.json --curve low.json

Takes the JSON written by rendertargetthumbs.py --stylise and draws each
curve as a dashed line on top of the render. The first curve gets the first
colour, the second the second, and so on.

⭐ This is the answer to a defect of the region outline: the boundary of a
displaced region follows mesh vertices, so it circles an *area* instead of
suggesting a *shape*, and it reads as a selection marquee. A curve derived from
an anatomical vertex group and reduced to the useful angular sector reads as a
drawing: for a breast seen from the front, the sweep of its underside rising
toward the armpit, and nothing else.

Colours are the Okabe-Ito vermillion and blue rather than the orange and yellow
of the shipped icons: those two do not separate, the yellow turning into a
smudge on skin. This pair is safe for every common form of colour blindness and
the two have very different luminances, so they stay apart even in greyscale.
"""

import argparse
import json
import math
import subprocess

COULEURS = ["#D55E00", "#0072B2", "#009E73", "#CC79A7"]
TIRET = 6               # longueur d'un tiret, en pixels de contour
INTERVALLE = 5


def executer(commande):
    subprocess.run(commande, check=True)


def tirets(points):
    """La courbe découpée en segments, à pas constant le long du tracé.

    ⚠ Le pointillé se mesure **le long de la courbe**, non en x : une courbe
    qui remonte à la verticale n'a presque pas d'étendue horizontale, et un
    motif posé en x y ferait un trait continu puis un grand vide.
    """
    segments, courant, parcouru, dessine = [], [], 0.0, True
    for i, p in enumerate(points):
        if dessine:
            courant.append(p)
        if i + 1 == len(points):
            break
        q = points[i + 1]
        pas = math.hypot(q[0] - p[0], q[1] - p[1])
        parcouru += pas
        limite = TIRET if dessine else INTERVALLE
        if parcouru >= limite:
            if dessine and len(courant) > 1:
                segments.append(courant)
            courant = []
            parcouru = 0.0
            dessine = not dessine
    if dessine and len(courant) > 1:
        segments.append(courant)
    return segments


def dessiner(base, sortie, courbes, epaisseur):
    commande = ["convert", base]
    for indice, chemin in enumerate(courbes):
        d = json.load(open(chemin))
        couleur = COULEURS[indice % len(COULEURS)]
        # ⚠ Pas de `-linecap` : l'option de ligne de commande n'existe pas
        # dans ImageMagick 6, et le réglage MVG `stroke-linecap` mis dans la
        # chaîne de `-draw` fait rejeter la primitive. On s'en passe, un tiret
        # à bouts carrés se lit aussi bien.
        commande += ["-stroke", couleur, "-strokewidth", str(epaisseur),
                     "-fill", "none"]
        for points in d["curves"].values():
            for segment in tirets(points):
                trace = " ".join(f"{x},{y}" for x, y in segment)
                commande += ["-draw", f"polyline {trace}"]
    commande.append(sortie)
    executer(commande)
    return sortie


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("base", help="le rendu du corps, etat moyen")
    a.add_argument("sortie")
    a.add_argument("--curve", action="append", default=[], dest="courbes",
                   help="un fichier de courbes ; repetable, une couleur par "
                        "fichier dans l'ordre")
    a.add_argument("--width", type=int, default=3, dest="epaisseur",
                   help="epaisseur du trait ; 2 sur une petite zone, ou il "
                        "cacherait ce qu'il designe")
    o = a.parse_args()
    if not o.courbes:
        raise SystemExit("rien a dessiner : donner au moins un --curve")
    print(dessiner(o.base, o.sortie, o.courbes, o.epaisseur))


if __name__ == "__main__":
    main()
