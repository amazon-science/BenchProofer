# P2 adversarial audit — django__django-13516

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
import sys
from django.core.management.base import OutputWrapper

class FakeStream:
    def __init__(self):
        self.flushed = 0
        self.data = []
    def write(self, s):
        self.data.append(s)
    def flush(self):
        self.flushed += 1

s = FakeStream()
w = OutputWrapper(s)
w.flush()
print("flush count on underlying stream:", s.flushed)
# Req1.1/1.2: flush must reach underlying stream exactly once (not a no-op)
sys.exit(0 if s.flushed == 1 else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from django.core.management.base import OutputWrapper

# Req1.3/1.4: stream without flush -> no error, no attempt to call flush
class NoFlushStream:
    def __init__(self):
        self.data = []
    def write(self, s):
        self.data.append(s)
    # deliberately no flush attribute

s = NoFlushStream()
w = OutputWrapper(s)
try:
    w.flush()
except Exception as e:
    print("ERROR raised:", repr(e))
    sys.exit(1)
print("no error; hasattr flush on stream:", hasattr(s, 'flush'))
# ensure the wrapper didn't inject a flush onto the stream
sys.exit(0 if not hasattr(s, 'flush') else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from django.core.management.base import OutputWrapper

# Req1.5: after flush(), underlying stream identity + flush support unchanged
class FakeStream:
    def __init__(self):
        self.flushed = 0
    def write(self, s):
        pass
    def flush(self):
        self.flushed += 1

s = FakeStream()
w = OutputWrapper(s)
before_id = id(w._out)
before_has = hasattr(w._out, 'flush')
w.flush()
after_id = id(w._out)
after_has = hasattr(w._out, 'flush')
print("id before/after:", before_id, after_id, "flush support before/after:", before_has, after_has)
print("same object:", w._out is s)
ok = before_id == after_id and before_has and after_has and (w._out is s)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from io import StringIO
from django.core.management.base import OutputWrapper

# Req2: write forwards styled text, appends ending when missing, no double ending
s = StringIO()
w = OutputWrapper(s, ending='\n')

s.truncate(0); s.seek(0)
w.write('hello')
r1 = s.getvalue()
print("no-ending msg ->", repr(r1))

s.truncate(0); s.seek(0)
w.write('world\n')
r2 = s.getvalue()
print("already-ending msg ->", repr(r2))

# style func applied
s.truncate(0); s.seek(0)
w.write('x', style_func=lambda m: '[' + m + ']')
r3 = s.getvalue()
print("styled ->", repr(r3))

ok = (r1 == 'hello\n') and (r2 == 'world\n') and (r3 == '[x\n]')
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from django.core.management.base import OutputWrapper

# Req3: attribute delegation + isatty
class FakeStream:
    def __init__(self, tty):
        self._tty = tty
        self.custom_attr = 'delegated_value'
    def write(self, s):
        pass
    def isatty(self):
        return self._tty

s = FakeStream(True)
w = OutputWrapper(s)
print("delegated attr:", w.custom_attr)
print("isatty (tty stream):", w.isatty())

# stream without isatty -> falsey
class NoTty:
    def write(self, s):
        pass
w2 = OutputWrapper(NoTty())
print("isatty (no isatty):", w2.isatty())

ok = (w.custom_attr == 'delegated_value') and (w.isatty() is True) and (not w2.isatty())
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from django.core.management.base import OutputWrapper

class FakeStream:
    def __init__(self):
        self.flushed = 0
        self.data = []
    def write(self, s):
        self.data.append(s)
    def flush(self):
        self.flushed += 1

s = FakeStream()
w = OutputWrapper(s)
w.flush()
print("flush count on underlying stream:", s.flushed)
# Req1.1/1.2: flush must reach underlying stream exactly once (not a no-op)
sys.exit(0 if s.flushed == 1 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

OutputWrapper.flush() fix for django__django-13516. 5 probes: probe_1 (Req1.1/1.2 flush reaches underlying stream exactly once, not no-op), probe_2 (Req1.3/1.4 stream lacking flush -> no error, no flush call), probe_3 (Req1.5 stream identity+flush-support unchanged after flush), probe_4 (Req2 write forwards styled text, appends ending when missing, no double ending), probe_5 (Req3 attribute delegation + isatty incl. falsey when no isatty). All 5 HOLD on gold-patched tree. Positive control = probe_1: FAILS at base (flush count 0, base flush() is io.TextIOBase no-op), HOLDS patched (flush count 1) -> discriminates. Candidate wrong-fix 'unguarded_flush' (flush() calls self._out.flush() without hasattr guard): probe suite REJECTS it via probe_2 (AttributeError on stream without flush, violating Req1.3/1.4) -> suite discriminates the lazy fix a weak reading permits. Suite is discriminating; requirements are faithful and not too weak.

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
import sys
from django.core.management.base import OutputWrapper

class FakeStream:
    def __init__(self):
        self.flushed = 0
        self.data = []
    def write(self, s):
        self.data.append(s)
    def flush(self):
        self.flushed += 1

s = FakeStream()
w = OutputWrapper(s)
w.flush()
print("flush count on underlying stream:", s.flushed)
# Req1.1/1.2: flush must reach underlying stream exactly once (not a no-op)
sys.exit(0 if s.flushed == 1 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

OutputWrapper.flush() fix for django__django-13516. 5 probes: probe_1 (Req1.1/1.2 flush reaches underlying stream exactly once, not no-op), probe_2 (Req1.3/1.4 stream lacking flush -> no error, no flush call), probe_3 (Req1.5 stream identity+flush-support unchanged after flush), probe_4 (Req2 write forwards styled text, appends ending when missing, no double ending), probe_5 (Req3 attribute delegation + isatty incl. falsey when no isatty). All 5 HOLD on gold-patched tree. Positive control = probe_1: FAILS at base (flush count 0, base flush() is io.TextIOBase no-op), HOLDS patched (flush count 1) -> discriminates. Candidate wrong-fix 'unguarded_flush' (flush() calls self._out.flush() without hasattr guard): probe suite REJECTS it via probe_2 (AttributeError on stream without flush, violating Req1.3/1.4) -> suite discriminates the lazy fix a weak reading permits. Suite is discriminating; requirements are faithful and not too weak.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary check: requirements pin the CHANGED observable behavior (flush relayed to underlying stream, with hasattr guard) as the biconditional core in Req 1, not a narrow slice or an unrelated helper. Preservation requirements (Req 2/3) correctly bound the unchanged surface. No requirement mandates behavior the patched code lacks, forbids behavior it has, or invents behavior. Probe HOLDS patched / VIOLATED base — clean discriminator matching Req 1.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes OutputWrapper.flush() relaying to the underlying stream's flush when supported (hasattr guard), no-op-free, plus preserving write/styling/isatty/__getattr__ delegation. All of this is either in the public problem_statement (flush doesn't work, migrate progress buffered) or legitimate localization of the class under change (OutputWrapper in django.core.management.base). No hidden-test content transmitted: no test function name (test_outputwrapper_flush), no test/command file paths (tests/user_commands/tests.py, management/commands/outputwrapper.py), no StringIO/mock.patch scaffolding, no 'Working...'/'OK' literals, no FAIL_TO_PASS/PASS_TO_PASS ids, no gold-patch verbatim lines, and no fix-invented identifiers (the gold adds a flush method using the private _out attr and hasattr, which the prose describes behaviorally without naming _out). Requirement enumerations track behavior (flush supported vs not), not the single test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
