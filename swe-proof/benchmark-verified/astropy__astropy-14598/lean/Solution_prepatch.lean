import Mathlib
-- imports-end

/-!
Recovering a quoted text field from a single continuation segment of a long,
space-padded record. Each segment carries one optionally-quoted token possibly
followed by a separator and trailing notes; this returns the token's contributed
text, or signals that the segment is not in the expected quoted shape (so the
caller keeps it verbatim). Doubled quote marks inside the token are part of the
text and are preserved exactly.
-/

-- axioms-start
-- No unchanged callee is consumed as a hypothesis: every operation of the
-- modeled segment parser (token scan, trailing-whitespace trim, trailing
-- continuation-marker trim) is modeled directly below. This region is
-- intentionally empty; the proof depends on no domain axiom.
-- axioms-end

-- pure-start

/-- Printable ASCII characters (code points 32..126). -/
def isPrintable (c : Char) : Bool :=
  let n := c.toNat
  decide (32 ≤ n ∧ n ≤ 126)

/-- ASCII whitespace trimmed from the right end of a field:
space, tab, newline, carriage return, vertical tab, form feed. -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  n == 32 || n == 9 || n == 10 || n == 13 || n == 11 || n == 12

/-- Drop trailing whitespace. -/
def dropTrailingWs (cs : List Char) : List Char :=
  (cs.reverse.dropWhile isWs).reverse

/-- Drop a single trailing continuation marker `&` if present. -/
def dropTrailingAmp (cs : List Char) : List Char :=
  match cs.getLast? with
  | some c => if c == '&' then cs.dropLast else cs
  | none => cs

/-- The single-quote delimiter character. -/
def quote : Char := '\''

/-- After a candidate closing quote, the remainder of the segment is acceptable
when it is `spaces*` followed by either the end of the segment or a separator `/`
that introduces trailing notes running to the end. -/
def remainderOk (cs : List Char) : Bool :=
  match cs.dropWhile (· == ' ') with
  | [] => true
  | c :: _ => c == '/'

/-- Scan the token body left to right, accumulating printable characters, and
accept the first quote that closes a non-empty accumulator and whose suffix is
acceptable. A non-printable character before any acceptable quote means the
segment has no token. Returns the captured token body. -/
def scanToken : List Char → List Char → Option (List Char)
  | _acc, [] => none
  | acc, c :: rest =>
      if c == quote && acc ≠ [] && remainderOk rest then
        some acc
      else if isPrintable c then
        scanToken (acc ++ [c]) rest
      else
        none

/-- Capture the token of a segment, if the whole segment is in the expected
shape. `none` ⇒ the segment is not in that shape (the caller keeps it verbatim).
A leading quote opens a token; an immediately following quote yields the empty
token; a segment with no leading quote matches the empty token exactly when its
remainder is acceptable. -/
def matchToken (vc : List Char) : Option (List Char) :=
  match vc with
  | q :: body =>
      if q == quote then
        match scanToken [] body with
        | some s => some s
        | none =>
            match body with
            | q2 :: rest => if q2 == quote && remainderOk rest then some [] else none
            | [] => none
      else
        if remainderOk vc then some [] else none
  | [] => if remainderOk vc then some [] else none
-- pure-end

-- post-conditions-start
/-- Specification of the segment value recovery.

`result` is `none` exactly when the segment is not in the expected quoted shape
(the caller then keeps the raw segment); otherwise `result = some v` where `v` is
the recovered token text. The recovered text is the captured token with trailing
whitespace and at most one trailing continuation marker removed; every interior
doubled quote `''` is part of the text and is preserved verbatim (frame on the
doubled-quote content). -/
def problem_spec_segmentValue (vc : List Char) (result : Option (List Char)) : Prop :=
  result = (matchToken vc).map (fun s => dropTrailingAmp (dropTrailingWs s))
-- post-conditions-end

-- impl-start
-- Local helpers for the pre-patch behavior, confined to this region so the
-- specification view stays identical to the post-patch bundle.
def lookaheadOk (cs : List Char) : Bool :=
  match cs with
  | [] => true
  | c :: _ => c == '/' || c == ' '

def scanTokenLoose : List Char → List Char → Option (List Char)
  | _acc, [] => none
  | acc, c :: rest =>
      if c == quote && acc ≠ [] && lookaheadOk rest then
        some acc
      else if isPrintable c then
        scanTokenLoose (acc ++ [c]) rest
      else
        none

def matchTokenLoose (vc : List Char) : List Char :=
  match vc with
  | q :: body =>
      if q == quote then
        match scanTokenLoose [] body with
        | some s => s
        | none => []
      else
        []
  | [] => []

def collapseDoubledQuote : List Char → List Char
  | [] => []
  | [c] => [c]
  | c1 :: c2 :: rest =>
      if c1 == quote && c2 == quote then
        quote :: collapseDoubledQuote rest
      else
        c1 :: collapseDoubledQuote (c2 :: rest)

def implementation_segmentValue (vc : List Char) : Option (List Char) := Id.run do
  let mut value := matchTokenLoose vc
  value := dropTrailingWs value
  value := collapseDoubledQuote value
  value := dropTrailingAmp value
  return some value
-- impl-end

-- proof-start
theorem correct_segmentValue :
    ∀ vc : List Char, problem_spec_segmentValue vc (implementation_segmentValue vc) := by
  sorry
-- proof-end
