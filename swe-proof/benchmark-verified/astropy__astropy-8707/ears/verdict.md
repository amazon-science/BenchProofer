# P2 adversarial audit — astropy__astropy-8707

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

Counterexample / evidence:

```
Weak candidate (gold patch with latin1->ascii for the functional decode/encode) is REJECTED by probe_2: Card.fromstring(b'COMMENT   hello \xff world') raises UnicodeDecodeError under ascii, whereas Req1.1 mandates latin-1 (byte 0xff -> code point 0xff preserved). This is exactly the non-ASCII-byte preservation exercised by the hidden test_card_from_bytes.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1/1.2 + positive control: Card.fromstring(bytes) == Card.fromstring(text) parsed keyword/value."""
import sys
from astropy.io.fits.card import Card

text = "ABC     =                  1.5 / a comment"
b = text.encode("latin1")

cb = Card.fromstring(b)
ct = Card.fromstring(text)

print("bytes card keyword=", repr(cb.keyword), "value=", repr(cb.value))
print("text  card keyword=", repr(ct.keyword), "value=", repr(ct.value))

ok = (cb.keyword == ct.keyword) and (cb.value == ct.value) and (cb.keyword == "ABC") and (cb.value == 1.5)
print("MATCH", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1 non-ASCII byte preservation via latin-1: byte 0xff maps to code point 0xff, equal to latin1 decode."""
import sys
from astropy.io.fits.card import Card

# a comment containing a stray non-ascii byte 0xff
b = b"COMMENT   hello \xff world"
cb = Card.fromstring(b)
ct = Card.fromstring(b.decode("latin1"))

print("bytes image=", repr(cb.image))
print("text  image=", repr(ct.image))
# image must equal the latin1-decoded padded text, and contain the \xff codepoint
ok = (cb.image == ct.image) and ("\xff" in cb.image)
print("MATCH", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3: short byte input (< 80 cols) succeeds and pads to card width, same as text."""
import sys
from astropy.io.fits.card import Card

short = "SIMPLE  =                    T"
b = short.encode("latin1")
cb = Card.fromstring(b)
ct = Card.fromstring(short)

print("bytes image len=", len(cb.image), "text image len=", len(ct.image))
print("bytes keyword/value=", repr(cb.keyword), repr(cb.value))
ok = (len(cb.image) == 80) and (cb.image == ct.image) and (cb.keyword == "SIMPLE") and (cb.value is True)
print("MATCH", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3: Header.fromstring(bytes) == Header.fromstring(text) == round-trip; identical tostring."""
import sys
from astropy.io.fits.header import Header

hdr = Header()
hdr["SIMPLE"] = True
hdr["BITPIX"] = 8
hdr["NAXIS"] = 0
hdr["EXTEND"] = True
hdr["OBSERVER"] = "someone"

s = hdr.tostring()  # raw text form, full 80-col cards, no sep
b = s.encode("latin1")

hb = Header.fromstring(b)
ht = Header.fromstring(s)

print("from bytes == from text:", hb == ht)
print("from bytes == source:", hb == hdr)
print("tostring identical:", hb.tostring() == ht.tostring() == hdr.tostring())
print("BITPIX from bytes:", hb["BITPIX"], "OBSERVER:", hb["OBSERVER"])
ok = (hb == ht) and (hb == hdr) and (hb.tostring() == hdr.tostring()) and (hb["BITPIX"] == 8) and (hb["OBSERVER"] == "someone")
print("MATCH", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.4: byte input honors card separator + continuation + END detection equivalently to text."""
import sys
from astropy.io.fits.header import Header

text = ("SIMPLE  =                    T / conforms to FITS standard\n"
        "BITPIX  =                    8 / array data type\n"
        "NAXIS   =                    0 / number of array dimensions\n"
        "EXTEND  =                    T\n"
        "END\n")
b = text.encode("latin1")

hb = Header.fromstring(b, sep="\n")
ht = Header.fromstring(text, sep="\n")

print("bytes hdr len=", len(hb), "text hdr len=", len(ht))
print("equal:", hb == ht, "SIMPLE:", hb["SIMPLE"], "BITPIX:", hb["BITPIX"])
# END should terminate; header should have exactly the 4 cards, no END card kept
ok = (hb == ht) and (len(hb) == 4) and (hb["SIMPLE"] is True) and (hb["BITPIX"] == 8) and ("END" not in hb)
print("MATCH", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.4 continuation cards: long string value split into CONTINUE cards, parsed from bytes == from text."""
import sys
from astropy.io.fits.header import Header
from astropy.io.fits.card import Card

longval = "x" * 120  # forces a CONTINUE card
c = Card("LONGKEY", longval)
h = Header([c])
s = h.tostring()
# sanity: must contain a CONTINUE card
assert "CONTINUE" in s, "test setup failed: no CONTINUE card"
b = s.encode("latin1")

hb = Header.fromstring(b)
ht = Header.fromstring(s)
print("bytes value len=", len(hb["LONGKEY"]), "text value len=", len(ht["LONGKEY"]))
ok = (hb == ht) and (hb["LONGKEY"] == longval)
print("MATCH", ok)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req3.1 regression: text card parsing for every FITS value type is preserved (string, bool, int, long, float, complex)."""
import sys
from astropy.io.fits.card import Card

cases = [
    ("STRVAL  = 'hello   '", "hello"),
    ("BOOLVAL =                    T", True),
    ("INTVAL  =                   42", 42),
    ("BIGINT  =        123456789012345", 123456789012345),
    ("FLTVAL  =                  3.14", 3.14),
    ("CPLXVAL =           (1.0, 2.0)", complex(1.0, 2.0)),
]
allok = True
for img, expected in cases:
    c = Card.fromstring(img)
    got = c.value
    match = (got == expected) and (type(got) == type(expected) or isinstance(got, type(expected)))
    print(f"{c.keyword}: got={got!r} expected={expected!r} ok={match}")
    if not match:
        allok = False
# also default-constructed card -> keyword empty string
d = Card()
print("default keyword=", repr(d.keyword))
if d.keyword != "":
    allok = False
print("MATCH", allok)
sys.exit(0 if allok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1/1.2 + positive control: Card.fromstring(bytes) == Card.fromstring(text) parsed keyword/value."""
import sys
from astropy.io.fits.card import Card

text = "ABC     =                  1.5 / a comment"
b = text.encode("latin1")

cb = Card.fromstring(b)
ct = Card.fromstring(text)

print("bytes card keyword=", repr(cb.keyword), "value=", repr(cb.value))
print("text  card keyword=", repr(ct.keyword), "value=", repr(ct.value))

ok = (cb.keyword == ct.keyword) and (cb.value == ct.value) and (cb.keyword == "ABC") and (cb.value == 1.5)
print("MATCH", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover: Req1.1/1.2 keyword+value equivalence (probe_1, positive control), Req1.1 non-ASCII latin-1 preservation (probe_2), Req1.3 short-input padding (probe_3), Req2.1/2.2/2.3 header-from-bytes == from-text == source & identical tostring (probe_4), Req2.4 card separator + END detection (probe_5), Req2.4 CONTINUE-card equivalence (probe_6), Req3.1/3.2 text value-type regression + default keyword (probe_7). Results: all 7 HOLD on patched tree. Positive control probe_1 VIOLATED at base, HOLDS patched -> discriminates (prepatch reproduced). Regression probe_7 HOLDS at both base and patched (correct: no behavior change). Weak candidate 'ascii_decode_weakfix' applies cleanly at base; probes 1,3,4,5,6,7 HOLD under it but probe_2 REJECTS it -> suite discriminates the wrong fix; this candidate would NOT resolve the hidden test. Verdict SOUND: >=5 probes hold, positive control discriminates, >=1 candidate exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (gold patch with latin1->ascii for the functional decode/encode) is REJECTED by probe_2: Card.fromstring(b'COMMENT   hello \xff world') raises UnicodeDecodeError under ascii, whereas Req1.1 mandates latin-1 (byte 0xff -> code point 0xff preserved). This is exactly the non-ASCII-byte preservation exercised by the hidden test_card_from_bytes.
```

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
"""Req1.1/1.2 + positive control: Card.fromstring(bytes) == Card.fromstring(text) parsed keyword/value."""
import sys
from astropy.io.fits.card import Card

text = "ABC     =                  1.5 / a comment"
b = text.encode("latin1")

cb = Card.fromstring(b)
ct = Card.fromstring(text)

print("bytes card keyword=", repr(cb.keyword), "value=", repr(cb.value))
print("text  card keyword=", repr(ct.keyword), "value=", repr(ct.value))

ok = (cb.keyword == ct.keyword) and (cb.value == ct.value) and (cb.keyword == "ABC") and (cb.value == 1.5)
print("MATCH", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover: Req1.1/1.2 keyword+value equivalence (probe_1, positive control), Req1.1 non-ASCII latin-1 preservation (probe_2), Req1.3 short-input padding (probe_3), Req2.1/2.2/2.3 header-from-bytes == from-text == source & identical tostring (probe_4), Req2.4 card separator + END detection (probe_5), Req2.4 CONTINUE-card equivalence (probe_6), Req3.1/3.2 text value-type regression + default keyword (probe_7). Results: all 7 HOLD on patched tree. Positive control probe_1 VIOLATED at base, HOLDS patched -> discriminates (prepatch reproduced). Regression probe_7 HOLDS at both base and patched (correct: no behavior change). Weak candidate 'ascii_decode_weakfix' applies cleanly at base; probes 1,3,4,5,6,7 HOLD under it but probe_2 REJECTS it -> suite discriminates the wrong fix; this candidate would NOT resolve the hidden test. Verdict SOUND: >=5 probes hold, positive control discriminates, >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is purely additive; requirements neither mandate absent behavior, forbid present behavior, invent behavior, nor narrow the boundary. R3 (preserve existing) is faithful — additions-only per G-INTEGRITY. R3's itemization mirroring the hidden PASS_TO_PASS suite is a leakage concern (G-PANEL-3, already stamped fail) and does not make any R3 claim untrue of the patched code. Faithfulness verdict: FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the byte-string acceptance behavior of Header.fromstring/Card.fromstring in general behavioral terms. Naming these methods and their modules (header.py/card.py) is legitimate localization. The latin-1 encoding detail, while it appears in the gold patch, is the substantive behavioral change being specified (how bytes are interpreted) — this is translating the fix into a requirement, not transmitting tests. None of the hidden-test specifics leak: the test data file (test0.fits), the literal card `b"ABC = 'abc'"` with keyword ABC/value abc, the NAXIS keyword assertion, the tostring equality check, the test function/class names (test_card_from_bytes, test_header_fromstring_bytes, TestHeaderFunctions), or GitHub issue #8706 are all absent. Requirement 2.2/2.3's header-equality and serialized-form clauses parallel the test's assertions but are stated as general behavior for 'the complete header section of a FITS file' rather than reconstructing the specific parametrized case. No fix-invented identifiers (CONTINUE/END/end_card locals) are exposed; the mentioned 'card separator argument' is the public sep parameter.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
