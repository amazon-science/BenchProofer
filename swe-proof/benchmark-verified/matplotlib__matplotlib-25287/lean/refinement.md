# refinement.md — matplotlib__matplotlib-25287

Maps every operation in the two implementations to its `patch.diff` counterpart.
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch decision, both axes — identical shape)
```python
if mpl.rcParams['xtick.labelcolor'] == 'inherit':
    tick_color = mpl.rcParams['xtick.color']
else:
    tick_color = mpl.rcParams['xtick.labelcolor']
...
self.offsetText.set(..., color=tick_color)
```
(`YAxis._init` is the byte-symmetric `ytick.*` version.) The modeled value is the
`color=` argument finally passed to `self.offsetText.set(...)`.

## Operation correspondence — `implementation_horizOffsetTextColor`
| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut chosen := tickColor` | the pre-patch default was `color=rcParams['xtick.color']`; the new code seeds `tick_color` from the tick color in the `'inherit'` branch | I | accumulator starts at the tick-mark color (the fallback). |
| 2 | `match labelColor with` | `if rcParams['xtick.labelcolor'] == 'inherit' … else …` | R | the `'inherit'` string sentinel ↔ `none`; any explicit color value `v` ↔ `some v` (mapping.md type bijection). The Python equality test against `'inherit'` ↔ the Lean `Option` case split. |
| 3 | `| none => chosen := tickColor` | `tick_color = mpl.rcParams['xtick.color']` (the `== 'inherit'` true branch) | R/I | defer-to-ticks: keep the tick-mark color. |
| 4 | `| some c => chosen := c` | `tick_color = mpl.rcParams['xtick.labelcolor']` (the else branch) | R/I | adopt the explicit label color. |
| 5 | `return chosen` | `color=tick_color` passed to `self.offsetText.set(...)` | I | the resolved offset-text color. |

## Operation correspondence — `implementation_vertOffsetTextColor`
Byte-symmetric to the horizontal case, against `YAxis._init` with the `ytick.*`
rcParams. Same tags row-for-row.

Every op is R or I; **no A row** — no axiom consumed and no A-reference (the two
rcParams enter as plain data per mapping.md; the choice is modeled deeply as an
`Option.getD`). Therefore `meta.json axioms = []`, `deep_model_references = []`,
and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow (`Option.getD` transliteration) against `patch.diff` behavior
(`rc[color] if rc[labelcolor]=='inherit' else rc[labelcolor]`) over ≥10^5 fuzzed
inputs, covering both axes. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, both `_init`s pass `color=mpl.rcParams['*tick.color']` unconditionally
— the offset text is always colored from the tick-mark color, ignoring the
label-color setting. The prepatch impls (`implementation_*OffsetTextColor :=
return tickColor`, unconditionally) are exactly this: they never consult
`labelColor`. They cannot satisfy `problem_spec_*OffsetTextColor` on the
discriminating clause `labelColor = some c ⇒ result = c` whenever
`c ≠ tickColor` — precisely the case the FAIL_TO_PASS tests
`test_xaxis_offsetText_color` / `test_yaxis_offsetText_color` exercise (set
`*tick.labelcolor` to an explicit color and assert `offsetText.get_color()`
equals it, distinct from `*tick.color`). The carried gold proof fails to
typecheck against the buggy impl (G-DIFF) — verified: `rfl` fails on the
`some c` case for both `Solution_prepatch.lean` (horiz buggy) and
`Solution_prepatch_2.lean` (vert buggy).
