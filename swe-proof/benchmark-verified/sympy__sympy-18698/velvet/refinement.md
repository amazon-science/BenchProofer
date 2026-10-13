# refinement.md — sympy__sympy-18698

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`combineByTag` `do` block plus the deep `combineAll`/`combineInto` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are **no A legs** in this bundle: the changed function's new
behavior is modeled deeply over its read-only input list `items`, and the
upstream computation that produces that list is unchanged (mapping.md §3). So
there are no axioms, no `axiom_check.py`, and G-AX is a skip.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed function — `_symbolic_factor_list` (`polytools.py:5898`)

Gold hunk 2 appends, just before `return coeff, factors`:
```python
    if method == 'sqf':
        factors = [(reduce(mul, (f for f, _ in factors if _ == k)), k)
                   for k in set(i for _, i in factors)]
```
i.e. replace the factor list with one entry per distinct multiplicity `k`,
whose factor is the product of every factor that had multiplicity `k`.

| # | Solution.lean impl op (`combineByTag`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `items : List Item` (read-only, not `mut`) | the local `factors` list as built by the unchanged factor-collection loop, just before the grouping tail | R | factor-list ↔ `List Item` via the row bijection `(poly, mult) ↔ (Content, tag)` (mapping.md §2). `items` is read-only: the loop never mutates it (directive 5 — no `mut` on `items`, fresh `result` built). |
| A2 | `let mut result : List Item := []` | the grouping comprehension starts from an empty grouping (each distinct `k` produces one entry; no `k` ⇒ no entries) | I | initialise the tag-keyed accumulator empty. |
| A3 | loop body `result := combineInto result e.1 e.2` for each `e` in `items` order | `reduce(mul, (f for f, _ in factors if _ == k))` per distinct `k` — gathering and multiplying every factor sharing multiplicity `k` | R + I | one tag-keyed combine per factor; `combineInto` = "fresh tag appended in first-encounter order; existing tag has the incoming value multiplied onto its running product (`acc ++ v`)". Performing this for every factor in order yields, per tag, the product of all its factors — exactly the `reduce(mul, …)` per group. The value product `++` ↔ polynomial `*` is **R** (free-monoid bridge, mapping.md §2); the per-step folding control is **I**. |
| A4 | `return result` (= `combineAll items` by the loop invariant) | the comprehension's resulting list `[(product_k, k) for k in set of multiplicities]` | I + R | reading the grouping out in first-encounter tag order ↔ `result`; the `out = combineAll items` postcondition pins the read-out to the tag-keyed product collapse. Order is **not** observable (re-sorted by `_sorted_factors`, mapping.md §3.3), so the set-comprehension's arbitrary order ↔ `out` as a **multiset** (R). |
| A5 | `ensures (out.map Prod.snd).Nodup` | structural consequence of `for k in set(...)`: each multiplicity appears once | I | `set(i for _, i in factors)` has unique elements ⇒ each multiplicity keys exactly one output entry; the deep model proves `combineAll_nodup`. This is the discriminating clause the prepatch violates. |

Discriminating content of the change — two distinct square-free factors that
**share** a multiplicity `k` are reported as **one** combined factor `(f1*f2, k)`
(post-patch) vs **two** separate factors `(f1, k), (f2, k)` (pre-patch). It lives
in `out = combineAll items` together with `(out.map Prod.snd).Nodup`. The
pre-patch skeleton (`Solution_prepatch.lean`) emits every factor raw
(`result := result ++ [e]`, i.e. `out = items`), so for any input with a
repeated multiplicity it has `out ≠ combineAll items` AND
`¬ (out.map Prod.snd).Nodup` — `prove_correct` **fails** (G-DIFF; the verifier
leaves the unprovable goal `items = List.foldl combineStep [] items`). This is
exactly the pre-patch "return the ungrouped `factors` list".

## B. Hunk 1 — the upstream factor-collection loop refactor (`polytools.py:5908`)

| # | Solution.lean | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (none — folded into the read-only input `items`) | rewrite `if arg.is_Mul: args.extend(arg.args); continue` + `if arg.is_Pow:` into `elif arg.is_Pow:` | I | a **pure refactor with no behavioral effect** on the inputs in scope: `Mul.make_args` already returns top-level factors, so the dropped `is_Mul` re-extend branch is dead. **Fuzz-verified inert**: full-patch ≡ grouping-only over 3000 random factor products, 0 differences (mapping.md §3.2). The pre-grouping `factors` list is therefore identical pre/post hunk 1, so it is faithfully the read-only input `items`; nothing about the modeled behavior depends on this hunk. |

## C. The upstream factor-collection loop — no axiom

The `for arg in args:` loop that builds `factors` (`polytools.py:5903-5950`) is
**not changed in behavior** by the patch (only the inert hunk 1 touches it) and
is **not axiomatized**. Its sole role is producing the pre-grouping factor list
that is the read-only input `items`. There is therefore no consumed axiom and no
A-reference deep model of a callee — `combineAll` is a deep model of the
**changed function's own** new grouping behavior, not of a callee.
(mapping.md §3.1.)

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — collapsing the
factor list by multiplicity and multiplying within each group — is modeled
**deeply** by `combineInto`/`combineAll` and the verified `while` loop
(steps A2-A5), not hidden behind any axiom. No row is A. The only non-trivial R
is the free-monoid value bridge (`++` ↔ polynomial `*`), and G-CONF de-interns
through it to compare against the **real** `sqf_list`.

## E. verify(Solution) ⇒ resolved

`combineByTag` verifies only if `out = combineAll items` (A4) and
`(out.map Prod.snd).Nodup` (A5). By R (`(poly, mult) ↔ Item`, factor-list ↔
`List Item`, value product `++` ↔ `*`, mapping.md §2) the verified `out` equals
the post-patch grouped `factors` list on every pre-grouping factor list the
real upstream loop can produce; by G-CONF the R/I transliteration of
`combineAll`/`combineInto` agrees with the **real patched** `sqf_list` factor
multiset over 100006 fuzzed inputs (incl. the issue polynomial's structure),
0 disagreements. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE: F2P `test_factor_terms` plus the added `test_issue_8695`). The single
trust point is refinement fidelity (this doc, G-CONF + G-EQ); there are no
axioms (G-AX skip).
