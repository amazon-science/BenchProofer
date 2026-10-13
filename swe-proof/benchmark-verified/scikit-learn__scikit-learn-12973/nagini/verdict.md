# P2 adversarial audit — scikit-learn__scikit-learn-12973

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,19 +40,16 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
     def __init__(self, default_copy: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
         self.default_copy = default_copy
 
 
 class InputArray:
     def __init__(self, intact: bool, native_format: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
         Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
         self.intact = intact
@@ -86,14 +83,6 @@
     Requires(Acc(config.default_copy, 1 / 2))
     Requires(Acc(data.intact))
     Requires(Acc(data.native_format, 1 / 2))
-    # Level is parametric because the specification must admit a call site that
-    # invokes fit on a FRESH native-format input (the admissibility probe): a
-    # constant level can never dominate itself, so a self-call cannot be proven
-    # terminating at any single constant n. A non-native input sits at level 3
-    # and may make one nested call on a native-format input at level 2; a
-    # native-format input sits at level 2 and makes none. 3 > 2 > 1 (the
-    # constructors' level), so the descent is well-founded and depth is <= 2.
-    Requires(MustTerminate(2 if data.native_format else 3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(config.default_copy, 1 / 2))
@@ -110,12 +99,7 @@
     Ensures(data.intact == (Result() or not data.native_format))
     # post-conditions-end
     # impl-start
-    if copy_X is None:
-        copy_X = config.default_copy
-    effective = copy_X  # governs both preprocessing and the fitting routine
-    if data.native_format:
-        data.intact = effective
-    else:
-        data.intact = True
-    return effective
+    copy_X = True
+    data.intact = True
+    return True
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,19 +40,16 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
     def __init__(self, default_copy: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
         self.default_copy = default_copy
 
 
 class InputArray:
     def __init__(self, intact: bool, native_format: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
         Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
         self.intact = intact
@@ -86,14 +83,6 @@
     Requires(Acc(config.default_copy, 1 / 2))
     Requires(Acc(data.intact))
     Requires(Acc(data.native_format, 1 / 2))
-    # Level is parametric because the specification must admit a call site that
-    # invokes fit on a FRESH native-format input (the admissibility probe): a
-    # constant level can never dominate itself, so a self-call cannot be proven
-    # terminating at any single constant n. A non-native input sits at level 3
-    # and may make one nested call on a native-format input at level 2; a
-    # native-format input sits at level 2 and makes none. 3 > 2 > 1 (the
-    # constructors' level), so the descent is well-founded and depth is <= 2.
-    Requires(MustTerminate(2 if data.native_format else 3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(config.default_copy, 1 / 2))
@@ -110,12 +99,10 @@
     Ensures(data.intact == (Result() or not data.native_format))
     # post-conditions-end
     # impl-start
-    if copy_X is None:
-        copy_X = config.default_copy
-    effective = copy_X  # governs both preprocessing and the fitting routine
+    copy_X = False
     if data.native_format:
-        data.intact = effective
+        data.intact = False
     else:
         data.intact = True
-    return effective
+    return False
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,19 +40,16 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
     def __init__(self, default_copy: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
         self.default_copy = default_copy
 
 
 class InputArray:
     def __init__(self, intact: bool, native_format: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
         Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
         self.intact = intact
@@ -86,14 +83,6 @@
     Requires(Acc(config.default_copy, 1 / 2))
     Requires(Acc(data.intact))
     Requires(Acc(data.native_format, 1 / 2))
-    # Level is parametric because the specification must admit a call site that
-    # invokes fit on a FRESH native-format input (the admissibility probe): a
-    # constant level can never dominate itself, so a self-call cannot be proven
-    # terminating at any single constant n. A non-native input sits at level 3
-    # and may make one nested call on a native-format input at level 2; a
-    # native-format input sits at level 2 and makes none. 3 > 2 > 1 (the
-    # constructors' level), so the descent is well-founded and depth is <= 2.
-    Requires(MustTerminate(2 if data.native_format else 3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(config.default_copy, 1 / 2))
@@ -110,9 +99,7 @@
     Ensures(data.intact == (Result() or not data.native_format))
     # post-conditions-end
     # impl-start
-    if copy_X is None:
-        copy_X = config.default_copy
-    effective = copy_X  # governs both preprocessing and the fitting routine
+    effective = config.default_copy
     if data.native_format:
         data.intact = effective
     else:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,19 +40,16 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
     def __init__(self, default_copy: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
         self.default_copy = default_copy
 
 
 class InputArray:
     def __init__(self, intact: bool, native_format: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
         Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
         self.intact = intact
@@ -86,14 +83,6 @@
     Requires(Acc(config.default_copy, 1 / 2))
     Requires(Acc(data.intact))
     Requires(Acc(data.native_format, 1 / 2))
-    # Level is parametric because the specification must admit a call site that
-    # invokes fit on a FRESH native-format input (the admissibility probe): a
-    # constant level can never dominate itself, so a self-call cannot be proven
-    # terminating at any single constant n. A non-native input sits at level 3
-    # and may make one nested call on a native-format input at level 2; a
-    # native-format input sits at level 2 and makes none. 3 > 2 > 1 (the
-    # constructors' level), so the descent is well-founded and depth is <= 2.
-    Requires(MustTerminate(2 if data.native_format else 3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(config.default_copy, 1 / 2))
@@ -110,12 +99,10 @@
     Ensures(data.intact == (Result() or not data.native_format))
     # post-conditions-end
     # impl-start
-    if copy_X is None:
-        copy_X = config.default_copy
-    effective = copy_X  # governs both preprocessing and the fitting routine
+    copy_X = config.default_copy
     if data.native_format:
-        data.intact = effective
+        data.intact = copy_X
     else:
         data.intact = True
-    return effective
+    return copy_X
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,19 +40,16 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
     def __init__(self, default_copy: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
         self.default_copy = default_copy
 
 
 class InputArray:
     def __init__(self, intact: bool, native_format: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
         Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
         self.intact = intact
@@ -86,14 +83,6 @@
     Requires(Acc(config.default_copy, 1 / 2))
     Requires(Acc(data.intact))
     Requires(Acc(data.native_format, 1 / 2))
-    # Level is parametric because the specification must admit a call site that
-    # invokes fit on a FRESH native-format input (the admissibility probe): a
-    # constant level can never dominate itself, so a self-call cannot be proven
-    # terminating at any single constant n. A non-native input sits at level 3
-    # and may make one nested call on a native-format input at level 2; a
-    # native-format input sits at level 2 and makes none. 3 > 2 > 1 (the
-    # constructors' level), so the descent is well-founded and depth is <= 2.
-    Requires(MustTerminate(2 if data.native_format else 3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(config.default_copy, 1 / 2))
@@ -110,12 +99,10 @@
     Ensures(data.intact == (Result() or not data.native_format))
     # post-conditions-end
     # impl-start
-    if copy_X is None:
-        copy_X = config.default_copy
-    effective = copy_X  # governs both preprocessing and the fitting routine
+    resolved = selected_preference(config.default_copy, copy_X)
     if data.native_format:
-        data.intact = effective
+        data.intact = not resolved
     else:
         data.intact = True
-    return effective
+    return resolved
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,19 +40,16 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
     def __init__(self, default_copy: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
         self.default_copy = default_copy
 
 
 class InputArray:
     def __init__(self, intact: bool, native_format: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
         Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
         self.intact = intact
@@ -86,14 +83,6 @@
     Requires(Acc(config.default_copy, 1 / 2))
     Requires(Acc(data.intact))
     Requires(Acc(data.native_format, 1 / 2))
-    # Level is parametric because the specification must admit a call site that
-    # invokes fit on a FRESH native-format input (the admissibility probe): a
-    # constant level can never dominate itself, so a self-call cannot be proven
-    # terminating at any single constant n. A non-native input sits at level 3
-    # and may make one nested call on a native-format input at level 2; a
-    # native-format input sits at level 2 and makes none. 3 > 2 > 1 (the
-    # constructors' level), so the descent is well-founded and depth is <= 2.
-    Requires(MustTerminate(2 if data.native_format else 3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(config.default_copy, 1 / 2))
@@ -110,12 +99,7 @@
     Ensures(data.intact == (Result() or not data.native_format))
     # post-conditions-end
     # impl-start
-    if copy_X is None:
-        copy_X = config.default_copy
-    effective = copy_X  # governs both preprocessing and the fitting routine
-    if data.native_format:
-        data.intact = effective
-    else:
-        data.intact = True
-    return effective
+    resolved = selected_preference(config.default_copy, copy_X)
+    data.intact = resolved
+    return resolved
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,19 +40,16 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
     def __init__(self, default_copy: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
         self.default_copy = default_copy
 
 
 class InputArray:
     def __init__(self, intact: bool, native_format: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
         Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
         self.intact = intact
@@ -86,14 +83,6 @@
     Requires(Acc(config.default_copy, 1 / 2))
     Requires(Acc(data.intact))
     Requires(Acc(data.native_format, 1 / 2))
-    # Level is parametric because the specification must admit a call site that
-    # invokes fit on a FRESH native-format input (the admissibility probe): a
-    # constant level can never dominate itself, so a self-call cannot be proven
-    # terminating at any single constant n. A non-native input sits at level 3
-    # and may make one nested call on a native-format input at level 2; a
-    # native-format input sits at level 2 and makes none. 3 > 2 > 1 (the
-    # constructors' level), so the descent is well-founded and depth is <= 2.
-    Requires(MustTerminate(2 if data.native_format else 3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(config.default_copy, 1 / 2))
@@ -110,12 +99,8 @@
     Ensures(data.intact == (Result() or not data.native_format))
     # post-conditions-end
     # impl-start
-    if copy_X is None:
-        copy_X = config.default_copy
-    effective = copy_X  # governs both preprocessing and the fitting routine
+    resolved = selected_preference(config.default_copy, copy_X)
     if data.native_format:
-        data.intact = effective
-    else:
-        data.intact = True
-    return effective
+        data.intact = resolved
+    return resolved
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-12973.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An estimator records, at construction time, a default boolean preference for
  whether the training-data array passed to the model-fitting routine is
  preserved (left byte-for-byte intact) or may be overwritten in place during
  preprocessing. The fitting routine ALSO accepts a per-call preference.

  The desired behaviour is that the per-call preference, when the caller
  supplies one, takes precedence over the construction-time default; when the
  caller supplies no per-call preference (the "unset" value), the
  construction-time default is used. Whichever preference is thus selected
  governs preprocessing in full:

    (1) the preference that actually governs preprocessing equals the per-call
        preference if one was supplied, otherwise the construction-time default
        (the per-call choice is never silently discarded); and

    (2) the input array's fate follows that selected preference, subject to
        the routine's numeric working format: the routine computes in a
        designated numeric representation, and when the supplied array is not
        already in that representation, input validation materializes a
        converted working copy up front, so the caller's array is left intact
        regardless of the selected preference. When the array IS already in
        the native working format, it is left intact after fitting if and
        only if the selected preference is "preserve" (True): a "preserve"
        selection copies the array before preprocessing, a "may overwrite"
        selection lets preprocessing mutate it in place.

The per-call preference is modelled as ``Optional[bool]`` (``None`` = "unset").
The estimator's construction-time default and the input array's touched
observables are modelled as minimal objects carrying only the touched fields:
``intact`` (the boolean the fitting routine's caller observes afterwards) and
``native_format`` (whether the array is already in the routine's native
numeric working representation — the property that decides whether validation
must materialize a converted copy).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class Estimator:
    def __init__(self, default_copy: bool) -> None:
        Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
        self.default_copy = default_copy


class InputArray:
    def __init__(self, intact: bool, native_format: bool) -> None:
        Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
        Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
        self.intact = intact
        self.native_format = native_format


# axioms-start
# (no callee is axiomatized: the changed behaviour is a boolean dataflow — the
# selection of the governing preference and its consequence for the input array
# — and is modelled deeply below, not behind a @ContractOnly axiom.)
# axioms-end


# pure-start
@Pure
def selected_preference(default_copy: bool, per_call: Optional[bool]) -> bool:
    """The preference that governs preprocessing: the per-call preference if the
    caller supplied one (not ``None``), otherwise the construction-time default."""
    if per_call is None:
        return default_copy
    return per_call
# pure-end


def fit(config: Estimator, data: InputArray, copy_X: Optional[bool]) -> bool:
    # pre-conditions-start
    # config is read-only (the construction-time default is consulted, not
    # changed) -> fractional permission; the array's format flag is likewise
    # only consulted -> fractional permission; data.intact IS mutated -> full
    # permission.
    Requires(Acc(config.default_copy, 1 / 2))
    Requires(Acc(data.intact))
    Requires(Acc(data.native_format, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(config.default_copy, 1 / 2))
    Ensures(config.default_copy == Old(config.default_copy))
    Ensures(Acc(data.intact))
    Ensures(Acc(data.native_format, 1 / 2))
    Ensures(data.native_format == Old(data.native_format))
    # (1) the preference governing preprocessing is the per-call one when given,
    # else the construction-time default — the per-call choice is not discarded.
    Ensures(Result() == selected_preference(Old(config.default_copy), copy_X))
    # (2) the input array is left intact iff the selected preference is True OR
    # the array was not already in the native working format (in which case
    # validation materialized a converted copy, shielding the caller's array).
    Ensures(data.intact == (Result() or not data.native_format))
    # post-conditions-end
    # impl-start
    if copy_X is None:
        copy_X = config.default_copy
    effective = copy_X  # governs both preprocessing and the fitting routine
    if data.native_format:
        data.intact = effective
    else:
        data.intact = True
    return effective
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for scikit-learn__scikit-learn-12973 (nagini).

SPEC SHAPE: fit's two postconditions are a COMPLETE functional spec. (1) Result() == selected_preference(Old(config.default_copy), copy_X); (2) data.intact == (Result() or not data.native_format). Both pin the observables as total functions of the inputs. The suspected hole was parameter-reassignment: postcond 1 names `copy_X`, which the impl reassigns (`if copy_X is None: copy_X = config.default_copy`). If Nagini bound that `copy_X` to its EXIT value, the postcondition would self-satisfy and admit wrong impls. It does NOT — Nagini binds the postcondition `copy_X` to the parameter ENTRY value (Old-semantics for the arg), so the hole is closed. Proven directly: atk_1/atk_2/atk_4 exploit exactly that reassignment and all FAIL to verify on postcond 1.

### ATTACKS (all same-spec confirmed via `adversary same-spec`, byte-identical spec signature; all editing only the impl region):
- atk_1.py (reassignment-hole, return True always): `python -m swebench_unified.adversary weakness nagini <id> atk_1.py` -> EXIT 2 NOT-A-COUNTEREXAMPLE (verification failed). Rejected.
- atk_2.py (reassignment-hole, return False always): weakness EXIT 2, verification failed. Rejected.
- atk_3.py (prepatch bug un-laundered: effective=config.default_copy): weakness EXIT 2; direct nagini_verify.sh -> error at line 95 'Postcondition ... Result() == selected_preference(Old(config.default_copy), copy_X) might not hold'. Genuine postcond-1 rejection.
- atk_4.py (prepatch bug laundered through copy_X reassignment, return copy_X): weakness EXIT 2, verification failed. Rejected (confirms reassignment does not launder the discriminating case).
- atk_5.py (boundary swap: correct selection but data.intact = not resolved on native path): weakness EXIT 2; direct verify -> error at line 99 'Postcondition ... data.intact == (Result() or not data.native_format) might not hold'. Genuine postcond-2 rejection.
- atk_6.py (ungrounded-oracle echo: data.intact=resolved, drops the not-native_format shield): weakness EXIT 2, verification failed. Rejected.
- atk_7.py (control-flow-effect / partial domain: only assigns data.intact on the native_format branch, leaks old value else): weakness EXIT 2, verification failed. Rejected.

No attack came back a CANDIDATE (exit 0), so there was NO verifying wrong impl whose faithful patch needed materializing/resolving. patches={} accordingly.

POSITIVE CONTROL: pos_control.py (gold impl verbatim) -> `adversary weakness` EXIT 0 CANDIDATE (shares spec AND verifies) — confirms the frozen spec is satisfiable by the gold impl (verifier + harness plumbing healthy).

PREPATCH TWIN (G-DIFF): model_prepatch.py copied to prepatch.py; same-spec confirmed; nagini_verify.sh EXIT 1 with error at line 95 on postcond 1 — the spec senses the fix exactly at copy_X=False & default_copy=True (the F2P case). prepatch_reproduced=true.

REFINEMENT AUDIT: refinement.md legs are all R / I / A-reference (no @ContractOnly axiom consumed; axioms region empty; NO kind-3 unexpressible-changed-op). Steps 1,2,6 = R (Optional[bool]/bool carriers, touched-field Estimator.default_copy, return-value abstraction to the governing preference). Steps 3,4 = I (identical control flow). Step 5 = the single A-reference: model's deep boolean `data.intact == (effective or not native_format)` is validated == the real LassoLarsIC.fit/_preprocess_data by axiom_check.py, which runs the REAL post-fix fit over the full cross product {T,F}x{T,F,None}x{native T,F} + 200 fuzz and asserts np.array_equal(X,X_copy) == (selected_preference(init,call) or not native). The A-reference correspondence to the real callee (check_array(X, copy=copy_X, dtype=FLOAT_DTYPES): copy-iff-flag on native float dtype, conversion-shielded on non-float) holds and matches mapping.md/base.py:117,150. Correspondence is faithful.

CONCLUSION: The spec fully determines both observables; every distinct wrong impl (partial-domain, boundary-invert, control-flow-effect, ungrounded-oracle echo, and both un-laundered and reassignment-laundered prepatch bugs) is rejected; the gold verifies; the prepatch fails at the discriminating assertion; refinement legs and the A-reference are sound. verify => correct holds. Verdict SOUND. All >=5 required attacks (7) were fully verified under calm load; positive control and prepatch both ran; no needed resolve run was blocked (none was triggered since no CANDIDATE arose).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-12973.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An estimator records, at construction time, a default boolean preference for
  whether the training-data array passed to the model-fitting routine is
  preserved (left byte-for-byte intact) or may be overwritten in place during
  preprocessing. The fitting routine ALSO accepts a per-call preference.

  The desired behaviour is that the per-call preference, when the caller
  supplies one, takes precedence over the construction-time default; when the
  caller supplies no per-call preference (the "unset" value), the
  construction-time default is used. Whichever preference is thus selected
  governs preprocessing in full:

    (1) the preference that actually governs preprocessing equals the per-call
        preference if one was supplied, otherwise the construction-time default
        (the per-call choice is never silently discarded); and

    (2) the input array's fate follows that selected preference, subject to
        the routine's numeric working format: the routine computes in a
        designated numeric representation, and when the supplied array is not
        already in that representation, input validation materializes a
        converted working copy up front, so the caller's array is left intact
        regardless of the selected preference. When the array IS already in
        the native working format, it is left intact after fitting if and
        only if the selected preference is "preserve" (True): a "preserve"
        selection copies the array before preprocessing, a "may overwrite"
        selection lets preprocessing mutate it in place.

The per-call preference is modelled as ``Optional[bool]`` (``None`` = "unset").
The estimator's construction-time default and the input array's touched
observables are modelled as minimal objects carrying only the touched fields:
``intact`` (the boolean the fitting routine's caller observes afterwards) and
``native_format`` (whether the array is already in the routine's native
numeric working representation — the property that decides whether validation
must materialize a converted copy).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class Estimator:
    def __init__(self, default_copy: bool) -> None:
        Ensures(Acc(self.default_copy) and self.default_copy == default_copy)  # type: ignore
        self.default_copy = default_copy


class InputArray:
    def __init__(self, intact: bool, native_format: bool) -> None:
        Ensures(Acc(self.intact) and self.intact == intact)  # type: ignore
        Ensures(Acc(self.native_format) and self.native_format == native_format)  # type: ignore
        self.intact = intact
        self.native_format = native_format


# axioms-start
# (no callee is axiomatized: the changed behaviour is a boolean dataflow — the
# selection of the governing preference and its consequence for the input array
# — and is modelled deeply below, not behind a @ContractOnly axiom.)
# axioms-end


# pure-start
@Pure
def selected_preference(default_copy: bool, per_call: Optional[bool]) -> bool:
    """The preference that governs preprocessing: the per-call preference if the
    caller supplied one (not ``None``), otherwise the construction-time default."""
    if per_call is None:
        return default_copy
    return per_call
# pure-end


def fit(config: Estimator, data: InputArray, copy_X: Optional[bool]) -> bool:
    # pre-conditions-start
    # config is read-only (the construction-time default is consulted, not
    # changed) -> fractional permission; the array's format flag is likewise
    # only consulted -> fractional permission; data.intact IS mutated -> full
    # permission.
    Requires(Acc(config.default_copy, 1 / 2))
    Requires(Acc(data.intact))
    Requires(Acc(data.native_format, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(config.default_copy, 1 / 2))
    Ensures(config.default_copy == Old(config.default_copy))
    Ensures(Acc(data.intact))
    Ensures(Acc(data.native_format, 1 / 2))
    Ensures(data.native_format == Old(data.native_format))
    # (1) the preference governing preprocessing is the per-call one when given,
    # else the construction-time default — the per-call choice is not discarded.
    Ensures(Result() == selected_preference(Old(config.default_copy), copy_X))
    # (2) the input array is left intact iff the selected preference is True OR
    # the array was not already in the native working format (in which case
    # validation materialized a converted copy, shielding the caller's array).
    Ensures(data.intact == (Result() or not data.native_format))
    # post-conditions-end
    # impl-start
    if copy_X is None:
        copy_X = config.default_copy
    effective = copy_X  # governs both preprocessing and the fitting routine
    if data.native_format:
        data.intact = effective
    else:
        data.intact = True
    return effective
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for scikit-learn__scikit-learn-12973 (nagini).

SPEC SHAPE: fit's two postconditions are a COMPLETE functional spec. (1) Result() == selected_preference(Old(config.default_copy), copy_X); (2) data.intact == (Result() or not data.native_format). Both pin the observables as total functions of the inputs. The suspected hole was parameter-reassignment: postcond 1 names `copy_X`, which the impl reassigns (`if copy_X is None: copy_X = config.default_copy`). If Nagini bound that `copy_X` to its EXIT value, the postcondition would self-satisfy and admit wrong impls. It does NOT — Nagini binds the postcondition `copy_X` to the parameter ENTRY value (Old-semantics for the arg), so the hole is closed. Proven directly: atk_1/atk_2/atk_4 exploit exactly that reassignment and all FAIL to verify on postcond 1.

### ATTACKS (all same-spec confirmed via `adversary same-spec`, byte-identical spec signature; all editing only the impl region):
- atk_1.py (reassignment-hole, return True always): `python -m swebench_unified.adversary weakness nagini <id> atk_1.py` -> EXIT 2 NOT-A-COUNTEREXAMPLE (verification failed). Rejected.
- atk_2.py (reassignment-hole, return False always): weakness EXIT 2, verification failed. Rejected.
- atk_3.py (prepatch bug un-laundered: effective=config.default_copy): weakness EXIT 2; direct nagini_verify.sh -> error at line 95 'Postcondition ... Result() == selected_preference(Old(config.default_copy), copy_X) might not hold'. Genuine postcond-1 rejection.
- atk_4.py (prepatch bug laundered through copy_X reassignment, return copy_X): weakness EXIT 2, verification failed. Rejected (confirms reassignment does not launder the discriminating case).
- atk_5.py (boundary swap: correct selection but data.intact = not resolved on native path): weakness EXIT 2; direct verify -> error at line 99 'Postcondition ... data.intact == (Result() or not data.native_format) might not hold'. Genuine postcond-2 rejection.
- atk_6.py (ungrounded-oracle echo: data.intact=resolved, drops the not-native_format shield): weakness EXIT 2, verification failed. Rejected.
- atk_7.py (control-flow-effect / partial domain: only assigns data.intact on the native_format branch, leaks old value else): weakness EXIT 2, verification failed. Rejected.

No attack came back a CANDIDATE (exit 0), so there was NO verifying wrong impl whose faithful patch needed materializing/resolving. patches={} accordingly.

POSITIVE CONTROL: pos_control.py (gold impl verbatim) -> `adversary weakness` EXIT 0 CANDIDATE (shares spec AND verifies) — confirms the frozen spec is satisfiable by the gold impl (verifier + harness plumbing healthy).

PREPATCH TWIN (G-DIFF): model_prepatch.py copied to prepatch.py; same-spec confirmed; nagini_verify.sh EXIT 1 with error at line 95 on postcond 1 — the spec senses the fix exactly at copy_X=False & default_copy=True (the F2P case). prepatch_reproduced=true.

REFINEMENT AUDIT: refinement.md legs are all R / I / A-reference (no @ContractOnly axiom consumed; axioms region empty; NO kind-3 unexpressible-changed-op). Steps 1,2,6 = R (Optional[bool]/bool carriers, touched-field Estimator.default_copy, return-value abstraction to the governing preference). Steps 3,4 = I (identical control flow). Step 5 = the single A-reference: model's deep boolean `data.intact == (effective or not native_format)` is validated == the real LassoLarsIC.fit/_preprocess_data by axiom_check.py, which runs the REAL post-fix fit over the full cross product {T,F}x{T,F,None}x{native T,F} + 200 fuzz and asserts np.array_equal(X,X_copy) == (selected_preference(init,call) or not native). The A-reference correspondence to the real callee (check_array(X, copy=copy_X, dtype=FLOAT_DTYPES): copy-iff-flag on native float dtype, conversion-shielded on non-float) holds and matches mapping.md/base.py:117,150. Correspondence is faithful.

CONCLUSION: The spec fully determines both observables; every distinct wrong impl (partial-domain, boundary-invert, control-flow-effect, ungrounded-oracle echo, and both un-laundered and reassignment-laundered prepatch bugs) is rejected; the gold verifies; the prepatch fails at the discriminating assertion; refinement legs and the A-reference are sound. verify => correct holds. Verdict SOUND. All >=5 required attacks (7) were fully verified under calm load; positive control and prepatch both ran; no needed resolve run was blocked (none was triggered since no CANDIDATE arose).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical to the bundle (same-spec self-check on model.py -> SAME, exit 0); model verifies under Nagini (9.26s). Ran the FULL modeled domain differential against the real repo callee: default_copy in {T,F} x per_call in {T,F,None} x native_format in {T,F} = 12 abstract points, two independent ways -- (a) via check_array(X, copy=copy_X, dtype=FLOAT_DTYPES) and (b) via the actual LinearModel._preprocess_data (sklearn._base) with LassoLarsIC defaults fit_intercept=True, normalize=True. BAD=0 in both: the modeled postcondition data.intact == (selected_preference(default_copy, copy_X) or not native_format) agrees with the real LassoLarsIC.fit array-preservation observable at EVERY point. (Full container-level LassoLarsIC.fit was attempted but the instance image is BLAS-pathologically slow -- single fits time out; the _preprocess_data/check_array differential is the exact governing path per mapping.md and axiom_check.py and is the faithful oracle.) The recorded verdict.md Role-3 UNFAITHFUL fail was against the PRIOR spec whose postcondition was unconditional (data.intact == Result(), no dtype-conversion shield). Its counterexample (default_copy=True, per_call=False, integer/non-native X: real leaves X intact=True while selected preference=False) is now CORRECTLY MODELED by the added `native_format` field and the `or not data.native_format` disjunct: at that point Result()=False, native_format=False => model predicts intact=True, matching the real callee. The spec was repaired; no diverging input remains in the modeled domain. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no patched file path sklearn/linear_model/least_angle.py, no patched module dotted-path, no patched repo symbol LassoLarsIC/_preprocess_data, no narration terms, no reproduced gold-patch line). Substantive check confirms no leak beyond the PUBLIC problem_statement: the reporter themselves states the fix — 'I propose that fit takes a default value of None and only overwrites the existing value if the user has explicitly passed it as an argument to fit.' The spec view's discriminating content — copy_X, fit, Optional[bool]/None, and the precedence rule (per-call preference wins when supplied, else the construction-time default) — is therefore already solver-visible in problem_statement; the spec view merely restates it at an abstract behavioral altitude with generic modeling names (Estimator, InputArray, selected_preference, default_copy). The repo-specific edit locators (LassoLarsIC, _preprocess_data, the file path, gold hunk lines) appear ONLY in the audit docs mapping.md/refinement.md, which are NOT the consumer spec view. Postcondition (2) (native_format / dtype-conversion shielding) is NOT in the problem statement, but it models the UNCHANGED _preprocess_data/check_array behavior (ambient context), not the gold edit; the discriminator is postcondition (1) + selected_preference, which is exactly the publicly-described change. No spec-view line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
