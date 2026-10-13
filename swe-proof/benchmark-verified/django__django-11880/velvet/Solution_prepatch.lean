import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No module-level `axiom` is needed. The only outside behavior the clone routine
   relies on is that of the standard copy helpers it calls to duplicate one of the
   field's attributes. Each such helper hands back a BRAND-NEW object — one
   distinct from its argument. For an attribute whose type defines value equality
   (a table of entries, a collection of items) the new object additionally reads
   back the same as the one it was given; for an attribute that is an opaque
   component with no value equality, distinctness is the whole of what the helper
   guarantees and nothing more may be assumed of it.

   Those helpers are UNCHANGED library/builtin behavior, so rather than being
   re-implemented they are modeled as inputs: the object each helper produced is
   taken as a parameter of the routine, constrained by exactly that helper's
   guarantee (`require`, below) and by nothing else. This is the weakest sufficient
   contract, sound by construction, and it is universally quantified — so no
   claim is made that a helper answers the same way twice, only that whatever it
   answers meets its guarantee. Each contract is checked against its real callee
   by G-AX (axiom_check.py). -/
-- axioms-end

-- pure-start
/- A runtime object, observed through exactly the two facets that matter here:
   * `ref`     — its identity (the answer to "is this the same object as that?").
                 Two objects are the SAME object iff their `ref`s are equal.
   * `payload` — its observable CONTENTS, for an attribute whose type defines
                 value equality: two such objects read back the same iff their
                 `payload`s are equal.
   The two facets are INDEPENDENT: two objects can be distinct (`ref`s differ) and
   still hold equal contents (`payload`s equal), which is precisely what an
   independent copy of a value-typed attribute is, and neither facet can be
   recovered from the other. See mapping.md §2 for the bijection to the repository
   value space. -/
structure Obj where
  ref     : Nat
  payload : Nat
deriving Inhabited, DecidableEq

/- A field, restricted to what the clone routine can be observed to do:
   * the three attributes it gives individual treatment — the opaque rendering
     component, the table of override messages, the validator collection;
   * `carried` — the AGGREGATE of everything else the field holds (its class and
     every remaining attribute), observed as one object because the routine never
     inspects or re-points any of it. The shallow duplication is what supplies it,
     and a shallow duplication hands the clone the source's OWN objects, so the
     faithful observation is one of IDENTITY: the clone's carried aggregate is the
     same object as the source's, not merely an equal one. -/
structure FormField where
  widget        : Obj
  errorMessages : Obj
  validators    : Obj
  carried       : Obj
deriving Inhabited, DecidableEq

/- `b` is a DISTINCT object from `a` — not the same object. This is the whole of
   what a copy helper guarantees about an OPAQUE component: such a component's
   type defines no value equality, so there is no readable content to compare and
   claiming content-equality of its copy would assert more than the helper
   delivers. -/
@[reducible] def freshDistinct (b a : Obj) : Prop := b.ref ≠ a.ref

/- `b` is an INDEPENDENT copy of `a`: a DISTINCT object (`b.ref ≠ a.ref` — not the
   same object) that ALSO reads back the same (`b.payload = a.payload`). This is
   what a copy helper guarantees for an attribute whose type DOES define value
   equality. Both conjuncts are load-bearing and neither implies the other:
   * distinctness ALONE is met by any unrelated object that happens to be new, so
     on its own it does not say the copy carries anything of the original;
   * content-equality ALONE is met by the original itself, so on its own it does
     not say the copy is independent of it. -/
@[reducible] def freshCopy (b a : Obj) : Prop := b.ref ≠ a.ref ∧ b.payload = a.payload

-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce an independent clone of a form field.

   A field carries several attributes that are objects in their own right — its
   opaque rendering component, its table of override messages, its validator
   collection. A shallow duplication of the field hands the clone the very same
   objects the source holds, so a later change reached through one field is
   observed through the other. The desired behavior is that the clone be
   independent of the source in EVERY one of these attributes.

   Independence is achieved by calling, for each attribute, the copy helper for
   that attribute and INSTALLING WHAT THAT HELPER RETURNED in the clone's
   corresponding slot. The objects the helpers returned are the parameters
   `widgetCopy`, `messagesCopy` and `validatorsCopy`; each is constrained by
   exactly the guarantee its helper delivers and by nothing more:
   * `widgetCopy` — a DISTINCT object (the rendering component is opaque: its type
     defines no value equality, so a copy of it reads back equal to nothing, not
     even to itself, and no content guarantee is available to assume);
   * `messagesCopy`, `validatorsCopy` — DISTINCT objects that also read back the
     same as the source's (these attributes' types do define value equality).

   The obligation on the clone is stated in two layers, and both are needed.
   * DERIVATION. Each of the clone's three slots must hold PRECISELY the object
     the corresponding helper returned. This is the substance of the routine: the
     slot is filled by the helper's answer, with nothing interposed. It forbids a
     routine that substitutes some other object, that rebuilds one from scratch
     instead of copying, or that takes the helper's answer and then alters it
     before installing it — every one of those leaves the clone rendering,
     reporting or validating differently from the field it was cloned from, and
     for the opaque component it is the ONLY thing that can forbid them, since
     that component's contents are not readable and so cannot be compared.
   * INDEPENDENCE. Each of the clone's three slots must additionally be a
     DISTINCT object from the source's, and for the two attributes whose types
     define value equality it must read back the same. Stated separately so the
     property the routine exists to deliver is visible in the contract on its
     own terms rather than only through the parameters.
   * CARRIED-OVER STATE. Everything the field holds BESIDES those three
     attributes — its class and every remaining attribute — must be the source's
     OWN, not a reconstruction of it. The routine obtains it by duplicating the
     field shallowly, and a shallow duplication hands over the very same objects,
     so the faithful statement is one of IDENTITY (`result.carried =
     source.carried`) rather than of equal contents. This is what forbids a
     routine that BUILDS a new field and fills in the three copies instead of
     duplicating the one it was given: such a routine can reproduce any amount of
     equal-looking state, but it cannot hand back the source's own aggregate, and
     the clone it returns is not even of the field's own class.

   `source` is the read-only field being cloned (not `mut`): it is observed and
   never altered (directive 5); the clone is a fresh value built from it. -/
method deepCopyField (source : FormField)
    (widgetCopy : Obj) (messagesCopy : Obj) (validatorsCopy : Obj)
    return (result : FormField)
  require freshDistinct widgetCopy     source.widget
  require freshCopy     messagesCopy   source.errorMessages
  require freshCopy     validatorsCopy source.validators
  ensures freshDistinct result.widget        source.widget
  ensures freshCopy     result.errorMessages source.errorMessages
  ensures freshCopy     result.validators    source.validators
  ensures result.widget        = widgetCopy
  ensures result.errorMessages = messagesCopy
  ensures result.validators    = validatorsCopy
  ensures result.carried        = source.carried
  do
    -- impl-start
    -- Skeleton under audit: the shallow duplication is followed by installing the
    -- copy of the opaque rendering component and the copy of the validator
    -- collection, but the table of override messages is LEFT AS THE SHARED
    -- REFERENCE the shallow duplication handed over (no copy of it is installed).
    let mut result := source
    result := { result with widget := widgetCopy }
    -- (no copy of the override-message table is installed here)
    result := { result with validators := validatorsCopy }
    return result
    -- impl-end

prove_correct deepCopyField by
  loom_solve
