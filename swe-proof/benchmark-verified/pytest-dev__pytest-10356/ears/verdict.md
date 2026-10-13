# P2 adversarial audit — pytest-dev__pytest-10356

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

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1 (ac 1,5): full-MRO gather collects marks from ALL marked bases.
POSITIVE CONTROL: holds on patched tree, fails at base (single-lookup drops one base)."""
import sys
import pytest
from _pytest.mark.structures import get_unpacked_marks


@pytest.mark.foo
class A:
    pass


@pytest.mark.bar
class B:
    pass


class C(A, B):
    pass


names = [m.name for m in get_unpacked_marks(C)]
print("collected mark names for C(A,B):", names)
ok = "foo" in names and "bar" in names
print("both bases' marks present:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1 ac 2,3: reads each class's OWN stored pytestmark, not inherited via lookup.
A class with no own pytestmark contributes nothing / does not duplicate."""
import sys
import pytest
from _pytest.mark.structures import get_unpacked_marks


@pytest.mark.foo
class A:
    pass


class D(A):  # D itself stores nothing
    pass


names = [m.name for m in get_unpacked_marks(D)]
print("D(A) marks:", names)
# D inherits foo from A (single chain, still gathered), but foo must appear exactly once.
ok = names.count("foo") == 1
print("foo appears exactly once (no duplication):", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1 ac 4: MRO order preserved — target class's own marks first, then bases in MRO order."""
import sys
import pytest
from _pytest.mark.structures import get_unpacked_marks


@pytest.mark.a1
class A:
    pass


@pytest.mark.b1
class B:
    pass


@pytest.mark.c1
class C(A, B):
    pass


names = [m.name for m in get_unpacked_marks(C)]
print("C order:", names)
# MRO is C, A, B, object -> c1, a1, b1
ok = names == ["c1", "a1", "b1"]
print("order matches MRO (c1,a1,b1):", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2: direct-only mode (consider_mro=False) returns only own marks; keyword-only; default is MRO."""
import sys
import inspect
import pytest
from _pytest.mark.structures import get_unpacked_marks


@pytest.mark.foo
class A:
    pass


@pytest.mark.bar
class B(A):
    pass


direct = [m.name for m in get_unpacked_marks(B, consider_mro=False)]
full = [m.name for m in get_unpacked_marks(B)]
print("direct-only B:", direct, "full B:", full)

sig = inspect.signature(get_unpacked_marks)
p = sig.parameters.get("consider_mro")
kwonly = p is not None and p.kind == inspect.Parameter.KEYWORD_ONLY and p.default is True
print("consider_mro keyword-only default True:", kwonly)

# Req2 ac3: direct-only on class with no own marks -> empty
class E(A):
    pass


empty = get_unpacked_marks(E, consider_mro=False)
print("direct-only E (no own marks):", [m.name for m in empty])

ok = direct == ["bar"] and "foo" in full and kwonly and list(empty) == []
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3: store_mark uses direct-only collection — appending a mark to a subclass
does NOT copy inherited base marks onto the subclass's own pytestmark."""
import sys
import pytest
from _pytest.mark.structures import store_mark, get_unpacked_marks
from _pytest.mark.structures import Mark


@pytest.mark.foo
class A:
    pass


class B(A):  # inherits foo, stores nothing itself yet
    pass


# Apply a new mark 'bar' directly to B via store_mark
newmark = Mark("bar", (), {})
store_mark(B, newmark)

own = B.__dict__.get("pytestmark", [])
own_names = [m.name for m in own]
print("B own pytestmark after store_mark:", own_names)
# Req3 ac2: inherited foo must NOT be copied; only bar (B had no own marks before)
ok = own_names == ["bar"]
print("only newly-applied mark stored (no inherited leak):", ok)

# Req3 ac3 / Req1 still works: full collection sees both
full = [m.name for m in get_unpacked_marks(B)]
print("full B:", full)
ok = ok and "foo" in full and "bar" in full
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4: non-class objects unchanged — ordinary attribute lookup, single value coerced,
missing attribute -> empty. Req 5 ac6: repeated collection stable (store_mark twice)."""
import sys
import pytest
from _pytest.mark.structures import get_unpacked_marks, store_mark, Mark


# Req4 ac1/ac2: non-class object with single (bare) pytestmark value
class Obj:
    pass


o = Obj()
o.pytestmark = pytest.mark.foo.mark  # a single Mark, not a list
names = [m.name for m in get_unpacked_marks(o)]
print("non-class single mark:", names)
c1 = names == ["foo"]

# Req4 ac3: no pytestmark -> empty
o2 = Obj()
empty = list(get_unpacked_marks(o2))
print("non-class no attr:", empty)
c2 = empty == []

# Req5 ac6: repeated store_mark does not grow/duplicate a class's own marks
@pytest.mark.base
class A:
    pass


class C(A):
    pass


store_mark(C, Mark("x", (), {}))
first = [m.name for m in C.__dict__["pytestmark"]]
store_mark(C, Mark("y", (), {}))
second = [m.name for m in C.__dict__["pytestmark"]]
print("after 1st store:", first, "after 2nd:", second)
# 'base' (inherited) must never appear in C's own stored marks; order preserved
c3 = first == ["x"] and second == ["x", "y"]

ok = c1 and c2 and c3
print("all non-class + stability checks:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1 (ac 1,5): full-MRO gather collects marks from ALL marked bases.
POSITIVE CONTROL: holds on patched tree, fails at base (single-lookup drops one base)."""
import sys
import pytest
from _pytest.mark.structures import get_unpacked_marks


@pytest.mark.foo
class A:
    pass


@pytest.mark.bar
class B:
    pass


class C(A, B):
    pass


names = [m.name for m in get_unpacked_marks(C)]
print("collected mark names for C(A,B):", names)
ok = "foo" in names and "bar" in names
print("both bases' marks present:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-10356: get_unpacked_marks must walk full MRO reading each class's OWN pytestmark; store_mark must use direct-only (consider_mro=False).

### PROBES (all HOLD on gold-patched tree):
- probe_1 (Req1 ac1,5 = POSITIVE CONTROL): C(A,B) with A@foo, B@bar -> {foo,bar}. Patched: HOLDS. Base: VIOLATED (only ['foo'] — one base dropped). Discriminates.
- probe_2 (Req1 ac2,3): D(A), D stores nothing -> foo appears exactly once (no duplication). Patched HOLDS.
- probe_3 (Req1 ac4): MRO order c1,a1,b1 for C(A,B). Patched HOLDS; base VIOLATED (['a1','c1']).
- probe_4 (Req2 ac1,2,3): consider_mro keyword-only default True; direct-only returns own marks; empty for no-own. Patched HOLDS; base VIOLATED (TypeError: no consider_mro kwarg).
- probe_5 (Req3 ac1,2): store_mark on B(A) with new mark -> B.__dict__ pytestmark == ['bar'], no inherited 'foo' leaked; full collection still sees both. Patched HOLDS.
- probe_6 (Req4 ac1,2,3 + Req5 ac6): non-class single-value coerced, missing attr -> [], repeated store_mark stable/no growth/no inherited leak. Patched HOLDS.

CANDIDATE PATCH (required floor): weakA = plausible partial fix that adds the MRO-aware get_unpacked_marks + consider_mro param but LEAVES store_mark calling get_unpacked_marks(obj) with the default (full-MRO) mode — the lazy reading that ignores Requirement 3. Under weakA the probe suite REJECTS it: probe_3 (order corrupted: ['a1','b1','c1','a1','b1']), probe_4, probe_5 (inherited 'foo' leaked into B's own pytestmark), probe_6 all fail. probe_1 still passes (full-MRO gather works), confirming weakA is a genuine near-miss the suite catches. This demonstrates discriminating power against a requirements-plausible wrong fix; no probe-conforming alternative that resolves-wrong was found.

Verdict SOUND: >=6 distinct probes all hold on patched; positive control (probe_1, also probe_3/4) fails at base; candidate wrong-fix rejected by suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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
"""Req 1 (ac 1,5): full-MRO gather collects marks from ALL marked bases.
POSITIVE CONTROL: holds on patched tree, fails at base (single-lookup drops one base)."""
import sys
import pytest
from _pytest.mark.structures import get_unpacked_marks


@pytest.mark.foo
class A:
    pass


@pytest.mark.bar
class B:
    pass


class C(A, B):
    pass


names = [m.name for m in get_unpacked_marks(C)]
print("collected mark names for C(A,B):", names)
ok = "foo" in names and "bar" in names
print("both bases' marks present:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-10356: get_unpacked_marks must walk full MRO reading each class's OWN pytestmark; store_mark must use direct-only (consider_mro=False).

### PROBES (all HOLD on gold-patched tree):
- probe_1 (Req1 ac1,5 = POSITIVE CONTROL): C(A,B) with A@foo, B@bar -> {foo,bar}. Patched: HOLDS. Base: VIOLATED (only ['foo'] — one base dropped). Discriminates.
- probe_2 (Req1 ac2,3): D(A), D stores nothing -> foo appears exactly once (no duplication). Patched HOLDS.
- probe_3 (Req1 ac4): MRO order c1,a1,b1 for C(A,B). Patched HOLDS; base VIOLATED (['a1','c1']).
- probe_4 (Req2 ac1,2,3): consider_mro keyword-only default True; direct-only returns own marks; empty for no-own. Patched HOLDS; base VIOLATED (TypeError: no consider_mro kwarg).
- probe_5 (Req3 ac1,2): store_mark on B(A) with new mark -> B.__dict__ pytestmark == ['bar'], no inherited 'foo' leaked; full collection still sees both. Patched HOLDS.
- probe_6 (Req4 ac1,2,3 + Req5 ac6): non-class single-value coerced, missing attr -> [], repeated store_mark stable/no growth/no inherited leak. Patched HOLDS.

CANDIDATE PATCH (required floor): weakA = plausible partial fix that adds the MRO-aware get_unpacked_marks + consider_mro param but LEAVES store_mark calling get_unpacked_marks(obj) with the default (full-MRO) mode — the lazy reading that ignores Requirement 3. Under weakA the probe suite REJECTS it: probe_3 (order corrupted: ['a1','b1','c1','a1','b1']), probe_4, probe_5 (inherited 'foo' leaked into B's own pytestmark), probe_6 all fail. probe_1 still passes (full-MRO gather works), confirming weakA is a genuine near-miss the suite catches. This demonstrates discriminating power against a requirements-plausible wrong fix; no probe-conforming alternative that resolves-wrong was found.

Verdict SOUND: >=6 distinct probes all hold on patched; positive control (probe_1, also probe_3/4) fails at base; candidate wrong-fix rejected by suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes get_unpacked_marks to (a) special-case classes: walk obj.__mro__ reading each class's OWN __dict__['pytestmark'] when consider_mro (default True), or only obj.__dict__ when False; (b) materialize to list(normalize_mark_list(...)); non-class path preserved via getattr. store_mark now calls get_unpacked_marks(obj, consider_mro=False). All acceptance criteria (R1.1-1.7, R2.1-2.3, R3.1-3.3, R4.1-4.3, R5.1-5.6) correspond to real behavior; the modeling boundary is the changed observable behavior (MRO-aware collection + direct-only mode + store_mark using it), not a narrow slice. Verified live in the instance image: patched holds, base diverges at the MRO merge.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes to the changed helpers (get_unpacked_marks, store_mark) and file (structures.py), which is legitimate. All test-relevant content is translated into behavioral requirements: full-MRO gathering, own-__dict__ reading, target-first MRO ordering, a keyword-only direct-only mode defaulting to MRO, store_mark using direct-only, unchanged non-class behavior, and regression invariants. It does NOT leak the hidden test: no test name (test_mark_mro), file path (testing/test_mark.py), parametrization ids, verbatim test/gold code, or the fix-invented identifier `consider_mro` (described behaviorally, never named). The A/B/C + xfail('a'/'b'/'c') case set is not reconstructed; ordering is stated generically. Req 5's regression list tracks pre-existing, publicly-observable pytest marker semantics being preserved, not the hidden tests themselves.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
