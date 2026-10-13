# mapping.md — symbol binding & type bijection (django__django-16938)

## Modeled function
- **Lean** `implementation_m2mPkQuery : QuerySet → QuerySet`
- **Python** the `queryset_iterator(obj, field)` closure inside
  `Serializer.handle_m2m_field`, in the non-natural-key branch:
  - `django/core/serializers/python.py:81-82 @ 1136aa5005`
  - `django/core/serializers/xml_serializer.py:157-158 @ 1136aa5005`

  Both sites are byte-identical pre-patch
  (`return getattr(obj, field.name).only("pk").iterator()`) and receive the same
  byte-identical edit, so they realize ONE abstract behavior; one triple models
  both (see "Multi-site" below).

The modeled function is the construction of the related-object query that the
serializer iterates to emit an m2m field's related primary keys. Starting from
the related manager's base queryset `getattr(obj, field.name)` (which a custom
manager may have configured with `select_related(<field>)`), the builder applies
`.only("pk")` (load only the primary key), and `.iterator()` (streaming
evaluation, behavior-irrelevant to the bug). The gold patch inserts a no-argument
`.select_related()` BEFORE `.only("pk")`.

## Why the bug happens (mechanism, kept out of the spec view)
`getattr(obj, field.name)` returns the related manager's queryset, which a custom
manager's `get_queryset` may have built with `select_related("master")`. That
call sets the query's `select_related` state to a RESTRICTED dict
(`isinstance(query.select_related, dict)` → `restricted=True`, `requested =
{"master": {}}`). The serializer then chains `.only("pk")`, which defers every
field except `pk` (so the FK `master` is deferred). At SQL-compile time,
`django/db/models/sql/compiler.py:get_related_selections` calls
`select_related_descend(field, restricted=True, requested, select_mask)`
(`django/db/models/query_utils.py:select_related_descend`), which for a field
that is `in requested` but NOT in `select_mask` raises
`FieldError("Field <Model>.<field> cannot be both deferred and traversed using
select_related at the same time.")`.

A no-argument `select_related()` sets `query.select_related = True` (the
unrestricted boolean — `QuerySet.select_related`, `django/db/models/query.py`),
which DISCARDS the field-specific dict. With `select_related` no longer a dict,
`restricted=False`, so the deferred-vs-traversed branch of
`select_related_descend` cannot fire. `.only("pk")` still loads only the primary
key, so query-count / load-minimization behavior is preserved (the F2P
`test_serialize_only_pk` checks the emitted SQL does not load the FK column).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| the related manager's queryset for the m2m field | `QuerySet` | projected onto only the components the builder/evaluation inspect |
| identity of the iterated related set (`getattr(obj, field.name)`, the through-relation) | `QuerySet.relation : String` | never altered by the builder chain; the frame anchor |
| `query.select_related` state | `QuerySet.selectRel : SelectRel` | non-dict (`False` OR `True`)→`unrestricted`; `dict {f: {}}`→`fields [f, …]` (the requested-field keys). The False/True distinction is behaviorally unobservable on the modeled slice (`restricted = isinstance(select_related, dict)` is False for both), so the projection collapses it — this also keeps the spec from encoding WHICH clearing call the gold patch used (see refinement.md "Leakage note"). |
| `query.deferred_loading` immediate mask (set by `.only(...)`) | `QuerySet.immediate : Option (List String)` | `none` = no `.only()` applied; `some mask` = only `mask` loaded immediately |
| `.select_related()` (no args) | `selectRel := SelectRel.unrestricted` | sets `query.select_related = True` (non-dict), discarding any restricted dict; projects to `unrestricted` |
| `.only("pk")` | `immediate := some ["pk"]` | immediate-load only the primary key |
| `.iterator()` | (not modeled) | streaming wrapper; no effect on the FieldError condition or the load mask |
| `select_related_descend` raises FieldError | `raisesFieldError q = true` | restricted traversal of a field absent from the immediate mask |

`SelectRel` enumerates the two OBSERVABLY distinct `query.select_related`
shapes (the three reachable Python values collapse to two behaviors).
The `restricted` boolean of `select_related_descend` is `isinstance(select_related,
dict)`, i.e. `selectRel` is a `fields _` — matched in `raisesFieldError`.

## Callee provenance
- `select_related_descend` (`query_utils.py`) is the UNCHANGED callee whose error
  condition the fix avoids. The patch does NOT change it; it changes the query
  state handed to query compilation by inserting `select_related()`. Its rejection
  condition is modeled DEEPLY as `raisesFieldError` (a total predicate over the
  projected query: restricted traversal of a field missing from the immediate
  mask), so it is an **A-reference** validated by G-CONF, NOT a consumed axiom.
- `QuerySet.select_related` / `QuerySet.only` (`query.py`) are the UNCHANGED query
  builders; their effect on `query.select_related` / `deferred_loading` is the
  R-leg modeled as the two record updates. Behavior-irrelevant chaining
  (`_chain`, `.iterator()`) is not modeled.
- The axioms region of Solution.lean is empty; `axiom_check.py` is a skip stub.

## Multi-site (one behavior, two call sites)
The python and xml serializers carry the IDENTICAL pre-patch line and the
IDENTICAL gold edit. There is no independently-observable difference between them
at the modeled level (both build `getattr(obj, field.name).only("pk")` and both
gain a leading `select_related()`), so they are a single modeled behavior with one
triple and one `Solution_prepatch.lean`. `patch.diff` carries BOTH hunks (gold
verbatim) so every F2P serializer variant (json/jsonl/yaml/xml) resolves.

## Flag dependency
The discriminator is the inherited `selectRel`: the bug is observable only when
the related manager supplied restricted traversal (`fields [..]`) of a field that
`.only("pk")` then defers. The fuzzer MUST include inputs whose `selectRel` is
`fields [f, …]` with `f` outside the `pk` mask (the F2P custom-manager scenario),
alongside `unrestricted` and field sets that intersect the mask.

## G-CONF fuzz seed
Pinned seed: **16938**. ≥10^5 fuzzed `QuerySet` inputs over random relation
names, both `selectRel` shapes (with field sets that do and do not overlap
the immediate mask), and varied pre-existing immediate masks.
