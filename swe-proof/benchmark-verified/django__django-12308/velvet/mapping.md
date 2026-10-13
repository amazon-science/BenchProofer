# mapping.md — django__django-12308

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2e0f04507b17362239ba49830d26fec504d46978`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `django/contrib/admin/utils.py` (the read-only-admin
value renderer).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `displayJson (v : ValueView)` | `display_for_field(value, field, empty_value_display)` — `django/contrib/admin/utils.py:380` (the inserted branch + its fall-through, body lines 398-405) | the modeled changed function, restricted to the JSON-typed-field dispatch the change governs |
| `jsonDisplay (v : ValueView)` | the dispatch logic of `display_for_field` on the JSON-field branch (`utils.py:401-405` post-patch) | pure spec: the display string chosen for a JSON-typed value |
| `ValueView.present` | Python truthiness `bool(value)` (`value` in `... and value`, `utils.py:401`) | observable: whether the value counts as present |
| `ValueView.prep` *(deep-model reference)* | `field.get_prep_value(value)` — `JSONField.get_prep_value`, `django/db/models/fields/json.py:81` (`return json.dumps(value, cls=self.encoder)`); the `try/except TypeError` distinguishes success from non-serializable | observable: the JSON-serialization outcome (`json (text)` on success, `unserializable` on `TypeError`) |
| `ValueView.generic` *(deep-model reference)* | `display_for_value(value, empty_value_display)` — `django/contrib/admin/utils.py:405` | observable: the generic textual rendering (the existing fall-through), which itself renders an absent value as `empty_value_display` |

No module-level `axiom`. Both helpers (`get_prep_value`/`json.dumps`,
`display_for_value`) are **unchanged** by the patch; their outcomes are carried
as the observable fields `prep`/`generic` of the value view and validated
against the real callees by axiom_check.py (G-AX). The modeled behaviour is the
**choice** among those outcomes — the new branch and its `try/except` fallback.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the admin value `value` rendered for a `JSONField` | `ValueView` (its three observable facts) | a Python `value` ↔ the `ValueView` `{present := bool(value), prep := prep(value), generic := display_for_value(value, empty)}`; the renderer reads only these three facts of `value` |
| `bool(value)` (Python truthiness, `utils.py:401`) | `ValueView.present : Bool` | `True ↔ true`, `False ↔ false`; empty containers / empty string / `0` / `None` are `false`, all else `true` |
| `field.get_prep_value(value)` outcome | `ValueView.prep : PrepResult` | a successful `json.dumps(value)` returning text `t` ↔ `PrepResult.json t.toList`-as-`String`; a raised `TypeError` ↔ `PrepResult.unserializable` |
| `display_for_value(value, empty_value_display)` | `ValueView.generic : String` | the returned `str` ↔ the Lean `String` verbatim (character content); for `value is None` it equals `empty_value_display` |
| the returned display `str` | `displayJson` result `String` | identity on character content (the F2P `assertEqual` compares the rendered string verbatim) |

The `field` parameter and the `isinstance(field, models.JSONField)` type guard
are R-collapsed: `displayJson` IS the JSON-typed branch (the bijection fixes the
field to a `JSONField`; `models.JSONField` exists at this base_commit —
`django/db/models/__init__.py:21,47`). The earlier `if/elif` arms of
`display_for_field` (`flatchoices`, `BooleanField`, `None`, date/number/file)
are orthogonal to the JSON value path and out of this model's scope; for a
`JSONField` value none of them fire before the JSON branch except the
`value is None` arm, which `display_for_value` reproduces (an absent value →
`empty_value_display`), so `generic` faithfully covers it.

## 3. Callee provenance (deep-model references — checked by G-AX / axiom_check.py)

### 3.1 `prep` ↔ `JSONField.get_prep_value` (A-reference)
**Callee:** `JSONField.get_prep_value(value)` = `json.dumps(value, cls=self.encoder)`
with the default encoder (`django/db/models/fields/json.py:81`). It returns the
JSON serialization on success and raises `TypeError` for a value `json.dumps`
cannot serialize (e.g. a dict with a tuple key). The `prep` field models exactly
this outcome split (`json text` vs `unserializable`); axiom_check.py runs the
real `JSONField().get_prep_value` and asserts `prep(value)` matches it (text on
success, `unserializable` iff it raises `TypeError`). Not consumed as an axiom —
it is a deeply-modeled observable.

### 3.2 `generic` ↔ `display_for_value` (A-reference)
**Callee:** `display_for_value(value, empty_value_display)`
(`django/contrib/admin/utils.py:405`), **unchanged** by the patch. The `generic`
field is its return value verbatim; axiom_check.py runs the real
`display_for_value` and asserts `generic == display_for_value(value, empty)`.

### 3.3 `present` ↔ `bool(value)` (A-reference)
Python truthiness, unchanged. axiom_check.py asserts `present == bool(value)`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12308`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`jsonDisplay`'s branch logic to Python (the if-ladder + match) and bridges the
three observable facts via the §2/§3 bijection, leaving the deeply-modeled
callees (`get_prep_value`, `display_for_value`) as the **real repo callees**. It
diffs the shadow against `patch.diff`'s `display_for_field(value, JSONField(),
empty)` over ≥10⁵ fuzzed values. Exit 0 iff zero disagreements.
