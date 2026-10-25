#!/usr/bin/env python3
"""Lot 6, les quatre familles restantes : bouche, oreilles, poitrine, machoire.

Diptyque avant/apres, avec la tache de zone, comme la famille des yeux.

⭐ La visee ne se devine pas par famille, elle se MESURE par cible : une sonde a
cadre large avec `--refine` donne le centre et l'etendue de la zone, et le cadre
definitif s'en deduit. C'est ce qui a sauve les cinq cibles des yeux dont la
tache sortait vide : leur zone tombait hors d'un cadre vise sur l'oeil.

⚠ La mesure du masque est aussi le CONTROLE du cadrage : une tache vide veut
dire, presque toujours, que la zone est hors champ. Les rares exceptions sont
les cibles qui deplacent des sommets sous la surface.

⚠⚠ `spread_m` est un RAYON autour du centre de la zone, pas sa largeur : le
moteur lui-meme cadre a `2 * etendue * CONTEXTE`. Un cadre pose a
`spread * 1.5` valait donc la moitie du necessaire, et la zone debordait du
cadre sans qu'on voie son etendue. Le cadre vaut `2 * spread * marge`, et une
seconde passe elargit encore si la tache touche un bord.
"""
import json
import math
import os
import subprocess

A = "/var/home/soleil/travail-makehuman"
CIB = f"{A}/cibles-communaute"
OUT = f"{A}/vignettes/lot6"
BLEU = "#0072B2"

# famille : (azimut, prise, axe de montage, decalage x de la visee)
# ⚠ Les oreilles se prennent de PROFIL : de face elles sont vues par la tranche.
# Ces cibles ne sont pas des asymetries, donc rien n'impose d'y voir les deux.
FAMILLES = {
    "face03": (22.0, "--rect", "horizontal", 0.0),
    "face04": (90.0, "--portrait", "vertical", 0.0),
    "breast03": (25.0, "--rect", "horizontal", 0.0),
    "face01": (22.0, "--rect", "horizontal", 0.0),
}
# Cibles qui transforment le CORPS ENTIER malgre leur rangement : cadre large.
CORPS_ENTIER = {"titleknown_great_soft_jelly_thing_from_i_have_no_mouth_and_i_must_scream",
                "jujube_male_fixed_nipples"}
PRESETS = None


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def presets():
    global PRESETS
    if PRESETS is None:
        r = sh(f". {A}/bin/vignettes-presets.sh && "
               "echo \"$LUM_FACE\"; echo \"$MONDE_FACE\"; echo \"$LUM_PROFIL\"; "
               "echo \"$MONDE_PROFIL\"; echo \"$PEAU_CLAIRE\"; "
               "echo \"$PEAU_CLAIRE_GROS_PLAN\"")
        PRESETS = r.stdout.strip().split("\n")
    return PRESETS


def rendre(cible, dossier, largeur, azimut, cadre, extra, gros_plan):
    lf, mf, lp, mp, peau, peau_gp = presets()
    lum, monde = (lp, mp) if azimut >= 60 else (lf, mf)
    p = peau_gp if gros_plan else peau
    cmd = (f"flatpak run --command=blender org.blender.Blender -b "
           f"{A}/studio_base.blend -P {A}/bin/rendertargetthumbs.py -- "
           f"--target {cible} --who female --size 256 --hide-inner --fstop 0 "
           f"--samples {'512' if extra else '96'} --width {largeur} "
           f"--azimuth {azimut} {cadre} {extra} --region --region-graded "
           f"--lights '{lum}' --world {monde} --skin-tune '{p}' "
           f"--out {dossier}")
    r = sh(cmd)
    if r.returncode:
        print(f"   !! rendu code {r.returncode}", flush=True)
    return r


def masque_de(dossier, nom):
    f = f"{dossier}/{nom}-region.png"
    return f if os.path.exists(f) else None


def couverture(masque):
    return float(sh(f"magick {masque} -alpha off -colorspace gray "
                    f"-threshold 5% -format '%[fx:mean]' info:").stdout or 0)


def touche_un_bord(masque):
    """La tache sort-elle du cadre ? Sa boite touche alors un bord de l'image."""
    b = sh(f"magick {masque} -alpha off -colorspace gray -threshold 5% "
           f"-format '%@' info:").stdout.strip()
    if not b or "x" not in b:
        return False
    l, reste = b.split("x")
    h, x, y = reste.replace("+", " ").split()
    l, h, x, y = int(l), int(h), int(x), int(y)
    return x <= 1 or y <= 1 or x + l >= 255 or y + h >= 255


def teinter(src, masque, dest):
    sh(f"magick {src} -background black -alpha remove -alpha off {OUT}/_b.png")
    sh(f"magick {OUT}/_b.png -fill '{BLEU}' -colorize 100 {OUT}/_a.png")
    sh(f"magick {OUT}/_b.png {OUT}/_a.png -compose Colorize -composite "
       f"-evaluate multiply 0.78 {OUT}/_col.png")
    sh(f"magick {OUT}/_b.png {OUT}/_col.png {masque} -alpha off -composite {dest}")


def main():
    os.makedirs(OUT, exist_ok=True)
    lignes = []
    for famille, (azimut, prise, axe, dx) in FAMILLES.items():
        dossier = f"{OUT}/{famille}"
        sonde = f"{dossier}/sonde"
        os.makedirs(sonde, exist_ok=True)
        for f in sorted(os.listdir(f"{CIB}/{famille}")):
            nom = f.replace(".target", "")
            cible = f"{CIB}/{famille}/{f}"
            entier = nom in CORPS_ENTIER
            # --- la sonde : ou est la zone, et quelle taille fait-elle ---
            rendre(cible, sonde, 1.8 if entier else 0.30, azimut,
                   "--refine", "", False)
            try:
                j = json.load(open(f"{sonde}/framing.json"))[nom]
            except (KeyError, FileNotFoundError):
                lignes.append(f"ECHEC-SONDE {famille} {nom}")
                print(lignes[-1], flush=True)
                continue
            x, y, z = j["look_at"]
            etendue = j["spread_m"]
            largeur = 1.8 if entier else max(2.0 * etendue * 1.25, 0.035)
            gp = largeur < 0.12
            extra = f"--lens 400 {prise}" if (gp and not entier) else prise
            visee = f"{x + dx:.4f},{y:.4f},{z:.4f}"
            rendre(cible, dossier, largeur, azimut, f"--look-at={visee}",
                   extra, gp)
            masque = masque_de(dossier, nom)
            avant = f"{dossier}/{nom}-before.png"
            apres = f"{dossier}/{nom}.png"
            if not (masque and os.path.exists(avant) and os.path.exists(apres)):
                lignes.append(f"ECHEC-RENDU {famille} {nom}")
                print(lignes[-1], flush=True)
                continue
            cov = couverture(masque)
            if not entier and touche_un_bord(masque):
                largeur2 = largeur * 1.45
                gp2 = largeur2 < 0.12
                extra2 = f"--lens 400 {prise}" if gp2 else prise
                rendre(cible, dossier, largeur2, azimut,
                       f"--look-at={visee}", extra2, gp2)
                m2 = masque_de(dossier, nom)
                if m2 and not touche_un_bord(m2):
                    largeur, masque, cov = largeur2, m2, couverture(m2)
            teinter(avant, masque, f"{dossier}/T-{nom}-avant.png")
            teinter(apres, masque, f"{dossier}/T-{nom}-apres.png")
            sh(f"python3 {A}/bin/composesplit.py --stack --axis {axe} "
               f"{dossier}/T-{nom}-avant.png {dossier}/T-{nom}-apres.png "
               f"{OUT}/vignette-{nom}.png")
            sh(f"magick {OUT}/vignette-{nom}.png -background black "
               f"-alpha remove -alpha off {OUT}/vignette-{nom}.png")
            lignes.append(f"{famille} {nom} cadre {largeur:.3f} "
                          f"tache {cov*100:.1f}%")
            print(lignes[-1], flush=True)

    open(f"{OUT}/journal.txt", "w").write("\n".join(lignes) + "\n")
    sh(f"rm -f {OUT}/_b.png {OUT}/_a.png {OUT}/_col.png")
    sh(f"cd {OUT} && magick montage -label '%t' $(ls vignette-*.png | sort) "
       f"-tile 6x5 -geometry 200x200+5+5 -background '#222' -fill white "
       f"-pointsize 10 planche.png")
    n = len([f for f in os.listdir(OUT) if f.startswith("vignette-")])
    print(f"LOT6-FAMILLES-FINI {n}")


main()
