# refinement.md — django__django-12209

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`decideForceInsert` `do` block and the deep `decidedForceInsert` /
`pkHasUsableDefault` models) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — A-consumed /
A-reference), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1, run in-container with the gold patch applied); the narrative is audited by
**G-EQ**. There are **no A-tagged ops** (no axioms, no deep-model references):
the changed behaviour is a closed boolean decision over attribute reads, with no
callee changed, so everything is modeled deeply as closed boolean functions of
the inputs.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The INSERT-forcing decision — `Model._save_table` (`django/db/models/base.py:851-857`)

Gold hunk (the behavioural core):
```
         updated = False
         # Skip an UPDATE when adding an instance and primary key has a default.
         if (
+            not raw and
             not force_insert and
             self._state.adding and
             self._meta.pk.default and
             self._meta.pk.default is not NOT_PROVIDED
         ):
             force_insert = True
```

| # | Solution.lean impl op (`decideForceInsert`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `raw : Bool` | the `raw` parameter of `_save_table` | R | direct/unprocessed-data-load flag ↔ `Bool` (mapping.md §2). The added `not raw and` conjunct ↔ the `!raw` conjunct of the guard. |
| A2 | param `forceInsert : Bool` | the incoming `force_insert` parameter | R | truthy ↔ `true` (mapping.md §2). Modeled as the value entering the guard; `out` is its post-guard value. |
| A3 | param `adding : Bool` | `self._state.adding` | R | first-time-add flag ↔ `Bool` (mapping.md §2). |
| A4 | params `pkDefaultTruthy`, `pkDefaultProvided : Bool` | `self._meta.pk.default` (truthiness) and `self._meta.pk.default is not NOT_PROVIDED` | R | the two pk-default observations ↔ `Bool` each (mapping.md §2); combined as `pkHasUsableDefault = pkDefaultTruthy && pkDefaultProvided`. |
| A5 | `if !raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided) then true else forceInsert` (= `decidedForceInsert ...`) | `if ( not raw and not force_insert and self._state.adding and self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED ): force_insert = True` | I (deep model of the changed guard) | the guard is spelled out conjunct-for-conjunct, and the assignment `force_insert = True` on the true branch / the unchanged flag on the false branch is `decidedForceInsert`. NOT a consumed axiom — G-CONF validates against the real guard. mapping.md §3.1. |

The post-condition pins this exactly: `out = decidedForceInsert ...` AND
`pkHasUsableDefault preDflt... = (pkDefaultTruthy && pkDefaultProvided)`. No
implementation that forces an INSERT for a direct/unprocessed data load
(`raw=True`) — which is the optimisation the issue forbids — or that fails to
force one for an ordinary first-time add of an instance whose pk has a usable
default (which the pre-patch behaviour requires and which downstream code
depends on), can satisfy it.

Discriminating content of the change — `raw=True` must NOT introduce the
forcing — lives in the `!raw` conjunct of `decidedForceInsert`. The pre-patch
guard omitted it; `Solution_prepatch.lean` reproduces that and **fails**
`out = decidedForceInsert ...` precisely on the `raw=True ∧ !forceInsert ∧
adding ∧ pkHasUsableDefault` configuration (G-DIFF), which is exactly the
serializer/`loaddata` round-trip the F2P test exercises (an explicit pk on a
model whose pk has `default=uuid.uuid4`, saved as a `raw` data load, must remain
free to UPDATE-then-INSERT rather than INSERT-only).

## B. No second site

The patch is a single one-line conjunct addition to one guard. There is no
refactor, no added helper, and no second independently-observable behaviour, so
there is exactly one modeled method and one failing prepatch.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The operation that genuinely *changed* — excluding
direct/unprocessed data loads from the INSERT-forcing guard — is modeled
**deeply** (`decidedForceInsert` / `pkHasUsableDefault`), not behind an axiom
about the function under change. There is **no axiomatized callee** (G-AX
skipped; `meta.json axioms = []`, `deep_model_references = []`): `raw`,
`force_insert`, `self._state.adding`, and the two `self._meta.pk.default`
observations are all read-only boolean observations abstracted as the method's
`Bool` inputs (R), and no function the patch touches calls anything with a
contract to consume.

## D. verify(Solution) ⇒ resolved

`decideForceInsert` verifies only if its output is `decidedForceInsert ...`
(A5): `true` exactly when an ordinary save (`!raw`, `!forceInsert`) of a
freshly-added instance (`adding`) whose pk has a usable default
(`pkHasUsableDefault`) is requested, and the unchanged incoming flag otherwise.
By R (each Python observation ↔ the corresponding boolean input) the verified
method equals the patched `_save_table` guard's resolved `force_insert` on every
configuration. By G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs against the REAL patched guard logic (and disagrees
against the pre-patch on the `raw=True` configuration, confirming
discrimination). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc + G-CONF);
there is no axiom-soundness trust point (no axioms).
