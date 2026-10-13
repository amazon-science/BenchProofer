# refinement.md — django__django-16255

The operation-by-operation correspondence between `model.py`'s implementation
(the `latest_stamp` impl region, a deep model of the changed reduction over
`List[int]`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The reduction site — `Sitemap.get_latest_lastmod()` (`django/contrib/sitemaps/__init__.py:170`)

Gold hunk:
```
- return max([self.lastmod(item) for item in self.items()])
+ return max([self.lastmod(item) for item in self.items()], default=None)
```

| # | model.py impl op (`latest_stamp`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `stamps: List[int]` | the comprehension `[self.lastmod(item) for item in self.items()]` (a `list` of comparable stamps) | R | a `list` of totally-ordered stamp values ↔ `List[int]` of comparable carriers (mapping.md §2). `self.lastmod`/`self.items()` build this list; they are unchanged and folded into the input — not separate modelled ops. |
| A2 | the loop computing a running maximum seeded with the absent marker `None`, returning `None` for the empty `stamps` and the greatest element otherwise (the deep model `latest_stamp`) | `max([...], default=None)` | A-reference | the changed reduction is modelled **deeply** as a running maximum with a `None` seed. There is **no consumed axiom** — the proof depends on no `@ContractOnly`. The deep model is validated **== the real builtin** out-of-band: G-AX (axiom_check.py) asserts `latest_stamp(values) == max(values, default=None)` over boundary (incl. the empty list) + 50 000 fuzz, and that the empty case yields `None` without raising. `max(L, default=None)` IS exactly "greatest element, else `None`" (mapping.md §3.1). |
| A3 | `result` returned (`Optional[int]`) | the `return` value of `get_latest_lastmod` on the callable-`lastmod` branch | R | `None` ↔ absent marker (no `Last-Modified` header); a stamp `int` ↔ the `max` value. |

The discriminating content of the change — the EMPTY section must report the
absent marker (`None`) rather than failing — lives in the model's clause
`Implies(len(stamps) == 0, Result() is None)`. The pre-patch `max(L)` with no
`default` raises `ValueError` on `L == []`; `model_prepatch.py` reproduces that
absence of an absent-marker fallback (a running maximum with no `None` seed,
returning a concrete stamp on the empty path) and **fails** exactly that clause
(G-DIFF). On the non-empty path the prepatch is identical to the gold (correct
maximum), so the divergence is isolated to the empty section — which is the
real bug.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the `max` reduction acquiring the `default=None` empty-collection
fallback — is modelled **deeply** (the spelled-out running-maximum loop with a
`None` seed in `latest_stamp`, step A2, an **A-reference**), not hidden behind an
axiom about the operation under change. There are **no consumed axioms**
(`model.py`'s `axioms` region is empty): the changed reduction `max(...)` is a
Python builtin modelled deeply and validated against the real builtin by G-AX,
not stood in for by a `@ContractOnly`. The unchanged guards (`hasattr`,
`callable`, the `except TypeError` and non-callable branches) are outside the
modelled scope (mapping.md §1) — the patch does not touch them.

## C. verify(model) ⇒ resolved

`latest_stamp` verifies only if its output is `None` exactly on the empty
section (A2's empty clause) and the greatest collected stamp otherwise (the
membership + dominance clauses). By R (the comprehension's totally-ordered
stamps ↔ `List[int]`, `None` ↔ absent marker) the verified function equals
`max([self.lastmod(item) for item in self.items()], default=None)` on the tested
inputs; by G-AX the deep model `latest_stamp` equals the real builtin
`max(values, default=None)` (the A-reference) including the empty case.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited builtin reference — and the gold
patch resolves (G-RESOLVE: the F2P `test_callable_sitemod_no_items` now sees no
`Last-Modified` header for a section with no items, instead of a `ValueError`).
The single trust point is refinement fidelity (this document, G-EQ) plus the
G-AX builtin-equality check; there is no axiom-soundness trust point because no
axiom is consumed.
