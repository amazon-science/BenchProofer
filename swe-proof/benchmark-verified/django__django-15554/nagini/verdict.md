# P2 adversarial audit — django__django-15554

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none - no verifying wrong impl found. The only CANDIDATE (atk_5, the pure-oracle echo returning no_eligible_match(...) directly) is behaviourally identical to the reference; its faithful refined patch is the gold patch, which RESOLVES under the official harness (run_resolve: resolved=True, completed=True). A resolving echo is not a weakness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     Requires(len(base) == len(reuse_mask))
     # in constrained mode reuse is genuinely constrained (reuse set supplied).
     Requires(Implies(constrained, not reuse_all))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -162,14 +160,13 @@
             found,
             not no_eligible_match(
                 base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         if constrained:
             if reuse_mask[i] and matches_constrained(i, n, jb, base):
                 found = True
         else:
             if reusable(i, n, reuse_all, reuse_mask) and \
-                    matches_default(i, n, jb, jf, base, frel):
+                    matches_constrained(i, n, jb, base):
                 found = True
         i = i + 1
     return not found
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     Requires(len(base) == len(reuse_mask))
     # in constrained mode reuse is genuinely constrained (reuse set supplied).
     Requires(Implies(constrained, not reuse_all))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -129,48 +127,5 @@
         base, frel, reuse_all, reuse_mask, jb, jf, constrained))
     # post-conditions-end
     # impl-start
-    n = len(base)
-    found = False
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(base), 1 / 2))
-        Invariant(Acc(list_pred(frel), 1 / 2))
-        Invariant(Acc(list_pred(reuse_mask), 1 / 2))
-        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)
-        Invariant(0 <= i and i <= n)
-        Invariant(Implies(constrained, not reuse_all))
-        Invariant(ToSeq(base) == Old(ToSeq(base)))
-        Invariant(ToSeq(frel) == Old(ToSeq(frel)))
-        # While no match has been seen, no eligible slot among 0..i matches.
-        Invariant(Implies(
-            not found,
-            Implies(not constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reusable(k, n, reuse_all, reuse_mask)
-                             and matches_default(k, n, jb, jf, base, frel)))
-            )))))
-        Invariant(Implies(
-            not found,
-            Implies(constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reuse_mask[k]
-                             and matches_constrained(k, n, jb, base)))
-            )))))
-        # Once a match has been seen, an eligible matching slot provably exists.
-        Invariant(Implies(
-            found,
-            not no_eligible_match(
-                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        if constrained:
-            if reuse_mask[i] and matches_constrained(i, n, jb, base):
-                found = True
-        else:
-            if reusable(i, n, reuse_all, reuse_mask) and \
-                    matches_default(i, n, jb, jf, base, frel):
-                found = True
-        i = i + 1
-    return not found
+    return True
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     Requires(len(base) == len(reuse_mask))
     # in constrained mode reuse is genuinely constrained (reuse set supplied).
     Requires(Implies(constrained, not reuse_all))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -132,8 +130,7 @@
     n = len(base)
     found = False
     i = 0
-    while i < n:
-        # invariants-start
+    while i < n - 1:
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(frel), 1 / 2))
         Invariant(Acc(list_pred(reuse_mask), 1 / 2))
@@ -142,28 +139,6 @@
         Invariant(Implies(constrained, not reuse_all))
         Invariant(ToSeq(base) == Old(ToSeq(base)))
         Invariant(ToSeq(frel) == Old(ToSeq(frel)))
-        # While no match has been seen, no eligible slot among 0..i matches.
-        Invariant(Implies(
-            not found,
-            Implies(not constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reusable(k, n, reuse_all, reuse_mask)
-                             and matches_default(k, n, jb, jf, base, frel)))
-            )))))
-        Invariant(Implies(
-            not found,
-            Implies(constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reuse_mask[k]
-                             and matches_constrained(k, n, jb, base)))
-            )))))
-        # Once a match has been seen, an eligible matching slot provably exists.
-        Invariant(Implies(
-            found,
-            not no_eligible_match(
-                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         if constrained:
             if reuse_mask[i] and matches_constrained(i, n, jb, base):
                 found = True
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     Requires(len(base) == len(reuse_mask))
     # in constrained mode reuse is genuinely constrained (reuse set supplied).
     Requires(Implies(constrained, not reuse_all))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -133,7 +131,6 @@
     found = False
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(frel), 1 / 2))
         Invariant(Acc(list_pred(reuse_mask), 1 / 2))
@@ -142,34 +139,11 @@
         Invariant(Implies(constrained, not reuse_all))
         Invariant(ToSeq(base) == Old(ToSeq(base)))
         Invariant(ToSeq(frel) == Old(ToSeq(frel)))
-        # While no match has been seen, no eligible slot among 0..i matches.
-        Invariant(Implies(
-            not found,
-            Implies(not constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reusable(k, n, reuse_all, reuse_mask)
-                             and matches_default(k, n, jb, jf, base, frel)))
-            )))))
-        Invariant(Implies(
-            not found,
-            Implies(constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reuse_mask[k]
-                             and matches_constrained(k, n, jb, base)))
-            )))))
-        # Once a match has been seen, an eligible matching slot provably exists.
-        Invariant(Implies(
-            found,
-            not no_eligible_match(
-                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         if constrained:
-            if reuse_mask[i] and matches_constrained(i, n, jb, base):
+            if reuse_mask[i]:
                 found = True
         else:
-            if reusable(i, n, reuse_all, reuse_mask) and \
-                    matches_default(i, n, jb, jf, base, frel):
+            if reusable(i, n, reuse_all, reuse_mask):
                 found = True
         i = i + 1
     return not found
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     Requires(len(base) == len(reuse_mask))
     # in constrained mode reuse is genuinely constrained (reuse set supplied).
     Requires(Implies(constrained, not reuse_all))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -129,48 +127,5 @@
         base, frel, reuse_all, reuse_mask, jb, jf, constrained))
     # post-conditions-end
     # impl-start
-    n = len(base)
-    found = False
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(base), 1 / 2))
-        Invariant(Acc(list_pred(frel), 1 / 2))
-        Invariant(Acc(list_pred(reuse_mask), 1 / 2))
-        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)
-        Invariant(0 <= i and i <= n)
-        Invariant(Implies(constrained, not reuse_all))
-        Invariant(ToSeq(base) == Old(ToSeq(base)))
-        Invariant(ToSeq(frel) == Old(ToSeq(frel)))
-        # While no match has been seen, no eligible slot among 0..i matches.
-        Invariant(Implies(
-            not found,
-            Implies(not constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reusable(k, n, reuse_all, reuse_mask)
-                             and matches_default(k, n, jb, jf, base, frel)))
-            )))))
-        Invariant(Implies(
-            not found,
-            Implies(constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reuse_mask[k]
-                             and matches_constrained(k, n, jb, base)))
-            )))))
-        # Once a match has been seen, an eligible matching slot provably exists.
-        Invariant(Implies(
-            found,
-            not no_eligible_match(
-                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        if constrained:
-            if reuse_mask[i] and matches_constrained(i, n, jb, base):
-                found = True
-        else:
-            if reusable(i, n, reuse_all, reuse_mask) and \
-                    matches_default(i, n, jb, jf, base, frel):
-                found = True
-        i = i + 1
-    return not found
+    return no_eligible_match(base, frel, reuse_all, reuse_mask, jb, jf, constrained)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     Requires(len(base) == len(reuse_mask))
     # in constrained mode reuse is genuinely constrained (reuse set supplied).
     Requires(Implies(constrained, not reuse_all))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -133,7 +131,6 @@
     found = False
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(frel), 1 / 2))
         Invariant(Acc(list_pred(reuse_mask), 1 / 2))
@@ -142,30 +139,8 @@
         Invariant(Implies(constrained, not reuse_all))
         Invariant(ToSeq(base) == Old(ToSeq(base)))
         Invariant(ToSeq(frel) == Old(ToSeq(frel)))
-        # While no match has been seen, no eligible slot among 0..i matches.
-        Invariant(Implies(
-            not found,
-            Implies(not constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reusable(k, n, reuse_all, reuse_mask)
-                             and matches_default(k, n, jb, jf, base, frel)))
-            )))))
-        Invariant(Implies(
-            not found,
-            Implies(constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reuse_mask[k]
-                             and matches_constrained(k, n, jb, base)))
-            )))))
-        # Once a match has been seen, an eligible matching slot provably exists.
-        Invariant(Implies(
-            found,
-            not no_eligible_match(
-                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         if constrained:
-            if reuse_mask[i] and matches_constrained(i, n, jb, base):
+            if reuse_mask[i] and matches_default(i, n, jb, jf, base, frel):
                 found = True
         else:
             if reusable(i, n, reuse_all, reuse_mask) and \
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     Requires(len(base) == len(reuse_mask))
     # in constrained mode reuse is genuinely constrained (reuse set supplied).
     Requires(Implies(constrained, not reuse_all))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -133,7 +131,6 @@
     found = False
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(frel), 1 / 2))
         Invariant(Acc(list_pred(reuse_mask), 1 / 2))
@@ -142,34 +139,11 @@
         Invariant(Implies(constrained, not reuse_all))
         Invariant(ToSeq(base) == Old(ToSeq(base)))
         Invariant(ToSeq(frel) == Old(ToSeq(frel)))
-        # While no match has been seen, no eligible slot among 0..i matches.
-        Invariant(Implies(
-            not found,
-            Implies(not constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reusable(k, n, reuse_all, reuse_mask)
-                             and matches_default(k, n, jb, jf, base, frel)))
-            )))))
-        Invariant(Implies(
-            not found,
-            Implies(constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reuse_mask[k]
-                             and matches_constrained(k, n, jb, base)))
-            )))))
-        # Once a match has been seen, an eligible matching slot provably exists.
-        Invariant(Implies(
-            found,
-            not no_eligible_match(
-                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         if constrained:
             if reuse_mask[i] and matches_constrained(i, n, jb, base):
                 found = True
         else:
-            if reusable(i, n, reuse_all, reuse_mask) and \
-                    matches_default(i, n, jb, jf, base, frel):
+            if matches_default(i, n, jb, jf, base, frel):
                 found = True
         i = i + 1
     return not found
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -110,7 +109,6 @@
     Requires(len(base) == len(reuse_mask))
     # in constrained mode reuse is genuinely constrained (reuse set supplied).
     Requires(Implies(constrained, not reuse_all))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -133,7 +131,6 @@
     found = False
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(frel), 1 / 2))
         Invariant(Acc(list_pred(reuse_mask), 1 / 2))
@@ -142,28 +139,6 @@
         Invariant(Implies(constrained, not reuse_all))
         Invariant(ToSeq(base) == Old(ToSeq(base)))
         Invariant(ToSeq(frel) == Old(ToSeq(frel)))
-        # While no match has been seen, no eligible slot among 0..i matches.
-        Invariant(Implies(
-            not found,
-            Implies(not constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reusable(k, n, reuse_all, reuse_mask)
-                             and matches_default(k, n, jb, jf, base, frel)))
-            )))))
-        Invariant(Implies(
-            not found,
-            Implies(constrained, Forall(int, lambda k: (
-                Implies(0 <= k and k < i,
-                        not (reuse_mask[k]
-                             and matches_constrained(k, n, jb, base)))
-            )))))
-        # Once a match has been seen, an eligible matching slot provably exists.
-        Invariant(Implies(
-            found,
-            not no_eligible_match(
-                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         if constrained:
             if reuse_mask[i] and matches_constrained(i, n, jb, base):
                 found = True
@@ -172,5 +147,5 @@
                     matches_default(i, n, jb, jf, base, frel):
                 found = True
         i = i + 1
-    return not found
+    return found
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15554.

Behaviour under specification (stated as desired behaviour, not as an edit):

A query maintains a registry of relation-join descriptors. Each descriptor has
a *base relation identity* (which underlying relation and connection it joins)
and an optional *refinement tag* (an extra per-join filtering refinement; tag 0
means "no refinement", a positive tag denotes a specific refinement). When a new
join descriptor must be installed, the registry first looks for an existing slot
it may reuse:

  - In the default mode the candidate is permitted to reuse a slot only when
    that slot matches the new descriptor on BOTH its base relation identity AND
    its refinement tag. Two descriptors that share the same base relation but
    carry DIFFERENT refinement tags are therefore NOT collapsed onto one slot:
    the second one is installed into a fresh slot of its own.

  - In the constrained mode the candidate may reuse only a slot drawn from an
    explicitly supplied reuse set, and the match is taken on the base relation
    identity alone (the refinement is supplied by the constrained caller).

If a reusable slot exists the existing slot is returned; otherwise a fresh slot
is appended and its index returned. The function reports whether a fresh slot
was created — the observable consequence the registry guarantees.

The decisive property: with two same-base, distinct-refinement descriptors and
default reuse, installing the second must create a NEW slot rather than reusing
the first — so distinct refinements of one relation are preserved, not merged.

The registry is modelled with parallel `List[int]` arrays (base identity and
refinement tag of each slot) plus the reuse set as a `List[bool]` mask and an
"all reusable" flag (the unconstrained case). Marker regions delimit the spec /
proof / impl.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the modelled operation is integer/equality comparison over the
#  slot registry, fully expressible in Nagini; no opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def reusable(i: int, n: int, reuse_all: bool, reuse_mask: List[bool]) -> bool:
    """A slot index i is reuse-eligible if all slots are reusable (the
    unconstrained case) or i is flagged in the supplied reuse mask."""
    Requires(Acc(list_pred(reuse_mask), 1 / 8))
    Requires(0 <= i and i < n and n == len(reuse_mask))
    return reuse_all or reuse_mask[i]


@Pure
def matches_default(i: int, n: int, jb: int, jf: int,
                    base: List[int], frel: List[int]) -> bool:
    """The default-mode match predicate: slot i matches the incoming
    descriptor (jb, jf) on BOTH the base relation identity AND the refinement
    tag."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(Acc(list_pred(frel), 1 / 8))
    Requires(0 <= i and i < n and n == len(base) and n == len(frel))
    return base[i] == jb and frel[i] == jf


@Pure
def matches_constrained(i: int, n: int, jb: int,
                        base: List[int]) -> bool:
    """The constrained-mode match predicate: slot i matches on the base
    relation identity alone."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(0 <= i and i < n and n == len(base))
    return base[i] == jb


@Pure
def no_eligible_match(base: List[int], frel: List[int],
                      reuse_all: bool, reuse_mask: List[bool],
                      jb: int, jf: int, constrained: bool) -> bool:
    """True iff NO reuse-eligible slot matches the incoming descriptor under
    the active match predicate — the condition that forces a fresh slot."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(Acc(list_pred(frel), 1 / 8))
    Requires(Acc(list_pred(reuse_mask), 1 / 8))
    Requires(len(base) == len(frel) and len(base) == len(reuse_mask))
    if constrained:
        return Forall(int, lambda k: (
            Implies(0 <= k and k < len(base),
                    not (reuse_mask[k]
                         and matches_constrained(k, len(base), jb, base)))))
    return Forall(int, lambda k: (
        Implies(0 <= k and k < len(base),
                not (reusable(k, len(base), reuse_all, reuse_mask)
                     and matches_default(k, len(base), jb, jf, base, frel)))))
# pure-end


def install_join(base: List[int], frel: List[int],
                 reuse_all: bool, reuse_mask: List[bool],
                 jb: int, jf: int,
                 constrained: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(frel), 1 / 2))
    Requires(Acc(list_pred(reuse_mask), 1 / 2))
    # registry arrays are aligned; the reuse mask covers every slot.
    Requires(len(base) == len(frel))
    Requires(len(base) == len(reuse_mask))
    # in constrained mode reuse is genuinely constrained (reuse set supplied).
    Requires(Implies(constrained, not reuse_all))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(frel), 1 / 2))
    Ensures(Acc(list_pred(reuse_mask), 1 / 2))
    # The registry arrays are read-only here (the caller appends a fresh slot
    # separately when Result() reports a new slot is needed).
    Ensures(ToSeq(base) == Old(ToSeq(base)))
    Ensures(ToSeq(frel) == Old(ToSeq(frel)))
    # Registry arrays stay aligned (read-only here).
    Ensures(len(base) == len(frel))
    Ensures(len(base) == len(reuse_mask))
    # Result() is True iff a FRESH slot must be created, i.e. NO reuse-eligible
    # slot matches the incoming descriptor under the active match predicate.
    Ensures(Result() == no_eligible_match(
        base, frel, reuse_all, reuse_mask, jb, jf, constrained))
    # post-conditions-end
    # impl-start
    n = len(base)
    found = False
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(frel), 1 / 2))
        Invariant(Acc(list_pred(reuse_mask), 1 / 2))
        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)
        Invariant(0 <= i and i <= n)
        Invariant(Implies(constrained, not reuse_all))
        Invariant(ToSeq(base) == Old(ToSeq(base)))
        Invariant(ToSeq(frel) == Old(ToSeq(frel)))
        # While no match has been seen, no eligible slot among 0..i matches.
        Invariant(Implies(
            not found,
            Implies(not constrained, Forall(int, lambda k: (
                Implies(0 <= k and k < i,
                        not (reusable(k, n, reuse_all, reuse_mask)
                             and matches_default(k, n, jb, jf, base, frel)))
            )))))
        Invariant(Implies(
            not found,
            Implies(constrained, Forall(int, lambda k: (
                Implies(0 <= k and k < i,
                        not (reuse_mask[k]
                             and matches_constrained(k, n, jb, base)))
            )))))
        # Once a match has been seen, an eligible matching slot provably exists.
        Invariant(Implies(
            found,
            not no_eligible_match(
                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
        # invariants-end
        if constrained:
            if reuse_mask[i] and matches_constrained(i, n, jb, base):
                found = True
        else:
            if reusable(i, n, reuse_all, reuse_mask) and \
                    matches_default(i, n, jb, jf, base, frel):
                found = True
        i = i + 1
    return not found
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-15554 (nagini). VERDICT: SOUND.

Spec shape (why hard to break): install_join's postcondition pins Result() == no_eligible_match(base,frel,reuse_all,reuse_mask,jb,jf,constrained) as a full ==, and the arrays are read-only (ToSeq(base)==Old, ToSeq(frel)==Old). no_eligible_match is a @Pure deterministic function of the inputs, so every verifying impl must return exactly the reference boolean on every valid input - there is no behavioural slack for a verifying-but-wrong impl. The only editable region is impl (markers.py spec_view elides only impl; axioms/@Pure/Requires/Ensures/invariants of the pure helpers are frozen).

Protocol executed; ran `python -m swebench_unified.adversary weakness nagini django__django-15554 <atk>` concurrently in batches of 3 JVMs. same-spec exit 0 for ALL nine files.
- atk_1_prepatch.py (recorded prepatch bug: default branch uses matches_constrained base-only): verify NO (weakness exit 2). Prepatch bug REPRODUCED - invariant Implies(found, not no_eligible_match(...)) undischargeable from a base-only match. GOOD.
- atk_2.py (partial-domain: return True always): verify NO (exit 2).
- atk_3.py (boundary off-by-one: while i < n-1, skips last slot): verify NO (exit 2).
- atk_4.py (control-flow-effect: reuse whenever eligible, ignoring match predicate): verify NO (exit 2).
- atk_5.py (ungrounded-oracle echo: return no_eligible_match(...) directly): verify YES => CANDIDATE (exit 0). Behaviourally identical to reference. Materialized faithful patch = gold patch; run_resolve under official harness => RESOLVED: True, completed: True, note 'resolved'. Resolving echo is NOT a weakness (2026-08-06 G-PANEL-1 policy). Does not break spec.
- atk_6.py (swap: matches_default full-identity in the CONSTRAINED branch, over-strict): verify NO (exit 2).
- atk_7.py (drop-reusable: default branch matches but ignores reuse eligibility): verify NO (exit 2).
- atk_8.py (negate observable: return `found` not `not found`): verify NO (exit 2).
positive_control.py (= frozen model.py impl): VERIFIED in 18.8s (exit 0).

A-leg / correspondence audit (refinement.md, mapping.md): NO A-consumed legs and NO kind-3 legs - the bundle consumes zero @ContractOnly axioms (axioms region empty by design). The one changed operation (alias-reuse equality predicate) is pure integer/tuple equality, modeled deeply (matches_default full-identity incl. filtered_relation; matches_constrained base-only; no_eligible_match folds eligible match over all slots). Sole external fact is an A-reference: real Join.__eq__ compares full identity incl. filtered_relation while Join.equals compares identity[:-1]. Validated EXECUTABLY by axiom_check.py (G-AX): exit 0 - '(j==join)<=>matches_default and j.equals(join)<=>matches_constrained over 96 boundary + 60000 fuzz registries; model new-alias-needed == gold join() decision; F2P distinct-refinement witness holds; pre-patch predicate confirmed to (wrongly) merge.' R legs (A1-A3,A6,B1) and I+R legs (A4,A5) all map faithfully (alias_map<->arrays, reuse<->reuse_all/mask, constrained = reuse_with_filtered_relation and reuse, Result()<->not reuse_aliases; keyword-thread hunks are a pure data-flow rename, no new observable). Correspondence to real callees holds.

Conclusion: 6 distinct wrong impls (partial-domain, boundary, control-flow-effect, swap, drop-reusable, negate) + prepatch all FAILED to verify; the only verifying candidate is a semantic echo whose faithful patch RESOLVES. No verifying-yet-non-resolving impl exists. Positive control verifies, prepatch reproduced, A-reference sound. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none - no verifying wrong impl found. The only CANDIDATE (atk_5, the pure-oracle echo returning no_eligible_match(...) directly) is behaviourally identical to the reference; its faithful refined patch is the gold patch, which RESOLVES under the official harness (run_resolve: resolved=True, completed=True). A resolving echo is not a weakness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15554.

Behaviour under specification (stated as desired behaviour, not as an edit):

A query maintains a registry of relation-join descriptors. Each descriptor has
a *base relation identity* (which underlying relation and connection it joins)
and an optional *refinement tag* (an extra per-join filtering refinement; tag 0
means "no refinement", a positive tag denotes a specific refinement). When a new
join descriptor must be installed, the registry first looks for an existing slot
it may reuse:

  - In the default mode the candidate is permitted to reuse a slot only when
    that slot matches the new descriptor on BOTH its base relation identity AND
    its refinement tag. Two descriptors that share the same base relation but
    carry DIFFERENT refinement tags are therefore NOT collapsed onto one slot:
    the second one is installed into a fresh slot of its own.

  - In the constrained mode the candidate may reuse only a slot drawn from an
    explicitly supplied reuse set, and the match is taken on the base relation
    identity alone (the refinement is supplied by the constrained caller).

If a reusable slot exists the existing slot is returned; otherwise a fresh slot
is appended and its index returned. The function reports whether a fresh slot
was created — the observable consequence the registry guarantees.

The decisive property: with two same-base, distinct-refinement descriptors and
default reuse, installing the second must create a NEW slot rather than reusing
the first — so distinct refinements of one relation are preserved, not merged.

The registry is modelled with parallel `List[int]` arrays (base identity and
refinement tag of each slot) plus the reuse set as a `List[bool]` mask and an
"all reusable" flag (the unconstrained case). Marker regions delimit the spec /
proof / impl.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the modelled operation is integer/equality comparison over the
#  slot registry, fully expressible in Nagini; no opaque callee is consumed.)
# axioms-end


# pure-start
@Pure
def reusable(i: int, n: int, reuse_all: bool, reuse_mask: List[bool]) -> bool:
    """A slot index i is reuse-eligible if all slots are reusable (the
    unconstrained case) or i is flagged in the supplied reuse mask."""
    Requires(Acc(list_pred(reuse_mask), 1 / 8))
    Requires(0 <= i and i < n and n == len(reuse_mask))
    return reuse_all or reuse_mask[i]


@Pure
def matches_default(i: int, n: int, jb: int, jf: int,
                    base: List[int], frel: List[int]) -> bool:
    """The default-mode match predicate: slot i matches the incoming
    descriptor (jb, jf) on BOTH the base relation identity AND the refinement
    tag."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(Acc(list_pred(frel), 1 / 8))
    Requires(0 <= i and i < n and n == len(base) and n == len(frel))
    return base[i] == jb and frel[i] == jf


@Pure
def matches_constrained(i: int, n: int, jb: int,
                        base: List[int]) -> bool:
    """The constrained-mode match predicate: slot i matches on the base
    relation identity alone."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(0 <= i and i < n and n == len(base))
    return base[i] == jb


@Pure
def no_eligible_match(base: List[int], frel: List[int],
                      reuse_all: bool, reuse_mask: List[bool],
                      jb: int, jf: int, constrained: bool) -> bool:
    """True iff NO reuse-eligible slot matches the incoming descriptor under
    the active match predicate — the condition that forces a fresh slot."""
    Requires(Acc(list_pred(base), 1 / 8))
    Requires(Acc(list_pred(frel), 1 / 8))
    Requires(Acc(list_pred(reuse_mask), 1 / 8))
    Requires(len(base) == len(frel) and len(base) == len(reuse_mask))
    if constrained:
        return Forall(int, lambda k: (
            Implies(0 <= k and k < len(base),
                    not (reuse_mask[k]
                         and matches_constrained(k, len(base), jb, base)))))
    return Forall(int, lambda k: (
        Implies(0 <= k and k < len(base),
                not (reusable(k, len(base), reuse_all, reuse_mask)
                     and matches_default(k, len(base), jb, jf, base, frel)))))
# pure-end


def install_join(base: List[int], frel: List[int],
                 reuse_all: bool, reuse_mask: List[bool],
                 jb: int, jf: int,
                 constrained: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(frel), 1 / 2))
    Requires(Acc(list_pred(reuse_mask), 1 / 2))
    # registry arrays are aligned; the reuse mask covers every slot.
    Requires(len(base) == len(frel))
    Requires(len(base) == len(reuse_mask))
    # in constrained mode reuse is genuinely constrained (reuse set supplied).
    Requires(Implies(constrained, not reuse_all))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(frel), 1 / 2))
    Ensures(Acc(list_pred(reuse_mask), 1 / 2))
    # The registry arrays are read-only here (the caller appends a fresh slot
    # separately when Result() reports a new slot is needed).
    Ensures(ToSeq(base) == Old(ToSeq(base)))
    Ensures(ToSeq(frel) == Old(ToSeq(frel)))
    # Registry arrays stay aligned (read-only here).
    Ensures(len(base) == len(frel))
    Ensures(len(base) == len(reuse_mask))
    # Result() is True iff a FRESH slot must be created, i.e. NO reuse-eligible
    # slot matches the incoming descriptor under the active match predicate.
    Ensures(Result() == no_eligible_match(
        base, frel, reuse_all, reuse_mask, jb, jf, constrained))
    # post-conditions-end
    # impl-start
    n = len(base)
    found = False
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(frel), 1 / 2))
        Invariant(Acc(list_pred(reuse_mask), 1 / 2))
        Invariant(len(base) == n and len(frel) == n and len(reuse_mask) == n)
        Invariant(0 <= i and i <= n)
        Invariant(Implies(constrained, not reuse_all))
        Invariant(ToSeq(base) == Old(ToSeq(base)))
        Invariant(ToSeq(frel) == Old(ToSeq(frel)))
        # While no match has been seen, no eligible slot among 0..i matches.
        Invariant(Implies(
            not found,
            Implies(not constrained, Forall(int, lambda k: (
                Implies(0 <= k and k < i,
                        not (reusable(k, n, reuse_all, reuse_mask)
                             and matches_default(k, n, jb, jf, base, frel)))
            )))))
        Invariant(Implies(
            not found,
            Implies(constrained, Forall(int, lambda k: (
                Implies(0 <= k and k < i,
                        not (reuse_mask[k]
                             and matches_constrained(k, n, jb, base)))
            )))))
        # Once a match has been seen, an eligible matching slot provably exists.
        Invariant(Implies(
            found,
            not no_eligible_match(
                base, frel, reuse_all, reuse_mask, jb, jf, constrained)))
        # invariants-end
        if constrained:
            if reuse_mask[i] and matches_constrained(i, n, jb, base):
                found = True
        else:
            if reusable(i, n, reuse_all, reuse_mask) and \
                    matches_default(i, n, jb, jf, base, frel):
                found = True
        i = i + 1
    return not found
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-15554 (nagini). VERDICT: SOUND.

Spec shape (why hard to break): install_join's postcondition pins Result() == no_eligible_match(base,frel,reuse_all,reuse_mask,jb,jf,constrained) as a full ==, and the arrays are read-only (ToSeq(base)==Old, ToSeq(frel)==Old). no_eligible_match is a @Pure deterministic function of the inputs, so every verifying impl must return exactly the reference boolean on every valid input - there is no behavioural slack for a verifying-but-wrong impl. The only editable region is impl (markers.py spec_view elides only impl; axioms/@Pure/Requires/Ensures/invariants of the pure helpers are frozen).

Protocol executed; ran `python -m swebench_unified.adversary weakness nagini django__django-15554 <atk>` concurrently in batches of 3 JVMs. same-spec exit 0 for ALL nine files.
- atk_1_prepatch.py (recorded prepatch bug: default branch uses matches_constrained base-only): verify NO (weakness exit 2). Prepatch bug REPRODUCED - invariant Implies(found, not no_eligible_match(...)) undischargeable from a base-only match. GOOD.
- atk_2.py (partial-domain: return True always): verify NO (exit 2).
- atk_3.py (boundary off-by-one: while i < n-1, skips last slot): verify NO (exit 2).
- atk_4.py (control-flow-effect: reuse whenever eligible, ignoring match predicate): verify NO (exit 2).
- atk_5.py (ungrounded-oracle echo: return no_eligible_match(...) directly): verify YES => CANDIDATE (exit 0). Behaviourally identical to reference. Materialized faithful patch = gold patch; run_resolve under official harness => RESOLVED: True, completed: True, note 'resolved'. Resolving echo is NOT a weakness (2026-08-06 G-PANEL-1 policy). Does not break spec.
- atk_6.py (swap: matches_default full-identity in the CONSTRAINED branch, over-strict): verify NO (exit 2).
- atk_7.py (drop-reusable: default branch matches but ignores reuse eligibility): verify NO (exit 2).
- atk_8.py (negate observable: return `found` not `not found`): verify NO (exit 2).
positive_control.py (= frozen model.py impl): VERIFIED in 18.8s (exit 0).

A-leg / correspondence audit (refinement.md, mapping.md): NO A-consumed legs and NO kind-3 legs - the bundle consumes zero @ContractOnly axioms (axioms region empty by design). The one changed operation (alias-reuse equality predicate) is pure integer/tuple equality, modeled deeply (matches_default full-identity incl. filtered_relation; matches_constrained base-only; no_eligible_match folds eligible match over all slots). Sole external fact is an A-reference: real Join.__eq__ compares full identity incl. filtered_relation while Join.equals compares identity[:-1]. Validated EXECUTABLY by axiom_check.py (G-AX): exit 0 - '(j==join)<=>matches_default and j.equals(join)<=>matches_constrained over 96 boundary + 60000 fuzz registries; model new-alias-needed == gold join() decision; F2P distinct-refinement witness holds; pre-patch predicate confirmed to (wrongly) merge.' R legs (A1-A3,A6,B1) and I+R legs (A4,A5) all map faithfully (alias_map<->arrays, reuse<->reuse_all/mask, constrained = reuse_with_filtered_relation and reuse, Result()<->not reuse_aliases; keyword-thread hunks are a pure data-flow rename, no new observable). Correspondence to real callees holds.

Conclusion: 6 distinct wrong impls (partial-domain, boundary, control-flow-effect, swap, drop-reusable, negate) + prepatch all FAILED to verify; the only verifying candidate is a semantic echo whose faithful patch RESOLVES. No verifying-yet-non-resolving impl exists. Positive control verifies, prepatch reproduced, A-reference sound. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-15554 (nagini). VERDICT: FAITHFUL — the modeled install_join agrees with the real patched Query.join on every tested input; no diverging input found.

Symbol binding verified against the real worktree at base_commit 59ab3fd0e9: matches_default == Join.__eq__ (full identity incl. filtered_relation, datastructures.py:155-158); matches_constrained == Join.equals (identity[:-1], excludes filtered_relation, :164-166); no_eligible_match()/Result() == 'not reuse_aliases' of the gold Query.join reuse comprehension (query.py post-patch, working tree confirmed to be the gold patch: default branch j==join, constrained branch j.equals(join) gated by 'reuse_with_filtered_relation and reuse'); constrained == the keyword-selected branch. The precondition Implies(constrained, not reuse_all) is sound because the constrained branch is reached only when a non-empty reuse set is supplied (reuse is not None), so it excludes no reachable behavior.

Evidence:
1. Reproduced the bundle's G-CONF against the REAL patched repo: 123768 Requires-satisfying inputs, 0 disagreements.
2. INDEPENDENT differential probe (5 fresh seeds 1/42/99999/271828/777, 400000 inputs, registries up to size 12, id vocab 1-5, tag vocab 0-5, all 4 reuse modes default-all/default-all-kw/default-mask/constrained): 0 divergences between shadow install_join and the real Query.join reuse-vs-fresh decision.
3. model.py verifies (nagini_verify.sh: Verification successful, 15.6s) so the Result()==no_eligible_match postcondition is a proven, non-vacuous property.
4. G-AX recorded pass (Join.__eq__/equals stand-in matches the two predicates over 96 boundary + 60000 fuzz registries).

The default predicate correctly uses full identity (distinguishing distinct FilteredRelations on the same base relation — the F2P test_multiple behavior), and the constrained branch uses base-only identity over masked slots, exactly as the gold patch. No spec-vs-repo disagreement exists on any input. The spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view is byte-identical to the frozen region_hashes.spec_view (recomputed sha256 764b30dd9a7e37652931b6edc8b7b49fd956f9802d6f25472068c0f0136bcec7 == meta.json), and the impl region is elided. The view is fully abstracted into a generic 'join-slot registry' model: it names NO repository symbol or artifact (no Query.join, alias_map, FilteredRelation, Join.__eq__/equals, reuse_with_filtered_relation, no file/line, no diff/patch/gold/base_commit, no Django vocabulary aside from the public instance id in the docstring header). Token scan over the lowercased view surfaced only benign substrings (the public id 'django__django-15554', and 'diff'/'q(' occurring inside Ensures(ToSeq(...))). The decisive behavioral statement ('two same-base, distinct-refinement descriptors under default reuse must create a NEW slot rather than reuse the first — distinct refinements preserved, not merged') is a restatement of the behavior ALREADY implied by the public problem_statement ('using multiple FilteredRelation with different filters for the same relation is ignored / generates a single JOIN'). Specifying the target behavior abstractly is the model's legitimate purpose. The 'constrained mode' is described abstractly ('the refinement is supplied by the constrained caller') and does NOT expose the reuse_with_filtered_relation keyword thread through build_filter/build_filtered_relation_q/setup_joins (the second gold hunk). Nothing in the view localizes the edit — it does not reveal the j.equals(join)->j==join predicate swap, which function/predicate to change, or which functions to thread a keyword through. The leaky repo-symbol content lives only in mapping.md/refinement.md, which are audit documents excluded from the spec_view (confirmed by hash). G-LEAK (lexical) also passed. No spec-view line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
