import Mathlib
-- imports-end

/-!
Discarding the memoized results held by an application registry.

A registry memoizes the answers of two independent query methods in two separate
result caches:

  * a name-lookup cache, mapping a queried string to the resolved name (or to
    "no such name"), and
  * an entity-list cache, mapping a pair of inclusion flags to the list of
    registered entities those flags select.

The registry also carries a readiness flag that governs an auxiliary refresh of
per-entity metadata. That refresh touches a separate metadata layer and is not
part of the two result caches.

The "discard" operation exists so that callers can return the registry to a
clean state whenever the underlying registry contents may have changed: after it
runs, *every* memoized result must be gone, so that the next query is recomputed
from the current registry contents rather than served from a stale cache. The
readiness flag is only consulted, never altered.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The registry's cache state and its
-- readiness flag enter as plain data (lists of memoized key/value pairs and a
-- boolean), and the only operation performed is discarding the memoized
-- entries, modeled directly below. Hence no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The cache state of an application registry, modeled by the two independent
result caches it memoizes plus its readiness flag.

  * `nameLookupCache`: memoized answers of the name-lookup query — each entry
    pairs the queried string with the resolved name (`some n`) or "no such
    name" (`none`).
  * `entityListCache`: memoized answers of the entity-list query — each entry
    pairs the two inclusion flags with the selected entity names.
  * `ready`: the readiness flag (consulted by the auxiliary metadata refresh,
    never modified by the discard operation). -/
structure CacheRegistry where
  nameLookupCache : List (String × Option String)
  entityListCache : List ((Bool × Bool) × List String)
  ready : Bool
-- pure-end

-- post-conditions-start
/-- The discard operation fully pins the resulting registry state to its input:

  * BOTH result caches are empty afterwards (`nameLookupCache = []` and
    `entityListCache = []`) — no memoized result of either query may survive;
  * the readiness flag is unchanged (frame: the operation only consults it). -/
def problem_spec_clearCaches (st : CacheRegistry) (result : CacheRegistry) : Prop :=
  result.nameLookupCache = [] ∧
  result.entityListCache = [] ∧
  result.ready = st.ready
-- post-conditions-end

-- impl-start
def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do
  let mut s := st
  -- discard the name-lookup cache
  s := { s with nameLookupCache := [] }
  -- discard the entity-list cache
  s := { s with entityListCache := [] }
  -- a readiness-gated refresh of per-entity metadata runs here; it touches a
  -- separate metadata layer and leaves both result caches (and `ready`) intact
  return s
-- impl-end

-- proof-start
theorem correct_clearCaches :
    ∀ (st : CacheRegistry),
      problem_spec_clearCaches st (implementation_clearCaches st) := by
  intro st
  refine ⟨rfl, rfl, rfl⟩
-- proof-end
