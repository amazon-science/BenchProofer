# mapping.md — astropy__astropy-7166

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 26d147868f8a891a6009a25cd6a8576d2e1bd747`, states the type
abstraction, and gives the provenance of each unchanged callee whose result the
model abstracts (validated by axiom_check.py / G-AX).

Repo file under change: `astropy/utils/misc.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `apply_inheritance(m)` | the body of the `for key, val in dct.items()` loop in `InheritDocstrings.__init__` — `astropy/utils/misc.py:529-538` (the `if`-guard at 530-532 and the inner MRO-walk assignment at 533-538) | the modeled changed decision: one loop iteration / one member |
| `m.is_callable_member` | `inspect.isfunction(val)` — `astropy/utils/misc.py:530` | unchanged stdlib predicate; result carried as a bool field |
| `m.is_computed_attribute` | `inspect.isdatadescriptor(val)` — the call the patch ADDS at `misc.py:530` (post-patch) | unchanged stdlib predicate; result carried as a bool field |
| `m.is_public` | `is_public_member(key)` — nested fn `astropy/utils/misc.py:525-528` | unchanged local predicate; result carried as a bool field |
| `m.has_own_doc` | `val.__doc__ is not None` (guard tests `val.__doc__ is None` at `misc.py:532`) | whether the member already has its own docstring |
| `m.inherited_doc` | result of the unchanged MRO walk `for base in cls.__mro__[1:]: super_method = getattr(base, key, None); ... super_method.__doc__` — `misc.py:533-538` | the docstring resolved from the base classes |
| `m.doc` | `val.__doc__` — assigned at `misc.py:537` | the member's current/resulting docstring |
| `fills_docstring(...)` | the full `if`-guard `(inspect.isfunction(val) or inspect.isdatadescriptor(val)) and is_public_member(key) and val.__doc__ is None` (post-patch, `misc.py:530-532`) | pure spec: eligibility for docstring inheritance |

The pre-patch repo symbol the change widens (for the refinement audit, not
referenced from the consumer spec view): the guard's left conjunct, which
pre-patch was `inspect.isfunction(val)` alone (`misc.py:530`), considering only
ordinary callable members.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `inspect.isfunction(val)` (bool) | `Member.is_callable_member: bool` | the stdlib predicate result, recorded as a field. |
| `inspect.isdatadescriptor(val)` (bool) | `Member.is_computed_attribute: bool` | the stdlib predicate result, recorded as a field. |
| `is_public_member(key)` (bool) | `Member.is_public: bool` | the local predicate result, recorded as a field. |
| `val.__doc__ is None` (bool) | `not Member.has_own_doc` | `has_own_doc` ↔ `val.__doc__ is not None`. |
| `val.__doc__` / `super_method.__doc__` (`str` or `None`) | `int` docstring identity; `0` = `None` (no docstring) | only *whether* a docstring is present and *whether it is assigned the resolved base docstring* is observable; the characters are irrelevant to the F2P test (`Subclass.bar.__doc__ == "BAR"` checks the inherited docstring is the base's). Distinct nonzero ints denote distinct docstrings; `inherited_doc` is the resolved base docstring's identity. Nagini bans `str` indexing, so an `int` identity is used. |
| one iteration of `for key, val in dct.items()` | one `apply_inheritance(m)` call | the loop is unchanged scaffolding; the per-iteration body is the patched hunk. |
| the MRO walk `for base in cls.__mro__[1:]: getattr(base, key, None)` resolving a base docstring | the input field `Member.inherited_doc` | unchanged resolution; abstracted as the already-resolved input value. |

## 3. Callee provenance (unchanged callees — abstractions checked by G-AX / axiom_check.py)

No `@ContractOnly` axiom is consumed by the proof. The model abstracts the
results of three unchanged callees as boolean/int fields (R / A-reference);
axiom_check.py validates each abstraction against the real callee on the
representative member kinds (G-AX runs the real callees in-container).

### 3.1 `is_callable_member` ↔ `inspect.isfunction` (A-reference)
**Callee:** CPython `inspect.isfunction(object)` — "Return True if the object is
a Python function" (`Lib/inspect.py`; returns `isinstance(object,
types.FunctionType)`). Docs:
https://docs.python.org/3/library/inspect.html#inspect.isfunction.
Relied-on facts: an ordinary `def` member -> `True`; a `property` -> `False`
(a property is not a function — the original bug). axiom_check.py asserts both.

### 3.2 `is_computed_attribute` ↔ `inspect.isdatadescriptor` (A-reference)
**Callee:** CPython `inspect.isdatadescriptor(object)` — "Return True if the
object is a data descriptor. Data descriptors have a `__set__` or a `__delete__`
method" (`Lib/inspect.py`). Docs:
https://docs.python.org/3/library/inspect.html#inspect.isdatadescriptor.
Relied-on facts: a `property` -> `True` (it defines `__set__`/`__delete__`); an
ordinary `def` member -> `False`; a plain data attribute -> `False`.
axiom_check.py asserts these. This is the call the patch adds, and the disjunct
that makes a public undocumented property eligible.

### 3.3 `is_public` ↔ `is_public_member` (A-reference)
**Callee:** the nested `is_public_member(key)` defined in
`InheritDocstrings.__init__` (`misc.py:525-528`), UNCHANGED by the patch:
`(key.startswith('__') and key.endswith('__') and len(key) > 4) or not
key.startswith('_')`. axiom_check.py mirrors it and checks representative keys
(dunder / public / private).

### 3.4 `inherited_doc` ↔ MRO `getattr` resolution (unchanged scaffolding)
**Callee:** the `cls.__mro__[1:]` walk with `getattr(base, key, None)` and
`super_method.__doc__` (`misc.py:533-538`), UNCHANGED by the patch. It resolves
the first base class along the MRO that defines `key`, and reads its
`__doc__`. The model abstracts the resolved docstring as the input
`inherited_doc`; this is not part of the behavioural change (the change is which
members reach this assignment), so it is modeled as a given resolved value.

**Soundness check (G-AX):** `axiom_check.py` builds a class with an ordinary
method, a `__call__`, a `property`, and a plain data attribute, then runs the
REAL `inspect.isfunction`, `inspect.isdatadescriptor`, and `is_public_member`
on each, asserting the model's field abstractions. It then re-derives the whole
patched eligibility decision with the real callees over the cross product of
member-kind × public × has-own-doc and asserts it equals the model's
`fills_docstring`, and spells out the discriminating witness (a public
undocumented property is filled under the patched guard but not under the
pre-patch `isfunction`-only guard). It imports only the standard-library
`inspect` module (the very module the patch calls). Exit 0 iff sound.
