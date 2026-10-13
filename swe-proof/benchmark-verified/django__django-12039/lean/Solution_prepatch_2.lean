import Mathlib
-- imports-end

/-!
Rendering a comma-separated list of column references for a database DDL
statement.

Each entry in the list is built from a column name and an optional rendering
hint supplied positionally. A name-quoting function turns a raw column name into
its quoted, statement-ready form. Two flavours of list are rendered:

* a plain list, where each entry is the quoted column name, optionally followed
  by a positional hint;
* an operator-annotated list, where each entry is the quoted column name
  followed by a mandatory per-column annotation, then optionally the positional
  hint.

The positional hints are addressed by entry position; a position with no hint
(out of range) contributes nothing. The required separation rule is: a hint is
appended only when it is a non-empty token, and when appended it is set off from
what precedes it by a single space. In particular an empty hint must leave the
entry unchanged — it contributes neither a token nor a stray separating space.
Entries are then joined with `", "`.
-/

-- axioms-start
-- The name-quoting operation is an UNCHANGED collaborator supplied by the
-- caller. It is modeled as an arbitrary function `quoteName : String → String`
-- and universally quantified in the correctness statement, so the contract
-- holds for every possible quoting behavior; no `opaque`/`axiom` callee
-- contract is required. The rendering rule itself (the separation/empty-hint
-- behavior the specification pins) is modeled DEEPLY below, not axiomatized.
-- axioms-end

-- pure-start
/-- Append a positional hint to an already-rendered entry `col`.

The hint for this entry is looked up positionally; a missing (out-of-range)
position leaves the entry untouched. A present but empty hint is also dropped.
A present, non-empty hint is appended preceded by exactly one space. -/
def appendSuffix (col : String) (suffixes : List String) (idx : Nat) : String :=
  match suffixes[idx]? with
  | some suffix => if suffix ≠ "" then col ++ " " ++ suffix else col
  | none => col

/-- Render the plain column list: each quoted column name, optionally followed
by its positional hint, joined with `", "`. -/
def renderColumns (quoteName : String → String)
    (columns suffixes : List String) : String :=
  String.intercalate ", "
    (columns.zipIdx.map (fun p => appendSuffix (quoteName p.1) suffixes p.2))

/-- Render the operator-annotated column list: each quoted column name followed
by its mandatory per-column annotation (separated by a space), then optionally
its positional hint, joined with `", "`. A missing annotation position
contributes the empty token. -/
def renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) : String :=
  String.intercalate ", "
    (columns.zipIdx.map (fun p =>
      appendSuffix (quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")) suffixes p.2))
-- pure-end

-- post-conditions-start
/-- The plain rendering equals the entry-wise, positionally-hinted, space-set
join described by `renderColumns`. -/
def problem_spec_renderColumns (quoteName : String → String)
    (columns suffixes : List String) (result : String) : Prop :=
  result = renderColumns quoteName columns suffixes
-- post-conditions-end

-- impl-start
def implementation_renderColumns (quoteName : String → String)
    (columns suffixes : List String) : String :=
  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
    let mut col := quoteName p.1
    match suffixes[p.2]? with
    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
    | none => pure ()
    return col))
-- impl-end

-- proof-start
theorem correct_renderColumns :
    ∀ (quoteName : String → String) (columns suffixes : List String),
      problem_spec_renderColumns quoteName columns suffixes
        (implementation_renderColumns quoteName columns suffixes) := by
  intro quoteName columns suffixes
  unfold problem_spec_renderColumns implementation_renderColumns renderColumns appendSuffix
  rfl
-- proof-end

-- post-conditions-start
/-- The operator-annotated rendering equals the entry-wise, positionally-hinted,
space-set join described by `renderIndexColumns`. -/
def problem_spec_renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) (result : String) : Prop :=
  result = renderIndexColumns quoteName columns suffixes opclasses
-- post-conditions-end

-- impl-start
def implementation_renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) : String :=
  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
    -- Pre-patch behavior: when a positional hint exists for this entry it is
    -- appended with a separating space UNCONDITIONALLY, so an empty hint still
    -- contributes a trailing space after the annotation.
    let mut col := quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")
    match suffixes[p.2]? with
    | some suffix => col := col ++ " " ++ suffix
    | none => pure ()
    return col))
-- impl-end

-- proof-start
theorem correct_renderIndexColumns :
    ∀ (quoteName : String → String) (columns suffixes opclasses : List String),
      columns.length ≤ opclasses.length →
      problem_spec_renderIndexColumns quoteName columns suffixes opclasses
        (implementation_renderIndexColumns quoteName columns suffixes opclasses) := by
  intro quoteName columns suffixes opclasses _hlen
  unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns appendSuffix
  rfl
-- proof-end
