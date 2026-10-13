# mapping.md — sympy__sympy-21847

## Symbol binding (file:line @ base_commit d9b18c518d64d0ebe8e35a98c2fb519938b9b151)

- Modeled function: `itermonomials(variables, max_degrees, min_degrees=None)`
  — `sympy/polys/monomials.py:14-152` @ base_commit.
- Patched lines: `sympy/polys/monomials.py:130` (commutative sub-branch) and
  `sympy/polys/monomials.py:142` (non-commutative sub-branch), both inside the
  `total_degree is True` branch (integer `max_degrees`/`min_degrees`).
- The modeled `implementation_selectMonomials` captures the per-candidate
  acceptance test that both patched lines share: the loop that, for each
  candidate monomial produced by `combinations_with_replacement(variables,
  max_degree)` (commutative) or `product(variables, repeat=max_degree)`
  (non-commutative), tallies the per-variable exponents into `powers` and then
  decides whether to append `Mul(*item)` to the output list.

### The candidate-enumeration / `Mul` / `set(...)` context (UNCHANGED)

The patch does NOT touch how candidate monomials are enumerated
(`combinations_with_replacement` / `product`), how exponents are tallied
(`powers[variable] += 1`), how a kept candidate is turned into an expression
(`Mul(*item)`), or the final dedup-and-yield (`yield from set(...)`). The ONLY
change is the per-candidate acceptance predicate: `max(powers.values())` →
`sum(powers.values())`. The model therefore takes the already-enumerated
candidate monomials — each reduced to its exponent vector `powers.values()` — as
the input list `candidates : List (List Nat)`, and models exactly the acceptance
filter.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean |
|---|---|
| a candidate monomial `item`'s exponent multiset `powers` (the dict `{var: count}`) | `powers : List Nat` (the exponent vector, one entry per variable, the dict's `.values()`) |
| `min_degree : int` (the integer min degree) | `minDegree : Nat` |
| the list of candidate monomials enumerated for the chosen `max_degree` | `candidates : List (List Nat)` |
| `sum(powers.values())` (total degree of a candidate) | `powers.sum` |
| `max(powers.values())` (largest single exponent — pre-patch test) | `powers.foldr Nat.max 0` (pre-patch only) |
| `sum(powers.values()) >= min_degree` (accept predicate) | `decide (minDegree ≤ powers.sum)` |
| the sub-list of accepted candidates, in enumeration order, before `set(...)` dedup | `result : List (List Nat)` |
| `monomials_list_comm.append(Mul(*item))` / `monomials_list_non_comm.append(...)` | keeping `powers` in `result` (the order-preserving append into the accumulator) |

Notes:
- The Python loop appends `Mul(*item)` (an expression) keyed off the SAME accept
  decision. Modeling the accumulator as the list of accepted exponent vectors is
  a faithful skeleton of the order-preserving append; the subsequent `Mul` and
  `set(...)` dedup are unchanged context downstream of the modeled predicate.
- `min_degree` is a Python `int` that has already been validated `>= 0` and
  `<= max_degree` before this loop runs (lines 104-115), so `Nat` is exact.
- The commutative and non-commutative sub-branches differ ONLY in the candidate
  enumerator (`combinations_with_replacement` vs `product`); the per-candidate
  acceptance loop and its patched predicate are byte-identical between them, so a
  single Lean model covers both.

## Callee provenance + flag deps

- No UNCHANGED callee property is consumed by the proof: the acceptance predicate
  is modeled DIRECTLY as `minDegree ≤ powers.sum`. `powers.sum` is the total
  degree; there is no opaque callee. (`sum`/`max` over the dict values are Python
  builtins, modeled by `List.sum` / `List.foldr Nat.max 0`.)
- Flag dependency: the patched predicate lives in the `total_degree is True`
  branch — reached when `max_degrees` (and hence `min_degrees`) is an INTEGER,
  not a list. The list-degree branch (lines 145-152) is unchanged and uses a
  different algorithm; it is out of the model's scope. G-CONF fuzzes the integer
  branch (`itermonomials(vars, max:int, min:int)`).

## G-CONF fuzz seed

`conf_seed = 21847` (pinned in meta.json).
