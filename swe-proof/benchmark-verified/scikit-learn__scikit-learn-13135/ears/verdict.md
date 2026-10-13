# P2 adversarial audit — scikit-learn__scikit-learn-13135

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control (Req 1.3 / hidden test): kmeans n_bins=5 on data whose
cluster centers would otherwise come back out of order must fit_transform
without ValueError and produce the expected ordinal codes [0,0,1,2,3,4].
Holds patched; must FAIL at base (raises ValueError bins must be monotonic)."""
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
est = KBinsDiscretizer(n_bins=5, strategy='kmeans', encode='ordinal')
try:
    Xt = est.fit_transform(X)
except ValueError as e:
    print("FAIL: fit_transform raised ValueError:", e)
    raise SystemExit(1)
got = Xt.ravel().astype(int).tolist()
expected = [0, 0, 1, 2, 3, 4]
print("observed ordinal codes:", got, "expected:", expected)
if got != expected:
    print("FAIL: codes differ from expected")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1: after fit with strategy='kmeans' on non-constant columns, stored
bin_edges_ for each feature SHALL be sorted non-decreasing. Test across many
n_bins values (approaching #distinct points) where centers likely unsorted."""
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
ok = True
for nb in range(2, 7):
    est = KBinsDiscretizer(n_bins=nb, strategy='kmeans', encode='ordinal')
    est.fit(X)
    edges = est.bin_edges_[0]
    mono = np.all(np.diff(edges) >= 0)
    print(f"n_bins={nb} edges={edges} nondecreasing={mono}")
    if not mono:
        ok = False
if not ok:
    print("FAIL: some edges not non-decreasing")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2 + 1.4: interior kmeans edges SHALL be midpoints of consecutive
cluster centers AFTER ascending ordering, bracketed by col min/max as first/
last edge; each interior edge lies strictly between col_min and col_max.
We verify by recomputing: edges[0]==min, edges[-1]==max, and interior edges are
sorted midpoints (each equals mean of two adjacent sorted values recoverable).
Key discriminating check: interior edges are strictly increasing AND lie
within (min,max)."""
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
ok = True
for nb in range(2, 7):
    est = KBinsDiscretizer(n_bins=nb, strategy='kmeans', encode='ordinal')
    est.fit(X)
    edges = est.bin_edges_[0]
    cmin, cmax = X.min(), X.max()
    first_ok = np.isclose(edges[0], cmin)
    last_ok = np.isclose(edges[-1], cmax)
    interior = edges[1:-1]
    within = np.all((interior > cmin) & (interior < cmax)) if len(interior) else True
    incr = np.all(np.diff(edges) > 0)  # non-constant col -> strictly increasing
    print(f"n_bins={nb} first_ok={first_ok} last_ok={last_ok} "
          f"interior_within={within} strictly_incr={incr} edges={edges}")
    if not (first_ok and last_ok and within and incr):
        ok = False
if not ok:
    print("FAIL")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.3: kmeans ordinal codes in [0, n_bins-1], monotonically
non-decreasing for increasing inputs, and clipped at extremes."""
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
ok = True
for nb in range(2, 7):
    est = KBinsDiscretizer(n_bins=nb, strategy='kmeans', encode='ordinal')
    Xt = est.fit_transform(X).ravel()
    n_bins_ = est.n_bins_[0]
    in_range = np.all((Xt >= 0) & (Xt <= n_bins_ - 1))
    nondec = np.all(np.diff(Xt) >= 0)  # X is sorted ascending
    # extremes: below-min and above-max clipped
    Xe = np.array([[-100.0], [1000.0]])
    Xet = est.transform(Xe).ravel()
    clipped = (Xet[0] == 0) and (Xet[1] == n_bins_ - 1)
    print(f"n_bins={nb} codes={Xt.astype(int).tolist()} in_range={in_range} "
          f"nondec={nondec} extremes={Xet.astype(int).tolist()} clipped={clipped}")
    if not (in_range and nondec and clipped):
        ok = False
if not ok:
    print("FAIL")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3 (regression): uniform and quantile strategies unchanged. Uses the
hidden-test expectations for X=[0,0.5,2,3,9,10] at 2,3,5 bins."""
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
cases = {
    'uniform': {2: [0, 0, 0, 0, 1, 1], 3: [0, 0, 0, 0, 2, 2], 5: [0, 0, 1, 1, 4, 4]},
    'quantile': {2: [0, 0, 0, 1, 1, 1], 3: [0, 0, 1, 1, 2, 2], 5: [0, 1, 2, 3, 4, 4]},
}
ok = True
for strat, m in cases.items():
    for nb, exp in m.items():
        est = KBinsDiscretizer(n_bins=nb, strategy=strat, encode='ordinal')
        got = est.fit_transform(X).ravel().astype(int).tolist()
        match = got == exp
        print(f"{strat} n_bins={nb} got={got} exp={exp} match={match}")
        if not match:
            ok = False
if not ok:
    print("FAIL")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.1: constant column -> single bin, warns constant, all transform to 0,
regardless of strategy (n_bins_[0]==1)."""
import warnings
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

ok = True
for strat in ['uniform', 'quantile', 'kmeans']:
    X = np.array([[1.0, 0.0], [1.0, 5.0], [1.0, 9.0], [1.0, 10.0]])
    est = KBinsDiscretizer(n_bins=3, strategy=strat, encode='ordinal')
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        Xt = est.fit_transform(X)
    warned = any("constant" in str(x.message).lower() for x in w)
    col0_zero = np.all(Xt[:, 0] == 0)
    nbins0 = est.n_bins_[0] == 1
    print(f"{strat}: warned_constant={warned} col0_all_zero={col0_zero} "
          f"n_bins_[0]={est.n_bins_[0]}")
    if not (warned and col0_zero and nbins0):
        ok = False
if not ok:
    print("FAIL")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 5.4: inverse_transform maps each code back to the center of its bin,
for kmeans strategy on a non-constant column. Each inverse value must equal the
midpoint of the bin edges the code indexes."""
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
ok = True
for strat in ['uniform', 'quantile', 'kmeans']:
    est = KBinsDiscretizer(n_bins=4, strategy=strat, encode='ordinal')
    Xt = est.fit_transform(X)
    Xinv = est.inverse_transform(Xt)
    edges = est.bin_edges_[0]
    centers = (edges[1:] + edges[:-1]) * 0.5
    codes = Xt.ravel().astype(int)
    expected = centers[codes]
    match = np.allclose(Xinv.ravel(), expected)
    print(f"{strat}: codes={codes.tolist()} inv={Xinv.ravel().tolist()} "
          f"expected_centers={expected.tolist()} match={match}")
    if not match:
        ok = False
if not ok:
    print("FAIL")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 1.3 / hidden test): kmeans n_bins=5 on data whose
cluster centers would otherwise come back out of order must fit_transform
without ValueError and produce the expected ordinal codes [0,0,1,2,3,4].
Holds patched; must FAIL at base (raises ValueError bins must be monotonic)."""
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
est = KBinsDiscretizer(n_bins=5, strategy='kmeans', encode='ordinal')
try:
    Xt = est.fit_transform(X)
except ValueError as e:
    print("FAIL: fit_transform raised ValueError:", e)
    raise SystemExit(1)
got = Xt.ravel().astype(int).tolist()
expected = [0, 0, 1, 2, 3, 4]
print("observed ordinal codes:", got, "expected:", expected)
if got != expected:
    print("FAIL: codes differ from expected")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-13135: gold sorts kmeans cluster centers ascending before deriving midpoint edges. 7 probes cover the requirements:
- probe_1 (POSITIVE CONTROL, Req 1.3 + hidden test): kmeans n_bins=5 on X=[0,0.5,2,3,9,10] fit_transform succeeds AND yields the hidden-test expected codes [0,0,1,2,3,4]. HOLDS patched; FAILS at base -> prepatch_reproduced=true.
- probe_2 (Req 1.1): bin_edges_ non-decreasing for n_bins 2..6. HOLDS patched.
- probe_3 (Req 1.2/1.4): edges[0]==col_min, edges[-1]==col_max, interior edges strictly within (min,max) and strictly increasing. HOLDS patched.
- probe_4 (Req 2.1/2.2/2.3): kmeans ordinal codes in [0,n_bins-1], non-decreasing for increasing inputs, extremes clipped. HOLDS patched.
- probe_5 (Req 3, regression): uniform & quantile ordinal codes match hidden-test expectations at 2/3/5 bins. HOLDS patched.
- probe_6 (Req 4.1): constant column -> warns constant, all zeros, n_bins_[0]==1 for all strategies. HOLDS patched.
- probe_7 (Req 5.4): inverse_transform maps codes to bin centers for all strategies. HOLDS patched.

CANDIDATE (weak.diff, 'naive_sort_edges'): sorts the derived edge array (midpoints of the UNSORTED centers) instead of sorting the centers first. This produces monotonic edges (so it PASSES probes 2,3,4 — the too-weak trap a monotonicity-only spec would admit) but computes WRONG midpoint values, giving codes [0,0,1,1,4,4] instead of [0,0,1,2,3,4]. probe_1 REJECTS it (VIOLATED). This demonstrates the suite discriminates a probe-conforming-on-monotonicity-alone wrong fix, and that the requirements' Req 1.2 (midpoints of *ordered centers*) + Req 2.2 are pinned tightly enough via the hidden-test expectation in probe_1.

All 7 probes HOLD on the gold-patched tree; positive control discriminates (fails at base). Requirements are faithful and not too weak.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control (Req 1.3 / hidden test): kmeans n_bins=5 on data whose
cluster centers would otherwise come back out of order must fit_transform
without ValueError and produce the expected ordinal codes [0,0,1,2,3,4].
Holds patched; must FAIL at base (raises ValueError bins must be monotonic)."""
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer

X = np.array([0, 0.5, 2, 3, 9, 10]).reshape(-1, 1)
est = KBinsDiscretizer(n_bins=5, strategy='kmeans', encode='ordinal')
try:
    Xt = est.fit_transform(X)
except ValueError as e:
    print("FAIL: fit_transform raised ValueError:", e)
    raise SystemExit(1)
got = Xt.ravel().astype(int).tolist()
expected = [0, 0, 1, 2, 3, 4]
print("observed ordinal codes:", got, "expected:", expected)
if got != expected:
    print("FAIL: codes differ from expected")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn-13135: gold sorts kmeans cluster centers ascending before deriving midpoint edges. 7 probes cover the requirements:
- probe_1 (POSITIVE CONTROL, Req 1.3 + hidden test): kmeans n_bins=5 on X=[0,0.5,2,3,9,10] fit_transform succeeds AND yields the hidden-test expected codes [0,0,1,2,3,4]. HOLDS patched; FAILS at base -> prepatch_reproduced=true.
- probe_2 (Req 1.1): bin_edges_ non-decreasing for n_bins 2..6. HOLDS patched.
- probe_3 (Req 1.2/1.4): edges[0]==col_min, edges[-1]==col_max, interior edges strictly within (min,max) and strictly increasing. HOLDS patched.
- probe_4 (Req 2.1/2.2/2.3): kmeans ordinal codes in [0,n_bins-1], non-decreasing for increasing inputs, extremes clipped. HOLDS patched.
- probe_5 (Req 3, regression): uniform & quantile ordinal codes match hidden-test expectations at 2/3/5 bins. HOLDS patched.
- probe_6 (Req 4.1): constant column -> warns constant, all zeros, n_bins_[0]==1 for all strategies. HOLDS patched.
- probe_7 (Req 5.4): inverse_transform maps codes to bin centers for all strategies. HOLDS patched.

CANDIDATE (weak.diff, 'naive_sort_edges'): sorts the derived edge array (midpoints of the UNSORTED centers) instead of sorting the centers first. This produces monotonic edges (so it PASSES probes 2,3,4 — the too-weak trap a monotonicity-only spec would admit) but computes WRONG midpoint values, giving codes [0,0,1,1,4,4] instead of [0,0,1,2,3,4]. probe_1 REJECTS it (VIOLATED). This demonstrates the suite discriminates a probe-conforming-on-monotonicity-alone wrong fix, and that the requirements' Req 1.2 (midpoints of *ordered centers*) + Req 2.2 are pinned tightly enough via the hidden-test expectation in probe_1.

All 7 probes HOLD on the gold-patched tree; positive control discriminates (fails at base). Requirements are faithful and not too weak.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Base probe VIOLATED (exit 1, ValueError in np.digitize); patched probe HOLDS (exit 0). Requirement boundary matches the changed behavior exactly (edge monotonicity / successful ordinal transform), not a narrow helper slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally (order kmeans cluster centers ascending before deriving midpoint edges; ensure bin_edges_ non-decreasing) and legitimately names the module/method (sklearn/preprocessing/_discretization.py, KBinsDiscretizer.fit, bin_edges_, np.digitize) — all needed to localize the change and all present in the public problem_statement, which already includes the full reproduction (X=[0,0.5,2,3,9,10], n_bins=5, strategy='kmeans', encode='ordinal', the exact ValueError, and the digitize traceback). No hidden-test content is transmitted: the added test's expected_5bins arrays ([0,0,1,2,3,4] kmeans, [0,0,1,1,4,4] uniform, [0,1,2,3,4,4] quantile), the test function name test_nonuniform_strategies, parametrization ids, and gold-patch line `centers.sort()` do not appear. Requirements' preservation clauses (uniform/quantile identical, inverse_transform, encode options, constant column, n_bins validation) mirror the PASS_TO_PASS behavior classes but are stated as general API contracts, not case-by-case value enumerations. No fix-invented identifiers (centers.sort() is a stdlib call, not exposed). No case enumerations reconstructing the parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
