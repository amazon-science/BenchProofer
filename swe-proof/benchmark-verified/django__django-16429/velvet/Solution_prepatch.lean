import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The modeled behavior is a
   pure data-flow that builds a shifted reference instant from the components of
   a source instant and a whole-unit (years, months) offset; every component is
   read directly from the inputs, nothing is delegated to an unchanged foreign
   callee (mapping.md §3). G-AX therefore has nothing to check. -/
-- axioms-end

-- pure-start
/- An instant on the calendar, separated into the components a later difference
   is computed from. `zone` records the time-zone designation the instant is
   expressed against: `none` is a floating instant (no designation), `some k` is
   an instant anchored to designation `k`. Two instants can only be compared /
   subtracted when they share the same designation status — a floating instant
   and an anchored one are not on a common timeline. -/
structure Instant where
  y    : Nat
  mo   : Nat
  d    : Nat
  h    : Nat
  mi   : Nat
  s    : Nat
  zone : Option Nat
deriving DecidableEq, Repr, Inhabited

/- The number of days in a (1-indexed) calendar month, the constant table used
   to clamp a day-of-month onto a target month. February is the common-year length;
   the clamp only ever caps an out-of-range day, so the leap-year case is not
   distinguished here. -/
def monthLen : Nat → Nat
  | 1  => 31 | 2  => 28 | 3  => 31 | 4  => 30 | 5  => 31 | 6  => 30
  | 7  => 31 | 8  => 31 | 9  => 30 | 10 => 31 | 11 => 30 | 12 => 31
  | _  => 30

/- Build the reference instant obtained by shifting `base` forward by whole
   `years` and `months`. The shifted month is normalized back into 1..12,
   carrying into the year when it overflows; the day-of-month is clamped to the
   target month's length so an end-of-month source never names a non-existent
   day; the hour/minute/second are carried across verbatim. Crucially the
   reference is expressed against the SAME time-zone designation as `base`
   (`zone := base.zone`): the shifted reference must lie on the same timeline as
   the source so that a later difference between the reference and another
   instant on that timeline is well-defined. -/
def shiftReference (base : Instant) (years months : Nat) : Instant :=
  let py  := base.y + years
  let pm  := base.mo + months
  let py' := if pm > 12 then py + 1 else py
  let pm' := if pm > 12 then pm - 12 else pm
  { y    := py',
    mo   := pm',
    d    := min (monthLen pm') base.d,
    h    := base.h,
    mi   := base.mi,
    s    := base.s,
    zone := base.zone }

@[grind] lemma shiftReference_def (base : Instant) (years months : Nat) :
    shiftReference base years months =
      (let py  := base.y + years
       let pm  := base.mo + months
       let py' := if pm > 12 then py + 1 else py
       let pm' := if pm > 12 then pm - 12 else pm
       { y    := py',
         mo   := pm',
         d    := min (monthLen pm') base.d,
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
         zone := base.zone : Instant }) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the reference instant used to measure the leftover span after whole
   years and months have been accounted for. `base` is read-only (not `mut`):
   the builder only reads its components and returns a fresh instant. The
   reference is the source shifted forward by `years`/`months`, normalized onto
   a real calendar day, and — the property the leftover-span measurement
   depends on — expressed against the SAME time-zone designation as `base`, so
   the two lie on a common timeline. The whole-unit offset is the result of a
   division by twelve, so `months ≤ 11`; this site is only reached when at least
   one whole unit elapsed. -/
method buildShiftedReference (base : Instant) (years : Nat) (months : Nat) return (out : Instant)
  require 1 ≤ base.mo ∧ base.mo ≤ 12
  require months ≤ 11
  require 0 < years ∨ 0 < months
  ensures out = shiftReference base years months
  do
    -- impl-start
    -- Pre-image skeleton: the reference instant is built from the source's
    -- date/time components ONLY; the time-zone designation is left unset
    -- (`zone := none`), so an anchored source yields a floating reference. The
    -- frozen spec requires `zone := base.zone`, so prove_correct MUST fail.
    let py  := base.y + years
    let pm  := base.mo + months
    let py' := if pm > 12 then py + 1 else py
    let pm' := if pm > 12 then pm - 12 else pm
    let out : Instant :=
      { y    := py',
        mo   := pm',
        d    := min (monthLen pm') base.d,
        h    := base.h,
        mi   := base.mi,
        s    := base.s,
        zone := none }
    return out
    -- impl-end

prove_correct buildShiftedReference by
  loom_solve
