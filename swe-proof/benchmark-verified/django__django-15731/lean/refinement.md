# refinement.md — django__django-15731

Maps every operation in `implementation_delegateMetadata` to its `patch.diff`
counterpart in `BaseManager._get_queryset_methods.create_method`
(`django/db/models/manager.py`, the produced-method metadata construction).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch metadata construction)
```python
def create_method(name, method):
    @wraps(method)
    def manager_method(self, *args, **kwargs):
        return getattr(self.get_queryset(), name)(*args, **kwargs)

    return manager_method
```
The modeled value is the INTROSPECTABLE METADATA of the produced
`manager_method`: the tuple `(__name__, __qualname__, __module__, __doc__,
__annotations__, str(inspect.signature(...)))`. `@wraps(method)` copies
`functools.WRAPPER_ASSIGNMENTS` (`__module__`, `__name__`, `__qualname__`,
`__doc__`, `__annotations__`, `__type_params__`) from `method` and sets
`__wrapped__ = method`, which makes `inspect.signature` report `method`'s real
parameter list. Net observable effect: every introspectable attribute of the
produced method equals `method`'s.

## Operation correspondence
| # | Lean op (`implementation_delegateMetadata`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut meta := rawDelegate` | `def manager_method(self, *args, **kwargs): ...` — the bare forwarding wrapper, before metadata propagation | R | the accumulator starts at the generic wrapper's intrinsic metadata: catch-all signature `(self, *args, **kwargs)`, own qualname/module, empty doc/annotations. `rawDelegate : MethodMetadata` ↔ that tuple (mapping.md). |
| 2 | `meta := { meta with name := underlying.name, qualname := underlying.qualname, module := underlying.module, doc := underlying.doc, annotations := underlying.annotations, signature := underlying.signature }` | `@wraps(method)` applied to `manager_method` | R/A-reference→modeled-deeply | `functools.wraps` copies `WRAPPER_ASSIGNMENTS` from `method` and sets `__wrapped__`, so `inspect.signature` follows to `method`. Its OBSERVABLE effect — every introspectable attribute equals `method`'s — is modeled deeply as a field-by-field copy of the `MethodMetadata` carrier (SPEC_GUIDE §3: a changed op is modeled deeply, not axiomatized). G-CONF validates the field-copy against the real `@wraps` + `inspect.signature` read-back. `str(inspect.signature(...))` ↔ `signature`; `__qualname__` ↔ `qualname`; `__module__` ↔ `module`; `__annotations__` (serialized) ↔ `annotations`; `__name__` ↔ `name`; `__doc__` ↔ `doc`. |
| 3 | `return meta` | `return manager_method` (with its propagated metadata) | I | return the produced method's resulting metadata. |

Every op is R or I; **no A row** — `functools.wraps` is the mechanism the gold
patch uses, but its effect is modeled deeply as the field copy, so no callee
property is consumed by the proof and no unchanged-callee A-reference is declared.
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs: the
shadow copies every field from `underlying`; the oracle builds the REAL pre/post
forwarding function, applies `functools.wraps`, and reads back the six
introspectable attributes. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, `create_method` copies ONLY `manager_method.__name__` and
`manager_method.__doc__` from `method`; every other introspectable attribute —
the call signature, `__qualname__`, `__module__`, `__annotations__` — keeps the
bare forwarding function's generic value. So `inspect.signature` reports
`(*args, **kwargs)`. The prepatch impl
(`implementation_delegateMetadata := { rawDelegate with name := underlying.name,
doc := underlying.doc }`) is exactly this: it propagates only `name` and `doc`.
It therefore cannot satisfy `problem_spec_delegateMetadata` on the discriminating
clauses (`result.signature = underlying.signature`,
`result.qualname = underlying.qualname`,
`result.module = underlying.module`,
`result.annotations = underlying.annotations`) whenever those fields of
`underlying` differ from `rawDelegate`'s generic placeholders — precisely the
case the FAIL_TO_PASS test `test_manager_method_signature` exercises (it asserts
`str(inspect.signature(Article.objects.bulk_create))` equals
`bulk_create`'s real parameter list, not `(*args, **kwargs)`). The carried gold
proof (`refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩`) fails to typecheck against the
buggy impl because four of the six conjuncts are no longer `rfl` (G-DIFF).
