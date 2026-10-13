# refinement.md — sympy__sympy-24539

Operation correspondence between `implementation_asExpr` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

The modeled function is `PolyElement.as_expr(*symbols)`. The patch reorders the
symbol-selection / error-raising logic so that a correctly-sized caller list is
actually used. The only callee, `expr_from_dict` (via `as_expr_dict`), is
UNCHANGED by the patch and is **A-reference**: it is left as the real repo
callee in the G-CONF shadow and never has a property consumed by the proof. No
`axiom … _prop` is declared (G-AX is a skip stub).

## `implementation_asExpr` ↔ the body of `PolyElement.as_expr`

Type bijection (mapping.md): the variadic `*symbols` Python tuple ↦ a Lean
`List Symb`; the empty tuple ↦ `symbols.isEmpty`; `self.ring.ngens` ↦ `ngens`;
`self.ring.symbols` ↦ `ringSymbols`; a raised `ValueError` ↦ `Except.error ()`;
the returned `Expr` ↦ `Except.ok (exprFromDict d gens)`. A generator is
`Symb.named name` when it carries a name and `Symb.other tag` when it does
not: a ring's generators are arbitrary expressions (`_parse_symbols`,
`rings.py:181-192`), of which only some are named symbols, so a generator is
not reconstructible from a string — and nothing on the modeled surface reads
one, since the surface decides only WHICH list of generators reaches the
callee.

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut gens := symbols` | (post-patch) `symbols` kept as the working list of generators | R | initial value of the generator list = the caller-supplied list |
| `if symbols.isEmpty then gens := ringSymbols` | `if not symbols: symbols = self.ring.symbols` | R/I | no-symbols branch selects the ring's own symbols; `not symbols` ↦ `symbols.isEmpty` |
| `else if symbols.length ≠ ngens then return .error ()` | `elif len(symbols) != self.ring.ngens: raise ValueError(...)` | R/I | wrong-count branch rejects; `len ≠ ngens` ↦ `symbols.length ≠ ngens`; `raise ValueError` ↦ `Except.error ()` |
| (implicit else: keep `gens := symbols`) | (implicit else: `symbols` unchanged — the correctly-sized caller list) | R | THE FIX: a correctly-sized caller list is used, not overwritten |
| `return .ok (exprFromDict d gens)` | `return expr_from_dict(self.as_expr_dict(), *symbols)` | A-reference | unchanged callee; `gens` is the selected symbol list; left as the real callee in G-CONF |

The observable the F2P test pins is the returned expression `f.as_expr(*symbols)`
(or the `ValueError` it raises): with a correctly-sized caller list, the result
must be built from *those* symbols (the issue's `f.as_expr(U, V, W) == g`).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the impl mirrors the pre-patch control flow — the
  `else` branch always overwrites `gens` with `ringSymbols`, so a correctly-sized
  caller list (`¬ symbols.isEmpty ∧ symbols.length = ngens`) is ignored. The
  carried gold proof of `correct_asExpr` fails to close on `refine_2` (clause 2
  of the spec): `exprFromDict d ringSymbols` is not definitionally equal to
  `exprFromDict d symbols`. This is exactly FAIL_TO_PASS `test_PolyElement_as_expr`
  (`f.as_expr(U, V, W) == g`).
