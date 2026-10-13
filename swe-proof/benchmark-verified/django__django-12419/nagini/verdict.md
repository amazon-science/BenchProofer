# P2 adversarial audit — django__django-12419

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -44,10 +43,6 @@
 
     def __init__(self, present: bool, value: List[int]) -> None:
         Requires(Acc(list_pred(value), 1 / 2))
-        # Terminates: field initialisation is straight-line work; measure 1
-        # lets any caller holding MustTerminate(2) construct a slot without
-        # leaking its own obligation.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.present) and self.present == present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
@@ -105,7 +100,6 @@
     # The response header slot is the genuinely-mutated object (full perm).
     Requires(Acc(slot.present) and Acc(slot.value))
     Requires(Acc(list_pred(slot.value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present) and Acc(slot.value))
@@ -125,31 +119,18 @@
                     ToSeq(slot.value) == baseline_policy()))
     # post-conditions-end
     # impl-start
-    # The configured referrer policy supplied by the shipped baseline.
-    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
-    Assert(ToSeq(policy) == baseline_policy())
+    policy = []  # type: List[int]
     if len(policy) > 0:
         if not slot.present:
-            # Build the normalized value: trim each comma-separated token,
-            # rejoin by commas. For the baseline (no comma, no whitespace) this
-            # copies the token verbatim.
             value = []  # type: List[int]
             i = 0
             while i < len(policy):
-                # invariants-start
                 Invariant(Acc(list_pred(policy)))
                 Invariant(Acc(list_pred(value)))
                 Invariant(0 <= i and i <= len(policy))
                 Invariant(ToSeq(value) == ToSeq(policy).take(i))
-                Invariant(ToSeq(policy) == baseline_policy())
-                Invariant(MustTerminate(len(policy) - i + 1))
-                # invariants-end
-                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
-                       ToSeq(policy).take(i + 1))
                 value = value + [policy[i]]
                 i = i + 1
-            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
-            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
             slot.present = True
             slot.value = value
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -44,10 +43,6 @@
 
     def __init__(self, present: bool, value: List[int]) -> None:
         Requires(Acc(list_pred(value), 1 / 2))
-        # Terminates: field initialisation is straight-line work; measure 1
-        # lets any caller holding MustTerminate(2) construct a slot without
-        # leaking its own obligation.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.present) and self.present == present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
@@ -105,7 +100,6 @@
     # The response header slot is the genuinely-mutated object (full perm).
     Requires(Acc(slot.present) and Acc(slot.value))
     Requires(Acc(list_pred(slot.value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present) and Acc(slot.value))
@@ -125,31 +119,8 @@
                     ToSeq(slot.value) == baseline_policy()))
     # post-conditions-end
     # impl-start
-    # The configured referrer policy supplied by the shipped baseline.
     policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
-    Assert(ToSeq(policy) == baseline_policy())
     if len(policy) > 0:
-        if not slot.present:
-            # Build the normalized value: trim each comma-separated token,
-            # rejoin by commas. For the baseline (no comma, no whitespace) this
-            # copies the token verbatim.
-            value = []  # type: List[int]
-            i = 0
-            while i < len(policy):
-                # invariants-start
-                Invariant(Acc(list_pred(policy)))
-                Invariant(Acc(list_pred(value)))
-                Invariant(0 <= i and i <= len(policy))
-                Invariant(ToSeq(value) == ToSeq(policy).take(i))
-                Invariant(ToSeq(policy) == baseline_policy())
-                Invariant(MustTerminate(len(policy) - i + 1))
-                # invariants-end
-                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
-                       ToSeq(policy).take(i + 1))
-                value = value + [policy[i]]
-                i = i + 1
-            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
-            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
-            slot.present = True
-            slot.value = value
+        slot.present = True
+        slot.value = policy
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -44,10 +43,6 @@
 
     def __init__(self, present: bool, value: List[int]) -> None:
         Requires(Acc(list_pred(value), 1 / 2))
-        # Terminates: field initialisation is straight-line work; measure 1
-        # lets any caller holding MustTerminate(2) construct a slot without
-        # leaking its own obligation.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.present) and self.present == present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
@@ -105,7 +100,6 @@
     # The response header slot is the genuinely-mutated object (full perm).
     Requires(Acc(slot.present) and Acc(slot.value))
     Requires(Acc(list_pred(slot.value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present) and Acc(slot.value))
@@ -125,31 +119,18 @@
                     ToSeq(slot.value) == baseline_policy()))
     # post-conditions-end
     # impl-start
-    # The configured referrer policy supplied by the shipped baseline.
     policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
-    Assert(ToSeq(policy) == baseline_policy())
     if len(policy) > 0:
         if not slot.present:
-            # Build the normalized value: trim each comma-separated token,
-            # rejoin by commas. For the baseline (no comma, no whitespace) this
-            # copies the token verbatim.
             value = []  # type: List[int]
             i = 0
-            while i < len(policy):
-                # invariants-start
+            while i < len(policy) - 1:
                 Invariant(Acc(list_pred(policy)))
                 Invariant(Acc(list_pred(value)))
                 Invariant(0 <= i and i <= len(policy))
                 Invariant(ToSeq(value) == ToSeq(policy).take(i))
-                Invariant(ToSeq(policy) == baseline_policy())
-                Invariant(MustTerminate(len(policy) - i + 1))
-                # invariants-end
-                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
-                       ToSeq(policy).take(i + 1))
                 value = value + [policy[i]]
                 i = i + 1
-            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
-            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
             slot.present = True
             slot.value = value
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -44,10 +43,6 @@
 
     def __init__(self, present: bool, value: List[int]) -> None:
         Requires(Acc(list_pred(value), 1 / 2))
-        # Terminates: field initialisation is straight-line work; measure 1
-        # lets any caller holding MustTerminate(2) construct a slot without
-        # leaking its own obligation.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.present) and self.present == present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
@@ -105,7 +100,6 @@
     # The response header slot is the genuinely-mutated object (full perm).
     Requires(Acc(slot.present) and Acc(slot.value))
     Requires(Acc(list_pred(slot.value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present) and Acc(slot.value))
@@ -125,31 +119,7 @@
                     ToSeq(slot.value) == baseline_policy()))
     # post-conditions-end
     # impl-start
-    # The configured referrer policy supplied by the shipped baseline.
-    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
-    Assert(ToSeq(policy) == baseline_policy())
-    if len(policy) > 0:
-        if not slot.present:
-            # Build the normalized value: trim each comma-separated token,
-            # rejoin by commas. For the baseline (no comma, no whitespace) this
-            # copies the token verbatim.
-            value = []  # type: List[int]
-            i = 0
-            while i < len(policy):
-                # invariants-start
-                Invariant(Acc(list_pred(policy)))
-                Invariant(Acc(list_pred(value)))
-                Invariant(0 <= i and i <= len(policy))
-                Invariant(ToSeq(value) == ToSeq(policy).take(i))
-                Invariant(ToSeq(policy) == baseline_policy())
-                Invariant(MustTerminate(len(policy) - i + 1))
-                # invariants-end
-                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
-                       ToSeq(policy).take(i + 1))
-                value = value + [policy[i]]
-                i = i + 1
-            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
-            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
-            slot.present = True
-            slot.value = value
+    if not slot.present:
+        slot.present = True
+        slot.value = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -44,10 +43,6 @@
 
     def __init__(self, present: bool, value: List[int]) -> None:
         Requires(Acc(list_pred(value), 1 / 2))
-        # Terminates: field initialisation is straight-line work; measure 1
-        # lets any caller holding MustTerminate(2) construct a slot without
-        # leaking its own obligation.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.present) and self.present == present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
@@ -105,7 +100,6 @@
     # The response header slot is the genuinely-mutated object (full perm).
     Requires(Acc(slot.present) and Acc(slot.value))
     Requires(Acc(list_pred(slot.value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present) and Acc(slot.value))
@@ -125,31 +119,9 @@
                     ToSeq(slot.value) == baseline_policy()))
     # post-conditions-end
     # impl-start
-    # The configured referrer policy supplied by the shipped baseline.
-    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
-    Assert(ToSeq(policy) == baseline_policy())
+    policy = [120]  # type: List[int]   # a different configured token
     if len(policy) > 0:
         if not slot.present:
-            # Build the normalized value: trim each comma-separated token,
-            # rejoin by commas. For the baseline (no comma, no whitespace) this
-            # copies the token verbatim.
-            value = []  # type: List[int]
-            i = 0
-            while i < len(policy):
-                # invariants-start
-                Invariant(Acc(list_pred(policy)))
-                Invariant(Acc(list_pred(value)))
-                Invariant(0 <= i and i <= len(policy))
-                Invariant(ToSeq(value) == ToSeq(policy).take(i))
-                Invariant(ToSeq(policy) == baseline_policy())
-                Invariant(MustTerminate(len(policy) - i + 1))
-                # invariants-end
-                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
-                       ToSeq(policy).take(i + 1))
-                value = value + [policy[i]]
-                i = i + 1
-            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
-            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
             slot.present = True
-            slot.value = value
+            slot.value = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -44,10 +43,6 @@
 
     def __init__(self, present: bool, value: List[int]) -> None:
         Requires(Acc(list_pred(value), 1 / 2))
-        # Terminates: field initialisation is straight-line work; measure 1
-        # lets any caller holding MustTerminate(2) construct a slot without
-        # leaking its own obligation.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.present) and self.present == present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
@@ -105,7 +100,6 @@
     # The response header slot is the genuinely-mutated object (full perm).
     Requires(Acc(slot.present) and Acc(slot.value))
     Requires(Acc(list_pred(slot.value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present) and Acc(slot.value))
@@ -125,31 +119,10 @@
                     ToSeq(slot.value) == baseline_policy()))
     # post-conditions-end
     # impl-start
-    # The configured referrer policy supplied by the shipped baseline.
     policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
-    Assert(ToSeq(policy) == baseline_policy())
-    if len(policy) > 0:
-        if not slot.present:
-            # Build the normalized value: trim each comma-separated token,
-            # rejoin by commas. For the baseline (no comma, no whitespace) this
-            # copies the token verbatim.
-            value = []  # type: List[int]
-            i = 0
-            while i < len(policy):
-                # invariants-start
-                Invariant(Acc(list_pred(policy)))
-                Invariant(Acc(list_pred(value)))
-                Invariant(0 <= i and i <= len(policy))
-                Invariant(ToSeq(value) == ToSeq(policy).take(i))
-                Invariant(ToSeq(policy) == baseline_policy())
-                Invariant(MustTerminate(len(policy) - i + 1))
-                # invariants-end
-                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
-                       ToSeq(policy).take(i + 1))
-                value = value + [policy[i]]
-                i = i + 1
-            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
-            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
-            slot.present = True
-            slot.value = value
+    if not slot.present:
+        slot.present = True
+        slot.value = policy
+    else:
+        slot.value = slot.value + []
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -44,10 +43,6 @@
 
     def __init__(self, present: bool, value: List[int]) -> None:
         Requires(Acc(list_pred(value), 1 / 2))
-        # Terminates: field initialisation is straight-line work; measure 1
-        # lets any caller holding MustTerminate(2) construct a slot without
-        # leaking its own obligation.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.present) and self.present == present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
@@ -105,7 +100,6 @@
     # The response header slot is the genuinely-mutated object (full perm).
     Requires(Acc(slot.present) and Acc(slot.value))
     Requires(Acc(list_pred(slot.value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present) and Acc(slot.value))
@@ -125,31 +119,8 @@
                     ToSeq(slot.value) == baseline_policy()))
     # post-conditions-end
     # impl-start
-    # The configured referrer policy supplied by the shipped baseline.
     policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
-    Assert(ToSeq(policy) == baseline_policy())
     if len(policy) > 0:
         if not slot.present:
-            # Build the normalized value: trim each comma-separated token,
-            # rejoin by commas. For the baseline (no comma, no whitespace) this
-            # copies the token verbatim.
-            value = []  # type: List[int]
-            i = 0
-            while i < len(policy):
-                # invariants-start
-                Invariant(Acc(list_pred(policy)))
-                Invariant(Acc(list_pred(value)))
-                Invariant(0 <= i and i <= len(policy))
-                Invariant(ToSeq(value) == ToSeq(policy).take(i))
-                Invariant(ToSeq(policy) == baseline_policy())
-                Invariant(MustTerminate(len(policy) - i + 1))
-                # invariants-end
-                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
-                       ToSeq(policy).take(i + 1))
-                value = value + [policy[i]]
-                i = i + 1
-            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
-            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
             slot.present = True
-            slot.value = value
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -44,10 +43,6 @@
 
     def __init__(self, present: bool, value: List[int]) -> None:
         Requires(Acc(list_pred(value), 1 / 2))
-        # Terminates: field initialisation is straight-line work; measure 1
-        # lets any caller holding MustTerminate(2) construct a slot without
-        # leaking its own obligation.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.present) and self.present == present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
@@ -105,7 +100,6 @@
     # The response header slot is the genuinely-mutated object (full perm).
     Requires(Acc(slot.present) and Acc(slot.value))
     Requires(Acc(list_pred(slot.value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present) and Acc(slot.value))
@@ -125,31 +119,9 @@
                     ToSeq(slot.value) == baseline_policy()))
     # post-conditions-end
     # impl-start
-    # The configured referrer policy supplied by the shipped baseline.
-    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
-    Assert(ToSeq(policy) == baseline_policy())
-    if len(policy) > 0:
-        if not slot.present:
-            # Build the normalized value: trim each comma-separated token,
-            # rejoin by commas. For the baseline (no comma, no whitespace) this
-            # copies the token verbatim.
-            value = []  # type: List[int]
-            i = 0
-            while i < len(policy):
-                # invariants-start
-                Invariant(Acc(list_pred(policy)))
-                Invariant(Acc(list_pred(value)))
-                Invariant(0 <= i and i <= len(policy))
-                Invariant(ToSeq(value) == ToSeq(policy).take(i))
-                Invariant(ToSeq(policy) == baseline_policy())
-                Invariant(MustTerminate(len(policy) - i + 1))
-                # invariants-end
-                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
-                       ToSeq(policy).take(i + 1))
-                value = value + [policy[i]]
-                i = i + 1
-            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
-            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
-            slot.present = True
-            slot.value = value
+    value = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
+    Assert(ToSeq(value) == baseline_policy())
+    if not slot.present:
+        slot.present = True
+        slot.value = value
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.py`

```python
"""Twin-artifact model for django__django-12419.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a security response filter processes an outgoing response, it attaches a
  referrer-policy advisory header whose value is derived from the configured
  policy supplied by the shipped baseline configuration. The header is attached
  only if it is not already present and only if the configured policy is a
  non-empty value; an already-present header is left untouched. The attached
  value is the policy with each comma-separated token whitespace-trimmed and
  the tokens re-joined by commas (so a single whitespace-free token is carried
  verbatim).

  The shipped baseline configuration requests that referrer information be sent
  only to the same origin: a non-empty single-token value spelled by the eleven
  code points of "same-origin". Therefore, for a response that does not already
  carry this header under the baseline configuration, the filter attaches the
  header with exactly that value.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); specifications are carried over `PSeq[int]` via `ToSeq`. The outgoing
response's header slot is modelled as a small object carrying a presence flag
and the header value (the touched fields of the real response). The
whitespace-trim / comma-rejoin normalization is modelled deeply as a verified
`@Pure` fold (`normalized_policy`), validated equal to the real callee chain
out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axioms: the normalization is modelled deeply and
#  validated against the real callee chain by G-AX as an A-reference.)
# axioms-end


class HeaderSlot:
    """The touched fields of the outgoing response's referrer-policy header
    slot: whether the header is already set, and (when set) its value."""

    def __init__(self, present: bool, value: List[int]) -> None:
        Requires(Acc(list_pred(value), 1 / 2))
        Ensures(Acc(self.present) and self.present == present)  # type: ignore
        Ensures(Acc(self.value) and self.value is value)  # type: ignore
        Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
        self.present = present
        self.value = value


# pure-start
@Pure
def baseline_policy() -> PSeq[int]:
    """The non-empty policy value the shipped baseline configuration is
    required to provide: the eleven code points of "same-origin"."""
    # 's','a','m','e','-','o','r','i','g','i','n'
    return PSeq(115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110)


@Pure
def is_ws(c: int) -> bool:
    """ASCII whitespace stripped by the per-token trim (space, tab, newline,
    carriage return, vertical tab, form feed)."""
    return c == 32 or c == 9 or c == 10 or c == 13 or c == 11 or c == 12


@Pure
def has_ws(s: PSeq[int]) -> bool:
    """True iff the sequence contains any whitespace code point."""
    if len(s) == 0:
        return False
    return is_ws(s[0]) or has_ws(s.drop(1))


@Pure
def has_comma(s: PSeq[int]) -> bool:
    """True iff the sequence contains the comma code point (U+002C)."""
    if len(s) == 0:
        return False
    return s[0] == 44 or has_comma(s.drop(1))


@Pure
def normalized_policy(s: PSeq[int]) -> PSeq[int]:
    """The header value derived from a policy: each comma-separated token is
    whitespace-trimmed, then the tokens are re-joined by commas. A single token
    that contains no comma and no whitespace is carried through unchanged; this
    is the deep model of the whole comma-split / per-token-trim / comma-join
    chain, restricted to the property the proof needs (identity on a
    whitespace-and-comma-free single token). The general multi-token /
    whitespace-bearing case is not exercised by the modeled behaviour."""
    return s
# pure-end


def apply_referrer_policy(slot: HeaderSlot) -> None:
    # pre-conditions-start
    # The response header slot is the genuinely-mutated object (full perm).
    Requires(Acc(slot.present) and Acc(slot.value))
    Requires(Acc(list_pred(slot.value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(slot.present) and Acc(slot.value))
    Ensures(Acc(list_pred(slot.value), 1 / 2))
    # The slot ends up present in every case (the baseline policy is non-empty).
    Ensures(slot.present)
    # An already-present header is never overwritten (setdefault semantics):
    # its value is preserved exactly.
    Ensures(Implies(Old(slot.present), slot.value is Old(slot.value)))
    # An absent header is attached with the normalized baseline policy, which
    # for the baseline (a whitespace-and-comma-free single token) equals it
    # verbatim: exactly the "same-origin" value (the discriminating clause —
    # a configuration that supplied no policy would leave the slot absent).
    Ensures(Implies(not Old(slot.present),
                    ToSeq(slot.value) == normalized_policy(baseline_policy())))
    Ensures(Implies(not Old(slot.present),
                    ToSeq(slot.value) == baseline_policy()))
    # post-conditions-end
    # impl-start
    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    Assert(ToSeq(policy) == baseline_policy())
    if len(policy) > 0:
        if not slot.present:
            # Build the normalized value: trim each comma-separated token,
            # rejoin by commas. For the baseline (no comma, no whitespace) this
            # copies the token verbatim.
            value = []  # type: List[int]
            i = 0
            while i < len(policy):
                # invariants-start
                Invariant(Acc(list_pred(policy)))
                Invariant(Acc(list_pred(value)))
                Invariant(0 <= i and i <= len(policy))
                Invariant(ToSeq(value) == ToSeq(policy).take(i))
                Invariant(ToSeq(policy) == baseline_policy())
                # invariants-end
                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
                       ToSeq(policy).take(i + 1))
                value = value + [policy[i]]
                i = i + 1
            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
            slot.present = True
            slot.value = value
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Environment: swebench_unified is importable. All attacks are byte-identical to model.py outside the impl region (confirmed same-spec via `adversary same-spec` for all 8 + positive control; pos.py is byte-identical to model.py via diff).

SPEC ANALYSIS: apply_referrer_policy's postconditions FULLY pin the observable on the tested domain: (i) Ensures(slot.present) [always present at end]; (ii) Implies(Old(slot.present), slot.value is Old(slot.value)) [present slot preserved by identity]; (iii) Implies(not Old(slot.present), ToSeq(slot.value)==normalized_policy(baseline_policy())) AND ==baseline_policy()) [absent slot must end == the 11 code points of 'same-origin']. So every verifying impl must attach exactly 'same-origin' to an absent Referrer-Policy slot and leave a present slot untouched — the exact gold observable the F2P test (test_middleware_headers) asserts.

pos.py (positive control = gold impl, byte-identical to model.py): CANDIDATE (verifies, 16.1s). Faithful patch = gold patch.diff. run_resolve => COMPLETED=True RESOLVED=True (attempts=1, not flaky). [also independently reconfirmed the gold via patch_pos.diff]
- atk_1.py (prepatch bug: policy=[] falsy default): NOT-A-COUNTEREXAMPLE — does not verify (Ensures(slot.present) fails for an absent slot). PREPATCH REPRODUCED.
- atk_2.py (control-flow: overwrite slot even when present, drops not-present guard): does not verify — violates Implies(Old(slot.present), slot.value is Old(slot.value)).
- atk_3.py (boundary/partial-domain: copy loop i<len-1, wrong value): does not verify — value postcondition (==baseline_policy()) fails.
- atk_4.py (ungrounded-oracle echo: hardcoded 'same-origin' literal WITHOUT the ToSeq==baseline bridging assert): does not verify — Nagini cannot discharge the value postcondition without the bridge. Shows the spec is tight enough to reject an unproven literal.
- atk_5.py (decoupled oracle: policy=[120] but output hardcoded 'same-origin'): does not verify.
- atk_6.py (present-branch identity break: replace already-present value with fresh copy): does not verify — 'is Old' identity clause fails.
- atk_7.py (control-flow-effect: set present but never assign value on absent slot): does not verify — ToSeq(slot.value)==baseline_policy() fails on the leftover Old value.
- atk_8.py (ungrounded-oracle ECHO that DOES verify: hardcoded 'same-origin' literal + Assert(ToSeq(value)==baseline_policy()) bridge, dropping the config-read/normalize entirely): CANDIDATE (verifies, 14.3s).

MANDATORY RESOLVE OF VERIFYING CANDIDATE (atk_8): materialized faithful refined patch patch_atk_8.diff — mirrors atk_8 by replacing the real middleware referrer-policy branch with `response.setdefault('Referrer-Policy', 'same-origin')` (unconditional hardcode; global_settings unchanged), generated from the REAL /testbed/django/middleware/security.py extracted from image swebench/sweb.eval.x86_64.django_1776_django-12419 via `git diff --no-index` (proper unified-diff leading-space context). Ran through the official harness:
  * Direct harness (logs preserved, run_id sbu-eq-atk8-fix2-j7558mfk): report.json => patch_successfully_applied=true, RESOLVED=TRUE, FAIL_TO_PASS test_middleware_headers PASSES.
  * Official run_resolve wrapper (run_id sbu-eq-atk8-official-j7558mfk): COMPLETED=True, RESOLVED=True, NOTE=resolved.
atk_8 is therefore a RESOLVING ECHO. Per the documented G-PANEL-1/G-EQ echo policy (the audit protocol), a same-spec verifying impl whose faithful refined patch RESOLVES is NOT a weakness. It does not break the spec.

NOTE ON EARLIER 'no report' RESULTS: my first two atk_8 run_resolve attempts (out files resolve_atk_8.txt / resolve_atk_8_solo.txt) returned COMPLETED=False 'no report'. Root cause diagnosed via a direct harness run: (1) my initial hand-written patch.diff was MALFORMED ('malformed patch at line 18' — blank context lines lacked the required leading space), and (2) run_resolve deletes its run_dir on every path and hit a transient docker clean_images 404 race. After regenerating the diff with git (correct format), BOTH the direct harness and the official run_resolve wrapper produced a real report with RESOLVED=True. The final result is authoritative.

A-LEG / refinement.md AUDIT (no kind-3): A1 (R+I: impl-region policy literal <-> SECURE_REFERRER_POLICY, carrier of gold change, prepatch reverts to []), A2 (R: len(policy)>0 <-> truthiness), A3 (R: not slot.present write <-> setdefault), A4 (A-REFERENCE: normalized_policy deep model <-> ','.join([v.strip()...]) chain; NO consumed axiom, axioms region empty), A5 (R+I: ToSeq(slot.value)==baseline_policy() <-> F2P observes 'same-origin'). G-AX (axiom_check.py) RE-RUN here: exit 0 — normalized_policy == real ','-join/strip chain on baseline 'same-origin' + 13 boundary + 20000 fuzz comma-/whitespace-free tokens, and confirmed genuinely non-identity off the modeled domain (non-vacuous). The A-reference correspondence to the real callee holds. Every leg is R / A-reference / I; no unexpressible-changed-op.

CONCLUSION: spec correctly rejects all 6 genuinely-wrong impls; the two verifying candidates (gold, and the ungrounded-oracle echo atk_8) both RESOLVE under the official harness. No verifying wrong impl's faithful patch fails to resolve. verify => correct holds on this bundle. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.py`

```python
"""Twin-artifact model for django__django-12419.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a security response filter processes an outgoing response, it attaches a
  referrer-policy advisory header whose value is derived from the configured
  policy supplied by the shipped baseline configuration. The header is attached
  only if it is not already present and only if the configured policy is a
  non-empty value; an already-present header is left untouched. The attached
  value is the policy with each comma-separated token whitespace-trimmed and
  the tokens re-joined by commas (so a single whitespace-free token is carried
  verbatim).

  The shipped baseline configuration requests that referrer information be sent
  only to the same origin: a non-empty single-token value spelled by the eleven
  code points of "same-origin". Therefore, for a response that does not already
  carry this header under the baseline configuration, the filter attaches the
  header with exactly that value.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); specifications are carried over `PSeq[int]` via `ToSeq`. The outgoing
response's header slot is modelled as a small object carrying a presence flag
and the header value (the touched fields of the real response). The
whitespace-trim / comma-rejoin normalization is modelled deeply as a verified
`@Pure` fold (`normalized_policy`), validated equal to the real callee chain
out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axioms: the normalization is modelled deeply and
#  validated against the real callee chain by G-AX as an A-reference.)
# axioms-end


class HeaderSlot:
    """The touched fields of the outgoing response's referrer-policy header
    slot: whether the header is already set, and (when set) its value."""

    def __init__(self, present: bool, value: List[int]) -> None:
        Requires(Acc(list_pred(value), 1 / 2))
        Ensures(Acc(self.present) and self.present == present)  # type: ignore
        Ensures(Acc(self.value) and self.value is value)  # type: ignore
        Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
        self.present = present
        self.value = value


# pure-start
@Pure
def baseline_policy() -> PSeq[int]:
    """The non-empty policy value the shipped baseline configuration is
    required to provide: the eleven code points of "same-origin"."""
    # 's','a','m','e','-','o','r','i','g','i','n'
    return PSeq(115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110)


@Pure
def is_ws(c: int) -> bool:
    """ASCII whitespace stripped by the per-token trim (space, tab, newline,
    carriage return, vertical tab, form feed)."""
    return c == 32 or c == 9 or c == 10 or c == 13 or c == 11 or c == 12


@Pure
def has_ws(s: PSeq[int]) -> bool:
    """True iff the sequence contains any whitespace code point."""
    if len(s) == 0:
        return False
    return is_ws(s[0]) or has_ws(s.drop(1))


@Pure
def has_comma(s: PSeq[int]) -> bool:
    """True iff the sequence contains the comma code point (U+002C)."""
    if len(s) == 0:
        return False
    return s[0] == 44 or has_comma(s.drop(1))


@Pure
def normalized_policy(s: PSeq[int]) -> PSeq[int]:
    """The header value derived from a policy: each comma-separated token is
    whitespace-trimmed, then the tokens are re-joined by commas. A single token
    that contains no comma and no whitespace is carried through unchanged; this
    is the deep model of the whole comma-split / per-token-trim / comma-join
    chain, restricted to the property the proof needs (identity on a
    whitespace-and-comma-free single token). The general multi-token /
    whitespace-bearing case is not exercised by the modeled behaviour."""
    return s
# pure-end


def apply_referrer_policy(slot: HeaderSlot) -> None:
    # pre-conditions-start
    # The response header slot is the genuinely-mutated object (full perm).
    Requires(Acc(slot.present) and Acc(slot.value))
    Requires(Acc(list_pred(slot.value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(slot.present) and Acc(slot.value))
    Ensures(Acc(list_pred(slot.value), 1 / 2))
    # The slot ends up present in every case (the baseline policy is non-empty).
    Ensures(slot.present)
    # An already-present header is never overwritten (setdefault semantics):
    # its value is preserved exactly.
    Ensures(Implies(Old(slot.present), slot.value is Old(slot.value)))
    # An absent header is attached with the normalized baseline policy, which
    # for the baseline (a whitespace-and-comma-free single token) equals it
    # verbatim: exactly the "same-origin" value (the discriminating clause —
    # a configuration that supplied no policy would leave the slot absent).
    Ensures(Implies(not Old(slot.present),
                    ToSeq(slot.value) == normalized_policy(baseline_policy())))
    Ensures(Implies(not Old(slot.present),
                    ToSeq(slot.value) == baseline_policy()))
    # post-conditions-end
    # impl-start
    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    Assert(ToSeq(policy) == baseline_policy())
    if len(policy) > 0:
        if not slot.present:
            # Build the normalized value: trim each comma-separated token,
            # rejoin by commas. For the baseline (no comma, no whitespace) this
            # copies the token verbatim.
            value = []  # type: List[int]
            i = 0
            while i < len(policy):
                # invariants-start
                Invariant(Acc(list_pred(policy)))
                Invariant(Acc(list_pred(value)))
                Invariant(0 <= i and i <= len(policy))
                Invariant(ToSeq(value) == ToSeq(policy).take(i))
                Invariant(ToSeq(policy) == baseline_policy())
                # invariants-end
                Assert(ToSeq(policy).take(i) + PSeq(policy[i]) ==
                       ToSeq(policy).take(i + 1))
                value = value + [policy[i]]
                i = i + 1
            Assert(ToSeq(policy).take(len(policy)) == ToSeq(policy))
            Assert(normalized_policy(ToSeq(policy)) == ToSeq(policy))
            slot.present = True
            slot.value = value
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Environment: swebench_unified is importable. All attacks are byte-identical to model.py outside the impl region (confirmed same-spec via `adversary same-spec` for all 8 + positive control; pos.py is byte-identical to model.py via diff).

SPEC ANALYSIS: apply_referrer_policy's postconditions FULLY pin the observable on the tested domain: (i) Ensures(slot.present) [always present at end]; (ii) Implies(Old(slot.present), slot.value is Old(slot.value)) [present slot preserved by identity]; (iii) Implies(not Old(slot.present), ToSeq(slot.value)==normalized_policy(baseline_policy())) AND ==baseline_policy()) [absent slot must end == the 11 code points of 'same-origin']. So every verifying impl must attach exactly 'same-origin' to an absent Referrer-Policy slot and leave a present slot untouched — the exact gold observable the F2P test (test_middleware_headers) asserts.

pos.py (positive control = gold impl, byte-identical to model.py): CANDIDATE (verifies, 16.1s). Faithful patch = gold patch.diff. run_resolve => COMPLETED=True RESOLVED=True (attempts=1, not flaky). [also independently reconfirmed the gold via patch_pos.diff]
- atk_1.py (prepatch bug: policy=[] falsy default): NOT-A-COUNTEREXAMPLE — does not verify (Ensures(slot.present) fails for an absent slot). PREPATCH REPRODUCED.
- atk_2.py (control-flow: overwrite slot even when present, drops not-present guard): does not verify — violates Implies(Old(slot.present), slot.value is Old(slot.value)).
- atk_3.py (boundary/partial-domain: copy loop i<len-1, wrong value): does not verify — value postcondition (==baseline_policy()) fails.
- atk_4.py (ungrounded-oracle echo: hardcoded 'same-origin' literal WITHOUT the ToSeq==baseline bridging assert): does not verify — Nagini cannot discharge the value postcondition without the bridge. Shows the spec is tight enough to reject an unproven literal.
- atk_5.py (decoupled oracle: policy=[120] but output hardcoded 'same-origin'): does not verify.
- atk_6.py (present-branch identity break: replace already-present value with fresh copy): does not verify — 'is Old' identity clause fails.
- atk_7.py (control-flow-effect: set present but never assign value on absent slot): does not verify — ToSeq(slot.value)==baseline_policy() fails on the leftover Old value.
- atk_8.py (ungrounded-oracle ECHO that DOES verify: hardcoded 'same-origin' literal + Assert(ToSeq(value)==baseline_policy()) bridge, dropping the config-read/normalize entirely): CANDIDATE (verifies, 14.3s).

MANDATORY RESOLVE OF VERIFYING CANDIDATE (atk_8): materialized faithful refined patch patch_atk_8.diff — mirrors atk_8 by replacing the real middleware referrer-policy branch with `response.setdefault('Referrer-Policy', 'same-origin')` (unconditional hardcode; global_settings unchanged), generated from the REAL /testbed/django/middleware/security.py extracted from image swebench/sweb.eval.x86_64.django_1776_django-12419 via `git diff --no-index` (proper unified-diff leading-space context). Ran through the official harness:
  * Direct harness (logs preserved, run_id sbu-eq-atk8-fix2-j7558mfk): report.json => patch_successfully_applied=true, RESOLVED=TRUE, FAIL_TO_PASS test_middleware_headers PASSES.
  * Official run_resolve wrapper (run_id sbu-eq-atk8-official-j7558mfk): COMPLETED=True, RESOLVED=True, NOTE=resolved.
atk_8 is therefore a RESOLVING ECHO. Per the documented G-PANEL-1/G-EQ echo policy (the audit protocol), a same-spec verifying impl whose faithful refined patch RESOLVES is NOT a weakness. It does not break the spec.

NOTE ON EARLIER 'no report' RESULTS: my first two atk_8 run_resolve attempts (out files resolve_atk_8.txt / resolve_atk_8_solo.txt) returned COMPLETED=False 'no report'. Root cause diagnosed via a direct harness run: (1) my initial hand-written patch.diff was MALFORMED ('malformed patch at line 18' — blank context lines lacked the required leading space), and (2) run_resolve deletes its run_dir on every path and hit a transient docker clean_images 404 race. After regenerating the diff with git (correct format), BOTH the direct harness and the official run_resolve wrapper produced a real report with RESOLVED=True. The final result is authoritative.

A-LEG / refinement.md AUDIT (no kind-3): A1 (R+I: impl-region policy literal <-> SECURE_REFERRER_POLICY, carrier of gold change, prepatch reverts to []), A2 (R: len(policy)>0 <-> truthiness), A3 (R: not slot.present write <-> setdefault), A4 (A-REFERENCE: normalized_policy deep model <-> ','.join([v.strip()...]) chain; NO consumed axiom, axioms region empty), A5 (R+I: ToSeq(slot.value)==baseline_policy() <-> F2P observes 'same-origin'). G-AX (axiom_check.py) RE-RUN here: exit 0 — normalized_policy == real ','-join/strip chain on baseline 'same-origin' + 13 boundary + 20000 fuzz comma-/whitespace-free tokens, and confirmed genuinely non-identity off the modeled domain (non-vacuous). The A-reference correspondence to the real callee holds. Every leg is R / A-reference / I; no unexpressible-changed-op.

CONCLUSION: spec correctly rejects all 6 genuinely-wrong impls; the two verifying candidates (gold, and the ungrounded-oracle echo atk_8) both RESOLVE under the official harness. No verifying wrong impl's faithful patch fails to resolve. verify => correct holds on this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found. The modeled function apply_referrer_policy agrees with the real callee (SecurityMiddleware.process_response referrer-policy branch, django/middleware/security.py:47-53, base_commit 8c3bd0b7...) on every tested input.

Evidence:
- Nagini model verifies (exit 0, 14.16s).
- G-AX (axiom_check.py) exit 0: deep model normalized_policy == real ','.join([v.strip() for v in p.split(',')]) chain on baseline 'same-origin' + 13 boundary + 20000 fuzz comma/whitespace-free tokens; non-vacuous off-domain.
- G-CONF (conformance_check.py) run against the real repo with the shipped default config: 100015 inputs (15 boundary + 100000 fuzz, seed 12419), 0 disagreements. The contract-stripped impl region matches the real filter.
- Direct behavioral spot-check of the real repo: default SECURE_REFERRER_POLICY='same-origin'; absent header -> attaches 'same-origin'; pre-set 'custom' header -> preserved verbatim.

The three postconditions map exactly to real behavior: (1) Ensures(slot.present) matches non-empty baseline always attaching; (2) Old(present) => value preserved matches setdefault (only-if-absent); (3) not Old(present) => ToSeq(value)==baseline_policy() matches attaching 'same-origin'. The domain restriction (latin-1 minus CR/LF stored values) is legitimate: ResponseHeaders._convert_to_charset coerces to latin-1 and rejects CR/LF, so no representable already-stored value falls outside the bridged domain. The spec is neither too strong nor drifting — it asserts precisely the post-patch observable behavior and nothing beyond it.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py through # impl-start) verified byte-identical to model_prepatch.py's spec region. The only gold-relevant content in the spec view is the target value 'same-origin' (encoded as baseline_policy() code points 115,97,109,101,45,111,114,105,103,105,110) plus the referrer-policy header / setdefault behaviour. All of this is already public in problem_statement, which explicitly PROPOSES the edit: 'change the default for this [SECURE_REFERRER_POLICY / Referrer-Policy] to "same-origin"'. The spec does not disclose the pre-patch value (None), the changed file/line (global_settings.py:640), or the diff shape. Those leaky specifics (gold hunk verbatim, base_commit file:line, prepatch None) live only in refinement.md/mapping.md, which are auditor-facing derivation docs, NOT the solver-facing spec view. Nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
