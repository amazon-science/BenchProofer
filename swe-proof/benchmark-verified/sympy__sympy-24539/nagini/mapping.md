# mapping.md — sympy__sympy-24539

Model ↔ repo symbol binding, type abstraction, and callee provenance, at
`base_commit` 193e3825645d93c73e31cdceb6d742cc6919624d.

## Modeled function

| model.py symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `select_render_symbols(symbols, default_symbols, ngens)` | `PolyElement.as_expr(self, *symbols)` | `sympy/polys/rings.py:618-624` |

The changed function `as_expr` renders a polynomial as an expression over a
chosen sequence of generator symbols. The gold patch changes ONLY *which*
generator-symbol sequence is selected before the downstream builder is called;
`select_render_symbols` is the faithful skeleton of that selection.

## Type abstraction (§2)

| repo reality | model carrier | bijection |
|---|---|---|
| `symbols`: the var-args tuple of `Symbol` objects the caller supplies | `symbols: List[int]` | each `Symbol` ↔ its identity (an `int`); the tuple ↔ the list, position-preserving. Only the per-position identity and the length matter to the tested behavior. |
| `self.ring.symbols`: the ring's own tuple of generator `Symbol`s | `default_symbols: List[int]` | same `Symbol` ↔ `int` bijection. |
| `self.ring.ngens`: the number of generators (`int`) | `ngens: int` | identity. Tied to `default_symbols` by the precondition `ngens == len(default_symbols)` — true in the repo: `PolyRing.__init__` sets `ngens = len(symbols)` (`sympy/polys/rings.py:201,217`). |
| the generator sequence passed to `expr_from_dict(self.as_expr_dict(), *gens)` | the returned `List[int]` | the modeled `Result()` IS the `gens` sequence the downstream builder is invoked over — the sole quantity the selection controls. |
| `raise ValueError("Wrong number of symbols ...")` | `raise SymbolCountError()` | builtin-exception `Exsures` crashes the Nagini translator (SPEC_GUIDE §2); a user-defined class stands in. Only the fact-of-raise and the triggering condition are observable to the tests. |

## Callee provenance — why nothing is axiomatized

The only callee `as_expr` invokes after selecting `gens` is `expr_from_dict`
(`sympy/polys/polyutils.py:375-387`, via `as_expr_dict`,
`sympy/polys/rings.py:626-628`):

```python
def expr_from_dict(rep, *gens):
    result = []
    for monom, coeff in rep.items():
        term = [coeff]
        for g, m in zip(gens, monom):
            if m:
                term.append(Pow(g, m))
        result.append(Mul(*term))
    return Add(*result)
```

`expr_from_dict` is UNCHANGED by the gold patch and is a deterministic function
of `(rep, gens)`. For a fixed polynomial the term dict `rep = as_expr_dict()` is
fixed; the patch changes only `gens`. The rendered expression therefore differs
between pre- and post-patch *iff* the selected `gens` differs (`Pow(g, m)` uses
`g` from `gens` position-wise). Hence the tested behavior is fully captured by
the selected `gens` sequence, which the model returns directly. There is NO
axiom to consume and NO `@ContractOnly` callee: the changed quantity is modeled
directly, so `axioms` and `pure` regions are empty (see refinement.md, all
rows R/I). `expr_from_dict` appears only as documented context, not a consumed
contract.

## The behavior the F2P test pins

`test_PolyElement_as_expr` (gold `test_patch`):

```python
U, V, W = symbols("u,v,w")
g = 3*U**2*V - U*V*W + 7*W**3 + 1
assert f != g
assert f.as_expr(U, V, W) == g          # supplied 3 symbols (== ngens) MUST be used
raises(ValueError, lambda: f.as_expr(X)) # supplied 1 symbol (!= ngens=3) MUST raise
```

`f` is built over `x,y,z`. The test asserts that `f.as_expr(U, V, W)` renders
over the SUPPLIED `u,v,w` (so it equals `g`) — not over the ring's default
`x,y,z`. Pre-patch, `as_expr` discarded the supplied symbols and rendered over
`x,y,z`, so `f.as_expr(U,V,W)` equaled `f` (`3*x**2*y - ...`) ≠ `g`. This is
exactly the `Ensures(Implies(len(symbols) == ngens and len(symbols) > 0,
ToSeq(Result()) == ToSeq(symbols)))` clause, and exactly where
`model_prepatch.py` fails. The `raises(ValueError, ...)` arm is the `Exsures`
on `len(symbols) > 0 and len(symbols) != ngens`.
