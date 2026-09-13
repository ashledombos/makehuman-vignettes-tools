#!/usr/bin/env python3
"""Mesurer une vignette d'epure APLATIE SUR NOIR. Sans numpy ni PIL : on lit
les octets RGBA que `convert` produit.

  corps    : mediane de la luminance des pixels clairs du sujet
  encre    : mediane des pixels sombres du sujet (les aretes)
  ecart    : corps - encre, la lisibilite de la trame
  brule    : part du sujet a 255, ce qui dit si l'on a perdu le modele
  contour  : luminance mediane de la bande d'un pixel au bord du sujet

⚠ Sur fond noir la silhouette ne peut pas manquer si le corps est clair ; ce
   qui peut manquer, c'est la trame. D'ou l'ecart comme mesure principale.
"""
import sys
import glob
import os
import subprocess


def lire(chemin):
    out = subprocess.run(["convert", chemin, "-depth", "8", "rgba:-"],
                         capture_output=True, check=True).stdout
    dims = subprocess.run(["identify", "-format", "%w %h", chemin],
                          capture_output=True, check=True).stdout.split()
    w, h = int(dims[0]), int(dims[1])
    assert len(out) == w * h * 4, "taille inattendue"
    return out, w, h


def mediane(liste):
    if not liste:
        return 0.0
    tri = sorted(liste)
    return float(tri[len(tri) // 2])


def mesurer(chemin):
    octets, w, h = lire(chemin)
    lum = [0.0] * (w * h)
    sujet = [False] * (w * h)
    for i in range(w * h):
        r, g, b, a = octets[4 * i:4 * i + 4]
        f = a / 255.0
        lum[i] = (0.2126 * r + 0.7152 * g + 0.0722 * b) * f
        sujet[i] = a > 229
    valeurs = [lum[i] for i in range(w * h) if sujet[i]]
    if len(valeurs) < 100:
        return None
    tri = sorted(valeurs)
    seuil = tri[int(0.35 * len(tri))]
    encre = [v for v in valeurs if v <= seuil]
    corps = [v for v in valeurs if v > seuil]
    bande = []
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            i = y * w + x
            if not sujet[i]:
                continue
            if not (sujet[i - 1] and sujet[i + 1]
                    and sujet[i - w] and sujet[i + w]):
                bande.append(lum[i])
    mc, me = mediane(corps), mediane(encre)
    return {
        "corps": mc,
        "encre": me,
        "ecart": mc - me,
        "brule": 100.0 * sum(1 for v in valeurs if v >= 254) / len(valeurs),
        "contour": mediane(bande),
        "part": 100.0 * len(valeurs) / (w * h),
    }


if __name__ == "__main__":
    print("%-52s %6s %6s %6s %6s %7s" %
          ("", "corps", "encre", "ecart", "brule", "contour"))
    for motif in sys.argv[1:]:
        for chemin in sorted(glob.glob(motif)):
            m = mesurer(chemin)
            etiquette = os.path.join(
                os.path.basename(os.path.dirname(chemin)),
                os.path.basename(chemin))[:52]
            if m is None:
                print("%-52s VIDE" % etiquette)
                continue
            print("%-52s %6.1f %6.1f %6.1f %5.1f%% %7.1f" %
                  (etiquette, m["corps"], m["encre"], m["ecart"],
                   m["brule"], m["contour"]))
