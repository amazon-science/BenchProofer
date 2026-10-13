# mapping.md — django__django-12965

## Instance
- repo: django/django
- base_commit: 437196da9a386bd4cc62b0ce3f2de4aba468613d
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The function under spec decides, while compiling a deletion, whether the deletion
targets exactly **one** table (in which case it can be issued directly, without a
self-referential subquery). At `base_commit` it computed that decision by counting
the query's recorded table references that have a positive reference count and
asking whether the count is exactly one:

```python
# django/db/models/sql/compiler.py — SQLDeleteCompiler.single_alias
@cached_property
def single_alias(self):
    return sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1
```

For a full-table deletion (`Model.objects.all().delete()`) the query has **no
recorded table references yet** (`alias_map` is empty), so the sum is `0`, the
predicate is `False`, and the caller (`SQLDeleteCompiler.as_sql`) takes the
subquery branch — emitting `DELETE FROM t WHERE pk IN (SELECT pk FROM t)`. The
gold patch first **ensures the deletion's own primary table is recorded among the
referenced tables** before counting:

```python
@cached_property
def single_alias(self):
    # Ensure base table is in aliases.
    self.query.get_initial_alias()
    return sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1
```

After this, a full-table deletion has exactly one active referenced table, the
predicate is `True`, and `as_sql` emits the direct `DELETE FROM t`.

### The deep-modeled callee `get_initial_alias`
`Query.get_initial_alias` (django/db/models/sql/query.py:916) is an UNCHANGED
callee that the fix now invokes. Its behavior (read at base_commit):

```python
def get_initial_alias(self):
    if self.alias_map:
        alias = self.base_table          # = first key of alias_map
        self.ref_alias(alias)            # alias_refcount[alias] += 1
    else:
        alias = self.join(BaseTable(self.get_meta().db_table, None))
                                         # adds db_table to alias_map, refcount = 1
    return alias
```

- **empty `alias_map`**: a new reference to the primary table is created with
  reference count `1` (`join` → `table_alias(create=True)` sets
  `alias_refcount[db_table] = 1`).
- **non-empty `alias_map`**: the reference count of the **first-recorded** table
  (`base_table = next(iter(alias_map))`) is incremented by one (`ref_alias`).

This is modeled deeply (NOT axiomatized) as `includePrimary` and validated against
the real callee by G-CONF (A-reference).

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_isSingleTableDelete` | `SQLDeleteCompiler.single_alias` (django/db/models/sql/compiler.py:1408-1410) |
| `problem_spec_isSingleTableDelete`   | the post-condition `single_alias` must satisfy |
| `includePrimary` (pure helper)       | deep model of `Query.get_initial_alias` (django/db/models/sql/query.py:916) restricted to its effect on the reference-count multiset |
| `activeCount` (pure helper)          | `sum(alias_refcount[t] > 0 for t in alias_map)` |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `refs : List Nat` | `[query.alias_refcount[t] for t in query.alias_map]` (insertion-ordered) | the reference counts of the query's recorded table references, in `alias_map` insertion order. `Nat ↔ int ≥ 0`. The element NAMES are irrelevant to the boolean (they are only dict keys) so only the counts are modeled; their order matters solely because `get_initial_alias`'s non-empty branch increments the FIRST one. |
| result `: Bool` | `bool(SQLDeleteCompiler.single_alias)` | `true ↔ True` |

`includePrimary refs`:
  - `refs = []`            ↔ empty `alias_map` ⇒ a fresh primary-table reference, count `1`  → `[1]`
  - `refs = c :: rest`     ↔ non-empty `alias_map` ⇒ first (base) reference count `c` bumped → `(c+1) :: rest`

## Callee provenance / flag deps
- No unchanged callee is consumed as an `axiom`. `get_initial_alias` is modeled
  deeply (`includePrimary`) and its model is validated == the real callee by
  G-CONF over the bijection (A-reference). The proof consumes no opaque-callee
  property, so there is no `axiom <callee>_prop` and `axiom_check.py` is a skip
  stub.
- No flag dependency.

## G-CONF fuzz seed
- pinned seed: `12965`
- ≥10^5 fuzzed `refs` lists (lengths 0..6, each count drawn 0..3, including the
  empty list with high weight — the discriminating case). For each, a real Django
  `Query` is materialized (`alias_map`/`alias_refcount` set to the fuzzed
  references; the empty case is left as a fresh full-table-delete query so the
  REAL `get_initial_alias` empty branch runs), a real `SQLDeleteCompiler` is built,
  and `compiler.single_alias` is the oracle. The shadow is the Lean impl
  transliterated (`includePrimary` then count-active==1).
