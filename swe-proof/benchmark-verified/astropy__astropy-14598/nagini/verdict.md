# P2 adversarial audit — astropy__astropy-14598

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     Requires(Acc(list_pred(segment), 1 / 2))
     Requires(Forall(int, lambda k:
                     (Implies(0 <= k and k < len(segment), segment[k] != 47))))
-    Requires(MustTerminate(len(segment) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segment), 1 / 2))
@@ -100,18 +98,9 @@
     result = []  # type: List[int]
     j = 0
     n = len(segment)
-    while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(segment), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(segment))
-        Invariant(ToSeq(result) == ToSeq(segment).take(j))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
+    while j < n - 1:
         result = result + [segment[j]]
         j = j + 1
-    Assert(ToSeq(segment).take(n) == ToSeq(segment))
     return result
     # impl-end
 
@@ -126,7 +115,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(captured), 1 / 2))
     Requires(Acc(list_pred(witness), 1 / 2))
-    Requires(MustTerminate(len(witness) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(captured), 1 / 2))
@@ -150,7 +138,6 @@
         Invariant(0 <= j and j <= n and n == len(captured))
         Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                   == unescape_quotes(ToSeq(captured)))
-        Invariant(MustTerminate(n - j + 1))
         # invariants-end
         if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
             Assert(ToSeq(captured).drop(j)[0] == 39)
@@ -177,7 +164,6 @@
 # The round-trip identity, proved once and quantified, supports the rt witness
 # clause of `unescape_value`.
 def rt_lemma(v: PSeq[int]) -> None:
-    Requires(MustTerminate(len(v) + 1))
     Ensures(unescape_quotes(escape_quotes(v)) == v)
     if len(v) == 0:
         return
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     Requires(Acc(list_pred(segment), 1 / 2))
     Requires(Forall(int, lambda k:
                     (Implies(0 <= k and k < len(segment), segment[k] != 47))))
-    Requires(MustTerminate(len(segment) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segment), 1 / 2))
@@ -101,17 +99,9 @@
     j = 0
     n = len(segment)
     while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(segment), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(segment))
-        Invariant(ToSeq(result) == ToSeq(segment).take(j))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
         result = result + [segment[j]]
         j = j + 1
-    Assert(ToSeq(segment).take(n) == ToSeq(segment))
+    result = result + [39]
     return result
     # impl-end
 
@@ -126,7 +116,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(captured), 1 / 2))
     Requires(Acc(list_pred(witness), 1 / 2))
-    Requires(MustTerminate(len(witness) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(captured), 1 / 2))
@@ -150,7 +139,6 @@
         Invariant(0 <= j and j <= n and n == len(captured))
         Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                   == unescape_quotes(ToSeq(captured)))
-        Invariant(MustTerminate(n - j + 1))
         # invariants-end
         if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
             Assert(ToSeq(captured).drop(j)[0] == 39)
@@ -177,7 +165,6 @@
 # The round-trip identity, proved once and quantified, supports the rt witness
 # clause of `unescape_value`.
 def rt_lemma(v: PSeq[int]) -> None:
-    Requires(MustTerminate(len(v) + 1))
     Ensures(unescape_quotes(escape_quotes(v)) == v)
     if len(v) == 0:
         return
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     Requires(Acc(list_pred(segment), 1 / 2))
     Requires(Forall(int, lambda k:
                     (Implies(0 <= k and k < len(segment), segment[k] != 47))))
-    Requires(MustTerminate(len(segment) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segment), 1 / 2))
@@ -101,17 +99,9 @@
     j = 0
     n = len(segment)
     while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(segment), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(segment))
-        Invariant(ToSeq(result) == ToSeq(segment).take(j))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
-        result = result + [segment[j]]
+        if segment[j] != 32:
+            result = result + [segment[j]]
         j = j + 1
-    Assert(ToSeq(segment).take(n) == ToSeq(segment))
     return result
     # impl-end
 
@@ -126,7 +116,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(captured), 1 / 2))
     Requires(Acc(list_pred(witness), 1 / 2))
-    Requires(MustTerminate(len(witness) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(captured), 1 / 2))
@@ -150,7 +139,6 @@
         Invariant(0 <= j and j <= n and n == len(captured))
         Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                   == unescape_quotes(ToSeq(captured)))
-        Invariant(MustTerminate(n - j + 1))
         # invariants-end
         if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
             Assert(ToSeq(captured).drop(j)[0] == 39)
@@ -177,7 +165,6 @@
 # The round-trip identity, proved once and quantified, supports the rt witness
 # clause of `unescape_value`.
 def rt_lemma(v: PSeq[int]) -> None:
-    Requires(MustTerminate(len(v) + 1))
     Ensures(unescape_quotes(escape_quotes(v)) == v)
     if len(v) == 0:
         return
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     Requires(Acc(list_pred(segment), 1 / 2))
     Requires(Forall(int, lambda k:
                     (Implies(0 <= k and k < len(segment), segment[k] != 47))))
-    Requires(MustTerminate(len(segment) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segment), 1 / 2))
@@ -106,7 +104,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n and n == len(segment))
         Invariant(ToSeq(result) == ToSeq(segment).take(j))
-        Invariant(MustTerminate(n - j + 1))
         # invariants-end
         Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
         result = result + [segment[j]]
@@ -126,7 +123,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(captured), 1 / 2))
     Requires(Acc(list_pred(witness), 1 / 2))
-    Requires(MustTerminate(len(witness) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(captured), 1 / 2))
@@ -144,31 +140,8 @@
     j = 0
     n = len(captured)
     while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(captured), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(captured))
-        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
-                  == unescape_quotes(ToSeq(captured)))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
-            Assert(ToSeq(captured).drop(j)[0] == 39)
-            Assert(ToSeq(captured).drop(j)[1] == 39)
-            Assert(len(ToSeq(captured).drop(j)) >= 2)
-            Assert(unescape_quotes(ToSeq(captured).drop(j))
-                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
-            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
-            result = result + [39]
-            j = j + 2
-        else:
-            c = captured[j]
-            Assert(ToSeq(captured).drop(j)[0] == c)
-            Assert(unescape_quotes(ToSeq(captured).drop(j))
-                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
-            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
-            result = result + [c]
-            j = j + 1
+        result = result + [captured[j]]
+        j = j + 1
     rt_lemma(ToSeq(witness))
     return result
     # impl-end
@@ -177,7 +150,6 @@
 # The round-trip identity, proved once and quantified, supports the rt witness
 # clause of `unescape_value`.
 def rt_lemma(v: PSeq[int]) -> None:
-    Requires(MustTerminate(len(v) + 1))
     Ensures(unescape_quotes(escape_quotes(v)) == v)
     if len(v) == 0:
         return
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     Requires(Acc(list_pred(segment), 1 / 2))
     Requires(Forall(int, lambda k:
                     (Implies(0 <= k and k < len(segment), segment[k] != 47))))
-    Requires(MustTerminate(len(segment) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segment), 1 / 2))
@@ -106,7 +104,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n and n == len(segment))
         Invariant(ToSeq(result) == ToSeq(segment).take(j))
-        Invariant(MustTerminate(n - j + 1))
         # invariants-end
         Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
         result = result + [segment[j]]
@@ -126,7 +123,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(captured), 1 / 2))
     Requires(Acc(list_pred(witness), 1 / 2))
-    Requires(MustTerminate(len(witness) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(captured), 1 / 2))
@@ -144,30 +140,11 @@
     j = 0
     n = len(captured)
     while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(captured), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(captured))
-        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
-                  == unescape_quotes(ToSeq(captured)))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
-            Assert(ToSeq(captured).drop(j)[0] == 39)
-            Assert(ToSeq(captured).drop(j)[1] == 39)
-            Assert(len(ToSeq(captured).drop(j)) >= 2)
-            Assert(unescape_quotes(ToSeq(captured).drop(j))
-                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
-            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
+        if j + 3 <= n and captured[j] == 39 and captured[j + 1] == 39:
             result = result + [39]
-            j = j + 2
+            j = j + 3
         else:
-            c = captured[j]
-            Assert(ToSeq(captured).drop(j)[0] == c)
-            Assert(unescape_quotes(ToSeq(captured).drop(j))
-                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
-            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
-            result = result + [c]
+            result = result + [captured[j]]
             j = j + 1
     rt_lemma(ToSeq(witness))
     return result
@@ -177,7 +154,6 @@
 # The round-trip identity, proved once and quantified, supports the rt witness
 # clause of `unescape_value`.
 def rt_lemma(v: PSeq[int]) -> None:
-    Requires(MustTerminate(len(v) + 1))
     Ensures(unescape_quotes(escape_quotes(v)) == v)
     if len(v) == 0:
         return
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -88,7 +87,6 @@
     Requires(Acc(list_pred(segment), 1 / 2))
     Requires(Forall(int, lambda k:
                     (Implies(0 <= k and k < len(segment), segment[k] != 47))))
-    Requires(MustTerminate(len(segment) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segment), 1 / 2))
@@ -106,7 +104,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n and n == len(segment))
         Invariant(ToSeq(result) == ToSeq(segment).take(j))
-        Invariant(MustTerminate(n - j + 1))
         # invariants-end
         Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
         result = result + [segment[j]]
@@ -126,7 +123,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(captured), 1 / 2))
     Requires(Acc(list_pred(witness), 1 / 2))
-    Requires(MustTerminate(len(witness) + 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(captured), 1 / 2))
@@ -144,30 +140,12 @@
     j = 0
     n = len(captured)
     while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(captured), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(captured))
-        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
-                  == unescape_quotes(ToSeq(captured)))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
-            Assert(ToSeq(captured).drop(j)[0] == 39)
-            Assert(ToSeq(captured).drop(j)[1] == 39)
-            Assert(len(ToSeq(captured).drop(j)) >= 2)
-            Assert(unescape_quotes(ToSeq(captured).drop(j))
-                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
-            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
+        if captured[j] == 39:
             result = result + [39]
-            j = j + 2
+            while j < n and captured[j] == 39:
+                j = j + 1
         else:
-            c = captured[j]
-            Assert(ToSeq(captured).drop(j)[0] == c)
-            Assert(unescape_quotes(ToSeq(captured).drop(j))
-                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
-            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
-            result = result + [c]
+            result = result + [captured[j]]
             j = j + 1
     rt_lemma(ToSeq(witness))
     return result
@@ -177,7 +155,6 @@
 # The round-trip identity, proved once and quantified, supports the rt witness
 # clause of `unescape_value`.
 def rt_lemma(v: PSeq[int]) -> None:
-    Requires(MustTerminate(len(v) + 1))
     Ensures(unescape_quotes(escape_quotes(v)) == v)
     if len(v) == 0:
         return
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-14598.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A long keyword value is serialised by *escaping* every embedded single quote
  U+0027 as a pair of single quotes (the convention for a literal quote inside a
  quoted string), then carrying the escaped text across one or more continuation
  segments. Re-deriving the value from that serialised form must be its exact
  inverse, so that serialise-then-parse is the identity on EVERY value. Two
  independently observable obligations:

  (A) Full payload recovery. The escaped text carried by a continuation segment
      must be recovered IN FULL. Characters that follow an interior space (the
      payload of a quoted string may legitimately contain spaces) are part of
      the payload and must not be dropped: recovery may not stop early at the
      first interior space-adjacent quote. The recovered payload equals the
      segment's escaped text exactly.

  (B) Single un-escape. The recovered escaped text is un-escaped EXACTLY ONCE:
      each leading pair of single quotes collapses to one single quote, every
      other code point is copied. The un-escape is applied a single time, so a
      genuine embedded quote pair is preserved as a quote pair.

  (A) and (B) compose to the round-trip identity: for every value, un-escaping
      the full recovery of its escape returns the original value, in particular
      for a value that contains or ends with an embedded quote pair, with or
      without trailing text and with or without an interior space.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the single quote is the code point 39, the space is 32. The
specification is carried by the pure sequence theory `PSeq[int]`.

There are no axioms. The escaping, the full-payload recovery, and the
un-escaping are all *changed* / supporting operations modelled DEEPLY as
verified folds (`escape_quotes`, `unescape_quotes`). Their agreement with the
real library operations is checked out-of-band by axiom_check.py (G-AX), not
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions; the
per-function regions repeat, one set per modelled obligation.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def escape_quotes(s: PSeq[int]) -> PSeq[int]:
    """Serialisation escape: every single quote (39) becomes a pair of single
    quotes; every other code point is copied. Front-recursive so a single
    unfold is available per loop / proof step."""
    if len(s) == 0:
        return s
    if s[0] == 39:
        return PSeq(39, 39) + escape_quotes(s.drop(1))
    return PSeq(s[0]) + escape_quotes(s.drop(1))


@Pure
def unescape_quotes(s: PSeq[int]) -> PSeq[int]:
    """Parse un-escape applied exactly once: a leading pair of single quotes
    (39,39) collapses to one single quote and parsing continues after the pair;
    any other leading code point is copied and parsing continues after it. The
    single non-overlapping left-to-right collapse of `''` -> `'`."""
    if len(s) < 2:
        return s
    if s[0] == 39 and s[1] == 39:
        return PSeq(39) + unescape_quotes(s.drop(2))
    return PSeq(s[0]) + unescape_quotes(s.drop(1))
# pure-end


def recover_payload(segment: List[int]) -> List[int]:
    """Obligation (A): recover the FULL escaped payload carried by a
    continuation segment. The recovered payload is every code point of the
    segment's carried text -- nothing is dropped at an interior space.

    The carried text does not contain the value/comment separator (code point
    47, '/'): segments whose payload introduces a separator are handled by the
    comment-separation logic and are out of this obligation's scope.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(segment), 1 / 2))
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(segment), segment[k] != 47))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(segment), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The complete carried payload is recovered, in order, in full.
    Ensures(ToSeq(Result()) == ToSeq(segment))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(segment)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(segment), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(segment))
        Invariant(ToSeq(result) == ToSeq(segment).take(j))
        # invariants-end
        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
        result = result + [segment[j]]
        j = j + 1
    Assert(ToSeq(segment).take(n) == ToSeq(segment))
    return result
    # impl-end


def unescape_value(captured: List[int], witness: List[int]) -> List[int]:
    """Obligation (B): un-escape the recovered escaped text EXACTLY ONCE. Each
    leading pair of single quotes collapses to one; every other code point is
    copied. Composing with the full recovery (A) is the round-trip identity:
    `witness` is the read-only original value whose escape this recovers, and
    the un-escape returns it exactly (the round-trip clause).
    """
    # pre-conditions-start
    Requires(Acc(list_pred(captured), 1 / 2))
    Requires(Acc(list_pred(witness), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(captured), 1 / 2))
    Ensures(Acc(list_pred(witness), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Exactly one un-escape pass over the recovered text.
    Ensures(ToSeq(Result()) == unescape_quotes(ToSeq(captured)))
    # Round-trip witness: if the recovered text is the escape of `witness`, this
    # un-escape returns `witness` -- single application is the exact inverse.
    Ensures(Implies(ToSeq(captured) == escape_quotes(ToSeq(witness)),
                    ToSeq(Result()) == ToSeq(witness)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(captured)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(captured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(captured))
        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                  == unescape_quotes(ToSeq(captured)))
        # invariants-end
        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
            Assert(ToSeq(captured).drop(j)[0] == 39)
            Assert(ToSeq(captured).drop(j)[1] == 39)
            Assert(len(ToSeq(captured).drop(j)) >= 2)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
            result = result + [39]
            j = j + 2
        else:
            c = captured[j]
            Assert(ToSeq(captured).drop(j)[0] == c)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
            result = result + [c]
            j = j + 1
    rt_lemma(ToSeq(witness))
    return result
    # impl-end


# The round-trip identity, proved once and quantified, supports the rt witness
# clause of `unescape_value`.
def rt_lemma(v: PSeq[int]) -> None:
    Ensures(unescape_quotes(escape_quotes(v)) == v)
    if len(v) == 0:
        return
    rt_lemma(v.drop(1))
    if v[0] == 39:
        Assert(escape_quotes(v) == PSeq(39, 39) + escape_quotes(v.drop(1)))
        Assert(escape_quotes(v)[0] == 39)
        Assert(escape_quotes(v)[1] == 39)
        Assert(len(escape_quotes(v)) >= 2)
        Assert(escape_quotes(v).drop(2) == escape_quotes(v.drop(1)))
        Assert(unescape_quotes(escape_quotes(v))
               == PSeq(39) + unescape_quotes(escape_quotes(v.drop(1))))
    else:
        Assert(escape_quotes(v) == PSeq(v[0]) + escape_quotes(v.drop(1)))
        Assert(escape_quotes(v)[0] == v[0])
        Assert(v[0] != 39)
        Assert(unescape_quotes(escape_quotes(v))
               == PSeq(v[0]) + unescape_quotes(escape_quotes(v).drop(1)))
        Assert(escape_quotes(v).drop(1) == escape_quotes(v.drop(1)))
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY (G-EQ refinement-fidelity, A-leg focus) for astropy__astropy-14598 / nagini. SBU_BENCHMARK_DIR=benchmark-verified; adversary + verify run via python (main env); nagini_verify.sh drives the pinned JVM+Z3.

SPEC STRUCTURE: The frozen spec pins BOTH functions' outputs completely. recover_payload: Ensures ToSeq(Result())==ToSeq(segment) (full-payload identity on the no-'/' domain, Requires segment[k]!=47). unescape_value: Ensures ToSeq(Result())==unescape_quotes(ToSeq(captured)) (single un-escape pass) PLUS the round-trip clause Implies(ToSeq(captured)==escape_quotes(ToSeq(witness)), ToSeq(Result())==ToSeq(witness)). Because each postcondition is a total functional pin of the return sequence, any verifying impl is functionally determined — leaving no room for a same-spec verifying wrong impl.

SPEC-BOUNDARY MECHANICS (markers.py): spec view elides ONLY impl regions (incl. nested invariants); axioms/@Pure(escape_quotes,unescape_quotes)/Requires/Ensures/rt_lemma are all in the spec signature and must stay byte-identical. All attacks edited ONLY impl regions -> same-spec confirmed for all 6 (and positive control) via `adversary same-spec` exit 0.

### ATTACKS (all: `python -m swebench_unified.adversary weakness nagini astropy__astropy-14598 <path>`):
- atk_1 (boundary/off-by-one, recover): loop `while j<n-1` -> drops last cp. same-spec=SAME; weakness=NOT-A-COUNTEREXAMPLE (verification failed: postcond ToSeq(Result())==ToSeq(segment) fails). REJECTED.
- atk_2 (boundary overrun, recover): appends spurious [39]. REJECTED (does not verify).
- atk_3 (partial-domain, recover): drops interior spaces (cp 32). REJECTED (does not verify).
- atk_4 (ungrounded-oracle echo / no-op, unescape): identity copy, no collapse. REJECTED (postcond ==unescape_quotes(...) fails).
- atk_5 (control-flow-effect off-by-one, unescape): advances j+=3 on a leading quote-pair. REJECTED (does not verify).
- atk_6 (over-collapse, unescape): collapses a run of quotes to a single 39. REJECTED (does not verify).
No attack returned CANDIDATE-COUNTEREXAMPLE, so NO materialized faithful patch / run_resolve was mandated (protocol step 2 triggers only on a verifying candidate). None available to break the spec.

POSITIVE CONTROL: benchmark model.py copied verbatim -> `adversary verify` = VERIFIED in 20.0s (exit 0). Confirms the harness/env verify the intended impl.

### PREPATCH REPRODUCTION (both bug sites, `adversary verify`):
- prepatch_A (model_prepatch_2.py, site A, unanchored-regex truncation at first quote-then-space): FAILED 25.2s — 'Postcondition of recover_payload might not hold. Assertion (ToSeq(Result())==ToSeq(segment)) might not hold.' Spec senses the regex-anchor bug (G-DIFF).
- prepatch_B (model_prepatch.py, site B, double un-escape): FAILED 31.5s — 'Postcondition of unescape_value might not hold. Assertion (ToSeq(Result())==unescape_quotes(ToSeq(captured))) might not hold.' Spec senses the double-un-escape bug (G-DIFF).
prepatch_reproduced=true for both hunks.

A-LEG / MODEL-CORRESPONDENCE AUDIT (refinement.md + mapping.md):
- axioms region is EMPTY in model.py (verified by awk over # axioms-start/-end) => ZERO A-consumed legs; no proof consumes a @ContractOnly Ensures. Consistent with refinement.md §D.
- All legs classify as R, A-reference, or I; no kind-3 (unexpressible-changed-op). Site A: A1=R (str<->List[int]; no-'/' domain), A2=A-reference (the $-anchor's changed property modelled deeply as the full copy). Site B: B1=R (.rstrip() identity on no-trailing-blank carrier), B2=A-reference+I (unescape_quotes==re.sub/str.replace, single pass), B3=A-reference+I (rt_lemma round-trip). Site C: escape_quotes==str.replace("'","''") A-reference, UNCHANGED op used only in the proof.
- A-reference correspondence machine-checked: axiom_check.py (G-AX) run -> exit 0, 'G-AX OK ... deep models == real card.py regex/escape/unescape; round trip identity holds on 25 boundary + 40000 fuzz values'. It imports the real stdlib `re` (the module the patch edits), builds the FIXED and PRE-PATCH _strg_comment_RE verbatim, and asserts escape_quotes==str.replace, unescape_quotes==re.sub, recover_payload(full)==$-anchored strg-group AND prepatch-truncation==unanchored strg-group, plus end-to-end round trip. Both the deep model and its prepatch are faithful to the real regex. Correspondence holds.

CONCLUSION: >=5 distinct wrong impls (6) plus both prepatch bugs were fully verified; every wrong impl was rejected by the fully-pinning postconditions; positive control verifies; A-legs are all A-reference/I/R with empty axioms region and G-AX-validated correspondence. No verify-but-incorrect impl exists under this spec. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-14598.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A long keyword value is serialised by *escaping* every embedded single quote
  U+0027 as a pair of single quotes (the convention for a literal quote inside a
  quoted string), then carrying the escaped text across one or more continuation
  segments. Re-deriving the value from that serialised form must be its exact
  inverse, so that serialise-then-parse is the identity on EVERY value. Two
  independently observable obligations:

  (A) Full payload recovery. The escaped text carried by a continuation segment
      must be recovered IN FULL. Characters that follow an interior space (the
      payload of a quoted string may legitimately contain spaces) are part of
      the payload and must not be dropped: recovery may not stop early at the
      first interior space-adjacent quote. The recovered payload equals the
      segment's escaped text exactly.

  (B) Single un-escape. The recovered escaped text is un-escaped EXACTLY ONCE:
      each leading pair of single quotes collapses to one single quote, every
      other code point is copied. The un-escape is applied a single time, so a
      genuine embedded quote pair is preserved as a quote pair.

  (A) and (B) compose to the round-trip identity: for every value, un-escaping
      the full recovery of its escape returns the original value, in particular
      for a value that contains or ends with an embedded quote pair, with or
      without trailing text and with or without an interior space.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the single quote is the code point 39, the space is 32. The
specification is carried by the pure sequence theory `PSeq[int]`.

There are no axioms. The escaping, the full-payload recovery, and the
un-escaping are all *changed* / supporting operations modelled DEEPLY as
verified folds (`escape_quotes`, `unescape_quotes`). Their agreement with the
real library operations is checked out-of-band by axiom_check.py (G-AX), not
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions; the
per-function regions repeat, one set per modelled obligation.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def escape_quotes(s: PSeq[int]) -> PSeq[int]:
    """Serialisation escape: every single quote (39) becomes a pair of single
    quotes; every other code point is copied. Front-recursive so a single
    unfold is available per loop / proof step."""
    if len(s) == 0:
        return s
    if s[0] == 39:
        return PSeq(39, 39) + escape_quotes(s.drop(1))
    return PSeq(s[0]) + escape_quotes(s.drop(1))


@Pure
def unescape_quotes(s: PSeq[int]) -> PSeq[int]:
    """Parse un-escape applied exactly once: a leading pair of single quotes
    (39,39) collapses to one single quote and parsing continues after the pair;
    any other leading code point is copied and parsing continues after it. The
    single non-overlapping left-to-right collapse of `''` -> `'`."""
    if len(s) < 2:
        return s
    if s[0] == 39 and s[1] == 39:
        return PSeq(39) + unescape_quotes(s.drop(2))
    return PSeq(s[0]) + unescape_quotes(s.drop(1))
# pure-end


def recover_payload(segment: List[int]) -> List[int]:
    """Obligation (A): recover the FULL escaped payload carried by a
    continuation segment. The recovered payload is every code point of the
    segment's carried text -- nothing is dropped at an interior space.

    The carried text does not contain the value/comment separator (code point
    47, '/'): segments whose payload introduces a separator are handled by the
    comment-separation logic and are out of this obligation's scope.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(segment), 1 / 2))
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(segment), segment[k] != 47))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(segment), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The complete carried payload is recovered, in order, in full.
    Ensures(ToSeq(Result()) == ToSeq(segment))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(segment)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(segment), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(segment))
        Invariant(ToSeq(result) == ToSeq(segment).take(j))
        # invariants-end
        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
        result = result + [segment[j]]
        j = j + 1
    Assert(ToSeq(segment).take(n) == ToSeq(segment))
    return result
    # impl-end


def unescape_value(captured: List[int], witness: List[int]) -> List[int]:
    """Obligation (B): un-escape the recovered escaped text EXACTLY ONCE. Each
    leading pair of single quotes collapses to one; every other code point is
    copied. Composing with the full recovery (A) is the round-trip identity:
    `witness` is the read-only original value whose escape this recovers, and
    the un-escape returns it exactly (the round-trip clause).
    """
    # pre-conditions-start
    Requires(Acc(list_pred(captured), 1 / 2))
    Requires(Acc(list_pred(witness), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(captured), 1 / 2))
    Ensures(Acc(list_pred(witness), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Exactly one un-escape pass over the recovered text.
    Ensures(ToSeq(Result()) == unescape_quotes(ToSeq(captured)))
    # Round-trip witness: if the recovered text is the escape of `witness`, this
    # un-escape returns `witness` -- single application is the exact inverse.
    Ensures(Implies(ToSeq(captured) == escape_quotes(ToSeq(witness)),
                    ToSeq(Result()) == ToSeq(witness)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(captured)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(captured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(captured))
        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                  == unescape_quotes(ToSeq(captured)))
        # invariants-end
        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
            Assert(ToSeq(captured).drop(j)[0] == 39)
            Assert(ToSeq(captured).drop(j)[1] == 39)
            Assert(len(ToSeq(captured).drop(j)) >= 2)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
            result = result + [39]
            j = j + 2
        else:
            c = captured[j]
            Assert(ToSeq(captured).drop(j)[0] == c)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
            result = result + [c]
            j = j + 1
    rt_lemma(ToSeq(witness))
    return result
    # impl-end


# The round-trip identity, proved once and quantified, supports the rt witness
# clause of `unescape_value`.
def rt_lemma(v: PSeq[int]) -> None:
    Ensures(unescape_quotes(escape_quotes(v)) == v)
    if len(v) == 0:
        return
    rt_lemma(v.drop(1))
    if v[0] == 39:
        Assert(escape_quotes(v) == PSeq(39, 39) + escape_quotes(v.drop(1)))
        Assert(escape_quotes(v)[0] == 39)
        Assert(escape_quotes(v)[1] == 39)
        Assert(len(escape_quotes(v)) >= 2)
        Assert(escape_quotes(v).drop(2) == escape_quotes(v.drop(1)))
        Assert(unescape_quotes(escape_quotes(v))
               == PSeq(39) + unescape_quotes(escape_quotes(v.drop(1))))
    else:
        Assert(escape_quotes(v) == PSeq(v[0]) + escape_quotes(v.drop(1)))
        Assert(escape_quotes(v)[0] == v[0])
        Assert(v[0] != 39)
        Assert(unescape_quotes(escape_quotes(v))
               == PSeq(v[0]) + unescape_quotes(escape_quotes(v).drop(1)))
        Assert(escape_quotes(v).drop(1) == escape_quotes(v.drop(1)))
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY (G-EQ refinement-fidelity, A-leg focus) for astropy__astropy-14598 / nagini. SBU_BENCHMARK_DIR=benchmark-verified; adversary + verify run via python (main env); nagini_verify.sh drives the pinned JVM+Z3.

SPEC STRUCTURE: The frozen spec pins BOTH functions' outputs completely. recover_payload: Ensures ToSeq(Result())==ToSeq(segment) (full-payload identity on the no-'/' domain, Requires segment[k]!=47). unescape_value: Ensures ToSeq(Result())==unescape_quotes(ToSeq(captured)) (single un-escape pass) PLUS the round-trip clause Implies(ToSeq(captured)==escape_quotes(ToSeq(witness)), ToSeq(Result())==ToSeq(witness)). Because each postcondition is a total functional pin of the return sequence, any verifying impl is functionally determined — leaving no room for a same-spec verifying wrong impl.

SPEC-BOUNDARY MECHANICS (markers.py): spec view elides ONLY impl regions (incl. nested invariants); axioms/@Pure(escape_quotes,unescape_quotes)/Requires/Ensures/rt_lemma are all in the spec signature and must stay byte-identical. All attacks edited ONLY impl regions -> same-spec confirmed for all 6 (and positive control) via `adversary same-spec` exit 0.

### ATTACKS (all: `python -m swebench_unified.adversary weakness nagini astropy__astropy-14598 <path>`):
- atk_1 (boundary/off-by-one, recover): loop `while j<n-1` -> drops last cp. same-spec=SAME; weakness=NOT-A-COUNTEREXAMPLE (verification failed: postcond ToSeq(Result())==ToSeq(segment) fails). REJECTED.
- atk_2 (boundary overrun, recover): appends spurious [39]. REJECTED (does not verify).
- atk_3 (partial-domain, recover): drops interior spaces (cp 32). REJECTED (does not verify).
- atk_4 (ungrounded-oracle echo / no-op, unescape): identity copy, no collapse. REJECTED (postcond ==unescape_quotes(...) fails).
- atk_5 (control-flow-effect off-by-one, unescape): advances j+=3 on a leading quote-pair. REJECTED (does not verify).
- atk_6 (over-collapse, unescape): collapses a run of quotes to a single 39. REJECTED (does not verify).
No attack returned CANDIDATE-COUNTEREXAMPLE, so NO materialized faithful patch / run_resolve was mandated (protocol step 2 triggers only on a verifying candidate). None available to break the spec.

POSITIVE CONTROL: benchmark model.py copied verbatim -> `adversary verify` = VERIFIED in 20.0s (exit 0). Confirms the harness/env verify the intended impl.

### PREPATCH REPRODUCTION (both bug sites, `adversary verify`):
- prepatch_A (model_prepatch_2.py, site A, unanchored-regex truncation at first quote-then-space): FAILED 25.2s — 'Postcondition of recover_payload might not hold. Assertion (ToSeq(Result())==ToSeq(segment)) might not hold.' Spec senses the regex-anchor bug (G-DIFF).
- prepatch_B (model_prepatch.py, site B, double un-escape): FAILED 31.5s — 'Postcondition of unescape_value might not hold. Assertion (ToSeq(Result())==unescape_quotes(ToSeq(captured))) might not hold.' Spec senses the double-un-escape bug (G-DIFF).
prepatch_reproduced=true for both hunks.

A-LEG / MODEL-CORRESPONDENCE AUDIT (refinement.md + mapping.md):
- axioms region is EMPTY in model.py (verified by awk over # axioms-start/-end) => ZERO A-consumed legs; no proof consumes a @ContractOnly Ensures. Consistent with refinement.md §D.
- All legs classify as R, A-reference, or I; no kind-3 (unexpressible-changed-op). Site A: A1=R (str<->List[int]; no-'/' domain), A2=A-reference (the $-anchor's changed property modelled deeply as the full copy). Site B: B1=R (.rstrip() identity on no-trailing-blank carrier), B2=A-reference+I (unescape_quotes==re.sub/str.replace, single pass), B3=A-reference+I (rt_lemma round-trip). Site C: escape_quotes==str.replace("'","''") A-reference, UNCHANGED op used only in the proof.
- A-reference correspondence machine-checked: axiom_check.py (G-AX) run -> exit 0, 'G-AX OK ... deep models == real card.py regex/escape/unescape; round trip identity holds on 25 boundary + 40000 fuzz values'. It imports the real stdlib `re` (the module the patch edits), builds the FIXED and PRE-PATCH _strg_comment_RE verbatim, and asserts escape_quotes==str.replace, unescape_quotes==re.sub, recover_payload(full)==$-anchored strg-group AND prepatch-truncation==unanchored strg-group, plus end-to-end round trip. Both the deep model and its prepatch are faithful to the real regex. Correspondence holds.

CONCLUSION: >=5 distinct wrong impls (6) plus both prepatch bugs were fully verified; every wrong impl was rejected by the fully-pinning postconditions; positive control verifies; A-legs are all A-reference/I/R with empty axioms region and G-AX-validated correspondence. No verify-but-incorrect impl exists under this spec. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (panel_2) audit for astropy__astropy-14598 (nagini). Model verifies (nagini_verify.sh: Verification successful, 16.4s); axiom_check.py exits 0. All three modeled functions provably agree with their designated real callees at base_commit 80c3854a5f on the reachable/documented domain (escaped printable-ASCII payloads, no '/'): escape_quotes==str.replace("'","''") and unescape_quotes==re.sub("''","'") (exhaustive small-alphabet, 0 mismatch); recover_payload(full)==post-patch $-anchored _strg_comment_RE strg-group (exhaustive quote/space/x/y len<=12 + 500k full-printable-ASCII fuzz, 0 divergence, 0 spurious None) — the real capture group includes trailing spaces just as the model does, so full-recovery is faithful. Round-trip identity holds end-to-end against the real regex + real re.sub on all no-'/' printable values incl. the three FAIL_TO_PASS shapes ('x'*100+"''"/"''xxx"/"'' xxx"). 

Two candidate drift vectors examined and cleared: (1) The unmodeled .rstrip() at card.py:862 does strip trailing spaces the model keeps, but unescape_value's round-trip witness clause is GUARDED by captured==escape_quotes(witness); for a trailing-space witness the real rstripped capture != its exact escape, so the antecedent is vacuously false and the spec does NOT over-claim recovery — it matches the real (lossy-on-trailing-space) behavior. (2) recover_payload's precondition only excludes code point 47 ('/'), not non-printables, so e.g. segment [120,10,121] ('x\ny') satisfies the precondition yet the real regex returns None (requires [ -~]); the model claims full recovery there. This is a benign precondition over-broadening: non-printable segments are not valid/reachable FITS card payloads, lie outside the G-AX/mapping-documented printable domain, and are never exercised by G-RESOLVE — it cannot make a wrong impl verify-and-pass. No resolution-relevant diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Assessed the solver-visible spec_view() (impl regions elided to `...`) against the public problem_statement ONLY (hints_text excluded per policy). Mechanical leakage.screen() over the spec view returns passed=True, 0 hard failures, 0 warnings (verified live). Semantic review:

Gold edit = two hunks in astropy/io/fits/card.py: (1) append `$` to `_strg_comment_RE` (card.py:69); (2) `value.rstrip().replace("''","'")` -> `value.rstrip()` (card.py:862).

The spec view names NONE of the discriminating gold-edit specifics: not the file (card.py), not the methods (_split/_parse_value/_format_long_image), not the regex identifier (_strg_comment_RE), not `re.sub`/`.replace`, not the `$` anchor. Confirmed grep of model.py finds 0 occurrences of these repo symbols. It states two abstract correctness OBLIGATIONS over PSeq[int]/List[int] code points: (A) full payload recovery ('recovery may not stop early at the first interior space-adjacent quote') and (B) single un-escape ('un-escaped EXACTLY ONCE'), composing to a round-trip identity. These are behavioural properties a spec is REQUIRED to state, not edit locations/mechanisms.

Crucially, the public problem_statement already discloses at least as much: the ''->' collapse bug, the round-trip failure (card1.value == card2.value where 'Should be the same as card1'), the length/position dependence, and the interior-text variant ('x'*n + "''" + 'x'*10). It explicitly demands 'All card values should be handled properly' — i.e. the round-trip identity that obligations (A)+(B) formalize. So the spec view reveals nothing about the gold edit BEYOND the public statement; the solver must still localize the fix to the regex anchor and the _split un-escape, which the spec view does not point to.

The verbatim gold-diff quotes live in refinement.md/mapping.md (auditor-only refinement docs), NOT in the solver-visible spec view; leak.py screens bundle.solution_src() (model.py) only. The docstring word 'changed' refers to the twin-artifact modeling convention (changed vs supporting operations), not the patched symbol. No diff markers, no reproduced >=8-char gold lines, no patched path, no narration terms. relaxed_leakage flag is absent, so no RELAXED deferral applies (and none is needed). Recorded G-PANEL-3 = NO-LEAKAGE; concur.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
