# mapping.md — matplotlib__matplotlib-25287

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f8ffce6d44127d4ea7d6491262ab30046b03294b`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance and flag dependencies.

Repo file under change: `lib/matplotlib/axis.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `xAxisOffsetColor (tickColor labelColor : String)` | the offset-text color computation in the horizontal axis initializer `XAxis._init` — `lib/matplotlib/axis.py:2252-2262` (the `self.offsetText.set(..., color=...)` call's `color` argument) | modeled changed function (horizontal-axis exponent/offset text color) |
| `yAxisOffsetColor (tickColor labelColor : String)` | the offset-text color computation in the vertical axis initializer `YAxis._init` — `lib/matplotlib/axis.py:2516-2526` (the `self.offsetText.set(..., color=...)` call's `color` argument) | modeled changed function (vertical-axis exponent/offset text color) |
| `offsetColor (tickColor labelColor : String)` | the chosen `color` value the patched `color=tick_color` selection computes (`if labelcolor == 'inherit': tick_color = color-setting else labelcolor-setting`) | pure spec: the selected color, deeply modeled |

The two repo `_init` methods are independent: each reads its own axis's two
settings (`xtick.color`/`xtick.labelcolor` for the horizontal axis;
`ytick.color`/`ytick.labelcolor` for the vertical axis) and paints its own
`offsetText`. The fix is the identical decision applied at both sites; the F2P
tests (`test_xaxis_offsetText_color`, `test_yaxis_offsetText_color`) observe the
two sites independently, so each is a separately-fixed behavior with its own
failing prepatch.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a matplotlib color setting (`rcParams['xtick.color']`, `rcParams['xtick.labelcolor']`, and the analogous `ytick.*`) — a color spec string (named color, hex string, or the literal sentinel `'inherit'` for the labelcolor) | `String` | the rcParam value (a `str` color spec) ↔ the Lean `String` of the same characters; the sentinel `'inherit'` ↔ the Lean string literal `"inherit"`; equality of color specs ↔ Lean `String` `=` |
| the `color=` value handed to `self.offsetText.set(...)`, later read back by `offsetText.get_color()` | `String` (the method result `out`) | the chosen color spec string ↔ the returned `String`; `Text.get_color()` returns exactly the spec that was set, with no normalization for the string values the F2P tests use ('blue','yellow','green','red'), so the comparison is character equality |

`labelColor` carries the tick-label color setting whose distinguished value is
the sentinel `'inherit'`; `tickColor` carries the tick color setting. Both are
read-only configuration strings — neither method mutates either (directive 5);
the methods take no `mut` parameter and `ensures` pins `out` purely as a function
of the two inputs.

## 3. Callee provenance

There are **no axiomatized callees and no deep-model references**. The modeled
operation is a closed pure decision over two input strings — the equality test
`labelColor == 'inherit'` and the selection between the two inputs — entirely
expressible in Lean. The downstream `self.offsetText.set(color=...)` /
`Text.get_color()` machinery that stores and returns the chosen color is an
UNCHANGED continuation reached identically whichever color is selected; the patch
does not touch it, and the F2P tests observe it only as the identity readback of
the color that was set. It is therefore neither consumed as an axiom nor
deep-modeled; the G-CONF oracle exercises the real (patched) `_init` +
`get_color()` end-to-end, so its fidelity is mechanically checked, not assumed.

### 3.1 Flag / configuration dependency

The selection is governed by the per-axis tick-label color setting:
`rcParams['xtick.labelcolor']` for `xAxisOffsetColor`,
`rcParams['ytick.labelcolor']` for `yAxisOffsetColor`. The sentinel that triggers
the fall-back to the tick color is the exact string `'inherit'` — matplotlib's
documented default for `*tick.labelcolor`. G-CONF fuzzes both the `'inherit'`
sentinel and a range of explicit color strings, against both the matching and a
mismatched tick color, for both axes.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`25287`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `offsetColor` to Python and bridges I/O via §2; there are no
A-tagged ops, so the oracle is the real patched `XAxis._init`/`YAxis._init` plus
`offsetText.get_color()`.
