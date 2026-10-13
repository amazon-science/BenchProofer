# refinement.md — matplotlib__matplotlib-26291

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `computePlacement` `do` block and its deep context-substitution branch)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses this opaque axiom), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + narrative are audited by **G-EQ** / **G-AX**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The placement site — `AnchoredLocatorBase.__call__` (`inset_locator.py:71`)

Gold hunk:
```
     def __call__(self, ax, renderer):
+        if renderer is None:
+            renderer = ax.figure._get_renderer()
         self.axes = ax
         bbox = self.get_window_extent(renderer)
         px, py = self.get_offset(bbox.width, bbox.height, 0, 0, renderer)
```

| # | Solution.lean impl op (`computePlacement`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `ctx : Option Ctx` | `renderer` (`RendererBase | None`) | R | `None ↔ none`, a live renderer `r ↔ some r` (mapping.md §2). |
| A2 | param `host : Host` | `ax` (the host axes) | R | opaque carrier; only its figure's context and pipeline role are observed (mapping.md §2). |
| A3 | `match ctx with | some c => c | none => hostContext host` | `if renderer is None: renderer = ax.figure._get_renderer()` | I | the **context substitution**: a present context passes through; an absent one is replaced by the host figure's context. This is the one operation the patch added (the `None`-guard fallback), modeled deeply — not axiomatized. |
| A4 | `hostContext host` (in the `none` branch) | `ax.figure._get_renderer()` | A-consumed (opaque) | UNCHANGED retrieval of the host figure's drawing context; total `Host → Ctx`, no contract assumed beyond totality (G-AX). |
| A5 | `placeWith chosen host` | the unchanged pipeline `self.get_window_extent(renderer)` → `get_offset(...)` → `Bbox.from_bounds(...)` → `transSubfigure.inverted()` → `TransformedBbox(...)` (`inset_locator.py:73-77`) | A-consumed (opaque) | UNCHANGED downstream; total/deterministic `Ctx → Host → Region` given a concrete context (G-AX). The patch did not touch it. |
| A6 | `return Except.ok (placeWith chosen host)` | the returned `TransformedBbox` | R | region ↔ `Region`; `Except.ok` ⇔ the patched code never raises (mapping.md §2). |

The discriminating content of the change — an **absent** `renderer` must NOT be
fed straight into the measurement (which raises on this figure-less artist) but
must be replaced by `ax.figure._get_renderer()` — lives in the impl's
`none ⇒ hostContext host` match branch (model) ⇔ the `if renderer is None:
renderer = ax.figure._get_renderer()` guard (real), and is pinned by the
frozen postcondition `ctx = none → out = Except.ok (placeWith (hostContext
host) host)`. The pre-patch fed the absent context straight to
`get_window_extent`, which on the container-less locator raised
`AttributeError: 'NoneType' object has no attribute '_get_renderer'`;
`Solution_prepatch.lean` reproduces that (the `none ⇒ Except.error` branch) and
**fails** both `∃ reg, out = Except.ok reg` and the
`ctx = none → out = Except.ok (placeWith (hostContext host) host)` clause (G-DIFF).

## B. Consumed axioms and the A-reference

- **A-consumed (opaque):** `hostContext` (`ax.figure._get_renderer`) and
  `placeWith` (the unchanged measure→offset→transform pipeline). Both UNCHANGED
  callees, left fully opaque (no `ensures`); the proof consumes only their
  existence/typing, not any output value. G-AX confirms each is a total,
  deterministic op of the claimed signature on a real `inset_axes` locator.
- **A-reference:** the deep context-substitution model — specifically the
  `none`-branch of the impl match and the `ctx = none` postcondition — encodes
  a CHECKED fact about the *unchanged* downstream: on the
  figure-less locator, the absent-context path is exactly the one that the fix
  exists to avoid. G-AX runs the REAL pre-patch with `renderer=None` and asserts
  it raises `AttributeError`, and that the substitution (`ax.figure._get_renderer()`)
  makes the real downstream return a region. This is validated == real, not a
  consumed contract about the changed function.
- **No callee under change is axiomatized.** `__call__` (the function under spec)
  is modeled (`computePlacement`), never assumed. The renderer substitution is
  modeled deeply (A3, an I op over R-refined carriers), not hidden behind an
  axiom.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — adding the
`renderer is None` fallback to the host figure's context — is modeled **deeply**
(the `none ⇒ hostContext host` branch of the impl match, step A3, pinned by the
`ctx = none` postcondition), not hidden behind an axiom. There is no consumed
axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`computePlacement` verifies only if, branch by branch on the input `ctx`, its
output is `Except.ok (placeWith c host)` when `ctx = some c` (present-context
pass-through), `Except.ok (placeWith (hostContext host) host)` when `ctx = none`
(the fallback, A3), and is always `Except.ok` (the never-raise frame) — the
three frozen postconditions jointly pin the exact gold value on every input
(A1–A6), each grounded directly in the inputs and the two opaque unchanged
callees, with no spec-level answer function an impl could echo. By R
(`renderer|None ↔ Option Ctx`, region ↔ `Region`, returned ↔
`Except.ok`) the verified placement equals the patched `__call__` output on every
context configuration; by G-CONF the R/I transliteration of the substitution
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs (present-renderer and
absent/`None`). The two opaque A-consumed callees are unchanged and G-AX-witnessed
total; the A-reference's `none`-branch is the G-AX-witnessed bug fact. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). Trust points: refinement
fidelity (this doc, G-EQ + G-CONF) and the two opaque-callee totalities + the
absent-context bug fact (G-AX).
