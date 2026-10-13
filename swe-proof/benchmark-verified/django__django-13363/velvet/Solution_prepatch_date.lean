import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The effective timezone name used when casting a stored datetime to a date or
   to a time value for a database backend.

   The resolution depends on three observable inputs:
   * `tzAware`  — whether the surrounding configuration treats stored datetimes
     as timezone-aware. When it does not, no zone name applies and the result is
     absent.
   * `explicitZone` — the name of a caller-supplied target zone, if one was
     supplied (`none` when the caller supplied no zone).
   * `currentZone` — the name of the ambient/active zone, used as the fallback
     when no explicit zone was supplied.

   When zone-awareness is in effect, a caller-supplied zone takes precedence over
   the ambient zone; otherwise the ambient zone name is used. The key obligation
   pinned here is that an explicitly supplied zone is honoured rather than
   discarded in favour of the ambient one. -/
@[grind] def resolveZoneName (tzAware : Bool) (explicitZone : Option String)
    (currentZone : String) : Option String :=
  if tzAware then
    match explicitZone with
    | none   => some currentZone
    | some z => some z
  else
    none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The timezone name selected when casting a stored datetime down to a calendar
   date for the database. See `resolveZoneName`: a caller-supplied target zone is
   honoured; absent one, the ambient zone applies; absent zone-awareness, no zone
   name applies. -/
method dateCastZoneName (tzAware : Bool) (explicitZone : Option String)
    (currentZone : String) return (out : Option String)
  ensures out = resolveZoneName tzAware explicitZone currentZone
  do
    -- impl-start
    -- Pre-image skeleton: when zone-awareness is in effect, the ambient zone
    -- name is used unconditionally, discarding any caller-supplied zone. The
    -- frozen spec honours the explicit zone, so prove_correct MUST fail.
    if tzAware then
      return some currentZone
    else
      return none
    -- impl-end

prove_correct dateCastZoneName by
  loom_solve
  all_goals simp_all [resolveZoneName]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The timezone name selected when casting a stored datetime down to a wall-clock
   time for the database. Same resolution as the date cast (`resolveZoneName`): a
   caller-supplied target zone is honoured over the ambient one. -/
method timeCastZoneName (tzAware : Bool) (explicitZone : Option String)
    (currentZone : String) return (out : Option String)
  ensures out = resolveZoneName tzAware explicitZone currentZone
  do
    -- impl-start
    if tzAware then
      match explicitZone with
      | none   => return some currentZone
      | some z => return some z
    else
      return none
    -- impl-end

prove_correct timeCastZoneName by
  loom_solve
  all_goals simp_all [resolveZoneName]
