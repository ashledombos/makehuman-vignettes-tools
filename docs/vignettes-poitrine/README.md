# The breast family, with the region patch

The six breast thumbnails Joel validated on 08-09, re-rendered with the patch
used on the asymmetry icons added on top. Reproduce with
`bin/poitrine-taches.sh`.

Nothing else changed: same pose, same framing, same lighting, same grey skin,
same before/after split with its dashed separator and arrow. The patch is
painted from the target file and applied to each half before the split is
assembled, preserving the body's luminance so the relief stays readable.

Two observations from the board:

`nipple-size-decr-incr` gains the most, the patch ringing exactly the areola.
`nipple-point-decr-incr` gains the least, its region being a few millimetres
wide. On `breast-dist` and `breast-trans` the patch covers the whole breast,
which colours more than it points — but it is true: the target does move the
whole breast.

`breast-volume-vert-down-up` used to be a single square view carrying a double
outline. The patch replaces that outline, so it now takes the before/after
split like the other five, shot upright rather than square. It loses its square
framing and gains the family convention.
