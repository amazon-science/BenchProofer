# refinement.md — sympy__sympy-13372

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`numericComplexResult` `do` block and the deep model `evalSpec`) and `patch.diff`
(the gold patch, applied at `base_commit`). Each row is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete
operation). No kind-3 (changed-but-inexpressible) step.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

The gold hunk adds the two missing `else` clauses to the real/imaginary
classification ladders inside the `evalf` `KeyError`-fallback block
(`sympy/core/evalf.py`):

```
             elif re.is_number:
                 re = re._to_mpmath(prec, allow_ints=False)._mpf_
                 reprec = prec
+            else:
+                raise NotImplementedError
             if im == 0:
                 ...
             elif im.is_number:
                 im = im._to_mpmath(prec, allow_ints=False)._mpf_
                 imprec = prec
+            else:
+                raise NotImplementedError
             r = re, im, reprec, imprec
```

## A. The assembly/short-circuit block — `evalf` fallback (`evalf.py:1295-1312`)

| # | Solution.lean impl op (`numericComplexResult`) | patch.diff / repo op (post-patch) | tag | justification |
|---|---|---|---|---|
| A1 | parameters `realPart imagPart : Part`, `prec : Int` | `re, im = xe.as_real_imag()` (the two components) and the working precision `prec` | R | a sympy component `Expr` ↔ `Part` = (classification tag, converted-value handle); `prec : Int` is identity. The classification (`== 0`, `is_number`) and conversion (`_to_mpmath`) are UNCHANGED callees, abstracted into the carrier (mapping.md §2). |
| A2 | `if realPart.status = PartStatus.nonNumeric then return none` | the **new** `else: raise NotImplementedError` after `elif re.is_number:` | I + R | the changed control op: a non-numeric real component short-circuits with no numeric result. `raise NotImplementedError` ↔ `out = none` (R: the exception is the function's existing "not numerically evaluable" signal, caught by the caller's fall-back path — mapping.md §2). Control structure identical (I). |
| A3 | `else: if imagPart.status = PartStatus.nonNumeric then return none` | the **new** `else: raise NotImplementedError` after `elif im.is_number:` | I + R | same for the imaginary component, reached only when the real component was reportable — mirrors the sequential ladder order. |
| A4 | `else: return some { realValue := if re exact-zero then none else some re.value, … }` | `r = re, im, reprec, imprec` assembled from the `if/elif` ladders | I + R | reached only when BOTH components are reportable. Per component: exact-zero ⇒ value+prec absent (`re=None; reprec=None`), numeric ⇒ value+prec present (`re=_mpf_; reprec=prec`). `None ↔ none`; the tuple ↔ the `EvalResult` record (mapping.md §2). |
| A5 | `evalSpec` (pure region) two-way `nonNumeric ⇒ none` ladder | the post-patch net behaviour of the whole block | I | `evalSpec` is the spelled-out total function the `do` block computes; the equality `out = evalSpec …` is the verified value postcondition. |

## B. No kind-A, no kind-3

- **No consumed axiom, no A-reference deep model.** The classification and
  conversion callees (`== 0`, `is_number`, `_to_mpmath`) are UNCHANGED and are
  abstracted as read-only inputs (the `Part` carrier), pinned to no value. There
  is no unchanged library callee whose `ensures` the proof consumes, and no
  changed op hidden behind an axiom. Hence `axioms` region is empty and G-AX is
  skipped (no `axiom_check.py`).
- **The changed operation is modeled directly.** The single behaviour the fix
  adds — non-numeric component ⇒ signal "no numeric result" (`none`) instead of
  assembling a record with an unset precision — is the A2/A3 short-circuit,
  expressed with the same control/data flow as the gold `else: raise
  NotImplementedError`. No step is inexpressible.

## C. The discriminating clause and the prepatch

The behaviour-fixing operation is "a non-numeric component yields no numeric
result." `Solution.lean` returns `none` on that case (A2/A3); the frozen
discriminating postcondition is

```
(realPart.status = nonNumeric ∨ imagPart.status = nonNumeric) → out = none .
```

`Solution_prepatch.lean` reproduces the base_commit defect — it never branches
on the non-numeric case and unconditionally assembles the record (treating a
non-numeric component as if it were numeric, the model of "reprec/imprec used
when never set"). For a non-numeric component its `out = some {…}`, so
`out = none` is false → the postcondition is unprovable and `prove_correct`
fails (G-DIFF). This is exactly the `UnboundLocalError` failure mode: the
pre-patch code reaches the tuple assembly for a non-numeric component, where the
fix instead refuses to produce a result.

## D. verify(Solution) ⇒ resolved

`numericComplexResult` verifies only if its output equals `evalSpec` (A5) — in
particular `none` exactly when a component is non-numeric (A2/A3) and the
fully-reportable record otherwise (A4). By R (`Expr` component ↔ `Part`,
`raise NotImplementedError` ↔ `none`, the result tuple ↔ `EvalResult`) the
verified step is the gold-patched fallback block on the inputs the F2P test
exercises: `Mul(Max(0, y), x, evaluate=False).evalf()` reaches this block with a
non-numeric real component (`Max(0, y)·x` does not split into numeric parts), so
the patched code raises `NotImplementedError` and the caller falls back to the
ordinary evalf, returning `x*Max(0, y)` instead of crashing with
`UnboundLocalError`. The frozen spec forbids any impl that fabricates a record
for a non-numeric component, so a verifying model refined by the map above is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
trust points reduce to refinement fidelity (this doc, G-EQ); there is no axiom
soundness obligation (no consumed axiom) and no R/I numeric shadow (conf_skip,
mapping.md §5).
