# mapping.md — django__django-15127

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9a6e2df3a8f01ea761529bec48e5a8dc0ea9575b`, states the type
abstraction, and gives the provenance of the modelled callee.

Repo file under change: `django/contrib/messages/apps.py`. The behaviour the
change makes observable lives across `django/contrib/messages/utils.py`,
`django/contrib/messages/storage/base.py`, and
`django/contrib/messages/constants.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `derive_tags_for_setting(setting, override, defaults, current)` *(mechanism-neutral model name)* | `update_level_tags(setting, **kwargs)` — added in `django/contrib/messages/apps.py` (the `setting_changed` receiver) | the modeled changed function: the per-setting derivation of the level-tags mapping |
| (the re-derivation result) | `base.LEVEL_TAGS = get_level_tags()` — `django/contrib/messages/storage/base.py:4` (the module constant the receiver rebinds), via `get_level_tags()` — `django/contrib/messages/utils.py:5` | the derived level-tags mapping being recomputed |
| `merge_slot(d, o)` *(deep model — A-reference)* | the dict merge `{**constants.DEFAULT_TAGS, **getattr(settings,'MESSAGE_TAGS',{})}` inside `get_level_tags()` — `django/contrib/messages/utils.py:9-12` | pure spec: the per-level override-wins merge, validated `== {**d, **o}` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `read_slot(slot)` | `Message.level_tag` property `LEVEL_TAGS.get(self.level, '')` — `django/contrib/messages/storage/base.py:39-41` | pure spec: the unchanged per-level read (`.get(level, '')`) |
| `setting_message_tags()` | the string `'MESSAGE_TAGS'` the receiver guards on — `apps.py` post-patch (`if setting == 'MESSAGE_TAGS'`) | pure spec: the setting-name token that triggers re-derivation |
| `defaults` (input) | `constants.DEFAULT_TAGS` — `django/contrib/messages/constants.py:7-13` | the built-in per-level default tags |
| `override` (input) | `settings.MESSAGE_TAGS` (the new value the signal carries) | the user-configurable override mapping |
| `current` (input) | the pre-change value of `base.LEVEL_TAGS` | the mapping in force before the change |
| `empty_tag()` | the empty string `''` default of `LEVEL_TAGS.get(self.level, '')` | pure spec: the read of an absent level |

The connection itself — `MessagesConfig.ready()` calling
`setting_changed.connect(update_level_tags)` (`apps.py` post-patch) — is the
wiring that makes the receiver run; the modeled function is the receiver's
*computation* (which mapping results from a given setting change). The wiring
is a kind-I control-flow fact stated in refinement.md, not a data computation.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Dict[int, str]` level→tag mapping (`LEVEL_TAGS`, `DEFAULT_TAGS`, `MESSAGE_TAGS`) | a `Tags` record with three `Optional[int]` slots `a`, `b`, `c` | each slot is one representative level; `None` ↔ level absent from the dict; a non-`None` token ↔ the level present with that tag. The three levels are chosen to discriminate every merge case (mapping.md §2.1). |
| a tag value `str` (e.g. `'info'`, `'custom'`, `''`) | an `int` tag token (`0` = the empty tag, others = distinct non-empty tags) | only equality/identity and presence of tag values are observed (the F2P asserts dict equality and a `.get` read), so a tag is an opaque token; string content is irrelevant to the tested behaviour. |
| the dict `.get(level, '')` read | `read_slot` | a present slot reads its token; an absent slot (`None`) reads `empty_tag()` (`0` ↔ `''`). |
| the setting name `str` `'MESSAGE_TAGS'` vs any other setting | `int` token `setting_message_tags()` (==1) vs any other int | only the equality `setting == 'MESSAGE_TAGS'` is observed. |

### 2.1 Why three representative levels are faithful and sufficient

The real `LEVEL_TAGS` has five built-in levels plus any custom levels the
override adds. The merge `{**DEFAULT_TAGS, **MESSAGE_TAGS}` is *pointwise* over
levels: each level is independently (i) overridden, (ii) defaulted, or (iii)
introduced by the override. The three slots instantiate exactly these three
classes:

* `a` — a built-in level the override **re-tags** (override wins over default);
* `b` — a built-in level the override **omits** (the default value survives);
* `c` — a **custom** level the defaults never had (present only via the
  override, so the read must be the override tag, NOT the empty token).

Class (iii) is the discriminating case the F2P test exercises (a custom level
`12: 'custom'`): pre-patch it reads the empty string because `LEVEL_TAGS` is
never re-derived; post-patch it reads `'custom'`. Pinning all three classes
pointwise means no wrong reaction (stale, partial-merge, default-wins) can
satisfy the spec — the merge is determined on every level class.

## 3. Callee provenance (deep model — checked by G-AX / axiom_check.py)

### 3.1 `merge_slot` deep model ↔ Python dict merge (A-reference)

**Callee:** the Python mapping merge `{**defaults, **override}` as used by
`get_level_tags()`:

```python
def get_level_tags():
    return {
        **constants.DEFAULT_TAGS,
        **getattr(settings, 'MESSAGE_TAGS', {}),
    }
```
(`django/contrib/messages/utils.py:5-12`). The merge is an **unchanged**
language primitive the reaction composes; it is modelled **deeply** by the
`@Pure` `merge_slot` (the override-wins-else-default choice per level), so there
is **no consumed `@ContractOnly` merge axiom**. The deep model is validated
**== the real Python merge** out-of-band by `axiom_check.py` (G-AX): for each
level, `{**d, **o}.get(level)` equals `merge_slot(d.get(level), o.get(level))`
under the `None`↔absent encoding (override value wins where present, else the
default value, else absent). Docs: the dict-merge semantics
(https://docs.python.org/3/reference/expressions.html#dictionary-displays — a
later key overrides an earlier one).

This is the only callee distance in the bundle; the rest of the reaction (the
`setting == 'MESSAGE_TAGS'` guard, rebinding the module constant) is identical
concrete control flow (refinement.md, kind I).

### 3.2 No consumed axioms

There is **no `@ContractOnly` axiom** in this bundle. The merge is a deep model
(A-reference, §3.1); the level-tag read and the setting guard are spelled out
concretely. `axiom_check.py` validates the A-reference deep model against the
real Python merge and the real `.get(level, '')` read on boundary + fuzz
inputs.
