#!/usr/bin/env python3
"""Les 17 cibles des yeux, recadrees sur la ZONE ENTIERE.

⭐ Regle posee par Raphael le 17-09 : montrer un seul oeil ne gene pas quand les
deux subissent le meme changement, mais une zone qui sort du cadre, si, parce
qu'on ne voit plus son etendue. La zone d'impact prime donc sur le gros plan.

Consequence : meme regle que les autres familles, cadre = 2 x spread x 1,25 sur
la visee sondee, sans decalage vers un oeil. Neuf des dix-sept debordaient avec
la visee de famille et la largeur de la table.
"""
import json
import os
import sys

A = "/var/home/soleil/travail-makehuman"
sys.argv = ["x"]
exec(open(f"{A}/bin/lot6-familles.py").read().replace("\nmain()\n", "\n"))

FAMILLE = "face02"
SORTIE_YEUX = f"{A}/vignettes/face02-v2"
os.makedirs(SORTIE_YEUX, exist_ok=True)
dossier = f"{SORTIE_YEUX}/rendus"
sonde = f"{dossier}/sonde"
os.makedirs(sonde, exist_ok=True)

lignes = []
for f in sorted(os.listdir(f"{CIB}/{FAMILLE}")):
    nom = f.replace(".target", "")
    cible = f"{CIB}/{FAMILLE}/{f}"
    rendre(cible, sonde, 0.30, 22.0, "--refine", "", False)
    try:
        j = json.load(open(f"{sonde}/framing.json"))[nom]
    except (KeyError, FileNotFoundError):
        lignes.append(f"ECHEC-SONDE {nom}")
        print(lignes[-1], flush=True)
        continue
    x, y, z = j["look_at"]
    largeur = max(2.0 * j["spread_m"] * 1.25, 0.035)
    gp = largeur < 0.12
    extra = f"--lens 400 --rect" if gp else "--rect"
    visee = f"{x:.4f},{y:.4f},{z:.4f}"
    rendre(cible, dossier, largeur, 22.0, f"--look-at={visee}", extra, gp)
    masque = masque_de(dossier, nom)
    avant, apres = f"{dossier}/{nom}-before.png", f"{dossier}/{nom}.png"
    if not (masque and os.path.exists(avant) and os.path.exists(apres)):
        lignes.append(f"ECHEC-RENDU {nom}")
        print(lignes[-1], flush=True)
        continue
    cov = couverture(masque)
    if touche_un_bord(masque):
        largeur2 = largeur * 1.45
        gp2 = largeur2 < 0.12
        extra2 = f"--lens 400 --rect" if gp2 else "--rect"
        rendre(cible, dossier, largeur2, 22.0, f"--look-at={visee}", extra2, gp2)
        m2 = masque_de(dossier, nom)
        if m2 and not touche_un_bord(m2):
            largeur, masque, cov = largeur2, m2, couverture(m2)
    bord = " DEBORDE" if touche_un_bord(masque) else ""
    teinter(avant, masque, f"{dossier}/T-{nom}-avant.png")
    teinter(apres, masque, f"{dossier}/T-{nom}-apres.png")
    sh(f"python3 {A}/bin/composesplit.py --stack --axis horizontal "
       f"{dossier}/T-{nom}-avant.png {dossier}/T-{nom}-apres.png "
       f"{SORTIE_YEUX}/vignette-{nom}.png")
    sh(f"magick {SORTIE_YEUX}/vignette-{nom}.png -background black "
       f"-alpha remove -alpha off {SORTIE_YEUX}/vignette-{nom}.png")
    lignes.append(f"face02 {nom} cadre {largeur:.3f} tache {cov*100:.1f}%{bord}")
    print(lignes[-1], flush=True)

open(f"{SORTIE_YEUX}/journal.txt", "w").write("\n".join(lignes) + "\n")
sh(f"rm -f {OUT}/_b.png {OUT}/_a.png {OUT}/_col.png")
sh(f"cd {SORTIE_YEUX} && magick montage -label '%t' $(ls vignette-*.png | sort) "
   f"-tile 6x3 -geometry 210x210+5+5 -background '#222' -fill white "
   f"-pointsize 10 planche.png")
print("YEUX-V2-FINI", len([f for f in os.listdir(SORTIE_YEUX)
                           if f.startswith("vignette-")]))
