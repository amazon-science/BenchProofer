# P2 adversarial audit — django__django-11400

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,13 +125,8 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
-    if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
-    res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
-    return res
+    qs = apply_order_by(base, ordering)  # type: List[int]
+    return qs
     # impl-end
 
 
@@ -150,11 +145,6 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
-    if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
-    res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
-    return res
+    qs = apply_order_by(base, ordering)  # type: List[int]
+    return qs
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,12 +125,10 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
-    if len(ordering) > 0:
+    if len(ordering) > 1:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
 
@@ -150,11 +148,9 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
-    if len(ordering) > 0:
+    if len(ordering) > 1:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,13 +125,14 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
-    if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
-    res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
-    return res
+    if len(base) <= 1:
+        if len(ordering) > 0:
+            q1 = apply_order_by(base, ordering)  # type: List[int]
+            return q1
+        r1 = copy_rows(base)  # type: List[int]
+        return r1
+    q2 = apply_order_by(base, ordering)  # type: List[int]
+    return q2
     # impl-end
 
 
@@ -150,11 +151,12 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
-    if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
-    res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
-    return res
+    if len(base) <= 1:
+        if len(ordering) > 0:
+            q1 = apply_order_by(base, ordering)  # type: List[int]
+            return q1
+        r1 = copy_rows(base)  # type: List[int]
+        return r1
+    q2 = apply_order_by(base, ordering)  # type: List[int]
+    return q2
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -129,6 +129,7 @@
         qs = apply_order_by(base, ordering)  # type: List[int]
         Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
+    junk = apply_order_by(base, ordering)  # type: List[int]
     res = copy_rows(base)  # type: List[int]
     Assert(ToSeq(res) == ToSeq(base))
     return res
@@ -154,6 +155,7 @@
         qs = apply_order_by(base, ordering)  # type: List[int]
         Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
+    junk = apply_order_by(base, ordering)  # type: List[int]
     res = copy_rows(base)  # type: List[int]
     Assert(ToSeq(res) == ToSeq(base))
     return res
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,11 +127,11 @@
     # impl-start
     if len(ordering) > 0:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
-    res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
-    return res
+    probe = []  # type: List[int]
+    probe.append(0)
+    alt = apply_order_by(base, probe)  # type: List[int]
+    return alt
     # impl-end
 
 
@@ -152,9 +152,9 @@
     # impl-start
     if len(ordering) > 0:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
-    res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
-    return res
+    probe = []  # type: List[int]
+    probe.append(0)
+    alt = apply_order_by(base, probe)  # type: List[int]
+    return alt
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -126,11 +126,10 @@
     # post-conditions-end
     # impl-start
     if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
+        tmp = copy_rows(base)  # type: List[int]
+        qs = apply_order_by(tmp, ordering)  # type: List[int]
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
 
@@ -151,10 +150,9 @@
     # post-conditions-end
     # impl-start
     if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
+        tmp = copy_rows(base)  # type: List[int]
+        qs = apply_order_by(tmp, ordering)  # type: List[int]
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,12 +125,13 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
+    if len(base) == 0:
+        z = []  # type: List[int]
+        return z
     if len(ordering) > 0:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
 
@@ -150,11 +151,12 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
+    if len(base) == 0:
+        z = []  # type: List[int]
+        return z
     if len(ordering) > 0:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,11 +126,9 @@
     # post-conditions-end
     # impl-start
     if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
+        f = copy_rows(base)  # type: List[int]
+        return f
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
 
@@ -151,10 +149,8 @@
     # post-conditions-end
     # impl-start
     if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
+        f = copy_rows(base)  # type: List[int]
+        return f
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -150,11 +150,6 @@
                     ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
     # post-conditions-end
     # impl-start
-    if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,10 +127,10 @@
     # impl-start
     if len(ordering) > 0:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
+    if len(res) > 0:
+        res.append(res[0])
     return res
     # impl-end
 
@@ -152,9 +152,9 @@
     # impl-start
     if len(ordering) > 0:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
+    if len(res) > 0:
+        res.append(res[0])
     return res
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,11 +126,10 @@
     # post-conditions-end
     # impl-start
     if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
+        q1 = apply_order_by(base, ordering)  # type: List[int]
+        q2 = apply_order_by(q1, ordering)  # type: List[int]
+        return q2
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
 
@@ -151,10 +150,9 @@
     # post-conditions-end
     # impl-start
     if len(ordering) > 0:
-        qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
-        return qs
+        q1 = apply_order_by(base, ordering)  # type: List[int]
+        q2 = apply_order_by(q1, ordering)  # type: List[int]
+        return q2
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
     return res
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,10 +127,12 @@
     # impl-start
     if len(ordering) > 0:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
+    if len(res) >= 2:
+        t = res[0]
+        res[0] = res[len(res) - 1]
+        res[len(res) - 1] = t
     return res
     # impl-end
 
@@ -152,9 +154,11 @@
     # impl-start
     if len(ordering) > 0:
         qs = apply_order_by(base, ordering)  # type: List[int]
-        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
         return qs
     res = copy_rows(base)  # type: List[int]
-    Assert(ToSeq(res) == ToSeq(base))
+    if len(res) >= 2:
+        t = res[0]
+        res[0] = res[len(res) - 1]
+        res[len(res) - 1] = t
     return res
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11400.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the row sequence backing a related model's choices is assembled, an
  EXPLICIT ordering is honoured only when one is supplied. The caller hands in
  a possibly-empty ordering specification. When that specification is non-empty,
  the rows are produced in the order it dictates (`reordered(base, ordering)`).
  When it is empty, NO reordering is performed: the rows keep the order of the
  base collection exactly as it arrives -- the base collection's own default
  order is preserved, never discarded.

  The hazard the contract rules out: applying the reorder operation with an
  empty specification is NOT guaranteed to reproduce the base order (an empty
  specification clears any pre-existing order and yields an unspecified
  arrangement). So an implementation may invoke the reorder operation only on
  the branch where the specification is non-empty.

Two related collection-choice builders share this behaviour and are modelled as
two contracted functions (`related_choice_rows`, `reverse_choice_rows`).

Rows are modelled as `List[int]` (opaque row identities); the ordering
specification is modelled as `List[int]` (its emptiness is the only property
the behaviour turns on). The reorder operation over a base collection is the
unchanged queryset callee, axiomatized (`reordered` / `apply_order_by`) and
validated against the real callee out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def reordered(base: PSeq[int], ordering: PSeq[int]) -> PSeq[int]:
    """Pure value of the unchanged queryset reorder callee
    (`QuerySet.order_by(*ordering)`) applied to a base collection.

    The operation is UNINTERPRETED: this contract states NO property of its
    value at all, and a caller may assume none.

      * Nothing ties `reordered(b, [])` to `b`. An empty ordering specification
        clears any pre-existing order, so the arrangement it then yields is
        unspecified.
      * Nothing ties the LENGTH, the membership, or the multiplicity of
        `reordered(b, o)` to `b` either. An ordering specification names
        traversal paths, and a path may cross a to-many association -- the
        operation then repeats base entries, one per associated element -- or a
        mandatory single-valued association, where an entry whose associate is
        absent drops out instead. So the operation is NOT a rearrangement of the
        base collection, and no count, set or multiset relation to `base` holds
        of its result.

    Being uninterpreted is also what GROUNDS the obligation that consumes it:
    the only way to obtain a value equal to `reordered(b, o)` is to invoke the
    operation itself (via `apply_order_by`), so the obligation cannot be
    discharged by reconstructing a value from the arguments.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """


@ContractOnly
def apply_order_by(base: List[int], ordering: List[int]) -> List[int]:
    """Effecting form of the reorder callee, returning a fresh row list whose
    value is `reordered(base, ordering)`. Used by the impl on the
    non-empty-ordering branch only. Read-only in its inputs (fractional)."""
    Requires(Acc(list_pred(base), 1 / 4))
    Requires(Acc(list_pred(ordering), 1 / 4))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(base), 1 / 4))
    Ensures(Acc(list_pred(ordering), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering)))
# axioms-end


# pure-start
# pure-end


def copy_rows(base: List[int]) -> List[int]:
    """A faithful copy of the base collection's rows in their arriving order
    (the result list comprehension that materializes the base queryset)."""
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(MustTerminate(len(base) + 2))
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(base))
    out = []  # type: List[int]
    i = 0
    while i < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(out) == ToSeq(base).take(i))
        Invariant(MustTerminate(len(base) - i + 1))
        # invariants-end
        out.append(base[i])
        Assert(ToSeq(base).take(i + 1) == ToSeq(base).take(i) + PSeq(base[i]))
        i = i + 1
    Assert(ToSeq(base).take(len(base)) == ToSeq(base))
    return out


def related_choice_rows(base: List[int], ordering: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ordering), 1 / 2))
    Requires(MustTerminate(len(base) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ordering), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The data-row sequence backing the choices:
    #  * empty ordering  -> the base order is preserved exactly;
    #  * non-empty order  -> the requested reordering of the base.
    Ensures(Implies(len(ordering) == 0, ToSeq(Result()) == ToSeq(base)))
    Ensures(Implies(len(ordering) > 0,
                    ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
    # post-conditions-end
    # impl-start
    if len(ordering) == 0:
        acc = []  # type: List[int]
        k = 0
        while k < len(base):
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(acc)))
            Invariant(0 <= k and k <= len(base))
            Invariant(ToSeq(acc) == ToSeq(base).take(k))
            Invariant(MustTerminate(len(base) - k + 1))
            acc.append(base[k])
            Assert(ToSeq(base).take(k + 1) == ToSeq(base).take(k) + PSeq(base[k]))
            k = k + 1
        Assert(ToSeq(base).take(len(base)) == ToSeq(base))
        return acc
    Assert(len(ordering) > 0)
    out2 = apply_order_by(base, ordering)  # type: List[int]
    return out2
    # impl-end


def reverse_choice_rows(base: List[int], ordering: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ordering), 1 / 2))
    Requires(MustTerminate(len(base) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ordering), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(Implies(len(ordering) == 0, ToSeq(Result()) == ToSeq(base)))
    Ensures(Implies(len(ordering) > 0,
                    ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
    # post-conditions-end
    # impl-start
    if len(ordering) == 0:
        acc = []  # type: List[int]
        k = 0
        while k < len(base):
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(acc)))
            Invariant(0 <= k and k <= len(base))
            Invariant(ToSeq(acc) == ToSeq(base).take(k))
            Invariant(MustTerminate(len(base) - k + 1))
            acc.append(base[k])
            Assert(ToSeq(base).take(k + 1) == ToSeq(base).take(k) + PSeq(base[k]))
            k = k + 1
        Assert(ToSeq(base).take(len(base)) == ToSeq(base))
        return acc
    Assert(len(ordering) > 0)
    out2 = apply_order_by(base, ordering)  # type: List[int]
    return out2
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-11400 (nagini). Scratch: 

IMPORTANT PRELIMINARY -- THE BUNDLE WAS REPAIRED SINCE THE LAST RECORDED G-EQ PASS, SO I RE-ATTACKED FROM SCRATCH RATHER THAN INHERITING THAT PASS. meta.json's recorded G-EQ sources/model.py = bc1369eaab4090462a80d5b648b44a2df67abba91cf5a03f901a9752bff6ca06, but the CURRENT model.py hashes 7800eee7a52e058d533800ece4f22fb3e46f52f5c3b08dc2c7db038206b9c189. The prior G-PANEL-2 (faithfulness) role FAILED this cell for exactly this reason: the old `reordered` axiom carried a positive clause Ensures(len(Result()) == len(base)) which is FALSE of the real QuerySet.order_by (a to-many ordering path fans rows out). The axiom has since been rewritten to be FULLY UNINTERPRETED (empty contract). That is a weaker assumption surface, which is the direction that could newly ADMIT wrong impls, so the old attack battery's verdicts are not transferable. Every result below was measured on 7800eee7 (re-confirmed unchanged after the audit; bundle never modified).

**ATTACK CONSTRUCTION.** 12 attacks + 1 positive control, all generated by gen.py, which regex-splices bodies between the two '# impl-start'/'# impl-end' marker pairs of the frozen model.py so axioms/@Pure/@ContractOnly/Requires/Ensures/Invariant are byte-identical. gen.py self-checks by asserting that splicing the GOLD body round-trips to the frozen file byte-for-byte (`splice([GOLD,GOLD]) == FROZEN`), which pins that only the impl regions ever differ. NOTE: `copy_rows` has NO impl markers -- its whole body (loop + invariants) lives in the spec view -- so it was never touched. Screens: `adversary same-spec` exit 0 on all 13, and variant_scope.unsound_evasions == [] on all 13 (no injected @ContractOnly / Assume / Refute).

**COMMANDS.** Per attack N: `python -m swebench_unified.adversary weakness nagini django__django-11400 atk_N.py`, run 3-at-a-time as background jobs (each Nagini check spawns a JVM+Z3). Positive control: `bash scripts/nagini_verify.sh.../pos_control.py`.

### RESULTS (10 rejected / 2 candidates):
- atk_1 PREPATCH REPRODUCED (unconditional `apply_order_by(base, ordering)` at BOTH sites, = model_prepatch.py) -> exit 2, does NOT verify (17s). The postcondition Implies(len(ordering)==0, ToSeq(Result())==ToSeq(base)) is unprovable because the axiom is silent on the empty case. prepatch_reproduced=true.
- atk_2 BOUNDARY, guard `len(ordering) > 1` (a 1-element ordering silently ignored) -> exit 2, rejected (16s).
- atk_3 PARTIAL DOMAIN, fix applied only when len(base)<=1; larger bases keep the prepatch unconditional reorder -> exit 2, rejected (17s).
- atk_4 CONTROL-FLOW EFFECT, gold plus `apply_order_by(base, ordering)` also invoked on the EMPTY branch and its value discarded -> exit 0 CANDIDATE (14.2s). RESOLVE-CHECKED BELOW.
- atk_5 UNGROUNDED-ORACLE ECHO: the empty branch routed through the callee with an INVENTED non-empty ordering spec ([0]) -> exit 2, rejected (14s). The axiom's opacity means an invented spec cannot be shown to reproduce the base order.
- atk_6 reorders a MATERIALIZED COPY (copy_rows(base) then apply_order_by on the copy) rather than base itself -> exit 0 CANDIDATE (14.2s). RESOLVE-CHECKED BELOW.
- atk_7 EMPTY-BASE SHORT CIRCUIT ahead of the gold body (returns a fresh [] when len(base)==0) -> exit 2, REJECTED (16s). *** THIS IS THE SHARPEST EVIDENCE THAT THE AXIOM REPAIR TIGHTENED THE SPEC: the pre-repair bundle ADMITTED this impl (recorded as a resolving echo in the old verdict.md), because the old length clause let the proof conclude len(reordered(b,o))==0 hence Result()==[]. With the clause gone the axiom no longer licenses that step and the spec now rejects it. ***
- atk_8 AXIOM-STRENGTH FORGERY (the key A-leg probe): the non-empty branch never invokes the callee and returns copy_rows(base) instead -> exit 2, rejected (17s). The postcondition demands sequence equality with reordered(...), and an uninterpreted axiom cannot be discharged by rebuilding a value from the arguments -- confirming the axiom GROUNDS the obligation rather than over-licensing it.
- atk_9 ASYMMETRIC SECOND SITE: site 1 gold, reverse_choice_rows ignores `ordering` entirely -> exit 2, rejected (16s). The second site is independently observable, matching G-DIFF's model_prepatch_2.py.
- atk_10 MULTIPLICITY BOUNDARY: empty branch preserves order but appends a duplicate of the first row -> exit 2, rejected (18s). The postcondition pins the whole SEQUENCE, not a set/prefix.
- atk_11 DOUBLE REORDER on the non-empty branch (probes a leaked idempotence of order_by) -> exit 2, rejected (18s). Nothing ties reordered(reordered(b,o),o) to reordered(b,o).
- atk_12 PARTIAL-DOMAIN WRONG ORDER: base order preserved except first/last transposed, so only bases with >=2 rows are misordered -> exit 2, rejected (19s).

MANDATORY RESOLVE RUNS FOR EVERY CANDIDATE (the actual verify=>correct test). Faithful refined patches materialized by mkpatch.py in a git worktree at base_commit 1f8382d34d54061eddc41df6994e20ee38c60907: gold patch applied, then ONLY the two MODELLED call sites rewritten to mirror the attack impl, with the admin/filters.py plumbing kept CONTENT-IDENTICAL to gold (machine-diffed: the +/- content lines of the filters.py hunk are identical to gold's for all three patches; only the `index` line and hunk-header context labels differ, which are cosmetic). All `git apply --check` clean against a verified-clean base tree. Executed via swebench_unified.harness.run_resolve (official harness, `docker` run_evaluation), 3 concurrently:
- atk_4 -> patch_atk_4.diff -> completed=True RESOLVED=True, F2P 6/6, P2P 58/58 (resolve_atk_4.json).
- atk_6 -> patch_atk_6a.diff -> completed=True RESOLVED=True, F2P 6/6, P2P 58/58 (resolve_atk_6a.json). This is the `.all()` clone reading of copy_rows (submitted in `patches`).
- atk_6 SECOND, STRICTER READING (extra adversarial rigor, since atk_6 is the one attack whose refinement is genuinely ambiguous): patch_atk_6b.diff materializes the base rows first and reorders a queryset of exactly those pks (`rows = list(qs); qs = manager.filter(pk__in=[r.pk for r in rows]).order_by(*ordering)`) -> completed=True RESOLVED=True, F2P 6/6, P2P 58/58 (resolve_atk_6b.json). BOTH readings of "reorder a materialized copy" resolve, so atk_6 is not a weakness under either refinement.
Both candidates are therefore CORRECT ECHOES (verify AND resolve), not spec weaknesses: an evaluated-and-discarded queryset has no observable effect on the rows returned, and `.all()` / a pk__in requery of the same rows is an order-preserving clone that order_by then sorts identically. Per docs/architecture.md 6 and `_derive_audit_verdict`, a candidate whose faithful patch DOES resolve must not fail the gate. NO candidate's patch failed to resolve, so there is no verify-but-incorrect witness.

A-LEG AUDIT (the assigned focus). Only ONE callee is axiomatized: `reordered` (@Pure @ContractOnly, EMPTY contract) with its effecting form `apply_order_by`, modelling the UNCHANGED `QuerySet.order_by(*ordering)`. meta.json deep_model_references == [], so there is NO A-reference/deep-model leg to check; the single A leg is A-consumed (A4/B4).
1. Re-ran axiom_check.py against the real callee in a base_commit worktree -> exit 0: 'G-AX OK... the real callee GROWS the collection on a to-many ordering path (len 5 > base 4) and SHRINKS it on a mandatory single-valued one (len 1 < base 2, row set changed), so no length, set or multiset clause would be sound. A local-field ordering is honoured (asc/desc); empty order_by() clears the base Meta.ordering ([1,2,3,4] != [4,3,2,1])'. The check now EXHIBITS the real callee breaking each tempting positive clause, which is precisely the defect the prior panel found -- so the repair is backed by an executable probe, not just by prose.
2. I INDEPENDENTLY CONFIRMED THE PRIOR G-PANEL-2 DEFECT IS ACTUALLY GONE, not merely reworded. entail2.py appends an audit-only spec client to the frozen model.py (additions only, all after # impl-end; no spec byte altered) that consumes ONLY the declared postconditions + the axiom. Holding FULL list_pred permission on both inputs (so len(...) is framed across the call -- my first attempt at this, entail.py/entail_ctl.py/diag.py, used fractional permission and gave away everything, which made even len(ordering)==0 unframed; diag.py isolated that as MY framing bug, not a spec fact, before I drew any conclusion):
   * CONTROL e2_ctl_empty (len(ordering)==0): Assert(len(ordering)==0), Assert(ToSeq(r)==ToSeq(base)) and Assert(len(r)==len(base)) ALL PROVE -- the empty branch really does pin the base order.
   * CONTROL e2_len_site1 (len(ordering)>0): Assert(ToSeq(r)==reordered(ToSeq(base),ToSeq(ordering))) PROVES -- the non-empty branch is genuinely pinned and the call is reachable, so the next line is not failing vacuously.
   * THE FALSE FACT Assert(len(r)==len(base)) on the non-empty branch is the ONLY error reported ('Assert might fail'). So the spec NO LONGER ENTAILS the length claim that broke the prior audit, while still entailing everything it should. The repair is real and is not over-corrected into vacuity.
3. The axiom's SILENCE on reordered(b,[]) is the soundness crux and it bites in the right direction: atk_1/atk_5 die precisely because an impl routing the empty case through the callee cannot prove the base order survives. And the silence is not so total that the obligation becomes discharge-able by construction: atk_8's forgery dies because sequence equality with an uninterpreted value can only be obtained by invoking the callee. The axiom is weaker than the real callee in the SAFE direction, with no reachable unsound consequence.

**REFINEMENT.MD LEG AUDIT.** Legs: A1 R / A2 R / A3 I / A4 A-consumed / A5 I,R / A6 R; B1..B6 = A1..A6 verbatim. Every leg is R, A-consumed, or I -- NO kind-3 (unexpressible-changed-op) step, and no A-reference leg exists (consistent with deep_model_references == []). The tags are accurate: A4 is the only axiom-consuming step and it cites the UNCHANGED callee (QuerySet.order_by), not the function under change (get_choices is the function under spec, not an axiom), so section D's claim holds. Section E's discriminating-clause story is independently confirmed by atk_1 (both sites fail) and atk_9 (reverse site fails alone). Correspondence to the real callees checked against the gold-applied worktree: mapping.md 1's cited sites (fields/`__init__`.py:809 body 828-831; reverse_related.py:117 body 125-127) match the actual gold hunks, and base <-> complex_filter(limit_choices_to) / `_default_manager`.all() is right at each site.

ONE DOCUMENTED DOC CAVEAT, CARRIED FORWARD (recorded, NOT a break -- and NOT re-run this pass since the C hunks are unchanged and the prior measurement stands): refinement.md C / mapping.md 4 say the admin/filters.py sites add 'zero discriminating power'. The prior pass falsified the strong reading by reverting ONLY the filters.py hunks -> RESOLVED=False, F2P 5/6, with 'RelatedOnlyFieldListFilter ordering respects ModelAdmin.ordering.' failing. So those sites ARE load-bearing for one F2P test and 'zero discriminating power' overstates it. This is not a G-EQ break: that probe is a repo-side patch mutilation, not a same-spec model impl, and section C does state the obligation ('pass ordering to related_choice_rows') as the A2/A4/A5 plumbing -- which every one of my three materialized patches preserved byte-for-byte. Suggested tightening: replace 'would add zero discriminating power' with 'is required plumbing whose omission loses test_relatedonlyfieldlistfilter_foreignkey_ordering, but which introduces no ordering semantics beyond A2/A4/A5'.

POSITIVE CONTROL pos_control.py: structurally different from model.py -- the EMPTY case is handled FIRST with an early return, the row copy is HAND-ROLLED inside the impl region (its own while loop, its own invariants, its own take()/PSeq lemma) instead of delegating to copy_rows, different variable names, explicit Assert(len(ordering) > 0) on the other branch. same-spec exit 0; `bash scripts/nagini_verify.sh` -> 'Verification successful' in 13.75s, exit 0. Not one of the submitted attack paths. So the spec is not merely rejecting everything that is not a byte-copy of the bundle impl.

**NO INCONCLUSIVE RUNS:** all 12 weakness checks, the positive control, 3 resolve runs, axiom_check.py and the 4 entailment/diagnostic probes reached a real verdict. Host was not saturated (verifications 14-19s each, resolves 1 attempt each).

**VERDICT SOUND:** >=5 admissible attacks re-run (12, all same-spec and admissible), prepatch reproduced, positive control verifies, and BOTH verifying candidates had faithful refined patches EXECUTED through the official harness -- all RESOLVED (atk_6 under two independent refinements) -- so no verify-but-incorrect witness exists. The A leg is executably sound and the prior faithfulness defect is confirmed repaired by my own entailment probe with working controls.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11400.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the row sequence backing a related model's choices is assembled, an
  EXPLICIT ordering is honoured only when one is supplied. The caller hands in
  a possibly-empty ordering specification. When that specification is non-empty,
  the rows are produced in the order it dictates (`reordered(base, ordering)`).
  When it is empty, NO reordering is performed: the rows keep the order of the
  base collection exactly as it arrives -- the base collection's own default
  order is preserved, never discarded.

  The hazard the contract rules out: applying the reorder operation with an
  empty specification is NOT guaranteed to reproduce the base order (an empty
  specification clears any pre-existing order and yields an unspecified
  arrangement). So an implementation may invoke the reorder operation only on
  the branch where the specification is non-empty.

Two related collection-choice builders share this behaviour and are modelled as
two contracted functions (`related_choice_rows`, `reverse_choice_rows`).

Rows are modelled as `List[int]` (opaque row identities); the ordering
specification is modelled as `List[int]` (its emptiness is the only property
the behaviour turns on). The reorder operation over a base collection is the
unchanged queryset callee, axiomatized (`reordered` / `apply_order_by`) and
validated against the real callee out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def reordered(base: PSeq[int], ordering: PSeq[int]) -> PSeq[int]:
    """Pure value of the unchanged queryset reorder callee
    (`QuerySet.order_by(*ordering)`) applied to a base collection.

    The operation is UNINTERPRETED: this contract states NO property of its
    value at all, and a caller may assume none.

      * Nothing ties `reordered(b, [])` to `b`. An empty ordering specification
        clears any pre-existing order, so the arrangement it then yields is
        unspecified.
      * Nothing ties the LENGTH, the membership, or the multiplicity of
        `reordered(b, o)` to `b` either. An ordering specification names
        traversal paths, and a path may cross a to-many association -- the
        operation then repeats base entries, one per associated element -- or a
        mandatory single-valued association, where an entry whose associate is
        absent drops out instead. So the operation is NOT a rearrangement of the
        base collection, and no count, set or multiset relation to `base` holds
        of its result.

    Being uninterpreted is also what GROUNDS the obligation that consumes it:
    the only way to obtain a value equal to `reordered(b, o)` is to invoke the
    operation itself (via `apply_order_by`), so the obligation cannot be
    discharged by reconstructing a value from the arguments.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """


@ContractOnly
def apply_order_by(base: List[int], ordering: List[int]) -> List[int]:
    """Effecting form of the reorder callee, returning a fresh row list whose
    value is `reordered(base, ordering)`. Used by the impl on the
    non-empty-ordering branch only. Read-only in its inputs (fractional)."""
    Requires(Acc(list_pred(base), 1 / 4))
    Requires(Acc(list_pred(ordering), 1 / 4))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(base), 1 / 4))
    Ensures(Acc(list_pred(ordering), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering)))
# axioms-end


# pure-start
# pure-end


def copy_rows(base: List[int]) -> List[int]:
    """A faithful copy of the base collection's rows in their arriving order
    (the result list comprehension that materializes the base queryset)."""
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(MustTerminate(len(base) + 2))
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(base))
    out = []  # type: List[int]
    i = 0
    while i < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(out) == ToSeq(base).take(i))
        Invariant(MustTerminate(len(base) - i + 1))
        # invariants-end
        out.append(base[i])
        Assert(ToSeq(base).take(i + 1) == ToSeq(base).take(i) + PSeq(base[i]))
        i = i + 1
    Assert(ToSeq(base).take(len(base)) == ToSeq(base))
    return out


def related_choice_rows(base: List[int], ordering: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ordering), 1 / 2))
    Requires(MustTerminate(len(base) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ordering), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The data-row sequence backing the choices:
    #  * empty ordering  -> the base order is preserved exactly;
    #  * non-empty order  -> the requested reordering of the base.
    Ensures(Implies(len(ordering) == 0, ToSeq(Result()) == ToSeq(base)))
    Ensures(Implies(len(ordering) > 0,
                    ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
    # post-conditions-end
    # impl-start
    if len(ordering) == 0:
        acc = []  # type: List[int]
        k = 0
        while k < len(base):
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(acc)))
            Invariant(0 <= k and k <= len(base))
            Invariant(ToSeq(acc) == ToSeq(base).take(k))
            Invariant(MustTerminate(len(base) - k + 1))
            acc.append(base[k])
            Assert(ToSeq(base).take(k + 1) == ToSeq(base).take(k) + PSeq(base[k]))
            k = k + 1
        Assert(ToSeq(base).take(len(base)) == ToSeq(base))
        return acc
    Assert(len(ordering) > 0)
    out2 = apply_order_by(base, ordering)  # type: List[int]
    return out2
    # impl-end


def reverse_choice_rows(base: List[int], ordering: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ordering), 1 / 2))
    Requires(MustTerminate(len(base) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ordering), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(Implies(len(ordering) == 0, ToSeq(Result()) == ToSeq(base)))
    Ensures(Implies(len(ordering) > 0,
                    ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
    # post-conditions-end
    # impl-start
    if len(ordering) == 0:
        acc = []  # type: List[int]
        k = 0
        while k < len(base):
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(acc)))
            Invariant(0 <= k and k <= len(base))
            Invariant(ToSeq(acc) == ToSeq(base).take(k))
            Invariant(MustTerminate(len(base) - k + 1))
            acc.append(base[k])
            Assert(ToSeq(base).take(k + 1) == ToSeq(base).take(k) + PSeq(base[k]))
            k = k + 1
        Assert(ToSeq(base).take(len(base)) == ToSeq(base))
        return acc
    Assert(len(ordering) > 0)
    out2 = apply_order_by(base, ordering)  # type: List[int]
    return out2
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-11400 (nagini). Scratch: 

IMPORTANT PRELIMINARY -- THE BUNDLE WAS REPAIRED SINCE THE LAST RECORDED G-EQ PASS, SO I RE-ATTACKED FROM SCRATCH RATHER THAN INHERITING THAT PASS. meta.json's recorded G-EQ sources/model.py = bc1369eaab4090462a80d5b648b44a2df67abba91cf5a03f901a9752bff6ca06, but the CURRENT model.py hashes 7800eee7a52e058d533800ece4f22fb3e46f52f5c3b08dc2c7db038206b9c189. The prior G-PANEL-2 (faithfulness) role FAILED this cell for exactly this reason: the old `reordered` axiom carried a positive clause Ensures(len(Result()) == len(base)) which is FALSE of the real QuerySet.order_by (a to-many ordering path fans rows out). The axiom has since been rewritten to be FULLY UNINTERPRETED (empty contract). That is a weaker assumption surface, which is the direction that could newly ADMIT wrong impls, so the old attack battery's verdicts are not transferable. Every result below was measured on 7800eee7 (re-confirmed unchanged after the audit; bundle never modified).

**ATTACK CONSTRUCTION.** 12 attacks + 1 positive control, all generated by gen.py, which regex-splices bodies between the two '# impl-start'/'# impl-end' marker pairs of the frozen model.py so axioms/@Pure/@ContractOnly/Requires/Ensures/Invariant are byte-identical. gen.py self-checks by asserting that splicing the GOLD body round-trips to the frozen file byte-for-byte (`splice([GOLD,GOLD]) == FROZEN`), which pins that only the impl regions ever differ. NOTE: `copy_rows` has NO impl markers -- its whole body (loop + invariants) lives in the spec view -- so it was never touched. Screens: `adversary same-spec` exit 0 on all 13, and variant_scope.unsound_evasions == [] on all 13 (no injected @ContractOnly / Assume / Refute).

**COMMANDS.** Per attack N: `python -m swebench_unified.adversary weakness nagini django__django-11400 atk_N.py`, run 3-at-a-time as background jobs (each Nagini check spawns a JVM+Z3). Positive control: `bash scripts/nagini_verify.sh.../pos_control.py`.

### RESULTS (10 rejected / 2 candidates):
- atk_1 PREPATCH REPRODUCED (unconditional `apply_order_by(base, ordering)` at BOTH sites, = model_prepatch.py) -> exit 2, does NOT verify (17s). The postcondition Implies(len(ordering)==0, ToSeq(Result())==ToSeq(base)) is unprovable because the axiom is silent on the empty case. prepatch_reproduced=true.
- atk_2 BOUNDARY, guard `len(ordering) > 1` (a 1-element ordering silently ignored) -> exit 2, rejected (16s).
- atk_3 PARTIAL DOMAIN, fix applied only when len(base)<=1; larger bases keep the prepatch unconditional reorder -> exit 2, rejected (17s).
- atk_4 CONTROL-FLOW EFFECT, gold plus `apply_order_by(base, ordering)` also invoked on the EMPTY branch and its value discarded -> exit 0 CANDIDATE (14.2s). RESOLVE-CHECKED BELOW.
- atk_5 UNGROUNDED-ORACLE ECHO: the empty branch routed through the callee with an INVENTED non-empty ordering spec ([0]) -> exit 2, rejected (14s). The axiom's opacity means an invented spec cannot be shown to reproduce the base order.
- atk_6 reorders a MATERIALIZED COPY (copy_rows(base) then apply_order_by on the copy) rather than base itself -> exit 0 CANDIDATE (14.2s). RESOLVE-CHECKED BELOW.
- atk_7 EMPTY-BASE SHORT CIRCUIT ahead of the gold body (returns a fresh [] when len(base)==0) -> exit 2, REJECTED (16s). *** THIS IS THE SHARPEST EVIDENCE THAT THE AXIOM REPAIR TIGHTENED THE SPEC: the pre-repair bundle ADMITTED this impl (recorded as a resolving echo in the old verdict.md), because the old length clause let the proof conclude len(reordered(b,o))==0 hence Result()==[]. With the clause gone the axiom no longer licenses that step and the spec now rejects it. ***
- atk_8 AXIOM-STRENGTH FORGERY (the key A-leg probe): the non-empty branch never invokes the callee and returns copy_rows(base) instead -> exit 2, rejected (17s). The postcondition demands sequence equality with reordered(...), and an uninterpreted axiom cannot be discharged by rebuilding a value from the arguments -- confirming the axiom GROUNDS the obligation rather than over-licensing it.
- atk_9 ASYMMETRIC SECOND SITE: site 1 gold, reverse_choice_rows ignores `ordering` entirely -> exit 2, rejected (16s). The second site is independently observable, matching G-DIFF's model_prepatch_2.py.
- atk_10 MULTIPLICITY BOUNDARY: empty branch preserves order but appends a duplicate of the first row -> exit 2, rejected (18s). The postcondition pins the whole SEQUENCE, not a set/prefix.
- atk_11 DOUBLE REORDER on the non-empty branch (probes a leaked idempotence of order_by) -> exit 2, rejected (18s). Nothing ties reordered(reordered(b,o),o) to reordered(b,o).
- atk_12 PARTIAL-DOMAIN WRONG ORDER: base order preserved except first/last transposed, so only bases with >=2 rows are misordered -> exit 2, rejected (19s).

MANDATORY RESOLVE RUNS FOR EVERY CANDIDATE (the actual verify=>correct test). Faithful refined patches materialized by mkpatch.py in a git worktree at base_commit 1f8382d34d54061eddc41df6994e20ee38c60907: gold patch applied, then ONLY the two MODELLED call sites rewritten to mirror the attack impl, with the admin/filters.py plumbing kept CONTENT-IDENTICAL to gold (machine-diffed: the +/- content lines of the filters.py hunk are identical to gold's for all three patches; only the `index` line and hunk-header context labels differ, which are cosmetic). All `git apply --check` clean against a verified-clean base tree. Executed via swebench_unified.harness.run_resolve (official harness, `docker` run_evaluation), 3 concurrently:
- atk_4 -> patch_atk_4.diff -> completed=True RESOLVED=True, F2P 6/6, P2P 58/58 (resolve_atk_4.json).
- atk_6 -> patch_atk_6a.diff -> completed=True RESOLVED=True, F2P 6/6, P2P 58/58 (resolve_atk_6a.json). This is the `.all()` clone reading of copy_rows (submitted in `patches`).
- atk_6 SECOND, STRICTER READING (extra adversarial rigor, since atk_6 is the one attack whose refinement is genuinely ambiguous): patch_atk_6b.diff materializes the base rows first and reorders a queryset of exactly those pks (`rows = list(qs); qs = manager.filter(pk__in=[r.pk for r in rows]).order_by(*ordering)`) -> completed=True RESOLVED=True, F2P 6/6, P2P 58/58 (resolve_atk_6b.json). BOTH readings of "reorder a materialized copy" resolve, so atk_6 is not a weakness under either refinement.
Both candidates are therefore CORRECT ECHOES (verify AND resolve), not spec weaknesses: an evaluated-and-discarded queryset has no observable effect on the rows returned, and `.all()` / a pk__in requery of the same rows is an order-preserving clone that order_by then sorts identically. Per docs/architecture.md 6 and `_derive_audit_verdict`, a candidate whose faithful patch DOES resolve must not fail the gate. NO candidate's patch failed to resolve, so there is no verify-but-incorrect witness.

A-LEG AUDIT (the assigned focus). Only ONE callee is axiomatized: `reordered` (@Pure @ContractOnly, EMPTY contract) with its effecting form `apply_order_by`, modelling the UNCHANGED `QuerySet.order_by(*ordering)`. meta.json deep_model_references == [], so there is NO A-reference/deep-model leg to check; the single A leg is A-consumed (A4/B4).
1. Re-ran axiom_check.py against the real callee in a base_commit worktree -> exit 0: 'G-AX OK... the real callee GROWS the collection on a to-many ordering path (len 5 > base 4) and SHRINKS it on a mandatory single-valued one (len 1 < base 2, row set changed), so no length, set or multiset clause would be sound. A local-field ordering is honoured (asc/desc); empty order_by() clears the base Meta.ordering ([1,2,3,4] != [4,3,2,1])'. The check now EXHIBITS the real callee breaking each tempting positive clause, which is precisely the defect the prior panel found -- so the repair is backed by an executable probe, not just by prose.
2. I INDEPENDENTLY CONFIRMED THE PRIOR G-PANEL-2 DEFECT IS ACTUALLY GONE, not merely reworded. entail2.py appends an audit-only spec client to the frozen model.py (additions only, all after # impl-end; no spec byte altered) that consumes ONLY the declared postconditions + the axiom. Holding FULL list_pred permission on both inputs (so len(...) is framed across the call -- my first attempt at this, entail.py/entail_ctl.py/diag.py, used fractional permission and gave away everything, which made even len(ordering)==0 unframed; diag.py isolated that as MY framing bug, not a spec fact, before I drew any conclusion):
   * CONTROL e2_ctl_empty (len(ordering)==0): Assert(len(ordering)==0), Assert(ToSeq(r)==ToSeq(base)) and Assert(len(r)==len(base)) ALL PROVE -- the empty branch really does pin the base order.
   * CONTROL e2_len_site1 (len(ordering)>0): Assert(ToSeq(r)==reordered(ToSeq(base),ToSeq(ordering))) PROVES -- the non-empty branch is genuinely pinned and the call is reachable, so the next line is not failing vacuously.
   * THE FALSE FACT Assert(len(r)==len(base)) on the non-empty branch is the ONLY error reported ('Assert might fail'). So the spec NO LONGER ENTAILS the length claim that broke the prior audit, while still entailing everything it should. The repair is real and is not over-corrected into vacuity.
3. The axiom's SILENCE on reordered(b,[]) is the soundness crux and it bites in the right direction: atk_1/atk_5 die precisely because an impl routing the empty case through the callee cannot prove the base order survives. And the silence is not so total that the obligation becomes discharge-able by construction: atk_8's forgery dies because sequence equality with an uninterpreted value can only be obtained by invoking the callee. The axiom is weaker than the real callee in the SAFE direction, with no reachable unsound consequence.

**REFINEMENT.MD LEG AUDIT.** Legs: A1 R / A2 R / A3 I / A4 A-consumed / A5 I,R / A6 R; B1..B6 = A1..A6 verbatim. Every leg is R, A-consumed, or I -- NO kind-3 (unexpressible-changed-op) step, and no A-reference leg exists (consistent with deep_model_references == []). The tags are accurate: A4 is the only axiom-consuming step and it cites the UNCHANGED callee (QuerySet.order_by), not the function under change (get_choices is the function under spec, not an axiom), so section D's claim holds. Section E's discriminating-clause story is independently confirmed by atk_1 (both sites fail) and atk_9 (reverse site fails alone). Correspondence to the real callees checked against the gold-applied worktree: mapping.md 1's cited sites (fields/`__init__`.py:809 body 828-831; reverse_related.py:117 body 125-127) match the actual gold hunks, and base <-> complex_filter(limit_choices_to) / `_default_manager`.all() is right at each site.

ONE DOCUMENTED DOC CAVEAT, CARRIED FORWARD (recorded, NOT a break -- and NOT re-run this pass since the C hunks are unchanged and the prior measurement stands): refinement.md C / mapping.md 4 say the admin/filters.py sites add 'zero discriminating power'. The prior pass falsified the strong reading by reverting ONLY the filters.py hunks -> RESOLVED=False, F2P 5/6, with 'RelatedOnlyFieldListFilter ordering respects ModelAdmin.ordering.' failing. So those sites ARE load-bearing for one F2P test and 'zero discriminating power' overstates it. This is not a G-EQ break: that probe is a repo-side patch mutilation, not a same-spec model impl, and section C does state the obligation ('pass ordering to related_choice_rows') as the A2/A4/A5 plumbing -- which every one of my three materialized patches preserved byte-for-byte. Suggested tightening: replace 'would add zero discriminating power' with 'is required plumbing whose omission loses test_relatedonlyfieldlistfilter_foreignkey_ordering, but which introduces no ordering semantics beyond A2/A4/A5'.

POSITIVE CONTROL pos_control.py: structurally different from model.py -- the EMPTY case is handled FIRST with an early return, the row copy is HAND-ROLLED inside the impl region (its own while loop, its own invariants, its own take()/PSeq lemma) instead of delegating to copy_rows, different variable names, explicit Assert(len(ordering) > 0) on the other branch. same-spec exit 0; `bash scripts/nagini_verify.sh` -> 'Verification successful' in 13.75s, exit 0. Not one of the submitted attack paths. So the spec is not merely rejecting everything that is not a byte-copy of the bundle impl.

**NO INCONCLUSIVE RUNS:** all 12 weakness checks, the positive control, 3 resolve runs, axiom_check.py and the 4 entailment/diagnostic probes reached a real verdict. Host was not saturated (verifications 14-19s each, resolves 1 attempt each).

**VERDICT SOUND:** >=5 admissible attacks re-run (12, all same-spec and admissible), prepatch reproduced, positive control verifies, and BOTH verifying candidates had faithful refined patches EXECUTED through the official harness -- all RESOLVED (atk_6 under two independent refinements) -- so no verify-but-incorrect witness exists. The A leg is executably sound and the prior faithfulness defect is confirmed repaired by my own entailment probe with working controls.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No diverging input found. The modeled functions agree with the real PATCHED repo callees on every input I could construct.

### SETUP
- Reference worktree = base_commit 1f8382d34d54 with patch.diff APPLIED (git apply clean). Negative-control worktree = base, unpatched.
- Bundle model.py verifies under the pinned Nagini: exit 0, 'Verification successful', 12.64s.
- same-spec identity sanity: exit 0 ('SAME').

### What the spec actually claims
Only two Ensures carry strength:
  P1: Implies(len(ordering)==0, ToSeq(Result())==ToSeq(base))
  P2: Implies(len(ordering)>0,  ToSeq(Result())==reordered(ToSeq(base),ToSeq(ordering)))
P2 cannot be over-strong: `reordered` is @Pure @ContractOnly with a genuinely EMPTY contract (no length/set/multiset/permutation clause), and the impl obtains the value only by really invoking apply_order_by. Verified by reading the axiom block — it asserts nothing. So over-strength can live only in P1. That is exactly where I aimed.

### INDEPENDENT PROBES (my own fixtures, not the bundle's)
1. Hostile matrix, 624 cases, 0 failures, on a REGISTERED app so relation paths resolve: limit_choices_to spanning TO-MANY joins ({'books__isnull':False}, {'books__title__gt':'t0'} -> duplicated base rows, len 6 > 5), single-valued joins, nullable FK (LEFT OUTER), empty pk subset, reversed subsets; ordering paths that traverse relations ('books__title' grows, 'pub__name' inner-joins), multi-column, descending; Meta.ordering in {(), ('name',), ('-name',), ('pub__name','name'), ('id',), ('books__title',)}. Both sites (Field.get_choices and ForeignObjectRel.get_choices), plus a second reverse rel via the nullable editor FK.
2. Functional-dependence hunt at the REAL-input level: 63 distinct (base_rows, ordering_names) keys across 12 limit shapes x 9 ordering tuples x 4 Meta.orderings -> 0 collisions. No pair of inputs shares base+ordering yet differs in result, so P2 is satisfiable by a single-valued `reordered`.
3. to_field projection (choice_func = attrgetter('code'), not pk), Q-object limits, Q|Q, callable limit_choices_to via get_limit_choices_to: 0 failures. Large base 2011 rows with NO Meta.ordering: P1 holds, P2 matches real order_by.
4. MTI (multi-table inheritance) + a custom default manager that imposes its own order_by('-name') distinct from Meta.ordering: 0 failures. Confirms `base` faithfully carries the base MANAGER's emission order, which is what mapping.md 2 claims.
5. The real admin shape limit_choices_to={'pk__in': <lazy queryset subquery>} (exactly RelatedOnlyFieldListFilter's argument, not a materialized list): 0 failures; stable across 50 re-evaluations.
6. DEFINITIVE instrumented test (the strongest one): monkeypatched QuerySet.`__iter__` to record the pk sequence get_choices ACTUALLY iterates, then compared the returned rows against that very sequence. 168 probes across 6 Meta.orderings x 4 limits x 7 ordering tuples -> 0 failures. Also confirmed via str(qs.query) that on the empty branch the base ORDER BY survives untouched ('name' ASC / 'name' DESC / None / RANDOM() ASC).

### One artifact I chased and dismissed
With Meta.ordering=('?',) (RANDOM()), a harness that evaluates the base queryset separately from get_choices disagrees 60/60 (45 distinct base orders). That is NOT spec over-strength: it is two independent SQL evaluations of a deliberately nondeterministic query. Probe 6 settles it — against the single evaluation get_choices actually consumed, the result matches every time, including ('?',). The model's `base` is a materialized VALUE handed in, so the faithful reading is the shared evaluation, and P1 holds there (60/60 in the shared-evaluation control too).

NEGATIVE CONTROL — proves P1's strength is NECESSARY, not excessive
Re-ran the identical 624-case matrix against the UNPATCHED base worktree: 30 failures, kind profile Counter({'P1-fwd': 24, 'P1-rev': 6}) — ONLY P1 ever fails, P2 never does. So the one strong clause is precisely the delta the patch introduces, at both sites, and nothing more. The to_field probe on base likewise fails only P1 (15 cases). Correspondingly the bundle's controls fail on exactly that clause: model_prepatch.py errors on the P1 postcondition at BOTH functions, model_prepatch_2.py at reverse_choice_rows only.

### BUNDLE GATES REPRODUCED (against my own patched worktree)
- axiom_check.py: G-AX OK. Real order_by GROWS on a to-many path (5>4) and SHRINKS on a mandatory single-valued one (1<2, row set changed), so no length/set/multiset clause would be sound and the uninterpreted axiom is required; empty order_by() clears Meta.ordering ([1,2,3,4] != [4,3,2,1]), so the silence on reordered(b,[]) is sound.
- conformance_check.py: G-CONF OK, 105,288 inputs, 0 disagreements.
- **F2P:** ran model_fields.tests.GetChoicesOrderingTests + admin_filters on the patched worktree — 34 tests, OK.

### OBSERVATION FOR THE RECORD (not a too-strong finding, not my lane's reject)
The ordering carrier collapses field-name tuples to list(range(len(names))), so ('name',) and ('-name',) both become [0]; I measured 15 such carrier-level collisions with differing real results. This is a deliberate and explicitly documented abstraction (mapping.md 2: 'only its EMPTINESS is observed... contents are passed through to the reordered operation and not interpreted further'), and it is sound here because the branch turns solely on emptiness while the result value is pinned by an actual invocation of apply_order_by at the concrete site (the G-CONF bridge instantiates the real names per case). It loses discriminating power rather than adding strength, so it cannot produce an input where the spec demands more than the repo delivers — it is a coarseness question for the too-weak/G-EQ lanes, not a faithfulness break. I flag it only so the panel sees I considered it.

**CONCLUSION:** the spec describes the patched behavior and nothing stronger. No diverging input exists among ~1,000 independent hostile cases plus the reproduced 105k-case gate.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: leakage / gold-reconstruction on the projected consumer spec view of nagini/model.py for django__django-11400, judged against the SOLVER-VISIBLE problem_statement only (hints_text excluded).

**NO RELAXATION IS CLAIMED.** I checked programmatically rather than assuming: `[k for k in meta if 'relax' in k.lower()]` == [], and there is no RELAXED_LEAKAGE.md in the bundle directory (`ls | grep -i relax` empty). So this is an ordinary strict review with no inherited disposition. I also ran leakage.reviewer_directed() over EVERY bundle file (axiom_check.py, conformance_check.py, mapping.md, meta.json, model.py, model_prepatch.py, model_prepatch_2.py, pbt_result.json, properties.py, refinement.md, verdict.md): [] for all eleven, and a targeted grep of the 195KB verdict.md for 'you must submit' / 'honest recording' / 'the correct verdict' / 'panel 3 should' found nothing. No file in this bundle addresses me or tries to prescribe a verdict.

### WHAT I MEASURED (my own runs, not the bundle's assertions):

1. Projected the spec view myself: swebench_unified.markers.spec_view(model.py, nagini backend) -> 148 lines, read in full. Both impl regions collapse to the elision placeholder (count == 2) and the nested invariants region goes with them. The prepatch models (which DO contain 'PRE-PATCH (buggy)' comments) are not part of the spec view; per eval/dataset.py only spec_view(model.py) reaches the consumer, and WITHHELD_FIELDS keeps patch/test_patch out.

2. Mechanical screen: leakage.screen(model.py, nagini, gold patch, problem_statement from the frozen row) -> hard_failures=[], warnings=[], passed=True.

3. Independent gold-line collision check (not trusting the screen's >=8 threshold): normalized every added/removed line of the gold patch against the normalized spec view at ANY length. Only collisions are the bare token '"""' twice -- a content-free docstring delimiter, no reproduced gold line. Confirmed the normalized gold guard 'ifordering:' is ABSENT, as is 'qs=qs.order_by(*ordering)'.

4. Symbol/path echo check: patch-touched def/class names are {get_choices, field_choices, field_admin_ordering, choices, has_output}; grepped the view for each plus RelatedFieldListFilter, RelatedOnlyFieldListFilter, complex_filter, `_default_manager`, limit_choices_to, blank_choice, filters.py, reverse_related, fields/`__init__` -- all zero. All three patched paths absent. No diff marker. Zero bug/fix narration vocabulary. The model uses abstract carriers (related_choice_rows, reverse_choice_rows, copy_rows, base/ordering: List[int]).

5. THE LOAD-BEARING TEST -- is the discriminator in the CONTRACT or in the PROSE? I built narration-stripped variants (all docstrings and all non-marker comments removed, `# type:` annotations and region markers kept) of model.py and both prepatches, then ran the pinned verifier on each:
   - gold_bare.py  -> 'Verification successful' (17.55s), exit 0
   - pp1_bare.py   -> FAILS, both sites: 'Postcondition of related_choice_rows might not hold. Assertion Implies((len(ordering) == 0), (ToSeq(Result()) == ToSeq(base)))' and the same for reverse_choice_rows
   - pp2_bare.py   -> FAILS at reverse_choice_rows only (second site independently sensed)
   With every word of prose deleted, the spec still verifies the gold impl and still rejects both prepatches on exactly the empty-ordering clause. The discrimination is carried entirely by the postcondition pair Implies(len(ordering)==0, Result()==base) / Implies(len(ordering)>0, Result()==reordered(base,ordering)) over the UNINTERPRETED `reordered`. The docstring narration is a restatement of the contract, adding no discriminating information -- which is why no relaxation is needed here and none is claimed.

6. Derivability from problem_statement alone. The public issue states the discriminator directly: 'RelatedFieldListFilter doesn't fall back to the ordering defined in Model.`_meta`.ordering. Ordering gets set to an empty tuple... unless ordering is defined on the related model's ModelAdmin class it stays an empty tuple. IMHO it should fall back to the ordering defined in the related model's Meta.ordering', plus 'the call to field.get_choices... omits the ordering kwarg entirely'. 'ordering', 'Meta.ordering', 'empty tuple' and 'get_choices' are all verbatim in the problem_statement (checked). So the empty-vs-non-empty ordering split -- the whole content of the contract -- is public, and the spec view tells the solver nothing about WHERE or HOW to edit that the issue does not.

7. Weighed the one borderline item: the string 'QuerySet.order_by(*ordering)' does appear in the `reordered` axiom docstring, and 'order_by(*ordering)' is a substring of a removed gold line. I judged this NOT a leak: order_by is the UNCHANGED callee (it is not among the patch-changed symbols), naming it is axiom provenance that mapping.md §3.1 is required to supply, it is the documented public Django API for queryset ordering that the issue's subject matter points straight at, and it does not disclose the edit -- the edit is the `if ordering:` guard, which is absent from the view. Per-line L1 collision is clean.

8. CORE GATES RE-RUN INDEPENDENTLY, not read off meta.json. Cloned django_django.git  at base_commit 1f8382d34d54061eddc41df6994e20ee38c60907 and a gold-applied copy dj_gold:
   - axiom_check.py (G-AX) with PYTHONPATH=dj -> exit 0. Reproduces the crux: empty order_by() clears the base Meta.ordering ([1,2,3,4] != [4,3,2,1]), the real callee GROWS on a to-many path (5>4) and SHRINKS on a mandatory single-valued one (1<2, row set changed). So `reordered` MUST stay uninterpreted and MUST NOT promise reordered(b,[])==b -- exactly the silence that makes the prepatch unprovable in test 5. Sound.
   - conformance_check.py (G-CONF) against dj_gold -> exit 0, 105288 inputs, 0 disagreements. Useful control: against the UNPATCHED dj it reports a disagreement at site=forward with ordering=() (shadow [4,2,5,1,3] vs real [1,2,3,4,5]) -- i.e. the harness genuinely discriminates and is not vacuous.
   - same-spec: `adversary same-spec nagini django__django-11400` on a copy of model.py -> exit 0, 'SAME -- attack shares the bundle's exact specification'.

ARTIFACT-HYGIENE OBSERVATION (reported, not a leakage finding). The top-level meta.json['region_hashes'] is STALE: it records spec_view=e4a3c1b4..., axioms=24550cbc..., pre-conditions=5d1dae8b... and omits 'invariants'. Recomputing region_hashes(model.py, nagini) myself gives spec_view=db6257a5..., axioms=c9e2f48a..., pre-conditions=73837055..., invariants=b676c3fa... -- which matches meta['gates']['G-HYGIENE']['data']['region_hashes'] BYTE-FOR-BYTE. So the gate record is current and the stale copy is the top-level convenience field. This does not weaken my review: G-LEAK/G-VERIFY/G-AX/G-CONF all record sources model.py=7800eee7a52e058d533800ece4f22fb3e46f52f5c3b08dc2c7db038206b9c189, which equals the on-disk sha256sum, so the artifact I screened is the artifact the gates screened. Flagging for the maintainer because a stale top-level hash field could mask a future spec-region edit.

OUT OF SCOPE, noted for the record: meta.json shows G-PANEL-2 (faithfulness) = fail, which is why the aggregate G-PANEL reads fail. That is a different facet and I did not adjudicate it. It does not bear on leakage here because there is no relaxation whose disposition leans on it.

**CONCLUSION:** NO-LEAKAGE. The spec view reproduces no gold line, names no patched symbol/path/file, carries no diff marker and no bug/fix narration; its discriminating power survives total prose removal (gold verifies, both prepatches fail on the empty-ordering postcondition); and the behavioural split it encodes is stated outright in the public problem_statement. Nothing in the view localizes or reconstructs the gold edit beyond what the issue already gives the solver.

**Scope:** leakage / gold-reconstruction on the projected consumer spec view of nagini/model.py for django__django-11400, judged against the SOLVER-VISIBLE problem_statement only (hints_text excluded).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
