import Mathlib
-- imports-end

/-!
Enumerating the contents of a test package.

A test package is a directory carrying an initialization file. Enumerating the
package's contents walks the directory tree and produces the child collectors it
contains:

* if the package's own initialization file matches the configured test-file
  pattern, a collector for that file is produced first;
* then, for every visited path, the path is examined: paths belonging to the
  package's own enumeration boundary (its own initialization file, or paths that
  already sit inside a nested sub-package that has been accounted for) contribute
  nothing, and every other regular file contributes whatever child collectors it
  resolves to.

Enumerating the package's contents is a directory-structure operation: it
inspects paths and builds collectors lazily. It must therefore NOT import the
package's own initialization file as a side effect — importing it is the job of
the produced collectors when (and if) they are later realized, not of the
enumeration itself. Importing an arbitrary package's initialization file merely
because its directory is being scanned would run that file's top-level code
prematurely.

The values modeled here are: the sequence of child collectors produced, and
whether enumerating the package imported the package's own initialization file.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-path
-- resolution of a regular file to its child collectors is an orthogonal,
-- unchanged operation whose result enters as plain input data (the `yields`
-- field of each enumerated entry); likewise whether a path lies on the package's
-- own enumeration boundary enters as a plain Boolean observation. No
-- `opaque`/`axiom` callee contract is therefore needed.
-- axioms-end

-- pure-start
/-- One enumerated path of the package directory, reduced to what content
enumeration consumes:

* `boundary` — the path contributes nothing to this package's own enumeration
  (it is the package's own initialization file, or it already sits inside a
  nested sub-package that has been accounted for);
* `isFile` — the path is a regular file (as opposed to a directory);
* `yields` — the child collectors a non-boundary regular file resolves to. -/
structure PkgEntry (α : Type) where
  boundary : Bool
  isFile : Bool
  yields : List α

/-- The child collectors produced by walking the enumerated paths, front
recursively: a boundary path or a directory contributes nothing; a non-boundary
regular file contributes its resolved collectors. -/
def walkEntries {α : Type} : List (PkgEntry α) → List α
  | [] => []
  | e :: es =>
    (if e.boundary || !e.isFile then [] else e.yields) ++ walkEntries es
-- pure-end

-- post-conditions-start
/-- Enumerating a package's contents:

* produces, in order, the collector for the package's own initialization file
  when it matches the configured test-file pattern (`initMatches`), followed by
  the child collectors of every non-boundary regular file enumerated; and
* does NOT import the package's own initialization file (`result.2 = false`):
  enumeration is a directory-structure operation with no such side effect.

Both output components are pinned to the inputs: the produced sequence is the
exact walk of the enumerated paths, and the import flag is unconditionally
absent. -/
def problem_spec_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α))
    (result : List α × Bool) : Prop :=
  result.2 = false ∧
  result.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
-- post-conditions-end

-- impl-start
def implementation_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
    List α × Bool := Id.run do
  -- Enumeration walks the directory structure only; it never imports the
  -- package's own initialization file.
  let importsOwnInit := false
  let mut collected : List α := []
  if initMatches then
    collected := collected ++ [initNode]
  for e in entries do
    if e.boundary then
      -- the path is on this package's enumeration boundary: contribute nothing
      continue
    if e.isFile then
      collected := collected ++ e.yields
  return (collected, importsOwnInit)
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop accumulating child collectors equals the prefix
`init` followed by `walkEntries`, generalized over the accumulator. -/
private theorem packageCollect_forIn {α : Type}
    (entries : List (PkgEntry α)) (init : List α) :
    Id.run (forIn entries init (fun e r =>
        if e.boundary = true then ForInStep.yield r
        else if e.isFile = true then ForInStep.yield (r ++ e.yields)
        else ForInStep.yield r))
      = init ++ walkEntries entries := by
  induction entries generalizing init with
  | nil => simp [walkEntries, Id.run, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases hb : a.boundary = true
    · simp only [hb, if_true, ih, walkEntries]
      simp
    · by_cases hf : a.isFile = true
      · simp only [hb, hf, if_true, ih, walkEntries]
        simp [List.append_assoc]
      · simp only [hb, hf, ih, walkEntries]
        simp

theorem correct_packageCollect {α : Type}
    (initMatches : Bool) (initNode : α) (entries : List (PkgEntry α)) :
    problem_spec_packageCollect initMatches initNode entries
      (implementation_packageCollect initMatches initNode entries) := by
  unfold problem_spec_packageCollect implementation_packageCollect
  simp only [Id.run, bind, pure]
  have hh := packageCollect_forIn entries
  simp only [Id.run] at hh
  refine ⟨?_, ?_⟩
  · split <;> rfl
  · split <;> simp [hh]
-- proof-end
