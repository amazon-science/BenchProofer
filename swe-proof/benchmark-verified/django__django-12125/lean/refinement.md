# refinement.md — django__django-12125

Maps every operation in `implementation_serializeType` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `serializeType` (`TypeSerializer.serialize`)

Post-patch repo code (`serializer.py:258-272`, the `__qualname__` line is the fix):
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
                return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}
```

Lean impl (`implementation_serializeType`):
```lean
def implementation_serializeType (v : TypeRef) :
    Option (String × List String) := Id.run do
  if v.isModelBase then
    return some ("models.Model", [])
  if v.isNoneType then
    return some ("type(None)", [])
  if v.hasModule then
    if v.module = builtinsModule then
      return some (v.shortName, [])
    else
      return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
  return none
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `v : TypeRef` (input carrier) | `self.value`, the class object being serialized | **R** | the class ↔ the six attributes the serializer reads (`is models.Model`, `is type(None)`, `hasattr(__module__)`, `__module__`, `__name__`, `__qualname__`). See mapping.md type bijection. |
| 2 | `if v.isModelBase then return some ("models.Model", [])` | first `special_cases` entry: `(models.Model, "models.Model", [])` checked in the `for` loop via `case is self.value` | **I** | identical concrete op: identity comparison against the base model class returns the fixed literal with no import. `set([]) ↔ []`. |
| 3 | `if v.isNoneType then return some ("type(None)", [])` | second `special_cases` entry: `(type(None), 'type(None)', [])` | **I** | identity comparison against the null type returns the fixed literal with no import; checked AFTER the model-base case, matching the list order. |
| 4 | `if v.hasModule then … else return none` | `if hasattr(self.value, "__module__"): …` + implicit `return None` | **R** | `hasModule ↔ hasattr(__module__)`. Falling off the function (no module) ↔ `Option.none`. |
| 5 | `if v.module = builtinsModule then return some (v.shortName, [])` | `module = self.value.__module__; if module == builtins.__name__: return self.value.__name__, set()` | **R** | `module ↔ __module__`; `builtinsModule = "builtins" ↔ builtins.__name__`; built-in namespace ⇒ leaf name `shortName ↔ __name__` with no import. |
| 6 | `else return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])` | `else: return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}` | **R** (deep model of the changed op) | **the fixed operation.** Post-patch emits `__qualname__`, the fully-qualified in-module path; modeled deeply as the field `fullName`. `module ++ "." ++ fullName ↔ "%s.%s" % (module, __qualname__)`; `["import " ++ module] ↔ {"import %s" % module}`. The pre-patch impl emits `shortName` (`__name__`), the bug. This is the heart of the fix. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `serialize`.

## Callee provenance (no consumed axiom)

- `case is self.value` (the two special-case identity tests) — pure identity
  comparisons, modeled as the `isModelBase` / `isNoneType` flags. No external
  callee.
- `hasattr(self.value, "__module__")` — a pure attribute-presence test, modeled
  as `hasModule`. No external callee.
- `self.value.__module__` / `__name__` / `__qualname__` — attribute reads on the
  class descriptor, modeled as the `module` / `shortName` / `fullName` fields. The
  changed read (`__name__` → `__qualname__`) is modeled DEEPLY as `fullName`
  (SPEC_GUIDE §3: a deeply-modeled changed read is never axiomatized), so it is an
  R leg, not an A-reference, and there is no `opaque`/`axiom` in Solution.lean.
- `"%s.%s" % (...)` and set/list construction — pure string/collection assembly,
  modeled as `++` and a singleton list.

## Soundness check (verify ⟹ correct)

- `problem_spec_serializeType` pins the result EXACTLY for every descriptor `v`
  (full equality to an input-grounded `Option (String × List String)`) —
  directive 5 (frame): every output component (the reference string AND the
  import list) is determined by the input fields, in the same priority order as
  the real serializer. No output component is left unconstrained; the reference
  in the non-builtins branch is pinned to `module ++ "." ++ fullName`, so a wrong
  impl that emitted `shortName` cannot satisfy it. No ungrounded oracle
  (directive 8) — the postcondition is dischargeable only by reading the actual
  descriptor fields and assembling the string.
- The prepatch impl reproduces the PRE-FIX behavior: the non-builtins branch
  emits `v.module ++ "." ++ v.shortName` (`__name__`). It violates the spec on the
  discriminating clause `¬isModelBase ∧ ¬isNoneType ∧ hasModule ∧ module ≠
  builtins ∧ fullName ≠ shortName` — a nested class: the spec requires
  `module.fullName` (`module.Outer.Inner`) but the prepatch produces
  `module.shortName` (`module.Inner`). Its carried gold proof cannot close
  (G-DIFF/G-PANEL).
- This discriminating case is precisely the FAIL_TO_PASS assertion added by the
  test patch (`test_serialize_nested_class`): `WriterTests.NestedEnum` /
  `WriterTests.NestedChoices` must serialize to
  `"migrations.test_writer.WriterTests.NestedEnum"`, not
  `"migrations.test_writer.NestedEnum"`. Pre-fix the leaf name dropped the
  enclosing `WriterTests`; post-fix `__qualname__` keeps it.
  `test_serialize_numbers` (also FAIL_TO_PASS) is the top-level-class regression
  side: `Money` / `Decimal` have `fullName == shortName`, so both impls agree —
  the spec's non-discriminating clause.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  `serialize` over hand-picked edge cases (including a non-builtins nested class
  with `fullName` strictly longer than `shortName`, the builtins branch, both
  special cases, and the no-module branch) plus ≥1e5 fuzzed descriptors.
