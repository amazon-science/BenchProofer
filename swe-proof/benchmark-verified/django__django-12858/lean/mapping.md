# mapping.md — django__django-12858

## Instance
- repo: django/django
- base_commit: f2051eb8a7febdaaa43bd33bf5a6108c5f428e59
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`Model._check_ordering` (django/db/models/base.py:1254, the changed line at
:1747) validates each entry of a model's `Meta.ordering`. For an entry that
spans relations (it contains the relation separator `LOOKUP_SEP`, `"__"`), the
method walks the entry segment-by-segment:

```python
for part in field.split(LOOKUP_SEP):
    try:
        if part == 'pk':
            fld = _cls._meta.pk
        else:
            fld = _cls._meta.get_field(part)
        if fld.is_relation:
            _cls = fld.get_path_info()[-1].to_opts.model
        else:
            _cls = None
    except (FieldDoesNotExist, AttributeError):
        if fld is None or fld.get_transform(part) is None:      # base_commit
            errors.append(checks.Error("'ordering' refers to the nonexistent "
                "field, related field, or lookup '%s'." % field, ..., id='models.E015'))
```

Each segment is resolved against the current model context (`_cls._meta`). A
resolved relation field advances the context to the related model; a resolved
non-relation field exhausts the context (`_cls = None`, so the next
`get_field` raises `AttributeError` because `None._meta` does not exist). When a
segment cannot be resolved (the `get_field` lookup raises `FieldDoesNotExist`,
or the context is exhausted so attribute access raises `AttributeError`), the
`except` branch decides whether to report `models.E015`.

At base_commit the report condition is:

```python
fld is None or fld.get_transform(part) is None
```

i.e. report unless the preceding resolved field `fld` has a registered
**transform** named `part`. The bug: a segment that names a registered
**lookup** (e.g. `isnull`) — which is a legitimate ordering directive (a query
like `order_by('rel__isnull')` works) — has no transform, so
`get_transform(part) is None` is true and E015 is wrongly raised. The gold
patch widens the acceptance to also spare a segment that is a registered lookup:

```python
fld is None or (fld.get_transform(part) is None and fld.get_lookup(part) is None)
```

So a segment is reported only when there is no preceding resolved field, OR the
segment is neither a transform nor a registered lookup of that field.

```python
-    if fld is None or fld.get_transform(part) is None:
+    if fld is None or (
+        fld.get_transform(part) is None and fld.get_lookup(part) is None
+    ):
```

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_orderingFieldCheck` | the E015-report decision for one relation-spanning ordering entry: the loop over `field.split(LOOKUP_SEP)` in `_check_ordering` (django/db/models/base.py:1738-1755), returning whether E015 is appended for that entry |
| `problem_spec_orderingFieldCheck`   | the post-condition this report decision must satisfy |
| `getField : Model → String → Option Field` | resolving one segment to a field of the current context: `pk` alias / `_cls._meta.get_field(part)`, returning `none` when it raises `FieldDoesNotExist` |
| `isRelation : Field → Bool` | `fld.is_relation` |
| `descend : Field → Model` | `fld.get_path_info()[-1].to_opts.model` (the related model the relation leads to) |
| `hasTransform : Field → String → Bool` | `fld.get_transform(part) is not None` |
| `hasLookup : Field → String → Bool`    | `fld.get_lookup(part) is not None` |

The Python context-exhaustion (`_cls = None` for a non-relation field, then a
later `get_field` raising `AttributeError`) is modeled by the `ctx : Option
Model` carrier: a non-relation field sets `ctx := none`, and any subsequent
segment hits the `ctx = none` branch (the analogue of the `AttributeError`),
which still runs the same report decision against the last resolved field.

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `parts : List String` | `field.split(LOOKUP_SEP)` | the entry's segments in order |
| `start : Model` | the originating model `cls` (`_cls` at loop entry) | walk starts here with no field resolved (`fld = none`) |
| `Field` | a Django model field object | only the four observations below are used |
| `result : Bool` | `True` = E015 appended for this entry, `False` = entry accepted | the per-entry contribution to `errors` |

`Model` / `Field` are opaque carriers; only `getField`, `isRelation`, `descend`,
`hasTransform`, `hasLookup` observe them — exactly the model machinery the walk
calls. The walk and report decision are what changed; the machinery did not.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as a proof axiom. The five machinery
  operations are universally-quantified parameters, so the spec/proof hold for
  EVERY machinery and consume no property of any of them. There is no
  `opaque`/`axiom` declaration in `Solution.lean`; `axiom_check.py` is a skip
  stub. The parameters are recorded as A-references solely to document the
  G-CONF binding to the real model machinery.
- No flag dependency: the report decision is unconditional within the `except`
  branch.

## G-CONF fuzz seed
- pinned seed: `12858`
- ≥10^5 fuzzed ordering entries over a synthetic model graph (relation fields
  with registered transforms and lookups, non-relation fields, missing
  segments, `pk` alias, chains that exhaust the context, lookup-only segments
  like `isnull`, transform-only segments, and segments that are neither). Each
  entry's E015-report decision from the REAL patched `_check_ordering` walk is
  compared against the shadow.
