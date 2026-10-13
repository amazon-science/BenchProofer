# mapping.md — django__django-15554

## Symbol binding (file:line @ base_commit 59ab3fd0e9e606d7f0f7ca26609c06ee679ece97)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_addJoin` / `problem_spec_addJoin` | the composed alias-allocation slice: the reuse-set decision in `Query.setup_joins` **plus** `Query.join` | `django/db/models/sql/query.py` — `setup_joins` reuse line `:1843` (`reuse = can_reuse if join.m2m else None`), `join` body `:1014-1054` |
| `registry : List (Alias × JoinKey)` | `self.alias_map` (ordered dict alias → join object), restricted to the touched fields | `query.py` `alias_map` |
| `JoinKey.base` (`Nat`) | the base part of a join's `identity` that `Join.equals` compares — `(__class__, table_name, parent_alias, join_field)` — encoded injectively into `Nat` (equality only) | `datastructures.py:147-166` (`identity` / `equals`) |
| `JoinKey.filt` (`Option Nat`) | the `filtered_relation` component of `Join.identity` (the last identity element), ignored by `equals` but significant for `__eq__` | `datastructures.py:153` (`self.filtered_relation`), `:156-159` (`__eq__`), `:164-166` (`equals`) |
| `keysEqual` | `Join.equals(other)` — compares `identity[:-1]` (base only, filter ignored) | `datastructures.py:164-166` |
| `canReuse : List Alias` | the `reuse` set passed to `join` (the filtered relation's `set(self.path)` reaching `setup_joins`'s `can_reuse`) | `query_utils.py:339`, `query.py:1843-1850` |
| `freshAlias : Alias` | the new alias produced by `self.table_alias(..., create=True)` when no reuse is possible | `query.py:1041-1043` |
| `newJoinAlias : Alias` | `join.table_alias` — the alias the freshly-built `connection` already carries; for a filtered relation this is `filtered_relation.alias`, set on the `connection` in `setup_joins` (`table_alias = filtered_relation.alias`), so it can coincide with a registered alias and trigger the `join.table_alias in reuse_aliases` preference | `query.py:1801-1802`, `1035-1037` |
| `isM2M : Bool` | `join.m2m` | `query.py:1843` |
| `reuseWithFilteredRelation : Bool` | the new `reuse_with_filtered_relation` parameter threaded into `setup_joins`/`join` | `query.py` (gold patch) |
| `chooseAlias`/`matchCandidates` (pure helpers) | `join`'s `reuse_aliases` computation + reuse-vs-create branch | `query.py:1027-1054` |

## What the modeled slice does (base_commit vs gold)

`setup_joins` builds a `connection` Join and asks `self.join` for its alias:

```python
# setup_joins, base_commit:
reuse = can_reuse if join.m2m else None
alias = self.join(connection, reuse=reuse)
```

`Query.join` then computes the reusable aliases and either reuses one or creates
a new alias + registers the join:

```python
# join, base_commit:
reuse_aliases = [
    a for a, j in self.alias_map.items()
    if (reuse is None or a in reuse) and j.equals(join)
]
if reuse_aliases:
    ... return a reused alias ...
# else: create a fresh alias, self.alias_map[alias] = join, return alias
```

### The bug (base_commit)

When a query annotates **two** `FilteredRelation`s on the *same* base relation
(e.g. `book` with two different conditions), each filtered relation is resolved
via `FilteredRelation.as_sql` → `build_filtered_relation_q(condition,
reuse=set(self.path))` → `build_filter` → `setup_joins`. The join is not m2m, so
`reuse = can_reuse if join.m2m else None` yields `reuse = None` — "every alias is
reusable". In `join`, `reuse is None` makes the candidate filter degenerate to
`j.equals(join)`, and `equals` **ignores `filtered_relation`**. So the second
filtered relation's join is judged equal to the first's already-registered join
and its alias is reused — collapsing two distinct filtered joins into ONE SQL
JOIN, which is the reported bug (`test_multiple`).

### The fix (gold)

A `reuse_with_filtered_relation` flag is threaded
`build_filtered_relation_q(=True)` → `build_filter` → `setup_joins` → `join`.
Two coordinated effects:

1. `setup_joins`: `reuse = can_reuse if join.m2m or reuse_with_filtered_relation
   else None`. On the filtered-relation path `reuse` becomes the explicitly
   supplied `can_reuse` set (the relation's own path), never `None`.
2. `join`: when `reuse_with_filtered_relation and reuse`, candidates are
   `a in reuse and j.equals(join)` (confined to the permitted set). The else
   branch additionally switches the general comparison to `j == join`
   (filter-sensitive), but on the modeled filtered-relation path the
   `reuse_with_filtered_relation and reuse` branch is taken.

Because the first relation's alias is reachable only along its own path, it is
NOT in the second relation's `can_reuse` set, so reuse is refused and a fresh
alias is allocated → two distinct JOINs, each with its own filter.

### Lean modeling

- The slice is modeled as one function `implementation_addJoin` over the data:
  `registry` (the ordered alias_map), the new join's `JoinKey`, the `freshAlias`
  to allocate, the `canReuse` set, `isM2M`, and `reuseWithFilteredRelation`.
- `keysEqual` models `Join.equals` (base parts only; filter ignored), so two
  joins on the same base relation with different `filt` tags ARE `keysEqual`.
- The permitted-reuse set is `some canReuse` when `isM2M || reuseWithFilteredRelation`,
  else `none` (= all aliases). `matchCandidates` filters registry by
  permitted-AND-`keysEqual`. `chooseAlias` reuses the join's own alias
  `newJoinAlias` when it is itself eligible (the `join.table_alias in
  reuse_aliases` preference), else the last candidate (registry unchanged), or
  allocates `freshAlias` and STORES the new join under it via `registryStore`.
- `registryStore` models `self.alias_map[alias] = join` (`query.py:1061`), which is
  a DICT store, not an append. `table_alias(create=True)` does not guarantee the
  alias is absent from `alias_map`: its `filtered_relation` branch
  (`query.py:812-814`) performs no uniqueness check at all, and its
  `'%s%d' % (self.alias_prefix, len(self.alias_map) + 1)` branch
  (`query.py:808`) collides with any user annotation alias of that shape (`T2`,
  `T3`, …). Both were reproduced against the real `table_alias`. So the store has
  two reachable legs: under an alias already present it REPLACES that entry in
  place (discarding the join that alias held on entry, order of keys unchanged,
  `len(alias_map)` unchanged), and under an absent alias it adds a last entry.
- The spec/theorem is UNCONDITIONAL: it quantifies over both values of
  `reuseWithFilteredRelation`/`restrictedTraversal` with no precondition, so both
  the filtered-relation route (the one the F2P test `test_multiple` exercises) and
  the ordinary route are constrained. The patch changes the candidate computation
  on each (the filtered-relation route gains the confinement to `reuse`; the
  ordinary route's comparison moves from `j.equals(join)` to `j == join`), so both
  are modeled.

The discriminator (why two JOINs not one): with the first relation's alias absent
from the second's `canReuse`, `matchCandidates` is empty → fresh alias allocated.
The prepatch impl (`reuse = some canReuse only if isM2M`) yields `reuse = none` on
this non-m2m path, so the first alias (base-compatible) is reused — one JOIN.

## G-CONF fuzz seed

Pinned seed: **15554** (also in conformance_check.py).
