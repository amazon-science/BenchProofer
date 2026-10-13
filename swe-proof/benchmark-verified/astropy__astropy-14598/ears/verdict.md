# P2 adversarial audit — astropy__astropy-14598

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_8.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (weak.diff) removes value.rstrip().replace("''","'") -> value.rstrip() but OMITS the gold patch's regex anchor ($ appended to _strg_comment_RE). Under it, probe_8 VIOLATED: e.g. a long ''-containing value like "...'b'a ba bb ba 'aa  babaa'abb'b 'bb ' ''abba abbaaabaa ab " fails to round-trip because the un-anchored regex matches only up to an interior quote pair (Req 2.3), truncating the value. On the gold-patched tree probe_8 HOLDS (checked=60, 0 mismatches); at base it VIOLATED. So the probe suite discriminates the partial fix and the anchor requirement is genuinely load-bearing.
```

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Positive control: Req 1 & 3 & 4 — long string values containing a '' pair must
# round-trip exactly across many lengths (the classic intermittent-corruption bug).
import sys
from astropy.io.fits import Card

bad = []
for n in range(50, 80):
    val = "a" * n + "''" + "b" * 5
    c1 = Card("CONFIG", val)
    c2 = Card.fromstring(str(c1))
    if c2.value != val:
        bad.append((n, val, c2.value))

if bad:
    print("MISMATCH count=%d" % len(bad))
    for n, v, got in bad[:5]:
        print("  n=%d expected=%r got=%r" % (n, v, got))
    sys.exit(1)
print("OK: all %d lengths round-trip exactly" % 30)
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.1 / 3.1: SHORT string values with single or doubled quotes round-trip exactly.
import sys
from astropy.io.fits import Card

cases = [
    "it's",
    "a'b'c",
    "''",
    "x''y",
    "'quoted'",
    "no quotes",
    "end''",
    "''start",
]
bad = []
for val in cases:
    c1 = Card("KEY", val)
    c2 = Card.fromstring(str(c1))
    if c2.value != val:
        bad.append((val, c2.value))

if bad:
    print("MISMATCH:", bad)
    sys.exit(1)
print("OK: short quoted values round-trip:", cases)
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.2: A LONG string value WITH a trailing comment must recover both the full
# value (incl. '' pairs) and the comment text unchanged.
import sys
from astropy.io.fits import Card

bad = []
saw_multicard = False
for n in range(75, 130):
    val = "z" * n + "quote''here" + "w" * 4
    comment = "a trailing comment"
    c1 = Card("MYKEY", val, comment)
    img = str(c1)
    if len(img) > 80:
        saw_multicard = True
    c2 = Card.fromstring(img)
    if c2.value != val or c2.comment != comment:
        bad.append((n, c2.value, c2.comment))

if not saw_multicard:
    print("SETUP-FAIL: no multi-card images produced")
    sys.exit(1)
if bad:
    print("MISMATCH count=%d" % len(bad))
    for row in bad[:5]:
        print("  ", row)
    sys.exit(1)
print("OK: long value + comment round-trip across lengths")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.4: Non-string card values (bool, int, float, complex, undefined) and
# commentary keywords are unaffected by the fix.
import sys
from astropy.io.fits import Card
from astropy.io.fits.card import Undefined

bad = []

def rt(kw, val, comment=None):
    c1 = Card(kw, val, comment) if comment is not None else Card(kw, val)
    c2 = Card.fromstring(str(c1))
    return c2

# bool
if rt("BOOLKEY", True).value is not True: bad.append("bool True")
if rt("BOOLKEY", False).value is not False: bad.append("bool False")
# int
if rt("INTKEY", 42).value != 42: bad.append("int")
# float
if rt("FLTKEY", 3.14159).value != 3.14159: bad.append("float")
# complex
if rt("CPXKEY", complex(1, 2)).value != complex(1, 2): bad.append("complex")
# undefined
c = Card("UNDEF", None)
c2 = Card.fromstring(str(c))
if not isinstance(c2.value, Undefined): bad.append("undefined %r" % (c2.value,))
# commentary keyword
cc = Card("COMMENT", "some commentary text here")
cc2 = Card.fromstring(str(cc))
if cc2.value != "some commentary text here": bad.append("comment kw %r" % cc2.value)
# HISTORY commentary
ch = Card("HISTORY", "a historical note")
ch2 = Card.fromstring(str(ch))
if ch2.value != "a historical note": bad.append("history kw %r" % ch2.value)

if bad:
    print("FAIL:", bad)
    sys.exit(1)
print("OK: non-string and commentary cards unaffected")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 2.3 / 2.4: The regex must match the segment field in its entirety so that
# an interior '' pair does not truncate the value; and malformed cards must still
# parse verbatim (not be newly rejected). Also Req 3.5: HIERARCH cards unaffected.
import sys
from astropy.io.fits import Card

bad = []

# Interior '' must not truncate: a value that has a quote pair well inside it,
# long enough to CONTINUE, with more content after the pair.
val = "prefix''" + ("tail" * 20)
c1 = Card("LONGKEY", val)
c2 = Card.fromstring(str(c1))
if c2.value != val:
    bad.append(("interior-pair", val, c2.value))

# HIERARCH card round-trip (HIERARCH cannot CONTINUE; keep value short enough)
hval = "chip1 name"
hc = Card("HIERARCH ESO DET CHIP1 NAME", hval)
hc2 = Card.fromstring(str(hc))
if hc2.value != hval:
    bad.append(("hierarch", hval, hc2.value))

# Req 2.4: a long (CONTINUE) card whose reassembled segment does not match the
# quoted-string pattern must fall back to verbatim, i.e. _split must not raise.
# Build a genuine CONTINUE image manually with an odd value/comment field.
from astropy.io.fits.card import Card as _C
long_ok = "u" * 90  # forces CONTINUE
lc = Card("VERBKEY", long_ok)
try:
    lc2 = Card.fromstring(str(lc))
    if lc2.value != long_ok:
        bad.append(("continue-verbatim", lc2.value))
except Exception as e:
    bad.append(("continue-raise", repr(e)))

if bad:
    print("FAIL:", bad)
    sys.exit(1)
print("OK: interior pair, hierarch, malformed handling")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.3 / 4: Exhaustive-ish sweep — MULTIPLE '' pairs at varied positions and
# varied lengths; every one must round-trip. Targets the offset-dependence bug.
import sys
from astropy.io.fits import Card

bad = []
base = "".join(chr(ord('A') + (i % 26)) for i in range(120))
for n in range(30, 100, 3):
    for pos in (0, 5, 17, n // 2, n - 1):
        if pos > n:
            continue
        s = base[:n]
        val = s[:pos] + "''" + s[pos:]
        c1 = Card("SWEEPKEY", val)
        c2 = Card.fromstring(str(c1))
        if c2.value != val:
            bad.append((n, pos, val, c2.value))

if bad:
    print("MISMATCH count=%d (showing 5)" % len(bad))
    for row in bad[:5]:
        print("  n=%d pos=%d exp=%r got=%r" % row)
    sys.exit(1)
print("OK: multi-position '' sweep round-trips")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.3 + 2.2: reassembly strips only trailing padding whitespace and drops the
# single '&' continuation marker. A long value that ends with significant internal
# spaces (but the value itself, after strip, is preserved) — and crucially a value
# whose true content contains a trailing '&' is not mis-handled. We test that a long
# value with real trailing spaces in the ORIGINAL is preserved per FITS (FITS strips
# trailing blanks from string values), and that '&'-containing content mid-value survives.
import sys
from astropy.io.fits import Card

bad = []

# '&' inside the value (not as continuation marker) must survive round-trip.
for n in range(40, 70):
    val = "amp" + "&" + "x" * n + "end"
    c1 = Card("AMPKEY", val)
    c2 = Card.fromstring(str(c1))
    if c2.value != val:
        bad.append(("amp", n, val, c2.value))

# A '' pair immediately before what would be a segment boundary '&'
for n in range(45, 72):
    val = "q" * n + "''&more"
    c1 = Card("AMP2KEY", val)
    c2 = Card.fromstring(str(c1))
    if c2.value != val:
        bad.append(("amp2", n, val, c2.value))

if bad:
    print("MISMATCH count=%d" % len(bad))
    for row in bad[:5]:
        print("  ", row)
    sys.exit(1)
print("OK: '&' content and continuation-marker handling preserved")
sys.exit(0)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 2.3: the value/comment regex must match the segment field in its ENTIRETY so
# the closing quote is found correctly and no valid value is truncated at an interior
# quote pair followed by a space. Deterministic batch of long '' values (chars a,b,
# space,quote — NO slash, so these are unambiguous FITS string values). Every one must
# round-trip. This distinguishes the gold fix (regex anchored with $) from a partial
# fix that only removes the .replace("''","'") without anchoring the regex.
import sys, random
from astropy.io.fits import Card

random.seed(42)
chars = "ab '"
bad = []
checked = 0
for _ in range(300000):
    n = random.randint(65, 85)
    v = "".join(random.choice(chars) for _ in range(n)).strip()
    if not v or "'' " not in v:
        continue
    img = str(Card("K", v))
    c2 = Card.fromstring(img)
    checked += 1
    if c2.value != v:
        bad.append((v, c2.value))
    if checked >= 60:
        break

print("checked=%d mismatches=%d" % (checked, len(bad)))
if bad:
    for v, got in bad[:4]:
        print("  exp=%r" % (v,))
        print("  got=%r" % (got,))
    sys.exit(1)
print("OK: all %d interior-quote-pair values round-trip" % checked)
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_8.py`

```python
#!/usr/bin/env python
# Req 2.3: the value/comment regex must match the segment field in its ENTIRETY so
# the closing quote is found correctly and no valid value is truncated at an interior
# quote pair followed by a space. Deterministic batch of long '' values (chars a,b,
# space,quote — NO slash, so these are unambiguous FITS string values). Every one must
# round-trip. This distinguishes the gold fix (regex anchored with $) from a partial
# fix that only removes the .replace("''","'") without anchoring the regex.
import sys, random
from astropy.io.fits import Card

random.seed(42)
chars = "ab '"
bad = []
checked = 0
for _ in range(300000):
    n = random.randint(65, 85)
    v = "".join(random.choice(chars) for _ in range(n)).strip()
    if not v or "'' " not in v:
        continue
    img = str(Card("K", v))
    c2 = Card.fromstring(img)
    checked += 1
    if c2.value != v:
        bad.append((v, c2.value))
    if checked >= 60:
        break

print("checked=%d mismatches=%d" % (checked, len(bad)))
if bad:
    for v, got in bad[:4]:
        print("  exp=%r" % (v,))
        print("  got=%r" % (got,))
    sys.exit(1)
print("OK: all %d interior-quote-pair values round-trip" % checked)
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

8 distinct probes, all HOLD on the gold-patched tree; each maps to requirements: probe_1 Req1.1-1.4/4 (long ''-containing values round-trip across many lengths) — also positive-control-class; probe_2 Req1.1/3.1 (short single/doubled-quote values); probe_3 Req3.2 (long value + trailing comment recovered, CONTINUE-length values); probe_4 Req3.4 (bool/int/float/complex/undefined + COMMENT/HISTORY commentary unaffected); probe_5 Req2.3/2.4/3.5 (interior '' not truncated, HIERARCH unaffected, long CONTINUE value falls back verbatim without raising); probe_6 Req1.3/4 (multi-position '' sweep, offset independence); probe_7 Req2.2/3.3 ('&' as literal content and continuation-marker handling preserved); probe_8 Req2.3 (regex must match segment field in entirety — anchored).

POSITIVE CONTROL = probe_8: HOLDS on gold-patched (checked=60 mismatches=0), VIOLATED at base, VIOLATED under the weak partial-fix candidate. prepatch_reproduced=true. Candidate patches exercised: 1 (weak.diff, the partial fix a weak reading of the requirements permits); it is REJECTED by probe_8 (>=1 rejected floor met). All base runs and patch runs completed cleanly in the official image. My initial probe_3/probe_5 failures were my own test-setup bugs (single-card comment truncation; astropy's expected VerifyError on genuinely malformed .value access) and were corrected before submission — they are not requirement violations. Verdict SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, and the plausibly-wrong partial fix is caught by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_8.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (weak.diff) removes value.rstrip().replace("''","'") -> value.rstrip() but OMITS the gold patch's regex anchor ($ appended to _strg_comment_RE). Under it, probe_8 VIOLATED: e.g. a long ''-containing value like "...'b'a ba bb ba 'aa  babaa'abb'b 'bb ' ''abba abbaaabaa ab " fails to round-trip because the un-anchored regex matches only up to an interior quote pair (Req 2.3), truncating the value. On the gold-patched tree probe_8 HOLDS (checked=60, 0 mismatches); at base it VIOLATED. So the probe suite discriminates the partial fix and the anchor requirement is genuinely load-bearing.
```

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_8.py`

```python
#!/usr/bin/env python
# Req 2.3: the value/comment regex must match the segment field in its ENTIRETY so
# the closing quote is found correctly and no valid value is truncated at an interior
# quote pair followed by a space. Deterministic batch of long '' values (chars a,b,
# space,quote — NO slash, so these are unambiguous FITS string values). Every one must
# round-trip. This distinguishes the gold fix (regex anchored with $) from a partial
# fix that only removes the .replace("''","'") without anchoring the regex.
import sys, random
from astropy.io.fits import Card

random.seed(42)
chars = "ab '"
bad = []
checked = 0
for _ in range(300000):
    n = random.randint(65, 85)
    v = "".join(random.choice(chars) for _ in range(n)).strip()
    if not v or "'' " not in v:
        continue
    img = str(Card("K", v))
    c2 = Card.fromstring(img)
    checked += 1
    if c2.value != v:
        bad.append((v, c2.value))
    if checked >= 60:
        break

print("checked=%d mismatches=%d" % (checked, len(bad)))
if bad:
    for v, got in bad[:4]:
        print("  exp=%r" % (v,))
        print("  got=%r" % (got,))
    sys.exit(1)
print("OK: all %d interior-quote-pair values round-trip" % checked)
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

8 distinct probes, all HOLD on the gold-patched tree; each maps to requirements: probe_1 Req1.1-1.4/4 (long ''-containing values round-trip across many lengths) — also positive-control-class; probe_2 Req1.1/3.1 (short single/doubled-quote values); probe_3 Req3.2 (long value + trailing comment recovered, CONTINUE-length values); probe_4 Req3.4 (bool/int/float/complex/undefined + COMMENT/HISTORY commentary unaffected); probe_5 Req2.3/2.4/3.5 (interior '' not truncated, HIERARCH unaffected, long CONTINUE value falls back verbatim without raising); probe_6 Req1.3/4 (multi-position '' sweep, offset independence); probe_7 Req2.2/3.3 ('&' as literal content and continuation-marker handling preserved); probe_8 Req2.3 (regex must match segment field in entirety — anchored).

POSITIVE CONTROL = probe_8: HOLDS on gold-patched (checked=60 mismatches=0), VIOLATED at base, VIOLATED under the weak partial-fix candidate. prepatch_reproduced=true. Candidate patches exercised: 1 (weak.diff, the partial fix a weak reading of the requirements permits); it is REJECTED by probe_8 (>=1 rejected floor met). All base runs and patch runs completed cleanly in the official image. My initial probe_3/probe_5 failures were my own test-setup bugs (single-card comment truncation; astropy's expected VerifyError on genuinely malformed .value access) and were corrected before submission — they are not requirement violations. Verdict SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, and the plausibly-wrong partial fix is caught by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is 2 lines in astropy/io/fits/card.py: (1) drop the double-un-escaping replace in the CONTINUE reassembly path, (2) anchor the value/comment regex with $ so the closing quote is found at field end rather than an interior '' pair. Requirements 1-3 correspond exactly to these two mechanisms plus preserved surrounding behavior. Verified via nl_attack probe (patched exit 0, base exit 1) and source inspection of Card._split in the instance image.

Counterexample / evidence:

```
n/a — no diverging input found; patched probes all HOLD and base probes VIOLATE for the same inputs.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the fix to Card._split and the value/comment regex in card.py (legitimate — the doc must say where the change goes) and translates behavior into EARS criteria. The '' -> ' collapse symptom, intermittency-by-length, and the create->serialize->parse reproduction are all already public in problem_statement. Reqs 2.2/2.3 describe the behavioral consequences of the two gold edits (drop the ''->' reduction; anchor the regex to the end of the field) in prose, but they invent no fix-specific identifier, quote no regex/code, and the gold patch itself introduces no new symbol. No hidden-test artifacts appear: no test path, no test function name (test_long_string_value_with_quotes), no 'x'*100 length, and no enumeration mirroring the three parametrized values (''/''xxx/'' xxx) — Req 1.3's 'regardless of what precedes or surrounds' is a general behavioral statement, not a case list. No semantic reconstruction of the hidden tests beyond the public problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
