# refinement.md — django__django-15731

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_proxy` impl region and the live `reported_signature` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The proxy-builder site — `create_method` (`django/db/models/manager.py:83`)

Gold hunks:
```
+from functools import wraps
 ...
 def create_method(name, method):
+    @wraps(method)
     def manager_method(self, *args, **kwargs):
         return getattr(self.get_queryset(), name)(*args, **kwargs)

-    manager_method.__name__ = method.__name__
-    manager_method.__doc__ = method.__doc__
     return manager_method
```

| # | model.py impl op (`build_proxy`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `source: Func` | `method` argument of `create_method` | R | the queryset method ↔ a `Func` carrying only the touched introspectable metadata (mapping.md §2). |
| A2 | `proxy = Func()` | `def manager_method(self, *args, **kwargs): ...` | R | constructing the forwarding proxy callable ↔ constructing the empty metadata record (mapping.md §2). |
| A3 | `proxy.sig = SIG_FORWARDING()` | the proxy's own parameter list `(self, *args, **kwargs)` | I/R | the proxy's own declared signature is the forwarding one in both worlds (`manager_method`'s body is unchanged by the patch); `SIG_FORWARDING()` ↔ that parameter list (mapping.md §1). Pinned directly by the postcondition `Result().sig == SIG_FORWARDING()` (clause 3), so a rival builder cannot substitute a differently-shaped own parameter list. |
| A4 | `proxy.name = source.name` | `@wraps(method)` copying `__name__` (was the manual `manager_method.__name__ = method.__name__`) | I/R | name copy; identical in both worlds — `functools.wraps`' `WRAPPER_ASSIGNMENTS` includes `__name__`, exactly the old manual assignment. |
| A5 | `proxy.doc = source.doc` | `@wraps(method)` copying `__doc__` (was the manual `manager_method.__doc__ = method.__doc__`) | I/R | doc copy; identical in both worlds — `WRAPPER_ASSIGNMENTS` includes `__doc__`. |
| A6 | `proxy.wrapped = True; proxy.target_sig = source.sig` | `@wraps(method)` setting `manager_method.__wrapped__ = method` | R | the **discriminating added behaviour**: `functools.wraps` records the original callable in `__wrapped__`. The model records the boolean fact plus the original's signature code (the only consequence the signature resolver observes; mapping.md §2). This is the line the pre-patch lacked. Pinned directly by the postconditions `Result().wrapped` and `Result().target_sig == source.sig` (clause 4): the recording is UNCONDITIONAL — the `@wraps(method)` decorator applies to every proxied method, never only to a sub-domain of sources — and what is recorded is exactly the source. |
| A7 | the postcondition `reported_signature(Result().wrapped, Result().target_sig) == source.sig` | the F2P observation `inspect.signature(Article.objects.bulk_create) == <bulk_create's real signature>` | A-consumed | `reported_signature` is the weakest contract on `inspect.signature` the spec needs (mapping.md §3.1): with the original recorded (A6), the resolver reports the original's signature, not the forwarding one. The proof **consumes** the axiom's `Ensures(Implies(wrapped, Result()==target_sig))`. G-AX confirms it against the real `inspect.signature` (under its default `follow_wrapped=True`, the F2P test's call). |
| A8 | `return proxy` | `return manager_method` | I | return the built proxy. |

The discriminating content of the change — recording the original callable so
the signature resolver follows it — lives in step A6
(`proxy.wrapped = True; proxy.target_sig = source.sig`) ⇔ the `@wraps(method)`
decorator setting `manager_method.__wrapped__ = method`. The pre-patch copied
only name and doc; `model_prepatch.py` reproduces that (omits A6, leaving
`proxy.wrapped == False`) and **fails** the postcondition
`reported_signature(Result().wrapped, Result().target_sig) == source.sig`,
because the resolver then returns `SIG_FORWARDING()` (the proxy's own
`(*args, **kwargs)`), which differs from a real method's signature. That is
exactly the spec sensing the change (G-DIFF), and exactly what the F2P
`test_manager_method_signature` observes (`(*args, **kwargs)` → the real
`bulk_create` signature).

The name/doc copy (A4/A5) is unchanged behaviour: `test_manager_method_attributes`
(in P2P — it passed before and after the patch) observes that `__name__`/`__doc__`
still match the source, which holds in both worlds. The spec keeps the name/doc
equality clauses so the proxy is pinned to mirror ALL three observables, not
just the signature.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
recording the original callable so signature introspection follows it — is a
type refinement (A6, the boolean `wrapped` + recorded `target_sig` standing in
for `functools.wraps`' `__wrapped__`). The only consumed axiom,
`reported_signature` (**A-consumed**, A7), covers an **unchanged** stdlib callee
(`inspect.signature`) the F2P test invokes on the proxy; the patch does not
change `inspect.signature`. There is no axiom about `functools.wraps` itself:
its single observed effect (recording the original ⇒ the resolver follows it)
is captured by the refinement A6 + the resolver axiom A7, and validated
end-to-end against the real `functools.wraps` + `inspect.signature` by
axiom_check.py (G-AX).

## C. verify(model) ⇒ resolved

`build_proxy` verifies only if the built proxy records the source it stands in
for (A6) so that `reported_signature(wrapped, target_sig) == source.sig` (A7),
AND its name/doc equal the source's (A4/A5), AND the source is left untouched
(read-only at fractional permission). By R (the `Func` record ↔ the real
callable's introspectable metadata, `SIG_FORWARDING()` ↔ the forwarding
parameter list, `wrapped`/`target_sig` ↔ `__wrapped__`) the verified builder
equals `@wraps(method)`-decorated `manager_method` on the tested inputs; by G-AX
the real `inspect.signature` meets the `reported_signature` axiom it stands in
for (A-consumed) under its default `follow_wrapped=True`, and the real
`functools.wraps` records the original so the resolver follows it. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
