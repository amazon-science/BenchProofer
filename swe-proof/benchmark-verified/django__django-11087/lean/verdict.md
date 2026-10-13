# P2 adversarial audit — django__django-11087

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 admissible attacks re-run of 9 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,8 +109,6 @@
     (allFields defaultColumns skippedNames : List String)
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
-  if !(guardA || guardB) then
-    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
   return loaded
 -- impl-end
 
@@ -130,4 +128,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,8 @@
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
   if !(guardA || guardB) then
-    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
+    if skippedNames.isEmpty then
+      loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
   return loaded
 -- impl-end
 
@@ -130,4 +131,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
   if !(guardA || guardB) then
-    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
+    loaded := (pkColumn :: restrictionNames skippedNames candidateRelations).dedup
   return loaded
 -- impl-end
 
@@ -130,4 +130,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
   if !(guardA || guardB) then
-    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
+    loaded := referencedColumns candidateRelations
   return loaded
 -- impl-end
 
@@ -130,4 +130,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,8 +109,11 @@
     (allFields defaultColumns skippedNames : List String)
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
-  if !(guardA || guardB) then
-    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
+  if guardA then
+    return loaded
+  loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
+  if guardB then
+    loaded := allFields
   return loaded
 -- impl-end
 
@@ -130,4 +133,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,9 @@
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
   if !(guardA || guardB) then
-    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
+    let named := restrictionNames skippedNames candidateRelations
+    loaded := if named.isEmpty then allFields
+              else ((defaultColumns.headD pkColumn) :: named).dedup
   return loaded
 -- impl-end
 
@@ -130,4 +132,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,9 @@
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
   if !(guardA || guardB) then
-    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
+    let named := restrictionNames skippedNames candidateRelations
+    loaded := if named.isEmpty then allFields
+              else (pkColumn :: referencedColumns candidateRelations).dedup
   return loaded
 -- impl-end
 
@@ -130,4 +132,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,10 @@
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
   if !(guardA || guardB) then
-    loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
+    let named := restrictionNames skippedNames candidateRelations
+    loaded := if named.isEmpty then allFields
+              else if skippedNames.contains pkColumn then named
+              else (pkColumn :: named).dedup
   return loaded
 -- impl-end
 
@@ -130,4 +133,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,7 +109,7 @@
     (allFields defaultColumns skippedNames : List String)
     (candidateRelations : List (List String)) : List String := Id.run do
   let mut loaded := defaultColumns
-  if !(guardA || guardB) then
+  if !(guardA && guardB) then
     loaded := loadedColumns pkColumn allFields skippedNames candidateRelations
   return loaded
 -- impl-end
@@ -130,4 +130,16 @@
     first
       | rfl
       | (exfalso; revert h; decide)
+      | simp
+      | simp_all
+      | simp_all [loadedColumns, restrictionNames, referencedColumns]
+      | (simp only [loadedColumns, restrictionNames, referencedColumns]
+         split <;> simp_all)
+      | (split <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | (unfold loadedColumns restrictionNames referencedColumns
+         split <;> simp_all)
+      | aesop
+      | (cases skippedNames <;> simp_all [loadedColumns, restrictionNames, referencedColumns])
+      | decide
+      | trivial
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing which columns to load when fetching the related objects that a cascade
deletion must visit.

While walking the graph of objects reachable from the ones being deleted, the
collector fetches, for each relation, the set of related objects that point at
the current batch. Only some columns of those related objects are ever needed:
the columns that other relations point at (their identity / target columns).
Loading the remaining columns is pure overhead and can even surface values the
caller never asked for.

The fetch that reaches this decision is described by:

  * `pkColumn` — the name of the related model's identifying column;
  * `allFields` — every column name of the related model (the whole row);
  * `defaultColumns` — the column names that fetch loads when it is handed on
    exactly as it arrived;
  * `skippedNames` — the names that fetch has already been told to leave out
    (empty when it has been told nothing);
  * `candidateRelations` — for each relation that may itself cascade from the
    related model, the list of target column names that relation points at;
  * `guardA`, `guardB` — two conditions of the fetch under which no restriction
    is applied to it at all. What makes either of them hold is not part of this
    decision: they arrive as flags.

When neither condition holds, the fetch is restricted to the referenced columns:
the target column names gathered across all candidate relations, with duplicates
removed. A restriction cannot ask for a name the fetch has already been told to
leave out, so those names are dropped from the request; and restricting a fetch
this way cannot drop the identifying column — an object still has to be
identified to be deleted — so the restricted load carries `pkColumn` as well,
even when the fetch had been told to leave that column out. A restriction
replaces whatever the fetch had been told rather than adding to it: if the
request is left naming no column at all there is nothing to restrict the fetch
to, and the whole row is loaded.

When either condition holds the fetch is handed on untouched and loads exactly
the columns it loaded by default.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two guard
-- flags, the identifying column name and the column-name lists enter as plain
-- data; the only operations are the gathering of the referenced column names,
-- modeled directly as list flattening followed by duplicate removal, the
-- dropping of the names the fetch has been told to leave out, modeled directly
-- as a filter, and the restriction of a fetch to a set of columns, modeled
-- directly by the column set such a restricted fetch is guaranteed to load.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The referenced column names: the target column names gathered across every
candidate relation, flattened into a single list and deduplicated (the set of
columns that some relation points at). -/
def referencedColumns (candidateRelations : List (List String)) : List String :=
  candidateRelations.flatten.dedup

/-- The column names a restriction of this fetch ends up naming: the referenced
columns, minus every name the fetch has already been told to leave out — a
restriction cannot ask for one of those. -/
def restrictionNames (skippedNames : List String)
    (candidateRelations : List (List String)) : List String :=
  (referencedColumns candidateRelations).filter (fun c => !skippedNames.contains c)

/-- The columns a fetch restricted to the referenced columns actually loads.

Restricting a fetch to a named set of columns is only meaningful when the
restriction names a column: with none named there is nothing to restrict to and
the fetch is left alone, loading the whole row (`allFields`) — the restriction
replaces what the fetch had been told, so the names it had been told to leave
out come back. When the restriction does name a column the restricted fetch
loads exactly those columns together with the identifying column `pkColumn`,
which such a restriction always retains. -/
def loadedColumns (pkColumn : String) (allFields skippedNames : List String)
    (candidateRelations : List (List String)) : List String :=
  let named := restrictionNames skippedNames candidateRelations
  if named.isEmpty then allFields else (pkColumn :: named).dedup
-- pure-end

-- post-conditions-start
/-- The set of columns to load is fully pinned to the inputs:

  * when neither condition holds, the load is exactly what a fetch restricted to
    the referenced columns loads — the referenced columns the fetch has not been
    told to leave out, plus the identifying column, or the whole row when the
    restriction is left naming nothing;
  * otherwise the fetch is handed on exactly as it arrived and the load is
    exactly `defaultColumns`.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_collectFieldSelection
    (guardA guardB : Bool) (pkColumn : String)
    (allFields defaultColumns skippedNames : List String)
    (candidateRelations : List (List String)) (result : List String) : Prop :=
  (guardA = false ∧ guardB = false →
      result = loadedColumns pkColumn allFields skippedNames candidateRelations) ∧
  (¬ (guardA = false ∧ guardB = false) →
      result = defaultColumns)
-- post-conditions-end

-- impl-start
def implementation_collectFieldSelection
    (guardA guardB : Bool) (pkColumn : String)
    (allFields defaultColumns skippedNames : List String)
    (candidateRelations : List (List String)) : List String :=
  match guardA, guardB with
  | false, false => loadedColumns pkColumn allFields skippedNames candidateRelations
  | true,  _     => defaultColumns
  | _,     true  => defaultColumns
-- impl-end

-- proof-start
theorem correct_collectFieldSelection :
    ∀ (guardA guardB : Bool) (pkColumn : String)
      (allFields defaultColumns skippedNames : List String)
      (candidateRelations : List (List String)),
      problem_spec_collectFieldSelection guardA guardB pkColumn allFields defaultColumns
        skippedNames candidateRelations
        (implementation_collectFieldSelection guardA guardB pkColumn allFields defaultColumns
          skippedNames candidateRelations) := by
  intro guardA guardB pkColumn allFields defaultColumns skippedNames candidateRelations
  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection
  cases guardA <;> cases guardB <;>
    refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    first
      | rfl
      | (exfalso; revert h; decide)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-11087 (lean), 7-binder REPAIRED spec. VERDICT: SOUND. No same-spec wrong impl closed, so protocol step 2 had no mandatory patch; 10 resolve runs were EXECUTED anyway to test the model<->patch correspondence in both directions. NOTE ON PRIOR PASSES: the two SOUND records in verdict.md were produced against the OLDER 5-binder pre-repair spec (no defaultColumns/skippedNames binders). This battery was authored fresh against the current spec; the prior attack list is not reusable, and two of its counterexamples (the pass-through branch modeled as allFields, and the skip reduction used only for the emptiness test) are re-encoded here as atk_5 and atk_7.

**SAME-SPEC:** all 9 attacks + positive control = True via swebench_unified.markers.same_spec (spec regions byte-identical; only impl region + tactic script differ). Admissibility: variant_scope.unsound_evasions returned [] for every file; 0 banned tokens (sorry/admit/sorryAx/native_decide/unsafe/extern), 0 new axiom/opaque declarations, obligation `theorem correct_collectFieldSelection` present and statement-identical in all 10.

VERIFY -- `bash scripts/lean_verify.sh <f>`, run 4-way concurrently as background jobs:
  pos_control.lean exit=0  (structurally unlike frozen: no `Id.run do` accumulator, a `match` on both flags; FROZEN proof body UNCHANGED)
  atk_1..atk_9     exit=1  (all nine rejected)
Every attack was given a proof script STRICTLY STRONGER than the frozen one (frozen alternatives first, then simp/simp_all/split/aesop/decide closers), so no rejection is blamable on a tactic tuned to gold's shape. Each failed on the DISCRIMINATING goal (residues captured in atk_N.log).

REJECTIONS ARE DECIDED REFUTATIONS, NOT TACTIC WEAKNESS. wit.lean re-encodes the frozen spec verbatim and DECIDES `¬ problem_spec ... (i_N ...)` for all 9 attacks at mapping.md §3 carrier states, plus 7 CONTROLS showing the gold impl SATISFIES the spec at those same points: `lean_verify.sh wit.lean` exit=0, no sorry. (`decide` needs problem_spec unfolded first -- it is an opaque `def _ : Prop`.) Two of my first-draft witness POINTS were badly chosen (atk_4 with the pk inside the referenced set; atk_6 with the request emptied so both took the allFields leg) and `decide` reported the negation false; I corrected the points to the to_field shape and the MTI-no-deferral shape rather than re-reading the module rejection as a hole.

### ATTACK INVENTORY (kind -> verify exit -> resolve of the materialized faithful patch):
  atk_1 PREPATCH BUG -- arm never restricts, fetch handed on as fetched (the real `elif sub_objs:`) -> 1 -> resolved=FALSE (F2P test_only_referenced_fields_selected failure, P2P 41/41) [PREPATCH REPRODUCED]
  atk_2 PARTIAL DOMAIN -- restricts only when the fetch carries no deferral state; correct on rows 2/5/9, wrong on 1/3/7/8/11/12/13 -> 1 -> resolved=TRUE
  atk_3 BOUNDARY -- drops the empty-request no-op leg, pk-only load where the whole row is due (rows 1/6/8/13) -> 1 -> resolved=TRUE
  atk_4 UNGROUNDED-ORACLE ECHO -- `.only()` modeled as the identity on its argument; drops the pk retention, the no-op leg AND the request reduction -> 1 -> resolved=TRUE
  atk_5 CONTROL-FLOW EFFECT -- early `continue` out of the arm + a second write on the receivers corner; pass-through predicts the whole row instead of the fetch's own default columns (row 4) -> 1 -> resolved=TRUE
  atk_6 DEEP-MODEL/A-leg -- retains the FIRST DEFAULT COLUMN instead of the identifying column -> 1 -> resolved=TRUE
  atk_7 PRE-REPAIR MODEL DEFECT -- skip reduction consulted ONLY for the emptiness test, request left unreduced (row 11: real {b,id}, this predicts {id,a,b}) -> 1 -> resolved=TRUE
  atk_8 DEEP-MODEL/A-leg -- pk retention cancelled when the fetch already skips the pk, contradicting the UNCONDITIONAL retention (row 12) -> 1 -> resolved=TRUE
  atk_9 guard mis-De-Morganed `!(A && B)`, restricts on 3 of 4 corners -> 1 -> resolved=FALSE (F2P failure + P2P failures test_proxied_model_duplicate_queries, test_relational_post_delete_signals_happen_before_parent_object)
No attack is a CANDIDATE (none verifies), so `patches` is submitted empty; the resolve column above is supplementary evidence, not a step-2 obligation. atk_2..atk_8 resolving while being REJECTED by the spec is the SAFE (too-strict) direction -- a resolving rival is a correct echo of gold, not a weakness.

WHY NO WRONG IMPL CAN CLOSE (structural, machine-checked). uniq.lean proves the postcondition is TOTAL: `spec_unique` (any two results satisfying it at the same inputs are equal) and `any_verifier_equals_gold` (ANY impl satisfying the obligation agrees POINTWISE with the gold impl). exit=0; `#print axioms spec_unique` / `any_verifier_equals_gold` -> both 'does not depend on any axioms'. So the obligation is a functional equation, and the ONLY residual break vector is the pinned function `loadedColumns` itself being unfaithful -- which is exactly the A-leg, audited live below.

**CLEAN AXIOMS:** ax_check.lean = pos_control + `#print axioms` -> exit=0: correct_collectFieldSelection, implementation_collectFieldSelection, loadedColumns, restrictionNames, referencedColumns all 'does not depend on any axioms'. Consistent with meta.json axioms=[] / deep_model_references=[] and the axiom_check.py skip stub.

A-LEG / DEEP-MODEL AUDIT (the assignment's focus). Because verification pins the impl to exactly `loadedColumns`, I measured that function against the LIVE callee at base_commit instead of accepting refinement.md's prose. only_probe.py drives the real `QuerySet.only()` through Django's deferred-loading machinery and reads the loaded column set off `SQLCompiler.pre_sql_setup`, over every referenced-column subset x every prior-defer subset of four model shapes (flat Referrer, custom-pk Custom, and BOTH halves of an MTI pair): 384 comparisons, 0 DISAGREEMENTS.

Corner evidence, all confirmed live: zero-arg `.only()` is a NO-OP loading the whole row; pk RETAINED though unreferenced (`.only(unique_field)` -> {id,unique_field}, the to_field case); pk retained EVEN WHEN DEFERRED (`defer(id)+.only(unique_field)` -> {id,unique_field}, mapping row 12 -- the unconditional retention atk_8 drops); the request reduction is a RAW STRING diff (`defer(origin)+.only(origin_id)` -> {id,origin_id}, row 7); skip COVERING the referenced set yields the whole row (row 13); MTI child pk IS the parent-link attname with `concrete_fields=['id','b','mtibase_ptr_id','c']` -- pk is NOT first, so atk_6's first-default-column model is genuinely wrong and `.only(c)` -> {c,mtibase_ptr_id}; custom pk retained (code). Both non-obvious guarantees the bundle asserts are true of the real callee, and atk_3/atk_6/atk_8 confirm the spec REJECTS impls that drop any of them. The deep model is not an ungrounded oracle echo.

**PATCH MATERIALIZATION VALIDATED:** mkpatch.py builds each faithful patch as the gold structure with only the FIELD-SELECTION ARM swapped, keeping the unmodeled legs (`_has_signal_listeners`, the `can_fast_delete` rewrite) identical to gold so a resolve difference is attributable to the modeled decision alone. My gold reconstruction is CODE-IDENTICAL to the bundle's patch.diff (differs only in comment lines) and resolved=TRUE with F2P 1/1 and P2P 41/41, which validates the method. All 10 runs completed=True; no timeouts, no image failures, no inconclusive run. Worktree at base 8180ffba21 (my own, via `git worktree add`).

**REFINEMENT.MD LEG AUDIT:** 6 legs, tagged R, R, R/I, R, R, I -- every leg is R or I, NO kind-3 leg, no untagged leg, and no leg claiming an axiom the bundle does not have. The 'no A row' claim is CORRECT rather than an evasion: `get_candidate_relations_to_delete` / `foreign_related_fields` legitimately enter as DATA (their observable output IS the candidateRelations input), and the gather itself is modeled deeply as flatten+dedup. Legs 4 and 5 are the load-bearing ones and are correctly tagged R with the `.only()` behaviours cited to sql/query.py:656/660/1971-1980 -- all verified live above. Leg 1's correspondence (accumulator starts at what the incoming fetch loads, NOT allFields) is the repaired pass-through claim and is pinned by atk_5. Prose matches the code I read at base and post-patch.

OBSERVATION (not a defect; too-STRONG direction). The spec is List-valued while the modeled decision is membership-determined (a SQL column choice), so order-only reshapes would be rejected even though their patches resolve. That cannot produce a verify-but-not-resolve witness; mapping.md §5's list<->set bijection and G-CONF's set comparison document the intended reading. Prior notes D5 recorded the same.

**FLOOR:** 9 admissible distinct attacks (>=5 required) spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo and two deep-model/A-leg classes; prepatch bug reproduced (atk_1, exit=1, decided witness, patch resolved=FALSE); structurally different positive control verifies (exit=0, frozen proof untouched). No impl with a closing clean-axiom proof exists, hence no faithful patch could fail to resolve. verify=>correct is NOT broken for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 admissible attacks re-run of 9 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing which columns to load when fetching the related objects that a cascade
deletion must visit.

While walking the graph of objects reachable from the ones being deleted, the
collector fetches, for each relation, the set of related objects that point at
the current batch. Only some columns of those related objects are ever needed:
the columns that other relations point at (their identity / target columns).
Loading the remaining columns is pure overhead and can even surface values the
caller never asked for.

The fetch that reaches this decision is described by:

  * `pkColumn` — the name of the related model's identifying column;
  * `allFields` — every column name of the related model (the whole row);
  * `defaultColumns` — the column names that fetch loads when it is handed on
    exactly as it arrived;
  * `skippedNames` — the names that fetch has already been told to leave out
    (empty when it has been told nothing);
  * `candidateRelations` — for each relation that may itself cascade from the
    related model, the list of target column names that relation points at;
  * `guardA`, `guardB` — two conditions of the fetch under which no restriction
    is applied to it at all. What makes either of them hold is not part of this
    decision: they arrive as flags.

When neither condition holds, the fetch is restricted to the referenced columns:
the target column names gathered across all candidate relations, with duplicates
removed. A restriction cannot ask for a name the fetch has already been told to
leave out, so those names are dropped from the request; and restricting a fetch
this way cannot drop the identifying column — an object still has to be
identified to be deleted — so the restricted load carries `pkColumn` as well,
even when the fetch had been told to leave that column out. A restriction
replaces whatever the fetch had been told rather than adding to it: if the
request is left naming no column at all there is nothing to restrict the fetch
to, and the whole row is loaded.

When either condition holds the fetch is handed on untouched and loads exactly
the columns it loaded by default.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two guard
-- flags, the identifying column name and the column-name lists enter as plain
-- data; the only operations are the gathering of the referenced column names,
-- modeled directly as list flattening followed by duplicate removal, the
-- dropping of the names the fetch has been told to leave out, modeled directly
-- as a filter, and the restriction of a fetch to a set of columns, modeled
-- directly by the column set such a restricted fetch is guaranteed to load.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The referenced column names: the target column names gathered across every
candidate relation, flattened into a single list and deduplicated (the set of
columns that some relation points at). -/
def referencedColumns (candidateRelations : List (List String)) : List String :=
  candidateRelations.flatten.dedup

/-- The column names a restriction of this fetch ends up naming: the referenced
columns, minus every name the fetch has already been told to leave out — a
restriction cannot ask for one of those. -/
def restrictionNames (skippedNames : List String)
    (candidateRelations : List (List String)) : List String :=
  (referencedColumns candidateRelations).filter (fun c => !skippedNames.contains c)

/-- The columns a fetch restricted to the referenced columns actually loads.

Restricting a fetch to a named set of columns is only meaningful when the
restriction names a column: with none named there is nothing to restrict to and
the fetch is left alone, loading the whole row (`allFields`) — the restriction
replaces what the fetch had been told, so the names it had been told to leave
out come back. When the restriction does name a column the restricted fetch
loads exactly those columns together with the identifying column `pkColumn`,
which such a restriction always retains. -/
def loadedColumns (pkColumn : String) (allFields skippedNames : List String)
    (candidateRelations : List (List String)) : List String :=
  let named := restrictionNames skippedNames candidateRelations
  if named.isEmpty then allFields else (pkColumn :: named).dedup
-- pure-end

-- post-conditions-start
/-- The set of columns to load is fully pinned to the inputs:

  * when neither condition holds, the load is exactly what a fetch restricted to
    the referenced columns loads — the referenced columns the fetch has not been
    told to leave out, plus the identifying column, or the whole row when the
    restriction is left naming nothing;
  * otherwise the fetch is handed on exactly as it arrived and the load is
    exactly `defaultColumns`.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_collectFieldSelection
    (guardA guardB : Bool) (pkColumn : String)
    (allFields defaultColumns skippedNames : List String)
    (candidateRelations : List (List String)) (result : List String) : Prop :=
  (guardA = false ∧ guardB = false →
      result = loadedColumns pkColumn allFields skippedNames candidateRelations) ∧
  (¬ (guardA = false ∧ guardB = false) →
      result = defaultColumns)
-- post-conditions-end

-- impl-start
def implementation_collectFieldSelection
    (guardA guardB : Bool) (pkColumn : String)
    (allFields defaultColumns skippedNames : List String)
    (candidateRelations : List (List String)) : List String :=
  match guardA, guardB with
  | false, false => loadedColumns pkColumn allFields skippedNames candidateRelations
  | true,  _     => defaultColumns
  | _,     true  => defaultColumns
-- impl-end

-- proof-start
theorem correct_collectFieldSelection :
    ∀ (guardA guardB : Bool) (pkColumn : String)
      (allFields defaultColumns skippedNames : List String)
      (candidateRelations : List (List String)),
      problem_spec_collectFieldSelection guardA guardB pkColumn allFields defaultColumns
        skippedNames candidateRelations
        (implementation_collectFieldSelection guardA guardB pkColumn allFields defaultColumns
          skippedNames candidateRelations) := by
  intro guardA guardB pkColumn allFields defaultColumns skippedNames candidateRelations
  unfold problem_spec_collectFieldSelection implementation_collectFieldSelection
  cases guardA <;> cases guardB <;>
    refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    first
      | rfl
      | (exfalso; revert h; decide)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-11087 (lean), 7-binder REPAIRED spec. VERDICT: SOUND. No same-spec wrong impl closed, so protocol step 2 had no mandatory patch; 10 resolve runs were EXECUTED anyway to test the model<->patch correspondence in both directions. NOTE ON PRIOR PASSES: the two SOUND records in verdict.md were produced against the OLDER 5-binder pre-repair spec (no defaultColumns/skippedNames binders). This battery was authored fresh against the current spec; the prior attack list is not reusable, and two of its counterexamples (the pass-through branch modeled as allFields, and the skip reduction used only for the emptiness test) are re-encoded here as atk_5 and atk_7.

**SAME-SPEC:** all 9 attacks + positive control = True via swebench_unified.markers.same_spec (spec regions byte-identical; only impl region + tactic script differ). Admissibility: variant_scope.unsound_evasions returned [] for every file; 0 banned tokens (sorry/admit/sorryAx/native_decide/unsafe/extern), 0 new axiom/opaque declarations, obligation `theorem correct_collectFieldSelection` present and statement-identical in all 10.

VERIFY -- `bash scripts/lean_verify.sh <f>`, run 4-way concurrently as background jobs:
  pos_control.lean exit=0  (structurally unlike frozen: no `Id.run do` accumulator, a `match` on both flags; FROZEN proof body UNCHANGED)
  atk_1..atk_9     exit=1  (all nine rejected)
Every attack was given a proof script STRICTLY STRONGER than the frozen one (frozen alternatives first, then simp/simp_all/split/aesop/decide closers), so no rejection is blamable on a tactic tuned to gold's shape. Each failed on the DISCRIMINATING goal (residues captured in atk_N.log).

REJECTIONS ARE DECIDED REFUTATIONS, NOT TACTIC WEAKNESS. wit.lean re-encodes the frozen spec verbatim and DECIDES `¬ problem_spec ... (i_N ...)` for all 9 attacks at mapping.md §3 carrier states, plus 7 CONTROLS showing the gold impl SATISFIES the spec at those same points: `lean_verify.sh wit.lean` exit=0, no sorry. (`decide` needs problem_spec unfolded first -- it is an opaque `def _ : Prop`.) Two of my first-draft witness POINTS were badly chosen (atk_4 with the pk inside the referenced set; atk_6 with the request emptied so both took the allFields leg) and `decide` reported the negation false; I corrected the points to the to_field shape and the MTI-no-deferral shape rather than re-reading the module rejection as a hole.

### ATTACK INVENTORY (kind -> verify exit -> resolve of the materialized faithful patch):
  atk_1 PREPATCH BUG -- arm never restricts, fetch handed on as fetched (the real `elif sub_objs:`) -> 1 -> resolved=FALSE (F2P test_only_referenced_fields_selected failure, P2P 41/41) [PREPATCH REPRODUCED]
  atk_2 PARTIAL DOMAIN -- restricts only when the fetch carries no deferral state; correct on rows 2/5/9, wrong on 1/3/7/8/11/12/13 -> 1 -> resolved=TRUE
  atk_3 BOUNDARY -- drops the empty-request no-op leg, pk-only load where the whole row is due (rows 1/6/8/13) -> 1 -> resolved=TRUE
  atk_4 UNGROUNDED-ORACLE ECHO -- `.only()` modeled as the identity on its argument; drops the pk retention, the no-op leg AND the request reduction -> 1 -> resolved=TRUE
  atk_5 CONTROL-FLOW EFFECT -- early `continue` out of the arm + a second write on the receivers corner; pass-through predicts the whole row instead of the fetch's own default columns (row 4) -> 1 -> resolved=TRUE
  atk_6 DEEP-MODEL/A-leg -- retains the FIRST DEFAULT COLUMN instead of the identifying column -> 1 -> resolved=TRUE
  atk_7 PRE-REPAIR MODEL DEFECT -- skip reduction consulted ONLY for the emptiness test, request left unreduced (row 11: real {b,id}, this predicts {id,a,b}) -> 1 -> resolved=TRUE
  atk_8 DEEP-MODEL/A-leg -- pk retention cancelled when the fetch already skips the pk, contradicting the UNCONDITIONAL retention (row 12) -> 1 -> resolved=TRUE
  atk_9 guard mis-De-Morganed `!(A && B)`, restricts on 3 of 4 corners -> 1 -> resolved=FALSE (F2P failure + P2P failures test_proxied_model_duplicate_queries, test_relational_post_delete_signals_happen_before_parent_object)
No attack is a CANDIDATE (none verifies), so `patches` is submitted empty; the resolve column above is supplementary evidence, not a step-2 obligation. atk_2..atk_8 resolving while being REJECTED by the spec is the SAFE (too-strict) direction -- a resolving rival is a correct echo of gold, not a weakness.

WHY NO WRONG IMPL CAN CLOSE (structural, machine-checked). uniq.lean proves the postcondition is TOTAL: `spec_unique` (any two results satisfying it at the same inputs are equal) and `any_verifier_equals_gold` (ANY impl satisfying the obligation agrees POINTWISE with the gold impl). exit=0; `#print axioms spec_unique` / `any_verifier_equals_gold` -> both 'does not depend on any axioms'. So the obligation is a functional equation, and the ONLY residual break vector is the pinned function `loadedColumns` itself being unfaithful -- which is exactly the A-leg, audited live below.

**CLEAN AXIOMS:** ax_check.lean = pos_control + `#print axioms` -> exit=0: correct_collectFieldSelection, implementation_collectFieldSelection, loadedColumns, restrictionNames, referencedColumns all 'does not depend on any axioms'. Consistent with meta.json axioms=[] / deep_model_references=[] and the axiom_check.py skip stub.

A-LEG / DEEP-MODEL AUDIT (the assignment's focus). Because verification pins the impl to exactly `loadedColumns`, I measured that function against the LIVE callee at base_commit instead of accepting refinement.md's prose. only_probe.py drives the real `QuerySet.only()` through Django's deferred-loading machinery and reads the loaded column set off `SQLCompiler.pre_sql_setup`, over every referenced-column subset x every prior-defer subset of four model shapes (flat Referrer, custom-pk Custom, and BOTH halves of an MTI pair): 384 comparisons, 0 DISAGREEMENTS.

Corner evidence, all confirmed live: zero-arg `.only()` is a NO-OP loading the whole row; pk RETAINED though unreferenced (`.only(unique_field)` -> {id,unique_field}, the to_field case); pk retained EVEN WHEN DEFERRED (`defer(id)+.only(unique_field)` -> {id,unique_field}, mapping row 12 -- the unconditional retention atk_8 drops); the request reduction is a RAW STRING diff (`defer(origin)+.only(origin_id)` -> {id,origin_id}, row 7); skip COVERING the referenced set yields the whole row (row 13); MTI child pk IS the parent-link attname with `concrete_fields=['id','b','mtibase_ptr_id','c']` -- pk is NOT first, so atk_6's first-default-column model is genuinely wrong and `.only(c)` -> {c,mtibase_ptr_id}; custom pk retained (code). Both non-obvious guarantees the bundle asserts are true of the real callee, and atk_3/atk_6/atk_8 confirm the spec REJECTS impls that drop any of them. The deep model is not an ungrounded oracle echo.

**PATCH MATERIALIZATION VALIDATED:** mkpatch.py builds each faithful patch as the gold structure with only the FIELD-SELECTION ARM swapped, keeping the unmodeled legs (`_has_signal_listeners`, the `can_fast_delete` rewrite) identical to gold so a resolve difference is attributable to the modeled decision alone. My gold reconstruction is CODE-IDENTICAL to the bundle's patch.diff (differs only in comment lines) and resolved=TRUE with F2P 1/1 and P2P 41/41, which validates the method. All 10 runs completed=True; no timeouts, no image failures, no inconclusive run. Worktree at base 8180ffba21 (my own, via `git worktree add`).

**REFINEMENT.MD LEG AUDIT:** 6 legs, tagged R, R, R/I, R, R, I -- every leg is R or I, NO kind-3 leg, no untagged leg, and no leg claiming an axiom the bundle does not have. The 'no A row' claim is CORRECT rather than an evasion: `get_candidate_relations_to_delete` / `foreign_related_fields` legitimately enter as DATA (their observable output IS the candidateRelations input), and the gather itself is modeled deeply as flatten+dedup. Legs 4 and 5 are the load-bearing ones and are correctly tagged R with the `.only()` behaviours cited to sql/query.py:656/660/1971-1980 -- all verified live above. Leg 1's correspondence (accumulator starts at what the incoming fetch loads, NOT allFields) is the repaired pass-through claim and is pinned by atk_5. Prose matches the code I read at base and post-patch.

OBSERVATION (not a defect; too-STRONG direction). The spec is List-valued while the modeled decision is membership-determined (a SQL column choice), so order-only reshapes would be rejected even though their patches resolve. That cannot produce a verify-but-not-resolve witness; mapping.md §5's list<->set bijection and G-CONF's set comparison document the intended reading. Prior notes D5 recorded the same.

**FLOOR:** 9 admissible distinct attacks (>=5 required) spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo and two deep-model/A-leg classes; prepatch bug reproduced (atk_1, exit=1, decided witness, patch resolved=FALSE); structurally different positive control verifies (exit=0, frozen proof untouched). No impl with a closing clean-axiom proof exists, hence no faithful patch could fail to resolve. verify=>correct is NOT broken for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS-BREAK ATTACK on django__django-11087 lean bundle. Searched for an input where problem_spec_collectFieldSelection disagrees with the real post-patch callee. FOUND NONE across ~57,300 real-Django comparisons.

**REFERENCE DISCIPLINE:** worktree at base_commit 8180ffba21 with patch.diff APPLIED (confirmed patch.diff == instance.json['patch']). The base version was NOT used as reference for the patched arm; base is reference only for the untouched deferred-loading machinery.

HARNESS (written from scratch, independent of the bundle's own conformance_check.py): SHADOW = op-for-op transliteration of the Lean model (referencedColumns = flatten+dedup, restrictionNames = filter on raw strings, loadedColumns = if named.isEmpty then allFields else (pk::named).dedup). ORACLE = real Django: run the patched arm's own expression on real `_meta` / real get_candidate_relations_to_delete, hand the result to the real QuerySet.only(), read the loaded attname set off the real SQLCompiler.select. Compared as sets per mapping.md section 5 list-set bijection.

### EVIDENCE (all 0 disagreements):
1. Base sweep, 23-model zoo x all defer-subsets of size <=2 x 4 guard combos: 396 cmp.
2. Chained prior states (defer-then-defer, only-then-defer, defer-then-only, only-then-only) x 23 models x 4 guard combos: 8,560 cmp.
3. Direct loadedColumns leg, arbitrary requests decoupled from candidate relations, all subsets <=3 of attnames x all prior states: 17,964 cmp.
4. Exotic shapes (Meta.ordering, OneToOne primary_key, unique_together, explicit custom-named parent_link, self-referential FK, single-column model): 321 cmp.
5. Multi-column ForeignObject, foreign_related_fields length 2 -- the inner-list>1 shape no other sweep produces: 69 cmp.
6. Randomized fuzz, seed 4242, up to 3 chained defer/only ops: 30,000 cmp.

CORNERS PROBED FOR OVER-STRENGTH, ALL CONFIRMED CORRECT:
- **MTI:** pk.attname is the parent-link (base_ptr_id, p2_ptr_id, g2_ptr_id); 3-level inheritance; referenced column on the PARENT table; referenced column child-local only. Real load always matched.
- The unconditional pk retention: defer('id') / defer('base_ptr_id') with referenced={a,b} really does load the pk anyway (add_immediate_loading REPLACES the defer state storing (request, False), query.py:1971-1980, then deferred_to_data seeds must_include with orig_opts.pk, query.py:660). Spec's unconditional cons of pkColumn is right, not too strong.
- The empty-request no-op leg: spec says allFields (whole row), NOT defaultColumns. Isolated on a leaf model with candidateRelations=[] under 7 prior states where defaultColumns != allFields (e.g. only('big') -> default {big,id}, allFields {big,id,origin_id,other}). Real load was allFields in every one -- the strictly harder of the two predictions, and correct.
- Raw-string difference: defer('origin') does NOT cancel referenced 'origin_id' (load {id,origin_id}) while defer('origin_id') DOES (load whole row). Both reproduced; a resolving bridge would be wrong, the lexical filter is right.
- Partial overlap: two referenced cols with one deferred shrinks the REQUEST (load {b,id}), not merely the emptiness test. Reproduced on the multi-column ForeignObject: defer('ka') with referenced={ka,kb} -> real {id,kb}.
- LOOKUP_SEP path prior states (defer('tgt__id')), the literal 'pk' in only(), proxy models: all matched.
- guardA truthiness binding: select_related False / True (bare) / dict / select_related(None) reset -- Bool coercion is faithful.

REAL END-TO-END CASCADES (leg 0, actual .delete() with connection.queries, SELECT-list parsed excluding WHERE): 7 cases covering all four guard quadrants -- plain, base-manager-defers, pre_delete receiver, post_delete receiver, select_related-injecting Collector subclass, select_related+defer, select_related+signals. All 7 matched the shadow. Note: my first parse counted origin_id from the WHERE clause and reported 2 false mismatches; fixing the extractor to read only the SELECT list cleared both -- my own bug, not a spec defect.

**DOMAIN CHECK:** the spec is total over its Bool/List signature and both postcondition clauses are exhaustive, so there is no vacuous region hiding a divergence. The fast-delete branch (mapping.md row 10) is genuinely out of domain -- no column choice is made there -- so excluding it is not spec drift.

**MECHANICAL CHECKS:** scripts/lean_verify.sh Solution.lean exit 0 (no sorry). '#print axioms correct_collectFieldSelection' -> 'does not depend on any axioms' (clean, no sorryAx). markers.region_hashes(Solution.lean) matches meta.json region_hashes exactly on all six regions incl. spec_view 4a14a8e5. markers.same_spec(Solution.lean, Solution_prepatch.lean) = True, so the prepatch rival carries a byte-identical spec region. F2P test delete.tests.DeletionTests.test_only_referenced_fields_selected PASSES on the patched worktree.

**VERDICT:** FAITHFUL. No diverging input exists to cite. The spec is if anything notably tighter than a naive model would be -- it correctly encodes three non-obvious real behaviours (unconditional pk retention surviving a skipped pk, the empty-request degeneration to the whole row including previously-skipped columns, and the raw-string namespace of the skip difference) that a too-strong 'loads exactly the referenced set' spec would get wrong. Each was independently reproduced against the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE/PROVENANCE: judged the CURRENT spec view only. The recorded G-PANEL-3 LEAKAGE (agent_verdict LEAKAGE) was stamped against Solution.lean sha 7c99edc48648b6...; the bundle now carries 3314edc4b2aca2ef7513dab4b8b1a7beb84d2a119d3f19c5e90cd1e0d0ea2717, which matches the current G-AX/G-CONF/G-DIFF/G-GOLD/G-LEAK source stamps. I re-judged fresh rather than echoing the stale label (retained attack labels carry the oracle verdict). The prior finding was that the spec view named the signals carve-out ("no deletion receiver is registered", "receivers see every column"); that prose is GONE from the current view and the guards are now abstracted.

**INTEGRITY:** recomputed via swebench_unified.markers with LeanBackend. All six region_hashes match meta.json byte-for-byte (axioms 4b3f6850, impl 966a4336, post-conditions 72aa8e87, proof 9362246, pure 6a65a8f2, spec_view 4a14a8e5). same_spec(Solution.lean, Solution_prepatch.lean) = True and both spec views hash identically to 4a14a8e5 -> the prepatch variant is a same-spec/different-impl rival, so G-DIFF is not smuggling a spec change. lean_verify.sh exit 0; `#print axioms correct_collectFieldSelection` -> "does not depend on any axioms" (no sorryAx, proof is real, not fake).

### LEAKAGE ANALYSIS (baseline = solver-visible problem_statement ONLY, never hints_text):
(1) Discriminator suppression. The gold edit's decisive fact is `not (sub_objs.query.select_related or _has_signal_listeners(related_model))`. The F2P test test_only_referenced_fields_selected turns on exactly the signals half. The current spec view models BOTH conditions as two uninterpreted Bools guardA/guardB and states explicitly (lines 25-27) "two conditions of the fetch under which no restriction is applied to it at all. What makes either of them hold is not part of this decision: they arrive as flags." Grep for signal|receiv|listen|select_related|pre_delete|post_delete|has_listeners|defer|eager|materiali over the spec view: ZERO hits. The hints-only vocabulary that the prior finding flagged is fully absent, so the non-public carve-out CONTENT is not transmitted.

(2) Identifier echo. Tokenized every gold-ADDED line; intersected with spec-view identifiers. Intersection is English stopwords plus {cases, model, only, referenced, related, set, some}. No gold-added identifier survives: `_has_signal_listeners`, select_related, pre_delete, post_delete, has_listeners, referenced_fields, foreign_related_fields, get_candidate_relations_to_delete, sub_objs, related_model, attname, on_delete, remote_field, chain, from_iterable are all ABSENT. Note `get_candidate_relations_to_delete` is pre-existing at base_commit (deletion.py:54, called at :150 and :211), so the spec's "candidate relations" phrasing describes a symbol the solver can already read, not an edit.

(3) Changed-symbol collision. `_patch_changed_symbols`(gold) = {add_field_update, can_fast_delete, collect, has_signal_listeners}. Only "collect" appears, as the English noun "collector" (line 9) and inside problem_spec_collectFieldSelection. "collector" is public: problem_statement contains "collector.collect(del_query)" in the traceback verbatim. Not a leak.

(4) Path/line/diff-marker/narration. No "deletion.py", no django/db/models path, no .py, no :2NN line refs, no @@ / diff --git / +++ markers. Narration screen clean (bug/fix/patch/regression/previously/incorrectly/wrong/broken all absent) -- and clean on prose, not just by luck of the G-LEAK vocabulary list.

(5) Mechanical control: leakage.screen(Solution.lean, LeanBackend, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. I did not rely on this alone; it agrees with the manual reads above.

WHAT REMAINS, AND WHY IT IS NOT LEAKAGE: the spec view does disclose the SHAPE "there exist two independent suppression flags," and the narrowing rule (dedup of gathered target columns, minus skipped names, plus pkColumn, whole row when empty). The narrowing rule is what the public problem_statement asks for in its own words ("the UnicodeDecodeError is occurring for a field ... that is not actually needed for the .delete() (it's not a primary key etc), so Django shouldn't be fetching that field") -- including the primary-key retention, which the statement's parenthetical supplies.

The two-flag arity is a signature fact, not the discriminating condition: a consumer handed guardA/guardB learns that two booleans gate the optimization but cannot recover that either one is select_related or a pre_delete/post_delete listener check, which is precisely the fact the prior panel proved decisive for the F2P test. Disclosing that a guard exists without disclosing its content does not let a solver reconstruct the gold edit; they would still have to discover the receiver check from the repo. Per spec_guide.md rule 6 the standard is "state the abstract desired behavior; never the edit or the diagnosis," and the abstracted-flag form is the canonical way to satisfy it. Judged NO-LEAKAGE without invoking the relaxed-leakage exception -- no leak needs excusing here.

ADJACENT OBSERVATION (out of this gate's scope, flagged not escalated): G-PANEL-2 is recorded fail/UNFAITHFUL against the OLD sha 7c99edc4 as well, with a repro arguing the modeled function is not a function of its declared inputs when the related manager carries a pre-existing defer (only() collapses deferred_loading, so real loads the whole row while the model predicts ['id','unique_field']). The current spec view's loadedColumns still keeps skippedNames as an input and drops those names from the restriction, which is the modeling that repro targeted. That is a faithfulness question for panel 2, not leakage, and I make no faithfulness ruling on it; the leakage verdict above is independent of how it resolves.

**SCOPE/PROVENANCE:** judged the CURRENT spec view only. The recorded G-PANEL-3 LEAKAGE (agent_verdict LEAKAGE) was stamped against Solution.lean sha 7c99edc48648b6...; the bundle now carries 3314edc4b2aca2ef7513dab4b8b1a7beb84d2a119d3f19c5e90cd1e0d0ea2717, which matches the current G-AX/G-CONF/G-DIFF/G-GOLD/G-LEAK source stamps. I re-judged fresh rather than echoing the stale label (retained attack labels carry the oracle verdict). The prior finding was that the spec view named the signals carve-out ("no deletion receiver is registered", "receivers see every column"); that prose is GONE from the current view and the guards are now abstracted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
