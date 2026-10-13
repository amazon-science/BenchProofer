# mapping.md — sphinx-doc__sphinx-9658

## Symbol binding (file:line @ base_commit 232dbe41c5)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_mockQualifiedName` / `problem_spec_mockQualifiedName` / `correct_mockQualifiedName` | the `__qualname__` a mock stand-in object reports after construction | `sphinx/ext/autodoc/mock.py:42-43` (`_MockObject.__init__`) @ base_commit |
| `name : String` | the short name `name` the stand-in is created with: the class attribute `__name__` set on the stand-in's type by `_make_subclass(name, …)` | gold patch: `mock.py:25-30` (`_MockObject.__name__ = ''`) + `mock.py:74-77` (`_make_subclass` adds `'__name__': name`) |
| `result : String` | `self.__qualname__` (read by the renderer `sphinx/util/typing.py:restify` as `'%s.%s' % (cls.__module__, cls.__qualname__)`) | `mock.py:43`; consumer `typing.py:194-198` |

## What the fix changes

A mock stand-in `o` is built by `_make_subclass(name, module, …)` which calls
`type(name, (superclass,), attrs)`; the resulting class has `__module__ = module`
and (post-patch) `__name__ = name`. `_MockObject.__init__` runs on
instantiation and sets the instance attribute `__qualname__`.

```python
# class attribute (post-patch adds __name__ = '')
class _MockObject:
    __name__ = ''                       # <-- added by patch

    def __init__(self, *args, **kwargs):
        self.__qualname__ = self.__name__   # PRE: self.__qualname__ = ''

# subclass factory (post-patch adds '__name__': name)
def _make_subclass(name, module, superclass=_MockObject, attributes=None, ...):
    attrs = {'__module__': module,
             '__display_name__': module + '.' + name,
             '__name__': name,           # <-- added by patch
             ...}
    return type(name, (superclass,), attrs)
```

The renderer `restify(cls)` reaches the `hasattr(cls, '__qualname__')` branch and
returns `':py:class:`%s.%s`' % (cls.__module__, cls.__qualname__)`. PRE-PATCH
`cls.__qualname__ == ''`, so the reference truncates to `module.` (e.g.
`unknown.secret.` — the final component dropped). POST-PATCH `cls.__qualname__`
equals the short `name`, so the reference is complete (`unknown.secret.Class`).

The modeled value-level computation is exactly:
`__qualname__ := __name__`, where `__name__` is the short name the stand-in was
created with. (`__name__` defaults to `''` on the base `_MockObject` so a
directly-instantiated `_MockObject()` still reports `''`; the observable case is
a `_make_subclass`-built stand-in, where `__name__ == name`.)

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `name` (the short name passed to `_make_subclass`, stored as the type's `__name__` class attribute) | `name : String` | Python `str` value-level ↦ Lean `String` (identity over the printable string value) |
| `self.__qualname__` after `_MockObject.__init__` | `result : String` | Python `str` ↦ Lean `String` |

The stand-in's `__module__` is unchanged by the fix and is the renderer's prefix
(`cls.__module__`), not part of `__qualname__`; it is therefore outside the
modeled output (the spec frames `result` to `name` only — the `__qualname__`
attribute is the sole component the fix touches).

## Callee provenance + flag dependencies

- No callee axiom is consumed. The reported qualified name is a direct
  value-level identity (`__qualname__ := __name__`), modeled deeply as the Lean
  `String` identity `result = name`. There is no opaque callee to declare.
- Flag dependency: none. `__init__` always sets `__qualname__ = self.__name__`
  unconditionally; `_make_subclass` always injects `'__name__': name`.
- Renderer observability: the FAIL_TO_PASS test `test_restify_mock` builds a
  stand-in `unknown.secret.Class` via mocked attribute access (each `__getattr__`
  / `__getitem__` calls `_make_subclass(key, …)`), then asserts
  `restify(...) == ':py:class:`unknown.secret.Class`'`. Pre-patch this rendered
  `':py:class:`unknown.secret.`'` (truncated). The companion
  `test_stringify_mock` already passed at base_commit (a mock stand-in is
  falsy — `__len__` returns 0 — so `stringify` short-circuits at `not annotation`
  and returns the display name; it never reads `__qualname__`). Hence only
  `test_restify_mock` is FAIL_TO_PASS.

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).
