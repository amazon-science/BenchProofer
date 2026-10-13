# mapping.md — sphinx-doc__sphinx-7910

## Symbol binding (file:line @ base_commit 27ac10de04)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_memberInclusion` / `problem_spec_memberInclusion` / `correct_memberInclusion` | `_skip_member` — decides whether a private/special/init class-or-module member is included in the generated docs | `sphinx/ext/napoleon/__init__.py:380-461` @ base_commit |
| `clsIsOwner` (helper) / the owning-class resolution | `cls_is_owner = (cls and hasattr(cls, name) and name in cls.__dict__)` after `cls = ...__globals__[cls_path]` | `sphinx/ext/napoleon/__init__.py:439-447` (edited line `440` of hunk: `cls = obj.__globals__[cls_path]` → `cls = inspect.unwrap(obj).__globals__[cls_path]`) |
| `coreObject` (helper) | `inspect.unwrap(obj)` (via `sphinx.util.inspect.unwrap`) — follow the `__wrapped__` decorator chain to the underlying object | gold patch, `napoleon/__init__.py:440`; callee `sphinx/util/inspect.py:121-127` |

The modeled function is `_skip_member`. Relevant body (base_commit):

```python
has_doc = getattr(obj, '__doc__', False)
is_member = (what == 'class' or what == 'exception' or what == 'module')
if name != '__weakref__' and has_doc and is_member:
    cls_is_owner = False
    if what == 'class' or what == 'exception':
        qualname = getattr(obj, '__qualname__', '')
        cls_path, _, _ = qualname.rpartition('.')
        if cls_path:
            try:
                if '.' in cls_path:
                    ...                                  # importlib branch (nested classes) — OUT OF SCOPE
                else:
                    cls = obj.__globals__[cls_path]      # PRE-PATCH  (bug)
                    # cls = inspect.unwrap(obj).__globals__[cls_path]   # POST-PATCH
            except Exception:
                cls_is_owner = False
            else:
                cls_is_owner = (cls and hasattr(cls, name) and name in cls.__dict__)
        else:
            cls_is_owner = False
    if what == 'module' or cls_is_owner:
        is_init    = (name == '__init__')
        is_special = (not is_init and name.startswith('__') and name.endswith('__'))
        is_private = (not is_init and not is_special and name.startswith('_'))
        inc_init    = app.config.napoleon_include_init_with_doc
        inc_special = app.config.napoleon_include_special_with_doc
        inc_private = app.config.napoleon_include_private_with_doc
        if ((is_special and inc_special) or (is_private and inc_private) or (is_init and inc_init)):
            return False
return None
```

### The bug and the fix
`obj` is the member object passed by autodoc, e.g. `SampleClass.__init__`. When the
member is **decorated** (e.g. with `functools.wraps`), `obj` is the *wrapper*
function. `functools.wraps` copies `__doc__` and `__qualname__` onto the wrapper,
but the wrapper's `__globals__` are the *decorator module's* globals — they do **not**
contain the class name `cls_path`. So `obj.__globals__[cls_path]` raises `KeyError`,
the `except` fires, `cls_is_owner` stays `False`, and the member is wrongly skipped
(`_skip_member` returns `None` instead of `False`).

The fix resolves the owning class through `inspect.unwrap(obj)` — the underlying
(undecorated) object, whose `__globals__` *do* contain the class — so `cls_is_owner`
becomes `True` and the decorated member is correctly included (returns `False`).

`inspect.unwrap` follows the `__wrapped__` attribute chain to its end (the innermost
object). `sphinx.util.inspect.unwrap` wraps `inspect.unwrap` in a try/except that
returns `obj` unchanged on `ValueError` (mock objects). For acyclic finite chains
(the realistic case) it returns the innermost object.

## Modeled branch / configuration
This bundle models the **`'.' not in cls_path`** branch — exactly the branch the patch
edits, and the one the F2P test exercises (`cls_path = 'SampleClass'`, no dot). The
nested-class `importlib` branch (`'.' in cls_path`) is unchanged by the patch and is
out of scope (G-CONF fuzzes only no-dot qualnames, matching how the bug manifests).
`skip`/`options` parameters are inert in the body and are dropped from the model.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `what : str` ("module"/"class"/"exception"/"method"/…) | `what : String` | identity |
| `name : str` (member name) | `name : String` | identity |
| member object `obj` | `obj : PyObj` | `qualname ↦ __qualname__`, `doc ↦ __doc__` (`None`/`""`/absent ↦ `none`/empty), `globalsMap ↦ __globals__` keys restricted to class names (`name ↦ Cls{attrs}` where `attrs = list(cls.__dict__)`), `inner ↦ __wrapped__` link (`none` if no `__wrapped__`) |
| class object `cls` | `Cls { attrs : List String }` | `attrs ↦ list(cls.__dict__)`; `name in cls.__dict__` ↦ `name ∈ attrs` |
| `inspect.unwrap(obj)` | `coreObject obj` | follow `__wrapped__` / `inner` to the innermost |
| `app.config.napoleon_include_{init,special,private}_with_doc` | `cfg.incInit / cfg.incSpecial / cfg.incPrivate : Bool` | identity |
| return `False` / `None` | `some false` / `none : Option Bool` | the function never returns `True` |

## Callee provenance + flag dependencies
- **`inspect.unwrap`** (unchanged callee, newly *called* by the fix): modeled DEEPLY as
  `coreObject` (follow the `inner`/`__wrapped__` chain). It is an **A-reference**
  validated by G-AX (real `inspect.unwrap` follows `__wrapped__` to innermost) and by
  G-CONF (differential test of the whole impl). Never axiomatized (§0.7).
- No consumed `axiom _prop` is needed: every changed op is modeled concretely.
- Flag dependency: the inclusion decision depends on the three `napoleon_include_*_with_doc`
  config flags; G-CONF fuzzes all 8 combinations.

## G-CONF fuzz seed
`SEED = 7910` (pinned in `conformance_check.py`).
