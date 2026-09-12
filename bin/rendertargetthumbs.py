#!/usr/bin/python3

"""Render thumbnail overrides for the modelling targets.

This has to run inside Blender, using the base studio template as the scene,
the same way bin/rendermeshthumbs.py does:

    blender -b thumbnail_production/studio_base.blend -P bin/rendertargetthumbs.py -- --family breast
    blender -b thumbnail_production/studio_base.blend -P bin/rendertargetthumbs.py -- --target /path/to/breast-dist-incr.target.gz
    blender -b thumbnail_production/studio_base.blend -P bin/rendertargetthumbs.py -- --family nose --azimuths 0,35 --samples 256

Targets are the one asset kind with no automatic camera support, which is why
sorting and thumbnailing them is the part that hurts. A mesh asset can be framed
on its own bounding box, but a target is not an object: it is a displacement of
part of the body, so what has to be framed is *the region that moves*, and that
region is different for every file.

The framing is therefore derived from the target data itself:

  - the point to look at is the centroid of the displaced vertices, weighted by
    how far each one moves, so a target that mostly moves one small area frames
    that area rather than the middle of the body;
  - the distance is computed from the **field of view of the studio camera**,
    not from a made up multiplier. ⚠ The studio shoots on a 200 mm lens, which
    is 10.3 degrees, so it frames about 74 cm of body from 4.1 m; a distance
    guessed from the size of the region alone puts the camera 47 cm away and
    the thumbnail shows a flat expanse of skin. The frame is asked to hold a
    given width of body and the distance follows from the optics. A minimum
    width keeps a tiny target readable: what makes a nose target legible is
    seeing a nose, not seeing the two millimetres that move;
  - the azimuth follows **which side of the body the moving region sits on**,
    not the direction it moves. Following the displacement looks right and is
    wrong: a target that pushes inwards points backwards, and the camera ends
    up behind the model. What is wanted is the side that region faces, so the
    azimuth comes from the horizontal offset of the region from the body axis,
    turned by a few degrees for a three quarter reading rather than a flat
    front. A region sitting on the axis, such as a belly target, has no side of
    its own, and there the displacement direction is the only clue left.

⭐ By default the framing is computed **once per family, over the union of what
its targets move**, and every thumbnail of that family then shares it. Framing
each target on its own is tempting and wrong: sibling targets end up at 24 cm
and at 72 cm of body, so browsing the pack becomes a zoom rollercoaster and the
eye compares crops instead of comparing anatomy. With a common frame, the only
thing that differs between two thumbnails is the body, which is the information
the thumbnail exists to carry. Use --framing target for the per-target
behaviour.

Unlike the mesh script, **the framing of every render is written next to the
image** in framing.json: same target, same thumbnail, on any machine. Automatic
framing that cannot be reproduced only moves the problem.

Each target is rendered before and after being applied, since for a target the
pair is what carries the information: the same body, the same light, one
difference. Use --after-only for the released single image.
"""

import bpy, sys, os, json, gzip, math, argparse, collections, importlib

import mathutils
from mathutils import Vector

file_path = os.path.dirname(os.path.realpath(__file__))
root = os.path.abspath(os.path.join(file_path, '..'))

thumbdir = os.path.join(root, "thumbnail_overrides")

# The studio bodies, and which one a target is rendered on. Targets that only
# exist for one sex would want that body; everything else uses the neutral one,
# like the released packs do.
BODY = "neutral"

# How much wider than the moving region the frame should be. At 1.0 the region
# would exactly fill the frame, which reads as a crop rather than as a body
# part; at 1.8 it takes a bit more than half the width and keeps its context.
CONTEXTE = 1.8

# The frame never holds less than this width of body, in metres. Below it, a
# small target gives a close up of nothing.
CHAMP_MINIMUM = 0.24

# Never closer than this. A single vertex target would otherwise put the camera
# inside the mesh.
MIN_DISTANCE = 0.28

# Vertices moving less than this fraction of the largest displacement are
# ignored when computing the framing: a target often nudges a wide skirt of
# vertices by a fraction of a millimetre, and letting those vote drags the
# framing back to the middle of the body.
NOISE_FLOOR = 0.15

# A region whose horizontal offset from the body axis is smaller than this is
# treated as sitting on the axis: it has no side of its own, and the direction
# of the displacement is used instead.
SUR_L_AXE = 0.02

# Added to the azimuth so the view is three quarter rather than flat on, which
# is what makes a change in relief readable.
BIAIS_TROIS_QUARTS = 22.0

# Fallback when neither the region nor the displacement gives a direction.
FALLBACK_AZIMUTH = 32.0

# Combien la sonde d'affinage cadre plus large que la vignette finale, et le
# plancher de son champ. Voir affiner_visee : une sonde cadrée comme la
# vignette ne voit pas un changement que la visée initiale a mis hors champ.
# Combien de points le long d'une courbe stylisée. Un point par secteur
# angulaire donnerait une ligne brisée ; on interpole entre les secteurs.
ECHANTILLONS_COURBE = 90

# Quelle fraction du poids **maximum du groupe** un sommet doit atteindre pour
# compter dans un tracé stylisé. `breast.L` est un groupe de déformation d'os,
# dont les poids s'estompent bien au-delà du sein visible : en gardant tout, la
# courbe passe loin du galbe et se lit comme un crochet posé à côté.
#
# ⚠ La fraction, et non un seuil absolu. Mesuré : les poids de `breast.L`
# plafonnent à **0,677**, donc un seuil absolu de 0,75 n'y retient aucun
# sommet et rien ne se dessine, en silence ; `eye.L` plafonne à 1,0. Une
# fraction du maximum vaut pour les deux.
FRACTION_STYLISE = 0.8

# En deçà de cette largeur cadrée, la profondeur de champ du studio est coupée
# d'office. Le studio tire au 200 mm à f/5,6, ce qui convient à un corps entier
# et ne laisse que quelques millimètres de net en gros plan : mesuré sur un
# mamelon de profil, la netteté passe de 4,2 à 17,2, un facteur quatre, et le
# relief comme le grain de peau réapparaissent.
GROS_PLAN = 0.20

SONDE_LARGE = 3.0
CHAMP_MINIMUM_SONDE = 0.50


def lire_cible(chemin):
    """A MakeHuman .target, gzipped or not: 'index dx dy dz' per line.

    MakeHuman works in decimetres and Y up, Blender in metres and Z up, hence
    (x, y, z) -> (x, -z, y) and the factor ten.
    """
    ouvrir = gzip.open if chemin.endswith(".gz") else open
    offsets = {}
    with ouvrir(chemin, "rt") as fichier:
        for ligne in fichier:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#"):
                continue
            morceaux = ligne.split()
            if len(morceaux) < 4:
                continue
            indice = int(morceaux[0])
            dx, dy, dz = (float(v) for v in morceaux[1:4])
            offsets[indice] = Vector((dx * 0.1, -dz * 0.1, dy * 0.1))
    return offsets


def cadrage(corps, offsets, camera, largeur_voulue=0.0):
    """Where to look, from how far, and from which side.

    Returns the look-at point in world space, the camera distance and the
    azimuth in degrees, plus the numbers behind them so a human can audit the
    choice instead of trusting it.
    """
    matrice = corps.matrix_world
    sommets = corps.data.vertices
    retenus = [(i, d) for i, d in offsets.items() if i < len(sommets)]
    if not retenus:
        raise ValueError("no vertex of this target exists on the body mesh")

    plus_grand = max(d.length for _, d in retenus)
    if plus_grand <= 0.0:
        raise ValueError("this target displaces nothing")
    utiles = [(i, d) for i, d in retenus
              if d.length >= plus_grand * NOISE_FLOOR]

    poids = sum(d.length for _, d in utiles)
    regard = Vector((0.0, 0.0, 0.0))
    for i, d in utiles:
        regard += (matrice @ sommets[i].co) * d.length
    regard /= poids

    ecarts = [((matrice @ sommets[i].co) - regard).length for i, _ in utiles]
    etendue = max(max(ecarts), plus_grand)

    # Le champ voulu, puis la distance que l'optique du studio impose pour
    # l'obtenir. `camera.data.angle` est l'angle réel, donc le calcul suit
    # l'objectif quel qu'il soit.
    # ⚠ Une largeur imposée l'emporte sur le calcul. Le champ déduit de
    # l'étendue garde du contexte, ce qu'il faut pour comprendre de quelle
    # partie du corps on parle, mais il peut noyer un petit mouvement : les
    # cibles de poitrine déplacent 3 cm dans un champ de 83 cm, donc à 128
    # pixels le sens du changement disparaît. Voir --width.
    champ = (largeur_voulue if largeur_voulue > 0.0
             else max(2.0 * etendue * CONTEXTE, CHAMP_MINIMUM))
    distance = max((champ / 2.0) / math.tan(camera.data.angle / 2.0),
                   MIN_DISTANCE)

    # Which side does the region sit on? The horizontal offset of the look-at
    # point from the body axis says it, and that is what the camera should
    # face. atan2 on (x, -y) because the studio camera sits at -Y and the
    # azimuth turns from there.
    if abs(regard.x) < SUR_L_AXE:
        # A symmetric region, breasts or belly, sits on the axis and has no
        # left or right of its own. ⚠ Deriving the azimuth from atan2 there
        # lets the *sign of a zero* decide the side, and two sibling targets
        # then get mirrored views, which is exactly what breaks the homogeneity
        # of a catalogue. Front or back is read from y, and the three quarter
        # bias always goes the same way.
        azimut = 0.0 if regard.y <= 0 else 180.0
        cote = "symmetric"
    elif math.hypot(regard.x, regard.y) >= SUR_L_AXE:
        azimut = math.degrees(math.atan2(regard.x, -regard.y))
        cote = "region"
    else:
        total = Vector((0.0, 0.0, 0.0))
        for _, d in utiles:
            total += d
        if math.hypot(total.x, total.y) > 1e-6:
            azimut = math.degrees(math.atan2(total.x, -total.y))
            cote = "displacement"
        else:
            azimut = FALLBACK_AZIMUTH
            cote = "fallback"
    # Bias away from a flat view. On a symmetric region the direction is fixed
    # rather than derived, for the reason above.
    if cote == "symmetric":
        azimut += BIAIS_TROIS_QUARTS
    else:
        azimut += BIAIS_TROIS_QUARTS * (1.0 if azimut >= 0 else -1.0)

    return regard, distance, azimut, {
        "vertices_moved": len(retenus),
        "vertices_used": len(utiles),
        "largest_displacement_mm": round(plus_grand * 1000, 3),
        "spread_m": round(etendue, 4),
        "framed_width_m": round(champ, 4),
        "azimuth_from": cote,
    }


def base_camera(azimut, elevation):
    """Les vecteurs droite et haut de la caméra, dans le repère du monde.

    Ils servent à retraduire un décalage mesuré **en pixels** en un décalage de
    la visée **en mètres**, ce que fait l'affinage en deux passes.
    """
    a = math.radians(azimut)
    e = math.radians(elevation)
    # ⚠ Le signe se démontre, il ne se devine pas. La caméra est posée en
    # `regard + d * (sin a, -cos a, 0)`, donc son axe de vue vaut
    # `f = (-sin a, cos a, 0)` et sa droite `cross(up, f) = (-cos a, -sin a, 0)`.
    # Contrôle à l'azimut nul : la caméra est en -y et regarde le modèle de
    # face, or le côté +x du modèle apparaît à **gauche** de l'image, donc la
    # droite de l'image est bien -x. Le signe inverse, écrit d'abord ici,
    # envoyait la correction horizontale de l'affinage du mauvais côté ; elle
    # est restée invisible sur les cibles symétriques, où elle vaut trois
    # pixels, et se serait vue sur un nez ou une oreille.
    droite = Vector((-math.cos(a), -math.sin(a), 0.0))
    haut = Vector((-math.sin(a) * math.sin(e),
                   math.cos(a) * math.sin(e),
                   math.cos(e)))
    return droite, haut


def affiner_visee(scene, corps, offsets, nom, regard, distance, azimut,
                  elevation, champ, travail, symetrique=False, un_cote=False):
    """Viser là où le changement se voit, et non là où les sommets bougent.

    ⚠ Le centroïde des sommets déplacés se calcule en coordonnées de monde, et
    il ne tombe pas où l'œil lit le changement : sur la famille `breast` il
    sort vingt pixels trop haut, parce qu'il pèse toute la surface qui se
    déplace alors que le regard s'accroche au galbe et au mamelon. Mesuré, 1,206
    m contre 1,141 m.

    L'affinage rend donc une paire d'essai en petit, mesure le centroïde de
    l'image de différence **en pixels**, et retraduit ce décalage en mètres le
    long des axes de la caméra. Une passe suffit : le second rendu est déjà
    centré sur ce qui bouge.

    ⚠ **La sonde cadre bien plus large que la vignette.** À 14 cm de champ,
    l'erreur de visée initiale fait la moitié du cadre : le changement sort de
    l'image, la sonde mesure ce qu'il en reste et l'affinage empire la visée au
    lieu de la corriger. En cadrant large, le changement est certainement dans
    l'image, et le décalage mesuré vaut pour n'importe quel zoom final.
    """
    memo = (scene.render.resolution_x, scene.render.resolution_y,
            scene.cycles.samples, scene.render.filepath)
    scene.render.resolution_x = max(64, memo[0] // 2)
    scene.render.resolution_y = max(32, memo[1] // 2)
    scene.cycles.samples = 32

    champ_sonde = max(champ * SONDE_LARGE, CHAMP_MINIMUM_SONDE)
    camera = bpy.data.objects["camera.r"]
    distance_sonde = (champ_sonde / 2.0) / math.tan(camera.data.angle / 2.0)
    poser_camera(scene, regard, distance_sonde, azimut, elevation)
    avant = os.path.join(travail, "_sonde-avant.png")
    apres = os.path.join(travail, "_sonde-apres.png")
    scene.render.filepath = avant
    bpy.ops.render.render(write_still=True)
    cle, _ = appliquer(corps, offsets, nom, 1.0)
    scene.render.filepath = apres
    bpy.ops.render.render(write_still=True)
    corps.shape_key_remove(cle)

    largeur, hauteur = scene.render.resolution_x, scene.render.resolution_y
    dx, dy = centroide_de_difference(avant, apres, largeur, hauteur, un_cote)
    (scene.render.resolution_x, scene.render.resolution_y,
     scene.cycles.samples, scene.render.filepath) = memo

    if dx is None:
        return regard, (None, None)

    droite, haut = base_camera(azimut, elevation)
    # Le champ vertical vaut la moitié du champ horizontal en format 2:1, donc
    # la conversion suit le rapport reel de l'image, pas une hypothese.
    metres_x = (dx - largeur / 2.0) / largeur * champ_sonde
    metres_y = ((dy - hauteur / 2.0) / hauteur * champ_sonde
                * (hauteur / largeur))
    vise = regard + droite * metres_x - haut * metres_y
    # ⚠ Une région symétrique reste sur l'axe du corps. Le bruit de la sonde
    # suffit à faire dériver la visée de cinq centimètres en x, ce qui décentre
    # tout le cadre d'une famille dont la symétrie est justement le sujet.
    #
    # ⚠ Et il faut pouvoir l'imposer, car la détection ne suffit pas : une
    # cible d'asymétrie n'est pas symétrique, elle pousse d'un seul côté, donc
    # la sonde la suit et le cadre part de travers. Or c'est la **famille** qui
    # est symétrique, et une asymétrie ne se lit que centrée sur la médiane.
    # Voir --on-axis.
    # ⚠ Les deux règles se contredisent et l'ordre compte : viser un seul des
    # deux traits est précisément **sortir de l'axe**, donc l'épinglage cède.
    if symetrique and not un_cote:
        vise.x = 0.0
    return vise, (dx, dy)


def visee_geometrique(corps, offsets, azimut, un_cote=False, loin=False):
    """Viser d'après la **géométrie**, sans rendu ni lumière.

    ⚠⚠ Pourquoi cette seconde voie existe, alors que la sonde photométrique la
    précédait. La sonde mesure une différence de **pixels**, donc elle suit les
    changements d'éclairement autant que les changements de forme. Mesuré le
    05-09 sur `nipple-point` : même côté retenu dans les trois cas, mais en
    passant du contre-jour à une clé dominante le cadre se décale jusqu'à
    perdre le mamelon hors champ, parce que le déplacement du reflet sur le
    galbe pèse plus que la saillie elle-même. **Une visée qui dépend de la
    lumière n'est pas une visée.**

    Ici le centroïde est pondéré par l'**amplitude** du déplacement, ce qui
    corrige le défaut qui avait fait écarter la voie géométrique au départ : à
    poids égal par sommet, `breast-point` visait vingt pixels trop haut, tout
    le flanc du sein pesant autant que la pointe.

    ⚠⚠ **Il faut lire le maillage évalué, non `corps.data.vertices`.** La
    morphologie de `female` vit en clés de forme, donc les coordonnées de base
    sont celles du basemesh neutre : 44 mm d'écart médian. Mesuré le 05-09, la
    visée tombait ainsi une demi-image à côté et les six vignettes ne
    montraient que de la peau nue.

    ⚠ Le côté ne se choisit pas au plus fort changement, mais par l'**azimut** :
    la caméra se place en `regard.x + rayon · sin(azimut)`, donc un azimut
    positif la met du côté des x positifs, et c'est ce sein-là qui fait face.
    À azimut nul, les deux se valent et le choix reste arbitraire mais stable.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evalue = corps.evaluated_get(depsgraph)
    sommets = evalue.data.vertices
    monde = evalue.matrix_world
    garder = math.sin(math.radians(azimut)) >= 0.0
    # ⚠ De profil, le detail qui se **decoupe sur le fond** est celui du cote
    # OPPOSE a la camera : le detail proche, lui, fait face et n'est sur aucun
    # contour. Pour tracer une silhouette il faut donc viser le lointain.
    if loin:
        garder = not garder
    total = 0.0
    somme = mathutils.Vector((0.0, 0.0, 0.0))
    for indice, ecart in offsets.items():
        if indice >= len(sommets):
            continue
        poids = ecart.length
        if poids <= 0.0:
            continue
        position = monde @ sommets[indice].co
        if un_cote and (position.x >= 0.0) != garder:
            continue
        total += poids
        somme += position * poids
    if total <= 0.0:
        return None
    vise = somme / total
    if un_cote:
        print("VISEE-GEO cote %s retenu d'apres l'azimut %.0f"
              % ("+x" if garder else "-x", azimut))
    return vise


def centroide_de_difference(avant, apres, largeur, hauteur, un_cote=False):
    """Le barycentre de ce qui change, en pixels, lu sur les deux rendus.

    Les images sont lues par Blender lui-meme : le script tourne dans Blender,
    donc aucune dependance externe n'est ajoutee pour cela.
    """
    a = bpy.data.images.load(avant)
    b = bpy.data.images.load(apres)
    pa, pb = list(a.pixels), list(b.pixels)
    total = sx = sy = 0.0
    # ⚠ Un trait **pairé et petit**, un mamelon ou un œil, met le barycentre du
    # changement **entre les deux**, donc sur le sternum ou l'arête du nez, et
    # un cadre serré n'y montre que de la peau nue. Il faut alors viser l'un des
    # deux, et le côté retenu est celui qui change le plus.
    milieu = largeur / 2.0
    if un_cote:
        gauche = droite = 0.0
        for i in range(0, len(pa), 4):
            d = (abs(pa[i] - pb[i]) + abs(pa[i + 1] - pb[i + 1])
                 + abs(pa[i + 2] - pb[i + 2]) + abs(pa[i + 3] - pb[i + 3]))
            if d <= 0.02:
                continue
            if (i // 4) % largeur < milieu:
                gauche += d
            else:
                droite += d
        garder_droite = droite >= gauche
        print(f"ONE-SIDE gauche={gauche:.1f} droite={droite:.1f} "
              f"retenu={'droite' if garder_droite else 'gauche'}")
    for i in range(0, len(pa), 4):
        d = (abs(pa[i] - pb[i]) + abs(pa[i + 1] - pb[i + 1])
             + abs(pa[i + 2] - pb[i + 2]) + abs(pa[i + 3] - pb[i + 3]))
        if d <= 0.02:
            continue
        pixel = i // 4
        # ⚠ Blender range les pixels de bas en haut : la rangée 0 est celle du
        # bas de l'image, l'inverse de la convention d'ImageMagick.
        x = pixel % largeur
        y = hauteur - 1 - pixel // largeur
        if un_cote and ((x >= milieu) != garder_droite):
            continue
        total += d
        sx += x * d
        sy += y * d
    bpy.data.images.remove(a)
    bpy.data.images.remove(b)
    if total <= 0.0:
        return None, None
    return sx / total, sy / total


def regler_zone(corps, motif, reglages):
    """Les réglages d'une **zone** de peau, et non de tout le corps.

    ⭐ Le corps ne porte pas un matériau mais **sept**, chacun une copie du même
    groupe de nœuds avec ses propres valeurs : `body` 17 136 faces,
    `nipple` 78, `lips` 380, `fingernails` 92, `toenails` 200, `ears` 600, et
    `genitals` **0**, la géométrie génitale étant masquée.

    ⚠ Le mamelon est réglé **exactement comme le corps**, teinte rouge à cinq
    pour cent, d'où le fait qu'il ne se distingue pas. Les ongles, eux, sont
    différenciés, blanc à quinze pour cent et sans pores : le mécanisme existe
    et sert déjà, personne ne s'en est servi pour l'aréole.
    """
    touches = 0
    for materiau in corps.data.materials:
        if not materiau or motif.lower() not in materiau.name.lower():
            continue
        if not materiau.use_nodes:
            continue
        for noeud in materiau.node_tree.nodes:
            if noeud.type != "GROUP":
                continue
            for nom, valeur in reglages.items():
                entree = noeud.inputs.get(nom)
                if entree is None:
                    continue
                if entree.type == "RGBA" and not isinstance(valeur, tuple):
                    valeur = (valeur, valeur, valeur, 1.0)
                entree.default_value = valeur
                touches += 1
        print(f"ZONE {materiau.name} {reglages} entrees={touches}")


def regler_peau(corps, reglages, subsurface=None):
    """Les réglages exposés par le matériau de peau de MPFB.

    ⭐ Il n'y a **aucune image** dans ce matériau : la peau est entièrement
    procédurale, un bruit qui alimente un relief de pores et un Principled. Il
    expose onze entrées, relevées :

    | entrée | défaut | ce qu'elle fait |
    |---|---|---|
    | `colorMixIn` | rouge 1 ; 0,2 ; 0,2 | la teinte mélangée à la peau |
    | `colorMixInStrength` | 0,05 | à cinq pour cent seulement |
    | `Roughness` | 0,45 | |
    | `Brightness`, `Contrast` | 0 | |
    | `Clearcoat`, `Clearcoat Roughness` | 0,1 et 0,3 | le lustre |
    | `Pore scale` | 2500 | la densité du grain |
    | `Pore detail` | 2 | |
    | `Pore distortion` | 1 | |
    | `Pore strength` | 0,2 | le relief du grain |

    ⚠ Le **subsurface est câblé mais désactivé** : `Subsurface Weight` vaut 0,
    alors que le rayon (1 ; 0,2 ; 0,1) et l'échelle 0,05 sont déjà réglés. Les
    peaux livrées par MakeHuman le déclarent pourtant, `sssEnabled True`. Il
    suffit donc de lever le poids.
    """
    # ⚠ Quatre des onze entrées ont une **espace** dans leur nom, ce qui casse
    # tout passage par une ligne de commande. Des alias sans espace évitent la
    # classe d'erreur entière.
    alias = {
        "pore_scale": "Pore scale",
        "pore_detail": "Pore detail",
        "pore_distortion": "Pore distortion",
        "pore_strength": "Pore strength",
        "clearcoat_roughness": "Clearcoat Roughness",
    }
    reglages = {alias.get(k, k): v for k, v in reglages.items()}
    touches = 0
    for materiau in corps.data.materials:
        if not materiau or not materiau.use_nodes:
            continue
        for noeud in materiau.node_tree.nodes:
            if noeud.type == "GROUP":
                for nom, valeur in reglages.items():
                    entree = noeud.inputs.get(nom)
                    if entree is None:
                        continue
                    if entree.type == "RGBA" and not isinstance(valeur, tuple):
                        valeur = (valeur, valeur, valeur, 1.0)
                    entree.default_value = valeur
                    touches += 1
                if subsurface is not None and noeud.node_tree:
                    for interne in noeud.node_tree.nodes:
                        if interne.type != "BSDF_PRINCIPLED":
                            continue
                        e = interne.inputs.get("Subsurface Weight")
                        if e is not None:
                            e.default_value = subsurface
                            touches += 1
    print(f"SKIN-TUNE {reglages} subsurface={subsurface} entrees={touches}")


def poser_peau(corps, texture, saturation=0.0, eclaircir=0.35):
    """Une peau désaturée : le grain sans le teint.

    ⚠ **À n'employer qu'en dernier recours, et mesuré comme une perte.** Ce
    matériau **remplace** celui de MPFB, lequel porte un relief procédural qui
    fait tout le travail : sur un gros plan de mamelon, le matériau nu rend un
    écart-type de 26,1 et laisse voir le grain de la peau, le remplacement 20,5
    et une surface lisse, quel que soit l'éclaircissement. Si l'on veut la
    couleur de l'aréole, il faut nourrir le matériau de MPFB par son entrée
    `colorMixIn`, non le remplacer.

    Les 26 peaux livrées avec MakeHuman n'ont qu'une texture **diffuse**,
    sans carte de relief. Le mamelon, l'aréole ou les lèvres ne s'y distinguent
    donc que par la **couleur**, et un corps sans texture les perd
    complètement : c'est pourquoi un gros plan de mamelon sur le matériau nu ne
    montre qu'une bosse.

    On garde donc la texture pour son contraste et l'on retire sa teinte, ce
    qui sert exactement l'intention de 2023 : un blanc neutre qui n'oblige pas
    à choisir une couleur de peau, ni un sexe, ni une origine.
    """
    materiau = bpy.data.materials.new("PEAU NEUTRE")
    materiau.use_nodes = True
    arbre = materiau.node_tree
    arbre.nodes.clear()
    sortie = arbre.nodes.new("ShaderNodeOutputMaterial")
    bsdf = arbre.nodes.new("ShaderNodeBsdfPrincipled")
    image = arbre.nodes.new("ShaderNodeTexImage")
    image.image = bpy.data.images.load(texture)
    teinte = arbre.nodes.new("ShaderNodeHueSaturation")
    teinte.inputs["Saturation"].default_value = saturation
    lumiere = arbre.nodes.new("ShaderNodeBrightContrast")
    lumiere.inputs["Bright"].default_value = eclaircir
    arbre.links.new(image.outputs["Color"], teinte.inputs["Color"])
    arbre.links.new(teinte.outputs["Color"], lumiere.inputs["Color"])
    arbre.links.new(lumiere.outputs["Color"], bsdf.inputs["Base Color"])
    arbre.links.new(bsdf.outputs["BSDF"], sortie.inputs["Surface"])
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = 0.6
    anciens = list(corps.data.materials)
    corps.data.materials.clear()
    corps.data.materials.append(materiau)
    print(f"SKIN {os.path.basename(texture)} saturation={saturation} "
          f"eclaircir={eclaircir}")
    return materiau, anciens


def mpfb_paquet():
    """Le nom de module de MPFB, qui n'est pas fixe.

    L'extension s'importe sous `bl_ext.user_default.mpfb` et non sous `mpfb`.
    Elle est déjà chargée quand ce script tourne, donc son nom se relit dans
    `sys.modules`. Même détour que `bin/rendermeshthumbs.py`.
    """
    noms = [n for n in sys.modules if n == "mpfb" or n.endswith(".mpfb")]
    if not noms:
        raise SystemExit("MPFB n'est pas installe dans ce Blender")
    return sorted(noms, key=len)[0]


def cuire_cible(corps, offsets, valeur=1.0):
    """La cible écrite dans les sommets du maillage, et de quoi revenir.

    ⚠ Nécessaire dès qu'un proxy doit suivre la déformation : l'ajustement de
    MPFB lit les coordonnées de base, donc une clé de forme lui est invisible.
    On rend les positions d'origine pour que l'appelant restaure.
    """
    memo = {}
    sommets = corps.data.vertices
    for indice, ecart in offsets.items():
        if indice >= len(sommets):
            continue
        memo[indice] = sommets[indice].co.copy()
        sommets[indice].co = sommets[indice].co + ecart * valeur
    corps.data.update()
    return memo


def restaurer_cible(corps, memo):
    sommets = corps.data.vertices
    for indice, position in memo.items():
        sommets[indice].co = position
    corps.data.update()


def ajuster_proxy(chemin, corps):
    """Un proxy ajusté au corps dans son état courant.

    ⭐ Pourquoi c'est nécessaire ici. Les trois curseurs de `genitals`
    déplacent 49 sommets de 162 mm, mais **tous** appartiennent à
    `HelperGeometry` et `helper-genital`, et aucun n'est dans le groupe `body`
    que conserve le masque `Hide helpers` : cette géométrie n'existe que pour
    ajuster un proxy, et sur le maillage nu elle est invisible. D'où les icônes
    livrées, dont les courbes sont **dessinées à la main** sur un pubis lisse :
    il n'y avait rien à photographier.

    ⚠ **L'ajustement lit les coordonnées de base du maillage, non le maillage
    évalué.** Mesuré : appliquer la cible en clé de forme puis ajuster donne
    exactement le même proxy pour les deux bouts du curseur, zéro pixel
    d'écart. La cible doit donc être **cuite dans les sommets** avant
    l'ajustement, ce que fait `cuire_cible`.

    ⚠ Et le corps du studio doit être **masqué au rendu** pendant ce temps. Le
    proxy génital de Slayer227 n'est pas un ajout local : mesuré, sa boîte
    englobante couvre tout le corps, 14 495 sommets de z 0 à 1,73 m. Sa surface
    se superpose donc à celle du basemesh, qui la cache par endroits et donne un
    rendu où rien ne bouge.
    """
    paquet = mpfb_paquet()
    Mhclo = importlib.import_module(paquet + ".entities.clothes.mhclo").Mhclo
    ClothesService = importlib.import_module(
        paquet + ".services.clothesservice").ClothesService

    mhclo = Mhclo()
    mhclo.load(chemin)
    proxy = mhclo.load_mesh(bpy.context)
    if not proxy:
        raise IOError("l'obj du proxy n'a pas pu etre importe")
    proxy.location = (0.0, 0.0, 0.0)
    # ⚠ L'obj arrive en ombrage **plat** : mesuré, 14 454 faces et zéro lissée,
    # quand le corps du studio a toutes les siennes lissées et une subdivision
    # par-dessus. Sans ces deux lignes le proxy sort en facettes et l'on croit
    # à une topologie grossière alors que sa densité vaut celle du corps.
    bpy.ops.object.shade_smooth()
    subdivision = proxy.modifiers.new("Subdivision", "SUBSURF")
    subdivision.levels = 0
    subdivision.render_levels = 1
    ClothesService.fit_clothes_to_human(proxy, corps, mhclo)
    mhclo.set_scalings(bpy.context, corps)
    # Le matériau du proxy n'est pas téléchargé avec lui, et un matériau
    # manquant sort en magenta. On reprend celui du corps, ce qui est de toute
    # façon ce qu'une vignette doit montrer : de la peau.
    if corps.data.materials:
        proxy.data.materials.clear()
        proxy.data.materials.append(corps.data.materials[0])
    corps.hide_render = True
    bpy.context.view_layer.update()
    return proxy


def styliser(corps, scene, groupes, chemin, secteur=(60.0, 255.0),
             points=48, lissage=5, poids=FRACTION_STYLISE):
    """Le contour stylisé d'un trait anatomique, en coordonnées d'image.

    ⭐ Ce que le contour de région ne sait pas faire. Le bord d'une région
    déplacée suit les sommets, donc il cerne une **aire** au lieu de suggérer
    une **forme**, et cela se voit : on lit un périmètre de sélection. Ici on
    part d'un groupe de sommets anatomique, `breast.L` ou `eye.R`, on projette
    ses sommets dans l'image, et on en tire une courbe radiale lissée dont on
    ne garde que le secteur utile.

    Pour un sein vu de face, ce secteur est **le galbe seul** : du bas
    intérieur, sous le sein, remontant vers l'aisselle. Le côté intérieur est
    écarté, il se distingue mal et n'apprend rien.

    Le secteur est donné en degrés dans le repère de l'image, x vers la droite
    et y vers le bas, donc 90° pointe vers le bas. Il est **miroité** pour le
    trait situé de l'autre côté de l'axe, sans quoi une moitié dessinerait son
    intérieur.
    """
    from bpy_extras.object_utils import world_to_camera_view
    camera = scene.camera
    maillage = corps.evaluated_get(
        bpy.context.evaluated_depsgraph_get()).to_mesh()
    matrice = corps.matrix_world
    largeur = scene.render.resolution_x
    hauteur = scene.render.resolution_y

    indices = {corps.vertex_groups[g].index for g in groupes
               if g in corps.vertex_groups}
    courbes = {}
    for nom_groupe in groupes:
        if nom_groupe not in corps.vertex_groups:
            continue
        cible = corps.vertex_groups[nom_groupe].index
        maxi = 0.0
        for v in maillage.vertices:
            for g in v.groups:
                if g.group == cible and g.weight > maxi:
                    maxi = g.weight
        if maxi <= 0.0:
            continue
        plancher = maxi * poids
        ecran = []
        for v in maillage.vertices:
            if not any(g.group == cible and g.weight >= plancher
                       for g in v.groups):
                continue
            p = world_to_camera_view(scene, camera, matrice @ v.co)
            ecran.append((p.x * largeur, (1.0 - p.y) * hauteur))
        if len(ecran) < 12:
            print(f"STYLISE {nom_groupe}: seulement {len(ecran)} sommets "
                  f"au-dela de {plancher:.3f}, rien n'est trace")
            continue
        cx = sum(p[0] for p in ecran) / len(ecran)
        cy = sum(p[1] for p in ecran) / len(ecran)

        # Le rayon le plus grand par secteur angulaire : une courbe en étoile,
        # qui suit le contour sans avoir à trianguler quoi que ce soit.
        seaux = [0.0] * points
        for x, y in ecran:
            a = math.degrees(math.atan2(y - cy, x - cx)) % 360.0
            i = int(a / 360.0 * points) % points
            r = math.hypot(x - cx, y - cy)
            if r > seaux[i]:
                seaux[i] = r
        # Les secteurs vides prennent la moyenne de leurs voisins, puis
        # l'ensemble est lissé en circulaire : sans cela la courbe est dentée.
        for i in range(points):
            if seaux[i] == 0.0:
                voisins = [seaux[(i + d) % points] for d in (-1, 1)
                           if seaux[(i + d) % points] > 0.0]
                seaux[i] = sum(voisins) / len(voisins) if voisins else 0.0
        lisses = []
        for i in range(points):
            fenetre = [seaux[(i + d) % points]
                       for d in range(-lissage // 2, lissage // 2 + 1)]
            lisses.append(sum(fenetre) / len(fenetre))

        gauche = cx < largeur / 2.0
        debut, fin = secteur
        # ⚠ Échantillonner un point par secteur donne une courbe en escalier
        # de vingt-six points. On échantillonne plus fin que les secteurs et
        # l'on **interpole** le rayon entre eux, ce qui rend une courbe lisse
        # sans changer la mesure.
        courbe = []
        n = ECHANTILLONS_COURBE
        for k in range(n + 1):
            a = debut + (fin - debut) * k / n
            if not gauche:
                a = 180.0 - a          # miroir autour de la verticale
            position = (a % 360.0) / 360.0 * points
            i = int(position) % points
            reste = position - int(position)
            r = lisses[i] * (1.0 - reste) + lisses[(i + 1) % points] * reste
            rad = math.radians(a)
            courbe.append([round(cx + r * math.cos(rad), 2),
                           round(cy + r * math.sin(rad), 2)])
        courbes[nom_groupe] = courbe

    corps.evaluated_get(
        bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    with open(chemin, "w") as f:
        json.dump({"size": [largeur, hauteur], "curves": courbes}, f, indent=1)
    return chemin


def rendre_region(corps, offsets, scene, chemin, plancher=NOISE_FLOOR):
    """Une passe où la zone que la cible déplace est blanche, le reste noir.

    ⭐ La troisième source de contour, et la seule qui marche sous n'importe
    quel angle. Le bord du canal alpha n'existe que si le changement est sur
    la silhouette ; un contour cherché dans l'ombrage suppose une limite nette,
    qu'un sein vu de face n'a pas. Ici le contour vient de la **géométrie** :
    on sait exactement quels sommets la cible déplace, donc on peint cette
    région et on prend son bord. C'est « la forme extérieure du sein », au
    sens propre.

    La région est peinte dans un attribut de couleur par sommet, ce qui laisse
    l'interpolation faire une frontière douce que le seuil rendra nette. Un
    matériau d'émission pure la restitue sans dépendre de l'éclairage.
    """
    maillage = corps.data
    nom_attribut = "REGION"
    if nom_attribut in maillage.color_attributes:
        maillage.color_attributes.remove(maillage.color_attributes[nom_attribut])
    attribut = maillage.color_attributes.new(
        name=nom_attribut, type="FLOAT_COLOR", domain="POINT")
    plus_grand = max((d.length for d in offsets.values()), default=0.0)
    for indice in range(len(maillage.vertices)):
        ecart = offsets.get(indice)
        dedans = (ecart is not None and plus_grand > 0.0
                  and ecart.length >= plus_grand * plancher)
        v = 1.0 if dedans else 0.0
        attribut.data[indice].color = (v, v, v, 1.0)

    matiere = bpy.data.materials.new("REGION")
    matiere.use_nodes = True
    arbre = matiere.node_tree
    arbre.nodes.clear()
    sortie = arbre.nodes.new("ShaderNodeOutputMaterial")
    emission = arbre.nodes.new("ShaderNodeEmission")
    couleur = arbre.nodes.new("ShaderNodeVertexColor")
    couleur.layer_name = nom_attribut
    arbre.links.new(couleur.outputs["Color"], emission.inputs["Color"])
    arbre.links.new(emission.outputs["Emission"], sortie.inputs["Surface"])

    anciennes = [f.material_index for f in maillage.polygons]
    matieres = list(maillage.materials)
    maillage.materials.clear()
    maillage.materials.append(matiere)
    for f in maillage.polygons:
        f.material_index = 0
    memo_echantillons = scene.cycles.samples
    memo_monde = scene.world
    scene.cycles.samples = 16
    scene.world = None

    scene.render.filepath = chemin
    bpy.ops.render.render(write_still=True)

    scene.cycles.samples = memo_echantillons
    scene.world = memo_monde
    maillage.materials.clear()
    for m in matieres:
        maillage.materials.append(m)
    for f, indice in zip(maillage.polygons, anciennes):
        f.material_index = indice
    bpy.data.materials.remove(matiere)
    maillage.color_attributes.remove(maillage.color_attributes[nom_attribut])
    return chemin


def preparer_scene(qui, echantillons, cote=0, rectangle=False,
                   portrait=False):
    scene = bpy.context.scene
    if cote:
        # ⚠ Le format de la prise n'est pas celui de la vignette. Une vignette
        # de cible est faite de **deux rendus** rectangulaires empilés, chacun
        # de la largeur de la vignette sur la moitié de sa hauteur : chaque
        # moitié montre alors la zone entière dans son état, et l'œil compare
        # deux images complètes au lieu de deux moitiés de corps. Le champ
        # calculé est horizontal, donc le capteur est fixé sur cet axe pour que
        # `camera.data.angle` désigne sans ambiguïté la largeur cadrée.
        # ⚠ Le sens du rectangle suit la **forme du sujet**, pas une
        # convention fixe. Vue de face, la poitrine est plus large que haute et
        # la prise est couchée, les deux moitiés s'empilant. Vue de profil, la
        # silhouette d'un sein est plus haute que large et la prise est
        # debout, les deux moitiés se posant côte à côte.
        if portrait:
            scene.render.resolution_x = cote // 2
            scene.render.resolution_y = cote
        else:
            scene.render.resolution_x = cote
            scene.render.resolution_y = cote // 2 if rectangle else cote
        scene.render.resolution_percentage = 100
        # Le capteur reste sur l'axe horizontal quel que soit le format, pour
        # que `camera.data.angle` désigne toujours la **largeur** cadrée et que
        # `--width` garde le même sens : en portrait, la hauteur vaut le double.
        for nom in ("camera.l", "camera.r"):
            bpy.data.objects[nom].data.sensor_fit = "HORIZONTAL"
    humains = bpy.context.view_layer.layer_collection.children["humans"]
    for nom, collection in humains.children.items():
        collection.exclude = (nom != qui)

    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for appareil in prefs.devices:
        appareil.use = (appareil.type == "OPTIX")
    scene.cycles.device = "GPU"
    scene.cycles.samples = echantillons
    # ⚠ Sans graine fixe, deux passes identiques rendent des images qui
    # different de 1 a 2/255 en moyenne : imperceptible, mais cela interdit de
    # verifier une reproduction par comparaison exacte, et donc de savoir si
    # un ecart vient d'un changement de reglage ou du bruit du moteur.
    scene.cycles.seed = 0
    scene.cycles.use_animated_seed = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    return scene


def regler_eclairage(reglages, force_monde=None):
    """Chaque famille de lampes multipliée par son propre facteur.

    ⚠ Le contraste ne vient **pas** de la quantité de lumière mais du rapport
    entre les lampes, et surtout de ce qui **remplit les ombres**. Mesuré
    famille par famille, chacune seule, sur un visage :

    | famille | moyenne | écart-type |
    |---|---|---|
    | le monde seul | 45,5 | 3,7 |
    | remplissage | 77,6 | 16,2 |
    | contre-jour | 57,1 | 24,1 |
    | **principale** | **127,0** | **41,9** |
    | spot | 126,6 | 31,8 |
    | toutes | 169,3 | 23,4 |

    La principale seule atteint donc l'écart-type des vignettes de 2023 de
    Raphaël, 42 à 59 : ce sont les autres qui inondent les ombres et font
    retomber le contraste à 23. Et le monde ajoute un plancher **plat** de 45
    de luminance, ce qui interdit tout noir quelle que soit la lampe.

    ⚠ Ma première tentative montait la principale et baissait le remplissage
    d'un même facteur : l'image saturait, moyenne à 253 et écart-type à 7 à
    facteur 8. Monter ne sert à rien, il faut **couper**.
    """
    compte = collections.Counter()
    for o in bpy.data.objects:
        if o.type != "LIGHT":
            continue
        nom = o.name.lower()
        for famille, facteur in reglages.items():
            if famille in nom:
                o.data.energy *= facteur
                compte[famille] += 1
                break
    if force_monde is not None:
        monde = bpy.context.scene.world
        if monde and monde.use_nodes:
            for n in monde.node_tree.nodes:
                if n.type == "BACKGROUND":
                    n.inputs[1].default_value = force_monde
    print(f"LIGHTING {dict(reglages)} monde={force_monde} "
          f"lampes={dict(compte)}")


def poser_camera(scene, regard, distance, azimut, elevation=0.0,
                 les_deux_rigs=True):
    """La caméra sur une sphère autour du point de visée.

    L'élévation manquait, et elle n'est pas un raffinement : un changement qui
    se lit en silhouette, un volume par exemple, demande un point de vue que
    l'azimut seul ne donne pas. Positive, la caméra monte et regarde vers le
    bas ; négative, elle plonge par-dessous. Le suivi de l'empty `target.r`
    fait le cadrage, donc rien d'autre n'est à recalculer.
    """
    camera = bpy.data.objects["camera.r"]
    cible = bpy.data.objects["target.r"]
    scene.camera = camera
    cible.location = regard
    angle = math.radians(azimut)
    hauteur = math.radians(elevation)
    rayon = distance * math.cos(hauteur)
    place = (regard.x + rayon * math.sin(angle),
             regard.y - rayon * math.cos(angle),
             regard.z + distance * math.sin(hauteur))
    camera.location = place
    if les_deux_rigs:
        # ⭐ Le studio contient **deux** rigs complets, gauche et droit, chacun
        # de quatre lampes parentées à une empty qui suit sa caméra. Sans
        # bouger `camera.l`, ses quatre lampes restent empilées à l'origine du
        # monde, sous les pieds du modèle : la moitié de l'éclairage ne sert à
        # rien et peut même polluer une contre-plongée.
        #
        # ⚠ Les poser au même endroit **double la lumière sans changer sa
        # direction**, donc cela n'ajoute pas de contraste ; cela donne la
        # marge pour couper le remplissage sans sous-exposer.
        autre = bpy.data.objects.get("camera.l")
        cible_autre = bpy.data.objects.get("target.l")
        if autre and cible_autre:
            cible_autre.location = regard
            autre.location = place
    # ⚠⚠ `view_layer.update()` **ne suffit pas** : la caméra suit l'empty et
    # l'empty suit la caméra, ce qui forme un cycle de dépendance, celui que
    # Blender signale par « Detected 1 dependency cycles ». Dans un cycle,
    # l'évaluation se fige sur un état périmé, et la répéter n'y change rien :
    # mesuré, le point visé se projetait en (0,906 ; −0,349) au lieu du centre,
    # et six mises à jour de suite donnaient la même valeur fausse.
    #
    # `depsgraph.update()` résout le cycle et le point visé retombe exactement
    # au centre. C'est la cause de tous les cadrages bancals de cette session,
    # et ce que l'affinage compensait à l'aveugle.
    bpy.context.evaluated_depsgraph_get().update()


def baisser_bras(qui, inclinaison=0.0):
    """Tendre les bras le long du corps, pour qu'ils sortent du cadre.

    ⭐ Le studio contient un squelette complet par corps (`female.rig`, 137 os)
    et le corps porte deja son modificateur d'armature : poser ne demande donc
    rien de plus que d'orienter deux os.

    ⚠ En pose de repos les bras sont ecartes en A, et dans un cadrage serre sur
    le sein ils **tiennent la silhouette** a la place du galbe. Les tendre les
    range derriere le torse et rend le contour au sein, ce qui est la condition
    du double trait.

    ⚠ Les cles de forme sont evaluees **avant** le modificateur d'armature :
    poser ne perturbe donc pas l'application des cibles.
    """
    rig = bpy.data.objects.get(qui + ".rig")
    if rig is None:
        raise SystemExit("pas de squelette %s.rig" % qui)
    bas = mathutils.Vector((0.0, math.sin(math.radians(inclinaison)),
                            -math.cos(math.radians(inclinaison))))
    bas.normalize()
    for cote in ("L", "R"):
        # ⚠⚠ **Un seul os, le premier.** Forcer aussi `upperarm02` et les
        # deux `lowerarm` a la verticale les fait tourner chacun dans son
        # repere alors qu'ils heritent deja de leur parent : le resultat
        # cisaille l'epaule, qui parait demise. Vu le 05-09 sur l'ecartement.
        for nom in ("upperarm01." + cote,):
            os_pose = rig.pose.bones.get(nom)
            if os_pose is None:
                continue
            os_pose.rotation_mode = "QUATERNION"
            # ⚠ L'axe Y de l'os **est** sa longueur : on cherche la rotation
            # qui amene cet axe sur la verticale descendante, puis on la pose
            # en espace d'armature, l'API se chargeant de la ramener au local.
            place = os_pose.matrix.translation.copy()
            tourne = mathutils.Vector((0.0, 1.0, 0.0)).rotation_difference(bas)
            neuve = tourne.to_matrix().to_4x4()
            neuve.translation = place
            os_pose.matrix = neuve
            bpy.context.view_layer.update()
    bpy.context.evaluated_depsgraph_get().update()
    print("BRAS tendus le long du corps, inclinaison %.0f deg" % inclinaison)


def poser_ethnie(corps, ethnie):
    """Pousser une des trois morphologies a fond, les deux autres a zero.

    ⭐ Le corps livre est un **melange a parts egales** : les trois cles
    `$md-$as-`, `$md-$ca-` et `$md-$af-` valent 0,327 chacune. Ce n'est donc pas
    un corps neutre mais une moyenne, et rien n'empeche de la defaire pour
    chercher la morphologie ou un changement se lit le mieux.

    ⚠ La cle universelle, elle, ne se touche pas : elle porte le sexe et l'age,
    non l'origine.
    """
    codes = {"asian": "$as", "caucasian": "$ca", "african": "$af"}
    if ethnie not in codes:
        raise SystemExit("ethnie inconnue : %s" % ethnie)
    formes = corps.data.shape_keys
    if formes is None:
        raise SystemExit("le corps n'a aucune cle de forme")
    touchees = []
    for cle in formes.key_blocks:
        for nom, code in codes.items():
            if cle.name.startswith("$md-" + code + "-"):
                cle.value = 1.0 if nom == ethnie else 0.0
                touchees.append((cle.name, cle.value))
    if len(touchees) != 3:
        raise SystemExit("attendu 3 cles d'origine, trouve %d" % len(touchees))
    print("ETHNIE %s : %s" % (ethnie, ", ".join(
        "%s=%.2f" % t for t in sorted(touchees))))


def appliquer(corps, offsets, nom, valeur=1.0):
    """The target as a shape key, and a way to undo it.

    `valeur` is the slider: a target is rarely at its best fully applied, and
    the pair that reads best is often a strong but not extreme setting on each
    side of the modifier.
    """
    if corps.data.shape_keys is None:
        corps.shape_key_add(name="Basis", from_mix=False)
    cle = corps.shape_key_add(name="TARGET." + nom, from_mix=False)
    hors = 0
    for indice, ecart in offsets.items():
        if indice >= len(cle.data):
            hors += 1
            continue
        position = cle.data[indice].co
        cle.data[indice].co = position + ecart
    cle.value = valeur
    cle.slider_min, cle.slider_max = 0.0, 1.0
    return cle, hors


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    a = argparse.ArgumentParser()
    a.add_argument("--target", action="append", default=[],
                   help="a .target or .target.gz file; repeatable")
    a.add_argument("--family", default="",
                   help="a target directory of the MPFB data, e.g. breast")
    a.add_argument("--targetdir", default=os.path.expanduser(
        "~/.var/app/org.blender.Blender/config/blender/5.2/extensions/"
        "user_default/mpfb/data/targets"),
        help="where the target families live")
    a.add_argument("--out", default=os.path.join(thumbdir, "targets"))
    a.add_argument("--who", default=BODY, choices=["neutral", "female", "male"])
    a.add_argument("--samples", type=int, default=128)
    a.add_argument("--size", type=int, default=0,
                   help="cote de la vignette en pixels ; avec --rect la prise "
                        "fait ce cote sur sa moitie")
    a.add_argument("--rect", action="store_true",
                   help="prises rectangulaires couchees 2:1, a empiler")
    a.add_argument("--portrait", action="store_true",
                   help="prises rectangulaires debout 1:2, a poser cote a "
                        "cote ; --width reste la largeur, la hauteur double")
    a.add_argument("--amounts", default="1.0",
                   help="valeurs du curseur a rendre, separees par des "
                        "virgules, par exemple 0.5,0.75,1.0")
    a.add_argument("--arms-down", nargs="?", const=0.0, type=float,
                   default=None, dest="bras",
                   help="tendre les bras le long du corps pour qu'ils sortent "
                        "du cadre ; valeur facultative = inclinaison en degres")
    a.add_argument("--hide-inner", action="store_true", dest="cacher_bouche",
                   help="masquer dents et langue. Elles ne servent jamais a "
                        "une vignette et leurs textures manquent sur le poste, "
                        "donc elles ne peuvent que fuir en magenta")
    a.add_argument("--ethnicity", default="", dest="ethnie",
                   choices=("", "asian", "caucasian", "african"),
                   help="pousser une morphologie a fond au lieu du melange a "
                        "parts egales livre par defaut")
    a.add_argument("--lift", type=float, default=0.0, dest="remontee",
                   help="remonter la visee de tant de metres apres calcul. "
                        "Une vignette ne montre pas que le changement : elle "
                        "doit se reconnaitre, donc garder le menton et le cou "
                        "dans le cadre meme quand rien n'y bouge")
    a.add_argument("--look-at", default="", dest="look_at",
                   help="point de visee impose, x,y,z en metres, au lieu du "
                        "centroide de ce que la cible deplace")
    a.add_argument("--fit", default="", dest="proxy",
                   help="un .proxy ou .mhclo ajuste au corps a chaque etat, "
                        "indispensable aux curseurs qui ne deplacent que de "
                        "la geometrie d'aide")
    a.add_argument("--zone-tune", action="append", default=[],
                   dest="zones",
                   help="reglages d'une zone, sous la forme "
                        "motif:cle=valeur,cle=valeur ; repetable. Exemple "
                        "nipple:colorMixInStrength=0.35")
    a.add_argument("--skin-tune", default="", dest="reglages_peau",
                   help="reglages du materiau de peau, par exemple "
                        "colorMixIn=1.0,colorMixInStrength=0.3,"
                        "Pore strength=0.5")
    a.add_argument("--sss", type=float, default=None, dest="subsurface",
                   help="poids du subsurface scattering ; il est cable mais a "
                        "zero dans le materiau de MPFB")
    a.add_argument("--skin", default="", dest="peau",
                   help="une texture diffuse de peau, appliquee desaturee : "
                        "le grain sans le teint")
    a.add_argument("--skin-saturation", type=float, default=0.0,
                   dest="saturation", help="0 = gris, 1 = teinte d'origine")
    a.add_argument("--skin-lift", type=float, default=0.35, dest="eclaircir",
                   help="remontee de luminosite de la peau desaturee")
    a.add_argument("--fstop", type=float, default=None, dest="ouverture",
                   help="ouverture de la camera ; 0 coupe la profondeur de "
                        "champ. Le studio est a f/5,6 sur un 200 mm, ce qui "
                        "ne laisse que quelques millimetres de net en gros plan")
    a.add_argument("--lights", default="", dest="lampes",
                   help="facteurs par famille, par exemple "
                        "key=1.5,fill=0,rim=0,spot=0 ; ce qui n'est pas cite "
                        "reste inchange")
    a.add_argument("--world", type=float, default=None, dest="monde",
                   help="force du monde ; il ajoute un plancher plat de 45 de "
                        "luminance, donc le baisser est ce qui rend les noirs")
    a.add_argument("--single-rig", action="store_true", dest="un_seul_rig",
                   help="ne pas poser le second rig d'eclairage")
    a.add_argument("--base", action="append", default=[], dest="socles",
                   help="une cible appliquee a **tous** les rendus, y compris "
                        "l'etat moyen, sous la forme fichier[:valeur] ; "
                        "repetable. Sert a donner au modele une morphologie "
                        "ou le changement se voit mieux, par exemple une "
                        "poitrine plus forte pour une cible d'ecartement.")
    a.add_argument("--far-side", action="store_true", dest="loin",
                   help="avec --one-side, viser le cote OPPOSE a la camera : "
                        "de profil, c'est lui qui se decoupe sur le fond")
    a.add_argument("--aim", default="sonde", choices=("sonde", "geo"),
                   dest="visee",
                   help="d'ou vient la visee : \"sonde\" mesure une paire de "
                        "rendus, \"geo\" pese les sommets deplaces. La geo ne "
                        "depend pas de l'eclairage")
    a.add_argument("--one-side", action="store_true", dest="un_cote",
                   help="viser un seul des deux traits d'une paire : sans "
                        "cela un mamelon ou un oeil fait viser entre les deux")
    a.add_argument("--on-axis", action="store_true", dest="sur_axe",
                   help="garder la visee sur l'axe du corps, quoi que dise "
                        "la sonde : indispensable aux cibles d'asymetrie")
    a.add_argument("--stylise", default="",
                   help="groupes de sommets a styliser, separes par des "
                        "virgules, par exemple breast.L,breast.R")
    a.add_argument("--weight", type=float, default=FRACTION_STYLISE,
                   dest="poids",
                   help="fraction du poids maximum du groupe qu'un sommet "
                        "doit atteindre pour compter")
    a.add_argument("--sector", default="60,255", dest="secteur",
                   help="secteur angulaire garde, en degres dans l'image")
    a.add_argument("--region", action="store_true",
                   help="rendre en plus une passe ou la zone deplacee est "
                        "blanche, pour en tracer le contour")
    a.add_argument("--refine", action="store_true",
                   help="affiner la visee par une paire d'essai en petit, "
                        "pour viser ou le changement se voit")
    a.add_argument("--elevation", type=float, default=0.0,
                   help="elevation de la camera en degres, positive au-dessus")
    a.add_argument("--azimuth", type=float, default=None,
                   help="azimut impose en degres, au lieu du cote deduit")
    a.add_argument("--width", type=float, default=0.0,
                   help="largeur de corps a cadrer, en metres, au lieu de "
                        "celle deduite de l'etendue de la cible")
    a.add_argument("--limit", type=int, default=0,
                   help="stop after this many targets (0 = all)")
    a.add_argument("--after-only", action="store_true", dest="after_only")
    a.add_argument("--framing", default="family", choices=["family", "target"],
                   help="one frame for the whole family (default) or one per "
                        "target")
    o = a.parse_args(argv)

    fichiers = list(o.target)
    if o.family:
        dossier = os.path.join(o.targetdir, o.family)
        fichiers += [os.path.join(dossier, f) for f in sorted(os.listdir(dossier))
                     if f.endswith((".target", ".target.gz"))]
    if o.limit:
        fichiers = fichiers[:o.limit]
    if not fichiers:
        raise SystemExit("nothing to render: give --target or --family")

    os.makedirs(o.out, exist_ok=True)
    scene = preparer_scene(o.who, o.samples, o.size, o.rect, o.portrait)
    # ⚠ L'ordre compte, et l'inverse était faux. `--skin-tune` s'applique aux
    # **sept** matériaux du corps, donc il écrase un réglage de zone posé
    # avant lui : trois essais de teinte d'aréole avaient rendu trois images
    # identiques pour cette seule raison. Le global d'abord, la zone ensuite.
    if o.reglages_peau or o.subsurface is not None:
        reglages = {}
        for morceau in o.reglages_peau.split(",") if o.reglages_peau else []:
            nom, _, valeur = morceau.rpartition("=")
            reglages[nom.strip()] = float(valeur)
        regler_peau(bpy.data.objects[o.who], reglages, o.subsurface)
    for zone in o.zones:
        motif, _, liste = zone.partition(":")
        reglages = {}
        for morceau in liste.split(","):
            nom, _, valeur = morceau.rpartition("=")
            if nom:
                reglages[nom.strip()] = float(valeur)
        regler_zone(bpy.data.objects[o.who], motif, reglages)
    if o.peau:
        poser_peau(bpy.data.objects[o.who], o.peau, o.saturation, o.eclaircir)
    ouverture = o.ouverture
    if ouverture is None and 0.0 < o.width < GROS_PLAN:
        ouverture = 0.0
        print(f"FSTOP largeur cadree {o.width} m, gros plan : profondeur de "
              f"champ coupee d'office")
    if ouverture is not None:
        # ⚠ Le studio tire au 200 mm a f/5,6, ce qui convient a un corps entier
        # et rend un gros plan flou : hors du plan de mise au point, qui passe
        # par le point vise, tout part en quelques millimetres. Fermer
        # l'ouverture ou couper la profondeur de champ rend le gros plan net.
        for nom in ("camera.l", "camera.r"):
            appareil = bpy.data.objects.get(nom)
            if not appareil:
                continue
            if ouverture <= 0.0:
                appareil.data.dof.use_dof = False
            else:
                appareil.data.dof.aperture_fstop = ouverture
    if o.lampes or o.monde is not None:
        reglages = {}
        for morceau in o.lampes.split(",") if o.lampes else []:
            nom, _, valeur = morceau.partition("=")
            reglages[nom.strip()] = float(valeur)
        regler_eclairage(reglages, o.monde)

    # ⭐ Les socles. Ils s'appliquent une fois, avant tout, et **restent** :
    # ils font partie du corps sur lequel la cible est montrée, non du
    # changement qu'elle produit. Ils entrent donc aussi dans l'état moyen,
    # sans quoi la vignette comparerait deux morphologies différentes.
    socles = []
    montants = [float(v) for v in o.amounts.split(",")]
    # L'affinage se fait une fois pour la famille : la visee doit rester
    # commune, sans quoi chaque vignette se recentre sur elle-meme et l'oeil
    # compare des recadrages.
    affine = None
    vise = (Vector([float(v) for v in o.look_at.split(",")])
            if o.look_at else None)
    corps = bpy.data.objects[o.who]
    camera = bpy.data.objects["camera.r"]

    if o.bras is not None:
        baisser_bras(o.who, o.bras)
    if o.cacher_bouche:
        # ⚠ Les maillages attaches n'ont **aucune** cle de forme : ils ne
        # suivent pas la morphologie du corps. Pousser une origine a fond
        # ecarte les levres et decouvre les dents, dont la texture
        # `teeth.png` est absente du poste : Blender la rend en magenta.
        for suffixe in ("teeth", "tongue"):
            objet = bpy.data.objects.get(o.who + "." + suffixe)
            if objet is None:
                continue
            objet.hide_render = True
            print("HIDE %s masque" % objet.name)
    if o.ethnie:
        poser_ethnie(corps, o.ethnie)
    for socle in o.socles:
        chemin_socle, _, valeur = socle.partition(":")
        cle_socle, _ = appliquer(corps, lire_cible(chemin_socle),
                                 "SOCLE." + os.path.basename(chemin_socle),
                                 float(valeur) if valeur else 1.0)
        socles.append(cle_socle)
        print(f"BASE {os.path.basename(chemin_socle)} "
              f"a {cle_socle.value:.2f}")
    if socles:
        # ⚠ Les socles doivent entrer dans le maillage **évalué** avant que le
        # cadrage ne mesure quoi que ce soit : sinon la visée et la distance se
        # calculent sur un corps que la vignette ne montrera pas.
        bpy.context.view_layer.update()

    # Le cadrage commun : l'union de ce que la famille déplace, chaque sommet
    # retenant son plus grand déplacement. La même fonction de cadrage
    # s'applique ensuite à cette union comme à une cible unique.
    commun = None
    union = None
    if o.framing == "family" and len(fichiers) > 1:
        union = {}
        for chemin in fichiers:
            for indice, ecart in lire_cible(chemin).items():
                if indice not in union or ecart.length > union[indice].length:
                    union[indice] = ecart
        commun = cadrage(corps, union, camera, o.width)
        regard, distance, azimut, mesures = commun
        print(f"FAMILY framing look_at={[round(v, 3) for v in regard]} "
              f"d={distance:.3f} az={azimut:.1f} "
              f"width={mesures['framed_width_m']:.3f}m "
              f"over {len(fichiers)} targets")

    journal = {}
    chemin_journal = os.path.join(o.out, "framing.json")
    if os.path.exists(chemin_journal):
        with open(chemin_journal) as fichier:
            journal = json.load(fichier)

    for chemin in fichiers:
        nom = os.path.basename(chemin).split(".target")[0]
        try:
            offsets = lire_cible(chemin)
            if commun:
                regard, distance, azimut, mesures = commun
                mesures = dict(mesures, framing="family")
            else:
                regard, distance, azimut, mesures = cadrage(corps, offsets,
                                                            camera, o.width)
                mesures = dict(mesures, framing="target")
        except ValueError as erreur:
            print(f"SKIP {nom}: {erreur}")
            continue

        if vise is not None:
            regard = vise
        if o.azimuth is not None:
            azimut = o.azimuth
        if o.visee == "geo" and affine is None:
            # La voie geometrique ne rend rien : elle pese les sommets.
            cible_visee = union if union is not None else offsets
            vise_geo = visee_geometrique(
                corps, cible_visee, azimut, o.un_cote, o.loin)
            if vise_geo is not None:
                if (o.sur_axe or mesures.get("azimuth_from") == "symmetric") \
                        and not o.un_cote:
                    vise_geo.x = 0.0
                regard = vise_geo
                affine = regard
                print(f"VISEE-GEO look_at={[round(v, 4) for v in regard]}")
        elif o.refine and affine is None:
            # ⚠ La sonde s'applique à l'**union** de la famille quand elle
            # existe, non à sa première cible : en profil, `dist` ne déplace
            # presque rien de visible, donc une sonde sur cette seule cible
            # n'aurait rien de net à mesurer et la visée resterait décalée.
            sonde_offsets = union if union is not None else offsets
            regard, sonde = affiner_visee(
                scene, corps, sonde_offsets, nom, regard, distance, azimut,
                o.elevation, mesures["framed_width_m"], o.out,
                o.sur_axe or mesures.get("azimuth_from") == "symmetric",
                o.un_cote)
            affine = regard
            print(f"REFINE look_at={[round(v, 4) for v in regard]} "
                  f"sonde={sonde}")
        elif affine is not None:
            regard = affine
        if o.remontee:
            # ⚠ La visee mesuree tombe sur ce qui bouge, ce qui est juste et
            # insuffisant : sur un profil de poitrine le cadre montre alors un
            # bras et un ventre, et l'oeil met un temps a reconnaitre un torse
            # de femme. Remonter garde le menton, qui donne l'echelle.
            regard = regard.copy()
            regard.z += o.remontee
            print(f"LIFT visee remontee de {o.remontee} m")
        poser_camera(scene, regard, distance, azimut, o.elevation,
                     not o.un_seul_rig)
        if not o.after_only:
            scene.render.filepath = os.path.join(o.out, nom + "-before.png")
            bpy.ops.render.render(write_still=True)

        hors = 0
        for montant in montants:
            cle, hors = appliquer(corps, offsets, nom, montant)
            suffixe = "" if montant == 1.0 and len(montants) == 1 \
                else "@%d" % round(montant * 100)
            memo = None
            proxy = None
            if o.proxy:
                # ⚠ La clé de forme ne suffit pas, l'ajustement ne la voit
                # pas : on cuit la cible dans les sommets, on ajuste, on rend,
                # puis on restaure.
                cle.value = 0.0
                memo = cuire_cible(corps, offsets, montant)
                proxy = ajuster_proxy(o.proxy, corps)
            scene.render.filepath = os.path.join(o.out, nom + suffixe + ".png")
            bpy.ops.render.render(write_still=True)
            if proxy:
                bpy.data.objects.remove(proxy, do_unlink=True)
                corps.hide_render = False
            if memo:
                restaurer_cible(corps, memo)
            if o.stylise and montant > 0.0:
                styliser(corps, scene, o.stylise.split(","),
                         os.path.join(o.out,
                                      nom + suffixe + "-stylise.json"),
                         tuple(float(v) for v in o.secteur.split(",")),
                         poids=o.poids)
            if o.region and montant > 0.0:
                rendre_region(corps, offsets, scene,
                              os.path.join(o.out,
                                           nom + suffixe + "-region.png"))
            corps.shape_key_remove(cle)

        journal[nom] = {
            "body": o.who,
            "look_at": [round(v, 5) for v in regard],
            "distance": round(distance, 5),
            "azimuth": round(azimut, 2),
            "elevation": round(o.elevation, 2),
            "samples": o.samples,
            "base": [os.path.basename(b) for b in o.socles],
            "lights": o.lampes,
            "world": o.monde,
            "both_rigs": not o.un_seul_rig,
            **mesures,
            "vertices_out_of_range": hors,
        }
        print(f"DONE {nom} look_at={[round(v, 3) for v in regard]} "
              f"d={distance:.3f} az={azimut:.1f} "
              f"moved={mesures['vertices_moved']} "
              f"used={mesures['vertices_used']} "
              f"max={mesures['largest_displacement_mm']}mm")

    for cle_socle in socles:
        corps.shape_key_remove(cle_socle)

    with open(chemin_journal, "w") as fichier:
        json.dump(journal, fichier, indent=2, sort_keys=True)
    print(f"FRAMING written to {chemin_journal}")


if __name__ == "__main__":
    main()
