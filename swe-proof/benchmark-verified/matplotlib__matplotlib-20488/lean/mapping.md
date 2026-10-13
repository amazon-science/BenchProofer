# mapping.md — matplotlib__matplotlib-20488

## Symbol binding (file:line @ base_commit b7ce415c15eb39b026a097a2865da73fbcf15c9c)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_boundedRange` / `problem_spec_boundedRange` | the lower/upper bound sanitisation applied to `vrange` just before the range is installed onto the norm and the data is normalised | `lib/matplotlib/image.py` `_AxesImageBase._make_image`, lines 532-541 @ base_commit |
| `bounds : ℚ × ℚ` | `s_vmin, s_vmax = vrange` (line 534) — the resampled value range | `image.py:534` |
| `logScale : Bool` | `isinstance(self.norm, mcolors.LogNorm)` (line 535) | `image.py:535` |
| `floor : ℚ` | `np.finfo(scaled_dtype).eps` (line 537) — the smallest representable positive epsilon for the working dtype | `image.py:537` |
| `result : ℚ × ℚ` | the `(s_vmin, s_vmax)` pair as installed via `cbook._setattr_cm(self.norm, vmin=s_vmin, vmax=s_vmax)` (lines 538-540) | `image.py:538-540` |

### What the patch changes (base_commit)

`_make_image` computes a resampled value range `vrange` and unpacks it into
`s_vmin, s_vmax`. When the norm is a `LogNorm`, a non-positive lower bound is
invalid (a logarithm of a non-positive number is undefined; downstream the norm
raises `ValueError: Invalid vmin or vmax`).

Pre-patch (lines 535-537):

```python
if isinstance(self.norm, mcolors.LogNorm):
    if s_vmin < 0:
        s_vmin = max(s_vmin, np.finfo(scaled_dtype).eps)
```

The guard is `s_vmin < 0` (strictly negative). An **exact-zero** lower bound
(`s_vmin == 0`) slips through untouched and is still handed to the `LogNorm`,
which then fails. (Also, `max(s_vmin, eps)` is redundant: when `s_vmin < 0` the
max is always `eps`.)

Post-patch (gold):

```python
if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0:
    # Don't give 0 or negative values to LogNorm
    s_vmin = np.finfo(scaled_dtype).eps
```

The guard becomes `s_vmin <= 0`, catching the exact-zero case as well, and the
lower bound is set directly to the positive epsilon floor. `s_vmax` is never
touched in either version.

### Lean modeling

- `bounds.1`/`bounds.2` are `s_vmin`/`s_vmax`; `result.1`/`result.2` are the
  sanitised pair.
- `logScale` models the `isinstance(self.norm, mcolors.LogNorm)` predicate.
- `floor` models `np.finfo(scaled_dtype).eps`, a fixed positive constant; the
  `0 < floor` precondition on `correct_boundedRange` records that it is a
  strictly-positive machine epsilon.
- The fix's behaviour — clamp the lower bound to `floor` exactly when a log
  scale is in use AND the lower bound is non-positive (`≤ 0`), passing it through
  otherwise, and always passing the upper bound through — is modeled DEEPLY and
  structurally in `problem_spec_boundedRange` (a direct conditional on the
  sign/zero ordering of `bounds.1` against `0`). SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed decision, so it is spelled out.
- The pre-patch impl (`Solution_prepatch.lean`) reproduces the buggy guard
  `s_vmin < 0` (and the redundant `max`): an exact-zero lower bound under a log
  scale is left as `0` instead of `floor`, which is exactly the bug.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `s_vmin, s_vmax` (floats) | `bounds : ℚ × ℚ` | exact rational ↔ float value; the fix depends only on the sign/zero ordering of `s_vmin` vs `0`, which `ℚ` captures exactly (kernel `Float` order is opaque to tactics — DECISIONS.md) |
| `isinstance(self.norm, mcolors.LogNorm)` | `logScale : Bool` | `true ↔ True` |
| `np.finfo(scaled_dtype).eps` | `floor : ℚ` | a fixed strictly-positive constant; `0 < floor` |
| installed `(vmin, vmax)` | `result : ℚ × ℚ` | `result.1 ↔ s_vmin`, `result.2 ↔ s_vmax` after sanitisation |

The range is modeled with exact rationals rather than `Float` because the fix is
an order-only (sign/zero) decision: whether `s_vmin ≤ 0`. Exact `ℚ` makes that
comparison decidable in the kernel; a real-valued epsilon is irrelevant beyond
being positive, so it is an abstract positive `floor`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behaviour the patch changes — the sign/zero
  guard and the clamp — is modeled deeply and structurally; nothing is
  axiomatized. The `axioms` region declares no `opaque` and no `axiom … _prop`,
  so **G-AX skips**.
- `floor` (= `np.finfo(scaled_dtype).eps`) is an unchanged library constant. It
  is modeled as an explicit positive input, not an axiomatized callee; the only
  property the proof needs is `0 < floor`, carried as a hypothesis.
- **Flag dependency:** the clamp applies only under `logScale = true` (the
  `LogNorm` branch). G-CONF fuzzes both `logScale` values so the non-log branch
  (lower bound always passed through) is exercised too.

## G-CONF fuzz seed

Pinned LCG seed: **20488** (see `conformance_check.py` `SEED`). Corpus:
randomised `(logScale, floor, (lo, hi))` tuples (≥1e5), with `floor` a random
positive rational and `lo`/`hi` random rationals spanning negative, zero, and
positive values; plus hand-picked edge cases pinning the discriminating clause:
`logScale=True` with `lo = 0` (the F2P scenario — must clamp to `floor`),
`logScale=True` with `lo < 0` (clamp), `logScale=True` with `lo > 0` (pass
through), and `logScale=False` with `lo ≤ 0` (pass through). The R/I shadow of
`implementation_boundedRange` is diffed against an in-process replica of the
POST-PATCH guard (`logScale and lo <= 0 → floor`).
