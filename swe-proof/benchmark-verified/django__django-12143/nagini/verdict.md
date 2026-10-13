# P2 adversarial audit — django__django-12143

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
     Requires(0 <= off and off + len(lit) <= len(key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -124,7 +122,6 @@
         Invariant(0 <= off and off + m <= len(key))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
         Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -143,7 +140,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(0 <= lo and lo <= hi and hi <= len(key))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -158,7 +154,6 @@
         Invariant(Acc(list_pred(key), 1 / 4))
         Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
         Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
-        Invariant(MustTerminate(i - lo + 1))
         # invariants-end
         c = key[i - 1]
         Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
@@ -177,7 +172,6 @@
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(pkname), 1 / 2))
     Requires(Acc(list_pred(key), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -193,25 +187,16 @@
     n = len(key)
     d = n - np - nk - 2
     if d < 1:
-        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
         return False
-    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
-    Assert(n == np + 2 + d + nk)
-    Assert(0 <= np and np < n)
-    Assert(np + 1 + d <= n and np + 1 + d < n)
-    Assert(np + 2 + d + nk == n)
     ok_label = match_literal(key, 0, prefix)
-    Assert(len(key) == n)
-    Assert(ToSeq(key).drop(0) == ToSeq(key))
-    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
-    Assert(0 <= np and np < len(key))
+    # PRE-PATCH: a '$' at the end of the label acts as an end anchor, so the
+    # leading region is rejected when the key continues past it.
+    label_ends_in_anchor = (np >= 1 and prefix[np - 1] == 36)
+    if label_ends_in_anchor:
+        ok_label = False
     hyphen1 = (key[np] == 45)
     ok_digits = run_is_digits(key, np + 1, np + 1 + d)
-    Assert(len(key) == n)
-    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
     hyphen2 = (key[np + 1 + d] == 45)
     ok_name = match_literal(key, np + 2 + d, pkname)
-    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
-           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
     return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
     Requires(0 <= off and off + len(lit) <= len(key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -124,7 +122,6 @@
         Invariant(0 <= off and off + m <= len(key))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
         Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -143,7 +140,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(0 <= lo and lo <= hi and hi <= len(key))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -158,7 +154,6 @@
         Invariant(Acc(list_pred(key), 1 / 4))
         Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
         Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
-        Invariant(MustTerminate(i - lo + 1))
         # invariants-end
         c = key[i - 1]
         Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
@@ -177,7 +172,6 @@
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(pkname), 1 / 2))
     Requires(Acc(list_pred(key), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -193,25 +187,11 @@
     n = len(key)
     d = n - np - nk - 2
     if d < 1:
-        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
         return False
-    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
-    Assert(n == np + 2 + d + nk)
-    Assert(0 <= np and np < n)
-    Assert(np + 1 + d <= n and np + 1 + d < n)
-    Assert(np + 2 + d + nk == n)
     ok_label = match_literal(key, 0, prefix)
-    Assert(len(key) == n)
-    Assert(ToSeq(key).drop(0) == ToSeq(key))
-    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
-    Assert(0 <= np and np < len(key))
     hyphen1 = (key[np] == 45)
     ok_digits = run_is_digits(key, np + 1, np + 1 + d)
-    Assert(len(key) == n)
-    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
     hyphen2 = (key[np + 1 + d] == 45)
-    ok_name = match_literal(key, np + 2 + d, pkname)
-    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
-           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
-    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
+    # WRONG: ignore the pk-field-name region entirely.
+    return ok_label and hyphen1 and ok_digits and hyphen2
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
     Requires(0 <= off and off + len(lit) <= len(key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -124,7 +122,6 @@
         Invariant(0 <= off and off + m <= len(key))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
         Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -143,7 +140,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(0 <= lo and lo <= hi and hi <= len(key))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -158,7 +154,6 @@
         Invariant(Acc(list_pred(key), 1 / 4))
         Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
         Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
-        Invariant(MustTerminate(i - lo + 1))
         # invariants-end
         c = key[i - 1]
         Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
@@ -177,7 +172,6 @@
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(pkname), 1 / 2))
     Requires(Acc(list_pred(key), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -192,26 +186,19 @@
     nk = len(pkname)
     n = len(key)
     d = n - np - nk - 2
-    if d < 1:
-        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
+    # WRONG: accept an empty digit run (d == 0) as well.
+    if d < 0:
         return False
-    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
-    Assert(n == np + 2 + d + nk)
-    Assert(0 <= np and np < n)
-    Assert(np + 1 + d <= n and np + 1 + d < n)
-    Assert(np + 2 + d + nk == n)
+    if d == 0:
+        # no digits: still claim recognised if label/hyphen/name line up
+        ok_label = match_literal(key, 0, prefix)
+        hyphen1 = (key[np] == 45)
+        ok_name = match_literal(key, np + 1, pkname)
+        return ok_label and hyphen1 and ok_name
     ok_label = match_literal(key, 0, prefix)
-    Assert(len(key) == n)
-    Assert(ToSeq(key).drop(0) == ToSeq(key))
-    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
-    Assert(0 <= np and np < len(key))
     hyphen1 = (key[np] == 45)
     ok_digits = run_is_digits(key, np + 1, np + 1 + d)
-    Assert(len(key) == n)
-    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
     hyphen2 = (key[np + 1 + d] == 45)
     ok_name = match_literal(key, np + 2 + d, pkname)
-    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
-           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
     return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
     Requires(0 <= off and off + len(lit) <= len(key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -124,7 +122,6 @@
         Invariant(0 <= off and off + m <= len(key))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
         Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -143,7 +140,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(0 <= lo and lo <= hi and hi <= len(key))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -158,7 +154,6 @@
         Invariant(Acc(list_pred(key), 1 / 4))
         Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
         Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
-        Invariant(MustTerminate(i - lo + 1))
         # invariants-end
         c = key[i - 1]
         Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
@@ -177,7 +172,6 @@
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(pkname), 1 / 2))
     Requires(Acc(list_pred(key), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -193,25 +187,7 @@
     n = len(key)
     d = n - np - nk - 2
     if d < 1:
-        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
         return False
-    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
-    Assert(n == np + 2 + d + nk)
-    Assert(0 <= np and np < n)
-    Assert(np + 1 + d <= n and np + 1 + d < n)
-    Assert(np + 2 + d + nk == n)
-    ok_label = match_literal(key, 0, prefix)
-    Assert(len(key) == n)
-    Assert(ToSeq(key).drop(0) == ToSeq(key))
-    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
-    Assert(0 <= np and np < len(key))
-    hyphen1 = (key[np] == 45)
-    ok_digits = run_is_digits(key, np + 1, np + 1 + d)
-    Assert(len(key) == n)
-    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
-    hyphen2 = (key[np + 1 + d] == 45)
-    ok_name = match_literal(key, np + 2 + d, pkname)
-    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
-           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
-    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
+    # WRONG: accept any key whose length admits a digit run.
+    return True
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
     Requires(0 <= off and off + len(lit) <= len(key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -124,7 +122,6 @@
         Invariant(0 <= off and off + m <= len(key))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
         Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -143,7 +140,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(0 <= lo and lo <= hi and hi <= len(key))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -158,7 +154,6 @@
         Invariant(Acc(list_pred(key), 1 / 4))
         Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
         Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
-        Invariant(MustTerminate(i - lo + 1))
         # invariants-end
         c = key[i - 1]
         Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
@@ -177,7 +172,6 @@
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(pkname), 1 / 2))
     Requires(Acc(list_pred(key), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -193,25 +187,11 @@
     n = len(key)
     d = n - np - nk - 2
     if d < 1:
-        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
         return False
-    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
-    Assert(n == np + 2 + d + nk)
-    Assert(0 <= np and np < n)
-    Assert(np + 1 + d <= n and np + 1 + d < n)
-    Assert(np + 2 + d + nk == n)
     ok_label = match_literal(key, 0, prefix)
-    Assert(len(key) == n)
-    Assert(ToSeq(key).drop(0) == ToSeq(key))
-    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
-    Assert(0 <= np and np < len(key))
     hyphen1 = (key[np] == 45)
-    ok_digits = run_is_digits(key, np + 1, np + 1 + d)
-    Assert(len(key) == n)
-    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
+    # WRONG: do not require the middle region to be digits.
     hyphen2 = (key[np + 1 + d] == 45)
     ok_name = match_literal(key, np + 2 + d, pkname)
-    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
-           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
-    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
+    return ok_label and hyphen1 and hyphen2 and ok_name
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
     Requires(0 <= off and off + len(lit) <= len(key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -124,7 +122,6 @@
         Invariant(0 <= off and off + m <= len(key))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
         Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -143,7 +140,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(0 <= lo and lo <= hi and hi <= len(key))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -158,7 +154,6 @@
         Invariant(Acc(list_pred(key), 1 / 4))
         Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
         Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
-        Invariant(MustTerminate(i - lo + 1))
         # invariants-end
         c = key[i - 1]
         Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
@@ -177,7 +172,6 @@
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(pkname), 1 / 2))
     Requires(Acc(list_pred(key), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -193,25 +187,11 @@
     n = len(key)
     d = n - np - nk - 2
     if d < 1:
-        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
         return False
-    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
-    Assert(n == np + 2 + d + nk)
-    Assert(0 <= np and np < n)
-    Assert(np + 1 + d <= n and np + 1 + d < n)
-    Assert(np + 2 + d + nk == n)
     ok_label = match_literal(key, 0, prefix)
-    Assert(len(key) == n)
-    Assert(ToSeq(key).drop(0) == ToSeq(key))
-    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
-    Assert(0 <= np and np < len(key))
-    hyphen1 = (key[np] == 45)
+    # WRONG: omit the first-hyphen requirement.
     ok_digits = run_is_digits(key, np + 1, np + 1 + d)
-    Assert(len(key) == n)
-    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
     hyphen2 = (key[np + 1 + d] == 45)
     ok_name = match_literal(key, np + 2 + d, pkname)
-    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
-           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
-    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
+    return ok_label and ok_digits and hyphen2 and ok_name
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
     Requires(0 <= off and off + len(lit) <= len(key))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -124,7 +122,6 @@
         Invariant(0 <= off and off + m <= len(key))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
         Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -143,7 +140,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(key), 1 / 4))
     Requires(0 <= lo and lo <= hi and hi <= len(key))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(key), 1 / 4))
@@ -158,7 +154,6 @@
         Invariant(Acc(list_pred(key), 1 / 4))
         Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
         Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
-        Invariant(MustTerminate(i - lo + 1))
         # invariants-end
         c = key[i - 1]
         Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
@@ -177,7 +172,6 @@
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(pkname), 1 / 2))
     Requires(Acc(list_pred(key), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -188,30 +182,6 @@
     Ensures(Result() == recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
     # post-conditions-end
     # impl-start
-    np = len(prefix)
-    nk = len(pkname)
-    n = len(key)
-    d = n - np - nk - 2
-    if d < 1:
-        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
-        return False
-    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
-    Assert(n == np + 2 + d + nk)
-    Assert(0 <= np and np < n)
-    Assert(np + 1 + d <= n and np + 1 + d < n)
-    Assert(np + 2 + d + nk == n)
-    ok_label = match_literal(key, 0, prefix)
-    Assert(len(key) == n)
-    Assert(ToSeq(key).drop(0) == ToSeq(key))
-    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
-    Assert(0 <= np and np < len(key))
-    hyphen1 = (key[np] == 45)
-    ok_digits = run_is_digits(key, np + 1, np + 1 + d)
-    Assert(len(key) == n)
-    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
-    hyphen2 = (key[np + 1 + d] == 45)
-    ok_name = match_literal(key, np + 2 + d, pkname)
-    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
-           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
-    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
+    # ECHO: return the deep model directly (correct, different shape).
+    return recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12143.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When selecting, from a body of submitted form keys, those keys that carry an
  edited row's primary key, a key is RECOGNISED exactly when it decomposes,
  reading it as a sequence of Unicode code points, as

      <group label>  '-'  <one or more decimal digits>  '-'  <pk field name>

  and NOTHING ELSE — the whole key, from its first code point to its last, is
  consumed by that decomposition. The group label is matched LITERALLY: every
  code point of the candidate key's leading region must equal the corresponding
  code point of the label, with no code point of the label given any special
  interpretation. In particular a label that happens to contain code points
  such as U+0024 ('$'), U+002E ('.') or U+002B ('+') is still matched
  character-for-character, so a key whose leading region is exactly that label
  followed by the '-<digits>-<field name>' tail IS recognised, and a key that
  merely shares a proper textual fragment of the label is NOT.

  The digit run between the two hyphens must be non-empty and consist solely of
  the decimal-digit code points U+0030..U+0039; the trailing region after the
  second hyphen must equal the primary-key field name exactly, ending the key.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification. The
recognition decision for one candidate key is modelled deeply as a verified
structural decomposition; the literal recognition it pins is validated == the
real compiled-pattern match out-of-band by axiom_check.py (G-AX), not consumed
as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the recognition decision is the changed behaviour and is
#  modelled DEEPLY below. The real compiled-pattern match is an A-reference,
#  validated == the deep model by axiom_check.py / G-AX, never consumed.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """A single code point is a decimal digit U+0030..U+0039."""
    return 48 <= c and c <= 57


@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL match of `lit` against the head of `s`. Total: if `s` is
    shorter than `lit` there can be no such match, so the result is False.
    Front-recursive (over both sequences) so a single unfold is available per
    loop step."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """Every code point of `s` is a decimal digit. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return True
    return is_digit(s[0]) and all_digits(s.drop(1))


@Pure
def recognises(prefix: PSeq[int], pkname: PSeq[int], key: PSeq[int]) -> bool:
    """True iff `key` decomposes EXACTLY as

        prefix ++ '-' ++ <one or more decimal digits> ++ '-' ++ pkname

    consuming the whole key, with `prefix` matched literally (code point for
    code point). The digit-run length is forced by the three fixed-length
    regions, so the decomposition is unique when it exists.

    The label region is `key[:np]`, the digit run `key[np+1 : np+1+d]`, and the
    field-name region `key[np+2+d:]`; the two hyphens sit at `np` and `np+1+d`."""
    np = len(prefix)
    nk = len(pkname)
    n = len(key)
    d = n - np - nk - 2          # length of the digit run if a match exists
    return (
        d >= 1
        and prefix_eq(key, prefix)                            # literal label
        and key[np] == 45                                     # first '-'
        and all_digits(key.take(np + 1 + d).drop(np + 1))     # the digit run
        and key[np + 1 + d] == 45                             # second '-'
        and prefix_eq(key.drop(np + 2 + d), pkname)           # field name, to end
    )
# pure-end

def match_literal(key: List[int], off: int, lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    Requires(0 <= off and off + len(lit) <= len(key))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL match of `lit` against `key[off:]`.
    Ensures(Result() == prefix_eq(ToSeq(key).drop(off), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    m = len(lit)
    ok = True
    i = m
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= m and m == len(lit))
        Invariant(0 <= off and off + m <= len(key))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
        Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
        # invariants-end
        Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(key).drop(off + i - 1).drop(1) == ToSeq(key).drop(off + i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if key[off + i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(key).drop(off + 0) == ToSeq(key).drop(off))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end


def run_is_digits(key: List[int], lo: int, hi: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 4))
    Requires(0 <= lo and lo <= hi and hi <= len(key))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 4))
    # Result is "every code point of key[lo:hi] is a decimal digit".
    Ensures(Result() == all_digits(ToSeq(key).take(hi).drop(lo)))
    # post-conditions-end
    # impl-start
    ok = True
    i = hi
    while i > lo:
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 4))
        Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
        Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
        # invariants-end
        c = key[i - 1]
        Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
        Assert(ToSeq(key).take(hi)[i - 1] == ToSeq(key)[i - 1])
        Assert(ToSeq(key).take(hi).drop(i - 1).drop(1) == ToSeq(key).take(hi).drop(i))
        if not (48 <= c and c <= 57):
            ok = False
        i = i - 1
    Assert(ToSeq(key).take(hi).drop(lo) == ToSeq(key).take(hi).drop(lo))
    return ok
    # impl-end


def is_edited_pk_key(prefix: List[int], pkname: List[int], key: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(prefix), 1 / 2))
    Requires(Acc(list_pred(pkname), 1 / 2))
    Requires(Acc(list_pred(key), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(pkname), 1 / 2))
    Ensures(Acc(list_pred(key), 1 / 2))
    # Recognised iff the key decomposes exactly as label-'-'-digits-'-'-name,
    # the label matched LITERALLY.
    Ensures(Result() == recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
    # post-conditions-end
    # impl-start
    np = len(prefix)
    nk = len(pkname)
    n = len(key)
    d = n - np - nk - 2
    if d < 1:
        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
        return False
    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
    Assert(n == np + 2 + d + nk)
    Assert(0 <= np and np < n)
    Assert(np + 1 + d <= n and np + 1 + d < n)
    Assert(np + 2 + d + nk == n)
    ok_label = match_literal(key, 0, prefix)
    Assert(len(key) == n)
    Assert(ToSeq(key).drop(0) == ToSeq(key))
    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
    Assert(0 <= np and np < len(key))
    hyphen1 = (key[np] == 45)
    ok_digits = run_is_digits(key, np + 1, np + 1 + d)
    Assert(len(key) == n)
    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
    hyphen2 = (key[np + 1 + d] == 45)
    ok_name = match_literal(key, np + 2 + d, pkname)
    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: is_edited_pk_key's top-level postcondition `Ensures(Result() == recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))` is UNCONDITIONAL (the only preconditions are Acc(list_pred,...) access permissions imposing no value constraints). `recognises` is a total @Pure function. Therefore any impl that verifies against this frozen spec must equal `recognises` on the ENTIRE input domain — the spec pins behaviour completely, leaving no room for a same-spec verifying wrong impl.

same-spec: all 7 attacks + positive_control returned SAME (byte-identical spec signature); only impl regions differ (diffs captured).

Positive control (correct model.py impl): `adversary verify nagini django__django-12143 positive_control.py` => VERIFIED in 14.0s (exit 0).

Attacks (`adversary weakness nagini django__django-12143 atk_N.py`):
- atk_1.py PREPATCH BUG (raw-prefix '$' end-anchor: label_ends_in_anchor forces ok_label=False when prefix[-1]==36): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). => spec SENSES the change / prepatch reproduced (G-DIFF).
- atk_2.py PARTIAL-DOMAIN (drop trailing pkname check): does not verify (exit 2).
- atk_3.py BOUNDARY off-by-one (accept empty digit run d==0): does not verify (exit 2).
- atk_4.py CONTROL-FLOW-EFFECT (return True whenever d>=1, skip all checks): does not verify (exit 2).
- atk_5.py INVERTED/dropped digit check (omit ok_digits): does not verify (exit 2).
- atk_6.py DROP first-hyphen check: does not verify (exit 2).
- atk_7.py UNGROUNDED-ORACLE ECHO (`return recognises(ToSeq(prefix),ToSeq(pkname),ToSeq(key))` directly): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies in 12.4s (exit 0). This is a correct-but-different-shape impl (echoes the pinned oracle), NOT a wrong impl.

MANDATORY RESOLVE for the one CANDIDATE (atk_7): its faithful refined repo patch is the re.escape fix (atk_7 computes exactly `recognises`, which the A-reference validates == the real re.escape-fixed .match). Materialized as gold_patch.diff and executed via swebench_unified.harness.run_resolve('django__django-12143', patch) => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. The verifying candidate's faithful patch RESOLVES, so no verify⇏correct witness exists.

A-LEG / DEEP-MODEL AUDIT (the focus): the sole trust point is A2 (A-reference) `recognises == real re.escape-fixed pattern .match` over the scoped POST-key domain.
- axiom_check.py (G-AX) executed => 'G-AX OK: deep model recognises == real re.escape-fixed pattern match over 60540 scoped boundary+fuzz inputs (0 mismatch); 30059 inputs discriminate fixed vs pre-fix (incl. the F2P prefix=form$ case)' (exit 0).
- INDEPENDENT differential (my own generator, not the bundle's): 612000 in-scope triples with adversarial hyphen/digit/metachar prefixes and digit-containing pknames (id, -a, 0, x, a-b) probing decomposition-ambiguity => 0 mismatches; F2P case recognises==fixed==True.
- Domain scoping (ASCII \d, no trailing newline) is legitimate: both properties are shared by pre- and post-fix code and by every real submitted HTTP form-field name; the gold fix changes ONLY prefix interpretation (literal via re.escape), exactly what recognises pins. F2P test admin_changelist.tests test_get_list_editable_queryset_with_regex_chars_in_prefix uses prefix='form$', key 'form$-0-uuid' — squarely in scope and correctly modeled.

REFINEMENT.md LEG AUDIT: R1 (str<->List[int] type refinement) = R; A2 (recognises<->re.escape-fixed match) = A-reference validated by G-AX (correspondence to real callee CONFIRMED, no consumed axiom); R3 (single-key predicate<->unchanged POST comprehension filter) = R, corroborated by conformance_check.py driving the real ModelAdmin._get_edited_object_pks per-key. §B helpers (match_literal/run_is_digits) are proof-only scaffolding, no repo counterpart. §C: NO kind-3 leg — the one changed op (regex escape) is modeled deeply, never axiomatized; model.py axioms region is empty (no consumed @ContractOnly), consistent with the doc. Correspondence holds.

CONCLUSION: spec is total-pinning; 6 distinct wrong impls (prepatch + partial-domain + boundary + control-flow-effect + dropped-digit + dropped-hyphen) all REJECTED; the single verifying candidate is a correct echo whose materialized faithful patch RESOLVES under the official harness; A-reference correspondence robustly holds. No verify⇏correct witness. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12143.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When selecting, from a body of submitted form keys, those keys that carry an
  edited row's primary key, a key is RECOGNISED exactly when it decomposes,
  reading it as a sequence of Unicode code points, as

      <group label>  '-'  <one or more decimal digits>  '-'  <pk field name>

  and NOTHING ELSE — the whole key, from its first code point to its last, is
  consumed by that decomposition. The group label is matched LITERALLY: every
  code point of the candidate key's leading region must equal the corresponding
  code point of the label, with no code point of the label given any special
  interpretation. In particular a label that happens to contain code points
  such as U+0024 ('$'), U+002E ('.') or U+002B ('+') is still matched
  character-for-character, so a key whose leading region is exactly that label
  followed by the '-<digits>-<field name>' tail IS recognised, and a key that
  merely shares a proper textual fragment of the label is NOT.

  The digit run between the two hyphens must be non-empty and consist solely of
  the decimal-digit code points U+0030..U+0039; the trailing region after the
  second hyphen must equal the primary-key field name exactly, ending the key.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification. The
recognition decision for one candidate key is modelled deeply as a verified
structural decomposition; the literal recognition it pins is validated == the
real compiled-pattern match out-of-band by axiom_check.py (G-AX), not consumed
as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the recognition decision is the changed behaviour and is
#  modelled DEEPLY below. The real compiled-pattern match is an A-reference,
#  validated == the deep model by axiom_check.py / G-AX, never consumed.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """A single code point is a decimal digit U+0030..U+0039."""
    return 48 <= c and c <= 57


@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL match of `lit` against the head of `s`. Total: if `s` is
    shorter than `lit` there can be no such match, so the result is False.
    Front-recursive (over both sequences) so a single unfold is available per
    loop step."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """Every code point of `s` is a decimal digit. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return True
    return is_digit(s[0]) and all_digits(s.drop(1))


@Pure
def recognises(prefix: PSeq[int], pkname: PSeq[int], key: PSeq[int]) -> bool:
    """True iff `key` decomposes EXACTLY as

        prefix ++ '-' ++ <one or more decimal digits> ++ '-' ++ pkname

    consuming the whole key, with `prefix` matched literally (code point for
    code point). The digit-run length is forced by the three fixed-length
    regions, so the decomposition is unique when it exists.

    The label region is `key[:np]`, the digit run `key[np+1 : np+1+d]`, and the
    field-name region `key[np+2+d:]`; the two hyphens sit at `np` and `np+1+d`."""
    np = len(prefix)
    nk = len(pkname)
    n = len(key)
    d = n - np - nk - 2          # length of the digit run if a match exists
    return (
        d >= 1
        and prefix_eq(key, prefix)                            # literal label
        and key[np] == 45                                     # first '-'
        and all_digits(key.take(np + 1 + d).drop(np + 1))     # the digit run
        and key[np + 1 + d] == 45                             # second '-'
        and prefix_eq(key.drop(np + 2 + d), pkname)           # field name, to end
    )
# pure-end

def match_literal(key: List[int], off: int, lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    Requires(0 <= off and off + len(lit) <= len(key))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL match of `lit` against `key[off:]`.
    Ensures(Result() == prefix_eq(ToSeq(key).drop(off), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    m = len(lit)
    ok = True
    i = m
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= m and m == len(lit))
        Invariant(0 <= off and off + m <= len(key))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
        Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
        # invariants-end
        Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(key).drop(off + i - 1).drop(1) == ToSeq(key).drop(off + i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if key[off + i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(key).drop(off + 0) == ToSeq(key).drop(off))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end


def run_is_digits(key: List[int], lo: int, hi: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 4))
    Requires(0 <= lo and lo <= hi and hi <= len(key))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 4))
    # Result is "every code point of key[lo:hi] is a decimal digit".
    Ensures(Result() == all_digits(ToSeq(key).take(hi).drop(lo)))
    # post-conditions-end
    # impl-start
    ok = True
    i = hi
    while i > lo:
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 4))
        Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
        Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
        # invariants-end
        c = key[i - 1]
        Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
        Assert(ToSeq(key).take(hi)[i - 1] == ToSeq(key)[i - 1])
        Assert(ToSeq(key).take(hi).drop(i - 1).drop(1) == ToSeq(key).take(hi).drop(i))
        if not (48 <= c and c <= 57):
            ok = False
        i = i - 1
    Assert(ToSeq(key).take(hi).drop(lo) == ToSeq(key).take(hi).drop(lo))
    return ok
    # impl-end


def is_edited_pk_key(prefix: List[int], pkname: List[int], key: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(prefix), 1 / 2))
    Requires(Acc(list_pred(pkname), 1 / 2))
    Requires(Acc(list_pred(key), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(pkname), 1 / 2))
    Ensures(Acc(list_pred(key), 1 / 2))
    # Recognised iff the key decomposes exactly as label-'-'-digits-'-'-name,
    # the label matched LITERALLY.
    Ensures(Result() == recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
    # post-conditions-end
    # impl-start
    np = len(prefix)
    nk = len(pkname)
    n = len(key)
    d = n - np - nk - 2
    if d < 1:
        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
        return False
    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
    Assert(n == np + 2 + d + nk)
    Assert(0 <= np and np < n)
    Assert(np + 1 + d <= n and np + 1 + d < n)
    Assert(np + 2 + d + nk == n)
    ok_label = match_literal(key, 0, prefix)
    Assert(len(key) == n)
    Assert(ToSeq(key).drop(0) == ToSeq(key))
    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
    Assert(0 <= np and np < len(key))
    hyphen1 = (key[np] == 45)
    ok_digits = run_is_digits(key, np + 1, np + 1 + d)
    Assert(len(key) == n)
    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
    hyphen2 = (key[np + 1 + d] == 45)
    ok_name = match_literal(key, np + 2 + d, pkname)
    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: is_edited_pk_key's top-level postcondition `Ensures(Result() == recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))` is UNCONDITIONAL (the only preconditions are Acc(list_pred,...) access permissions imposing no value constraints). `recognises` is a total @Pure function. Therefore any impl that verifies against this frozen spec must equal `recognises` on the ENTIRE input domain — the spec pins behaviour completely, leaving no room for a same-spec verifying wrong impl.

same-spec: all 7 attacks + positive_control returned SAME (byte-identical spec signature); only impl regions differ (diffs captured).

Positive control (correct model.py impl): `adversary verify nagini django__django-12143 positive_control.py` => VERIFIED in 14.0s (exit 0).

Attacks (`adversary weakness nagini django__django-12143 atk_N.py`):
- atk_1.py PREPATCH BUG (raw-prefix '$' end-anchor: label_ends_in_anchor forces ok_label=False when prefix[-1]==36): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). => spec SENSES the change / prepatch reproduced (G-DIFF).
- atk_2.py PARTIAL-DOMAIN (drop trailing pkname check): does not verify (exit 2).
- atk_3.py BOUNDARY off-by-one (accept empty digit run d==0): does not verify (exit 2).
- atk_4.py CONTROL-FLOW-EFFECT (return True whenever d>=1, skip all checks): does not verify (exit 2).
- atk_5.py INVERTED/dropped digit check (omit ok_digits): does not verify (exit 2).
- atk_6.py DROP first-hyphen check: does not verify (exit 2).
- atk_7.py UNGROUNDED-ORACLE ECHO (`return recognises(ToSeq(prefix),ToSeq(pkname),ToSeq(key))` directly): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies in 12.4s (exit 0). This is a correct-but-different-shape impl (echoes the pinned oracle), NOT a wrong impl.

MANDATORY RESOLVE for the one CANDIDATE (atk_7): its faithful refined repo patch is the re.escape fix (atk_7 computes exactly `recognises`, which the A-reference validates == the real re.escape-fixed .match). Materialized as gold_patch.diff and executed via swebench_unified.harness.run_resolve('django__django-12143', patch) => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. The verifying candidate's faithful patch RESOLVES, so no verify⇏correct witness exists.

A-LEG / DEEP-MODEL AUDIT (the focus): the sole trust point is A2 (A-reference) `recognises == real re.escape-fixed pattern .match` over the scoped POST-key domain.
- axiom_check.py (G-AX) executed => 'G-AX OK: deep model recognises == real re.escape-fixed pattern match over 60540 scoped boundary+fuzz inputs (0 mismatch); 30059 inputs discriminate fixed vs pre-fix (incl. the F2P prefix=form$ case)' (exit 0).
- INDEPENDENT differential (my own generator, not the bundle's): 612000 in-scope triples with adversarial hyphen/digit/metachar prefixes and digit-containing pknames (id, -a, 0, x, a-b) probing decomposition-ambiguity => 0 mismatches; F2P case recognises==fixed==True.
- Domain scoping (ASCII \d, no trailing newline) is legitimate: both properties are shared by pre- and post-fix code and by every real submitted HTTP form-field name; the gold fix changes ONLY prefix interpretation (literal via re.escape), exactly what recognises pins. F2P test admin_changelist.tests test_get_list_editable_queryset_with_regex_chars_in_prefix uses prefix='form$', key 'form$-0-uuid' — squarely in scope and correctly modeled.

REFINEMENT.md LEG AUDIT: R1 (str<->List[int] type refinement) = R; A2 (recognises<->re.escape-fixed match) = A-reference validated by G-AX (correspondence to real callee CONFIRMED, no consumed axiom); R3 (single-key predicate<->unchanged POST comprehension filter) = R, corroborated by conformance_check.py driving the real ModelAdmin._get_edited_object_pks per-key. §B helpers (match_literal/run_is_digits) are proof-only scaffolding, no repo counterpart. §C: NO kind-3 leg — the one changed op (regex escape) is modeled deeply, never axiomatized; model.py axioms region is empty (no consumed @ContractOnly), consistent with the doc. Correspondence holds.

CONCLUSION: spec is total-pinning; 6 distinct wrong impls (prepatch + partial-domain + boundary + control-flow-effect + dropped-digit + dropped-hyphen) all REJECTED; the single verifying candidate is a correct echo whose materialized faithful patch RESOLVES under the official harness; A-reference correspondence robustly holds. No verify⇏correct witness. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the deep-model A-reference `recognises(prefix, pkname, key)` vs the real post-fix callee re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkname)).match(key) is not None.

METHOD: independent transcription of model.py's `recognises`/`prefix_eq`/`all_digits` into Python str, fuzzed against the real CPython `re` callee. (1) Strict in-scope domain (ASCII-only, no newline, identifier pknames, prefixes over all regex metachars): 2,000,000 inputs -> 0 mismatches. (2) Broad fuzz incl. metachars/newlines/unicode digits: 500,000 inputs -> 0 in-scope mismatches. (3) Targeted boundary suite (literal '.', '$', empty prefix, F2P form$ case, leading/trailing newlines, unicode digit): all agree except the two documented out-of-scope points.

The ONLY divergences from the real callee are the two boundaries explicitly scoped out in mapping.md/axiom_check.py: (a) key='form-0-uuid\n' (trailing newline; $ pre-\n tolerance), model=False real=True; (b) key='form-٠-uuid' (Arabic-Indic zero, unicode \d acceptance), model=False real=True. Both were verified FIX-ORTHOGONAL: pre-fix (raw prefix) and post-fix (re.escape) match agree on them, so they are not part of the behaviour the patch changes and their exclusion cannot mask the fix. HTTP form-field names cannot carry a raw newline and formset indices are int-rendered ASCII, so neither is a real submitted key. The scoping is thus a legitimate narrowing, not spec drift.

The discriminating content (literal vs regex prefix) is faithfully modeled: `prefix_eq` matches char-for-char, so 'a.b' matches 'a.b-3-pk' but NOT 'axb-3-pk', and 'form$' F2P case = True (matching real). No in-scope input was found where the modeled function disagrees with the real repo behaviour. Bundle model.py verifies under pinned Nagini (12.4s); G-AX/G-CONF pass in meta.json (60540 + 101406 checked, 0 disagreements).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit is: wrap `prefix` in `re.escape(...)` inside `re.compile(r'{}-\d+-{}$'.format(...))` in ModelAdmin._get_edited_object_pks. The PUBLIC problem_statement (not hints_text) already fully discloses this edit: it quotes the exact buggy line `pk_pattern = re.compile(r'{}-\d+-{}$'.format(prefix, self.model._meta.pk.name))` verbatim, identifies `prefix` as the unescaped source of the regex-special-character bug, and states the fix outright: 'The fix is quite straightforward (use re.escape())'.

Spec view examined: model.py (recognises/prefix_eq/all_digits deep model + is_edited_pk_key impl w/ helpers), refinement.md, mapping.md. These do reference re.escape, literal code-point-for-code-point prefix matching, and the pre-patch '$'-as-anchor behavior (model_prepatch skeleton, F2P prefix='form$'). However, each of these facts is already public in the problem_statement: the buggy line, `prefix` as culprit, and the re.escape fix. The `recognises` predicate (literal structural decomposition prefix ++ '-' ++ digits ++ '-' ++ pkname) is simply the natural behavioral restatement of 'match prefix literally' — the direct consequence of the publicly-named re.escape fix — not an independent reconstruction of gold-patch specifics. The '$'/U+0024 discussion is the mechanism the problem_statement already flags (regex special characters in prefix). No spec-view line leaks gold-edit information beyond the public problem_statement.

Note: this is a case where the public problem_statement is maximally revealing (it literally names the fix), so the leakage bar is trivially met — the spec cannot leak 'beyond' a statement that already states the fix. Spec-region marker integrity not machine-verified here (swebench_unified module not importable from this shell/venv), but not material to the leakage verdict.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
