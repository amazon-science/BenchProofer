# mapping.md — astropy__astropy-7166

## Symbol binding (file:line @ base_commit 26d147868f)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_inheritDocstrings` / `problem_spec_inheritDocstrings` / `correct_inheritDocstrings` | the per-member docstring-filling loop run when a class is created under the `InheritDocstrings` metaclass (`InheritDocstrings.__init__`) | `astropy/utils/misc.py:523-540` @ base_commit (edited guard at file line `529-531`, hunk `@@ -528,9 +524,9 @@`) |
| `Member` structure (`key`, `isFunction`, `isDataDescriptor`, `doc`) | one `(key, val)` entry of the class namespace `dct.items()`, with `inspect.isfunction(val)`, `inspect.isdatadescriptor(val)`, `val.__doc__` | `misc.py:529` |
| `isPublicMember : List Char → Bool` | the nested `is_public_member(key)` helper | `misc.py:525-528` |
| `superDoc : List Char → Option (List Char)` | the inherited docstring resolved by the MRO walk `for base in cls.__mro__[1:]: super_method = getattr(base, key, None); if super_method is not None: val.__doc__ = super_method.__doc__; break` | `misc.py:532-537` |

## The modeled function

`InheritDocstrings.__init__(cls, name, bases, dct)` walks the class's own
namespace `dct.items()`. For each member it decides — via a guard — whether to
*fill in* a missing docstring from the first base class (in MRO order) that
defines an attribute of the same name:

```python
def is_public_member(key):
    return ((key.startswith('__') and key.endswith('__') and len(key) > 4)
            or not key.startswith('_'))

for key, val in dct.items():
    if ((inspect.isfunction(val) or inspect.isdatadescriptor(val)) and  # POST (was: isfunction(val) only)
            is_public_member(key) and
            val.__doc__ is None):
        for base in cls.__mro__[1:]:
            super_method = getattr(base, key, None)
            if super_method is not None:
                val.__doc__ = super_method.__doc__
                break
```

The PRE-PATCH guard tested `inspect.isfunction(val)` only. A property (and any
other data descriptor) is **not** a function, so `inspect.isfunction` returns
`False`: such a member was skipped and never had its missing docstring filled
from the base class. The fix admits members for which
`inspect.isdatadescriptor(val)` is also true, so a property defined in a
subclass without its own docstring inherits the base property's docstring.

## Lean ↔ Python type bijection (G-CONF + G-AX use this)

| Lean | Python | note |
|---|---|---|
| `List Char` (a member name) | `str` key | per-code-point; `isPublicMember` is a pure string predicate |
| `Member.isFunction : Bool` | `inspect.isfunction(val)` | |
| `Member.isDataDescriptor : Bool` | `inspect.isdatadescriptor(val)` | disjoint from `isFunction` in practice (a function is not a data descriptor; a `property` is a data descriptor but not a function) |
| `Member.doc : Option (List Char)` | `val.__doc__` (`None` ↦ `none`, a docstring `s` ↦ `some s.toList`) | |
| `superDoc key : Option (List Char)` | the docstring `val.__doc__` would be assigned by the MRO walk: `none` if no base in `cls.__mro__[1:]` defines `key` OR the first that does has `__doc__ is None`; otherwise `some` of that base member's docstring | resolves the unchanged `getattr`/MRO traversal |
| `List Member` (input `dct`) | ordered `dct.items()` | order preserved; length preserved |

`superDoc` carries the result of the **unchanged** base-class lookup
(`getattr` over `cls.__mro__[1:]`). It is supplied as an input function (the
class's resolved inheritance environment) rather than re-deriving the MRO walk
in Lean; the gold patch does not touch that walk. It is an **A-reference**:
G-CONF reconstructs it by building real classes under the real (patched)
`InheritDocstrings` metaclass and reading the resulting docstrings, so the
modeled `superDoc` semantics are validated against the real callee.

## Callee provenance + flag deps

- `inspect.isfunction`, `inspect.isdatadescriptor`, `getattr` — Python stdlib;
  unchanged by the patch. Not axiomatized: the selection guard is modeled
  deeply (the boolean predicate), and the MRO lookup is folded into the
  `superDoc` input (A-reference, G-CONF-validated). No consumed callee axiom.
- The guard is **not** flag-dependent.

## G-CONF fuzz seed

Pinned seed: `20240627` (see `conformance_check.py`, `meta.json verifier_pins`).
