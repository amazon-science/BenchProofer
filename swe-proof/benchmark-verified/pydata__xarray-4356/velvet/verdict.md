# P2 adversarial audit — pydata__xarray-4356

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_2.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -77,26 +77,11 @@
        requiredCount fillAdmissible)
   do
     -- impl-start
-    -- Always produce a decision (never reject), regardless of whether the
-    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
-    -- consulted. When the output keeps a dimension, count the collapsed elements
-    -- as the product of the reduced extents (a backward fold) and report missing
-    -- iff the present count is short. When the output is a single collapsed
-    -- value, report missing only when its representation admits a missing marker
-    -- (`fillAdmissible`) and the present count is short.
+    -- ECHO variant: compute the array-branch count directly as `prodList
+    -- reducedSizes` (same value as the backward fold, no loop). Scalar branch
+    -- unchanged. Returns exactly cellMissing on every input, so it VERIFIES.
     if remainingDimCount ≥ 1 then
-      let mut total : Nat := 1
-      let mut i := reducedSizes.length
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
-        invariant total = prodList (reducedSizes.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let s := reducedSizes[i - 1]!
-        total := s * total
-        i := i - 1
-      return Except.ok (decide (total < missingCount + requiredCount))
+      return Except.ok (decide (prodList reducedSizes < missingCount + requiredCount))
     else
       return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
     -- impl-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -77,13 +77,10 @@
        requiredCount fillAdmissible)
   do
     -- impl-start
-    -- Always produce a decision (never reject), regardless of whether the
-    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
-    -- consulted. When the output keeps a dimension, count the collapsed elements
-    -- as the product of the reduced extents (a backward fold) and report missing
-    -- iff the present count is short. When the output is a single collapsed
-    -- value, report missing only when its representation admits a missing marker
-    -- (`fillAdmissible`) and the present count is short.
+    -- ECHO variant: scalar branch expressed as an if-then-else that is
+    -- extensionally equal to `fillAdmissible && (totalSize - missingCount <
+    -- requiredCount)`; array branch keeps the verified backward fold. Returns
+    -- exactly cellMissing, so it VERIFIES.
     if remainingDimCount ≥ 1 then
       let mut total : Nat := 1
       let mut i := reducedSizes.length
@@ -98,7 +95,10 @@
         i := i - 1
       return Except.ok (decide (total < missingCount + requiredCount))
     else
-      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
+      if totalSize - missingCount < requiredCount then
+        return Except.ok fillAdmissible
+      else
+        return Except.ok false
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,25 +77,11 @@
        requiredCount fillAdmissible)
   do
     -- impl-start
-    -- Always produce a decision (never reject), regardless of whether the
-    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
-    -- consulted. When the output keeps a dimension, count the collapsed elements
-    -- as the product of the reduced extents (a backward fold) and report missing
-    -- iff the present count is short. When the output is a single collapsed
-    -- value, report missing only when its representation admits a missing marker
-    -- (`fillAdmissible`) and the present count is short.
+    -- WRONG (partial-domain): array branch counts a SINGLE reduced extent
+    -- (headD) instead of the product over all of them. Correct only when at
+    -- most one axis is reduced; undercounts for >=2, so must FAIL verify.
     if remainingDimCount ≥ 1 then
-      let mut total : Nat := 1
-      let mut i := reducedSizes.length
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
-        invariant total = prodList (reducedSizes.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let s := reducedSizes[i - 1]!
-        total := s * total
-        i := i - 1
+      let total : Nat := reducedSizes.headD 1
       return Except.ok (decide (total < missingCount + requiredCount))
     else
       return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,26 +77,10 @@
        requiredCount fillAdmissible)
   do
     -- impl-start
-    -- Always produce a decision (never reject), regardless of whether the
-    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
-    -- consulted. When the output keeps a dimension, count the collapsed elements
-    -- as the product of the reduced extents (a backward fold) and report missing
-    -- iff the present count is short. When the output is a single collapsed
-    -- value, report missing only when its representation admits a missing marker
-    -- (`fillAdmissible`) and the present count is short.
+    -- WRONG (boundary/off-by-one): array branch uses `<=` in place of `<`,
+    -- flagging missing one requirement-value too eagerly. Must FAIL verify.
     if remainingDimCount ≥ 1 then
-      let mut total : Nat := 1
-      let mut i := reducedSizes.length
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
-        invariant total = prodList (reducedSizes.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let s := reducedSizes[i - 1]!
-        total := s * total
-        i := i - 1
-      return Except.ok (decide (total < missingCount + requiredCount))
+      return Except.ok (decide (prodList reducedSizes ≤ missingCount + requiredCount))
     else
       return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,26 +77,13 @@
        requiredCount fillAdmissible)
   do
     -- impl-start
-    -- Always produce a decision (never reject), regardless of whether the
-    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
-    -- consulted. When the output keeps a dimension, count the collapsed elements
-    -- as the product of the reduced extents (a backward fold) and report missing
-    -- iff the present count is short. When the output is a single collapsed
-    -- value, report missing only when its representation admits a missing marker
-    -- (`fillAdmissible`) and the present count is short.
-    if remainingDimCount ≥ 1 then
-      let mut total : Nat := 1
-      let mut i := reducedSizes.length
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
-        invariant total = prodList (reducedSizes.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let s := reducedSizes[i - 1]!
-        total := s * total
-        i := i - 1
-      return Except.ok (decide (total < missingCount + requiredCount))
+    -- WRONG (control-flow/effect): reinstates the removed pre-patch ValueError
+    -- for a sequence-named (multi-dim) reduction. The frozen ensures pins
+    -- `out = Except.ok (...)` for EVERY input, so this must FAIL verify.
+    if axisWasSequence then
+      return Except.error ()
+    else if remainingDimCount ≥ 1 then
+      return Except.ok (decide (prodList reducedSizes < missingCount + requiredCount))
     else
       return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,28 +77,14 @@
        requiredCount fillAdmissible)
   do
     -- impl-start
-    -- Always produce a decision (never reject), regardless of whether the
-    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
-    -- consulted. When the output keeps a dimension, count the collapsed elements
-    -- as the product of the reduced extents (a backward fold) and report missing
-    -- iff the present count is short. When the output is a single collapsed
-    -- value, report missing only when its representation admits a missing marker
-    -- (`fillAdmissible`) and the present count is short.
+    -- WRONG (ungrounded-oracle echo): scalar branch DROPS the fillAdmissible
+    -- dtype guard, always deciding on the count. Differs from cellMissing when
+    -- fillAdmissible = false (a NAT-type result), so must FAIL verify — the
+    -- spec pins the guard even though the F2P dtypes all have it true.
     if remainingDimCount ≥ 1 then
-      let mut total : Nat := 1
-      let mut i := reducedSizes.length
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
-        invariant total = prodList (reducedSizes.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let s := reducedSizes[i - 1]!
-        total := s * total
-        i := i - 1
-      return Except.ok (decide (total < missingCount + requiredCount))
+      return Except.ok (decide (prodList reducedSizes < missingCount + requiredCount))
     else
-      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
+      return Except.ok (decide (totalSize - missingCount < requiredCount))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,28 +77,13 @@
        requiredCount fillAdmissible)
   do
     -- impl-start
-    -- Always produce a decision (never reject), regardless of whether the
-    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
-    -- consulted. When the output keeps a dimension, count the collapsed elements
-    -- as the product of the reduced extents (a backward fold) and report missing
-    -- iff the present count is short. When the output is a single collapsed
-    -- value, report missing only when its representation admits a missing marker
-    -- (`fillAdmissible`) and the present count is short.
+    -- WRONG (branch-selector): applies the scalar (dtype-guarded) decision on
+    -- the ARRAY branch and the product decision on the scalar branch — the two
+    -- branch bodies swapped. Disagrees with cellMissing, so must FAIL verify.
     if remainingDimCount ≥ 1 then
-      let mut total : Nat := 1
-      let mut i := reducedSizes.length
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
-        invariant total = prodList (reducedSizes.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        let s := reducedSizes[i - 1]!
-        total := s * total
-        i := i - 1
-      return Except.ok (decide (total < missingCount + requiredCount))
+      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
     else
-      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
+      return Except.ok (decide (prodList reducedSizes < missingCount + requiredCount))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms: the only modeled callee is the element-count product,
-- which is modeled deeply by `prodList` below (an A-reference validated against
-- the real array reduction by axiom_check.py / G-AX), not axiomatized.
-- axioms-end

-- pure-start
/- The number of elements collapsed into one output cell when a reduction runs
   over a collection of dimensions: the product of the per-dimension extents.
   Front-recursive (one unfold per loop step — the fold pattern, plan §5.4); the
   empty product is 1 (a reduction over no dimensions touches a single cell). -/
def prodList : List Nat → Nat
  | []      => 1
  | x :: xs => x * prodList xs

@[grind] lemma prodList_nil : prodList [] = 1 := rfl
@[grind] lemma prodList_cons (x : Nat) (xs : List Nat) :
    prodList (x :: xs) = x * prodList xs := rfl

/- The missing-decision for one output cell, as a function of which shape the
   output takes. When the output still has at least one dimension
   (`remainingDimCount ≥ 1`) each cell aggregates the product of the collapsed
   extents, and is missing exactly when the present count falls short of the
   requirement. When the whole input collapses to a single value
   (`remainingDimCount = 0`) the cell aggregates every element, and is reported
   missing only when the value's representation admits a missing marker
   (`fillAdmissible`) AND the present count falls short — for representations
   that cannot carry a missing marker the cell is never reported missing
   regardless of the requirement. -/
def cellMissing
    (remainingDimCount : Nat) (reducedSizes : List Nat) (totalSize : Nat)
    (missingCount : Nat) (requiredCount : Nat) (fillAdmissible : Bool) : Bool :=
  if remainingDimCount ≥ 1 then
    decide (prodList reducedSizes < missingCount + requiredCount)
  else
    fillAdmissible && decide (totalSize - missingCount < requiredCount)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for one cell of the output, whether its aggregate must be reported
   as missing — for a reduction that collapses a collection of dimensions, no
   matter how many. `reducedSizes` are the extents of the collapsed dimensions
   and `missingCount` of those collapsed elements were missing; the caller
   demands at least `requiredCount` present ones. `remainingDimCount` is how many
   dimensions the output keeps: when it is positive the output is a shaped
   collection whose per-cell aggregate spans the product of the collapsed
   extents; when it is zero the whole input has collapsed to a single value that
   spans `totalSize` elements, and that single value is only ever flagged missing
   when its representation admits a missing marker (`fillAdmissible`). The
   decision is produced for EVERY reduction, including one whose collapsed
   dimensions were named as a sequence (`axisWasSequence`): collapsing several
   dimensions is handled exactly like collapsing one, so the post-state pins
   `out` to a produced decision independently of that flag (never a rejection).
   There is NO precondition: the decision is pinned for EVERY `requiredCount`,
   including a requirement of zero (a present count — at most the collapsed
   element count — can then never fall short, so nothing real is flagged). -/
method reductionMissingDecision
    (reducedSizes : List Nat) (missingCount : Nat) (requiredCount : Nat)
    (remainingDimCount : Nat) (totalSize : Nat)
    (fillAdmissible : Bool) (axisWasSequence : Bool)
    return (out : Except Unit Bool)
  ensures out = Except.ok
    (cellMissing remainingDimCount reducedSizes totalSize missingCount
       requiredCount fillAdmissible)
  do
    -- impl-start
    -- Always produce a decision (never reject), regardless of whether the
    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
    -- consulted. When the output keeps a dimension, count the collapsed elements
    -- as the product of the reduced extents (a backward fold) and report missing
    -- iff the present count is short. When the output is a single collapsed
    -- value, report missing only when its representation admits a missing marker
    -- (`fillAdmissible`) and the present count is short.
    if remainingDimCount ≥ 1 then
      let mut total : Nat := 1
      let mut i := reducedSizes.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
        invariant total = prodList (reducedSizes.drop i)
        done_with i = 0
        decreasing i
      do
        let s := reducedSizes[i - 1]!
        total := s * total
        i := i - 1
      return Except.ok (decide (total < missingCount + requiredCount))
    else
      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `prodList` peels one factor. The single goal
   `loom_solve` leaves for the loop body. -/
lemma prodList_drop_step (xs : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    prodList (xs.drop (i - 1)) = xs[i - 1]! * prodList (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, prodList_cons]

prove_correct reductionMissingDecision by
  loom_solve <;>
    first
      | (rw [prodList_drop_step reducedSizes i (by omega) (by omega)]; simp_all)
      | (simp only [cellMissing]; split <;> simp_all)
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (A-leg) AUDIT — VERDICT SOUND.

Spec shape: `ensures out = Except.ok (cellMissing remainingDimCount reducedSizes totalSize missingCount requiredCount fillAdmissible)` — the output is FULLY PINNED with NO precondition, under loom total-correctness. Consequence: every verifying impl must compute exactly `cellMissing`, i.e. is behaviorally identical to gold on the modeled domain. same_spec=True confirmed for all 8 files (positive_control + 7 attacks); impl region is the ONLY edit.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run concurrently ≤4):
  positive_control.lean -> exit 0 (verifies)
  atk_1 (ECHO: direct `prodList reducedSizes`, no loop) -> exit 0 VERIFIES
  atk_2 (ECHO: scalar branch rewritten as if-then-else extensionally = fillAdmissible && (...)) -> exit 0 VERIFIES
  atk_3 (partial-domain: array-branch counts a SINGLE reduced extent `reducedSizes.headD 1`; = Solution_prepatch_2) -> exit 1 REJECTED. Goal: `headD 1 < m+r ↔ prodList < m+r`.
  atk_4 (boundary/off-by-one: `≤` for `<`) -> exit 1 REJECTED. Goal: `prodList ≤ m+r ↔ prodList < m+r`.
  atk_5 (control-flow-effect: reinstates pre-patch ValueError on axisWasSequence; = Solution_prepatch / the prepatch bug) -> exit 1 REJECTED. Goal: `False`. (prepatch_reproduced=true)
  atk_6 (ungrounded-oracle echo: drops the fillAdmissible dtype guard on scalar branch) -> exit 1 REJECTED. Goal: `totalSize - missingCount < requiredCount → fillAdmissible = true`.
  atk_7 (branch-selector swap: array/scalar bodies swapped) -> exit 1 REJECTED (branch bodies unequal).
All 5 rejections fail on a GENUINE semantic inequivalence to cellMissing (not a tactic/syntax artifact), confirming the spec discriminates behaviorally-distinct impls.

RESOLVE ON VERIFYING ATTACKS (protocol step 2): atk_1 and atk_2 each compute exactly cellMissing (= gold formula), so each faithful refined patch is the gold hunk (raise removed; `mask.shape[axis]` -> `np.take(mask.shape, axis).prod()`) — byte-identical for both. Ran through official harness: run_resolve('pydata__xarray-4356', <gold hunk>, timeout=1800, retries=1) -> RESOLVED=True COMPLETED=True attempts=1 flaky=False. So no verifying wrong-impl's faithful patch FAILS to resolve => verify does NOT ⇏ correct here.

A-LEG / refinement.md audit: legs A1-A5 = R (type/branch/behaviour-removal refinements), A6 = A-reference + I (deep model prodList == np.take(shape,axis).prod(), NOT a consumed axiom), A7/A8 = R + I. NO kind-3 legs; the one genuinely-changed op (single-size -> product count) is modeled DEEPLY by prodList, not axiomatized; axioms region empty. A-reference correspondence validated: axiom_check.py exit 0 (14 boundary + 20000 fuzz reduced-axis configs, empty product = 1). conformance_check.py exists (R/I leg, G-CONF scope, mechanically covered by G-CONF). mapping.md binds every symbol to _maybe_null_out @ base e05fddea; the A6 callee (numpy .prod() on np.take gather) is real.

CONCLUSION: verifying attacks are gold-equivalent echoes whose faithful patches resolve (per fixed G-PANEL-1/G-EQ echo policy, an echo that resolves is NOT a weakness); genuinely-wrong impls all fail verify. Spec is refinement-faithful. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_1.lean`, `atk_2.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms: the only modeled callee is the element-count product,
-- which is modeled deeply by `prodList` below (an A-reference validated against
-- the real array reduction by axiom_check.py / G-AX), not axiomatized.
-- axioms-end

-- pure-start
/- The number of elements collapsed into one output cell when a reduction runs
   over a collection of dimensions: the product of the per-dimension extents.
   Front-recursive (one unfold per loop step — the fold pattern, plan §5.4); the
   empty product is 1 (a reduction over no dimensions touches a single cell). -/
def prodList : List Nat → Nat
  | []      => 1
  | x :: xs => x * prodList xs

@[grind] lemma prodList_nil : prodList [] = 1 := rfl
@[grind] lemma prodList_cons (x : Nat) (xs : List Nat) :
    prodList (x :: xs) = x * prodList xs := rfl

/- The missing-decision for one output cell, as a function of which shape the
   output takes. When the output still has at least one dimension
   (`remainingDimCount ≥ 1`) each cell aggregates the product of the collapsed
   extents, and is missing exactly when the present count falls short of the
   requirement. When the whole input collapses to a single value
   (`remainingDimCount = 0`) the cell aggregates every element, and is reported
   missing only when the value's representation admits a missing marker
   (`fillAdmissible`) AND the present count falls short — for representations
   that cannot carry a missing marker the cell is never reported missing
   regardless of the requirement. -/
def cellMissing
    (remainingDimCount : Nat) (reducedSizes : List Nat) (totalSize : Nat)
    (missingCount : Nat) (requiredCount : Nat) (fillAdmissible : Bool) : Bool :=
  if remainingDimCount ≥ 1 then
    decide (prodList reducedSizes < missingCount + requiredCount)
  else
    fillAdmissible && decide (totalSize - missingCount < requiredCount)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for one cell of the output, whether its aggregate must be reported
   as missing — for a reduction that collapses a collection of dimensions, no
   matter how many. `reducedSizes` are the extents of the collapsed dimensions
   and `missingCount` of those collapsed elements were missing; the caller
   demands at least `requiredCount` present ones. `remainingDimCount` is how many
   dimensions the output keeps: when it is positive the output is a shaped
   collection whose per-cell aggregate spans the product of the collapsed
   extents; when it is zero the whole input has collapsed to a single value that
   spans `totalSize` elements, and that single value is only ever flagged missing
   when its representation admits a missing marker (`fillAdmissible`). The
   decision is produced for EVERY reduction, including one whose collapsed
   dimensions were named as a sequence (`axisWasSequence`): collapsing several
   dimensions is handled exactly like collapsing one, so the post-state pins
   `out` to a produced decision independently of that flag (never a rejection).
   There is NO precondition: the decision is pinned for EVERY `requiredCount`,
   including a requirement of zero (a present count — at most the collapsed
   element count — can then never fall short, so nothing real is flagged). -/
method reductionMissingDecision
    (reducedSizes : List Nat) (missingCount : Nat) (requiredCount : Nat)
    (remainingDimCount : Nat) (totalSize : Nat)
    (fillAdmissible : Bool) (axisWasSequence : Bool)
    return (out : Except Unit Bool)
  ensures out = Except.ok
    (cellMissing remainingDimCount reducedSizes totalSize missingCount
       requiredCount fillAdmissible)
  do
    -- impl-start
    -- Always produce a decision (never reject), regardless of whether the
    -- collapsed dimensions were named as a sequence: `axisWasSequence` is not
    -- consulted. When the output keeps a dimension, count the collapsed elements
    -- as the product of the reduced extents (a backward fold) and report missing
    -- iff the present count is short. When the output is a single collapsed
    -- value, report missing only when its representation admits a missing marker
    -- (`fillAdmissible`) and the present count is short.
    if remainingDimCount ≥ 1 then
      let mut total : Nat := 1
      let mut i := reducedSizes.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ reducedSizes.length
        invariant total = prodList (reducedSizes.drop i)
        done_with i = 0
        decreasing i
      do
        let s := reducedSizes[i - 1]!
        total := s * total
        i := i - 1
      return Except.ok (decide (total < missingCount + requiredCount))
    else
      return Except.ok (fillAdmissible && decide (totalSize - missingCount < requiredCount))
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `prodList` peels one factor. The single goal
   `loom_solve` leaves for the loop body. -/
lemma prodList_drop_step (xs : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    prodList (xs.drop (i - 1)) = xs[i - 1]! * prodList (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, prodList_cons]

prove_correct reductionMissingDecision by
  loom_solve <;>
    first
      | (rw [prodList_drop_step reducedSizes i (by omega) (by omega)]; simp_all)
      | (simp only [cellMissing]; split <;> simp_all)
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (A-leg) AUDIT — VERDICT SOUND.

Spec shape: `ensures out = Except.ok (cellMissing remainingDimCount reducedSizes totalSize missingCount requiredCount fillAdmissible)` — the output is FULLY PINNED with NO precondition, under loom total-correctness. Consequence: every verifying impl must compute exactly `cellMissing`, i.e. is behaviorally identical to gold on the modeled domain. same_spec=True confirmed for all 8 files (positive_control + 7 attacks); impl region is the ONLY edit.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run concurrently ≤4):
  positive_control.lean -> exit 0 (verifies)
  atk_1 (ECHO: direct `prodList reducedSizes`, no loop) -> exit 0 VERIFIES
  atk_2 (ECHO: scalar branch rewritten as if-then-else extensionally = fillAdmissible && (...)) -> exit 0 VERIFIES
  atk_3 (partial-domain: array-branch counts a SINGLE reduced extent `reducedSizes.headD 1`; = Solution_prepatch_2) -> exit 1 REJECTED. Goal: `headD 1 < m+r ↔ prodList < m+r`.
  atk_4 (boundary/off-by-one: `≤` for `<`) -> exit 1 REJECTED. Goal: `prodList ≤ m+r ↔ prodList < m+r`.
  atk_5 (control-flow-effect: reinstates pre-patch ValueError on axisWasSequence; = Solution_prepatch / the prepatch bug) -> exit 1 REJECTED. Goal: `False`. (prepatch_reproduced=true)
  atk_6 (ungrounded-oracle echo: drops the fillAdmissible dtype guard on scalar branch) -> exit 1 REJECTED. Goal: `totalSize - missingCount < requiredCount → fillAdmissible = true`.
  atk_7 (branch-selector swap: array/scalar bodies swapped) -> exit 1 REJECTED (branch bodies unequal).
All 5 rejections fail on a GENUINE semantic inequivalence to cellMissing (not a tactic/syntax artifact), confirming the spec discriminates behaviorally-distinct impls.

RESOLVE ON VERIFYING ATTACKS (protocol step 2): atk_1 and atk_2 each compute exactly cellMissing (= gold formula), so each faithful refined patch is the gold hunk (raise removed; `mask.shape[axis]` -> `np.take(mask.shape, axis).prod()`) — byte-identical for both. Ran through official harness: run_resolve('pydata__xarray-4356', <gold hunk>, timeout=1800, retries=1) -> RESOLVED=True COMPLETED=True attempts=1 flaky=False. So no verifying wrong-impl's faithful patch FAILS to resolve => verify does NOT ⇏ correct here.

A-LEG / refinement.md audit: legs A1-A5 = R (type/branch/behaviour-removal refinements), A6 = A-reference + I (deep model prodList == np.take(shape,axis).prod(), NOT a consumed axiom), A7/A8 = R + I. NO kind-3 legs; the one genuinely-changed op (single-size -> product count) is modeled DEEPLY by prodList, not axiomatized; axioms region empty. A-reference correspondence validated: axiom_check.py exit 0 (14 boundary + 20000 fuzz reduced-axis configs, empty product = 1). conformance_check.py exists (R/I leg, G-CONF scope, mechanically covered by G-CONF). mapping.md binds every symbol to _maybe_null_out @ base e05fddea; the A6 callee (numpy .prod() on np.take gather) is real.

CONCLUSION: verifying attacks are gold-equivalent echoes whose faithful patches resolve (per fixed G-PANEL-1/G-EQ echo policy, an echo that resolves is NOT a weakness); genuinely-wrong impls all fail verify. Spec is refinement-faithful. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack UNSUCCESSFUL — the spec faithfully models the real gold-patched xarray.core.nanops._maybe_null_out; no diverging input found.

Setup verified:
- Spec regions byte-identical (swebench_unified.markers.same_spec = True) between Solution.lean and both Solution_prepatch*.lean → spec is genuinely frozen.
- Solution.lean verifies (lean_verify exit 0). Both prepatch variants FAIL to verify (exit 1): Solution_prepatch reinstates the deleted multi-dim `raise ValueError` (Except.error on axisWasSequence) and Solution_prepatch_2 reproduces the single-axis count → each fails the frozen `ensures`. So the spec is discriminating, not vacuous.
- Compared real repo (pre) vs (gold): patch removes `if hasattr(axis,'__len__'): raise ValueError` and changes `mask.shape[axis]` → `np.take(mask.shape, axis).prod()`. Callers nansum/nanprod short-circuit when min_count is None (nanops.py:110,180), so min_count is a nonneg int whenever the code runs.

Differential testing (independent of the pinned seed 4356): reconstructed the exact post-patch _maybe_null_out and drove it against the model cellMissing (prodList + dtype-guarded scalar branch), reading NaN per output cell as the oracle:
- >1,000,000 inputs across TWO runs (seeds 999, 7, 31 — different from the shipped seed), covering BOTH branches: array branch (ndim>=1, strict-subset axes, product-of-extents count) and scalar/all-dims branch (ndim==0, the F2P scenario).
- dtypes float64, float32, int32, int64 — exercising the numpy NaT quirk (np.dtype('float64') in dtypes.NAT_TYPES == True → fillAdmissible False → never nulls out; float32/int → live null-out). Confirmed NAT_TYPES = (datetime64('NaT'), timedelta64('NaT')).
- min_count drawn from 0 upward (the previously-unpinned requiredCount=0 slice).
- Result: 0 disagreements in every run.

The modeling is exact: array branch `prodList reducedSizes < missingCount + requiredCount` ⇔ `(np.take(shape,axis).prod() - mask.sum(axis) - min_count) < 0` on the bridge domain missing ≤ prod; scalar branch `fillAdmissible && (totalSize - missingCount < requiredCount)` ⇔ the dtype-guarded `mask.size - mask.sum() < min_count`; raise-removal modeled by `out` always Except.ok independent of axisWasSequence. Under total-correctness semantics the loop carries a `decreasing` measure so no vacuous-divergence hole. The spec is neither too strong (no false missing-detection on float64/NAT scalars) nor drifted (matches real callee on all tested inputs). No counterexample exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction audit of the velvet spec view for pydata__xarray-4356.

Mechanical + semantic both clean:
- leakage.screen() over the projected spec view (impl elided to 'implementation elided — supplied by the consumer', proof elided): 0 hard failures, 0 warnings.
- same_spec(Solution.lean, Solution_prepatch.lean) = True and same_spec(Solution.lean, Solution_prepatch_2.lean) = True — spec region byte-identical across all three, so the pre/post pair cannot betray the edit via a spec diff.

Spec view discloses nothing beyond the PUBLIC problem_statement:
- No repo symbols leak: the gold patch touches `_maybe_null_out` in `xarray/core/nanops.py`, replacing `mask.shape[axis]` with `np.take(mask.shape, axis).prod()` and deleting the multi-dim `raise ValueError`. None of `_maybe_null_out`, `nanops`, `mask`, `min_count`, `np.take`, `NAT_TYPES` appear in the view. The spec uses fully abstracted carriers (`reductionMissingDecision`, `prodList`, `cellMissing`, `reducedSizes`, `missingCount`, `requiredCount`, `remainingDimCount`, `fillAdmissible`, `axisWasSequence`).
- No diff markers, no patched file/module path, no narration vocabulary (bug/fix/patch/pre-patch/regression/…).
- The gold edit is ALREADY fully public in problem_statement: it names the exact line to change and the substitution `mask.shape[axis]` -> `np.take(a.shape, axis).prod()`, and the deleted guard's verbatim message 'min_count is not available for reduction with more than one dimensions.' Hence the spec's 'product of the reduced-axis extents' modeling and its 'produce a decision for EVERY reduction, never a rejection, independent of axisWasSequence' content reconstruct only what the public task already states — no beyond-problem_statement disclosure.
- The scalar-branch `fillAdmissible` dtype nuance (float64-in-NAT_TYPES quirk) is NOT part of the gold patch (the patch modifies only the array branch), so it is background repo behavior, not the gold edit; modeling it cannot leak the edit.

Judged against solver-visible problem_statement only (hints_text excluded); everything the spec reveals about the gold edit is contained in the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
