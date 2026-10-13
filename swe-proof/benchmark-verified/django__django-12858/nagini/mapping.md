# mapping.md — django__django-12858

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f2051eb8a7febdaaa43bd33bf5a6108c5f428e59`, states the type
abstraction, and gives the provenance of the two registry-query callees the
modeled decision consults.

Repo file under change: `django/db/models/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_reported_paths(reached_field, is_value_op, is_compare_op)` | the related-field loop of `Model._check_ordering(cls)` — `django/db/models/base.py:1735-1758` (the `for field in related_fields:` loop and its inner `except (FieldDoesNotExist, AttributeError):` reporting decision at line 1749-1758) | the modeled changed function (the per-path "report invalid ordering reference?" decision and the list of reports it accumulates) |
| `flag_path(reached_field, is_value_op, is_compare_op)` | the boolean reporting predicate inside the `except` handler — `base.py:1750` post-patch: `fld is None or (fld.get_transform(part) is None and fld.get_lookup(part) is None)` | pure spec: the per-path decision (1 = a `checks.Error(... id='models.E015')` is appended for this path, 0 = accepted) |
| input `reached_field[k]` (0/1) | `fld is not None` for path `k` at the point its trailing segment failed `get_field` (`fld` is the last field resolved on the path; `None` if none was, e.g. the first segment failed) — `base.py:1737,1744,1750` | whether a concrete field was reached just before the unresolved trailing segment |
| input `is_value_op[k]` (0/1) | `fld.get_transform(part) is not None` for path `k` — `base.py:1750` | whether the trailing segment is a registered value-producing operator (a `Transform`) on the reached field |
| input `is_compare_op[k]` (0/1) | `fld.get_lookup(part) is not None` for path `k` — `base.py:1750` (the clause ADDED by the gold patch) | whether the trailing segment is a registered comparison operator (a `Lookup`) on the reached field |
| `Result()[k]` (0/1) | whether `errors.append(checks.Error(..., id='models.E015'))` ran for path `k` — `base.py:1751-1758` | per-path report flag, in input order |

Pre-patch repo predicate the change widens (for the refinement audit, not
referenced from the consumer spec view): `base.py:1750` pre-patch reads
`if fld is None or fld.get_transform(part) is None:` — i.e. it ignores
`get_lookup`, so a trailing segment that is ONLY a comparison operator
(`get_transform` is None, `get_lookup` is not None) is wrongly reported.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the ordered collection of related-field paths examined in the `except` handler (each a dotted `str` like `'test__isnull'`) | three index-aligned `List[int]` of 0/1, one entry per examined path | path `k` ↔ index `k`; the three per-path booleans of path `k` ↔ `reached_field[k]`, `is_value_op[k]`, `is_compare_op[k]` |
| `fld is not None` (an object/`None` test on the last resolved field) | `reached_field[k] != 0` | truthy ↔ 1, `None`/falsy ↔ 0 |
| `fld.get_transform(part) is not None` (a `Transform` subclass or `None`) | `is_value_op[k] != 0` | non-None ↔ 1, None ↔ 0 |
| `fld.get_lookup(part) is not None` (a `Lookup` subclass or `None`) | `is_compare_op[k] != 0` | non-None ↔ 1, None ↔ 0 |
| `errors` accumulating `checks.Error(id='models.E015')` objects | `Result()` as a `List[int]` of 0/1 report flags | the modeled behaviour observes only WHICH paths are reported; the F2P test asserts `Model.check() == []` (no `models.E015`), i.e. flag 0 for its single lookup path |

The handler in the real code only ever appends the SAME `models.E015` error
(differing solely by the path string interpolated into the message), one per
offending path; the observable content the F2P test depends on is the
presence/absence of that error per path, captured by the 0/1 flag. `str`
indexing is banned in Nagini, and the path strings never enter the decision
beyond the three booleans above, so the carrier is `List[int]`.

## 3. Callee provenance (the two registry queries — A-references, checked by G-AX / axiom_check.py)

The reporting decision is modelled DEEPLY (`flag_path` / the verified loop) over
the two booleans the real predicate consults; there is **no consumed
`@ContractOnly` axiom**. The two registry queries that produce those booleans
are unchanged callees, validated against their real semantics out-of-band.

### 3.1 `is_value_op` ↔ `Field.get_transform(part)` (A-reference)
**Callee:** `RegisterLookupMixin.get_transform(self, lookup_name)` —
`django/db/models/query_utils.py:188-195` (inherited by `Field`). Source @ base_commit:

```python
def get_transform(self, lookup_name):
    from django.db.models.lookups import Transform
    found = self._get_lookup(lookup_name)
    if found is None and hasattr(self, 'output_field'):
        return self.output_field.get_transform(lookup_name)
    if found is not None and not issubclass(found, Transform):
        return None
    return found
```

Returns a non-`None` `Transform` subclass iff `lookup_name` is a registered
transform reachable from the field (directly or via its `output_field`), else
`None`. The model encodes only the boolean "is it non-None?" (`is_value_op`).

### 3.2 `is_compare_op` ↔ `Field.get_lookup(part)` (A-reference, the clause the patch adds)
**Callee:** `RegisterLookupMixin.get_lookup(self, lookup_name)` —
`django/db/models/query_utils.py:179-186` (inherited by `Field`). Source @ base_commit:

```python
def get_lookup(self, lookup_name):
    from django.db.models.lookups import Lookup
    found = self._get_lookup(lookup_name)
    if found is None and hasattr(self, 'output_field'):
        return self.output_field.get_lookup(lookup_name)
    if found is not None and not issubclass(found, Lookup):
        return None
    return found
```

Returns a non-`None` `Lookup` subclass iff `lookup_name` is a registered lookup
reachable from the field, else `None`. `isnull` (the F2P case) is a built-in
`Lookup` registered on `CharField` (via `Field.class_lookups`), so
`get_lookup('isnull')` is non-None while `get_transform('isnull')` is None —
the exact configuration that the pre-patch predicate mis-reports and the patch
accepts. The model encodes only the boolean "is it non-None?" (`is_compare_op`).

**Soundness check (G-AX):** `axiom_check.py` constructs real Django `Field`
instances (and registers test lookups/transforms), invokes the real
`get_transform` / `get_lookup`, and asserts (a) each returns non-None exactly
for the registered operator kind, and (b) the deep model `flag_path` equals the
real post-patch predicate `fld is None or (get_transform is None and
get_lookup is None)` over the full truth table of (`reached_field`,
`is_value_op`, `is_compare_op`). Exit 0 iff sound. It imports only Django
(the repo under test) — nothing extraneous — and runs in-container.
