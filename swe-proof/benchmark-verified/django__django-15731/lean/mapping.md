# mapping.md — django__django-15731

## Symbol binding (file:line @ base_commit 93cedc82f29076c824d476354527af1150888e4f)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_delegateMetadata` / `problem_spec_delegateMetadata` | `create_method`'s construction of the inner forwarding function's introspectable metadata | `django/db/models/manager.py:83-89` |
| `MethodMetadata` (pure structure) | the introspectable-metadata attributes of a Python function (`__name__`, `__qualname__`, `__module__`, `__doc__`, `__annotations__`, and the call signature `inspect.signature(...)` exposes) | the attributes read by `inspect.signature` / `inspect.getmembers` on the produced method |
| `underlying : MethodMetadata` | `method` — the source queryset method whose metadata should be mirrored | `create_method(name, method)` parameter, `manager.py:83` |
| `rawDelegate : MethodMetadata` | the freshly-`def`-ined inner forwarding function `manager_method` BEFORE any metadata propagation — it carries the generic catch-all signature `(*args, **kwargs)`, its own `__qualname__`/`__module__`, no docstring | `manager.py:84-85` |

The modeled function is the metadata-construction performed by `create_method`. It
is the only behavior the patch changes and the behavior the FAIL_TO_PASS test
`test_manager_method_signature` observes (it asserts
`str(inspect.signature(Article.objects.bulk_create))` equals the real
parameter list, not `(*args, **kwargs)`), together with the PASS_TO_PASS
`test_manager_method_attributes` (asserts the produced method's `__doc__` /
`__name__` equal the source method's).

### What the function does (base_commit)

```python
@classmethod
def _get_queryset_methods(cls, queryset_class):
    def create_method(name, method):
        def manager_method(self, *args, **kwargs):
            return getattr(self.get_queryset(), name)(*args, **kwargs)

        manager_method.__name__ = method.__name__      # <-- only name ...
        manager_method.__doc__ = method.__doc__         # <-- ... and docstring copied
        return manager_method
    ...
```

Step by step:
1. `def manager_method(self, *args, **kwargs)` — a generic forwarding function.
   Its intrinsic introspectable metadata is the catch-all signature
   `(self, *args, **kwargs)`, qualname `…create_method.<locals>.manager_method`,
   module `django.db.models.manager`, and no docstring.
2. base_commit copies ONLY `__name__` and `__doc__` from `method` onto it. Every
   OTHER introspectable attribute — the call signature, `__qualname__`,
   `__module__`, `__annotations__` — keeps the generic forwarding function's
   value. So `inspect.signature(manager_method)` returns `(*args, **kwargs)`.
3. The post-patch propagates the FULL introspectable metadata bundle of `method`
   onto the forwarding function, so signature/qualname/module/annotations/name/
   docstring all observe `method`'s values.

### Lean modeling

- `MethodMetadata` is a structure holding the touched observable attributes:
  `name`, `qualname`, `module`, `doc`, `annotations`, `signature` (each modeled
  as a `String` — only equality is observed; `signature` is the rendered
  parameter list `str(inspect.signature(...))`, `annotations` a serialization of
  `__annotations__`).
- `underlying : MethodMetadata` is the source method's metadata (the queryset
  method being delegated to).
- `rawDelegate : MethodMetadata` is the bare forwarding function's intrinsic
  metadata before any propagation: the generic catch-all signature, the
  forwarding function's own qualname/module, empty docstring/annotations.
- `delegateMetadata underlying rawDelegate` builds the delegating method's
  resulting metadata. Post-patch: every field is taken from `underlying`.
  Pre-patch: only `name` and `doc` are taken from `underlying`; the rest stay at
  `rawDelegate`'s generic values.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| a function's introspectable metadata `(__name__, __qualname__, __module__, __doc__, __annotations__, str(inspect.signature(...)))` | `MethodMetadata` | tuple of strings ↔ the six structure fields; `None` doc/annotations ↔ `""`. |
| the source queryset `method` | `underlying : MethodMetadata` | its real metadata tuple. |
| the bare `def manager_method(self,*args,**kwargs)` before propagation | `rawDelegate : MethodMetadata` | name `"manager_method"`, qualname `"…manager_method"`, module `"django.db.models.manager"`, doc `""`, annotations `""`, signature `"(self, *args, **kwargs)"`. |
| the metadata of the method RETURNED by `create_method` | `delegateMetadata underlying rawDelegate` result | the six observed attributes of the produced method. |

The result of the modeled construction is the produced method's observable
metadata tuple. We model it as the resulting `MethodMetadata`.

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The behavior the patch changes —
  which introspectable attributes the produced method exposes — is modeled DEEPLY
  as a field-by-field copy of the `MethodMetadata` carrier (SPEC_GUIDE §3: a
  deeply-modeled changed op is never axiomatized). `functools.wraps` is the
  mechanism the gold patch uses, but its EFFECT (copy the
  `WRAPPER_ASSIGNMENTS` attributes + make `inspect.signature` follow to the
  underlying method) is exactly the field-copy we model; no opaque callee
  contract is consumed by the proof. Hence the `axioms` region is empty and
  **G-AX skips**.
- `getattr(self.get_queryset(), name)(*args, **kwargs)` — the runtime call the
  forwarding function performs — is UNCHANGED by the patch and is not part of the
  modeled metadata behavior. The patch touches only the produced method's
  *metadata*, not its call semantics; so the call body is not modeled. Its
  omission constrains no output component the spec leaves free — the spec pins
  every metadata field.
- `inspect.getmembers(queryset_class, predicate=inspect.isfunction)` and the
  `queryset_only`/`startswith('_')` filtering loop (`manager.py:92-104`) select
  WHICH methods get a delegate; they are unchanged by the patch and do not affect
  any single produced method's metadata, so they are not modeled.

## functools.wraps semantics confirmed (base_commit env)

`functools.WRAPPER_ASSIGNMENTS == ('__module__', '__name__', '__qualname__',
'__doc__', '__annotations__', '__type_params__')` and `WRAPPER_UPDATES ==
('__dict__',)`; `@wraps(method)` additionally sets `wrapper.__wrapped__ =
method`, which makes `inspect.signature(wrapper)` follow through to `method`'s
signature. Verified in-process: the pre-patch wrapper reports
`(self, *args, **kwargs)`; the post-patch (`@wraps`) wrapper reports the source
method's real parameter list. The model's `signature` field captures exactly this
observable.

## G-CONF fuzz seed

Pinned LCG seed: **15731** (see `conformance_check.py` `SEED`). Corpus: randomized
`(underlying, rawDelegate)` metadata pairs — `underlying` drawn with varied
name/qualname/module/doc/annotations/signature strings (so each field genuinely
differs from `rawDelegate`'s generic values), `rawDelegate` drawn from the
generic-forwarding-function shape (catch-all signature, own qualname/module,
empty doc) — over ≥1e5 fuzzed inputs. The R/I shadow of
`implementation_delegateMetadata` (copy every field from `underlying`) is diffed
against an in-process replica that builds the REAL pre/post forwarding function,
applies `functools.wraps`, and reads back `(__name__, __qualname__, __module__,
__doc__, __annotations__, str(inspect.signature(...)))`. Hand-picked edge cases
pin the discriminating clause: an `underlying` whose signature ≠
`(self, *args, **kwargs)` (the exact F2P shape — `bulk_create`'s real parameter
list must surface).
