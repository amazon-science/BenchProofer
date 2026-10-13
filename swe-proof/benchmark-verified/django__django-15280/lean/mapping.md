# mapping.md — symbol binding & type bijection (django__django-15280)

## Modeled function
- **Lean** `implementation_assignParents : (Int → Int) → List Child → List Child`
- **Python** `RelatedManager.get_prefetch_queryset` —
  `django/db/models/fields/related_descriptors.py:633-652 @ 973fa56`
  (the reverse-relation assignment loop, lines 648-650 pre-patch / 648-651
  post-patch).

The function under spec is the manual reverse-relation management loop inside
`get_prefetch_queryset`. The patch guards the per-child assignment with
`if not self.field.is_cached(rel_obj):` so that a child object which already has
its parent set (e.g. by an inner nested prefetch) is no longer overwritten by the
outer object. Everything else in `get_prefetch_queryset` (hints, db routing, the
`filter`, the returned tuple) is unchanged and outside the modeled behavior.

## Type bijection (used by G-CONF)
| Python | Lean | notes |
|---|---|---|
| `queryset` (batch of child rows, ordered) | `List Child` | order- and length-preserving iteration |
| a child `rel_obj` | `Child {key : Int, parent : Option Int}` | only the touched aspects: the related-value key, and the (possibly already-set) parent slot |
| `rel_obj_attr(rel_obj)` (the local related value) | `c.key : Int` | the value used to key into `instances_dict` |
| `instances_dict` (maps related value → parent instance) | `lookup : Int → Int` | total function from key to default parent id; G-CONF builds a finite random table |
| `instances_dict[rel_obj_attr(rel_obj)]` | `lookup c.key` | dict subscript |
| `self.field.is_cached(rel_obj)` | `c.parent.isSome` | `FieldCacheMixin.is_cached` = "cache name present in `instance._state.fields_cache`"; modeled as "the parent slot is populated" |
| `not self.field.is_cached(rel_obj)` | `c.parent.isNone` | the new guard |
| `setattr(rel_obj, self.field.name, instance)` | `{ c with parent := some (lookup c.key) }` | populate the parent slot; other fields framed unchanged |
| parent instance identity | `Int` | a parent is identified by an integer id; equality of parents ↔ equality of ids |

A `Child` carrying `parent = some v` models a row whose reverse relation is
ALREADY cached (the inner-prefetch case from the issue); `parent = none` models a
row with no value yet (the ordinary case). The bug is that the pre-patch loop
overwrites `some v` with the outer object; the fix keeps `some v`.

## Callee provenance
- `FieldCacheMixin.is_cached` (`django/db/models/fields/mixins.py:21`) — an
  UNCHANGED callee, but NOT axiomatized: its result (membership of the cache key)
  is modeled directly by the `Option` parent slot's `isSome`/`isNone`. So it is an
  R-tagged structural model, not a consumed axiom and not an A-reference.
- `instances_dict[...]`, `rel_obj_attr`, `setattr` — likewise modeled directly
  (total lookup function, projection, record update). No UNCHANGED callee is
  consumed as an axiom; the axioms region is empty.

## Flag dependency
None. The new guard applies on every iteration regardless of relation kind
(the issue notes it manifests for both OneToOneField and ForeignKey reverse
relations); no configuration flag selects the behavior.

## G-CONF fuzz seed
Pinned seed: **15280**. ≥10^5 fuzzed batches over a small key space (forcing
table collisions) with ~40% of children pre-populated with a cached parent (so
the discriminating cached-branch clause is hit hard), plus deterministic boundary
batches (empty, single cached, single uncached, same-key mixed).
