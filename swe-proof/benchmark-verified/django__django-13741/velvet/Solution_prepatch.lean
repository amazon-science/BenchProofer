import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The two presentation hooks a generic form field already provides for a field
   the user is not allowed to edit. They are UNCHANGED, pre-existing behaviour
   of the base field class; here they are axiomatized as the weakest contracts
   the desired behaviour relies on (provenance + executable soundness check:
   mapping.md / axiom_check.py, G-AX).

   `noEditChange initial data` — whether the field reports that its submitted
   `data` differs from its stored `initial`, as a function of whether the field
   is non-editable. The single fact consumed: a non-editable field NEVER reports
   a change, whatever the submitted and stored values are.

   `noEditValue data initial` — the value the field exposes when rendering a
   bound form, as a function of whether the field is non-editable. The single
   fact consumed: a non-editable field always exposes its stored `initial`,
   discarding the submitted `data`. -/
axiom noEditChange : Bool → List Char → List Char → Bool
axiom noEditChange_locked : ∀ (initial data : List Char),
    noEditChange true initial data = false

axiom noEditValue : Bool → List Char → List Char → List Char
axiom noEditValue_locked : ∀ (data initial : List Char),
    noEditValue true data initial = initial

@[grind] lemma noEditChange_locked' (initial data : List Char) :
    noEditChange true initial data = false := noEditChange_locked initial data
@[grind] lemma noEditValue_locked' (data initial : List Char) :
    noEditValue true data initial = initial := noEditValue_locked data initial
-- axioms-end

-- pure-start
/- The non-editability flag a freshly constructed read-only credential-digest
   field ends up with.

   Construction may receive an explicit flag (`some true` / `some false`); if the
   caller leaves it unspecified (`none`), the field supplies its own default. The
   desired behaviour is that, unspecified, such a field is non-editable: its
   stored value is shown but cannot be changed by the user, so a tampered
   submission is ignored in favour of the stored value. An explicitly supplied
   flag is honoured verbatim (it is not overridden). -/
@[grind] def lockedDefault (userFlag : Option Bool) : Bool :=
  userFlag.getD true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the non-editability flag with which a read-only credential-digest
   field is constructed.

   Desired behaviour: when the caller does not specify the flag, the field is
   non-editable by default, so the stored value is displayed but protected from
   user edits; an explicitly specified flag is honoured unchanged.

   Two consequences of defaulting to non-editable are pinned as well (the reason
   no bespoke change-suppression hooks are needed on such a field): a field that
   is non-editable by this default never reports a change between stored and
   submitted values, and always exposes its stored value when bound. These rest
   on the field framework's pre-existing non-editable handling (the `noEdit*`
   contracts).

   `userFlag` is read-only (not `mut`): construction reads the caller's optional
   flag and returns the resulting flag; it mutates nothing (directive 5). -/
method readonlyDigestFieldLocked (userFlag : Option Bool) return (out : Bool)
  ensures out = lockedDefault userFlag
  ensures ∀ (initial data : List Char),
    noEditChange (lockedDefault none) initial data = false
  ensures ∀ (data initial : List Char),
    noEditValue (lockedDefault none) data initial = initial
  do
    -- impl-start
    -- Pre-image skeleton: when the caller leaves the flag unspecified, fall back
    -- to the generic field default of EDITABLE (false) rather than locking the
    -- field. The frozen spec requires `lockedDefault` (none ⇒ true), so
    -- prove_correct MUST fail on the `userFlag = none` case.
    let out := userFlag.getD false
    return out
    -- impl-end

prove_correct readonlyDigestFieldLocked by
  loom_solve
