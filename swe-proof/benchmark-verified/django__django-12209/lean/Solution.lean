import Mathlib
-- imports-end

/-!
Routing a single-row persistence operation between two strategies: attempting an
in-place UPDATE of an existing row first, or going straight to a fresh INSERT.

When persisting one record the routine must decide whether to try updating an
existing row before falling back to inserting a new one. Five observable facts
drive the decision:

* whether the caller is replaying records verbatim — e.g. reloading a stored data
  set whose values (including the primary key) are supplied as-is, rather than an
  ordinary application-level save;
* whether the caller has explicitly demanded a fresh insert;
* whether the record is newly created (not yet known to originate from storage);
* whether the record's primary-key field supplies its own default value;
* whether a primary-key value is actually present.

The routine first determines an effective "force a fresh insert" verdict. The
verdict is forced on precisely when EITHER the caller already demanded a fresh
insert, OR all of the following hold together: the operation is an ordinary save
(not a verbatim replay), no fresh insert was already demanded, the record is
newly created, and its primary-key field carries a default. An in-place update is
then attempted exactly when a primary-key value is present AND the effective
verdict does not force a fresh insert.

The decisive subtlety: a verbatim replay must NOT have a fresh insert forced on it
merely because the key field has a default — such a replay carries an explicit key
and should still attempt to update the matching existing row. The behavior is
stated abstractly as an input→output relation; the implementation and correctness
proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every fact the decision
-- consults — whether the save is a verbatim replay, whether a fresh insert was
-- demanded, whether the record is new, whether the key field has a default, and
-- whether a key value is present — is supplied as a boolean input, and the
-- routing logic is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The routing decision for one single-row persistence operation: the effective
verdict on forcing a fresh insert, and whether an in-place update is attempted
first. -/
structure SaveDecision where
  forcesFresh : Bool
  attemptsUpdate : Bool
deriving Repr, DecidableEq

/-- The effective "force a fresh insert" verdict. It is set when the caller
already demanded a fresh insert, or when an ordinary (non-verbatim) save of a
newly created record whose key field has a default has no fresh insert already
demanded. -/
def forcesFreshInsert (verbatimLoad forceFresh isNew keyHasDefault : Bool) : Bool :=
  forceFresh || (!verbatimLoad && !forceFresh && isNew && keyHasDefault)
-- pure-end

-- post-conditions-start
/-- Input→output relation for routing one single-row persistence operation.

Inputs:
* `verbatimLoad`  — the operation is replaying caller-supplied records verbatim;
* `forceFresh`    — the caller explicitly demanded a fresh insert;
* `isNew`         — the record is newly created (not known to come from storage);
* `keyHasDefault` — the primary-key field supplies its own default value;
* `keySet`        — a primary-key value is present.

Both result components are pinned. The effective fresh-insert verdict is exactly
`forcesFreshInsert` of the four routing inputs, and an in-place update is
attempted exactly when a key value is present and the verdict does not force a
fresh insert. Neither component is left free. -/
def problem_spec_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
    (result : SaveDecision) : Prop :=
  result.forcesFresh = forcesFreshInsert verbatimLoad forceFresh isNew keyHasDefault ∧
  result.attemptsUpdate = (keySet && !result.forcesFresh)
-- post-conditions-end

-- impl-start
def implementation_saveDecision (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool)
    : SaveDecision := Id.run do
  let mut forced := forceFresh
  -- Skip the update attempt (force a fresh insert) when adding a newly created
  -- record whose key field has a default — but only for an ordinary save, never
  -- for a verbatim replay carrying an explicit key.
  if (!verbatimLoad) && (!forced) && isNew && keyHasDefault then
    forced := true
  -- An in-place update is attempted only when a key value is present and a fresh
  -- insert is not being forced.
  let attemptsUpdate := keySet && !forced
  return { forcesFresh := forced, attemptsUpdate := attemptsUpdate }
-- impl-end

-- proof-start
theorem correct_saveDecision :
    ∀ (verbatimLoad forceFresh isNew keyHasDefault keySet : Bool),
      problem_spec_saveDecision verbatimLoad forceFresh isNew keyHasDefault keySet
        (implementation_saveDecision verbatimLoad forceFresh isNew keyHasDefault keySet) := by
  intro verbatimLoad forceFresh isNew keyHasDefault keySet
  cases verbatimLoad <;> cases forceFresh <;> cases isNew <;>
    cases keyHasDefault <;> cases keySet <;>
    exact ⟨rfl, rfl⟩
-- proof-end
