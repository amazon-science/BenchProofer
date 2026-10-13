# mapping.md — django__django-11490

## Instance
- repo: django/django
- base_commit: a7038adbd02c916315b16939b835f021c2ee8880
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`SQLCompiler.get_combinator_sql` (django/db/models/sql/compiler.py:410) builds the
SQL for a composed (UNION / INTERSECT / DIFFERENCE) query. It iterates over the
per-part compilers; for each part whose underlying `Query` does NOT already fix a
column list (`not compiler.query.values_select`) while the composed query DOES
(`self.query.values_select`), it adopts the composed column list by calling
`compiler.query.set_values((*extra_select, *values_select, *annotation_select))`.

At base_commit `compiler.query` is a reference to a `Query` object that is SHARED
across repeated evaluations of the same composed queryset, and `set_values`
MUTATES it in place. So the first time the composed queryset is evaluated for a
column list, every part's shared `Query` is permanently rewritten to that list;
a SECOND evaluation requesting a DIFFERENT column list finds `values_select`
already non-empty and silently keeps the stale list — the column list cannot be
changed (the symptom in the issue).

The gold patch clones the part's query before mutating it, so the shared `Query`
is never altered:

```python
 if not compiler.query.values_select and self.query.values_select:
+    compiler.query = compiler.query.clone()
     compiler.query.set_values((...))
```

`Query.clone` (django/db/models/sql/query.py:292) returns a fresh copy; the
subsequent `set_values` mutates only that copy.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_propagateColumns` | the per-part column-propagation loop of `SQLCompiler.get_combinator_sql` (compiler.py:422-433) |
| `problem_spec_propagateColumns`   | the post-condition that loop must satisfy |
| `QueryPart`                       | the underlying `Query` of one combined-query compiler (`compiler.query`), observed by its column list |
| `QueryPart.columns`               | `Query.values_select` (tuple of str) — the column list the part projects; empty ⇔ no specific list |
| `composedColumns`                 | the composed query's projected column list `self.query.values_select` (with `extra_select`/`annotation_select`) |
| result `.fst` of an entry         | the query actually used to build that part's SQL THIS evaluation (`compiler.query` after the branch) |
| result `.snd` of an entry         | the part's underlying `Query` definition AS CARRIED FORWARD (the shared object after the branch) |

## Modeling the aliasing bug in a pure setting
Lean is referentially transparent: there is no in-place mutation or aliasing, so
the persistence symptom ("a later evaluation sees a stale list") cannot be
observed by re-running the function. The faithful pure encoding makes the two
distinct quantities the buggy code conflated into observable OUTPUTS:

- `.fst` — the query built FOR THIS evaluation (adopts the composed list);
- `.snd` — the part definition CARRIED FORWARD (must remain the input part, so a
  later evaluation is free to choose another list).

The fix (`clone()` then `set_values` on the copy) keeps these two distinct:
`.fst` adopts the composed list, `.snd` equals the input part. The bug
(`set_values` on the shared object) makes them the SAME altered object, so `.snd`
no longer equals the input — exactly the carried-forward staleness. `.snd = parts`
(the directive-5 frame clause) is therefore the discriminator the prepatch
violates.

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `parts : List QueryPart` | the list of `compiler.query` objects for the combined-query compilers | order preserved |
| `QueryPart.columns : List String` | `Query.values_select` (tuple of str) | emptiness preserved; element order preserved |
| `composedColumns : List String` | `self.query.values_select` (the composed query's column list) | empty ⇔ composed query fixes no specific list |
| result `: List (QueryPart × QueryPart)` | per part, `(query_used_this_eval.values_select, shared_query.values_select_after)` | observed by the column lists |

`List String` ↔ Python tuple-of-str is the identity bijection (order + contents).

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom and none is deep-modeled.
  `Query.set_values` and `Query.clone` are not modeled as callees: the only
  observable each contributes to the modeled behavior is "the column list the
  resulting query projects", captured directly as `QueryPart.columns`. The model
  therefore needs no `opaque`/`axiom` callee contract; `axiom_check.py` is a skip
  stub.
- Branch dependency: a part adopts the composed list iff `not part.values_select`
  (part fixes no list) AND `self.query.values_select` is non-empty (composed query
  requests a list). G-CONF fuzzes both conditions across all parts.

## G-CONF fuzz seed
- pinned seed: `11490`
- ≥10^5 fuzzed `(parts' column lists, composedColumns)` inputs. The shadow is the
  R/I transliteration of `implementation_propagateColumns`; the oracle replays the
  POST-PATCH per-part propagation (`clone` then `set_values` on the copy, leaving
  the shared part untouched), observing, per part, the pair
  `(used_query_columns, carried_forward_part_columns)`.
