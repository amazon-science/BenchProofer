# P2 adversarial audit — sympy__sympy-11618

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(u), 1 / 2))
     Requires(Acc(list_pred(v), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(u), 1 / 2))
@@ -114,8 +112,9 @@
                                   len(u) if len(u) >= len(v) else len(v))))
     # post-conditions-end
     # impl-start
+
     n = len(u)
-    if len(v) > n:
+    if len(v) < n:
         n = len(v)
     acc = 0
     i = 0
@@ -124,9 +123,8 @@
         Invariant(Acc(list_pred(u), 1 / 2))
         Invariant(Acc(list_pred(v), 1 / 2))
         Invariant(0 <= i and i <= n)
-        Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
+        Invariant(n == (len(u) if len(u) <= len(v) else len(v)))
         Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         cu = 0
         if i < len(u):
@@ -136,13 +134,10 @@
             cv = v[i]
         Assert(cu == coord(ToSeq(u), i))
         Assert(cv == coord(ToSeq(v), i))
-        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
         Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
         acc = acc + (cu - cv) * (cu - cv)
         i = i + 1
-    Assert(i == n)
-    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
-    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
+    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) <= len(v) else len(v))
     Assert(acc == total)
     return root(total)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(u), 1 / 2))
     Requires(Acc(list_pred(v), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(u), 1 / 2))
@@ -114,19 +112,19 @@
                                   len(u) if len(u) >= len(v) else len(v))))
     # post-conditions-end
     # impl-start
+
     n = len(u)
     if len(v) > n:
         n = len(v)
     acc = 0
     i = 0
-    while i < n:
+    while i < n - 1:
         # invariants-start
         Invariant(Acc(list_pred(u), 1 / 2))
         Invariant(Acc(list_pred(v), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
         Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         cu = 0
         if i < len(u):
@@ -134,15 +132,7 @@
         cv = 0
         if i < len(v):
             cv = v[i]
-        Assert(cu == coord(ToSeq(u), i))
-        Assert(cv == coord(ToSeq(v), i))
-        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
-        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
         acc = acc + (cu - cv) * (cu - cv)
         i = i + 1
-    Assert(i == n)
-    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
-    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
-    Assert(acc == total)
-    return root(total)
+    return root(acc)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(u), 1 / 2))
     Requires(Acc(list_pred(v), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(u), 1 / 2))
@@ -114,6 +112,7 @@
                                   len(u) if len(u) >= len(v) else len(v))))
     # post-conditions-end
     # impl-start
+
     n = len(u)
     if len(v) > n:
         n = len(v)
@@ -125,8 +124,7 @@
         Invariant(Acc(list_pred(v), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
-        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
-        Invariant(MustTerminate(n - i + 1))
+        Invariant(acc >= 0)
         # invariants-end
         cu = 0
         if i < len(u):
@@ -134,15 +132,7 @@
         cv = 0
         if i < len(v):
             cv = v[i]
-        Assert(cu == coord(ToSeq(u), i))
-        Assert(cv == coord(ToSeq(v), i))
-        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
-        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
-        acc = acc + (cu - cv) * (cu - cv)
+        acc = acc + (cu - cv)
         i = i + 1
-    Assert(i == n)
-    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
-    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
-    Assert(acc == total)
-    return root(total)
+    return root(acc)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(u), 1 / 2))
     Requires(Acc(list_pred(v), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(u), 1 / 2))
@@ -114,35 +112,30 @@
                                   len(u) if len(u) >= len(v) else len(v))))
     # post-conditions-end
     # impl-start
-    n = len(u)
-    if len(v) > n:
-        n = len(v)
-    acc = 0
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(u), 1 / 2))
-        Invariant(Acc(list_pred(v), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
-        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        cu = 0
-        if i < len(u):
+
+    if len(u) == len(v):
+        n = len(u)
+        acc = 0
+        i = 0
+        while i < n:
+            # invariants-start
+            Invariant(Acc(list_pred(u), 1 / 2))
+            Invariant(Acc(list_pred(v), 1 / 2))
+            Invariant(0 <= i and i <= n)
+            Invariant(n == len(u))
+            Invariant(len(u) == len(v))
+            Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
+            Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
+            # invariants-end
             cu = u[i]
-        cv = 0
-        if i < len(v):
             cv = v[i]
-        Assert(cu == coord(ToSeq(u), i))
-        Assert(cv == coord(ToSeq(v), i))
-        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
-        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
-        acc = acc + (cu - cv) * (cu - cv)
-        i = i + 1
-    Assert(i == n)
-    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
-    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
-    Assert(acc == total)
-    return root(total)
+            Assert(cu == coord(ToSeq(u), i))
+            Assert(cv == coord(ToSeq(v), i))
+            Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
+            acc = acc + (cu - cv) * (cu - cv)
+            i = i + 1
+        total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
+        Assert(acc == total)
+        return root(total)
+    return root(0)
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(u), 1 / 2))
     Requires(Acc(list_pred(v), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(u), 1 / 2))
@@ -114,35 +112,7 @@
                                   len(u) if len(u) >= len(v) else len(v))))
     # post-conditions-end
     # impl-start
-    n = len(u)
-    if len(v) > n:
-        n = len(v)
-    acc = 0
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(u), 1 / 2))
-        Invariant(Acc(list_pred(v), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
-        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        cu = 0
-        if i < len(u):
-            cu = u[i]
-        cv = 0
-        if i < len(v):
-            cv = v[i]
-        Assert(cu == coord(ToSeq(u), i))
-        Assert(cv == coord(ToSeq(v), i))
-        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
-        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
-        acc = acc + (cu - cv) * (cu - cv)
-        i = i + 1
-    Assert(i == n)
-    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
+
     total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
-    Assert(acc == total)
     return root(total)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(u), 1 / 2))
     Requires(Acc(list_pred(v), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(u), 1 / 2))
@@ -114,9 +112,8 @@
                                   len(u) if len(u) >= len(v) else len(v))))
     # post-conditions-end
     # impl-start
+
     n = len(u)
-    if len(v) > n:
-        n = len(v)
     acc = 0
     i = 0
     while i < n:
@@ -124,9 +121,8 @@
         Invariant(Acc(list_pred(u), 1 / 2))
         Invariant(Acc(list_pred(v), 1 / 2))
         Invariant(0 <= i and i <= n)
-        Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
+        Invariant(n == len(u))
         Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         cu = 0
         if i < len(u):
@@ -134,15 +130,8 @@
         cv = 0
         if i < len(v):
             cv = v[i]
-        Assert(cu == coord(ToSeq(u), i))
-        Assert(cv == coord(ToSeq(v), i))
-        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
         Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
         acc = acc + (cu - cv) * (cu - cv)
         i = i + 1
-    Assert(i == n)
-    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
-    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
-    Assert(acc == total)
-    return root(total)
+    return root(acc)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(u), 1 / 2))
     Requires(Acc(list_pred(v), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(u), 1 / 2))
@@ -114,19 +112,19 @@
                                   len(u) if len(u) >= len(v) else len(v))))
     # post-conditions-end
     # impl-start
+
     n = len(u)
     if len(v) > n:
         n = len(v)
     acc = 0
-    i = 0
+    i = 1
     while i < n:
         # invariants-start
         Invariant(Acc(list_pred(u), 1 / 2))
         Invariant(Acc(list_pred(v), 1 / 2))
-        Invariant(0 <= i and i <= n)
+        Invariant(1 <= i and i <= n or n == 0)
         Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
-        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
-        Invariant(MustTerminate(n - i + 1))
+        Invariant(acc >= 0)
         # invariants-end
         cu = 0
         if i < len(u):
@@ -134,15 +132,7 @@
         cv = 0
         if i < len(v):
             cv = v[i]
-        Assert(cu == coord(ToSeq(u), i))
-        Assert(cv == coord(ToSeq(v), i))
-        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
-        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
         acc = acc + (cu - cv) * (cu - cv)
         i = i + 1
-    Assert(i == n)
-    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
-    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
-    Assert(acc == total)
-    return root(total)
+    return root(acc)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(u), 1 / 2))
     Requires(Acc(list_pred(v), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(u), 1 / 2))
@@ -114,9 +112,10 @@
                                   len(u) if len(u) >= len(v) else len(v))))
     # post-conditions-end
     # impl-start
-    n = len(u)
-    if len(v) > n:
-        n = len(v)
+
+    n = len(v)
+    if len(u) > n:
+        n = len(u)
     acc = 0
     i = 0
     while i < n:
@@ -126,23 +125,11 @@
         Invariant(0 <= i and i <= n)
         Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
         Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        cu = 0
-        if i < len(u):
-            cu = u[i]
-        cv = 0
-        if i < len(v):
-            cv = v[i]
-        Assert(cu == coord(ToSeq(u), i))
-        Assert(cv == coord(ToSeq(v), i))
-        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
+        cu = coord(ToSeq(u), i)
+        cv = coord(ToSeq(v), i)
         Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
         acc = acc + (cu - cv) * (cu - cv)
         i = i + 1
-    Assert(i == n)
-    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
-    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
-    Assert(acc == total)
-    return root(total)
+    return root(acc)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-11618.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two points are described by their coordinate vectors `u` (this point) and `v`
  (the other point), each a finite sequence of scalar coordinates over a common
  axis indexing `0, 1, 2, ...`. The two vectors may have DIFFERENT lengths,
  i.e. live in spaces of different dimension. A point of dimension `d` is
  understood to occupy the larger ambient space by treating every axis beyond
  its own as carrying the coordinate zero.

  The Euclidean distance between the points is the non-negative real number
  whose square is the sum, over EVERY axis `i` of the larger ambient dimension
  `n = max(len(u), len(v))`, of the squared coordinate difference on that axis:

      squared = sum_{i=0}^{n-1} (coord(u, i) - coord(v, i))**2

  where `coord(s, i)` is the i-th coordinate of `s` when `i < len(s)` and zero
  otherwise. In particular, when the two vectors have different lengths the
  axes present only in the longer vector still contribute `(coordinate - 0)**2`
  to the sum; they are NOT dropped. The returned distance is the square root of
  that sum, where the square root is a single, deterministic, order-respecting
  function of its non-negative argument (so two equal sums give one distance and
  a larger sum gives at least as large a distance).

Scalar coordinates are modelled as `int`: the contract concerns WHICH squared
differences enter the sum (the set of axes summed over and the zero-padding of
the shorter vector), which is precision-independent (refinement.md R0). Vectors
are `List[int]`; the specification is carried by `PSeq[int]` via `ToSeq`. The
square root is an opaque, deterministic, monotone callee (axiomatized: equal
arguments give equal results, so the distance is a function of the EXACT
padded sum). Markers (machine-parsed) delimit the spec / proof / impl regions;
provenance binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def root(x: int) -> int:
    """The (unchanged) square-root applied to the squared distance: a single,
    deterministic function of its non-negative argument. The contract encodes
    only what the proof consumes — that it is a deterministic function (equal
    arguments give equal results, automatic for a pure function), so the
    distance is a function of the EXACT padded sum and never an exact value.
    Provenance and the executable soundness check are in mapping.md §3 /
    axiom_check.py (G-AX).
    """
    Requires(x >= 0)
    Ensures(Result() >= 0)
# axioms-end


# pure-start
@Pure
def coord(s: PSeq[int], i: int) -> int:
    """The coordinate of vector `s` on axis `i`: the stored value when the axis
    is within the vector's own dimension, and zero on every axis beyond it
    (the zero-padding of the shorter vector into the larger ambient space)."""
    Requires(i >= 0)
    if i < len(s):
        return s[i]
    return 0


@Pure
def term(u: PSeq[int], v: PSeq[int], i: int) -> int:
    """The squared coordinate difference contributed by axis `i`."""
    Requires(i >= 0)
    return (coord(u, i) - coord(v, i)) * (coord(u, i) - coord(v, i))


@Pure
def psum(u: PSeq[int], v: PSeq[int], k: int) -> int:
    """The sum of the squared coordinate differences over the first `k` axes
    `0 <= i < k`. Prefix-recursive (extends by one axis per step) so the
    accumulation loop's invariant tracks `acc == psum(u, v, i)`. Non-negative,
    since every summand is a square."""
    Requires(k >= 0)
    Ensures(Result() >= 0)
    if k == 0:
        return 0
    return psum(u, v, k - 1) + term(u, v, k - 1)


@Pure
def lemma_psum_unfold(u: PSeq[int], v: PSeq[int], k: int) -> bool:
    """The prefix-recursion equation of `psum`, exposed for callers (its body
    unfolded once)."""
    Requires(k > 0)
    Ensures(Result())
    Ensures(psum(u, v, k) == psum(u, v, k - 1) + term(u, v, k - 1))
    return True
# pure-end


def point_distance(u: List[int], v: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(u), 1 / 2))
    Requires(Acc(list_pred(v), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(u), 1 / 2))
    Ensures(Acc(list_pred(v), 1 / 2))
    # The distance is the square root of the sum of squared coordinate
    # differences over EVERY axis of the larger ambient dimension, with the
    # shorter vector zero-padded. The axes present only in the longer vector
    # contribute their squared coordinate; they are not dropped.
    Ensures(Result() == root(psum(ToSeq(u), ToSeq(v),
                                  len(u) if len(u) >= len(v) else len(v))))
    # post-conditions-end
    # impl-start
    n = len(u)
    if len(v) > n:
        n = len(v)
    acc = 0
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(u), 1 / 2))
        Invariant(Acc(list_pred(v), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
        # invariants-end
        cu = 0
        if i < len(u):
            cu = u[i]
        cv = 0
        if i < len(v):
            cv = v[i]
        Assert(cu == coord(ToSeq(u), i))
        Assert(cv == coord(ToSeq(v), i))
        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    Assert(i == n)
    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
    Assert(acc == total)
    return root(total)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: 8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`, impl-region-only edits, axioms/@Pure/Requires/Ensures untouched). Verified concurrently (=3 JVMs/batch) via `adversary weakness nagini sympy__sympy-11618 <atk>`.

### RESULTS (exact commands, PY=python):
- atk_1.py PREPATCH bug (truncating zip, n=min; returns root(psum(min))): weakness exit=2, NOT-A-COUNTEREXAMPLE (verification failed) => prepatch reproduced & spec senses it.
- atk_2.py BOUNDARY off-by-one (sum first n-1 axes, return root(acc)): exit=2, rejected.
- atk_3.py WRONG-SUMMAND (linear diff, no square, return root(acc)): exit=2, rejected.
- atk_4.py PARTIAL-DOMAIN (correct for equal-dim, root(0) otherwise): exit=2, rejected.
- atk_5.py ECHO / correct impl (returns pinned spec value root(psum(u,v,max))): weakness exit=0, CANDIDATE (shares spec AND verifies, 16.9s).
- atk_6.py CONTROL-FLOW (ignore v length, n=len(u), return root(acc)): exit=2, rejected.
- atk_7.py CONTROL-FLOW (skip axis 0, i starts at 1, return root(acc)): exit=2, rejected.
- atk_8.py UNGROUNDED-ORACLE echo variant (build acc over max axes via coord(), return root(acc)): exit=2, rejected (proof-shape did not close, not a candidate).

MANDATORY RESOLVE for the sole CANDIDATE atk_5: its faithful refined patch is the gold dimension-aware padded-sum patch (atk_5 computes EXACTLY the pinned spec quantity root(psum(u,v,max)), so its behaviourally-faithful concrete refinement is that patch). Ran harness.run_resolve('sympy__sympy-11618', <patch>, timeout=1800): RESOLVED=True, completed=True. report: FAIL_TO_PASS test_issue_11617 success; PASS_TO_PASS test_point3D/test_Point2D/test_issue_9214/test_transform all success; no failures. So the only verify-passing impl RESOLVES => no verify-not-correct witness.

POSITIVE CONTROL pos_control.py (unmodified model.py): bash scripts/nagini_verify.sh => 'Verification successful', exit 0.

WHY THE SPEC IS TIGHT: postcondition pins Result()==root(psum(ToSeq(u),ToSeq(v),max(len(u),len(v)))) with root an opaque @Pure @ContractOnly fn (Nagini treats it uninterpreted; only x>=0=>Result()>=0). Determinism forces any verifying impl to make its returned argument PROVABLY equal to psum(u,v,max) -- the full zero-padded squared-difference sum over the larger ambient dimension. Every wrong summand-set / axis-count / domain defect changes that argument and cannot be proved equal (root is not injective/known), so verification fails -- confirmed empirically by atk_1,2,3,4,6,7.

REFINEMENT AUDIT (refinement.md): legs A1=R (Tuple<->List[int]), A2=I (max), A3=R+I scoped (coord zero-pad <-> gold p1/p2 under guard type(p) is not type(self)), A4=A-reference (deep psum/coord/term model, NO consumed distance axiom), A5=A-consumed (root<->sqrt weakest contract). No kind-3 legs. A-reference correspondence validated out-of-band by G-AX/axiom_check.py (real Point.distance == sqrt(psum(max)) on 9 boundary + 3000 in-domain fuzz pairs, plus negative-control scope boundary asserting same-type differing-dim is NOT padded). A-consumed root<->sqrt checked deterministic+non-negative on boundary+2000 fuzz. Section C 'stronger-than-gold off-domain' is sound: the entire correctness oracle (the resolve test set: 1 distinct-type F2P + 4 equal-dim same-type P2P) lies in the modeled domain, so verify => returns root(psum(max)) => matches gold on every oracle input => resolves. No F2P/P2P input is a same-type differing-dim pair, so the deliberate off-domain strengthening never blocks resolution.

VERDICT: SOUND. >=5 distinct wrong-impl attacks (6 genuinely-wrong: prepatch/boundary/wrong-summand/partial-domain/control-flow x2) all rejected by verification; the single verifying candidate's materialized faithful patch RESOLVES under the official harness. No verify-implies-not-correct witness found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-11618.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two points are described by their coordinate vectors `u` (this point) and `v`
  (the other point), each a finite sequence of scalar coordinates over a common
  axis indexing `0, 1, 2, ...`. The two vectors may have DIFFERENT lengths,
  i.e. live in spaces of different dimension. A point of dimension `d` is
  understood to occupy the larger ambient space by treating every axis beyond
  its own as carrying the coordinate zero.

  The Euclidean distance between the points is the non-negative real number
  whose square is the sum, over EVERY axis `i` of the larger ambient dimension
  `n = max(len(u), len(v))`, of the squared coordinate difference on that axis:

      squared = sum_{i=0}^{n-1} (coord(u, i) - coord(v, i))**2

  where `coord(s, i)` is the i-th coordinate of `s` when `i < len(s)` and zero
  otherwise. In particular, when the two vectors have different lengths the
  axes present only in the longer vector still contribute `(coordinate - 0)**2`
  to the sum; they are NOT dropped. The returned distance is the square root of
  that sum, where the square root is a single, deterministic, order-respecting
  function of its non-negative argument (so two equal sums give one distance and
  a larger sum gives at least as large a distance).

Scalar coordinates are modelled as `int`: the contract concerns WHICH squared
differences enter the sum (the set of axes summed over and the zero-padding of
the shorter vector), which is precision-independent (refinement.md R0). Vectors
are `List[int]`; the specification is carried by `PSeq[int]` via `ToSeq`. The
square root is an opaque, deterministic, monotone callee (axiomatized: equal
arguments give equal results, so the distance is a function of the EXACT
padded sum). Markers (machine-parsed) delimit the spec / proof / impl regions;
provenance binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def root(x: int) -> int:
    """The (unchanged) square-root applied to the squared distance: a single,
    deterministic function of its non-negative argument. The contract encodes
    only what the proof consumes — that it is a deterministic function (equal
    arguments give equal results, automatic for a pure function), so the
    distance is a function of the EXACT padded sum and never an exact value.
    Provenance and the executable soundness check are in mapping.md §3 /
    axiom_check.py (G-AX).
    """
    Requires(x >= 0)
    Ensures(Result() >= 0)
# axioms-end


# pure-start
@Pure
def coord(s: PSeq[int], i: int) -> int:
    """The coordinate of vector `s` on axis `i`: the stored value when the axis
    is within the vector's own dimension, and zero on every axis beyond it
    (the zero-padding of the shorter vector into the larger ambient space)."""
    Requires(i >= 0)
    if i < len(s):
        return s[i]
    return 0


@Pure
def term(u: PSeq[int], v: PSeq[int], i: int) -> int:
    """The squared coordinate difference contributed by axis `i`."""
    Requires(i >= 0)
    return (coord(u, i) - coord(v, i)) * (coord(u, i) - coord(v, i))


@Pure
def psum(u: PSeq[int], v: PSeq[int], k: int) -> int:
    """The sum of the squared coordinate differences over the first `k` axes
    `0 <= i < k`. Prefix-recursive (extends by one axis per step) so the
    accumulation loop's invariant tracks `acc == psum(u, v, i)`. Non-negative,
    since every summand is a square."""
    Requires(k >= 0)
    Ensures(Result() >= 0)
    if k == 0:
        return 0
    return psum(u, v, k - 1) + term(u, v, k - 1)


@Pure
def lemma_psum_unfold(u: PSeq[int], v: PSeq[int], k: int) -> bool:
    """The prefix-recursion equation of `psum`, exposed for callers (its body
    unfolded once)."""
    Requires(k > 0)
    Ensures(Result())
    Ensures(psum(u, v, k) == psum(u, v, k - 1) + term(u, v, k - 1))
    return True
# pure-end


def point_distance(u: List[int], v: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(u), 1 / 2))
    Requires(Acc(list_pred(v), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(u), 1 / 2))
    Ensures(Acc(list_pred(v), 1 / 2))
    # The distance is the square root of the sum of squared coordinate
    # differences over EVERY axis of the larger ambient dimension, with the
    # shorter vector zero-padded. The axes present only in the longer vector
    # contribute their squared coordinate; they are not dropped.
    Ensures(Result() == root(psum(ToSeq(u), ToSeq(v),
                                  len(u) if len(u) >= len(v) else len(v))))
    # post-conditions-end
    # impl-start
    n = len(u)
    if len(v) > n:
        n = len(v)
    acc = 0
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(u), 1 / 2))
        Invariant(Acc(list_pred(v), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == (len(u) if len(u) >= len(v) else len(v)))
        Invariant(acc == psum(ToSeq(u), ToSeq(v), i))
        # invariants-end
        cu = 0
        if i < len(u):
            cu = u[i]
        cv = 0
        if i < len(v):
            cv = v[i]
        Assert(cu == coord(ToSeq(u), i))
        Assert(cv == coord(ToSeq(v), i))
        Assert((cu - cv) * (cu - cv) == term(ToSeq(u), ToSeq(v), i))
        Assert(lemma_psum_unfold(ToSeq(u), ToSeq(v), i + 1))
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    Assert(i == n)
    Assert(n == (len(u) if len(u) >= len(v) else len(v)))
    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
    Assert(acc == total)
    return root(total)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: 8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`, impl-region-only edits, axioms/@Pure/Requires/Ensures untouched). Verified concurrently (=3 JVMs/batch) via `adversary weakness nagini sympy__sympy-11618 <atk>`.

### RESULTS (exact commands, PY=python):
- atk_1.py PREPATCH bug (truncating zip, n=min; returns root(psum(min))): weakness exit=2, NOT-A-COUNTEREXAMPLE (verification failed) => prepatch reproduced & spec senses it.
- atk_2.py BOUNDARY off-by-one (sum first n-1 axes, return root(acc)): exit=2, rejected.
- atk_3.py WRONG-SUMMAND (linear diff, no square, return root(acc)): exit=2, rejected.
- atk_4.py PARTIAL-DOMAIN (correct for equal-dim, root(0) otherwise): exit=2, rejected.
- atk_5.py ECHO / correct impl (returns pinned spec value root(psum(u,v,max))): weakness exit=0, CANDIDATE (shares spec AND verifies, 16.9s).
- atk_6.py CONTROL-FLOW (ignore v length, n=len(u), return root(acc)): exit=2, rejected.
- atk_7.py CONTROL-FLOW (skip axis 0, i starts at 1, return root(acc)): exit=2, rejected.
- atk_8.py UNGROUNDED-ORACLE echo variant (build acc over max axes via coord(), return root(acc)): exit=2, rejected (proof-shape did not close, not a candidate).

MANDATORY RESOLVE for the sole CANDIDATE atk_5: its faithful refined patch is the gold dimension-aware padded-sum patch (atk_5 computes EXACTLY the pinned spec quantity root(psum(u,v,max)), so its behaviourally-faithful concrete refinement is that patch). Ran harness.run_resolve('sympy__sympy-11618', <patch>, timeout=1800): RESOLVED=True, completed=True. report: FAIL_TO_PASS test_issue_11617 success; PASS_TO_PASS test_point3D/test_Point2D/test_issue_9214/test_transform all success; no failures. So the only verify-passing impl RESOLVES => no verify-not-correct witness.

POSITIVE CONTROL pos_control.py (unmodified model.py): bash scripts/nagini_verify.sh => 'Verification successful', exit 0.

WHY THE SPEC IS TIGHT: postcondition pins Result()==root(psum(ToSeq(u),ToSeq(v),max(len(u),len(v)))) with root an opaque @Pure @ContractOnly fn (Nagini treats it uninterpreted; only x>=0=>Result()>=0). Determinism forces any verifying impl to make its returned argument PROVABLY equal to psum(u,v,max) -- the full zero-padded squared-difference sum over the larger ambient dimension. Every wrong summand-set / axis-count / domain defect changes that argument and cannot be proved equal (root is not injective/known), so verification fails -- confirmed empirically by atk_1,2,3,4,6,7.

REFINEMENT AUDIT (refinement.md): legs A1=R (Tuple<->List[int]), A2=I (max), A3=R+I scoped (coord zero-pad <-> gold p1/p2 under guard type(p) is not type(self)), A4=A-reference (deep psum/coord/term model, NO consumed distance axiom), A5=A-consumed (root<->sqrt weakest contract). No kind-3 legs. A-reference correspondence validated out-of-band by G-AX/axiom_check.py (real Point.distance == sqrt(psum(max)) on 9 boundary + 3000 in-domain fuzz pairs, plus negative-control scope boundary asserting same-type differing-dim is NOT padded). A-consumed root<->sqrt checked deterministic+non-negative on boundary+2000 fuzz. Section C 'stronger-than-gold off-domain' is sound: the entire correctness oracle (the resolve test set: 1 distinct-type F2P + 4 equal-dim same-type P2P) lies in the modeled domain, so verify => returns root(psum(max)) => matches gold on every oracle input => resolves. No F2P/P2P input is a same-type differing-dim pair, so the deliberate off-domain strengthening never blocks resolution.

VERDICT: SOUND. >=5 distinct wrong-impl attacks (6 genuinely-wrong: prepatch/boundary/wrong-summand/partial-domain/control-flow x2) all rejected by verification; the single verifying candidate's materialized faithful patch RESOLVES under the official harness. No verify-implies-not-correct witness found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified in worktree at base_commit 360290c4... with the gold patch applied (git diff = +14 lines, the dimension-aware branch). Ran the REAL patched Point.distance via mpmath-backed sympy (python3.8).

MODELED DOMAIN (equal-dimension OR distinct concrete type — the regime where the gold pads/zips over all axes): 151,900 randomized integer-coordinate fuzz pairs, 0 mismatch vs model.py's psum/coord/term encoding. Boundary + F2P confirmed: test_issue_11617 = Point3D(1,0,2).distance(Point2D(2,0)) -> real sqrt(5), model sqrt(5), MATCH.

OFF-DOMAIN (two SAME concrete type points of differing dimension, achievable only for generic n-D Point): the model is DELIBERATELY STRONGER — real callee does NOT pad there (returns 0 for [0] vs [0,0,0,0,5]), model asserts sqrt(25)=5. This is a genuine spec/real disagreement.

WHY STILL FAITHFUL: The divergence is fully documented (refinement.md §C, mapping.md §3.1) and explicitly asserted as a negative control by axiom_check.py. Crucially, EVERY oracle input lies in the modeled domain: F2P test_issue_11617 is Point3D-vs-Point2D (distinct type); the P2P tests (test_point3D, test_Point2D, test_issue_9214, test_transform) are all equal-dimension same-type pairs. No F2P/P2P input is a same-type differing-dim pair. A spec STRONGER than gold off the oracle domain does not break verify⟹resolved: it only forbids implementations that would ALSO pad same-type differing-dim pairs (a superset-correct behaviour the frozen tests never penalize). Any implementation verifying against this spec computes psum(u,v,max) and therefore matches the gold on every oracle input, hence resolves. The spec is neither too weak nor unsoundly too strong for the resolution guarantee.

Spec region (axioms/pure/pre/post markers) matches the bundle; the too-strong region is a documented, oracle-disjoint strengthening, not an unhandled drift.

Counterexample / evidence:

```
u=[0], v=[0,0,0,0,5]: real Point.distance = 0, model = root(psum) = sqrt(25) = 5. Also u=[2,0,0,0], v=[1,0,0,0,7]: real=1, model=5*sqrt(2). Both are same-type (generic n-D Point) differing-dimension pairs the gold leaves on its truncating path.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen (leakage.screen, nagini backend) passes with zero hard failures; semantic review confirms the spec view leaks nothing beyond the public problem_statement. The problem_statement already publicly discloses BOTH the bug and the correct behavior: 'The 3rd dimension is being ignored when the Points are zipped together ... sqrt((2-1)**2 + (0-0)**2) is being computed instead of sqrt(5)' — i.e. the extra dimension must be included and the shorter point is implicitly zero on the missing axis (Point(2,0) -> (2,0,0), axis 2 contributes (0-2)**2=4, sqrt(5)). The spec view (module docstring + coord/term/psum/point_distance contracts) states exactly this DESIRED behavior abstractly: distance = root(sum over every axis i<n of (coord(u,i)-coord(v,i))**2, n=max(len(u),len(v)), shorter vector zero-padded). That is the required behavioral contract already visible in the public task, not the gold edit. The spec view contains NONE of the gold-edit specifics beyond the problem_statement: no patched file/module path (sympy/geometry/point.py, geometry), no patched symbol echo (Point/.distance — it uses an abstract point_distance), no reproduced gold-diff lines (type(p) is not type(self), zip(self.args, p.args), the p1=[0]*max(...)/p2 construction, the min(...) fill loop), no diff markers, and no bug/fix narration disclosing the type-dispatch mechanism. The docstring is explicitly framed 'stated as desired behaviour, not as an edit.' Notably the spec is deliberately STRONGER than the gold (it also pads same-type differing-dim pairs, which the gold's type(p) is not type(self) guard leaves on its truncating path — the source of the G-PANEL-2 UNFAITHFUL verdict), so the spec view diverges from the gold mechanism rather than reproducing it — the opposite of a leak. Internal pointers to refinement.md/mapping.md/axiom_check.py are bundle-audit references, not consumer-facing gold disclosures. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
