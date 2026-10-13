# mapping.md — matplotlib__matplotlib-24870

## Symbol binding (file:line @ base_commit 6091437)

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_chooseLevels` / `problem_spec_chooseLevels` / `correct_chooseLevels` | the level-`arg` selection block inside `_process_contour_level_args` (the value assigned to `levels_arg` before it is converted/stored) | `lib/matplotlib/contour.py:1120-1134` |

The gold patch edits exactly this selection block (and threads the data dtype to
the method); the same method is reused by the triangular-grid contour path
(`lib/matplotlib/tri/_tricontour.py:_contour_args`, line 77 @ base_commit),
which the patch updates identically. Both call sites share one selection logic,
so one modeled function covers both.

## The change (what the modeled function computes)

`_process_contour_level_args` decides `levels_arg`, then converts/stores it.
Only the *decision* changed. At base_commit:

```python
if self.levels is None:
    if len(args) == 0:
        levels_arg = 7            # hard-wired count
    else:
        levels_arg = args[0]
else:
    levels_arg = self.levels
```

The new behaviour (post-patch) adds a data-dtype-dependent branch when the user
supplied no explicit levels and no positional level argument: a boolean-valued
input selects an explicit single mid-level for line contours and an explicit
three-element set for filled contours; otherwise the hard-wired count is kept.

The downstream conversion (`isinstance(levels_arg, Integral)` → `_autolev` /
`np.asarray`, in-range filtering, the "≥2 levels"/"increasing" checks) is
UNCHANGED by the patch and is therefore outside the modeled function.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean | Python |
|---|---|
| `LevelsArg.count n` | an integral `levels_arg` (a count `n` of automatic levels, fed to `_autolev`) |
| `LevelsArg.explicit xs` | a non-integral `levels_arg` (an explicit sequence of level values); `xs : List Rat` ↔ a Python list of exact rationals |
| `userLevels : Option LevelsArg` | `self.levels` (`None` ↔ `none`; an explicit count/sequence ↔ `some …`) |
| `args : List LevelsArg` | the leftover positional level arguments; `args[0]` ↔ `args.head` |
| `zIsBool : Bool` | `np.issubdtype(z.dtype, bool)` |
| `filled : Bool` | `self.filled` (`contourf`/`tricontourf` ⇒ true, `contour`/`tricontour` ⇒ false) |
| `result : LevelsArg` | the value bound to `levels_arg` |

Exact level values are modeled with `Rat` (the values `0`, `1/2`, `1` are exact;
no real-valued arithmetic is involved in the selection — see DECISIONS.md on
keeping order/value-exact data off `Float`).

## Callee provenance + flag deps

- `_autolev` (count → automatic level array) and `np.asarray`/in-range filtering
  are UNCHANGED downstream callees, invoked only AFTER the modeled selection.
  They are NOT axiomatized (the selection is modeled deeply / value-exact). In
  `conformance_check.py` the count branch is reconciled against the **real**
  `_autolev` output (A-reference); the explicit branches are compared directly
  for inputs whose data range leaves the downstream conversion an identity.
- Flag dependency: the explicit-level branches fire only when `self.levels is
  None` AND there are no positional level args AND the data dtype is boolean;
  the line-vs-filled split is governed by `self.filled`. G-CONF fuzzes all of
  {bool, float} × {filled, line} × {no-arg, positional-arg, levels= kwarg}.

## G-CONF fuzz seed

`conf_seed = 20240630` (pinned in meta.json).
