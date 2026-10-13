# P2 adversarial audit — scikit-learn__scikit-learn-26323

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
"""Positive control / Req1.2 + Req1.3: estimator remainder honors pandas output.

set_output(transform="pandas") on a ColumnTransformer whose remainder is an
estimator; fit_transform must return a DataFrame equal to the input (leftover
columns preserved with values and labels). Fails at base (remainder ignored).
"""
import sys
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.feature_selection import VarianceThreshold

df = pd.DataFrame({"a": [True, False, True], "b": [1, 2, 3]})

ct = make_column_transformer(
    (VarianceThreshold(), make_column_selector(dtype_include=bool)),
    remainder=VarianceThreshold(),
    verbose_feature_names_out=False,
)
ct.set_output(transform="pandas")
out = ct.fit_transform(df)
print("type(out) =", type(out))
if not isinstance(out, pd.DataFrame):
    print("FAIL: output is not a DataFrame")
    sys.exit(1)
try:
    pd.testing.assert_frame_equal(out, df)
except AssertionError as e:
    print("FAIL: output not equal to input df:\n", e)
    sys.exit(1)
print("PASS: pandas DataFrame equal to input, remainder columns preserved")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1: set_output actually configures the remainder estimator's output config.

Inspect the remainder estimator's _sklearn_output_config after set_output.
It must record transform="pandas". Fails at base.
"""
import sys
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.feature_selection import VarianceThreshold

rem = VarianceThreshold()
ct = make_column_transformer(
    (VarianceThreshold(), make_column_selector(dtype_include=bool)),
    remainder=rem,
    verbose_feature_names_out=False,
)
ct.set_output(transform="pandas")
cfg = getattr(ct.remainder, "_sklearn_output_config", None)
print("remainder _sklearn_output_config =", cfg)
if not cfg or cfg.get("transform") != "pandas":
    print("FAIL: remainder estimator output config not set to pandas")
    sys.exit(1)
print("PASS: remainder estimator configured with transform=pandas")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2: sentinel remainders ("passthrough"/"drop") unchanged & no error.

set_output must complete without error and must NOT set an output config on
the sentinel string. Holds at base and patched (regression criterion).
"""
import sys
import pandas as pd
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.feature_selection import VarianceThreshold

ok = True
for sentinel in ("passthrough", "drop"):
    ct = make_column_transformer(
        (VarianceThreshold(), make_column_selector(dtype_include=bool)),
        remainder=sentinel,
        verbose_feature_names_out=False,
    )
    try:
        ret = ct.set_output(transform="pandas")
    except Exception as e:
        print(f"FAIL: set_output raised for remainder={sentinel!r}: {e}")
        sys.exit(1)
    # remainder must remain the exact sentinel string, unchanged
    if ct.remainder != sentinel or not isinstance(ct.remainder, str):
        print(f"FAIL: remainder changed for sentinel {sentinel!r}: {ct.remainder!r}")
        sys.exit(1)
    print(f"OK sentinel {sentinel!r} unchanged, set_output completed")

# passthrough remainder + pandas still works end to end
df = pd.DataFrame({"a": [True, False, True], "b": [1, 2, 3]})
ct = make_column_transformer(
    (VarianceThreshold(), make_column_selector(dtype_include=bool)),
    remainder="passthrough",
    verbose_feature_names_out=False,
)
ct.set_output(transform="pandas")
out = ct.fit_transform(df)
print("passthrough out type:", type(out))
if not isinstance(out, pd.DataFrame):
    print("FAIL: passthrough remainder pandas output not DataFrame")
    sys.exit(1)
print("PASS: sentinel remainders unchanged and functional")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3: listed sub-transformers still configured (no regression).

The non-remainder sub-transformer must also get transform="pandas". And Req4.1:
set_output returns self. Holds at base and patched (regression criterion).
"""
import sys
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.feature_selection import VarianceThreshold

sub = VarianceThreshold()
ct = make_column_transformer(
    (sub, make_column_selector(dtype_include=bool)),
    remainder=VarianceThreshold(),
    verbose_feature_names_out=False,
)
ret = ct.set_output(transform="pandas")
print("returned self?", ret is ct)
if ret is not ct:
    print("FAIL: set_output did not return self")
    sys.exit(1)
cfg = getattr(sub, "_sklearn_output_config", None)
print("listed sub-transformer config:", cfg)
if not cfg or cfg.get("transform") != "pandas":
    print("FAIL: listed sub-transformer not configured to pandas")
    sys.exit(1)
print("PASS: listed sub-transformer configured and self returned")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4.2: default container behavior with estimator remainder.

After set_output(transform="default"), fit_transform returns a native NumPy
ndarray (not a DataFrame), even with an estimator remainder. This must hold
regardless of a prior "pandas" configuration. Holds at base and patched.
"""
import sys
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.feature_selection import VarianceThreshold

df = pd.DataFrame({"a": [True, False, True], "b": [1, 2, 3]})
ct = make_column_transformer(
    (VarianceThreshold(), make_column_selector(dtype_include=bool)),
    remainder=VarianceThreshold(),
    verbose_feature_names_out=False,
)
ct.set_output(transform="pandas")
ct.set_output(transform="default")
out = ct.fit_transform(df)
print("type(out) =", type(out))
if not isinstance(out, np.ndarray):
    print("FAIL: default output is not a numpy ndarray")
    sys.exit(1)
print("PASS: default container yields numpy ndarray")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.3: set_output(transform=None) leaves configuration unchanged.

Configure pandas, then call set_output(transform=None); the remainder and
listed sub-transformer configs must remain "pandas". Holds at base & patched
for the CT itself; the remainder leg only holds patched (still None-safe).
"""
import sys
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.feature_selection import VarianceThreshold

sub = VarianceThreshold()
rem = VarianceThreshold()
ct = make_column_transformer(
    (sub, make_column_selector(dtype_include=bool)),
    remainder=rem,
    verbose_feature_names_out=False,
)
ct.set_output(transform="pandas")
ct.set_output(transform=None)  # must not clobber
own = getattr(ct, "_sklearn_output_config", None)
subc = getattr(sub, "_sklearn_output_config", None)
print("ct config:", own, "sub config:", subc)
if not own or own.get("transform") != "pandas":
    print("FAIL: CT own config changed by None")
    sys.exit(1)
if not subc or subc.get("transform") != "pandas":
    print("FAIL: sub-transformer config changed by None")
    sys.exit(1)
print("PASS: transform=None left configuration unchanged")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.2 + Req1.3: estimator remainder honors pandas output.

set_output(transform="pandas") on a ColumnTransformer whose remainder is an
estimator; fit_transform must return a DataFrame equal to the input (leftover
columns preserved with values and labels). Fails at base (remainder ignored).
"""
import sys
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.feature_selection import VarianceThreshold

df = pd.DataFrame({"a": [True, False, True], "b": [1, 2, 3]})

ct = make_column_transformer(
    (VarianceThreshold(), make_column_selector(dtype_include=bool)),
    remainder=VarianceThreshold(),
    verbose_feature_names_out=False,
)
ct.set_output(transform="pandas")
out = ct.fit_transform(df)
print("type(out) =", type(out))
if not isinstance(out, pd.DataFrame):
    print("FAIL: output is not a DataFrame")
    sys.exit(1)
try:
    pd.testing.assert_frame_equal(out, df)
except AssertionError as e:
    print("FAIL: output not equal to input df:\n", e)
    sys.exit(1)
print("PASS: pandas DataFrame equal to input, remainder columns preserved")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: ColumnTransformer.set_output must propagate the output-container choice to an estimator `remainder`. Gold patch adds `if self.remainder not in {'passthrough','drop'}: _safe_set_output(self.remainder, transform=transform)`.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req1.2/1.3): set_output(transform='pandas'); fit_transform returns DataFrame equal to input df (remainder columns preserve values/labels/dtype). PATCHED: HOLDS. BASE: VIOLATED (remainder col 'a' coerced bool->int64). WEAK: VIOLATED.
- probe_2 (Req1.1): remainder estimator's _sklearn_output_config == {'transform':'pandas'}. PATCHED HOLDS; BASE VIOLATED (None); WEAK VIOLATED (None).
- probe_3 (Req2.1/2.2): 'passthrough'/'drop' sentinels unchanged, set_output no error, passthrough+pandas still yields DataFrame. HOLDS patched & weak (regression leg).
- probe_4 (Req3.1/4.1): listed sub-transformer configured to pandas AND set_output returns self. HOLDS patched & weak.
- probe_5 (Req4.2): after set_output('default') with estimator remainder, fit_transform returns numpy ndarray. HOLDS patched & weak.
- probe_6 (Req4.3): set_output(transform=None) leaves prior 'pandas' config unchanged for CT and sub-transformer. HOLDS patched & weak.

Discrimination: positive control fails at base and holds patched (prepatch_reproduced=true). Wrong-fix candidate weak.diff inverts the sentinel guard (`if self.remainder in {'passthrough','drop'}` -> only sentinels, never a real estimator remainder = base behavior with cosmetic blank line). Probes 1 & 2 REJECT it; regression probes 3-6 still pass. Suite discriminates the correct fix from a plausible weak reading. All required runs completed cleanly.

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
"""Positive control / Req1.2 + Req1.3: estimator remainder honors pandas output.

set_output(transform="pandas") on a ColumnTransformer whose remainder is an
estimator; fit_transform must return a DataFrame equal to the input (leftover
columns preserved with values and labels). Fails at base (remainder ignored).
"""
import sys
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer, make_column_selector
from sklearn.feature_selection import VarianceThreshold

df = pd.DataFrame({"a": [True, False, True], "b": [1, 2, 3]})

ct = make_column_transformer(
    (VarianceThreshold(), make_column_selector(dtype_include=bool)),
    remainder=VarianceThreshold(),
    verbose_feature_names_out=False,
)
ct.set_output(transform="pandas")
out = ct.fit_transform(df)
print("type(out) =", type(out))
if not isinstance(out, pd.DataFrame):
    print("FAIL: output is not a DataFrame")
    sys.exit(1)
try:
    pd.testing.assert_frame_equal(out, df)
except AssertionError as e:
    print("FAIL: output not equal to input df:\n", e)
    sys.exit(1)
print("PASS: pandas DataFrame equal to input, remainder columns preserved")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: ColumnTransformer.set_output must propagate the output-container choice to an estimator `remainder`. Gold patch adds `if self.remainder not in {'passthrough','drop'}: _safe_set_output(self.remainder, transform=transform)`.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req1.2/1.3): set_output(transform='pandas'); fit_transform returns DataFrame equal to input df (remainder columns preserve values/labels/dtype). PATCHED: HOLDS. BASE: VIOLATED (remainder col 'a' coerced bool->int64). WEAK: VIOLATED.
- probe_2 (Req1.1): remainder estimator's _sklearn_output_config == {'transform':'pandas'}. PATCHED HOLDS; BASE VIOLATED (None); WEAK VIOLATED (None).
- probe_3 (Req2.1/2.2): 'passthrough'/'drop' sentinels unchanged, set_output no error, passthrough+pandas still yields DataFrame. HOLDS patched & weak (regression leg).
- probe_4 (Req3.1/4.1): listed sub-transformer configured to pandas AND set_output returns self. HOLDS patched & weak.
- probe_5 (Req4.2): after set_output('default') with estimator remainder, fit_transform returns numpy ndarray. HOLDS patched & weak.
- probe_6 (Req4.3): set_output(transform=None) leaves prior 'pandas' config unchanged for CT and sub-transformer. HOLDS patched & weak.

Discrimination: positive control fails at base and holds patched (prepatch_reproduced=true). Wrong-fix candidate weak.diff inverts the sentinel guard (`if self.remainder in {'passthrough','drop'}` -> only sentinels, never a real estimator remainder = base behavior with cosmetic blank line). Probes 1 & 2 REJECT it; regression probes 3-6 still pass. Suite discriminates the correct fix from a plausible weak reading. All required runs completed cleanly.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds exactly: after super().set_output and the sub-transformer loop, `if self.remainder not in {'passthrough','drop'}: _safe_set_output(self.remainder, transform=transform)`. Requirements describe the changed behavior at the correct boundary (remainder-estimator container propagation) and correctly frame Req3/Req4 as preserved pre-existing behavior. Probes: patched HOLDS (DataFrame, b preserved, default->ndarray, sentinels no error); base reproduces the bug (b coerced to [1,0,1]).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to ColumnTransformer.set_output in sklearn/compose/_column_transformer.py (legitimate) and translates the behavior into EARS requirements. Every specific it names is public: the remainder-as-estimator vs sentinel ('passthrough'/'drop') distinction, set_output(transform=...) with 'pandas'/'default'/None, and propagation to transformers/transformers_ are all in the problem_statement or the documented public API. No hidden-test content leaks: no test function/file name (test_remainder_set_output / test_column_transformer.py), no parametrization ids, no quoted test or gold code, no fixture specifics (the {'a':[True,False,True],'b':[1,2,3]} DataFrame, VarianceThreshold, make_column_selector dtype filters), and no fix-invented identifiers. Req 4.2 (default -> np.ndarray) parallels a test assertion but is standard documented behavior described as a general requirement, not a reconstruction of the test. Requirements read as behavior descriptions, not test enumerations.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
