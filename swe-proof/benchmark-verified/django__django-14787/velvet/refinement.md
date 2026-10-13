# refinement.md — django__django-14787

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildPresentedAttrs` `do` block, the deep `mergePlan`/`mergeAt` model, and the
`lookupAttr`/`firstDefined` helpers) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**
where the proof uses an axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed site — `_wrapper`'s bound callable (`django/utils/decorators.py:40`)

Gold hunk:
```
- bound_method = partial(method.__get__(self, type(self)))
+ bound_method = wraps(method)(partial(method.__get__(self, type(self))))
```

`bound_method` is the object subsequently handed to each user decorator
(`for dec in decorators: bound_method = dec(bound_method)`). The fix wraps the
attribute-less `partial` with `wraps(method)` so that the object the decorators
introspect presents `method`'s function-identity attributes
(`__name__`, `__qualname__`, `__module__`, …) instead of the `partial`'s
(which lacks `__name__` entirely).

| # | Solution.lean impl op (`buildPresentedAttrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `methodAttrs : List (String × String)` | `method`'s attribute environment (the `wraps(method)` source) | R | object attribute env ↔ assoc list (mapping.md §2). |
| A2 | param `baseAttrs : List (String × String)` | the `partial(method.__get__(self, type(self)))` object's own attribute env (the wrap target) | R | same bijection; the `partial` defines `__module__`/`__doc__` but not `__name__`/`__qualname__`. |
| A3 | param `names : List String` | `functools.WRAPPER_ASSIGNMENTS` (the names `update_wrapper` copies) | R | identical name sequence (mapping.md §2). |
| A4 | result `mergePlan methodAttrs baseAttrs names`: per name, the source value when present else the base value, computed by the backward `while` fold | `wraps(method)(partial(...))` — i.e. `update_wrapper(partial, method)` — observed per assigned name | A-reference + I | the changed wrap operation is modeled **deeply**: `mergeAt`/`firstDefined`/`lookupAttr` (pure region) and the verified loop ARE the per-name overlay. No consumed `updateWrapper` axiom. The fold ops (`mergeAt n`, `::`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `functools.update_wrapper` is the **A-reference** G-AX validates. mapping.md §3.1. |

Discriminating content of the change — for any name the source object defines but
the bare object lacks (canonically `__name__`), the presented value becomes the
source's (`some method_name`) rather than absent (`none`) — lives in
`mergeAt methodAttrs baseAttrs n = firstDefined (lookupAttr methodAttrs n) (lookupAttr baseAttrs n)`
(model) ⇔ the `getattr(method, n)` → `setattr(bound_method, n, …)` step of
`update_wrapper` (real). The pre-patch presented only `baseAttrs`
(`lookupAttr baseAttrs n`); `Solution_prepatch.lean` reproduces that and **fails**
`out = mergePlan methodAttrs baseAttrs names` (G-DIFF) on exactly the names where
`methodAttrs` and `baseAttrs` disagree (e.g. `__name__`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — wrapping
the bare callable so it presents the source object's identity attributes — is
modeled **deeply** (the spelled-out per-name overlay `mergePlan`, step A4, an
A-reference + I), not hidden behind an axiom about the changed expression. There
is **no consumed axiom** in this bundle (`axioms` region empty); the only
kind-A element is the A-reference `mergePlan == functools.update_wrapper`,
validated by G-AX against the real unchanged stdlib callee.

## C. verify(Solution) ⇒ resolved

`buildPresentedAttrs` verifies only if its output equals the exact per-name
overlay `mergePlan` (A4): for every assigned name, the method's value when the
method defines it, else the bare object's. By R (object attribute env ↔ assoc
list; `WRAPPER_ASSIGNMENTS` ↔ `names`) the verified result equals the per-name
observation of `wraps(method)(partial(...))` on the tested inputs; by G-AX the
deep model `mergePlan` equals the real `functools.update_wrapper` (A-reference);
by G-CONF the R/I transliteration of the fold agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs (including the exact django F2P scenario). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
