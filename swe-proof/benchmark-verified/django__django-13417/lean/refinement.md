# refinement.md — operation correspondence (django__django-13417)

Maps every op in `implementation_querysetOrdered` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`QuerySet.ordered`) is a cascade of `if/elif` returns. We model
each guard as the equivalent boolean observation on the Lean carrier, preserving the
short-circuit precedence with early `return`s.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if isEmpty then return true` | `if isinstance(self, EmptyQuerySet): return True` | R | the EmptyQuerySet predicate ↔ `isEmpty : Bool` (mapping.md); UNCHANGED by patch |
| 2 | `if !extraOrderBy.isEmpty \|\| !orderBy.isEmpty then return true` | `if self.query.extra_order_by or self.query.order_by: return True` | R | Python truthiness of the two sequences ↔ `List.isEmpty` negation (mapping.md); UNCHANGED, short-circuits before the default-ordering branch |
| 3 | `else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then return true` | `elif (self.query.default_ordering and self.query.get_meta().ordering and not self.query.group_by): return True` | R | the **changed op** modeled deeply: the added conjunct `not self.query.group_by` ↔ `groupBy.isEmpty`. `default_ordering` ↔ the `Bool`; `get_meta().ordering` truthiness ↔ `!metaOrdering.isEmpty`. NOT axiomatized. |
| 4 | `else return false` | `else: return False` | I | identical fallthrough |

No A-consumed rows: the proof discharges the boolean combination directly; no
UNCHANGED callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: every guard is reproduced concretely as a flag/emptiness
observation (R/I), not abstracted behind a model that needs G-AX validation. No
changed-inexpressible op.

The discriminating clause is row 3: the patch adds the `groupBy.isEmpty` conjunct.
The prepatch impl omits it (`defaultOrdering && !metaOrdering.isEmpty`), so whenever
`defaultOrdering = true`, `metaOrdering` non-empty, `groupBy` non-empty, and the
earlier branches do not fire (`isEmpty = false`, both `extraOrderBy`/`orderBy`
empty), the prepatch returns `true` while the frozen
`problem_spec_querysetOrdered` requires `false`. Hence prepatch
`correct_querysetOrdered` cannot close — the G-DIFF signal. This is exactly the
`test_annotated_default_ordering` / `test_annotated_values_default_ordering`
scenario (a GROUP BY queryset over a model with `Meta.ordering`).
