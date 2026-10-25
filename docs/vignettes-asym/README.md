# Thumbnails for the 31 asymmetry sliders

One 256×256 thumbnail per slider of `src/mpfb/data/targets/asym`, where none
exists today. Reproduce the set with `bin/asymthumbs-v6.py` on the render
machine.

## What the image shows

Two things at once: the face pushed to one end of the slider, and the region
the target displaces, painted over it. If the left cheek swells, the thumbnail
shows the swollen cheek, the patch around it, and the deflated right cheek.

The region is read from the target file itself: a `.target` is a list of moved
vertices, so the painted area is known and not guessed. Intensity follows the
displacement, so the patch fades out at its edges.

## Conventions

Front view on axis, black opaque background, porcelain skin, both mirrored
light rigs on (`--mirror-lights`), region in #0072B2.

**Everything is shot from the front and centred on the axis**, ears included,
and the close-ups are no exception: both instances of a feature stay in frame.
An asymmetry is read against the symmetry it breaks, so a thumbnail that shows
one eye enlarges the patch and removes the term of comparison. Two framings
were tried and dropped for that reason: a profile for the ears, which shows one
ear only, and a crop on a single focus.

**The patch does not erase what it surrounds.** A flat opaque fill hid the very
relief the exaggeration had just made visible. The colour is applied preserving
the body's luminance (`-compose Colorize`) and the region is then darkened by a
fifth. Measured on three sliders: relief under the patch rises from 22-34 to
27-41 in standard deviation, while the patch stays at 111-152 in luminance
against 103-119 for the flat fill.

**Amplitude is per slider**, taken from the calibration of 16-09: the smallest
value whose symmetry residual clearly clears the neutral noise. Eyes are capped
at ×2, beyond which the eyelid looks damaged. Amplitude does not affect the
mask, which comes from the target file.

**Small regions are re-framed close**, in two passes: a probe that measures the
patch, then a frame computed on it. The brow and the nose cover 32 to 39 % of
the image, while the eyelid, the jaw and the skull fall to 3 to 5 %. The frame
stays centred, so its half-width is taken from whichever edge of the patch lies
further from the axis and only the height of the aim follows the patch; a
region spread across the whole face therefore gains little, which is the price
of keeping both sides. The re-frame is kept only where it measurably improves
coverage. `rendering-log.txt` records the probe coverage and the outcome per
slider.

## Checks

31 of 31 opaque. The contact sheet is `planche-v6.png`.
