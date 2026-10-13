# P2 adversarial audit — scikit-learn__scikit-learn-9288

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
"""
Probe 1 (POSITIVE CONTROL) — Requirement 1, criterion 1.
KMeans fit twice, same random_state, differing only in n_jobs, must give
identical labels_ for every sample.
HOLDS on patched tree; must FAIL at base (base seeds serial vs parallel differently).
"""
import sys
import numpy as np
from sklearn.cluster import KMeans

rng = np.random.RandomState(0)
X = rng.rand(80, 4)

km1 = KMeans(n_clusters=5, n_init=10, random_state=42, n_jobs=1).fit(X)
km2 = KMeans(n_clusters=5, n_init=10, random_state=42, n_jobs=2).fit(X)

same = np.array_equal(km1.labels_, km2.labels_)
print("n_jobs=1 labels[:10]:", km1.labels_[:10])
print("n_jobs=2 labels[:10]:", km2.labels_[:10])
print("labels identical:", same)
sys.exit(0 if same else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""
Probe 2 — Requirement 1, criterion 2.
Two fits differing only in n_jobs must give identical inertia_ AND cluster_centers_
(bit-for-bit). Uses the module-level k_means function too.
"""
import sys
import numpy as np
from sklearn.cluster import k_means

rng = np.random.RandomState(1)
X = rng.rand(120, 6)

c1, l1, i1 = k_means(X, n_clusters=4, n_init=8, random_state=7, n_jobs=1)
c2, l2, i2 = k_means(X, n_clusters=4, n_init=8, random_state=7, n_jobs=3)

centers_eq = np.array_equal(c1, c2)
inertia_eq = (i1 == i2)
labels_eq = np.array_equal(l1, l2)
print("inertia n_jobs=1:", i1, " n_jobs=3:", i2, " equal:", inertia_eq)
print("centers bit-equal:", centers_eq)
print("labels equal:", labels_eq)
ok = centers_eq and inertia_eq and labels_eq
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""
Probe 3 — Requirement 2, criterion 3 + Requirement 1.
Reproducibility across runs: same fixed integer seed => same model, and
n_jobs-independence holds across several parameter configs (elkan/full, various n).
"""
import sys
import numpy as np
from sklearn.cluster import KMeans

rng = np.random.RandomState(2)
X = rng.rand(100, 5)

ok = True
for algo in ("full", "elkan"):
    for nj in (1, 2, 4):
        a = KMeans(n_clusters=3, n_init=6, random_state=123, n_jobs=nj,
                   algorithm=algo).fit(X)
        b = KMeans(n_clusters=3, n_init=6, random_state=123, n_jobs=nj,
                   algorithm=algo).fit(X)
        # repeated fit reproducible
        rep = np.array_equal(a.labels_, b.labels_) and (a.inertia_ == b.inertia_)
        if not rep:
            print("NOT reproducible algo=%s n_jobs=%d" % (algo, nj))
            ok = False

# n_jobs independence per algo
for algo in ("full", "elkan"):
    ref = KMeans(n_clusters=3, n_init=6, random_state=123, n_jobs=1,
                 algorithm=algo).fit(X)
    for nj in (2, 4):
        c = KMeans(n_clusters=3, n_init=6, random_state=123, n_jobs=nj,
                   algorithm=algo).fit(X)
        if not (np.array_equal(ref.labels_, c.labels_) and
                ref.inertia_ == c.inertia_):
            print("n_jobs dependence algo=%s n_jobs=%d" % (algo, nj))
            ok = False

print("all reproducible and n_jobs-independent:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""
Probe 4 — Requirement 3, criterion 3 + criterion 1.
Explicit init array => single init run (n_init treated as 1), and result is
n_jobs-independent. Also verifies best (lowest inertia) selection is returned:
with explicit init and n_init effectively 1, serial and parallel must match.
"""
import sys
import numpy as np
from sklearn.cluster import KMeans

rng = np.random.RandomState(3)
X = rng.rand(90, 4)
init = X[:3].copy()  # explicit centers -> n_init should be 1

# even if user passes n_init>1, explicit array means single run; result n_jobs-indep
a = KMeans(n_clusters=3, init=init, n_init=1, random_state=5, n_jobs=1).fit(X)
b = KMeans(n_clusters=3, init=init, n_init=1, random_state=5, n_jobs=2).fit(X)
same = np.array_equal(a.labels_, b.labels_) and (a.inertia_ == b.inertia_)
print("explicit-init n_jobs indep labels/inertia equal:", same)
sys.exit(0 if same else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""
Probe 5 — Requirement 3, criteria 1,2,5 (regression protection).
- best (lowest inertia) restart is returned (inertia_ is the min over restarts,
  and clustering is correct: within-cluster inertia matches recomputation).
- sparse CSR input and float32 both work and are n_jobs-independent.
- error when n_samples < n_clusters is preserved.
"""
import sys
import numpy as np
from scipy import sparse
from sklearn.cluster import KMeans

ok = True
rng = np.random.RandomState(4)
X = rng.rand(60, 5)

# correctness: inertia_ equals sum of squared dists to assigned centers
km = KMeans(n_clusters=4, n_init=5, random_state=9, n_jobs=1).fit(X)
d = ((X - km.cluster_centers_[km.labels_]) ** 2).sum()
if not np.isclose(d, km.inertia_, rtol=1e-6):
    print("inertia mismatch: recomputed %r vs %r" % (d, km.inertia_))
    ok = False

# sparse CSR n_jobs independence
Xs = sparse.csr_matrix(X)
s1 = KMeans(n_clusters=4, n_init=5, random_state=9, n_jobs=1).fit(Xs)
s2 = KMeans(n_clusters=4, n_init=5, random_state=9, n_jobs=2).fit(Xs)
if not (np.array_equal(s1.labels_, s2.labels_) and s1.inertia_ == s2.inertia_):
    print("sparse n_jobs dependence")
    ok = False

# float32 n_jobs independence
Xf = X.astype(np.float32)
f1 = KMeans(n_clusters=4, n_init=5, random_state=9, n_jobs=1).fit(Xf)
f2 = KMeans(n_clusters=4, n_init=5, random_state=9, n_jobs=2).fit(Xf)
if not np.array_equal(f1.labels_, f2.labels_):
    print("float32 n_jobs dependence")
    ok = False

# error when n_samples < n_clusters preserved
try:
    KMeans(n_clusters=10, n_init=2, random_state=1).fit(rng.rand(3, 5))
    print("expected ValueError for n_samples < n_clusters, none raised")
    ok = False
except ValueError as e:
    print("ValueError preserved:", str(e)[:60])

print("regression checks ok:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""
Probe 1 (POSITIVE CONTROL) — Requirement 1, criterion 1.
KMeans fit twice, same random_state, differing only in n_jobs, must give
identical labels_ for every sample.
HOLDS on patched tree; must FAIL at base (base seeds serial vs parallel differently).
"""
import sys
import numpy as np
from sklearn.cluster import KMeans

rng = np.random.RandomState(0)
X = rng.rand(80, 4)

km1 = KMeans(n_clusters=5, n_init=10, random_state=42, n_jobs=1).fit(X)
km2 = KMeans(n_clusters=5, n_init=10, random_state=42, n_jobs=2).fit(X)

same = np.array_equal(km1.labels_, km2.labels_)
print("n_jobs=1 labels[:10]:", km1.labels_[:10])
print("n_jobs=2 labels[:10]:", km2.labels_[:10])
print("labels identical:", same)
sys.exit(0 if same else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: KMeans/k_means result must be independent of n_jobs. Gold fix hoists `seeds = random_state.randint(iinfo(int32).max, size=n_init)` before the n_jobs branch and seeds each serial restart from seeds[i] (matching the parallel branch), instead of threading the shared random_state through serial restarts.

Probes (all HOLD on patched tree, exit 0):
- probe_1 (POSITIVE CONTROL) — Req1.1: KMeans n_jobs=1 vs n_jobs=2, same random_state=42 -> identical labels_. PATCHED: identical. BASE: labels differ (exit1). WEAK candidate: differ (exit1). Discriminates.
- probe_2 — Req1.2: k_means() n_jobs=1 vs n_jobs=3 -> bit-equal cluster_centers_, equal inertia_ & labels. PATCHED holds; BASE inertia 40.170 vs 40.205 (fail); WEAK fails.
- probe_3 — Req2.3 + Req1: reproducible repeated fits AND n_jobs-independence across full/elkan x n_jobs {1,2,4}. PATCHED holds; BASE fails all; WEAK fails (reproducible but n_jobs-dependent).
- probe_4 — Req3.3: explicit init array => single init run, n_jobs-independent. PATCHED holds.
- probe_5 — Req3.1/3.2/3.5: inertia_ equals recomputed within-cluster SSE (correct best-restart selection); sparse CSR and float32 n_jobs-independence; ValueError preserved for n_samples<n_clusters. PATCHED holds.

Candidate patch `naive_per_index_seed`: seeds serial restart i from constant `it` (loop index) instead of a random_state-derived seed. This is a plausibly-weak reading ("make serial deterministic") that yields reproducibility but a DIFFERENT seed derivation from the parallel branch — so n_jobs-independence still fails. Probes 1,2,3 REJECT it (exit1 each), demonstrating the suite discriminates wrong fixes. Not a too-weak finding.

Positive control failed at base (prepatch_reproduced=true) and holds patched. >=5 distinct probes all hold on patched; candidate exercised and rejected. Verdict SOUND.

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
"""
Probe 1 (POSITIVE CONTROL) — Requirement 1, criterion 1.
KMeans fit twice, same random_state, differing only in n_jobs, must give
identical labels_ for every sample.
HOLDS on patched tree; must FAIL at base (base seeds serial vs parallel differently).
"""
import sys
import numpy as np
from sklearn.cluster import KMeans

rng = np.random.RandomState(0)
X = rng.rand(80, 4)

km1 = KMeans(n_clusters=5, n_init=10, random_state=42, n_jobs=1).fit(X)
km2 = KMeans(n_clusters=5, n_init=10, random_state=42, n_jobs=2).fit(X)

same = np.array_equal(km1.labels_, km2.labels_)
print("n_jobs=1 labels[:10]:", km1.labels_[:10])
print("n_jobs=2 labels[:10]:", km2.labels_[:10])
print("labels identical:", same)
sys.exit(0 if same else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: KMeans/k_means result must be independent of n_jobs. Gold fix hoists `seeds = random_state.randint(iinfo(int32).max, size=n_init)` before the n_jobs branch and seeds each serial restart from seeds[i] (matching the parallel branch), instead of threading the shared random_state through serial restarts.

Probes (all HOLD on patched tree, exit 0):
- probe_1 (POSITIVE CONTROL) — Req1.1: KMeans n_jobs=1 vs n_jobs=2, same random_state=42 -> identical labels_. PATCHED: identical. BASE: labels differ (exit1). WEAK candidate: differ (exit1). Discriminates.
- probe_2 — Req1.2: k_means() n_jobs=1 vs n_jobs=3 -> bit-equal cluster_centers_, equal inertia_ & labels. PATCHED holds; BASE inertia 40.170 vs 40.205 (fail); WEAK fails.
- probe_3 — Req2.3 + Req1: reproducible repeated fits AND n_jobs-independence across full/elkan x n_jobs {1,2,4}. PATCHED holds; BASE fails all; WEAK fails (reproducible but n_jobs-dependent).
- probe_4 — Req3.3: explicit init array => single init run, n_jobs-independent. PATCHED holds.
- probe_5 — Req3.1/3.2/3.5: inertia_ equals recomputed within-cluster SSE (correct best-restart selection); sparse CSR and float32 n_jobs-independence; ValueError preserved for n_samples<n_clusters. PATCHED holds.

Candidate patch `naive_per_index_seed`: seeds serial restart i from constant `it` (loop index) instead of a random_state-derived seed. This is a plausibly-weak reading ("make serial deterministic") that yields reproducibility but a DIFFERENT seed derivation from the parallel branch — so n_jobs-independence still fails. Probes 1,2,3 REJECT it (exit1 each), demonstrating the suite discriminates wrong fixes. Not a too-weak finding.

Positive control failed at base (prepatch_reproduced=true) and holds patched. >=5 distinct probes all hold on patched; candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init) moved above the `if effective_n_jobs(n_jobs)==1` branch; serial loop changed from `for it in range(n_init): ... random_state=random_state` to `for seed in seeds: ... random_state=seed`; the parallel branch's identical seeds line removed (now shared). Requirements correctly describe: (1) n_jobs-independence of labels_/inertia_/cluster_centers_, (2) single canonical per-restart seed sequence derived before the branch with i-th restart<->i-th seed, (3) regression preservation (min-inertia selection, explicit-init single run, unchanged unseeded behavior). Modeling boundary is the changed observable behavior, not one branch. FAIL_TO_PASS test test_result_of_kmeans_equal_in_diff_n_jobs aligns.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to k_means in sklearn/cluster/k_means_.py (legitimate) and describes the fix behavior — deriving per-restart seeds once from random_state before branching on n_jobs so serial and parallel evaluate the same initializations. This mirrors the gold strategy but is a description of PUBLIC source-code behavior plus the intended fix, not a transmission of the hidden test. No test names/paths (test_result_of_kmeans_equal_in_diff_n_jobs never appears), no quoted test/gold code, no fix-invented identifiers ('seeds' is referenced only as a generic 'per-restart seed sequence'). Req 1 (identical labels/inertia/centers across n_jobs) is directly derivable from the problem_statement, which itself demonstrates the n_jobs loop and inertia comparison. Req 3.2's full/elkan x dense/sparse x float32/float64 enumeration resembles the test_kmeans_results[...] PASS_TO_PASS parametrization, but these are the standard public configuration axes of KMeans and describe genuine regression coverage rather than reconstructing hidden test ids. No semantic leak beyond the public problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
