# mapping.md — astropy__astropy-13977

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5250b2442501e6c671c6b380536f1edb352602d1`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `astropy/units/quantity.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `applyUfunc (call : Int)` | `Quantity.__array_ufunc__(self, function, method, *inputs, **kwargs)` — `astropy/units/quantity.py:620` (body 638-682) | the modeled changed function (the numpy-ufunc dispatch wrapper) |
| `coreUfunc` *(opaque — A-reference)* | the UNCHANGED body of `__array_ufunc__`, lines 639-682 @ base_commit (compute converters/unit, normalize `out`, convert inputs, call `super().__array_ufunc__`, wrap result). Consults `converters_and_unit`, `check_output`, `super().__array_ufunc__`, `_result_as_quantity`, `_to_own_unit` — all unchanged. | pure spec: the success/raise outcome of the unchanged computation |
| `canDefer` *(opaque — A-reference + I)* | the deferral predicate the change introduces: `not all(getattr(type(io), "__array_ufunc__", None) in ignored_ufunc for io in inputs + out_normalized)`, where `ignored_ufunc = (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__)` (post-patch lines 700-707) | pure spec: whether some participating operand advertises its own ufunc handler |
| `ufuncSpec` | the post-patch control flow (the `try` body's outcome dispatch + the `except (TypeError, ValueError)` recover/re-raise) | pure spec: outcome of the whole dispatch |
| `UfuncErr.recoverable` | a `TypeError` or `ValueError` — exactly the two the `except (TypeError, ValueError)` clause catches | the recoverable failure shape |
| `UfuncErr.fatal` | any other raised exception (never caught by the clause; propagates unchanged) | the non-recoverable failure shape |
| `Outcome.deferred` | the `NotImplemented` sentinel returned by the recover branch | the "operation not implemented" return |
| `Outcome.result v` | a normally-returned value of the dispatch (a `Quantity`/array, possibly the body's own `NotImplemented`/`None`) | a normal (non-deferred) return |

The per-operand handler lookup `getattr(type(io), "__array_ufunc__", None)` and the
membership in `ignored_ufunc` are UNCHANGED Python attribute-resolution
primitives; the `try`/`except` wrapper, the `inputs + out_normalized`
concatenation, the `all(...)` aggregation, and the `NotImplemented` return are
the operations the change ADDS (modeled directly — §A2/A3 of refinement.md).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the ufunc-call descriptor `(self, function, method, inputs, kwargs)` | `call : Int` | opaque handle; only the two observations `coreUfunc call` (its outcome) and `canDefer call` (its deferral classification) are ever consulted — never decomposed. G-CONF bridges by replaying each real call and reading both observations. |
| a normally-returned value (a `Quantity`/array view, or the body's own `None`/`NotImplemented`) | `Outcome.result (v : Int)`, `v` an opaque `Int` handle | the change returns the success value VERBATIM, so its content is never inspected; modeled as an opaque handle. |
| the `NotImplemented` sentinel produced by the recover branch | `Outcome.deferred` | the distinguished "defer to a reflected operator" return the issue asks for. |
| a raised `TypeError`/`ValueError` | `Except.error UfuncErr.recoverable` | the two exception classes the recover clause catches. |
| any other raised exception | `Except.error UfuncErr.fatal` | never caught; propagates identically pre/post. |
| "the dispatch returned X" vs "the dispatch raised E" | `Except.ok X` vs `Except.error E` | `ok` ↔ returned, `error` ↔ raised. |

Operands are modeled as opaque handles (decidable-equality `Int` domain); no
arithmetic on them is observed — only the two boolean/outcome observations. This
is a control-flow bundle, so no string/float precision modeling is needed.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `coreUfunc` ↔ the unchanged `__array_ufunc__` body (A-reference)
**Callee:** the body of `Quantity.__array_ufunc__` at base_commit (lines 639-682),
left BYTE-FOR-BYTE unchanged by the patch — the patch only wraps it in `try:` and
appends an `except (TypeError, ValueError):` clause. It is modeled `opaque` with
NO asserted `ensures`: the change assumes nothing about WHICH value the body
returns, only how a success vs a recoverable raise is handled.

The body raises on incompatible inputs:
* an operand whose unit is convertible but different and which is itself not a
  plain number/array (the issue's duck type) → the input-conversion step
  (`converter(input_)`, via `core._condition_arg`) raises **`ValueError`**;
* a wholly unsupported operand (e.g. a `dict`) → `converters_and_unit` raises
  **`TypeError`** ("Unsupported operand type(s) for ufunc …").

Both are subclasses of the `(TypeError, ValueError)` the recover clause catches
(`UfuncErr.recoverable`). On compatible inputs the body returns a value without
raising (`Except.ok`).

### 3.2 `canDefer` ↔ the deferral classification (A-reference + I)
**Predicate:** `not all(getattr(type(io), "__array_ufunc__", None) in
(None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__) for io in
inputs + out_normalized)`. The per-operand attribute lookup is the UNCHANGED
Python attribute machinery (A-reference); the `inputs + out` concatenation, the
`all(...)` aggregation and its negation are the I ops the change adds, replayed
verbatim by G-CONF's shadow. `canDefer` is `True` exactly when some participating
operand supplies its own `__array_ufunc__` distinct from `ndarray`'s and from the
`Quantity`'s own — i.e. some other object could still handle the ufunc via a
reflected operator (the issue's scenario), so deferral is warranted.

On the F2P operands: a `DuckQuantity3` input (defines `__array_ufunc__`) ⇒
`canDefer = True` ⇒ recoverable raise becomes `NotImplemented`; a `dict` input
(no `__array_ufunc__`) ⇒ `canDefer = False` ⇒ the recoverable raise is re-raised
unchanged (the PASS_TO_PASS `test_non_number_type` still gets its `TypeError`).

**Soundness check (G-AX):** `axiom_check.py` reconstructs the unchanged body
standalone and the deferral classification, runs them in-container on boundary
operands (compatible Quantity pair; incompatible duck with custom handler;
unsupported `dict`; list-valued duck) plus randomized fuzz, asserting (a)
`coreUfunc` raises exactly a `TypeError`/`ValueError` (recoverable) on the
incompatible operands and returns without raising on compatible ones, and (b)
`canDefer` matches the real classification (True for duck operands, False for the
`dict`). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13977`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds replays
the unchanged body (`coreUfunc`, A-reference → real) and the deferral predicate
(`canDefer`, A-reference per-operand lookups + I aggregation → real) and
transliterates the NEW dispatch control flow (success → return; recoverable
raise → defer iff `canDefer` else re-raise; other raise → propagate). The oracle
is the patched `Quantity.__array_ufunc__` itself.
