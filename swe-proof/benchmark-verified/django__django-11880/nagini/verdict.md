# P2 adversarial audit — django__django-11880

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -58,10 +57,6 @@
 
 class Field:
     def __init__(self) -> None:
-        # Terminates: no loops and no calls — exactly three attribute stores.
-        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
-        # strictly exceed its callee's) and above the list literals it builds.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
         Ensures(len(self.msg_codes) == 0)  # type: ignore
         Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
@@ -82,7 +77,6 @@
     Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
     # The two arrays carrying the override mapping are index-aligned.
     Requires(len(self.msg_codes) == len(self.msg_values))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The original field is left exactly as it was: same overrides, same
@@ -125,77 +119,23 @@
                                             Result().validators[k] == self.validators[k]))))
     # post-conditions-end
     # impl-start
+    # ATTACK (prepatch bug): shallow copy aliases the message collections; only
+    # validators are freshly copied. Duplicate shares self's msg collections.
     result = Field()
-
-    # result.error_messages = self.error_messages.copy()  -- a fresh collection
-    # holding the same overrides as the original (the added line).
-    a = 0
-    while a < len(self.msg_codes):
-        # invariants-start
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(len(result.validators) == 0)
-        Invariant(0 <= a and a <= len(self.msg_codes))
-        Invariant(len(result.msg_codes) == a)
-        Invariant(len(result.msg_values) == a)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
-                                                  result.msg_values[k] == self.msg_values[k]))))
-        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
-        # invariants-end
-        result.msg_codes.append(self.msg_codes[a])
-        result.msg_values.append(self.msg_values[a])
-        a = a + 1
-
-    # result.validators = self.validators[:]  -- a fresh list holding the same
-    # validators in order (this collection was already copied before the fix).
+    result.msg_codes = self.msg_codes
+    result.msg_values = self.msg_values
     b = 0
     while b < len(self.validators):
-        # invariants-start
         Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
+        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
+        Invariant(result.validators is not self.validators)
         Invariant(len(self.validators) == Old(len(self.validators)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                   self.validators[k] == Old(self.validators[k])))))
-        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(result.validators is not self.validators)
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(len(result.msg_codes) == len(self.msg_codes))
-        Invariant(len(result.msg_values) == len(self.msg_values))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  result.msg_values[k] == self.msg_values[k]))))
         Invariant(0 <= b and b <= len(self.validators))
         Invariant(len(result.validators) == b)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
                                                   result.validators[k] == self.validators[k]))))
-        Invariant(MustTerminate(len(self.validators) - b + 1))
-        # invariants-end
         result.validators.append(self.validators[b])
         b = b + 1
     return result
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -58,10 +57,6 @@
 
 class Field:
     def __init__(self) -> None:
-        # Terminates: no loops and no calls — exactly three attribute stores.
-        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
-        # strictly exceed its callee's) and above the list literals it builds.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
         Ensures(len(self.msg_codes) == 0)  # type: ignore
         Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
@@ -82,7 +77,6 @@
     Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
     # The two arrays carrying the override mapping are index-aligned.
     Requires(len(self.msg_codes) == len(self.msg_values))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The original field is left exactly as it was: same overrides, same
@@ -125,28 +119,18 @@
                                             Result().validators[k] == self.validators[k]))))
     # post-conditions-end
     # impl-start
+    # ATTACK (partial-domain): copy msg entries for a < len-1, dropping the last.
     result = Field()
-
-    # result.error_messages = self.error_messages.copy()  -- a fresh collection
-    # holding the same overrides as the original (the added line).
     a = 0
-    while a < len(self.msg_codes):
-        # invariants-start
+    while a < len(self.msg_codes) - 1:
         Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
         Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
         Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
         Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
         Invariant(result.msg_codes is not self.msg_codes)
         Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
         Invariant(result.msg_values is not self.msg_values)
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(len(result.validators) == 0)
         Invariant(0 <= a and a <= len(self.msg_codes))
         Invariant(len(result.msg_codes) == a)
         Invariant(len(result.msg_values) == a)
@@ -154,48 +138,19 @@
                                                   result.msg_codes[k] == self.msg_codes[k]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                   result.msg_values[k] == self.msg_values[k]))))
-        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
-        # invariants-end
         result.msg_codes.append(self.msg_codes[a])
         result.msg_values.append(self.msg_values[a])
         a = a + 1
-
-    # result.validators = self.validators[:]  -- a fresh list holding the same
-    # validators in order (this collection was already copied before the fix).
     b = 0
     while b < len(self.validators):
-        # invariants-start
         Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(len(self.validators) == Old(len(self.validators)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
-                                                  self.validators[k] == Old(self.validators[k])))))
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
         Invariant(result.validators is not self.validators)
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(len(result.msg_codes) == len(self.msg_codes))
-        Invariant(len(result.msg_values) == len(self.msg_values))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  result.msg_values[k] == self.msg_values[k]))))
+        Invariant(len(self.validators) == Old(len(self.validators)))
         Invariant(0 <= b and b <= len(self.validators))
         Invariant(len(result.validators) == b)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
                                                   result.validators[k] == self.validators[k]))))
-        Invariant(MustTerminate(len(self.validators) - b + 1))
-        # invariants-end
         result.validators.append(self.validators[b])
         b = b + 1
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -58,10 +57,6 @@
 
 class Field:
     def __init__(self) -> None:
-        # Terminates: no loops and no calls — exactly three attribute stores.
-        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
-        # strictly exceed its callee's) and above the list literals it builds.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
         Ensures(len(self.msg_codes) == 0)  # type: ignore
         Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
@@ -82,7 +77,6 @@
     Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
     # The two arrays carrying the override mapping are index-aligned.
     Requires(len(self.msg_codes) == len(self.msg_values))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The original field is left exactly as it was: same overrides, same
@@ -125,77 +119,30 @@
                                             Result().validators[k] == self.validators[k]))))
     # post-conditions-end
     # impl-start
+    # ATTACK (boundary off-by-one): start copying msg entries at index 1.
     result = Field()
-
-    # result.error_messages = self.error_messages.copy()  -- a fresh collection
-    # holding the same overrides as the original (the added line).
-    a = 0
+    a = 1
     while a < len(self.msg_codes):
-        # invariants-start
         Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
         Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
         Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
         Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
         Invariant(result.msg_codes is not self.msg_codes)
         Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
         Invariant(result.msg_values is not self.msg_values)
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(len(result.validators) == 0)
-        Invariant(0 <= a and a <= len(self.msg_codes))
-        Invariant(len(result.msg_codes) == a)
-        Invariant(len(result.msg_values) == a)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
-                                                  result.msg_values[k] == self.msg_values[k]))))
-        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
-        # invariants-end
-        result.msg_codes.append(self.msg_codes[a])
-        result.msg_values.append(self.msg_values[a])
+        Invariant(1 <= a and a <= len(self.msg_codes) + 1)
+        result.msg_codes.append(self.msg_codes[a - 1])
+        result.msg_values.append(self.msg_values[a - 1])
         a = a + 1
-
-    # result.validators = self.validators[:]  -- a fresh list holding the same
-    # validators in order (this collection was already copied before the fix).
     b = 0
     while b < len(self.validators):
-        # invariants-start
         Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(len(self.validators) == Old(len(self.validators)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
-                                                  self.validators[k] == Old(self.validators[k])))))
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
         Invariant(result.validators is not self.validators)
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(len(result.msg_codes) == len(self.msg_codes))
-        Invariant(len(result.msg_values) == len(self.msg_values))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  result.msg_values[k] == self.msg_values[k]))))
+        Invariant(len(self.validators) == Old(len(self.validators)))
         Invariant(0 <= b and b <= len(self.validators))
         Invariant(len(result.validators) == b)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
-                                                  result.validators[k] == self.validators[k]))))
-        Invariant(MustTerminate(len(self.validators) - b + 1))
-        # invariants-end
         result.validators.append(self.validators[b])
         b = b + 1
     return result
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -58,10 +57,6 @@
 
 class Field:
     def __init__(self) -> None:
-        # Terminates: no loops and no calls — exactly three attribute stores.
-        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
-        # strictly exceed its callee's) and above the list literals it builds.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
         Ensures(len(self.msg_codes) == 0)  # type: ignore
         Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
@@ -82,7 +77,6 @@
     Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
     # The two arrays carrying the override mapping are index-aligned.
     Requires(len(self.msg_codes) == len(self.msg_values))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The original field is left exactly as it was: same overrides, same
@@ -125,28 +119,17 @@
                                             Result().validators[k] == self.validators[k]))))
     # post-conditions-end
     # impl-start
+    # ATTACK (aliased validators): msg copied correctly but validators SHARED.
     result = Field()
-
-    # result.error_messages = self.error_messages.copy()  -- a fresh collection
-    # holding the same overrides as the original (the added line).
     a = 0
     while a < len(self.msg_codes):
-        # invariants-start
         Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
         Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
         Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
         Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
         Invariant(result.msg_codes is not self.msg_codes)
         Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
         Invariant(result.msg_values is not self.msg_values)
-        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(len(result.validators) == 0)
         Invariant(0 <= a and a <= len(self.msg_codes))
         Invariant(len(result.msg_codes) == a)
         Invariant(len(result.msg_values) == a)
@@ -154,49 +137,9 @@
                                                   result.msg_codes[k] == self.msg_codes[k]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                   result.msg_values[k] == self.msg_values[k]))))
-        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
-        # invariants-end
         result.msg_codes.append(self.msg_codes[a])
         result.msg_values.append(self.msg_values[a])
         a = a + 1
-
-    # result.validators = self.validators[:]  -- a fresh list holding the same
-    # validators in order (this collection was already copied before the fix).
-    b = 0
-    while b < len(self.validators):
-        # invariants-start
-        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(len(self.validators) == Old(len(self.validators)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
-                                                  self.validators[k] == Old(self.validators[k])))))
-        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(result.validators is not self.validators)
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(len(result.msg_codes) == len(self.msg_codes))
-        Invariant(len(result.msg_values) == len(self.msg_values))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  result.msg_values[k] == self.msg_values[k]))))
-        Invariant(0 <= b and b <= len(self.validators))
-        Invariant(len(result.validators) == b)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
-                                                  result.validators[k] == self.validators[k]))))
-        Invariant(MustTerminate(len(self.validators) - b + 1))
-        # invariants-end
-        result.validators.append(self.validators[b])
-        b = b + 1
+    result.validators = self.validators
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -58,10 +57,6 @@
 
 class Field:
     def __init__(self) -> None:
-        # Terminates: no loops and no calls — exactly three attribute stores.
-        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
-        # strictly exceed its callee's) and above the list literals it builds.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
         Ensures(len(self.msg_codes) == 0)  # type: ignore
         Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
@@ -82,7 +77,6 @@
     Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
     # The two arrays carrying the override mapping are index-aligned.
     Requires(len(self.msg_codes) == len(self.msg_values))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The original field is left exactly as it was: same overrides, same
@@ -125,28 +119,17 @@
                                             Result().validators[k] == self.validators[k]))))
     # post-conditions-end
     # impl-start
+    # ATTACK (dropped validators): copy msg correctly but never copy validators.
     result = Field()
-
-    # result.error_messages = self.error_messages.copy()  -- a fresh collection
-    # holding the same overrides as the original (the added line).
     a = 0
     while a < len(self.msg_codes):
-        # invariants-start
         Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
         Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
         Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
         Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
         Invariant(result.msg_codes is not self.msg_codes)
         Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
         Invariant(result.msg_values is not self.msg_values)
-        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(len(result.validators) == 0)
         Invariant(0 <= a and a <= len(self.msg_codes))
         Invariant(len(result.msg_codes) == a)
         Invariant(len(result.msg_values) == a)
@@ -154,49 +137,8 @@
                                                   result.msg_codes[k] == self.msg_codes[k]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                   result.msg_values[k] == self.msg_values[k]))))
-        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
-        # invariants-end
         result.msg_codes.append(self.msg_codes[a])
         result.msg_values.append(self.msg_values[a])
         a = a + 1
-
-    # result.validators = self.validators[:]  -- a fresh list holding the same
-    # validators in order (this collection was already copied before the fix).
-    b = 0
-    while b < len(self.validators):
-        # invariants-start
-        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(len(self.validators) == Old(len(self.validators)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
-                                                  self.validators[k] == Old(self.validators[k])))))
-        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(result.validators is not self.validators)
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(len(result.msg_codes) == len(self.msg_codes))
-        Invariant(len(result.msg_values) == len(self.msg_values))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  result.msg_values[k] == self.msg_values[k]))))
-        Invariant(0 <= b and b <= len(self.validators))
-        Invariant(len(result.validators) == b)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
-                                                  result.validators[k] == self.validators[k]))))
-        Invariant(MustTerminate(len(self.validators) - b + 1))
-        # invariants-end
-        result.validators.append(self.validators[b])
-        b = b + 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -58,10 +57,6 @@
 
 class Field:
     def __init__(self) -> None:
-        # Terminates: no loops and no calls — exactly three attribute stores.
-        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
-        # strictly exceed its callee's) and above the list literals it builds.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
         Ensures(len(self.msg_codes) == 0)  # type: ignore
         Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
@@ -82,7 +77,6 @@
     Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
     # The two arrays carrying the override mapping are index-aligned.
     Requires(len(self.msg_codes) == len(self.msg_values))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The original field is left exactly as it was: same overrides, same
@@ -125,77 +119,32 @@
                                             Result().validators[k] == self.validators[k]))))
     # post-conditions-end
     # impl-start
+    # ATTACK (swapped contents): result.msg_values filled from self.msg_codes.
     result = Field()
-
-    # result.error_messages = self.error_messages.copy()  -- a fresh collection
-    # holding the same overrides as the original (the added line).
     a = 0
     while a < len(self.msg_codes):
-        # invariants-start
         Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
         Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
         Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
         Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
         Invariant(result.msg_codes is not self.msg_codes)
         Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
         Invariant(result.msg_values is not self.msg_values)
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(len(result.validators) == 0)
         Invariant(0 <= a and a <= len(self.msg_codes))
         Invariant(len(result.msg_codes) == a)
         Invariant(len(result.msg_values) == a)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
-                                                  result.msg_values[k] == self.msg_values[k]))))
-        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
-        # invariants-end
         result.msg_codes.append(self.msg_codes[a])
-        result.msg_values.append(self.msg_values[a])
+        result.msg_values.append(self.msg_codes[a])
         a = a + 1
-
-    # result.validators = self.validators[:]  -- a fresh list holding the same
-    # validators in order (this collection was already copied before the fix).
     b = 0
     while b < len(self.validators):
-        # invariants-start
         Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(len(self.validators) == Old(len(self.validators)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
-                                                  self.validators[k] == Old(self.validators[k])))))
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
         Invariant(result.validators is not self.validators)
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(len(result.msg_codes) == len(self.msg_codes))
-        Invariant(len(result.msg_values) == len(self.msg_values))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  result.msg_values[k] == self.msg_values[k]))))
+        Invariant(len(self.validators) == Old(len(self.validators)))
         Invariant(0 <= b and b <= len(self.validators))
         Invariant(len(result.validators) == b)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
-                                                  result.validators[k] == self.validators[k]))))
-        Invariant(MustTerminate(len(self.validators) - b + 1))
-        # invariants-end
         result.validators.append(self.validators[b])
         b = b + 1
     return result
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -58,10 +57,6 @@
 
 class Field:
     def __init__(self) -> None:
-        # Terminates: no loops and no calls — exactly three attribute stores.
-        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
-        # strictly exceed its callee's) and above the list literals it builds.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
         Ensures(len(self.msg_codes) == 0)  # type: ignore
         Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
@@ -82,7 +77,6 @@
     Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
     # The two arrays carrying the override mapping are index-aligned.
     Requires(len(self.msg_codes) == len(self.msg_values))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The original field is left exactly as it was: same overrides, same
@@ -125,77 +119,34 @@
                                             Result().validators[k] == self.validators[k]))))
     # post-conditions-end
     # impl-start
+    # ATTACK (reverse order): copy msg entries in reverse index order.
     result = Field()
-
-    # result.error_messages = self.error_messages.copy()  -- a fresh collection
-    # holding the same overrides as the original (the added line).
     a = 0
-    while a < len(self.msg_codes):
-        # invariants-start
+    n = len(self.msg_codes)
+    while a < n:
         Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
         Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
         Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
+        Invariant(n == len(self.msg_codes))
         Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
         Invariant(result.msg_codes is not self.msg_codes)
         Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
         Invariant(result.msg_values is not self.msg_values)
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(len(result.validators) == 0)
-        Invariant(0 <= a and a <= len(self.msg_codes))
+        Invariant(0 <= a and a <= n)
         Invariant(len(result.msg_codes) == a)
         Invariant(len(result.msg_values) == a)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
-                                                  result.msg_values[k] == self.msg_values[k]))))
-        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
-        # invariants-end
-        result.msg_codes.append(self.msg_codes[a])
-        result.msg_values.append(self.msg_values[a])
+        result.msg_codes.append(self.msg_codes[n - 1 - a])
+        result.msg_values.append(self.msg_values[n - 1 - a])
         a = a + 1
-
-    # result.validators = self.validators[:]  -- a fresh list holding the same
-    # validators in order (this collection was already copied before the fix).
     b = 0
     while b < len(self.validators):
-        # invariants-start
         Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(len(self.validators) == Old(len(self.validators)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
-                                                  self.validators[k] == Old(self.validators[k])))))
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
         Invariant(result.validators is not self.validators)
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(len(result.msg_codes) == len(self.msg_codes))
-        Invariant(len(result.msg_values) == len(self.msg_values))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  result.msg_values[k] == self.msg_values[k]))))
+        Invariant(len(self.validators) == Old(len(self.validators)))
         Invariant(0 <= b and b <= len(self.validators))
         Invariant(len(result.validators) == b)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
-                                                  result.validators[k] == self.validators[k]))))
-        Invariant(MustTerminate(len(self.validators) - b + 1))
-        # invariants-end
         result.validators.append(self.validators[b])
         b = b + 1
     return result
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -58,10 +57,6 @@
 
 class Field:
     def __init__(self) -> None:
-        # Terminates: no loops and no calls — exactly three attribute stores.
-        # Level 2 leaves room BELOW deep_duplicate's level 6 (a caller's level must
-        # strictly exceed its callee's) and above the list literals it builds.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
         Ensures(len(self.msg_codes) == 0)  # type: ignore
         Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
@@ -82,7 +77,6 @@
     Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
     # The two arrays carrying the override mapping are index-aligned.
     Requires(len(self.msg_codes) == len(self.msg_values))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The original field is left exactly as it was: same overrides, same
@@ -125,28 +119,62 @@
                                             Result().validators[k] == self.validators[k]))))
     # post-conditions-end
     # impl-start
+    # ATTACK (echo, gold-equivalent restructured): copy validators FIRST then
+    # msg entries; identical observable result to gold. Legitimate echo.
     result = Field()
-
-    # result.error_messages = self.error_messages.copy()  -- a fresh collection
-    # holding the same overrides as the original (the added line).
-    a = 0
-    while a < len(self.msg_codes):
-        # invariants-start
+    b = 0
+    while b < len(self.validators):
+        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
         Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
         Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
         Invariant(len(self.msg_codes) == len(self.msg_values))
+        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
+        Invariant(result.validators is not self.validators)
+        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
+        Invariant(result.msg_codes is not self.msg_codes)
+        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
+        Invariant(result.msg_values is not self.msg_values)
+        Invariant(len(result.msg_codes) == 0)
+        Invariant(len(result.msg_values) == 0)
+        Invariant(len(self.validators) == Old(len(self.validators)))
         Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
         Invariant(len(self.msg_values) == Old(len(self.msg_values)))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                   self.msg_codes[k] == Old(self.msg_codes[k])))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                   self.msg_values[k] == Old(self.msg_values[k])))))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
+                                                  self.validators[k] == Old(self.validators[k])))))
+        Invariant(0 <= b and b <= len(self.validators))
+        Invariant(len(result.validators) == b)
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
+                                                  result.validators[k] == self.validators[k]))))
+        result.validators.append(self.validators[b])
+        b = b + 1
+    a = 0
+    while a < len(self.msg_codes):
+        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
+        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
+        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
+        Invariant(len(self.msg_codes) == len(self.msg_values))
         Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
         Invariant(result.msg_codes is not self.msg_codes)
         Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
         Invariant(result.msg_values is not self.msg_values)
         Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(len(result.validators) == 0)
+        Invariant(result.validators is not self.validators)
+        Invariant(len(result.validators) == len(self.validators))
+        Invariant(len(self.validators) == Old(len(self.validators)))
+        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
+        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
+                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
+                                                  self.msg_values[k] == Old(self.msg_values[k])))))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
+                                                  self.validators[k] == Old(self.validators[k])))))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
+                                                  result.validators[k] == self.validators[k]))))
         Invariant(0 <= a and a <= len(self.msg_codes))
         Invariant(len(result.msg_codes) == a)
         Invariant(len(result.msg_values) == a)
@@ -154,49 +182,8 @@
                                                   result.msg_codes[k] == self.msg_codes[k]))))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                   result.msg_values[k] == self.msg_values[k]))))
-        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
-        # invariants-end
         result.msg_codes.append(self.msg_codes[a])
         result.msg_values.append(self.msg_values[a])
         a = a + 1
-
-    # result.validators = self.validators[:]  -- a fresh list holding the same
-    # validators in order (this collection was already copied before the fix).
-    b = 0
-    while b < len(self.validators):
-        # invariants-start
-        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
-        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
-        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
-        Invariant(len(self.msg_codes) == len(self.msg_values))
-        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
-        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
-        Invariant(len(self.validators) == Old(len(self.validators)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  self.msg_values[k] == Old(self.msg_values[k])))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
-                                                  self.validators[k] == Old(self.validators[k])))))
-        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
-        Invariant(result.validators is not self.validators)
-        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
-        Invariant(result.msg_codes is not self.msg_codes)
-        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
-        Invariant(result.msg_values is not self.msg_values)
-        Invariant(len(result.msg_codes) == len(self.msg_codes))
-        Invariant(len(result.msg_values) == len(self.msg_values))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
-                                                  result.msg_codes[k] == self.msg_codes[k]))))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
-                                                  result.msg_values[k] == self.msg_values[k]))))
-        Invariant(0 <= b and b <= len(self.validators))
-        Invariant(len(result.validators) == b)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
-                                                  result.validators[k] == self.validators[k]))))
-        Invariant(MustTerminate(len(self.validators) - b + 1))
-        # invariants-end
-        result.validators.append(self.validators[b])
-        b = b + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11880.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Producing an independent duplicate of a form field must yield a field that is
  observably *sealed away* from the original: replacing or mutating one of the
  duplicate's mutable per-field collections must never be reflected on the
  original, and vice versa. Two such collections matter here.

  For EACH such collection the duplicate must carry a SEPARATE container object
  whose contents equal the original's at the moment of duplication:

    (1) the validator collection of the duplicate is a distinct list object
        holding the same validators, in order, as the original (this collection
        was already independent before this change), and

    (2) the per-field message overrides of the duplicate are likewise a
        distinct collection object holding the same overrides as the original.
        Because the collection is a distinct object, replacing or mutating one
        field's overrides leaves every other field's overrides untouched.

  The original field is read-only throughout duplication: its own collections
  are left exactly as they were, with the same contents.

A field is modelled as a minimal object exposing only the two touched mutable
collections. The per-field message overrides are a mapping from an override
code to an override value; the tested behaviour observes only (a) WHICH codes
are present and (b) the value bound to each, and crucially that the duplicate's
mapping is a SEPARATE object from the original's. So the mapping is carried by
two index-aligned `List[int]` — `msg_codes[k]` bound to `msg_values[k]` — and
the validators by a `List[int]` of validator identities. Object distinctness
("the duplicate owns its own collection") is carried by Nagini's separation:
the duplicate holds full permission to its own collections while the original
retains permission to its own, provable only when the two are distinct objects
(`is not`). No callee is axiomatized: the duplication is pure object/structure
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the duplication is pure object/structure logic, modelled
# deeply (a distinct collection object with equal contents). The shallow-copy
# primitive the duplication builds on is validated against its real Python
# semantics out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Field:
    def __init__(self) -> None:
        Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
        Ensures(len(self.msg_codes) == 0)  # type: ignore
        Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
        Ensures(len(self.msg_values) == 0)  # type: ignore
        Ensures(Acc(self.validators) and Acc(list_pred(self.validators)))  # type: ignore
        Ensures(len(self.validators) == 0)  # type: ignore
        self.msg_codes = []  # type: List[int]
        self.msg_values = []  # type: List[int]
        self.validators = []  # type: List[int]


def deep_duplicate(self: Field) -> Field:
    # pre-conditions-start
    # The original field is read-only: its collections are required (and
    # ensured) only at fractional permission.
    Requires(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
    Requires(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
    Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
    # The two arrays carrying the override mapping are index-aligned.
    Requires(len(self.msg_codes) == len(self.msg_values))
    # pre-conditions-end
    # post-conditions-start
    # The original field is left exactly as it was: same overrides, same
    # validators, untouched (returned at the same fractional permission).
    Ensures(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
    Ensures(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
    Ensures(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
    Ensures(len(self.msg_codes) == Old(len(self.msg_codes)))
    Ensures(len(self.msg_values) == Old(len(self.msg_values)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                            self.msg_codes[k] == Old(self.msg_codes[k])))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                            self.msg_values[k] == Old(self.msg_values[k])))))
    Ensures(len(self.validators) == Old(len(self.validators)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                            self.validators[k] == Old(self.validators[k])))))

    # The duplicate is a fully-owned object whose mutable collections are
    # DISTINCT container objects from the original's. The `is not` clauses are
    # the discriminating guarantee: a duplicate that shared either collection
    # with the original (so that mutating one reached the other) is rejected.
    Ensures(Acc(Result().msg_codes) and Acc(list_pred(Result().msg_codes)))
    Ensures(Acc(Result().msg_values) and Acc(list_pred(Result().msg_values)))
    Ensures(Result().msg_codes is not self.msg_codes)
    Ensures(Result().msg_values is not self.msg_values)
    Ensures(Acc(Result().validators) and Acc(list_pred(Result().validators)))
    Ensures(Result().validators is not self.validators)

    # The distinct collections hold the same contents as the original's at the
    # moment of duplication: the same override codes bound to the same values ...
    Ensures(len(Result().msg_codes) == len(self.msg_codes))
    Ensures(len(Result().msg_values) == len(self.msg_values))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                            Result().msg_codes[k] == self.msg_codes[k]))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                            Result().msg_values[k] == self.msg_values[k]))))
    # ... and the same validators in the same order.
    Ensures(len(Result().validators) == len(self.validators))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                            Result().validators[k] == self.validators[k]))))
    # post-conditions-end
    # impl-start
    result = Field()

    # result.error_messages = self.error_messages.copy()  -- a fresh collection
    # holding the same overrides as the original (the added line).
    a = 0
    while a < len(self.msg_codes):
        # invariants-start
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(len(result.validators) == 0)
        Invariant(0 <= a and a <= len(self.msg_codes))
        Invariant(len(result.msg_codes) == a)
        Invariant(len(result.msg_values) == a)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_values[k] == self.msg_values[k]))))
        # invariants-end
        result.msg_codes.append(self.msg_codes[a])
        result.msg_values.append(self.msg_values[a])
        a = a + 1

    # result.validators = self.validators[:]  -- a fresh list holding the same
    # validators in order (this collection was already copied before the fix).
    b = 0
    while b < len(self.validators):
        # invariants-start
        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(len(self.validators) == Old(len(self.validators)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  self.validators[k] == Old(self.validators[k])))))
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(len(result.msg_codes) == len(self.msg_codes))
        Invariant(len(result.msg_values) == len(self.msg_values))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  result.msg_values[k] == self.msg_values[k]))))
        Invariant(0 <= b and b <= len(self.validators))
        Invariant(len(result.validators) == b)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
                                                  result.validators[k] == self.validators[k]))))
        # invariants-end
        result.validators.append(self.validators[b])
        b = b + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec is a COMPLETE functional specification of Field.__deepcopy__'s per-field-collection behaviour: for BOTH the message-override collection (msg_codes/msg_values) and the validators collection it requires (a) the result carries a DISTINCT object (`Result().x is not self.x`, forced by Nagini separation of full Acc(list_pred(Result().x)) against the original's retained 1/2 permission), (b) exact length equality, (c) exact per-index content equality, and (d) the original left untouched (Old-preservation on all three lists).

SBU_BENCHMARK_DIR=benchmark-verified. Commands run from project root. Verifications scheduled concurrently in 3 background batches (<=3 JVMs each).

POSITIVE CONTROL: `adversary verify nagini django__django-11880 positive_control.py` -> VERIFIED (31.8s). positive_control.py is a byte-identical copy of model.py.

PREPATCH BUG REPRODUCED (atk_1): aliases result.msg_codes/msg_values to self's (the shallow-copy bug, matches model_prepatch.py). `adversary weakness ... atk_1.py` -> NOT-A-COUNTEREXAMPLE: does not verify (exit 2). Spec sees the bug via Acc(list_pred(Result().msg_codes)) full-permission + `is not` clause.

### ATTACK BATTERY (all confirmed same-spec byte-identical; only impl region edited):
- atk_1 prepatch-alias (control-flow-effect: shared msg objects) -> FAILED verify (exit 2).
- atk_2 partial-domain (msg copy loop runs a<len-1, drops last entry) -> FAILED verify (exit 2). Rejected by len(Result().msg_codes)==len(self.msg_codes).
- atk_3 boundary off-by-one (msg copy starts at index 1) -> FAILED verify (exit 2). Rejected by per-index content equality / length.
- atk_4 aliased-validators (result.validators = self.validators) -> FAILED verify (exit 2). Rejected by Result().validators is not self.validators + full permission.
- atk_5 dropped-validators (never copy validators; result.validators empty) -> FAILED verify (exit 2). Rejected by len(Result().validators)==len(self.validators).
- atk_6 swapped/ungrounded contents (result.msg_values filled from self.msg_codes) -> FAILED verify (exit 2). Rejected by per-index msg_values content equality.
- atk_7 reverse-order msg copy -> FAILED verify (exit 2). Rejected by per-index content equality.
- atk_8 ECHO (gold-equivalent, restructured: copies validators FIRST then messages, both into fresh distinct objects) -> CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (58.7s, exit 0).

MANDATORY RESOLVE STEP for the one CANDIDATE (atk_8): materialized its faithful refined patch (patch_atk_8.diff = the gold `result.error_messages = self.error_messages.copy()` line, placed after the existing `result.validators = self.validators[:]` line, mirroring the impl's loop reordering). Ran `swebench_unified.harness.run_resolve('django__django-11880', patch, timeout=1800)` -> RESOLVED: True, COMPLETED: True, note 'resolved', 1 attempt, not flaky. Gold-patch baseline also run: RESOLVED True. Per the resolved-echo policy (the audit protocol: a same-spec verifying attack whose refined patch RESOLVES is NOT a weakness), atk_8 does not break the spec — it is a faithful behavioural equivalent of the gold that correctly resolves.

REFINEMENT.MD AUDIT (A-leg / correspondence focus): 5 legs A1..A5. A1 (Field<->minimal object) R; A2 (Field()+loops <-> copy.copy+per-collection rebinds) R, unmodelled shallow-shared scalars carry no tested behaviour of this change; A3 (msg copy loop <-> error_messages.copy()) I-under-R = the FIX; A4 (validators loop <-> validators[:]) I-under-R; A5 (return result) I. NO A-consumed axioms (no @ContractOnly in the model; axioms region empty). The only callee semantics relied on are TWO A-REFERENCES: CPython dict.copy() and list[:] (distinct object, equal contents). Their correspondence to the real callees holds and is validated by axiom_check.py (G-AX), which (a) checks the primitives directly over 5000 randomized observations and (b) executes the REAL post-patch Django Field.__deepcopy__ over the exact F2P scenario (CharField subclass setting error_messages) + 200 fuzz fields, asserting distinct-object + equal-contents + original-untouched + mutation-isolation. No kind-3 (unexpressible-changed-op) legs. Correspondence is faithful.

CONCLUSION: >=5 distinct wrong impls (7 non-echo) were all REJECTED by the spec; the single verifying impl is a faithful gold-equivalent echo whose materialized refined patch RESOLVES under the official harness. No verifying wrong impl exists whose faithful patch fails to resolve. Refinement legs are all R/I/A-reference with sound correspondence; no consumed axioms. verify => correct holds for this bundle. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11880.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Producing an independent duplicate of a form field must yield a field that is
  observably *sealed away* from the original: replacing or mutating one of the
  duplicate's mutable per-field collections must never be reflected on the
  original, and vice versa. Two such collections matter here.

  For EACH such collection the duplicate must carry a SEPARATE container object
  whose contents equal the original's at the moment of duplication:

    (1) the validator collection of the duplicate is a distinct list object
        holding the same validators, in order, as the original (this collection
        was already independent before this change), and

    (2) the per-field message overrides of the duplicate are likewise a
        distinct collection object holding the same overrides as the original.
        Because the collection is a distinct object, replacing or mutating one
        field's overrides leaves every other field's overrides untouched.

  The original field is read-only throughout duplication: its own collections
  are left exactly as they were, with the same contents.

A field is modelled as a minimal object exposing only the two touched mutable
collections. The per-field message overrides are a mapping from an override
code to an override value; the tested behaviour observes only (a) WHICH codes
are present and (b) the value bound to each, and crucially that the duplicate's
mapping is a SEPARATE object from the original's. So the mapping is carried by
two index-aligned `List[int]` — `msg_codes[k]` bound to `msg_values[k]` — and
the validators by a `List[int]` of validator identities. Object distinctness
("the duplicate owns its own collection") is carried by Nagini's separation:
the duplicate holds full permission to its own collections while the original
retains permission to its own, provable only when the two are distinct objects
(`is not`). No callee is axiomatized: the duplication is pure object/structure
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the duplication is pure object/structure logic, modelled
# deeply (a distinct collection object with equal contents). The shallow-copy
# primitive the duplication builds on is validated against its real Python
# semantics out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Field:
    def __init__(self) -> None:
        Ensures(Acc(self.msg_codes) and Acc(list_pred(self.msg_codes)))  # type: ignore
        Ensures(len(self.msg_codes) == 0)  # type: ignore
        Ensures(Acc(self.msg_values) and Acc(list_pred(self.msg_values)))  # type: ignore
        Ensures(len(self.msg_values) == 0)  # type: ignore
        Ensures(Acc(self.validators) and Acc(list_pred(self.validators)))  # type: ignore
        Ensures(len(self.validators) == 0)  # type: ignore
        self.msg_codes = []  # type: List[int]
        self.msg_values = []  # type: List[int]
        self.validators = []  # type: List[int]


def deep_duplicate(self: Field) -> Field:
    # pre-conditions-start
    # The original field is read-only: its collections are required (and
    # ensured) only at fractional permission.
    Requires(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
    Requires(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
    Requires(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
    # The two arrays carrying the override mapping are index-aligned.
    Requires(len(self.msg_codes) == len(self.msg_values))
    # pre-conditions-end
    # post-conditions-start
    # The original field is left exactly as it was: same overrides, same
    # validators, untouched (returned at the same fractional permission).
    Ensures(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
    Ensures(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
    Ensures(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
    Ensures(len(self.msg_codes) == Old(len(self.msg_codes)))
    Ensures(len(self.msg_values) == Old(len(self.msg_values)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                            self.msg_codes[k] == Old(self.msg_codes[k])))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                            self.msg_values[k] == Old(self.msg_values[k])))))
    Ensures(len(self.validators) == Old(len(self.validators)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                            self.validators[k] == Old(self.validators[k])))))

    # The duplicate is a fully-owned object whose mutable collections are
    # DISTINCT container objects from the original's. The `is not` clauses are
    # the discriminating guarantee: a duplicate that shared either collection
    # with the original (so that mutating one reached the other) is rejected.
    Ensures(Acc(Result().msg_codes) and Acc(list_pred(Result().msg_codes)))
    Ensures(Acc(Result().msg_values) and Acc(list_pred(Result().msg_values)))
    Ensures(Result().msg_codes is not self.msg_codes)
    Ensures(Result().msg_values is not self.msg_values)
    Ensures(Acc(Result().validators) and Acc(list_pred(Result().validators)))
    Ensures(Result().validators is not self.validators)

    # The distinct collections hold the same contents as the original's at the
    # moment of duplication: the same override codes bound to the same values ...
    Ensures(len(Result().msg_codes) == len(self.msg_codes))
    Ensures(len(Result().msg_values) == len(self.msg_values))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                            Result().msg_codes[k] == self.msg_codes[k]))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                            Result().msg_values[k] == self.msg_values[k]))))
    # ... and the same validators in the same order.
    Ensures(len(Result().validators) == len(self.validators))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                            Result().validators[k] == self.validators[k]))))
    # post-conditions-end
    # impl-start
    result = Field()

    # result.error_messages = self.error_messages.copy()  -- a fresh collection
    # holding the same overrides as the original (the added line).
    a = 0
    while a < len(self.msg_codes):
        # invariants-start
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(len(result.validators) == 0)
        Invariant(0 <= a and a <= len(self.msg_codes))
        Invariant(len(result.msg_codes) == a)
        Invariant(len(result.msg_values) == a)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_values[k] == self.msg_values[k]))))
        # invariants-end
        result.msg_codes.append(self.msg_codes[a])
        result.msg_values.append(self.msg_values[a])
        a = a + 1

    # result.validators = self.validators[:]  -- a fresh list holding the same
    # validators in order (this collection was already copied before the fix).
    b = 0
    while b < len(self.validators):
        # invariants-start
        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(len(self.validators) == Old(len(self.validators)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  self.validators[k] == Old(self.validators[k])))))
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(len(result.msg_codes) == len(self.msg_codes))
        Invariant(len(result.msg_values) == len(self.msg_values))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  result.msg_values[k] == self.msg_values[k]))))
        Invariant(0 <= b and b <= len(self.validators))
        Invariant(len(result.validators) == b)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
                                                  result.validators[k] == self.validators[k]))))
        # invariants-end
        result.validators.append(self.validators[b])
        b = b + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec is a COMPLETE functional specification of Field.__deepcopy__'s per-field-collection behaviour: for BOTH the message-override collection (msg_codes/msg_values) and the validators collection it requires (a) the result carries a DISTINCT object (`Result().x is not self.x`, forced by Nagini separation of full Acc(list_pred(Result().x)) against the original's retained 1/2 permission), (b) exact length equality, (c) exact per-index content equality, and (d) the original left untouched (Old-preservation on all three lists).

SBU_BENCHMARK_DIR=benchmark-verified. Commands run from project root. Verifications scheduled concurrently in 3 background batches (<=3 JVMs each).

POSITIVE CONTROL: `adversary verify nagini django__django-11880 positive_control.py` -> VERIFIED (31.8s). positive_control.py is a byte-identical copy of model.py.

PREPATCH BUG REPRODUCED (atk_1): aliases result.msg_codes/msg_values to self's (the shallow-copy bug, matches model_prepatch.py). `adversary weakness ... atk_1.py` -> NOT-A-COUNTEREXAMPLE: does not verify (exit 2). Spec sees the bug via Acc(list_pred(Result().msg_codes)) full-permission + `is not` clause.

### ATTACK BATTERY (all confirmed same-spec byte-identical; only impl region edited):
- atk_1 prepatch-alias (control-flow-effect: shared msg objects) -> FAILED verify (exit 2).
- atk_2 partial-domain (msg copy loop runs a<len-1, drops last entry) -> FAILED verify (exit 2). Rejected by len(Result().msg_codes)==len(self.msg_codes).
- atk_3 boundary off-by-one (msg copy starts at index 1) -> FAILED verify (exit 2). Rejected by per-index content equality / length.
- atk_4 aliased-validators (result.validators = self.validators) -> FAILED verify (exit 2). Rejected by Result().validators is not self.validators + full permission.
- atk_5 dropped-validators (never copy validators; result.validators empty) -> FAILED verify (exit 2). Rejected by len(Result().validators)==len(self.validators).
- atk_6 swapped/ungrounded contents (result.msg_values filled from self.msg_codes) -> FAILED verify (exit 2). Rejected by per-index msg_values content equality.
- atk_7 reverse-order msg copy -> FAILED verify (exit 2). Rejected by per-index content equality.
- atk_8 ECHO (gold-equivalent, restructured: copies validators FIRST then messages, both into fresh distinct objects) -> CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (58.7s, exit 0).

MANDATORY RESOLVE STEP for the one CANDIDATE (atk_8): materialized its faithful refined patch (patch_atk_8.diff = the gold `result.error_messages = self.error_messages.copy()` line, placed after the existing `result.validators = self.validators[:]` line, mirroring the impl's loop reordering). Ran `swebench_unified.harness.run_resolve('django__django-11880', patch, timeout=1800)` -> RESOLVED: True, COMPLETED: True, note 'resolved', 1 attempt, not flaky. Gold-patch baseline also run: RESOLVED True. Per the resolved-echo policy (the audit protocol: a same-spec verifying attack whose refined patch RESOLVES is NOT a weakness), atk_8 does not break the spec — it is a faithful behavioural equivalent of the gold that correctly resolves.

REFINEMENT.MD AUDIT (A-leg / correspondence focus): 5 legs A1..A5. A1 (Field<->minimal object) R; A2 (Field()+loops <-> copy.copy+per-collection rebinds) R, unmodelled shallow-shared scalars carry no tested behaviour of this change; A3 (msg copy loop <-> error_messages.copy()) I-under-R = the FIX; A4 (validators loop <-> validators[:]) I-under-R; A5 (return result) I. NO A-consumed axioms (no @ContractOnly in the model; axioms region empty). The only callee semantics relied on are TWO A-REFERENCES: CPython dict.copy() and list[:] (distinct object, equal contents). Their correspondence to the real callees holds and is validated by axiom_check.py (G-AX), which (a) checks the primitives directly over 5000 randomized observations and (b) executes the REAL post-patch Django Field.__deepcopy__ over the exact F2P scenario (CharField subclass setting error_messages) + 200 fuzz fields, asserting distinct-object + equal-contents + original-untouched + mutation-isolation. No kind-3 (unexpressible-changed-op) legs. Correspondence is faithful.

CONCLUSION: >=5 distinct wrong impls (7 non-echo) were all REJECTED by the spec; the single verifying impl is a faithful gold-equivalent echo whose materialized refined patch RESOLVES under the official harness. No verifying wrong impl exists whose faithful patch fails to resolve. Refinement legs are all R/I/A-reference with sound correspondence; no consumed axioms. verify => correct holds for this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11880 nagini bundle. Findings:

1. model.py VERIFIES under the pinned Nagini verifier (exit 0, ~24s).

2. The spec models Field.__deepcopy__ (django/forms/fields.py:198-203): the duplicate must own DISTINCT error_messages (modeled as index-aligned msg_codes/msg_values List[int]) and validators collections holding the same contents as the original, with the original left untouched (read-only, half-permission).

3. Real-callee agreement confirmed by executing the bundle's axiom_check.py against the REAL post-patch Django (which contains `result.error_messages = self.error_messages.copy()`): 'G-AX OK ... over 209 observations' — every duplicate has error_messages/validators that are distinct objects with equal contents and the original untouched. This includes the exact F2P scenario (CharField subclass overriding error_messages in __init__), boundary cases (no overrides), and 200 fuzz fields. These outcomes exactly match every spec postcondition (Result().msg_* is not self.msg_*, per-index content equality, len equality, untouched original).

4. Discriminating / not-too-strong: run against PRE-patch Django (— no error_messages.copy() line) the identical check fails on the FIRST observation: 'AssertionError: deepcopy shared the error_messages dict (the bug)'. So the spec captures exactly the fixed behavior, not more.

5. The `is not` distinctness postcondition holds for real Python even in the empty-collection boundary ({}.copy() is not {} == True; [][:] is not [] == True), so no empty-input divergence.

No input was found on which the modeled deep_duplicate disagrees with the real Field.__deepcopy__. Spec is FAITHFUL to real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures): no diff markers, no gold-patch line reproduced (>=8 char normalized), no patched file path 'django/forms/fields.py' or dotted module, no spec-view identifier or comment naming the patched repo symbol (real symbol 'error_messages'/'__deepcopy__' never appears; the model uses abstract carriers 'msg_codes'/'msg_values'/'validators' and 'deep_duplicate'), and no bug/fix narration keywords.

Semantic judgment (does the spec view leak the gold edit beyond the PUBLIC problem_statement, not hints_text): NO. The public problem_statement already states the entire bug and intended fix — it links __deepcopy__ at fields.py:200, says it 'performs a shallow copy of self and does not include additional treatment for the error_messages dictionary', that 'all copies of the same field share the same dictionary', and that each form instance's fields are expected to be "sealed" away. The spec view merely restates this same desired behavior in abstract terms: the duplicate must carry a SEPARATE container object for the per-field message overrides (and, unchanged, for validators) whose contents equal the original's, using the public word 'sealed away'. 

Crucially, the gold edit itself (result.error_messages = self.error_messages.copy()) lives only in the impl region, which is ELIDED in the spec view (`...  # implementation elided — supplied by the consumer`); the edit-revealing impl comments in model.py are NOT part of the consumer-visible spec view. The two-collection model (validators + message overrides) reflects the surrounding unchanged context (validators already copied) plus the public target collection, not privileged knowledge of which line was added. No line, path, symbol, or edit narration in the spec view reveals the gold beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
