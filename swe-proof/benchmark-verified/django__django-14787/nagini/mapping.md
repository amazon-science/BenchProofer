# mapping.md — django__django-14787

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 004b4620f6f4ad87261e149898940f2dcd5757ef`, states the type
abstraction, and gives the provenance of the deep-modelled standard-library
primitive (source + the exact behaviour the model encodes).

Repo file under change: `django/utils/decorators.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble_bound_callable(method)` | the construction of the per-instance bound callable inside `_multi_decorate(...)._wrapper(self, *args, **kwargs)` — `django/utils/decorators.py:35-43`; specifically the assignment at line 40 that produces the callable subsequently passed to the decorator chain (`for dec in decorators: bound_method = dec(bound_method)`) | the modeled changed function: assemble the callable handed to the user's decorator |
| `method` (a `FuncIdentity`) | the original `method` argument of `_multi_decorate` (`decorators.py:22`), reached via `method.__get__(self, type(self))` (line 40) | the original method whose function-identity metadata must be preserved |
| `method.has_name` / `method.name` | `method.__name__` (present on a real function/method) | the method's name attribute (presence + value) |
| `method.has_module` / `method.module` | `method.__module__` | the method's defining-module attribute (presence + value) |
| `Result()` (the returned `FuncIdentity`) | `bound_method` after line 40, i.e. the object passed into `dec(bound_method)` | the assembled bound callable the decorator inspects |
| the deep model of the copy (impl region: the two guarded per-attribute assignments) | `wraps(method)(...)` ⇒ `functools.update_wrapper(partial, method)` (the wrapper-update primitive; `wraps`/`update_wrapper` imported at `decorators.py:3`) | unchanged stdlib callee the fix introduces a call to; modelled DEEPLY (A-reference, §3.1) |

The gold patch (the one change, `decorators.py:40`) rewrites
```
- bound_method = partial(method.__get__(self, type(self)))
+ bound_method = wraps(method)(partial(method.__get__(self, type(self))))
```
i.e. it wraps the bare `partial(...)` with `wraps(method)(...)`. Pre-patch the
assembled callable is the bare partial; post-patch it carries `method`'s
wrapper-identity attributes.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `partial(method.__get__(self, type(self)))` — the bound-method partial application | a fresh `FuncIdentity` with both attributes absent (`FuncIdentity(False, 0, False, 0)`) | the partial exposes no `__name__` of its own; the relevant wrapper-identity attributes the decorator reads are modelled by the two facets. `__get__`/`type(self)`/`partial` are call-shape that produces a callable with no caller-relevant identity metadata; modelled as the all-absent `FuncIdentity`. |
| `method.__name__` (a `str`) | `(has_name: bool, name: int)` | `str` indexing is banned in Nagini; the *value* of the name is modelled by an opaque `int` token and its *presence* by a flag. The F2P test observes `func.__name__ == 'method'`, i.e. equality to the method's own name — captured by `Result().name == method.name` together with `Result().has_name`. The token identity (not its concrete characters) is what the equality test needs. |
| `method.__module__` (a `str`) | `(has_module: bool, module: int)` | same scheme; the F2P test observes `func.__module__ is not None` — captured by `Result().has_module`. The post-patch value equals the method's (`Result().module == method.module`), the WRAPPER_ASSIGNMENTS semantics. |
| `wraps(method)(partial)` returning the same (now-updated) object | a fresh `FuncIdentity` returned with the copied facets | `update_wrapper` mutates and returns its first argument; the bound callable passed onward IS the updated partial. Modelled as constructing/returning the assembled object with the method's facets copied. |
| `self`, `*args`, `**kwargs`, `type(self)`, the `for dec in decorators` chain | omitted | these do not affect which wrapper-identity attributes the assembled callable exposes; the change and the F2P observation are entirely about the attributes ON the assembled callable, which is what `assemble_bound_callable` returns. |

`str` attribute names and `str` values are banned (Nagini bans `str`
indexing/dynamic attribute access), so each wrapper-identity attribute is
modelled as a concrete `(presence flag, int token value)` pair; the F2P
observations are presence (`has_name`/`has_module`) and value-equality to the
method's own (`name`/`module` ==), both expressible over the carrier.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 The wrapper-identity copy (deep model) ↔ `functools.update_wrapper` / `wraps` (A-reference)
**Callee:** CPython `functools.update_wrapper(wrapper, wrapped, assigned=WRAPPER_ASSIGNMENTS, updated=WRAPPER_UPDATES)`, invoked via `wraps(method)(partial_obj)` (which is `partial(update_wrapper, wrapped=method)(partial_obj)`). `WRAPPER_ASSIGNMENTS` includes `'__name__'` and `'__module__'`. Source (CPython `Lib/functools.py`, stable across the supported 3.x including the 3.8/3.9 interpreter in this instance's Django-4.1 image):

```python
def update_wrapper(wrapper, wrapped, assigned=WRAPPER_ASSIGNMENTS, updated=WRAPPER_UPDATES):
    for attr in assigned:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass
        else:
            setattr(wrapper, attr, value)
    for attr in updated:
        getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
    wrapper.__wrapped__ = wrapped
    return wrapper
```

The changed operation (wrapping the bare partial) is modelled **deeply**: the
impl region's two guarded assignments

```
if method.has_name:   bound.has_name = True;   bound.name = method.name
if method.has_module: bound.has_module = True; bound.module = method.module
```

ARE the `update_wrapper` per-attribute copy specialized to the two
behaviour-bearing attributes (`__name__`, `__module__`). There is **no consumed
`@ContractOnly` axiom**; the deep model is validated **== the real callee**
out-of-band by `axiom_check.py` (G-AX): for a function whose `__name__` and
`__module__` are present, `update_wrapper(partial(...), func)` (equivalently
`wraps(func)(partial(...))`) sets `wrapper.__name__ == func.__name__` and
`wrapper.__module__ == func.__module__`. Docs:
https://docs.python.org/3/library/functools.html#functools.wraps and
https://docs.python.org/3/library/functools.html#functools.update_wrapper.

**Pre-patch subtlety (recorded so G-AX fuzzes the right thing).** A `partial`
object has **no `__name__`** of its own — so before the fix, a decorator that
reads `bound_method.__name__` raises `AttributeError: 'functools.partial' object
has no attribute '__name__'` (the exact exception in the problem statement),
and `getattr(bound_method, '__name__', None)` returns `None`. This is the
behaviour the F2P test pins via `self.assertEqual(func_name, 'method')` — pre-
patch `func_name` is `None ≠ 'method'`. (A `partial` *does* inherit a
`__module__` of `'functools'` from its type, but it is NOT the method's module;
the fix's `update_wrapper` overwrites it with the method's own. The model treats
`__module__` as absent on the bare partial because the caller-relevant module
metadata — the method's module — is what the WRAPPER_ASSIGNMENTS copy supplies;
the F2P test's `func_module is not None` is satisfied either way, and the
discriminating clause the prepatch fails on is the **name**, which is genuinely
absent on the partial. axiom_check.py records both facts.)

The deep model is the **weakest** faithful model the proof needs: it copies the
two attributes the F2P test observes, exactly as `update_wrapper` does, and
leaves the method unmodified (read-only). The patch does not change
`functools.update_wrapper`/`wraps`; it introduces a call to it, so it is a
genuine kind-A reference, not the operation under change (the operation under
change is `_wrapper`'s assembly of `bound_method`, which is `assemble_bound_callable`).

**Soundness check (G-AX):** `axiom_check.py` imports only the standard library
(`functools` — the very module the patch calls) and runs the real
`functools.wraps`/`update_wrapper` over (a) boundary functions (a plain
function, a method bound via `__get__`, a `partial`, lambdas, functions with
unusual names/modules) wrapped onto a `partial`, and (b) randomized fuzz over
name/module tokens, asserting in every case that the wrapped partial's
`__name__`/`__module__` equal the wrapped function's, that the original function
is unmodified, and recording the pre-wrap `AttributeError` on the bare partial's
`__name__`. Exit 0 iff every observation matches the deep model. (Outside a
Python environment it cannot run; the orchestrator runs it in-container, where
`functools` is always importable.)
