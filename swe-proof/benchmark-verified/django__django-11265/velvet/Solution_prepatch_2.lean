import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
--  logic over FREE INPUTS: the set of named filtered relations a query already
--  recognises, the name referenced by a lookup, and two structural properties of
--  a join (whether it preserves rows with no match on the other side, and whether
--  it was introduced by a named filtered relation and so carries its own filter).
--  The downstream query machinery these decisions feed into — name resolution,
--  join construction, SQL compilation — is UNCHANGED code the operations only
--  invoke, never reshape, so there is no callee contract to assume and nothing for
--  G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- A named filtered relation, identified abstractly: the decisions modeled here
   observe only whether such a name is PRESENT in a query's registry, never its
   concrete spelling, so a single opaque carrier suffices. -/
abbrev Name := Nat

/- Whether a lookup name can be resolved against a query. A lookup that names a
   concrete model field resolves directly; a lookup that names a filtered
   relation resolves only when that name is among the relations the query
   recognises. Modeling the resolution step lets the spec state the behaviour the
   issue describes: a reference to a named filtered relation must resolve in the
   subquery a negated lookup is rewritten into, instead of failing because the
   subquery does not recognise it. -/
def resolves (recognised : List Name) (name : Name) (isField : Bool) : Prop :=
  isField = true ∨ name ∈ recognised

@[grind] lemma resolves_def (recognised : List Name) (name : Name) (isField : Bool) :
    resolves recognised name isField = (isField = true ∨ name ∈ recognised) := rfl

/- Whether a leading join may be removed from a subquery as a simplification. It
   is safe to drop only when removing it can neither lose rows nor lose filtering:
   that is, only when the join does NOT preserve rows that have no match on the
   other side AND the join does NOT carry its own filter (a join introduced by a
   named filtered relation carries the relation's filter condition, so dropping it
   would silently discard that condition). -/
def joinRemovable (preservesUnmatchedRows : Bool) (carriesOwnFilter : Bool) : Bool :=
  (! preservesUnmatchedRows) && (! carriesOwnFilter)

@[grind] lemma joinRemovable_def (preservesUnmatchedRows carriesOwnFilter : Bool) :
    joinRemovable preservesUnmatchedRows carriesOwnFilter
      = ((! preservesUnmatchedRows) && (! carriesOwnFilter)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a negated lookup is rewritten into a nested subquery, that subquery must
   recognise the SAME named filtered relations the originating query did, so a
   lookup referencing one of them resolves there instead of failing. This models
   the registry the freshly-built subquery inherits from its originating query:
   it is exactly the originating query's registry (`outerRelations`), and every
   name in it is therefore recognised by the subquery — so a lookup naming any of
   those relations resolves (`resolves out n false`, a non-field name resolving by
   recognition). `outerRelations` is read-only (not `mut`): the originating
   query's registry is consulted, never mutated (directive 5). -/
method inheritedFilteredRelations (outerRelations : List Name) return (out : List Name)
  ensures out = outerRelations
  ensures ∀ n, n ∈ outerRelations → resolves out n false
  do
    -- impl-start
    let out := outerRelations
    return out
    -- impl-end

prove_correct inheritedFilteredRelations by
  loom_solve

/- Decide whether the leading join of a subquery may be removed as a
   simplification. Removal is permitted exactly when the join neither preserves
   rows that have no match on the other side nor carries its own filter; if it
   does either, the join must be kept (removing it would drop rows or drop a
   filter condition, changing the result). Both inputs are read-only (not `mut`):
   the join's properties are read and a fresh decision is produced (directive 5). -/
method canRemoveLeadingJoin (preservesUnmatchedRows : Bool) (carriesOwnFilter : Bool)
    return (out : Bool)
  ensures out = joinRemovable preservesUnmatchedRows carriesOwnFilter
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: the removal decision considers ONLY whether the
    -- join preserves unmatched rows (the LEFT-OUTER-JOIN case), ignoring whether
    -- the join carries its own filter. A leading inner join introduced by a named
    -- filtered relation (carriesOwnFilter = true, preservesUnmatchedRows = false)
    -- is then judged removable and its filter is silently dropped — the wrong
    -- result the issue reports. The frozen spec requires the `carriesOwnFilter`
    -- conjunct, so prove_correct MUST fail on exactly that case.
    let out := (! preservesUnmatchedRows)
    return out
    -- impl-end

prove_correct canRemoveLeadingJoin by
  loom_solve
