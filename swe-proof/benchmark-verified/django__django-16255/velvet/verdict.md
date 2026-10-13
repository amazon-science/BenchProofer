# P2 adversarial audit — django__django-16255

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1_prepatch.lean`, `atk2_none.lean`, `atk3_min.lean`, `atk4_head.lean`, `atk5_const.lean`, `atk6_offbyone.lean`, `atk7_partial.lean`, `atk8_droptail.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,7 +67,7 @@
     ∃ k, k < stamps.length ∧ stamps[k]! = v
   do
     -- impl-start
-    let mut result : Option Int := none
+    let mut result : Option Int := some 0
     let mut i := stamps.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ stamps.length
```

Attack 2 — `atk2_none.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,18 +67,7 @@
     ∃ k, k < stamps.length ∧ stamps[k]! = v
   do
     -- impl-start
-    let mut result : Option Int := none
-    let mut i := stamps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ stamps.length
-      invariant result = latestStamp (stamps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := stamps[i - 1]!
-      result := some (match result with | none => c | some m => max c m)
-      i := i - 1
-    return result
+    return none
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -161,6 +150,10 @@
             rw [hidx]; exact hkm
 
 prove_correct latestLastmod by
-  loom_solve
-  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
-  rw [‹result = latestStamp (stamps.drop i)›]
+  loom_solve <;>
+    (first
+      | rfl
+      | simp_all [latestStamp]
+      | grind
+      | (try rw [latestStamp_drop_step stamps i (by omega) (by omega)]) <;> grind
+      | omega)
```

Attack 3 — `atk3_min.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,12 +71,11 @@
     let mut i := stamps.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ stamps.length
-      invariant result = latestStamp (stamps.drop i)
       done_with i = 0
       decreasing i
     do
       let c := stamps[i - 1]!
-      result := some (match result with | none => c | some m => max c m)
+      result := some (match result with | none => c | some m => min c m)
       i := i - 1
     return result
     -- impl-end
@@ -161,6 +160,10 @@
             rw [hidx]; exact hkm
 
 prove_correct latestLastmod by
-  loom_solve
-  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
-  rw [‹result = latestStamp (stamps.drop i)›]
+  loom_solve <;>
+    (first
+      | rfl
+      | simp_all [latestStamp]
+      | grind
+      | (try rw [latestStamp_drop_step stamps i (by omega) (by omega)]) <;> grind
+      | omega)
```

Attack 4 — `atk4_head.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,18 +67,10 @@
     ∃ k, k < stamps.length ∧ stamps[k]! = v
   do
     -- impl-start
-    let mut result : Option Int := none
-    let mut i := stamps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ stamps.length
-      invariant result = latestStamp (stamps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := stamps[i - 1]!
-      result := some (match result with | none => c | some m => max c m)
-      i := i - 1
-    return result
+    if stamps.length = 0 then
+      return none
+    else
+      return some (stamps[0]!)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -161,6 +153,10 @@
             rw [hidx]; exact hkm
 
 prove_correct latestLastmod by
-  loom_solve
-  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
-  rw [‹result = latestStamp (stamps.drop i)›]
+  loom_solve <;>
+    (first
+      | rfl
+      | simp_all [latestStamp]
+      | grind
+      | (try rw [latestStamp_drop_step stamps i (by omega) (by omega)]) <;> grind
+      | omega)
```

Attack 5 — `atk5_const.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,18 +67,7 @@
     ∃ k, k < stamps.length ∧ stamps[k]! = v
   do
     -- impl-start
-    let mut result : Option Int := none
-    let mut i := stamps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ stamps.length
-      invariant result = latestStamp (stamps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := stamps[i - 1]!
-      result := some (match result with | none => c | some m => max c m)
-      i := i - 1
-    return result
+    return some 0
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -161,6 +150,10 @@
             rw [hidx]; exact hkm
 
 prove_correct latestLastmod by
-  loom_solve
-  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
-  rw [‹result = latestStamp (stamps.drop i)›]
+  loom_solve <;>
+    (first
+      | rfl
+      | simp_all [latestStamp]
+      | grind
+      | (try rw [latestStamp_drop_step stamps i (by omega) (by omega)]) <;> grind
+      | omega)
```

Attack 6 — `atk6_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,10 +68,9 @@
   do
     -- impl-start
     let mut result : Option Int := none
-    let mut i := stamps.length
+    let mut i := stamps.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ stamps.length
-      invariant result = latestStamp (stamps.drop i)
       done_with i = 0
       decreasing i
     do
@@ -161,6 +160,10 @@
             rw [hidx]; exact hkm
 
 prove_correct latestLastmod by
-  loom_solve
-  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
-  rw [‹result = latestStamp (stamps.drop i)›]
+  loom_solve <;>
+    (first
+      | rfl
+      | simp_all [latestStamp]
+      | grind
+      | (try rw [latestStamp_drop_step stamps i (by omega) (by omega)]) <;> grind
+      | omega)
```

Attack 7 — `atk7_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,18 +67,10 @@
     ∃ k, k < stamps.length ∧ stamps[k]! = v
   do
     -- impl-start
-    let mut result : Option Int := none
-    let mut i := stamps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ stamps.length
-      invariant result = latestStamp (stamps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := stamps[i - 1]!
-      result := some (match result with | none => c | some m => max c m)
-      i := i - 1
-    return result
+    if stamps.length = 0 then
+      return none
+    else
+      return some 0
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -161,6 +153,10 @@
             rw [hidx]; exact hkm
 
 prove_correct latestLastmod by
-  loom_solve
-  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
-  rw [‹result = latestStamp (stamps.drop i)›]
+  loom_solve <;>
+    (first
+      | rfl
+      | simp_all [latestStamp]
+      | grind
+      | (try rw [latestStamp_drop_step stamps i (by omega) (by omega)]) <;> grind
+      | omega)
```

Attack 8 — `atk8_droptail.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,18 +67,7 @@
     ∃ k, k < stamps.length ∧ stamps[k]! = v
   do
     -- impl-start
-    let mut result : Option Int := none
-    let mut i := stamps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ stamps.length
-      invariant result = latestStamp (stamps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := stamps[i - 1]!
-      result := some (match result with | none => c | some m => max c m)
-      i := i - 1
-    return result
+    return latestStamp (stamps.drop 1)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -161,6 +150,10 @@
             rw [hidx]; exact hkm
 
 prove_correct latestLastmod by
-  loom_solve
-  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
-  rw [‹result = latestStamp (stamps.drop i)›]
+  loom_solve <;>
+    (first
+      | rfl
+      | simp_all [latestStamp]
+      | grind
+      | (try rw [latestStamp_drop_step stamps i (by omega) (by omega)]) <;> grind
+      | omega)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: the modeled reduction is a bounded fold over a finite
-- stamp list that always terminates and returns, so a diverging implementation
-- must NOT satisfy the spec (partial correctness would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the reported value is the greatest of the collected
--  per-entry stamps, modeled deeply as a running maximum over `List Int`. There
--  is no unchanged library callee the proof must axiomatize.)
-- axioms-end

-- pure-start
/- The latest stamp reported across a collection of comparable per-entry stamps.
   With no entries the collection is empty and there is no stamp to report, so
   the result is the absent marker `none` (reporting a latest stamp over an empty
   collection must NOT fail). With one or more entries the result is the greatest
   stamp. Front-recursive so a single unfold is available per loop step (the
   Velvet fold pattern). -/
def latestStamp : List Int → Option Int
  | []      => none
  | c :: cs =>
      some (match latestStamp cs with
            | none   => c
            | some m => max c m)

@[grind] lemma latestStamp_nil : latestStamp [] = none := rfl
@[grind] lemma latestStamp_cons (c : Int) (cs : List Int) :
    latestStamp (c :: cs) =
      some (match latestStamp cs with | none => c | some m => max c m) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A section that exposes a per-entry modification stamp reports the most recent
   stamp across its entries. The per-entry stamp function applied across the
   enumerated entries yields a collection of comparable values, modeled as
   `List Int`; the reported value is `Option Int`.

   Two guarantees pin the behavior the issue demands:

   - when the section enumerates NO entries, the collection is empty and the
     reported value is the absent marker `none` — computing a latest stamp over
     an empty section must NOT fail;
   - when the section enumerates one or more entries, the reported value is the
     greatest stamp in the collection: it is one of the collected stamps and is
     greater than or equal to every collected stamp.

   `stamps` is read-only (not `mut`); the reduction builds a fresh result and
   mutates nothing (directive 5). -/
method latestLastmod (stamps : List Int) return (out : Option Int)
  ensures out = latestStamp stamps
  ensures stamps.length = 0 → out = none
  ensures stamps.length > 0 → ∃ v, out = some v
  ensures ∀ k, k < stamps.length →
    ∃ v, out = some v ∧ stamps[k]! ≤ v
  ensures ∀ v, out = some v →
    ∃ k, k < stamps.length ∧ stamps[k]! = v
  do
    -- impl-start
    let mut result : Option Int := none
    let mut i := stamps.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ stamps.length
      invariant result = latestStamp (stamps.drop i)
      done_with i = 0
      decreasing i
    do
      let c := stamps[i - 1]!
      result := some (match result with | none => c | some m => max m c)
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `latestStamp` peels one running-maximum step. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma latestStamp_drop_step (stamps : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ stamps.length) :
    latestStamp (stamps.drop (i - 1)) =
      some (match latestStamp (stamps.drop i) with
            | none => stamps[i - 1]! | some m => max stamps[i - 1]! m) := by
  have hlt : i - 1 < stamps.length := by omega
  have hcons : stamps.drop (i - 1) = stamps[i - 1]! :: stamps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, latestStamp_cons]

/- `latestStamp` is `none` exactly on the empty collection. -/
@[grind] lemma latestStamp_eq_none_iff (xs : List Int) :
    latestStamp xs = none ↔ xs = [] := by
  cases xs with
  | nil => simp [latestStamp]
  | cons c cs => simp [latestStamp]

/- Every reported stamp dominates each collected stamp. -/
@[grind] lemma latestStamp_dominates (xs : List Int) :
    ∀ k, k < xs.length → ∃ v, latestStamp xs = some v ∧ xs[k]! ≤ v := by
  induction xs with
  | nil => intro k h; simp at h
  | cons c cs ih =>
      intro k h
      cases hcs : latestStamp cs with
      | none =>
          have hcsempty : cs = [] := (latestStamp_eq_none_iff cs).mp hcs
          subst hcsempty
          have hk0 : k = 0 := by simp at h; omega
          subst hk0
          exact ⟨c, by simp [latestStamp], by simp⟩
      | some m =>
          have hgoal : latestStamp (c :: cs) = some (max c m) := by
            rw [latestStamp_cons, hcs]
          rcases k with _ | k
          · exact ⟨max c m, hgoal, by simpa using le_max_left c m⟩
          · refine ⟨max c m, hgoal, ?_⟩
            have h' : k < cs.length := by simpa using h
            obtain ⟨v, hv, hle⟩ := ih k h'
            rw [hcs] at hv
            have hvm : m = v := by simpa using hv
            have hidx : (c :: cs)[k+1]! = cs[k]! := by
              simp [List.getElem!_eq_getElem?_getD]
            rw [hidx, hvm]
            exact le_trans hle (le_max_right c v)

/- Every reported stamp is one of the collected stamps. -/
@[grind] lemma latestStamp_member (xs : List Int) :
    ∀ v, latestStamp xs = some v → ∃ k, k < xs.length ∧ xs[k]! = v := by
  induction xs with
  | nil => intro v h; simp [latestStamp] at h
  | cons c cs ih =>
      intro v h
      rw [latestStamp_cons] at h
      cases hcs : latestStamp cs with
      | none =>
          rw [hcs] at h
          have hvc : v = c := by simp at h; exact h.symm
          subst hvc
          exact ⟨0, by simp, by simp⟩
      | some m =>
          rw [hcs] at h
          have hv : v = max c m := by simp at h; exact h.symm
          subst hv
          rcases max_choice c m with hmc | hmc
          · rw [hmc]; exact ⟨0, by simp, by simp⟩
          · rw [hmc]
            obtain ⟨k, hk, hkm⟩ := ih m (by rw [hcs])
            refine ⟨k+1, by simpa using hk, ?_⟩
            have hidx : (c :: cs)[k+1]! = cs[k]! := by
              simp [List.getElem!_eq_getElem?_getD]
            rw [hidx]; exact hkm

prove_correct latestLastmod by
  loom_solve
  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
  rw [‹result = latestStamp (stamps.drop i)›]
  simp [max_comm]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ / refinement-fidelity adversarial audit for django__django-16255 (velvet). VERDICT: SOUND.

Spec structure: clause 1 `ensures out = latestStamp stamps` extensionally pins the output to a CONCRETE TOTAL recursive `def` (running maximum with `none` empty base), backed by clauses 2-5 (empty->none, nonempty->some, dominance, membership). Total-correctness semantics (`loom.semantics.termination "total"`) excludes the diverging-impl class that an earlier partial-correctness revision admitted. This leaves no room for a verifying-but-wrong impl over the modeled domain.

PROTOCOL RESULTS (all files same_spec=True vs frozen Solution.lean, confirmed via swebench_unified.markers.same_spec + velvet backend; all verified with scripts/lean_verify.sh <file>):
- Positive control pos_control.lean (structurally-different correct impl: max step commuted to `max m c`, proof closed with simp [max_comm]): EXIT 0 (verifies) -> spec non-vacuous.
- atk1_prepatch (seed `some 0`, ORIGINAL proof tail): EXIT 1. Fails on exactly the empty-section clause: unsolved `some 0 = latestStamp (List.drop stamps.length stamps)` => `some 0 = none`. PREPATCH REPRODUCED, divergence isolated to empty section = the real bug (G-DIFF).
- atk2_none (return none): EXIT 1 (metavariables/unsolved, none != latestStamp).
- atk3_min (running MINIMUM): EXIT 1, unsolved `ensures_5: result_1 = latestStamp stamps`.
- atk4_head (some stamps[0]!, none if empty; boundary/off-value): EXIT 1, unsolved `ensures_5: some (stamps[0]?.getD 0) = latestStamp stamps`.
- atk5_const (return some 0): EXIT 1 (unsolved/metavariables).
- atk6_offbyone (i := stamps.length - 1, skips last elem; control-flow-effect): EXIT 1.
- atk7_partial (partial-domain: correct on empty->none, else some 0; wrong membership): EXIT 1, unsolved `ensures_5: some 0 = latestStamp stamps`.
- atk8_droptail (ungrounded-oracle echo DROPPED: `latestStamp (stamps.drop 1)` = max over wrong sub-collection): EXIT 1, unsolved dominance/nonempty/`ensures_5: latestStamp stamps.tail = latestStamp stamps`.
Every rejection is a GENUINE unsolved spec-clause goal (inspected logs), not a parse/syntax error; attacks were given a generous best-effort proof tail (loom_solve <;> first | rfl | simp_all | grind | drop_step;grind | omega) so failure reflects the impl.

RESOLVE OBLIGATION: vacuous. Step 2 requires materializing+resolve-running the faithful refined patch for EVERY wrong impl that VERIFIES. ZERO wrong impls verified, so there is no verifying-wrong-impl whose patch could fail to resolve. `patches` is therefore empty by construction (not skipped). The gold change is the one-liner `max([...]) -> max([...], default=None)` at django/contrib/sitemaps/__init__.py:170 (confirmed verbatim from the frozen dataset row; F2P test_callable_sitemod_no_items). NOTE: the bundle dir has no patch.diff file (only Solution/prepatch/refinement/mapping/axiom_check/conformance/meta/verdict); refinement.md refers to patch.diff as gold-verbatim and it matches the dataset patch.

A-LEG / correspondence audit (my mandate focus):
- Axioms region is EMPTY (comment-only); grep confirms no `axiom`/`opaque`/`sorry`/`admit` consumed. No A-consumed legs, so no axiom-soundness trust point.
- refinement.md legs: A1 (R: `List Int` <-> list of comparable date/datetime stamps, order-only bijection), A2 (A-REFERENCE: the changed `max(...,default=None)` reduction modeled DEEPLY as `latestStamp`, validated == real Python builtin by G-AX), A3 (R: none<->absent marker, some v<->max). NO kind-3 legs. Correspondence of the single A-reference to the real callee holds.
- G-AX (axiom_check.py) EXIT 0: `latestStamp(values) == max(values, default=None)` over 14 boundary (incl. empty list) + 50000 fuzz (seed 16255, n in [0,16]); empty -> None without raising. The A-reference correspondence is machine-validated.
- Int carrier faithfulness: date/datetime total order => max order-only => faithful; empty behavior type-independent; unchanged guards (hasattr/callable/except TypeError/non-callable branch) correctly out of modeled scope and untouched by the patch.

Ran 8 distinct attacks (partial-domain atk7, boundary atk4, control-flow-effect atk6, ungrounded-oracle echo atk8, plus prepatch/none/min/const) — none breaks the spec. Docker oracle reachable via `docker` (SG_DOCKER_OK) but not exercised because no resolve run was required (no verifying wrong impl).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1_prepatch.lean`, `atk2_none.lean`, `atk3_min.lean`, `atk4_head.lean`, `atk5_const.lean`, `atk6_offbyone.lean`, `atk7_partial.lean`, `atk8_droptail.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_none.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_min.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_head.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_const.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_partial.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_droptail.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: the modeled reduction is a bounded fold over a finite
-- stamp list that always terminates and returns, so a diverging implementation
-- must NOT satisfy the spec (partial correctness would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the reported value is the greatest of the collected
--  per-entry stamps, modeled deeply as a running maximum over `List Int`. There
--  is no unchanged library callee the proof must axiomatize.)
-- axioms-end

-- pure-start
/- The latest stamp reported across a collection of comparable per-entry stamps.
   With no entries the collection is empty and there is no stamp to report, so
   the result is the absent marker `none` (reporting a latest stamp over an empty
   collection must NOT fail). With one or more entries the result is the greatest
   stamp. Front-recursive so a single unfold is available per loop step (the
   Velvet fold pattern). -/
def latestStamp : List Int → Option Int
  | []      => none
  | c :: cs =>
      some (match latestStamp cs with
            | none   => c
            | some m => max c m)

@[grind] lemma latestStamp_nil : latestStamp [] = none := rfl
@[grind] lemma latestStamp_cons (c : Int) (cs : List Int) :
    latestStamp (c :: cs) =
      some (match latestStamp cs with | none => c | some m => max c m) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A section that exposes a per-entry modification stamp reports the most recent
   stamp across its entries. The per-entry stamp function applied across the
   enumerated entries yields a collection of comparable values, modeled as
   `List Int`; the reported value is `Option Int`.

   Two guarantees pin the behavior the issue demands:

   - when the section enumerates NO entries, the collection is empty and the
     reported value is the absent marker `none` — computing a latest stamp over
     an empty section must NOT fail;
   - when the section enumerates one or more entries, the reported value is the
     greatest stamp in the collection: it is one of the collected stamps and is
     greater than or equal to every collected stamp.

   `stamps` is read-only (not `mut`); the reduction builds a fresh result and
   mutates nothing (directive 5). -/
method latestLastmod (stamps : List Int) return (out : Option Int)
  ensures out = latestStamp stamps
  ensures stamps.length = 0 → out = none
  ensures stamps.length > 0 → ∃ v, out = some v
  ensures ∀ k, k < stamps.length →
    ∃ v, out = some v ∧ stamps[k]! ≤ v
  ensures ∀ v, out = some v →
    ∃ k, k < stamps.length ∧ stamps[k]! = v
  do
    -- impl-start
    let mut result : Option Int := none
    let mut i := stamps.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ stamps.length
      invariant result = latestStamp (stamps.drop i)
      done_with i = 0
      decreasing i
    do
      let c := stamps[i - 1]!
      result := some (match result with | none => c | some m => max m c)
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `latestStamp` peels one running-maximum step. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma latestStamp_drop_step (stamps : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ stamps.length) :
    latestStamp (stamps.drop (i - 1)) =
      some (match latestStamp (stamps.drop i) with
            | none => stamps[i - 1]! | some m => max stamps[i - 1]! m) := by
  have hlt : i - 1 < stamps.length := by omega
  have hcons : stamps.drop (i - 1) = stamps[i - 1]! :: stamps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, latestStamp_cons]

/- `latestStamp` is `none` exactly on the empty collection. -/
@[grind] lemma latestStamp_eq_none_iff (xs : List Int) :
    latestStamp xs = none ↔ xs = [] := by
  cases xs with
  | nil => simp [latestStamp]
  | cons c cs => simp [latestStamp]

/- Every reported stamp dominates each collected stamp. -/
@[grind] lemma latestStamp_dominates (xs : List Int) :
    ∀ k, k < xs.length → ∃ v, latestStamp xs = some v ∧ xs[k]! ≤ v := by
  induction xs with
  | nil => intro k h; simp at h
  | cons c cs ih =>
      intro k h
      cases hcs : latestStamp cs with
      | none =>
          have hcsempty : cs = [] := (latestStamp_eq_none_iff cs).mp hcs
          subst hcsempty
          have hk0 : k = 0 := by simp at h; omega
          subst hk0
          exact ⟨c, by simp [latestStamp], by simp⟩
      | some m =>
          have hgoal : latestStamp (c :: cs) = some (max c m) := by
            rw [latestStamp_cons, hcs]
          rcases k with _ | k
          · exact ⟨max c m, hgoal, by simpa using le_max_left c m⟩
          · refine ⟨max c m, hgoal, ?_⟩
            have h' : k < cs.length := by simpa using h
            obtain ⟨v, hv, hle⟩ := ih k h'
            rw [hcs] at hv
            have hvm : m = v := by simpa using hv
            have hidx : (c :: cs)[k+1]! = cs[k]! := by
              simp [List.getElem!_eq_getElem?_getD]
            rw [hidx, hvm]
            exact le_trans hle (le_max_right c v)

/- Every reported stamp is one of the collected stamps. -/
@[grind] lemma latestStamp_member (xs : List Int) :
    ∀ v, latestStamp xs = some v → ∃ k, k < xs.length ∧ xs[k]! = v := by
  induction xs with
  | nil => intro v h; simp [latestStamp] at h
  | cons c cs ih =>
      intro v h
      rw [latestStamp_cons] at h
      cases hcs : latestStamp cs with
      | none =>
          rw [hcs] at h
          have hvc : v = c := by simp at h; exact h.symm
          subst hvc
          exact ⟨0, by simp, by simp⟩
      | some m =>
          rw [hcs] at h
          have hv : v = max c m := by simp at h; exact h.symm
          subst hv
          rcases max_choice c m with hmc | hmc
          · rw [hmc]; exact ⟨0, by simp, by simp⟩
          · rw [hmc]
            obtain ⟨k, hk, hkm⟩ := ih m (by rw [hcs])
            refine ⟨k+1, by simpa using hk, ?_⟩
            have hidx : (c :: cs)[k+1]! = cs[k]! := by
              simp [List.getElem!_eq_getElem?_getD]
            rw [hidx]; exact hkm

prove_correct latestLastmod by
  loom_solve
  rw [latestStamp_drop_step stamps i (by omega) (by omega)]
  rw [‹result = latestStamp (stamps.drop i)›]
  simp [max_comm]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ / refinement-fidelity adversarial audit for django__django-16255 (velvet). VERDICT: SOUND.

Spec structure: clause 1 `ensures out = latestStamp stamps` extensionally pins the output to a CONCRETE TOTAL recursive `def` (running maximum with `none` empty base), backed by clauses 2-5 (empty->none, nonempty->some, dominance, membership). Total-correctness semantics (`loom.semantics.termination "total"`) excludes the diverging-impl class that an earlier partial-correctness revision admitted. This leaves no room for a verifying-but-wrong impl over the modeled domain.

PROTOCOL RESULTS (all files same_spec=True vs frozen Solution.lean, confirmed via swebench_unified.markers.same_spec + velvet backend; all verified with scripts/lean_verify.sh <file>):
- Positive control pos_control.lean (structurally-different correct impl: max step commuted to `max m c`, proof closed with simp [max_comm]): EXIT 0 (verifies) -> spec non-vacuous.
- atk1_prepatch (seed `some 0`, ORIGINAL proof tail): EXIT 1. Fails on exactly the empty-section clause: unsolved `some 0 = latestStamp (List.drop stamps.length stamps)` => `some 0 = none`. PREPATCH REPRODUCED, divergence isolated to empty section = the real bug (G-DIFF).
- atk2_none (return none): EXIT 1 (metavariables/unsolved, none != latestStamp).
- atk3_min (running MINIMUM): EXIT 1, unsolved `ensures_5: result_1 = latestStamp stamps`.
- atk4_head (some stamps[0]!, none if empty; boundary/off-value): EXIT 1, unsolved `ensures_5: some (stamps[0]?.getD 0) = latestStamp stamps`.
- atk5_const (return some 0): EXIT 1 (unsolved/metavariables).
- atk6_offbyone (i := stamps.length - 1, skips last elem; control-flow-effect): EXIT 1.
- atk7_partial (partial-domain: correct on empty->none, else some 0; wrong membership): EXIT 1, unsolved `ensures_5: some 0 = latestStamp stamps`.
- atk8_droptail (ungrounded-oracle echo DROPPED: `latestStamp (stamps.drop 1)` = max over wrong sub-collection): EXIT 1, unsolved dominance/nonempty/`ensures_5: latestStamp stamps.tail = latestStamp stamps`.
Every rejection is a GENUINE unsolved spec-clause goal (inspected logs), not a parse/syntax error; attacks were given a generous best-effort proof tail (loom_solve <;> first | rfl | simp_all | grind | drop_step;grind | omega) so failure reflects the impl.

RESOLVE OBLIGATION: vacuous. Step 2 requires materializing+resolve-running the faithful refined patch for EVERY wrong impl that VERIFIES. ZERO wrong impls verified, so there is no verifying-wrong-impl whose patch could fail to resolve. `patches` is therefore empty by construction (not skipped). The gold change is the one-liner `max([...]) -> max([...], default=None)` at django/contrib/sitemaps/__init__.py:170 (confirmed verbatim from the frozen dataset row; F2P test_callable_sitemod_no_items). NOTE: the bundle dir has no patch.diff file (only Solution/prepatch/refinement/mapping/axiom_check/conformance/meta/verdict); refinement.md refers to patch.diff as gold-verbatim and it matches the dataset patch.

A-LEG / correspondence audit (my mandate focus):
- Axioms region is EMPTY (comment-only); grep confirms no `axiom`/`opaque`/`sorry`/`admit` consumed. No A-consumed legs, so no axiom-soundness trust point.
- refinement.md legs: A1 (R: `List Int` <-> list of comparable date/datetime stamps, order-only bijection), A2 (A-REFERENCE: the changed `max(...,default=None)` reduction modeled DEEPLY as `latestStamp`, validated == real Python builtin by G-AX), A3 (R: none<->absent marker, some v<->max). NO kind-3 legs. Correspondence of the single A-reference to the real callee holds.
- G-AX (axiom_check.py) EXIT 0: `latestStamp(values) == max(values, default=None)` over 14 boundary (incl. empty list) + 50000 fuzz (seed 16255, n in [0,16]); empty -> None without raising. The A-reference correspondence is machine-validated.
- Int carrier faithfulness: date/datetime total order => max order-only => faithful; empty behavior type-independent; unchanged guards (hasattr/callable/except TypeError/non-callable branch) correctly out of modeled scope and untouched by the patch.

Ran 8 distinct attacks (partial-domain atk7, boundary atk4, control-flow-effect atk6, ungrounded-oracle echo atk8, plus prepatch/none/min/const) — none breaks the spec. Docker oracle reachable via `docker` (SG_DOCKER_OK) but not exercised because no resolve run was required (no verifying wrong impl).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-16255/velvet. (1) same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend)=True — spec region (method sig, 5 ensures clauses, latestStamp def + grind lemmas) is byte-identical across variants; only the impl region differs. (2) Modeled latestStamp corresponds to the changed reduction max([self.lastmod(item) for item in self.items()], default=None) at django/contrib/sitemaps/__init__.py:170. Real repo confirmed: prepatch is max([...]) (raises ValueError on empty); gold adds default=None (empty->None). Model: empty->none, non-empty->greatest — exact match. (3) G-AX axiom_check.py PASSED: latestStamp(values)==max(values,default=None) over 14 boundary cases (incl. []) + 50000 pinned-seed(16255) fuzz inputs; no divergence, empty reports None without raising. (4) The ensures clauses (out=latestStamp stamps; empty->none; nonempty->some; dominance ∀k stamps[k]!≤v; membership ∀v∃k stamps[k]!=v) jointly characterize exactly 'greatest element else none' — neither too strong nor too weak vs max(...,default=None). List Int is a faithful carrier for totally-ordered date/datetime stamps (only comparability + empty split used); unchanged guards (hasattr/callable/except TypeError) correctly out of scope, untouched by patch. (5) Solution.lean verifies (exit 0). Prepatch fails exactly at empty-section clause (some 0 = none, G-DIFF), confirming spec discriminates the real bug. No input found where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified the consumer spec view via markers.spec_view (VelvetBackend): impl region and prove_correct body are elided; pure helper `latestStamp`, lemmas, method signature + ensures clauses, and behavioral comments pass through. same_spec(Solution.lean, Solution_prepatch.lean)=True — the frozen spec is identical across the diff, so the spec view carries no prepatch/postpatch discriminator. Mechanical leakage.screen passes (no hard failures) and bundle is NOT relaxed (relaxed_leakage flag absent, G-LEAK status 'pass').

Semantic judgment (against the public problem_statement ONLY, not hints_text): the gold edit is `max([...])` -> `max([...], default=None)`, delta = empty collection returns None instead of raising ValueError. The PUBLIC problem_statement already discloses everything of substance: the exact function get_latest_lastmod, the verbatim changed line, the ValueError-on-empty failure mode, AND a candidate fix that returns None for the empty case. The spec view's ensures clauses (`stamps.length = 0 -> out = none`; `out = latestStamp stamps` with non-empty -> maximum) and the comment 'computing a latest stamp over an empty collection must NOT fail' merely restate this already-public empty-vs-nonempty behavior, abstracted to an Option-valued fold over List Int. It is if anything LESS prescriptive than the problem_statement (which shows literal Python + a candidate patch).

The specific gold MECHANISM (`default=None` keyword arg) appears only in hints_text ('The default argument of max() can be used'), which is out of scope. The spec view never names `default=None` and does not reveal the edit beyond the public statement.

Identifier/narration checks: spec-view identifiers (latestLastmod, latestStamp, stamps, out) do not embed the patched repo symbol get_latest_lastmod; 'lastmod' is already public in problem_statement; no diff markers; no narration tokens (bug/fix/prepatch/etc.) in spec-view comments. refinement.md, mapping.md, meta.json are audit-side artifacts, not the consumer spec view, so out of scope for this gate. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
