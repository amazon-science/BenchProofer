# refinement.md — django__django-14787

The operation-by-operation correspondence between `model.py`'s implementation
(the `assemble_bound_callable` impl region — including the spelled-out
wrapper-identity copy, the deep model) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The bound-callable assembly — `_multi_decorate(...)._wrapper` (`django/utils/decorators.py:35-43`)

Gold hunk (the one change, at `decorators.py:40`):
```
-        bound_method = partial(method.__get__(self, type(self)))
+        bound_method = wraps(method)(partial(method.__get__(self, type(self))))
         for dec in decorators:
             bound_method = dec(bound_method)
         return bound_method(*args, **kwargs)
```

The decorator chain `for dec in decorators: bound_method = dec(bound_method)`
hands `bound_method` to each user decorator `dec`, which routinely inspects
`bound_method.__name__` / `__module__` (e.g. `@wraps(func)` inside the user's
decorator, or logging `func.__name__`). The bug: `partial(...)` carries no
`__name__`, so that inspection raises `AttributeError` (the problem statement's
exact trace). The fix wraps the partial with `wraps(method)(...)`
(`functools.update_wrapper`), copying the method's wrapper-identity attributes
onto it.

| # | model.py impl op (`assemble_bound_callable`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `method: FuncIdentity` with facets `has_name/name`, `has_module/module` | the `method` argument reached via `method.__get__(self, type(self))`; its `__name__`/`__module__` | R | the original method's behaviour-bearing wrapper-identity attributes modelled as `(presence, int token)` pairs (mapping.md §1, §2). `__get__`/`type(self)`/`self` are call-shape producing a bound callable with no caller-relevant identity of its own; not behaviour the change/test observes. |
| A2 | the bare partial application (the `update_wrapper` *target*) that on its own exposes no identity metadata | `partial(method.__get__(self, type(self)))` — the bare partial application | R | the partial exposes no `__name__` (and no method-relevant `__module__`); the all-absent identity. Pre-patch this absence is the assembled callable's final state (modelled by `FuncIdentity(False, 0, False, 0)` in `model_prepatch.py`); post-patch it is the pre-copy target that `update_wrapper` overwrites — so in the patched model the absent placeholder is dead under the contracted domain (both attributes get copied) and is elided to its post-copy result (A3). (mapping.md §2.) |
| A3 | `has_name/name/has_module/module = method.has_name/name/has_module/module; bound = FuncIdentity(has_name, name, has_module, module)` — the assembled callable carries, for each attribute the method has, that attribute marked present with the method's value | `wraps(method)(…)`  ⇒  `functools.update_wrapper(partial, method)` | **A-reference** | the changed operation is modelled **deeply**: the construction IS the `update_wrapper` per-attribute copy specialized to the two behaviour-bearing WRAPPER_ASSIGNMENTS (`__name__`, `__module__`). `update_wrapper` copies the attributes the wrapped object *has*; the precondition pins that the method has both (a real function/method always does), so the copy yields exactly `(present, method.name)` and `(present, method.module)` — written directly as the contracted-domain result (no throwaway placeholder constant; this also removes dead G-MUT mutants). There is **no consumed `update_wrapper` axiom**; the deep model is validated **== the real callee** by G-AX (axiom_check.py runs the real `wraps`/`update_wrapper` and asserts the wrapped partial's `__name__`/`__module__` equal the method's, and the method is unchanged). mapping.md §3.1. |
| A4 | `return bound` (the assembled `FuncIdentity` the caller inspects) | `bound_method = <the wrapped partial>`; subsequently `dec(bound_method)` and `bound_method(*args, **kwargs)` | R | `update_wrapper` returns the same (now-updated) object, which is what flows into the decorator chain; the model returns the assembled object carrying the copied facets. The downstream `for dec` / call are not part of the change and do not alter the assembled callable's identity attributes (mapping.md §2). |

The discriminating content of the change — the assembled callable now carries
`method.__name__` (and `__module__`) where before it had none — lives in step
**A3** (the deep copy) and is sensed by the postconditions `Result().has_name`,
`Result().name == method.name`, `Result().has_module`,
`Result().module == method.module`.

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it drops step **A3** entirely
(the assembled callable is the bare partial, no identity copied) exactly as the
pre-patch line is `bound_method = partial(...)` without the `wraps(method)(...)`
wrap. With the byte-identical frozen spec it **fails** verification on the
postcondition `Ensures(Result().has_name)`
(`model_prepatch.py:77` — `Assertion Result().has_name might not hold`). That is
precisely the behaviour the F2P test observes: `test_wrapper_assignments`
applies a decorator whose inner reads `getattr(func, '__name__', None)` and
asserts `func_name == 'method'`; pre-patch `partial` has no `__name__`, so
`func_name` is `None ≠ 'method'`. The spec is therefore strong enough that no
implementation omitting the identity copy can verify (spec sees the bug).

The companion clauses `Result().module == method.module` / `Result().has_module`
pin the module copy (the test's `assertIsNotNone(func_module)`), and the
read-only clauses `method.name == Old(method.name)` /
`method.module == Old(method.module)` (held under the fractional
`Acc(method.*, 1/2)` permission, directive 5) forbid a wrong impl from
satisfying the spec by mutating the method instead of producing a correctly
assembled fresh callable.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — wrapping the partial so it carries the method's identity — is
modelled **deeply** (the spelled-out per-attribute copy in the impl region,
step **A3**, an **A-reference**), not hidden behind an axiom about the function
under change. There is **no consumed `@ContractOnly` axiom** in this bundle: the
only kind-A construct is the **A-reference** deep model of the unchanged stdlib
primitive `functools.update_wrapper`/`wraps`, which the new code invokes and
which G-AX validates the deep model against. We never axiomatize the function
under change (the assembly inside `_wrapper`, i.e. `assemble_bound_callable`).

## D. verify(model) ⇒ resolved

`assemble_bound_callable` verifies only if (A3) it copies the method's present
identity attributes onto the assembled callable — so `Result().has_name` and
`Result().name == method.name` (and likewise module) hold — and only if it
leaves the method unmodified. By R (the partial ↔ the all-absent `FuncIdentity`;
`__name__`/`__module__` ↔ the `(presence, token)` pairs; `str` value-equality
↔ token equality) and the deep copy (A3), the verified assembly equals the gold
`wraps(method)(partial(method.__get__(self, type(self))))` on the tested method:
the assembled callable handed to the decorator chain carries
`__name__ == method.__name__` and `__module__ == method.__module__`. By G-AX the
real `functools.wraps`/`update_wrapper` performs exactly that copy (the
A-reference) and does not mutate the method. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited stdlib reference — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: axiom/reference soundness (G-AX) and
refinement fidelity (this document, G-EQ).
