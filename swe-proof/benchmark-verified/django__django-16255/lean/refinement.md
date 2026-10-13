# refinement.md — django__django-16255

Maps every operation in `implementation_latestLastmod` to its `patch.diff`
counterpart in `Sitemap.get_latest_lastmod` (django/contrib/sitemaps/__init__.py:165).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** op left as the real repo callee in G-CONF, **I** identical
concrete op.

## Patch (post-patch method)
```python
def get_latest_lastmod(self):
    if not hasattr(self, "lastmod"):
        return None
    if callable(self.lastmod):
        try:
            return max([self.lastmod(item) for item in self.items()], default=None)
        except TypeError:
            return None
    else:
        return self.lastmod
```

The single changed token is the `, default=None` added to the `max(...)` call.
Everything else (the `hasattr` guard, the `callable` branch, the `else` fixed-value
branch, the `except TypeError` guard) is unchanged.

## Modeling decision
The observable behavior is: what does `get_latest_lastmod` return (and does it
raise)? We model the outcome as `Option (Option Int)`:
- outer `none` ↔ the method raised (the `ValueError` from `max([])`);
- outer `some v` ↔ it returned, where `v : Option Int` is the returned optional
  timestamp (`none ↔` Python `None` = "no latest timestamp"; `some d ↔` a date).

The decision is a pure function of `(hasM, callM, vals, fixedM)` where `vals` is
the list of per-item timestamps `[self.lastmod(item) for item in self.items()]`.
A timestamp/date is modeled as a comparable `Int` ordinal — `max` performs only
the order comparison, and dates are totally ordered (DECISIONS.md: order-only
values are modeled exactly, not as `Float`). `max(vals, default=None)` is exactly
Lean's `List.max?`: `none` for the empty list, `some (greatest)` otherwise.

The unchanged `except TypeError` path (heterogeneous, incomparable timestamps) is
out of the modeled domain: `vals : List Int` is homogeneous and totally ordered,
so that path is unreachable. The MODELED change is strictly the empty-collection
(`ValueError`) case the patch fixes.

## Operation correspondence
| # | Lean op (`implementation_latestLastmod`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if hasM = false then return some none` | `if not hasattr(self, "lastmod"): return None` | I | `hasattr ↔ hasM : Bool`; returns "no latest timestamp" |
| 2 | `if callM then …` | `if callable(self.lastmod):` | I | `callable ↔ callM : Bool`; selects the per-item branch |
| 3 | `return some vals.max?` | `return max([self.lastmod(item) for item in self.items()], default=None)` | R | `[self.lastmod(item) …] ↔ vals : List Int` (date↔Int ordinal); `max(…, default=None) ↔ List.max?` (empty ⇒ `none`, no raise). This is the FIXED token. |
| 4 | `else return some fixedM` | `else: return self.lastmod` | R | `self.lastmod ↔ fixedM : Option Int` (a fixed timestamp; `None ↔ none`) |
| 5 | (outer `some _` on every path) | the method completes; never raises in-domain | I | total outcome (`some _`) — the post-patch method does not raise for `vals : List Int` |

## R/I legs ⇒ G-CONF
Op 3 (the empty-safe greatest-of-list, R) is the modeled change; op 4 (fixed-value
type refinement, R) and ops 1,2,5 (I) are the unchanged framing. `conf_skip =
false`: the impl region is genuine R/I content. `conformance_check.py` builds the
R/I shadow (the full report decision) and differential-tests it against the REAL
patched `Sitemap.get_latest_lastmod` — driving live sitemap objects with varied
`(hasattr, callable, items(), lastmod)` configurations, observing both whether it
raised and the returned value — over ≥10^5 fuzzed inputs.

## No A-consumed / A-reference row
`get_latest_lastmod` calls no unchanged callee that needs a property: it is a pure
decision plus a greatest-element selection. `self.items()` and `self.lastmod(item)`
are abstracted to their result (the list `vals`), supplied as the input carrier;
they are not axiomatized, not modeled. So `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## F2P alignment
`test_callable_sitemod_no_items` builds a sitemap with a per-item callable
`lastmod` and `items()` returning `[]`, and requests the sitemap index — which
calls `get_latest_lastmod()`. Pre-patch, `max([])` raises `ValueError` (uncaught
by `except TypeError`), so the index view 500s — modeled as the prepatch impl
returning outer `none`, which violates the spec's TOTAL `result = some _` clause
(the discriminating clause). The fixed impl returns `some none` ("no latest
timestamp" ⇒ no `Last-Modified` header), satisfying the spec. `patch.diff` (gold
verbatim) makes the harness resolve.
