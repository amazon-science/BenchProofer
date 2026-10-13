# P2 adversarial audit — django__django-15278

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
-  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
+  if !c.allowsNull || c.hasStoredDefault then
     return true
   return false
 -- impl-end
@@ -65,9 +65,7 @@
         (implementation_requiresTableRebuild c) := by
   intro c
   unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
-  simp only [Id.run, bind, pure]
-  by_cases h : (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) = true
-  · simp [h]
-  · simp only [Bool.not_eq_true] at h
-    simp [h]
+  simp only [Id.run]
+  cases c.isPrimaryKey <;> cases c.isUnique <;> cases c.allowsNull <;>
+    cases c.hasStoredDefault <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
-  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
+  if c.isPrimaryKey || c.isUnique || !c.allowsNull then
     return true
   return false
 -- impl-end
@@ -65,9 +65,7 @@
         (implementation_requiresTableRebuild c) := by
   intro c
   unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
-  simp only [Id.run, bind, pure]
-  by_cases h : (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) = true
-  · simp [h]
-  · simp only [Bool.not_eq_true] at h
-    simp [h]
+  simp only [Id.run]
+  cases c.isPrimaryKey <;> cases c.isUnique <;> cases c.allowsNull <;>
+    cases c.hasStoredDefault <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
-  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
+  if c.isPrimaryKey || c.isUnique || (!c.allowsNull && c.hasStoredDefault) then
     return true
   return false
 -- impl-end
@@ -65,9 +65,7 @@
         (implementation_requiresTableRebuild c) := by
   intro c
   unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
-  simp only [Id.run, bind, pure]
-  by_cases h : (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) = true
-  · simp [h]
-  · simp only [Bool.not_eq_true] at h
-    simp [h]
+  simp only [Id.run]
+  cases c.isPrimaryKey <;> cases c.isUnique <;> cases c.allowsNull <;>
+    cases c.hasStoredDefault <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,9 +53,7 @@
 
 -- impl-start
 def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
-  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
-    return true
-  return false
+  return true
 -- impl-end
 
 -- proof-start
@@ -65,9 +63,7 @@
         (implementation_requiresTableRebuild c) := by
   intro c
   unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
-  simp only [Id.run, bind, pure]
-  by_cases h : (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) = true
-  · simp [h]
-  · simp only [Bool.not_eq_true] at h
-    simp [h]
+  simp only [Id.run]
+  cases c.isPrimaryKey <;> cases c.isUnique <;> cases c.allowsNull <;>
+    cases c.hasStoredDefault <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,8 +53,6 @@
 
 -- impl-start
 def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
-  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
-    return true
   return false
 -- impl-end
 
@@ -65,9 +63,7 @@
         (implementation_requiresTableRebuild c) := by
   intro c
   unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
-  simp only [Id.run, bind, pure]
-  by_cases h : (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) = true
-  · simp [h]
-  · simp only [Bool.not_eq_true] at h
-    simp [h]
+  simp only [Id.run]
+  cases c.isPrimaryKey <;> cases c.isUnique <;> cases c.allowsNull <;>
+    cases c.hasStoredDefault <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 
 -- impl-start
 def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
-  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
+  if c.isPrimaryKey || c.isUnique || c.allowsNull || c.hasStoredDefault then
     return true
   return false
 -- impl-end
@@ -65,9 +65,7 @@
         (implementation_requiresTableRebuild c) := by
   intro c
   unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
-  simp only [Id.run, bind, pure]
-  by_cases h : (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) = true
-  · simp [h]
-  · simp only [Bool.not_eq_true] at h
-    simp [h]
+  simp only [Id.run]
+  cases c.isPrimaryKey <;> cases c.isUnique <;> cases c.allowsNull <;>
+    cases c.hasStoredDefault <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing how a newly-added column is materialized on a backend whose in-place
column-addition statement is restricted.

Some backends can append a column to an existing table only when the column is
"plain": it permits nulls, carries no stored default value, and is neither a
primary-key column nor a uniqueness-bearing column. For any column outside that
plain class the column cannot be appended in place and the table must instead be
reconstructed to accommodate it.

The decision modeled here returns whether the table must be reconstructed. The
table must be reconstructed exactly when the column is a primary-key column, or a
uniqueness-bearing column, or a non-nullable column, or a column that carries a
stored default value; otherwise the plain in-place column addition suffices.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether the
-- column carries a stored default value is computed elsewhere by machinery that
-- is identical regardless of the decision modeled here; it is abstracted into
-- the input as a single boolean observation rather than recomputed, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The properties of a freshly-added column that determine how the column is
materialized on the restricted backend. Each component is the boolean
observation the decision consults:

* `isPrimaryKey`   — the column is the table's primary-key column;
* `isUnique`       — the column carries a uniqueness requirement;
* `allowsNull`     — the column permits null values;
* `hasStoredDefault` — the column carries a stored default value. -/
structure ColumnProps where
  isPrimaryKey : Bool
  isUnique : Bool
  allowsNull : Bool
  hasStoredDefault : Bool
-- pure-end

-- post-conditions-start
/-- The table must be reconstructed exactly when the column is a primary-key
column, or a uniqueness-bearing column, or a non-nullable column, or a column
that carries a stored default value. Each of these four conditions independently
forces reconstruction; only a column that is none of them is materialized by the
plain in-place column addition. -/
def problem_spec_requiresTableRebuild (c : ColumnProps) (result : Bool) : Prop :=
  result = (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault)
-- post-conditions-end

-- impl-start
def implementation_requiresTableRebuild (c : ColumnProps) : Bool :=
  (c.isPrimaryKey || c.isUnique) || (!c.allowsNull || c.hasStoredDefault)
-- impl-end

-- proof-start
theorem correct_requiresTableRebuild :
    ∀ (c : ColumnProps),
      problem_spec_requiresTableRebuild c
        (implementation_requiresTableRebuild c) := by
  intro c
  unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
  cases c.isPrimaryKey <;> cases c.isUnique <;> cases c.allowsNull <;>
    cases c.hasStoredDefault <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is maximally tight: problem_spec_requiresTableRebuild c result := result = (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) — full boolean equality to a 4-way disjunction over four fully-grounded input booleans. No axioms; G-AX is a correct skip stub (the changed add_field routing decision is modeled DEEPLY as the concrete disjunction, not axiomatized).

AXIOM/DEEP-MODEL AUDIT (A-leg focus): refinement.md legs 1-4 = R (boolean field <-> field attribute, negation), legs 5-6 = I (disjunction, branch selector). NO A-legs exist and NO kind-3 (ungrounded) leg. Leg 4 (hasStoredDefault <- `effective_default(field) is not None`) abstracts an UNCHANGED callee into an input observation — legitimate R, not an ungrounded oracle: the result is fully determined by the 4 grounded inputs and effective_default is byte-identical pre/post-patch (mapping.md callee provenance confirms). axiom_check.py skip stub is correct. conformance_check.py differential-tests the R/I shadow == in-process replica of the post-patch decision over all 16 exhaustive 4-bit assignments + 120k fuzz.

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec; impl region edited only, axioms/pure/pre/post byte-identical; verified concurrently, batches of 4 then 3):
  atk_1 prepatch bug (drops isPrimaryKey||isUnique): lean_verify.sh EXIT=1, rfl fails at 70:33 — does NOT close.
  atk_2 partial-domain (drops hasStoredDefault): EXIT=1, does NOT close.
  atk_3 control-flow-effect (&& instead of || on last two disjuncts): EXIT=1, does NOT close.
  atk_4 ungrounded over-approx (return true): EXIT=1, does NOT close.
  atk_5 under-approx (return false): EXIT=1, does NOT close.
  atk_6 boundary polarity flip (allowsNull instead of !allowsNull): EXIT=1, does NOT close.
All 6 fail with genuine `rfl` proof failures (equality to the gold disjunction unprovable), not syntax errors.

Commands: `bash scripts/lean_verify.sh atk_N.lean` -> exit 1 for all N in 1..6.

POSITIVE CONTROL pos_ctrl.lean (semantically-identical rewrite: direct return `(isPrimaryKey||isUnique)||(!allowsNull||hasStoredDefault)`, no if/Id.run): lean_verify.sh EXIT=0; `#print axioms correct_requiresTableRebuild` => "does not depend on any axioms" (clean, no sorry).

No wrong impl produced a closing clean-axiom proof, so there was NO faithful patch to materialize/run through run_resolve (patches={}). Because the postcondition is exact boolean equality over grounded inputs, ANY proof-closing impl is provably equal to the gold disjunction and therefore behaviorally identical to the post-patch decision, so its patch would resolve. verify => correct holds. VERDICT: SOUND (>=6 distinct wrong impls attempted, none breaks the spec; positive control verifies with clean axioms).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing how a newly-added column is materialized on a backend whose in-place
column-addition statement is restricted.

Some backends can append a column to an existing table only when the column is
"plain": it permits nulls, carries no stored default value, and is neither a
primary-key column nor a uniqueness-bearing column. For any column outside that
plain class the column cannot be appended in place and the table must instead be
reconstructed to accommodate it.

The decision modeled here returns whether the table must be reconstructed. The
table must be reconstructed exactly when the column is a primary-key column, or a
uniqueness-bearing column, or a non-nullable column, or a column that carries a
stored default value; otherwise the plain in-place column addition suffices.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether the
-- column carries a stored default value is computed elsewhere by machinery that
-- is identical regardless of the decision modeled here; it is abstracted into
-- the input as a single boolean observation rather than recomputed, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The properties of a freshly-added column that determine how the column is
materialized on the restricted backend. Each component is the boolean
observation the decision consults:

* `isPrimaryKey`   — the column is the table's primary-key column;
* `isUnique`       — the column carries a uniqueness requirement;
* `allowsNull`     — the column permits null values;
* `hasStoredDefault` — the column carries a stored default value. -/
structure ColumnProps where
  isPrimaryKey : Bool
  isUnique : Bool
  allowsNull : Bool
  hasStoredDefault : Bool
-- pure-end

-- post-conditions-start
/-- The table must be reconstructed exactly when the column is a primary-key
column, or a uniqueness-bearing column, or a non-nullable column, or a column
that carries a stored default value. Each of these four conditions independently
forces reconstruction; only a column that is none of them is materialized by the
plain in-place column addition. -/
def problem_spec_requiresTableRebuild (c : ColumnProps) (result : Bool) : Prop :=
  result = (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault)
-- post-conditions-end

-- impl-start
def implementation_requiresTableRebuild (c : ColumnProps) : Bool :=
  (c.isPrimaryKey || c.isUnique) || (!c.allowsNull || c.hasStoredDefault)
-- impl-end

-- proof-start
theorem correct_requiresTableRebuild :
    ∀ (c : ColumnProps),
      problem_spec_requiresTableRebuild c
        (implementation_requiresTableRebuild c) := by
  intro c
  unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
  cases c.isPrimaryKey <;> cases c.isUnique <;> cases c.allowsNull <;>
    cases c.hasStoredDefault <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is maximally tight: problem_spec_requiresTableRebuild c result := result = (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) — full boolean equality to a 4-way disjunction over four fully-grounded input booleans. No axioms; G-AX is a correct skip stub (the changed add_field routing decision is modeled DEEPLY as the concrete disjunction, not axiomatized).

AXIOM/DEEP-MODEL AUDIT (A-leg focus): refinement.md legs 1-4 = R (boolean field <-> field attribute, negation), legs 5-6 = I (disjunction, branch selector). NO A-legs exist and NO kind-3 (ungrounded) leg. Leg 4 (hasStoredDefault <- `effective_default(field) is not None`) abstracts an UNCHANGED callee into an input observation — legitimate R, not an ungrounded oracle: the result is fully determined by the 4 grounded inputs and effective_default is byte-identical pre/post-patch (mapping.md callee provenance confirms). axiom_check.py skip stub is correct. conformance_check.py differential-tests the R/I shadow == in-process replica of the post-patch decision over all 16 exhaustive 4-bit assignments + 120k fuzz.

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec; impl region edited only, axioms/pure/pre/post byte-identical; verified concurrently, batches of 4 then 3):
  atk_1 prepatch bug (drops isPrimaryKey||isUnique): lean_verify.sh EXIT=1, rfl fails at 70:33 — does NOT close.
  atk_2 partial-domain (drops hasStoredDefault): EXIT=1, does NOT close.
  atk_3 control-flow-effect (&& instead of || on last two disjuncts): EXIT=1, does NOT close.
  atk_4 ungrounded over-approx (return true): EXIT=1, does NOT close.
  atk_5 under-approx (return false): EXIT=1, does NOT close.
  atk_6 boundary polarity flip (allowsNull instead of !allowsNull): EXIT=1, does NOT close.
All 6 fail with genuine `rfl` proof failures (equality to the gold disjunction unprovable), not syntax errors.

Commands: `bash scripts/lean_verify.sh atk_N.lean` -> exit 1 for all N in 1..6.

POSITIVE CONTROL pos_ctrl.lean (semantically-identical rewrite: direct return `(isPrimaryKey||isUnique)||(!allowsNull||hasStoredDefault)`, no if/Id.run): lean_verify.sh EXIT=0; `#print axioms correct_requiresTableRebuild` => "does not depend on any axioms" (clean, no sorry).

No wrong impl produced a closing clean-axiom proof, so there was NO faithful patch to materialize/run through run_resolve (patches={}). Because the postcondition is exact boolean equality over grounded inputs, ANY proof-closing impl is provably equal to the gold disjunction and therefore behaviorally identical to the post-patch decision, so its patch would resolve. verify => correct holds. VERDICT: SOUND (>=6 distinct wrong impls attempted, none breaks the spec; positive control verifies with clean axioms).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-15278 lean bundle. Modeled function = the boolean routing predicate at the head of DatabaseSchemaEditor.add_field (sqlite3 backend), which selects _remake_table (True) vs super().add_field (False).

GROUND TRUTH: verified the real repo at base_commit 0ab58c120939093fea90822f376e1866fc714d1f (git show ...:django/db/backends/sqlite3/schema.py) and the gold patch from data/swe_bench_verified/test.jsonl. Post-patch condition is exactly:
  if (field.primary_key or field.unique or not field.null or self.effective_default(field) is not None): _remake_table else super().add_field
At base_commit add_field has NO earlier branch before this decision (the M2M special-case is a later revision), so the decision IS precisely this if-condition.

SPEC: problem_spec_requiresTableRebuild c result := result = (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault). Component-wise bijection: isPrimaryKey<-field.primary_key, isUnique<-field.unique, allowsNull<-field.null, hasStoredDefault<-(effective_default(field) is not None) (mapping.md). This is exactly the post-patch boolean function; not stronger, not weaker. Python 'or' short-circuits but with no side effects affecting truth value here, so || truth-value-matches.

SEARCHED FOR DIVERGENCE: exhaustive over all 16 assignments of the four booleans + 120k pinned-seed fuzz via conformance_check.py -> checked=120016 disagreements=0. No input found where the spec disagrees with the real repo's post-patch decision. The abstraction of effective_default into a single boolean is sound because its computation is byte-identical pre/post-patch and is not part of the changed decision.

MECHANICAL CHECKS: (1) same_spec(Solution, Solution_prepatch) = True under LeanBackend tables — spec region byte-identical; prepatch differs only in impl/proof. (2) lean_verify.sh exit 0 (compiles, no sorry). (3) #print axioms correct_requiresTableRebuild -> [propext] only; NO sorryAx — proof is genuine. (4) The spec correctly discriminates the fix: prepatch impl (drops isPrimaryKey||isUnique) violates the spec on isUnique=true,allowsNull=true,isPrimaryKey=false,hasStoredDefault=false — precisely the F2P test_add_field_o2o_nullable case (nullable OneToOneField, unique forced True).

CONCLUSION: The modeled function agrees with the real callee on every input. Spec does not drift and is not too strong. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen) PASSES with zero hard_failures; same_spec(Solution, Solution_prepatch)=True (spec region byte-identical); axioms/pure/post regions identical in prepatch. Spec view (imports + docstrings + ColumnProps struct + problem_spec postcondition) elides impl and proof (both shown as 'elided — supplied by the consumer'), so no gold edit is reconstructible from it.

Leakage analysis vs public problem_statement:
- Problem statement already discloses the SQLite crash on adding a nullable OneToOneField and the 'Cannot add a UNIQUE column' error, so the uniqueness dimension is public.
- No diff markers, no patched file path (django/db/backends/sqlite3/schema.py), no patched dotted module path in the view.
- Patched repo symbols (add_field, _remake_table, effective_default; changed-symbol set = {delete_model}) appear nowhere in spec-view identifiers or comments. Spec uses abstracted domain names (requiresTableRebuild, ColumnProps, isPrimaryKey/isUnique/allowsNull/hasStoredDefault).
- No bug/fix/regression/pre-patch narration in any spec-view comment or docstring; rationale prose is abstract ('backend whose in-place column-addition statement is restricted').
- The postcondition pins CORRECT final behavior (result = isPrimaryKey || isUnique || !allowsNull || hasStoredDefault). This is the legitimate target of a spec, not a leak: it does not narrate the delta, does not reveal the pre-patch decision, and presents all four disjuncts symmetrically so a solver cannot localize which disjuncts the gold edit added, nor the file/symbol/diff of the edit.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement (hints_text excluded per policy). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
