# P2 adversarial audit — scikit-learn__scikit-learn-10844

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
# R1.1/R1.3: overflow-inducing large input -> finite (not nan/inf), no overflow RuntimeWarning.
# POSITIVE CONTROL: holds on patched, fails at base (base returns nan + warns).
import warnings
import numpy as np
from sklearn.metrics.cluster import fowlkes_mallows_score

x = np.array([1] * (52632 + 2529) + [2] * (14660 + 793) + [3] * (3271 +
             204) + [4] * (814 + 39) + [5] * (316 + 20))
y = np.array([0] * 52632 + [1] * 2529 + [0] * 14660 + [1] * 793 +
             [0] * 3271 + [1] * 204 + [0] * 814 + [1] * 39 + [0] * 316 +
             [1] * 20)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    score = fowlkes_mallows_score(x, y)
    overflow_warns = [ww for ww in w if issubclass(ww.category, RuntimeWarning)
                      and 'overflow' in str(ww.message).lower()]

print("score =", score)
print("overflow_warnings =", [str(ww.message) for ww in overflow_warns])
ok = np.isfinite(score) and len(overflow_warns) == 0
print("finite_and_no_overflow_warning =", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.4: score stays within [0,1] on the large overflow-inducing input.
import numpy as np
from sklearn.metrics.cluster import fowlkes_mallows_score
x = np.array([1] * (52632 + 2529) + [2] * (14660 + 793) + [3] * (3271 +
             204) + [4] * (814 + 39) + [5] * (316 + 20))
y = np.array([0] * 52632 + [1] * 2529 + [0] * 14660 + [1] * 793 +
             [0] * 3271 + [1] * 204 + [0] * 814 + [1] * 39 + [0] * 316 +
             [1] * 20)
s = fowlkes_mallows_score(x, y)
print("score =", s)
ok = np.isfinite(s) and 0.0 <= s <= 1.0
print("in_[0,1] =", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R2.3: perfect match (identical partitions up to relabeling) -> 1.0
import numpy as np
from sklearn.metrics.cluster import fowlkes_mallows_score
a = np.array([0,0,1,1,2,2,2,3])
b = np.array([5,5,9,9,7,7,7,1])   # same partition, relabeled
s = fowlkes_mallows_score(a, b)
print("perfect score =", s)
ok = abs(s - 1.0) < 1e-9
print("equals_1 =", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2.4: independent clusterings (one all-singletons) -> 0.0.  Also R2.2 tk==0 -> 0.0
import numpy as np
from sklearn.metrics.cluster import fowlkes_mallows_score
n = 20
labels_true = np.arange(n)          # each sample its own singleton
labels_pred = np.zeros(n, dtype=int)  # all in one cluster
s = fowlkes_mallows_score(labels_true, labels_pred)
print("independent score =", s)
ok = s == 0.0
print("equals_0 =", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R2.1/R2.5: on small inputs, value equals the agreement-over-geometric-mean formula
# computed independently with big python ints (exact reference).
import numpy as np
from collections import Counter
from sklearn.metrics.cluster import fowlkes_mallows_score

def ref(lt, lp):
    n = len(lt)
    cont = Counter(zip(lt, lp))
    rows = Counter(lt); cols = Counter(lp)
    tk = sum(v*v for v in cont.values()) - n
    pk = sum(v*v for v in cols.values()) - n
    qk = sum(v*v for v in rows.values()) - n
    if tk == 0:
        return 0.0
    import math
    return tk / math.sqrt(pk*qk)

rng = np.random.RandomState(0)
worst = 0.0
for _ in range(50):
    lt = rng.randint(0, 5, size=40)
    lp = rng.randint(0, 5, size=40)
    got = fowlkes_mallows_score(lt, lp)
    exp = ref(lt, lp)
    d = abs(got - exp)
    worst = max(worst, d)
print("max abs diff vs reference =", worst)
ok = worst < 1e-9
print("matches_reference =", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R3.2/R3.3: validation error on mismatched lengths preserved; label-invariance under relabeling.
import numpy as np
from sklearn.metrics.cluster import fowlkes_mallows_score

# mismatched lengths must raise ValueError
raised = False
try:
    fowlkes_mallows_score(np.array([0,1,2]), np.array([0,1]))
except ValueError as e:
    raised = True
    print("raised ValueError:", e)
print("length_mismatch_raises =", raised)

# relabeling invariance
a = np.array([0,0,1,1,2,0,1,2,2,1])
b = np.array([1,1,0,0,2,1,0,2,2,0])
s1 = fowlkes_mallows_score(a, b)
# relabel a -> 10,20,30 ; b -> 7,8,9
amap = {0:10,1:20,2:30}; bmap={0:7,1:8,2:9}
a2 = np.array([amap[v] for v in a]); b2 = np.array([bmap[v] for v in b])
s2 = fowlkes_mallows_score(a2, b2)
print("s1 =", s1, "s2(relabeled) =", s2)
inv = abs(s1 - s2) < 1e-12
print("relabel_invariant =", inv)
ok = raised and inv
import sys; sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# R2.1/R2.5 on the LARGE overflow input: value must equal the exact big-int
# agreement-over-geometric-mean reference (not merely be finite/in-range).
import numpy as np
from collections import Counter
import math
from sklearn.metrics.cluster import fowlkes_mallows_score

x = np.array([1] * (52632 + 2529) + [2] * (14660 + 793) + [3] * (3271 +
             204) + [4] * (814 + 39) + [5] * (316 + 20))
y = np.array([0] * 52632 + [1] * 2529 + [0] * 14660 + [1] * 793 +
             [0] * 3271 + [1] * 204 + [0] * 814 + [1] * 39 + [0] * 316 +
             [1] * 20)

def ref(lt, lp):
    n = len(lt)
    cont = Counter(zip(lt.tolist(), lp.tolist()))
    rows = Counter(lt.tolist()); cols = Counter(lp.tolist())
    tk = sum(v*v for v in cont.values()) - n           # exact python bigint
    pk = sum(v*v for v in cols.values()) - n
    qk = sum(v*v for v in rows.values()) - n
    if tk == 0:
        return 0.0
    return tk / math.sqrt(pk * qk)

got = fowlkes_mallows_score(x, y)
exp = ref(x, y)
print("got =", got, "exact_ref =", exp)
ok = np.isfinite(got) and abs(got - exp) < 1e-9
print("matches_exact_reference =", ok)
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1/R1.3: overflow-inducing large input -> finite (not nan/inf), no overflow RuntimeWarning.
# POSITIVE CONTROL: holds on patched, fails at base (base returns nan + warns).
import warnings
import numpy as np
from sklearn.metrics.cluster import fowlkes_mallows_score

x = np.array([1] * (52632 + 2529) + [2] * (14660 + 793) + [3] * (3271 +
             204) + [4] * (814 + 39) + [5] * (316 + 20))
y = np.array([0] * 52632 + [1] * 2529 + [0] * 14660 + [1] * 793 +
             [0] * 3271 + [1] * 204 + [0] * 814 + [1] * 39 + [0] * 316 +
             [1] * 20)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    score = fowlkes_mallows_score(x, y)
    overflow_warns = [ww for ww in w if issubclass(ww.category, RuntimeWarning)
                      and 'overflow' in str(ww.message).lower()]

print("score =", score)
print("overflow_warnings =", [str(ww.message) for ww in overflow_warns])
ok = np.isfinite(score) and len(overflow_warns) == 0
print("finite_and_no_overflow_warning =", ok)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

scikit-learn-10844: fowlkes_mallows_score overflow fix. Gold casts contingency data to int64 AND reformulates the score as sqrt(tk/pk)*sqrt(tk/qk) to avoid the overflowing pk*qk product.

7 probes, all HOLD on gold-patched tree:
- probe_1 (R1.1/R1.3, POSITIVE CONTROL): large overflow-inducing input (the F2P test's arrays) -> finite score AND no overflow RuntimeWarning. Patched: score=0.7289..., no warnings. Base: score=nan + 'overflow encountered in long_scalars' -> exit 1. Discriminates.
- probe_2 (R1.4): score in [0,1] on large input. Patched holds; base returns nan.
- probe_3 (R2.3): perfect match up to relabeling -> 1.0.
- probe_4 (R2.4/R2.2): all-singletons vs single-cluster (independent, tk=0) -> 0.0.
- probe_5 (R2.1/R2.5): 50 random small inputs match exact big-int agreement/geometric-mean reference (max diff 5.5e-17).
- probe_6 (R3.2/R3.3): mismatched-length raises ValueError; relabeling invariance holds.
- probe_7 (R2.1/R2.5 on LARGE input): value equals exact big-int reference 0.7289... (closes the gap probe_1/2 leave — finite+in-range is not enough). Base: nan -> exit 1. Discriminates.

### CANDIDATE PATCHES (both REJECTED by suite -> suite discriminates wrong fixes):
- candA (int64 cast ONLY, keep tk/sqrt(pk*qk)): REJECTED by probe_1 & probe_2 (int64 marginals ~1e9 still overflow int64 when squared/multiplied in pk*qk -> overflow warning + nan). This is the lazy 'just widen the type' fix; it does NOT resolve.
- candB (keep original formula but errstate-suppress overflow and map non-finite -> 0.0): passes probe_1/2 (finite, in [0,1]) but REJECTED by probe_7 (returns 0.0 instead of correct 0.7289 on the large input) — a plausible requirements-conforming-looking fix that is actually WRONG value; probe_7 catches it and it would also fail the hidden F2P/value expectations.

All needed runs completed in the official image. >=5 distinct probes, positive control reproduces prepatch failure and holds patched, >=1 candidate exercised and REJECTED. No violation found; suite discriminates. SOUND.

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
# R1.1/R1.3: overflow-inducing large input -> finite (not nan/inf), no overflow RuntimeWarning.
# POSITIVE CONTROL: holds on patched, fails at base (base returns nan + warns).
import warnings
import numpy as np
from sklearn.metrics.cluster import fowlkes_mallows_score

x = np.array([1] * (52632 + 2529) + [2] * (14660 + 793) + [3] * (3271 +
             204) + [4] * (814 + 39) + [5] * (316 + 20))
y = np.array([0] * 52632 + [1] * 2529 + [0] * 14660 + [1] * 793 +
             [0] * 3271 + [1] * 204 + [0] * 814 + [1] * 39 + [0] * 316 +
             [1] * 20)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    score = fowlkes_mallows_score(x, y)
    overflow_warns = [ww for ww in w if issubclass(ww.category, RuntimeWarning)
                      and 'overflow' in str(ww.message).lower()]

print("score =", score)
print("overflow_warnings =", [str(ww.message) for ww in overflow_warns])
ok = np.isfinite(score) and len(overflow_warns) == 0
print("finite_and_no_overflow_warning =", ok)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

scikit-learn-10844: fowlkes_mallows_score overflow fix. Gold casts contingency data to int64 AND reformulates the score as sqrt(tk/pk)*sqrt(tk/qk) to avoid the overflowing pk*qk product.

7 probes, all HOLD on gold-patched tree:
- probe_1 (R1.1/R1.3, POSITIVE CONTROL): large overflow-inducing input (the F2P test's arrays) -> finite score AND no overflow RuntimeWarning. Patched: score=0.7289..., no warnings. Base: score=nan + 'overflow encountered in long_scalars' -> exit 1. Discriminates.
- probe_2 (R1.4): score in [0,1] on large input. Patched holds; base returns nan.
- probe_3 (R2.3): perfect match up to relabeling -> 1.0.
- probe_4 (R2.4/R2.2): all-singletons vs single-cluster (independent, tk=0) -> 0.0.
- probe_5 (R2.1/R2.5): 50 random small inputs match exact big-int agreement/geometric-mean reference (max diff 5.5e-17).
- probe_6 (R3.2/R3.3): mismatched-length raises ValueError; relabeling invariance holds.
- probe_7 (R2.1/R2.5 on LARGE input): value equals exact big-int reference 0.7289... (closes the gap probe_1/2 leave — finite+in-range is not enough). Base: nan -> exit 1. Discriminates.

### CANDIDATE PATCHES (both REJECTED by suite -> suite discriminates wrong fixes):
- candA (int64 cast ONLY, keep tk/sqrt(pk*qk)): REJECTED by probe_1 & probe_2 (int64 marginals ~1e9 still overflow int64 when squared/multiplied in pk*qk -> overflow warning + nan). This is the lazy 'just widen the type' fix; it does NOT resolve.
- candB (keep original formula but errstate-suppress overflow and map non-finite -> 0.0): passes probe_1/2 (finite, in [0,1]) but REJECTED by probe_7 (returns 0.0 instead of correct 0.7289 on the large input) — a plausible requirements-conforming-looking fix that is actually WRONG value; probe_7 catches it and it would also fail the hidden F2P/value expectations.

All needed runs completed in the official image. >=5 distinct probes, positive control reproduces prepatch failure and holds patched, >=1 candidate exercised and REJECTED. No violation found; suite discriminates. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch modifies only two lines in fowlkes_mallows_score: cast contingency to int64 and reformulate the ratio. Requirements pin the changed observable behavior (overflow-safe finite score + unchanged values), not a narrow slice or helper. Boundary is correct. Base probe reproduces the exact issue overflow warning; patched probe is clean.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to fowlkes_mallows_score in sklearn/metrics/cluster/supervised.py and translate the overflow bug into behavioral criteria. All potentially-sensitive content is already public in problem_statement: the int32 overflow, the RuntimeWarning/nan symptom, the marginal-product (pk*qk) overflow, and even the proposed fix formula np.sqrt(tk/pk)*np.sqrt(tk/qk). The doc does NOT reproduce: test names (test_int_overflow_mutual_info_fowlkes_mallows_score), test file path, the large label-array constants from test_patch, or the gold token .astype(np.int64) (it says only 'enough integer width' generically). Behavioral properties (perfect match->1.0, singleton independence->0.0, zero agreement->0.0, bounds [0,1], symmetry, non-consecutive relabeling invariance) are standard, documented FM-index properties describing behavior, not enumerations mirroring the hidden test parametrization. Naming the module/function/signature (sparse flag) is legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
