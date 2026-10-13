# P2 adversarial audit — sympy__sympy-21612

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 11 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verifying wrong impl exists to exhibit. All 11 same-spec wrong impls were REJECTED by lean_verify.sh (rc=1, genuine 'unsolved goals' on the ensures obligation, not tactic weakness), so protocol step 2 (materialize + resolve the faithful patch of a VERIFYING wrong impl) has an empty obligation set. Structural reason: the axioms region declares ZERO `axiom`s (only `inductive DenomShape` + `structure DenomFactor`), there is NO `requires`, and the postcondition is the unconditional pointwise equality `out = renderDenomFactors slots` against a TOTAL, fully concrete deep model. Any verifying impl is therefore extensionally equal to renderDenomFactors on every input — no partial-domain, boundary, control-flow or ungrounded-oracle wedge is available. Residual goals confirm real semantic gaps, e.g. atk_5 left `result_1 = applyWraps (slotTexts slots) (bracketTargets slots slots)` with only `applyWraps ... (bracketTargets slots slots).eraseDups = result_1` in hand; atk_1 (prepatch) left the same goal with the product-only filter. Since the wedge must instead be model-vs-patch, I materialized the deep model VERBATIM as the real function (faithful_model.diff: own isReciprocal flags + transliterated needsBrackets/firstSlotWithKey/cumulative wrap replacing the real pow_paren/b.index block) and it RESOLVED — so the model↔patch correspondence is behaviourally sound on the graded tests, in the strongest form the protocol asks for.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,8 +151,13 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 1 (prepatch bug): the gate admits only `product` inners, so a
+    -- reciprocal whose inner expression is a POWER raises no request.
     let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
+    let targets : List Nat :=
+      (slots.filter (fun f =>
+          f.isReciprocal && (f.components != 1) && (f.shape == DenomShape.product))).map
+        (fun f => firstSlotWithKey f.innerKey slots)
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
     while k < targets.length
@@ -181,6 +186,9 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
+  · rw [applyWraps_take_step (slotTexts slots)
+      ((slots.filter (fun f =>
+          f.isReciprocal && (f.components != 1) && (f.shape == DenomShape.product))).map
+        (fun f => firstSlotWithKey f.innerKey slots)) k (by omega)]
     simp_all
-  · simp_all [renderDenomFactors]
+  · simp_all [renderDenomFactors, bracketTargets, needsBrackets, shapeIsCompound]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,19 +151,10 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
-    let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
-    let mut result : List (List Char) := texts
-    let mut k : Nat := 0
-    while k < targets.length
-      invariant k ≤ targets.length
-      invariant result = applyWraps texts (targets.take k)
-      done_with k = targets.length
-      decreasing targets.length - k
-    do
-      result := wrapAt result targets[k]!
-      k := k + 1
-    return result
+    -- ATTACK 2 (partial-domain collapse): satisfy NO bracket request; return the
+    -- slots' bare texts. Agrees with the model on every slot list that raises no
+    -- request (a large sub-domain), diverges the moment one is raised.
+    return slotTexts slots
     -- impl-end
 
 /- The forward step: taking one more bracket request appends it at the end, so
@@ -181,6 +172,5 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
-    simp_all
-  · simp_all [renderDenomFactors]
+  simp_all [renderDenomFactors, bracketTargets, needsBrackets, shapeIsCompound,
+            applyWraps, slotTexts]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,8 +151,15 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 3 (boundary): the request gate reads `components > 1` instead of
+    -- `components != 1`. Identical on every slot with components >= 1; diverges
+    -- exactly at the components = 0 boundary (a compound-shaped slot with no
+    -- top-level components).
     let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
+    let targets : List Nat :=
+      (slots.filter (fun f =>
+          f.isReciprocal && (f.components > 1) && shapeIsCompound f.shape)).map
+        (fun f => firstSlotWithKey f.innerKey slots)
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
     while k < targets.length
@@ -181,6 +188,9 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
+  · rw [applyWraps_take_step (slotTexts slots)
+      ((slots.filter (fun f =>
+          f.isReciprocal && (f.components > 1) && shapeIsCompound f.shape)).map
+        (fun f => firstSlotWithKey f.innerKey slots)) k (by omega)]
     simp_all
-  · simp_all [renderDenomFactors]
+  · simp_all [renderDenomFactors, bracketTargets, needsBrackets, shapeIsCompound]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,8 +151,15 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 4 (idealized per-slot resolution — the counterexample refinement.md
+    -- §C names): wrap each raising slot at its OWN position instead of at the
+    -- position its inner expression is FOUND at. Internally consistent and
+    -- agrees with the model on every slot list whose inners are pairwise
+    -- distinct; diverges on the equal-inner class, predicting
+    -- x/(((y*z))*((y*z))) where the real printer gives x/((((y*z)))*(y*z)).
     let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
+    let targets : List Nat :=
+      (List.range slots.length).filter (fun i => needsBrackets slots[i]!)
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
     while k < targets.length
@@ -181,6 +188,7 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
+  · rw [applyWraps_take_step (slotTexts slots)
+      ((List.range slots.length).filter (fun i => needsBrackets slots[i]!)) k (by omega)]
     simp_all
-  · simp_all [renderDenomFactors]
+  · simp_all [renderDenomFactors, bracketTargets, needsBrackets, shapeIsCompound]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,8 +151,13 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 5 (control-flow effect — dropped cumulative application): collapse
+    -- co-targeted requests so a position is wrapped at most ONCE. Agrees with the
+    -- model whenever no two raising slots share an inner expression; on the
+    -- equal-inner class it under-wraps (one bracket pair where the real
+    -- cumulative b_str loop lays down two).
     let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
+    let targets : List Nat := (bracketTargets slots slots).eraseDups
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
     while k < targets.length
@@ -181,6 +186,7 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
+  · rw [applyWraps_take_step (slotTexts slots)
+      ((bracketTargets slots slots).eraseDups) k (by omega)]
     simp_all
   · simp_all [renderDenomFactors]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,14 +151,17 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 6 (control-flow off-by-one): the fold stops one request short, so the
+    -- LAST bracket request is never satisfied. Agrees with the model on every slot
+    -- list that raises no request; diverges as soon as one is raised.
     let texts : List (List Char) := slotTexts slots
     let targets : List Nat := bracketTargets slots slots
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
-    while k < targets.length
+    while k + 1 < targets.length
       invariant k ≤ targets.length
       invariant result = applyWraps texts (targets.take k)
-      done_with k = targets.length
+      done_with k + 1 ≥ targets.length
       decreasing targets.length - k
     do
       result := wrapAt result targets[k]!
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,8 +151,14 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 7 (over-widening in the direction of the patch): treat EVERY inner
+    -- shape as compound, so a reciprocal of a simple atom also raises a request.
+    -- This over-brackets (x/(y) for what must print x/y) — the failure mode a spec
+    -- that only pinned "power now brackets" would not exclude.
     let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
+    let targets : List Nat :=
+      (slots.filter (fun f => f.isReciprocal && (f.components != 1))).map
+        (fun f => firstSlotWithKey f.innerKey slots)
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
     while k < targets.length
@@ -181,6 +187,8 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
+  · rw [applyWraps_take_step (slotTexts slots)
+      ((slots.filter (fun f => f.isReciprocal && (f.components != 1))).map
+        (fun f => firstSlotWithKey f.innerKey slots)) k (by omega)]
     simp_all
-  · simp_all [renderDenomFactors]
+  · simp_all [renderDenomFactors, bracketTargets, needsBrackets, shapeIsCompound]
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,8 +151,15 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 8 (branch-context dropped): ignore `isReciprocal`, so an apow /
+    -- Rational denominator slot — never appended to pow_paren in the real
+    -- function — also raises a bracket request. Agrees with the model on every
+    -- all-reciprocal slot list; diverges once a non-reciprocal compound slot
+    -- appears.
     let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
+    let targets : List Nat :=
+      (slots.filter (fun f => (f.components != 1) && shapeIsCompound f.shape)).map
+        (fun f => firstSlotWithKey f.innerKey slots)
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
     while k < targets.length
@@ -181,6 +188,8 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
+  · rw [applyWraps_take_step (slotTexts slots)
+      ((slots.filter (fun f => (f.components != 1) && shapeIsCompound f.shape)).map
+        (fun f => firstSlotWithKey f.innerKey slots)) k (by omega)]
     simp_all
-  · simp_all [renderDenomFactors]
+  · simp_all [renderDenomFactors, bracketTargets, needsBrackets, shapeIsCompound]
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,8 +151,16 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 9 (wrong resolution rule — last instead of first occurrence): resolve
+    -- each request to the LAST slot holding the inner expression, i.e. rindex
+    -- rather than b.index. Agrees with the model whenever inners are pairwise
+    -- distinct; on the equal-inner class it wraps the LATER slot twice and leaves
+    -- the earlier bare — the mirror image of the real function.
     let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
+    let n : Nat := slots.length
+    let targets : List Nat :=
+      (slots.filter (fun f => needsBrackets f)).map
+        (fun f => n - 1 - firstSlotWithKey f.innerKey slots.reverse)
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
     while k < targets.length
@@ -181,6 +189,8 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
+  · rw [applyWraps_take_step (slotTexts slots)
+      ((slots.filter (fun f => needsBrackets f)).map
+        (fun f => slots.length - 1 - firstSlotWithKey f.innerKey slots.reverse)) k (by omega)]
     simp_all
-  · simp_all [renderDenomFactors]
+  · simp_all [renderDenomFactors, bracketTargets]
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,8 +151,12 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
+    -- ATTACK 10 (control-flow effect — reversed application order): satisfy the
+    -- bracket requests from last to first instead of in slot order. Same multiset
+    -- of targets, but the cumulative b_str fold is order-sensitive, so nested
+    -- wrappings come out in the wrong order once two requests interact.
     let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
+    let targets : List Nat := (bracketTargets slots slots).reverse
     let mut result : List (List Char) := texts
     let mut k : Nat := 0
     while k < targets.length
@@ -181,6 +185,6 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
+  · rw [applyWraps_take_step (slotTexts slots) ((bracketTargets slots slots).reverse) k (by omega)]
     simp_all
   · simp_all [renderDenomFactors]
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,19 +151,12 @@
   ensures out = renderDenomFactors slots
   do
     -- impl-start
-    let texts : List (List Char) := slotTexts slots
-    let targets : List Nat := bracketTargets slots slots
-    let mut result : List (List Char) := texts
-    let mut k : Nat := 0
-    while k < targets.length
-      invariant k ≤ targets.length
-      invariant result = applyWraps texts (targets.take k)
-      done_with k = targets.length
-      decreasing targets.length - k
-    do
-      result := wrapAt result targets[k]!
-      k := k + 1
-    return result
+    -- ATTACK 11 (ungrounded-oracle echo): call the spec's own deep model, but on a
+    -- slot list with the non-reciprocal slots stripped out. This *looks* like it
+    -- echoes the oracle and is correct on all-reciprocal inputs, but dropping the
+    -- apow / Rational slots shifts every position b.index resolves to, so both the
+    -- texts and the targets come out wrong once a non-reciprocal slot is present.
+    return renderDenomFactors (slots.filter (fun f => f.isReciprocal))
     -- impl-end
 
 /- The forward step: taking one more bracket request appends it at the end, so
@@ -181,6 +174,4 @@
 
 prove_correct bracketDenomFactors by
   loom_solve
-  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
-    simp_all
-  · simp_all [renderDenomFactors]
+  simp_all [renderDenomFactors]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The structural classification of the inner expression sitting underneath a
   denominator slot. When a quotient is rendered to its textual form, each
   denominator slot holds some inner expression; that inner expression has one of
   three shapes:

     • `product` — it is a product of two or more factors;
     • `power`   — it is itself a power (an exponentiation);
     • `simple`  — anything else (a single atom, a number, …).

   This is an OBSERVATION of an unchanged sub-object, not a computed value: the
   renderer already knows, for any sub-expression, both its rendered text and its
   top-level shape. Provenance + the executable soundness check that these
   observations match reality: mapping.md §3 / axiom_check.py (G-AX). -/
inductive DenomShape where
  | product
  | power
  | simple
deriving DecidableEq, Inhabited, Repr

/- One slot of the rendered denominator, described by the observations the
   bracketing decision needs:
     • `rendered`     — the already-rendered text of the slot's inner expression
                        (the result of the renderer's standard sub-rendering, an
                        unchanged callee taken here as a given value);
     • `shape`        — the inner expression's top-level shape (above);
     • `components`   — the number of top-level components of the inner
                        expression (e.g. the factor count of a product);
     • `isReciprocal` — whether this slot arose as the reciprocal of its inner
                        expression. Only reciprocal slots are ever considered for
                        protective brackets; the other denominator slots are
                        assembled from their text unchanged.
     • `innerKey`     — an identity code for the slot's inner expression: two
                        slots carry the SAME `innerKey` exactly when they hold
                        equal inner expressions. This is what lets a bracket
                        request be located by the expression it names rather than
                        by the position it was raised from. -/
structure DenomFactor where
  rendered     : List Char
  shape        : DenomShape
  components   : Nat
  isReciprocal : Bool
  innerKey     : Nat
deriving Inhabited
-- axioms-end

-- pure-start
/- A shape is *compound* when the inner expression is built from sub-parts that
   could be torn apart by a surrounding division — a product or a power. A simple
   atom is never compound. -/
def shapeIsCompound : DenomShape → Bool
  | DenomShape.product => true
  | DenomShape.power   => true
  | DenomShape.simple  => false

/- Whether a denominator slot raises a request for protective brackets. A
   reciprocal slot whose inner expression is COMPOUND (a product or a power) and
   has MORE THAN ONE top-level component raises one; otherwise the surrounding
   division would re-associate across the inner operator and change the meaning
   (the missing-brackets defect the issue describes: a denominator that is itself
   a fraction/quotient prints without the brackets it needs). A reciprocal of a
   single-component or simple inner expression, and any non-reciprocal slot,
   raises none. -/
def needsBrackets (f : DenomFactor) : Bool :=
  f.isReciprocal && (f.components != 1) && shapeIsCompound f.shape

/- Wrap one piece of text in a single bracket pair. -/
def wrapText (t : List Char) : List Char := "(".toList ++ t ++ ")".toList

/- The position of the FIRST denominator slot holding the given inner
   expression. A bracket request names an inner expression, and it is satisfied
   at the earliest slot carrying that expression — so requests raised by slots
   holding equal inner expressions all resolve to the same, earliest position.
   Past the end (no slot holds it) when there is no such slot. -/
def firstSlotWithKey (k : Nat) : List DenomFactor → Nat
  | []      => 0
  | f :: fs => if f.innerKey == k then 0 else 1 + firstSlotWithKey k fs

/- Wrap the text at one position in a bracket pair, leaving every other position
   alone. A position past the end wraps nothing. -/
def wrapAt : List (List Char) → Nat → List (List Char)
  | [],      _     => []
  | t :: ts, 0     => wrapText t :: ts
  | t :: ts, n + 1 => t :: wrapAt ts n

/- The positions the bracket requests resolve to, in slot order: walk the slots
   and, for each one that raises a request, record the position its inner
   expression is found at (`firstSlotWithKey` over the whole slot list `all`).
   One entry per raising slot, so several slots holding the same inner expression
   contribute several entries all naming the same position. -/
def bracketTargets (all : List DenomFactor) : List DenomFactor → List Nat
  | []      => []
  | f :: fs =>
      if needsBrackets f then firstSlotWithKey f.innerKey all :: bracketTargets all fs
      else bracketTargets all fs

/- Satisfy the bracket requests in order, each one wrapping the text at the
   position it named. Requests are applied one after another to the text produced
   so far, so two requests naming the same position wrap that text twice. -/
def applyWraps : List (List Char) → List Nat → List (List Char)
  | texts, []      => texts
  | texts, k :: ks => applyWraps (wrapAt texts k) ks

/- The denominator slots' texts before any bracket request is satisfied. -/
def slotTexts (slots : List DenomFactor) : List (List Char) :=
  slots.map (fun f => f.rendered)

/- The rendered text of every denominator slot: start from the slots' own texts
   and satisfy each bracket request at the position it names. -/
def renderDenomFactors (slots : List DenomFactor) : List (List Char) :=
  applyWraps (slotTexts slots) (bracketTargets slots slots)

@[grind] lemma applyWraps_nil (texts : List (List Char)) : applyWraps texts [] = texts := rfl
@[grind] lemma applyWraps_cons (texts : List (List Char)) (k : Nat) (ks : List Nat) :
    applyWraps texts (k :: ks) = applyWraps (wrapAt texts k) ks := rfl

/- Satisfying `ks` then `js` is satisfying their concatenation. -/
lemma applyWraps_append (texts : List (List Char)) (ks js : List Nat) :
    applyWraps texts (ks ++ js) = applyWraps (applyWraps texts ks) js := by
  induction ks generalizing texts with
  | nil => rfl
  | cons k ks ih => simp [applyWraps_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render every denominator slot of a quotient, satisfying the protective-bracket
   requests raised by its reciprocal slots. `slots` is read-only (not `mut`); the
   step builds a fresh result list and mutates no input (directive 5).

   Desired behaviour: the result is the slots' rendered texts with each bracket
   request satisfied at the position its inner expression is found at — a request
   raised by a reciprocal of a compound inner expression, a reciprocal of a
   simple or single-component inner expression raising none. The defect this pins
   out is a reciprocal whose inner expression is itself a power (e.g. `1/y`)
   being rendered WITHOUT the brackets that a division around it requires, so the
   division re-associates and the printed expression means something else. -/
method bracketDenomFactors (slots : List DenomFactor) return (out : List (List Char))
  ensures out = renderDenomFactors slots
  do
    -- impl-start
    let texts : List (List Char) := slotTexts slots
    let targets : List Nat := bracketTargets slots slots
    let mut result : List (List Char) := texts
    let mut k : Nat := 0
    while k < targets.length
      invariant k ≤ targets.length
      invariant result = applyWraps texts (targets.take k)
      done_with k = targets.length
      decreasing targets.length - k
    do
      result := wrapAt result targets[k]!
      k := k + 1
    return result
    -- impl-end

/- The forward step: taking one more bracket request appends it at the end, so
   satisfying the longer prefix is satisfying the shorter one and then wrapping
   at the new request's position. This is the single goal `loom_solve` leaves for
   the loop body. -/
lemma applyWraps_take_step (texts : List (List Char)) (ks : List Nat) (k : Nat)
    (hk : k < ks.length) :
    applyWraps texts (ks.take (k + 1)) = wrapAt (applyWraps texts (ks.take k)) ks[k]! := by
  have h : ks.take (k + 1) = ks.take k ++ [ks[k]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hk, Option.getD_some]
    exact List.take_succ_eq_append_getElem hk
  rw [h, applyWraps_append]
  rfl

prove_correct bracketDenomFactors by
  loom_solve
  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
    simp_all
  · simp_all [renderDenomFactors]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 11 attacks + pos_control return True from swebench_unified.markers.same_spec (velvet tables). Built by copying Solution.lean and editing ONLY the impl region + the prove_correct body (both elided from spec_view).

== 1. VERIFY RESULTS (each: bash scripts/lean_verify.sh <path>; run 4-at-a-time as concurrent background jobs) ==
  pos_control.lean  rc=0  VERIFIES (positive control — the shipped impl)
  atk_1  rc=1  prepatch bug: product-only gate (power inner raises no request)
  atk_2  rc=1  partial-domain collapse: satisfy NO request, return bare slotTexts
  atk_3  rc=1  boundary: components > 1 instead of != 1 (diverges at components = 0)
  atk_4  rc=1  idealized per-slot resolution — the counterexample refinement.md §C names
  atk_5  rc=1  control-flow effect: dedup co-targeted requests (drops cumulative double-wrap)
  atk_6  rc=1  control-flow off-by-one: fold stops one request short
  atk_7  rc=1  over-widened gate: every shape compound (over-brackets x/(y))
  atk_8  rc=1  branch context dropped: ignore isReciprocal (apow/Rational slots raise requests)
  atk_9  rc=1  wrong resolution rule: LAST occurrence (rindex) instead of b.index
  atk_10 rc=1  control-flow effect: requests satisfied in REVERSE order
  atk_11 rc=1  ungrounded-oracle echo: call renderDenomFactors on the isReciprocal-FILTERED list
11 distinct wrong impls across all four required families; none verified. Rejections inspected in the .log files and confirmed to be 'unsolved goals' on the ensures obligation with a genuinely non-model target.

### 2. RESOLVE RUNS (run_resolve via swebench_unified.harness, real Docker oracle)
  gold patch.diff                -> resolved=True  completed=True  (G-RESOLVE control OK)
  faithful_model.diff (DEEP MODEL as the real function) -> resolved=True completed=True  <== the decisive A-leg test
  ctl_prepatch.diff (atk_1 faithful, product-only gate) -> resolved=False completed=True, 'did not resolve in 3 attempts (consistent — not flaky)'  => harness DOES discriminate; prepatch bug reproduced end-to-end
  ctl_perslot.diff (atk_4 faithful, per-slot wrap)       -> resolved=True   completed=True
  empty patch -> completed=False (harness error, not a usable control; discarded)
NOTE on ctl_perslot: the idealized per-slot resolution RESOLVES (test_Mul does not pin the equal-inner aliasing), but its Lean encoding atk_4 does NOT verify. That is the safe direction (verify is STRICTER than the tests) and is not a verify=>correct break. The unsafe direction — verifies but does not resolve — is what I hunted and did not find.

### 3. A-LEG / MODEL-CORRESPONDENCE AUDIT (the assigned focus)
Built a private pristine base tree (git archive at base_commit b4777fdcef) + a patched copy under my scratch dir. IMPORTANT: the shared worktree is CONCURRENTLY MUTATED by another job — it flipped from base to patched mid-audit — so I did not rely on it; all Python evidence below uses my own repo_base/repo_patched.
  * Shadow model (shadow.py): one Python function per Lean def, observations read from the REAL slot objects, reassembled through _print_Mul's unchanged scaffold, installed via monkeypatch so `rendered` is taken at the REAL print level. Deliberately does NOT reuse pow_paren or b.index (else the check is tautological).
  * Fuzz vs the real PATCHED _print_Mul, seed 21612, over StrPrinter() and StrPrinter({'order':'none'}): NARROW doc family 60,016 inputs -> 0 mismatches; WIDE pool (Float/I/pi/sqrt/Add/Rational/half-powers) 60,000 inputs -> 0 mismatches. Total 120,016 / 0.
  * TEETH check (all three wrong models must disagree, and do): per-slot idealized 644 disagreements, first real='x/((((y*z)))*(y*z))' vs model='x/(((y*z))*((y*z)))' — exactly the string refinement.md §C predicts; prepatch Mul-only 3,390, first real='x/(1/y)' vs model='x/1/y'; dedup-co-targets 630. So the 0-mismatch result is meaningful, not vacuous.
  * A6 (innerKey <-> ==, the sharpest leg): sympy `==` on real slot values is reflexive/symmetric/TRANSITIVE over the candidate pool (0 violations), so a Nat code CAN faithfully encode it; and first-match Nat coding reproduces real b.index on 6,000 random real slot lists (0 divergences).
  * A4/A3: `item.base is item.args[0]` holds for all 28 real reciprocal-slot constructions tried (0 violations), so components=len(b[k].args) really is the gate's len(item.args[0].args); Mul/Pow disjoint (0 violations) so `shape` is a faithful 3-way classification.
  * Doc anchors reproduce exactly on the real printer: equal-inner (y*z)^-1 twice -> 'x/((((y*z)))*(y*z))' and (1/y)^-1 twice -> 'x/(((1/y))*1/y)', matching mapping.md §0 / §4 verbatim.
  * One apparent WIDE-fuzz mismatch family (1.5 vs 1.50000000000000, 4,508 hits) was diagnosed to MY harness calling parenthesize outside doprint (full_prec='auto' depends on _print_level), NOT a model defect: it vanished entirely under the in-situ monkeypatch and never once differed in bracketing.

### 4. refinement.md LEG KINDS
11 legs A1-A11, tagged 2x R, 4x R + A-reference, 4x I (+ A8 'I' with G-AX grounding). No kind-3, no A-consumed anywhere; `grep -c '^\s*axiom\s' Solution.lean` = 0, consistent with §C's 'there is no consumed axiom'. The A-reference legs' correspondence to the real callees (parenthesize, type(b[k]), len(b[k].args), the exp==-1 branch, ==-classes) is exactly what §3 above checked against the real objects, and each holds. §B's altitude claim (first arm untouched by the patch, gate only in the main arm) matches the source I read; my fuzz correctly skips first-arm inputs (7,332 skips in the standalone run).

### Verdict: SOUND
>=5 attacks (11) encoded, same-spec-confirmed and fully verified; positive control verifies; prepatch bug reproduced in Lean (atk_1 rc=1) AND end-to-end in the harness (ctl_prepatch resolved=False, consistent). No verifying wrong impl exists, so no faithful patch was obligated by step 2; I nonetheless executed 5 resolve runs, including materializing the deep model itself, which resolved. The one residual risk I can identify is NOT a spec defect but a coverage fact worth recording: the graded tests do not pin the equal-inner aliasing (ctl_perslot resolves), so G-EQ's soundness here rests on the spec being STRICTER than the tests — the safe direction.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 11 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verifying wrong impl exists to exhibit. All 11 same-spec wrong impls were REJECTED by lean_verify.sh (rc=1, genuine 'unsolved goals' on the ensures obligation, not tactic weakness), so protocol step 2 (materialize + resolve the faithful patch of a VERIFYING wrong impl) has an empty obligation set. Structural reason: the axioms region declares ZERO `axiom`s (only `inductive DenomShape` + `structure DenomFactor`), there is NO `requires`, and the postcondition is the unconditional pointwise equality `out = renderDenomFactors slots` against a TOTAL, fully concrete deep model. Any verifying impl is therefore extensionally equal to renderDenomFactors on every input — no partial-domain, boundary, control-flow or ungrounded-oracle wedge is available. Residual goals confirm real semantic gaps, e.g. atk_5 left `result_1 = applyWraps (slotTexts slots) (bracketTargets slots slots)` with only `applyWraps ... (bracketTargets slots slots).eraseDups = result_1` in hand; atk_1 (prepatch) left the same goal with the product-only filter. Since the wedge must instead be model-vs-patch, I materialized the deep model VERBATIM as the real function (faithful_model.diff: own isReciprocal flags + transliterated needsBrackets/firstSlotWithKey/cumulative wrap replacing the real pow_paren/b.index block) and it RESOLVED — so the model↔patch correspondence is behaviourally sound on the graded tests, in the strongest form the protocol asks for.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The structural classification of the inner expression sitting underneath a
   denominator slot. When a quotient is rendered to its textual form, each
   denominator slot holds some inner expression; that inner expression has one of
   three shapes:

     • `product` — it is a product of two or more factors;
     • `power`   — it is itself a power (an exponentiation);
     • `simple`  — anything else (a single atom, a number, …).

   This is an OBSERVATION of an unchanged sub-object, not a computed value: the
   renderer already knows, for any sub-expression, both its rendered text and its
   top-level shape. Provenance + the executable soundness check that these
   observations match reality: mapping.md §3 / axiom_check.py (G-AX). -/
inductive DenomShape where
  | product
  | power
  | simple
deriving DecidableEq, Inhabited, Repr

/- One slot of the rendered denominator, described by the observations the
   bracketing decision needs:
     • `rendered`     — the already-rendered text of the slot's inner expression
                        (the result of the renderer's standard sub-rendering, an
                        unchanged callee taken here as a given value);
     • `shape`        — the inner expression's top-level shape (above);
     • `components`   — the number of top-level components of the inner
                        expression (e.g. the factor count of a product);
     • `isReciprocal` — whether this slot arose as the reciprocal of its inner
                        expression. Only reciprocal slots are ever considered for
                        protective brackets; the other denominator slots are
                        assembled from their text unchanged.
     • `innerKey`     — an identity code for the slot's inner expression: two
                        slots carry the SAME `innerKey` exactly when they hold
                        equal inner expressions. This is what lets a bracket
                        request be located by the expression it names rather than
                        by the position it was raised from. -/
structure DenomFactor where
  rendered     : List Char
  shape        : DenomShape
  components   : Nat
  isReciprocal : Bool
  innerKey     : Nat
deriving Inhabited
-- axioms-end

-- pure-start
/- A shape is *compound* when the inner expression is built from sub-parts that
   could be torn apart by a surrounding division — a product or a power. A simple
   atom is never compound. -/
def shapeIsCompound : DenomShape → Bool
  | DenomShape.product => true
  | DenomShape.power   => true
  | DenomShape.simple  => false

/- Whether a denominator slot raises a request for protective brackets. A
   reciprocal slot whose inner expression is COMPOUND (a product or a power) and
   has MORE THAN ONE top-level component raises one; otherwise the surrounding
   division would re-associate across the inner operator and change the meaning
   (the missing-brackets defect the issue describes: a denominator that is itself
   a fraction/quotient prints without the brackets it needs). A reciprocal of a
   single-component or simple inner expression, and any non-reciprocal slot,
   raises none. -/
def needsBrackets (f : DenomFactor) : Bool :=
  f.isReciprocal && (f.components != 1) && shapeIsCompound f.shape

/- Wrap one piece of text in a single bracket pair. -/
def wrapText (t : List Char) : List Char := "(".toList ++ t ++ ")".toList

/- The position of the FIRST denominator slot holding the given inner
   expression. A bracket request names an inner expression, and it is satisfied
   at the earliest slot carrying that expression — so requests raised by slots
   holding equal inner expressions all resolve to the same, earliest position.
   Past the end (no slot holds it) when there is no such slot. -/
def firstSlotWithKey (k : Nat) : List DenomFactor → Nat
  | []      => 0
  | f :: fs => if f.innerKey == k then 0 else 1 + firstSlotWithKey k fs

/- Wrap the text at one position in a bracket pair, leaving every other position
   alone. A position past the end wraps nothing. -/
def wrapAt : List (List Char) → Nat → List (List Char)
  | [],      _     => []
  | t :: ts, 0     => wrapText t :: ts
  | t :: ts, n + 1 => t :: wrapAt ts n

/- The positions the bracket requests resolve to, in slot order: walk the slots
   and, for each one that raises a request, record the position its inner
   expression is found at (`firstSlotWithKey` over the whole slot list `all`).
   One entry per raising slot, so several slots holding the same inner expression
   contribute several entries all naming the same position. -/
def bracketTargets (all : List DenomFactor) : List DenomFactor → List Nat
  | []      => []
  | f :: fs =>
      if needsBrackets f then firstSlotWithKey f.innerKey all :: bracketTargets all fs
      else bracketTargets all fs

/- Satisfy the bracket requests in order, each one wrapping the text at the
   position it named. Requests are applied one after another to the text produced
   so far, so two requests naming the same position wrap that text twice. -/
def applyWraps : List (List Char) → List Nat → List (List Char)
  | texts, []      => texts
  | texts, k :: ks => applyWraps (wrapAt texts k) ks

/- The denominator slots' texts before any bracket request is satisfied. -/
def slotTexts (slots : List DenomFactor) : List (List Char) :=
  slots.map (fun f => f.rendered)

/- The rendered text of every denominator slot: start from the slots' own texts
   and satisfy each bracket request at the position it names. -/
def renderDenomFactors (slots : List DenomFactor) : List (List Char) :=
  applyWraps (slotTexts slots) (bracketTargets slots slots)

@[grind] lemma applyWraps_nil (texts : List (List Char)) : applyWraps texts [] = texts := rfl
@[grind] lemma applyWraps_cons (texts : List (List Char)) (k : Nat) (ks : List Nat) :
    applyWraps texts (k :: ks) = applyWraps (wrapAt texts k) ks := rfl

/- Satisfying `ks` then `js` is satisfying their concatenation. -/
lemma applyWraps_append (texts : List (List Char)) (ks js : List Nat) :
    applyWraps texts (ks ++ js) = applyWraps (applyWraps texts ks) js := by
  induction ks generalizing texts with
  | nil => rfl
  | cons k ks ih => simp [applyWraps_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render every denominator slot of a quotient, satisfying the protective-bracket
   requests raised by its reciprocal slots. `slots` is read-only (not `mut`); the
   step builds a fresh result list and mutates no input (directive 5).

   Desired behaviour: the result is the slots' rendered texts with each bracket
   request satisfied at the position its inner expression is found at — a request
   raised by a reciprocal of a compound inner expression, a reciprocal of a
   simple or single-component inner expression raising none. The defect this pins
   out is a reciprocal whose inner expression is itself a power (e.g. `1/y`)
   being rendered WITHOUT the brackets that a division around it requires, so the
   division re-associates and the printed expression means something else. -/
method bracketDenomFactors (slots : List DenomFactor) return (out : List (List Char))
  ensures out = renderDenomFactors slots
  do
    -- impl-start
    let texts : List (List Char) := slotTexts slots
    let targets : List Nat := bracketTargets slots slots
    let mut result : List (List Char) := texts
    let mut k : Nat := 0
    while k < targets.length
      invariant k ≤ targets.length
      invariant result = applyWraps texts (targets.take k)
      done_with k = targets.length
      decreasing targets.length - k
    do
      result := wrapAt result targets[k]!
      k := k + 1
    return result
    -- impl-end

/- The forward step: taking one more bracket request appends it at the end, so
   satisfying the longer prefix is satisfying the shorter one and then wrapping
   at the new request's position. This is the single goal `loom_solve` leaves for
   the loop body. -/
lemma applyWraps_take_step (texts : List (List Char)) (ks : List Nat) (k : Nat)
    (hk : k < ks.length) :
    applyWraps texts (ks.take (k + 1)) = wrapAt (applyWraps texts (ks.take k)) ks[k]! := by
  have h : ks.take (k + 1) = ks.take k ++ [ks[k]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hk, Option.getD_some]
    exact List.take_succ_eq_append_getElem hk
  rw [h, applyWraps_append]
  rfl

prove_correct bracketDenomFactors by
  loom_solve
  · rw [applyWraps_take_step (slotTexts slots) (bracketTargets slots slots) k (by omega)]
    simp_all
  · simp_all [renderDenomFactors]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 11 attacks + pos_control return True from swebench_unified.markers.same_spec (velvet tables). Built by copying Solution.lean and editing ONLY the impl region + the prove_correct body (both elided from spec_view).

== 1. VERIFY RESULTS (each: bash scripts/lean_verify.sh <path>; run 4-at-a-time as concurrent background jobs) ==
  pos_control.lean  rc=0  VERIFIES (positive control — the shipped impl)
  atk_1  rc=1  prepatch bug: product-only gate (power inner raises no request)
  atk_2  rc=1  partial-domain collapse: satisfy NO request, return bare slotTexts
  atk_3  rc=1  boundary: components > 1 instead of != 1 (diverges at components = 0)
  atk_4  rc=1  idealized per-slot resolution — the counterexample refinement.md §C names
  atk_5  rc=1  control-flow effect: dedup co-targeted requests (drops cumulative double-wrap)
  atk_6  rc=1  control-flow off-by-one: fold stops one request short
  atk_7  rc=1  over-widened gate: every shape compound (over-brackets x/(y))
  atk_8  rc=1  branch context dropped: ignore isReciprocal (apow/Rational slots raise requests)
  atk_9  rc=1  wrong resolution rule: LAST occurrence (rindex) instead of b.index
  atk_10 rc=1  control-flow effect: requests satisfied in REVERSE order
  atk_11 rc=1  ungrounded-oracle echo: call renderDenomFactors on the isReciprocal-FILTERED list
11 distinct wrong impls across all four required families; none verified. Rejections inspected in the .log files and confirmed to be 'unsolved goals' on the ensures obligation with a genuinely non-model target.

### 2. RESOLVE RUNS (run_resolve via swebench_unified.harness, real Docker oracle)
  gold patch.diff                -> resolved=True  completed=True  (G-RESOLVE control OK)
  faithful_model.diff (DEEP MODEL as the real function) -> resolved=True completed=True  <== the decisive A-leg test
  ctl_prepatch.diff (atk_1 faithful, product-only gate) -> resolved=False completed=True, 'did not resolve in 3 attempts (consistent — not flaky)'  => harness DOES discriminate; prepatch bug reproduced end-to-end
  ctl_perslot.diff (atk_4 faithful, per-slot wrap)       -> resolved=True   completed=True
  empty patch -> completed=False (harness error, not a usable control; discarded)
NOTE on ctl_perslot: the idealized per-slot resolution RESOLVES (test_Mul does not pin the equal-inner aliasing), but its Lean encoding atk_4 does NOT verify. That is the safe direction (verify is STRICTER than the tests) and is not a verify=>correct break. The unsafe direction — verifies but does not resolve — is what I hunted and did not find.

### 3. A-LEG / MODEL-CORRESPONDENCE AUDIT (the assigned focus)
Built a private pristine base tree (git archive at base_commit b4777fdcef) + a patched copy under my scratch dir. IMPORTANT: the shared worktree is CONCURRENTLY MUTATED by another job — it flipped from base to patched mid-audit — so I did not rely on it; all Python evidence below uses my own repo_base/repo_patched.
  * Shadow model (shadow.py): one Python function per Lean def, observations read from the REAL slot objects, reassembled through _print_Mul's unchanged scaffold, installed via monkeypatch so `rendered` is taken at the REAL print level. Deliberately does NOT reuse pow_paren or b.index (else the check is tautological).
  * Fuzz vs the real PATCHED _print_Mul, seed 21612, over StrPrinter() and StrPrinter({'order':'none'}): NARROW doc family 60,016 inputs -> 0 mismatches; WIDE pool (Float/I/pi/sqrt/Add/Rational/half-powers) 60,000 inputs -> 0 mismatches. Total 120,016 / 0.
  * TEETH check (all three wrong models must disagree, and do): per-slot idealized 644 disagreements, first real='x/((((y*z)))*(y*z))' vs model='x/(((y*z))*((y*z)))' — exactly the string refinement.md §C predicts; prepatch Mul-only 3,390, first real='x/(1/y)' vs model='x/1/y'; dedup-co-targets 630. So the 0-mismatch result is meaningful, not vacuous.
  * A6 (innerKey <-> ==, the sharpest leg): sympy `==` on real slot values is reflexive/symmetric/TRANSITIVE over the candidate pool (0 violations), so a Nat code CAN faithfully encode it; and first-match Nat coding reproduces real b.index on 6,000 random real slot lists (0 divergences).
  * A4/A3: `item.base is item.args[0]` holds for all 28 real reciprocal-slot constructions tried (0 violations), so components=len(b[k].args) really is the gate's len(item.args[0].args); Mul/Pow disjoint (0 violations) so `shape` is a faithful 3-way classification.
  * Doc anchors reproduce exactly on the real printer: equal-inner (y*z)^-1 twice -> 'x/((((y*z)))*(y*z))' and (1/y)^-1 twice -> 'x/(((1/y))*1/y)', matching mapping.md §0 / §4 verbatim.
  * One apparent WIDE-fuzz mismatch family (1.5 vs 1.50000000000000, 4,508 hits) was diagnosed to MY harness calling parenthesize outside doprint (full_prec='auto' depends on _print_level), NOT a model defect: it vanished entirely under the in-situ monkeypatch and never once differed in bracketing.

### 4. refinement.md LEG KINDS
11 legs A1-A11, tagged 2x R, 4x R + A-reference, 4x I (+ A8 'I' with G-AX grounding). No kind-3, no A-consumed anywhere; `grep -c '^\s*axiom\s' Solution.lean` = 0, consistent with §C's 'there is no consumed axiom'. The A-reference legs' correspondence to the real callees (parenthesize, type(b[k]), len(b[k].args), the exp==-1 branch, ==-classes) is exactly what §3 above checked against the real objects, and each holds. §B's altitude claim (first arm untouched by the patch, gate only in the main arm) matches the source I read; my fuzz correctly skips first-arm inputs (7,332 skips in the standalone run).

### Verdict: SOUND
>=5 attacks (11) encoded, same-spec-confirmed and fully verified; positive control verifies; prepatch bug reproduced in Lean (atk_1 rc=1) AND end-to-end in the harness (ctl_prepatch resolved=False, consistent). No verifying wrong impl exists, so no faithful patch was obligated by step 2; I nonetheless executed 5 resolve runs, including materializing the deep model itself, which resolved. The one residual risk I can identify is NOT a spec defect but a coverage fact worth recording: the graded tests do not pin the equal-inner aliasing (ctl_perslot resolves), so G-EQ's soundness here rests on the spec being STRICTER than the tests — the safe direction.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK LANE: faithfulness-break (spec too strong / modeled function disagrees with real callee). Result: NO divergence found after ~130k in-altitude differential comparisons plus structural attacks. Verdict FAITHFUL.

### Integrity
- Spec-region byte-identity CONFIRMED: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend)=True; axioms (2244B) and pure (3961B) byte-identical, pre/post-conditions empty. region_hashes axioms=6baf48b34824... matches the G-HYGIENE record in meta.json, so the prepatch rival is judged against THIS frozen spec.
- Baseline Solution.lean verifies: scripts/lean_verify.sh -> EXIT=0.
- Worktree at base_commit b4777fdcef46 with gold applied; patch.diff is verbatim the one-line gate widening isinstance(item.base, Mul) -> (Mul, Pow).

### INDEPENDENT HARNESS (did NOT reuse conformance_check.py)
Wrote my own transliteration of the Lean pure region (shapeIsCompound, needsBrackets, firstSlotWithKey, wrapAt, bracketTargets, applyWraps, slotTexts, renderDenomFactors) plus my own instrumented VERBATIM copy of the patched _print_Mul main arm capturing (b, b_str_pre, b_str_post, per-slot isReciprocal). Observations read from the REAL slot objects. Compared model renderDenomFactors vs real post-wrap b_str, and separately reassembled the FULL string from the MODEL's b_str vs real str().
NEGATIVE CONTROL (proves teeth): swapping in the idealized per-slot wrap immediately DIVERGES on Mul(x, 1/(y*z), 1/(y*z)) -- real ['(((y*z)))','(y*z)'] vs model ['((y*z))','((y*z))']. My harness catches exactly the failure mode refinement.md sec C warns about, so the clean runs are informative.

### DIFFERENTIAL RESULTS (0 divergences everywhere)
1. Random fuzz, seed 999001 (deliberately NOT velvet's 21612), nested Mul/Pow/Add inners, small pool sampled WITH REPLACEMENT, ~20% apow (exp != -1) slots, both StrPrinter() and order:none: 35846 in-altitude compared, 0 bad.
2. EXHAUSTIVE ordered pairs over 10 inners x {recip, apow, num} x 2 printers x optional numerator: 3600 compared, 0 bad.
3. EXHAUSTIVE ordered triples over 7 inners x 3 kinds x 2 printers: 18522 compared, 0 bad.
4. Heavy-aliasing fuzz (4-6 slots drawn from a 1-2 element pool, forcing triple/quadruple co-targeting on one position): 40000 compared, 0 bad.
5. END-TO-END full-string reassembly from the MODEL's b_str vs real str(): 33524 compared, 0 mismatches.
6. Gold test file: 100 passed (F2P str(Mul(x, Pow(1/y,-1))) == 'x/(1/y)' and the #14160 P2P both green).

### Targeted attacks on the modeling assumptions
- innerKey as an equivalence code: the real lookup is b.index/in, i.e. PyObject_RichCompareBool, which has an IDENTITY SHORTCUT before ==. A self-non-equal slot value would break innerKey's equivalence-class model. Checked reflexivity of NaN, Float('nan'), zoo, Symbol, Eq -- all reflexive under sympy ==, so the shortcut is unobservable here. Also verified exhaustively over a 37-element quirky pool (multi-precision Floats at 5/15/30/53 bits, Rational vs Float, +-0.0, oo, NaN, zoo, assumption-tagged Symbols, unevaluated Mul/Pow/Add, order-swapped products) that == is reflexive, symmetric AND transitive: 0 violations of each. So innerKey is a faithful code for the ==-classes, exactly as mapping.md sec 2 claims. My harness additionally asserts pairwise (codes[i]==codes[j]) == bool(b[i]==b[j]) on EVERY fuzz case and never fired.
- Equal-value / different-text attack: Float('1.0',5) == Float('1.0',30) is True but they render '1.0000' vs '1.00000000000000000000000000000'. Built Mul(x, 1/(1.0_p5*y), 1/(1.0_p30*y)): the two inners compare == so both requests co-target slot 0. Model matched real ('x/((((1.0*y)))*(1.0*y))'). This is the sharpest available probe of firstSlotWithKey vs b.index and it agrees.
- Order-swapped inners: Mul(y,z,ev=F) vs Mul(z,y,ev=F) render identically but are == False -> distinct innerKeys, each wrapped at its own slot. Model matched real. Confirms innerKey tracks == and NOT rendered text.
- Cross-kind aliasing (a non-reciprocal apow or Rational(q) slot holding a value == a reciprocal slot's base, so b.index lands on a slot that can never itself raise a request): probed directly; model matched. Confirms A1's decision to model ALL of b, not only reciprocal entries.
- Observation invariants: for every reciprocal factor item.base IS item.args[0] and len(item.args[0].args) == len(item.base.args) (0 violations over the inner pool), so components faithfully models the quantity the gate at str.py:335 actually reads. shapeIsCompound(shape) == isinstance(v,(Mul,Pow)) for all slot values, 0 violations.
- Shape-ambiguity is neutralized: needsBrackets uses shape only through shapeIsCompound, which collapses product and power to true, exactly mirroring isinstance(item.base, (Mul, Pow)). Confirmed no Mul/Pow subclass can reach a str.py denominator slot (only MatMul subclasses Mul, and MatMul routes to _print_MatMul), so the 3-way classification cannot be mis-assigned in a way that matters.
- past-the-end request (item.base not in b): firstSlotWithKey returns slots.length and wrapAt is a no-op, matching the real 'if item.base in b' guard that skips the request. Structurally checked in the transliteration.

### Altitude honesty
The first arm of _print_Mul (leading One / any Number in args[1:] / integer-base-and-exp Pow) is genuinely untouched by the patch and is correctly declared out of altitude in refinement.md sec B / mapping.md. I independently confirmed BOTH anchors route to the MAIN arm (F2P Mul(x, Pow(1/y,-1)) and #14160 Mul(-2,x,1/(y*y))), so the altitude exclusion does not quietly exclude the discriminating input -- the exclusion is not a dodge. My harness reports first-arm inputs as an explicit skip category (6476-23594 per run, always logged, never silently counted as agreement).

### Why not UNFAITHFUL
The spec is neither too strong nor too weak on the tested space. The three places it could have over-committed all check out against the real repo: (a) the changed gate is modeled directly and matches the patched conjunct including the unchanged components != 1 and the enclosing exp is NegativeOne branch; (b) the UNCHANGED request-resolution rule (first-occurrence value lookup, cumulative re-read of b_str, double-wrap on co-target, bare later slot) is modeled explicitly rather than idealized -- and this is the trap the negative control shows a lazier spec would fall into; (c) innerKey and shape, the two abstractions that could have smuggled in strength, are provably faithful (== is a true equivalence; shape is used only through the compound collapse). I found no input on which renderDenomFactors disagrees with the real patched b_str, so I cannot cite a diverging input and do not claim a defect.

CAVEAT (scope, not a defect): my coverage is the commutative-Pow / Rational denominator families reachable from unevaluated Mul in the main arm. Non-commutative factors and exotic Expr subclasses defining custom __eq__ were not swept exhaustively; a custom non-transitive __eq__ would in principle break innerKey, but no such type reaches a str.py denominator slot in this repo, so this is hypothetical rather than a live divergence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous leakage / gold-reconstruction review of the velvet spec view for sympy__sympy-21612.

GOLD EDIT: widen the pow_paren request gate at sympy/printing/str.py:335-336 from `isinstance(item.base, Mul)` to `isinstance(item.base, (Mul, Pow))`, so a reciprocal denominator factor whose inner expression is a POWER (not only a product) is bracketed.

### PRECONDITIONS VERIFIED (as instructed)
1. same_spec(Solution.lean, Solution_prepatch.lean) = True under swebench_unified.markers (velvet) -- the frozen spec region is byte-identical patched vs prepatch; impl/prove_correct bodies are the only differences and both are elided by the spec-view projection. spec_view is idempotent. Confirmed the pure region diff between the two files is empty.
2. scripts/lean_verify.sh Solution.lean -> exit 0 (verifies, no sorry/error).
3. Mechanical G-LEAK screen (leakage.screen over spec_view, judged against problem_statement, NOT hints_text) PASSES with zero hard failures: no diff markers; no reproduced >=8-char normalized gold line; no patched file path `sympy/printing/str.py` nor dotted module; no spec-view identifier embedding the patch's only distinctive changed symbol (`apow`); no narration keyword. I re-ran the screen myself rather than trusting meta.json.

### SEMANTIC GOLD-RECONSTRUCTION (the part the lexical screen cannot do)
The discriminating content of the spec view is real and deliberate: `shapeIsCompound DenomShape.power => true` plus `needsBrackets f = f.isReciprocal && (f.components != 1) && shapeIsCompound f.shape`. That is, up to renaming, the patched gate. So the question is strictly whether the POWER trigger is derivable from the PUBLIC problem_statement.

It is, and I confirmed it empirically against the real repo rather than on paper. Running in the base worktree (b4777fdcef): the public statement's own worked example is \frac{\frac{a^3+b}{c}}{\frac{1}{c^2}}, whose denominator slot is Pow(inner,-1) with inner = 1/c**2 = `c**`. Measured: type(inner).__name__ == 'Pow', len(inner.args) == 2, isinstance(item.base, Pow) is True, isinstance(item.base, Mul) is FALSE, and the gate quantity len(item.args[0].args) != 1 is True. So the single public example IS precisely the reciprocal-of-a-POWER, components!=1 case -- not a product case -- and the statement publishes the expected bracketed output ((a**3 + b)/c)/(1/(c**2)) plus the words "missing brackets in the denominator result in a wrong expression". Both the trigger class and the required behavior are therefore public. The spec states abstract desired behavior; it never states the edit.

### Attack vectors tried and cleared
- Patched symbols/paths: `Mul`, `Pow`, `pow_paren`, `b_str`, `parenthesize`, `b.index`, `apow`, `isinstance`, `_print_Mul`, `str.py`, `sympy`, `printing`, `Rational`, `NegativeOne`, `14160`, `21537` -- grepped the spec view case-insensitively. NONE appear. "power" appears only as the abstract English word / the `DenomShape.power` constructor, which is domain vocabulary (an exponentiation), not the repo type name in a localizing context.
- Narration: the spec uses "defect"/"means something else" where "bug"/"wrong" would trip the screen. I checked whether this is de-narration dodging and concluded it is not: the problem_statement itself already says "missing brackets" and "wrong expression", so this prose is public content restated abstractly. No pre-patch-vs-post-patch mechanism is narrated, no diff is described.
- Hidden-test leak (my closest call, reported for transparency): the spec view's illustrative `e.g. 1/y` coincides with the hidden F2P assertion str(Mul(x, Pow(1/y,-1)))=='x/(1/y)'. The formal-flavor screen ignores test_patch by design, so I judged this semantically. Verified in real sympy that `1/y` = Pow(y,-1) and the public `1/c**2` = Pow(c,-2) are the SAME case on every quantity the gate reads (both Pow-based, both len(args)==2, both trigger identically). `1/y` is thus a relabeling of the public example and conveys no discriminating power beyond it. Not a leak, but it is the tightest line in the file.
- Bundle-doc channel: spec-view line 22 points the consumer at "mapping.md §3 / axiom_check.py (G-AX)", and mapping.md DOES quote the gold hunk verbatim (`isinstance(item.base, (Mul, Pow))` at lines 67-68, 133). I checked reachability: the eval agent's bash tool executes inside the container with cwd /testbed (eval/agent.py _do_bash -> container.exec), and only task.spec_view is rendered into the prompt (eval/prompts.py _spec_block); no code path copies mapping.md/refinement.md/verdict.md into the container. The bundle docs live on the host and are unreachable by the consumer, so this pointer is dangling, not leaking. Worth noting as a latent hazard if a future harness ever ships bundle docs alongside the spec.
- The `components != 1` conjunct and the firstSlotWithKey/cumulative-applyWraps resolution rule encode repo-internal structure, but both are UNCHANGED by the patch; modeling them is required for behavioral faithfulness and neither localizes the edit.

CONCLUSION: no spec-view line reveals the gold edit beyond the public problem_statement. Verdict NO-LEAKAGE.

OUT OF SCOPE (flagged, not my gate): verdict.md records a sibling attacker's finding that the frozen spec's per-slot bracketing model drifts from the real b.index/duplicate-base aliasing behavior, and that the shipped conformance_check.py cannot see it. That is a spec-strength/fidelity question for the equivalence and conformance gates, not a leakage question, and it does not change my verdict here.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.