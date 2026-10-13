# P2 adversarial audit — sympy__sympy-15017

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_self_recursion.py`, `atk_2_infinite_loop.py`, `atk_3_const_zero.py`, `atk_4_offbyone.py`, `atk_5_prepatch.py`, `atk_6_partial_empty.py`, `atk_8_reverse_fold.py`, `atk_9_control_flow_early.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7_oracle_echo.py`, `atk_10_echo_via_local.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl whose faithful refined patch fails to resolve was found. The postcondition Result()==axis_count(ToSeq(shape),len(shape)) together with Implies(len(shape)==0,Result()==1) fully pins Result to the exact gold value reduce(mul,shape,1); MustTerminate(2) closes the vacuous-Ensures / divergence loophole. Every verifying same-spec impl therefore returns the gold value and its faithful patch IS the gold edit, which resolves.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_self_recursion.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,21 +90,5 @@
     Ensures(Implies(len(shape) == 0, Result() == 1))
     # post-conditions-end
     # impl-start
-    acc = 1
-    i = 0
-    while i < len(shape):
-        # invariants-start
-        Invariant(Acc(list_pred(shape), 1 / 2))
-        Invariant(0 <= i and i <= len(shape))
-        Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
-        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
-        acc = acc * shape[i]
-        i = i + 1
-    Assert(i == len(shape))
-    return acc
+    return array_element_count(shape)
     # impl-end
```

Attack 2 — `atk_2_infinite_loop.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,18 +93,10 @@
     acc = 1
     i = 0
     while i < len(shape):
-        # invariants-start
         Invariant(Acc(list_pred(shape), 1 / 2))
         Invariant(0 <= i and i <= len(shape))
         Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
-        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
         acc = acc * shape[i]
-        i = i + 1
-    Assert(i == len(shape))
     return acc
     # impl-end
```

Attack 3 — `atk_3_const_zero.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,21 +90,5 @@
     Ensures(Implies(len(shape) == 0, Result() == 1))
     # post-conditions-end
     # impl-start
-    acc = 1
-    i = 0
-    while i < len(shape):
-        # invariants-start
-        Invariant(Acc(list_pred(shape), 1 / 2))
-        Invariant(0 <= i and i <= len(shape))
-        Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
-        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
-        acc = acc * shape[i]
-        i = i + 1
-    Assert(i == len(shape))
-    return acc
+    return 0
     # impl-end
```

Attack 4 — `atk_4_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,19 +92,12 @@
     # impl-start
     acc = 1
     i = 0
-    while i < len(shape):
-        # invariants-start
+    while i < len(shape) - 1:
         Invariant(Acc(list_pred(shape), 1 / 2))
         Invariant(0 <= i and i <= len(shape))
         Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
-        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
         acc = acc * shape[i]
         i = i + 1
-    Assert(i == len(shape))
     return acc
     # impl-end
```

Attack 5 — `atk_5_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,18 +90,15 @@
     Ensures(Implies(len(shape) == 0, Result() == 1))
     # post-conditions-end
     # impl-start
-    acc = 1
-    i = 0
+    if len(shape) == 0:
+        return 0
+    acc = shape[0]
+    i = 1
     while i < len(shape):
-        # invariants-start
         Invariant(Acc(list_pred(shape), 1 / 2))
-        Invariant(0 <= i and i <= len(shape))
+        Invariant(1 <= i and i <= len(shape))
         Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
         Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
         acc = acc * shape[i]
         i = i + 1
```

Attack 6 — `atk_6_partial_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,21 +90,17 @@
     Ensures(Implies(len(shape) == 0, Result() == 1))
     # post-conditions-end
     # impl-start
+    if len(shape) == 0:
+        return 2
     acc = 1
     i = 0
     while i < len(shape):
-        # invariants-start
         Invariant(Acc(list_pred(shape), 1 / 2))
         Invariant(0 <= i and i <= len(shape))
         Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
         Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
         acc = acc * shape[i]
         i = i + 1
-    Assert(i == len(shape))
     return acc
     # impl-end
```

Attack 7 — `atk_7_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,21 +90,5 @@
     Ensures(Implies(len(shape) == 0, Result() == 1))
     # post-conditions-end
     # impl-start
-    acc = 1
-    i = 0
-    while i < len(shape):
-        # invariants-start
-        Invariant(Acc(list_pred(shape), 1 / 2))
-        Invariant(0 <= i and i <= len(shape))
-        Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
-        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
-        acc = acc * shape[i]
-        i = i + 1
-    Assert(i == len(shape))
-    return acc
+    return axis_count(ToSeq(shape), len(shape))
     # impl-end
```

Attack 8 — `atk_8_reverse_fold.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,20 +91,12 @@
     # post-conditions-end
     # impl-start
     acc = 1
-    i = 0
-    while i < len(shape):
-        # invariants-start
+    i = len(shape)
+    while i > 0:
         Invariant(Acc(list_pred(shape), 1 / 2))
         Invariant(0 <= i and i <= len(shape))
-        Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
-        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
-        acc = acc * shape[i]
-        i = i + 1
-    Assert(i == len(shape))
+        Invariant(MustTerminate(i + 1))
+        acc = acc * shape[i - 1]
+        i = i - 1
     return acc
     # impl-end
```

Attack 9 — `atk_9_control_flow_early.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,18 +93,14 @@
     acc = 1
     i = 0
     while i < len(shape):
-        # invariants-start
         Invariant(Acc(list_pred(shape), 1 / 2))
         Invariant(0 <= i and i <= len(shape))
         Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
         Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
         acc = acc * shape[i]
         i = i + 1
-    Assert(i == len(shape))
+        if i == 1:
+            return acc
     return acc
     # impl-end
```

Attack 10 — `atk_10_echo_via_local.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,21 +90,6 @@
     Ensures(Implies(len(shape) == 0, Result() == 1))
     # post-conditions-end
     # impl-start
-    acc = 1
-    i = 0
-    while i < len(shape):
-        # invariants-start
-        Invariant(Acc(list_pred(shape), 1 / 2))
-        Invariant(0 <= i and i <= len(shape))
-        Invariant(acc == axis_count(ToSeq(shape), i))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(shape) - i + 1,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(shape) - i + 1))
-        # invariants-end
-        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
-        acc = acc * shape[i]
-        i = i + 1
-    Assert(i == len(shape))
-    return acc
+    res = axis_count(ToSeq(shape), len(shape))
+    return res
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-15017.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multidimensional array is described by its shape: a finite sequence of
  axis lengths `shape[0], shape[1], ..., shape[k-1]` (each a non-negative
  integer dimension count). The number of stored elements of the array — the
  value reported as its length — is the PRODUCT of the axis lengths over every
  axis of the shape:

      element_count = shape[0] * shape[1] * ... * shape[k-1]

  The product is taken with the empty-product convention: a shape with NO axes
  (the rank-zero / scalar case, an empty sequence) has element count ONE, not
  zero, because a scalar holds exactly one element (its single stored value).
  In particular the count is the neutral multiplicative element 1 when the
  shape is empty, and the running product of the lengths otherwise; a shape
  containing a zero-length axis yields count zero.

The axis lengths are modelled as `int`; which integers enter the product and
the empty-shape convention are precision-independent (refinement.md R0). The
shape is a `List[int]`; the specification is carried by `PSeq[int]` via
`ToSeq`. The product is spelled out deeply as a prefix-recursive fold whose
base case (no axes) is 1.

The count is computed by ONE bounded pass over the finitely many axes — the
real operation (`functools.reduce` over a finite tuple) always ANSWERS. Nagini
verifies partial correctness by default, so without a total-correctness
obligation a diverging implementation (bare self-recursion, an endless loop)
would satisfy every `Ensures` vacuously; the obligation is carried as
`MustTerminate` in the precondition and consumed by the loop with a strictly
decreasing, bounded-below measure. Markers (machine-parsed) delimit the spec /
proof / impl regions; provenance binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no axiomatized callees: the changed operation — the running product of the
# axis lengths with empty-product == 1 — is modelled deeply in the pure region
# below, not behind an opaque axiom.)
# axioms-end

# pure-start
@Pure
def axis_count(shape: PSeq[int], k: int) -> int:
    """The element count contributed by the first `k` axes `0 <= i < k`: the
    running product of their lengths. Prefix-recursive (extends by one axis per
    step) so the multiplication loop's invariant can track `acc ==
    axis_count(shape, i)`. The base case — zero axes — is the empty product 1,
    which is exactly the rank-zero (scalar) element count."""
    Requires(0 <= k and k <= len(shape))
    if k == 0:
        return 1
    return axis_count(shape, k - 1) * shape[k - 1]

@Pure
def lemma_axis_count_unfold(shape: PSeq[int], k: int) -> bool:
    """The prefix-recursion equation of `axis_count`, exposed for callers (its
    body unfolded once)."""
    Requires(0 < k and k <= len(shape))
    Ensures(Result())
    Ensures(axis_count(shape, k) == axis_count(shape, k - 1) * shape[k - 1])
    return True
# pure-end

def array_element_count(shape: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(shape), 1 / 2))
    # Total-correctness obligation: the count must ANSWER. The real operation
    # is one bounded fold over the finitely many axes (`reduce(mul, shape, 1)`)
    # and always returns; without this a diverging impl (bare self-recursion,
    # endless loop) satisfies the Ensures vacuously. Measure 2: the impl may
    # invoke the pure helpers but may NOT re-invoke this routine itself.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(shape), 1 / 2))
    # The element count is the product of the axis lengths over EVERY axis,
    # taken with the empty-product convention: a shape with no axes (rank zero /
    # scalar) has count 1, never 0; otherwise the running product of the lengths.
    Ensures(Result() == axis_count(ToSeq(shape), len(shape)))
    # At the rank-zero boundary: a shape with no axes counts exactly one
    # element (the single scalar value), not zero.
    Ensures(Implies(len(shape) == 0, Result() == 1))
    # post-conditions-end
    # impl-start
    acc = 1
    i = 0
    while i < len(shape):
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        Invariant(MustTerminate(len(shape) - i + 1))
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 10 attacks share the bundle spec byte-identical (only the impl region edited; head/tail regions verified byte-identical to model.py via programmatic diff for a sample).

positive control: bash scripts/nagini_verify.sh <D>/pos_control.py  -> Verification successful (20.83s)
per attack: python -m swebench_unified.adversary weakness nagini sympy__sympy-15017 <D>/atk_N.py

### Per-attack observed weakness result
  atk_1_self_recursion (return array_element_count(shape)) -> NOT-A-COUNTEREXAMPLE (exit2): MustTerminate(2) forbids re-invoking self; does not verify.
  atk_2_infinite_loop (loop w/o increment) -> NOT-A-COUNTEREXAMPLE (exit2): MustTerminate measure not strictly decreasing.
  atk_3_const_zero (return 0) -> NOT-A-COUNTEREXAMPLE (exit2): fails postcondition (empty must be 1, non-empty product).
  atk_4_offbyone (loop i<len-1, drops last axis) -> NOT-A-COUNTEREXAMPLE (exit2): acc!=axis_count(...,len).
  atk_5_prepatch (if len==0: return 0; seed=shape[0] fold rest) -> NOT-A-COUNTEREXAMPLE (exit2): PREPATCH BUG reproduced; fails Implies(len==0,Result==1).
  atk_6_partial_empty (correct except empty->2) -> NOT-A-COUNTEREXAMPLE (exit2): boundary; fails rank-zero clause.
  atk_7_oracle_echo (return axis_count(ToSeq(shape),len(shape))) -> CANDIDATE (exit0), verifies 16.9s.
  atk_8_reverse_fold (fold from end) -> NOT-A-COUNTEREXAMPLE (exit2): loop invariant acc==axis_count(...,i) unprovable for reverse order.
  atk_9_control_flow_early (early return after first axis) -> NOT-A-COUNTEREXAMPLE (exit2): partial product, fails postcondition.
  atk_10_echo_via_local (res=axis_count(...); return res) -> CANDIDATE (exit0), verifies 17.4s.

MANDATORY RESOLVE STEP (the step the prior INCONCLUSIVE pass never completed): both candidates atk_7 and atk_10 return exactly axis_count(ToSeq(shape),len(shape)) == reduce(mul,shape,1) == the gold value, so their faithful refined patches are IDENTICAL and equal to the gold edit (patch_7.diff). Materialized it and ran the OFFICIAL harness:
  python -c 'from swebench_unified.harness import run_resolve; run_resolve("sympy__sympy-15017", <patch_7.diff>)'
  -> RESOLVED: True, COMPLETED: True, note='resolved'.
A verifying wrong-impl whose faithful patch RESOLVES is NOT a weakness (verify=>correct holds here). No BROKEN candidate found.

REFINEMENT AUDIT (refinement.md): legs R0(R), A1(R Tuple/Integer<->List[int]), A1b(R MustTerminate total-correctness), A2(R reduce(mul,shape,1)<->verified fold), A3(I __len__ identity return self._loop_size). All R or I; NO kind-3 (unexpressible-changed-op) steps. The single changed op (empty-product convention, rank-zero count=1 not 0) is modeled DEEPLY via prefix-recursive @Pure axis_count base case 1, NOT behind an opaque axiom. Confirmed on disk: axioms region empty (comment only), 0 @ContractOnly, no axiom_check.py shipped => G-AX vacuous, no A-consumed / A-reference callee correspondence to validate. MustTerminate genuinely enforced (all 3 divergence attacks failed to verify).

VERDICT: SOUND. 10 same-spec wrong-impl attacks + positive control run to completion. 8 rejected (do not verify). 2 verifying candidates (echo of gold) had their materialized faithful patch RUN through the official harness -> RESOLVED True. No verifying impl whose faithful patch fails to resolve exists; spec fully pins Result and MustTerminate closes divergence. Not INCONCLUSIVE: all needed verifications and the resolve run completed with recorded evidence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_self_recursion.py`, `atk_2_infinite_loop.py`, `atk_3_const_zero.py`, `atk_4_offbyone.py`, `atk_5_prepatch.py`, `atk_6_partial_empty.py`, `atk_8_reverse_fold.py`, `atk_9_control_flow_early.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7_oracle_echo.py`, `atk_10_echo_via_local.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl whose faithful refined patch fails to resolve was found. The postcondition Result()==axis_count(ToSeq(shape),len(shape)) together with Implies(len(shape)==0,Result()==1) fully pins Result to the exact gold value reduce(mul,shape,1); MustTerminate(2) closes the vacuous-Ensures / divergence loophole. Every verifying same-spec impl therefore returns the gold value and its faithful patch IS the gold edit, which resolves.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_self_recursion.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_infinite_loop.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_const_zero.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_offbyone.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_prepatch.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_partial_empty.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_reverse_fold.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_control_flow_early.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_echo_via_local.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-15017.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multidimensional array is described by its shape: a finite sequence of
  axis lengths `shape[0], shape[1], ..., shape[k-1]` (each a non-negative
  integer dimension count). The number of stored elements of the array — the
  value reported as its length — is the PRODUCT of the axis lengths over every
  axis of the shape:

      element_count = shape[0] * shape[1] * ... * shape[k-1]

  The product is taken with the empty-product convention: a shape with NO axes
  (the rank-zero / scalar case, an empty sequence) has element count ONE, not
  zero, because a scalar holds exactly one element (its single stored value).
  In particular the count is the neutral multiplicative element 1 when the
  shape is empty, and the running product of the lengths otherwise; a shape
  containing a zero-length axis yields count zero.

The axis lengths are modelled as `int`; which integers enter the product and
the empty-shape convention are precision-independent (refinement.md R0). The
shape is a `List[int]`; the specification is carried by `PSeq[int]` via
`ToSeq`. The product is spelled out deeply as a prefix-recursive fold whose
base case (no axes) is 1.

The count is computed by ONE bounded pass over the finitely many axes — the
real operation (`functools.reduce` over a finite tuple) always ANSWERS. Nagini
verifies partial correctness by default, so without a total-correctness
obligation a diverging implementation (bare self-recursion, an endless loop)
would satisfy every `Ensures` vacuously; the obligation is carried as
`MustTerminate` in the precondition and consumed by the loop with a strictly
decreasing, bounded-below measure. Markers (machine-parsed) delimit the spec /
proof / impl regions; provenance binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no axiomatized callees: the changed operation — the running product of the
# axis lengths with empty-product == 1 — is modelled deeply in the pure region
# below, not behind an opaque axiom.)
# axioms-end

# pure-start
@Pure
def axis_count(shape: PSeq[int], k: int) -> int:
    """The element count contributed by the first `k` axes `0 <= i < k`: the
    running product of their lengths. Prefix-recursive (extends by one axis per
    step) so the multiplication loop's invariant can track `acc ==
    axis_count(shape, i)`. The base case — zero axes — is the empty product 1,
    which is exactly the rank-zero (scalar) element count."""
    Requires(0 <= k and k <= len(shape))
    if k == 0:
        return 1
    return axis_count(shape, k - 1) * shape[k - 1]

@Pure
def lemma_axis_count_unfold(shape: PSeq[int], k: int) -> bool:
    """The prefix-recursion equation of `axis_count`, exposed for callers (its
    body unfolded once)."""
    Requires(0 < k and k <= len(shape))
    Ensures(Result())
    Ensures(axis_count(shape, k) == axis_count(shape, k - 1) * shape[k - 1])
    return True
# pure-end

def array_element_count(shape: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(shape), 1 / 2))
    # Total-correctness obligation: the count must ANSWER. The real operation
    # is one bounded fold over the finitely many axes (`reduce(mul, shape, 1)`)
    # and always returns; without this a diverging impl (bare self-recursion,
    # endless loop) satisfies the Ensures vacuously. Measure 2: the impl may
    # invoke the pure helpers but may NOT re-invoke this routine itself.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(shape), 1 / 2))
    # The element count is the product of the axis lengths over EVERY axis,
    # taken with the empty-product convention: a shape with no axes (rank zero /
    # scalar) has count 1, never 0; otherwise the running product of the lengths.
    Ensures(Result() == axis_count(ToSeq(shape), len(shape)))
    # At the rank-zero boundary: a shape with no axes counts exactly one
    # element (the single scalar value), not zero.
    Ensures(Implies(len(shape) == 0, Result() == 1))
    # post-conditions-end
    # impl-start
    acc = 1
    i = 0
    while i < len(shape):
        Invariant(Acc(list_pred(shape), 1 / 2))
        Invariant(0 <= i and i <= len(shape))
        Invariant(acc == axis_count(ToSeq(shape), i))
        Invariant(MustTerminate(len(shape) - i + 1))
        Assert(lemma_axis_count_unfold(ToSeq(shape), i + 1))
        acc = acc * shape[i]
        i = i + 1
    Assert(i == len(shape))
    return acc
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 10 attacks share the bundle spec byte-identical (only the impl region edited; head/tail regions verified byte-identical to model.py via programmatic diff for a sample).

positive control: bash scripts/nagini_verify.sh <D>/pos_control.py  -> Verification successful (20.83s)
per attack: python -m swebench_unified.adversary weakness nagini sympy__sympy-15017 <D>/atk_N.py

### Per-attack observed weakness result
  atk_1_self_recursion (return array_element_count(shape)) -> NOT-A-COUNTEREXAMPLE (exit2): MustTerminate(2) forbids re-invoking self; does not verify.
  atk_2_infinite_loop (loop w/o increment) -> NOT-A-COUNTEREXAMPLE (exit2): MustTerminate measure not strictly decreasing.
  atk_3_const_zero (return 0) -> NOT-A-COUNTEREXAMPLE (exit2): fails postcondition (empty must be 1, non-empty product).
  atk_4_offbyone (loop i<len-1, drops last axis) -> NOT-A-COUNTEREXAMPLE (exit2): acc!=axis_count(...,len).
  atk_5_prepatch (if len==0: return 0; seed=shape[0] fold rest) -> NOT-A-COUNTEREXAMPLE (exit2): PREPATCH BUG reproduced; fails Implies(len==0,Result==1).
  atk_6_partial_empty (correct except empty->2) -> NOT-A-COUNTEREXAMPLE (exit2): boundary; fails rank-zero clause.
  atk_7_oracle_echo (return axis_count(ToSeq(shape),len(shape))) -> CANDIDATE (exit0), verifies 16.9s.
  atk_8_reverse_fold (fold from end) -> NOT-A-COUNTEREXAMPLE (exit2): loop invariant acc==axis_count(...,i) unprovable for reverse order.
  atk_9_control_flow_early (early return after first axis) -> NOT-A-COUNTEREXAMPLE (exit2): partial product, fails postcondition.
  atk_10_echo_via_local (res=axis_count(...); return res) -> CANDIDATE (exit0), verifies 17.4s.

MANDATORY RESOLVE STEP (the step the prior INCONCLUSIVE pass never completed): both candidates atk_7 and atk_10 return exactly axis_count(ToSeq(shape),len(shape)) == reduce(mul,shape,1) == the gold value, so their faithful refined patches are IDENTICAL and equal to the gold edit (patch_7.diff). Materialized it and ran the OFFICIAL harness:
  python -c 'from swebench_unified.harness import run_resolve; run_resolve("sympy__sympy-15017", <patch_7.diff>)'
  -> RESOLVED: True, COMPLETED: True, note='resolved'.
A verifying wrong-impl whose faithful patch RESOLVES is NOT a weakness (verify=>correct holds here). No BROKEN candidate found.

REFINEMENT AUDIT (refinement.md): legs R0(R), A1(R Tuple/Integer<->List[int]), A1b(R MustTerminate total-correctness), A2(R reduce(mul,shape,1)<->verified fold), A3(I __len__ identity return self._loop_size). All R or I; NO kind-3 (unexpressible-changed-op) steps. The single changed op (empty-product convention, rank-zero count=1 not 0) is modeled DEEPLY via prefix-recursive @Pure axis_count base case 1, NOT behind an opaque axiom. Confirmed on disk: axioms region empty (comment only), 0 @ContractOnly, no axiom_check.py shipped => G-AX vacuous, no A-consumed / A-reference callee correspondence to validate. MustTerminate genuinely enforced (all 3 divergence attacks failed to verify).

VERDICT: SOUND. 10 same-spec wrong-impl attacks + positive control run to completion. 8 rejected (do not verify). 2 verifying candidates (echo of gold) had their materialized faithful patch RUN through the official harness -> RESOLVED True. No verifying impl whose faithful patch fails to resolve exists; spec fully pins Result and MustTerminate closes divergence. Not INCONCLUSIVE: all needed verifications and the resolve run completed with recorded evidence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-15017 nagini bundle. The modeled unit is array_element_count(shape) ~ the _loop_size computation in ImmutableDenseNDimArray._new (dense_ndim_array.py:152), reported via NDimArray.__len__ (identity return self._loop_size). The gold patch changes `functools.reduce(mul, shape) if shape else 0` -> `functools.reduce(mul, shape, 1)`; the model specifies the POST-patch behavior via axis_count(shape,k): base case k==0 -> 1 (empty product), else axis_count(shape,k-1)*shape[k-1]. The postcondition Result()==axis_count(ToSeq(shape),len(shape)) is exactly reduce(mul,shape,1). 

Evidence: (1) model.py verifies under pinned Nagini (exit 0, 16.7s). (2) Differential test of axis_count vs functools.reduce(mul,shape,1) over 2010 inputs (empty [], [0], zero-axis shapes, products up to 1e12, negatives) -> 0 divergences. (3) The spec imposes NO domain restriction beyond Acc(list_pred(shape),1/2) — no valid input is excluded, so it is not too strong. The extra clause Implies(len(shape)==0, Result()==1) is redundant with the axis_count fold (empty product), not an over-constraint. (4) MustTerminate(2) is a standard total-correctness obligation correctly reflecting that the real bounded fold over finitely many axes always returns; it does not exclude any behavior of the real callee. 

Note: the /tmp worktree at base_commit 6810dee holds the PRE-patch source (reduce(mul,shape) if shape else 0); the model correctly targets the gold-patched (fixed) callee, which is the intended correctness oracle. The modeled function agrees with the real post-patch callee on every input; no diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + axioms + pure region [axis_count, lemma_axis_count_unfold] + pre/post-conditions of array_element_count; impl elided) assessed against the PUBLIC problem_statement only (hints excluded). same-spec confirms atk.py == bundle spec (exit 0, byte-identical).

Gold edit (sole discriminator): `self._loop_size = functools.reduce(lambda x,y: x*y, shape) if shape else 0` -> `functools.reduce(lambda x,y: x*y, shape, 1)`. Only behavioral change: empty-shape / rank-0 (scalar) case now yields count 1 instead of 0 (empty-product convention); non-empty products unchanged.

The public problem_statement ALREADY fully discloses this discriminator: it states NDimArray.__len__ 'always returns zero for rank-0 arrays (scalars)' and 'the correct value should be one, which is the number of elements of the iterator', with the concrete sympy.Array(3) len 0-vs-1 example and the numpy .size==1 analogy. So the spec view's 'empty-product convention ... element count ONE, not zero' is a rewording of information the solver already has.

- 'element_count = product of axis lengths' is the faithful natural spec of the length computation and is the PRE-patch behavior for non-empty shapes, not the edit.
- functools.reduce is named as provenance but appears in BOTH pre- and post-patch code, so naming it discloses nothing about what changed; the discriminating 'seed 1 / empty-product' fact is exactly what the public statement gives.
- No implementation locus leaks: token scan of the rendered spec view shows _loop_size=absent, dense_ndim_array=absent, ndim_array=absent, __len__=absent, ImmutableDense=absent, base_commit/commit-hash=absent. Patched path/symbol appear only in mapping.md (out of spec-view scope).
- No L1 diff markers, no verbatim gold-patch line, no path/symbol/hash narration.
- Not a relaxed-leakage bundle (flag absent, no RELAXED_LEAKAGE.md); no deferral needed.

Every discriminating fact in the spec view is already in the public problem_statement; nothing hands the solver the gold edit beyond the task.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.