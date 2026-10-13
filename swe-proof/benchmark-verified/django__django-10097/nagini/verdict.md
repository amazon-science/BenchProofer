# P2 adversarial audit — django__django-10097

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def validate_authsegment(seg: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(seg), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(seg), 1 / 2))
@@ -102,43 +100,5 @@
     Ensures(Result() == accepts(ToSeq(seg)))
     # post-conditions-end
     # impl-start
-    n = len(seg)
-    if n == 0:
-        Assert(len(ToSeq(seg)) == 0)
-        return False
-    Assert(ToSeq(seg)[0] == seg[0])
-    if seg[0] == 58:
-        return False
-    good = True
-    ncolon = 0
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(seg), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(seg))
-        Invariant(seg[0] != 58)
-        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
-        Invariant(good == body_ok(ToSeq(seg).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = seg[i - 1]
-        # drop(i-1) == [seg[i-1]] ++ drop(i) : peel the first element of the suffix
-        Assert(ToSeq(seg).drop(i - 1)[0] == c)
-        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
-        if c == 58:
-            ncolon = ncolon + 1
-        elif not is_uchar(c):
-            good = False
-        i = i - 1
-    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
-    Assert(good == body_ok(ToSeq(seg)))
-    Assert(ncolon == colons(ToSeq(seg)))
-    Assert(len(ToSeq(seg)) > 0)
-    Assert(ToSeq(seg)[0] == seg[0])
-    Assert(ToSeq(seg)[0] != 58)
-    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
-                                   and colons(ToSeq(seg)) <= 1
-                                   and ToSeq(seg)[0] != 58))
-    return good and ncolon <= 1
+    return True
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def validate_authsegment(seg: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(seg), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(seg), 1 / 2))
@@ -102,43 +100,6 @@
     Ensures(Result() == accepts(ToSeq(seg)))
     # post-conditions-end
     # impl-start
-    n = len(seg)
-    if n == 0:
-        Assert(len(ToSeq(seg)) == 0)
-        return False
-    Assert(ToSeq(seg)[0] == seg[0])
-    if seg[0] == 58:
-        return False
-    good = True
-    ncolon = 0
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(seg), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(seg))
-        Invariant(seg[0] != 58)
-        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
-        Invariant(good == body_ok(ToSeq(seg).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = seg[i - 1]
-        # drop(i-1) == [seg[i-1]] ++ drop(i) : peel the first element of the suffix
-        Assert(ToSeq(seg).drop(i - 1)[0] == c)
-        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
-        if c == 58:
-            ncolon = ncolon + 1
-        elif not is_uchar(c):
-            good = False
-        i = i - 1
-    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
-    Assert(good == body_ok(ToSeq(seg)))
-    Assert(ncolon == colons(ToSeq(seg)))
-    Assert(len(ToSeq(seg)) > 0)
-    Assert(ToSeq(seg)[0] == seg[0])
-    Assert(ToSeq(seg)[0] != 58)
-    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
-                                   and colons(ToSeq(seg)) <= 1
-                                   and ToSeq(seg)[0] != 58))
-    return good and ncolon <= 1
+    return (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
+            and colons(ToSeq(seg)) <= 2 and ToSeq(seg)[0] != 58)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def validate_authsegment(seg: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(seg), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(seg), 1 / 2))
@@ -102,43 +100,6 @@
     Ensures(Result() == accepts(ToSeq(seg)))
     # post-conditions-end
     # impl-start
-    n = len(seg)
-    if n == 0:
-        Assert(len(ToSeq(seg)) == 0)
-        return False
-    Assert(ToSeq(seg)[0] == seg[0])
-    if seg[0] == 58:
-        return False
-    good = True
-    ncolon = 0
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(seg), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(seg))
-        Invariant(seg[0] != 58)
-        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
-        Invariant(good == body_ok(ToSeq(seg).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = seg[i - 1]
-        # drop(i-1) == [seg[i-1]] ++ drop(i) : peel the first element of the suffix
-        Assert(ToSeq(seg).drop(i - 1)[0] == c)
-        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
-        if c == 58:
-            ncolon = ncolon + 1
-        elif not is_uchar(c):
-            good = False
-        i = i - 1
-    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
-    Assert(good == body_ok(ToSeq(seg)))
-    Assert(ncolon == colons(ToSeq(seg)))
-    Assert(len(ToSeq(seg)) > 0)
-    Assert(ToSeq(seg)[0] == seg[0])
-    Assert(ToSeq(seg)[0] != 58)
-    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
-                                   and colons(ToSeq(seg)) <= 1
-                                   and ToSeq(seg)[0] != 58))
-    return good and ncolon <= 1
+    return (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
+            and colons(ToSeq(seg)) <= 1)
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def validate_authsegment(seg: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(seg), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(seg), 1 / 2))
@@ -102,43 +100,5 @@
     Ensures(Result() == accepts(ToSeq(seg)))
     # post-conditions-end
     # impl-start
-    n = len(seg)
-    if n == 0:
-        Assert(len(ToSeq(seg)) == 0)
-        return False
-    Assert(ToSeq(seg)[0] == seg[0])
-    if seg[0] == 58:
-        return False
-    good = True
-    ncolon = 0
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(seg), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(seg))
-        Invariant(seg[0] != 58)
-        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
-        Invariant(good == body_ok(ToSeq(seg).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = seg[i - 1]
-        # drop(i-1) == [seg[i-1]] ++ drop(i) : peel the first element of the suffix
-        Assert(ToSeq(seg).drop(i - 1)[0] == c)
-        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
-        if c == 58:
-            ncolon = ncolon + 1
-        elif not is_uchar(c):
-            good = False
-        i = i - 1
-    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
-    Assert(good == body_ok(ToSeq(seg)))
-    Assert(ncolon == colons(ToSeq(seg)))
-    Assert(len(ToSeq(seg)) > 0)
-    Assert(ToSeq(seg)[0] == seg[0])
-    Assert(ToSeq(seg)[0] != 58)
-    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
-                                   and colons(ToSeq(seg)) <= 1
-                                   and ToSeq(seg)[0] != 58))
-    return good and ncolon <= 1
+    return accepts(ToSeq(seg))
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def validate_authsegment(seg: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(seg), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(seg), 1 / 2))
@@ -102,43 +100,5 @@
     Ensures(Result() == accepts(ToSeq(seg)))
     # post-conditions-end
     # impl-start
-    n = len(seg)
-    if n == 0:
-        Assert(len(ToSeq(seg)) == 0)
-        return False
-    Assert(ToSeq(seg)[0] == seg[0])
-    if seg[0] == 58:
-        return False
-    good = True
-    ncolon = 0
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(seg), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(seg))
-        Invariant(seg[0] != 58)
-        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
-        Invariant(good == body_ok(ToSeq(seg).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = seg[i - 1]
-        # drop(i-1) == [seg[i-1]] ++ drop(i) : peel the first element of the suffix
-        Assert(ToSeq(seg).drop(i - 1)[0] == c)
-        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
-        if c == 58:
-            ncolon = ncolon + 1
-        elif not is_uchar(c):
-            good = False
-        i = i - 1
-    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
-    Assert(good == body_ok(ToSeq(seg)))
-    Assert(ncolon == colons(ToSeq(seg)))
-    Assert(len(ToSeq(seg)) > 0)
-    Assert(ToSeq(seg)[0] == seg[0])
-    Assert(ToSeq(seg)[0] != 58)
-    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
-                                   and colons(ToSeq(seg)) <= 1
-                                   and ToSeq(seg)[0] != 58))
-    return good and ncolon <= 1
+    return accepts(ToSeq(seg)) or (len(ToSeq(seg)) > 0 and ToSeq(seg)[0] == 47)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def validate_authsegment(seg: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(seg), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(seg), 1 / 2))
@@ -104,41 +102,18 @@
     # impl-start
     n = len(seg)
     if n == 0:
-        Assert(len(ToSeq(seg)) == 0)
         return False
-    Assert(ToSeq(seg)[0] == seg[0])
-    if seg[0] == 58:
-        return False
-    good = True
-    ncolon = 0
+    nonws = True
     i = n
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(seg), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(seg))
-        Invariant(seg[0] != 58)
-        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
-        Invariant(good == body_ok(ToSeq(seg).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = seg[i - 1]
-        # drop(i-1) == [seg[i-1]] ++ drop(i) : peel the first element of the suffix
-        Assert(ToSeq(seg).drop(i - 1)[0] == c)
-        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
-        if c == 58:
-            ncolon = ncolon + 1
-        elif not is_uchar(c):
-            good = False
+        if is_whitespace(c):
+            nonws = False
         i = i - 1
-    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
-    Assert(good == body_ok(ToSeq(seg)))
-    Assert(ncolon == colons(ToSeq(seg)))
-    Assert(len(ToSeq(seg)) > 0)
-    Assert(ToSeq(seg)[0] == seg[0])
-    Assert(ToSeq(seg)[0] != 58)
-    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
-                                   and colons(ToSeq(seg)) <= 1
-                                   and ToSeq(seg)[0] != 58))
-    return good and ncolon <= 1
+    return nonws
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -94,7 +93,6 @@
 def validate_authsegment(seg: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(seg), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(seg), 1 / 2))
@@ -102,43 +100,6 @@
     Ensures(Result() == accepts(ToSeq(seg)))
     # post-conditions-end
     # impl-start
-    n = len(seg)
-    if n == 0:
-        Assert(len(ToSeq(seg)) == 0)
-        return False
-    Assert(ToSeq(seg)[0] == seg[0])
-    if seg[0] == 58:
-        return False
-    good = True
-    ncolon = 0
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(seg), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(seg))
-        Invariant(seg[0] != 58)
-        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
-        Invariant(good == body_ok(ToSeq(seg).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = seg[i - 1]
-        # drop(i-1) == [seg[i-1]] ++ drop(i) : peel the first element of the suffix
-        Assert(ToSeq(seg).drop(i - 1)[0] == c)
-        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
-        if c == 58:
-            ncolon = ncolon + 1
-        elif not is_uchar(c):
-            good = False
-        i = i - 1
-    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
-    Assert(good == body_ok(ToSeq(seg)))
-    Assert(ncolon == colons(ToSeq(seg)))
-    Assert(len(ToSeq(seg)) > 0)
-    Assert(ToSeq(seg)[0] == seg[0])
-    Assert(ToSeq(seg)[0] != 58)
-    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
-                                   and colons(ToSeq(seg)) <= 1
-                                   and ToSeq(seg)[0] != 58))
-    return good and ncolon <= 1
+    return (len(ToSeq(seg)) > 0 and colons(ToSeq(seg)) <= 1
+            and ToSeq(seg)[0] != 58)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for django__django-10097.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A URL may optionally carry a leading authentication segment (the text that
  appears before the host and is terminated by a literal ``@``). RFC 1738
  section 3.1 requires that within that segment any ``":"``, ``"@"`` or ``"/"``
  be percent-encoded; whitespace is likewise not permitted. The acceptance
  predicate for a candidate authentication segment is therefore:

    * the segment is non-empty;
    * it may be split at most once by a single ``":"`` separator into a
      *user* run followed by an optional *password* run;
    * the user run (the text before that separator, or the whole segment when
      there is no separator) is non-empty;
    * every code point other than that one permitted separator colon is an
      "authentication character": it is none of whitespace, ``":"``,
      ``"@"`` or ``"/"``.

A segment is accepted iff all four hold. The discriminating cases are segments
that smuggle an unencoded ``"/"``, ``"@"`` or a second ``":"`` into the user or
password: those must be rejected.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``.
The acceptance predicate is modelled DEEPLY as front-recursive ``@Pure``
sequence predicates (no consumed axiom); its equality to the real compiled
matcher is checked out-of-band by axiom_check.py (G-AX), not consumed here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none — the changed operation is modelled deeply; the real compiled matcher
#  is an A-reference validated by axiom_check.py / G-AX, not a consumed axiom.)
# axioms-end

# pure-start
@Pure
def is_whitespace(c: int) -> bool:
    """The full set of whitespace code points (the Unicode whitespace class):
    the ASCII run ``{9..13, 32}`` together with the C1/separator code points
    ``{0x1c..0x1f, 0x85, 0xa0, 0x1680, 0x2000..0x200a, 0x2028, 0x2029,
    0x202f, 0x205f, 0x3000}``. A character is whitespace iff it lies in this
    set."""
    return ((9 <= c and c <= 13) or c == 32
            or (0x1c <= c and c <= 0x1f) or c == 0x85 or c == 0xa0
            or c == 0x1680 or (0x2000 <= c and c <= 0x200a)
            or c == 0x2028 or c == 0x2029 or c == 0x202f
            or c == 0x205f or c == 0x3000)

@Pure
def is_uchar(c: int) -> bool:
    """A single authentication character: every code point EXCEPT whitespace
    and the three RFC-1738 separators that must be encoded — ``":"`` (58),
    ``"@"`` (64) and ``"/"`` (47)."""
    return not is_whitespace(c) and c != 58 and c != 64 and c != 47

@Pure
def body_ok(s: PSeq[int]) -> bool:
    """Every code point is either an authentication character or the single
    permitted separator colon (58). Front-recursive: one unfold per step."""
    if len(s) == 0:
        return True
    return (is_uchar(s[0]) or s[0] == 58) and body_ok(s.drop(1))

@Pure
def colons(s: PSeq[int]) -> int:
    """Number of separator colons (code point 58) in the segment.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return 0
    return (1 if s[0] == 58 else 0) + colons(s.drop(1))

@Pure
def accepts(s: PSeq[int]) -> bool:
    """The authentication segment ``s`` (the text before the terminating
    ``@``) is accepted iff it is non-empty, contains only authentication
    characters apart from at most one separator colon, and does not begin with
    that colon (the user run is non-empty)."""
    return len(s) > 0 and body_ok(s) and colons(s) <= 1 and s[0] != 58
# pure-end

def validate_authsegment(seg: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(seg), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seg), 1 / 2))
    # The decision is exactly the structural acceptance predicate on the input.
    Ensures(Result() == accepts(ToSeq(seg)))
    # post-conditions-end
    # impl-start
    n = len(seg)
    if n == 0:
        Assert(len(ToSeq(seg)) == 0)
        return False
    Assert(ToSeq(seg)[0] == seg[0])
    if seg[0] == 58:
        return False
    good = True
    ncolon = 0
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(seg), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(seg))
        Invariant(seg[0] != 58)
        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
        Invariant(good == body_ok(ToSeq(seg).drop(i)))
        # invariants-end
        c = seg[i - 1]
        Assert(ToSeq(seg).drop(i - 1)[0] == c)
        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
        if c == 58:
            ncolon = ncolon + 1
        elif not is_uchar(c):
            good = False
        i = i - 1
    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
    Assert(good == body_ok(ToSeq(seg)))
    Assert(ncolon == colons(ToSeq(seg)))
    Assert(len(ToSeq(seg)) > 0)
    Assert(ToSeq(seg)[0] == seg[0])
    Assert(ToSeq(seg)[0] != 58)
    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
                                   and colons(ToSeq(seg)) <= 1
                                   and ToSeq(seg)[0] != 58))
    return good and ncolon <= 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. The spec cannot be broken (verify does NOT fail to imply correct here).

SPEC SHAPE (root cause of soundness): validate_authsegment's precondition places NO value restriction (only Acc(list_pred(seg),1/2)); its postcondition is a TOTAL functional biconditional Ensures(Result() == accepts(ToSeq(seg))). Therefore ANY same-spec impl that verifies is forced to equal the deep model `accepts` on every input in the whole domain -> its faithful refined patch is the gold behavior. A wrong impl (differing from accepts on any input) cannot verify.

ATTACKS (7 distinct same-spec wrong impls; all confirmed SAME-SPEC by official `adversary same-spec` and byte-identical spec-region sha256 7ed9c32421c7; run via `adversary weakness nagini django__django-10097 <path>` on env python, SBU_BENCHMARK_DIR=benchmark-verified, concurrently <=3 at a time):
  - atk_1.py total-accept `return True` (partial-domain/ungrounded): rc=2 NOT-A-COUNTEREXAMPLE (verification failed) — wrong on '', ':', 'foo/bar'.
  - atk_2.py boundary off-by-one `colons<=2`: rc=2 verification failed — wrong on 'foo:bar:baz'.
  - atk_3.py control-flow-effect: drop leading-colon reject: rc=2 verification failed — wrong on ':x'.
  - atk_4.py ungrounded-oracle ECHO `return accepts(ToSeq(seg))`: rc=0 CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 10.7s). [see resolve below]
  - atk_5.py accept leading unencoded '/': rc=2 verification failed — wrong on '/x'.
  - atk_6.py prepatch-shaped whitespace-only (\S+ semantics): rc=2 verification failed — wrong on 'foo/bar'.
  - atk_7.py ignore body_ok (accept any <=1-colon non-leading-colon segment): rc=2 verification failed — wrong on 'foo/bar','foo@bar'.
Only the echo verifies — exactly as a total biconditional demands.

MANDATORY RESOLVE OF THE VERIFYING CANDIDATE (atk_4): its faithful refined patch computes exactly `accepts` = the gold userinfo-regex behavior, so the materialized patch is atk_4.patch (BYTE-IDENTICAL to the gold patch, verified via difflib against dataset row). EXECUTED through the official harness: swebench_unified.harness.run_resolve('django__django-10097', patch, timeout=1800, retries=1) -> RESOLVED: True, COMPLETED: True (log atk_4.resolve.log; the trailing AttributeError is only my print of a nonexistent r.summary attr, AFTER resolved=True was read from the harness report). So the sole verifying candidate RESOLVES => spec is NOT broken.

**POSITIVE CONTROL:** atk_pc.py = gold impl region verbatim -> `bash scripts/nagini_verify.sh` rc=0, 'Verification successful' (11.46s).

**PREPATCH REPRODUCED:** model_prepatch.py (whitespace-only \S+ skeleton) -> nagini_verify rc=1, fails EXACTLY on 'Postcondition ... Result() == accepts(ToSeq(seg)) might not hold' (model.py:100) — the spec senses the change (G-DIFF).

A-LEG (A-reference) INDEPENDENT AUDIT (the G-EQ-relevant leg; R/I legs covered by G-CONF): refinement.md classifies A1=R (str<->List[int]), A2=I (n==0 vs `+`), A3=I (leading colon vs non-empty user run), A4=A-reference (deep model accepts/body_ok/colons/is_uchar == compiled group [^\s:@/]+(?::[^\s:@/]*)? validated out-of-band by G-AX). NO consumed axiom (axioms region empty) and NO kind-3 leg — the single changed op (the matcher) is modeled deeply and validated as an A-reference; classification is correct.

I independently re-encoded `accepts` (NOT importing the bundle) and ran a differential vs the REAL gold regex re.compile(r'[^\s:@/]+(?::[^\s:@/]*)?', re.IGNORECASE).fullmatch: 0 mismatches over exhaustive alphabet<=len4 (incl :,@,/,space,\t,\xa0,ideographic-space,accent,emoji), full per-codepoint sweep 0..0x3100 alone+embedded, all issue cases, and 200000 random fuzz. Also verified the model's enumerated 29-codepoint whitespace set == Python's actual re `\s` set EXACTLY (set-equality over 0..0x10FFFF), so the A-reference correspondence is universal, not ASCII-only. axiom_check.py compiles the real group with the same IGNORECASE flag and imports only stdlib `re` (the engine the gold regex uses) — grounded, not circular.

**CONCLUSION:** >=5 (7) distinct same-spec wrong impls run; 6 rejected by verification, the 1 that verifies (echo) has a faithful patch that RESOLVES under run_resolve. A-reference independently confirmed sound. No verify⇒incorrect witness exists. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for django__django-10097.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A URL may optionally carry a leading authentication segment (the text that
  appears before the host and is terminated by a literal ``@``). RFC 1738
  section 3.1 requires that within that segment any ``":"``, ``"@"`` or ``"/"``
  be percent-encoded; whitespace is likewise not permitted. The acceptance
  predicate for a candidate authentication segment is therefore:

    * the segment is non-empty;
    * it may be split at most once by a single ``":"`` separator into a
      *user* run followed by an optional *password* run;
    * the user run (the text before that separator, or the whole segment when
      there is no separator) is non-empty;
    * every code point other than that one permitted separator colon is an
      "authentication character": it is none of whitespace, ``":"``,
      ``"@"`` or ``"/"``.

A segment is accepted iff all four hold. The discriminating cases are segments
that smuggle an unencoded ``"/"``, ``"@"`` or a second ``":"`` into the user or
password: those must be rejected.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``.
The acceptance predicate is modelled DEEPLY as front-recursive ``@Pure``
sequence predicates (no consumed axiom); its equality to the real compiled
matcher is checked out-of-band by axiom_check.py (G-AX), not consumed here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none — the changed operation is modelled deeply; the real compiled matcher
#  is an A-reference validated by axiom_check.py / G-AX, not a consumed axiom.)
# axioms-end

# pure-start
@Pure
def is_whitespace(c: int) -> bool:
    """The full set of whitespace code points (the Unicode whitespace class):
    the ASCII run ``{9..13, 32}`` together with the C1/separator code points
    ``{0x1c..0x1f, 0x85, 0xa0, 0x1680, 0x2000..0x200a, 0x2028, 0x2029,
    0x202f, 0x205f, 0x3000}``. A character is whitespace iff it lies in this
    set."""
    return ((9 <= c and c <= 13) or c == 32
            or (0x1c <= c and c <= 0x1f) or c == 0x85 or c == 0xa0
            or c == 0x1680 or (0x2000 <= c and c <= 0x200a)
            or c == 0x2028 or c == 0x2029 or c == 0x202f
            or c == 0x205f or c == 0x3000)

@Pure
def is_uchar(c: int) -> bool:
    """A single authentication character: every code point EXCEPT whitespace
    and the three RFC-1738 separators that must be encoded — ``":"`` (58),
    ``"@"`` (64) and ``"/"`` (47)."""
    return not is_whitespace(c) and c != 58 and c != 64 and c != 47

@Pure
def body_ok(s: PSeq[int]) -> bool:
    """Every code point is either an authentication character or the single
    permitted separator colon (58). Front-recursive: one unfold per step."""
    if len(s) == 0:
        return True
    return (is_uchar(s[0]) or s[0] == 58) and body_ok(s.drop(1))

@Pure
def colons(s: PSeq[int]) -> int:
    """Number of separator colons (code point 58) in the segment.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return 0
    return (1 if s[0] == 58 else 0) + colons(s.drop(1))

@Pure
def accepts(s: PSeq[int]) -> bool:
    """The authentication segment ``s`` (the text before the terminating
    ``@``) is accepted iff it is non-empty, contains only authentication
    characters apart from at most one separator colon, and does not begin with
    that colon (the user run is non-empty)."""
    return len(s) > 0 and body_ok(s) and colons(s) <= 1 and s[0] != 58
# pure-end

def validate_authsegment(seg: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(seg), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seg), 1 / 2))
    # The decision is exactly the structural acceptance predicate on the input.
    Ensures(Result() == accepts(ToSeq(seg)))
    # post-conditions-end
    # impl-start
    n = len(seg)
    if n == 0:
        Assert(len(ToSeq(seg)) == 0)
        return False
    Assert(ToSeq(seg)[0] == seg[0])
    if seg[0] == 58:
        return False
    good = True
    ncolon = 0
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(seg), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(seg))
        Invariant(seg[0] != 58)
        Invariant(ncolon == colons(ToSeq(seg).drop(i)))
        Invariant(good == body_ok(ToSeq(seg).drop(i)))
        # invariants-end
        c = seg[i - 1]
        Assert(ToSeq(seg).drop(i - 1)[0] == c)
        Assert(ToSeq(seg).drop(i - 1).drop(1) == ToSeq(seg).drop(i))
        if c == 58:
            ncolon = ncolon + 1
        elif not is_uchar(c):
            good = False
        i = i - 1
    Assert(ToSeq(seg).drop(0) == ToSeq(seg))
    Assert(good == body_ok(ToSeq(seg)))
    Assert(ncolon == colons(ToSeq(seg)))
    Assert(len(ToSeq(seg)) > 0)
    Assert(ToSeq(seg)[0] == seg[0])
    Assert(ToSeq(seg)[0] != 58)
    Assert(accepts(ToSeq(seg)) == (len(ToSeq(seg)) > 0 and body_ok(ToSeq(seg))
                                   and colons(ToSeq(seg)) <= 1
                                   and ToSeq(seg)[0] != 58))
    return good and ncolon <= 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. The spec cannot be broken (verify does NOT fail to imply correct here).

SPEC SHAPE (root cause of soundness): validate_authsegment's precondition places NO value restriction (only Acc(list_pred(seg),1/2)); its postcondition is a TOTAL functional biconditional Ensures(Result() == accepts(ToSeq(seg))). Therefore ANY same-spec impl that verifies is forced to equal the deep model `accepts` on every input in the whole domain -> its faithful refined patch is the gold behavior. A wrong impl (differing from accepts on any input) cannot verify.

ATTACKS (7 distinct same-spec wrong impls; all confirmed SAME-SPEC by official `adversary same-spec` and byte-identical spec-region sha256 7ed9c32421c7; run via `adversary weakness nagini django__django-10097 <path>` on env python, SBU_BENCHMARK_DIR=benchmark-verified, concurrently <=3 at a time):
  - atk_1.py total-accept `return True` (partial-domain/ungrounded): rc=2 NOT-A-COUNTEREXAMPLE (verification failed) — wrong on '', ':', 'foo/bar'.
  - atk_2.py boundary off-by-one `colons<=2`: rc=2 verification failed — wrong on 'foo:bar:baz'.
  - atk_3.py control-flow-effect: drop leading-colon reject: rc=2 verification failed — wrong on ':x'.
  - atk_4.py ungrounded-oracle ECHO `return accepts(ToSeq(seg))`: rc=0 CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 10.7s). [see resolve below]
  - atk_5.py accept leading unencoded '/': rc=2 verification failed — wrong on '/x'.
  - atk_6.py prepatch-shaped whitespace-only (\S+ semantics): rc=2 verification failed — wrong on 'foo/bar'.
  - atk_7.py ignore body_ok (accept any <=1-colon non-leading-colon segment): rc=2 verification failed — wrong on 'foo/bar','foo@bar'.
Only the echo verifies — exactly as a total biconditional demands.

MANDATORY RESOLVE OF THE VERIFYING CANDIDATE (atk_4): its faithful refined patch computes exactly `accepts` = the gold userinfo-regex behavior, so the materialized patch is atk_4.patch (BYTE-IDENTICAL to the gold patch, verified via difflib against dataset row). EXECUTED through the official harness: swebench_unified.harness.run_resolve('django__django-10097', patch, timeout=1800, retries=1) -> RESOLVED: True, COMPLETED: True (log atk_4.resolve.log; the trailing AttributeError is only my print of a nonexistent r.summary attr, AFTER resolved=True was read from the harness report). So the sole verifying candidate RESOLVES => spec is NOT broken.

**POSITIVE CONTROL:** atk_pc.py = gold impl region verbatim -> `bash scripts/nagini_verify.sh` rc=0, 'Verification successful' (11.46s).

**PREPATCH REPRODUCED:** model_prepatch.py (whitespace-only \S+ skeleton) -> nagini_verify rc=1, fails EXACTLY on 'Postcondition ... Result() == accepts(ToSeq(seg)) might not hold' (model.py:100) — the spec senses the change (G-DIFF).

A-LEG (A-reference) INDEPENDENT AUDIT (the G-EQ-relevant leg; R/I legs covered by G-CONF): refinement.md classifies A1=R (str<->List[int]), A2=I (n==0 vs `+`), A3=I (leading colon vs non-empty user run), A4=A-reference (deep model accepts/body_ok/colons/is_uchar == compiled group [^\s:@/]+(?::[^\s:@/]*)? validated out-of-band by G-AX). NO consumed axiom (axioms region empty) and NO kind-3 leg — the single changed op (the matcher) is modeled deeply and validated as an A-reference; classification is correct.

I independently re-encoded `accepts` (NOT importing the bundle) and ran a differential vs the REAL gold regex re.compile(r'[^\s:@/]+(?::[^\s:@/]*)?', re.IGNORECASE).fullmatch: 0 mismatches over exhaustive alphabet<=len4 (incl :,@,/,space,\t,\xa0,ideographic-space,accent,emoji), full per-codepoint sweep 0..0x3100 alone+embedded, all issue cases, and 200000 random fuzz. Also verified the model's enumerated 29-codepoint whitespace set == Python's actual re `\s` set EXACTLY (set-equality over 0..0x10FFFF), so the A-reference correspondence is universal, not ASCII-only. axiom_check.py compiles the real group with the same IGNORECASE flag and imports only stdlib `re` (the engine the gold regex uses) — grounded, not circular.

**CONCLUSION:** >=5 (7) distinct same-spec wrong impls run; 6 rejected by verification, the 1 that verifies (echo) has a faithful patch that RESOLVES under run_resolve. A-reference independently confirmed sound. No verify⇒incorrect witness exists. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 faithfulness audit of django__django-10097/nagini. The modeled function validate_authsegment specs Result() == accepts(ToSeq(seg)), where accepts is a deep @Pure model of the post-patch URLValidator userinfo group [^\s:@/]+(?::[^\s:@/]*)? (re.IGNORECASE). I checked whether this modeled predicate drifts from real repo behavior (the compiled matcher) and found no divergence:

1. Whitespace set fidelity: model.py's is_whitespace enumerates exactly the 29 code points Python's re \s matches (verified by exhaustive scan of all 0x110000 code points: real_ws == model_ws, both symmetric-diff empty). So not is_whitespace is exactly [^\s]; is_uchar is the exact complement of [\s:@/]. The refinement note documents a prior ASCII-only hole (e.g. foo\xa0bar) that has been correctly closed.

2. Exhaustive single-code-point sweep (all 0x110000): model's accepts on single chars == USERINFO.fullmatch — 0 mismatches.

3. Independent 500k broad fuzz (astral emoji, all whitespace variants, separators, latin-1, zero-width) plus the bundle's own axiom_check.py (RC=0, 188 boundary + full 29-codepoint whitespace sweep + 100k fuzz): 0 mismatches.

4. Targeted boundary strings (foo:, foo::, a:b:c, :, :x, xxx:, a:@, foo:​, :😀, etc.): all agree. The tricky cases — empty password (foo: accepted, matching (?::...*)?), double colon rejected via colons<=1, leading colon rejected — all match the real regex.

5. Model verifies in pinned Nagini (RC=0, 11.4s), so the postcondition Result()==accepts(...) is non-vacuous and the impl loop faithfully computes accepts.

The spec neither over-constrains nor under-constrains relative to the real compiled userinfo group. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). Consumer spec view = docstring + axioms/pure/pre/post regions; impl region is elided ('... implementation elided — supplied by the consumer'), so the gold implementation approach (the compiled regex, the character-class edit) is not shown. Confirmed the spec view contains NONE of: gold regex literals ([^\s:@/], \S+), patched file path (validators.py), patched symbol (URLValidator/regex), diff markers, issue example URLs (foo/bar, foo@bar), or regex-engine refs (re.compile/fullmatch/IGNORECASE). Semantically, everything the spec expresses is already public in the problem_statement: it quotes RFC 1738 3.1 'Within the user and password field, any ":", "@", or "/" must be encoded' and the example http://foo/bar@example.com should be invalid. The acceptance predicate (non-empty; only auth chars apart from <=1 separator colon; no leading colon; excludes whitespace/:/@//) is the natural formalization of that public requirement; the user:pass single-colon split is inherent URL userinfo syntax that follows from the publicly-stated 'user and password field'. The docstring is written as desired behaviour ('not as an edit'), names no pre-patch regex, and narrates no fix. No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).