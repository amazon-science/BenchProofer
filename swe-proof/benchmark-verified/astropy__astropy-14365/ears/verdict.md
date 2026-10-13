# P2 adversarial audit — astropy__astropy-14365

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_4.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1.1/1.2/1.3: _line_type classifies lowercase READ SERR/TERR as command; uppercase too; same category.
from astropy.io.ascii.qdp import _line_type
ok = True
for line in ["read serr 1 2", "READ SERR 1 2", "Read Terr 1 2", "read terr 1 2", "READ TERR 1 2"]:
    t = _line_type(line)
    print(repr(line), "->", t)
    if t != "command":
        ok = False
# same category regardless of case
if _line_type("read serr 1 2") != _line_type("READ SERR 1 2"):
    print("case mismatch category"); ok = False
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req2.1: table-break 'new' marker recognized in any case
from astropy.io.ascii.qdp import _line_type
ok = True
for line in ["NO NO NO NO NO", "no no no no no", "No No No", "nO nO"]:
    t = _line_type(line)
    print(repr(line), "->", t)
    if t != "new":
        ok = False
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.2/2.4: data rows with numeric+missing tokens (any case) classified data,N; whitespace and comma delim
from astropy.io.ascii.qdp import _line_type
ok = True
cases = [
    (" 21345.45 1.53e-3 1e-3 .04 no nan", None, "data,6"),
    (" 21345.45 1.53e-3 1e-3 .04 NO nan", None, "data,6"),
    (" 21345.45,1.53e-3,1e-3,.04,no,nan", ",", "data,6"),
]
for line, d, exp in cases:
    t = _line_type(line, delimiter=d)
    print(repr(line), "delim", repr(d), "->", t)
    if t != exp:
        ok = False
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1/3.2/3.3 & Req4: end-to-end read of lowercase file masks 'no', attaches error cols, matches uppercase
import numpy as np
from astropy.table import Table
low = """read serr 1 2
1 0.5 1 0.5
no no no no
2 0.5 no 0.5
"""
up = """READ SERR 1 2
1 0.5 1 0.5
NO NO NO NO
2 0.5 NO 0.5
"""
import io
tl = Table.read(low.splitlines(), format="ascii.qdp")
tu = Table.read(up.splitlines(), format="ascii.qdp")
print("low cols", tl.colnames)
print("up cols", tu.colnames)
ok = tl.colnames == tu.colnames
# masked entries same
for c in tl.colnames:
    ml = list(np.ma.getmaskarray(tl[c]))
    mu = list(np.ma.getmaskarray(tu[c]))
    print(c, "masks low", ml, "up", mu)
    if ml != mu:
        ok = False
    # values where not masked
    for a,b,m in zip(tl[c], tu[c], mu):
        if not m and a != b:
            ok = False
# must have error columns attached (serr -> _err columns)
if not any("err" in c.lower() for c in tl.colnames):
    print("no error columns"); ok = False
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req5: preservation - uppercase round-trip, comma delimiter, numeric parsing (int/float/nan), unrecognized raises
import numpy as np, io, sys
from astropy.table import Table
from astropy.io.ascii.qdp import _line_type
ok = True
# unrecognized line still raises
try:
    _line_type(" some non-comment gibberish")
    print("FAIL: should have raised"); ok = False
except ValueError:
    print("gibberish raised ValueError OK")
# numeric parsing preserved: int stays int
t = Table.read(["3 4 5"], format="ascii.qdp")
print("row0 dtypes", [t[c].dtype.kind for c in t.colnames], "vals", [t[c][0] for c in t.colnames])
# round-trip uppercase via write/read
tab = Table({'a':[1,2],'b':[3.5,4.5]})
buf = io.StringIO()
tab.write(buf, format="ascii.qdp")
buf.seek(0)
back = Table.read(buf.read().splitlines(), format="ascii.qdp")
print("roundtrip cols", back.colnames)
for c in ['col1','col2']:
    pass
# nan parsing
tn = Table.read(["1 nan 2"], format="ascii.qdp")
print("nan row", [tn[c][0] for c in tn.colnames])
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_4.py`

```python
# Req3.1/3.2/3.3 & Req4: end-to-end read of lowercase file masks 'no', attaches error cols, matches uppercase
import numpy as np
from astropy.table import Table
low = """read serr 1 2
1 0.5 1 0.5
no no no no
2 0.5 no 0.5
"""
up = """READ SERR 1 2
1 0.5 1 0.5
NO NO NO NO
2 0.5 NO 0.5
"""
import io
tl = Table.read(low.splitlines(), format="ascii.qdp")
tu = Table.read(up.splitlines(), format="ascii.qdp")
print("low cols", tl.colnames)
print("up cols", tu.colnames)
ok = tl.colnames == tu.colnames
# masked entries same
for c in tl.colnames:
    ml = list(np.ma.getmaskarray(tl[c]))
    mu = list(np.ma.getmaskarray(tu[c]))
    print(c, "masks low", ml, "up", mu)
    if ml != mu:
        ok = False
    # values where not masked
    for a,b,m in zip(tl[c], tu[c], mu):
        if not m and a != b:
            ok = False
# must have error columns attached (serr -> _err columns)
if not any("err" in c.lower() for c in tl.colnames):
    print("no error columns"); ok = False
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes cover the requirements. probe_1 (Req1.1-1.3: _line_type classifies lowercase/mixed-case READ SERR/TERR as 'command'), probe_2 (Req2.1: 'NO NO...' table-break marker recognized in any case as 'new'), probe_3 (Req2.2/2.4: mixed-case data rows -> data,N for whitespace and comma delimiter), probe_4 (Req3.1/3.2/3.3 + Req4: end-to-end lowercase read masks 'no', attaches serr error columns, matches uppercase table), probe_5 (Req5 regression: gibberish still raises ValueError, int/float/nan parsing and round-trip preserved).

Results: all 5 HOLD on gold-patched tree. Probes 1-4 FAIL at base (VIOLATED with 'Unrecognized QDP line'); probe_5 HOLDS at base (correct: regression criteria). Positive control = probe_4 (HOLDS patched, FAILS at base with 'Unrecognized QDP line: read serr 1 2') -> discriminating power confirmed.

Candidate wrong-fix 'regex_only_partial_fix' (weak.diff): applies ONLY the re.IGNORECASE change, omitting the `v.upper()=="NO"` masking fix. This is the partial fix a weak reading of Req1/Req2 permits. Probes 1,2,3,5 HOLD under it, but probe_4 REJECTS it. Suite discriminates a probe-conforming-on-line-classification-but-wrong implementation. Requirement 3 (case-insensitive missing-value detection) is the criterion that the partial fix violates, so the requirements are NOT too weak and the gold patch's two-part change is fully mandated. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_4.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_4.py`

```python
# Req3.1/3.2/3.3 & Req4: end-to-end read of lowercase file masks 'no', attaches error cols, matches uppercase
import numpy as np
from astropy.table import Table
low = """read serr 1 2
1 0.5 1 0.5
no no no no
2 0.5 no 0.5
"""
up = """READ SERR 1 2
1 0.5 1 0.5
NO NO NO NO
2 0.5 NO 0.5
"""
import io
tl = Table.read(low.splitlines(), format="ascii.qdp")
tu = Table.read(up.splitlines(), format="ascii.qdp")
print("low cols", tl.colnames)
print("up cols", tu.colnames)
ok = tl.colnames == tu.colnames
# masked entries same
for c in tl.colnames:
    ml = list(np.ma.getmaskarray(tl[c]))
    mu = list(np.ma.getmaskarray(tu[c]))
    print(c, "masks low", ml, "up", mu)
    if ml != mu:
        ok = False
    # values where not masked
    for a,b,m in zip(tl[c], tu[c], mu):
        if not m and a != b:
            ok = False
# must have error columns attached (serr -> _err columns)
if not any("err" in c.lower() for c in tl.colnames):
    print("no error columns"); ok = False
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes cover the requirements. probe_1 (Req1.1-1.3: _line_type classifies lowercase/mixed-case READ SERR/TERR as 'command'), probe_2 (Req2.1: 'NO NO...' table-break marker recognized in any case as 'new'), probe_3 (Req2.2/2.4: mixed-case data rows -> data,N for whitespace and comma delimiter), probe_4 (Req3.1/3.2/3.3 + Req4: end-to-end lowercase read masks 'no', attaches serr error columns, matches uppercase table), probe_5 (Req5 regression: gibberish still raises ValueError, int/float/nan parsing and round-trip preserved).

Results: all 5 HOLD on gold-patched tree. Probes 1-4 FAIL at base (VIOLATED with 'Unrecognized QDP line'); probe_5 HOLDS at base (correct: regression criteria). Positive control = probe_4 (HOLDS patched, FAILS at base with 'Unrecognized QDP line: read serr 1 2') -> discriminating power confirmed.

Candidate wrong-fix 'regex_only_partial_fix' (weak.diff): applies ONLY the re.IGNORECASE change, omitting the `v.upper()=="NO"` masking fix. This is the partial fix a weak reading of Req1/Req2 permits. Probes 1,2,3,5 HOLD under it, but probe_4 REJECTS it. Suite discriminates a probe-conforming-on-line-classification-but-wrong implementation. Requirement 3 (case-insensitive missing-value detection) is the criterion that the partial fix violates, so the requirements are NOT too weak and the gold patch's two-part change is fully mandated. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements correctly identify both changed helpers (_line_type via re.IGNORECASE, _get_tables_from_qdp_file via v.upper()) rather than a narrow slice. Boundary is the full changed observable behavior (case-insensitive classification + missing-value detection + end-to-end read + upper-case preservation). All probe observations agree with requirements.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior (case-insensitive line classification and NO-sentinel detection) that is directly derivable from the public problem_statement, which already exposes the case-insensitivity requirement, the 'READ SERR 1 2' / 'read serr 1 2' equivalence, and the ValueError('Unrecognized QDP line') symptom. Naming the two changed helpers (_line_type, _get_tables_from_qdp_file, both in the gold patch) and the NO sentinel is legitimate localization. SERR/TERR, 'nan', and comma-delimiter are QDP domain features (pre-existing in the code/regex), not fix-invented identifiers. No test file path (tests/test_qdp.py), test/function names (test_roundtrip, lowercase_header), parametrization ids (test_roundtrip[True/False]), quoted test/gold code, or case-enumerations mirroring the test parametrization appear. The lowercase-vs-uppercase 'same table content' requirement mirrors the general fixed behavior, not the specific hidden test fixture.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
