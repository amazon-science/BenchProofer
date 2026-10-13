# mapping.md — django__django-14915

Binds `Solution.lean` symbols to the repo at
`base_commit = 903aaa35e5ceaa33bfc9b19b7f6da65ce5a91dd4`.

Repo file under change: `django/forms/models.py`. The gold patch ADDS a
`__hash__` method to `class ModelChoiceIteratorValue` (inserted after `__str__`,
before `__eq__`, around `django/forms/models.py:1166`), with body
`return hash(self.value)`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `choiceValueHash (value : Int)` | `ModelChoiceIteratorValue.__hash__(self)` — inserted into `class ModelChoiceIteratorValue` (`django/forms/models.py:1159`) by the patch; body `return hash(self.value)` | the modeled (patched) method |
| `value` | `self.value` — the wrapped underlying value (`__init__` stores `self.value = value`, `models.py:1161`) | the underlying value the wrapper carries |
| `valueHash value` | `hash(self.value)` — the builtin `hash()` applied to the wrapped value | the UNCHANGED library hashing of the wrapped value |
| `h` | the method's return value (`int`, the object's hash) | the wrapper's hash |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.value` : in the F2P test this is `Category.pk` (a primary key, an integer) | `Int` `value` | the pk integer ↔ Lean `Int`. The fix is value-generic; the test exercises integer pks. |
| `hash(self.value)` : `int` (CPython hash of the value) | `valueHash value : Int` | exact (`hash` returns a Python `int` ↔ Lean `Int`); modeled OPAQUE — see §3 |
| return value : `int` | `h : Int` | exact |

The model abstracts the wrapped value to `Int` because the patched body uses it
ONLY through `hash(self.value)`, and the F2P test wraps integer primary keys
(`self.c1.pk`, `self.c2.pk`). The KEY property the fix establishes — and the
spec pins — is that the wrapper's hash is a deterministic FUNCTION of its
wrapped value: equal values hash equal (`h = valueHash value`).

## 3. Callee provenance — the value hash (A-consumed, OPAQUE)

`hash(self.value)` is the builtin `hash()` applied to whatever value the wrapper
carries (`django/forms/models.py`, the patched `__hash__` body). Its concrete
output is **implementation- and salt-dependent** (CPython's `hash()` for `str`
is randomized per-process via `PYTHONHASHSEED`; for `int` it is
implementation-defined modular reduction). The spec therefore does NOT claim any
concrete hash value.

The value hash is modeled as a fully OPAQUE free function
`opaque valueHash : Int → Int` with NO asserted contract about its return value.
The spec pins only the STRUCTURE the fix introduces: `h = valueHash value` — the
object's hash is exactly the hash of its wrapped value (a deterministic function
of the value, hence equal values ⇒ equal hashes).

It is declared `opaque` rather than `axiom` because it is referenced inside the
executable `do` block (LESSONS.md: a bare `axiom` in a `do` block fails codegen;
`opaque` keeps the value abstract for the proof yet computable).

Rationale (SPEC_GUIDE §0.7 — weakest contract): leaving the value hash opaque is
the weakest possible contract. Any real `hash()` (salt-dependent, version-
dependent) satisfies it vacuously, because nothing is asserted about its value;
only its functional dependence on `value` is used. There is therefore NOTHING
for an axiom_check to validate — **no `axiom_check.py`; G-AX skips.**

## 4. G-CONF — conformance is SKIPPED (conf_skip=true)

The impl region is all-A-tagged: the result is exactly `valueHash value`, the
opaque value hash. There is no R/I leg to differential-test. Moreover, the
discriminator — the concrete output of `hash()` — has no DB-free, deterministic,
cross-language shadow: CPython `hash()` is salt-/implementation-dependent and not
reproducible without the process's `PYTHONHASHSEED`. Per WORKER_PROMPT, a
`status=skip` conformance stub is shipped and `meta.json conf_skip=true`.
