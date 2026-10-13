# P2 adversarial audit — sympy__sympy-13974

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -84,13 +83,6 @@
     # (``base ** 1`` is the factor itself), so this operation is reached only for
     # a genuine, non-identity exponent.
     Requires(exp != 1)
-    # The distribution must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(args), 1 / 2))
@@ -112,16 +104,12 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(args))
         Invariant(len(result) == len(args) - i)
-        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
+        Invariant(ToSeq(result) == ToSeq(args).drop(i))
         # invariants-end
         e = args[i - 1]
         Assert(ToSeq(args).drop(i - 1)[0] == e)
         Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
-        result = [pow_expr(e, exp)] + result
+        result = [e] + result
         i = i - 1
     return result
     # impl-end
@@ -136,12 +124,6 @@
     # (`is_pow_of_tp` False). A power node never carries the identity exponent.
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(Implies(is_pow_of_tp, exp != 1))
-    # The simplification must COMPLETE (total correctness): without this
-    # obligation every Ensures below is claimed only of runs that reach the
-    # return, so an implementation that never gets there satisfies the whole
-    # postcondition vacuously. Level 3 is strictly above the callee it delegates
-    # to (power_of_collection at 2).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -165,10 +147,6 @@
         Invariant(0 <= i and i <= len(factors))
         Invariant(len(result) == len(factors) - i)
         Invariant(ToSeq(result) == ToSeq(factors).drop(i))
-        # At most i + 1 passes remain: the passthrough counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = factors[i - 1]
         Assert(ToSeq(factors).drop(i - 1)[0] == e)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -84,13 +83,6 @@
     # (``base ** 1`` is the factor itself), so this operation is reached only for
     # a genuine, non-identity exponent.
     Requires(exp != 1)
-    # The distribution must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(args), 1 / 2))
@@ -105,24 +97,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(args)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(args), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(args))
-        Invariant(len(result) == len(args) - i)
-        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        e = args[i - 1]
-        Assert(ToSeq(args).drop(i - 1)[0] == e)
-        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
-        result = [pow_expr(e, exp)] + result
-        i = i - 1
     return result
     # impl-end
 
@@ -136,12 +110,6 @@
     # (`is_pow_of_tp` False). A power node never carries the identity exponent.
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(Implies(is_pow_of_tp, exp != 1))
-    # The simplification must COMPLETE (total correctness): without this
-    # obligation every Ensures below is claimed only of runs that reach the
-    # return, so an implementation that never gets there satisfies the whole
-    # postcondition vacuously. Level 3 is strictly above the callee it delegates
-    # to (power_of_collection at 2).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -165,10 +133,6 @@
         Invariant(0 <= i and i <= len(factors))
         Invariant(len(result) == len(factors) - i)
         Invariant(ToSeq(result) == ToSeq(factors).drop(i))
-        # At most i + 1 passes remain: the passthrough counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = factors[i - 1]
         Assert(ToSeq(factors).drop(i - 1)[0] == e)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -84,13 +83,6 @@
     # (``base ** 1`` is the factor itself), so this operation is reached only for
     # a genuine, non-identity exponent.
     Requires(exp != 1)
-    # The distribution must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(args), 1 / 2))
@@ -105,6 +97,8 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    if len(args) == 0:
+        return result
     i = len(args)
     while i > 0:
         # invariants-start
@@ -112,16 +106,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(args))
         Invariant(len(result) == len(args) - i)
-        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
+        Invariant(ToSeq(result) == ToSeq(args).drop(i))
         # invariants-end
         e = args[i - 1]
-        Assert(ToSeq(args).drop(i - 1)[0] == e)
-        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
-        result = [pow_expr(e, exp)] + result
+        result = [e] + result
         i = i - 1
     return result
     # impl-end
@@ -136,12 +124,6 @@
     # (`is_pow_of_tp` False). A power node never carries the identity exponent.
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(Implies(is_pow_of_tp, exp != 1))
-    # The simplification must COMPLETE (total correctness): without this
-    # obligation every Ensures below is claimed only of runs that reach the
-    # return, so an implementation that never gets there satisfies the whole
-    # postcondition vacuously. Level 3 is strictly above the callee it delegates
-    # to (power_of_collection at 2).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -165,10 +147,6 @@
         Invariant(0 <= i and i <= len(factors))
         Invariant(len(result) == len(factors) - i)
         Invariant(ToSeq(result) == ToSeq(factors).drop(i))
-        # At most i + 1 passes remain: the passthrough counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = factors[i - 1]
         Assert(ToSeq(factors).drop(i - 1)[0] == e)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -84,13 +83,6 @@
     # (``base ** 1`` is the factor itself), so this operation is reached only for
     # a genuine, non-identity exponent.
     Requires(exp != 1)
-    # The distribution must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(args), 1 / 2))
@@ -106,17 +98,13 @@
     # impl-start
     result = []  # type: List[int]
     i = len(args)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(args), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(args))
+        Invariant(1 <= i and i <= len(args))
         Invariant(len(result) == len(args) - i)
         Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = args[i - 1]
         Assert(ToSeq(args).drop(i - 1)[0] == e)
@@ -136,12 +124,6 @@
     # (`is_pow_of_tp` False). A power node never carries the identity exponent.
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(Implies(is_pow_of_tp, exp != 1))
-    # The simplification must COMPLETE (total correctness): without this
-    # obligation every Ensures below is claimed only of runs that reach the
-    # return, so an implementation that never gets there satisfies the whole
-    # postcondition vacuously. Level 3 is strictly above the callee it delegates
-    # to (power_of_collection at 2).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -165,10 +147,6 @@
         Invariant(0 <= i and i <= len(factors))
         Invariant(len(result) == len(factors) - i)
         Invariant(ToSeq(result) == ToSeq(factors).drop(i))
-        # At most i + 1 passes remain: the passthrough counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = factors[i - 1]
         Assert(ToSeq(factors).drop(i - 1)[0] == e)
```

Attack 5 — `atk_5.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -84,13 +83,6 @@
     # (``base ** 1`` is the factor itself), so this operation is reached only for
     # a genuine, non-identity exponent.
     Requires(exp != 1)
-    # The distribution must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(args), 1 / 2))
@@ -105,24 +97,12 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(args)
-    while i > 0:
+    while True:
         # invariants-start
         Invariant(Acc(list_pred(args), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(args))
-        Invariant(len(result) == len(args) - i)
-        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        e = args[i - 1]
-        Assert(ToSeq(args).drop(i - 1)[0] == e)
-        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
-        result = [pow_expr(e, exp)] + result
-        i = i - 1
+        result = result
     return result
     # impl-end
 
@@ -136,12 +116,6 @@
     # (`is_pow_of_tp` False). A power node never carries the identity exponent.
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(Implies(is_pow_of_tp, exp != 1))
-    # The simplification must COMPLETE (total correctness): without this
-    # obligation every Ensures below is claimed only of runs that reach the
-    # return, so an implementation that never gets there satisfies the whole
-    # postcondition vacuously. Level 3 is strictly above the callee it delegates
-    # to (power_of_collection at 2).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -165,10 +139,6 @@
         Invariant(0 <= i and i <= len(factors))
         Invariant(len(result) == len(factors) - i)
         Invariant(ToSeq(result) == ToSeq(factors).drop(i))
-        # At most i + 1 passes remain: the passthrough counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = factors[i - 1]
         Assert(ToSeq(factors).drop(i - 1)[0] == e)
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -84,13 +83,6 @@
     # (``base ** 1`` is the factor itself), so this operation is reached only for
     # a genuine, non-identity exponent.
     Requires(exp != 1)
-    # The distribution must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(args), 1 / 2))
@@ -113,10 +105,6 @@
         Invariant(0 <= i and i <= len(args))
         Invariant(len(result) == len(args) - i)
         Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = args[i - 1]
         Assert(ToSeq(args).drop(i - 1)[0] == e)
@@ -136,12 +124,6 @@
     # (`is_pow_of_tp` False). A power node never carries the identity exponent.
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(Implies(is_pow_of_tp, exp != 1))
-    # The simplification must COMPLETE (total correctness): without this
-    # obligation every Ensures below is claimed only of runs that reach the
-    # return, so an implementation that never gets there satisfies the whole
-    # postcondition vacuously. Level 3 is strictly above the callee it delegates
-    # to (power_of_collection at 2).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -154,7 +136,7 @@
     Ensures(Implies(not is_pow_of_tp, ToSeq(Result()) == ToSeq(factors)))
     # post-conditions-end
     # impl-start
-    if is_pow_of_tp:
+    if not is_pow_of_tp:
         return power_of_collection(factors, exp)
     result = []  # type: List[int]
     i = len(factors)
@@ -165,14 +147,8 @@
         Invariant(0 <= i and i <= len(factors))
         Invariant(len(result) == len(factors) - i)
         Invariant(ToSeq(result) == ToSeq(factors).drop(i))
-        # At most i + 1 passes remain: the passthrough counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = factors[i - 1]
-        Assert(ToSeq(factors).drop(i - 1)[0] == e)
-        Assert(ToSeq(factors).drop(i - 1).drop(1) == ToSeq(factors).drop(i))
         result = [e] + result
         i = i - 1
     return result
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -84,13 +83,6 @@
     # (``base ** 1`` is the factor itself), so this operation is reached only for
     # a genuine, non-identity exponent.
     Requires(exp != 1)
-    # The distribution must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(args), 1 / 2))
@@ -105,24 +97,18 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(args)
-    while i > 0:
+    i = 0
+    while i < len(args):
         # invariants-start
         Invariant(Acc(list_pred(args), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(args))
-        Invariant(len(result) == len(args) - i)
-        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
+        Invariant(len(result) == i)
+        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).take(i), exp))
         # invariants-end
-        e = args[i - 1]
-        Assert(ToSeq(args).drop(i - 1)[0] == e)
-        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
-        result = [pow_expr(e, exp)] + result
-        i = i - 1
+        e = args[i]
+        result = result + [pow_expr(e, exp)]
+        i = i + 1
     return result
     # impl-end
 
@@ -136,12 +122,6 @@
     # (`is_pow_of_tp` False). A power node never carries the identity exponent.
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(Implies(is_pow_of_tp, exp != 1))
-    # The simplification must COMPLETE (total correctness): without this
-    # obligation every Ensures below is claimed only of runs that reach the
-    # return, so an implementation that never gets there satisfies the whole
-    # postcondition vacuously. Level 3 is strictly above the callee it delegates
-    # to (power_of_collection at 2).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -165,10 +145,6 @@
         Invariant(0 <= i and i <= len(factors))
         Invariant(len(result) == len(factors) - i)
         Invariant(ToSeq(result) == ToSeq(factors).drop(i))
-        # At most i + 1 passes remain: the passthrough counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = factors[i - 1]
         Assert(ToSeq(factors).drop(i - 1)[0] == e)
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -84,13 +83,6 @@
     # (``base ** 1`` is the factor itself), so this operation is reached only for
     # a genuine, non-identity exponent.
     Requires(exp != 1)
-    # The distribution must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(args), 1 / 2))
@@ -113,10 +105,6 @@
         Invariant(0 <= i and i <= len(args))
         Invariant(len(result) == len(args) - i)
         Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = args[i - 1]
         Assert(ToSeq(args).drop(i - 1)[0] == e)
@@ -136,12 +124,6 @@
     # (`is_pow_of_tp` False). A power node never carries the identity exponent.
     Requires(Acc(list_pred(factors), 1 / 2))
     Requires(Implies(is_pow_of_tp, exp != 1))
-    # The simplification must COMPLETE (total correctness): without this
-    # obligation every Ensures below is claimed only of runs that reach the
-    # return, so an implementation that never gets there satisfies the whole
-    # postcondition vacuously. Level 3 is strictly above the callee it delegates
-    # to (power_of_collection at 2).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -154,8 +136,6 @@
     Ensures(Implies(not is_pow_of_tp, ToSeq(Result()) == ToSeq(factors)))
     # post-conditions-end
     # impl-start
-    if is_pow_of_tp:
-        return power_of_collection(factors, exp)
     result = []  # type: List[int]
     i = len(factors)
     while i > 0:
@@ -165,10 +145,6 @@
         Invariant(0 <= i and i <= len(factors))
         Invariant(len(result) == len(factors) - i)
         Invariant(ToSeq(result) == ToSeq(factors).drop(i))
-        # At most i + 1 passes remain: the passthrough counts DOWN over the input
-        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = factors[i - 1]
         Assert(ToSeq(factors).drop(i - 1)[0] == e)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.py`

```python
"""Twin-artifact model for sympy__sympy-13974.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tensor product is an ordered collection of factor expressions. Two related
  operations are specified:

  (1) Raising a tensor product to an exponent (``power_of_collection``). Given the
      ordered factors and a single exponent, the result is a tensor product with:
        * the same number of factors as the input, in the same order;
        * factor k equal to the power expression that raises input factor k to the
          given exponent (the value of the binary power map on that factor);
        * the same exponent used for every factor.

  (2) Simplifying ONE non-commutative factor of a product when that factor is such
      a power of a tensor product (``simp_pow_factor``). The simplifier replaces
      the power-of-a-tensor-product by its per-factor distribution (operation 1);
      a factor that is already a bare tensor product is returned unchanged; the
      decision is driven solely by whether the factor is a power whose base is a
      tensor product. This is the routing that lets the per-factor distribution be
      reached for a tensor-product power appearing as a factor of a product, not
      only as the whole expression.

A tensor product cannot be expressed in Nagini's fragment, so its content that the
operations touch — the ordered list of factor expressions — is the carrier
(``List[int]`` of opaque expression handles), and the exponent is one opaque
handle. The binary power map that takes one factor and one exponent to a power
expression is the single axiomatized callee (``pow_expr``), a deterministic map;
its soundness is checked out-of-band by axiom_check.py (G-AX). The specification of
a distributed result is the element-wise image of that map, carried by ``PSeq[int]``
via ``ToSeq`` (the front-recursive fold ``pointwise_pow``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def pow_expr(base: int, exp: int) -> int:
    """The binary power map: the handle of the power expression that raises one
    factor handle ``base`` to the exponent handle ``exp`` (the symbolic
    ``base ** exp``), as a deterministic map over expression handles. Two
    properties are relied upon:

      * determinism / functionality — the result depends only on (base, exp), so
        every reader of the map sees the SAME power handle for the same
        (factor, exponent) pair;
      * non-triviality away from the identity exponent — when ``exp`` is not the
        identity exponent (the reserved handle ``1`` for the exponent one, which
        a power node never carries because ``base ** 1`` is the factor itself),
        the power expression is distinct from the factor: ``Result() != base``.

    The identity exponent is excluded by the precondition; on it the real power
    map returns the factor unchanged, so the axiom does not over-claim there.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(exp != 1)
    Ensures(Result() != base)
# axioms-end


# pure-start
@Pure
def pointwise_pow(s: PSeq[int], exp: int) -> PSeq[int]:
    """The factor list of a distributed result: the element-wise image of the
    power map on the factors of ``s`` at exponent ``exp``, in order.
    Front-recursive so a single unfold is available per loop step."""
    Requires(exp != 1)
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(pow_expr(s[0], exp)) + pointwise_pow(s.drop(1), exp)
# pure-end


def power_of_collection(args: List[int], exp: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(args), 1 / 2))
    # The identity exponent (handle 1) is excluded: a power node never carries it
    # (``base ** 1`` is the factor itself), so this operation is reached only for
    # a genuine, non-identity exponent.
    Requires(exp != 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(args), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result has the same number of factors as the input, in the same order.
    Ensures(len(Result()) == len(args))
    # Factor k of the result is the value of the power map on input factor k at
    # the given exponent. Stated as the element-wise image over the actual input
    # factors, so the result is tied to a structural property of the input
    # carrier (its k-th factor), not to any constant or answer-key value.
    Ensures(ToSeq(Result()) == pointwise_pow(ToSeq(args), exp))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(args)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(args), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(args))
        Invariant(len(result) == len(args) - i)
        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
        # invariants-end
        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        result = [pow_expr(e, exp)] + result
        i = i - 1
    return result
    # impl-end


def simp_pow_factor(is_pow_of_tp: bool, factors: List[int], exp: int) -> List[int]:
    # pre-conditions-start
    # A single non-commutative factor of a product whose base is a tensor product:
    # `factors` are the tensor-product factors of that base (in order). The factor
    # is EITHER a power of that tensor product (`is_pow_of_tp` True), in which case
    # `exp` is the power's exponent, OR the bare tensor product itself
    # (`is_pow_of_tp` False). A power node never carries the identity exponent.
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Implies(is_pow_of_tp, exp != 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(factors))
    # Routing decision: a power-of-tensor-product factor is replaced by its
    # per-factor distribution (each base factor raised to the exponent); a bare
    # tensor-product factor passes through unchanged (factor k stays factor k).
    Ensures(Implies(is_pow_of_tp, ToSeq(Result()) == pointwise_pow(ToSeq(factors), exp)))
    Ensures(Implies(not is_pow_of_tp, ToSeq(Result()) == ToSeq(factors)))
    # post-conditions-end
    # impl-start
    if is_pow_of_tp:
        return power_of_collection(factors, exp)
    result = []  # type: List[int]
    i = len(factors)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(factors))
        Invariant(len(result) == len(factors) - i)
        Invariant(ToSeq(result) == ToSeq(factors).drop(i))
        # invariants-end
        e = factors[i - 1]
        Assert(ToSeq(factors).drop(i - 1)[0] == e)
        Assert(ToSeq(factors).drop(i - 1).drop(1) == ToSeq(factors).drop(i))
        result = [e] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-13974 (nagini). The frozen spec pins BOTH operations tightly: power_of_collection must satisfy len(Result())==len(args) AND ToSeq(Result())==pointwise_pow(ToSeq(args),exp); simp_pow_factor must distribute on is_pow_of_tp (==pointwise_pow(ToSeq(factors),exp)) and pass through otherwise (==ToSeq(factors)). Only the two impl regions are editable; axioms/@Pure/Requires/Ensures/invariant-structure spec bytes are frozen. Every attack confirmed SAME-spec via `adversary same-spec` (no JVM). weakness/verify runs executed in the swebench-lean env with SBU_BENCHMARK_DIR=benchmark-verified, scheduled in background batches of <=3 JVMs.

EXACT COMMANDS (per file): python -m swebench_unified.adversary same-spec nagini sympy__sympy-13974 <path>; python -m swebench_unified.adversary weakness nagini sympy__sympy-13974 <path>; bash scripts/nagini_verify.sh <path>.

### ATTACKS (all copy model.py editing ONLY the impl region; same-spec=SAME for all 8):
- atk_1 (prepatch bug / identity fold in power_of_collection): weakness EXIT=2 NOT-A-COUNTEREXAMPLE. nagini_verify: 'Postcondition of power_of_collection might not hold. Assertion (ToSeq(Result()) == pointwise_pow(ToSeq(args), exp)) might not hold.' Spec senses the change exactly (G-DIFF reproduced) -> prepatch_reproduced=true.
- atk_2 (return empty list; wrong length+seq): weakness EXIT=2, does not verify.
- atk_3 (partial-domain: correct on empty input, identity fold otherwise): weakness EXIT=2, does not verify.
- atk_4 (boundary off-by-one: while i>1, skips last factor, otherwise faithful distribute): weakness EXIT=2, does not verify.
- atk_5 (control-flow-effect: non-terminating `while True`): weakness EXIT=2; nagini_verify: 'Translation failed / Type error: dead.code' -> NOT JUDGED: the front end refused the program (the return after `while True` is statically unreachable), so the spec never ruled on it and it counts in neither tally; the attack SHAPE is unexpressible in nagini's fragment and did not test the spec's method-level `MustTerminate`.
- atk_6 (routing swap: distribute on the NOT-is_pow_of_tp branch): weakness EXIT=2; nagini_verify: 'The precondition of method power_of_collection might not hold. Assertion (exp != 1) might not hold.' -> rejected.
- atk_7 (ungrounded-oracle-echo / alternative CORRECT forward-loop distribute): weakness EXIT=2 does not verify (front-recursive pointwise_pow admits only the backward fold's proof shape; a same-behaviour forward variant fails to verify -> proof-engineering, not a spec weakness).
- atk_8 (routing: always-passthrough ignoring is_pow_of_tp): weakness EXIT=2; nagini_verify: 'Postcondition of simp_pow_factor might not hold. Assertion Implies(is_pow_of_tp, (ToSeq(Result()) == pointwise_pow(ToSeq(factors), exp))) might not hold.' -> the is_pow_of_tp distribution leg is genuinely pinned.

POSITIVE CONTROL pos.py (exact original impl): weakness EXIT=0 CANDIDATE (shares spec AND verifies) -> the intended impl verifies as expected.

RESOLVE RUNS: none required. No wrong impl produced a CANDIDATE (verify+same-spec) => there is NO verifying-but-wrong impl whose faithful refined patch could fail resolve. The only CANDIDATE is the correct positive control. verify_completed was true for all runs (the code distinguishes timeouts/infra as inconclusive; none occurred) so the SOUND verdict rests on genuine rejections, not fail-closed artifacts.

A-LEG / refinement.md audit: The sole consumed axiom pow_expr maps to the UNCHANGED callee `b ** e.exp` (real sympy Pow); mapping.md §3 correspondence is faithful (the patch only moves WHERE `**` is applied, per tensor factor, and does not change the constructor). It is correctly tagged A-consumed. Both genuinely-changed operations are modeled DEEPLY: the exponent distribution via the spelled-out front-recursive pointwise_pow fold consumed in power_of_collection (A3), and the routing decision via simp_pow_factor as concrete branches delegating to the deep power_of_collection (B3) + an identity fold (B4). No `tensor_product_simp_Pow` or `tensor_product_simp_Mul` oracle axiom exists. Every refinement leg is R / A-consumed / I — NO kind-3 (unexpressible-changed-op) leg. The axiom precondition Requires(exp!=1) is weakest-sufficient and faithful (a Pow node never carries exponent 1); axiom_check.py exercises the identity boundary (base**1==base) and asserts non-triviality only for exp!=1, so the axiom does not over-claim.

CONCLUSION: The spec discriminates every distinct wrong impl class attempted (prepatch, empty, partial-domain, boundary, control-flow-effect, oracle-echo, routing-swap, routing-passthrough) while admitting the correct impl. verify => correct holds for this bundle. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.py`

```python
"""Twin-artifact model for sympy__sympy-13974.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tensor product is an ordered collection of factor expressions. Two related
  operations are specified:

  (1) Raising a tensor product to an exponent (``power_of_collection``). Given the
      ordered factors and a single exponent, the result is a tensor product with:
        * the same number of factors as the input, in the same order;
        * factor k equal to the power expression that raises input factor k to the
          given exponent (the value of the binary power map on that factor);
        * the same exponent used for every factor.

  (2) Simplifying ONE non-commutative factor of a product when that factor is such
      a power of a tensor product (``simp_pow_factor``). The simplifier replaces
      the power-of-a-tensor-product by its per-factor distribution (operation 1);
      a factor that is already a bare tensor product is returned unchanged; the
      decision is driven solely by whether the factor is a power whose base is a
      tensor product. This is the routing that lets the per-factor distribution be
      reached for a tensor-product power appearing as a factor of a product, not
      only as the whole expression.

A tensor product cannot be expressed in Nagini's fragment, so its content that the
operations touch — the ordered list of factor expressions — is the carrier
(``List[int]`` of opaque expression handles), and the exponent is one opaque
handle. The binary power map that takes one factor and one exponent to a power
expression is the single axiomatized callee (``pow_expr``), a deterministic map;
its soundness is checked out-of-band by axiom_check.py (G-AX). The specification of
a distributed result is the element-wise image of that map, carried by ``PSeq[int]``
via ``ToSeq`` (the front-recursive fold ``pointwise_pow``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def pow_expr(base: int, exp: int) -> int:
    """The binary power map: the handle of the power expression that raises one
    factor handle ``base`` to the exponent handle ``exp`` (the symbolic
    ``base ** exp``), as a deterministic map over expression handles. Two
    properties are relied upon:

      * determinism / functionality — the result depends only on (base, exp), so
        every reader of the map sees the SAME power handle for the same
        (factor, exponent) pair;
      * non-triviality away from the identity exponent — when ``exp`` is not the
        identity exponent (the reserved handle ``1`` for the exponent one, which
        a power node never carries because ``base ** 1`` is the factor itself),
        the power expression is distinct from the factor: ``Result() != base``.

    The identity exponent is excluded by the precondition; on it the real power
    map returns the factor unchanged, so the axiom does not over-claim there.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(exp != 1)
    Ensures(Result() != base)
# axioms-end


# pure-start
@Pure
def pointwise_pow(s: PSeq[int], exp: int) -> PSeq[int]:
    """The factor list of a distributed result: the element-wise image of the
    power map on the factors of ``s`` at exponent ``exp``, in order.
    Front-recursive so a single unfold is available per loop step."""
    Requires(exp != 1)
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(pow_expr(s[0], exp)) + pointwise_pow(s.drop(1), exp)
# pure-end


def power_of_collection(args: List[int], exp: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(args), 1 / 2))
    # The identity exponent (handle 1) is excluded: a power node never carries it
    # (``base ** 1`` is the factor itself), so this operation is reached only for
    # a genuine, non-identity exponent.
    Requires(exp != 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(args), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result has the same number of factors as the input, in the same order.
    Ensures(len(Result()) == len(args))
    # Factor k of the result is the value of the power map on input factor k at
    # the given exponent. Stated as the element-wise image over the actual input
    # factors, so the result is tied to a structural property of the input
    # carrier (its k-th factor), not to any constant or answer-key value.
    Ensures(ToSeq(Result()) == pointwise_pow(ToSeq(args), exp))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(args)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(args), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(args))
        Invariant(len(result) == len(args) - i)
        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
        # invariants-end
        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        result = [pow_expr(e, exp)] + result
        i = i - 1
    return result
    # impl-end


def simp_pow_factor(is_pow_of_tp: bool, factors: List[int], exp: int) -> List[int]:
    # pre-conditions-start
    # A single non-commutative factor of a product whose base is a tensor product:
    # `factors` are the tensor-product factors of that base (in order). The factor
    # is EITHER a power of that tensor product (`is_pow_of_tp` True), in which case
    # `exp` is the power's exponent, OR the bare tensor product itself
    # (`is_pow_of_tp` False). A power node never carries the identity exponent.
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Implies(is_pow_of_tp, exp != 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(factors))
    # Routing decision: a power-of-tensor-product factor is replaced by its
    # per-factor distribution (each base factor raised to the exponent); a bare
    # tensor-product factor passes through unchanged (factor k stays factor k).
    Ensures(Implies(is_pow_of_tp, ToSeq(Result()) == pointwise_pow(ToSeq(factors), exp)))
    Ensures(Implies(not is_pow_of_tp, ToSeq(Result()) == ToSeq(factors)))
    # post-conditions-end
    # impl-start
    if is_pow_of_tp:
        return power_of_collection(factors, exp)
    result = []  # type: List[int]
    i = len(factors)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(factors))
        Invariant(len(result) == len(factors) - i)
        Invariant(ToSeq(result) == ToSeq(factors).drop(i))
        # invariants-end
        e = factors[i - 1]
        Assert(ToSeq(factors).drop(i - 1)[0] == e)
        Assert(ToSeq(factors).drop(i - 1).drop(1) == ToSeq(factors).drop(i))
        result = [e] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-13974 (nagini). The frozen spec pins BOTH operations tightly: power_of_collection must satisfy len(Result())==len(args) AND ToSeq(Result())==pointwise_pow(ToSeq(args),exp); simp_pow_factor must distribute on is_pow_of_tp (==pointwise_pow(ToSeq(factors),exp)) and pass through otherwise (==ToSeq(factors)). Only the two impl regions are editable; axioms/@Pure/Requires/Ensures/invariant-structure spec bytes are frozen. Every attack confirmed SAME-spec via `adversary same-spec` (no JVM). weakness/verify runs executed in the swebench-lean env with SBU_BENCHMARK_DIR=benchmark-verified, scheduled in background batches of <=3 JVMs.

EXACT COMMANDS (per file): python -m swebench_unified.adversary same-spec nagini sympy__sympy-13974 <path>; python -m swebench_unified.adversary weakness nagini sympy__sympy-13974 <path>; bash scripts/nagini_verify.sh <path>.

### ATTACKS (all copy model.py editing ONLY the impl region; same-spec=SAME for all 8):
- atk_1 (prepatch bug / identity fold in power_of_collection): weakness EXIT=2 NOT-A-COUNTEREXAMPLE. nagini_verify: 'Postcondition of power_of_collection might not hold. Assertion (ToSeq(Result()) == pointwise_pow(ToSeq(args), exp)) might not hold.' Spec senses the change exactly (G-DIFF reproduced) -> prepatch_reproduced=true.
- atk_2 (return empty list; wrong length+seq): weakness EXIT=2, does not verify.
- atk_3 (partial-domain: correct on empty input, identity fold otherwise): weakness EXIT=2, does not verify.
- atk_4 (boundary off-by-one: while i>1, skips last factor, otherwise faithful distribute): weakness EXIT=2, does not verify.
- atk_5 (control-flow-effect: non-terminating `while True`): weakness EXIT=2; nagini_verify: 'Translation failed / Type error: dead.code' -> NOT JUDGED: the front end refused the program (the return after `while True` is statically unreachable), so the spec never ruled on it and it counts in neither tally; the attack SHAPE is unexpressible in nagini's fragment and did not test the spec's method-level `MustTerminate`.
- atk_6 (routing swap: distribute on the NOT-is_pow_of_tp branch): weakness EXIT=2; nagini_verify: 'The precondition of method power_of_collection might not hold. Assertion (exp != 1) might not hold.' -> rejected.
- atk_7 (ungrounded-oracle-echo / alternative CORRECT forward-loop distribute): weakness EXIT=2 does not verify (front-recursive pointwise_pow admits only the backward fold's proof shape; a same-behaviour forward variant fails to verify -> proof-engineering, not a spec weakness).
- atk_8 (routing: always-passthrough ignoring is_pow_of_tp): weakness EXIT=2; nagini_verify: 'Postcondition of simp_pow_factor might not hold. Assertion Implies(is_pow_of_tp, (ToSeq(Result()) == pointwise_pow(ToSeq(factors), exp))) might not hold.' -> the is_pow_of_tp distribution leg is genuinely pinned.

POSITIVE CONTROL pos.py (exact original impl): weakness EXIT=0 CANDIDATE (shares spec AND verifies) -> the intended impl verifies as expected.

RESOLVE RUNS: none required. No wrong impl produced a CANDIDATE (verify+same-spec) => there is NO verifying-but-wrong impl whose faithful refined patch could fail resolve. The only CANDIDATE is the correct positive control. verify_completed was true for all runs (the code distinguishes timeouts/infra as inconclusive; none occurred) so the SOUND verdict rests on genuine rejections, not fail-closed artifacts.

A-LEG / refinement.md audit: The sole consumed axiom pow_expr maps to the UNCHANGED callee `b ** e.exp` (real sympy Pow); mapping.md §3 correspondence is faithful (the patch only moves WHERE `**` is applied, per tensor factor, and does not change the constructor). It is correctly tagged A-consumed. Both genuinely-changed operations are modeled DEEPLY: the exponent distribution via the spelled-out front-recursive pointwise_pow fold consumed in power_of_collection (A3), and the routing decision via simp_pow_factor as concrete branches delegating to the deep power_of_collection (B3) + an identity fold (B4). No `tensor_product_simp_Pow` or `tensor_product_simp_Mul` oracle axiom exists. Every refinement leg is R / A-consumed / I — NO kind-3 (unexpressible-changed-op) leg. The axiom precondition Requires(exp!=1) is weakest-sufficient and faithful (a Pow node never carries exponent 1); axiom_check.py exercises the identity boundary (base**1==base) and asserts non-triviality only for exp!=1, so the axiom does not over-claim.

CONCLUSION: The spec discriminates every distinct wrong impl class attempted (prepatch, empty, partial-domain, boundary, control-flow-effect, oracle-echo, routing-swap, routing-passthrough) while admitting the correct impl. verify => correct holds for this bundle. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: I tried to show the spec is too strong / drifts from the real callee, but could not. Setup: gold-patched worktree (sympy 1.1.2.dev @ base_commit 84c1259, ran py3.8 with PYTHONPATH). Spec region confirmed byte-identical (same-spec exit 0).

Modeled functions vs real repo:
(1) power_of_collection(args,exp) models tensor_product_simp_Pow(e) = TensorProduct(*[b**e.exp for b in e.base.args]). Postconditions: len(Result())==len(args); ToSeq(Result())==pointwise_pow(...,exp) i.e. factor k == pow_expr(args[k],exp); Requires(exp!=1).
(2) simp_pow_factor models the tensor_product_simp_Mul routing: is_pow_of_tp True -> distribute (power_of_collection); False -> passthrough unchanged.
(3) pow_expr axiom: Requires(exp!=1) => Result()!=base (determinism + non-triviality).

Divergence hunt (all NEGATIVE - no divergence found):
- 20,000-trial independent fuzz over 1-6 factors, 16 exponent shapes (symbols, ints incl. -1/-2, x+1, 2*x, x*y, x/2, x-1): tuple(tpp(p).args)==[b**exp...] and len preserved in every case where base**exp is a bare Pow-of-TP. 0 divergences.
- Arg-count invariant len(Result())==len(args): probed identity operator, repeated factors, factor-that-is-a-power/product/sum, exp -1 and 1/2. All preserve arg count. Reasoning confirmed: a bare TensorProduct survives canonicalization only if all args are non-commutative (TP(p,A) collapses to a Mul), and b**exp of a non-commutative b stays non-commutative, so reconstruction never drops/merges factors. No shrinking counterexample exists.
- Axiom precondition exp!=1 is weakest-sufficient and faithful: b**1==b (real), b**exp!=b for every exp!=1 including symbolic n, 0, -1; x/x canonicalizes to 1 (returns b) but a Pow node never carries exp 1 so tensor_product_simp_Pow is never reached there. No over-claim.
- Routing passthrough (is_pow_of_tp False): c*TP(*factors) leaves the TP factor's args unchanged in all tested cases — matches identity fold.
- Exponent 0 / other collapses (base**exp not a Pow) are outside the modeled domain (the guard isinstance(e,Pow) & base is TP), so not a spec obligation — no drift.

Bundle's own axiom_check.py passes against the gold worktree (RC 0: 35 non-trivial + 10 boundary + 500 fuzz axiom pairs, 8+500 end-to-end, 11+500 routing, all 4 F2P witnesses). model.py verifies under pinned Nagini (Verification successful, 17s). The spec neither over-claims nor drifts from the real repo behavior on any input in the modeled domain. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view = model.py spec regions only (docstring + pow_expr axiom + pointwise_pow fold + pre/post-conditions for power_of_collection and simp_pow_factor); impl regions are elided (`...`). mapping.md/refinement.md are auditor artifacts, not part of the spec view.

Mechanical screen (leakage.screen, nagini flavor) PASSES with zero hard failures. Verified by inspection: no diff markers, no gold-patch line reproduced (>=8 chars), no patched file path (tensorproduct.py) or module path, no repo-symbol collisions, no bug/fix narration. All repo identifiers are absent from the view: tensor_product_simp_Pow, tensor_product_simp_Mul, tensorproduct.py, TensorProduct, nc_part, c_part, args_cnc, e.base, e.exp, Pow, isinstance.

Semantic check (what the lexical screen can miss): the desired end-behavior the spec pins is ALREADY fully public in problem_statement. The problem statement's [5]/[9] examples show the expected result of evaluating powers of TensorProduct (tps(tp(1,1)*tp(1,a)).subs(a,1) == tp(1,1) etc.), i.e. distributing the exponent to each factor. Spec operation (1) 'raise a tensor product to an exponent -> each factor raised, same order/count' is exactly this publicly-stated desired behavior, not a disclosure of the edit. Operation (2)'s 'routing' is stated abstractly (a power-of-tensor-product factor of a product must reach the same distribution) over opaque int handles / PSeq / ToSeq, naming no repo file, symbol, method, or edit location. The pre-patch behavior is discussed only in mapping.md/refinement.md (auditor-only), never in the spec view. No line in the spec view reveals the gold edit beyond what problem_statement already makes public.

Note: bundle is NOT relaxed (relaxed_leakage flag false, no RELAXED_LEAKAGE.md), so this is a genuine clean pass, not a deferral. (Aside: G-EQ is recorded BROKEN via atk_3 verify-not-resolve, but that is a G-EQ concern, outside panel_3 leakage scope.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
