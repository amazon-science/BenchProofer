# mapping.md — django__django-16255

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 444b6da7cc229a58a2c476a52e45233001dc7073`, states the type
abstraction, and gives the provenance of the (single, deeply-modeled) changed
operation.

Repo file under change: `django/contrib/sitemaps/__init__.py`.

Imports: `Velvet.Std` only (no extra `Mathlib.*` subdirectories beyond what
`Velvet.Std` re-exports; `max`/`LinearOrder` on `Int` and `List.drop`/`getElem!`
come from the standard front door).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `latestLastmod (stamps)` | `Sitemap.get_latest_lastmod(self)` — `django/contrib/sitemaps/__init__.py:165` (changed body line 170) | the modeled changed function: report the most recent per-entry modification stamp across a section's entries |
| `stamps : List Int` | `[self.lastmod(item) for item in self.items()]` — the list comprehension at `__init__.py:170` | the collection of per-entry stamp values, one per enumerated entry |
| `out : Option Int` | the value `get_latest_lastmod` returns on the callable-`lastmod` branch (`max(...)` / `None`) | the reported latest stamp, or the absent marker |
| `latestStamp : List Int → Option Int` | the reduction `max([...], default=None)` (post-patch) | the deep model of the changed reduction (A-reference, §3) |

Repo context the model abstracts away (unchanged by the patch, not referenced
from the consumer spec view):
- `self.items()` (`__init__.py:124`) enumerates the section's entries — the base
  returns `[]`; subclasses override. The model takes the already-collected
  per-entry stamp list as its input, so `items()` is not a modeled callee.
- `self.lastmod` (a per-entry callable, e.g. `__init__.py:246`) maps one entry to
  its stamp. The model takes the collected stamps directly; `lastmod` is folded
  into the construction of the `List Int` input and is not a modeled callee.
- The `hasattr(self, "lastmod")`, `callable(self.lastmod)`, the
  `except TypeError: return None` branch, and the non-callable
  `return self.lastmod` branch (`__init__.py:166-174`) are UNCHANGED by the
  patch. The patch touches only the callable-branch reduction at line 170; the
  model scopes itself to that reduction (the comparable-stamp path the F2P test
  exercises) and does not re-model the unchanged guards.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the list `[self.lastmod(item) for item in self.items()]` of comparable stamp values (Python `date`/`datetime`, totally ordered by `<`/`max`) | `List Int` of comparable stamps | a stamp `s_k` ↔ `stamps[k]`; ordering `s_j < s_k` ↔ `stamps[j] < stamps[k]`; `len` of the comprehension ↔ `stamps.length`. The tested behavior (empty ⇒ absent marker; non-empty ⇒ maximum) depends only on comparability and the empty/non-empty split, not on the concrete stamp type, so `Int` is a faithful carrier (the F2P test distinguishes only "no entries ⇒ no `Last-Modified` header" from "entries ⇒ the latest"). |
| the returned `None` (absent marker — no `Last-Modified` to emit) | `none : Option Int` | `None` ↔ `none`. |
| the returned `max(...)` value (a stamp) | `some v` (the non-`none` `Int` result) | the greatest element. |

`date`/`datetime` comparison is total on the values a section produces, so
`max` over them is exactly `max` over the corresponding `Int` carriers; the
empty-collection behavior (`default=None`) is type-independent. `Int` carries a
`LinearOrder`, so `max`, `le_max_left`, `le_max_right`, `max_choice` apply
exactly as the model uses them.

## 3. The changed operation (deeply modeled — checked by G-AX / axiom_check.py)

### 3.1 `latestStamp` deep model ↔ `max(values, default=None)` (A-reference)
**Callee:** the Python builtin `max(iterable, *, default)`. The changed
operation is the reduction at `__init__.py:170`:

```
- return max([self.lastmod(item) for item in self.items()])
+ return max([self.lastmod(item) for item in self.items()], default=None)
```

The pre-patch `max(L)` (no `default`) raises `ValueError: max() arg is an empty
sequence` when `L == []` (an empty section). The post-patch `max(L, default=None)`
returns `None` for `L == []` and the greatest element otherwise. This is the
single behavioral delta.

It is **modeled deeply** by `latestStamp` (a front-recursive running maximum
whose empty base case is the absent marker `none`), NOT hidden behind a consumed
axiom — `prove_correct` consumes no `axiom`/`opaque` callee contract. The deep
model is validated **== the real builtin** out-of-band by `axiom_check.py`
(G-AX): it asserts `latestStamp(values) == max(values, default=None)` on
boundary inputs (critically the EMPTY list, plus singletons, negatives,
duplicates, sorted/reversed) and 50 000 randomized fuzz inputs (with `n == 0`
fuzzing the empty section), and asserts the empty case yields `None` and does
not raise. Docs:
https://docs.python.org/3/library/functions.html#max ("If the iterable is empty
and default is not provided, a ValueError is raised.").

No flag dependency (the reduction is `max` with a keyword `default`; no locale,
no `quote=`-style configuration). There are **no consumed axioms** in this
bundle (the `axioms` region of Solution.lean is empty).

## 4. Pinned fuzz seed

- `axiom_check.py` (G-AX): `random.Random(16255)`, 50 000 fuzz inputs +
  14 boundary cases (incl. the empty section).
- `conformance_check.py` (G-CONF): status=skip (conf_skip=true) — the impl
  region's only behavioral op is the A-reference (§3.1), validated by G-AX; the
  input/output legs are identity-level R bijections, so there is no independent
  R/I shadow to differentially test.
