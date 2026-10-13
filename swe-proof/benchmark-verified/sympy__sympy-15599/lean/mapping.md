# mapping.md — sympy__sympy-15599

## Instance
- repo: sympy/sympy
- base_commit: 5e17a90c19f7eecfa10c1ab872648ae7e2131323
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change (one behavior, one site)
`Mod.eval(p, q)` evaluates `p % q` symbolically. When `p` is a `Mul` (a product
of factors) the routine splits the factors into `mod_l` (factors that are
themselves `Mod(...)` objects) and `non_mod_l` (everything else). The gold patch
adds a normalisation of `non_mod_l` when the divisor `q` is a concrete integer
other than one:

```python
elif isinstance(p, Mul):                        # sympy/core/mod.py:120 @ base_commit
    both_l = non_mod_l, mod_l = [], []
    for arg in p.args:
        both_l[isinstance(arg, cls)].append(arg)

    if mod_l and all(inner.args[1] == q for inner in mod_l):
        ...                                       # (pre-existing distributive branch)
        return prod_non_mod*cls(net, q)

    # ---- GOLD PATCH (the modeled behavior) ----
    if q.is_Integer and q is not S.One:
        _ = []
        for i in non_mod_l:
            if i.is_Integer and (i % q is not S.Zero):
                _.append(i % q)                   # reduce a concrete int factor
            else:
                _.append(i)                       # keep symbolic / zero-residue
        non_mod_l = _

    p = Mul(*(non_mod_l + mod_l))
```

The effect: in a product, every concrete-integer coefficient factor is reduced
modulo `q` (unless the residue is `0`, in which case it is kept so the product is
not collapsed), while symbolic factors and `Mod(...)` factors are preserved. This
is what reduces `Mod(3*i, 2)` to `Mod(i, 2)` (coefficient `3 → 3 % 2 = 1`) and
keeps `Mod(8*i, 4)` reducible (`8 → 8 % 4 = 0`, factor kept, later collapses).

## Modeled function — the `non_mod_l` reduction loop of `Mod.eval`'s `Mul` branch
| field | value |
|---|---|
| file @ base_commit | `sympy/core/mod.py` |
| function | `Mod.eval` (classmethod; the patched block is the new `for i in non_mod_l` loop added at lines 140-151 of the patched file, inside the `isinstance(p, Mul)` branch which begins at line 120 @ base_commit) |
| role | sole modeled function; the per-factor integer reduction is the whole behavioral fix |

The observable the F2P test (`test_Mod`, issue 15493 assertions) pins is the
factor list of the rebuilt product `Mul(*(non_mod_l + mod_l))` — specifically
that each concrete-integer factor has been reduced modulo `q`. The Lean
`implementation_modFactors q factors` models exactly this per-factor
transformation over `non_mod_l`.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
A product's factor list is modelled by `List Factor`:

| Lean | Python | note |
|---|---|---|
| `Factor.coeff n` (`n : Int`) | a `non_mod_l` element with `i.is_Integer == True` | a concrete integer coefficient factor; `n` ↔ `int(i)` |
| `Factor.sym k` (`k : Nat`) | a `non_mod_l` element with `i.is_Integer == False` | a symbolic / non-integer factor (incl. symbols, `Mod(...)`); the tag `k` is an opaque identity, never reduced |
| `factors : List Factor` | `non_mod_l` (in argument order) | the non-`Mod` factors of the product |
| `q : Int` | `q` (a concrete `Integer`) | the divisor; `q = 0` is unreachable in the repo (`doit` raises `ZeroDivisionError("Modulo by zero")` before the `Mul` branch), and the total spec extends there by identity — see below |
| `implementation_modFactors q factors` | the rebuilt `non_mod_l` after the patch loop | factor-for-factor image |
| `intMod n q` | `n % q` (Python / sympy `Integer.__mod__`) | floored remainder, sign of `q` |

`Mod(...)` factors (`mod_l`) and the trailing concatenation `non_mod_l + mod_l`
are outside the modeled transformation (the loop only rewrites `non_mod_l`); they
are carried unchanged and so are not part of the per-factor contract.

## The residue convention (the R-leg refinement)
sympy `Integer.__mod__` and Python `int.__mod__` both follow the floored
convention: the residue has the sign of the divisor (`(-7) % 2 == 1`,
`7 % (-2) == -1`). Lean `Int`'s `%` is the *truncating* `Int.emod` (residue sign
of the dividend), so the spec/impl use `intMod a b := a - b * (Int.fdiv a b)`
(`Int.fdiv` = floored division), which reproduces the Python convention exactly.
This equality (`intMod == Python %`) is the **R** refinement that G-CONF tests.

## The `is not S.Zero` subtlety (zero-residue factor is kept)
The patch tests `i % q is not S.Zero` (identity, not `!= 0`). For a concrete
integer `i` and integer `q`, `i % q` returns a sympy `Integer`; it `is S.Zero`
exactly when its value is `0`. So the identity test is value-equivalent to
`i % q != 0` here, and is modeled as `intMod n q ≠ 0`. When the residue is zero
the original factor `i` is appended unchanged (the product keeps that factor so a
later branch can collapse the whole product, e.g. `Mod(8*i, 4)`).

## The `q = 0` totalization (no precondition on `correct_modFactors`)
In the real repo `q = 0` never reaches the modeled loop: `Mod.eval`'s `doit`
raises `ZeroDivisionError("Modulo by zero")` up front (pre- and post-patch
alike), so the `Mul` branch is unreachable for a zero divisor. The Lean model
is nevertheless TOTAL: `Int.fdiv n 0 = 0` gives `intMod n 0 = n`, so
`reduceFactor 0` (and hence `reduceFactors 0`) is the identity — the natural
"loop reduces nothing" extension. `correct_modFactors` therefore carries NO
`q ≠ 0` hypothesis: the spec pins `result` for EVERY `(q, factors)`, leaving an
adversarial implementation no precondition-shadowed freedom (the earlier
`q ≠ 0` precondition admitted a same-spec impl diverging only at `q = 0`,
flagged by the audit as spec-too-weak). The unreachable `q = 0` point is a
modeling convention, not a claimed repo behavior; `conformance_check.py` still
skips `q = 0` because the REAL leg would raise there.

## Callee provenance / flag deps
- `i.is_Integer` is the **unchanged** integer-ness predicate of a factor, modeled
  directly by the `Factor` constructor (`coeff` vs `sym`) — an **R** op, not a
  separately-defined callee the patch changes, so it is NOT axiomatized.
- `i % q` (the residue arithmetic) is the **changed** op, modeled DEEPLY as
  `intMod n q` (floored remainder) — an **R** op validated by G-CONF.
- No flag dependency (the loop runs unconditionally once `q.is_Integer and
  q is not S.One`).

## G-CONF fuzz seed
Pinned seed: **15599** (used in `conformance_check.py`).
