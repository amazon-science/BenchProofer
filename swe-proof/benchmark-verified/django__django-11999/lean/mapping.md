# mapping.md — symbol binding & type bijection (django__django-11999)

## Modeled function

The fix touches one function that, when a model field carries an enumerated set
of `choices`, installs an auto-generated display accessor method named
`get_<fieldname>_display` onto the model class' attribute namespace. The bug
installed it unconditionally, clobbering any accessor the user already declared;
the fix installs it only when the class does not already provide one.

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_registerDisplay` / `problem_spec_registerDisplay` / `correct_registerDisplay` | `Field.contribute_to_class` — the `self.choices is not None` registration block | `django/db/models/fields/__init__.py:749` (def), block at `:762-765` (changed lines `:763-765`) |

## Type bijection (used by G-CONF and G-AX)

| Python value | Lean model | notes |
|---|---|---|
| the model class' resolved attribute namespace `cls` (incl. MRO) as seen by `hasattr`/`setattr` | `attrs : List (String × Val)` (assoc list, key→value) | only key membership and the stored value are observable; attribute lookup is by-key, so order is not observable — G-CONF compares the induced mapping (dict) |
| attribute method object (the generated `partialmethod(...)` OR a user-declared method) | `Val` (an opaque value type; modeled as an `Int` tag in G-CONF) | the proof is parametric in `Val`; only key presence and value identity matter |
| the field's `self.name` | `name : String` | |
| the guard `self.choices is not None` | `hasChoices : Bool` | `True` ⇔ field has an enumerated choice set |
| `'get_%s_display' % self.name` | `displayKey name = "get_" ++ name ++ "_display"` | `%`-format ↔ concatenation; `get_..._display` appears verbatim in the public problem statement |
| `hasattr(cls, key)` | `hasKey attrs key` (Bool) | membership of key in the namespace mapping |
| `setattr(cls, key, v)` | `setKey attrs key v` (replace-or-append) | Python attribute assignment; modeled concretely as an `I`/`R` op, NOT axiomatized |
| `partialmethod(cls._get_FIELD_display, field=self)` | `display : Val` (input) | the default accessor object is an INPUT to the modeled function; its construction is not in scope |

## Callee provenance

- `hasattr`, `setattr`, `%`-formatting are CPython builtins; all are modeled
  deeply/concretely as `hasKey` / `setKey` / `displayKey` (R/I ops). None is an
  axiomatized callee, so the `axioms` region is empty and G-AX is a skip stub.
- `partialmethod(...)` is not modeled — its result is the `display` input.

## Flag dependency

The registration block runs only under `self.choices is not None`
(`hasChoices = true`); G-CONF fuzzes both flag values.

## G-CONF fuzz seed

`conf_seed = 11999` (pinned; see meta.json).
