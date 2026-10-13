# P2 adversarial audit — django__django-13551

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,10 +58,6 @@
 
 class Account:
     def __init__(self) -> None:
-        # Terminates: field initialisation is straight-line work, but the four
-        # empty containers it builds each carry their own obligation, so this
-        # sits at the leaf level above them rather than at 1.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
         Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
         Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
@@ -83,9 +78,6 @@
     Requires(Acc(user.address, 1 / 2))
     Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
     Requires(Acc(list_pred(timestamp), 1 / 2))
-    # Strictly above the account constructor's own level (2), so a caller may
-    # build an account value before invoking this.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
@@ -109,8 +101,6 @@
         == effective_address(user.address))
     # post-conditions-end
     # impl-start
-    # Ghost snapshots of the component sequences, so the loop invariants read
-    # only locals (each field's fractional permission is held by the frame).
     pk_s = ToSeq(user.pk)
     pw_s = ToSeq(user.password)
     lr_s = ToSeq(user.login_repr)
@@ -119,75 +109,46 @@
     result = []  # type: List[int]
     i = 0
     while i < len(user.pk):
-        # invariants-start
         Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
         Invariant(pk_s == ToSeq(user.pk))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.pk))
         Invariant(ToSeq(result) == pk_s.take(i))
-        Invariant(MustTerminate(len(user.pk) - i + 1))
-        # invariants-end
         result.append(user.pk[i])
         i = i + 1
     Assert(pk_s.take(len(user.pk)) == pk_s)
 
     i = 0
     while i < len(user.password):
-        # invariants-start
         Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
         Invariant(pw_s == ToSeq(user.password))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.password))
         Invariant(ToSeq(result) == pk_s + pw_s.take(i))
-        Invariant(MustTerminate(len(user.password) - i + 1))
-        # invariants-end
         result.append(user.password[i])
         i = i + 1
     Assert(pw_s.take(len(user.password)) == pw_s)
 
     i = 0
     while i < len(user.login_repr):
-        # invariants-start
         Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
         Invariant(lr_s == ToSeq(user.login_repr))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.login_repr))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
-        Invariant(MustTerminate(len(user.login_repr) - i + 1))
-        # invariants-end
         result.append(user.login_repr[i])
         i = i + 1
     Assert(lr_s.take(len(user.login_repr)) == lr_s)
 
     i = 0
     while i < len(timestamp):
-        # invariants-start
         Invariant(Acc(list_pred(timestamp), 1 / 2))
         Invariant(ts_s == ToSeq(timestamp))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(timestamp))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
-        Invariant(MustTerminate(len(timestamp) - i + 1))
-        # invariants-end
         result.append(timestamp[i])
         i = i + 1
     Assert(ts_s.take(len(timestamp)) == ts_s)
-
-    addr = user.address
-    if addr is not None:
-        addr_s = ToSeq(addr)
-        j = 0
-        while j < len(addr):
-            # invariants-start
-            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
-            Invariant(addr_s == ToSeq(addr))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(addr))
-            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
-            Invariant(MustTerminate(len(addr) - j + 1))
-            # invariants-end
-            result.append(addr[j])
-            j = j + 1
-        Assert(addr_s.take(len(addr)) == addr_s)
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,10 +58,6 @@
 
 class Account:
     def __init__(self) -> None:
-        # Terminates: field initialisation is straight-line work, but the four
-        # empty containers it builds each carry their own obligation, so this
-        # sits at the leaf level above them rather than at 1.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
         Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
         Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
@@ -83,9 +78,6 @@
     Requires(Acc(user.address, 1 / 2))
     Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
     Requires(Acc(list_pred(timestamp), 1 / 2))
-    # Strictly above the account constructor's own level (2), so a caller may
-    # build an account value before invoking this.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
@@ -109,8 +101,6 @@
         == effective_address(user.address))
     # post-conditions-end
     # impl-start
-    # Ghost snapshots of the component sequences, so the loop invariants read
-    # only locals (each field's fractional permission is held by the frame).
     pk_s = ToSeq(user.pk)
     pw_s = ToSeq(user.password)
     lr_s = ToSeq(user.login_repr)
@@ -119,73 +109,57 @@
     result = []  # type: List[int]
     i = 0
     while i < len(user.pk):
-        # invariants-start
         Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
         Invariant(pk_s == ToSeq(user.pk))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.pk))
         Invariant(ToSeq(result) == pk_s.take(i))
-        Invariant(MustTerminate(len(user.pk) - i + 1))
-        # invariants-end
         result.append(user.pk[i])
         i = i + 1
     Assert(pk_s.take(len(user.pk)) == pk_s)
 
     i = 0
     while i < len(user.password):
-        # invariants-start
         Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
         Invariant(pw_s == ToSeq(user.password))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.password))
         Invariant(ToSeq(result) == pk_s + pw_s.take(i))
-        Invariant(MustTerminate(len(user.password) - i + 1))
-        # invariants-end
         result.append(user.password[i])
         i = i + 1
     Assert(pw_s.take(len(user.password)) == pw_s)
 
     i = 0
+    while i < len(timestamp):
+        Invariant(Acc(list_pred(timestamp), 1 / 2))
+        Invariant(ts_s == ToSeq(timestamp))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= i and i <= len(timestamp))
+        Invariant(ToSeq(result) == pk_s + pw_s + ts_s.take(i))
+        result.append(timestamp[i])
+        i = i + 1
+    Assert(ts_s.take(len(timestamp)) == ts_s)
+
+    i = 0
     while i < len(user.login_repr):
-        # invariants-start
         Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
         Invariant(lr_s == ToSeq(user.login_repr))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.login_repr))
-        Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
-        Invariant(MustTerminate(len(user.login_repr) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(result) == pk_s + pw_s + ts_s + lr_s.take(i))
         result.append(user.login_repr[i])
         i = i + 1
     Assert(lr_s.take(len(user.login_repr)) == lr_s)
-
-    i = 0
-    while i < len(timestamp):
-        # invariants-start
-        Invariant(Acc(list_pred(timestamp), 1 / 2))
-        Invariant(ts_s == ToSeq(timestamp))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(timestamp))
-        Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
-        Invariant(MustTerminate(len(timestamp) - i + 1))
-        # invariants-end
-        result.append(timestamp[i])
-        i = i + 1
-    Assert(ts_s.take(len(timestamp)) == ts_s)
-
     addr = user.address
     if addr is not None:
         addr_s = ToSeq(addr)
         j = 0
         while j < len(addr):
-            # invariants-start
             Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
             Invariant(addr_s == ToSeq(addr))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(addr))
             Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
-            Invariant(MustTerminate(len(addr) - j + 1))
-            # invariants-end
             result.append(addr[j])
             j = j + 1
         Assert(addr_s.take(len(addr)) == addr_s)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,10 +58,6 @@
 
 class Account:
     def __init__(self) -> None:
-        # Terminates: field initialisation is straight-line work, but the four
-        # empty containers it builds each carry their own obligation, so this
-        # sits at the leaf level above them rather than at 1.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
         Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
         Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
@@ -83,9 +78,6 @@
     Requires(Acc(user.address, 1 / 2))
     Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
     Requires(Acc(list_pred(timestamp), 1 / 2))
-    # Strictly above the account constructor's own level (2), so a caller may
-    # build an account value before invoking this.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
@@ -109,8 +101,6 @@
         == effective_address(user.address))
     # post-conditions-end
     # impl-start
-    # Ghost snapshots of the component sequences, so the loop invariants read
-    # only locals (each field's fractional permission is held by the frame).
     pk_s = ToSeq(user.pk)
     pw_s = ToSeq(user.password)
     lr_s = ToSeq(user.login_repr)
@@ -119,75 +109,58 @@
     result = []  # type: List[int]
     i = 0
     while i < len(user.pk):
-        # invariants-start
         Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
         Invariant(pk_s == ToSeq(user.pk))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.pk))
         Invariant(ToSeq(result) == pk_s.take(i))
-        Invariant(MustTerminate(len(user.pk) - i + 1))
-        # invariants-end
         result.append(user.pk[i])
         i = i + 1
     Assert(pk_s.take(len(user.pk)) == pk_s)
 
     i = 0
     while i < len(user.password):
-        # invariants-start
         Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
         Invariant(pw_s == ToSeq(user.password))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.password))
         Invariant(ToSeq(result) == pk_s + pw_s.take(i))
-        Invariant(MustTerminate(len(user.password) - i + 1))
-        # invariants-end
         result.append(user.password[i])
         i = i + 1
     Assert(pw_s.take(len(user.password)) == pw_s)
 
     i = 0
     while i < len(user.login_repr):
-        # invariants-start
         Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
         Invariant(lr_s == ToSeq(user.login_repr))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.login_repr))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
-        Invariant(MustTerminate(len(user.login_repr) - i + 1))
-        # invariants-end
         result.append(user.login_repr[i])
         i = i + 1
     Assert(lr_s.take(len(user.login_repr)) == lr_s)
 
     i = 0
     while i < len(timestamp):
-        # invariants-start
         Invariant(Acc(list_pred(timestamp), 1 / 2))
         Invariant(ts_s == ToSeq(timestamp))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(timestamp))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
-        Invariant(MustTerminate(len(timestamp) - i + 1))
-        # invariants-end
         result.append(timestamp[i])
         i = i + 1
     Assert(ts_s.take(len(timestamp)) == ts_s)
-
     addr = user.address
     if addr is not None:
         addr_s = ToSeq(addr)
-        j = 0
+        j = 1
         while j < len(addr):
-            # invariants-start
             Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
             Invariant(addr_s == ToSeq(addr))
             Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(addr))
+            Invariant(1 <= j and j <= len(addr))
             Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
-            Invariant(MustTerminate(len(addr) - j + 1))
-            # invariants-end
             result.append(addr[j])
             j = j + 1
-        Assert(addr_s.take(len(addr)) == addr_s)
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,10 +58,6 @@
 
 class Account:
     def __init__(self) -> None:
-        # Terminates: field initialisation is straight-line work, but the four
-        # empty containers it builds each carry their own obligation, so this
-        # sits at the leaf level above them rather than at 1.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
         Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
         Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
@@ -83,9 +78,6 @@
     Requires(Acc(user.address, 1 / 2))
     Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
     Requires(Acc(list_pred(timestamp), 1 / 2))
-    # Strictly above the account constructor's own level (2), so a caller may
-    # build an account value before invoking this.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
@@ -109,85 +101,29 @@
         == effective_address(user.address))
     # post-conditions-end
     # impl-start
-    # Ghost snapshots of the component sequences, so the loop invariants read
-    # only locals (each field's fractional permission is held by the frame).
     pk_s = ToSeq(user.pk)
     pw_s = ToSeq(user.password)
     lr_s = ToSeq(user.login_repr)
-    ts_s = ToSeq(timestamp)
 
     result = []  # type: List[int]
     i = 0
     while i < len(user.pk):
-        # invariants-start
         Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
         Invariant(pk_s == ToSeq(user.pk))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.pk))
         Invariant(ToSeq(result) == pk_s.take(i))
-        Invariant(MustTerminate(len(user.pk) - i + 1))
-        # invariants-end
         result.append(user.pk[i])
         i = i + 1
-    Assert(pk_s.take(len(user.pk)) == pk_s)
 
     i = 0
     while i < len(user.password):
-        # invariants-start
         Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
         Invariant(pw_s == ToSeq(user.password))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.password))
         Invariant(ToSeq(result) == pk_s + pw_s.take(i))
-        Invariant(MustTerminate(len(user.password) - i + 1))
-        # invariants-end
         result.append(user.password[i])
         i = i + 1
-    Assert(pw_s.take(len(user.password)) == pw_s)
-
-    i = 0
-    while i < len(user.login_repr):
-        # invariants-start
-        Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
-        Invariant(lr_s == ToSeq(user.login_repr))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(user.login_repr))
-        Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
-        Invariant(MustTerminate(len(user.login_repr) - i + 1))
-        # invariants-end
-        result.append(user.login_repr[i])
-        i = i + 1
-    Assert(lr_s.take(len(user.login_repr)) == lr_s)
-
-    i = 0
-    while i < len(timestamp):
-        # invariants-start
-        Invariant(Acc(list_pred(timestamp), 1 / 2))
-        Invariant(ts_s == ToSeq(timestamp))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(timestamp))
-        Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
-        Invariant(MustTerminate(len(timestamp) - i + 1))
-        # invariants-end
-        result.append(timestamp[i])
-        i = i + 1
-    Assert(ts_s.take(len(timestamp)) == ts_s)
-
-    addr = user.address
-    if addr is not None:
-        addr_s = ToSeq(addr)
-        j = 0
-        while j < len(addr):
-            # invariants-start
-            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
-            Invariant(addr_s == ToSeq(addr))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(addr))
-            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
-            Invariant(MustTerminate(len(addr) - j + 1))
-            # invariants-end
-            result.append(addr[j])
-            j = j + 1
-        Assert(addr_s.take(len(addr)) == addr_s)
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,10 +58,6 @@
 
 class Account:
     def __init__(self) -> None:
-        # Terminates: field initialisation is straight-line work, but the four
-        # empty containers it builds each carry their own obligation, so this
-        # sits at the leaf level above them rather than at 1.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
         Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
         Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
@@ -83,9 +78,6 @@
     Requires(Acc(user.address, 1 / 2))
     Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
     Requires(Acc(list_pred(timestamp), 1 / 2))
-    # Strictly above the account constructor's own level (2), so a caller may
-    # build an account value before invoking this.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
@@ -109,8 +101,6 @@
         == effective_address(user.address))
     # post-conditions-end
     # impl-start
-    # Ghost snapshots of the component sequences, so the loop invariants read
-    # only locals (each field's fractional permission is held by the frame).
     pk_s = ToSeq(user.pk)
     pw_s = ToSeq(user.password)
     lr_s = ToSeq(user.login_repr)
@@ -119,75 +109,60 @@
     result = []  # type: List[int]
     i = 0
     while i < len(user.pk):
-        # invariants-start
         Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
         Invariant(pk_s == ToSeq(user.pk))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.pk))
         Invariant(ToSeq(result) == pk_s.take(i))
-        Invariant(MustTerminate(len(user.pk) - i + 1))
-        # invariants-end
         result.append(user.pk[i])
         i = i + 1
     Assert(pk_s.take(len(user.pk)) == pk_s)
 
     i = 0
     while i < len(user.password):
-        # invariants-start
         Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
         Invariant(pw_s == ToSeq(user.password))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.password))
         Invariant(ToSeq(result) == pk_s + pw_s.take(i))
-        Invariant(MustTerminate(len(user.password) - i + 1))
-        # invariants-end
         result.append(user.password[i])
         i = i + 1
     Assert(pw_s.take(len(user.password)) == pw_s)
 
     i = 0
     while i < len(user.login_repr):
-        # invariants-start
         Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
         Invariant(lr_s == ToSeq(user.login_repr))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.login_repr))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
-        Invariant(MustTerminate(len(user.login_repr) - i + 1))
-        # invariants-end
         result.append(user.login_repr[i])
         i = i + 1
     Assert(lr_s.take(len(user.login_repr)) == lr_s)
 
     i = 0
     while i < len(timestamp):
-        # invariants-start
         Invariant(Acc(list_pred(timestamp), 1 / 2))
         Invariant(ts_s == ToSeq(timestamp))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(timestamp))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
-        Invariant(MustTerminate(len(timestamp) - i + 1))
-        # invariants-end
         result.append(timestamp[i])
         i = i + 1
     Assert(ts_s.take(len(timestamp)) == ts_s)
-
     addr = user.address
     if addr is not None:
         addr_s = ToSeq(addr)
         j = 0
         while j < len(addr):
-            # invariants-start
             Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
             Invariant(addr_s == ToSeq(addr))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(addr))
             Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
-            Invariant(MustTerminate(len(addr) - j + 1))
-            # invariants-end
             result.append(addr[j])
             j = j + 1
-        Assert(addr_s.take(len(addr)) == addr_s)
+        if len(addr) > 0:
+            result.append(addr[0])
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,10 +58,6 @@
 
 class Account:
     def __init__(self) -> None:
-        # Terminates: field initialisation is straight-line work, but the four
-        # empty containers it builds each carry their own obligation, so this
-        # sits at the leaf level above them rather than at 1.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
         Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
         Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
@@ -83,9 +78,6 @@
     Requires(Acc(user.address, 1 / 2))
     Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
     Requires(Acc(list_pred(timestamp), 1 / 2))
-    # Strictly above the account constructor's own level (2), so a caller may
-    # build an account value before invoking this.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
@@ -109,85 +101,16 @@
         == effective_address(user.address))
     # post-conditions-end
     # impl-start
-    # Ghost snapshots of the component sequences, so the loop invariants read
-    # only locals (each field's fractional permission is held by the frame).
     pk_s = ToSeq(user.pk)
-    pw_s = ToSeq(user.password)
-    lr_s = ToSeq(user.login_repr)
-    ts_s = ToSeq(timestamp)
-
     result = []  # type: List[int]
     i = 0
     while i < len(user.pk):
-        # invariants-start
         Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
         Invariant(pk_s == ToSeq(user.pk))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.pk))
         Invariant(ToSeq(result) == pk_s.take(i))
-        Invariant(MustTerminate(len(user.pk) - i + 1))
-        # invariants-end
         result.append(user.pk[i])
         i = i + 1
-    Assert(pk_s.take(len(user.pk)) == pk_s)
-
-    i = 0
-    while i < len(user.password):
-        # invariants-start
-        Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
-        Invariant(pw_s == ToSeq(user.password))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(user.password))
-        Invariant(ToSeq(result) == pk_s + pw_s.take(i))
-        Invariant(MustTerminate(len(user.password) - i + 1))
-        # invariants-end
-        result.append(user.password[i])
-        i = i + 1
-    Assert(pw_s.take(len(user.password)) == pw_s)
-
-    i = 0
-    while i < len(user.login_repr):
-        # invariants-start
-        Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
-        Invariant(lr_s == ToSeq(user.login_repr))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(user.login_repr))
-        Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
-        Invariant(MustTerminate(len(user.login_repr) - i + 1))
-        # invariants-end
-        result.append(user.login_repr[i])
-        i = i + 1
-    Assert(lr_s.take(len(user.login_repr)) == lr_s)
-
-    i = 0
-    while i < len(timestamp):
-        # invariants-start
-        Invariant(Acc(list_pred(timestamp), 1 / 2))
-        Invariant(ts_s == ToSeq(timestamp))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(timestamp))
-        Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
-        Invariant(MustTerminate(len(timestamp) - i + 1))
-        # invariants-end
-        result.append(timestamp[i])
-        i = i + 1
-    Assert(ts_s.take(len(timestamp)) == ts_s)
-
-    addr = user.address
-    if addr is not None:
-        addr_s = ToSeq(addr)
-        j = 0
-        while j < len(addr):
-            # invariants-start
-            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
-            Invariant(addr_s == ToSeq(addr))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(addr))
-            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
-            Invariant(MustTerminate(len(addr) - j + 1))
-            # invariants-end
-            result.append(addr[j])
-            j = j + 1
-        Assert(addr_s.take(len(addr)) == addr_s)
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,10 +58,6 @@
 
 class Account:
     def __init__(self) -> None:
-        # Terminates: field initialisation is straight-line work, but the four
-        # empty containers it builds each carry their own obligation, so this
-        # sits at the leaf level above them rather than at 1.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
         Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
         Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
@@ -83,9 +78,6 @@
     Requires(Acc(user.address, 1 / 2))
     Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
     Requires(Acc(list_pred(timestamp), 1 / 2))
-    # Strictly above the account constructor's own level (2), so a caller may
-    # build an account value before invoking this.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
@@ -109,8 +101,6 @@
         == effective_address(user.address))
     # post-conditions-end
     # impl-start
-    # Ghost snapshots of the component sequences, so the loop invariants read
-    # only locals (each field's fractional permission is held by the frame).
     pk_s = ToSeq(user.pk)
     pw_s = ToSeq(user.password)
     lr_s = ToSeq(user.login_repr)
@@ -119,75 +109,58 @@
     result = []  # type: List[int]
     i = 0
     while i < len(user.pk):
-        # invariants-start
         Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
         Invariant(pk_s == ToSeq(user.pk))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.pk))
         Invariant(ToSeq(result) == pk_s.take(i))
-        Invariant(MustTerminate(len(user.pk) - i + 1))
-        # invariants-end
         result.append(user.pk[i])
         i = i + 1
     Assert(pk_s.take(len(user.pk)) == pk_s)
 
     i = 0
     while i < len(user.password):
-        # invariants-start
         Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
         Invariant(pw_s == ToSeq(user.password))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.password))
         Invariant(ToSeq(result) == pk_s + pw_s.take(i))
-        Invariant(MustTerminate(len(user.password) - i + 1))
-        # invariants-end
         result.append(user.password[i])
         i = i + 1
     Assert(pw_s.take(len(user.password)) == pw_s)
 
     i = 0
     while i < len(user.login_repr):
-        # invariants-start
         Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
         Invariant(lr_s == ToSeq(user.login_repr))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.login_repr))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
-        Invariant(MustTerminate(len(user.login_repr) - i + 1))
-        # invariants-end
         result.append(user.login_repr[i])
         i = i + 1
     Assert(lr_s.take(len(user.login_repr)) == lr_s)
 
     i = 0
     while i < len(timestamp):
-        # invariants-start
         Invariant(Acc(list_pred(timestamp), 1 / 2))
         Invariant(ts_s == ToSeq(timestamp))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(timestamp))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
-        Invariant(MustTerminate(len(timestamp) - i + 1))
-        # invariants-end
         result.append(timestamp[i])
         i = i + 1
     Assert(ts_s.take(len(timestamp)) == ts_s)
-
     addr = user.address
-    if addr is not None:
+    if addr is not None and len(addr) > 0 and addr[0] == 97:
         addr_s = ToSeq(addr)
         j = 0
         while j < len(addr):
-            # invariants-start
             Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
             Invariant(addr_s == ToSeq(addr))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(addr))
             Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
-            Invariant(MustTerminate(len(addr) - j + 1))
-            # invariants-end
             result.append(addr[j])
             j = j + 1
-        Assert(addr_s.take(len(addr)) == addr_s)
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,10 +58,6 @@
 
 class Account:
     def __init__(self) -> None:
-        # Terminates: field initialisation is straight-line work, but the four
-        # empty containers it builds each carry their own obligation, so this
-        # sits at the leaf level above them rather than at 1.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
         Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
         Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
@@ -83,9 +78,6 @@
     Requires(Acc(user.address, 1 / 2))
     Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
     Requires(Acc(list_pred(timestamp), 1 / 2))
-    # Strictly above the account constructor's own level (2), so a caller may
-    # build an account value before invoking this.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
@@ -109,8 +101,6 @@
         == effective_address(user.address))
     # post-conditions-end
     # impl-start
-    # Ghost snapshots of the component sequences, so the loop invariants read
-    # only locals (each field's fractional permission is held by the frame).
     pk_s = ToSeq(user.pk)
     pw_s = ToSeq(user.password)
     lr_s = ToSeq(user.login_repr)
@@ -119,73 +109,57 @@
     result = []  # type: List[int]
     i = 0
     while i < len(user.pk):
-        # invariants-start
         Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
         Invariant(pk_s == ToSeq(user.pk))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.pk))
         Invariant(ToSeq(result) == pk_s.take(i))
-        Invariant(MustTerminate(len(user.pk) - i + 1))
-        # invariants-end
         result.append(user.pk[i])
         i = i + 1
     Assert(pk_s.take(len(user.pk)) == pk_s)
 
     i = 0
     while i < len(user.password):
-        # invariants-start
         Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
         Invariant(pw_s == ToSeq(user.password))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.password))
         Invariant(ToSeq(result) == pk_s + pw_s.take(i))
-        Invariant(MustTerminate(len(user.password) - i + 1))
-        # invariants-end
         result.append(user.password[i])
         i = i + 1
     Assert(pw_s.take(len(user.password)) == pw_s)
 
     i = 0
     while i < len(user.login_repr):
-        # invariants-start
         Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
         Invariant(lr_s == ToSeq(user.login_repr))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(user.login_repr))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
-        Invariant(MustTerminate(len(user.login_repr) - i + 1))
-        # invariants-end
         result.append(user.login_repr[i])
         i = i + 1
     Assert(lr_s.take(len(user.login_repr)) == lr_s)
 
     i = 0
     while i < len(timestamp):
-        # invariants-start
         Invariant(Acc(list_pred(timestamp), 1 / 2))
         Invariant(ts_s == ToSeq(timestamp))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(timestamp))
         Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
-        Invariant(MustTerminate(len(timestamp) - i + 1))
-        # invariants-end
         result.append(timestamp[i])
         i = i + 1
     Assert(ts_s.take(len(timestamp)) == ts_s)
-
     addr = user.address
     if addr is not None:
         addr_s = ToSeq(addr)
         j = 0
         while j < len(addr):
-            # invariants-start
             Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
             Invariant(addr_s == ToSeq(addr))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(addr))
             Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
-            Invariant(MustTerminate(len(addr) - j + 1))
-            # invariants-end
             result.append(addr[j])
             j = j + 1
         Assert(addr_s.take(len(addr)) == addr_s)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The single-use credential-reset token for an account is derived from a
  fingerprint of the account state that must change whenever the account is
  altered in a way that should retire any outstanding token. The fingerprint
  is the concatenation, in a set order, of:

    1. the account's primary key,
    2. the stored password verifier,
    3. the truncated last-sign-in instant,
    4. the issuing timestamp, and
    5. the account's contact-address value.

  The contact-address value participates in the fingerprint exactly like the
  other components: two accounts that agree on the first four components but
  differ in their contact address MUST produce different fingerprints, so a
  token minted before a contact-address change no longer matches the
  fingerprint computed afterwards. An account need not have a contact address;
  when the address is absent or empty it contributes the empty sequence (and an
  account with no address therefore fingerprints exactly as the historical
  four-component concatenation did).

The components are modelled as `List[int]` sequences of Unicode code points
(Nagini bans `str` indexing); the account is a minimal object exposing only the
five touched components, the contact address being an `Optional[List[int]]`
(absent ~ `None`). The pure sequence theory `PSeq[int]` carries the spec, the
fingerprint being the front-to-back concatenation of the five component
sequences.

No callee is axiomatized: the change is pure concatenation/structure logic over
the account's own fields, modelled deeply. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def effective_address(addr: Optional[List[int]]) -> PSeq[int]:
    """The contact-address contribution to the fingerprint: the address itself
    when present and non-empty, otherwise the empty sequence (an absent or
    empty address contributes nothing)."""
    Requires(Implies(addr is not None, Acc(list_pred(addr), 1 / 4)))
    if addr is None:
        return PSeq(0).take(0)
    if len(addr) == 0:
        return PSeq(0).take(0)
    return ToSeq(addr)
# pure-end


class Account:
    def __init__(self) -> None:
        Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
        Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
        Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
        Ensures(Acc(self.address) and self.address is None)
        self.pk = []  # type: List[int]
        self.password = []  # type: List[int]
        self.login_repr = []  # type: List[int]
        self.address = None  # type: Optional[List[int]]


def make_hash_value(user: Account, timestamp: List[int]) -> List[int]:
    # pre-conditions-start
    # All read-only inputs at fractional permission (directive 5): the
    # fingerprint computation mutates nothing it is given.
    Requires(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
    Requires(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
    Requires(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
    Requires(Acc(user.address, 1 / 2))
    Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
    Requires(Acc(list_pred(timestamp), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
    Ensures(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
    Ensures(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
    Ensures(Acc(user.address, 1 / 2))
    Ensures(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
    Ensures(Acc(list_pred(timestamp), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The fingerprint is the set-order concatenation of the five components,
    # the contact address last. Because the address contributes its own
    # sequence, two accounts agreeing on the first four components but differing
    # in contact address produce different fingerprints.
    Ensures(ToSeq(Result()) ==
            ToSeq(user.pk) + ToSeq(user.password) + ToSeq(user.login_repr) +
            ToSeq(timestamp) + effective_address(user.address))
    # The contact address contributes faithfully as the trailing segment: what
    # follows the four leading components is exactly the resolved contact address.
    Ensures(ToSeq(Result()).drop(
        len(user.pk) + len(user.password) + len(user.login_repr) + len(timestamp))
        == effective_address(user.address))
    # post-conditions-end
    # impl-start
    # Ghost snapshots of the component sequences, so the loop invariants read
    # only locals (each field's fractional permission is held by the frame).
    pk_s = ToSeq(user.pk)
    pw_s = ToSeq(user.password)
    lr_s = ToSeq(user.login_repr)
    ts_s = ToSeq(timestamp)

    result = []  # type: List[int]
    i = 0
    while i < len(user.pk):
        # invariants-start
        Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
        Invariant(pk_s == ToSeq(user.pk))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.pk))
        Invariant(ToSeq(result) == pk_s.take(i))
        # invariants-end
        result.append(user.pk[i])
        i = i + 1
    Assert(pk_s.take(len(user.pk)) == pk_s)

    i = 0
    while i < len(user.password):
        # invariants-start
        Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
        Invariant(pw_s == ToSeq(user.password))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.password))
        Invariant(ToSeq(result) == pk_s + pw_s.take(i))
        # invariants-end
        result.append(user.password[i])
        i = i + 1
    Assert(pw_s.take(len(user.password)) == pw_s)

    i = 0
    while i < len(user.login_repr):
        # invariants-start
        Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
        Invariant(lr_s == ToSeq(user.login_repr))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.login_repr))
        Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
        # invariants-end
        result.append(user.login_repr[i])
        i = i + 1
    Assert(lr_s.take(len(user.login_repr)) == lr_s)

    i = 0
    while i < len(timestamp):
        # invariants-start
        Invariant(Acc(list_pred(timestamp), 1 / 2))
        Invariant(ts_s == ToSeq(timestamp))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(timestamp))
        Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
        # invariants-end
        result.append(timestamp[i])
        i = i + 1
    Assert(ts_s.take(len(timestamp)) == ts_s)

    addr = user.address
    if addr is not None:
        addr_s = ToSeq(addr)
        j = 0
        while j < len(addr):
            # invariants-start
            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
            Invariant(addr_s == ToSeq(addr))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(addr))
            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
            # invariants-end
            result.append(addr[j])
            j = j + 1
        Assert(addr_s.take(len(addr)) == addr_s)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-13551 (nagini), focused on the A-legs + model<->patch correspondence (R/I legs covered by G-CONF). PY=python; docker via `docker` (harness uses it internally).

SPEC SHAPE: make_hash_value's postcondition PINS ToSeq(Result()) EXACTLY to ToSeq(pk)+ToSeq(password)+ToSeq(login_repr)+ToSeq(timestamp)+effective_address(user.address), plus a redundant trailing-segment clause ToSeq(Result()).drop(prefix_len)==effective_address(user.address) and Acc(list_pred(Result())). This is a fully-functional (value-determining) postcondition, so any verifying impl produces the exact gold sequence -> behaviorally equal to gold by construction.

### ATTACKS (8 total, all same-spec exit0 confirmed; weakness run concurrently in 3 batches, <=3 JVM+Z3 each):
- atk_1 (PREPATCH bug: four-component concat, omits email): `python -m swebench_unified.adversary weakness nagini django__django-13551 .../atk_1.py` -> NOT-A-COUNTEREXAMPLE (exit 2, verification failed). PREPATCH REPRODUCED: spec rejects the email-omitting body.
- atk_2 (control-flow / order swap: timestamp appended before login_repr) -> exit 2, rejected.
- atk_3 (boundary/off-by-one: address loop starts j=1, drops first email char) -> exit 2, rejected.
- atk_4 (control-flow-effect: early return after password loop, drops login_repr+timestamp+address) -> exit 2, rejected.
- atk_5 (boundary: duplicates addr[0] after the address loop) -> exit 2, rejected.
- atk_6 (ungrounded/echo-empty: returns only pk) -> exit 2, rejected.
- atk_7 (partial-domain: appends address only when non-empty AND addr[0]==97('a'), else drops it) -> exit 2, rejected.
- atk_8 (ECHO: gold-equivalent impl, identical logic to model.py) -> CANDIDATE-COUNTEREXAMPLE (exit 0, shares spec AND verifies, 19.5s).

MANDATORY RESOLVE ON CANDIDATE: atk_8 produces exactly the 5-component concatenation with email last, so its faithful refined patch is the gold patch. Materialized at atk_8_faithful_patch.diff (= benchmark patch.diff). Ran the OFFICIAL harness: swebench_unified.harness.run_resolve('django__django-13551', <gold patch>, timeout=3600) -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the verifying candidate's faithful patch DOES resolve => NOT a weakness (per 2026-08-06 echo-attack policy: a resolving echo is not spec-too-weak).

POSITIVE CONTROL: model.py (pos_control.py) -> weakness exit 0 (verifies).

A-LEG AUDIT (refinement.md): The single genuinely-changed op (folding email into the fingerprint) is modeled DEEPLY as an A-reference (step A4): effective_address + trailing concatenation, NOT a consumed @ContractOnly axiom (axioms region empty). No kind-3 step; every leg is R / A-reference / I. G-AX correspondence check: ran axiom_check.py -> exit 0, 'deep model (effective_address + derived_value) == real _make_hash_value derivation on 10 boundary + 20000 fuzz inputs; email-change discriminator holds'. It faithfully reconstructs get_email_field_name (EMAIL_FIELD-or-'email') + getattr(user, field, '') or '' + the f-string, and asserts (a) deep model == real, (b) trailing segment == resolved email on the REAL output (no double-mask), (c) email-change discriminator. A-reference correspondence HOLDS.

VERDICT: SOUND. >=5 distinct wrong impls (7 non-echo) all rejected by the tight functional postcondition; prepatch reproduced; the lone verifying candidate is a gold-equivalent echo whose faithful (gold) patch RESOLVES under run_resolve; A-reference validated by G-AX. No verify-but-wrong impl found; verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

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

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The single-use credential-reset token for an account is derived from a
  fingerprint of the account state that must change whenever the account is
  altered in a way that should retire any outstanding token. The fingerprint
  is the concatenation, in a set order, of:

    1. the account's primary key,
    2. the stored password verifier,
    3. the truncated last-sign-in instant,
    4. the issuing timestamp, and
    5. the account's contact-address value.

  The contact-address value participates in the fingerprint exactly like the
  other components: two accounts that agree on the first four components but
  differ in their contact address MUST produce different fingerprints, so a
  token minted before a contact-address change no longer matches the
  fingerprint computed afterwards. An account need not have a contact address;
  when the address is absent or empty it contributes the empty sequence (and an
  account with no address therefore fingerprints exactly as the historical
  four-component concatenation did).

The components are modelled as `List[int]` sequences of Unicode code points
(Nagini bans `str` indexing); the account is a minimal object exposing only the
five touched components, the contact address being an `Optional[List[int]]`
(absent ~ `None`). The pure sequence theory `PSeq[int]` carries the spec, the
fingerprint being the front-to-back concatenation of the five component
sequences.

No callee is axiomatized: the change is pure concatenation/structure logic over
the account's own fields, modelled deeply. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def effective_address(addr: Optional[List[int]]) -> PSeq[int]:
    """The contact-address contribution to the fingerprint: the address itself
    when present and non-empty, otherwise the empty sequence (an absent or
    empty address contributes nothing)."""
    Requires(Implies(addr is not None, Acc(list_pred(addr), 1 / 4)))
    if addr is None:
        return PSeq(0).take(0)
    if len(addr) == 0:
        return PSeq(0).take(0)
    return ToSeq(addr)
# pure-end


class Account:
    def __init__(self) -> None:
        Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
        Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
        Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
        Ensures(Acc(self.address) and self.address is None)
        self.pk = []  # type: List[int]
        self.password = []  # type: List[int]
        self.login_repr = []  # type: List[int]
        self.address = None  # type: Optional[List[int]]


def make_hash_value(user: Account, timestamp: List[int]) -> List[int]:
    # pre-conditions-start
    # All read-only inputs at fractional permission (directive 5): the
    # fingerprint computation mutates nothing it is given.
    Requires(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
    Requires(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
    Requires(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
    Requires(Acc(user.address, 1 / 2))
    Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
    Requires(Acc(list_pred(timestamp), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
    Ensures(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
    Ensures(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
    Ensures(Acc(user.address, 1 / 2))
    Ensures(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
    Ensures(Acc(list_pred(timestamp), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The fingerprint is the set-order concatenation of the five components,
    # the contact address last. Because the address contributes its own
    # sequence, two accounts agreeing on the first four components but differing
    # in contact address produce different fingerprints.
    Ensures(ToSeq(Result()) ==
            ToSeq(user.pk) + ToSeq(user.password) + ToSeq(user.login_repr) +
            ToSeq(timestamp) + effective_address(user.address))
    # The contact address contributes faithfully as the trailing segment: what
    # follows the four leading components is exactly the resolved contact address.
    Ensures(ToSeq(Result()).drop(
        len(user.pk) + len(user.password) + len(user.login_repr) + len(timestamp))
        == effective_address(user.address))
    # post-conditions-end
    # impl-start
    # Ghost snapshots of the component sequences, so the loop invariants read
    # only locals (each field's fractional permission is held by the frame).
    pk_s = ToSeq(user.pk)
    pw_s = ToSeq(user.password)
    lr_s = ToSeq(user.login_repr)
    ts_s = ToSeq(timestamp)

    result = []  # type: List[int]
    i = 0
    while i < len(user.pk):
        # invariants-start
        Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
        Invariant(pk_s == ToSeq(user.pk))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.pk))
        Invariant(ToSeq(result) == pk_s.take(i))
        # invariants-end
        result.append(user.pk[i])
        i = i + 1
    Assert(pk_s.take(len(user.pk)) == pk_s)

    i = 0
    while i < len(user.password):
        # invariants-start
        Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
        Invariant(pw_s == ToSeq(user.password))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.password))
        Invariant(ToSeq(result) == pk_s + pw_s.take(i))
        # invariants-end
        result.append(user.password[i])
        i = i + 1
    Assert(pw_s.take(len(user.password)) == pw_s)

    i = 0
    while i < len(user.login_repr):
        # invariants-start
        Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
        Invariant(lr_s == ToSeq(user.login_repr))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.login_repr))
        Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
        # invariants-end
        result.append(user.login_repr[i])
        i = i + 1
    Assert(lr_s.take(len(user.login_repr)) == lr_s)

    i = 0
    while i < len(timestamp):
        # invariants-start
        Invariant(Acc(list_pred(timestamp), 1 / 2))
        Invariant(ts_s == ToSeq(timestamp))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(timestamp))
        Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
        # invariants-end
        result.append(timestamp[i])
        i = i + 1
    Assert(ts_s.take(len(timestamp)) == ts_s)

    addr = user.address
    if addr is not None:
        addr_s = ToSeq(addr)
        j = 0
        while j < len(addr):
            # invariants-start
            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
            Invariant(addr_s == ToSeq(addr))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(addr))
            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
            # invariants-end
            result.append(addr[j])
            j = j + 1
        Assert(addr_s.take(len(addr)) == addr_s)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-13551 (nagini), focused on the A-legs + model<->patch correspondence (R/I legs covered by G-CONF). PY=python; docker via `docker` (harness uses it internally).

SPEC SHAPE: make_hash_value's postcondition PINS ToSeq(Result()) EXACTLY to ToSeq(pk)+ToSeq(password)+ToSeq(login_repr)+ToSeq(timestamp)+effective_address(user.address), plus a redundant trailing-segment clause ToSeq(Result()).drop(prefix_len)==effective_address(user.address) and Acc(list_pred(Result())). This is a fully-functional (value-determining) postcondition, so any verifying impl produces the exact gold sequence -> behaviorally equal to gold by construction.

### ATTACKS (8 total, all same-spec exit0 confirmed; weakness run concurrently in 3 batches, <=3 JVM+Z3 each):
- atk_1 (PREPATCH bug: four-component concat, omits email): `python -m swebench_unified.adversary weakness nagini django__django-13551 .../atk_1.py` -> NOT-A-COUNTEREXAMPLE (exit 2, verification failed). PREPATCH REPRODUCED: spec rejects the email-omitting body.
- atk_2 (control-flow / order swap: timestamp appended before login_repr) -> exit 2, rejected.
- atk_3 (boundary/off-by-one: address loop starts j=1, drops first email char) -> exit 2, rejected.
- atk_4 (control-flow-effect: early return after password loop, drops login_repr+timestamp+address) -> exit 2, rejected.
- atk_5 (boundary: duplicates addr[0] after the address loop) -> exit 2, rejected.
- atk_6 (ungrounded/echo-empty: returns only pk) -> exit 2, rejected.
- atk_7 (partial-domain: appends address only when non-empty AND addr[0]==97('a'), else drops it) -> exit 2, rejected.
- atk_8 (ECHO: gold-equivalent impl, identical logic to model.py) -> CANDIDATE-COUNTEREXAMPLE (exit 0, shares spec AND verifies, 19.5s).

MANDATORY RESOLVE ON CANDIDATE: atk_8 produces exactly the 5-component concatenation with email last, so its faithful refined patch is the gold patch. Materialized at atk_8_faithful_patch.diff (= benchmark patch.diff). Ran the OFFICIAL harness: swebench_unified.harness.run_resolve('django__django-13551', <gold patch>, timeout=3600) -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the verifying candidate's faithful patch DOES resolve => NOT a weakness (per 2026-08-06 echo-attack policy: a resolving echo is not spec-too-weak).

POSITIVE CONTROL: model.py (pos_control.py) -> weakness exit 0 (verifies).

A-LEG AUDIT (refinement.md): The single genuinely-changed op (folding email into the fingerprint) is modeled DEEPLY as an A-reference (step A4): effective_address + trailing concatenation, NOT a consumed @ContractOnly axiom (axioms region empty). No kind-3 step; every leg is R / A-reference / I. G-AX correspondence check: ran axiom_check.py -> exit 0, 'deep model (effective_address + derived_value) == real _make_hash_value derivation on 10 boundary + 20000 fuzz inputs; email-change discriminator holds'. It faithfully reconstructs get_email_field_name (EMAIL_FIELD-or-'email') + getattr(user, field, '') or '' + the f-string, and asserts (a) deep model == real, (b) trailing segment == resolved email on the REAL output (no double-mask), (c) email-change discriminator. A-reference correspondence HOLDS.

VERDICT: SOUND. >=5 distinct wrong impls (7 non-echo) all rejected by the tight functional postcondition; prepatch reproduced; the lone verifying candidate is a gold-equivalent echo whose faithful (gold) patch RESOLVES under run_resolve; A-reference validated by G-AX. No verify-but-wrong impl found; verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for django__django-13551 nagini bundle. The modeled function make_hash_value corresponds to PasswordResetTokenGenerator._make_hash_value (django/contrib/auth/tokens.py) at base_commit. The real gold body is `email = getattr(user, user.get_email_field_name(), '') or ''; return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'`. Both /tmp worktrees carry an identical _make_hash_value body (diffs are only surrounding line offsets), confirming the base body.

The model deeply encodes this: effective_address(addr) returns [] for None/empty else the address (exactly the `getattr(...,'') or ''` coercion of a falsy contact value to ''), and the postcondition ToSeq(Result()) == ToSeq(pk)+ToSeq(password)+ToSeq(login_repr)+ToSeq(timestamp)+effective_address(addr) — the in-order 5-component concatenation with email last. The unchanged prefix (str coercions + microsecond truncation) is legitimately abstracted as pre-rendered List[int] input sequences, since those operations are unchanged by the patch.

Evidence the spec is neither too strong nor drifting: (1) model.py VERIFIES under the pinned nagini verifier (14.57s, exit 0), so the postcondition is satisfiable/non-vacuous; (2) axiom_check.py G-AX passes on 10 boundary + 20000 fuzz inputs, exit 0, asserting deep model == real derivation at code-point level plus the email-change discriminator; (3) my own independent 200,000-input fuzz comparing the modeled concatenation semantics against a faithful recreation of the real getattr+f-string derivation (including None/''/missing-attr/renamed-EMAIL_FIELD cases) found 0 mismatches. The spec exactly matches real repo behavior on all tested inputs — no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region integrity confirmed: `adversary same-spec nagini django__django-13551 atk.py` -> SAME (exit 0), so the audited spec view is byte-identical with the bundle.

Comparison basis: the consumer spec view = model.py module docstring (lines 1-35) + the `effective_address` pure region + `Account` class + `make_hash_value` pre/post-conditions. Auditor-only artifacts refinement.md and mapping.md (which DO quote the gold hunk and name get_email_field_name/getattr/EMAIL_FIELD/the f-string) are NOT part of the solver's spec view and are excluded per G-LEAK scope. Comparison is against problem_statement only (hints excluded).

Public problem_statement discloses MORE, not less: it names the exact patched symbol ('add the user's email address into PasswordResetTokenGenerator._make_hash_value()') and the absent-email edge ('Nothing forces a user to even have an email as per AbstractBaseUser').

Spec view describes the same behaviour at a MORE ABSTRACT altitude: a 'credential-reset token' fingerprint = ordered concatenation of five components with the 'contact-address' last, empty when absent/None/empty. It uses neutral identifiers (Account, address, login_repr, effective_address), never quotes the diff, and never names get_email_field_name / getattr(..., '') or '' / EMAIL_FIELD / the f-string. The first four components (pk, password, last-sign-in, timestamp) are the pre-existing public source structure at base_commit, not part of the gold edit. The only edit-specific content — 'the contact address is a new fifth trailing component that changes the fingerprint' — is exactly what problem_statement already states (add the email; must invalidate the old token). Placing it last is the natural append and reveals no information beyond the public statement.

No spec-view line leaks the gold edit beyond problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
