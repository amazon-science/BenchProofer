import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The behavior under spec is
-- the selection of a single representative value to stand for a coordinate
-- argument: the SHAPE of that argument is modeled DEEPLY (`CoordArg`), the REGIME
-- of each coordinate value and the finiteness test that weighs it are modeled
-- DEEPLY (`CoordVal` / `CoordVal.countsAsFinite`), and the selection is spelled
-- out below, so nothing is axiomatized. The proof agent may add `_prop` axioms
-- only if genuinely stuck.
-- axioms-end

-- pure-start
/-- One coordinate value, in the three regimes the finiteness test distinguishes.
The test is not a bare arithmetic predicate on a number: only a value it can
actually weigh as a quantity is weighed, and it has its own settled ruling for
each of the two other regimes. -/
inductive CoordVal where
  /-- A coordinate value the finiteness test can weigh as a quantity. -/
  | numeric (v : Float) : CoordVal
  /-- A coordinate value the finiteness test cannot weigh as a quantity — a point
  in time, an elapsed duration, an exactly-represented quantity, a whole vector
  standing in one position. Distinct `tag`s denote distinct such values. -/
  | unweighable (tag : Nat) : CoordVal
  /-- A coordinate value that is missing: a hole where a coordinate should be. -/
  | missing : CoordVal

/-- Whether a coordinate value counts as finite for the purposes of the search.

A value that can be weighed counts exactly when it is finite. A value that cannot
be weighed counts REGARDLESS — no finiteness requirement bears on it, so a search
for a finite value does not pass it over. A missing value NEVER counts, whichever
of the other two regimes it might superficially resemble. -/
def CoordVal.countsAsFinite : CoordVal → Bool
  | .numeric v     => v.isFinite
  | .unweighable _ => true
  | .missing       => false

/-- A coordinate argument, in the three shapes it can take. Which shape an
argument has is settled by WHAT KIND of thing it is and never by which values it
holds: a lone coordinate value is not a sequence at all, and of the two shapes
that are sequences, one is a kind the search runs over while the other is a kind
that is read at a position instead. -/
inductive CoordArg where
  /-- A lone coordinate value, which is not a sequence of values. -/
  | single (v : CoordVal) : CoordArg
  /-- A sequence of coordinate values that the search runs over. -/
  | sequence (vs : List CoordVal) : CoordArg
  /-- A sequence of coordinate values that the search does NOT run over, because
  of the kind of sequence it is: such a sequence is read at its leading position
  instead, so no finiteness test bears on any value it holds. -/
  | unsearched (vs : List CoordVal) : CoordArg

/-- Choose one representative value to stand for a coordinate argument.

A lone coordinate value is its own representative, whatever value it is and
whichever regime it belongs to: there is no sequence to search, so no finiteness
test bears on it at all. For a sequence the search runs over, the first value that
COUNTS AS FINITE is chosen if one exists; otherwise, when no value counts but the
sequence is non-empty, the very first value of the sequence is chosen
unconditionally — whatever regime that first value belongs to, including a regime
the test itself declines to count. For a sequence the search does NOT run over,
the leading value is chosen directly and unconditionally: no finiteness test bears
on it either, so it is chosen even when it does not count and even when some later
value would have. Only an empty sequence, of whichever of the two sequence shapes,
yields no representative. -/
def chooseRepresentative : CoordArg → Option CoordVal
  | .single v    => some v
  | .sequence vs =>
    match vs.find? (fun v => v.countsAsFinite) with
    | some v => some v
    | none   => vs.head?
  | .unsearched vs => vs.head?
-- pure-end

-- post-conditions-start
/-- The result is exactly the representative chosen for the coordinate argument: a
lone coordinate value stands for itself unconditionally, with no finiteness test
applied; for a sequence the search runs over it is the first value that counts as
finite when one is present and the first value of the sequence when no value
counts but the sequence is non-empty; for a sequence the search does not run over
it is the leading value unconditionally, with no finiteness test applied there
either; and no value at all only when a sequence is empty. Because counting as
finite is settled per REGIME — weighed only for a value that can be weighed,
granted to a value that cannot be, withheld from a missing value — and because
WHICH of the three shapes an argument has is settled by its kind rather than by
its contents, the representative is pinned for every argument, not only for
searched sequences of numbers. -/
def problem_spec_safeRepresentative (arg : CoordArg) (result : Option CoordVal) : Prop :=
  result = chooseRepresentative arg
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy) selection: a lone coordinate value stands for itself, but for
a sequence only the first-counting search is performed. When no value counts the
search exhausts the sequence with no representative — the non-empty fall-back to
the first value is MISSING, so a non-empty sequence in which nothing counts yields
no value instead of its first element. -/
def implementation_safeRepresentative (arg : CoordArg) : Option CoordVal := Id.run do
  match arg with
  | .single v => return (some v)
  | .sequence vs =>
    for v in vs do
      if v.countsAsFinite then
        return (some v)
    return none
  | .unsearched vs => return vs.head?
-- impl-end

-- proof-start
theorem correct_safeRepresentative : ∀ arg : CoordArg,
    problem_spec_safeRepresentative arg (implementation_safeRepresentative arg) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
