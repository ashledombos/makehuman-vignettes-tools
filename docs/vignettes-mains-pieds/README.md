# Hands and feet, with the wireframe patch

Thumbnails for the official MPFB hand and foot targets
(`data/targets/hands|feet`, left side only, plus `measure-wrist-circ` and
`measure-ankle-circ`). Reproduce with `bin/lot6-fil-paire.sh`. Each view is a
neutral/modified split, with an arrow from neutral to the end of the slider it
shows, the region the target moves painted blue.

## Hands

Seen at 60°, back of the hand whole and fingers apart. Head-on the thumb
leaves the frame; at 90° the fingers overlap. The visual aim is measured on
the hand (`--one-side --aim geo`).

The hip behind the hand made it hard to read, so the trunk is hidden with
`--keep-above x:0.24`. This gives a Holdout material to the faces below the
threshold. ⚠ A Mask modifier does not work here: it changes the number of
evaluated vertices, and the aim and the patch, both read by vertex index, miss
the hand.

Frame width 0.32, except 0.28 for finger length (decrease).

`fingers-diameter` and `fingers-distance` move no vertex by more than 3 mm,
which leaves the neutral and modified states indistinguishable at any frame
that shows the whole hand. These two are therefore shown as **decrease against
increase**, the full travel of the slider, with one fixed aim for both halves
and no arrow. Each also comes as a GIF alternating the two states, where the
change is much easier to see.

The wrist targets move both wrists. Seen from behind, the right wrist's
wireframe floated in the picture even with the trunk hidden, so the targets
were filtered to the left side (x > 0 in the neutral mesh) before rendering.
Head-on (0°), width 0.32.

## Feet

Three-quarter and front views were rejected. Each target takes the view
where its movement reads best:

- **from below** (`--elevation -70`, aim 0.16, −0.06, 0.03, width 0.32) for
  `scale`, `scale-horiz`, `scale-depth`, `trans-in/out`,
  `trans-forward/backward`;
- **in profile** (90°, stacked landscape shots, aim 0.16, −0.06, 0.05, width
  0.40) for `trans-up/down`, `scale-vert` and the ankle girth.

The aim is set by hand: measured on the region, it climbs to the shin, which
the scale targets also move, and the foot is cut at the bottom.

In profile the right foot is hidden behind the left one until a target moves
or flattens it. It then shows as grey skin that looks out of register with the
wireframe, so it is hidden with `--keep-above x:0.05`. The ankle targets are
filtered to the left side as for the wrist.

Grey vertices left inside a patch are vertices the target does not move, such
as the fixed point of a scale.
