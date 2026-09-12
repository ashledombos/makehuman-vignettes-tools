#!/usr/bin/python3

"""Compose a before/after pair into one split thumbnail with an arrow.

    python3 bin/composesplit.py before.png after.png out.png
    python3 bin/composesplit.py --axis vertical before.png after.png out.png

This is the convention the target thumbnails have used since 2023: one square,
split by a dotted line, the state before the target on one side and the state
after on the other, and a filled arrow on the line pointing from one to the
other. A subtle deformation is nearly invisible on a single 256 pixel render,
and putting the two states in one image is what makes it readable at a glance.

**The split follows the shape of the subject, not the direction of the
change.** Something wide, a neck or a chest, is split horizontally, before on
top; something tall, a nose in profile, is split vertically, before on the
left. The arrow always points from before to after, so downwards or rightwards.

⚠ **The split must fall through what moves, and the middle of the image is not
that place.** The frame is centred on the centroid of the displaced vertices in
world space, which after projection does not land at the centre of the picture:
on the breast family it sits twenty pixels above the change, so the whole
deformation ended up on the "after" side and the thumbnail showed no
comparison at all. The line is therefore measured on the pair itself, by
weighting each row of the before/after difference. --measure prints that number
without composing, so a family can share one line the same way it shares one
framing: sibling thumbnails must differ by the body, never by the geometry of
the overlay.

Colours and geometry are taken from the 2023 thumbnails rather than chosen
again: the dotted line is pure orange and the arrow a soft yellow, both read
clearly against skin tones and against a transparent background, which is what
these renders have. Sampled from thumbnail_overrides/elvs_ladies_thick_neck_1.png.

Requires ImageMagick, which is why this is a separate script: the renders come
out of Blender, and Blender is a poor place to draw a dotted line.
"""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import outlineoverlay

LIGNE = "#FF6600"        # orange pur, échantillonné sur les vignettes de 2023
FLECHE = "#F3D351"       # jaune doux, idem
TIRET = 5                # longueur d'un tiret, en pixels
INTERVALLE = 4           # et de l'intervalle entre deux
LARGEUR_FLECHE = 22
HAUTEUR_FLECHE = 13


def mesurer(avant, apres, axe):
    """Where the change actually is, in pixels along the split axis.

    The difference of the two renders is collapsed onto one line and the
    centroid of that profile is returned: a robust reading, unlike the peak,
    which a stray highlight elsewhere in the frame can steal.
    """
    echelle = "1x%d!" if axe == "horizontal" else "%dx1!"
    largeur, hauteur = taille(avant)
    n = hauteur if axe == "horizontal" else largeur
    sortie = subprocess.run(
        ["convert", avant, apres, "-compose", "difference", "-composite",
         "-alpha", "off", "-colorspace", "gray", "-scale", echelle % n,
         "-depth", "8", "txt:-"],
        capture_output=True, text=True, check=True).stdout

    profil = []
    for ligne in sortie.splitlines()[1:]:
        coord, reste = ligne.split(":", 1)
        x, y = (int(v) for v in coord.split(","))
        valeur = int(reste.split("(")[1].split(")")[0].split(",")[0])
        profil.append((y if axe == "horizontal" else x, valeur))

    total = sum(v for _, v in profil)
    if not total:
        return n // 2
    return int(round(sum(p * v for p, v in profil) / total))


def taille(chemin):
    sortie = subprocess.run(["identify", "-format", "%w %h", chemin],
                            capture_output=True, text=True, check=True)
    return (int(v) for v in sortie.stdout.split())


def empiler(bas, haut, sortie, axe, miroir=False, tracer=False,
            travail="/tmp", nu=False, sans_fleche=False):
    """Two rectangular captures put together, with the overlay on the seam.

    ⭐ This, and not the cropping below, is the convention. A target thumbnail
    is made of **two renders**, each the width of the thumbnail by half its
    height, framed identically on the region the modifier moves: one capture
    with the slider low, one with it high. Each half then shows the whole
    region in its own state and the eye compares two complete pictures, where
    cropping one square render in two only shows half a body twice and hides
    whatever moves sideways.

    The frame is wide enough to hold the shoulders and a little of the elbows,
    so the zone is recognised before it is compared.
    """
    largeur, hauteur = taille(bas)
    # ⚠⚠ **Le format de la prise et l'axe de la coupe doivent être
    # complémentaires**, sinon le résultat n'est pas un carré. Une vignette
    # **est** un carré : deux prises couchées s'empilent, deux prises debout se
    # posent côte à côte. Une prise debout coupée horizontalement rend un
    # 128 × 512, et l'erreur ne se voit qu'à la livraison.
    # ⚠⚠ La garde se pose sur le RESULTAT, non sur la forme de la prise. La
    # version precedente ne testait `largeur != hauteur`, donc elle laissait
    # passer deux prises CARREES, qui donnent un rectangle de 512 x 256. Erreur
    # commise le 06-09 sur les vignettes de proxies, et rattrapee par Raphael.
    resultat = ((largeur * 2, hauteur) if axe == "vertical"
                else (largeur, hauteur * 2))
    if resultat[0] != resultat[1]:
        attendu = "vertical" if hauteur > largeur else "horizontal"
        forme = ("carree" if largeur == hauteur
                 else "debout" if hauteur > largeur else "couchee")
        conseil = (f"Une prise {forme} demande une coupe {attendu}."
                   if largeur != hauteur else
                   f"Deux prises carrees ne peuvent pas s'assembler en carre : "
                   f"il faut des prises de {largeur}x{hauteur // 2} pour une "
                   f"coupe horizontale, ou {largeur // 2}x{hauteur} pour une "
                   f"coupe verticale.")
        raise SystemExit(
            f"prise de {largeur}x{hauteur} et coupe {axe} : le resultat serait "
            f"{resultat[0]}x{resultat[1]}, donc pas carre. {conseil}")
    # ⚠ `+repage` n'est pas cosmétique. `-append` laisse une géométrie de page
    # à la taille d'une seule prise, si bien que l'image fait bien 256 × 256
    # mais se dit 256 × 128 : le premier `-flatten` d'un usager en recoupe la
    # moitié, silencieusement.
    assemble = [bas, haut, "-append" if axe == "horizontal" else "+append",
                "+repage"]
    couture = hauteur if axe == "horizontal" else largeur
    if axe == "horizontal":
        ligne, triangle = overlay(largeur, hauteur * 2, couture, axe)
    else:
        ligne, triangle = overlay(largeur * 2, hauteur, couture, axe)
    if nu:
        # ⭐ Le minimum d'habillage : deux prises, rien d'autre. Raphaël, le
        # 04-09 : « moins on met de surlignage, de pointillés, et cetera, mieux
        # c'est », et Joël avait choisi les mêmes coupes nues. Quand le
        # changement se voit tout seul, la ligne et la flèche n'ajoutent qu'un
        # obstacle de plus entre l'œil et le sujet.
        return dessiner(assemble, [], "", sortie)
    if sans_fleche:
        # ⭐ Le trait sans la flèche. Sur un curseur qui va dans **deux sens**
        # depuis un milieu, la flèche ment : elle suggère un passage d'un état
        # vers un autre, alors qu'il n'y a ni départ ni arrivée, seulement deux
        # bouts. Le trait, lui, reste nécessaire : il déclare qu'il y a deux
        # états là où le raccord serait invisible.
        return dessiner(assemble, ligne, "", sortie)
    if not tracer:
        return dessiner(assemble, ligne, triangle, sortie)

    # ⭐ La convention hybride, arbitrée le 03-09. Le contour de l'état fort
    # est posé sur **les deux moitiés** : à gauche le sein n'atteint pas la
    # courbe, à droite il l'épouse exactement. La comparaison ne demande plus
    # de mémoriser une moitié, elle se lit comme un remplissage.
    #
    # ⚠ L'état solide de gauche doit être le **faible**, non l'opposé du
    # curseur : avec les deux bouts, le contour du fort ne suit pas le bas du
    # sein faible et le pointillé paraît mal placé. Constaté sur la planche du
    # volume, où les variantes « neutre contre maximum » lisaient bien et les
    # variantes « deux bouts » non.
    masque = outlineoverlay.masque_pointille(bas, haut, travail)
    if axe == "horizontal":
        pose = ["-page", f"+0+0", masque, "-page", f"+0+{couture}", masque]
        plein = (largeur, hauteur * 2)
    else:
        pose = ["-page", f"+0+0", masque, "-page", f"+{couture}+0", masque]
        plein = (largeur * 2, hauteur)
    double = f"{travail}/_double.png"
    executer(["convert", "-size", f"{plein[0]}x{plein[1]}", "xc:black"]
             + pose + ["-background", "black", "-layers", "flatten",
                       "+repage", double])
    colore = f"{travail}/_colore.png"
    executer(["convert", "-size", f"{plein[0]}x{plein[1]}",
              f"xc:{outlineoverlay.CONTOUR}", double, "-alpha", "off",
              "-compose", "copy_opacity", "-composite", colore])
    return dessiner(assemble + [colore, "-compose", "over", "-composite"],
                    ligne, triangle, sortie)


def overlay(largeur, hauteur, couture, axe):
    """The dotted line and the arrow, in the 2023 palette and geometry."""
    if axe == "horizontal":
        ligne = [f"rectangle {x},{couture} "
                 f"{min(x + TIRET - 1, largeur - 1)},{couture}"
                 for x in range(0, largeur, TIRET + INTERVALLE)]
        # ⚠ La flèche est **centrée sur le trait**, elle ne s'y appuie pas :
        # c'est le milieu du triangle qui tombe sur la couture, la base d'un
        # côté et la pointe de l'autre. Posée pointe sur le trait, elle se lit
        # comme une marque de position au lieu d'un sens de lecture.
        moitie_fleche = HAUTEUR_FLECHE // 2
        pointe = (largeur // 2, couture + moitie_fleche)
        triangle = (f"polygon "
                    f"{pointe[0] - LARGEUR_FLECHE // 2},"
                    f"{couture - moitie_fleche} "
                    f"{pointe[0] + LARGEUR_FLECHE // 2},"
                    f"{couture - moitie_fleche} "
                    f"{pointe[0]},{pointe[1]}")
    else:
        ligne = [f"rectangle {couture},{y} "
                 f"{couture},{min(y + TIRET - 1, hauteur - 1)}"
                 for y in range(0, hauteur, TIRET + INTERVALLE)]
        moitie_fleche = HAUTEUR_FLECHE // 2
        pointe = (couture + moitie_fleche, hauteur // 2)
        triangle = (f"polygon "
                    f"{couture - moitie_fleche},"
                    f"{pointe[1] - LARGEUR_FLECHE // 2} "
                    f"{couture - moitie_fleche},"
                    f"{pointe[1] + LARGEUR_FLECHE // 2} "
                    f"{pointe[0]},{pointe[1]}")
    return ligne, triangle


def executer(commande):
    subprocess.run(commande, check=True)


def dessiner(assemble, ligne, triangle, sortie):
    if not triangle and ligne:
        commande = ["convert"] + assemble + [
            "-stroke", "none", "-fill", LIGNE, "-draw", " ".join(ligne),
            sortie]
        subprocess.run(commande, check=True)
        return sortie
    if not ligne and not triangle:
        executer(["convert"] + assemble + [sortie])
        return sortie
    # ⚠ Deux pièges d'ImageMagick, payés chacun d'un essai.
    #
    # `-draw` exige un mot-clé de primitive : un chemin nu « M x,y L … » sort
    # en erreur sans message utile. Le pointillé est donc dessiné tiret par
    # tiret plutôt que par `-strokedasharray`, ce qui donne en plus le motif
    # exact des vignettes de 2023.
    #
    # Et chaque tiret est un **rectangle rempli**, non un trait : un trait de
    # un pixel tombe sur une frontière de pixels, se répartit en demi-teinte
    # sur deux rangées, et la ligne sort grise au lieu d'orange. Un rectangle
    # aux bornes entières couvre des pixels entiers.
    commande = ["convert"] + assemble + [
        "-stroke", "none", "-fill", LIGNE,
        "-draw", " ".join(ligne),
        "-fill", FLECHE, "-draw", triangle,
        sortie,
    ]
    subprocess.run(commande, check=True)
    return sortie


def composer(avant, apres, sortie, axe, coupe=None):
    """Le repli : une seule prise carrée, coupée en deux.

    Utile quand on ne dispose que d'un rendu carré par état, mais la voie
    normale est `empiler`.
    """
    largeur, hauteur = taille(avant)
    if coupe is None:
        coupe = mesurer(avant, apres, axe)
    if axe == "horizontal":
        moitie = max(1, min(hauteur - 1, coupe))
        # La moitié haute vient de l'avant, la basse de l'après : les deux
        # rendus partagent le cadrage, donc les deux moitiés se raccordent.
        decoupe = [
            "(", avant, "-crop", f"{largeur}x{moitie}+0+0", "+repage", ")",
            "(", apres, "-crop", f"{largeur}x{hauteur - moitie}+0+{moitie}",
            "+repage", ")", "-append",
        ]
        ligne = [f"rectangle {x},{moitie} {min(x + TIRET - 1, largeur - 1)},{moitie}"
                 for x in range(0, largeur, TIRET + INTERVALLE)]
        pointe = (largeur // 2, moitie)
        triangle = (f"polygon "
                    f"{pointe[0] - LARGEUR_FLECHE // 2},"
                    f"{pointe[1] - HAUTEUR_FLECHE} "
                    f"{pointe[0] + LARGEUR_FLECHE // 2},"
                    f"{pointe[1] - HAUTEUR_FLECHE} "
                    f"{pointe[0]},{pointe[1]}")
    else:
        moitie = max(1, min(largeur - 1, coupe))
        decoupe = [
            "(", avant, "-crop", f"{moitie}x{hauteur}+0+0", "+repage", ")",
            "(", apres, "-crop", f"{largeur - moitie}x{hauteur}+{moitie}+0",
            "+repage", ")", "+append",
        ]
        ligne = [f"rectangle {moitie},{y} {moitie},{min(y + TIRET - 1, hauteur - 1)}"
                 for y in range(0, hauteur, TIRET + INTERVALLE)]
        pointe = (moitie, hauteur // 2)
        triangle = (f"polygon "
                    f"{pointe[0] - HAUTEUR_FLECHE},"
                    f"{pointe[1] - LARGEUR_FLECHE // 2} "
                    f"{pointe[0] - HAUTEUR_FLECHE},"
                    f"{pointe[1] + LARGEUR_FLECHE // 2} "
                    f"{pointe[0]},{pointe[1]}")

    # ⚠ Deux pièges d'ImageMagick, payés chacun d'un essai.
    #
    # `-draw` exige un mot-clé de primitive : un chemin nu « M x,y L … » sort
    # en erreur sans message utile. Le pointillé est donc dessiné tiret par
    # tiret plutôt que par `-strokedasharray`, ce qui donne en plus le motif
    # exact des vignettes de 2023.
    #
    # Et chaque tiret est un **rectangle rempli**, non un trait : un trait de
    # un pixel tombe sur une frontière de pixels, se répartit en demi-teinte
    # sur deux rangées, et la ligne sort grise au lieu d'orange. Un rectangle
    # aux bornes entières couvre des pixels entiers.
    commande = ["convert"] + decoupe + [
        "-stroke", "none", "-fill", LIGNE,
        "-draw", " ".join(ligne),
        "-fill", FLECHE, "-draw", triangle,
        sortie,
    ]
    subprocess.run(commande, check=True)
    return sortie


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("avant")
    a.add_argument("apres")
    a.add_argument("sortie", nargs="?")
    a.add_argument("--axis", default="horizontal",
                   choices=["horizontal", "vertical"],
                   help="horizontal pour un sujet large (cou, poitrine), "
                        "vertical pour un sujet haut (nez de profil)")
    a.add_argument("--split", default="auto",
                   help="auto (mesure sur la paire) ou un nombre de pixels, "
                        "pour donner la meme ligne a toute une famille")
    a.add_argument("--measure", action="store_true",
                   help="afficher la ligne mesuree et s'arreter")
    a.add_argument("--mirror", action="store_true",
                   help="miroiter la seconde prise, pour que les deux "
                        "silhouettes se touchent a la ligne de coupe")
    a.add_argument("--no-arrow", action="store_true", dest="sans_fleche",
                   help="le trait de separation sans la fleche : pour un "
                        "curseur qui va dans deux sens depuis un milieu")
    a.add_argument("--bare", action="store_true", dest="nu",
                   help="aucun trait ni fleche : deux prises et rien d'autre")
    a.add_argument("--outline", action="store_true",
                   help="tracer le contour de la seconde prise sur les deux "
                        "moities : convention hybride")
    a.add_argument("--stack", action="store_true",
                   help="les deux entrees sont deja les moities : les empiler "
                        "telles quelles au lieu de recadrer une prise carree")
    o = a.parse_args()
    if o.stack:
        print(empiler(o.avant, o.apres, o.sortie, o.axis, o.mirror,
                      o.outline, nu=o.nu, sans_fleche=o.sans_fleche))
        return
    if o.measure:
        print(mesurer(o.avant, o.apres, o.axis))
        return
    coupe = None if o.split == "auto" else int(o.split)
    print(composer(o.avant, o.apres, o.sortie, o.axis, coupe))


if __name__ == "__main__":
    main()
