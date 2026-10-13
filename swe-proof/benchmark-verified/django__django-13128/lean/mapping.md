# mapping.md — django__django-13128

## Symbol binding (file:line @ base_commit 2d67222472f80f251607ae1b720527afceba06ad)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_resolveKind` / `problem_spec_resolveKind` | `CombinedExpression.resolve_expression` | `django/db/models/expressions.py:476-481` (base_commit) |
| `ExprKind` (pure) | the *class* of the resolved expression object (`CombinedExpression` vs `DurationExpression` vs `TemporalSubtraction`) | see field table |
| `FieldType` (pure) | the string returned by `output_field.get_internal_type()` (`'DurationField'`, `'DateField'`, `'DateTimeField'`, `'TimeField'`, or any other) | `Option` models the `(AttributeError, FieldError)`→`None` case |
| `Connector` (pure) | `self.connector` — `self.SUB` vs any other operator | only the SUB / non-SUB distinction is observable |
| `isDateTimeField` (pure) | membership test `lhs_type in {'DateField','DateTimeField','TimeField'}` | the datetime-family family check |

The modeled function is `CombinedExpression.resolve_expression`. It is the
function whose behavior changes and that the FAIL_TO_PASS tests observe: an
arithmetic combination of two temporal operands (e.g. `F('completed') -
F('assigned')`) must, after resolution, become an expression that carries a
DurationField output type — so it can be annotated directly, without wrapping it
in an `ExpressionWrapper(..., output_field=DurationField())`.

### What the function does (base_commit, pre-fix)

```python
def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
    c = self.copy()
    c.is_summary = summarize
    c.lhs = c.lhs.resolve_expression(query, allow_joins, reuse, summarize, for_save)
    c.rhs = c.rhs.resolve_expression(query, allow_joins, reuse, summarize, for_save)
    return c
```

Resolution always returns a plain copy of the *same class*. A combination of two
date/datetime/time operands therefore stays a generic combined expression with no
determinate output type — hence the "Expression contains mixed types … You must
set output_field" error unless the caller wraps it.

### What the function does (post-fix)

```python
def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
    lhs = self.lhs.resolve_expression(query, allow_joins, reuse, summarize, for_save)
    rhs = self.rhs.resolve_expression(query, allow_joins, reuse, summarize, for_save)
    if not isinstance(self, (DurationExpression, TemporalSubtraction)):
        try:
            lhs_type = lhs.output_field.get_internal_type()
        except (AttributeError, FieldError):
            lhs_type = None
        try:
            rhs_type = rhs.output_field.get_internal_type()
        except (AttributeError, FieldError):
            rhs_type = None
        if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type:
            return DurationExpression(self.lhs, self.connector, self.rhs).resolve_expression(...)
        datetime_fields = {'DateField', 'DateTimeField', 'TimeField'}
        if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
            return TemporalSubtraction(self.lhs, self.rhs).resolve_expression(...)
    c = self.copy()
    c.is_summary = summarize
    c.lhs = lhs
    c.rhs = rhs
    return c
```

During resolution the expression now inspects the resolved operand types and, for
the two temporal cases, returns a *different class* of resolved expression:

* **DurationExpression** — when exactly one operand is a `DurationField` and the
  two operand types differ (a duration mixed with a non-duration). The recursive
  `.resolve_expression(...)` on the new `DurationExpression` re-enters this method
  with `self` now an instance of that class, so the `isinstance(...)` guard short
  circuits and a plain copy of the DurationExpression is returned (no infinite
  recursion).
* **TemporalSubtraction** — when the connector is subtraction and both operands
  share the same date/datetime/time type. `TemporalSubtraction` declares
  `output_field = DurationField()`, so the resolved expression now has a
  determinate output type.
* otherwise — a plain copy of the same class (the original behavior).

The fix's entire observable effect is **which class the resolved expression
becomes**; that class fixes the output field and therefore whether the annotation
is usable without an explicit wrapper. We model exactly that observable: the
resolved expression *kind*.

### Modeled-observable scope (directive 5 / frame)

The modeled output is the resolved expression's KIND (`ExprKind`). The other
effects of resolution — resolving the two operands, copying, and setting
`is_summary` — are unchanged between pre- and post-fix (the post-fix code resolves
the operands once up front and reuses them; the pre-fix code resolves them on the
copy; both produce a copy with the same operands and `is_summary = summarize`).
None of those components changes the behavior the FAIL_TO_PASS tests observe, so
the modeled output type `ExprKind` has no other component to pin — it is fully
determined by the inputs, leaving no frame hole.

### `ExprKind` ↔ Python class bijection

| `ExprKind` | Python class of the resolved expression | output type consequence |
|---|---|---|
| `combined` | `CombinedExpression` (or any subclass that is NOT a Duration/Temporal one) | generic combination; output type undetermined for temporal operands |
| `duration` | `DurationExpression` | duration-arithmetic expression |
| `temporal` | `TemporalSubtraction` | carries `output_field = DurationField()` |

### `FieldType` ↔ Python internal-type bijection

| `FieldType` (wrapped in `Option`) | `output_field.get_internal_type()` |
|---|---|
| `some FieldType.duration` | `'DurationField'` |
| `some FieldType.date` | `'DateField'` |
| `some FieldType.datetime` | `'DateTimeField'` |
| `some FieldType.time` | `'TimeField'` |
| `some FieldType.other` | any other internal type string (e.g. `'IntegerField'`) |
| `none` | `output_field` access raised `AttributeError`/`FieldError` (type unknown) |

### Inputs

| Lean input | Python meaning |
|---|---|
| `selfKind : ExprKind` | the class of the expression being resolved. The dispatch only runs when this is `combined` (the `not isinstance(self, (DurationExpression, TemporalSubtraction))` guard); a Duration/Temporal expression resolves to its own kind. |
| `connector : Connector` | `self.connector`; only `sub` (`self.SUB`) vs `other` matters. |
| `lhsType : Option FieldType` | the resolved left operand's `output_field.get_internal_type()`, or `none` if it raised. |
| `rhsType : Option FieldType` | the resolved right operand's `output_field.get_internal_type()`, or `none` if it raised. |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| class of resolved expression | `ExprKind` | `CombinedExpression`/`DurationExpression`/`TemporalSubtraction` ↔ `combined`/`duration`/`temporal`. |
| `get_internal_type()` string or raised access | `Option FieldType` | the five recognised strings ↔ the five `FieldType` constructors; raised access ↔ `none`. |
| `self.connector == self.SUB` | `connector = Connector.sub` | subtraction vs any other operator. |
| `isinstance(self, (DurationExpression, TemporalSubtraction))` | `selfKind ≠ ExprKind.combined` | the recursion-guard / already-classified case. |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The operations the dispatch consults —
  `lhs.resolve_expression(...)` (recursively resolving operands),
  `output_field.get_internal_type()` (the operand's type string), and the
  `isinstance` class test — are all UNCHANGED across the patch. Their *results*
  are the inputs to the modeled decision (`selfKind`, `connector`, `lhsType`,
  `rhsType`); the proof consumes none of them as an axiom. The behavior the patch
  changes — the classification decision itself — is modeled DEEPLY as a total
  function of those inputs (SPEC_GUIDE §3: a deeply-modeled changed decision is
  never axiomatized). Hence the `axioms` region is empty, `axiom_check.py` is a
  skip stub, and G-AX skips.
- **`'DurationField' in {lhs_type, rhs_type}` set membership** is modeled exactly:
  `lhsType = some duration ∨ rhsType = some duration`, combined with `lhsType ≠
  rhsType`. Set semantics with at most two elements reduce to this disjunction +
  inequality.
- **`datetime_fields = {'DateField','DateTimeField','TimeField'}` membership** is
  modeled by `isDateTimeField` (true for `some date`/`some datetime`/`some time`;
  false for `none`, since a raised-access type is not in the set).
- **Flag dependency.** The dispatch only fires for an expression that is not
  already a Duration/Temporal expression — modeled by gating on `selfKind =
  combined`. This is the recursion guard that lets the recursive resolve of the
  freshly-built subclass return a plain copy.
- **`DurationExpression.as_sql` native-duration short-circuit** (the third hunk of
  the gold patch) and the removed type-dispatch in `CombinedExpression.as_sql`
  (the first hunk) are downstream SQL-compilation refinements that follow from the
  relocation; they do not change the resolved-expression *kind* the FAIL_TO_PASS
  tests observe (the tests assert query results/values, which depend on the
  resolved class carrying the right output type). They are abstracted out of the
  modeled observable; see refinement.md (A-reference / abstracted rows).

## G-CONF fuzz seed

Pinned LCG seed: **13128** (see `conformance_check.py` `SEED`). The modeled input
space is finite (selfKind ∈ 3, connector ∈ 2, lhsType ∈ 6, rhsType ∈ 6 = 216
combinations); `conformance_check.py` enumerates ALL 216 exhaustively and
additionally fuzzes ≥1e5 randomly-drawn inputs, diffing the R/I shadow of the impl
against an in-process replica of the post-patch classification dispatch.
