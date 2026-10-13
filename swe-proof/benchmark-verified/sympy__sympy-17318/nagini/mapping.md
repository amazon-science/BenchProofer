# mapping.md — sympy__sympy-17318

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d4e0231b08147337745dcf601e62de7eefe2fb2d`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo files under change: `sympy/simplify/sqrtdenest.py` (the behavioural fix)
and `sympy/simplify/radsimp.py` (docstring-only clarification of the two
helpers' positive-rational domain).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `match_additive(codes)` | `_sqrt_match(p)`, the `p.is_Add` branch — `sympy/simplify/sqrtdenest.py:140` (changed guard at body line 159) | the modeled changed function (additive-expression matcher); the guard that decides whether to use the fast splitting helper |
| `split_by_radicand_gcd(codes, k)` *(axiom — A-consumed)* | `split_surds(expr)` — `sympy/simplify/radsimp.py:1062` (calls `_split_gcd(*surds)` at line 1080; `_split_gcd` indexes `a[0]` at line 1116) | unchanged helper the matcher *calls* on the fast path; meaningful only for a sum of square-root terms whose squares are positive rationals |
| `all_fast_facet(s)` (facet E = fast-path eligible) | the post-patch guard predicate `all(sq.is_Rational and sq.is_positive for sq in sqargs)` over `sqargs = [x**2 for x in pargs]` (`sqrtdenest.py:159-160` post-patch) | pure spec: every addend is fast-path eligible. The eligibility facet E is the real criterion "the addend's square is a positive rational"; the model-symbol name is kept abstract (no positivity wording) because that diagnosis is hints_text-only and would leak in the consumer spec view (SPEC_GUIDE §6). |
| `num_surds(s)` | `len(surds)` inside `split_surds`, where `surds = [x[1]**2 for x in coeff_muls if x[1].is_Pow]` (`radsimp.py:1078`) | pure spec: how many addends are square-root terms |
| `any_has_depth(s)` (facet N = carries a nested radical) | `nmax[0] != 0`, the maximal `sqrt_depth` over the addends in the depth-based fallback (`sqrtdenest.py:166-168`) | pure spec: some addend carries a nested square root |
| `code_fast_facet / code_is_surd / code_has_depth` | the per-addend facet tests `(x**2).is_Rational`, `(x**2).is_positive`, `x[1].is_Pow`, `sqrt_depth(x) >= 1` | pure spec: the per-addend predicates the folds reduce. `code_fast_facet` = facet E (the conjunction `(x**2).is_Rational and (x**2).is_positive`); `code_has_depth` = facet N. |
| `NoMatch` (exception) | the empty list `[]` returned by `_sqrt_match` when `nmax[0] == 0` (`sqrtdenest.py:169`) and at the trailing `return list(res)` for a non-matching shape (`sqrtdenest.py:215`) | the "no match" result; an exception stands in for the empty list (a builtin exception in `Exsures` crashes the translator, SPEC_GUIDE §2) |

The pre-patch guard the change replaces (for the refinement audit, not
referenced from the consumer spec view): `if all((x**2).is_Rational for x in
pargs):` (`sqrtdenest.py:159`). It tests rationality of the square only, NOT its
sign, so an imaginary addend (square a negative rational) passes and the helper
is invoked on a sum with no square-root term → `_split_gcd()` is handed an empty
tuple → `a[0]` raises `IndexError`.

The `radsimp.py` hunk of the gold patch is a **docstring-only** change
(`rad_rationalize` and `split_surds`: "rationals" → "positive rationals"); it
alters no executable behaviour and so is not modeled — it merely documents the
precondition the `split_by_radicand_gcd` axiom encodes. (refinement.md §C.)

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a sorted list of addends `pargs` of a SymPy `Add` | `List[int]` of per-addend category codes (`0..3`) | addend `x` ↔ `codes[k]`, where the code records only the two facets that decide the branch: whether `(x**2)` is a positive rational and whether `sqrt_depth(x) >= 1` (see §3 for the code table). `len(pargs)` ↔ `len(codes)`. |
| addend-list value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(codes)` materializes the list as a `PSeq`; the per-element predicates are folded front-recursively (`all_fast_facet`, `num_surds`, `any_has_depth`) so a single unfold is available per loop step. |
| the matched triple `[a, b, r]` / the empty list `[]` | a path-distinguishing `int` outcome: on the fast path the result is exactly the splitting helper's output `split_by_radicand_gcd(codes, num_surds(codes))` (an OPAQUE value, only constrained to be `!= 1`); on the depth path the match marker **1** / the `NoMatch` exception | the F2P observes *match vs. no-match* (`_sqrt_match(4 + I) == []`) and *no IndexError*; the PASS_TO_PASS observe *which mechanism produced the match* (`test_sqrtdenest2/3` exercise the fast-path split, distinct from depth-fallback matches), so the result distinguishes the two success paths. Crucially the fast-path result is GROUNDED in the modeled computation: the postcondition pins it equal to the helper's *output*, and that value is opaque (unpinned), so a wrong impl cannot satisfy the clause with a fabricated literal — it must actually invoke the helper (2nd-pass fix of the re-audit's residual hole, where the previous `Result()==2` could be echoed by a literal `return 2`). The concrete triple *contents* `(a,b,r)` are still not pinned — only the producing mechanism and the helper's exact (opaque) output are. |
| `(x**2).is_Rational`, `(x**2).is_positive`, `x[1].is_Pow`/`sqrt_depth(x)>=1` | the boolean facets packed into the code (§3) | each is a SymPy three-valued assumption query coerced to a definite bool for the concrete numeric addends the tests exercise (`bool(...)`). |

SymPy objects cannot be indexed in Nagini specs, so each addend is abstracted to
the integer code carrying exactly the facets the guard reads.

## 3. The addend code table and the guard

Each addend `x` is abstracted to one of four codes over `(positive-rational
square?, nested square root?)`:

| code | `(x**2).is_Rational ∧ is_positive` | `sqrt_depth(x) >= 1` | example | `is_surd` (in `split_surds`) |
|---|---|---|---|---|
| 0 | yes | no | a rational `4`, `5/3` | no |
| 1 | yes | yes | a real surd `sqrt(2)`, `3*sqrt(5)` | **yes** |
| 2 | no (rational but ≤ 0, or non-rational shallow) | no | imaginary `I` (square `-1`) | no |
| 3 | no | yes | a nested non-positive square | no |

- **Fast path taken** ⟺ every code ∈ {0, 1} ⟺ `all_fast_facet` (facet E on
  every addend; the underlying repo criterion is "the square is a positive
  rational").
- **`num_surds`** = count of code-1 addends = `len(surds)` in `split_surds`.
- **`any_has_depth`** ⟺ some code ∈ {1, 3} ⟺ the depth-based fallback finds a
  nesting (facet N).

**Frame fact (model precondition `all_fast_facet ⇒ num_surds ≥ 1`).** A genuine
multi-term `Add` (`len(pargs) >= 2`) whose addends *all* square to positive
rationals must contain at least one irrational square-root term: a sum of only
rationals would auto-evaluate to a single `Number` and never reach the
`p.is_Add` branch. Hence on the fast path `surds` is non-empty and `_split_gcd`
is never handed an empty tuple. This is the property whose ABSENCE on the
imaginary input (`4 + I`: codes `[0, 2]`, all squares rational, none positive
beyond the `4`, zero surds) is the root cause of the `IndexError`. Validated on
the real `Add` by axiom_check.py.

## 4. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 4.1 `split_by_radicand_gcd` ↔ `split_surds` (A-consumed)
**Callee:** `sympy.simplify.radsimp.split_surds(expr)` (`radsimp.py:1062`),
unchanged by the behavioural fix. It collects the radicands of the square-root
addends (`surds = [x[1]**2 for x in coeff_muls if x[1].is_Pow]`,
`radsimp.py:1078`), then calls `_split_gcd(*surds)` (`radsimp.py:1080`).
`_split_gcd` reads `g = a[0]` (`radsimp.py:1116`) — so an empty `surds` list
raises `IndexError`.

The axiom encodes the WEAKEST contract the proof needs:

  - `Requires(all_fast_facet(codes))` — every addend is fast-path eligible
    (facet E; the real criterion is "the addend's square is a positive
    rational", the post-patch guard / the helper's intended domain, now
    documented in its docstring by the gold patch);
  - `Requires(k == num_surds(codes))` and `Requires(k >= 1)` — the sum contains
    at least one square-root term, so `surds` is non-empty and `_split_gcd`
    does not index an empty tuple;
  - `Ensures(Result() != 1)` — under those preconditions `split_surds` RETURNS
    NORMALLY (no `IndexError`), yielding a match, abstracted to an OPAQUE SPLIT
    outcome constrained only to differ from the depth-analysis match marker
    **1**. The exact value is deliberately UNPINNED: this is the 2nd-pass fix of
    the re-audit's residual hole — the previous `Ensures(Result() == 2)` pinned
    an exact value the caller could fabricate with a literal `return 2` without
    ever invoking the helper. With the value opaque, the caller's postcondition
    `Result() == split_by_radicand_gcd(codes, num_surds(codes))` can be
    discharged ONLY by actually calling the helper.

It does **not** claim the concrete `(g, a, b)` triple value (not needed by the
tested behaviour) — only that the call is well-defined and that the result
EQUALS the helper's own (opaque) output, so the result is grounded in the
modeled computation rather than a hardcoded tag; `axiom_check.py` therefore
asserts only normal-return/raise, never a marker value. This is sound precisely
because the change never touches `split_surds`; it only restricts *who calls it*
via the guard.

**Soundness check (G-AX):** `axiom_check.py` imports `sympy` (the patched repo)
and exercises the real `split_surds`:
  * on a battery of all-positive-rational sums with ≥ 1 surd, asserts it returns
    normally (the axiom's `Ensures`) and that the frame fact `num_surds ≥ 1`
    holds (its precondition is established, not vacuous);
  * on the shallow imaginary sums the OLD rational-only guard admitted
    (`4 + I`, `3 + 2*I`, `5/3 + I`, `7 + I`), asserts `split_surds` RAISES
    `IndexError` — so the positive requirement in the axiom precondition is
    load-bearing;
  * end-to-end, asserts the real `_sqrt_match` returns `[]` on those shallow
    imaginary inputs (the FAIL_TO_PASS `_sqrt_match(4 + I) == []`) and a
    3-element match on all-positive-rational sums.
Exit 0 iff every observation holds. Run from a neutral directory with the
patched repo on `PYTHONPATH` (the in-container layout); running with the cwd
*inside* the worktree triggers an unrelated submodule-shadowing import quirk.
