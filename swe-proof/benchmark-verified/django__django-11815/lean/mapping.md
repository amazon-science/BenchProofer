# mapping.md — symbol binding & type bijection (django__django-11815)

## Modeled function
- **Lean** `implementation_serializeEnum : List Char → List Char → List Char → List Char → List Char`
- **Python** `EnumSerializer.serialize(self)` —
  `django/db/migrations/serializer.py:120-125 @ base_commit`.

The function renders the source text that reproduces an enum *member* in a
generated migration file. The member carrier `self.value` exposes:
- `self.value.__class__.__module__` — the module path (e.g. `migrations.test_writer`)
- `self.value.__class__.__name__` — the enum type name (e.g. `TextEnum`)
- `self.value.value` — the member's stored payload (e.g. `'a-value'`, `b'a-value'`, `2`)
- `self.value.name` — the member's identifier (e.g. `'A'`, `'B'`, `'DOTALL'`)

```python
# base (buggy):
v_string, v_imports = serializer_factory(self.value.value).serialize()
imports = {'import %s' % module, *v_imports}
return "%s.%s(%s)" % (module, enum_class.__name__, v_string), imports
# patched:
return ('%s.%s[%r]' % (module, enum_class.__name__, self.value.name),
        {'import %s' % module})
```

The observable behavior demanded by the F2P tests is the rendered string: post-patch
`migrations.test_writer.TextEnum['A']` (member referenced by its *identifier* as a
quoted subscript), pre-patch the payload-based call `migrations.test_writer.TextEnum('a-value')`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `module` (`enum_class.__module__`, e.g. `'migrations.test_writer'`) | `module : List Char` | dotted module path, per-character |
| `enum_class.__name__` (e.g. `'TextEnum'`) | `className : List Char` | enum type name, per-character |
| `self.value.name` (e.g. `'A'`) | `name : List Char` | the member identifier; a Python identifier (letters/digits/underscore), contains no quote chars |
| `self.value.value` rendered (`v_string`, e.g. `"'a-value'"`) | `payload : List Char` | the member's serialized stored payload; consulted only by the pre-patch path |
| returned source-text string (the `[0]` of the tuple) | `List Char` | per-character; the `imports` set component is unaffected by the rendered-text fix and not modeled (see scope note) |

The `%r` conversion of an enum member identifier yields the identifier wrapped in
single quotes (`'A'`), since identifiers contain only name characters that `repr`
does not escape. The format `'%s.%s[%r]'` substituted with `module`,
`className`, `name` is therefore the fixed-order concatenation
`module + '.' + className + '[' + "'" + name + "'" + ']'`. It is reproduced
exactly as an **I** (identical concrete op), not axiomatized. `quoted name`
models the `%r` of the identifier.

## Callee provenance
- `serializer_factory(self.value.value).serialize()` (renders the member payload)
  is CALLED only on the **pre-patch** path; the patch DELETES this call entirely.
  Post-patch, the payload is not consulted, so no UNCHANGED callee property is
  consumed by the spec/proof. The axioms region is empty; G-AX is a skip stub.
- The `'%s.%s[%r]'` substitution is the **changed op**; it is modeled deeply as the
  fixed-order concatenation with `quoted` (R/I), NOT axiomatized.

## Flag dependency
None. The rendering is unconditional; there is no flag branch.

## Scope note
The patch also changes the returned `imports` set: pre-patch
`{'import %s' % module, *v_imports}` (union with the payload's imports), post-patch
`{'import %s' % module}` (just the module import). This second component is a set,
is orthogonal to the rendered-text fix the F2P tests assert on the `[0]` element,
and is not modeled. The F2P tests
(`test_serialize_enums`, `test_serialize_class_based_validators`) assert on the
rendered string `[0]`, which is what `problem_spec_serializeEnum` pins.

## G-CONF fuzz seed
Pinned seed: **11815**. ≥10^5 fuzzed inputs over module-path / class-name /
member-identifier / payload alphabets.
