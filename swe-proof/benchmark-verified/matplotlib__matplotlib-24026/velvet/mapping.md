# mapping.md — matplotlib__matplotlib-24026

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 14c96b510ebeba40f573e512299b1976f35b620e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the (deep-modeled) callee.

Repo file under change: `lib/matplotlib/stackplot.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectLayerColors (mut sharedCycle) (colors) (layerCount)` | the `colors`-supplied colour-selection of `stackplot(...)` — `lib/matplotlib/stackplot.py:72-73, 110-123` | the modeled changed function: pick the per-area fill colours and leave the axes' shared colour cycle untouched |
| `sharedCycle : List String` *(`mut`, frame-pinned)* | the axes' shared property/colour cycle, read via `axes._get_lines.get_next_color()` (`stackplot.py:111,120`) and overwritten pre-patch via `axes.set_prop_cycle(color=colors)` (`stackplot.py:73`) | the colour-cycle state shared with the OTHER artists on the same axes; must survive unchanged |
| `colors : List String` | the `colors=...` keyword argument of `stackplot` (`stackplot.py:14`, used at `:72-73`) | the user-supplied, non-empty list of colour specifications |
| `layerCount : Nat` | the number of stacked areas = `y.shape[0]` = `len(args)` rows (`y = np.row_stack(args)`, `stackplot.py:69`); areas are drawn at `:112` and the `:119` loop | how many fill colours are needed |
| `cyclicColors (colors) (layerCount)` *(deep model — A-reference)* | `itertools.cycle(colors)` consumed by `next(colors)` once per area (post-patch `stackplot.py:74, 113-122`) | pure spec: the per-area colour list, the supplied colours repeated cyclically; deep model of the unchanged stdlib finite cyclic iterator, validated `cyclicColors == itertools.cycle` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo construct the change removes (refinement audit only, not in the
consumer spec view): `axes.set_prop_cycle(color=colors)` (`stackplot.py:73`) and
the per-area `color = axes._get_lines.get_next_color()` (`stackplot.py:111,120`),
replaced post-patch by `colors = itertools.cycle(colors)` /
`colors = (axes._get_lines.get_next_color() for _ in y)` and `next(colors)`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a single colour specification (named colour, hex, `CN` cycle reference such as `"C2"`) | Lean `String` | the token is carried opaquely; equal tokens ↔ equal `String`s. stackplot only copies/reorders these tokens (it passes them on as `facecolor=`), never interpreting them, so opaque equality is faithful. G-CONF resolves both sides to an RGBA tuple via `matplotlib.colors.to_rgba` before comparing (the observable the F2P image test ultimately renders). |
| the supplied `colors` list | `List String` | Python list ↔ `List String`; `len(colors)` ↔ `colors.length`; indexing `colors[i % len(colors)]` ↔ `colors[i % colors.length]!`. Non-empty (`require colors.length > 0`) ↔ the call site only takes the cyclic branch when `colors is not None` and a list is given. |
| the number of stacked areas | `Nat` (`layerCount`) | `y.shape[0]` ↔ `layerCount`; the ordered area indices `range(len(y))` ↔ `List.range layerCount`. |
| the per-area colour list handed to `fill_between(facecolor=...)` | `List String` (`out`) | the ordered list of colour tokens, area `i` ↔ `out[i]`; `out.length` ↔ number of areas. |
| the axes' shared colour cycle (`axes._get_lines`) | `List String` (`sharedCycle`) | the shared cycle's state, observed through the colour sequence it would hand to the OTHER artists. The directive-5 frame `sharedCycle = sharedCycleOld` ↔ "the colour the axes gives its next non-stackplot artist is the same as if stackplot had not been called" — checked end-to-end in conformance_check.py via a control axes. |

Lean has no aliasing: a fresh `let`-binding to an immutable value is a private
copy, exactly the role `itertools.cycle(colors)` plays (a private iterator that
does not touch the axes cycle).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `cyclicColors` deep model ↔ `itertools.cycle` (A-reference)
**Callee:** CPython `itertools.cycle(iterable)`, consumed by `next(...)` once per
area. Post-patch source (`stackplot.py:72-74, 113, 121`):

```python
if colors is not None:
    colors = itertools.cycle(colors)
else:
    colors = (axes._get_lines.get_next_color() for _ in y)
...
coll = axes.fill_between(..., facecolor=next(colors), ...)   # area 0
for i in range(len(y) - 1):                                  # areas 1..M-1
    r.append(axes.fill_between(..., facecolor=next(colors), ...))
```

`itertools.cycle(colors)` yields `colors[0], colors[1], …, colors[len-1],
colors[0], …` indefinitely; drawing the colour for area `i` is the `(i+1)`-th
`next`, i.e. `colors[i % len(colors)]`. That is exactly what `cyclicColors`
encodes (`(List.range layerCount).map (fun i => colors[i % colors.length]!)`).
There is **no `nextColor` axiom** the proof consumes; the changed colour-source
operation is modeled **deeply** and validated against the real iterator.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `itertools.cycle`
(the same stdlib the gold patch imports), drawing `layerCount` values, on
boundary cases (single colour; more colours than areas; fewer colours than areas
— wrap-around; `layerCount = 0`) plus 20 000 randomized `(colors, layerCount)`
fuzz cases, and asserts `cyclicColors(colors, layerCount)` equals the real
`[next(itertools.cycle(colors)) for _ in range(layerCount)]`. Imports only stdlib
`itertools`. Exit 0 iff sound.

### 3.2 The shared-cycle frame — no axiom
The directive-5 frame (`sharedCycle = sharedCycleOld`) is the change's discriminating
content; it consumes no callee contract. Its real-world soundness (filling the
areas does not perturb the axes' shared colour cycle) is exercised end-to-end by
conformance_check.py against the patched repo (G-CONF), not by an axiom.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24026`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `cyclicColors` to Python (`colors[i % len(colors)]`) and resolves
colour tokens to RGBA via `matplotlib.colors.to_rgba`; there are NO A-tagged ops
in the computed `out` (no consumed axiom), so the colour-value shadow is pure
R/I. The frame leg is checked against a control axes (a second, untouched axes
whose next cycle colour must match the stackplot'd axes' next cycle colour).
