# refinement.md — django__django-15569

Maps every op in `implementation_unregisterLookup` to its `patch.diff`
counterpart in `RegisterLookupMixin._unregister_lookup`. Tags: **R** (type
refinement), **A-consumed**, **A-reference**, **I** (identical concrete op).

| # | Lean impl op | Python counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut st := s` | the classmethod operates on `cls` state (`class_lookups` dict + memoized `get_lookups`) | R | the mutable object state `{class_lookups dict, lru-cache}` ↔ `LookupState {classLookups, cache}` (bijection in mapping.md) |
| 2 | `st := { st with classLookups := eraseKey st.classLookups lookupName }` | `del cls.class_lookups[lookup_name]` (line 219) | R | `del dict[name]` (remove key) ↔ `eraseKey` (drop pairs with that key). `lookup_name` defaulting (`lookup_name = lookup.lookup_name`) happens before; the name string is the input. |
| 3 | `st := { st with cache := none }` | `cls._clear_cached_lookups()` (the ADDED line) | R | the memo invalidation. Real callee walks `subclasses(cls)` calling `get_lookups.cache_clear()`; observable effect is "reader memo is empty", modeled deeply as `cache := none`. NOT axiomatized (the patch ADDS this call — it is the fix). |
| 4 | `return st` | implicit return of the classmethod | I | — |

No A-consumed and no A-reference rows: every op is R or I. The fix's added
operation (op 3) is modeled deeply (`cache := none`), so its callee
`_clear_cached_lookups` is neither consumed as an axiom nor validated as an
A-reference. `conf_skip = false` (the impl region is all-R/I, mechanically
shadowable in Python).

## Pre-patch (the bug)
`Solution_prepatch.lean` drops op 3 (`cache := none`) — exactly the missing
`cls._clear_cached_lookups()` call. After removal the reader memo (`cache`) can
still hold the old snapshot containing `lookupName`, so spec clause 2
(`result.cache = none`), clause 3 (`getLookups result = result.classLookups`)
and clause 4 (`lookupName ∉ keys (getLookups result)`) all fail ⇒ `correct_*`
is unprovable. This is the F2P `test_lookups_caching` assertion
`assertNotIn("exactly", field.get_lookups())`.

## Spec strengthening (P1 repair, 2026-08-03)
The original postconditions pinned only table MEMBERSHIP and the derived reader
view; they never constrained `result.cache` itself. That admitted a wrong impl
that RE-PRIMES the memo with a precomputed snapshot (`cache := some (eraseKey
… )`) instead of clearing it — same-spec-verifying but not the real fix
(`_clear_cached_lookups()` empties the lru-cache; it does not re-prime it), and
also admitted duplicated/reordered tables (membership-iff ignores multiplicity
and order). Strengthened, faithful to the real post-patch behavior:
- clause 1: `result.classLookups = eraseKey s.classLookups lookupName` exactly
  (Python dicts are insertion-ordered and `del` preserves the order of the
  remaining entries — exact-list equality is real behavior, not over-tightening);
- clause 2: `result.cache = none` (memo CLEARED, per mapping.md `none` ⇔
  lru-cache empty/cleared — exactly what `cls._clear_cached_lookups()` does).

## Spec determinism (P1 repair, 2026-08-03, second pass)
The strengthened clauses 1–2 pin BOTH fields of the result record, so the spec
is DETERMINISTIC: `spec_unregisterLookup_deterministic` (proved in
`Solution.lean`, axioms `[propext]`) shows any `result` satisfying
`problem_spec_unregisterLookup s lookupName result` equals
`implementation_unregisterLookup s lookupName`. Consequently NO observably
wrong same-spec implementation can verify — any verifying same-spec variant is
extensionally the gold behavior (e.g. a direct structure literal
`{ classLookups := eraseKey s.classLookups lookupName, cache := none }` is a
positive control, not a counterexample; its faithful patch IS the gold patch
and resolves). A prior audit round listed exactly such a gold-equivalent
restatement in its attack set and the mechanized re-check scored it as a
spec-too-weak candidate; the determinism lemma documents why that reading is
unsound: spec-admittance here implies gold-equal output.
