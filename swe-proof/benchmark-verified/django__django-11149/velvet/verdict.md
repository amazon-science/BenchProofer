# P2 adversarial audit — django__django-11149

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.lean`, `atk_3.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,7 +93,7 @@
   do
     -- impl-start
     let r ← if autoCreated then
-        holdsAnyTargetPerm userHasPerm [Perm.change]
+        holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]
       else
         pure superResult
     return r
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,18 +49,8 @@
   ensures result = anyPerm userHasPerm perms
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := perms.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ perms.length
-      invariant acc = anyPerm userHasPerm (perms.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := perms[i - 1]!
-      acc := userHasPerm p || acc
-      i := i - 1
-    return acc
+    -- Echo: compute the same disjunction via the total library fold `List.any`.
+    return perms.any userHasPerm
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -79,8 +69,9 @@
 
 prove_correct holdsAnyTargetPerm by
   loom_solve
-  rw [anyPerm_drop_step userHasPerm perms i (by omega) (by omega)]
-  simp_all
+  induction perms with
+  | nil => rfl
+  | cons p ps ih => simp [List.any, anyPerm, ih]
 
 /- Authority to ADD a row of the link relation. An implicitly-created link
    relation carries no permissions of its own, so for it authority is derived
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -92,11 +92,9 @@
   ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
   do
     -- impl-start
-    let r ← if autoCreated then
-        holdsAnyTargetPerm userHasPerm [Perm.change]
-      else
-        pure superResult
-    return r
+    -- Echo: inline the specified disjunction at the call site rather than
+    -- delegating to holdsAnyTargetPerm; same boolean value.
+    return (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
     -- impl-end
 
 prove_correct addRelationAllowed by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,18 +49,12 @@
   ensures result = anyPerm userHasPerm perms
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := perms.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ perms.length
-      invariant acc = anyPerm userHasPerm (perms.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := perms[i - 1]!
-      acc := userHasPerm p || acc
-      i := i - 1
-    return acc
+    -- BUG (partial-domain): only tests the FIRST requested permission,
+    -- ignoring the rest. Correct on singleton lists, wrong for len>=2.
+    if perms.isEmpty then
+      return false
+    else
+      return userHasPerm perms[0]!
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -79,8 +73,6 @@
 
 prove_correct holdsAnyTargetPerm by
   loom_solve
-  rw [anyPerm_drop_step userHasPerm perms i (by omega) (by omega)]
-  simp_all
 
 /- Authority to ADD a row of the link relation. An implicitly-created link
    relation carries no permissions of its own, so for it authority is derived
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,10 @@
   ensures result = anyPerm userHasPerm perms
   do
     -- impl-start
+    -- BUG (boundary/off-by-one): starts the counter at length-1 so the last
+    -- element is never inspected (skips index length-1's disjunct).
     let mut acc : Bool := false
-    let mut i := perms.length
+    let mut i := perms.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ perms.length
       invariant acc = anyPerm userHasPerm (perms.drop i)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,8 +144,9 @@
   ensures result = (if autoCreated then anyPerm userHasPerm [Perm.view, Perm.change] else superResult)
   do
     -- impl-start
+    -- BUG: view gate demands CHANGE only, dropping the VIEW disjunct.
     let r ← if autoCreated then
-        holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]
+        holdsAnyTargetPerm userHasPerm [Perm.change]
       else
         pure superResult
     return r
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,18 +49,8 @@
   ensures result = anyPerm userHasPerm perms
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := perms.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ perms.length
-      invariant acc = anyPerm userHasPerm (perms.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := perms[i - 1]!
-      acc := userHasPerm p || acc
-      i := i - 1
-    return acc
+    -- Ungrounded-oracle echo: returns the spec function directly.
+    return anyPerm userHasPerm perms
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -79,8 +69,6 @@
 
 prove_correct holdsAnyTargetPerm by
   loom_solve
-  rw [anyPerm_drop_step userHasPerm perms i (by omega) (by omega)]
-  simp_all
 
 /- Authority to ADD a row of the link relation. An implicitly-created link
    relation carries no permissions of its own, so for it authority is derived
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,11 +92,8 @@
   ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
   do
     -- impl-start
-    let r ← if autoCreated then
-        holdsAnyTargetPerm userHasPerm [Perm.change]
-      else
-        pure superResult
-    return r
+    -- BUG: ignore autoCreated; always return inherited decision.
+    return superResult
     -- impl-end
 
 prove_correct addRelationAllowed by
@@ -109,11 +106,8 @@
   ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
   do
     -- impl-start
-    let r ← if autoCreated then
-        holdsAnyTargetPerm userHasPerm [Perm.change]
-      else
-        pure superResult
-    return r
+    -- BUG: ignore autoCreated; always return inherited decision.
+    return superResult
     -- impl-end
 
 prove_correct changeRelationAllowed by
@@ -126,11 +120,8 @@
   ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
   do
     -- impl-start
-    let r ← if autoCreated then
-        holdsAnyTargetPerm userHasPerm [Perm.change]
-      else
-        pure superResult
-    return r
+    -- BUG: ignore autoCreated; always return inherited decision.
+    return superResult
     -- impl-end
 
 prove_correct deleteRelationAllowed by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-permission test on the related model and the
--  inherited fallback decision are taken as FREE INPUTS — `userHasPerm` and
--  `superResult` — so the spec makes no behavioural claim about them and holds
--  for every value. Nothing to check against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The two permissions whose codenames are ever interrogated on the related
   model: the right to VIEW it and the right to CHANGE it. -/
inductive Perm where
  | view
  | change
  deriving DecidableEq, Inhabited

/- "Does the principal hold ANY of the listed permissions (on the related
   model)?" — the disjunction of the per-permission test over the list. Written
   front-recursively so a single unfold is available per loop step (the backward
   fold pattern, plan §5.4). Empty list ⇒ no permission ⇒ `false`. -/
def anyPerm (userHasPerm : Perm → Bool) : List Perm → Bool
  | []      => false
  | p :: ps => userHasPerm p || anyPerm userHasPerm ps

@[grind] lemma anyPerm_nil (f : Perm → Bool) : anyPerm f [] = false := rfl
@[grind] lemma anyPerm_cons (f : Perm → Bool) (p : Perm) (ps : List Perm) :
    anyPerm f (p :: ps) = (f p || anyPerm f ps) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The disjunctive permission probe: returns whether the principal holds at
   least one of the requested permissions on the related model. It folds the
   per-permission test `userHasPerm` over the requested list. `userHasPerm` and
   `perms` are read-only (not `mut`); the probe mutates nothing it is handed
   (directive 5). -/
method holdsAnyTargetPerm (userHasPerm : Perm → Bool) (perms : List Perm) return (result : Bool)
  ensures result = anyPerm userHasPerm perms
  do
    -- impl-start
    let mut acc : Bool := false
    let mut i := perms.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ perms.length
      invariant acc = anyPerm userHasPerm (perms.drop i)
      done_with i = 0
      decreasing i
    do
      let p := perms[i - 1]!
      acc := userHasPerm p || acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyPerm` peels one disjunct. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma anyPerm_drop_step (f : Perm → Bool) (perms : List Perm) (i : Nat)
    (hi : 0 < i) (hle : i ≤ perms.length) :
    anyPerm f (perms.drop (i - 1)) = (f perms[i - 1]! || anyPerm f (perms.drop i)) := by
  have hlt : i - 1 < perms.length := by omega
  have hcons : perms.drop (i - 1) = perms[i - 1]! :: perms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyPerm_cons]

prove_correct holdsAnyTargetPerm by
  loom_solve
  rw [anyPerm_drop_step userHasPerm perms i (by omega) (by omega)]
  simp_all

/- Authority to ADD a row of the link relation. An implicitly-created link
   relation carries no permissions of its own, so for it authority is derived
   from the related model: the principal may add only if it holds the CHANGE
   permission there. For any other relation the ordinary inherited decision
   (`superResult`) stands. `autoCreated`, `userHasPerm`, `superResult` are
   read-only (directive 5). -/
method addRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct addRelationAllowed by
  loom_solve

/- Authority to CHANGE a row of the link relation. Same derivation as
   `addRelationAllowed`: for an implicitly-created link relation it requires the
   CHANGE permission on the related model; otherwise the inherited decision. -/
method changeRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct changeRelationAllowed by
  loom_solve

/- Authority to DELETE a row of the link relation. Same derivation: for an
   implicitly-created link relation it requires the CHANGE permission on the
   related model; otherwise the inherited decision. -/
method deleteRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct deleteRelationAllowed by
  loom_solve

/- Authority to VIEW a row of the link relation. For an implicitly-created link
   relation the principal may view it if it holds EITHER the VIEW or the CHANGE
   permission on the related model (holding CHANGE implies viewing is allowed);
   otherwise the inherited decision. -/
method viewRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.view, Perm.change] else superResult)
  do
    -- impl-start
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct viewRelationAllowed by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Positive control (unmodified Solution.lean) verifies: lean_verify.sh exit 0. All 8 attacks confirmed same_spec=True (swebench_unified.markers.same_spec, velvet). Verifications run concurrently in 2 batches of 4 background jobs.

SPEC SHAPE: the five postconditions pin EXACT functional equality on free inputs — holdsAnyTargetPerm ensures `result = anyPerm userHasPerm perms`; each gate ensures `= (if autoCreated then anyPerm userHasPerm <list> else superResult)` with the add/change/delete gates using [Perm.change] and the view gate [Perm.view, Perm.change]. These ensures clauses live OUTSIDE the impl region (frozen, shared byte-identical by both twins). Therefore any verifying impl must compute the identical boolean decision as the gold on every input assignment — verify ⇒ behavioural equality with the gold, up to the R type-refinements in mapping.md §2.

### ATTACKS (path | cmd `bash scripts/lean_verify.sh <path>` | result):
- atk_1.lean  (prepatch bug: add gate delegates to [view,change] probe)          -> EXIT=1 REJECTED. Unsolved goal: `ensures_1: x = anyPerm userHasPerm [Perm.view,Perm.change] ⊢ x = if autoCreated then anyPerm userHasPerm [Perm.change] else superResult`. Reproduces the prepatch bug and is correctly refused by the frozen spec (matches Solution_prepatch.lean's documented G-DIFF).
- atk_2.lean  (ECHO: holdsAnyTargetPerm = `perms.any userHasPerm`, proof by induction)  -> EXIT=0 VERIFIES. Behaviourally identical to gold.
- atk_3.lean  (ECHO: addRelationAllowed inlines the specified disjunction directly)     -> EXIT=0 VERIFIES. Behaviourally identical to gold.
- atk_4.lean  (partial-domain bug: probe returns only userHasPerm perms[0]!)           -> EXIT=1 REJECTED. Unsolved goal `userHasPerm perms[0]! = anyPerm userHasPerm perms` (wrong for len>=2).
- atk_5.lean  (boundary/off-by-one: counter starts at length-1, last elt skipped)     -> EXIT=1 REJECTED. Unsolved goal `false = anyPerm userHasPerm (drop (length-1) perms)`.
- atk_6.lean  (control-flow-effect bug: view gate demands [change] only)              -> EXIT=1 REJECTED. Unsolved goal `x = anyPerm userHasPerm [change] ⊢ x = if autoCreated then anyPerm userHasPerm [view,change] else superResult`.
- atk_7.lean  (ungrounded-oracle echo: probe returns `anyPerm userHasPerm perms`)      -> EXIT=0 VERIFIES. Behaviourally identical to gold.
- atk_8.lean  (constant/boolean bug: add/change/delete gates always return superResult) -> EXIT=1 REJECTED. Unsolved goal `superResult = if autoCreated then anyPerm userHasPerm [change] else superResult`.

Summary: 6/8 genuine wrong impls (partial-domain, boundary, control-flow-effect, constant, prepatch, view-gate) are REJECTED with exactly the right unsolved-clause. The only impls that verify (atk_2, atk_3, atk_7) are behaviourally-IDENTICAL echoes of the gold decision — the exact-equality postconditions force this.

RESOLVE STEP (mandatory for every verifying attack): the three verifying echoes produce the identical decision to the gold on every input, so each one's faithful refined patch (mapping.md §2 R-refinement) is the gold options.py edit. Materialized as faithful_patch.diff (byte-identical to bundle patch.diff) and executed through the official harness:
  PY -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-11149", patch, timeout=1800, retries=1)'
  OBSERVED: RESOLVED=True, COMPLETED=True, note="resolved" (bench swe_bench_verified, supports_docker_oracle=True, dataset SWE-bench_Verified). The same faithful patch is submitted under each of atk_2/atk_3/atk_7. Every verifying attack's faithful patch RESOLVES — no verify⇏correct witness found.

REFINEMENT AUDIT (refinement.md): all legs are R or I with no kind-3. A-block A1/A2 = R (composite per-codename test ↔ `Perm→Bool`; codename-list ↔ `List Perm`), A3 = I (`anyPerm` is the `any(...)` disjunction, modeled deeply). B-block B1 = R+I (autoCreated bool + super()->superResult free input), B2/B3 = I (gates call the modeled helper with [change] / [view,change]). §D and mapping.md §3 correctly justify axioms:[] / deep_model_references:[] — the only callees (has_perm, get_permission_codename, target-model field walk, super().has_*) are UNCHANGED by the patch and abstracted as universally-quantified free inputs (userHasPerm, superResult, autoCreated) with no relied-on property, so G-AX genuinely skips (verified against the gold hunks — the field walk/has_perm are relocated-verbatim, not changed). The changed operation (which permissions the auto-created branch demands) is modeled DEEPLY via explicit [Perm.change] vs [Perm.view,Perm.change] lists, not hidden behind an axiom. Model↔patch correspondence holds.

VERDICT: SOUND. ≥5 distinct wrong-impl attacks (6 genuine bugs across partial-domain/boundary/control-flow/constant/prepatch/view-gate classes) all rejected; the only verifying impls are gold-equivalent echoes whose materialized faithful patch was RUN through the official harness and RESOLVED. No verifying wrong impl whose faithful patch fails to resolve exists — verify ⇒ correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.lean`, `atk_3.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-permission test on the related model and the
--  inherited fallback decision are taken as FREE INPUTS — `userHasPerm` and
--  `superResult` — so the spec makes no behavioural claim about them and holds
--  for every value. Nothing to check against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The two permissions whose codenames are ever interrogated on the related
   model: the right to VIEW it and the right to CHANGE it. -/
inductive Perm where
  | view
  | change
  deriving DecidableEq, Inhabited

/- "Does the principal hold ANY of the listed permissions (on the related
   model)?" — the disjunction of the per-permission test over the list. Written
   front-recursively so a single unfold is available per loop step (the backward
   fold pattern, plan §5.4). Empty list ⇒ no permission ⇒ `false`. -/
def anyPerm (userHasPerm : Perm → Bool) : List Perm → Bool
  | []      => false
  | p :: ps => userHasPerm p || anyPerm userHasPerm ps

@[grind] lemma anyPerm_nil (f : Perm → Bool) : anyPerm f [] = false := rfl
@[grind] lemma anyPerm_cons (f : Perm → Bool) (p : Perm) (ps : List Perm) :
    anyPerm f (p :: ps) = (f p || anyPerm f ps) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The disjunctive permission probe: returns whether the principal holds at
   least one of the requested permissions on the related model. It folds the
   per-permission test `userHasPerm` over the requested list. `userHasPerm` and
   `perms` are read-only (not `mut`); the probe mutates nothing it is handed
   (directive 5). -/
method holdsAnyTargetPerm (userHasPerm : Perm → Bool) (perms : List Perm) return (result : Bool)
  ensures result = anyPerm userHasPerm perms
  do
    -- impl-start
    let mut acc : Bool := false
    let mut i := perms.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ perms.length
      invariant acc = anyPerm userHasPerm (perms.drop i)
      done_with i = 0
      decreasing i
    do
      let p := perms[i - 1]!
      acc := userHasPerm p || acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyPerm` peels one disjunct. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma anyPerm_drop_step (f : Perm → Bool) (perms : List Perm) (i : Nat)
    (hi : 0 < i) (hle : i ≤ perms.length) :
    anyPerm f (perms.drop (i - 1)) = (f perms[i - 1]! || anyPerm f (perms.drop i)) := by
  have hlt : i - 1 < perms.length := by omega
  have hcons : perms.drop (i - 1) = perms[i - 1]! :: perms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyPerm_cons]

prove_correct holdsAnyTargetPerm by
  loom_solve
  rw [anyPerm_drop_step userHasPerm perms i (by omega) (by omega)]
  simp_all

/- Authority to ADD a row of the link relation. An implicitly-created link
   relation carries no permissions of its own, so for it authority is derived
   from the related model: the principal may add only if it holds the CHANGE
   permission there. For any other relation the ordinary inherited decision
   (`superResult`) stands. `autoCreated`, `userHasPerm`, `superResult` are
   read-only (directive 5). -/
method addRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct addRelationAllowed by
  loom_solve

/- Authority to CHANGE a row of the link relation. Same derivation as
   `addRelationAllowed`: for an implicitly-created link relation it requires the
   CHANGE permission on the related model; otherwise the inherited decision. -/
method changeRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct changeRelationAllowed by
  loom_solve

/- Authority to DELETE a row of the link relation. Same derivation: for an
   implicitly-created link relation it requires the CHANGE permission on the
   related model; otherwise the inherited decision. -/
method deleteRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult)
  do
    -- impl-start
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct deleteRelationAllowed by
  loom_solve

/- Authority to VIEW a row of the link relation. For an implicitly-created link
   relation the principal may view it if it holds EITHER the VIEW or the CHANGE
   permission on the related model (holding CHANGE implies viewing is allowed);
   otherwise the inherited decision. -/
method viewRelationAllowed (autoCreated : Bool) (userHasPerm : Perm → Bool) (superResult : Bool) return (result : Bool)
  ensures result = (if autoCreated then anyPerm userHasPerm [Perm.view, Perm.change] else superResult)
  do
    -- impl-start
    let r ← if autoCreated then
        holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]
      else
        pure superResult
    return r
    -- impl-end

prove_correct viewRelationAllowed by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Positive control (unmodified Solution.lean) verifies: lean_verify.sh exit 0. All 8 attacks confirmed same_spec=True (swebench_unified.markers.same_spec, velvet). Verifications run concurrently in 2 batches of 4 background jobs.

SPEC SHAPE: the five postconditions pin EXACT functional equality on free inputs — holdsAnyTargetPerm ensures `result = anyPerm userHasPerm perms`; each gate ensures `= (if autoCreated then anyPerm userHasPerm <list> else superResult)` with the add/change/delete gates using [Perm.change] and the view gate [Perm.view, Perm.change]. These ensures clauses live OUTSIDE the impl region (frozen, shared byte-identical by both twins). Therefore any verifying impl must compute the identical boolean decision as the gold on every input assignment — verify ⇒ behavioural equality with the gold, up to the R type-refinements in mapping.md §2.

### ATTACKS (path | cmd `bash scripts/lean_verify.sh <path>` | result):
- atk_1.lean  (prepatch bug: add gate delegates to [view,change] probe)          -> EXIT=1 REJECTED. Unsolved goal: `ensures_1: x = anyPerm userHasPerm [Perm.view,Perm.change] ⊢ x = if autoCreated then anyPerm userHasPerm [Perm.change] else superResult`. Reproduces the prepatch bug and is correctly refused by the frozen spec (matches Solution_prepatch.lean's documented G-DIFF).
- atk_2.lean  (ECHO: holdsAnyTargetPerm = `perms.any userHasPerm`, proof by induction)  -> EXIT=0 VERIFIES. Behaviourally identical to gold.
- atk_3.lean  (ECHO: addRelationAllowed inlines the specified disjunction directly)     -> EXIT=0 VERIFIES. Behaviourally identical to gold.
- atk_4.lean  (partial-domain bug: probe returns only userHasPerm perms[0]!)           -> EXIT=1 REJECTED. Unsolved goal `userHasPerm perms[0]! = anyPerm userHasPerm perms` (wrong for len>=2).
- atk_5.lean  (boundary/off-by-one: counter starts at length-1, last elt skipped)     -> EXIT=1 REJECTED. Unsolved goal `false = anyPerm userHasPerm (drop (length-1) perms)`.
- atk_6.lean  (control-flow-effect bug: view gate demands [change] only)              -> EXIT=1 REJECTED. Unsolved goal `x = anyPerm userHasPerm [change] ⊢ x = if autoCreated then anyPerm userHasPerm [view,change] else superResult`.
- atk_7.lean  (ungrounded-oracle echo: probe returns `anyPerm userHasPerm perms`)      -> EXIT=0 VERIFIES. Behaviourally identical to gold.
- atk_8.lean  (constant/boolean bug: add/change/delete gates always return superResult) -> EXIT=1 REJECTED. Unsolved goal `superResult = if autoCreated then anyPerm userHasPerm [change] else superResult`.

Summary: 6/8 genuine wrong impls (partial-domain, boundary, control-flow-effect, constant, prepatch, view-gate) are REJECTED with exactly the right unsolved-clause. The only impls that verify (atk_2, atk_3, atk_7) are behaviourally-IDENTICAL echoes of the gold decision — the exact-equality postconditions force this.

RESOLVE STEP (mandatory for every verifying attack): the three verifying echoes produce the identical decision to the gold on every input, so each one's faithful refined patch (mapping.md §2 R-refinement) is the gold options.py edit. Materialized as faithful_patch.diff (byte-identical to bundle patch.diff) and executed through the official harness:
  PY -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-11149", patch, timeout=1800, retries=1)'
  OBSERVED: RESOLVED=True, COMPLETED=True, note="resolved" (bench swe_bench_verified, supports_docker_oracle=True, dataset SWE-bench_Verified). The same faithful patch is submitted under each of atk_2/atk_3/atk_7. Every verifying attack's faithful patch RESOLVES — no verify⇏correct witness found.

REFINEMENT AUDIT (refinement.md): all legs are R or I with no kind-3. A-block A1/A2 = R (composite per-codename test ↔ `Perm→Bool`; codename-list ↔ `List Perm`), A3 = I (`anyPerm` is the `any(...)` disjunction, modeled deeply). B-block B1 = R+I (autoCreated bool + super()->superResult free input), B2/B3 = I (gates call the modeled helper with [change] / [view,change]). §D and mapping.md §3 correctly justify axioms:[] / deep_model_references:[] — the only callees (has_perm, get_permission_codename, target-model field walk, super().has_*) are UNCHANGED by the patch and abstracted as universally-quantified free inputs (userHasPerm, superResult, autoCreated) with no relied-on property, so G-AX genuinely skips (verified against the gold hunks — the field walk/has_perm are relocated-verbatim, not changed). The changed operation (which permissions the auto-created branch demands) is modeled DEEPLY via explicit [Perm.change] vs [Perm.view,Perm.change] lists, not hidden behind an axiom. Model↔patch correspondence holds.

VERDICT: SOUND. ≥5 distinct wrong-impl attacks (6 genuine bugs across partial-domain/boundary/control-flow/constant/prepatch/view-gate classes) all rejected; the only verifying impls are gold-equivalent echoes whose materialized faithful patch was RUN through the official harness and RESOLVED. No verifying wrong impl whose faithful patch fails to resolve exists — verify ⇒ correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-11149 (velvet).

### Setup verified
- same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True (spec region byte-identical).
- Solution.lean elaborates clean (lean_verify exit 0). Solution_prepatch.lean fails (exit 1) at the three add/change/delete gates on exactly `x = anyPerm userHasPerm [Perm.view,Perm.change] ⊢ x = anyPerm userHasPerm [Perm.change]`, view gate verifying — matches the claimed G-DIFF.
- Base commit e245046 confirmed present; base-commit options.py shows all four auto_created branches returning the VIEW-or-CHANGE probe (via has_view_permission). Gold patch splits add/change/delete to CHANGE-only and keeps view at VIEW-or-CHANGE via the new _has_any_perms_for_target_model helper.

### FAITHFULNESS TO REAL REPO (patched InlineModelAdmin.has_*_permission):
- add/change/delete spec = (if autoCreated then anyPerm userHasPerm [Perm.change] else superResult). anyPerm f [change] = f change ≡ any(user.has_perm(...) for perm in ['change']). Exact match to patched methods.
- view spec = (if autoCreated then anyPerm userHasPerm [Perm.view,Perm.change] else superResult) = userHasPerm view || userHasPerm change ≡ any(... for perm in ['view','change']). Exact match.
- All unchanged callees (has_perm, get_permission_codename, app_label formatting, the target-model field-walk) are abstracted into the free input userHasPerm : Perm → Bool; the non-auto branch into free superResult. Spec is universally quantified over these, so it asserts nothing false about any concrete callee behavior and cannot over-constrain them. For EVERY assignment of (auto_created, user's view/change perms, super result) the modeled decision equals the real patched decision.
- G-CONF (seed 11149) differential-tests shadow vs patched-source oracle over the exhaustive 2^4 cube × 4 gates + 100k fuzz: 0 disagreements.
- Total-correctness strengthening is faithful: the real helper is a bounded any(...) over a 1-2 element finite list, so it always terminates; demanding termination does not exceed real repo behavior.

No input exists where the modeled functions disagree with the real repo. Spec is neither too strong nor drifting. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged on the computed velvet spec view of Solution.lean (impl + prove_correct bodies elided). Mechanical leakage.screen passes with zero hard failures: no diff markers, no patched file path (django/contrib/admin/options.py) or dotted module, no gold-patch line reproduced, no patched repo symbol embedded in or named by spec-view identifiers/comments. Patch changed symbols are get_queryset and has_any_perms_for_target_model; the spec uses the abstract name holdsAnyTargetPerm (not the repo helper _has_any_perms_for_target_model), and the target-model field-walk is abstracted into the free input userHasPerm — neither surfaces. same_spec(Solution.lean, Solution_prepatch.lean)=True, so the discriminating clause (add/change/delete gates use [Perm.change], view uses [Perm.view, Perm.change]) is part of the frozen spec shared byte-identical by both twins. Semantically this is the spec encoding the CORRECT target behavior, which is exactly what the public problem_statement already discloses: a view-only user must be denied add/remove on an auto-created ManyToManyField inline. The required-permission discriminator is thus derivable from problem_statement and not leaked beyond it. Spec-view comments describe correct behavior abstractly ('may add only if it holds the CHANGE permission'); none narrate the bug, the prepatch state, or the edit. Bug/prepatch narration lives only in refinement.md §C, which is auditor documentation, not the consumer spec view. meta records G-LEAK=pass and no RELAXED_LEAKAGE.md / relaxed_leakage flag, so no relaxation deferral applies.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
