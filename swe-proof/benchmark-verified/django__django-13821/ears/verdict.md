# P2 adversarial audit — django__django-13821

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control (R1.1, R2.1/2.2/2.4): the hidden-test boundary case.
mock sqlite_version_info=(3,8,11,1), sqlite_version='3.8.11.1' -> below 3.9.0
=> must raise ImproperlyConfigured with the exact message reporting 3.9.0
required and the verbatim found string '3.8.11.1'.
HOLDS on patched, FAILS at base (base minimum is (3,8,3): (3,8,11,1) is NOT
< (3,8,3), so base does not raise at all)."""
import sys
from unittest import mock
from django.core.exceptions import ImproperlyConfigured
import django.db.backends.sqlite3.base as base

Database = base.Database
want = 'SQLite 3.9.0 or later is required (found 3.8.11.1).'
with mock.patch.object(Database, 'sqlite_version_info', (3, 8, 11, 1)), \
     mock.patch.object(Database, 'sqlite_version', '3.8.11.1'):
    try:
        base.check_sqlite_version()
        print("FAIL: no exception raised for (3,8,11,1)")
        sys.exit(1)
    except ImproperlyConfigured as e:
        got = str(e)
        print("raised ImproperlyConfigured:", repr(got))
        if got == want:
            print("PASS: exact expected message")
            sys.exit(0)
        print("FAIL: message mismatch, want", repr(want))
        sys.exit(1)
    except Exception as e:
        print("FAIL: wrong exception type:", type(e).__name__, e)
        sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.2: a version at/above the PREVIOUS minimum (3.8.3) but below 3.9.0 must
still be rejected. Use (3,8,7) — previously supported, now unsupported."""
import sys
from unittest import mock
from django.core.exceptions import ImproperlyConfigured
import django.db.backends.sqlite3.base as base
Database = base.Database
with mock.patch.object(Database, 'sqlite_version_info', (3, 8, 7)), \
     mock.patch.object(Database, 'sqlite_version', '3.8.7'):
    try:
        base.check_sqlite_version()
        print("FAIL: (3,8,7) accepted, but should be rejected")
        sys.exit(1)
    except ImproperlyConfigured as e:
        print("PASS: (3,8,7) rejected:", repr(str(e)))
        sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.4: 3.9.0 and greater must return normally (no raise). Test the exact
boundary (3,9,0) and a higher (3,11,0). Note: 3.11.0 vs 3.9.0 is the
numeric-vs-lexical case ('3.11' < '3.9' lexically) from R1.3 — a lexical
comparison would wrongly reject 3.11.0."""
import sys
from unittest import mock
import django.db.backends.sqlite3.base as base
Database = base.Database
ok = True
for vi, vs in [((3, 9, 0), '3.9.0'), ((3, 11, 0), '3.11.0')]:
    with mock.patch.object(Database, 'sqlite_version_info', vi), \
         mock.patch.object(Database, 'sqlite_version', vs):
        try:
            base.check_sqlite_version()
            print("OK: %s accepted (no raise)" % vs)
        except Exception as e:
            print("FAIL: %s raised %s: %s" % (vs, type(e).__name__, e))
            ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.3: numeric component-wise comparison, not lexical. (3,10,0) is below
3.9.0? No — it is ABOVE 3.9.0 numerically (10 > 9), but lexically '3.10' < '3.9'.
So (3,10,0) must be ACCEPTED. Conversely a two-digit-below case: (3,8,20)
lexically '3.8.20' vs boundary — must be REJECTED (8<9). Both classified by
numeric ordering."""
import sys
from unittest import mock
from django.core.exceptions import ImproperlyConfigured
import django.db.backends.sqlite3.base as base
Database = base.Database
ok = True
# (3,10,0): numerically >= (3,9,0) -> accept; lexical would reject
with mock.patch.object(Database, 'sqlite_version_info', (3, 10, 0)), \
     mock.patch.object(Database, 'sqlite_version', '3.10.0'):
    try:
        base.check_sqlite_version()
        print("OK: (3,10,0) accepted (numeric ordering)")
    except Exception as e:
        print("FAIL: (3,10,0) rejected -> lexical bug:", e)
        ok = False
# (3,8,20): numerically < (3,9,0) -> reject
with mock.patch.object(Database, 'sqlite_version_info', (3, 8, 20)), \
     mock.patch.object(Database, 'sqlite_version', '3.8.20'):
    try:
        base.check_sqlite_version()
        print("FAIL: (3,8,20) accepted, should reject")
        ok = False
    except ImproperlyConfigured:
        print("OK: (3,8,20) rejected")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R2.1/R2.3: the raised message must name the required minimum as '3.9.0'
exactly and NOT the old '3.8.3'. Also R2.2 shape 'SQLite 3.9.0 or later is
required (found <version>).'. Use a plain 3-component too-old version."""
import sys, re
from unittest import mock
from django.core.exceptions import ImproperlyConfigured
import django.db.backends.sqlite3.base as base
Database = base.Database
with mock.patch.object(Database, 'sqlite_version_info', (3, 8, 2)), \
     mock.patch.object(Database, 'sqlite_version', '3.8.2'):
    try:
        base.check_sqlite_version()
        print("FAIL: (3,8,2) not rejected")
        sys.exit(1)
    except ImproperlyConfigured as e:
        msg = str(e)
        print("msg:", repr(msg))
        if '3.8.3' in msg:
            print("FAIL: message still names old minimum 3.8.3")
            sys.exit(1)
        if msg != 'SQLite 3.9.0 or later is required (found 3.8.2).':
            print("FAIL: message not in required form / minimum not 3.9.0")
            sys.exit(1)
        print("PASS: message names 3.9.0 and correct form")
        sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R2.4: the 'found' value must be the library's own reported version string
reproduced VERBATIM, whatever its form (not reformatted/truncated). Use a
4-component odd string like '3.8.11.1' AND a weird string that doesn't match
sqlite_version_info to prove it's the STRING that is reproduced, not a render
of the tuple."""
import sys
from unittest import mock
from django.core.exceptions import ImproperlyConfigured
import django.db.backends.sqlite3.base as base
Database = base.Database
# version string deliberately unusual; verbatim reproduction required
weird = '3.8.11.1'
with mock.patch.object(Database, 'sqlite_version_info', (3, 8, 11, 1)), \
     mock.patch.object(Database, 'sqlite_version', weird):
    try:
        base.check_sqlite_version()
        print("FAIL: not rejected")
        sys.exit(1)
    except ImproperlyConfigured as e:
        msg = str(e)
        print("msg:", repr(msg))
        expected_tail = '(found %s).' % weird
        if not msg.endswith(expected_tail):
            print("FAIL: found value not verbatim; want tail", repr(expected_tail))
            sys.exit(1)
        print("PASS: verbatim found string reproduced")
        sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R3.1/R3.2: the check runs automatically at import time of the base module,
and the exception type for an unsupported version is exactly
ImproperlyConfigured. Verify: (a) module has check_sqlite_version and calls it
at import (module imports cleanly on real >=3.9 lib), (b) function exists and
raises ImproperlyConfigured subtype of django.core.exceptions."""
import sys, inspect
import django.db.backends.sqlite3.base as base
from django.core.exceptions import ImproperlyConfigured
# (a) the module imported successfully = version check ran at import time
src = inspect.getsource(base)
if 'check_sqlite_version()' not in src:
    print("FAIL: no module-level check_sqlite_version() call in source")
    sys.exit(1)
# ensure a top-level (import-time) invocation exists (not just the def)
lines = [l for l in src.splitlines() if l.strip() == 'check_sqlite_version()']
if not lines:
    print("FAIL: check not invoked at module top level")
    sys.exit(1)
print("OK: module-level check_sqlite_version() call present; module imported")
# (b) exception type
from unittest import mock
Database = base.Database
with mock.patch.object(Database, 'sqlite_version_info', (3, 8, 0)), \
     mock.patch.object(Database, 'sqlite_version', '3.8.0'):
    try:
        base.check_sqlite_version()
        print("FAIL: no raise")
        sys.exit(1)
    except ImproperlyConfigured:
        print("PASS: raises ImproperlyConfigured")
        sys.exit(0)
    except Exception as e:
        print("FAIL: wrong type", type(e).__name__)
        sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (R1.1, R2.1/2.2/2.4): the hidden-test boundary case.
mock sqlite_version_info=(3,8,11,1), sqlite_version='3.8.11.1' -> below 3.9.0
=> must raise ImproperlyConfigured with the exact message reporting 3.9.0
required and the verbatim found string '3.8.11.1'.
HOLDS on patched, FAILS at base (base minimum is (3,8,3): (3,8,11,1) is NOT
< (3,8,3), so base does not raise at all)."""
import sys
from unittest import mock
from django.core.exceptions import ImproperlyConfigured
import django.db.backends.sqlite3.base as base

Database = base.Database
want = 'SQLite 3.9.0 or later is required (found 3.8.11.1).'
with mock.patch.object(Database, 'sqlite_version_info', (3, 8, 11, 1)), \
     mock.patch.object(Database, 'sqlite_version', '3.8.11.1'):
    try:
        base.check_sqlite_version()
        print("FAIL: no exception raised for (3,8,11,1)")
        sys.exit(1)
    except ImproperlyConfigured as e:
        got = str(e)
        print("raised ImproperlyConfigured:", repr(got))
        if got == want:
            print("PASS: exact expected message")
            sys.exit(0)
        print("FAIL: message mismatch, want", repr(want))
        sys.exit(1)
    except Exception as e:
        print("FAIL: wrong exception type:", type(e).__name__, e)
        sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Change: raise SQLite minimum from 3.8.3 to 3.9.0 in check_sqlite_version() (django/db/backends/sqlite3/base.py), updating both the boundary and the message.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1/R2.1/R2.2/R2.4, POSITIVE CONTROL): hidden-test case mock sqlite_version_info=(3,8,11,1), sqlite_version='3.8.11.1' -> raises ImproperlyConfigured with exact msg 'SQLite 3.9.0 or later is required (found 3.8.11.1).'. HOLDS patched; FAILS at base (base minimum (3,8,3): (3,8,11,1) NOT < (3,8,3) so base does not raise) -> prepatch_reproduced=true.
- probe_2 (R1.2): (3,8,7) — at/above old min but below 3.9.0 — rejected.
- probe_3 (R1.4): (3,9,0) and (3,11,0) accepted without raising.
- probe_4 (R1.3): numeric ordering — (3,10,0) accepted (lexical '3.10'<'3.9' would wrongly reject), (3,8,20) rejected.
- probe_5 (R2.1/R2.3): message names 3.9.0 exactly and NOT old 3.8.3; correct form.
- probe_6 (R2.4): verbatim reproduction of the reported version string in 'found ...'.
- probe_7 (R3.1/R3.2): module-level import-time check present; exception type is exactly ImproperlyConfigured.

Weak candidates (BOTH REJECTED -> suite discriminates):
- weakA_oldmsg: bumps boundary to (3,9,0) but leaves the OLD '3.8.3' message text. Rejected by probe_1 (message mismatch) and probe_5 (still names 3.8.3). Passes the pure-boundary probes, confirming they don't over-constrain.
- weakB_lexical: uses lexical string compare `Database.sqlite_version < '3.9.0'` instead of numeric version_info. Rejected by ALL probes — on the real image lib (3.45.3) '3.45.3' < '3.9.0' lexically, so the backend raises at import time and the module can't even load. This directly exercises the R1.3 numeric-vs-lexical criterion.

All 7 probes hold on patched; positive control discriminates base vs patched; >=1 requirements-permitted-but-wrong candidate rejected. Verdict SOUND.

Note: meta.json records G-PANEL-3=fail (LEAKAGE) regarding the requirements' emphasis on >3-component version strings mirroring the hidden test's 3.8.11.1 input. That is a separate leakage concern outside G-EQ (spec-too-weak/discrimination) scope; the G-EQ requirement-fidelity dimension is sound.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control (R1.1, R2.1/2.2/2.4): the hidden-test boundary case.
mock sqlite_version_info=(3,8,11,1), sqlite_version='3.8.11.1' -> below 3.9.0
=> must raise ImproperlyConfigured with the exact message reporting 3.9.0
required and the verbatim found string '3.8.11.1'.
HOLDS on patched, FAILS at base (base minimum is (3,8,3): (3,8,11,1) is NOT
< (3,8,3), so base does not raise at all)."""
import sys
from unittest import mock
from django.core.exceptions import ImproperlyConfigured
import django.db.backends.sqlite3.base as base

Database = base.Database
want = 'SQLite 3.9.0 or later is required (found 3.8.11.1).'
with mock.patch.object(Database, 'sqlite_version_info', (3, 8, 11, 1)), \
     mock.patch.object(Database, 'sqlite_version', '3.8.11.1'):
    try:
        base.check_sqlite_version()
        print("FAIL: no exception raised for (3,8,11,1)")
        sys.exit(1)
    except ImproperlyConfigured as e:
        got = str(e)
        print("raised ImproperlyConfigured:", repr(got))
        if got == want:
            print("PASS: exact expected message")
            sys.exit(0)
        print("FAIL: message mismatch, want", repr(want))
        sys.exit(1)
    except Exception as e:
        print("FAIL: wrong exception type:", type(e).__name__, e)
        sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Change: raise SQLite minimum from 3.8.3 to 3.9.0 in check_sqlite_version() (django/db/backends/sqlite3/base.py), updating both the boundary and the message.

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.1/R2.1/R2.2/R2.4, POSITIVE CONTROL): hidden-test case mock sqlite_version_info=(3,8,11,1), sqlite_version='3.8.11.1' -> raises ImproperlyConfigured with exact msg 'SQLite 3.9.0 or later is required (found 3.8.11.1).'. HOLDS patched; FAILS at base (base minimum (3,8,3): (3,8,11,1) NOT < (3,8,3) so base does not raise) -> prepatch_reproduced=true.
- probe_2 (R1.2): (3,8,7) — at/above old min but below 3.9.0 — rejected.
- probe_3 (R1.4): (3,9,0) and (3,11,0) accepted without raising.
- probe_4 (R1.3): numeric ordering — (3,10,0) accepted (lexical '3.10'<'3.9' would wrongly reject), (3,8,20) rejected.
- probe_5 (R2.1/R2.3): message names 3.9.0 exactly and NOT old 3.8.3; correct form.
- probe_6 (R2.4): verbatim reproduction of the reported version string in 'found ...'.
- probe_7 (R3.1/R3.2): module-level import-time check present; exception type is exactly ImproperlyConfigured.

Weak candidates (BOTH REJECTED -> suite discriminates):
- weakA_oldmsg: bumps boundary to (3,9,0) but leaves the OLD '3.8.3' message text. Rejected by probe_1 (message mismatch) and probe_5 (still names 3.8.3). Passes the pure-boundary probes, confirming they don't over-constrain.
- weakB_lexical: uses lexical string compare `Database.sqlite_version < '3.9.0'` instead of numeric version_info. Rejected by ALL probes — on the real image lib (3.45.3) '3.45.3' < '3.9.0' lexically, so the backend raises at import time and the module can't even load. This directly exercises the R1.3 numeric-vs-lexical criterion.

All 7 probes hold on patched; positive control discriminates base vs patched; >=1 requirements-permitted-but-wrong candidate rejected. Verdict SOUND.

Note: meta.json records G-PANEL-3=fail (LEAKAGE) regarding the requirements' emphasis on >3-component version strings mirroring the hidden test's 3.8.11.1 input. That is a separate leakage concern outside G-EQ (spec-too-weak/discrimination) scope; the G-EQ requirement-fidelity dimension is sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patched probe HOLDS (exit 0): 3.8.3 rejected with correct message, 3.9.0 and 3.10.0 accepted. Base probe VIOLATED (3.8.3 accepted), confirming the requirements pin the actually-changed boundary. Requirements are a slightly verbose but accurate description of a one-line boundary bump.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the public change (raise SQLite minimum to 3.9.0; JSON1 + expression indexes) which is fully in the problem_statement. Localization to check_sqlite_version() in base.py raising ImproperlyConfigured is legitimate. The hidden test's specific mock input 3.8.11.1 / (3,8,11,1) is NOT reproduced anywhere; no test names/paths/ids, no verbatim test code, no fix-invented identifiers (the gold merely bumps a version tuple/message constant). The message template 'SQLite 3.9.0 or later is required (found <version>).' (Req 2.2) matches the gold output string, but it is the natural behavioral specification of the required message given the public intent to report minimum + found version, not a reconstruction of the tests. Req 1.3's numeric-vs-lexical comparison prose describes general behavior and does not enumerate the test parametrization or quote the test value.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
