# refinement.md — matplotlib__matplotlib-25287

The operation-by-operation correspondence between `model.py`'s implementation
(the `offset_color_primary` / `offset_color_secondary` impl regions, plus the
pure `effective_color` / `sentinel_inherit`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — none
here), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (applies at `base_commit`; the real
correctness oracle, G-RESOLVE).

## A. Site 1 — `XAxis._init` (`lib/matplotlib/axis.py:2237`, body ~2252-2259)

Gold hunk:
```
+ if mpl.rcParams['xtick.labelcolor'] == 'inherit':
+     tick_color = mpl.rcParams['xtick.color']
+ else:
+     tick_color = mpl.rcParams['xtick.labelcolor']
  self.offsetText.set(
      ...
-     color=mpl.rcParams['xtick.color'],
+     color=tick_color
  )
```

Modeled by `offset_color_primary(base_color, label_color)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `base_color: List[int]` | `mpl.rcParams['xtick.color']` (a colour-name `str`) read at the site | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | param `label_color: List[int]` | `mpl.rcParams['xtick.labelcolor']` (a colour-name `str`) read at the site | R | same `str` ↔ `List[int]` refinement. |
| A3 | `if ToSeq(label_color) == sentinel_inherit()` | `if mpl.rcParams['xtick.labelcolor'] == 'inherit'` | I + R | identical equality test; the compared values are refined `str` → `List[int]`, with `'inherit'` ↔ `sentinel_inherit()` = `PSeq(105,110,104,101,114,105,116)` (mapping.md §2). |
| A4 | `tick_color = list(base_color)` (true branch) | `tick_color = mpl.rcParams['xtick.color']` | I + R | take the base colour; `list(...)` is the carrier-level copy of the same value (content-equal). |
| A5 | `tick_color = list(label_color)` (false branch) | `tick_color = mpl.rcParams['xtick.labelcolor']` | I + R | take the label colour; content-equal copy. |
| A6 | `return tick_color` | `self.offsetText.set(..., color=tick_color)` then `offsetText.get_color()` returns it | R | `Text.set(color=v)` stores `v` verbatim; `get_color()` returns it unchanged (mapping.md §2) — the function's returned value IS the colour the F2P test reads. |

## B. Site 2 — `YAxis._init` (`lib/matplotlib/axis.py:2496`, body ~2511-2519)

Gold hunk is structurally identical with `ytick.*` in place of `xtick.*`:
```
+ if mpl.rcParams['ytick.labelcolor'] == 'inherit':
+     tick_color = mpl.rcParams['ytick.color']
+ else:
+     tick_color = mpl.rcParams['ytick.labelcolor']
  self.offsetText.set( ... -color=mpl.rcParams['ytick.color'], +color=tick_color )
```

Modeled by `offset_color_secondary(base_color, label_color)`; the row-by-row
correspondence is identical to A1–A6 with `ytick.color`/`ytick.labelcolor`
substituted for `xtick.color`/`xtick.labelcolor`. The two sites are independent
(different rcParam pairs, different axis), hence two contracted functions and two
differential witnesses (model_prepatch.py / model_prepatch_2.py), matching the
two F2P tests `test_xaxis_offsetText_color` / `test_yaxis_offsetText_color`.

## C. No axioms; no kind-3 step

Every step is R or I. The one operation that genuinely *changed* — selecting the
offset-text colour from the explicit label colour (falling back to the base
colour only on the `inherit` sentinel) — is expressed **directly** as the
conditional `effective_color` consumed in both impls; nothing is hidden behind an
axiom and no library callee is abstracted, so there is no A-consumed or
A-reference row and no `axiom_check.py`. The `dict.__getitem__` on `rcParams`
and `Text.set`/`get_color` are pure value-identity passthroughs captured by the R
refinements in mapping.md §2 (not behaviour the proof depends on).

## D. The discriminating clause (G-DIFF)

The pre-patch code at both sites set the offset colour to the **base** colour
unconditionally, ignoring the label colour. `model_prepatch.py` (site 1) and
`model_prepatch_2.py` (site 2) reproduce that exactly (`tick_color = base_color`
regardless of `label_color`) and **fail** the postcondition
`ToSeq(Result()) == effective_color(ToSeq(base_color), ToSeq(label_color))`
(equivalently the clause `label_color != inherit ⇒ Result == label_color`),
which is precisely the behaviour the F2P tests observe (a non-`'inherit'` label
colour must reach the offset text). The spec senses the bug at each site
independently.

## E. verify(model) ⇒ resolved

`offset_color_primary` / `offset_color_secondary` verify only if their result
equals `effective_color(base, label)` — i.e. the label colour, except the base
colour when the label colour is `inherit`. By the R refinements (str ↔
List[int]; `Text.set`/`get_color` value identity; `rcParams` reads ↔ the two
inputs) and the identical control flow (I), a model satisfying this spec is the
gold patch up to type refinement. The gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this document, G-EQ); axiom soundness (G-AX)
is vacuous since there are no axioms.
