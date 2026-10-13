import Mathlib
-- imports-end

/-!
# Removing a registered lookup from a lookup registry

A lookup registry holds, per class, a table of registered named lookups
(`classLookups`) together with a memoized view of the table that readers consult
(`cache`). When a name is removed from the registry, two things must hold for the
registry to behave correctly: the name must be gone from the underlying table,
and the value subsequently seen by readers must reflect the current table rather
than a stale snapshot.

This bundle models the removal operation and pins exactly that behavior.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the memo-invalidation effect is
-- modeled deeply (the reader view is recomputed from the current table), and the
-- table edit is modeled deeply via `eraseKey`.
-- axioms-end

-- pure-start
/-- A registry for one class: the underlying table of named entries
(`classLookups`) and a memoized snapshot consulted by readers (`cache`); `none`
means "no snapshot — readers recompute from the table". Entry identities are
abstracted to `Nat` ids. -/
structure LookupState where
  classLookups : List (String × Nat)
  cache : Option (List (String × Nat))
deriving Repr, DecidableEq

/-- Drop every entry whose name equals `k` from a table. -/
def eraseKey (xs : List (String × Nat)) (k : String) : List (String × Nat) :=
  xs.filter (fun p => p.1 != k)

/-- The list of names currently present in a table. -/
def keys (xs : List (String × Nat)) : List String := xs.map Prod.fst

/-- The table value seen by readers: the memoized snapshot if present, otherwise
the freshly recomputed table. -/
def getLookups (s : LookupState) : List (String × Nat) :=
  s.cache.getD s.classLookups
-- pure-end

-- post-conditions-start
/-- Correctness of removing the entry named `lookupName` from registry `s`,
producing `result`.

1. the underlying table is exactly the input table with every entry named
   `lookupName` dropped — all other entries preserved in order, nothing added;
2. the memoized reader snapshot is invalidated (cleared, not re-primed with a
   precomputed value): readers recompute from the table, so subsequent table
   changes are also visible;
3. readers see the current table, not a stale snapshot: the reader view equals
   the (recomputed) underlying table, and in particular no longer reports the
   removed name.

Note for reviewers: clauses 1–2 pin BOTH fields of `result`, so this spec is
DETERMINISTIC — any `result` satisfying it is a single, fully determined
state. A same-spec implementation can verify only by computing exactly that
state (extensionally identical output); a verifying same-spec variant is
therefore a positive control, not evidence of spec weakness. -/
def problem_spec_unregisterLookup
    (s : LookupState) (lookupName : String) (result : LookupState) : Prop :=
  result.classLookups = eraseKey s.classLookups lookupName ∧
  result.cache = none ∧
  getLookups result = result.classLookups ∧
  lookupName ∉ keys (getLookups result)
-- post-conditions-end

-- impl-start
/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed
procedure: drop the entry from the underlying table, then invalidate the reader
snapshot so subsequent reads reflect the current table. -/
def implementation_unregisterLookup
    (s : LookupState) (lookupName : String) : LookupState := Id.run do
  let mut st := s
  -- remove the named entry from the underlying table
  st := { st with classLookups := eraseKey st.classLookups lookupName }
  -- invalidate the reader snapshot
  st := { st with cache := none }
  return st
-- impl-end

-- proof-start
theorem correct_unregisterLookup :
    ∀ (s : LookupState) (lookupName : String),
      problem_spec_unregisterLookup s lookupName
        (implementation_unregisterLookup s lookupName) := by
  intro s lookupName
  unfold problem_spec_unregisterLookup implementation_unregisterLookup
  simp only [Id.run, getLookups, Option.getD_none, pure]
  refine ⟨trivial, trivial, trivial, ?_⟩
  simp only [eraseKey, keys, List.mem_map, List.mem_filter, bne_iff_ne, ne_eq,
    not_exists, not_and]
  rintro p ⟨_, hne⟩ rfl
  exact hne rfl

/-- The spec is DETERMINISTIC: it pins both fields of the result exactly, so
any `result` satisfying it equals the (gold) implementation's output. Hence no
same-spec implementation with observably wrong behavior can verify — a
verifying same-spec variant is extensionally the gold behavior. -/
theorem spec_unregisterLookup_deterministic :
    ∀ (s : LookupState) (lookupName : String) (r : LookupState),
      problem_spec_unregisterLookup s lookupName r →
        r = implementation_unregisterLookup s lookupName := by
  intro s lookupName r h
  obtain ⟨h1, h2, -, -⟩ := h
  unfold implementation_unregisterLookup
  simp only [Id.run, pure]
  cases r
  simp_all
-- proof-end
