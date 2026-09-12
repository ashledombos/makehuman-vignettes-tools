#!/usr/bin/python3

"""Draw the silhouette of one state as a dotted outline over the other.

    python3 bin/outlineoverlay.py before.png after.png out.png

The split thumbnail puts two states side by side and lets the eye compare them.
That works when the change alters shading over a wide area, and it fails when
the change is small or purely a matter of volume: the two halves then look like
the same picture twice, which is worse than no thumbnail, because it promises a
difference and does not deliver one.

This is the other way round. One state is shown solid, the other as a **dotted
outline drawn on top of it**, so the difference is not remembered from one half
to the other, it is *seen in one place*. The original MakeHuman slider icons
used the same device, hand drawn.

⚠ **It only works where the change is on the silhouette.** A breast seen from
the front has its volume in the shading, not in the outline, so nothing useful
can be traced; seen in profile the same volume *is* the outline. The camera
angle and this overlay are therefore one decision, not two.

The outline is clipped to where the silhouette actually moved, dilated a
little: tracing the whole body would draw a dotted line down the arm and the
belly, where nothing happens, and the eye would have to hunt for the part that
matters.
"""

import argparse
import subprocess
import sys

CONTOUR = "#FF6600"     # le pointillé des vignettes de 2023
CONTOUR_BAS = "#F3D351"  # ⭐ la seconde couleur, celle des vignettes livrées
                         # par MPFB : orange pour un bout du curseur, jaune
                         # pour l'autre. Convention retrouvée dans
                         # data/targets/_images, non inventée ici.
EPAISSEUR = 2           # en pixels : un contour de 1 px se perd sur la peau
MARGE = 6               # dilatation du masque de changement, en pixels
LISSAGE_REGION = 3      # flou appliqué à la région avant seuil : son bord
                        # suit les arêtes du maillage et sort en escalier
TIRET = 5               # motif du pointillé, comme la ligne de coupe
INTERVALLE = 4


def executer(commande):
    subprocess.run(commande, check=True)


def masque_de_pointilles(largeur, hauteur, chemin):
    """Des bandes obliques, qui serviront à trouer le contour continu.

    Pointiller une courbe est autrement plus pénible que pointiller une droite,
    et `-strokedasharray` ne s'applique pas à un contour extrait d'une image.
    Le détour qui marche : dessiner le contour plein, puis le masquer par une
    grille de bandes. La courbe reçoit ainsi son pointillé sans qu'on ait à la
    parcourir.

    ⚠ **Les bandes sont obliques, non verticales.** Un masque vertical ne coupe
    que ce qui est horizontal : sur le flanc d'un sein vu de profil, où le
    contour est presque vertical, les tirets fusionnent en un long trait et le
    pointillé disparaît. À 45°, une courbe est découpée quelle que soit son
    orientation, sauf sur le seul segment qui suit exactement la diagonale.

    ⚠ **Le motif se met à l'échelle de la prise.** Un damier a été essayé
    d'abord, pour n'avoir aucune orientation privilégiée, et il rend moins bien
    : il ampute la courbe au lieu de la pointiller. Le vrai défaut n'était pas
    l'orientation mais la taille : une prise en portrait ne fait que la moitié
    de la largeur d'une vignette, si bien qu'un motif calibré pour 256 pixels y
    mange le double et que les tirets paraissent « très écartés ».
    """
    petit = min(largeur, hauteur)
    tiret = max(3, round(TIRET * petit / 256.0))
    intervalle = max(2, round(INTERVALLE * petit / 256.0))
    pas = tiret + intervalle
    bandes = [f"line {x},0 {x + hauteur},{hauteur}"
              for x in range(-hauteur, largeur + pas, pas)]
    executer(["convert", "-size", f"{largeur}x{hauteur}", "xc:black",
              "-stroke", "white", "-strokewidth", str(tiret),
              "-fill", "none", "-draw", " ".join(bandes), chemin])
    return chemin


def masque_pointille(solide, tracee, travail="/tmp", bords=False,
                     region=None, suffixe="", epaisseur=None, contre=None):
    """Le pointillé prêt à colorier : contour ∩ zone de changement ∩ tirets.

    Sorti de `superposer` pour être réutilisable : la convention hybride pose
    ce même masque sur **les deux moitiés** d'une paire, si bien que l'état
    faible n'atteint pas la courbe et que l'état fort l'épouse exactement.
    """
    epaisseur = EPAISSEUR if epaisseur is None else epaisseur
    # ⚠ La zone de changement se mesure contre l'état que l'on compare, qui
    # n'est pas toujours l'état solide. Avec deux courbes, elle vaut d'un bout
    # du curseur à l'autre : mesurée contre le neutre, la courbe du bout faible
    # est tronquée à presque rien, puisque le faible ressemble au neutre.
    contre = solide if contre is None else contre
    contour = f"{travail}/_contour{suffixe}.png"
    changement = f"{travail}/_changement{suffixe}.png"
    pointilles = f"{travail}/_pointilles{suffixe}.png"
    final = f"{travail}/_final{suffixe}.png"

    dimensions = subprocess.run(
        ["identify", "-format", "%w %h", solide],
        capture_output=True, text=True, check=True).stdout.split()
    largeur, hauteur = (int(v) for v in dimensions)

    # Le contour de l'état à tracer.
    #
    # Par défaut, le bord de son canal alpha : c'est le vrai contour du corps,
    # net et sans réglage. ⚠ Il n'existe que si le changement est sur la
    # silhouette. Vu de face, l'écartement des seins ne l'est pas du tout : le
    # bord du sein n'est qu'une limite d'ombrage sur une surface continue, et
    # le tracé par l'alpha ne dessine alors que le bord du bras, ce qui est
    # inutile. D'où `bords`, qui détecte le contour **dans l'ombrage** du
    # rendu. Moins net, mais c'est le seul contour disponible de face.
    if region:
        # Le contour de la région peinte par la passe de géométrie : un seuil
        # sur un masque net, sans réglage à deviner.
        #
        # ⚠ Le fond s'aplatit sur du **noir**. `-alpha remove` compose sur le
        # blanc par défaut, ce qui rend le fond clair et le corps sombre : le
        # seuil dessine alors toute la silhouette du corps, un contour qui
        # n'existe pas dans la région.
        #
        # ⚠ Et la région est floutée avant le seuil : peinte par sommet, son
        # bord suit les arêtes du maillage et sort en escalier polygonal.
        executer(["convert", region, "-background", "black", "-alpha",
                  "remove", "-colorspace", "gray",
                  "-blur", f"0x{LISSAGE_REGION}", "-threshold", "50%",
                  "-morphology", "edgeout", "diamond:1",
                  "-morphology", "dilate", f"disk:{max(1, epaisseur - 1)}",
                  "-threshold", "50%", contour])
    elif bords:
        executer(["convert", tracee, "-alpha", "remove", "-colorspace", "gray",
                  "-blur", "0x1", "-canny", "0x1+8%+20%",
                  "-morphology", "dilate", f"disk:{max(1, epaisseur - 1)}",
                  "-threshold", "50%", contour])
    else:
        executer(["convert", tracee, "-alpha", "extract",
                  "-morphology", "edgeout", "diamond:1",
                  "-morphology", "dilate", f"disk:{max(1, epaisseur - 1)}",
                  "-threshold", "50%", contour])

    # Où le changement se voit. Sur la silhouette, la différence des deux
    # canaux alpha suffit ; dans l'ombrage, il faut la différence des images.
    if region:
        # Toute la région compte, puisque c'est elle que l'on trace.
        executer(["convert", region, "-background", "black", "-alpha",
                  "remove", "-colorspace", "gray",
                  "-blur", f"0x{LISSAGE_REGION}", "-threshold", "50%",
                  "-morphology", "dilate", f"disk:{MARGE}", changement])
    elif bords:
        executer(["convert", contre, "-alpha", "remove", tracee,
                  "-alpha", "remove", "-compose", "difference", "-composite",
                  "-colorspace", "gray", "-threshold", "4%",
                  "-morphology", "close", "disk:2",
                  "-morphology", "dilate", f"disk:{MARGE}", changement])
    else:
        executer(["convert", contre, "-alpha", "extract", "(", tracee,
                  "-alpha", "extract", ")", "-compose", "difference",
                  "-composite", "-threshold", "10%",
                  "-morphology", "dilate", f"disk:{MARGE}", changement])

    masque_de_pointilles(largeur, hauteur, pointilles)

    # Contour ∩ zone de changement ∩ pointillé.
    executer(["convert", contour, changement, "-compose", "multiply",
              "-composite", pointilles, "-compose", "multiply",
              "-composite", final])

    return final


def poser(base, masque, couleur, largeur, hauteur, sortie):
    """Un masque de pointillés colorié et posé sur une image."""
    executer(["convert", base,
              "(", "-size", f"{largeur}x{hauteur}", f"xc:{couleur}",
              masque, "-alpha", "off", "-compose", "copy_opacity",
              "-composite", ")",
              "-compose", "over", "-composite", sortie])
    return sortie


def superposer(solide, tracee, sortie, travail="/tmp", bords=False,
               region=None, aussi=None, epaisseur=None,
               couleur=None, couleur2=None):
    dimensions = subprocess.run(
        ["identify", "-format", "%w %h", solide],
        capture_output=True, text=True, check=True).stdout.split()
    largeur, hauteur = (int(v) for v in dimensions)
    final = masque_pointille(solide, tracee, travail, bords, region,
                             epaisseur=epaisseur, contre=aussi)
    base = solide
    if aussi:
        # ⭐ Les deux bouts du curseur, chacun dans sa couleur, sur un fond
        # neutre. C'est ce que font les vignettes livrées par MPFB, et cela
        # supprime la coupe : une seule image, deux courbes, aucun état à
        # mémoriser.
        autre = masque_pointille(solide, aussi, travail, bords, None,
                                 suffixe="2", epaisseur=epaisseur,
                                 contre=tracee)
        base = poser(solide, autre, couleur2 or CONTOUR_BAS, largeur, hauteur,
                     f"{travail}/_base.png")
    return poser(base, final, couleur or CONTOUR, largeur, hauteur, sortie)


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("solide", help="l'etat rendu en dur")
    a.add_argument("tracee", help="l'etat dont on trace la silhouette")
    a.add_argument("sortie")
    a.add_argument("--region", default=None,
                   help="la passe de region rendue par rendertargetthumbs, "
                        "dont on trace le bord")
    a.add_argument("--colour", default=None, dest="couleur",
                   help="couleur du contour du bout fort")
    a.add_argument("--colour2", default=None, dest="couleur2",
                   help="couleur du contour du bout faible")
    a.add_argument("--also", default=None, dest="aussi",
                   help="un second etat a tracer, dans la seconde couleur : "
                        "les deux bouts du curseur en une seule image")
    a.add_argument("--width", type=int, default=None, dest="epaisseur",
                   help="epaisseur du pointille en pixels")
    a.add_argument("--edges", action="store_true", dest="bords",
                   help="tracer le contour lu dans l'ombrage, et non sur le "
                        "canal alpha : indispensable de face")
    o = a.parse_args()
    print(superposer(o.solide, o.tracee, o.sortie, bords=o.bords,
                     region=o.region, aussi=o.aussi,
                     epaisseur=o.epaisseur, couleur=o.couleur,
                     couleur2=o.couleur2))


if __name__ == "__main__":
    main()
