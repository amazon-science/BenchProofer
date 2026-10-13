# mapping.md — django__django-16255

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 444b6da7cc229a58a2c476a52e45233001dc7073`, states the type
abstraction, and gives the provenance of the (single, deeply-modelled) changed
operation.

Repo file under change: `django/contrib/sitemaps/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `latest_stamp(stamps)` | `Sitemap.get_latest_lastmod(self)` — `django/contrib/sitemaps/__init__.py:165` (changed body line 170) | the modeled changed function: report the most recent per-entry modification stamp across a section's entries |
| `stamps: List[int]` | `[self.lastmod(item) for item in self.items()]` — the list comprehension at `__init__.py:170` | the collection of per-entry stamp values, one per enumerated entry |
| `Result(): Optional[int]` | the value `get_latest_lastmod` returns on the callable-`lastmod` branch (`max(...)` / `None`) | the reported latest stamp, or the absent marker |

Repo context the model abstracts away (unchanged by the patch, not referenced
from the consumer spec view):
- `self.items()` (`__init__.py:124`) enumerates the section's entries — the base
  returns `[]`; subclasses override. The model takes the already-collected
  per-entry stamp list as its input, so `items()` is not a modelled callee.
- `self.lastmod` (a per-entry callable, e.g. `__init__.py:246`) maps one entry to
  its stamp. The model takes the collected stamps directly; `lastmod` is folded
  into the construction of the `List[int]` input and is not a modelled callee.
- The `hasattr(self, "lastmod")`, `callable(self.lastmod)`, the
  `except TypeError: return None` branch, and the non-callable
  `return self.lastmod` branch (`__init__.py:166-174`) are UNCHANGED by the
  patch. The patch touches only the callable-branch reduction at line 170; the
  model scopes itself to that reduction (the comparable-stamp path the F2P test
  exercises) and does not re-model the unchanged guards.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the list `[self.lastmod(item) for item in self.items()]` of comparable stamp values (Python `date`/`datetime`, which are totally ordered by `<`/`max`) | `List[int]` of comparable stamps | a stamp `s_k` ↔ `stamps[k]`; ordering `s_j < s_k` ↔ `stamps[j] < stamps[k]`; `len` of the comprehension ↔ `len(stamps)`. The tested behaviour (empty ⇒ absent marker; non-empty ⇒ maximum) depends only on comparability and the empty/non-empty split, not on the concrete stamp type, so `int` is a faithful carrier (the F2P test distinguishes only "no entries ⇒ no `Last-Modified` header" from "entries ⇒ the latest"). |
| the returned `None` (absent marker — no `Last-Modified` to emit) | `None` (`Optional[int]`) | `None` ↔ `None`. |
| the returned `max(...)` value (a stamp) | the non-`None` `int` result | the greatest element. |

`date`/`datetime` comparison is total on the values a section produces, so
`max` over them is exactly `max` over the corresponding `int` carriers; the
empty-collection behaviour (`default=None`) is type-independent.

## 3. The changed operation (deeply modelled — checked by G-AX / axiom_check.py)

### 3.1 `latest_stamp` deep model ↔ `max(values, default=None)` (A-reference)
**Callee:** the Python builtin `max(iterable, *, default)`. The changed
operation is the reduction at `__init__.py:170`:

```
- return max([self.lastmod(item) for item in self.items()])
+ return max([self.lastmod(item) for item in self.items()], default=None)
```

The pre-patch `max(L)` (no `default`) raises `ValueError: max() arg is an empty
sequence` when `L == []` (an empty section). The post-patch `max(L, default=None)`
returns `None` for `L == []` and the greatest element otherwise. This is the
single behavioural delta.

It is **modelled deeply** by the `latest_stamp` impl (a running maximum seeded
with the absent marker `None`), NOT hidden behind a `@ContractOnly` axiom — the
proof consumes no axiom. The deep model is validated **== the real builtin**
out-of-band by `axiom_check.py` (G-AX): it asserts
`latest_stamp(values) == max(values, default=None)` on boundary inputs
(critically the EMPTY list, plus singletons, negatives, duplicates,
sorted/reversed) and 50 000 randomized fuzz inputs (with `n == 0` fuzzing the
empty section), and asserts the empty case yields `None` and does not raise.
Docs: https://docs.python.org/3/library/functions.html#max ("If the iterable is
empty and default is not provided, a ValueError is raised.").

No flag dependency (the reduction is `max` with a keyword `default`; no locale,
no `quote=`-style configuration). There are **no consumed axioms** in this
bundle (the `axioms` region of model.py is empty).
