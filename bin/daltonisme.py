#!/usr/bin/env python3
"""La zone bleue tient-elle pour un daltonien ?

⚠ Le canon garde une lecon sur ce point : rose/cyan etait plus lisible a l'oeil
et inutilisable, sa distance tombant de 215 a 55 en deuteranopie. Une couleur
se simule, elle ne se choisit pas a l'oeil.

Simulation de Brettel-Vienot-Mollon par matrices sur RGB lineaire, les trois
formes : protanopie (rouge absent), deuteranopie (vert absent), tritanopie
(bleu absent). On mesure ensuite la meme chose que sur l'original : la part de
pixels dont la zone se distingue du corps, et l'ecart de luminance zone/corps.
"""
import sys
import subprocess

MATRICES = {
    "normal": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "protanopie": ((0.170556992, 0.829443014, 0),
                   (0.170556991, 0.829443008, 0),
                   (-0.004517144, 0.004517144, 1)),
    "deuteranopie": ((0.33066007, 0.66933993, 0),
                     (0.33066007, 0.66933993, 0),
                     (-0.02785538, 0.02785538, 1)),
    "tritanopie": ((1, 0.1273989, -0.1273989),
                   (0, 0.8739093, 0.1260907),
                   (0, 0.8739093, 0.1260907)),
}


def vers_lineaire(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def vers_srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def lire(chemin):
    out = subprocess.run(["convert", chemin, "-alpha", "remove",
                          "-depth", "8", "rgb:-"],
                         capture_output=True, check=True).stdout
    return out


def mesurer(octets, forme):
    m = MATRICES[forme]
    n = len(octets) // 3
    colores = 0
    sujet = 0
    ecarts = []
    for i in range(n):
        r, g, b = (vers_lineaire(v) for v in octets[3 * i:3 * i + 3])
        rr = m[0][0] * r + m[0][1] * g + m[0][2] * b
        gg = m[1][0] * r + m[1][1] * g + m[1][2] * b
        bb = m[2][0] * r + m[2][1] * g + m[2][2] * b
        R, G, B = (255 * vers_srgb(v) for v in (rr, gg, bb))
        if max(R, G, B) < 20:      # le fond noir
            continue
        sujet += 1
        e = max(R, G, B) - min(R, G, B)
        if e > 25:
            colores += 1
            ecarts.append(e)
    return (100.0 * colores / max(sujet, 1),
            sum(ecarts) / len(ecarts) if ecarts else 0.0)


if __name__ == "__main__":
    print("%-44s %-13s %8s %9s" % ("image", "vision", "part %", "ecart RGB"))
    for chemin in sys.argv[1:]:
        octets = lire(chemin)
        for forme in ("normal", "protanopie", "deuteranopie", "tritanopie"):
            part, ecart = mesurer(octets, forme)
            print("%-44s %-13s %7.2f%% %9.1f"
                  % (chemin.split("/")[-1][:44], forme, part, ecart))
