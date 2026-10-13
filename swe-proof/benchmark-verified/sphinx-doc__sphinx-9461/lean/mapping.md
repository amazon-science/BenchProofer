# mapping.md — sphinx-doc__sphinx-9461

## Modeled function

`PyProperty.get_signature_prefix(self, sig: str) -> str`
— `sphinx/domains/python.py`, lines **866–871 @ base_commit
`939c7bb7ff7c53a4d27df067cea637540f0e1dad`** (post-patch: the rewritten
list-building block).

Lean symbols (Solution.lean):
- `problem_spec_propertyPrefix`
- `implementation_propertyPrefix`
- `correct_propertyPrefix`
- helper `prefixWords` (pure region)

## Why this function (multi-site fix; the rest is not faithfully expressible)

The gold patch touches three files:

1. `sphinx/domains/python.py` — `PyProperty`: adds the `classmethod` option flag
   and rewrites `get_signature_prefix` to emit `class` before `property`.
   **← MODELED.** This is the directly F2P-pinned, pure, deterministic core:
   `test_domain_py.py::test_pyproperty` asserts the rendered annotation is
   `"class property "` (and `"abstract property "`). The function is a pure
   transformation of two boolean toggles into a string — fully expressible.
2. `sphinx/ext/autodoc/__init__.py` — `PropertyDocumenter.can_document_member` /
   `import_object` / `add_directive_header`: detect a `classmethod(property(...))`
   descriptor via Python runtime introspection (`safe_getattr(..., '__dict__')`,
   `inspect.isproperty`, `isinstance(obj, classmethod)`, `obj.__func__`) and emit
   the `:classmethod:` directive option. **NOT modeled:** faithfully expressing
   this requires the live CPython object model (descriptors, `__dict__`, MRO),
   which can only be reached by axiomatizing the very introspection callees under
   test — forbidden by §0.7. Modeling it would be a re-imagined algorithm, not a
   skeleton (§0.3).
3. `sphinx/util/inspect.py` — `isclassmethod` / `getdoc` gain `cls`/`name`
   parameters and an MRO walk to recover the docstring of a classmethod-property.
   **NOT modeled:** same reason — `getmro`, `basecls.__dict__`, `obj.__func__` are
   runtime reflection.

Site 1 is the user-visible behavioral fix the F2P prefix assertions check; sites
2–3 are the plumbing that routes the flag to it. Modeling site 1 deeply, with a
prepatch that reproduces the actual "class-level attribute renders like a plain
property" bug, is the faithful, soundness-preserving choice. The non-expressible
introspection sites are recorded here for completeness but excluded from the
triple.

## Type bijection (Lean ↔ Python)

| Python | Lean | note |
|---|---|---|
| `'abstractmethod' in self.options` | `isAbstract : Bool` | flag-present predicate → Bool |
| `'classmethod' in self.options` | `isClassLevel : Bool` | flag-present predicate → Bool (the new option) |
| `prefix : list[str]` | `words : List String` | ordered word list |
| `'abstract'`, `'class'`, `'property'` | `"abstract"`, `"class"`, `"property"` | literal strings, identical bytes |
| `' '.join(prefix) + ' '` | `String.intercalate " " words ++ " "` | join on single space, trailing space |
| return `str` | `String` | the rendered prefix |

`sig : str` is an unused parameter of the real method; it carries no observable
effect on the output and is dropped from the model (the output depends only on
the two flags).

## Callee provenance / flag deps

None consumed. The behavior is modeled deeply over the two toggles; there is no
unchanged callee whose contract the proof relies on. `' '.join` /
`list.append` / `list.insert(0, ...)` are language primitives, transliterated to
`String.intercalate` / `++`, not axiomatized callees.

Flag dependency: the `class` word is emitted iff the `classmethod` option flag is
present (the new flag added to `option_spec` in the same patch hunk); the
`abstract` word iff the `abstractmethod` flag is present. G-CONF fuzzes all four
combinations.

## G-CONF fuzz seed

`9461` (pinned; also in conformance_check.py and meta.json).
