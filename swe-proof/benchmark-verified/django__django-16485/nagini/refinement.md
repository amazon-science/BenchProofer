# refinement.md — django__django-16485

The operation-by-operation correspondence between `model.py`'s implementation
(the `format_value` impl region, with the deep `int_render` / `rendered` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model validated == the real callee by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `floatformat()` (`django/template/defaultfilters.py:171`)

Gold hunk:
```
-    if not m and p < 0:
+    if not m and p <= 0:
         return mark_safe(
             formats.number_format(
                 "%d" % (int(d)),
                 ...
```

`m = int(d) - d` (line 167), `p = int(arg)` (line 162), `d = Decimal(str(text))`
(line 155). The early return formats the bare integer; the fall-through path
formats with a fractional part.

| # | model.py impl op (`format_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `int_value: int` | `int(d)` (`int(Decimal(str(text)))`) | R | the integer part of the parsed value; `int` ↔ `int` (mapping.md §1,§2). |
| A2 | parameter `frac_zero: bool` | `not m`, `m = int(d) - d` | R | `frac_zero == (m == 0)`; both denote "the value is exactly integral" (mapping.md §2). |
| A3 | parameter `p: int` | `p = int(arg)` | I | the requested decimal places; identical integer. |
| A4 | branch guard `if frac_zero and p <= 0:` | `if not m and p <= 0:` | I | the SAME boolean guard after R-mapping `frac_zero ↔ not m`. The single changed token (`<` → `<=`) is reproduced identically; `model_prepatch.py` uses `p < 0` (the pre-image) and FAILS, so the spec senses the change (G-DIFF). |
| A5 | early-return value `int_render(int_value)` (the digit loop building the bare integer code-point list) | `mark_safe(formats.number_format("%d" % (int(d)), 0, ...))` | A-reference + R | the bare-integer rendering is modeled DEEPLY (`int_render` over `digits_acc`); there is no consumed axiom. The unchanged localisation callee `number_format` is the **A-reference**: digit-content preserving on `"%d" % int(d)` under `decimal_pos=0` / no grouping (mapping.md §3.1), so the modeled `int_render(int_value)` equals the end-to-end `floatformat` output the F2P observes. `mark_safe` is the identity on character content (mapping.md §2). G-AX validates `floatformat == int_render` end-to-end for integral values at `p <= 0`. |
| A6 | else-branch value `int_render(int_value) + PSeq(46) + zeros_seq(mag(p))` (digits, separator 46, fractional field) | `mark_safe(formats.number_format(number, abs(p), ...))` where `number` is the `Decimal.quantize`/`as_tuple` digit string with `'.'` inserted (lines 181-198) | A-reference + R | the UNCHANGED decimal path; modeled as a faithful skeleton whose load-bearing property is that the **core** string (the digit string the filter hands to the localisation callee, BEFORE `number_format` lays it out) CONTAINS the decimal separator (46). G-AX confirms the real decimal-path **core** is separator-bearing for every non-integral value or `p > 0`, and that the post-patch and pre-patch filters AGREE here (the fix is localised). The exact fractional digits ARE observed by P2P/F2P tests (e.g. `floatformat(0.000000000000000000015, 20) == "0.00000000000000000002"`; `7.7,3 → "7.700"`; `5555.555,2 → "5555.56"`), but every such input lies in the patch-UNCHANGED regime (pre == post); the else-branch is tagged A-reference and refines to the real unchanged decimal path, so the skeleton's all-zeros field is discarded under refinement and is **not** the resolving oracle. Its sole load-bearing role is **core-layer** separator-presence, which distinguishes it from the bare-integer regime (mapping.md §3.2). NB the separator-presence discriminator holds at the **core** layer only: end-to-end, `number_format` at `decimal_pos=0` may STRIP a trailing separator (`floatformat(-0.499, 0) == "0"` — a non-integral value at `p<=0` that rounds to an integer), so "separator present iff NOT (integral and p<=0)" is true of the core string but false of the end-to-end output. |

## B. The discriminating behaviour

The change moves the boundary case `frac_zero == True ∧ p == 0` from the
separator-bearing branch into the bare-integer branch. The frozen postcondition
`ToSeq(Result()) == rendered(int_value, frac_zero, p)` with
`rendered(int_value, True, p<=0) == int_render(int_value)` pins the bare-integer
outcome. The pre-patch skeleton (`p < 0`) routes `frac_zero=True, p=0` into the
else branch, producing `int_render(int_value) + PSeq(46) + zeros_seq(0)
== int_render(int_value) + PSeq(46)`, which is NOT equal to
`rendered(int_value, True, 0) == int_render(int_value)` — so `model_prepatch.py`
FAILS exactly on the `format_value` postcondition (G-DIFF). In the real filter
this same misrouting raises `ValueError: valid range for prec is [1, MAX_PREC]`
for `"0.00"` (`prec = abs(0) + units + 1 = 0` ⇒ `Context(prec=0)`), which is the
crash the issue reports; the F2P inputs `floatformat("0.00", 0)` and
`floatformat(Decimal("0.00"), 0)` are exactly the `int_value == 0` instance,
yielding `"0"`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The operation that genuinely changed —
the branch selection between the bare-integer rendering and the separator-bearing
rendering — is modeled **deeply** (the `rendered` branch over the spelled-out
digit folds `int_render` / `zeros_seq`, consumed in `format_value`), NOT hidden
behind an axiom about the function under change. There is **no consumed
`@ContractOnly` axiom** (the axioms region is empty). The only callee referenced
is the UNCHANGED localisation function `number_format`, which appears solely as
the **A-reference** that G-AX validates the deep model against (digit-content
preservation on the integer string); the proof does not consume any axiom about
it.

## D. verify(model) ⇒ resolved

`format_value` verifies only if its output equals `rendered(int_value,
frac_zero, p)` — in particular only if an integral value at `p <= 0` renders as
the bare integer `int_render(int_value)` with no separator (A5), and only if the
guard is `p <= 0` rather than `p < 0` (A4; the `p < 0` pre-image fails, G-DIFF).
By R (`int(d) ↔ int_value`, `not m ↔ frac_zero`, `int(arg) ↔ p`, `mark_safe`/
character-content identities) and by the A-reference (G-AX: `number_format`
preserves the integer digit content, so `floatformat == int_render` end-to-end
in the bare-integer regime; the decimal path is unchanged and agrees pre/post),
the verified `format_value` equals `mark_safe(number_format("%d" % int(d), 0,
...))` on the integral `p <= 0` inputs the fix targets. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited A-reference callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
