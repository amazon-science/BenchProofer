# mapping.md — django__django-17084

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f8c43aca467b7b0c4bb0a7fa41362f90b610b8df`, states the type
abstraction (the bijection a conformance gate would use to bridge Lean↔Python),
and records callee provenance and flag dependencies.

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `wrappedEvaluationDecisionM (...)` | the disjunction guarding the wrapping-subquery branch of `Query.get_aggregation` — `django/db/models/sql/query.py:449-457` (the `if (isinstance(self.group_by, tuple) or … or self.combinator):` test) | the modeled changed decision |
| `wrappedEvaluationDecision priorConditions aggregates` | the boolean value of that `if` condition | pure spec: the guard, including the newly-added window disjunct |
| `referencesWindow aggregates` | the new `refs_window` accumulator (`query.py:406`, accumulated at `query.py:423-426`, consumed at `query.py:457`) | pure spec: any requested aggregate references a window-using annotation |
| `aggregateUsesWindow refs` | `any(getattr(self.annotations[ref], "contains_over_clause", True) for ref in aggregate.get_refs())` (`query.py:423-426`) | pure spec: this one aggregate references a window-using annotation |
| `aggregates` | the per-aggregate list of `aggregate.get_refs()` resolved flags, in `aggregate_exprs` iteration order (`query.py:408`, the `for alias, aggregate_expr` loop) | the modeled carrier |
| each inner `List Bool` | for one aggregate, `[getattr(self.annotations[ref], "contains_over_clause", True) for ref in aggregate.get_refs()]` | per-reference window flags of that aggregate |
| `priorConditions` | the disjunction of the pre-existing wrapping conditions: `isinstance(self.group_by, tuple) or self.is_sliced or has_existing_aggregation or refs_subquery or qualify or self.distinct or self.combinator` (`query.py:450-456`) — UNCHANGED by the patch | shared structural context |
| `out` | the boolean fed to the `if`, deciding the wrapping-subquery branch | the decision outcome |

The patch (`query.py`) makes exactly three additions: declare `refs_window =
False` (line 406), accumulate `refs_window |= any(getattr(self.annotations[ref],
"contains_over_clause", True) for ref in aggregate.get_refs())` inside the
existing per-aggregate loop (lines 423-426), and add `or refs_window` to the
wrapping-decision disjunction (line 457). Everything else in `get_aggregation`
— including how `aggregate.get_refs()`, `self.annotations[ref]`, and each
annotation's `contains_over_clause` are produced — is shared identically by the
pre- and post-patch code.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `getattr(self.annotations[ref], "contains_over_clause", True)` (a `bool`; `True` if the annotation expression contains an `OVER (…)` window clause) | `Bool` (one element of an inner `List Bool`) | identity. The Python `getattr(…, "contains_over_clause", True)` defaults missing attributes to `True` (conservative: treat an undeterminable reference as window-using) — modeled as that flag already being `true` for such a reference (the "treated conservatively" note in the `aggregateUsesWindow` docstring). |
| `aggregate.get_refs()` for one aggregate (a `set` of referenced annotation aliases) → its window flags | one inner `List Bool` | each referenced alias contributes its `contains_over_clause` flag. `any(... for ref in aggregate.get_refs())` ↔ `refs.any (fun b => b)` (`aggregateUsesWindow`). `get_refs()` is a set, but `any` over it is order- and duplicate-insensitive, so the `List Bool` model (any order, any multiplicity) is observationally exact for the disjunction. |
| the per-aggregate iteration `for alias, aggregate_expr in aggregate_exprs.items()` accumulating `refs_window |= any(...)` | outer `List (List Bool)` folded by `referencesWindow` | `refs_window` after the loop ↔ `referencesWindow aggregates`: a left-to-right OR over the per-aggregate `any` flags. `|=` over `bool` ↔ `||`; the OR-fold is order- and duplicate-insensitive, so the list model is exact. |
| the pre-existing disjunction `isinstance(self.group_by, tuple) or … or self.combinator` | `Bool` (`priorConditions`) | the truthiness of the unchanged structural conditions, collapsed to a single Bool. The patch does not touch any of these operands; collapsing them is exact for the decision's boolean outcome. |
| the full `if (… or refs_window):` value | `Bool` (`out`) | `priorConditions || referencesWindow aggregates` ↔ the Python `or` chain. Python `or` yields operand truthiness and short-circuits; every operand here is modeled at `Bool` level, so the Lean `||` chain is observationally identical to the Python `or` chain for the guard's boolean outcome. |

## 3. Callee provenance

No axiomatized callees and no A-reference deep models of outside callees. The
operands the decision reads — `aggregate.get_refs()`, `self.annotations[ref]`,
and each annotation's `contains_over_clause` property
(`django/db/models/expressions.py:246-250`, a `cached_property` OR-folding over
the expression's source expressions; `Window.contains_over_clause = True` at
`expressions.py:1703`, `BaseExpression.contains_over_clause = False` at
`expressions.py:858`) — are UNCHANGED by the patch and are read identically by
both the pre- and post-patch code. They are therefore not part of the modeled
decision: they are shared context, not a contract the proof consumes. The
patch's entire behavioral content is the new `refs_window` disjunct.

Flag/config dependencies: none at the Lean-model level. (In Python the F2P test
is `@skipUnlessDBFeature("supports_over_clause")`, a backend capability gate,
not a runtime flag the modeled decision reads.)

## 4. G-CONF: skipped (conf_skip = true)

There is no DB-free R/I shadow of this decision. The operands that drive the
discriminating disjunct — the resolved `aggregate.get_refs()` for each requested
aggregate and the `contains_over_clause` flag of each referenced annotation in
`self.annotations` — are produced only by resolving aggregate expressions
against a live ORM query: `aggregate_expr.resolve_expression(self,
allow_joins=True, reuse=None, summarize=True)` (`query.py:409-411`) walks the
model's annotation graph and field metadata. Reproducing the bug-triggering case
(an aggregate, e.g. `Sum("cumul_DJR")`, that references an annotation built from
a `Window(...)` expression, so its referenced annotation's
`contains_over_clause` is `True` while none of the pre-existing structural
conditions hold) requires standing up the model classes, their annotations, and
a resolved query — i.e. the F2P integration test
`test_referenced_window_requires_wrapping` itself, not a pure transliteration a
gate can fuzz. Per SPEC_GUIDE §0 / WORKER_PROMPT, `meta.json conf_skip=true` and
`conformance_check.py` is a `status=skip` stub. Soundness of the modeled guard
rests on G-VERIFY (`wrappedEvaluationDecision` provably equals the OR of
`priorConditions` and the window-reference fold the impl computes) + G-DIFF (the
prepatch, which omits the window disjunct, fails the invariant that pins
`acc = referencesWindow (aggregates.drop i)` exactly when some aggregate uses a
window function). This mirrors the django__django-13033 / django__django-13315
precedent (a boolean ORM-decision guard whose operands are resolvable only
against a live model graph). No pinned fuzz seed (no fuzzing performed).
