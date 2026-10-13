import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The character-class recognizers and the identifier
   name-mangling this module relies on are modeled DEEPLY in the `pure` region
   below and validated against their real counterparts by axiom_check.py (G-AX)
   as A-references; none is hidden behind a consumed axiom. -/
-- axioms-end

-- pure-start
/- Character classes (per-code-point, ASCII alphabet). A "word" character is a
   letter, a digit, or underscore; an identifier may start with a letter or
   underscore; the four type-tag characters are f/F/l/L. -/
def isWordChar (c : Char) : Bool := c.isAlpha || c.isDigit || c == '_'
def isIdentStart (c : Char) : Bool := c.isAlpha || c == '_'
def isTypeTagChar (c : Char) : Bool := c == 'f' || c == 'F' || c == 'l' || c == 'L'

/- A trailing type tag is a single tag character that is NOT immediately
   followed by another word character (so a run like `fudl` is a name, not a
   tag). Deep model of `[fFlL]\b`; the word boundary is exactly the
   "next char is non-word, or end of input" condition. -/
def matchTypeTag (rest : List Char) : Option Char :=
  match rest with
  | []      => none
  | c :: cs =>
    if isTypeTagChar c then
      match cs with
      | []     => some c
      | d :: _ => if isWordChar d then none else some c
    else none

/- A trailing suffix name is a maximal run of word characters that begins with
   a letter or underscore. Deep model of `[a-zA-Z_][a-zA-Z0-9_]*\b`; after a
   maximal word run the closing boundary always holds. -/
def matchSuffixName (rest : List Char) : Option (List Char) :=
  match rest with
  | []      => none
  | c :: cs =>
    if isIdentStart c then some (c :: cs.takeWhile (fun d => isWordChar d))
    else none

/- Id of a plain numeric literal: the token wrapped in `L … E`. -/
def numberLitId (text : List Char) : List Char := ['L'] ++ text ++ ['E']

/- Id of an identifier (the relevant case: ordinary names): the decimal length
   prefix followed by the name, with the special abbreviation `std → St`. -/
def identId (ident : List Char) : List Char :=
  if ident = ['s', 't', 'd'] then ['S', 't']
  else (toString ident.length).toList ++ ident

/- Id of a suffixed literal: mangled as the call of a one-argument function
   named by the suffix applied to the underlying literal. -/
def suffixedLitId (litText ident : List Char) : List Char :=
  "clL_Zli".toList ++ identId ident ++ ['E'] ++ numberLitId litText ++ ['E']

/- The id a floating-point literal token produces, given the recognized float
   text `floatText` and the characters `rest` that follow it. Three cases:
   (1) a trailing type tag is part of the number; (2) a trailing suffix name
   produces a suffixed literal; (3) otherwise a plain number. -/
def parsedFloatId (floatText rest : List Char) : List Char :=
  match matchTypeTag rest with
  | some c => numberLitId (floatText ++ [c])
  | none   =>
    match matchSuffixName rest with
    | some ident => suffixedLitId floatText ident
    | none       => numberLitId floatText
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method literalIdAfterFloat (floatText : List Char) (rest : List Char) return (out : List Char)
  ensures out = parsedFloatId floatText rest
  do
    -- impl-start
    match matchTypeTag rest, matchSuffixName rest with
    | some c, _         => pure (numberLitId (floatText ++ [c]))
    | none,   some ident => pure (suffixedLitId floatText ident)
    | none,   none       => pure (numberLitId floatText)
    -- impl-end

prove_correct literalIdAfterFloat by
  loom_solve <;> simp_all [parsedFloatId]
