# refinement.md — django__django-15569

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `removeBinding` `do` block, plus the deep `recomputeLookups` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (modeled callee — **A-consumed** where the proof uses an axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The operation — `_unregister_lookup(cls, lookup, lookup_name=None)` (`query_utils.py:212`)

Gold hunk:
```
         if lookup_name is None:
             lookup_name = lookup.lookup_name
         del cls.class_lookups[lookup_name]
+        cls._clear_cached_lookups()
```

| # | Solution.lean impl op (`removeBinding`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `registry : List (String × Nat)` *(mut)* | `cls.class_lookups` (the owned-binding dict, read/written) | R | `dict[str, lookup-class]` ↔ `List (String × Nat)` as a key→value mapping (mapping.md §2); the value class is abstracted to a stable id since only key add/remove/expose is observable. |
| A2 | param `name : String`; `require hasKey registry name = true` | `lookup_name`, after the `if lookup_name is None: lookup_name = lookup.lookup_name` defaulting; `del cls.class_lookups[lookup_name]` requires the key present | R | `str` ↔ `String` identity (mapping.md §2). The `is None` defaulting is pure argument resolution with no observable store/view effect (not modeled). `del d[k]` raises `KeyError` unless `k in d`; the `require` captures that the name is currently bound. |
| A3 | `registry := eraseKey registry name` | `del cls.class_lookups[lookup_name]` | I | the concrete store mutation: drop the one binding for `name`. `eraseKey` removes exactly that key (keys unique). Pinned by `ensures registry = eraseKey registryOld name`. Transliterated by G-CONF. |
| A4 | `cached := recomputeLookups inherited registry` | `cls._clear_cached_lookups()` (the ADDED line) | A-reference + I | the re-sync of the read-through view. The real added line clears the `lru_cache` so the NEXT `get_lookups()` recomputes; the spec models the observable net effect — the cached view equals the view re-derived from the now-current registry. The re-derivation is modeled **deeply**: `recomputeLookups`/`lookupKey` (pure region) ARE `get_lookups`'s reverse-merge `merge_dicts([*inherited_parents, own])` (own wins). The assignment (`:=`) is **I**; the equality of the deep model to the real `get_lookups()` is the **A-reference** G-AX validates (mapping.md §3.1). No consumed axiom. |
| A5 | param `inherited : List (String × Nat)` — NOT `mut`, never written | the inherited bindings from the parent MRO classes (read by `get_lookups`, untouched by `_unregister_lookup`) | R | **directive-5 mut-frame.** `inherited` is read-only: the operation neither mutates parents' `class_lookups` nor is it declared `mut`. It feeds the re-derivation only. (The two genuinely mutated stores — `registry`, `cached` — are each `mut` with their post-states pinned exactly by the two `ensures`; no `mut` param is left unconstrained.) |

Discriminating content of the change — **the cached read-through view is
re-synced to the registry after the removal**, so it equals
`recomputeLookups inherited registry` (the view of the registry AFTER the
binding is dropped), not its stale prior value — lives in the second `ensures`.
The pre-patch repo deleted the binding from `class_lookups` but **left the
`lru_cache`'d `get_lookups()` stale**, so a later consultation of the view still
exposed the removed name. `Solution_prepatch.lean` reproduces that exactly:
`registry := eraseKey registry name` (the delete still happens) but
`cached := cached` (no re-sync), and it **fails** the second `ensures`
(`cached = recomputeLookups inherited registry`) — the goal left unsolved is
`cachedOld = recomputeLookups inherited (eraseKey registryOld name)`, false
whenever the removed name was exposed by the cached view (G-DIFF).

## B. The plumbing — `_clear_cached_lookups` / `lru_cache` (`query_utils.py:197`)

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the deep re-derivation `recomputeLookups inherited registry` standing in for the post-clear view | `cls._clear_cached_lookups()` invalidating `get_lookups`'s `lru_cache` | A-reference (plumbing) | `_clear_cached_lookups` iterates `subclasses(cls)` calling `get_lookups.cache_clear()`; it performs no view computation of its own — its sole observable effect is that the next `get_lookups()` recomputes the view from the current `class_lookups`. The spec models that net effect (A4) rather than the cache machinery. Exercised end-to-end by the F2P tests under G-RESOLVE: without the clear, `field.get_lookups()` / `get_transform(...)` still return the removed name. No consumed axiom; no separately modeled function. |

No separate failing prepatch for site B: the cache-clear is unchanged plumbing
and a prepatch must keep the spec byte-identical (G-DIFF). The behavior the clear
enables — the re-synced view — is site A4, whose prepatch (`cached := cached`,
the stale view) already fails on the discriminating clause.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — adding
the re-sync of the cached view after the store mutation — is modeled
**directly** (the second assignment, A4, **I** up to the A-reference
re-derivation), not hidden behind an axiom about the function under change:
there is **no consumed axiom**. The only A legs are **A-references** — the deep
model `recomputeLookups` of the unchanged read-through derivation `get_lookups`
(G-AX-validated) and the unchanged cache-invalidation plumbing
(G-RESOLVE-exercised).

## D. verify(Solution) ⇒ resolved

`removeBinding` verifies only if (A3) it drops exactly the named binding from the
registry (`registry = eraseKey registryOld name`) AND (A4) it re-derives the
cached view from the now-current registry (`cached = recomputeLookups inherited
registry`). By R (`dict ↔ List (String × Nat)` as a mapping, `str ↔ String`
identities) the verified operation equals the gold `_unregister_lookup` (delete
+ cache clear); by G-AX the deep model `recomputeLookups` equals the real
`get_lookups()` (A-reference); by G-CONF the R/I transliteration of the store
delete + re-derivation agrees with `patch.diff`'s observable effect on the
post-operation view over ≥10⁵ inputs; and by G-RESOLVE the gold patch makes the
F2P tests pass (the removed name is no longer exposed). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves. Trust points are
exactly the two of plan §1.1: axiom soundness (G-AX, here the A-reference deep
model) and refinement fidelity (this doc, G-EQ + G-CONF).
