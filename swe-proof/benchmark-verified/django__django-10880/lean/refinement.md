# refinement.md — operation correspondence (django__django-10880)

Maps every op in `implementation_buildCallSql` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`Aggregate.as_sql`, no-filter path) computes the `distinct`
template slot and then renders the literal template
`'%(function)s(%(distinct)s%(expressions)s)'` via `super().as_sql`. We model the
slot computation deeply and the literal-template substitution as the equivalent
fixed-order concatenation.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `function : List Char` | `%(function)s` slot (e.g. `'COUNT'`) | R | str ↔ List Char bijection (mapping.md); function name passed through unchanged |
| 2 | `expressions : List Char` | `%(expressions)s` slot (rendered argument SQL) | R | str ↔ List Char bijection; argument text passed through unchanged |
| 3 | `let mut distinctSlot := []` then `if distinct then distinctSlot := "DISTINCT ".toList` | `extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''` | R | the **changed op** modeled deeply: the flag selects the keyword-plus-separator fragment vs empty. The trailing space is the fix. NOT axiomatized. |
| 4 | `function ++ ['('] ++ distinctSlot ++ expressions ++ [')']` | substitution of the three slots into the literal template `'%(function)s(%(distinct)s%(expressions)s)'` by `super().as_sql` | I | identical concrete op: substitution into a fixed literal template is fixed-order concatenation with the literal `(` and `)` separators |
| 5 | `return …` | returned `sql` of the call | I | the returned `params` list is unaffected by the fix and is out of model scope (mapping.md) |

No A-consumed rows: the proof discharges the concatenation directly; no UNCHANGED
callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: the only callee (`super().as_sql`'s literal-template
substitution) is reproduced concretely as an I op, not abstracted behind a model
that needs G-AX validation. No changed-inexpressible op.

The discriminating clause is row 3: when `distinct = true`, the fragment is
`"DISTINCT "` (with the trailing space). The prepatch impl emits `"DISTINCT"`
(no space), so the rendered text is `function ++ "(DISTINCT" ++ expressions …`
which differs from the frozen `problem_spec_buildCallSql`
(`… ++ distinctKeyword true ++ …` = `… ++ "DISTINCT " ++ …`) whenever
`distinct = true`. Hence prepatch `correct_buildCallSql` cannot close — the
G-DIFF signal.
