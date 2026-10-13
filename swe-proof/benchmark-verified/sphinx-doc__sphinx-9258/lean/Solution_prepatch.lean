import Mathlib
-- imports-end

/-!
Splitting a parameter/attribute type specification into the pieces that should
be cross-referenced as type names versus the pieces that are mere separators.

A type specification written in a documentation field (for example the text
after `:type age:`) may name several alternative types joined by punctuation and
keywords. The specification string is tokenised left-to-right into a sequence of
segments, alternating free text and separators, in the manner of a regular
splitting operation whose separator is the following alternation (tried in this
order at each position):

* optional surrounding whitespace around one of the bracket/parenthesis/comma
  characters `[ ] ( ) ,`, where the closing side may additionally absorb a
  following `or` keyword;
* the word `or` surrounded by whitespace;
* a vertical bar `|` with optional surrounding whitespace;
* an ellipsis `...`.

After splitting, the empty pieces are discarded. Each surviving piece is then
classified: a piece that is itself a separator (its front matches the separator
alternation) is kept verbatim as separator text; every other piece is a type
name to be cross-referenced. The result lists these classified segments in
order.

The desired behaviour treats a vertical bar `|` (optionally padded by
whitespace) as one of the separators, so that a specification such as
`int | str` yields the two type names `int` and `str` around a `|` separator,
matching the alternatives already available with the `or` keyword.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The separator
-- recognition and the split are modeled DEEPLY over the observable input string
-- (a list of characters), so no `opaque`/`axiom` callee contract is needed. The
-- downstream, unchanged step that turns each classified segment into a rendered
-- node is a structural one-to-one map and is represented directly by the segment
-- carrier below.
-- axioms-end

-- pure-start
/-- A classified piece of a split type specification: either separator text kept
verbatim, or a type name to be cross-referenced. -/
inductive Seg where
  | sep  : List Char → Seg
  | name : List Char → Seg
deriving DecidableEq, Repr

/-- Whitespace characters recognised by the separator matcher: exactly the code
points the splitting operation treats as whitespace (ASCII whitespace including
vertical tab and form feed, the information-separator controls, NEL, NBSP, and
the Unicode space/line/paragraph separators). -/
def isSp (c : Char) : Bool :=
  let n := c.toNat
  decide ((0x9 ≤ n ∧ n ≤ 0xD) ∨ (0x1C ≤ n ∧ n ≤ 0x20) ∨ n = 0x85 ∨ n = 0xA0 ∨
    n = 0x1680 ∨ (0x2000 ≤ n ∧ n ≤ 0x200A) ∨ n = 0x2028 ∨ n = 0x2029 ∨
    n = 0x202F ∨ n = 0x205F ∨ n = 0x3000)

/-- The bracket / parenthesis / comma characters that may act as separators. -/
def isBracket (c : Char) : Bool :=
  c == '[' || c == ']' || c == '(' || c == ')' || c == ','

/-- Length of the leading run of whitespace. -/
def spacesLen : List Char → Nat
  | []      => 0
  | c :: cs => if isSp c then 1 + spacesLen cs else 0

/-- Ellipsis alternative: `...` matches three characters. -/
def dotsLen (cs : List Char) : Option Nat :=
  match cs with
  | '.' :: '.' :: '.' :: _ => some 3
  | _ => none

/-- Vertical-bar alternative (`\s*\|\s*`), then the ellipsis alternative. The
`pipe` flag selects whether the vertical bar participates. -/
def pipeOrDots (pipe : Bool) (cs : List Char) : Option Nat :=
  if pipe then
    let k := spacesLen cs
    match cs.drop k with
    | '|' :: _ => some (k + 1 + spacesLen (cs.drop (k + 1)))
    | _        => dotsLen cs
  else dotsLen cs

/-- The `or`-keyword alternative (`\s+or\s+`), then the vertical bar / ellipsis
alternatives. -/
def tailDelim (pipe : Bool) (cs : List Char) : Option Nat :=
  let k := spacesLen cs
  match cs.drop k with
  | 'o' :: 'r' :: tl =>
    if k ≥ 1 ∧ spacesLen tl ≥ 1 then some (k + 2 + spacesLen tl)
    else pipeOrDots pipe cs
  | _ => pipeOrDots pipe cs

/-- Match the whole separator alternation as a prefix of `cs`, returning the
length consumed, or `none` if no alternative matches at the front. The first
alternative is `\s*[\[\]\(\),](?:\s*or\s)?\s*` (optional whitespace around a
bracket-class character, the closing side optionally absorbing a following
`or`); the remaining alternatives follow in `tailDelim`. -/
def delimLen (pipe : Bool) (cs : List Char) : Option Nat :=
  let k := spacesLen cs
  match cs.drop k with
  | c :: _ =>
    if isBracket c then
      let b := k + 1
      let k2 := spacesLen (cs.drop b)
      let j := b + k2
      match cs.drop j with
      | 'o' :: 'r' :: c3 :: _ =>
        if isSp c3 then some (j + 3 + spacesLen (cs.drop (j + 3)))
        else some (b + spacesLen (cs.drop b))
      | _ => some (b + spacesLen (cs.drop b))
    else tailDelim pipe cs
  | [] => tailDelim pipe cs

/-- Split a character list the way a regular splitting operation with a capturing
separator does: emit alternating free-text and separator pieces (including empty
pieces), consuming a separator whenever the alternation matches at the current
position and otherwise accumulating one character of free text. `fuel` bounds the
recursion; the wrapper below supplies `target.length`, which always suffices. -/
def reSplitFuel (pipe : Bool) : Nat → List Char → List Char → List (List Char)
  | 0,        cur, _        => [cur]
  | (_ + 1),  cur, []       => [cur]
  | (fuel+1), cur, c :: rest =>
    match delimLen pipe (c :: rest) with
    | some n =>
        let s := c :: rest
        cur :: (s.take n) :: reSplitFuel pipe fuel [] (s.drop n)
    | none => reSplitFuel pipe fuel (cur ++ [c]) rest

/-- The split of `target` into alternating text/separator pieces (with empties). -/
def reSplit (pipe : Bool) (target : List Char) : List (List Char) :=
  reSplitFuel pipe target.length [] target

/-- Classify a nonempty split piece: a piece whose front matches the separator
alternation is separator text; otherwise it is a type name. -/
def classifySeg (piece : List Char) : Seg :=
  match delimLen true piece with
  | some _ => Seg.sep piece
  | none   => Seg.name piece

/-- Tokenise a type specification into classified segments: split, drop empty
pieces, classify each survivor. The vertical bar participates as a separator. -/
def tokenize (target : List Char) : List Seg :=
  ((reSplit true target).filter (· ≠ [])).map classifySeg
-- pure-end

-- post-conditions-start
/-- The result is exactly the classified-segment tokenisation of the type
specification, with the vertical bar recognised as a separator alongside the
brackets, commas, the `or` keyword and the ellipsis. -/
def problem_spec_splitTypeSpec (target : List Char) (result : List Seg) : Prop :=
  result = tokenize target
-- post-conditions-end

-- impl-start
def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do
  -- Separator recognition here omits the vertical-bar alternative (the `false`
  -- flag), so a specification such as `int | str` is never split around the bar
  -- and is kept as one type name.
  let subTargets := reSplit false target
  let mut results : List Seg := []
  for sub in subTargets do
    if sub ≠ [] then
      if (delimLen false sub).isSome then
        results := results ++ [Seg.sep sub]
      else
        results := results ++ [Seg.name sub]
  return results
-- impl-end

-- proof-start
theorem correct_splitTypeSpec :
    ∀ (target : List Char),
      problem_spec_splitTypeSpec target (implementation_splitTypeSpec target) := by
  sorry
-- proof-end
