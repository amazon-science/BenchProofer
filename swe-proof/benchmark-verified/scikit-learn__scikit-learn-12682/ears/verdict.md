# P2 adversarial audit — scikit-learn__scikit-learn-12682

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
"""Positive control — R2.1/R2.2/R2.3 & R1.1/R1.3: the configured budget genuinely
governs convergence of the coordinate-descent (lasso_cd) solver.

transform_max_iter=1  -> solver cannot converge -> ConvergenceWarning emitted.
transform_max_iter=2000 -> solver converges -> NO ConvergenceWarning.
Holds on gold-patched; must FAIL at base (base SparseCoder has no such lever
and the default cap of 1000 already converges => no warning at "=1").
"""
import warnings
import numpy as np
from sklearn.decomposition import SparseCoder
from sklearn.exceptions import ConvergenceWarning


def ricker_function(resolution, center, width):
    x = np.linspace(0, resolution - 1, resolution)
    x = ((2 / (np.sqrt(3 * width) * np.pi ** .25))
         * (1 - (x - center) ** 2 / width ** 2)
         * np.exp(-(x - center) ** 2 / (2 * width ** 2)))
    return x


def ricker_matrix(width, resolution, n_components):
    centers = np.linspace(0, resolution - 1, n_components)
    D = np.empty((n_components, resolution))
    for i, center in enumerate(centers):
        D[i] = ricker_function(resolution, center, width)
    D /= np.sqrt(np.sum(D ** 2, axis=1))[:, np.newaxis]
    return D


resolution = 1024
subsampling = 3
n_components = resolution // subsampling
D_multi = np.r_[tuple(ricker_matrix(width=w, resolution=resolution,
                      n_components=n_components // 5)
                      for w in (10, 50, 100, 500, 1000))]
X = np.linspace(0, resolution - 1, resolution)
first_quarter = X < resolution / 4
X[first_quarter] = 3.
X[np.logical_not(first_quarter)] = -1.
X = X.reshape(1, -1)

# case 1: tiny budget -> ConvergenceWarning
with warnings.catch_warnings(record=True) as rec1:
    warnings.simplefilter("always")
    m = SparseCoder(D_multi, transform_algorithm='lasso_cd', transform_max_iter=1)
    m.fit_transform(X)
saw_warn_small = any(issubclass(w.category, ConvergenceWarning) for w in rec1)

# case 2: large budget -> no warning at all
with warnings.catch_warnings(record=True) as rec2:
    warnings.simplefilter("always")
    m = SparseCoder(D_multi, transform_algorithm='lasso_cd', transform_max_iter=2000)
    m.fit_transform(X)
saw_any_warn_large = len(rec2) > 0

print("small-budget ConvergenceWarning:", saw_warn_small)
print("large-budget any warning:", saw_any_warn_large, [str(w.category.__name__) for w in rec2])

ok = saw_warn_small and not saw_any_warn_large
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.1 & R1.2: SparseCoder constructor accepts an optional integer
transform_max_iter defaulting to 1000, records it on the estimator, and does not
disturb the other constructor options.
"""
import numpy as np
from sklearn.decomposition import SparseCoder

D = np.random.RandomState(0).randn(4, 6)

# default is 1000
c_default = SparseCoder(D, transform_algorithm='omp')
print("default transform_max_iter:", getattr(c_default, "transform_max_iter", "<MISSING>"))

# supplied value is recorded, other options preserved
c = SparseCoder(D, transform_algorithm='lasso_cd',
                transform_n_nonzero_coefs=3, transform_alpha=0.5,
                split_sign=True, n_jobs=2, positive_code=True,
                transform_max_iter=1234)
checks = {
    "transform_max_iter==1234": c.transform_max_iter == 1234,
    "algorithm preserved": c.transform_algorithm == 'lasso_cd',
    "n_nonzero preserved": c.transform_n_nonzero_coefs == 3,
    "alpha preserved": c.transform_alpha == 0.5,
    "split_sign preserved": c.split_sign is True,
    "n_jobs preserved": c.n_jobs == 2,
    "positive_code preserved": c.positive_code is True,
    "default is 1000": getattr(c_default, "transform_max_iter", None) == 1000,
}
for k, v in checks.items():
    print(k, v)

ok = all(checks.values())
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.3: SparseCoder.transform passes the configured budget to sparse_encode.
Intercept the module-level sparse_encode call transform() makes and confirm the
max_iter kwarg equals the configured transform_max_iter (not a fixed 1000).
"""
import importlib
import numpy as np
from sklearn.decomposition import SparseCoder

dl = importlib.import_module("sklearn.decomposition.dict_learning")
real = dl.sparse_encode
captured = {}


def spy(X, dictionary, **kwargs):
    captured.update(kwargs)
    return np.zeros((X.shape[0], dictionary.shape[0]))


D = np.random.RandomState(0).randn(4, 3)
coder = SparseCoder(D, transform_algorithm='lasso_cd', transform_max_iter=777)
X = np.random.RandomState(1).randn(2, 3)
dl.sparse_encode = spy
try:
    coder.transform(X)
finally:
    dl.sparse_encode = real

got = captured.get("max_iter", "<NOT PASSED>")
print("max_iter forwarded to sparse_encode:", got)
ok = got == 777
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1: sparse_encode forwards max_iter to the solver for BOTH lasso_cd AND
lasso_lars (not only one). Intercept the LassoLars and Lasso classes used inside
the dict_learning module and assert each receives our max_iter.
"""
import importlib
import numpy as np

dl = importlib.import_module("sklearn.decomposition.dict_learning")

captured = {"lars": None, "cd": None}

RealLassoLars = dl.LassoLars
RealLasso = dl.Lasso


class SpyLassoLars(RealLassoLars):
    def __init__(self, *a, max_iter=500, **k):
        captured["lars"] = max_iter
        super().__init__(*a, max_iter=max_iter, **k)


class SpyLasso(RealLasso):
    def __init__(self, *a, max_iter=1000, **k):
        captured["cd"] = max_iter
        super().__init__(*a, max_iter=max_iter, **k)


rng = np.random.RandomState(0)
D = rng.randn(4, 8)
X = rng.randn(3, 8)

dl.LassoLars = SpyLassoLars
dl.Lasso = SpyLasso
try:
    dl.sparse_encode(X, D, algorithm='lasso_lars', alpha=1.0, max_iter=321)
    dl.sparse_encode(X, D, algorithm='lasso_cd', alpha=1.0, max_iter=654)
finally:
    dl.LassoLars = RealLassoLars
    dl.Lasso = RealLasso

print("LassoLars received max_iter:", captured["lars"])
print("Lasso received max_iter:", captured["cd"])
ok = captured["lars"] == 321 and captured["cd"] == 654
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.2 & R3.3: dict_learning and dict_learning_online accept a method_max_iter
parameter (default 1000) and forward it to their internal sparse_encode calls.
Intercept sparse_encode inside the module and check the forwarded max_iter.
"""
import importlib
import inspect
import numpy as np

dl = importlib.import_module("sklearn.decomposition.dict_learning")

# default 1000 in both signatures
sig_dl = inspect.signature(dl.dict_learning)
sig_dlo = inspect.signature(dl.dict_learning_online)
d1 = sig_dl.parameters.get("method_max_iter")
d2 = sig_dlo.parameters.get("method_max_iter")
print("dict_learning method_max_iter default:", None if d1 is None else d1.default)
print("dict_learning_online method_max_iter default:", None if d2 is None else d2.default)

real = dl.sparse_encode
seen = []


def spy(X, dictionary, **kwargs):
    seen.append(kwargs.get("max_iter"))
    return np.zeros((X.shape[0], dictionary.shape[0]))


rng = np.random.RandomState(0)
X = rng.randn(6, 8)

dl.sparse_encode = spy
try:
    dl.dict_learning(X, n_components=4, alpha=1.0, max_iter=2,
                     method='cd', method_max_iter=222)
    seen_dl = list(seen)
    seen.clear()
    dl.dict_learning_online(X, n_components=4, alpha=1.0, n_iter=3,
                            method='cd', method_max_iter=333,
                            batch_size=2)
    seen_dlo = list(seen)
finally:
    dl.sparse_encode = real

print("dict_learning forwarded max_iters:", seen_dl)
print("dict_learning_online forwarded max_iters:", seen_dlo)

ok = (d1 is not None and d1.default == 1000 and
      d2 is not None and d2.default == 1000 and
      len(seen_dl) > 0 and all(v == 222 for v in seen_dl) and
      len(seen_dlo) > 0 and all(v == 333 for v in seen_dlo))
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.1/R4.2/R4.3: DictionaryLearning and MiniBatchDictionaryLearning accept
transform_max_iter (default 1000), record it, and forward it into their
dict_learning / dict_learning_online routines' sparse-coding step.
"""
import importlib
import numpy as np
from sklearn.decomposition import DictionaryLearning, MiniBatchDictionaryLearning

dl = importlib.import_module("sklearn.decomposition.dict_learning")

# defaults + recording
dlrn = DictionaryLearning(n_components=3, transform_max_iter=1000)
mb = MiniBatchDictionaryLearning(n_components=3)
print("DL transform_max_iter:", getattr(dlrn, "transform_max_iter", "<MISSING>"))
print("MB default transform_max_iter:", getattr(mb, "transform_max_iter", "<MISSING>"))

# forwarding via method_max_iter into dict_learning / dict_learning_online
real_dlf = dl.dict_learning
real_dlo = dl.dict_learning_online
seen = {}


def spy_dl(X, n_components, alpha, **kwargs):
    seen["dl"] = kwargs.get("method_max_iter")
    return real_dlf(X, n_components, alpha, **kwargs)


def spy_dlo(X, n_components=2, alpha=1, **kwargs):
    seen["dlo"] = kwargs.get("method_max_iter")
    return real_dlo(X, n_components, alpha, **kwargs)


rng = np.random.RandomState(0)
X = rng.randn(10, 8)

dl.dict_learning = spy_dl
dl.dict_learning_online = spy_dlo
try:
    DictionaryLearning(n_components=3, max_iter=2, fit_algorithm='cd',
                       transform_max_iter=456).fit(X)
    MiniBatchDictionaryLearning(n_components=3, n_iter=2, fit_algorithm='cd',
                                transform_max_iter=789).fit(X)
finally:
    dl.dict_learning = real_dlf
    dl.dict_learning_online = real_dlo

print("DictionaryLearning.fit forwarded method_max_iter:", seen.get("dl"))
print("MiniBatch.fit forwarded method_max_iter:", seen.get("dlo"))

ok = (getattr(dlrn, "transform_max_iter", None) == 1000 and
      getattr(mb, "transform_max_iter", None) == 1000 and
      seen.get("dl") == 456 and seen.get("dlo") == 789)
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R5 regression: shapes across algorithms (R5.1), positivity honored & rejected
where unsupported (R5.2), unknown algorithm rejected (R5.3), split-sign doubles
feature width (R5.4). All must still hold under the new option.
"""
import numpy as np
from sklearn.decomposition import sparse_encode, SparseCoder

rng = np.random.RandomState(0)
n_components, n_features, n_samples = 8, 6, 5
D = rng.randn(n_components, n_features)
X = rng.randn(n_samples, n_features)

ok = True

# R5.1: shapes across supported algorithms
for algo in ("omp", "lars", "lasso_lars", "lasso_cd", "threshold"):
    code = sparse_encode(X, D, algorithm=algo, alpha=1.0, n_nonzero_coefs=3)
    good = code.shape == (n_samples, n_components)
    print(f"shape[{algo}]:", code.shape, good)
    ok = ok and good

# R5.2: positivity honored for algorithms that support it
for algo in ("lasso_lars", "lasso_cd", "threshold"):
    code = sparse_encode(X, D, algorithm=algo, alpha=1.0, positive=True)
    nonneg = (code >= 0).all()
    print(f"positive[{algo}] nonneg:", nonneg)
    ok = ok and nonneg

# R5.2: positivity rejected where unsupported (omp, lars)
for algo in ("omp", "lars"):
    try:
        sparse_encode(X, D, algorithm=algo, alpha=1.0, positive=True)
        print(f"positive[{algo}] wrongly accepted")
        ok = False
    except ValueError:
        print(f"positive[{algo}] rejected: ok")

# R5.3: unknown algorithm rejected
try:
    sparse_encode(X, D, algorithm="nope")
    print("unknown algorithm wrongly accepted")
    ok = False
except ValueError:
    print("unknown algorithm rejected: ok")

# R5.4: split-sign doubles code width
coder = SparseCoder(D, transform_algorithm='threshold', transform_alpha=1.0,
                    split_sign=True)
split_code = coder.transform(X)
good_split = split_code.shape == (n_samples, 2 * n_components)
print("split-sign shape:", split_code.shape, good_split)
ok = ok and good_split

print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — R2.1/R2.2/R2.3 & R1.1/R1.3: the configured budget genuinely
governs convergence of the coordinate-descent (lasso_cd) solver.

transform_max_iter=1  -> solver cannot converge -> ConvergenceWarning emitted.
transform_max_iter=2000 -> solver converges -> NO ConvergenceWarning.
Holds on gold-patched; must FAIL at base (base SparseCoder has no such lever
and the default cap of 1000 already converges => no warning at "=1").
"""
import warnings
import numpy as np
from sklearn.decomposition import SparseCoder
from sklearn.exceptions import ConvergenceWarning


def ricker_function(resolution, center, width):
    x = np.linspace(0, resolution - 1, resolution)
    x = ((2 / (np.sqrt(3 * width) * np.pi ** .25))
         * (1 - (x - center) ** 2 / width ** 2)
         * np.exp(-(x - center) ** 2 / (2 * width ** 2)))
    return x


def ricker_matrix(width, resolution, n_components):
    centers = np.linspace(0, resolution - 1, n_components)
    D = np.empty((n_components, resolution))
    for i, center in enumerate(centers):
        D[i] = ricker_function(resolution, center, width)
    D /= np.sqrt(np.sum(D ** 2, axis=1))[:, np.newaxis]
    return D


resolution = 1024
subsampling = 3
n_components = resolution // subsampling
D_multi = np.r_[tuple(ricker_matrix(width=w, resolution=resolution,
                      n_components=n_components // 5)
                      for w in (10, 50, 100, 500, 1000))]
X = np.linspace(0, resolution - 1, resolution)
first_quarter = X < resolution / 4
X[first_quarter] = 3.
X[np.logical_not(first_quarter)] = -1.
X = X.reshape(1, -1)

# case 1: tiny budget -> ConvergenceWarning
with warnings.catch_warnings(record=True) as rec1:
    warnings.simplefilter("always")
    m = SparseCoder(D_multi, transform_algorithm='lasso_cd', transform_max_iter=1)
    m.fit_transform(X)
saw_warn_small = any(issubclass(w.category, ConvergenceWarning) for w in rec1)

# case 2: large budget -> no warning at all
with warnings.catch_warnings(record=True) as rec2:
    warnings.simplefilter("always")
    m = SparseCoder(D_multi, transform_algorithm='lasso_cd', transform_max_iter=2000)
    m.fit_transform(X)
saw_any_warn_large = len(rec2) > 0

print("small-budget ConvergenceWarning:", saw_warn_small)
print("large-budget any warning:", saw_any_warn_large, [str(w.category.__name__) for w in rec2])

ok = saw_warn_small and not saw_any_warn_large
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering all 5 requirements, all HOLD on gold-patched tree. Probe mapping: probe_1 (R1.1/R1.3/R2.1-2.3 positive control: lasso_cd, transform_max_iter=1 => ConvergenceWarning, =2000 => no warning); probe_2 (R1.1/R1.2 ctor accepts transform_max_iter default 1000, records it, other options preserved); probe_3 (R1.3 transform forwards budget to sparse_encode via interception, got max_iter=777); probe_4 (R3.1 sparse_encode forwards max_iter to BOTH lasso_lars AND lasso_cd solvers); probe_5 (R3.2/R3.3 dict_learning + dict_learning_online accept method_max_iter default 1000 and forward it); probe_6 (R4.1-4.3 DictionaryLearning/MiniBatchDictionaryLearning record transform_max_iter and forward as method_max_iter); probe_7 (R5 regression: shapes across omp/lars/lasso_lars/lasso_cd/threshold, positivity honored & rejected for omp/lars, unknown algo rejected, split-sign doubles width).

Positive control (probe_1) HOLDS on patched, FAILS at base with TypeError: __init__() got an unexpected keyword argument 'transform_max_iter' — discriminates base vs patched.

Weak candidate 'weak_lasso_lars_missing' = gold patch minus the `LassoLars(..., max_iter=max_iter)` hunk in _sparse_encode. This is the lazy fix a weak reading of the requirements permits (thread the budget for lasso_cd only), and it explicitly violates R3.1 ('forward ... for BOTH ... rather than passing it to only one of them'). The probe suite REJECTS it: probe_4 shows LassoLars still receives its default max_iter=500 instead of the requested 321 (exit 1). This weak fix would also fail the hidden F2P conceptually for lasso_lars usage. 1/1 weak candidate rejected => suite discriminates wrong implementations. All required legs complete; verdict SOUND.

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
"""Positive control — R2.1/R2.2/R2.3 & R1.1/R1.3: the configured budget genuinely
governs convergence of the coordinate-descent (lasso_cd) solver.

transform_max_iter=1  -> solver cannot converge -> ConvergenceWarning emitted.
transform_max_iter=2000 -> solver converges -> NO ConvergenceWarning.
Holds on gold-patched; must FAIL at base (base SparseCoder has no such lever
and the default cap of 1000 already converges => no warning at "=1").
"""
import warnings
import numpy as np
from sklearn.decomposition import SparseCoder
from sklearn.exceptions import ConvergenceWarning


def ricker_function(resolution, center, width):
    x = np.linspace(0, resolution - 1, resolution)
    x = ((2 / (np.sqrt(3 * width) * np.pi ** .25))
         * (1 - (x - center) ** 2 / width ** 2)
         * np.exp(-(x - center) ** 2 / (2 * width ** 2)))
    return x


def ricker_matrix(width, resolution, n_components):
    centers = np.linspace(0, resolution - 1, n_components)
    D = np.empty((n_components, resolution))
    for i, center in enumerate(centers):
        D[i] = ricker_function(resolution, center, width)
    D /= np.sqrt(np.sum(D ** 2, axis=1))[:, np.newaxis]
    return D


resolution = 1024
subsampling = 3
n_components = resolution // subsampling
D_multi = np.r_[tuple(ricker_matrix(width=w, resolution=resolution,
                      n_components=n_components // 5)
                      for w in (10, 50, 100, 500, 1000))]
X = np.linspace(0, resolution - 1, resolution)
first_quarter = X < resolution / 4
X[first_quarter] = 3.
X[np.logical_not(first_quarter)] = -1.
X = X.reshape(1, -1)

# case 1: tiny budget -> ConvergenceWarning
with warnings.catch_warnings(record=True) as rec1:
    warnings.simplefilter("always")
    m = SparseCoder(D_multi, transform_algorithm='lasso_cd', transform_max_iter=1)
    m.fit_transform(X)
saw_warn_small = any(issubclass(w.category, ConvergenceWarning) for w in rec1)

# case 2: large budget -> no warning at all
with warnings.catch_warnings(record=True) as rec2:
    warnings.simplefilter("always")
    m = SparseCoder(D_multi, transform_algorithm='lasso_cd', transform_max_iter=2000)
    m.fit_transform(X)
saw_any_warn_large = len(rec2) > 0

print("small-budget ConvergenceWarning:", saw_warn_small)
print("large-budget any warning:", saw_any_warn_large, [str(w.category.__name__) for w in rec2])

ok = saw_warn_small and not saw_any_warn_large
print("PASS" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering all 5 requirements, all HOLD on gold-patched tree. Probe mapping: probe_1 (R1.1/R1.3/R2.1-2.3 positive control: lasso_cd, transform_max_iter=1 => ConvergenceWarning, =2000 => no warning); probe_2 (R1.1/R1.2 ctor accepts transform_max_iter default 1000, records it, other options preserved); probe_3 (R1.3 transform forwards budget to sparse_encode via interception, got max_iter=777); probe_4 (R3.1 sparse_encode forwards max_iter to BOTH lasso_lars AND lasso_cd solvers); probe_5 (R3.2/R3.3 dict_learning + dict_learning_online accept method_max_iter default 1000 and forward it); probe_6 (R4.1-4.3 DictionaryLearning/MiniBatchDictionaryLearning record transform_max_iter and forward as method_max_iter); probe_7 (R5 regression: shapes across omp/lars/lasso_lars/lasso_cd/threshold, positivity honored & rejected for omp/lars, unknown algo rejected, split-sign doubles width).

Positive control (probe_1) HOLDS on patched, FAILS at base with TypeError: __init__() got an unexpected keyword argument 'transform_max_iter' — discriminates base vs patched.

Weak candidate 'weak_lasso_lars_missing' = gold patch minus the `LassoLars(..., max_iter=max_iter)` hunk in _sparse_encode. This is the lazy fix a weak reading of the requirements permits (thread the budget for lasso_cd only), and it explicitly violates R3.1 ('forward ... for BOTH ... rather than passing it to only one of them'). The probe suite REJECTS it: probe_4 shows LassoLars still receives its default max_iter=500 instead of the requested 321 (exit 1). This weak fix would also fail the hidden F2P conceptually for lasso_lars usage. 1/1 weak candidate rejected => suite discriminates wrong implementations. All required legs complete; verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified via nl_attack probe on gold-patched tree: RESULT {"default": 1000, "small_CW": 20, "large_CW": 0, "lasso_lars_maxiter": true, "dl_default": 1000, "dlo_default": 1000}. The patch's core observable change is exactly threading a max_iter budget from the estimators through sparse_encode/_sparse_encode into both the Lasso (lasso_cd) and LassoLars (lasso_lars) solvers, plus the module-level dict_learning/dict_learning_online method_max_iter param. R2 pins the changed OBSERVABLE behavior (warning presence keyed on user value), not a narrow internal helper — correct modeling boundary. R3.1 specifically demands forwarding to BOTH algorithms 'rather than passing it to only one of them', which precisely captures the pre-patch defect (lasso_lars lacked max_iter). R5 regression clauses restate preserved behavior; consistent with the patch touching only signatures/threading. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior without transmitting hidden-test or gold content. (1) The gold-invented identifiers `transform_max_iter` and `method_max_iter` are never named — the doc uses generic prose ('an optional integer option/parameter'). (2) The F2P test's specific values (transform_max_iter=1 fails, 2000 converges, lasso_cd) are not reproduced; Req 2 uses 'far too small'/'large enough' behavioral phrasing traceable to the ConvergenceWarning already in the public problem_statement. (3) No test function name (test_max_iter), test file path, Ricker-wavelet code, or pytest.warns scaffolding appears. (4) The algorithm list (omp, lars, lasso_lars, lasso_cd, threshold) and function/module names are legitimate public sklearn API localization, not a reconstruction of PASS_TO_PASS parametrization ids. The default of 1000 is stated in the public problem_statement. All content is either public or a legitimate behavioral translation.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
