# refinement.md — django__django-15127

Maps every operation in `implementation_resolveTagMap` to its `patch.diff`
counterpart — the `update_level_tags` receiver added to
`django/contrib/messages/apps.py` (and the cache it maintains in
`django/contrib/messages/storage/base.py`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled changed op
validated == real callee, **I** identical concrete op.

## Patch (the receiver maintaining the cache)
```python
def update_level_tags(setting, **kwargs):
    if setting == 'MESSAGE_TAGS':
        base.LEVEL_TAGS = get_level_tags()      # {**DEFAULT_TAGS, **MESSAGE_TAGS}
```
connected via `setting_changed.connect(update_level_tags)` in
`MessagesConfig.ready`. The modeled value is the resulting cached mapping
(`base.LEVEL_TAGS`) after a configuration change.

## Operation correspondence
| # | Lean op (`implementation_resolveTagMap`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut tagMap := prevTagMap` | the cache `base.LEVEL_TAGS` keeps its current value unless the receiver assigns it | I | the accumulator starts at the previously-cached mapping; if the guard does not fire nothing is reassigned. |
| 2 | `if tagsSettingChanged then` | `if setting == 'MESSAGE_TAGS':` | R | `setting == 'MESSAGE_TAGS'` (bool) ↔ `tagsSettingChanged : Bool`. Type bijection in mapping.md. |
| 3 | `tagMap := mergeTags defaultTags overrideTags` | `base.LEVEL_TAGS = get_level_tags()` = `{**DEFAULT_TAGS, **MESSAGE_TAGS}` | R | `get_level_tags()` dict-spread ↔ `mergeTags d o = o ++ d` under first-match assoc lookup (override-wins). `DEFAULT_TAGS` ↔ `defaultTags`, `getattr(settings,'MESSAGE_TAGS',{})` ↔ `overrideTags`. The spread is modeled DEEPLY (`++`), not axiomatized; G-CONF compares as dicts. |
| 4 | `return tagMap` | the value `base.LEVEL_TAGS` now holds | I | return the resolved cached mapping. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — `DEFAULT_TAGS` and `MESSAGE_TAGS` enter as data, the
dict-spread is modeled deeply). Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the cached mapping is a module constant computed once at import
(`base.LEVEL_TAGS = utils.get_level_tags()`) and NEVER recomputed when the
override setting changes — there is no receiver. The prepatch impl
(`implementation_resolveTagMap := return prevTagMap`, unconditionally) is exactly
this: it leaves the cache at its stale value regardless of the change. It
therefore cannot satisfy `problem_spec_resolveTagMap` on the discriminating
clause (`tagsSettingChanged = true → result = mergeTags defaultTags overrideTags`)
whenever `mergeTags defaultTags overrideTags ≠ prevTagMap` — precisely the case
the FAIL_TO_PASS test `test_override_settings_level_tags` exercises (under
`@override_settings(MESSAGE_TAGS={...})` the cache must equal the merged map, not
the stale import-time map). The carried gold proof fails to typecheck against the
buggy impl (G-DIFF — confirmed: `simp` makes no progress on the `= true` arm).
