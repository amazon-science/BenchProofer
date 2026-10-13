# P2 adversarial audit — sympy__sympy-15017

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
# Req 1.1 (positive control): rank-0 ImmutableDenseNDimArray reports len == 1
from sympy.tensor.array import ImmutableDenseNDimArray
from sympy import symbols
x = symbols('x')
a = ImmutableDenseNDimArray(x)
print("shape=", a.shape, "len=", len(a))
assert a.shape == (), a.shape
assert len(a) == 1, "len should be 1, got %r" % len(a)
print("OK: rank-0 len == 1")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2 & 1.3: rank-0 shape==(), rank()==0, iteration yields exactly one element == len
from sympy.tensor.array import ImmutableDenseNDimArray
from sympy import symbols
x = symbols('x')
a = ImmutableDenseNDimArray(x)
els = list(a)
print("shape=", a.shape, "rank=", a.rank(), "list=", els, "len=", len(a))
assert a.shape == ()
assert a.rank() == 0, a.rank()
assert len(els) == 1, els
assert len(els) == len(a)
assert els[0] == x
print("OK: shape/rank/iteration consistent")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1, 2.2, 2.3: scalar accessible by arr[()] and arr[0]; valid flat index range is exactly {0}
from sympy.tensor.array import ImmutableDenseNDimArray
from sympy import symbols
x = symbols('x')
a = ImmutableDenseNDimArray(x)
assert a[()] == x, a[()]
assert a[0] == x, a[0]
print("a[()]=", a[()], "a[0]=", a[0])
# index 1 must be out of range
raised = False
try:
    a[1]
except Exception as e:
    raised = True
    print("a[1] raised", type(e).__name__)
assert raised, "a[1] should raise (only {0} valid)"
print("OK: req 2 addressing holds")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.1 & 3.2: zero-dim array len==0 rank==1; positive-dim arrays keep product len
from sympy.tensor.array import ImmutableDenseNDimArray
z = ImmutableDenseNDimArray([], (0,))
print("shape=(0,) len=", len(z), "rank=", z.rank())
assert len(z) == 0, len(z)
assert z.rank() == 1, z.rank()

one = ImmutableDenseNDimArray([5])           # shape (1,)
assert len(one) == 1, len(one)
nine = ImmutableDenseNDimArray(range(9), (3,3))
print("shape=(3,3) len=", len(nine))
assert len(nine) == 9, len(nine)
print("OK: req 3 counts preserved")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4.1 & 4.2: len == count of iterated elements for multi-dim AND rank-0;
# reshape to compatible product succeeds & preserves len; incompatible product raises.
from sympy.tensor.array import ImmutableDenseNDimArray
from sympy import symbols
x = symbols('x')

# len == iterated count across several shapes incl rank-0
for arr in [ImmutableDenseNDimArray(x),
            ImmutableDenseNDimArray([5]),
            ImmutableDenseNDimArray(range(6), (2,3)),
            ImmutableDenseNDimArray(range(9), (3,3))]:
    assert len(arr) == len(list(arr)), (arr.shape, len(arr), len(list(arr)))
print("OK: len == iterated count for all shapes incl rank-0")

b = ImmutableDenseNDimArray(range(6), (2,3))
c = b.reshape(3,2)
assert len(c) == len(b) == 6, (len(c), len(b))
assert c.shape == (3,2)
print("reshape(3,2) OK len", len(c))

# incompatible product must raise (req 4.2 'SHALL instead raise an error')
raised = False
try:
    b.reshape(2,4)   # product 8 != 6
except Exception as e:
    raised = True
    print("reshape(2,4) raised", type(e).__name__)
assert raised, "incompatible reshape must raise"
print("OK: req 4.1/4.2 consistency")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 4.3 regression: nested-list construction, elementwise arithmetic, equality,
# slicing, applyfunc unchanged for arrays with >=1 dimension.
from sympy.tensor.array import ImmutableDenseNDimArray
from sympy import symbols
x, y = symbols('x y')

m = ImmutableDenseNDimArray([[1,2],[3,4]])
assert m.shape == (2,2) and len(m) == 4
assert m == ImmutableDenseNDimArray([[1,2],[3,4]])
# arithmetic
s = m + m
assert s == ImmutableDenseNDimArray([[2,4],[6,8]]), s
# scalar mult
assert (2*m) == s
# slicing
row = m[0, :]
assert list(row) == [1,2], list(row)
# applyfunc
ap = m.applyfunc(lambda e: e+1)
assert ap == ImmutableDenseNDimArray([[2,3],[4,5]]), ap
print("OK: req 4.3 regressions hold")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1 (positive control): rank-0 ImmutableDenseNDimArray reports len == 1
from sympy.tensor.array import ImmutableDenseNDimArray
from sympy import symbols
x = symbols('x')
a = ImmutableDenseNDimArray(x)
print("shape=", a.shape, "len=", len(a))
assert a.shape == (), a.shape
assert len(a) == 1, "len should be 1, got %r" % len(a)
print("OK: rank-0 len == 1")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Reqs 1-4. All HOLD on the gold-patched tree. Positive control (probe_1, rank-0 len==1) HOLDS patched and FAILS at base; probes 2,3,5 also fail at base. probe_1 Req1.1 rank-0 len==1; probe_2 Req1.2/1.3 shape=()/rank=0/iteration==len; probe_3 Req2.1/2.2/2.3 arr[()] and arr[0] return scalar, a[1] raises, valid flat index range {0}; probe_4 Req3.1/3.2 shape=(0,)->len 0/rank 1, (3,3)->len 9; probe_5 Req4.1/4.2 len==iterated count incl rank-0, reshape(3,2) preserves len, reshape(2,4) (product 8!=6) raises; probe_6 Req4.3 regression: nested-list construction, elementwise arithmetic, equality, slicing, applyfunc.

Wrong-fix candidate 'lazy_or_1' (uses `... or 1` to force a nonzero count) fixes rank-0 but is REJECTED by probe_4: it makes shape=(0,) report len 1 instead of 0, violating Req3.1. This demonstrates the suite discriminates a plausibly-wrong partial fix.

IMPORTANT contra the prior recorded G-EQ/G-PANEL-1 fail: that VIOLATION rested on a probe expecting reshape(2,4) on a len-6 array to SUCCEED. Req4.2 explicitly states that when the new shape's product differs from the element count, reshaping SHALL raise an error. The patched tree correctly raises (TypeError). The prior probe was itself unfaithful to the requirement — a false-positive VIOLATION, not a real spec-too-weak or spec-too-strong defect. (Separately, G-PANEL-2's 'Mutable dense also named' point concerns Req1.1 scope wording, not this G-EQ spec-fidelity dimension; the requirements explicitly scope the element-count change to the immutable dense type in the Introduction and each acceptance criterion, and gold indeed only changes ImmutableDenseNDimArray.)

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
# Req 1.1 (positive control): rank-0 ImmutableDenseNDimArray reports len == 1
from sympy.tensor.array import ImmutableDenseNDimArray
from sympy import symbols
x = symbols('x')
a = ImmutableDenseNDimArray(x)
print("shape=", a.shape, "len=", len(a))
assert a.shape == (), a.shape
assert len(a) == 1, "len should be 1, got %r" % len(a)
print("OK: rank-0 len == 1")
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover Reqs 1-4. All HOLD on the gold-patched tree. Positive control (probe_1, rank-0 len==1) HOLDS patched and FAILS at base; probes 2,3,5 also fail at base. probe_1 Req1.1 rank-0 len==1; probe_2 Req1.2/1.3 shape=()/rank=0/iteration==len; probe_3 Req2.1/2.2/2.3 arr[()] and arr[0] return scalar, a[1] raises, valid flat index range {0}; probe_4 Req3.1/3.2 shape=(0,)->len 0/rank 1, (3,3)->len 9; probe_5 Req4.1/4.2 len==iterated count incl rank-0, reshape(3,2) preserves len, reshape(2,4) (product 8!=6) raises; probe_6 Req4.3 regression: nested-list construction, elementwise arithmetic, equality, slicing, applyfunc.

Wrong-fix candidate 'lazy_or_1' (uses `... or 1` to force a nonzero count) fixes rank-0 but is REJECTED by probe_4: it makes shape=(0,) report len 1 instead of 0, violating Req3.1. This demonstrates the suite discriminates a plausibly-wrong partial fix.

IMPORTANT contra the prior recorded G-EQ/G-PANEL-1 fail: that VIOLATION rested on a probe expecting reshape(2,4) on a len-6 array to SUCCEED. Req4.2 explicitly states that when the new shape's product differs from the element count, reshaping SHALL raise an error. The patched tree correctly raises (TypeError). The prior probe was itself unfaithful to the requirement — a false-positive VIOLATION, not a real spec-too-weak or spec-too-strong defect. (Separately, G-PANEL-2's 'Mutable dense also named' point concerns Req1.1 scope wording, not this G-EQ spec-fidelity dimension; the requirements explicitly scope the element-count change to the immutable dense type in the Introduction and each acceptance criterion, and gold indeed only changes ImmutableDenseNDimArray.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base probe: len(ImmutableDenseNDimArray(3))==0 (AssertionError), so requirements correctly capture the changed observable behavior. Scoping is precise rather than over-broad: NDimArray base __len__ derives from _loop_size, but only the immutable dense _new was patched, and the requirements say so.

Counterexample / evidence:

```
None — no requirement mandates behavior the patched code lacks, forbids behavior it has, mis-pins the boundary, or invents behavior. The modeling boundary (immutable dense only) matches the code exactly.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit is a single one-liner (_loop_size empty-product 0→1); its invented/identifier content (_loop_size, functools.reduce(...,shape,1)) is never named in the doc — only the behavioral phrasing 'empty product is 1' appears, which is a description, not a code leak. The problem_statement already discloses the central facts (rank-0 len should be 1, len(list(a))==1, numpy parity, NDimArray.__len__). Additional example cases in the doc (arr[()]==x, arr[0]==x formerly-ValueError, shape=(0,)→len 0/rank 1, shape=(3,3)→9) coincide with the hidden test assertions but are natural behavioral consequences of the one-element/empty-product rule and are given as illustrative 'e.g.' cases, i.e. behavior-describing, not test-reconstructing. No test function names (test_ndim_array_initiation etc.), no test file path (tests/test_immutable_ndim_array.py), no parametrization ids, and no verbatim test/gold code lines appear. Module/class localization (dense_ndim_array.py, ImmutableDenseNDimArray, NDimArray) is legitimate. Requirement enumeration follows behavioral categories, not the test's structure.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
