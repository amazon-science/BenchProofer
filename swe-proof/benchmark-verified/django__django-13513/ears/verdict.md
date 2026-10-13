# P2 adversarial audit — django__django-13513

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

Counterexample / evidence:

```
Positive control (probe_1): the FAIL_TO_PASS scenario — inner exception raised whose __context__ was attached but never raised (its __traceback__ is None). PATCHED returns exactly 1 frame; BASE returns 0 frames (chain aborted at the traceback-less context exception), which the debug page would render with a truncated/empty traceback. Candidate A (naive `if tb is None: tb = self.tb` fallback) yields 2 frames for the same case — REJECTED by probe_1 — demonstrating the suite discriminates a requirements-plausible but wrong per-exception-walk fix.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control. Req 1.2/1.3: innermost/context exception with NO traceback
must not abort the chain; the exception that DOES have a traceback still
contributes its frames. Mirrors FAIL_TO_PASS test_innermost_exception_without_traceback.
HOLDS iff exactly 1 frame is returned."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.views.debug import ExceptionReporter

try:
    try:
        raise RuntimeError('Oops')
    except Exception as exc:
        new_exc = RuntimeError('My context')
        exc.__context__ = new_exc  # attached, never raised -> no traceback
        raise
except Exception:
    exc_type, exc_value, tb = sys.exc_info()

reporter = ExceptionReporter(None, exc_type, exc_value, tb)
frames = reporter.get_traceback_frames()
print("num frames:", len(frames))
print("context exc has tb:", new_exc.__traceback__ is not None)
assert len(frames) == 1, "expected exactly 1 frame, got %d" % len(frames)
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.4/4.6: multi-exception chain where BOTH have real tracebacks.
Frames = concatenation of per-exception frame lists; total = sum of visible
frames; order = deepest cause first, reported last. We verify count > 1 and
that the reported (last) frame's exception is different from the first (cause)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.views.debug import ExceptionReporter

def raise_cause():
    raise ValueError('the cause')

try:
    try:
        raise_cause()
    except Exception:
        raise RuntimeError('the outer')  # implicit context, has real tb
except Exception:
    exc_type, exc_value, tb = sys.exc_info()

reporter = ExceptionReporter(None, exc_type, exc_value, tb)
frames = reporter.get_traceback_frames()
print("num frames:", len(frames))
# Count how many frames per distinct exc_cause pattern.
# cause chain: outer's cause is ValueError('the cause'); ValueError's cause is None.
first = frames[0]
last = frames[-1]
print("first exc_cause:", first['exc_cause'])
print("last exc_cause:", last['exc_cause'])
# Deepest cause (ValueError) frames come first: its exc_cause is None.
# Reported (RuntimeError) frames come last: its exc_cause is the ValueError.
assert first['exc_cause'] is None, "deepest-cause frames should be first (exc_cause None)"
assert isinstance(last['exc_cause'], ValueError), "reported frames last, exc_cause=the cause"
assert len(frames) >= 2, "expected frames from both exceptions"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.4: per-frame cause attribution. Every frame belonging to a given
exception must report exc_cause = that exception's resolved cause and
exc_cause_explicit = that exception's __cause__. With an explicit
'raise ... from', the reported exception's frames must carry a truthy
exc_cause_explicit; the cause's own frames must carry falsy explicit."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.views.debug import ExceptionReporter

def raise_cause():
    raise ValueError('cause')

try:
    try:
        raise_cause()
    except Exception as e:
        raise RuntimeError('outer') from e  # explicit cause
except Exception:
    exc_type, exc_value, tb = sys.exc_info()

reporter = ExceptionReporter(None, exc_type, exc_value, tb)
frames = reporter.get_traceback_frames()
print("num frames:", len(frames))
# reported exception (RuntimeError) frames -> exc_cause is the ValueError, explicit truthy
# cause (ValueError) frames -> exc_cause None, explicit falsy
runtime_frames = [f for f in frames if isinstance(f['exc_cause'], ValueError)]
value_frames = [f for f in frames if f['exc_cause'] is None]
print("runtime(explicit-cause) frames:", len(runtime_frames))
print("value(no-cause) frames:", len(value_frames))
assert runtime_frames, "expected reported-exception frames with the ValueError cause"
for f in runtime_frames:
    assert f['exc_cause_explicit'], "explicit raise-from frames must be truthy explicit"
for f in value_frames:
    assert not f['exc_cause_explicit'], "cause frames (no __cause__) must be falsy explicit"
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.2: raise ... from None suppresses context -> no causing exception, so
the debug page must NOT resurface the suppressed context. Verify the chain built
by get_traceback_frames stops at the reported exception (single frame group,
exc_cause None) even though __context__ is set but suppressed."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.views.debug import ExceptionReporter

try:
    try:
        raise ValueError('ctx')
    except Exception:
        raise RuntimeError('outer') from None  # suppress context
except Exception:
    exc_type, exc_value, tb = sys.exc_info()

print("suppress_context:", exc_value.__suppress_context__)
print("has context:", exc_value.__context__ is not None)
reporter = ExceptionReporter(None, exc_type, exc_value, tb)
frames = reporter.get_traceback_frames()
print("num frames:", len(frames))
# No frame should reference the suppressed ValueError context as its cause.
for f in frames:
    assert f['exc_cause'] is None, "suppressed context must not appear as exc_cause: %r" % (f['exc_cause'],)
    assert not f['exc_cause_explicit'], "no explicit cause expected"
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.5 + 5.3: cycle detection. When following the cause chain would revisit
an exception, the system must emit the existing cycle warning and stop (no
infinite loop), returning a well-formed frame list. Build a cycle via
__context__ referencing back."""
import sys
import warnings
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.views.debug import ExceptionReporter

try:
    raise RuntimeError('a')
except Exception as exc_a:
    a = exc_a
    a_type, a_val, a_tb = sys.exc_info()
try:
    raise RuntimeError('b')
except Exception as exc_b:
    b = exc_b

# Make a cycle: a's context is b, b's context is a
a.__context__ = b
b.__context__ = a
a.__suppress_context__ = False
b.__suppress_context__ = False

reporter = ExceptionReporter(None, a_type, a, a_tb)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    frames = reporter.get_traceback_frames()  # must terminate
print("num frames:", len(frames))
print("warnings:", [str(x.message) for x in w])
assert any('Cycle in the exception chain' in str(x.message) for x in w), "expected cycle warning"
assert isinstance(frames, list), "must return a list"
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.5 + 5.4: empty/no-exception + full HTML report for a chain including an
exception without a traceback. (a) no exception -> empty frame list.
(b) the innermost-without-tb case renders HTML with the 'During handling'
notice naming the context exception, and exception type/value/traceback/request
sections all present (Req 5.4)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[], SECRET_KEY='x')
django.setup()
from django.views.debug import ExceptionReporter

# (a) no exceptions supplied
rep0 = ExceptionReporter(None, None, None, None)
frames0 = rep0.get_traceback_frames()
print("empty frames:", frames0)
assert frames0 == [], "no exceptions -> empty list"

# (b) innermost without traceback, full HTML
try:
    try:
        raise RuntimeError('Oops')
    except Exception as exc:
        new_exc = RuntimeError('My context')
        exc.__context__ = new_exc
        raise
except Exception:
    exc_type, exc_value, tb = sys.exc_info()

reporter = ExceptionReporter(None, exc_type, exc_value, tb)
html = reporter.get_traceback_html()
import re
# normalize whitespace (mirrors assertInHTML semantics) for robust tag matching
norm = re.sub(r'\s+', ' ', html)
checks = [
    '<h1>RuntimeError </h1>',  # normalized <h1>RuntimeError</h1>
    '<pre class="exception_value">Oops</pre>',
    '<th>Exception Type:</th>',
    '<th>Exception Value:</th>',
    '<h2>Traceback ',
    '<h2>Request information</h2>',
    '<p>Request data not supplied</p>',
    'During handling of the above exception (My context), another exception occurred',
]
for c in checks:
    ok = c in norm
    print("present:", ok, repr(c[:45]))
    assert ok, "missing from HTML: %r" % c
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req 1.2/1.3: innermost/context exception with NO traceback
must not abort the chain; the exception that DOES have a traceback still
contributes its frames. Mirrors FAIL_TO_PASS test_innermost_exception_without_traceback.
HOLDS iff exactly 1 frame is returned."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.views.debug import ExceptionReporter

try:
    try:
        raise RuntimeError('Oops')
    except Exception as exc:
        new_exc = RuntimeError('My context')
        exc.__context__ = new_exc  # attached, never raised -> no traceback
        raise
except Exception:
    exc_type, exc_value, tb = sys.exc_info()

reporter = ExceptionReporter(None, exc_type, exc_value, tb)
frames = reporter.get_traceback_frames()
print("num frames:", len(frames))
print("context exc has tb:", new_exc.__traceback__ is not None)
assert len(frames) == 1, "expected exactly 1 frame, got %d" % len(frames)
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-13513, module django/views/debug.py, ExceptionReporter.get_traceback_frames. Base_commit 6599608c4d0. All runs completed in the official image.

Probe -> criterion -> results (patched / base / candA):
- probe_1 (POS CTRL): Req 1.2/1.3 — context exc with no traceback must not abort chain; exactly 1 frame. PATCHED HOLD(1 frame) / BASE FAIL(0 frames) / candA FAIL(2 frames).
- probe_2: Req 1.1/1.4/4.6 — both exceptions have real tb; frames = concatenation, order deepest-cause-first (exc_cause None) then reported-last (exc_cause=the cause), total>=2. PATCHED HOLD(3 frames, order correct) / candA HOLD (not discriminating on this case).
- probe_3: Req 2.1/2.2/2.4 — explicit raise-from: reported-exception frames carry truthy exc_cause_explicit and the ValueError cause; cause's own frames carry falsy explicit + None cause. PATCHED HOLD.
- probe_4: Req 3.1/3.2 — raise ... from None suppresses context; no frame's exc_cause resurfaces the suppressed context; explicit falsy. PATCHED HOLD.
- probe_5: Req 3.5/5.3 — cyclic __context__ reference: emits the existing 'Cycle in the exception chain detected' warning, terminates, returns a well-formed list. PATCHED HOLD.
- probe_6: Req 4.5 (no exceptions -> empty list) + Req 5.4 (full HTML report for a chain incl. a traceback-less exception: exception type/value, Traceback section, Request information, 'During handling of the above exception (My context)' notice). PATCHED HOLD. (Whitespace-normalized HTML matching mirrors assertInHTML.)

All 6 probes HOLD on the gold-patched tree. Positive control discriminates (HOLD patched, FAIL base — prepatch reproduced). Candidate A is a plausible partial fix a weak reading permits (keep the buggy loop but backfill tb from self.tb when the popped exception has no traceback); it is REJECTED by probe_1 (produces 2 frames instead of 1) — so the suite is not a rubber stamp. No too-weak (probe-conforming yet non-resolving) patch was found; suite discriminates the wrong fix. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Positive control (probe_1): the FAIL_TO_PASS scenario — inner exception raised whose __context__ was attached but never raised (its __traceback__ is None). PATCHED returns exactly 1 frame; BASE returns 0 frames (chain aborted at the traceback-less context exception), which the debug page would render with a truncated/empty traceback. Candidate A (naive `if tb is None: tb = self.tb` fallback) yields 2 frames for the same case — REJECTED by probe_1 — demonstrating the suite discriminates a requirements-plausible but wrong per-exception-walk fix.
```

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
"""Positive control. Req 1.2/1.3: innermost/context exception with NO traceback
must not abort the chain; the exception that DOES have a traceback still
contributes its frames. Mirrors FAIL_TO_PASS test_innermost_exception_without_traceback.
HOLDS iff exactly 1 frame is returned."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={}, INSTALLED_APPS=[])
django.setup()
from django.views.debug import ExceptionReporter

try:
    try:
        raise RuntimeError('Oops')
    except Exception as exc:
        new_exc = RuntimeError('My context')
        exc.__context__ = new_exc  # attached, never raised -> no traceback
        raise
except Exception:
    exc_type, exc_value, tb = sys.exc_info()

reporter = ExceptionReporter(None, exc_type, exc_value, tb)
frames = reporter.get_traceback_frames()
print("num frames:", len(frames))
print("context exc has tb:", new_exc.__traceback__ is not None)
assert len(frames) == 1, "expected exactly 1 frame, got %d" % len(frames)
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-13513, module django/views/debug.py, ExceptionReporter.get_traceback_frames. Base_commit 6599608c4d0. All runs completed in the official image.

Probe -> criterion -> results (patched / base / candA):
- probe_1 (POS CTRL): Req 1.2/1.3 — context exc with no traceback must not abort chain; exactly 1 frame. PATCHED HOLD(1 frame) / BASE FAIL(0 frames) / candA FAIL(2 frames).
- probe_2: Req 1.1/1.4/4.6 — both exceptions have real tb; frames = concatenation, order deepest-cause-first (exc_cause None) then reported-last (exc_cause=the cause), total>=2. PATCHED HOLD(3 frames, order correct) / candA HOLD (not discriminating on this case).
- probe_3: Req 2.1/2.2/2.4 — explicit raise-from: reported-exception frames carry truthy exc_cause_explicit and the ValueError cause; cause's own frames carry falsy explicit + None cause. PATCHED HOLD.
- probe_4: Req 3.1/3.2 — raise ... from None suppresses context; no frame's exc_cause resurfaces the suppressed context; explicit falsy. PATCHED HOLD.
- probe_5: Req 3.5/5.3 — cyclic __context__ reference: emits the existing 'Cycle in the exception chain detected' warning, terminates, returns a well-formed list. PATCHED HOLD.
- probe_6: Req 4.5 (no exceptions -> empty list) + Req 5.4 (full HTML report for a chain incl. a traceback-less exception: exception type/value, Traceback section, Request information, 'During handling of the above exception (My context)' notice). PATCHED HOLD. (Whitespace-normalized HTML matching mirrors assertInHTML.)

All 6 probes HOLD on the gold-patched tree. Positive control discriminates (HOLD patched, FAIL base — prepatch reproduced). Candidate A is a plausible partial fix a weak reading permits (keep the buggy loop but backfill tb from self.tb when the popped exception has no traceback); it is REJECTED by probe_1 (produces 2 frames instead of 1) — so the suite is not a rubber stamp. No too-weak (probe-conforming yet non-resolving) patch was found; suite discriminates the wrong fix. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements correctly pin the CHANGED observable behavior (per-exception independent traceback walking + preserved per-frame cause attribution), not a narrow slice. The suppress_context helper (from the original issue) is preserved and correctly required. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior detected. F2P test is test_innermost_exception_without_traceback, which Req 1.2/1.3 directly model.

Counterexample / evidence:

```
None. Base-vs-patched probe divergence exactly matches the requirements: base drops the reported exception's frames when a chain exception lacks a traceback (exit 1), patched preserves them (exit 0, num frames=1).
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the gold edit's behavior (per-exception traceback walking, cause/suppress_context resolution) and localize to django/views/debug.py and the existing method get_traceback_frames() using only pre-existing identifiers (exc_cause, exc_cause_explicit, __cause__, __context__, __suppress_context__, __traceback_hide__). The fix-invented method names (get_exception_traceback_frames, _get_explicit_or_implicit_cause) are NOT disclosed. No test file paths, test function/class names (e.g. test_innermost_exception_without_traceback / ExceptionReporterTests), parametrization ids, or quoted test/gold code appear. The 'During handling of the above exception (…), another exception occurred' phrasing is a standard Python/Django-template chaining notice present in the codebase, not a test-invented string. Requirement 1's traceback-None scenario exceeds the suppress_context-only problem_statement, but that is legitimate translation of gold-edit behavior into requirements, not transmission of the hidden test; the specific test setup (manual __context__ assignment + re-raise, len(frames)==1 assertion) is not reconstructable from the prose. Behavior-level enumeration, single non-parametrized F2P test — no case-mirroring leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
