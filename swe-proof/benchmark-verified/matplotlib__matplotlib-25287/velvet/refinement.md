# refinement.md — matplotlib__matplotlib-25287

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `xAxisOffsetColor` / `yAxisOffsetColor` `do` blocks and the deep
`offsetColor` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A** (axiomatized callee —
A-consumed / A-reference), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The horizontal-axis offset-text color — `XAxis._init` (`lib/matplotlib/axis.py:2252`)

Gold hunk:
```
+        if mpl.rcParams['xtick.labelcolor'] == 'inherit':
+            tick_color = mpl.rcParams['xtick.color']
+        else:
+            tick_color = mpl.rcParams['xtick.labelcolor']
+
         self.offsetText.set(
             ...
             fontsize=mpl.rcParams['xtick.labelsize'],
-            color=mpl.rcParams['xtick.color'],
+            color=tick_color
         )
```

| # | Solution.lean impl op (`xAxisOffsetColor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `tickColor : String` | `mpl.rcParams['xtick.color']` | R | a color-spec `str` ↔ `String` (mapping.md §2). |
| A2 | parameter `labelColor : String` | `mpl.rcParams['xtick.labelcolor']` | R | a color-spec `str` (or the sentinel `'inherit'`) ↔ `String` (mapping.md §2). |
| A3 | `if labelColor = "inherit" then tickColor else labelColor` (= `offsetColor tickColor labelColor`) | `tick_color = (xtick.color if xtick.labelcolor == 'inherit' else xtick.labelcolor)` | I | identical concrete decision: the sentinel test `== 'inherit'` ↔ `= "inherit"`, the two-way selection between the two settings ↔ the `if … else …`. Transliterated and differential-tested by G-CONF. |
| A4 | result `out : String` returned | `color=tick_color` handed to `self.offsetText.set(...)`, read back by `offsetText.get_color()` | R | the unchanged set/get-color continuation is identity on the chosen color spec for the string values the F2P test uses (mapping.md §2, §3); `test_xaxis_offsetText_color` compares `get_color()` to the spec string. |

Discriminating content of the change — when `xtick.labelcolor` is an explicit
color (not `'inherit'`), the offset text must take that label color, NOT the tick
color. `Solution_prepatch_1.lean` reproduces the pre-patch behavior
(`color=mpl.rcParams['xtick.color']`, i.e. always `tickColor`) and **fails**
`out = offsetColor tickColor labelColor` on the explicit-label clause (G-DIFF).

## B. The vertical-axis offset-text color — `YAxis._init` (`lib/matplotlib/axis.py:2516`)

Gold hunk: the identical decision on the `ytick.*` settings:
```
+        if mpl.rcParams['ytick.labelcolor'] == 'inherit':
+            tick_color = mpl.rcParams['ytick.color']
+        else:
+            tick_color = mpl.rcParams['ytick.labelcolor']
+
         self.offsetText.set(
             ...
             fontsize=mpl.rcParams['ytick.labelsize'],
-            color=mpl.rcParams['ytick.color'],
+            color=tick_color
         )
```

| # | Solution.lean impl op (`yAxisOffsetColor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `tickColor : String` | `mpl.rcParams['ytick.color']` | R | color-spec `str` ↔ `String` (mapping.md §2). |
| B2 | parameter `labelColor : String` | `mpl.rcParams['ytick.labelcolor']` | R | color-spec `str` / `'inherit'` ↔ `String` (mapping.md §2). |
| B3 | `if labelColor = "inherit" then tickColor else labelColor` (= `offsetColor tickColor labelColor`) | `tick_color = (ytick.color if ytick.labelcolor == 'inherit' else ytick.labelcolor)` | I | identical concrete decision (as A3, for the vertical axis). Transliterated and differential-tested by G-CONF. |
| B4 | result `out : String` returned | `color=tick_color` set on `self.offsetText`, read by `offsetText.get_color()` | R | unchanged set/get-color continuation, identity on the chosen spec (mapping.md §2, §3); `test_yaxis_offsetText_color` compares `get_color()`. |

`Solution_prepatch_2.lean` reproduces the pre-patch `color=mpl.rcParams['ytick.color']`
(always `tickColor`) and **fails** the explicit-label clause (G-DIFF). Two
independently-observable fixed behaviors ⇒ two failing prepatches, one per axis.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The operation that genuinely changed — the selection of
the offset-text color — is modeled **deeply** (the spelled-out `offsetColor`
decision, steps A3/B3, I-tagged), not hidden behind any axiom about the function
under change. There are **no consumed axioms and no A-reference**: the only
callees touched by the result (`Text.set(color=...)` / `Text.get_color()`) are an
UNCHANGED identity-on-content continuation that G-CONF exercises for real, so no
contract about them is assumed. `meta.json conf_skip=false` (the impl region is
pure R/I, not all-A-tagged); `axiom_check.py` is therefore absent (no axioms /
A-references to validate).

## D. verify(Solution) ⇒ resolved

`xAxisOffsetColor`/`yAxisOffsetColor` verify only if their output equals
`offsetColor tickColor labelColor` — i.e. the explicit label color when set and
the tick color only on the `'inherit'` sentinel (A3/B3). By R (`str ↔ String`,
the set/get-color identity) the verified decision equals the gold patch's
`color=tick_color` selection on the tested inputs; by G-CONF the I-transliteration
of `offsetColor` agrees with the real patched `XAxis._init`/`YAxis._init` +
`offsetText.get_color()` on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms to trust (no G-AX leg).
