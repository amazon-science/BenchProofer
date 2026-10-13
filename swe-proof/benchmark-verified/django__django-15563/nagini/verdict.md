# P2 adversarial audit — django__django-15563

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,45 +105,14 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    width = 1
     i = 0
     while i < len(chain):
-        # invariants-start
         Invariant(Acc(list_pred(chain), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(chain))
         Invariant(len(result) == i)
-        Invariant(width >= 1)
-        # `width - 1` is the number of fresh targets seen in result[0..i); adding
-        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
-        # total. This pins width to the dense running column count: column 0 (the
-        # source pk) plus exactly one column per fresh target reached so far, i.e.
-        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
-        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
-                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
-        # column 0 iff this target is a primary-key chain
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
-        # every fresh column already placed sits at its EXACT dense index: one
-        # past the number of fresh targets strictly before it.
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
-                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
-        # invariants-end
-        Assert(ToSeq(chain)[i] == chain[i])
-        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
-        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
-        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
-        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
-        if chain[i] == 1:
-            result = result + [0]
-        else:
-            # The fresh column placed here is the running `width`, which the
-            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
-            # the dense index for target i.
-            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
-            result = result + [width]
-            width = width + 1
+        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i, result[k] == 0)))
+        result = result + [0]
         i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,43 +105,17 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    width = 1
+    width = 0
     i = 0
     while i < len(chain):
-        # invariants-start
         Invariant(Acc(list_pred(chain), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(chain))
         Invariant(len(result) == i)
-        Invariant(width >= 1)
-        # `width - 1` is the number of fresh targets seen in result[0..i); adding
-        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
-        # total. This pins width to the dense running column count: column 0 (the
-        # source pk) plus exactly one column per fresh target reached so far, i.e.
-        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
-        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
-                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
-        # column 0 iff this target is a primary-key chain
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
-        # every fresh column already placed sits at its EXACT dense index: one
-        # past the number of fresh targets strictly before it.
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
-                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
-        # invariants-end
-        Assert(ToSeq(chain)[i] == chain[i])
-        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
-        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
-        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
-        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
+        Invariant(width >= 0)
         if chain[i] == 1:
             result = result + [0]
         else:
-            # The fresh column placed here is the running `width`, which the
-            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
-            # the dense index for target i.
-            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
             result = result + [width]
             width = width + 1
         i = i + 1
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -108,42 +108,16 @@
     width = 1
     i = 0
     while i < len(chain):
-        # invariants-start
         Invariant(Acc(list_pred(chain), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(chain))
         Invariant(len(result) == i)
         Invariant(width >= 1)
-        # `width - 1` is the number of fresh targets seen in result[0..i); adding
-        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
-        # total. This pins width to the dense running column count: column 0 (the
-        # source pk) plus exactly one column per fresh target reached so far, i.e.
-        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
-        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
-                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
-        # column 0 iff this target is a primary-key chain
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
-        # every fresh column already placed sits at its EXACT dense index: one
-        # past the number of fresh targets strictly before it.
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
-                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
-        # invariants-end
-        Assert(ToSeq(chain)[i] == chain[i])
-        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
-        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
-        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
-        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
         if chain[i] == 1:
             result = result + [0]
         else:
-            # The fresh column placed here is the running `width`, which the
-            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
-            # the dense index for target i.
-            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
             result = result + [width]
-            width = width + 1
+            width = width + 2
         i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -108,40 +108,14 @@
     width = 1
     i = 0
     while i < len(chain):
-        # invariants-start
         Invariant(Acc(list_pred(chain), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(chain))
         Invariant(len(result) == i)
         Invariant(width >= 1)
-        # `width - 1` is the number of fresh targets seen in result[0..i); adding
-        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
-        # total. This pins width to the dense running column count: column 0 (the
-        # source pk) plus exactly one column per fresh target reached so far, i.e.
-        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
-        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
-                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
-        # column 0 iff this target is a primary-key chain
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
-        # every fresh column already placed sits at its EXACT dense index: one
-        # past the number of fresh targets strictly before it.
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
-                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
-        # invariants-end
-        Assert(ToSeq(chain)[i] == chain[i])
-        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
-        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
-        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
-        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
-        if chain[i] == 1:
+        if chain[i] == 0:
             result = result + [0]
         else:
-            # The fresh column placed here is the running `width`, which the
-            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
-            # the dense index for target i.
-            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
             result = result + [width]
             width = width + 1
         i = i + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,45 +105,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    width = 1
     i = 0
     while i < len(chain):
-        # invariants-start
         Invariant(Acc(list_pred(chain), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(chain))
         Invariant(len(result) == i)
-        Invariant(width >= 1)
-        # `width - 1` is the number of fresh targets seen in result[0..i); adding
-        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
-        # total. This pins width to the dense running column count: column 0 (the
-        # source pk) plus exactly one column per fresh target reached so far, i.e.
-        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
-        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
-                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
-        # column 0 iff this target is a primary-key chain
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
-        # every fresh column already placed sits at its EXACT dense index: one
-        # past the number of fresh targets strictly before it.
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
-                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
-        # invariants-end
-        Assert(ToSeq(chain)[i] == chain[i])
-        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
-        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
-        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
-        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
         if chain[i] == 1:
             result = result + [0]
         else:
-            # The fresh column placed here is the running `width`, which the
-            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
-            # the dense index for target i.
-            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
-            result = result + [width]
-            width = width + 1
+            result = result + [1]
         i = i + 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,45 +105,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    width = 1
     i = 0
     while i < len(chain):
-        # invariants-start
         Invariant(Acc(list_pred(chain), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(chain))
         Invariant(len(result) == i)
-        Invariant(width >= 1)
-        # `width - 1` is the number of fresh targets seen in result[0..i); adding
-        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
-        # total. This pins width to the dense running column count: column 0 (the
-        # source pk) plus exactly one column per fresh target reached so far, i.e.
-        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
-        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
-                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
-        # column 0 iff this target is a primary-key chain
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
-        # every fresh column already placed sits at its EXACT dense index: one
-        # past the number of fresh targets strictly before it.
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
-                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
-        # invariants-end
-        Assert(ToSeq(chain)[i] == chain[i])
-        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
-        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
-        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
-        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
         if chain[i] == 1:
             result = result + [0]
         else:
-            # The fresh column placed here is the running `width`, which the
-            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
-            # the dense index for target i.
-            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
-            result = result + [width]
-            width = width + 1
+            result = result + [1 - 0]
         i = i + 1
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,43 +105,17 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    width = 1
+    width = 2
     i = 0
     while i < len(chain):
-        # invariants-start
         Invariant(Acc(list_pred(chain), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(chain))
         Invariant(len(result) == i)
-        Invariant(width >= 1)
-        # `width - 1` is the number of fresh targets seen in result[0..i); adding
-        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
-        # total. This pins width to the dense running column count: column 0 (the
-        # source pk) plus exactly one column per fresh target reached so far, i.e.
-        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
-        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
-                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
-        # column 0 iff this target is a primary-key chain
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
-                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
-        # every fresh column already placed sits at its EXACT dense index: one
-        # past the number of fresh targets strictly before it.
-        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
-                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
-        # invariants-end
-        Assert(ToSeq(chain)[i] == chain[i])
-        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
-        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
-        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
-        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
+        Invariant(width >= 2)
         if chain[i] == 1:
             result = result + [0]
         else:
-            # The fresh column placed here is the running `width`, which the
-            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
-            # the dense index for target i.
-            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
             result = result + [width]
             width = width + 1
         i = i + 1
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -108,39 +108,24 @@
     width = 1
     i = 0
     while i < len(chain):
-        # invariants-start
         Invariant(Acc(list_pred(chain), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(chain))
         Invariant(len(result) == i)
         Invariant(width >= 1)
-        # `width - 1` is the number of fresh targets seen in result[0..i); adding
-        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
-        # total. This pins width to the dense running column count: column 0 (the
-        # source pk) plus exactly one column per fresh target reached so far, i.e.
-        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
         Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                                ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
-        # column 0 iff this target is a primary-key chain
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                                (result[k] == 0) == (ToSeq(chain)[k] == 1))))
-        # every fresh column already placed sits at its EXACT dense index: one
-        # past the number of fresh targets strictly before it.
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
                   result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
-        # invariants-end
         Assert(ToSeq(chain)[i] == chain[i])
-        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
-        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
         Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
         Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
-        if chain[i] == 1:
+        if chain[i] != 0:
             result = result + [0]
         else:
-            # The fresh column placed here is the running `width`, which the
-            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
-            # the dense index for target i.
             Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
             result = result + [width]
             width = width + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15563.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a row in a concrete multi-table-inheritance tree is updated and the
  update touches fields living on more than one ancestor table, the engine
  first collects, for every ancestor it must touch, the set of primary-key
  values that identify the ancestor rows to change. Those values are read out
  of a single pre-selection that returns several columns per source row.

  Two facts pin the behaviour:

  (1) Column assignment. The pre-selection always returns the source model's
      own primary key as its first column (column 0). For each ancestor that
      must be touched, if every link on the path up to that ancestor is itself
      a primary-key link (so the ancestor's identifying value coincides with
      the source row's own primary key), that ancestor reuses column 0;
      otherwise the ancestor needs its own identifying column, which is
      appended as a fresh column at a positive index (never column 0).

  (2) Projection. The identifying values used to constrain each ancestor's
      update are then read from THAT ancestor's assigned column of every source
      row — not uniformly from column 0. An ancestor whose identifying value
      is genuinely distinct from the source row's own primary key is therefore
      constrained by its own positive column, while a primary-key-chain
      ancestor reuses column 0.

Tables and per-target metadata are modelled with `List[int]` carriers and the
pure sequence theory `PSeq[int]`; a per-target boolean ("the whole path up to
this ancestor is a primary-key chain") is modelled as an `int` flag 0/1, the
value of the unchanged path-classification callee, validated out of band
(axiom_check.py / G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No consumed @ContractOnly axiom: the per-target path classification is an
#  input flag, modelled as an A-reference and validated against the real callee
#  by axiom_check.py / G-AX; the column-assignment and projection logic is
#  modelled deeply below.)
# axioms-end

# pure-start
@Pure
def count_fresh(s: PSeq[int]) -> int:
    """Total number of fresh (non-reuse) targets in `s`, i.e. the count of
    indices m with `s[m] == 0`. Front-recursive over the sequence (peeling the
    head, one auto-unfold per loop step), so the value is uniquely pinned. This
    is the number of source columns appended beyond column 0 — the maximum
    fresh column index, and one less than the pre-selection row width."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    elif s[0] == 0:
        return 1 + count_fresh(s.drop(1))
    else:
        return count_fresh(s.drop(1))
# pure-end

def assign_columns(chain: List[int]) -> List[int]:
    """Assign each ancestor target the index of the pre-selection column whose
    values identify the rows to update (the column-assignment fact, item (1)).

    `chain[k]` is 1 when the path up to target k is a full primary-key chain
    (so target k's identifying value coincides with the source row's own
    primary key, column 0) and 0 otherwise."""
    # pre-conditions-start
    Requires(Acc(list_pred(chain), 1 / 2))
    Requires(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                           ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(chain), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(chain))
    # A full primary-key-chain target reuses column 0; any other target is
    # placed in a fresh column strictly past column 0 (column index >= 1, i.e.
    # NEVER column 0). This biconditional is the heart of the behaviour: a
    # non-chain ancestor is constrained by its own column, never by the source
    # row's own primary key (column 0).
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                          (Result()[k] == 0) == (ToSeq(chain)[k] == 1))))
    # Dense running column index — the load-bearing fact. A non-chain ancestor's
    # column is read by the consumer as a PHYSICAL OFFSET into a source row whose
    # width is exactly 1 + (total fresh ancestors): column 0 is the source pk,
    # then exactly one column per fresh ancestor in target order. So the fresh
    # ancestor at index k occupies column 1 + (number of fresh ancestors strictly
    # before k). That prefix count is written here as
    #   count_fresh(chain) - count_fresh(chain[k:])
    # (total fresh minus the fresh from k onward). This EXACT pin forces the
    # fresh columns to be the contiguous block 1, 2, ..., F (F = count_fresh) —
    # dense, distinct, in-bounds. A merely "positive and strictly increasing"
    # assignment (e.g. sparse columns 2, 4, 6, ...) does NOT satisfy it: such an
    # index over-runs the row width and would read past the end of every source
    # row.
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < len(chain) and ToSeq(chain)[k] == 0,
                  Result()[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    width = 1
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(result) == i)
        Invariant(width >= 1)
        # `width - 1` is the number of fresh targets seen in result[0..i); adding
        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
        # total. This pins width to the dense running column count: column 0 (the
        # source pk) plus exactly one column per fresh target reached so far, i.e.
        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
        # column 0 iff this target is a primary-key chain
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
        # every fresh column already placed sits at its EXACT dense index: one
        # past the number of fresh targets strictly before it.
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
        # invariants-end
        Assert(ToSeq(chain)[i] == chain[i])
        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
        if chain[i] == 1:
            result = result + [0]
        else:
            # The fresh column placed here is the running `width`, which the
            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
            # the dense index for target i.
            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
            result = result + [width]
            width = width + 1
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit for django__django-15563 (nagini). Interpreter: python; verifier: scripts/nagini_verify.sh.

SPEC ANALYSIS: assign_columns(chain) has three postconditions that pin Result()[k] POINTWISE for EVERY k over the {0,1} domain: (a) len(Result())==len(chain); (b) biconditional (Result()[k]==0)==(chain[k]==1); (c) for chain[k]==0, the EXACT dense index Result()[k]==1+(count_fresh(chain)-count_fresh(chain[k:])). Together these uniquely determine the output as the gold column-assignment function on every input, leaving no room for a behaviorally-distinct verifying impl. count_fresh is a frozen @Pure helper (spec region), so attacks cannot weaken it.

ATTACKS (all confirmed SAME-SPEC via `adversary same-spec`, exit 0; then run through `adversary weakness nagini django__django-15563 <file>`):
- atk_1 (control-flow-effect / prepatch echo: every target -> col 0): NOT-A-COUNTEREXAMPLE, verify failed (exit 2). gold-diff at flags=(0,).
- atk_2 (boundary/off-by-one: width starts at 0, first fresh col collides w/ pk col 0): verify failed (exit 2). gold-diff at (0,).
- atk_3 (sparse: width+=2, the historic batch08 IndexError survivor): verify failed (exit 2). gold-diff at (0,0) got [1,3] vs gold [1,2].
- atk_4 (inverted biconditional: branches swapped): verify failed (exit 2). gold-diff at (0,).
- atk_5 (partial-domain: non-chain target -> constant col 1): verify failed (exit 2). gold-diff at (0,0) got [1,1].
- atk_6 (ungrounded-oracle echo of atk_5 via 1-0): verify failed (exit 2). gold-diff at (0,0).
- atk_7 (shifted dense index: width starts at 2, over-runs row width by 1): verify failed (exit 2). gold-diff at (0,).
- atk_8 (faithful alternative correct impl: `chain[i]!=0` complement of gold `==1`): CANDIDATE — SAME-SPEC AND VERIFIES (exit 0, 117.1s). Proven gold-EQUAL on all binary vectors n<=9 (behavioral-equivalence harness). Its faithful refined patch = the gold patch.py verbatim (refines under refinement.md map A1-A5; the `!=0`/`==1` complement is logically identical). MATERIALIZED and RUN through the official harness: run_resolve("django__django-15563", gold_patch) => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, non-flaky (log resolve_atk8.txt). A resolving echo of the gold is NOT a weakness (verify=>correct holds for it).

No verifying wrong impl exists: the only same-spec impl that verified (atk_8) is gold-equivalent and its patch resolves. Every genuinely-wrong impl (atk_1..7 across partial-domain, boundary, control-flow-effect, sparse-index, ungrounded-oracle-echo classes) is REJECTED by the verifier — the spec is tight.

POSITIVE CONTROL: bundle model.py verifies (exit 0, 104.8s).
PREPATCH: model_prepatch.py is SAME-SPEC and FAILS verify (exit 1, 16.5s) precisely on the biconditional postcondition (Result()[k]==0)==(chain[k]==1) — the bug is sensed (G-DIFF), so prepatch_reproduced=true.

REFINEMENT.md AUDIT (A-legs + correspondence): axioms=[] (NO consumed @ContractOnly axiom, confirmed in model.py axioms region and meta). Legs: A1 (index domain 0..len-1 <-> ordered related_updates keys) = R; A2 (chain[i] <-> all(path.join_field.primary_key for path in meta.get_path_to_parent(related))) = A-reference, validated by axiom_check.py/G-AX against REAL Django 4.x on BOTH F2P scenarios (Congressman parent-through-child, Senator grand-parent-through-child), reproducing gold column assignment at the INDEX level (model_index[k]==0 <=> real_is_pk_chain[k], NO double mask) + 20000 fuzz vectors == gold construction (meta G-AX=pass); A3 (reuse col 0) = I; A4 (fresh col = running width <-> len(fields)) = R; A5 (result list <-> index projection of related_ids_index + add_fields) = R; Site B/P (r[index] projection + keyed self.related_ids[model] filter) = R/I.

Section C confirmed: NO kind-3 (unexpressible-changed-op) leg — the one genuinely-changed op (per-ancestor column choice) is modeled DEEPLY in assign_columns, and the sole abstracted callee is the A-reference (get_path_to_parent/join_field.primary_key). A2 correspondence to the real callee holds (axiom_check.py drives the real UpdateQuery.add_update_values and evaluates the real predicate). No kind-3 steps.

VERDICT: SOUND. 8 same-spec attacks run; 7 wrong impls rejected by the verifier; the lone verifying candidate (atk_8) is gold-equal and its materialized faithful patch RESOLVES under run_resolve. verify=>correct holds; the spec admits no verifying-but-incorrect implementation.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15563.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a row in a concrete multi-table-inheritance tree is updated and the
  update touches fields living on more than one ancestor table, the engine
  first collects, for every ancestor it must touch, the set of primary-key
  values that identify the ancestor rows to change. Those values are read out
  of a single pre-selection that returns several columns per source row.

  Two facts pin the behaviour:

  (1) Column assignment. The pre-selection always returns the source model's
      own primary key as its first column (column 0). For each ancestor that
      must be touched, if every link on the path up to that ancestor is itself
      a primary-key link (so the ancestor's identifying value coincides with
      the source row's own primary key), that ancestor reuses column 0;
      otherwise the ancestor needs its own identifying column, which is
      appended as a fresh column at a positive index (never column 0).

  (2) Projection. The identifying values used to constrain each ancestor's
      update are then read from THAT ancestor's assigned column of every source
      row — not uniformly from column 0. An ancestor whose identifying value
      is genuinely distinct from the source row's own primary key is therefore
      constrained by its own positive column, while a primary-key-chain
      ancestor reuses column 0.

Tables and per-target metadata are modelled with `List[int]` carriers and the
pure sequence theory `PSeq[int]`; a per-target boolean ("the whole path up to
this ancestor is a primary-key chain") is modelled as an `int` flag 0/1, the
value of the unchanged path-classification callee, validated out of band
(axiom_check.py / G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No consumed @ContractOnly axiom: the per-target path classification is an
#  input flag, modelled as an A-reference and validated against the real callee
#  by axiom_check.py / G-AX; the column-assignment and projection logic is
#  modelled deeply below.)
# axioms-end

# pure-start
@Pure
def count_fresh(s: PSeq[int]) -> int:
    """Total number of fresh (non-reuse) targets in `s`, i.e. the count of
    indices m with `s[m] == 0`. Front-recursive over the sequence (peeling the
    head, one auto-unfold per loop step), so the value is uniquely pinned. This
    is the number of source columns appended beyond column 0 — the maximum
    fresh column index, and one less than the pre-selection row width."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    elif s[0] == 0:
        return 1 + count_fresh(s.drop(1))
    else:
        return count_fresh(s.drop(1))
# pure-end

def assign_columns(chain: List[int]) -> List[int]:
    """Assign each ancestor target the index of the pre-selection column whose
    values identify the rows to update (the column-assignment fact, item (1)).

    `chain[k]` is 1 when the path up to target k is a full primary-key chain
    (so target k's identifying value coincides with the source row's own
    primary key, column 0) and 0 otherwise."""
    # pre-conditions-start
    Requires(Acc(list_pred(chain), 1 / 2))
    Requires(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                           ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(chain), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(chain))
    # A full primary-key-chain target reuses column 0; any other target is
    # placed in a fresh column strictly past column 0 (column index >= 1, i.e.
    # NEVER column 0). This biconditional is the heart of the behaviour: a
    # non-chain ancestor is constrained by its own column, never by the source
    # row's own primary key (column 0).
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                          (Result()[k] == 0) == (ToSeq(chain)[k] == 1))))
    # Dense running column index — the load-bearing fact. A non-chain ancestor's
    # column is read by the consumer as a PHYSICAL OFFSET into a source row whose
    # width is exactly 1 + (total fresh ancestors): column 0 is the source pk,
    # then exactly one column per fresh ancestor in target order. So the fresh
    # ancestor at index k occupies column 1 + (number of fresh ancestors strictly
    # before k). That prefix count is written here as
    #   count_fresh(chain) - count_fresh(chain[k:])
    # (total fresh minus the fresh from k onward). This EXACT pin forces the
    # fresh columns to be the contiguous block 1, 2, ..., F (F = count_fresh) —
    # dense, distinct, in-bounds. A merely "positive and strictly increasing"
    # assignment (e.g. sparse columns 2, 4, 6, ...) does NOT satisfy it: such an
    # index over-runs the row width and would read past the end of every source
    # row.
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < len(chain) and ToSeq(chain)[k] == 0,
                  Result()[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    width = 1
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(result) == i)
        Invariant(width >= 1)
        # `width - 1` is the number of fresh targets seen in result[0..i); adding
        # the fresh targets remaining in the un-walked suffix chain[i:] gives the
        # total. This pins width to the dense running column count: column 0 (the
        # source pk) plus exactly one column per fresh target reached so far, i.e.
        # width == 1 + (count_fresh(chain) - count_fresh(chain[i:])).
        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + count_fresh(ToSeq(chain).drop(i)))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(chain),
                                               ToSeq(chain)[k] == 0 or ToSeq(chain)[k] == 1)))
        # column 0 iff this target is a primary-key chain
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i,
                                               (result[k] == 0) == (ToSeq(chain)[k] == 1))))
        # every fresh column already placed sits at its EXACT dense index: one
        # past the number of fresh targets strictly before it.
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and result[k] != 0,
                  result[k] == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(k))))))
        # invariants-end
        Assert(ToSeq(chain)[i] == chain[i])
        # Peel the head of the un-walked suffix: chain[i:][0] is chain[i] and
        # chain[i:].drop(1) is chain[i+1:], so count_fresh unfolds one step here.
        Assert(ToSeq(chain).drop(i)[0] == ToSeq(chain)[i])
        Assert(ToSeq(chain).drop(i).drop(1) == ToSeq(chain).drop(i + 1))
        if chain[i] == 1:
            result = result + [0]
        else:
            # The fresh column placed here is the running `width`, which the
            # suffix invariant pins to 1 + (fresh strictly before i) — exactly
            # the dense index for target i.
            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))
            result = result + [width]
            width = width + 1
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit for django__django-15563 (nagini). Interpreter: python; verifier: scripts/nagini_verify.sh.

SPEC ANALYSIS: assign_columns(chain) has three postconditions that pin Result()[k] POINTWISE for EVERY k over the {0,1} domain: (a) len(Result())==len(chain); (b) biconditional (Result()[k]==0)==(chain[k]==1); (c) for chain[k]==0, the EXACT dense index Result()[k]==1+(count_fresh(chain)-count_fresh(chain[k:])). Together these uniquely determine the output as the gold column-assignment function on every input, leaving no room for a behaviorally-distinct verifying impl. count_fresh is a frozen @Pure helper (spec region), so attacks cannot weaken it.

ATTACKS (all confirmed SAME-SPEC via `adversary same-spec`, exit 0; then run through `adversary weakness nagini django__django-15563 <file>`):
- atk_1 (control-flow-effect / prepatch echo: every target -> col 0): NOT-A-COUNTEREXAMPLE, verify failed (exit 2). gold-diff at flags=(0,).
- atk_2 (boundary/off-by-one: width starts at 0, first fresh col collides w/ pk col 0): verify failed (exit 2). gold-diff at (0,).
- atk_3 (sparse: width+=2, the historic batch08 IndexError survivor): verify failed (exit 2). gold-diff at (0,0) got [1,3] vs gold [1,2].
- atk_4 (inverted biconditional: branches swapped): verify failed (exit 2). gold-diff at (0,).
- atk_5 (partial-domain: non-chain target -> constant col 1): verify failed (exit 2). gold-diff at (0,0) got [1,1].
- atk_6 (ungrounded-oracle echo of atk_5 via 1-0): verify failed (exit 2). gold-diff at (0,0).
- atk_7 (shifted dense index: width starts at 2, over-runs row width by 1): verify failed (exit 2). gold-diff at (0,).
- atk_8 (faithful alternative correct impl: `chain[i]!=0` complement of gold `==1`): CANDIDATE — SAME-SPEC AND VERIFIES (exit 0, 117.1s). Proven gold-EQUAL on all binary vectors n<=9 (behavioral-equivalence harness). Its faithful refined patch = the gold patch.py verbatim (refines under refinement.md map A1-A5; the `!=0`/`==1` complement is logically identical). MATERIALIZED and RUN through the official harness: run_resolve("django__django-15563", gold_patch) => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, non-flaky (log resolve_atk8.txt). A resolving echo of the gold is NOT a weakness (verify=>correct holds for it).

No verifying wrong impl exists: the only same-spec impl that verified (atk_8) is gold-equivalent and its patch resolves. Every genuinely-wrong impl (atk_1..7 across partial-domain, boundary, control-flow-effect, sparse-index, ungrounded-oracle-echo classes) is REJECTED by the verifier — the spec is tight.

POSITIVE CONTROL: bundle model.py verifies (exit 0, 104.8s).
PREPATCH: model_prepatch.py is SAME-SPEC and FAILS verify (exit 1, 16.5s) precisely on the biconditional postcondition (Result()[k]==0)==(chain[k]==1) — the bug is sensed (G-DIFF), so prepatch_reproduced=true.

REFINEMENT.md AUDIT (A-legs + correspondence): axioms=[] (NO consumed @ContractOnly axiom, confirmed in model.py axioms region and meta). Legs: A1 (index domain 0..len-1 <-> ordered related_updates keys) = R; A2 (chain[i] <-> all(path.join_field.primary_key for path in meta.get_path_to_parent(related))) = A-reference, validated by axiom_check.py/G-AX against REAL Django 4.x on BOTH F2P scenarios (Congressman parent-through-child, Senator grand-parent-through-child), reproducing gold column assignment at the INDEX level (model_index[k]==0 <=> real_is_pk_chain[k], NO double mask) + 20000 fuzz vectors == gold construction (meta G-AX=pass); A3 (reuse col 0) = I; A4 (fresh col = running width <-> len(fields)) = R; A5 (result list <-> index projection of related_ids_index + add_fields) = R; Site B/P (r[index] projection + keyed self.related_ids[model] filter) = R/I.

Section C confirmed: NO kind-3 (unexpressible-changed-op) leg — the one genuinely-changed op (per-ancestor column choice) is modeled DEEPLY in assign_columns, and the sole abstracted callee is the A-reference (get_path_to_parent/join_field.primary_key). A2 correspondence to the real callee holds (axiom_check.py drives the real UpdateQuery.add_update_values and evaluates the real predicate). No kind-3 steps.

VERDICT: SOUND. 8 same-spec attacks run; 7 wrong impls rejected by the verifier; the lone verifying candidate (atk_8) is gold-equal and its materialized faithful patch RESOLVES under run_resolve. verify=>correct holds; the spec admits no verifying-but-incorrect implementation.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled assign_columns and the real repo behavior. Evidence: (1) same-spec identity check returns SAME (exit 0) — spec region byte-identical. (2) Model verifies under pinned Nagini (Verification successful, 111.9s) — spec is satisfiable, not vacuously/over-strong. (3) Independent 500k random-flag-vector differential: model's assign_columns == the gold related_ids_index construction (fields starts [pk] len 1, non-pk-chain target gets column len(fields) then fields grows by 1 => contiguous block 1..F) with 0 disagreements, while also satisfying both discriminating postconditions: biconditional (Result()[k]==0 iff chain[k]==1) and the dense-index pin Result()[k]==1+(count_fresh(chain)-count_fresh(chain[k:])). (4) Shipped gates corroborate on the REAL callee: G-CONF 100040 inputs / 0 disagreements against the real patched SQLUpdateCompiler.pre_sql_setup; G-AX drives real Django 4.x get_path_to_parent/join_field.primary_key on both F2P MTI scenarios (Congressman, Senator) and reproduces the gold column assignment at the index level with no double mask; G-DIFF confirms model_prepatch (all column 0) verification-fails, so the spec senses the bug rather than over-constraining. The single abstraction (path-primary-key predicate -> 0/1 flag) is an A-reference validated against the real callee, not a strengthening. The dense-index pin matches the real running-width semantics exactly (len(fields)), so it is not a spec-too-strong artifact. Spec is faithful to the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py with the impl region (lines 106-149) elided; refinement.md/mapping.md are NOT part of the leak screen (leakage.screen consumes only solution_src()). Mechanical screen run directly: PASSED with zero hard_failures; bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md, meta G-LEAK status='pass'). Semantic check beyond the lexical screen: (1) neither patched file (compiler.py, subqueries.py) nor any patched symbol (pre_sql_setup, get_related_updates) appears in the spec view — the abstracted callee is referred to only as 'the unchanged path-classification callee', never get_path_to_parent/join_field.primary_key; (2) no gold-patch line, diff marker, or bug/fix narration (docstring explicitly frames content as 'desired behaviour, not as an edit'); (3) the behavioral facts stated (per-ancestor column assignment; each ancestor read from its own column, never uniformly column 0) are the corrected behavior of the bug ALREADY disclosed publicly in problem_statement, which shows the wrong single-pk SELECT and states 'query is using primary keys from Base class'. The spec describes required behavior in its own List[int]/PSeq carrier vocabulary, not edit localization. axiom_check.py / G-AX references are internal audit-tooling, not gold-edit reconstruction. No spec-view line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.