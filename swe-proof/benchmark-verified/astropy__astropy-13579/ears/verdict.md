# P2 adversarial audit — astropy__astropy-13579

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Req1.5/1.4: coupled WCS, kept-axis pixel comes back finite ~0.
Exit 0 iff out_pix[0] is finite and ~0 (the correct slice-plane pixel)."""
import numpy as np
import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS

H = {
    'WCSAXES': 3, 'CRPIX1': (100+1)/2, 'CRPIX2': (25+1)/2, 'CRPIX3': 1.0,
    'PC1_1': 0.0, 'PC1_2': -1.0, 'PC1_3': 0.0,
    'PC2_1': 1.0, 'PC2_2': 0.0, 'PC2_3': -1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}
fits_wcs = astropy.wcs.WCS(header=H)
sl = SlicedLowLevelWCS(fits_wcs, 0)
world = fits_wcs.pixel_to_world_values(0, 0, 0)
out_pix = sl.world_to_pixel_values(world[0], world[1])
print("out_pix:", out_pix)
ok = np.isfinite(out_pix[0]) and np.allclose(out_pix[0], 0, atol=1e-6)
print("finite&~0:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.4: sliced world_to_pixel of the kept axes must match the unsliced
round trip's corresponding pixel coordinates for a coupled WCS.
Exit 0 iff sliced out_pix == unsliced pixels[0:2]."""
import numpy as np
import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS

H = {
    'WCSAXES': 3, 'CRPIX1': (100+1)/2, 'CRPIX2': (25+1)/2, 'CRPIX3': 1.0,
    'PC1_1': 0.0, 'PC1_2': -1.0, 'PC1_3': 0.0,
    'PC2_1': 1.0, 'PC2_2': 0.0, 'PC2_3': -1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}
fits_wcs = astropy.wcs.WCS(header=H)
sl = SlicedLowLevelWCS(fits_wcs, 0)
# world point at pixel (0,0,0)
world = fits_wcs.pixel_to_world_values(0, 0, 0)
full_pix = fits_wcs.world_to_pixel_values(*world)
out_pix = sl.world_to_pixel_values(world[0], world[1])
print("full unsliced pix:", full_pix)
print("sliced out pix:   ", out_pix)
# kept pixel axes are 0 and 1 (wavelength pixel axis 2 dropped)
ok = np.allclose(out_pix[0], full_pix[0], atol=1e-6) and np.allclose(out_pix[1], full_pix[1], atol=1e-6)
print("match:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3.2: pixel->world->pixel round trip on the sliced coupled WCS recovers
the original kept pixel coordinates.
Exit 0 iff w2p(p2w(px,py)) == (px,py)."""
import numpy as np
import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS

H = {
    'WCSAXES': 3, 'CRPIX1': (100+1)/2, 'CRPIX2': (25+1)/2, 'CRPIX3': 1.0,
    'PC1_1': 0.0, 'PC1_2': -1.0, 'PC1_3': 0.0,
    'PC2_1': 1.0, 'PC2_2': 0.0, 'PC2_3': -1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}
fits_wcs = astropy.wcs.WCS(header=H)
sl = SlicedLowLevelWCS(fits_wcs, 0)
px, py = 10.0, 7.0
w = sl.pixel_to_world_values(px, py)
back = sl.world_to_pixel_values(*w)
print("input pix:", (px, py))
print("world:", w)
print("recovered pix:", back)
ok = np.allclose(back[0], px, atol=1e-6) and np.allclose(back[1], py, atol=1e-6)
print("round-trip ok:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req4.1: independent (diagonal) axes -> sliced w2p returns the same kept-axis
pixels as the full unsliced w2p (placeholder was harmless here; must remain).
Exit 0 iff sliced == unsliced kept pixels."""
import numpy as np
import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS

# Fully diagonal PC (independent axes)
H = {
    'WCSAXES': 3, 'CRPIX1': 50.5, 'CRPIX2': 13.0, 'CRPIX3': 1.0,
    'PC1_1': 1.0, 'PC1_2': 0.0, 'PC1_3': 0.0,
    'PC2_1': 0.0, 'PC2_2': 1.0, 'PC2_3': 0.0,
    'PC3_1': 0.0, 'PC3_2': 0.0, 'PC3_3': 1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}
fits_wcs = astropy.wcs.WCS(header=H)
sl = SlicedLowLevelWCS(fits_wcs, 0)
# pick a spatial world point
world = fits_wcs.pixel_to_world_values(20, 8, 0)
full_pix = fits_wcs.world_to_pixel_values(*world)
out_pix = sl.world_to_pixel_values(world[0], world[1])
print("full:", full_pix, "sliced:", out_pix)
ok = np.allclose(out_pix[0], full_pix[0], atol=1e-6) and np.allclose(out_pix[1], full_pix[1], atol=1e-6)
# also confirm they equal the input pixels 20,8
ok2 = np.allclose(out_pix[0], 20, atol=1e-6) and np.allclose(out_pix[1], 8, atol=1e-6)
print("match_full:", ok, "match_input:", ok2)
raise SystemExit(0 if (ok and ok2) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1: pixel_to_world_values on the sliced coupled WCS still returns, for
each kept world axis, the underlying WCS's world coordinate (forward direction
unchanged by the fix). Compare sliced p2w against the full underlying p2w with
the dropped pixel axis fixed at its slice value (0).
Exit 0 iff sliced p2w matches the corresponding full-WCS world coords."""
import numpy as np
import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS

H = {
    'WCSAXES': 3, 'CRPIX1': (100+1)/2, 'CRPIX2': (25+1)/2, 'CRPIX3': 1.0,
    'PC1_1': 0.0, 'PC1_2': -1.0, 'PC1_3': 0.0,
    'PC2_1': 1.0, 'PC2_2': 0.0, 'PC2_3': -1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}
fits_wcs = astropy.wcs.WCS(header=H)
sl = SlicedLowLevelWCS(fits_wcs, 0)   # drop wavelength array axis (pixel z=0)
px, py = 11.0, 4.0
sliced_world = sl.pixel_to_world_values(px, py)
# underlying full transform at (x=px, y=py, z=0)
full_world = fits_wcs.pixel_to_world_values(px, py, 0)
print("sliced p2w:", sliced_world)
print("full p2w  :", full_world)
# kept world axes for a WAVE slice are the two spatial ones (indices 0,1)
ok = np.allclose(sliced_world[0], full_world[0]) and np.allclose(sliced_world[1], full_world[1])
print("forward unchanged:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.1 / Req4.3: range slice with a start offset -> returned pixel is
expressed in the sliced frame (start offset subtracted). Coupled WCS.
Exit 0 iff sliced w2p == unsliced kept pixels minus the range starts."""
import numpy as np
import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS

H = {
    'WCSAXES': 3, 'CRPIX1': (100+1)/2, 'CRPIX2': (25+1)/2, 'CRPIX3': 1.0,
    'PC1_1': 0.0, 'PC1_2': -1.0, 'PC1_3': 0.0,
    'PC2_1': 1.0, 'PC2_2': 0.0, 'PC2_3': -1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}
fits_wcs = astropy.wcs.WCS(header=H)
# array axes order is reverse of pixel: array [wave, y, x]. Slice: drop wave (int 0),
# range on y starting at 5, range on x starting at 10.
sl = SlicedLowLevelWCS(fits_wcs, [0, slice(5, 25), slice(10, 100)])
print("pixel_n_dim:", sl.pixel_n_dim)
world = fits_wcs.pixel_to_world_values(0, 0, 0)
full_pix = fits_wcs.world_to_pixel_values(*world)  # (x, y, z)
out = sl.world_to_pixel_values(world[0], world[1])
# kept pixel axes: x (offset 10), y (offset 5)
exp_x = full_pix[0] - 10
exp_y = full_pix[1] - 5
print("full:", full_pix, "expected sliced:", (exp_x, exp_y), "got:", out)
ok = np.allclose(out[0], exp_x, atol=1e-6) and np.allclose(out[1], exp_y, atol=1e-6)
print("offset ok:", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1.5/1.4: coupled WCS, kept-axis pixel comes back finite ~0.
Exit 0 iff out_pix[0] is finite and ~0 (the correct slice-plane pixel)."""
import numpy as np
import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS

H = {
    'WCSAXES': 3, 'CRPIX1': (100+1)/2, 'CRPIX2': (25+1)/2, 'CRPIX3': 1.0,
    'PC1_1': 0.0, 'PC1_2': -1.0, 'PC1_3': 0.0,
    'PC2_1': 1.0, 'PC2_2': 0.0, 'PC2_3': -1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}
fits_wcs = astropy.wcs.WCS(header=H)
sl = SlicedLowLevelWCS(fits_wcs, 0)
world = fits_wcs.pixel_to_world_values(0, 0, 0)
out_pix = sl.world_to_pixel_values(world[0], world[1])
print("out_pix:", out_pix)
ok = np.isfinite(out_pix[0]) and np.allclose(out_pix[0], 0, atol=1e-6)
print("finite&~0:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements describe the astropy SlicedLowLevelWCS.world_to_pixel_values fix: dropped world axes must carry the slice-location world value (obtained by transforming the sliced-out pixel position through the underlying WCS), not the constant 1.

Six probes, all HOLD on gold-patched tree:
- probe_1 (Req1.5/1.4, POSITIVE CONTROL): coupled WCS, kept pixel returns finite ~0. PATCHED HOLDS (out_pix[0]=-2.9e-12); BASE VIOLATED (out_pix[0]=1.818e11, near-infinite) => discriminates.
- probe_2 (Req1.4): sliced w2p of kept axes == unsliced full round-trip pixels. PATCHED match; BASE mismatch.
- probe_3 (Req3.2): pixel->world->pixel round trip recovers (10,7). PATCHED ok.
- probe_4 (Req4.1): diagonal/independent axes unchanged (placeholder was harmless). PATCHED ok.
- probe_5 (Req3.1): forward pixel_to_world unchanged vs full WCS. HOLDS on BOTH base and patched (correct: fix only touches inverse direction).
- probe_6 (Req2.1/4.3): range slice start-offsets subtracted (coupled WCS, offsets 10 and 5). PATCHED ok.

Candidate wrong-fix weak_zero.diff: replaces placeholder 1. with 0. (still a constant, ignores the slice-location world value). Probe suite REJECTS it: probes 1,2,3,6 VIOLATED (e.g. probe_1 out_pix[0]=-19.09, not ~0). probes 4,5 hold (expected — they don't exercise the coupled dropped-axis value). This demonstrates the suite discriminates the naive constant-placeholder fix that a weak reading of the requirements would permit; the runner can also confirm weak_zero fails the official harness.

All needed runs completed. >=5 distinct probes all hold on patched; positive control discriminates base vs patched; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1.5/1.4: coupled WCS, kept-axis pixel comes back finite ~0.
Exit 0 iff out_pix[0] is finite and ~0 (the correct slice-plane pixel)."""
import numpy as np
import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS

H = {
    'WCSAXES': 3, 'CRPIX1': (100+1)/2, 'CRPIX2': (25+1)/2, 'CRPIX3': 1.0,
    'PC1_1': 0.0, 'PC1_2': -1.0, 'PC1_3': 0.0,
    'PC2_1': 1.0, 'PC2_2': 0.0, 'PC2_3': -1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}
fits_wcs = astropy.wcs.WCS(header=H)
sl = SlicedLowLevelWCS(fits_wcs, 0)
world = fits_wcs.pixel_to_world_values(0, 0, 0)
out_pix = sl.world_to_pixel_values(world[0], world[1])
print("out_pix:", out_pix)
ok = np.isfinite(out_pix[0]) and np.allclose(out_pix[0], 0, atol=1e-6)
print("finite&~0:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements describe the astropy SlicedLowLevelWCS.world_to_pixel_values fix: dropped world axes must carry the slice-location world value (obtained by transforming the sliced-out pixel position through the underlying WCS), not the constant 1.

Six probes, all HOLD on gold-patched tree:
- probe_1 (Req1.5/1.4, POSITIVE CONTROL): coupled WCS, kept pixel returns finite ~0. PATCHED HOLDS (out_pix[0]=-2.9e-12); BASE VIOLATED (out_pix[0]=1.818e11, near-infinite) => discriminates.
- probe_2 (Req1.4): sliced w2p of kept axes == unsliced full round-trip pixels. PATCHED match; BASE mismatch.
- probe_3 (Req3.2): pixel->world->pixel round trip recovers (10,7). PATCHED ok.
- probe_4 (Req4.1): diagonal/independent axes unchanged (placeholder was harmless). PATCHED ok.
- probe_5 (Req3.1): forward pixel_to_world unchanged vs full WCS. HOLDS on BOTH base and patched (correct: fix only touches inverse direction).
- probe_6 (Req2.1/4.3): range slice start-offsets subtracted (coupled WCS, offsets 10 and 5). PATCHED ok.

Candidate wrong-fix weak_zero.diff: replaces placeholder 1. with 0. (still a constant, ignores the slice-location world value). Probe suite REJECTS it: probes 1,2,3,6 VIOLATED (e.g. probe_1 out_pix[0]=-19.09, not ~0). probes 4,5 hold (expected — they don't exercise the coupled dropped-axis value). This demonstrates the suite discriminates the naive constant-placeholder fix that a weak reading of the requirements would permit; the runner can also confirm weak_zero fails the official harness.

All needed runs completed. >=5 distinct probes all hold on patched; positive control discriminates base vs patched; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a 2-line change: adds sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep)) and replaces the placeholder world_arrays_new.append(1.) with world_arrays_new.append(sliced_out_world_coords[iworld]). Requirements model the changed observable behavior (dropped-axis fill value -> correct sliced-location world coordinate) biconditionally rather than pinning a narrow helper/branch. Probed live on the gold-patched instance image: patch verification HOLDS and all behavioral checks pass. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the defect into behavioral acceptance criteria without transmitting the hidden test. All concrete numeric/config detail cited (non-diagonal PCij matrix mixing spectral+spatial axes, near-infinite kept-pixel result, correct central-pixel expectation) is present in the PUBLIC problem_statement, which includes the full WCS header and reproduction. The only single FAIL_TO_PASS test (test_coupled_world_slicing) is not named; no test file path, no parametrization ids, no COUPLED_WCS_HEADER dict, and no `np.allclose(out_pix[0], 0)` assertion appear. Gold-patch identifiers (_pixel_to_world_values_all, _pixel_keep, sliced_out_world_coords, the placeholder `1.`->indexed-world-coord swap) are described behaviorally ('constant 1.', 'transform the sliced-out pixel position ... index by the underlying world-axis number') but the invented identifiers themselves are not quoted. Requirement 2.2 (single-kept-dim returns unwrapped) and Req 4 items reflect pre-existing code behavior / PASS_TO_PASS regression scope, not reconstruction of the new test. Naming sliced_wcs.py and world_to_pixel_values is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
