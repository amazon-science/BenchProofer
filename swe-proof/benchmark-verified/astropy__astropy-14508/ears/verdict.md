# P2 adversarial audit — astropy__astropy-14508

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
"""Req1.3 (positive control): HIERARCH card with value 0.009125 renders value
field exactly as 0.009125, not an expanded form."""
import sys
from astropy.io.fits.card import Card

c = Card("HIERARCH ABC DEF GH IJKLMN", 0.009125, "Comment")
img = str(c)
print("card image:", repr(img))
if "0.009124999999999999" in img:
    print("FAIL: expanded form present")
    sys.exit(1)
if "0.009125" not in img:
    print("FAIL: shortest value form absent")
    sys.exit(1)
print("OK: value rendered as 0.009125")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1/1.2/1.4: _format_float derives from shortest str/repr form. For values
with short reprs, it returns them exactly (no trailing-digit expansion)."""
import sys
from astropy.io.fits.card import _format_float

cases = {
    0.009125: "0.009125",
    8.95: "8.95",
    -99.9: "-99.9",
    0.1: "0.1",
    -0.5: "-0.5",
}
ok = True
for v, expected in cases.items():
    got = _format_float(v)
    print(f"_format_float({v!r}) = {got!r}  expected {expected!r}")
    if got != expected:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3/2.4: FITS-legal formatting. Every formatted float contains
'.' or 'E'; exponent marker is upper-case E; whole numbers keep decimal;
scientific notation reproduces the value with upper-case E."""
import sys
from astropy.io.fits.card import _format_float

ok = True

# 2.1 + 2.3: whole number keeps decimal, has '.' or 'E'
for v in [1.0, 2.0, -3.0, 100.0]:
    got = _format_float(v)
    print(f"_format_float({v!r}) = {got!r}")
    if "." not in got and "E" not in got:
        print("  FAIL: no decimal point or exponent")
        ok = False

# 2.2 + 2.4: scientific notation upper-case E, no lower-case e, round-trips
for v in [1e32, 1e-32, 1.5e-40, -2.7e50]:
    got = _format_float(v)
    print(f"_format_float({v!r}) = {got!r}")
    if "e" in got:
        print("  FAIL: lower-case e present")
        ok = False
    if "E" not in got:
        print("  FAIL: expected exponent marker E")
        ok = False
    else:
        if float(got) != v:
            print(f"  FAIL: does not round-trip ({float(got)!r} != {v!r})")
            ok = False

sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2/3.3: 20-char length cap. No-E long strings truncated to first 20
chars; E-containing long strings keep the exponent suffix and are exactly 20;
every finite float returns <= 20 chars."""
import sys
from astropy.io.fits.card import _format_float

ok = True

# 3.1: long, no exponent -> first 20 chars
v = 0.00012345678901234567
got = _format_float(v)
s = str(v)
print(f"no-E: str={s!r} (len {len(s)}) -> {got!r} (len {len(got)})")
if "E" not in got:
    if got != s[:20]:
        print("  FAIL: not first-20-char truncation")
        ok = False
    if len(got) != 20:
        print("  FAIL: expected length 20")
        ok = False
else:
    print("  NOTE: value unexpectedly has E; skipping no-E check")

# 3.2: long, exponent -> keep suffix, exactly 20 chars
v = 1.2345678901234567e+300
got = _format_float(v)
s = str(v).replace("e", "E")
print(f"E: str={s!r} (len {len(s)}) -> {got!r} (len {len(got)})")
idx = s.find("E")
suffix = s[idx:]
if len(got) != 20:
    print("  FAIL: expected exactly 20 chars")
    ok = False
if not got.endswith(suffix):
    print(f"  FAIL: exponent suffix {suffix!r} not preserved")
    ok = False

# 3.3: every finite float <= 20 chars
for v in [0.009125, 8.95, -99.9, 1.0, 1e32, 1e-32,
          1.2345678901234567e+300, 1.2345678901234568e+16,
          0.00012345678901234567, -1.2345678901234567e-250]:
    got = _format_float(v)
    if len(got) > 20:
        print(f"  FAIL: {v!r} -> {got!r} len {len(got)} > 20")
        ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4.1/4.2: complex values formatted via same float helper into parenthesized
form; non-finite floats (inf, -inf, nan) render without error via established
forms."""
import sys
import math
from astropy.io.fits.card import _format_value, _format_float

ok = True

# 4.1: complex -> parenthesized, parts use _format_float
z = complex(0.009125, 8.95)
got = _format_value(z).strip()
print(f"_format_value({z!r}) = {got!r}")
if not (got.startswith("(") and got.endswith(")")):
    print("  FAIL: not parenthesized")
    ok = False
if _format_float(0.009125) not in got or _format_float(8.95) not in got:
    print("  FAIL: parts not formatted via _format_float")
    ok = False

# 4.2: non-finite floats render without error
for v in [float("inf"), float("-inf"), float("nan")]:
    try:
        got = _format_float(v)
        print(f"_format_float({v!r}) = {got!r}")
    except Exception as e:
        print(f"  FAIL: raised {e!r}")
        ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.3/4.4/4.5: full-card behavior. A HIERARCH keyword + 0.009125 + comment
fits without truncation warning and preserves comment; round-trip re-create
renders 0.009125; ordinary/negative/scientific float cards render unchanged."""
import sys
import warnings
from astropy.io.fits.card import Card

ok = True

# 4.3 + 4.4: no truncation warning, comment preserved, value 0.009125
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    c = Card("HIERARCH ESO IFM CL RADIUS", 0.009125, "[m] radius arround actuator to avoid")
    img = str(c)
    print("image:", repr(img))
    trunc = [x for x in w if "too long" in str(x.message).lower()
             or "truncat" in str(x.message).lower()]
    if trunc:
        print("  FAIL: truncation warning emitted:", [str(x.message) for x in trunc])
        ok = False
if "0.009125" not in img:
    print("  FAIL: value not 0.009125")
    ok = False
if "[m] radius arround actuator to avoid" not in img:
    print("  FAIL: comment truncated")
    ok = False

# round-trip: re-parse image, re-create card
c2 = Card.fromstring(img)
print("roundtrip value:", repr(c2.value), "comment:", repr(c2.comment))
if c2.value != 0.009125:
    print("  FAIL: roundtrip value changed")
    ok = False

# 4.5: ordinary float cards render as expected
for kw, val, expect_val in [("FOO", 1.0, "1.0"),
                            ("BAR", -99.9, "-99.9"),
                            ("BAZ", 1e32, "1E+32")]:
    c = Card(kw, val)
    img = str(c)
    print(f"{kw}={val!r} -> {img[:40]!r}")
    if expect_val not in img:
        print(f"  FAIL: expected {expect_val!r} in image")
        ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.3 (positive control): HIERARCH card with value 0.009125 renders value
field exactly as 0.009125, not an expanded form."""
import sys
from astropy.io.fits.card import Card

c = Card("HIERARCH ABC DEF GH IJKLMN", 0.009125, "Comment")
img = str(c)
print("card image:", repr(img))
if "0.009124999999999999" in img:
    print("FAIL: expanded form present")
    sys.exit(1)
if "0.009125" not in img:
    print("FAIL: shortest value form absent")
    sys.exit(1)
print("OK: value rendered as 0.009125")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover _format_float in astropy/io/fits/card.py: render floats from shortest str/repr form (Req1), preserve FITS-legal formatting (Req2), enforce 20-char cap (Req3), keep existing behaviors incl. complex/non-finite/roundtrip (Req4).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.3, POSITIVE CONTROL): HIERARCH card + 0.009125 renders value field exactly 0.009125, not 0.009124999999999999. HOLDS patched, FAILS at base (base emits expanded form) -> discriminates.
- probe_2 (Req1.1/1.2/1.4): _format_float returns exact shortest reps for 0.009125,8.95,-99.9,0.1,-0.5. HOLDS patched; FAILS at base.
- probe_3 (Req2.1/2.2/2.3/2.4): decimal-or-E present; whole numbers keep '.'; sci notation uses upper-case E, no lower-case e, round-trips. HOLDS patched.
- probe_4 (Req3.1/3.2/3.3): no-E long -> first-20-char truncation len 20; E long -> exponent suffix preserved, exactly 20; every finite float <=20 chars. HOLDS patched.
- probe_5 (Req4.1/4.2): complex formatted via same helper into parenthesized form; inf/-inf/nan render without error. HOLDS patched.
- probe_6 (Req4.3/4.4/4.5): HIERARCH ESO IFM CL RADIUS + 0.009125 + long comment: no truncation warning, comment preserved, value 0.009125; roundtrip via fromstring; ordinary/negative/sci float cards render 1.0/-99.9/1E+32. HOLDS patched.

CANDIDATE PATCH 'seventeen_sig_digits' (weak.diff): replaces the shortest-form str(value) with f"{value:.17G}" (17 sig digits still round-trips) + '.0' fallback + e->E. It satisfies round-trip and FITS-legality but expands 0.009125 -> 0.009124999999999999. Probe suite REJECTS it: probe_1 FAIL (expanded form), probe_2 FAIL (all shortest-rep cases wrong), probe_6 FAIL (comment truncated, 1E+32 becomes 1.00000000000000E+32). Probes 3/4/5 hold, but the discriminating probes 1/2/6 catch it. => 1/1 weak candidate rejected; suite discriminates the lazy fix a weak reading permits.

Conclusion: 6 distinct probes all hold on patched; positive control discriminates base vs patched (prepatch_reproduced=true); >=1 wrong-fix candidate exercised and REJECTED by the suite. No mandated behavior the gold code lacks. SOUND.

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
"""Req1.3 (positive control): HIERARCH card with value 0.009125 renders value
field exactly as 0.009125, not an expanded form."""
import sys
from astropy.io.fits.card import Card

c = Card("HIERARCH ABC DEF GH IJKLMN", 0.009125, "Comment")
img = str(c)
print("card image:", repr(img))
if "0.009124999999999999" in img:
    print("FAIL: expanded form present")
    sys.exit(1)
if "0.009125" not in img:
    print("FAIL: shortest value form absent")
    sys.exit(1)
print("OK: value rendered as 0.009125")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements cover _format_float in astropy/io/fits/card.py: render floats from shortest str/repr form (Req1), preserve FITS-legal formatting (Req2), enforce 20-char cap (Req3), keep existing behaviors incl. complex/non-finite/roundtrip (Req4).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.3, POSITIVE CONTROL): HIERARCH card + 0.009125 renders value field exactly 0.009125, not 0.009124999999999999. HOLDS patched, FAILS at base (base emits expanded form) -> discriminates.
- probe_2 (Req1.1/1.2/1.4): _format_float returns exact shortest reps for 0.009125,8.95,-99.9,0.1,-0.5. HOLDS patched; FAILS at base.
- probe_3 (Req2.1/2.2/2.3/2.4): decimal-or-E present; whole numbers keep '.'; sci notation uses upper-case E, no lower-case e, round-trips. HOLDS patched.
- probe_4 (Req3.1/3.2/3.3): no-E long -> first-20-char truncation len 20; E long -> exponent suffix preserved, exactly 20; every finite float <=20 chars. HOLDS patched.
- probe_5 (Req4.1/4.2): complex formatted via same helper into parenthesized form; inf/-inf/nan render without error. HOLDS patched.
- probe_6 (Req4.3/4.4/4.5): HIERARCH ESO IFM CL RADIUS + 0.009125 + long comment: no truncation warning, comment preserved, value 0.009125; roundtrip via fromstring; ordinary/negative/sci float cards render 1.0/-99.9/1E+32. HOLDS patched.

CANDIDATE PATCH 'seventeen_sig_digits' (weak.diff): replaces the shortest-form str(value) with f"{value:.17G}" (17 sig digits still round-trips) + '.0' fallback + e->E. It satisfies round-trip and FITS-legality but expands 0.009125 -> 0.009124999999999999. Probe suite REJECTS it: probe_1 FAIL (expanded form), probe_2 FAIL (all shortest-rep cases wrong), probe_6 FAIL (comment truncated, 1E+32 becomes 1.00000000000000E+32). Probes 3/4/5 hold, but the discriminating probes 1/2/6 catch it. => 1/1 weak candidate rejected; suite discriminates the lazy fix a weak reading permits.

Conclusion: 6 distinct probes all hold on patched; positive control discriminates base vs patched (prepatch_reproduced=true); >=1 wrong-fix candidate exercised and REJECTED by the suite. No mandated behavior the gold code lacks. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces f'{value:.16G}' with str(value).replace('e','E') plus the 20-char cap logic. Requirements 1-4 map one-to-one onto: (1) shortest repr source, (2) FITS-legal formatting incl. upper-case E and decimal presence — note the '.0' append branch is dead in the new code because str(float) always yields a '.' or 'e', but Req2.1/2.3 are stated as guaranteed properties of the output (dot-or-E present, whole numbers keep decimal), which the probe confirms hold, so the requirement is faithful to observable behavior even though its mechanism differs; (3) both truncation branches verified; (4) complex/non-finite/roundtrip preserved. No mandated behavior absent, no forbidden behavior present, boundary correctly placed on the full _format_float output and Card.image.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within the public problem_statement plus legitimate behavioral generalization. The only concrete value cited (0.009125 and its expanded form 0.009124999999999999) and the HIERARCH scenario, the 20-char cap, _format_float/Card.image/str(Card) identifiers, and the str(value) approach are ALL in the public problem_statement. The hidden FAIL_TO_PASS test (test_floating_point_string_representation_card) additionally checks 8.95 and -99.9 — these specific values are NOT enumerated; Req 1.4 instead describes 'few significant digits (whether positive or negative)' as behavior, which is legitimate translation. No test names/paths/ids, no quoted test or gold code, no fix-invented identifiers. Req 2.4's 1e+32/1e-32 and Req 2.3's 1.0 are generic illustrations, not drawn from hidden tests (the existing PASS_TO_PASS test uses -4.6737463674763E+32; not reproduced). Req 3's truncation rules describe preserved existing code behavior with no corresponding hidden test, so they are not test-shaped reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
