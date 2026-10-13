# mapping.md — symbol binding & type bijection (django__django-14580)

## Modeled function
- **Lean** `implementation_serializeType : TypeVal → String × List String`
- **Python** `TypeSerializer.serialize` —
  `django/db/migrations/serializer.py:273-289 @ 36fa071d6e`
  (post-patch: the `models.Model` special case carries
  `['from django.db import models']`).

The function under spec serializes a Python *type object* to a pair `(source
text, set of import statements)` used when writing migration files. It first
checks a small table of specially-recognised types by identity; otherwise it
derives the reference from the type's module and qualified name (built-in types
use the bare name with no import). The observable behavior change demanded by
the F2P test is purely the import set attached to the `models.Model` special
case: it must now contain the statement that makes the bare `models.Model`
reference resolve, instead of being empty.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| the type object `models.Model` | `TypeVal.baseModel` | the first special-case table entry |
| the type object `type(None)` | `TypeVal.noneType` | the second special-case table entry |
| a built-in type `t` (`t.__module__ == builtins`) | `TypeVal.builtin t.__name__` | referenced by bare `__name__`, no import |
| any other type `t` | `TypeVal.other t.__module__ t.__qualname__` | referenced `module.qualname`, import `import module` |
| return value `(string, imports)` | `String × List String` | imports is a `set()` in Python; modeled as a duplicate-free ordered `List String` (membership/contents is the only observable) |
| the source string e.g. `"models.Model"` | `String` literal | |
| an import line e.g. `"from django.db import models"` | `String` literal element | |

`self.value` (the type being serialized) is the sole input; the identity test
`case is self.value` becomes `sameType case v` (`BEq` on the `TypeVal` view, which
is reference identity at the level the function observes). The `hasattr(self.value,
"__module__")` branch is total over real type objects (every type has
`__module__`); it is modeled by the `builtin` / `other` constructors.

## Callee provenance
- No UNCHANGED callee is consumed as an axiom. The serialization logic — the
  special-case table, the identity test, and the module/qualname fallback — is
  the changed function itself and is modeled DEEPLY (`serializeSpec`). The axioms
  region is empty.
- `set(imports)` / `"%s.%s" % (module, qualname)` / `"import %s" % module` are
  concrete string/collection ops modeled directly (I-tagged), not callees.

## Flag dependency
None. The branch taken depends only on the identity of the input type, not on any
configuration flag.

## G-CONF fuzz seed
Pinned seed: **14580**. ≥10^5 fuzzed inputs over a pool that oversamples the two
special-case types (`models.Model`, `type(None)`) plus built-in types and a
spread of arbitrary module/qualname types.
