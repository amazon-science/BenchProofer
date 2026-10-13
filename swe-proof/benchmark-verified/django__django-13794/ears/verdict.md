# P2 adversarial audit — django__django-13794

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1: lazy proxy on left of + (R1.1/R1.2 str, R1.3 int, R1.4 on-demand)."""
import sys
from django.utils.functional import lazy

calls = []
def make():
    calls.append(1)
    return "lazy"

lz = lazy(make, str)()
# on-demand: not evaluated until +
before = len(calls)
res = lz + "!"
print("str result:", repr(res), "calls_before_add:", before)
if before != 0:
    print("FAIL: forced before addition")
    sys.exit(1)
if res != "lazy!":
    print("FAIL: expected 'lazy!'")
    sys.exit(1)

lint = lazy(lambda: 4, int)()
ri = lint + 5
print("int result:", ri)
if ri != 9:
    print("FAIL: int add")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2: reflected addition — ordinary string on left, proxy on right (R2.1/R2.2/R2.3)."""
import sys
from django.utils.functional import lazy

lz = lazy(lambda: "lazy", str)()
res = "x" + lz
print("radd result:", repr(res))
if res != "xlazy":
    print("FAIL: expected 'xlazy'")
    sys.exit(1)
# order preservation
lz2 = lazy(lambda: "B", str)()
res2 = "A" + lz2
if res2 != "AB":
    print("FAIL: order not preserved:", repr(res2))
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R3: concatenating two lazy proxies (R3.1 str, R3.2 int)."""
import sys
from django.utils.functional import lazy

a = lazy(lambda: "string", str)()
b = lazy(lambda: "lazy", str)()
res = a + b
print("two-proxy str:", repr(res))
if res != "stringlazy":
    print("FAIL: expected 'stringlazy'")
    sys.exit(1)

i4 = lazy(lambda: 4, int)()
i5 = lazy(lambda: 5, int)()
ri = i4 + i5
print("two-proxy int:", ri)
if ri != 9:
    print("FAIL: expected 9")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R4: add filter concatenates lazy strings (R4.1 str+lazy, R4.2 lazy+lazy, R4.3 no empty)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.template.defaultfilters import add
from django.utils.translation import gettext_lazy

r1 = add("string", gettext_lazy("lazy"))
print("add(str, lazy):", repr(str(r1)))
if str(r1) != "stringlazy":
    print("FAIL R4.1")
    sys.exit(1)

r2 = add(gettext_lazy("string"), gettext_lazy("lazy"))
print("add(lazy, lazy):", repr(str(r2)))
if str(r2) != "stringlazy":
    print("FAIL R4.2")
    sys.exit(1)

# R4.3: not empty string
if str(r1) == "" or str(r2) == "":
    print("FAIL R4.3: empty string")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R5: preserve existing behavior (R5.1 numeric sum, R5.2 list/str concat, R5.3 empty fallback, R5.5 unmasked error)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()
from django.template.defaultfilters import add
from django.utils.functional import lazy

# R5.1 numeric strings -> arithmetic sum
r = add("1", "2")
print("add('1','2'):", r)
if r != 3:
    print("FAIL R5.1")
    sys.exit(1)

# R5.2 lists concat, strings concat
rl = add([1, 2], [3, 4])
print("add lists:", rl)
if rl != [1, 2, 3, 4]:
    print("FAIL R5.2 list")
    sys.exit(1)
rs = add("foo", "bar")
if str(rs) != "foobar":
    print("FAIL R5.2 str")
    sys.exit(1)

# R5.3 unaddable -> empty string
ru = add(1, "abc")
print("add(1,'abc'):", repr(ru))
if ru != "":
    print("FAIL R5.3")
    sys.exit(1)

# R5.5 proxy+int (str-wrapped) raises TypeError, unmasked
lz = lazy(lambda: "s", str)()
raised = None
try:
    lz + 5
except TypeError as e:
    raised = e
# direct comparison: "s" + 5 also raises TypeError
direct = None
try:
    "s" + 5
except TypeError as e:
    direct = e
print("proxy raised:", type(raised).__name__ if raised else None,
      "direct:", type(direct).__name__ if direct else None)
if raised is None or direct is None or type(raised) is not type(direct):
    print("FAIL R5.5")
    sys.exit(1)
print("OK")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""R2: reflected addition — ordinary string on left, proxy on right (R2.1/R2.2/R2.3)."""
import sys
from django.utils.functional import lazy

lz = lazy(lambda: "lazy", str)()
res = "x" + lz
print("radd result:", repr(res))
if res != "xlazy":
    print("FAIL: expected 'xlazy'")
    sys.exit(1)
# order preservation
lz2 = lazy(lambda: "B", str)()
res2 = "A" + lz2
if res2 != "AB":
    print("FAIL: order not preserved:", repr(res2))
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: lazy proxy gains __add__/__radd__ so + concatenates/adds like the underlying value, fixing the add filter. Probes: p1=R1 (left-hand add, str 'lazy!' + int 4+5=9, on-demand forcing not before add); p2=R2 (reflected add 'x'+lazy=='xlazy', order preserved) [POSITIVE CONTROL]; p3=R3 (two proxies concat/int); p4=R4 (add filter str+lazy and lazy+lazy == 'stringlazy', no empty string); p5=R5 regressions (add('1','2')==3, list/str concat, unaddable->'', proxy+int raises same TypeError unmasked). Results: ALL 5 HOLD on patched tree. Positive controls p2/p3/p4 VIOLATE at base ('must be str, not __proxy__' / add filter returns ''), so the prepatch discriminator is confirmed. Weak candidate (add-only, omits __radd__ — the lazy fix a partial reading permits) is REJECTED by p2, p3(int-radd path), and p4 while p1/p5 still hold, demonstrating the suite discriminates the reflected-addition requirement (R2). Note: meta.json G-PANEL-3 flags requirements line 17 as leaking the hidden test's exact 4/5 int values — that is a leakage concern (separate gate), not a spec-fidelity/too-weak defect; G-EQ (equivalence/too-weak) is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""R2: reflected addition — ordinary string on left, proxy on right (R2.1/R2.2/R2.3)."""
import sys
from django.utils.functional import lazy

lz = lazy(lambda: "lazy", str)()
res = "x" + lz
print("radd result:", repr(res))
if res != "xlazy":
    print("FAIL: expected 'xlazy'")
    sys.exit(1)
# order preservation
lz2 = lazy(lambda: "B", str)()
res2 = "A" + lz2
if res2 != "AB":
    print("FAIL: order not preserved:", repr(res2))
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: lazy proxy gains __add__/__radd__ so + concatenates/adds like the underlying value, fixing the add filter. Probes: p1=R1 (left-hand add, str 'lazy!' + int 4+5=9, on-demand forcing not before add); p2=R2 (reflected add 'x'+lazy=='xlazy', order preserved) [POSITIVE CONTROL]; p3=R3 (two proxies concat/int); p4=R4 (add filter str+lazy and lazy+lazy == 'stringlazy', no empty string); p5=R5 regressions (add('1','2')==3, list/str concat, unaddable->'', proxy+int raises same TypeError unmasked). Results: ALL 5 HOLD on patched tree. Positive controls p2/p3/p4 VIOLATE at base ('must be str, not __proxy__' / add filter returns ''), so the prepatch discriminator is confirmed. Weak candidate (add-only, omits __radd__ — the lazy fix a partial reading permits) is REJECTED by p2, p3(int-radd path), and p4 while p1/p5 still hold, demonstrating the suite discriminates the reflected-addition requirement (R2). Note: meta.json G-PANEL-3 flags requirements line 17 as leaking the hidden test's exact 4/5 int values — that is a leakage concern (separate gate), not a spec-fidelity/too-weak defect; G-EQ (equivalence/too-weak) is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary is correct: requirements pin the changed observable behavior (+ operator delegation via __add__/__radd__ and the resulting add-filter fix), not a narrow slice. Error-preservation (Req5.5) and on-demand evaluation (Req1.4) follow directly from delegating to __cast(). All probes exit 0 on patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the addition protocol (__add__/__radd__) on the lazy proxy and the add filter's concatenation of lazy strings purely as behavior. Module/function names (django.utils.functional.lazy, django.template.defaultfilters.add) are legitimate localization already implied by the public problem_statement (which names the add filter and the TypeError). The case enumeration (lazy left, reflected right, both-lazy, string vs integer) is the natural decomposition of the + operator's semantics, not a mirror of the hidden test parametrization. The integer example (Req 1.3) generalizes the behavior rather than quoting test_lazy_add's lazy(lambda:4,int)/lazy(lambda:5,int)==9. No hidden-test artifacts leak: no test function names (test_add08/add09/test_lazy_add), no template ids ('add08'/'add09'), no file paths (tests/template_tests/filter_tests/test_add.py, tests/utils_tests/test_functional.py), no verbatim gold lines (self.__cast() + other), and no fix-invented identifiers. Requirement 5's regression clauses (numeric sums, list concat, empty-string fallback) come from the public add-filter behavior, not the hidden PASS_TO_PASS set.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
