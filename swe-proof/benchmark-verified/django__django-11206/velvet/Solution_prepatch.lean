import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The display string produced by the plain zero value -- the value that denotes
   zero and is written as a single zero digit in the units place -- at a
   requested number of visible fractional positions.

   It is a free constant with nothing asserted about it: the operation modeled
   here selects which value is displayed and never inspects the characters of a
   display string. Provenance and the executable soundness check that this
   constant really is the display step applied to that one value:
   mapping.md / axiom_check.py (G-AX). -/
opaque zeroRender : Option Nat → List Char

/- A decimal input, carried as the two facets the operation modeled here reads it
   through, and no others:

   * `amount` -- the exact amount it denotes, as a rational. The one decision the
     operation makes compares magnitudes, and a magnitude is a property of the
     amount alone.
   * `render` -- the display string this very value produces at a requested
     number of visible fractional positions. The operation hands its input on to
     a display step it does not itself change, and inputs that denote one amount
     can still display differently, so that behaviour travels WITH the value
     rather than being reconstructible from a description of it.

   Carrying the display behaviour as a facet of the value is what makes the pass-
   through case below a claim about the input ITSELF: a value assembled from a
   description of the input satisfies the claim only when it displays exactly as
   the input does. Provenance of the correspondence, and the executable check
   that these two facets are the only ones the operation reads:
   mapping.md §2 / axiom_check.py (G-AX). -/
structure DecVal where
  amount : Rat
  render : Option Nat → List Char
deriving Inhabited
-- axioms-end

-- pure-start
/- The display string a value produces at a requested number of visible
   fractional positions. -/
def renderDecimal (d : DecVal) (dp : Option Nat) : List Char := d.render dp

/- The plain zero value: it denotes zero and displays as the plain zero form.
   Naming this value, and not merely the amount it denotes, is what makes the
   normalization below observable: every value denoting zero has the same amount,
   yet the display step tells them apart, so the obligation has to say WHICH zero
   is displayed. -/
def plainZero : DecVal := { amount := 0, render := zeroRender }

/- The magnitude of an exact amount (order-only; modeled with exact rationals so
   comparisons are decidable -- DECISIONS.md float-order note). -/
def ratAbs (n : Rat) : Rat := max n (-n)

/- The number of significant digits the ambient environment keeps when it
   materializes a magnitude. -/
def workingDigits : Nat := 28

/- The smallest magnitude that is still distinguishable given a requested number
   of visible fractional positions `p`: one unit in the last visible position,
   i.e. ten to the power of negative `max p 1`. (With zero requested positions
   the boundary is still the first fractional position.) -/
def resolution (p : Nat) : Rat := 1 / (10 : Rat) ^ (max p 1)

/- The magnitude threshold the comparison below actually uses: the resolution,
   lowered by HALF a unit in the last significant position the ambient
   environment keeps.

   The lowering is not a tolerance and not slack. The magnitude a comparison sees
   is first materialized at the ambient working precision, ties to even, and only
   then compared, so a magnitude strictly under the resolution can still
   materialize AT it and compare not-under -- which happens exactly for
   magnitudes at or above this threshold. Comparing the exact magnitude against
   the lowered threshold is therefore the same predicate as comparing the
   materialized magnitude against the resolution, with equality at the threshold
   itself resolving upward because ties go to the even last digit. Derivation and
   the executable equivalence check: mapping.md §2 / axiom_check.py (G-AX). -/
def guardCutoff (p : Nat) : Rat :=
  resolution p - resolution p / (2 * (10 : Rat) ^ workingDigits)

/- Whether the amount a value denotes is smaller in magnitude than the threshold
   for the requested number of visible positions. When no number of positions is
   requested, nothing is below resolution. -/
def belowResolution (d : DecVal) (dp : Option Nat) : Bool :=
  match dp with
  | none   => false
  | some p => decide (ratAbs d.amount < guardCutoff p)

/- Normalize an input for display: a value whose magnitude is below the threshold
   for the requested number of visible positions is replaced by the plain zero
   value, and every other input is carried through exactly as it came in. This is
   the value the display step must receive. -/
def clampSmall (d : DecVal) (dp : Option Nat) : DecVal :=
  if belowResolution d dp then plainZero else d
-- pure-end

-- pre-conditions-start
/- The magnitude of the least exponent the ambient environment can represent. A
   magnitude whose last significant position would fall below it is materialized
   on a COARSER grid than the working precision alone determines, because that
   position cannot be held. Provenance and the executable boundary measurement:
   mapping.md §2 / axiom_check.py (G-AX). -/
def leastExponentMagnitude : Nat := 1000026

/- The requested position counts this obligation speaks about: those for which
   materializing a magnitude near the resolution still lands on the grid the
   working precision determines, so that `guardCutoff` below is the threshold a
   comparison applies.

   Past this count the grid is the coarser one set by the least representable
   exponent, and the threshold parts company with `guardCutoff` in BOTH
   directions -- a magnitude under it can materialize at the resolution, and one
   over it can materialize at zero. Those counts are outside the correspondence
   and this obligation says nothing about them. The boundary is exact and
   measured: every count up to `leastExponentMagnitude - workingDigits` agrees,
   the next one does not (mapping.md §2 domain paragraph, axiom_check.py). Note
   the bound restricts only the requested position count -- it puts NO bound on
   the input, whose magnitude may lie below the least representable exponent and
   still be covered. -/
def positionsInExponentRange (dp : Option Nat) : Prop :=
  match dp with
  | none   => True
  | some p => max p 1 + workingDigits ≤ leastExponentMagnitude
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the display string for a decimal input at a requested number of
   visible fractional positions. The input is first normalized so that a
   magnitude too small to affect any visible position is replaced by the plain
   zero value, and the resulting value is then displayed.
   `number` and `decimalPos` are read-only inputs (neither declared `mut`); the
   only mutated local is the working value handed on for display (directive 5:
   its post-state is pinned to `clampSmall number decimalPos`). -/
method formatDecimal (number : DecVal) (decimalPos : Option Nat) return (out : List Char)
  require positionsInExponentRange decimalPos
  ensures out = renderDecimal (clampSmall number decimalPos) decimalPos
  do
    -- impl-start
    return renderDecimal number decimalPos
    -- impl-end

prove_correct formatDecimal by
  loom_solve <;> simp_all [clampSmall, plainZero, renderDecimal]
