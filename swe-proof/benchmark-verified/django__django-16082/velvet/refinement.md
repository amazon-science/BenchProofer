# refinement.md — django__django-16082

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveModType` `do` block plus the pure `combinedNumeric` / `lookup` /
`modCombinators` it scans) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — A-consumed / A-reference),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, computes the same combined output
type as the gold patch on the numeric operand domain the F2P tests exercise, so
it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change

Gold hunk (`django/db/models/expressions.py`, the different-type **numeric**
connector group):
```
             Combinable.SUB,
             Combinable.MUL,
             Combinable.DIV,
+            Combinable.MOD,
         )
```
Pre-patch, the remainder connector `MOD` is registered only in the *same-type*
numeric group (and the NULL group), so `_resolve_combined_type(MOD, lhs, rhs)`
returns `None` for mixed numeric operands (e.g. Integer × Decimal). The patch
adds `MOD` to the *different-type* group, registering the four mixed widening
rules so the resolver returns the wider type, like the other arithmetic
operators.

## Operation correspondence

| # | Solution.lean impl op (`resolveModType`) | patch.diff op (effect on `_resolve_combined_type(MOD,·,·)`) | tag | justification |
|---|---|---|---|---|
| 1 | params `lhs rhs : NumKind` | the `lhs_type`/`rhs_type` operand field classes (with `connector = MOD`) | R | operand field class ↔ `NumKind` (mapping.md §2); the `issubclass` collapse of the IntegerField family to one kind is captured by the bijection. G-CONF bridges. |
| 2 | `combs := modCombinators` — the registered remainder rules (3 same-kind + 4 mixed widening) | the post-patch registered combinator list for `MOD` (same-type group ∪ different-type group, numeric slice) | I | the literal rule list IS the registered list under the bijection. Pre-patch it lacks the 4 mixed rows — the discriminating content (G-DIFF prepatch). |
| 3 | the backward `while` scan setting `res` to the first matching rule's result kind | `_resolve_combined_type`'s `for … in combinators: if issubclass(lhs)…issubclass(rhs): return combined_type` first-match loop | I | identical first-match search; the backward-overwrite scan makes the lowest-index rule win, matching Python's `return`-on-first-match. Verified equal to `combinedNumeric` (lemma `lookup_modCombinators`). |
| 4 | result `Option NumKind` (`some k` / `none`) | the returned field class, or `None` → caller raises `FieldError` | R | result class ↔ `some kind`; `None` ↔ `none` (mapping.md §2). The F2P `test_resolve_output_field_number` observes the instantiated class via `CombinedExpression.output_field`. |

The discriminating content of the change — mixed Integer/Decimal (and
Integer/Float) under `MOD` resolving to the wider kind rather than `none` —
lives in the four mixed rows of `modCombinators` (`(int,dec)→dec`,
`(dec,int)→dec`, `(int,float)→float`, `(float,int)→float`) and in
`combinedNumeric`. `Solution_prepatch.lean` drops those rows (scans only the
three same-kind rules) and **fails** `out = combinedNumeric lhs rhs` at e.g.
`lhs = .int, rhs = .dec` (G-DIFF).

## No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — the data-table
registration that the resolver scans — is modeled **deeply** (the spelled-out
`modCombinators` rule list and the verified `lookup` scan), not hidden behind an
axiom about the function under change. There are **no consumed axioms and no
A-reference**: the bundle ships no `axiom` and no `axiom_check.py` (G-AX skips).

## verify(Solution) ⇒ resolved

`resolveModType` verifies only if its output equals `combinedNumeric lhs rhs` —
the result-kind relation that returns the wider kind for mixed Integer/Decimal
and Integer/Float (and `none` only for the genuinely-incompatible pairs). By R
(operand/result field class ↔ `NumKind`/`Option NumKind`) the verified scan
equals the post-patch `_resolve_combined_type(MOD, ·, ·)` on the numeric operand
domain; by G-CONF the R/I transliteration of that scan agrees with `patch.diff`'s
real resolver on 10⁵ inputs (exhaustive over the 49 numeric class pairs + fuzz),
0 disagreements. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point because there are no axioms.
