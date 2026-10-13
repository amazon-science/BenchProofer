# P2 adversarial audit — sympy__sympy-14711

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_return_self.py`, `atk_3_drop_other_vec_self.py`, `atk_4_swallow_neither.py`, `atk_5_reversed_concat.py`, `atk_6_zero_norm_copy.py`, `atk_8_empty.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_skip_guard.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotAVector(Exception):
@@ -67,9 +66,6 @@
     (the constructor never invents a component), never longer."""
     def __init__(self, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # The normalising construction terminates. Level 2: strictly above
-        # `normalise` (level 1), which this body calls.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.terms))  # type: ignore
         Ensures(Acc(list_pred(self.terms)))  # type: ignore
         Ensures(Acc(list_pred(terms), 1 / 2))
@@ -86,9 +82,6 @@
     that is neither is an unsupported addend."""
     def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # Two flag stores plus one list copy: terminating. Level 2 so the
-        # `list(terms)` copy (which carries its own obligation) has room below.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
         Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
         Ensures(Acc(self.terms))  # type: ignore
@@ -124,9 +117,6 @@
     against it."""
     Requires(Acc(other.is_vector, 1 / 2))
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-    # The guard is a single isinstance test: bounded, loop-free work that either
-    # returns or raises. Level 1, strictly below every caller.
-    Requires(MustTerminate(1))
     Ensures(Acc(other.is_vector, 1 / 2))
     Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     Ensures(other.is_vector)
@@ -148,9 +138,6 @@
     shrink it). G-AX validates this against the real constructor (mapping.md
     §3.2)."""
     Requires(Acc(list_pred(terms), 1 / 2))
-    # The frame-merging normaliser walks its argument once and terminates.
-    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
-    Requires(MustTerminate(1))
     Ensures(Acc(list_pred(terms), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
@@ -172,10 +159,6 @@
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     # The scalar zero and a vector are distinct kinds of operand.
     Requires(Implies(other.is_scalar_zero, not other.is_vector))
-    # The sum terminates. Level 3: strictly above vector_guard / normalise
-    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
-    # enough that the `list(self.terms)` copy has room below the caller.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
@@ -212,9 +195,8 @@
             and Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2)
             and not other.is_scalar_zero and not other.is_vector)
     # impl-start
-    if other.is_scalar_zero:
-        return self
     checked = vector_guard(other)  # type: Vec
+    Assert(not other.is_scalar_zero)
     combined = list(self.terms)  # type: List[int]
     j = 0
     while j < len(checked.terms):
@@ -230,11 +212,6 @@
         Invariant(Acc(list_pred(combined)))
         Invariant(0 <= j and j <= len(checked.terms))
         Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
-        # `j` rises by one per pass and the bound len(checked.terms) is fixed
-        # (checked.terms is held read-only at 1/2 and never written), so
-        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
-        # j < len(checked.terms).
-        Invariant(MustTerminate(len(checked.terms) - j + 1))
         # invariants-end
         combined.append(checked.terms[j])
         Assert(ToSeq(checked.terms).take(j + 1)
@@ -243,9 +220,6 @@
     Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
     Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
     result = Vec(combined)  # type: Vec
-    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
-    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
-    # function, so this is exactly clause (2).
     Assert(ToSeq(result.terms)
            == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
     return result
```

Attack 2 — `atk_2_return_self.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotAVector(Exception):
@@ -67,9 +66,6 @@
     (the constructor never invents a component), never longer."""
     def __init__(self, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # The normalising construction terminates. Level 2: strictly above
-        # `normalise` (level 1), which this body calls.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.terms))  # type: ignore
         Ensures(Acc(list_pred(self.terms)))  # type: ignore
         Ensures(Acc(list_pred(terms), 1 / 2))
@@ -86,9 +82,6 @@
     that is neither is an unsupported addend."""
     def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # Two flag stores plus one list copy: terminating. Level 2 so the
-        # `list(terms)` copy (which carries its own obligation) has room below.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
         Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
         Ensures(Acc(self.terms))  # type: ignore
@@ -124,9 +117,6 @@
     against it."""
     Requires(Acc(other.is_vector, 1 / 2))
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-    # The guard is a single isinstance test: bounded, loop-free work that either
-    # returns or raises. Level 1, strictly below every caller.
-    Requires(MustTerminate(1))
     Ensures(Acc(other.is_vector, 1 / 2))
     Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     Ensures(other.is_vector)
@@ -148,9 +138,6 @@
     shrink it). G-AX validates this against the real constructor (mapping.md
     §3.2)."""
     Requires(Acc(list_pred(terms), 1 / 2))
-    # The frame-merging normaliser walks its argument once and terminates.
-    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
-    Requires(MustTerminate(1))
     Ensures(Acc(list_pred(terms), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
@@ -172,10 +159,6 @@
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     # The scalar zero and a vector are distinct kinds of operand.
     Requires(Implies(other.is_scalar_zero, not other.is_vector))
-    # The sum terminates. Level 3: strictly above vector_guard / normalise
-    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
-    # enough that the `list(self.terms)` copy has room below the caller.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
@@ -212,41 +195,5 @@
             and Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2)
             and not other.is_scalar_zero and not other.is_vector)
     # impl-start
-    if other.is_scalar_zero:
-        return self
-    checked = vector_guard(other)  # type: Vec
-    combined = list(self.terms)  # type: List[int]
-    j = 0
-    while j < len(checked.terms):
-        # invariants-start
-        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
-        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
-        Invariant(Acc(other.is_scalar_zero, 1 / 2))
-        Invariant(not other.is_scalar_zero)
-        Invariant(Acc(other.is_vector, 1 / 2))
-        Invariant(other.is_vector)
-        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
-        Invariant(Acc(list_pred(combined)))
-        Invariant(0 <= j and j <= len(checked.terms))
-        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
-        # `j` rises by one per pass and the bound len(checked.terms) is fixed
-        # (checked.terms is held read-only at 1/2 and never written), so
-        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
-        # j < len(checked.terms).
-        Invariant(MustTerminate(len(checked.terms) - j + 1))
-        # invariants-end
-        combined.append(checked.terms[j])
-        Assert(ToSeq(checked.terms).take(j + 1)
-               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
-        j = j + 1
-    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
-    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
-    result = Vec(combined)  # type: Vec
-    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
-    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
-    # function, so this is exactly clause (2).
-    Assert(ToSeq(result.terms)
-           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
-    return result
+    return self
     # impl-end
```

Attack 3 — `atk_3_drop_other_vec_self.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotAVector(Exception):
@@ -67,9 +66,6 @@
     (the constructor never invents a component), never longer."""
     def __init__(self, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # The normalising construction terminates. Level 2: strictly above
-        # `normalise` (level 1), which this body calls.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.terms))  # type: ignore
         Ensures(Acc(list_pred(self.terms)))  # type: ignore
         Ensures(Acc(list_pred(terms), 1 / 2))
@@ -86,9 +82,6 @@
     that is neither is an unsupported addend."""
     def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # Two flag stores plus one list copy: terminating. Level 2 so the
-        # `list(terms)` copy (which carries its own obligation) has room below.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
         Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
         Ensures(Acc(self.terms))  # type: ignore
@@ -124,9 +117,6 @@
     against it."""
     Requires(Acc(other.is_vector, 1 / 2))
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-    # The guard is a single isinstance test: bounded, loop-free work that either
-    # returns or raises. Level 1, strictly below every caller.
-    Requires(MustTerminate(1))
     Ensures(Acc(other.is_vector, 1 / 2))
     Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     Ensures(other.is_vector)
@@ -148,9 +138,6 @@
     shrink it). G-AX validates this against the real constructor (mapping.md
     §3.2)."""
     Requires(Acc(list_pred(terms), 1 / 2))
-    # The frame-merging normaliser walks its argument once and terminates.
-    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
-    Requires(MustTerminate(1))
     Ensures(Acc(list_pred(terms), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
@@ -172,10 +159,6 @@
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     # The scalar zero and a vector are distinct kinds of operand.
     Requires(Implies(other.is_scalar_zero, not other.is_vector))
-    # The sum terminates. Level 3: strictly above vector_guard / normalise
-    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
-    # enough that the `list(self.terms)` copy has room below the caller.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
@@ -215,38 +198,5 @@
     if other.is_scalar_zero:
         return self
     checked = vector_guard(other)  # type: Vec
-    combined = list(self.terms)  # type: List[int]
-    j = 0
-    while j < len(checked.terms):
-        # invariants-start
-        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
-        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
-        Invariant(Acc(other.is_scalar_zero, 1 / 2))
-        Invariant(not other.is_scalar_zero)
-        Invariant(Acc(other.is_vector, 1 / 2))
-        Invariant(other.is_vector)
-        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
-        Invariant(Acc(list_pred(combined)))
-        Invariant(0 <= j and j <= len(checked.terms))
-        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
-        # `j` rises by one per pass and the bound len(checked.terms) is fixed
-        # (checked.terms is held read-only at 1/2 and never written), so
-        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
-        # j < len(checked.terms).
-        Invariant(MustTerminate(len(checked.terms) - j + 1))
-        # invariants-end
-        combined.append(checked.terms[j])
-        Assert(ToSeq(checked.terms).take(j + 1)
-               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
-        j = j + 1
-    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
-    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
-    result = Vec(combined)  # type: Vec
-    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
-    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
-    # function, so this is exactly clause (2).
-    Assert(ToSeq(result.terms)
-           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
-    return result
+    return Vec(list(self.terms))
     # impl-end
```

Attack 4 — `atk_4_swallow_neither.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotAVector(Exception):
@@ -67,9 +66,6 @@
     (the constructor never invents a component), never longer."""
     def __init__(self, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # The normalising construction terminates. Level 2: strictly above
-        # `normalise` (level 1), which this body calls.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.terms))  # type: ignore
         Ensures(Acc(list_pred(self.terms)))  # type: ignore
         Ensures(Acc(list_pred(terms), 1 / 2))
@@ -86,9 +82,6 @@
     that is neither is an unsupported addend."""
     def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # Two flag stores plus one list copy: terminating. Level 2 so the
-        # `list(terms)` copy (which carries its own obligation) has room below.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
         Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
         Ensures(Acc(self.terms))  # type: ignore
@@ -124,9 +117,6 @@
     against it."""
     Requires(Acc(other.is_vector, 1 / 2))
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-    # The guard is a single isinstance test: bounded, loop-free work that either
-    # returns or raises. Level 1, strictly below every caller.
-    Requires(MustTerminate(1))
     Ensures(Acc(other.is_vector, 1 / 2))
     Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     Ensures(other.is_vector)
@@ -148,9 +138,6 @@
     shrink it). G-AX validates this against the real constructor (mapping.md
     §3.2)."""
     Requires(Acc(list_pred(terms), 1 / 2))
-    # The frame-merging normaliser walks its argument once and terminates.
-    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
-    Requires(MustTerminate(1))
     Ensures(Acc(list_pred(terms), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
@@ -172,10 +159,6 @@
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     # The scalar zero and a vector are distinct kinds of operand.
     Requires(Implies(other.is_scalar_zero, not other.is_vector))
-    # The sum terminates. Level 3: strictly above vector_guard / normalise
-    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
-    # enough that the `list(self.terms)` copy has room below the caller.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
@@ -214,39 +197,24 @@
     # impl-start
     if other.is_scalar_zero:
         return self
-    checked = vector_guard(other)  # type: Vec
-    combined = list(self.terms)  # type: List[int]
-    j = 0
-    while j < len(checked.terms):
-        # invariants-start
-        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
-        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
-        Invariant(Acc(other.is_scalar_zero, 1 / 2))
-        Invariant(not other.is_scalar_zero)
-        Invariant(Acc(other.is_vector, 1 / 2))
-        Invariant(other.is_vector)
-        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
-        Invariant(Acc(list_pred(combined)))
-        Invariant(0 <= j and j <= len(checked.terms))
-        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
-        # `j` rises by one per pass and the bound len(checked.terms) is fixed
-        # (checked.terms is held read-only at 1/2 and never written), so
-        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
-        # j < len(checked.terms).
-        Invariant(MustTerminate(len(checked.terms) - j + 1))
-        # invariants-end
-        combined.append(checked.terms[j])
-        Assert(ToSeq(checked.terms).take(j + 1)
-               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
-        j = j + 1
-    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
-    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
-    result = Vec(combined)  # type: Vec
-    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
-    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
-    # function, so this is exactly clause (2).
-    Assert(ToSeq(result.terms)
-           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
-    return result
+    if other.is_vector:
+        combined = list(self.terms)  # type: List[int]
+        j = 0
+        while j < len(other.terms):
+            Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
+            Invariant(Acc(other.is_scalar_zero, 1 / 2))
+            Invariant(not other.is_scalar_zero)
+            Invariant(Acc(other.is_vector, 1 / 2))
+            Invariant(other.is_vector)
+            Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
+            Invariant(Acc(list_pred(combined)))
+            Invariant(0 <= j and j <= len(other.terms))
+            Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms).take(j))
+            combined.append(other.terms[j])
+            Assert(ToSeq(other.terms).take(j + 1)
+                   == ToSeq(other.terms).take(j) + PSeq(other.terms[j]))
+            j = j + 1
+        Assert(ToSeq(other.terms).take(len(other.terms)) == ToSeq(other.terms))
+        return Vec(combined)
+    return self
     # impl-end
```

Attack 5 — `atk_5_reversed_concat.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotAVector(Exception):
@@ -67,9 +66,6 @@
     (the constructor never invents a component), never longer."""
     def __init__(self, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # The normalising construction terminates. Level 2: strictly above
-        # `normalise` (level 1), which this body calls.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.terms))  # type: ignore
         Ensures(Acc(list_pred(self.terms)))  # type: ignore
         Ensures(Acc(list_pred(terms), 1 / 2))
@@ -86,9 +82,6 @@
     that is neither is an unsupported addend."""
     def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # Two flag stores plus one list copy: terminating. Level 2 so the
-        # `list(terms)` copy (which carries its own obligation) has room below.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
         Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
         Ensures(Acc(self.terms))  # type: ignore
@@ -124,9 +117,6 @@
     against it."""
     Requires(Acc(other.is_vector, 1 / 2))
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-    # The guard is a single isinstance test: bounded, loop-free work that either
-    # returns or raises. Level 1, strictly below every caller.
-    Requires(MustTerminate(1))
     Ensures(Acc(other.is_vector, 1 / 2))
     Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     Ensures(other.is_vector)
@@ -148,9 +138,6 @@
     shrink it). G-AX validates this against the real constructor (mapping.md
     §3.2)."""
     Requires(Acc(list_pred(terms), 1 / 2))
-    # The frame-merging normaliser walks its argument once and terminates.
-    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
-    Requires(MustTerminate(1))
     Ensures(Acc(list_pred(terms), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
@@ -172,10 +159,6 @@
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     # The scalar zero and a vector are distinct kinds of operand.
     Requires(Implies(other.is_scalar_zero, not other.is_vector))
-    # The sum terminates. Level 3: strictly above vector_guard / normalise
-    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
-    # enough that the `list(self.terms)` copy has room below the caller.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
@@ -215,10 +198,9 @@
     if other.is_scalar_zero:
         return self
     checked = vector_guard(other)  # type: Vec
-    combined = list(self.terms)  # type: List[int]
+    combined = list(checked.terms)  # type: List[int]
     j = 0
-    while j < len(checked.terms):
-        # invariants-start
+    while j < len(self.terms):
         Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
         Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
         Invariant(Acc(other.is_scalar_zero, 1 / 2))
@@ -228,25 +210,13 @@
         Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
         Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
         Invariant(Acc(list_pred(combined)))
-        Invariant(0 <= j and j <= len(checked.terms))
-        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
-        # `j` rises by one per pass and the bound len(checked.terms) is fixed
-        # (checked.terms is held read-only at 1/2 and never written), so
-        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
-        # j < len(checked.terms).
-        Invariant(MustTerminate(len(checked.terms) - j + 1))
-        # invariants-end
-        combined.append(checked.terms[j])
-        Assert(ToSeq(checked.terms).take(j + 1)
-               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
+        Invariant(0 <= j and j <= len(self.terms))
+        Invariant(ToSeq(combined) == ToSeq(checked.terms) + ToSeq(self.terms).take(j))
+        combined.append(self.terms[j])
+        Assert(ToSeq(self.terms).take(j + 1)
+               == ToSeq(self.terms).take(j) + PSeq(self.terms[j]))
         j = j + 1
-    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
-    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
+    Assert(ToSeq(self.terms).take(len(self.terms)) == ToSeq(self.terms))
     result = Vec(combined)  # type: Vec
-    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
-    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
-    # function, so this is exactly clause (2).
-    Assert(ToSeq(result.terms)
-           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
     return result
     # impl-end
```

Attack 6 — `atk_6_zero_norm_copy.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotAVector(Exception):
@@ -67,9 +66,6 @@
     (the constructor never invents a component), never longer."""
     def __init__(self, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # The normalising construction terminates. Level 2: strictly above
-        # `normalise` (level 1), which this body calls.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.terms))  # type: ignore
         Ensures(Acc(list_pred(self.terms)))  # type: ignore
         Ensures(Acc(list_pred(terms), 1 / 2))
@@ -86,9 +82,6 @@
     that is neither is an unsupported addend."""
     def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # Two flag stores plus one list copy: terminating. Level 2 so the
-        # `list(terms)` copy (which carries its own obligation) has room below.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
         Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
         Ensures(Acc(self.terms))  # type: ignore
@@ -124,9 +117,6 @@
     against it."""
     Requires(Acc(other.is_vector, 1 / 2))
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-    # The guard is a single isinstance test: bounded, loop-free work that either
-    # returns or raises. Level 1, strictly below every caller.
-    Requires(MustTerminate(1))
     Ensures(Acc(other.is_vector, 1 / 2))
     Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     Ensures(other.is_vector)
@@ -148,9 +138,6 @@
     shrink it). G-AX validates this against the real constructor (mapping.md
     §3.2)."""
     Requires(Acc(list_pred(terms), 1 / 2))
-    # The frame-merging normaliser walks its argument once and terminates.
-    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
-    Requires(MustTerminate(1))
     Ensures(Acc(list_pred(terms), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
@@ -172,10 +159,6 @@
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     # The scalar zero and a vector are distinct kinds of operand.
     Requires(Implies(other.is_scalar_zero, not other.is_vector))
-    # The sum terminates. Level 3: strictly above vector_guard / normalise
-    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
-    # enough that the `list(self.terms)` copy has room below the caller.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
@@ -213,12 +196,11 @@
             and not other.is_scalar_zero and not other.is_vector)
     # impl-start
     if other.is_scalar_zero:
-        return self
+        return Vec(list(self.terms))
     checked = vector_guard(other)  # type: Vec
     combined = list(self.terms)  # type: List[int]
     j = 0
     while j < len(checked.terms):
-        # invariants-start
         Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
         Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
         Invariant(Acc(other.is_scalar_zero, 1 / 2))
@@ -230,12 +212,6 @@
         Invariant(Acc(list_pred(combined)))
         Invariant(0 <= j and j <= len(checked.terms))
         Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
-        # `j` rises by one per pass and the bound len(checked.terms) is fixed
-        # (checked.terms is held read-only at 1/2 and never written), so
-        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
-        # j < len(checked.terms).
-        Invariant(MustTerminate(len(checked.terms) - j + 1))
-        # invariants-end
         combined.append(checked.terms[j])
         Assert(ToSeq(checked.terms).take(j + 1)
                == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
@@ -243,10 +219,5 @@
     Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
     Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
     result = Vec(combined)  # type: Vec
-    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
-    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
-    # function, so this is exactly clause (2).
-    Assert(ToSeq(result.terms)
-           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
     return result
     # impl-end
```

Attack 7 — `atk_7_skip_guard.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotAVector(Exception):
@@ -67,9 +66,6 @@
     (the constructor never invents a component), never longer."""
     def __init__(self, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # The normalising construction terminates. Level 2: strictly above
-        # `normalise` (level 1), which this body calls.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.terms))  # type: ignore
         Ensures(Acc(list_pred(self.terms)))  # type: ignore
         Ensures(Acc(list_pred(terms), 1 / 2))
@@ -86,9 +82,6 @@
     that is neither is an unsupported addend."""
     def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # Two flag stores plus one list copy: terminating. Level 2 so the
-        # `list(terms)` copy (which carries its own obligation) has room below.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
         Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
         Ensures(Acc(self.terms))  # type: ignore
@@ -124,9 +117,6 @@
     against it."""
     Requires(Acc(other.is_vector, 1 / 2))
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-    # The guard is a single isinstance test: bounded, loop-free work that either
-    # returns or raises. Level 1, strictly below every caller.
-    Requires(MustTerminate(1))
     Ensures(Acc(other.is_vector, 1 / 2))
     Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     Ensures(other.is_vector)
@@ -148,9 +138,6 @@
     shrink it). G-AX validates this against the real constructor (mapping.md
     §3.2)."""
     Requires(Acc(list_pred(terms), 1 / 2))
-    # The frame-merging normaliser walks its argument once and terminates.
-    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
-    Requires(MustTerminate(1))
     Ensures(Acc(list_pred(terms), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
@@ -172,10 +159,6 @@
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     # The scalar zero and a vector are distinct kinds of operand.
     Requires(Implies(other.is_scalar_zero, not other.is_vector))
-    # The sum terminates. Level 3: strictly above vector_guard / normalise
-    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
-    # enough that the `list(self.terms)` copy has room below the caller.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
@@ -214,39 +197,25 @@
     # impl-start
     if other.is_scalar_zero:
         return self
-    checked = vector_guard(other)  # type: Vec
+    if not other.is_vector:
+        raise NotAVector()
     combined = list(self.terms)  # type: List[int]
     j = 0
-    while j < len(checked.terms):
-        # invariants-start
+    while j < len(other.terms):
         Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
-        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
         Invariant(Acc(other.is_scalar_zero, 1 / 2))
         Invariant(not other.is_scalar_zero)
         Invariant(Acc(other.is_vector, 1 / 2))
         Invariant(other.is_vector)
         Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
         Invariant(Acc(list_pred(combined)))
-        Invariant(0 <= j and j <= len(checked.terms))
-        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
-        # `j` rises by one per pass and the bound len(checked.terms) is fixed
-        # (checked.terms is held read-only at 1/2 and never written), so
-        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
-        # j < len(checked.terms).
-        Invariant(MustTerminate(len(checked.terms) - j + 1))
-        # invariants-end
-        combined.append(checked.terms[j])
-        Assert(ToSeq(checked.terms).take(j + 1)
-               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
+        Invariant(0 <= j and j <= len(other.terms))
+        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms).take(j))
+        combined.append(other.terms[j])
+        Assert(ToSeq(other.terms).take(j + 1)
+               == ToSeq(other.terms).take(j) + PSeq(other.terms[j]))
         j = j + 1
-    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
-    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
+    Assert(ToSeq(other.terms).take(len(other.terms)) == ToSeq(other.terms))
     result = Vec(combined)  # type: Vec
-    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
-    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
-    # function, so this is exactly clause (2).
-    Assert(ToSeq(result.terms)
-           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
     return result
     # impl-end
```

Attack 8 — `atk_8_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NotAVector(Exception):
@@ -67,9 +66,6 @@
     (the constructor never invents a component), never longer."""
     def __init__(self, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # The normalising construction terminates. Level 2: strictly above
-        # `normalise` (level 1), which this body calls.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.terms))  # type: ignore
         Ensures(Acc(list_pred(self.terms)))  # type: ignore
         Ensures(Acc(list_pred(terms), 1 / 2))
@@ -86,9 +82,6 @@
     that is neither is an unsupported addend."""
     def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
         Requires(Acc(list_pred(terms), 1 / 2))
-        # Two flag stores plus one list copy: terminating. Level 2 so the
-        # `list(terms)` copy (which carries its own obligation) has room below.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
         Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
         Ensures(Acc(self.terms))  # type: ignore
@@ -124,9 +117,6 @@
     against it."""
     Requires(Acc(other.is_vector, 1 / 2))
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-    # The guard is a single isinstance test: bounded, loop-free work that either
-    # returns or raises. Level 1, strictly below every caller.
-    Requires(MustTerminate(1))
     Ensures(Acc(other.is_vector, 1 / 2))
     Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     Ensures(other.is_vector)
@@ -148,9 +138,6 @@
     shrink it). G-AX validates this against the real constructor (mapping.md
     §3.2)."""
     Requires(Acc(list_pred(terms), 1 / 2))
-    # The frame-merging normaliser walks its argument once and terminates.
-    # Level 1, strictly below Vec.__init__ (level 2) which calls it.
-    Requires(MustTerminate(1))
     Ensures(Acc(list_pred(terms), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
@@ -172,10 +159,6 @@
     Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
     # The scalar zero and a vector are distinct kinds of operand.
     Requires(Implies(other.is_scalar_zero, not other.is_vector))
-    # The sum terminates. Level 3: strictly above vector_guard / normalise
-    # (level 1) and Vec.__init__ (level 2), which this body calls, and high
-    # enough that the `list(self.terms)` copy has room below the caller.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
@@ -215,38 +198,6 @@
     if other.is_scalar_zero:
         return self
     checked = vector_guard(other)  # type: Vec
-    combined = list(self.terms)  # type: List[int]
-    j = 0
-    while j < len(checked.terms):
-        # invariants-start
-        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
-        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
-        Invariant(Acc(other.is_scalar_zero, 1 / 2))
-        Invariant(not other.is_scalar_zero)
-        Invariant(Acc(other.is_vector, 1 / 2))
-        Invariant(other.is_vector)
-        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
-        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
-        Invariant(Acc(list_pred(combined)))
-        Invariant(0 <= j and j <= len(checked.terms))
-        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
-        # `j` rises by one per pass and the bound len(checked.terms) is fixed
-        # (checked.terms is held read-only at 1/2 and never written), so
-        # len(checked.terms) - j + 1 strictly decreases and stays >= 1 while
-        # j < len(checked.terms).
-        Invariant(MustTerminate(len(checked.terms) - j + 1))
-        # invariants-end
-        combined.append(checked.terms[j])
-        Assert(ToSeq(checked.terms).take(j + 1)
-               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
-        j = j + 1
-    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
-    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
-    result = Vec(combined)  # type: Vec
-    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
-    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
-    # function, so this is exactly clause (2).
-    Assert(ToSeq(result.terms)
-           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
-    return result
+    empty = []  # type: List[int]
+    return Vec(empty)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-14711.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A free vector is a formal sum of components, each living in some component
  family (a "frame"); it is represented by a list of component-family tags.
  Adding a right operand to a left vector is defined as:

    (1) When the right operand is the additive identity (the scalar zero, the
        seed an iterated sum starts from), the sum is the left vector itself,
        unchanged: the component list of the result equals the component list of
        the left operand. This must hold and RETURN NORMALLY: the scalar zero is
        a permitted right operand, never rejected as a non-vector.

    (2) When the right operand is itself a vector, the sum is the re-normalised
        combination of BOTH operands' components: it equals the normal form of
        the two component lists concatenated together. Re-normalisation (the
        normal form) folds same-family components and drops a family whose
        combined contribution vanishes; it never invents a component. The result
        is the normal form of self's components followed by the other's
        components -- so the other operand's components are genuinely combined
        in, not discarded. (The result is NOT, in general, the verbatim
        concatenation: same-family components fold together and cancelling
        families disappear, so the list can only get shorter -- but it is the
        normal form of BOTH operands together, which is not the normal form of
        self alone unless the other operand contributes nothing.)

    (3) A right operand that is neither the scalar zero nor a vector is rejected
        (signalled as not-a-vector). Rejection is MANDATORY: a normal return is
        only permitted when the operand is the scalar zero or a genuine vector
        (clause (3a) in the postconditions) -- such an operand is never
        silently accepted.

A vector is modelled as a minimal class carrying only the touched facet, its
component list ``terms`` (``List[int]``: each entry is an opaque int tag
identifying the component family the term belongs to). The right operand is
modelled by two discriminators: ``is_scalar_zero`` (the additive identity) and
``is_vector`` (a genuine vector). The "operand must be a vector" guard is an
unchanged callee (``vector_guard``), axiomatized: it returns the operand when it
is a vector and signals ``NotAVector`` otherwise. The vector-constructing
normaliser is modelled by ``normal_form`` -- a deterministic, opaque function of
the WHOLE component list (equal lists give equal normal forms; lists that differ
are not provably equal). Its faithful "never grows the list" length bound and
its determinism are validated against the real constructor by axiom_check.py /
G-AX. The reject signal is a user-defined exception class (a builtin exception in
an ``Exsures`` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NotAVector(Exception):
    """Signals that an operand is not a vector. Stands in for the `TypeError`
    the unchanged operand guard raises (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


class Vec:
    """A vector, carrying only its component-family tag list. Construction is a
    NORMALISING operation: the stored list is the normal form of the input
    (same-family components folded together, a family whose combined contribution
    vanishes dropped), so it is not the verbatim input -- it can only get SHORTER
    (the constructor never invents a component), never longer."""
    def __init__(self, terms: List[int]) -> None:
        Requires(Acc(list_pred(terms), 1 / 2))
        Ensures(Acc(self.terms))  # type: ignore
        Ensures(Acc(list_pred(self.terms)))  # type: ignore
        Ensures(Acc(list_pred(terms), 1 / 2))
        # Normalising constructor: the stored list is the normal form of the
        # input; the merge/cancel can only shrink it.
        Ensures(ToSeq(self.terms) == normal_form(ToSeq(terms)))  # type: ignore
        Ensures(len(self.terms) <= len(terms))  # type: ignore
        self.terms = normalise(terms)  # type: List[int]


class Operand:
    """The right-hand operand of the sum. `is_scalar_zero` flags the additive
    identity; `is_vector` flags a genuine vector (carrying `terms`). An operand
    that is neither is an unsupported addend."""
    def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
        Requires(Acc(list_pred(terms), 1 / 2))
        Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
        Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
        Ensures(Acc(self.terms))  # type: ignore
        Ensures(Acc(list_pred(self.terms)))  # type: ignore
        Ensures(Acc(list_pred(terms), 1 / 2))
        Ensures(ToSeq(self.terms) == ToSeq(terms))  # type: ignore
        self.is_scalar_zero = is_scalar_zero
        self.is_vector = is_vector
        self.terms = list(terms)


# axioms-start
@Pure
@ContractOnly
def normal_form(s: PSeq[int]) -> PSeq[int]:
    """The vector-constructing normaliser as a deterministic pure function of
    the WHOLE component sequence (A-reference). It folds same-family components
    and drops a family whose combined contribution vanishes, so it never invents
    a component: the normal form is no longer than the input (and may be strictly
    shorter when families merge or cancel). Being a function, equal inputs give
    equal normal forms and inputs that differ are NOT provably equal -- so the
    normal form of BOTH operands' components together is not provably the normal
    form of self's components alone. G-AX validates the length bound and the
    determinism against the real constructor (mapping.md §3.2)."""
    Ensures(len(Result()) <= len(s))


@ContractOnly
def vector_guard(other: Operand) -> Vec:
    """The operand guard: returns the operand as a vector when it IS a vector,
    and signals `NotAVector` otherwise (the scalar zero is not a vector). The
    weakest contract the proof needs (mapping.md §3); G-AX runs the real callee
    against it."""
    Requires(Acc(other.is_vector, 1 / 2))
    Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    Ensures(Acc(other.is_vector, 1 / 2))
    Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    Ensures(other.is_vector)
    Ensures(Acc(Result().terms, 1 / 2))
    Ensures(Acc(list_pred(Result().terms), 1 / 2))
    Ensures(ToSeq(Result().terms) == ToSeq(other.terms))
    Exsures(NotAVector,
            Acc(other.is_vector, 1 / 2)
            and Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2)
            and not other.is_vector)


@ContractOnly
def normalise(terms: List[int]) -> List[int]:
    """The vector-constructing normaliser (impl helper): builds a vector's
    stored component list from a raw concatenated component list by applying the
    `normal_form` merge. The stored list's contents are exactly the normal form
    of the input, and it is no longer than the input (the merge/cancel can only
    shrink it). G-AX validates this against the real constructor (mapping.md
    §3.2)."""
    Requires(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
    Ensures(len(Result()) <= len(terms))
# axioms-end


# pure-start
# (no module-level pure helpers required: the behaviour is stated directly over
# the component-family lists via ToSeq and the normal_form function.)
# pure-end


def vec_add(self: Vec, other: Operand) -> Vec:
    # pre-conditions-start
    Requires(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
    Requires(Acc(other.is_scalar_zero, 1 / 2))
    Requires(Acc(other.is_vector, 1 / 2))
    Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    # The scalar zero and a vector are distinct kinds of operand.
    Requires(Implies(other.is_scalar_zero, not other.is_vector))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
    Ensures(Acc(other.is_scalar_zero, 1 / 2))
    Ensures(Acc(other.is_vector, 1 / 2))
    Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    Ensures(Acc(Result().terms, 1 / 4))
    Ensures(Acc(list_pred(Result().terms), 1 / 4))
    # (1) Adding the scalar zero returns the left vector unchanged (and returns
    #     NORMALLY for it: the scalar zero is a well-defined right operand).
    Ensures(Implies(other.is_scalar_zero,
                    ToSeq(Result().terms) == ToSeq(self.terms)))
    # (2) Adding a genuine vector yields the normal form of BOTH operands'
    #     components concatenated together: the result combines self's components
    #     WITH the other operand's components, then re-normalises (folds
    #     same-family components, drops a vanishing family). It is the normal form
    #     of self.terms ++ other.terms -- NOT the normal form of self alone (that
    #     would discard the other operand) and NOT the verbatim concatenation.
    Ensures(Implies(other.is_vector,
                    ToSeq(Result().terms)
                    == normal_form(ToSeq(self.terms) + ToSeq(other.terms))))
    # (3a) A NORMAL return happens ONLY for the scalar zero or a genuine
    #      vector: an operand that is neither MUST raise (clause (3) below) --
    #      the real guard raises TypeError on it, it is never silently
    #      accepted. Without this clause both Implies above are vacuous on the
    #      neither-operand state and a swallowing normal return would verify.
    Ensures(other.is_scalar_zero or other.is_vector)
    # post-conditions-end
    # (3) An operand that is neither the scalar zero nor a vector is rejected.
    Exsures(NotAVector,
            Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4)
            and Acc(other.is_scalar_zero, 1 / 2)
            and Acc(other.is_vector, 1 / 2)
            and Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2)
            and not other.is_scalar_zero and not other.is_vector)
    # impl-start
    if other.is_scalar_zero:
        return self
    checked = vector_guard(other)  # type: Vec
    combined = list(self.terms)  # type: List[int]
    j = 0
    while j < len(checked.terms):
        # invariants-start
        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
        Invariant(Acc(other.is_scalar_zero, 1 / 2))
        Invariant(not other.is_scalar_zero)
        Invariant(Acc(other.is_vector, 1 / 2))
        Invariant(other.is_vector)
        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
        Invariant(Acc(list_pred(combined)))
        Invariant(0 <= j and j <= len(checked.terms))
        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
        # invariants-end
        combined.append(checked.terms[j])
        Assert(ToSeq(checked.terms).take(j + 1)
               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
        j = j + 1
    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
    result = Vec(combined)  # type: Vec
    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
    # function, so this is exactly clause (2).
    Assert(ToSeq(result.terms)
           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-14711 (nagini). Env: verifier via scripts/nagini_verify.sh; adversary+harness driven by python; SBU_BENCHMARK_DIR=benchmark-verified.

Positive control (bundle model.py copy): bash scripts/nagini_verify.sh positive_control.py -> Verification successful (13.0s). Gold patch control: run_resolve -> RESOLVED=True COMPLETED=True. Harness confirmed working before trusting any non-resolve.

8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec` exit 0), verifications run concurrently in batches of <=3 (each spawns JVM+Z3):
- atk_1_prepatch (model_prepatch.py, prepatch bug re-encoded): weakness -> NOT-A-COUNTEREXAMPLE, does not verify (spec senses the missing short-circuit; G-DIFF). prepatch_reproduced=true.
- atk_2_return_self (partial-domain: drop other, return self always): NOT-CE, fails verify (clause 2 rejects dropping other; normal_form(self++other)!=normal_form(self)).
- atk_3_drop_other_vec_self (gold zero branch, vector branch returns Vec(self.terms)): NOT-CE, fails verify (clause 2).
- atk_4_swallow_neither (gold zero+vector branches, neither-operand falls through to `return self`): NOT-CE, fails verify (clause 3a Ensures(is_scalar_zero or is_vector) obliges the raise).
- atk_5_reversed_concat (build checked.terms ++ self.terms): NOT-CE, fails verify (clause 2 pins self++other order).
- atk_6_zero_norm_copy (scalar-zero returns Vec(list(self.terms)) instead of self): NOT-CE, fails verify (clause 1 pins ToSeq(Result)==ToSeq(self), Vec re-normalises so not provably equal).
- atk_7_skip_guard (control-flow variant: inline the guard as `if not other.is_vector: raise NotAVector()` instead of calling vector_guard; otherwise gold): weakness -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 13.4s). MATERIALIZED faithful patch (patch_atk7.diff: inline `if not isinstance(other, Vector): raise TypeError('A Vector must be supplied')` in place of `_check_vector(other)`) built via a real git checkout of the base-commit vector.py so hunk headers/context are exact. run_resolve -> RESOLVED=True COMPLETED=True. This is a behavioral ECHO of the gold (inlining the unchanged _check_vector guard), NOT a spec weakness. (Note: two earlier `no report / COMPLETED=False` runs of this patch were malformed-hunk-header artifacts, not non-resolutions; corrected diff resolves, and the gold control confirms the harness is healthy.)
- atk_8_empty (drop both operands, return Vec([])): NOT-CE, fails verify (clause 2; normal_form(empty)!=normal_form(self++other)).

No verifying wrong-impl whose faithful patch fails to resolve was found; the single CANDIDATE resolves. Verify=>correct is NOT broken.

refinement.md A-leg audit: A1=R (Vector<->Vec, .args<->.terms), A2=R+I (the changed hunk `other==0`/`is_scalar_zero`, modeled DEEPLY not axiomatized), A3=A-consumed (vector_guard<->_check_vector, proof consumes Ensures/Exsures), A4a=R (append loop = list concat argument), A4b=A-reference (normal_form/normalise<->Vector.__init__ frame-keyed merging constructor; content-bearing contract len(result)<=len(input) AND determinism, validated by axiom_check.py/G-AX). No kind-3 legs. A-leg correspondence to the real callees holds and matches the recorded G-PANEL-2 empirical validation (both callees patch-invariant library calls). Clause (2)'s grounded normal_form(self++other) is what closes the length-only hole the prior refinement shipped; it is not an ungrounded answer-key oracle.

VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_return_self.py`, `atk_3_drop_other_vec_self.py`, `atk_4_swallow_neither.py`, `atk_5_reversed_concat.py`, `atk_6_zero_norm_copy.py`, `atk_8_empty.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_skip_guard.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_return_self.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_drop_other_vec_self.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_swallow_neither.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_reversed_concat.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_zero_norm_copy.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_skip_guard.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_empty.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-14711.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A free vector is a formal sum of components, each living in some component
  family (a "frame"); it is represented by a list of component-family tags.
  Adding a right operand to a left vector is defined as:

    (1) When the right operand is the additive identity (the scalar zero, the
        seed an iterated sum starts from), the sum is the left vector itself,
        unchanged: the component list of the result equals the component list of
        the left operand. This must hold and RETURN NORMALLY: the scalar zero is
        a permitted right operand, never rejected as a non-vector.

    (2) When the right operand is itself a vector, the sum is the re-normalised
        combination of BOTH operands' components: it equals the normal form of
        the two component lists concatenated together. Re-normalisation (the
        normal form) folds same-family components and drops a family whose
        combined contribution vanishes; it never invents a component. The result
        is the normal form of self's components followed by the other's
        components -- so the other operand's components are genuinely combined
        in, not discarded. (The result is NOT, in general, the verbatim
        concatenation: same-family components fold together and cancelling
        families disappear, so the list can only get shorter -- but it is the
        normal form of BOTH operands together, which is not the normal form of
        self alone unless the other operand contributes nothing.)

    (3) A right operand that is neither the scalar zero nor a vector is rejected
        (signalled as not-a-vector). Rejection is MANDATORY: a normal return is
        only permitted when the operand is the scalar zero or a genuine vector
        (clause (3a) in the postconditions) -- such an operand is never
        silently accepted.

A vector is modelled as a minimal class carrying only the touched facet, its
component list ``terms`` (``List[int]``: each entry is an opaque int tag
identifying the component family the term belongs to). The right operand is
modelled by two discriminators: ``is_scalar_zero`` (the additive identity) and
``is_vector`` (a genuine vector). The "operand must be a vector" guard is an
unchanged callee (``vector_guard``), axiomatized: it returns the operand when it
is a vector and signals ``NotAVector`` otherwise. The vector-constructing
normaliser is modelled by ``normal_form`` -- a deterministic, opaque function of
the WHOLE component list (equal lists give equal normal forms; lists that differ
are not provably equal). Its faithful "never grows the list" length bound and
its determinism are validated against the real constructor by axiom_check.py /
G-AX. The reject signal is a user-defined exception class (a builtin exception in
an ``Exsures`` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NotAVector(Exception):
    """Signals that an operand is not a vector. Stands in for the `TypeError`
    the unchanged operand guard raises (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


class Vec:
    """A vector, carrying only its component-family tag list. Construction is a
    NORMALISING operation: the stored list is the normal form of the input
    (same-family components folded together, a family whose combined contribution
    vanishes dropped), so it is not the verbatim input -- it can only get SHORTER
    (the constructor never invents a component), never longer."""
    def __init__(self, terms: List[int]) -> None:
        Requires(Acc(list_pred(terms), 1 / 2))
        Ensures(Acc(self.terms))  # type: ignore
        Ensures(Acc(list_pred(self.terms)))  # type: ignore
        Ensures(Acc(list_pred(terms), 1 / 2))
        # Normalising constructor: the stored list is the normal form of the
        # input; the merge/cancel can only shrink it.
        Ensures(ToSeq(self.terms) == normal_form(ToSeq(terms)))  # type: ignore
        Ensures(len(self.terms) <= len(terms))  # type: ignore
        self.terms = normalise(terms)  # type: List[int]


class Operand:
    """The right-hand operand of the sum. `is_scalar_zero` flags the additive
    identity; `is_vector` flags a genuine vector (carrying `terms`). An operand
    that is neither is an unsupported addend."""
    def __init__(self, is_scalar_zero: bool, is_vector: bool, terms: List[int]) -> None:
        Requires(Acc(list_pred(terms), 1 / 2))
        Ensures(Acc(self.is_scalar_zero) and self.is_scalar_zero == is_scalar_zero)  # type: ignore
        Ensures(Acc(self.is_vector) and self.is_vector == is_vector)  # type: ignore
        Ensures(Acc(self.terms))  # type: ignore
        Ensures(Acc(list_pred(self.terms)))  # type: ignore
        Ensures(Acc(list_pred(terms), 1 / 2))
        Ensures(ToSeq(self.terms) == ToSeq(terms))  # type: ignore
        self.is_scalar_zero = is_scalar_zero
        self.is_vector = is_vector
        self.terms = list(terms)


# axioms-start
@Pure
@ContractOnly
def normal_form(s: PSeq[int]) -> PSeq[int]:
    """The vector-constructing normaliser as a deterministic pure function of
    the WHOLE component sequence (A-reference). It folds same-family components
    and drops a family whose combined contribution vanishes, so it never invents
    a component: the normal form is no longer than the input (and may be strictly
    shorter when families merge or cancel). Being a function, equal inputs give
    equal normal forms and inputs that differ are NOT provably equal -- so the
    normal form of BOTH operands' components together is not provably the normal
    form of self's components alone. G-AX validates the length bound and the
    determinism against the real constructor (mapping.md §3.2)."""
    Ensures(len(Result()) <= len(s))


@ContractOnly
def vector_guard(other: Operand) -> Vec:
    """The operand guard: returns the operand as a vector when it IS a vector,
    and signals `NotAVector` otherwise (the scalar zero is not a vector). The
    weakest contract the proof needs (mapping.md §3); G-AX runs the real callee
    against it."""
    Requires(Acc(other.is_vector, 1 / 2))
    Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    Ensures(Acc(other.is_vector, 1 / 2))
    Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    Ensures(other.is_vector)
    Ensures(Acc(Result().terms, 1 / 2))
    Ensures(Acc(list_pred(Result().terms), 1 / 2))
    Ensures(ToSeq(Result().terms) == ToSeq(other.terms))
    Exsures(NotAVector,
            Acc(other.is_vector, 1 / 2)
            and Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2)
            and not other.is_vector)


@ContractOnly
def normalise(terms: List[int]) -> List[int]:
    """The vector-constructing normaliser (impl helper): builds a vector's
    stored component list from a raw concatenated component list by applying the
    `normal_form` merge. The stored list's contents are exactly the normal form
    of the input, and it is no longer than the input (the merge/cancel can only
    shrink it). G-AX validates this against the real constructor (mapping.md
    §3.2)."""
    Requires(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == normal_form(ToSeq(terms)))
    Ensures(len(Result()) <= len(terms))
# axioms-end


# pure-start
# (no module-level pure helpers required: the behaviour is stated directly over
# the component-family lists via ToSeq and the normal_form function.)
# pure-end


def vec_add(self: Vec, other: Operand) -> Vec:
    # pre-conditions-start
    Requires(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
    Requires(Acc(other.is_scalar_zero, 1 / 2))
    Requires(Acc(other.is_vector, 1 / 2))
    Requires(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    # The scalar zero and a vector are distinct kinds of operand.
    Requires(Implies(other.is_scalar_zero, not other.is_vector))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4))
    Ensures(Acc(other.is_scalar_zero, 1 / 2))
    Ensures(Acc(other.is_vector, 1 / 2))
    Ensures(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
    Ensures(Acc(Result().terms, 1 / 4))
    Ensures(Acc(list_pred(Result().terms), 1 / 4))
    # (1) Adding the scalar zero returns the left vector unchanged (and returns
    #     NORMALLY for it: the scalar zero is a well-defined right operand).
    Ensures(Implies(other.is_scalar_zero,
                    ToSeq(Result().terms) == ToSeq(self.terms)))
    # (2) Adding a genuine vector yields the normal form of BOTH operands'
    #     components concatenated together: the result combines self's components
    #     WITH the other operand's components, then re-normalises (folds
    #     same-family components, drops a vanishing family). It is the normal form
    #     of self.terms ++ other.terms -- NOT the normal form of self alone (that
    #     would discard the other operand) and NOT the verbatim concatenation.
    Ensures(Implies(other.is_vector,
                    ToSeq(Result().terms)
                    == normal_form(ToSeq(self.terms) + ToSeq(other.terms))))
    # (3a) A NORMAL return happens ONLY for the scalar zero or a genuine
    #      vector: an operand that is neither MUST raise (clause (3) below) --
    #      the real guard raises TypeError on it, it is never silently
    #      accepted. Without this clause both Implies above are vacuous on the
    #      neither-operand state and a swallowing normal return would verify.
    Ensures(other.is_scalar_zero or other.is_vector)
    # post-conditions-end
    # (3) An operand that is neither the scalar zero nor a vector is rejected.
    Exsures(NotAVector,
            Acc(self.terms, 1 / 4) and Acc(list_pred(self.terms), 1 / 4)
            and Acc(other.is_scalar_zero, 1 / 2)
            and Acc(other.is_vector, 1 / 2)
            and Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2)
            and not other.is_scalar_zero and not other.is_vector)
    # impl-start
    if other.is_scalar_zero:
        return self
    checked = vector_guard(other)  # type: Vec
    combined = list(self.terms)  # type: List[int]
    j = 0
    while j < len(checked.terms):
        # invariants-start
        Invariant(Acc(self.terms, 1 / 2) and Acc(list_pred(self.terms), 1 / 2))
        Invariant(Acc(checked.terms, 1 / 2) and Acc(list_pred(checked.terms), 1 / 2))
        Invariant(Acc(other.is_scalar_zero, 1 / 2))
        Invariant(not other.is_scalar_zero)
        Invariant(Acc(other.is_vector, 1 / 2))
        Invariant(other.is_vector)
        Invariant(Acc(other.terms, 1 / 2) and Acc(list_pred(other.terms), 1 / 2))
        Invariant(ToSeq(checked.terms) == ToSeq(other.terms))
        Invariant(Acc(list_pred(combined)))
        Invariant(0 <= j and j <= len(checked.terms))
        Invariant(ToSeq(combined) == ToSeq(self.terms) + ToSeq(checked.terms).take(j))
        # invariants-end
        combined.append(checked.terms[j])
        Assert(ToSeq(checked.terms).take(j + 1)
               == ToSeq(checked.terms).take(j) + PSeq(checked.terms[j]))
        j = j + 1
    Assert(ToSeq(checked.terms).take(len(checked.terms)) == ToSeq(checked.terms))
    Assert(ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms))
    result = Vec(combined)  # type: Vec
    # Vec.__init__ pins ToSeq(result.terms) == normal_form(ToSeq(combined)), and
    # ToSeq(combined) == ToSeq(self.terms) + ToSeq(other.terms); normal_form is a
    # function, so this is exactly clause (2).
    Assert(ToSeq(result.terms)
           == normal_form(ToSeq(self.terms) + ToSeq(other.terms)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sympy__sympy-14711 (nagini). Env: verifier via scripts/nagini_verify.sh; adversary+harness driven by python; SBU_BENCHMARK_DIR=benchmark-verified.

Positive control (bundle model.py copy): bash scripts/nagini_verify.sh positive_control.py -> Verification successful (13.0s). Gold patch control: run_resolve -> RESOLVED=True COMPLETED=True. Harness confirmed working before trusting any non-resolve.

8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec` exit 0), verifications run concurrently in batches of <=3 (each spawns JVM+Z3):
- atk_1_prepatch (model_prepatch.py, prepatch bug re-encoded): weakness -> NOT-A-COUNTEREXAMPLE, does not verify (spec senses the missing short-circuit; G-DIFF). prepatch_reproduced=true.
- atk_2_return_self (partial-domain: drop other, return self always): NOT-CE, fails verify (clause 2 rejects dropping other; normal_form(self++other)!=normal_form(self)).
- atk_3_drop_other_vec_self (gold zero branch, vector branch returns Vec(self.terms)): NOT-CE, fails verify (clause 2).
- atk_4_swallow_neither (gold zero+vector branches, neither-operand falls through to `return self`): NOT-CE, fails verify (clause 3a Ensures(is_scalar_zero or is_vector) obliges the raise).
- atk_5_reversed_concat (build checked.terms ++ self.terms): NOT-CE, fails verify (clause 2 pins self++other order).
- atk_6_zero_norm_copy (scalar-zero returns Vec(list(self.terms)) instead of self): NOT-CE, fails verify (clause 1 pins ToSeq(Result)==ToSeq(self), Vec re-normalises so not provably equal).
- atk_7_skip_guard (control-flow variant: inline the guard as `if not other.is_vector: raise NotAVector()` instead of calling vector_guard; otherwise gold): weakness -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 13.4s). MATERIALIZED faithful patch (patch_atk7.diff: inline `if not isinstance(other, Vector): raise TypeError('A Vector must be supplied')` in place of `_check_vector(other)`) built via a real git checkout of the base-commit vector.py so hunk headers/context are exact. run_resolve -> RESOLVED=True COMPLETED=True. This is a behavioral ECHO of the gold (inlining the unchanged _check_vector guard), NOT a spec weakness. (Note: two earlier `no report / COMPLETED=False` runs of this patch were malformed-hunk-header artifacts, not non-resolutions; corrected diff resolves, and the gold control confirms the harness is healthy.)
- atk_8_empty (drop both operands, return Vec([])): NOT-CE, fails verify (clause 2; normal_form(empty)!=normal_form(self++other)).

No verifying wrong-impl whose faithful patch fails to resolve was found; the single CANDIDATE resolves. Verify=>correct is NOT broken.

refinement.md A-leg audit: A1=R (Vector<->Vec, .args<->.terms), A2=R+I (the changed hunk `other==0`/`is_scalar_zero`, modeled DEEPLY not axiomatized), A3=A-consumed (vector_guard<->_check_vector, proof consumes Ensures/Exsures), A4a=R (append loop = list concat argument), A4b=A-reference (normal_form/normalise<->Vector.__init__ frame-keyed merging constructor; content-bearing contract len(result)<=len(input) AND determinism, validated by axiom_check.py/G-AX). No kind-3 legs. A-leg correspondence to the real callees holds and matches the recorded G-PANEL-2 empirical validation (both callees patch-invariant library calls). Clause (2)'s grounded normal_form(self++other) is what closes the length-only hole the prior refinement shipped; it is not an ungrounded answer-key oracle.

VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit found no divergence between the modeled vec_add spec and the real Vector.__add__ (sympy/physics/vector/vector.py:58) at base_commit c6753448. Evidence: (1) Nagini verifies model.py RC=0 (12.6s). (2) axiom_check.py runs the REAL callees and passes RC=0 (14 Vector identity cases, 7 scalar-zero raises, 29 boundary + 2000 fuzz non-Vector raises for _check_vector; never-grows bound + determinism + combined!=self distinguisher for Vector.__init__ on 10 boundary pairs incl. >=6 strict merges + 500 fuzz). (3) I directly enumerated all operand classes against a faithful reconstruction of the patched __add__: scalar 0/S(0) -> normal return of self (clause 1); genuine vector -> normal_form(self++other) which equals real Vector(self.args+other.args) (clause 2); non-zero scalar/string/object -> TypeError->NotAVector (clause 3); clause (3a) normal-return-only-for-0-or-Vector matches real semantics. (4) Zero-vector subtlety verified: N.x-N.x==0 is True, real code short-circuits on other==0 returning self; the model maps it to is_scalar_zero=True under Implies(is_scalar_zero,not is_vector), giving identical result, and even the is_vector alt path yields normal_form(self++[])==normal_form(self)==self, so no diverging input exists. Clause (2) is content-bearing normal_form(self++other), not verbatim concat (faithful to frame-keyed merge) and not a weak length bound (excludes dropped-other impls). No spec-too-strong / drift defect identified.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard failures). Independent review confirms the spec view leaks nothing about the gold edit (`if other == 0: return self`) beyond the PUBLIC problem_statement. The problem_statement itself already reveals the entire fix — its traceback contains the commented `#if other == 0: return self`, the full `__add__` body, `_check_vector`, and `raise TypeError('A Vector must be supplied')`, and the issue title is 'vector add 0 error'. Spec-view specifics: (a) no diff markers; (b) patched file path `sympy/physics/vector/vector.py` and its dotted module form never appear; (c) gold changed lines `if other == 0:` / `return self` are NOT reproduced — the impl region is elided to `...` and clause (1) states behavior abstractly ('the sum is the left vector itself, unchanged'), not the literal code; (d) the only distinctive patch-changed symbol is `hash` (from the `def __hash__` section header), never echoed in a spec-view identifier or comment; (e) no bug/fix/patch/regression narration. The spec is framed as desired behavior over abstract carriers (Vec, Operand, is_scalar_zero, is_vector, normal_form) and localizes the edit no more than the public issue already does — if anything, less. Note: refinement.md/mapping.md quote the gold hunk directly, but those are AUDITOR-only artifacts, not part of the solver-visible spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
