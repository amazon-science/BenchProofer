# mapping.md — sympy__sympy-20438

## Modeled function

| Lean | Python | file:line @ base_commit `33b47e4bd6` |
|---|---|---|
| `implementation_isSubset` / `problem_spec_isSubset` / `correct_isSubset` | the subset test of a product of finite collections against a finite collection of tuples — returns whether every tuple of the product is a member of the finite collection | `sympy/sets/handlers/issubset.py:136-139` (new dispatch `is_subset_sets(a_ps : ProductSet, b_fs : FiniteSet) -> fuzzy_and(b_fs.contains(x) for x in a_ps)`) |

## Type bijection (Lean ↔ Python) — used by G-CONF + G-AX

| Python | Lean | notes |
|---|---|---|
| `FiniteSet(*ints)` (a factor of the product) | `List Int` | a finite collection of integer elements; order irrelevant to the modeled result |
| `ProductSet(f1, …, fn)` | `factors : List (List Int)` | the product is given by its list of factors; iterating the ProductSet yields the cartesian-product tuples |
| a product tuple `(x1, …, xn)` of integers | `List Int` | a tuple of integers ↔ a `List Int` of the same length (per-position, in order) |
| `FiniteSet` of tuples (the candidate superset `b_fs`) | `List (List Int)` | a finite collection of integer-tuples |
| `b_fs.contains(tuple)` for concrete integer tuples | `b_fs.contains x` (`List.contains`, structural `BEq` on `List Int`) | on concrete integers SymPy's membership is structural tuple equality; modeled deeply (A-reference, G-AX validated) |
| the cartesian-product enumeration of `a_ps` | `productSet factors` (pure helper) | yields every integer-tuple of the product; element order is irrelevant to the membership-conjunction result |
| `fuzzy_and(definite bools)` over the concrete domain | boolean conjunction wrapped in `some` (`Option Bool`) | on the concrete integer domain every `contains` is definite (True/False), so `fuzzy_and` is a *determined* verdict `some (boolean AND)`; `None`/`none` denotes the absent (pre-patch) verdict |
| the three-valued subset verdict (`True`/`False`/`None`) | `Option Bool` (`some true` / `some false` / `none`) | the fix turns a `None` (no dispatch) into a determined `some _` |

The modeled domain is **concrete integer ProductSet/FiniteSet** (the domain the
FAIL_TO_PASS assertions exercise: `a = FiniteSet(1,2)`, `b = ProductSet(a,a)`,
`c = FiniteSet((1,1),(1,2),(2,1),(2,2))`, `d = FiniteSet(1)`). Over this domain
the per-element membership is definite, so the fuzzy three-valued result
collapses to a definite Bool — modeled as `Bool`.

## Callee provenance / flag deps

- `b_fs.contains(x)`: UNCHANGED callee (`FiniteSet.contains`). On the concrete
  integer-tuple domain it is structural membership; modeled DEEPLY as
  `List.contains` (A-reference, validated == real callee by G-AX, not a consumed
  axiom).
- iterating a `ProductSet` (`for x in a_ps`): UNCHANGED behavior — yields the
  cartesian product of the factors; modeled deeply as `productSet`
  (A-reference, validated by G-AX).
- `fuzzy_and`: UNCHANGED logic helper; over definite bools it is boolean AND with
  short-circuit. Modeled deeply as the accumulator loop. No flag dependency.

## Out-of-scope edits in the same gold patch

The gold patch also edits two downstream consumers, which ride along in
`patch.diff` (gold verbatim) so the harness resolves but are **not** separately
modeled (they are not independently cold-derivable from the issue as a clean
input→output function — they are guard/dispatch plumbing on top of the fixed
subset test):

- `sympy/core/relational.py` (`Relational._eval_simplify`,
  `Equality._eval_simplify`): adds `isinstance(... , Expr)` guards that early-out
  when the relation's sides are non-`Expr` sets, preventing the `AttributeError`
  crash reported in the issue. Behavior plumbing around the simplify path.
- `sympy/sets/handlers/comparison.py`: removes a stale `(FiniteSet, Interval)`
  equality handler and gives the generic `(Set, Set)` equality the symmetric
  `is_subset`-based answer `tfn[fuzzy_and(a.is_subset(b), b.is_subset(a))]`. This
  consumes the very subset test modeled here.

These produce no independently-modeled triple; they are tagged ride-along edits
in refinement.md. The single modeled triple captures the root fixed behavior
(`ProductSet.is_subset(FiniteSet)`), which `test_issue_19378` directly asserts.

## G-CONF fuzz seed

`conf_seed = 20438` (pinned; see conformance_check.py and meta.json).
