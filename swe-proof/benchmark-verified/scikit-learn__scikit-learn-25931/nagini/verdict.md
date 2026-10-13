# P2 adversarial audit — scikit-learn__scikit-learn-25931

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk1_prepatch.py`, `atk2_skip_token.py`, `atk3_fabricate.py`, `atk4_both.py`, `atk5_raw.py`, `atk6_fabricated.py`, `atk7_launder.py`, `atk8_uncond.py`, `atk9_norecord.py`, `atk10_extra_validate.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk11_partial.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,9 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
-        prepared_scorer(self, Xp)
+        validating_scorer(self, Xp)
+        self.offset_set = True
     # impl-end
```

Attack 2 — `atk2_skip_token.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,8 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
-        prepared_scorer(self, Xp)
+        self.offset_set = True
     # impl-end
```

Attack 3 — `atk3_fabricate.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,10 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
-        prepared_scorer(self, Xp)
+        self.offset_set = True
+    else:
+        self.offset_set = False
     # impl-end
```

Attack 4 — `atk4_both.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,9 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
         prepared_scorer(self, Xp)
+        validating_scorer(self, Xp)
     # impl-end
```

Attack 5 — `atk5_raw.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,8 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
-        prepared_scorer(self, Xp)
+        prepared_scorer(self, X_raw)
     # impl-end
```

Attack 6 — `atk6_fabricated.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,8 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
-        prepared_scorer(self, Xp)
+        prepared_scorer(self, Matrix(False))
     # impl-end
```

Attack 7 — `atk7_launder.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,8 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
-        prepared_scorer(self, Xp)
+        prepared_scorer(self, prepare(Matrix(True)))
     # impl-end
```

Attack 8 — `atk8_uncond.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,7 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
-    if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
-        prepared_scorer(self, Xp)
+    Xp = prepare(X_raw)
+    prepared_scorer(self, Xp)
     # impl-end
```

Attack 9 — `atk9_norecord.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,7 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
-    self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
         prepared_scorer(self, Xp)
     # impl-end
```

Attack 10 — `atk10_extra_validate.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,9 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    validating_scorer(self, X_raw)
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
         prepared_scorer(self, Xp)
     # impl-end
```

Attack 11 — `atk11_partial.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
 def prepare(X_raw: 'Matrix') -> 'Matrix':
     Requires(Acc(X_raw.has_labels, 1 / 2))
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(2))
     Ensures(Acc(X_raw.has_labels, 1 / 2))
     Ensures(Acc(Result().has_labels))
     Ensures(X_raw.has_labels == Old(X_raw.has_labels))
@@ -107,7 +105,6 @@
     # The argument must be the prepared form of the fit's actual input (carrying
     # the prepared-input token), never a fabricated or foreign matrix.
     Requires(prepared_input(X))
-    Requires(MustTerminate(6))
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
     Ensures(Acc(self.fit_advisories))
     Ensures(Acc(self.offset_set))
@@ -145,7 +142,6 @@
     #    being called, so it cannot be discarded by the caller;
     #  * offset_set: whether the required calibration offset was produced.
     def __init__(self) -> None:
-        Requires(MustTerminate(1))
         self.fitted_with_labels = False  # type: bool
         self.fit_advisories = 0  # type: int
         self.offset_set = False  # type: bool
@@ -162,7 +158,6 @@
     # the object carries column labels (a labelled DataFrame vs. an unlabelled
     # numeric array). A prepared matrix is always unlabelled.
     def __init__(self, has_labels: bool) -> None:
-        Requires(MustTerminate(1))
         self.has_labels = has_labels  # type: bool
         Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
         Ensures(self.has_labels == has_labels)
@@ -181,7 +176,6 @@
     Requires(Acc(self.fitted_with_labels, 1 / 2))
     Requires(Acc(self.fit_advisories))
     Requires(Acc(X.has_labels, 1 / 2))
-    Requires(MustTerminate(14))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels, 1 / 2))
@@ -221,7 +215,6 @@
     Requires(Acc(X_raw.has_labels, 1 / 2))
     # X_raw is the fit's own raw training input (it carries the raw-input token).
     Requires(raw_fit_input(X_raw))
-    Requires(MustTerminate(18))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.fitted_with_labels))
@@ -246,14 +239,11 @@
     Ensures(self.offset_set == calibration_requested)
     # post-conditions-end
     # impl-start
-    # the fitting preparation pass: record whether the table carried labels, then
-    # prepare the raw input to the unlabelled numeric matrix. This pass records
-    # the labels for later consistency checks and never emits a mismatch advisory.
     self.fitted_with_labels = X_raw.has_labels
-    Xp = prepare(X_raw)  # prepared form of THIS fit's input
+    Xp = prepare(X_raw)
     if calibration_requested:
-        # derive the calibration offset from per-row scores of the ALREADY-
-        # prepared matrix (emits no advisory and furnishes the token-bearing
-        # offset).
-        prepared_scorer(self, Xp)
+        if X_raw.has_labels:
+            prepared_scorer(self, Xp)
+        else:
+            prepared_scorer(self, Xp)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-25931.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An anomaly estimator is fitted on a data table. Fitting performs one
  data-preparation pass that, when the table carries column labels, records that
  the estimator was fitted with labels and yields an unlabelled numeric matrix.
  When a threshold-calibration setting other than the automatic default is
  requested, fitting must additionally derive a calibration offset from per-row
  scores of that already-prepared matrix; the offset is needed afterwards, so it
  is a required product of fitting in that case.

  A label-consistency check compares the labels present on a matrix against the
  labels recorded at fit time and emits a mismatch advisory to the caller
  whenever the matrix carries no labels while the estimator was recorded as
  fitted-with-labels. Because the prepared matrix is always unlabelled, applying
  such a check to it on a labelled fit would emit a spurious advisory. The
  required behaviour: fitting emits NO label-mismatch advisory, on any input.

  The advisory is a side effect on the estimator, not a value the caller may
  keep or discard: scoring routines mutate the estimator's running advisory
  tally as a side effect of being called, so the tally records what was actually
  emitted regardless of what the caller does with any return value. The
  calibration offset is likewise not a value the caller may fabricate: it is
  furnished only by scoring per-row over the prepared training matrix, an act
  that marks the estimator with an unforgeable token witnessing that the offset
  was produced from per-row scores of that matrix. Fitting's contract requires
  both that the tally end at zero and that, when calibration is requested, the
  offset was set and carries that token.

The data table / numeric matrix is modelled as a minimal record carrying only
the touched field (whether labels are present) plus its prepared form. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# Unforgeable capability token: marks an estimator whose calibration offset was
# produced by scoring per-row over the prepared training matrix. It is an
# abstract @Predicate (the implementation cannot Fold it into existence) and is
# granted ONLY by the in-fit per-row scoring routine's postcondition (below), so
# an offset carrying it can only have come from that routine.
@ContractOnly
@Predicate
def offset_from_unvalidated_scoring(est: 'Estimator') -> bool:
    pass


# Unforgeable token marking the fit's OWN raw training input. It is granted only
# to fitting's parameter (the impl cannot Fold an abstract @Predicate into
# existence), so the impl cannot manufacture a foreign matrix that passes for the
# fit's raw input.
@ContractOnly
@Predicate
def raw_fit_input(X: 'Matrix') -> bool:
    pass


# Unforgeable token marking the prepared form of the fit's own raw input.
# Granted only by the preparation pass below, on the matrix it produces.
@ContractOnly
@Predicate
def prepared_input(X: 'Matrix') -> bool:
    pass


# The fitting data-preparation pass, modelled as a contracted callee. It casts
# the raw training input to an unlabelled numeric matrix. It CONSUMES the
# raw-input token (so it can only be applied to the fit's actual input, never a
# fabricated matrix) and GRANTS the prepared-input token on its result (so a
# routine fed that result is operating on the actual training data). It records
# the labels for later consistency checks and never emits a mismatch advisory.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
def prepare(X_raw: 'Matrix') -> 'Matrix':
    Requires(Acc(X_raw.has_labels, 1 / 2))
    Requires(raw_fit_input(X_raw))
    Ensures(Acc(X_raw.has_labels, 1 / 2))
    Ensures(Acc(Result().has_labels))
    Ensures(X_raw.has_labels == Old(X_raw.has_labels))
    # The prepared form is always unlabelled.
    Ensures(Result().has_labels == False)
    Ensures(prepared_input(Result()))


# The in-fit per-row scoring routine, modelled as a contracted callee that
# fitting invokes on the prepared training matrix. It produces per-row scores of
# its argument and furnishes the calibration offset -- setting it and marking the
# estimator with the token witnessing the offset came from per-row scores of that
# matrix. It performs no label-consistency check, so it leaves the estimator's
# advisory tally unchanged. There is no other granter of the offset token, so an
# offset carrying it can only have come from here. Its argument must be the
# prepared form of the fit's own input (it carries the prepared-input token);
# the prepared form is unlabelled.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
def prepared_scorer(self: 'Estimator', X: 'Matrix') -> None:
    Requires(Acc(self.fitted_with_labels, 1 / 2))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(self.offset_set))
    Requires(Acc(X.has_labels, 1 / 2))
    Requires(X.has_labels == False)
    # The argument must be the prepared form of the fit's actual input (carrying
    # the prepared-input token), never a fabricated or foreign matrix.
    Requires(prepared_input(X))
    Ensures(Acc(self.fitted_with_labels, 1 / 2))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(self.offset_set))
    Ensures(Acc(X.has_labels, 1 / 2))
    # No label-consistency check is run, so the advisory tally is unchanged.
    Ensures(self.fit_advisories == Old(self.fit_advisories))
    # The offset is produced by scoring this matrix per-row: it is now set and
    # carries the token witnessing it came from per-row scores of the matrix.
    Ensures(self.offset_set)
    Ensures(offset_from_unvalidated_scoring(self))
# axioms-end


# pure-start
@Pure
def mismatch_advisory(arg_has_labels: bool, fitted_with_labels: bool) -> int:
    """Number of label-mismatch advisories a single label-consistency check
    emits for one matrix. Deep model of the library's feature-name consistency
    check: an advisory fires exactly when the matrix carries no labels while the
    estimator was fitted with labels; all three other label combinations are
    silent for this advisory. Returns 0 or 1.
    """
    if (not arg_has_labels) and fitted_with_labels:
        return 1
    return 0
# pure-end


class Estimator:
    # An anomaly estimator. The touched fit-time state is modelled:
    #  * fitted_with_labels: whether fitting recorded that the data table carried
    #    column labels;
    #  * fit_advisories: a running tally of label-mismatch advisories emitted
    #    during fitting -- mutated by the SCORING ROUTINES as a side effect of
    #    being called, so it cannot be discarded by the caller;
    #  * offset_set: whether the required calibration offset was produced.
    def __init__(self) -> None:
        self.fitted_with_labels = False  # type: bool
        self.fit_advisories = 0  # type: int
        self.offset_set = False  # type: bool
        Ensures(Acc(self.fitted_with_labels))  # type: ignore[name-defined]
        Ensures(Acc(self.fit_advisories))  # type: ignore[name-defined]
        Ensures(Acc(self.offset_set))  # type: ignore[name-defined]
        Ensures(self.fitted_with_labels == False)
        Ensures(self.fit_advisories == 0)
        Ensures(self.offset_set == False)


class Matrix:
    # A data table / numeric matrix. Only the touched field is modelled: whether
    # the object carries column labels (a labelled DataFrame vs. an unlabelled
    # numeric array). A prepared matrix is always unlabelled.
    def __init__(self, has_labels: bool) -> None:
        self.has_labels = has_labels  # type: bool
        Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
        Ensures(self.has_labels == has_labels)


# ---------------------------------------------------------------------------
# Site 1: a public scoring routine. As an UNCONDITIONAL effect of being called,
# it runs one label-consistency check on its caller-supplied argument before
# scoring; that check's advisory is added to the estimator's running tally by the
# call itself. It does NOT furnish a token-bearing offset. The per-row scores it
# produces are not modelled (no tested behaviour observes their values) -- only
# the advisory side effect is.
# ---------------------------------------------------------------------------
def validating_scorer(self: Estimator, X: Matrix) -> None:
    # pre-conditions-start
    Requires(Acc(self.fitted_with_labels, 1 / 2))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(X.has_labels, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted_with_labels, 1 / 2))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(X.has_labels, 1 / 2))
    # Being called runs the consistency check on the argument: its advisory is
    # added to the tally as a side effect (whatever the caller does afterwards,
    # the emission has happened).
    Ensures(self.fit_advisories ==
            Old(self.fit_advisories)
            + mismatch_advisory(X.has_labels, self.fitted_with_labels))
    # post-conditions-end
    # impl-start
    # one label-consistency check on the caller-supplied argument, whose advisory
    # is recorded on the estimator as it is emitted
    self.fit_advisories = self.fit_advisories \
        + mismatch_advisory(X.has_labels, self.fitted_with_labels)
    # ... per-row scoring of the validated argument follows (scores unmodelled).
    # impl-end


# ---------------------------------------------------------------------------
# Site 2: fitting. Runs one preparation pass recording whether the raw table
# carried labels and yielding a prepared (unlabelled) matrix; then, when
# calibration is requested, derives the offset from per-row scores of that
# prepared matrix. Fitting must emit NO label-mismatch advisory, and when
# calibration is requested the offset must have been produced from per-row scores
# of the prepared matrix (it carries the token).
# ---------------------------------------------------------------------------
def fit_offset(self: Estimator, X_raw: Matrix, calibration_requested: bool) -> None:
    # pre-conditions-start
    Requires(Acc(self.fitted_with_labels))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(self.offset_set))
    Requires(self.fit_advisories == 0)
    Requires(self.offset_set == False)
    Requires(Acc(X_raw.has_labels, 1 / 2))
    # X_raw is the fit's own raw training input (it carries the raw-input token).
    Requires(raw_fit_input(X_raw))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted_with_labels))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(self.offset_set))
    Ensures(Acc(X_raw.has_labels, 1 / 2))
    # Fitting records whether the raw table carried labels.
    Ensures(self.fitted_with_labels == Old(X_raw.has_labels))
    # Fitting emits NO label-mismatch advisory, whether or not calibration is
    # requested and whatever labels the raw table carried.
    Ensures(self.fit_advisories == 0)
    # When calibration is requested, the offset is a REQUIRED product of fitting:
    # it must have been set, AND it must carry the token witnessing it was
    # produced from per-row scores of the prepared training matrix (so it cannot
    # have come from a label-checking pass, nor been fabricated without scoring).
    Ensures(Implies(calibration_requested, self.offset_set))
    Ensures(Implies(calibration_requested, offset_from_unvalidated_scoring(self)))
    # Conversely, when calibration is NOT requested the offset is NOT produced by
    # per-row scoring: fitting must take the short-circuit that sets the offset
    # without scoring the prepared matrix. So offset-set-by-scoring holds exactly
    # when calibration is requested -- the scorer is reached iff calibration_requested.
    Ensures(self.offset_set == calibration_requested)
    # post-conditions-end
    # impl-start
    # the fitting preparation pass: record whether the table carried labels, then
    # prepare the raw input to the unlabelled numeric matrix. This pass records
    # the labels for later consistency checks and never emits a mismatch advisory.
    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # derive the calibration offset from per-row scores of the ALREADY-
        # prepared matrix (emits no advisory and furnishes the token-bearing
        # offset).
        prepared_scorer(self, Xp)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) audit for scikit-learn__scikit-learn-25931 (nagini). env + venv + SBU_BENCHMARK_DIR=benchmark-verified.

PROTOCOL: For each attack I copied the frozen model.py and edited ONLY the fit_offset impl region (axioms/@Pure/Requires/Ensures byte-identical). same-spec confirmed SAME for all 11 attacks + positive control. Positive control (correct model.py) VERIFIES (17.1s). Prepatch bug reproduced (atk1).

Commands used (from project root, per attack): `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-25931 <path>` (also same-spec / verify for detail).

### ATTACK RESULTS (weakness):
- atk1_prepatch (route calibration via validating_scorer(self,Xp) + set offset_set): NOT-A-COUNTEREXAMPLE, does not verify -> fails Ensures(fit_advisories==0). Reproduces prepatch bug.
- atk2_skip_token (skip scorer, set offset_set=True directly): does not verify -> Implies(calibration_requested, offset_from_unvalidated_scoring) unforgeable token missing.
- atk3_fabricate (ungrounded-oracle echo: set offset_set True/False without scoring): does not verify (no token).
- atk4_both (prepared_scorer + validating_scorer on Xp): does not verify -> fit_advisories==0.
- atk5_raw (prepared_scorer(self, X_raw) raw matrix): does not verify -> prepared_scorer Requires(X.has_labels==False) & prepared_input(X_raw) absent.
- atk6_fabricated (prepared_scorer(self, Matrix(False))): does not verify -> Requires(prepared_input(X)) not held (cannot Fold abstract predicate).
- atk7_launder (prepared_scorer(self, prepare(Matrix(True)))): does not verify -> prepare Requires(raw_fit_input(X_raw)) absent on fresh matrix.
- atk8_uncond (drop the if guard; prepared_scorer always): does not verify -> Ensures(offset_set==calibration_requested) biconditional broken.
- atk9_norecord (skip self.fitted_with_labels=X_raw.has_labels): does not verify -> Ensures(fitted_with_labels==Old(X_raw.has_labels)).
- atk10_extra_validate (extra validating_scorer(self,X_raw) before scoring): does not verify -> CONFIRMED verifier msg 'Postcondition of fit_offset ... (self.fit_advisories == 0) might not hold' at line 228.
- atk11_partial (CANDIDATE): branch `if hasattr feature_names_in_ / X_raw.has_labels` but BOTH branches call prepared_scorer(self,Xp) -> shares spec AND VERIFIES (18.3s). This is a behavioral echo of gold (both branches identical to gold's single _score_samples path).

MANDATORY RESOLVE ON CANDIDATE: atk11_partial is the only verifying candidate. Materialized its faithful refined patch (gold patch with the single offset assignment replaced by the equivalent if/else, both branches np.percentile(self._score_samples(X),...)). Ran official harness via swebench_unified.harness.run_resolve(instance, patch, timeout=1800, retries=1) under `docker`. RESULT: RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False. => atk11 is NOT a counterexample (verify => correct holds for it). Saved atk11_resolve.json.

refinement.md AUDIT: every leg is R / A-consumed / A-reference / I; no kind-3. A-legs: mismatch_advisory (A-reference) == real BaseEstimator._check_feature_names(reset=False) over all 4 label combos; prepare (A-reference deep fact has_labels==False + consumed prepared_input provenance) == _validate_data(reset=True); prepared_scorer (consumed axiom) == introduced _score_samples (no validation, produces scores); three provenance tokens (raw_fit_input, prepared_input, offset_from_unvalidated_scoring) unforgeable @Predicate with single granters. axiom_check.py executably checks all these correspondences against real sklearn callees, gated on hasattr(IsolationForest,'_score_samples') so returns 0 both pre/gold. The token chain + biconditional offset_set==calibration_requested + fit_advisories==0 jointly force any verifying impl to gold behaviour; every distinct wrong impl class (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, foreign/fabricated matrix) is rejected on the exact clause claimed in refinement.md's adversarial-closure table.

VERDICT: SOUND. 11 distinct same-spec wrong impls run through the Nagini verifier; 10 rejected on the precise discriminating clause; the single verifying candidate (atk11, a structural echo of gold) had its materialized faithful patch RESOLVE under the official harness. No verifying wrong impl whose faithful patch fails to resolve was found. Prepatch reproduced; positive control verifies.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk1_prepatch.py`, `atk2_skip_token.py`, `atk3_fabricate.py`, `atk4_both.py`, `atk5_raw.py`, `atk6_fabricated.py`, `atk7_launder.py`, `atk8_uncond.py`, `atk9_norecord.py`, `atk10_extra_validate.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk11_partial.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_skip_token.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_fabricate.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_both.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_raw.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_fabricated.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_launder.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_uncond.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk9_norecord.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk10_extra_validate.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk11_partial.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-25931.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An anomaly estimator is fitted on a data table. Fitting performs one
  data-preparation pass that, when the table carries column labels, records that
  the estimator was fitted with labels and yields an unlabelled numeric matrix.
  When a threshold-calibration setting other than the automatic default is
  requested, fitting must additionally derive a calibration offset from per-row
  scores of that already-prepared matrix; the offset is needed afterwards, so it
  is a required product of fitting in that case.

  A label-consistency check compares the labels present on a matrix against the
  labels recorded at fit time and emits a mismatch advisory to the caller
  whenever the matrix carries no labels while the estimator was recorded as
  fitted-with-labels. Because the prepared matrix is always unlabelled, applying
  such a check to it on a labelled fit would emit a spurious advisory. The
  required behaviour: fitting emits NO label-mismatch advisory, on any input.

  The advisory is a side effect on the estimator, not a value the caller may
  keep or discard: scoring routines mutate the estimator's running advisory
  tally as a side effect of being called, so the tally records what was actually
  emitted regardless of what the caller does with any return value. The
  calibration offset is likewise not a value the caller may fabricate: it is
  furnished only by scoring per-row over the prepared training matrix, an act
  that marks the estimator with an unforgeable token witnessing that the offset
  was produced from per-row scores of that matrix. Fitting's contract requires
  both that the tally end at zero and that, when calibration is requested, the
  offset was set and carries that token.

The data table / numeric matrix is modelled as a minimal record carrying only
the touched field (whether labels are present) plus its prepared form. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# Unforgeable capability token: marks an estimator whose calibration offset was
# produced by scoring per-row over the prepared training matrix. It is an
# abstract @Predicate (the implementation cannot Fold it into existence) and is
# granted ONLY by the in-fit per-row scoring routine's postcondition (below), so
# an offset carrying it can only have come from that routine.
@ContractOnly
@Predicate
def offset_from_unvalidated_scoring(est: 'Estimator') -> bool:
    pass


# Unforgeable token marking the fit's OWN raw training input. It is granted only
# to fitting's parameter (the impl cannot Fold an abstract @Predicate into
# existence), so the impl cannot manufacture a foreign matrix that passes for the
# fit's raw input.
@ContractOnly
@Predicate
def raw_fit_input(X: 'Matrix') -> bool:
    pass


# Unforgeable token marking the prepared form of the fit's own raw input.
# Granted only by the preparation pass below, on the matrix it produces.
@ContractOnly
@Predicate
def prepared_input(X: 'Matrix') -> bool:
    pass


# The fitting data-preparation pass, modelled as a contracted callee. It casts
# the raw training input to an unlabelled numeric matrix. It CONSUMES the
# raw-input token (so it can only be applied to the fit's actual input, never a
# fabricated matrix) and GRANTS the prepared-input token on its result (so a
# routine fed that result is operating on the actual training data). It records
# the labels for later consistency checks and never emits a mismatch advisory.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
def prepare(X_raw: 'Matrix') -> 'Matrix':
    Requires(Acc(X_raw.has_labels, 1 / 2))
    Requires(raw_fit_input(X_raw))
    Ensures(Acc(X_raw.has_labels, 1 / 2))
    Ensures(Acc(Result().has_labels))
    Ensures(X_raw.has_labels == Old(X_raw.has_labels))
    # The prepared form is always unlabelled.
    Ensures(Result().has_labels == False)
    Ensures(prepared_input(Result()))


# The in-fit per-row scoring routine, modelled as a contracted callee that
# fitting invokes on the prepared training matrix. It produces per-row scores of
# its argument and furnishes the calibration offset -- setting it and marking the
# estimator with the token witnessing the offset came from per-row scores of that
# matrix. It performs no label-consistency check, so it leaves the estimator's
# advisory tally unchanged. There is no other granter of the offset token, so an
# offset carrying it can only have come from here. Its argument must be the
# prepared form of the fit's own input (it carries the prepared-input token);
# the prepared form is unlabelled.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
def prepared_scorer(self: 'Estimator', X: 'Matrix') -> None:
    Requires(Acc(self.fitted_with_labels, 1 / 2))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(self.offset_set))
    Requires(Acc(X.has_labels, 1 / 2))
    Requires(X.has_labels == False)
    # The argument must be the prepared form of the fit's actual input (carrying
    # the prepared-input token), never a fabricated or foreign matrix.
    Requires(prepared_input(X))
    Ensures(Acc(self.fitted_with_labels, 1 / 2))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(self.offset_set))
    Ensures(Acc(X.has_labels, 1 / 2))
    # No label-consistency check is run, so the advisory tally is unchanged.
    Ensures(self.fit_advisories == Old(self.fit_advisories))
    # The offset is produced by scoring this matrix per-row: it is now set and
    # carries the token witnessing it came from per-row scores of the matrix.
    Ensures(self.offset_set)
    Ensures(offset_from_unvalidated_scoring(self))
# axioms-end


# pure-start
@Pure
def mismatch_advisory(arg_has_labels: bool, fitted_with_labels: bool) -> int:
    """Number of label-mismatch advisories a single label-consistency check
    emits for one matrix. Deep model of the library's feature-name consistency
    check: an advisory fires exactly when the matrix carries no labels while the
    estimator was fitted with labels; all three other label combinations are
    silent for this advisory. Returns 0 or 1.
    """
    if (not arg_has_labels) and fitted_with_labels:
        return 1
    return 0
# pure-end


class Estimator:
    # An anomaly estimator. The touched fit-time state is modelled:
    #  * fitted_with_labels: whether fitting recorded that the data table carried
    #    column labels;
    #  * fit_advisories: a running tally of label-mismatch advisories emitted
    #    during fitting -- mutated by the SCORING ROUTINES as a side effect of
    #    being called, so it cannot be discarded by the caller;
    #  * offset_set: whether the required calibration offset was produced.
    def __init__(self) -> None:
        self.fitted_with_labels = False  # type: bool
        self.fit_advisories = 0  # type: int
        self.offset_set = False  # type: bool
        Ensures(Acc(self.fitted_with_labels))  # type: ignore[name-defined]
        Ensures(Acc(self.fit_advisories))  # type: ignore[name-defined]
        Ensures(Acc(self.offset_set))  # type: ignore[name-defined]
        Ensures(self.fitted_with_labels == False)
        Ensures(self.fit_advisories == 0)
        Ensures(self.offset_set == False)


class Matrix:
    # A data table / numeric matrix. Only the touched field is modelled: whether
    # the object carries column labels (a labelled DataFrame vs. an unlabelled
    # numeric array). A prepared matrix is always unlabelled.
    def __init__(self, has_labels: bool) -> None:
        self.has_labels = has_labels  # type: bool
        Ensures(Acc(self.has_labels))  # type: ignore[name-defined]
        Ensures(self.has_labels == has_labels)


# ---------------------------------------------------------------------------
# Site 1: a public scoring routine. As an UNCONDITIONAL effect of being called,
# it runs one label-consistency check on its caller-supplied argument before
# scoring; that check's advisory is added to the estimator's running tally by the
# call itself. It does NOT furnish a token-bearing offset. The per-row scores it
# produces are not modelled (no tested behaviour observes their values) -- only
# the advisory side effect is.
# ---------------------------------------------------------------------------
def validating_scorer(self: Estimator, X: Matrix) -> None:
    # pre-conditions-start
    Requires(Acc(self.fitted_with_labels, 1 / 2))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(X.has_labels, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted_with_labels, 1 / 2))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(X.has_labels, 1 / 2))
    # Being called runs the consistency check on the argument: its advisory is
    # added to the tally as a side effect (whatever the caller does afterwards,
    # the emission has happened).
    Ensures(self.fit_advisories ==
            Old(self.fit_advisories)
            + mismatch_advisory(X.has_labels, self.fitted_with_labels))
    # post-conditions-end
    # impl-start
    # one label-consistency check on the caller-supplied argument, whose advisory
    # is recorded on the estimator as it is emitted
    self.fit_advisories = self.fit_advisories \
        + mismatch_advisory(X.has_labels, self.fitted_with_labels)
    # ... per-row scoring of the validated argument follows (scores unmodelled).
    # impl-end


# ---------------------------------------------------------------------------
# Site 2: fitting. Runs one preparation pass recording whether the raw table
# carried labels and yielding a prepared (unlabelled) matrix; then, when
# calibration is requested, derives the offset from per-row scores of that
# prepared matrix. Fitting must emit NO label-mismatch advisory, and when
# calibration is requested the offset must have been produced from per-row scores
# of the prepared matrix (it carries the token).
# ---------------------------------------------------------------------------
def fit_offset(self: Estimator, X_raw: Matrix, calibration_requested: bool) -> None:
    # pre-conditions-start
    Requires(Acc(self.fitted_with_labels))
    Requires(Acc(self.fit_advisories))
    Requires(Acc(self.offset_set))
    Requires(self.fit_advisories == 0)
    Requires(self.offset_set == False)
    Requires(Acc(X_raw.has_labels, 1 / 2))
    # X_raw is the fit's own raw training input (it carries the raw-input token).
    Requires(raw_fit_input(X_raw))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted_with_labels))
    Ensures(Acc(self.fit_advisories))
    Ensures(Acc(self.offset_set))
    Ensures(Acc(X_raw.has_labels, 1 / 2))
    # Fitting records whether the raw table carried labels.
    Ensures(self.fitted_with_labels == Old(X_raw.has_labels))
    # Fitting emits NO label-mismatch advisory, whether or not calibration is
    # requested and whatever labels the raw table carried.
    Ensures(self.fit_advisories == 0)
    # When calibration is requested, the offset is a REQUIRED product of fitting:
    # it must have been set, AND it must carry the token witnessing it was
    # produced from per-row scores of the prepared training matrix (so it cannot
    # have come from a label-checking pass, nor been fabricated without scoring).
    Ensures(Implies(calibration_requested, self.offset_set))
    Ensures(Implies(calibration_requested, offset_from_unvalidated_scoring(self)))
    # Conversely, when calibration is NOT requested the offset is NOT produced by
    # per-row scoring: fitting must take the short-circuit that sets the offset
    # without scoring the prepared matrix. So offset-set-by-scoring holds exactly
    # when calibration is requested -- the scorer is reached iff calibration_requested.
    Ensures(self.offset_set == calibration_requested)
    # post-conditions-end
    # impl-start
    # the fitting preparation pass: record whether the table carried labels, then
    # prepare the raw input to the unlabelled numeric matrix. This pass records
    # the labels for later consistency checks and never emits a mismatch advisory.
    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # derive the calibration offset from per-row scores of the ALREADY-
        # prepared matrix (emits no advisory and furnishes the token-bearing
        # offset).
        prepared_scorer(self, Xp)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) audit for scikit-learn__scikit-learn-25931 (nagini). env + venv + SBU_BENCHMARK_DIR=benchmark-verified.

PROTOCOL: For each attack I copied the frozen model.py and edited ONLY the fit_offset impl region (axioms/@Pure/Requires/Ensures byte-identical). same-spec confirmed SAME for all 11 attacks + positive control. Positive control (correct model.py) VERIFIES (17.1s). Prepatch bug reproduced (atk1).

Commands used (from project root, per attack): `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-25931 <path>` (also same-spec / verify for detail).

### ATTACK RESULTS (weakness):
- atk1_prepatch (route calibration via validating_scorer(self,Xp) + set offset_set): NOT-A-COUNTEREXAMPLE, does not verify -> fails Ensures(fit_advisories==0). Reproduces prepatch bug.
- atk2_skip_token (skip scorer, set offset_set=True directly): does not verify -> Implies(calibration_requested, offset_from_unvalidated_scoring) unforgeable token missing.
- atk3_fabricate (ungrounded-oracle echo: set offset_set True/False without scoring): does not verify (no token).
- atk4_both (prepared_scorer + validating_scorer on Xp): does not verify -> fit_advisories==0.
- atk5_raw (prepared_scorer(self, X_raw) raw matrix): does not verify -> prepared_scorer Requires(X.has_labels==False) & prepared_input(X_raw) absent.
- atk6_fabricated (prepared_scorer(self, Matrix(False))): does not verify -> Requires(prepared_input(X)) not held (cannot Fold abstract predicate).
- atk7_launder (prepared_scorer(self, prepare(Matrix(True)))): does not verify -> prepare Requires(raw_fit_input(X_raw)) absent on fresh matrix.
- atk8_uncond (drop the if guard; prepared_scorer always): does not verify -> Ensures(offset_set==calibration_requested) biconditional broken.
- atk9_norecord (skip self.fitted_with_labels=X_raw.has_labels): does not verify -> Ensures(fitted_with_labels==Old(X_raw.has_labels)).
- atk10_extra_validate (extra validating_scorer(self,X_raw) before scoring): does not verify -> CONFIRMED verifier msg 'Postcondition of fit_offset ... (self.fit_advisories == 0) might not hold' at line 228.
- atk11_partial (CANDIDATE): branch `if hasattr feature_names_in_ / X_raw.has_labels` but BOTH branches call prepared_scorer(self,Xp) -> shares spec AND VERIFIES (18.3s). This is a behavioral echo of gold (both branches identical to gold's single _score_samples path).

MANDATORY RESOLVE ON CANDIDATE: atk11_partial is the only verifying candidate. Materialized its faithful refined patch (gold patch with the single offset assignment replaced by the equivalent if/else, both branches np.percentile(self._score_samples(X),...)). Ran official harness via swebench_unified.harness.run_resolve(instance, patch, timeout=1800, retries=1) under `docker`. RESULT: RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False. => atk11 is NOT a counterexample (verify => correct holds for it). Saved atk11_resolve.json.

refinement.md AUDIT: every leg is R / A-consumed / A-reference / I; no kind-3. A-legs: mismatch_advisory (A-reference) == real BaseEstimator._check_feature_names(reset=False) over all 4 label combos; prepare (A-reference deep fact has_labels==False + consumed prepared_input provenance) == _validate_data(reset=True); prepared_scorer (consumed axiom) == introduced _score_samples (no validation, produces scores); three provenance tokens (raw_fit_input, prepared_input, offset_from_unvalidated_scoring) unforgeable @Predicate with single granters. axiom_check.py executably checks all these correspondences against real sklearn callees, gated on hasattr(IsolationForest,'_score_samples') so returns 0 both pre/gold. The token chain + biconditional offset_set==calibration_requested + fit_advisories==0 jointly force any verifying impl to gold behaviour; every distinct wrong impl class (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, foreign/fabricated matrix) is rejected on the exact clause claimed in refinement.md's adversarial-closure table.

VERDICT: SOUND. 11 distinct same-spec wrong impls run through the Nagini verifier; 10 rejected on the precise discriminating clause; the single verifying candidate (atk11, a structural echo of gold) had its materialized faithful patch RESOLVE under the official harness. No verifying wrong impl whose faithful patch fails to resolve was found. Prepatch reproduced; positive control verifies.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: checked whether any modeled function/contract over-claims (drifts stronger than) the real scikit-learn callee at base_commit e3d1f9ac (gold-applied for the patch-introduced routine). Ran the bundle's axiom_check.py against the real sklearn 1.3.0 IsolationForest/_iforest.py + BaseEstimator: exit 0. Independently re-verified each modeled callee:

1. mismatch_advisory(arg,fitted) == real BaseEstimator._check_feature_names(X, reset=False) advisory count over ALL 4 (arg_has_labels,fitted_with_labels) combinations: {F,F}->0, {F,T(arg labelled)}->0, {T(fitted),F(arg)}->1, {T,T}->0. Model matches on every input; notably the fitted-without/arg-with case (real emits a DIFFERENT message) is correctly scored 0.
2. prepare == _validate_data(reset=True): output carries no feature names for both labelled and unlabelled input, so Ensures(Result().has_labels==False) is sound (not an over-claim).
3. prepared_scorer == _score_samples: fed an unlabelled array after a labelled fit, emits 0 label-mismatch advisories AND returns one score per row -> Ensures(fit_advisories unchanged) + offset-furnishing are sound.
4. Gold fit emits 0 advisories across all 4 (labelled x contamination) cases and sets offset_ iff contamination != 'auto' -> fit_offset postconditions fit_advisories==0 and offset_set==calibration_requested match reality.
5. Public score_samples still validates (exactly 1 advisory) -> validating_scorer faithful.

The precondition narrowing on prepared_scorer (has_labels==False, prepared_input(X)) is soundness-safe: narrowing a callee precondition can only make the proof harder, never mask a wrong impl. check_offset_derives_from_prepared_training_input confirms the offset is grounded in the actual prepared training data and differs from a foreign array, so the provenance tokens are load-bearing and faithful, not an artificial over-strengthening. Spec regions were exercised as-is (no spec edits). No input found where a modeled function disagrees with the real repo. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec confirmed frozen: same-spec exit 0 on the bundle's own model.py (spec_view hash 05f11bfb… matches meta.json). Reviewed the solver-visible spec view (docstring + spec/pre/post/pure regions).

Public problem_statement already discloses: the 'X does not have valid feature names, but IsolationForest was fitted with feature names' warning fires during fit(), ONLY when contamination != 'auto', because the estimator 'essentially calls predict on the training data in order to determine the offset_ parameters' (exact source line linked); expected behavior = fit does not raise it. The gold recipe (add private _score_samples w/o validation; score_samples validates then delegates; call _score_samples at end of fit) lives ONLY in hints_text, which is out of scope for leakage.

Spec-view findings: (1) all identifiers abstract — prepared_scorer / validating_scorer / fit_offset / prepare / has_labels / fit_advisories / offset_set / calibration_requested; NONE of the patched repo symbols (_score_samples, score_samples, _validate_data, _compute_chunked_score_samples) appear. (2) No contamination / offset_ / percentile / IsolationForest, no path sklearn/ensemble/_iforest.py, no diff markers or fix/bug narration. (3) The behavioral contract (fitting derives the calibration offset from per-row scores of the already-prepared/unlabelled matrix WITHOUT a label-consistency check, emitting no mismatch advisory) is a formalization of the PUBLIC root-cause + expected result, not an edit-localizer: it does not reveal that a new private method is introduced, that validation is skipped there, or which method to call — that is derivable from the public diagnosis. (4) respec_history (2026-06-16) explicitly de-narrated the docstring to strip the hints-only 'two scoring entry points / one without a preparation pass' fix-recipe vocabulary; current text carries none.

Mechanical G-LEAK screen passes (recorded G-LEAK pass, failures=[]); bundle is not relaxed (no RELAXED_LEAKAGE.md). refinement.md/mapping.md gold-narration is bundle-internal, not part of the spec view. No spec-view line leaks the gold edit beyond problem_statement. Concur with recorded G-PANEL-3 pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
