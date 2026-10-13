# mapping.md — sympy__sympy-15599

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5e17a90c19f7eecfa10c1ab872648ae7e2131323`, states the type
abstraction, and gives the provenance of the `@ContractOnly` reference symbol
(callee source + the exact behaviour validated against the real callee by G-AX).
This bundle has no consumed axiom: both `reduced_factor` and `residue` are
A-reference (value validated == the real callee; the proof uses their
determinism, not their `Ensures`).

Repo file under change: `sympy/core/mod.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduce_coefficients(is_int, value, m)` | the integer-coefficient rewrite of the non-modular factor list inside `Mod.eval.doit`'s product branch — `sympy/core/mod.py`, the `elif isinstance(p, Mul):` block, lines 120-140 (the gold patch inserts the rewrite at line 140) | the modeled changed function (per-factor product reduction modulo an integer divisor) |
| `residue(value, m)` *(reference symbol — A-reference)* | `Integer.__mod__` — `sympy/core/numbers.py:2135` (`return Integer(self.p % other.p)`); invoked as `i % q` in the inserted block | unchanged numeric primitive the new block calls to shrink an integer coefficient; its value is validated == the real callee by G-AX, the proof uses only its determinism (not its `Ensures`) |
| `reduced_factor(is_int, value, m)` *(deep model — A-reference)* | the per-factor body `if i.is_Integer and (i % q is not S.Zero): i%q else: i` inside the inserted block (`sympy/core/mod.py:141-147` post-patch) | pure spec: the rewrite applied to one factor; deep model of the changed operation, validated `reduced_factor == real factor rewrite` by axiom_check.py (G-AX), NOT consumed as an axiom |

The product `p` is an `Add`/`Mul` of factors; in the `Mul` branch the code splits
`p.args` into `non_mod_l` (factors that are not themselves `Mod`) and `mod_l`
(factors that are `Mod`). The gold patch rewrites the factors in `non_mod_l`:
every concrete-`Integer` factor whose value is not a multiple of `q` is replaced
by `i % q`, then `p = Mul(*(non_mod_l + mod_l))` and `Mod.eval` continues to its
gcd-extraction / `doit` re-check. The modeled function is exactly this
per-factor `non_mod_l` rewrite; the surrounding `Mod.eval` machinery
(gcd_terms, the re-`doit`, `Mul` reconstruction) is unchanged and outside the
spec.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `non_mod_l`: a Python list of sympy factor `Expr` objects | two parallel `List[int]`: `is_int[k]` (1 iff factor k is a concrete `Integer`, else 0) and `value[k]` (the integer value when `is_int[k]==1`; an irrelevant placeholder otherwise) | factor k ↔ `(is_int[k], value[k])`; `len(non_mod_l)` ↔ `len(value)`; the rewrite returns one factor per input factor ↔ `len(Result()) == len(value)` |
| a concrete `Integer` factor `i` with value `v` | `is_int[k]==1`, `value[k]==v` | `int(i) == value[k]` |
| an opaque (symbolic / non-`Integer`) factor | `is_int[k]==0` | the factor is left identically unchanged by the rewrite; only its integer-ness tag (0) matters to the spec |
| the divisor `q`, a sympy `Integer` with `q.is_Integer and q is not S.One` (the inserted block's guard) | `m: int`, `m >= 2` | `int(q) == m`; the guard `q.is_Integer and q != 1` for the divisors the tests exercise (2, 4, …) ↔ `m >= 2`. Negative integer divisors are outside the tested behaviour and the modeled domain (mapping note below). |
| the factor value after `i % q` | the residue value `residue(value[k], m)` | `int(i % q) == residue(value[k], m)` for `q >= 2` (sympy `Integer.__mod__` is Python floored mod) |

The non-`Integer` factor's *value* is irrelevant to the rewrite (the branch is
gated on `is_int==1`), so it is an unconstrained placeholder in the carrier; the
spec only relies on the integer-ness tag for such factors and pins their output
to be the unchanged input value.

**Modeled-domain note.** The guard is `q.is_Integer and q is not S.One`, i.e. any
integer divisor `!= 1`. The benchmark's tested divisors are positive (`2`, `4`),
for which sympy `Integer.__mod__` returns the least non-negative residue in
`[0, m)`. The model fixes `m >= 2`, which is faithful to every tested case and
to the discriminating behaviour `Mod(3*i, 2) == Mod(i, 2)` / `Mod(8*i, 4) == 0`.
A negative integer divisor would route through the same `% ` (sign of divisor)
but is neither tested nor part of the observed F2P behaviour; it is excluded
from the modeled domain rather than mis-modeled.

`str`/object indexing is banned in Nagini, so the heterogeneous factor list is
carried by parallel `List[int]`; the specification is phrased over `PSeq[int]`
via `ToSeq`/element indexing with explicit in-bounds guards.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `reduced_factor` deep model ↔ the gold factor rewrite (A-reference)
The *changed* operation — rewriting one factor of `non_mod_l` modulo `q` — is
modeled **deeply** by the `@Pure` function `reduced_factor` in the `pure` region
and the verified loop in `reduce_coefficients`; there is **no `reduce_factor`
axiom** the proof consumes. The deep model is validated equal to the real
rewrite out-of-band by axiom_check.py (G-AX). Source (the gold block,
`sympy/core/mod.py` post-patch):

```python
if q.is_Integer and q is not S.One:
    _ = []
    for i in non_mod_l:
        if i.is_Integer and (i % q is not S.Zero):
            _.append(i%q)
        else:
            _.append(i)
    non_mod_l = _
p = Mul(*(non_mod_l + mod_l))
```

For each factor `i`: a concrete-`Integer` `i` with `i % q != 0` becomes `i % q`;
any other factor (opaque, or an `Integer` multiple of `q`) is appended
unchanged. This is precisely `reduced_factor(is_int, value, m)`:
`is_int==1 and residue(value,m)!=0 -> residue(value,m)`, else `value`. G-AX runs
the real rewrite on real sympy factors and asserts `reduced_factor == real`
factor by factor.

### 3.2 `residue` ↔ `Integer.__mod__` (A-reference)
**Callee:** sympy `Integer.__mod__` (`sympy/core/numbers.py:2135`):

```python
def __mod__(self, other):
    if global_evaluate[0]:
        if isinstance(other, integer_types):
            return Integer(self.p % other)
        elif isinstance(other, Integer):
            return Integer(self.p % other.p)
        ...
```

It delegates to Python's `int.__mod__` on the underlying `p` values, i.e. the
**floored** remainder whose sign follows the divisor. For a divisor `m >= 2`
this is the least non-negative residue: `0 <= r < m` and `(value - r)` a
multiple of `m`, and `r == value` when `0 <= value < m`. These three facts are
the symbol's `Ensures` (range, congruence, in-range idempotence) — consistent
with the real callee, not the full `Integer` arithmetic API — but they are
**A-reference, not A-consumed**: the proof of `reduce_coefficients` does NOT use
them. It discharges the postcondition `Result()[k] == reduced_factor(...)` purely
by **structural identity** — the impl reuses the exact same `residue(...)` calls
as `reduced_factor`, so determinism of the `@Pure residue` is all the proof
needs (weakening the three `Ensures` to `True` still verifies — confirmed). What
G-AX validates is `residue`'s **value** `== Integer.__mod__` (the A-reference
discipline of SPEC_GUIDE §3), exactly as for the `reduced_factor` deep model in
§3.1. The symbol is `@Pure @ContractOnly` because it is referenced inside
`reduced_factor`/the postcondition.

**Soundness check (G-AX):** `axiom_check.py` runs the real `Integer % Integer`
on 162 boundary `(value, m)` pairs (moduli 2…100; values incl. negatives, 0,
in-range, multiples, boundaries) plus 50 000 randomized pairs, asserting all
three `Ensures`. It then runs the real per-factor rewrite on real sympy factors
(integer constants across the residue boundary, and opaque symbols `i, x, y,
i*x` that must stay unchanged) over the moduli 2…12 plus 20 000 fuzz factors,
asserting `reduced_factor == real`. Finally it checks the end-to-end tested
witnesses `Mod(3*i,2)==Mod(i,2)`, `Mod(8*i,4)==0`, `Mod(8*i/j,4)==4*Mod(2*i/j,1)`.
It imports only `sympy` (the package under change) + stdlib `random`/`sys`. Exit
0 iff sound.
