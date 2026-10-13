# refinement.md — mwaskom__seaborn-3069

Maps every operation in `implementation_nominalAxis` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `nominalAxis` (the per-axis finalization decision in `Plotter._finalize_figure`)

Post-patch repo code (`patch.diff`), per axis inside the `for axis in "xy"` loop:
```python
axis_obj = getattr(ax, f"{axis}axis")
...
# Nominal scale special-casing
if isinstance(self._scales.get(axis_key), Nominal):
    axis_obj.grid(False, which="both")
    if axis_key not in p._limits:
        nticks = len(axis_obj.get_major_ticks())
        lo, hi = -.5, nticks - .5
        if axis == "y":
            lo, hi = hi, lo
        set_lim = getattr(ax, f"set_{axis}lim")
        set_lim(lo, hi, auto=None)
```

Lean impl (`implementation_nominalAxis`): an `Id.run do` skeleton with the same
nested-branch control flow — outer `if isNominal` forces the grid off and, when
`!hasLimit`, computes `lo, hi = -1/2, nticks - 1/2`, swapping them on the `y`
axis, and records the pinned extent.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `isY : Bool` argument | `axis == "y"` | **R** | `"x"`/`"y"` loop variable reduced to the only behaviorally-relevant bit (which axis). mapping.md bijection. |
| 2 | `isNominal : Bool` argument | `isinstance(self._scales.get(axis_key), Nominal)` | **R** | Python `bool` ↔ Lean `Bool`. The scale-lookup + isinstance test is upstream input; only its truth value reaches the modeled decision. |
| 3 | `hasLimit : Bool` argument | `axis_key in p._limits` | **R** | Python `bool` ↔ Lean `Bool`; dict-membership truth value. |
| 4 | `nticks : Nat` argument | `len(axis_obj.get_major_ticks())` | **R** | Python `int ≥ 0` (a length) ↔ Lean `Nat`. The tick count is an upstream observation. |
| 5 | `let mut gridHidden := false; let mut fixedLimit := none` | the implicit "no special-casing" default before the new block | **I** | initial state: grid not forced off, extent not pinned (matches the non-nominal path and base_commit). |
| 6 | `if isNominal then gridHidden := true` | `if isinstance(...Nominal): axis_obj.grid(False, which="both")` | **I** (the changed op, deeply modeled) | **the fixed operation (grid).** The patch unconditionally hides the grid for a nominal axis; modeled directly as setting `gridHidden := true`. The prepatch impl omits this (grid left to style), matching base_commit. |
| 7 | `if !hasLimit then …` (nested) | `if axis_key not in p._limits:` | **I** | the extent pin is applied only when no explicit limit is set; identical guard. |
| 8 | `let lo : ℚ := -1/2; let hi : ℚ := (nticks:ℚ) - 1/2` | `lo, hi = -.5, nticks - .5` | **R** | exact half-integer floats ↔ exact `ℚ` (mapping.md: order/value-exact, never kernel `Float`). `-0.5` and `n - 0.5` are exactly representable; the refinement is the identity on these exact values. |
| 9 | `if isY then fixedLimit := some (hi, lo) else fixedLimit := some (lo, hi)` | `if axis == "y": lo, hi = hi, lo` then `set_{axis}lim(lo, hi, auto=None)` | **I** (the changed op, deeply modeled) | **the fixed operation (extent).** The y-axis swap reverses the extent; modeled directly as the pair swap inside `some`. The call `set_{axis}lim(...)` is the act of pinning the extent → `some (...)`; no call → `none`. |
| 10 | `return ⟨gridHidden, fixedLimit⟩` | the two side effects (`grid(...)`, `set_{axis}lim(...)`) on `ax`/`axis_obj` | **R** | the two mutations on the axis object are modeled as the returned `AxisLayout` record carrying the two decisions (mapping.md). The surrounding loop, the unchanged explicit-limit block, and the layout-engine code are not part of the modeled decision and are unchanged by the patch. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch per-axis finalization decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_nominalAxis` pins BOTH output components in every input case
  (directive 5 — frame): `gridHidden` is pinned to `isNominal` for all inputs;
  `fixedLimit` is pinned to the exact categorical extent when nominal-and-no-limit
  (with the `y` reversal), and pinned to `none` whenever the axis is non-nominal
  OR an explicit limit is present. No output component is left unconstrained.
- Directive 8 (grounded): the pinned extent is `(-1/2, nticks - 1/2)` — a closed
  arithmetic expression in the input `nticks`, not an ungrounded oracle; a wrong
  impl cannot echo an answer-key, it must compute the half-integer extent.
- Discriminating clauses: the prepatch impl leaves `gridHidden := false` and
  `fixedLimit := none` for ALL inputs (base_commit: no special-casing). Against a
  nominal axis the carried gold proof must show `false = true` (first conjunct,
  grid) and — when no limit — `none = some (...)` (second conjunct, extent),
  neither definitionally true, so `Solution_prepatch.lean` fails G-VERIFY
  (G-DIFF / G-PANEL). On a non-nominal axis prepatch and patched agree.
- This is exactly what the two FAIL_TO_PASS tests exercise:
  - `test_nominal_x_axis_tweaks`: `x` is categorical (`isNominal=true`, `isY=false`),
    no limit → extent `(-0.5, 2.5)` for 3 categories and gridlines invisible;
    with `.limit(x=(-1, 2.1))` (`hasLimit=true`) the extent is the user limit and
    the special-cased extent is NOT applied.
  - `test_nominal_y_axis_tweaks`: `y` categorical (`isY=true`) → reversed extent
    `(2.5, -0.5)` and gridlines invisible.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  per-axis decision over the boundary cross-product (the 8 boolean combinations ×
  boundary `nticks`, including the discriminating nominal cases on both axes) plus
  ≥1e5 fuzzed tuples (0 disagreements).
