# P2 adversarial audit — matplotlib__matplotlib-25122

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1.1 (positive control): magnitude spectrum divides by SIGNED window sum.
Window has negative samples so signed sum != abs sum.
HOLDS on gold (divide by window.sum()); FAILS at base (abs(window).sum())."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(0)
N = 8
x = rng.randn(N)
# window with negatives: signed sum=5.0, abs sum=6.0 (distinct)
w = np.array([1., 1., -0.5, 1., 1., -0.5, 1., 1.])
print("signed sum=", w.sum(), "abs sum=", np.abs(w).sum())

spec, freqs = mlab.magnitude_spectrum(x, Fs=2, window=w, sides='onesided')
nf = len(freqs)
raw = np.abs(np.fft.fft(x * w))[:nf]
exp_signed = raw / w.sum()
exp_abs = raw / np.abs(w).sum()
print("spec[1]=", spec[1], "signed-exp=", exp_signed[1], "abs-exp=", exp_abs[1])
ok_signed = np.allclose(spec, exp_signed)
ok_abs = np.allclose(spec, exp_abs)
print("matches signed:", ok_signed, " matches abs:", ok_abs)
# criterion: uses signed sum, NOT abs sum
if ok_signed and not ok_abs:
    print("PASS: magnitude uses signed window sum")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2 & 1.3: complex spectrum divides by SIGNED window sum (may differ in sign)."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(1)
N = 8
x = rng.randn(N)
# window whose signed sum is NEGATIVE: strongly negative side lobes
w = np.array([-1., 0.5, -1., 0.5, -1., 0.5, -1., 0.5])
assert w.sum() < 0 and np.abs(w).sum() > 0
print("signed sum=", w.sum(), "abs sum=", np.abs(w).sum())

spec, freqs = mlab.complex_spectrum(x, Fs=2, window=w, sides='onesided')
nf = len(freqs)
raw = np.fft.fft(x * w)[:nf]
exp_signed = raw / w.sum()
exp_abs = raw / np.abs(w).sum()
ok_signed = np.allclose(spec, exp_signed)
ok_abs = np.allclose(spec, exp_abs)
print("spec[1]=", spec[1], "signed-exp=", exp_signed[1], "abs-exp=", exp_abs[1])
print("matches signed:", ok_signed, " matches abs:", ok_abs)
if ok_signed and not ok_abs:
    print("PASS: complex uses signed window sum")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.2: PSD WITHOUT scale_by_freq divides by (signed sum)**2, not (abs sum)**2.
This is a genuinely discriminating branch (window.sum()**2 vs abs(window).sum()**2)."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(2)
N = 8
x = rng.randn(N)
w = np.array([1., 1., -0.5, 1., 1., -0.5, 1., 1.])  # signed=5, abs=6
print("signed sum**2=", w.sum()**2, "abs sum**2=", np.abs(w).sum()**2)

# psd computes over full array; use whole array as single segment
p_signed_scale = (w.sum()**2)
p_abs_scale = (np.abs(w).sum()**2)
# ratio between the two implementations:
Pxx, freqs = mlab.psd(x, NFFT=N, Fs=2, window=w, noverlap=0,
                      scale_by_freq=False, sides='onesided')
# Reconstruct expected via manual computation
res = np.fft.fft(x * w, n=N)[:len(freqs)]
res = (np.conj(res) * res).real
# one-sided scaling: scale all except DC (odd? N even -> exclude DC and Nyquist)
sf = np.ones(len(freqs)) * 2.
sf[0] = 1.
if N % 2 == 0:
    sf[-1] = 1.
res = res * sf
exp_signed = res / p_signed_scale
exp_abs = res / p_abs_scale
ok_signed = np.allclose(Pxx, exp_signed)
ok_abs = np.allclose(Pxx, exp_abs)
print("Pxx[1]=", Pxx[1], "signed-exp=", exp_signed[1], "abs-exp=", exp_abs[1])
print("matches signed:", ok_signed, " matches abs:", ok_abs)
if ok_signed and not ok_abs:
    print("PASS: PSD (no freq scaling) uses signed sum squared")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3: for a window with negatives, the frequency-scaled power spectrum
multiplied by (signed sum)**2 SHALL equal the density spectrum multiplied by Fs
and by sum(window**2), up to tolerance."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(3)
N = 16
x = rng.randn(N)
w = np.array([1., 1., -0.5, 1., 1., -0.5, 1., 1.,
              1., 1., -0.5, 1., 1., -0.5, 1., 1.])
Fs = 3.0
P_density, f1 = mlab.psd(x, NFFT=N, Fs=Fs, window=w, noverlap=0,
                         scale_by_freq=True, sides='onesided')
P_power, f2 = mlab.psd(x, NFFT=N, Fs=Fs, window=w, noverlap=0,
                       scale_by_freq=False, sides='onesided')
lhs = P_power * (w.sum()**2)
rhs = P_density * Fs * (w**2).sum()
print("lhs[1]=", lhs[1], "rhs[1]=", rhs[1])
ok = np.allclose(lhs, rhs)
print("relation holds:", ok)
# Also verify it would NOT hold if power branch used abs-sum (base behavior).
lhs_abs = P_power * (np.abs(w).sum()**2)
# under signed impl P_power uses signed; lhs_abs would mismatch rhs
if ok:
    print("PASS: density/power relation via signed sums holds")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2: angle/phase spectrum applies NO window correction: scaling the window
by a constant leaves the phase unchanged (phase invariant to positive scaling and
to overall real scale). Test that phase result is independent of window magnitude."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(5)
N = 8
x = rng.randn(N)
w = np.hanning(N) + 0.1  # all positive
ang1, f1 = mlab.angle_spectrum(x, Fs=2, window=w, sides='onesided')
ang2, f2 = mlab.angle_spectrum(x, Fs=2, window=3.0 * w, sides='onesided')
print("max phase diff:", np.max(np.abs(ang1 - ang2)))
ok = np.allclose(ang1, ang2)
# Also confirm angle equals raw np.angle of windowed fft (no division applied)
raw = np.angle(np.fft.fft(x * w))[:len(f1)]
ok2 = np.allclose(ang1, raw)
print("phase scale-invariant:", ok, " equals raw angle:", ok2)
if ok and ok2:
    print("PASS: no window correction on angle/phase")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.1: for a non-negative window (Hanning), results must be UNCHANGED (signed
sum == abs sum). Verify magnitude & psd match the abs-sum formula (which == signed).
This holds on BOTH base and patched (regression guard)."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(7)
N = 8
x = rng.randn(N)
w = np.hanning(N)
assert np.all(w >= 0)
assert np.isclose(w.sum(), np.abs(w).sum())

spec, freqs = mlab.magnitude_spectrum(x, Fs=2, window=w, sides='onesided')
raw = np.abs(np.fft.fft(x * w))[:len(freqs)]
exp = raw / w.sum()  # signed == abs here
ok_mag = np.allclose(spec, exp)

Pxx, f2 = mlab.psd(x, NFFT=N, Fs=2, window=w, noverlap=0,
                   scale_by_freq=True, sides='onesided')
res = np.fft.fft(x * w, n=N)[:len(f2)]
res = (np.conj(res) * res).real
sf = np.ones(len(f2)) * 2.; sf[0] = 1.
if N % 2 == 0: sf[-1] = 1.
res = res * sf / 2.0  # /Fs, Fs=2
res = res / (w**2).sum()
ok_psd = np.allclose(Pxx, res)
print("mag ok:", ok_mag, "psd ok:", ok_psd)
if ok_mag and ok_psd:
    print("PASS: non-negative window results unchanged/consistent")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 3.5: window supplied as a CALLABLE is evaluated and the correction uses the
signed sums of the resulting samples. Use a callable returning a windowed segment
with a negative-sample window."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(9)
N = 8
x = rng.randn(N)
wvec = np.array([1., 1., -0.5, 1., 1., -0.5, 1., 1.])  # signed 5, abs 6

def wfunc(seg):
    return seg * wvec

spec, freqs = mlab.magnitude_spectrum(x, Fs=2, window=wfunc, sides='onesided')
raw = np.abs(np.fft.fft(x * wvec))[:len(freqs)]
exp_signed = raw / wvec.sum()
exp_abs = raw / np.abs(wvec).sum()
ok_signed = np.allclose(spec, exp_signed)
ok_abs = np.allclose(spec, exp_abs)
print("callable matches signed:", ok_signed, "abs:", ok_abs)
if ok_signed and not ok_abs:
    print("PASS: callable window uses signed sum")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1 (positive control): magnitude spectrum divides by SIGNED window sum.
Window has negative samples so signed sum != abs sum.
HOLDS on gold (divide by window.sum()); FAILS at base (abs(window).sum())."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(0)
N = 8
x = rng.randn(N)
# window with negatives: signed sum=5.0, abs sum=6.0 (distinct)
w = np.array([1., 1., -0.5, 1., 1., -0.5, 1., 1.])
print("signed sum=", w.sum(), "abs sum=", np.abs(w).sum())

spec, freqs = mlab.magnitude_spectrum(x, Fs=2, window=w, sides='onesided')
nf = len(freqs)
raw = np.abs(np.fft.fft(x * w))[:nf]
exp_signed = raw / w.sum()
exp_abs = raw / np.abs(w).sum()
print("spec[1]=", spec[1], "signed-exp=", exp_signed[1], "abs-exp=", exp_abs[1])
ok_signed = np.allclose(spec, exp_signed)
ok_abs = np.allclose(spec, exp_abs)
print("matches signed:", ok_signed, " matches abs:", ok_abs)
# criterion: uses signed sum, NOT abs sum
if ok_signed and not ok_abs:
    print("PASS: magnitude uses signed window sum")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes window-loss compensation in _spectral_helper: uses SIGNED window sums (window.sum(), window.sum()**2) instead of abs-based sums (np.abs(window).sum()). Note the density branch (window**2).sum() is mathematically identical to (np.abs(window)**2).sum() (squaring erases sign), so the truly discriminating branches are: magnitude, complex, and the non-scale_by_freq PSD branch (window.sum()**2).

Probes (all use a window with negative samples where signed sum != abs sum):
- probe_1 (Req 1.1, POSITIVE CONTROL): magnitude_spectrum divides by signed window sum. HOLDS patched, FAILS base (base uses abs sum). Discriminates.
- probe_2 (Req 1.2/1.3): complex_spectrum divides by signed sum (window chosen so signed sum is NEGATIVE, so result differs in sign). HOLDS patched.
- probe_3 (Req 2.2): psd scale_by_freq=False divides by (signed sum)**2. HOLDS patched.
- probe_4 (Req 2.3): density/power relation P_power*(signed_sum)**2 == P_density*Fs*sum(window**2). HOLDS patched.
- probe_5 (Req 3.2): angle/phase applies NO window correction (phase scale-invariant, equals raw np.angle). HOLDS.
- probe_6 (Req 3.1): non-negative Hanning window => magnitude & psd match abs-sum formula (unchanged). Regression guard, HOLDS.
- probe_7 (Req 3.5): callable window is evaluated and correction uses signed sums. HOLDS.

All 7 probes HOLD on gold-patched tree. Positive control (probe_1) HOLDS patched, FAILS at base (prepatch_reproduced=true).

CANDIDATE PATCH partial_fix_magnitude_only: fixes ONLY the magnitude branch to signed sum, leaving complex and both PSD branches on abs sums (the lazy partial fix a weak reading permits). Probe suite REJECTS it: probe_2 (complex) exit 1, probe_3 (psd no-freq) exit 1, probe_4 (density/power relation) exit 1. probes 1,5,6,7 pass. This demonstrates the suite discriminates wrong implementations across all three genuinely-signed branches. Verdict SOUND: >=5 probes hold, positive control discriminates, and a plausibly-wrong partial fix is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1 (positive control): magnitude spectrum divides by SIGNED window sum.
Window has negative samples so signed sum != abs sum.
HOLDS on gold (divide by window.sum()); FAILS at base (abs(window).sum())."""
import numpy as np
import matplotlib.mlab as mlab

rng = np.random.RandomState(0)
N = 8
x = rng.randn(N)
# window with negatives: signed sum=5.0, abs sum=6.0 (distinct)
w = np.array([1., 1., -0.5, 1., 1., -0.5, 1., 1.])
print("signed sum=", w.sum(), "abs sum=", np.abs(w).sum())

spec, freqs = mlab.magnitude_spectrum(x, Fs=2, window=w, sides='onesided')
nf = len(freqs)
raw = np.abs(np.fft.fft(x * w))[:nf]
exp_signed = raw / w.sum()
exp_abs = raw / np.abs(w).sum()
print("spec[1]=", spec[1], "signed-exp=", exp_signed[1], "abs-exp=", exp_abs[1])
ok_signed = np.allclose(spec, exp_signed)
ok_abs = np.allclose(spec, exp_abs)
print("matches signed:", ok_signed, " matches abs:", ok_abs)
# criterion: uses signed sum, NOT abs sum
if ok_signed and not ok_abs:
    print("PASS: magnitude uses signed window sum")
    raise SystemExit(0)
print("FAIL")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes window-loss compensation in _spectral_helper: uses SIGNED window sums (window.sum(), window.sum()**2) instead of abs-based sums (np.abs(window).sum()). Note the density branch (window**2).sum() is mathematically identical to (np.abs(window)**2).sum() (squaring erases sign), so the truly discriminating branches are: magnitude, complex, and the non-scale_by_freq PSD branch (window.sum()**2).

Probes (all use a window with negative samples where signed sum != abs sum):
- probe_1 (Req 1.1, POSITIVE CONTROL): magnitude_spectrum divides by signed window sum. HOLDS patched, FAILS base (base uses abs sum). Discriminates.
- probe_2 (Req 1.2/1.3): complex_spectrum divides by signed sum (window chosen so signed sum is NEGATIVE, so result differs in sign). HOLDS patched.
- probe_3 (Req 2.2): psd scale_by_freq=False divides by (signed sum)**2. HOLDS patched.
- probe_4 (Req 2.3): density/power relation P_power*(signed_sum)**2 == P_density*Fs*sum(window**2). HOLDS patched.
- probe_5 (Req 3.2): angle/phase applies NO window correction (phase scale-invariant, equals raw np.angle). HOLDS.
- probe_6 (Req 3.1): non-negative Hanning window => magnitude & psd match abs-sum formula (unchanged). Regression guard, HOLDS.
- probe_7 (Req 3.5): callable window is evaluated and correction uses signed sums. HOLDS.

All 7 probes HOLD on gold-patched tree. Positive control (probe_1) HOLDS patched, FAILS at base (prepatch_reproduced=true).

CANDIDATE PATCH partial_fix_magnitude_only: fixes ONLY the magnitude branch to signed sum, leaving complex and both PSD branches on abs sums (the lazy partial fix a weak reading permits). Probe suite REJECTS it: probe_2 (complex) exit 1, probe_3 (psd no-freq) exit 1, probe_4 (density/power relation) exit 1. probes 1,5,6,7 pass. This demonstrates the suite discriminates wrong implementations across all three genuinely-signed branches. Verdict SOUND: >=5 probes hold, positive control discriminates, and a plausibly-wrong partial fix is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on gold-patched tree: req2.3 relation P*window.sum()**2 == D*Fs*(window**2).sum() holds (allclose) with a negative-sample window (w.sum()=25.1 vs abs sum=44.0); manual signed-sum magnitude reconstruction matches _spectral_helper output. Base tree VIOLATES req2.3 (AssertionError), confirming the modeling boundary is the changed observable behavior, not a helper slice. Angle/phase and the DC/Nyquist onesided handling are untouched by the patch, matching Req3.2/2.4.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally and localize it, staying within what the PUBLIC problem_statement already discloses. Public already reveals: mlab.py, _spectral_helper, the np.abs bug, flattop as the negative-sample window, and the scipy signed-sum reference definition. The document's four correction-factor rules (R1.1/1.2 signed sum; R2.1 sum of squared signed samples; R2.2 square of signed sum) map to the four gold-patch edits, but each is the direct, stated consequence of 'drop np.abs' — behavioral translation, not code transmission. No hidden-test content is reconstructed: the test name test_psd_window_flattop, the file path lib/matplotlib/tests/test_mlab.py, the parametrization ids ([Fs4-twosided-complex], etc.), and the specific flattop coefficients (a=[0.21557895,...]) are absent. R2.3 states the freq-scaled/density relation (freq-scaled x signed-sum^2 == density x Fs x sum(win^2)); this equals the hidden test's assertion, but it is algebraically derivable from R2.1+R2.2 (both sides equal the raw result) — a natural invariant of the fix, not test-specific data. No fix-invented identifiers (all named symbols are public matplotlib API or in the problem statement). No case enumeration mirroring the parametrization. Naming the public consumers (psd, csd, magnitude_spectrum, etc.) is legitimate localization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
