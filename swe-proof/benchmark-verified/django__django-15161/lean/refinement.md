# refinement.md — django__django-15161

Maps every operation in `implementation_deconstructedPath` to its `patch.diff`
counterpart. The gold patch adds `@deconstructible(path='django.db.models.X')`
to six expression classes (`django/db/models/expressions.py`); the behavior it
enables lives in the `deconstruct` closure installed by that decorator
(`django/utils/deconstruct.py`), which now selects the configured short path for
direct instances. Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (the path-selection enabled by the decorator)
```python
# django/db/models/expressions.py — gold adds, per class:
@deconstructible(path='django.db.models.Value')   # Func / ExpressionWrapper / When / Case / OrderBy likewise
class Value(...): ...

# django/utils/deconstruct.py — the closure that consumes `path`:
return (
    path if path and type(obj) is klass
    else f'{obj.__class__.__module__}.{name}',
    ...,
)
```
The modeled value is the FIRST tuple component — the canonical import path.

## Operation correspondence
| # | Lean op (`implementation_deconstructedPath`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `match simplifiedPath with \| some p => …` | the configured `path` from `@deconstructible(path=…)`; the truthiness test `if path` in `path if path and type(obj) is klass` | R | `path` (`str`/`None`) ↔ `simplifiedPath : Option String`. The gold patch supplies `path='django.db.models.X'` (a `some`); pre-patch the bare `@deconstructible` gave `path=None` (a `none`). Type bijection in mapping.md. |
| 2 | `if isExactType then return p` | `path if path and type(obj) is klass` — selecting the configured `path` verbatim | R | `type(obj) is klass` (bool) ↔ `isExactType : Bool`; the returned value is `path` itself (`p`), not a recomputation. |
| 3 | `else return qualifiedName objModule objClassName` | `else f'{obj.__class__.__module__}.{name}'` | R | the dot-join is modeled DEEPLY as `objModule ++ "." ++ objClassName` (`qualifiedName`), not axiomatized; `obj.__class__.__module__` ↔ `objModule`, `name` ↔ `objClassName`. |
| 4 | `\| none => return qualifiedName objModule objClassName` | the `else` branch when `path` is falsy (`path=None`) | R | absent configured path ⇒ fully-qualified location, exactly as op 3. |

Every op is R; the only concrete computation (`++`) is modeled deeply. **No A
row** (no axiom consumed, no deep-model reference of an unchanged callee — the
`path`, `module`, and `name` enter as data; the dot-join is modeled deeply).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

### Not modeled (justified)
* `obj._constructor_args` (the 2nd/3rd tuple components — reconstruction args):
  unchanged by the patch; the patch only changes the path component.
* `import_module(module_name)` + `hasattr(module, name)` existence check
  (`deconstruct.py:32-41`): a guard that succeeds on the modeled public classes
  and never alters the returned path value; not on the value path of the
  selection, so not modeled (mapping.md modeling notes).

## R/I legs ⇒ G-CONF
The whole impl is R, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior (the `deconstruct` path selection)
over ≥10^5 fuzzed inputs. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the six expression classes carried only the inherited bare
`@deconstructible` on `Expression`, invoked with `path=None`. The guard
`path and type(obj) is klass` was therefore always false, so `deconstruct`
ALWAYS returned the fully-qualified `f'{module}.{name}'`
(`django.db.models.expressions.Value`, etc.). The prepatch impl
(`implementation_deconstructedPath := return qualifiedName objModule objClassName`,
unconditionally) is exactly this: it ignores any configured short path. It
therefore cannot satisfy `problem_spec_deconstructedPath` on the discriminating
clause (`simplifiedPath = some p → isExactType = true → result = p`) whenever
`p ≠ qualifiedName objModule objClassName` — precisely the case the FAIL_TO_PASS
tests exercise (`test_deconstruct`/`test_deconstruct_output_field` expect
`'django.db.models.Value'`, not `'django.db.models.expressions.Value'`;
`test_serialize_complex_func_index` expects `models.Func(...)` etc.). The carried
gold proof fails to typecheck against the buggy impl (G-DIFF — confirmed: the
`refine_1` goal reduces to `qualifiedName objModule objClassName = p`, unprovable
for distinct strings).
