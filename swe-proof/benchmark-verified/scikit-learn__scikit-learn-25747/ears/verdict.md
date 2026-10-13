# P2 adversarial audit — scikit-learn__scikit-learn-25747

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
# Positive control -- Req 1.1 / 1.2: a DataFrame's own index is kept, supplied index ignored.
import sys
import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

df = pd.DataFrame({"a": [1, 2, 3]}, index=[10, 20, 30])
supplied_index = [0, 1, 2]  # same length, different labels
out = _wrap_in_pandas_container(df, index=supplied_index, columns=None)
got = list(out.index)
print("returned index:", got, "expected:", [10, 20, 30])
if got == [10, 20, 30]:
    print("HOLDS: DataFrame's own index preserved, supplied index ignored")
    sys.exit(0)
print("VIOLATED: index was overwritten")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.3 / 1.5: a returned DataFrame with a DIFFERENT row count than the supplied index
# must be wrapped without raising, and keep its own index + row count.
import sys
import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

# transformer aggregated 6 rows down to 2
df = pd.DataFrame({"g": [100, 200]}, index=["grpA", "grpB"])
supplied_index = list(range(6))  # original input had 6 rows -> mismatch
try:
    out = _wrap_in_pandas_container(df, index=supplied_index, columns=None)
except Exception as e:
    print("VIOLATED: raised", type(e).__name__, e)
    sys.exit(1)
print("rows:", len(out), "index:", list(out.index))
if len(out) == 2 and list(out.index) == ["grpA", "grpB"]:
    print("HOLDS: no raise, own index + row count preserved")
    sys.exit(0)
print("VIOLATED: wrong index/rowcount")
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1 + Req 1: DataFrame columns are still relabeled while its index is untouched.
import sys
import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

df = pd.DataFrame([[1, 2], [3, 4]], index=["r0", "r1"], columns=["old0", "old1"])
out = _wrap_in_pandas_container(df, columns=["new0", "new1"], index=[9, 9])
print("columns:", list(out.columns), "index:", list(out.index))
if list(out.columns) == ["new0", "new1"] and list(out.index) == ["r0", "r1"]:
    print("HOLDS: columns relabeled, index preserved")
    sys.exit(0)
print("VIOLATED")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3: plain numpy array is wrapped into a NEW DataFrame using supplied index+columns.
import sys
import numpy as np
import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

arr = np.array([[1, 2], [3, 4], [5, 6]])
out = _wrap_in_pandas_container(arr, index=["a", "b", "c"], columns=["x", "y"])
print("type:", type(out).__name__, "index:", list(out.index), "columns:", list(out.columns))
ok = (isinstance(out, pd.DataFrame)
      and list(out.index) == ["a", "b", "c"]
      and list(out.columns) == ["x", "y"]
      and out.values.tolist() == [[1, 2], [3, 4], [5, 6]])
if ok:
    print("HOLDS: array wrapped with supplied index/columns")
    sys.exit(0)
print("VIOLATED")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4: scipy sparse input must be rejected with a ValueError mentioning sparse.
import sys
import scipy.sparse as sp
from sklearn.utils._set_output import _wrap_in_pandas_container

m = sp.csr_matrix([[1, 0], [0, 1]])
try:
    _wrap_in_pandas_container(m, index=None, columns=["a", "b"])
except ValueError as e:
    print("raised ValueError:", e)
    if "sparse" in str(e).lower():
        print("HOLDS: sparse rejected")
        sys.exit(0)
    print("VIOLATED: ValueError but not about sparse")
    sys.exit(1)
except Exception as e:
    print("VIOLATED: wrong exception", type(e).__name__)
    sys.exit(1)
print("VIOLATED: no exception")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 5.1 end-to-end: an estimator's transform returning a DataFrame whose row count
# differs from the input, under set_output(transform="pandas"), delivers that DataFrame
# with its own index preserved and does not raise.
import sys
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils._set_output import _SetOutputMixin


class Aggregator(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None):
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        # collapse all rows to two aggregated rows with custom labels
        arr = np.asarray(X)
        agg = np.vstack([arr.sum(axis=0), arr.mean(axis=0)])
        return pd.DataFrame(agg, index=["sum", "mean"], columns=[f"c{i}" for i in range(arr.shape[1])])

    def get_feature_names_out(self, input_features=None):
        return np.array([f"c{i}" for i in range(self.n_features_in_)])


X = pd.DataFrame(np.arange(12).reshape(6, 2), columns=["p", "q"])
est = Aggregator().set_output(transform="pandas")
est.fit(X)
try:
    out = est.transform(X)
except Exception as e:
    print("VIOLATED: raised", type(e).__name__, e)
    sys.exit(1)
print("type:", type(out).__name__, "rows:", len(out), "index:", list(out.index))
if isinstance(out, pd.DataFrame) and len(out) == 2 and list(out.index) == ["sum", "mean"]:
    print("HOLDS: end-to-end pandas output keeps own index, no raise")
    sys.exit(0)
print("VIOLATED")
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control -- Req 1.1 / 1.2: a DataFrame's own index is kept, supplied index ignored.
import sys
import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

df = pd.DataFrame({"a": [1, 2, 3]}, index=[10, 20, 30])
supplied_index = [0, 1, 2]  # same length, different labels
out = _wrap_in_pandas_container(df, index=supplied_index, columns=None)
got = list(out.index)
print("returned index:", got, "expected:", [10, 20, 30])
if got == [10, 20, 30]:
    print("HOLDS: DataFrame's own index preserved, supplied index ignored")
    sys.exit(0)
print("VIOLATED: index was overwritten")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: preserve a transformer's own row index when wrapping pandas output; gold patch removes the `if index is not None: data_to_wrap.index = index` branch in _wrap_in_pandas_container.

6 probes, all HOLD on gold-patched tree:
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): DataFrame's own index preserved, supplied index ignored. PATCHED index=[10,20,30] HOLDS; BASE index overwritten to [0,1,2] FAIL (prepatch reproduced).
- probe_2 (Req 1.3/1.5): aggregating transformer output (2 rows) with mismatched supplied index (6) wrapped without raising, own index+rowcount kept. PATCHED HOLDS; BASE raises ValueError Length mismatch.
- probe_3 (Req 2.1 + index): columns relabeled while index untouched (supplied same-length index [9,9] ignored). PATCHED HOLDS.
- probe_4 (Req 3): numpy array wrapped into new DataFrame with supplied index/columns. HOLDS.
- probe_5 (Req 4): scipy sparse rejected with ValueError mentioning sparse. HOLDS.
- probe_6 (Req 5.1): end-to-end set_output(transform='pandas') with an aggregating estimator returning 2-row DataFrame from 6-row input; delivers DataFrame with own index, no raise. PATCHED HOLDS.

Note: _wrap_in_pandas_container has `columns` as a required keyword-only arg (probes pass columns=None explicitly).

WRONG-FIX CANDIDATE (weak.diff): length-guarded assignment `if index is not None and len(index)==len(data_to_wrap): data_to_wrap.index = index`. This is the lazy fix a weak reading permits — it avoids the crash (Req 1.3) but still overwrites the index when lengths match, violating Req 1.2 ('SHALL ignore the supplied index ... SHALL NOT modify the DataFrame's row index', unconditional). Under weak.diff: probes 2,4,5,6 HOLD but probes 1 and 3 are REJECTED (index overwritten). Suite discriminates this wrong implementation => not a too-weak finding.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, positive control discriminates (holds patched / fails base), and the plausible wrong-fix is rejected by the suite.

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
# Positive control -- Req 1.1 / 1.2: a DataFrame's own index is kept, supplied index ignored.
import sys
import pandas as pd
from sklearn.utils._set_output import _wrap_in_pandas_container

df = pd.DataFrame({"a": [1, 2, 3]}, index=[10, 20, 30])
supplied_index = [0, 1, 2]  # same length, different labels
out = _wrap_in_pandas_container(df, index=supplied_index, columns=None)
got = list(out.index)
print("returned index:", got, "expected:", [10, 20, 30])
if got == [10, 20, 30]:
    print("HOLDS: DataFrame's own index preserved, supplied index ignored")
    sys.exit(0)
print("VIOLATED: index was overwritten")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: preserve a transformer's own row index when wrapping pandas output; gold patch removes the `if index is not None: data_to_wrap.index = index` branch in _wrap_in_pandas_container.

6 probes, all HOLD on gold-patched tree:
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): DataFrame's own index preserved, supplied index ignored. PATCHED index=[10,20,30] HOLDS; BASE index overwritten to [0,1,2] FAIL (prepatch reproduced).
- probe_2 (Req 1.3/1.5): aggregating transformer output (2 rows) with mismatched supplied index (6) wrapped without raising, own index+rowcount kept. PATCHED HOLDS; BASE raises ValueError Length mismatch.
- probe_3 (Req 2.1 + index): columns relabeled while index untouched (supplied same-length index [9,9] ignored). PATCHED HOLDS.
- probe_4 (Req 3): numpy array wrapped into new DataFrame with supplied index/columns. HOLDS.
- probe_5 (Req 4): scipy sparse rejected with ValueError mentioning sparse. HOLDS.
- probe_6 (Req 5.1): end-to-end set_output(transform='pandas') with an aggregating estimator returning 2-row DataFrame from 6-row input; delivers DataFrame with own index, no raise. PATCHED HOLDS.

Note: _wrap_in_pandas_container has `columns` as a required keyword-only arg (probes pass columns=None explicitly).

WRONG-FIX CANDIDATE (weak.diff): length-guarded assignment `if index is not None and len(index)==len(data_to_wrap): data_to_wrap.index = index`. This is the lazy fix a weak reading permits — it avoids the crash (Req 1.3) but still overwrites the index when lengths match, violating Req 1.2 ('SHALL ignore the supplied index ... SHALL NOT modify the DataFrame's row index', unconditional). Under weak.diff: probes 2,4,5,6 HOLD but probes 1 and 3 are REJECTED (index overwritten). Suite discriminates this wrong implementation => not a too-weak finding.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, positive control discriminates (holds patched / fails base), and the plausible wrong-fix is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: requirements pin the changed observable behavior of _wrap_in_pandas_container (DataFrame index preservation) as the biconditional core (R1), while R2/R3/R4/R5 explicitly fence off the unchanged behaviors (column relabel incl. callable resolution, array wrapping, sparse rejection, end-to-end dispatch). No invented behavior, no forbidden behavior, no over-narrow slice. All 15 criteria machine-verified in the instance image.

Counterexample / evidence:

```
n/a — no requirement diverges from patched behavior. Base-vs-patched probe: base forces supplied index onto DataFrame (and raises on row-count mismatch); patched preserves the DataFrame's own index and never raises, exactly as R1 mandates.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All identifiers cited in requirements.md (_wrap_in_pandas_container, _wrap_data_with_container, _SetOutputMixin, module path sklearn/utils/_set_output.py, the index/columns args, ValueError for sparse) appear verbatim in the PUBLIC problem_statement traceback, so naming them is legitimate localization. No hidden-test content is transmitted: the test name (test_set_output_pandas_keep_index), test file path (tests/test_set_output.py), the fix-related test helper class (EstimatorWithSetOutputIndex), and its invented values ('s0'/'s1' index labels, 'X{i}' feature names, the [[1,2,3],[4,5,6]] fixture) are absent. The gold patch is a two-line deletion (drop the `if index is not None: data_to_wrap.index = index`); requirements describe this as behavior (keep the DataFrame's own index, ignore supplied index) rather than quoting patch lines. Acceptance criteria translate observable behavior (index preservation on row-count mismatch, column relabeling incl. callable-raises fallback which is pre-existing code, array wrapping, sparse rejection, set_output precedence) into requirements — the intended purpose, not test reconstruction. Req 1.3's 'differs from number of rows of input' mirrors the public problem_statement's aggregating-FeatureUnion scenario, not a hidden parametrization. No case enumeration mirrors test ids.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
