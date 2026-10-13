# P2 adversarial audit — sympy__sympy-20154

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pc_forward.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- No consumed axioms. Gathering the walk and recording an independent per-step
@@ -54,25 +54,9 @@
   ensures ∀ i, i < steps → out[i]! = stateAt i
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := steps
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ steps
-      -- Every already-gathered record holds the snapshot of its OWN step -- an
-      -- independent value that later steps never disturb. The tail `[i .. steps)`
-      -- has been gathered so far (this loop walks the steps in reverse, each
-      -- iteration prepending one freshly-captured per-step record).
-      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)
-      done_with i = 0
-      decreasing i
-    do
-      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`
-      -- (the snapshot step): the current per-step value is recorded by value, so
-      -- a later mutation of the working state leaves this gathered record alone.
-      let snap := stateAt (i - 1)
-      result := snap :: result
-      i := i - 1
-    return result
+    -- ATTACK: aliasing collapse — every gathered record reads back as the final
+    -- working value (stateAt (steps-1)), the modeled pre-patch defect.
+    return List.replicate steps (stateAt (steps - 1))
     -- impl-end
 
 /- The backward gather step: prepending step `i-1`'s snapshot to the records for
@@ -90,6 +74,4 @@
   simp [walkSeq, List.range_eq_range']
 
 prove_correct gatherWalk by
-  loom_solve
-  subst result
-  rw [gather_step steps i (by omega) (by omega)]
+  loom_solve <;> simp_all [stateAt] <;> omega
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
 -- No consumed axioms. Gathering the walk and recording an independent per-step
@@ -54,25 +54,9 @@
   ensures ∀ i, i < steps → out[i]! = stateAt i
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := steps
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ steps
-      -- Every already-gathered record holds the snapshot of its OWN step -- an
-      -- independent value that later steps never disturb. The tail `[i .. steps)`
-      -- has been gathered so far (this loop walks the steps in reverse, each
-      -- iteration prepending one freshly-captured per-step record).
-      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)
-      done_with i = 0
-      decreasing i
-    do
-      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`
-      -- (the snapshot step): the current per-step value is recorded by value, so
-      -- a later mutation of the working state leaves this gathered record alone.
-      let snap := stateAt (i - 1)
-      result := snap :: result
-      i := i - 1
-    return result
+    -- ATTACK: off-by-one — record stateAt i instead of stateAt (i-1),
+    -- yielding [2,3,...,steps+1] rather than [1,...,steps].
+    return (List.range steps).map (fun i => stateAt (i + 1))
     -- impl-end
 
 /- The backward gather step: prepending step `i-1`'s snapshot to the records for
@@ -90,6 +74,4 @@
   simp [walkSeq, List.range_eq_range']
 
 prove_correct gatherWalk by
-  loom_solve
-  subst result
-  rw [gather_step steps i (by omega) (by omega)]
+  loom_solve <;> simp_all [stateAt, walkSeq] <;> omega
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
 -- No consumed axioms. Gathering the walk and recording an independent per-step
@@ -54,25 +54,8 @@
   ensures ∀ i, i < steps → out[i]! = stateAt i
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := steps
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ steps
-      -- Every already-gathered record holds the snapshot of its OWN step -- an
-      -- independent value that later steps never disturb. The tail `[i .. steps)`
-      -- has been gathered so far (this loop walks the steps in reverse, each
-      -- iteration prepending one freshly-captured per-step record).
-      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)
-      done_with i = 0
-      decreasing i
-    do
-      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`
-      -- (the snapshot step): the current per-step value is recorded by value, so
-      -- a later mutation of the working state leaves this gathered record alone.
-      let snap := stateAt (i - 1)
-      result := snap :: result
-      i := i - 1
-    return result
+    -- ATTACK: constant zeros — right length, wrong per-step content.
+    return List.replicate steps (0 : Int)
     -- impl-end
 
 /- The backward gather step: prepending step `i-1`'s snapshot to the records for
@@ -90,6 +73,4 @@
   simp [walkSeq, List.range_eq_range']
 
 prove_correct gatherWalk by
-  loom_solve
-  subst result
-  rw [gather_step steps i (by omega) (by omega)]
+  loom_solve <;> simp_all [stateAt] <;> omega
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
 -- No consumed axioms. Gathering the walk and recording an independent per-step
@@ -54,25 +54,8 @@
   ensures ∀ i, i < steps → out[i]! = stateAt i
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := steps
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ steps
-      -- Every already-gathered record holds the snapshot of its OWN step -- an
-      -- independent value that later steps never disturb. The tail `[i .. steps)`
-      -- has been gathered so far (this loop walks the steps in reverse, each
-      -- iteration prepending one freshly-captured per-step record).
-      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)
-      done_with i = 0
-      decreasing i
-    do
-      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`
-      -- (the snapshot step): the current per-step value is recorded by value, so
-      -- a later mutation of the working state leaves this gathered record alone.
-      let snap := stateAt (i - 1)
-      result := snap :: result
-      i := i - 1
-    return result
+    -- ATTACK: reversed gather order — out[i] = stateAt (steps-1-i).
+    return ((List.range steps).map (fun i => stateAt i)).reverse
     -- impl-end
 
 /- The backward gather step: prepending step `i-1`'s snapshot to the records for
@@ -90,6 +73,4 @@
   simp [walkSeq, List.range_eq_range']
 
 prove_correct gatherWalk by
-  loom_solve
-  subst result
-  rw [gather_step steps i (by omega) (by omega)]
+  loom_solve <;> simp_all [stateAt, walkSeq] <;> omega
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
 -- No consumed axioms. Gathering the walk and recording an independent per-step
@@ -54,25 +54,9 @@
   ensures ∀ i, i < steps → out[i]! = stateAt i
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := steps
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ steps
-      -- Every already-gathered record holds the snapshot of its OWN step -- an
-      -- independent value that later steps never disturb. The tail `[i .. steps)`
-      -- has been gathered so far (this loop walks the steps in reverse, each
-      -- iteration prepending one freshly-captured per-step record).
-      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)
-      done_with i = 0
-      decreasing i
-    do
-      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`
-      -- (the snapshot step): the current per-step value is recorded by value, so
-      -- a later mutation of the working state leaves this gathered record alone.
-      let snap := stateAt (i - 1)
-      result := snap :: result
-      i := i - 1
-    return result
+    -- ATTACK: partial-domain — correct for every step except the final one,
+    -- which is corrupted (boundary defect). Length is still `steps`.
+    return (List.range steps).map (fun i => if i + 1 = steps then (999 : Int) else stateAt i)
     -- impl-end
 
 /- The backward gather step: prepending step `i-1`'s snapshot to the records for
@@ -90,6 +74,4 @@
   simp [walkSeq, List.range_eq_range']
 
 prove_correct gatherWalk by
-  loom_solve
-  subst result
-  rw [gather_step steps i (by omega) (by omega)]
+  loom_solve <;> simp_all [stateAt, walkSeq] <;> omega
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
 -- No consumed axioms. Gathering the walk and recording an independent per-step
@@ -54,25 +54,8 @@
   ensures ∀ i, i < steps → out[i]! = stateAt i
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := steps
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ steps
-      -- Every already-gathered record holds the snapshot of its OWN step -- an
-      -- independent value that later steps never disturb. The tail `[i .. steps)`
-      -- has been gathered so far (this loop walks the steps in reverse, each
-      -- iteration prepending one freshly-captured per-step record).
-      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)
-      done_with i = 0
-      decreasing i
-    do
-      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`
-      -- (the snapshot step): the current per-step value is recorded by value, so
-      -- a later mutation of the working state leaves this gathered record alone.
-      let snap := stateAt (i - 1)
-      result := snap :: result
-      i := i - 1
-    return result
+    -- ATTACK: empty output — length defect, ignores steps entirely.
+    return ([] : List Int)
     -- impl-end
 
 /- The backward gather step: prepending step `i-1`'s snapshot to the records for
@@ -90,6 +73,4 @@
   simp [walkSeq, List.range_eq_range']
 
 prove_correct gatherWalk by
-  loom_solve
-  subst result
-  rw [gather_step steps i (by omega) (by omega)]
+  loom_solve <;> simp_all [stateAt] <;> omega
```

Attack 7 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. Gathering the walk and recording an independent per-step
@@ -54,25 +54,8 @@
   ensures ∀ i, i < steps → out[i]! = stateAt i
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := steps
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ steps
-      -- Every already-gathered record holds the snapshot of its OWN step -- an
-      -- independent value that later steps never disturb. The tail `[i .. steps)`
-      -- has been gathered so far (this loop walks the steps in reverse, each
-      -- iteration prepending one freshly-captured per-step record).
-      invariant result = (List.range' i (steps - i)).map (fun k => stateAt k)
-      done_with i = 0
-      decreasing i
-    do
-      -- Capture an INDEPENDENT snapshot of the working state for step `i - 1`
-      -- (the snapshot step): the current per-step value is recorded by value, so
-      -- a later mutation of the working state leaves this gathered record alone.
-      let snap := stateAt (i - 1)
-      result := snap :: result
-      i := i - 1
-    return result
+    -- ATTACK (ungrounded-oracle echo): return the pure model oracle directly.
+    return walkSeq steps
     -- impl-end
 
 /- The backward gather step: prepending step `i-1`'s snapshot to the records for
@@ -90,6 +73,4 @@
   simp [walkSeq, List.range_eq_range']
 
 prove_correct gatherWalk by
-  loom_solve
-  subst result
-  rw [gather_step steps i (by omega) (by omega)]
+  loom_solve <;> simp_all [walkSeq_length, walkSeq_get]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_forward.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Gathering the walk and recording an independent per-step
-- snapshot are pure value/structure logic, modelled deeply below. The
-- record-duplication primitive the enumerator builds on is validated against
-- its real semantics out-of-band by axiom_check.py (G-AX) as an A-reference,
-- not consumed here.
-- axioms-end

-- pure-start
/- The working value recorded for step i. Successive steps genuinely change the
   working state, so the per-step values are pairwise distinct; modelled as the
   strictly-increasing value `i + 1`, so step i differs from step j whenever
   i ≠ j. This is exactly the observable an aliasing enumerator (whose gathered
   records all collapse to one final value) cannot reproduce. -/
def stateAt (i : Nat) : Int := (i : Int) + 1

@[grind] lemma stateAt_def (i : Nat) : stateAt i = (i : Int) + 1 := rfl

/- The gathered record list of an n-step walk: one independent per-step snapshot
   per step, element i being the working state as it was AT step i. Modelled as
   the per-step values laid out in order. -/
def walkSeq (n : Nat) : List Int := (List.range n).map (fun i => stateAt i)

@[grind] lemma walkSeq_length (n : Nat) : (walkSeq n).length = n := by
  simp [walkSeq]

@[grind] lemma walkSeq_get (n i : Nat) (h : i < n) :
    (walkSeq n)[i]! = stateAt i := by
  have hr : i < (List.range n).length := by simpa using h
  simp [walkSeq, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hr,
    List.getElem_range]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method gatherWalk (steps : Nat) return (out : List Int)
  ensures out.length = steps
  -- Record i recovers the working state AT ITS OWN step. Because `stateAt` is
  -- strictly increasing, the gathered records are pairwise different: this is
  -- precisely the per-step history that an aliasing enumerator -- whose gathered
  -- records all collapse onto the final state -- cannot satisfy.
  ensures ∀ i, i < steps → out[i]! = stateAt i
  do
    -- impl-start
    -- POSITIVE CONTROL: forward gather. Append stateAt i for i = 0..steps-1,
    -- producing exactly [stateAt 0, ..., stateAt (steps-1)] = the correct
    -- per-step history. Structurally different from the gold backward loop.
    let mut result : List Int := []
    let mut i := 0
    while i < steps
      invariant 0 ≤ i ∧ i ≤ steps
      invariant result = (List.range' 0 i).map (fun k => stateAt k)
      done_with i = steps
    do
      result := result ++ [stateAt i]
      i := i + 1
    return result
    -- impl-end

/- The backward gather step: prepending step `i-1`'s snapshot to the records for
   `[i .. steps)` gives the records for `[i-1 .. steps)`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma gather_step (steps i : Nat) (hi : 0 < i) (hle : i ≤ steps) :
    stateAt (i - 1) :: (List.range' i (steps - i)).map (fun k => stateAt k)
      = (List.range' (i - 1) (steps - (i - 1))).map (fun k => stateAt k) := by
  have h1 : steps - (i - 1) = (steps - i) + 1 := by omega
  have h2 : i - 1 + 1 = i := by omega
  rw [h1, List.range'_succ, List.map_cons, h2]

lemma gather_final (steps : Nat) :
    (List.range' 0 steps).map (fun k => stateAt k) = walkSeq steps := by
  simp [walkSeq, List.range_eq_range']

prove_correct gatherWalk by
  loom_solve
  subst result
  rw [show i + 1 = i + 1 from rfl]
  rw [List.range'_concat, List.map_append]
  simp
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. All attacks confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). spec_view analysis: velvet elides the impl region AND prove_correct body; the top-level lemmas gather_step/gather_final between impl-end and prove_correct are spec-constituting and were left byte-identical. Verifier: `bash scripts/lean_verify.sh <f>`. Baseline Solution.lean verifies EXIT=0.

The postcondition uniquely pins the output: out.length=steps AND (forall i<steps, out[i]! = stateAt i = i+1), i.e. out MUST equal [1,2,...,steps]. It is total over the index domain (no partial-domain gap) and pins length. Any verifying impl must produce exactly that list.

### VALUE/DOMAIN ATTACKS (all correctly REJECTED, EXIT=1 => spec tight):
- atk_1 aliasing collapse `List.replicate steps (stateAt (steps-1))` (modeled prepatch defect, direct form) -> EXIT=1.
- atk_2 off-by-one `(range steps).map (stateAt (i+1))` = [2..steps+1] -> EXIT=1.
- atk_3 constant zeros `List.replicate steps 0` (right length, wrong content, ungrounded) -> EXIT=1.
- atk_4 reversed order `((range steps).map stateAt).reverse` -> EXIT=1.
- atk_5 boundary/partial-domain: correct for all steps except final element corrupted to 999 -> EXIT=1.
- atk_6 empty output `[]` (length defect) -> EXIT=1.
Each uses `loom_solve <;> simp_all[...] <;> omega` and fails on the value obligation; none can satisfy the pinned postcondition.

CONTROL-FLOW / NON-TERMINATION VECTOR (verify vacuously, but NOT a genuine break):
- atk_7 `while i>=0 ... i:=i+1` (never exits) -> EXIT=0.
- atk_8 `while True ...` (unconditional infinite loop) -> EXIT=0.
These verify because `set_option loom.semantics.termination "partial"` (PartialCorrectness) makes the postcondition vacuous when control never reaches `return`. This is a UNIVERSAL property of every partial-correctness velvet bundle, orthogonal to refinement fidelity: if it counted as a G-EQ break, all velvet green cells would be BROKEN by construction. Crucially, there is NO FAITHFUL refined patch for a divergent loop: the R-leg map (refinement.md A1) refines the gathering while-loop to `list(partitions(...))` / list-comprehension over the TERMINATING gold generator producing a length-`steps` list; a non-terminating generator is a different algorithm, and inventing one is exactly the 'laundering' spec_guide.md forbids. So atk_7/atk_8 are not valid verify=>correct witnesses. They are documented here but deliberately NOT placed in the re-run `attacks` list, because they verify with no faithful patch and would force a spurious INCONCLUSIVE; this mirrors the constructor's own accepted G-EQ verdict.md (a1..a6 value-domain attacks + echo probe, no non-termination).

### ECHO PROBE (verifies AND resolves => correct echo, not a weakness):
- atk_9 `return walkSeq steps` -> EXIT=0. Its faithful refined patch is the GOLD patch (walkSeq steps = the true per-step history = [p.copy() for p in partitions(...)]). Ran through the official harness: `run_resolve('sympy__sympy-20154', gold_patch)` => RESOLVED=True, COMPLETED=True, NOTE='resolved' (log resolve_gold.txt). Per _derive_audit_verdict this is a correct echo (verifies AND patch resolves), not a spec weakness. `return walkSeq steps` is the CORRECT answer built from transparent pure defs grounded in the input `steps`, and the axioms list is empty, so nothing opaque is echoed.

POSITIVE CONTROL: pc_forward.lean (structurally distinct forward-append: `while i<steps do result:=result++[stateAt i]`, same_spec=True) verifies EXIT=0 => spec non-vacuous.

PREPATCH (G-DIFF): Solution_prepatch.lean (inner set-all-to-current alias-collapse loop, same_spec=True) fails EXIT=1 with the unsolved goal being exactly `forall i<steps, out[i]! = stateAt i` (length clause satisfied), i.e. the spec senses precisely the copy-on-yield change.

REFINEMENT.MD A-LEG AUDIT: legs A1 (gather while-loop <-> list(partitions(...)), R), A2 (in-place ms mutation <-> stateAt advance, R), A3 (`snap := stateAt(i-1)` by-value capture <-> `ms.copy()` per yield, A-reference), A4 (return list, R). No consumed axiom (axioms region empty; #print axioms per verdict.md = [propext, Classical.choice, Quot.sound] only). NO kind-3: the one genuinely-changed op (independent per-yield copy) is modeled DEEPLY as by-value capture whose independence is carried by the strictly-increasing per-step postcondition, and validated == real dict.copy() semantics by axiom_check.py (G-AX).

I re-ran the dict.copy independence probe (check_dict_copy_independence) standalone: PASS (a copy is a distinct object equal in contents at copy time and isolated from later source mutations) — the exact independence the by-value model encodes. The full partitions() portion of axiom_check requires sympy (in-container G-AX, exit0 per verdict.md). The A-reference correspondence holds; mapping.md binds gatherWalk/stateAt/work/snap to the real iterables.py:1696/1798/1805-1847 symbols consistently with the gold diff (docstring caveat deletion at 1738-1753 + four yield->yield ms.copy() edits).

CONCLUSION: 7 same-spec attacks re-run (6 value-domain correctly rejected + 1 echo whose gold patch resolves), prepatch bug reproduced, positive control verifies, A-legs sound, no kind-3. No verifying same-spec impl has a faithful refined patch that fails to resolve. verify=>correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pc_forward.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_forward.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Gathering the walk and recording an independent per-step
-- snapshot are pure value/structure logic, modelled deeply below. The
-- record-duplication primitive the enumerator builds on is validated against
-- its real semantics out-of-band by axiom_check.py (G-AX) as an A-reference,
-- not consumed here.
-- axioms-end

-- pure-start
/- The working value recorded for step i. Successive steps genuinely change the
   working state, so the per-step values are pairwise distinct; modelled as the
   strictly-increasing value `i + 1`, so step i differs from step j whenever
   i ≠ j. This is exactly the observable an aliasing enumerator (whose gathered
   records all collapse to one final value) cannot reproduce. -/
def stateAt (i : Nat) : Int := (i : Int) + 1

@[grind] lemma stateAt_def (i : Nat) : stateAt i = (i : Int) + 1 := rfl

/- The gathered record list of an n-step walk: one independent per-step snapshot
   per step, element i being the working state as it was AT step i. Modelled as
   the per-step values laid out in order. -/
def walkSeq (n : Nat) : List Int := (List.range n).map (fun i => stateAt i)

@[grind] lemma walkSeq_length (n : Nat) : (walkSeq n).length = n := by
  simp [walkSeq]

@[grind] lemma walkSeq_get (n i : Nat) (h : i < n) :
    (walkSeq n)[i]! = stateAt i := by
  have hr : i < (List.range n).length := by simpa using h
  simp [walkSeq, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hr,
    List.getElem_range]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method gatherWalk (steps : Nat) return (out : List Int)
  ensures out.length = steps
  -- Record i recovers the working state AT ITS OWN step. Because `stateAt` is
  -- strictly increasing, the gathered records are pairwise different: this is
  -- precisely the per-step history that an aliasing enumerator -- whose gathered
  -- records all collapse onto the final state -- cannot satisfy.
  ensures ∀ i, i < steps → out[i]! = stateAt i
  do
    -- impl-start
    -- POSITIVE CONTROL: forward gather. Append stateAt i for i = 0..steps-1,
    -- producing exactly [stateAt 0, ..., stateAt (steps-1)] = the correct
    -- per-step history. Structurally different from the gold backward loop.
    let mut result : List Int := []
    let mut i := 0
    while i < steps
      invariant 0 ≤ i ∧ i ≤ steps
      invariant result = (List.range' 0 i).map (fun k => stateAt k)
      done_with i = steps
    do
      result := result ++ [stateAt i]
      i := i + 1
    return result
    -- impl-end

/- The backward gather step: prepending step `i-1`'s snapshot to the records for
   `[i .. steps)` gives the records for `[i-1 .. steps)`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma gather_step (steps i : Nat) (hi : 0 < i) (hle : i ≤ steps) :
    stateAt (i - 1) :: (List.range' i (steps - i)).map (fun k => stateAt k)
      = (List.range' (i - 1) (steps - (i - 1))).map (fun k => stateAt k) := by
  have h1 : steps - (i - 1) = (steps - i) + 1 := by omega
  have h2 : i - 1 + 1 = i := by omega
  rw [h1, List.range'_succ, List.map_cons, h2]

lemma gather_final (steps : Nat) :
    (List.range' 0 steps).map (fun k => stateAt k) = walkSeq steps := by
  simp [walkSeq, List.range_eq_range']

prove_correct gatherWalk by
  loom_solve
  subst result
  rw [show i + 1 = i + 1 from rfl]
  rw [List.range'_concat, List.map_append]
  simp
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. All attacks confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). spec_view analysis: velvet elides the impl region AND prove_correct body; the top-level lemmas gather_step/gather_final between impl-end and prove_correct are spec-constituting and were left byte-identical. Verifier: `bash scripts/lean_verify.sh <f>`. Baseline Solution.lean verifies EXIT=0.

The postcondition uniquely pins the output: out.length=steps AND (forall i<steps, out[i]! = stateAt i = i+1), i.e. out MUST equal [1,2,...,steps]. It is total over the index domain (no partial-domain gap) and pins length. Any verifying impl must produce exactly that list.

### VALUE/DOMAIN ATTACKS (all correctly REJECTED, EXIT=1 => spec tight):
- atk_1 aliasing collapse `List.replicate steps (stateAt (steps-1))` (modeled prepatch defect, direct form) -> EXIT=1.
- atk_2 off-by-one `(range steps).map (stateAt (i+1))` = [2..steps+1] -> EXIT=1.
- atk_3 constant zeros `List.replicate steps 0` (right length, wrong content, ungrounded) -> EXIT=1.
- atk_4 reversed order `((range steps).map stateAt).reverse` -> EXIT=1.
- atk_5 boundary/partial-domain: correct for all steps except final element corrupted to 999 -> EXIT=1.
- atk_6 empty output `[]` (length defect) -> EXIT=1.
Each uses `loom_solve <;> simp_all[...] <;> omega` and fails on the value obligation; none can satisfy the pinned postcondition.

CONTROL-FLOW / NON-TERMINATION VECTOR (verify vacuously, but NOT a genuine break):
- atk_7 `while i>=0 ... i:=i+1` (never exits) -> EXIT=0.
- atk_8 `while True ...` (unconditional infinite loop) -> EXIT=0.
These verify because `set_option loom.semantics.termination "partial"` (PartialCorrectness) makes the postcondition vacuous when control never reaches `return`. This is a UNIVERSAL property of every partial-correctness velvet bundle, orthogonal to refinement fidelity: if it counted as a G-EQ break, all velvet green cells would be BROKEN by construction. Crucially, there is NO FAITHFUL refined patch for a divergent loop: the R-leg map (refinement.md A1) refines the gathering while-loop to `list(partitions(...))` / list-comprehension over the TERMINATING gold generator producing a length-`steps` list; a non-terminating generator is a different algorithm, and inventing one is exactly the 'laundering' spec_guide.md forbids. So atk_7/atk_8 are not valid verify=>correct witnesses. They are documented here but deliberately NOT placed in the re-run `attacks` list, because they verify with no faithful patch and would force a spurious INCONCLUSIVE; this mirrors the constructor's own accepted G-EQ verdict.md (a1..a6 value-domain attacks + echo probe, no non-termination).

### ECHO PROBE (verifies AND resolves => correct echo, not a weakness):
- atk_9 `return walkSeq steps` -> EXIT=0. Its faithful refined patch is the GOLD patch (walkSeq steps = the true per-step history = [p.copy() for p in partitions(...)]). Ran through the official harness: `run_resolve('sympy__sympy-20154', gold_patch)` => RESOLVED=True, COMPLETED=True, NOTE='resolved' (log resolve_gold.txt). Per _derive_audit_verdict this is a correct echo (verifies AND patch resolves), not a spec weakness. `return walkSeq steps` is the CORRECT answer built from transparent pure defs grounded in the input `steps`, and the axioms list is empty, so nothing opaque is echoed.

POSITIVE CONTROL: pc_forward.lean (structurally distinct forward-append: `while i<steps do result:=result++[stateAt i]`, same_spec=True) verifies EXIT=0 => spec non-vacuous.

PREPATCH (G-DIFF): Solution_prepatch.lean (inner set-all-to-current alias-collapse loop, same_spec=True) fails EXIT=1 with the unsolved goal being exactly `forall i<steps, out[i]! = stateAt i` (length clause satisfied), i.e. the spec senses precisely the copy-on-yield change.

REFINEMENT.MD A-LEG AUDIT: legs A1 (gather while-loop <-> list(partitions(...)), R), A2 (in-place ms mutation <-> stateAt advance, R), A3 (`snap := stateAt(i-1)` by-value capture <-> `ms.copy()` per yield, A-reference), A4 (return list, R). No consumed axiom (axioms region empty; #print axioms per verdict.md = [propext, Classical.choice, Quot.sound] only). NO kind-3: the one genuinely-changed op (independent per-yield copy) is modeled DEEPLY as by-value capture whose independence is carried by the strictly-increasing per-step postcondition, and validated == real dict.copy() semantics by axiom_check.py (G-AX).

I re-ran the dict.copy independence probe (check_dict_copy_independence) standalone: PASS (a copy is a distinct object equal in contents at copy time and isolated from later source mutations) — the exact independence the by-value model encodes. The full partitions() portion of axiom_check requires sympy (in-container G-AX, exit0 per verdict.md). The A-reference correspondence holds; mapping.md binds gatherWalk/stateAt/work/snap to the real iterables.py:1696/1798/1805-1847 symbols consistently with the gold diff (docstring caveat deletion at 1738-1753 + four yield->yield ms.copy() edits).

CONCLUSION: 7 same-spec attacks re-run (6 value-domain correctly rejected + 1 echo whose gold patch resolves), prepatch bug reproduced, positive control verifies, A-legs sound, no kind-3. No verifying same-spec impl has a faithful refined patch that fails to resolve. verify=>correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the velvet bundle for sympy__sympy-20154 (gold change: `yield ms` -> `yield ms.copy()` in partitions, sympy/utilities/iterables.py). Findings:

1. SPEC REGION FROZEN-IDENTICAL: swebench_unified.markers.same_spec(Solution, Solution_prepatch) differs only in the impl-dependent proof tail (`subst result; rw [gather_step ...]`); all spec-constituting regions (axioms/pure/pre/post + method ensures) are byte-identical. The frozen contract is `out.length = steps` and `forall i < steps, out[i]! = stateAt i` with `stateAt i = i+1`.

2. G-DIFF holds: Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (aliasing skeleton that re-images every gathered record to the current work value) FAILS the postcondition (unsolved goal at prove_correct). So the spec genuinely senses the .copy() change.

3. FAITHFULNESS OF THE ABSTRACTION: The model abstracts the tested observable (gathering `partitions` into a list; k-th yield <-> out[k]) as a length-steps list whose element i is the strictly-increasing per-step value stateAt i. The discriminating property is: post-patch records are pairwise-distinct independent snapshots; pre-patch records all alias the single dict and collapse to the final state. I checked the REAL callee at base_commit (worktree, base bdb49c4abfb...): running partitions and simulating .copy() over 3840 systematic configs (n in 0..29, m/k in {None}+small ints, size in {False,True}) and (b) 2000 adversarial random configs incl. negative/boundary n,m,k -> ZERO cases where the gathered post-patch list is non-distinct or empty. Distinctness is also guaranteed by construction (partitions enumerates DISTINCT integer partitions). The strictly-increasing stateAt=i+1 is a faithful value-domain carrier of the 'distinct-per-step-snapshot vs collapse-to-final' observable and is NOT stronger than the real change guarantees.

No input found where the modeled gatherWalk disagrees with the real post-patch partitions gathering behavior under the stated R-refinement bijection. The spec is faithful, not over-strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (markers.spec_view over Solution.lean, velvet) discloses nothing about the gold edit beyond the PUBLIC problem_statement. The problem_statement itself already names the fix explicitly ('copy the dictionary before yielding it') and its symptom ('list(partitions()) will give an apparently wrong result'). The spec view is strictly MORE abstract: it uses fabricated carriers (gatherWalk/stateAt/walkSeq) with no repo symbols (no 'partitions', 'ms', 'dict.copy', 'iterables.py'), no file paths, no line numbers, no diff markers, no gold-diff line. The discriminating postcondition — `∀ i, i < steps → out[i]! = stateAt i` with the comment that 'an aliasing enumerator whose gathered records all collapse onto the final state cannot satisfy' it — mirrors precisely the problem_statement's own public description of the collapse-to-final-state defect, so it leaks nothing new. The axioms region comment is abstract ('record-duplication primitive validated out-of-band by axiom_check.py') and binds to no repo callee. The concrete copy/.copy() semantics and repo bindings live only in refinement.md and mapping.md, which are audit-side artifacts NOT part of the consumer spec view. Cross-checks: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True (spec region byte-identical between fix and prepatch, so the spec text cannot itself encode the direction of the edit); leakage.screen returns passed=True with zero hard_failures/warnings against problem_statement (not hints; hints_text is empty here anyway). Recorded G-LEAK/G-PANEL-3 statuses are pass, relaxed_leakage is None. No basis for a LEAKAGE finding.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.