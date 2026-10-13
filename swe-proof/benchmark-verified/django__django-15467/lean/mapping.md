# mapping.md — django__django-15467

## Symbol binding (file:line @ base_commit `e0442a628eb480eac6a7888aed5a86f83499e299`)

- Modeled function: `ModelAdmin.formfield_for_foreignkey`
  — `django/contrib/admin/options.py:251` (the changed assignment at line 272).
- Changed assignment (pre-patch, line 272):
  `kwargs["empty_label"] = _("None") if db_field.blank else None`
- Post-patch (gold / `patch.diff`):
  `kwargs["empty_label"] = (kwargs.get("empty_label", _("None")) if db_field.blank else None)`
- The assignment is reached only inside the radio branch:
  `elif db_field.name in self.radio_fields:` (line 266), itself guarded by
  `if "widget" not in kwargs:` (line 257).

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip stub)

| Lean (Solution.lean) | Python (real code) | bijection |
|---|---|---|
| `radioBranch : Bool` | `("widget" not in kwargs) and (db_field.name in self.radio_fields)` — the guard conjunction that reaches the changed assignment | `True ↔ true`, `False ↔ false`. Pre-resolved single Bool: whether the changed assignment executes at all. |
| `blank : Bool` | `db_field.blank` (a `bool`) | `True ↔ true`, `False ↔ false`. |
| `provided : Option String` | `kwargs.get("empty_label")` — the caller-supplied placeholder | absent key / `None` ↔ `none`; a string `s` ↔ `some s`. (Django callers pass a non-`None` string; `None` itself is not a meaningful caller-supplied label, so absence is modeled as `none`.) |
| `result : Option String` | the resolved `kwargs["empty_label"]` forwarded into `db_field.formfield(**kwargs)` | `None` ↔ `none`; string `s` ↔ `some s`. |
| `noneLabel : String := "None"` | `_("None")` — the translatable default placeholder, literal `"None"` in the default/test locale | string equality. |

### Callee provenance + flag deps

- `_("None")` (`django.utils.translation.gettext`/`gettext_lazy`): a translation
  lookup. In the default (and test) locale it returns the literal `"None"`. The
  fix's discriminating behavior (caller value vs. default) is independent of the
  default's concrete text, so it is modeled as the constant `noneLabel` rather
  than axiomatized. NOT a consumed axiom — there is no `axiom` the proof uses.
- Flag dependency: the changed assignment is gated on `db_field.blank`
  (`blank = True` for `Inventory.parent` in the F2P test) and on taking the radio
  branch (`db_field.name in self.radio_fields` with the widget not pre-set). Both
  are captured as the `blank` and `radioBranch` inputs; G-CONF fuzzes both
  configurations.

## G-CONF fuzz seed

Pinned seed: **15467** (used by `conformance_check.py`; also `N = 120_000`
fuzzed inputs in addition to the exhaustive `radioBranch × blank × provided∈{none,
"None", "Custom empty label", …}` edge set).
