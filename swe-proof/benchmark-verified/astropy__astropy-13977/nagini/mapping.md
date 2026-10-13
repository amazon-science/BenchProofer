# mapping.md — astropy__astropy-13977

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5250b2442501e6c671c6b380536f1edb352602d1`, states the type
abstraction, and gives the provenance of the classification predicate the deep
model is validated against.

Repo file under change: `astropy/units/quantity.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `dispatch_ufunc(io_overrides, body_raises)` | `Quantity.__array_ufunc__(self, function, method, *inputs, **kwargs)` — `astropy/units/quantity.py:620` (body 639-682) | the modeled changed function (the ufunc dispatcher) |
| `io_overrides: List[int]` | the concatenation `inputs + out_normalized` (gold lines: `inputs_and_outputs = inputs + out_normalized`); one entry per input/output operand | per-operand classification of `type(io).__array_ufunc__` |
| `body_raises: bool` | whether the protected body (`converters_and_unit` → `check_output` → conversions → `super().__array_ufunc__`) raised a `TypeError` or `ValueError` | the recoverable-error flag the new `try/except (TypeError, ValueError)` traps |
| `has_override(io_overrides)` *(deep model — A-reference)* | `not all(getattr(type(io), "__array_ufunc__", None) in ignored_ufunc for io in inputs_and_outputs)` where `ignored_ufunc = (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__)` | pure spec: does at least one operand carry a non-ignored (custom) `__array_ufunc__`? |
| outcome codes `0/1/2` | the three control-flow exits: `0` = return a Quantity result normally; `1` = `return NotImplemented`; `2` = `raise e` (propagate the original error) | the observable result class |

The body callees the new code merely *wraps* but does not change
(`converters_and_unit`, `check_output`, `self._to_own_unit`,
`super().__array_ufunc__`, `self._result_as_quantity`) are abstracted into the
single `body_raises` boolean: the patch does not alter what they compute, only
whether their raising of `TypeError`/`ValueError` is caught and re-dispatched.
The `ValueError` source that motivated the issue is
`astropy/units/core.py:_condition_arg` (line 2604, `raise ValueError("Value not
scalar compatible …")`); the `TypeError` source is the unsupported-operand path
in `converters_and_unit`. Both are reached from inside the protected body.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the operand tuple `inputs + out_normalized` (each element an arbitrary Python object) | `List[int]` of per-operand override flags | element `k` is `1` iff `type(io_k).__array_ufunc__` is NOT in `ignored_ufunc` (a custom override), else `0`. `len` mirrors the operand count. |
| the boolean "the protected body raised `TypeError`/`ValueError`" | `bool` parameter `body_raises` | `True` ↔ the wrapped computation raised one of the two caught classes |
| `return NotImplemented` / `return <Quantity>` / `raise e` | int outcome codes `1` / `0` / `2` | the three mutually-exclusive control-flow exits of the patched function |
| `function.nout`, `kwargs["out"]` tuple normalization | folded into the operand list construction | the gold normalizes `out` to a tuple before concatenation; observationally each output operand becomes one `io_overrides` entry. |

`*inputs`/`**kwargs` packing, the numpy ufunc machinery, and the Quantity
construction are not part of the *changed* decision logic; they are the
unchanged body summarized by `body_raises` and outcome `0`.

## 3. Classification provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `has_override` deep model ↔ the `ignored_ufunc` membership test (A-reference)
**Predicate:** for each operand `io`,
`getattr(type(io), "__array_ufunc__", None) in (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__)`.
The changed decision operation is modeled **deeply** by the `@Pure` predicate
`has_override` over the per-operand flag list; there is **no consumed axiom**.
The deep model is validated equal to the real classification out-of-band by
`axiom_check.py` (G-AX), which constructs representative operands of each kind
and checks the membership outcome:

  - a `Quantity` (its own type) → in `ignored_ufunc` → flag `0`;
  - a plain `np.ndarray` → `np.ndarray.__array_ufunc__` → in `ignored_ufunc` → flag `0`;
  - a Python scalar / object with no `__array_ufunc__` → `None` → in `ignored_ufunc` → flag `0`;
  - a duck type defining its own `__array_ufunc__` (the issue's `DuckArray`,
    the test's `DuckQuantity3`) → a distinct method → NOT in `ignored_ufunc` →
    flag `1`.

`has_override(flags)` returns `True` iff some flag is `1`, i.e.
`not all(flag == 0)`, mirroring the gold's `not all(... in ignored_ufunc ...)`.
Provenance: gold patch hunk `astropy/units/quantity.py` lines 689-700 (the
`except (TypeError, ValueError)` handler); numpy subclassing docs
(https://numpy.org/doc/stable/user/basics.subclassing.html — `__array_ufunc__`
must return `NotImplemented` when it cannot handle the inputs so reflected
operators are tried).

There is no consumed `@ContractOnly` axiom in this bundle: the body callees are
summarized by `body_raises` (their unchanged behaviour is irrelevant to the
decision being verified), and the one genuinely-new operation (the override
classification + the NotImplemented-vs-raise dispatch) is modeled deeply and
G-AX-validated, not axiomatized.

**Soundness check (G-AX):** `axiom_check.py` imports only `numpy` and constructs
objects of each operand kind, computing the real membership predicate exactly as
the gold patch does, and asserts it equals the flag the deep model assigns; it
then drives the full decision (`has_override` + outcome selection) against a
reference transcription of the gold control flow over boundary + fuzzed operand
lists and raise flags. Exit 0 iff sound.
