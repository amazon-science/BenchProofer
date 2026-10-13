# refinement.md — sympy__sympy-23950

Operation correspondence between `implementation_asSet` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the modeled function returns one of the
object's two stored operands verbatim. Every row is **R** or **I**. The R/I leg
is differential-tested by G-CONF; G-AX is a skip stub (no consumed callee axiom).

## `implementation_asSet` ↔ `Contains.as_set`

The gold patch changes the method body from `raise NotImplementedError()` (no
value produced) to `return self.args[1]` (return the stored set operand).

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `return some c.setArg` | `return self.args[1]` | R | the patched line. `self.args[1]` (the set operand) ↦ `c.setArg : S`; the Python method returns the very object stored as the second constructor argument (object identity), so the result is exactly the unchanged set operand. The `some`/`none` envelope is the §2 exception-vs-value refinement: a produced value ↦ `some _`, a raise (no value) ↦ `none`. The post-patch method always produces a value, so the result is `some c.setArg`. |

The result is the precise observable the F2P test pins: `Contains(x, s).as_set()`
returns `s` (the set operand) for symbol element `x`.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the impl returns `none` — the model of the pre-patch
  body, which raised `NotImplementedError` and produced no set value. The carried
  proof of `correct_asSet` cannot close: `(pure none).run = some c.setArg` is not
  definitionally true (a missing value is never the set operand), so the prepatch
  fails G-VERIFY. (FAIL_TO_PASS: `test_as_set` — `Contains(x, FiniteSet(y)).as_set()
  == FiniteSet(y)`, etc.: pre-patch this raised, so the assertions could not even
  be reached.)
