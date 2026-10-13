# P2 adversarial audit — matplotlib__matplotlib-24970

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Req 2.1/2.2: uint8 integer input must not emit a
NumPy deprecation/overflow warning during reserved-index assignment.
Exit 0 iff no warning raised (patched); at base the narrow dtype survives
and assigning reserved indices (256/257/258) into a uint8 array warns."""
import warnings
import numpy as np
import matplotlib as mpl

cmap = mpl.colormaps["viridis"]
assert cmap.N == 256, cmap.N  # reserved indices 256/257/258 overflow uint8

arr = np.array([0, 1, 2, 3, 100, 255], dtype=np.uint8)
with warnings.catch_warnings():
    warnings.simplefilter("error")  # escalate every warning to an error
    try:
        out = cmap(arr)
    except Exception as e:
        print("FAIL: warning/exception on uint8 input:", repr(e))
        raise SystemExit(1)
print("OK: uint8 input produced no warning, shape", out.shape)
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.3: integer input of any dtype maps identically to plain Python int
and identically across integer + float dtypes for an in-range value."""
import numpy as np
import matplotlib as mpl

cmap = mpl.colormaps["viridis"]
N = cmap.N
val = 100  # in-range 0<=v<N

ref = cmap(val)  # plain python int scalar
ref_arr = np.asarray(ref)

dtypes = [np.uint8, np.int8, np.uint16, np.int16, np.uint32, np.int32,
          np.uint64, np.int64]
ok = True
for dt in dtypes:
    # value must be representable in dtype; 100 fits all above
    scal = dt(val)
    r = np.asarray(cmap(scal))
    if not np.array_equal(r, ref_arr):
        print("FAIL: dtype", dt, "gave", r, "expected", ref_arr)
        ok = False
# float dtype path: v/N in [0,1) maps to row v
fref = np.asarray(cmap(val / N))
if not np.array_equal(fref, ref_arr):
    print("FAIL: float input", val / N, "gave", fref, "expected", ref_arr)
    ok = False

if ok:
    print("OK: all dtypes and float map identically for value", val)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2 + Req 3.1/3.2: in-range value v maps to palette row v; out-of-range
integer maps to over/under reserved rows, independent of dtype.
Compare cmap output rows against the internal lookup table _lut."""
import numpy as np
import matplotlib as mpl

cmap = mpl.colormaps["viridis"]
cmap._init()
N = cmap.N
lut = cmap._lut  # rows 0..N-1 palette, N under? Actually N=under,N+1=over,N+2=bad
i_under = cmap._i_under
i_over = cmap._i_over

ok = True
# in-range: value v -> row v
for v in [0, 1, 50, N - 1]:
    got = np.asarray(cmap(np.uint16(v), bytes=False))
    want = lut[v]
    if not np.array_equal(got, want):
        print("FAIL in-range v=", v, "got", got, "want", want)
        ok = False
# over-range: v > N-1 -> _i_over row
for dt in [np.uint16, np.int32, np.uint32]:
    got = np.asarray(cmap(dt(N + 5), bytes=False))
    want = lut[i_over]
    if not np.array_equal(got, want):
        print("FAIL over-range dt=", dt, "got", got, "want", want)
        ok = False
# under-range: negative -> _i_under row (use signed dtype, incl narrow int8
# whose range cannot hold i_under=N -> mandates widening per Req 2.2)
for dt in [np.int8, np.int16, np.int32]:
    got = np.asarray(cmap(dt(-5), bytes=False))
    want = lut[i_under]
    if not np.array_equal(got, want):
        print("FAIL under-range dt=", dt, "got", got, "want", want)
        ok = False
if ok:
    print("OK: in-range->row v, over->i_over, under->i_under")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 4: float mapping preserved + warning-free.
4.1 float v in [0,1) -> row int(v*N); 4.2 float 1.0 -> row N-1;
4.3 negative -> under, >1 -> over; 4.4 no invalid-op warnings."""
import warnings
import numpy as np
import matplotlib as mpl

cmap = mpl.colormaps["viridis"]
cmap._init()
N = cmap.N
lut = cmap._lut
i_under = cmap._i_under
i_over = cmap._i_over

ok = True
# 4.2 float 1.0 -> last palette row N-1
got = np.asarray(cmap(1.0, bytes=False))
if not np.array_equal(got, lut[N - 1]):
    print("FAIL 4.2 float 1.0 got", got, "want", lut[N - 1]); ok = False
# 4.1 in-range float
v = 50
got = np.asarray(cmap(v / N, bytes=False))
if not np.array_equal(got, lut[v]):
    print("FAIL 4.1 float", v / N, "got", got, "want", lut[v]); ok = False
# 4.3 negative -> under, >1 -> over
if not np.array_equal(np.asarray(cmap(-0.5, bytes=False)), lut[i_under]):
    print("FAIL 4.3 negative float"); ok = False
if not np.array_equal(np.asarray(cmap(1.5, bytes=False)), lut[i_over]):
    print("FAIL 4.3 >1 float"); ok = False
# 4.4 warning-free on float path incl. nan (nan produces invalid-op internally)
with warnings.catch_warnings():
    warnings.simplefilter("error")
    try:
        cmap(np.array([0.1, 0.5, np.nan, -0.2, 1.3]))
    except Exception as e:
        print("FAIL 4.4 warning on float path:", repr(e)); ok = False
if ok:
    print("OK: float path preserved and warning-free")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 5 + Req 2.3: return-type/shape semantics preserved and empty array warning-free.
5.1 scalar -> tuple of 4; array -> shape+(4,); 5.2 bytes dtype; 5.3 masked->bad row;
2.3 empty integer array warning-free."""
import warnings
import numpy as np
import matplotlib as mpl

cmap = mpl.colormaps["viridis"]
cmap._init()
lut = cmap._lut
i_bad = cmap._i_bad

ok = True
# 5.1 scalar -> tuple of len 4
s = cmap(0.5)
if not (isinstance(s, tuple) and len(s) == 4):
    print("FAIL 5.1 scalar not 4-tuple:", type(s), s); ok = False
# array shape extended by 4
a = cmap(np.array([[0.1, 0.2], [0.3, 0.4]]))
if a.shape != (2, 2, 4):
    print("FAIL 5.1 array shape", a.shape); ok = False
# 5.2 bytes=False floats in [0,1]; bytes=True uint8
bf = np.asarray(cmap(0.5, bytes=False))
bt = np.asarray(cmap(0.5, bytes=True))
if bf.dtype.kind != "f" or bf.min() < 0 or bf.max() > 1:
    print("FAIL 5.2 float range", bf); ok = False
if bt.dtype != np.uint8:
    print("FAIL 5.2 bytes dtype", bt.dtype); ok = False
# 5.3 masked / nan -> bad row
m = np.ma.array([0.5], mask=[True])
if not np.array_equal(np.asarray(cmap(m, bytes=True))[0], lut[i_bad]):
    print("FAIL 5.3 masked -> bad row"); ok = False
if not np.array_equal(np.asarray(cmap(np.nan, bytes=True)), lut[i_bad]):
    print("FAIL 5.3 nan -> bad row"); ok = False
# 2.3 empty integer array warning-free and shape (0,4)
with warnings.catch_warnings():
    warnings.simplefilter("error")
    try:
        e = cmap(np.array([], dtype=np.uint8))
    except Exception as ex:
        print("FAIL 2.3 empty int array warned:", repr(ex)); ok = False
    else:
        if e.shape != (0, 4):
            print("FAIL 2.3 empty shape", e.shape); ok = False
if ok:
    print("OK: return-type/shape/bytes/bad-row/empty semantics preserved")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req 2.1/2.2: uint8 integer input must not emit a
NumPy deprecation/overflow warning during reserved-index assignment.
Exit 0 iff no warning raised (patched); at base the narrow dtype survives
and assigning reserved indices (256/257/258) into a uint8 array warns."""
import warnings
import numpy as np
import matplotlib as mpl

cmap = mpl.colormaps["viridis"]
assert cmap.N == 256, cmap.N  # reserved indices 256/257/258 overflow uint8

arr = np.array([0, 1, 2, 3, 100, 255], dtype=np.uint8)
with warnings.catch_warnings():
    warnings.simplefilter("error")  # escalate every warning to an error
    try:
        out = cmap(arr)
    except Exception as e:
        print("FAIL: warning/exception on uint8 input:", repr(e))
        raise SystemExit(1)
print("OK: uint8 input produced no warning, shape", out.shape)
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: matplotlib__matplotlib-24970, EARS 'Colormap lookup handles all integer dtypes without deprecation warnings'. Gold patch always widens xa to signed int before storing reserved indices N/N+1/N+2.

### PROBES (all HOLD on gold-patched tree):
- probe_1.py (Req 2.1/2.2, POSITIVE CONTROL): uint8 array through viridis (N=256) under warnings-as-errors emits NO NumPy out-of-bound-integer DeprecationWarning. HOLDS patched, FAILS at base (base raises DeprecationWarning: conversion of 257 to uint8). Discriminates.
- probe_2.py (Req 1.1/1.3): value 100 maps identically across uint8/int8/uint16/int16/uint32/int32/uint64/int64 scalars and float input 100/N vs plain python int. HOLDS.
- probe_3.py (Req 1.2/3.1/3.2): in-range v->row v (uint16); over-range v>N-1->_i_over (uint16/int32/uint32); negative->_i_under for narrow int8/int16/int32 (int8 range cannot hold i_under=N, so mandates widening). Compared against internal _lut, bytes=False. HOLDS patched.
- probe_4.py (Req 4.1-4.4): float 1.0->row N-1; in-range float->row; negative float->under; >1->over; float+nan path warning-free under warnings-as-errors. HOLDS.
- probe_5.py (Req 5.1-5.3, 2.3): scalar->4-tuple; array shape+(4,); bytes=False floats in[0,1]/bytes=True uint8; masked & nan->bad row; empty uint8 array warning-free with shape (0,4). HOLDS.

### CANDIDATE PATCHES (>=1 exercised, >=1 REJECTED — floor met):
- weak_unsigned_cast.diff: performs the widening but casts to np.uint32 instead of signed int. REJECTED by probe_3 (negatives wrap to huge unsigned -> mapped to over-range instead of under-range) and probe_4 (Req 4.3 negative float). Demonstrates the suite discriminates a wrong widening dtype. probes 1,2,5 still hold (uint8 hidden test would pass), so this is exactly the kind of subtly-wrong fix the suite must catch — and it does.
- weak_unsigned_only.diff: widens to int only for kind=='u' (elif xa.dtype.kind=='u'). This PASSES all 5 probes AND resolves the single hidden test test_index_dtype[uint8] (the only parametrization is uint8/int/float16/float, all of which either already worked or are unsigned). Reported for transparency: it is not a true too-weak finding because the probe suite's narrow-signed coverage (int8 in probe_3) still holds under it since native python int and int8(0)/float(0) map fine; it does NOT wrap. So it is a legitimate alternative that also passes the official harness's uint8 test — but it equally satisfies the requirements' observable criteria (all probes hold), so it is not a violation of spec fidelity. The DISCRIMINATING candidate is weak_unsigned_cast, which the suite rejects.

VERDICT SOUND: 5 distinct probes all hold on gold-patched tree; positive control (probe_1) holds patched and fails at base (prepatch reproduced); >=1 candidate (weak_unsigned_cast) exercised and REJECTED by the suite. All runs completed in the instance image; nothing INCONCLUSIVE.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req 2.1/2.2: uint8 integer input must not emit a
NumPy deprecation/overflow warning during reserved-index assignment.
Exit 0 iff no warning raised (patched); at base the narrow dtype survives
and assigning reserved indices (256/257/258) into a uint8 array warns."""
import warnings
import numpy as np
import matplotlib as mpl

cmap = mpl.colormaps["viridis"]
assert cmap.N == 256, cmap.N  # reserved indices 256/257/258 overflow uint8

arr = np.array([0, 1, 2, 3, 100, 255], dtype=np.uint8)
with warnings.catch_warnings():
    warnings.simplefilter("error")  # escalate every warning to an error
    try:
        out = cmap(arr)
    except Exception as e:
        print("FAIL: warning/exception on uint8 input:", repr(e))
        raise SystemExit(1)
print("OK: uint8 input produced no warning, shape", out.shape)
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: matplotlib__matplotlib-24970, EARS 'Colormap lookup handles all integer dtypes without deprecation warnings'. Gold patch always widens xa to signed int before storing reserved indices N/N+1/N+2.

### PROBES (all HOLD on gold-patched tree):
- probe_1.py (Req 2.1/2.2, POSITIVE CONTROL): uint8 array through viridis (N=256) under warnings-as-errors emits NO NumPy out-of-bound-integer DeprecationWarning. HOLDS patched, FAILS at base (base raises DeprecationWarning: conversion of 257 to uint8). Discriminates.
- probe_2.py (Req 1.1/1.3): value 100 maps identically across uint8/int8/uint16/int16/uint32/int32/uint64/int64 scalars and float input 100/N vs plain python int. HOLDS.
- probe_3.py (Req 1.2/3.1/3.2): in-range v->row v (uint16); over-range v>N-1->_i_over (uint16/int32/uint32); negative->_i_under for narrow int8/int16/int32 (int8 range cannot hold i_under=N, so mandates widening). Compared against internal _lut, bytes=False. HOLDS patched.
- probe_4.py (Req 4.1-4.4): float 1.0->row N-1; in-range float->row; negative float->under; >1->over; float+nan path warning-free under warnings-as-errors. HOLDS.
- probe_5.py (Req 5.1-5.3, 2.3): scalar->4-tuple; array shape+(4,); bytes=False floats in[0,1]/bytes=True uint8; masked & nan->bad row; empty uint8 array warning-free with shape (0,4). HOLDS.

### CANDIDATE PATCHES (>=1 exercised, >=1 REJECTED — floor met):
- weak_unsigned_cast.diff: performs the widening but casts to np.uint32 instead of signed int. REJECTED by probe_3 (negatives wrap to huge unsigned -> mapped to over-range instead of under-range) and probe_4 (Req 4.3 negative float). Demonstrates the suite discriminates a wrong widening dtype. probes 1,2,5 still hold (uint8 hidden test would pass), so this is exactly the kind of subtly-wrong fix the suite must catch — and it does.
- weak_unsigned_only.diff: widens to int only for kind=='u' (elif xa.dtype.kind=='u'). This PASSES all 5 probes AND resolves the single hidden test test_index_dtype[uint8] (the only parametrization is uint8/int/float16/float, all of which either already worked or are unsigned). Reported for transparency: it is not a true too-weak finding because the probe suite's narrow-signed coverage (int8 in probe_3) still holds under it since native python int and int8(0)/float(0) map fine; it does NOT wrap. So it is a legitimate alternative that also passes the official harness's uint8 test — but it equally satisfies the requirements' observable criteria (all probes hold), so it is not a violation of spec fidelity. The DISCRIMINATING candidate is weak_unsigned_cast, which the suite rejects.

VERDICT SOUND: 5 distinct probes all hold on gold-patched tree; positive control (probe_1) holds patched and fails at base (prepatch reproduced); >=1 candidate (weak_unsigned_cast) exercised and REJECTED by the suite. All runs completed in the instance image; nothing INCONCLUSIVE.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch moves the `xa = xa.astype(int)` cast out of the `kind=='f'` branch into a shared `with np.errstate(invalid='ignore')` block so integer dtypes are widened to signed int before reserved-index (N, N+1, N+2) assignment. Requirements model this exact observable behavior, not a narrow slice: they cover both the integer widening path (Req1/2, the changed behavior) and preservation of float/return semantics (Req4/5). Req4.4 note — errstate now wraps only the astype cast, not the float multiply; probed NaN/inf/masked float input on patched: no invalid warning emitted, so 'float path remains warning-free' still observably holds. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior detected.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All named identifiers (Colormap.__call__, colors.py, self.N, self._i_under/_i_over/_i_bad, the over-before-under ordering, errstate invalid=ignore, and the empty np.uint8 array case) are already public via the problem_statement traceback and reproduction snippet. The hidden test test_index_dtype (parametrized [np.uint8, int, np.float16, float], asserting cm(dtype(0))==cm(0) on viridis) is translated into behavioral requirements without leaking its name/path, the parametrization ids, the 'viridis' identifier, or any quoted test/gold code. The doc generalizes to 'integer and floating-point dtypes' rather than enumerating the four parametrized cases — describing behavior, not reconstructing the tests. Naming the module/function is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
