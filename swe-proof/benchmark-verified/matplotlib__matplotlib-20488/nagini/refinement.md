# refinement.md — matplotlib__matplotlib-20488

Operation-by-operation correspondence between `model.py`'s impl region and
`patch.diff` (the gold hunk). Every step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's Ensures), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete operation).
There are no axiomatized callees in this bundle, so no A-consumed / A-reference
rows.

## The patched hunk (gold)

```python
# base_commit (buggy):
s_vmin, s_vmax = vrange
if isinstance(self.norm, mcolors.LogNorm):
    if s_vmin < 0:
        s_vmin = max(s_vmin, np.finfo(scaled_dtype).eps)

# patched (fixed):
s_vmin, s_vmax = vrange
if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0:
    # Don't give 0 or negative values to LogNorm
    s_vmin = np.finfo(scaled_dtype).eps
```

## model.py impl (fixed skeleton)

```python
result = s_vmin
if is_log and s_vmin <= 0.0:
    result = eps
else:
    Assert(Implies(is_log, s_vmin > 0.0))   # proof annotation only
return result
```

## Correspondence table

| # | model.py op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `result = s_vmin` (carry the candidate bound) | `s_vmin` after `s_vmin, s_vmax = vrange` (the working value, untouched unless the guard fires) | R | `s_vmin: float` ↔ the numpy-float scalar unpacked from `vrange`. Same value, refined carrier (interpreted real ↔ numpy float). |
| 2 | `is_log` (the test in the `if`) | `isinstance(self.norm, mcolors.LogNorm)` | R / I | the boolean condition is identical; its operand `self.norm` is abstracted to the single bit the hunk consults (is it a logarithmic norm). The `isinstance` call is unchanged across the patch, so this is a faithful identity refinement of a bool-valued condition. |
| 3 | `s_vmin <= 0.0` (the second conjunct of the guard) | `s_vmin <= 0` | I | the SAME comparison the fix introduces. This is the corrected boundary (`<= 0`, catching the exact-zero case that `< 0` missed). Identical concrete operation under the float refinement of `s_vmin`. |
| 4 | `result = eps` (the sanitised value when the guard fires) | `s_vmin = np.finfo(scaled_dtype).eps` | R | `eps: float` ↔ `np.finfo(scaled_dtype).eps`. Same assignment; the floor constant is refined to a parameter carrying its sole relevant property (`eps > 0.0`). |
| 5 | `else: Assert(...)`; `return result` | falls through to `with cbook._setattr_cm(self.norm, vmin=s_vmin, ...)` | I | control-flow exit carrying the (possibly sanitised) lower bound onward. The `Assert` is a proof annotation, not a runtime op; it has no patch counterpart and is permitted (it does not alter the modeled behavior). |

## Why no kind-3 step

Every operation is R or I. There is no *changed operation Nagini cannot
express*: the change is a boundary-comparison + assignment over real numbers,
modeled directly with `--float-encoding=real`. No callee changes; nothing is
axiomatized.

## Behavioral-delta faithfulness (verify ⟹ correct)

The patch changes behavior ONLY in the logarithmic branch:

- `is_log = True, s_vmin == 0.0`: pre-patch `s_vmin < 0` is False → `s_vmin`
  stays `0.0` → fed to LogNorm → `ValueError: Invalid vmin or vmax` (the F2P
  failure). Post-patch `s_vmin <= 0` is True → `s_vmin = eps > 0`. The spec
  clause `Implies(is_log, Result() > 0.0)` and `Implies(is_log and s_vmin<=0,
  Result()==eps)` pin exactly this; `model_prepatch.py` fails on the former.
- `is_log = True, s_vmin < 0.0`: both pre- and post-patch yield `eps`
  (`max(neg, eps) == eps`); behavior identical. Spec agrees (both give `eps`).
- `is_log = True, s_vmin > 0.0` and any non-log case: pass-through unchanged on
  both sides. Spec clause `Implies(not(is_log and s_vmin<=0), Result()==s_vmin)`
  pins this.

So the spec is the exact behavioral image of the fix, and the prepatch (the
real bug) fails the discriminating postcondition — `verify ⟹ resolved`.
