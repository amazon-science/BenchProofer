# refinement.md — django__django-9296

Maps every operation in `implementation_paginatorPages` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `paginatorPages` (`Paginator.__iter__`, gold-added)

Post-patch repo code (`patch.diff`, `django/core/paginator.py:37-39`):
```python
def __iter__(self):
    for page_number in self.page_range:
        yield self.page(page_number)
```

Lean impl (`implementation_paginatorPages`):
```lean
def implementation_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
    List (List α) := Id.run do
  let mut pages : List (List α) := []
  for n in pageNumbers objectList.length perPage orphans allowEmpty do
    pages := pages ++ [pageSlice objectList perPage orphans n]
  return pages
```

The Python `__iter__` is a generator yielding `Page` objects; the F2P test
observes each yielded page via `list(next(page_iterator))`, i.e. the page's
`object_list` slice. The Lean impl materializes that observed sequence as the
list of per-page slices (a generator that is fully consumed in order is
extensionally its list of yields; the `Page` object is represented by the only
observed field, its `object_list` slice — mapping.md).

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut pages := []` | the generator's (implicit) accumulated yield sequence, empty before the loop | **R** | the yielded-`Page` sequence ↔ `List (List α)` of object-list slices; empty start = no pages yielded yet. |
| 2 | `for n in pageNumbers objectList.length perPage orphans allowEmpty do` | `for page_number in self.page_range:` | **R** (deep model of unchanged callee `page_range`) | `pageNumbers count perPage orphans allowEmpty = List.range' 1 (pageCount …)` ↔ `range(1, num_pages + 1)`. `pageCount` reproduces `num_pages` exactly: `if count==0 and not allow_empty: 0 else ceil(max(1,count-orphans)/per_page)`, with `(h+p-1)//p = ceil(h/p)` for `p≥1`, and `max 1 (count-orphans)` (Nat truncated sub) ↔ `max(1, count-orphans)`. Validated == real `page_range` by G-CONF. |
| 3 | `pages := pages ++ [pageSlice objectList perPage orphans n]` | `yield self.page(page_number)` | **R** (deep model of unchanged callee `page`) | each yielded `Page(page_number)` is observed as its `object_list` slice. `pageSlice` reproduces `page(n)`: `bottom=(n-1)*per_page`, `top=bottom+per_page`, `if top+orphans>=count: top=count`, returning `object_list[bottom:top]` (`(drop bottom).take (top-bottom)`). `validate_number(n)` is the identity for `n ∈ page_range` (never raises on a `page_range` element), so it is elided. Appending to the tail ↔ yielding in increasing page order. |
| 4 | `return pages` | end of generator (sequence of all yields) | **R** | the materialized slice sequence ↔ the fully-consumed generator's yields, in order. |

All impl-region ops are **R** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched paginator's `num_pages` / `page_range` / `page(n)` callees.

## Callee provenance (no consumed axiom)

- `self.page_range` (`paginator.py:101`, property) returns `range(1,
  num_pages+1)` UNCHANGED by the patch; modeled deeply as `pageNumbers`. No
  property consumed.
- `self.num_pages` (`paginator.py:93`, cached_property) UNCHANGED by the patch;
  modeled deeply as `pageCount`.
- `self.page(n)` (`paginator.py:67`) UNCHANGED by the patch; modeled deeply as
  `pageSlice` (the slice it computes), with `validate_number` elided because it
  is the identity on `page_range` elements.
- `self.count` is `len(object_list)` for a plain list (`paginator.py:91`); the
  `QuerySet.count()` branch and the `_check_object_list_is_ordered` warning are
  orthogonal to the iteration value and not modeled. The F2P test uses a plain
  `list`.

## Soundness check (verify ⟹ correct)

- `problem_spec_paginatorPages` pins the result EXACTLY: `result =
  (pageNumbers …).map (pageSlice …)` — directive 5 (frame): both the length (the
  page count) and every element (page `k`'s slice) are determined by the inputs.
  No output component is left unconstrained. No ungrounded oracle (directive 8):
  the postcondition is dischargeable only by actually computing the page numbers
  and the per-page slices from `objectList`/`perPage`/`orphans`/`allowEmpty`.
- The prepatch impl reproduces the PRE-FIX behavior: at `base_commit` `Paginator`
  defined no `__iter__`, so `iter(paginator)` raised `TypeError` — no pages were
  ever produced. The faithful prepatch skeleton returns the empty page list
  `[]`. It violates the spec on the discriminating clause `pageCount … ≥ 1`
  (i.e. any non-degenerate paginator): the spec requires a non-empty list of
  slices, but the prepatch returns `[]`. Its carried `sorry` proof cannot close
  (G-DIFF/G-PANEL).
- This discriminating case is precisely the FAIL_TO_PASS assertion added by the
  test patch (`test_paginator_iteration`): `Paginator([1,2,3], 2)` iterated must
  yield pages `[1,2]` then `[3]`. Pre-fix iteration raised; post-fix it walks the
  two pages. The prepatch's empty result fails the first `next(page_iterator)`.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  paginator iteration over hand-picked edge cases (the F2P input, empty list with
  `allow_empty` both ways, exact-multiple lengths, orphan-absorption boundaries,
  `orphans > count`, `per_page > count`) plus ≥1e5 fuzzed inputs.
