# P2 adversarial audit — sympy__sympy-20438

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(elems), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems), 1 / 2))
@@ -101,21 +99,9 @@
     Ensures(Result() == all_in(ToSeq(elems), finite_id))
     # post-conditions-end
     # impl-start
-    res = True
-    i = len(elems)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(elems), 1 / 2))
-        Invariant(0 <= i and i <= len(elems))
-        Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        e = elems[i - 1]
-        Assert(ToSeq(elems).drop(i - 1)[0] == e)
-        Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
-        res = member(finite_id, e) and res
-        i = i - 1
-    Assert(ToSeq(elems).drop(0) == ToSeq(elems))
+    # ATTACK 1 (prepatch bug): the containment fact is never computed;
+    # the decision does not depend on `member` at all.
+    res = len(elems) == 0
     return res
     # impl-end
 
@@ -125,7 +111,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -153,7 +138,6 @@
     # element handles and collection ids of behaviour (2) for the two operands.
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(elems), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems), 1 / 2))
@@ -108,12 +106,12 @@
         Invariant(Acc(list_pred(elems), 1 / 2))
         Invariant(0 <= i and i <= len(elems))
         Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = elems[i - 1]
         Assert(ToSeq(elems).drop(i - 1)[0] == e)
         Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
-        res = member(finite_id, e) and res
+        # ATTACK 2 (control-flow-effect): OR-fold instead of AND-fold
+        res = member(finite_id, e) or res
         i = i - 1
     Assert(ToSeq(elems).drop(0) == ToSeq(elems))
     return res
@@ -125,7 +123,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -153,7 +150,6 @@
     # element handles and collection ids of behaviour (2) for the two operands.
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(elems), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems), 1 / 2))
@@ -103,16 +101,16 @@
     # impl-start
     res = True
     i = len(elems)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(elems), 1 / 2))
         Invariant(0 <= i and i <= len(elems))
         Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = elems[i - 1]
         Assert(ToSeq(elems).drop(i - 1)[0] == e)
         Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
+        # ATTACK 3 (boundary): loop stops at i>1, dropping element 0
         res = member(finite_id, e) and res
         i = i - 1
     Assert(ToSeq(elems).drop(0) == ToSeq(elems))
@@ -125,7 +123,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -153,7 +150,6 @@
     # element handles and collection ids of behaviour (2) for the two operands.
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(elems), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems), 1 / 2))
@@ -108,7 +106,6 @@
         Invariant(Acc(list_pred(elems), 1 / 2))
         Invariant(0 <= i and i <= len(elems))
         Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = elems[i - 1]
         Assert(ToSeq(elems).drop(i - 1)[0] == e)
@@ -125,7 +122,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -137,9 +133,9 @@
                          and all_in(ToSeq(elems_b), id_a)))
     # post-conditions-end
     # impl-start
+    # ATTACK 4 (partial-domain): only check a subset of b, drop the reverse.
     a_sub_b = product_subset_of_finite(elems_a, id_b)
-    b_sub_a = product_subset_of_finite(elems_b, id_a)
-    return a_sub_b and b_sub_a
+    return a_sub_b
     # impl-end
 
 
@@ -153,7 +149,6 @@
     # element handles and collection ids of behaviour (2) for the two operands.
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(elems), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems), 1 / 2))
@@ -108,7 +106,6 @@
         Invariant(Acc(list_pred(elems), 1 / 2))
         Invariant(0 <= i and i <= len(elems))
         Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = elems[i - 1]
         Assert(ToSeq(elems).drop(i - 1)[0] == e)
@@ -125,7 +122,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -153,7 +149,6 @@
     # element handles and collection ids of behaviour (2) for the two operands.
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -177,9 +172,7 @@
     if both_arith:
         # Both operands arithmetic: take the unchanged arithmetic-reduction path.
         return ARITH_PATH()
-    # At least one operand is a collection: do NOT attempt the arithmetic
-    # reduction (which has no defined result for a collection operand); defer to
-    # the collection-equality decision of behaviour (2).
-    equal = finite_sets_equal(elems_a, id_a, elems_b, id_b)
-    return collection_outcome(equal)
+    # ATTACK 5 (ungrounded-oracle echo): return the collection outcome without
+    # consulting the actual equality decision -- claim always-equal.
+    return collection_outcome(True)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(elems), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems), 1 / 2))
@@ -108,7 +106,6 @@
         Invariant(Acc(list_pred(elems), 1 / 2))
         Invariant(0 <= i and i <= len(elems))
         Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = elems[i - 1]
         Assert(ToSeq(elems).drop(i - 1)[0] == e)
@@ -125,7 +122,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -153,7 +149,6 @@
     # element handles and collection ids of behaviour (2) for the two operands.
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -174,12 +169,10 @@
                         and all_in(ToSeq(elems_b), id_a))))
     # post-conditions-end
     # impl-start
-    if both_arith:
-        # Both operands arithmetic: take the unchanged arithmetic-reduction path.
+    # ATTACK 6 (control-flow swap): route arithmetic operands to the
+    # collection decision and collection operands to the arithmetic path.
+    if not both_arith:
         return ARITH_PATH()
-    # At least one operand is a collection: do NOT attempt the arithmetic
-    # reduction (which has no defined result for a collection operand); defer to
-    # the collection-equality decision of behaviour (2).
     equal = finite_sets_equal(elems_a, id_a, elems_b, id_b)
     return collection_outcome(equal)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(elems), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems), 1 / 2))
@@ -101,21 +99,16 @@
     Ensures(Result() == all_in(ToSeq(elems), finite_id))
     # post-conditions-end
     # impl-start
+    # ATTACK 7 (subtle wrong): decide subset by only the LAST enumerated
+    # element's membership, ignoring the rest of the fold.
     res = True
     i = len(elems)
-    while i > 0:
+    if i > 0:
         # invariants-start
         Invariant(Acc(list_pred(elems), 1 / 2))
-        Invariant(0 <= i and i <= len(elems))
-        Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = elems[i - 1]
-        Assert(ToSeq(elems).drop(i - 1)[0] == e)
-        Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
-        res = member(finite_id, e) and res
-        i = i - 1
-    Assert(ToSeq(elems).drop(0) == ToSeq(elems))
+        res = member(finite_id, e)
     return res
     # impl-end
 
@@ -125,7 +118,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
@@ -153,7 +145,6 @@
     # element handles and collection ids of behaviour (2) for the two operands.
     Requires(Acc(list_pred(elems_a), 1 / 2))
     Requires(Acc(list_pred(elems_b), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(elems_a), 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-20438.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Deciding whether a structured (Cartesian-product) collection is contained
      in a finite collection.  Enumerate the elements of the product collection
      and ask, for each, whether it belongs to the finite collection.  The
      product collection is a subset of the finite collection EXACTLY when every
      enumerated element belongs to it.  In particular the answer is a definite
      truth value computed FROM the per-element membership facts -- it is not
      left undecided when those facts are all available.

  (2) Deciding whether two finite collections are equal.  Two collections are
      equal EXACTLY when each is contained in the other -- i.e. every element of
      the first belongs to the second AND every element of the second belongs to
      the first.  Equality is therefore the conjunction of the two containment
      decisions of behaviour (1), again a definite truth value when all the
      per-element membership facts are available.

  (3) Routing the simplification of an equality between two operands.  An
      equality is simplified by first attempting an arithmetic-style reduction
      that only applies when BOTH operands are arithmetic (number-like) values:
      it forms their difference and compares it with zero.  That reduction is
      only meaningful for arithmetic operands; for operands that are collections
      (which carry no difference / zero-comparison) the reduction must NOT be
      attempted -- attempting it on a collection operand has no defined result.
      The behaviour under specification: the routing is guarded on operand kind.
      When both operands are arithmetic it takes the arithmetic-reduction path.
      When at least one operand is a collection it does NOT take that path; it
      defers to the collection-equality decision of behaviour (2) and returns
      that definite truth value.  In particular the collection case is ALWAYS
      decided through behaviour (2) and never routed into the arithmetic
      reduction that has no defined result for a collection operand.

Elements are modelled as opaque integer handles.  Membership of a handle in a
collection is an unchanged deterministic pure oracle keyed by a collection
identifier (axioms region); only totality + determinism are relied upon -- the
impl reads the SAME membership fact the spec folds read.  Each containment
decision is the front-recursive boolean fold `all_in` over the enumerated
element handles, paired with a matching loop in the impl.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def member(setid: int, el: int) -> bool:
    """The unchanged membership oracle: whether element handle `el` belongs to
    the finite collection identified by `setid`.  Deterministic and total -- the
    only properties relied upon -- so the impl loop reads the same membership
    fact that the specification fold reads.  Provenance + executable soundness
    check: mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
@Pure
def all_in(s: PSeq[int], setid: int) -> bool:
    """Whether every enumerated element handle in `s` belongs to the collection
    `setid`.  Front-recursive so a single unfold is available per loop step:
    empty enumerates to True; otherwise the head must be a member AND the tail
    must all be members."""
    if len(s) == 0:
        return True
    return member(setid, s[0]) and all_in(s.drop(1), setid)

@Pure
def ARITH_PATH() -> int:
    """Outcome token meaning the arithmetic-reduction path was taken (the
    unchanged behaviour for two arithmetic operands -- its result is opaque to
    this routing model)."""
    return 0

@Pure
def collection_outcome(equal: bool) -> int:
    """Outcome token of the collection-equality decision: a definite truth value
    (distinct from the arithmetic-path token).  `equal` is the collection
    equality of behaviour (2)."""
    return 1 if equal else 2
# pure-end

def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(elems), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems), 1 / 2))
    # The product collection is a subset of the finite collection EXACTLY when
    # every enumerated element belongs to it -- a definite truth value derived
    # from the per-element membership facts.
    Ensures(Result() == all_in(ToSeq(elems), finite_id))
    # post-conditions-end
    # impl-start
    res = True
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elems), 1 / 2))
        Invariant(0 <= i and i <= len(elems))
        Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
        # invariants-end
        e = elems[i - 1]
        Assert(ToSeq(elems).drop(i - 1)[0] == e)
        Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
        res = member(finite_id, e) and res
        i = i - 1
    Assert(ToSeq(elems).drop(0) == ToSeq(elems))
    return res
    # impl-end

def finite_sets_equal(elems_a: List[int], id_a: int,
                      elems_b: List[int], id_b: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(elems_a), 1 / 2))
    Requires(Acc(list_pred(elems_b), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems_a), 1 / 2))
    Ensures(Acc(list_pred(elems_b), 1 / 2))
    # Two finite collections are equal EXACTLY when each is contained in the
    # other: every element of the first belongs to the second AND every element
    # of the second belongs to the first.
    Ensures(Result() == (all_in(ToSeq(elems_a), id_b)
                         and all_in(ToSeq(elems_b), id_a)))
    # post-conditions-end
    # impl-start
    a_sub_b = product_subset_of_finite(elems_a, id_b)
    b_sub_a = product_subset_of_finite(elems_b, id_a)
    return a_sub_b and b_sub_a
    # impl-end

def simplify_equality_route(both_arith: bool,
                            elems_a: List[int], id_a: int,
                            elems_b: List[int], id_b: int) -> int:
    # pre-conditions-start
    # `both_arith` records whether BOTH equality operands are arithmetic
    # (number-like) values; if False, at least one is a collection.  When the
    # operands are collections, `elems_a`/`id_a` and `elems_b`/`id_b` are the
    # element handles and collection ids of behaviour (2) for the two operands.
    Requires(Acc(list_pred(elems_a), 1 / 2))
    Requires(Acc(list_pred(elems_b), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems_a), 1 / 2))
    Ensures(Acc(list_pred(elems_b), 1 / 2))
    # The routing is total: it always returns a definite outcome token -- it
    # never has an undefined result.  In particular the collection case is
    # decided, never left without a defined result.
    # When both operands are arithmetic the arithmetic-reduction path is taken.
    Ensures(Implies(both_arith, Result() == ARITH_PATH()))
    # When at least one operand is a collection the arithmetic reduction is NOT
    # attempted (its token is never returned); the routing defers to the
    # collection-equality decision of behaviour (2) and returns that definite
    # truth value as a collection outcome token.
    Ensures(Implies(not both_arith, Result() != ARITH_PATH()))
    Ensures(Implies(not both_arith,
                    Result() == collection_outcome(
                        all_in(ToSeq(elems_a), id_b)
                        and all_in(ToSeq(elems_b), id_a))))
    # post-conditions-end
    # impl-start
    if both_arith:
        # Both operands arithmetic: take the unchanged arithmetic-reduction path.
        return ARITH_PATH()
    # At least one operand is a collection: do NOT attempt the arithmetic
    # reduction (which has no defined result for a collection operand); defer to
    # the collection-equality decision of behaviour (2).
    equal = finite_sets_equal(elems_a, id_a, elems_b, id_b)
    return collection_outcome(equal)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### Audit protocol

SPEC SHAPE: three contracted functions. The post-conditions pin Result() EXACTLY to deep folds: product_subset_of_finite -> Result()==all_in(ToSeq(elems),finite_id); finite_sets_equal -> Result()==(all_in(a,id_b) and all_in(b,id_a)); simplify_equality_route -> Implies(both_arith, Result()==ARITH_PATH()) AND Implies(not both_arith, Result()!=ARITH_PATH() and Result()==collection_outcome(all_in(a,id_b) and all_in(b,id_a))). all_in is the spelled-out front-recursive AND-fold in the frozen pure region; member is the only consumed axiom (purity/totality only, no value Ensures). So a behaviorally-wrong impl must still meet an exact-value postcondition to verify — the spec is tight by construction.

ATTACKS (7 distinct wrong impls; axioms/@Pure/Requires/Ensures/invariants-contract left byte-identical; only impl regions edited). Every one confirmed same-spec (adversary same-spec exit 0) then run through `python -m swebench_unified.adversary weakness nagini sympy__sympy-20438 <atk>`:
  atk_1 (prepatch bug, ungrounded/partial-domain): product_subset_of_finite returns len(elems)==0 (containment never computed, ignores member) -> weakness EXIT=2, verification failed (this is the recorded prepatch bug from model_prepatch.py -> prepatch_reproduced=true).
  atk_2 (control-flow-effect): OR-fold `member or res` instead of AND-fold -> EXIT=2, failed.
  atk_3 (boundary/off-by-one): loop guard `while i>1` drops element 0 -> EXIT=2, failed.
  atk_4 (partial-domain): finite_sets_equal returns only a_sub_b, drops reverse containment -> EXIT=2, failed.
  atk_5 (ungrounded-oracle echo): routing collection branch returns collection_outcome(True) without consulting finite_sets_equal -> EXIT=2, failed.
  atk_6 (control-flow swap): routing branches swapped (arith path for collections) -> EXIT=2, failed.
  atk_7 (subtle wrong): product_subset_of_finite decides on only the last element's membership -> EXIT=2, failed.
Ran concurrently in batches of 3 background jobs (each Nagini check spawns JVM+Z3): batch1={1,2,3}, batch2={4,5,6}, batch3={7}+positive_control.

RESULT: ALL 7 same-spec wrong impls were REJECTED by the Nagini verifier (0 CANDIDATEs). Because no attack both shared the spec AND verified, there was no verifying-but-wrong impl requiring a faithful-patch materialization + run_resolve; the verify=>correct implication is not falsified by any attack tried. Positive control (unmodified model.py) verifies: `bash scripts/nagini_verify.sh positive_control.py` -> Verification successful, 10.82s, EXIT=0. same-spec on the unmodified model returns SAME (spec-view projection sanity check passed).

REFINEMENT.MD AUDIT (A-legs focus; R/I mechanically covered by G-CONF): every leg is R / A-consumed / A-reference / I with NO kind-3 step (section D confirmed). The single A-consumed leg (A3, member <-> FiniteSet.contains) claims only determinism+totality (weakest sufficient contract, no value Ensures) — axiom_check.py real_member confirms determinism + definite-bool totality on F2P witnesses + 4000-round fuzz, asserting no exact value, matching the empty value-contract.

The three A-reference deep folds are validated (not consumed) by axiom_check.py: check_subset asserts ProductSet.is_subset(FiniteSet)==all_in over the enumerated product with no double-mask (membership predicate on only one side of the decided value); check_equal asserts Eq(A,B).simplify() is S.true iff mutual subset, S.false otherwise; check_route asserts the real Eq(A,B).simplify() on non-Expr (collection) operands does not raise (pre-patch AttributeError) and reaches a defined collection decision, and that model flag both_arith matches isinstance(lhs,Expr) and isinstance(rhs,Expr).

Model<->patch correspondence holds: A1/A2 tuple<->int handle & FiniteSet<->id (R); A4 fuzzy_and over decidable concrete terms IS boolean AND, tfn maps True->S.true/False->S.false; B1/B2 reuse the containment decision as lhs.is_subset(rhs)/rhs.is_subset(lhs); C1 both_arith<->both-Expr guard, C2 fall-through to arithmetic path (opaque ARITH_PATH token), C3 non-Expr routed to collection rule with ARITH_PATH forbidden. mapping.md §4 no-op sites (duplicate FiniteSet,Interval rule deletion; ProductSet import) are behavioral no-ops shipped verbatim in patch.diff. The A-references' correspondence to the real callees holds.

VERDICT: SOUND. >=5 distinct attacks (7) run and fully verified; none is a verifying wrong impl (0 CANDIDATEs), so no materialized faithful patch failed to resolve; positive control verifies; refinement.md has no kind-3 legs and the A-legs' callee correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-20438.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Deciding whether a structured (Cartesian-product) collection is contained
      in a finite collection.  Enumerate the elements of the product collection
      and ask, for each, whether it belongs to the finite collection.  The
      product collection is a subset of the finite collection EXACTLY when every
      enumerated element belongs to it.  In particular the answer is a definite
      truth value computed FROM the per-element membership facts -- it is not
      left undecided when those facts are all available.

  (2) Deciding whether two finite collections are equal.  Two collections are
      equal EXACTLY when each is contained in the other -- i.e. every element of
      the first belongs to the second AND every element of the second belongs to
      the first.  Equality is therefore the conjunction of the two containment
      decisions of behaviour (1), again a definite truth value when all the
      per-element membership facts are available.

  (3) Routing the simplification of an equality between two operands.  An
      equality is simplified by first attempting an arithmetic-style reduction
      that only applies when BOTH operands are arithmetic (number-like) values:
      it forms their difference and compares it with zero.  That reduction is
      only meaningful for arithmetic operands; for operands that are collections
      (which carry no difference / zero-comparison) the reduction must NOT be
      attempted -- attempting it on a collection operand has no defined result.
      The behaviour under specification: the routing is guarded on operand kind.
      When both operands are arithmetic it takes the arithmetic-reduction path.
      When at least one operand is a collection it does NOT take that path; it
      defers to the collection-equality decision of behaviour (2) and returns
      that definite truth value.  In particular the collection case is ALWAYS
      decided through behaviour (2) and never routed into the arithmetic
      reduction that has no defined result for a collection operand.

Elements are modelled as opaque integer handles.  Membership of a handle in a
collection is an unchanged deterministic pure oracle keyed by a collection
identifier (axioms region); only totality + determinism are relied upon -- the
impl reads the SAME membership fact the spec folds read.  Each containment
decision is the front-recursive boolean fold `all_in` over the enumerated
element handles, paired with a matching loop in the impl.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def member(setid: int, el: int) -> bool:
    """The unchanged membership oracle: whether element handle `el` belongs to
    the finite collection identified by `setid`.  Deterministic and total -- the
    only properties relied upon -- so the impl loop reads the same membership
    fact that the specification fold reads.  Provenance + executable soundness
    check: mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
@Pure
def all_in(s: PSeq[int], setid: int) -> bool:
    """Whether every enumerated element handle in `s` belongs to the collection
    `setid`.  Front-recursive so a single unfold is available per loop step:
    empty enumerates to True; otherwise the head must be a member AND the tail
    must all be members."""
    if len(s) == 0:
        return True
    return member(setid, s[0]) and all_in(s.drop(1), setid)

@Pure
def ARITH_PATH() -> int:
    """Outcome token meaning the arithmetic-reduction path was taken (the
    unchanged behaviour for two arithmetic operands -- its result is opaque to
    this routing model)."""
    return 0

@Pure
def collection_outcome(equal: bool) -> int:
    """Outcome token of the collection-equality decision: a definite truth value
    (distinct from the arithmetic-path token).  `equal` is the collection
    equality of behaviour (2)."""
    return 1 if equal else 2
# pure-end

def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(elems), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems), 1 / 2))
    # The product collection is a subset of the finite collection EXACTLY when
    # every enumerated element belongs to it -- a definite truth value derived
    # from the per-element membership facts.
    Ensures(Result() == all_in(ToSeq(elems), finite_id))
    # post-conditions-end
    # impl-start
    res = True
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elems), 1 / 2))
        Invariant(0 <= i and i <= len(elems))
        Invariant(res == all_in(ToSeq(elems).drop(i), finite_id))
        # invariants-end
        e = elems[i - 1]
        Assert(ToSeq(elems).drop(i - 1)[0] == e)
        Assert(ToSeq(elems).drop(i - 1).drop(1) == ToSeq(elems).drop(i))
        res = member(finite_id, e) and res
        i = i - 1
    Assert(ToSeq(elems).drop(0) == ToSeq(elems))
    return res
    # impl-end

def finite_sets_equal(elems_a: List[int], id_a: int,
                      elems_b: List[int], id_b: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(elems_a), 1 / 2))
    Requires(Acc(list_pred(elems_b), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems_a), 1 / 2))
    Ensures(Acc(list_pred(elems_b), 1 / 2))
    # Two finite collections are equal EXACTLY when each is contained in the
    # other: every element of the first belongs to the second AND every element
    # of the second belongs to the first.
    Ensures(Result() == (all_in(ToSeq(elems_a), id_b)
                         and all_in(ToSeq(elems_b), id_a)))
    # post-conditions-end
    # impl-start
    a_sub_b = product_subset_of_finite(elems_a, id_b)
    b_sub_a = product_subset_of_finite(elems_b, id_a)
    return a_sub_b and b_sub_a
    # impl-end

def simplify_equality_route(both_arith: bool,
                            elems_a: List[int], id_a: int,
                            elems_b: List[int], id_b: int) -> int:
    # pre-conditions-start
    # `both_arith` records whether BOTH equality operands are arithmetic
    # (number-like) values; if False, at least one is a collection.  When the
    # operands are collections, `elems_a`/`id_a` and `elems_b`/`id_b` are the
    # element handles and collection ids of behaviour (2) for the two operands.
    Requires(Acc(list_pred(elems_a), 1 / 2))
    Requires(Acc(list_pred(elems_b), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems_a), 1 / 2))
    Ensures(Acc(list_pred(elems_b), 1 / 2))
    # The routing is total: it always returns a definite outcome token -- it
    # never has an undefined result.  In particular the collection case is
    # decided, never left without a defined result.
    # When both operands are arithmetic the arithmetic-reduction path is taken.
    Ensures(Implies(both_arith, Result() == ARITH_PATH()))
    # When at least one operand is a collection the arithmetic reduction is NOT
    # attempted (its token is never returned); the routing defers to the
    # collection-equality decision of behaviour (2) and returns that definite
    # truth value as a collection outcome token.
    Ensures(Implies(not both_arith, Result() != ARITH_PATH()))
    Ensures(Implies(not both_arith,
                    Result() == collection_outcome(
                        all_in(ToSeq(elems_a), id_b)
                        and all_in(ToSeq(elems_b), id_a))))
    # post-conditions-end
    # impl-start
    if both_arith:
        # Both operands arithmetic: take the unchanged arithmetic-reduction path.
        return ARITH_PATH()
    # At least one operand is a collection: do NOT attempt the arithmetic
    # reduction (which has no defined result for a collection operand); defer to
    # the collection-equality decision of behaviour (2).
    equal = finite_sets_equal(elems_a, id_a, elems_b, id_b)
    return collection_outcome(equal)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### Audit protocol

SPEC SHAPE: three contracted functions. The post-conditions pin Result() EXACTLY to deep folds: product_subset_of_finite -> Result()==all_in(ToSeq(elems),finite_id); finite_sets_equal -> Result()==(all_in(a,id_b) and all_in(b,id_a)); simplify_equality_route -> Implies(both_arith, Result()==ARITH_PATH()) AND Implies(not both_arith, Result()!=ARITH_PATH() and Result()==collection_outcome(all_in(a,id_b) and all_in(b,id_a))). all_in is the spelled-out front-recursive AND-fold in the frozen pure region; member is the only consumed axiom (purity/totality only, no value Ensures). So a behaviorally-wrong impl must still meet an exact-value postcondition to verify — the spec is tight by construction.

ATTACKS (7 distinct wrong impls; axioms/@Pure/Requires/Ensures/invariants-contract left byte-identical; only impl regions edited). Every one confirmed same-spec (adversary same-spec exit 0) then run through `python -m swebench_unified.adversary weakness nagini sympy__sympy-20438 <atk>`:
  atk_1 (prepatch bug, ungrounded/partial-domain): product_subset_of_finite returns len(elems)==0 (containment never computed, ignores member) -> weakness EXIT=2, verification failed (this is the recorded prepatch bug from model_prepatch.py -> prepatch_reproduced=true).
  atk_2 (control-flow-effect): OR-fold `member or res` instead of AND-fold -> EXIT=2, failed.
  atk_3 (boundary/off-by-one): loop guard `while i>1` drops element 0 -> EXIT=2, failed.
  atk_4 (partial-domain): finite_sets_equal returns only a_sub_b, drops reverse containment -> EXIT=2, failed.
  atk_5 (ungrounded-oracle echo): routing collection branch returns collection_outcome(True) without consulting finite_sets_equal -> EXIT=2, failed.
  atk_6 (control-flow swap): routing branches swapped (arith path for collections) -> EXIT=2, failed.
  atk_7 (subtle wrong): product_subset_of_finite decides on only the last element's membership -> EXIT=2, failed.
Ran concurrently in batches of 3 background jobs (each Nagini check spawns JVM+Z3): batch1={1,2,3}, batch2={4,5,6}, batch3={7}+positive_control.

RESULT: ALL 7 same-spec wrong impls were REJECTED by the Nagini verifier (0 CANDIDATEs). Because no attack both shared the spec AND verified, there was no verifying-but-wrong impl requiring a faithful-patch materialization + run_resolve; the verify=>correct implication is not falsified by any attack tried. Positive control (unmodified model.py) verifies: `bash scripts/nagini_verify.sh positive_control.py` -> Verification successful, 10.82s, EXIT=0. same-spec on the unmodified model returns SAME (spec-view projection sanity check passed).

REFINEMENT.MD AUDIT (A-legs focus; R/I mechanically covered by G-CONF): every leg is R / A-consumed / A-reference / I with NO kind-3 step (section D confirmed). The single A-consumed leg (A3, member <-> FiniteSet.contains) claims only determinism+totality (weakest sufficient contract, no value Ensures) — axiom_check.py real_member confirms determinism + definite-bool totality on F2P witnesses + 4000-round fuzz, asserting no exact value, matching the empty value-contract.

The three A-reference deep folds are validated (not consumed) by axiom_check.py: check_subset asserts ProductSet.is_subset(FiniteSet)==all_in over the enumerated product with no double-mask (membership predicate on only one side of the decided value); check_equal asserts Eq(A,B).simplify() is S.true iff mutual subset, S.false otherwise; check_route asserts the real Eq(A,B).simplify() on non-Expr (collection) operands does not raise (pre-patch AttributeError) and reaches a defined collection decision, and that model flag both_arith matches isinstance(lhs,Expr) and isinstance(rhs,Expr).

Model<->patch correspondence holds: A1/A2 tuple<->int handle & FiniteSet<->id (R); A4 fuzzy_and over decidable concrete terms IS boolean AND, tfn maps True->S.true/False->S.false; B1/B2 reuse the containment decision as lhs.is_subset(rhs)/rhs.is_subset(lhs); C1 both_arith<->both-Expr guard, C2 fall-through to arithmetic path (opaque ARITH_PATH token), C3 non-Expr routed to collection rule with ARITH_PATH forbidden. mapping.md §4 no-op sites (duplicate FiniteSet,Interval rule deletion; ProductSet import) are behavioral no-ops shipped verbatim in patch.diff. The A-references' correspondence to the real callees holds.

VERDICT: SOUND. >=5 distinct attacks (7) run and fully verified; none is a verifying wrong impl (0 CANDIDATEs), so no materialized faithful patch failed to resolve; positive control verifies; refinement.md has no kind-3 legs and the A-legs' callee correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Set up patched testbed: git worktree at base_commit 33b47e4bd60e2302e42616141e76285038b724d6 + gold patch applied. Validated the spec against the REAL patched callees on all three modeled behaviors: (1) product_subset_of_finite == ProductSet.is_subset(FiniteSet), (2) finite_sets_equal == Eq(A,B).simplify() mutual-subset value, (3) simplify_equality_route == the isinstance(_,Expr) routing guard.

Evidence: identity same-spec check exit 0 (markers intact); nagini_verify.sh SUCCEEDS in 11.6s (spec real & non-vacuous); axiom_check.py (G-AX) passes against real repo; conformance_check.py (G-CONF) reports 0 disagreements over 100,034 concrete inputs; my independent 60k-round fuzz over random concrete FiniteSet/ProductSet/Interval collections found 0 non-definite results and 0 raises — the real Eq(...).simplify() is always definite (S.true/S.false) on the concrete domain, exactly matching collection_outcome (token 1/2, never ARITH_PATH).

The only divergence (non-definite result) requires SYMBOLIC elements, which make `member` non-definite and are excluded from the modeled domain per mapping.md §2/§3.1 and the conformance BridgeError. This domain restriction is documented honestly (not a hidden over-claim). Within its declared concrete domain, the modeled functions agree with the real callees on every input tested. The spec is neither too strong nor drifting: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no patched file/module paths, no changed-symbol collisions, no bug/fix narration; changed repo symbols is_subset_sets/_eval_is_eq/equals/binary_symbols absent from the spec view). Semantic gold-reconstruction check: the spec view describes three behaviors, all grounded in the UNUSUALLY EXPLICIT public problem_statement plus standard mathematical definitions, adding no localization beyond it:

(1) ProductSet ⊆ FiniteSet iff every enumerated element is a member. The failing operation `b.is_subset(c)` (ProductSet.is_subset(FiniteSet)) is named verbatim in the problem_statement repro. 'subset iff all elements are members' is the textbook definition of subset, not a distinctive edit.

(2) Set equality iff mutual containment. `Eq(b,c).simplify()` failure is shown in the problem_statement. 'two sets equal iff each is a subset of the other' is the universal definition of set equality — not gold-specific.

(3) Routing guarded on operand kind: do NOT attempt the arithmetic difference (`lhs - rhs`)/zero-comparison (`.equals(0)`) reduction for collection operands. This mirrors the PUBLIC traceback in the problem_statement, which shows exactly `dif = r.lhs - r.rhs` and `elif dif.equals(0)` at relational.py:308 raising `AttributeError: 'Complement' object has no attribute 'equals'`. Guarding the arithmetic path away from non-arithmetic operands is the direct, obvious fix implied by the public crash; the spec uses neutral 'arithmetic (number-like)' phrasing and never names the `isinstance(_, Expr)` mechanism or Expr type.

Abstraction names (product_subset_of_finite, finite_sets_equal, simplify_equality_route, member, all_in, ARITH_PATH, collection_outcome) are behavioral and do not echo any patched repo symbol. No diff line, edit mechanism, or repo-internal path is disclosed. The spec is a faithful behavioral model reconstructible from the public problem_statement alone; it does not leak the gold edit beyond it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).