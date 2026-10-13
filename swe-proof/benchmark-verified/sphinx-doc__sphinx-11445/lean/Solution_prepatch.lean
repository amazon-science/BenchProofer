import Mathlib
-- imports-end

/-!
Behavior: inserting a configured preamble block into the leading lines of a
reStructuredText document body, while preserving any bibliographic header that
the document opens with.

A document body is a sequence of text lines. A preamble (itself a sequence of
lines) is spliced in near the top. The placement rule depends on how many of the
document's *leading* lines are bibliographic field lines:

  * A bibliographic field line opens with a name enclosed in colons followed by
    a space or the end of the line (the reStructuredText field-marker grammar):
    `:name: value` or `:name:`. The name is non-empty, may itself contain
    (escaped or interior) colons, and may not begin with a space.
  * Lines that merely START with a colon-delimited token but are NOT field
    markers — e.g. an interpreted-text role applied to a title such as a
    cross-reference written `:role:` immediately followed by back-quoted text —
    are NOT counted as leading field lines.

Let `k` be the number of consecutive field lines at the very front of the body.
The preamble is placed immediately after those `k` lines. When `k > 0` a single
blank line is emitted between the header block and the preamble; in every case a
single blank line is emitted after the preamble, before the remaining body.
When the preamble is empty the body is returned unchanged.

This module pins exactly where the preamble lands relative to the leading lines,
so that a document whose first line is a colon-delimited role (not a field) keeps
that line adjacent to the line that follows it.
-/

-- axioms-start
-- No outside callee is consumed: the classification of a leading line as a
-- field line, and the placement arithmetic, are modeled DEEPLY from the input
-- line text. There are no `opaque` declarations and no `_prop` axioms; the
-- field-line grammar is validated against the real reference matcher by the
-- mechanical differential check (G-CONF).
-- axioms-end

-- pure-start
/-- Scan the body of a field marker starting just after its opening colon.
`prev` is the character immediately to the left of the cursor (used to enforce
that a closing colon is not preceded by a space). Returns `true` as soon as a
valid closing colon — one not preceded by a space and followed by a space or the
end of the line — is reached. Interior colons (followed by a non-space,
non-backtick character) and backslash-escaped characters are consumed as part of
the name; a backtick or space directly after an interior-looking colon ends the
scan unsuccessfully. -/
def fieldMarkerScan : List Char → Char → Bool
  -- ran off the end without reaching a valid closing colon: no field marker
  | [], _ => false
  -- a trailing backslash with nothing to escape: no field marker
  | (['\\']), _ => false
  -- backslash escapes the next character; both are consumed as name text and
  -- the escaped character becomes the left-neighbour of what follows
  | ('\\' :: d :: rest2), _ => fieldMarkerScan rest2 d
  | (':' :: []), prev => prev != ' '
  | (':' :: d :: tail), prev =>
    -- a closing colon: not preceded by a space, followed by a space or EOL
    if prev != ' ' && d == ' ' then true
    -- an interior colon (part of the name): keep scanning
    else if d != ' ' && d != '`' then fieldMarkerScan (d :: tail) ':'
    else false
  | (c :: rest), _ => fieldMarkerScan rest c
termination_by l _ => l.length
decreasing_by all_goals (simp_wf; try omega)

/-- Whether a line is a bibliographic field line: it opens with `:`, the first
name character is neither `:` nor a space, and the field-marker grammar reaches
a valid closing colon. -/
def isFieldLine (line : List Char) : Bool :=
  match line with
  | (':' :: d :: rest) =>
    if d == ':' || d == ' ' then false else fieldMarkerScan (d :: rest) ':'
  | _ => false

/-- The number of consecutive leading lines of `body` that are field lines. -/
def leadingFieldCount (body : List String) : Nat :=
  (body.takeWhile (fun l => isFieldLine l.toList)).length

/-- The placed-preamble result: the leading `k = leadingFieldCount body` lines,
then (only when `k > 0`) a blank separator, then the preamble, then a blank
separator, then the rest of the body. An empty preamble leaves the body as-is. -/
def placePreambleSpec (body preamble : List String) : List String :=
  if preamble = [] then body
  else
    let k := leadingFieldCount body
    body.take k ++ (if k > 0 then [""] else []) ++ preamble ++ [""] ++ body.drop k
-- pure-end

-- post-conditions-start
/-- The result is exactly the body with the preamble spliced in after the
leading run of field lines: the unchanged leading lines, an optional blank
separator present iff there was at least one leading field line, the preamble
lines in order, a trailing blank separator, and the remaining body lines
unchanged. An empty preamble yields the body verbatim. -/
def problem_spec_placePreamble
    (body preamble : List String) (result : List String) : Prop :=
  result = placePreambleSpec body preamble
-- post-conditions-end

-- impl-start
def implementation_placePreamble
    (body preamble : List String) : List String := Id.run do
  if preamble = [] then
    return body
  -- Pre-patch leading-line test: a line counts as a leading field line as soon
  -- as it opens `:` followed by one-or-more name characters and another `:`,
  -- ignoring what follows. This loose test also accepts a colon-delimited role
  -- at the head of a title (`:role:` immediately followed by back-quoted text),
  -- so such a line is wrongly counted and the preamble is placed after it.
  let looseFieldHead : List Char → Bool := fun cs =>
    match cs with
    | (':' :: rest) =>
      let rec scan : List Char → Bool → Bool
        | [], _ => false
        | (c :: cs'), seen =>
          if c == ':' then seen
          else if c.isAlphanum || c == '_' then scan cs' true
          else false
      scan rest false
    | _ => false
  let mut pos := 0
  for line in body do
    if looseFieldHead line.toList then
      pos := pos + 1
    else
      break
  let head := body.take pos
  let tail := body.drop pos
  let sep := if pos > 0 then ([""] : List String) else []
  return head ++ sep ++ preamble ++ [""] ++ tail
-- impl-end

-- proof-start
theorem correct_placePreamble : ∀ (body preamble : List String),
    problem_spec_placePreamble body preamble
      (implementation_placePreamble body preamble) := by
  sorry
-- proof-end
