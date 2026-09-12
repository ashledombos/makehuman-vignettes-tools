# Le vocabulaire des vignettes

*Arrêté le 06-09-2026, à la demande de Raphaël : sans un nom par effet, chaque
essai oblige à tout redécrire, et une amélioration obtenue sur une vignette se
perd en réglant la suivante.*

⚠ Distinguer les **vues**, qui disent d'où l'on regarde et jusqu'où l'on cadre,
des **effets**, qui disent ce qu'on ajoute à l'image. Une vignette est toujours
une vue **plus** un effet.

⚠ **La coupe et le diptyque ont chacun deux orientations**, et elle se mesure :
on projette la zone qui change sur les axes de la caméra et l'on compare ses
deux étendues. Plus large que haute, coupe **horizontale** et deux prises
couchées ; plus haute que large, coupe **verticale** et deux prises debout.
Vérifié : un sexe en érection sort couché, au repos debout.

⚠ L'orientation fixe donc aussi la **forme des prises**, puisque deux moitiés
doivent s'assembler en carré : 256 × 128 pour une coupe horizontale, 128 × 256
pour une verticale.

## Les effets

| nom | ce que c'est |
|---|---|
| **la coupe** | les deux bouts d'un curseur, côte à côte, séparés d'un trait pointillé. Chaque moitié est un demi-format, l'assemblage un carré. |
| **le double trait** | l'état **médian** rendu en dur, et les deux bouts tracés en courbes pointillées par-dessus, jaune `#F0E442` et bleu ciel `#56B4E9`, 3 px. Une seule image. |
| **le diptyque** | deux moitiés du **même** objet : à gauche le rendu, gris du studio et liseré ; à droite le maillage, tracé d'encre sur **blanc technique**, exposition montée de 0,9 diaphragme. Ce que ça rend, et de quoi c'est fait. |
| **l'épure** | une seule image, maillage tracé sur un corps très clair, facettes à plat, subdivision coupée. Un plan technique. Pour les retopologies. |
| **la carte** | une seule image, corps gris et lisse, et les zones qui s'écartent du corps de base peintes en **vermillon**. Dit **où** l'asset modifie quelque chose. |
| **le portrait** | une seule image, rien d'ajouté. Pour ce qui se reconnaît seul, un squelette, une sirène. |

## Les vues, côté cibles

| nom | cadrage |
|---|---|
| **la paire** | trois-quarts à 25°, format couché, coupe horizontale. Les deux seins, les deux mamelons en repères. |
| **la silhouette** | trois-quarts à 70°, format debout, visée remontée de 6 cm pour garder le menton. |
| **le gros plan** | carré, bras tendus, aucun visage. Pour un changement **intérieur** à la forme. |

## Les vues, côté assets

| nom | cadrage |
|---|---|
| **la tête** | le cinquième supérieur du sujet. Pour l'épure, où le sujet est la densité. |
| **l'écart** | la zone qui s'écarte du corps, marge relative à son étendue. Pour le diptyque. |
| **l'enveloppe** | les zones peintes, cadre collé à 2 %. Pour la carte. |
| **l'entier** | tout l'objet. Pour le portrait. |

## Les éclairages

| nom | valeurs |
|---|---|
| **le liseré** | `key=0.7,fill=0.6,rim=2.0,spot=0.05`, monde 0,4. Pour les profils et les gros plans. |
| **la face** | `key=1.1,fill=0.9,rim=4.0,spot=0.05`, monde 0,55. Pour les vues à 25°, où la lampe arrière ne frise pas. |
| ⚠ *le volumineux* | `key=0.8,fill=0.2,rim=4`, monde 0,2. **Retiré** : plaque l'avant du buste en blanc. |
| ⚠ *le plat* | `key=0.4,fill=2.0,rim=0.2`, monde 0,6. **Retiré** depuis que la pigmentation masque le cratère du mamelon. |

## Les matières

| nom | valeurs |
|---|---|
| **le gris du studio** | `colorMixIn=0.5,colorMixInStrength=0.6`, ou `GRIS_STUDIO` 0,62 pour un asset |
| **le grain fin** | idem plus `pore_strength=0.10,pore_scale=6000`. Pour les gros plans. |
| **le delta d'aréole** | `nipple:colorMixIn=0.15,colorMixInStrength=0.6` |
| **le blanc technique** | `BLANC_TECHNIQUE` 0,92 **et** exposition +0,9 diaphragme. La matière seule ne suffit pas. |

## Comment se dit une vignette

> « la silhouette au liseré, en coupe » — la poitrine, curseur de hauteur.
> « le gros plan, en double trait » — la répartition du volume.
> « l'écart, en diptyque » — un sexe ajouté.
> « la tête, en épure » — un maillage de jeu.
> « l'enveloppe, en carte » — une musculature.
> « l'entier, en portrait » — un squelette.
