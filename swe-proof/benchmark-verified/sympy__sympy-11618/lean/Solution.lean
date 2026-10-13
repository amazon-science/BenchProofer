import Mathlib
-- imports-end

/-!
The squared Euclidean separation between two points given by their finite
sequences of numeric coordinates.

A point in `n`-dimensional space is described by its ordered list of
coordinates. The Euclidean separation between two points is obtained from the
sum of the squared differences of their coordinates, taken coordinate by
coordinate. The actual distance is the square root of that sum; the square root
is a constant, order-preserving outer wrapper, so the quantity that fully
determines the distance is this sum of squared coordinate differences — the
radicand — and that is what is specified here.

The two sequences may have DIFFERENT dimensions, and the dimension the
comparison is carried out in depends on whether the two points are of the SAME
kind (`sameKind = true`) or of DIFFERENT kinds (`sameKind = false`):

* When the two points are of the same kind, the comparison runs in the SMALLER
  of the two dimensions: positions present in only the longer sequence are
  dropped (the plain coordinate-by-coordinate pairing truncates to the shorter
  sequence).
* When the two points are of different kinds, the comparison runs in the LARGER
  of the two dimensions: the shorter sequence is embedded at the origin of the
  larger ambient space, so a position present in only one sequence still
  contributes the square of that sequence's coordinate (the missing trailing
  coordinates of the shorter sequence read as zero), and must NOT be dropped.

Thus a position beyond the compared dimension contributes nothing, and a
position within it where one sequence is too short reads that sequence's
coordinate as `0`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The quantity
-- is modeled DEEPLY and structurally over the two coordinate sequences (summing
-- squared coordinate differences across the compared dimension, with missing
-- coordinates within that dimension read as zero). The square-root outer wrapper
-- is constant and order-preserving, hence modeled away. So no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- The ambient dimension the two coordinate sequences are compared in. When the
two points are of the same kind (`sameKind = true`) the comparison runs in the
SMALLER dimension (the truncating coordinate pairing); when they are of
different kinds it runs in the LARGER dimension (the shorter sequence is
zero-embedded into the larger ambient space). -/
def commonLen (sameKind : Bool) (a b : List Rat) : Nat :=
  if sameKind then min a.length b.length else max a.length b.length

/-- The squared separation of two coordinate sequences `a` and `b` with kind
discriminator `sameKind`: the sum, over every position `i` below the compared
dimension `commonLen sameKind a b`, of the squared difference of the coordinates
at `i`, where a sequence too short to have a coordinate at position `i` reads as
`0` there. Front-aligned accumulator fold over the positions
`0, 1, …, commonLen sameKind a b - 1`. -/
def sqSep (sameKind : Bool) (a b : List Rat) : Rat :=
  (List.range (commonLen sameKind a b)).foldl
    (fun acc i => acc + (a.getD i 0 - b.getD i 0) ^ 2) 0
-- pure-end

-- post-conditions-start
/-- The reported squared separation is exactly the sum of squared coordinate
differences over every position up to the compared dimension (missing
coordinates counting as zero): `result = sqSep sameKind a b`. -/
def problem_spec_sqSeparation (sameKind : Bool) (a b : List Rat) (result : Rat) : Prop :=
  result = sqSep sameKind a b
-- post-conditions-end

-- impl-start
def implementation_sqSeparation (sameKind : Bool) (a b : List Rat) : Rat := Id.run do
  let n := if sameKind then min a.length b.length else max a.length b.length
  let mut acc : Rat := 0
  for i in [0:n] do
    acc := acc + (a.getD i 0 - b.getD i 0) ^ 2
  return acc
-- impl-end

-- proof-start
theorem correct_sqSeparation : ∀ (sameKind : Bool) (a b : List Rat),
    problem_spec_sqSeparation sameKind a b (implementation_sqSeparation sameKind a b) := by
  intro sameKind a b
  unfold problem_spec_sqSeparation implementation_sqSeparation sqSep commonLen
  simp [List.range_eq_range']
-- proof-end
