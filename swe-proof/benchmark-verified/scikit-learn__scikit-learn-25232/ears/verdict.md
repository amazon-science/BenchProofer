# P2 adversarial audit — scikit-learn__scikit-learn-25232

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
# Req 2.3 (positive control): constant strategy + supplied constant -> missing
# entries replaced by that constant, non-missing left unchanged.
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

X = np.array([[1.0, np.nan, 3.0],
              [np.nan, 2.0, np.nan],
              [4.0, 5.0, 6.0]])
FILL = 99.0
imp = IterativeImputer(initial_strategy="constant", fill_value=FILL, max_iter=0,
                       random_state=0)
Xi = imp.fit_transform(X)
print("input:\n", X)
print("output:\n", Xi)
# non-missing unchanged
mask = ~np.isnan(X)
if not np.allclose(Xi[mask], X[mask]):
    print("FAIL: non-missing entries changed")
    raise SystemExit(1)
# missing replaced by FILL
miss = np.isnan(X)
if not np.allclose(Xi[miss], FILL):
    print("FAIL: missing entries not replaced by fill_value; got", Xi[miss])
    raise SystemExit(1)
print("OK: missing seeded with fill_value, non-missing preserved")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.1 & 1.2: fill_value keyword accepted, default None, stored verbatim,
# get_params returns it verbatim.
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

# default None
d = IterativeImputer()
assert d.fill_value is None, ("default not None: %r" % d.fill_value)
assert d.get_params()["fill_value"] is None

# stored verbatim
for v in [7, 3.5, "banana", None]:
    imp = IterativeImputer(fill_value=v)
    assert imp.fill_value == v or (v is None and imp.fill_value is None), \
        ("attr mismatch for %r -> %r" % (v, imp.fill_value))
    assert imp.get_params()["fill_value"] == v or (v is None and imp.get_params()["fill_value"] is None), \
        ("get_params mismatch for %r" % v)
print("OK: fill_value accepted, default None, stored verbatim in get_params")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.2: after fitting with constant + numeric constant, the fitted internal
# initial imputer exposes statistics_ where every feature equals the constant.
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

X = np.array([[1.0, np.nan, 3.0],
              [np.nan, 2.0, np.nan],
              [4.0, 5.0, 6.0]])
FILL = -12.5
imp = IterativeImputer(initial_strategy="constant", fill_value=FILL, max_iter=0,
                       random_state=0)
imp.fit_transform(X)
stats = imp.initial_imputer_.statistics_
print("statistics_:", stats)
if not np.allclose(stats, FILL):
    print("FAIL: not all feature statistics equal the supplied constant")
    raise SystemExit(1)
print("OK: every feature statistic equals supplied constant")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.4 & Req 1.4: constant strategy, no fill_value supplied -> default 0 for
# numeric data (prior behavior preserved).
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

X = np.array([[1.0, np.nan, 3.0],
              [np.nan, 2.0, np.nan],
              [4.0, 5.0, 6.0]])
imp = IterativeImputer(initial_strategy="constant", max_iter=0, random_state=0)
Xi = imp.fit_transform(X)
stats = imp.initial_imputer_.statistics_
print("statistics_ (no fill_value):", stats)
if not np.allclose(stats, 0.0):
    print("FAIL: default numeric constant not 0")
    raise SystemExit(1)
miss = np.isnan(X)
if not np.allclose(Xi[miss], 0.0):
    print("FAIL: missing entries not seeded with default 0")
    raise SystemExit(1)
print("OK: default numeric constant is 0")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 2.5: max_iter=0 -> fit_transform still completes the initial imputation,
# fits the internal initial imputer, and exposes it on the estimator.
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

X = np.array([[1.0, np.nan, 3.0],
              [np.nan, 2.0, np.nan],
              [4.0, 5.0, 6.0]])
imp = IterativeImputer(initial_strategy="constant", fill_value=8.0, max_iter=0,
                       random_state=0)
Xi = imp.fit_transform(X)
assert hasattr(imp, "initial_imputer_") and imp.initial_imputer_ is not None, \
    "initial_imputer_ not available"
assert Xi.shape == X.shape, ("shape changed: %r" % (Xi.shape,))
# with max_iter=0 the output equals the initial imputation
miss = np.isnan(X)
if not np.allclose(Xi[miss], 8.0):
    print("FAIL: max_iter=0 output not the initial constant imputation")
    raise SystemExit(1)
print("OK: max_iter=0 completes initial imputation, initial_imputer_ exposed")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.1: with initial_strategy="mean", the fill_value parameter is ignored;
# initial imputation uses column means unaffected by fill_value.
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

X = np.array([[1.0, np.nan, 3.0],
              [np.nan, 2.0, np.nan],
              [4.0, 5.0, 6.0]])
# means: col0 mean of [1,4]=2.5 ; col1 mean of[2,5]=3.5 ; col2 mean of[3,6]=4.5
imp = IterativeImputer(initial_strategy="mean", fill_value=999.0, max_iter=0,
                       random_state=0)
imp.fit_transform(X)
stats = imp.initial_imputer_.statistics_
print("mean statistics_:", stats)
expected = np.array([2.5, 3.5, 4.5])
if not np.allclose(stats, expected):
    print("FAIL: mean stats affected/incorrect; fill_value leaked into mean strategy")
    raise SystemExit(1)
if np.any(np.isclose(stats, 999.0)):
    print("FAIL: fill_value leaked into mean strategy")
    raise SystemExit(1)
print("OK: mean strategy unaffected by fill_value")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 3.2: only mean/median/most_frequent/constant are valid initial_strategy;
# any other value is rejected at fit time.
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

X = np.array([[1.0, np.nan, 3.0],
              [np.nan, 2.0, np.nan],
              [4.0, 5.0, 6.0]])
imp = IterativeImputer(initial_strategy="bogus", max_iter=0, random_state=0)
try:
    imp.fit_transform(X)
except (ValueError, Exception) as e:
    print("OK: invalid initial_strategy rejected:", type(e).__name__)
    # ensure it's actually rejecting (ValueError from param validation)
    raise SystemExit(0)
print("FAIL: invalid initial_strategy accepted")
raise SystemExit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 2.3 (positive control): constant strategy + supplied constant -> missing
# entries replaced by that constant, non-missing left unchanged.
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

X = np.array([[1.0, np.nan, 3.0],
              [np.nan, 2.0, np.nan],
              [4.0, 5.0, 6.0]])
FILL = 99.0
imp = IterativeImputer(initial_strategy="constant", fill_value=FILL, max_iter=0,
                       random_state=0)
Xi = imp.fit_transform(X)
print("input:\n", X)
print("output:\n", Xi)
# non-missing unchanged
mask = ~np.isnan(X)
if not np.allclose(Xi[mask], X[mask]):
    print("FAIL: non-missing entries changed")
    raise SystemExit(1)
# missing replaced by FILL
miss = np.isnan(X)
if not np.allclose(Xi[miss], FILL):
    print("FAIL: missing entries not replaced by fill_value; got", Xi[miss])
    raise SystemExit(1)
print("OK: missing seeded with fill_value, non-missing preserved")
```

Prepatch bug re-encoded as an attack: `True`.

IterativeImputer requires `from sklearn.experimental import enable_iterative_imputer` before import; all probes include it.

Probe coverage (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 2.3): constant strategy + fill_value=99 -> missing entries seeded with 99, non-missing unchanged. HOLDS patched; FAILS at base (TypeError: unexpected keyword argument 'fill_value') => discriminates.
- probe_2 (Req 1.1/1.2): fill_value keyword accepted, default None, stored verbatim, get_params round-trips (int/float/str/None). HOLDS patched; FAILS at base (AttributeError, no fill_value attr).
- probe_3 (Req 2.2): after fit with fill_value=-12.5, initial_imputer_.statistics_ == constant for every feature. HOLDS patched; FAILS at base (TypeError).
- probe_4 (Req 1.4/2.4): constant strategy, no fill_value -> default numeric constant 0 (prior behavior). HOLDS patched.
- probe_5 (Req 2.5): max_iter=0 -> fit_transform completes initial imputation, initial_imputer_ exposed, output == initial constant imputation. HOLDS patched.
- probe_6 (Req 3.1): initial_strategy='mean' with fill_value=999 -> statistics_ are column means (2.5,3.5,4.5), fill_value ignored/does not leak. HOLDS patched.
- probe_7 (Req 3.2): initial_strategy='bogus' rejected (InvalidParameterError). HOLDS patched.

WEAK CANDIDATE (weak.diff): adds fill_value param + _parameter_constraints + stores self.fill_value, but does NOT forward it to the internal SimpleImputer in _initial_imputation. This satisfies Req 1 entirely (probe_2 HOLDS, probe_7 HOLDS) but is REJECTED by the propagation criteria: probe_1 FAIL (got [0,0,0] instead of 99), probe_3 FAIL (stats not equal to constant), probe_5 VIOLATED (max_iter=0 output not the constant imputation). This demonstrates the suite discriminates the exact lazy partial fix a weak reading of Req 1 permits, and confirms Req 2's forwarding requirement is load-bearing.

Conclusion: >=5 distinct probes all hold on patched; positive control discriminates patched-vs-base (prepatch reproduced); a plausibly-wrong requirements-partial patch is rejected by the suite. No violation and no too-weak alternative found.

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
# Req 2.3 (positive control): constant strategy + supplied constant -> missing
# entries replaced by that constant, non-missing left unchanged.
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

X = np.array([[1.0, np.nan, 3.0],
              [np.nan, 2.0, np.nan],
              [4.0, 5.0, 6.0]])
FILL = 99.0
imp = IterativeImputer(initial_strategy="constant", fill_value=FILL, max_iter=0,
                       random_state=0)
Xi = imp.fit_transform(X)
print("input:\n", X)
print("output:\n", Xi)
# non-missing unchanged
mask = ~np.isnan(X)
if not np.allclose(Xi[mask], X[mask]):
    print("FAIL: non-missing entries changed")
    raise SystemExit(1)
# missing replaced by FILL
miss = np.isnan(X)
if not np.allclose(Xi[miss], FILL):
    print("FAIL: missing entries not replaced by fill_value; got", Xi[miss])
    raise SystemExit(1)
print("OK: missing seeded with fill_value, non-missing preserved")
```

Prepatch bug re-encoded as an attack: `True`.

IterativeImputer requires `from sklearn.experimental import enable_iterative_imputer` before import; all probes include it.

Probe coverage (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 2.3): constant strategy + fill_value=99 -> missing entries seeded with 99, non-missing unchanged. HOLDS patched; FAILS at base (TypeError: unexpected keyword argument 'fill_value') => discriminates.
- probe_2 (Req 1.1/1.2): fill_value keyword accepted, default None, stored verbatim, get_params round-trips (int/float/str/None). HOLDS patched; FAILS at base (AttributeError, no fill_value attr).
- probe_3 (Req 2.2): after fit with fill_value=-12.5, initial_imputer_.statistics_ == constant for every feature. HOLDS patched; FAILS at base (TypeError).
- probe_4 (Req 1.4/2.4): constant strategy, no fill_value -> default numeric constant 0 (prior behavior). HOLDS patched.
- probe_5 (Req 2.5): max_iter=0 -> fit_transform completes initial imputation, initial_imputer_ exposed, output == initial constant imputation. HOLDS patched.
- probe_6 (Req 3.1): initial_strategy='mean' with fill_value=999 -> statistics_ are column means (2.5,3.5,4.5), fill_value ignored/does not leak. HOLDS patched.
- probe_7 (Req 3.2): initial_strategy='bogus' rejected (InvalidParameterError). HOLDS patched.

WEAK CANDIDATE (weak.diff): adds fill_value param + _parameter_constraints + stores self.fill_value, but does NOT forward it to the internal SimpleImputer in _initial_imputation. This satisfies Req 1 entirely (probe_2 HOLDS, probe_7 HOLDS) but is REJECTED by the propagation criteria: probe_1 FAIL (got [0,0,0] instead of 99), probe_3 FAIL (stats not equal to constant), probe_5 VIOLATED (max_iter=0 output not the constant imputation). This demonstrates the suite discriminates the exact lazy partial fix a weak reading of Req 1 permits, and confirms Req 2's forwarding requirement is load-bearing.

Conclusion: >=5 distinct probes all hold on patched; positive control discriminates patched-vs-base (prepatch reproduced); a plausibly-wrong requirements-partial patch is rejected by the suite. No violation and no too-weak alternative found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds fill_value=None to __init__, self.fill_value assignment, 'fill_value':'no_validation' in _parameter_constraints, and fill_value=self.fill_value forwarded to SimpleImputer in _initial_imputation. Modeling boundary is correct (changed behavior, not a narrow branch/helper). Probes run via nl_attack on gold-patched tree (exit 0, ALL OK) and --base confirms the discriminator.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes only behavior derivable from the PUBLIC problem_statement plus legitimate localization. The public problem_statement already names IterativeImputer, the missing `fill_value` parameter, initial_strategy="constant", the SimpleImputer analogy, and the default constants (0 numeric / "missing_value" string). The doc's identifiers (fill_value, initial_strategy, SimpleImputer, min_value/max_value, keep_empty_features) are all pre-existing public API — none are fix-invented (the gold patch invents nothing; it forwards the public `fill_value`). Naming `_iterative.py` / `_initial_imputation` is legitimate change-localization. The nearest-to-test acceptance criteria — Req 2.2 (fitted internal imputer's per-feature statistics equal the supplied constant) and Req 2.5 (with zero refinement rounds, fit_transform still fits and exposes the internal initial imputer) — are the *behavioral* translation of the hidden assertion, not the test itself: no test name (test_iterative_imputer_constant_fill_value), path, quoted code, concrete fixture (X array, missing_values=-1, fill_value=100, max_iter=0), or parametrization ids appear. The hidden test is a single non-parametrized function, so there is no case enumeration to mirror; Req-3's enumeration of {mean,median,most_frequent,constant} strategies comes straight from the public docstring/StrOptions and problem_statement. Translating what the test checks into a behavioral requirement is the intended purpose. No reconstruction of hidden tests beyond the public spec.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
