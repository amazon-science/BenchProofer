# mapping.md — django__django-14915

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 903aaa35e5ceaa33bfc9b19b7f6da65ce5a91dd4`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `ChoiceValue` | class `ModelChoiceIteratorValue` — `django/forms/models.py:1161` | the wrapper class under change (minimal: only the two touched fields) |
| `ChoiceValue.value` | `ModelChoiceIteratorValue.value` (set in `__init__`, `models.py:1163`) | the wrapped stored lookup value (a prepared primary key) |
| `ChoiceValue.instance` | `ModelChoiceIteratorValue.instance` (set in `__init__`, `models.py:1164`) | the domain object the value was derived from (e.g. a model instance, or `None`) |
| `ChoiceValue.membership_identity(self)` | `ModelChoiceIteratorValue.__hash__(self)` — **added** by the patch (`models.py:1169-1170` post-patch) | the modeled changed method: the wrapper's hash |
| `value_identity(v)` *(axiom — A-consumed)* | the built-in `hash(...)` applied to `self.value` (CPython `object.__hash__`/`int.__hash__`; the `hash(self.value)` call in the new `__hash__`) | unchanged stdlib membership-identity primitive the new method defers to |

The pre-patch state the change addresses (for the refinement audit, not
referenced from the consumer spec view): the class defines `__eq__`
(`models.py:1166-1169`) but **no** `__hash__`. Per the Python data model, a
class that overrides `__eq__` without defining `__hash__` has its `__hash__`
set to `None`, making instances unhashable; absent that rule the inherited
`object.__hash__` is an identity hash keyed on the *object* (the derived
instance), not on the wrapped `value`. Either way the pre-patch membership
identity is governed by the object/instance, not by `value` — which is what
`model_prepatch.py` reproduces (`return value_identity(self.instance)`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.value` — a prepared primary key (typically an `int`; CheckboxSelectMultiple/widget compares it against dict/array members) | `int` | the F2P test wraps `self.c1.pk` / `self.c2.pk`, which are auto-increment **integers**; modeled directly as `int` |
| `self.instance` — the derived model object (a `Category` instance, or `None`) | `int` | an opaque integer standing for the object's identity; the operation never inspects its structure, only whether the hash depends on it. Distinct objects ↔ distinct ints; `None` ↔ a distinct int. Only the *dependence* of the result on this field is observable, and the spec forbids it. |
| `hash(self.value)` (built-in) | `value_identity(self.value)` (`@Pure @ContractOnly`) | the membership-identity primitive on the bare value; see §3 |
| return value of `__hash__` (a Python hash `int`) | `int` | identical (hash values are integers) |

`self.instance` is held at fractional permission (`Acc(..., 1/2)`, Required AND
Ensured) and the result is forbidden from depending on it — a wrong impl cannot
satisfy the postcondition by reading or overwriting it (directive 5).

The precondition also carries `Requires(MustTerminate(1))`: the real method is
a bounded, straight-line delegation to the unchanged stdlib primitive, so it
terminates on every input. Nagini's default is partial correctness, under
which a diverging impl (`while True: pass`) satisfies every value
postcondition vacuously while its faithful real patch (a `__hash__` that
hangs) would freeze every membership lookup and never pass the F2P test; the
termination obligation pins the gold's actual behaviour and closes that
verify⇏correct class.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `value_identity` ↔ built-in `hash` (A-consumed)
**Callee:** the CPython built-in `hash(x)`, which for the wrapped value `x =
self.value` dispatches to `type(x).__hash__` (for the integer keys the F2P
test uses, `int.__hash__`). Docs:
https://docs.python.org/3/reference/datamodel.html#object.__hash__ and
https://docs.python.org/3/library/functions.html#hash.

The new `__hash__` is literally `return hash(self.value)` — it computes the
membership identity of the **bare wrapped value** and returns it unchanged.
The axiom encodes only the property the spec consumes: `value_identity` is a
**fixed pure (deterministic) function of its single argument** — the same value
always hashes to the same integer, and the result depends on `v` and nothing
else. As a `@Pure @ContractOnly` with no `Ensures`, the contract is the
weakest possible: an uninterpreted deterministic function of `v`. It
deliberately does **not** assert global injectivity (`hash` may collide on
distinct inputs in general), which would be an over-claim.

Why this is sufficient for the two tested obligations:
- *Equal value ⇒ equal hash, independent of the derived object* (F2P assertion
  1: `hash(value_1) == hash(ModelChoiceIteratorValue(c1.pk, None))`): the spec
  fixes `Result() == value_identity(self.value)`, a function of `value` only,
  so two wrappers with the same `value` and different `instance` (here, `c1`
  vs `None`) get the same hash. Pinned by the postcondition; no injectivity
  needed.
- *Distinct values ⇒ distinct hash* (F2P assertion 2: `hash(value_1) !=
  hash(value_2)`): the spec yields `value_identity(c1.pk)` vs
  `value_identity(c2.pk)`. `c1.pk` and `c2.pk` are distinct positive
  auto-increment integers; for such ints `hash(n) == n` in CPython, so the
  hashes differ. This is a property of the **real** `hash` on the specific
  test inputs, validated out-of-band by G-AX (axiom_check.py), NOT claimed in
  the axiom.

**Conformance check (G-CONF):** `conformance_check.py` runs the
contract-stripped impl region against the real patched
`ModelChoiceIteratorValue.__hash__` in-container on >= 1e5 inputs
(boundary + fuzz). Pinned fuzz seed: **14915** (the instance number).

**Soundness check (G-AX):** `axiom_check.py` runs the real built-in `hash` and
asserts (a) determinism — `hash(v) == hash(v)` on every probed value, including
the F2P pks, boundary ints (0, 1, -1, large), and fuzz; (b) the F2P
non-collision — `hash(c1.pk) != hash(c2.pk)` for the auto-increment pk pattern
(and across many distinct positive int pairs); and (c) the eq/hash consistency
the wrapper relies on — for the integer keys used, `hash(a) == hash(b)`
whenever the wrapped values are equal. It imports only the standard library;
nothing repo-specific. Exit 0 iff sound.
