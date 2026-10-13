# refinement.md — sympy__sympy-15599

Operation correspondence between `implementation_modFactors` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the modeled function rewrites a product's
non-`Mod` factor list by reducing each concrete-integer factor modulo `q`. Every
op is **R** or **I** — the only non-trivial type refinement is the residue
arithmetic (Python floored `%` ↦ Lean `intMod` via `Int.fdiv`), which G-CONF
differential-tests. G-AX is a skip stub (no consumed callee axiom).

## `implementation_modFactors` ↔ the `non_mod_l` reduction loop of `Mod.eval`'s `Mul` branch

The gold patch adds, inside `isinstance(p, Mul)`, a loop that rebuilds
`non_mod_l`: when `q.is_Integer and q is not S.One`, each integer factor `i` is
replaced by `i % q` unless that residue is zero (then `i` is kept); non-integer
factors are kept unchanged.

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `if q = 1 then return factors` | `if q.is_Integer and q is not S.One:` guards the whole loop — when `q is S.One` the loop is skipped and `non_mod_l` is unchanged | R | divisor-is-one short-circuit; `q.is_Integer` is the modeled precondition (`q : Int`), `q is not S.One` ↦ `q ≠ 1`. Returning `factors` unchanged is exactly "skip the loop". |
| `for f in factors do …` | `for i in non_mod_l:` | I | same iteration over the non-`Mod` factor list, in order, accumulating into a fresh list (`_` / `acc`). |
| `match f with \| Factor.coeff n => if intMod n q ≠ 0 then acc := acc ++ [Factor.coeff (intMod n q)]` | `if i.is_Integer and (i % q is not S.Zero): _.append(i % q)` | R | `i.is_Integer` ↦ the `coeff` constructor; `i % q` (floored Python remainder) ↦ `intMod n q` (`a - b*Int.fdiv a b`); `is not S.Zero` ↦ `≠ 0` (value-equivalent for concrete `Integer` residues, see mapping.md). |
| `else acc := acc ++ [Factor.coeff n]` (zero-residue integer factor) | `else: _.append(i)` (the `i % q is S.Zero` case for an integer factor) | I | zero-residue factor kept unchanged so the product is not collapsed (`Mod(8*i,4)`: `8 → 0` residue, factor `8` kept). |
| `\| Factor.sym s => acc := acc ++ [Factor.sym s]` | `else: _.append(i)` (the `not i.is_Integer` case) | I | symbolic / non-integer factor preserved exactly. |
| `return acc` | `non_mod_l = _` (then `p = Mul(*(non_mod_l + mod_l))`) | R | the rebuilt non-`Mod` factor list; the trailing `+ mod_l` concat and `Mul(...)` reconstruction are outside the modeled per-factor transformation (carried unchanged). |

The result is the precise observable the F2P test pins: the reduced factor list,
so that `Mod(3*i, 2)` → factor `3` becomes `1` → `Mod(i, 2)`.

`correct_modFactors` carries NO `q ≠ 0` precondition: the model is total
(`intMod n 0 = n`, so `reduceFactors 0` is the identity — see mapping.md's
"`q = 0` totalization"), which closes the precondition-shadowed freedom a
spec-too-weak audit exploited (a same-spec impl diverging only at the
repo-unreachable `q = 0`).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the impl returns `factors` unchanged (the pre-patch
  `Mul` branch performed NO reduction of `non_mod_l`). For `q = 2`,
  `factors = [Factor.coeff 3]` the spec requires the result to equal
  `reduceFactors 2 [coeff 3] = [coeff 1]`, but the prepatch impl yields
  `[coeff 3] ≠ [coeff 1]`, so the carried gold proof of `correct_modFactors`
  cannot close. (FAIL_TO_PASS: `test_Mod`, issue 15493: `Mod(3*i, 2) == Mod(i, 2)`.)
