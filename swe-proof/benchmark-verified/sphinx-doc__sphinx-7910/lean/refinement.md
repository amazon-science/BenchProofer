# refinement.md — sphinx-doc__sphinx-7910

Operation correspondence between `implementation_memberInclusion` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No `axiom _prop` is declared or consumed. The single callee the fix newly relies
on — `inspect.unwrap` (resolve an object to the underlying object it wraps) — is
modeled DEEPLY as `coreObject` (follow the wrapper links to the end). It is
therefore an **A-reference** (validated == real `inspect.unwrap` by G-AX, and the
whole impl differential-tested by G-CONF), never an axiomatized `opaque`. Every
row is **R**, **A-reference**, or **I**.

## `implementation_memberInclusion` ↔ `_skip_member`

The gold patch turns

```python
cls = obj.__globals__[cls_path]                    # PRE-PATCH (bug)
```

into

```python
cls = inspect.unwrap(obj).__globals__[cls_path]    # POST-PATCH
```

(plus the `from sphinx.util import inspect` import), with the surrounding
ownership / docstring / category logic unchanged.

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `let hasDoc := obj.hasDoc` | `has_doc = getattr(obj, '__doc__', False)` | R | "has a (truthy) docstring" ↦ `Bool` |
| `let isMember := what == "module" \|\| "class" \|\| "exception"` | `is_member = (what == 'class' or 'exception' or 'module')` | I | |
| `if name != "__weakref__" && hasDoc && isMember then` | `if name != '__weakref__' and has_doc and is_member:` | I | guard |
| `if what == "class" \|\| what == "exception" then` | `if what == 'class' or what == 'exception':` | I | |
| `clsPathSingle obj.qualname` (single dotless prefix branch) | `qualname = getattr(obj,'__qualname__',''); cls_path,_,_ = qualname.rpartition('.')` then the `'.' not in cls_path` `else` branch | R | models ONLY the no-dot `cls_path` branch (mapping.md); a dotless owner short-name ↦ `some c` |
| `match obj.coreObject.globalsMap.lookup clsPath with \| some cls => clsOwner := cls.attrs.contains name \| none => clsOwner := false` | `cls = inspect.unwrap(obj).__globals__[cls_path]` … `cls_is_owner = (cls and hasattr(cls,name) and name in cls.__dict__)`; `KeyError` ↦ `except: cls_is_owner = False` | **A-reference** | the EDITED op. `inspect.unwrap(obj)` modeled deeply as `coreObject` (follow `inner`/`__wrapped__` to innermost); the `[cls_path]` lookup + `KeyError` modeled as `List.lookup` returning `none`; `name in cls.__dict__` ↦ `cls.attrs.contains name`. Validated == real callee by G-AX/G-CONF |
| `if what == "module" \|\| clsOwner then` | `if what == 'module' or cls_is_owner:` | I | |
| `isInit / isSpecial / isPrivate` | `is_init / is_special / is_private` (name string tests) | I | identical `startswith`/`endswith` logic |
| `if (isSpecial && incSpecial) \|\| (isPrivate && incPrivate) \|\| (isInit && incInit) then return some false` | `if ((is_special and inc_special) or (is_private and inc_private) or (is_init and inc_init)): return False` | R | Python `False` ↦ `some false` |
| `return none` | `return None` (fall-through) | R | Python `None` ↦ `none : Option Bool` |

`hasattr(cls, name)`: in CPython `name in cls.__dict__ ⟹ hasattr(cls, name)`, so
`name in cls.__dict__` alone is the discriminating conjunct; modeled as
`cls.attrs.contains name` (where `attrs = list(cls.__dict__)`). The `cls and …`
truthiness guard is subsumed by a successful `lookup` returning a class.

The observable is the inclusion verdict (`False` = include, `None` = defer; the
function never returns `True`). The F2P test `test_class_decorated_doc` asserts
`_skip_member(...) is False` for a `functools.wraps`-decorated special member.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the owning class is resolved from `obj.globalsMap`
  (the wrapper's own scope) instead of `obj.coreObject.globalsMap`. For a
  decorated member the wrapper's `globalsMap` lacks the class, so `clsOwner`
  stays `false` and the impl returns `none` — contradicting the
  `shouldInclude … = true → result = some false` clause whenever the member is a
  decorated, owned, toggled-on member. The carried gold proof of
  `correct_memberInclusion` fails to close on that clause. This is the single
  fixed behavior. (FAIL_TO_PASS: `tests/test_ext_napoleon.py::SkipMemberTest::test_class_decorated_doc`.)
