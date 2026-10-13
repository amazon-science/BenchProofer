# mapping.md — django__django-15022

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`e1d673c373a7d032060872b690a92fc95496612e`). No pre-existing solution consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_searchFilter` / `problem_spec_searchFilter` / `correct_searchFilter` | the search-term filtering loop inside `ModelAdmin.get_search_results` (the `for bit in smart_split(search_term): … queryset = queryset.filter(or_queries)` block, lines 1031–1046) | `django/contrib/admin/options.py:1031-1046` |
| `parents : List Parent` | the `queryset` being narrowed (a collection of model instances) | param `queryset` of `get_search_results` (`:994`) |
| `Parent.rows : List Row` | for one instance, the set of related rows reachable through the multi-valued joins induced by the search fields | the JOIN rows produced by the `child__…`-style lookups |
| `Row.matched : List Nat` | for one related row, the set of (processed) search terms that row matches under the OR-of-lookups | per-row evaluation of `or_queries = Q(*((orm_lookup, bit) …), _connector=OR)` |
| `terms : List Nat` | the processed list of search words `smart_split(search_term)` after the per-bit unescape | the `bit` iteration source (`:1034`) |

## The observable behavior

`get_search_results` narrows `queryset` by the user's `search_term`. At
`base_commit` the search-term loop is:

```python
if search_fields and search_term:
    orm_lookups = [construct_search(str(search_field)) for search_field in search_fields]
    for bit in smart_split(search_term):
        if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
            bit = unescape_string_literal(bit)
        or_queries = models.Q(*((orm_lookup, bit) for orm_lookup in orm_lookups), _connector=models.Q.OR)
        queryset = queryset.filter(or_queries)        # <-- one .filter() per word
    ...
return queryset, may_have_duplicates
```

When a search field spans a **multi-valued relation** (e.g. `child__name`,
a reverse FK / m2m), each `queryset.filter(...)` call introduces its OWN join,
so successive per-word filters may each be satisfied by a DIFFERENT related row.
The base_commit semantics for an instance is therefore:

> instance kept ⟺ **for every** word, **there exists** a related row matching it
> (under the OR over the search fields) — possibly a different row per word.

The gold patch collects each word's OR-query into `term_queries` and applies a
single combined `queryset.filter(models.Q(*term_queries))`. Because it is one
filter (one set of join aliases), the AND of the per-word queries must be
satisfied **within a single related row**. The post-patch semantics is:

> instance kept ⟺ **there exists** a related row that matches **every** word
> (under the OR over the search fields).

That is the quantifier swap `(∀word ∃row) → (∃row ∀word)`. It both removes the
per-word joins (the performance issue) and corrects over-matching across
multi-valued relations (the F2P assertions). The output component
`may_have_duplicates` is **unchanged** by the patch and orthogonal to this
observable; it is abstracted out of the modeled function (see below).

### F2P anchors
- `test_many_search_terms`: `search_fields=['child__name']`, query `'daniel '*80`
  (80 identical words), one parent with children `Danielle`, `Daniel`. Post-patch:
  some single child contains `daniel` ⇒ kept; single combined filter ⇒ exactly
  ONE join. `count()==1`, `JOIN count==1`.
- `test_related_field_multiple_search_terms`: `search_fields=['child__name','child__age']`,
  parent Mary with `Danielle/18`, `Daniel/19`.
  - `'danielle 19'`: no single child matches both words ⇒ `count()==0`
    (pre-patch wrongly returned 1, matching `danielle` on one child and `19` on
    the other).
  - `'daniel 19'`: child `Daniel/19` matches both ⇒ `count()==1`.
- `test_multiple_search_fields`: `('Mary Jonathan Duo', 1) → 0` — same quantifier
  fix across multiple multi-valued search fields.

## Lean ↔ Python type bijection

| Python | Lean | bijection |
|---|---|---|
| `queryset` (collection of distinct model instances) | `parents : List Parent` | one element per distinct instance; result compared at instance-identity level (the `.count()`/`.distinct()` observable the F2P tests assert) |
| the related-row JOIN rows for one instance | `Parent.rows : List Row` | one `Row` per related row the search joins expose for that instance |
| "this related row matches processed word `w` under `Q(OR of (lookup, w))`" | `w ∈ Row.matched` (`Row.matched.contains w`) | the OR-over-search-fields icontains/iexact/istartswith/search test for one row, folded to a per-row matched-term set. The OR-of-lookups + per-lookup operator + `icontains` substring test are UNCHANGED by the patch, so they are folded into the input matrix |
| `smart_split(search_term)` + per-bit `unescape_string_literal` | `terms : List Nat` | processed search words as opaque term-ids (the splitting + unescape are unchanged by the patch and folded into the input); equal words ⇒ equal ids (so `'daniel '*80 → [k,k,…,k]`) |
| `queryset.filter(...)` returning the narrowed queryset | `List.filter (predicate) parents` | order-preserving subset; keeps each instance at most once |
| return `queryset` | result `: List Parent` | the narrowed instance collection |
| return `may_have_duplicates` | — (abstracted out) | unchanged by the patch; computed after the loop from `lookup_spawns_duplicates(orm_lookups)`; orthogonal to the quantifier observable, not modeled |

## Callee provenance / flag deps

- **No UNCHANGED callee needs an axiom.** The changed op (the quantifier
  structure of the filtering) is modeled DEEPLY with concrete Lean operations
  (`List.filter` of `rows.any` of `terms.all`). → `axioms` region is empty;
  `axiom_check.py` is a skip stub.
- `smart_split`, `unescape_string_literal`, `construct_search`, `models.Q`/`.filter`'s
  per-row OR-of-lookups matching are all UNCHANGED by the patch. They are folded
  into the inputs (`terms`, `Row.matched`) rather than modeled — they are not
  consumed axioms and not reference callees, because the modeled value (which
  instances survive) does not depend on their internals, only on the per-(row,word)
  match matrix they produce.
- `may_have_duplicates` / `lookup_spawns_duplicates` — unchanged by the patch,
  abstracted out of the modeled result (frame note above).
- Flag deps: none. The `bit.startswith(('"',"'"))` quote-unescape branch is
  unchanged and folded into the processed `terms`.

## G-CONF fuzz seed

Pinned seed: **15022**. `conformance_check.py` stands up a real in-memory Django
(sqlite) with `Parent`/`Child` models and calls the REAL patched
`ModelAdmin.get_search_results` over fuzzed scenarios (random parents, each with
a random set of children, each child a random subset of NATO-word tokens;
search term = a random multiset of those tokens). It bridges each abstract
scenario to DB rows (token-id ↦ a unique NATO word; a `Row.matched` set ↦ a
child whose `name` is the space-join of its tokens; no token is a substring of
another), then diffs the real surviving parent-pk set against the R/I shadow of
`implementation_searchFilter`. ≥10⁵ randomized draws plus enumerated edge cases.
Exit 0 iff zero disagreements.
