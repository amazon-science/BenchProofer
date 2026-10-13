# refinement.md — sympy__sympy-21847

Operation correspondence between `implementation_selectMonomials` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

The modeled function is `itermonomials(variables, max_degrees, min_degrees)`, in
its integer-degree (`total_degree is True`) branch. The patch changes the
per-candidate acceptance predicate from "the largest single exponent reaches the
threshold" to "the total degree reaches the threshold", at two byte-identical
sites (the commutative and non-commutative sub-branches). The model is built
DIRECTLY (no callee axiom): the total-degree test is `minDegree ≤ powers.sum`.
There are no opaque callees; `axiom_check.py` is a skip stub and G-CONF
mechanically refutes the R/I legs.

## `implementation_selectMonomials` ↔ the body of the patched loop

Type bijection (mapping.md): a candidate monomial's exponent vector
`powers.values()` ↦ `powers : List Nat`; the enumerated candidate list ↦
`candidates : List (List Nat)`; `min_degree:int` ↦ `minDegree : Nat`;
`sum(powers.values())` ↦ `powers.sum`; `append(Mul(*item))` ↦ the
order-preserving append of `powers` into the accumulator.

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut acc := []` | `monomials_list_comm = []` / `monomials_list_non_comm = []` | R | the accumulator of accepted candidates, in enumeration order |
| `for powers in candidates do` | `for item in combinations_with_replacement(...)` / `product(...)`, after `powers` is tallied from `item` | R | iterate the enumerated candidates; each `powers` is the exponent vector for one `item` |
| `if minDegree ≤ powers.sum then` | `if sum(powers.values()) >= min_degree:` (THE FIX — was `max(powers.values()) >= min_degree`) | R | accept iff total degree meets the threshold; `sum(powers.values())` ↦ `powers.sum`, `>=` direction preserved (`min_degree <= sum`) |
| `acc := acc ++ [powers]` | `monomials_list_*.append(Mul(*item))` | R | order-preserving append of the accepted candidate |
| `return acc` | `yield from set(monomials_list_*)` | R | the accepted candidates; the unchanged `set(...)` dedup + `Mul` conversion are downstream context, not part of the modeled predicate |

The observable the F2P test pins: `set(itermonomials([x, y], 3, 2))` must
include `x**2`, `x*y`, `y**2` (total degree 2) and the degree-3 monomials — i.e.
candidates whose degree is spread across several variables and whose largest
single exponent (e.g. `x*y` → max exponent 1) is below `min_degree=2` but whose
total degree (2) meets it. The post-patch `sum` test keeps them; the pre-patch
`max` test drops them.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the impl mirrors the pre-patch control flow — the
  acceptance test is `minDegree ≤ powers.foldr Nat.max 0` (the largest single
  exponent). The carried gold proof of `correct_selectMonomials` fails to
  typecheck: the `h2 := rfl` bridge from the desugared loop body to the
  sum-keyed `select_helper` does not hold against a max-keyed loop body, so the
  proof's `rw [h2, select_helper]` fails (G-DIFF: prepatch verification fails).
  This is exactly FAIL_TO_PASS `test_monomials`
  (`set(itermonomials([x, y], 3, 2)) == {x**2, x*y, y**2, x**3, x**2*y, x*y**2,
  y**3}`): under `max`, `x*y` (max exponent 1 < 2) is wrongly dropped.

## Conformance (G-CONF)

`conformance_check.py` builds the Python shadow of `implementation_selectMonomials`
(the `sum`-keyed accept filter over the enumerated candidate exponent vectors)
and diffs the resulting SET of accepted monomials (matching the real
`set(itermonomials(...))`) against the REAL patched `itermonomials` over a
boundary catalogue plus >=1e5 fuzzed `(variables, max_degree, min_degree)`
inputs, in both the commutative and non-commutative configurations. Every op in
the impl is R/I, so the impl region is NOT all-A-tagged (`conf_skip=false`).
