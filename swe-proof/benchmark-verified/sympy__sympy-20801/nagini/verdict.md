# P2 adversarial audit — sympy__sympy-20801

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_15.py` |

**Non-vacuity.** The positive control `ctrl_gold.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -102,6 +102,8 @@
                     Result() == False))
     # post-conditions-end
     # impl-start
+    if self_is_zero:
+        return not other_truthy
     if kind == 0:
         return False
     if kind == 1:
@@ -114,7 +116,5 @@
         return numeric_eq
     if kind == 5:
         return numeric_eq
-    if self_is_zero:
-        return not other_truthy
     return False
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -102,19 +102,7 @@
                     Result() == False))
     # post-conditions-end
     # impl-start
-    if kind == 0:
-        return False
-    if kind == 1:
-        return False
-    if kind == 2:
-        return numeric_eq
-    if kind == 3:
-        return numeric_eq
-    if kind == 4:
-        return numeric_eq
-    if kind == 5:
-        return numeric_eq
-    if self_is_zero:
-        return not other_truthy
+    while True:
+        pass
     return False
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -102,17 +102,12 @@
                     Result() == False))
     # post-conditions-end
     # impl-start
+    Assert(False)
     if kind == 0:
         return False
     if kind == 1:
         return False
-    if kind == 2:
-        return numeric_eq
-    if kind == 3:
-        return numeric_eq
-    if kind == 4:
-        return numeric_eq
-    if kind == 5:
+    if is_numeric_kind(kind):
         return numeric_eq
     if self_is_zero:
         return not other_truthy
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -113,7 +113,7 @@
     if kind == 4:
         return numeric_eq
     if kind == 5:
-        return numeric_eq
+        raise ValueError()
     if self_is_zero:
         return not other_truthy
     return False
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -115,6 +115,6 @@
     if kind == 5:
         return numeric_eq
     if self_is_zero:
-        return not other_truthy
+        return other_truthy
     return False
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -102,19 +102,13 @@
                     Result() == False))
     # post-conditions-end
     # impl-start
-    if kind == 0:
-        return False
-    if kind == 1:
-        return False
-    if kind == 2:
+    if is_numeric_kind(kind):
         return numeric_eq
-    if kind == 3:
-        return numeric_eq
-    if kind == 4:
-        return numeric_eq
-    if kind == 5:
-        return numeric_eq
-    if self_is_zero:
-        return not other_truthy
+    if is_other_kind(kind):
+        if not self_is_zero:
+            return False
+        if other_truthy:
+            return False
+        return True
     return False
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -113,7 +113,7 @@
     if kind == 4:
         return numeric_eq
     if kind == 5:
-        return numeric_eq
+        return False
     if self_is_zero:
         return not other_truthy
     return False
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -116,5 +116,5 @@
         return numeric_eq
     if self_is_zero:
         return not other_truthy
-    return False
+    return float_equals(self_is_zero, kind, other_truthy, numeric_eq)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,7 @@
     # post-conditions-end
     # impl-start
     if kind == 0:
-        return False
+        return numeric_eq
     if kind == 1:
         return False
     if kind == 2:
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,8 @@
     if kind == 0:
         return False
     if kind == 1:
-        return False
+        empty = []  # type: List[bool]
+        return empty[0]
     if kind == 2:
         return numeric_eq
     if kind == 3:
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,7 @@
     if kind == 0:
         return False
     if kind == 1:
-        return False
+        return numeric_eq
     if kind == 2:
         return numeric_eq
     if kind == 3:
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,5 @@
         return numeric_eq
     if kind == 5:
         return numeric_eq
-    if self_is_zero:
-        return not other_truthy
-    return False
+    return not other_truthy
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,6 +103,8 @@
     # post-conditions-end
     # impl-start
     if kind == 0:
+        while self_is_zero:
+            pass
         return False
     if kind == 1:
         return False
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -116,5 +116,7 @@
         return numeric_eq
     if self_is_zero:
         return not other_truthy
+    if kind == 6 and not self_is_zero:
+        return float_equals(False, 6, other_truthy, numeric_eq)
     return False
     # impl-end
```

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -102,19 +102,10 @@
                     Result() == False))
     # post-conditions-end
     # impl-start
-    if kind == 0:
-        return False
-    if kind == 1:
-        return False
-    if kind == 2:
-        return numeric_eq
-    if kind == 3:
-        return numeric_eq
-    if kind == 4:
-        return numeric_eq
-    if kind == 5:
-        return numeric_eq
-    if self_is_zero:
-        return not other_truthy
-    return False
+    result = False
+    if is_numeric_kind(kind):
+        result = numeric_eq
+    elif is_other_kind(kind) and self_is_zero and not other_truthy:
+        result = True
+    return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_gold.py`

```python
"""Twin-artifact model for sympy__sympy-20801.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Equality of an exact floating value against an already-sympified operand is
  determined by WHAT the operand is. The operand falls into one of a small
  number of kinds, and the equality verdict is determined by that kind:

    * a logical truth value (one of the two symbolic booleans) is NEVER equal to
      a floating value: the result is False, irrespective of the floating
      value — in particular a floating value that happens to be zero is still
      unequal to either symbolic boolean;
    * an irrational named constant is never equal to a floating value (False);
    * a rational named constant, a rational number, or another floating value
      compares by the numeric-equality decision proper to that kind;
    * any other numeric operand compares by the numeric-equality decision;
    * an operand that is none of the above (neither a number nor a logical truth
      value) is equal to the floating value exactly when the floating value is
      zero and the operand is falsy; otherwise the result is False.

The operand is abstracted by an integer kind code over these cases; two further
observations of the operand are carried explicitly: its truth value, and, for
the numeric kinds, the numeric-equality decision (a sub-decision proper to each
numeric kind, supplied as an opaque boolean). The floating value itself is
abstracted by whether it is zero. The result is the equality verdict.

The equality decision MUST terminate (a total-correctness obligation, carried
as MustTerminate in the precondition): the real dispatch is a bounded,
loop-free decision that always returns a verdict. Nagini verifies partial
correctness by default, so without the obligation a diverging implementation
(`while True: pass`) would satisfy every value postcondition vacuously — yet
its real counterpart is a Float.__eq__ that hangs every equality test and
does NOT resolve the instance.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# axioms-end

# pure-start
@Pure
def is_truth_value(kind: int) -> bool:
    """The operand is a symbolic logical truth value (kind 0)."""
    return kind == 0

@Pure
def is_irrational_const(kind: int) -> bool:
    """The operand is an irrational named constant (kind 1)."""
    return kind == 1

@Pure
def is_numeric_kind(kind: int) -> bool:
    """The operand is one of the numeric kinds whose verdict is the
    numeric-equality decision: a rational named constant, another floating
    value, a rational number, or any other number (kinds 2..5)."""
    return kind == 2 or kind == 3 or kind == 4 or kind == 5

@Pure
def is_other_kind(kind: int) -> bool:
    """The operand is none of the above: neither a number nor a logical truth
    value (kind 6)."""
    return kind == 6
# pure-end

def float_equals(self_is_zero: bool, kind: int, other_truthy: bool,
                 numeric_eq: bool) -> bool:
    # pre-conditions-start
    # `kind` ranges over the seven cases the dispatch distinguishes.
    Requires(0 <= kind and kind <= 6)
    # TERMINATION (total correctness): the real Float.__eq__ dispatch is a
    # bounded, loop-free decision — it always returns a verdict. Nagini
    # verifies partial correctness by default, so without this obligation a
    # diverging impl (`while True: pass`) satisfies every value postcondition
    # VACUOUSLY yet its real counterpart hangs every Float equality test
    # (the F2P run times out) and does not resolve. Any loop now needs a
    # decreasing measure; a bare infinite loop is rejected.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # A symbolic logical truth value is never equal to a floating value, even a
    # zero one — the verdict is False regardless of self_is_zero / other_truthy.
    Ensures(Implies(is_truth_value(kind), Result() == False))
    # An irrational named constant is never equal to a floating value.
    Ensures(Implies(is_irrational_const(kind), Result() == False))
    # The numeric kinds defer to the numeric-equality decision proper to them.
    Ensures(Implies(is_numeric_kind(kind), Result() == numeric_eq))
    # An otherwise-uncategorised operand can match only a zero floating value,
    # and then the verdict is the negation of the operand's truth value; a
    # non-zero floating value is unequal to it.
    Ensures(Implies(is_other_kind(kind) and self_is_zero,
                    Result() == (not other_truthy)))
    Ensures(Implies(is_other_kind(kind) and not self_is_zero,
                    Result() == False))
    # post-conditions-end
    # impl-start
    if kind == 0:
        return False
    if kind == 1:
        return False
    if kind == 2:
        return numeric_eq
    if kind == 3:
        return numeric_eq
    if kind == 4:
        return numeric_eq
    if kind == 5:
        return numeric_eq
    if self_is_zero:
        return not other_truthy
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, sympy__sympy-20801 (nagini). 15 same-spec attacks + 1 positive control, all built by splicing ONLY the impl region of the frozen model.py (spec prefix/suffix confirmed byte-identical for every file before running). Work dir Every run: `python -m swebench_unified.adversary weakness nagini sympy__sympy-20801 <file>`, executed 3-at-a-time as concurrent background jobs.

POSITIVE CONTROL ctrl_gold.py (frozen gold impl verbatim): CANDIDATE (shares spec AND verifies, 12.5s) => control verifies.

REJECTED (exit 2, 'does not verify' - the spec rejected them), 13 of 15:
- atk_1 PREPATCH BUG re-encoded: zero short circuit hoisted to the FRONT (the base_commit dispatch order, so S(0.0)==S.false returns not S.false == True). REJECTED => prepatch_reproduced=True. This is the exact G-DIFF clause Implies(is_truth_value(kind), Result()==False).
- atk_2 DIVERGENCE `while True: pass` (the counterexample refinement.md A10 names as a prior pass's atk_7): REJECTED by Requires(MustTerminate(1)). Confirms the termination leg is load-bearing, not decorative.
- atk_3 VACUITY CONTROL `Assert(False)` prepended to a correct impl: REJECTED => the frozen precondition set (0<=kind<=6 plus MustTerminate) is SATISFIABLE, so the five Ensures clauses are not discharged vacuously. This is the control my memory note 'guarded self-calls can go vacuous' calls for.
- atk_4 EXCEPTIONAL EXIT: `raise ValueError()` on kind 5. Ensures constrains only normal termination, yet REJECTED (Nagini proves absence of the exception) => no partial-domain hole on the numeric fall-through.
- atk_5 BOUNDARY sign flip on the relocated block: kind 6 + zero float returns other_truthy instead of `not other_truthy`. REJECTED.
- atk_7 PARTIAL DOMAIN: kind 5 returns False instead of numeric_eq (the plausible 'a non-Float number never equals a Float' misreading). REJECTED => the A7 leg is pinned.
- atk_8 UNBOUNDED RECURSION: unguarded tail self-call. REJECTED by MustTerminate(1).
- atk_9 kind 0 returns numeric_eq (G-CONF's named negative control, here as a real impl). REJECTED.
- atk_10 IMPLICIT runtime error (empty-list index on the kind-1 path, no `raise` token at all). REJECTED.
- atk_11 kind 1 DEFERS to numeric_eq instead of False (drops the `if other.is_irrational: return False` early-out, so Float(0.0)==pi would consult delegated equality). REJECTED => the A3 leg is pinned.
- atk_12 relocated block loses its ZERO GUARD: returns `not other_truthy` for EVERY float, so Float(2.0)==Tuple() would become True. REJECTED => the A8 leg's guard is pinned by the fifth Ensures.
- atk_13 CONDITIONAL DIVERGENCE ON THE F2P WITNESS - the sharpest attack: every RETURNING path satisfies all five Ensures, and the impl diverges precisely on kind 0 + self_is_zero, i.e. exactly the `S(0.0) == S.false` shape the fix is about. Had this verified, its faithful patch would HANG the FAIL_TO_PASS test => BROKEN. REJECTED. Per my memory note, MustTerminate at the METHOD level (not just loop invariants) is what does this.
- atk_14 GUARDED SELF-CALL under a FEASIBLE guard (kind 6, non-zero float), no decreasing measure - distinct from atk_8 in that a measure check looking only at unguarded tail calls would miss it. REJECTED.

CANDIDATES (2) - both are CORRECT reshapes ('ungrounded-oracle echo' lane), and per the weakness protocol I materialized each one's FAITHFUL refined patch and RAN it through the official harness:
- atk_6.py (predicate-driven reshape: is_numeric_kind first, then is_other_kind with reversed nesting) -> patch atk_6.patch, `python do_resolve.py atk_6.patch atk_6` (harness.run_resolve, run_id sbu-audit-eq-sympy__sympy-20801-atk_6): completed=True RESOLVED=True, attempts=1, flaky=False.
- atk_15.py (single accumulated `result` boolean, no early returns) -> patch atk_15.patch, same command with tag atk_15: completed=True RESOLVED=True, attempts=1, flaky=False.
Both patches were smoke-tested on a base_commit worktree first and reproduce gold behaviour on all 12 discriminating pairs, including all four issue witnesses (S(0.0)==S.false, S.false==S(0.0), S(0)==S.false all False) and the relocated block's only surviving effect (Float(0.0)==Tuple() True, Float(2.0)==Tuple() False). So both are correct ECHOES of the gold patch, NOT weaknesses - verify=>correct held on both.

**WHY THE SPEC HAS NO VALUE-LEG HOLE:** the five Ensures clauses jointly determine Result() at EVERY point of the finite abstract domain (2 x 7 x 2 x 2 = 56): kinds 0,1 -> False; kinds 2-5 -> numeric_eq; kind 6 splits on self_is_zero into `not other_truthy` / False. There is no unconstrained combination left for a wrong impl to occupy, which is why every value-mutation attack (atk_1,5,7,9,11,12) is rejected and the only surviving degrees of freedom are non-value ones - divergence, exceptional exit, vacuity - each of which I attacked and found closed (atk_2,8,13,14 by MustTerminate; atk_4,10 by Nagini's error-freedom; atk_3 by satisfiable preconditions).

REFINEMENT.MD LEG AUDIT (A-legs, per instruction): 11 legs A0-A10, tagged I / R / R+I only - NO kind-3 (unexpressible-changed-op) step, consistent with mapping.md section 3 ('None consumed', empty axioms region, verified: model.py's axioms-start/axioms-end region is empty and meta.json axioms == []). There is no A-consumed leg, so there is no axiom trust point. The single A-REFERENCE is the deep dispatch model (refinement.md section C), checked by axiom_check.py / G-AX (recorded pass: 161 pairs, all kinds {0..6}).

I re-validated its correspondence claims independently against the real repo at base_commit: (a) A4's kind-2 reachability claim HOLDS - Catalan.is_irrational is None and EulerGamma.is_irrational is None (falsy), so both route to the delegate branch, while pi/E/GoldenRatio have is_irrational True and take kind 1, exactly as mapping.md section 2 states; (b) A2's disjointness holds - S.true/S.false are Boolean with is_Number False, bool(S.false) False; (c) A1/A8's `self_is_zero == (not self)` holds on Float, including Float(-0.0) and Float(0) (all `_mpf_` == (0,0,0,0), truthy False) while Float(1e-300) is correctly non-zero; (d) A8's concrete effect matches (Float(0.0)==Tuple() True, Float(2.0)==Tuple() False); (e) kinds 5 vs 6 split as claimed (oo/-oo/nan is_Number True -> kind 5; zoo/I/sqrt(2)/Tuple is_Number False -> kind 6). Every A-leg's correspondence to the real callee holds.

ONE DOCUMENTATION NIT (not a fidelity defect, no gate impact, reported for completeness): axiom_check.py line ~128 comments `Symbol("x")` as '# kind 6 (not a number)', but sympy's Symbol has Boolean in its MRO (Symbol -> AtomicExpr -> Atom -> Expr -> Boolean -> Basic), so isinstance(Symbol('x'), Boolean) is True and classify() actually returns kind 0 for it. The check is still SOUND - classify() reads exactly the facet the real dispatch reads (isinstance(other, Boolean)), so model and real code agree on this operand either way, and the real code likewise takes its Boolean branch; only the inline comment mislabels the kind. Kind 6 remains genuinely exercised by Tuple(1,2), sqrt(2), I and zoo, so G-AX's all-kinds coverage claim is unaffected.

**VERDICT:** SOUND (advisory). 15 attacks encoded and all 15 reached a verifier verdict; 13 rejected by the spec; 2 candidates were correct echoes whose materialized faithful patches BOTH resolved under the official harness (executed, not speculated); positive control verifies; prepatch bug reproduced and rejected. No verifying wrong implementation exists among the probes, so no verify-not-implies-correct break was found. The prior recorded G-EQ fail was 'INCONCLUSIVE - 0 admissible attacks of 0 submitted' (an agent that never ran, per meta.json), not a measured defect.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_15.py` |

**Non-vacuity.** The positive control `ctrl_gold.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_gold.py`

```python
"""Twin-artifact model for sympy__sympy-20801.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Equality of an exact floating value against an already-sympified operand is
  determined by WHAT the operand is. The operand falls into one of a small
  number of kinds, and the equality verdict is determined by that kind:

    * a logical truth value (one of the two symbolic booleans) is NEVER equal to
      a floating value: the result is False, irrespective of the floating
      value — in particular a floating value that happens to be zero is still
      unequal to either symbolic boolean;
    * an irrational named constant is never equal to a floating value (False);
    * a rational named constant, a rational number, or another floating value
      compares by the numeric-equality decision proper to that kind;
    * any other numeric operand compares by the numeric-equality decision;
    * an operand that is none of the above (neither a number nor a logical truth
      value) is equal to the floating value exactly when the floating value is
      zero and the operand is falsy; otherwise the result is False.

The operand is abstracted by an integer kind code over these cases; two further
observations of the operand are carried explicitly: its truth value, and, for
the numeric kinds, the numeric-equality decision (a sub-decision proper to each
numeric kind, supplied as an opaque boolean). The floating value itself is
abstracted by whether it is zero. The result is the equality verdict.

The equality decision MUST terminate (a total-correctness obligation, carried
as MustTerminate in the precondition): the real dispatch is a bounded,
loop-free decision that always returns a verdict. Nagini verifies partial
correctness by default, so without the obligation a diverging implementation
(`while True: pass`) would satisfy every value postcondition vacuously — yet
its real counterpart is a Float.__eq__ that hangs every equality test and
does NOT resolve the instance.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# axioms-end

# pure-start
@Pure
def is_truth_value(kind: int) -> bool:
    """The operand is a symbolic logical truth value (kind 0)."""
    return kind == 0

@Pure
def is_irrational_const(kind: int) -> bool:
    """The operand is an irrational named constant (kind 1)."""
    return kind == 1

@Pure
def is_numeric_kind(kind: int) -> bool:
    """The operand is one of the numeric kinds whose verdict is the
    numeric-equality decision: a rational named constant, another floating
    value, a rational number, or any other number (kinds 2..5)."""
    return kind == 2 or kind == 3 or kind == 4 or kind == 5

@Pure
def is_other_kind(kind: int) -> bool:
    """The operand is none of the above: neither a number nor a logical truth
    value (kind 6)."""
    return kind == 6
# pure-end

def float_equals(self_is_zero: bool, kind: int, other_truthy: bool,
                 numeric_eq: bool) -> bool:
    # pre-conditions-start
    # `kind` ranges over the seven cases the dispatch distinguishes.
    Requires(0 <= kind and kind <= 6)
    # TERMINATION (total correctness): the real Float.__eq__ dispatch is a
    # bounded, loop-free decision — it always returns a verdict. Nagini
    # verifies partial correctness by default, so without this obligation a
    # diverging impl (`while True: pass`) satisfies every value postcondition
    # VACUOUSLY yet its real counterpart hangs every Float equality test
    # (the F2P run times out) and does not resolve. Any loop now needs a
    # decreasing measure; a bare infinite loop is rejected.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # A symbolic logical truth value is never equal to a floating value, even a
    # zero one — the verdict is False regardless of self_is_zero / other_truthy.
    Ensures(Implies(is_truth_value(kind), Result() == False))
    # An irrational named constant is never equal to a floating value.
    Ensures(Implies(is_irrational_const(kind), Result() == False))
    # The numeric kinds defer to the numeric-equality decision proper to them.
    Ensures(Implies(is_numeric_kind(kind), Result() == numeric_eq))
    # An otherwise-uncategorised operand can match only a zero floating value,
    # and then the verdict is the negation of the operand's truth value; a
    # non-zero floating value is unequal to it.
    Ensures(Implies(is_other_kind(kind) and self_is_zero,
                    Result() == (not other_truthy)))
    Ensures(Implies(is_other_kind(kind) and not self_is_zero,
                    Result() == False))
    # post-conditions-end
    # impl-start
    if kind == 0:
        return False
    if kind == 1:
        return False
    if kind == 2:
        return numeric_eq
    if kind == 3:
        return numeric_eq
    if kind == 4:
        return numeric_eq
    if kind == 5:
        return numeric_eq
    if self_is_zero:
        return not other_truthy
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, sympy__sympy-20801 (nagini). 15 same-spec attacks + 1 positive control, all built by splicing ONLY the impl region of the frozen model.py (spec prefix/suffix confirmed byte-identical for every file before running). Work dir Every run: `python -m swebench_unified.adversary weakness nagini sympy__sympy-20801 <file>`, executed 3-at-a-time as concurrent background jobs.

POSITIVE CONTROL ctrl_gold.py (frozen gold impl verbatim): CANDIDATE (shares spec AND verifies, 12.5s) => control verifies.

REJECTED (exit 2, 'does not verify' - the spec rejected them), 13 of 15:
- atk_1 PREPATCH BUG re-encoded: zero short circuit hoisted to the FRONT (the base_commit dispatch order, so S(0.0)==S.false returns not S.false == True). REJECTED => prepatch_reproduced=True. This is the exact G-DIFF clause Implies(is_truth_value(kind), Result()==False).
- atk_2 DIVERGENCE `while True: pass` (the counterexample refinement.md A10 names as a prior pass's atk_7): REJECTED by Requires(MustTerminate(1)). Confirms the termination leg is load-bearing, not decorative.
- atk_3 VACUITY CONTROL `Assert(False)` prepended to a correct impl: REJECTED => the frozen precondition set (0<=kind<=6 plus MustTerminate) is SATISFIABLE, so the five Ensures clauses are not discharged vacuously. This is the control my memory note 'guarded self-calls can go vacuous' calls for.
- atk_4 EXCEPTIONAL EXIT: `raise ValueError()` on kind 5. Ensures constrains only normal termination, yet REJECTED (Nagini proves absence of the exception) => no partial-domain hole on the numeric fall-through.
- atk_5 BOUNDARY sign flip on the relocated block: kind 6 + zero float returns other_truthy instead of `not other_truthy`. REJECTED.
- atk_7 PARTIAL DOMAIN: kind 5 returns False instead of numeric_eq (the plausible 'a non-Float number never equals a Float' misreading). REJECTED => the A7 leg is pinned.
- atk_8 UNBOUNDED RECURSION: unguarded tail self-call. REJECTED by MustTerminate(1).
- atk_9 kind 0 returns numeric_eq (G-CONF's named negative control, here as a real impl). REJECTED.
- atk_10 IMPLICIT runtime error (empty-list index on the kind-1 path, no `raise` token at all). REJECTED.
- atk_11 kind 1 DEFERS to numeric_eq instead of False (drops the `if other.is_irrational: return False` early-out, so Float(0.0)==pi would consult delegated equality). REJECTED => the A3 leg is pinned.
- atk_12 relocated block loses its ZERO GUARD: returns `not other_truthy` for EVERY float, so Float(2.0)==Tuple() would become True. REJECTED => the A8 leg's guard is pinned by the fifth Ensures.
- atk_13 CONDITIONAL DIVERGENCE ON THE F2P WITNESS - the sharpest attack: every RETURNING path satisfies all five Ensures, and the impl diverges precisely on kind 0 + self_is_zero, i.e. exactly the `S(0.0) == S.false` shape the fix is about. Had this verified, its faithful patch would HANG the FAIL_TO_PASS test => BROKEN. REJECTED. Per my memory note, MustTerminate at the METHOD level (not just loop invariants) is what does this.
- atk_14 GUARDED SELF-CALL under a FEASIBLE guard (kind 6, non-zero float), no decreasing measure - distinct from atk_8 in that a measure check looking only at unguarded tail calls would miss it. REJECTED.

CANDIDATES (2) - both are CORRECT reshapes ('ungrounded-oracle echo' lane), and per the weakness protocol I materialized each one's FAITHFUL refined patch and RAN it through the official harness:
- atk_6.py (predicate-driven reshape: is_numeric_kind first, then is_other_kind with reversed nesting) -> patch atk_6.patch, `python do_resolve.py atk_6.patch atk_6` (harness.run_resolve, run_id sbu-audit-eq-sympy__sympy-20801-atk_6): completed=True RESOLVED=True, attempts=1, flaky=False.
- atk_15.py (single accumulated `result` boolean, no early returns) -> patch atk_15.patch, same command with tag atk_15: completed=True RESOLVED=True, attempts=1, flaky=False.
Both patches were smoke-tested on a base_commit worktree first and reproduce gold behaviour on all 12 discriminating pairs, including all four issue witnesses (S(0.0)==S.false, S.false==S(0.0), S(0)==S.false all False) and the relocated block's only surviving effect (Float(0.0)==Tuple() True, Float(2.0)==Tuple() False). So both are correct ECHOES of the gold patch, NOT weaknesses - verify=>correct held on both.

**WHY THE SPEC HAS NO VALUE-LEG HOLE:** the five Ensures clauses jointly determine Result() at EVERY point of the finite abstract domain (2 x 7 x 2 x 2 = 56): kinds 0,1 -> False; kinds 2-5 -> numeric_eq; kind 6 splits on self_is_zero into `not other_truthy` / False. There is no unconstrained combination left for a wrong impl to occupy, which is why every value-mutation attack (atk_1,5,7,9,11,12) is rejected and the only surviving degrees of freedom are non-value ones - divergence, exceptional exit, vacuity - each of which I attacked and found closed (atk_2,8,13,14 by MustTerminate; atk_4,10 by Nagini's error-freedom; atk_3 by satisfiable preconditions).

REFINEMENT.MD LEG AUDIT (A-legs, per instruction): 11 legs A0-A10, tagged I / R / R+I only - NO kind-3 (unexpressible-changed-op) step, consistent with mapping.md section 3 ('None consumed', empty axioms region, verified: model.py's axioms-start/axioms-end region is empty and meta.json axioms == []). There is no A-consumed leg, so there is no axiom trust point. The single A-REFERENCE is the deep dispatch model (refinement.md section C), checked by axiom_check.py / G-AX (recorded pass: 161 pairs, all kinds {0..6}).

I re-validated its correspondence claims independently against the real repo at base_commit: (a) A4's kind-2 reachability claim HOLDS - Catalan.is_irrational is None and EulerGamma.is_irrational is None (falsy), so both route to the delegate branch, while pi/E/GoldenRatio have is_irrational True and take kind 1, exactly as mapping.md section 2 states; (b) A2's disjointness holds - S.true/S.false are Boolean with is_Number False, bool(S.false) False; (c) A1/A8's `self_is_zero == (not self)` holds on Float, including Float(-0.0) and Float(0) (all `_mpf_` == (0,0,0,0), truthy False) while Float(1e-300) is correctly non-zero; (d) A8's concrete effect matches (Float(0.0)==Tuple() True, Float(2.0)==Tuple() False); (e) kinds 5 vs 6 split as claimed (oo/-oo/nan is_Number True -> kind 5; zoo/I/sqrt(2)/Tuple is_Number False -> kind 6). Every A-leg's correspondence to the real callee holds.

ONE DOCUMENTATION NIT (not a fidelity defect, no gate impact, reported for completeness): axiom_check.py line ~128 comments `Symbol("x")` as '# kind 6 (not a number)', but sympy's Symbol has Boolean in its MRO (Symbol -> AtomicExpr -> Atom -> Expr -> Boolean -> Basic), so isinstance(Symbol('x'), Boolean) is True and classify() actually returns kind 0 for it. The check is still SOUND - classify() reads exactly the facet the real dispatch reads (isinstance(other, Boolean)), so model and real code agree on this operand either way, and the real code likewise takes its Boolean branch; only the inline comment mislabels the kind. Kind 6 remains genuinely exercised by Tuple(1,2), sqrt(2), I and zoo, so G-AX's all-kinds coverage claim is unaffected.

**VERDICT:** SOUND (advisory). 15 attacks encoded and all 15 reached a verifier verdict; 13 rejected by the spec; 2 candidates were correct echoes whose materialized faithful patches BOTH resolved under the official harness (executed, not speculated); positive control verifies; prepatch bug reproduced and rejected. No verifying wrong implementation exists among the probes, so no verify-not-implies-correct break was found. The prior recorded G-EQ fail was 'INCONCLUSIVE - 0 admissible attacks of 0 submitted' (an agent that never ran, per meta.json), not a measured defect.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** METHOD. Built the reference myself: `git worktree add --detach` from the sympy mirror at base_commit e11d3fed782146eebbffdc9ced0364b223b84b6c, then applied the gold relocation (delete `if not self: return not other` from before the `isinstance(other, Boolean)` test; re-insert it after the numeric branches, before `return False    # Float != non-Number`). Confirmed the post-patch dispatch order is Boolean -> NumberSymbol -> Float -> Rational -> Number -> zero-short-circuit -> False. A second worktree kept at base for the pre/post comparison.

The differential oracle copies the model's `# impl-start`/`# impl-end` region VERBATIM and inverts mapping.md S2 to build the bridge from real objects: kind by exactly the dispatch's own facets (0 = isinstance(other, Boolean); 1 = is_NumberSymbol and is_irrational; 2 = is_NumberSymbol and not is_irrational; 3 = is_Float; 4 = is_Rational; 5 = is_Number; 6 = else), self_is_zero = (not self), other_truthy = bool(other), and numeric_eq obtained by CALLING the repo's own unchanged sub-decisions (other.`__eq__`(self) for kinds 2/4, the `_mpf_` tuple compare for 3, mlib.mpf_eq(self.`_mpf_`, other.`_as_mpf_val`(self.`_prec`)) for 5) -- never reimplemented.

WHAT I CHECKED, AND WHAT WOULD HAVE BROKEN IT.

1. Value agreement. 798 pairs (14 Floats x 57 operands) and 100k fuzz: 0 mismatches, 0 non-bool real results. Branch coverage over the fuzz hit every impl branch: kind0=16204, kind1=6594, kind2=2895, kind3=8230, kind4=25921, kind5=6371, kind6+zero=12189, kind6+nonzero=19971. Floats included +0.0, -0.0, Float(0,3), Float(0,53), 1e300, 1e-300, 1e-1000000, and varied precisions (0.1 at prec 3/15/33) to stress the exact-mpf branch.

2. ABSTRACTION FUNCTIONALITY -- the check that actually earns the FAITHFUL. A kind code that merged two real operands with different real verdicts would make the postconditions over-strong on one of them. I grouped all 798 rows by the abstract point (self_is_zero, kind, other_truthy, numeric_eq) and required every real verdict in a group to agree: 24 of the 56 abstract points are realizable, 0 conflicts. The 24/56 figure independently reproduces the count mapping.md's G-CONF section claims, and the fuzz hit exactly the same 24 points -- the unrealizable 32 are the ones where kinds 0/1/6 would have to carry numeric_eq True, which no real pair produces.

3. Kind boundaries are the real ones, not a convenient fiction. Confirmed `Symbol` IS a Boolean subclass in sympy 1.8.dev, so Symbol('x') classifies as kind 0, not kind 6 -- and the real code agrees (Float(0.0) == Symbol('x') -> False both pre- and post-patch, since a Symbol is truthy the pre-patch short circuit also returned False; no divergence hides there). Confirmed the kind-2 branch is genuinely REACHABLE and not dead: Catalan.is_irrational is None and EulerGamma.is_irrational is None (falsy) so they route through `return other.__eq__(self)`, while pi/E/GoldenRatio have is_irrational True and take kind 1. Enumerated all 13 Number subclasses; the only failures were the abstract bases IntegerConstant()/RationalConstant() (no .p/.q), which are malformed objects the real code cannot evaluate either.

4. Sub-decision coercion. The model carries numeric_eq as a bool while the real branches return raw sub-results. I checked kinds 2/4/5 for any raw result that is not a plain bool or whose bool() differs from the real verdict: 0 anomalies across NumberSymbols, Rationals, Integers, and Integer(`10**50`).

5. Adversarial sweep for the exception vector. I mass-instantiated 978 Basic subclasses discovered by walking every sympy submodule (810 instantiated) plus a hand-built battery of infinite/symbolic sets, matrices, polys, quaternions, permutations, Range(0,oo), ProductSet, ImageSet, ConditionSet, PowerSet, sequences and NDimArrays, hunting for the one shape that could make the spec too strong: a kind-6 operand where bool(other) raises so the real code raises but the model returns a verdict. Exactly two survived (documented under diverging_input) plus one malformed ArrayComprehension(0). All are pre-existing and patch-invariant, so none is a faithfulness defect on the modeled delta.

6. Termination clause is not over-strong. `Requires(MustTerminate(1))` is discharged trivially by the real function: post-patch `Float.__eq__` is straight-line -- no loop, no recursion, returns a verdict on every in-domain operand. I read the body directly to confirm. So the obligation costs the real code nothing while ruling out the vacuous `while True: pass` impl, which is the correct direction (it makes the spec harder to satisfy for a WRONG impl, not for the real one).

**RESIDUAL RISK I AM DECLARING.** mapping.md S2 excludes only the NotImplemented/SympifyError path from the modeled domain; it does not state that operands with no observable Python truth value are also excluded. That is a documentation gap in the domain statement, not a spec-too-strong defect -- the excluded inputs are ones the real function does not decide either, in both the pre- and post-patch orderings. Everything else the spec asserts, the real gold-patched callee does.

**BUNDLE CONTEXT.** The recorded panel_2 verdict for this cell was "INCONCLUSIVE (no verdict submitted)", i.e. a prior run ended in prose instead of a submission. This submission is a fresh, independently measured review, not a re-judging of any retained attack label.

Counterexample / evidence:

```
None. No attack was constructed because no input was found on which the modeled function disagrees with the real gold-patched callee. Positive control confirming the harness has teeth: the SAME differential harness run against the BASE (unpatched) worktree flags the patch delta immediately -- base `Float(0.0) == S.false` -> True while the model (and the patched repo) -> False. Per the gate's instruction this base divergence is NOT reported as unfaithfulness: it is exactly the delta the patch introduces, and the model correctly describes the FIXED behavior. Model verifies under the pinned verifier: `scripts/nagini_verify.sh` -> "Verification successful" (12.93s, exit 0). Spec integrity: `adversary same-spec nagini sympy__sympy-20801` -> "SAME -- attack shares the bundle's exact specification" (exit 0) on a verbatim copy of the shipped model.py, so the spec region I audited is byte-identical to the bundle's.
```

**METHOD.** Built the reference myself: `git worktree add --detach` from the sympy mirror at base_commit e11d3fed782146eebbffdc9ced0364b223b84b6c, then applied the gold relocation (delete `if not self: return not other` from before the `isinstance(other, Boolean)` test; re-insert it after the numeric branches, before `return False    # Float != non-Number`). Confirmed the post-patch dispatch order is Boolean -> NumberSymbol -> Float -> Rational -> Number -> zero-short-circuit -> False. A second worktree kept at base for the pre/post comparison.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker 3 (leakage / gold-reconstruction) on sympy__sympy-20801 nagini. Verdict NO-LEAKAGE.

GOLD EDIT (what must NOT be reconstructable): relocate the two-line block `if not self: return not other` from immediately after the sympify preamble (before the `isinstance(other, Boolean)` test) to after all boolean/number branches, just before `return False    # Float != non-Number`. Dispatch order changes [zero-short-circuit] -> Boolean -> NumberSymbol -> Float -> Rational -> Number -> False  ==>  Boolean -> NumberSymbol -> Float -> Rational -> Number -> [zero-short-circuit] -> False.

1. **MECHANICAL SCREEN PASSES.** swebench_unified.leakage.screen(model.py, nagini, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. Verified against the real frozen row from data/swe_bench_verified/test.jsonl (problem_statement only; hints_text is EMPTY for this instance, so the hints-vs-PS trap cannot arise here).

2. SCREEN IS LIVE (3 positive controls, not a rubber stamp). Injecting each defect into the docstring/comments is caught: (a) 'This fixes the buggy behaviour' -> L3 narration 'fixes'; (b) '# if not self: return not other' -> L1 gold-patch line reproduced (x2); (c) 'sympy/core/numbers.py' -> L2 patched file path. So the zero-failure result on the real bundle is a measurement, not a silent no-op.

3. HAND CHECKS the screen cannot make. Note `_patch_changed_symbols`(gold_patch) == EMPTY SET (`__eq__` is in `_COMMON_NONDISTINCTIVE`), so the L2/L5 symbol check is VACUOUS on this instance -- I checked by hand rather than trusting it. Spec view (106 lines) contains: NO diff marker, NO gold-diff line, NO `sympy/core/numbers.py` and NO dotted module path, NO hidden-test name (`test_zero_not_false` absent), NO `S(0.0)`/`S.false`/`Boolean`/`is_NumberSymbol`/`is_Float`/`is_Rational`/`is_Number`/`_mpf_`/`mlib`/`_sympify` token.

4. **NO EDIT/ORDERING VOCABULARY.** Grepped all 106 spec-view lines case-insensitively for move, relocat, reorder, order, position, before, after, short circuit, short-circuit, swap, hunk, delete, insert, revert, first, last, precede, earlier, later, instead, 'no longer', 'used to', currently -> ZERO hits. The edit is a pure REORDERING, so ordering vocabulary is exactly the leak vector, and it is absent. The spec states each kind's verdict as an independent implication (Implies(is_truth_value(kind), Result()==False), etc.) -- a set of unordered behavioural clauses, never a dispatch sequence.

5. **THE DIFF NARRATION IS NOT CONSUMER-VISIBLE.** refinement.md DOES quote the gold hunk verbatim and narrates 'relocates one two-line block', 'DELETES', 'RE-INSERTS', the before/after dispatch order, and the A2-vs-A8 ordering as 'the whole content of the fix' -- but refinement.md/mapping.md/patch.diff/model_prepatch.py are NOT in the consumer view. Traced eval/prompts.py `_spec_block` + eval/dataset.py as_dict: the consumer receives ONLY spec_view + modeled_functions + float_encoding, with WITHHELD_FIELDS = (patch, test_patch, FAIL_TO_PASS, PASS_TO_PASS). Bundle-internal audit prose stays out.

6. THE ONE CANDIDATE, ADJUDICATED: `Float.__eq__` appears in the spec view (lines 32, 79, 83) and neither 'Float' nor '`__eq__`' occurs in problem_statement. Not a leak: it is exactly the SANCTIONED edit-localization the harness hands the consumer in the SAME prompt block -- nagini sets modeled_functions_from_meta=True, so `_spec_block` renders meta.json's repo_symbol `sympy.core.numbers.Float.__eq__` and repo_location `sympy/core/numbers.py:1383` verbatim, and mode 0 gets the identical localization with no spec at all. Naming the modeled function reveals WHERE the fix goes (deliberately provided, information-environment parity) and not WHAT the edit is. Localization != gold edit.

7. RECONSTRUCTION TEST -- THE DECISIVE EVIDENCE. (a) The kind taxonomy is NOT new information: I read numbers.py at base_commit e11d3fed (git show ...:sympy/core/numbers.py, lines 1383-1410) and the full dispatch -- Boolean / NumberSymbol+is_irrational / is_Float / is_Rational / is_Number / `return False    # Float != non-Number` -- is ALREADY THERE VERBATIM, pre-patch, in the source the solver reads. The spec view's kinds 0..6 are a de-narrated abstraction of a dispatch that already exists, so enumerating them leaks nothing the solver cannot read off the unpatched file. (b) The only genuinely new normative content is 'a symbolic boolean is never equal to a floating value, even a zero one' -- which IS the public issue: the problem_statement reports `S(0.0) == S.false` -> True as the defect and exhibits `S.false == S(0.0)` -> False, `S(0) == S.false` -> False, `S.false == S(0)` -> False, making the desired verdict False for a zero float public. (c) MACHINE-CHECKED non-uniqueness: I wrote atk_leak20801.py which does NOT perform the gold relocation -- it keeps the zero short-circuit in its PRE-PATCH FIRST position and instead GUARDS it (`if self_is_zero and not is_truth_value(kind) and not is_numeric_kind(kind) and not is_irrational_const(kind)`), collapsing the six dispatch branches into three. `adversary same-spec nagini sympy__sympy-20801` -> exit 0 ('SAME -- attack shares the bundle's exact specification'); `scripts/nagini_verify.sh` -> exit 0 ('Verification successful'). So the spec view admits a materially DIFFERENT edit shape and does not encode 'move the two-line block after the Number branches'. The gold diff is NOT reconstructable from the spec view.

**CONCLUSION:** the spec view states the abstract behavioural contract the issue demands over a taxonomy already visible in the unpatched source, adds nothing from hints_text (which is empty), quotes no gold line, names no patched path or hidden test, uses no ordering/edit vocabulary, and provably does not pin the gold edit shape. NO-LEAKAGE.

OUT-OF-SCOPE OBSERVATIONS (not leakage; for whoever owns provenance): (i) meta.json region_hashes are STALE -- computed pre-conditions sha 7b0ba3427bd15627... vs recorded 66144d1dc27fa91b..., and spec_view 77800440256cc4d1... vs recorded 44ecee0069ae3097... (impl/post-conditions/pure DO match), so model.py's pre-conditions region (apparently the MustTerminate comment block) was edited after the hashes were frozen. I screened the ACTUAL current spec view, so my verdict is unaffected. (ii) The MustTerminate comment mentions 'the F2P run times out' and 'does not resolve' -- harness/verification meta-commentary about a diverging impl, not the gold edit and not a hidden-test name; it survives the L3 narration list and reveals nothing about the relocation, so I did not treat it as a finding, though it is stylistically gate-adjacent. (iii) verdict.md records all four P2 roles as fail/INCONCLUSIVE including panel_3 'no verdict submitted' -- this submission supersedes that for role 4.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
