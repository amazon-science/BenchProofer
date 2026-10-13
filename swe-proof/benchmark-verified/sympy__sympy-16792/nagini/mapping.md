# mapping.md — sympy__sympy-16792

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 09786a173e7a0a488f46dd6000177c23e5d24eed`, states the type
abstraction, and gives the provenance of each axiom / deep-model reference.

Repo file under change: `sympy/utilities/codegen.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `pointer_flags(kinds, present)` | the `argument_sequence` handling loop in `CodeGen.routine` — `sympy/utilities/codegen.py:719-743` (the `for symbol in argument_sequence:` loop, lines 738-743) | the modeled changed function: builds the final ordered argument list to match a user-supplied argument sequence, deciding each argument's array-ness |
| `is_array_kind(k)` | `isinstance(symbol, (IndexedBase, MatrixSymbol))` test introduced by the fix at `sympy/utilities/codegen.py:742` (post-patch) | pure spec: whether a requested symbol is array-like |
| `arg_is_pointer(has_dims)` | `CCodeGen.get_prototype` — `sympy/utilities/codegen.py:911-916` (the `if arg.dimensions or isinstance(arg, ResultBase):` → `"*%s"` branch) | pure spec: the C prototype renders an argument as a pointer (`*name`) iff it carries non-empty `dimensions` |
| `dimensions(s)` *(deep model — A-reference)* | the patch's local helper `def dimensions(s): return [(S.Zero, dim - 1) for dim in s.shape]` (`sympy/utilities/codegen.py:698-700` post-patch); identical to the inlined loop at `codegen.py:706-709` (pre-patch) | pure spec: the dimension-list builder. For any array-like symbol with ≥1 shape entry it yields a NON-EMPTY list; this non-emptiness is the only property the prototype consults. Validated == the real `shape`/dimensions computation by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): in the `KeyError` branch the missing
symbol was wrapped as `InputArgument(symbol)` with NO `dimensions`
(`codegen.py:742` pre-patch), so an array-like argument absent from the
expression got an empty `dimensions` and was rendered as a scalar.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the ordered `argument_sequence` of sympy symbols | `kinds: List[int]` (one tag per requested argument: `0` = scalar `Symbol`, `1` = array-like `IndexedBase`/`MatrixSymbol`) | `kinds[i] == 1` ↔ `isinstance(argument_sequence[i], (IndexedBase, MatrixSymbol))`; `len(kinds)` ↔ `len(argument_sequence)` |
| "does this symbol appear in the wrapped expression?" (i.e. is it a key of `name_arg_dict`, equivalently in `arg_list` built from `symbols`) | `present: List[bool]` (parallel to `kinds`) | `present[i] == True` ↔ `argument_sequence[i] in name_arg_dict` ↔ the symbol occurs free in `expr`/`local_expressions` |
| an `Argument` object's `dimensions` attribute being non-empty | a `bool` "has dimensions" flag per output argument | `dimensions` truthy ↔ flag `True`; the C prototype consults ONLY this truthiness (`codegen.py:913`) |
| the rendered C parameter (`double *x` vs `double x`) | a `bool` "is pointer" per output argument | `*name` emitted ↔ flag `True` (`codegen.py:914`); `name` ↔ `False` (`codegen.py:916`) |

The concrete sympy symbols, shapes, datatypes and names are irrelevant to the
tested behaviour: the F2P test (`test_ccode_unused_array_arg`) observes only
whether the array argument `x` is rendered `double *x` (pointer) or `double x`
(scalar). The behaviour under specification is therefore the per-argument
pointer flag of the generated prototype, as a function of each requested
argument's array-ness and its presence in the expression.

## 3. Callee provenance

### 3.1 `dimensions` deep model ↔ real shape/dimension computation (A-reference)
**Callee:** the dimension-list builder
`[(S.Zero, dim - 1) for dim in s.shape]` (the patch factors it into the local
helper `dimensions(s)`; pre-patch it was the inlined loop at `codegen.py:706-709`).
The changed decision — "give a missing array-like argument its dimensions" — is
modeled **deeply**: the model spells out that an array-like symbol's dimension
list is NON-EMPTY (every `IndexedBase`/`MatrixSymbol` has shape with ≥1 entry,
so the comprehension yields ≥1 tuple), which is the sole property the C
prototype consults (`if arg.dimensions:`). There is no consumed `dimensions`
axiom. The deep model is validated equal to the real computation out-of-band by
axiom_check.py (G-AX): for `MatrixSymbol`/`IndexedBase` instances the real
`dimensions(s)` is a non-empty list, and the real `CCodeGen.get_prototype`
renders such an argument with a leading `*`. Source (post-patch helper, and the
pre-patch inlined form it replaces verbatim):

```python
def dimensions(s):
    return [(S.Zero, dim - 1) for dim in s.shape]
```

`MatrixSymbol('x', m, n).shape == (m, n)` and `IndexedBase(..., shape=sh).shape
== sh` are always non-empty for these types, so `dimensions(s)` is non-empty,
so `arg.dimensions` is truthy, so the prototype emits a pointer.

### 3.2 `arg_is_pointer` ↔ `CCodeGen.get_prototype` (the I/R rendering link)
**Callee:** `CCodeGen.get_prototype` (`codegen.py:894-918`). For each argument it
emits `(ctype, "*name")` when `arg.dimensions or isinstance(arg, ResultBase)`,
else `(ctype, "name")`. For a plain `InputArgument` (never a `ResultBase`) the
sole determinant is `arg.dimensions`. `arg_is_pointer(has_dims) == has_dims`
encodes exactly this. Validated by axiom_check.py (G-AX): the real prototype of
an argument-with-dimensions contains `*`, and one without does not.

**Soundness check (G-AX):** `axiom_check.py` constructs real sympy
`MatrixSymbol`/`IndexedBase`/`Symbol` arguments, runs the real
`CodeGen.routine` + `CCodeGen.get_prototype` (and the end-to-end
`codegen(...)`) on the exact F2P scenario and on fuzzed argument sequences
(array-like and scalar, present and absent in the expression), and asserts that
the rendered prototype marks an argument as a pointer iff it is array-like —
i.e. the deep model `dimensions`/`arg_is_pointer` matches the real callees.
Imports only sympy (the module under change). Exit 0 iff sound.
