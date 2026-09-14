# Spécification des vignettes MakeHuman / MPFB2

*Table de décision, arrêtée le 12-09-2026, mise à jour le 13-09-2026. Elle
remplace le tâtonnement : pour tout besoin de vignette, elle donne le
dispositif, l'éclairage, le cadrage et l'azimut sans interprétation.*

⚠⚠ **Pour les PROXIES (maillages de corps de remplacement), le §2.7 et le
CANON section 1.23 priment sur ce qui les contredit dans les sections
suivantes.** Le 13-09-2026 a tranché le décor (fond noir, corps porcelaine),
la couleur (encre bleue plutôt qu'orange), le sens de l'azimut, et remplacé le
classificateur à sept règles du §6.2 par un classement à trois régimes mesuré
sur trois nombres. `rendermeshthumbs.py` est désormais versionné dans ce
dépôt (§8, §9.1 résolu). Ce qui suit sur les **cibles** (curseurs) n'a pas
changé.

Ce document **ne rejoue pas** les mesures. Chaque choix renvoie à la section du
CANON (`~/dev/admin/makehuman-vignettes-CANON.md`) qui le paie d'un chiffre.
Le vocabulaire court reste dans `bin/vignettes-vocabulaire.md` (fr) et
`bin/thumbnail-vocabulary.md` (en) ; ici c'est la **spécification**, c'est-à-dire
ce qui s'applique, ce qui ne s'applique pas, et dans quel ordre on décide.

## 0. Comment lire

Une vignette se spécifie en quatre champs, et **jamais moins** :

| champ | ce qu'il dit | où le trouver |
|---|---|---|
| **dispositif** (effet) | ce qu'on ajoute à l'image | §2, choisi par la règle du §6 |
| **vue** (cadrage) | d'où l'on regarde, jusqu'où l'on cadre | §5 |
| **éclairage** | quel préréglage nommé | §3, imposé par l'azimut et la famille |
| **matière** | gris du studio, grain fin, blanc technique | §4 |

Se dit en trois mots : « la silhouette au liseré, en coupe » ; « l'écart, en
diptyque » ; « la tête, en épure ».

⭐ **Principe qui gouverne toute la table** (CANON 1.11, énoncé après cinq
occurrences) : aucun réglage n'est absolu, chacun est **relatif à ce qu'il
décrit**. L'éclairage suit l'angle de vue, le grain de peau suit l'échelle du
cadre, l'épaisseur du trait suit la densité du maillage, la marge de cadrage
suit l'étendue de l'écart. Avant de recopier une valeur d'une ligne à l'autre,
demander **à quoi elle sert ici**, pas seulement d'où elle vient.

---

## 1. Deux familles, deux moteurs

| famille | sujet | moteur | ce qu'on montre |
|---|---|---|---|
| **cibles** (curseurs MPFB) | une déformation continue | `bin/rendertargetthumbs.py` | les deux bouts du curseur |
| **assets** (proxies, maillages) | un maillage de rechange | `rendermeshthumbs.py`, versionné dans `bin/` depuis le 13-09 | la topologie ou l'écart au corps |

⚠ Les deux familles sortent du **même studio** depuis le 06-09 : même gris, même
liseré, même fond transparent, même taille. L'écart de teinte entre vignettes est
tombé de 89,0 à 49,4 et l'exposition du sujet de 172,6 à 122,3, soit la bande des
cibles qui tournent à 135 (CANON 1.12). L'homogénéité du catalogue ne se plaide
plus, elle se chiffre. ⚠ Ce constat vaut pour les **cibles**, sur fond
transparent ; les **proxies** ont depuis basculé sur un fond et un corps
différents, §2.7.

⚠⚠ **Le fond est transparent et le thème de l'usager est inconnu**, vrai pour
les **cibles**. Les 41 vignettes réelles du catalogue sont transparentes sans
exception, et Blender livre deux thèmes (panneau sombre à 48/255, panneau clair
de `#999999` à `#dbdbdb`). Toute vignette de cible se juge donc sur **les deux
fonds**, jamais aplatie sur blanc. Aucune valeur de corps ne survit aux deux :
question ouverte pour les cibles, laissée au propriétaire du pack (CANON 1.17,
1.18). ⛔ **Pour les proxies, la question est tranchée le 13-09** : fond **noir
opaque**, qui supprime le problème par construction. Voir §2.7 et CANON 1.23.

⚠⚠ **Le sens de l'azimut est inversé entre les deux scripts.** Sur
`rendertargetthumbs.py` (cibles), un azimut **négatif** fait regarder à
gauche. Sur `rendermeshthumbs.py` (assets), c'est l'inverse : un azimut
**positif** fait regarder à gauche, vérifié à l'œil sur six valeurs le 13-09.
Ne jamais recopier une valeur d'azimut d'un script à l'autre sans revérifier
le sens sur l'image (CANON 1.23, §5.4).

---

## 2. Les dispositifs

Six dispositifs. Pour chacun : le besoin auquel il répond, ce qui s'y règle, et
ce qui **n'a pas de sens** pour lui. Cette dernière colonne est la moitié utile
de la table : la plupart des pannes du chantier viennent d'une option juste dans
un dispositif et fausse dans l'autre, sans que rien ne le signale (CANON 1.11,
le piège `--top` en mode paire).

### 2.1 La coupe (*split*), cibles

Les deux bouts d'un curseur côte à côte, séparés d'un trait pointillé. Chaque
moitié est un **demi-format**, l'assemblage un carré.

- **Besoin** : un changement qui **ne déplace pas** le contour (déplacement
  mesuré sous ~5 %).
- **S'applique** : azimut, vue, éclairage, matière, `--amounts`, sens de coupe
  (horizontal / vertical), `--lift`, `--one-side` / `--on-axis`.
- **Sans objet** : trait d'encre, subdivision, zone peinte (ce sont des affaires
  de maillage).
- **Contrainte de forme** : format de prise et axe de coupe sont
  **complémentaires**, sinon le résultat n'est pas carré. Coupe horizontale →
  prises couchées 256×128 (`--rect`) ; coupe verticale → prises debout 128×256
  (`--portrait`). Deux prises **carrées** font un rectangle 512×256, pas une
  icône (CANON 1.9).
- Outil : `bin/composesplit.py --axis {horizontal,vertical} [--stack] [--no-arrow]`.

### 2.2 Le double trait (*two lines*), cibles

L'état **médian** rendu en dur, et les deux bouts tracés par-dessus en courbes
pointillées, jaune `#F0E442` et bleu ciel `#56B4E9`, 3 px. Une seule image.

- **Besoin** : un changement qui **déplace** le contour (au-dessus de ~5 %).
  En dessous, les deux courbes se superposent et ne disent rien.
- **S'applique** : azimut, vue, éclairage, matière, couleur et épaisseur du trait.
- **Sans objet** : sens de coupe, demi-format (c'est une image unique).
- ⚠ **Le sujet doit tenir la silhouette.** Bras en pose de repos, c'est le bras
  qui tient le contour et le tracé suit un fragment près de l'aisselle : 2,35 %
  contre 7,0 % bras tendus (CANON 1.2). D'où `--arms-down 0` pour ce dispositif.
- ⚠ Les deux couleurs viennent d'Okabe-Ito. Rose/cyan est plus lisible à l'œil et
  **inutilisable** : simulée en deutéranopie, sa distance tombe de 215 à 55. Une
  couleur se simule, elle ne se choisit pas à l'œil (CANON 1.2, §2 « écarté »).
- Outil : `bin/drawoutline.py --curve … --width 3`, ou `bin/outlineoverlay.py`.

### 2.3 Le diptyque, assets

Deux moitiés du **même** objet : à gauche le rendu (gris du studio, liseré), à
droite le maillage (trait d'encre sur blanc technique, exposition +0,9 diaphragme).
Ce que l'asset rend, et de quoi il est fait.

- **Besoin** : un asset dont l'ajout est **local** (un sexe), ou un proxy
  **partiel** (une tête seule). La différence saute aux yeux : le corps de base
  ne sert à rien, on montre l'objet (CANON 1.10, arbitrage de Raphaël).
- **S'applique** : cadrage sur **l'écart** (§5.3), marge relative, sens de coupe
  mesuré, éclairage, blanc technique, trait d'encre.
- **Sans objet** : `--top` (CANON 1.11 : sur `head_only` il ne gardait que la
  calotte et la vignette montrait deux dômes) ; le liseré sur le **résultat**
  (il s'applique aux **moitiés**, avant assemblage, sinon la règle de séparation
  ajoute du périmètre et fait basculer le test de filigrane, CANON 1.17).
- ⚠ **Le sens de la coupe se mesure, il ne se choisit pas** : on projette la zone
  qui compte sur les axes de la caméra et on compare ses deux étendues. Zone plus
  large que haute → coupe horizontale et prises couchées ; plus haute que large →
  coupe verticale et prises debout. Vérifié : un sexe en érection sort couché, au
  repos debout (CANON 1.10).
- ⚠ **Marge 2,2**, descendue de 3,0. Et ce n'était pas le réglage qui était faux
  mais l'étendue de la zone, plus large au repos. À 1,7 il ne reste que de la
  cuisse (CANON 1.17).
- ⚠⚠ **Le blanc technique ne s'obtient pas par la matière.** Albédo 0,62 → 0,92,
  soit +48 %, ne donne que 8 % à l'image : la courbe de rendu comprime les hautes
  lumières. Il faut monter l'**exposition** de la seule prise de maillage, +0,9
  diaphragme, et la remettre aussitôt. L'écart entre moitiés passe de 10,0/−0,3/5,4
  à 39,6/29,0/34,8 (CANON 1.12).
- ⚠⚠ **Les vraies arêtes**, comme l'épure, jamais le nœud Wireframe seul : celui-ci
  trace la géométrie **triangulée par le moteur**, et le catalogue affirmerait deux
  topologies différentes pour un même maillage selon l'effet retenu (CANON 1.17).
- Outil : `bin/composediptyque.py <render> <mesh> <out>`.

### 2.4 L'épure (*blueprint*), assets

Une seule image : le maillage tracé sur un corps **très clair**, facettes à plat,
subdivision coupée. Un plan technique.

- **Besoin** : une **retopologie**, low poly ou à densité égale. C'est ce que cet
  asset vend : sa topologie, pas sa forme.
- **S'applique** : `--top` (cadrage sur la tête), épaisseur et couleur du trait,
  azimut, éclairage.
- **Sans objet** : zone peinte, marge relative à l'écart, sens de coupe.
- ⚠⚠ `--subdiv 0` **obligatoire** : la subdivision est active par défaut et efface
  le sujet même de la vignette. Et `--flat`, sans quoi un corps à 412 faces est
  aussi rond qu'un corps à 14 000 (CANON 1.8).
- ⚠ **Trait d'encre**, `--wire-colour sombre` : 15,3 de distance médiane contre
  11,8 pour le bleu et 10,8 pour le blanc. Les couleurs vives se logent dans les
  creux, yeux et narines, et maquillent le visage ; le blanc disparaît sur un
  corps clair (CANON 1.8).
- ⚠ **Épaisseur = fraction de l'arête moyenne**, `--wire 0.09`, jamais une valeur
  fixe. Et c'est nécessaire sans être suffisant : elle est relative au **cadre**
  autant qu'à l'arête, plancher d'un pixel et demi du côté long, plafond de 30 %
  de l'arête. Conséquence d'ordre : **l'épaisseur ne se décide qu'après le
  cadrage** (CANON 1.16).
- ⚠⚠ **Corps très clair, pas gris du studio**, et pour deux raisons distinctes :
  les arêtes des quads se lisent mieux sur un fond clair, et l'épure était la
  seule vignette à **perdre sa silhouette** sur thème sombre, son contour étant
  fait de traits d'encre (décile bas à 34 et 48 pour un fond à 48 ; le corps clair
  porte la moyenne du contour de 92 à 127) (CANON 1.17).
- ⚠ **Couper l'épure en deux** (moitié lisse à gauche) : **oui** pour un maillage
  de jeu (densité > 1,5), **non** pour une retopologie à densité ≈ 1, où la moitié
  lisse devient un corps générique et les retopologies s'effondrent les unes sur
  les autres, 2 → 6 paires confondables sur 21 (CANON 1.22). Et la moitié lisse
  n'informe que si son sujet se **reconnaît** : cadrée sur la tête, un 412 faces
  ne donne qu'un œuf gris (CANON 1.19).

### 2.5 La carte (*map*), assets

Une seule image : corps gris et lisse, zones qui s'écartent du corps de base
peintes en **orange**, partiellement **émissives**. Dit **où** l'asset modifie
quelque chose.

- **Besoin** : un changement de forme **sans retopologie**, où le titre seul
  (« female muscular ») laisse deviner quelles parties changent.
- **S'applique** : cadrage sur **l'enveloppe** des zones peintes (§5.3), teinte et
  part d'émission, éclairage, azimut.
- **Sans objet** : le trait d'encre comme sujet, la subdivision coupée (le lissage
  est une propriété de **face** : on ne peut pas mélanger lisse et facettes par
  sommet, donc l'objet reste lisse et subdivisé partout, CANON 1.13) ; la marge de
  contexte au sens habituel (voir ci-dessous).
- ⚠⚠ **Émission 0,55.** En couleur purement diffuse, la teinte est divisée par
  l'éclairage : un vermillon à 0,84 ressort vers 0,42, brun et terne. Pas plus de
  0,55 : à 1,0 la zone devient un aplat et le modelé disparaît dessous (CANON 1.17).
- ⚠ **Orange**, à l'œil et à la mesure qui s'accordent : dispersion chromatique b*
  de 9,65 contre 8,43 au vermillon et 4,46 à l'ancienne version diffuse. Le jaune
  paraît le plus vif et ne mesure que 5,39, car sur un corps clair il rejoint le
  ton de la peau et la frontière de zone se perd (CANON 1.17).
- ⚠ **Marge 1,02**, collée à l'enveloppe. **Ailleurs la marge replace le sujet dans
  son contexte ; ici le contexte est précisément ce qu'on veut exclure.** Même
  nombre, deux fonctions opposées (CANON 1.13).
- ⚠ **Ne pas normaliser sur le maximum** : un sommet aberrant ailleurs sur le corps
  écrase l'échelle. Rampe calée sur un **percentile**, le dixième le plus écarté
  (CANON 1.13).
- ⚠ **Ne pas écrêter la carte**, contrairement à la zone du diptyque : une
  musculature change épaules, bras et cuisses à la fois, donc plusieurs foyers
  légitimes. Son cadre se calcule à part, sur l'enveloppe (CANON 1.16).
- ⚠ **Elle informe mais ne distingue pas.** Deux proxies qui ne diffèrent que par
  un motif de taches réparties restent à 1,1 de distance à 120 px, contre 15 à 30
  ailleurs. Limite de résolution, pas de conception (CANON 1.13).

### 2.6 Le portrait, assets

Une seule image, rien d'ajouté.

- **Besoin** : ce qui se reconnaît seul, quand **toute la silhouette est autre** :
  un squelette, une queue de sirène. Un aplat de couleur y serait du bruit.
- **S'applique** : cadrage sur **l'entier**, azimut, éclairage, matière.
- **Sans objet** : trait d'encre, zone peinte, diptyque, `--top`.
- ⚠ **Pas de liseré sur un filigrane.** Le liseré empâte une silhouette dont les
  côtes et les doigts sont plus fins que l'anneau. Test : périmètre sur racine de
  la surface (`bin/filigrane.py` dans le CANON), squelette 23,1, corps en pied
  10,4, sirène 8,2, épures 3,3, diptyque 2,7 ; **seuil à 6,0**, au-dessus duquel on
  n'applique pas le liseré (CANON 1.17).

### 2.7 ⭐⭐⭐ Le régime unifié des proxies, arrêté le 13-09-2026

*Ceci remplace, pour les **proxies** (maillages de corps de remplacement), le
choix de dispositif du §6.2/6.3 et le décor décrit aux sections 2.3 à 2.6.
Détail complet, mesures et planches : CANON section 1.23,
`makehuman-planches-2026-09-13/`. Le diptyque (2.3) et le portrait (2.6)
restent le vocabulaire pour ce que ce classement ne couvre pas (un accessoire
isolé, une pièce hors mesh de corps) : ils ne sont pas retirés, seulement
non pilotés par la règle ci-dessous.*

**Le décor commun**, recette exécutable `bin/proxies-v2.sh` :

| réglage | valeur | pourquoi |
|---|---|---|
| fond | **noir opaque** | supprime le risque de contraste inversé selon le thème (§1) |
| corps | `--albedo 0.92`, dit « porcelaine » | 216/255, zéro pixel brûlé |
| exposition | `--exposure 0.7` | corps et écart de lisibilité montent ensemble |
| éclairage | **la face**, monde 0,55 | bat le liseré sur fond noir, corps 198 contre 158 |
| azimut | **+34°** | symétrique du −34° figé de l'ancien studio, sens vérifié à l'œil |
| trait | `--true-edges` (vraies arêtes) | ⚠⚠ sans lui `--wire` retombe sur le nœud Wireframe, qui **triangule les quads** |
| couleur | **encre bleue** `(0.04, 0.12, 0.50)` | une seule couleur pour tout ce qui parle du maillage ; passe les trois daltonismes, contrairement à l'orange (CANON 1.23) |

**Le classement**, par `bin/proxies-v2.sh <pack> mesurer` (option
`--measure-only`, qui imprime pour chaque asset `neufs` / `grappes` /
`étendue`) :

| régime | critère | dispositif | mode du script |
|---|---|---|---|
| **global** | neufs > 90 % du maillage | épure, tout le maillage en bleu, `--top 0.20` | `global` |
| **local** | étendue des sommets neufs < 35 % de la hauteur | épure **bicolore** : gris clair 0,85 partout, bleu sur la seule zone, zoom | `local` |
| **dispersé** | ni l'un ni l'autre | carte : la zone en aplat du même bleu, cadre sur son enveloppe | `disperse` |

⚠ **Un proxy partiel passe avant ce classement.** Un proxy qui **retire** de
la géométrie (une tête seule, un torse) fait ressortir son **bord de coupe**
comme « neuf », pas son propos : à traiter par exception avant de lire le
régime (CANON 1.10, 1.23).

⚠⚠ « neufs » désigne les sommets du proxy qui ne coïncident avec **aucun**
sommet du maillage de base (au dixième d'arête près) : c'est une définition
**topologique**, pas géométrique. Deux définitions géométriques ont été
essayées pour la même question et ont échoué (densité rapportée à la base,
écart de forme par percentile) : voir CANON 1.23, tableau « ce qui a échoué ».

**Correspondance avec le vocabulaire des sections précédentes** : le régime
*global* est une épure (2.4) avec ce nouveau décor ; le régime *dispersé* est
une carte (2.5) avec ce nouveau décor et cette nouvelle définition de zone ;
le régime *local* est un dispositif **nouveau**, une épure zoomée et
bicolore, sans équivalent antérieur dans ce document.

Appliqué aux 29 proxies des deux paquets CC0/CC-BY : **4 globaux, 11 locaux,
13 dispersés**.

### 2.8 Le diptyque empilé, l'exception des deux foyers éloignés

*Arrêté le 13-09-2026 sur `jujube_proxy_with_helpers_test`, seul cas du
catalogue à ce jour. CANON 1.23.*

**Besoin** : un asset qui modifie **deux foyers loin l'un de l'autre**, ici une
anatomie ajoutée au bassin (hauteur 0,45 à 0,50) et le visage (la bouche à
0,89, les quatre paupières à 0,94). Aucune image unique ne les sert : cadrée
large, les paupières sont illisibles ; cadrée serré, il faut choisir un foyer.

**Forme** : deux prises en **demi-format couché** (256 × 128, `--shape couche`)
empilées en un carré, le visage en haut, l'anatomie en bas, séparées d'un trait
blanc d'un pixel. Outil : `bin/composer-diptyque-empile.py`.

| réglage | valeur | pourquoi |
|---|---|---|
| marge du haut | 1,8 | le visage entier reste reconnaissable |
| marge du bas | 1,3 | la trame du maillage de l'ajout se lit |
| corps | **masculin** (`--base-force male`) | le seul des trois où l'ajout ne paraît pas rapporté. ⚠ Le neutre reste la règle pour les 28 autres proxies |
| trait | **non forcé** | le défaut, comme partout ailleurs |

⭐⭐ **La coupure entre les deux paquets se lit, elle ne se décrète pas.**
`--frame-zone haut|bas` trie les grappes par hauteur et coupe au **plus grand
trou** : ici 39 points de hauteur séparent le sexe du visage, contre 3 entre la
bouche et les yeux. L'asset désigne lui-même ses paquets, et la règle
se transporte à tout asset à deux foyers.

⚠ **Ce n'était pas « seulement les yeux »**, ce que l'œil croyait. Sans le
détail par grappe (`DETAIL grappe` sous `--measure-only`), on aurait fait un
macro sur les paupières et perdu la bouche. **Mesurer où sont les zones avant
de choisir le cadrage.**

⚠ **Le trait de séparation se dessine, il ne s'insère pas** : un `-splice 0x1`
ajoute sa ligne à la hauteur et sort du 256 × 257, donc plus une icône carrée.

⛔ **Trois voies écartées pour ce même cas, toutes mesurées** (CANON 1.23) :
le **polyptyque** (vue d'ensemble plus une cellule par grappe), jugé « moins
bien » ; la **vignette unique très resserrée** (`--zone-to-top`, gardée au
moteur), lisible mais moins cohérente ; et deux leviers morts pour épaissir une
zone fine, `--wire` (aucun effet : c'est un **aplat** qu'on regarde, pas un
trait) et `--paint-dilate` (sature, la zone est un **îlot fermé** du maillage).

⚠⚠ **Le format carré impose la largeur.** À champ égal, une fois la hauteur
fixée, la largeur réellement montrée vaut la même distance physique : les mains
entrent dans le champ parce qu'elles y sont, non parce que la visée les
cherchait. Trois filtrages des points de visée n'y ont rien changé. Pour ne
dépendre que de la hauteur, ne donner à `fit_camera` que **deux points sur
l'axe vertical central**, dont le terme de largeur est nul par construction.

### 2.9 ⭐⭐⭐ La recette de la famille poitrine, arrêtée le 13-09-2026

*Symétrique du §2.7 pour les cibles. Six curseurs, six vignettes, un geste.
Chaque case cite un **nom** défini ailleurs dans cette spécification, jamais
un chiffre nu : c'est ce qui permet de reprendre une vignette sans rouvrir le
script.*

```sh
ATELIER=… CIBLES=… sh bin/poitrine.sh clair    # rend les bouts, puis assemble
ATELIER=… sh bin/assembler-poitrine.sh clair   # l'assemblage seul, sans GPU
```

| curseur | cibles `.target.gz` | vue (§5.5) | éclairage (§3) | matière (§4) | dispositif (§2) | nom livré |
|---|---|---|---|---|---|---|
| écartement | `breast-dist-decr` / `-incr` | **la paire**, 0,26 m | **la face** | le clair + delta d'aréole | **la coupe**, horizontale | `breast-dist-decr-incr.png` |
| taille d'aréole | `nipple-size-decr` / `-incr` | **la paire**, 0,26 m | **la face** | le clair + delta d'aréole | **la coupe**, horizontale | `nipple-size-decr-incr.png` |
| saillie du mamelon | `nipple-point-decr` / `-incr` | **la paire**, 0,26 m | **la face** | le clair + delta d'aréole | **la coupe**, horizontale | `nipple-point-decr-incr.png` |
| pointe | `breast-point-decr` / `-incr` | **la silhouette**, 0,15 m | **le liseré** | le clair + delta d'aréole | **la coupe**, verticale | `breast-point-decr-incr.png` |
| hauteur | `breast-trans-down` / `-up` | **la silhouette**, 0,20 m | **le liseré** | le clair + delta d'aréole | **la coupe**, verticale | `breast-trans-down-up.png` |
| répartition | `breast-volume-vert-down` / `-up` | **le gros plan**, 0,20 m | **le liseré** | le clair **grain fin** + delta d'aréole | **le double trait** | `breast-volume-vert-down-up.png` |

| réglage | valeur | pourquoi |
|---|---|---|
| fond | **noir opaque**, appliqué **en dernier** | même convention que les proxies (§2.7). ⚠ L'aplatir avant le tracé ferait mentir `outlineoverlay.py` et `composesplit.py`, qui cherchent leur région dans la **différence** des deux états |
| matière | **le clair des cibles**, `colorMixIn=0.68` (§4) | volontairement plus sombre que le porcelaine 0,92 des proxies : le corps d'un proxy est un **fond**, celui d'une cible est le **sujet** (CANON 1.24) |
| azimut | **25°** pour la paire, **70°** pour la silhouette et le gros plan | l'éclairage suit l'angle, il ne se recopie pas (§3). ⚠⚠ Le signe est celui de `rendertargetthumbs.py`, **inverse** de `rendermeshthumbs.py` (§5.4) |
| amplitudes | `--amounts 1.0 --after-only` pour les coupes, **sans** `--after-only` pour le double trait | le double trait a besoin de l'état **médian** en plus des deux bouts : c'est le fichier `-before` |
| trait | chaud `#F0E442` pour le bout haut, froid `#56B4E9` pour le bas, 3 px | Okabe-Ito. Mesure du 13-09 : les deux traits restent séparés de **189 à 201** en distance RGB sous les trois daltonismes, contre 232 en vision normale, là où rose/cyan tombait à 55 |
| communs | `--who female --size 256 --refine --hide-inner --fstop 0 --samples 512` | §5.5 |

⭐ **Les noms livrés ne s'inventent pas.** Une image de curseur MPFB s'appelle
`<cible-basse>-<suffixe-haut>.png` et vit dans `data/targets/_images/`. Les six
ci-dessus **existent déjà** parmi les 216 images de l'extension installée : la
livraison est un remplacement, pas un ajout.

⚠ **Les prises et l'axe de coupe sont liés** : `--rect` donne 256 × 128 et
demande une coupe horizontale, `--portrait` donne 128 × 256 et demande une
coupe verticale (§2.1). Le gros plan est carré, et c'est cohérent : le double
trait produit une **image unique**, pas un assemblage.

⭐ **Reproductibilité mesurée depuis ce dépôt seul** : trois à vingt-trois
pixels d'écart sur 65 536 pour les cinq coupes, contre 33 000 à 60 000 pour un
témoin décalé d'un degré d'azimut. La répartition fait exception en compte
(8 199 px) sans faire exception à l'œil : son amplitude moyenne vaut 0,066 sur
255 contre 8,16 pour le témoin, son grain de pores en gros plan ne se
redébruitant pas à l'identique. Table complète au README.

⭐ **Le tracé est insensible au corps**, mesuré : il couvre 2,49 % des pixels
sur corps clair contre 2,52 % sur gris. Il est dessiné **en 2D après le
rendu**, donc ni l'éclairage ni la courbe de rendu ne l'atteignent. Avant de
recalibrer une couleur pour un nouveau fond, demander par où elle passe
(CANON 1.24).

---

## 3. Les éclairages

⚠⚠ **Règle générale : l'éclairage se règle par angle de vue, jamais recopié en
chiffres fixes.** À 25° la lampe arrière est derrière le sujet et n'éclaire
presque rien de visible ; à 70° elle frise la surface. À réglages identiques,
121 de moyenne à 25° contre 158-184 à 70° (CANON 1.2).

| nom | valeurs | monde | prévu pour |
|---|---|---|---|
| **le studio** | `key=1.0,fill=1.0,rim=1.0,spot=1.0` | 1,0 | le défaut du `studio_base.blend`. Le plus de volume et le seul dont le contour passe **les deux thèmes** (CANON 1.20) |
| **le liseré** (*rim*) | `key=0.7,fill=0.6,rim=2.0,spot=0.05` | 0,4 | profils et gros plans, azimut ≥ 70°. Et **tous les proxies** : c'est ce que `bin/proxies.sh` pose |
| **la face** (*front*) | `key=1.1,fill=0.9,rim=4.0,spot=0.05` | 0,55 | vues proches de la face, azimut ≤ 40°, où la lampe arrière ne frise pas. Le contre-jour doit y être **fort** : à 2,0 le liseré disparaît (bord contre fond 146,7), à 4,0 il est franc (167,5), à 6,0 il brûle |

**Retirés, gardés pour ne pas les réinventer** (CANON §2) :

| nom | valeurs | verdict |
|---|---|---|
| *le volumineux* | `key=0.8,fill=0.2,rim=4,spot=0.05`, monde 0,2 | beau modelé, mais **plaque** l'avant du buste en blanc avec du noir devant. Ce n'est pas le contre-jour seul, c'est sa combinaison avec un remplissage et une ambiante bas |
| *le plat* | `key=0.4,fill=2.0,rim=0.2`, monde 0,6 | seul moyen d'éclairer le fond de l'entonnoir du mamelon ; inutile depuis que la pigmentation le masque |

⚠ **Remonter l'ambiante ne sauve pas un contour.** De 0,4 à 0,7, soit 75 % de
lumière en plus, le décile du contour gagne 3 points là où il en manque 22, et le
volume baisse de 31,99 à 31,14. Les deux mesures divergent, donc ce n'est pas un
progrès (CANON 1.17).

⚠ **Arbitrage ouvert sur le studio, pour les CIBLES** : il bat nos préréglages
sur nos propres critères (volume 22,05 contre 18,63 sur un nez macro, 16,85
contre 14,29 sur la poitrine) mais n'a **pas** de contre-jour marqué, donc pas
le « gris avec liseré et beaucoup de volume » demandé. Le choix se fait **par
famille**, pas globalement, et il **brûle l'épure** (216 de moyenne, 17 % de
tons moyens) : pour elle, l'adopter obligerait à baisser l'albédo (CANON 1.20).
Voir §9. ⛔ **Pour les proxies, cet arbitrage est tranché le 13-09** : voir
ci-dessous.

⭐ **Éclairage par défaut du cas générique, arbitré le 12-09-2026 : la face.**
Choisi à l'œil contre le liseré sur le buste de test, pour un dispositif
portrait/blueprint à azimut proche de 0. **Ne tranche pas l'arbitrage
ci-dessus** ni le choix par famille : sur un profil marqué (azimut ≥ 70°) ou
sur une épure, la question reste ouverte telle que décrite plus haut.

⭐⭐⭐ **Confirmé et généralisé le 13-09-2026, pour les PROXIES sur fond noir et
corps porcelaine (`--albedo 0.92`)** : **la face**, monde 0,55, bat le liseré
sur toute la gamme testée, corps 198 contre 158, écart corps/encre 113 contre
81. La combinaison fond noir + corps porcelaine + exposition +0,7 ne brûle
pas l'épure (zéro pixel saturé), ce qui lève le problème qui limitait « la
face » aux cibles seules. Voir §2.7 et CANON 1.23.

---

## 4. Les matières

| nom | valeurs | pour |
|---|---|---|
| **le gris du studio** | `colorMixIn=0.5,colorMixInStrength=0.6` ; `0.62` linéaire pour un asset (`--grey`) | partout |
| **le grain fin** | idem + `pore_strength=0.10,pore_scale=6000` | les gros plans |
| **le delta d'aréole** | `nipple:colorMixIn=0.15,colorMixInStrength=0.6` | la famille poitrine |
| **le blanc technique** | `0.92` **et** exposition +0,9 diaphragme | la moitié maillage d'un diptyque |
| **le clair des cibles** | `colorMixIn=0.68,colorMixInStrength=0.70` | toute la famille poitrine sur fond noir (§2.9). Volontairement **plus sombre** que le porcelaine des proxies : entre 0,50 et 0,92 le modelé perd 13 à 18 % et les tons moyens tombent de 95 à 83 %, tandis que l'amplitude du changement monte de 27 à 41. Les deux critères vont en sens **inverse**, et 0,68 est le seul niveau où ils tiennent ensemble : 5 % de modelé perdu, 5 à 22 % d'amplitude gagnée, 99 % de tons moyens (CANON 1.24) |
| **le corps très clair** | albédo remonté, sans exposition | l'épure, sur fond transparent (cibles) |
| **le porcelaine** | `--albedo 0.92`, `--exposure 0.7` | tous les proxies, sur fond noir opaque (13-09) |

⚠ **Gris, pas blanc.** Le gris est le seul stable quel que soit le thème : 6 points
d'écart entre thème clair et sombre contre 48 pour le blanc. Ce n'est pas un
compromis, c'est une indépendance (CANON 1.1). ⚠ **Ne s'applique qu'aux cibles**,
qui restent sur fond transparent. Sur fond **noir opaque**, ce problème
n'existe plus : le corps peut être porté à 0,92 sans risque d'inversion de
contraste, voir le porcelaine ci-dessus et CANON 1.23.

⚠ **Le grain suit l'échelle du cadre.** Des pores réglés pour un corps entier
deviennent des cratères en gros plan, et la texture prend le pas sur la forme. Le
grain redevient cratère à `macro` (CANON 1.2, 1.21).

⚠ **Le delta d'aréole compense l'éclairage.** Une lumière claire noie le pigment :
contraste 37 à 0,20/0,4, 45 à 0,15/0,6, 57 à 0,10/0,8, et 95 à 0,05/1,0 mais
l'aréole devient une **pastille noire**. Retenu 0,15/0,6 (CANON 1.2).

⚠ **Ordre d'application** : le réglage global (`--skin-tune`) s'applique aux
**sept** matériaux du corps, donc il écrase un réglage de zone posé avant lui.
Le global d'abord, la zone (`--zone-tune`) ensuite.

---

## 5. Les cadrages

⭐⭐ Le cadrage n'est pas une échelle mais **deux**, indépendantes (CANON 1.21).
Une vignette se spécifie sur l'une **ou** l'autre, jamais sur les deux.

### 5.1 Échelle A : combien de corps (`--top`, fraction de la hauteur)

| nom | `--top` | ce qu'on voit |
|---|---|---|
| `full length` | 0 | de la tête aux pieds |
| `wide bust` | 0,58 | jusqu'au haut des cuisses |
| `bust` | 0,45 | jusqu'au bas du ventre |
| `portrait` | 0,30 | jusqu'au niveau des seins |
| `head` | 0,12 | la tête |

⚠ `face` retiré : il n'y a aucune raison de cadrer sur un front.

⚠ **Le cadrage des épures est à `--top 0.20`**, valeur posée par `bin/proxies.sh`
et non un palier de cette échelle. En pied les arêtes s'écrasent en moiré
(distance médiane 2,1 → 9,2) ; plus serré, on perd le contexte du corps
(CANON 1.7). Divergence à trancher, voir §9.

### 5.2 Échelle B : combien serré sur une région

⚠⚠ **Chaque palier s'illustre d'une région différente.** Montrer les quatre sur
la poitrine se retourne contre la démonstration : en macro « on voit juste le
thorax en gros plan, on ne voit même plus ce que c'est » (correction de Raphaël,
CANON 1.21).

| nom | région de référence | ce qu'on garde | largeur |
|---|---|---|---|
| `wide` | les seins | du menton au ventre | à figer (§9) |
| `medium` | le sexe | la zone avec son contexte | à figer (§9) |
| `tight` | les mains | la zone seule | à figer (§9) |
| `macro` | le nez | un seul détail | **0,06 m** |

⚠ `macro` veut 0,06 m et **non 0,09** : à 0,09 il reste les yeux et la bouche,
donc c'est un gros plan de visage, pas une macro.

⭐ La force de cette échelle est d'être **nommée et non déduite**. Définir la macro
en multiples de la région qui bouge ne transfère pas d'un nez à une oreille, dont
la cible ne déplace que le lobe. En laissant l'auteur choisir son palier, le
problème disparaît.

⚠⚠ **`tight` et `macro` exigent `--one-side`.** En serrant sur une région
symétrique il faut à un moment choisir un côté : avec `--on-axis` les deux paliers
serrés se rapprochent du **sternum** et l'on obtient une peau nue sans repère. La
correction n'est pas cosmétique, elle change ce que la vignette montre.

⚠ **De profil, viser le côté opposé à la caméra** (`--far-side`) : le détail proche
fait face et n'est sur aucun contour (CANON 1.2).

### 5.3 Les vues déduites, côté assets

Trois cadrages qui ne sont pas des paliers mais des **calculs** :

| nom | comment il se calcule | pour |
|---|---|---|
| **l'écart** | zone où le proxy s'écarte du corps, seuil `max(4 × médiane, 0,35 × maximum)` plafonné à 3 % des sommets ; marge `min(4, max(1.2, 0.55 / étendue))`, plafond porté à **5,5** | le diptyque |
| **l'enveloppe** | enveloppe des zones peintes, marge 1,02 | la carte |
| **l'entier** | tout l'objet | le portrait |

⚠⚠ **Une fraction fixe des sommets ne marche pas.** Sur un proxy générique l'écart
a une médiane de 0,3 mm pour un maximum de 13 mm : prendre les 15 % les plus
écartés retient 2 000 points dispersés sur tout le corps et le cadre reprend le
corps entier. Le seuil relatif ramène à 185 points (CANON 1.9).

⚠⚠ **La marge doit être relative à l'étendue de l'écart.** Une marge fixe de 3,5,
parfaite là où l'écart tient dans quelques centimètres, réduit les huit corps
génériques à deux silhouettes minuscules quand l'écart est diffus : les paires
confondables tombaient de 22 à 3 sur 105, et la lisibilité des facettes s'effondrait
de 108,9 à 75,8 (CANON 1.9). Étendue mesurée de 4 % (les deux sexes, marge 4,0) à
97 % (un corps générique, marge 1,2).

⚠ **Le plafond de marge se calibre aux deux extrêmes.** Posé à 4,0 sur le premier
cas de gros plan, il mordait sur le cas où l'écart est le plus petit du lot. Porté
à **5,5** : le pubis, la racine et les testicules entrent dans le cadre et
l'anatomie se lit (CANON 1.14).

⚠⚠ **Un proxy PARTIEL fait mentir la mesure d'écart.** Quand il **retire** de la
géométrie plutôt que d'en ajouter, les sommets les plus écartés sont ceux du
**bord de coupe**, là où le corps a disparu, non l'objet. D'où un gros plan sur
l'arrière d'un crâne pour `head_only`. Détecté à la taille, sous 0,9 m de haut :
on cadre alors sur **l'objet** (CANON 1.10).

⚠ **Le corps de base doit recevoir le même traitement** que le proxy, subdivisions
coupées comprises : sinon il reste lisse quand le proxy est à facettes, et la
vignette oppose deux **traitements** au lieu de deux maillages (CANON 1.9).

### 5.4 L'azimut

⚠⚠ **Le signe est inversé entre les deux moteurs.** Les valeurs ci-dessous
(25°, 70°, 90°) sont celles de `rendertargetthumbs.py`, pour les **cibles**,
où un azimut négatif fait regarder à gauche. Sur `rendermeshthumbs.py`, pour
les **proxies**, c'est l'inverse, vérifié à l'œil sur six valeurs le 13-09 :
un azimut **positif** fait regarder à gauche. Ne jamais recopier une valeur
d'un moteur à l'autre sans revérifier le sens sur l'image.

| valeur | usage |
|---|---|
| **+34°** | tous les proxies (`rendermeshthumbs.py`), depuis le 13-09 ; symétrique exact de l'ancien −34° figé, dont le sens s'est révélé inversé |
| **25°** | « la paire », trois-quarts de face, **cibles**. Éclairage **face** |
| **70°** | « la silhouette » et « le gros plan », trois-quarts de profil, **cibles**. Éclairage **liseré** |
| **90°** | profil strict, **cibles** |

⭐ **Valeur par défaut du cas générique, arbitrée le 12-09-2026 : azimut −25°,
éclairage face.** Vérifiée à l'œil sur une cible de visage (`nose-base-down`) :
à −25° le personnage regarde vers la **gauche** de l'image, presque de face ;
à −45° le trois-quarts est net, le regard se lit sans ambiguïté vers la
gauche. Choisie pour équilibrer des icônes qui, ailleurs, regardent
généralement vers la droite. **Elle ne remplace pas la table ci-dessus** :
c'est le réglage à prendre quand aucune des lignes du tableau (ou la règle du
§6) ne s'applique mieux au cas en cours. Elle ne s'étend pas au `macro`, à la
**carte**, ni à un cadrage serré, pour lesquels l'avertissement suivant reste
entier.

⚠ L'azimut ne se montre que dans **un seul sens**, de −25° à +90° (ou son
image miroir côté gauche) : un demi-tour suffit à donner l'échelle, et les
vignettes existantes vivent dans cette plage.

⚠ **L'azimut n'a pas de sens** sur un `macro` et sur les paliers serrés en général :
à cette échelle c'est le choix du côté (`--one-side`, `--far-side`) qui décide de
ce qu'on voit, pas l'angle de rotation du corps. Il n'en a pas davantage pour une
**carte** en pied, où la pose et l'enveloppe fixent le cadre.

### 5.5 Les trois vues nommées, côté cibles

| nom | définition | option |
|---|---|---|
| **la paire** | trois-quarts à 25°, format couché, coupe horizontale. Les deux seins visibles, les deux mamelons assombris en repères | `--rect --azimuth 25 --on-axis` |
| **la silhouette** | trois-quarts à 70°, format debout, coupe verticale, visée remontée de 6 cm | `--portrait --azimuth 70 --lift 0.06` |
| **le gros plan** | carré, bras tendus, aucun visage. Pour un changement **intérieur** à la forme | `--azimuth 70 --lift 0.02 --arms-down 0` |

⚠ **Une vignette doit se reconnaître, pas seulement montrer.** La visée mesurée
tombe sur ce qui bouge, ce qui est juste et insuffisant : sans repère, le cadre
montre un bras et un ventre. La remontée de 6 cm garde le menton et le cou ; à
10 cm la bouche et le nez entrent et l'œil quitte le sujet (CANON 1.1).

Communs à toutes les vignettes de cibles :
`--who female --size 256 --refine --hide-inner --fstop 0 --samples 512`.

⚠ `--who female` et non `neutral` : les cibles de poitrine sont invisibles sur le
neutre. ⚠ `--hide-inner` : dents et langue n'ont aucune clé de forme, ne suivent
aucune déformation, et leurs textures manquent, donc elles ne peuvent que fuir en
magenta dès qu'une cible écarte les lèvres (CANON 1.6).

---

## 6. La règle de décision

### 6.1 Une cible (curseur)

**Un seul critère, mesuré : le déplacement de contour**, c'est-à-dire l'aire où
l'alpha diffère entre les deux bouts du curseur, rapportée au sujet.

| déplacement de contour | dispositif |
|---|---|
| **au-dessus de ~5 %** | **le double trait** (le contour bouge, il y a à tracer) |
| **en dessous** | **la coupe** avant/après |

Mesures sur la poitrine : hauteur 18,3 %, pointe 10,1 %, répartition 7,0 % contre
écartement 3,6 % et saillie 0,47 % (CANON 1.2).

⚠⚠ **Ce seuil juge un CADRAGE, pas une cible.** Le même téton passe de 0,47 % en
vue trois-quarts à 5,70 % en gros plan de profil. Donc : choisir la vue d'abord,
mesurer ensuite.

⚠ Et il faut que le **sujet tienne la silhouette** : bras baissés, 2,35 % contre
7,0 % bras tendus.

### 6.2 Un asset (proxy)

⛔ **SUPERSEDÉ le 13-09-2026 pour le CHOIX du dispositif** : voir §2.7 et CANON
1.23. Le classement à sept règles ci-dessous, mesuré sur 15 assets, a été
remplacé par un classement à trois régimes mesuré sur trois nombres
(`neufs` / `grappes` / `étendue`), plus simple et validé sur les 29 proxies
des deux paquets. Gardé ici pour la genèse (§6.3) et parce que `density` reste
utile ponctuellement pour repérer un maillage de jeu.

**Quatre mesures, sept règles, et l'ordre compte autant que les seuils** (état
avant le 13-09) :

| mesure | définition |
|---|---|
| `density` | arête moyenne du proxy sur celle du corps |
| `shape` | 99ᵉ percentile de la distance au corps, sur l'arête moyenne |
| `max` | plus grande distance au corps, en mètres |
| `far` | part des sommets à plus de 10 mm du corps |

1. `density > 1.5` → **épure**. Un maillage de jeu, quoi qu'il fasse par ailleurs.
2. hauteur du proxy `< 0.9 m` → **diptyque**. Un objet partiel, une tête seule.
3. `max > 0.30` → **portrait**. Un membre remplacé : la sirène.
4. `far > 0.25` → **portrait**. Tout le maillage est ailleurs : le squelette.
5. `max > 0.06` → **diptyque**. Un ajout local : un sexe.
6. `shape < 0.30` → **épure**. Un rééchantillonnage de la même surface.
7. sinon → **carte**. Un vrai changement de forme : une musculature.

⚠ **La règle 1 doit passer en premier** : un maillage à 412 faces s'écarte du corps
sur 47 % de ses sommets par le seul **facettage**, donc la règle 4 l'attraperait.
⚠ **La règle 3 avant la règle 4** : seulement 5 % des sommets de la sirène
s'écartent, mais ils s'écartent de 74 cm.

⚠ **Le seuil 0,30 de la règle 6 est lu dans les données**, pas déduit d'un principe.
Le raisonnement « une retopologie s'écarte d'au plus une longueur d'arête » est
vrai, mais les vrais changements de forme du pack sont **aussi** sous une longueur
d'arête : 0,58 pour une musculature. Ils restent cinq à sept fois au-dessus des
vraies retopologies, mesurées à 0,00, 0,08 et 0,11. Une musculature MakeHuman est
un changement **plus fin que la résolution du maillage**, ce qui explique qu'elle
résiste à tous les dispositifs.

Appliqué à `proxies01_cc0`, 15 assets : **7 épures, 4 diptyques, 2 portraits,
2 cartes**, aucun cas codé à la main.

### 6.3 D'où vient cette règle : les 12 %

Le classement du §6.2 est la forme opérationnelle d'un seul arbitrage, énoncé le
06-09 sur le **critère d'étendue de l'écart** (CANON 1.11) :

| étendue de l'écart | dispositif |
|---|---|
| **sous 12 %** du sujet | **la paire** (diptyque), gros plan sur l'écart, lisse contre maillé |
| **au-dessus** | **la vignette simple** (épure) au trait d'encre, cadrée sur la tête |

Rendement mesuré sur les quinze :

| dispositif | médiane | paires sous 2 | facettes |
|---|---|---|---|
| départ : lisse, subdivisé, en pied | 1,8 | 55/105 | 77,4 |
| tout en vignette simple | 15,5 | 22/105 | 108,9 |
| tout en paire, objet entier | 14,3 | 28/105 | 97,7 |
| **la règle des 12 %** | **30,4** | **11/105** | **111,3** |

⭐ **La généralisation qui en a été tirée** : 12 % d'étendue est une lecture de
« l'écart est-il local ou diffus ». Le §6.2 remplace cette lecture unique par
quatre mesures, parce qu'un écart diffus se subdivise lui-même en trois cas que
les 12 % ne séparaient pas : le maillage de jeu (règle 1), le corps entièrement
autre (règles 3 et 4), et le changement de forme fin (règle 7). Les règles 2 et 5
sont le côté « local » des 12 %, celles de l'épure le côté « diffus ».

### 6.4 La question préalable : retrouver ou comprendre

⭐⭐⭐ Avant toute mesure, une distinction de fond, qui vaut au-delà de MakeHuman
(CANON 1.13) :

| besoin | dispositif |
|---|---|
| **retrouver** un asset dans une grille | épure au trait d'encre, cadrée sur la tête |
| **comprendre** ce qu'un asset modifie | carte, cadre collé aux zones |

⚠ La métrique de distance entre icônes mesure le **premier** besoin. Elle a paru
condamner la carte alors que la carte sert le second. **Vérifier que la mesure
teste bien l'objectif visé**, et pas un objectif voisin.

### 6.5 L'exception nommée

`--device <nom>=<dispositif>` impose un dispositif pour un asset donné. Prévu pour
le cas « si Joël dit pour tel asset je préférerais un diptyque ».

⭐ Une exception nommée vaut mieux qu'un seuil tordu pour la faire entrer. Et le
journal imprime **les deux** dispositifs, l'imposé et le mesuré, sinon une
exception masque une règle qui se dégrade et l'on ne s'en aperçoit qu'au pack
suivant.

⚠ **Une heuristique ne doit jamais défaire une consigne.** La règle des 12 %
annulait six lignes plus bas le dispositif imposé, et le mode automatique écrasait
`--top` : l'explicite prime, en **un seul** endroit, après toute la chaîne
(CANON 1.19).

---

## 7. Comment ajouter un cas

1. **Dire le besoin** : quelle différence doit se voir, et pour qui. Retrouver ou
   comprendre (§6.4) ?
2. **Mesurer**, pas juger : déplacement de contour pour une cible (§6.1), les
   quatre nombres pour un asset (§6.2).
3. **Sortir la planche de contact** du type de vignette concerné avant de produire.
   On choisit sur une planche, on ne produit pas à l'aveugle.
4. **Si le cas tombe dans une case existante**, la spécification est complète :
   dispositif, vue, éclairage, matière.
5. **S'il n'y tombe pas**, ne pas tordre un seuil. Deux voies : une **exception
   nommée** (§6.5) si le cas est isolé ; une **nouvelle règle mesurée**, insérée à
   sa place dans l'ordre du §6.2, si une famille s'annonce. Puis l'inscrire au §9
   le temps qu'elle soit tranchée.
6. **Vérifier la conséquence, jamais le message.** Un journal prouve une intention,
   pas un effet : trois pannes de la même nuit annonçaient le bon réglage sur une
   image fausse (CANON 1.14).
7. **Signe d'un vrai progrès** : les **deux** mesures montent ensemble, la
   distinction entre icônes et la lisibilité des facettes. Quand l'une monte
   pendant que l'autre s'effondre, c'est un défaut déguisé en amélioration
   (CANON 1.15).

⚠ Et le rappel qui a coûté le plus cher : **la mesure sert à détecter l'impossible,
pas à choisir le meilleur.** Elle s'est trompée cinq fois sur cinq en récompensant
un défaut (trait à 12 % congestionné, épaisseur fixe transformant les maillages
denses en taches, marge fixe réduisant les corps à des silhouettes minuscules).
C'est l'œil du commanditaire qui tranche (CANON 1.15).

---

## 8. Ce qui est réellement implémenté

⭐⭐⭐ **`rendermeshthumbs.py` est versionné dans ce dépôt depuis le
13-09-2026** (commit qui a ajouté `bin/rendermeshthumbs.py` et
`bin/proxies-v2.sh`). L'avertissement du 12-09 ci-dessous ne vaut plus pour ce
script ; il est corrigé et complété.

| option | script | état |
|---|---|---|
| `--azimuth --elevation --width --lift --look-at --rect --portrait --size --samples --amounts --arms-down --hide-inner --one-side --on-axis --far-side --aim --refine --region --stylise --sector --weight --lights --world --skin-tune --zone-tune --sss --skin --skin-saturation --skin-lift --fstop --base --fit --who --framing --single-rig --ethnicity` | `bin/rendertargetthumbs.py` | ✅ vérifié dans ce dépôt |
| `--axis --split --measure --mirror --stack --outline --no-arrow --bare` | `bin/composesplit.py` | ✅ vérifié |
| `--width --colour` | `bin/keyline.py` | ✅ vérifié |
| `--curve --width` | `bin/drawoutline.py` | ✅ vérifié |
| `--region --colour --colour2 --also --width --edges` | `bin/outlineoverlay.py` | ✅ vérifié |
| (trois positionnels) | `bin/composediptyque.py` | ✅ vérifié |
| `--top --flat --grey --wire --wire-colour --paint --highlight --compare --mesh-pair --zone --device --shape --subdiv` | `bin/rendermeshthumbs.py` | ✅ **versionné depuis le 13-09** (voir ligne suivante pour les options ajoutées ce jour-là) |
| `--out --albedo --paint-floor --paint-emission --paint-new --frame-new --measure-only` (métriques `neufs`/`grappes`/`étendue`) | `bin/rendermeshthumbs.py` | ✅ ajoutées le 13-09-2026, patchs séparés conservés dans `makehuman-scripts-2026-09-13/` sur `~/dev/admin` (hors dépôt, historique de développement) |
| `--frame-zone haut\|bas` (cadrer sur un paquet de zones, coupé au plus grand trou de hauteur) | `bin/rendermeshthumbs.py` | ✅ ajoutée le 13-09, pilote le diptyque empilé du §2.8 |
| `--base-force neutral\|male\|female` (imposer le corps porteur) | `bin/rendermeshthumbs.py` | ✅ ajoutée le 13-09. ⚠ Exception nommée : seul `jujube_proxy_with_helpers_test` s'en sert, le neutre reste la règle |
| `--resolution <px>` (rendu carré plus grand, pour recadrer sans flou) | `bin/rendermeshthumbs.py` | ✅ ajoutée le 13-09 |
| `--zone-to-top <marge_m>` (zoom vertical pur, du bas de la zone au sommet du crâne) | `bin/rendermeshthumbs.py` | ✅ ajoutée le 13-09, **non retenue** en production : voir §2.8 |
| `--polyptych`, `--paint-dilate` | `bin/rendermeshthumbs.py` | ⛔ présentes mais **écartées**, mesures au CANON 1.23. Gardées pour ne pas les réinventer |
| `bin/composer-diptyque-empile.py` |  | ✅ empile les deux demi-formats du §2.8 en un carré |
| `bin/epaissir-zone.py` |  | ✅ épaissit une zone colorée **dans l'image**, seul levier qui agisse quand la zone est un îlot fermé du maillage. En réserve, inutile depuis le diptyque |
| `bin/mesurer.py`, `bin/daltonisme.py`, `bin/morceaux.py` |  | ✅ mesures : contraste corps/encre, simulation des trois daltonismes, morceaux séparés d'un proxy |
| `bin/composer-polyptyque.py` |  | ⛔ essai consigné, non retenu |
| `--paint-rework` (densité normalisée) | `bin/rendermeshthumbs.py` | ⛔ présente mais **écartée** : n'ajoute rien à la densité brute, voir CANON 1.23 « ce qui a échoué » |
| couleurs d'encre `noir`, `brique`, `encre_bleue`, `vert_sombre` | `bin/rendermeshthumbs.py` | ✅ ajoutées le 13-09, testées pour le daltonisme |
| `bin/proxies-v2.sh <pack> {mesurer,global,local,disperse}` |  | ✅ recette arrêtée, remplace `bin/proxies.sh` pour les proxies (celui-ci reste utilisable pour d'autres besoins d'assets) |
| `bin/poitrine.sh [clair]` |  | ✅ recette arrêtée de la famille poitrine (§2.9) : rend les six paires de bouts, puis appelle l'assemblage. Sans argument, l'ancien gris ; `clair` pour la convention du 13-09 |
| `bin/assembler-poitrine.sh [clair]` |  | ✅ compose les six carrés de 256 à partir des bouts : cinq coupes et un double trait, puis fond noir opaque. Ne demande **pas** Blender, donc se rejoue en deux secondes |
| `ATELIER=` et `CIBLES=` |  | ✅ surchargent le dossier de travail et le dossier des `.target.gz` dans `poitrine.sh` et `assembler-poitrine.sh`. ⚠ Les autres scripts gardent un chemin en dur vers clairdelune : un chemin en dur **ne se teste pas** |
| `bin/filigrane.py`, `bin/mesurer-volume.py` |  | ⚠ cités par le CANON, absents de ce dépôt |

⚠ La copie de `asset_packs_staging` reste celle de Joël, qui n'expose que
`--pack --samples --subdiv --margin --exposure --ambient --gap --force
--no-download --whole` : ne pas y chercher les options ci-dessus.

---

## 9. Points d'arbitrage, non tranchés

*Cas déjà rencontrés qui ne rentrent proprement dans aucune case de cette table.
Ils ne sont pas forcés ; ils attendent une décision.*

### 9.1 ✅ RÉSOLU le 13-09-2026 : le moteur des assets n'était pas versionné

Toutes les options du §2 côté assets ne vivaient que sur la machine de rendu.
**Fait** : `rendermeshthumbs.py` et `bin/proxies-v2.sh` sont versionnés dans
`bin/` depuis le 13-09-2026. `filigrane.py` et `mesurer-volume.py` restent à
verser, ils ne sont pas mobilisés par le régime unifié du §2.7.

### 9.2 ✅ RÉSOLU PAR REMPLACEMENT le 13-09-2026 : la recette des 14 proxies contredisait le classificateur

`makehuman-lot2-recette-proxies-2026-09-12.md` fixait le mode asset par asset
sur un critère binaire écrit à la main, en désaccord avec le §6.2. **Les deux
sont maintenant caducs** : le §6.2 est superseded (voir §6.2), et le
classement à trois régimes du §2.7 a été mesuré et validé à l'œil sur les 29
proxies des deux paquets, recette y compris. La table de désaccord ci-dessous
est gardée pour mémoire, elle ne pilote plus rien :

| asset | recette du 12-09 | §6.2 (caduc) | régime du 13-09 (§2.7) |
|---|---|---|---|
| `culturalibre_blind_hand` | `simple` | diptyque (règle 2) | local |
| `culturalibre_big_foot` | `simple` | diptyque (règle 2) | dispersé |
| `joachip_snek` | `simple`, « testé en zone, moins lisible » | portrait (règle 3) | dispersé |
| `myxibrium_low_poly_with_mouth_interior` | `simple` | épure (règle 1) | global |
| `wolgade_female_muscular` / `less_muscular` | `zone` | carte (règle 7) | dispersé |

### 9.3 `female_generic` et sa version `_fixed` : montrables par aucune vignette

Même `.obj` (md5 `511ac30e`), `.proxy` différents sur 16 lignes de 13 936 : douze
sommets que l'un interpole sur un triangle à six poids et que l'autre rattache
rigidement. Les deux vignettes sortent **identiques à 0,00 % de pixels**.

Ce n'est pas un manque de recette : la différence n'existe qu'**en déformation**,
jamais au repos, donc aucune image fixe ne peut la porter. **À décider** : deux
vignettes identiques assumées, une seule vignette pour les deux, ou une mention
textuelle dans le catalogue. (Et ce ne sont **pas** des doublons : le doublon
735/1518, lui, tient, car il a le même uuid, seul critère d'identité d'un asset.)

### 9.4 Les deux jumeaux musculaires : la carte informe mais ne distingue pas

`wolgade_female_muscular` et `less_muscular` restent à **1,1** de distance à 120 px
contre 15 à 30 partout ailleurs. Élargir la zone peinte n'y change rien (testé au
quart et aux deux cinquièmes du corps, la distance reste à 0,2 et l'on perd
l'information de **où**). Ce qui les sépare est un **motif de taches réparties**,
qu'une icône de 120 px ne porte pas. **Limite de résolution assumée, ou ces deux
assets réclament autre chose qu'une icône ?**

### 9.5 ✅ RÉSOLU le 13-09-2026, POUR LES PROXIES : l'éclairage du studio par défaut contre nos préréglages

Sur fond transparent (cibles), l'arbitrage reste ouvert tel que décrit :
l'éclairage du studio gagne sur nos critères mais brûle l'épure. **Pour les
proxies**, la question ne se pose plus dans les mêmes termes : sur fond noir
et corps porcelaine, **la face** bat le liseré sans brûler quoi que ce soit
(zéro pixel saturé), voir §3 et CANON 1.23. La bascule par famille reste
d'actualité côté cibles seulement.

### 9.6 ✅ RÉSOLU le 13-09-2026, POUR LE RÉGIME GLOBAL : `--top 0.20`

Confirmé et arrêté comme cadrage du régime **global** (§2.7) : ni un palier de
l'échelle A ni le `head` à 0,12, une valeur propre au régime. Le régime
**local** ne s'en sert plus, il cadre par `--frame-new` sur les sommets neufs
avec une marge relative (plafond 2,2), voir §2.7 et CANON 1.23.

### 9.7 Les trois premiers paliers de l'échelle B n'ont pas de valeur

`macro` vaut 0,06 m, mesuré. `wide`, `medium` et `tight` n'ont qu'une région de
référence et une intention, jamais un nombre : le script qui a produit
`shots-and-light.png` est **introuvable** (aucune trace locale, git, ni sur la
machine de rendu). **À décider** : remesurer les trois largeurs sur la planche, ou
les refixer à l'œil et les consigner.

### 9.8 La flèche du diptyque

Produite et comparée. **Sémantiquement justifiée**, la relation base →
remplacement étant orientée, contrairement à un curseur bidirectionnel où elle
avait été retirée. Mais **visuellement négligeable** à cette taille, et la position
gauche/droite dit déjà l'ordre de lecture. Recommandation : s'en passer. Jamais
tranché.

### 9.9 ✅ RÉSOLU le 13-09-2026, POUR LES PROXIES : le fond opaque au niveau du pack

**Tranché pour les proxies** : fond **noir** opaque. Voir §1, §2.7
et CANON 1.23. Ce choix rompt effectivement avec la convention transparente
des 41 vignettes existantes du catalogue, assumé par Raphaël. **Reste ouvert**
pour les cibles, et reste ouvert la question de savoir si le catalogue
existant (cibles + anciennes vignettes d'assets) doit être regénéré pour
suivre la même convention, ou coexister avec elle.

---

## 10. Index des renvois au CANON

| sujet | section |
|---|---|
| principes, gris contre blanc, fond du panneau | 1.1 |
| règles générales et leurs mesures, seuil des 5 % | 1.2 |
| réglages nommés | 1.3 |
| les trois vues des cibles | 1.4 |
| la famille poitrine arrêtée | 1.5 |
| faits sur le studio et MPFB (matériaux, maillages internes, taille d'icône) | 1.6 |
| ouverture des proxies, trait d'encre, subdivision | 1.7, 1.8 |
| comparaison au corps de base, seuil et marge relatifs | 1.9 |
| doctrine des proxies, sens de coupe mesuré, proxy partiel | 1.10 |
| la règle des 12 % | 1.11 |
| gris du studio pour les assets, blanc technique | 1.12 |
| la carte, émission, enveloppe collée, retrouver contre comprendre | 1.13 |
| journal contre effet, calibrage d'un garde-fou | 1.14 |
| les quatre familles de pannes silencieuses | 1.15 |
| trois correctifs de calcul, ordre épaisseur/cadrage | 1.16 |
| fond du thème, liseré, filigrane, marge du diptyque, exception nommée | 1.17 |
| limites de la mesure de contour | 1.18 |
| moitié lisse reconnaissable, explicite contre heuristique | 1.19 |
| l'éclairage du studio par défaut | 1.20 |
| les deux axes de cadrage | 1.21 |
| couper l'épure en deux | 1.22 |
| le système des proxies (fond noir, porcelaine, azimut, encre bleue, régime unifié) | 1.23 |
| voies écartées, à ne pas réinventer | §2 |
| pièges d'outillage | §3 |
| erreurs de méthode | §4 |
