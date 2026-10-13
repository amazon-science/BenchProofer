# refinement.md — django__django-12708

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `selectIndexConstraints` `do` block, plus the `keep`/`selected` pure model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs, so G-EQ has only the overall correspondence
narrative to audit. Claim: any impl verifying against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The selection site — `alter_index_together` deletion path

Gold hunk (`django/db/backends/base/schema.py:396`):
```
- self._delete_composed_index(model, fields, {'index': True}, self.sql_delete_index)
+ self._delete_composed_index(
+     model,
+     fields,
+     {'index': True, 'unique': False},
+     self.sql_delete_index,
+ )
```
`_delete_composed_index` forwards `constraint_kwargs` to `_constraint_names`,
which loops over the constraints on the target columns and selects those whose
`infodict` flags match the kwargs (`schema.py:1148-1168`). The patch changes the
kwargs from `{'index': True}` to `{'index': True, 'unique': False}`.

| # | Solution.lean impl op (`selectIndexConstraints`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `cs : List Constraint` | the constraints on the target columns — the `{name: infodict}` map `_constraint_names` iterates (`schema.py:1150`) | R | the column-matched constraint map ↔ `List Constraint` (mapping.md §2). Order is dict insertion order ↔ list order; the observable (selected name set) is order-respecting and the model preserves order. |
| A2 | `Constraint.isIndex` / `Constraint.isUnique` field reads | `infodict['index']` / `infodict['unique']` (`schema.py:1153,1155`) | R | the two boolean flags `_constraint_names` tests ↔ `Bool` fields (mapping.md §2). G-CONF feeds the real callee `infodict`s with each flag combination. |
| A3 | `keep c = c.isIndex && !c.isUnique` | the post-patch filter `infodict['index'] == True and infodict['unique'] == False` imposed by the kwargs `{'index': True, 'unique': False}` (`schema.py:1153-1156`) | I | the changed selection predicate, modeled **identically**: the boolean structure (`isIndex AND NOT isUnique`) is exactly what the two kwargs select. This IS the operation the patch changed (the `unique: False` conjunct is the added filter); modeled concretely, not behind an axiom. |
| A4 | `out = selected cs`: the backward `while` fold keeping each `keep`-passing constraint, in order | the list of names `_constraint_names` returns under the post-patch kwargs (`schema.py:1167`), which `_delete_composed_index` requires to have length 1 (`schema.py:1158`) and then deletes | R + I | the unchanged filtering loop reduces to "select the constraints passing the kwargs filter"; `selected`/the `if keep then [c] else [] ++` fold is that selection (R for the loop/map shape, I for the per-element keep test). G-CONF transliterates it and diffs against the real `_constraint_names`. |

Discriminating content of the change — a constraint that is both an index AND a
uniqueness constraint (the index-backed unique constraint the issue describes,
`isIndex = true, isUnique = true`) must NOT be selected — lives in
`keep c = c.isIndex && !c.isUnique` (model) ⇔ the added `unique: False` filter
conjunct (real). The pre-patch kwargs `{'index': True}` select on the index flag
ALONE; `Solution_prepatch.lean` reproduces that (`if c.isIndex then [c] else []`)
and **fails** `out = selected cs` (G-DIFF): for a constraint with
`isIndex = true, isUnique = true` the prepatch keeps it (selecting 2 constraints,
which makes `_delete_composed_index` raise `ValueError` — the crash in the F2P
scenario) while `selected` drops it (selecting exactly the 1 plain index).

## B. No second site

The `constraint_kwargs` literal at `schema.py:396` is the only changed line; the
parallel `alter_unique_together` deletion (`schema.py:382`) and the
`_delete_composed_index`/`_constraint_names` bodies are byte-identical before and
after the patch. There is a single independently-observable fixed behavior (an
index-backed unique constraint over the same columns must be excluded from the
index-deletion selection), exercised by one `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the selection
filter — is modeled **identically** (`keep`, step A3), not hidden behind an
axiom. There are no consumed axioms and no deep-model references: the changed
behavior is a kwargs-driven filter over the constraint flags, and the filtering
callee `_constraint_names` is run for real by G-CONF (not axiomatized), so its
fidelity is mechanically checked, not assumed.

## D. verify(Solution) ⇒ resolved

`selectIndexConstraints` verifies only if its output equals the exact per-
constraint selection with the conjoined `NOT isUnique` guard (A3, A4). By R
(constraint map ↔ `List Constraint`, `infodict` flags ↔ `Bool` fields, selected
names ↔ kept constraints) the verified selection equals the set the patched
`_constraint_names` returns under `{'index': True, 'unique': False}` on the
tested inputs; by G-CONF the R/I transliteration of `keep`/`selected` agrees with
the real `_constraint_names`'s selection over ≥10⁵ fuzzed constraint maps.
Because the patched deletion then operates on exactly that selection (length-1
check + delete), a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
only trust point is refinement fidelity (this doc + G-CONF); there is no
axiom-soundness trust point (no axioms).
