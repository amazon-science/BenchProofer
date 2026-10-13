# mapping.md — django__django-14787

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 004b4620f6f4ad87261e149898940f2dcd5757ef`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the modeled callee.

Repo file under change: `django/utils/decorators.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildPresentedAttrs (methodAttrs baseAttrs names)` | the construction of the callable handed to the decorator chain inside `_wrapper` — `django/utils/decorators.py:35-43` (the changed expression is line 40) | the modeled changed function: which introspection-attribute values that callable presents |
| `mergeAt` / `mergePlan` *(deep model — A-reference)* | `functools.update_wrapper` (CPython stdlib `Lib/functools.py`) restricted to its `WRAPPER_ASSIGNMENTS` copy loop — invoked by `functools.wraps(method)(...)` (`django/utils/decorators.py:40` post-patch) | pure spec: the per-name attribute overlay (source value if present, else base); deep model of the unchanged stdlib callee, validated `mergePlan == update_wrapper` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `lookupAttr` | attribute access `getattr(obj, name)` / "name present?" on the callable object | pure spec helper: the value an object's attribute environment binds to a name, or `none` if absent |
| `firstDefined` | the `if name in wrapped: setattr(wrapper, name, value)` rule of `update_wrapper`'s assign loop | pure spec helper: overlay one optional value over another |

The bare callable that the source attributes are overlaid onto is
`partial(method.__get__(self, type(self)))` — a `functools.partial` object, whose
own attribute environment is `baseAttrs` (e.g. `__module__='functools'`,
`__doc__=<partial docstring>`, and **no** `__name__`/`__qualname__`). `method` is
the source object whose attributes are `methodAttrs` (a function: it carries
`__name__`, `__qualname__`, `__module__`, `__doc__`, `__annotations__`).

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): `bound_method = partial(method.__get__(self, type(self)))`
— the bare object with no overlay (`decorators.py:40` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| an object's introspection-attribute environment (the subset of `WRAPPER_ASSIGNMENTS` names it defines, with values) | `List (String × String)` | name `n` defined with value `v` ↔ `(n, v) ∈` the assoc list (first match wins, mirroring `getattr`); `n` absent ↔ no pair with key `n` |
| `getattr(obj, n, <<ABSENT>>)` restricted to assigned names | `lookupAttr attrs n : Option String` | the bound value ↔ `some v`; the attribute being absent ↔ `none` |
| the list of attribute names copied (`functools.WRAPPER_ASSIGNMENTS`) | `names : List String` | identical name sequence |
| `wraps(method)(obj)` / `update_wrapper(obj, method)` result, observed per assigned name | `mergePlan methodAttrs baseAttrs names : List (String × Option String)` | for each name, the value the resulting object presents ↔ `mergeAt methodAttrs baseAttrs n` |

Attribute *values* are modeled as opaque `String`s: the change is purely about
**which source the presented value comes from** (the source object vs the bare
object), never about computing a value, so an opaque-string carrier is faithful
and total. `WRAPPER_ASSIGNMENTS` are the only names involved; `update_wrapper`'s
separate `__dict__.update` (the `updated` argument) does not affect these
function-identity attributes and is out of scope of the modeled behavior.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `mergePlan` deep model ↔ `functools.update_wrapper` assign-loop (A-reference)
**Callee:** CPython `functools.update_wrapper(wrapper, wrapped, assigned=WRAPPER_ASSIGNMENTS)`,
as invoked by `functools.wraps(method)`. Source (every supported 3.x, incl. the
3.x interpreter in this image):

```python
WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__qualname__', '__doc__',
                       '__annotations__', ...)
def update_wrapper(wrapper, wrapped, assigned=WRAPPER_ASSIGNMENTS, updated=...):
    for attr in assigned:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass                       # leave wrapper's existing value in place
        else:
            setattr(wrapper, attr, value)
    ...
    return wrapper
```

For each assigned name the resulting object presents `wrapped`'s value when
`wrapped` defines it, otherwise it keeps `wrapper`'s existing value — exactly the
per-name `firstDefined (lookupAttr methodAttrs n) (lookupAttr baseAttrs n)` of
`mergeAt`, lifted over the name list by `mergePlan`. There is **no consumed
`updateWrapper` axiom**; the operation is modeled deeply and validated against the
real callee. Docs: https://docs.python.org/3/library/functools.html#functools.update_wrapper

**Flag/configuration dependency:** the relevant copy is governed solely by the
`assigned` name list (`WRAPPER_ASSIGNMENTS`); `wraps` uses the default. G-AX
fuzzes with the real `WRAPPER_ASSIGNMENTS` of the in-image interpreter, so the
check stays faithful to whatever name set ships there.

**Soundness check (G-AX):** `axiom_check.py` constructs source/base objects with
arbitrary subsets of the assigned names bound to arbitrary values, runs the REAL
`functools.update_wrapper` on a fresh carrier object, and asserts that the value
it presents for every assigned name equals `mergePlan` (the deep model). It also
exercises the exact django scenario — a real `partial(method.__get__(...))`
wrapped by `wraps(method)` — and asserts the presented `__name__` is the method's
name and was absent before. Imports only stdlib `functools`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14787`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `lookupAttr`/`firstDefined`/`mergeAt`/`mergePlan` (the R/I ops) to
Python and bridges I/O via the §2 bijection; the ORACLE is `patch.diff`'s
behaviour — the real `functools.wraps(method)(partial(...))` observed per assigned
name through a capturing decorator (the F2P observation channel).
