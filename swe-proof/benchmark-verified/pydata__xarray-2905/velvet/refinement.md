# refinement.md — pydata__xarray-2905

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`prepareData` `do` block + the `forwarded` pure model) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
A-consumed / A-reference), or **I** (identical concrete op). EVERY step is R, A,
or I; no kind-3 (changed inexpressible op).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change — `as_compatible_data` (`xarray/core/variable.py:220–221`)

Gold hunk:
```
     # we don't want nested self-described arrays
-    data = getattr(data, "values", data)
+    if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)):
+        data = data.values
```

| # | Solution.lean impl op (`prepareData`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `w : Incoming` (`obj`, `valuesPayload`, `isRecognized`) | the live `data` object reaching line 220 | R | opaque-identity modeling (mapping.md §2): the slice observes only the object's identity, the presence/identity of its `.values`, and whether it is a recognized container type — never array content. Same shape as astropy__astropy-14096. |
| A2 | `if w.isRecognized then …` | `if isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` | R | the recognized-container type predicate ↔ `isRecognized : Bool` (mapping.md §2). The unchanged `isinstance`/pandas types; its outcome is the free input `isRecognized`. |
| A3 | recognized arm: `w.valuesPayload.getD w.obj` | `data = data.values` | R + I | take the stored values payload. `getD w.obj` is total; the `require` (`isRecognized → valuesPayload.isSome`) guarantees the genuine payload is taken, matching `data.values`. The selection itself is concrete (I) over the R-refined carrier. |
| A4 | other arm: `w.obj` (object forwarded unchanged) | `data` left untouched (the `if` did not fire) | R + I | forward the object itself. This is the behavioural change: under the pre-patch `getattr(data, "values", data)` an unrecognized object exposing `.values` was replaced by its payload; the fix forwards it unchanged. Modeled deeply by the `else w.obj` arm of `forwarded`. |

The discriminating content of the change — **an unrecognized object that exposes
a `.values` payload is forwarded as itself, not unwrapped** — lives in
`forwarded w = w.obj` when `w.isRecognized = false` (regardless of
`w.valuesPayload`). The pre-patch unwrapped on the mere presence of a payload;
`Solution_prepatch.lean` reproduces that (`match w.valuesPayload with | some v =>
v | none => w.obj`) and **fails** `out = forwarded w` exactly on the
`isRecognized = false ∧ valuesPayload = some v` case (G-DIFF).

## B. No consumed axioms, no deep-model references

No callee contract is consumed (`axioms` is empty) and no callee is modeled as an
external reference. The two primitives the dispatch performs —
`isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` and the `.values`
attribute access — are unchanged Python/pandas reflection whose outcomes are
carried as the free inputs `isRecognized` and `valuesPayload` (mapping.md §3).
The spec holds for every value those observables can take, so there is nothing to
validate against a real callee: **G-AX is not applicable** (no `axiom_check.py`;
auto-skips), as in astropy__astropy-14096.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, R+I, or I. The operation that genuinely *changed* — narrowing
the unwrap from "any object with a `.values` attribute" to "only the recognized
self-describing container types" — is modeled **deeply** by `forwarded`'s
two-arm dispatch on `isRecognized` (A2/A3/A4), not hidden behind an axiom about
the function under change. There is no consumed axiom anywhere.

## D. G-CONF — conf_skip (see mapping.md §4)

`conf_skip=true`. The modeled op's only discriminating observable is the
**identity** of the forwarded object — an arbitrary user object with a `.values`
attribute must be returned as itself, which materializes only against the live
CPython type system + numpy object-array machinery (the F2P test
`test_unsupported_type`), with no interpreter-free, input-dependent R/I shadow to
fuzz. Both arms select among free inputs (A3/A4) with no content computation. The
R/I fidelity of the dispatch is instead pinned by G-VERIFY and discriminated by
G-DIFF. Precedent: astropy__astropy-14096, django__django-11451.

## E. verify(Solution) ⇒ resolved

`prepareData` verifies only if its output equals `forwarded w`: the recognized
container is unwrapped to its payload (A3) and **every other object — including
one exposing a `.values` payload — is forwarded unchanged** (A4). By R
(opaque-identity carrier, the `isRecognized`/`valuesPayload`/`obj` correspondence
of mapping.md §2) the verified dispatch equals the post-patch
`if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)): data = data.values`
on the object reaching line 220. The pre-patch bug (`getattr(data, "values",
data)`) is exactly the prepatch skeleton, which fails the A4 clause (G-DIFF).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The single
trust point is refinement fidelity (this doc, G-EQ); there are no consumed axioms
(no G-AX) and no R/I shadow to differential-test beyond what G-VERIFY pins
(conf_skip, G-CONF).
