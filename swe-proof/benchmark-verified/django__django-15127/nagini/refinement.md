# refinement.md — django__django-15127

The operation-by-operation correspondence between `model.py`'s implementation
(the `derive_tags_for_setting` impl region and the deep `merge_slot` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The derivation — model `derive_tags_for_setting` ↔ gold `update_level_tags` (`apps.py`)

Gold hunk (the added receiver + its wiring):
```python
+from django.contrib.messages.storage import base
+from django.contrib.messages.utils import get_level_tags
+from django.test.signals import setting_changed
+
+def update_level_tags(setting, **kwargs):
+    if setting == 'MESSAGE_TAGS':
+        base.LEVEL_TAGS = get_level_tags()
 class MessagesConfig(AppConfig):
     ...
+    def ready(self):
+        setting_changed.connect(update_level_tags)
```
where `get_level_tags()` returns `{**constants.DEFAULT_TAGS,
**getattr(settings,'MESSAGE_TAGS',{})}` (`utils.py:5-12`).

| # | model.py impl op (`derive_tags_for_setting`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `setting: int` | `setting` argument of the receiver (a `str`, compared `== 'MESSAGE_TAGS'`) | R | the setting name is observed only by equality with the message-tags token; `int` token `setting_message_tags()` ↔ the string `'MESSAGE_TAGS'`, any other int ↔ any other setting name (mapping.md §2). |
| A2 | `override: Tags`, `defaults: Tags`, `current: Tags` (three `Optional[int]`-slot records) | `settings.MESSAGE_TAGS` (the new override), `constants.DEFAULT_TAGS`, and the pre-change `base.LEVEL_TAGS` | R | each `Dict[int,str]` is abstracted to the three representative level slots that discriminate the merge (mapping.md §2.1); `None`↔absent, token↔present-with-tag. |
| A3 | `if setting == setting_message_tags():` | `if setting == 'MESSAGE_TAGS':` | I | the same guard: re-derive only when the message-tags setting changed. |
| A4 | `return Tags(merge_slot(defaults.a, override.a), merge_slot(defaults.b, override.b), merge_slot(defaults.c, override.c))` | `base.LEVEL_TAGS = get_level_tags()` i.e. `base.LEVEL_TAGS = {**DEFAULT_TAGS, **MESSAGE_TAGS}` | A-reference | the re-derived mapping is the override merged onto the defaults; the merge is modelled **deeply** by `merge_slot` per level (override-wins-else-default). There is no consumed merge axiom — the deep model is validated **== the real `{**d, **o}`** out-of-band by G-AX (axiom_check.py). Rebinding the module constant `base.LEVEL_TAGS` ↔ returning the fresh record (the model's value-return is the abstraction of the constant rebind; both make the new mapping the one a subsequent read sees). |
| A5 | else branch: `return Tags(current.a, current.b, current.c)` | the receiver returns without touching `base.LEVEL_TAGS` (the constant keeps its current value) | I | a non-message-tags change leaves the mapping unchanged; the model returns a record with the same per-slot values as `current` (observationally the identical mapping — no slot changes), the faithful abstraction of "the constant is left as-is". |
| A6 | (the function is the receiver `update_level_tags`) | `setting_changed.connect(update_level_tags)` in `ready()` | I | the wiring that makes the receiver run on every setting change; control-flow fact, not a data computation. Modeled as: the receiver is invoked with the changed setting and the new override (the spec is over one invocation). |

The level-tag read the F2P observes — `Message.level_tag = LEVEL_TAGS.get(self.level, '')` (`base.py:39-41`) — is the unchanged pure helper `read_slot` (kind I; a present slot reads its token, an absent slot the empty token). The postcondition's `read_slot(Result().c) == read_slot(override.c)` clause is exactly this read applied to the derived mapping at the custom level.

## B. The discriminating behaviour (G-DIFF)

The change makes a setting change to `MESSAGE_TAGS` re-derive `LEVEL_TAGS`. The
single behaviour the F2P `test_override_settings_level_tags` observes: after
`@override_settings(MESSAGE_TAGS={... 12:'custom' ...})`, `base.LEVEL_TAGS`
equals the override (all built-in levels re-tagged plus the custom level `12`),
so a `.get(12, '')` read returns `'custom'` rather than `''`.

`model_prepatch.py` reproduces the pre-patch world: **no receiver reacts**, so
the mapping is never re-derived — the reaction returns the stale `current`
mapping regardless of which setting changed. It therefore **fails** the
re-derivation postcondition (clause (a): `Result().a is override.a` when the
message-tags setting changed; and clause (c): a custom level the override adds
is present in `Result()` with the override tag). That is precisely the spec
sensing the change (G-DIFF). One prepatch suffices: the change is a single
behaviour (re-derive on the message-tags setting), and all three level classes
share the one missing reaction.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — re-deriving the mapping on the message-tags setting change — is
spelled out **deeply** (the `setting == setting_message_tags()` guard plus the
per-level `merge_slot` fold in the impl, an **A-reference** for the merge
primitive it composes), not hidden behind an axiom about the function under
change. There is **no consumed `@ContractOnly` axiom**: the only callee
distance, the dict merge `{**d, **o}`, is an unchanged language primitive
modelled deeply and validated == real Python by G-AX (A-reference, mapping.md
§3.1).

## D. verify(model) ⇒ resolved

`derive_tags_for_setting` verifies only if, under the message-tags identifier,
it returns the override merged onto the defaults, pinned uniformly per slot
(`Result().X is merge_slot(defaults.X, override.X)` for X in a, b, c — A4: this
covers override-wins on a re-tagged built-in level, default-survives on an
omitted one, and a custom override level present with its tag), and otherwise
leaves the mapping unchanged (A5). By
R (setting/tag-token and `Dict`↔`Tags`-record refinements) and by G-AX (the
deep model `merge_slot` == the real `{**d, **o}` merge, the read `read_slot`
== the real `.get(level, '')`), the verified reaction equals
`base.LEVEL_TAGS = get_level_tags()` guarded on `'MESSAGE_TAGS'`. Connected by
`ready()` (A6), this is the gold patch up to type refinement and the audited
merge — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: A-reference soundness (G-AX) and refinement fidelity
(this document, G-EQ).
