#!/usr/bin/python3

"""Render thumbnail overrides for the mesh assets of one asset pack.

This has to run inside Blender, using the base studio template as the scene:

    blender -b thumbnail_production/studio_base.blend -P bin/rendermeshthumbs.py -- --pack jewelry01_cc0
    blender -b thumbnail_production/studio_base.blend -P bin/rendermeshthumbs.py -- --pack jewelry01_cc0 --samples 128 joachip_ring_1
    blender -b thumbnail_production/studio_base.blend -P bin/rendermeshthumbs.py -- --pack jewelry01_cc0 --force

Unlike bin/renderposethumbs.py this needs MPFB installed in the Blender that runs
it: fitting an mhclo to the studio bodies is far too much machinery to
reimplement here, and the studio bodies are macro-morphed basemeshes, so the
asset obj cannot simply be imported as it is on disk.

Exactly one pack is rendered per run, named with --pack and looked up in packs/
and then packs-wip/. There is deliberately no way to render every pack in one
go. Bare arguments limit a run to the assets they name.

Only assets that have an mhclo or a proxy are rendered, which is what excludes
the materials, targets, skins and poses that may share the pack. Anything else
is reported and skipped. Assets that are not downloaded yet are fetched first,
unless --no-download is given.

Each asset is fitted to the neutral studio body, which is then hidden: the
released mesh thumbnails show the asset alone on a transparent background, not
the body wearing it. The camera keeps the studio angle but is recentred and
moved until the asset fills the frame, and the light rigs are moved to follow it,
since an asset may be anything from a ring on a finger to a full uniform. Assets
that come as a separated pair, such as earrings, are framed on one of the two
rather than on the empty space between them, unless --whole is given. Camera
positions are not recorded anywhere, so a second render of the same asset may
differ slightly.

Existing thumbnails are left alone unless --force is given.
"""

import bpy, sys, os, json, time, math, importlib, subprocess, re

from mathutils import Vector, Matrix

file_path = os.path.dirname(os.path.realpath(__file__))
root = os.path.abspath(os.path.join(file_path, '..'))

thumbdir = os.path.join(root, "thumbnail_overrides")

# Which of the three studio bodies to fit against. It is never rendered, but the
# fit follows the shape of the body, and the neutral one is what the released
# packs use.
BODY = "neutral"

BODIES = ["female", "male", "neutral"]

# The cameras and empties that drive the light rigs. The lights are parented to
# the targets, and the targets track the cameras, so moving a target moves its
# whole rig and moving a camera turns that rig to face from a new direction.
LIGHT_CAMERAS = ["camera.l", "camera.r"]
LIGHT_TARGETS = ["target.l", "target.r"]

# How much empty space to leave around the asset, as a divisor of the frustum.
MARGIN = 1.10
marge = None             # --margin : impose la marge, sinon elle s'adapte
epaisseur_aretes = 0.0   # --wire : fraction de l'arete moyenne, 0 = aucun trait
couleur_aretes = "bleu"  # --wire-colour : bleu, jaune, sombre, blanc, rouge
facettes = False         # --flat : eteindre le lissage, montrer les polygones
comparer = False         # --compare : rendre AUSSI le corps de base, meme cadre
paire_maillage = False   # --mesh-pair : deux prises, sans puis avec le maillage
lampes = ""              # --lights : facteurs par famille, key/fill/rim/spot
monde_fond = None        # --world : force la lumiere d'ambiance
# ⭐ Demande de Raphael le 06-09 : « au pire, si Joel dit pour tel asset je
# prefererais un diptyque, je te le dis et hop ». Une exception nommee vaut
# mieux qu'un seuil tordu pour la faire entrer : la regle mesuree decide par
# defaut, et une liste d'exceptions la surpasse, en clair dans la commande.
#   --device porky11_simple_penis=diptyque,joachip_snek=portrait
exceptions = {}          # --device : dispositif impose, par asset
gris = False             # --grey : le gris uniforme des vignettes de cibles
peindre = False          # --paint : marquer la zone modifiee dans le maillage
densite = False          # --paint-density : marquer l'ecart de DENSITE, non de forme
plancher_ecart = 0.0     # --paint-floor : en metres, voir peindre_lecart
sommets_neufs = False    # --paint-new : peindre ce que la base n'a pas
cadrer_neufs = False     # --frame-new : cadrer dessus sans le peindre
expo_carte = 0.0         # --paint-exposure : la carte ne suit pas --exposure
resolution_forcee = None  # --resolution <px> : override carre
corps_force = None       # --base-force neutral|male|female
dilatation_zone = 0      # --paint-dilate N : N anneaux de voisins en plus
paquet_de_zones = None   # --frame-zone haut|bas
polyptyque = False       # --polyptych : overview + une cellule par grappe
zone_a_la_couronne = None  # --zone-to-top <marge> : voir plus bas
part_emission = None     # --paint-emission : 0,55 par defaut, voir PART_EMISSION
densite_normalisee = False  # --paint-rework : le meme rapport, divise par sa
                         # mediane, pour ne garder que les zones retravaillees
mesurer_seulement = False  # --measure-only : classer sans rendre
auto = False             # --auto : choisir le dispositif d'apres les mesures
vraies_aretes = False    # --true-edges : Freestyle, pour voir les quads
# ⭐ L'orange par defaut depuis le 06-09. Choisi a l'oeil ET a la mesure, qui
# s'accordent : dispersion chromatique b* de 9,65 pour l'orange, 8,43 pour le
# vermillon, 4,46 pour l'ancienne version diffuse, et 5,39 seulement pour le
# jaune, qui parait pourtant le plus vif mais se rapproche trop du ton d'un
# corps clair, si bien que la frontiere de la zone se perd.
valeur_relief = "orange"  # --highlight : couleur de mise en valeur de la zone
part_peinte = 0.90       # --paint-part : percentile a partir duquel on peint
forme = "carre"          # --shape : carre, portrait (demi-largeur), couche
part_haute = 0.0         # --top  : fraction haute du sujet a cadrer, 0 = tout
# ⚠ Ce que l'usager a ECRIT, distinct de ce que le mode automatique deduit. Sans
# cette distinction le bloc automatique ecrase `--top` en posant 0,0 pour un
# diptyque, et l'option est acceptee sans effet. Vu le 06-09 en essayant un
# diptyque au cadrage de l'epure. Meme famille que les autres pannes muettes du
# chantier : une valeur posee, puis annulee plus bas.
part_haute_cli = None
# ⭐ Deux axes INDEPENDANTS, remarque de Raphael le 06-09 : le dispositif dit ce
# qu'on fabrique, la prise de vue dit d'ou l'on regarde et de combien on
# s'approche. Les melanger empeche de demander « la prise de l'epure avec le
# dispositif du diptyque », qui est une combinaison parfaitement legitime.
coupe_forcee = None      # --cut : horizontal ou vertical, sinon mesure
# ⚠⚠ Jusqu'au 06-09 ce script ne posait AUCUN azimut : il prenait la camera du
# studio telle quelle, rotation Z figee a -34 degres, et se contentait de la
# reculer pour cadrer. Le script des CIBLES, lui, calcule son azimut d'apres le
# cote du corps ou se trouve la region qui bouge. Les deux familles ne pouvaient
# donc s'accorder que par hasard, et Raphael a vu le resultat : les cibles
# tournees vers la gauche, les proxies vers la droite. L'angle devient ici un
# choix, comme il l'est deja la-bas.
azimut = None            # --azimuth : rotation autour de l'axe vertical, en degres
# ⭐ Le cadrage du diptyque, mais une seule prise CARREE. Il manquait : la
# combinaison « cadrer sur la zone d'ecart » et « une seule image » n'existait
# pas, le cadrage sur la zone etant lie a la paire. Or une planche qui montre
# des paliers de cadrage a besoin de prises carrees, sinon une case couchee
# parait plus petite que les autres et l'on croit a un defaut de cadrage.
zone_seule = False       # --zone : cadrer sur l'ecart, sans la paire

# An empty band this wide, as a fraction of the width of the asset on screen, is
# taken to mean that the asset comes as a separated pair rather than as one
# object. See largest_group().
GAP_RATIO = 0.35

# The camera is never brought closer than this. A tightly framed ring would put
# it three centimetres away, which is inside the near clip and gives a wildly
# distorted macro shot. Below this distance the camera stays put and the framing
# is done with focal length instead, which is both undistorted and flattering.
MIN_DISTANCE = 0.8

# Multiplier on the studio's world background. The studio is built around a body,
# which is diffuse and so is lit almost entirely by the light rigs, and its world
# is a near black grey. Mesh assets are frequently metal or otherwise glossy, and
# those show mostly what they reflect, which against that world is nothing. The
# background is therefore lifted for the mesh thumbnails, which is the difference
# between a gold ring and a brown smudge.
AMBIENT = 2.0


# -- MPFB, which is loaded as an extension and so does not have a fixed module
# name. It is initialized during Blender startup, so it is already in
# sys.modules by the time this script runs and the package name can be read
# back out of there.

def mpfb_package():
    names = [name for name in sys.modules if name == "mpfb" or name.endswith(".mpfb")]
    if not names:
        print("MPFB does not appear to be installed in this Blender. Unlike the pose")
        print("thumbnails, the mesh thumbnails need MPFB to fit assets to the body.")
        sys.exit(1)
    return sorted(names, key=len)[0]


package = mpfb_package()
Mhclo = importlib.import_module(package + ".entities.clothes.mhclo").Mhclo
MakeSkinMaterial = importlib.import_module(package + ".entities.material.makeskinmaterial").MakeSkinMaterial
ClothesService = importlib.import_module(package + ".services.clothesservice").ClothesService
MaterialService = importlib.import_module(package + ".services.materialservice").MaterialService


# -- Which assets to render, as (thumbnail name, mhclo path) pairs

def find_pack(packname):
    for packdir in ["packs", "packs-wip"]:
        candidate = os.path.join(root, packdir, packname + ".json")
        if os.path.exists(candidate):
            return candidate
    print("No such pack: " + packname)
    sys.exit(1)


def find_mhclo(asset):
    """Path to the downloaded mhclo (or proxy) of an asset, or None. The name in
    the asset db is the basename of the url, but a few of them differ from what
    ended up on disk, so the directory is scanned as a fallback."""
    download_dir = asset.get_download_dir()
    files = asset.asset.get("files", {})
    for key in ["mhclo", "proxy"]:
        if key not in files:
            continue
        candidate = os.path.join(download_dir, files[key].rsplit("/", 1)[-1])
        if os.path.exists(candidate):
            return candidate
    found = [f for f in sorted(os.listdir(download_dir))
             if f.lower().endswith(".mhclo") or f.lower().endswith(".proxy")]
    if len(found) == 1:
        return os.path.join(download_dir, found[0])
    return None


def pack_jobs(packname, download=True):
    """Every mesh asset of a pack definition, named after its final_name. Assets
    that are not mesh assets, or that cannot be resolved, are reported and
    skipped rather than aborting the batch."""

    # Imported lazily and by path, since this runs inside Blender rather than
    # from the repository root. src/staging is pure stdlib, so it loads here.
    sys.path.append(os.path.join(root, "src"))
    from staging import AssetDB

    with open(find_pack(packname), "r") as json_file:
        packdb = json.load(json_file)

    jobs = []
    for entry in sorted(packdb.get("assets", {}).values(), key=lambda e: e["final_name"]):
        final_name = entry["final_name"]
        asset = AssetDB.get_asset(entry["node_id"])
        if not asset:
            print("-- SKIP (node " + str(entry["node_id"]) + " not in the asset db): " + final_name)
            continue
        files = asset.asset.get("files", {})
        # The asset db never keys a proxy file as "proxy": a proxy entry carries
        # obj_file / file / thumb, the same way a target carries its data under
        # "file". Testing for a "proxy" key therefore skipped every proxy in the
        # database, which is why no proxy has ever had a thumbnail here. The
        # rest of the path already handles them: find_mhclo() falls back to
        # scanning the download directory for *.proxy, and MPFB loads them.
        usable = ("mhclo" in files or "proxy" in files
                  or (asset.asset.get("type") == "proxy" and "file" in files))
        if not usable:
            print("-- SKIP (" + str(asset.asset.get("type")) + " asset, no mhclo): " + final_name)
            continue
        if download:
            # Asset.download() skips what is already on disk, but it chdirs into
            # the download directory and does not come back.
            cwd = os.getcwd()
            try:
                asset.download()
            finally:
                os.chdir(cwd)
        mhclo = find_mhclo(asset)
        if not mhclo:
            print("-- SKIP (no mhclo on disk, run bin/download.py " + str(entry["node_id"]) + "): " + final_name)
            continue
        jobs.append((final_name, mhclo))
    return jobs


# -- Loading an asset

def repair_path(path, extension):
    """Find what an mhclo meant by a file it refers to.

    The asset repository appends an underscore to the name of an uploaded file
    when it collides with one that is already there, so a handful of published
    assets have an mhclo pointing at diamond_ring.left.obj while what can be
    downloaded is diamond_ring.left_.obj. The mhclo itself cannot be corrected
    from here, so the reference is followed to whatever is actually on disk."""

    if not path or os.path.exists(path):
        return path

    underscored = path[:-len(extension)] + "_" + extension
    if os.path.exists(underscored):
        print("-- NOTE: the mhclo asks for " + os.path.basename(path) + ", using " + os.path.basename(underscored))
        return underscored

    directory = os.path.dirname(path)
    found = [f for f in sorted(os.listdir(directory)) if f.lower().endswith(extension)]
    if len(found) == 1:
        print("-- NOTE: the mhclo asks for " + os.path.basename(path) + ", using " + found[0])
        return os.path.join(directory, found[0])

    return path


def load_asset(mhclo_file, basemesh, subdiv):
    """Import an mhclo and fit it to the basemesh, the way the load clothes
    operator of MPFB does it without a delete group and without rigging. The
    basemesh is left untouched: the temporary shape key that the fitting adds is
    removed again by ClothesService."""

    mhclo = Mhclo()
    mhclo.load(mhclo_file)
    mhclo.obj_file = repair_path(mhclo.obj_file, ".obj")
    mhclo.material = repair_path(mhclo.material, ".mhmat")
    if mhclo.material and not os.path.exists(mhclo.material):
        # An mhclo may name a material that was never published alongside it:
        # the site lists the obj, the proxy and a thumbnail, and nothing else.
        # Six of the fifteen proxies of proxies01_cc0 are in that state. The
        # asset is still perfectly renderable with whatever the obj brought, so
        # a missing material is a note and not a failure.
        print("-- NOTE: the mhclo names " + os.path.basename(mhclo.material)
              + ", which was never published; rendering without it")
        mhclo.material = None
    clothes = mhclo.load_mesh(bpy.context)
    if not clothes:
        raise IOError("the mhclo obj could not be imported")
    clothes.location = (0.0, 0.0, 0.0)
    bpy.ops.object.shade_smooth()

    if mhclo.material:
        MaterialService.delete_all_materials(clothes)
        makeskin_material = MakeSkinMaterial()
        makeskin_material.populate_from_mhmat(mhclo.material)
        name = os.path.basename(mhclo.material)
        makeskin_material.apply_node_tree(MaterialService.create_empty_material(name, clothes))
    else:
        print("-- WARNING: no material in the mhclo, rendering with whatever the obj brought")

    ClothesService.fit_clothes_to_human(clothes, basemesh, mhclo)
    if gris:
        poser_gris(clothes)
    if facettes and not paire_maillage:
        poser_facettes(clothes)
    if epaisseur_aretes and not paire_maillage:
        montrer_les_aretes(clothes, epaisseur_aretes, couleur_aretes)
    mhclo.set_scalings(bpy.context, basemesh)

    if subdiv > 0:
        # Clothes are usually authored low poly, and a thumbnail is the one place
        # where the subdivided shape is what the viewer should be judging.
        modifier = clothes.modifiers.new("Subdivision", "SUBSURF")
        modifier.levels = 0
        modifier.render_levels = subdiv

    return clothes


COULEURS_ARETES = {
    "bleu": (0.20, 0.55, 0.85, 1.0),     # le bleu ciel de nos vignettes
    "jaune": (0.94, 0.89, 0.26, 1.0),    # le jaune Okabe-Ito
    "sombre": (0.06, 0.06, 0.07, 1.0),   # un trait d'encre
    "noir": (0.0, 0.0, 0.0, 1.0),        # emission nulle : seule encre
                                         # que l'exposition ne remonte pas
    "blanc": (0.95, 0.95, 0.97, 1.0),    # un trait clair, pour un fond sombre
    "rouge": (0.84, 0.37, 0.00, 1.0),    # le vermillon Okabe-Ito
    # ⚠ Ajoutees le 06-09 : Raphael ne percoit pas assez le vermillon sur un
    # fond de theme sombre. La cause n'est pas la teinte mais le fait qu'elle
    # serve de couleur DIFFUSE, donc divisee par l'eclairage : un vermillon a
    # 0,84 ressort autour de 0,42, c'est-a-dire brun. Corrige par une part
    # d'emission (voir `peindre_lecart`) ; ces deux teintes plus claires sont
    # la pour choisir, l'orange restant proche du vermillon et le jaune
    # tranchant beaucoup plus.
    "orange": (0.90, 0.62, 0.00, 1.0),   # l'orange Okabe-Ito
    "jaune_vif": (0.94, 0.89, 0.26, 1.0),   # le jaune Okabe-Ito, le plus clair
    # ⚠ Pour un corps porcelaine : une teinte SOMBRE, sans quoi les deux
    # canaux clairs saturent et toute couleur vive vire au jaune.
    "brique": (0.42, 0.08, 0.02, 1.0),      # un rouge brun profond
    "encre_bleue": (0.04, 0.12, 0.50, 1.0), # le bleu d outremer
    "vert_sombre": (0.04, 0.30, 0.12, 1.0), # un vert bouteille
}


def objet_de_fil(objet, fraction=0.06, couleur=(0.06, 0.06, 0.07, 1.0),
                 epaisseur_min=0.0, marques=None, couleur_marquee=None):
    """Un objet SEPARE fait des vraies aretes du maillage.

    ⚠⚠ Pourquoi ni le noeud Wireframe ni Freestyle. Le **noeud** trace les
    aretes de la geometrie **triangulee par le moteur** : il invente une
    diagonale dans chaque quad, et les maillages de MakeHuman sont
    integralement en quads, verifie, 18 486 faces a quatre cotes pour le corps.
    Une epure qui triangule mentirait sur son seul sujet. **Freestyle**, essaye
    le 06-09 sur Blender 5.2 avec Cycles, ne rend que « strokes set empty »
    malgre les deux interrupteurs et les aretes marquees par attribut.

    Le modificateur Wireframe, lui, travaille sur les **vraies** aretes. Son
    defaut etait esthetique : applique a l'objet, il ajoutait un bourrelet a
    chaque face et donnait l'aspect d'un filet de tissu pose dessus. Applique
    a une COPIE avec `use_replace`, il ne reste que les aretes, en tubes fins,
    et le corps garde sa surface propre en dessous.
    """
    fil = objet.copy()
    fil.data = objet.data.copy()
    fil.name = objet.name + ".fil"
    bpy.context.scene.collection.objects.link(fil)
    aretes = [(fil.data.vertices[a].co - fil.data.vertices[b].co).length
              for a, b in (e.vertices for e in fil.data.edges)]
    moyenne = sum(aretes) / len(aretes) if aretes else 0.02
    # ⚠⚠ Encore le principe du chantier : une epaisseur relative a la seule
    # ARETE ne suffit pas, elle doit aussi etre relative au CADRE. Sur un
    # maillage a 8,8 mm d'arete le tube fait 0,53 mm, ce qui dans un cadre de
    # 34 cm rendu sur 256 pixels vaut 0,6 pixel : l'epure ne montre rien.
    # `epaisseur_min` est donc calculee par l'appelant a partir du cadre, une
    # fois les points de cadrage connus. Le plafond a 30 % de l'arete evite le
    # symptome oppose, le maillage dense qui se bouche en masse pleine.
    tube = moyenne * fraction
    if epaisseur_min > 0.0:
        tube = min(max(tube, epaisseur_min), moyenne * 0.30)
    m = fil.modifiers.new("fil", "WIREFRAME")
    m.thickness = tube
    m.use_replace = True
    m.use_even_offset = False
    matiere = bpy.data.materials.new("fil_encre")
    matiere.use_nodes = True
    principe = matiere.node_tree.nodes.get("Principled BSDF")
    if principe is not None:
        principe.inputs["Base Color"].default_value = couleur
        if "Roughness" in principe.inputs:
            principe.inputs["Roughness"].default_value = 0.8
    fil.data.materials.clear()
    fil.data.materials.append(matiere)
    for face in fil.data.polygons:
        face.material_index = 0
    if marques and couleur_marquee:
        # ⭐ Le second materiau se pose AVANT le modificateur : le Wireframe
        # herite de l'index de matiere de la face dont il tire ses aretes,
        # donc marquer les faces suffit a colorer les tubes correspondants.
        # ⚠ Une face compte comme marquee des qu'UN de ses sommets l'est :
        # exiger les quatre laisserait un liseré gris tout autour de la zone,
        # et c'est justement sa frontiere qu'on veut voir.
        vive = bpy.data.materials.new("fil_zone")
        vive.use_nodes = True
        p2 = vive.node_tree.nodes.get("Principled BSDF")
        if p2 is not None:
            p2.inputs["Base Color"].default_value = couleur_marquee
            if "Roughness" in p2.inputs:
                p2.inputs["Roughness"].default_value = 0.8
        fil.data.materials.append(vive)
        touchees = 0
        for face in fil.data.polygons:
            if any(i in marques for i in face.vertices):
                face.material_index = 1
                touchees += 1
        print("   fil bicolore : %d faces sur %d en couleur de zone"
              % (touchees, len(fil.data.polygons)))
    print("   fil sur les vraies aretes : %d aretes, arete moyenne %.4f m, "
          "tube de %.4f m (%.0f%% de l'arete)"
          % (len(fil.data.edges), moyenne, tube, 100.0 * tube / moyenne))
    return fil


def tracer_vraies_aretes(objet, scene, epaisseur=1.2, couleur=(0.06, 0.06, 0.07)):
    """Tracer les VRAIES aretes du maillage, quads compris.

    ⚠⚠ Trouve par Raphael le 06-09 : les maillages de MakeHuman sont
    **entierement en quads**, verifie, 18 486 faces a quatre cotes pour le corps
    et 410 pour le very low poly, zero triangle. Or le noeud Wireframe de
    Cycles trace les aretes de la geometrie **triangulee par le moteur** : il
    invente une diagonale dans chaque quad. Une vignette dont le sujet EST la
    topologie annoncait donc un maillage triangule la ou l'asset est en quads.

    Freestyle, lui, trace les aretes reelles. On marque toutes les aretes de
    l'objet et l'on demande a Freestyle de ne dessiner que ces marques.

    ⚠ L'epaisseur de Freestyle est en PIXELS et non en metres : elle ne suit
    donc pas la densite du maillage, et un maillage dense redevient une masse.
    Il faut la reduire a mesure que les aretes se resserrent.
    """
    # ⚠ Depuis Blender 4, les marques Freestyle ne sont plus une propriete de
    # l'arete (`edge.use_freestyle_mark`, disparue) mais un ATTRIBUT booleen du
    # maillage sur le domaine des aretes. Vu le 06-09 sur Blender 5.2.
    marque = objet.data.attributes.get(".freestyle_edge_mark")
    if marque is None:
        marque = objet.data.attributes.new(
            ".freestyle_edge_mark", "BOOLEAN", "EDGE")
    for donnee in marque.data:
        donnee.value = True
    # ⚠ Deux interrupteurs, et non un : `scene.render.use_freestyle` allume le
    # moteur de trace, `view_layer.use_freestyle` l'active sur la couche. Sans
    # le second, Blender rend sans erreur et signale seulement « strokes set
    # empty ». Vu le 06-09.
    scene.render.use_freestyle = True
    couche = bpy.context.view_layer
    couche.use_freestyle = True
    reglages = couche.freestyle_settings
    reglages.mode = "EDITOR"
    for jeu in list(reglages.linesets):
        reglages.linesets.remove(jeu)
    jeu = reglages.linesets.new("maillage")
    jeu.select_silhouette = False
    jeu.select_border = True
    jeu.select_crease = False
    jeu.select_edge_mark = True
    jeu.edge_type_combination = "OR"
    style = jeu.linestyle
    style.color = couleur
    style.thickness = epaisseur
    print("   Freestyle : %d aretes marquees, trait de %.1f px"
          % (len(objet.data.edges), epaisseur))


def poser_facettes(objet):
    """Eteindre le lissage, pour que les polygones se voient.

    ⚠⚠ Un maillage lisse n'a plus de facettes : c'est ce qui rendait un corps a
    412 faces aussi rond qu'un corps a 14 000. Et le script applique par defaut
    une **subdivision de niveau 1**, qui lisse davantage encore : pour une
    vignette dont le sujet EST la topologie, il faut `--subdiv 0`.
    """
    for face in objet.data.polygons:
        face.use_smooth = False


INDICES_NEUFS = set()  # rempli par peindre_les_nouveaux, lu par le fil bicolore
GRIS_NEUTRE = (0.85, 0.85, 0.87, 1.0)     # le fil hors zone, en mode local.
# ⚠ Choisi a 0,85 le 13-09 sur quatre valeurs. L intuition disait sombre,
# pour contraster avec le bleu ; la planche dit clair. Un fil gris sombre
# fait ressortir TOUT le maillage et l oeil ne va nulle part, tandis qu un
# fil presque fondu dans le corps porcelaine laisse la zone seule accrocher
# le regard. Ce n est pas le contraste avec le bleu qui compte, c est celui
# du bleu avec le reste.
GRIS_STUDIO = (0.62, 0.62, 0.63, 1.0)     # la teinte des vignettes de cibles
BLANC_TECHNIQUE = (0.92, 0.92, 0.93, 1.0)  # le fond de la moitie « maillage »
PART_EMISSION = 0.55  # la part d'emission dans une zone de mise en valeur
ECART_BLANC = 0.9  # en diaphragmes : ce qui separe vraiment les deux moities


def montrer_les_aretes(objet, fraction, couleur="bleu", garder_matiere=False,
                       fond=None):
    """Tracer les aretes comme des TRAITS, sans ajouter un seul sommet.

    ⚠⚠ **Ne pas employer le modificateur Wireframe** : il fabrique de la
    geometrie, donc chaque face devient un bourrelet et le maillage prend
    l'aspect d'un filet de tissu pose dessus. Sur un maillage a 412 faces cela
    **trahit l'asset**, dont les faces sont plates.

    ⚠ L'epaisseur est une **fraction de l'arete moyenne** et non une valeur
    fixe : la meme epaisseur qui dessine proprement un maillage a 412 faces
    noie un maillage a 14 000 en une masse de couleur.
    """
    materiau = bpy.data.materials.new("proxy_aretes")
    materiau.use_nodes = True
    arbre = materiau.node_tree
    principe = arbre.nodes.get("Principled BSDF")
    sortie = arbre.nodes.get("Material Output")
    if principe is None or sortie is None:
        print("-- NOTE: materiau inattendu, aretes non tracees")
        return
    # ⭐ Arbitrage de Raphael le 06-09 : la moitie « rendu » garde le gris des
    # vignettes de cibles, la moitie « maillage » passe au BLANC, pour se lire
    # comme un plan technique, traits d'encre sur fond clair. Les deux moities
    # disent alors deux choses differentes jusque dans leur matiere.
    principe.inputs["Base Color"].default_value = fond or GRIS_STUDIO
    if "Roughness" in principe.inputs:
        principe.inputs["Roughness"].default_value = 0.55

    aretes = [(objet.data.vertices[a].co - objet.data.vertices[b].co).length
              for a, b in (arete.vertices for arete in objet.data.edges)]
    moyenne = sum(aretes) / len(aretes) if aretes else 0.02
    taille = moyenne * fraction

    fil = arbre.nodes.new("ShaderNodeWireframe")
    fil.use_pixel_size = False
    fil.inputs["Size"].default_value = taille
    trait = arbre.nodes.new("ShaderNodeEmission")
    trait.inputs["Color"].default_value = COULEURS_ARETES.get(
        couleur, COULEURS_ARETES["bleu"])
    trait.inputs["Strength"].default_value = 1.0
    melange = arbre.nodes.new("ShaderNodeMixShader")
    arbre.links.new(fil.outputs["Fac"], melange.inputs["Fac"])
    arbre.links.new(principe.outputs["BSDF"], melange.inputs[1])
    arbre.links.new(trait.outputs["Emission"], melange.inputs[2])
    arbre.links.new(melange.outputs["Shader"], sortie.inputs["Surface"])

    if not garder_matiere:
        objet.data.materials.clear()
    objet.data.materials.append(materiau)
    # ⚠⚠ Vider les emplacements ne remet pas l'index de matiere des FACES a
    # zero : un objet importe avec plusieurs matieres garde des faces pointant
    # sur l'emplacement 1 ou 2, qui n'existent plus, et elles se rendent sans
    # notre materiau. Deux proxies sur quinze rendaient ainsi une paire
    # rigoureusement identique, sans la moindre erreur affichee, alors que le
    # journal confirmait la pose du trait. Vu le 06-09.
    if not garder_matiere:
        indice = len(objet.data.materials) - 1
        for face in objet.data.polygons:
            face.material_index = indice
    print("   aretes %s : arete moyenne %.4f m, trait %.4f m (x%.2f)"
          % (couleur, moyenne, taille, fraction))


def garder_le_haut(points, part):
    """Ne conserver que la tranche haute des points, pour cadrer sur la tete.

    ⚠ Un corps entier a 256 pixels ne montre pas sa topologie : les aretes s'y
    ecrasent en moire. Il faut zoomer sur une zone parlante, et la tete l'est
    plus que tout : c'est la que le nombre de faces se voit, un corps a 412
    faces y ayant un visage a facettes.
    """
    if not points:
        return points
    hauts = [p[2] for p in points]
    seuil = max(hauts) - (max(hauts) - min(hauts)) * part
    retenus = [p for p in points if p[2] >= seuil]
    print("   cadrage sur le haut : %d points sur %d" % (len(retenus), len(points)))
    return retenus or points


def regler_lampes(reglages, force_monde=None):
    """Chaque famille de lampes multipliee par son facteur, comme pour les
    cibles.

    ⭐ Porte ici depuis `rendertargetthumbs.py` pour que les vignettes d'assets
    et celles de curseurs sortent du meme studio avec le meme rendu : Raphael
    demande la meme couleur homogene partout, gris avec un lisere et du volume.
    Reglage retenu pour les vues de trois-quarts et de profil :
    `key=0.7,fill=0.6,rim=2.0,spot=0.05`, monde 0,4.

    ⚠ Le contraste ne vient pas de la quantite de lumiere mais du rapport entre
    les lampes, et surtout de ce qui REMPLIT les ombres. Monter ne sert a rien,
    il faut couper.
    """
    for o in bpy.data.objects:
        if o.type != "LIGHT":
            continue
        nom = o.name.lower()
        for famille, facteur in reglages.items():
            if famille in nom:
                o.data.energy *= facteur
                break
    if force_monde is not None:
        monde = bpy.context.scene.world
        if monde and monde.use_nodes:
            for n in monde.node_tree.nodes:
                if n.type == "BACKGROUND":
                    n.inputs[1].default_value = force_monde
    print("   lampes : %s, monde %s"
          % (", ".join("%s=%g" % kv for kv in sorted(reglages.items())),
             force_monde if force_monde is not None else "inchange"))


def poser_gris(objet, couleur=None):
    """Un gris uniforme, celui des vignettes de cibles.

    ⭐ Les assets arrivent avec la matiere de leur auteur, ou sans matiere du
    tout, donc d'un blanc a l'autre le catalogue n'a aucune unite. Raphael
    demande la meme couleur partout : un gris moyen, qui est aussi le seul
    stable quel que soit le theme de l'usager, 6 points d'ecart entre theme
    clair et sombre contre 48 pour le blanc.
    """
    materiau = bpy.data.materials.new("gris_studio")
    materiau.use_nodes = True
    principe = materiau.node_tree.nodes.get("Principled BSDF")
    if principe is not None:
        principe.inputs["Base Color"].default_value = couleur or GRIS_STUDIO
        if "Roughness" in principe.inputs:
            principe.inputs["Roughness"].default_value = 0.55
    objet.data.materials.clear()
    objet.data.materials.append(materiau)
    for face in objet.data.polygons:
        face.material_index = 0


SEXE_MOTS = {
    "male": ("male", "males", "man", "men", "boy", "penis", "phallus",
             "scrotum", "testicle", "masculine"),
    "female": ("female", "females", "woman", "women", "girl", "vulva",
               "vagina", "labia", "breast", "feminine"),
}


def activer_le_corps(nom):
    """Rendre un corps du studio utilisable, collection comprise.

    ⚠⚠ Les trois corps existent dans le fichier, mais leurs collections sont
    **exclues de la couche de vue** sauf celle du neutre : `bpy.data.objects`
    les voit, `view_layer.objects` non, et poser l'objet actif echoue sur
    « ViewLayer does not contain object 'male' ». Vu le 06-09 en montant les
    assets masculins sur le corps masculin.
    """
    def parcourir(couche):
        if couche.collection.name == nom:
            return couche
        for enfant in couche.children:
            trouve = parcourir(enfant)
            if trouve is not None:
                return trouve
        return None
    cible = parcourir(bpy.context.view_layer.layer_collection)
    if cible is not None:
        cible.exclude = False
        cible.hide_viewport = False
    collection = bpy.data.collections.get(nom)
    if collection is not None:
        collection.hide_render = False
        collection.hide_viewport = False
    objet = bpy.data.objects.get(nom)
    if objet is not None:
        objet.hide_render = False
        objet.hide_viewport = False
    return objet


def deviner_le_sexe(nom, titre="", categorie=""):
    """Sur quel corps monter cet asset : masculin, feminin, ou le neutre.

    ⭐ Demande de Raphael le 06-09 : un asset qui ne vaut que pour un sexe se
    montre mal sur le corps neutre, qui est un melange a parts egales et donne
    une apparence indecise ou l'on ne distingue plus rien. Un proxy feminin va
    donc sur `female`, un masculin sur `male`.

    ⚠ Et ce choix doit precede la MESURE, non seulement le rendu : l'ecart au
    corps sert a classer l'asset, donc le comparer au mauvais corps y melerait
    la difference de sexe.

    ⚠ Les mots sont cherches dans le nom, le titre ET la categorie du
    catalogue, celle-ci portant deja « Gender-specific (female) » pour une
    partie des assets.
    """
    champ = (" " + nom + " " + titre + " " + categorie + " ").lower()
    champ = re.sub(r"[^a-z]+", " ", champ)
    trouves = set()
    for sexe, mots in SEXE_MOTS.items():
        for mot in mots:
            if " " + mot + " " in champ:
                trouves.add(sexe)
                break
    if len(trouves) == 1:
        sexe = trouves.pop()
        print("   corps %s, d'apres le nom" % sexe)
        return sexe
    if len(trouves) > 1:
        print("   nom ambigu sur le sexe, corps neutre")
    return BODY


def classer_lasset(clothes, basemesh, ecarts_bruts=None):
    """Quels criteres, et donc quel dispositif, pour cet asset.

    ⭐⭐ Doctrine arretee avec Raphael le 06-09, trois cas :

    - **silhouette radicalement differente** (squelette, sirene) : on ne montre
      RIEN de plus, l'evidence suffit et la couleur serait du bruit ;
    - **retopologie**, basse resolution ou a densite egale : un seul cadrage
      serre, maillage trace sur un corps tres clair ;
    - **changement de forme** sans retopologie, une musculature : zones en
      vermillon, cadre colle a leur enveloppe.

    ⭐ Le critere qui separe les deux derniers : une retopologie
    **reechantillonne la meme surface**, donc son ecart au corps ne vient que du
    fait que ses sommets ne tombent pas aux memes endroits, et cet ecart est de
    l'ordre d'UNE ARETE. Un vrai changement de forme eloigne la surface bien
    au-dela. On compare donc l'ecart maximal a la longueur d'arete moyenne : au
    dela de 1, la forme change ; en dessous, c'est le meme galbe echantillonne
    autrement.
    """
    from mathutils.bvhtree import BVHTree
    coupes = [m for m in basemesh.modifiers
              if m.type in ("SUBSURF", "MULTIRES") and m.show_render]
    for m in coupes:
        m.show_render = False
        m.show_viewport = False
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    arbre = BVHTree.FromObject(basemesh, depsgraph)
    corps = basemesh.evaluated_get(depsgraph)
    mc = corps.matrix_world
    lc = []
    for face in corps.data.polygons:
        pts = [mc @ corps.data.vertices[i].co for i in face.vertices]
        n = len(pts)
        lc.append(sum((pts[i] - pts[(i + 1) % n]).length for i in range(n)) / n)
    arete_corps = sum(lc) / len(lc) if lc else 0.02

    mp = clothes.matrix_world
    aretes = [((mp @ clothes.data.vertices[a].co)
               - (mp @ clothes.data.vertices[b].co)).length
              for a, b in (e.vertices for e in clothes.data.edges)]
    arete_proxy = sum(aretes) / len(aretes) if aretes else 0.02
    ecarts = []
    for sommet in clothes.data.vertices:
        _, _, _, d = arbre.find_nearest(mp @ sommet.co)
        ecarts.append(d if d is not None else 0.0)
    for m in coupes:
        m.show_render = True
        m.show_viewport = True

    ecarts.sort()
    maxi = ecarts[-1] if ecarts else 0.0
    p99 = ecarts[int(len(ecarts) * 0.99)] if ecarts else 0.0
    densite = arete_proxy / arete_corps if arete_corps else 1.0
    forme = p99 / arete_proxy if arete_proxy else 0.0
    # ⚠ On prend le 99e percentile et non le maximum : un seul sommet aberrant
    # suffirait a faire passer une retopologie pour un changement de forme.
    hauteur = max(bounds([mp @ v.co for v in clothes.data.vertices])[1])
    # ⚠⚠ « Evidence » n'est pas UN cas mais DEUX, et leur traitement differe.
    # Un objet dont la silhouette entiere est autre (squelette, sirene) se
    # montre nu et en entier : une seule prise, rien d'ajoute. Un objet dont
    # l'evidence est LOCALE (un sexe ajoute) ou PARTIELLE (une tete seule) se
    # montre en PAIRE, lisse contre maille, la moitie maillee bien plus claire.
    # Preference de Raphael, planche du 06-09. Vu apres coup : j'appliquais a
    # tous le traitement de l'un.
    # ⚠⚠ Ce qui separe une silhouette AUTRE d'un simple ajout n'est ni
    # l'ampleur de l'ecart ni l'etendue de la zone retenue, mais la PART DU
    # MAILLAGE qui s'eloigne du corps. Un squelette est tout entier a
    # l'interieur, une sirene a la moitie du corps ailleurs ; un sexe ajoute ne
    # concerne que ses propres sommets. Mesure du 06-09, apres deux criteres
    # rates : l'ampleur classait la sirene comme un ajout, l'etendue de zone
    # faisait l'inverse.
    part_loin = sum(1 for d in ecarts if d > 0.01) / max(len(ecarts), 1)
    # ⚠⚠ L'ORDRE des regles compte autant que leurs seuils. Deux inversions
    # mesurees le 06-09 : un maillage a 412 sommets s'ecarte du corps sur 47 %
    # de ses sommets par simple FACETTAGE, donc la regle de « silhouette
    # autre » le capturait avant celle de densite ; et la sirene, dont 5 %
    # seulement des sommets s'eloignent mais de 74 cm, tombait dans les ajouts.
    # La densite passe donc en premier, et l'AMPLEUR avant la PART.
    if densite > 1.5:
        quoi = "epure"          # un maillage de jeu, quoi qu'il fasse
    elif hauteur < 0.9:
        quoi = "diptyque"                # un objet partiel, une tete seule
    elif maxi > 0.30:
        quoi = "portrait"             # un membre remplace : la sirene
    elif part_loin > 0.25:
        quoi = "portrait"             # tout le maillage ailleurs : le squelette
    elif maxi > 0.06:
        quoi = "diptyque"                # un ajout local : un sexe
    elif forme < 0.30:
        # ⚠⚠ Seuil ramene de 1,0 a 0,30. Mon raisonnement etait qu'une
        # retopologie s'ecarte du corps d'au plus UNE arete : c'est juste, mais
        # les changements de forme reels de ce pack sont eux aussi **sous
        # l'arete**, 0,58 pour une musculature. Ils restent pourtant cinq a
        # sept fois au-dessus des vraies retopologies, mesurees a 0,00, 0,08 et
        # 0,11. C'est donc l'ECART ENTRE LES DEUX POPULATIONS qui donne le
        # seuil, non un raisonnement a priori sur la maille.
        quoi = "epure"
    else:
        quoi = "carte"
    print("MESURE %-42s %6d %6.2f %6.2f %7.3f %6.0f%% %s"
          % (clothes.name[:42], len(clothes.data.vertices),
             densite, forme, maxi, 100.0 * part_loin, quoi))
    return quoi


def peindre_densite(clothes, basemesh, seuil=1.6, normaliser=False):
    """Marquer ou le maillage du proxy est plus grossier ou plus fin.

    ⭐⭐ Question de Raphael le 06-09 : la couleur montre ou la FORME diffère,
    pas ou la TOPOLOGIE diffère, et il ne faut pas confondre les deux. Un
    maillage basse resolution a la meme forme generale : il ne s'ecarte du corps
    que par ses facettes, donc la carte d'ecart n'y marque que du bruit de
    facettage.

    Cette seconde mesure est independante : on compare la longueur d'arete
    **locale** du proxy a celle du corps au point le plus proche. Le rapport dit
    « ici la maille est plus grossiere », et un proxy dont seule l'oreille est
    raffinee s'allume sur l'oreille.

    ⚠ L'enjeu est pratique : la bibliotheque de MPFB n'affiche qu'un **nom et
    une image de 120 px**, verifie dans `assetlibrarypanel.py`. Un titre comme
    « alpha 7 ear topology » ne dit presque rien, donc la vignette doit dire
    seule de quoi il s'agit.
    """
    from mathutils.bvhtree import BVHTree
    # ⚠⚠ Le corps du studio porte une SUBDIVISION : son maillage evalue a des
    # aretes deux fois plus courtes que son maillage reel, donc tout proxy
    # paraissait deux fois plus grossier qu'il n'est. Mesure du 06-09 : rapport
    # median de 2,09 sur deux proxies de densite comparable au corps, et 100 %
    # des sommets marques sur les cinq assets. Un resultat a 100 % partout est
    # aussi suspect qu'un resultat a zero.
    coupes = [m for m in basemesh.modifiers
              if m.type in ("SUBSURF", "MULTIRES") and m.show_render]
    for m in coupes:
        m.show_render = False
        m.show_viewport = False
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    corps = basemesh.evaluated_get(depsgraph)
    arbre = BVHTree.FromObject(basemesh, depsgraph)
    if coupes:
        print("   %d subdivision(s) du corps neutralisee(s) pour la mesure"
              % len(coupes))

    # longueur d'arete moyenne par face du corps, en monde
    mc = corps.matrix_world
    par_face = []
    for face in corps.data.polygons:
        sommets = [mc @ corps.data.vertices[i].co for i in face.vertices]
        n = len(sommets)
        aretes = [(sommets[i] - sommets[(i + 1) % n]).length for i in range(n)]
        par_face.append(sum(aretes) / n)

    # longueur d'arete moyenne par sommet du proxy
    mp = clothes.matrix_world
    cumul = [0.0] * len(clothes.data.vertices)
    compte = [0] * len(clothes.data.vertices)
    for arete in clothes.data.edges:
        a, b = arete.vertices
        d = ((mp @ clothes.data.vertices[a].co)
             - (mp @ clothes.data.vertices[b].co)).length
        cumul[a] += d; compte[a] += 1
        cumul[b] += d; compte[b] += 1

    couche = clothes.data.color_attributes.get("densite")
    if couche is None:
        couche = clothes.data.color_attributes.new(
            name="densite", type="FLOAT_COLOR", domain="POINT")
    rapports = []
    for i, sommet in enumerate(clothes.data.vertices):
        locale = cumul[i] / compte[i] if compte[i] else 0.0
        _, _, indice, _ = arbre.find_nearest(mp @ sommet.co)
        ref = par_face[indice] if indice is not None and indice < len(par_face) else 0.0
        r = (locale / ref) if ref > 1e-9 else 1.0
        rapports.append(r)
    if normaliser:
        # ⭐ Normaliser par la mediane : sur une retopologie le rapport a la
        # base vaut 1,00 partout et il n'y a rien a peindre. Divise par sa
        # mediane, il ne reste que ce que CE proxy a fait de different du
        # schema de densite de la base, donc les zones retravaillees.
        milieu = sorted(rapports)[len(rapports) // 2]
        if milieu > 1e-9:
            rapports = [r / milieu for r in rapports]
        print("   densite normalisee par la mediane brute %.2f" % milieu)
    forts = 0
    for i, r in enumerate(rapports):
        # ⚠ Le rapport est multiplicatif : un maillage deux fois plus grossier
        # donne 2, deux fois plus fin 0,5. C'est donc son LOGARITHME qu'il faut
        # peindre, sinon le plus fin ne peut jamais atteindre l'intensite du
        # plus grossier.
        ecart = abs(math.log(max(r, 1e-6), 2))
        v = min(1.0, ecart / math.log(seuil, 2))
        forts += v > 0.5
        couche.data[i].color = (v, v, v, 1.0)
    for m in coupes:
        m.show_render = True
        m.show_viewport = True
    tri = sorted(rapports)
    print("   densite : rapport median %.2f, quartiles %.2f et %.2f, "
          "%d sommets sur %d marques (%.0f%%)"
          % (tri[len(tri) // 2], tri[len(tri) // 4], tri[3 * len(tri) // 4],
             forts, len(rapports), 100.0 * forts / max(len(rapports), 1)))
    return "densite", [mp @ clothes.data.vertices[i].co
                       for i, r in enumerate(rapports)
                       if abs(math.log(max(r, 1e-6), 2)) > math.log(seuil, 2) * 0.5]


def mesurer_les_grappes(clothes, basemesh, nom=""):
    """La dispersion des sommets absents de la base : combien de grappes.

    ⚠ Les composantes se comptent sur les ARETES DU PROXY, non par distance :
    deux zones voisines mais non reliees (les deux omoplates) doivent compter
    pour deux, et un regroupement par distance les fondrait selon le rayon
    choisi. Le maillage porte deja la bonne relation de voisinage.
    """
    from mathutils.kdtree import KDTree
    coupes = [m for m in basemesh.modifiers
              if m.type in ("SUBSURF", "MULTIRES") and m.show_render]
    for m in coupes:
        m.show_render = False
        m.show_viewport = False
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    corps = basemesh.evaluated_get(depsgraph)
    mc = corps.matrix_world
    arbre = KDTree(len(corps.data.vertices))
    for i, sommet in enumerate(corps.data.vertices):
        arbre.insert(mc @ sommet.co, i)
    arbre.balance()
    aretes_base = [(mc @ corps.data.vertices[a].co
                    - mc @ corps.data.vertices[b].co).length
                   for a, b in (e.vertices for e in corps.data.edges)]
    tolerance = (0.1 * (sum(aretes_base) / len(aretes_base))
                 if aretes_base else 0.001)

    mp = clothes.matrix_world
    marque = []
    for sommet in clothes.data.vertices:
        _, _, d = arbre.find(mp @ sommet.co)
        marque.append(d is None or d > tolerance)
    for m in coupes:
        m.show_render = True
        m.show_viewport = True

    total = len(marque)
    marques = sum(marque)
    if marques == 0:
        print("-- ZONES %-46s neufs 0%%" % nom)
        return

    # composantes connexes des sommets marques, par union-find sur les aretes
    parent = list(range(total))

    def racine(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for arete in clothes.data.edges:
        a, b = arete.vertices
        if marque[a] and marque[b]:
            ra, rb = racine(a), racine(b)
            if ra != rb:
                parent[ra] = rb

    tailles = {}
    for i in range(total):
        if marque[i]:
            r = racine(i)
            tailles[r] = tailles.get(r, 0) + 1
    ordre = sorted(tailles.values(), reverse=True)
    notables = [t for t in ordre if t >= 0.02 * marques]

    zs = [(mp @ clothes.data.vertices[i].co)[2]
          for i in range(total) if marque[i]]
    zo = [(mp @ s.co)[2] for s in clothes.data.vertices]
    etendue = ((max(zs) - min(zs)) / max(max(zo) - min(zo), 1e-6)) if zs else 0.0

    # ⚠ Premier critere essaye et FAUX : « une seule grosse grappe = local ».
    # Le maillage etant connexe, une musculature repartie sur tout le corps ne
    # forme qu une grappe et sortait LOCAL alors qu elle s etale sur 91 % de la
    # hauteur. C est l ETENDUE qui decide, le nombre de grappes ne fait que la
    # nuancer.
    if 100.0 * marques / total > 90.0:
        regime = "GLOBAL"
    elif etendue < 0.35:
        regime = "LOCAL"
    else:
        regime = "DISPERSE"
    # ⭐ Le detail par grappe : sans lui on sait qu'il y a « six zones » mais
    # pas si elles sont aux yeux, a la bouche ou ailleurs, donc on ne peut pas
    # choisir un cadrage.
    zo_bas = min(zo)
    zo_haut = max(zo)
    hauteur_objet = max(zo_haut - zo_bas, 1e-6)
    membres_par_racine = {}
    for i in range(total):
        if marque[i]:
            membres_par_racine.setdefault(racine(i), []).append(i)
    groupes_tries = sorted(membres_par_racine.items(),
                           key=lambda kv: len(kv[1]), reverse=True)
    for rang, (_, membres) in enumerate(groupes_tries, 1):
        if len(membres) < 0.02 * marques:
            continue
        pts = [mp @ clothes.data.vertices[i].co for i in membres]
        hs = [(p[2] - zo_bas) / hauteur_objet for p in pts]
        xs = [p[0] for p in pts]
        print("   DETAIL grappe %d : %5d sommets, hauteur %.2f a %.2f, "
              "x median %+.3f" % (rang, len(membres), min(hs), max(hs),
                                  sorted(xs)[len(xs) // 2]))
    print("-- ZONES %-46s neufs %5.1f%%  grappes %3d  plus_gros %5.1f%%  "
          "etendue %5.1f%%  %s"
          % (nom, 100.0 * marques / total, len(notables),
             100.0 * ordre[0] / marques, 100.0 * etendue, regime))


def grappes_des_neufs(clothes, indices_neufs):
    """Regrouper des indices de sommets en composantes connexes du proxy.

    Reprend le principe de mesurer_les_grappes, mais retourne les INDICES de
    chaque grappe notable (>= 2% du total marque), triees par taille
    decroissante, pour qu'on puisse peindre et cadrer CHACUNE separement.
    """
    marque = set(indices_neufs)
    if not marque:
        return []
    parent = {i: i for i in marque}

    def racine(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for arete in clothes.data.edges:
        a, b = arete.vertices
        if a in marque and b in marque:
            ra, rb = racine(a), racine(b)
            if ra != rb:
                parent[ra] = rb
    groupes = {}
    for i in marque:
        groupes.setdefault(racine(i), []).append(i)
    seuil = 0.02 * len(marque)
    notables = [g for g in groupes.values() if len(g) >= seuil]
    notables.sort(key=len, reverse=True)
    return notables


def peindre_indices(clothes, indices):
    """Ecrire l'attribut « neuf » pour EXACTEMENT ces sommets, les autres a 0.

    Reutilise pour l'overview (tous les indices) et pour chaque cellule du
    polyptyque (les indices d'une seule grappe).
    """
    couche = clothes.data.color_attributes.get("neuf")
    if couche is None:
        couche = clothes.data.color_attributes.new(
            name="neuf", type="FLOAT_COLOR", domain="POINT")
    marque = set(indices)
    for i in range(len(clothes.data.vertices)):
        v = 1.0 if i in marque else 0.0
        couche.data[i].color = (v, v, v, 1.0)


def peindre_les_nouveaux(clothes, basemesh, tolerance=None):



    """Peindre les sommets du proxy qui ne sont dans le maillage de base.

    ⚠ La comparaison se fait en monde, sur les SOMMETS et non sur les faces :
    un sommet repris tel quel de la base est a distance nulle d'un sommet de
    base, tandis qu'un sommet retopologise tombe au milieu d'une face et s'en
    ecarte d'une fraction d'arete. La tolerance vaut donc un dixieme de l'arete
    moyenne de la base, ce qui separe franchement les deux cas.

    ⚠⚠ Les subdivisions du corps sont coupees pour la mesure, comme ailleurs :
    sinon le maillage evalue porte des sommets intermediaires que le proxy ne
    peut pas reprendre, et tout ressort comme retravaille.
    """
    from mathutils.kdtree import KDTree
    coupes = [m for m in basemesh.modifiers
              if m.type in ("SUBSURF", "MULTIRES") and m.show_render]
    for m in coupes:
        m.show_render = False
        m.show_viewport = False
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    corps = basemesh.evaluated_get(depsgraph)
    mc = corps.matrix_world

    arbre = KDTree(len(corps.data.vertices))
    for i, sommet in enumerate(corps.data.vertices):
        arbre.insert(mc @ sommet.co, i)
    arbre.balance()

    if tolerance is None:
        aretes = [(mc @ corps.data.vertices[a].co
                   - mc @ corps.data.vertices[b].co).length
                  for a, b in (e.vertices for e in corps.data.edges)]
        tolerance = 0.1 * (sum(aretes) / len(aretes)) if aretes else 0.001

    couche = clothes.data.color_attributes.get("neuf")
    if couche is None:
        couche = clothes.data.color_attributes.new(
            name="neuf", type="FLOAT_COLOR", domain="POINT")
    mp = clothes.matrix_world
    neufs = []
    indices_neufs = []
    for i, sommet in enumerate(clothes.data.vertices):
        p = mp @ sommet.co
        _, _, d = arbre.find(p)
        v = 1.0 if (d is None or d > tolerance) else 0.0
        couche.data[i].color = (v, v, v, 1.0)
        if v:
            neufs.append(p)
            indices_neufs.append(i)
    for m in coupes:
        m.show_render = True
        m.show_viewport = True
    if dilatation_zone > 0:
        # ⭐ Dilatation le long des ARETES du maillage : chaque tour ajoute
        # les voisins immediats des sommets deja marques. Une ligne d'un
        # sommet de large (une paupiere) s'epaissit d'autant, une zone deja
        # large (un sexe) ne bouge presque pas.
        marques = set(indices_neufs)
        voisins = {}
        for arete in clothes.data.edges:
            a, b = arete.vertices
            voisins.setdefault(a, []).append(b)
            voisins.setdefault(b, []).append(a)
        for _ in range(dilatation_zone):
            ajout = set()
            for i in marques:
                ajout.update(voisins.get(i, ()))
            marques |= ajout
        avant_dilatation = len(indices_neufs)
        indices_neufs = sorted(marques)
        neufs = [mp @ clothes.data.vertices[i].co for i in indices_neufs]
        for i in indices_neufs:
            couche.data[i].color = (1.0, 1.0, 1.0, 1.0)
        print("   zone dilatee de %d anneau(x) : %d sommets marques au lieu "
              "de %d" % (dilatation_zone, len(indices_neufs), avant_dilatation))
    global INDICES_NEUFS
    INDICES_NEUFS = set(indices_neufs)
    print("   sommets absents de la base : %d sur %d (%.0f%%), tolerance %.4f m"
          % (len(neufs), len(clothes.data.vertices),
             100.0 * len(neufs) / max(len(clothes.data.vertices), 1), tolerance))
    return "neuf", neufs


def peindre_lecart(clothes, basemesh, part=0.90, plancher=0.0):
    """Ecrire l'ecart au corps dans un attribut du maillage.

    ⭐⭐ Idee de Raphael le 06-09 : puisque seule une partie du maillage est
    modifiee, et qu'on mesure deja cet ecart sommet par sommet, autant le
    **montrer**. La vignette dit alors deux choses en une seule image, ce qui a
    ete modifie et de quoi c'est fait, en gardant le corps reconnaissable
    autour.

    L'ecart est normalise sur son maximum et durci par un seuil, pour que la
    zone se detache franchement au lieu de se fondre en degrade.
    """
    from mathutils.bvhtree import BVHTree
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    arbre = BVHTree.FromObject(basemesh, depsgraph)
    monde = clothes.matrix_world
    distances = []
    for sommet in clothes.data.vertices:
        _, _, _, d = arbre.find_nearest(monde @ sommet.co)
        distances.append(d if d is not None else 0.0)
    # ⚠⚠ Ne PAS normaliser sur le maximum : il suffit d'un sommet aberrant
    # ailleurs sur le corps pour que la zone qui compte passe sous le seuil.
    # Mesure du 06-09 : sur `simple_penis`, 1 % des sommets etaient peints et
    # pas ceux du sexe. On reprend le seuil qui a fait ses preuves pour le
    # cadrage, quatre fois la mediane ou un tiers du maximum, et l'on peint en
    # rampe au-dessus.
    tri = sorted(distances)
    median = tri[len(tri) // 2]
    maximum = tri[-1] or 1.0
    # ⚠⚠ Pour un corps ENTIER, le but n'est plus de designer un ajout mais de
    # dire OU le proxy change quelque chose : la tete, le torse, les jambes.
    # Un seuil calcule sur le maximum ou sur un multiple de la mediane ne peint
    # alors presque rien, l'ecart etant diffus. On cale donc la rampe sur un
    # PERCENTILE de la distribution : le dixieme le plus ecarte s'allume.
    bas = tri[int(len(tri) * part)]
    haut = tri[int(len(tri) * (part + (1.0 - part) * 0.6))]
    if plancher > 0.0 and bas < plancher:
        # ⚠ La rampe par percentile allume toujours 10 % des sommets, meme
        # quand il n'y a rien a montrer. Le plancher absolu la fait taire.
        bas = plancher
        print("   plancher absolu %.4f m applique a la rampe" % plancher)
    if haut <= bas:
        haut = bas * 1.5 + 1e-6
    couche = clothes.data.color_attributes.get("ecart")
    if couche is None:
        couche = clothes.data.color_attributes.new(
            name="ecart", type="FLOAT_COLOR", domain="POINT")
    forts = 0
    for i, d in enumerate(distances):
        v = 0.0 if d <= bas else min(1.0, (d - bas) / max(haut - bas, 1e-6))
        forts += v > 0.5
        couche.data[i].color = (v, v, v, 1.0)
    print("   ecart peint : mediane %.4f m, max %.4f m, rampe %.4f a %.4f m, "
          "%d sommets sur %d marques (%.0f%%)"
          % (median, maximum, bas, haut, forts, len(distances),
             100.0 * forts / max(len(distances), 1)))
    # ⭐ Arbitrage de Raphael le 06-09 : le cadre doit etre le PLUS SERRE qui
    # garde toutes les zones colorees visibles. La tete et le bas des jambes
    # sortent donc du champ quand rien ne les touche, et la regle reste unique
    # pour tous les assets, donc le resultat homogene.
    peints = [monde @ clothes.data.vertices[i].co
              for i, d in enumerate(distances) if d > bas]
    return "ecart", peints


def materiau_deux_zones(objet, attribut, fraction, couleur="sombre",
                        mise_en_valeur=None):
    """Gris et lisse la ou rien ne change, blanc et maille la ou ca change.

    ⚠ Le lissage est une propriete de FACE : on ne peut pas melanger lisse et
    facettes par sommet. C'est donc le **trace des aretes** qui marque la zone,
    module par l'attribut d'ecart, et la base qui s'eclaircit au meme endroit.
    """
    materiau = bpy.data.materials.new("deux_zones")
    materiau.use_nodes = True
    arbre = materiau.node_tree
    principe = arbre.nodes.get("Principled BSDF")
    sortie = arbre.nodes.get("Material Output")
    if principe is None or sortie is None:
        return
    if "Roughness" in principe.inputs:
        principe.inputs["Roughness"].default_value = 0.55

    ecart = arbre.nodes.new("ShaderNodeVertexColor")
    ecart.layer_name = attribut
    # la base : gris du studio, qui s'eclaircit vers le blanc dans la zone
    teinte = arbre.nodes.new("ShaderNodeMixRGB")
    teinte.inputs[1].default_value = GRIS_STUDIO
    teinte.inputs[2].default_value = (mise_en_valeur or BLANC_TECHNIQUE)
    arbre.links.new(ecart.outputs["Color"], teinte.inputs[0])
    arbre.links.new(teinte.outputs["Color"], principe.inputs["Base Color"])

    aretes = [(objet.data.vertices[a].co - objet.data.vertices[b].co).length
              for a, b in (arete.vertices for arete in objet.data.edges)]
    moyenne = sum(aretes) / len(aretes) if aretes else 0.02
    fil = arbre.nodes.new("ShaderNodeWireframe")
    fil.use_pixel_size = False
    fil.inputs["Size"].default_value = moyenne * fraction
    # ⭐ Le trait n'apparait QUE dans la zone : on multiplie le facteur du
    # noeud Wireframe par l'ecart peint.
    masque = arbre.nodes.new("ShaderNodeMath")
    masque.operation = "MULTIPLY"
    arbre.links.new(fil.outputs["Fac"], masque.inputs[0])
    arbre.links.new(ecart.outputs["Color"], masque.inputs[1])
    trait = arbre.nodes.new("ShaderNodeEmission")
    trait.inputs["Color"].default_value = COULEURS_ARETES.get(couleur)
    melange = arbre.nodes.new("ShaderNodeMixShader")
    arbre.links.new(masque.outputs["Value"], melange.inputs["Fac"])
    arbre.links.new(principe.outputs["BSDF"], melange.inputs[1])
    arbre.links.new(trait.outputs["Emission"], melange.inputs[2])
    # ⭐⭐ Une part d'EMISSION dans la zone, ajoutee le 06-09. Sans elle la
    # couleur de mise en valeur n'est qu'une couleur diffuse, donc l'eclairage
    # la divise : un vermillon a 0,84 ressort a 0,42, brun et terne, et sur un
    # fond de theme sombre il ne se detache plus. Avec une part d'emission la
    # zone garde sa teinte quel que soit l'eclairage. ⚠ Une part seulement, et
    # non la totalite : a 100 % la zone devient un aplat qui perd le modele du
    # corps, donc on ne voit plus la forme sous la couleur.
    eclat = arbre.nodes.new("ShaderNodeEmission")
    eclat.inputs["Color"].default_value = (mise_en_valeur or BLANC_TECHNIQUE)
    eclat.inputs["Strength"].default_value = 1.0
    dose = arbre.nodes.new("ShaderNodeMath")
    dose.operation = "MULTIPLY"
    dose.inputs[1].default_value = PART_EMISSION
    arbre.links.new(ecart.outputs["Color"], dose.inputs[0])
    par_dessus = arbre.nodes.new("ShaderNodeMixShader")
    arbre.links.new(dose.outputs["Value"], par_dessus.inputs["Fac"])
    arbre.links.new(melange.outputs["Shader"], par_dessus.inputs[1])
    arbre.links.new(eclat.outputs["Emission"], par_dessus.inputs[2])
    arbre.links.new(par_dessus.outputs["Shader"], sortie.inputs["Surface"])

    objet.data.materials.clear()
    objet.data.materials.append(materiau)
    for face in objet.data.polygons:
        face.material_index = 0
    print("   materiau a deux zones pose, trait %.4f m" % (moyenne * fraction))


def sens_de_lobjet(points, camera):
    """Horizontal ou vertical, vu de la camera.

    ⭐ Arbitrage de Raphael le 06-09 : quand on assemble deux prises, la coupe
    doit suivre le sens de l'objet. Un sexe en erection est horizontal, donc
    coupe horizontale ; au repos il pend, donc coupe verticale. Cela se mesure :
    on projette la zone qui compte sur les axes de la camera et on compare ses
    deux etendues.

    ⚠ Le sens decide aussi de la FORME des prises, puisque deux prises doivent
    s'assembler en carre : couchees 256 x 128 pour une coupe horizontale,
    debout 128 x 256 pour une verticale.
    """
    base = camera.matrix_world.to_3x3()
    droite = base.col[0].normalized()
    haut = base.col[1].normalized()
    largeurs = [p.dot(droite) for p in points]
    hauteurs = [p.dot(haut) for p in points]
    dl = max(largeurs) - min(largeurs)
    dh = max(hauteurs) - min(hauteurs)
    sens = "horizontal" if dl >= dh else "vertical"
    print("   zone de %.3f m de large sur %.3f m de haut : objet %s"
          % (dl, dh, sens))
    return sens


def le_maillage_apprend_il(sans, avec):
    """Le maillage ajoute-t-il de l'information a cette vignette ?

    ⭐ Question posee par Raphael : arbitrer pour chaque asset si la version
    avec maillage vaut la peine. Elle se mesure, en comparant les deux prises :
    si le trace change peu de pixels, il n'apprend rien et une seule image
    suffit. Le seuil est empirique, a calibrer sur un pack.

    ⚠⚠ Cette fonction mesurait FAUX depuis le debut, corrige le 06-09, et le
    piege tient en une ligne :

        convert A B -compose difference -composite -format "%[fx:mean]" info:

    renvoie la meme valeur pour TOUTES les paires, y compris deux fichiers
    identiques au bit, parce que `%[fx:mean]` dans `info:` s'evalue sur la
    **premiere image de la liste** et non sur le composite. Il faut donc ecrire
    le composite dans un fichier avant de le mesurer. Et couper l'alpha : sur
    fond transparent la difference s'evalue autrement et invente un ecart.

    ⭐ On rend deux nombres plutot qu'un : la moyenne, et la **part de pixels
    changes**, qui dit mieux si le trace se voit. Mesure sur les quatre
    diptyques du pack : 26 a 56 % de pixels changes, donc la moitie maillee
    apprend bien quelque chose partout.
    """
    # ⚠⚠ Et surtout : PAS d'ImageMagick. `convert` n'existe pas dans le bac a
    # sable Flatpak de Blender, donc cette mesure ne pouvait jamais aboutir sur
    # cette machine ; l'ancienne version avalait l'erreur et le journal
    # affichait « ? » sans dire pourquoi. On lit donc les deux images par l'API
    # de Blender, ce qui ne depend de rien et vaut mieux pour une contribution
    # amont, dont les usagers n'ont pas forcement ImageMagick.
    images = []
    try:
        for chemin in (sans, avec):
            image = bpy.data.images.load(chemin)
            images.append(image)
        gauche, droite = (list(i.pixels) for i in images)
        if len(gauche) != len(droite):
            return None
        # ⚠ Sauter le canal alpha : sur fond transparent il domine la
        # difference et invente un ecart la ou il n'y en a pas.
        total = 0.0
        changes = 0
        pixels = len(gauche) // 4
        for indice in range(pixels):
            base = indice * 4
            ecart = max(abs(gauche[base + canal] - droite[base + canal])
                        for canal in range(3))
            total += ecart
            if ecart > 0.06:
                changes += 1
        moyenne = 255.0 * total / max(pixels, 1)
        part = 100.0 * changes / max(pixels, 1)
    except Exception as souci:
        print("-- NOTE: mesure du maillage impossible (%s: %s)"
              % (type(souci).__name__, souci))
        return None
    finally:
        for image in images:
            bpy.data.images.remove(image)
    return (moyenne, part)


def ou_le_proxy_secarte(clothes, basemesh, part=0.03):
    """Les points du proxy qui s'ecartent le plus du corps de base.

    ⭐⭐ Cadrer sur la tete distingue les proxies par leur DENSITE et rend
    aveugle a tout le reste : `wolgade_female_muscular` et sa version moins
    musclee ont des tetes identiques au sommet pres, 2 711 sur 2 711, alors que
    464 sommets different sur le corps. Leur vignette est alors rigoureusement
    la meme image. Il faut donc cadrer la ou le proxy **s'ecarte du corps**.

    ⚠ Un proxy n'a pas le meme nombre de sommets que le basemesh : il n'y a
    aucune correspondance un pour un. On mesure donc, pour chaque sommet du
    proxy, sa distance a la **surface** du corps, par un arbre BVH.
    """
    from mathutils.bvhtree import BVHTree
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    arbre = BVHTree.FromObject(basemesh, depsgraph)
    evalue = clothes.evaluated_get(depsgraph)
    monde = evalue.matrix_world
    ecarts = []
    for sommet in evalue.data.vertices:
        point = monde @ sommet.co
        _, _, _, distance = arbre.find_nearest(point)
        if distance is not None:
            ecarts.append((distance, point))
    if not ecarts:
        return []
    ecarts.sort(key=lambda e: -e[0])
    tous = list(ecarts)
    # ⚠⚠ Prendre une FRACTION fixe des sommets ne marche pas : sur un proxy
    # generique l'ecart median vaut 0,3 mm et le maximum 13 mm, donc 15 % des
    # sommets sont disperses sur tout le corps et le cadre reprend le corps
    # entier. Il faut un seuil **relatif a la distribution** : ne garder que ce
    # qui s'ecarte franchement, et plafonner a une petite part.
    median = ecarts[len(ecarts) // 2][0]
    maximum = ecarts[0][0]
    seuil = max(median * 4.0, maximum * 0.35)
    retenus = [e for e in ecarts if e[0] >= seuil][:max(12, int(len(ecarts) * part))]
    if len(retenus) < 12:
        retenus = ecarts[:12]
    # ⚠⚠ Ne garder que les sommets qui s'ecartent le plus **tronque l'objet** :
    # sur un sexe en erection, la pointe s'ecarte beaucoup et la racine peu,
    # donc le cadre tombait sur la seule extremite et l'on ne reconnaissait
    # rien. Vu le 06-09. On fait donc CROITRE la zone : tout sommet du proxy
    # situe a moins de 1,6 rayon du centre de la zone en fait partie, ce qui
    # rattrape la base de l'organe sans revenir au corps entier.
    # ⚠⚠ Le rayon ne peut pas etre le MAXIMUM des distances au centre : il est
    # alors fixe par le sommet le plus isole, et la zone avale le corps. Mesure
    # le 06-09 sur `proxy_with_helpers_test` : 81 sommets crus, rayon 0,532 m,
    # 11 822 sommets retenus, soit 92 % du sujet, et la regle des 12 % rejetait
    # le diptyque d'un proxy de sexe. Les deux autres sexes, dont la zone crue
    # est groupee, gardaient 4 a 5 cm et sortaient juste : le defaut ne se voit
    # donc que sur le cas disperse. On ecrete d'abord : centre par la MEDIANE
    # par axe, puis on jette ce qui depasse trois fois la distance mediane, ce
    # qui resiste a une moitie de sommets epars, et seulement ensuite on prend
    # le maximum du noyau, qui doit rester l'etendue vraie de l'organe.
    def _mediane(valeurs):
        v = sorted(valeurs)
        return v[len(v) // 2]

    centre = Vector((_mediane([p.x for _, p in retenus]),
                     _mediane([p.y for _, p in retenus]),
                     _mediane([p.z for _, p in retenus])))
    distances = [(p - centre).length for _, p in retenus]
    limite = max(_mediane(distances) * 3.0, 0.02)
    noyau = [e for e, d in zip(retenus, distances) if d <= limite]
    if len(noyau) >= 8:
        if len(noyau) < len(retenus):
            print("   zone ecretee : %d sommets epars jetes sur %d"
                  % (len(retenus) - len(noyau), len(retenus)))
        retenus = noyau
        centre = sum((p for _, p in retenus), Vector()) / len(retenus)
    rayon = max((p - centre).length for _, p in retenus)
    voisins = [(d, p) for d, p in tous if (p - centre).length <= rayon * 1.6]
    if len(voisins) > len(retenus):
        print("   zone crue de %d a %d sommets (rayon %.3f m)"
              % (len(retenus), len(voisins), rayon))
        retenus = voisins
    print("   ecart au corps : median %.4f m, maximum %.4f m, seuil %.4f m, "
          "%d points sur %d" % (median, maximum, seuil, len(retenus), len(ecarts)))
    return [point for _, point in retenus]


def hide_bodies():
    """Hide every studio body from the render. The asset has already been fitted
    at this point, and fitting does not care about render visibility."""
    for body in BODIES:
        bpy.data.collections[body].hide_render = True
        for obj in bpy.data.collections[body].objects:
            obj.hide_render = True


# -- Framing. Same approach as the pose thumbnails: keep the studio angle, but
# recentre and move the camera until the subject fills the frame.

def asset_islands(objects):
    """World space vertex coordinates of the fitted geometry, grouped into
    connected pieces. The bounding box of an evaluated object does not take the
    fit into account, so the vertices have to be read out explicitly, and the
    pieces are what largest_group() reasons about."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    islands = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world

        # Union find over the edges, which is what makes a piece a piece.
        parent = list(range(len(mesh.vertices)))

        def root(index):
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        for edge in mesh.edges:
            (first, second) = edge.vertices
            (one, other) = (root(first), root(second))
            if one != other:
                parent[one] = other

        grouped = dict()
        for index in range(len(mesh.vertices)):
            grouped.setdefault(root(index), []).append(matrix @ mesh.vertices[index].co)
        islands.extend(grouped.values())

        evaluated.to_mesh_clear()
    return islands


def bounds(points):
    """(centre, size) of the world space bounding box of the given points."""
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    return ((low + high) / 2.0, high - low)


def split_on_gap(islands, camera, axis, gap_ratio):
    """Drop the smaller side of the widest empty band that separates whole pieces
    of the asset along the given axis of the camera view. Returns the islands
    unchanged when there is no such band.

    The band has to separate whole pieces, not merely the vertices sorted along
    the axis: an industrial piercing is a bar with a ball at each end, and the bar
    has so few vertices along its length that by vertex spacing alone it looks
    exactly like a pair of separate balls."""

    to_camera = camera.matrix_world.inverted()
    spans = []
    for island in islands:
        coordinates = [(to_camera @ point)[axis] for point in island]
        spans.append((min(coordinates), max(coordinates), island))
    spans.sort(key=lambda span: span[0])

    extent = max(span[1] for span in spans) - spans[0][0]
    if extent <= 0.0:
        return islands

    # Sweep the pieces in order, tracking how far the ones seen so far reach. A
    # piece that starts beyond that reach leaves a band that nothing crosses.
    widest = 0.0
    at = 0
    reach = spans[0][1]
    for index in range(1, len(spans)):
        gap = spans[index][0] - reach
        if gap > widest:
            widest = gap
            at = index
        reach = max(reach, spans[index][1])

    if widest < gap_ratio * extent:
        return islands

    before = spans[:at]
    after = spans[at:]
    counted = lambda group: sum(len(span[2]) for span in group)
    kept = before if counted(before) >= counted(after) else after
    return [span[2] for span in kept]


def largest_group(islands, camera, gap_ratio=GAP_RATIO):
    """Assets that come in pairs - earrings, wristbands, a left and a right shoe -
    are fitted to both sides of the body at once, and framing all of it at once
    gives a thumbnail of two specks at opposite edges with nothing in between.
    Where the pieces of the asset fall into two clearly separated groups on
    screen, only the larger group is framed, which turns that into a picture of
    one earring. Assets that merely consist of many pieces, such as a chain, run
    together with no empty band and are left alone."""
    for axis in [0, 1]:
        while True:
            grouped = split_on_gap(islands, camera, axis, gap_ratio)
            if len(grouped) == len(islands):
                break
            islands = grouped
    return islands


def frustum_tangents(camera, scene):
    """Tangents of the half field of view actually used for the render. Note that
    camera.data.angle_y cannot be used for this: with the default AUTO sensor fit
    the sensor is fitted to the larger side of the render, so at the square
    resolution of the thumbnails both axes use the horizontal field of view."""
    render = scene.render
    aspect_x = render.resolution_x * render.pixel_aspect_x
    aspect_y = render.resolution_y * render.pixel_aspect_y

    tangent = math.tan(camera.data.angle / 2.0)
    if camera.data.sensor_fit == "VERTICAL" or (camera.data.sensor_fit == "AUTO" and aspect_y > aspect_x):
        return (tangent * aspect_x / aspect_y, tangent)
    return (tangent, tangent * aspect_y / aspect_x)


def poser_azimut(camera, centre, degres):
    """Tourner la camera autour de l'axe vertical passant par le sujet.

    ⚠ La camera de rendu du studio n'a **aucune contrainte** : sa rotation est
    posee en dur, 88,4 degres d'inclinaison et -34 autour de Z. Il faut donc
    tourner ENSEMBLE sa position et son orientation, sinon elle regarde a cote.

    L'azimut est absolu, en degres : 0 place la camera devant le sujet, les
    valeurs negatives la portent d'un cote et les positives de l'autre. La
    hauteur et la distance ne changent pas, le cadrage etant refait ensuite.
    """
    voulu = math.radians(degres)
    delta = voulu - camera.rotation_euler.z
    rotation = Matrix.Rotation(delta, 4, "Z")
    camera.location = centre + (rotation @ (camera.location - centre))
    camera.rotation_euler.z = voulu
    # ⚠⚠ `depsgraph.update()`, pas `view_layer.update()` : le studio a un cycle
    # de dependance entre la camera et son empty, et seul le premier le resout.
    # Piege le plus couteux du chantier, deja paye deux fois.
    bpy.context.evaluated_depsgraph_get().update()


def fit_camera(camera, points, margin=None):
    """Keep the camera orientation, but recentre and move it so that everything in
    points sits inside the frustum with a bit of margin."""
    if margin is None:
        margin = MARGIN
    rotation = camera.matrix_world.to_3x3()
    to_camera = camera.matrix_world.inverted()
    local = [to_camera @ point for point in points]

    (tan_x, tan_y) = frustum_tangents(camera, bpy.context.scene)
    tan_x = tan_x / margin
    tan_y = tan_y / margin

    centre_x = (max(p.x for p in local) + min(p.x for p in local)) / 2.0
    centre_y = (max(p.y for p in local) + min(p.y for p in local)) / 2.0

    # Distance to move the camera backwards along its own view axis, so that the
    # widest and the tallest point both end up on the edge of the frustum.
    distance = max(max(p.z + abs(p.x - centre_x) / tan_x,
                       p.z + abs(p.y - centre_y) / tan_y) for p in local)

    camera.location = camera.location + rotation @ Vector((centre_x, centre_y, distance))


def zoom_instead_of_approaching(camera, centre):
    """Small assets would put the camera a few centimetres away, inside the near
    clip and with brutal perspective. Below MIN_DISTANCE the camera is pulled back
    to MIN_DISTANCE and the same framing is recovered with focal length, which
    keeps the apparent size identical."""
    forward = camera.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
    distance = (centre - camera.location).dot(forward)
    if distance <= 0.0 or distance >= MIN_DISTANCE:
        return distance
    camera.location = camera.location - forward * (MIN_DISTANCE - distance)
    camera.data.lens = camera.data.lens * MIN_DISTANCE / distance
    return MIN_DISTANCE


def aim_lights(camera, centre):
    """Move both light rigs onto the asset.

    The rigs are built for a figure standing at the origin, so for an asset that
    sits anywhere else - a ring on a hand, an earring at the side of a head -
    they would otherwise light empty air. Since the lights are children of the
    targets, moving a target takes its whole rig along.

    The rig is deliberately not scaled down for small assets. Shrinking it toward
    a 2 cm ring so that the area lights stayed soft relative to the subject was
    tried and is much worse: at a few centimetres the lights are no longer
    remotely point sources, the inverse square compensation of their energy stops
    holding, and the asset comes out dark and flat. Irradiance at a fixed distance
    does not care how large the subject is, so leaving the rig at studio scale
    exposes a ring and a full uniform alike."""

    for name in LIGHT_TARGETS:
        bpy.data.objects[name].location = centre

    # The targets track these, so this is what decides from which side the rigs
    # end up lighting the asset. Putting them where the render camera ended up
    # reproduces the relative geometry the studio was set up with.
    for name in LIGHT_CAMERAS:
        bpy.data.objects[name].location = camera.location


def raise_ambient(scene, ambient):
    """Lift the world background, so that glossy and metallic assets have
    something to reflect. Scaling the strength rather than replacing the world
    keeps the studio's own colour."""
    if ambient == 1.0:
        return
    world = scene.world
    if not world or not world.use_nodes:
        return
    for node in world.node_tree.nodes:
        if node.type == "BACKGROUND":
            node.inputs["Strength"].default_value = node.inputs["Strength"].default_value * ambient


# -- Arguments

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

force = False
download = True
whole = False
packname = None
samples = None
exposure = None
subdiv = 1
ambient = AMBIENT
wanted = []

index = 0
while index < len(argv):
    argument = argv[index]
    if argument in ["--pack", "--samples", "--subdiv", "--margin", "--exposure",
                    "--ambient", "--wire", "--top", "--wire-colour", "--shape",
                    "--device", "--cut", "--azimuth",
                    "--lights", "--world", "--highlight",
                    "--paint-part", "--out", "--albedo", "--paint-floor",
                    "--paint-exposure", "--paint-emission", "--zone-to-top",
                    "--resolution", "--base-force", "--paint-dilate",
                    "--frame-zone"]:
        index = index + 1
        if index >= len(argv):
            print(argument + " needs a value")
            sys.exit(1)
        if argument == "--pack":
            if packname:
                print("Only one --pack can be rendered per run")
                sys.exit(1)
            packname = argv[index]
        elif argument == "--samples":
            samples = int(argv[index])
        elif argument == "--subdiv":
            subdiv = int(argv[index])
        elif argument == "--margin":
            marge = float(argv[index])
            MARGIN = marge
        elif argument == "--ambient":
            ambient = float(argv[index])
        elif argument == "--wire":
            epaisseur_aretes = float(argv[index])
        elif argument == "--azimuth":
            azimut = float(argv[index])
        elif argument == "--cut":
            if argv[index] not in ("horizontal", "vertical"):
                sys.exit("--cut attend horizontal ou vertical, recu : %s"
                         % argv[index])
            coupe_forcee = argv[index]
        elif argument == "--device":
            # ⚠ Pas de `index = index + 1` ici : le bloc englobant l'a deja
            # fait, comme pour toutes les options a valeur. Ma premiere version
            # l'avancait deux fois et lisait le mot d'apres, donc le nom de
            # l'asset au lieu de l'exception.
            for morceau in argv[index].split(","):
                if "=" not in morceau:
                    sys.exit("--device attend nom=dispositif, recu : %s"
                             % morceau)
                nom, quel = morceau.split("=", 1)
                if quel not in ("epure", "diptyque", "carte", "portrait"):
                    sys.exit("dispositif inconnu : %s (epure, diptyque, "
                             "carte ou portrait)" % quel)
                exceptions[nom.strip()] = quel.strip()
        elif argument == "--top":
            part_haute = float(argv[index])
            part_haute_cli = part_haute
        elif argument == "--wire-colour":
            couleur_aretes = argv[index]
        elif argument == "--highlight":
            valeur_relief = argv[index]
        elif argument == "--zone-to-top":
            zone_a_la_couronne = float(argv[index])
        elif argument == "--resolution":
            resolution_forcee = int(argv[index])
        elif argument == "--frame-zone":
            paquet_de_zones = argv[index]
            if paquet_de_zones not in ("haut", "bas"):
                sys.exit("--frame-zone attend haut ou bas")
        elif argument == "--paint-dilate":
            dilatation_zone = int(argv[index])
        elif argument == "--base-force":
            corps_force = argv[index]
            if corps_force not in ("neutral", "male", "female"):
                sys.exit("--base-force attend neutral, male ou female")
        elif argument == "--paint-emission":
            PART_EMISSION = float(argv[index])
        elif argument == "--paint-exposure":
            expo_carte = float(argv[index])
        elif argument == "--paint-floor":
            plancher_ecart = float(argv[index])
        elif argument == "--paint-part":
            part_peinte = float(argv[index])
        elif argument == "--out":
            # ⚠ Le script n'avait aucune option de sortie : deux passes
            # de test s'ecrasaient l'une l'autre ET ecrasaient les
            # vignettes du depot.
            thumbdir = os.path.abspath(argv[index])
            if not os.path.isdir(thumbdir):
                os.makedirs(thumbdir)
        elif argument == "--albedo":
            # La couleur du corps. 0,62 est le gris du studio ; au-dela
            # on va vers le « porcelaine » demande sur fond noir.
            a = float(argv[index])
            GRIS_STUDIO = (a, a, min(1.0, a + 0.01), 1.0)
        elif argument == "--shape":
            forme = argv[index]
        elif argument == "--lights":
            lampes = argv[index]
        elif argument == "--world":
            monde_fond = float(argv[index])
        else:
            exposure = float(argv[index])
    elif argument == "--paint":
        peindre = True
    elif argument == "--zone":
        zone_seule = True
    elif argument == "--true-edges":
        vraies_aretes = True
    elif argument == "--auto":
        auto = True
    elif argument == "--measure-only":
        mesurer_seulement = True
    elif argument == "--frame-new":
        cadrer_neufs = True
    elif argument == "--polyptych":
        polyptyque = True
    elif argument == "--paint-new":
        peindre = True
        sommets_neufs = True
    elif argument == "--paint-rework":
        peindre = True
        densite = True
        densite_normalisee = True
    elif argument == "--paint-density":
        peindre = True
        densite = True
    elif argument == "--grey":
        gris = True
    elif argument == "--flat":
        facettes = True
    elif argument == "--compare":
        comparer = True
    elif argument == "--mesh-pair":
        paire_maillage = True
    elif argument == "--force":
        force = True
    elif argument == "--no-download":
        download = False
    elif argument == "--whole":
        whole = True
    elif argument.startswith("--"):
        print("Unknown option: " + argument)
        sys.exit(1)
    else:
        wanted.append(argument)
    index = index + 1

if not packname:
    print("--pack is required. This renders the mesh assets of exactly one pack,")
    print("for example: --pack jewelry01_cc0")
    sys.exit(1)

# Read before the first reload, since that is what makes the scene reusable.
blend_file = bpy.data.filepath

assets = pack_jobs(packname, download)

if wanted:
    assets = [asset for asset in assets if asset[0] in wanted]
if not assets:
    print("No mesh assets to render")
    sys.exit(1)

rendered = 0
skipped = 0
failed = 0

for (name, mhclo_file) in assets:
    destination = os.path.join(thumbdir, name + ".png")

    if os.path.exists(destination) and not force:
        print("-- SKIP (already exists): " + destination)
        skipped = skipped + 1
        continue

    print("-- ASSET: " + name)

    # Reloading the studio is the cheapest way to be sure that nothing survives
    # from the previous asset: no leftover meshes, materials or images, and the
    # cameras and light rigs back where the file has them. It costs about a
    # second against a render measured in tens of seconds.
    bpy.ops.wm.open_mainfile(filepath=blend_file)

    scene = bpy.context.scene
    if samples is not None:
        scene.cycles.samples = samples
    # ⚠⚠ Graine fixe, comme dans `rendertargetthumbs.py` ou je l'avais posee
    # sans la transposer ici. Sans elle, deux assets IDENTIQUES rendent des
    # images qui different de 2,4/255 par le seul bruit du moteur, ce qui rend
    # inutilisable le test le plus sur de fuite d'etat : le doublon du pack
    # doit produire deux vignettes au pixel pres. Vu le 06-09.
    scene.cycles.seed = 0
    scene.cycles.use_animated_seed = False
    if exposure is not None:
        scene.view_settings.exposure = exposure
    # ⚠⚠ Deux prises CARREES assemblees cote a cote font un rectangle de
    # 512 x 256, pas une icone. Une vignette de comparaison demande donc des
    # prises en DEMI-FORMAT : 128 x 256 pour une coupe verticale, 256 x 128
    # pour une coupe horizontale. Erreur commise le 06-09, rattrapee par
    # Raphael, et la garde de composesplit.py la refuse desormais.
    if forme == "portrait":
        scene.render.resolution_x = scene.render.resolution_y // 2
    elif forme == "couche":
        scene.render.resolution_y = scene.render.resolution_x // 2
    if resolution_forcee:
        scene.render.resolution_x = resolution_forcee
        scene.render.resolution_y = resolution_forcee
    memo_resolution = (scene.render.resolution_x, scene.render.resolution_y)
    raise_ambient(scene, ambient)
    if lampes or monde_fond is not None:
        reglages = {}
        for morceau in lampes.split(",") if lampes else []:
            nom, _, valeur = morceau.partition("=")
            reglages[nom.strip()] = float(valeur)
        regler_lampes(reglages, monde_fond)

    # ⚠ La boucle ne porte que le nom final de l'asset, pas sa fiche : le nom
    # suffit, il contient « female », « male » ou « penis » quand cela compte.
    # ⚠ Et « female » ne doit pas declencher « male » : les mots sont cherches
    # entiers, entoures d'espaces, jamais en sous-chaine. « unisex » ne
    # declenche donc rien non plus, ce qui est le comportement voulu.
    corps_voulu = corps_force or (deviner_le_sexe(name) if auto else BODY)
    basemesh = activer_le_corps(corps_voulu) or bpy.data.objects[corps_voulu]
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = basemesh

    try:
        clothes = load_asset(mhclo_file, basemesh, subdiv)
    except Exception as error:
        print("-- FAILED (" + type(error).__name__ + ": " + str(error) + "): " + name)
        failed = failed + 1
        continue

    # ⚠⚠ `MARGIN` est un global que la marge adaptative modifie a chaque asset.
    # Sans le remettre a sa valeur de depart, un asset herite de la marge du
    # precedent : `head_only` sortait minuscule parce qu'il avait recu le 4,0
    # calcule pour un sexe. Fuite d'etat entre iterations, sans erreur.
    MARGIN = marge if marge is not None else 1.10
    # ⚠ Meme raison : tout drapeau lu plus bas doit etre remis a zero ICI, sur
    # le chemin que TOUS les assets traversent, et non dans la branche qui le
    # pose. Sinon un asset non concerne herite du precedent, ou leve une
    # NameError s'il est le premier.
    fil_a_creer = None
    expo_blanche = False
    imposé = False
    ecarts = (ou_le_proxy_secarte(clothes, basemesh)
              if (comparer or auto or mesurer_seulement) else None)

    if mesurer_seulement:
        classer_lasset(clothes, basemesh, ecarts)
        mesurer_les_grappes(clothes, basemesh, name)
        rendered = rendered + 1
        continue

    if auto:
        # ⭐⭐⭐ Le dispositif se choisit sur les mesures, pas asset par asset.
        #   evidence    : rien d'ajoute, cadre serre sur ce qui change ;
        #   retopologie : cadrage serre, maillage trace sur corps tres clair ;
        #   forme       : zones en vermillon, cadre colle a leur enveloppe.
        quoi = classer_lasset(clothes, basemesh, ecarts)
        if name in exceptions:
            # ⚠ On journalise le dispositif MESURE en meme temps que celui qui
            # est impose : sans cela une exception masque silencieusement une
            # regle qui se degrade, et l'on ne s'en apercoit qu'au prochain pack.
            print("   dispositif impose : %s (la mesure disait %s)"
                  % (exceptions[name], quoi))
            quoi = exceptions[name]
            imposé = True
        peindre = (quoi == "carte")
        densite = False
        paire_maillage = (quoi == "diptyque") and not zone_seule
        if zone_seule and quoi != "diptyque":
            # ⚠ Le cadrage sur l'ecart n'existe que pour le diptyque ; ailleurs
            # `ecarts` est mis a None et l'option n'aurait aucun effet. On le
            # dit plutot que de la laisser silencieusement inoperante.
            print("   --zone demande, mais le dispositif mesure est %s : "
                  "le cadrage sur l'ecart ne s'applique pas" % quoi)
        couleur_aretes = "sombre"
        # ⚠⚠ UNE SEULE chaine, et c'est une correction du 06-09. La version
        # precedente ouvrait `if quoi == "epure":` pour poser les reglages,
        # puis une SECONDE chaine, `if quoi == "epure" and not <drapeau>:`,
        # suivie de ses `elif`. Une epure a vraies aretes echoue cette seconde
        # condition, donc Python deroulait la chaine jusqu'au `else` destine a
        # la carte, qui remettait `part_haute` a zero et coupait les facettes.
        # Le reglage etait donc pose, puis annule six lignes plus bas, et le
        # journal annoncait « epure » en rendant un corps entier sans facettes.
        # ⭐ La panne ne venait pas des regles mais de leur ENCHAINEMENT, ce qui
        # est exactement ce que la reprise a froid devait attraper. ⭐⭐ Et la
        # regle generale : deux chaines successives sur la MEME variable sont un
        # piege, la seconde rattrapant dans son `else` ce que la premiere avait
        # deja traite. Une variable, une chaine.
        if quoi == "epure":
            # ⚠ L'epure est la SEULE vignette dont le sujet est la topologie :
            # c'est donc la seule ou une fausse triangulation serait un
            # mensonge, les maillages de MakeHuman etant integralement en quads.
            #
            # ⚠ Le zoom sur la partie la plus parlante doit s'imposer AU
            # cadrage sur l'ecart, sinon celui-ci reprend la main et l'on
            # obtient le corps entier. On annule donc l'ecart pour ce cas.
            ecarts = None
            facettes = True
            part_haute = 0.20
            gris = False
            poser_facettes(clothes)
            if vraies_aretes:
                # ⚠⚠ Le fil ne se cree PAS ici. Son epaisseur depend du cadre,
                # qui n'est pas encore choisi : la version precedente calculait
                # une epaisseur en pixels, puis appelait `objet_de_fil` sans la
                # lui passer, donc avec sa valeur par defaut. Le calcul ne
                # servait a rien et personne ne le disait. On note l'intention
                # et l'on cree apres cadrage.
                # ⭐⭐ Corps tres CLAIR, demande de Raphael le 06-09, et la
                # mesure lui donne raison deux fois. D'abord les aretes des
                # quads se distinguent mieux sur un fond clair que sur le gris
                # du studio. Ensuite, et c'est le point que je n'avais pas vu :
                # l'epure etait la seule vignette a PERDRE SA SILHOUETTE sur le
                # fond de theme sombre de Blender, son contour etant fait de
                # traits d'encre. Decile bas du contour a 34 et 48 pour un fond
                # a 48, donc le bord se confondait avec le fond. Un corps clair
                # remonte ce contour.
                poser_gris(clothes, couleur=BLANC_TECHNIQUE)
                fil_a_creer = clothes
                epaisseur_aretes = 0.0
                expo_blanche = True
                print("   dispositif : epure (vraies aretes, corps clair)")
            else:
                epaisseur_aretes = 0.09
                montrer_les_aretes(clothes, 0.09, "sombre", fond=BLANC_TECHNIQUE)
        elif quoi == "portrait":
            # silhouette entiere autre : nu, en entier
            ecarts = None
            epaisseur_aretes = 0.0
            facettes = False
            part_haute = 0.0
            poser_gris(clothes)
        elif quoi == "diptyque":
            epaisseur_aretes = 0.09
            facettes = False
            part_haute = 0.0
        else:
            epaisseur_aretes = 0.09
            facettes = False
            part_haute = 0.0
        if part_haute_cli is not None:
            part_haute = part_haute_cli
            print("   cadrage force par --top : %.2f" % part_haute)
        print("   dispositif : %s" % quoi)

    # ⚠⚠ `comparer` servait a DEUX choses : calculer l'ecart au corps, dont le
    # cadrage a besoin, et declencher les deux rendus base/proxy. En mode auto
    # j'ai active la premiere en heritant de la seconde, et les quinze assets
    # sont sortis en paires. Une variable, deux usages : les separer.



    hide_bodies()

    bpy.context.view_layer.update()
    islands = asset_islands([clothes])
    if not islands:
        print("-- FAILED (the fitted asset has no geometry): " + name)
        failed = failed + 1
        continue

    camera = scene.camera
    if not whole:
        framed = largest_group(islands, camera)
        if len(framed) < len(islands):
            print("   framing %d of the %d separate pieces" % (len(framed), len(islands)))
        islands = framed

    points = [point for island in islands for point in island]
    # ⚠⚠ Garder la trace de l'objet AVANT toute substitution : le bloc de
    # comparaison remplace `points` par la zone d'ecart, si bien qu'un rapport
    # calcule ensuite entre les deux vaut toujours 1. Vu le 06-09, l'etendue
    # sortait a 100 % pour les quinze assets.
    points_objet = list(points)
    # ⚠⚠ `paire_ici` doit etre initialise ICI, avant le bloc de cadrage qui le
    # lit. Il l'etait six lignes APRES, si bien que la condition employait la
    # valeur de l'asset PRECEDENT. C'est la fuite d'etat qui faisait sortir
    # differemment les deux entrees identiques du pack, le doublon
    # `female_generic` : l'une cadree sur la tete, l'autre en pied, selon ce
    # qui les precedait dans la boucle. Trouvee le 06-09 en comparant deux
    # fichiers de meme somme de controle. ⭐ Deux entrees identiques DOIVENT
    # produire deux vignettes identiques : c'est le test de fuite le plus
    # simple et le plus sur.
    paire_ici = paire_maillage
    # ⚠⚠ Un proxy PARTIEL, qui retire de la geometrie plutot que d'en ajouter
    # (une tete seule, un torse, une queue), fait mentir la mesure d'ecart :
    # les sommets qui s'ecartent le plus du corps sont ceux du BORD DE COUPE,
    # la ou le corps a disparu, et non l'objet lui-meme. Cadrer dessus donne un
    # gros plan sur l'arriere d'un crane. Vu le 06-09 sur `head_only` et
    # `snek`. On le detecte a la taille : un proxy qui couvre nettement moins
    # que le corps est partiel, et se cadre sur LUI-MEME.
    if peindre and ecarts:
        # ⚠ En mode peinture le cadre ne doit PAS suivre l'ecart : c'est
        # justement pour situer la zone SUR le corps que la couleur sert.
        print("   peinture : cadrage sur l'objet entier, la couleur situe la zone")
        ecarts = None

    if ecarts:
        (_, taille_proxy) = bounds(points)
        (_, taille_ref) = bounds([p for i in asset_islands(
            [bpy.data.objects[BODY]]) for p in i]) if False else (None, None)
        hauteur_proxy = taille_proxy[2]
        if hauteur_proxy < 0.9:
            print("   proxy partiel (%.2f m de haut) : cadrage sur l'objet, "
                  "non sur l'ecart" % hauteur_proxy)
            ecarts = None

    if ecarts:
        # ⭐ En mode comparaison, le cadre suit l'ecart au corps, non la
        # silhouette : c'est la visee geometrique des curseurs, transposee.
        #
        # ⚠⚠ Et la marge doit etre RELATIVE a l'etendue de cet ecart, non fixe.
        # Une marge large, indispensable quand l'ecart tient dans quelques
        # centimetres (un sexe, une main), reduit le sujet a deux silhouettes
        # minuscules quand l'ecart est deja diffus sur tout le corps. Mesure du
        # 06-09 : a marge 3,5 les huit corps generiques deviennent illisibles
        # alors que la distance entre vignettes MONTE, la mesure recompensant
        # une fois de plus un defaut.
        (_, taille_zone) = bounds(ecarts)
        (_, taille_corps) = bounds(points_objet)
        etendue = max(taille_zone) / max(max(taille_corps), 1e-6)
        # ⚠ Le plafond etait a 4,0, choisi sur un seul cas et pris pour une
        # valeur generale. Verifie le 06-09 sur les deux sexes : a 4 le cadre
        # colle a l'organe et l'on ne comprend pas ce qu'on regarde ; a 5,5 le
        # pubis, la racine et les testicules entrent dans le cadre et
        # l'anatomie se lit ; a 7,5 le sujet redevient petit et une main entre
        # dans le coin.
        # ⚠ Plafond ramene de 5,5 a 3,0 : la croissance de zone rattrape
        # desormais la base de l'organe, donc il n'y a plus besoin d'une marge
        # enorme pour la faire entrer. Deux corrections successives du meme
        # symptome, dont la seconde rend la premiere excessive.
        # ⚠ Plafond ramene de 3,0 a 2,2 le 06-09, sur l'oeil de Raphael : a 3,0
        # le sexe au repos etait « vraiment tres eloigne ». Essais compares a
        # 3,0, 2,2 et 1,7 : a 1,7 il ne reste que de la cuisse et le contexte
        # disparait. ⭐ Le sexe en erection, qu'il jugeait bon, a la MEME marge
        # de 3,0 : ce n'est donc pas le reglage qui etait faux mais l'etendue
        # de la zone, plus large au repos parce que l'ecart y est plus faible
        # et gagne le pubis. Corriger la marge est le remede simple ; corriger
        # la zone demanderait un seuil par asset, ce qui n'en vaut pas le prix.
        marge_auto = min(2.2, max(1.2, 0.55 / max(etendue, 0.02)))
        MARGIN = marge_auto if marge is None else marge
        print("   zone d'ecart : %.0f%% du sujet, marge %.2f"
              % (etendue * 100.0, MARGIN))
        points = ecarts
    elif part_haute and not paire_ici:
        # ⚠ `--top` cadre sur la tete pour une vignette simple, dont le sujet
        # est la densite du maillage. En mode paire le sujet est l'OBJET, donc
        # le recadrage n'a pas lieu d'etre : applique a `head_only`, il ne
        # gardait que la calotte du crane et la vignette montrait deux domes.
        points = garder_le_haut(points, part_haute)
    if cadrer_neufs and not paire_ici:
        # ⚠ Marge relative a l'etendue, comme la carte : une petite zone se
        # replace dans son contexte par une grande marge, une zone etendue
        # par une marge serree. Meme formule, meme plafond.
        _, neufs = peindre_les_nouveaux(clothes, basemesh)
        if len(neufs) >= 8:
            hz = bounds(neufs)[1][2]
            ho = max(bounds(points_objet)[1][2], 1e-6)
            # ⚠ Plafond a 2,2 et non 5,5 : la formule de la CARTE sert a
            # replacer une zone dans son contexte, celle-ci a ZOOMER dessus.
            # A 5,5 l oreille de jujube revenait au buste entier. Et 2,2 est
            # la valeur deja arbitree pour le diptyque le 06-09 : les deux
            # cadrages cherchent la meme chose, voir la zone avec juste ce
            # qu il faut autour.
            MARGIN = (marge if marge is not None
                      else min(2.2, max(1.02, 0.55 / max(hz / ho, 0.02))))
            points = neufs
            print("   cadre sur les sommets neufs : %d, marge %.2f"
                  % (len(neufs), MARGIN))
        else:
            print("   trop peu de sommets neufs (%d), cadrage inchange"
                  % len(neufs))
    elif part_haute_cli is not None and not paire_ici:
        # ⭐ --top donne en ligne de commande : l'explicite prime sur le
        # cadrage calcule sur la zone d'ecart. Sans cela --compare ramene
        # toujours au corps entier et le trait d'arete s'ecrase en moire.
        points = garder_le_haut(points_objet, part_haute_cli)
        print("   cadrage force par --top : %.2f" % part_haute_cli)
    if paire_maillage and ecarts:
        # ⭐⭐ En mode paire, le sujet est l'OBJET, non la difference : c'est la
        # doctrine de Raphael, on montre ce que l'asset apporte. On ne garde le
        # cadrage sur l'ecart que s'il est tres localise, un sexe par exemple,
        # ou le gros plan est justement ce qui parle.
        #
        # ⚠ Et il faut que la TETE reste dans le cadre plutot que les pieds :
        # une silhouette sans tete ne se reconnait pas. Un format debout de
        # 128 x 256 a le meme rapport qu'un corps debout, donc cadrer l'objet
        # entier le remplit bien, contrairement au carre.
        (_, taille_zone) = bounds(ecarts)
        (_, taille_obj) = bounds(points_objet)
        etendue = max(taille_zone) / max(max(taille_obj), 1e-6)
        if etendue < 0.12:
            print("   ecart tres localise (%.0f%%) : gros plan dessus" % (etendue * 100))
            points = ecarts
        else:
            # ⭐⭐⭐ LA SYNTHESE, mesuree le 06-09. Cadrer l'objet entier le rend
            # reconnaissable et fait disparaitre sa topologie : les huit corps
            # generiques redeviennent huit silhouettes. Or un proxy dont l'ecart
            # est DIFFUS est justement defini par sa topologie, sa forme n'etant
            # qu'un corps humain de plus. Pour ceux-la, la paire ne sert a rien
            # et la vignette simple au trait d'encre, cadree sur la tete, dit le
            # vrai sujet.
            #
            # Mesure sur les quinze, distance mediane / paires confondables /
            # lisibilite des facettes :
            #   tout en vignette simple      15,5   22/105   108,9
            #   tout en paire, objet entier  14,3   28/105    97,7
            #   la synthese                  59,6   11/105   108,3
            # Seule la synthese fait monter les DEUX mesures, signature d'un
            # vrai progres.
            # ⚠⚠ La regle des 12 % ne doit PAS defaire un dispositif impose :
            # elle est une heuristique, la consigne est une decision. Sans ce
            # garde-fou `--device nom=diptyque` etait accepte, journalise, puis
            # annule six lignes plus bas, et l'on obtenait une epure en croyant
            # avoir demande un diptyque. Vu le 06-09, et c'est exactement la
            # meme forme de panne que la double chaine `if` de l'epure.
            if imposé:
                print("   ecart diffus (%.0f%%), mais le dispositif est "
                      "impose : on garde la paire" % (etendue * 100))
            else:
                print("   ecart diffus (%.0f%%) : la paire n'apprend rien, "
                      "vignette simple au trait" % (etendue * 100))
                paire_ici = False
            points = points_objet
            if part_haute:
                points = garder_le_haut(points, part_haute)
            # ⚠⚠ Ne remettre la marge a sa valeur de base QUE dans ce cas. La
            # version precedente le faisait sans condition, juste apres avoir
            # calcule 5,50 pour un gros plan : le journal annoncait donc la
            # bonne marge et le cadre restait serre. Onzieme panne muette du
            # chantier, meme famille que les autres, une variable ecrasee
            # apres avoir ete calculee.
            MARGIN = marge if marge is not None else 1.10

    if paire_ici:
        # ⚠⚠ La forme des prises doit etre fixee AVANT le cadrage, non apres :
        # `zoom_instead_of_approaching` agit sur la focale, donc le rejouer
        # multiplie le zoom et pousse le sujet hors champ. Deux assets sur
        # quinze sortaient a 0,03 % de pixels opaques, c'est-a-dire vides,
        # sans aucune erreur affichee. Vu le 06-09.
        sens = sens_de_lobjet(points, camera)
        if coupe_forcee is not None and coupe_forcee != sens:
            # ⚠ La mesure du sens est une heuristique, comme la regle des 12 % :
            # une consigne la surpasse, et le journal dit les deux.
            print("   coupe forcee en %s (la mesure disait %s)"
                  % (coupe_forcee, sens))
            sens = coupe_forcee
        if sens == "horizontal":
            scene.render.resolution_x = max(memo_resolution)
            scene.render.resolution_y = max(memo_resolution) // 2
        else:
            scene.render.resolution_x = max(memo_resolution) // 2
            scene.render.resolution_y = max(memo_resolution)

    if azimut is not None:
        (centre_sujet, _) = bounds(points)
        poser_azimut(camera, centre_sujet, azimut)
        print("   azimut pose a %.0f degres" % azimut)

    if vraies_aretes and fil_a_creer is None:
        # ⚠⚠ Le fil ne se creait que dans la branche automatique : hors de
        # celle-ci, --true-edges etait accepte puis ignore, et le noeud
        # Wireframe de --wire trianguilait les quads sans que rien ne le dise.
        fil_a_creer = clothes
        epaisseur_aretes = 0.0
    if fil_a_creer is not None:
        # ⭐ L'epaisseur du trait se decide ICI, quand on sait enfin quelle
        # portion du sujet va remplir l'image. Le cadre vaut l'etendue des
        # points de cadrage multipliee par la marge ; on veut qu'un trait pese
        # environ un pixel et demi sur le cote long du rendu.
        (_, etendue_cadre) = bounds(points)
        cote = max(etendue_cadre) * MARGIN
        pixels = max(memo_resolution) if memo_resolution else 256
        plancher = 1.5 * cote / max(pixels, 1)
        objet_de_fil(
            fil_a_creer, epaisseur_min=plancher,
            couleur=(GRIS_NEUTRE if (cadrer_neufs and INDICES_NEUFS)
                     else COULEURS_ARETES.get(couleur_aretes,
                                              COULEURS_ARETES["sombre"])),
            marques=(INDICES_NEUFS if cadrer_neufs else None),
            couleur_marquee=(COULEURS_ARETES.get(couleur_aretes,
                                                 COULEURS_ARETES["sombre"])
                             if cadrer_neufs else None))
        print("   cadre %.3f m sur %d px : plancher de trait %.4f m"
              % (cote, pixels, plancher))

    (centre, size) = bounds(points)
    fit_camera(camera, points)
    distance = zoom_instead_of_approaching(camera, centre)
    aim_lights(camera, centre)
    print("   size %.3f x %.3f x %.3f m, camera %.2f m at %.0f mm"
          % (size[0], size[1], size[2], distance, camera.data.lens))

    if peindre:
        # ⭐⭐ Idee de Raphael, precisee le 06-09 : sur un corps ENTIER on ne
        # voit pas quelle zone le proxy modifie. Une couleur de mise en valeur
        # le dit, et le cadre reste sur l'objet entier pour qu'on situe la zone
        # sur le corps.
        if sommets_neufs:
            attribut, zones = peindre_les_nouveaux(clothes, basemesh)
        elif densite:
            attribut, zones = peindre_densite(
                clothes, basemesh, normaliser=densite_normalisee)
        else:
            attribut, zones = peindre_lecart(clothes, basemesh, part_peinte,
                                            plancher=plancher_ecart)
        # ⚠⚠ Une zone PETITE ne se cadre pas serree : il faut le corps autour
        # pour comprendre. Sur `snek`, la zone peinte est le bout de la queue,
        # et cadree seule elle ne donne « une espece de jambe en pointe
        # bizarre » dont Raphael dit ne pas savoir ce que c'est. Alors qu'une
        # zone ETENDUE, une musculature par exemple, se lit tres bien serree,
        # tete hors champ, et c'est meme sa meilleure version.
        # Critere : la hauteur de l'enveloppe rapportee a celle de l'objet.
        # ⭐ Decide le 13-09 : on S'APPROCHE d'une petite zone au lieu de
        # reculer, et c'est la MARGE qui remet le contexte, relative a
        # l'etendue comme pour le diptyque. La regle precedente, « sous 40 %
        # de hauteur on cadre l'objet entier », venait de la carte d'ecart de
        # forme, ou une petite zone etait un artefact du percentile ; avec les
        # sommets neufs elle est un fait, et reculer la rendait invisible.
        marge_zone = 1.02
        if zones:
            hz = bounds(zones)[1][2]
            ho = max(bounds(points_objet)[1][2], 1e-6)
            etendue_z = hz / ho
            marge_zone = min(5.5, max(1.02, 0.55 / max(etendue_z, 0.02)))
            print("   enveloppe de %.0f%% de la hauteur du sujet, marge %.2f"
                  % (100.0 * etendue_z, marge_zone))
        if paquet_de_zones is not None and zones:
            # ⭐ On coupe les grappes en deux paquets au PLUS GRAND TROU de
            # hauteur, puis on cadre sur celui demande. La coupure se lit
            # dans l'asset, elle n'est pas decretee.
            grappes_ici = grappes_des_neufs(clothes, INDICES_NEUFS)
            mp_ici = clothes.matrix_world
            centres = []
            for membres in grappes_ici:
                pts = [mp_ici @ clothes.data.vertices[i].co for i in membres]
                centres.append((sum(p[2] for p in pts) / len(pts), pts))
            centres.sort(key=lambda c: c[0])
            if len(centres) >= 2:
                trous = [(centres[k + 1][0] - centres[k][0], k)
                         for k in range(len(centres) - 1)]
                _, coupure = max(trous)
                bas = [p for _, pts in centres[:coupure + 1] for p in pts]
                haut = [p for _, pts in centres[coupure + 1:] for p in pts]
            else:
                bas = haut = [p for _, pts in centres for p in pts]
            choisi = haut if paquet_de_zones == "haut" else bas
            (_, taille_choisie) = bounds(choisi)
            (_, taille_obj) = bounds(points_objet)
            etendue_c = max(taille_choisie) / max(max(taille_obj), 1e-6)
            MARGIN = (marge if marge is not None
                      else min(4.0, max(1.2, 0.35 / max(etendue_c, 0.01))))
            fit_camera(camera, choisi)
            centre_c = bounds(choisi)[0]
            zoom_instead_of_approaching(camera, centre_c)
            aim_lights(camera, centre_c)
            print("   cadre sur le paquet %s : %d sommets, etendue %.1f%%, "
                  "marge %.2f" % (paquet_de_zones, len(choisi),
                                  100.0 * etendue_c, MARGIN))
        elif zone_a_la_couronne is not None and zones:
            # ⭐⭐⭐ Cadrage sur mesure, carre INCHANGE, meme azimut : la
            # camera se rapproche jusqu'a ce que le sommet du crane touche
            # le bord haut et le bas de la zone (moins la marge) touche le
            # bord bas. Les mains n'entrent JAMAIS dans ce calcul.
            tous_les_sommets = [clothes.matrix_world @ s2.co
                                for s2 in clothes.data.vertices]
            z_bas = min(p[2] for p in zones) - zone_a_la_couronne
            z_haut = max(p[2] for p in tous_les_sommets)
            # L'AXE VERTICAL CENTRAL du corps : x,y du sommet du crane (region
            # fiable, toujours sur l'axe du corps, jamais deportee par la
            # pose des bras). Deux points seulement, memes x,y, z differents :
            # leur terme de LARGEUR est nul, seule la HAUTEUR compte.
            bande_crane = [p for p in tous_les_sommets if p[2] >= z_haut - 0.03]
            if not bande_crane:
                bande_crane = tous_les_sommets
            cx = sum(p[0] for p in bande_crane) / len(bande_crane)
            cy = sum(p[1] for p in bande_crane) / len(bande_crane)
            from mathutils import Vector as _V
            point_haut = _V((cx, cy, z_haut))
            point_bas = _V((cx, cy, z_bas))
            MARGIN = marge if marge is not None else 1.02
            fit_camera(camera, [point_haut, point_bas])
            centre_z = bounds([point_haut, point_bas])[0]
            zoom_instead_of_approaching(camera, centre_z)
            aim_lights(camera, centre_z)
            print("   cadre vertical serre, marge %.3f m, du sommet du "
                  "crane au bas de la zone (mains ignorees)" % zone_a_la_couronne)
        elif len(zones) >= 8:
            # ⚠ Une marge de 35 % remettait la tete dans le champ : les zones
            # peintes s'etendent souvent des epaules aux mollets, donc leur
            # enveloppe fait deja presque tout le corps et il ne reste rien a
            # rogner. Le cadre doit **coller** aux zones.
            MARGIN = marge if marge is not None else marge_zone
            fit_camera(camera, zones)
            centre_z = bounds(zones)[0]
            zoom_instead_of_approaching(camera, centre_z)
            aim_lights(camera, centre_z)
            print("   cadre sur l'enveloppe des zones : %d sommets" % len(zones))
        materiau_deux_zones(clothes, attribut, epaisseur_aretes or 0.09,
                            couleur_aretes,
                            COULEURS_ARETES.get(valeur_relief))
        sous = clothes.modifiers.new("arrondi", "SUBSURF")
        sous.levels = 1
        sous.render_levels = 1
        scene.render.filepath = destination
        # ⚠ Une couleur de mise en valeur ne survit pas a l'exposition qui
        # rend le corps porcelaine : a +0,7 l'orange sort jaune pale, la
        # courbe de rendu comprimant les hautes lumieres. La carte se rend
        # donc a sa propre exposition, 0 par defaut.
        memo_expo_carte = scene.view_settings.exposure
        scene.view_settings.exposure = expo_carte
        bpy.ops.render.render(write_still=True)
        scene.view_settings.exposure = memo_expo_carte
        print("-- RENDER: " + destination + " (zone peinte, exposition %.2f)"
              % expo_carte)
        rendered = rendered + 1

        if polyptyque and sommets_neufs:
            # ⭐⭐⭐ Demande de Raphael, 13-09 : sur un proxy dont les zones
            # sont ELOIGNEES (la sirene, jujube_proxy_with_helpers_test), une
            # seule image ne peut pas etre a la fois large (montrer que
            # c'est un corps) et serree (montrer chaque zone). L'overview
            # garde le corps entier ; une cellule par grappe zoome dessus.
            grappes = grappes_des_neufs(clothes, INDICES_NEUFS)
            if len(grappes) >= 2:
                base_destination = destination[:-4]
                # -- overview : toutes les zones peintes, cadre sur l'OBJET
                # ⚠⚠ PAS sur points_objet : celui-ci ne garde que le plus
                # gros ilot connexe (largest_group), ce qui coupe les mains et
                # les pieds d'un proxy en plusieurs morceaux comme punkduck.
                tous_les_sommets_du_proxy = [
                    clothes.matrix_world @ s.co for s in clothes.data.vertices]
                peindre_indices(clothes, INDICES_NEUFS)
                fit_camera(camera, tous_les_sommets_du_proxy)
                centre_o = bounds(tous_les_sommets_du_proxy)[0]
                zoom_instead_of_approaching(camera, centre_o)
                aim_lights(camera, centre_o)
                scene.render.filepath = base_destination + "-overview.png"
                scene.view_settings.exposure = expo_carte
                bpy.ops.render.render(write_still=True)
                scene.view_settings.exposure = memo_expo_carte
                print("-- RENDER: " + base_destination + "-overview.png"
                      " (polyptyque, %d grappes)" % len(grappes))
                # -- une cellule par grappe, zoomee, meme couleur
                for i, grappe in enumerate(grappes):
                    peindre_indices(clothes, grappe)
                    positions = [clothes.matrix_world @ clothes.data.vertices[idx].co
                                 for idx in grappe]
                    hz = bounds(positions)[1][2]
                    ho = max(bounds(tous_les_sommets_du_proxy)[1][2], 1e-6)
                    marge_cellule = min(2.2, max(1.02, 0.55 / max(hz / ho, 0.02)))
                    ancienne_marge = MARGIN
                    MARGIN = marge_cellule
                    fit_camera(camera, positions)
                    centre_c = bounds(positions)[0]
                    zoom_instead_of_approaching(camera, centre_c)
                    aim_lights(camera, centre_c)
                    MARGIN = ancienne_marge
                    scene.render.filepath = (base_destination
                                              + "-cell%d.png" % (i + 1))
                    scene.view_settings.exposure = expo_carte
                    bpy.ops.render.render(write_still=True)
                    scene.view_settings.exposure = memo_expo_carte
                    print("-- RENDER: " + base_destination + "-cell%d.png"
                          " (%d sommets, marge %.2f)"
                          % (i + 1, len(grappe), marge_cellule))
                # remettre l'attribut complet, au cas ou un mode suivant le lirait
                peindre_indices(clothes, INDICES_NEUFS)
            else:
                print("   polyptyque : une seule grappe notable, "
                      "l'image simple suffit")
        continue

    if paire_maillage and not paire_ici:
        # ⚠ Cet asset retombe sur la vignette simple : il faut lui appliquer le
        # traitement que `load_asset` avait saute en mode paire, sinon il sort
        # lisse et sans aretes, donc sans son sujet.
        if facettes:
            poser_facettes(clothes)
        if epaisseur_aretes:
            montrer_les_aretes(clothes, epaisseur_aretes, couleur_aretes)
        scene.render.filepath = destination
        bpy.ops.render.render(write_still=True)
        print("-- RENDER: " + destination + " (vignette simple)")
        rendered = rendered + 1
        continue

    if paire_ici:
        # ⭐⭐ Doctrine arretee par Raphael le 06-09. Quand la difference saute
        # aux yeux (un sexe ajoute, un squelette, une tete seule), le corps de
        # base **ne sert a rien** : il faut l'objet, bien cadre et centre, ni
        # trop pres ni trop loin. L'interet d'une seconde image est alors
        # ailleurs : une version SANS maillage et une AVEC, qui dit de quoi
        # l'objet est fait sans cesser de le montrer.
        # ⭐⭐ A GAUCHE : ce que l'asset rend, lisse et subdivise, avec sa
        # propre matiere et le lisere du studio. A DROITE : de quoi il est
        # fait, facettes a plat et aretes tracees. Demande de Raphael le
        # 06-09 : la moitie gauche doit montrer les rondeurs et la peau, sinon
        # elle n'apprend rien de plus que la droite.
        sous = clothes.modifiers.new("arrondi", "SUBSURF")
        sous.levels = 1
        sous.render_levels = 1
        sans = destination[:-4] + "-lisse.png"
        scene.render.filepath = sans
        bpy.ops.render.render(write_still=True)

        clothes.modifiers.remove(sous)
        poser_facettes(clothes)
        avec = destination[:-4] + "-maille.png"
        # ⚠⚠ Les VRAIES aretes ici aussi, et pas seulement dans l'epure. Le
        # noeud Wireframe trace la geometrie **triangulee par le moteur**,
        # l'objet de fil les aretes reelles : les faire cohabiter dans un meme
        # catalogue ferait affirmer DEUX topologies differentes pour un seul et
        # meme maillage, selon l'effet qui lui a ete attribue. Porte le 06-09.
        #
        # ⭐ Benefice second, mesure sur la case 8 de la planche : l'objet de
        # fil porte le plancher d'epaisseur relatif au cadre, que le noeud
        # n'avait pas. La moitie maillee d'un sexe au repos, dont le trait
        # etait bien plus faible que celle d'une tete seule, se lit desormais.
        fil_du_diptyque = None
        if epaisseur_aretes:
            if vraies_aretes:
                poser_gris(clothes, couleur=BLANC_TECHNIQUE)
                (_, etendue_dip) = bounds(points)
                cote_dip = max(etendue_dip) * MARGIN
                pixels_dip = max(memo_resolution) if memo_resolution else 256
                fil_du_diptyque = objet_de_fil(
                    clothes, epaisseur_min=1.5 * cote_dip / max(pixels_dip, 1))
            else:
                montrer_les_aretes(clothes, epaisseur_aretes, couleur_aretes,
                                   fond=BLANC_TECHNIQUE)
        # ⚠⚠ Un albedo plus clair ne suffit pas : la courbe de rendu comprime
        # les hautes lumieres, si bien que passer de 0,62 a 0,92, soit 48 % de
        # plus, ne donne que 8 % a l'image. Mesure du 06-09 : 10 points
        # d'ecart, et meme -0,3 sur un des trois assets. Le blanc technique
        # s'obtient donc a l'EXPOSITION, pas a la matiere.
        memo_expo = scene.view_settings.exposure
        scene.view_settings.exposure = memo_expo + ECART_BLANC
        scene.render.filepath = avec
        bpy.ops.render.render(write_still=True)
        scene.view_settings.exposure = memo_expo
        # ⚠ Retirer le fil MAINTENANT : un objet laisse dans la scene se
        # retrouverait dans la vignette de l'asset suivant, ce qui est
        # exactement la famille de fuite d'etat qui a coute le plus cher ici.
        if fil_du_diptyque is not None:
            donnees = fil_du_diptyque.data
            bpy.data.objects.remove(fil_du_diptyque, do_unlink=True)
            bpy.data.meshes.remove(donnees)
        mesure = le_maillage_apprend_il(sans, avec)
        print("-- PAIRE: %s, coupe %s, le maillage change %s"
              % (name, sens,
                 "%.1f/255 sur %.0f%% des pixels" % mesure if mesure
                 else "une part inconnue"))
        rendered = rendered + 1
        continue

    if comparer:
        # ⚠ Deux prises au MEME cadre : le proxy, puis le corps de base seul.
        # L'utilisateur ne connait pas le corps de reference par coeur, donc
        # une vignette qui ne montre que la zone modifiee ne lui apprend rien
        # s'il n'a pas de quoi comparer.
        base = destination[:-4] + "-proxy.png"
        scene.render.filepath = base
        bpy.ops.render.render(write_still=True)
        print("-- RENDER: " + base)
        clothes.hide_render = True
        corps = bpy.data.objects[BODY]
        corps.hide_render = False
        bpy.data.collections[BODY].hide_render = False
        # ⚠ Le corps de base porte ses propres modificateurs, dont une
        # subdivision : sans les couper il reste lisse quand le proxy est a
        # facettes, et la comparaison oppose deux traitements au lieu de deux
        # maillages.
        for mod in list(corps.modifiers):
            if mod.type in ("SUBSURF", "MULTIRES"):
                corps.modifiers.remove(mod)
        if facettes:
            poser_facettes(corps)
        if epaisseur_aretes:
            montrer_les_aretes(corps, epaisseur_aretes, couleur_aretes)
        scene.render.filepath = destination[:-4] + "-base.png"
        bpy.ops.render.render(write_still=True)
        print("-- RENDER: " + destination[:-4] + "-base.png")
        rendered = rendered + 1
        continue

    scene.render.filepath = destination
    start = time.time()
    # ⚠ Le blanc technique ne s'obtient PAS a la matiere seule : la courbe de
    # rendu comprime les hautes lumieres, si bien qu'un albedo de 0,92 au lieu
    # de 0,62, soit 48 % de plus, ne donne que 8 % a l'image. Il faut de
    # l'exposition, comme pour la moitie maillee du diptyque.
    memo_expo_generale = scene.view_settings.exposure
    if expo_blanche:
        scene.view_settings.exposure = memo_expo_generale + ECART_BLANC
    bpy.ops.render.render(write_still=True)
    scene.view_settings.exposure = memo_expo_generale
    print("-- RENDER: " + destination + " (%.0fs)" % (time.time() - start))
    rendered = rendered + 1

print("Rendered " + str(rendered) + " thumbnails, skipped " + str(skipped) + ", failed " + str(failed))
