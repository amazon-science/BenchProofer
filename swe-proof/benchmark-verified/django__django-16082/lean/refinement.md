# refinement.md — operation correspondence (django__django-16082)

Maps every op in `implementation_resolveCombinedType` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) ·
**I** identical op.

The patched Python `_resolve_combined_type(connector, lhs_type, rhs_type)` looks
up the registered combination rows for `connector` (built once at import from the
`_connector_combinations` table, where the gold patch adds `Combinable.MOD` to the
different-type numeric connector tuple) and returns the `combined_type` of the
first row whose two slots both accept the operand types under `issubclass`, else
`None`. We reproduce the row set deeply (`combosFor`) and the `issubclass` slot
test deeply (`kindMatches`), then scan in registration order.

| # | Lean impl op | patch.diff / base counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `op : ArithOp`, `lhs rhs : FieldKind` | `connector`, `lhs_type`, `rhs_type` | R | connector-string ↔ `ArithOp` and field-class ↔ `FieldKind` bijections (mapping.md) |
| 2 | `if sameKindOps.contains op then combinators := … ++ sameKindRows` | same-type numeric dict rows registered for `op` (`expressions.py:505-523`) — present for `ADD,SUB,MUL,DIV,MOD,POW` | I | the registered same-type rows reproduced exactly, in registration order; unchanged by the patch |
| 3 | `if ([add,sub,mul,div,modOp]).contains op then combinators := … ++ mixedKindRows` | different-type numeric dict rows registered for `op` (`expressions.py:524-540`) — **the patched tuple `(ADD,SUB,MUL,DIV,MOD)`** | R | the **changed op** modeled deeply: the gold patch adds `MOD` to this connector tuple, so remainder now contributes the four mixed-kind promotion rows. `POW` is absent (mixed-kind POW → none). NOT axiomatized. |
| 4 | `for (clhs,crhs,combined) in combinators do if kindMatches lhs clhs && kindMatches rhs crhs then return some combined` | `for … in combinators: if issubclass(lhs_type, clhs) and issubclass(rhs_type, crhs): return combined_type` | A-reference | `kindMatches` is the deep model of `issubclass` over the finite numeric-kind lattice (only `autoKind ⊂ integerKind`); validated == real `issubclass` over all modeled (operand, slot) pairs by G-AX. Concrete in Lean, so the proof consumes no `_prop` axiom. |
| 5 | `return none` | falls off the loop → implicit `return None` | I | identical: no accepting row ⟹ none/`None` |

- **No A-consumed rows.** The proof discharges `implementation = resolveSpec`
  structurally; no UNCHANGED-callee property is *assumed* (axioms region empty).
- **One A-reference row (#4).** `kindMatches` deep-models `issubclass`; G-AX
  validates the model against the real builtin. It is concrete (decidable), so
  the proof needs no axiom about it.
- No changed-inexpressible op: the added MOD promotion is fully expressed by
  including `modOp` in the mixed-kind operator set.

## Discriminating clause (G-DIFF)
Row #3. For a mixed numeric kind under remainder — e.g. `(modOp, integerKind,
decimalKind)` — the post-patch impl includes `modOp` in the mixed-kind operators,
so `combinators` contains `mixedKindRows`, the first accepting row is
`(integerKind, decimalKind, decimalKind)`, and the result is `some decimalKind` =
`resolveSpec (modOp) integerKind decimalKind`. The prepatch impl omits `modOp`
from the mixed-kind operator list, so `combinators = sameKindRows` only; no
same-kind row accepts `(integerKind, decimalKind)` (they require equal kinds), and
it returns `none ≠ some decimalKind = resolveSpec …`. Hence prepatch
`correct_resolveCombinedType` cannot close — the G-DIFF signal — while the spec
(`resolveSpec`, which itself includes `modOp` in `mixedKindOps`) demands the
promotion.
