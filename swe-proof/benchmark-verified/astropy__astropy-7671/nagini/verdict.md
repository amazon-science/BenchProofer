# P2 adversarial audit — astropy__astropy-7671

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -149,29 +147,9 @@
                     Result() == loose_gt(ToSeq(have), normalize(ToSeq(want)))))
     # post-conditions-end
     # impl-start
-    norm = []  # type: List[int]
-    i = len(want)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(have), 1 / 2))
-        Invariant(Acc(list_pred(want), 1 / 2))
-        Invariant(Acc(list_pred(norm)))
-        Invariant(is_numeric(ToSeq(have)))
-        Invariant(0 <= i and i <= len(want))
-        Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = want[i - 1]
-        Assert(ToSeq(want).drop(i - 1)[0] == c)
-        Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
-        if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
-        else:
-            norm = [c] + norm
-        i = i - 1
-    Assert(ToSeq(norm) == normalize(ToSeq(want)))
+    # WRONG: compares the raw requested version, no qualifier stripping
     if inclusive:
-        return loose_ge(ToSeq(have), ToSeq(norm))
+        return loose_ge(ToSeq(have), ToSeq(want))
     else:
-        return loose_gt(ToSeq(have), ToSeq(norm))
+        return loose_gt(ToSeq(have), ToSeq(want))
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -152,20 +150,17 @@
     norm = []  # type: List[int]
     i = len(want)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(have), 1 / 2))
         Invariant(Acc(list_pred(want), 1 / 2))
         Invariant(Acc(list_pred(norm)))
         Invariant(is_numeric(ToSeq(have)))
         Invariant(0 <= i and i <= len(want))
         Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = want[i - 1]
         Assert(ToSeq(want).drop(i - 1)[0] == c)
         Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
         if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
+            norm = []
         else:
             norm = [c] + norm
         i = i - 1
@@ -173,5 +168,6 @@
     if inclusive:
         return loose_ge(ToSeq(have), ToSeq(norm))
     else:
-        return loose_gt(ToSeq(have), ToSeq(norm))
+        # WRONG: strict branch reports inclusive order
+        return loose_ge(ToSeq(have), ToSeq(norm))
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -152,24 +150,15 @@
     norm = []  # type: List[int]
     i = len(want)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(have), 1 / 2))
         Invariant(Acc(list_pred(want), 1 / 2))
         Invariant(Acc(list_pred(norm)))
         Invariant(is_numeric(ToSeq(have)))
         Invariant(0 <= i and i <= len(want))
-        Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = want[i - 1]
-        Assert(ToSeq(want).drop(i - 1)[0] == c)
-        Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
-        if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
-        else:
-            norm = [c] + norm
+        # WRONG: always prepend, never reset on the qualifier marker
+        norm = [c] + norm
         i = i - 1
-    Assert(ToSeq(norm) == normalize(ToSeq(want)))
     if inclusive:
         return loose_ge(ToSeq(have), ToSeq(norm))
     else:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -152,26 +150,24 @@
     norm = []  # type: List[int]
     i = len(want)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(have), 1 / 2))
         Invariant(Acc(list_pred(want), 1 / 2))
         Invariant(Acc(list_pred(norm)))
         Invariant(is_numeric(ToSeq(have)))
         Invariant(0 <= i and i <= len(want))
         Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = want[i - 1]
         Assert(ToSeq(want).drop(i - 1)[0] == c)
         Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
         if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
+            norm = []
         else:
             norm = [c] + norm
         i = i - 1
     Assert(ToSeq(norm) == normalize(ToSeq(want)))
+    # WRONG: branches swapped
     if inclusive:
+        return loose_gt(ToSeq(have), ToSeq(norm))
+    else:
         return loose_ge(ToSeq(have), ToSeq(norm))
-    else:
-        return loose_gt(ToSeq(have), ToSeq(norm))
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -149,29 +147,6 @@
                     Result() == loose_gt(ToSeq(have), normalize(ToSeq(want)))))
     # post-conditions-end
     # impl-start
-    norm = []  # type: List[int]
-    i = len(want)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(have), 1 / 2))
-        Invariant(Acc(list_pred(want), 1 / 2))
-        Invariant(Acc(list_pred(norm)))
-        Invariant(is_numeric(ToSeq(have)))
-        Invariant(0 <= i and i <= len(want))
-        Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = want[i - 1]
-        Assert(ToSeq(want).drop(i - 1)[0] == c)
-        Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
-        if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
-        else:
-            norm = [c] + norm
-        i = i - 1
-    Assert(ToSeq(norm) == normalize(ToSeq(want)))
-    if inclusive:
-        return loose_ge(ToSeq(have), ToSeq(norm))
-    else:
-        return loose_gt(ToSeq(have), ToSeq(norm))
+    # WRONG: always reports satisfied
+    return True
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -149,29 +147,6 @@
                     Result() == loose_gt(ToSeq(have), normalize(ToSeq(want)))))
     # post-conditions-end
     # impl-start
-    norm = []  # type: List[int]
-    i = len(want)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(have), 1 / 2))
-        Invariant(Acc(list_pred(want), 1 / 2))
-        Invariant(Acc(list_pred(norm)))
-        Invariant(is_numeric(ToSeq(have)))
-        Invariant(0 <= i and i <= len(want))
-        Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = want[i - 1]
-        Assert(ToSeq(want).drop(i - 1)[0] == c)
-        Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
-        if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
-        else:
-            norm = [c] + norm
-        i = i - 1
-    Assert(ToSeq(norm) == normalize(ToSeq(want)))
-    if inclusive:
-        return loose_ge(ToSeq(have), ToSeq(norm))
-    else:
-        return loose_gt(ToSeq(have), ToSeq(norm))
+    # WRONG: always reports not satisfied
+    return False
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -152,26 +150,24 @@
     norm = []  # type: List[int]
     i = len(want)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(have), 1 / 2))
         Invariant(Acc(list_pred(want), 1 / 2))
         Invariant(Acc(list_pred(norm)))
         Invariant(is_numeric(ToSeq(have)))
         Invariant(0 <= i and i <= len(want))
         Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = want[i - 1]
         Assert(ToSeq(want).drop(i - 1)[0] == c)
         Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
         if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
+            norm = []
         else:
             norm = [c] + norm
         i = i - 1
     Assert(ToSeq(norm) == normalize(ToSeq(want)))
+    # WRONG: negated comparison
     if inclusive:
-        return loose_ge(ToSeq(have), ToSeq(norm))
+        return not loose_ge(ToSeq(have), ToSeq(norm))
     else:
-        return loose_gt(ToSeq(have), ToSeq(norm))
+        return not loose_gt(ToSeq(have), ToSeq(norm))
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -152,26 +150,24 @@
     norm = []  # type: List[int]
     i = len(want)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(have), 1 / 2))
         Invariant(Acc(list_pred(want), 1 / 2))
         Invariant(Acc(list_pred(norm)))
         Invariant(is_numeric(ToSeq(have)))
         Invariant(0 <= i and i <= len(want))
         Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = want[i - 1]
         Assert(ToSeq(want).drop(i - 1)[0] == c)
         Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
         if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
+            norm = []
         else:
             norm = [c] + norm
         i = i - 1
     Assert(ToSeq(norm) == normalize(ToSeq(want)))
+    # WRONG: operands swapped -> tests whether have <= norm
     if inclusive:
-        return loose_ge(ToSeq(have), ToSeq(norm))
+        return loose_ge(ToSeq(norm), ToSeq(have))
     else:
-        return loose_gt(ToSeq(have), ToSeq(norm))
+        return loose_gt(ToSeq(norm), ToSeq(have))
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -132,7 +131,6 @@
     # contract a sound over-approximation: it promises a defined boolean ONLY
     # where the real comparison is itself defined.
     Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(have), 1 / 2))
@@ -152,26 +150,24 @@
     norm = []  # type: List[int]
     i = len(want)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(have), 1 / 2))
         Invariant(Acc(list_pred(want), 1 / 2))
         Invariant(Acc(list_pred(norm)))
         Invariant(is_numeric(ToSeq(have)))
         Invariant(0 <= i and i <= len(want))
         Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = want[i - 1]
         Assert(ToSeq(want).drop(i - 1)[0] == c)
         Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
         if c < 0:
-            norm = []  # qualifier marker: discard the tail accumulated so far
+            norm = []
         else:
             norm = [c] + norm
         i = i - 1
     Assert(ToSeq(norm) == normalize(ToSeq(want)))
+    # WRONG: strict branch regresses to the raw (unstripped) requested version
     if inclusive:
         return loose_ge(ToSeq(have), ToSeq(norm))
     else:
-        return loose_gt(ToSeq(have), ToSeq(norm))
+        return loose_gt(ToSeq(have), ToSeq(want))
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-7671.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routine reports whether an installed component's version satisfies a
  requested minimum version. A version is an ordered list of release segments
  (the dotted numeric components of the public version label). A requested
  version label may carry a trailing NON-numeric qualifier (a pre/dev/release
  suffix such as the textual tail of "0.12dev" or "1.2rc1"); only the leading
  run of numeric release segments is meaningful for the ordering, and the
  qualifier tail must be discarded before any comparison. The installed
  version is a plain numeric version with no qualifier tail.

  The comparison itself is the standard component-wise version order: compare
  segments left to right; the first differing segment decides; when one is a
  proper prefix of the other the longer (more specific) version is the greater.
  The routine returns, inclusively, whether the installed version is at least
  the (qualifier-stripped) requested version, or, non-inclusively, whether it
  is strictly greater.

  Crucially the comparison operates on the qualifier-STRIPPED requested
  version: comparing against a label that still carries its non-numeric tail is
  not well defined and must never be performed.

Versions are modelled as `List[int]` of parsed release segments: a segment
>= 0 is a numeric release component; the sentinel value -1 marks the start of
the non-numeric qualifier tail (so "0.12dev" ~ [0, 12, -1], "1.2rc1" ~
[1, 2, -1], "0.12.0.dev" ~ [0, 12, 0, -1]). The pure sequence theory
`PSeq[int]` carries the specification. No external callee is axiomatized: the
qualifier stripping and the component-wise order are modelled deeply, and are
validated against the real version machinery out-of-band by axiom_check.py
(G-AX), not consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# axioms-end

# pure-start
@Pure
def is_numeric(s: PSeq[int]) -> bool:
    """True iff every segment is a numeric release component (>= 0), i.e. the
    sequence carries no non-numeric qualifier tail. Front-recursive so a single
    unfold is available per fold/loop step."""
    if len(s) == 0:
        return True
    return s[0] >= 0 and is_numeric(s.drop(1))

@Pure
def normalize(s: PSeq[int]) -> PSeq[int]:
    """The meaningful leading run of numeric release segments: the prefix of
    `s` up to (not including) the first qualifier marker (the first negative
    segment). Front-recursive, one unfold per leading segment. The result is
    always qualifier-free, so the component-wise order is always defined on it.
    """
    if len(s) == 0:
        return PSeq(0).take(0)
    if s[0] < 0:
        return PSeq(0).take(0)
    return PSeq(s[0]) + normalize(s.drop(1))

@Pure
def loose_ge(a: PSeq[int], b: PSeq[int]) -> bool:
    """Component-wise version order, inclusive (`a` is at least `b`). Compare
    release segments left to right; the first differing segment decides; on a
    proper prefix the longer (more specific) version is the greater.

    The order is well defined only between two qualifier-free versions. If a
    position pairs a numeric segment of one version with the qualifier marker
    of the other, the comparison has no defined result (the real version
    machinery raises a type error there); the modelled value at such a position
    is the non-satisfied outcome `False`, so a comparison that ever reaches the
    qualifier tail can never report 'satisfied'. The specification only ever
    compares against the qualifier-STRIPPED requested version, on which this
    case never arises. Front-recursive."""
    if len(a) == 0 and len(b) == 0:
        return True
    if len(a) == 0:
        return False
    if len(b) == 0:
        return True
    if (a[0] < 0) != (b[0] < 0):
        return False        # numeric vs qualifier marker: comparison undefined
    if a[0] != b[0]:
        return a[0] > b[0]
    return loose_ge(a.drop(1), b.drop(1))

@Pure
def loose_gt(a: PSeq[int], b: PSeq[int]) -> bool:
    """Strict component-wise version order (`a` is greater than `b`), with the
    same qualifier-marker handling as `loose_ge`: a position pairing a numeric
    segment with a qualifier marker has no defined result and is modelled as the
    non-satisfied outcome `False`. Front-recursive."""
    if len(a) == 0 and len(b) == 0:
        return False
    if len(a) == 0:
        return False
    if len(b) == 0:
        return True
    if (a[0] < 0) != (b[0] < 0):
        return False        # numeric vs qualifier marker: comparison undefined
    if a[0] != b[0]:
        return a[0] > b[0]
    return loose_gt(a.drop(1), b.drop(1))
# pure-end

def version_meets_minimum(have: List[int], want: List[int], inclusive: bool) -> bool:
    # pre-conditions-start
    # Both version lists are read-only (the routine reports a boolean and
    # mutates nothing): required AND ensured at fractional permission
    # (directive 5).
    Requires(Acc(list_pred(have), 1 / 2))
    Requires(Acc(list_pred(want), 1 / 2))
    # The installed version is a plain numeric version with no qualifier tail.
    Requires(is_numeric(ToSeq(have)))
    # The requested version begins with a numeric release segment, so its
    # qualifier-stripped form has a non-empty leading numeric run. A requested
    # label whose first segment is NOT a numeric release component (a pure or
    # leading qualifier such as "dev" / "" / ".1") has no well-defined release
    # ordering at all -- the comparison is not meaningful and is outside the
    # behaviour this contract specifies. Restricting the domain here keeps the
    # contract a sound over-approximation: it promises a defined boolean ONLY
    # where the real comparison is itself defined.
    Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(have), 1 / 2))
    Ensures(Acc(list_pred(want), 1 / 2))
    Ensures(is_numeric(ToSeq(have)))
    # The result is the component-wise order against the qualifier-STRIPPED
    # requested version: inclusively at-least, or strictly-greater. Comparing
    # against the un-stripped `want` (which may carry a qualifier tail) is
    # never performed; the comparison's domain is the normalized, numeric-only
    # version. This pins the discriminating behaviour the issue demands.
    Ensures(Implies(inclusive,
                    Result() == loose_ge(ToSeq(have), normalize(ToSeq(want)))))
    Ensures(Implies(not inclusive,
                    Result() == loose_gt(ToSeq(have), normalize(ToSeq(want)))))
    # post-conditions-end
    # impl-start
    norm = []  # type: List[int]
    i = len(want)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(have), 1 / 2))
        Invariant(Acc(list_pred(want), 1 / 2))
        Invariant(Acc(list_pred(norm)))
        Invariant(is_numeric(ToSeq(have)))
        Invariant(0 <= i and i <= len(want))
        Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
        # invariants-end
        c = want[i - 1]
        Assert(ToSeq(want).drop(i - 1)[0] == c)
        Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
        if c < 0:
            norm = []  # qualifier marker: discard the tail accumulated so far
        else:
            norm = [c] + norm
        i = i - 1
    Assert(ToSeq(norm) == normalize(ToSeq(want)))
    if inclusive:
        return loose_ge(ToSeq(have), ToSeq(norm))
    else:
        return loose_gt(ToSeq(have), ToSeq(norm))
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for astropy__astropy-7671 (nagini). VERDICT: SOUND. Ran from project root with venv (SBU_BENCHMARK_DIR=benchmark-verified).

PROTOCOL RESULT: 9 distinct same-spec wrong impls + the prepatch reproduction were all REJECTED by the Nagini verifier. Zero CANDIDATEs (nothing shares-spec-AND-verifies), therefore NO faithful-patch resolve runs were triggered (that step fires only for verifying candidates). patches={} accordingly.

Baselines:
- positive_control (bundle model.py impl, byte-copied): `bash scripts/nagini_verify.sh .../positive_control.py` -> VERIFIED (16.05s, exit 0).
- prepatch (bundle model_prepatch.py, raw-want comparison, the real bug): `adversary weakness nagini astropy__astropy-7671 .../prepatch.py` -> exit 2, does-not-verify (spec rejects the prepatch bug -> G-DIFF sensing confirmed).

All attacks: `python -m swebench_unified.adversary same-spec nagini astropy__astropy-7671 <atk>` -> SAME (exit 0) for all 9; then `python -m swebench_unified.adversary weakness nagini astropy__astropy-7671 <atk>` -> exit 2 (NOT-A-COUNTEREXAMPLE: does not verify) for all 9. Run concurrently in batches of <=3 JVMs.
  atk_1: prepatch bug (raw want, no normalization)            -> same-spec SAME, weakness exit 2 (rejected)
  atk_2: control-flow — strict branch uses loose_ge not loose_gt -> SAME, exit 2
  atk_3: boundary — loop never resets norm on qualifier marker    -> SAME, exit 2
  atk_4: control-flow — inclusive/strict branches swapped         -> SAME, exit 2
  atk_5: ungrounded oracle — return True constant                 -> SAME, exit 2
  atk_6: ungrounded oracle — return False constant                -> SAME, exit 2
  atk_7: ungrounded oracle — negated comparison (not loose_ge/gt)  -> SAME, exit 2
  atk_8: swapped operands loose_ge(norm,have) / loose_gt(norm,have) -> SAME, exit 2
  atk_9: mixed partial-domain — strict branch regresses to raw want -> SAME, exit 2

WHY SOUND (no free impl behaviour): the postcondition is an EXACT functional equality on the full in-domain space — Ensures(Implies(inclusive, Result()==loose_ge(ToSeq(have), normalize(ToSeq(want))))) and Ensures(Implies(not inclusive, Result()==loose_gt(ToSeq(have), normalize(ToSeq(want))))). Both branches pin Result pointwise, so any verifying impl is extensionally equal to the deep-model reference; there is no room for a verifying wrong impl.

A-LEG / correspondence audit (the focus per instructions): axioms region is EMPTY and model.py has 0 @ContractOnly (matches refinement.md §C and mapping.md §3 'no consumed axioms'). All refinement.md legs are R / A-reference / I — no kind-3 (unexpressible changed op). The two changed ops (qualifier-strip regex, LooseVersion comparison) are modelled DEEPLY as normalize / loose_ge / loose_gt (A-references validated by G-AX/axiom_check.py: check_normalize_vs_independent, check_normalize_strips, check_order, check_end_to_end_in_domain, check_out_of_domain_is_partial; encode raises Unencodable on epochs). axiom_check.py has no @ContractOnly to consume.

I independently re-derived the deep model in plain Python and confirmed it matches the gold-patched minversion on ALL 6 F2P test labels (have='0.12.2'): good ['0.12','0.12.1','0.12.0.dev','0.12dev'] -> True==True, bad ['1','1.2rc1'] -> False==False. Domain restriction Requires(len(want)>0 and want[0]>=0) matches the real callee's non-raising region; the discriminator 0.12dev ([0,12,-1], first seg 0>=0) is in-domain, so G-DIFF is unaffected. Gold F2P = test_minversion (adds '0.12dev' to good_versions); FAIL_TO_PASS=['astropy/utils/tests/test_introspection.py::test_minversion'].

CONCLUSION: spec is tight (exact-equality functional oracle), deep-model A-references correspond to the real callees on the tested inputs, no kind-3 legs, prepatch is sensed, positive control verifies. No verifying wrong impl exists -> verify DOES imply correct here. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-7671.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routine reports whether an installed component's version satisfies a
  requested minimum version. A version is an ordered list of release segments
  (the dotted numeric components of the public version label). A requested
  version label may carry a trailing NON-numeric qualifier (a pre/dev/release
  suffix such as the textual tail of "0.12dev" or "1.2rc1"); only the leading
  run of numeric release segments is meaningful for the ordering, and the
  qualifier tail must be discarded before any comparison. The installed
  version is a plain numeric version with no qualifier tail.

  The comparison itself is the standard component-wise version order: compare
  segments left to right; the first differing segment decides; when one is a
  proper prefix of the other the longer (more specific) version is the greater.
  The routine returns, inclusively, whether the installed version is at least
  the (qualifier-stripped) requested version, or, non-inclusively, whether it
  is strictly greater.

  Crucially the comparison operates on the qualifier-STRIPPED requested
  version: comparing against a label that still carries its non-numeric tail is
  not well defined and must never be performed.

Versions are modelled as `List[int]` of parsed release segments: a segment
>= 0 is a numeric release component; the sentinel value -1 marks the start of
the non-numeric qualifier tail (so "0.12dev" ~ [0, 12, -1], "1.2rc1" ~
[1, 2, -1], "0.12.0.dev" ~ [0, 12, 0, -1]). The pure sequence theory
`PSeq[int]` carries the specification. No external callee is axiomatized: the
qualifier stripping and the component-wise order are modelled deeply, and are
validated against the real version machinery out-of-band by axiom_check.py
(G-AX), not consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# axioms-end

# pure-start
@Pure
def is_numeric(s: PSeq[int]) -> bool:
    """True iff every segment is a numeric release component (>= 0), i.e. the
    sequence carries no non-numeric qualifier tail. Front-recursive so a single
    unfold is available per fold/loop step."""
    if len(s) == 0:
        return True
    return s[0] >= 0 and is_numeric(s.drop(1))

@Pure
def normalize(s: PSeq[int]) -> PSeq[int]:
    """The meaningful leading run of numeric release segments: the prefix of
    `s` up to (not including) the first qualifier marker (the first negative
    segment). Front-recursive, one unfold per leading segment. The result is
    always qualifier-free, so the component-wise order is always defined on it.
    """
    if len(s) == 0:
        return PSeq(0).take(0)
    if s[0] < 0:
        return PSeq(0).take(0)
    return PSeq(s[0]) + normalize(s.drop(1))

@Pure
def loose_ge(a: PSeq[int], b: PSeq[int]) -> bool:
    """Component-wise version order, inclusive (`a` is at least `b`). Compare
    release segments left to right; the first differing segment decides; on a
    proper prefix the longer (more specific) version is the greater.

    The order is well defined only between two qualifier-free versions. If a
    position pairs a numeric segment of one version with the qualifier marker
    of the other, the comparison has no defined result (the real version
    machinery raises a type error there); the modelled value at such a position
    is the non-satisfied outcome `False`, so a comparison that ever reaches the
    qualifier tail can never report 'satisfied'. The specification only ever
    compares against the qualifier-STRIPPED requested version, on which this
    case never arises. Front-recursive."""
    if len(a) == 0 and len(b) == 0:
        return True
    if len(a) == 0:
        return False
    if len(b) == 0:
        return True
    if (a[0] < 0) != (b[0] < 0):
        return False        # numeric vs qualifier marker: comparison undefined
    if a[0] != b[0]:
        return a[0] > b[0]
    return loose_ge(a.drop(1), b.drop(1))

@Pure
def loose_gt(a: PSeq[int], b: PSeq[int]) -> bool:
    """Strict component-wise version order (`a` is greater than `b`), with the
    same qualifier-marker handling as `loose_ge`: a position pairing a numeric
    segment with a qualifier marker has no defined result and is modelled as the
    non-satisfied outcome `False`. Front-recursive."""
    if len(a) == 0 and len(b) == 0:
        return False
    if len(a) == 0:
        return False
    if len(b) == 0:
        return True
    if (a[0] < 0) != (b[0] < 0):
        return False        # numeric vs qualifier marker: comparison undefined
    if a[0] != b[0]:
        return a[0] > b[0]
    return loose_gt(a.drop(1), b.drop(1))
# pure-end

def version_meets_minimum(have: List[int], want: List[int], inclusive: bool) -> bool:
    # pre-conditions-start
    # Both version lists are read-only (the routine reports a boolean and
    # mutates nothing): required AND ensured at fractional permission
    # (directive 5).
    Requires(Acc(list_pred(have), 1 / 2))
    Requires(Acc(list_pred(want), 1 / 2))
    # The installed version is a plain numeric version with no qualifier tail.
    Requires(is_numeric(ToSeq(have)))
    # The requested version begins with a numeric release segment, so its
    # qualifier-stripped form has a non-empty leading numeric run. A requested
    # label whose first segment is NOT a numeric release component (a pure or
    # leading qualifier such as "dev" / "" / ".1") has no well-defined release
    # ordering at all -- the comparison is not meaningful and is outside the
    # behaviour this contract specifies. Restricting the domain here keeps the
    # contract a sound over-approximation: it promises a defined boolean ONLY
    # where the real comparison is itself defined.
    Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(have), 1 / 2))
    Ensures(Acc(list_pred(want), 1 / 2))
    Ensures(is_numeric(ToSeq(have)))
    # The result is the component-wise order against the qualifier-STRIPPED
    # requested version: inclusively at-least, or strictly-greater. Comparing
    # against the un-stripped `want` (which may carry a qualifier tail) is
    # never performed; the comparison's domain is the normalized, numeric-only
    # version. This pins the discriminating behaviour the issue demands.
    Ensures(Implies(inclusive,
                    Result() == loose_ge(ToSeq(have), normalize(ToSeq(want)))))
    Ensures(Implies(not inclusive,
                    Result() == loose_gt(ToSeq(have), normalize(ToSeq(want)))))
    # post-conditions-end
    # impl-start
    norm = []  # type: List[int]
    i = len(want)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(have), 1 / 2))
        Invariant(Acc(list_pred(want), 1 / 2))
        Invariant(Acc(list_pred(norm)))
        Invariant(is_numeric(ToSeq(have)))
        Invariant(0 <= i and i <= len(want))
        Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
        # invariants-end
        c = want[i - 1]
        Assert(ToSeq(want).drop(i - 1)[0] == c)
        Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
        if c < 0:
            norm = []  # qualifier marker: discard the tail accumulated so far
        else:
            norm = [c] + norm
        i = i - 1
    Assert(ToSeq(norm) == normalize(ToSeq(want)))
    if inclusive:
        return loose_ge(ToSeq(have), ToSeq(norm))
    else:
        return loose_gt(ToSeq(have), ToSeq(norm))
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for astropy__astropy-7671 (nagini). VERDICT: SOUND. Ran from project root with venv (SBU_BENCHMARK_DIR=benchmark-verified).

PROTOCOL RESULT: 9 distinct same-spec wrong impls + the prepatch reproduction were all REJECTED by the Nagini verifier. Zero CANDIDATEs (nothing shares-spec-AND-verifies), therefore NO faithful-patch resolve runs were triggered (that step fires only for verifying candidates). patches={} accordingly.

Baselines:
- positive_control (bundle model.py impl, byte-copied): `bash scripts/nagini_verify.sh .../positive_control.py` -> VERIFIED (16.05s, exit 0).
- prepatch (bundle model_prepatch.py, raw-want comparison, the real bug): `adversary weakness nagini astropy__astropy-7671 .../prepatch.py` -> exit 2, does-not-verify (spec rejects the prepatch bug -> G-DIFF sensing confirmed).

All attacks: `python -m swebench_unified.adversary same-spec nagini astropy__astropy-7671 <atk>` -> SAME (exit 0) for all 9; then `python -m swebench_unified.adversary weakness nagini astropy__astropy-7671 <atk>` -> exit 2 (NOT-A-COUNTEREXAMPLE: does not verify) for all 9. Run concurrently in batches of <=3 JVMs.
  atk_1: prepatch bug (raw want, no normalization)            -> same-spec SAME, weakness exit 2 (rejected)
  atk_2: control-flow — strict branch uses loose_ge not loose_gt -> SAME, exit 2
  atk_3: boundary — loop never resets norm on qualifier marker    -> SAME, exit 2
  atk_4: control-flow — inclusive/strict branches swapped         -> SAME, exit 2
  atk_5: ungrounded oracle — return True constant                 -> SAME, exit 2
  atk_6: ungrounded oracle — return False constant                -> SAME, exit 2
  atk_7: ungrounded oracle — negated comparison (not loose_ge/gt)  -> SAME, exit 2
  atk_8: swapped operands loose_ge(norm,have) / loose_gt(norm,have) -> SAME, exit 2
  atk_9: mixed partial-domain — strict branch regresses to raw want -> SAME, exit 2

WHY SOUND (no free impl behaviour): the postcondition is an EXACT functional equality on the full in-domain space — Ensures(Implies(inclusive, Result()==loose_ge(ToSeq(have), normalize(ToSeq(want))))) and Ensures(Implies(not inclusive, Result()==loose_gt(ToSeq(have), normalize(ToSeq(want))))). Both branches pin Result pointwise, so any verifying impl is extensionally equal to the deep-model reference; there is no room for a verifying wrong impl.

A-LEG / correspondence audit (the focus per instructions): axioms region is EMPTY and model.py has 0 @ContractOnly (matches refinement.md §C and mapping.md §3 'no consumed axioms'). All refinement.md legs are R / A-reference / I — no kind-3 (unexpressible changed op). The two changed ops (qualifier-strip regex, LooseVersion comparison) are modelled DEEPLY as normalize / loose_ge / loose_gt (A-references validated by G-AX/axiom_check.py: check_normalize_vs_independent, check_normalize_strips, check_order, check_end_to_end_in_domain, check_out_of_domain_is_partial; encode raises Unencodable on epochs). axiom_check.py has no @ContractOnly to consume.

I independently re-derived the deep model in plain Python and confirmed it matches the gold-patched minversion on ALL 6 F2P test labels (have='0.12.2'): good ['0.12','0.12.1','0.12.0.dev','0.12dev'] -> True==True, bad ['1','1.2rc1'] -> False==False. Domain restriction Requires(len(want)>0 and want[0]>=0) matches the real callee's non-raising region; the discriminator 0.12dev ([0,12,-1], first seg 0>=0) is in-domain, so G-DIFF is unaffected. Gold F2P = test_minversion (adds '0.12dev' to good_versions); FAIL_TO_PASS=['astropy/utils/tests/test_introspection.py::test_minversion'].

CONCLUSION: spec is tight (exact-equality functional oracle), deep-model A-references correspond to the real callees on the tested inputs, no kind-3 legs, prepatch is sensed, positive control verifies. No verifying wrong impl exists -> verify DOES imply correct here. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) audit for astropy__astropy-7671 nagini. Spec region byte-identical to bundle (same-spec exit 0). The modeled version_meets_minimum computes loose_ge/loose_gt(have, normalize(want)) which is exactly the gold-patched minversion tail: re.match(EXPR, version).group(0) strip + LooseVersion >=/>. 

Independent differential test (not reusing the bundle's fuzzer): loaded the REAL gold-patched astropy/utils/introspection.py:minversion directly from a base-commit worktree + patch.diff, and compared it against the deep model via the documented encode() bijection. Results: 354,540 in-domain (have,want)x(inclusive,strict) triples over segments including leading zeros (01, 007), large ints, and 20+ qualifier tails => 0 mismatches. A 200,000-triple raise-hunt found 0 in-domain inputs where the real callee raises, confirming Requires(len(want)>0 and want[0]>=0) is a sound subset of the real callee's total region (contract is conservative, never over-claims a defined boolean). Boundary/test-suite constellation (0.12.2 vs 0.12/0.12.1/0.12.0.dev/0.12dev good; 1/1.2rc1 bad) all agree. Bundled G-AX exit 0.

The qualifier-marker undefined case ((a[0]<0)!=(b[0]<0) -> False) is unreachable on the spec path because normalize(want) is always qualifier-free (proved numeric in the loop). No divergence between model and real repo behavior on any input in the modeled domain. Spec is a faithful, sound over-approximation; not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified the consumer spec view (module docstring + pure helpers normalize/loose_ge/loose_gt/is_numeric + pre/post-conditions; impl-start...impl-end elided to a placeholder) with swebench_unified.markers.spec_view. The mechanical G-LEAK screen (leakage.screen) passes with zero hard failures (only distinctive patched symbol is 'minversion', which already appears verbatim in the public problem_statement, so it is exempt).

Gold edit's distinctive mechanism: `import re` + a PEP440 leading-dotted-number regex literal '^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*' fed to re.match(...).group(0) to strip a version qualifier before the LooseVersion >=/> comparison. NONE of that solution vocabulary appears in the spec view: no 're', 're.match', 'regex', 'PEP440', 'LooseVersion', 'distutils', and no regex literal. Those tokens live only in mapping.md / refinement.md / axiom_check.py, which are NOT part of the consumer spec view.

The spec view stays at the behavioral level: 'only the leading run of numeric release segments is meaningful ... the qualifier tail must be discarded before any comparison', pinned formally as Result() == loose_ge(have, normalize(want)) / loose_gt(...). Stating the REQUIRED behavior (compare against the qualifier-stripped requested version) is the spec's legitimate job and is exactly what G-DIFF needs to sense the prepatch bug; it is not disclosure of the specific gold edit.

Beyond-problem_statement check: the public problem_statement already reveals the crux (minversion('numpy','1.14dev') raises TypeError; '1.14' works but '1.14dev' fails; the dev/rc qualifier is the culprit; it even floats an alternative pkg_resources.parse_version fix). So the spec view's notion that a qualifier tail must be stripped adds no gold-edit specificity beyond what the solver already sees.

Non-uniqueness: the bundle's own reference impl satisfies the spec with a backward loop over the parsed List[int] (accumulate norm, discard on the -1 sentinel), NOT the gold regex — demonstrating the specific gold mechanism is not pinned by the spec. meta.json G-LEAK=pass and G-PANEL-3=pass are consistent with this finding.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.