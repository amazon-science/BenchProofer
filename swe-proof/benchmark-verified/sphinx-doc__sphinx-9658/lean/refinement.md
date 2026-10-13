# refinement.md — sphinx-doc__sphinx-9658

Operation correspondence between `implementation_mockQualifiedName` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: the changed operation is a value-level
string identity (`self.__qualname__ = self.__name__`), modeled DEEPLY as the Lean
`String` identity. Every row is **R** or **I**. The R/I legs are
differential-tested by G-CONF; G-AX is a skip stub (no consumed callee axiom).

## `implementation_mockQualifiedName` ↔ the `_MockObject.__init__` qualified-name assignment

The gold patch turns

```python
class _MockObject:
    __display_name__ = '_MockObject'
    # (no __name__ class attribute)

    def __init__(self, *args, **kwargs):
        self.__qualname__ = ''
```

into

```python
class _MockObject:
    __display_name__ = '_MockObject'
    __name__ = ''                         # base default

    def __init__(self, *args, **kwargs):
        self.__qualname__ = self.__name__
```

and, in the stand-in factory `_make_subclass(name, module, …)`, adds
`'__name__': name` to the type's attribute dict so a factory-built stand-in's
`self.__name__` is the short `name` it was created with.

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `let mut nameAttr := name` | `__name__ = name` injected by `_make_subclass` (the type's `__name__` class attribute) → read as `self.__name__` | R | Python `str` short-name value ↦ Lean `String`. The added `__name__ = ''` base default ↦ the base case where `name = ""`. |
| `let mut qualname := nameAttr` | `self.__qualname__ = self.__name__` | I | the qualified name is set to the recorded short name (identity copy) |
| `return qualname` | the resulting `self.__qualname__` attribute (read downstream by `restify` as `cls.__qualname__`) | R | Python `str` ↦ Lean `String` |

The result is the precise observable: `cls.__qualname__`, which `restify`
(`typing.py:194-198`) joins with `cls.__module__` as `module.qualname`. Empty
qualname ⇒ truncated reference `module.`; qualname == short name ⇒ complete
reference `module.name`. The F2P test `test_restify_mock` asserts the complete
reference `:py:class:`unknown.secret.Class``.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the qualified name is fixed to `""` regardless of the
  short name (the pre-patch `self.__qualname__ = ''`), so the rendered reference
  drops its final component. The carried gold proof of `correct_mockQualifiedName`
  fails to close (`"" = name` is not reflexivity for a general `name`).
  (FAIL_TO_PASS: `tests/test_util_typing.py::test_restify_mock`.)
