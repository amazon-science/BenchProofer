# P2 adversarial audit — scikit-learn__scikit-learn-9288

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk2_append.lean`, `atk3_reverse.lean`, `atk4_le_tie.lean`, `atk5_partial.lean`, `atk6_argmax.lean`, `atk7_skipfirst.lean`, `atk8_echo.lean`, `atk_prepatch.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8b_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `ensures out = bestOverKeys runFor keys` is a COMPLETE functional specification: it pins the output to a unique value for every (keys, altKeys, runFor). Therefore every same-spec impl that verifies is provably output-equal to the gold (`bestOverKeys runFor keys` = best k-means run over the canonical seed sequence). No verifying-but-wrong impl exists; verify ⇒ correct on this spec.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk2_append.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,15 +89,16 @@
   ensures out = bestOverKeys runFor keys
   do
     -- impl-start
+    let allk := keys ++ altKeys
     let mut best : Option Run := none
     let mut i := 0
-    while i < keys.length
-      invariant i ≤ keys.length
-      invariant best = (keys.take i).foldl (consider runFor) none
-      done_with i = keys.length
-      decreasing keys.length - i
+    while i < allk.length
+      invariant i ≤ allk.length
+      invariant best = (allk.take i).foldl (consider runFor) none
+      done_with i = allk.length
+      decreasing allk.length - i
     do
-      let k := keys[i]!
+      let k := allk[i]!
       let r := runFor k
       best := match best with
         | none   => some r
```

Attack 2 — `atk3_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,15 +89,16 @@
   ensures out = bestOverKeys runFor keys
   do
     -- impl-start
+    let ks := keys.reverse
     let mut best : Option Run := none
     let mut i := 0
-    while i < keys.length
-      invariant i ≤ keys.length
-      invariant best = (keys.take i).foldl (consider runFor) none
-      done_with i = keys.length
-      decreasing keys.length - i
+    while i < ks.length
+      invariant i ≤ ks.length
+      invariant best = (ks.take i).foldl (consider runFor) none
+      done_with i = ks.length
+      decreasing ks.length - i
     do
-      let k := keys[i]!
+      let k := ks[i]!
       let r := runFor k
       best := match best with
         | none   => some r
```

Attack 3 — `atk4_le_tie.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,7 @@
       let r := runFor k
       best := match best with
         | none   => some r
-        | some b => if r.score < b.score then some r else some b
+        | some b => if r.score ≤ b.score then some r else some b
       i := i + 1
     return best
     -- impl-end
```

Attack 4 — `atk5_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,10 +91,10 @@
     -- impl-start
     let mut best : Option Run := none
     let mut i := 0
-    while i < keys.length
+    while i + 1 < keys.length
       invariant i ≤ keys.length
       invariant best = (keys.take i).foldl (consider runFor) none
-      done_with i = keys.length
+      done_with i + 1 = keys.length
       decreasing keys.length - i
     do
       let k := keys[i]!
```

Attack 5 — `atk6_argmax.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,7 @@
       let r := runFor k
       best := match best with
         | none   => some r
-        | some b => if r.score < b.score then some r else some b
+        | some b => if r.score > b.score then some r else some b
       i := i + 1
     return best
     -- impl-end
```

Attack 6 — `atk7_skipfirst.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
   do
     -- impl-start
     let mut best : Option Run := none
-    let mut i := 0
+    let mut i := 1
     while i < keys.length
       invariant i ≤ keys.length
       invariant best = (keys.take i).foldl (consider runFor) none
```

Attack 7 — `atk8_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,21 +89,7 @@
   ensures out = bestOverKeys runFor keys
   do
     -- impl-start
-    let mut best : Option Run := none
-    let mut i := 0
-    while i < keys.length
-      invariant i ≤ keys.length
-      invariant best = (keys.take i).foldl (consider runFor) none
-      done_with i = keys.length
-      decreasing keys.length - i
-    do
-      let k := keys[i]!
-      let r := runFor k
-      best := match best with
-        | none   => some r
-        | some b => if r.score < b.score then some r else some b
-      i := i + 1
-    return best
+    return bestOverKeys runFor keys
     -- impl-end
 
 prove_correct selectBest by
```

Attack 8 — `atk8b_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -89,29 +89,8 @@
   ensures out = bestOverKeys runFor keys
   do
     -- impl-start
-    let mut best : Option Run := none
-    let mut i := 0
-    while i < keys.length
-      invariant i ≤ keys.length
-      invariant best = (keys.take i).foldl (consider runFor) none
-      done_with i = keys.length
-      decreasing keys.length - i
-    do
-      let k := keys[i]!
-      let r := runFor k
-      best := match best with
-        | none   => some r
-        | some b => if r.score < b.score then some r else some b
-      i := i + 1
-    return best
+    return bestOverKeys runFor keys
     -- impl-end
 
 prove_correct selectBest by
   loom_solve
-  · have hi : i < keys.length := by omega
-    rw [bestOverKeys_take_step runFor keys i hi, ← invariant_2]
-    simp [consider]
-  · have hlen : i = keys.length := done_1
-    subst hlen
-    rw [List.take_length] at invariant_2
-    simp_all [bestOverKeys]
```

Attack 9 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,15 +89,19 @@
   ensures out = bestOverKeys runFor keys
   do
     -- impl-start
+    -- PRE-PATCH (buggy): the attempts are run over `altKeys` — a separate key
+    -- sequence that happens to be in scope — instead of the canonical `keys`.
+    -- The two sequences agree only by accident, so the reported best is in
+    -- general the best over the WRONG runs; prove_correct MUST fail.
     let mut best : Option Run := none
     let mut i := 0
-    while i < keys.length
-      invariant i ≤ keys.length
-      invariant best = (keys.take i).foldl (consider runFor) none
-      done_with i = keys.length
-      decreasing keys.length - i
+    while i < altKeys.length
+      invariant i ≤ altKeys.length
+      invariant best = (altKeys.take i).foldl (consider runFor) none
+      done_with i = altKeys.length
+      decreasing altKeys.length - i
     do
-      let k := keys[i]!
+      let k := altKeys[i]!
       let r := runFor k
       best := match best with
         | none   => some r
@@ -108,10 +112,10 @@
 
 prove_correct selectBest by
   loom_solve
-  · have hi : i < keys.length := by omega
-    rw [bestOverKeys_take_step runFor keys i hi, ← invariant_2]
+  · have hi : i < altKeys.length := by omega
+    rw [bestOverKeys_take_step runFor altKeys i hi, ← invariant_2]
     simp [consider]
-  · have hlen : i = keys.length := done_1
+  · have hlen : i = altKeys.length := done_1
     subst hlen
     rw [List.take_length] at invariant_2
     simp_all [bestOverKeys]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
import Mathlib.Data.Rat.Defs
import Mathlib.Algebra.Order.Field.Rat
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. One attempt's outcome is produced by an UNCHANGED
--  routine that this code does not alter; it is observed here only through the
--  free input `runFor : Key → Run`. The spec makes NO behavioural claim about
--  that routine — every clause holds for EVERY function it could be — so there
--  is nothing to validate against a real callee (no G-AX). The behaviour under
--  spec — over WHICH sequence of per-attempt keys the attempts are run, and that
--  the best-scoring outcome is reported — is modeled deeply in the `pure`/`impl`
--  regions, with no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The per-attempt key that fully determines one attempt's outcome: identified
   abstractly, since the only thing observed is WHICH sequence of keys the
   attempts are run over (two equal sequences must yield the same report). -/
abbrev Key := Int

/- The outcome of a single attempt. `score` is the quantity to be minimised
   (lower is better); `payload` is the reportable content of the attempt
   (identified abstractly). Two attempts with different content are different
   outcomes even at the same score. -/
structure Run where
  score : Rat
  payload : Nat

/- Fold one more attempt into the running best-so-far. `acc` is the best outcome
   seen over the attempts considered so far (`none` before any attempt). The next
   attempt's outcome is `runFor k`; it replaces the incumbent exactly when there
   is no incumbent yet, or when it scores strictly lower. A tie keeps the earlier
   incumbent — the first attempt achieving the minimum score is the one reported. -/
def consider (runFor : Key → Run) (acc : Option Run) (k : Key) : Option Run :=
  let r := runFor k
  match acc with
  | none   => some r
  | some b => if r.score < b.score then some r else some b

/- The reported outcome of running one attempt per key, in order, over the given
   key sequence and keeping the best-scoring one. Front-to-back fold so a single
   unfold is available per loop step (the Velvet forward-fold pattern). -/
def bestOverKeys (runFor : Key → Run) (keys : List Key) : Option Run :=
  keys.foldl (consider runFor) none

/- Forward-fold step: extending the consumed prefix by one key folds that key's
   attempt into the best built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
@[grind] lemma bestOverKeys_take_step (runFor : Key → Run) (keys : List Key)
    (i : Nat) (hi : i < keys.length) :
    (keys.take (i + 1)).foldl (consider runFor) none
      = consider runFor ((keys.take i).foldl (consider runFor) none) keys[i]! := by
  have hcons : keys.take (i + 1) = keys.take i ++ [keys[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Run several independent attempts and report the best-scoring one.

   `keys` is the canonical sequence of per-attempt keys — the one source of
   per-attempt keys this routine must use, the SAME sequence whatever machinery
   carries out the attempts. `altKeys` is some other key sequence that happens to
   be in scope; it must NOT drive the attempts. `runFor` is the UNCHANGED routine
   mapping any key to that attempt's outcome. All three are read-only (none
   `mut`): the routine reads them and returns a result, mutating nothing it is
   handed (directive 5).

   The reported outcome is `bestOverKeys runFor keys`: the best (strictly lowest
   score; earliest on a tie) attempt over the runs determined by the CANONICAL
   key sequence — never over runs determined by `altKeys`. Two callers that pin
   the same canonical key sequence therefore obtain the same report regardless of
   how the attempts are arranged. -/
method selectBest (keys : List Key) (altKeys : List Key) (runFor : Key → Run)
    return (out : Option Run)
  ensures out = bestOverKeys runFor keys
  do
    -- impl-start
    let mut best : Option Run := none
    let mut i := 0
    while i < keys.length
      invariant i ≤ keys.length
      invariant best = (keys.take i).foldl (consider runFor) none
      done_with i = keys.length
      decreasing keys.length - i
    do
      let k := keys[i]!
      let r := runFor k
      best := match best with
        | none   => some r
        | some b => if r.score < b.score then some r else some b
      i := i + 1
    return best
    -- impl-end

prove_correct selectBest by
  loom_solve
  · have hi : i < keys.length := by omega
    rw [bestOverKeys_take_step runFor keys i hi, ← invariant_2]
    simp [consider]
  · have hlen : i = keys.length := done_1
    subst hlen
    rw [List.take_length] at invariant_2
    simp_all [bestOverKeys]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (project root; for elan). same_spec=True confirmed for ALL 9 files (velvet backend). Positive control pos_control.lean = frozen Solution.lean verifies rc=0 (`bash scripts/lean_verify.sh <f>`). Prepatch reproduced: atk_prepatch.lean (loop iterates altKeys) fails verification rc=1 (unsolved goals on the `out = bestOverKeys runFor keys` obligation) — the G-DIFF bug confirmed.

8 DISTINCT wrong impls encoded (impl region only edited; axioms/pure/pre/post byte-identical):
- atk2_append (iterate keys++altKeys, extra runs): rc=1 (omega/invariant fail).
- atk3_reverse (iterate keys.reverse): rc=1 (omega/invariant fail).
- atk4_le_tie (control-flow-effect: `≤` last-wins tie-break): rc=1 (unsolved goals — differs from strict `<` consider).
- atk5_partial (partial-domain: `i+1<len`, drops last key): rc=1 (unsolved goals).
- atk6_argmax (ungrounded-oracle wrong direction, `>` pick worst): rc=1 (unsolved goals — goal shows swapped `<` mismatch vs consider).
- atk7_skipfirst (boundary: start i=1, skip first attempt): rc=1 (unsolved goals — invariant broken at entry).
- atk8_echo (return bestOverKeys runFor keys but leave stale proof bullets): rc=1 ('No goals to be solved' — proof-artifact only, not a spec break).
- atk8b_echo (SAME echo impl, proof reduced to `loom_solve`): rc=0 VERIFIES. This is the only verifying variant and it is BEHAVIORALLY CORRECT (returns exactly the spec value).

All verifications run concurrently in background batches of 4 (independent inputs, read-only lean_shared).

MANDATORY RESOLVE RUN (executed, not speculated): the only verifying impl (atk8b_echo) is output-equal to gold, so its faithful refined patch IS the gold patch. Materialized gold.patch (extracted from data/swe_bench_verified/test.jsonl, base_commit 3eacf948) and ran harness.run_resolve('scikit-learn__scikit-learn-9288', gold, timeout=1800, retries=0) -> RESOLVED: True COMPLETED: True NOTE: resolved (F2P test_result_of_kmeans_equal_in_diff_n_jobs). So the verifying impl's faithful patch RESOLVES => spec is NOT broken.

refinement.md AUDIT (§C no kind-3; A-leg correspondence): legs A1 (keys<->precomputed `seeds=random_state.randint(...,size=n_init)`), A2 (altKeys<->the removed per-iter live `random_state` draw), A5 (return<->best_* result) are R (type refinements, mapping.md §2 bijections — Int seed / Rat order-only inertia / Option incumbent). A3 (runFor<->UNCHANGED kmeans_single) is carried as a FREE INPUT with NO behavioural claim — the postcondition holds for EVERY runFor, so there is genuinely no callee contract to validate (correctly NOT an A-consumed/A-reference leg; G-AX skip is justified: no `axiom` in the spec). A4 (consider argmin, strict-`<` first-wins) is I, transliterated. The single genuinely-changed op (which key sequence the single-thread loop iterates) is modeled DIRECTLY as `keys` vs `altKeys` in the impl — not hidden behind an axiom — so no kind-3 (inexpressible-changed-op) leg exists. The A-leg correspondence claim in §B/§3 holds: kmeans_single is unchanged by the gold patch (patch only re-keys the loop), matching its abstract free-input treatment.

CONCLUSION: The frozen spec is a complete functional postcondition; 6-8 distinct wrong impls (partial-domain, boundary, control-flow-effect tie-break, wrong-direction/ungrounded oracle, extra/reordered runs, prepatch wrong-sequence) all FAIL verification, and the sole verifying impl's faithful patch RESOLVES under the official harness. verify ⇒ correct holds. No falsification found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk2_append.lean`, `atk3_reverse.lean`, `atk4_le_tie.lean`, `atk5_partial.lean`, `atk6_argmax.lean`, `atk7_skipfirst.lean`, `atk8_echo.lean`, `atk_prepatch.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8b_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `ensures out = bestOverKeys runFor keys` is a COMPLETE functional specification: it pins the output to a unique value for every (keys, altKeys, runFor). Therefore every same-spec impl that verifies is provably output-equal to the gold (`bestOverKeys runFor keys` = best k-means run over the canonical seed sequence). No verifying-but-wrong impl exists; verify ⇒ correct on this spec.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk2_append.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk3_reverse.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk4_le_tie.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk5_partial.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk6_argmax.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk7_skipfirst.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk8_echo.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8b_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
import Mathlib.Data.Rat.Defs
import Mathlib.Algebra.Order.Field.Rat
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. One attempt's outcome is produced by an UNCHANGED
--  routine that this code does not alter; it is observed here only through the
--  free input `runFor : Key → Run`. The spec makes NO behavioural claim about
--  that routine — every clause holds for EVERY function it could be — so there
--  is nothing to validate against a real callee (no G-AX). The behaviour under
--  spec — over WHICH sequence of per-attempt keys the attempts are run, and that
--  the best-scoring outcome is reported — is modeled deeply in the `pure`/`impl`
--  regions, with no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- The per-attempt key that fully determines one attempt's outcome: identified
   abstractly, since the only thing observed is WHICH sequence of keys the
   attempts are run over (two equal sequences must yield the same report). -/
abbrev Key := Int

/- The outcome of a single attempt. `score` is the quantity to be minimised
   (lower is better); `payload` is the reportable content of the attempt
   (identified abstractly). Two attempts with different content are different
   outcomes even at the same score. -/
structure Run where
  score : Rat
  payload : Nat

/- Fold one more attempt into the running best-so-far. `acc` is the best outcome
   seen over the attempts considered so far (`none` before any attempt). The next
   attempt's outcome is `runFor k`; it replaces the incumbent exactly when there
   is no incumbent yet, or when it scores strictly lower. A tie keeps the earlier
   incumbent — the first attempt achieving the minimum score is the one reported. -/
def consider (runFor : Key → Run) (acc : Option Run) (k : Key) : Option Run :=
  let r := runFor k
  match acc with
  | none   => some r
  | some b => if r.score < b.score then some r else some b

/- The reported outcome of running one attempt per key, in order, over the given
   key sequence and keeping the best-scoring one. Front-to-back fold so a single
   unfold is available per loop step (the Velvet forward-fold pattern). -/
def bestOverKeys (runFor : Key → Run) (keys : List Key) : Option Run :=
  keys.foldl (consider runFor) none

/- Forward-fold step: extending the consumed prefix by one key folds that key's
   attempt into the best built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
@[grind] lemma bestOverKeys_take_step (runFor : Key → Run) (keys : List Key)
    (i : Nat) (hi : i < keys.length) :
    (keys.take (i + 1)).foldl (consider runFor) none
      = consider runFor ((keys.take i).foldl (consider runFor) none) keys[i]! := by
  have hcons : keys.take (i + 1) = keys.take i ++ [keys[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Run several independent attempts and report the best-scoring one.

   `keys` is the canonical sequence of per-attempt keys — the one source of
   per-attempt keys this routine must use, the SAME sequence whatever machinery
   carries out the attempts. `altKeys` is some other key sequence that happens to
   be in scope; it must NOT drive the attempts. `runFor` is the UNCHANGED routine
   mapping any key to that attempt's outcome. All three are read-only (none
   `mut`): the routine reads them and returns a result, mutating nothing it is
   handed (directive 5).

   The reported outcome is `bestOverKeys runFor keys`: the best (strictly lowest
   score; earliest on a tie) attempt over the runs determined by the CANONICAL
   key sequence — never over runs determined by `altKeys`. Two callers that pin
   the same canonical key sequence therefore obtain the same report regardless of
   how the attempts are arranged. -/
method selectBest (keys : List Key) (altKeys : List Key) (runFor : Key → Run)
    return (out : Option Run)
  ensures out = bestOverKeys runFor keys
  do
    -- impl-start
    let mut best : Option Run := none
    let mut i := 0
    while i < keys.length
      invariant i ≤ keys.length
      invariant best = (keys.take i).foldl (consider runFor) none
      done_with i = keys.length
      decreasing keys.length - i
    do
      let k := keys[i]!
      let r := runFor k
      best := match best with
        | none   => some r
        | some b => if r.score < b.score then some r else some b
      i := i + 1
    return best
    -- impl-end

prove_correct selectBest by
  loom_solve
  · have hi : i < keys.length := by omega
    rw [bestOverKeys_take_step runFor keys i hi, ← invariant_2]
    simp [consider]
  · have hlen : i = keys.length := done_1
    subst hlen
    rw [List.take_length] at invariant_2
    simp_all [bestOverKeys]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (project root; for elan). same_spec=True confirmed for ALL 9 files (velvet backend). Positive control pos_control.lean = frozen Solution.lean verifies rc=0 (`bash scripts/lean_verify.sh <f>`). Prepatch reproduced: atk_prepatch.lean (loop iterates altKeys) fails verification rc=1 (unsolved goals on the `out = bestOverKeys runFor keys` obligation) — the G-DIFF bug confirmed.

8 DISTINCT wrong impls encoded (impl region only edited; axioms/pure/pre/post byte-identical):
- atk2_append (iterate keys++altKeys, extra runs): rc=1 (omega/invariant fail).
- atk3_reverse (iterate keys.reverse): rc=1 (omega/invariant fail).
- atk4_le_tie (control-flow-effect: `≤` last-wins tie-break): rc=1 (unsolved goals — differs from strict `<` consider).
- atk5_partial (partial-domain: `i+1<len`, drops last key): rc=1 (unsolved goals).
- atk6_argmax (ungrounded-oracle wrong direction, `>` pick worst): rc=1 (unsolved goals — goal shows swapped `<` mismatch vs consider).
- atk7_skipfirst (boundary: start i=1, skip first attempt): rc=1 (unsolved goals — invariant broken at entry).
- atk8_echo (return bestOverKeys runFor keys but leave stale proof bullets): rc=1 ('No goals to be solved' — proof-artifact only, not a spec break).
- atk8b_echo (SAME echo impl, proof reduced to `loom_solve`): rc=0 VERIFIES. This is the only verifying variant and it is BEHAVIORALLY CORRECT (returns exactly the spec value).

All verifications run concurrently in background batches of 4 (independent inputs, read-only lean_shared).

MANDATORY RESOLVE RUN (executed, not speculated): the only verifying impl (atk8b_echo) is output-equal to gold, so its faithful refined patch IS the gold patch. Materialized gold.patch (extracted from data/swe_bench_verified/test.jsonl, base_commit 3eacf948) and ran harness.run_resolve('scikit-learn__scikit-learn-9288', gold, timeout=1800, retries=0) -> RESOLVED: True COMPLETED: True NOTE: resolved (F2P test_result_of_kmeans_equal_in_diff_n_jobs). So the verifying impl's faithful patch RESOLVES => spec is NOT broken.

refinement.md AUDIT (§C no kind-3; A-leg correspondence): legs A1 (keys<->precomputed `seeds=random_state.randint(...,size=n_init)`), A2 (altKeys<->the removed per-iter live `random_state` draw), A5 (return<->best_* result) are R (type refinements, mapping.md §2 bijections — Int seed / Rat order-only inertia / Option incumbent). A3 (runFor<->UNCHANGED kmeans_single) is carried as a FREE INPUT with NO behavioural claim — the postcondition holds for EVERY runFor, so there is genuinely no callee contract to validate (correctly NOT an A-consumed/A-reference leg; G-AX skip is justified: no `axiom` in the spec). A4 (consider argmin, strict-`<` first-wins) is I, transliterated. The single genuinely-changed op (which key sequence the single-thread loop iterates) is modeled DIRECTLY as `keys` vs `altKeys` in the impl — not hidden behind an axiom — so no kind-3 (inexpressible-changed-op) leg exists. The A-leg correspondence claim in §B/§3 holds: kmeans_single is unchanged by the gold patch (patch only re-keys the loop), matching its abstract free-input treatment.

CONCLUSION: The frozen spec is a complete functional postcondition; 6-8 distinct wrong impls (partial-domain, boundary, control-flow-effect tie-break, wrong-direction/ungrounded oracle, extra/reordered runs, prepatch wrong-sequence) all FAIL verification, and the sole verifying impl's faithful patch RESOLVES under the official harness. verify ⇒ correct holds. No falsification found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for scikit-learn__scikit-learn-9288 (velvet). No divergence found between the modeled function `selectBest` and the real repo callee.

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet-backend) = True — the spec region (axioms/pure/pre/post + method signature + `ensures out = bestOverKeys runFor keys`) is byte-identical between post- and pre-patch. Nothing was smuggled into the impl-only region.
2. Solution.lean verifies under lean_verify.sh (exit 0, no sorry/error).
3. conformance_check.py passes: 100007 fuzzed inputs, 0 disagreements between the R/I shadow (consider/bestOverKeys over canonical `keys`) and the gold-patched single-thread selection loop transliteration.

Faithfulness argument (why the spec is NOT too strong):
- The real changed code (gold patch, k_means_.py single-thread branch) is: `seeds = random_state.randint(int32.max, size=n_init); for seed in seeds: labels,inertia,... = kmeans_single(..., random_state=seed); if best_inertia is None or inertia < best_inertia: best_* = ...`. This is exactly argmin over the canonical seed array with strict `<` and first-wins on ties.
- The model's `consider` (none -> some r; some b -> `if r.score < b.score then some r else some b`) folded left over `keys` reproduces this precisely: min score, earliest on tie. `keys=[]` (n_init=0) -> `none`, matching `best_*` staying None.
- `runFor : Key -> Run` is a FREE INPUT; the `ensures` quantifies over EVERY `runFor`, so the spec makes NO behavioural claim about the unchanged `kmeans_single`. That is conservative, not too strong — there is no callee contract to over-constrain, hence G-AX correctly skipped.
- Float inertia modeled as `Rat` (order-only). k-means inertia is finite non-negative (no NaN), so the total order of `Rat` matches Python `<` on the observed domain; tie semantics (equal scores keep incumbent) are identical.
- The discriminating content — WHICH sequence drives the loop (`keys` post-patch vs `altKeys` pre-patch) — is modeled directly by which list the `while` iterates; prepatch fails on the same ensures clause (G-DIFF sound).

Searched for a diverging input across the plausible failure modes (argmax vs argmin, wrong tie direction, off-by-one/iteration order, empty list, NaN score, altKeys vs keys) and found none. Spec is FAITHFUL to the real repo behaviour.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Re-verified the accepted RELAXED_LEAKAGE disposition rather than rubber-stamping; no leak beyond the dispositioned two-sequence facet found. VERIFIED CORE SOUNDNESS: (1) same_spec(Solution, Solution_prepatch, velvet.LanguageTables) = True (spec regions byte-identical). (2) G-VERIFY live: lean_verify.sh on Solution.lean exits 0. (3) G-DIFF live: Solution_prepatch.lean (folds over altKeys, not keys) fails on EXACTLY the discriminating clause 'ensures out = bestOverKeys runFor keys' (error at :118, unsolved goal foldl consider none altKeys = foldl consider none keys) — genuine semantic failure, not a syntactic break. meta gates G-EQ/PANEL-1/PANEL-2/CONF/MUT all pass; G-LEAK=relaxed, relaxed_leakage=true.

LEAKAGE ANALYSIS (spec view vs problem_statement, excluding hints_text): The spec view DOES carry a genuine semantic leak of the gold diagnosis — the second parameter altKeys and its docstring ('some other key sequence that happens to be in scope; it must NOT drive the attempts' / 'never over runs determined by altKeys') guide a reader to the root cause (two per-attempt seed sequences exist; the buggy single-thread loop is keyed on the wrong one). But this is precisely the DISPOSITIONED facet. Independently re-derived unavoidability: problem_statement is symptom-only (KMeans inertia differs for n_jobs=1 vs >1); token scan confirms 0 occurrences of seed/n_init/randint/sequence, random_state only as the constructor arg — no root cause.

The modeled change is PURELY which sequence drives the loop (kmeans_single routine and the argmin selection rule are byte-unchanged by the gold patch). G-DIFF requires the byte-identical frozen spec to reject the true prepatch behavior (fold over the alternate sequence); a spec that never names a second sequence could only assert 'best over the runs performed', which the prepatch satisfies over its own runs, so G-DIFF could not fire. Faithful + non-leaking is therefore provably impossible — a real problem_statement<->gold mismatch.

NO NEW LEAK: the remainder of the spec view is de-narrated (neutral attempts/keys/score/payload/runFor vocabulary; no k_means/seed/inertia/n_jobs tokens); the disclosed argmin/first-wins selection rule is UNCHANGED by the patch, so it does not leak the edit. No new leaking line beyond the two-sequence facet and no broken disposition (core gates sound, unavoidability holds, RELAXED_LEAKAGE.md present, meta flag set). Per _audit.py convention a properly-dispositioned relaxed-leakage panel_3 records NO-LEAKAGE/pass + note.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.