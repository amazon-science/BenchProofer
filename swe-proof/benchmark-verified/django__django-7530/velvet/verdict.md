# P2 adversarial audit — django__django-7530

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 16 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch_union.lean`, `atk_2_boundary_skip_first.lean`, `atk_3_offbyone_elem.lean`, `atk_4_break_last.lean`, `atk_5_partial_domain.lean`, `atk_6_dedup_multiset.lean`, `atk_7_rotate_models.lean`, `atk_8_donewith_false.lean`, `atk_9_oob_start_echo.lean`, `atk_10_reverse_order.lean`, `atk_11_union_closed.lean`, +3 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_14_echo_map_flatten.lean`, `atk_16_foldr_flagged_refinement.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None against the SPEC. No same-spec wrong impl verified: all 14 wrong impls were rejected, and the 2 impls that verified (atk_14, atk_16) are behaviourally correct consumers of the carrier whose materialized faithful patches BOTH RESOLVED under the official harness. So verify=>correct is not refuted and G-EQ is SOUND.

HOWEVER, an ORACLE defect (outside G-EQ's remit, reported for the record) was found and machine-confirmed. The frozen row's FAIL_TO_PASS for django__django-7530 is ["test_squashmigrations_initial_attribute (migrations.test_commands.SquashMigrationsTests)"], which is UNRELATED to this fix; the test the gold test_patch actually adds/strengthens (test_makemigrations_consistency_checks_respect_routers) appears in NEITHER F2P nor the 59 P2P. CONTROL RUN: patch_oracle_control_bug_retained.diff is a comment-only patch that LEAVES THE PRE-PATCH BUGGY LINE `for model in apps.get_models(app_label)` COMPLETELY UNCHANGED. Executed run_resolve => resolved=True, completed=True, F2P 1/1 ok, P2P 59/59 ok. That is, the buggy code resolves this instance. Consequence: for THIS row, 'resolves' carries no information about the makemigrations fix, so the resolve half of the bundle's biconditional is anchored on a vacuous oracle. This makes 'no verifying attack failed to resolve' unfalsifiable-by-construction here rather than evidence of strength -- the real discriminating power in this bundle comes from G-DIFF/G-PBT/G-CONF and from the postcondition rejections recorded below, not from G-RESOLVE.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_union.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,6 +61,7 @@
   ensures out = allPairs apps
   do
     -- impl-start
+    let everyModel : List Nat := (apps.map (fun a => a.2)).flatten
     let mut result : List (Nat × Nat) := []
     let mut i := apps.length
     while i > 0
@@ -70,7 +71,7 @@
       decreasing i
     do
       let a := apps[i - 1]!
-      result := appPairs a ++ result
+      result := (everyModel.map (fun m => (a.1, m))) ++ result
       i := i - 1
     return result
     -- impl-end
@@ -91,5 +92,7 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  all_goals try rw [allPairs_drop_step apps i (by omega) (by omega)]
+  all_goals try simp_all
+  all_goals try grind
+  all_goals try omega
```

Attack 2 — `atk_2_boundary_skip_first.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
     -- impl-start
     let mut result : List (Nat × Nat) := []
     let mut i := apps.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ apps.length
       invariant result = allPairs (apps.drop i)
       done_with i = 0
@@ -91,5 +91,7 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  all_goals try rw [allPairs_drop_step apps i (by omega) (by omega)]
+  all_goals try simp_all
+  all_goals try grind
+  all_goals try omega
```

Attack 3 — `atk_3_offbyone_elem.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,7 +69,7 @@
       done_with i = 0
       decreasing i
     do
-      let a := apps[i - 1]!
+      let a := apps[i]!
       result := appPairs a ++ result
       i := i - 1
     return result
@@ -91,5 +91,7 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  all_goals try rw [allPairs_drop_step apps i (by omega) (by omega)]
+  all_goals try simp_all
+  all_goals try grind
+  all_goals try omega
```

Attack 4 — `atk_4_break_last.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,6 +69,7 @@
       done_with i = 0
       decreasing i
     do
+      if i = 1 then break
       let a := apps[i - 1]!
       result := appPairs a ++ result
       i := i - 1
@@ -91,5 +92,7 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  all_goals try rw [allPairs_drop_step apps i (by omega) (by omega)]
+  all_goals try simp_all
+  all_goals try grind
+  all_goals try omega
```

Attack 5 — `atk_5_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,10 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    if apps.length ≤ 1 then
+      return allPairs apps
+    else
+      return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +83,3 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
```

Attack 6 — `atk_6_dedup_multiset.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,8 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    let out := (allPairs apps).dedup
+    return out
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +81,3 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
```

Attack 7 — `atk_7_rotate_models.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,11 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    let models : List (List Nat) := apps.map (fun a => a.2)
+    let rotated : List AppEntry :=
+      (apps.zipIdx).map (fun p => (p.1.1, (models.rotate 1)[p.2]!))
+    let out := allPairs rotated
+    return out
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +84,3 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
```

Attack 8 — `atk_8_donewith_false.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,12 +65,9 @@
     let mut i := apps.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
+      done_with False
       decreasing i
     do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
       i := i - 1
     return result
     -- impl-end
@@ -91,5 +88,7 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  all_goals try rw [allPairs_drop_step apps i (by omega) (by omega)]
+  all_goals try simp_all
+  all_goals try grind
+  all_goals try omega
```

Attack 9 — `atk_9_oob_start_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,9 +62,9 @@
   do
     -- impl-start
     let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
+    let mut i := apps.length + 1
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
+      invariant 0 ≤ i ∧ i ≤ apps.length + 1
       invariant result = allPairs (apps.drop i)
       done_with i = 0
       decreasing i
@@ -91,5 +91,13 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  rcases Nat.lt_or_ge (i - 1) apps.length with hlt | hge
+  · rw [allPairs_drop_step apps i (by omega) (by omega)]
+    simp_all
+  · have hdef : apps[i - 1]! = (default : Nat × List Nat) := by
+      rw [List.getElem!_eq_getElem?_getD]
+      rw [List.getElem?_eq_none hge]
+      rfl
+    have h1 : apps.drop (i - 1) = [] := List.drop_eq_nil_of_le hge
+    have h2 : apps.drop i = [] := List.drop_eq_nil_of_le (by omega)
+    simp_all [appPairs]
```

Attack 10 — `atk_10_reverse_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
       decreasing i
     do
       let a := apps[i - 1]!
-      result := appPairs a ++ result
+      result := result ++ appPairs a
       i := i - 1
     return result
     -- impl-end
@@ -91,5 +91,7 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  all_goals try rw [allPairs_drop_step apps i (by omega) (by omega)]
+  all_goals try simp_all
+  all_goals try grind
+  all_goals try omega
```

Attack 11 — `atk_11_union_closed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,9 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    let everyModel : List Nat := (apps.map (fun a => a.2)).flatten
+    let out := (apps.map (fun a => everyModel.map (fun m => (a.1, m)))).flatten
+    return out
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +82,3 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
```

Attack 12 — `atk_12_skip_first_closed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,8 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    let out := allPairs apps.tail
+    return out
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +81,3 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
```

Attack 13 — `atk_13_first_app_models_closed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,9 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    let firstModels : List Nat := (apps.head?.map (fun a => a.2)).getD []
+    let out := (apps.map (fun a => firstModels.map (fun m => (a.1, m)))).flatten
+    return out
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +82,3 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
```

Attack 14 — `atk_14_echo_map_flatten.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -61,18 +61,8 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    let out := (apps.map appPairs).flatten
+    return out
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +81,9 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  have h : ∀ (l : List AppEntry), (l.map appPairs).flatten = allPairs l := by
+    intro l
+    induction l with
+    | nil => simp [allPairs]
+    | cons a t ih => simp [allPairs_cons, ih]
+  simp_all [h]
```

Attack 15 — `atk_15_partial_shard_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,18 +61,11 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    let everyModel : List Nat := (apps.map (fun a => a.2)).flatten
+    if everyModel.length = everyModel.dedup.length then
+      return allPairs apps
+    else
+      return (apps.map (fun a => everyModel.map (fun m => (a.1, m)))).flatten
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +84,3 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
```

Attack 16 — `atk_16_foldr_flagged_refinement.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -61,18 +61,8 @@
   ensures out = allPairs apps
   do
     -- impl-start
-    let mut result : List (Nat × Nat) := []
-    let mut i := apps.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ apps.length
-      invariant result = allPairs (apps.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := apps[i - 1]!
-      result := appPairs a ++ result
-      i := i - 1
-    return result
+    let out := apps.foldr (fun a acc => appPairs a ++ acc) []
+    return out
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -91,5 +81,10 @@
 
 prove_correct appModelPairs by
   loom_solve
-  rw [allPairs_drop_step apps i (by omega) (by omega)]
-  simp_all
+  have h : ∀ (l : List AppEntry),
+      l.foldr (fun a acc => appPairs a ++ acc) [] = allPairs l := by
+    intro l
+    induction l with
+    | nil => simp [allPairs]
+    | cons a t ih => simp [allPairs_cons, ih]
+  simp_all [h]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The behaviour under specification — which (application
--  label, model) pairs are enumerated for the registry consistency scan — is
--  modeled DEEPLY over the application registry given as input: the per-label
--  pair expansion is spelled out directly in the `pure` region and built by the
--  loop. The proof consumes no callee contract. The fidelity of the registry
--  carrier to the live application registry is a type refinement, audited
--  mechanically by conformance_check.py / G-CONF — see mapping.md / refinement.md.)
-- axioms-end

-- pure-start
/- An entry of the application registry: an application's label paired with the
   list of models that application itself owns. (Labels and models are carried
   as opaque `Nat` identifiers; the proof needs no operation on them — see
   mapping.md for the identifier bijection.) -/
abbrev AppEntry := Nat × List Nat

/- The (label, model) pairs contributed by a single application: its own label
   paired with each of its own models, one pair per owned model. -/
def appPairs (a : AppEntry) : List (Nat × Nat) :=
  a.2.map (fun m => (a.1, m))

/- The full enumeration over the registry: concatenate, in registry order, the
   pairs contributed by each application. Front-recursive so a single unfold is
   available per loop step (the fold pattern). Each pair's model is therefore
   one of THAT application's own models — never a model belonging only to some
   other application in the registry. -/
def allPairs : List AppEntry → List (Nat × Nat)
  | []      => []
  | a :: rest => appPairs a ++ allPairs rest

@[grind] lemma allPairs_nil : allPairs [] = [] := rfl
@[grind] lemma allPairs_cons (a : AppEntry) (rest : List AppEntry) :
    allPairs (a :: rest) = appPairs a ++ allPairs rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The (application label, model) pairs the registry consistency scan validates,
   modeled over the application registry `apps` (each entry an application label
   together with the models that application owns). The result is the in-order
   concatenation, across every application, of that application's own (label,
   model) pairs: for every application the enumerated models range over exactly
   that application's own models.

   `apps` is read-only and the operation mutates none of its inputs
   (directive 5). -/
method appModelPairs (apps : List AppEntry) return (out : List (Nat × Nat))
  ensures out = allPairs apps
  do
    -- impl-start
    let out := allPairs apps
    return out
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `allPairs` peels one application's `appPairs`. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma allPairs_drop_step (apps : List AppEntry) (i : Nat)
    (hi : 0 < i) (hle : i ≤ apps.length) :
    allPairs (apps.drop (i - 1)) = appPairs apps[i - 1]! ++ allPairs (apps.drop i) := by
  have hlt : i - 1 < apps.length := by omega
  have hcons : apps.drop (i - 1) = apps[i - 1]! :: apps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, allPairs_cons]

prove_correct appModelPairs by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:** (all paths absolute, nothing written elsewhere). Repo root for commands:.

**METHOD.** Every file was produced by gen.py|gen2.py|gen3.py, which copy the bundle Solution.lean and rewrite ONLY the impl region and (b) the elided `prove_correct` tactic body. imports/axioms/pure/pre/post regions, the method signature + `ensures`, and the top-level allPairs_drop_step lemma are byte-identical. same_spec was re-verified for all 17 files at the end with markers.same_spec(velvet): 17/17 True, 17/17 differ from Solution.lean (TOTAL 17 BAD 0).

VERIFY COMMANDS (each: `bash scripts/lean_verify.sh <abs path> 300`, run from repo root, launched as concurrent background jobs in batches of <=4 per the parallelism directive; per-file stdout in <name>.log, exit codes collected in results.txt).

POSITIVE CONTROL (non-vacuity): pos_control.lean = loop-free `let out := allPairs apps; return out` => EXIT=0 VERIFIES. So the spec is not too strong and every rejection below is informative.

REJECTED (same spec, does NOT verify -- the spec bites). 14 of 16:
- atk_1_prepatch_union (THE PREPATCH BUG re-encoded in the frozen loop shape: every label x whole-registry model union) EXIT=1, unsolved `invariant_2: result = allPairs (apps.drop i)`. prepatch_reproduced=true.
- atk_11_union_closed (same bug, LOOP-FREE so the rejection is forced onto the postcondition) EXIT=1, unsolved `ensures_1: out = allPairs apps`, goal shown: (map (fun a => map (fun m => (a.1,m)) (map (.2) apps).flatten) apps).flatten = allPairs apps.
- atk_2_boundary_skip_first (guard `i > 1`, first app never contributes) EXIT=1, unsolved `done_1: i = 0`.
- atk_12_skip_first_closed (loop-free: allPairs apps.tail) EXIT=1, unsolved `ensures_1`, goal `allPairs apps.tail = allPairs apps`.
- atk_3_offbyone_elem (`apps[i]!` not `apps[i-1]!`) EXIT=1, unsolved `invariant_2`.
- atk_4_break_last (CONTROL-FLOW EFFECT: `if i = 1 then break`) EXIT=1, unsolved `invariant_2: result = allPairs apps.tail`.
- atk_5_partial_domain (PARTIAL DOMAIN: correct only for length<=1, [] otherwise) EXIT=1, unsolved `ensures_1`.
- atk_15_partial_shard_domain (sharper partial domain: correct unless two apps share a model identity, i.e. wrong exactly on the issue's sharded registries) EXIT=1, unsolved `ensures_1`.
- atk_6_dedup_multiset (MULTIPLICITY COLLAPSE, the `set(...)` refinement) EXIT=1, unsolved `ensures_1`.
- atk_7_rotate_models (CROSS-APP LEAK: each label paired with the NEXT app's models) EXIT=1, unsolved `ensures_1`.
- atk_13_first_app_models_closed (every label paired with the FIRST app's models) EXIT=1, unsolved `ensures_1`.
- atk_8_donewith_false (VACUITY probe: empty result + `done_with False`) EXIT=1, unsolved `done_1: False` with `if_neg : i = 0 |- False`. IMPORTANT: this shows Velvet PROVES the loop-exit assertion rather than assuming it, so the guarded-self-call/infeasible-guard vacuity mode does not apply here.
- atk_9_oob_start_echo (start i at apps.length+1 so the first read is out of bounds) EXIT=1, unsolved `invariant_2` (both branches).
- atk_10_reverse_order (append at the BACK => registry order reversed) EXIT=1, unsolved `invariant_2`. Reported honestly: mapping.md 2.1 makes the observable order-INSENSITIVE, so this impl's faithful patch WOULD resolve; it is listed to measure how much rejection power is order-strictness rather than content, not as a claimed weakness.

VERIFIED => RESOLVE-CHECKED (protocol step 2 discharged; both patches materialized from the real base_commit file by mkpatch.py and `git apply --check`ed OK before running):
- atk_14_echo_map_flatten (`(apps.map appPairs).flatten`, a CORRECT reshape) EXIT=0 VERIFIES. Faithful refined patch iterates the AppConfig objects directly (`for app_config in map(apps.get_app_config, consistency_check_labels) / for model in app_config.get_models()`, label read off the config) -- a structurally different real edit from gold with the same enumeration. EXECUTED run_resolve('django__django-7530', patch) => resolved=True completed=True attempts=1 note='resolved', F2P 1/1, P2P 59/59, 0 failures. => correct echo, NOT a weakness (build_one.`_derive_`* treats a candidate whose patch resolves as an echo).
- atk_16_foldr_flagged_refinement (`apps.foldr (fun a acc => appPairs a ++ acc) []`, also correct) EXIT=0 VERIFIES. This was my sharpest A/R-leg probe: the frozen spec is PARAMETRIC in the per-app model sets (`a.2` is an INPUT and the postcondition only says out = allPairs apps), so nothing INSIDE the spec pins which models an app 'owns' -- that binding lives only in mapping.md's R-leg and in G-CONF's shadow. Its faithful patch therefore reads `get_models(include_auto_created=True, include_swapped=True)` (still 'that application's own models' under mapping.md 2, whose own text calls these the private-API knobs). Independently confirmed with legcheck.py that this genuinely CHANGES the real enumeration: on an app owning {Real, Auto_M2M(auto_created), Swapped(swapped)} gold enumerates [('a','Real')] while the flagged form enumerates [('a','Auto_M2M'),('a','Real'),('a','Swapped')]. EXECUTED run_resolve => resolved=True completed=True attempts=2 flaky=True note='resolved on attempt 2/3', F2P 1/1, P2P 59/59. So even this latitude does not produce a non-resolving patch -- but see the counterexample field: that is largely because the oracle for this row does not test the fix at all.

STEP 3 -- refinement.md LEG AUDIT.
- Structural check reproduced from source: `grep -n 'axiom|:|' Solution.lean` finds NO `axiom` declaration and NO `:|` stub (the only hits are the prose word 'axioms' in the marker comments), and region_text shows the axioms region is comment-only while pre-conditions/post-conditions are EMPTY. meta.json corroborates: axioms=[], deep_model_references=[], G-AX status=skip ('no axiom_check.py'). So refinement.md's central claim -- no A-consumed and no A-reference leg -- is TRUE, and there is no axiom-soundness trust point to attack. The 4 legs are tagged R, R+I, I, R; there is no kind-3 (inexpressible-changed-op) leg: the op that actually changed (per-label model selection) is modeled deeply as appPairs/allPairs in the pure region, not hidden behind an axiom.
- I did NOT rely on the bundle's conformance_check.py (a transliteration shares any modeling error it is meant to detect). legcheck.py transcribes the REAL base_commit bodies of AppConfig.get_models (django/apps/config.py:174) and Apps.get_models (django/apps/registry.py:160) verbatim from `git show f8fab6f9...` and drives them. Results: the Lean model composed with mapping.md's R-leg equals the PATCHED generator on 6/6 registries (empty, single, issue-shards, 3-way disjoint, shared-model-name, empty-app) and DIVERGES from the pre-patch expansion on exactly the 4 non-degenerate ones -- confirming both the R-leg correspondence and that the model tracks the fix, not the bug. I also independently confirmed the mapping.md claim that pre-patch `apps.get_models(app_label)` binds app_label to the `include_auto_created` positional flag (Apps.get_models has signature (self, include_auto_created=False, include_swapped=False) -- no app_label), which is the stated root cause.

**VERDICT:** SOUND (advisory). 16 attacks re-encoded and machine-verified (>=5 floor met), prepatch bug reproduced and rejected, positive control verifies, and BOTH verifying impls had their faithful patches materialized and EXECUTED through the official harness -- both resolved, so verify=>correct is not refuted. Caveat that a reviewer should weigh, and the reason I am flagging it rather than silently passing: the resolve oracle for THIS row is vacuous w.r.t. the fix (control run above -- bug-retaining patch resolves, F2P is an unrelated squashmigrations test), so the resolve half of step 2 could not have failed for any patch here. G-EQ's own criterion is met on real evidence; the residual risk sits in G-RESOLVE/row selection, not in this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 16 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch_union.lean`, `atk_2_boundary_skip_first.lean`, `atk_3_offbyone_elem.lean`, `atk_4_break_last.lean`, `atk_5_partial_domain.lean`, `atk_6_dedup_multiset.lean`, `atk_7_rotate_models.lean`, `atk_8_donewith_false.lean`, `atk_9_oob_start_echo.lean`, `atk_10_reverse_order.lean`, `atk_11_union_closed.lean`, +3 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_14_echo_map_flatten.lean`, `atk_16_foldr_flagged_refinement.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None against the SPEC. No same-spec wrong impl verified: all 14 wrong impls were rejected, and the 2 impls that verified (atk_14, atk_16) are behaviourally correct consumers of the carrier whose materialized faithful patches BOTH RESOLVED under the official harness. So verify=>correct is not refuted and G-EQ is SOUND.

HOWEVER, an ORACLE defect (outside G-EQ's remit, reported for the record) was found and machine-confirmed. The frozen row's FAIL_TO_PASS for django__django-7530 is ["test_squashmigrations_initial_attribute (migrations.test_commands.SquashMigrationsTests)"], which is UNRELATED to this fix; the test the gold test_patch actually adds/strengthens (test_makemigrations_consistency_checks_respect_routers) appears in NEITHER F2P nor the 59 P2P. CONTROL RUN: patch_oracle_control_bug_retained.diff is a comment-only patch that LEAVES THE PRE-PATCH BUGGY LINE `for model in apps.get_models(app_label)` COMPLETELY UNCHANGED. Executed run_resolve => resolved=True, completed=True, F2P 1/1 ok, P2P 59/59 ok. That is, the buggy code resolves this instance. Consequence: for THIS row, 'resolves' carries no information about the makemigrations fix, so the resolve half of the bundle's biconditional is anchored on a vacuous oracle. This makes 'no verifying attack failed to resolve' unfalsifiable-by-construction here rather than evidence of strength -- the real discriminating power in this bundle comes from G-DIFF/G-PBT/G-CONF and from the postcondition rejections recorded below, not from G-RESOLVE.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_union.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_boundary_skip_first.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_offbyone_elem.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_break_last.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_dedup_multiset.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_rotate_models.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_donewith_false.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_oob_start_echo.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_reverse_order.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_union_closed.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_skip_first_closed.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_first_app_models_closed.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_echo_map_flatten.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15_partial_shard_domain.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_foldr_flagged_refinement.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The behaviour under specification — which (application
--  label, model) pairs are enumerated for the registry consistency scan — is
--  modeled DEEPLY over the application registry given as input: the per-label
--  pair expansion is spelled out directly in the `pure` region and built by the
--  loop. The proof consumes no callee contract. The fidelity of the registry
--  carrier to the live application registry is a type refinement, audited
--  mechanically by conformance_check.py / G-CONF — see mapping.md / refinement.md.)
-- axioms-end

-- pure-start
/- An entry of the application registry: an application's label paired with the
   list of models that application itself owns. (Labels and models are carried
   as opaque `Nat` identifiers; the proof needs no operation on them — see
   mapping.md for the identifier bijection.) -/
abbrev AppEntry := Nat × List Nat

/- The (label, model) pairs contributed by a single application: its own label
   paired with each of its own models, one pair per owned model. -/
def appPairs (a : AppEntry) : List (Nat × Nat) :=
  a.2.map (fun m => (a.1, m))

/- The full enumeration over the registry: concatenate, in registry order, the
   pairs contributed by each application. Front-recursive so a single unfold is
   available per loop step (the fold pattern). Each pair's model is therefore
   one of THAT application's own models — never a model belonging only to some
   other application in the registry. -/
def allPairs : List AppEntry → List (Nat × Nat)
  | []      => []
  | a :: rest => appPairs a ++ allPairs rest

@[grind] lemma allPairs_nil : allPairs [] = [] := rfl
@[grind] lemma allPairs_cons (a : AppEntry) (rest : List AppEntry) :
    allPairs (a :: rest) = appPairs a ++ allPairs rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The (application label, model) pairs the registry consistency scan validates,
   modeled over the application registry `apps` (each entry an application label
   together with the models that application owns). The result is the in-order
   concatenation, across every application, of that application's own (label,
   model) pairs: for every application the enumerated models range over exactly
   that application's own models.

   `apps` is read-only and the operation mutates none of its inputs
   (directive 5). -/
method appModelPairs (apps : List AppEntry) return (out : List (Nat × Nat))
  ensures out = allPairs apps
  do
    -- impl-start
    let out := allPairs apps
    return out
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `allPairs` peels one application's `appPairs`. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma allPairs_drop_step (apps : List AppEntry) (i : Nat)
    (hi : 0 < i) (hle : i ≤ apps.length) :
    allPairs (apps.drop (i - 1)) = appPairs apps[i - 1]! ++ allPairs (apps.drop i) := by
  have hlt : i - 1 < apps.length := by omega
  have hcons : apps.drop (i - 1) = apps[i - 1]! :: apps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, allPairs_cons]

prove_correct appModelPairs by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:** (all paths absolute, nothing written elsewhere). Repo root for commands:.

**METHOD.** Every file was produced by gen.py|gen2.py|gen3.py, which copy the bundle Solution.lean and rewrite ONLY the impl region and (b) the elided `prove_correct` tactic body. imports/axioms/pure/pre/post regions, the method signature + `ensures`, and the top-level allPairs_drop_step lemma are byte-identical. same_spec was re-verified for all 17 files at the end with markers.same_spec(velvet): 17/17 True, 17/17 differ from Solution.lean (TOTAL 17 BAD 0).

VERIFY COMMANDS (each: `bash scripts/lean_verify.sh <abs path> 300`, run from repo root, launched as concurrent background jobs in batches of <=4 per the parallelism directive; per-file stdout in <name>.log, exit codes collected in results.txt).

POSITIVE CONTROL (non-vacuity): pos_control.lean = loop-free `let out := allPairs apps; return out` => EXIT=0 VERIFIES. So the spec is not too strong and every rejection below is informative.

REJECTED (same spec, does NOT verify -- the spec bites). 14 of 16:
- atk_1_prepatch_union (THE PREPATCH BUG re-encoded in the frozen loop shape: every label x whole-registry model union) EXIT=1, unsolved `invariant_2: result = allPairs (apps.drop i)`. prepatch_reproduced=true.
- atk_11_union_closed (same bug, LOOP-FREE so the rejection is forced onto the postcondition) EXIT=1, unsolved `ensures_1: out = allPairs apps`, goal shown: (map (fun a => map (fun m => (a.1,m)) (map (.2) apps).flatten) apps).flatten = allPairs apps.
- atk_2_boundary_skip_first (guard `i > 1`, first app never contributes) EXIT=1, unsolved `done_1: i = 0`.
- atk_12_skip_first_closed (loop-free: allPairs apps.tail) EXIT=1, unsolved `ensures_1`, goal `allPairs apps.tail = allPairs apps`.
- atk_3_offbyone_elem (`apps[i]!` not `apps[i-1]!`) EXIT=1, unsolved `invariant_2`.
- atk_4_break_last (CONTROL-FLOW EFFECT: `if i = 1 then break`) EXIT=1, unsolved `invariant_2: result = allPairs apps.tail`.
- atk_5_partial_domain (PARTIAL DOMAIN: correct only for length<=1, [] otherwise) EXIT=1, unsolved `ensures_1`.
- atk_15_partial_shard_domain (sharper partial domain: correct unless two apps share a model identity, i.e. wrong exactly on the issue's sharded registries) EXIT=1, unsolved `ensures_1`.
- atk_6_dedup_multiset (MULTIPLICITY COLLAPSE, the `set(...)` refinement) EXIT=1, unsolved `ensures_1`.
- atk_7_rotate_models (CROSS-APP LEAK: each label paired with the NEXT app's models) EXIT=1, unsolved `ensures_1`.
- atk_13_first_app_models_closed (every label paired with the FIRST app's models) EXIT=1, unsolved `ensures_1`.
- atk_8_donewith_false (VACUITY probe: empty result + `done_with False`) EXIT=1, unsolved `done_1: False` with `if_neg : i = 0 |- False`. IMPORTANT: this shows Velvet PROVES the loop-exit assertion rather than assuming it, so the guarded-self-call/infeasible-guard vacuity mode does not apply here.
- atk_9_oob_start_echo (start i at apps.length+1 so the first read is out of bounds) EXIT=1, unsolved `invariant_2` (both branches).
- atk_10_reverse_order (append at the BACK => registry order reversed) EXIT=1, unsolved `invariant_2`. Reported honestly: mapping.md 2.1 makes the observable order-INSENSITIVE, so this impl's faithful patch WOULD resolve; it is listed to measure how much rejection power is order-strictness rather than content, not as a claimed weakness.

VERIFIED => RESOLVE-CHECKED (protocol step 2 discharged; both patches materialized from the real base_commit file by mkpatch.py and `git apply --check`ed OK before running):
- atk_14_echo_map_flatten (`(apps.map appPairs).flatten`, a CORRECT reshape) EXIT=0 VERIFIES. Faithful refined patch iterates the AppConfig objects directly (`for app_config in map(apps.get_app_config, consistency_check_labels) / for model in app_config.get_models()`, label read off the config) -- a structurally different real edit from gold with the same enumeration. EXECUTED run_resolve('django__django-7530', patch) => resolved=True completed=True attempts=1 note='resolved', F2P 1/1, P2P 59/59, 0 failures. => correct echo, NOT a weakness (build_one.`_derive_`* treats a candidate whose patch resolves as an echo).
- atk_16_foldr_flagged_refinement (`apps.foldr (fun a acc => appPairs a ++ acc) []`, also correct) EXIT=0 VERIFIES. This was my sharpest A/R-leg probe: the frozen spec is PARAMETRIC in the per-app model sets (`a.2` is an INPUT and the postcondition only says out = allPairs apps), so nothing INSIDE the spec pins which models an app 'owns' -- that binding lives only in mapping.md's R-leg and in G-CONF's shadow. Its faithful patch therefore reads `get_models(include_auto_created=True, include_swapped=True)` (still 'that application's own models' under mapping.md 2, whose own text calls these the private-API knobs). Independently confirmed with legcheck.py that this genuinely CHANGES the real enumeration: on an app owning {Real, Auto_M2M(auto_created), Swapped(swapped)} gold enumerates [('a','Real')] while the flagged form enumerates [('a','Auto_M2M'),('a','Real'),('a','Swapped')]. EXECUTED run_resolve => resolved=True completed=True attempts=2 flaky=True note='resolved on attempt 2/3', F2P 1/1, P2P 59/59. So even this latitude does not produce a non-resolving patch -- but see the counterexample field: that is largely because the oracle for this row does not test the fix at all.

STEP 3 -- refinement.md LEG AUDIT.
- Structural check reproduced from source: `grep -n 'axiom|:|' Solution.lean` finds NO `axiom` declaration and NO `:|` stub (the only hits are the prose word 'axioms' in the marker comments), and region_text shows the axioms region is comment-only while pre-conditions/post-conditions are EMPTY. meta.json corroborates: axioms=[], deep_model_references=[], G-AX status=skip ('no axiom_check.py'). So refinement.md's central claim -- no A-consumed and no A-reference leg -- is TRUE, and there is no axiom-soundness trust point to attack. The 4 legs are tagged R, R+I, I, R; there is no kind-3 (inexpressible-changed-op) leg: the op that actually changed (per-label model selection) is modeled deeply as appPairs/allPairs in the pure region, not hidden behind an axiom.
- I did NOT rely on the bundle's conformance_check.py (a transliteration shares any modeling error it is meant to detect). legcheck.py transcribes the REAL base_commit bodies of AppConfig.get_models (django/apps/config.py:174) and Apps.get_models (django/apps/registry.py:160) verbatim from `git show f8fab6f9...` and drives them. Results: the Lean model composed with mapping.md's R-leg equals the PATCHED generator on 6/6 registries (empty, single, issue-shards, 3-way disjoint, shared-model-name, empty-app) and DIVERGES from the pre-patch expansion on exactly the 4 non-degenerate ones -- confirming both the R-leg correspondence and that the model tracks the fix, not the bug. I also independently confirmed the mapping.md claim that pre-patch `apps.get_models(app_label)` binds app_label to the `include_auto_created` positional flag (Apps.get_models has signature (self, include_auto_created=False, include_swapped=False) -- no app_label), which is the stated root cause.

**VERDICT:** SOUND (advisory). 16 attacks re-encoded and machine-verified (>=5 floor met), prepatch bug reproduced and rejected, positive control verifies, and BOTH verifying impls had their faithful patches materialized and EXECUTED through the official harness -- both resolved, so verify=>correct is not refuted. Caveat that a reviewer should weigh, and the reason I am flagging it rather than silently passing: the resolve oracle for THIS row is vacuous w.r.t. the fix (control run above -- bug-retaining patch resolves, F2P is an unrelated squashmigrations test), so the resolve half of step 2 could not have failed for any patch here. G-EQ's own criterion is met on real evidence; the residual risk sits in G-RESOLVE/row selection, not in this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK ROLE: faithfulness-break (spec too strong / modeled function disagrees with the real callee on some input). I found NO diverging input. Verdict FAITHFUL.

### Spec-region identity
same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) => True. axioms/pure/pre/post regions plus the 'ensures out = allPairs apps' contract are byte-identical between the passing and pre-patch files; only impl/proof differ. The frozen contract discriminates, not an edited spec.

BASELINE / CONTROLS
- lean_verify.sh Solution.lean => exit 0, no sorry/admit. Solution_prepatch.lean => exit 1, 'unsolved goals' at prove_correct: the pre-patch whole-registry-union impl genuinely FAILS the frozen postcondition (G-DIFF real, not stipulated).
- Hygiene: no sorry/admit/axiom/':|' in Solution.lean; termination 'total', choice 'demonic'.
- **NON-VACUITY:** adding a false conjunct (ensures out != out) => exit 1 / unsolved goals, so the method context is feasible and the passing proof is not vacuous. NOTE: my first control attempt, an inline 'assert (False)', failed with 'Failed to parse an assertion without names' -- a PARSE error, not a semantic rejection. I discarded it and re-ran the control via the postcondition. Recording so the parse failure is not misread as a vacuity result.

### MODELED FUNCTION vs REAL CALLEE
Patched generator at makemigrations.py:105-108: (app_label, model) for app_label in consistency_check_labels for model in apps.get_app_config(app_label).get_models(). Spec: out = allPairs apps, with appPairs a = a.2.map (fun m => (a.1,m)).

### LIVE DIFFERENTIAL AGAINST THE REAL REPO (worktree at base_commit f8fab6f9, Django 1.11a, py3.8)
I did not rely on conformance_check.py's stdlib re-implementation. I stood up real configured Django registries and materialized the actual patched generator's pair stream, comparing it to allPairs over the mapping.md carrier (a.2 = get_app_config(L).get_models()):
- contenttypes; appA; appB; [appA,appB]; [appB,appA]; [appA,appB,contenttypes]: multiset equal True AND exact-list equal True in every case, 0 divergences.
- auto_created edge: appA has an implicit M2M (Book.authors) creating auto-created Book_authors. Real per-app get_models() omits it; allPairs over the filtered carrier omits it. Agreement.
- swapped edge: appB.Gadget with swappable GADGET_MODEL='appB.Widget'. Real omits Gadget; spec omits it. Agreement.
- proxy/abstract: proxy Proxy is included by the real callee and by the carrier; abstract Abstract is in neither. Agreement.
- app with no models module (nA): real yields nothing, carrier entry is (nA, []), allPairs contributes nothing. Agreement (the empty-list case the front-recursive allPairs handles by allPairs_nil).
- cross-app name collision (cA.Book and cB.Book) plus a model declared in cB's module but app_label='cA': real pairs and spec pairs identical; no spurious duplicate; every yielded model's `_meta`.app_label equals its pairing label.
- F2P app set [migrations, migrations2]: carrier [(migrations,[ModelWithCustomBase,UnmigratedModel]),(migrations2,[])]; multiset True, exact True, bug_differs True. The F2P assertion body (get_app_config(app).get_model(model_name) must not raise) PASSES on the spec's pairs and FAILS on the bug's pairs at ('migrations2','ModelWithCustomBase') -- exactly the assertion the test patch adds.
- Bug side verified live: apps.get_models(app_label) binds app_label to include_auto_created, so every label gets the whole-project union (e.g. ('appB','Author'), ('appA','Book_authors')). Real divergence confirmed; the spec tracks the fix.

### OVER-STRENGTH PROBE (does the contract pin an implementation rather than behaviour?)
I replaced the backward index fold with a structurally different but equally correct implementation, 'return apps.flatMap appPairs', with its own induction proof. It VERIFIES against the unmodified frozen contract (exit 0). So 'ensures out = allPairs apps' constrains the observable pair enumeration, not the loop shape -- not over-strong.

### ORDER-STRENGTH (the strongest available attack, and why it fails)
allPairs fixes registry order while consistency_check_labels is a Python set, so a priori the spec looks stronger than reality. It is not a defect: (a) the observable is order-insensitive -- pairs feed any(router.allow_migrate(...)) and the F2P test uses assert_any_call plus a per-call validity loop over mock_calls, never a fixed sequence; (b) empirically the exact list equality held on every live configuration once the carrier is taken in the set's own iteration order, i.e. allPairs is a sound representative of the set, and any set order is realizable by permuting the input list. A total-order spec over an unordered observable is a benign strengthening in the input variable, not a disagreement on any input.

### SHORT-CIRCUIT (second attack considered)
any() stops at the first truthy allow_migrate: with a router returning True only 1 of 3 pairs is actually passed, whereas allPairs is the FULL enumeration. This is a genuine abstraction gap, but not a faithfulness defect for the modeled function: the spec models the generator's pair stream (mapping.md step 4 scopes 'out' to the pairs the scan enumerates), the patch changes only that stream, and the F2P scenario mocks allow_migrate to return_value=False so the full stream is consumed. The gold patch changes nothing about the short-circuit. Flagging it as the one place the model is deliberately more total than a truthy-router execution.

### G-CONF HAS TEETH (I mutation-tested the oracle rather than trusting its OK)
- Baseline: exit 0 over 100,007 registries, seed 7530.
- Mutant A (shadow carrier = whole-registry union, i.e. the bug): FAIL with 5 disagreements, first at [(1,[10]),(2,[20])].
- Mutant B (subtle: carrier drops the auto_created/swapped filter, appconfig_get_models(owned,True,True)): FAIL, first at [(1,[(10,True,False),(11,False,True)]),(2,[(20,False,False)])].
So the gate rejects both the coarse and the subtle carrier infidelity; its OK is informative.

### Lean pure-region sanity
#eval confirms allPairs [(1,[10,11]),(2,[20])] = [(1,10),(1,11),(2,20)]; allPairs [] = []; an empty-model app contributes nothing. I proved on the side that every p in appPairs a satisfies p.1 = a.1 and p.2 in a.2, i.e. the spec really does forbid pairing a label with a foreign app's model -- the exact discriminating content of the fix.

### Conclusion
No input exists on which the modeled appModelPairs disagrees with the real patched callee, across auto_created, swapped, proxy, abstract, empty-app, cross-app-name-collision, reassigned-app_label, and the F2P app set. The contract admits an independent alternative implementation, so it is not implementation-pinning. Order totality is a benign strengthening over an order-insensitive observable. The only noted abstraction gap (any() short-circuit) is outside the modeled function's scope and orthogonal to the patch. Faithfulness attack fails: FAITHFUL.

**HOUSEKEEPING:** scratch under mktemp -d dirs; the base_commit worktree was removed with 'git worktree remove --force'; no tree-wide git operation was performed and the repo's pre-existing modified files were left untouched.

**ATTACK ROLE:** faithfulness-break (spec too strong / modeled function disagrees with the real callee on some input). I found NO diverging input. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage/gold-reconstruction audit of django__django-7530 velvet bundle. I did not rely on the recorded G-PANEL-3 status; I recomputed the consumer view and re-derived the verdict.

**CONSUMER VIEW ESTABLISHED.** Recomputed markers.spec_view(Solution.lean, velvet.language) directly. Confirmed via eval/dataset.py:258 + eval/prompts.py:`_spec_block` that the consumer receives exactly (a) problem_statement, (b) the spec_view string, (c) meta.json modeled_functions as 'model_symbol (<-> repo_symbol)' pairs. refinement.md, mapping.md, conformance_check.py, Solution_prepatch.lean, meta.json gate records and verdict.md are NOT in the consumer view (no reader in eval/container.py or eval/prompts.py touches them) -- so the strongest gold disclosures in this bundle are out of scope by construction.

SPEC-VIEW / PREPATCH BYTE IDENTITY. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True, and stronger: spec_view(Solution) == spec_view(Solution_prepatch) BYTE-IDENTICALLY. The spec view therefore carries zero residue that distinguishes the patched from the unpatched artifact -- a spec view that cannot tell gold from bug cannot leak gold. Verified the prepatch impl-region comments that DO narrate the bug ('Pre-image skeleton', 'the WHOLE-registry model list', 'everyModel', 'flatten', 'prove_correct MUST fail') are all correctly elided and absent from the prepatch spec view.

**MECHANICAL SCREEN.** leakage.screen re-run live: passed=True, hard_failures=[], warnings=[]. No gold-diff line reproduced, no diff markers, no patched file path, no narration vocabulary (`_NARRATION_RE` finds zero hits across the entire spec view -- notable given my prior finding that measure/justification prose often trips 'fixed'/'copy').

REPO-SYMBOL ECHO SWEEP (the real attack). Checked every distinctive symbol on either side of the gold hunk against the spec view. ABSENT from the spec view: get_app_config, get_models, AppConfig, apps.get_models, include_auto_created, include_swapped, object_name, `_meta`, consistency_check_labels, connection, alias, allow_migrate, router, makemigrations, loader, check_consistent_history, django/core/management/commands/makemigrations.py, and any line number (104-109 / 108). The spec view thus names NEITHER side of the swap. The mechanical edit -- replace apps.get_models(app_label) with apps.get_app_config(app_label).get_models() -- is not recoverable from the spec view; a solver must still find the call site and discover the correct registry API itself.

CRITICALLY, the deepest insight of this bug is absent: that Apps.get_models(self, include_auto_created=False, include_swapped=False) takes NO app_label, so the pre-patch call silently binds app_label to the include_auto_created positional flag and returns the whole-project union. That explanation exists only in mapping.md 'Pre-patch repo symbols (refinement audit only -- not in the consumer view)', explicitly out of the consumer view. Nothing in the spec view hints that the bug is a positional-argument mis-binding.

**DISCRIMINATOR IS ALREADY PUBLIC.** The strongest candidate leak lines are the pure-region/method doc comments: L27 'paired with each of its own models', L34 'one of THAT application's own models -- never a model belonging only to some other application', L56 'for every application the enumerated models range over exactly that application's own models', and the contract L61 'ensures out = allPairs apps'. These disclose the semantic direction of the fix: label L pairs with L's OWN models, not the global union.

But problem_statement discloses precisely this, in its own words: 'makemigrations incorrectly calls allow_migrate() for each app with all the models in the project RATHER THAN for each app with the APP'S MODELS', reinforced by 'invalid combinations for shards since not all shards have the same models'. The spec view's own-models framing is therefore a restatement of public text, not an increment over it. Leakage is judged against problem_statement only (leakage.py module docstring), and the delta here is empty. Per-app-own-models is also the irreducible content of the postcondition -- a spec that omitted it would specify nothing and could not pin the fix (see the G-DIFF role of the prepatch rival), so this is the faithful-spec floor, not over-disclosure.

ONLY NON-PUBLIC TOKEN considered: 'registry' (spec view, not in problem_statement). Rejected as a leak -- it names the domain object (the application registry) at the same altitude as the public text's 'each app ... models in the project'. It localizes no edit, names no module (django/apps/registry.py never appears), and identifies no API. A solver already told allow_migrate is called per-app-per-model necessarily reasons over the app registry.

MODELED-FUNCTION PAIR (also consumer-visible) checked: repo_symbol 'django.core.management.commands.makemigrations.Command.handle (consistency-scan generator)' at 'makemigrations.py:104-109'. This is edit LOCALIZATION, deliberately and uniformly provided by the harness in spec modes (MODES_WITH_SPEC / MODES_WITH_LOCALIZATION), not a spec-view leak, and it still does not disclose WHICH call to change or what to change it to.

**CONCLUSION:** the spec view discloses the fix's semantic direction, which problem_statement already states explicitly, and withholds the entire mechanical edit (both API names, the argument-binding root cause, the file/line of the changed expression). No spec-view line leaks the gold edit beyond problem_statement. Not my lane and not adjudicated here: G-EQ and G-PANEL-1 are recorded fail; my NO-LEAKAGE finding is scoped strictly to leakage/gold-reconstruction and does not vouch for the bundle overall.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.