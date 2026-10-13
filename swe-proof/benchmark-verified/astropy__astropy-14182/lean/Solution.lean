import Mathlib
-- imports-end

/-!
Supporting a configurable list of header rows in the simple reStructuredText
fixed-width table format.

A simple reStructuredText table is laid out as a leading column-rule line (a row
of `=` characters), then one or more header rows, then a second rule line, then
the data rows, then a trailing rule line. Historically this format always emitted
and consumed exactly one header row (the column names). The desired behaviour is
to let the caller supply a list of header rows (for example the column names, the
units, and the element types), just as the sibling fixed-width formats already
allow.

Two positions in the format depend on HOW MANY header rows there are:

* When emitting, the renderer lays out the header rows first and then the
  column-rule line, so that rule line sits at 0-based position `numHeaderRows`
  in the rendered sequence of lines. The finished output brackets the whole
  rendered table with a copy of that rule line at the top and the bottom.

* When parsing, the first data line sits two lines below the last header row
  together with the leading rule line — i.e. at position `2 + numHeaderRows`.

For the historical single-header-row case (`numHeaderRows = 1`) these reduce to
the positions `1` and `3` respectively, so existing single-row tables are
unaffected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both modeled
-- quantities are pure functions of the number of header rows (and, for the
-- emit case, of the already-rendered sequence of lines, which enters as a direct
-- input observation rather than being recomputed). No `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Emitting: the finished output is the already-rendered sequence of `lines`
bracketed top and bottom by a copy of the column-rule line, which is the line at
position `numHeaderRows` in that sequence. Every other line is exactly the
rendered line in its original order. -/
def problem_spec_rstWrap
    (numHeaderRows : Nat) (lines : List String) (result : List String) : Prop :=
  result = [lines.getD numHeaderRows ""] ++ lines ++ [lines.getD numHeaderRows ""]
-- post-conditions-end

-- impl-start
def implementation_rstWrap
    (numHeaderRows : Nat) (lines : List String) : List String := Id.run do
  let idx := numHeaderRows
  let sep := lines.getD idx ""
  let mut out := [sep] ++ lines ++ [sep]
  return out
-- impl-end

-- proof-start
theorem correct_rstWrap :
    ∀ (numHeaderRows : Nat) (lines : List String),
      problem_spec_rstWrap numHeaderRows lines
        (implementation_rstWrap numHeaderRows lines) := by
  intro numHeaderRows lines
  unfold problem_spec_rstWrap implementation_rstWrap
  rfl
-- proof-end

-- post-conditions-start
/-- Parsing: the position of the first data line is two lines below the header
rows together with the leading rule line, i.e. `2 + numHeaderRows`. -/
def problem_spec_rstDataStart (numHeaderRows : Nat) (result : Nat) : Prop :=
  result = 2 + numHeaderRows
-- post-conditions-end

-- impl-start
def implementation_rstDataStart (numHeaderRows : Nat) : Nat := Id.run do
  return 2 + numHeaderRows
-- impl-end

-- proof-start
theorem correct_rstDataStart :
    ∀ (numHeaderRows : Nat),
      problem_spec_rstDataStart numHeaderRows
        (implementation_rstDataStart numHeaderRows) := by
  intro numHeaderRows
  unfold problem_spec_rstDataStart implementation_rstDataStart
  rfl
-- proof-end
