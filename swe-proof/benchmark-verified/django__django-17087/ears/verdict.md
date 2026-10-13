# P2 adversarial audit — django__django-17087

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
Base (unpatched) and the weak candidate both emit 'module.Inner.method' for a classmethod bound to nested class Outer.Inner, instead of the required 'module.Outer.Inner.method' (probe_1 FAILS on both).
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1, criteria 1+2 (positive control): a classmethod bound to a NESTED
class must serialize to <module>.<Outer.Inner>.<method>, i.e. include the full
enclosing-class path via __qualname__ — not just the innermost class name.
Exit 0 iff the reference contains the full nested path.
"""
import os
import sys
import tempfile
import textwrap
import importlib

SRC = textwrap.dedent('''
class Outer:
    class Inner:
        @classmethod
        def method(cls):
            return 1
''')

d = tempfile.mkdtemp(prefix="sbu_probe_")
name = "sbu_probe_mod1"
with open(os.path.join(d, name + ".py"), "w") as f:
    f.write(SRC)
sys.path.insert(0, d)
mod = importlib.import_module(name)

from django.db.migrations.serializer import serializer_factory

value = mod.Outer.Inner.method
ser = serializer_factory(value)
ref, imports = ser.serialize()
print("ref     =", repr(ref))
print("imports =", imports)

expected = "%s.Outer.Inner.method" % name
ok = (ref == expected)
print("expected=", repr(expected))
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1, criterion 4: the class-bound-method branch must return imports that
are EXACTLY the single entry 'import <module>'. Uses a nested class.
Exit 0 iff imports == {'import <module>'}.
"""
import os
import sys
import tempfile
import textwrap
import importlib

SRC = textwrap.dedent('''
class Outer:
    class Inner:
        @classmethod
        def method(cls):
            return 1
''')

d = tempfile.mkdtemp(prefix="sbu_probe_")
name = "sbu_probe_mod2"
with open(os.path.join(d, name + ".py"), "w") as f:
    f.write(SRC)
sys.path.insert(0, d)
mod = importlib.import_module(name)

from django.db.migrations.serializer import serializer_factory

ref, imports = serializer_factory(mod.Outer.Inner.method).serialize()
print("ref     =", repr(ref))
print("imports =", imports)

expected_imports = {"import %s" % name}
ok = (imports == expected_imports)
print("expected imports =", expected_imports)
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1, criterion 3: for a TOP-LEVEL class (bare name == qualname), the
reference must be unchanged historical form <module>.<ClassName>.<method>.
Exit 0 iff ref equals that form.
"""
import os
import sys
import tempfile
import textwrap
import importlib

SRC = textwrap.dedent('''
class TopClass:
    @classmethod
    def method(cls):
        return 2
''')

d = tempfile.mkdtemp(prefix="sbu_probe_")
name = "sbu_probe_mod3"
with open(os.path.join(d, name + ".py"), "w") as f:
    f.write(SRC)
sys.path.insert(0, d)
mod = importlib.import_module(name)

from django.db.migrations.serializer import serializer_factory

ref, imports = serializer_factory(mod.TopClass.method).serialize()
print("ref     =", repr(ref))
print("imports =", imports)

expected = "%s.TopClass.method" % name
ok = (ref == expected and imports == {"import %s" % name})
print("expected=", repr(expected))
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2, criterion 2: a plain module-level function must serialize to
<module>.<qualname> with import <module>. (Regression: the non-bound branch.)
Exit 0 iff correct.
"""
import os
import sys
import tempfile
import textwrap
import importlib

SRC = textwrap.dedent('''
def plain_func():
    return 3
''')

d = tempfile.mkdtemp(prefix="sbu_probe_")
name = "sbu_probe_mod4"
with open(os.path.join(d, name + ".py"), "w") as f:
    f.write(SRC)
sys.path.insert(0, d)
mod = importlib.import_module(name)

from django.db.migrations.serializer import serializer_factory

ref, imports = serializer_factory(mod.plain_func).serialize()
print("ref     =", repr(ref))
print("imports =", imports)

expected = "%s.plain_func" % name
ok = (ref == expected and imports == {"import %s" % name})
print("expected=", repr(expected))
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2, criteria 3 & 4: lambdas and local-scope functions must raise
ValueError. Exit 0 iff both raise ValueError.
"""
import sys

from django.db.migrations.serializer import serializer_factory

ok = True

# lambda
f = lambda: 0
try:
    serializer_factory(f).serialize()
    print("lambda: NO ERROR (bad)")
    ok = False
except ValueError as e:
    print("lambda: ValueError ->", e)

# local scope function (<locals> in __qualname__)
def make():
    def local_func():
        return 1
    return local_func

lf = make()
print("local qualname =", lf.__qualname__)
try:
    serializer_factory(lf).serialize()
    print("local: NO ERROR (bad)")
    ok = False
except ValueError as e:
    print("local: ValueError ->", e)

print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 2, criterion 5: unrelated value types serialize byte-for-byte as before.
Spot-check scalars, collections, and an enum. Exit 0 iff all match expected.
"""
import sys
import datetime
from django.db.migrations.serializer import serializer_factory


def ser(v):
    return serializer_factory(v).serialize()[0]


checks = []
checks.append((ser(42), "42"))
checks.append((ser("hi"), "'hi'"))
checks.append((ser([1, 2]), "[1, 2]"))
checks.append((ser({1, 2}), "{1, 2}"))
checks.append((ser((1, 2)), "(1, 2)"))
checks.append((ser(True), "True"))
checks.append((ser(None), "None"))

ok = True
for got, exp in checks:
    good = (got == exp)
    ok = ok and good
    print("got=%r expected=%r %s" % (got, exp, "ok" if good else "MISMATCH"))

# datetime import path sanity
dref, dimp = serializer_factory(datetime.date(2020, 1, 1)).serialize()
print("date ref =", dref, "imports=", dimp)
ok = ok and ("datetime.date(2020, 1, 1)" in dref)

print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1, criteria 1+2 (positive control): a classmethod bound to a NESTED
class must serialize to <module>.<Outer.Inner>.<method>, i.e. include the full
enclosing-class path via __qualname__ — not just the innermost class name.
Exit 0 iff the reference contains the full nested path.
"""
import os
import sys
import tempfile
import textwrap
import importlib

SRC = textwrap.dedent('''
class Outer:
    class Inner:
        @classmethod
        def method(cls):
            return 1
''')

d = tempfile.mkdtemp(prefix="sbu_probe_")
name = "sbu_probe_mod1"
with open(os.path.join(d, name + ".py"), "w") as f:
    f.write(SRC)
sys.path.insert(0, d)
mod = importlib.import_module(name)

from django.db.migrations.serializer import serializer_factory

value = mod.Outer.Inner.method
ser = serializer_factory(value)
ref, imports = ser.serialize()
print("ref     =", repr(ref))
print("imports =", imports)

expected = "%s.Outer.Inner.method" % name
ok = (ref == expected)
print("expected=", repr(expected))
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all criteria. probe_1 (Req1 c1+c2, positive control): nested-class classmethod must serialize to <module>.Outer.Inner.method — HOLDS patched, FAILS base and FAILS weak candidate (discriminates). probe_2 (Req1 c4): imports == exactly {'import <module>'} — HOLDS. probe_3 (Req1 c3): top-level class ref unchanged historical form — HOLDS on patched/base/weak (regression criterion, correctly does not falsely fail). probe_4 (Req2 c2): plain module-level function -> <module>.<qualname> + import — HOLDS. probe_5 (Req2 c3+c4): lambda and <locals> function both raise ValueError — HOLDS. probe_6 (Req2 c5): scalars/collections/datetime serialize byte-identical — HOLDS. Candidate patches exercised: (a) base/unpatched via --base (rejected by probe_1), (b) weak.diff using __qualname__.split('.')[-1] i.e. innermost name only — a plausibly-wrong reading — rejected by probe_1, passes probe_3. Suite discriminates wrong implementations; gold patch (klass.__qualname__) satisfies every criterion. No too-weak candidate found that passes all probes.

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
Base (unpatched) and the weak candidate both emit 'module.Inner.method' for a classmethod bound to nested class Outer.Inner, instead of the required 'module.Outer.Inner.method' (probe_1 FAILS on both).
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
"""Req 1, criteria 1+2 (positive control): a classmethod bound to a NESTED
class must serialize to <module>.<Outer.Inner>.<method>, i.e. include the full
enclosing-class path via __qualname__ — not just the innermost class name.
Exit 0 iff the reference contains the full nested path.
"""
import os
import sys
import tempfile
import textwrap
import importlib

SRC = textwrap.dedent('''
class Outer:
    class Inner:
        @classmethod
        def method(cls):
            return 1
''')

d = tempfile.mkdtemp(prefix="sbu_probe_")
name = "sbu_probe_mod1"
with open(os.path.join(d, name + ".py"), "w") as f:
    f.write(SRC)
sys.path.insert(0, d)
mod = importlib.import_module(name)

from django.db.migrations.serializer import serializer_factory

value = mod.Outer.Inner.method
ser = serializer_factory(value)
ref, imports = ser.serialize()
print("ref     =", repr(ref))
print("imports =", imports)

expected = "%s.Outer.Inner.method" % name
ok = (ref == expected)
print("expected=", repr(expected))
print("HOLDS" if ok else "FAILS")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover all criteria. probe_1 (Req1 c1+c2, positive control): nested-class classmethod must serialize to <module>.Outer.Inner.method — HOLDS patched, FAILS base and FAILS weak candidate (discriminates). probe_2 (Req1 c4): imports == exactly {'import <module>'} — HOLDS. probe_3 (Req1 c3): top-level class ref unchanged historical form — HOLDS on patched/base/weak (regression criterion, correctly does not falsely fail). probe_4 (Req2 c2): plain module-level function -> <module>.<qualname> + import — HOLDS. probe_5 (Req2 c3+c4): lambda and <locals> function both raise ValueError — HOLDS. probe_6 (Req2 c5): scalars/collections/datetime serialize byte-identical — HOLDS. Candidate patches exercised: (a) base/unpatched via --base (rejected by probe_1), (b) weak.diff using __qualname__.split('.')[-1] i.e. innermost name only — a plausibly-wrong reading — rejected by probe_1, passes probe_3. Suite discriminates wrong implementations; gold patch (klass.__qualname__) satisfies every criterion. No too-weak candidate found that passes all probes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified against gold-patched instance image via nl_attack probe and base-commit source. Base branch used klass.__name__ (produces module.Inner.method); patched uses klass.__qualname__ (module.Outer.Inner.method). Requirement 1.2 pins the exact nested-class discriminator that is the whole point of the fix — correct modeling boundary. Req 2's byte-for-byte-identical claim for other value types is faithful since the diff touches only this one line.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to django/db/migrations/serializer.py::FunctionTypeSerializer.serialize and describe the fix behaviorally (use fully-qualified class name / __qualname__ instead of bare __name__ for class-bound methods). All of this is either already public in problem_statement (nested TextChoices classmethod as Field.default; the wrong 'appname.models.Capability.default' vs right 'appname.models.Profile.Capability.default' dotted form) or is legitimate module/behavior naming. __qualname__/__name__ are the actual changed code identifiers, not fix-invented names, and translating what the test checks into behavioral requirements is the intended purpose. No hidden-test content leaks: no test file path (tests/migrations/test_writer.py), no test/fixture names (test_serialize_nested_class_method, WriterTests, NestedChoices), no parametrization ids, no verbatim gold-patch lines (the %s.%s.%s format string and the exact node id 'migrations.test_writer.WriterTests.NestedChoices.method' are absent). The top-level vs nested distinction (Req 1.2/1.3) reflects genuine behavior derivable from the public problem statement, not the single hidden test's shape.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
