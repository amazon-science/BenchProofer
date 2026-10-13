# P2 adversarial audit — django__django-11099

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
 def accepts_ascii(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -100,30 +98,13 @@
     n = len(value)
     if n == 0:
         return False
-    i = n
-    ok = True
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
-        if not permitted_ascii(c):
-            ok = False
-        i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
-    return ok
+    return True
     # impl-end
 
 
 def accepts_unicode(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -135,21 +116,5 @@
     n = len(value)
     if n == 0:
         return False
-    i = n
-    ok = True
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
-        if not permitted_unicode(c):
-            ok = False
-        i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
-    return ok
+    return True
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
 def accepts_ascii(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -102,20 +100,13 @@
         return False
     i = n
     ok = True
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(1 <= i and i <= n and n == len(value))
         c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         if not permitted_ascii(c):
             ok = False
         i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
     return ok
     # impl-end
 
@@ -123,7 +114,6 @@
 def accepts_unicode(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -137,19 +127,12 @@
         return False
     i = n
     ok = True
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(1 <= i and i <= n and n == len(value))
         c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         if not permitted_unicode(c):
             ok = False
         i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
     return ok
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
 def accepts_ascii(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -100,22 +98,24 @@
     n = len(value)
     if n == 0:
         return False
-    i = n
+    m = n
+    if value[n - 1] == 10:
+        m = n - 1
+    if m == 0:
+        return False
+    i = m
     ok = True
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(0 <= i and i <= m and m <= n and n == len(value))
+        Invariant(ok == all_ascii_permitted(ToSeq(value).take(m).drop(i)))
         c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
+        Assert(ToSeq(value).take(m).drop(i - 1)[0] == c)
+        Assert(ToSeq(value).take(m).drop(i - 1).drop(1) == ToSeq(value).take(m).drop(i))
         if not permitted_ascii(c):
             ok = False
         i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
+    Assert(ToSeq(value).take(m).drop(0) == ToSeq(value).take(m))
     return ok
     # impl-end
 
@@ -123,7 +123,6 @@
 def accepts_unicode(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -135,21 +134,23 @@
     n = len(value)
     if n == 0:
         return False
-    i = n
+    m = n
+    if value[n - 1] == 10:
+        m = n - 1
+    if m == 0:
+        return False
+    i = m
     ok = True
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(0 <= i and i <= m and m <= n and n == len(value))
+        Invariant(ok == all_unicode_permitted(ToSeq(value).take(m).drop(i)))
         c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
+        Assert(ToSeq(value).take(m).drop(i - 1)[0] == c)
+        Assert(ToSeq(value).take(m).drop(i - 1).drop(1) == ToSeq(value).take(m).drop(i))
         if not permitted_unicode(c):
             ok = False
         i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
+    Assert(ToSeq(value).take(m).drop(0) == ToSeq(value).take(m))
     return ok
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
 def accepts_ascii(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -101,29 +99,20 @@
     if n == 0:
         return False
     i = n
-    ok = True
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
-        if not permitted_ascii(c):
-            ok = False
+        if permitted_ascii(c):
+            return True
         i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
-    return ok
+    return False
     # impl-end
 
 
 def accepts_unicode(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -136,20 +125,12 @@
     if n == 0:
         return False
     i = n
-    ok = True
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
-        if not permitted_unicode(c):
-            ok = False
+        if permitted_unicode(c):
+            return True
         i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
-    return ok
+    return False
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
 def accepts_ascii(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -99,16 +97,13 @@
     # impl-start
     n = len(value)
     if n == 0:
-        return False
+        return True
     i = n
     ok = True
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= n and n == len(value))
         Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == c)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
@@ -116,14 +111,13 @@
             ok = False
         i = i - 1
     Assert(ToSeq(value).drop(0) == ToSeq(value))
-    return ok
+    return not ok
     # impl-end
 
 
 def accepts_unicode(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -134,16 +128,13 @@
     # impl-start
     n = len(value)
     if n == 0:
-        return False
+        return True
     i = n
     ok = True
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= n and n == len(value))
         Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == c)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
@@ -151,5 +142,5 @@
             ok = False
         i = i - 1
     Assert(ToSeq(value).drop(0) == ToSeq(value))
-    return ok
+    return not ok
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
 def accepts_ascii(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -99,16 +97,13 @@
     # impl-start
     n = len(value)
     if n == 0:
-        return False
+        return True
     i = n
     ok = True
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= n and n == len(value))
         Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == c)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
@@ -123,7 +118,6 @@
 def accepts_unicode(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -134,16 +128,13 @@
     # impl-start
     n = len(value)
     if n == 0:
-        return False
+        return True
     i = n
     ok = True
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= n and n == len(value))
         Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == c)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
 def accepts_ascii(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -100,22 +98,18 @@
     n = len(value)
     if n == 0:
         return False
-    i = n
+    i = 0
     ok = True
-    while i > 0:
-        # invariants-start
+    while i < n:
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
+        Invariant(ok == all_ascii_permitted(ToSeq(value).take(i)))
+        c = value[i]
+        Assert(ToSeq(value).take(i + 1).drop(i)[0] == c)
         if not permitted_ascii(c):
             ok = False
-        i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
+        i = i + 1
+    Assert(ToSeq(value).take(n) == ToSeq(value))
     return ok
     # impl-end
 
@@ -123,7 +117,6 @@
 def accepts_unicode(value: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -135,21 +128,17 @@
     n = len(value)
     if n == 0:
         return False
-    i = n
+    i = 0
     ok = True
-    while i > 0:
-        # invariants-start
+    while i < n:
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= n and n == len(value))
-        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = value[i - 1]
-        Assert(ToSeq(value).drop(i - 1)[0] == c)
-        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
+        Invariant(ok == all_unicode_permitted(ToSeq(value).take(i)))
+        c = value[i]
+        Assert(ToSeq(value).take(i + 1).drop(i)[0] == c)
         if not permitted_unicode(c):
             ok = False
-        i = i - 1
-    Assert(ToSeq(value).drop(0) == ToSeq(value))
+        i = i + 1
+    Assert(ToSeq(value).take(n) == ToSeq(value))
     return ok
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11099.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A candidate identifier string is accepted as VALID only when, reading it as a
  sequence of Unicode code points, it is NON-EMPTY and EVERY one of its code
  points belongs to the permitted character class (word characters together
  with the symbols '.', '@', '+', '-'). The acceptance test is anchored to the
  TRUE boundaries of the whole string: the very first code point and the very
  last code point are both inside the run that must consist only of permitted
  characters. In particular a line-feed code point (U+000A) is NOT a permitted
  character, so a string whose final code point is a line feed is REJECTED even
  when every earlier code point is permitted — there is no end-of-string
  tolerance that would let a terminal line feed slip through.

  Two permitted-character regimes are specified: an ASCII regime in which the
  word characters are exactly the ASCII letters, digits, and the low-line; and
  a wider regime in which the word characters additionally include the relevant
  non-ASCII letters and digits. The anchoring behaviour above is identical in
  both regimes.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification. The
permitted-character membership test for each regime is an unchanged callee and
is axiomatized; the whole-string acceptance decision is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def permitted_ascii(c: int) -> bool:
    """Membership of one code point in the ASCII permitted class
    (ASCII letters, digits, low-line, and the symbols '.', '@', '+', '-').
    Unchanged community callee; provenance + executable soundness check:
    mapping.md / axiom_check.py. The line feed U+000A is NOT a member."""
    Ensures(Implies(c == 10, not Result()))          # line feed excluded
    Ensures(Implies(c == 32, not Result()))           # space excluded
    Ensures(Implies(c == 97, Result()))               # 'a' included
    Ensures(Implies(c == 65, Result()))               # 'A' included
    Ensures(Implies(c == 48, Result()))               # '0' included
    Ensures(Implies(c == 45, Result()))               # '-' included
    Ensures(Implies(c == 46, Result()))               # '.' included


@Pure
@ContractOnly
def permitted_unicode(c: int) -> bool:
    """Membership of one code point in the wider permitted class (the word
    characters of the wider regime plus the symbols '.', '@', '+', '-').
    Unchanged community callee; provenance + executable soundness check:
    mapping.md / axiom_check.py. The line feed U+000A is NOT a member."""
    Ensures(Implies(c == 10, not Result()))          # line feed excluded
    Ensures(Implies(c == 32, not Result()))           # space excluded
    Ensures(Implies(c == 97, Result()))               # 'a' included
    Ensures(Implies(c == 233, Result()))              # 'é' included (wider)
    Ensures(Implies(c == 48, Result()))               # '0' included
    Ensures(Implies(c == 45, Result()))               # '-' included
    Ensures(Implies(c == 46, Result()))               # '.' included
# axioms-end


# pure-start
@Pure
def all_ascii_permitted(s: PSeq[int]) -> bool:
    """Every code point of the sequence is in the ASCII permitted class.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return permitted_ascii(s[0]) and all_ascii_permitted(s.drop(1))


@Pure
def all_unicode_permitted(s: PSeq[int]) -> bool:
    """Every code point of the sequence is in the wider permitted class.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return permitted_unicode(s[0]) and all_unicode_permitted(s.drop(1))
# pure-end


def accepts_ascii(value: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    # Accepted iff the WHOLE string is a non-empty run of permitted code points,
    # anchored to both true ends — a terminal line feed is therefore rejected.
    Ensures(Result() == (len(value) >= 1 and all_ascii_permitted(ToSeq(value))))
    # post-conditions-end
    # impl-start
    n = len(value)
    if n == 0:
        return False
    i = n
    ok = True
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= n and n == len(value))
        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
        # invariants-end
        c = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == c)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        if not permitted_ascii(c):
            ok = False
        i = i - 1
    Assert(ToSeq(value).drop(0) == ToSeq(value))
    return ok
    # impl-end


def accepts_unicode(value: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    # Accepted iff the WHOLE string is a non-empty run of permitted code points,
    # anchored to both true ends — a terminal line feed is therefore rejected.
    Ensures(Result() == (len(value) >= 1 and all_unicode_permitted(ToSeq(value))))
    # post-conditions-end
    # impl-start
    n = len(value)
    if n == 0:
        return False
    i = n
    ok = True
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= n and n == len(value))
        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
        # invariants-end
        c = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == c)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        if not permitted_unicode(c):
            ok = False
        i = i - 1
    Assert(ToSeq(value).drop(0) == ToSeq(value))
    return ok
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit of django__django-11099 (nagini).

SPEC SHAPE (why it is tight): both accepts_ascii/accepts_unicode carry a TOTAL functional postcondition `Ensures(Result() == (len(value) >= 1 and all_*_permitted(ToSeq(value))))` with the only precondition being read permission `Requires(Acc(list_pred(value),1/2))` — i.e. NO domain restriction. Result() is fully pinned on the entire input domain, so any verifying impl must return exactly the spec value for every input; there is no slack for a behaviourally-different impl to verify.

POSITIVE CONTROL: pos_control.py (byte-identical to model.py) -> bash scripts/nagini_verify.sh -> Verification successful, 13.09s, exit 0 (log_pos.txt).

ATTACKS (each edits ONLY the two impl regions; spec/axioms/@Pure/Requires/Ensures/Invariant-context byte-identical — machine-confirmed OUTSIDE-IMPL identical for all 7; same-spec exit 0 for all 7).
atk_1 partial-domain (accept any non-empty, drop permitted check): NOT-A-COUNTEREXAMPLE, verification failed, exit 2 (log_w1.txt).
atk_2 boundary off-by-one (loop i>1, ignores the LAST code point — the exact anchoring the fix targets): exit 2 (log_w2.txt).
atk_3 PREPATCH BUG re-encoded ($ semantics: tolerate one trailing line feed via m=n-1 when value[n-1]==10, matching model_prepatch.py): NOT-A-COUNTEREXAMPLE, verification failed, exit 2 (log_w3.txt) — the spec SENSES the bug, prepatch reproduced+rejected.
atk_4 control-flow-effect (early return True on first permitted char): exit 2 (log_w4.txt).
atk_5 ungrounded/inverted oracle (return not ok, empty->True): exit 2 (log_w5.txt).
atk_6 empty-accepted boundary (flip len==0 branch to return True): exit 2 (log_w6.txt).
atk_7 forward-loop echo (structurally different, front-fold take(i) accumulation): exit 2 (log_w7.txt).

RESULT: 0 CANDIDATES. No same-spec wrong impl verifies, so the materialize-faithful-patch-and-resolve obligation is VACUOUS (patches={}); no verify->non-resolve pair exists.

A-LEG AUDIT (refinement.md): every leg is R / A-consumed / A-reference / I; no kind-3. The one changed op (regex end anchor $ -> \Z) is modeled DEEPLY (A5/B4 A-reference: len>=1 and all_*_permitted via front-recursive folds + verified backward loop), not hidden behind an axiom about the function under change. A-consumed axioms (permitted_ascii/permitted_unicode) cover only the UNCHANGED class [\w.@+-]. Executable G-AX (axiom_check.py) exit 0: all 14 membership pins agree with the real re class under matching flags (re.ASCII / flags=0); deep model == real FIXED regex `^[\w.@+-]+\Z` over 13 boundary + 20000 fuzz + 0x2100 single-cp sweep in both regimes, 0 mismatches; deep/buggy disagreements are exactly the lone-trailing-line-feed case. A-reference correspondence to the real callee therefore holds.

VERDICT: SOUND. >=5 distinct wrong impls (7) run through the official weakness harness, positive control verifies, A-legs audited and G-AX-confirmed; nothing breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11099.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A candidate identifier string is accepted as VALID only when, reading it as a
  sequence of Unicode code points, it is NON-EMPTY and EVERY one of its code
  points belongs to the permitted character class (word characters together
  with the symbols '.', '@', '+', '-'). The acceptance test is anchored to the
  TRUE boundaries of the whole string: the very first code point and the very
  last code point are both inside the run that must consist only of permitted
  characters. In particular a line-feed code point (U+000A) is NOT a permitted
  character, so a string whose final code point is a line feed is REJECTED even
  when every earlier code point is permitted — there is no end-of-string
  tolerance that would let a terminal line feed slip through.

  Two permitted-character regimes are specified: an ASCII regime in which the
  word characters are exactly the ASCII letters, digits, and the low-line; and
  a wider regime in which the word characters additionally include the relevant
  non-ASCII letters and digits. The anchoring behaviour above is identical in
  both regimes.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification. The
permitted-character membership test for each regime is an unchanged callee and
is axiomatized; the whole-string acceptance decision is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def permitted_ascii(c: int) -> bool:
    """Membership of one code point in the ASCII permitted class
    (ASCII letters, digits, low-line, and the symbols '.', '@', '+', '-').
    Unchanged community callee; provenance + executable soundness check:
    mapping.md / axiom_check.py. The line feed U+000A is NOT a member."""
    Ensures(Implies(c == 10, not Result()))          # line feed excluded
    Ensures(Implies(c == 32, not Result()))           # space excluded
    Ensures(Implies(c == 97, Result()))               # 'a' included
    Ensures(Implies(c == 65, Result()))               # 'A' included
    Ensures(Implies(c == 48, Result()))               # '0' included
    Ensures(Implies(c == 45, Result()))               # '-' included
    Ensures(Implies(c == 46, Result()))               # '.' included


@Pure
@ContractOnly
def permitted_unicode(c: int) -> bool:
    """Membership of one code point in the wider permitted class (the word
    characters of the wider regime plus the symbols '.', '@', '+', '-').
    Unchanged community callee; provenance + executable soundness check:
    mapping.md / axiom_check.py. The line feed U+000A is NOT a member."""
    Ensures(Implies(c == 10, not Result()))          # line feed excluded
    Ensures(Implies(c == 32, not Result()))           # space excluded
    Ensures(Implies(c == 97, Result()))               # 'a' included
    Ensures(Implies(c == 233, Result()))              # 'é' included (wider)
    Ensures(Implies(c == 48, Result()))               # '0' included
    Ensures(Implies(c == 45, Result()))               # '-' included
    Ensures(Implies(c == 46, Result()))               # '.' included
# axioms-end


# pure-start
@Pure
def all_ascii_permitted(s: PSeq[int]) -> bool:
    """Every code point of the sequence is in the ASCII permitted class.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return permitted_ascii(s[0]) and all_ascii_permitted(s.drop(1))


@Pure
def all_unicode_permitted(s: PSeq[int]) -> bool:
    """Every code point of the sequence is in the wider permitted class.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return permitted_unicode(s[0]) and all_unicode_permitted(s.drop(1))
# pure-end


def accepts_ascii(value: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    # Accepted iff the WHOLE string is a non-empty run of permitted code points,
    # anchored to both true ends — a terminal line feed is therefore rejected.
    Ensures(Result() == (len(value) >= 1 and all_ascii_permitted(ToSeq(value))))
    # post-conditions-end
    # impl-start
    n = len(value)
    if n == 0:
        return False
    i = n
    ok = True
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= n and n == len(value))
        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))
        # invariants-end
        c = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == c)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        if not permitted_ascii(c):
            ok = False
        i = i - 1
    Assert(ToSeq(value).drop(0) == ToSeq(value))
    return ok
    # impl-end


def accepts_unicode(value: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    # Accepted iff the WHOLE string is a non-empty run of permitted code points,
    # anchored to both true ends — a terminal line feed is therefore rejected.
    Ensures(Result() == (len(value) >= 1 and all_unicode_permitted(ToSeq(value))))
    # post-conditions-end
    # impl-start
    n = len(value)
    if n == 0:
        return False
    i = n
    ok = True
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= n and n == len(value))
        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))
        # invariants-end
        c = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == c)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        if not permitted_unicode(c):
            ok = False
        i = i - 1
    Assert(ToSeq(value).drop(0) == ToSeq(value))
    return ok
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit of django__django-11099 (nagini).

SPEC SHAPE (why it is tight): both accepts_ascii/accepts_unicode carry a TOTAL functional postcondition `Ensures(Result() == (len(value) >= 1 and all_*_permitted(ToSeq(value))))` with the only precondition being read permission `Requires(Acc(list_pred(value),1/2))` — i.e. NO domain restriction. Result() is fully pinned on the entire input domain, so any verifying impl must return exactly the spec value for every input; there is no slack for a behaviourally-different impl to verify.

POSITIVE CONTROL: pos_control.py (byte-identical to model.py) -> bash scripts/nagini_verify.sh -> Verification successful, 13.09s, exit 0 (log_pos.txt).

ATTACKS (each edits ONLY the two impl regions; spec/axioms/@Pure/Requires/Ensures/Invariant-context byte-identical — machine-confirmed OUTSIDE-IMPL identical for all 7; same-spec exit 0 for all 7).
atk_1 partial-domain (accept any non-empty, drop permitted check): NOT-A-COUNTEREXAMPLE, verification failed, exit 2 (log_w1.txt).
atk_2 boundary off-by-one (loop i>1, ignores the LAST code point — the exact anchoring the fix targets): exit 2 (log_w2.txt).
atk_3 PREPATCH BUG re-encoded ($ semantics: tolerate one trailing line feed via m=n-1 when value[n-1]==10, matching model_prepatch.py): NOT-A-COUNTEREXAMPLE, verification failed, exit 2 (log_w3.txt) — the spec SENSES the bug, prepatch reproduced+rejected.
atk_4 control-flow-effect (early return True on first permitted char): exit 2 (log_w4.txt).
atk_5 ungrounded/inverted oracle (return not ok, empty->True): exit 2 (log_w5.txt).
atk_6 empty-accepted boundary (flip len==0 branch to return True): exit 2 (log_w6.txt).
atk_7 forward-loop echo (structurally different, front-fold take(i) accumulation): exit 2 (log_w7.txt).

RESULT: 0 CANDIDATES. No same-spec wrong impl verifies, so the materialize-faithful-patch-and-resolve obligation is VACUOUS (patches={}); no verify->non-resolve pair exists.

A-LEG AUDIT (refinement.md): every leg is R / A-consumed / A-reference / I; no kind-3. The one changed op (regex end anchor $ -> \Z) is modeled DEEPLY (A5/B4 A-reference: len>=1 and all_*_permitted via front-recursive folds + verified backward loop), not hidden behind an axiom about the function under change. A-consumed axioms (permitted_ascii/permitted_unicode) cover only the UNCHANGED class [\w.@+-]. Executable G-AX (axiom_check.py) exit 0: all 14 membership pins agree with the real re class under matching flags (re.ASCII / flags=0); deep model == real FIXED regex `^[\w.@+-]+\Z` over 13 boundary + 20000 fuzz + 0x2100 single-cp sweep in both regimes, 0 mismatches; deep/buggy disagreements are exactly the lone-trailing-line-feed case. A-reference correspondence to the real callee therefore holds.

VERDICT: SOUND. >=5 distinct wrong impls (7) run through the official weakness harness, positive control verifies, A-legs audited and G-AX-confirmed; nothing breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-11099 nagini bundle. Task: determine whether the spec is too strong / drifts from the real repo (modeled function disagreeing with the real callee on some input). Conclusion: FAITHFUL — no divergence found.

Mandate checks:
1. Spec byte-identity: `python -m swebench_unified.adversary same-spec nagini django__django-11099 <prepatch>` -> exit 0 (SAME). The frozen postcondition is `Result() == (len(value) >= 1 and all_*_permitted(ToSeq(value)))`, modeling the fixed validator regex `^[\w.@+-]+\Z` under re.ASCII / flags=0.
2. Model verifies: `nagini_verify.sh model.py` -> Verification successful (12.77s, exit 0).
3. Spec is bug-sensitive (not vacuous / not too weak on the delta): the prepatch reproducing the buggy `$` semantics (tolerating one terminal line feed) FAILS to verify against the spec — `adversary weakness` exit 2, "spec rejected this impl (good)". So the spec correctly requires rejecting a trailing-LF string like [97,10].

Faithfulness (is the spec TOO STRONG / drifting from real repo?): I ran an INDEPENDENT differential test (not the bundle's) comparing the deep model `deep(value)=len>=1 and all(member(cls,c))` against the REAL patched regex `^[\w.@+-]+\Z` under BOTH flag regimes over: full BMP + astral sweeps (0x0-0x11000, 0x1F000-0x1F800, 0x10FF00-0x110000) in 5 positional contexts, plus 300,000 random fuzz strings whose alphabet included line separators U+000A/000D/0085/2028/2029, NBSP, ZWSP, vertical tab/form feed, and astral code points. RESULT: 0 mismatches. The bundle's own axiom_check.py (stdlib, re engine — same engine the patched code uses) also passes: membership axioms sound on every pinned clause; deep model == real FIXED regex over 13 boundary + 20000 fuzz + 0x2100 single-cp sweep in both regimes; deep/buggy disagreements are exactly the lone-trailing-LF case.

The membership axioms (permitted_ascii/permitted_unicode) are the WEAKEST sufficient contract — they pin only LF/space excluded and a handful of included points (a,A/é,0,-,.), asserting nothing about unpinned code points, so they cannot be stronger than the real class. G-AX confirms every pinned clause matches the real `[\w.@+-]` class element-wise across the whole sweep. The whole-string decision is modeled deeply and equals the real fixed regex exactly. No input exists where the modeled function disagrees with the real patched repo callee. Spec is neither too strong nor drifting: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `$`->`\Z` in both username-validator regexes so a trailing newline is rejected. The public problem_statement ALREADY discloses the entire fix verbatim: it shows the buggy regex r'^[\w.@+-]+$', explains that `$` matches a trailing newline (so usernames ending in newline are wrongly accepted), and states the fix is r'\A[\w.@+-]+\Z' 'in order to reject usernames that end with a newline' in the two contrib.auth.validators. So the newline-rejection behavior is fully public. The spec view (spec_view over model.py) contains ONLY abstract desired behavior: acceptance iff non-empty and every code point in the permitted class, with a terminal U+000A rejected ('no end-of-string tolerance'), across an ASCII regime and a wider regime. It uses only model symbols (accepts_ascii/unicode, permitted_ascii/unicode, all_*_permitted) — no repo symbols (ASCIIUsernameValidator, RegexValidator, regex), no regex tokens ($, \Z, [\w.@+-]), no diff markers, no patched file path, no bug/fix narration. Mechanical G-LEAK screen: passed=True, hard_failures=[]. Every substantive spec-view claim, including the terminal-line-feed rejection that is the crux of the gold edit, lies entirely within problem_statement's disclosure and does not draw on hints_text (empty). Describing the desired post-fix behavior is the spec's job and here that behavior is already public. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
