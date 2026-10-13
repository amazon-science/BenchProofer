# mapping.md — matplotlib__matplotlib-24870

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6091437be9776139d3672cde28a19cbe6c09dcd5`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance + the flag dependencies G-CONF/G-AX rely on.

Repo files under change: `lib/matplotlib/contour.py`,
`lib/matplotlib/tri/_tricontour.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `chooseLevelArg` | `ContourSet._process_contour_level_args` — `lib/matplotlib/contour.py:1119` (selection branch, body lines 1121-1130 post-patch) | the modeled changed function: selection of the level argument when no `levels` keyword was passed |
| `LevelArg` (`count`/`explicit`) | the local `levels_arg` of `_process_contour_level_args` (`contour.py:1124-1132`), an `int`-or-`list` before the `isinstance(levels_arg, Integral)` dispatch | the pre-dispatch level specification |
| `chooseLevelArg` input `boolField` | `np.issubdtype(z_dtype, bool)` — `contour.py:1125` post-patch; `z_dtype` is the new 2nd parameter | whether the field is boolean |
| `chooseLevelArg` input `filled` | `self.filled` — `contour.py:1127` | whether the plot fills between levels |
| `chooseLevelArg` input `levelsKwSet`/`levelsKw` | `self.levels is not None` / `self.levels` — `contour.py:1131-1132` | the explicit `levels` keyword branch |
| `chooseLevelArg` input `posGiven`/`posArg` | `bool(args)` / `args[0]` — `contour.py:1123-1124` post-patch (`if args:`) | the positional level argument branch |

There is **no axiomatized callee and no deep-model reference**: the modeled
function is a pure selection over flags/values that the surrounding routine has
already computed. The `np.issubdtype(z_dtype, bool)` and `self.filled` tests are
*inputs* to `chooseLevelArg`, not callees invoked inside it. So G-AX is vacuous
(no axiom or A-reference to validate) and the impl region is **all R/I**
(`conf_skip = false`; G-CONF produces a real verdict).

## 2. Supporting refactor that makes `boolField` observable (R)

The gold patch has coupled supporting hunks whose only purpose is to deliver an
**un-coerced** `z.dtype` to `_process_contour_level_args`, so that
`np.issubdtype(z_dtype, bool)` can ever be true:

- `contour.py:_contour_args` — `self._process_contour_level_args(args)` becomes
  `self._process_contour_level_args(args, z.dtype)` (passes the dtype); the
  `z = ma.asarray(args[0], dtype=np.float64)` / `_check_xyz` calls drop the
  `dtype=np.float64` coercion (`z = ma.asarray(z)`), so a boolean input keeps
  its boolean dtype instead of being silently upcast to `float64`.
- `tri/_tricontour.py:_contour_args` — same: `z = np.ma.asarray(args[0])`
  (no float64 coercion) and `self._process_contour_level_args(args, z.dtype)`.

These are **type-plumbing (R)**: they do not change the *selection logic*; they
make the `boolField` input to `chooseLevelArg` faithfully equal to "the field is
boolean". The binding of `chooseLevelArg`'s `boolField` parameter to the repo is
therefore **`np.issubdtype(z.dtype, bool)` with `z` the un-coerced masked array
the patched `_contour_args`/`_check_xyz`/tri `_contour_args` produce**. A patch
that implemented the selection branch but kept the `float64` coercion would make
`boolField` always false and is NOT a valid refinement of this spec (refinement.md
§B). `patch.diff` is the gold (both the selection and the dtype-plumbing), so the
twin is consistent; G-RESOLVE confirms it resolves.

## 3. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the local `levels_arg`, an `int` (e.g. `7`, or an integer `self.levels`/`args[0]`) | `LevelArg.count n` | Python `int v` ↔ `LevelArg.count v.toNat`; G-CONF compares as `('count', n)`. (All level counts in scope are non-negative; `7` and any plausible user count are `Nat`.) |
| the local `levels_arg`, a `list` of numbers (`[0, .5, 1]`, `[.5]`, an explicit list `self.levels`/`args[0]`) | `LevelArg.explicit ls` | Python `[x0, x1, …]` ↔ `LevelArg.explicit [q0, q1, …]` where each `qi : Rat` is the exact rational value of `xi`; G-CONF compares as `('explicit', [float qi])`. The modeled constants `0, .5, 1` are exact in both `Rat` and IEEE-754 `float`, so the round trip is lossless. |
| `np.issubdtype(z_dtype, bool)` | Lean `Bool` (`boolField`) | true ↔ `true` |
| `self.filled` | Lean `Bool` (`filled`) | true ↔ `true` |
| `self.levels is None` | Lean `Bool` (`levelsKwSet = ¬None`) | `self.levels is not None` ↔ `levelsKwSet = true` |
| `bool(args)` (`if args:`) | Lean `Bool` (`posGiven`) | non-empty `args` ↔ `posGiven = true`; `posArg ↔ args[0]` |

`Rat` (exact rationals) is the carrier for level positions, modeling order only —
matplotlib stores levels as `np.float64`, but the only level values the change
introduces (`0`, `.5`, `1`) are dyadic and exact, so `Rat` is faithful and gives
decidable equality (`LevelArg` derives `DecidableEq`).

## 4. Flag dependencies for G-CONF / G-AX

- `chooseLevelArg` is exercised over the full Boolean cube of
  `(levelsKwSet, posGiven, boolField, filled)` plus representative `levelsKw` /
  `posArg` values (integer → `count`, increasing float list → `explicit`).
- The G-CONF oracle calls the **real patched** `_process_contour_level_args`
  (in-container, after `patch.diff` is applied) on a lightweight fake `self`
  whose `_autolev(n)` records `n` (capturing the `count` selection) and whose
  `filled` / wide `zmin,zmax` let the unchanged downstream pass cleanly so the
  raw `levels_arg` selection is observable. This isolates the **changed
  selection branch** — the R/I content of the impl — from the unchanged
  downstream `isinstance`/`asarray`/level-filtering, exactly per §4.1.
- `z_dtype` is passed as a real numpy dtype: `np.dtype(bool)` (boolField=true) or
  `np.dtype(np.float64)` (boolField=false).

## 5. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24870`** so the
consumer-side verdict (§11.3) is reproducible. There is no axiom model to leave
unsubstituted (no A-tagged ops); the shadow is the full branch logic.
