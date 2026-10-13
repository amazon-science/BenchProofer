# P2 adversarial audit — sympy__sympy-16792

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -105,7 +104,6 @@
     Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                             0 <= kinds[i] and kinds[i] <= 2),
                                      [[kinds[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kinds), 1 / 2))
@@ -123,7 +121,7 @@
     result = []  # type: List[bool]
     j = 0
     while j < len(kinds):
-        # invariants-start
+# invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(present), 1 / 2))
         Invariant(len(kinds) == len(present))
@@ -137,33 +135,18 @@
                                                  result[i] == want_pointer(kinds[i], present[i])),
                                           [[result[i]]])))
         Invariant(j <= len(present))
-        Invariant(MustTerminate(len(kinds) - j + 1))
         # invariants-end
         k = kinds[j]
         is_present = present[j]
-        # Resolve the argument's array-ness, then render the dimension flag.
-        # A matrix is intrinsically an array and is given dimensions whether or
-        # not it occurs in the expression. An indexed array is given dimensions
-        # only when it occurs (its shape is recovered from the entries there).
-        # A scalar never carries dimensions.
-        if shape_is_intrinsic(k):
-            has_dims = True
-        elif k == 2:
-            if is_present:
+        if is_present:
+            if shape_is_intrinsic(k) or k == 2:
                 has_dims = True
             else:
                 has_dims = False
         else:
             has_dims = False
         flag = arg_is_pointer(has_dims)
-        Assert(flag == want_pointer(k, is_present))
-        old_result = result
         result = result + [flag]
-        Assert(len(result) == j + 1)
-        Assert(result[j] == want_pointer(kinds[j], present[j]))
-        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
-                                              result[i] == old_result[i]),
-                                       [[result[i]]])))
         j = j + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -105,7 +104,6 @@
     Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                             0 <= kinds[i] and kinds[i] <= 2),
                                      [[kinds[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kinds), 1 / 2))
@@ -123,7 +121,7 @@
     result = []  # type: List[bool]
     j = 0
     while j < len(kinds):
-        # invariants-start
+# invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(present), 1 / 2))
         Invariant(len(kinds) == len(present))
@@ -137,33 +135,14 @@
                                                  result[i] == want_pointer(kinds[i], present[i])),
                                           [[result[i]]])))
         Invariant(j <= len(present))
-        Invariant(MustTerminate(len(kinds) - j + 1))
         # invariants-end
         k = kinds[j]
         is_present = present[j]
-        # Resolve the argument's array-ness, then render the dimension flag.
-        # A matrix is intrinsically an array and is given dimensions whether or
-        # not it occurs in the expression. An indexed array is given dimensions
-        # only when it occurs (its shape is recovered from the entries there).
-        # A scalar never carries dimensions.
-        if shape_is_intrinsic(k):
-            has_dims = True
-        elif k == 2:
-            if is_present:
-                has_dims = True
-            else:
-                has_dims = False
+        if is_present:
+            flag = want_pointer(k, is_present)
         else:
-            has_dims = False
-        flag = arg_is_pointer(has_dims)
-        Assert(flag == want_pointer(k, is_present))
-        old_result = result
+            flag = False
         result = result + [flag]
-        Assert(len(result) == j + 1)
-        Assert(result[j] == want_pointer(kinds[j], present[j]))
-        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
-                                              result[i] == old_result[i]),
-                                       [[result[i]]])))
         j = j + 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -105,7 +104,6 @@
     Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                             0 <= kinds[i] and kinds[i] <= 2),
                                      [[kinds[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kinds), 1 / 2))
@@ -122,8 +120,8 @@
     # impl-start
     result = []  # type: List[bool]
     j = 0
-    while j < len(kinds):
-        # invariants-start
+    while j < len(kinds) - 1:
+# invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(present), 1 / 2))
         Invariant(len(kinds) == len(present))
@@ -137,33 +135,11 @@
                                                  result[i] == want_pointer(kinds[i], present[i])),
                                           [[result[i]]])))
         Invariant(j <= len(present))
-        Invariant(MustTerminate(len(kinds) - j + 1))
         # invariants-end
         k = kinds[j]
         is_present = present[j]
-        # Resolve the argument's array-ness, then render the dimension flag.
-        # A matrix is intrinsically an array and is given dimensions whether or
-        # not it occurs in the expression. An indexed array is given dimensions
-        # only when it occurs (its shape is recovered from the entries there).
-        # A scalar never carries dimensions.
-        if shape_is_intrinsic(k):
-            has_dims = True
-        elif k == 2:
-            if is_present:
-                has_dims = True
-            else:
-                has_dims = False
-        else:
-            has_dims = False
-        flag = arg_is_pointer(has_dims)
-        Assert(flag == want_pointer(k, is_present))
-        old_result = result
+        flag = want_pointer(k, is_present)
         result = result + [flag]
-        Assert(len(result) == j + 1)
-        Assert(result[j] == want_pointer(kinds[j], present[j]))
-        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
-                                              result[i] == old_result[i]),
-                                       [[result[i]]])))
         j = j + 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -105,7 +104,6 @@
     Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                             0 <= kinds[i] and kinds[i] <= 2),
                                      [[kinds[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kinds), 1 / 2))
@@ -123,7 +121,7 @@
     result = []  # type: List[bool]
     j = 0
     while j < len(kinds):
-        # invariants-start
+# invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(present), 1 / 2))
         Invariant(len(kinds) == len(present))
@@ -137,33 +135,17 @@
                                                  result[i] == want_pointer(kinds[i], present[i])),
                                           [[result[i]]])))
         Invariant(j <= len(present))
-        Invariant(MustTerminate(len(kinds) - j + 1))
         # invariants-end
         k = kinds[j]
         is_present = present[j]
-        # Resolve the argument's array-ness, then render the dimension flag.
-        # A matrix is intrinsically an array and is given dimensions whether or
-        # not it occurs in the expression. An indexed array is given dimensions
-        # only when it occurs (its shape is recovered from the entries there).
-        # A scalar never carries dimensions.
-        if shape_is_intrinsic(k):
+        if k == 0:
             has_dims = True
         elif k == 2:
-            if is_present:
-                has_dims = True
-            else:
-                has_dims = False
+            has_dims = is_present
         else:
             has_dims = False
         flag = arg_is_pointer(has_dims)
-        Assert(flag == want_pointer(k, is_present))
-        old_result = result
         result = result + [flag]
-        Assert(len(result) == j + 1)
-        Assert(result[j] == want_pointer(kinds[j], present[j]))
-        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
-                                              result[i] == old_result[i]),
-                                       [[result[i]]])))
         j = j + 1
     return result
     # impl-end
```

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -105,7 +104,6 @@
     Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                             0 <= kinds[i] and kinds[i] <= 2),
                                      [[kinds[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kinds), 1 / 2))
@@ -123,7 +121,7 @@
     result = []  # type: List[bool]
     j = 0
     while j < len(kinds):
-        # invariants-start
+# invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(present), 1 / 2))
         Invariant(len(kinds) == len(present))
@@ -137,33 +135,17 @@
                                                  result[i] == want_pointer(kinds[i], present[i])),
                                           [[result[i]]])))
         Invariant(j <= len(present))
-        Invariant(MustTerminate(len(kinds) - j + 1))
         # invariants-end
         k = kinds[j]
         is_present = present[j]
-        # Resolve the argument's array-ness, then render the dimension flag.
-        # A matrix is intrinsically an array and is given dimensions whether or
-        # not it occurs in the expression. An indexed array is given dimensions
-        # only when it occurs (its shape is recovered from the entries there).
-        # A scalar never carries dimensions.
-        if shape_is_intrinsic(k):
-            has_dims = True
+        if k == 1:
+            has_dims = is_present
         elif k == 2:
-            if is_present:
-                has_dims = True
-            else:
-                has_dims = False
+            has_dims = is_present
         else:
             has_dims = False
         flag = arg_is_pointer(has_dims)
-        Assert(flag == want_pointer(k, is_present))
-        old_result = result
         result = result + [flag]
-        Assert(len(result) == j + 1)
-        Assert(result[j] == want_pointer(kinds[j], present[j]))
-        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
-                                              result[i] == old_result[i]),
-                                       [[result[i]]])))
         j = j + 1
     return result
     # impl-end
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -105,7 +104,6 @@
     Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                             0 <= kinds[i] and kinds[i] <= 2),
                                      [[kinds[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kinds), 1 / 2))
@@ -123,7 +121,7 @@
     result = []  # type: List[bool]
     j = 0
     while j < len(kinds):
-        # invariants-start
+# invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(present), 1 / 2))
         Invariant(len(kinds) == len(present))
@@ -137,33 +135,17 @@
                                                  result[i] == want_pointer(kinds[i], present[i])),
                                           [[result[i]]])))
         Invariant(j <= len(present))
-        Invariant(MustTerminate(len(kinds) - j + 1))
         # invariants-end
         k = kinds[j]
         is_present = present[j]
-        # Resolve the argument's array-ness, then render the dimension flag.
-        # A matrix is intrinsically an array and is given dimensions whether or
-        # not it occurs in the expression. An indexed array is given dimensions
-        # only when it occurs (its shape is recovered from the entries there).
-        # A scalar never carries dimensions.
-        if shape_is_intrinsic(k):
+        if k == 1:
             has_dims = True
         elif k == 2:
-            if is_present:
-                has_dims = True
-            else:
-                has_dims = False
+            has_dims = True
         else:
             has_dims = False
         flag = arg_is_pointer(has_dims)
-        Assert(flag == want_pointer(k, is_present))
-        old_result = result
         result = result + [flag]
-        Assert(len(result) == j + 1)
-        Assert(result[j] == want_pointer(kinds[j], present[j]))
-        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
-                                              result[i] == old_result[i]),
-                                       [[result[i]]])))
         j = j + 1
     return result
     # impl-end
```

Attack 7 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -105,7 +104,6 @@
     Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                             0 <= kinds[i] and kinds[i] <= 2),
                                      [[kinds[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kinds), 1 / 2))
@@ -123,7 +121,7 @@
     result = []  # type: List[bool]
     j = 0
     while j < len(kinds):
-        # invariants-start
+# invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(present), 1 / 2))
         Invariant(len(kinds) == len(present))
@@ -137,26 +135,10 @@
                                                  result[i] == want_pointer(kinds[i], present[i])),
                                           [[result[i]]])))
         Invariant(j <= len(present))
-        Invariant(MustTerminate(len(kinds) - j + 1))
         # invariants-end
         k = kinds[j]
         is_present = present[j]
-        # Resolve the argument's array-ness, then render the dimension flag.
-        # A matrix is intrinsically an array and is given dimensions whether or
-        # not it occurs in the expression. An indexed array is given dimensions
-        # only when it occurs (its shape is recovered from the entries there).
-        # A scalar never carries dimensions.
-        if shape_is_intrinsic(k):
-            has_dims = True
-        elif k == 2:
-            if is_present:
-                has_dims = True
-            else:
-                has_dims = False
-        else:
-            has_dims = False
-        flag = arg_is_pointer(has_dims)
-        Assert(flag == want_pointer(k, is_present))
+        flag = want_pointer(k, is_present)
         old_result = result
         result = result + [flag]
         Assert(len(result) == j + 1)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-16792.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A code generator builds the ordered list of function arguments to match a
  caller-supplied argument sequence, then renders a C function prototype from
  it. Each requested argument falls into one of three kinds:

    * a plain scalar quantity;
    * a fixed-shape matrix quantity (always an array — its shape is intrinsic
      to the symbol);
    * an indexed-array quantity whose array shape is known only through the
      indexed entries that occur in the wrapped expression.

  Independently, each requested argument may or may not actually occur in the
  wrapped expression.

  The generated C prototype declares an argument as a pointer (`*name`) exactly
  when that argument is an array, and as a plain value (`name`) otherwise. The
  array-ness is resolved as follows, and element i of the rendered prototype is
  a pointer exactly when:

    * a matrix argument: ALWAYS — its shape is intrinsic, so it is an array
      whether or not it appears in the expression;
    * an indexed-array argument: only when it appears in the expression (its
      shape is recovered from the indexed entries that occur there);
    * a scalar argument: never.

  The behaviour the specification pins is that a matrix argument is declared as
  a pointer even when it does NOT appear in the wrapped expression — its
  intrinsic shape makes it an array regardless of use.

Each requested argument is modelled by a kind tag (`0` = scalar, `1` = matrix,
`2` = indexed-array) and a presence flag (does it occur in the expression). The
C prototype's per-argument pointer decision is rendered as a `bool`. The
specification is carried element-wise via the pure predicate `want_pointer`.

The array-ness decision and the prototype's pointer rendering are modelled
deeply (`shape_is_intrinsic`, `array_resolved`, `arg_is_pointer`); their
equality to the real shape/dimension computation and the real C prototype
renderer is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the array-ness decision and the prototype's
# pointer rendering are modelled DEEPLY below as @Pure functions, and validated
# == the real sympy callees out-of-band by axiom_check.py / G-AX. There is no
# consumed axiom.)
# axioms-end


# pure-start
@Pure
def shape_is_intrinsic(k: int) -> bool:
    """Whether the argument's array shape is intrinsic to the symbol (a matrix,
    tag 1) rather than recovered from the expression (an indexed array, tag 2)
    or absent (a scalar, tag 0)."""
    return k == 1


@Pure
def array_resolved(k: int, present: bool) -> bool:
    """Whether the argument is resolved to be an array (and so carries a
    non-empty dimension list):
      * a matrix (intrinsic shape) is an array regardless of presence;
      * an indexed array is an array only when it appears in the expression;
      * a scalar is never an array."""
    if shape_is_intrinsic(k):
        return True
    if k == 2:
        return present
    return False


@Pure
def arg_is_pointer(has_dims: bool) -> bool:
    """The C prototype renders an argument as a pointer (`*name`) exactly when
    it carries a non-empty dimension list, and as a plain value otherwise."""
    return has_dims


@Pure
def want_pointer(k: int, present: bool) -> bool:
    """The desired pointer declaration for a requested argument of kind k that
    is/ is not present in the expression: a pointer iff the argument resolves
    to an array. A matrix is a pointer even when absent."""
    return arg_is_pointer(array_resolved(k, present))
# pure-end


def pointer_flags(kinds: List[int], present: List[bool]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(present), 1 / 2))
    # the two parallel descriptors are aligned, one entry per requested argument
    Requires(len(kinds) == len(present))
    # each requested argument is scalar (0), matrix (1), or indexed array (2)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                            0 <= kinds[i] and kinds[i] <= 2),
                                     [[kinds[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(present), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the rendered prototype has exactly one flag per requested argument
    Ensures(len(Result()) == len(kinds))
    # each output flag is a pointer iff its argument resolves to an array; a
    # matrix argument is a pointer even when it is absent from the expression
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds) and i < len(present),
                                           Result()[i] == want_pointer(kinds[i], present[i])),
                                    [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    j = 0
    while j < len(kinds):
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(present), 1 / 2))
        Invariant(len(kinds) == len(present))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(kinds))
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                                 0 <= kinds[i] and kinds[i] <= 2),
                                          [[kinds[i]]])))
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < j,
                                                 result[i] == want_pointer(kinds[i], present[i])),
                                          [[result[i]]])))
        Invariant(j <= len(present))
        # invariants-end
        k = kinds[j]
        is_present = present[j]
        # Resolve the argument's array-ness, then render the dimension flag.
        # A matrix is intrinsically an array and is given dimensions whether or
        # not it occurs in the expression. An indexed array is given dimensions
        # only when it occurs (its shape is recovered from the entries there).
        # A scalar never carries dimensions.
        if shape_is_intrinsic(k):
            has_dims = True
        elif k == 2:
            if is_present:
                has_dims = True
            else:
                has_dims = False
        else:
            has_dims = False
        flag = arg_is_pointer(has_dims)
        Assert(flag == want_pointer(k, is_present))
        old_result = result
        result = result + [flag]
        Assert(len(result) == j + 1)
        Assert(result[j] == want_pointer(kinds[j], present[j]))
        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
                                              result[i] == old_result[i]),
                                       [[result[i]]])))
        j = j + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen postcondition is a TOTAL functional spec over the abstract domain: Ensures(len(Result())==len(kinds)) AND Ensures(Forall i in-domain: Result()[i]==want_pointer(kinds[i],present[i])). This pins every output element to the gold per-argument decision, leaving no loophole for a same-spec wrong impl to verify.

All files pass same-spec (spec_signature byte-identical: 8/8, incl. pos_control). Env: SBU_BENCHMARK_DIR=benchmark-verified, python=python. Command form: `python -m swebench_unified.adversary weakness nagini sympy__sympy-16792 <atk>`.

Attack results (weakness):
- atk_1.py PREPATCH BUG (absent matrix -> not pointer; reverts the fix): NOT-A-COUNTEREXAMPLE, verification failed. Direct verify error: 'Loop invariant might not be preserved. Assertion Forall(...(result[i]==want_pointer(kinds[i],present[i]))) might not hold' — the spec rejects the prepatch on exactly kind=1,present=False. prepatch_reproduced=True (G-DIFF class reproduced).
- atk_2.py PARTIAL-DOMAIN (absent args all False): verification failed (spec rejects absent-matrix).
- atk_3.py BOUNDARY off-by-one (while j < len(kinds)-1, short list): verification failed (violates len(Result())==len(kinds)).
- atk_4.py CONTROL-FLOW-EFFECT (swap scalar<->matrix): verification failed.
- atk_6.py matrix -> pointer iff present (partial revert): verification failed.
- atk_7.py UNGROUNDED-ORACLE ECHO (absent indexed over-promoted to pointer): verification failed (absent indexed must be scalar). Direct-verify confirmed: invariant not preserved.
All six wrong impls fail on the value obligation result[i]==want_pointer(...), i.e. the spec genuinely rejects them.

CANDIDATE (shares spec AND verifies): atk_8.py — a genuinely-equivalent restructure computing flag=want_pointer(k,is_present) per element with the frame-preservation asserts. weakness => CANDIDATE-COUNTEREXAMPLE (13.4s). PER PROTOCOL its faithful refined patch was MATERIALIZED (= the gold patch, since its per-element decision is byte-equal to the gold model) and RUN through the official harness: run_resolve('sympy__sympy-16792', patch, retries=0) => RESOLVED=True COMPLETED=True note='resolved'. A verifying impl maps to a RESOLVING patch — no verify-not-correct gap. (atk_5.py, an equivalent restructure WITHOUT the frame asserts, failed verification on a pure proof obligation, not semantics — not a counterexample.)

Positive control pos_control.py (exact gold model impl): Verification successful (14.0s).

Refinement audit (refinement.md §C): legs C1=R, C2=I, C3=R+A-reference, C4=R+A-reference (THE FIX, KeyError branch), C5=R+A-reference, C6=A-reference. axioms-region is EMPTY: no @ContractOnly axiom => NO A-consumed and NO kind-3 legs. The only trust points are A-reference legs, validated out-of-band by axiom_check.py (G-AX), which I RE-RAN against real sympy 1.14.0: exit 0, 'deep model (matrix=>pointer always; indexed=>pointer iff present; scalar=>never) matches real sympy CCodeGen on F2P + 13 boundary + 400 fuzz'. The load-bearing subtlety (an ABSENT IndexedBase reaches the KeyError branch as its scalar label and is NOT promoted; only an absent MatrixSymbol is promoted) is covered by boundary case 'indexed absent (NOT promoted)' + fuzz. Model<->patch correspondence holds.

No verifying wrong impl exists whose faithful patch fails to resolve. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-16792.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A code generator builds the ordered list of function arguments to match a
  caller-supplied argument sequence, then renders a C function prototype from
  it. Each requested argument falls into one of three kinds:

    * a plain scalar quantity;
    * a fixed-shape matrix quantity (always an array — its shape is intrinsic
      to the symbol);
    * an indexed-array quantity whose array shape is known only through the
      indexed entries that occur in the wrapped expression.

  Independently, each requested argument may or may not actually occur in the
  wrapped expression.

  The generated C prototype declares an argument as a pointer (`*name`) exactly
  when that argument is an array, and as a plain value (`name`) otherwise. The
  array-ness is resolved as follows, and element i of the rendered prototype is
  a pointer exactly when:

    * a matrix argument: ALWAYS — its shape is intrinsic, so it is an array
      whether or not it appears in the expression;
    * an indexed-array argument: only when it appears in the expression (its
      shape is recovered from the indexed entries that occur there);
    * a scalar argument: never.

  The behaviour the specification pins is that a matrix argument is declared as
  a pointer even when it does NOT appear in the wrapped expression — its
  intrinsic shape makes it an array regardless of use.

Each requested argument is modelled by a kind tag (`0` = scalar, `1` = matrix,
`2` = indexed-array) and a presence flag (does it occur in the expression). The
C prototype's per-argument pointer decision is rendered as a `bool`. The
specification is carried element-wise via the pure predicate `want_pointer`.

The array-ness decision and the prototype's pointer rendering are modelled
deeply (`shape_is_intrinsic`, `array_resolved`, `arg_is_pointer`); their
equality to the real shape/dimension computation and the real C prototype
renderer is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the array-ness decision and the prototype's
# pointer rendering are modelled DEEPLY below as @Pure functions, and validated
# == the real sympy callees out-of-band by axiom_check.py / G-AX. There is no
# consumed axiom.)
# axioms-end


# pure-start
@Pure
def shape_is_intrinsic(k: int) -> bool:
    """Whether the argument's array shape is intrinsic to the symbol (a matrix,
    tag 1) rather than recovered from the expression (an indexed array, tag 2)
    or absent (a scalar, tag 0)."""
    return k == 1


@Pure
def array_resolved(k: int, present: bool) -> bool:
    """Whether the argument is resolved to be an array (and so carries a
    non-empty dimension list):
      * a matrix (intrinsic shape) is an array regardless of presence;
      * an indexed array is an array only when it appears in the expression;
      * a scalar is never an array."""
    if shape_is_intrinsic(k):
        return True
    if k == 2:
        return present
    return False


@Pure
def arg_is_pointer(has_dims: bool) -> bool:
    """The C prototype renders an argument as a pointer (`*name`) exactly when
    it carries a non-empty dimension list, and as a plain value otherwise."""
    return has_dims


@Pure
def want_pointer(k: int, present: bool) -> bool:
    """The desired pointer declaration for a requested argument of kind k that
    is/ is not present in the expression: a pointer iff the argument resolves
    to an array. A matrix is a pointer even when absent."""
    return arg_is_pointer(array_resolved(k, present))
# pure-end


def pointer_flags(kinds: List[int], present: List[bool]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(present), 1 / 2))
    # the two parallel descriptors are aligned, one entry per requested argument
    Requires(len(kinds) == len(present))
    # each requested argument is scalar (0), matrix (1), or indexed array (2)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                            0 <= kinds[i] and kinds[i] <= 2),
                                     [[kinds[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(present), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the rendered prototype has exactly one flag per requested argument
    Ensures(len(Result()) == len(kinds))
    # each output flag is a pointer iff its argument resolves to an array; a
    # matrix argument is a pointer even when it is absent from the expression
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds) and i < len(present),
                                           Result()[i] == want_pointer(kinds[i], present[i])),
                                    [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    j = 0
    while j < len(kinds):
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(present), 1 / 2))
        Invariant(len(kinds) == len(present))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(kinds))
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                                 0 <= kinds[i] and kinds[i] <= 2),
                                          [[kinds[i]]])))
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < j,
                                                 result[i] == want_pointer(kinds[i], present[i])),
                                          [[result[i]]])))
        Invariant(j <= len(present))
        # invariants-end
        k = kinds[j]
        is_present = present[j]
        # Resolve the argument's array-ness, then render the dimension flag.
        # A matrix is intrinsically an array and is given dimensions whether or
        # not it occurs in the expression. An indexed array is given dimensions
        # only when it occurs (its shape is recovered from the entries there).
        # A scalar never carries dimensions.
        if shape_is_intrinsic(k):
            has_dims = True
        elif k == 2:
            if is_present:
                has_dims = True
            else:
                has_dims = False
        else:
            has_dims = False
        flag = arg_is_pointer(has_dims)
        Assert(flag == want_pointer(k, is_present))
        old_result = result
        result = result + [flag]
        Assert(len(result) == j + 1)
        Assert(result[j] == want_pointer(kinds[j], present[j]))
        Assert(Forall(int, lambda i: (Implies(0 <= i and i < j,
                                              result[i] == old_result[i]),
                                       [[result[i]]])))
        j = j + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen postcondition is a TOTAL functional spec over the abstract domain: Ensures(len(Result())==len(kinds)) AND Ensures(Forall i in-domain: Result()[i]==want_pointer(kinds[i],present[i])). This pins every output element to the gold per-argument decision, leaving no loophole for a same-spec wrong impl to verify.

All files pass same-spec (spec_signature byte-identical: 8/8, incl. pos_control). Env: SBU_BENCHMARK_DIR=benchmark-verified, python=python. Command form: `python -m swebench_unified.adversary weakness nagini sympy__sympy-16792 <atk>`.

Attack results (weakness):
- atk_1.py PREPATCH BUG (absent matrix -> not pointer; reverts the fix): NOT-A-COUNTEREXAMPLE, verification failed. Direct verify error: 'Loop invariant might not be preserved. Assertion Forall(...(result[i]==want_pointer(kinds[i],present[i]))) might not hold' — the spec rejects the prepatch on exactly kind=1,present=False. prepatch_reproduced=True (G-DIFF class reproduced).
- atk_2.py PARTIAL-DOMAIN (absent args all False): verification failed (spec rejects absent-matrix).
- atk_3.py BOUNDARY off-by-one (while j < len(kinds)-1, short list): verification failed (violates len(Result())==len(kinds)).
- atk_4.py CONTROL-FLOW-EFFECT (swap scalar<->matrix): verification failed.
- atk_6.py matrix -> pointer iff present (partial revert): verification failed.
- atk_7.py UNGROUNDED-ORACLE ECHO (absent indexed over-promoted to pointer): verification failed (absent indexed must be scalar). Direct-verify confirmed: invariant not preserved.
All six wrong impls fail on the value obligation result[i]==want_pointer(...), i.e. the spec genuinely rejects them.

CANDIDATE (shares spec AND verifies): atk_8.py — a genuinely-equivalent restructure computing flag=want_pointer(k,is_present) per element with the frame-preservation asserts. weakness => CANDIDATE-COUNTEREXAMPLE (13.4s). PER PROTOCOL its faithful refined patch was MATERIALIZED (= the gold patch, since its per-element decision is byte-equal to the gold model) and RUN through the official harness: run_resolve('sympy__sympy-16792', patch, retries=0) => RESOLVED=True COMPLETED=True note='resolved'. A verifying impl maps to a RESOLVING patch — no verify-not-correct gap. (atk_5.py, an equivalent restructure WITHOUT the frame asserts, failed verification on a pure proof obligation, not semantics — not a counterexample.)

Positive control pos_control.py (exact gold model impl): Verification successful (14.0s).

Refinement audit (refinement.md §C): legs C1=R, C2=I, C3=R+A-reference, C4=R+A-reference (THE FIX, KeyError branch), C5=R+A-reference, C6=A-reference. axioms-region is EMPTY: no @ContractOnly axiom => NO A-consumed and NO kind-3 legs. The only trust points are A-reference legs, validated out-of-band by axiom_check.py (G-AX), which I RE-RAN against real sympy 1.14.0: exit 0, 'deep model (matrix=>pointer always; indexed=>pointer iff present; scalar=>never) matches real sympy CCodeGen on F2P + 13 boundary + 400 fuzz'. The load-bearing subtlety (an ABSENT IndexedBase reaches the KeyError branch as its scalar label and is NOT promoted; only an absent MatrixSymbol is promoted) is covered by boundary case 'indexed absent (NOT promoted)' + fuzz. Model<->patch correspondence holds.

No verifying wrong impl exists whose faithful patch fails to resolve. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeled function pointer_flags / want_pointer(k, present) agrees with the real repo callee (CodeGen.routine + CCodeGen.get_prototype) on every realizable input. Verified in worktree at base_commit 09786a1 (gold patch applied). Enumerated all 6 realizable (kind, present) combos plus a mixed 7-arg ordered sequence — 0 mismatches:
- scalar present  -> plain value (double x)         == want_pointer(0,T)=False
- scalar absent   -> plain value (double w)         == want_pointer(0,F)=False
- matrix present  -> pointer (double *A)            == want_pointer(1,T)=True
- matrix absent   -> pointer (double *C)  [THE FIX] == want_pointer(1,F)=True
- indexed present -> pointer (double *B)            == want_pointer(2,T)=True
- indexed absent  -> plain value (double D)         == want_pointer(2,F)=False

The discriminating clause (absent matrix is a pointer; absent indexed is NOT) is correctly modeled and matches reality: an absent IndexedBase is normalized to its scalar .label at codegen.py:722-729, so isinstance(symbol,(IndexedBase,MatrixSymbol)) is False in the KeyError branch and it stays scalar — exactly the model's k==2&!present->False. The C renderer's rule arg.dimensions truthy iff pointer (get_prototype, codegen.py:913-914, InputArgument never a ResultBase) equals arg_is_pointer(has_dims)==has_dims. same-spec command returns exit 0. No spec drift, no too-strong behavior found; no diverging input exists.

- scalar present  -> plain value (double x)         == want_pointer(0,T)=False
- scalar absent   -> plain value (double w)         == want_pointer(0,F)=False
- matrix present  -> pointer (double *A)            == want_pointer(1,T)=True
- matrix absent   -> pointer (double *C)  [THE FIX] == want_pointer(1,F)=True
- indexed present -> pointer (double *B)            == want_pointer(2,T)=True
- indexed absent  -> plain value (double D)         == want_pointer(2,F)=False

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py projection (docstring + @Pure region shape_is_intrinsic/array_resolved/arg_is_pointer/want_pointer + pre/post-conditions of pointer_flags; impl elided). Mechanical G-LEAK screen (swebench_unified.leakage.screen with the nagini backend + frozen problem_statement/patch) returns passed=True, zero hard failures. Manual review confirms: (1) no diff markers, no patched file path (sympy/utilities/codegen.py) or module path; (2) no gold-patch lines reproduced (no 'dimensions(s)', 'InputArgument', 'isinstance(symbol,(IndexedBase,MatrixSymbol))', "metadata={'dimensions':...}"); (3) gold-changed repo symbols 'dimensions' and 'routine' appear neither as spec-view identifiers nor verbatim in comments (prose uses 'dimension list', not the symbol 'dimensions'); (4) no bug/fix narration — docstring explicitly frames content as 'desired behaviour, not as an edit'. The load-bearing observable the spec pins — an absent matrix argument is still rendered a pointer ('*name') — is already fully public in the problem_statement, which shows the MatrixSymbol('x',2,1)/expr=1.0 case stating 'x should be double *, not double' and that depending on the arg fixes it. The abstract three-kind taxonomy (scalar/matrix/indexed, indexed-iff-present) is a behavioral characterization of the function's domain, not a disclosure of the edit mechanics. refinement.md/mapping.md do quote gold lines + file:line anchors + 'dimensions', but those are auditor-only artifacts, NOT part of the consumer spec view, so out of G-LEAK scope. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
