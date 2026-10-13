# mapping.md — django__django-12304

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 4c1b401e8250f9f520b3c7dc369554477ce8b15a`, states the type
abstraction (the Lean↔Python bijection used by G-CONF), and records the pinned
fuzz seed.

Repo file under change: `django/db/models/enums.py`.
Changed method: `ChoicesMeta.__new__(metacls, classname, bases, classdict)`
(`django/db/models/enums.py:11`). The added line is `enums.py:34`
(post-patch): `cls.do_not_call_in_templates = True`, sitting between the
`cls.label = property(...)` assignment (`enums.py:33`) and the
`return enum.unique(cls)` (`enums.py:35` post-patch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `publishChoicesClass (built : ChoicesClass)` | the tail of `ChoicesMeta.__new__` — `enums.py:29–34`, i.e. from after the value→label map is assembled (`cls._value2label_map_ = …`, line 29) through the final published class | the modeled changed behavior: publish the constructed choices class, now carrying the `do_not_call_in_templates` flag, with the rest of the construction preserved |
| `ChoicesClass.doNotCallInTemplates : Bool` | the `do_not_call_in_templates` class attribute (set to `True` by the new line `enums.py:34`; absent/falsey by default) | the boolean class flag the template engine reads |
| `ChoicesClass.valueToLabel : List (Int × List Char)` | `cls._value2label_map_` — the `dict(zip(cls._value2member_map_, labels))` built at `enums.py:29`; the value→label association underlying `member.label` (`enums.py:33`) | the rest of the constructed state, which the publish step must preserve |
| `out : ChoicesClass` | the value returned by `__new__` (after `enum.unique(cls)`, which is identity on attributes) | the published class: `out.doNotCallInTemplates = true` and `out.valueToLabel = built.valueToLabel` |

No callee is consumed as a contract. The publish step's effect is modeled
directly (set one boolean field; copy the rest), so there is no axiom and no
A-reference — see §3.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| the constructed choices class object | `ChoicesClass` structure (touched/observed fields only) | the class object ↔ the record of its `do_not_call_in_templates` flag and its value→label map; other class machinery is irrelevant to the fix and elided |
| `cls.do_not_call_in_templates` (a class attribute holding `True`, or absent) | `doNotCallInTemplates : Bool` | `getattr(cls, 'do_not_call_in_templates', False)` (exactly how `template/base.py` reads it) ↔ the `Bool`. Real `True` ↔ `true`; attribute absent or falsey ↔ `false`. |
| `cls._value2label_map_ : dict[value -> label]` | `valueToLabel : List (Int × List Char)` | the value→label association as an ordered association list; an integer-valued enum member's value ↔ `Int`, its label string ↔ `List Char`. The fix does not touch this map; the carrier only needs it to state the preservation (frame) clause. |
| `cls.do_not_call_in_templates = True` assignment | `{ built with doNotCallInTemplates := true }` | setting the one flag and leaving everything else untouched ↔ a record update of the single field. |

The downstream consumer is `Variable._resolve_lookup` in
`django/template/base.py` (UNCHANGED by this patch): when a resolved value is
`callable`, it does `if getattr(current, 'do_not_call_in_templates', False):
pass` — i.e. it skips auto-calling the class iff the flag is truthy. That is the
behavior the flag controls; it is not modeled (out of scope of the change) but
documented here to justify the `doNotCallInTemplates = true` postcondition.

## 3. Callee provenance

None. The patch adds a single literal assignment (`cls.do_not_call_in_templates
= True`) inside the function under spec. There is no outside callee whose
behavior is assumed, so the bundle declares **no axioms** and **no A-reference**
deep models (cf. the thin-fix precedent django__django-10914). The frame clause
`out.valueToLabel = built.valueToLabel` records that the new assignment does not
disturb the previously-built `_value2label_map_` (directive 5/8): a wrong impl
that set the flag but clobbered the map would fail the F2P `.label`/`.value`
read.

## 4. G-CONF fuzz

Seed **12304**, `N_FUZZ = 100_000`, stdlib-only, no Django/DB/Docker. The
oracle reproduces the patched assignment's observable effect directly in Python
(`obj.do_not_call_in_templates = True` on a fresh carrier object whose other
state is left untouched) and reads it back exactly as `template/base.py` does
(`getattr(obj, 'do_not_call_in_templates', False)`); the shadow is the
transliterated `do` block (`{ built with doNotCallInTemplates := true }`). Both
must agree that the flag is `True` and the value→label map is unchanged, over
fuzzed value→label maps of varying length plus the empty/singleton boundaries.
Exit 0 iff zero disagreements.
