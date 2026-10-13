# mapping.md — django__django-15127

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9a6e2df3a8f01ea761529bec48e5a8dc0ea9575b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `django/contrib/messages/apps.py` (the gold patch ADDS
the change-notification receiver `update_level_tags` and wires it up in
`MessagesConfig.ready`). The receiver reads two unchanged callees and mutates a
module-level cached table.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `refreshCachedTable` (the modeled `method`) | `update_level_tags(setting, **kwargs)` — `django/contrib/messages/apps.py` (ADDED by the gold patch, lines 7-9) | the modeled changed function: the `setting_changed` receiver |
| `cached : List (Int × String)` *(mut)* | the module global `base.LEVEL_TAGS` — `django/contrib/messages/storage/base.py:4` (read at `base.py:41` by `Message.level_tag`) | the cached level→tag lookup table the receiver keeps in sync |
| `changedKey : String` | the `setting` argument of the receiver (the name of the setting that just changed) | which configuration key changed |
| `watchedKey : String` | the literal `'MESSAGE_TAGS'` the receiver guards on (`apps.py` added line 8) | the one configuration key this receiver reacts to |
| `base : List (Int × String)` | `constants.DEFAULT_TAGS` — `django/contrib/messages/constants.py:7` | the default level→tag entries |
| `overrides : List (Int × String)` | `getattr(settings, 'MESSAGE_TAGS', {})` (the project's `MESSAGE_TAGS` setting) | the override level→tag entries |
| `recomputeTable base overrides` *(deep model — A-reference)* | `get_level_tags()` — `django/contrib/messages/utils.py:5` (body lines 9-12: `{**DEFAULT_TAGS, **getattr(settings,'MESSAGE_TAGS',{})}`) | pure spec: the recomputed table; deep model of the unchanged callee `get_level_tags`, validated `recomputeTable == get_level_tags()` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `lookupEntry` | (helper) the dict-membership test `k in overrides` used to express the overlay; no standalone repo symbol | pure helper for the overlay semantics |

The second gold hunk — `MessagesConfig.ready` calling
`setting_changed.connect(update_level_tags)` — is pure registration plumbing
(it connects the receiver to Django's `setting_changed` signal so the receiver
fires under `@override_settings`). It has no observable computation of its own:
its only effect is that `update_level_tags` runs on each setting change, which
is exactly the behavior the modeled `method` specifies. It is therefore an
A-reference to the unchanged signal-dispatch machinery (`Signal.connect` /
`Signal.send`), validated operationally by the F2P test under G-RESOLVE (the
receiver must actually be invoked). It introduces no consumed axiom and no
separate modeled function. See refinement.md §B.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `dict[int, str]` (`LEVEL_TAGS`, `DEFAULT_TAGS`, `MESSAGE_TAGS`, and `get_level_tags()`'s return) | `List (Int × String)` | a Python dict `d` ↔ a `List (Int × String)` whose pairs are `d.items()` with **unique keys**; equality is **as a key→value mapping** (order-insensitive, since real dicts have unique keys). `recomputeTable` lists `overrides` first so that, read as "first binding wins", overrides shadow base — exactly Python `{**base, **overrides}`. |
| a level value (Python `int` dict key, e.g. `10,20,25,30,40,12`) | `Int` | identity on the integer value |
| a tag string (Python `str` dict value) | `String` | identity on the character content |
| the `setting` name (Python `str`) | `String` | identity on the character content; `changedKey = watchedKey` ↔ `setting == 'MESSAGE_TAGS'` |

`**kwargs` of the real receiver (`signal`, `sender`, `enter`, …) are ignored by
the body and carry no observable content; they are not modeled.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `recomputeTable` deep model ↔ `get_level_tags()` (A-reference)
**Callee:** `django.contrib.messages.utils.get_level_tags`
(`utils.py:5`, unchanged by the patch). Body at `base_commit`:

```python
def get_level_tags():
    return {
        **constants.DEFAULT_TAGS,            # base
        **getattr(settings, 'MESSAGE_TAGS', {}),  # overrides
    }
```

It is a dict-merge: the default tags overlaid by the project's `MESSAGE_TAGS`,
**overrides winning** on shared keys (later `**` spread wins in Python). The
recompute is modeled **deeply** by `recomputeTable` (with `lookupEntry`) in the
`pure` region — `overrides ++ base.filter (key not overridden)` — which as a
key→value mapping is exactly `{**base, **overrides}`. There is **no consumed
axiom** about it; G-AX validates the deep model against the real callee.

**Soundness check (G-AX):** `axiom_check.py` configures Django, sets
`settings.MESSAGE_TAGS` to boundary + fuzzed dicts (empty; each single default
key remapped; all five default keys remapped — the F2P shape; extra
non-default keys like `12`; value-collision and empty-string values), calls the
**real** `get_level_tags()`, and asserts `dict(recomputeTable(DEFAULT_TAGS,
MESSAGE_TAGS)) == get_level_tags()` as a mapping. ≥10⁵ fuzzed configurations.
Imports only `django.*` already present in the instance image. Exit 0 iff sound.

### 3.2 Signal registration ↔ `setting_changed.connect` (A-reference, plumbing)
**Callee:** `django.test.signals.setting_changed` (a `django.dispatch.Signal`)
and `MessagesConfig.ready` calling `.connect(...)`. Unchanged dispatch
machinery. Not modeled as a separate computation (it has none); its sole
observable effect — that `update_level_tags` runs on each setting change — is
the premise of the modeled `method` and is exercised end-to-end by the F2P test
under G-RESOLVE. No consumed axiom. (refinement.md §B.)

## 4. G-CONF / G-AX fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` and `axiom_check.py` seed their `random.Random` with
**`15127`** so the consumer-side verdict (§11.3) is reproducible. The R/I shadow
`conformance_check.py` builds transliterates the conditional control flow + the
frame (I-tagged ops) to Python and leaves the recompute as the **real**
`get_level_tags()` callee (A-reference → run real callee, not the deep model);
the deep model itself is validated separately by `axiom_check.py` (G-AX).
