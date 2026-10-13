import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The step that turns three textual date components into a
   concrete calendar value (and then renders it) is an unchanged callee whose
   three mutually-exclusive outcomes are the ONLY thing that matters here; it is
   modeled as a free input `ConstructOutcome` (see below). The postconditions
   hold for EVERY such outcome, so the callee is owed no contract — it is
   strictly weaker than any concrete implementation of it (directive 7). The
   behaviour this bundle actually pins — how each outcome is turned into the
   returned text — is modeled DEEPLY in the `pure` region. There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The result of attempting to interpret three textual components as a calendar
   value, in three mutually-exclusive shapes:
     * `rendered s`  — a calendar value was obtained and rendered to the text `s`;
     * `notCalendar` — the components name no representable calendar value
                       (e.g. a zero/oversize month or day, or a non-numeric
                       component);
     * `unrepresentable` — a component's magnitude exceeds the range the
                       calendar machinery accepts at all. -/
inductive ConstructOutcome where
  | rendered (s : List Char)
  | notCalendar
  | unrepresentable
  deriving DecidableEq

/- The non-value shape of the result carrier: the caller is handed no text at
   all. It is the error side of the `Except` this branch returns. -/
inductive DateErr where
  | valueEscaped
  deriving DecidableEq

/- A single component, normalized for the fallback rendering: an empty component
   shows as the digit zero, any other component shows verbatim. -/
def orZero (x : List Char) : List Char :=
  if x = [] then ['0'] else x

/- The fallback rendering: the three normalized components joined by hyphens
   (a pseudo-ISO triple). -/
def pseudoTriple (y m d : List Char) : List Char :=
  orZero y ++ ['-'] ++ orZero m ++ ['-'] ++ orZero d

/- That same fallback rendering taken at three unsupplied components. -/
def fallbackNoComponents : List Char := pseudoTriple [] [] []

/- The returned text for the all-components-supplied branch, as a total function
   of the three components and the construction outcome. The function is total:
   every outcome is mapped to a value (`Except.ok`). -/
def dateText (y m d : List Char) (o : ConstructOutcome) : Except DateErr (List Char) :=
  match o with
  | .rendered s     => Except.ok s
  | .notCalendar    => Except.ok (pseudoTriple y m d)
  | .unrepresentable => Except.ok fallbackNoComponents

@[grind] lemma dateText_rendered (y m d : List Char) (s : List Char) :
    dateText y m d (.rendered s) = Except.ok s := rfl
@[grind] lemma dateText_notCalendar (y m d : List Char) :
    dateText y m d .notCalendar = Except.ok (pseudoTriple y m d) := rfl
@[grind] lemma dateText_unrepresentable (y m d : List Char) :
    dateText y m d .unrepresentable = Except.ok fallbackNoComponents := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Turn three supplied textual date components into the text this widget reports,
   on the branch where all three components are present. The components are first
   handed to the calendar machinery; its outcome decides the result, per
   `dateText`.
   `y`, `m`, `d` and `outcome` are read-only (not `mut`); the routine builds a
   fresh result and mutates none of them (directive 5). -/
method dateComponentsText (y : List Char) (m : List Char) (d : List Char)
    (outcome : ConstructOutcome) return (out : Except DateErr (List Char))
  ensures out = dateText y m d outcome
  ensures ∀ s, outcome = .rendered s → out = Except.ok s
  ensures outcome = .notCalendar → out = Except.ok (pseudoTriple y m d)
  ensures outcome = .unrepresentable → out = Except.ok fallbackNoComponents
  ensures ∃ r, out = Except.ok r
  do
    -- impl-start
    -- Pre-image skeleton: the dispatch handles only the representable value and
    -- the no-representable-value fallback; the third outcome is left to the
    -- error side of the carrier (`Except.error .valueEscaped`) instead of being
    -- mapped to a text. The frozen spec maps every outcome to a text via
    -- `dateText`, so prove_correct MUST fail.
    let result : Except DateErr (List Char) :=
      match outcome with
      | .rendered s      => Except.ok s
      | .notCalendar     => Except.ok (pseudoTriple y m d)
      | .unrepresentable => Except.error .valueEscaped
    return result
    -- impl-end

prove_correct dateComponentsText by
  loom_solve
  cases outcome <;> simp_all
