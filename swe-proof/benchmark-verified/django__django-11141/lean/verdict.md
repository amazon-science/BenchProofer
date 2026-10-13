# P2 adversarial audit — django__django-11141

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,8 +73,10 @@
 def implementation_migration_module_status
     (hasFile hasPath ignoreNoMigrations : Bool)
     (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do
-  -- The package flavour (`hasFile`) is deliberately not consulted.
   if !hasPath then
+    return { migrated := false, names := [] }
+  -- WRONG (prepatch behavior A): reject packages lacking a __file__ attribute.
+  if !hasFile then
     return { migrated := false, names := [] }
   let mut names : List String := []
   for entry in entries do
@@ -123,5 +125,4 @@
       Bool.false_eq_true, if_false, bind_pure_comp, map_pure, pure_bind]
     rw [key []]
     exact ⟨rfl, rfl⟩
-
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,15 +73,14 @@
 def implementation_migration_module_status
     (hasFile hasPath ignoreNoMigrations : Bool)
     (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do
-  -- The package flavour (`hasFile`) is deliberately not consulted.
   if !hasPath then
     return { migrated := false, names := [] }
   let mut names : List String := []
   for entry in entries do
     if (!entry.2) && validMigrationName entry.1 then
       names := names ++ [entry.1]
-  let migrated := (!names.isEmpty) || ignoreNoMigrations
-  return { migrated := migrated, names := names }
+  -- WRONG (prepatch behavior B): always migrated, ignoring empty+flag case.
+  return { migrated := true, names := names }
 -- impl-end
 
 
@@ -123,5 +122,4 @@
       Bool.false_eq_true, if_false, bind_pure_comp, map_pure, pure_bind]
     rw [key []]
     exact ⟨rfl, rfl⟩
-
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,14 +73,14 @@
 def implementation_migration_module_status
     (hasFile hasPath ignoreNoMigrations : Bool)
     (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do
-  -- The package flavour (`hasFile`) is deliberately not consulted.
   if !hasPath then
     return { migrated := false, names := [] }
   let mut names : List String := []
   for entry in entries do
     if (!entry.2) && validMigrationName entry.1 then
       names := names ++ [entry.1]
-  let migrated := (!names.isEmpty) || ignoreNoMigrations
+  -- WRONG: conjunction instead of disjunction for the flag.
+  let migrated := (!names.isEmpty) && ignoreNoMigrations
   return { migrated := migrated, names := names }
 -- impl-end
 
@@ -123,5 +123,4 @@
       Bool.false_eq_true, if_false, bind_pure_comp, map_pure, pure_bind]
     rw [key []]
     exact ⟨rfl, rfl⟩
-
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,13 +73,13 @@
 def implementation_migration_module_status
     (hasFile hasPath ignoreNoMigrations : Bool)
     (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do
-  -- The package flavour (`hasFile`) is deliberately not consulted.
   if !hasPath then
     return { migrated := false, names := [] }
   let mut names : List String := []
   for entry in entries do
     if (!entry.2) && validMigrationName entry.1 then
-      names := names ++ [entry.1]
+      -- WRONG: prepend, so names comes out reversed vs filteredNames.
+      names := entry.1 :: names
   let migrated := (!names.isEmpty) || ignoreNoMigrations
   return { migrated := migrated, names := names }
 -- impl-end
@@ -123,5 +123,4 @@
       Bool.false_eq_true, if_false, bind_pure_comp, map_pure, pure_bind]
     rw [key []]
     exact ⟨rfl, rfl⟩
-
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,12 +73,12 @@
 def implementation_migration_module_status
     (hasFile hasPath ignoreNoMigrations : Bool)
     (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do
-  -- The package flavour (`hasFile`) is deliberately not consulted.
   if !hasPath then
     return { migrated := false, names := [] }
   let mut names : List String := []
   for entry in entries do
-    if (!entry.2) && validMigrationName entry.1 then
+    -- WRONG: subpackage entries are no longer excluded.
+    if validMigrationName entry.1 then
       names := names ++ [entry.1]
   let migrated := (!names.isEmpty) || ignoreNoMigrations
   return { migrated := migrated, names := names }
@@ -123,5 +123,4 @@
       Bool.false_eq_true, if_false, bind_pure_comp, map_pure, pure_bind]
     rw [key []]
     exact ⟨rfl, rfl⟩
-
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -72,16 +72,12 @@
 -- impl-start
 def implementation_migration_module_status
     (hasFile hasPath ignoreNoMigrations : Bool)
-    (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do
-  -- The package flavour (`hasFile`) is deliberately not consulted.
-  if !hasPath then
-    return { migrated := false, names := [] }
-  let mut names : List String := []
-  for entry in entries do
-    if (!entry.2) && validMigrationName entry.1 then
-      names := names ++ [entry.1]
-  let migrated := (!names.isEmpty) || ignoreNoMigrations
-  return { migrated := migrated, names := names }
+    (entries : List (String × Bool)) : MigrationModuleStatus :=
+  if hasPath then
+    let names := filteredNames entries
+    { migrated := (! names.isEmpty) || ignoreNoMigrations, names := names }
+  else
+    { migrated := false, names := [] }
 -- impl-end
 
 
@@ -93,35 +89,5 @@
   intro hasFile hasPath ignoreNoMigrations entries
   refine ⟨fun hp => ?_, fun hp => ?_⟩
   · simp [implementation_migration_module_status, hp]
-  · have key : ∀ (acc : List String),
-        (forIn entries acc (fun entry r =>
-          if (!entry.2 && validMigrationName entry.1) = true then
-            pure (ForInStep.yield (r ++ [entry.1]))
-          else pure (ForInStep.yield r)) : Id (List String))
-          = acc ++ filteredNames entries := by
-      intro acc
-      have hbody : (fun (entry : String × Bool) (r : List String) =>
-          if (!entry.2 && validMigrationName entry.1) = true then
-            (pure (ForInStep.yield (r ++ [entry.1])) : Id _)
-          else pure (ForInStep.yield r))
-          = (fun entry r => ForInStep.yield (if (!entry.2 && validMigrationName entry.1) = true then r ++ [entry.1] else r)) := by
-        funext entry r
-        by_cases hc : (!entry.2 && validMigrationName entry.1) = true <;> simp [hc] <;> rfl
-      rw [hbody, List.forIn_yield_eq_foldl]
-      induction entries generalizing acc with
-      | nil => simp [filteredNames]
-      | cons hd tl ih =>
-        simp only [List.foldl_cons, filteredNames, List.filter_cons]
-        by_cases hc : (!hd.2 && validMigrationName hd.1) = true
-        · simp only [hc, if_true, List.map_cons]
-          rw [ih (acc ++ [hd.1])]
-          simp [filteredNames]
-        · simp only [hc, Bool.false_eq_true, if_false]
-          rw [ih acc]
-          simp [filteredNames]
-    simp only [implementation_migration_module_status, hp, Id.run, Bool.not_true,
-      Bool.false_eq_true, if_false, bind_pure_comp, map_pure, pure_bind]
-    rw [key []]
-    exact ⟨rfl, rfl⟩
-
+  · simp [implementation_migration_module_status, hp]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Classifying an application's migrations package as *migrated* (it participates
in the migration graph) or *unmigrated*, and reporting the migration files
discovered in it.

The package has already been imported successfully. Two boolean facts about it
are available: whether it is a package at all (it exposes a search path), and a
flag requesting that a package with no migration files still be treated as
migrated. The discovered entries are a list of `(name, isSubpackage)` pairs;
a migration file is an entry that is not itself a subpackage and whose name does
not begin with `_` or `~`.

A package directory may be an ordinary package or an implicit namespace package
(a directory without an `__init__.py`); both expose a search path and must be
treated the same way. Classification depends ONLY on whether any migration file
was discovered (or the flag is set), never on the package's flavour.

Inputs are modeled as `List Char`-free booleans and a `List (String × Bool)`;
the result carries the classification and the discovered file names.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the module-discovery output is
-- taken as the input `entries`, and the file-name filtering + classification
-- are modeled deeply.
-- axioms-end

-- pure-start
/-- A discovered entry is a migration file iff it is not a subpackage and its
name does not begin with `_` or `~`. -/
def validMigrationName (name : String) : Bool :=
  match name.toList with
  | [] => false
  | c :: _ => (c != '_') && (c != '~')

/-- The migration file names discovered among `entries`, in order: non-subpackage
entries with an admissible name. -/
def filteredNames (entries : List (String × Bool)) : List String :=
  (entries.filter (fun p => (!p.2) && validMigrationName p.1)).map Prod.fst

/-- The classification of an application's migrations package. -/
structure MigrationModuleStatus where
  migrated : Bool
  names : List String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Specification of the classification.

* If the imported module is not a package (no search path), it is unmigrated and
  contributes no files.
* Otherwise the discovered files are exactly `filteredNames entries`, and the
  package is migrated iff at least one file was discovered or the
  treat-as-migrated flag is set.

The flavour flag `hasFile` does NOT appear on the right-hand side: the
classification is independent of it. -/
def problem_spec_migration_module_status
    (hasFile hasPath ignoreNoMigrations : Bool)
    (entries : List (String × Bool))
    (result : MigrationModuleStatus) : Prop :=
  (hasPath = false → result.migrated = false ∧ result.names = []) ∧
  (hasPath = true →
     result.names = filteredNames entries ∧
     result.migrated = ((! (filteredNames entries).isEmpty) || ignoreNoMigrations))
-- post-conditions-end

-- impl-start
def implementation_migration_module_status
    (hasFile hasPath ignoreNoMigrations : Bool)
    (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do
  -- The package flavour (`hasFile`) is deliberately not consulted.
  if !hasPath then
    return { migrated := false, names := [] }
  let mut names : List String := []
  for entry in entries do
    if (!entry.2) && validMigrationName entry.1 then
      names := names ++ [entry.1]
  let migrated := (!names.isEmpty) || ignoreNoMigrations
  return { migrated := migrated, names := names }
-- impl-end


-- proof-start
theorem correct_migration_module_status :
    ∀ (hasFile hasPath ignoreNoMigrations : Bool) (entries : List (String × Bool)),
      problem_spec_migration_module_status hasFile hasPath ignoreNoMigrations entries
        (implementation_migration_module_status hasFile hasPath ignoreNoMigrations entries) := by
  intro hasFile hasPath ignoreNoMigrations entries
  refine ⟨fun hp => ?_, fun hp => ?_⟩
  · simp [implementation_migration_module_status, hp]
  · have key : ∀ (acc : List String),
        (forIn entries acc (fun entry r =>
          if (!entry.2 && validMigrationName entry.1) = true then
            pure (ForInStep.yield (r ++ [entry.1]))
          else pure (ForInStep.yield r)) : Id (List String))
          = acc ++ filteredNames entries := by
      intro acc
      have hbody : (fun (entry : String × Bool) (r : List String) =>
          if (!entry.2 && validMigrationName entry.1) = true then
            (pure (ForInStep.yield (r ++ [entry.1])) : Id _)
          else pure (ForInStep.yield r))
          = (fun entry r => ForInStep.yield (if (!entry.2 && validMigrationName entry.1) = true then r ++ [entry.1] else r)) := by
        funext entry r
        by_cases hc : (!entry.2 && validMigrationName entry.1) = true <;> simp [hc] <;> rfl
      rw [hbody, List.forIn_yield_eq_foldl]
      induction entries generalizing acc with
      | nil => simp [filteredNames]
      | cons hd tl ih =>
        simp only [List.foldl_cons, filteredNames, List.filter_cons]
        by_cases hc : (!hd.2 && validMigrationName hd.1) = true
        · simp only [hc, if_true, List.map_cons]
          rw [ih (acc ++ [hd.1])]
          simp [filteredNames]
        · simp only [hc, Bool.false_eq_true, if_false]
          rw [ih acc]
          simp [filteredNames]
    simp only [implementation_migration_module_status, hp, Id.run, Bool.not_true,
      Bool.false_eq_true, if_false, bind_pure_comp, map_pure, pure_bind]
    rw [key []]
    exact ⟨rfl, rfl⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TIGHT. The postcondition problem_spec_migration_module_status is TOTAL and fully DETERMINISTIC: for hasPath=false it pins result.migrated=false ∧ result.names=[]; for hasPath=true it pins result.names = filteredNames entries (exact ordered list) AND result.migrated = ((! (filteredNames entries).isEmpty) || ignoreNoMigrations). hasFile never appears on the RHS (frame directive: correct_* quantifies over all hasFile). Zero extensional freedom => every verifying impl is forced output-identical to the reference over the whole modeled domain.

same_spec: all 6 attacks True (spec/axioms/pure/pre/post regions byte-identical; only impl+proof edited).

### ATTACKS (all run via `bash scripts/lean_verify.sh <file>`):
- atk_1 (partial-domain / prepatch behavior-A bug): re-adds the removed `if !hasFile` gate. lean_verify exit=1 (error at proof line 127: `(if !hasFile ...).migrated = ...` cannot be closed by rfl since hasFile-dependent branch is not the RHS). Correctly UNPROVABLE. Faithfully reproduces Solution_prepatch.lean bug.
- atk_2 (boundary / prepatch behavior-B bug): migrated := true unconditionally. exit=1 (error line 124: `true = (! isEmpty || ino)` unprovable when empty & !ino). Reproduces Solution_prepatch_2.lean bug.
- atk_3 (control-flow/logic effect): migrated := (!names.isEmpty) && ino instead of ||. exit=1 (error line 125, && ≠ ||). Correctly UNPROVABLE.
- atk_4 (ordering effect / ungrounded vs order-sensitive spec): names built by prepend (entry.1 :: names) => reversed. exit=1 (rewrite fails; result.names would be reverse of filteredNames, spec pins exact order). Correctly UNPROVABLE — note the Lean names clause is ORDER-sensitive and catches this even though G-CONF compares as a set.
- atk_5 (ungrounded-oracle / wrong filter): drops the `!entry.2` subpackage guard, so subpackages with valid names leak into names. exit=1. Correctly UNPROVABLE (e.g. entries=[("x",true)]: filteredNames=[] but impl yields ["x"]).
- atk_6 (equivalent 'echo' control): non-monadic reformulation computing exactly `if hasPath then {(!filteredNames.isEmpty||ino), filteredNames} else {false,[]}`. lean_verify exit=0, #print axioms => `[propext]` only (clean, no sorryAx/Classical). This is the ONLY attack that closes. Per protocol I materialized its faithful refined patch. Because atk_6 is extensionally identical to the gold implementation (satisfies the same total spec), its faithful patch IS the gold patch (meta.patch_equals_gold=True). That patch RESOLVES: meta.json G-RESOLVE status=pass, resolved=true, attempts=1, non-flaky. So the one verifying clean-axiom impl has a materialized faithful patch that DOES resolve => no verify⇏correct break.

Positive control (pos_control.lean = bundle Solution.lean): lean_verify exit=0.

REFINEMENT.MD AUDIT: 5 legs, all tagged R or R/I; zero A-consumed, zero A-reference, no kind-3 legs. Consistent with axiom_check.py being a skip stub and meta.json axioms/deep_model_references both empty. No A-legs => no deep-model↔callee correspondence to falsify. mapping.md confirms iter_modules output is taken as input `entries` (not axiomatized). Both patch behaviors (A: __file__ gate removed; B: empty+no-flag => unmigrated) are modeled deeply and each is independently defended by a failing prepatch twin (reproduced as atk_1/atk_2).

VERDICT: SOUND. 6 same-spec attacks run; 5 genuinely-wrong impls all fail to verify (exit 1, real elaboration/proof errors, not timeouts); the sole verifying clean-axiom impl is behaviorally gold-equivalent and its faithful (=gold) patch resolves. No counterexample to verify⇒correct found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Classifying an application's migrations package as *migrated* (it participates
in the migration graph) or *unmigrated*, and reporting the migration files
discovered in it.

The package has already been imported successfully. Two boolean facts about it
are available: whether it is a package at all (it exposes a search path), and a
flag requesting that a package with no migration files still be treated as
migrated. The discovered entries are a list of `(name, isSubpackage)` pairs;
a migration file is an entry that is not itself a subpackage and whose name does
not begin with `_` or `~`.

A package directory may be an ordinary package or an implicit namespace package
(a directory without an `__init__.py`); both expose a search path and must be
treated the same way. Classification depends ONLY on whether any migration file
was discovered (or the flag is set), never on the package's flavour.

Inputs are modeled as `List Char`-free booleans and a `List (String × Bool)`;
the result carries the classification and the discovered file names.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the module-discovery output is
-- taken as the input `entries`, and the file-name filtering + classification
-- are modeled deeply.
-- axioms-end

-- pure-start
/-- A discovered entry is a migration file iff it is not a subpackage and its
name does not begin with `_` or `~`. -/
def validMigrationName (name : String) : Bool :=
  match name.toList with
  | [] => false
  | c :: _ => (c != '_') && (c != '~')

/-- The migration file names discovered among `entries`, in order: non-subpackage
entries with an admissible name. -/
def filteredNames (entries : List (String × Bool)) : List String :=
  (entries.filter (fun p => (!p.2) && validMigrationName p.1)).map Prod.fst

/-- The classification of an application's migrations package. -/
structure MigrationModuleStatus where
  migrated : Bool
  names : List String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Specification of the classification.

* If the imported module is not a package (no search path), it is unmigrated and
  contributes no files.
* Otherwise the discovered files are exactly `filteredNames entries`, and the
  package is migrated iff at least one file was discovered or the
  treat-as-migrated flag is set.

The flavour flag `hasFile` does NOT appear on the right-hand side: the
classification is independent of it. -/
def problem_spec_migration_module_status
    (hasFile hasPath ignoreNoMigrations : Bool)
    (entries : List (String × Bool))
    (result : MigrationModuleStatus) : Prop :=
  (hasPath = false → result.migrated = false ∧ result.names = []) ∧
  (hasPath = true →
     result.names = filteredNames entries ∧
     result.migrated = ((! (filteredNames entries).isEmpty) || ignoreNoMigrations))
-- post-conditions-end

-- impl-start
def implementation_migration_module_status
    (hasFile hasPath ignoreNoMigrations : Bool)
    (entries : List (String × Bool)) : MigrationModuleStatus := Id.run do
  -- The package flavour (`hasFile`) is deliberately not consulted.
  if !hasPath then
    return { migrated := false, names := [] }
  let mut names : List String := []
  for entry in entries do
    if (!entry.2) && validMigrationName entry.1 then
      names := names ++ [entry.1]
  let migrated := (!names.isEmpty) || ignoreNoMigrations
  return { migrated := migrated, names := names }
-- impl-end


-- proof-start
theorem correct_migration_module_status :
    ∀ (hasFile hasPath ignoreNoMigrations : Bool) (entries : List (String × Bool)),
      problem_spec_migration_module_status hasFile hasPath ignoreNoMigrations entries
        (implementation_migration_module_status hasFile hasPath ignoreNoMigrations entries) := by
  intro hasFile hasPath ignoreNoMigrations entries
  refine ⟨fun hp => ?_, fun hp => ?_⟩
  · simp [implementation_migration_module_status, hp]
  · have key : ∀ (acc : List String),
        (forIn entries acc (fun entry r =>
          if (!entry.2 && validMigrationName entry.1) = true then
            pure (ForInStep.yield (r ++ [entry.1]))
          else pure (ForInStep.yield r)) : Id (List String))
          = acc ++ filteredNames entries := by
      intro acc
      have hbody : (fun (entry : String × Bool) (r : List String) =>
          if (!entry.2 && validMigrationName entry.1) = true then
            (pure (ForInStep.yield (r ++ [entry.1])) : Id _)
          else pure (ForInStep.yield r))
          = (fun entry r => ForInStep.yield (if (!entry.2 && validMigrationName entry.1) = true then r ++ [entry.1] else r)) := by
        funext entry r
        by_cases hc : (!entry.2 && validMigrationName entry.1) = true <;> simp [hc] <;> rfl
      rw [hbody, List.forIn_yield_eq_foldl]
      induction entries generalizing acc with
      | nil => simp [filteredNames]
      | cons hd tl ih =>
        simp only [List.foldl_cons, filteredNames, List.filter_cons]
        by_cases hc : (!hd.2 && validMigrationName hd.1) = true
        · simp only [hc, if_true, List.map_cons]
          rw [ih (acc ++ [hd.1])]
          simp [filteredNames]
        · simp only [hc, Bool.false_eq_true, if_false]
          rw [ih acc]
          simp [filteredNames]
    simp only [implementation_migration_module_status, hp, Id.run, Bool.not_true,
      Bool.false_eq_true, if_false, bind_pure_comp, map_pure, pure_bind]
    rw [key []]
    exact ⟨rfl, rfl⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS TIGHT. The postcondition problem_spec_migration_module_status is TOTAL and fully DETERMINISTIC: for hasPath=false it pins result.migrated=false ∧ result.names=[]; for hasPath=true it pins result.names = filteredNames entries (exact ordered list) AND result.migrated = ((! (filteredNames entries).isEmpty) || ignoreNoMigrations). hasFile never appears on the RHS (frame directive: correct_* quantifies over all hasFile). Zero extensional freedom => every verifying impl is forced output-identical to the reference over the whole modeled domain.

same_spec: all 6 attacks True (spec/axioms/pure/pre/post regions byte-identical; only impl+proof edited).

### ATTACKS (all run via `bash scripts/lean_verify.sh <file>`):
- atk_1 (partial-domain / prepatch behavior-A bug): re-adds the removed `if !hasFile` gate. lean_verify exit=1 (error at proof line 127: `(if !hasFile ...).migrated = ...` cannot be closed by rfl since hasFile-dependent branch is not the RHS). Correctly UNPROVABLE. Faithfully reproduces Solution_prepatch.lean bug.
- atk_2 (boundary / prepatch behavior-B bug): migrated := true unconditionally. exit=1 (error line 124: `true = (! isEmpty || ino)` unprovable when empty & !ino). Reproduces Solution_prepatch_2.lean bug.
- atk_3 (control-flow/logic effect): migrated := (!names.isEmpty) && ino instead of ||. exit=1 (error line 125, && ≠ ||). Correctly UNPROVABLE.
- atk_4 (ordering effect / ungrounded vs order-sensitive spec): names built by prepend (entry.1 :: names) => reversed. exit=1 (rewrite fails; result.names would be reverse of filteredNames, spec pins exact order). Correctly UNPROVABLE — note the Lean names clause is ORDER-sensitive and catches this even though G-CONF compares as a set.
- atk_5 (ungrounded-oracle / wrong filter): drops the `!entry.2` subpackage guard, so subpackages with valid names leak into names. exit=1. Correctly UNPROVABLE (e.g. entries=[("x",true)]: filteredNames=[] but impl yields ["x"]).
- atk_6 (equivalent 'echo' control): non-monadic reformulation computing exactly `if hasPath then {(!filteredNames.isEmpty||ino), filteredNames} else {false,[]}`. lean_verify exit=0, #print axioms => `[propext]` only (clean, no sorryAx/Classical). This is the ONLY attack that closes. Per protocol I materialized its faithful refined patch. Because atk_6 is extensionally identical to the gold implementation (satisfies the same total spec), its faithful patch IS the gold patch (meta.patch_equals_gold=True). That patch RESOLVES: meta.json G-RESOLVE status=pass, resolved=true, attempts=1, non-flaky. So the one verifying clean-axiom impl has a materialized faithful patch that DOES resolve => no verify⇏correct break.

Positive control (pos_control.lean = bundle Solution.lean): lean_verify exit=0.

REFINEMENT.MD AUDIT: 5 legs, all tagged R or R/I; zero A-consumed, zero A-reference, no kind-3 legs. Consistent with axiom_check.py being a skip stub and meta.json axioms/deep_model_references both empty. No A-legs => no deep-model↔callee correspondence to falsify. mapping.md confirms iter_modules output is taken as input `entries` (not axiomatized). Both patch behaviors (A: __file__ gate removed; B: empty+no-flag => unmigrated) are modeled deeply and each is independently defended by a failing prepatch twin (reproduced as atk_1/atk_2).

VERDICT: SOUND. 6 same-spec attacks run; 5 genuinely-wrong impls all fail to verify (exit 1, real elaboration/proof errors, not timeouts); the sole verifying clean-axiom impl is behaviorally gold-equivalent and its faithful (=gold) patch resolves. No counterexample to verify⇒correct found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of the modeled per-app success branch of MigrationLoader.load_disk (django/db/migrations/loader.py, base 5d9cf79b + gold patch). No input found where the modeled function disagrees with the real patched callee.

Evidence:
1) Solution.lean compiles via lean_verify.sh (exit 0, no sorry); `#print axioms correct_migration_module_status` = [propext, Quot.sound] only — no sorryAx, proof genuine.
2) Spec encodes exactly the patch's two behavioral changes: (A) removal of the `getattr(module,'__file__',None) is None` gate — namespace packages (hasFile=false) now reach discovery; (B) `if migration_names or self.ignore_no_migrations` — a path-exposing but empty package with no flag is classified unmigrated, not migrated. Verified against the actual patched source.
3) conformance_check.py run against a fresh worktree with the gold patch applied (confirmed loader.__file__ points to the worktree and the __file__ gate is gone): 100000 fuzzed inputs, 0 disagreements.
4) 10 deterministic adversarial edge cases (empty entries; only `_`/`~`/single-char names; subpackage-only; duplicate names; hasPath=false∧ino=true; namespace-pkg hasFile=false with a valid file; mixed) all agree with the real oracle.

Probed and dismissed drift: Lean filteredNames returns a List (retains duplicates) whereas the repo builds a set. Not a real divergence — mapping.md binds result.names AS A SET (compared duplicate/order-independently) and pkgutil.iter_modules never yields duplicate module names in the real domain. hasFile is an input that correctly does not appear on the postcondition RHS, matching the fix making classification independent of __file__. Empty module name is outside iter_modules' domain and the total Lean model still handles it (validMigrationName "" = false).

The spec is neither too strong nor too weak relative to real behavior; it is faithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region markers byte-identical (same_spec=True vs both prepatch variants; markers gate clean). Mechanical leak.screen passes (hard_failures=[]). Semantic gold-reconstruction review of the full spec view (docstring L4-23, axioms comment L25-29, pure defs L31-49, postcondition L51-70):

Gold edit = two behaviors: (A) remove the getattr(module,'__file__',None) is None gate so namespace packages reach discovery; (B) reclassify a no-files/no-flag package as unmigrated instead of unconditionally migrated.

Behavior A is FULLY disclosed by the public problem_statement (namespace packages have no __file__, the __file__ check is no longer needed and prevents migrate, discovery uses pkgutil.iter_modules over __path__). The docstring's restatement (L16-19, L60-61) therefore leaks nothing beyond public text.

Behavior B is NOT in problem_statement, and the postcondition (L69: migrated = ((!filteredNames.isEmpty) || ignoreNoMigrations)) encodes it. But this is a description of correct post-patch behavior expressed as an abstract boolean formula over inputs — the specification's job, and required for a faithful spec (G-PANEL-2). It does not disclose the gold EDIT: no diff hunks, no file paths, no line-level before/after shape, no 'previously always migrated' framing. The Lean symbol migration_module_status is de-narrated (does not echo load_disk). No spec-view comment references the patch or uses handover prose. A solver must still derive the implementation and proof.

Matches the accepted G-PANEL-3 standard: postcondition describing intended behavior is not a leak of the gold patch. Bundle is not relaxed (no RELAXED_LEAKAGE.md path triggered).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
