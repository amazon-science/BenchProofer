# refinement.md — sympy__sympy-13757

Operation-by-operation correspondence between `implementation_polyMul`
(Solution.lean impl region) and `patch.diff` (the gold edit `Poly._op_priority =
10.001`, in the context of the UNCHANGED `call_highest_priority` dispatch and the
`Poly`/`Expr` multiplication methods). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let exprPriority : Rat := 10` | `Expr._op_priority = 10.0` (expr.py:105, UNCHANGED) | A-reference |
| 2 | `let polyPriority : Rat := 10.001` | `Poly._op_priority = 10.001` — the line the patch ADDS (polytools.py:109) | I |
| 3 | `match side with \| Side.polyLeft => if coercible then evaluated else symbolic` | `Poly.__mul__(p,e)`: not priority-decorated; `try: g = Poly(e, *p.gens) except PolynomialError: return p.as_expr()*e` then `return p.mul(g)` — a `Poly` iff `e` coerces (polytools.py:4041-4048) | A-reference / R |
| 4 | `\| Side.polyRight => if polyPriority > exprPriority then ... else ...` | `Expr.__mul__(e,p)` → `binary_op_wrapper`: delegate to `p.__rmul__(e)` iff `p._op_priority > e._op_priority` (decorators.py:126) | A-reference |
| 5 | `then (if coercible then evaluated else symbolic)` | delegation hits `Poly.__rmul__` → same coerce-or-fallback rule: `Poly` iff `e` coerces, else `e*p.as_expr()` (polytools.py:4050-4059) | A-reference / R |
| 6 | `else return MulResult.symbolic` | no delegation → `func(self, other)` returns the unevaluated `Mul(e, p)` — not a `Poly`, regardless of coercibility (decorators.py:132) | R |

Notes:

- **No A-consumed axiom; no `opaque` callee.** The dispatch decision — the heart
  of the fix — is modeled DEEPLY: the precedence comparison
  `polyPriority > exprPriority` is spelled out in the impl. SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed decision, so there is no consumed
  `_prop` axiom. The proof closes by `rfl`/`norm_num` over the concrete
  rationals.
- **A-reference rows (1, 3, 4, 5)** are validated by `axiom_check.py` (G-AX)
  against the real repo: the unchanged plain-expression precedence is `10.0`;
  the `call_highest_priority` dispatch delegates iff the other operand's
  `_op_priority` is STRICTLY greater; and `Poly.__mul__`/`__rmul__` produce a
  `Poly` iff the expression factor is convertible over the generators (else a
  plain non-`Poly` fallback). All are patch-independent facts the impl's
  faithfulness rests on; none is the operation the patch changes.
- **The fix itself is row 2 (tag I):** the patch literally inserts the constant
  `Poly._op_priority = 10.001`. The impl pins `polyPriority := 10.001`, the same
  value, so row 4's comparison becomes `10.001 > 10` (true) and a right-hand
  polynomial product runs `Poly.__rmul__` — `evaluated` for coercible input.
  The pre-patch impl (`Solution_prepatch.lean`) pins `polyPriority := 10` (the
  inherited `Expr` value), making the comparison `10 > 10` (false), so a
  right-hand product stays `symbolic` even for coercible input — exactly the
  reported bug (`x*Poly(x)` not evaluating). That is the discriminating clause
  the spec sees: `problem_spec_polyMul` demands `evaluated` for
  (`polyRight`, `coercible = true`), which the prepatch impl cannot satisfy.
- **The `coercible` input** (rows 3, 5) keeps the spec faithful on the
  NON-coercible slice: real post-patch products like `sin(x)*Poly(x, x)` →
  `x*sin(x)` (a `Mul`, not a `Poly`) are `symbolic`, and the spec demands
  exactly that (`coercible = false` → `symbolic`, both sides). The earlier
  unconditional `result = evaluated` spec was unfaithful there (G-PANEL-2) and
  admitted an impl ignoring the dispatch entirely (G-PANEL-1/G-EQ).
- **R legs (rows 3, 5, 6):** the type refinement is the observable bijection
  `a Poly value (is_Poly=True) ↔ MulResult.evaluated`, `a plain non-Poly
  expression ↔ MulResult.symbolic`, plus `Poly(e, *gens) succeeds ↔
  coercible = true` (mapping.md). The actual product carriers (`Poly.mul`,
  `Mul`) are unchanged by the patch; the spec pins only the observable outcome,
  leaving no output component free.
- **G-CONF** mechanically refutes the R/I legs: the Python shadow of the impl is
  diffed against an in-process replica of the POST-PATCH dispatch (with the
  coerce-or-fallback rule) over both operand orders × both coercibility values
  + ≥1e5 fuzzed priority pairs; the precedence rule is checked against Python's
  `>`. **G-AX** validates the A-reference rows against the real repo.
