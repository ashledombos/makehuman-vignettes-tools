#!/usr/bin/env python3
"""Epaissir la zone coloree d'une vignette, dans l'IMAGE.

    python3 epaissir-zone.py <entree.png> <sortie.png> [rayon_px]

⚠⚠ Pourquoi dans l'image et non dans la geometrie (mesure du 13-09-2026).
Deux leviers geometriques ont ete essayes et mesures, tous deux sans effet :

  - `--wire` (epaisseur du trait du nœud Wireframe) : de 0,20 a 1,00, soit
    cinq fois plus epais, l'image ne bouge pas d'un pixel visible. Ce qu'on
    voit dans une zone fine n'est pas le trait mais l'APLAT de couleur ;
  - `--paint-dilate` (dilatation de la zone le long des aretes du maillage) :
    584 sommets marques, puis 636, 668, 674 — elle SATURE. La zone des
    paupieres est un ILOT FERME du maillage : tous les voisins de ses
    sommets sont deja marques, la dilatation n'a nulle part ou aller.

Le seul levier qui reste est donc le pixel. On detecte les pixels bleus de la
vignette, on dilate ce masque de `rayon_px`, et l'on TEINTE les pixels ajoutes
plutot que de les aplatir, pour garder le modele du corps dessous.
"""
import subprocess
import sys


def epaissir(entree, sortie, rayon=2):
    # 1. le masque des pixels bleus : le canal bleu domine nettement le rouge.
    #    Un simple seuil sur (B - R) suffit et resiste a l'eclairage, la peau
    #    porcelaine etant quasi neutre (R proche de B).
    subprocess.run([
        "convert", entree, "-alpha", "off",
        "-channel", "B", "-separate", "+channel", "/tmp/_b.png"], check=True)
    subprocess.run([
        "convert", entree, "-alpha", "off",
        "-channel", "R", "-separate", "+channel", "/tmp/_r.png"], check=True)
    subprocess.run([
        "convert", "/tmp/_b.png", "/tmp/_r.png", "-compose", "minus_src",
        "-composite", "-threshold", "12%", "/tmp/_masque.png"], check=True)

    # 2. le masque dilate
    subprocess.run([
        "convert", "/tmp/_masque.png", "-morphology", "Dilate",
        "Disk:%d" % rayon, "/tmp/_masque_gros.png"], check=True)

    # 3. la teinte a poser : celle des pixels deja bleus, moyennee, pour que
    #    l'epaississement ne jure pas avec l'existant.
    teinte = subprocess.run([
        "convert", entree, "-alpha", "off", "/tmp/_masque.png",
        "-compose", "CopyOpacity", "-composite",
        "-scale", "1x1!", "-alpha", "off",
        "-format", "%[pixel:p{0,0}]", "info:"],
        capture_output=True, check=True).stdout.decode().strip()

    # 4. teinter les pixels du masque elargi, en gardant le modele : on
    #    multiplie l'image par la teinte plutot que de la remplacer.
    subprocess.run([
        "convert", entree, "-alpha", "off",
        "(", "+clone", "-fill", teinte, "-colorize", "70%", ")",
        "/tmp/_masque_gros.png", "-composite", sortie], check=True)
    print("epaissi de %d px, teinte %s : %s" % (rayon, teinte, sortie))


if __name__ == "__main__":
    entree = sys.argv[1]
    sortie = sys.argv[2]
    rayon = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    epaissir(entree, sortie, rayon)
