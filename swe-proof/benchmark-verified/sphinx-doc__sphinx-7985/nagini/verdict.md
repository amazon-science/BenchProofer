# P2 adversarial audit — sphinx-doc__sphinx-7985

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
@@ -48,7 +48,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -236,7 +235,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -259,10 +257,6 @@
         Invariant(n <= len(target))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
-        # Termination: `i` falls by exactly 1 per pass towards the fixed floor
-        # 0, so `i + 1` strictly decreases; the guard `i > 0` makes it >= 2 at
-        # every loop head.
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -280,7 +274,6 @@
 def scheme_present(target: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -295,12 +288,6 @@
         Invariant(Acc(list_pred(target), 1 / 4))
         Invariant(0 <= k and k <= n and n == len(target))
         Invariant(all_lower_below(ToSeq(target), k))
-        # Termination: the guard's FIRST conjunct `k < n` alone bounds the run --
-        # `k` rises by exactly 1 per pass and `n == len(target)` is fixed (target
-        # is only read), so `n - k + 1` strictly decreases and is >= 2 at every
-        # loop head. The `97 <= target[k]` / `target[k] <= 122` conjuncts only
-        # make the loop exit sooner, so they cannot invalidate the bound.
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
         Assert(lemma_all_lower_extend(ToSeq(target), k))
         k = k + 1
@@ -322,9 +309,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 2))
     # `remote` carries the opaque outcome of the unchanged remote-handling path.
-    # Level 3: strictly above the level-2 callees starts_with / scheme_present,
-    # and it leaves room for the list literals this body builds.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 2))
@@ -374,14 +358,13 @@
     hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
     if not (starts_with(target, hp) or starts_with(target, hsp)):
         if scheme_present(target):
-            # recognised non-verifiable leading shape: nothing to verify
             return UNCHECKED()
         else:
-            if file_exists:
-                return WORKING()
+            if ignore_match:
+                return IGNORED()
             else:
-                if ignore_match:
-                    return IGNORED()
+                if file_exists:
+                    return WORKING()
                 else:
                     return MISSING()
     return remote
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -236,7 +235,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -259,10 +257,6 @@
         Invariant(n <= len(target))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
-        # Termination: `i` falls by exactly 1 per pass towards the fixed floor
-        # 0, so `i + 1` strictly decreases; the guard `i > 0` makes it >= 2 at
-        # every loop head.
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -280,7 +274,6 @@
 def scheme_present(target: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -295,12 +288,6 @@
         Invariant(Acc(list_pred(target), 1 / 4))
         Invariant(0 <= k and k <= n and n == len(target))
         Invariant(all_lower_below(ToSeq(target), k))
-        # Termination: the guard's FIRST conjunct `k < n` alone bounds the run --
-        # `k` rises by exactly 1 per pass and `n == len(target)` is fixed (target
-        # is only read), so `n - k + 1` strictly decreases and is >= 2 at every
-        # loop head. The `97 <= target[k]` / `target[k] <= 122` conjuncts only
-        # make the loop exit sooner, so they cannot invalidate the bound.
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
         Assert(lemma_all_lower_extend(ToSeq(target), k))
         k = k + 1
@@ -322,9 +309,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 2))
     # `remote` carries the opaque outcome of the unchanged remote-handling path.
-    # Level 3: strictly above the level-2 callees starts_with / scheme_present,
-    # and it leaves room for the list literals this body builds.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 2))
@@ -373,16 +357,12 @@
     hp = [104, 116, 116, 112, 58]  # type: List[int]
     hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
     if not (starts_with(target, hp) or starts_with(target, hsp)):
-        if scheme_present(target):
-            # recognised non-verifiable leading shape: nothing to verify
-            return UNCHECKED()
+        if file_exists:
+            return WORKING()
         else:
-            if file_exists:
-                return WORKING()
+            if ignore_match:
+                return IGNORED()
             else:
-                if ignore_match:
-                    return IGNORED()
-                else:
-                    return MISSING()
+                return MISSING()
     return remote
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -236,7 +235,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -259,10 +257,6 @@
         Invariant(n <= len(target))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
-        # Termination: `i` falls by exactly 1 per pass towards the fixed floor
-        # 0, so `i + 1` strictly decreases; the guard `i > 0` makes it >= 2 at
-        # every loop head.
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -280,7 +274,6 @@
 def scheme_present(target: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -295,12 +288,6 @@
         Invariant(Acc(list_pred(target), 1 / 4))
         Invariant(0 <= k and k <= n and n == len(target))
         Invariant(all_lower_below(ToSeq(target), k))
-        # Termination: the guard's FIRST conjunct `k < n` alone bounds the run --
-        # `k` rises by exactly 1 per pass and `n == len(target)` is fixed (target
-        # is only read), so `n - k + 1` strictly decreases and is >= 2 at every
-        # loop head. The `97 <= target[k]` / `target[k] <= 122` conjuncts only
-        # make the loop exit sooner, so they cannot invalidate the bound.
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
         Assert(lemma_all_lower_extend(ToSeq(target), k))
         k = k + 1
@@ -322,9 +309,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 2))
     # `remote` carries the opaque outcome of the unchanged remote-handling path.
-    # Level 3: strictly above the level-2 callees starts_with / scheme_present,
-    # and it leaves room for the list literals this body builds.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 2))
@@ -374,15 +358,8 @@
     hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
     if not (starts_with(target, hp) or starts_with(target, hsp)):
         if scheme_present(target):
-            # recognised non-verifiable leading shape: nothing to verify
             return UNCHECKED()
         else:
-            if file_exists:
-                return WORKING()
-            else:
-                if ignore_match:
-                    return IGNORED()
-                else:
-                    return MISSING()
+            return WORKING()
     return remote
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -236,7 +235,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -259,10 +257,6 @@
         Invariant(n <= len(target))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
-        # Termination: `i` falls by exactly 1 per pass towards the fixed floor
-        # 0, so `i + 1` strictly decreases; the guard `i > 0` makes it >= 2 at
-        # every loop head.
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -280,7 +274,6 @@
 def scheme_present(target: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -295,12 +288,6 @@
         Invariant(Acc(list_pred(target), 1 / 4))
         Invariant(0 <= k and k <= n and n == len(target))
         Invariant(all_lower_below(ToSeq(target), k))
-        # Termination: the guard's FIRST conjunct `k < n` alone bounds the run --
-        # `k` rises by exactly 1 per pass and `n == len(target)` is fixed (target
-        # is only read), so `n - k + 1` strictly decreases and is >= 2 at every
-        # loop head. The `97 <= target[k]` / `target[k] <= 122` conjuncts only
-        # make the loop exit sooner, so they cannot invalidate the bound.
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
         Assert(lemma_all_lower_extend(ToSeq(target), k))
         k = k + 1
@@ -322,9 +309,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 2))
     # `remote` carries the opaque outcome of the unchanged remote-handling path.
-    # Level 3: strictly above the level-2 callees starts_with / scheme_present,
-    # and it leaves room for the list literals this body builds.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 2))
@@ -373,16 +357,6 @@
     hp = [104, 116, 116, 112, 58]  # type: List[int]
     hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
     if not (starts_with(target, hp) or starts_with(target, hsp)):
-        if scheme_present(target):
-            # recognised non-verifiable leading shape: nothing to verify
-            return UNCHECKED()
-        else:
-            if file_exists:
-                return WORKING()
-            else:
-                if ignore_match:
-                    return IGNORED()
-                else:
-                    return MISSING()
+        return remote
     return remote
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -236,7 +235,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -259,10 +257,6 @@
         Invariant(n <= len(target))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
-        # Termination: `i` falls by exactly 1 per pass towards the fixed floor
-        # 0, so `i + 1` strictly decreases; the guard `i > 0` makes it >= 2 at
-        # every loop head.
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -280,7 +274,6 @@
 def scheme_present(target: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -295,12 +288,6 @@
         Invariant(Acc(list_pred(target), 1 / 4))
         Invariant(0 <= k and k <= n and n == len(target))
         Invariant(all_lower_below(ToSeq(target), k))
-        # Termination: the guard's FIRST conjunct `k < n` alone bounds the run --
-        # `k` rises by exactly 1 per pass and `n == len(target)` is fixed (target
-        # is only read), so `n - k + 1` strictly decreases and is >= 2 at every
-        # loop head. The `97 <= target[k]` / `target[k] <= 122` conjuncts only
-        # make the loop exit sooner, so they cannot invalidate the bound.
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
         Assert(lemma_all_lower_extend(ToSeq(target), k))
         k = k + 1
@@ -322,9 +309,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 2))
     # `remote` carries the opaque outcome of the unchanged remote-handling path.
-    # Level 3: strictly above the level-2 callees starts_with / scheme_present,
-    # and it leaves room for the list literals this body builds.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 2))
@@ -367,14 +351,12 @@
     # impl-start
     h = []   # type: List[int]
     h = [35]
-    m = [109, 97, 105, 108, 116, 111, 58]  # type: List[int]
-    if len(target) == 0 or starts_with(target, h) or starts_with(target, m):
+    if len(target) == 0 or starts_with(target, h):
         return UNCHECKED()
     hp = [104, 116, 116, 112, 58]  # type: List[int]
     hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
     if not (starts_with(target, hp) or starts_with(target, hsp)):
         if scheme_present(target):
-            # recognised non-verifiable leading shape: nothing to verify
             return UNCHECKED()
         else:
             if file_exists:
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -236,7 +235,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -259,10 +257,6 @@
         Invariant(n <= len(target))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
-        # Termination: `i` falls by exactly 1 per pass towards the fixed floor
-        # 0, so `i + 1` strictly decreases; the guard `i > 0` makes it >= 2 at
-        # every loop head.
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -280,7 +274,6 @@
 def scheme_present(target: List[int]) -> bool:
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 4))
@@ -295,12 +288,6 @@
         Invariant(Acc(list_pred(target), 1 / 4))
         Invariant(0 <= k and k <= n and n == len(target))
         Invariant(all_lower_below(ToSeq(target), k))
-        # Termination: the guard's FIRST conjunct `k < n` alone bounds the run --
-        # `k` rises by exactly 1 per pass and `n == len(target)` is fixed (target
-        # is only read), so `n - k + 1` strictly decreases and is >= 2 at every
-        # loop head. The `97 <= target[k]` / `target[k] <= 122` conjuncts only
-        # make the loop exit sooner, so they cannot invalidate the bound.
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
         Assert(lemma_all_lower_extend(ToSeq(target), k))
         k = k + 1
@@ -322,9 +309,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(target), 1 / 2))
     # `remote` carries the opaque outcome of the unchanged remote-handling path.
-    # Level 3: strictly above the level-2 callees starts_with / scheme_present,
-    # and it leaves room for the list literals this body builds.
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(target), 1 / 2))
@@ -374,15 +358,14 @@
     hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
     if not (starts_with(target, hp) or starts_with(target, hsp)):
         if scheme_present(target):
-            # recognised non-verifiable leading shape: nothing to verify
             return UNCHECKED()
         else:
             if file_exists:
                 return WORKING()
             else:
                 if ignore_match:
+                    return MISSING()
+                else:
                     return IGNORED()
-                else:
-                    return MISSING()
     return remote
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7985.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reference target is classified, without contacting the network, by reading
  it as a sequence of Unicode code points. The classification distinguishes a
  handful of status outcomes, encoded here as small integers:

      UNCHECKED, WORKING, MISSING, IGNORED  (the locally-decidable outcomes),
      and a remotely-handled outcome whose value is opaque to this spec.

  Two opaque predicates over a target abstract the recognition steps and are
  the ONLY string-shape facts this contract uses:

      `is_skippable(t)`  — t matches a recognised non-verifiable form, so it
                           carries no local claim to verify;
      `is_remote(t)`     — t names a remotely-handled resource, delegated to
                           the unchanged remote path.

  The classification of one target is then:

    (1) A skippable target (`is_skippable`) is UNCHECKED — there is nothing to
        verify for it.

    (2) Otherwise, a non-remote target (`not is_remote`) denotes a resource
        decidable from the local source tree:
          - if it is present, the target is WORKING;
          - else if some configured ignore pattern matches it, it is IGNORED;
          - else the target is MISSING.

    (3) A remote target (`is_remote`) is delegated to the unchanged remote
        path, whose outcome is opaque to this specification.

  The decisive content: a non-remote, non-skippable target that is absent
  locally and matches no ignore pattern is MISSING — it is positively
  verified, not silently passed through as an undecided local target.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]`. The two recognition
predicates are modelled DEEPLY (spelled-out folds over the code points) and
validated == their real counterparts out-of-band by axiom_check.py (G-AX); see
mapping.md for the concrete forms they recognise. Two genuinely
environment-dependent facts — whether the resource is present locally, and
whether any ignore pattern matches — and the opaque remote outcome enter as
values, not as consumed axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No consumed axioms. The two string-recognition decisions used by the
#  classification are modelled DEEPLY below (`starts_with`, `has_uri_scheme`)
#  and validated == their real counterparts out-of-band by axiom_check.py /
#  G-AX (the concrete recognised forms are documented in mapping.md), never
#  consumed. The local-presence fact, the ignore-pattern fact, and the opaque
#  remote outcome are plain input values, not axioms.)
# axioms-end

# pure-start
@Pure
def is_lower(c: int) -> bool:
    """A single code point is an ASCII lowercase letter U+0061..U+007A."""
    return 97 <= c and c <= 122

@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL prefix match. Total: if `s` is shorter than `lit` no such
    match exists, so the result is False. Front-recursive (over both sequences)
    so a single unfold is available per loop step."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))

@Pure
def lemma_prefix_too_long(s: PSeq[int], lit: PSeq[int]) -> bool:
    """If `lit` is strictly longer than `s`, no literal prefix match exists.
    Proven by front-recursion on `s`."""
    Requires(len(lit) > len(s))
    Ensures(Result())
    Ensures(not prefix_eq(s, lit))
    if len(s) == 0:
        return True
    return lemma_prefix_too_long(s.drop(1), lit.drop(1))

@Pure
def lower_run(s: PSeq[int]) -> int:
    """Length of the maximal leading run of ASCII lowercase letters of `s`.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return 0
    if not is_lower(s[0]):
        return 0
    return 1 + lower_run(s.drop(1))

@Pure
def all_lower_below(s: PSeq[int], k: int) -> bool:
    """Every code point of `s` strictly below index `k` is lowercase.
    Front-recursive so a single unfold is available per loop step."""
    Requires(0 <= k and k <= len(s))
    if k == 0:
        return True
    return is_lower(s[0]) and all_lower_below(s.drop(1), k - 1)

@Pure
def lemma_lower_run_eq(s: PSeq[int], k: int) -> bool:
    """If `s[0..k)` are all lowercase and the run stops at `k` (end of `s`, or a
    non-lowercase code point there), then the maximal leading lowercase run has
    length exactly `k`. Proven by front-recursion on `s`/`k`."""
    Requires(0 <= k and k <= len(s))
    Requires(all_lower_below(s, k))
    Requires(k == len(s) or not is_lower(s[k]))
    Ensures(Result())
    Ensures(lower_run(s) == k)
    if k == 0:
        return True
    return lemma_lower_run_eq(s.drop(1), k - 1)

@Pure
def lemma_all_lower_extend(s: PSeq[int], k: int) -> bool:
    """Extending an all-lowercase prefix of length `k` by one more lowercase
    code point at index `k` yields an all-lowercase prefix of length `k+1`.
    Proven by front-recursion."""
    Requires(0 <= k and k < len(s))
    Requires(all_lower_below(s, k))
    Requires(is_lower(s[k]))
    Ensures(Result())
    Ensures(all_lower_below(s, k + 1))
    if k == 0:
        Assert(all_lower_below(s.drop(1), 0))
        Assert(is_lower(s[0]))
        return True
    Assert(lemma_all_lower_extend(s.drop(1), k - 1))
    Assert(is_lower(s[0]))
    return True

@Pure
def lit_http() -> PSeq[int]:
    # one of the recognised "remote" leading literals (code points; mapping.md)
    return PSeq(104, 116, 116, 112, 58)

@Pure
def lit_https() -> PSeq[int]:
    # one of the recognised "remote" leading literals (code points; mapping.md)
    return PSeq(104, 116, 116, 112, 115, 58)

@Pure
def lit_hash() -> PSeq[int]:
    # one of the recognised "skippable" leading literals (code points; mapping.md)
    return PSeq(35)

@Pure
def lit_mailto() -> PSeq[int]:
    # one of the recognised "skippable" leading literals (code points; mapping.md)
    return PSeq(109, 97, 105, 108, 116, 111, 58)

@Pure
def has_uri_scheme(s: PSeq[int]) -> bool:
    """Recognises the leading shape described in mapping.md (a maximal leading
    run of ASCII-lowercase code points, of length >= 1, immediately followed by
    the three code points U+003A, U+002F, U+002F). `k` is the length of that
    leading lowercase run; the result is True iff `k >= 1` and code points
    `k, k+1, k+2` are `:`,`/`,`/`."""
    k = lower_run(s)
    return (
        k >= 1
        and len(s) >= k + 3
        and s[k] == 58
        and s[k + 1] == 47
        and s[k + 2] == 47
    )

# Status codes (the local-classification outcomes; the remote branch carries
# its own opaque outcome value).
@Pure
def UNCHECKED() -> int:
    return 0

@Pure
def WORKING() -> int:
    return 1

@Pure
def MISSING() -> int:
    return 2

@Pure
def IGNORED() -> int:
    return 3

@Pure
def classify(s: PSeq[int], file_exists: bool, ignore_match: bool,
             remote: int) -> int:
    """The full per-target classification, as a pure function of the target
    code points and the three environment facts (file present on disk, an
    ignore pattern matches, the opaque remote outcome). Mirrors the decision
    cascade (1)-(3) above."""
    if len(s) == 0 or prefix_eq(s, lit_hash()) or prefix_eq(s, lit_mailto()):
        return UNCHECKED()
    if not (prefix_eq(s, lit_http()) or prefix_eq(s, lit_https())):
        if has_uri_scheme(s):
            return UNCHECKED()
        if file_exists:
            return WORKING()
        if ignore_match:
            return IGNORED()
        return MISSING()
    return remote
# pure-end

def starts_with(target: List[int], lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL prefix match of `lit` against `target`.
    Ensures(Result() == prefix_eq(ToSeq(target), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    n = len(lit)
    if n > len(target):
        Assert(lemma_prefix_too_long(ToSeq(target), ToSeq(lit)))
        return False
    ok = True
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= n and n == len(lit))
        Invariant(n <= len(target))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
        Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
        # invariants-end
        Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(target).drop(i - 1).drop(1) == ToSeq(target).drop(i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if target[i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(target).drop(0) == ToSeq(target))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end

def scheme_present(target: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 4))
    # Result is the leading-shape recognition decision on `target` (mapping.md).
    Ensures(Result() == has_uri_scheme(ToSeq(target)))
    # post-conditions-end
    # impl-start
    n = len(target)
    k = 0
    while k < n and 97 <= target[k] and target[k] <= 122:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 4))
        Invariant(0 <= k and k <= n and n == len(target))
        Invariant(all_lower_below(ToSeq(target), k))
        # invariants-end
        Assert(lemma_all_lower_extend(ToSeq(target), k))
        k = k + 1
    # k is now the maximal leading lowercase run length.
    Assert(k == n or not is_lower(ToSeq(target)[k]))
    Assert(lemma_lower_run_eq(ToSeq(target), k))
    Assert(lower_run(ToSeq(target)) == k)
    if k < 1:
        return False
    if k + 3 > n:
        return False
    res = (target[k] == 58 and target[k + 1] == 47 and target[k + 2] == 47)
    return res
    # impl-end

def check(target: List[int], file_exists: bool, ignore_match: bool,
          remote: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 2))
    # `remote` carries the opaque outcome of the unchanged remote-handling path.
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 2))
    # The classification is exactly the decision cascade `classify`.
    Ensures(Result() == classify(ToSeq(target), file_exists, ignore_match,
                                  remote))
    # A locally-decidable target (non-remote, non-skippable) that is absent
    # locally and matches no ignore pattern is MISSING; a present one is
    # WORKING; an ignore-matched one is IGNORED.
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and not file_exists
        and not ignore_match,
        Result() == MISSING()))
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and file_exists,
        Result() == WORKING()))
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and not file_exists
        and ignore_match,
        Result() == IGNORED()))
    # post-conditions-end
    # impl-start
    h = []   # type: List[int]
    h = [35]
    m = [109, 97, 105, 108, 116, 111, 58]  # type: List[int]
    if len(target) == 0 or starts_with(target, h) or starts_with(target, m):
        return UNCHECKED()
    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        if scheme_present(target):
            # recognised non-verifiable leading shape: nothing to verify
            return UNCHECKED()
        else:
            if file_exists:
                return WORKING()
            else:
                if ignore_match:
                    return IGNORED()
                else:
                    return MISSING()
    return remote
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle sphinx-doc__sphinx-7985 (nagini). Frozen spec: check(target,file_exists,ignore_match,remote) with a TOTAL functional postcondition Result()==classify(ToSeq(target),file_exists,ignore_match,remote) plus three structural implications pinning MISSING/WORKING/IGNORED to witnessed input+environment properties. classify is a @Pure spelled-out decision cascade (not an opaque oracle), and there are NO value-restricting Requires on the inputs, so the postcondition pins behaviour over the entire input domain; any verifying impl must PRODUCE each outcome through the modelled branch logic. meta axioms=[] (no consumed axioms); the two changed string decisions are A-references (deep models).

PROTOCOL (all files; project root; env SBU_BENCHMARK_DIR=benchmark-verified; verifier env swebench-lean python -m swebench_unified.adversary).

POSITIVE CONTROL (gold model.py copied to positive_control.py): cmd `python -m swebench_unified.adversary verify nagini sphinx-doc__sphinx-7985 .../positive_control.py` -> VERIFIED in 17.5s (exit 0).

PREPATCH (model_prepatch.py copied as atk_prepatch.py): cmd `... weakness nagini sphinx-doc__sphinx-7985 .../atk_prepatch.py` -> same-spec TRUE, does NOT verify (exit 2). It keeps the old ('#','mailto:','ftp:') guard and collapses the whole non-web branch to unclassified code 4; fails Result()==classify for non-web/non-scheme targets (spec demands MISSING/WORKING/IGNORED). prepatch_reproduced=true.

6 DISTINCT same-spec wrong impls (edited ONLY the check() impl region; axioms/@Pure/Requires/Ensures byte-identical; same-spec explicitly confirmed for atk_2/atk_4/atk_6 = SAME, and implied SAME for the rest since weakness checks same-spec before verify).

Each run via `... weakness nagini sphinx-doc__sphinx-7985 .../atk_N.py`: atk_1 (control-flow-effect): swap file_exists/ignore_match priority in the local leaf (differs when both true: gold WORKING, atk IGNORED) -> does NOT verify (exit 2). atk_2 (dropped-branch / boundary): remove the scheme_present unsupported-scheme branch, so e.g. gopher:// non-web targets misroute to WORKING/IGNORED/MISSING instead of UNCHECKED -> does NOT verify (exit 2). atk_3 (control-flow-effect): return WORKING for all non-web/non-scheme targets regardless of file_exists/ignore_match -> does NOT verify (exit 2). atk_4 (ungrounded-oracle echo): delegate the local branch to the opaque `remote` value -> does NOT verify (exit 2). atk_5 (partial-domain / dropped-guard): drop 'mailto:' from the first UNCHECKED guard, so mailto: targets fall to the local branch -> does NOT verify (exit 2). atk_6 (boundary code-swap): swap MISSING<->IGNORED status codes in the local leaf -> does NOT verify (exit 2).

Every attack came back NOT-A-COUNTEREXAMPLE (spec rejected the impl). Zero CANDIDATEs (nothing shares-spec AND verifies), so there is no faithful refined patch to materialize/run through run_resolve; patches={}. The runner re-runs these artifacts.

A-LEG / deep-model audit: ran axiom_check.py (G-AX) copy -> 'G-AX OK: prefix_eq == str.startswith and has_uri_scheme == re.match([a-z]+://) and classify == real post-patch check() over 47 boundary + 80000 fuzz inputs (0 mismatch); 4 F2P targets discriminate fixed vs pre-patch' (exit 0). Confirmed axiom_check.py real_check_postpatch transcribes patch.diff verbatim: guard ('#','mailto:'), not http:/https: -> uri_re.match->UNCHECKED else path.exists->WORKING / to_ignore loop->IGNORED / else->broken(=MISSING), else web branch->remote. refinement.md legs A1-A12 are all R / A-reference / I (no kind-3, per section C); the two genuinely-changed ops (dropped 'ftp:' from the prefix tuple; new [a-z]+:// scheme test) are modelled deeply as A-references validated by G-AX, never consumed axioms. model_inputs_not_axioms = {file_exists, ignore_match, remote} are environment facts / unchanged-branch outcome passed as values, correct. meta.json gates all pass.

VERDICT: SOUND. >=6 distinct wrong impls (+ prepatch) run, none is a verifying counterexample; positive control verifies; G-AX A-references hold; refinement legs sound with no kind-3. No verify-but-incorrect impl exists for this frozen spec (verify=>correct holds here).

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
"""Twin-artifact model for sphinx-doc__sphinx-7985.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reference target is classified, without contacting the network, by reading
  it as a sequence of Unicode code points. The classification distinguishes a
  handful of status outcomes, encoded here as small integers:

      UNCHECKED, WORKING, MISSING, IGNORED  (the locally-decidable outcomes),
      and a remotely-handled outcome whose value is opaque to this spec.

  Two opaque predicates over a target abstract the recognition steps and are
  the ONLY string-shape facts this contract uses:

      `is_skippable(t)`  — t matches a recognised non-verifiable form, so it
                           carries no local claim to verify;
      `is_remote(t)`     — t names a remotely-handled resource, delegated to
                           the unchanged remote path.

  The classification of one target is then:

    (1) A skippable target (`is_skippable`) is UNCHECKED — there is nothing to
        verify for it.

    (2) Otherwise, a non-remote target (`not is_remote`) denotes a resource
        decidable from the local source tree:
          - if it is present, the target is WORKING;
          - else if some configured ignore pattern matches it, it is IGNORED;
          - else the target is MISSING.

    (3) A remote target (`is_remote`) is delegated to the unchanged remote
        path, whose outcome is opaque to this specification.

  The decisive content: a non-remote, non-skippable target that is absent
  locally and matches no ignore pattern is MISSING — it is positively
  verified, not silently passed through as an undecided local target.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]`. The two recognition
predicates are modelled DEEPLY (spelled-out folds over the code points) and
validated == their real counterparts out-of-band by axiom_check.py (G-AX); see
mapping.md for the concrete forms they recognise. Two genuinely
environment-dependent facts — whether the resource is present locally, and
whether any ignore pattern matches — and the opaque remote outcome enter as
values, not as consumed axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No consumed axioms. The two string-recognition decisions used by the
#  classification are modelled DEEPLY below (`starts_with`, `has_uri_scheme`)
#  and validated == their real counterparts out-of-band by axiom_check.py /
#  G-AX (the concrete recognised forms are documented in mapping.md), never
#  consumed. The local-presence fact, the ignore-pattern fact, and the opaque
#  remote outcome are plain input values, not axioms.)
# axioms-end

# pure-start
@Pure
def is_lower(c: int) -> bool:
    """A single code point is an ASCII lowercase letter U+0061..U+007A."""
    return 97 <= c and c <= 122

@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL prefix match. Total: if `s` is shorter than `lit` no such
    match exists, so the result is False. Front-recursive (over both sequences)
    so a single unfold is available per loop step."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))

@Pure
def lemma_prefix_too_long(s: PSeq[int], lit: PSeq[int]) -> bool:
    """If `lit` is strictly longer than `s`, no literal prefix match exists.
    Proven by front-recursion on `s`."""
    Requires(len(lit) > len(s))
    Ensures(Result())
    Ensures(not prefix_eq(s, lit))
    if len(s) == 0:
        return True
    return lemma_prefix_too_long(s.drop(1), lit.drop(1))

@Pure
def lower_run(s: PSeq[int]) -> int:
    """Length of the maximal leading run of ASCII lowercase letters of `s`.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return 0
    if not is_lower(s[0]):
        return 0
    return 1 + lower_run(s.drop(1))

@Pure
def all_lower_below(s: PSeq[int], k: int) -> bool:
    """Every code point of `s` strictly below index `k` is lowercase.
    Front-recursive so a single unfold is available per loop step."""
    Requires(0 <= k and k <= len(s))
    if k == 0:
        return True
    return is_lower(s[0]) and all_lower_below(s.drop(1), k - 1)

@Pure
def lemma_lower_run_eq(s: PSeq[int], k: int) -> bool:
    """If `s[0..k)` are all lowercase and the run stops at `k` (end of `s`, or a
    non-lowercase code point there), then the maximal leading lowercase run has
    length exactly `k`. Proven by front-recursion on `s`/`k`."""
    Requires(0 <= k and k <= len(s))
    Requires(all_lower_below(s, k))
    Requires(k == len(s) or not is_lower(s[k]))
    Ensures(Result())
    Ensures(lower_run(s) == k)
    if k == 0:
        return True
    return lemma_lower_run_eq(s.drop(1), k - 1)

@Pure
def lemma_all_lower_extend(s: PSeq[int], k: int) -> bool:
    """Extending an all-lowercase prefix of length `k` by one more lowercase
    code point at index `k` yields an all-lowercase prefix of length `k+1`.
    Proven by front-recursion."""
    Requires(0 <= k and k < len(s))
    Requires(all_lower_below(s, k))
    Requires(is_lower(s[k]))
    Ensures(Result())
    Ensures(all_lower_below(s, k + 1))
    if k == 0:
        Assert(all_lower_below(s.drop(1), 0))
        Assert(is_lower(s[0]))
        return True
    Assert(lemma_all_lower_extend(s.drop(1), k - 1))
    Assert(is_lower(s[0]))
    return True

@Pure
def lit_http() -> PSeq[int]:
    # one of the recognised "remote" leading literals (code points; mapping.md)
    return PSeq(104, 116, 116, 112, 58)

@Pure
def lit_https() -> PSeq[int]:
    # one of the recognised "remote" leading literals (code points; mapping.md)
    return PSeq(104, 116, 116, 112, 115, 58)

@Pure
def lit_hash() -> PSeq[int]:
    # one of the recognised "skippable" leading literals (code points; mapping.md)
    return PSeq(35)

@Pure
def lit_mailto() -> PSeq[int]:
    # one of the recognised "skippable" leading literals (code points; mapping.md)
    return PSeq(109, 97, 105, 108, 116, 111, 58)

@Pure
def has_uri_scheme(s: PSeq[int]) -> bool:
    """Recognises the leading shape described in mapping.md (a maximal leading
    run of ASCII-lowercase code points, of length >= 1, immediately followed by
    the three code points U+003A, U+002F, U+002F). `k` is the length of that
    leading lowercase run; the result is True iff `k >= 1` and code points
    `k, k+1, k+2` are `:`,`/`,`/`."""
    k = lower_run(s)
    return (
        k >= 1
        and len(s) >= k + 3
        and s[k] == 58
        and s[k + 1] == 47
        and s[k + 2] == 47
    )

# Status codes (the local-classification outcomes; the remote branch carries
# its own opaque outcome value).
@Pure
def UNCHECKED() -> int:
    return 0

@Pure
def WORKING() -> int:
    return 1

@Pure
def MISSING() -> int:
    return 2

@Pure
def IGNORED() -> int:
    return 3

@Pure
def classify(s: PSeq[int], file_exists: bool, ignore_match: bool,
             remote: int) -> int:
    """The full per-target classification, as a pure function of the target
    code points and the three environment facts (file present on disk, an
    ignore pattern matches, the opaque remote outcome). Mirrors the decision
    cascade (1)-(3) above."""
    if len(s) == 0 or prefix_eq(s, lit_hash()) or prefix_eq(s, lit_mailto()):
        return UNCHECKED()
    if not (prefix_eq(s, lit_http()) or prefix_eq(s, lit_https())):
        if has_uri_scheme(s):
            return UNCHECKED()
        if file_exists:
            return WORKING()
        if ignore_match:
            return IGNORED()
        return MISSING()
    return remote
# pure-end

def starts_with(target: List[int], lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL prefix match of `lit` against `target`.
    Ensures(Result() == prefix_eq(ToSeq(target), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    n = len(lit)
    if n > len(target):
        Assert(lemma_prefix_too_long(ToSeq(target), ToSeq(lit)))
        return False
    ok = True
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= n and n == len(lit))
        Invariant(n <= len(target))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(target).drop(i)))
        Invariant(ok == prefix_eq(ToSeq(target).drop(i), ToSeq(lit).drop(i)))
        # invariants-end
        Assert(ToSeq(target).drop(i - 1)[0] == ToSeq(target)[i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(target).drop(i - 1).drop(1) == ToSeq(target).drop(i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if target[i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(target).drop(0) == ToSeq(target))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end

def scheme_present(target: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 4))
    # Result is the leading-shape recognition decision on `target` (mapping.md).
    Ensures(Result() == has_uri_scheme(ToSeq(target)))
    # post-conditions-end
    # impl-start
    n = len(target)
    k = 0
    while k < n and 97 <= target[k] and target[k] <= 122:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 4))
        Invariant(0 <= k and k <= n and n == len(target))
        Invariant(all_lower_below(ToSeq(target), k))
        # invariants-end
        Assert(lemma_all_lower_extend(ToSeq(target), k))
        k = k + 1
    # k is now the maximal leading lowercase run length.
    Assert(k == n or not is_lower(ToSeq(target)[k]))
    Assert(lemma_lower_run_eq(ToSeq(target), k))
    Assert(lower_run(ToSeq(target)) == k)
    if k < 1:
        return False
    if k + 3 > n:
        return False
    res = (target[k] == 58 and target[k + 1] == 47 and target[k + 2] == 47)
    return res
    # impl-end

def check(target: List[int], file_exists: bool, ignore_match: bool,
          remote: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(target), 1 / 2))
    # `remote` carries the opaque outcome of the unchanged remote-handling path.
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(target), 1 / 2))
    # The classification is exactly the decision cascade `classify`.
    Ensures(Result() == classify(ToSeq(target), file_exists, ignore_match,
                                  remote))
    # A locally-decidable target (non-remote, non-skippable) that is absent
    # locally and matches no ignore pattern is MISSING; a present one is
    # WORKING; an ignore-matched one is IGNORED.
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and not file_exists
        and not ignore_match,
        Result() == MISSING()))
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and file_exists,
        Result() == WORKING()))
    Ensures(Implies(
        len(target) > 0
        and not prefix_eq(ToSeq(target), lit_hash())
        and not prefix_eq(ToSeq(target), lit_mailto())
        and not prefix_eq(ToSeq(target), lit_http())
        and not prefix_eq(ToSeq(target), lit_https())
        and not has_uri_scheme(ToSeq(target))
        and not file_exists
        and ignore_match,
        Result() == IGNORED()))
    # post-conditions-end
    # impl-start
    h = []   # type: List[int]
    h = [35]
    m = [109, 97, 105, 108, 116, 111, 58]  # type: List[int]
    if len(target) == 0 or starts_with(target, h) or starts_with(target, m):
        return UNCHECKED()
    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        if scheme_present(target):
            # recognised non-verifiable leading shape: nothing to verify
            return UNCHECKED()
        else:
            if file_exists:
                return WORKING()
            else:
                if ignore_match:
                    return IGNORED()
                else:
                    return MISSING()
    return remote
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle sphinx-doc__sphinx-7985 (nagini). Frozen spec: check(target,file_exists,ignore_match,remote) with a TOTAL functional postcondition Result()==classify(ToSeq(target),file_exists,ignore_match,remote) plus three structural implications pinning MISSING/WORKING/IGNORED to witnessed input+environment properties. classify is a @Pure spelled-out decision cascade (not an opaque oracle), and there are NO value-restricting Requires on the inputs, so the postcondition pins behaviour over the entire input domain; any verifying impl must PRODUCE each outcome through the modelled branch logic. meta axioms=[] (no consumed axioms); the two changed string decisions are A-references (deep models).

PROTOCOL (all files; project root; env SBU_BENCHMARK_DIR=benchmark-verified; verifier env swebench-lean python -m swebench_unified.adversary).

POSITIVE CONTROL (gold model.py copied to positive_control.py): cmd `python -m swebench_unified.adversary verify nagini sphinx-doc__sphinx-7985 .../positive_control.py` -> VERIFIED in 17.5s (exit 0).

PREPATCH (model_prepatch.py copied as atk_prepatch.py): cmd `... weakness nagini sphinx-doc__sphinx-7985 .../atk_prepatch.py` -> same-spec TRUE, does NOT verify (exit 2). It keeps the old ('#','mailto:','ftp:') guard and collapses the whole non-web branch to unclassified code 4; fails Result()==classify for non-web/non-scheme targets (spec demands MISSING/WORKING/IGNORED). prepatch_reproduced=true.

6 DISTINCT same-spec wrong impls (edited ONLY the check() impl region; axioms/@Pure/Requires/Ensures byte-identical; same-spec explicitly confirmed for atk_2/atk_4/atk_6 = SAME, and implied SAME for the rest since weakness checks same-spec before verify).

Each run via `... weakness nagini sphinx-doc__sphinx-7985 .../atk_N.py`: atk_1 (control-flow-effect): swap file_exists/ignore_match priority in the local leaf (differs when both true: gold WORKING, atk IGNORED) -> does NOT verify (exit 2). atk_2 (dropped-branch / boundary): remove the scheme_present unsupported-scheme branch, so e.g. gopher:// non-web targets misroute to WORKING/IGNORED/MISSING instead of UNCHECKED -> does NOT verify (exit 2). atk_3 (control-flow-effect): return WORKING for all non-web/non-scheme targets regardless of file_exists/ignore_match -> does NOT verify (exit 2). atk_4 (ungrounded-oracle echo): delegate the local branch to the opaque `remote` value -> does NOT verify (exit 2). atk_5 (partial-domain / dropped-guard): drop 'mailto:' from the first UNCHECKED guard, so mailto: targets fall to the local branch -> does NOT verify (exit 2). atk_6 (boundary code-swap): swap MISSING<->IGNORED status codes in the local leaf -> does NOT verify (exit 2).

Every attack came back NOT-A-COUNTEREXAMPLE (spec rejected the impl). Zero CANDIDATEs (nothing shares-spec AND verifies), so there is no faithful refined patch to materialize/run through run_resolve; patches={}. The runner re-runs these artifacts.

A-LEG / deep-model audit: ran axiom_check.py (G-AX) copy -> 'G-AX OK: prefix_eq == str.startswith and has_uri_scheme == re.match([a-z]+://) and classify == real post-patch check() over 47 boundary + 80000 fuzz inputs (0 mismatch); 4 F2P targets discriminate fixed vs pre-patch' (exit 0). Confirmed axiom_check.py real_check_postpatch transcribes patch.diff verbatim: guard ('#','mailto:'), not http:/https: -> uri_re.match->UNCHECKED else path.exists->WORKING / to_ignore loop->IGNORED / else->broken(=MISSING), else web branch->remote. refinement.md legs A1-A12 are all R / A-reference / I (no kind-3, per section C); the two genuinely-changed ops (dropped 'ftp:' from the prefix tuple; new [a-z]+:// scheme test) are modelled deeply as A-references validated by G-AX, never consumed axioms. model_inputs_not_axioms = {file_exists, ignore_match, remote} are environment facts / unchanged-branch outcome passed as values, correct. meta.json gates all pass.

VERDICT: SOUND. >=6 distinct wrong impls (+ prepatch) run, none is a verifying counterexample; positive control verifies; G-AX A-references hold; refinement legs sound with no kind-3. No verify-but-incorrect impl exists for this frozen spec (verify=>correct holds here).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/spec-drift audit for sphinx-doc__sphinx-7985 (nagini). Verdict: FAITHFUL — no input found where a modeled function disagrees with the real repo callee.

Setup verified: worktree is at base_commit f30284e and its `git diff` shows the gold patch applied to sphinx/builders/linkcheck.py; the post-patch nested check() body matches the modeled decision cascade exactly (ftp: dropped from the first startswith tuple; new module-level `uri_re = re.compile('[a-z]+://')` used as an `if uri_re.match(uri)` gate; else-branch does path.exists -> working / to_ignore loop -> ignored / else -> broken).

Modeling boundaries checked:
- prefix_eq/starts_with == str.startswith (anchored literal prefix; tuple form = per-prefix disjunction). Confirmed for #, mailto:, http:, https:, ftp:.
- has_uri_scheme/scheme_present == re.match('[a-z]+://'). `[a-z]` is an ASCII char range (not \w), so ASCII-lowercase-only (is_lower = 97..122) is correct even for Unicode strings; greedy `+` cannot backtrack to a shorter run because the char terminating a maximal lowercase run is never ':' — so 'maximal leading [a-z] run k>=1 then ://' is exactly the anchored regex.
- classify == post-patch check(); file_exists / ignore_match / remote are faithful value-abstractions of path.exists(join(srcdir,uri)), the inner `for rex in self.to_ignore: rex.match(uri)` loop, and the unchanged web branch. The `remote` param is a free input so the spec neither over- nor under-constrains the unchanged branch.

Evidence:
1. axiom_check.py (G-AX) exit 0: 47 boundary + 80000 fuzz, 0 mismatch; 4 F2P targets discriminate fixed vs pre-patch.
2. Independent adversarial re-implementation fuzz: 400,000 random inputs over a broad alphabet (ASCII lowercase/uppercase/digits/punct/whitespace PLUS Unicode: accented lowercase é ç ß µ, Greek λ Ω, ligatures ﬀ ﬁ, fullwidth latin ａ ｚ, fullwidth colon ： and slash ／, dotless/dotted i, long s ſ) + 39 targeted regex-backtracking edge cases (a://, abc:/, µa://, aＡ://, ａ://, http:, gopher://, HTTP://, 1://, A://, etc.) — checked startswith(5 literals), has_uri_scheme, and classify(all fe/im combos). Zero divergence.

The spec's extra MISSING/WORKING/IGNORED postcondition implications are strict corollaries of `classify` (redundant reinforcement, not an over-strong constraint). Spec region is the frozen bundle spec (only impl region under audit). No spec-too-strong drift detected.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement only (not hints_text). Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures): no diff markers, no reproduced gold-patch line >=8 chars, no patched file path 'sphinx/builders/linkcheck.py' or module 'sphinx.builders.linkcheck', no spec-view identifier/comment echoing a patched repo symbol (e.g. uri_re, check_uri, CheckExternalLinksBuilder), and no bug/fix narration terms. meta G-LEAK=pass, relaxed_leakage=None, no RELAXED_LEAKAGE.md.

Semantic gold-reconstruction review of the spec view (docstring + axioms comment + pure region + check/starts_with/scheme_present pre/post-conditions):
- The decisive gold edit token 'ftp:' (the literal removed from the ('#','mailto:','ftp:') tuple) is ENTIRELY ABSENT from the spec view. The spec models only '#', 'mailto:', 'http:', 'https:' literals and a generic [a-z]+:// scheme shape; the ftp special-case that the patch deletes is nowhere reconstructable.
- The classification the spec pins (a non-remote, non-skippable local target that is absent -> MISSING/'broken', present -> WORKING, ignore-matched -> IGNORED) is exactly the behavior the PUBLIC problem_statement requests ('linkcheck could also check local (internal) links'; 'broken local-link' / 'doesntexist' -> broken; 'Expected results: Also a check for the local link'). Specifying required behavior that the task itself states is legitimate behavioral specification, not edit leakage.
- The docstring explicitly frames content as 'desired behaviour, not as an edit' and abstracts the two string decisions as opaque predicates (is_skippable/is_remote); it does not narrate a before/after, a bug, or the diff.
- The [a-z]+:// scheme-recognition (has_uri_scheme/scheme_present) is a behavioral detail beyond the literal problem-statement prose, but it is expressed positively as part of the correct classification a verifier must pin down, not as a reproduction of the gold hunk (the regex literal '[a-z]+://', the symbol uri_re, and the file path never appear in the spec view). This is inherent spec content, not gold-edit leakage.
- Comments in the spec view (lit_http/lit_https/lit_hash/lit_mailto provenance notes, status-code notes, contract descriptions) describe modeled meaning and reference mapping.md/axiom_check.py, none naming the patched symbol or the edit.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.