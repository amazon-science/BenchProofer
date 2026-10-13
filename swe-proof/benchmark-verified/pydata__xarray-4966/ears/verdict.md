# P2 adversarial audit — pydata__xarray-4966

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
"""Positive control. Req 1.1 + 1.2: unsigned-kind array flagged _Unsigned="false"
decodes to signed dtype of same width, 8-bit 255 -> -1."""
import sys
import numpy as np
import xarray as xr
from xarray.coding import variables

u = np.dtype("u1")
vals = np.array([255], dtype=u)
enc = xr.Variable(("x",), vals, attrs={"_Unsigned": "false"})
dec = variables.UnsignedIntegerCoder().decode(enc)
print("dtype:", dec.dtype, "values:", np.asarray(dec.values))
ok = dec.dtype == np.dtype("i1") and int(np.asarray(dec.values)[0]) == -1
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2 + 1.3: exact two's-complement mapping across all widths 1,2,4,8.
For each width: max -> -1, 2**(bits-1) -> -2**(bits-1), 2**(bits-1)-1 stays."""
import sys
import numpy as np
import xarray as xr
from xarray.coding import variables

ok = True
for bits in (1, 2, 4, 8):
    u = np.dtype("u%d" % bits)
    s = np.dtype("i%d" % bits)
    b = bits * 8
    half = 1 << (b - 1)
    cases = {int(np.iinfo(u).max): -1, half: -half, half - 1: half - 1}
    for x, expect in cases.items():
        vals = np.array([x], dtype=u)
        enc = xr.Variable(("x",), vals, attrs={"_Unsigned": "false"})
        dec = variables.UnsignedIntegerCoder().decode(enc)
        got = int(np.asarray(dec.values)[0])
        good = dec.dtype == s and got == expect
        print(f"bits={bits} x={x} -> {got} (expect {expect}) dtype={dec.dtype} {'ok' if good else 'BAD'}")
        ok = ok and good
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.4 + 1.5: _FillValue converted to signed dtype width-preserving,
and NO 'not of integer type' warning emitted for the u/false case."""
import sys, warnings
import numpy as np
import xarray as xr
from xarray.coding import variables
from xarray.core.variable import Variable

u = np.dtype("u1")
vals = np.array([255, 1], dtype=u)
enc = xr.Variable(("x",), vals, attrs={"_Unsigned": "false", "_FillValue": u.type(255)})
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    dec = variables.UnsignedIntegerCoder().decode(enc)
fv = dec.attrs["_FillValue"]
print("fill:", fv, "fill_dtype:", np.dtype(type(fv)) if not hasattr(fv,'dtype') else fv.dtype)
fv_dtype = fv.dtype if hasattr(fv, "dtype") else np.dtype(type(fv))
fv_ok = fv_dtype == np.dtype("i1") and int(fv) == -1
warned = any("not of integer type" in str(x.message) for x in w)
print("fill_ok:", fv_ok, "warned:", warned)
ok = fv_ok and not warned
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2 regression: signed-typed array flagged _Unsigned="true" decodes to
unsigned dtype same width across all widths; -1 -> max. Also fillvalue converts."""
import sys
import numpy as np
import xarray as xr
from xarray.coding import variables

ok = True
for bits in (1, 2, 4, 8):
    u = np.dtype("u%d" % bits)
    s = np.dtype("i%d" % bits)
    vals = np.array([-1], dtype=s)
    enc = xr.Variable(("x",), vals, attrs={"_Unsigned": "true", "_FillValue": s.type(-1)})
    dec = variables.UnsignedIntegerCoder().decode(enc)
    got = int(np.asarray(dec.values)[0])
    fv = dec.attrs["_FillValue"]
    fv_dtype = fv.dtype if hasattr(fv, "dtype") else np.dtype(type(fv))
    good = dec.dtype == u and got == int(np.iinfo(u).max) and fv_dtype == u
    print(f"bits={bits} -> {got} dtype={dec.dtype} fill_dtype={fv_dtype} {'ok' if good else 'BAD'}")
    ok = ok and good
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3: leave unaffected inputs unchanged.
3.1 signed dtype, _Unsigned != true -> unchanged.
3.2 unsigned dtype, _Unsigned != false -> unchanged.
3.3 non-integer dtype with _Unsigned -> unchanged + warning.
3.4 no _Unsigned -> unchanged.
3.5 _Unsigned moved from attrs to encoding.
"""
import sys, warnings
import numpy as np
import xarray as xr
from xarray.coding import variables

ok = True

# 3.1 signed with _Unsigned="false" (not "true") -> unchanged
v = xr.Variable(("x",), np.array([-1, 5], dtype="i1"), attrs={"_Unsigned": "false"})
d = variables.UnsignedIntegerCoder().decode(v)
c = d.dtype == np.dtype("i1") and list(np.asarray(d.values)) == [-1, 5]
print("3.1 signed/false unchanged:", c, d.dtype)
ok = ok and c

# 3.2 unsigned with _Unsigned="true" (not "false") -> unchanged
v = xr.Variable(("x",), np.array([255, 5], dtype="u1"), attrs={"_Unsigned": "true"})
d = variables.UnsignedIntegerCoder().decode(v)
c = d.dtype == np.dtype("u1") and list(np.asarray(d.values)) == [255, 5]
print("3.2 unsigned/true unchanged:", c, d.dtype)
ok = ok and c

# 3.3 float dtype with _Unsigned -> unchanged + warning
v = xr.Variable(("x",), np.array([1.5, 2.5], dtype="f4"), attrs={"_Unsigned": "false"})
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    d = variables.UnsignedIntegerCoder().decode(v, name="test")
warned = any("not of integer type" in str(x.message) for x in w)
c = d.dtype == np.dtype("f4") and warned
print("3.3 float unchanged+warn:", c, "warned:", warned)
ok = ok and c

# 3.4 no _Unsigned -> unchanged, no _Unsigned in encoding
v = xr.Variable(("x",), np.array([255, 5], dtype="u1"), attrs={"foo": "bar"})
d = variables.UnsignedIntegerCoder().decode(v)
c = d.dtype == np.dtype("u1") and list(np.asarray(d.values)) == [255, 5] and d.attrs.get("foo") == "bar"
print("3.4 no _Unsigned unchanged:", c)
ok = ok and c

# 3.5 _Unsigned moved to encoding, not in attrs
v = xr.Variable(("x",), np.array([255], dtype="u1"), attrs={"_Unsigned": "false", "keep": 1})
d = variables.UnsignedIntegerCoder().decode(v)
c = ("_Unsigned" not in d.attrs) and d.encoding.get("_Unsigned") == "false" and d.attrs.get("keep") == 1
print("3.5 moved to encoding:", c, "attrs:", dict(d.attrs), "enc:", dict(d.encoding))
ok = ok and c

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.1: encode direction preserved. encoding _Unsigned="true" on unsigned
array -> signed dtype same width, fill converted, _Unsigned moved encoding->attrs."""
import sys
import numpy as np
import xarray as xr
from xarray.coding import variables

u = np.dtype("u1")
vals = np.array([255, 1], dtype=u)  # 255 -> -1 under signed
v = xr.Variable(("x",), vals, attrs={"_FillValue": u.type(255)}, encoding={"_Unsigned": "true"})
e = variables.UnsignedIntegerCoder().encode(v)
got = list(np.asarray(e.values))
fv = e.attrs.get("_FillValue")
fv_dtype = fv.dtype if hasattr(fv, "dtype") else np.dtype(type(fv))
print("enc dtype:", e.dtype, "values:", got, "fill:", fv, fv_dtype)
print("attrs _Unsigned:", e.attrs.get("_Unsigned"), "enc has:", "_Unsigned" in e.encoding)
ok = (e.dtype == np.dtype("i1") and got == [-1, 1]
      and e.attrs.get("_Unsigned") == "true" and "_Unsigned" not in e.encoding
      and fv_dtype == np.dtype("i1") and int(fv) == -1)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req 1.1 + 1.2: unsigned-kind array flagged _Unsigned="false"
decodes to signed dtype of same width, 8-bit 255 -> -1."""
import sys
import numpy as np
import xarray as xr
from xarray.coding import variables

u = np.dtype("u1")
vals = np.array([255], dtype=u)
enc = xr.Variable(("x",), vals, attrs={"_Unsigned": "false"})
dec = variables.UnsignedIntegerCoder().decode(enc)
print("dtype:", dec.dtype, "values:", np.asarray(dec.values))
ok = dec.dtype == np.dtype("i1") and int(np.asarray(dec.values)[0]) == -1
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Six distinct probes covering all requirements, all HOLD on the gold-patched tree:
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): u1 array _Unsigned=false decodes to int8, 255->-1. HOLDS patched, FAILS at base (base returns uint8 255 + 'not of integer type' warning). Discriminates.
- probe_2 (Req 1.2/1.3): exact two's-complement mapping across widths 1,2,4,8 (max->-1, half->-half, half-1 unchanged), correct signed dtype each width. HOLDS.
- probe_3 (Req 1.4/1.5): _FillValue converted to matching signed dtype (255->-1 int8) AND no serialization warning for u/false case. HOLDS.
- probe_4 (Req 2, regression): signed _Unsigned=true -> unsigned same width all widths, -1->max, fillvalue converted. HOLDS.
- probe_5 (Req 3.1-3.5): unaffected inputs unchanged (signed/false, unsigned/true, float+warning, no-_Unsigned), and _Unsigned moved attrs->encoding leaving other attrs intact. HOLDS.
- probe_6 (Req 4.1): encode direction unchanged (u1 _Unsigned=true encoding -> int8 255->-1, fill converted, marker moved encoding->attrs). HOLDS.

CANDIDATE PATCH (weak.diff): a partial 'lazy fix' handling only itemsize==1 for the u/false branch. It satisfies probe_1 and probe_5 (naively conforms to Req 1 for the byte case + leaves others unchanged) but is REJECTED by probe_2 (widths 2/4/8 not reinterpreted) — matching the hidden FAIL_TO_PASS test_decode_signed_from_unsigned[2],[4],[8]. This demonstrates the suite discriminates wrong/partial implementations across the mandated widths. No requirements-conforming patch found that would fail the harness; suite is discriminating and complete.

Verdict SOUND: >=5 probes all hold on patched tree; positive control holds patched and fails at base; >=1 candidate exercised and REJECTED.

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
"""Positive control. Req 1.1 + 1.2: unsigned-kind array flagged _Unsigned="false"
decodes to signed dtype of same width, 8-bit 255 -> -1."""
import sys
import numpy as np
import xarray as xr
from xarray.coding import variables

u = np.dtype("u1")
vals = np.array([255], dtype=u)
enc = xr.Variable(("x",), vals, attrs={"_Unsigned": "false"})
dec = variables.UnsignedIntegerCoder().decode(enc)
print("dtype:", dec.dtype, "values:", np.asarray(dec.values))
ok = dec.dtype == np.dtype("i1") and int(np.asarray(dec.values)[0]) == -1
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Six distinct probes covering all requirements, all HOLD on the gold-patched tree:
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): u1 array _Unsigned=false decodes to int8, 255->-1. HOLDS patched, FAILS at base (base returns uint8 255 + 'not of integer type' warning). Discriminates.
- probe_2 (Req 1.2/1.3): exact two's-complement mapping across widths 1,2,4,8 (max->-1, half->-half, half-1 unchanged), correct signed dtype each width. HOLDS.
- probe_3 (Req 1.4/1.5): _FillValue converted to matching signed dtype (255->-1 int8) AND no serialization warning for u/false case. HOLDS.
- probe_4 (Req 2, regression): signed _Unsigned=true -> unsigned same width all widths, -1->max, fillvalue converted. HOLDS.
- probe_5 (Req 3.1-3.5): unaffected inputs unchanged (signed/false, unsigned/true, float+warning, no-_Unsigned), and _Unsigned moved attrs->encoding leaving other attrs intact. HOLDS.
- probe_6 (Req 4.1): encode direction unchanged (u1 _Unsigned=true encoding -> int8 255->-1, fill converted, marker moved encoding->attrs). HOLDS.

CANDIDATE PATCH (weak.diff): a partial 'lazy fix' handling only itemsize==1 for the u/false branch. It satisfies probe_1 and probe_5 (naively conforms to Req 1 for the byte case + leaves others unchanged) but is REJECTED by probe_2 (widths 2/4/8 not reinterpreted) — matching the hidden FAIL_TO_PASS test_decode_signed_from_unsigned[2],[4],[8]. This demonstrates the suite discriminates wrong/partial implementations across the mandated widths. No requirements-conforming patch found that would fail the harness; suite is discriminating and complete.

Verdict SOUND: >=5 probes all hold on patched tree; positive control holds patched and fails at base; >=1 candidate exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds a single elif branch (data.dtype.kind=="u" and unsigned=="false") mirroring the pre-existing kind=="i"/"true" branch, computing signed_dtype=np.dtype('i%s'%itemsize) via lazy_elemwise_func(np.asarray) plus _FillValue conversion. Requirements 1-4 describe precisely this and the surrounding unchanged behavior. The two's-complement description in R1.2/R2.2 is a correct mathematical characterization of np.asarray dtype reinterpretation of the same bit pattern. Probe exit=0, ALL OK.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable entirely from the public problem_statement, which already links to variables.py L311 and names the `if .kind == "u" and unsigned == False` fix location, and shows the concrete example (values decoding to -128, -1, ..., 127 vs 128, 255). Naming UnsignedIntegerCoder.decode/encode and variables.py legitimately localizes the change. The byte-width set (1,2,4,8) is the natural complete set of numpy integer widths and follows from the two's-complement description, not a test artifact (the tests only exercise max-value / -1, not the full 128->-128, 127->127 illustrations given here). The worked examples (255->-1, 128->-128, 127->127) are a general spec of two's-complement, broader than and not mirroring the parametrized cases. No leakage of test names (test_decode_signed_from_unsigned / test_decode_unsigned_from_signed), file paths (xarray/tests/test_coding.py), parametrization ids, quoted test/gold code, or fix-invented identifiers (signed_dtype, transform, lazy_elemwise_func). The parametrization ids [1,2,4,8] happen to equal itemsize widths but the requirement expresses byte widths behaviorally, not as test ids.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
