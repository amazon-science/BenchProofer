import Velvet.Std
-- imports-end

-- Total correctness: the modeled conversion is a straight-line kind dispatch
-- over a finite array that always terminates and returns, so a diverging
-- implementation must NOT satisfy the spec (partial correctness would admit
-- it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two unchanged conversion callees this slice relies on
   — the epoch-relative datetime→number conversion (`epochCount`) and the direct
   float cast of a duration (`durationCast`) — are modeled DEEPLY in the `pure`
   region and validated == the real callees by G-AX (A-references, mapping.md
   §3), so neither carries a module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The element kind of an array's values, in the three mutually-exclusive shapes
   this conversion distinguishes: `datetime` (absolute time points), `duration`
   (timedeltas — relative spans, the kind the problem statement is about), and
   `numeric` (values that are already plain numbers). -/
inductive Kind where
  | datetime
  | duration
  | numeric
  deriving Inhabited, DecidableEq

/- A typed array: an element-kind tag together with the underlying integer
   representation of its values (for time kinds, the signed-64-bit integer count
   in the base resolution; for numeric arrays, the integer-valued payload). Only
   the kind and that integer carrier are observable to the conversion. -/
structure TypedArr where
  kind : Kind
  raw  : Array Int
  deriving Inhabited

/- The one reserved count in a time array's signed-64-bit integer carrier that
   denotes a MISSING time value ("not-a-time") rather than a real instant/span:
   the minimum representable signed-64-bit value. -/
def missingCount : Int := -9223372036854775808

/- A converted numeric value: either an exact integer-valued number, or the
   floating-point not-a-number that a missing datetime converts to. -/
inductive NumVal where
  | num (n : Int)
  | nan
  deriving Inhabited, DecidableEq

/- Failure of the epoch-relative conversion: it is undefined on a duration
   value. A duration is a relative span with no position relative to an absolute
   epoch, so re-expressing it against a reference epoch is ill-typed. -/
inductive ConvErr where
  | illTypedForDuration
  deriving Inhabited, DecidableEq

/- The epoch-relative datetime→number conversion (unchanged callee; A-reference,
   deep model — mapping.md §3.1). Re-expressing an absolute datetime array as a
   count relative to a reference epoch in the base resolution yields exactly that
   integer count — except that a MISSING datetime (the reserved count) has no
   distance to the epoch and converts to not-a-number. The operation is
   undefined on a duration value (no absolute epoch position), and it is not
   reached on an already-numeric array. -/
def epochCount (t : TypedArr) : Except ConvErr (Array NumVal) :=
  match t.kind with
  | .datetime =>
      Except.ok (t.raw.map fun i =>
        if i = missingCount then NumVal.nan else NumVal.num i)
  | _         => Except.error .illTypedForDuration

/- The direct float cast of a duration array (unchanged callee; A-reference, deep
   model — mapping.md §3.2). Casting a duration to its floating-point numeric
   value preserves the signed-64-bit integer count in the base resolution exactly
   — including the reserved missing-value count, which this direct cast does NOT
   special-case: it comes through as that count's plain numeric value. -/
def durationCast (t : TypedArr) : Array NumVal := t.raw.map NumVal.num

/- The intended numeric representation of a typed array:
     * a datetime array is re-expressed against a reference epoch (`epochCount`),
       its missing values becoming not-a-number;
     * a duration array is cast directly to its numeric value (`durationCast`);
     * an already-numeric array passes through unchanged.
   Both time kinds therefore yield a well-defined numeric array — the duration
   kind via the direct cast, NOT via the epoch conversion that is ill-typed on
   it. -/
def toNumericSpec (t : TypedArr) : Except ConvErr (Array NumVal) :=
  match t.kind with
  | .datetime => epochCount t
  | .duration => Except.ok (durationCast t)
  | .numeric  => Except.ok (t.raw.map NumVal.num)

@[grind] lemma toNumericSpec_datetime (t : TypedArr) (h : t.kind = .datetime) :
    toNumericSpec t = epochCount t := by simp [toNumericSpec, h]
@[grind] lemma toNumericSpec_duration (t : TypedArr) (h : t.kind = .duration) :
    toNumericSpec t = Except.ok (durationCast t) := by simp [toNumericSpec, h]
@[grind] lemma toNumericSpec_numeric (t : TypedArr) (h : t.kind = .numeric) :
    toNumericSpec t = Except.ok (t.raw.map NumVal.num) := by simp [toNumericSpec, h]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method toNumeric (t : TypedArr) return (out : Except ConvErr (Array NumVal))
  ensures out = toNumericSpec t
  do
    -- impl-start
    -- Pre-image skeleton: BOTH time kinds — datetime AND duration — are routed
    -- through the single epoch-relative conversion, with only the already-numeric
    -- kind passing through. The frozen spec requires a duration array to be cast
    -- directly to its numeric value (it has no absolute epoch position, so the
    -- epoch conversion is ill-typed on it), so prove_correct MUST fail.
    let isTimeKind : Bool :=
      match t.kind with
      | .datetime => true
      | .duration => true
      | .numeric  => false
    let out := if isTimeKind then epochCount t
               else Except.ok (t.raw.map NumVal.num)
    return out
    -- impl-end

prove_correct toNumeric by
  loom_solve
