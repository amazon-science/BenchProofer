# mapping.md — symbol binding & type bijection (django__django-17087)

## Modeled function
- **Lean** `implementation_classMethodRef : BoundClassMethod → SerializedRef`
- **Python** `FunctionTypeSerializer.serialize(self)` — the branch that handles a
  method bound to a class — `django/db/migrations/serializer.py:164-173 @ 4a72da7`.

The function under spec is the migration serializer's handling of a method whose
`__self__` is a class object (i.e. a classmethod). In this branch it returns a
dotted reference string `"%s.%s.%s" % (module, <class label>, method.__name__)`
plus a one-element import set `{"import %s" % module}`. The observable behavior
the F2P test demands is which class label is used: the bound class's
fully-qualified dotted name (`__qualname__`) rather than its bare innermost name
(`__name__`). For a class nested inside another class the two differ — the
qualified name includes the enclosing class path — so a method on a nested class
must reference the full path to resolve at import time.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `klass.__module__` (`str`) | `BoundClassMethod.module : List Char` | dotted module path |
| `klass.__name__` (`str`) | `BoundClassMethod.ownerName : List Char` | bare innermost class name |
| `klass.__qualname__` (`str`) | `BoundClassMethod.ownerQualname : List Char` | fully-qualified dotted class name; `==` ownerName for a top-level class, strictly longer (`Outer.Inner`) for a nested class |
| `self.value.__name__` (`str`) | `BoundClassMethod.methodName : List Char` | the method's own name |
| returned reference `str` | `SerializedRef.text : List Char` | the `"%s.%s.%s"` join |
| returned imports `set[str]` | `SerializedRef.imports : List (List Char)` | the single `"import %s" % module`; set modeled as a singleton list (this branch always emits exactly one) |
| `"%s.%s.%s" % (a,b,c)` | `a ++ "." ++ b ++ "." ++ c` (char lists) | dotted join |
| `"import %s" % module` | `importFor module = "import " ++ module` | literal join |

`__self__`/`isinstance(..., type)` is the branch guard (precondition that the
value is a method bound to a class); it selects this branch and is not part of
the output relation. The `set` of imports always has exactly one element on this
branch, modeled as a singleton list.

## Callee provenance
- No UNCHANGED repo callee is consumed: `__module__`, `__name__`, `__qualname__`,
  and the method `__name__` are attribute reads modeled as input fields; the
  string assembly (`%`-formatting / dotted join) is modeled DEEPLY as Lean list
  concatenation and validated by G-CONF/G-AX. The axioms region is empty.
- `__qualname__` is a Python language attribute (not a repo symbol); its
  relationship to `__name__` (equal for top-level classes, a dotted superset for
  nested classes) is exercised in G-AX against the real CPython attribute.

## Flag dependency
None. The branch is selected purely by `getattr(self.value, "__self__", None)`
being truthy and a class instance; no configuration flag participates.

## G-CONF fuzz seed
Pinned seed: **17087**. ≥10^5 fuzzed `BoundClassMethod` records over an alphabet
of module/class/method name fragments, oversampling nested-class qualnames
(`Outer.Inner`, `A.B.C`) so the discriminating case (qualname ≠ name) is hit hard.
