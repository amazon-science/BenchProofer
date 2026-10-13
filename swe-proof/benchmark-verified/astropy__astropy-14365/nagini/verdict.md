# P2 adversarial audit — astropy__astropy-14365

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -162,7 +161,6 @@
     case-insensitively."""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -174,37 +172,8 @@
     Ensures(Implies(ToSeq(field) == PSeq(110, 111), Result()))  # "no"
     # post-conditions-end
     # impl-start
-    folded = []  # type: List[int]
-    i = len(field)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(field), 1 / 2))
-        Invariant(Acc(list_pred(folded)))
-        Invariant(0 <= i and i <= len(field))
-        Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = field[i - 1]
-        Assert(ToSeq(field).drop(i - 1)[0] == c)
-        Assert(ToSeq(field).drop(i - 1).drop(1) == ToSeq(field).drop(i))
-        if 97 <= c and c <= 122:
-            folded = [c - 32] + folded
-        elif c == 383:
-            folded = [83] + folded
-        else:
-            folded = [c] + folded
-        i = i - 1
-    Assert(ToSeq(field).drop(0) == ToSeq(field))
-    # Witness lemmas: case fold of the two relevant concrete spellings of the
-    # masked sentinel, proved by explicit front-recursion unfold.
-    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
-    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
-    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
-    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
-    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
-    Assert(upseq(PSeq(78, 79)) == kw_NO())     # upseq("NO") == "NO"
-    Assert(upseq(PSeq(110, 111)) == kw_NO())   # upseq("no") == "NO"
-    return ToSeq(folded) == kw_NO()
+    # PREPATCH BUG: raw case-sensitive compare; 'no' not recognised.
+    return ToSeq(field) == kw_NO()
     # impl-end
 
 
@@ -218,7 +187,6 @@
     comparison would wrongly reject in lower case.)"""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -239,7 +207,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -288,7 +255,6 @@
     Requires(Acc(list_pred(tok0), 1 / 2))
     Requires(Acc(list_pred(tok1), 1 / 2))
     Requires(ncols >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tok0), 1 / 2))
@@ -314,7 +280,6 @@
         Invariant(Acc(list_pred(f0)))
         Invariant(0 <= i and i <= len(tok0))
         Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = tok0[i - 1]
         Assert(ToSeq(tok0).drop(i - 1)[0] == c)
@@ -336,7 +301,6 @@
         Invariant(Acc(list_pred(f1)))
         Invariant(0 <= j and j <= len(tok1))
         Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = tok1[j - 1]
         Assert(ToSeq(tok1).drop(j - 1)[0] == d)
```

Attack 2 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -162,7 +161,6 @@
     case-insensitively."""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -182,7 +180,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -218,7 +215,6 @@
     comparison would wrongly reject in lower case.)"""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -239,7 +235,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -288,7 +283,6 @@
     Requires(Acc(list_pred(tok0), 1 / 2))
     Requires(Acc(list_pred(tok1), 1 / 2))
     Requires(ncols >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tok0), 1 / 2))
@@ -306,93 +300,8 @@
                     and ncols >= 1, Result()))
     # post-conditions-end
     # impl-start
-    f0 = []  # type: List[int]
-    i = len(tok0)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(tok0), 1 / 2))
-        Invariant(Acc(list_pred(f0)))
-        Invariant(0 <= i and i <= len(tok0))
-        Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = tok0[i - 1]
-        Assert(ToSeq(tok0).drop(i - 1)[0] == c)
-        Assert(ToSeq(tok0).drop(i - 1).drop(1) == ToSeq(tok0).drop(i))
-        if 97 <= c and c <= 122:
-            f0 = [c - 32] + f0
-        elif c == 383:
-            f0 = [83] + f0
-        else:
-            f0 = [c] + f0
-        i = i - 1
-    Assert(ToSeq(tok0).drop(0) == ToSeq(tok0))
-
-    f1 = []  # type: List[int]
-    j = len(tok1)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(tok1), 1 / 2))
-        Invariant(Acc(list_pred(f1)))
-        Invariant(0 <= j and j <= len(tok1))
-        Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        d = tok1[j - 1]
-        Assert(ToSeq(tok1).drop(j - 1)[0] == d)
-        Assert(ToSeq(tok1).drop(j - 1).drop(1) == ToSeq(tok1).drop(j))
-        if 97 <= d and d <= 122:
-            f1 = [d - 32] + f1
-        elif d == 383:
-            f1 = [83] + f1
-        else:
-            f1 = [d] + f1
-        j = j - 1
-    Assert(ToSeq(tok1).drop(0) == ToSeq(tok1))
-
-    # Witness lemmas: case fold of the lower- and upper-case spellings of the
-    # two keyword words, proved by explicit front-recursion unfold.
-    Assert(up(114) == 82 and up(101) == 69 and up(97) == 65 and up(100) == 68)
-    Assert(up(115) == 83 and up(82) == 82 and up(69) == 69 and up(65) == 65)
-    Assert(up(68) == 68 and up(83) == 83)
-    # upseq("read") == "READ"
-    Assert(PSeq(114, 101, 97, 100).drop(1) == PSeq(101, 97, 100))
-    Assert(PSeq(101, 97, 100).drop(1) == PSeq(97, 100))
-    Assert(PSeq(97, 100).drop(1) == PSeq(100))
-    Assert(PSeq(100).drop(1) == PSeq(0).take(0))
-    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
-    Assert(upseq(PSeq(100)) == PSeq(68))
-    Assert(upseq(PSeq(97, 100)) == PSeq(65, 68))
-    Assert(upseq(PSeq(101, 97, 100)) == PSeq(69, 65, 68))
-    Assert(upseq(PSeq(114, 101, 97, 100)) == kw_READ())
-    # upseq("serr") == "SERR"
-    Assert(PSeq(115, 101, 114, 114).drop(1) == PSeq(101, 114, 114))
-    Assert(PSeq(101, 114, 114).drop(1) == PSeq(114, 114))
-    Assert(PSeq(114, 114).drop(1) == PSeq(114))
-    Assert(PSeq(114).drop(1) == PSeq(0).take(0))
-    Assert(upseq(PSeq(114)) == PSeq(82))
-    Assert(upseq(PSeq(114, 114)) == PSeq(82, 82))
-    Assert(upseq(PSeq(101, 114, 114)) == PSeq(69, 82, 82))
-    Assert(upseq(PSeq(115, 101, 114, 114)) == kw_SERR())
-    # upseq("READ") == "READ" (already upper)
-    Assert(PSeq(82, 69, 65, 68).drop(1) == PSeq(69, 65, 68))
-    Assert(PSeq(69, 65, 68).drop(1) == PSeq(65, 68))
-    Assert(PSeq(65, 68).drop(1) == PSeq(68))
-    Assert(PSeq(68).drop(1) == PSeq(0).take(0))
-    Assert(upseq(PSeq(68)) == PSeq(68))
-    Assert(upseq(PSeq(65, 68)) == PSeq(65, 68))
-    Assert(upseq(PSeq(69, 65, 68)) == PSeq(69, 65, 68))
-    Assert(upseq(PSeq(82, 69, 65, 68)) == kw_READ())
-    # upseq("SERR") == "SERR" (already upper)
-    Assert(PSeq(83, 69, 82, 82).drop(1) == PSeq(69, 82, 82))
-    Assert(PSeq(69, 82, 82).drop(1) == PSeq(82, 82))
-    Assert(PSeq(82, 82).drop(1) == PSeq(82) and PSeq(82).drop(1) == PSeq(0).take(0))
-    Assert(upseq(PSeq(82)) == PSeq(82))
-    Assert(upseq(PSeq(82, 82)) == PSeq(82, 82))
-    Assert(upseq(PSeq(69, 82, 82)) == PSeq(69, 82, 82))
-    Assert(upseq(PSeq(83, 69, 82, 82)) == kw_SERR())
-
-    is_read = ToSeq(f0) == kw_READ()
-    is_err = ToSeq(f1) == kw_SERR() or ToSeq(f1) == kw_TERR()
+    # PREPATCH BUG: raw case-sensitive keyword compare.
+    is_read = ToSeq(tok0) == kw_READ()
+    is_err = ToSeq(tok1) == kw_SERR() or ToSeq(tok1) == kw_TERR()
     return is_read and is_err and ncols >= 1
     # impl-end
```

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -162,7 +161,6 @@
     case-insensitively."""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -182,7 +180,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -218,7 +215,6 @@
     comparison would wrongly reject in lower case.)"""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -239,7 +235,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -288,7 +283,6 @@
     Requires(Acc(list_pred(tok0), 1 / 2))
     Requires(Acc(list_pred(tok1), 1 / 2))
     Requires(ncols >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tok0), 1 / 2))
@@ -314,7 +308,6 @@
         Invariant(Acc(list_pred(f0)))
         Invariant(0 <= i and i <= len(tok0))
         Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = tok0[i - 1]
         Assert(ToSeq(tok0).drop(i - 1)[0] == c)
@@ -336,7 +329,6 @@
         Invariant(Acc(list_pred(f1)))
         Invariant(0 <= j and j <= len(tok1))
         Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = tok1[j - 1]
         Assert(ToSeq(tok1).drop(j - 1)[0] == d)
@@ -394,5 +386,6 @@
 
     is_read = ToSeq(f0) == kw_READ()
     is_err = ToSeq(f1) == kw_SERR() or ToSeq(f1) == kw_TERR()
-    return is_read and is_err and ncols >= 1
+    # PARTIAL DOMAIN: only SERR recognised, TERR dropped.
+    return upseq(tok0) == kw_READ() and upseq(tok1) == kw_SERR() and ncols >= 1
     # impl-end
```

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -162,7 +161,6 @@
     case-insensitively."""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -182,7 +180,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -218,7 +215,6 @@
     comparison would wrongly reject in lower case.)"""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -239,7 +235,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -276,7 +271,8 @@
     is_signed_nan = (len(field) >= 1
                      and (field[0] == 43 or field[0] == 45)
                      and ToSeq(folded).drop(1) == kw_NAN())
-    return is_no or is_nan or is_signed_nan
+    # BOUNDARY BUG: signed-NAN alternative dropped.
+    return upseq(field) == kw_NO() or upseq(field) == kw_NAN()
     # impl-end
 
 
@@ -288,7 +284,6 @@
     Requires(Acc(list_pred(tok0), 1 / 2))
     Requires(Acc(list_pred(tok1), 1 / 2))
     Requires(ncols >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tok0), 1 / 2))
@@ -314,7 +309,6 @@
         Invariant(Acc(list_pred(f0)))
         Invariant(0 <= i and i <= len(tok0))
         Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = tok0[i - 1]
         Assert(ToSeq(tok0).drop(i - 1)[0] == c)
@@ -336,7 +330,6 @@
         Invariant(Acc(list_pred(f1)))
         Invariant(0 <= j and j <= len(tok1))
         Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = tok1[j - 1]
         Assert(ToSeq(tok1).drop(j - 1)[0] == d)
```

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -162,7 +161,6 @@
     case-insensitively."""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -174,37 +172,8 @@
     Ensures(Implies(ToSeq(field) == PSeq(110, 111), Result()))  # "no"
     # post-conditions-end
     # impl-start
-    folded = []  # type: List[int]
-    i = len(field)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(field), 1 / 2))
-        Invariant(Acc(list_pred(folded)))
-        Invariant(0 <= i and i <= len(field))
-        Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = field[i - 1]
-        Assert(ToSeq(field).drop(i - 1)[0] == c)
-        Assert(ToSeq(field).drop(i - 1).drop(1) == ToSeq(field).drop(i))
-        if 97 <= c and c <= 122:
-            folded = [c - 32] + folded
-        elif c == 383:
-            folded = [83] + folded
-        else:
-            folded = [c] + folded
-        i = i - 1
-    Assert(ToSeq(field).drop(0) == ToSeq(field))
-    # Witness lemmas: case fold of the two relevant concrete spellings of the
-    # masked sentinel, proved by explicit front-recursion unfold.
-    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
-    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
-    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
-    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
-    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
-    Assert(upseq(PSeq(78, 79)) == kw_NO())     # upseq("NO") == "NO"
-    Assert(upseq(PSeq(110, 111)) == kw_NO())   # upseq("no") == "NO"
-    return ToSeq(folded) == kw_NO()
+    # CONTROL-FLOW BUG: treat any length-2 field as masked.
+    return len(field) == 2
     # impl-end
 
 
@@ -218,7 +187,6 @@
     comparison would wrongly reject in lower case.)"""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -239,7 +207,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -288,7 +255,6 @@
     Requires(Acc(list_pred(tok0), 1 / 2))
     Requires(Acc(list_pred(tok1), 1 / 2))
     Requires(ncols >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tok0), 1 / 2))
@@ -314,7 +280,6 @@
         Invariant(Acc(list_pred(f0)))
         Invariant(0 <= i and i <= len(tok0))
         Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = tok0[i - 1]
         Assert(ToSeq(tok0).drop(i - 1)[0] == c)
@@ -336,7 +301,6 @@
         Invariant(Acc(list_pred(f1)))
         Invariant(0 <= j and j <= len(tok1))
         Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = tok1[j - 1]
         Assert(ToSeq(tok1).drop(j - 1)[0] == d)
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -162,7 +161,6 @@
     case-insensitively."""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -182,7 +180,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -218,7 +215,6 @@
     comparison would wrongly reject in lower case.)"""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -239,7 +235,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -288,7 +283,6 @@
     Requires(Acc(list_pred(tok0), 1 / 2))
     Requires(Acc(list_pred(tok1), 1 / 2))
     Requires(ncols >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tok0), 1 / 2))
@@ -314,7 +308,6 @@
         Invariant(Acc(list_pred(f0)))
         Invariant(0 <= i and i <= len(tok0))
         Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = tok0[i - 1]
         Assert(ToSeq(tok0).drop(i - 1)[0] == c)
@@ -336,7 +329,6 @@
         Invariant(Acc(list_pred(f1)))
         Invariant(0 <= j and j <= len(tok1))
         Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = tok1[j - 1]
         Assert(ToSeq(tok1).drop(j - 1)[0] == d)
@@ -394,5 +386,6 @@
 
     is_read = ToSeq(f0) == kw_READ()
     is_err = ToSeq(f1) == kw_SERR() or ToSeq(f1) == kw_TERR()
-    return is_read and is_err and ncols >= 1
+    # BOUNDARY BUG: allow zero trailing columns.
+    return upseq(tok0) == kw_READ() and (upseq(tok1) == kw_SERR() or upseq(tok1) == kw_TERR()) and ncols >= 0
     # impl-end
```

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -162,7 +161,6 @@
     case-insensitively."""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -182,7 +180,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -218,7 +215,6 @@
     comparison would wrongly reject in lower case.)"""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -239,7 +235,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -276,7 +271,8 @@
     is_signed_nan = (len(field) >= 1
                      and (field[0] == 43 or field[0] == 45)
                      and ToSeq(folded).drop(1) == kw_NAN())
-    return is_no or is_nan or is_signed_nan
+    # OVER-ACCEPT BUG: NOO etc. wrongly accepted via prefix.
+    return (len(field) >= 2 and upseq(field).take(2) == kw_NO())
     # impl-end
 
 
@@ -288,7 +284,6 @@
     Requires(Acc(list_pred(tok0), 1 / 2))
     Requires(Acc(list_pred(tok1), 1 / 2))
     Requires(ncols >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tok0), 1 / 2))
@@ -314,7 +309,6 @@
         Invariant(Acc(list_pred(f0)))
         Invariant(0 <= i and i <= len(tok0))
         Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = tok0[i - 1]
         Assert(ToSeq(tok0).drop(i - 1)[0] == c)
@@ -336,7 +330,6 @@
         Invariant(Acc(list_pred(f1)))
         Invariant(0 <= j and j <= len(tok1))
         Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = tok1[j - 1]
         Assert(ToSeq(tok1).drop(j - 1)[0] == d)
```

Attack 8 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -46,7 +46,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -162,7 +161,6 @@
     case-insensitively."""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -182,7 +180,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -204,7 +201,7 @@
     Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
     Assert(upseq(PSeq(78, 79)) == kw_NO())     # upseq("NO") == "NO"
     Assert(upseq(PSeq(110, 111)) == kw_NO())   # upseq("no") == "NO"
-    return ToSeq(folded) == kw_NO()
+    return is_masked_field(ToSeq(field))
     # impl-end
 
 
@@ -218,7 +215,6 @@
     comparison would wrongly reject in lower case.)"""
     # pre-conditions-start
     Requires(Acc(list_pred(field), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field), 1 / 2))
@@ -239,7 +235,6 @@
         Invariant(Acc(list_pred(folded)))
         Invariant(0 <= i and i <= len(field))
         Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = field[i - 1]
         Assert(ToSeq(field).drop(i - 1)[0] == c)
@@ -276,7 +271,7 @@
     is_signed_nan = (len(field) >= 1
                      and (field[0] == 43 or field[0] == 45)
                      and ToSeq(folded).drop(1) == kw_NAN())
-    return is_no or is_nan or is_signed_nan
+    return is_reserved_data_token(ToSeq(field))
     # impl-end
 
 
@@ -288,7 +283,6 @@
     Requires(Acc(list_pred(tok0), 1 / 2))
     Requires(Acc(list_pred(tok1), 1 / 2))
     Requires(ncols >= 0)
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(tok0), 1 / 2))
@@ -314,7 +308,6 @@
         Invariant(Acc(list_pred(f0)))
         Invariant(0 <= i and i <= len(tok0))
         Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = tok0[i - 1]
         Assert(ToSeq(tok0).drop(i - 1)[0] == c)
@@ -336,7 +329,6 @@
         Invariant(Acc(list_pred(f1)))
         Invariant(0 <= j and j <= len(tok1))
         Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = tok1[j - 1]
         Assert(ToSeq(tok1).drop(j - 1)[0] == d)
@@ -394,5 +386,5 @@
 
     is_read = ToSeq(f0) == kw_READ()
     is_err = ToSeq(f1) == kw_SERR() or ToSeq(f1) == kw_TERR()
-    return is_read and is_err and ncols >= 1
+    return is_command_tokens(ToSeq(tok0), ToSeq(tok1), ncols)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-14365.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A plotting-table text format is parsed line by line. Two recognition
  decisions must treat the format's reserved words case-INsensitively, because
  the format itself is not case sensitive: a reserved word written in any
  mixture of upper- and lower-case denotes the same token.

  (1) COMMAND RECOGNITION.  An error-specification line begins with the
      reserved word ``READ`` followed by one of the two error kinds ``SERR`` or
      ``TERR`` and then a non-empty list of column numbers.  Whether a given
      line is such a command must depend only on the *case-folded* spelling of
      its leading two words: ``read serr 1 2``, ``READ SERR 1 2`` and
      ``Read Serr 1 2`` are all the same command.  A line whose first word
      case-folds to ``READ`` and whose second word case-folds to ``SERR`` or
      ``TERR``, with at least one trailing column number, is a command;
      otherwise it is not (and in particular must not be rejected merely for
      being written in lower case).

  (2) MISSING-VALUE RECOGNITION.  Inside a data row, a single field denotes a
      missing (masked) value exactly when that field, compared
      case-INsensitively, equals the reserved word ``NO``.  Thus ``NO``, ``no``,
      ``No`` and ``nO`` are all the masked sentinel, while any other field is an
      ordinary numeric value.

Both decisions reduce to: normalise the field/word to a single case and
compare the normalised result to a constant reserved word.  Deciding either by
a raw, case-distinguishing comparison is correct only for the all-upper-case
spelling and wrongly rejects the lower- and mixed-case spellings the format
permits.

Text is modelled as ``List[int]`` / ``PSeq[int]`` of code points (Nagini bans
``str`` indexing); the case normalisation is modelled DEEPLY as a per-code-point
upper-casing fold (``upseq``): the ASCII letters ``a``..``z`` fold to
``A``..``Z``, and the single further code point that case-insensitive text
matching identifies with one of the reserved-word letters — the historic long-s
letterform (383), identified with ``S`` — folds to that letter (83); every
other code point is unchanged. The fold is validated equal to the real case
normalisation by axiom_check.py (G-AX), not consumed as an axiom.  The unchanged
surrounding machinery (splitting a line into fields/words, the numeric column
list, the numeric data fields) is case-irrelevant and is handled by refinement,
not re-modelled here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the changed operation in both sites is the case normalisation
#  itself, modelled deeply below by `up`/`upseq`. The real case normalisation is
#  an A-reference validated by axiom_check.py / G-AX, not a consumed
#  @ContractOnly axiom. The unchanged surrounding machinery is handled by
#  composition in refinement.md and is not referenced from this spec.)
# axioms-end


# pure-start
@Pure
def up(c: int) -> int:
    """Case normalisation of a single code point: a lower-case ASCII letter
    (``a``..``z``, 97..122) maps to its upper-case form (subtract 32); the
    historic long-s letterform (383) — the one further code point that
    case-insensitive text matching identifies with a reserved-word letter —
    maps to ``S`` (83); every other code point is unchanged. This is the
    per-code-point action of the case fold the two recognition decisions rely
    on."""
    Ensures(Implies(97 <= c and c <= 122, Result() == c - 32))
    Ensures(Implies(c == 383, Result() == 83))
    Ensures(Implies(not (97 <= c and c <= 122) and not (c == 383),
                    Result() == c))
    if 97 <= c and c <= 122:
        return c - 32
    if c == 383:
        return 83
    return c


@Pure
def upseq(s: PSeq[int]) -> PSeq[int]:
    """Case fold of a whole field/word: the per-code-point upper-casing applied
    elementwise. Front-recursive so a single unfold is available per loop step.
    Equal in length to the input."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return s
    return PSeq(up(s[0])) + upseq(s.drop(1))


@Pure
def kw_NO() -> PSeq[int]:
    # "NO"
    return PSeq(78, 79)


@Pure
def kw_READ() -> PSeq[int]:
    # "READ"
    return PSeq(82, 69, 65, 68)


@Pure
def kw_SERR() -> PSeq[int]:
    # "SERR"
    return PSeq(83, 69, 82, 82)


@Pure
def kw_TERR() -> PSeq[int]:
    # "TERR"
    return PSeq(84, 69, 82, 82)


@Pure
def kw_NAN() -> PSeq[int]:
    # "NAN"
    return PSeq(78, 65, 78)


@Pure
def is_masked_field(field: PSeq[int]) -> bool:
    """A data field denotes a missing/masked value iff its case fold equals the
    reserved word ``NO`` (case-insensitive)."""
    return upseq(field) == kw_NO()


@Pure
def is_reserved_data_token(field: PSeq[int]) -> bool:
    """A field is one of the format's RESERVED-WORD data tokens iff (case
    folded) it is the missing-value word ``NO`` or the not-a-number word ``NAN``
    (optionally preceded by a single ``+``/``-`` sign). These reserved words —
    unlike ordinary decimal numbers, which contain no letters — must be
    recognised case-INsensitively: ``no``, ``No``, ``nan``, ``NaN``, ``+nan``
    all denote the same reserved token as ``NO``/``NAN``. (Ordinary numeric
    fields are case-irrelevant and recognised by the unchanged numeric
    machinery, not by this predicate.)"""
    return (upseq(field) == kw_NO()
            or upseq(field) == kw_NAN()
            or (len(field) >= 1
                and (field[0] == 43 or field[0] == 45)   # '+' or '-'
                and upseq(field.drop(1)) == kw_NAN()))


@Pure
def is_command_tokens(tok0: PSeq[int], tok1: PSeq[int], ncols: int) -> bool:
    """The leading two words ``tok0``, ``tok1`` and the count ``ncols`` of
    trailing column numbers denote an error-specification command iff (case
    folded) ``tok0`` is ``READ``, ``tok1`` is ``SERR`` or ``TERR``, and there is
    at least one trailing column number. The case fold is applied to BOTH
    keyword words; the column count is case-irrelevant."""
    return (upseq(tok0) == kw_READ()
            and (upseq(tok1) == kw_SERR() or upseq(tok1) == kw_TERR())
            and ncols >= 1)
# pure-end


def masked_field(field: List[int]) -> bool:
    """Decide whether a single data field is the masked sentinel ``NO``,
    case-insensitively."""
    # pre-conditions-start
    Requires(Acc(list_pred(field), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field), 1 / 2))
    # The field is masked iff its case fold equals the reserved word ``NO``.
    Ensures(Result() == is_masked_field(ToSeq(field)))
    # Discriminating witnesses: both ``NO`` and ``no`` are masked; a length-2
    # field that is not a case variant of ``NO`` is not.
    Ensures(Implies(ToSeq(field) == PSeq(78, 79), Result()))   # "NO"
    Ensures(Implies(ToSeq(field) == PSeq(110, 111), Result()))  # "no"
    # post-conditions-end
    # impl-start
    folded = []  # type: List[int]
    i = len(field)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field), 1 / 2))
        Invariant(Acc(list_pred(folded)))
        Invariant(0 <= i and i <= len(field))
        Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
        # invariants-end
        c = field[i - 1]
        Assert(ToSeq(field).drop(i - 1)[0] == c)
        Assert(ToSeq(field).drop(i - 1).drop(1) == ToSeq(field).drop(i))
        if 97 <= c and c <= 122:
            folded = [c - 32] + folded
        elif c == 383:
            folded = [83] + folded
        else:
            folded = [c] + folded
        i = i - 1
    Assert(ToSeq(field).drop(0) == ToSeq(field))
    # Witness lemmas: case fold of the two relevant concrete spellings of the
    # masked sentinel, proved by explicit front-recursion unfold.
    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
    Assert(upseq(PSeq(78, 79)) == kw_NO())     # upseq("NO") == "NO"
    Assert(upseq(PSeq(110, 111)) == kw_NO())   # upseq("no") == "NO"
    return ToSeq(folded) == kw_NO()
    # impl-end


def reserved_data_token(field: List[int]) -> bool:
    """Decide whether a single field of a data row is one of the format's
    RESERVED-WORD data tokens — the missing-value word ``NO`` or the
    not-a-number word ``NAN`` (with an optional leading sign) — recognised
    case-INsensitively. (Ordinary decimal-number fields are recognised by the
    unchanged numeric machinery and are out of scope of this decision; this
    decides only the reserved-word alternative that a case-distinguishing
    comparison would wrongly reject in lower case.)"""
    # pre-conditions-start
    Requires(Acc(list_pred(field), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field), 1 / 2))
    # The field is a reserved data token iff (case folded) it is ``NO`` or
    # ``NAN`` or a signed ``NAN``.
    Ensures(Result() == is_reserved_data_token(ToSeq(field)))
    # Discriminating witnesses: the lower-case missing-value word ``no`` and the
    # upper-case ``NO`` are both recognised reserved data tokens.
    Ensures(Implies(ToSeq(field) == PSeq(110, 111), Result()))  # "no"
    Ensures(Implies(ToSeq(field) == PSeq(78, 79), Result()))    # "NO"
    # post-conditions-end
    # impl-start
    folded = []  # type: List[int]
    i = len(field)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field), 1 / 2))
        Invariant(Acc(list_pred(folded)))
        Invariant(0 <= i and i <= len(field))
        Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
        # invariants-end
        c = field[i - 1]
        Assert(ToSeq(field).drop(i - 1)[0] == c)
        Assert(ToSeq(field).drop(i - 1).drop(1) == ToSeq(field).drop(i))
        if 97 <= c and c <= 122:
            folded = [c - 32] + folded
        elif c == 383:
            folded = [83] + folded
        else:
            folded = [c] + folded
        i = i - 1
    Assert(ToSeq(field).drop(0) == ToSeq(field))
    # The whole field is now folded: ToSeq(folded) == upseq(ToSeq(field)).
    Assert(ToSeq(folded) == upseq(ToSeq(field)))
    # Witness lemmas: case fold of the two relevant concrete spellings of the
    # missing-value reserved word, proved by explicit front-recursion unfold.
    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
    Assert(upseq(PSeq(78, 79)) == kw_NO())     # upseq("NO") == "NO"
    Assert(upseq(PSeq(110, 111)) == kw_NO())   # upseq("no") == "NO"
    # Sign-prefix lemma: the case fold commutes with dropping the leading sign
    # (an unfold of upseq), so the signed-NAN test can be read off `folded`.
    if len(field) >= 1:
        Assert(upseq(ToSeq(field)) == PSeq(up(ToSeq(field)[0]))
               + upseq(ToSeq(field).drop(1)))
        Assert(upseq(ToSeq(field)).drop(1) == upseq(ToSeq(field).drop(1)))
        Assert(Implies(ToSeq(field)[0] == 43 or ToSeq(field)[0] == 45,
                       up(ToSeq(field)[0]) == ToSeq(field)[0]))
    is_no = ToSeq(folded) == kw_NO()
    is_nan = ToSeq(folded) == kw_NAN()
    is_signed_nan = (len(field) >= 1
                     and (field[0] == 43 or field[0] == 45)
                     and ToSeq(folded).drop(1) == kw_NAN())
    return is_no or is_nan or is_signed_nan
    # impl-end


def command_line(tok0: List[int], tok1: List[int], ncols: int) -> bool:
    """Decide whether a line whose leading two whitespace-separated words are
    ``tok0`` and ``tok1`` and which carries ``ncols`` trailing column numbers is
    an error-specification command, case-insensitively."""
    # pre-conditions-start
    Requires(Acc(list_pred(tok0), 1 / 2))
    Requires(Acc(list_pred(tok1), 1 / 2))
    Requires(ncols >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tok0), 1 / 2))
    Ensures(Acc(list_pred(tok1), 1 / 2))
    # A command iff (case folded) the words are ``READ`` and ``SERR``/``TERR``
    # with at least one trailing column number.
    Ensures(Result() == is_command_tokens(ToSeq(tok0), ToSeq(tok1), ncols))
    # Discriminating witnesses: a lower-case ``read serr 1`` IS a command;
    # an upper-case ``READ SERR 1`` is too; an unknown error kind is not.
    Ensures(Implies(ToSeq(tok0) == PSeq(114, 101, 97, 100)        # "read"
                    and ToSeq(tok1) == PSeq(115, 101, 114, 114)   # "serr"
                    and ncols >= 1, Result()))
    Ensures(Implies(ToSeq(tok0) == PSeq(82, 69, 65, 68)           # "READ"
                    and ToSeq(tok1) == PSeq(83, 69, 82, 82)       # "SERR"
                    and ncols >= 1, Result()))
    # post-conditions-end
    # impl-start
    f0 = []  # type: List[int]
    i = len(tok0)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tok0), 1 / 2))
        Invariant(Acc(list_pred(f0)))
        Invariant(0 <= i and i <= len(tok0))
        Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
        # invariants-end
        c = tok0[i - 1]
        Assert(ToSeq(tok0).drop(i - 1)[0] == c)
        Assert(ToSeq(tok0).drop(i - 1).drop(1) == ToSeq(tok0).drop(i))
        if 97 <= c and c <= 122:
            f0 = [c - 32] + f0
        elif c == 383:
            f0 = [83] + f0
        else:
            f0 = [c] + f0
        i = i - 1
    Assert(ToSeq(tok0).drop(0) == ToSeq(tok0))

    f1 = []  # type: List[int]
    j = len(tok1)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(tok1), 1 / 2))
        Invariant(Acc(list_pred(f1)))
        Invariant(0 <= j and j <= len(tok1))
        Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
        # invariants-end
        d = tok1[j - 1]
        Assert(ToSeq(tok1).drop(j - 1)[0] == d)
        Assert(ToSeq(tok1).drop(j - 1).drop(1) == ToSeq(tok1).drop(j))
        if 97 <= d and d <= 122:
            f1 = [d - 32] + f1
        elif d == 383:
            f1 = [83] + f1
        else:
            f1 = [d] + f1
        j = j - 1
    Assert(ToSeq(tok1).drop(0) == ToSeq(tok1))

    # Witness lemmas: case fold of the lower- and upper-case spellings of the
    # two keyword words, proved by explicit front-recursion unfold.
    Assert(up(114) == 82 and up(101) == 69 and up(97) == 65 and up(100) == 68)
    Assert(up(115) == 83 and up(82) == 82 and up(69) == 69 and up(65) == 65)
    Assert(up(68) == 68 and up(83) == 83)
    # upseq("read") == "READ"
    Assert(PSeq(114, 101, 97, 100).drop(1) == PSeq(101, 97, 100))
    Assert(PSeq(101, 97, 100).drop(1) == PSeq(97, 100))
    Assert(PSeq(97, 100).drop(1) == PSeq(100))
    Assert(PSeq(100).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(100)) == PSeq(68))
    Assert(upseq(PSeq(97, 100)) == PSeq(65, 68))
    Assert(upseq(PSeq(101, 97, 100)) == PSeq(69, 65, 68))
    Assert(upseq(PSeq(114, 101, 97, 100)) == kw_READ())
    # upseq("serr") == "SERR"
    Assert(PSeq(115, 101, 114, 114).drop(1) == PSeq(101, 114, 114))
    Assert(PSeq(101, 114, 114).drop(1) == PSeq(114, 114))
    Assert(PSeq(114, 114).drop(1) == PSeq(114))
    Assert(PSeq(114).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(114)) == PSeq(82))
    Assert(upseq(PSeq(114, 114)) == PSeq(82, 82))
    Assert(upseq(PSeq(101, 114, 114)) == PSeq(69, 82, 82))
    Assert(upseq(PSeq(115, 101, 114, 114)) == kw_SERR())
    # upseq("READ") == "READ" (already upper)
    Assert(PSeq(82, 69, 65, 68).drop(1) == PSeq(69, 65, 68))
    Assert(PSeq(69, 65, 68).drop(1) == PSeq(65, 68))
    Assert(PSeq(65, 68).drop(1) == PSeq(68))
    Assert(PSeq(68).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(68)) == PSeq(68))
    Assert(upseq(PSeq(65, 68)) == PSeq(65, 68))
    Assert(upseq(PSeq(69, 65, 68)) == PSeq(69, 65, 68))
    Assert(upseq(PSeq(82, 69, 65, 68)) == kw_READ())
    # upseq("SERR") == "SERR" (already upper)
    Assert(PSeq(83, 69, 82, 82).drop(1) == PSeq(69, 82, 82))
    Assert(PSeq(69, 82, 82).drop(1) == PSeq(82, 82))
    Assert(PSeq(82, 82).drop(1) == PSeq(82) and PSeq(82).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(82)) == PSeq(82))
    Assert(upseq(PSeq(82, 82)) == PSeq(82, 82))
    Assert(upseq(PSeq(69, 82, 82)) == PSeq(69, 82, 82))
    Assert(upseq(PSeq(83, 69, 82, 82)) == kw_SERR())

    is_read = ToSeq(f0) == kw_READ()
    is_err = ToSeq(f1) == kw_SERR() or ToSeq(f1) == kw_TERR()
    return is_read and is_err and ncols >= 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. env (module swebench_unified), FSx HOME. Commands: `python -m swebench_unified.adversary same-spec/weakness nagini astropy__astropy-14365 <atk>`; verify via scripts/nagini_verify.sh; resolve via harness.run_resolve.

SPEC STRUCTURE: The three contracted functions (masked_field, reserved_data_token, command_line) each carry an EXACT-EQUALITY postcondition Result() == <frozen @Pure oracle> (is_masked_field / is_reserved_data_token / is_command_tokens), where the oracles are the deep case-fold models up/upseq. Exact equality pins every verifying impl to be functionally identical to the gold-patched behavior over the whole PSeq[int] domain, so no verify-but-wrong impl can exist at the refinement layer.

SAME-SPEC: all 8 attack files confirmed byte-identical spec via `same-spec` (exit 0).

atk_1.py (ORACLE-ECHO on all 3 fns; returns is_masked_field/is_reserved_data_token/is_command_tokens directly): CANDIDATE — shares spec AND verifies (16.6s, exit 0). This is functionally identical to gold, a resolving echo, which per the 2026-08-06 policy is NOT a weakness.
- atk_2.py (PREPATCH masked: raw case-sensitive ToSeq(field)==kw_NO()): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_3.py (PREPATCH command: raw case-sensitive keyword compare): verification failed (exit 2).
- atk_4.py (PARTIAL-DOMAIN: only SERR recognised, TERR dropped): verification failed (exit 2).
- atk_5.py (BOUNDARY: signed-NAN alternative dropped): verification failed (exit 2).
- atk_6.py (CONTROL-FLOW: any length-2 field treated masked): verification failed (exit 2).
- atk_7.py (BOUNDARY: allow zero trailing columns, ncols>=0): verification failed (exit 2).
- atk_8.py (UNGROUNDED/OVER-ACCEPT: NO-prefix via take(2)): verification failed (exit 2).
Positive control (unmodified model.py): VERIFIED (16.66s).

MANDATORY RESOLVE RUN ON THE ONLY CANDIDATE: atk_1's faithful refined patch = the gold patch (re.IGNORECASE + v.upper()=="NO"), because atk_1 computes exactly the oracle values which G-AX/G-CONF validate == the real patched recognition behaviour. Executed run_resolve('astropy__astropy-14365', <faithful patch>, run_id=sbu-eq-atk1-audit) under the official Docker harness => RESOLVED: True, completed: True. Faithful patch at atk_1_faithful_patch.diff. Since the CANDIDATE resolves, verify=>correct holds; no BROKEN evidence.

REFINEMENT.MD AUDIT: 12 legs A1-A4/B1-B4/C1-C4, all tagged R / A-reference / I; no consumed @ContractOnly axioms (axioms region empty), no kind-3 unexpressible-changed-op steps (§D). The four A-references (up/upseq<->str.upper; is_masked_field<->v.upper()=="NO"; is_command_tokens<->patched _line_type command verdict; is_reserved_data_token<->patched (NO|[-+]?nan)+_line_type data/new) each map to a real callee at base_commit and are validated by G-AX (strict pass: 164 boundary + 73000 fuzz, 0 violations, run with gold applied via the DEFECT-3 post-patch self-guard). Correspondence holds. G-CONF strict pass (117682 comparisons, 0 disagreements). Model<->patch correspondence sound.

VERDICT: SOUND — >=5 (7) distinct wrong impls run, none verifies; the sole verifying same-spec impl is a gold-equivalent echo whose faithful patch RESOLVES under the executed official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-14365.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A plotting-table text format is parsed line by line. Two recognition
  decisions must treat the format's reserved words case-INsensitively, because
  the format itself is not case sensitive: a reserved word written in any
  mixture of upper- and lower-case denotes the same token.

  (1) COMMAND RECOGNITION.  An error-specification line begins with the
      reserved word ``READ`` followed by one of the two error kinds ``SERR`` or
      ``TERR`` and then a non-empty list of column numbers.  Whether a given
      line is such a command must depend only on the *case-folded* spelling of
      its leading two words: ``read serr 1 2``, ``READ SERR 1 2`` and
      ``Read Serr 1 2`` are all the same command.  A line whose first word
      case-folds to ``READ`` and whose second word case-folds to ``SERR`` or
      ``TERR``, with at least one trailing column number, is a command;
      otherwise it is not (and in particular must not be rejected merely for
      being written in lower case).

  (2) MISSING-VALUE RECOGNITION.  Inside a data row, a single field denotes a
      missing (masked) value exactly when that field, compared
      case-INsensitively, equals the reserved word ``NO``.  Thus ``NO``, ``no``,
      ``No`` and ``nO`` are all the masked sentinel, while any other field is an
      ordinary numeric value.

Both decisions reduce to: normalise the field/word to a single case and
compare the normalised result to a constant reserved word.  Deciding either by
a raw, case-distinguishing comparison is correct only for the all-upper-case
spelling and wrongly rejects the lower- and mixed-case spellings the format
permits.

Text is modelled as ``List[int]`` / ``PSeq[int]`` of code points (Nagini bans
``str`` indexing); the case normalisation is modelled DEEPLY as a per-code-point
upper-casing fold (``upseq``): the ASCII letters ``a``..``z`` fold to
``A``..``Z``, and the single further code point that case-insensitive text
matching identifies with one of the reserved-word letters — the historic long-s
letterform (383), identified with ``S`` — folds to that letter (83); every
other code point is unchanged. The fold is validated equal to the real case
normalisation by axiom_check.py (G-AX), not consumed as an axiom.  The unchanged
surrounding machinery (splitting a line into fields/words, the numeric column
list, the numeric data fields) is case-irrelevant and is handled by refinement,
not re-modelled here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the changed operation in both sites is the case normalisation
#  itself, modelled deeply below by `up`/`upseq`. The real case normalisation is
#  an A-reference validated by axiom_check.py / G-AX, not a consumed
#  @ContractOnly axiom. The unchanged surrounding machinery is handled by
#  composition in refinement.md and is not referenced from this spec.)
# axioms-end


# pure-start
@Pure
def up(c: int) -> int:
    """Case normalisation of a single code point: a lower-case ASCII letter
    (``a``..``z``, 97..122) maps to its upper-case form (subtract 32); the
    historic long-s letterform (383) — the one further code point that
    case-insensitive text matching identifies with a reserved-word letter —
    maps to ``S`` (83); every other code point is unchanged. This is the
    per-code-point action of the case fold the two recognition decisions rely
    on."""
    Ensures(Implies(97 <= c and c <= 122, Result() == c - 32))
    Ensures(Implies(c == 383, Result() == 83))
    Ensures(Implies(not (97 <= c and c <= 122) and not (c == 383),
                    Result() == c))
    if 97 <= c and c <= 122:
        return c - 32
    if c == 383:
        return 83
    return c


@Pure
def upseq(s: PSeq[int]) -> PSeq[int]:
    """Case fold of a whole field/word: the per-code-point upper-casing applied
    elementwise. Front-recursive so a single unfold is available per loop step.
    Equal in length to the input."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return s
    return PSeq(up(s[0])) + upseq(s.drop(1))


@Pure
def kw_NO() -> PSeq[int]:
    # "NO"
    return PSeq(78, 79)


@Pure
def kw_READ() -> PSeq[int]:
    # "READ"
    return PSeq(82, 69, 65, 68)


@Pure
def kw_SERR() -> PSeq[int]:
    # "SERR"
    return PSeq(83, 69, 82, 82)


@Pure
def kw_TERR() -> PSeq[int]:
    # "TERR"
    return PSeq(84, 69, 82, 82)


@Pure
def kw_NAN() -> PSeq[int]:
    # "NAN"
    return PSeq(78, 65, 78)


@Pure
def is_masked_field(field: PSeq[int]) -> bool:
    """A data field denotes a missing/masked value iff its case fold equals the
    reserved word ``NO`` (case-insensitive)."""
    return upseq(field) == kw_NO()


@Pure
def is_reserved_data_token(field: PSeq[int]) -> bool:
    """A field is one of the format's RESERVED-WORD data tokens iff (case
    folded) it is the missing-value word ``NO`` or the not-a-number word ``NAN``
    (optionally preceded by a single ``+``/``-`` sign). These reserved words —
    unlike ordinary decimal numbers, which contain no letters — must be
    recognised case-INsensitively: ``no``, ``No``, ``nan``, ``NaN``, ``+nan``
    all denote the same reserved token as ``NO``/``NAN``. (Ordinary numeric
    fields are case-irrelevant and recognised by the unchanged numeric
    machinery, not by this predicate.)"""
    return (upseq(field) == kw_NO()
            or upseq(field) == kw_NAN()
            or (len(field) >= 1
                and (field[0] == 43 or field[0] == 45)   # '+' or '-'
                and upseq(field.drop(1)) == kw_NAN()))


@Pure
def is_command_tokens(tok0: PSeq[int], tok1: PSeq[int], ncols: int) -> bool:
    """The leading two words ``tok0``, ``tok1`` and the count ``ncols`` of
    trailing column numbers denote an error-specification command iff (case
    folded) ``tok0`` is ``READ``, ``tok1`` is ``SERR`` or ``TERR``, and there is
    at least one trailing column number. The case fold is applied to BOTH
    keyword words; the column count is case-irrelevant."""
    return (upseq(tok0) == kw_READ()
            and (upseq(tok1) == kw_SERR() or upseq(tok1) == kw_TERR())
            and ncols >= 1)
# pure-end


def masked_field(field: List[int]) -> bool:
    """Decide whether a single data field is the masked sentinel ``NO``,
    case-insensitively."""
    # pre-conditions-start
    Requires(Acc(list_pred(field), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field), 1 / 2))
    # The field is masked iff its case fold equals the reserved word ``NO``.
    Ensures(Result() == is_masked_field(ToSeq(field)))
    # Discriminating witnesses: both ``NO`` and ``no`` are masked; a length-2
    # field that is not a case variant of ``NO`` is not.
    Ensures(Implies(ToSeq(field) == PSeq(78, 79), Result()))   # "NO"
    Ensures(Implies(ToSeq(field) == PSeq(110, 111), Result()))  # "no"
    # post-conditions-end
    # impl-start
    folded = []  # type: List[int]
    i = len(field)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field), 1 / 2))
        Invariant(Acc(list_pred(folded)))
        Invariant(0 <= i and i <= len(field))
        Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
        # invariants-end
        c = field[i - 1]
        Assert(ToSeq(field).drop(i - 1)[0] == c)
        Assert(ToSeq(field).drop(i - 1).drop(1) == ToSeq(field).drop(i))
        if 97 <= c and c <= 122:
            folded = [c - 32] + folded
        elif c == 383:
            folded = [83] + folded
        else:
            folded = [c] + folded
        i = i - 1
    Assert(ToSeq(field).drop(0) == ToSeq(field))
    # Witness lemmas: case fold of the two relevant concrete spellings of the
    # masked sentinel, proved by explicit front-recursion unfold.
    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
    Assert(upseq(PSeq(78, 79)) == kw_NO())     # upseq("NO") == "NO"
    Assert(upseq(PSeq(110, 111)) == kw_NO())   # upseq("no") == "NO"
    return ToSeq(folded) == kw_NO()
    # impl-end


def reserved_data_token(field: List[int]) -> bool:
    """Decide whether a single field of a data row is one of the format's
    RESERVED-WORD data tokens — the missing-value word ``NO`` or the
    not-a-number word ``NAN`` (with an optional leading sign) — recognised
    case-INsensitively. (Ordinary decimal-number fields are recognised by the
    unchanged numeric machinery and are out of scope of this decision; this
    decides only the reserved-word alternative that a case-distinguishing
    comparison would wrongly reject in lower case.)"""
    # pre-conditions-start
    Requires(Acc(list_pred(field), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field), 1 / 2))
    # The field is a reserved data token iff (case folded) it is ``NO`` or
    # ``NAN`` or a signed ``NAN``.
    Ensures(Result() == is_reserved_data_token(ToSeq(field)))
    # Discriminating witnesses: the lower-case missing-value word ``no`` and the
    # upper-case ``NO`` are both recognised reserved data tokens.
    Ensures(Implies(ToSeq(field) == PSeq(110, 111), Result()))  # "no"
    Ensures(Implies(ToSeq(field) == PSeq(78, 79), Result()))    # "NO"
    # post-conditions-end
    # impl-start
    folded = []  # type: List[int]
    i = len(field)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field), 1 / 2))
        Invariant(Acc(list_pred(folded)))
        Invariant(0 <= i and i <= len(field))
        Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
        # invariants-end
        c = field[i - 1]
        Assert(ToSeq(field).drop(i - 1)[0] == c)
        Assert(ToSeq(field).drop(i - 1).drop(1) == ToSeq(field).drop(i))
        if 97 <= c and c <= 122:
            folded = [c - 32] + folded
        elif c == 383:
            folded = [83] + folded
        else:
            folded = [c] + folded
        i = i - 1
    Assert(ToSeq(field).drop(0) == ToSeq(field))
    # The whole field is now folded: ToSeq(folded) == upseq(ToSeq(field)).
    Assert(ToSeq(folded) == upseq(ToSeq(field)))
    # Witness lemmas: case fold of the two relevant concrete spellings of the
    # missing-value reserved word, proved by explicit front-recursion unfold.
    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
    Assert(upseq(PSeq(78, 79)) == kw_NO())     # upseq("NO") == "NO"
    Assert(upseq(PSeq(110, 111)) == kw_NO())   # upseq("no") == "NO"
    # Sign-prefix lemma: the case fold commutes with dropping the leading sign
    # (an unfold of upseq), so the signed-NAN test can be read off `folded`.
    if len(field) >= 1:
        Assert(upseq(ToSeq(field)) == PSeq(up(ToSeq(field)[0]))
               + upseq(ToSeq(field).drop(1)))
        Assert(upseq(ToSeq(field)).drop(1) == upseq(ToSeq(field).drop(1)))
        Assert(Implies(ToSeq(field)[0] == 43 or ToSeq(field)[0] == 45,
                       up(ToSeq(field)[0]) == ToSeq(field)[0]))
    is_no = ToSeq(folded) == kw_NO()
    is_nan = ToSeq(folded) == kw_NAN()
    is_signed_nan = (len(field) >= 1
                     and (field[0] == 43 or field[0] == 45)
                     and ToSeq(folded).drop(1) == kw_NAN())
    return is_no or is_nan or is_signed_nan
    # impl-end


def command_line(tok0: List[int], tok1: List[int], ncols: int) -> bool:
    """Decide whether a line whose leading two whitespace-separated words are
    ``tok0`` and ``tok1`` and which carries ``ncols`` trailing column numbers is
    an error-specification command, case-insensitively."""
    # pre-conditions-start
    Requires(Acc(list_pred(tok0), 1 / 2))
    Requires(Acc(list_pred(tok1), 1 / 2))
    Requires(ncols >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tok0), 1 / 2))
    Ensures(Acc(list_pred(tok1), 1 / 2))
    # A command iff (case folded) the words are ``READ`` and ``SERR``/``TERR``
    # with at least one trailing column number.
    Ensures(Result() == is_command_tokens(ToSeq(tok0), ToSeq(tok1), ncols))
    # Discriminating witnesses: a lower-case ``read serr 1`` IS a command;
    # an upper-case ``READ SERR 1`` is too; an unknown error kind is not.
    Ensures(Implies(ToSeq(tok0) == PSeq(114, 101, 97, 100)        # "read"
                    and ToSeq(tok1) == PSeq(115, 101, 114, 114)   # "serr"
                    and ncols >= 1, Result()))
    Ensures(Implies(ToSeq(tok0) == PSeq(82, 69, 65, 68)           # "READ"
                    and ToSeq(tok1) == PSeq(83, 69, 82, 82)       # "SERR"
                    and ncols >= 1, Result()))
    # post-conditions-end
    # impl-start
    f0 = []  # type: List[int]
    i = len(tok0)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tok0), 1 / 2))
        Invariant(Acc(list_pred(f0)))
        Invariant(0 <= i and i <= len(tok0))
        Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
        # invariants-end
        c = tok0[i - 1]
        Assert(ToSeq(tok0).drop(i - 1)[0] == c)
        Assert(ToSeq(tok0).drop(i - 1).drop(1) == ToSeq(tok0).drop(i))
        if 97 <= c and c <= 122:
            f0 = [c - 32] + f0
        elif c == 383:
            f0 = [83] + f0
        else:
            f0 = [c] + f0
        i = i - 1
    Assert(ToSeq(tok0).drop(0) == ToSeq(tok0))

    f1 = []  # type: List[int]
    j = len(tok1)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(tok1), 1 / 2))
        Invariant(Acc(list_pred(f1)))
        Invariant(0 <= j and j <= len(tok1))
        Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
        # invariants-end
        d = tok1[j - 1]
        Assert(ToSeq(tok1).drop(j - 1)[0] == d)
        Assert(ToSeq(tok1).drop(j - 1).drop(1) == ToSeq(tok1).drop(j))
        if 97 <= d and d <= 122:
            f1 = [d - 32] + f1
        elif d == 383:
            f1 = [83] + f1
        else:
            f1 = [d] + f1
        j = j - 1
    Assert(ToSeq(tok1).drop(0) == ToSeq(tok1))

    # Witness lemmas: case fold of the lower- and upper-case spellings of the
    # two keyword words, proved by explicit front-recursion unfold.
    Assert(up(114) == 82 and up(101) == 69 and up(97) == 65 and up(100) == 68)
    Assert(up(115) == 83 and up(82) == 82 and up(69) == 69 and up(65) == 65)
    Assert(up(68) == 68 and up(83) == 83)
    # upseq("read") == "READ"
    Assert(PSeq(114, 101, 97, 100).drop(1) == PSeq(101, 97, 100))
    Assert(PSeq(101, 97, 100).drop(1) == PSeq(97, 100))
    Assert(PSeq(97, 100).drop(1) == PSeq(100))
    Assert(PSeq(100).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(100)) == PSeq(68))
    Assert(upseq(PSeq(97, 100)) == PSeq(65, 68))
    Assert(upseq(PSeq(101, 97, 100)) == PSeq(69, 65, 68))
    Assert(upseq(PSeq(114, 101, 97, 100)) == kw_READ())
    # upseq("serr") == "SERR"
    Assert(PSeq(115, 101, 114, 114).drop(1) == PSeq(101, 114, 114))
    Assert(PSeq(101, 114, 114).drop(1) == PSeq(114, 114))
    Assert(PSeq(114, 114).drop(1) == PSeq(114))
    Assert(PSeq(114).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(114)) == PSeq(82))
    Assert(upseq(PSeq(114, 114)) == PSeq(82, 82))
    Assert(upseq(PSeq(101, 114, 114)) == PSeq(69, 82, 82))
    Assert(upseq(PSeq(115, 101, 114, 114)) == kw_SERR())
    # upseq("READ") == "READ" (already upper)
    Assert(PSeq(82, 69, 65, 68).drop(1) == PSeq(69, 65, 68))
    Assert(PSeq(69, 65, 68).drop(1) == PSeq(65, 68))
    Assert(PSeq(65, 68).drop(1) == PSeq(68))
    Assert(PSeq(68).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(68)) == PSeq(68))
    Assert(upseq(PSeq(65, 68)) == PSeq(65, 68))
    Assert(upseq(PSeq(69, 65, 68)) == PSeq(69, 65, 68))
    Assert(upseq(PSeq(82, 69, 65, 68)) == kw_READ())
    # upseq("SERR") == "SERR" (already upper)
    Assert(PSeq(83, 69, 82, 82).drop(1) == PSeq(69, 82, 82))
    Assert(PSeq(69, 82, 82).drop(1) == PSeq(82, 82))
    Assert(PSeq(82, 82).drop(1) == PSeq(82) and PSeq(82).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(82)) == PSeq(82))
    Assert(upseq(PSeq(82, 82)) == PSeq(82, 82))
    Assert(upseq(PSeq(69, 82, 82)) == PSeq(69, 82, 82))
    Assert(upseq(PSeq(83, 69, 82, 82)) == kw_SERR())

    is_read = ToSeq(f0) == kw_READ()
    is_err = ToSeq(f1) == kw_SERR() or ToSeq(f1) == kw_TERR()
    return is_read and is_err and ncols >= 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. env (module swebench_unified), FSx HOME. Commands: `python -m swebench_unified.adversary same-spec/weakness nagini astropy__astropy-14365 <atk>`; verify via scripts/nagini_verify.sh; resolve via harness.run_resolve.

SPEC STRUCTURE: The three contracted functions (masked_field, reserved_data_token, command_line) each carry an EXACT-EQUALITY postcondition Result() == <frozen @Pure oracle> (is_masked_field / is_reserved_data_token / is_command_tokens), where the oracles are the deep case-fold models up/upseq. Exact equality pins every verifying impl to be functionally identical to the gold-patched behavior over the whole PSeq[int] domain, so no verify-but-wrong impl can exist at the refinement layer.

SAME-SPEC: all 8 attack files confirmed byte-identical spec via `same-spec` (exit 0).

atk_1.py (ORACLE-ECHO on all 3 fns; returns is_masked_field/is_reserved_data_token/is_command_tokens directly): CANDIDATE — shares spec AND verifies (16.6s, exit 0). This is functionally identical to gold, a resolving echo, which per the 2026-08-06 policy is NOT a weakness.
- atk_2.py (PREPATCH masked: raw case-sensitive ToSeq(field)==kw_NO()): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_3.py (PREPATCH command: raw case-sensitive keyword compare): verification failed (exit 2).
- atk_4.py (PARTIAL-DOMAIN: only SERR recognised, TERR dropped): verification failed (exit 2).
- atk_5.py (BOUNDARY: signed-NAN alternative dropped): verification failed (exit 2).
- atk_6.py (CONTROL-FLOW: any length-2 field treated masked): verification failed (exit 2).
- atk_7.py (BOUNDARY: allow zero trailing columns, ncols>=0): verification failed (exit 2).
- atk_8.py (UNGROUNDED/OVER-ACCEPT: NO-prefix via take(2)): verification failed (exit 2).
Positive control (unmodified model.py): VERIFIED (16.66s).

MANDATORY RESOLVE RUN ON THE ONLY CANDIDATE: atk_1's faithful refined patch = the gold patch (re.IGNORECASE + v.upper()=="NO"), because atk_1 computes exactly the oracle values which G-AX/G-CONF validate == the real patched recognition behaviour. Executed run_resolve('astropy__astropy-14365', <faithful patch>, run_id=sbu-eq-atk1-audit) under the official Docker harness => RESOLVED: True, completed: True. Faithful patch at atk_1_faithful_patch.diff. Since the CANDIDATE resolves, verify=>correct holds; no BROKEN evidence.

REFINEMENT.MD AUDIT: 12 legs A1-A4/B1-B4/C1-C4, all tagged R / A-reference / I; no consumed @ContractOnly axioms (axioms region empty), no kind-3 unexpressible-changed-op steps (§D). The four A-references (up/upseq<->str.upper; is_masked_field<->v.upper()=="NO"; is_command_tokens<->patched _line_type command verdict; is_reserved_data_token<->patched (NO|[-+]?nan)+_line_type data/new) each map to a real callee at base_commit and are validated by G-AX (strict pass: 164 boundary + 73000 fuzz, 0 violations, run with gold applied via the DEFECT-3 post-patch self-guard). Correspondence holds. G-CONF strict pass (117682 comparisons, 0 disagreements). Model<->patch correspondence sound.

VERDICT: SOUND — >=5 (7) distinct wrong impls run, none verifies; the sole verifying same-spec impl is a gold-equivalent echo whose faithful patch RESOLVES under the executed official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Re-audited the CURRENT model.py (mtime Aug 13 03:46, NEWER than the recorded verdict.md at Aug 13 00:00). The recorded G-PANEL-2=fail/UNFAITHFUL verdict cited 'READ ſERR 1' (long-s U+017F=383 in the SERR keyword): the real patched _line_type uses re.IGNORECASE, and re.fullmatch('S','ſ',re.IGNORECASE)==True and 'ſ'.upper()=='S', so the real callee accepts it while the old model (ASCII-only fold) rejected it — a genuine spec-too-strong drift. The model has since been REPAIRED: up(c) now explicitly maps 383->83 (ſ->S), covering exactly that code point.

Re-verification against the current model, all against the byte-faithful gold-patched callees (regex 'READ [TS]ERR(\s+[0-9]+)+', '(NO|[-+]?nan)' compiled re.IGNORECASE; masking str.upper()=='NO'):
(1) Exhaustive single-code-point scan over 0..0x10FFFF: every char whose str.upper() is a single reserved letter {N,O,S,T,R,E,A,D} is folded correctly by the model — 0 mismatches. The complete set of code points Python's re.IGNORECASE/str.upper identifies with a reserved letter is exactly the ASCII case pairs plus ſ(383)->S; all captured.
(2) Per-position full-range (0..0x10FFFF) substitution scans on all three predicates (command tok0=READ/tok1=[TS]ERR; masking NO; reserved-token NO|[-+]?nan with sign positions): 0 divergences from the real callee.
(3) Multi-char case-fold expansions (ß->SS, ﬅ/ﬆ->ST) are NOT matched by Python re.IGNORECASE (confirmed empirically), so they present no leak.
(4) The prior counterexample 'READ ſERR 1' now: model=True, real=True.
(5) 300k full-Unicode random fuzz across all three sites: 0 divergences.
(6) model.py still verifies under the pinned Nagini verifier (Verification successful, 15.6s).

Spec region is a faithfulness/drift concern (not same-spec) and the modeled functions now agree with the real patched repo callees on every well-typed, precondition-satisfying input I could construct or enumerate. No diverging input exists. The old UNFAITHFUL verdict is stale; the repaired model is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py with impl/proof elided) checked against the public problem_statement only (NOT hints_text). Mechanical G-LEAK screen passes (0 hard failures, 0 warnings). Gold edit is two hunks in astropy/io/ascii/qdp.py: (1) re.compile(_type_re) -> re.compile(_type_re, re.IGNORECASE); (2) `if v == "NO":` -> `if v.upper() == "NO":`. The spec view leaks none of the edit's localization or mechanism: it does not name the patched file (qdp.py), the patched symbols (_line_type, _get_tables_from_qdp_file, _type_re), the flag re.IGNORECASE, or str.upper()/`v == "NO"`; no diff markers, no reproduced diff line, no bug/fix narration. Spec identifiers (up, upseq, masked_field, command_line, reserved_data_token) echo no underscore-stripped patched repo symbol. The case-insensitive framing ('QDP reserved words are case-insensitive; read serr 1 2 == READ SERR 1 2') is a direct abstract restatement of what the public problem_statement ALREADY states ('QDP itself is not case sensitive', lowercase `read serr 1 2` should parse instead of raising ValueError). The NO/nan masked/reserved-token behavior is additional required black-box behavior needed for the F2P roundtrip, described at the behavioral level (the legitimate role of a spec) without localizing or narrating the specific gold edit. The long-s (383)->S detail is a soundness artifact of the deep case-fold model, not part of the gold edit. Stated as desired behaviour, not as an edit — no leakage beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
