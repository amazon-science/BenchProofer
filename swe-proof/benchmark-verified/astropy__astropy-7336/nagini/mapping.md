# mapping.md — astropy__astropy-7336

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 732d89c2940156bdc0e200bb36dc38b5e424bcba`, states the type
abstraction, and gives the provenance of the deep-model references (validated
by axiom_check.py / G-AX).

Repo file under change: `astropy/units/decorators.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `finalize_return(ret, target)` | the return-finalisation tail of `QuantityInput.__call__.wrapper` — `astropy/units/decorators.py:223-226` (`if wrapped_signature.return_annotation …: return return_.to(…) else: return return_`) | the modeled changed behaviour: how the wrapper finalises the wrapped function's return value given the declared return target |
| `convert_unit(q_unit, target)` *(deep model — A-reference)* | `astropy.units.Quantity.to(unit)` — `astropy/units/quantity.py:821` (called as `return_.to(wrapped_signature.return_annotation)`, `decorators.py:224`) | pure spec: the unit of a quantity after converting it into `target`; deep model of the unchanged conversion callee the wrapper invokes |
| `ret: RetVal` | the local `return_` (`decorators.py:222`), i.e. the value the wrapped function returned | the value being finalised; `is_none` ↔ "`return_` is the Python `None` object", `unit` ↔ its current unit id when it is a `Quantity` |
| `target: int` | `wrapped_signature.return_annotation` (`decorators.py:223`) | the declared return target, abstracted to an int code |
| `TARGET_UNSPECIFIED()` | `inspect.Signature.empty` (the "no return annotation" sentinel) | the unspecified sentinel |
| `TARGET_NOVALUE()` | the literal `None` return annotation (`-> None`) | the "declared to produce nothing" target |
| `is_genuine_target(target)` | the post-fix guard `return_annotation not in (inspect.Signature.empty, None)` | true iff a genuine unit conversion target was declared |

The pre-patch repo guard the change replaces (for the refinement audit, not
referenced from the consumer spec view): `if wrapped_signature.return_annotation
is not inspect.Signature.empty:` (`decorators.py:223`), which excludes only the
unspecified sentinel and therefore attempts `return_.to(None)` on a `-> None`
function — the bug.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `wrapped_signature.return_annotation` — one of `inspect.Signature.empty`, `None`, or a unit/physical-type object | `target: int` | `inspect.Signature.empty` ↔ `TARGET_UNSPECIFIED()` (`-1`); the `None` annotation ↔ `TARGET_NOVALUE()` (`-2`); any genuine unit object ↔ any int with `is_genuine_target(target)` true (its identity is abstracted to a distinct id) |
| the returned object `return_` (a `Quantity`, or the `None` object) | `ret: RetVal` with fields `is_none: bool`, `unit: int` | `return_ is None` ↔ `ret.is_none`; the current unit of a `Quantity` return ↔ `ret.unit` (a genuine unit id, `!= NO_UNIT()`); the `None` object carries no unit ↔ `ret.unit == NO_UNIT()` |
| `return_.to(annotation)` → a new `Quantity` in unit `annotation` | `convert_unit(ret.unit, target)` → `target`; result wrapped as `RetVal(False, target)` | `q.to(U).unit == Unit(U)` ↔ `convert_unit(_, target) == target` and the result is a genuine quantity (`is_none == False`) |
| `return return_` (the pass-through branch) | `RetVal(ret.is_none, ret.unit)` | observationally identical: the only observables the F2P/P2P tests read are `result is None` (↔ `is_none`) and `result.unit` (↔ `unit`); the real wrapper returns the *same* object, the model an equal fresh one — equal on every observed field (refinement.md A4) |

`inspect`/object identity are not Nagini-expressible, so the annotation is
abstracted to an int code and the return value to a two-field record carrying
exactly the observed properties.

## 3. Callee provenance — deep-model references (A-reference; G-AX) — no consumed axiom

The axioms region of model.py is **empty**: the spec consumes no `@ContractOnly`
contract inside any `Ensures`. The changed behaviour is the wrapper's
*decision* (convert vs. pass through), modelled deeply by the verified
`finalize_return` plus the pure `convert_unit`. Two A-references are validated
against the real callees by `axiom_check.py` (G-AX), not consumed as axioms:

### 3.1 `convert_unit` ↔ `Quantity.to` (A-reference)
**Callee:** `astropy.units.Quantity.to(unit, equivalencies=[])`
(`astropy/units/quantity.py:821`):
```python
def to(self, unit, equivalencies=[]):
    unit = Unit(unit)
    return self._new_view(self._to_value(unit, equivalencies), unit)
```
It returns a NEW `Quantity` whose `.unit` is exactly `Unit(unit)` — the target.
This is the unchanged conversion the wrapper invokes when a genuine return
target is declared. `convert_unit(q_unit, target) == target` encodes precisely
that the converted quantity's unit is the target unit. axiom_check.py asserts
`q.to(target).unit == target` over a range of (quantity, target) pairs.

### 3.2 `finalize_return` decision ↔ `quantity_input` wrapper (A-reference)
**Callee:** the return-finalisation of `astropy.units.quantity_input`'s wrapper
(`astropy/units/decorators.py:223-226`), **post-fix** (the face of the spec):
the gold patch makes the guard `return_annotation not in (inspect.Signature.empty,
None)`. So a genuine unit target converts; both `inspect.Signature.empty` (no
annotation) and `None` (`-> None`) pass the return value through untouched.
axiom_check.py builds real decorated functions and asserts:
* `def f(x: u.arcsec) -> u.deg` → result `.unit == u.deg` (convert);
* `def ctor(x: u.V) -> None: return None` → result `is None` (pass through —
  the F2P behaviour `test_return_annotation_none`);
* `def h(x: u.arcsec)` (no return annotation) → result `.unit == u.arcsec`
  (pass through).

**Flag/configuration dependency:** none. `Quantity.to` is called with the
default `equivalencies=[]` here; the wrapper's equivalencies affect only the
argument-side checks, not the return-target decision the spec pins.

**Conformance (G-CONF):** `conformance_check.py` runs the contract-stripped
impl region differentially against the real patched wrapper in-container
(>= 1e5 Requires-satisfying inputs; boundary cases + fuzz, pinned fuzz seed
7336).

**Soundness check (G-AX):** `axiom_check.py` imports only `astropy.units` (the
package the gold patch edits) and the standard library. The G-AX driver applies
the gold patch first, so the wrapper under test is the fixed callee. Under the
buggy pre-fix wrapper the `-> None` check raises `AttributeError`
(`None.to(None)`), so the script fails — itself a witness that the deep model
matches only the fixed behaviour. Exit 0 iff every observation matches the deep
model.
