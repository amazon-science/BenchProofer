# refinement.md — scikit-learn__scikit-learn-14983

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildReprValues` `do` block plus the deep `resolveOne`/`resolveAll` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the deep-model fidelity is audited by **G-AX**; the narrative by G-EQ.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The value-resolution site — `_build_repr` (`sklearn/model_selection/_split.py:2158`)

Gold hunk (the behavioural change):
```
                 value = getattr(self, key, None)
+                if value is None and hasattr(self, 'cvargs'):
+                    value = self.cvargs.get(key, None)
```

| # | Solution.lean impl op (`buildReprValues`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `keys : List String`, `attrs`, `fallback : List (String × Int)`, `hasFallback : Bool` | the loop over `args` reading `getattr(self,key,None)`, `self.cvargs`, `hasattr(self,'cvargs')` | R | type bijection (mapping.md §2): sorted param-name list ↔ `keys`; object attr table ↔ `attrs`; secondary store ↔ `fallback`; presence of the store ↔ `hasFallback`. |
| A2 | `resolveOne attrs fallback hasFallback k` = `attrs.lookup k`, and if that is `none` and `hasFallback`, then `fallback.lookup k` | `value = getattr(self,key,None)`; `if value is None and hasattr(self,'cvargs'): value = self.cvargs.get(key,None)` | A-reference + I | the changed value-resolution is modeled **deeply** by `resolveOne` (pure region). Its primitive ops — `attrs.lookup`, the `none` test, `fallback.lookup`, the `hasFallback` guard — are **I** (concrete, transliterated by G-CONF). The equality of this deep model to the real patched resolution is the **A-reference** G-AX validates. No consumed axiom. |
| A3 | result is `resolveAll … keys`: the per-key resolution collected in order, computed by the backward `while` fold | the loop populating `params[key] = value` over the sorted `args` | A-reference + I | front-recursive `resolveAll` + the verified loop ARE the ordered sweep. The fold ops (`resolveOne`, `::`, the loop) are **I**; ordered equality to the real `params` map is checked by G-AX/G-CONF. |
| A4 | (no node) | `'%s(%s)' % (class_name, _pprint(params, ...))` rendering of `params`; `__init__` introspection producing `args`; the new `__repr__` delegating to `_build_repr` | R / I (out-of-scope-unchanged) | `_pprint`, the format string, the `signature(init)` prelude and the one-line `__repr__` delegation are **unchanged** by the patch and are identity-on-content w.r.t. the resolved value map (mapping.md §2). The observable behavioural delta the F2P test sees is entirely the value map `resolveAll` pins. |

Discriminating content of the change — a parameter name absent from the object's
own attribute table but present in the secondary store now resolves to the
store's value instead of `None` — lives in the `none`-branch of `resolveOne`
(`if hasFallback then fallback.lookup key else none`) ⇔ the added
`if value is None and hasattr(self,'cvargs'): value = self.cvargs.get(key,None)`.
The pre-patch resolution read the own attribute table **only**;
`Solution_prepatch.lean` reproduces that (`attrs.lookup k`) and **fails**
`out = resolveAll …` on exactly the keys that live in `fallback` (G-DIFF — the
unsolved goal is `attrs.lookup k = resolveOne attrs fallback hasFallback k`).

## B. The `__repr__` delegation site (`_split.py:105-106` region of the patch)

The patch also adds, to the repeated-splits base class, a `__repr__` that
delegates to `_build_repr(self)`. This introduces **no new computation** beyond
invoking the modeled function: its entire observable behaviour is the string
`_build_repr` returns, whose value-resolution is modeled in §A. There is no
independent fixed behaviour here to discriminate — without §A's fallback the
delegation would still display `None` for the store-only parameters (the actual
bug). Hence no separate failing prepatch for site B (a prepatch must keep the
spec byte-identical, G-DIFF); site A's prepatch already exercises the shared
resolution logic that both observable F2P cases depend on.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — value
resolution gaining a secondary-store fallback — is modeled **deeply** (the
spelled-out `resolveOne`/`resolveAll`, step A2/A3, an A-reference + I), not
hidden behind an axiom about the function under change. There are **no consumed
axioms**: the `axioms` region is empty, and the only modeled callees are the two
total dictionary reads, which are concrete `List.lookup` ops (I).

## D. verify(Solution) ⇒ resolved

`buildReprValues` verifies only if its output equals, in order, the exact
per-key resolution with the secondary-store fallback (A2/A3). By R (the type
bijections of mapping.md §2; `_pprint`/format/introspection identity-on-content,
A4) the verified resolution equals the patched `_build_repr`'s value map on the
tested object states; by G-AX the deep model `resolveOne`/`resolveAll` equals
the real patched resolution (A-reference); by G-CONF the R/I transliteration
agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed object states. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The single trust
point is refinement/deep-model fidelity (this doc + G-AX + G-CONF); there is no
axiom-soundness trust point because no axiom is consumed.
