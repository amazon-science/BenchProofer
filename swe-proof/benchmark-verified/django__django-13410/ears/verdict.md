# P2 adversarial audit — django__django-13410

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control. Req1.1/1.2/1.3: lock() with LOCK_EX on an unlocked file
returns the boolean True (identical to True). HOLDS patched, FAILS at base
(base returns None==0 -> False)."""
import os, tempfile, sys
from django.core.files import locks

d = tempfile.mkdtemp()
p = os.path.join(d, "f")
f = open(p, "wb")
ret = locks.lock(f, locks.LOCK_EX)
print("lock(LOCK_EX) returned:", repr(ret), "type:", type(ret).__name__)
locks.unlock(f)
f.close()
if ret is True:
    print("HOLDS: returned True (identical)")
    sys.exit(0)
print("VIOLATED: not identical to True")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3: lock() with LOCK_EX|LOCK_NB on a file already exclusively
locked by another handle returns the boolean False (identical to False)."""
import os, tempfile, sys
from django.core.files import locks

d = tempfile.mkdtemp()
p = os.path.join(d, "f")
f1 = open(p, "wb")
assert locks.lock(f1, locks.LOCK_EX) is True, "setup: first EX lock must succeed"
f2 = open(p, "wb")
ret = locks.lock(f2, locks.LOCK_EX | locks.LOCK_NB)
print("nonblocking EX on locked file returned:", repr(ret), "type:", type(ret).__name__)
locks.unlock(f1)
f1.close(); f2.close()
if ret is False:
    print("HOLDS: returned False (identical)")
    sys.exit(0)
print("VIOLATED: expected False identity")
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.4: LOCK_SH|LOCK_NB request on a file already exclusively locked by
another handle returns False. Req1.5: SH|NB on a file already SH-locked -> True.
Both compatibility semantics in one probe."""
import os, tempfile, sys
from django.core.files import locks

d = tempfile.mkdtemp()

# case A: SH|NB against existing EX  -> False
pa = os.path.join(d, "a")
a1 = open(pa, "wb")
assert locks.lock(a1, locks.LOCK_EX) is True
a2 = open(pa, "wb")
retA = locks.lock(a2, locks.LOCK_SH | locks.LOCK_NB)
print("SH|NB vs EX:", repr(retA))

# case B: SH|NB against existing SH -> True (shared compatible)
pb = os.path.join(d, "b")
open(pb, "wb").close()  # ensure file exists
b1 = open(pb, "rb")
assert locks.lock(b1, locks.LOCK_SH) is True
b2 = open(pb, "rb")
retB = locks.lock(b2, locks.LOCK_SH | locks.LOCK_NB)
print("SH|NB vs SH:", repr(retB))

for fh in (a1, a2, b1, b2):
    try: locks.unlock(fh)
    except Exception: pass
    fh.close()

if retA is False and retB is True:
    print("HOLDS")
    sys.exit(0)
print("VIOLATED")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2/3.3: unlock() returns boolean True (identical) after releasing an
acquired lock. Also Req1.4: LOCK_SH returns True."""
import os, tempfile, sys
from django.core.files import locks

d = tempfile.mkdtemp()
p = os.path.join(d, "f")
f = open(p, "rb") if False else open(p, "wb")

sh_ok = locks.lock(f, locks.LOCK_SH)
print("lock(LOCK_SH) returned:", repr(sh_ok))
ret = locks.unlock(f)
print("unlock returned:", repr(ret), "type:", type(ret).__name__)
f.close()

if ret is True and sh_ok is True:
    print("HOLDS")
    sys.exit(0)
print("VIOLATED")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4.1/4.2: locks module importable from the file utilities package and
exposes lock, unlock, LOCK_EX, LOCK_SH, LOCK_NB with the fcntl values on POSIX.
Req2.5: a non-would-block error propagates (lock on a bad fd raises, is NOT
swallowed into a boolean)."""
import sys
from django.core.files import locks
import fcntl

# Req4.1 exports + fcntl-sourced constants
for name in ("lock", "unlock", "LOCK_EX", "LOCK_SH", "LOCK_NB"):
    assert hasattr(locks, name), "missing export: " + name
assert locks.LOCK_EX == fcntl.LOCK_EX
assert locks.LOCK_SH == fcntl.LOCK_SH
assert locks.LOCK_NB == fcntl.LOCK_NB
assert set(locks.__all__) >= {"LOCK_EX", "LOCK_SH", "LOCK_NB", "lock", "unlock"}
print("exports and constants OK")

# Req2.5: a non-BlockingIOError must propagate, not be turned into a bool.
# Use a stale (closed) fd: fcntl.flock raises OSError (EBADF), not BlockingIOError.
import os, tempfile
d = tempfile.mkdtemp()
fh = open(os.path.join(d, "x"), "wb")
badfd = fh.fileno()
fh.close()  # fd is now invalid -> EBADF
raised = False
try:
    r = locks.lock(badfd, locks.LOCK_EX)
    print("lock(stale fd) returned:", repr(r), "(should have raised)")
except BlockingIOError:
    print("VIOLATED: EBADF misclassified as BlockingIOError")
    sys.exit(1)
except OSError as e:
    raised = True
    print("propagated OSError:", e.errno)

if raised:
    print("HOLDS")
    sys.exit(0)
print("VIOLATED: error was swallowed into a boolean")
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req1.1/1.2/1.3: lock() with LOCK_EX on an unlocked file
returns the boolean True (identical to True). HOLDS patched, FAILS at base
(base returns None==0 -> False)."""
import os, tempfile, sys
from django.core.files import locks

d = tempfile.mkdtemp()
p = os.path.join(d, "f")
f = open(p, "wb")
ret = locks.lock(f, locks.LOCK_EX)
print("lock(LOCK_EX) returned:", repr(ret), "type:", type(ret).__name__)
locks.unlock(f)
f.close()
if ret is True:
    print("HOLDS: returned True (identical)")
    sys.exit(0)
print("VIOLATED: not identical to True")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes POSIX lock/unlock in django/core/files/locks.py: fcntl.flock returns None (not 0) on success and raises on failure, so base code (ret==0) always reported False. Gold: try flock -> True, except BlockingIOError -> False; unlock -> flock(LOCK_UN); return True.

5 probes (all HOLD on patched tree):
- probe_1 (POSITIVE CONTROL, Req1.1/1.2/1.3): lock(LOCK_EX) on unlocked file returns identical True. HOLDS patched, FAILS at base (returns False). prepatch_reproduced=true.
- probe_2 (Req2.1/2.2/2.3): LOCK_EX|LOCK_NB on already-EX-locked file returns identical False. Base: setup lock fails.
- probe_3 (Req2.4 + Req1.5): SH|NB vs existing EX -> False; SH|NB vs existing SH -> True (shared compatibility). Base fails at setup.
- probe_4 (Req3.1/3.2/3.3 + Req1.4): LOCK_SH -> True and unlock -> identical True. Base: both False.
- probe_5 (Req4.1/4.2 exports+fcntl constants + Req2.5 error propagation): stale-fd EBADF OSError propagates, not swallowed into a bool. Correctly HOLDS at base too (API-preservation/regression leg).

Candidate wrong patches, both REJECTED by the suite:
- weak_broad (except Exception instead of except BlockingIOError): probe_5 REJECTS it — EBADF gets swallowed into False, violating Req2.5.
- weak_truthy (returns int 1/0 instead of bool): probes 1 & 4 REJECT it — not identical to True/False, violating Req1.2/2.2/3.2.

No requirements-conforming patch found that would fail the hidden tests; suite discriminates both plausible wrong readings. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control. Req1.1/1.2/1.3: lock() with LOCK_EX on an unlocked file
returns the boolean True (identical to True). HOLDS patched, FAILS at base
(base returns None==0 -> False)."""
import os, tempfile, sys
from django.core.files import locks

d = tempfile.mkdtemp()
p = os.path.join(d, "f")
f = open(p, "wb")
ret = locks.lock(f, locks.LOCK_EX)
print("lock(LOCK_EX) returned:", repr(ret), "type:", type(ret).__name__)
locks.unlock(f)
f.close()
if ret is True:
    print("HOLDS: returned True (identical)")
    sys.exit(0)
print("VIOLATED: not identical to True")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes POSIX lock/unlock in django/core/files/locks.py: fcntl.flock returns None (not 0) on success and raises on failure, so base code (ret==0) always reported False. Gold: try flock -> True, except BlockingIOError -> False; unlock -> flock(LOCK_UN); return True.

5 probes (all HOLD on patched tree):
- probe_1 (POSITIVE CONTROL, Req1.1/1.2/1.3): lock(LOCK_EX) on unlocked file returns identical True. HOLDS patched, FAILS at base (returns False). prepatch_reproduced=true.
- probe_2 (Req2.1/2.2/2.3): LOCK_EX|LOCK_NB on already-EX-locked file returns identical False. Base: setup lock fails.
- probe_3 (Req2.4 + Req1.5): SH|NB vs existing EX -> False; SH|NB vs existing SH -> True (shared compatibility). Base fails at setup.
- probe_4 (Req3.1/3.2/3.3 + Req1.4): LOCK_SH -> True and unlock -> identical True. Base: both False.
- probe_5 (Req4.1/4.2 exports+fcntl constants + Req2.5 error propagation): stale-fd EBADF OSError propagates, not swallowed into a bool. Correctly HOLDS at base too (API-preservation/regression leg).

Candidate wrong patches, both REJECTED by the suite:
- weak_broad (except Exception instead of except BlockingIOError): probe_5 REJECTS it — EBADF gets swallowed into False, violating Req2.5.
- weak_truthy (returns int 1/0 instead of bool): probes 1 & 4 REJECT it — not identical to True/False, violating Req1.2/2.2/3.2.

No requirements-conforming patch found that would fail the hidden tests; suite discriminates both plausible wrong readings. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: lock wraps fcntl.flock in try/except BlockingIOError returning True/False; unlock calls flock(LOCK_UN) then returns True unconditionally. Requirements correctly pin the CHANGED observable behavior (boolean status via exception channel, not the ret==0 comparison) rather than a narrow slice. Notably R2.5 correctly captures that only the would-block condition is converted to False and other OSErrors propagate — matching the patch's BlockingIOError-specific except (narrower than the issue's suggested OSError, and R2.5 is faithful to the actual patch, not the issue text). R4 (API preservation, non-POSIX paths untouched) is consistent with the additions-only diff. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally without transmitting hidden test artifacts. No test names (test_exclusive_lock/test_shared_lock), no test file path (tests/files/tests.py), no test fixture (test.png), no class name (FileTests), and no quoted test/gold code appear. The module/function names (locks.py, lock, unlock) and flag constants (LOCK_EX/LOCK_SH/LOCK_NB) plus the fcntl.flock None-vs-raise semantics and literal True/False returns are all PUBLIC via the problem_statement (which even includes a proposed diff returning literal True/False and cites the fcntl docs). Req 1.2/2.2/3.2's 'identical to True/False, not merely truthy' echoes assertIs identity checking but is directly derivable from the public proposed diff's literal boolean returns. The case enumeration (shared/shared compatible -> True; exclusive-held + non-blocking -> False) states standard POSIX advisory-lock compatibility semantics describable from behavior alone, not the test parametrization; it omits the test scaffolding (two handles on same file, assertIs chain). Req 2.5 (catch only the would-block condition, propagate other errors) generalizes the gold's narrower BlockingIOError handling without naming that identifier and is legitimate behavioral translation. No fix-invented identifiers are leaked.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
