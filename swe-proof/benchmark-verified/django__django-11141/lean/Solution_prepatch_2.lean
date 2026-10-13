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
  if !hasPath then
    return { migrated := false, names := [] }
  let mut names : List String := []
  for entry in entries do
    if (!entry.2) && validMigrationName entry.1 then
      names := names ++ [entry.1]
  -- BUG (behavior B): a package is unconditionally classified migrated, even
  -- when no migration files were discovered and the flag is not set.
  return { migrated := true, names := names }
-- impl-end

-- proof-start
theorem correct_migration_module_status :
    ∀ (hasFile hasPath ignoreNoMigrations : Bool) (entries : List (String × Bool)),
      problem_spec_migration_module_status hasFile hasPath ignoreNoMigrations entries
        (implementation_migration_module_status hasFile hasPath ignoreNoMigrations entries) := by
  sorry
-- proof-end
