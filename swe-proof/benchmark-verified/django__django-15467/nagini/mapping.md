# mapping.md — django__django-15467

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e0442a628eb480eac6a7888aed5a86f83499e299`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `set_radio_empty_label(permits_empty, kwargs)` | the radio-fields branch of `ModelAdmin.formfield_for_foreignkey` — `django/contrib/admin/options.py:266-272` (the assignment `kwargs["empty_label"] = ...` on line 272) | the modeled changed behaviour: choosing the empty-choice label entry of the keyword mapping |
| `empty_label_key()` | the string key literal `"empty_label"` | the distinguished mapping key (string → fixed int token) |
| `absent_label()` | Python `None` (the value assigned when `not db_field.blank`) | sentinel: no empty choice offered (None → fixed int code) |
| `default_label()` | `_("None")` — the lazily-translated built-in default label | the built-in default empty-choice label (string label → fixed int code) |
| `permits_empty` (param) | `db_field.blank` (a `bool` attribute of the relation field) | whether the relation permits the empty selection |
| `kwargs` (param) | the `**kwargs` mapping accumulated by `formfield_for_foreignkey` and passed to `db_field.formfield(**kwargs)` (line 279) | the keyword mapping; the observable the F2P test reads (`ff.empty_label`) |

The enclosing guards on lines 257/262/266 (`"widget" not in kwargs`,
`db_field.name in self.radio_fields`) select the branch in which this
assignment occurs; they are context, not part of the modeled assignment, so
they are not referenced from the consumer spec view.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `kwargs: dict` with string keys and arbitrary values | `Dict[int, int]` | the key `"empty_label"` ↔ the int token `empty_label_key()==1`; a label value ↔ an int code; key membership ↔ membership in the dict; `kwargs.get(k, d)` ↔ `kwargs[k] if k in kwargs else d` |
| `db_field.blank: bool` | `permits_empty: bool` | identity (a Python bool) |
| `_("None")` (a lazy translation proxy, a concrete non-None label) | `default_label() == 2` | a fixed label code distinct from the absent sentinel and from any caller label |
| `None` (the value when the relation forbids empty) | `absent_label() == 0` | a fixed sentinel code distinct from every real label |
| a caller-supplied empty-choice label (e.g. `"Custom empty label"`) | any int value stored at `empty_label_key()` distinct from the model's fixed codes | the caller's value; read back verbatim |
| `db_field.formfield(**kwargs)` + the resulting field's `.empty_label` | the post-state of `kwargs[empty_label_key()]` (= `Result()`) | `formfield` forwards the `empty_label` kwarg to the field unchanged; the observable `ff.empty_label` is exactly the mapping's `empty_label` entry at call time |

Because the WHOLE mapping is subsequently splatted into
`db_field.formfield(**kwargs)`, every key of the mapping — not just the
empty-choice entry — is runtime-observable (an extra, dropped, or revalued
entry changes or crashes the built field). The spec therefore carries a frame
postcondition pinning every key other than `empty_label_key()` unchanged
(membership and value), matching the real code, whose only write in this slice
is to the empty-choice key.

The two distinct facts the gold's `dict.get(key, default)` distinguishes —
"key present" vs "key absent" — are modeled by dict **membership** (`k in
kwargs`), NOT by value truthiness. This is faithful to the gold, which uses
`kwargs.get("empty_label", _("None"))` (present value kept verbatim, even when
falsy), rather than the `… or _("None")` form floated in the issue (which would
replace a falsy present value). The spec's "membership wins regardless of value
truthiness" clause pins the gold's `.get(key, default)` semantics.

## 3. Callee provenance (kind-A)

None. The changed operation is a mapping update built only from dict membership
(`in`), dict indexing (`[]`), a boolean test, and assignment — all expressed
deeply in the impl region. `dict.get(key, default)` is the unchanged language
primitive being recomposed, and it is modeled deeply (`kwargs[k] if k in kwargs
else d`), so there is **no `@ContractOnly` axiom** and therefore no
`axiom_check.py` / G-AX obligation. `_("None")` (gettext lazy translation) is a
constant from this behaviour's perspective (the built-in default label,
`default_label()`); it is not a callee whose behaviour the fix depends on.
