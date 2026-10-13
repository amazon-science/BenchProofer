# mapping.md — matplotlib__matplotlib-24026

Binds every model.py symbol to the real repo symbol it abstracts, at
`base_commit` 14c96b510ebeba40f573e512299b1976f35b620e.

## 1. The changed function

| model.py symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `assign_layer_facecolors` | `matplotlib.stackplot.stackplot` (the per-layer facecolor assignment + the property-cycle side effect) | `lib/matplotlib/stackplot.py:16` (def), color logic at `:71-73` and `:110-123` |
| `Axes` (model class) field `cycle` | the Axes' line-property cycle state, read/advanced through `axes._get_lines` (a `_process_plot_var_args`) and mutated by `axes.set_prop_cycle(...)` | `lib/matplotlib/axes/_base.py:210` (`_process_plot_var_args`), `:314` (`get_next_color`), `:1550` (`Axes.set_prop_cycle`) |

The function draws one facecolor per stacked layer. With `args = (y1, ..., yM)`
the layer count is `M = len(y)` where `y = np.row_stack(args)`. Each layer `i`
(`0 <= i < M`) is drawn by `axes.fill_between(..., facecolor=<color i>, ...)`
at `:112` (layer 0) and `:121` (layers 1..M-1).

## 2. Type abstraction

| repo reality | model.py |
|---|---|
| `colors` (a sequence of color specs / `CN` aliases / RGBA tuples) | `List[int]` of opaque color tokens; only identity/order/length matter, never the spec syntax. The `CN`-alias case that the pre-patch rejects is one inhabitant — the model abstracts over the token values. |
| the per-layer facecolor list passed to successive `fill_between` calls | `List[int]` returned by `assign_layer_facecolors`, element `i` = the facecolor of layer `i` |
| the Axes line-property-cycle STATE (what `set_prop_cycle`/`get_next_color` read and write) | `Axes.cycle : PSeq[int]`, an opaque snapshot of that state; the only thing observed is whether the call MUTATES it |
| `M = len(y)` (number of stacked layers) | `n : int`, `n >= 1` (a stackplot always draws at least the first layer, `:112`) |
| `itertools.cycle(colors)` then `next(...)` per layer | element `i` = `colors[i % len(colors)]` (cycle repeats from the beginning; docstring `:50-52`: "need not be exactly the same length ... colors will repeat from the beginning") |

The model specifies ONLY the `colors is not None` branch (the F2P case:
`colors=["C0","C1","C2"]`). The default-cycle branch (`else`) draws `M` colors
from the Axes cycle in both pre- and post-patch identically; it is not the
tested behaviour and is out of the modelled scope (noted in refinement.md §C).

## 3. Callee provenance (no consumed axioms)

This change introduces no new unchanged-callee dependency that the proof must
axiomatize. The post-patch color source for the `colors is not None` branch is
`itertools.cycle(colors)` + `next(...)`, whose behaviour ("element `i` is
`colors[i mod len(colors)]`") is modelled DEEPLY as `colors[i % len(colors)]`
(Python `itertools.cycle` semantics, docs.python.org/3/library/itertools.html#itertools.cycle).
There is therefore no `@ContractOnly` axiom: the modelled operation is integer
indexing with a modulus, fully expressible in Nagini. `axiom_check.py` validates
the deep model against the real `itertools.cycle` (A-reference) in-container.

`set_prop_cycle` / `get_next_color` (`axes/_base.py`) are referenced only to
identify the property-cycle STATE that the fix must leave untouched; the proof
does not depend on their internal contract, only on the fact that the post-patch
code no longer calls `set_prop_cycle` (so `Axes.cycle` is unchanged).

## 4. The tested behaviour (F2P) and how the spec pins it

`lib/matplotlib/tests/test_axes.py::test_stackplot` (test_patch) changes the
second stackplot call to `ax.stackplot("x","y1","y2","y3", data=data,
colors=["C0","C1","C2"])` and image-compares against the reference produced by
the default Axes cycle (whose first three colors are C0, C1, C2). For the image
to match:
  (a) the call must NOT raise (pre-patch `set_prop_cycle(color=["C0",...])`
      raises ValueError on `CN` aliases — the issue's traceback);
  (b) layer `i` must be drawn with `colors[i % len(colors)]` (here C0, C1, C2);
  (c) the Axes property cycle must be UNCHANGED by the call ("stackplot should
      not change Axes cycler" — the issue title).

The spec pins (b) exactly (`Result()[i] == colors[i % len(colors)]`) and (c)
exactly (`axes.cycle` ensured equal to its pre-state at `Acc(...,1/2)`); (a) is
the refinement consequence of (c) — not mutating the cycle is exactly how the
post-patch avoids the validating `set_prop_cycle` path. `model_prepatch.py`
reproduces the mutation (`axes.cycle := colors`) and FAILS clause (c).
