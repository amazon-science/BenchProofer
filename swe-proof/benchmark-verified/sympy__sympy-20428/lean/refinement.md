# refinement.md — sympy__sympy-20428

Operation correspondence between `implementation_nonzero` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the changed operation (the zero-test) is
modeled DEEPLY by the input flags. Every row is **R**, **A-reference**, or
**I**. The R/I legs and the A-reference are differential-tested by G-CONF; G-AX
is a skip stub (no consumed callee axiom).

## `implementation_nonzero` ↔ `Expression.__bool__`

The gold patch turns

```python
def __bool__(f):
    return f.ex != 0          # PRE-PATCH: syntactic non-zero test
```

into

```python
def __bool__(f):
    return not f.ex.is_zero   # POST-PATCH: semantic (determined) zero test
```

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `return !e.isMathZero` | `return not f.ex.is_zero` | A-reference | `f.ex.is_zero` (the assumptions-system determined-zero query) is modeled deeply by `isMathZero` (`true` iff `f.ex.is_zero is True`; both `False` and `None` ↦ `false`, matching `not None == True`). `not …` ↦ `!…`. Validated == real `not f.ex.is_zero` by G-CONF over the three-valued `is_zero` domain. |
| Boolean result | Python `bool` returned by `__bool__` | R | `True`/`False` ↦ `true`/`false` |

The pre-patch op `return f.ex != 0` corresponds to `return !e.isLiteralZero`
(`f.ex != 0` is the negation of the *syntactic* `f.ex == 0`, i.e.
`!isLiteralZero`); it appears only in `Solution_prepatch.lean`.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the nonzero test returns `!isLiteralZero` — truthy
  unless the value is *syntactically* `0`. For the issue's coefficient
  (`isLiteralZero = false`, `isMathZero = true`: written non-trivially but
  mathematically zero) the pre-patch returns `true` where the spec demands
  `false`. The (unconditional) theorem `∀ e, !isLiteralZero = !isMathZero` is
  therefore genuinely **false** — the witness `{ isLiteralZero := false,
  isMathZero := true }` refutes it — so NO proof can close `correct_nonzero`
  against the buggy impl (the carried gold proof's `rfl` already fails: exit 1).
  This is the single fixed behavior; FAIL_TO_PASS
  `test_issue_20427` exercises it via `Poly(...).clear_denoms()` /
  `f == Poly(0, x, domain='EX')`, which relies on the zero coefficient being
  stripped from the DMP.
