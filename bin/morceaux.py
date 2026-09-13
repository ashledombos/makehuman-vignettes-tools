#!/usr/bin/env python3
"""De quoi un proxy est-il fait ? Ses morceaux separes, et ou ils sont.

⭐ Question de Raphael, 13-09 : punkduck n'est-il qu'une tete, deux mains et
deux pieds ? Et le torse de duarteemerich est-il ferme au cou, donc un torse de
mannequin plutot qu'un corps mutile ? Cela se mesure : on compte les
composantes connexes du maillage et l'on donne, pour chacune, sa taille, sa
hauteur relative et ses dimensions.

La hauteur relative se lit sur le corps humain : 1,0 le sommet du crane, 0,85
le cou, 0,72 les epaules, 0,55 la taille, 0,45 le pubis, 0,0 les pieds.
"""
import sys
import math


def lire(chemin):
    sommets = []
    aretes = []
    for ligne in open(chemin, encoding="utf-8", errors="ignore"):
        if ligne.startswith("v "):
            p = ligne.split()
            sommets.append((float(p[1]), float(p[2]), float(p[3])))
        elif ligne.startswith("f "):
            idx = []
            for bloc in ligne.split()[1:]:
                n = int(bloc.split("/")[0])
                idx.append(n - 1 if n > 0 else len(sommets) + n)
            for i in range(len(idx)):
                aretes.append((idx[i], idx[(i + 1) % len(idx)]))
    return sommets, aretes


def composantes(sommets, aretes):
    parent = list(range(len(sommets)))

    def racine(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b in aretes:
        ra, rb = racine(a), racine(b)
        if ra != rb:
            parent[ra] = rb
    groupes = {}
    for i in range(len(sommets)):
        groupes.setdefault(racine(i), []).append(i)
    return groupes


for chemin in sys.argv[1:]:
    sommets, aretes = lire(chemin)
    groupes = composantes(sommets, aretes)
    ys = [p[1] for p in sommets]
    lo, hi = min(ys), max(ys)
    span = max(hi - lo, 1e-9)
    print("\n%s : %d sommets, %d morceaux"
          % (chemin.split("/")[-1], len(sommets), len(groupes)))
    gros = sorted(groupes.values(), key=len, reverse=True)[:12]
    for g in gros:
        pts = [sommets[i] for i in g]
        h = [(p[1] - lo) / span for p in pts]
        dx = max(p[0] for p in pts) - min(p[0] for p in pts)
        dy = max(p[1] for p in pts) - min(p[1] for p in pts)
        dz = max(p[2] for p in pts) - min(p[2] for p in pts)
        cx = sum(p[0] for p in pts) / len(pts)
        print("   %6d sommets  hauteur %.2f a %.2f  taille %.2f x %.2f x %.2f"
              "  centre x %+.2f"
              % (len(g), min(h), max(h), dx, dy, dz, cx))
