# mapping.md — django__django-15467

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e0442a628eb480eac6a7888aed5a86f83499e299`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one deep-model reference.

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `emptyLabelFor (allowsBlank : Bool) (override : Option (Option String))` | the empty-placeholder resolution statement inside `ModelAdmin.formfield_for_foreignkey` — `django/contrib/admin/options.py:251` (body), the assignment at line **272** (`kwargs["empty_label"] = …`) | the modeled changed slice: choose the placeholder shown for the empty selection of a radio-rendered ForeignKey |
| `allowsBlank : Bool` | `db_field.blank` (the related model field's `blank` attribute) | R: whether an empty selection is admitted |
| `override : Option (Option String)` | the caller-supplied `kwargs` entry for the empty-placeholder key, with **key-presence** semantics: `none` ↔ key absent, `some v` ↔ key present with value `v` (`v = none` ↔ explicit `None`) | R: what the caller already provided |
| `out : Option String` | the value the slice writes to `kwargs["empty_label"]`, ultimately the `empty_label` of the constructed `ModelChoiceField` | R: the resolved placeholder |
| `defaultLabel` *(deep model — A-reference)* | `_("None")` — `gettext("None")` via `from django.utils.translation import gettext as _` (`django/contrib/admin/options.py:65`) | the standard fallback placeholder; deep model `some "None"`, validated `== _("None")` by axiom_check.py (G-AX) under the default (English / no-translation) locale the F2P test runs in |
| `resolvedLabel` | the resolution expression `kwargs.get(<key>, _("None")) if db_field.blank else None` (post-patch, line 272-274) | pure spec: the resolved placeholder as a closed function of the two inputs |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): `_("None") if db_field.blank else None` — i.e. the blank
branch always installed `_("None")`, discarding any caller-supplied value.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `db_field.blank` (a `bool`) | `Bool` | `True ↔ true`, `False ↔ false` |
| the `kwargs` empty-placeholder entry | `Option (Option String)` | key absent ↔ `none`; key present with a string `s` ↔ `some (some s)`; key present with Python `None` ↔ `some none` |
| a placeholder value (Python `str` or `None`) | `Option String` | `None ↔ none`; a string `s ↔ some s` (content compared as a Python `str`) |
| `_("None")` / `gettext("None")` (`options.py:272`) | `defaultLabel = some "None"` | under the default locale (no active translation, the F2P test's environment) `gettext("None") == "None"`, so the placeholder string is `"None"`; G-AX validates this against the real callee |
| `dict.get(key, default)` (`options.py:272`, post-patch) | `Option.getD` | `kwargs.get(key, d)` ↔ `override.getD d`: returns the stored value if the key is present, else `d` |

Note on key-presence: the gold uses `kwargs.get("empty_label", _("None"))`, which
distinguishes *key absent* (→ default) from *key present with value `None`*
(→ `None` kept). The carrier `Option (Option String)` preserves exactly this
three-way distinction; modeling the override as a plain `Option String` would
conflate "absent" with "present-and-None" and weaken the spec, so the nested
option is load-bearing.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `defaultLabel` deep model ↔ `gettext("None")` (A-reference)
**Callee:** `django.utils.translation.gettext` applied to the literal `"None"`.
The fallback placeholder is modeled **deeply** as the literal `some "None"`;
there is **no consumed axiom** about `gettext`. Under the default locale active
in the admin-widgets test environment (no translation catalog installed for the
test models), `gettext("None")` returns the source string `"None"` unchanged.

**Soundness check (G-AX):** `axiom_check.py` configures a minimal Django settings
module and calls the real `django.utils.translation.gettext("None")`, asserting
it equals `"None"` (the `defaultLabel` model) under the default locale, and also
exercises `gettext_lazy` resolution to a `str`. It then drives the resolution
function `resolved_label` (the Python transliteration of `resolvedLabel`) against
the placeholder semantics over boundary + fuzz inputs. Imports only `django`
(present in the instance image) + stdlib. Exit 0 iff sound.

`gettext` is **not** the function under change and is **not** axiomatized as a
consumed contract; it is an unchanged callee whose single observed value the deep
model `defaultLabel` reproduces, validated by G-AX.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15467`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `resolvedLabel`/`emptyLabelFor` (R/I-tagged ops) to Python and
compares against the **real patched** `ModelAdmin.formfield_for_foreignkey`
(the gold patch applied at base_commit by the harness): it constructs a
`ModelAdmin` over a self-referential `ForeignKey`, with and without
`formfield_overrides`/explicit `empty_label`, with `radio_fields` set, and reads
back the resulting form field's `empty_label`. The `defaultLabel` A-reference
value (`gettext("None")`) is left to the real callee in the oracle, not the
model, so the shadow's `defaultLabel` is the literal `"None"` and the oracle's is
the real `gettext` result (equal under the test locale, per §3.1).
