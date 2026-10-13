# P2 adversarial audit — pydata__xarray-4356

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,16 +74,12 @@
             (prod(ToSeq(sizes)) - missing - required_minimum < 0))
     # post-conditions-end
     # impl-start
-    # total = product over the reduced axes of their sizes  (select then product)
     total = 1
     k = 0
     while k < len(sizes):
-        # invariants-start
         Invariant(Acc(list_pred(sizes), 1 / 2))
         Invariant(0 <= k and k <= len(sizes))
-        # the running product is the product over the sizes processed so far
         Invariant(total == prod(ToSeq(sizes).take(k)))
-        # invariants-end
         Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
         Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
         lemma_prod_snoc(ToSeq(sizes).take(k + 1))
@@ -91,7 +87,7 @@
         k = k + 1
     Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
     Assert(total == prod(ToSeq(sizes)))
-    return (total - missing - required_minimum) < 0
+    return (total - missing - required_minimum) <= 0
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,23 +74,7 @@
             (prod(ToSeq(sizes)) - missing - required_minimum < 0))
     # post-conditions-end
     # impl-start
-    # total = product over the reduced axes of their sizes  (select then product)
-    total = 1
-    k = 0
-    while k < len(sizes):
-        # invariants-start
-        Invariant(Acc(list_pred(sizes), 1 / 2))
-        Invariant(0 <= k and k <= len(sizes))
-        # the running product is the product over the sizes processed so far
-        Invariant(total == prod(ToSeq(sizes).take(k)))
-        # invariants-end
-        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
-        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
-        lemma_prod_snoc(ToSeq(sizes).take(k + 1))
-        total = total * sizes[k]
-        k = k + 1
-    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
-    Assert(total == prod(ToSeq(sizes)))
+    total = sizes[0]
     return (total - missing - required_minimum) < 0
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,23 +74,7 @@
             (prod(ToSeq(sizes)) - missing - required_minimum < 0))
     # post-conditions-end
     # impl-start
-    # total = product over the reduced axes of their sizes  (select then product)
-    total = 1
-    k = 0
-    while k < len(sizes):
-        # invariants-start
-        Invariant(Acc(list_pred(sizes), 1 / 2))
-        Invariant(0 <= k and k <= len(sizes))
-        # the running product is the product over the sizes processed so far
-        Invariant(total == prod(ToSeq(sizes).take(k)))
-        # invariants-end
-        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
-        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
-        lemma_prod_snoc(ToSeq(sizes).take(k + 1))
-        total = total * sizes[k]
-        k = k + 1
-    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
-    Assert(total == prod(ToSeq(sizes)))
+    total = len(sizes)
     return (total - missing - required_minimum) < 0
     # impl-end
 
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -74,24 +74,7 @@
             (prod(ToSeq(sizes)) - missing - required_minimum < 0))
     # post-conditions-end
     # impl-start
-    # total = product over the reduced axes of their sizes  (select then product)
-    total = 1
-    k = 0
-    while k < len(sizes):
-        # invariants-start
-        Invariant(Acc(list_pred(sizes), 1 / 2))
-        Invariant(0 <= k and k <= len(sizes))
-        # the running product is the product over the sizes processed so far
-        Invariant(total == prod(ToSeq(sizes).take(k)))
-        # invariants-end
-        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
-        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
-        lemma_prod_snoc(ToSeq(sizes).take(k + 1))
-        total = total * sizes[k]
-        k = k + 1
-    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
-    Assert(total == prod(ToSeq(sizes)))
-    return (total - missing - required_minimum) < 0
+    return (prod(ToSeq(sizes)) - missing - required_minimum) < 0
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,16 +74,14 @@
             (prod(ToSeq(sizes)) - missing - required_minimum < 0))
     # post-conditions-end
     # impl-start
-    # total = product over the reduced axes of their sizes  (select then product)
+    if len(sizes) == 1:
+        return (sizes[0] - missing - required_minimum) < 0
     total = 1
     k = 0
     while k < len(sizes):
-        # invariants-start
         Invariant(Acc(list_pred(sizes), 1 / 2))
         Invariant(0 <= k and k <= len(sizes))
-        # the running product is the product over the sizes processed so far
         Invariant(total == prod(ToSeq(sizes).take(k)))
-        # invariants-end
         Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
         Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
         lemma_prod_snoc(ToSeq(sizes).take(k + 1))
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -74,24 +74,19 @@
             (prod(ToSeq(sizes)) - missing - required_minimum < 0))
     # post-conditions-end
     # impl-start
-    # total = product over the reduced axes of their sizes  (select then product)
     total = 1
     k = 0
     while k < len(sizes):
-        # invariants-start
         Invariant(Acc(list_pred(sizes), 1 / 2))
         Invariant(0 <= k and k <= len(sizes))
-        # the running product is the product over the sizes processed so far
         Invariant(total == prod(ToSeq(sizes).take(k)))
-        # invariants-end
         Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
         Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
         lemma_prod_snoc(ToSeq(sizes).take(k + 1))
         total = total * sizes[k]
         k = k + 1
-    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
     Assert(total == prod(ToSeq(sizes)))
-    return (total - missing - required_minimum) < 0
+    return required_minimum > (total - missing)
     # impl-end
 
 
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,23 +74,13 @@
             (prod(ToSeq(sizes)) - missing - required_minimum < 0))
     # post-conditions-end
     # impl-start
-    # total = product over the reduced axes of their sizes  (select then product)
-    total = 1
+    total = 0
     k = 0
     while k < len(sizes):
-        # invariants-start
         Invariant(Acc(list_pred(sizes), 1 / 2))
         Invariant(0 <= k and k <= len(sizes))
-        # the running product is the product over the sizes processed so far
-        Invariant(total == prod(ToSeq(sizes).take(k)))
-        # invariants-end
-        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
-        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
-        lemma_prod_snoc(ToSeq(sizes).take(k + 1))
-        total = total * sizes[k]
+        total = total + sizes[k]
         k = k + 1
-    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
-    Assert(total == prod(ToSeq(sizes)))
     return (total - missing - required_minimum) < 0
     # impl-end
 
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,24 +74,19 @@
             (prod(ToSeq(sizes)) - missing - required_minimum < 0))
     # post-conditions-end
     # impl-start
-    # total = product over the reduced axes of their sizes  (select then product)
     total = 1
     k = 0
     while k < len(sizes):
-        # invariants-start
         Invariant(Acc(list_pred(sizes), 1 / 2))
         Invariant(0 <= k and k <= len(sizes))
-        # the running product is the product over the sizes processed so far
         Invariant(total == prod(ToSeq(sizes).take(k)))
-        # invariants-end
         Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
         Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
         lemma_prod_snoc(ToSeq(sizes).take(k + 1))
         total = total * sizes[k]
         k = k + 1
-    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
     Assert(total == prod(ToSeq(sizes)))
-    return (total - missing - required_minimum) < 0
+    return (total - missing - required_minimum) >= 0
     # impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-4356.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A masked reduction over a SET of axes records, at every output position, how
  many of the reduced-over input elements were missing, and compares the number
  of present (non-missing) elements against a required minimum. The position is
  flagged as "too few present" exactly when

      (present elements at the position) < (the required minimum),

  where the number of elements that were reduced over at a position is the
  COUNT OF THE WHOLE REDUCED BLOCK -- the product of the input's sizes along
  every reduced axis -- not the size of a single axis. With several reduced
  axes the block spans the PRODUCT of their sizes; with a single reduced axis it
  is just that axis's size. So, writing `total` for that product and `missing`
  for the number of missing elements at the position, the position is flagged
  iff `total - missing < required_minimum`.

  This must hold for any non-empty group of reduced axes (one or many), each
  with a positive size.

Modelling: `sizes` is the input's sizes along the reduced axes (`List[int]`,
the per-reduced-axis-list selection of the input's shape; each > 0). `prod`
folds them to `total`; `missing` is the number of missing elements at the
position (0 <= missing <= total). `flag_too_few` returns whether the position
is flagged.

`prod` is spelled out DEEPLY (front-recursive fold), and the composition
"select the reduced-axes sizes, then take their product" is validated == the
real select-then-product callee by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom: the changed quantity -- the product of the
# reduced-axes sizes -- is modelled deeply by `prod` below and validated against
# the real select-then-product callee by axiom_check.py (G-AX, an A-reference).
# There is no unchanged opaque callee the proof depends on.)
# axioms-end


# pure-start
@Pure
def prod(xs: PSeq[int]) -> int:
    """Product fold over a sequence (empty product is 1). Front-recursive so a
    single unfold is available per loop step."""
    if len(xs) == 0:
        return 1
    return xs[0] * prod(xs.drop(1))
# pure-end


def flag_too_few(sizes: List[int], missing: int,
                 required_minimum: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(sizes), 1 / 2))
    # at least one reduced axis
    Requires(len(sizes) >= 1)
    # the number of missing elements is between none and the whole block
    Requires(0 <= missing)
    Requires(missing <= prod(ToSeq(sizes)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(sizes), 1 / 2))
    # The position is flagged iff the present elements -- the product of the
    # reduced-axes sizes minus the missing ones -- are fewer than the minimum.
    Ensures(Result() ==
            (prod(ToSeq(sizes)) - missing - required_minimum < 0))
    # post-conditions-end
    # impl-start
    # total = product over the reduced axes of their sizes  (select then product)
    total = 1
    k = 0
    while k < len(sizes):
        # invariants-start
        Invariant(Acc(list_pred(sizes), 1 / 2))
        Invariant(0 <= k and k <= len(sizes))
        # the running product is the product over the sizes processed so far
        Invariant(total == prod(ToSeq(sizes).take(k)))
        # invariants-end
        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
        lemma_prod_snoc(ToSeq(sizes).take(k + 1))
        total = total * sizes[k]
        k = k + 1
    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
    Assert(total == prod(ToSeq(sizes)))
    return (total - missing - required_minimum) < 0
    # impl-end


def lemma_prod_snoc(xs: PSeq[int]) -> None:
    """Lemma: the product of a non-empty sequence equals the product of its
    front (all but the last) times the last element:
        prod(xs) == prod(xs.take(len-1)) * xs[len-1].
    Proved by induction on the front-recursive fold."""
    Requires(len(xs) >= 1)
    Ensures(prod(xs) == prod(xs.take(len(xs) - 1)) * xs[len(xs) - 1])
    if len(xs) == 1:
        Assert(xs.take(0) == PSeq(0).take(0))
        Assert(xs.drop(1) == PSeq(0).take(0))
    else:
        lemma_prod_snoc(xs.drop(1))
        Assert(xs[len(xs) - 1] == xs.drop(1)[len(xs) - 2])
        Assert(xs.take(len(xs) - 1).drop(1) == xs.drop(1).take(len(xs) - 2))
        Assert(prod(xs) == xs[0] * prod(xs.drop(1)))
        Assert(prod(xs.take(len(xs) - 1)) ==
               xs.take(len(xs) - 1)[0] * prod(xs.take(len(xs) - 1).drop(1)))
        Assert(xs.take(len(xs) - 1)[0] == xs[0])
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for pydata__xarray-4356 (nagini). VERDICT: SOUND. The frozen postcondition Result() == (prod(ToSeq(sizes)) - missing - required_minimum < 0) is a TIGHT functional spec: it fully pins Result() as a total function of the inputs over the entire Requires domain (len(sizes)>=1, 0<=missing<=prod(sizes)). Any verifying impl must return exactly the gold quantity.

Harness validation: positive control (bundle model.py, loop computing prod) is a CANDIDATE (shares spec AND verifies, 13.2s). Prepatch (prepatch.py = total=sizes[0], first-axis only) does NOT verify -> spec rejects the bug (prepatch reproduced/rejected).

8 same-spec attacks (all confirmed byte-identical spec via `same-spec`; only impl region edited).
- atk_1 off-by-one (<=0 instead of <0): REJECTED (does not verify) - good.
- atk_2 partial-domain first-axis total=sizes[0]: REJECTED - good.
- atk_3 ungrounded count total=len(sizes): REJECTED - good.
- atk_5 control-flow-effect (single-axis special case then product): REJECTED (correct-but-unproven; the len==1 branch lacks the invariant machinery) - good, spec is not weakened by it.
- atk_7 boundary/wrong-fold SUM of sizes instead of product: REJECTED - good.
- atk_8 control-flow negated comparison (>=0): REJECTED - good.
- atk_4 ungrounded-oracle ECHO (return prod(ToSeq(sizes)) - missing - required_minimum < 0 directly, calling @Pure prod): CANDIDATE (verifies, 15.2s).
- atk_6 rearranged-arithmetic echo (required_minimum > total - missing): CANDIDATE (verifies, 13.1s).

For BOTH candidates I materialized the faithful refined patch per refinement.md (delete the early raise on tuple/list axis + replace mask.shape[axis] with np.take(mask.shape,axis).prod(); atk_6's patch uses the behaviourally-identical min_count > (...) spelling) and RAN it through the official harness via swebench_unified.harness.run_resolve:
 - patch_atk_4.diff -> RESOLVED=True, completed=True, note=resolved.
 - patch_atk_6.diff -> RESOLVED=True, completed=True, note=resolved.
Both verifying wrong-candidate patches RESOLVE, so no verify-not-correct break exists (verify => correct holds for this spec).

Refinement.md audit: 5 legs, all R / A-reference / I; NO kind-3 (unexpressible-changed-op) leg. Step 1 (sizes<->np.take(mask.shape,axis)) R; step 2 (missing<->mask.sum(axis)) R; step 3 (required_minimum<->min_count) I; step 4 (prod(sizes)<->np.take(...).prod()) A-reference (the one changed quantity, modeled deeply, NOT consumed as axiom); step 5 (comparison) I+R. There is NO consumed @ContractOnly axiom (axioms region is a comment only). The single A-reference (step 4) correspondence to the real callee holds: re-ran bundle axiom_check.py (G-AX) = PASS (prod(select)==np.take(shape,axis).prod() on 13 boundary + 4000 fuzz; null_mask decision == gold numpy on 7 real-array configs). Independent broad cross-check: spec postcondition == real fixed numpy null_mask on 259,746 output positions (0 mismatches) over ndim 1-5, sizes 1-6, all non-empty proper axis subsets, min_count in [-2, block+3], real boolean masks; and prepatch single-axis semantics diverge from the spec on 23,303 of those positions (spec genuinely senses the change, G-DIFF). model<->patch correspondence is faithful and the A-reference is sound.

All >=8 attacks were fully verified and every candidate's materialized faithful patch was run through run_resolve; none breaks the spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-4356.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A masked reduction over a SET of axes records, at every output position, how
  many of the reduced-over input elements were missing, and compares the number
  of present (non-missing) elements against a required minimum. The position is
  flagged as "too few present" exactly when

      (present elements at the position) < (the required minimum),

  where the number of elements that were reduced over at a position is the
  COUNT OF THE WHOLE REDUCED BLOCK -- the product of the input's sizes along
  every reduced axis -- not the size of a single axis. With several reduced
  axes the block spans the PRODUCT of their sizes; with a single reduced axis it
  is just that axis's size. So, writing `total` for that product and `missing`
  for the number of missing elements at the position, the position is flagged
  iff `total - missing < required_minimum`.

  This must hold for any non-empty group of reduced axes (one or many), each
  with a positive size.

Modelling: `sizes` is the input's sizes along the reduced axes (`List[int]`,
the per-reduced-axis-list selection of the input's shape; each > 0). `prod`
folds them to `total`; `missing` is the number of missing elements at the
position (0 <= missing <= total). `flag_too_few` returns whether the position
is flagged.

`prod` is spelled out DEEPLY (front-recursive fold), and the composition
"select the reduced-axes sizes, then take their product" is validated == the
real select-then-product callee by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom: the changed quantity -- the product of the
# reduced-axes sizes -- is modelled deeply by `prod` below and validated against
# the real select-then-product callee by axiom_check.py (G-AX, an A-reference).
# There is no unchanged opaque callee the proof depends on.)
# axioms-end


# pure-start
@Pure
def prod(xs: PSeq[int]) -> int:
    """Product fold over a sequence (empty product is 1). Front-recursive so a
    single unfold is available per loop step."""
    if len(xs) == 0:
        return 1
    return xs[0] * prod(xs.drop(1))
# pure-end


def flag_too_few(sizes: List[int], missing: int,
                 required_minimum: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(sizes), 1 / 2))
    # at least one reduced axis
    Requires(len(sizes) >= 1)
    # the number of missing elements is between none and the whole block
    Requires(0 <= missing)
    Requires(missing <= prod(ToSeq(sizes)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(sizes), 1 / 2))
    # The position is flagged iff the present elements -- the product of the
    # reduced-axes sizes minus the missing ones -- are fewer than the minimum.
    Ensures(Result() ==
            (prod(ToSeq(sizes)) - missing - required_minimum < 0))
    # post-conditions-end
    # impl-start
    # total = product over the reduced axes of their sizes  (select then product)
    total = 1
    k = 0
    while k < len(sizes):
        # invariants-start
        Invariant(Acc(list_pred(sizes), 1 / 2))
        Invariant(0 <= k and k <= len(sizes))
        # the running product is the product over the sizes processed so far
        Invariant(total == prod(ToSeq(sizes).take(k)))
        # invariants-end
        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
        lemma_prod_snoc(ToSeq(sizes).take(k + 1))
        total = total * sizes[k]
        k = k + 1
    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
    Assert(total == prod(ToSeq(sizes)))
    return (total - missing - required_minimum) < 0
    # impl-end


def lemma_prod_snoc(xs: PSeq[int]) -> None:
    """Lemma: the product of a non-empty sequence equals the product of its
    front (all but the last) times the last element:
        prod(xs) == prod(xs.take(len-1)) * xs[len-1].
    Proved by induction on the front-recursive fold."""
    Requires(len(xs) >= 1)
    Ensures(prod(xs) == prod(xs.take(len(xs) - 1)) * xs[len(xs) - 1])
    if len(xs) == 1:
        Assert(xs.take(0) == PSeq(0).take(0))
        Assert(xs.drop(1) == PSeq(0).take(0))
    else:
        lemma_prod_snoc(xs.drop(1))
        Assert(xs[len(xs) - 1] == xs.drop(1)[len(xs) - 2])
        Assert(xs.take(len(xs) - 1).drop(1) == xs.drop(1).take(len(xs) - 2))
        Assert(prod(xs) == xs[0] * prod(xs.drop(1)))
        Assert(prod(xs.take(len(xs) - 1)) ==
               xs.take(len(xs) - 1)[0] * prod(xs.take(len(xs) - 1).drop(1)))
        Assert(xs.take(len(xs) - 1)[0] == xs[0])
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for pydata__xarray-4356 (nagini). VERDICT: SOUND. The frozen postcondition Result() == (prod(ToSeq(sizes)) - missing - required_minimum < 0) is a TIGHT functional spec: it fully pins Result() as a total function of the inputs over the entire Requires domain (len(sizes)>=1, 0<=missing<=prod(sizes)). Any verifying impl must return exactly the gold quantity.

Harness validation: positive control (bundle model.py, loop computing prod) is a CANDIDATE (shares spec AND verifies, 13.2s). Prepatch (prepatch.py = total=sizes[0], first-axis only) does NOT verify -> spec rejects the bug (prepatch reproduced/rejected).

8 same-spec attacks (all confirmed byte-identical spec via `same-spec`; only impl region edited).
- atk_1 off-by-one (<=0 instead of <0): REJECTED (does not verify) - good.
- atk_2 partial-domain first-axis total=sizes[0]: REJECTED - good.
- atk_3 ungrounded count total=len(sizes): REJECTED - good.
- atk_5 control-flow-effect (single-axis special case then product): REJECTED (correct-but-unproven; the len==1 branch lacks the invariant machinery) - good, spec is not weakened by it.
- atk_7 boundary/wrong-fold SUM of sizes instead of product: REJECTED - good.
- atk_8 control-flow negated comparison (>=0): REJECTED - good.
- atk_4 ungrounded-oracle ECHO (return prod(ToSeq(sizes)) - missing - required_minimum < 0 directly, calling @Pure prod): CANDIDATE (verifies, 15.2s).
- atk_6 rearranged-arithmetic echo (required_minimum > total - missing): CANDIDATE (verifies, 13.1s).

For BOTH candidates I materialized the faithful refined patch per refinement.md (delete the early raise on tuple/list axis + replace mask.shape[axis] with np.take(mask.shape,axis).prod(); atk_6's patch uses the behaviourally-identical min_count > (...) spelling) and RAN it through the official harness via swebench_unified.harness.run_resolve:
 - patch_atk_4.diff -> RESOLVED=True, completed=True, note=resolved.
 - patch_atk_6.diff -> RESOLVED=True, completed=True, note=resolved.
Both verifying wrong-candidate patches RESOLVE, so no verify-not-correct break exists (verify => correct holds for this spec).

Refinement.md audit: 5 legs, all R / A-reference / I; NO kind-3 (unexpressible-changed-op) leg. Step 1 (sizes<->np.take(mask.shape,axis)) R; step 2 (missing<->mask.sum(axis)) R; step 3 (required_minimum<->min_count) I; step 4 (prod(sizes)<->np.take(...).prod()) A-reference (the one changed quantity, modeled deeply, NOT consumed as axiom); step 5 (comparison) I+R. There is NO consumed @ContractOnly axiom (axioms region is a comment only). The single A-reference (step 4) correspondence to the real callee holds: re-ran bundle axiom_check.py (G-AX) = PASS (prod(select)==np.take(shape,axis).prod() on 13 boundary + 4000 fuzz; null_mask decision == gold numpy on 7 real-array configs). Independent broad cross-check: spec postcondition == real fixed numpy null_mask on 259,746 output positions (0 mismatches) over ndim 1-5, sizes 1-6, all non-empty proper axis subsets, min_count in [-2, block+3], real boolean masks; and prepatch single-axis semantics diverge from the spec on 23,303 of those positions (spec genuinely senses the change, G-DIFF). model<->patch correspondence is faithful and the A-reference is sound.

All >=8 attacks were fully verified and every candidate's materialized faithful patch was run through run_resolve; none breaks the spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pydata__xarray-4356 nagini bundle. The modeled function flag_too_few pins the per-position null_mask boolean of the patched _maybe_null_out: postcondition Result() == (prod(ToSeq(sizes)) - missing - required_minimum < 0). This is byte-identical arithmetic to the fixed repo expression (np.take(mask.shape, axis).prod() - mask.sum(axis) - min_count) < 0 (xarray/core/nanops.py:34, base_commit e05fddea). Mapping: sizes = np.take(mask.shape, axis) (selected reduced-axes sizes, each >0), missing = mask.sum(axis) per position, required_minimum = min_count; prod = numpy .prod over the selection. The precondition domain (len(sizes)>=1, 0<=missing<=prod(sizes)) is exactly what any real boolean-mask reduction over a non-empty axis group produces, so the spec neither over- nor under-constrains the callee's actual inputs. Model VERIFIES against the frozen spec (nagini_verify.sh exit 0, 10.8s). Differential test of the modeled flag against the REAL patched callee _maybe_null_out (behaviorally, via NaN-fill sentinel observation) over 150,013 output positions across randomized multi-axis shapes/axes/min_count (incl. negative/zero/interior/beyond-block minimums, bare-int and tuple axis spellings): ZERO disagreements. No diverging input exists; the modeled function agrees with the real repo callee on every precondition-satisfying input. Spec is faithful, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: no hard failures). Semantic review confirms NO-LEAKAGE.

Baseline: the public problem_statement already discloses the entire gold fix verbatim -- it names the file/line (xarray/core/nanops.py#L35) and states the exact edit: 'replacing mask.shape[axis] with np.take(a.shape, axis).prod()'. Thus the discriminating content of the change (count the PRODUCT of the reduced-axes sizes, allowing multi-dim reductions, rather than a single axis's size) is fully public and NOT considered leakage.

Spec view (docstring + pre/post-conditions + prod pure region + lemma) leaks nothing beyond that:
- Uses only abstract model symbols: flag_too_few, prod, sizes, missing, required_minimum, total, lemma_prod_snoc. None echo patched repo symbols (_maybe_null_out, nanops, mask, min_count, null_mask, axis); min_count is even abstracted to required_minimum.
- Postcondition 'Result() == (prod(ToSeq(sizes)) - missing - required_minimum < 0)' restates the desired behaviour (product of reduced-axes sizes minus missing < minimum), which the problem_statement already states as the intended solution -- no additional edit-localization.
- No diff markers, no patched file path/module path, no gold-patch line reproduced (mechanical L1/L2 clean), no narration terms (bug/fix/patch/etc.).
- The 'select the reduced-axes sizes then take their product' phrasing mirrors the np.take(shape,axis).prod() already named publicly in the problem statement.

The refinement.md and mapping.md are NOT part of the consumer spec view (spec_view projection), so their explicit gold-hunk quotes are out of scope for G-PANEL-3. The spec view (model.py projected) reveals no gold-edit detail beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
