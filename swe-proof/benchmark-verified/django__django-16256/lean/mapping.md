# mapping.md — symbol binding & type bijection (django__django-16256)

## Instance
- repo: django/django  base_commit: 76e37513e22f4d9a01c7f15eee36fe44388e6670
- version: 4.2

## Changed symbols (file:line @ base_commit)
The gold patch adds async wrappers to related-manager factories:
- `django/db/models/fields/related_descriptors.py`
  - `create_reverse_many_to_one_manager` → new `acreate` (after L795),
    `aget_or_create`, `aupdate_or_create`.
  - `create_forward_many_to_many_manager` → new `acreate` (after L1199),
    `aget_or_create`, `aupdate_or_create`.
- `django/contrib/contenttypes/fields.py`
  - `create_generic_related_manager` → new `acreate` (after L748),
    `aget_or_create`, `aupdate_or_create`.

Each new `async def a<op>(self, **kwargs)` returns
`await sync_to_async(self.<op>)(**kwargs)`, i.e. delegates to the related
manager's OWN sync `<op>`. Those sync methods (unchanged by the patch) inject
the scope bindings before calling super:
- reverse FK `create`/`get_or_create`/`update_or_create` (L788–810):
  `kwargs[self.field.name] = self.instance`.
- generic `create`/`get_or_create`/`update_or_create` (fields.py L741–763):
  `kwargs[self.content_type_field_name] = self.content_type;
   kwargs[self.object_id_field_name] = self.pk_val`.
- forward M2M `create` etc. (related_descriptors.py L1191+): the through/M2M
  binding via `super(ManyRelatedManager, self.db_manager(db)).create(...)`.

Pre-fix, `a<op>` was the QuerySet method inherited via the manager's dynamic
class (added in commit 58b27e0dbb…), which runs `super().<op>` on the QuerySet
WITHOUT the scope-binding injection.

## Modeled function
`scopedOp` (Solution.lean) abstracts all three ops × directions: the observable
behavior is "merge the scope bindings into the caller kwargs, then run the data
op on the effective map". The data op itself is behavior-identical pre/post-fix.

## Type bijection (used by G-CONF / G-AX)
| Python | Lean |
|---|---|
| kwargs `dict[str, obj]` (insertion-ordered) | `kwargs : List (String × Int)` |
| scope bindings `dict[str, obj]` (distinct keys) | `bindings : List (String × Int)`, keys `Nodup` |
| object/value identity | `Int` |
| `d[k] = v` (assign) | `kwUpsert d k v` (replace-first-else-append) |
| `d.get(k)` / `d[k]` read | `d.lookup k` (first occurrence) |
| effective kwargs handed to data op | `implementation_scopedOp bindings kwargs` |

Distinct-key invariant: Python builds scope bindings from distinct field names
(`field.name` for FK; the two distinct `content_type_field_name` /
`object_id_field_name` for generic), so `(bindings.map Prod.fst).Nodup` holds —
it is the `correct_scopedOp` precondition binder.

## Callee provenance / flag deps
None consumed. The merge is modeled deeply (R); no `opaque` callee, no `_prop`
axiom. The underlying `create/get_or_create/update_or_create` data op is not
modeled (behavior-identical across the fix).

## G-CONF fuzz seed
seed = 16256 (pinned). Fuzzes random kwargs maps and random distinct-key
binding sets; compares `implementation_scopedOp` shadow vs the Python dict-merge
reference over >=1e5 inputs.
