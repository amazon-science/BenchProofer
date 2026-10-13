# mapping.md — django__django-16801

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3b62d8c83e3e48d2ed61cfa32a61c56d9e030293`, states the type
abstraction, and gives the provenance of the one A-reference (the deep model of
the registration decision validated against the real Django callee by G-AX).

Repo file under change: `django/db/models/fields/files.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `attach_post_init_hook(receivers, owner_id, is_abstract, width_target, height_target)` | `ImageField.contribute_to_class(self, cls, name, **kwargs)` — `django/db/models/fields/files.py:438` (the registration block, body lines 443-445) | the modeled changed function: decides whether to register the per-instance recalculation hook with the owning class's `post_init` notification list |
| `should_register(is_abstract, width_target, height_target)` *(deep model — A-reference)* | the registration guard `not cls._meta.abstract and (self.width_field or self.height_field)` — `files.py:444` (post-patch) | pure spec: the registration decision; the deep model of the real guard, validated `should_register == real registration` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `configured(name)` | the truthiness test inside `self.width_field or self.height_field` — `files.py:444` | pure spec: a companion target is configured iff present and non-empty |
| `receivers` (mutated `List[int]`) | `signals.post_init.receivers` — the notification list `signals.post_init.connect(self.update_dimension_fields, sender=cls)` appends to (`files.py:445`); inspected by the F2P test as `signals.post_init.receivers` | the notification list; registering appends the owning class's identity token |
| `owner_id` | `id(cls)` — the owning model class's identity (the `sender` of `post_init.connect`) | the owning-class identity token the F2P test probes for membership |
| `is_abstract` | `cls._meta.abstract` (`files.py:444`) | whether the owning class is an abstract base |
| `width_target` / `height_target` | `self.width_field` / `self.height_field` — the companion size-field names set in `ImageField.__init__` (`files.py:403`) | the two optional companion-target names |

The second gold hunk (`update_dimension_fields`, `files.py:447-464`) removes the
now-redundant `has_dimension_fields` early-return guard; it is a
behaviour-preserving cleanup *enabled by* hunk 1 and carries no behaviour the
F2P/P2P tests independently observe — see refinement.md §B. It is not modeled as
a separate contracted function (it has no independently-observable fixed
behaviour, hence no separate failing `model_prepatch`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.width_field` / `self.height_field` — a field-name `str` or `None` | `Optional[List[int]]` (a name as code points, or `None`) | a configured target ↔ a non-None, non-empty `List[int]`; an unconfigured target ↔ `None` (or empty). Only truthiness is observed: `bool(name)` ↔ `configured(name) == name is not None and len(name) > 0`. Real Django field names are always non-empty strings, so `bool(self.width_field)` ↔ `width_target is not None and len(width_target) > 0`. |
| `cls._meta.abstract` — a `bool` | `bool` (`is_abstract`) | identical. |
| `id(cls)` — the sender identity | `int` (`owner_id`) | identical: an opaque identity token; the F2P test compares it by membership. |
| `signals.post_init.receivers` — the global receiver list (entries keyed by `(receiver_id, sender_id)`) | `List[int]` of sender identity tokens (`receivers`) | the F2P test reduces each entry to its `sender_id` and tests membership of `id(PersonModel)`; the model carries exactly that projection — the list of registered owner-identity tokens. Registering one handler appends one `owner_id`. |
| `signals.post_init.connect(self.update_dimension_fields, sender=cls)` (`files.py:445`) | `receivers.append(owner_id)` | the registration side effect ↔ appending the owner's token; the F2P test observes only that the sender token is present/absent. |

`str` indexing/iteration is banned in Nagini, so the companion-target names are
carried as `Optional[List[int]]`; only their truthiness (presence + non-empty)
is observed by the modeled decision.

## 3. The A-reference (checked by G-AX / axiom_check.py)

### 3.1 `should_register` deep model ↔ the real `ImageField.contribute_to_class` registration decision (A-reference)
**Callee / behaviour:** the registration guard in
`ImageField.contribute_to_class` after the patch:

```python
def contribute_to_class(self, cls, name, **kwargs):
    super().contribute_to_class(cls, name, **kwargs)
    # Only run post-initialization dimension update on non-abstract models
    # with width_field/height_field.
    if not cls._meta.abstract and (self.width_field or self.height_field):
        signals.post_init.connect(self.update_dimension_fields, sender=cls)
```

The registration decision is the pure boolean
`not cls._meta.abstract and (self.width_field or self.height_field)`. Python
truthiness of `self.width_field or self.height_field` is `True` iff at least one
of the two field names is a non-empty string (a configured companion target);
both `None` (and both empty) give `False`. Hence the decision is exactly

  `register ⟺ (not abstract) and (width configured or height configured)`,

which is what `should_register` / `configured` encode. There is **no
`@ContractOnly` axiom the proof consumes** — the decision is modeled deeply as a
pure predicate over the abstract flag and the two optional target names.

**Soundness check (G-AX):** `axiom_check.py` (a) confirms, with stdlib only,
that the model's `configured` / `should_register` reference agrees with Python
truthiness of the real `width_field or height_field` guard over all
target-name shapes (absent / empty / genuine field names) × {concrete,
abstract}; and (b) builds REAL Django model classes whose `ImageField` carries
every {none, width, height, both} companion-target configuration (concrete and
abstract), attaches each field via the real
`ImageField.contribute_to_class` during class creation, and asserts the
field's recalculation handler is present in the class's `post_init.receivers`
**iff** `should_register` says so — including the exact F2P scenario (a concrete
model with no companion target ⇒ handler absent). It imports only `django` +
`PIL` (the very modules the patched code lives in / requires); nothing
benchmark-specific. Exit 0 iff sound. (Outside the container, where Pillow is
absent, it confirms the truthiness A-reference and SKIPs the model-building
half; the orchestrator runs it in-container.)
