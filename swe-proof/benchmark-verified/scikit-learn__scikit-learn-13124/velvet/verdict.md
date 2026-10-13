# P2 adversarial audit — scikit-learn__scikit-learn-13124

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- The permutation a random source yields for a block of the given size, taking
@@ -84,18 +84,15 @@
   do
     -- impl-start
     let mut result : List (List Nat) := []
-    let mut prev : List Nat := []
     let mut i := 0
     while i < counts.length
       invariant i ≤ counts.length
-      invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])
+      invariant result = (counts.take i).map (fun count => shuffleAfter s [] (blockSize nSplits count))
       done_with i = counts.length
-      decreasing counts.length - i
     do
       let count := counts[i]!
       let sz := blockSize nSplits count
-      result := result ++ [shuffleAfter s prev sz]
-      prev := prev ++ [sz]
+      result := result ++ [shuffleAfter s [] sz]
       i := i + 1
     return result
     -- impl-end
@@ -103,14 +100,3 @@
 
 prove_correct perClassShuffles by
   loom_solve
-  · have hi : i < counts.length := by omega
-    have hr := congrArg Prod.fst invariant_2
-    have hp := congrArg Prod.snd invariant_2
-    simp only at hr hp
-    rw [hr, hp, threadAll_take_step nSplits s counts i hi, threadStep, blockSize]
-  · have hr := congrArg Prod.fst invariant_2
-    simp only at hr
-    have hlen : i = counts.length := done_1
-    subst hlen
-    rw [List.take_length] at hr
-    simp_all [threadAll]
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
 /- The permutation a random source yields for a block of the given size, taking
@@ -90,12 +90,11 @@
       invariant i ≤ counts.length
       invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])
       done_with i = counts.length
-      decreasing counts.length - i
     do
       let count := counts[i]!
       let sz := blockSize nSplits count
       result := result ++ [shuffleAfter s prev sz]
-      prev := prev ++ [sz]
+      prev := prev ++ [count]
       i := i + 1
     return result
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
 /- The permutation a random source yields for a block of the given size, taking
@@ -90,10 +90,9 @@
       invariant i ≤ counts.length
       invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])
       done_with i = counts.length
-      decreasing counts.length - i
     do
       let count := counts[i]!
-      let sz := blockSize nSplits count
+      let sz := count
       result := result ++ [shuffleAfter s prev sz]
       prev := prev ++ [sz]
       i := i + 1
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
 /- The permutation a random source yields for a block of the given size, taking
@@ -90,12 +90,10 @@
       invariant i ≤ counts.length
       invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])
       done_with i = counts.length
-      decreasing counts.length - i
     do
       let count := counts[i]!
       let sz := blockSize nSplits count
       result := result ++ [shuffleAfter s prev sz]
-      prev := prev ++ [sz]
       i := i + 1
     return result
     -- impl-end
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
 /- The permutation a random source yields for a block of the given size, taking
@@ -90,11 +90,10 @@
       invariant i ≤ counts.length
       invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])
       done_with i = counts.length
-      decreasing counts.length - i
     do
       let count := counts[i]!
       let sz := blockSize nSplits count
-      result := result ++ [shuffleAfter s prev sz]
+      result := [shuffleAfter s prev sz] ++ result
       prev := prev ++ [sz]
       i := i + 1
     return result
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
 /- The permutation a random source yields for a block of the given size, taking
@@ -83,34 +83,9 @@
   ensures out = (threadAll nSplits s counts).1
   do
     -- impl-start
-    let mut result : List (List Nat) := []
-    let mut prev : List Nat := []
-    let mut i := 0
-    while i < counts.length
-      invariant i ≤ counts.length
-      invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])
-      done_with i = counts.length
-      decreasing counts.length - i
-    do
-      let count := counts[i]!
-      let sz := blockSize nSplits count
-      result := result ++ [shuffleAfter s prev sz]
-      prev := prev ++ [sz]
-      i := i + 1
-    return result
+    return []
     -- impl-end
 end
 
 prove_correct perClassShuffles by
   loom_solve
-  · have hi : i < counts.length := by omega
-    have hr := congrArg Prod.fst invariant_2
-    have hp := congrArg Prod.snd invariant_2
-    simp only at hr hp
-    rw [hr, hp, threadAll_take_step nSplits s counts i hi, threadStep, blockSize]
-  · have hr := congrArg Prod.fst invariant_2
-    simp only at hr
-    have hlen : i = counts.length := done_1
-    subst hlen
-    rw [List.take_length] at hr
-    simp_all [threadAll]
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
 /- The permutation a random source yields for a block of the given size, taking
@@ -83,34 +83,10 @@
   ensures out = (threadAll nSplits s counts).1
   do
     -- impl-start
-    let mut result : List (List Nat) := []
-    let mut prev : List Nat := []
-    let mut i := 0
-    while i < counts.length
-      invariant i ≤ counts.length
-      invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])
-      done_with i = counts.length
-      decreasing counts.length - i
-    do
-      let count := counts[i]!
-      let sz := blockSize nSplits count
-      result := result ++ [shuffleAfter s prev sz]
-      prev := prev ++ [sz]
-      i := i + 1
-    return result
+    let reset : List (List Nat) := counts.map (fun count => shuffleAfter s [] (blockSize nSplits count))
+    return reset
     -- impl-end
 end
 
 prove_correct perClassShuffles by
   loom_solve
-  · have hi : i < counts.length := by omega
-    have hr := congrArg Prod.fst invariant_2
-    have hp := congrArg Prod.snd invariant_2
-    simp only at hr hp
-    rw [hr, hp, threadAll_take_step nSplits s counts i hi, threadStep, blockSize]
-  · have hr := congrArg Prod.fst invariant_2
-    simp only at hr
-    have hlen : i = counts.length := done_1
-    subst hlen
-    rw [List.take_length] at hr
-    simp_all [threadAll]
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
 /- The permutation a random source yields for a block of the given size, taking
@@ -85,12 +85,11 @@
     -- impl-start
     let mut result : List (List Nat) := []
     let mut prev : List Nat := []
-    let mut i := 0
+    let mut i := 1
     while i < counts.length
       invariant i ≤ counts.length
       invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])
       done_with i = counts.length
-      decreasing counts.length - i
     do
       let count := counts[i]!
       let sz := blockSize nSplits count
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The permutation a random source yields for a block of the given size, taking
   into account that the source has already been consumed to permute every
   earlier block. The arguments are: an integer configuration value selecting the
   source; the (ordered) list of earlier block sizes already drawn from this
   source — the residue that determines where the source currently stands; and
   the size of the block to permute now. Permuting a block of size `sz` after
   earlier blocks `prev` therefore depends on ALL THREE — the source is consumed
   in sequence, never restarted for each block. UNCHANGED community callee (a
   standard pseudo-random generator), left fully opaque; its soundness (this
   residue model == the real source's sequential behaviour) is validated by
   axiom_check.py (G-AX, an A-reference). Provenance: mapping.md. -/
axiom shuffleAfter : Int → List Nat → Nat → List Nat
-- axioms-end

-- pure-start
/- The block size used for one class: a class with `count` members is permuted
   as a block of `max count nSplits` positions (so a block is never smaller than
   the number of requested splits). -/
def blockSize (nSplits : Nat) (count : Nat) : Nat := max count nSplits

/- Fold one class into the running result: it contributes the permutation its
   block receives from the shared source AFTER all earlier classes have been
   permuted (`prev` = earlier block sizes), and then records its own block size
   so the next class is permuted from the advanced source. The accumulator pairs
   the permutations produced so far with the residue (`prev`) of the source. -/
noncomputable def threadStep (nSplits : Nat) (s : Int)
    (acc : List (List Nat) × List Nat) (count : Nat) : List (List Nat) × List Nat :=
  let sz := blockSize nSplits count
  (acc.1 ++ [shuffleAfter s acc.2 sz], acc.2 ++ [sz])

/- The whole per-class shuffle pass: thread the single shared source through the
   classes in order. Each class is permuted from the source as advanced by every
   earlier class, so distinct configuration values produce distinct per-class
   shuffles (the source is never restarted per class). Front of the pair = the
   per-class permutations in class order; back = the consumed block sizes. -/
noncomputable def threadAll (nSplits : Nat) (s : Int) (counts : List Nat) :
    List (List Nat) × List Nat :=
  counts.foldl (threadStep nSplits s) ([], [])

/- Forward-fold step: extending the consumed prefix by one class folds that
   class into the result built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
@[grind] lemma threadAll_take_step (nSplits : Nat) (s : Int) (counts : List Nat)
    (i : Nat) (hi : i < counts.length) :
    (counts.take (i + 1)).foldl (threadStep nSplits s) ([], [])
      = threadStep nSplits s ((counts.take i).foldl (threadStep nSplits s) ([], []))
          counts[i]! := by
  have hcons : counts.take (i + 1) = counts.take i ++ [counts[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce, for each class in order, the permutation of its block of positions
   used to assign the class's members to splits.

   `counts` (the per-class member counts), `nSplits` (the number of requested
   splits) and `s` (the integer configuration value selecting the random source)
   are read-only inputs (none is `mut`). Desired behaviour: the classes share a
   SINGLE random source consumed in sequence — each class is permuted from the
   source as already advanced by every earlier class — so two different
   configuration values yield different per-class shuffles. The source is never
   restarted for each class. The result lists the per-class permutations in
   class order. -/
noncomputable section
method perClassShuffles (counts : List Nat) (nSplits : Nat) (s : Int)
    return (out : List (List Nat))
  ensures out = (threadAll nSplits s counts).1
  do
    -- impl-start
    return (threadAll nSplits s counts).1
    -- impl-end
end

prove_correct perClassShuffles by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No same-spec wrong impl verifies against the frozen spec, so there is no verifying-but-wrong impl whose faithful refined patch could fail to resolve.

SPEC SHAPE: perClassShuffles has no `require` and a single answer-key-tight functional postcondition `ensures out = (threadAll nSplits s counts).1`, where `threadAll = counts.foldl threadStep ([],[])` and `threadStep` emits `shuffleAfter s prev sz` (sz = max count nSplits) with residue `prev` accumulating block sizes. `shuffleAfter` is an OPAQUE axiom (A-reference), so `shuffleAfter s [] sz` and `shuffleAfter s prev sz` are NOT provably equal — the residue is genuinely load-bearing in the logic. The spec view (markers.spec_view) elides ONLY the impl region + prove_correct body; axioms/pure/pre/post kept verbatim, so attacks vary only impl+proof. same_spec=True verified for all 8 attacks + pc.

### ATTACKS (all, cmd `bash scripts/lean_verify.sh <f>` from project root; verifications launched concurrently in 2 batches of 4):
- pc.lean  (POSITIVE CONTROL, `return (threadAll nSplits s counts).1`): exit 0 = VERIFIES. Spec non-vacuous.
- atk_1 (prepatch bug / reset-residue echo, `shuffleAfter s [] sz` per class): exit 1, unsolved goal at postcondition.
- atk_2 (residue advanced by `count` instead of `sz`): exit 1, postcondition unprovable.
- atk_3 (boundary: block size = `count`, drops `max ... nSplits`): exit 1.
- atk_4 (residue never advanced, prev stays []): exit 1 (degenerates to bug).
- atk_5 (control-flow-effect: reversed result, prepend not append): exit 1.
- atk_6 (constant: `return []`, loop skipped): exit 1, `[] = (threadAll ...).1` unprovable.
- atk_7 (ungrounded-oracle echo: reset-residue `counts.map (shuffleAfter s [] ...)` then return): exit 1, `List.map (fun count => shuffleAfter s [] (blockSize nSplits count)) counts = (threadAll ...).1` unprovable.
- atk_8 (partial-domain: loop starts at i=1, skips first class): exit 1, fails invariant init AND postcondition.
Every failure is SEMANTIC (at the `ensures out = (threadAll nSplits s counts).1` obligation), verified by inspecting the goal states — none is a syntax/automation artifact. Because `shuffleAfter` is opaque, the postcondition pins `out` to the exact threaded fold over input `counts`; no residue-drop, block-size change, reordering, constant, partial-domain, or ungrounded echo discharges it. Spec is TIGHT.

MANDATORY RESOLVE STEP: no attack verified, so there is no verifying wrong-impl patch to materialize/run — patches={}. The ONLY verifying impl is the correct positive control, whose faithful refined patch is patch.diff (gold). Baseline sanity: ran gold patch.diff through the official harness `run_resolve('scikit-learn__scikit-learn-13124', gold, timeout=1500, retries=0)` -> {"resolved": true, "completed": true, "note": "resolved", "attempts": 1, "flaky": false}. So the correspondence baseline holds (verify -> correct -> resolves). prepatch.lean (Solution_prepatch, reset-residue skeleton): exit 1 for the right reason (G-DIFF), same_spec=True.

A-LEG / MODEL-PATCH CORRESPONDENCE AUDIT (the focus per plan §4): refinement.md legs are all R / A-reference / I; NO kind-3. The single axiom `shuffleAfter` is the UNCHANGED community callee (numpy.random.RandomState obtained via check_random_state), left fully opaque; the CHANGED data-flow (one shared source threaded across classes rather than restarted per class) is modeled DEEPLY by threadAll/threadStep over the accumulating residue `prev` = block sizes [sz_0, sz_1, ...] in class order (A5/A6, A-reference+I), not hidden behind an axiom about the function under change. `#print axioms` (per meta/prior pass) = [propext, shuffleAfter, Classical.choice, Quot.sound] — no value-pinning axiom. G-AX (axiom_check.py) run locally against real numpy RandomState: PASS (deterministic 3000/3000; residue load-bearing threaded != reset on >=50%; seed-sensitive >=50%) — the residue model faithfully mirrors the shared-RandomState sequential consumption of the patched per-class KFold(...).split(np.zeros(max(count,n_splits))). Correspondence of `shuffleAfter s prev sz` / residue-of-block-sizes-in-class-order to the real callee is sound.

G-CONF NOTE (not a break): running the bundle's conformance_check.py locally reported disagreements, but this is a PURE VERSION ARTIFACT — the host env has sklearn 1.3.0, whose StratifiedKFold._make_test_folds was rewritten to a round-robin `allocation` + `rng.shuffle(folds_for_class)` algorithm that no longer matches the base_commit-era `per_cls_cvs = [KFold(..., random_state=rng).split(np.zeros(max(count, n_splits))) for count in y_counts]` comprehension the model targets (confirmed by inspecting the installed source). G-CONF is designed to run IN-CONTAINER at base_commit with patch.diff applied; meta.json records the in-container G-CONF as pass (exit 0, shadow_provenance=transliterated, 100,005 inputs). So the local mismatch is NOT evidence against model fidelity.

CONCLUSION: verify => correct holds on this bundle, conditioned on the two declared trust points (G-AX axiom soundness, G-CONF refinement fidelity), both of which pass (G-AX locally, G-CONF in-container per meta.json). >=5 distinct attack classes exercised (reset-residue echo, wrong-residue-advance, boundary block-size, no-advance, control-flow reorder, constant, ungrounded-oracle echo, partial-domain); none verifies. No verifying wrong impl -> no non-resolving faithful patch -> spec is NOT broken.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The permutation a random source yields for a block of the given size, taking
   into account that the source has already been consumed to permute every
   earlier block. The arguments are: an integer configuration value selecting the
   source; the (ordered) list of earlier block sizes already drawn from this
   source — the residue that determines where the source currently stands; and
   the size of the block to permute now. Permuting a block of size `sz` after
   earlier blocks `prev` therefore depends on ALL THREE — the source is consumed
   in sequence, never restarted for each block. UNCHANGED community callee (a
   standard pseudo-random generator), left fully opaque; its soundness (this
   residue model == the real source's sequential behaviour) is validated by
   axiom_check.py (G-AX, an A-reference). Provenance: mapping.md. -/
axiom shuffleAfter : Int → List Nat → Nat → List Nat
-- axioms-end

-- pure-start
/- The block size used for one class: a class with `count` members is permuted
   as a block of `max count nSplits` positions (so a block is never smaller than
   the number of requested splits). -/
def blockSize (nSplits : Nat) (count : Nat) : Nat := max count nSplits

/- Fold one class into the running result: it contributes the permutation its
   block receives from the shared source AFTER all earlier classes have been
   permuted (`prev` = earlier block sizes), and then records its own block size
   so the next class is permuted from the advanced source. The accumulator pairs
   the permutations produced so far with the residue (`prev`) of the source. -/
noncomputable def threadStep (nSplits : Nat) (s : Int)
    (acc : List (List Nat) × List Nat) (count : Nat) : List (List Nat) × List Nat :=
  let sz := blockSize nSplits count
  (acc.1 ++ [shuffleAfter s acc.2 sz], acc.2 ++ [sz])

/- The whole per-class shuffle pass: thread the single shared source through the
   classes in order. Each class is permuted from the source as advanced by every
   earlier class, so distinct configuration values produce distinct per-class
   shuffles (the source is never restarted per class). Front of the pair = the
   per-class permutations in class order; back = the consumed block sizes. -/
noncomputable def threadAll (nSplits : Nat) (s : Int) (counts : List Nat) :
    List (List Nat) × List Nat :=
  counts.foldl (threadStep nSplits s) ([], [])

/- Forward-fold step: extending the consumed prefix by one class folds that
   class into the result built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
@[grind] lemma threadAll_take_step (nSplits : Nat) (s : Int) (counts : List Nat)
    (i : Nat) (hi : i < counts.length) :
    (counts.take (i + 1)).foldl (threadStep nSplits s) ([], [])
      = threadStep nSplits s ((counts.take i).foldl (threadStep nSplits s) ([], []))
          counts[i]! := by
  have hcons : counts.take (i + 1) = counts.take i ++ [counts[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce, for each class in order, the permutation of its block of positions
   used to assign the class's members to splits.

   `counts` (the per-class member counts), `nSplits` (the number of requested
   splits) and `s` (the integer configuration value selecting the random source)
   are read-only inputs (none is `mut`). Desired behaviour: the classes share a
   SINGLE random source consumed in sequence — each class is permuted from the
   source as already advanced by every earlier class — so two different
   configuration values yield different per-class shuffles. The source is never
   restarted for each class. The result lists the per-class permutations in
   class order. -/
noncomputable section
method perClassShuffles (counts : List Nat) (nSplits : Nat) (s : Int)
    return (out : List (List Nat))
  ensures out = (threadAll nSplits s counts).1
  do
    -- impl-start
    return (threadAll nSplits s counts).1
    -- impl-end
end

prove_correct perClassShuffles by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No same-spec wrong impl verifies against the frozen spec, so there is no verifying-but-wrong impl whose faithful refined patch could fail to resolve.

SPEC SHAPE: perClassShuffles has no `require` and a single answer-key-tight functional postcondition `ensures out = (threadAll nSplits s counts).1`, where `threadAll = counts.foldl threadStep ([],[])` and `threadStep` emits `shuffleAfter s prev sz` (sz = max count nSplits) with residue `prev` accumulating block sizes. `shuffleAfter` is an OPAQUE axiom (A-reference), so `shuffleAfter s [] sz` and `shuffleAfter s prev sz` are NOT provably equal — the residue is genuinely load-bearing in the logic. The spec view (markers.spec_view) elides ONLY the impl region + prove_correct body; axioms/pure/pre/post kept verbatim, so attacks vary only impl+proof. same_spec=True verified for all 8 attacks + pc.

### ATTACKS (all, cmd `bash scripts/lean_verify.sh <f>` from project root; verifications launched concurrently in 2 batches of 4):
- pc.lean  (POSITIVE CONTROL, `return (threadAll nSplits s counts).1`): exit 0 = VERIFIES. Spec non-vacuous.
- atk_1 (prepatch bug / reset-residue echo, `shuffleAfter s [] sz` per class): exit 1, unsolved goal at postcondition.
- atk_2 (residue advanced by `count` instead of `sz`): exit 1, postcondition unprovable.
- atk_3 (boundary: block size = `count`, drops `max ... nSplits`): exit 1.
- atk_4 (residue never advanced, prev stays []): exit 1 (degenerates to bug).
- atk_5 (control-flow-effect: reversed result, prepend not append): exit 1.
- atk_6 (constant: `return []`, loop skipped): exit 1, `[] = (threadAll ...).1` unprovable.
- atk_7 (ungrounded-oracle echo: reset-residue `counts.map (shuffleAfter s [] ...)` then return): exit 1, `List.map (fun count => shuffleAfter s [] (blockSize nSplits count)) counts = (threadAll ...).1` unprovable.
- atk_8 (partial-domain: loop starts at i=1, skips first class): exit 1, fails invariant init AND postcondition.
Every failure is SEMANTIC (at the `ensures out = (threadAll nSplits s counts).1` obligation), verified by inspecting the goal states — none is a syntax/automation artifact. Because `shuffleAfter` is opaque, the postcondition pins `out` to the exact threaded fold over input `counts`; no residue-drop, block-size change, reordering, constant, partial-domain, or ungrounded echo discharges it. Spec is TIGHT.

MANDATORY RESOLVE STEP: no attack verified, so there is no verifying wrong-impl patch to materialize/run — patches={}. The ONLY verifying impl is the correct positive control, whose faithful refined patch is patch.diff (gold). Baseline sanity: ran gold patch.diff through the official harness `run_resolve('scikit-learn__scikit-learn-13124', gold, timeout=1500, retries=0)` -> {"resolved": true, "completed": true, "note": "resolved", "attempts": 1, "flaky": false}. So the correspondence baseline holds (verify -> correct -> resolves). prepatch.lean (Solution_prepatch, reset-residue skeleton): exit 1 for the right reason (G-DIFF), same_spec=True.

A-LEG / MODEL-PATCH CORRESPONDENCE AUDIT (the focus per plan §4): refinement.md legs are all R / A-reference / I; NO kind-3. The single axiom `shuffleAfter` is the UNCHANGED community callee (numpy.random.RandomState obtained via check_random_state), left fully opaque; the CHANGED data-flow (one shared source threaded across classes rather than restarted per class) is modeled DEEPLY by threadAll/threadStep over the accumulating residue `prev` = block sizes [sz_0, sz_1, ...] in class order (A5/A6, A-reference+I), not hidden behind an axiom about the function under change. `#print axioms` (per meta/prior pass) = [propext, shuffleAfter, Classical.choice, Quot.sound] — no value-pinning axiom. G-AX (axiom_check.py) run locally against real numpy RandomState: PASS (deterministic 3000/3000; residue load-bearing threaded != reset on >=50%; seed-sensitive >=50%) — the residue model faithfully mirrors the shared-RandomState sequential consumption of the patched per-class KFold(...).split(np.zeros(max(count,n_splits))). Correspondence of `shuffleAfter s prev sz` / residue-of-block-sizes-in-class-order to the real callee is sound.

G-CONF NOTE (not a break): running the bundle's conformance_check.py locally reported disagreements, but this is a PURE VERSION ARTIFACT — the host env has sklearn 1.3.0, whose StratifiedKFold._make_test_folds was rewritten to a round-robin `allocation` + `rng.shuffle(folds_for_class)` algorithm that no longer matches the base_commit-era `per_cls_cvs = [KFold(..., random_state=rng).split(np.zeros(max(count, n_splits))) for count in y_counts]` comprehension the model targets (confirmed by inspecting the installed source). G-CONF is designed to run IN-CONTAINER at base_commit with patch.diff applied; meta.json records the in-container G-CONF as pass (exit 0, shadow_provenance=transliterated, 100,005 inputs). So the local mismatch is NOT evidence against model fidelity.

CONCLUSION: verify => correct holds on this bundle, conditioned on the two declared trust points (G-AX axiom soundness, G-CONF refinement fidelity), both of which pass (G-AX locally, G-CONF in-container per meta.json). >=5 distinct attack classes exercised (reset-residue echo, wrong-residue-advance, boundary block-size, no-advance, control-flow reorder, constant, ungrounded-oracle echo, partial-domain); none verifies. No verifying wrong impl -> no non-resolving faithful patch -> spec is NOT broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on velvet bundle scikit-learn__scikit-learn-13124. Modeled function: perClassShuffles, ensures out = (threadAll nSplits s counts).1, where threadAll threads ONE shared random source through the classes in order and each class contributes shuffleAfter s prev sz over a block of size max(count,nSplits) after residue prev (list of earlier block sizes). Real callee at base_commit 9f0b959a: post-patch StratifiedKFold._make_test_folds sets rng=check_random_state(self.random_state) (one RandomState instance) and the per-class KFold(...).split(np.zeros(max(count,n_splits))) generators share that instance, consumed lazily in class order via zip(*per_cls_cvs); each KFold._iter_test_indices does check_random_state(instance).shuffle(indices) which advances the SAME source across classes.

Checks performed:
1. Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True.
2. Solution.lean verifies: scripts/lean_verify.sh exit 0 (no sorry/error).
3. Model-vs-real differential fuzz (respecting Requires: n_splits>=2, count>=n_splits, binary/multiclass y): reconstructed the exact patched code path (shared check_random_state(seed) rng across lazy KFold(...).split generators + verbatim fold-assignment/scatter I-structure) and compared against the threadAll shadow. 4000 (faith13124b) + 20000 (faith13124c) + 50000 (faith13124d, n_splits 2-8, up to 7 classes, seeds to 1e7) inputs => 0 mismatches.
4. Axiom abstraction sound: shuffleAfter deterministic in (seed,prev,sz) and residue prev is load-bearing (~91% of configs differ from prev=[]), so the model is not vacuously the buggy prepatch behavior. Solution_prepatch.lean (shuffleAfter s [] sz per class) fails the ensures, confirming the spec discriminates the fix.

The modeled function agrees with the real repo callee on every tested input across ~74k adversarial cases; the residue-as-block-size-list abstraction is exact for numpy sequential RandomState.shuffle, and the lazy generator interleaving matches class order. No diverging input found. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = `rng = self.random_state` -> `rng = check_random_state(self.random_state)` in StratifiedKFold._make_test_folds (sklearn/model_selection/_split.py), plus a comment-only docstring reword excluded from the spec view. Behavioral discriminator: one shared RandomState threaded across the per-class KFold splits, so distinct random_state values yield distinct per-class shuffles.

Verified: (1) same_spec(Solution, Solution_prepatch) = True; consumer spec view generated via markers.spec_view (impl + prove_correct body elided). (2) leakage.screen passes with zero hard failures; meta G-LEAK = pass (not relaxed).

Lexical/mechanical check (independent of the gate): no diff markers; patched file path sklearn/model_selection/_split.py and its dotted module path absent; NO patched repo symbol named — check_random_state, _make_test_folds, StratifiedKFold, KFold, random_state do not appear as spec-view identifiers or in comments (identifiers are neutral: shuffleAfter, threadAll, threadStep, blockSize, perClassShuffles, counts, nSplits, s). No narration terms (bug/fix/wrong/regression/previously/...).

But they are the same'). A specification asserting the publicly-stated correct outcome is its legitimate function, not leakage. The spec does NOT reveal the gold IMPLEMENTATION beyond the problem statement: it never discloses that the repo fix is a one-line check_random_state(...) wrap, nor the int-vs-RandomState-instance mechanism of check_random_state that is the crux of solving. That mechanism is discussed only in refinement.md/mapping.md/axiom_check.py (auditor-facing docs, NOT in the consumer spec view) and partly echoes hints_text — which the gate correctly ignores. A solver still must locate the function and know check_random_state semantics; those steps are not handed over.

Conclusion: spec view leaks nothing about the gold edit beyond what problem_statement already makes public. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
