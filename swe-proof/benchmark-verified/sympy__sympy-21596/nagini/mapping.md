# mapping.md — sympy__sympy-21596

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 110997fe18b9f7d5ba7d22f624d156a29bf40759`, states the type
abstraction, and gives the provenance of the deep-model reference (the unchanged
callees the model is validated against by G-AX).

Repo file under change: `sympy/sets/handlers/intersection.py`.

The consumer-visible spec view of `model.py` is an abstract index-filter
contract (a base domain filtered against a "keep" collection and a "drop"
collection). The repo-level meaning of those two collections (imaginary-part
roots / denominator-zero indices) is recorded here for the refinement audit
ONLY — it is NOT part of the spec view.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collect_real_indices(base, keep, drop)` | `intersection_sets(self, other)` for `other == S.Reals` — `sympy/sets/handlers/intersection.py:279` (else branch + denominator step) | the modeled changed function (aggregate view): applies the keep/drop collections per index to the base domain at once |
| `collect_real_indices_two_step(base, keep, drop)` | the TWO `_solution_union` call sites of `intersection_sets(self, other==S.Reals)`: `base_set &= _solution_union(Mul.make_args(numer(im)), n)` (gold `intersection.py:316-317`) then `base_set -= _solution_union(denoms(f), n)` (gold `intersection.py:322`) | the modeled changed function (per-site view): pins WHERE each collection is applied — keep at the intersection `&=` (step 1, `keep_filter`), drop at the difference `-=` (step 2, `drop_filter`) — and the ORDER (keep then drop) |
| `keep_filter(base, keep)` *(deep model — A-reference)* | the imaginary-part intersection `base_set &= _solution_union(Mul.make_args(numer(im)), n)` (gold) | pure spec: step 1 — the subsequence of base whose indices are in the keep collection |
| `drop_filter(seq, drop)` *(deep model — A-reference)* | the denominator difference `base_set -= _solution_union(denoms(f), n)` (gold), applied to the step-1 result | pure spec: step 2 — the subsequence whose indices are NOT in the drop collection |
| `survives(v, keep, drop)` *(deep model — A-reference)* | the changed aggregation `base_set &= _solution_union(numer(im) factors)` then `base_set -= _solution_union(denoms(f) factors)` (gold) | pure spec: an index is retained iff it is in the keep collection and not in the drop collection |
| `kept_seq(base, keep, drop)` *(deep model — A-reference)* | the final `base_set` fed to `imageset(lam, base_set)` (gold, line ~322) | pure spec: the retained subsequence of the base domain, in order |
| `contains(s, v)` | set membership `v in S` for the index sets | pure spec: membership in an index collection |
| `keep` (input) | the per-factor LINEAR roots `xis` of `solve_linear(i,0,[n])` over `i in Mul.make_args(numer(im))` (gold's `_solution_union`) | input: the indices that keep the image real (roots of the imaginary part) |
| `drop` (input) | the integer indices at which any denominator of `f` vanishes — the roots of every factor of `denoms(f)`, linear OR non-linear (gold's `base_set -= _solution_union(denoms(f), n)`, where a non-linear factor contributes a `ConditionSet` removing its integer roots) | input: the indices to exclude (denominator poles) |

The pre-patch repo code the change removes (for the refinement audit, not
referenced from the consumer spec view):
- `x, xis = zip(*[solve_linear(i, 0) for i in Mul.make_args(im) if n in i.free_symbols])`
  then `base_set -= FiniteSet(xis)` (`intersection.py:307-309`) — the buggy
  aggregation that collapses the per-factor roots into one composite tuple key.
- the denominator `for i in denoms(f):` loop with the same collapse
  (`intersection.py:313-321`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an index Set (`S.Integers`, `S.Naturals0`, or a `Complement`/`FiniteSet` thereof) | `List[int]` of candidate indices | membership `k in S` ↔ `contains(ToSeq(base), k)`; the spec/impl are pointwise so a finite candidate window is sound (membership of any index is decided independently) |
| `Union(*[FiniteSet(r) for r ...])` (gold's `_solution_union` over `numer(im)`) | `List[int]` `keep` of the per-factor LINEAR roots | each `FiniteSet(r)` ↔ one element; `Union` membership ↔ `contains(·)` |
| the integer indices killed by `base_set -= _solution_union(denoms(f), n)` | `List[int]` `drop` of every index at which a denominator vanishes | a linear denominator factor contributes its scalar root; a non-linear factor contributes a `ConditionSet` whose integer members are exactly its integer roots — so `drop` is ALL denominator-zero indices, not only the linear-factor roots; membership ↔ `contains(·)` |
| `base_set &= _solution_union(numer(im))` (intersect with keep) | step 1 `keep_filter(base, keep)` (and the `contains(keep, c)` conjunct of `survives`) | set intersection ↔ pointwise membership; the `&=` site is pinned individually as `keep_filter` (`collect_real_indices_two_step`) |
| `base_set -= _solution_union(denoms(f))` (subtract drop) | step 2 `drop_filter(keep_filter(base, keep), drop)` (and the `not contains(drop, c)` conjunct of `survives`) | set difference ↔ pointwise non-membership; the `-=` site is pinned individually as `drop_filter` applied to the step-1 carrier, in the gold's keep-then-drop order |
| `imageset(lam, base_set)` (re-express the surviving indices through `lam`) | the surviving index list; the value `f(k)` is real exactly for the surviving k, and `lam` is injective on the surviving integer indices in all in-scope cases | the surviving INDEX set ↔ the gold's surviving index set is asserted directly at the index level by axiom_check.py (`survives(k) ⇔ k is retained by the real fixed result`); see §3 |

### 2.1 Modeled regime and out-of-scope cases (honest scope statement)

The model covers the regime where the **imaginary-part numerator is a product
of factors each LINEAR in the index** (every factor solvable to a scalar root).
Within that regime:

- The **keep** collection is exactly the per-factor linear roots of `numer(im)`.
- The **drop** collection is ALL integer indices at which any denominator
  vanishes (a non-linear denominator factor such as `n**2-9` removes its
  integer roots via a `ConditionSet`, which the model captures as the
  corresponding `drop` indices). This is what makes the EmptySet case
  (`n/(n**2-9)+…`) come out correct: the index that the imaginary part keeps is
  also a denominator pole, so it is dropped.

OUT OF SCOPE: when a factor of `numer(im)` is **non-linear** (e.g. an
expanded quadratic such as `n**2 - n/2 - 1/2`, or a repeated linear root
`(n-r)**2`), the real result is itself a `ConditionSet`-image rather than a
finite index list, so it is **not** representable as a `List[int]` selection.
`axiom_check.py` detects this regime and reports it as **SKIPPED-OUT-OF-SCOPE**
(it does not silently pass it). Of the seven F2P assertions, exactly one — the
`n/2 + im.expand()*I` case whose imaginary part is a single expanded quadratic —
is out of scope; the model and this bundle make **no** correctness claim about
it. The remaining six F2P assertions are in scope, are checked at the index
level, and still fully discriminate the fixed behaviour from the pre-fix bug
(the issue's `2 in S1.intersect(Reals)` flipping `True→False`).

## 3. Reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `survives` / `kept_seq` deep model ↔ the real fixed `intersect(S.Reals)`
There is **no consumed axiom**. The changed operation (applying the keep/drop
collections to the base domain) is modeled DEEPLY by `survives` / `kept_seq`.
The unchanged callees that produce the two collections are:

- `solve_linear(lhs, rhs=0, symbols=[...])` — `sympy/solvers/solvers.py:1984`.
  Returns `(symbol, solution)` when `lhs-rhs` is linear in `symbol` (the scalar
  root the model consumes into `keep`), else `(numer, denom)` — the non-scalar
  case the model treats as out-of-regime for the imaginary part. The fix passes
  `symbols=[sym]` explicitly (gold).
- `numer(expr)` — `sympy/simplify/radsimp.py:1114` (`fraction(expr)[0]`): the
  numerator of the imaginary part, whose `Mul.make_args` are its factors.
- `Mul.make_args(e)` — `sympy/core/mul.py`: the multiplicative factors of `e`.
- `denoms(eq, *symbols)` — `sympy/solvers/solvers.py:130`: the denominators of
  `eq`; the integer indices at which any of them vanishes are the `drop`
  indices.

These are **unchanged** by the gold patch (the patch only adds
`from sympy.simplify.radsimp import numer` and rewrites the aggregation). The
deep model `survives`/`kept_seq` is validated **== the real fixed behaviour**
out-of-band by axiom_check.py (G-AX): for the in-scope issue/F2P cases and
randomized distinct-linear-factor products, for every base index `k` in a
window it asserts a **full index-level biconditional**

  `survives(k, keep, drop)  ==  gold_keeps(k)`

where `gold_keeps(k)` is "the real fixed `imageset(Lambda(n, f),
base).intersect(S.Reals)` retains index k" (i.e. `f(k)` is finite, real, and a
member of the real result), `keep` is recomputed from the real
`numer`/`Mul.make_args`/`solve_linear([n])`, and `drop` is the set of all
denominator-zero indices from the real `denoms(f)`. The biconditional is checked
in BOTH directions on every window index with **no value-realness mask applied
to only one side** — so an index the model over-keeps whose image is a pole
(`f(k)=zoo`) is caught, not hidden (this is exactly the F2P-7 EmptySet case).
In-container it runs the gold-patched code, so the reference is the fixed
routine. (Run against the buggy base it deliberately FAILS — confirming the
model captures the FIXED semantics, not the bug.)

**Soundness check (G-AX):** `axiom_check.py` imports only `sympy` (the library
under change). It reproduces the keep collection via the real
`numer` / `Mul.make_args` / `solve_linear([sym])` and the drop collection via
the real `denoms`, then asserts the index-level biconditional on the 6 in-scope
boundary cases (the issue example + the five in-scope F2P assertions), reports
the one out-of-scope F2P case (quadratic imaginary part) as SKIPPED, runs 400
randomized distinct-linear-factor imaginary parts over a 25-index window, and
runs 120 repeated-root (non-linear) cases asserting they are correctly flagged
out-of-scope (the regime guard fires honestly rather than passing silently).
A coverage-completeness assertion requires that exactly the documented
out-of-scope F2P case is skipped and all six in-scope ones are checked; it also
re-derives that the in-scope subset still separates the pre-fix collapse
(keeps index 2) from gold (excludes it). Exit 0 iff every obligation holds.

### 3.2 `keep_filter` / `drop_filter` two-step decomposition ↔ the gold's two `_solution_union` call sites
The widened function `collect_real_indices_two_step` is validated against the
gold's two SEPARATE set operations, at the index level, by `check_two_step` in
`axiom_check.py`. It reproduces the gold-added helper `_solution_union(exprs,
sym)` **verbatim** (`sympy/sets/handlers/intersection.py:283-294` post-patch)
and replays the gold's two operations in order:

- step 1 (`base_set &= _solution_union(Mul.make_args(numer(im)), n)`): asserts
  the retained index list of `base_set & keep_solution` equals
  `keep_filter(base_idx, keep)`;
- step 2 (`… -= _solution_union(denoms(f), n)`): asserts the retained index
  list of `(base_set & keep_solution) - drop_solution` equals
  `drop_filter(keep_filter(base_idx, keep), drop)`;
- and that this composition equals the aggregate `kept_seq(base_idx, keep,
  drop)` — a mathematical identity (the two views denote the same retained
  subsequence), confirmed here at the index level against the gold composition.

So the A-reference pins not only the aggregate selection (§3.1) but the
**per-call-site behaviour and the keep-then-drop ORDER** exactly as the gold
patch performs them. `_solution_union` is the only gold-added symbol referenced,
and it is reproduced (not imported) so the check needs only the unchanged
callees `solve_linear` / `numer` / `Mul.make_args` / `denoms`. This runs on
every in-scope F2P + distinct-linear-factor fuzz case (the out-of-scope
non-linear cases return before it). Exit 0 iff every obligation holds.
