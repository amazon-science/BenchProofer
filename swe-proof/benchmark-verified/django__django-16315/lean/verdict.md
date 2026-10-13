# P2 adversarial audit — django__django-16315

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,11 @@
     (uniqueFields updateFields : List FieldRef) : List Char := Id.run do
   let mut uniqueCols : List (List Char) := []
   for f in uniqueFields do
-    uniqueCols := uniqueCols ++ [quoteName f.column]
+    uniqueCols := uniqueCols ++ [quoteName f.name]
   let mut assigns : List (List Char) := []
   for f in updateFields do
-    assigns := assigns ++ [assignColumn f]
+    let q := quoteName f.name
+    assigns := assigns ++ [q ++ " = EXCLUDED.".toList ++ q]
   return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
     ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,8 @@
     uniqueCols := uniqueCols ++ [quoteName f.column]
   let mut assigns : List (List Char) := []
   for f in updateFields do
-    assigns := assigns ++ [assignColumn f]
+    let q := quoteName f.name
+    assigns := assigns ++ [q ++ " = EXCLUDED.".toList ++ q]
   return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
     ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,10 +52,10 @@
 def implementation_renderUpsertClause
     (uniqueFields updateFields : List FieldRef) : List Char := Id.run do
   let mut uniqueCols : List (List Char) := []
-  for f in uniqueFields do
+  for f in updateFields do
     uniqueCols := uniqueCols ++ [quoteName f.column]
   let mut assigns : List (List Char) := []
-  for f in updateFields do
+  for f in uniqueFields do
     assigns := assigns ++ [assignColumn f]
   return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
     ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,8 +57,8 @@
   let mut assigns : List (List Char) := []
   for f in updateFields do
     assigns := assigns ++ [assignColumn f]
-  return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
-    ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
+  return "ON CONFLICT(".toList ++ List.intercalate ",".toList uniqueCols
+    ++ ") DO UPDATE SET ".toList ++ List.intercalate ",".toList assigns
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,7 +57,7 @@
   let mut assigns : List (List Char) := []
   for f in updateFields do
     assigns := assigns ++ [assignColumn f]
-  return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
+  return "ON CONFLICT (".toList ++ List.intercalate ", ".toList uniqueCols
     ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -50,41 +50,18 @@
 
 -- impl-start
 def implementation_renderUpsertClause
-    (uniqueFields updateFields : List FieldRef) : List Char := Id.run do
-  let mut uniqueCols : List (List Char) := []
-  for f in uniqueFields do
-    uniqueCols := uniqueCols ++ [quoteName f.column]
-  let mut assigns : List (List Char) := []
-  for f in updateFields do
-    assigns := assigns ++ [assignColumn f]
-  return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
-    ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
+    (uniqueFields updateFields : List FieldRef) : List Char :=
+  "ON CONFLICT(".toList
+    ++ List.intercalate ", ".toList (uniqueFields.map (fun f => quoteName f.column))
+    ++ ") DO UPDATE SET ".toList
+    ++ List.intercalate ", ".toList (updateFields.map assignColumn)
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop `acc := acc ++ [g f]`, generalized
-over the accumulator, computes `init ++ xs.map g`. -/
-theorem foldMapHelper_renderUpsertClause
-    (g : FieldRef → List Char) (xs : List FieldRef) (init : List (List Char)) :
-    (forIn (m := Id) xs init (fun f acc => pure (ForInStep.yield (acc ++ [g f]))))
-      = init ++ xs.map g := by
-  induction xs generalizing init with
-  | nil => simp only [List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_renderUpsertClause :
     ∀ (uniqueFields updateFields : List FieldRef),
     problem_spec_renderUpsertClause uniqueFields updateFields
       (implementation_renderUpsertClause uniqueFields updateFields) := by
   intro uf vf
-  unfold problem_spec_renderUpsertClause implementation_renderUpsertClause
-  simp only [Id.run, bind]
-  rw [foldMapHelper_renderUpsertClause (fun f => quoteName f.column) uf [],
-      foldMapHelper_renderUpsertClause assignColumn vf []]
-  simp only [List.nil_append]
   rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,41 +50,21 @@
 
 -- impl-start
 def implementation_renderUpsertClause
-    (uniqueFields updateFields : List FieldRef) : List Char := Id.run do
-  let mut uniqueCols : List (List Char) := []
-  for f in uniqueFields do
-    uniqueCols := uniqueCols ++ [quoteName f.column]
-  let mut assigns : List (List Char) := []
-  for f in updateFields do
-    assigns := assigns ++ [assignColumn f]
-  return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
-    ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
+    (uniqueFields updateFields : List FieldRef) : List Char :=
+  match uniqueFields, updateFields with
+  | [], [] => []
+  | _, _ =>
+    "ON CONFLICT(".toList
+      ++ List.intercalate ", ".toList (uniqueFields.map (fun f => quoteName f.column))
+      ++ ") DO UPDATE SET ".toList
+      ++ List.intercalate ", ".toList (updateFields.map assignColumn)
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` accumulation loop `acc := acc ++ [g f]`, generalized
-over the accumulator, computes `init ++ xs.map g`. -/
-theorem foldMapHelper_renderUpsertClause
-    (g : FieldRef → List Char) (xs : List FieldRef) (init : List (List Char)) :
-    (forIn (m := Id) xs init (fun f acc => pure (ForInStep.yield (acc ++ [g f]))))
-      = init ++ xs.map g := by
-  induction xs generalizing init with
-  | nil => simp only [List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_renderUpsertClause :
     ∀ (uniqueFields updateFields : List FieldRef),
     problem_spec_renderUpsertClause uniqueFields updateFields
       (implementation_renderUpsertClause uniqueFields updateFields) := by
   intro uf vf
-  unfold problem_spec_renderUpsertClause implementation_renderUpsertClause
-  simp only [Id.run, bind]
-  rw [foldMapHelper_renderUpsertClause (fun f => quoteName f.column) uf [],
-      foldMapHelper_renderUpsertClause assignColumn vf []]
-  simp only [List.nil_append]
   rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two attributes of a
-- resolved field that this behavior reads (its declared name and its database
-- column) are carried explicitly by the `FieldRef` carrier below, and the
-- identifier-quoting and separator-joining are reproduced concretely (R/I), not
-- abstracted behind an axiom. The proof agent may add `_prop` axioms only if it
-- gets stuck.
-- axioms-end

-- pure-start
/-- A resolved schema field, carrying only the two attributes this behavior
reads: its declared `name` and the `column` it occupies in the database (which
may differ from the name when an explicit database column is configured). -/
structure FieldRef where
  name : List Char
  column : List Char
deriving DecidableEq, Repr

/-- Quote a database identifier for embedding in SQL: wrap it in double quotes,
unless it is already wrapped in double quotes (quoting once is enough). -/
def quoteName (s : List Char) : List Char :=
  match s.head?, s.getLast? with
  | some '"', some '"' => s
  | _, _ => '"' :: (s ++ ['"'])

/-- The text assigning one updated column from the conflicting row: the quoted
column, ` = EXCLUDED.`, then the same quoted column. -/
def assignColumn (f : FieldRef) : List Char :=
  let q := quoteName f.column
  q ++ " = EXCLUDED.".toList ++ q
-- pure-end

-- post-conditions-start
/-- The upsert suffix renders the conflict-target list and the assignment list,
both keyed by each field's database `column` (never its declared name), separated
by `", "`. The literal template text framing the two slots is pinned verbatim,
and both rendered slots are pinned element-wise to the input field lists, so no
component is left unconstrained. -/
def problem_spec_renderUpsertClause
    (uniqueFields updateFields : List FieldRef) (result : List Char) : Prop :=
  result =
    "ON CONFLICT(".toList
      ++ List.intercalate ", ".toList (uniqueFields.map (fun f => quoteName f.column))
      ++ ") DO UPDATE SET ".toList
      ++ List.intercalate ", ".toList (updateFields.map assignColumn)
-- post-conditions-end

-- impl-start
def implementation_renderUpsertClause
    (uniqueFields updateFields : List FieldRef) : List Char := Id.run do
  let mut uniqueCols : List (List Char) := []
  for f in uniqueFields do
    uniqueCols := uniqueCols ++ [quoteName f.column]
  let mut assigns : List (List Char) := []
  for f in updateFields do
    assigns := assigns ++ [assignColumn f]
  return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
    ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation loop `acc := acc ++ [g f]`, generalized
over the accumulator, computes `init ++ xs.map g`. -/
theorem foldMapHelper_renderUpsertClause
    (g : FieldRef → List Char) (xs : List FieldRef) (init : List (List Char)) :
    (forIn (m := Id) xs init (fun f acc => pure (ForInStep.yield (acc ++ [g f]))))
      = init ++ xs.map g := by
  induction xs generalizing init with
  | nil => simp only [List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_renderUpsertClause :
    ∀ (uniqueFields updateFields : List FieldRef),
    problem_spec_renderUpsertClause uniqueFields updateFields
      (implementation_renderUpsertClause uniqueFields updateFields) := by
  intro uf vf
  unfold problem_spec_renderUpsertClause implementation_renderUpsertClause
  simp only [Id.run, bind]
  rw [foldMapHelper_renderUpsertClause (fun f => quoteName f.column) uf [],
      foldMapHelper_renderUpsertClause assignColumn vf []]
  simp only [List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

R/I-only bundle: axioms=[], deep_model_references=[], opaque_callees=[]. The postcondition problem_spec_renderUpsertClause is a TOTAL FUNCTIONAL EQUALITY (result = exact expression, forall-quantified over both field lists), the strongest spec form. same_spec=True verified for all 7 attacks (impl region only edited; axioms/pure/pre/post byte-identical).

### ATTACK RESULTS (cmd: bash scripts/lean_verify.sh <file>; run concurrently <=4):
- atk_1.lean (prepatch bug: key by f.name on BOTH lists): exit=1 (rewrite failed, does NOT verify) -> prepatch reproduced.
- atk_2.lean (partial: unique by column, update by name): exit=1, does NOT verify.
- atk_3.lean (control-flow-effect: swap the two field lists): exit=1, does NOT verify.
- atk_4.lean (boundary: wrong separator ',' vs ', '): exit=1, does NOT verify.
- atk_5.lean (boundary: wrong template 'ON CONFLICT (' extra space): exit=1, does NOT verify.
- atk_6.lean (ungrounded-oracle echo: returns spec RHS verbatim, keyed by f.column): exit=0 VERIFIES; #print axioms correct_renderUpsertClause -> 'does not depend on any axioms' (clean). This is a GOLD-EQUIVALENT echo (functionally identical to gold, keys by f.column).
- atk_7.lean (partial-domain: echo when nonempty else [] on ([],[])): exit=1, does NOT verify (spec demands the framing template even for empty lists).

pos_control.lean (exact gold Solution.lean): exit=0 verifies; #print axioms -> [propext, Quot.sound] (standard, clean, from List.intercalate/Id.run).

RESOLVE (echo-attack policy): the only clean-axiom-closing impl, atk_6, is functionally equal to gold (keys by f.column), so its faithful refined patch IS the gold patch. Ran official harness: run_resolve('django__django-16315', gold_patch, timeout=1800, retries=1) -> RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1 (log: resolve_atk6.log). A resolving gold-equivalent echo is NOT a weakness (per 2026-08-06 resolved echo-attack policy).

A-LEG AUDIT: no A-consumed / A-reference legs to audit (axioms region empty, only a comment; no opaque/axiom/_prop declarations). refinement.md's 4 legs are R (str->FieldRef type refinement of get_field carrier) or I (quote_name and the ON CONFLICT(...) DO UPDATE SET template reproduced concretely) with zero kind-3/deep-model refs. No model<->real-callee correspondence gap: quote_name and the template are reproduced concretely rather than abstracted, so there is nothing an axiom could over-approximate. refinement.md legs are all R/I -> audit passes.

CONCLUSION: >=5 distinct wrong impls run; every genuinely-wrong impl (prepatch, partial, control-flow, 2x boundary, partial-domain) FAILS to verify. The single verifying impl is a gold-equivalent echo whose materialized faithful patch RESOLVES. No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two attributes of a
-- resolved field that this behavior reads (its declared name and its database
-- column) are carried explicitly by the `FieldRef` carrier below, and the
-- identifier-quoting and separator-joining are reproduced concretely (R/I), not
-- abstracted behind an axiom. The proof agent may add `_prop` axioms only if it
-- gets stuck.
-- axioms-end

-- pure-start
/-- A resolved schema field, carrying only the two attributes this behavior
reads: its declared `name` and the `column` it occupies in the database (which
may differ from the name when an explicit database column is configured). -/
structure FieldRef where
  name : List Char
  column : List Char
deriving DecidableEq, Repr

/-- Quote a database identifier for embedding in SQL: wrap it in double quotes,
unless it is already wrapped in double quotes (quoting once is enough). -/
def quoteName (s : List Char) : List Char :=
  match s.head?, s.getLast? with
  | some '"', some '"' => s
  | _, _ => '"' :: (s ++ ['"'])

/-- The text assigning one updated column from the conflicting row: the quoted
column, ` = EXCLUDED.`, then the same quoted column. -/
def assignColumn (f : FieldRef) : List Char :=
  let q := quoteName f.column
  q ++ " = EXCLUDED.".toList ++ q
-- pure-end

-- post-conditions-start
/-- The upsert suffix renders the conflict-target list and the assignment list,
both keyed by each field's database `column` (never its declared name), separated
by `", "`. The literal template text framing the two slots is pinned verbatim,
and both rendered slots are pinned element-wise to the input field lists, so no
component is left unconstrained. -/
def problem_spec_renderUpsertClause
    (uniqueFields updateFields : List FieldRef) (result : List Char) : Prop :=
  result =
    "ON CONFLICT(".toList
      ++ List.intercalate ", ".toList (uniqueFields.map (fun f => quoteName f.column))
      ++ ") DO UPDATE SET ".toList
      ++ List.intercalate ", ".toList (updateFields.map assignColumn)
-- post-conditions-end

-- impl-start
def implementation_renderUpsertClause
    (uniqueFields updateFields : List FieldRef) : List Char := Id.run do
  let mut uniqueCols : List (List Char) := []
  for f in uniqueFields do
    uniqueCols := uniqueCols ++ [quoteName f.column]
  let mut assigns : List (List Char) := []
  for f in updateFields do
    assigns := assigns ++ [assignColumn f]
  return "ON CONFLICT(".toList ++ List.intercalate ", ".toList uniqueCols
    ++ ") DO UPDATE SET ".toList ++ List.intercalate ", ".toList assigns
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation loop `acc := acc ++ [g f]`, generalized
over the accumulator, computes `init ++ xs.map g`. -/
theorem foldMapHelper_renderUpsertClause
    (g : FieldRef → List Char) (xs : List FieldRef) (init : List (List Char)) :
    (forIn (m := Id) xs init (fun f acc => pure (ForInStep.yield (acc ++ [g f]))))
      = init ++ xs.map g := by
  induction xs generalizing init with
  | nil => simp only [List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_renderUpsertClause :
    ∀ (uniqueFields updateFields : List FieldRef),
    problem_spec_renderUpsertClause uniqueFields updateFields
      (implementation_renderUpsertClause uniqueFields updateFields) := by
  intro uf vf
  unfold problem_spec_renderUpsertClause implementation_renderUpsertClause
  simp only [Id.run, bind]
  rw [foldMapHelper_renderUpsertClause (fun f => quoteName f.column) uf [],
      foldMapHelper_renderUpsertClause assignColumn vf []]
  simp only [List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

R/I-only bundle: axioms=[], deep_model_references=[], opaque_callees=[]. The postcondition problem_spec_renderUpsertClause is a TOTAL FUNCTIONAL EQUALITY (result = exact expression, forall-quantified over both field lists), the strongest spec form. same_spec=True verified for all 7 attacks (impl region only edited; axioms/pure/pre/post byte-identical).

### ATTACK RESULTS (cmd: bash scripts/lean_verify.sh <file>; run concurrently <=4):
- atk_1.lean (prepatch bug: key by f.name on BOTH lists): exit=1 (rewrite failed, does NOT verify) -> prepatch reproduced.
- atk_2.lean (partial: unique by column, update by name): exit=1, does NOT verify.
- atk_3.lean (control-flow-effect: swap the two field lists): exit=1, does NOT verify.
- atk_4.lean (boundary: wrong separator ',' vs ', '): exit=1, does NOT verify.
- atk_5.lean (boundary: wrong template 'ON CONFLICT (' extra space): exit=1, does NOT verify.
- atk_6.lean (ungrounded-oracle echo: returns spec RHS verbatim, keyed by f.column): exit=0 VERIFIES; #print axioms correct_renderUpsertClause -> 'does not depend on any axioms' (clean). This is a GOLD-EQUIVALENT echo (functionally identical to gold, keys by f.column).
- atk_7.lean (partial-domain: echo when nonempty else [] on ([],[])): exit=1, does NOT verify (spec demands the framing template even for empty lists).

pos_control.lean (exact gold Solution.lean): exit=0 verifies; #print axioms -> [propext, Quot.sound] (standard, clean, from List.intercalate/Id.run).

RESOLVE (echo-attack policy): the only clean-axiom-closing impl, atk_6, is functionally equal to gold (keys by f.column), so its faithful refined patch IS the gold patch. Ran official harness: run_resolve('django__django-16315', gold_patch, timeout=1800, retries=1) -> RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1 (log: resolve_atk6.log). A resolving gold-equivalent echo is NOT a weakness (per 2026-08-06 resolved echo-attack policy).

A-LEG AUDIT: no A-consumed / A-reference legs to audit (axioms region empty, only a comment; no opaque/axiom/_prop declarations). refinement.md's 4 legs are R (str->FieldRef type refinement of get_field carrier) or I (quote_name and the ON CONFLICT(...) DO UPDATE SET template reproduced concretely) with zero kind-3/deep-model refs. No model<->real-callee correspondence gap: quote_name and the template are reproduced concretely rather than abstracted, so there is nothing an axiom could over-approximate. refinement.md legs are all R/I -> audit passes.

CONCLUSION: >=5 distinct wrong impls run; every genuinely-wrong impl (prepatch, partial, control-flow, 2x boundary, partial-domain) FAILS to verify. The single verifying impl is a gold-equivalent echo whose materialized faithful patch RESOLVES. No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found; spec is faithful to and not stronger than the real repo behavior.

Modeled function: OnConflict.UPDATE branch of on_conflict_suffix_sql fed the resolved field lists by patched compiler.py/bulk_create (base_commit 7d5329852f, verified).

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region (axioms/pure/post-conditions) byte-identical; only impl/proof differ.
2. Solution.lean compiles via lean_verify.sh (exit 0). #print axioms correct_renderUpsertClause => [propext, Quot.sound] only — NO sorryAx, proof is genuine.
3. Prepatch (keyed by f.name) FAILS G-VERIFY (exit 1) => spec is a genuine discriminator, not vacuously weak.
4. Real-callee equivalence at base_commit:
   - quoteName exhaustively equals sqlite/postgres quote_name (operations.py:187-190 sqlite; identical pg) over all identifier strings incl. empty, single '"', pre-quoted, embedded separators — 0 divergences.
   - assignColumn (q ++ ' = EXCLUDED.' ++ q) matches f'{field} = EXCLUDED.{field}'.
   - List.intercalate ', ' matches ', '.join; template 'ON CONFLICT(%s) DO UPDATE SET %s' matches verbatim (sqlite operations.py:415-428, identical postgres 352-364).
   - R-refinement: keying by .column is exactly what patched compiler.py passes ((f.column for f in self.query.{update,unique}_fields)); get_field is the unchanged callee correctly carried as the FieldRef carrier, not axiomatized (axioms region empty).
5. conformance_check.py: 120,004 fuzzed inputs (seed 16315, column==name and column!=name, mixed case, pre-quoted, 0-6 fields), 0 disagreements. Plus independent edge-case differential (empty lists, single-quote, pre-quoted, embedded ', 2x2) — 0 divergences.

Scope is correct: only the UPDATE branch is modeled (the branch the F2P test and issue exercise); IGNORE and None branches render no fields and are orthogonal to the column-vs-name fix. The spec pins each rendered slot element-wise, so it is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical (markers.same_spec = True; Solution vs Solution_prepatch spec views identical). Mechanical G-LEAK screen (leakage.screen, lean flavor) PASSES with zero hard failures: no diff markers, no gold-patch line reproduced, no patched file path/module, no spec-view identifier embedding a patched repo symbol (changed symbols = as_sql, bulk_create, check_bulk_create_options — none appear in the view), no narration terms. Semantic check: the public problem_statement is highly explicit — it states the ON CONFLICT clause 'uses the field name and not the db_column which leads to a syntax error', shows the wrong output ON CONFLICT("blacklistid"), and states 'What should be generated is ... ON CONFLICT("BlacklistID")' (the db_column). Thus the entire behavioral requirement (key the upsert suffix by each field's database column, not its declared name) is already fully public. The spec view's post-condition ('both keyed by each field's database column (never its declared name)') and the FieldRef structure with name/column merely restate that public requirement; they do not reveal the gold edit's location (query.py / compiler.py, get_field relocation, (f.column for f in ...)) beyond the problem statement. Identifiers are abstract (FieldRef, quoteName, assignColumn, renderUpsertClause). No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
