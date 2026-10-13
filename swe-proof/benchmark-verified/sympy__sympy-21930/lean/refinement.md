# refinement.md — sympy__sympy-21930

Maps every operation of the three `implementation_*Markup` skeletons to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real
callee/operation by G-AX / G-CONF), **I** (identical concrete op).

The fix wraps each of the three `_latex` renderers' output in one outer brace
pair, so the rendered token is a single group and a following superscript binds
to the whole token instead of producing an ill-formed double superscript.

## `implementation_tensorMarkup` ↔ `AntiSymmetricTensor._latex`

| # | Lean op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `for i in upper do up := up ++ i` | `"".join([i.name for i in self.args[1]])` | A-reference | empty-string join of the upper index names, modeled deeply as the accumulator loop / `joinNames`. Validated == `"".join` by G-AX. |
| 2 | `for i in lower do lo := lo ++ i` | `"".join([i.name for i in self.args[2]])` | A-reference | same, for the lower index block. |
| 3 | `return "{" ++ sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}}"` | `return "{%s^{%s}_{%s}}" % (self.symbol, ..., ...)` | I | identical concrete string assembly: splice `sym`, `up`, `lo` into the template AND enclose in one outer brace pair. |

## `implementation_bosonCreatorMarkup` ↔ `CreateBoson._latex`

| # | Lean op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `return "{b^\\dagger_{" ++ name ++ "}}"` | `return "{b^\\dagger_{%s}}" % self.state.name` | I | identical concrete string assembly: splice the state name and enclose in one outer brace pair. |

## `implementation_fermionCreatorMarkup` ↔ `CreateFermion._latex`

| # | Lean op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `return "{a^\\dagger_{" ++ name ++ "}}"` | `return "{a^\\dagger_{%s}}" % self.state.name` | I | identical concrete string assembly: splice the state name and enclose in one outer brace pair. |

## Type refinements (R)
- `str` index/symbol/state names ↔ Lean `String` (value-level; `%s` splice ↔
  `++`). No code-point-level operation is performed, so `String` (not
  `List Char`) is the faithful carrier.
- `self.args[k]` (a tuple of index objects) ↔ `List String` of their `.name`s;
  the only observable contribution of each index to the result is its name.
- `printer` argument is never read; not modeled (no op).

No changed op is inexpressible: the entire fix is concrete string assembly, so
every changed op is **I**, and the only sub-operation (the name join) is an
**A-reference** modeled deeply (`joinNames`). No `axiom` is consumed
(`conf_skip=false`; all impl rows are I/A-reference and are differential-tested by
G-CONF, with the join also checked by G-AX).

## Independently-fixed behaviors → prepatch variants
Three independently-observable fixed behaviors, one prepatch each (each replaces
the relevant renderer with its bare, brace-less pre-state token; the carried gold
proof cannot close on the discriminating outer-brace clause):
- `Solution_prepatch_1.lean` — indexed-symbol renderer emits `<sym>^{..}_{..}`
  with no outer braces (F2P `test_Tensors`).
- `Solution_prepatch_2.lean` — bosonic token emits `b^\dagger_{..}` with no outer
  braces (F2P `test_create`, `test_issue_19661`).
- `Solution_prepatch_3.lean` — fermionic token emits `a^\dagger_{..}` with no
  outer braces (F2P `test_create_f`, `test_commutation`, `test_NO`).
