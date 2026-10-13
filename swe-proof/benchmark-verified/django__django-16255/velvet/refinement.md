# refinement.md — django__django-16255

The operation-by-operation correspondence between `Solution.lean`'s `latestLastmod`
impl region (a deep model of the changed reduction over `List Int`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type-only refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (a deep model validated `== the real callee` by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviorally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so the backward
`while` fold carries a `decreasing i` measure and a verifying implementation
must TERMINATE and return `latestStamp stamps`. (An earlier revision used
partial correctness, which a same-spec diverging implementation — an infinite
loop with a trivial invariant — vacuously satisfied; the G-PANEL-1 audit found
that counterexample, and total semantics excludes the whole class. The real
`get_latest_lastmod` reduction trivially terminates: `max(...)` over the
finite comprehension `[self.lastmod(item) for item in self.items()]` is a
bounded fold that always returns.)

## A. The reduction site — `Sitemap.get_latest_lastmod()` (`django/contrib/sitemaps/__init__.py:170`)

Gold hunk:
```
- return max([self.lastmod(item) for item in self.items()])
+ return max([self.lastmod(item) for item in self.items()], default=None)
```

| # | Solution.lean impl op (`latestLastmod`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `stamps : List Int` | the comprehension `[self.lastmod(item) for item in self.items()]` (a `list` of comparable stamps) | R | a `list` of totally-ordered stamp values ↔ `List Int` of comparable carriers (mapping.md §2). `self.lastmod`/`self.items()` build this list; they are unchanged and folded into the input — not separate modeled ops. |
| A2 | the `while` loop computing a running maximum seeded with the absent marker `none`, returning `none` for empty `stamps` and the greatest element otherwise (the deep model `latestStamp`, established by the loop invariant `result = latestStamp (stamps.drop i)` + the `latestStamp_drop_step` fold lemma) | `max([...], default=None)` | A-reference | the changed reduction is modeled **deeply** as a running maximum with a `none` seed. There is **no consumed axiom** — the proof depends on no `axiom`/`opaque` callee. The deep model is validated **== the real builtin** out-of-band: G-AX (axiom_check.py) asserts `latestStamp(values) == max(values, default=None)` over boundary (incl. the empty list) + 50 000 fuzz, and that the empty case yields `None` without raising. `max(L, default=None)` IS exactly "greatest element, else `None`" (mapping.md §3.1). |
| A3 | `result` returned (`Option Int`) | the `return` value of `get_latest_lastmod` on the callable-`lastmod` branch | R | `none` ↔ absent marker (no `Last-Modified` header); `some v` (a stamp `Int`) ↔ the `max` value. |

The discriminating content of the change — the EMPTY section must report the
absent marker (`none`) rather than failing — lives in the spec clauses
`ensures stamps.length = 0 → out = none` and `ensures out = latestStamp stamps`
(with `latestStamp [] = none`). The pre-patch `max(L)` with no `default` raises
`ValueError` on `L == []`; `Solution_prepatch.lean` reproduces that absence of an
absent-marker fallback (the running maximum is seeded with a concrete stamp
`some 0` instead of `none`, so the empty path reports a concrete stamp) and
**fails** exactly that clause: the loop-invariant-initialization obligation
`some 0 = latestStamp (stamps.drop stamps.length)` reduces to `some 0 = none`,
which is unprovable (G-DIFF). On the non-empty path the prepatch is identical to
the gold (correct maximum), so the divergence is isolated to the empty section —
which is the real bug.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely
*changed* — the `max` reduction acquiring the `default=None` empty-collection
fallback — is modeled **deeply** (the spelled-out front-recursive running-maximum
`latestStamp` with a `none` base case, driven by the backward `while` loop, step
A2, an **A-reference**), not hidden behind an axiom about the operation under
change. There are **no consumed axioms** (`Solution.lean`'s `axioms` region is
empty): the changed reduction `max(...)` is a Python builtin modeled deeply and
validated against the real builtin by G-AX, not stood in for by an `axiom`/
`opaque`. The unchanged guards (`hasattr`, `callable`, the `except TypeError`
and non-callable branches) are outside the modeled scope (mapping.md §1) — the
patch does not touch them.

## C. verify(Solution.lean) ⇒ resolved

`latestLastmod` verifies only if its output is `none` exactly on the empty
section (the `latestStamp [] = none` / `stamps.length = 0 → out = none` clauses)
and the greatest collected stamp otherwise (the membership clause
`∀ v, out = some v → ∃ k, k < stamps.length ∧ stamps[k]! = v` and the dominance
clause `∀ k, k < stamps.length → ∃ v, out = some v ∧ stamps[k]! ≤ v`). By R (the
comprehension's totally-ordered stamps ↔ `List Int`, `none` ↔ absent marker) the
verified function equals `max([self.lastmod(item) for item in self.items()],
default=None)` on the tested inputs; by G-AX the deep model `latestStamp` equals
the real builtin `max(values, default=None)` (the A-reference) including the
empty case. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited builtin reference — and the
gold patch resolves (G-RESOLVE: the F2P `test_callable_sitemod_no_items` now sees
no `Last-Modified` header for a section with no items, instead of a
`ValueError`). The single trust point is refinement fidelity (this document,
G-EQ) plus the G-AX builtin-equality check; there is no axiom-soundness trust
point because no axiom is consumed.
