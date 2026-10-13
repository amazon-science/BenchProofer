# mapping.md — django__django-15561

Symbol binding, the Lean↔Python type bijection, callee provenance, and the
pinned G-CONF fuzz seed. Binding commit: `base_commit`
`6991880109e35c879b71b7d9d9c154baeec12b89`.

## Modeled function

| Lean | Python (file:line @ base_commit) |
|---|---|
| `implementation_requiresColumnChange` / `problem_spec_requiresColumnChange` | `BaseDatabaseSchemaEditor._field_should_be_altered(self, old_field, new_field)` — `django/db/backends/base/schema.py:1371-1399` |

`_field_should_be_altered` returns a bool: `True` ⇒ altering the field requires
a column-level schema change (SQL is emitted); `False` ⇒ the change is a no-op
(no SQL). The fix makes a *choices-only* field change a no-op.

Real post-patch body (`patch.diff`):
```python
def _field_should_be_altered(self, old_field, new_field):
    _, old_path, old_args, old_kwargs = old_field.deconstruct()
    _, new_path, new_args, new_kwargs = new_field.deconstruct()
    for attr in old_field.non_db_attrs:
        old_kwargs.pop(attr, None)
    for attr in new_field.non_db_attrs:
        new_kwargs.pop(attr, None)
    return self.quote_name(old_field.column) != self.quote_name(
        new_field.column
    ) or (old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)
```
where `Field.non_db_attrs` (added by the patch, `django/db/models/fields/__init__.py:143-159`)
is the tuple `("blank", "choices", "db_column", "editable", "error_messages",
"help_text", "limit_choices_to", "on_delete", "related_name",
"related_query_name", "validators", "verbose_name")`.

## Type bijection (G-CONF + G-AX use this)

| Python | Lean |
|---|---|
| a `Field` instance, observed through `deconstruct()` + `.column` | `structure Field` with `column : String`, `path : String`, `args : List String`, `kwargs : List (String × String)` |
| `old_field.column` (resolved db column name) | `Field.column` |
| `deconstruct()` → `(name, path, args, kwargs)` | the `path`/`args`/`kwargs` fields (the deconstruct `name`, the first tuple slot, is never read by `_field_should_be_altered`, so it is not modeled) |
| `path : str` (import path of the field class + ctor) | `Field.path : String` |
| `args : list` (positional deconstruct args) | `Field.args : List String` (each arg as its canonical repr) |
| `kwargs : dict[str, Any]` (keyword deconstruct args) | `Field.kwargs : List (String × String)` (attr name → canonical repr of its value) |
| `self.quote_name(name)` | `opaque quoteName : String → String` |
| the popped-attr set (`non_db_attrs`, post-patch tuple) | `ignoredAttrs : List String` (pure region; carries `"choices"`) |
| `kwargs.pop(attr, None)` over the set | `popAttrs ignoredAttrs kwargs` (spec) / accumulator `for … filter` loop (impl) |
| `(path, args, kwargs1) != (path2, args2, kwargs2)` (dict/tuple `!=`) | `(p,a,k) ≠ (p',a',k')` structural `≠` on `String × List String × List (String × String)` |

### `kwargs` ordering note (modeling decision)
Python compares `(old_path, old_args, old_kwargs) != (...)` where the kwargs are
`dict`s — equality is **content** (order-independent). The Lean model uses an
association `List (String × String)` with order-sensitive `≠`. This is faithful
because both fields are deconstructed by the **same** `deconstruct()` code path,
which builds kwargs in a fixed, deterministic key order (Python ≥3.7 dicts
preserve insertion order; `Field.deconstruct` inserts keys in a fixed source
order). Two fields of the same class therefore yield kwargs in identical key
order, so list-equality coincides with dict content-equality on the modeled
domain. G-CONF builds both kwargs dicts in matching key order to honor this.

### `quote_name` note (callee)
`quote_name` is an UNCHANGED callee; it quotes an identifier (e.g. SQLite:
`'"%s"' % name.replace('"', '""')`) and is **injective**. It is left
`opaque quoteName : String → String` and used **identically** in spec and impl,
so no property of it is consumed by the proof (A-reference, not A-consumed); the
`#print axioms` stays clean of any `quoteName_prop`. G-CONF uses a faithful
in-process `quote_name` replica (the SQLite quoting) in both oracle and shadow,
so no injectivity assumption is needed there either.

## `non_db_attrs` as a code constant (elidable corner)
Post-patch the loop iterates `old_field.non_db_attrs` / `new_field.non_db_attrs`
— a **class attribute**. For the base `Field` (and every field in the F2P/PASS
tests) both equal the constant tuple above. A third-party subclass could override
`non_db_attrs`; that sub-class-specific override is an elidable corner not
exercised by any F2P/PASS test, so the modeled value pops the fixed base-`Field`
set `ignoredAttrs`. The observable fix — `"choices"` is among the ignored attrs —
is fully captured. Recorded as an elidable corner (does not affect F2P).

## Flag dependencies
None. `_field_should_be_altered` reads no configuration flag; the decision is a
pure function of the two field descriptions.

## G-CONF fuzz seed
`SEED = 15561` (also hard-coded in `conformance_check.py`).
