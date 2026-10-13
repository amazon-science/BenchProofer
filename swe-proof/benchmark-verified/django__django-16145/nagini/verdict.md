# P2 adversarial audit — django__django-16145

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no attack became a CANDIDATE (no same-spec impl verified other than the exact-gold positive control). The postcondition `ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6)` is an EXACT, TOTAL functional equality against the @Pure oracle shown_address, so any TERMINATING verifying impl is forced extensionally equal to gold on every input; and Nagini's proof obligation does not admit a vacuous non-termination bypass here (see atk_2/atk_6). Therefore verify==correct is preserved and no faithful patch needed to be run through run_resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
 def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(addr), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(addr), 1 / 2))
@@ -83,6 +81,7 @@
     # impl-start
     result = []  # type: List[int]
     c = 0
+    i = 0
     if raw_ipv6:
         result = [91]
         i = 0
@@ -92,21 +91,13 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
             Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
         Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
         result = result + [93]
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
-    elif ToSeq(addr) == wildcard_short():
-        result = [48, 46, 48, 46, 48, 46, 48]
-        Assert(ToSeq(result) == wildcard_dotted())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
     else:
         i = 0
         while i < len(addr):
@@ -114,17 +105,12 @@
             Invariant(Acc(list_pred(addr), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(addr) != wildcard_short())
             Invariant(ToSeq(result) == ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
         Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == ToSeq(addr))
-        Assert(ToSeq(addr) != wildcard_short())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
 def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(addr), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(addr), 1 / 2))
@@ -82,49 +80,11 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    c = 0
-    if raw_ipv6:
-        result = [91]
-        i = 0
-        while i < len(addr):
-            # invariants-start
-            Invariant(Acc(list_pred(addr), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
-            # invariants-end
-            c = addr[i]
-            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
-            result = result + [c]
-            i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
-        result = result + [93]
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
-    elif ToSeq(addr) == wildcard_short():
-        result = [48, 46, 48, 46, 48, 46, 48]
-        Assert(ToSeq(result) == wildcard_dotted())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
-    else:
-        i = 0
-        while i < len(addr):
-            # invariants-start
-            Invariant(Acc(list_pred(addr), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(addr) != wildcard_short())
-            Invariant(ToSeq(result) == ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
-            # invariants-end
-            c = addr[i]
-            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
-            result = result + [c]
-            i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == ToSeq(addr))
-        Assert(ToSeq(addr) != wildcard_short())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
+    while True:
+        # invariants-start
+        Invariant(Acc(list_pred(addr), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        # invariants-end
+        result = result
     return result
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
@@ -72,7 +71,6 @@
 def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(addr), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(addr), 1 / 2))
@@ -83,7 +81,10 @@
     # impl-start
     result = []  # type: List[int]
     c = 0
-    if raw_ipv6:
+    i = 0
+    if ToSeq(addr) == wildcard_short():
+        result = [48, 46, 48, 46, 48, 46, 48]
+    elif raw_ipv6:
         result = [91]
         i = 0
         while i < len(addr):
@@ -92,21 +93,12 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
             Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
         result = result + [93]
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
-    elif ToSeq(addr) == wildcard_short():
-        result = [48, 46, 48, 46, 48, 46, 48]
-        Assert(ToSeq(result) == wildcard_dotted())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
     else:
         i = 0
         while i < len(addr):
@@ -114,17 +106,11 @@
             Invariant(Acc(list_pred(addr), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(addr) != wildcard_short())
             Invariant(ToSeq(result) == ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == ToSeq(addr))
-        Assert(ToSeq(addr) != wildcard_short())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
 def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(addr), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(addr), 1 / 2))
@@ -83,6 +81,7 @@
     # impl-start
     result = []  # type: List[int]
     c = 0
+    i = 0
     if raw_ipv6:
         result = [91]
         i = 0
@@ -92,21 +91,14 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
             Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
         result = result + [93]
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
     elif ToSeq(addr) == wildcard_short():
-        result = [48, 46, 48, 46, 48, 46, 48]
-        Assert(ToSeq(result) == wildcard_dotted())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
+        result = [48, 46, 48, 46, 48]
     else:
         i = 0
         while i < len(addr):
@@ -114,17 +106,11 @@
             Invariant(Acc(list_pred(addr), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(addr) != wildcard_short())
             Invariant(ToSeq(result) == ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == ToSeq(addr))
-        Assert(ToSeq(addr) != wildcard_short())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
     return result
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
@@ -72,7 +71,6 @@
 def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(addr), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(addr), 1 / 2))
@@ -83,6 +81,7 @@
     # impl-start
     result = []  # type: List[int]
     c = 0
+    i = 0
     if raw_ipv6:
         result = [91]
         i = 0
@@ -92,21 +91,13 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
             Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
-        result = result + [93]
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
     elif ToSeq(addr) == wildcard_short():
         result = [48, 46, 48, 46, 48, 46, 48]
-        Assert(ToSeq(result) == wildcard_dotted())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
     else:
         i = 0
         while i < len(addr):
@@ -114,17 +105,11 @@
             Invariant(Acc(list_pred(addr), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(addr) != wildcard_short())
             Invariant(ToSeq(result) == ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == ToSeq(addr))
-        Assert(ToSeq(addr) != wildcard_short())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
     return result
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
@@ -72,7 +71,6 @@
 def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(addr), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(addr), 1 / 2))
@@ -83,6 +81,7 @@
     # impl-start
     result = []  # type: List[int]
     c = 0
+    i = 0
     if raw_ipv6:
         result = [91]
         i = 0
@@ -92,21 +91,19 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
             Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
         result = result + [93]
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
     elif ToSeq(addr) == wildcard_short():
-        result = [48, 46, 48, 46, 48, 46, 48]
-        Assert(ToSeq(result) == wildcard_dotted())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
+        while True:
+            # invariants-start
+            Invariant(Acc(list_pred(addr), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            # invariants-end
+            result = result
     else:
         i = 0
         while i < len(addr):
@@ -114,17 +111,11 @@
             Invariant(Acc(list_pred(addr), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(addr) != wildcard_short())
             Invariant(ToSeq(result) == ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
             # invariants-end
             c = addr[i]
             Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
             result = result + [c]
             i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == ToSeq(addr))
-        Assert(ToSeq(addr) != wildcard_short())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
     return result
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
@@ -72,7 +71,6 @@
 def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(addr), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(addr), 1 / 2))
@@ -83,48 +81,17 @@
     # impl-start
     result = []  # type: List[int]
     c = 0
-    if raw_ipv6:
-        result = [91]
-        i = 0
-        while i < len(addr):
-            # invariants-start
-            Invariant(Acc(list_pred(addr), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
-            # invariants-end
-            c = addr[i]
-            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
-            result = result + [c]
-            i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
-        result = result + [93]
-        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
-    elif ToSeq(addr) == wildcard_short():
-        result = [48, 46, 48, 46, 48, 46, 48]
-        Assert(ToSeq(result) == wildcard_dotted())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
-    else:
-        i = 0
-        while i < len(addr):
-            # invariants-start
-            Invariant(Acc(list_pred(addr), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(addr))
-            Invariant(ToSeq(addr) != wildcard_short())
-            Invariant(ToSeq(result) == ToSeq(addr).take(i))
-            Invariant(MustTerminate(len(addr) - i + 1))
-            # invariants-end
-            c = addr[i]
-            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
-            result = result + [c]
-            i = i + 1
-        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
-        Assert(ToSeq(result) == ToSeq(addr))
-        Assert(ToSeq(addr) != wildcard_short())
-        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
+    i = 0
+    while i < len(addr):
+        # invariants-start
+        Invariant(Acc(list_pred(addr), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= i and i <= len(addr))
+        Invariant(ToSeq(result) == ToSeq(addr).take(i))
+        # invariants-end
+        c = addr[i]
+        Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
+        result = result + [c]
+        i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for django__django-16145.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the development server announces the address it is listening on, the
  address that is shown to the operator is derived from the bound address as
  follows:

    * If the bound address is a bracketed literal IPv6 address, the shown
      address is that address enclosed in square brackets (so it reads as a
      valid host part of a URL).

    * Otherwise, if the bound address is the single-character wildcard "0",
      the shown address is its fully-written unspecified-IPv4 equivalent
      "0.0.0.0" — because "0" binds every IPv4 interface yet is not a host a
      browser can follow, whereas "0.0.0.0" denotes the same binding and is a
      usable URL host.

    * Otherwise the shown address is the bound address unchanged.

  These cases are tried in this priority order; in particular the bracketing
  rule takes precedence over the wildcard-expansion rule.

Addresses are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
single code point '0' is U+0030 (48); '.' is U+002E (46); '[' is U+005B (91);
']' is U+005D (93). No callee is axiomatized: the shown address is a pure
piecewise transcription of the bound address, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the shown address is a pure, piecewise transcription of
# the bound address (bracket-wrap / wildcard-expand / identity) over code
# points. Nothing is an unchanged opaque callee whose contract the proof needs.
# axioms-end


# pure-start
@Pure
def wildcard_short() -> PSeq[int]:
    # "0"  (the single-character wildcard form)
    return PSeq(48)


@Pure
def wildcard_dotted() -> PSeq[int]:
    # "0.0.0.0"  (the fully-written unspecified-IPv4 form)
    return PSeq(48, 46, 48, 46, 48, 46, 48)


@Pure
def shown_address(addr: PSeq[int], raw_ipv6: bool) -> PSeq[int]:
    """The address shown to the operator, derived from the bound address.

    Priority order: bracketed-IPv6 first, then the "0" -> "0.0.0.0" wildcard
    expansion, then the bound address unchanged.
    """
    if raw_ipv6:
        return PSeq(91) + addr + PSeq(93)        # "[" + addr + "]"
    if addr == wildcard_short():
        return wildcard_dotted()
    return addr
# pure-end


def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(addr), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(addr), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The shown address is the piecewise transcription of the bound address.
    Ensures(ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    c = 0
    if raw_ipv6:
        result = [91]
        i = 0
        while i < len(addr):
            # invariants-start
            Invariant(Acc(list_pred(addr), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(addr))
            Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
            # invariants-end
            c = addr[i]
            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
            result = result + [c]
            i = i + 1
        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
        result = result + [93]
        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
    elif ToSeq(addr) == wildcard_short():
        result = [48, 46, 48, 46, 48, 46, 48]
        Assert(ToSeq(result) == wildcard_dotted())
        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
    else:
        i = 0
        while i < len(addr):
            # invariants-start
            Invariant(Acc(list_pred(addr), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(addr))
            Invariant(ToSeq(addr) != wildcard_short())
            Invariant(ToSeq(result) == ToSeq(addr).take(i))
            # invariants-end
            c = addr[i]
            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
            result = result + [c]
            i = i + 1
        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
        Assert(ToSeq(result) == ToSeq(addr))
        Assert(ToSeq(addr) != wildcard_short())
        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

verifier via main-env python python + scripts/nagini_verify.sh under concurrent runs. All 8 files (7 attacks + PC) confirmed byte-identical spec via `same-spec` (exit 0 all).

SPEC SHAPE: exact functional postcondition Ensures(ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6)) where shown_address is a TOTAL @Pure oracle (bracket-wrap if raw_ipv6, else '0'->'0.0.0.0' if addr==PSeq(48), else identity), priority order fixed. This pins the output uniquely for every input, so the only realistic verify-not-correct break is non-termination / vacuous partial-correctness (MustTerminate is NOT in the model and NOT in nagini banned_tokens=('Assume(','Refute(')). Both non-termination attacks were exhibited and BOTH failed.

### PER-ATTACK RESULTS (cmd: python -m swebench_unified.adversary weakness nagini django__django-16145 <path>):
- atk_1.py = PREPATCH bug (bracket + verbatim only, no '0'->'0.0.0.0'): NOT-A-COUNTEREXAMPLE, exit 2, 'verification failed' -> postcondition rejects on addr='0',raw_ipv6=False. Confirms G-DIFF: spec senses the exact bug the gold patch fixes. prepatch_reproduced=true.
- atk_2.py = FULL non-termination (while True; return unreachable): NOT-A-COUNTEREXAMPLE, exit 2. Direct nagini_verify (verify_2.txt): EXIT=1, 'Translation failed / Type error: dead.code (atk_2.py@89.0)'. The unreachable trailing return is a translation error, so a whole-body infinite loop cannot smuggle a vacuous proof.
- atk_3.py = WRONG PRIORITY (wildcard checked before raw_ipv6; addr='0',ipv6=True yields '0.0.0.0' vs gold '[0]'): NOT-A-COUNTEREXAMPLE, exit 2, verification failed.
- atk_4.py = BOUNDARY (wildcard returns '0.0.0' — one dot short of '0.0.0.0'): NOT-A-COUNTEREXAMPLE, exit 2, verification failed.
- atk_5.py = BOUNDARY (bracket branch omits closing ']', returns '['+addr): NOT-A-COUNTEREXAMPLE, exit 2, verification failed.
- atk_6.py = CONTROL-FLOW-EFFECT non-termination ONLY on the discriminating addr=='0',ipv6=False case (while True in that branch; final return REACHABLE via other branches so no dead.code): NOT-A-COUNTEREXAMPLE, exit 2. Direct nagini_verify (verify_6.txt): EXIT=1, 'Postcondition of display_address might not hold. Assertion (ToSeq(Result()) == shown_address(...)) might not hold' at 12.14s. Nagini does NOT treat the infinite loop as vacuously establishing the exact functional postcondition -> the targeted non-termination bypass is closed.
- atk_7.py = UNGROUNDED identity echo (always returns addr verbatim, drops both bracket and wildcard): NOT-A-COUNTEREXAMPLE, exit 2, verification failed.

POSITIVE CONTROL atk_pc.py = exact gold impl (byte-identical to model.py, confirmed in-script): nagini_verify EXIT=0, 'Verification successful' 11.82s.

REFINEMENT.MD AUDIT: legs A1-A5 are all R / R+I / I; NO axioms (no A-consumed, no A-reference) — legitimate: the changed operation is primitive Python string formatting/==/literal (f'[{...}]', =='0', '0.0.0.0'), modeled DEEPLY as shown_address's branches over the List[int]/PSeq[int] code-point carrier. No kind-3 (unexpressible-changed-op) leg. mapping.md §3 correctly records no library callee. axiom_check.py RAN: EXIT=0, 'SOUND: model shown_address == gold expression on all 40026 inputs (13 boundary x2 + 40000 fuzz); pre-patch differs from gold on 68, including the discriminating addr=0 (gold 0.0.0.0 vs pre-patch 0)'. The R-refinement (code-point transcription == native gold expression) and the discriminator both hold.

CONCLUSION: >=5 distinct wrong impls (partial-domain, boundary, control-flow-effect x2, wrong-priority, ungrounded echo, prepatch) all rejected by a same, byte-identical spec; positive control verifies; no CANDIDATE => no run_resolve required. verify=>correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no attack became a CANDIDATE (no same-spec impl verified other than the exact-gold positive control). The postcondition `ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6)` is an EXACT, TOTAL functional equality against the @Pure oracle shown_address, so any TERMINATING verifying impl is forced extensionally equal to gold on every input; and Nagini's proof obligation does not admit a vacuous non-termination bypass here (see atk_2/atk_6). Therefore verify==correct is preserved and no faithful patch needed to be run through run_resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for django__django-16145.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the development server announces the address it is listening on, the
  address that is shown to the operator is derived from the bound address as
  follows:

    * If the bound address is a bracketed literal IPv6 address, the shown
      address is that address enclosed in square brackets (so it reads as a
      valid host part of a URL).

    * Otherwise, if the bound address is the single-character wildcard "0",
      the shown address is its fully-written unspecified-IPv4 equivalent
      "0.0.0.0" — because "0" binds every IPv4 interface yet is not a host a
      browser can follow, whereas "0.0.0.0" denotes the same binding and is a
      usable URL host.

    * Otherwise the shown address is the bound address unchanged.

  These cases are tried in this priority order; in particular the bracketing
  rule takes precedence over the wildcard-expansion rule.

Addresses are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
single code point '0' is U+0030 (48); '.' is U+002E (46); '[' is U+005B (91);
']' is U+005D (93). No callee is axiomatized: the shown address is a pure
piecewise transcription of the bound address, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the shown address is a pure, piecewise transcription of
# the bound address (bracket-wrap / wildcard-expand / identity) over code
# points. Nothing is an unchanged opaque callee whose contract the proof needs.
# axioms-end


# pure-start
@Pure
def wildcard_short() -> PSeq[int]:
    # "0"  (the single-character wildcard form)
    return PSeq(48)


@Pure
def wildcard_dotted() -> PSeq[int]:
    # "0.0.0.0"  (the fully-written unspecified-IPv4 form)
    return PSeq(48, 46, 48, 46, 48, 46, 48)


@Pure
def shown_address(addr: PSeq[int], raw_ipv6: bool) -> PSeq[int]:
    """The address shown to the operator, derived from the bound address.

    Priority order: bracketed-IPv6 first, then the "0" -> "0.0.0.0" wildcard
    expansion, then the bound address unchanged.
    """
    if raw_ipv6:
        return PSeq(91) + addr + PSeq(93)        # "[" + addr + "]"
    if addr == wildcard_short():
        return wildcard_dotted()
    return addr
# pure-end


def display_address(addr: List[int], raw_ipv6: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(addr), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(addr), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The shown address is the piecewise transcription of the bound address.
    Ensures(ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    c = 0
    if raw_ipv6:
        result = [91]
        i = 0
        while i < len(addr):
            # invariants-start
            Invariant(Acc(list_pred(addr), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(addr))
            Invariant(ToSeq(result) == PSeq(91) + ToSeq(addr).take(i))
            # invariants-end
            c = addr[i]
            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
            result = result + [c]
            i = i + 1
        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr))
        result = result + [93]
        Assert(ToSeq(result) == PSeq(91) + ToSeq(addr) + PSeq(93))
        Assert(shown_address(ToSeq(addr), raw_ipv6) == PSeq(91) + ToSeq(addr) + PSeq(93))
    elif ToSeq(addr) == wildcard_short():
        result = [48, 46, 48, 46, 48, 46, 48]
        Assert(ToSeq(result) == wildcard_dotted())
        Assert(shown_address(ToSeq(addr), raw_ipv6) == wildcard_dotted())
    else:
        i = 0
        while i < len(addr):
            # invariants-start
            Invariant(Acc(list_pred(addr), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(addr))
            Invariant(ToSeq(addr) != wildcard_short())
            Invariant(ToSeq(result) == ToSeq(addr).take(i))
            # invariants-end
            c = addr[i]
            Assert(ToSeq(addr).take(i + 1) == ToSeq(addr).take(i) + PSeq(c))
            result = result + [c]
            i = i + 1
        Assert(ToSeq(addr).take(len(addr)) == ToSeq(addr))
        Assert(ToSeq(result) == ToSeq(addr))
        Assert(ToSeq(addr) != wildcard_short())
        Assert(shown_address(ToSeq(addr), raw_ipv6) == ToSeq(addr))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

verifier via main-env python python + scripts/nagini_verify.sh under concurrent runs. All 8 files (7 attacks + PC) confirmed byte-identical spec via `same-spec` (exit 0 all).

SPEC SHAPE: exact functional postcondition Ensures(ToSeq(Result()) == shown_address(ToSeq(addr), raw_ipv6)) where shown_address is a TOTAL @Pure oracle (bracket-wrap if raw_ipv6, else '0'->'0.0.0.0' if addr==PSeq(48), else identity), priority order fixed. This pins the output uniquely for every input, so the only realistic verify-not-correct break is non-termination / vacuous partial-correctness (MustTerminate is NOT in the model and NOT in nagini banned_tokens=('Assume(','Refute(')). Both non-termination attacks were exhibited and BOTH failed.

### PER-ATTACK RESULTS (cmd: python -m swebench_unified.adversary weakness nagini django__django-16145 <path>):
- atk_1.py = PREPATCH bug (bracket + verbatim only, no '0'->'0.0.0.0'): NOT-A-COUNTEREXAMPLE, exit 2, 'verification failed' -> postcondition rejects on addr='0',raw_ipv6=False. Confirms G-DIFF: spec senses the exact bug the gold patch fixes. prepatch_reproduced=true.
- atk_2.py = FULL non-termination (while True; return unreachable): NOT-A-COUNTEREXAMPLE, exit 2. Direct nagini_verify (verify_2.txt): EXIT=1, 'Translation failed / Type error: dead.code (atk_2.py@89.0)'. The unreachable trailing return is a translation error, so a whole-body infinite loop cannot smuggle a vacuous proof.
- atk_3.py = WRONG PRIORITY (wildcard checked before raw_ipv6; addr='0',ipv6=True yields '0.0.0.0' vs gold '[0]'): NOT-A-COUNTEREXAMPLE, exit 2, verification failed.
- atk_4.py = BOUNDARY (wildcard returns '0.0.0' — one dot short of '0.0.0.0'): NOT-A-COUNTEREXAMPLE, exit 2, verification failed.
- atk_5.py = BOUNDARY (bracket branch omits closing ']', returns '['+addr): NOT-A-COUNTEREXAMPLE, exit 2, verification failed.
- atk_6.py = CONTROL-FLOW-EFFECT non-termination ONLY on the discriminating addr=='0',ipv6=False case (while True in that branch; final return REACHABLE via other branches so no dead.code): NOT-A-COUNTEREXAMPLE, exit 2. Direct nagini_verify (verify_6.txt): EXIT=1, 'Postcondition of display_address might not hold. Assertion (ToSeq(Result()) == shown_address(...)) might not hold' at 12.14s. Nagini does NOT treat the infinite loop as vacuously establishing the exact functional postcondition -> the targeted non-termination bypass is closed.
- atk_7.py = UNGROUNDED identity echo (always returns addr verbatim, drops both bracket and wildcard): NOT-A-COUNTEREXAMPLE, exit 2, verification failed.

POSITIVE CONTROL atk_pc.py = exact gold impl (byte-identical to model.py, confirmed in-script): nagini_verify EXIT=0, 'Verification successful' 11.82s.

REFINEMENT.MD AUDIT: legs A1-A5 are all R / R+I / I; NO axioms (no A-consumed, no A-reference) — legitimate: the changed operation is primitive Python string formatting/==/literal (f'[{...}]', =='0', '0.0.0.0'), modeled DEEPLY as shown_address's branches over the List[int]/PSeq[int] code-point carrier. No kind-3 (unexpressible-changed-op) leg. mapping.md §3 correctly records no library callee. axiom_check.py RAN: EXIT=0, 'SOUND: model shown_address == gold expression on all 40026 inputs (13 boundary x2 + 40000 fuzz); pre-patch differs from gold on 68, including the discriminating addr=0 (gold 0.0.0.0 vs pre-patch 0)'. The R-refinement (code-point transcription == native gold expression) and the discriminator both hold.

CONCLUSION: >=5 distinct wrong impls (partial-domain, boundary, control-flow-effect x2, wrong-priority, ungrounded echo, prepatch) all rejected by a same, byte-identical spec; positive control verifies; no CANDIDATE => no run_resolve required. verify=>correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function `display_address`/`shown_address` (over the List[int]/PSeq[int] code-point carrier) is an exact transcription of the real post-patch callee in django/core/management/commands/runserver.py `inner_run`: the value bound to "addr" = `f"[{self.addr}]"` if self._raw_ipv6, elif self.addr=="0": "0.0.0.0", else self.addr. Refinement is a true bijection: str<->List[int] code points, '['=91 ']'=93 '0'=48 '.'=46 all correct; "0"<->PSeq(48), "0.0.0.0"<->PSeq(48,46,48,46,48,46,48), bracket-wrap<->PSeq(91)+addr+PSeq(93). Priority order (raw_ipv6 first, then wildcard, then identity) matches the repo branch precedence.

Evidence: (1) axiom_check.py SOUND, 0 violations over 40026 inputs (13 boundary x2 + 40000 fuzz), pre-patch differs on discriminating addr='0'. Independent faithfulness fuzz (fb16145.py) comparing model_shown against the verbatim post-patch f-string derivation: 0 divergences over 300,000+ inputs including adversarial ones (%s, %d, {}, {addr}, '[', ']', '::1', empty string, arabic-indic zero U+0660, fullwidth zero U+FF10, astral U+1F680). (3) nagini_verify.sh on model.py: Verification successful (10.65s). The spec is neither too strong nor drifting; no input found where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over spec_view) passes with zero hard_failures. Verified semantically: the gold edit is the wildcard expansion "0" -> "0.0.0.0" for a non-IPv6 bound address (the f"[{self.addr}]" IPv6 bracketing is PRE-EXISTING behavior preserved from the original expression, not the fix). That exact discriminator is already fully disclosed by the PUBLIC problem_statement, which shows `runserver 0:8000` currently prints http://0:8000/ and states it SHOULD print http://0.0.0.0:8000/. So the spec view reveals nothing about the edit beyond the public problem statement. No diff markers, no gold-patch line reproduced (>=8 normalized chars), no patched file path (runserver.py) or dotted module path in view, no spec-view identifier embeds a patched repo symbol, no bug/fix/patch/previously narration in comments. Docstring frames behaviour as desired ('stated as desired behaviour, not as an edit'), abstract throughout. Spec region byte-identical concern N/A to this role.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
