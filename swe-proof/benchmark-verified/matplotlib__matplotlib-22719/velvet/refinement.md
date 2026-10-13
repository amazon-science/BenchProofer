# refinement.md — matplotlib__matplotlib-22719

Operation-by-operation correspondence between `Solution.lean`'s two impl regions
(`numericNoticeFires` and `numericLabelNoticeFires`, the deep `noticeFires`/
`allTrue` model) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. This bundle has **no axioms**, so
there are no A-consumed/A-reference rows and no `axiom_check.py` (G-AX skip).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. Site A — `StrCategoryConverter.convert` (`lib/matplotlib/category.py:61`)

Gold hunk:
```
-        if is_numlike:
+        if values.size and is_numlike:
             _api.warn_deprecated( ... )
```

`is_numlike` was set just above by
`is_numlike = all(units.ConversionInterface.is_numlike(v) and not isinstance(v, (str, bytes)) for v in values)`.

| # | Solution.lean impl op (`numericNoticeFires`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `numlikeFlags : List Bool` | the per-element results of `is_numlike(v) and not isinstance(v,(str,bytes))` over `values` | R | each element `v` ↔ its boolean test result; `len(values)` ↔ `flags.length`; empty `values` ↔ `[]` (mapping.md §2). The per-element test is UNCHANGED and observed only through its boolean result — no axiom (django__django-12406 treatment). |
| A2 | `allTrue numlikeFlags` | `is_numlike` (the `all(...)` aggregate) | I | `all(t(v) for v in values)` ↔ the front-recursive conjunction `allTrue`; `all([]) = True` ↔ `allTrue [] = true`. Concrete transliteration, G-CONF-checked. |
| A3 | `!numlikeFlags.isEmpty` | `values.size` (numpy length, used for truthiness) | R | `bool(values.size)` ↔ `!flags.isEmpty`: `np.atleast_1d(np.array(x, dtype=object)).size == 0` iff `x` is empty (mapping.md §2). |
| A4 | `out = !numlikeFlags.isEmpty && allTrue numlikeFlags` | `if values.size and is_numlike:` (notice emitted iff true) | I | the new conjoined guard `values.size and is_numlike` ↔ `noticeFires`. `out` models the boolean "advisory emitted". |

Discriminating content: the empty collection. Pre-patch `if is_numlike:` →
`allTrue []` = `true` → advisory fires (the false-alarm warning the issue
reports). Post-patch the conjunction with `values.size` suppresses it.
`Solution_prepatch.lean` reproduces the pre-image (`return allTrue numlikeFlags`)
and **fails** `out = noticeFires numlikeFlags` precisely at `numlikeFlags = []`
(G-DIFF).

## B. Site B — `UnitData.update` (`lib/matplotlib/category.py:233`)

Gold hunk:
```
-        if convertible:
+        if data.size and convertible:
             _log.info( ... )
```

`convertible` is the running conjunction over the unique values of `data`:
`convertible &= self._str_is_convertible(val)` for each `val` in
`OrderedDict.fromkeys(data)`, starting from `True`.

| # | Solution.lean impl op (`numericLabelNoticeFires`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `parsableFlags : List Bool` | the per-(unique-)value results of `self._str_is_convertible(val)` | R | each unique value `val` ↔ its boolean test result (mapping.md §2). The test is UNCHANGED, observed only through its boolean result — no axiom. |
| B2 | `allTrue parsableFlags` | `convertible` (the running `&=` conjunction, init `True`) | I | the left-fold conjunction starting from `True` ↔ `allTrue` over the per-value results; over zero values it stays `True` ↔ `allTrue [] = true`. |
| B3 | `!parsableFlags.isEmpty` | `data.size` (numpy length, used for truthiness) | R | `bool(data.size)` ↔ `!flags.isEmpty`. `data.size` counts ALL elements while the flags are per-unique-value, but the guard consumes only the TRUTHINESS, and `bool(data.size) == (#unique > 0)` since unique-count is 0 iff element-count is 0 (mapping.md §2 note). |
| B4 | `out = !parsableFlags.isEmpty && allTrue parsableFlags` | `if data.size and convertible:` | I | the new conjoined guard ↔ `noticeFires`. `out` models the boolean "advisory (INFO log) emitted". |

Discriminating content: again the empty collection. Pre-patch `if convertible:`
→ `allTrue []` = `true` → the INFO advisory fires on empty input. Post-patch the
`data.size` conjunct suppresses it. `Solution_prepatch_2.lean` reproduces the
pre-image (`return allTrue parsableFlags`) and **fails** at `parsableFlags = []`
(G-DIFF). The two sites are independently observable, hence two prepatches.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely changed at each site — the
addition of the non-empty guard conjunct to the notice-emission decision — is
modeled **deeply** (`noticeFires = !isEmpty && allTrue`), not hidden behind an
axiom. The per-element classification tests (`is_numlike`, `_str_is_convertible`)
are UNCHANGED and contribute only their boolean results, modeled as the input
carriers — there is no consumed axiom and no deep-model reference, so no
`axiom_check.py` (G-AX skip). The `all(...)` aggregate is itself unchanged
(I-tagged); only the surrounding guard moved.

## D. verify(Solution) ⇒ resolved

Each method verifies only if its output equals `noticeFires flags` = exactly
"non-empty AND every per-element classification affirmative". By R (`bool(size)`
↔ `!isEmpty`; per-element test result ↔ `Bool`) and I (the `all`/`&=` aggregate
↔ `allTrue`), the verified decision equals the post-patch guard
`<coll>.size and <aggregate>` at each site. G-CONF (§4.1) derives the flags from
the REAL unchanged tests and drives the REAL patched `convert`/`update`
in-container, confirming the R/I shadow `noticeFires` agrees with whether the
advisory actually fires over ≥10⁵ fuzzed inputs (boundary: empty, all-true,
mixed, all-false). The F2P test `test_no_deprecation_on_empty_data` exercises
exactly the empty-collection case the spec pins to `false`. Therefore a model
satisfying this spec, refined by the maps above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom soundness point.
