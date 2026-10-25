#!/usr/bin/env python3
"""Les cinq cibles du globe en tache fil de fer, globes masques (12-10).

Les globes sont des maillages attaches sans cle de forme : ils gardent leur
taille quand la cible change l'orbite, et semblent sortir de la paupiere. La
cible vise la forme des paupieres, on la montre donc sans eux (--hide-eyes).

Cadre des deux yeux de lot6-globe.py (width 0.13, azimut 22), dispositif fil
de fer de lot6-yeux-reste-face.py, un pochoir par etat (regle du 29-09).
"""
import os
import sys

A = "/var/home/soleil/travail-makehuman"
sys.argv = ["x"]
exec(open(f"{A}/bin/lot6-familles.py").read().replace("\nmain()\n", "\n"))

O = f"{A}/vignettes/lot6-globe-fil"
sh(f"rm -rf {O}")
os.makedirs(O)
LF, MF, LP, MP, PEAU, PEAU_GP = presets()
BLEU = "#0072B2"
VISEE = "0.0,-0.139,1.492"
CIBLES = ["elvs_very_large_eyes1", "jujube_eyeballs_grow",
          "jujube_eyeballs_shrink", "jujube_eyes_in", "jujube_eyes_out"]

lignes = []
for nom in CIBLES:
    cible = f"{CIB}/face02/{nom}.target"
    dossier = f"{O}/{nom}"
    paire = {}
    for amp, tag in (("0.0001", "a"), ("1.0", "b")):
        d = f"{dossier}/{tag}"
        os.makedirs(d, exist_ok=True)
        sh(f"flatpak run --command=blender org.blender.Blender -b "
           f"{A}/studio_base.blend -P {A}/bin/rendertargetthumbs.py -- "
           f"--target {cible} --who female --size 1024 --rect --hide-inner "
           f"--hide-eyes --fstop 0 --samples 256 --width 0.13 --lens 400 "
           f"--azimuth 22 --look-at={VISEE} --amounts {amp} "
           f"--wire --wire-thickness 0.00016 --region --region-graded "
           f"--lights '{LF}' --world {MF} --skin-tune '{PEAU_GP}' --out {d}")
        fs = os.listdir(d)
        base = [f for f in fs if f.endswith(".png") and "-fil" not in f
                and "-region" not in f and "-before" not in f]
        fil = [f for f in fs if f.endswith("-fil.png")]
        reg = [f for f in fs if f.endswith("-region.png")]
        if base and fil and reg:
            paire[tag] = (f"{d}/{base[0]}", f"{d}/{fil[0]}", f"{d}/{reg[0]}")
    if len(paire) < 2:
        lignes.append(f"ECHEC {nom}")
        print(lignes[-1], flush=True)
        continue
    for tag in ("a", "b"):
        base, fil, reg = paire[tag]
        sh(f"magick {fil} -colorspace gray -resize 256x128! {O}/_f.png")
        sh(f"magick {reg} -colorspace gray -resize 256x128! {O}/_z.png")
        sh(f"magick {O}/_f.png {O}/_z.png -compose multiply -composite {O}/_fz.png")
        sh(f"magick {base} -background black -alpha remove -alpha off "
           f"-resize 256x128! {O}/_c.png")
        sh(f"magick {O}/_c.png \\( {O}/_c.png -fill '{BLEU}' -colorize 100 \\) "
           f"{O}/_fz.png -alpha off -composite {dossier}/T-{tag}.png")
    out = f"{O}/vignette-{nom}.png"
    sh(f"python3 {A}/bin/composesplit.py --stack --axis horizontal --no-arrow "
       f"{dossier}/T-a.png {dossier}/T-b.png {out}")
    sh(f"magick {out} -background black -alpha remove -alpha off {out}")
    bb = sh(f"magick {paire['b'][2]} -background black -alpha remove -alpha off "
            f"-colorspace gray -threshold 5% -format '%@' info:").stdout.strip()
    lignes.append(f"{nom} boite-pochoir {bb}")
    print(lignes[-1], flush=True)

open(f"{O}/journal.txt", "w").write("\n".join(lignes) + "\n")
sh(f"cd {O} && magick montage -label '%t' $(ls vignette-*.png | sort) -tile 5x1 "
   f"-geometry 250x250+5+5 -background '#222' -fill white -pointsize 11 planche.png")
print("GLOBE-FIL-FINI")
