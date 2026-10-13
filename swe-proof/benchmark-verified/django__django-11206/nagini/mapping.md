# mapping.md — django__django-11206

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 571ab44e8a8936014c22e7eebe4948d9611fd7ce`, states the type
abstraction, and gives the provenance of each deep-model reference (the real
arithmetic the deep model is validated against, plus the exact behaviour
encoded).

Repo file under change: `django/utils/numberformat.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `format_small(coeff, exponent, decimal_pos)` | `format(number, decimal_sep, decimal_pos=None, …)` — `django/utils/numberformat.py:7`; the changed guard is inserted after `if isinstance(number, Decimal):` (`numberformat.py:29`) and its collapse feeds the existing render tail (`numberformat.py:43,52,56,58,79`) | the modeled changed behaviour: the small-magnitude → padded-zero collapse the patch adds, plus the zero rendering it enables |
| `below_cutoff(coeff, exponent, decimal_pos)` *(deep model — A-reference)* | `abs(number) < cutoff` where `cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))` (added at `numberformat.py:30-35` post-patch) | pure spec: the smallness decision, modeled deeply over exact integer arithmetic; validated `below_cutoff == abs(number) < cutoff` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `threshold_exp(decimal_pos)` | the `'1'.rjust(decimal_pos, '0')` width quirk inside `Decimal('0.' + …)` | pure spec: the threshold exponent `max(decimal_pos, 1)` |
| `pow10(n)` | the power-of-ten scaling implicit in `Decimal` magnitude and in `cutoff = 10**-p` | pure spec: `10**n`, `n >= 0` |
| `zero_render(decimal_pos)` *(deep model — A-reference)* | the existing render tail applied to `number = Decimal('0')`: `'{:f}'.format(Decimal('0'))` → `'0'`, then `dec_part` padding and the separator join (`numberformat.py:43,52,56-58`) | pure spec: the padded plain-zero string; validated `zero_render == real Decimal('0') rendering` by axiom_check.py (G-AX) |
| `zeros(n)` | the `'0' * (decimal_pos - len(dec_part))` padding for `Decimal('0')` (`numberformat.py:57`) | pure spec: a run of `n` `'0'` digits |
| `opt_seq(x)` | (helper only) | guards the `Optional` result so the spec compares a produced rendering without indexing through `None` |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): with no smallness guard, a Decimal
whose `abs(exponent) + len(digits) > 200` (`numberformat.py:33`) was rendered in
scientific notation (`'{:e}'.format(number)`, `numberformat.py:34`) even when
`decimal_pos` made it indistinguishable from zero.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `number: Decimal` | non-negative magnitude `coeff * 10**exponent` with `coeff >= 0`, plus the sign discarded by `abs` | `Decimal` value `= (-1)**sign · coeff · 10**exponent` exactly, where `(sign, digits, exponent) = number.as_tuple()` and `coeff` is the integer of `digits`; `abs(number)` ↔ the `coeff >= 0` magnitude (the patch compares `abs(number)`, so the sign is irrelevant). |
| `abs(number)` | drop of the sign; magnitude `coeff * 10**exponent` | exact: `abs` negates `sign` to 0; the digit-integer `coeff` and `exponent` are unchanged. |
| `decimal_pos` (an `int`, guard runs only when `is not None`) | `int >= 0` | the modeled domain is exactly `decimal_pos is not None`; Django passes a non-negative count of fractional places. |
| `Decimal('0.' + '1'.rjust(decimal_pos, '0'))` (the cutoff) | `10 ** -threshold_exp(decimal_pos)` = `10 ** -max(decimal_pos, 1)` | `'1'.rjust(w,'0')` left-pads `'1'` with `'0'` to width `w`, but for `w in {0,1}` leaves `'1'` unpadded, so `'0.'+…` is `'0.1' = 10**-1`; for `w >= 2` it is `10**-w`. Hence the cutoff is `10**-max(decimal_pos,1)` (verified in axiom_check.py at `decimal_pos=0`). |
| comparison `abs(number) < cutoff` (Decimal `<`) | `coeff * 10**(exponent+threshold_exp) < 1` (integer) | multiply both sides of `coeff·10**exponent < 10**-p` by the positive `10**p`; STRICT `<` preserved. The edge `abs(number) == cutoff` is NOT below. |
| rendered string (`str`) | `List[int]` / `PSeq[int]` of code points | `'0'` ↔ 48, `'.'` ↔ 46 (the F2P `decimal_sep` is `'.'`); `str` concatenation ↔ list `+`. |

`str` indexing/iteration is banned in Nagini, so the rendered output is carried
as `List[int]` of code points; the specification is phrased over `PSeq[int]` via
`ToSeq` / `opt_seq`.

## 3. Deep-model references (kind-A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom** in this bundle: the two operations
the patch changes are modeled deeply and validated against the real arithmetic.

### 3.1 `below_cutoff` deep model ↔ real `abs(number) < cutoff` (A-reference)
**Refined operation:** the gold guard
`cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0')); abs(number) < cutoff`
(`django/utils/numberformat.py:30-35` post-patch). The smallness comparison is
modeled deeply by `below_cutoff` (with `threshold_exp`, `pow10`) over exact
integer arithmetic; there is **no `is_small` axiom** the proof consumes. The
deep model is instead validated equal to the real callee out-of-band by
axiom_check.py (G-AX), which reproduces the cutoff expression **verbatim**:

```python
cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))
real   = abs(number) < cutoff
```

Equivalence argument: a `Decimal`'s magnitude is exactly `coeff · 10**exponent`
(`coeff >= 0`), and `cutoff == 10**-max(decimal_pos,1)`. Multiplying the strict
inequality `coeff·10**exponent < 10**-p` (with `p = max(decimal_pos,1)`) by the
positive `10**p` gives `coeff·10**(exponent+p) < 1`, which (for `coeff >= 0`) is
`coeff == 0`, or `exponent+p < 0` and `coeff < 10**-(exponent+p)` — exactly
`below_cutoff`. The STRICT `<` (so `abs(number) == cutoff` is NOT collapsed, the
`1e-8`/`decimal_pos=8` edge) is preserved.

**Soundness check (G-AX):** axiom_check.py asserts `below_cutoff == real` on the
problem-statement witnesses (`1e-199` below / `1e-200` … note the bug rendered
the over-budget `1e-200` as `1.00e-200`), every F2P/P2P magnitude, the exact-
threshold edge for `decimal_pos` 0..29 (cutoff itself, ten-times, one-tenth,
negative, zero), and 200000 randomized fuzz numbers straddling the cutoff. It
imports only the standard-library `decimal` module. Pinned to the `'.'` decimal
separator and `decimal_pos is not None` (Django's guarded call).

### 3.2 `zero_render` deep model ↔ real `Decimal('0')` rendering (A-reference)
**Refined operation:** once the guard fires, `number = Decimal('0')` and the
existing tail renders it: `'{:f}'.format(Decimal('0')) == '0'`, no `'.'`, so
`int_part = '0'`, `dec_part = ''`, then `dec_part += '0'*decimal_pos`, and
`dec_part = dec_part and decimal_sep + dec_part` (`numberformat.py:43,52,56-58`).
The rendering is modeled deeply by `zero_render`:
`'0'` for `decimal_pos == 0`, else `'0.' + '0'*decimal_pos`.

**Soundness check (G-AX):** axiom_check.py reproduces the render tail verbatim
on `Decimal('0')` and asserts `zero_render(dp)` equals it for `decimal_pos`
0..32, with the `'.'` separator. (F2P witnesses: `decimal_pos=3 → '0.000'`,
`decimal_pos=2 → '0.00'`, `decimal_pos=8 → '0.00000000'`, `decimal_pos=0 → '0'`.)
