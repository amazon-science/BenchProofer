# mapping.md — sympy__sympy-14711

## Symbol binding (file:line @ base_commit c6753448b5c34f95e250105d76709fe4d349ca1f)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_vectorAdd` / `problem_spec_vectorAdd` / `correct_vectorAdd` | `Vector.__add__` | `sympy/physics/vector/vector.py:58-60` (post-patch 58-62) |
| `AddOperand` (pure helper) | the right operand `other` of `__add__`, classified by shape | `vector.py:58` (`other`) |
| `isAdditiveZero` (pure helper) | the added guard predicate `other == 0` | `vector.py:59` (post-patch) |
| `_check_vector` (folded into `AddOperand` classification) | `_check_vector(other)` | `vector.py:723-726` |
| `Vector(self.args + other.args)` (folded into the append result) | the `Vector` constructor over the combined argument list | `vector.py:26-53`, `60` |

The modeled function is `Vector.__add__`. It is the only behavior the patch
changes and the only behavior the FAIL_TO_PASS test (`test_Vector`) newly
observes:

- `test_Vector` adds the assertion `A.x + 0 == A.x` — adding the scalar `0` to a
  basis vector must return that vector unchanged (it previously raised
  `TypeError` via `_check_vector`).

### What the function does (base_commit, pre-patch — buggy)

```python
def __add__(self, other):
    """The add operator for Vector. """
    other = _check_vector(other)              # raises TypeError if not a Vector
    return Vector(self.args + other.args)     # append component (arg) lists
```

`_check_vector` raises `TypeError('A Vector must be supplied')` for any `other`
that is not a `Vector`. The scalar `0` is therefore rejected, so
`sum([N.x, 0*N.x])` (which seeds the running sum with the int `0`) and `N.x + 0`
both raise. The post-patch adds a leading `if other == 0: return self` guard so
the additive identity returns the vector unchanged.

A `Vector` carries `self.args`, a list of `(measure-number-matrix, frame)`
pairs. `__add__` concatenates the two `args` lists and hands them to the
`Vector` constructor (which sums duplicate-frame entries and drops zero
entries — UNCHANGED by the patch, and orthogonal to the additive-identity fix).

### Lean modeling

- A vector is modeled by its component (argument) list, abstracted to `List Int`
  (the concrete component payload is irrelevant to the additive-identity fix; the
  fix is about WHICH operands are accepted and that the identity is a no-op).
- `AddOperand` classifies the right operand by the shape the fix distinguishes:
  `vector args` (`other` is a `Vector`, carried by its arg list), `scalarZero`
  (`other` is the scalar `0`, i.e. `other == 0` true and not a `Vector`),
  `nonVector` (any other value `_check_vector` would reject).
- `isAdditiveZero` is the added guard `other == 0`. `other == 0` is true for the
  scalar `0` (`.scalarZero`) and, via `Vector.__eq__`, for an empty-arg vector
  (the zero vector, `.vector []`); both map to the identity branch. For
  `.vector []` the identity result `selfArgs` coincides with the append result
  `selfArgs ++ [] = selfArgs`, so the overlap introduces no disagreement
  (refinement.md op 1).
- The result is `Except Unit (List Int)`: `Except.error ()` models the
  `TypeError` raise from `_check_vector`; `Except.ok (selfArgs ++ otherArgs)`
  models the appended component list handed to the `Vector` constructor;
  `Except.ok selfArgs` models returning `self` unchanged on the identity branch.
- The post-patch decision is `problem_spec_vectorAdd`; the impl is the
  `Id.run do` skeleton mirroring the guard-then-append/raise control flow. The
  pre-patch impl drops the leading guard, so `.scalarZero` falls through to the
  `Except.error ()` path — the original bug.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `other` is a `Vector` with argument list `a` | `AddOperand.vector a` | `Vector(args) ↔ .vector args`; component payload abstracted to `Int` tokens |
| `other` is the scalar `0` | `AddOperand.scalarZero` | identity |
| `other` is any other value | `AddOperand.nonVector` | identity (everything `_check_vector` rejects and that is not `== 0`) |
| `self.args` | `selfArgs : List Int` | the vector's component (argument) list |
| returns `Vector(self.args + other.args)` | `Except.ok (selfArgs ++ otherArgs)` | combined argument list |
| returns `self` (identity branch) | `Except.ok selfArgs` | unchanged argument list |
| raises `TypeError` (`_check_vector`) | `Except.error ()` | the type error |

The function's observable result is either the produced vector (modeled by its
component list) or a raised `TypeError`; we model it as
`result : Except Unit (List Int)`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — whether the
  additive identity is accepted and is a no-op — is modeled DEEPLY and
  structurally over the operand shape (`AddOperand`); SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed decision. The `axioms` region is empty
  and **G-AX skips**.
- `_check_vector` (the operand validator that raises) is UNCHANGED by the patch;
  its net effect (identity on a `Vector`, `TypeError` otherwise) is folded into
  the `AddOperand` classification and the `.nonVector → Except.error` leg. Not
  separately modeled.
- The `Vector` constructor (`Vector.__init__`: sum duplicate-frame entries, drop
  zero entries) is UNCHANGED by the patch and orthogonal to the
  additive-identity fix; the modeled value is the argument list passed to it
  (`self.args + other.args`), which is what the fix affects. Its
  duplicate/zero-collapsing is not part of the observed behaviour the patch or
  F2P test changes and constrains no output component the spec leaves free.
- No flag dependencies.

## G-CONF fuzz seed

Pinned LCG seed: **14711** (see `conformance_check.py` `SEED`). Corpus:
randomized `AddOperand`s crossing all three shapes — `vector` operands with
randomized component lists, the scalar zero, and non-vector values — paired with
randomized `selfArgs`, over ≥1e5 fuzzed inputs, with emphasis on the
discriminating category (the scalar zero, which must yield `Except.ok selfArgs`,
not `Except.error`). Hand-picked edge cases pin the F2P scenario
(`A.x + 0 == A.x`: a one-component vector plus scalar zero returns the
one-component vector) and the empty-vector overlap (`.vector []`).
