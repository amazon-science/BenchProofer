# refinement.md — django__django-15731

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildForwarderMeta` `do` block and the deep `propagate` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (modeled
callee — **A-consumed** where the proof uses an axiom's `ensures`, **A-reference**
where a deep model is validated == the real facility by G-AX), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested observables, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The proxy-builder — `create_method` (`django/db/models/manager.py:83-89`)

Gold hunk:
```
     def create_method(name, method):
+        @wraps(method)
         def manager_method(self, *args, **kwargs):
             return getattr(self.get_queryset(), name)(*args, **kwargs)

-        manager_method.__name__ = method.__name__
-        manager_method.__doc__ = method.__doc__
         return manager_method
```
(plus the new `from functools import wraps` import.)

| # | Solution.lean impl op (`buildForwarderMeta`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `target : CallableMeta` | `method` arg of `create_method` (the queryset method being proxied) | R | a Python callable's introspectable identity ↔ `CallableMeta` (mapping.md §2): `target.name ↔ method.__name__`, `target.doc ↔ method.__doc__ or ""`, `target.sig ↔ str(inspect.signature(method))`. |
| A2 | parameter `forwarder : CallableMeta` | the inner `manager_method` BEFORE metadata is conferred (`manager.py:84`) | R | the raw proxy's introspectable triple: `forwarder.sig ↔ "(*args, **kwargs)"` (the generic forwarding signature), `forwarder.name ↔ "manager_method"`. Read-only frame (mapping.md §2.1): no field of `forwarder` appears in the result. |
| A3 | `return propagate forwarder target` — the result's `name`, `doc`, AND `sig` are all `target`'s | `@wraps(method)` confers `method`'s full metadata onto `manager_method` (copying `__name__`/`__doc__` and setting `__wrapped__ = method`) | A-reference + I | the changed metadata-propagation operation is modeled **deeply**: `propagate` (pure region) IS the propagation, taking every observed field from `target`. There is no consumed `wraps` axiom. The op (`propagate forwarder target`, a record build) is **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `functools.wraps` effect on the three observed fields is the **A-reference** G-AX validates. mapping.md §3.1. |

Discriminating content of the change — the proxy's **call signature** must
resolve to the target's (`out.sig = target.sig`), not stay the wrapper's generic
`(*args, **kwargs)` — lives in `propagate`'s `sig := target.sig` field (model) ⇔
the `__wrapped__ = method` link `@wraps` sets, which `inspect.signature` follows
(real). The pre-patch copied only `__name__`/`__doc__`, leaving the generic
signature; `Solution_prepatch.lean` reproduces that (`sig := forwarder.sig`) and
**fails** `out.sig = target.sig` (G-DIFF) while still satisfying the name/doc
clauses — exactly the F2P `test_manager_method_signature` failure.

## B. No A-consumed axioms

`get_queryset()` and the forwarded `getattr(...)(*args, **kwargs)` call
(`manager.py:84-85`) are UNCHANGED by the patch, and the run-time behaviour they
implement is NOT observed by the F2P/P2P tests this bundle pins — those tests
introspect the wrapper's metadata (`__name__`, `__doc__`,
`inspect.signature(...)`), they never invoke the proxy against a database. They
are therefore not modeled at all; modeling them would be a dead axiom (SPEC_GUIDE
§3 / directive 7). The single trust point is the A-reference of A3.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
metadata propagation `manual name+doc copy → @functools.wraps` — is modeled
**deeply** (the spelled-out record build `propagate`, step A3, an A-reference + I),
not hidden behind an axiom about the function under change: there is no consumed
`wraps` axiom, and `create_method` itself (the function under spec) is never
axiomatized. The frozen spec pins exactly the three introspectable observations
the issue and the F2P tests demand (name, doc, signature).

## D. verify(Solution) ⇒ resolved

`buildForwarderMeta` verifies only if its result's name, doc, AND signature all
equal `target`'s (A3 — the three `ensures`). By R (a callable's introspectable
triple ↔ `CallableMeta`, mapping.md §2) the verified builder produces a wrapper
whose `(__name__, __doc__, str(inspect.signature(·)))` equals the proxied
queryset method's — which is exactly what the patched `create_method` produces
via `@functools.wraps(method)`. By G-AX the deep model `propagate` equals the real
`functools.wraps` effect on the three observed fields (A-reference), including the
`__wrapped__`-following signature resolution. By G-CONF the R/I transliteration of
`propagate` agrees with `patch.diff`'s behaviour — the real patched
`_get_queryset_methods` wrappers + reconstructed `create_method` over ≥10⁵ fuzzed
callables. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited facility — and the gold
patch resolves (G-RESOLVE). The single trust point is the A-reference of A3,
audited by G-AX (soundness) and this doc + G-CONF (refinement fidelity).
