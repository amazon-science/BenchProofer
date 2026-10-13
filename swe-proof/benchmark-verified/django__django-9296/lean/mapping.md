# mapping.md — django__django-9296

## Instance
- repo: django/django
- base_commit: 84322a29ce9b0940335f8ab3d60e55192bef1e50
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch makes a paginator object directly iterable: iterating it walks the
paginator's 1-based range of page numbers and yields, in order, the page object
for each number. Concretely (gold patch, `django/core/paginator.py`):

```python
def __iter__(self):
    for page_number in self.page_range:
        yield self.page(page_number)
```

`page_range` and `page(...)` already existed at `base_commit` and are NOT changed
by the patch; the patch only adds the iteration protocol that drives them. The
observable effect (exercised by the F2P test `test_paginator_iteration`) is the
in-order sequence of page object-list slices.

## Modeled function
| Lean symbol | Python source @ base_commit | role |
|---|---|---|
| `implementation_paginatorPages` | `Paginator.__iter__` (django/core/paginator.py:37, gold-added) | modeled function |
| `problem_spec_paginatorPages`   | the post-condition this iteration must satisfy | — |
| `pageCount` (pure helper)       | `Paginator.num_pages` (paginator.py:93) — unchanged callee, modeled deeply | A-reference¹ |
| `pageNumbers` (pure helper)     | `Paginator.page_range` (paginator.py:101) — unchanged callee, modeled deeply | A-reference¹ |
| `pageSlice` (pure helper)       | `Paginator.page(...).object_list` (paginator.py:67) — unchanged callee, modeled deeply | A-reference¹ |

¹ These three are **unchanged** callees the new iteration drives. They are modeled
DEEPLY as concrete pure helpers (arithmetic + list slicing), NOT axiomatized — so
the postcondition is grounded entirely in the inputs (SPEC_GUIDE §0.8). Their
deep models are validated == the real callees by G-CONF (the whole impl is R/I);
there is no `opaque`/`axiom` in the bundle, so `axiom_check.py` is a skip stub and
`deep_model_references` records them for provenance only.

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `objectList : List α` | `Paginator.object_list` (a list) | the paged collection; `count = len(object_list)` |
| `perPage : Nat` | `int(per_page)` | objects per page; domain `per_page ≥ 1` (Python `ceil(hits/per_page)` divides by it) |
| `orphans : Nat` | `int(orphans)` | trailing items folded into the last page; `orphans ≥ 0` |
| `allowEmpty : Bool` | `allow_empty_first_page` (bool) | whether an empty list still yields one (empty) page |
| result `: List (List α)` | `[p.object_list for p in iter(paginator)]` | per yielded page, its object-list slice (what the F2P test observes via `list(next(...))`) |

`List α` ↔ Python `list` is the identity bijection on the slice contents.
`Nat` ↔ non-negative `int`. The yielded `Page` object is represented by its
`object_list` slice — the only field the F2P test observes (`list(next(page_iterator))`).

## num_pages / page_range / page modeling (deep, == real callees)
- `pageCount count perPage orphans allowEmpty`:
  `if count == 0 and not allowEmpty then 0 else ceil(max(1, count - orphans) / perPage)`,
  with `ceil(h/p) = (h + p - 1) / p` for `p ≥ 1` (Nat floor division). Mirrors
  `num_pages` exactly: `count - orphans` (Python int subtraction that may go
  negative) ↔ `max 1 (count - orphans)` (Nat truncated subtraction), agreeing
  because `max(1, k)` clamps any non-positive `k` to `1`.
- `pageNumbers ... = List.range' 1 (pageCount ...)` = `[1, …, num_pages]` ↔
  `range(1, num_pages + 1)` (= `page_range`).
- `pageSlice objectList perPage orphans n` for 1-based `n`:
  `bottom = (n-1)*perPage`, `top = bottom + perPage`, then
  `if top + orphans ≥ count then top := count`, returning
  `objectList[bottom:top]` (`(drop bottom).take (top-bottom)`). Mirrors `page(n)`:
  `validate_number(n)` is the identity for `n ∈ [1, num_pages]` (never raises on a
  `page_range` element), so it is elided.

## Callee provenance / flag deps
- No unchanged repo callee is *consumed as an axiom*: `num_pages`, `page_range`,
  and `page` are pure functions of `(object_list, per_page, orphans,
  allow_empty_first_page)` and are modeled deeply (R/I), so they are validated by
  the G-CONF differential test against the real (post-patch) `Paginator`. Hence the
  `axioms` region is empty and `axiom_check.py` is a skip stub.
- Flag dependency: `allow_empty_first_page` only changes `num_pages` when
  `count == 0`. G-CONF fuzzes `allowEmpty ∈ {True, False}` and includes empty
  object lists.

## G-CONF fuzz seed
- pinned seed: `9296`
- ≥10^5 fuzzed `(objectList, perPage, orphans, allowEmpty)` tuples; lengths
  include `0` (empty) and small/large values; `perPage ∈ [1, …]`,
  `orphans ∈ [0, …]`, biased to the `orphans`-near-`per_page` and last-page
  boundaries.
