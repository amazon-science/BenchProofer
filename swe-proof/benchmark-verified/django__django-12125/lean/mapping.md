# mapping.md — django__django-12125

## Symbol binding (file:line @ base_commit 89d41cba392b759732ba9f1db4ff29ed47da6a56)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_serializeType` / `problem_spec_serializeType` | `TypeSerializer.serialize` | `django/db/migrations/serializer.py:258-272` |
| `TypeRef` (pure helper) | the class/type value `self.value` being serialized, restricted to the observed attributes | the `TypeSerializer` instance's `value` |
| `TypeRef.isModelBase` | `self.value is models.Model` (first special case) | `serializer.py:261,264-266` |
| `TypeRef.isNoneType` | `self.value is type(None)` (second special case) | `serializer.py:262,264-266` |
| `TypeRef.hasModule` | `hasattr(self.value, "__module__")` | `serializer.py:267` |
| `TypeRef.module` | `self.value.__module__` | `serializer.py:268` |
| `TypeRef.shortName` | `self.value.__name__` (unqualified leaf name) | `serializer.py:270, 272 (pre-patch)` |
| `TypeRef.fullName` | `self.value.__qualname__` (fully-qualified in-module path) | `serializer.py:272 (post-patch)` |
| `builtinsModule` | `builtins.__name__` (`== "builtins"`) | `serializer.py:1,269` |

The modeled function is `TypeSerializer.serialize`. It is the only function whose
behavior changes and the only one whose output the FAIL_TO_PASS test
`test_serialize_nested_class` observes (it serializes `WriterTests.NestedEnum`
and `WriterTests.NestedChoices`, asserting the reference path threads through the
enclosing `WriterTests` class). `test_serialize_numbers` is a PASS-side regression
guard over the same code path (top-level classes `Money`, `Decimal`), where
`__qualname__ == __name__`, so the patch leaves it unchanged.

### What the function does (base_commit)

```python
class TypeSerializer(BaseSerializer):
    def serialize(self):
        special_cases = [
            (models.Model, "models.Model", []),
            (type(None), 'type(None)', []),
        ]
        for case, string, imports in special_cases:
            if case is self.value:
                return string, set(imports)
        if hasattr(self.value, "__module__"):
            module = self.value.__module__
            if module == builtins.__name__:
                return self.value.__name__, set()
            else:
                return "%s.%s" % (module, self.value.__name__), {"import %s" % module}
                #                                ^^^^^^^^^^^^^^  pre-patch: __name__
                #                                post-patch:     __qualname__
```

Step by step:
1. Two fixed special cases tried in order: the base model class ⇒ `"models.Model"`
   with no import; the null type ⇒ `"type(None)"` with no import.
2. If the value has no `__module__`, the function falls off the end and returns
   `None` (Python implicit return) — modeled as `none`.
3. If the value's module is the built-in namespace, return the unqualified leaf
   name (`__name__`) with no import.
4. Otherwise return `"<module>.<name>"` with `{"import <module>"}`. At base_commit
   `<name>` is `__name__` (the bare leaf name), so a class declared inside another
   class serializes as if it were a sibling top-level class — the bug. The patch
   replaces `__name__` with `__qualname__`, the fully-qualified in-module path
   that threads through every enclosing scope (`Outer.Inner`,
   `WriterTests.NestedEnum`), which is the correct reference. For a top-level
   class `__qualname__ == __name__`, so that case is unaffected.

### Lean modeling

- The class value `self.value` is modeled as `TypeRef`, carrying exactly the six
  attributes the serializer reads: the two special-case identity flags
  (`isModelBase`, `isNoneType`), the module presence flag (`hasModule`), the
  module name (`module`), the leaf name (`shortName` ↔ `__name__`), and the
  fully-qualified in-module path (`fullName` ↔ `__qualname__`).
- `shortName` and `fullName` are distinct fields because the fix turns precisely
  on which one the non-builtins branch emits. For a top-level class they coincide
  (`fullName == shortName`); for a nested class `fullName` is strictly longer
  (`"WriterTests.NestedEnum"` vs `"NestedEnum"`).
- The Python set-of-imports `{"import %s" % module}` / `set()` is modeled as a
  `List String` (`["import " ++ module]` / `[]`); ordering is irrelevant here
  because at most one import is produced (bijection below).
- The implicit `None` return (no `__module__`) is modeled as `Option.none`.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.value` (a class object) | `TypeRef` | the class ↔ the tuple of its six observed attributes. |
| `self.value is models.Model` | `isModelBase : Bool` | identity test against the base model class. |
| `self.value is type(None)` | `isNoneType : Bool` | identity test against the null type. |
| `hasattr(self.value, "__module__")` | `hasModule : Bool` | whether a home module is observable. |
| `self.value.__module__` | `module : String` | the dotted home-module name. |
| `self.value.__name__` | `shortName : String` | the unqualified leaf name. |
| `self.value.__qualname__` | `fullName : String` | the fully-qualified in-module path. |
| `builtins.__name__` | `builtinsModule = "builtins"` | the built-in namespace name. |
| `return string, set(imports)` / implicit `return None` | `Option (String × List String)` | `(reference, imports)` pair, or `none`. |
| `{"import %s" % module}` | `["import " ++ module]` | the single-element import set. |

The result of `serialize()` is the `(reference, imports)` pair (or `None`).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** Every operation the serializer performs — the two
  special-case identity comparisons, the `hasattr(__module__)` test, the
  builtins-namespace comparison, and the string assembly from `__module__`,
  `__name__`, `__qualname__` — is a direct read of an attribute on the class
  descriptor or a pure string concatenation. There is no external callee whose
  behavior the proof must assume; the changed operation (emit `__qualname__`
  rather than `__name__`) is modeled DEEPLY as the field `fullName`
  (SPEC_GUIDE §3: a deeply-modeled changed read is never axiomatized). So the
  `axioms` region is empty and **G-AX skips**.
- `__name__` vs `__qualname__` for the modeled classes: CPython guarantees
  `cls.__qualname__ == cls.__name__` for a class defined at module top level, and
  `cls.__qualname__` is the dotted path through the enclosing classes for a nested
  class (e.g. `WriterTests.NestedEnum`). This relationship is what the bijection
  encodes: `fullName == shortName` for top-level, `fullName` strictly carries the
  enclosing path otherwise. `conformance_check.py` exercises both regimes.
- The `special_cases` loop and the `for … in` over a two-element list are pure
  control flow with no I/O; modeled as the two leading `if` checks in order.

## G-CONF fuzz seed

Pinned LCG seed: **12125** (see `conformance_check.py` `SEED`). Corpus: randomized
`TypeRef` descriptors — the two special-case flags toggled (including the
priority case where both are set, base model wins); `hasModule` toggled (covering
the implicit-`None` branch); `module` drawn from a small pool that both includes
and excludes the built-in namespace `"builtins"`; `shortName` a random leaf token;
and `fullName` constructed to be EITHER equal to `shortName` (top-level class) OR
`shortName` prefixed by one or more enclosing-class segments (nested class), so
the discriminating regime `fullName ≠ shortName` is heavily sampled — over ≥1e5
fuzzed inputs. The R/I shadow of `implementation_serializeType` (emit
`module.fullName`) is diffed against an in-process replica of the POST-PATCH
`serialize` (emit `module.__qualname__`). Hand-picked edge cases pin the
discriminating clause: a non-builtins nested class with `fullName` strictly
longer than `shortName` (the bug the patch fixes).
