# P2 adversarial audit — sympy__sympy-20154

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
# POSITIVE CONTROL: Req1.2/1.3 -- materialized list has distinct entries, not repeated final
from sympy.utilities.iterables import partitions
got = [p for p in partitions(6, k=2)]
print("got:", got)
expected = [{2: 3}, {1: 2, 2: 2}, {1: 4, 2: 1}, {1: 6}]
print("expected:", expected)
assert got == expected, "list does not reflect true sequence"
assert not all(p == got[-1] for p in got), "collapsed to repeated final partition"
print("OK: distinct partitions preserved")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.1/1.5: distinct dictionary objects at each step; mutating one does not affect others
from sympy.utilities.iterables import partitions
got = list(partitions(6, k=2))
# all distinct object identities
ids = [id(p) for p in got]
print("ids:", ids)
assert len(set(ids)) == len(ids), "yielded values share object identity"
# mutate the first, others unaffected
snapshot = [dict(p) for p in got]
got[0]['999'] = 123
for i in range(1, len(got)):
    assert got[i] == snapshot[i], "mutation leaked across yields"
print("OK: independent objects, no shared mutable state")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.1/2.2/2.3: size=True form yields (count, dict); count == sum of multiplicities; independent
from sympy.utilities.iterables import partitions
got = list(partitions(6, k=2, size=True))
print("got:", got)
expected = [(3, {2: 3}), (4, {1: 2, 2: 2}), (5, {1: 4, 2: 1}), (6, {1: 6})]
assert got == expected, "size=True sequence wrong"
for M, p in got:
    assert M == sum(p.values()), "count != sum of multiplicities"
# independence of retained dicts
dicts = [p for _, p in got]
assert len(set(id(d) for d in dicts)) == len(dicts), "size=True dicts share identity"
assert not all(d == dicts[-1] for d in dicts), "collapsed to final"
print("OK: size=True independent and count-correct")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1/3.2/3.3/3.4/3.5: same partitions, contents, order; bounds respected; sum==n
from sympy.utilities.iterables import partitions

# Full unbounded partitions of 7 -- known count is 15, all valid
got7 = [dict(p) for p in partitions(7)]
assert len(got7) == 15, ("expected 15 partitions of 7, got %d" % len(got7))
for p in got7:
    assert all(v > 0 for v in p.values()), "non-positive multiplicity"
    assert sum(k*v for k, v in p.items()) == 7, "does not sum to n"

# k bound
for p in partitions(10, k=3):
    assert all(k <= 3 for k in p), "part exceeds k"
# m bound
for p in partitions(10, m=2):
    assert sum(p.values()) <= 2, "too many parts vs m"
# both bounds, exact expected order (known reference)
both = [dict(p) for p in partitions(6, m=3, k=4)]
print("m=3,k=4:", both)
expected = [{4: 1, 2: 1}, {4: 1, 1: 2}, {3: 2}, {3: 1, 2: 1, 1: 1}, {2: 3}]
assert both == expected, "m&k combined sequence/order changed"
print("OK: partitions/contents/order/bounds preserved")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3.6: no-partition inputs yield exactly one empty partition; Req3.7 sympy Integer accepted
from sympy.utilities.iterables import partitions
from sympy import Integer

# non-positive n
for args in [dict(n=0), dict(n=-3)]:
    r = list(partitions(**args))
    print(args, "->", r)
    assert r == [{}], "expected exactly one empty partition"
# bound < 1
r = list(partitions(5, k=0))
print("k=0 ->", r)
assert r == [{}], "expected one empty partition for k<1"
# size=True empty form -> (0, {})
r = list(partitions(0, size=True))
print("size empty ->", r)
assert r == [(0, {})], "expected (0, {}) empty pair"

# Req3.7: sympy Integer equivalent to python int
a = [dict(p) for p in partitions(Integer(6), k=2)]
b = [dict(p) for p in partitions(6, k=2)]
print("Integer:", a)
assert a == b, "sympy Integer input differs from python int"
print("OK: empty-partition convention and Integer input")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req1.4: order-preserving de-dup of yielded values reports consecutive distinct partitions distinct.
# Uses a case where consecutive partitions repeat if the SAME object is shared (base bug).
from sympy.utilities.iterables import partitions
seq = list(partitions(6, k=2))
# order-preserving dedup on consecutive equality
dedup = []
for p in seq:
    if not dedup or dedup[-1] != p:
        dedup.append(p)
print("dedup:", dedup)
# The 4 partitions of 6 with k=2 are all distinct, so dedup keeps all 4.
assert len(dedup) == 4, "consecutive-distinct partitions collapsed under dedup"
print("OK: dedup reflects true sequence")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# POSITIVE CONTROL: Req1.2/1.3 -- materialized list has distinct entries, not repeated final
from sympy.utilities.iterables import partitions
got = [p for p in partitions(6, k=2)]
print("got:", got)
expected = [{2: 3}, {1: 2, 2: 2}, {1: 4, 2: 1}, {1: 6}]
print("expected:", expected)
assert got == expected, "list does not reflect true sequence"
assert not all(p == got[-1] for p in got), "collapsed to repeated final partition"
print("OK: distinct partitions preserved")
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: sympy-20154, gold patch makes partitions() yield independent dict snapshots (ms.copy() at every yield) instead of one shared mutated dict.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (POSITIVE CONTROL, Req1.2/1.3): list(partitions(6,k=2)) equals the true distinct sequence [{2:3},{1:2,2:2},{1:4,2:1},{1:6}] and does NOT collapse to repeated final. HOLDS patched, FAILS base (prepatch reproduced) and FAILS the partial-fix candidate.
- probe_2 (Req1.1/1.5): all four yielded dicts have distinct id(); mutating one leaves others unchanged. HOLDS patched, FAILS base, FAILS partial fix.
- probe_3 (Req2.1/2.2/2.3): size=True yields (count,dict) with count==sum(multiplicities), dicts independent, no collapse. HOLDS patched, FAILS base, FAILS partial fix.
- probe_4 (Req3.1-3.5): 15 partitions of 7 all valid & sum to n; k-bound and m-bound respected; combined m=3,k=4 sequence/order matches reference. HOLDS on patched (also holds on base/partial as a pure regression criterion, as expected).
- probe_5 (Req3.6/3.7): non-positive n / bound<1 yield exactly [{}]; size=True empty yields [(0,{})]; sympy Integer(6) equivalent to int. HOLDS.
- probe_6 (Req1.4): order-preserving consecutive dedup of yielded values keeps all 4 distinct partitions. HOLDS patched, FAILS base, FAILS partial fix.

Discriminating power: positive control (probe_1) fails at base with 'list does not reflect true sequence' and holds patched.

Candidate patch REJECTED: weak.diff copies ONLY the pre-loop first yield (leaving the while-loop yields sharing the mutated dict). This is the lazy partial reading of Req1. Probes 1,2,3,6 REJECT it (share identity / collapsed sequence), demonstrating the suite discriminates wrong implementations. Probes 4/5 (pure content/bounds regression criteria) still pass under it, correctly, since they don't test independence.

No requirements-conforming alternative that fails the hidden tests was found; the independence requirement is fully pinned by probes 1/2/3/6. Verdict SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, and a plausible partial fix is rejected.

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
# POSITIVE CONTROL: Req1.2/1.3 -- materialized list has distinct entries, not repeated final
from sympy.utilities.iterables import partitions
got = [p for p in partitions(6, k=2)]
print("got:", got)
expected = [{2: 3}, {1: 2, 2: 2}, {1: 4, 2: 1}, {1: 6}]
print("expected:", expected)
assert got == expected, "list does not reflect true sequence"
assert not all(p == got[-1] for p in got), "collapsed to repeated final partition"
print("OK: distinct partitions preserved")
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: sympy-20154, gold patch makes partitions() yield independent dict snapshots (ms.copy() at every yield) instead of one shared mutated dict.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (POSITIVE CONTROL, Req1.2/1.3): list(partitions(6,k=2)) equals the true distinct sequence [{2:3},{1:2,2:2},{1:4,2:1},{1:6}] and does NOT collapse to repeated final. HOLDS patched, FAILS base (prepatch reproduced) and FAILS the partial-fix candidate.
- probe_2 (Req1.1/1.5): all four yielded dicts have distinct id(); mutating one leaves others unchanged. HOLDS patched, FAILS base, FAILS partial fix.
- probe_3 (Req2.1/2.2/2.3): size=True yields (count,dict) with count==sum(multiplicities), dicts independent, no collapse. HOLDS patched, FAILS base, FAILS partial fix.
- probe_4 (Req3.1-3.5): 15 partitions of 7 all valid & sum to n; k-bound and m-bound respected; combined m=3,k=4 sequence/order matches reference. HOLDS on patched (also holds on base/partial as a pure regression criterion, as expected).
- probe_5 (Req3.6/3.7): non-positive n / bound<1 yield exactly [{}]; size=True empty yields [(0,{})]; sympy Integer(6) equivalent to int. HOLDS.
- probe_6 (Req1.4): order-preserving consecutive dedup of yielded values keeps all 4 distinct partitions. HOLDS patched, FAILS base, FAILS partial fix.

Discriminating power: positive control (probe_1) fails at base with 'list does not reflect true sequence' and holds patched.

Candidate patch REJECTED: weak.diff copies ONLY the pre-loop first yield (leaving the while-loop yields sharing the mutated dict). This is the lazy partial reading of Req1. Probes 1,2,3,6 REJECT it (share identity / collapsed sequence), demonstrating the suite discriminates wrong implementations. Probes 4/5 (pure content/bounds regression criteria) still pass under it, correctly, since they don't test independence.

No requirements-conforming alternative that fails the hidden tests was found; the independence requirement is fully pinned by probes 1/2/3/6. Verdict SOUND: >=5 probes hold on patched, positive control discriminates base vs patched, and a plausible partial fix is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a two-site copy-on-yield fix. Requirement boundary is correct: R1 targets the independence behavior that actually changed (not a narrow helper/branch); R3 correctly locks the invariant that the generated partition sequence itself is unchanged, which the FAIL_TO_PASS tests (list==expected literals, uniq) confirm. No mandated behavior absent from the code, no forbidden behavior present, no invented behavior.

Counterexample / evidence:

```
Probe on gold-patched tree: list(partitions(6,k=2)) == [{2:3},{1:2,2:2},{1:4,2:1},{1:6}] with all-distinct object ids; size form == [(3,{2:3}),(4,{1:2,2:2}),(5,{1:4,2:1}),(6,{1:6})] with M==sum(p.values()); partitions(0)==[{}], partitions(-1)==[{}], partitions(0,size=True)==[(0,{})]; partitions(S(3),m=2)==[{3:1},{1:1,2:1}]. All match requirements.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the partitions() independence fix purely as behavior. The hidden tests enumerate concrete outputs (e.g. partitions(6,k=2)==[{2:3},{1:2,2:2},{1:4,2:1},{1:6}], partitions(6,k=3)==..., partitions(8,k=4,m=3)==...) and use uniq()/S(3); none of these concrete partition lists or values are reproduced in the document. No test names/paths (test_partitions, test_uniq, test_iterables.py), no parametrization ids, and no fix-invented identifiers appear. The gold edit only adds .copy(); the spec doesn't leak that mechanic. Parameters n,m,k,size and the reused-dictionary defect (incl. list(partitions()) apparent-wrong-result) are all public via problem_statement. Req 1.4's 'order-preserving de-duplication' loosely mirrors the test_uniq FAIL_TO_PASS but is stated as a generic behavioral consequence, not as the test itself, and uniq is a public API — legitimate behavior translation. Localizing to sympy/utilities/iterables.py partitions() is legitimate.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
