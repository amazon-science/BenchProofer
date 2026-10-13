# P2 adversarial audit — scikit-learn__scikit-learn-12682

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec verifying impl was found whose faithful refined patch produces a completed non-resolving harness run (verify⇏correct). The spec's total equality postconditions pin the returned iteration budget exactly on the whole precondition domain, so every value/data-flow-wrong impl is rejected by the verifier. The only same-spec impls that verify are non-terminating ones (partial-correctness vacuity), whose faithful patches HANG the F2P test → the official harness returns completed=False (INCONCLUSIVE), never completed∧¬resolved (BROKEN). Non-termination is a universal Nagini partial-correctness artifact (~405/500 green nagini cells lack MustTerminate and pass G-EQ), not a spec-specific weakness, and it structurally cannot flip the runner's derivation to BROKEN.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The constructed iterative-lasso solver receives EXACTLY the budget handed
@@ -83,9 +81,7 @@
     Ensures(Result() == max_iter)
     # post-conditions-end
     # impl-start
-    # Whichever iterative-lasso solver is built, it is constructed with the
-    # supplied budget -- the budget reaches the solver unchanged.
-    budget = max_iter
+    budget = max_iter + 1
     return budget
     # impl-end
 
@@ -94,7 +90,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The generic coder forwards its budget, unchanged, to the solver builder.
@@ -119,7 +114,6 @@
     Requires(Acc(self.configured_max_iter, 1 / 2))
     Requires(self.configured_max_iter >= 1)
     Requires(is_iterative_lasso(algorithm))
-    Requires(MustTerminate(4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured_max_iter, 1 / 2))
```

Attack 2 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The constructed iterative-lasso solver receives EXACTLY the budget handed
@@ -83,9 +81,10 @@
     Ensures(Result() == max_iter)
     # post-conditions-end
     # impl-start
-    # Whichever iterative-lasso solver is built, it is constructed with the
-    # supplied budget -- the budget reaches the solver unchanged.
-    budget = max_iter
+    if algorithm == 0:
+        budget = lars_builtin_default()
+    else:
+        budget = max_iter
     return budget
     # impl-end
 
@@ -94,7 +93,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The generic coder forwards its budget, unchanged, to the solver builder.
@@ -119,7 +117,6 @@
     Requires(Acc(self.configured_max_iter, 1 / 2))
     Requires(self.configured_max_iter >= 1)
     Requires(is_iterative_lasso(algorithm))
-    Requires(MustTerminate(4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured_max_iter, 1 / 2))
```

Attack 3 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The constructed iterative-lasso solver receives EXACTLY the budget handed
@@ -83,9 +81,7 @@
     Ensures(Result() == max_iter)
     # post-conditions-end
     # impl-start
-    # Whichever iterative-lasso solver is built, it is constructed with the
-    # supplied budget -- the budget reaches the solver unchanged.
-    budget = max_iter
+    budget = coder_param_default()
     return budget
     # impl-end
 
@@ -94,7 +90,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The generic coder forwards its budget, unchanged, to the solver builder.
@@ -119,7 +114,6 @@
     Requires(Acc(self.configured_max_iter, 1 / 2))
     Requires(self.configured_max_iter >= 1)
     Requires(is_iterative_lasso(algorithm))
-    Requires(MustTerminate(4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured_max_iter, 1 / 2))
```

Attack 4 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The constructed iterative-lasso solver receives EXACTLY the budget handed
@@ -94,7 +92,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The generic coder forwards its budget, unchanged, to the solver builder.
@@ -119,7 +116,6 @@
     Requires(Acc(self.configured_max_iter, 1 / 2))
     Requires(self.configured_max_iter >= 1)
     Requires(is_iterative_lasso(algorithm))
-    Requires(MustTerminate(4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured_max_iter, 1 / 2))
@@ -129,5 +125,7 @@
     # post-conditions-end
     # impl-start
     budget = coder_solver_budget(algorithm, self.configured_max_iter)
+    while budget > 0:
+        Invariant(budget == self.configured_max_iter)
     return budget
     # impl-end
```

Attack 5 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The constructed iterative-lasso solver receives EXACTLY the budget handed
@@ -94,7 +92,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The generic coder forwards its budget, unchanged, to the solver builder.
@@ -119,7 +116,6 @@
     Requires(Acc(self.configured_max_iter, 1 / 2))
     Requires(self.configured_max_iter >= 1)
     Requires(is_iterative_lasso(algorithm))
-    Requires(MustTerminate(4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured_max_iter, 1 / 2))
@@ -128,6 +124,6 @@
     Ensures(Result() == self.configured_max_iter)
     # post-conditions-end
     # impl-start
-    budget = coder_solver_budget(algorithm, self.configured_max_iter)
+    budget = self.configured_max_iter + 1
     return budget
     # impl-end
```

Attack 6 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The constructed iterative-lasso solver receives EXACTLY the budget handed
@@ -94,14 +92,13 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The generic coder forwards its budget, unchanged, to the solver builder.
     Ensures(Result() == max_iter)
     # post-conditions-end
     # impl-start
-    return encode_iteration_budget(algorithm, max_iter)
+    return coder_param_default()
     # impl-end
 
 
@@ -119,7 +116,6 @@
     Requires(Acc(self.configured_max_iter, 1 / 2))
     Requires(self.configured_max_iter >= 1)
     Requires(is_iterative_lasso(algorithm))
-    Requires(MustTerminate(4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured_max_iter, 1 / 2))
```

Attack 7 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The constructed iterative-lasso solver receives EXACTLY the budget handed
@@ -94,7 +92,6 @@
     # pre-conditions-start
     Requires(is_iterative_lasso(algorithm))
     Requires(max_iter >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # The generic coder forwards its budget, unchanged, to the solver builder.
@@ -119,7 +116,6 @@
     Requires(Acc(self.configured_max_iter, 1 / 2))
     Requires(self.configured_max_iter >= 1)
     Requires(is_iterative_lasso(algorithm))
-    Requires(MustTerminate(4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured_max_iter, 1 / 2))
@@ -128,6 +124,9 @@
     Ensures(Result() == self.configured_max_iter)
     # post-conditions-end
     # impl-start
-    budget = coder_solver_budget(algorithm, self.configured_max_iter)
+    if algorithm == 0:
+        budget = coder_solver_budget(algorithm, self.configured_max_iter)
+    else:
+        budget = coder_param_default()
     return budget
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-12682.

Behaviour under specification (the desired behaviour, stated abstractly):

  A sparse-coding estimator exposes a user-controlled iteration budget. When
  the estimator encodes data with an iterative least-squares solver (either of
  the two coordinate-descent / least-angle lasso solvers), the solver is
  constructed with EXACTLY the iteration budget the user configured on the
  estimator. The budget the user supplies must propagate, unchanged, through
  the layered coding routines all the way to the solver that is built; it is
  never replaced by a constant library default at any layer.

  Concretely:
    (1) The generic single-block coder, when it builds either iterative lasso
        solver, gives that solver the iteration budget it was handed (never the
        solver class's own built-in default).
    (2) The estimator's encoding path hands the generic coder the iteration
        budget stored on the estimator (the value the user configured), rather
        than the coder routine's own parameter default.

  The end-to-end guarantee: for the iterative-lasso algorithms, the iteration
  budget the constructed solver receives equals the budget configured on the
  estimator, for ANY configured value.

This behaviour is pure parameter propagation: integer-valued and
precision-independent, so iteration budgets and the algorithm selector are
modelled as plain `int` (no floating-point semantics are involved). The
estimator is modelled as a minimal object carrying only the single relevant
field.

The two independently-specified behaviours each have their own contracted
function so each is differentially observable on its own.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none) The changed operation is integer parameter propagation, fully
# expressible; no library callee's behaviour is relied upon, so there is no
# @ContractOnly axiom. The solver constructor's only modelled effect is to
# record the iteration budget it is given, which is the identity on that int.
# axioms-end

# pure-start
@Pure
def is_iterative_lasso(algorithm: int) -> bool:
    """Whether the chosen coding algorithm builds an iterative least-squares
    lasso solver (the two algorithms whose iteration budget is meaningful).
    Selector encoding: 0 = least-angle lasso, 1 = coordinate-descent lasso,
    2 = least-angle, 3 = orthogonal matching pursuit, 4 = thresholding."""
    return algorithm == 0 or algorithm == 1

@Pure
def lars_builtin_default() -> int:
    """The least-angle solver class's own built-in iteration default (the value
    silently used when the budget is not threaded into its constructor)."""
    return 500

@Pure
def coder_param_default() -> int:
    """The generic coder routine's own iteration-budget parameter default (the
    value silently used when the encoding path does not forward the budget)."""
    return 1000
# pure-end

def encode_iteration_budget(algorithm: int, max_iter: int) -> int:
    # pre-conditions-start
    Requires(is_iterative_lasso(algorithm))
    Requires(max_iter >= 1)
    # pre-conditions-end
    # post-conditions-start
    # The constructed iterative-lasso solver receives EXACTLY the budget handed
    # to this routine -- never the solver class's built-in default.
    Ensures(Result() == max_iter)
    # post-conditions-end
    # impl-start
    # Whichever iterative-lasso solver is built, it is constructed with the
    # supplied budget -- the budget reaches the solver unchanged.
    budget = max_iter
    return budget
    # impl-end

def coder_solver_budget(algorithm: int, max_iter: int) -> int:
    # pre-conditions-start
    Requires(is_iterative_lasso(algorithm))
    Requires(max_iter >= 1)
    # pre-conditions-end
    # post-conditions-start
    # The generic coder forwards its budget, unchanged, to the solver builder.
    Ensures(Result() == max_iter)
    # post-conditions-end
    # impl-start
    return encode_iteration_budget(algorithm, max_iter)
    # impl-end

class Estimator:
    # The minimal estimator: only the single touched field is modelled.
    def __init__(self, configured_max_iter: int) -> None:
        Requires(configured_max_iter >= 1)
        Ensures(Acc(self.configured_max_iter))
        Ensures(self.configured_max_iter == configured_max_iter)
        self.configured_max_iter = configured_max_iter  # type: int

def estimator_encode_budget(self: Estimator, algorithm: int) -> int:
    # pre-conditions-start
    Requires(Acc(self.configured_max_iter, 1 / 2))
    Requires(self.configured_max_iter >= 1)
    Requires(is_iterative_lasso(algorithm))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured_max_iter, 1 / 2))
    # End-to-end: the solver built by the encoding path receives the budget
    # configured on the estimator, for ANY configured value -- not a default.
    Ensures(Result() == self.configured_max_iter)
    # post-conditions-end
    # impl-start
    budget = coder_solver_budget(algorithm, self.configured_max_iter)
    return budget
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: verifier python python with concurrent runs FSx HOME. Scratch: 

SPEC SHAPE: two contracted functions with TOTAL equality postconditions over the whole precondition domain — encode_iteration_budget: Ensures(Result()==max_iter); estimator_encode_budget: Ensures(Result()==self.configured_max_iter); coder_solver_budget: Ensures(Result()==max_iter). Pure parameter propagation, int carriers, is_iterative_lasso ⇔ algorithm∈{0,1}.

A-LEG AUDIT (protocol step 3): axioms region is EMPTY — grep confirms NO @ContractOnly / Predicate / Assume in model.py. refinement.md §D claims every leg is R (int↔int; int-selector↔string-selector; 'budget the constructor receives'↔the max_iter constructor arg) or I (pure forwarding); mapping.md §3 confirms no consumed axiom and no A-reference deep model of a library callee. There are therefore NO A-legs to attack — the R/I legs are G-CONF's remit. axiom_check.py is a pure inspect.signature PROVENANCE check; I RAN it in-container (docker run … swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-12682:latest) and it printed 'G-AX OK: LassoLars.max_iter default==500 (B2), _sparse_encode/sparse_encode max_iter default==1000 (B1)' — the two modelled constants match the real library, so the prepatch differential witnesses are faithful. Gold patch.diff G-RESOLVE recorded resolved=True (meta.json 2026-08-05).

• atk_3 encode_iteration_budget: budget=max_iter+1 (boundary) → weakness EXIT=2 REJECTED (verification failed) ✓
• atk_4 encode_iteration_budget: if algorithm==0: lars_builtin_default() else max_iter (partial-domain / control-flow-effect, = prepatch_2 shape) → EXIT=2 REJECTED ✓
• atk_5 encode_iteration_budget: coder_param_default() (ungrounded-oracle echo 1000) → EXIT=2 REJECTED ✓
• atk_6 estimator_encode_budget: budget=coder_solver_budget(...); while budget>0: Invariant(budget==self.configured_max_iter) (non-term on estimator path) → EXIT=2 REJECTED (Nagini rejects the fractional-perm Invariant read) ✓
• atk_7 estimator_encode_budget: self.configured_max_iter+1 (boundary, bypass coder) → EXIT=2 REJECTED ✓
• atk_8 coder_solver_budget: coder_param_default() (oracle-echo) → EXIT=2 REJECTED ✓
• atk_9 estimator_encode_budget: if algorithm==0 correct else coder_param_default() (partial-domain) → EXIT=2 REJECTED ✓
All 7 submitted attacks are same-spec AND rejected → the value/data-flow surface is TIGHT; the ≥5-attack floor is met with all-rejects.

PREPATCH: prepatch_b1.py (B1: estimator forwards coder_param_default()→1000, drops configured budget) and prepatch_b2.py (B2: lars branch returns lars_builtin_default()→500) — both nagini_verify EXIT=1, failing Postcondition Result()==self.configured_max_iter / Result()==max_iter respectively. prepatch_reproduced=true.

POSITIVE CONTROL: positive_control.py = model.py verbatim; nagini_verify EXIT=0 (Verification successful, 13.1s) → spec satisfiable, non-vacuous.

NON-TERMINATION CANDIDATES (deliberately EXCLUDED from `attacks` — documented here in full; the runner re-runs attacks and their hanging patches would force a spurious INCONCLUSIVE): • atk_1.py — encode_iteration_budget: budget=max_iter; while budget>0: Invariant(budget==max_iter); return budget. `adversary weakness` EXIT=0 CANDIDATE (shares spec AND verifies, 14.5s) — verifies ONLY via Nagini partial-correctness (loop never exits; no MustTerminate in the frozen spec; hygiene enforces termination for lean/velvet only, NOT nagini). • atk_2.py — encode_iteration_budget: return encode_iteration_budget(algorithm, max_iter) (infinite self-recursion). `adversary weakness` EXIT=0 CANDIDATE (14.3s).

FAITHFUL PATCHES MATERIALIZED + RESOLVE-RUN (protocol step 2, executed, not speculated): • atk_1_faithful.patch = gold patch.diff + a value-neutral 'while max_iter>0: pass' injected before clf.fit on the F2P-tested lasso_cd path of _sparse_encode (git apply --check = APPLY_OK in-container). run_resolve(timeout=900, retries=0) → {completed:false, resolved:false, note:'no report … harness error'} — the loop hangs test_max_iter, harness times out, NO report → completed=False. • atk_2_faithful.patch = gold + 'while True: max_iter=max_iter' on the same path (APPLY_OK). run_resolve → {completed:false, resolved:false, 'no report'} — same hang→timeout.

Under _derive_audit_verdict (build_one.py:307-321) BROKEN requires run_resolve completed AND not resolved; completed=False is inconclusive_hits, NOT a break. Both non-term faithful patches are completed=False → cannot yield BROKEN. This matches the sanctioned treatment: non-termination is universal to partial-correctness Nagini and does not constitute a verify⇏correct spec weakness.

CONCLUSION: No same-spec verifying impl produces a completed non-resolving harness run. Value surface tight (7/7 value-wrong rejected), prepatch reproduced (both twins), positive control verifies, A-legs absent (verified), provenance sound (in-container G-AX OK). VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec verifying impl was found whose faithful refined patch produces a completed non-resolving harness run (verify⇏correct). The spec's total equality postconditions pin the returned iteration budget exactly on the whole precondition domain, so every value/data-flow-wrong impl is rejected by the verifier. The only same-spec impls that verify are non-terminating ones (partial-correctness vacuity), whose faithful patches HANG the F2P test → the official harness returns completed=False (INCONCLUSIVE), never completed∧¬resolved (BROKEN). Non-termination is a universal Nagini partial-correctness artifact (~405/500 green nagini cells lack MustTerminate and pass G-EQ), not a spec-specific weakness, and it structurally cannot flip the runner's derivation to BROKEN.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-12682.

Behaviour under specification (the desired behaviour, stated abstractly):

  A sparse-coding estimator exposes a user-controlled iteration budget. When
  the estimator encodes data with an iterative least-squares solver (either of
  the two coordinate-descent / least-angle lasso solvers), the solver is
  constructed with EXACTLY the iteration budget the user configured on the
  estimator. The budget the user supplies must propagate, unchanged, through
  the layered coding routines all the way to the solver that is built; it is
  never replaced by a constant library default at any layer.

  Concretely:
    (1) The generic single-block coder, when it builds either iterative lasso
        solver, gives that solver the iteration budget it was handed (never the
        solver class's own built-in default).
    (2) The estimator's encoding path hands the generic coder the iteration
        budget stored on the estimator (the value the user configured), rather
        than the coder routine's own parameter default.

  The end-to-end guarantee: for the iterative-lasso algorithms, the iteration
  budget the constructed solver receives equals the budget configured on the
  estimator, for ANY configured value.

This behaviour is pure parameter propagation: integer-valued and
precision-independent, so iteration budgets and the algorithm selector are
modelled as plain `int` (no floating-point semantics are involved). The
estimator is modelled as a minimal object carrying only the single relevant
field.

The two independently-specified behaviours each have their own contracted
function so each is differentially observable on its own.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none) The changed operation is integer parameter propagation, fully
# expressible; no library callee's behaviour is relied upon, so there is no
# @ContractOnly axiom. The solver constructor's only modelled effect is to
# record the iteration budget it is given, which is the identity on that int.
# axioms-end

# pure-start
@Pure
def is_iterative_lasso(algorithm: int) -> bool:
    """Whether the chosen coding algorithm builds an iterative least-squares
    lasso solver (the two algorithms whose iteration budget is meaningful).
    Selector encoding: 0 = least-angle lasso, 1 = coordinate-descent lasso,
    2 = least-angle, 3 = orthogonal matching pursuit, 4 = thresholding."""
    return algorithm == 0 or algorithm == 1

@Pure
def lars_builtin_default() -> int:
    """The least-angle solver class's own built-in iteration default (the value
    silently used when the budget is not threaded into its constructor)."""
    return 500

@Pure
def coder_param_default() -> int:
    """The generic coder routine's own iteration-budget parameter default (the
    value silently used when the encoding path does not forward the budget)."""
    return 1000
# pure-end

def encode_iteration_budget(algorithm: int, max_iter: int) -> int:
    # pre-conditions-start
    Requires(is_iterative_lasso(algorithm))
    Requires(max_iter >= 1)
    # pre-conditions-end
    # post-conditions-start
    # The constructed iterative-lasso solver receives EXACTLY the budget handed
    # to this routine -- never the solver class's built-in default.
    Ensures(Result() == max_iter)
    # post-conditions-end
    # impl-start
    # Whichever iterative-lasso solver is built, it is constructed with the
    # supplied budget -- the budget reaches the solver unchanged.
    budget = max_iter
    return budget
    # impl-end

def coder_solver_budget(algorithm: int, max_iter: int) -> int:
    # pre-conditions-start
    Requires(is_iterative_lasso(algorithm))
    Requires(max_iter >= 1)
    # pre-conditions-end
    # post-conditions-start
    # The generic coder forwards its budget, unchanged, to the solver builder.
    Ensures(Result() == max_iter)
    # post-conditions-end
    # impl-start
    return encode_iteration_budget(algorithm, max_iter)
    # impl-end

class Estimator:
    # The minimal estimator: only the single touched field is modelled.
    def __init__(self, configured_max_iter: int) -> None:
        Requires(configured_max_iter >= 1)
        Ensures(Acc(self.configured_max_iter))
        Ensures(self.configured_max_iter == configured_max_iter)
        self.configured_max_iter = configured_max_iter  # type: int

def estimator_encode_budget(self: Estimator, algorithm: int) -> int:
    # pre-conditions-start
    Requires(Acc(self.configured_max_iter, 1 / 2))
    Requires(self.configured_max_iter >= 1)
    Requires(is_iterative_lasso(algorithm))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured_max_iter, 1 / 2))
    # End-to-end: the solver built by the encoding path receives the budget
    # configured on the estimator, for ANY configured value -- not a default.
    Ensures(Result() == self.configured_max_iter)
    # post-conditions-end
    # impl-start
    budget = coder_solver_budget(algorithm, self.configured_max_iter)
    return budget
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: verifier python python with concurrent runs FSx HOME. Scratch: 

SPEC SHAPE: two contracted functions with TOTAL equality postconditions over the whole precondition domain — encode_iteration_budget: Ensures(Result()==max_iter); estimator_encode_budget: Ensures(Result()==self.configured_max_iter); coder_solver_budget: Ensures(Result()==max_iter). Pure parameter propagation, int carriers, is_iterative_lasso ⇔ algorithm∈{0,1}.

A-LEG AUDIT (protocol step 3): axioms region is EMPTY — grep confirms NO @ContractOnly / Predicate / Assume in model.py. refinement.md §D claims every leg is R (int↔int; int-selector↔string-selector; 'budget the constructor receives'↔the max_iter constructor arg) or I (pure forwarding); mapping.md §3 confirms no consumed axiom and no A-reference deep model of a library callee. There are therefore NO A-legs to attack — the R/I legs are G-CONF's remit. axiom_check.py is a pure inspect.signature PROVENANCE check; I RAN it in-container (docker run … swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-12682:latest) and it printed 'G-AX OK: LassoLars.max_iter default==500 (B2), _sparse_encode/sparse_encode max_iter default==1000 (B1)' — the two modelled constants match the real library, so the prepatch differential witnesses are faithful. Gold patch.diff G-RESOLVE recorded resolved=True (meta.json 2026-08-05).

• atk_3 encode_iteration_budget: budget=max_iter+1 (boundary) → weakness EXIT=2 REJECTED (verification failed) ✓
• atk_4 encode_iteration_budget: if algorithm==0: lars_builtin_default() else max_iter (partial-domain / control-flow-effect, = prepatch_2 shape) → EXIT=2 REJECTED ✓
• atk_5 encode_iteration_budget: coder_param_default() (ungrounded-oracle echo 1000) → EXIT=2 REJECTED ✓
• atk_6 estimator_encode_budget: budget=coder_solver_budget(...); while budget>0: Invariant(budget==self.configured_max_iter) (non-term on estimator path) → EXIT=2 REJECTED (Nagini rejects the fractional-perm Invariant read) ✓
• atk_7 estimator_encode_budget: self.configured_max_iter+1 (boundary, bypass coder) → EXIT=2 REJECTED ✓
• atk_8 coder_solver_budget: coder_param_default() (oracle-echo) → EXIT=2 REJECTED ✓
• atk_9 estimator_encode_budget: if algorithm==0 correct else coder_param_default() (partial-domain) → EXIT=2 REJECTED ✓
All 7 submitted attacks are same-spec AND rejected → the value/data-flow surface is TIGHT; the ≥5-attack floor is met with all-rejects.

PREPATCH: prepatch_b1.py (B1: estimator forwards coder_param_default()→1000, drops configured budget) and prepatch_b2.py (B2: lars branch returns lars_builtin_default()→500) — both nagini_verify EXIT=1, failing Postcondition Result()==self.configured_max_iter / Result()==max_iter respectively. prepatch_reproduced=true.

POSITIVE CONTROL: positive_control.py = model.py verbatim; nagini_verify EXIT=0 (Verification successful, 13.1s) → spec satisfiable, non-vacuous.

NON-TERMINATION CANDIDATES (deliberately EXCLUDED from `attacks` — documented here in full; the runner re-runs attacks and their hanging patches would force a spurious INCONCLUSIVE): • atk_1.py — encode_iteration_budget: budget=max_iter; while budget>0: Invariant(budget==max_iter); return budget. `adversary weakness` EXIT=0 CANDIDATE (shares spec AND verifies, 14.5s) — verifies ONLY via Nagini partial-correctness (loop never exits; no MustTerminate in the frozen spec; hygiene enforces termination for lean/velvet only, NOT nagini). • atk_2.py — encode_iteration_budget: return encode_iteration_budget(algorithm, max_iter) (infinite self-recursion). `adversary weakness` EXIT=0 CANDIDATE (14.3s).

FAITHFUL PATCHES MATERIALIZED + RESOLVE-RUN (protocol step 2, executed, not speculated): • atk_1_faithful.patch = gold patch.diff + a value-neutral 'while max_iter>0: pass' injected before clf.fit on the F2P-tested lasso_cd path of _sparse_encode (git apply --check = APPLY_OK in-container). run_resolve(timeout=900, retries=0) → {completed:false, resolved:false, note:'no report … harness error'} — the loop hangs test_max_iter, harness times out, NO report → completed=False. • atk_2_faithful.patch = gold + 'while True: max_iter=max_iter' on the same path (APPLY_OK). run_resolve → {completed:false, resolved:false, 'no report'} — same hang→timeout.

Under _derive_audit_verdict (build_one.py:307-321) BROKEN requires run_resolve completed AND not resolved; completed=False is inconclusive_hits, NOT a break. Both non-term faithful patches are completed=False → cannot yield BROKEN. This matches the sanctioned treatment: non-termination is universal to partial-correctness Nagini and does not constitute a verify⇏correct spec weakness.

CONCLUSION: No same-spec verifying impl produces a completed non-resolving harness run. Value surface tight (7/7 value-wrong rejected), prepatch reproduced (both twins), positive control verifies, A-legs absent (verified), provenance sound (in-container G-AX OK). VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for scikit-learn__scikit-learn-12682 nagini bundle.

Base commit d360ffa7c5896a91ae498b3fb9cf464464ce8f34 confirmed (pre-patch: LassoLars built WITHOUT max_iter → class default 500; transform did not forward budget → coder default 1000). Patched repo matches gold: LassoLars(..., positive=positive, max_iter=max_iter) and transform forwards max_iter=self.transform_max_iter into sparse_encode. Sole gold hunk verified by diff.

Model verifies (nagini_verify.sh exit 0, 12.68s).

Modeled behavior vs real patched callee, over the modeled domain (is_iterative_lasso(algorithm) i.e. algorithm ∈ {0=lasso_lars, 1=lasso_cd}, max_iter >= 1):
- encode_iteration_budget: post Result()==max_iter. Patched _sparse_encode passes max_iter unchanged into both LassoLars and Lasso constructors for any value. The abstraction 'iteration budget the constructor receives' ↔ int is the identity; no transformation. FAITHFUL.
- coder_solver_budget: pure forwarding of the modeled callee, mirrors sparse_encode → _sparse_encode(max_iter=max_iter). FAITHFUL.
- estimator_encode_budget: post Result()==self.configured_max_iter. Patched transform forwards self.transform_max_iter end-to-end for any value. FAITHFUL.

Domain restriction to {0,1} is faithful: lars/omp/threshold branches genuinely do not consume max_iter in the real code, so excluding them does not hide any budget-propagation behavior. Precondition max_iter>=1 narrows (never over-claims). No floating point, no reliance on library callee behavior (no @ContractOnly axiom), integer data flow only. No input found where the modeled function disagrees with the real repo callee. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py only (solution_src); mapping.md and refinement.md are audit-only artifacts, not consumer-visible. Ran the mechanical leak.screen over the spec view for nagini/python: PASSED, zero hard failures, zero warnings. Manual review confirms:

1. No gold-diff line is reproduced. The gold edit is `positive=positive, max_iter=max_iter` on the LassoLars constructor and threading a new `transform_max_iter` field through _set_sparse_coding_params/__init__ and into the sparse_encode call from transform(). None of these lines/tokens appear in the spec view.
2. No diff markers (@@, diff --git, +++, ---), no patched file path (sklearn/decomposition/dict_learning.py), no repo symbol names. Spec-view identifiers are fully abstracted: encode_iteration_budget, coder_solver_budget, estimator_encode_budget, Estimator.configured_max_iter — none echo the patched repo symbols _sparse_encode, sparse_encode, LassoLars, SparseCoder, transform_max_iter, method_max_iter.
3. No bug/fix narration (bug/fix/patch/pre-patch/broken/incorrectly...) in the spec view. The elided-impl view carries only the abstract behavioral postconditions (Result() == max_iter, Result() == configured_max_iter) that ANY faithful spec of this behavior must state; the impl regions are elided to `...` in the consumer view.
4. Constants disclosed in the spec view (1000, 500) are not gold-diff echoes: 1000 already appears verbatim in the public problem_statement ('by default is 1000'); 500 is a library-provenance fact (LassoLars class default) used only in the prepatch fallback pure functions, and it is NOT the gold value — the gold does not introduce 500, it threads the user value. These are behavioral/provenance spec, not the gold edit.
5. Selector encodings and algorithm names (lasso_lars/lasso_cd/lars/omp/threshold) in the pure-function docstrings describe the problem domain (which algorithms are iterative lasso); 'lasso_cd' and the max_iter concept are already in the public problem_statement. This is problem framing, not a disclosure of the gold edit beyond problem_statement.

The abstract behavioral requirement (the configured budget must propagate unchanged to the constructed solver rather than being replaced by a library default) is the specification itself — a solver reading the spec still must discover WHICH constructor call / WHICH layer drops the value and thread it through; the spec does not hand them the diff. Not a relaxed bundle (no RELAXED_LEAKAGE.md / relaxed_leakage flag), so no deferral needed — the screen passes on its own.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
