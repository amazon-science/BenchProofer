import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The SQL expression is built entirely from the four
--  inputs — a pure string computation modeled in full below; nothing is
--  delegated to an unchanged callee.)
-- axioms-end

-- pure-start
/- The database read converts a stored timestamp so that a later date/time
   comparison is evaluated in the time zone the query expects. Two time-zone
   names are in play: the one the stored values are kept in (`storedZone`) and
   the one the query is evaluated against (`queryZone`). The conversion is only
   meaningful when time-zone support is active AND the two zones actually
   differ; when they coincide, or support is off, the field expression is used
   unchanged so no zone table is required. When a conversion IS needed the
   field expression is wrapped to re-interpret it from the stored zone into the
   query zone:  CONVERT_TZ(<expr>, '<storedZone>', '<queryZone>').

   `active` carries whether time-zone support is on; `expr` is the field
   expression; `queryZone` and `storedZone` are the target and source zone
   names. The result is a fresh expression. -/
def tzAdjustedExpr
    (active : Bool) (expr queryZone storedZone : List Char) : List Char :=
  if active ∧ storedZone ≠ queryZone then
    "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
      ++ "', '".toList ++ queryZone ++ "')".toList
  else
    expr

/- Single-step unfold so `loom_solve` can discharge the postcondition. -/
@[grind] lemma tzAdjustedExpr_def
    (active : Bool) (expr queryZone storedZone : List Char) :
    tzAdjustedExpr active expr queryZone storedZone =
      (if active ∧ storedZone ≠ queryZone then
        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
          ++ "', '".toList ++ queryZone ++ "')".toList
       else expr) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the field expression used to read a stored timestamp for a date/time
   comparison evaluated in the query's time zone. When time-zone support is
   active and the stored zone differs from the query zone, the expression is
   wrapped to re-interpret it from the stored zone into the query zone; in every
   other case (support off, or the two zones identical) the original expression
   is returned verbatim — avoiding a needless conversion and the zone tables it
   would require. All four inputs are read-only (none declared `mut`); the
   builder only reads them (directive 5) and returns a fresh expression. -/
method buildTzAdjustedExpr
    (active : Bool) (expr : List Char) (queryZone : List Char) (storedZone : List Char)
    return (out : List Char)
  ensures out = tzAdjustedExpr active expr queryZone storedZone
  do
    -- impl-start
    -- Pre-image skeleton: whenever support is active the expression is ALWAYS
    -- wrapped, with a hardcoded fixed origin zone ("UTC") rather than the
    -- stored zone, and with no skip when the two zones coincide. The frozen
    -- spec requires tzAdjustedExpr (origin = storedZone, identity when the
    -- zones match), so prove_correct MUST fail.
    let out : List Char :=
      if active then
        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ "UTC".toList
          ++ "', '".toList ++ queryZone ++ "')".toList
      else
        expr
    return out
    -- impl-end

prove_correct buildTzAdjustedExpr by
  loom_solve
