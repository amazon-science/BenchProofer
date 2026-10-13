# P2 adversarial audit — sympy__sympy-20590

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
"""R1.1: Symbol instance exposes no __dict__ (positive control)."""
import sys
from sympy import Symbol
from sympy.core.basic import Basic

s = Symbol('s')
has_dict = hasattr(s, '__dict__')
print("hasattr(Symbol('s'), '__dict__') =", has_dict)

# also a bare Basic
b = Basic()
has_dict_b = hasattr(b, '__dict__')
print("hasattr(Basic(), '__dict__') =", has_dict_b)

if not has_dict and not has_dict_b:
    print("OK: no per-instance __dict__")
    sys.exit(0)
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.1: assigning an undeclared attribute raises AttributeError."""
import sys
from sympy import Symbol

s = Symbol('s')
try:
    s.some_random_attr = 1
    print("FAIL: assignment silently succeeded; value =", s.some_random_attr)
    sys.exit(1)
except AttributeError as e:
    print("OK: AttributeError raised on undeclared attr:", e)
    sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.2: Printable mixin itself pins layout with empty __slots__ and
no ancestor of Symbol (except object) reintroduces __dict__."""
import sys
from sympy import Symbol
from sympy.core._print_helpers import Printable

# Printable must declare __slots__ == ()
slots = Printable.__dict__.get('__slots__', None)
print("Printable.__slots__ =", slots)
ok_slots = slots == ()

# No ancestor except object should have a __dict__ descriptor in its own dict
bad = []
for klass in type(Symbol('s')).__mro__:
    if klass is object:
        continue
    if '__dict__' in klass.__dict__:
        bad.append(klass.__name__)
print("ancestors (non-object) declaring __dict__:", bad)

if ok_slots and not bad:
    print("OK: mixin pins layout, no ancestor reintroduces __dict__")
    sys.exit(0)
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1/3.2/3.3: construction, equality, hashing, subs, args unchanged."""
import sys
from sympy import Symbol, sin, cos
from sympy.abc import x, y

checks = []

# construction / args
e = sin(x) + cos(y)
checks.append(("args", set(e.args) == {sin(x), cos(y)}))

# equality & hash
a1, a2 = Symbol('a'), Symbol('a')
checks.append(("eq", a1 == a2))
checks.append(("hash", hash(a1) == hash(a2)))
checks.append(("neq", Symbol('a') != Symbol('b')))

# subs
checks.append(("subs", (x + y).subs(x, 1) == 1 + y))

# has / free_symbols
checks.append(("has", (x + y).has(x)))
checks.append(("free_symbols", (x + y).free_symbols == {x, y}))

# xreplace
checks.append(("xreplace", (x + y).xreplace({x: y}) == 2*y))

for name, ok in checks:
    print(name, "->", ok)

if all(ok for _, ok in checks):
    print("OK: behavior preserved")
    sys.exit(0)
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.4/3.5: printing behavior preserved; declared slotted attrs read/set."""
import sys
from sympy import Symbol, Integer
from sympy.abc import x

checks = []

# str / repr / latex printing hooks still work
checks.append(("str", str(x + 1) == 'x + 1'))
checks.append(("repr", repr(Integer(3)) == '3'))
from sympy import latex
checks.append(("latex", latex(x**2) == 'x^{2}'))
# jupyter hook exists
checks.append(("repr_latex_hook", hasattr(x, '_repr_latex_')))

# declared/assumption attributes readable
s = Symbol('s', positive=True)
checks.append(("assumption_read", s.is_positive is True))
checks.append(("name_read", s.name == 's'))

for name, ok in checks:
    print(name, "->", ok)

if all(ok for _, ok in checks):
    print("OK: printing + declared attrs preserved")
    sys.exit(0)
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1: Symbol instance exposes no __dict__ (positive control)."""
import sys
from sympy import Symbol
from sympy.core.basic import Basic

s = Symbol('s')
has_dict = hasattr(s, '__dict__')
print("hasattr(Symbol('s'), '__dict__') =", has_dict)

# also a bare Basic
b = Basic()
has_dict_b = hasattr(b, '__dict__')
print("hasattr(Basic(), '__dict__') =", has_dict_b)

if not has_dict and not has_dict_b:
    print("OK: no per-instance __dict__")
    sys.exit(0)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-20590: gold patch adds `__slots__ = ()` to Printable mixin so core symbolic instances regain dict-free layout.

Probes (all HOLD on patched tree):
- probe_1 (R1.1, POSITIVE CONTROL): Symbol('s') and Basic() expose no __dict__. Patched exit0; BASE exit1 (hasattr True) — discriminates.
- probe_2 (R2.1): assigning undeclared attr raises AttributeError. Patched exit0; BASE exit1 (silently stored) — discriminates.
- probe_3 (R1.2): Printable.__slots__==() and no non-object ancestor of Symbol declares __dict__. Patched exit0; BASE exit1 (Printable.__slots__ None, declares __dict__) — discriminates.
- probe_4 (R3.1/3.2/3.3): args, equality, hash, neq, subs, has, free_symbols, xreplace unchanged. Patched exit0.
- probe_5 (R3.4/3.5): str/repr/latex printing + _repr_latex_ hook + assumption/name declared-attr reads unchanged. Patched exit0.

Weak candidate `slots_with_dict` (__slots__ = ('__dict__',)): the naive/lazy reading — declares slots but includes __dict__, which re-introduces the per-instance dict. REJECTED by probes 1,2,3 (VIOLATED); probes 4,5 still HOLD. Suite discriminates the wrong fix, so requirements are not too weak on the dict-free criterion. This candidate would NOT resolve the hidden test_immutable.

>=5 distinct probes all hold on patched; positive control (probe_1) fails at base and holds patched; >=1 candidate exercised and rejected. Verdict SOUND.

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
"""R1.1: Symbol instance exposes no __dict__ (positive control)."""
import sys
from sympy import Symbol
from sympy.core.basic import Basic

s = Symbol('s')
has_dict = hasattr(s, '__dict__')
print("hasattr(Symbol('s'), '__dict__') =", has_dict)

# also a bare Basic
b = Basic()
has_dict_b = hasattr(b, '__dict__')
print("hasattr(Basic(), '__dict__') =", has_dict_b)

if not has_dict and not has_dict_b:
    print("OK: no per-instance __dict__")
    sys.exit(0)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-20590: gold patch adds `__slots__ = ()` to Printable mixin so core symbolic instances regain dict-free layout.

Probes (all HOLD on patched tree):
- probe_1 (R1.1, POSITIVE CONTROL): Symbol('s') and Basic() expose no __dict__. Patched exit0; BASE exit1 (hasattr True) — discriminates.
- probe_2 (R2.1): assigning undeclared attr raises AttributeError. Patched exit0; BASE exit1 (silently stored) — discriminates.
- probe_3 (R1.2): Printable.__slots__==() and no non-object ancestor of Symbol declares __dict__. Patched exit0; BASE exit1 (Printable.__slots__ None, declares __dict__) — discriminates.
- probe_4 (R3.1/3.2/3.3): args, equality, hash, neq, subs, has, free_symbols, xreplace unchanged. Patched exit0.
- probe_5 (R3.4/3.5): str/repr/latex printing + _repr_latex_ hook + assumption/name declared-attr reads unchanged. Patched exit0.

Weak candidate `slots_with_dict` (__slots__ = ('__dict__',)): the naive/lazy reading — declares slots but includes __dict__, which re-introduces the per-instance dict. REJECTED by probes 1,2,3 (VIOLATED); probes 4,5 still HOLD. Suite discriminates the wrong fix, so requirements are not too weak on the dict-free criterion. This candidate would NOT resolve the hidden test_immutable.

>=5 distinct probes all hold on patched; positive control (probe_1) fails at base and holds patched; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a single line adding `__slots__ = ()` to Printable in sympy/core/_print_helpers.py. Requirements correctly frame this as: an unpinned mixin layer reintroduced a per-instance __dict__ in CPython; pinning it with empty slots removes the __dict__ and restores immutability. Modeling boundary is the changed observable behavior (dict-free + reject arbitrary attribute), matching test_immutable. Probe HOLDS on patched (exit 0), VIOLATED on base (exit 1).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior (dict-free/immutable instances, AttributeError on undeclared attribute assignment, preserved construction/equality/subs/traversal/printing) and localizes the change to the Printable mixin in sympy/core/_print_helpers.py. Naming that class/file is legitimate localization; Symbol/__dict__/__slots__/immutability are all public in the problem_statement. No test function names (test_immutable), no test file path (test_basic.py), no verbatim gold line (__slots__ = ()), no fix-invented identifiers, and no parametrization ids are leaked. The 'instance.x = 1' example and hasattr(...,'__dict__') phrasing are generic behavioral illustrations that coincide with, but do not quote, the hidden test. Requirement 3's list of preserved operations (subs, replace, has, traversal, doit, rewrite) is a natural behavioral-preservation enumeration, not a mirror of the test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
