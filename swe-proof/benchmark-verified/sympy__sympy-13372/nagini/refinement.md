# refinement.md — sympy__sympy-13372

The operation-by-operation correspondence between `model.py`'s implementation
(the `assemble_evalf_result` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, proof uses the axiom's `Ensures`/`Requires`, and
**A-reference**, a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The classification chains — `evalf` fallback (`sympy/core/evalf.py:1298-1310`)

Gold hunks (add the missing `else` to each `if part == 0 / elif part.is_number`
chain):
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

| # | model.py impl op (`assemble_evalf_result`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `re_kind: int ∈ {0,1,2}` | the three-way classification of `re` (`re == 0` / `elif re.is_number` / neither) | R | each branch outcome ↦ a case tag (mapping.md §2): `0` ↔ `re == 0`, `1` ↔ `re.is_number`, `2` ↔ neither. Mutually exclusive and exhaustive on the chain. |
| A2 | parameter `im_kind: int ∈ {0,1,2}` | the three-way classification of `im` | R | identical to A1 for the imaginary part. |
| A3 | `if re_kind == 0: reprec = None` | `if re == 0: re = None; reprec = None` | R + I | the exact-zero branch sets the precision component absent. The value assignment `re = None` is independent of the precision bug and is abstracted away (only `reprec` is the touched component, mapping.md §2). |
| A4 | `elif re_kind == 1: reprec = prec` | `elif re.is_number: re = re._to_mpmath(prec,...)._mpf_; reprec = prec` | R + I | the numeric branch sets the precision component to the working precision `prec`. The `_to_mpmath` value computation is independent of the precision bug and abstracted (mapping.md §2,§3); `reprec = prec` ↔ `reprec = prec` identically. |
| A5 | `else: raise EvalfDeferred()` (real part) | `else: raise NotImplementedError` (the ADDED branch) | R + I | **the fix.** A part that is neither exact-zero nor numeric defers instead of falling through. `NotImplementedError` ↦ the user-defined `EvalfDeferred` (a builtin exception in an `Exsures` crashes the translator, mapping.md §2); the discriminating observable is the deferral (caught by the surrounding `except`/fallback), preserved by the stand-in. |
| A6 | the `im_kind` `if/elif/else` block (`imprec = None` / `imprec = prec` / `raise EvalfDeferred()`) | the second gold hunk (the `im` chain + its added `else: raise NotImplementedError`) | R + I | identical to A3-A5 for the imaginary part. |
| A7 | `return EvalfResult(reprec, imprec)` | `r = re, im, reprec, imprec` | R | the result-assembly. The tuple ↦ the `EvalfResult` carrying only the two touched precision components (mapping.md §2). Reached only when both parts are exact-zero or numeric — i.e. only when both `reprec` and `imprec` are defined — which the added `else` raises guarantee. |

The discriminating content of the change — a part that is neither the exact
zero nor a number must DEFER (so the precision component is never read unset),
rather than fall through to assemble the result — lives in steps A5/A6 (the
added `else: raise`). The pre-patch chains had no `else`; `model_prepatch.py`
reproduces that (it drops the two `else: raise EvalfDeferred()` branches, so on
an OTHER part the precision local keeps its placeholder and the function reaches
the result-assembly) and **fails** verification on the postcondition
`re_kind != 2 and im_kind != 2` — the formal face of `r = re, im, reprec,
imprec` reading the unbound `reprec`/`imprec`. That is exactly the spec sensing
the change (G-DIFF), and the exact F2P observation: `Mul(Max(0, y), x,
evaluate=False).evalf()` must not crash with `UnboundLocalError` — it must defer
(`NotImplementedError`) so `evalf` falls back and returns `x*Max(0, y)`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — adding the
`else: raise NotImplementedError` so an unrepresentable part defers instead of
falling through to read an unset precision component — is modeled **directly**
by the `else: raise EvalfDeferred()` branches (steps A5/A6) over the integer
case tags. There is **no consumed axiom** and **no A-reference deep model**: the
surrounding callees (`as_real_imag`, `== 0`, `is_number`, `_to_mpmath`) are
UNCHANGED and are not the source of the bug; the model abstracts the *outcome*
of the classification (`re_kind`/`im_kind`) and pins only the precision-component
assignment and the must-defer obligation, which is the whole changed delta.

## C. verify(model) ⇒ resolved

`assemble_evalf_result` verifies only if (a) it returns normally exactly when
both parts are exact-zero or numeric — the postcondition `re_kind != 2 and
im_kind != 2` is unprovable on an OTHER part unless that case raises (this is
what `model_prepatch.py` fails on), (b) each assembled precision component is
exactly the one its part's case demands (`Result().reprec is
part_precision(re_kind, prec)`, absent for exact-zero, `prec` for numeric), and
(c) it defers (`Exsures(EvalfDeferred, re_kind == 2 or im_kind == 2)`) exactly
when some part is the OTHER case. By R (`re`/`im` classification ↦ case tags;
the precision-component assignment ↦ `part_precision`; `NotImplementedError` ↦
`EvalfDeferred`; the result tuple ↦ `EvalfResult`) the verified function equals
the patched `evalf` fallback on the tested inputs: on the F2P input the real
part `Max(0, y)` is the OTHER case, so the patched code raises
`NotImplementedError` and the model raises `EvalfDeferred`, both deferring to
the caller's fallback (which yields `x*Max(0, y)`); the pre-patch read the
unbound `reprec`. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There is no axiom trust point (no consumed `@ContractOnly`); the
sole trust point is refinement fidelity (this document, G-EQ).
