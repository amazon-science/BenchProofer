import Mathlib
-- imports-end

/-!
Running a duplicate-similarity analysis over a set of appended source files and
emitting its findings on standard output.

The analysis is governed by a threshold: the minimum number of consecutive
similar lines that must coincide between two files for them to count as a
duplicated block. When that threshold is at least one, the analysis computes the
similarities among the appended files and renders them as a textual report,
which is the output produced.

When the threshold is set to zero, the analysis is disabled: it performs no
comparison and produces no output at all. (Setting a numeric limit to zero to
turn a check off is the convention used by several other linters.)

The behavior is stated abstractly as an input→output relation, where the output
is modeled as the optional rendered report (`none` when nothing is emitted);
the implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Unchanged dependency callees the analysis uses, declared as opaque signatures.
-- The proof needs no property axiom about either — the contract is stated
-- directly over them and discharged by case analysis on the threshold:
--
-- * `computeSims self` : the set of similarities discovered among the appended
--   files (the comparison pipeline, unaffected by this behavior).
-- * `renderReport sims` : the textual report rendered from a set of discovered
--   similarities and emitted on standard output.

/-- The analyzer state: the appended files and the analysis configuration. -/
opaque Analyzer : Type

/-- The carrier of the similarities discovered among the appended files; its
internal structure is irrelevant to this behavior, so it is a genuinely opaque
type: no property of a similarity set is provable, and in particular the
similarity sets of distinct analyzer states cannot be proven equal — the
enabled branch of the contract is thereby pinned to the report rendered from
THIS analyzer's discovered similarities. -/
opaque SimsRep : NonemptyType.{0}
def Sims : Type := SimsRep.type
instance : Nonempty Sims := SimsRep.property

/-- The similarities discovered among the appended files. -/
noncomputable opaque computeSims : Analyzer → Sims

/-- The textual report rendered from a set of discovered similarities. -/
opaque renderReport : Sims → String
-- axioms-end

-- pure-start
-- (no additional pure helpers required)
-- pure-end

-- post-conditions-start
/-- The analysis run's contract, relating the configured threshold to the
emitted output (`none` = nothing emitted):

* if the threshold of required similar lines is exactly zero, the analysis is
  disabled and emits no output;
* for any other threshold value the output is exactly the report rendered from
  the similarities discovered among the appended files. -/
def problem_spec_run (self : Analyzer) (minLines : Int)
    (result : Option String) : Prop :=
  (minLines = 0 → result = none) ∧
  (minLines ≠ 0 → result = some (renderReport (computeSims self)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
