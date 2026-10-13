# refinement.md — django__django-15563

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `parentFilterIds` `do` block plus the deep `stepCol` / `assignedColumns` /
`idColumn` model) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — none here), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are no axioms, so no
A-consumed / A-reference rows and no G-AX. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The column-routing site — `pre_sql_setup` (`compiler.py:1819`)

Gold hunk (essentials):
```
- query.add_fields([query.get_meta().pk.name])
+ meta = query.get_meta()
+ fields = [meta.pk.name]
+ related_ids_index = []
+ for related in self.query.related_updates:
+     if all(path.join_field.primary_key for path in meta.get_path_to_parent(related)):
+         related_ids_index.append((related, 0))
+     else:
+         related_ids_index.append((related, len(fields)))
+         fields.append(related._meta.pk.name)
+ query.add_fields(fields)
  ...
- idents = []
+ idents = []
+ related_ids = collections.defaultdict(list)
  for rows in query.get_compiler(self.using).execute_sql(MULTI):
      idents.extend(r[0] for r in rows)
+     for parent, index in related_ids_index:
+         related_ids[parent].extend(r[index] for r in rows)
  self.query.add_filter("pk__in", idents)
- self.query.related_ids = idents
+ self.query.related_ids = related_ids
```

| # | Solution.lean impl op (`parentFilterIds`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `parents : List Parent` | `self.query.related_updates` (dict iterated in order) | R | each ancestor ↔ one `Parent`, in iteration order (mapping.md §2). G-CONF bridges the list. |
| A2 | param `rows : List (List Int)` | the rows of `execute_sql(MULTI)` | R | one fetched tuple ↔ one `List Int` (mapping.md §2); the unchanged pre-select that produces them is a free input. |
| A3 | `Parent.sharesChildPk` | `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))` | R | identity on `Bool` (mapping.md §2/§3); a free input — the unchanged pk-chain test. |
| A4 | the `while` loop folding `stepCol` over `parents`, threading `(cols, next)` from `([], 1)` | the `for related in related_updates:` loop building `fields` / `related_ids_index` | I | concrete transliteration of the column assignment: a shared-pk ancestor → column 0; otherwise → `len(fields)`, then a column is appended (`next := next+1`). `next` starts at 1 = `len([pk])`. G-CONF transliterates it (SHADOW). |
| A5 | `assignedColumns parents` = the column list `(foldl stepCol …).1` | the completed `related_ids_index` `(related, index)` pairs | I | the per-ancestor fetched-column index. Concrete. |
| A6 | `idColumn rows idx = rows.map (·[idx]!)` | `related_ids[parent].extend(r[index] for r in rows)` | I | the filter id list for one ancestor = column `idx` of every fetched row. Concrete; element order = row order. |
| A7 | result `= (assignedColumns parents).map (idColumn rows)` | `get_related_updates`: `query.add_filter("pk__in", self.related_ids[model])`, one query per ancestor in order (`subqueries.py:137`) | R + I | the per-ancestor `pk__in` value list. `self.related_ids[model]` is a pure dict index (I); the list-of-ancestors order ↔ `related_updates` order (R). mapping.md §1. |

Discriminating content of the change — a **non-shared-pk** ancestor must read a
**distinct fetched column** (its own appended identity), NOT the child identity
column 0 — lives in `stepCol`'s `else` branch (`(cols ++ [next], next + 1)`,
`next ≥ 1`) ⇔ the patched `else: related_ids_index.append((related, len(fields)));
fields.append(...)`. The pre-patch routed **every** ancestor to the child
identity list (`self.query.related_ids = idents`, then
`add_filter("pk__in", self.related_ids)` for each ancestor);
`Solution_prepatch.lean` reproduces that (always column 0) and **fails**
`out = (assignedColumns parents).map (idColumn rows)` on a non-shared-pk
ancestor (G-DIFF) — exactly the bug the two F2P tests
(`test_mti_update_parent_through_child`,
`test_mti_update_grand_parent_through_child`) observe.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — per-ancestor
identity-column routing — is modeled **deeply** (the spelled-out fold `stepCol`/
`assignedColumns` and the column read `idColumn`), not hidden behind an axiom
about the function under change. There are no consumed axioms and no A-reference:
the two facts the routing consumes (`sharesChildPk`, `rows`) are free inputs the
spec holds for universally, so nothing is borrowed from an oracle and there is
nothing for G-AX to check.

## C. verify(Solution) ⇒ resolved

`parentFilterIds` verifies only if its output equals, per ancestor in order, the
column-`idx` projection of the fetched rows where `idx` is 0 for a shared-pk
ancestor and a distinct appended column otherwise (A4-A7). By R (`related_updates`
order ↔ list order, the free `sharesChildPk`/`rows`, the pure `related_ids[model]`
index) the verified routing equals the gold patch's `related_ids` construction
and its consumption in `get_related_updates` on the tested inputs; by G-CONF the
R/I transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵
inputs incl. the two F2P scenarios. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point of plan §1.1 — refinement
fidelity — is discharged by this doc + G-CONF; there is no axiom-soundness trust
point (no axioms).
