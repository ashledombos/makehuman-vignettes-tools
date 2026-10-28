#!/usr/bin/env python3
"""Les 31 vignettes d'asymetrie, convention v8 : la v7 en tache fil de fer.

v8, 27-10-2026 : memes cadrages, amplitudes et visees que la v7 (PR #433),
mais la tache devient fil de fer, comme toutes les vignettes depuis le
24-09 : le bleu ne colore plus que les mailles de la zone, le relief reste
nu dessous. Rendu 1024, fil d'epaisseur proportionnelle a la largeur,
vignette 512 (a 256 le fil se fond en gris).

Ce qui suit est la note de la v7.

Dispositif arrete par Raphael le 16-09-2026, en deux temps. D'abord la zone
graduee seule, sur corps neutre ; puis, la planche vue : « je trouverais mieux
s'il y avait les deux en meme temps, la tache mais aussi le curseur de
deformation ». Si la joue gauche est gonflee, on voit la joue gonflee, et la
tache qui l'entoure.

⭐⭐ Tout se rend DE FACE et CENTRE SUR L'AXE, oreilles comprises, et le gros
plan ne fait pas exception : « il est plus pertinent d'avoir une image qui
normalement serait symetrique mais est deformee par une asymetrie, donc autant
avoir les deux yeux, autant que le cadrage soit toujours centre pour qu'on
percoive bien la symetrie ». Un cadre sur un seul oeil grossit la tache mais
supprime le terme de comparaison, qui est le sujet meme de ces cibles. Deux
essais ecartes pour cette raison : le profil des oreilles, et le recadrage sur
un foyer unique.

Deux corrections a la planche qu'il a vue :

1. PLEINE OPACITE au coeur de la tache. Le melange a 65 % delavait la couleur
   contre une peau claire : mesure du 16-09, l'ecart de chroma entre la tache
   et la peau qui l'entoure passe de 35 a 54 en supprimant ce voile. La teinte,
   elle, ne change pas : bleu #0072B2, la couleur de tout ce qui parle du
   maillage depuis le 13-09, et le vermillon qui mesure un peu mieux evoque
   une irritation de la peau.

2. SUPER-MACRO quand la tache est petite. Mesure du 16-09 : le sourcil et le
   nez couvrent 32 a 39 % de l'image, mais l'oreille, la paupiere, la machoire
   et le crane tombent a 3 a 5 %. Le cadre se recalcule alors sur la tache
   elle-meme, en deux passes : une sonde qui mesure, puis le rendu.

⭐ Le corps porteur est DEFORME, et l'amplitude reprend donc son sens : elle
vient du tableau d'etalonnage du 16-09, la plus faible dont le residu de
symetrie decolle nettement du bruit neutre. Le masque, lui, ne depend pas
d'elle : il vient des deplacements ecrits dans le fichier cible.

⚠ La tache ne doit pas effacer ce qu'elle entoure : un aplat opaque cachait le
relief qu'on venait d'exagerer. La couleur se pose donc en preservant la
luminance du corps (`-compose Colorize`), puis la zone est assombrie d'un
cinquieme pour rester franche. Mesure sur trois curseurs : le relief sous la
tache passe de 22-34 a 27-41 d'ecart-type, la tache restant a 111-152 de
luminance contre 103-119 pour l'aplat.

🪤 Sous 5 cm de large, `--width` ne fait plus rien (MIN_DISTANCE borne la
distance) : on n'approche pas, on allonge la focale, d'ou `--lens 400`.
"""
import json
import os
import subprocess
import sys

A = "/var/home/soleil/travail-makehuman"
CIBLES = os.path.expanduser(
    "~/.var/app/org.blender.Blender/config/blender/5.2/extensions/"
    "user_default/mpfb/data/targets/asym")
SORTIE = os.environ.get("SORTIE", f"{A}/vignettes-cibles/asym-v8")
TAILLE = 1024
# Facteur d'epaisseur du fil. A 1 (celle du lot 6, pensee pour un cadre de
# 5 cm), un visage entier bouche les mailles : la tache revient.
FIL = float(os.environ.get("FIL", "1"))
BRUT = f"{SORTIE}/brut"
BLEU = "#0072B2"
LUM = "key=0.55,fill=0.45,rim=2.0,spot=0.025"
COUVERTURE_VOULUE = 0.13     # part de l'image que la tache doit occuper
COUVERTURE_PLANCHER = 0.10   # en dessous, on recadre
PLANCHER_CADRE = 0.035       # metres ; en dessous la vignette perd son sujet

# Largeur de depart par famille, reprise de la v4 : elle sert de sonde, le
# cadre definitif se calcule sur la tache mesuree.
LARGEURS = [("-brown-", 0.10), ("-temple-", 0.15), ("-top-", 0.16),
            ("-eye-", 0.11), ("-nose-", 0.06), ("-mouth-", 0.09),
            ("-cheek-", 0.13), ("-jaw-", 0.16), ("-ear-", 0.16),
            ("breast", 0.26), ("trunk", 0.55)]
# v8, 28-10 : le tronc agit sur les EPAULES ; a 0,40 m vise a la taille, elles
# sortaient du cadre par le haut (Raphael). Visee aux epaules, cadre elargi.
# ⚠ Quatre visees restent imposees : la sonde --refine y remonte sur le front
# et sort un dome nu. Valeurs tirees du journal de la sonde, jamais d'une
# mesure du maillage (le repere de --look-at n'est pas celui de matrix_world).
# Dosage par curseur, lu au tableau d'etalonnage : la plus faible amplitude
# dont le residu depasse 2,2 fois le bruit neutre.
# ⚠ Les yeux sont plafonnes a 2 : au-dela la paupiere paraissait abimee
# (note du 16-09), et ici la tache porte deja l'essentiel de l'information.
AMPLITUDES = {
    "asym-brown-1": 3.0, "asym-brown-2": 2.0, "asym-cheek-1": 2.0,
    "asym-cheek-2": 2.0, "asym-ear-1": 2.0, "asym-ear-2": 1.0,
    "asym-ear-3": 2.0, "asym-ear-4": 4.0, "asym-eye-1": 2.0,
    "asym-eye-2": 2.0, "asym-eye-3": 2.0, "asym-eye-4": 2.0,
    "asym-eye-5": 2.0, "asym-eye-6": 2.0, "asym-eye-7": 2.0,
    "asym-eye-8": 2.0, "asym-jaw-1": 1.0, "asym-jaw-2": 2.0,
    "asym-jaw-3": 2.0, "asym-mouth-1": 2.0, "asym-mouth-2": 2.0,
    "asym-nose-1": 2.0, "asym-nose-2": 4.0, "asym-nose-3": 2.0,
    "asym-nose-4": 4.0, "asym-temple-1": 1.0, "asym-temple-2": 1.0,
    "asym-top-1": 1.0, "asym-top-2": 1.0, "asymm-breast-1": 1.0,
    "asymm-trunk-1": 1.0,
}

VISEES = {"asym-brown-2": "0.0,-0.1049,1.515", "asym-nose-4": "0.0,-0.1496,1.478",
          "asym-top-1": "0.0,-0.0735,1.520", "asym-top-2": "0.0,-0.0569,1.520",
          "asymm-trunk-1": "0.0,-0.1846,1.300"}


def sh(cmd, tolere=False, **kw):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    if r.returncode and not tolere:
        # Un rendu rate doit se voir : sans cela on relit le fichier de la
        # passe precedente et on croit avoir mesure la nouvelle.
        print(f"!! code {r.returncode} : {cmd[:110]}", flush=True)
        for ligne in (r.stdout + r.stderr).splitlines():
            if "error" in ligne.lower():
                print(f"   {ligne.strip()[:160]}", flush=True)
    return r


def largeur_de(curseur):
    for motif, valeur in LARGEURS:
        if motif in curseur:
            return valeur
    return 0.14


def rendre(curseur, largeur, visee, dossier):
    amplitude = AMPLITUDES.get(curseur, 2.0)
    # 🪤 `--look-at=` et non `--look-at ` : une visee decalee vers la gauche
    # commence par un signe moins, et argparse la prend alors pour une option.
    # Le rendu echouait en silence, donc tout recadrage vers la gauche etait
    # perdu et la vignette restait celle de la sonde, a la couverture identique.
    cadre = f"--look-at={visee}" if visee else "--refine"
    focale = "--lens 400" if largeur < 0.055 else ""
    cmd = (f"flatpak run --command=blender org.blender.Blender -b "
           f"{A}/studio_base.blend -P {A}/bin/rendertargetthumbs.py -- "
           f"--target {CIBLES}/{curseur}-l.target.gz "
           f"--who female --size {TAILLE} --hide-inner --fstop 0 --samples 384 "
           f"--width {largeur} --azimuth 0 --on-axis {cadre} {focale} "
           f"--mirror-lights --region --region-graded "
           f"--wire --wire-thickness {FIL * 0.00016 * largeur / 0.048:.6f} "
           f"--lights '{LUM}' --world 0.55 "
           f"--skin-tune 'colorMixIn=0.68,colorMixInStrength=0.7' "
           f"--amounts {amplitude} {os.environ.get('EXTRA', '')} --out {dossier}")
    sh(cmd)
    # Le corps porteur est l'image DEFORMEE, pas le neutre `-before`. Son nom
    # porte l'amplitude, sauf a 1.0 ou le moteur n'ajoute aucun suffixe.
    apres = [f for f in os.listdir(dossier)
             if f.startswith(f"{curseur}-l") and f.endswith(".png")
             and "-region" not in f and "-before" not in f and "-fil" not in f]
    zones = [f for f in os.listdir(dossier)
             if f.startswith(f"{curseur}-l") and f.endswith("-region.png")]
    fils = [f for f in os.listdir(dossier)
            if f.startswith(f"{curseur}-l") and f.endswith("-fil.png")]
    if not (apres and zones and fils):
        return None, None, None
    return tuple(os.path.join(dossier, x[0]) for x in (apres, zones, fils))


def mesurer(masque):
    """Couverture de la tache et sa boite."""
    seuil = f"magick {masque} -alpha off -colorspace gray -threshold 5%"
    cov = float(sh(f"{seuil} -format '%[fx:mean]' info:").stdout)
    boite = sh(f"{seuil} -format '%@' info:").stdout.strip()
    l, reste = boite.split("x")
    h, x, y = reste.replace("+", " ").split()
    l, h, x, y = int(l), int(h), int(x), int(y)
    return cov, (l, h, x, y)


def recadrer(curseur, largeur, cov, boite, journal):
    """Nouveau cadre, calcule sur la tache, et TOUJOURS centre sur l'axe.

    ⭐ Le cadre ne se decale pas horizontalement : ces cibles sont miroir, et
    une vignette qui ne montrerait qu'un cote perdrait le terme de comparaison.
    Le cadre doit donc contenir la tache ENTIERE tout en restant centre, d'ou
    une demi-largeur prise au plus eloigne de ses deux bords. Seule la hauteur
    de visee suit la tache.
    """
    l, h, x, y = boite
    # ⭐ On ne PREDIT pas la couverture finale, la densite dans la boite n'etant
    # pas uniforme : on cadre sur la tache, marge comprise, et c'est la mesure
    # du rendu suivant qui dit si le recadrage a servi.
    demi = max(abs(x - TAILLE / 2), abs(x + l - TAILLE / 2))
    nouvelle = max(largeur * max(2.0 * demi, h) / TAILLE * 1.2, PLANCHER_CADRE)
    # Seule la hauteur bouge ; l'abscisse reste sur l'axe du corps.
    cy = y + h / 2.0
    dz = -(cy - TAILLE / 2) / TAILLE * largeur
    _, vy, vz = journal["look_at"]
    return nouvelle, f"0.0,{vy:.4f},{vz + dz:.4f}"


def composer(corps, masque, fil, sortie):
    """Tache fil de fer : le pochoir est le fil MULTIPLIE par la zone graduee,
    le bleu plein n'est pose que la, comme dans lot6-fil-paire.sh."""
    t = f"{BRUT}/_compo"
    sh(f"magick {fil} -colorspace gray -resize 512x512! {t}-f.png")
    sh(f"magick {masque} -background black -alpha remove -alpha off "
       f"-colorspace gray -resize 512x512! {t}-z.png")
    sh(f"magick {t}-f.png {t}-z.png -compose multiply -composite {t}-fz.png")
    sh(f"magick {corps} -background black -alpha remove -alpha off "
       f"-resize 512x512! {t}-b.png")
    sh(f"magick {t}-b.png \\( {t}-b.png -fill '{BLEU}' -colorize 100 \\) "
       f"{t}-fz.png -alpha off -composite {sortie}")


def main():
    os.makedirs(BRUT, exist_ok=True)
    curseurs = sorted({f.split(".target")[0][:-2]
                       for f in os.listdir(CIBLES) if ".target" in f})
    # SEULS="asym-eye-3 asym-nose-1" : n'en rendre que quelques-uns (essai).
    if os.environ.get("SEULS"):
        curseurs = [c for c in curseurs if c in os.environ["SEULS"].split()]
    lignes = []
    for curseur in curseurs:
        largeur = largeur_de(curseur)
        visee = VISEES.get(curseur, "")
        corps, masque, fil = rendre(curseur, largeur, visee, BRUT)
        if not masque:
            lignes.append(f"ECHEC-SONDE {curseur}")
            continue
        journal = json.load(open(f"{BRUT}/framing.json"))[f"{curseur}-l"]
        cov, boite = mesurer(masque)
        note = f"{curseur} sonde={cov*100:.1f}%"
        if cov < COUVERTURE_PLANCHER:
            largeur2, visee2 = recadrer(curseur, largeur, cov, boite, journal)
            if largeur2 < largeur * 0.98:
                # La seconde passe ecrit a part : sinon un rendu rate laisse en
                # place le fichier de la sonde, qu'on mesure en croyant l'avoir
                # recadre.
                macro = f"{BRUT}/macro"
                os.makedirs(macro, exist_ok=True)
                c2, m2, f2 = rendre(curseur, largeur2, visee2, macro)
                if m2:
                    cov2, _ = mesurer(m2)
                    # ⚠ Un recadrage qui perd la tache est pire que pas de
                    # recadrage : on ne garde que s'il ameliore vraiment.
                    if cov2 > cov:
                        corps, masque, fil, cov = c2, m2, f2, cov2
                        note += (f" -> cadre {largeur2:.3f} m "
                                 f"= {cov2*100:.1f}%")
                    else:
                        note += f" macro refusee ({cov2*100:.1f}%)"
        composer(corps, masque, fil, f"{SORTIE}/{curseur}-l-r.png")
        lignes.append(note)
        print(note, flush=True)

    with open(f"{SORTIE}/journal.txt", "w") as f:
        f.write("\n".join(lignes) + "\n")
    faits = sorted(f for f in os.listdir(SORTIE) if f.endswith("-l-r.png"))
    opaques = sum(1 for f in faits
                  if sh(f"identify -format '%[opaque]' {SORTIE}/{f}"
                        ).stdout.strip() == "True")
    print(f"OPACITE {opaques}/{len(faits)}")
    sh(f"cd {SORTIE} && magick montage -label '%t' $(ls *-l-r.png | sort) "
       f"-tile 6x6 -geometry 200x200+5+5 -background '#222' -fill white "
       f"-pointsize 12 planche-v8.png")
    print(f"V8-FINI {len(faits)}")


if __name__ == "__main__":
    sys.exit(main())
