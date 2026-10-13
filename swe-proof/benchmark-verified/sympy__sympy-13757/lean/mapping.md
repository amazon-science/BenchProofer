# mapping.md — sympy__sympy-13757

## Symbol binding (file:line @ base_commit a5e6a101869e027e7930e694f8b1cfb082603453)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_polyMul` / `problem_spec_polyMul` | the result of multiplying a plain expression by a polynomial (whether the product is carried out into a `Poly` or expressed as a plain symbolic expression), as decided by the binary-operator precedence dispatch plus `Poly`'s own multiplication routines | `sympy/core/decorators.py:121-133` (`call_highest_priority.binary_op_wrapper`) driving `Expr.__mul__`/`__rmul__` (`sympy/core/expr.py:138-146`) and `Poly.__mul__`/`__rmul__` (`sympy/polys/polytools.py:4041-4059`) |
| `Side` (pure helper) | which factor is the polynomial: `polyLeft` ↔ `Poly(...) * expr`, `polyRight` ↔ `expr * Poly(...)` | the two operand orders in the issue (`Poly(x)*x` vs `x*Poly(x)`) |
| `coercible : Bool` (spec input) | whether the plain-expression factor is convertible into a polynomial over the polynomial operand's generators: `Poly(e, *p.gens)` succeeds ↔ `true`; raises `PolynomialError` ↔ `false` | the `try: g = f.__class__(g, *f.gens) except PolynomialError:` guard inside `Poly.__mul__`/`__rmul__` (polytools.py:4043-4046 / 4053-4056) |
| `MulResult` (pure helper) | the observable outcome of the product: `evaluated` ↔ a `Poly` is produced (`is_Poly=True`), `symbolic` ↔ a plain non-`Poly` expression results | `Poly(x**2, x, domain='ZZ')` vs `x*Poly(x, x, domain='ZZ')` / `x*sin(x)` |
| `exprPriority` (impl-region constant `10`) | `Expr._op_priority` | `sympy/core/expr.py:105` (`_op_priority = 10.0`) — UNCHANGED by the patch |
| `polyPriority` (impl-region constant `10.001`) | `Poly._op_priority` | `sympy/polys/polytools.py:109` (`_op_priority = 10.001`) — the value the patch INTRODUCES (was inherited `10.0`) |
| dispatch test `polyPriority > exprPriority` | `other._op_priority > self._op_priority` | `sympy/core/decorators.py:126` |

## What the code does (base_commit)

`Expr.__mul__`/`__rmul__` are wrapped by `call_highest_priority`:

```python
def binary_op_wrapper(self, other):
    if hasattr(other, '_op_priority'):
        if other._op_priority > self._op_priority:        # decorators.py:126
            try:
                f = getattr(other, method_name)            # method_name='__rmul__' for __mul__
            except AttributeError:
                pass
            else:
                return f(self)                             # delegate to the higher-priority operand
    return func(self, other)                               # else: build the default Mul(...)
```

`Poly.__mul__`/`__rmul__` (polytools.py:4041-4059) both follow the same shape:

```python
def __mul__(f, g):
    if not g.is_Poly:
        try:
            g = f.__class__(g, *f.gens)     # coerce the expression into a Poly
        except PolynomialError:
            return f.as_expr()*g            # NOT coercible: plain symbolic product
    return f.mul(g)                          # coercible: carry the product out
```

Two operand orders for a product of a plain expression `e` (an `Expr`/`Number`,
`_op_priority == 10.0`) and a polynomial `p` (a `Poly`):

- **`p * e` (`polyLeft`).** `Poly.__mul__(p, e)` is decorated with `@_sympifyit`
  only, NOT `call_highest_priority`, so it runs directly: if `e` is coercible
  into `Poly(e, *p.gens)` the product is carried out → a `Poly` (`evaluated`);
  if the coercion raises `PolynomialError` (e.g. `sin(x)`, `sqrt(x)`, `1/x` —
  a generator used non-polynomially) it falls back to `p.as_expr()*e` → a plain
  expression (`symbolic`). Both pre- and post-patch.
- **`e * p` (`polyRight`).** `Expr.__mul__(e, p)` runs `binary_op_wrapper`:
  it delegates to `p.__rmul__(e)` **iff** `p._op_priority > e._op_priority`;
  `__rmul__` then applies the same coercible/fallback rule (evaluated when
  coercible, plain symbolic when not). Without delegation it returns
  `Mul(e, p)` — an unevaluated symbolic product (`symbolic`), regardless of
  coercibility.

### The bug and the fix

At base_commit `Poly` does NOT set `_op_priority`, so it inherits
`Expr._op_priority == 10.0`. For `polyRight`, `10.0 > 10.0` is **false**, so
`e * p` falls through to `Mul(e, p)` and stays symbolic even for a coercible
`e` — exactly the reported bug (`x*Poly(x)` → `x*Poly(x, x, domain='ZZ')`).
The patch adds `Poly._op_priority = 10.001`; now `10.001 > 10.0` is true, so
`e * p` delegates to `Poly.__rmul__`, which evaluates when `e` is coercible.
`polyLeft` is unaffected (it never used the priority dispatch). Non-coercible
expressions stay `symbolic` on both sides both pre- and post-patch (post-patch
via the `__rmul__` fallback `e*p.as_expr()` instead of the raw `Mul` — either
way, NOT a `Poly`).

The five F2P products (`test_issue_13079`) — every operand coercible:

| product | side | coercible | post-patch |
|---|---|---|---|
| `Poly(x)*x` | polyLeft | true | evaluated |
| `x*Poly(x)` | polyRight | true | evaluated (was symbolic — the bug) |
| `-2*Poly(x)` | polyRight | true | evaluated (was symbolic) |
| `S(-2)*Poly(x)` | polyRight | true | evaluated (was symbolic) |
| `Poly(x)*S(-2)` | polyLeft | true | evaluated |

`-2` becomes a sympy `Integer` (an `Expr`, priority `10.0`) before dispatch, so it
behaves identically to `x` / `S(-2)`.

Real-repo probes of the non-coercible leg (post-patch, verified in a /tmp
checkout at base_commit + gold patch): `sin(x)*Poly(x, x)` → `x*sin(x)` (`Mul`),
`Poly(x, x)*sin(x)` → `x*sin(x)`, `sqrt(x)*Poly(x, x)` → `x**(3/2)` (`Pow`),
`(1/x)*Poly(x, x)` → `1` (`One`) — all `is_Poly=False`, i.e. `symbolic`. Note
`sin(y)*Poly(x, x)` IS coercible (`Poly(sin(y)*x, x, domain='ZZ[sin(y)]')` —
`sin(y)` does not involve the generator `x`) → `evaluated`.

## Lean modeling

- `Side` models the operand order; `coercible` models whether the expression
  converts into a polynomial over the `Poly`'s generators; `MulResult` models
  the observable outcome (a `Poly` vs a plain non-`Poly` expression).
- The mechanism — the two operands' operator priorities (`exprPriority = 10`,
  `polyPriority = 10.001`) and the precedence test `polyPriority > exprPriority`
  — lives entirely in the `impl` region (it is the fix mechanism, elided from the
  spec view). The pre-patch impl sets `polyPriority := 10` (the inherited `Expr`
  value); its `polyRight` branch then yields `symbolic` even for coercible
  input, the bug.
- `problem_spec_polyMul` pins the post-patch observable behavior as a function
  of coercibility: `evaluated` iff the expression is coercible, for EITHER
  operand order (`symbolic` otherwise). A verifying impl must produce
  `evaluated` for coercible `polyRight`, which the dispatch only does when the
  polynomial advertises strictly greater priority — and must NOT produce
  `evaluated` for non-coercible input, matching the real fallback.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| operand order of the product | `Side` | `Poly*expr ↔ .polyLeft`, `expr*Poly ↔ .polyRight` |
| `Poly(e, *p.gens)` succeeds / raises `PolynomialError` | `coercible : Bool` | succeeds ↔ `true`, raises ↔ `false` |
| product outcome | `MulResult` | a `Poly` (`is_Poly=True`) ↔ `.evaluated`; a plain non-`Poly` expression (unevaluated `Mul`, or the coercion-fallback result) ↔ `.symbolic` |
| `Expr._op_priority` (`== 10.0`) | `exprPriority : Rat := 10` | `10.0 ↔ (10 : Rat)` |
| `Poly._op_priority` (`== 10.001`) | `polyPriority : Rat := 10.001` | `10.001 ↔ (10001/1000 : Rat)` |
| `other._op_priority > self._op_priority` | `polyPriority > exprPriority` | identity on `Rat` order |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no `opaque` decl.** The dispatch decision is
  modeled DEEPLY (the precedence comparison is spelled out in the impl);
  SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed decision. The proof
  consumes no `_prop` axiom (it is `rfl`/`norm_num` over the concrete rationals).
- **Deep-model references validated by G-AX (`axiom_check.py`):**
  (1) `Expr._op_priority == 10.0` (the UNCHANGED left-operand priority);
  (2) the `call_highest_priority` dispatch rule (delegate iff
  `other._op_priority > self._op_priority`);
  (3) the `Poly.__mul__`/`__rmul__` coercion rule (a `Poly` results iff the
  expression is convertible over the generators, else a plain non-`Poly`
  fallback). All three are unchanged by the patch and asserted against the real
  repo. `Poly._op_priority == 10.001` is the value the patch introduces (tagged
  I in refinement.md, validated by G-GOLD/G-RESOLVE); it is observed too, as a
  post-patch fact, not consumed as an axiom.
- `Poly.mul` / `Mul` are the unchanged carriers of the actual product; the patch
  does not touch them. Their net effect is folded into the `MulResult`
  observable (evaluated vs symbolic) — orthogonal to the dispatch fix.

## G-CONF fuzz seed

Pinned LCG seed: **13757** (see `conformance_check.py` `SEED`). The R/I shadow of
`implementation_polyMul` is diffed against an in-process replica of the
POST-PATCH dispatch (`binary_op_wrapper` semantics with `Expr` priority `10.0`,
`Poly` priority `10.001`, plus the coerce-or-fallback rule of
`Poly.__mul__`/`__rmul__`) over the two operand orders × both coercibility
values, plus a fuzz over arbitrary `(leftPriority, rightPriority)` pairs
confirming the precedence rule matches Python's `>` dispatch, over ≥1e5 inputs.
Hand-picked edge cases pin the discriminating clause (`expr * Poly` with a
coercible expr must be `evaluated` — it was `symbolic` when the priorities
tied) AND the non-coercible fallback (`sin(x)*Poly(x)`, `Poly(x)*sin(x)`,
`sqrt(x)*Poly(x)`, `Poly(x)*(1/x)` all `symbolic`).
