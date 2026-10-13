# refinement.md — astropy__astropy-7336

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `processReturn` `do` block + the `coerceUnit` deep model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-reference**
(deep model validated == the real callee by G-AX), or **I** (identical concrete
op). There are no consumed axioms.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg + this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The return post-processing tail — `wrapper` (`astropy/units/decorators.py:223-226`)

Gold hunk:
```
- if wrapped_signature.return_annotation is not inspect.Signature.empty:
+ if wrapped_signature.return_annotation not in (inspect.Signature.empty, None):
      return return_.to(wrapped_signature.return_annotation)
  else:
      return return_
```

| # | Solution.lean impl op (`processReturn`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `annot : Annot` | `wrapped_signature.return_annotation` | R | `inspect.Signature.empty ↔ .absent`, `None ↔ .nullAnnot`, a unit ↔ `.target u` (mapping.md §2). G-CONF bridges the three shapes. |
| A2 | parameter `ret : RetVal` | `return_` (the wrapped result) | R | `None ↔ .null`, a `Quantity` of unit `u` ↔ `.quantity u`; only the unit is observed (mapping.md §2). |
| A3 | the guard `annotated := match annot with .absent => false \| .nullAnnot => false \| .target _ => true` | `return_annotation not in (inspect.Signature.empty, None)` | I | the **changed** op. The fixed guard is true exactly for a genuine unit target; both the empty sentinel and the null sentinel route to pass-through. Transliterated 1:1 by G-CONF. This is the single behavioural change `test_return_annotation_none` observes. |
| A4 | when `annotated`: `coerceUnit ret (annotTarget annot)` | `return_.to(wrapped_signature.return_annotation)` | A-reference + I | the unchanged unit re-expression callee, modeled deeply by `coerceUnit` and validated == real `.to` by G-AX (mapping.md §3.1). The branch (`if annotated then …`) and target selection are **I**; the equality of the deep model to real `.to` is the **A-reference**. `coerceUnit` is **partial on dimensional compatibility**: it yields `.ok (.quantity t)` only when source and target share a measurement kind (`compatible`), and `.error .notCompatible` otherwise — matching real `.to`, which raises `UnitConversionError` on a different-kind target (e.g. `(3 h).to(kg)`); and `.error .noConvertOp` on the null value (the `None.to` `AttributeError` crash). |
| A5 | otherwise: `Except.ok ret` | `return return_` | I | the pass-through branch; the result is handed back unchanged. |

Discriminating content of the change — a `.nullAnnot` annotation (repo `None`)
routes to **pass-through**, not to `.to` — lives in `processReturnSpec
.nullAnnot ret = Except.ok ret` (model) ⇔ the added `, None` in the guard tuple
(real). The pre-patch guard fired `.to` on `None`-annotated results;
`Solution_prepatch.lean` reproduces that (`nullAnnot => true`) and **fails**
`out = processReturnSpec annot ret` on the `.nullAnnot` case (G-DIFF), because
`coerceUnit .null _ = .error .noConvertOp ≠ Except.ok .null` — the modeled
analogue of the real `AttributeError`.

## B. No consumed axioms

The only callee, `.to`, is modeled deeply (`coerceUnit`, an A-reference checked
by G-AX), not consumed as an axiom. The function under change (the guard) is
never axiomatized (SPEC_GUIDE §0.7).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the guard predicate — is modeled concretely (step A3, **I**), with its abstract
desired behavior pinned by `processReturnSpec`. The re-expression callee it
guards is unchanged and modeled deeply.

## D. verify(Solution) ⇒ resolved

`processReturn` verifies only if its output equals `processReturnSpec annot ret`
for **all** `annot, ret` — in particular the `.nullAnnot` case must hand the
result back unchanged (A3/A5), and the `.target` case must re-express via the
real `.to` semantics (A4). By R (`annotation/return ↔ Annot/RetVal`, only the
unit observed) the verified tail equals the patched
`return_.to(...) if … not in (empty, None) else return_` on the tested inputs;
by G-AX the deep model `coerceUnit` equals the real `.to` (incl. the `None.to`
crash, an A-reference); by G-CONF the R/I transliteration of the guard agrees
with `patch.diff`'s patched-wrapper behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: deep-model fidelity (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
