# refinement.md — django__django-15863

The operation-by-operation correspondence between `model.py`'s implementation
(the `reconstruct_digits` impl region and the deep `narrowed_to_significand`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated `==` a real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The reconstruction site — `floatformat` (`django/template/defaultfilters.py:153-160`)

Gold hunk:
```
     try:
-        input_val = repr(text)
+        input_val = str(text)
         d = Decimal(input_val)
     except InvalidOperation:
         try:
             d = Decimal(str(float(text)))
```

The value reconstruction has two control-flow branches that the change rewires:
the primary branch (`input_val = <conv>(text); d = Decimal(input_val)`) and the
fallback branch (`d = Decimal(str(float(text)))`, reached when `Decimal` raises
`InvalidOperation`). The change swaps the primary conversion from `repr` to
`str`. With `str`, the primary branch parses the canonical decimal string and
succeeds with full precision for the inputs the F2P test exercises; with `repr`,
the primary branch raises on `Decimal` inputs and the value falls into the lossy
binary fallback.

| # | model.py impl op (`reconstruct_digits`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text: List[int]` (the exact significant digit sequence) | the `text` argument of `floatformat`, viewed as the value's `Decimal.as_tuple().digits` | R | `Decimal`/numeric value ↔ `List[int]` of significant decimal digits (mapping.md §2). |
| A2 | the result is `ToSeq(text)`, i.e. the input digit sequence reproduced exactly (the verified backward identity copy) | `input_val = str(text); d = Decimal(input_val)` (the fixed primary branch) | A-reference | the changed reconstruction is modeled **deeply**: `reconstruct_digits` returns the input digit sequence unchanged, encoding that `Decimal(str(value))` preserves every significant digit. There is no consumed reconstruction axiom; the deep model (the identity) is validated **== the real callee** out-of-band by G-AX (`Decimal(str(value)) == value`, equal digit tuples; axiom_check.py A-reference 1, mapping.md §3.1). |
| A3 | (no node in the verified impl; the lossy alternative is the `narrowed_to_significand` pure model) | the unchanged fallback `d = Decimal(str(float(text)))` and the pre-patch primary `repr` path that routes into it | A-reference | the lossy binary reconstruction is modeled deeply by `narrowed_to_significand` (retain ≤ `significand_budget()` significant digits). The fix's primary branch no longer routes long-precision Decimals here; the prepatch does. G-AX validates `narrowed_to_significand` against the real `Decimal(str(float(value)))` (same float image; long-input divergence; axiom_check.py A-reference 2, mapping.md §3.2). |

The discriminating content of the change — full precision retained vs. collapse
through a binary significand — lives in the postcondition
`ToSeq(Result()) == ToSeq(text)` (model) ⇔ the `str(text)` primary conversion
(real). The pre-patch primary conversion was `repr(text)`, which sends
long-precision Decimal inputs into the `float` fallback; `model_prepatch.py`
reproduces that by building `narrowed_to_significand(ToSeq(text))` and **fails**
the postcondition `ToSeq(Result()) == ToSeq(text)`, which is exactly the spec
sensing the change (G-DIFF). The failure occurs precisely for inputs longer than
`significand_budget()` significant digits — e.g. the F2P input
`Decimal("123456.123456789012345678901")` (27 digits).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the value reconstruction — is modeled **deeply** (the verified
identity copy in `reconstruct_digits`, with the lossy alternative spelled out in
`narrowed_to_significand`), not hidden behind an axiom about the function under
change. There is no consumed `@ContractOnly` axiom: the reconstruction's real
callees (`str`/`repr`/`float`/`Decimal`) appear only as **A-references** that
G-AX validates the deep models against. The downstream formatting of `d`
(`quantize`, `as_tuple`, `number_format`) is unchanged by the patch and
unobservable to the modeled delta, so it is not part of the skeleton.

## C. verify(model) ⇒ resolved

`reconstruct_digits` verifies only if its output equals the exact input digit
sequence (A2) — full precision preserved. By R (Decimal value ↔ List[int] of
significant digits) the verified reconstruction equals `Decimal(str(text))` on
the tested inputs; by G-AX the deep identity model equals the real
`Decimal(str(value))` reconstruction (A-reference 1) and `narrowed_to_significand`
faithfully abstracts the lossy `Decimal(str(float(value)))` path the fix avoids
(A-reference 2). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited callees — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom/deep-model soundness (G-AX) and refinement fidelity (this
document, G-EQ).
