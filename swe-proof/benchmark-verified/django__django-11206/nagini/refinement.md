# refinement.md — django__django-11206

The operation-by-operation correspondence between `model.py`'s implementation
(the `format_small` impl region together with the deep models `below_cutoff`,
`threshold_exp`, `pow10`, `zeros`, `zero_render`, `opt_seq` in the `pure`
region) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`), **A-reference**
(a deep model is validated == the real callee/arithmetic by axiom_check.py /
G-AX, NOT consumed), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The changed site — `format()` (`django/utils/numberformat.py:29`)

Gold hunk (inserted immediately after `if isinstance(number, Decimal):`):
```python
+        if decimal_pos is not None:
+            # If the provided number is too small to affect any of the visible
+            # decimal places, consider it equal to '0'.
+            cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))
+            if abs(number) < cutoff:
+                number = Decimal('0')
```
The new guard, when it fires, replaces `number` with `Decimal('0')`; the
existing tail of `format` then renders `Decimal('0')` at `decimal_pos`
fixed-point places. When the guard does NOT fire, `number` is unchanged and the
ordinary path (incl. the `abs(exponent)+len(digits) > 200` scientific-notation
branch) governs. `model.py`'s `format_small` is the skeleton of exactly this
guard plus the zero-render tail it enables: it returns the rendered code-point
list when the guard fires (`Result() is not None`) and the absent value `None`
when it does not (fall through).

| # | model.py impl op (`format_small`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameters `coeff, exponent` (`coeff >= 0`) | `number: Decimal`, accessed via `abs(number)` and its magnitude `coeff * 10**exponent` | R | a `Decimal` value is exactly `(-1)**sign * coeff * 10**exponent` (its `as_tuple()` digit-integer and scale); `abs(number)` drops the sign, leaving the non-negative magnitude `coeff * 10**exponent` with `coeff >= 0` (mapping.md §2). |
| 2 | `decimal_pos` (`int >= 0`) | `decimal_pos` (the guard runs only under `decimal_pos is not None`) | R | the modeled domain is exactly the patch's guarded domain `decimal_pos is not None`; Django's callers pass a non-negative count (mapping.md §2). |
| 3 | `p = decimal_pos; if p < 1: p = 1` (i.e. `threshold_exp`) | the `'1'.rjust(decimal_pos, '0')` quirk inside `Decimal('0.' + ...)`: width-0 (and width-1) `rjust` leaves `'1'` unpadded, so the threshold is `10**-1` for `decimal_pos` 0 and 1 | R | `Decimal('0.' + '1'.rjust(dp,'0'))` equals `10**-max(dp,1)`; `threshold_exp` is exactly `max(dp,1)` (mapping.md §3.1, validated by axiom_check.py at `decimal_pos=0`). |
| 4 | the decision `below_cutoff(coeff, exponent, decimal_pos)` = `coeff*10**(exponent+threshold_exp) < 1` (the deep model: `coeff==0`, or shifted scale `< 0` and `coeff < 10**(-shifted)`) | `abs(number) < cutoff` | A-reference | the changed smallness comparison is modeled **deeply** over exact integer arithmetic (cross-multiplying the positive `10**threshold_exp` away); there is no consumed axiom for it. G-AX (`axiom_check.py`) runs the REAL `abs(number) < Decimal('0.'+'1'.rjust(dp,'0'))` against `below_cutoff` over boundary + exact-threshold edge + 200k fuzz and asserts equality, incl. the STRICT edge `1e-8 == cutoff ⇒ not below` (mapping.md §3.1). |
| 5 | `if not is_small: return None` | the guard not firing: `number` unchanged ⇒ ordinary path (which this routine does not render; for a below-200-digit-budget value it is `{:f}` formatting, for an over-budget tiny value it WAS scientific notation — the very bug) | I + R | the absent value `None` is the "no collapse, fall through" outcome; the ordinary path is outside the modeled changed behaviour (it is unchanged by the patch). |
| 6 | when `is_small`: build `[48]` (`decimal_pos==0`) or `[48,46] + zeros(decimal_pos)` (`decimal_pos>=1`), i.e. `zero_render(decimal_pos)` | `number = Decimal('0')` followed by the existing tail rendering `Decimal('0')` at `decimal_pos`: `'0'`, or `'0' + decimal_sep + '0'*decimal_pos` | A-reference | the zero rendering is modeled **deeply** (`zero_render`, the spelled-out code-point sequence); G-AX asserts `zero_render(dp)` equals the REAL post-collapse rendering of `Decimal('0')` (reproduced verbatim from the `format` tail) over `decimal_pos` 0..32. Code points: `'0'`=48, `'.'`=46 (the F2P separator is `'.'`). |

## Why exactly one failing prepatch

The single independently-fixed behaviour is the smallness collapse. `model_prepatch.py`
keeps the spec byte-identical and reverts the impl to the pre-patch skeleton:
**no smallness guard at all** — every value falls through (`return None`),
mirroring the pre-patch `format` where a below-window magnitude was rendered in
exponential form rather than collapsed. It **fails** the postcondition
`Implies(below_cutoff(coeff, exponent, decimal_pos), Result() is not None)`
(verifier reports exactly this clause) — the spec sensing the change (G-DIFF).
This is the same delta the F2P test row flips from `'1.234e-300'` to `'0.000'`.

## No consumed axiom; no kind-3 step

Every step above is R, I, or **A-reference**. The two operations that genuinely
*changed* — the smallness comparison and the resulting zero rendering — are
modeled **deeply** (`below_cutoff` / `zero_render`, steps 4 and 6) and validated
== the real arithmetic by G-AX, not hidden behind a consumed `@ContractOnly`
axiom about the function under change. There is **no A-consumed axiom** in this
bundle (the `axioms` region is empty). The `Decimal` decomposition, `abs`, and
the fixed-point zero-rendering are the type-refinement boundary (R / A-reference,
mapping.md §2–§3), not consumed axioms. There is no kind-3 (changed-op-Nagini-
cannot-express) step.

## verify(model) ⇒ resolved

`format_small` verifies only if (4) it produces a rendering exactly when
`coeff*10**(exponent+threshold_exp) < 1` — i.e. exactly when the value is
strictly below the visibility threshold, with the strict edge pinned — and only
if (6) that rendering is exactly the padded plain zero. By R (Decimal magnitude
↔ `(coeff, exponent)`, `abs`, the `rjust` threshold quirk) and by G-AX
(A-reference: `below_cutoff` == the real `abs(number) < cutoff`; `zero_render`
== the real `Decimal('0')` rendering), the verified routine equals the gold
patch's guard-and-collapse on the tested inputs. The gold patch resolves
(G-RESOLVE). The single trust point of PLAN §1.1 that applies here is
refinement fidelity (this document, G-EQ) together with the A-reference
arithmetic soundness (G-AX); there is no consumed-axiom trust point.
