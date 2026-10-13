# mapping.md — django__django-12325

## Symbol binding (file:line @ base_commit 29c126bb34)
Modeled function: the construction of the **parent-link mapping** built while a
model class is assembled, `django/db/models/base.py:194-207` (`ModelBase.__new__`,
the `# Collect the parent links for multi-table inheritance.` block):

```python
parent_links = {}
for base in reversed([new_class] + parents):
    if not hasattr(base, '_meta'):
        continue
    if base != new_class and not base._meta.abstract:
        continue
    # Locate OneToOneField instances.
    for field in base._meta.local_fields:
        if isinstance(field, OneToOneField):            # gold adds: and field.remote_field.parent_link
            related = resolve_relation(new_class, field.remote_field.model)
            parent_links[make_model_tuple(related)] = field
```

The mapping keys a *related-model identity* to the field that links to it; it is
later consumed to promote the linking field to the primary key for multi-table
inheritance. The mapping is a Python `dict`, so the assignment is
**last-write-wins** per key.

Lean modeled function name: `collectParentLinks` (neutral — names the *behavior*
"collect the parent-link mapping", not the patched method `__new__` / `_prepare`).

### The second hunk (`options.py`)
The gold also deletes a now-unreachable guard in `Options._prepare`
(`django/db/models/options.py:254-257`):
```python
if not field.remote_field.parent_link:
    raise ImproperlyConfigured('Add parent_link=True to %s.' % field)
```
This `raise` fired only when a *non-parent-link* OneToOneField had wrongly been
recorded into `parent_links` and then promoted to the pk by `_prepare`. Once
`__new__` records **only** designated parent-link fields, the promoted field
always has `parent_link=True`, so the guard can never trip — it is dead code.
The behavior change is therefore **fully localized to the `__new__` mapping**;
the `options.py` edit removes code that the corrected mapping makes unreachable.
It is NOT an independently-observable fixed behavior, so a single triple +
single prepatch covers G-DIFF.

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `collectParentLinks` (modeled mapping build) | `ModelBase.__new__` parent-link block, `base.py:194-207` |
| `fields : List Field` | the in-iteration-order concatenation of `base._meta.local_fields` over the bases the outer `for base in reversed([new_class] + parents)` loop visits (i.e. `new_class` + abstract bases) |
| `Field.isOneToOne` | `isinstance(field, OneToOneField)`, `base.py:205` |
| `Field.parentLink` | `field.remote_field.parent_link`, the OneToOne's parent-link designation (gold's added conjunct) |
| `Field.relatedKey` | `make_model_tuple(resolve_relation(new_class, field.remote_field.model))`, `base.py:206-207` — the related-model identity used as the dict key |
| `Field.name` | `field.name` — a stable per-field identity (disambiguates fields with equal `relatedKey`); carries no semantics, only identity |
| result | the final `parent_links` dict, modeled as `List (String × Field)` (assoc list, last-write-wins per key) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `isinstance(field, OneToOneField)` → bool | `Field.isOneToOne : Bool` |
| `field.remote_field.parent_link` → bool | `Field.parentLink : Bool` |
| `make_model_tuple(resolve_relation(...))` → a hashable model-key | `Field.relatedKey : String` |
| `field` identity | `Field.name : String` |
| ordered `base._meta.local_fields` across visited bases | `fields : List Field` (iteration order preserved) |
| `parent_links : dict[key, field]` (last-write-wins) | `result : List (String × Field)` via `dictInsert` (replace prior entry for key, then append) |

### dict ↔ assoc-list modeling note
A Python `dict` assignment `parent_links[k] = field` keeps the LAST field written
for key `k`. We model the dict as an assoc list and the assignment as `dictInsert
d k v = d.filter (·.1 ≠ k) ++ [(k, v)]` (drop any prior entry for `k`, append the
new one at the end). This reproduces last-write-wins exactly, and gives a single
canonical list for each dict state (no duplicate keys, insertion-stable for keys
that are never rewritten). G-CONF compares the two legs as **key→field maps**
(dict equality), so the list↔dict bijection is exact. The key-collision /
overwrite behavior is the crux of the fix and is modeled directly.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `isinstance`,
  `resolve_relation`, `make_model_tuple`, and `field.remote_field.parent_link`
  enter as **DATA**: their observable output per visited field is supplied as the
  `Field` record (`isOneToOne`, `parentLink`, `relatedKey`, `name`). The mapping
  build itself (the guarded last-write-wins insertion) is modeled deeply as a
  `foldl`/`for` over `dictInsert` (R/I ops, not axioms).
- Flag dependency: a field is recorded iff it is a OneToOneField AND it is
  designated a parent link — i.e. `isOneToOne ∧ parentLink`. The outer-loop base
  selection (`new_class` + abstract bases only) is folded into which fields appear
  in `fields`; it is unchanged by the patch.

## G-LEAK
The solver-visible `problem_statement` already contains `OneToOneField`,
`parent_link`, `models.Model`, and discusses multi-table-inheritance pk setup, so
the behavioral vocabulary used in the spec view (parent-link designation, the
related-model key, last-write-wins) is public. The patched method names `__new__`
and `_prepare` do NOT appear in any spec-view identifier or comment
(`collectParentLinks`, `parentLinkMapping`, `dictInsert`, `Field`, `relatedKey`
embed neither `prepare` nor `new` as a token). No patched file path / diff line
is reproduced.

## Pinned G-CONF fuzz seed
`12325`.
