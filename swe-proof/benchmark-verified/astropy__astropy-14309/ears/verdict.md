# P2 adversarial audit — astropy__astropy-14309

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control: Req1.4 - non-FITS path, no positional args -> False, no IndexError."""
import sys
from astropy.io.fits.connect import is_fits
try:
    r = is_fits("read", "test.ecsv", None)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("returned:", repr(r))
sys.exit(0 if r is False else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2 - FITS suffixes (case-insensitive) return True, without accessing args."""
import sys
from astropy.io.fits.connect import is_fits
cases = ["a.fits", "a.FITS", "a.fits.gz", "b.fit", "b.FIT.GZ", "c.fts", "c.FTS.GZ"]
ok = True
for c in cases:
    r = is_fits("read", c, None)  # no positional args on purpose
    print(c, "->", repr(r))
    if r is not True:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3 - non-FITS suffixes return False (bool), no args accessed."""
import sys
from astropy.io.fits.connect import is_fits
cases = ["a.ecsv", "a.txt", "a.hdf5", "b.fits.bz2", "c.fitz", "noext"]
ok = True
for c in cases:
    r = is_fits("read", c, None)
    print(c, "->", repr(r))
    if r is not False:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2 - readable fileobj path: reads 30 bytes, restores position, True iff FITS signature.
Also verifies filepath/args are NOT consulted when a fileobj is given."""
import sys, io
from astropy.io.fits.connect import is_fits
from astropy.io.fits.hdu.hdulist import FITS_SIGNATURE

# Genuine FITS signature -> True; filepath is non-FITS, no args -> must not matter
buf = io.BytesIO(b"xxxxx" + FITS_SIGNATURE + b" " * 100)
buf.seek(5)  # signature begins here; verdict must use leading 30 bytes from here
r_true = is_fits("read", "notfits.ecsv", buf)
pos_after = buf.tell()
print("sig-match ->", repr(r_true), "pos restored to", pos_after)

# Non-signature bytes -> False
buf2 = io.BytesIO(b"HELLO WORLD not a fits header at all here...")
r_false = is_fits("read", "a.fits", buf2)  # filepath says fits, must be ignored
print("non-sig, filepath=.fits ->", repr(r_false))

ok = (r_true is True) and (pos_after == 5) and (r_false is False)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.3/2.4 - object-based: no fileobj, no filepath, first arg FITS object type -> True; else False.
And registry integration (Req1.5): identify_format for .ecsv does not raise."""
import sys
from astropy.io.fits.connect import is_fits
from astropy.io.fits import HDUList, BinTableHDU

# object detection
r_hdu = is_fits("read", None, None, HDUList())
r_other = is_fits("read", None, None, object())
print("HDUList ->", repr(r_hdu), "; object ->", repr(r_other))

# registry integration for a non-FITS filename with empty args
from astropy.io.registry import identify_format
try:
    fmts = identify_format("read", object, "spam.ecsv", None, [], {})
    print("identify_format('spam.ecsv') ->", fmts)
    reg_ok = "fits" not in fmts
except Exception as e:
    print("identify_format RAISED:", type(e).__name__, e)
    reg_ok = False

ok = (r_hdu is True) and (r_other is False) and reg_ok
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.4 - non-FITS path, no positional args -> False, no IndexError."""
import sys
from astropy.io.fits.connect import is_fits
try:
    r = is_fits("read", "test.ecsv", None)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("returned:", repr(r))
sys.exit(0 if r is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy__astropy-14309: is_fits fell through to args[0] for a non-FITS path with no positional args -> IndexError. Gold patch makes the filepath branch return the (case-insensitive) suffix match unconditionally.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.4/1.1, POSITIVE CONTROL): is_fits('read','test.ecsv',None) -> False, no IndexError. HOLDS patched (returned False); at base RAISES IndexError 'tuple index out of range' => prepatch reproduced, discriminating power confirmed.
- probe_2 (Req1.2): recognised FITS suffixes incl. uppercase (a.FITS, b.FIT.GZ, c.FTS.GZ) -> True, called with NO positional args. HOLDS patched.
- probe_3 (Req1.3): non-FITS suffixes (.ecsv/.txt/.hdf5/.fits.bz2/.fitz/noext) -> False (bool), no args. HOLDS patched.
- probe_4 (Req2.1/2.2): readable fileobj with FITS signature at offset 5 -> True and stream position restored to 5; non-signature bytes with filepath='.fits' -> False (proves filepath/args ignored when fileobj present). HOLDS patched.
- probe_5 (Req2.3/2.4 + Req1.5): no fileobj/no filepath, first arg HDUList -> True, plain object -> False; and registry.identify_format('read',...,'spam.ecsv',None,[],{}) returns [] (no 'fits'), does not raise. HOLDS patched.

Candidate wrong-fix (weak.diff): gold structure but drops .lower(), i.e. `return filepath.endswith((...))` with no case-folding. A weak reading of Req1 (only the IndexError crash / non-FITS negative) permits this. Applied at base_commit cleanly. Under it: probe_1 HOLDS, probe_2 REJECTED (a.FITS -> True is False... i.e. 'a.FITS' -> False, violating Req1.2 case-insensitive True), probe_3/4/5 HOLD. => the suite discriminates this wrong implementation (probe_2 catches loss of case-insensitivity). Not a TOO-WEAK finding.

Verdict SOUND: 5 distinct probes cover Req1.1-1.5 and Req2.1-2.4 including the SHALL-keep fileobj/object regression criteria; positive control discriminates (patched HOLD / base FAIL); >=1 candidate exercised and REJECTED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control: Req1.4 - non-FITS path, no positional args -> False, no IndexError."""
import sys
from astropy.io.fits.connect import is_fits
try:
    r = is_fits("read", "test.ecsv", None)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("returned:", repr(r))
sys.exit(0 if r is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy__astropy-14309: is_fits fell through to args[0] for a non-FITS path with no positional args -> IndexError. Gold patch makes the filepath branch return the (case-insensitive) suffix match unconditionally.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.4/1.1, POSITIVE CONTROL): is_fits('read','test.ecsv',None) -> False, no IndexError. HOLDS patched (returned False); at base RAISES IndexError 'tuple index out of range' => prepatch reproduced, discriminating power confirmed.
- probe_2 (Req1.2): recognised FITS suffixes incl. uppercase (a.FITS, b.FIT.GZ, c.FTS.GZ) -> True, called with NO positional args. HOLDS patched.
- probe_3 (Req1.3): non-FITS suffixes (.ecsv/.txt/.hdf5/.fits.bz2/.fitz/noext) -> False (bool), no args. HOLDS patched.
- probe_4 (Req2.1/2.2): readable fileobj with FITS signature at offset 5 -> True and stream position restored to 5; non-signature bytes with filepath='.fits' -> False (proves filepath/args ignored when fileobj present). HOLDS patched.
- probe_5 (Req2.3/2.4 + Req1.5): no fileobj/no filepath, first arg HDUList -> True, plain object -> False; and registry.identify_format('read',...,'spam.ecsv',None,[],{}) returns [] (no 'fits'), does not raise. HOLDS patched.

Candidate wrong-fix (weak.diff): gold structure but drops .lower(), i.e. `return filepath.endswith((...))` with no case-folding. A weak reading of Req1 (only the IndexError crash / non-FITS negative) permits this. Applied at base_commit cleanly. Under it: probe_1 HOLDS, probe_2 REJECTED (a.FITS -> True is False... i.e. 'a.FITS' -> False, violating Req1.2 case-insensitive True), probe_3/4/5 HOLD. => the suite discriminates this wrong implementation (probe_2 catches loss of case-insensitivity). Not a TOO-WEAK finding.

Verdict SOUND: 5 distinct probes cover Req1.1-1.5 and Req2.1-2.4 including the SHALL-keep fileobj/object regression criteria; positive control discriminates (patched HOLD / base FAIL); >=1 candidate exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed gold-patched tree: R1.2 is_fits('write','foo.fits',None)=True; R1.3 'foo.ecsv'=False; R1.1 case-insensitive 'FOO.FITS'=True; R1.4 no-ext filepath with no positional args returns False and raises no IndexError (the regression fix). R2.1 fileobj path reads 30 bytes (FITS_SIGNATURE len=30), restores tell() (verified pos 3→3), returns sig==signature. R2.3 args[0] branch: HDUList()→True, 5→False; exact type tuple (HDUList, TableHDU, BinTableHDU, GroupsHDU) matches source. R1.4 correctly scopes the no-IndexError guarantee to the filepath-present case; the residual IndexError for the (no fileobj, no filepath, no args) call pattern is pre-existing and unchanged by the patch, and the requirements do not claim to fix it — so no over-claim. Boundary is correctly modeled at the changed observable behavior, not a sub-branch.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All potentially test-derived content in requirements.md is already public via the problem_statement: the recognized FITS suffixes (.fits, .fits.gz, .fit, .fit.gz, .fts, .fts.gz), the isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU)) object types, the IndexError/args[0] fall-through, and the non-FITS .ecsv registry-probe scenario all appear verbatim in the traceback quoted in the issue. The hidden test (test_is_fits_gh_14305, `assert not connect.is_fits("", "foo.bar", None)`) contributes no unique identifiers to the document: the test name, path, issue number #14305, and the "foo.bar" literal are absent. Req 2.1's 'leading 30 bytes / restore stream position / FITS signature' describes the pre-existing fileobj branch (untouched by the gold edit) — legitimate localization, not test/gold reconstruction. The gold edit (return endswith(...)) is translated into behavioral criteria without quoting gold lines or inventing identifiers. No test-shaped case enumeration beyond the public traceback.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
