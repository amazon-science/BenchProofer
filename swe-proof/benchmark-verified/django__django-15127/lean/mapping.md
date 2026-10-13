# mapping.md — django__django-15127

## Symbol binding (file:line @ base_commit 9a6e2df3a8)
The fix makes the cached level→tag mapping consistent with the configuration
after a settings change. Pre-patch, the mapping is a module constant computed
once at import (`django/contrib/messages/storage/base.py:4`,
`LEVEL_TAGS = utils.get_level_tags()`); when a test changes the override setting
via `@override_settings(MESSAGE_TAGS=...)` the constant is never recomputed, so
`Message.level_tag` (`base.py:39-41`, `LEVEL_TAGS.get(self.level, '')`) returns
stale values.

The gold patch (`django/contrib/messages/apps.py`) adds a `setting_changed`
receiver `update_level_tags(setting, **kwargs)` that, *iff* the changed setting
is the message-tag override, recomputes the cached mapping:

```python
def update_level_tags(setting, **kwargs):
    if setting == 'MESSAGE_TAGS':
        base.LEVEL_TAGS = get_level_tags()
```

and connects it in `MessagesConfig.ready`. `get_level_tags`
(`django/contrib/messages/utils.py:5-12`) returns
`{**constants.DEFAULT_TAGS, **getattr(settings, 'MESSAGE_TAGS', {})}`.

Lean modeled function name: `resolveTagMap` (deliberately neutral — it names the
*behavior* "resolve the cached tag mapping after a configuration change", not the
patched symbol `update_level_tags`; see G-LEAK below).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `resolveTagMap` (modeled receiver behavior) | `update_level_tags(setting, **kwargs)`, gold `apps.py` |
| `tagsSettingChanged` | the guard `setting == 'MESSAGE_TAGS'` (gold `apps.py`) |
| `defaultTags` | `constants.DEFAULT_TAGS`, `constants.py:7-13` (the `{**DEFAULT_TAGS}` half of `get_level_tags`) |
| `overrideTags` | `getattr(settings, 'MESSAGE_TAGS', {})`, the `{**MESSAGE_TAGS}` half of `get_level_tags` (`utils.py:9-12`) |
| `prevTagMap` | `base.LEVEL_TAGS` prior to the receiver firing (`base.py:4`) |
| `mergeTags defaultTags overrideTags` | `{**DEFAULT_TAGS, **MESSAGE_TAGS}` = `get_level_tags()` (`utils.py:9-12`) |
| result | the value assigned to `base.LEVEL_TAGS` after the receiver runs (unchanged if the changed setting is not the override) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `setting == 'MESSAGE_TAGS'` (bool) | `tagsSettingChanged : Bool` |
| `constants.DEFAULT_TAGS` — `dict[int, str]` | `defaultTags : List (Int × String)` |
| `getattr(settings, 'MESSAGE_TAGS', {})` — `dict[int, str]` | `overrideTags : List (Int × String)` |
| previous `base.LEVEL_TAGS` — `dict[int, str]` | `prevTagMap : List (Int × String)` |
| `{**DEFAULT_TAGS, **MESSAGE_TAGS}` — `dict[int, str]` | `mergeTags defaultTags overrideTags = overrideTags ++ defaultTags` |
| resulting `base.LEVEL_TAGS` — `dict[int, str]` | `result : List (Int × String)` |

### Dict vs assoc-list modeling note
A Python `dict[int, str]` is modeled as a `List (Int × String)` of key→value
pairs. The merge `{**DEFAULT_TAGS, **MESSAGE_TAGS}` is *override-wins*: for any
key present in both, the `MESSAGE_TAGS` value is kept. We model the merge as
`overrideTags ++ defaultTags` (overrides first), which under a *first-match*
association lookup (`List.lookup` / `find?`) yields the override value when a key
is overridden and the default value otherwise — exactly the dict-spread
semantics. The key set of the result is the union of both key sets, identical to
the dict-spread key set. G-CONF bridges this by comparing the two legs as the
**dict they denote** (`dict(first-match assoc list) == {**defaults, **overrides}`)
so the assoc-list↔dict bijection is sound and override precedence is tested.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `get_level_tags` is the
  composition of the two dict-spread halves; its two operands (`DEFAULT_TAGS`,
  `getattr(settings,'MESSAGE_TAGS',{})`) enter as the `defaultTags` /
  `overrideTags` DATA, and the spread itself is modeled deeply as
  `overrideTags ++ defaultTags` (an R/I op, not an axiom).
- Flag dependency: the recomputation fires iff the changed setting is the
  message-tag override (`setting == 'MESSAGE_TAGS'`). Any other `setting_changed`
  signal leaves the cached mapping untouched. Modeled as the single Bool
  `tagsSettingChanged`; G-CONF fuzzes both values.

## G-LEAK
The solver-visible `problem_statement` mentions only "message tags",
"@override_settings", "LEVEL_TAGS", and "level_tag". The spec view uses neutral
behavioral vocabulary ("effective mapping", "configuration value that changed",
"message-tag override", "cached mapping"). The modeled-function identifier
`resolveTagMap` shares no patched def/class name (`update_level_tags`,
`MessagesConfig`, `ready`, `get_level_tags`, `setting_changed`, `LEVEL_TAGS`) as a
substring. The mechanism (registering a settings-change receiver that recomputes
a module constant) is NOT narrated in the spec view — only the desired behavior
(the cache stays consistent with the configuration after a change).

## Pinned G-CONF fuzz seed
`15127`.
