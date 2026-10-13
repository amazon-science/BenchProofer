# P2 adversarial audit — django__django-14122

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk6.lean`, `atk7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,24 +83,8 @@
   ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
   do
     -- impl-start
-    -- Collect the ordering-term contributions (reference terms contribute
-    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
-    -- per loop step.
-    let mut order : List Int := []
-    let mut i := orderTerms.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ orderTerms.length
-      invariant order = orderFold (orderTerms.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let t := orderTerms[i - 1]!
-      order := (if t.isRef then [] else t.cols) ++ order
-      i := i - 1
-    -- The ordering terms widen the grouping set only when the ordering is
-    -- explicit; a default-ordering-derived ordering contributes nothing.
-    let orderContrib : List Int := if metaOrdering then [] else order
-    return baseCols ++ selectCols ++ orderContrib ++ havingCols
+    -- partial-domain: never includes order columns (always drops them)
+    return baseCols ++ selectCols ++ havingCols
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,22 +83,16 @@
   ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
   do
     -- impl-start
-    -- Collect the ordering-term contributions (reference terms contribute
-    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
-    -- per loop step.
+    -- boundary: loop stops at i>1, dropping the first ordering term
     let mut order : List Int := []
     let mut i := orderTerms.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ orderTerms.length
-      invariant order = orderFold (orderTerms.drop i)
-      done_with i = 0
+    while i > 1
+      invariant 1 ≤ i ∧ i ≤ orderTerms.length
       decreasing i
     do
       let t := orderTerms[i - 1]!
       order := (if t.isRef then [] else t.cols) ++ order
       i := i - 1
-    -- The ordering terms widen the grouping set only when the ordering is
-    -- explicit; a default-ordering-derived ordering contributes nothing.
     let orderContrib : List Int := if metaOrdering then [] else order
     return baseCols ++ selectCols ++ orderContrib ++ havingCols
     -- impl-end
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,7 @@
   ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
   do
     -- impl-start
-    -- Collect the ordering-term contributions (reference terms contribute
-    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
-    -- per loop step.
+    -- control-flow: places the order contribution BEFORE selectCols
     let mut order : List Int := []
     let mut i := orderTerms.length
     while i > 0
@@ -97,10 +95,8 @@
       let t := orderTerms[i - 1]!
       order := (if t.isRef then [] else t.cols) ++ order
       i := i - 1
-    -- The ordering terms widen the grouping set only when the ordering is
-    -- explicit; a default-ordering-derived ordering contributes nothing.
     let orderContrib : List Int := if metaOrdering then [] else order
-    return baseCols ++ selectCols ++ orderContrib ++ havingCols
+    return baseCols ++ orderContrib ++ selectCols ++ havingCols
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,22 +83,16 @@
   ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
   do
     -- impl-start
-    -- Collect the ordering-term contributions (reference terms contribute
-    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
-    -- per loop step.
+    -- ungrounded: reference (isRef) terms wrongly contribute their columns too
     let mut order : List Int := []
     let mut i := orderTerms.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ orderTerms.length
-      invariant order = orderFold (orderTerms.drop i)
-      done_with i = 0
       decreasing i
     do
       let t := orderTerms[i - 1]!
-      order := (if t.isRef then [] else t.cols) ++ order
+      order := t.cols ++ order
       i := i - 1
-    -- The ordering terms widen the grouping set only when the ordering is
-    -- explicit; a default-ordering-derived ordering contributes nothing.
     let orderContrib : List Int := if metaOrdering then [] else order
     return baseCols ++ selectCols ++ orderContrib ++ havingCols
     -- impl-end
```

Attack 5 — `atk5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -83,24 +83,8 @@
   ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
   do
     -- impl-start
-    -- Collect the ordering-term contributions (reference terms contribute
-    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
-    -- per loop step.
-    let mut order : List Int := []
-    let mut i := orderTerms.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ orderTerms.length
-      invariant order = orderFold (orderTerms.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let t := orderTerms[i - 1]!
-      order := (if t.isRef then [] else t.cols) ++ order
-      i := i - 1
-    -- The ordering terms widen the grouping set only when the ordering is
-    -- explicit; a default-ordering-derived ordering contributes nothing.
-    let orderContrib : List Int := if metaOrdering then [] else order
-    return baseCols ++ selectCols ++ orderContrib ++ havingCols
+    -- oracle echo: return the spec's groupingSet verbatim
+    return groupingSet baseCols selectCols orderTerms havingCols metaOrdering
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -121,6 +105,4 @@
 
 prove_correct groupingColumns by
   loom_solve
-  · rw [orderFold_drop_step orderTerms i (by omega) (by omega)]
-    simp_all
   all_goals simp_all [groupingSet]
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,7 @@
   ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
   do
     -- impl-start
-    -- Collect the ordering-term contributions (reference terms contribute
-    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
-    -- per loop step.
+    -- inverted guard: contributes order columns exactly when metaOrdering is TRUE
     let mut order : List Int := []
     let mut i := orderTerms.length
     while i > 0
@@ -97,9 +95,7 @@
       let t := orderTerms[i - 1]!
       order := (if t.isRef then [] else t.cols) ++ order
       i := i - 1
-    -- The ordering terms widen the grouping set only when the ordering is
-    -- explicit; a default-ordering-derived ordering contributes nothing.
-    let orderContrib : List Int := if metaOrdering then [] else order
+    let orderContrib : List Int := if metaOrdering then order else []
     return baseCols ++ selectCols ++ orderContrib ++ havingCols
     -- impl-end
 
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,7 @@
   ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
   do
     -- impl-start
-    -- Collect the ordering-term contributions (reference terms contribute
-    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
-    -- per loop step.
+    -- drops havingCols entirely
     let mut order : List Int := []
     let mut i := orderTerms.length
     while i > 0
@@ -97,10 +95,8 @@
       let t := orderTerms[i - 1]!
       order := (if t.isRef then [] else t.cols) ++ order
       i := i - 1
-    -- The ordering terms widen the grouping set only when the ordering is
-    -- explicit; a default-ordering-derived ordering contributes nothing.
     let orderContrib : List Int := if metaOrdering then [] else order
-    return baseCols ++ selectCols ++ orderContrib ++ havingCols
+    return baseCols ++ selectCols ++ orderContrib
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The grouping-column set is assembled from contributions
-- that are explicit, observable inputs of the routine: the grouping base, the
-- selected columns (already pruned of those reachable by reference), the
-- ordering terms, and the filter columns. The per-term column lists are taken
-- as given (each term already carries the columns it would contribute and a
-- flag marking it as a mere reference to the selected set); the routine does
-- not recompute them, so there is no unchanged library callee whose contract
-- the proof must assume. The whole decision is modeled DEEPLY over these inputs.
-- axioms-end

-- pure-start
/- One ordering term, abstracted to exactly the two facts that decide its
   contribution to the grouping set: the columns it would contribute
   (`cols`), and whether it is merely a reference back into the selected set
   (`isRef`). A term that is a reference contributes nothing — its columns are
   already part of the grouping set by virtue of being selected. -/
structure OrderTerm where
  cols : List Int
  isRef : Bool
deriving Inhabited

/- The grouping columns contributed by the ordering terms: each term that is
   NOT a back-reference contributes its columns, in order; a reference term
   contributes nothing. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern). -/
def orderFold : List OrderTerm → List Int
  | []      => []
  | t :: ts => (if t.isRef then [] else t.cols) ++ orderFold ts

@[grind] lemma orderFold_nil : orderFold [] = [] := rfl
@[grind] lemma orderFold_cons (t : OrderTerm) (ts : List OrderTerm) :
    orderFold (t :: ts) = (if t.isRef then [] else t.cols) ++ orderFold ts := rfl

/- The full grouping set: the grouping base, then the selected columns, then —
   only when the ordering was requested explicitly rather than derived from the
   model's default ordering — the ordering-term columns, then the filter
   columns. The single behavioural distinction this routine must honour is that
   a default-ordering-derived ordering contributes NO columns to the grouping
   set: its terms exist only to sort rows, never to widen the grouping. -/
def groupingSet (baseCols selectCols : List Int) (orderTerms : List OrderTerm)
    (havingCols : List Int) (metaOrdering : Bool) : List Int :=
  baseCols ++ selectCols
    ++ (if metaOrdering then [] else orderFold orderTerms)
    ++ havingCols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the columns a row-grouping clause must contain. The set is built by
   concatenating four contributions, in order:

   - `baseCols`    — the explicit grouping base (the minimal set to group by);
   - `selectCols`  — the selected columns that are not reachable purely by
                     reference (already pruned by the caller);
   - the ordering-term columns — but ONLY when `metaOrdering` is `false`, i.e.
                     when the ordering was requested explicitly. When the
                     ordering is derived from the model's default ordering
                     (`metaOrdering = true`), it contributes nothing: its terms
                     order the rows without widening the grouping;
   - `havingCols`  — the columns required by row-filtering predicates.

   All five parameters are read-only (none is `mut`): the routine builds a fresh
   result and mutates none of them (directive 5). The result is the assembled
   column list, in contribution order (later de-duplication is observationally
   the identity on which columns are present and is performed downstream). -/
method groupingColumns (baseCols : List Int) (selectCols : List Int)
    (orderTerms : List OrderTerm) (havingCols : List Int) (metaOrdering : Bool)
    return (out : List Int)
  ensures out = groupingSet baseCols selectCols orderTerms havingCols metaOrdering
  ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
  do
    -- impl-start
    -- Collect the ordering-term contributions (reference terms contribute
    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
    -- per loop step.
    let mut order : List Int := []
    let mut i := orderTerms.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ orderTerms.length
      invariant order = orderFold (orderTerms.drop i)
      done_with i = 0
      decreasing i
    do
      let t := orderTerms[i - 1]!
      order := (if t.isRef then [] else t.cols) ++ order
      i := i - 1
    -- The ordering terms widen the grouping set only when the ordering is
    -- explicit; a default-ordering-derived ordering contributes nothing.
    let orderContrib : List Int := if metaOrdering then [] else order
    return baseCols ++ selectCols ++ orderContrib ++ havingCols
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `orderFold` peels one contribution. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma orderFold_drop_step (orderTerms : List OrderTerm) (i : Nat)
    (hi : 0 < i) (hle : i ≤ orderTerms.length) :
    orderFold (orderTerms.drop (i - 1)) =
      (if (orderTerms[i - 1]!).isRef then [] else (orderTerms[i - 1]!).cols)
        ++ orderFold (orderTerms.drop i) := by
  have hlt : i - 1 < orderTerms.length := by omega
  have hcons : orderTerms.drop (i - 1) = orderTerms[i - 1]! :: orderTerms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, orderFold_cons]

prove_correct groupingColumns by
  loom_solve
  · rw [orderFold_drop_step orderTerms i (by omega) (by omega)]
    simp_all
  all_goals simp_all [groupingSet]
```

Prepatch bug re-encoded as an attack: `True`.

Bundle has NO axioms (mapping.md §3, G-AX=skip): every dependency (per-term cols/isRef, baseCols/selectCols/havingCols, metaOrdering) is an explicit observable input; the changed op (the `not self._meta_ordering` guard) is modeled DEEPLY as groupingSet's `if metaOrdering` guard (refinement.md step 4, tagged I). No A-reference deep model exists to attack; no kind-3 step. So the A-leg attack surface reduces to the model↔patch correspondence + whether the pinned postcondition admits a behavior-differing verifying impl.

Same-spec confirmed True (swebench_unified.markers.same_spec, velvet) for pos_control, atk_prepatch, and atk1-atk7. Verified with `bash scripts/lean_verify.sh <f>` (run concurrently, ≤4 at a time):
- pos_control.lean (gold impl): EXIT 0 (verifies) — positive control.
- atk_prepatch.lean (order columns appended UNCONDITIONALLY, no metaOrdering guard — the reported bug): EXIT 1 (fails on clause `metaOrdering=true → out = base++select++having`). Prepatch bug reproduced.
- atk1 (partial-domain: never includes order columns, returns base++select++having always): EXIT 1.
- atk2 (boundary off-by-one: loop `while i>1`, drops first ordering term's contribution): EXIT 1.
- atk3 (control-flow-effect: order contribution placed BEFORE selectCols): EXIT 1.
- atk4 (ungrounded: reference/isRef terms wrongly contribute their columns, ignores isRef): EXIT 1.
- atk6 (inverted guard: contributes order columns when metaOrdering=TRUE instead of false): EXIT 1.
- atk7 (drops havingCols entirely): EXIT 1.
- atk5 (ungrounded-oracle ECHO: returns `groupingSet baseCols selectCols orderTerms havingCols metaOrdering` verbatim): EXIT 0 (VERIFIES).

Only the echo verifies, because the postcondition `out = groupingSet ...` pins the output list exactly — any behavior-differing impl fails prove_correct. Per protocol, atk5's faithful refined patch was materialized (behaviorally identical to groupingSet, which mapping.md refines exactly to the gold-patched get_group_by ⇒ faithful patch == the verbatim gold patch, byte-confirmed identical to the frozen dataset row's patch) and RUN through the official harness:
  run_resolve('django__django-14122', <atk5 faithful patch>) → RESOLVED: True, COMPLETED: True, ATTEMPTS: 1 (run_id sbu-audit-eq-9ho69lan-atk5b). Also confirmed via direct `python -m swebench_unified.run_evaluation` under `docker`: Instances resolved: 1, ✓=1. (First run_resolve attempt returned COMPLETED:False 'no report' — a transient first-touch/HF-metadata race; the warm re-run completed and resolved.)

Since the sole verifying same-spec impl's faithful patch RESOLVES, verify does NOT diverge from correct here; the echo resolving is not a weakness (G-PANEL-1 policy). refinement.md audit: 6 legs all R or I, no kind-3, no axioms; A-leg correspondence vacuously holds (no A-legs). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk6.lean`, `atk7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The grouping-column set is assembled from contributions
-- that are explicit, observable inputs of the routine: the grouping base, the
-- selected columns (already pruned of those reachable by reference), the
-- ordering terms, and the filter columns. The per-term column lists are taken
-- as given (each term already carries the columns it would contribute and a
-- flag marking it as a mere reference to the selected set); the routine does
-- not recompute them, so there is no unchanged library callee whose contract
-- the proof must assume. The whole decision is modeled DEEPLY over these inputs.
-- axioms-end

-- pure-start
/- One ordering term, abstracted to exactly the two facts that decide its
   contribution to the grouping set: the columns it would contribute
   (`cols`), and whether it is merely a reference back into the selected set
   (`isRef`). A term that is a reference contributes nothing — its columns are
   already part of the grouping set by virtue of being selected. -/
structure OrderTerm where
  cols : List Int
  isRef : Bool
deriving Inhabited

/- The grouping columns contributed by the ordering terms: each term that is
   NOT a back-reference contributes its columns, in order; a reference term
   contributes nothing. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern). -/
def orderFold : List OrderTerm → List Int
  | []      => []
  | t :: ts => (if t.isRef then [] else t.cols) ++ orderFold ts

@[grind] lemma orderFold_nil : orderFold [] = [] := rfl
@[grind] lemma orderFold_cons (t : OrderTerm) (ts : List OrderTerm) :
    orderFold (t :: ts) = (if t.isRef then [] else t.cols) ++ orderFold ts := rfl

/- The full grouping set: the grouping base, then the selected columns, then —
   only when the ordering was requested explicitly rather than derived from the
   model's default ordering — the ordering-term columns, then the filter
   columns. The single behavioural distinction this routine must honour is that
   a default-ordering-derived ordering contributes NO columns to the grouping
   set: its terms exist only to sort rows, never to widen the grouping. -/
def groupingSet (baseCols selectCols : List Int) (orderTerms : List OrderTerm)
    (havingCols : List Int) (metaOrdering : Bool) : List Int :=
  baseCols ++ selectCols
    ++ (if metaOrdering then [] else orderFold orderTerms)
    ++ havingCols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the columns a row-grouping clause must contain. The set is built by
   concatenating four contributions, in order:

   - `baseCols`    — the explicit grouping base (the minimal set to group by);
   - `selectCols`  — the selected columns that are not reachable purely by
                     reference (already pruned by the caller);
   - the ordering-term columns — but ONLY when `metaOrdering` is `false`, i.e.
                     when the ordering was requested explicitly. When the
                     ordering is derived from the model's default ordering
                     (`metaOrdering = true`), it contributes nothing: its terms
                     order the rows without widening the grouping;
   - `havingCols`  — the columns required by row-filtering predicates.

   All five parameters are read-only (none is `mut`): the routine builds a fresh
   result and mutates none of them (directive 5). The result is the assembled
   column list, in contribution order (later de-duplication is observationally
   the identity on which columns are present and is performed downstream). -/
method groupingColumns (baseCols : List Int) (selectCols : List Int)
    (orderTerms : List OrderTerm) (havingCols : List Int) (metaOrdering : Bool)
    return (out : List Int)
  ensures out = groupingSet baseCols selectCols orderTerms havingCols metaOrdering
  ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
  do
    -- impl-start
    -- Collect the ordering-term contributions (reference terms contribute
    -- nothing) into `order`, built back-to-front so one fold unfold is exposed
    -- per loop step.
    let mut order : List Int := []
    let mut i := orderTerms.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ orderTerms.length
      invariant order = orderFold (orderTerms.drop i)
      done_with i = 0
      decreasing i
    do
      let t := orderTerms[i - 1]!
      order := (if t.isRef then [] else t.cols) ++ order
      i := i - 1
    -- The ordering terms widen the grouping set only when the ordering is
    -- explicit; a default-ordering-derived ordering contributes nothing.
    let orderContrib : List Int := if metaOrdering then [] else order
    return baseCols ++ selectCols ++ orderContrib ++ havingCols
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `orderFold` peels one contribution. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma orderFold_drop_step (orderTerms : List OrderTerm) (i : Nat)
    (hi : 0 < i) (hle : i ≤ orderTerms.length) :
    orderFold (orderTerms.drop (i - 1)) =
      (if (orderTerms[i - 1]!).isRef then [] else (orderTerms[i - 1]!).cols)
        ++ orderFold (orderTerms.drop i) := by
  have hlt : i - 1 < orderTerms.length := by omega
  have hcons : orderTerms.drop (i - 1) = orderTerms[i - 1]! :: orderTerms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, orderFold_cons]

prove_correct groupingColumns by
  loom_solve
  · rw [orderFold_drop_step orderTerms i (by omega) (by omega)]
    simp_all
  all_goals simp_all [groupingSet]
```

Prepatch bug re-encoded as an attack: `True`.

Bundle has NO axioms (mapping.md §3, G-AX=skip): every dependency (per-term cols/isRef, baseCols/selectCols/havingCols, metaOrdering) is an explicit observable input; the changed op (the `not self._meta_ordering` guard) is modeled DEEPLY as groupingSet's `if metaOrdering` guard (refinement.md step 4, tagged I). No A-reference deep model exists to attack; no kind-3 step. So the A-leg attack surface reduces to the model↔patch correspondence + whether the pinned postcondition admits a behavior-differing verifying impl.

Same-spec confirmed True (swebench_unified.markers.same_spec, velvet) for pos_control, atk_prepatch, and atk1-atk7. Verified with `bash scripts/lean_verify.sh <f>` (run concurrently, ≤4 at a time):
- pos_control.lean (gold impl): EXIT 0 (verifies) — positive control.
- atk_prepatch.lean (order columns appended UNCONDITIONALLY, no metaOrdering guard — the reported bug): EXIT 1 (fails on clause `metaOrdering=true → out = base++select++having`). Prepatch bug reproduced.
- atk1 (partial-domain: never includes order columns, returns base++select++having always): EXIT 1.
- atk2 (boundary off-by-one: loop `while i>1`, drops first ordering term's contribution): EXIT 1.
- atk3 (control-flow-effect: order contribution placed BEFORE selectCols): EXIT 1.
- atk4 (ungrounded: reference/isRef terms wrongly contribute their columns, ignores isRef): EXIT 1.
- atk6 (inverted guard: contributes order columns when metaOrdering=TRUE instead of false): EXIT 1.
- atk7 (drops havingCols entirely): EXIT 1.
- atk5 (ungrounded-oracle ECHO: returns `groupingSet baseCols selectCols orderTerms havingCols metaOrdering` verbatim): EXIT 0 (VERIFIES).

Only the echo verifies, because the postcondition `out = groupingSet ...` pins the output list exactly — any behavior-differing impl fails prove_correct. Per protocol, atk5's faithful refined patch was materialized (behaviorally identical to groupingSet, which mapping.md refines exactly to the gold-patched get_group_by ⇒ faithful patch == the verbatim gold patch, byte-confirmed identical to the frozen dataset row's patch) and RUN through the official harness:
  run_resolve('django__django-14122', <atk5 faithful patch>) → RESOLVED: True, COMPLETED: True, ATTEMPTS: 1 (run_id sbu-audit-eq-9ho69lan-atk5b). Also confirmed via direct `python -m swebench_unified.run_evaluation` under `docker`: Instances resolved: 1, ✓=1. (First run_resolve attempt returned COMPLETED:False 'no report' — a transient first-touch/HF-metadata race; the warm re-run completed and resolved.)

Since the sole verifying same-spec impl's faithful patch RESOLVES, verify does NOT diverge from correct here; the echo resolving is not a weakness (G-PANEL-1 policy). refinement.md audit: 6 legs all R or I, no kind-3, no axioms; A-leg correspondence vacuously holds (no A-legs). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identity confirmed: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True (axioms/pure/pre/post regions frozen; only impl+proof differ, as required for the G-DIFF prepatch variant).

Faithfulness verified by differential testing the modeled groupingSet/orderFold (transliterated) against the REAL gold-patched SQLCompiler.get_group_by (django/db/models/sql/compiler.py, patch.diff applied cleanly at base_commit bc04941bf8):
  - Pinned G-CONF (100,012 inputs, seed=14122): 0 disagreements (re-ran independently against the gold worktree).
  - Independent exhaustive attack (93,184 cases): ids {0,1,2}, up to 3 order terms with all is_ref polarities, all base/select/having/meta combinations: 0 disagreements.

Boundary probes all consistent (spec is neither too strong nor drifting):
  - metaOrdering=true drops the order contribution exactly matching `if not self._meta_ordering`; empty-list _meta_ordering (falsy) -> order contributes (mapping.md §2 truthy<->true bijection holds).
  - is_ref order terms contribute nothing on both sides.
  - set-observable is exact: dedup-by-(sql,params_hash) with empty params + unique sql per column id == set of column ids; collapse_group_by under base features (allows_group_by_pk=allows_group_by_selected_pks=False, the real sqlite/base default) is identity and is untouched by the patch.
  - group_by None/True fast-paths are outside the modeled list domain and are unchanged by the patch (not part of the discriminating change), so their omission from the model is a legitimate scope boundary, not a strengthening.

The secondary postcondition `metaOrdering = true -> out = baseCols ++ selectCols ++ havingCols` is a logical consequence of the primary `out = groupingSet ...` clause (groupingSet collapses the order term to [] when metaOrdering=true), so it adds no over-constraint. No input was found on which the modeled function disagrees with the real callee over the modeled domain and the declared set observation. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes cleanly (leakage.screen: no hard failures, no warnings). same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region byte-identical, confirming a frozen shared spec. Semantic review: the spec view's discriminating content — parameter `metaOrdering : Bool`, the clause `if metaOrdering then [] else orderFold orderTerms`, and postcondition `metaOrdering = true → out = baseCols ++ selectCols ++ havingCols` — restates behavior already PUBLIC in the problem_statement, which explicitly says 'Meta.ordering fields must not be included in GROUP BY clause' and that the prior commit 'still populates GROUP BY with Meta.ordering fields'. `metaOrdering` maps to `self._meta_ordering` (i.e. Meta.ordering), named verbatim in the public statement. The spec view does NOT reveal the gold edit beyond the problem statement: it does not name the patched file (django/db/models/sql/compiler.py), does not name the patched method (get_group_by — abstracted as `groupingColumns` over explicit inputs), reproduces no gold-patch line, carries no diff markers, and contains no pre-patch/fix narration. The behavioral gate the spec encodes is exactly the publicly requested behavior, not a leak of the code-level edit. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
