import Mathlib
-- imports-end

/-!
Deciding whether a finite sum of terms is definitely zero, definitely nonzero,
or undetermined — a three-valued verdict (`some true` / `some false` / `none`).

Each term is pre-classified by where it lives:

* `realZero`     — a real term already known to be zero;
* `realNonzero`  — a real term known to be nonzero;
* `realUnknown`  — a real term whose zero-ness cannot be settled;
* `imaginary`    — a purely imaginary (nonzero) term;
* `imagOrZero`   — a term that is either purely imaginary or zero (its product
                   with the imaginary unit is real), but which is not pinned to
                   be purely imaginary;
* `indeterminate`— a term that fits none of the above categories.

The verdict must be *sound*: it may answer `none` (undetermined) whenever it
cannot be sure, but every definite zero/nonzero answer it gives must hold. The
decision also consumes one auxiliary three-valued fact —
`realSumZero`, whether the combined sum of just the definitely-nonzero real
terms is itself zero — since cancellation among those terms can still occur.

The governing principle this captures: when every term is real and zero the sum
is zero; when there is no definitely-nonzero real term to anchor the real part
(or every term is such a term), no definite verdict about the whole sum is
warranted and the answer must stay undetermined; otherwise the real anchor plus
the imaginary content jointly decide the outcome.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Each term's category is supplied as
-- an input classification (`Summand`), and the three-valued zero-test of the
-- real anchor sub-sum is supplied as the input `realSumZero`, so the verdict is
-- grounded directly in the inputs and the proof needs no callee contract.
-- (G-AX is a skip stub.)
-- axioms-end

-- pure-start
/-- Category of a single summand (see module docstring). -/
inductive Summand
  | realZero
  | realNonzero
  | realUnknown
  | imaginary
  | imagOrZero
  | indeterminate
deriving DecidableEq, Repr

/-- A real term whose zero-ness cannot be decided, or a wholly unclassifiable
term: either forces the overall verdict to be undetermined. -/
def isUnclassified : Summand → Bool
  | .realUnknown => true
  | .indeterminate => true
  | _ => false

def isRealZero : Summand → Bool
  | .realZero => true
  | _ => false

def isRealNonzero : Summand → Bool
  | .realNonzero => true
  | _ => false

def isImag : Summand → Bool
  | .imaginary => true
  | _ => false

def isImagOrZero : Summand → Bool
  | .imagOrZero => true
  | _ => false

/-- The sound three-valued zero-verdict for the whole sum, as a total function
of the term categories and the real-anchor fact `realSumZero`. -/
def zeroVerdict (terms : List Summand) (realSumZero : Option Bool) : Option Bool :=
  if terms.any isUnclassified then
    none
  else
    let z := terms.countP isRealZero
    let nz := terms.countP isRealNonzero
    let n := terms.length
    let im := terms.any isImag
    let imOrZ := terms.any isImagOrZero
    if z == n then
      some true
    else if nz == 0 || nz == n then
      none
    else
      match realSumZero with
      | some true =>
          if !imOrZ && !im then some true
          else if im && !imOrZ then some false
          else none
      | some false => some false
      | none => none
-- pure-end

-- post-conditions-start
/-- The result is exactly the sound three-valued zero-verdict determined by the
term categories and the real-anchor fact. This pins every case: a sum of only
real-zero terms is zero; a sum with no definitely-nonzero real anchor (or made
up entirely of such terms) is undetermined; otherwise the anchor combined with
the imaginary content decides, and any presence of an undecidable real term or
an unclassifiable term forces `none`. -/
def problem_spec_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) (result : Option Bool) : Prop :=
  result = zeroVerdict terms realSumZero
-- post-conditions-end

-- impl-start
def implementation_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) : Option Bool := Id.run do
  let mut z := 0
  let mut nz := 0
  let mut im := false
  let mut imOrZ := false
  for a in terms do
    match a with
    | .realZero => z := z + 1
    | .realNonzero => nz := nz + 1
    | .realUnknown => return none
    | .imaginary => im := true
    | .imagOrZero => imOrZ := true
    | .indeterminate => return none
  if z == terms.length then
    return some true
  if nz == terms.length then
    return none
  match realSumZero with
  | some true =>
      if !imOrZ && !im then
        return some true
      if im && !imOrZ then
        return some false
  | some false => return some false
  | none => pure ()
  return none
-- impl-end

-- proof-start
theorem correct_zeroStatus :
    ∀ (terms : List Summand) (realSumZero : Option Bool),
      problem_spec_zeroStatus terms realSumZero
        (implementation_zeroStatus terms realSumZero) := by
  sorry
-- proof-end
