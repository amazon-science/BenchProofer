# refinement.md — django__django-13569

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`groupingColumns` `do` block and the deep `groupingContribution` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — A-consumed / A-reference), or **I** (identical
concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1, run in-container with the gold patch applied); the narrative is audited by
**G-EQ**. There are **no A-tagged ops** (no axioms, no deep-model references):
the modeled function is the changed function itself and its new body
(`return []`) calls no other callee.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `Random.get_group_by_cols` (`django/db/models/functions/math.py`, added after `Random.as_sqlite`, line 154)

Gold hunk:
```
+    def get_group_by_cols(self, alias=None):
+        return []
```

| # | Solution.lean impl op (`groupingColumns`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `e : Expr` with `require e.isNondetGenerator = true` | `self` — the `Random` receiver of the added method | R | the method exists only on `Random`, so the receiver is always a non-deterministic value generator; `isNondetGenerator = true` ↔ `isinstance(self, Random)` (mapping.md §2). G-CONF instantiates the real `Random()` node. |
| A2 | (the `alias` argument is omitted) | `alias=None` parameter | R | the patched body ignores `alias` (`return []` regardless); the model drops it. G-CONF fuzzes 8 distinct `alias` values incl. `None` and confirms the result is invariant. |
| A3 | `return []` (i.e. `groupingContribution e` under the `isNondetGenerator` branch) | `return []` | I | identical concrete op: the empty grouping-column list. Bridged by `[] ↔ empty Python list` (mapping.md §2). |

The post-condition pins this exactly: `out = []` AND
`out = groupingContribution e` (which, under `require isNondetGenerator = true`,
reduces to `[]`). No implementation contributing a non-empty column list for a
`Random` leaf can satisfy it.

## B. The contrasted generic rule — `BaseExpression.get_group_by_cols` (`django/db/models/expressions.py:349`)

This is **not** a step of `patch.diff`; it is the inherited behaviour the new
override replaces, modeled deeply by the `else` branch of `groupingContribution`
(`if e.isNondetGenerator then [] else [e]`). It exists in `Solution.lean` only to
make the abstraction boundary explicit and to give the prepatch a faithful
pre-image.

| # | Solution.lean construct | repo behaviour | tag | justification |
|---|---|---|---|---|
| B1 | `groupingContribution e = [e]` when `isNondetGenerator = false` | `BaseExpression.get_group_by_cols` returns `[self]` for a non-aggregate leaf (`contains_aggregate == False`) | I (deep model of an UNCHANGED inherited rule) | this is the rule `Random` inherited pre-patch and that ordinary value-level leaves keep. It is spelled out, not axiomatized; G-CONF validates it against the real `Pi`/`Now` leaves (which inherit `[self]`). NOT a consumed axiom. |

`Solution_prepatch.lean` reproduces exactly B1 applied to a `Random` leaf
(`return [e]`), i.e. the inherited generic rule with no `Random` special case —
the literal pre-patch state where `Random` had no `get_group_by_cols` of its own.
It therefore **fails** `out = []` (and `out = groupingContribution e`, since
under `require isNondetGenerator = true` that model is `[]`). This is the
observed defect: `Random()` used for ordering contributes `RANDOM()` into the
GROUP BY, splitting the aggregation groups (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The one operation that genuinely *changed* — a
`Random` leaf's grouping-column contribution flipping from `[self]` to `[]` — is
modeled **deeply** (the `isNondetGenerator` branch of `groupingContribution`),
not behind an axiom about the function under change. The contrasted inherited
rule (B1) is likewise a deep model, not a consumed axiom. There is **no
axiomatized callee** (G-AX skipped; `meta.json axioms = []`,
`deep_model_references = []`).

## D. verify(Solution) ⇒ resolved

`groupingColumns` verifies only if, for a non-deterministic value generator
(`require isNondetGenerator = true`), its output is the empty contribution
(`out = [] = groupingContribution e`, A3). By R (`isNondetGenerator = true ↔
isinstance(self, Random)`; `[] ↔` empty `list`; `alias` irrelevant) the verified
method equals the patched `Random.get_group_by_cols(alias)` on every input. By
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on 10⁵
inputs against the REAL `Random`/`Pi`/`Now` nodes (and disagrees against the
pre-patch repo, confirming discrimination). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc + G-CONF); there is no axiom-soundness trust point (no axioms).
