# mapping.md — matplotlib__matplotlib-25287

## Symbol binding (file:line @ base_commit)
Changed file: `lib/matplotlib/axis.py`.

| Lean function | Python site | location @ base_commit |
|---|---|---|
| `implementation_horizOffsetTextColor` | `XAxis._init`, the `self.offsetText.set(..., color=...)` call | `lib/matplotlib/axis.py` ~2252–2266 |
| `implementation_vertOffsetTextColor` | `YAxis._init`, the `self.offsetText.set(..., color=...)` call | `lib/matplotlib/axis.py` ~2517–2536 |

Each `_init` initializes its axis's `offsetText` artist; the modeled value is the
`color=` argument passed to `self.offsetText.set(...)`, i.e. the resolved color of
the offset text.

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | note |
|---|---|---|
| `Color` (opaque token) | a matplotlib color spec (`str` name / RGBA tuple) drawn from `mpl.rcParams[...color...]` | only identity matters; never inspected. |
| `tickColor : Color` | `mpl.rcParams['xtick.color']` (horiz) / `mpl.rcParams['ytick.color']` (vert) | the tick-mark color. |
| `labelColor : Option Color` | `mpl.rcParams['xtick.labelcolor']` (horiz) / `mpl.rcParams['ytick.labelcolor']` (vert) | the tick-label color setting; the string sentinel `'inherit'` ↔ `none`, any other color value `v` ↔ `some v`. |
| `result : Color` | the `color=` argument actually passed to `self.offsetText.set(...)` | the resolved offset-text color. |
| `labelColor.getD tickColor` | `tick_color = rc[color] if rc[labelcolor]=='inherit' else rc[labelcolor]` | `none ↦ tickColor`, `some v ↦ v`. |

The `'inherit'` ↔ `none` correspondence is the heart of the model: matplotlib's
`*.labelcolor` rcParam uses the literal string `'inherit'` as its
defer-to-tick-color sentinel; every other value is an explicit color.

## Callee provenance + flag deps
No unchanged outside callee is consumed. The patch reads two rcParams
(`*tick.color`, `*tick.labelcolor`) — plain configuration data, entering the
model as `tickColor` and `labelColor` — and performs a pure two-way choice
inline. `self.offsetText.set` / `blended_transform_factory` etc. are unrelated to
the modeled color decision and are not part of the spec. Hence no
`opaque <callee>` decl and no `axiom <callee>_prop`.

The choice depends only on whether `labelColor` is the `'inherit'` sentinel
(modeled as `none`) — there is no other flag dependency.

## G-CONF fuzz seed
Pinned seed: **25287** (also in `conformance_check.py`).
