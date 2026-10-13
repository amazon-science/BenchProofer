# P2 adversarial audit — scikit-learn__scikit-learn-10297

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EngineConfig:
@@ -36,7 +35,6 @@
     def __init__(self, retain_values: bool) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.retain_values))  # type: ignore
@@ -55,7 +53,6 @@
                  n_alphas: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
@@ -86,7 +83,6 @@
 def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(12))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().retain_values))
@@ -95,7 +91,7 @@
     Ensures(Result().retain_values == store_cv_values)
     # post-conditions-end
     # impl-start
-    cfg = EngineConfig(store_cv_values)
+    cfg = EngineConfig(False)
     return cfg
     # impl-end
 
@@ -105,7 +101,6 @@
     # pre-conditions-start
     Requires(Acc(cfg.retain_values, 1 / 2))
     Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(cfg.retain_values, 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EngineConfig:
@@ -36,7 +35,6 @@
     def __init__(self, retain_values: bool) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.retain_values))  # type: ignore
@@ -55,7 +53,6 @@
                  n_alphas: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
@@ -86,7 +83,6 @@
 def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(12))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().retain_values))
@@ -105,7 +101,6 @@
     # pre-conditions-start
     Requires(Acc(cfg.retain_values, 1 / 2))
     Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(cfg.retain_values, 1 / 2))
@@ -123,7 +118,9 @@
     # post-conditions-end
     # impl-start
     if cfg.retain_values:
-        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
+        # buggy: flattened two-dimensional (samples, penalties) form with no
+        # target axis (rank 2) rather than the always-three-dimensional record
+        record = CvRecord(2, n_samples, n_alphas, n_alphas)  # type: Optional[CvRecord]
         return record
     return None
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EngineConfig:
@@ -36,7 +35,6 @@
     def __init__(self, retain_values: bool) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.retain_values))  # type: ignore
@@ -55,7 +53,6 @@
                  n_alphas: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
@@ -86,7 +83,6 @@
 def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(12))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().retain_values))
@@ -105,7 +101,6 @@
     # pre-conditions-start
     Requires(Acc(cfg.retain_values, 1 / 2))
     Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(cfg.retain_values, 1 / 2))
@@ -123,7 +118,7 @@
     # post-conditions-end
     # impl-start
     if cfg.retain_values:
-        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
+        record = CvRecord(3, n_samples, n_alphas, n_targets)  # type: Optional[CvRecord]
         return record
     return None
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EngineConfig:
@@ -36,7 +35,6 @@
     def __init__(self, retain_values: bool) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.retain_values))  # type: ignore
@@ -55,7 +53,6 @@
                  n_alphas: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
@@ -86,7 +83,6 @@
 def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(12))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().retain_values))
@@ -105,7 +101,6 @@
     # pre-conditions-start
     Requires(Acc(cfg.retain_values, 1 / 2))
     Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(cfg.retain_values, 1 / 2))
@@ -122,7 +117,7 @@
     Ensures(Implies(Result() is not None, Result().n_alphas == n_alphas))
     # post-conditions-end
     # impl-start
-    if cfg.retain_values:
+    if cfg.retain_values and n_targets > 1:
         record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
         return record
     return None
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EngineConfig:
@@ -36,7 +35,6 @@
     def __init__(self, retain_values: bool) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.retain_values))  # type: ignore
@@ -55,7 +53,6 @@
                  n_alphas: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
@@ -86,7 +83,6 @@
 def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(12))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().retain_values))
@@ -95,7 +91,7 @@
     Ensures(Result().retain_values == store_cv_values)
     # post-conditions-end
     # impl-start
-    cfg = EngineConfig(store_cv_values)
+    cfg = EngineConfig(not store_cv_values)
     return cfg
     # impl-end
 
@@ -105,7 +101,6 @@
     # pre-conditions-start
     Requires(Acc(cfg.retain_values, 1 / 2))
     Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(cfg.retain_values, 1 / 2))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EngineConfig:
@@ -36,7 +35,6 @@
     def __init__(self, retain_values: bool) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.retain_values))  # type: ignore
@@ -55,7 +53,6 @@
                  n_alphas: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
@@ -86,7 +83,6 @@
 def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(12))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().retain_values))
@@ -105,7 +101,6 @@
     # pre-conditions-start
     Requires(Acc(cfg.retain_values, 1 / 2))
     Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(cfg.retain_values, 1 / 2))
@@ -123,7 +118,7 @@
     # post-conditions-end
     # impl-start
     if cfg.retain_values:
-        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
+        record = CvRecord(2, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
         return record
     return None
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EngineConfig:
@@ -36,7 +35,6 @@
     def __init__(self, retain_values: bool) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.retain_values))  # type: ignore
@@ -55,7 +53,6 @@
                  n_alphas: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
@@ -86,7 +83,6 @@
 def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(12))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().retain_values))
@@ -105,7 +101,6 @@
     # pre-conditions-start
     Requires(Acc(cfg.retain_values, 1 / 2))
     Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(cfg.retain_values, 1 / 2))
@@ -123,7 +118,7 @@
     # post-conditions-end
     # impl-start
     if cfg.retain_values:
-        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
+        record = CvRecord(3, n_alphas, n_targets, n_samples)  # type: Optional[CvRecord]
         return record
     return None
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class EngineConfig:
@@ -36,7 +35,6 @@
     def __init__(self, retain_values: bool) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.retain_values))  # type: ignore
@@ -55,7 +53,6 @@
                  n_alphas: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
@@ -86,7 +83,6 @@
 def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(12))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().retain_values))
@@ -105,7 +101,6 @@
     # pre-conditions-start
     Requires(Acc(cfg.retain_values, 1 / 2))
     Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(cfg.retain_values, 1 / 2))
@@ -122,8 +117,6 @@
     Ensures(Implies(Result() is not None, Result().n_alphas == n_alphas))
     # post-conditions-end
     # impl-start
-    if cfg.retain_values:
-        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
-        return record
-    return None
+    record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
+    return record
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-10297.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cross-validated ridge classifier exposes an optional flag requesting that
  the per-alpha cross-validation values be retained after fitting. Two things
  must hold:

    (1) The flag supplied when the classifier is configured is honoured: the
        retention setting the caller requested is the retention setting used
        when fitting.

    (2) When retention is requested, the classifier produces a
        three-dimensional record of cross-validation values whose axes are, in
        order, the number of samples, the number of targets (n_targets >= 1),
        and the number of candidate penalty strengths. It is never the
        flattened two-dimensional (samples, penalties) form.

The configuration the classifier hands to its engine is modelled as a small
object carrying only the touched field (the retention flag). The retained
record is modelled as a small object carrying its axis count and the three
axis lengths.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *

class EngineConfig:
    """The configuration handed to the underlying cross-validation engine.
    Only the touched field is modelled: whether the per-alpha values are
    retained."""

    def __init__(self, retain_values: bool) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.retain_values))  # type: ignore
        Ensures(self.retain_values == retain_values)  # type: ignore
        # post-conditions-end
        # impl-start
        self.retain_values = retain_values  # type: bool
        # impl-end

class CvRecord:
    """The retained cross-validation values record. Modelled by its axis count
    and the three axis lengths (samples, targets, penalties)."""

    def __init__(self, rank: int, n_samples: int, n_targets: int,
                 n_alphas: int) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
                and Acc(self.n_targets) and Acc(self.n_alphas))  # type: ignore
        Ensures(self.rank == rank)  # type: ignore
        Ensures(self.n_samples == n_samples)  # type: ignore
        Ensures(self.n_targets == n_targets)  # type: ignore
        Ensures(self.n_alphas == n_alphas)  # type: ignore
        # post-conditions-end
        # impl-start
        self.rank = rank            # type: int
        self.n_samples = n_samples  # type: int
        self.n_targets = n_targets  # type: int
        self.n_alphas = n_alphas    # type: int
        # impl-end

# axioms-start
# (no unchanged-callee axioms are required for this behaviour)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().retain_values))
    # (1) The retention flag the caller requested is forwarded unchanged to the
    # engine configuration: the engine retains values iff the caller asked it to.
    Ensures(Result().retain_values == store_cv_values)
    # post-conditions-end
    # impl-start
    cfg = EngineConfig(store_cv_values)
    return cfg
    # impl-end

def stored_cv_values(cfg: EngineConfig, n_samples: int, n_targets: int,
                     n_alphas: int) -> Optional[CvRecord]:
    # pre-conditions-start
    Requires(Acc(cfg.retain_values, 1 / 2))
    Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(cfg.retain_values, 1 / 2))
    # A record is retained exactly when the engine is configured to retain.
    Ensures((Result() is not None) == cfg.retain_values)
    # (2) When retained, the record is three-dimensional with axes
    # (samples, targets, penalties) -- the target axis is always present.
    Ensures(Implies(Result() is not None,
                    Acc(Result().rank) and Acc(Result().n_samples)
                    and Acc(Result().n_targets) and Acc(Result().n_alphas)))
    Ensures(Implies(Result() is not None, Result().rank == 3))
    Ensures(Implies(Result() is not None, Result().n_samples == n_samples))
    Ensures(Implies(Result() is not None, Result().n_targets == n_targets))
    Ensures(Implies(Result() is not None, Result().n_alphas == n_alphas))
    # post-conditions-end
    # impl-start
    if cfg.retain_values:
        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
        return record
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn__scikit-learn-10297, nagini backend.

SPEC SHAPE: two-leg complete functional spec, both legs pinning outputs by equality, leaving essentially no slack for a verifying-but-wrong impl:
  * configure_classifier_cv: Ensures(Result().retain_values == store_cv_values) -- forwards the flag exactly.
  * stored_cv_values: Ensures((Result() is not None) == cfg.retain_values); Result().rank==3; Result().n_samples==n_samples; Result().n_targets==n_targets; Result().n_alphas==n_alphas -- pins retention guard AND all three axis lengths AND rank exactly.

REFINEMENT.md AUDIT (A-leg focus): The '# axioms-start/end' and '# pure-start/end' regions are GENUINELY EMPTY (verified in model.py lines 73-80). refinement.md §C and mapping.md §3 correctly state: no @ContractOnly axioms, no A-reference deep model of an unchanged callee, G-AX vacuous, no kind-3 (unexpressible-changed-op) steps. Every leg is R or I: A1=R (bool ↔ store_cv_values kwarg), A2=R+I (EngineConfig(store_cv_values)/return ↔ super().__init__(..., store_cv_values=store_cv_values) storing self.store_cv_values in _BaseRidgeCV.__init__, ridge.py:1098); B1=I (retention guard `if self.store_cv_values`), B2=R (CvRecord(3,n_samples,n_targets,n_alphas) ↔ cv_values_.reshape((n_samples,n_y,len(alphas))) 3-D else-branch, always taken because RidgeClassifierCV label-binarizes y to a 2-D Y). No A-reference correspondence to audit because there are no A-legs; axiom_check.py is a REFERENCE WITNESS (imports real post-patch sklearn.linear_model.RidgeClassifierCV, asserts (1) flag forwarded and (2) cv_values_ rank-3 (n_samples,n_targets,n_alphas) on F2P boundary + 200 fuzz fits), not a proof-trusted axiom -- so there is no axiom-soundness trust point. Correspondence to real callees holds.

### Machine-checked results
  same-spec (python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-10297 <atk>): ALL 8 attacks exit 0 = SAME (spec byte-identical; only impl region differs).
  positive control (adversary verify ... pos_control.py, exact model.py copy): VERIFIED in 12.2s (exit 0).
  weakness (adversary weakness ... <atk>): ALL 8 attacks exit 2 = NOT-A-COUNTEREXAMPLE 'attack does not verify (verification failed) -- the spec rejected this impl'. NO CANDIDATE emerged. Attacks run concurrently as background jobs, ≤3 JVM+Z3 at a time (batch1: pos+atk1+atk2; batch2: atk3,4,5; batch3: atk6,7,8).

### ATTACK ROSTER (all same-spec wrong impls, each targeting a distinct postcondition clause):
atk_1 = leg-A prepatch bug: EngineConfig(False) -- BYTE-IDENTICAL to bundle model_prepatch.py (diff confirms). FAILS verify (cannot prove False==store_cv_values). PREPATCH REPRODUCED. atk_2 = leg-B prepatch bug: CvRecord(2, n_samples, n_alphas, n_alphas) flattened 2-D form -- BYTE-IDENTICAL to bundle model_prepatch_2.py (diff confirms). FAILS verify (rank!=3). PREPATCH REPRODUCED. atk_3 = boundary/axis-swap: CvRecord(3, n_samples, n_alphas, n_targets) swaps target/penalty axes. FAILS verify. atk_4 = partial-domain: return record only when cfg.retain_values AND n_targets>1, else None -- drops binary (n_targets==1) case. FAILS verify ((Result() is not None)==cfg.retain_values violated). atk_5 = control-flow-effect (leg A): EngineConfig(not store_cv_values) forwards negated flag.

FAILS verify. atk_6 = wrong-rank: CvRecord(2, n_samples, n_targets, n_alphas) correct axis lengths but rank literal 2. FAILS verify (rank!=3). atk_7 = boundary: CvRecord(3, n_alphas, n_targets, n_samples) mislabels the samples axis. FAILS verify. atk_8 = ungrounded-oracle echo: drops the `if cfg.retain_values` guard, always returns a record. FAILS verify ((Result() is not None)==cfg.retain_values violated when retention off).

CONCLUSION: Both prepatch bugs reproduced (verify-fail), positive control verifies, and 6 further distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) all FAIL verification. The spec is a complete functional specification with equality postconditions on every observable, admits no verifying-but-wrong impl, and refinement.md has no A-legs/kind-3 to falsify. No CANDIDATE => no faithful patch to materialize/resolve. verify⇒correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-10297.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cross-validated ridge classifier exposes an optional flag requesting that
  the per-alpha cross-validation values be retained after fitting. Two things
  must hold:

    (1) The flag supplied when the classifier is configured is honoured: the
        retention setting the caller requested is the retention setting used
        when fitting.

    (2) When retention is requested, the classifier produces a
        three-dimensional record of cross-validation values whose axes are, in
        order, the number of samples, the number of targets (n_targets >= 1),
        and the number of candidate penalty strengths. It is never the
        flattened two-dimensional (samples, penalties) form.

The configuration the classifier hands to its engine is modelled as a small
object carrying only the touched field (the retention flag). The retained
record is modelled as a small object carrying its axis count and the three
axis lengths.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *

class EngineConfig:
    """The configuration handed to the underlying cross-validation engine.
    Only the touched field is modelled: whether the per-alpha values are
    retained."""

    def __init__(self, retain_values: bool) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.retain_values))  # type: ignore
        Ensures(self.retain_values == retain_values)  # type: ignore
        # post-conditions-end
        # impl-start
        self.retain_values = retain_values  # type: bool
        # impl-end

class CvRecord:
    """The retained cross-validation values record. Modelled by its axis count
    and the three axis lengths (samples, targets, penalties)."""

    def __init__(self, rank: int, n_samples: int, n_targets: int,
                 n_alphas: int) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.rank) and Acc(self.n_samples)  # type: ignore
                and Acc(self.n_targets) and Acc(self.n_alphas))  # type: ignore
        Ensures(self.rank == rank)  # type: ignore
        Ensures(self.n_samples == n_samples)  # type: ignore
        Ensures(self.n_targets == n_targets)  # type: ignore
        Ensures(self.n_alphas == n_alphas)  # type: ignore
        # post-conditions-end
        # impl-start
        self.rank = rank            # type: int
        self.n_samples = n_samples  # type: int
        self.n_targets = n_targets  # type: int
        self.n_alphas = n_alphas    # type: int
        # impl-end

# axioms-start
# (no unchanged-callee axioms are required for this behaviour)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def configure_classifier_cv(store_cv_values: bool) -> EngineConfig:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().retain_values))
    # (1) The retention flag the caller requested is forwarded unchanged to the
    # engine configuration: the engine retains values iff the caller asked it to.
    Ensures(Result().retain_values == store_cv_values)
    # post-conditions-end
    # impl-start
    cfg = EngineConfig(store_cv_values)
    return cfg
    # impl-end

def stored_cv_values(cfg: EngineConfig, n_samples: int, n_targets: int,
                     n_alphas: int) -> Optional[CvRecord]:
    # pre-conditions-start
    Requires(Acc(cfg.retain_values, 1 / 2))
    Requires(n_samples >= 0 and n_targets >= 1 and n_alphas >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(cfg.retain_values, 1 / 2))
    # A record is retained exactly when the engine is configured to retain.
    Ensures((Result() is not None) == cfg.retain_values)
    # (2) When retained, the record is three-dimensional with axes
    # (samples, targets, penalties) -- the target axis is always present.
    Ensures(Implies(Result() is not None,
                    Acc(Result().rank) and Acc(Result().n_samples)
                    and Acc(Result().n_targets) and Acc(Result().n_alphas)))
    Ensures(Implies(Result() is not None, Result().rank == 3))
    Ensures(Implies(Result() is not None, Result().n_samples == n_samples))
    Ensures(Implies(Result() is not None, Result().n_targets == n_targets))
    Ensures(Implies(Result() is not None, Result().n_alphas == n_alphas))
    # post-conditions-end
    # impl-start
    if cfg.retain_values:
        record = CvRecord(3, n_samples, n_targets, n_alphas)  # type: Optional[CvRecord]
        return record
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Instance scikit-learn__scikit-learn-10297, nagini backend.

SPEC SHAPE: two-leg complete functional spec, both legs pinning outputs by equality, leaving essentially no slack for a verifying-but-wrong impl:
  * configure_classifier_cv: Ensures(Result().retain_values == store_cv_values) -- forwards the flag exactly.
  * stored_cv_values: Ensures((Result() is not None) == cfg.retain_values); Result().rank==3; Result().n_samples==n_samples; Result().n_targets==n_targets; Result().n_alphas==n_alphas -- pins retention guard AND all three axis lengths AND rank exactly.

REFINEMENT.md AUDIT (A-leg focus): The '# axioms-start/end' and '# pure-start/end' regions are GENUINELY EMPTY (verified in model.py lines 73-80). refinement.md §C and mapping.md §3 correctly state: no @ContractOnly axioms, no A-reference deep model of an unchanged callee, G-AX vacuous, no kind-3 (unexpressible-changed-op) steps. Every leg is R or I: A1=R (bool ↔ store_cv_values kwarg), A2=R+I (EngineConfig(store_cv_values)/return ↔ super().__init__(..., store_cv_values=store_cv_values) storing self.store_cv_values in _BaseRidgeCV.__init__, ridge.py:1098); B1=I (retention guard `if self.store_cv_values`), B2=R (CvRecord(3,n_samples,n_targets,n_alphas) ↔ cv_values_.reshape((n_samples,n_y,len(alphas))) 3-D else-branch, always taken because RidgeClassifierCV label-binarizes y to a 2-D Y). No A-reference correspondence to audit because there are no A-legs; axiom_check.py is a REFERENCE WITNESS (imports real post-patch sklearn.linear_model.RidgeClassifierCV, asserts (1) flag forwarded and (2) cv_values_ rank-3 (n_samples,n_targets,n_alphas) on F2P boundary + 200 fuzz fits), not a proof-trusted axiom -- so there is no axiom-soundness trust point. Correspondence to real callees holds.

### Machine-checked results
  same-spec (python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-10297 <atk>): ALL 8 attacks exit 0 = SAME (spec byte-identical; only impl region differs).
  positive control (adversary verify ... pos_control.py, exact model.py copy): VERIFIED in 12.2s (exit 0).
  weakness (adversary weakness ... <atk>): ALL 8 attacks exit 2 = NOT-A-COUNTEREXAMPLE 'attack does not verify (verification failed) -- the spec rejected this impl'. NO CANDIDATE emerged. Attacks run concurrently as background jobs, ≤3 JVM+Z3 at a time (batch1: pos+atk1+atk2; batch2: atk3,4,5; batch3: atk6,7,8).

### ATTACK ROSTER (all same-spec wrong impls, each targeting a distinct postcondition clause):
atk_1 = leg-A prepatch bug: EngineConfig(False) -- BYTE-IDENTICAL to bundle model_prepatch.py (diff confirms). FAILS verify (cannot prove False==store_cv_values). PREPATCH REPRODUCED. atk_2 = leg-B prepatch bug: CvRecord(2, n_samples, n_alphas, n_alphas) flattened 2-D form -- BYTE-IDENTICAL to bundle model_prepatch_2.py (diff confirms). FAILS verify (rank!=3). PREPATCH REPRODUCED. atk_3 = boundary/axis-swap: CvRecord(3, n_samples, n_alphas, n_targets) swaps target/penalty axes. FAILS verify. atk_4 = partial-domain: return record only when cfg.retain_values AND n_targets>1, else None -- drops binary (n_targets==1) case. FAILS verify ((Result() is not None)==cfg.retain_values violated). atk_5 = control-flow-effect (leg A): EngineConfig(not store_cv_values) forwards negated flag.

FAILS verify. atk_6 = wrong-rank: CvRecord(2, n_samples, n_targets, n_alphas) correct axis lengths but rank literal 2. FAILS verify (rank!=3). atk_7 = boundary: CvRecord(3, n_alphas, n_targets, n_samples) mislabels the samples axis. FAILS verify. atk_8 = ungrounded-oracle echo: drops the `if cfg.retain_values` guard, always returns a record. FAILS verify ((Result() is not None)==cfg.retain_values violated when retention off).

CONCLUSION: Both prepatch bugs reproduced (verify-fail), positive control verifies, and 6 further distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) all FAIL verification. The spec is a complete functional specification with equality postconditions on every observable, admits no verifying-but-wrong impl, and refinement.md has no A-legs/kind-3 to falsify. No CANDIDATE => no faithful patch to materialize/resolve. verify⇒correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical with the bundle (same-spec toolkit: SAME, exit 0). Empirically validated both modeled behaviours against the real sklearn.linear_model.RidgeClassifierCV (patched repo behaviour; the reshape branch and __init__ forwarding are the exact code the model models per mapping.md/refinement.md).

(1) configure_classifier_cv — Ensures(Result().retain_values == store_cv_values): RidgeClassifierCV(store_cv_values=flag).store_cv_values == flag for both booleans and varied orthogonal kwargs (fit_intercept/normalize/alphas). Exact identity, no drift; retention-off => no cv_values_ attribute (<-> None) confirmed.

(2) stored_cv_values — Ensures rank==3 with axes (n_samples, n_targets, n_alphas) whenever retained, where n_targets = column count of the LabelBinarizer(pos_label=1,neg_label=-1) target matrix. The classifier always binarizes y to a 2-D matrix, so _RidgeGCV.fit always takes the else-branch (n_samples, n_y, len(alphas)). Verified: binary->(5,1,3); 3-class->(5,3,3); multilabel-3col->(8,3,3); multilabel-1col->(8,1,3); single-class->(5,1,3) with model n_targets=1; single-alpha->(5,1,1). Every case matches the spec exactly (rank==3, per-axis identity, retention iff flag). No in-domain input found where the modeled return contradicts the real return.

MODELING BOUNDARIES (examined, not defects): the precondition admits n_samples>=0 and n_alphas>=0, but the real fit RAISES on degenerate extents (n_samples=0 ValueError; empty alphas AttributeError). A raise is not a differing RETURN the postconditions assert about, and these extents are outside the modeled/conformance operating domain (n_samples>=5, n_alphas>=1 — the F2P/gold-patch domain where model and repo agree). The cv!=None path (raises ValueError in-repo) is un-modeled and out of scope. These are legitimate modeling boundaries, NOT spec-too-strong drift.

Orthogonal note: the separately-recorded G-PANEL-1 fail concerns spec-too-WEAK (missing MustTerminate) — not a faithfulness/strong-side issue and outside this role. Conclusion: no diverging input exists within the modeled domain; the spec does not over-constrain relative to the real repo. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK returns pass (verified live: leakage.screen -> passed=True, no hard failures); no relaxation flag (relaxed_leakage=None, no RELAXED_LEAKAGE.md). I re-derived the spec view with markers.spec_view and checked it against the frozen row's problem_statement (NOT hints_text).

Gold edit: add store_cv_values=False kwarg to RidgeClassifierCV.__init__, forward it via super().__init__(..., store_cv_values=store_cv_values), and docstring change stating the classifier's cv_values_ shape is [n_samples, n_targets, n_alphas] (dropping the 2-D form).

The spec view discloses nothing about the edit's LOCATION or CONTENT beyond the public task:
- Patched file path 'sklearn/linear_model/ridge.py', patched symbols {RidgeClassifierCV, RidgeCV}, the super().__init__ forwarding, and every gold-diff line are ABSENT. The view uses invented abstract carriers: EngineConfig, CvRecord, configure_classifier_cv, stored_cv_values, retain_values, rank, n_targets, n_alphas. No diff markers, no patched module path, no bug/fix narration.
- The only overlapping tokens are already public in problem_statement: 'store_cv_values' (the repro uses store_cv_values=True and the task explicitly asks to 'Add store_cv_values boolean flag support to RidgeClassifierCV'), and the axis vocabulary n_samples/n_targets/n_alphas (the quoted docstring in the task gives 'shape = [n_samples, n_alphas] or shape = [n_samples, n_responses, n_alphas]').
- The spec's claim that when retention is on the record is always rank-3 (never the flattened 2-D form) is a statement of DESIRED behaviour derivable from the public docstring, not disclosure of where/how the code is edited. That is a correctness spec, which is exactly its purpose; it is not gold-edit leakage.

No spec-view line localizes the gold edit beyond what problem_statement already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).