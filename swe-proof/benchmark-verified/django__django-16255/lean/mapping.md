# mapping.md — django__django-16255

## Instance
- repo: django/django
- base_commit: 444b6da7cc229a58a2c476a52e45233001dc7073
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`Sitemap.get_latest_lastmod` (django/contrib/sitemaps/__init__.py:165) reports the
single "latest timestamp" of a sitemap. Its three branches are:

```python
def get_latest_lastmod(self):
    if not hasattr(self, "lastmod"):
        return None
    if callable(self.lastmod):
        try:
            return max([self.lastmod(item) for item in self.items()])   # base_commit
        except TypeError:
            return None
    else:
        return self.lastmod
```

When `lastmod` is a per-item callable AND the item collection is EMPTY, the list
comprehension `[self.lastmod(item) for item in self.items()]` is `[]`, and
`max([])` raises `ValueError: max() arg is an empty sequence`. That exception is
NOT caught by the surrounding `except TypeError`, so `get_latest_lastmod` crashes
(the traceback in the problem statement). The fix supplies a default for the empty
case:

```python
-            return max([self.lastmod(item) for item in self.items()])
+            return max([self.lastmod(item) for item in self.items()], default=None)
```

so an empty collection yields `None` (no latest timestamp) instead of raising.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_latestLastmod` | `Sitemap.get_latest_lastmod` (django/contrib/sitemaps/__init__.py:165) |
| `problem_spec_latestLastmod`   | the post-condition this method must satisfy |
| `List.max?` (builtin)          | `max(<list>, default=None)` — the patched call (empty ⇒ `none`/`None`) |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `hasM : Bool` | `hasattr(self, "lastmod")` | whether a timestamp source is defined at all |
| `callM : Bool` | `callable(self.lastmod)` | whether the timestamp is computed per item |
| `vals : List Int` | `[self.lastmod(item) for item in self.items()]` | the per-item timestamps; a date is modeled as a comparable `Int` (ordinal). `[] ↔` empty collection |
| `fixedM : Option Int` | `self.lastmod` when NOT callable | a fixed timestamp attribute: `some d ↔` a date, `none ↔` `None` |
| result `: Option (Option Int)` | observable outcome | outer: `none ↔` the method raised; `some v ↔` it returned. inner `Option Int`: `none ↔` returned Python `None` ("no latest timestamp"), `some d ↔` returned a date |

`date ↔ Int`: the only operation the method performs on a timestamp is the order
comparison inside `max`. Dates are totally ordered; an order-isomorphic `Int`
ordinal is the faithful carrier (DECISIONS.md: model order-only values exactly,
not as `Float`). `Option Int` carries the `None`-or-date possibility.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The reported behavior is a
  pure decision over `(hasattr, callable, the per-item timestamp list, the fixed
  timestamp)`. `self.items()` and `self.lastmod(item)` are abstracted to their
  result — the list `vals` of per-item timestamps — and supplied as the input
  carrier (G-CONF drives the real method, which calls the real `items()`/
  `lastmod`). `axiom_check.py` is a skip stub.
- The unchanged `except TypeError` guard catches the case where the per-item
  timestamps are mutually incomparable (a heterogeneous list). It is present both
  pre- and post-patch and is out of the modeled domain: `vals : List Int` is
  homogeneous and totally ordered, so the `TypeError` path is never reached. The
  MODELED change is strictly the empty-collection (`ValueError`) case.
- Flag dependency: the empty-collection comparison is reached only when
  `hasattr(self, "lastmod")` is true AND `self.lastmod` is callable. G-CONF fuzzes
  all of `(hasM, callM, vals∈{[]}∪nonempty, fixedM)`.

## G-CONF fuzz seed
- pinned seed: `16255`
- ≥10^5 fuzzed `(hasM, callM, vals, fixedM)` tuples, `vals` drawn from `[]` plus
  random nonempty lists of ordinal-dates `0..N`, exercising the empty-collection
  boundary (callM=true, vals=[]) that triggered the crash.
