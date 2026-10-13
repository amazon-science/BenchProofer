# P2 adversarial audit — sympy__sympy-13551

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: INCONCLUSIVE)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No completing verify⇏ correct counterexample exists. The postcondition `ensures out = prodOfSums M` pins the output EXACTLY to a total computable pure function (prodOfSums/rowSum) with ZERO axioms and no opaque oracle, so every TERMINATING same-spec impl that verifies must return the gold value and therefore resolves. The only same-spec wrong impls that verify (atk_9, atk_10) do so via NON-TERMINATION vacuity under `loom.semantics.termination "partial"`: an always-true-guard loop (`while i>0` with `i:=1`, invariant `i=1`) leaves a contradictory post-loop state (¬(i>0) with i=1), which discharges the postcondition vacuously while the method diverges (returns 0 / no value). Their FAITHFUL refined patch must itself diverge (an infinite loop in `_eval_product`), so the mandatory resolve run does NOT complete (completed=False, no report — the harness 600s timeout kills the hung container) rather than completing with a wrong answer. Thus it is NOT a `completed ∧ ¬resolved` break (not BROKEN), but the needed resolve could not complete ⇒ INCONCLUSIVE per the rubric.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -46,18 +46,29 @@
   ensures out = prodOfSums M
   do
     -- impl-start
-    let mut acc : Rat := 1
-    let mut i := M.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ M.length
-      invariant acc = prodOfSums (M.drop i)
-      done_with i = 0
-      decreasing i
+    -- Pre-image skeleton: distributes the iterated multiplication over the
+    -- additive parts — for each part, the product of its values across every
+    -- position is taken, and those are summed. The frozen spec requires the
+    -- genuine product of positional totals (prodOfSums), so prove_correct
+    -- MUST fail whenever a position contributes more than one nonzero part.
+    let mut total : Rat := 0
+    let mut j := width
+    while j > 0
+      invariant 0 ≤ j ∧ j ≤ width
+      done_with j = 0
     do
-      let r := M[i - 1]!
-      acc := rowSum r * acc
-      i := i - 1
-    return acc
+      let mut colProd : Rat := 1
+      let mut i := M.length
+      while i > 0
+        invariant 0 ≤ i ∧ i ≤ M.length
+        done_with i = 0
+      do
+        let r := M[i - 1]!
+        colProd := r[j - 1]! * colProd
+        i := i - 1
+      total := total + colProd
+      j := j - 1
+    return total
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the position at
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -52,10 +52,9 @@
       invariant 0 ≤ i ∧ i ≤ M.length
       invariant acc = prodOfSums (M.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := M[i - 1]!
-      acc := rowSum r * acc
+      acc := rowSum r + acc
       i := i - 1
     return acc
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -46,18 +46,7 @@
   ensures out = prodOfSums M
   do
     -- impl-start
-    let mut acc : Rat := 1
-    let mut i := M.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ M.length
-      invariant acc = prodOfSums (M.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := M[i - 1]!
-      acc := rowSum r * acc
-      i := i - 1
-    return acc
+    return 1
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the position at
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -48,11 +48,10 @@
     -- impl-start
     let mut acc : Rat := 1
     let mut i := M.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ M.length
       invariant acc = prodOfSums (M.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = 1
     do
       let r := M[i - 1]!
       acc := rowSum r * acc
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -52,10 +52,9 @@
       invariant 0 ≤ i ∧ i ≤ M.length
       invariant acc = prodOfSums (M.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := M[i - 1]!
-      acc := rowSum r * acc
+      acc := r[0]! * acc
       i := i - 1
     return acc
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -52,10 +52,9 @@
       invariant 0 ≤ i ∧ i ≤ M.length
       invariant acc = prodOfSums (M.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := M[i - 1]!
-      acc := rowSum r * acc
+      acc := rowSum r * rowSum r * acc
       i := i - 1
     return acc
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -46,13 +46,12 @@
   ensures out = prodOfSums M
   do
     -- impl-start
-    let mut acc : Rat := 1
+    let mut acc : Rat := 0
     let mut i := M.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ M.length
       invariant acc = prodOfSums (M.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := M[i - 1]!
       acc := rowSum r * acc
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -52,12 +52,11 @@
       invariant 0 ≤ i ∧ i ≤ M.length
       invariant acc = prodOfSums (M.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := M[i - 1]!
       acc := rowSum r * acc
       i := i - 1
-    return acc
+    return acc + acc
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the position at
```

Attack 9 — `atk_9.lean` → not a counterexample (changed the spec)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -46,23 +46,19 @@
   ensures out = prodOfSums M
   do
     -- impl-start
-    let mut acc : Rat := 1
-    let mut i := M.length
+    let mut acc : Rat := 0
+    let mut i : Nat := 1
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ M.length
-      invariant acc = prodOfSums (M.drop i)
+      invariant i = 1
       done_with i = 0
-      decreasing i
     do
-      let r := M[i - 1]!
-      acc := rowSum r * acc
-      i := i - 1
+      acc := acc
+      i := 1
     return acc
     -- impl-end
 
-/- The backward-fold step: dropping one fewer element exposes the position at
-   `i-1` on the front, so `prodOfSums` peels one positional total. This is the
-   single goal `loom_solve` leaves for the loop body. -/
+/- The backward-fold step (unused by the vacuous proof but kept identical to
+   the bundle so the spec-view/helpers are unchanged). -/
 lemma prodOfSums_drop_step (M : List (List Rat)) (i : Nat)
     (hi : 0 < i) (hle : i ≤ M.length) :
     prodOfSums (M.drop (i - 1)) = rowSum M[i - 1]! * prodOfSums (M.drop i) := by
@@ -76,5 +72,3 @@
 
 prove_correct productOverRange by
   loom_solve
-  rw [prodOfSums_drop_step M i (by omega) (by omega)]
-  simp_all
```

Attack 10 — `atk_10.lean` → not a counterexample (changed the spec)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- axioms-end
@@ -46,23 +46,19 @@
   ensures out = prodOfSums M
   do
     -- impl-start
-    let mut acc : Rat := 1
-    let mut i := M.length
+    let mut acc : Rat := 0
+    let mut i : Nat := 1
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ M.length
-      invariant acc = prodOfSums (M.drop i)
+      invariant i = 1
       done_with i = 0
-      decreasing i
     do
-      let r := M[i - 1]!
-      acc := rowSum r * acc
-      i := i - 1
+      acc := acc + 1
+      i := 1
     return acc
     -- impl-end
 
-/- The backward-fold step: dropping one fewer element exposes the position at
-   `i-1` on the front, so `prodOfSums` peels one positional total. This is the
-   single goal `loom_solve` leaves for the loop body. -/
+/- The backward-fold step (unused by the vacuous proof but kept identical to
+   the bundle so the spec-view/helpers are unchanged). -/
 lemma prodOfSums_drop_step (M : List (List Rat)) (i : Nat)
     (hi : 0 < i) (hle : i ≤ M.length) :
     prodOfSums (M.drop (i - 1)) = rowSum M[i - 1]! * prodOfSums (M.drop i) := by
@@ -76,5 +72,3 @@
 
 prove_correct productOverRange by
   loom_solve
-  rw [prodOfSums_drop_step M i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The total of one position: the sum of the values contributed there by every
   additive part of the expression. -/
def rowSum (r : List Rat) : Rat := r.foldr (· + ·) 0

/- The value the iterated multiplication must produce over a finite range: the
   running product, across all index positions, of each position's total. Each
   element of `M` is the list of part-values at one index position; the result
   is the genuine product of those positional totals. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def prodOfSums : List (List Rat) → Rat
  | []      => 1
  | r :: rs => rowSum r * prodOfSums rs

@[grind] lemma prodOfSums_nil : prodOfSums [] = 1 := rfl
@[grind] lemma prodOfSums_cons (r : List Rat) (rs : List (List Rat)) :
    prodOfSums (r :: rs) = rowSum r * prodOfSums rs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `M` carries, for each index position of the finite range, the list of the
   `width` additive part-values contributed at that position. The result is the
   product over positions of each position's total `rowSum`. A position whose
   total is 0 is outside the modeled domain: over such a range the repository's
   symbolic result is an undefined value with no rational image, so no `Rat`
   output is claimed there. -/
method productOverRange (M : List (List Rat)) (width : Nat) return (out : Rat)
  require ∀ r ∈ M, r.length = width
  require ∀ r ∈ M, rowSum r ≠ 0
  ensures out = prodOfSums M
  do
    -- impl-start
    let mut acc : Rat := 1
    let mut i := M.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ M.length
      invariant acc = prodOfSums (M.drop i)
      done_with i = 0
    do
      let r := M[i - 1]!
      acc := rowSum r * acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the position at
   `i-1` on the front, so `prodOfSums` peels one positional total. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma prodOfSums_drop_step (M : List (List Rat)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ M.length) :
    prodOfSums (M.drop (i - 1)) = rowSum M[i - 1]! * prodOfSums (M.drop i) := by
  have hlt : i - 1 < M.length := by omega
  have hcons : M.drop (i - 1) = M[i - 1]! :: M.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, prodOfSums_cons]

prove_correct productOverRange by
  loom_solve
  rw [prodOfSums_drop_step M i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

patch.diff is not present in the bundle (gold patch obtained from the frozen dataset row and confirmed to resolve). All same_spec checks = True for every attack + positive control.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>.lean):
- positive_control.lean (gold, backward `drop` fold): EXIT 0 (verifies).
- atk_1 prepatch bug sum-of-column-products (== bundled Solution_prepatch.lean skeleton): EXIT 1, rejected on `ensures out = prodOfSums M`.
- atk_2 '+' instead of '*': EXIT 1. atk_3 `return 1` ungrounded-oracle echo: EXIT 1. atk_4 off-by-one skip position 0: EXIT 1. atk_5 M[i-1][0] instead of rowSum (partial-domain): EXIT 1. atk_6 squares each rowSum (boundary): EXIT 1. atk_7 acc init 0 (always 0): EXIT 1. atk_8 return acc+acc (scaling boundary): EXIT 1.
=> 8 DISTINCT terminating wrong impls (partial-domain, boundary, control-flow, ungrounded-oracle echo) ALL rejected. Spec is TIGHT over the terminating fragment.
- atk_9, atk_10 NON-TERMINATION vacuity: EXIT 0 (VERIFY). loom_solve closes the goal from the contradictory loop-exit state.

### RESOLVE RESULTS (swebench_unified.harness.run_resolve under `docker`, image sweb.eval.x86_64.sympy_1776_sympy-13551 present locally):
- GOLD control patch: completed=True, resolved=True (note='resolved') — pipeline validated on this instance.
- atk_9 faithful diverging patch (identical for atk_10) run with timeout=600, retries=0: completed=False, resolved=False, note='no report ... harness error' — the infinite loop hung the container until the harness timeout; NO report.json produced. This is `verify_completed`/resolve NOT completing, i.e. inconclusive_hits in _derive_audit_verdict → fail-closed INCONCLUSIVE, NOT a BROKEN (`completed ∧ ¬resolved`).

REFINEMENT AUDIT (refinement.md / mapping.md): axioms region EMPTY; NO A legs (no A-consumed, no A-reference); no kind-3; no `sorry`/`admit`/`:|`/opaque/native_decide. rowSum = foldr (+) 0 and prodOfSums are total computable pure defs. The single changed op (numerator p) is modeled DEEPLY (A3, kind=deep-model-of-changed-op) and covered by G-CONF (recorded pass: 100005 inputs seed=13551, 0 disagreements, + 60-sample literal patch-text symbolic identity exp(Sum(log(p),(k,a,n)))). Legs R1/R2 are type refinements (range↔rows, Rational↔Rat), I2 is the unchanged /q. Model↔patch correspondence holds; no kind-3 laundering.

SCOPE NOTE on the vacuity finding: non-termination vacuity is a UNIVERSAL property of EVERY partial-correctness Velvet spec (`termination "partial"` is an explicitly sanctioned mode in prompts/velvet/spec_guide.md §1.1 and is used by Velvet's own Total_Partial examples), not a defect specific to this bundle's refinement fidelity. It cannot yield a completing verify⇏correct witness because the faithful patch necessarily diverges. So this bundle exhibits NO SOUND-breaking spec-too-weak counterexample; the honest verdict is INCONCLUSIVE (the only verifying attacks' faithful patches cannot complete a resolve run), consistent with the recorded G-EQ verdict 'INCONCLUSIVE — 2 attack(s) inconclusive'.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: INCONCLUSIVE)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No completing verify⇏ correct counterexample exists. The postcondition `ensures out = prodOfSums M` pins the output EXACTLY to a total computable pure function (prodOfSums/rowSum) with ZERO axioms and no opaque oracle, so every TERMINATING same-spec impl that verifies must return the gold value and therefore resolves. The only same-spec wrong impls that verify (atk_9, atk_10) do so via NON-TERMINATION vacuity under `loom.semantics.termination "partial"`: an always-true-guard loop (`while i>0` with `i:=1`, invariant `i=1`) leaves a contradictory post-loop state (¬(i>0) with i=1), which discharges the postcondition vacuously while the method diverges (returns 0 / no value). Their FAITHFUL refined patch must itself diverge (an infinite loop in `_eval_product`), so the mandatory resolve run does NOT complete (completed=False, no report — the harness 600s timeout kills the hung container) rather than completing with a wrong answer. Thus it is NOT a `completed ∧ ¬resolved` break (not BROKEN), but the needed resolve could not complete ⇒ INCONCLUSIVE per the rubric.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → not a counterexample (changed the spec)

Attack 10 — `atk_10.lean` → not a counterexample (changed the spec)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The total of one position: the sum of the values contributed there by every
   additive part of the expression. -/
def rowSum (r : List Rat) : Rat := r.foldr (· + ·) 0

/- The value the iterated multiplication must produce over a finite range: the
   running product, across all index positions, of each position's total. Each
   element of `M` is the list of part-values at one index position; the result
   is the genuine product of those positional totals. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def prodOfSums : List (List Rat) → Rat
  | []      => 1
  | r :: rs => rowSum r * prodOfSums rs

@[grind] lemma prodOfSums_nil : prodOfSums [] = 1 := rfl
@[grind] lemma prodOfSums_cons (r : List Rat) (rs : List (List Rat)) :
    prodOfSums (r :: rs) = rowSum r * prodOfSums rs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `M` carries, for each index position of the finite range, the list of the
   `width` additive part-values contributed at that position. The result is the
   product over positions of each position's total `rowSum`. A position whose
   total is 0 is outside the modeled domain: over such a range the repository's
   symbolic result is an undefined value with no rational image, so no `Rat`
   output is claimed there. -/
method productOverRange (M : List (List Rat)) (width : Nat) return (out : Rat)
  require ∀ r ∈ M, r.length = width
  require ∀ r ∈ M, rowSum r ≠ 0
  ensures out = prodOfSums M
  do
    -- impl-start
    let mut acc : Rat := 1
    let mut i := M.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ M.length
      invariant acc = prodOfSums (M.drop i)
      done_with i = 0
    do
      let r := M[i - 1]!
      acc := rowSum r * acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the position at
   `i-1` on the front, so `prodOfSums` peels one positional total. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma prodOfSums_drop_step (M : List (List Rat)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ M.length) :
    prodOfSums (M.drop (i - 1)) = rowSum M[i - 1]! * prodOfSums (M.drop i) := by
  have hlt : i - 1 < M.length := by omega
  have hcons : M.drop (i - 1) = M[i - 1]! :: M.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, prodOfSums_cons]

prove_correct productOverRange by
  loom_solve
  rw [prodOfSums_drop_step M i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

patch.diff is not present in the bundle (gold patch obtained from the frozen dataset row and confirmed to resolve). All same_spec checks = True for every attack + positive control.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>.lean):
- positive_control.lean (gold, backward `drop` fold): EXIT 0 (verifies).
- atk_1 prepatch bug sum-of-column-products (== bundled Solution_prepatch.lean skeleton): EXIT 1, rejected on `ensures out = prodOfSums M`.
- atk_2 '+' instead of '*': EXIT 1. atk_3 `return 1` ungrounded-oracle echo: EXIT 1. atk_4 off-by-one skip position 0: EXIT 1. atk_5 M[i-1][0] instead of rowSum (partial-domain): EXIT 1. atk_6 squares each rowSum (boundary): EXIT 1. atk_7 acc init 0 (always 0): EXIT 1. atk_8 return acc+acc (scaling boundary): EXIT 1.
=> 8 DISTINCT terminating wrong impls (partial-domain, boundary, control-flow, ungrounded-oracle echo) ALL rejected. Spec is TIGHT over the terminating fragment.
- atk_9, atk_10 NON-TERMINATION vacuity: EXIT 0 (VERIFY). loom_solve closes the goal from the contradictory loop-exit state.

### RESOLVE RESULTS (swebench_unified.harness.run_resolve under `docker`, image sweb.eval.x86_64.sympy_1776_sympy-13551 present locally):
- GOLD control patch: completed=True, resolved=True (note='resolved') — pipeline validated on this instance.
- atk_9 faithful diverging patch (identical for atk_10) run with timeout=600, retries=0: completed=False, resolved=False, note='no report ... harness error' — the infinite loop hung the container until the harness timeout; NO report.json produced. This is `verify_completed`/resolve NOT completing, i.e. inconclusive_hits in _derive_audit_verdict → fail-closed INCONCLUSIVE, NOT a BROKEN (`completed ∧ ¬resolved`).

REFINEMENT AUDIT (refinement.md / mapping.md): axioms region EMPTY; NO A legs (no A-consumed, no A-reference); no kind-3; no `sorry`/`admit`/`:|`/opaque/native_decide. rowSum = foldr (+) 0 and prodOfSums are total computable pure defs. The single changed op (numerator p) is modeled DEEPLY (A3, kind=deep-model-of-changed-op) and covered by G-CONF (recorded pass: 100005 inputs seed=13551, 0 disagreements, + 60-sample literal patch-text symbolic identity exp(Sum(log(p),(k,a,n)))). Legs R1/R2 are type refinements (range↔rows, Rational↔Rat), I2 is the unchanged /q. Model↔patch correspondence holds; no kind-3 laundering.

SCOPE NOTE on the vacuity finding: non-termination vacuity is a UNIVERSAL property of EVERY partial-correctness Velvet spec (`termination "partial"` is an explicitly sanctioned mode in prompts/velvet/spec_guide.md §1.1 and is used by Velvet's own Total_Partial examples), not a defect specific to this bundle's refinement fidelity. It cannot yield a completing verify⇏correct witness because the faithful patch necessarily diverges. So this bundle exhibits NO SOUND-breaking spec-too-weak counterexample; the honest verdict is INCONCLUSIVE (the only verifying attacks' faithful patches cannot complete a resolve run), consistent with the recorded G-EQ verdict 'INCONCLUSIVE — 2 attack(s) inconclusive'.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-13551 velvet.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean, velvet-tables) = True; only the impl+proof regions differ. Solution.lean elaborates cleanly (lean_verify.sh exit 0). Spec region: method productOverRange (M: List (List Rat)) (width: Nat) require (rectangular) require (rowSum r != 0) ensures out = prodOfSums M, where prodOfSums = product over positions of each position's rowSum (total of additive parts).

MAPPING TO REAL CALLEE: the gold patch changes Product._eval_product's additive branch numerator to `p = exp(Sum(log(p), (k, a, n)))`. On a concrete integer range this equals Mul(*[p.subs(k,k0) for k0 in a..n]) = the product over positions of each position's total (p.subs(k,k0) = sum of that row's parts = rowSum). This is exactly prodOfSums M under mapping.md's bijection (range position k0=a+p <-> row M[p], part value <-> M[p][i]).

DIFFERENTIAL TESTING vs the REAL patched sympy (base_commit 9476425b9e, patched worktree, sympy 1.1-era + mpmath): I evaluated the LITERAL patched expression exp(Sum(log(p),(k,a,n))).doit() and compared to the plain iterated product (== prodOfSums) over 550+ random in-domain inputs — polynomial-in-k numerators with rational coeffs, negative totals (log goes complex), 2**k /**k exponential parts, and constants. ZERO divergences. Even-vs-odd counts of negative positional totals match (e.g. -2 constant over 3 positions -> -8; k-2 over two negatives -> +2). The issue example Product(n+1/2**k,(k,0,n-1)).subs(n,2) gives 15/2 as expected.

PRECONDITION IS AN HONEST BOUNDARY, NOT OVER-STRENGTHENING: the require `rowSum r != 0` excludes exactly the inputs where the real callee produces a NON-RATIONAL value. Confirmed: p=k-1 over 0..2 (a zero positional total) makes the real repo return exp(zoo) (log(0)=zoo), which has no Rat image — so claiming nothing there is correct, not evasive. Crucially the idealized product-of-totals would return 0 at such inputs, but the real repo does NOT return 0, so INCLUDING those inputs would make the model UNfaithful; excluding them is the faithful choice. Negative totals (where the idealized model still equals the real value) are INCLUDED and verified, so the precondition is not gratuitously narrow. Empty range: exp(Sum over empty)=1 = prodOfSums [] = 1.

CONCLUSION: No in-domain input diverges between the modeled function and the real patched callee; the modeling-domain precondition matches precisely where the real callee leaves the Rat carrier. Spec is FAITHFUL (neither too strong nor drifting). (Note: the task prompt referenced patch.diff which is absent from the bundle; refinement.md/mapping.md quote the gold hunk verbatim and it matches exactly, so the audit proceeded against the real patched worktree.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous review of the velvet spec view for sympy__sympy-13551. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Mechanical leakage.screen passes: no diff markers, no reproduced gold-patch line, patched file path sympy/concrete/products.py absent, patched symbol 'eval_product' not embedded in any spec-view identifier or comment, no narration words. Gold edit (p = sum([self._eval_product(i,(k,a,n)) for i in p.as_coeff_Add()]) -> p = exp(Sum(log(p),(k,a,n)))) is modeled abstractly as 'product over positions of each position's total' via prodOfSums/rowSum on a List (List Rat) carrier; the spec view never names exp/log/Sum/as_coeff_Add/_eval_product/q-Pochhammer. The corrected behavior (n=2 -> 15/2 vs buggy 9/2) is ALREADY in the public problem_statement, so exposing the correct product semantics is not a leak. Critically, the hints-only diagnostic ('product of a sum is the same as the sum of the products of its summands', the line-286 pointer, q-Pochhammer) is NOT echoed anywhere in the spec view (checked 'summand', 'product of a sum', 'sum of the product', 'pochhammer' — all absent). No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
