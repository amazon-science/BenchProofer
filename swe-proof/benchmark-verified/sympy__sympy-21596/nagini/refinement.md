# refinement.md — sympy__sympy-21596

The operation-by-operation correspondence between `model.py`'s implementation
(the `collect_real_indices` impl region plus the deep `survives` / `kept_seq`
model in the `pure` region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**, the
proof uses the axiom's `Ensures`, or **A-reference**, a deep model validated
== the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the in-scope tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` — confirmed — and is the real correctness oracle, G-RESOLVE).

## A. What the fix changes

The function under change is `intersection_sets(self, other)` for
`self : ImageSet`, `other == S.Reals` (`sympy/sets/handlers/intersection.py`,
the `if other == S.Reals:` branch). For an image set `imageset(Lambda(n, f),
base)` it forms the real values: an index `n` contributes a real value iff the
imaginary part `im(n)` vanishes, and `n` must be discarded where a denominator
of `f` vanishes.

Gold replaces a buggy aggregation with a helper `_solution_union(exprs, sym)`
and two uses of it:

```
# imaginary-part vanishing (the else branch):
- x, xis = zip(*[solve_linear(i, 0) for i in Mul.make_args(im) if n in i.free_symbols])
- if x and all(i == n for i in x):
-     base_set -= FiniteSet(xis)            # removes ONE composite tuple key
- else:
-     base_set -= ConditionSet(n, Eq(im, 0), S.Integers)
+ base_set &= _solution_union(Mul.make_args(numer(im)), n)   # keep vanishing indices

# denominator exclusion:
- for i in denoms(f): ... base_set -= FiniteSet(xis) / ConditionSet ...
+ base_set -= _solution_union(denoms(f), n)                  # drop forbidden indices
```

where
```
def _solution_union(exprs, sym):
    sols = []
    for i in exprs:
        x, xis = solve_linear(i, 0, [sym])
        if x == sym: sols.append(FiniteSet(xis))      # this factor's single root
        else:        sols.append(ConditionSet(sym, Eq(i, 0)))  # its (integer) roots
    return Union(*sols)
```

The bug: `zip(*[...])` collapses the per-factor roots `[(n,-1),(n,1)]` into
`x=(n,n)`, `xis=(-1,1)`, so `base_set -= FiniteSet((-1,1))` removes a single
**2-tuple** from the integer domain — which equals no integer — leaving the
imaginary-part filter a no-op (e.g. `2 in S1.intersect(Reals)` wrongly `True`;
result `Complement(Integers, FiniteSet((-1,1)))` instead of `FiniteSet(-1,1)`).
The fix solves each factor separately, takes the **Union** of the individual
roots, and **intersects** the base with it (and **subtracts** the denominator
roots) — so each index is tested individually. (All confirmed by direct
execution at `base_commit` and post-gold.)

## B. model.py impl ↔ patch.diff operation map

| # | model.py op (`collect_real_indices` / pure region) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `base : List[int]` (candidate indices of the domain) | `base_set` (`S.Integers` / `S.Naturals0`, a domain of indices) | R | a Set of indices ↔ `List[int]` of candidate indices; membership of `k` ↔ `contains(ToSeq(base), k)` (mapping.md §2). Pointwise membership is sound because the spec/impl are pointwise. |
| A2 | `keep : List[int]` — the indices kept by the imaginary-part condition | the scalars `xis` produced by `solve_linear(i,0,[sym])` for `i in Mul.make_args(numer(im))`, gathered by `_solution_union` into `Union(*[FiniteSet(xis)])` | R + A-reference | each factor's `FiniteSet(xis)` ↔ one element of `keep`; the `Union` of singletons ↔ the set whose membership is `contains(keep, ·)`. `solve_linear`/`numer`/`Mul.make_args` are UNCHANGED callees producing these roots — taken as model input; their root-production is validated by axiom_check.py. **In the modeled all-linear regime** (§D). |
| A3 | `drop : List[int]` — the indices excluded as denominator poles | the indices killed by `base_set -= _solution_union(denoms(f), n)` (each denominator factor's roots — a linear factor's scalar root, a non-linear factor's `ConditionSet` integer roots) | R + A-reference | `drop` ↔ ALL denominator-zero indices, linear OR non-linear; `Union` of the per-factor solution sets ↔ `contains(drop, ·)`. axiom_check.py computes `drop` as every index at which a real `denoms(f)` factor vanishes, so the non-linear-denominator case (`n**2-9`) is covered. |
| A4 | `survives(c, keep, drop) == contains(keep,c) and not contains(drop,c)` | `base_set &= _solution_union(numer(im) factors)` **then** `base_set -= _solution_union(denoms(f) factors)` | A-reference | the CHANGED aggregation, modelled **deeply**: intersect-with-keep (`&=`) is `contains(keep,·)`; subtract-drop (`-=`) is `not contains(drop,·)`. There is no consumed `intersection` axiom; the deep model is validated against the real fixed result by a full **index-level biconditional** `survives(k,keep,drop) ⇔ (the real fixed result retains index k)` in axiom_check.py / G-AX, checked in both directions with no value-realness mask. |
| A5 | the backward loop building `result` = retained subsequence of `base`; `ToSeq(result) == kept_seq(...)` | `imageset(lam, base_set)` over the final `base_set` | R + I | the resulting set of retained indices ↔ `kept_seq` (front-recursive filter). `imageset(lam, ·)` re-expresses the retained indices through the unchanged map `lam`. The correspondence is asserted at the **INDEX level**: axiom_check.py checks that the model's retained index list equals the gold's retained index list (the indices whose image lands in the real result), so the claim is "same indices kept", NOT a value-membership proxy. In every in-scope case `lam` is injective on the retained integer indices, so the retained-index set and the gold image-value set are in bijection. |

### B.1 The two `_solution_union` call sites, modeled individually (`collect_real_indices_two_step`)

`collect_real_indices` above pins the *aggregate* per-index selection (both
collections at once, via `survives`/`kept_seq`). The second modeled function
`collect_real_indices_two_step` pins the *concrete two-site application* — WHERE
and in what ORDER each collection is applied — exactly as the gold patch does:
first `base_set &= _solution_union(Mul.make_args(numer(im)), n)` (the
imaginary-part intersection), then `base_set -= _solution_union(denoms(f), n)`
(the denominator difference).

| # | model.py op (`collect_real_indices_two_step` / pure region) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | step-1 loop building `kept` = `keep_filter(ToSeq(base), ToSeq(keep))` (front-recursive filter keeping only indices in `keep`) | `base_set &= _solution_union(Mul.make_args(numer(im)), n)` (the imaginary-part **intersection** `&=`) — gold `intersection.py:316-317` | R + A-reference | intersection with the keep-roots ↔ `keep_filter` (the `contains(keep, ·)` step). axiom_check.py recomputes `base_set & _solution_union(numer(im) factors)` with the real gold helper and asserts its retained index list equals `keep_filter(base_idx, keep)` (index-level, both directions). |
| B2 | step-2 loop building `result` = `drop_filter(kept, ToSeq(drop))` applied to the step-1 result (front-recursive filter removing indices in `drop`) | `base_set -= _solution_union(denoms(f), n)` (the denominator **difference** `-=`) — gold `intersection.py:322` | R + A-reference | difference with the denominator-roots ↔ `drop_filter` (the `not contains(drop, ·)` step), applied to the step-1 carrier. axiom_check.py recomputes `(base_set & keep_solution) - drop_solution` with the real gold helper and asserts its retained index list equals `drop_filter(keep_filter(base_idx, keep), drop)`. The ORDER (keep then drop) matches the gold. |
| B3 | `Ensures(ToSeq(Result()) == drop_filter(keep_filter(ToSeq(base), ToSeq(keep)), ToSeq(drop)))` | the two `&=`/`-=` operations compose to the final `base_set` fed to `imageset(lam, ·)` | I + R | the result is pinned to the exact ordered composition of the two per-site filters (keep at the `&=`, drop at the `-=`), which is what the gold's two operations produce. The single postcondition fully determines the output structurally over the input carriers; it is established directly from the two-loop invariants (B1, B2) with no auxiliary induction. |

The two-step postcondition `drop_filter(keep_filter(base,keep),drop)` and the
aggregate `kept_seq(base,keep,drop)` (the postcondition of
`collect_real_indices`, A4) are two descriptions of the same retained
subsequence, so they denote the same value; the spec pins the behaviour through
whichever view each function uses (per-site composition here, aggregate there).
That the two views coincide is a mathematical identity — not needed to pin the
behaviour (each postcondition already does), and confirmed out-of-band at the
index level against the gold composition by `axiom_check.py` (`check_two_step`).

## C. The discriminating clause (G-DIFF)

`model_prepatch.py` keeps the byte-identical spec but its impl reproduces the
pre-fix aggregation in **both** modeled functions (two complementary witnesses):

- `collect_real_indices`: the keep collection is collapsed into one composite
  key that matches no individual index, so the keep test is a no-op and
  `survives` degrades to `not contains(drop, c)` (keep every index outside the
  drop collection). It **fails** the postcondition / loop invariant
  `ToSeq(result) == kept_seq(ToSeq(base), ToSeq(keep), ToSeq(drop))`, because a
  base index not in the drop collection but also not in the keep collection
  (e.g. the index `2` in the issue) is wrongly kept. This is exactly the spec
  sensing the bug (the issue's `2 in S1.intersect(Reals)` going `True`→`False`).
- `collect_real_indices_two_step`: the **difference** step (step 2, `base_set
  -=`) is collapsed into a no-op — every index that survived the intersection
  step is kept unconditionally, never tested against the drop collection. It
  **fails** the postcondition `ToSeq(Result()) == drop_filter(keep_filter(
  ToSeq(base), ToSeq(keep)), ToSeq(drop))`, because an index in BOTH `keep` and
  `drop` (e.g. F2P-7's pole index `3` in `n/(n**2-9)+…`, which gold removes via
  `base_set -= …` to give `EmptySet`) survives the collapsed step. This witnesses
  that the spec senses the denominator step specifically, at its own call site.

## D. No kind-3 (unexpressible-changed-op) steps; modeled regime

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — applying the keep/drop collections to the base domain
(`zip`-collapse-then-subtract-a-tuple ⟶ per-index intersect-with-keep then
subtract-drop) — is modelled **deeply** in two complementary ways: as the
aggregate per-index selection (`survives` / `kept_seq`, `collect_real_indices`)
and as the two ordered per-site filters (`keep_filter` then `drop_filter`,
`collect_real_indices_two_step`); the two views denote the same retained
subsequence (a mathematical identity, confirmed at the index level by
axiom_check.py). Neither is hidden behind an axiom about the function under
change. There is **no consumed `@ContractOnly` axiom**. The
unchanged callees (`solve_linear`, `numer`, `Mul.make_args`, `denoms`) and the
gold-added `_solution_union` helper appear only as the **A-reference** that
axiom_check.py validates the deep model against: the two-step decomposition
(B1, B2, B3) is checked at the index level against the gold's actual
`&=`-then-`-=` step ordering, recomputed with the real gold helper.

**Modeled regime (honest scope).** The model covers the regime where the
imaginary-part numerator is a product of factors each LINEAR in the index. In
this regime `keep` is exactly the per-factor scalar roots and `drop` is all
denominator-zero indices, and the index-level biconditional holds (G-AX).
OUT OF SCOPE: when a factor of `numer(im)` is non-linear (an expanded quadratic
or a repeated linear root), the real result is a `ConditionSet`-image not a
finite index list; such an input is **not** modeled and `axiom_check.py` flags
it SKIPPED-OUT-OF-SCOPE rather than passing it. Of the seven F2P assertions,
exactly one (`n/2 + im.expand()*I`, a single expanded-quadratic imaginary part)
is out of scope; the bundle makes no correctness claim about it. The remaining
six in-scope F2P assertions — including the non-linear-DENOMINATOR EmptySet case
`n/(n**2-9)+…` (which is in scope because its *imaginary part* is linear; only
its denominator is non-linear, and `drop` covers non-linear denominators) — are
checked at the index level and still fully discriminate the bug.

## E. verify(model) ⇒ resolved

`collect_real_indices` verifies only if its result equals exactly the retained
subsequence `kept_seq(base, keep, drop)` — i.e. only if each base index is kept
iff it is in `keep` (A4) and not in `drop` (A4). `collect_real_indices_two_step`
verifies only if step 1 equals `keep_filter` (the `&=` site, B1) and the final
result equals `drop_filter` over it (the `-=` site, B2), i.e. only if the result
is the exact ordered composition `drop_filter(keep_filter(·))` (B3). So the spec
pins BOTH the aggregate selection (`collect_real_indices`) AND the per-call-site
application and ordering (`collect_real_indices_two_step`). By R (Set-of-indices ↔ `List[int]`, pointwise membership) and
A-reference (the `keep` indices are what `solve_linear` over `numer(im)`
produces, `drop` is ALL denominator-zero indices from `denoms(f)`, the deep
aggregation == the real `&=`/`-=` over `_solution_union`, AND the two-step
decomposition matches the gold's actual `&=`-then-`-=` ordering — all validated
by an index-level biconditional / decomposition check in G-AX), the verified
selection equals the gold patch's `base_set` on every in-scope tested input;
`imageset` over it reproduces the real result (the retained indices are in
bijection with the gold image values, `lam` being injective on the retained
integer indices). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited references on the
in-scope inputs — and the gold patch resolves all seven F2P assertions
(G-RESOLVE), the one out-of-scope assertion included (it is unaffected by any
verifying refinement because the model makes no claim there; the SHIPPED patch
is the gold patch verbatim and resolves it). The trust points are the two of
PLAN §1.1: A-reference soundness (G-AX, now an honest index-level biconditional)
and refinement fidelity (this document, G-EQ).
