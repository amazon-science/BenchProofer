# mapping.md — symbol binding & type bijection (django__django-10880)

## Modeled function
- **Lean** `implementation_buildCallSql : List Char → Bool → List Char → List Char`
- **Python** `Aggregate.as_sql(self, compiler, connection, **extra_context)` —
  `django/db/models/aggregates.py:70-88 @ base_commit`.

The function builds the SQL text for an aggregate function invocation from the
template `'%(function)s(%(distinct)s%(expressions)s)'` (class attribute
`Aggregate.template`, line 17). Before rendering, it computes the value of the
`distinct` template slot:

```python
extra_context['distinct'] = 'DISTINCT' if self.distinct else ''   # base (buggy)
extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''  # patched
```

The rendered call (the no-filter path, which the F2P test exercises) is
`super().as_sql(...)` = the template with `function`, `distinct`, `expressions`
substituted. The observable behavior demanded by the F2P test is the separator
between the DISTINCT keyword and the expression text: post-patch
`COUNT(DISTINCT CASE WHEN ... END)`, pre-patch the broken
`COUNT(DISTINCTCASE WHEN ... END)`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `self.function` (e.g. `'COUNT'`) — the function name string | `function : List Char` | a SQL identifier, per-character |
| `self.distinct` (bool) | `distinct : Bool` | DISTINCT modifier flag |
| `expressions` slot (rendered inner SQL, e.g. `'CASE WHEN ... END'`) | `expressions : List Char` | the already-rendered argument SQL text |
| rendered call SQL (output `sql` string) | `List Char` | per-character; params list is unaffected by the fix and not modeled |

The template `'%(function)s(%(distinct)s%(expressions)s)'` substitution into a
*literal* template is, semantically, the fixed-order concatenation
`function + '(' + distinct + expressions + ')'`. It is reproduced exactly as an
**I** (identical concrete op), not axiomatized.

## Callee provenance
- `super().as_sql` (`Func.as_sql`) does the `%`-substitution into the literal
  `template`. UNCHANGED by the patch; reproduced concretely as the literal-driven
  concatenation above (I-tagged), so no `opaque`/axiom is needed.
- The `distinct`-slot value (`'DISTINCT '` vs `''`) is the **changed op**; it is
  modeled deeply as `distinctKeyword` (R/I), NOT axiomatized.
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is a
  skip stub.

## Flag dependency
The DISTINCT keyword is emitted only when `self.distinct` is true (it requires
`allow_distinct = True`, which `Count` sets; line 108). G-CONF fuzzes both flag
values.

## Scope note
The F2P path has `self.filter is None`, so `as_sql` returns the bare templated
call. The two filter branches (lines 72-87) re-render the same template with the
same `distinct` slot, so the distinct-separator fix is identical there; the
filter wrapping is orthogonal to the modeled behavior and is not modeled.

## G-CONF fuzz seed
Pinned seed: **10880**. ≥10^5 fuzzed inputs over function-name / expression
alphabets plus both DISTINCT flag values.
