# mapping.md — symbol binding & type bijection (astropy__astropy-13977)

## Modeled function
| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_dispatchOp` / `problem_spec_dispatchOp` / `correct_dispatchOp` | `Quantity.__array_ufunc__` (the dispatch wrapper / error-recovery tail) | `astropy/units/quantity.py:620-682` @ `5250b2442501e6c671c6b380536f1edb352602d1` |

The patch wraps the entire body of `__array_ufunc__` in a `try` and adds an
`except (TypeError, ValueError)` recovery clause (diff hunk at lines 633-682).
The modeled behavior is exactly the new control decision:

* `try` body completes normally → its return value `result` is handed back
  unchanged (`return self._result_as_quantity(...)` / `return result`);
* `try` body raises `TypeError`/`ValueError` →
  `if not all(getattr(type(io), "__array_ufunc__", None) in ignored_ufunc
  for io in inputs_and_outputs): return NotImplemented else: raise e`.

## Type bijection (used by G-CONF and G-AX)
| Python reality | Lean model |
|---|---|
| outcome of the `try` body: returns a value `r` | `Outcome.completes r` |
| outcome of the `try` body: raises `TypeError`/`ValueError` | `Outcome.fails` |
| the returned object `r` (Quantity / plain array / `None` / `NotImplemented`) | `Result.value r` (abstracted; only value-identity is observed) |
| `NotImplemented` sentinel returned by the recovery clause | `Result.unhandled` |
| the original error `e` re-raised by the recovery clause | `Result.surfacedError` |
| one element of `inputs_and_outputs = inputs + out_normalized` | one `Operand` |
| `getattr(type(io), "__array_ufunc__", None) in ignored_ufunc` (io defers to default ufunc handling: its type supplies no override, or it is `ndarray`/`Quantity`) | `Operand.defersToDefault = true` |
| io supplies its own `__array_ufunc__` (a foreign duck type) | `Operand.defersToDefault = false` |
| `all(... in ignored_ufunc for io in inputs_and_outputs)` | `operands.all (·.defersToDefault)` |
| `not all(...)` ⟹ `return NotImplemented` | `¬ operands.all (·.defersToDefault)` ⟹ `Result.unhandled` |
| `ignored_ufunc = (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__)` | the membership test folded into `defersToDefault` per operand |

`α` (the value type of `Outcome`/`Result`) is the type of the ufunc return
object; the modeled decision is parametric in it (the value is passed through
untouched on the `completes` branch and never inspected on the `fails` branch).

## Callee provenance / flag dependencies
- `converters_and_unit`, `check_output`, `super().__array_ufunc__`,
  `_result_as_quantity`, `_to_own_unit` — UNCHANGED callees that constitute the
  `try` body. The patch does not alter any of them; it only relocates them under
  the `try`. Their composite outcome (returns-a-value vs raises `TypeError`/
  `ValueError`) is taken as the modeled input `inner : Outcome α`, so no
  `axiom <callee>_prop` is consumed (the proof never reasons about HOW the body
  produces its outcome, only about what the wrapper does with it). G-CONF drives
  the real body end-to-end, validating the abstraction.
- Flag dependency: the recovery decision depends only on each operand's
  `__array_ufunc__` slot (whether it is in `ignored_ufunc`). G-CONF fuzzes both
  configurations: operands that defer (plain `Quantity`, `dict`, a duck class
  with no `__array_ufunc__`) and operands that override it (a duck class
  defining `__array_ufunc__`).

## G-CONF fuzz seed
`conf_seed = 20240625` (pinned; `conformance_check.py`).
