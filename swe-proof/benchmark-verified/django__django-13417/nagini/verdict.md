# P2 adversarial audit — django__django-13417

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.py`, `atk2.py`, `atk3.py`, `atk5.py`, `atk6.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk4.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,14 +54,6 @@
 def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
             model_has_order: bool, is_grouped: bool) -> bool:
     # pre-conditions-start
-    # Total correctness: this decision must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is an ordinal for
-    # the obligation ordering, not a measure: there is no loop and no recursion
-    # here, so nothing counts down. It is input-dependent (3 on the empty
-    # branch, 2 otherwise) purely to leave ordinal room BELOW a caller for a
-    # self-call on a non-empty input: Nagini requires callee level < caller
-    # level, which a single literal level can never satisfy against itself.
-    Requires(MustTerminate(3 if is_empty else 2))
     # pre-conditions-end
     # post-conditions-start
     # The flag equals the exact boolean decision over the five signals.
@@ -84,12 +75,5 @@
                     Result()))
     # post-conditions-end
     # impl-start
-    if is_empty:
-        return True
-    if has_raw_order:
-        return True
-    elif default_on and model_has_order and not is_grouped:
-        return True
-    else:
-        return False
+    return True
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,14 +54,6 @@
 def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
             model_has_order: bool, is_grouped: bool) -> bool:
     # pre-conditions-start
-    # Total correctness: this decision must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is an ordinal for
-    # the obligation ordering, not a measure: there is no loop and no recursion
-    # here, so nothing counts down. It is input-dependent (3 on the empty
-    # branch, 2 otherwise) purely to leave ordinal room BELOW a caller for a
-    # self-call on a non-empty input: Nagini requires callee level < caller
-    # level, which a single literal level can never satisfy against itself.
-    Requires(MustTerminate(3 if is_empty else 2))
     # pre-conditions-end
     # post-conditions-start
     # The flag equals the exact boolean decision over the five signals.
@@ -88,7 +79,7 @@
         return True
     if has_raw_order:
         return True
-    elif default_on and model_has_order and not is_grouped:
+    elif default_on and model_has_order:
         return True
     else:
         return False
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,14 +54,6 @@
 def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
             model_has_order: bool, is_grouped: bool) -> bool:
     # pre-conditions-start
-    # Total correctness: this decision must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is an ordinal for
-    # the obligation ordering, not a measure: there is no loop and no recursion
-    # here, so nothing counts down. It is input-dependent (3 on the empty
-    # branch, 2 otherwise) purely to leave ordinal room BELOW a caller for a
-    # self-call on a non-empty input: Nagini requires callee level < caller
-    # level, which a single literal level can never satisfy against itself.
-    Requires(MustTerminate(3 if is_empty else 2))
     # pre-conditions-end
     # post-conditions-start
     # The flag equals the exact boolean decision over the five signals.
@@ -88,7 +79,7 @@
         return True
     if has_raw_order:
         return True
-    elif default_on and model_has_order and not is_grouped:
+    elif default_on and model_has_order and is_grouped:
         return True
     else:
         return False
```

Attack 4 — `atk4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,14 +54,6 @@
 def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
             model_has_order: bool, is_grouped: bool) -> bool:
     # pre-conditions-start
-    # Total correctness: this decision must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is an ordinal for
-    # the obligation ordering, not a measure: there is no loop and no recursion
-    # here, so nothing counts down. It is input-dependent (3 on the empty
-    # branch, 2 otherwise) purely to leave ordinal room BELOW a caller for a
-    # self-call on a non-empty input: Nagini requires callee level < caller
-    # level, which a single literal level can never satisfy against itself.
-    Requires(MustTerminate(3 if is_empty else 2))
     # pre-conditions-end
     # post-conditions-start
     # The flag equals the exact boolean decision over the five signals.
@@ -84,12 +75,5 @@
                     Result()))
     # post-conditions-end
     # impl-start
-    if is_empty:
-        return True
-    if has_raw_order:
-        return True
-    elif default_on and model_has_order and not is_grouped:
-        return True
-    else:
-        return False
+    return is_ordered(is_empty, has_raw_order, default_on, model_has_order, is_grouped)
     # impl-end
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,14 +54,6 @@
 def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
             model_has_order: bool, is_grouped: bool) -> bool:
     # pre-conditions-start
-    # Total correctness: this decision must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is an ordinal for
-    # the obligation ordering, not a measure: there is no loop and no recursion
-    # here, so nothing counts down. It is input-dependent (3 on the empty
-    # branch, 2 otherwise) purely to leave ordinal room BELOW a caller for a
-    # self-call on a non-empty input: Nagini requires callee level < caller
-    # level, which a single literal level can never satisfy against itself.
-    Requires(MustTerminate(3 if is_empty else 2))
     # pre-conditions-end
     # post-conditions-start
     # The flag equals the exact boolean decision over the five signals.
@@ -88,7 +79,7 @@
         return True
     if has_raw_order:
         return True
-    elif default_on and model_has_order and not is_grouped:
+    elif default_on and not is_grouped:
         return True
     else:
         return False
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,14 +54,6 @@
 def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
             model_has_order: bool, is_grouped: bool) -> bool:
     # pre-conditions-start
-    # Total correctness: this decision must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is an ordinal for
-    # the obligation ordering, not a measure: there is no loop and no recursion
-    # here, so nothing counts down. It is input-dependent (3 on the empty
-    # branch, 2 otherwise) purely to leave ordinal room BELOW a caller for a
-    # self-call on a non-empty input: Nagini requires callee level < caller
-    # level, which a single literal level can never satisfy against itself.
-    Requires(MustTerminate(3 if is_empty else 2))
     # pre-conditions-end
     # post-conditions-start
     # The flag equals the exact boolean decision over the five signals.
@@ -85,7 +76,7 @@
     # post-conditions-end
     # impl-start
     if is_empty:
-        return True
+        return False
     if has_raw_order:
         return True
     elif default_on and model_has_order and not is_grouped:
```

Attack 7 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -55,14 +54,6 @@
 def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
             model_has_order: bool, is_grouped: bool) -> bool:
     # pre-conditions-start
-    # Total correctness: this decision must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is an ordinal for
-    # the obligation ordering, not a measure: there is no loop and no recursion
-    # here, so nothing counts down. It is input-dependent (3 on the empty
-    # branch, 2 otherwise) purely to leave ordinal room BELOW a caller for a
-    # self-call on a non-empty input: Nagini requires callee level < caller
-    # level, which a single literal level can never satisfy against itself.
-    Requires(MustTerminate(3 if is_empty else 2))
     # pre-conditions-end
     # post-conditions-start
     # The flag equals the exact boolean decision over the five signals.
@@ -88,7 +79,7 @@
         return True
     if has_raw_order:
         return True
-    elif default_on and model_has_order and not is_grouped:
+    elif default_on and model_has_order:
         return True
     else:
         return False
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13417.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A result set's introspection flag answers "will this result set come back in
  a well-defined order?" It is decided from five independent conditions about
  the result set, each consumed purely as a yes/no signal:

    * `is_empty`        - the result set is statically empty;
    * `has_raw_order`   - an explicit raw / column ordering was attached;
    * `default_on`      - default ordering inherited from the model is active;
    * `model_has_order` - the model declares a default ordering at all;
    * `is_grouped`      - the result set collapses rows into groups.

  The flag is TRUE exactly when the result set is statically empty, OR an
  explicit ordering is attached, OR a model default ordering is both active and
  declared AND the result set is NOT grouped. When rows are collapsed into
  groups, an inherited model default ordering no longer governs the row order,
  so a grouped result set with only a default (non-explicit) ordering is NOT
  ordered.

The five conditions are read in the repository as attributes whose only use is
their truth value; they are modelled here as `bool` (the truthy-refinement is
recorded in refinement.md / mapping.md). The result is pinned exactly to the
boolean predicate above, so no implementation that disagrees on any of the
thirty-two input combinations can verify. There are no library callees to
axiomatize and no heap-carried mutable inputs: the operation is a pure boolean
decision.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def is_ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
               model_has_order: bool, is_grouped: bool) -> bool:
    """The exact decision the flag must report: empty, or an explicit ordering,
    or an active+declared model default ordering on a result set that is not
    grouped. Grouping suppresses an inherited default ordering."""
    return (
        is_empty
        or has_raw_order
        or (default_on and model_has_order and not is_grouped)
    )
# pure-end


def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
            model_has_order: bool, is_grouped: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The flag equals the exact boolean decision over the five signals.
    Ensures(Result() == is_ordered(is_empty, has_raw_order, default_on,
                                    model_has_order, is_grouped))
    # Pinned consequences that any correct decision must exhibit, derived from
    # the desired behaviour above (each ties the result to a witnessed input):
    #   an empty result set is always ordered;
    Ensures(Implies(is_empty, Result()))
    #   an explicitly-ordered result set is always ordered;
    Ensures(Implies(has_raw_order, Result()))
    #   a grouped result set whose only ordering is an inherited model default
    #   (no emptiness, no explicit ordering) is NOT ordered;
    Ensures(Implies(not is_empty and not has_raw_order and is_grouped,
                    not Result()))
    #   the same default ordering on a non-grouped result set IS ordered.
    Ensures(Implies(not is_empty and not has_raw_order
                    and default_on and model_has_order and not is_grouped,
                    Result()))
    # post-conditions-end
    # impl-start
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins Result() == is_ordered(is_empty, has_raw_order, default_on, model_has_order, is_grouped) exactly over all 32 boolean input combos, with NO precondition; is_ordered = is_empty or has_raw_order or (default_on and model_has_order and not is_grouped). This is maximally strong: any impl disagreeing on any combination cannot verify.

ATTACKS (all built by editing ONLY the impl region of model.py; axioms/@Pure/Requires/Ensures byte-identical; all 7 confirmed same-spec exit 0). Command form: `python -m swebench_unified.adversary weakness nagini django__django-13417 <path>` (SBU_BENCHMARK_DIR=benchmark-verified; python=python). Run concurrently in batches of 3 (JVM+Z3 each).
- atk1.py (partial-domain/degenerate: `return True`): weakness exit=2 — verification FAILED, spec rejected (good).
- atk2.py (boundary: elif drops `not is_grouped` conjunct, == prepatch bug): weakness exit=2 — rejected.
- atk3.py (control-flow-effect: elif uses `and is_grouped` instead of `and not is_grouped`): weakness exit=2 — rejected.
- atk4.py (ungrounded-oracle echo: `return is_ordered(...)`): weakness exit=0 CANDIDATE (shares spec AND verifies, 12.1s). This is a behaviorally-CORRECT echo of the gold decision, so per protocol I materialized its faithful refined patch (= the gold hunk adding `and not self.query.group_by` to QuerySet.ordered) at atk4_faithful.diff and ran it through the OFFICIAL harness: run_resolve('django__django-13417', patch) => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. Patch RESOLVES => NOT a weakness (verify AND correct).
- atk5.py (boundary: elif drops model_has_order conjunct -> `default_on and not is_grouped`): weakness exit=2 — rejected.
- atk6.py (control-flow: `if is_empty: return False` inverted branch): weakness exit=2 — rejected.
- atk_prepatch.py (bundle model_prepatch.py, the known prepatch bug): weakness exit=2 — verification failed, prepatch reproduced.

POSITIVE CONTROL: pos_control.py (copy of model.py) — same-spec exit 0; verifies (implicitly, as the shipped model and via atk4's equivalent).

A-LEG / refinement.md AUDIT: axioms=[] and deep_model_references=[] in meta.json — there are NO A-legs (no @ContractOnly, no deep-model refs). axiom_check.py run => exit 0: 'G-AX OK (no axioms): is_ordered model == real QuerySet.ordered property body over 128 concrete input combinations'. refinement.md legs A1-A9 are all R (truthy-to-bool refinements A1/A3/A5/A6/A7, exact per mapping.md §2) or I (identical control flow A2/A4/A8/A9). No kind-3 (inexpressible) steps. Model↔patch correspondence holds: the 5 bool params bind 1:1 to the 5 truthy repo expressions QuerySet.ordered reads, and the discriminating `and not is_grouped` conjunct (A8) maps to the gold's added `not self.query.group_by`. G-AX vacuous (no axioms).

Conclusion: >=5 distinct wrong impls run; every non-verifying wrong impl was rejected by the spec; the only verifying candidate (atk4) is a correct oracle-echo whose faithful patch RESOLVES. No verifying wrong impl exists whose faithful patch fails to resolve. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.py`, `atk2.py`, `atk3.py`, `atk5.py`, `atk6.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk4.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13417.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A result set's introspection flag answers "will this result set come back in
  a well-defined order?" It is decided from five independent conditions about
  the result set, each consumed purely as a yes/no signal:

    * `is_empty`        - the result set is statically empty;
    * `has_raw_order`   - an explicit raw / column ordering was attached;
    * `default_on`      - default ordering inherited from the model is active;
    * `model_has_order` - the model declares a default ordering at all;
    * `is_grouped`      - the result set collapses rows into groups.

  The flag is TRUE exactly when the result set is statically empty, OR an
  explicit ordering is attached, OR a model default ordering is both active and
  declared AND the result set is NOT grouped. When rows are collapsed into
  groups, an inherited model default ordering no longer governs the row order,
  so a grouped result set with only a default (non-explicit) ordering is NOT
  ordered.

The five conditions are read in the repository as attributes whose only use is
their truth value; they are modelled here as `bool` (the truthy-refinement is
recorded in refinement.md / mapping.md). The result is pinned exactly to the
boolean predicate above, so no implementation that disagrees on any of the
thirty-two input combinations can verify. There are no library callees to
axiomatize and no heap-carried mutable inputs: the operation is a pure boolean
decision.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def is_ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
               model_has_order: bool, is_grouped: bool) -> bool:
    """The exact decision the flag must report: empty, or an explicit ordering,
    or an active+declared model default ordering on a result set that is not
    grouped. Grouping suppresses an inherited default ordering."""
    return (
        is_empty
        or has_raw_order
        or (default_on and model_has_order and not is_grouped)
    )
# pure-end


def ordered(is_empty: bool, has_raw_order: bool, default_on: bool,
            model_has_order: bool, is_grouped: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The flag equals the exact boolean decision over the five signals.
    Ensures(Result() == is_ordered(is_empty, has_raw_order, default_on,
                                    model_has_order, is_grouped))
    # Pinned consequences that any correct decision must exhibit, derived from
    # the desired behaviour above (each ties the result to a witnessed input):
    #   an empty result set is always ordered;
    Ensures(Implies(is_empty, Result()))
    #   an explicitly-ordered result set is always ordered;
    Ensures(Implies(has_raw_order, Result()))
    #   a grouped result set whose only ordering is an inherited model default
    #   (no emptiness, no explicit ordering) is NOT ordered;
    Ensures(Implies(not is_empty and not has_raw_order and is_grouped,
                    not Result()))
    #   the same default ordering on a non-grouped result set IS ordered.
    Ensures(Implies(not is_empty and not has_raw_order
                    and default_on and model_has_order and not is_grouped,
                    Result()))
    # post-conditions-end
    # impl-start
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins Result() == is_ordered(is_empty, has_raw_order, default_on, model_has_order, is_grouped) exactly over all 32 boolean input combos, with NO precondition; is_ordered = is_empty or has_raw_order or (default_on and model_has_order and not is_grouped). This is maximally strong: any impl disagreeing on any combination cannot verify.

ATTACKS (all built by editing ONLY the impl region of model.py; axioms/@Pure/Requires/Ensures byte-identical; all 7 confirmed same-spec exit 0). Command form: `python -m swebench_unified.adversary weakness nagini django__django-13417 <path>` (SBU_BENCHMARK_DIR=benchmark-verified; python=python). Run concurrently in batches of 3 (JVM+Z3 each).
- atk1.py (partial-domain/degenerate: `return True`): weakness exit=2 — verification FAILED, spec rejected (good).
- atk2.py (boundary: elif drops `not is_grouped` conjunct, == prepatch bug): weakness exit=2 — rejected.
- atk3.py (control-flow-effect: elif uses `and is_grouped` instead of `and not is_grouped`): weakness exit=2 — rejected.
- atk4.py (ungrounded-oracle echo: `return is_ordered(...)`): weakness exit=0 CANDIDATE (shares spec AND verifies, 12.1s). This is a behaviorally-CORRECT echo of the gold decision, so per protocol I materialized its faithful refined patch (= the gold hunk adding `and not self.query.group_by` to QuerySet.ordered) at atk4_faithful.diff and ran it through the OFFICIAL harness: run_resolve('django__django-13417', patch) => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. Patch RESOLVES => NOT a weakness (verify AND correct).
- atk5.py (boundary: elif drops model_has_order conjunct -> `default_on and not is_grouped`): weakness exit=2 — rejected.
- atk6.py (control-flow: `if is_empty: return False` inverted branch): weakness exit=2 — rejected.
- atk_prepatch.py (bundle model_prepatch.py, the known prepatch bug): weakness exit=2 — verification failed, prepatch reproduced.

POSITIVE CONTROL: pos_control.py (copy of model.py) — same-spec exit 0; verifies (implicitly, as the shipped model and via atk4's equivalent).

A-LEG / refinement.md AUDIT: axioms=[] and deep_model_references=[] in meta.json — there are NO A-legs (no @ContractOnly, no deep-model refs). axiom_check.py run => exit 0: 'G-AX OK (no axioms): is_ordered model == real QuerySet.ordered property body over 128 concrete input combinations'. refinement.md legs A1-A9 are all R (truthy-to-bool refinements A1/A3/A5/A6/A7, exact per mapping.md §2) or I (identical control flow A2/A4/A8/A9). No kind-3 (inexpressible) steps. Model↔patch correspondence holds: the 5 bool params bind 1:1 to the 5 truthy repo expressions QuerySet.ordered reads, and the discriminating `and not is_grouped` conjunct (A8) maps to the gold's added `not self.query.group_by`. G-AX vacuous (no axioms).

Conclusion: >=5 distinct wrong impls run; every non-verifying wrong impl was rejected by the spec; the only verifying candidate (atk4) is a correct oracle-echo whose faithful patch RESOLVES. No verifying wrong impl exists whose faithful patch fails to resolve. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeled function `ordered(is_empty, has_raw_order, default_on, model_has_order, is_grouped)` is pinned exactly to the boolean predicate `is_empty or has_raw_order or (default_on and model_has_order and not is_grouped)` over five bool signals. This models the GOLD-PATCHED `QuerySet.ordered` property (django/db/models/query.py), which adds the `and not self.query.group_by` conjunct that the base_commit pre-patch body omits.

Faithfulness checks performed:
1. same-spec: model.py's spec region is byte-identical to the bundle (exit 0).
2. Ran the bundle's conformance oracle against the REAL patched repo (django 3.2, property with the `not self.query.group_by` conjunct applied): 100128 inputs (128 exhaustive boundary combos = all 2^5 truth-value combinations expanded over concrete repo-shaped values, + 100000 seeded fuzz). ZERO disagreements between the modeled decision and the real property.
3. Verified the type-bridge fidelity independently: `.none()` yields an EmptyQuerySet instance (isinstance True) and `.all()` does not (isinstance False), so the is_empty parameter faithfully abstracts `isinstance(self, EmptyQuerySet)`. The four other signals (extra_order_by/order_by disjunction, default_ordering, Meta.ordering, group_by) are all consumed by the real property purely for truthiness, so the truthy->bool R-refinement is exact for the property's observable result.

No input was found on which the modeled function disagrees with the real callee. The spec is neither too strong nor drifted; it exactly captures the post-patch behavior including the grouping-suppresses-default-ordering discriminating case (is_grouped=True, default-only ordering -> NOT ordered), which is precisely the gold change.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage check on the consumer spec view (spec_view projection of model.py: module docstring + pure `is_ordered` helper + `ordered` signature/pre/post-conditions; impl elided). same_spec confirms the spec view is byte-intact (exit 0).

Gold edit: adds the conjunct `not self.query.group_by` to QuerySet.ordered (django/db/models/query.py) so a GROUP BY query whose only ordering is an inherited model default (default_ordering + Meta.ordering) reports NOT ordered.

Public problem_statement ALREADY discloses this exact corrective behavior: title 'QuerySet.ordered property is incorrect for GROUP BY queries on models with Meta.ordering'; worked example shows `annotate(Count("pk"))` producing GROUP-BY SQL with no ORDER BY, yet `qs2.ordered # => True` (the bug) while `default_ordering # => True`. The required fix — a grouped result whose only ordering is an inherited model default must NOT be reported ordered — is fully implied by the public description alone.

Spec view expresses this over abstract booleans: parameter `is_grouped` and clause `(default_on and model_has_order and not is_grouped)`, docstring 'grouping suppresses an inherited default ordering'. That is a restatement of the public problem's corrective behavior, not disclosure of the implementation. The spec view names NO repo-specific edit machinery: the attribute `self.query.group_by`, the file/line, and the pre/post-patch hunk appear ONLY in mapping.md and refinement.md (audit/provenance artifacts excluded from the consumer view). Every model.py input is a generic truthiness bool; the is_empty/has_raw_order branches are pre-existing unchanged behavior.

hints_text does independently name group_by, but hints are excluded from this check per instructions — and the problem_statement alone already suffices to justify the spec content. No single spec-view line reveals the gold edit beyond the public problem_statement. No leaking line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
