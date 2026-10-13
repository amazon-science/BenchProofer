# refinement.md — django__django-15554

Maps every operation in `implementation_addJoin` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op). Every step is R, A, or I.

## Modeled slice: the alias-allocation of `Query.setup_joins` + `Query.join`

Post-patch repo code (`patch.diff`, `query.py`):

```python
# setup_joins:
reuse = can_reuse if join.m2m or reuse_with_filtered_relation else None
alias = self.join(
    connection, reuse=reuse, reuse_with_filtered_relation=reuse_with_filtered_relation,
)

# join:
if reuse_with_filtered_relation and reuse:
    reuse_aliases = [a for a, j in self.alias_map.items() if a in reuse and j.equals(join)]
else:
    reuse_aliases = [a for a, j in self.alias_map.items()
                     if (reuse is None or a in reuse) and j == join]
if reuse_aliases:
    if join.table_alias in reuse_aliases:
        reuse_alias = join.table_alias
    else:
        reuse_alias = reuse_aliases[-1]
    self.ref_alias(reuse_alias)
    return reuse_alias
alias, _ = self.table_alias(join.table_name, create=True, filtered_relation=join.filtered_relation)
... self.alias_map[alias] = join
return alias
```

Lean impl (`implementation_addJoin`):

```lean
let reuse := if isM2M || reuseWithFilteredRelation then some canReuse else none
let mut cands := []
for p in registry do
  let permitted := match reuse with | none => true | some s => s.contains p.1
  if permitted && keysEqual p.2 newJoin then cands := cands ++ [p.1]
if cands.isEmpty then return (freshAlias, registryStore registry freshAlias newJoin)
return (cands.getLastD freshAlias, registry)
```

| # | Lean op | patch.diff op | tag | notes |
|---|---|---|---|---|
| 1 | `reuse := if isM2M ‖ reuseWithFilteredRelation then some canReuse else none` | `reuse = can_reuse if join.m2m or reuse_with_filtered_relation else None` | I | the changed `setup_joins` reuse-set line, transliterated. `some/none` ↔ a set/`None`. |
| 2 | `for p in registry do … if permitted && keysEqual p.2 newJoin` | the `reuse_aliases` list comprehension over `self.alias_map.items()` | R | `registry : List (Alias × JoinKey)` ↔ ordered `alias_map`. On the modeled path (`reuseWithFilteredRelation = true`, so `reuse = some canReuse`), the patched `join` takes the `reuse_with_filtered_relation and reuse` branch: `a in reuse and j.equals(join)`. `keysEqual` ↔ `Join.equals` (base parts; filter ignored). |
| 3 | `permitted := match reuse with none => true ‖ some s => s.contains p.1` | `a in reuse` (with `reuse` always a set on this path) | R | membership in the permitted set. `none` (all permitted) is unreachable on the modeled path but kept for faithfulness to the general `join`. |
| 4 | `if cands.isEmpty then (freshAlias, registryStore registry freshAlias newJoin)` | `table_alias(create=True)` + `self.alias_map[alias] = join; return alias` | R | alias allocation + registry STORE. `freshAlias` ↔ the alias string from `table_alias`. The store is a DICT assignment, not an append, and `table_alias(create=True)` does NOT guarantee the alias is absent: its `filtered_relation` branch (`query.py:812-814`) performs no uniqueness check, and its `'%s%d' % (alias_prefix, len(alias_map)+1)` branch (`query.py:808`) collides with a user annotation alias of that shape. So `registryStore` has both legs — replace in place under an alias already held (discarding the join it held on entry, key order and `len(alias_map)` unchanged), add a last entry otherwise — and both are differential-tested against the real `Query.join` by G-CONF. |
| 5 | `else if cands.contains newJoinAlias then (newJoinAlias, registry)` | `if join.table_alias in reuse_aliases: reuse_alias = join.table_alias` | R | prefer the join's own alias when it is itself eligible. `newJoinAlias` ↔ `join.table_alias` (for a filtered relation this is `filtered_relation.alias`, so it can coincide with a registered alias). Registry unchanged. |
| 6 | `else (cands.getLastD freshAlias, registry)` | `reuse_alias = reuse_aliases[-1]; self.ref_alias(...); return reuse_alias` | R | otherwise reuse the most-recent eligible alias; registry unchanged. |

No row is A-consumed or A-reference: the reuse decision and registry update are
modeled deeply over the data; `Join.equals` is modeled directly as `keysEqual`,
not axiomatized. The unchanged callees (`table_alias`, `ref_alias`) contribute
no property the spec consumes — `freshAlias` is supplied as data, and
`ref_alias`/refcounts are not observable in the modeled value (the SQL JOIN
structure / alias_map shape). So `axiom_check.py` is a skip stub and the impl is
all R/I (G-CONF differential-tests it).

## Prepatch (the bug)

`Solution_prepatch.lean` sets `reuse := if isM2M then some canReuse else none`
(the base_commit `reuse = can_reuse if join.m2m else None`). On the modeled
filtered-relation path `isM2M = false`, so `reuse = none` (all aliases
permitted), and the first relation's base-compatible alias is reused — one JOIN.
This fails `problem_spec_addJoin` exactly on the discriminating input
(`registry` containing a base-compatible alias NOT in `canReuse`).
