# P2 adversarial audit — scikit-learn__scikit-learn-14496

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
# Positive control: OPTICS.fit with float min_samples in (0,1) completes without raising (Req1.3/1.2)
import numpy as np
from sklearn.cluster import OPTICS
rng = np.random.RandomState(0)
X = rng.rand(60, 2)
try:
    clust = OPTICS(min_samples=0.1).fit(X)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    raise SystemExit(1)
assert hasattr(clust, 'labels_') and clust.labels_.shape[0] == 60, "no labels"
print("OK: fit with float min_samples=0.1 produced labels, n_labels=", clust.labels_.shape[0])
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req3.1: xi float min_samples/min_cluster_size equal equivalent integer counts (clean resolve)
import numpy as np
from sklearn.cluster import OPTICS
rng = np.random.RandomState(42)
X = rng.rand(50, 2)
n = X.shape[0]  # 50; 0.1*50=5 -> int=5
lab_float = OPTICS(min_samples=0.1, min_cluster_size=0.1, cluster_method='xi').fit(X).labels_
lab_int   = OPTICS(min_samples=5,   min_cluster_size=5,   cluster_method='xi').fit(X).labels_
print("float labels[:10]", lab_float[:10])
print("int   labels[:10]", lab_int[:10])
if not np.array_equal(lab_float, lab_int):
    print("FAIL: float xi labels differ from integer-equivalent labels")
    raise SystemExit(1)
print("OK: xi float sizing == integer sizing")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.1: truncation toward zero (int), NOT rounding. n=31, 0.19*31=5.89 -> int=5 (round=6)
import numpy as np
from sklearn.cluster import OPTICS, compute_optics_graph
rng = np.random.RandomState(7)
X = rng.rand(31, 2)
n = X.shape[0]
val = 0.19
prod = val * n
print("product =", prod, "int(trunc) =", int(prod))
assert int(prod) == 5 and round(prod) == 6, "test setup: need trunc!=round"
# float resolves to 5 by truncation; compare to explicit integer 5, and ensure it is NOT 6
lab_float = OPTICS(min_samples=val, cluster_method='xi', min_cluster_size=0.19).fit(X).labels_
lab_5 = OPTICS(min_samples=5, cluster_method='xi', min_cluster_size=5).fit(X).labels_
lab_6 = OPTICS(min_samples=6, cluster_method='xi', min_cluster_size=6).fit(X).labels_
eq5 = np.array_equal(lab_float, lab_5)
eq6 = np.array_equal(lab_float, lab_6)
print("equals int(5)?", eq5, " equals round(6)?", eq6)
if not eq5:
    print("FAIL: float 0.19 did not resolve to truncated integer 5")
    raise SystemExit(1)
print("OK: fractional sizing truncated toward zero to 5")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.2: clamp converted count to at least 2. n=50, 0.01*50=0.5 -> int=0 -> max(2,0)=2
import numpy as np
from sklearn.cluster import OPTICS
rng = np.random.RandomState(1)
X = rng.rand(50, 2)
lab_small = OPTICS(min_samples=0.01, cluster_method='xi', min_cluster_size=0.01).fit(X).labels_
lab_two   = OPTICS(min_samples=2, cluster_method='xi', min_cluster_size=2).fit(X).labels_
print("tiny-fraction labels[:10]", lab_small[:10])
print("min=2 labels[:10]        ", lab_two[:10])
if not np.array_equal(lab_small, lab_two):
    print("FAIL: tiny fraction did not clamp to 2")
    raise SystemExit(1)
print("OK: tiny fraction clamped to neighborhood/cluster size 2")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req4.1/4.2: validation preserved - reject bad sizing params with ValueError
import numpy as np
from sklearn.cluster import OPTICS
rng = np.random.RandomState(0)
X = rng.rand(20, 2)
# (a) value > 1 not whole number -> ValueError
try:
    OPTICS(min_samples=2.5).fit(X)
    print("FAIL: 2.5 min_samples accepted"); raise SystemExit(1)
except ValueError as e:
    print("OK reject 2.5:", str(e)[:80])
# (b) non-positive -> ValueError
try:
    OPTICS(min_samples=-3).fit(X)
    print("FAIL: -3 accepted"); raise SystemExit(1)
except ValueError as e:
    print("OK reject -3:", str(e)[:80])
# (c) exceeds n_samples -> ValueError
try:
    OPTICS(min_samples=999).fit(X)
    print("FAIL: 999 accepted"); raise SystemExit(1)
except ValueError as e:
    print("OK reject 999:", str(e)[:80])
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req4.3 & Req1.4: default min_samples is 5, and integer min_samples used directly (equals compute path)
import inspect
from sklearn.cluster import OPTICS
sig = inspect.signature(OPTICS.__init__)
default = sig.parameters['min_samples'].default
print("OPTICS.min_samples default =", default)
if default != 5:
    print("FAIL: default min_samples != 5"); raise SystemExit(1)
# integer path: compute_optics_graph with int uses value directly (no rescale) -> works & equals
import numpy as np
from sklearn.cluster import compute_optics_graph
X = np.random.RandomState(3).rand(40, 2)
res = compute_optics_graph(X, min_samples=5, max_eps=np.inf, metric='minkowski', p=2,
                           metric_params=None, algorithm='auto', leaf_size=30, n_jobs=None)
print("compute_optics_graph int ok, ordering len", len(res[0]))
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: OPTICS.fit with float min_samples in (0,1) completes without raising (Req1.3/1.2)
import numpy as np
from sklearn.cluster import OPTICS
rng = np.random.RandomState(0)
X = rng.rand(60, 2)
try:
    clust = OPTICS(min_samples=0.1).fit(X)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    raise SystemExit(1)
assert hasattr(clust, 'labels_') and clust.labels_.shape[0] == 60, "no labels"
print("OK: fit with float min_samples=0.1 produced labels, n_labels=", clust.labels_.shape[0])
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: OPTICS float min_samples/min_cluster_size must convert to integer neighborhood counts via max(2, int(frac*n)) (truncate toward zero), yielding same clustering as equivalent integer sizing.

Probes (criterion -> result on patched / base / weak.diff):
- probe_1 (Req1.2/1.3, POSITIVE CONTROL): OPTICS(min_samples=0.1).fit succeeds and yields labels. patched=HOLDS, base=VIOLATED (TypeError n_neighbors non-integer), weak=HOLDS. Discriminates.
- probe_2 (Req3.1): xi float(0.1,0.1)==int(5,5) labels on n=50. patched=HOLDS, weak=HOLDS.
- probe_3 (Req1.1 truncation, KEY DISCRIMINATOR): n=31, 0.19*31=5.89 -> int=5 not round=6. patched=HOLDS (equals 5), base=VIOLATED (crash), weak=VIOLATED (equals 6, round). Rejects the round() wrong-fix.
- probe_4 (Req3.2 clamp>=2): tiny fraction 0.01 -> size 2. patched=HOLDS (also base HOLDS since 0.01*50=0.5 clamps to 2 even as float, no int path effect).
- probe_5 (Req4.1/4.2 validation preserved): rejects 2.5, -3, 999 with ValueError. patched=HOLDS.
- probe_6 (Req4.3/1.4): default min_samples==5; integer path compute_optics_graph works directly. patched=HOLDS.

Candidate patch 'round_instead_of_trunc' (weak.diff): replaces int() with round() in both routines — the lazy 'just make it an integer' reading. Satisfies Req1.2/1.3 (fit succeeds) but VIOLATES Req1.1's explicit 'integer part (truncated toward zero)' — REJECTED by probe_3. Suite discriminates the wrong fix; no requirements-conforming alternative found that would fail hidden tests. Verdict SOUND: >=5 probes hold on patched, positive control fails at base and holds patched, and a plausible wrong-fix is caught.

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
# Positive control: OPTICS.fit with float min_samples in (0,1) completes without raising (Req1.3/1.2)
import numpy as np
from sklearn.cluster import OPTICS
rng = np.random.RandomState(0)
X = rng.rand(60, 2)
try:
    clust = OPTICS(min_samples=0.1).fit(X)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    raise SystemExit(1)
assert hasattr(clust, 'labels_') and clust.labels_.shape[0] == 60, "no labels"
print("OK: fit with float min_samples=0.1 produced labels, n_labels=", clust.labels_.shape[0])
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: OPTICS float min_samples/min_cluster_size must convert to integer neighborhood counts via max(2, int(frac*n)) (truncate toward zero), yielding same clustering as equivalent integer sizing.

Probes (criterion -> result on patched / base / weak.diff):
- probe_1 (Req1.2/1.3, POSITIVE CONTROL): OPTICS(min_samples=0.1).fit succeeds and yields labels. patched=HOLDS, base=VIOLATED (TypeError n_neighbors non-integer), weak=HOLDS. Discriminates.
- probe_2 (Req3.1): xi float(0.1,0.1)==int(5,5) labels on n=50. patched=HOLDS, weak=HOLDS.
- probe_3 (Req1.1 truncation, KEY DISCRIMINATOR): n=31, 0.19*31=5.89 -> int=5 not round=6. patched=HOLDS (equals 5), base=VIOLATED (crash), weak=VIOLATED (equals 6, round). Rejects the round() wrong-fix.
- probe_4 (Req3.2 clamp>=2): tiny fraction 0.01 -> size 2. patched=HOLDS (also base HOLDS since 0.01*50=0.5 clamps to 2 even as float, no int path effect).
- probe_5 (Req4.1/4.2 validation preserved): rejects 2.5, -3, 999 with ValueError. patched=HOLDS.
- probe_6 (Req4.3/1.4): default min_samples==5; integer path compute_optics_graph works directly. patched=HOLDS.

Candidate patch 'round_instead_of_trunc' (weak.diff): replaces int() with round() in both routines — the lazy 'just make it an integer' reading. Satisfies Req1.2/1.3 (fit succeeds) but VIOLATES Req1.1's explicit 'integer part (truncated toward zero)' — REJECTED by probe_3. Suite discriminates the wrong fix; no requirements-conforming alternative found that would fail hidden tests. Verdict SOUND: >=5 probes hold on patched, positive control fails at base and holds patched, and a plausible wrong-fix is caught.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed patched tree: labels equal True for float vs equivalent-int sizing; int(0.19*50)=9 confirms truncation-toward-zero wording; tiny fraction 0.01 fits (clamp to 2); ValueErrors reproduce for 3.5, 0, and 100 on n=50. Default min_samples=5 matches patched signature. Requirements pin the actual changed observable behavior (fraction-to-integer conversion), not a narrow slice — the modeling boundary is correct.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior fully covered by the public problem_statement: float min_samples=0.1, the TypeError from NearestNeighbors, the max(2, min_samples*n_samples) rescale, and the int() truncation fix are all in the issue text. Naming compute_optics_graph, cluster_optics_xi, _validate_size, and the default min_samples=5 is legitimate localization (all visible in the gold diff context but constitutes describing the change site, not transmitting tests). No hidden-test artifacts leak: the test's distinctive value min_cluster_size=0.08 is absent; the test function name test_extract_xi, file path, expected_labels arrays, and assert_array_equal structure are absent. Requirement 3's 'fractional resolves to same clustering as equivalent integer' is a behavioral equivalence property (also implied by the docstring), not a parametrization-mirroring enumeration. No fix-invented identifiers appear.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
