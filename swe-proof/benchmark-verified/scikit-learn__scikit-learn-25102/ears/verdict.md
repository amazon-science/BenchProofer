# P2 adversarial audit — scikit-learn__scikit-learn-25102

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
"""Positive control: Req1 - per-column dtypes preserved in pandas output.
Mixed float32/float64/category columns keep their dtype after transform.
The category column is made predictive so it is retained.
Exit 0 iff every retained column keeps its original dtype AND a category
column is among the retained set."""
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif

rng = np.random.RandomState(0)
n = 60
y = rng.randint(0, 2, n)
X = pd.DataFrame({
    "a": rng.rand(n).astype(np.float32),
    "b": (y + 0.01 * rng.rand(n)).astype(np.float64),   # predictive float64
    "c": pd.Categorical(y),                              # predictive category
    "d": rng.rand(n).astype(np.float32),
    "e": rng.rand(n).astype(np.float64),
})

sel = SelectKBest(f_classif, k=3)
Xfit = X.copy()
Xfit["c"] = X["c"].cat.codes.astype(np.float64)
sel.fit(Xfit, y)
sel.set_output(transform="pandas")

out = sel.transform(X)
print("input dtypes:\n", X.dtypes)
print("output columns:", list(out.columns))
print("output dtypes:\n", out.dtypes)

ok = True
for col in out.columns:
    if str(out[col].dtype) != str(X[col].dtype):
        print(f"MISMATCH {col}: {out[col].dtype} != {X[col].dtype}")
        ok = False
has_cat = any(str(out[c].dtype) == "category" for c in out.columns)
print("category retained:", has_cat)
if not ok or not has_cat:
    raise SystemExit(1)
print("PASS: all retained columns preserved dtype incl. category")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2: pandas output columns == exactly get_support() selection, in input
order, with original labels. Exit 0 iff output columns match the support mask
labels in the original relative order."""
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif

rng = np.random.RandomState(1)
n = 50
y = rng.randint(0, 2, n)
cols = ["c0", "c1", "c2", "c3", "c4", "c5"]
data = {}
for i, c in enumerate(cols):
    # make some predictive to vary selection
    if i in (1, 3, 5):
        data[c] = (y + 0.1 * rng.rand(n)).astype(np.float64)
    else:
        data[c] = rng.rand(n).astype(np.float64)
X = pd.DataFrame(data)

sel = SelectKBest(f_classif, k=3)
sel.fit(X, y)
sel.set_output(transform="pandas")
out = sel.transform(X)

support = sel.get_support()
expected = [cols[i] for i in range(len(cols)) if support[i]]
print("support:", support)
print("expected labels (input order):", expected)
print("output columns:", list(out.columns))
if list(out.columns) != expected:
    raise SystemExit(1)
print("PASS: output columns match support mask in input order")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3: row count and row index preserved in pandas output. Uses a non-default
index. Exit 0 iff output row count == input and index is identical."""
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif

rng = np.random.RandomState(2)
n = 30
y = rng.randint(0, 2, n)
idx = [f"row_{i*3}" for i in range(n)]
X = pd.DataFrame(
    {f"c{i}": (y * (i % 2) + rng.rand(n)).astype(np.float64) for i in range(5)},
    index=idx,
)

sel = SelectKBest(f_classif, k=2)
sel.fit(X, y)
sel.set_output(transform="pandas")
out = sel.transform(X)

print("input index head:", list(X.index[:3]))
print("output index head:", list(out.index[:3]))
print("shapes:", X.shape, out.shape)
if out.shape[0] != X.shape[0]:
    raise SystemExit(1)
if list(out.index) != list(X.index):
    raise SystemExit(1)
print("PASS: rows and index preserved")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req4: empty selection with pandas output -> DataFrame with 0 columns, same
rows, same index, AND a UserWarning is emitted. Force zero features via
SelectKBest with all-identical (constant) features so scores are NaN and
GenericUnivariateSelect / threshold yields nothing -> use SelectPercentile
percentile=0. Exit 0 iff empty-but-well-formed pandas result + warning."""
import warnings
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectPercentile, f_classif

rng = np.random.RandomState(3)
n = 25
y = rng.randint(0, 2, n)
idx = [f"r{i}" for i in range(n)]
X = pd.DataFrame(
    {f"c{i}": (y * (i % 2) + rng.rand(n)).astype(np.float64) for i in range(4)},
    index=idx,
)

sel = SelectPercentile(f_classif, percentile=0)  # selects nothing
sel.fit(X, y)
sel.set_output(transform="pandas")

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    out = sel.transform(X)

print("type:", type(out).__name__)
print("shape:", getattr(out, "shape", None))
print("n warnings:", len(w))
msgs = [str(x.message) for x in w if issubclass(x.category, UserWarning)]
print("user warnings:", msgs)

ok = isinstance(out, pd.DataFrame)
ok &= out.shape == (n, 0)
ok &= list(out.index) == idx
ok &= any("no features were selected" in m.lower() or "no feature" in m.lower() for m in msgs)
if not ok:
    raise SystemExit(1)
print("PASS: empty pandas result well-formed with warning + index")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req6 regression: non-pandas (default array output) path unchanged.
Array input -> ndarray output with selected columns matching support mask;
sparse input -> sparse output; empty selection -> ndarray (n,0) + warning.
Exit 0 iff all hold."""
import warnings
import numpy as np
from scipy import sparse
from sklearn.feature_selection import SelectKBest, SelectPercentile, f_classif

rng = np.random.RandomState(4)
n = 40
y = rng.randint(0, 2, n)
X = np.column_stack([
    rng.rand(n),
    y + 0.1 * rng.rand(n),
    rng.rand(n),
    y + 0.1 * rng.rand(n),
    rng.rand(n),
]).astype(np.float64)

sel = SelectKBest(f_classif, k=2)
sel.fit(X, y)  # default output = array
out = sel.transform(X)
support = sel.get_support()
print("array out type:", type(out).__name__, "shape:", out.shape)
ok = isinstance(out, np.ndarray)
ok &= out.shape == (n, int(support.sum()))
# columns equal source columns for the selected indices
sel_idx = np.where(support)[0]
ok &= np.allclose(out, X[:, sel_idx])

# sparse
Xs = sparse.csr_matrix(X)
sel2 = SelectKBest(f_classif, k=2)
sel2.fit(Xs, y)
outs = sel2.transform(Xs)
print("sparse out type:", type(outs).__name__)
ok &= sparse.issparse(outs)
ok &= outs.shape == (n, 2)

# empty selection array path -> ndarray (n,0) + warning
sel3 = SelectPercentile(f_classif, percentile=0)
sel3.fit(X, y)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    oute = sel3.transform(X)
print("empty array out:", type(oute).__name__, oute.shape)
ok &= isinstance(oute, np.ndarray) and oute.shape == (n, 0)
ok &= any("no feature" in str(x.message).lower() for x in w)

if not ok:
    raise SystemExit(1)
print("PASS: array/sparse regression behavior intact")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req6.4: inverse_transform unchanged - retained cols from input, dropped
filled with zeros, dense and sparse. Exit 0 iff both reconstruct correctly."""
import numpy as np
from scipy import sparse
from sklearn.feature_selection import SelectKBest, f_classif

rng = np.random.RandomState(5)
n = 30
y = rng.randint(0, 2, n)
X = np.column_stack([
    rng.rand(n),
    y + 0.1 * rng.rand(n),
    rng.rand(n),
    y + 0.1 * rng.rand(n),
]).astype(np.float64)

sel = SelectKBest(f_classif, k=2)
sel.fit(X, y)
support = sel.get_support()
sel_idx = np.where(support)[0]

Xt = sel.transform(X)
Xinv = sel.inverse_transform(Xt)
print("dense inv shape:", Xinv.shape)
ok = Xinv.shape == X.shape
# retained columns match, dropped are zero
for j in range(X.shape[1]):
    if j in sel_idx:
        ok &= np.allclose(Xinv[:, j], X[:, j])
    else:
        ok &= np.allclose(Xinv[:, j], 0.0)

# sparse
Xs = sparse.csr_matrix(X)
sel2 = SelectKBest(f_classif, k=2)
sel2.fit(Xs, y)
Xts = sel2.transform(Xs)
Xinvs = sel2.inverse_transform(Xts)
print("sparse inv sparse?", sparse.issparse(Xinvs), "shape:", Xinvs.shape)
ok &= sparse.issparse(Xinvs) and Xinvs.shape == X.shape

if not ok:
    raise SystemExit(1)
print("PASS: inverse_transform intact (dense+sparse)")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req5: _validate_data(cast_to_ndarray=False) leaves X unchanged (no array
coercion, dtypes intact) yet still records n_features_in_. Exit 0 iff the
returned object is the same DataFrame with same dtypes and n_features_in_ set,
AND default mode (cast_to_ndarray=True) still casts to ndarray."""
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif

rng = np.random.RandomState(6)
n = 20
y = rng.randint(0, 2, n)
X = pd.DataFrame({
    "a": rng.rand(n).astype(np.float32),
    "b": rng.rand(n).astype(np.float64),
    "c": rng.rand(n).astype(np.float32),
})

est = SelectKBest(f_classif, k=2)
est.fit(X, y)

# non-casting mode
out = est._validate_data(X, dtype=None, accept_sparse="csr",
                         cast_to_ndarray=False, reset=False)
print("non-cast out type:", type(out).__name__)
print("dtypes:\n", getattr(out, "dtypes", None))
ok = isinstance(out, pd.DataFrame)
ok &= list(out.dtypes.astype(str)) == list(X.dtypes.astype(str))
ok &= est.n_features_in_ == 3

# default casting mode still yields ndarray
out2 = est._validate_data(X, dtype=None, accept_sparse="csr", reset=False)
print("default out type:", type(out2).__name__)
ok &= isinstance(out2, np.ndarray)

if not ok:
    raise SystemExit(1)
print("PASS: non-casting mode preserves X + sets n_features_in_; default casts")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1 - per-column dtypes preserved in pandas output.
Mixed float32/float64/category columns keep their dtype after transform.
The category column is made predictive so it is retained.
Exit 0 iff every retained column keeps its original dtype AND a category
column is among the retained set."""
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif

rng = np.random.RandomState(0)
n = 60
y = rng.randint(0, 2, n)
X = pd.DataFrame({
    "a": rng.rand(n).astype(np.float32),
    "b": (y + 0.01 * rng.rand(n)).astype(np.float64),   # predictive float64
    "c": pd.Categorical(y),                              # predictive category
    "d": rng.rand(n).astype(np.float32),
    "e": rng.rand(n).astype(np.float64),
})

sel = SelectKBest(f_classif, k=3)
Xfit = X.copy()
Xfit["c"] = X["c"].cat.codes.astype(np.float64)
sel.fit(Xfit, y)
sel.set_output(transform="pandas")

out = sel.transform(X)
print("input dtypes:\n", X.dtypes)
print("output columns:", list(out.columns))
print("output dtypes:\n", out.dtypes)

ok = True
for col in out.columns:
    if str(out[col].dtype) != str(X[col].dtype):
        print(f"MISMATCH {col}: {out[col].dtype} != {X[col].dtype}")
        ok = False
has_cat = any(str(out[c].dtype) == "category" for c in out.columns)
print("category retained:", has_cat)
if not ok or not has_cat:
    raise SystemExit(1)
print("PASS: all retained columns preserved dtype incl. category")
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree; each maps to a requirement:
- probe_1 (Req1/positive control): mixed float32/float64/category DataFrame -> every retained column keeps its dtype and category is retained. HOLDS patched, FAILS at base (base collapses all to float64: 'MISMATCH c: float64!=category, d: float64!=float32'). Discriminates.
- probe_2 (Req2): pandas output columns == get_support() labels in input order.
- probe_3 (Req3): row count + non-default row index preserved.
- probe_4 (Req4): empty selection -> DataFrame (n,0), same index, UserWarning 'No features were selected'.
- probe_5 (Req6.1/6.2): array output path -> ndarray matching support cols; sparse -> csr; empty array -> (n,0)+warning.
- probe_6 (Req6.4): inverse_transform dense+sparse, dropped cols zero-filled.
- probe_7 (Req5): _validate_data(cast_to_ndarray=False) returns unchanged DataFrame w/ dtypes intact + sets n_features_in_; default mode still casts to ndarray. FAILS at base (kwarg doesn't exist).

### CANDIDATE PATCHES (both REJECTED by suite -> discriminating power confirmed):
- weak_partial: gold _base.py hunks (incl. cast_to_ndarray=... in the transform call) but WITHOUT the base.py cast_to_ndarray plumbing. Rejected by ALL probes: TypeError check_array() got unexpected kwarg 'cast_to_ndarray'. Models the forget-base.py partial fix.
- weak_no_empty: full gold EXCEPT the pandas empty-selection branch (X.iloc[:, :0]) omitted. probe_1/probe_7 pass but probe_4 REJECTS it: AttributeError 'DataFrame' has no attribute 'dtype' in the old ndarray empty path. Models the lazy fix that ignores Req4.

No requirements-conforming alternative found that fails the hidden tests: the requirements' criteria (dtype-per-column, empty-frame handling, non-casting validate mode) tightly pin the gold behavior. Suite has >=5 distinct probes, all hold patched, positive control discriminates.

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
"""Positive control: Req1 - per-column dtypes preserved in pandas output.
Mixed float32/float64/category columns keep their dtype after transform.
The category column is made predictive so it is retained.
Exit 0 iff every retained column keeps its original dtype AND a category
column is among the retained set."""
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif

rng = np.random.RandomState(0)
n = 60
y = rng.randint(0, 2, n)
X = pd.DataFrame({
    "a": rng.rand(n).astype(np.float32),
    "b": (y + 0.01 * rng.rand(n)).astype(np.float64),   # predictive float64
    "c": pd.Categorical(y),                              # predictive category
    "d": rng.rand(n).astype(np.float32),
    "e": rng.rand(n).astype(np.float64),
})

sel = SelectKBest(f_classif, k=3)
Xfit = X.copy()
Xfit["c"] = X["c"].cat.codes.astype(np.float64)
sel.fit(Xfit, y)
sel.set_output(transform="pandas")

out = sel.transform(X)
print("input dtypes:\n", X.dtypes)
print("output columns:", list(out.columns))
print("output dtypes:\n", out.dtypes)

ok = True
for col in out.columns:
    if str(out[col].dtype) != str(X[col].dtype):
        print(f"MISMATCH {col}: {out[col].dtype} != {X[col].dtype}")
        ok = False
has_cat = any(str(out[c].dtype) == "category" for c in out.columns)
print("category retained:", has_cat)
if not ok or not has_cat:
    raise SystemExit(1)
print("PASS: all retained columns preserved dtype incl. category")
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree; each maps to a requirement:
- probe_1 (Req1/positive control): mixed float32/float64/category DataFrame -> every retained column keeps its dtype and category is retained. HOLDS patched, FAILS at base (base collapses all to float64: 'MISMATCH c: float64!=category, d: float64!=float32'). Discriminates.
- probe_2 (Req2): pandas output columns == get_support() labels in input order.
- probe_3 (Req3): row count + non-default row index preserved.
- probe_4 (Req4): empty selection -> DataFrame (n,0), same index, UserWarning 'No features were selected'.
- probe_5 (Req6.1/6.2): array output path -> ndarray matching support cols; sparse -> csr; empty array -> (n,0)+warning.
- probe_6 (Req6.4): inverse_transform dense+sparse, dropped cols zero-filled.
- probe_7 (Req5): _validate_data(cast_to_ndarray=False) returns unchanged DataFrame w/ dtypes intact + sets n_features_in_; default mode still casts to ndarray. FAILS at base (kwarg doesn't exist).

### CANDIDATE PATCHES (both REJECTED by suite -> discriminating power confirmed):
- weak_partial: gold _base.py hunks (incl. cast_to_ndarray=... in the transform call) but WITHOUT the base.py cast_to_ndarray plumbing. Rejected by ALL probes: TypeError check_array() got unexpected kwarg 'cast_to_ndarray'. Models the forget-base.py partial fix.
- weak_no_empty: full gold EXCEPT the pandas empty-selection branch (X.iloc[:, :0]) omitted. probe_1/probe_7 pass but probe_4 REJECTS it: AttributeError 'DataFrame' has no attribute 'dtype' in the old ndarray empty path. Models the lazy fix that ignores Req4.

No requirements-conforming alternative found that fails the hidden tests: the requirements' criteria (dtype-per-column, empty-frame handling, non-casting validate mode) tightly pin the gold behavior. Suite has >=5 distinct probes, all hold patched, positive control discriminates.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds cast_to_ndarray flag to base._validate_data and, in SelectorMixin.transform, sets preserve_X = hasattr(X,'iloc') and output_config_dense=='pandas', passing cast_to_ndarray=not preserve_X; _transform now uses _safe_indexing(X, mask, axis=1) and returns X.iloc[:,:0] for empty DataFrame selection. Requirements pin exactly this changed observable behavior at the correct boundary (dtype-preserving pandas path vs unchanged array/sparse path), not a narrow helper slice. Probes run via nl_attack on gold-patched /testbed; the 'Input contains NaN' text seen in some runs was leaked stderr from probes that used category columns through the casting validation path, not a failure of the tested requirement — clean per-requirement probes all returned HOLDS (exit 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md translates the public feature request (problem_statement: preserve per-column dtypes for pandas feature-selection output; SelectKBest; set_output(transform="pandas"); load_iris; category + reduced-precision float columns coerced to float64) into behavioral EARS requirements. Module/method localization (SelectorMixin.transform/_transform in feature_selection/_base.py, _validate_data in base.py) is legitimate spec localization and notably diverges from the problem_statement's own proposed solution (which pointed at _SetOutputMixin/_wrap_in_pandas_container), so it is behavioral re-derivation, not a transcription of the gold edit. No hidden-test content is transmitted: no test file paths, no test/class names (test_output_dataframe, test_dataframe_output_dtypes, StepSelector), no gh-24860 reference, no parametrization ids (step=2/3, the iris ranking dict). No fix-invented identifiers surface: the gold's cast_to_ndarray parameter, _safe_indexing helper, and X.iloc[:, :0] empty-return idiom are described purely behaviorally ("non-casting mode", "take retained columns from original container", "zero-column DataFrame with same rows/index") rather than named. dtype examples (float32/float64/category) are generic or already public. Requirement 4's empty-selection UserWarning is a pre-existing codebase behavior. Requirements 5-6 (validation records n_features_in_ without casting; array/sparse regression protection) describe general behavioral contracts, not the specific test cases. No case enumeration mirrors the test parametrization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
