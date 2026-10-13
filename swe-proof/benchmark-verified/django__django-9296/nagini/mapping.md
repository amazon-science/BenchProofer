# mapping.md — django__django-9296

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 84322a29ce9b0940335f8ab3d60e55192bef1e50`, states the type
abstraction, and gives the provenance of the axiom / deep-model reference (the
unchanged callee + the exact behaviour relied on).

Repo file under change: `django/core/paginator.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `paginate_iter(page_numbers)` | the NEW page traversal added to `Paginator` (`django/core/paginator.py`, inserted at line 37, between `__init__` (line 29) and `validate_number` (line 37 pre-patch)) — `for page_number in self.page_range: yield self.page(page_number)` | the modeled changed behaviour: the collection's page traversal |
| `page_numbers` (parameter, `List[int]`) | `self.page_range` — `Paginator.page_range` property (`django/core/paginator.py:102`, body `return range(1, self.num_pages + 1)` at line 107) | the collection's ordered run of 1-based page numbers; an UNCHANGED property the new traversal iterates |
| `page_lookup(number)` *(axiom — A-consumed; also the A-reference target of `mapped`)* | `Paginator.page(number)` — `django/core/paginator.py:67` (returns `self._get_page(self.object_list[bottom:top], number, self)` at line 74) | the collection's UNCHANGED page-by-number accessor the new traversal yields per page number |
| `mapped(s)` *(deep model — A-reference)* | the body of the new traversal: the per-page-number image of `self.page` over `self.page_range`, in order | pure spec of the traversal output; validated `mapped(page_range) == real Paginator.__iter__` by axiom_check.py (G-AX), NOT consumed as an axiom |

The change is purely additive: the gold patch adds a `Paginator.__iter__`
generator and touches nothing else. `page_range`, `page`, `num_pages`,
`_get_page`, and the `Page` class are all unchanged by the patch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.page_range` — a `range(1, num_pages + 1)` object | `page_numbers: List[int]` (its materialized elements `[1, 2, ..., num_pages]`) | iterating the `range` ↔ iterating the list left-to-right; `len(range)` ↔ `len(page_numbers)`; the empty range (`num_pages == 0`) ↔ `[]`. The model does not re-derive `page_range == [1..num_pages]` (an unchanged property); it abstracts `page_range` to its ordered element list and pins that the traversal maps each element through `page` in order. |
| a yielded `Page` object `self.page(n)` | `page_lookup(n): int` — an opaque per-page-number value | a `Page` is a rich object; the traversal's contribution is *which* page is produced *in what order*, not the page's internals. Each yielded `Page` is abstracted to the opaque value `page_lookup(n)`, a pure function of `n`. The observable page content (`list(page)`) is `page`'s unchanged responsibility, checked equal to `mapped`'s positional image by G-AX. |
| the generator produced by `__iter__` | `List[int]` `Result()` (the yielded values, in order) | a generator consumed left-to-right ↔ the result list read left-to-right; `list(iter(paginator))` ↔ `Result()`. The order and per-position value are what the F2P test observes (`list(next(page_iterator))` for successive pages). |

`range`/generator iteration is abstracted to `List[int]`; the specification is
phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `mapped` deep model ↔ real `Paginator.__iter__` (A-reference)
**Callee chain:** `Paginator.page_range` (unchanged, `paginator.py:102`) and
`Paginator.page` (unchanged, `paginator.py:67`). The new traversal is

```python
def __iter__(self):
    for page_number in self.page_range:
        yield self.page(page_number)
```

i.e. the in-order image of the unchanged `self.page` over the unchanged
`self.page_range`. The model spells this out **deeply** as the front-recursive
map `mapped(s) == PSeq(page_lookup(s[0])) + mapped(s.drop(1))` over the page-
number run `s`. There is no `__iter__` axiom the proof consumes; the deep model
is instead validated equal to the real traversal out-of-band by axiom_check.py
(G-AX): it asserts, over a broad sweep of collection shapes (object_list length,
per_page, orphans, allow_empty_first_page; incl. the empty / single-page /
orphan boundaries and the F2P witness `Paginator([1,2,3], 2)`), that

```python
list(iter(paginator)) == [paginator.page(n) for n in paginator.page_range]
```

page-for-page (compared by page number AND page content). This is exactly the
order-and-per-position correspondence `mapped` encodes.

### 3.2 `page_lookup` ↔ `Paginator.page` (A-consumed)
**Callee:** `Paginator.page(number)` (`paginator.py:67`), unchanged by the
patch. The axiom's contract is the WEAKEST sufficient one: `Ensures(True)` — it
claims nothing about the value beyond that it is a well-defined PURE function of
the 1-based page number (the value for a given page number does not depend on
when in the traversal it is observed). The traversal proof relies only on this:
that visiting page number `n` produces `page_lookup(n)`, the same value
regardless of traversal position. The axiom deliberately does NOT encode the
page's slice/content, orphan handling, or any `EmptyPage`/`PageNotAnInteger`
behaviour — those are `page`'s unchanged concern and not what `__iter__`
changes, so over-claiming them would be unsound and unnecessary.

**Soundness check (G-AX):** `axiom_check.py` constructs real `Paginator`
instances and asserts (a) `paginator.page(n)` is deterministic in `n`
(`page(n) == page(n)` by number + content), the only property the axiom needs,
and (b) the A-reference equality of §3.1. It imports `django.core.paginator`
(the very module the patch edits), available at the official evaluation
interpreter in-container. Exit 0 iff sound.

**Flag/configuration dependence:** none. The traversal calls `self.page` with
the default arguments and reads `self.page_range`; no keyword/flag affects the
modeled order-and-image property. (The page *content* depends on `per_page`,
`orphans`, `count` — all `page`'s unchanged responsibility, swept by G-AX but
outside the axiom's claim.)
