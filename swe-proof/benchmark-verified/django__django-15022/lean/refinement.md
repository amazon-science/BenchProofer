# refinement.md — django__django-15022

Operation correspondence between the Lean `implementation_searchFilter` skeleton
and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the changed behaviour (the quantifier
structure of the search-term filtering) is modeled DEEPLY with concrete Lean
operations. Every row is **R** or **I**. (G-AX is therefore a skip stub; the R/I
legs are differential-tested by G-CONF against the real patched
`get_search_results`.)

## What the gold patch changes

`patch.diff` rewrites the search-term loop in `ModelAdmin.get_search_results`
(`django/contrib/admin/options.py`). Pre-patch:

```python
for bit in smart_split(search_term):
    ...
    or_queries = models.Q(*((orm_lookup, bit) for orm_lookup in orm_lookups), _connector=models.Q.OR)
    queryset = queryset.filter(or_queries)        # one .filter() per word
```

Post-patch:

```python
term_queries = []
for bit in smart_split(search_term):
    ...
    or_queries = models.Q(*((orm_lookup, bit) for orm_lookup in orm_lookups), _connector=models.Q.OR)
    term_queries.append(or_queries)
queryset = queryset.filter(models.Q(*term_queries))   # one combined .filter()
```

The behavioural change is a quantifier swap over the related rows that the
multi-valued search joins expose. Pre-patch each `queryset.filter(...)`
introduces its own join, so successive words may be satisfied by DIFFERENT
related rows: a record survives iff **∀word ∃row** matching that word. Post-patch
the per-word OR-queries are combined into one `filter`, sharing one set of join
aliases, so the AND across words must hold **within a single related row**: a
record survives iff **∃row ∀word** that row matches.

The other output component, `may_have_duplicates`, is computed AFTER this loop
from `lookup_spawns_duplicates(orm_lookups)` and is unchanged by the patch; it is
orthogonal to the modeled observable and abstracted out of the modeled function
(frame note in mapping.md).

## `implementation_searchFilter` ↔ patched `get_search_results` loop

| Lean op | patch.diff / base counterpart | tag | note |
|---|---|---|---|
| `let mut termQueries : List Nat := []` | `term_queries = []` | R | the accumulator the patch introduces; `models.Q` OR-query per word ↦ the processed word-id `t` (the per-row match test for a word is folded into `Row.matched`, since it is unchanged by the patch) |
| `for t in terms do termQueries := termQueries ++ [t]` | `for bit in smart_split(search_term): … term_queries.append(or_queries)` | R | `smart_split` + per-bit unescape + per-word `or_queries` construction ↦ appending the processed word-id. The splitting/unescape/OR-construction are unchanged and folded into `terms`; the loop only accumulates |
| `return parents.filter (fun p => combinedMatch termQueries p)` | `queryset = queryset.filter(models.Q(*term_queries))` | R | the SINGLE combined filter. `models.Q(*term_queries)` AND-combines the per-word OR-queries over ONE join ↦ `combinedMatch`: keep a record iff one related row (`p.rows.any`) matches every word (`rowMatchesAll = terms.all (· ∈ row.matched)`). Empty `terms` ⇒ `models.Q()` (a no-op match-all) ↦ `combinedMatch [] = true`. `queryset.filter` order-preserving subset ↦ `List.filter` |

`combinedMatch` / `rowMatchesAll` are spec helpers (pure region) shared by spec
and impl: the impl's single-filter structure is exactly the post-patch
`queryset.filter(models.Q(*term_queries))`, and the spec pins the result to that
same filter. The discriminating observable — one related row must satisfy the
whole query — is `p.rows.any (terms.all (· ∈ ·.matched))`.

## Independently-observable behavior (G-DIFF)

`Solution_prepatch.lean` encodes the pre-patch control flow: a per-word loop
`qs := qs.filter (fun p => p.rows.any (fun r => r.matched.contains t))`, i.e. one
filter per word, each requiring only SOME related row to match that word. The
carried gold proof of `correct_searchFilter` fails to close precisely on inputs
where two words are matched by two different rows but no single row matches both:
the per-word impl keeps the record (`∀word ∃row`) while the spec drops it
(`∃row ∀word`). That is the exact FAIL_TO_PASS behaviour
(`test_related_field_multiple_search_terms`: `'danielle 19'` → `count()==0`, where
`danielle` matches one child and `19` another). A single prepatch suffices: the
quantifier-order defect is the one behaviour the patch fixes, and this prepatch
discriminates it (it also covers `test_many_search_terms`' single-join /
`test_multiple_search_fields`' over-matching, which are the same fix).
