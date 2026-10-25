#!/usr/bin/env python3
"""Huit retouches vues par Raphael en regardant les icones une par une.

La planche de contact les avait masquees : a 200 pixels on juge la tache, pas
le cadre. ⭐ Une planche sert a comparer, pas a recevoir ; le jugement final se
fait sur l'image seule, a sa taille.

- les quatre oreilles : cadre elargi, elles touchaient les bords de l'image ;
- `asymm-trunk-1` : la tache est aux EPAULES et sortait par le haut pendant que
  le bas du cadre montrait un ventre que la cible ne touche pas. Visee remontee
  et cadre ouvert pour tenir les epaules entieres ;
- `asym-brown-2` : tache aux coins du front, coupee par le haut ;
- `asym-eye-1` et `-2` : a x2 le globe traversait la paupiere. Ramenes a x1 :
  ces deux-la deplacent assez pour se passer d'exageration.
"""
import os
import sys

A = "/var/home/soleil/travail-makehuman"
sys.argv = ["x"]
exec(open(f"{A}/bin/asym-v7.py").read().replace("if __name__", "if 0 and __name__"))

# curseur : (largeur, amplitude, visee)
RETOUCHES = {
    "asym-ear-1": (0.21, 2.0, ""),
    "asym-ear-2": (0.21, 1.0, ""),
    "asym-ear-3": (0.21, 2.0, ""),
    "asym-ear-4": (0.21, 4.0, ""),
    "asymm-trunk-1": (0.52, 1.0, "0.0,-0.1846,1.3300"),
    "asym-brown-2": (0.13, 2.0, "0.0,-0.1049,1.5230"),
    "asym-eye-1": (0.11, 1.0, ""),
    "asym-eye-2": (0.11, 1.0, ""),
}

d = f"{BRUT}/retouches"
os.makedirs(d, exist_ok=True)
for curseur, (largeur, amplitude, visee) in RETOUCHES.items():
    AMPLITUDES[curseur] = amplitude
    corps, masque = rendre(curseur, largeur, visee, d)
    if not masque:
        print(f"ECHEC {curseur}", flush=True)
        continue
    cov, _ = mesurer(masque)
    composer(corps, masque, f"{SORTIE}/{curseur}-l-r.png")
    print(f"{curseur} cadre {largeur} x{amplitude} couverture {cov*100:.1f}%",
          flush=True)

os.chdir(SORTIE)
sh("magick montage -label '%t' $(ls *-l-r.png | sort) -tile 6x6 "
   "-geometry 200x200+5+5 -background '#222' -fill white -pointsize 12 "
   "planche-v7.png")
print("RETOUCHES-FINI")
