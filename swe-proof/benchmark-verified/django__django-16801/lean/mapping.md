# mapping.md — django__django-16801

## Symbol binding (file:line @ base_commit 3b62d8c83e)
Modeled function: the decision taken in
`ImageField.contribute_to_class(self, cls, name, **kwargs)`,
`django/db/models/fields/files.py:438-445`, of whether to connect the
post-`__init__` handler `update_dimension_fields` to the model `cls` via
`signals.post_init.connect(...)`.

Pre-patch (`files.py:444-445`):
```python
if not cls._meta.abstract:
    signals.post_init.connect(self.update_dimension_fields, sender=cls)
```
Post-patch (gold) widens the guard:
```python
if not cls._meta.abstract and (self.width_field or self.height_field):
    signals.post_init.connect(self.update_dimension_fields, sender=cls)
```

Lean modeled function name: `connectPostInit` (names the *behavior* — "decide
whether to install the post-initialization handler" — at the abstract level).
The Boolean it returns is the truth value of the guard, i.e. whether the
`signals.post_init.connect(...)` call is reached for this `(model, field)`.

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `isAbstract : Bool` | `cls._meta.abstract` (the model `Options.abstract` flag; read at `files.py:444`) |
| `widthField : Option String` | `self.width_field` — the optional width attribute name (`ImageField.__init__`, `files.py:399`, `403`); `None`/`""` ↔ `none`/`some ""` (both falsy) |
| `heightField : Option String` | `self.height_field` — the optional height attribute name (`files.py:400`, `403`) |
| `result : Bool` | whether `signals.post_init.connect(self.update_dimension_fields, sender=cls)` is invoked — i.e. the truth value of the post-patch `if` guard |
| `truthy o` | Python truthiness of the optional name: `bool(self.width_field)` / `bool(self.height_field)` — `None` and `""` are falsy, any non-empty name is truthy |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `cls._meta.abstract : bool` | `isAbstract : Bool` |
| `self.width_field` (`None`, `""`, or a name str) | `widthField : Option String` (`none`, `some ""`, `some s`) |
| `self.height_field` (`None`, `""`, or a name str) | `heightField : Option String` |
| `bool(self.width_field)` | `truthy widthField` |
| `bool(self.height_field)` | `truthy heightField` |
| `not cls._meta.abstract and (self.width_field or self.height_field)` (as a truth value) | `!isAbstract && (truthy widthField \|\| truthy heightField)` |
| the guard is True → `connect(...)` runs | `result = true` |
| the guard is False → no connect | `result = false` |

### Truthiness bijection
A Django field's `width_field`/`height_field` default to `None`
(`ImageField.__init__`, `files.py:399-403`) and otherwise hold an attribute-name
string. The guard uses them in boolean position (`self.width_field or
self.height_field`), so the only distinction it observes is truthy vs falsy:
`None` and `""` are falsy, any non-empty string is truthy. `truthy : Option
String → Bool` models exactly this guard truthiness (`none ↦ false`, `some s ↦
¬s.isEmpty`).

Scope note: the model is faithful to the *guard's* truthiness, not to the full
constructor invariant. In practice `width_field` is `None` or a non-empty name,
so `some ""` is not a value Django produces; the model admits it (mapping it to
the same falsy outcome as `none`, matching `bool("") == False`) purely to make
`truthy` total. This widens the domain harmlessly — both falsy cases drive the
guard identically — and is exercised explicitly by G-CONF (`""` is in the
conformance name set), confirming the `some ""` ↦ falsy mapping matches Python.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The decision reads only
  `cls._meta.abstract`, `self.width_field`, `self.height_field` — plain attribute
  reads of already-computed data, modeled as the three inputs — and combines them
  with `not`/`and`/`or` plus the implicit truthiness test, all modeled directly
  (`Bool` connectives, `truthy`). No `opaque`/`axiom` callee contract is required
  ⇒ `axioms = []`, `deep_model_references = []`, `axiom_check.py` is a skip stub
  (G-AX skips). The handler `update_dimension_fields` and
  `signals.post_init.connect` are NOT modeled: the F2P test observes only whether
  the connection happens (the guard's truth value), which is precisely `result`.
- No flag dependency: the guard fires purely on the abstract flag and the two
  field-name truthiness tests.

### Second hunk (out of scope of the modeled decision, NOT separately modeled)
The gold patch has a second hunk in `update_dimension_fields` (`files.py:461-464`)
that deletes the now-redundant early-return guard
`has_dimension_fields = self.width_field or self.height_field; if not
has_dimension_fields or ...: return`. This is dead-code cleanup justified by the
new connection invariant: once hunk 1 stops connecting the handler for
dimension-less fields, the `not has_dimension_fields` disjunct can no longer
fire on the `post_init` path (the handler is never registered there).

Scope claim (deliberately narrow — NOT a global behavior-preservation claim):
the second hunk is **not needed to explain the FAIL_TO_PASS regression**
(`test_post_init_not_connected`), which observes only whether the handler is
connected — i.e. exactly the connection decision modeled by `connectPostInit`.

- On the `post_init` path the two hunks are coupled: post-patch, a dimension-less
  field never connects the handler, so `update_dimension_fields` is never invoked
  from `post_init`, and the deleted guard is unreachable there.
- The ONLY remaining caller of `update_dimension_fields` is
  `ImageFileDescriptor.__set__` with `force=True`. There, removing the guard does
  change the executed path for a dimension-less field: control now proceeds past
  `dimension_fields_filled = not(False or False) = True` (the `not force` return
  is skipped) and reaches the `getattr`/`file.width`/`file.height` reads before
  the trailing `if self.width_field:`/`if self.height_field:` `setattr` guards —
  both falsy, so no attribute is written. So **no instance field is mutated**, but
  the path is not provably side-effect-free (it may read the file). We do NOT
  claim strict behavior-preservation of this `force=True` path; it is simply
  outside the modeled connection decision and is irrelevant to the F2P test.

Because the modeled, F2P-observable fixed behavior is the connection decision
alone, the second hunk is not separately modeled and needs no
`Solution_prepatch_2.lean`. The full gold behavior (both hunks) is carried
faithfully by `patch.diff` (gold verbatim), which is what G-RESOLVE / G-GOLD
exercise against the real harness.

## G-LEAK
The solver-visible `problem_statement` publicly names `ImageField`,
`post_init`, the "post_init signal handler", `width_field`, and `height_field`.
The spec view uses none of the patched identifiers
(`contribute_to_class`, `update_dimension_fields`, `signals.post_init.connect`,
`cls._meta.abstract`); it describes the abstract behavior — "install the
post-initialization handler exactly when the model is concrete and the field
names a width or height attribute". No gold-diff line is reproduced, no diff
marker, no patched file path, and no bug→fix mechanism is narrated.

## Pinned G-CONF fuzz seed
`16801`.
