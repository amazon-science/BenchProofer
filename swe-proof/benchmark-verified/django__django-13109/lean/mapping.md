# mapping.md — django__django-13109

## Symbol binding (file:line @ base_commit fbe82f82555bc25dccb476c749ca062f0b522be3)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_validateReference` / `problem_spec_validateReference` | `ForeignKey.validate` | `django/db/models/fields/related.py:909-928` |
| `Row` (pure helper) | one candidate object of the referenced model's stored table, together with the two booleans the existence query observes | see field table below |

The modeled function is `ForeignKey.validate(value, model_instance)`. It is the
only function whose behavior changes and the behavior the FAIL_TO_PASS tests
observe (`test_FK_validates_using_base_manager`,
`test_validate_foreign_key_to_model_with_overridden_manager`): a reference to a
stored object that the referenced model's *default* presentation filter hides
(in the tests, an `archived=True` row) must still validate, because the object
genuinely exists in the underlying table.

### What the function does (base_commit)

```python
def validate(self, value, model_instance):
    if self.remote_field.parent_link:
        return                                  # no existence check for parent links
    super().validate(value, model_instance)     # required/blank checks (out of scope)
    if value is None:
        return                                  # null reference: nothing to check
    using = router.db_for_read(self.remote_field.model, instance=model_instance)
    qs = self.remote_field.model._default_manager.using(using).filter(
        **{self.remote_field.field_name: value}
    )
    qs = qs.complex_filter(self.get_limit_choices_to())
    if not qs.exists():
        raise exceptions.ValidationError(self.error_messages['invalid'], code='invalid', ...)
```

The existence query is built from a *manager*. A manager exposes a base
collection of rows:

* the **default manager** (`_default_manager`) returns `get_queryset()`, which a
  model may override to apply a standing filter (e.g. exclude `archived=True`
  rows). Rows excluded by that filter are invisible through this manager.
* the **base manager** (`_base_manager`) returns the unfiltered collection — all
  stored rows, regardless of the model's default presentation filter.

The query then keeps the rows whose related field equals `value`
(`.filter(field_name=value)`) and that satisfy the choice constraint
(`.complex_filter(get_limit_choices_to())`); validation succeeds iff at least one
such row remains. The observable fix swaps which base collection the query starts
from: from the default-filtered view to the unfiltered base collection.

### `Row` field ↔ Python expression bijection

The verdict for a value reduces to observations on each stored row of the
referenced model's table.

| `Row` field | Python meaning | notes |
|---|---|---|
| `key` | the row's value for `self.remote_field.field_name` (the column the FK targets, e.g. `pk`) | `Nat`. The query matches rows with `key == value`. |
| `defaultVisible` | whether the row survives the model's default manager `get_queryset()` filter (e.g. `archived == False`) | `Bool`. `false` ⇒ the row is hidden through `_default_manager` but still present in `_base_manager`. This is the only field whose treatment changes between pre- and post-fix. |
| `limitOk` | whether the row satisfies `self.get_limit_choices_to()` (the `complex_filter` constraint) | `Bool`. Folded deeply into the row: `complex_filter(get_limit_choices_to())` keeps a row iff it satisfies the constraint. |

The whole input is `(parentLink : Bool, value : Option Nat, rows : List Row)`:

| Lean input | Python meaning |
|---|---|
| `parentLink` | `self.remote_field.parent_link`. `true` ⇒ early `return` (no existence check, always valid). |
| `value` | the foreign-key value being validated. `none` ⇒ `value is None` early `return` (valid). `some v` ⇒ existence check for `v`. |
| `rows` | the referenced model's underlying (base) stored table — ALL rows, each annotated with `key`, `defaultVisible`, `limitOk`. The choice of manager selects WHICH subset of `rows` the query starts from. |

The result models the existence-check verdict: `true` = no `ValidationError`
raised for the reference (validation passes), `false` = `qs.exists()` was false so
a `ValidationError` is raised.

`super().validate(...)` (required/blank checks) is an unchanged callee whose
outcome is orthogonal to the manager-selection fix; the modeled result is the
FK-existence verdict conditioned on reaching that check, so `super().validate` is
abstracted out (it is neither the changed op nor consumed by the spec).

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| referenced model's base table (set of rows) | `List Row` | each list element ↔ one stored row; `key`/`defaultVisible`/`limitOk` ↔ the three observables the existence query consults. |
| `self.remote_field.parent_link` | `parentLink : Bool` | the parent-link early-exit gate. |
| the FK value (or `None`) | `value : Option Nat` | `none` ↔ `None` (null reference). |
| `not qs.exists()` ⇒ raise / else success | `result : Bool` | `true` ↔ validation passes (no error), `false` ↔ `ValidationError` raised. |

The function returns `None` / raises; we model it as a pure function returning
the existence-check verdict as a `Bool`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — which base
  collection the existence query starts from — is modeled DEEPLY as the choice of
  whether the row scan honors `defaultVisible` (default manager) or ignores it
  (base manager). The post-fix collection is the full `rows`; the pre-fix
  collection is `rows.filter (·.defaultVisible)`. This is a list transformation
  over the modeled rows, not an axiom (SPEC_GUIDE §3: a deeply-modeled changed
  decision is never axiomatized). `_default_manager` / `_base_manager` are the
  operations the patch swaps; their differing visibility semantics ARE the
  modeled content, so there is no opaque callee whose contract the proof consumes.
- **`complex_filter(get_limit_choices_to())`** is unchanged across the patch; it
  is folded into the per-row `limitOk` observable (it keeps a row iff the row
  satisfies the choice constraint). Both pre- and post-fix code apply it
  identically, so it does not discriminate the fix.
- **`super().validate` / `router.db_for_read`** are unchanged and orthogonal to
  the manager-selection fix; abstracted out of the modeled verdict (see above).
- **Gate dependencies.** `parent_link` and `value is None` both short-circuit to
  a valid verdict before any existence query; modeled exactly by the
  `parentLink` and `value = none` branches.

## G-CONF fuzz seed

Pinned LCG seed: **13109** (see `conformance_check.py` `SEED`). Corpus:
randomized base tables (length 0–8, each row with `key` drawn from `0..4`,
`defaultVisible`/`limitOk` random booleans) crossed with `parentLink ∈ {True,
False}` and `value ∈ {None} ∪ {0..4}`, over ≥1e5 fuzzed inputs, diffed against an
in-process replica of the post-patch behavior (existence checked over the
unfiltered base collection, ignoring `defaultVisible`).
