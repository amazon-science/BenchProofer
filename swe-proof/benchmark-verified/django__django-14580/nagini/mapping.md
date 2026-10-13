# mapping.md — django__django-14580

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 36fa071d6ebd18a61c4d7f1b5c9d17106134bd44`, states the type
abstraction, and gives the provenance of the one A-reference deep model
(validated by axiom_check.py / G-AX).

Repo file under change: `django/db/migrations/serializer.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serialize_type(value_tag)` | `TypeSerializer.serialize(self)` — `django/db/migrations/serializer.py:273-287` (the `special_cases` scan, lines 274-281) | the modeled changed function: render a distinguished type into a (text, import-directive-set) pair |
| `Serialized` (`.text`, `.imports`) | the `(string, set(imports))` pair `TypeSerializer.serialize` returns (`serializer.py:281`) | the serializer's output: rendered text + the set of import directives that text requires |
| `base_ref_tag()` / `base_ref_text()` / `base_ref_directive()` | the first `special_cases` row `(models.Model, "models.Model", ['from django.db import models'])` (`serializer.py:276`, post-patch) | the base-class reference distinguished row: its type identity, its rendered text, and the single import directive its dotted reference requires |
| `other_ref_tag()` / `other_ref_text()` / `other_ref_directive_empty()` | the second `special_cases` row `(type(None), 'type(None)', [])` (`serializer.py:277`) | the no-import distinguished row: its type identity, its rendered text, and its empty directive list (rendering refers to no external namespace) |

The reference value the F2P test serializes is `models.Model`
(`tests/migrations/test_writer.py:661`, `test_serialize_type_model`); it reaches
`TypeSerializer` via `serializer_factory(value)` → `isinstance(value, type)`
(`serializer.py:345-346`) and `MigrationWriter.serialize`
(`django/db/migrations/writer.py:270-271`), which is just
`serializer_factory(value).serialize()`. These dispatch wrappers are unchanged
and outside the modeled scope.

The pre-patch repo state the change fixes (for the refinement audit, not
referenced from the consumer spec view): the first `special_cases` row was
`(models.Model, "models.Model", [])` (`serializer.py:276`, **empty** import
list) — so `set(imports)` for that row was the empty set and the surfaced
directive set omitted `from django.db import models`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the type object being serialized (`self.value`, a Python `type`) | integer identity tag (`value_tag`) | each distinguished type is an opaque identity; the `case is self.value` reference-identity test (`serializer.py:280`) ↔ the `tags[i] == value_tag` integer-equality test. Only WHICH distinguished row matches is observable; the type's internals are irrelevant to this change. |
| `str` (the rendered text `string`, and the import-directive strings) | `List[int]` of Unicode code points; specification over `PSeq[int]` via `ToSeq` | `s[k]` ↔ code point `ord(s[k])`; `len(s)` ↔ list length; `str` concatenation ↔ list `+`. `str` indexing is banned in Nagini, so text/directives are code-point lists. |
| `set(imports)` — a set of directive **strings** (`serializer.py:281`) | `List[int]` of the single directive's code points (empty list = empty set) | the directive set has at most one element here (each `special_cases` row carries 0 or 1 directives); the modeled `imports` carries that one directive's code points, or is empty. The set-membership semantics (`d ∈ set(imports)`) ↔ "the modeled `imports` equals that directive's code points". The set-materialisation is the **A-reference** validated by axiom_check.py / G-AX (§3). |
| the `special_cases` **list literal** of `(case, string, imports)` triples (`serializer.py:275-278`) | three index-aligned `List`/`PSeq` columns (`tags`, `texts`, `directives`) constructed inside `serialize_type`, exactly as the source constructs the literal | row `k` ↔ triple `k`; the `for case, string, imports in special_cases:` first-match scan (`serializer.py:279-281`) ↔ the modeled `while i < len(tags): if tags[i] == value_tag:` first-match loop. The table is built INSIDE the function (as in the source), so the fix — the row's directive content — lives in the impl, exactly where the gold patch edits it. |

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

### 3.1 the deep (text, directive-set) model ↔ the real `TypeSerializer.serialize` + `set(imports)`
**Callee / behaviour modeled deeply:** the post-patch `TypeSerializer.serialize`
distinguished-row scan and its `return string, set(imports)`
(`django/db/migrations/serializer.py:274-281`). There is **no `@ContractOnly`
axiom** the proof consumes; the table scan and the `set(imports)`
materialisation are spelled out in the impl region. The deep model is validated
**== the real callee** out-of-band by axiom_check.py (G-AX). Source (post-patch):

```python
class TypeSerializer(BaseSerializer):
    def serialize(self):
        special_cases = [
            (models.Model, "models.Model", ['from django.db import models']),
            (type(None), 'type(None)', []),
        ]
        for case, string, imports in special_cases:
            if case is self.value:
                return string, set(imports)
        ...
```

The behaviour the F2P test (`test_serialize_type_model`) observes, and the deep
model encodes:

  * serializing `models.Model` returns `("models.Model", {'from django.db import models'})`
    — text `base_ref_text()`, directive set `{base_ref_directive()}`;
  * serializing `type(None)` returns `("type(None)", set())` — text
    `other_ref_text()`, empty directive set.

The single behavioural change is row 0's directive content: `[]` → `['from
django.db import models']`, i.e. the directive set surfaced for `models.Model`
goes from empty to `{'from django.db import models'}`. With the empty list, a
generated migration whose `bases=(..., models.Model)` references the rendered
`models.Model` would raise `NameError: name 'models' is not defined`, because no
`from django.db import models` import is emitted; the directive makes the
rendered reference resolve. `set(imports)` materialises the row's directive list
into that directive set (deterministically; the list has 0 or 1 element, so set
order/dedup are non-issues).

**Soundness check (G-AX):** `axiom_check.py` runs the REAL Django
`MigrationWriter.serialize` (= `TypeSerializer.serialize`) on `models.Model` and
`type(None)` and asserts the deep model's (text, import-set) pair matches the
real callee exactly; it also `exec`s the surfaced imports and `eval`s the
rendered text to confirm the reference resolves to `models.Model` (the
end-to-end consequence the issue reports). Independently of Django it confirms
`set(imports)` has the modeled directive-set-materialisation semantics over
5000 randomized directive lists. Exit 0 iff sound. It imports only Django (the
package under test) and the standard library — nothing else repo-specific.
