# mapping.md — django__django-14351

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 06fd4df41afb5aa1d681b853c3c08d8c688ca3a5`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the delegated callees.

Repo file under change: `django/db/models/lookups.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `inGroupByCols` (`method`) | `In.get_group_by_cols(self, alias=None)` — the method the patch ADDS to class `In` (`django/db/models/lookups.py:409`, inside `In(FieldGetDbPrepValueIterableMixin, BuiltinLookup)` declared at line 376) | the modeled changed function — overrides the inherited `Lookup.get_group_by_cols` |
| `rhsSelect : List Col` *(mut)* | the rhs subquery's SELECT-clause column list — `self.rhs.select` together with `self.rhs.default_cols` (`django/db/models/sql/query.py:177,164`), as cleared by `clear_select_clause()` (`query.py:1861`) and repopulated by `add_fields(['pk'])` (`query.py:1893`) | the mutable carrier state the patch conditionally rewrites |
| `rhsIsExpr : Bool` | `hasattr(self.rhs, 'get_group_by_cols')` (`lookups.py:411` post-patch) | whether the rhs is a column-contributing expression (a subquery) vs a direct value list |
| `rhsHasSelectFields : Bool` | `getattr(self.rhs, 'has_select_fields', True)` — the rhs `Query.has_select_fields` property (`django/db/models/sql/query.py:243`) | whether the rhs subquery explicitly names a select list |
| `pkCol : Col` | the column produced by `self.rhs.add_fields(['pk'])` (`lookups.py:413`) — the subquery model's primary-key column | the single column the clamp installs |
| `lhsCols : List Col` *(free input — directive 7)* | `self.lhs.get_group_by_cols()` (`lookups.py:410`) | the lhs's contributed grouping columns; the unchanged delegated callee |
| `rhsCols : List Col` *(free input — directive 7)* | `self.rhs.get_group_by_cols()` (`lookups.py:414`) | the rhs's contributed grouping columns; the unchanged delegated callee |
| `Col` (opaque `structure`, `DecidableEq`) | a column expression that may appear in a GROUP BY / SELECT clause; its **identity** is the observable | only identity matters (which object); internal content is never inspected |

The inherited method the override replaces (refinement audit only, not in the
consumer spec view): `Lookup.get_group_by_cols` (`lookups.py:117`), which computes
`cols = self.lhs.get_group_by_cols()` then unconditionally
`cols.extend(self.rhs.get_group_by_cols())` — i.e. WITHOUT the select-clause clamp.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a column expression (`Col`/expression object) appearing in SELECT or GROUP BY; de-duplicated by identity | `Col` (opaque `structure`, `DecidableEq`) | a distinct expression object ↔ a distinct `Col`; object identity (`a is b`) ↔ `Col` equality; internal content never inspected |
| `list` of grouping columns returned by `get_group_by_cols` | `List Col` | Python `list` ↔ Lean `List`; order and length preserved; element-wise identity bijection above |
| the rhs subquery's SELECT clause (`rhs.select` tuple together with `rhs.default_cols`) | `List Col` | the ordered tuple of selected column objects ↔ `List Col`; **`default_cols=True` (no explicit select) ↔ the entry value `rhsSelectOld`** (an arbitrary multi-column list standing for "all default columns"); after the clamp, `rhs.select == (pk_col,)` and `default_cols=False` ↔ the singleton `[pkCol]` |
| `hasattr(self.rhs, 'get_group_by_cols')` | `rhsIsExpr : Bool` | `True ↔ true` (rhs is a subquery / expression), `False ↔ false` (rhs is a direct value list) |
| `getattr(self.rhs, 'has_select_fields', True)` | `rhsHasSelectFields : Bool` | `True ↔ true`, `False ↔ false`; the default-`True` behaviour for a rhs lacking the attribute is folded into the bool the model receives |
| the pk column installed by `add_fields(['pk'])` | `pkCol : Col` | the resolved primary-key column object ↔ a distinguished `Col`; the observable is that the post-clamp select is **exactly this one column** |
| `alias=None`/`alias='...'` parameter | (not modeled) | the patch body ignores `alias` entirely (accepted only for signature compatibility); it influences neither the returned cols nor the clamp, so it is not a free input |

`get_group_by_cols` returns the actual expression objects and `rhs.select` holds
the actual column objects; downstream GROUP BY / SELECT construction
de-duplicates and emits by identity. Hence G-CONF compares both the returned
columns and the post-clamp select clause by **object identity** (`id(c)`), which
is what the `Col` abstraction (identity-only, `DecidableEq`) models.

## 3. Callee provenance — the delegated steps are FREE inputs (directive 7)

There is **no `axiom`** and **no deep-model reference** in this bundle. The two
unchanged steps the operation delegates to —
`self.lhs.get_group_by_cols()` and `self.rhs.get_group_by_cols()` — are modeled
as the FREE inputs `lhsCols` and `rhsCols`: the postconditions hold for EVERY
value of those inputs, so the callees are owed no contract (the spec is strictly
weaker than any concrete implementation of either delegated step). This is the
directive-7-correct treatment of unchanged callees the fix merely *forwards to*:
there is nothing to axiomatize, hence no G-AX.

Critically, the clamp does NOT change what `self.rhs.get_group_by_cols()`
returns: for the non-aggregating subquery the issue exercises,
`Query.get_group_by_cols` returns `[self]` (the rhs object itself,
`django/db/models/expressions.py:348`), whose identity is unaffected by
`clear_select_clause()`/`add_fields(['pk'])`. So `rhsCols` is genuinely a free
input independent of `rhsSelect`, and the patched method's RETURN value is
identical to the pre-patch method's. The behaviour the F2P test observes is
entirely the **side effect** on the rhs select clause (a directive-5 mut-frame
property): when the subquery names no explicit select fields, its select clause
must be clamped to the single pk column, so the subquery used in the IN/GROUP BY
returns exactly one column (otherwise: "subquery must return only one column").

The pinned behaviour is a property of the **caller** (it clamps the rhs select
exactly when the rhs is a column-contributing subquery with no explicit select
fields, and otherwise preserves it), grounded structurally in the relation
between `rhsSelect` and the actual inputs — not an ungrounded oracle (directive 8).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14351`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`inGroupByCols` (`rhsSelect = clampedSelect …`, `out = contributedCols …`) to
Python and derives `lhsCols`/`rhsCols`/`pkCol` exactly as the gold delegation
does — `self.lhs.get_group_by_cols()`, `self.rhs.get_group_by_cols()`, and the
real resolved pk column — then runs the REAL patched
`In.get_group_by_cols(alias=alias)` as the oracle, comparing (a) the returned
column list by identity and (b) the rhs select-clause post-state (the `select`
tuple by identity, and `default_cols`) over the F2P matrix
(subquery-with/without explicit select fields × direct-value rhs) plus ≥10⁵
fuzzed configurations.
