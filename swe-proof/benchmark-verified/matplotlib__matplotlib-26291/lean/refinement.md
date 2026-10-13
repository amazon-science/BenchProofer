# refinement.md — matplotlib__matplotlib-26291

Maps every operation in `implementation_resolveRenderContext` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep-modeled changed op validated ==
real callee by G-AX), **I** (identical concrete op). Every step is R, A, or I.

The gold patch adds exactly two lines to one method in
`lib/mpl_toolkits/axes_grid1/inset_locator.py`:

```python
 def __call__(self, ax, renderer):
+    if renderer is None:
+        renderer = ax.figure._get_renderer()
     self.axes = ax
     bbox = self.get_window_extent(renderer)
     px, py = self.get_offset(bbox.width, bbox.height, 0, 0, renderer)
     ...
```

This is the single independently-observable fixed behavior; it has one
`Solution_prepatch.lean`.

## Modeling the resolve-renderer-if-None fix

`AnchoredLocatorBase.__call__(self, ax, renderer)` is the axes locator invoked to
compute the inset axes' bounding box. It consumes `renderer` (a drawing/
measurement context) in its two downstream calls (`get_window_extent(renderer)`,
`get_offset(..., renderer)`). Callers ordinarily pass a concrete renderer, but
the tight-bbox path (`matplotlib/_tight_bbox.py:28`) calls `locator(ax, None)` —
it passes `None`. Pre-fix, `None` flowed unchanged into the downstream pipeline,
where `OffsetBox.get_window_extent` did `self.figure._get_renderer()` on an
object whose `figure` was `None`, raising `AttributeError: 'NoneType' object has
no attribute '_get_renderer'` — the reported crash.

The fix resolves the renderer at the head of the method: if the caller passed
`None`, obtain one from the axes' figure (`ax.figure._get_renderer()`), which is
always available; otherwise keep the supplied renderer. Because the guard rebinds
the method's own PARAMETER, the resolved renderer is what BOTH downstream calls
receive. The observable the fix changes is therefore *which renderer each
downstream step is handed*: post-fix each of them gets the same present, concrete
renderer; pre-fix each of them could get `None`.

We model this resolution directly:

  * `suppliedContext : Option RenderContext` — the `renderer` argument (`None` ↔
    `none`, a concrete renderer ↔ `some _`).
  * `surfaceContext : RenderContext` — `ax.figure._get_renderer()`, the always-
    present context from the host's drawing surface.
  * `result : Option RenderContext × Option RenderContext` — the ordered pair of
    renderers the method's two downstream steps are handed: `result.1` the
    renderer passed to `get_window_extent`, `result.2` the renderer passed to
    `get_offset` (both always present post-fix).

A correct (post-fix) implementation hands `some (suppliedContext.getD
surfaceContext)` to each step: the supplied renderer when present, else the
surface's. The pre-fix implementation passes `suppliedContext` through unchanged,
so on `none` both steps are handed an unresolved `none` — the bug.

### Why the pair, and not a single resolved context (audit repair)

An earlier revision modeled `result : Option RenderContext`, bound to "the value
`renderer` holds when `get_window_extent(renderer)` is called". That model is
UNFAITHFULLY NARROW: the patch's rebinding is observable at two call sites, not
one, and a rival that resolves for the first site only satisfies the narrow model
while leaving the second site exactly as broken as before. Such a rival was
submitted, VERIFIED against the narrow spec, and its faithful patch failed
`FAIL_TO_PASS` 1/1 (`test_inset_axes_tight`) while passing `PASS_TO_PASS` 49/49 —
the crash simply reappears one frame downstream, in
`AnchoredOffsetbox.get_offset`, which does `renderer.points_to_pixels(...)` on the
value it was handed.

Pinning the pair COMPONENTWISE closes that hole, and does so without demanding
anything the gold-patched repo does not exhibit: in the post-patch source the
`renderer is None` test and the two intercepted call arguments are the only reads
of `renderer` in the method, so "both steps receive the resolved renderer" is a
property of the real patched code (mechanically re-checked from the method's AST
by `conformance_check.py::_capture_is_complete`, and differentially confirmed at
1e5 inputs with 0 disagreements). It also does not force the gold's SHAPE: the
G-PBT positives include correct impls that resolve per branch, or bind the
resolved value once and share it, rather than mutating a single local.

## Modeled function: `resolveRenderContext` (`AnchoredLocatorBase.__call__`)

Post-patch repo code (`patch.diff`):
```python
def __call__(self, ax, renderer):
    if renderer is None:
        renderer = ax.figure._get_renderer()
    self.axes = ax
    bbox = self.get_window_extent(renderer)                            # extent step
    px, py = self.get_offset(bbox.width, bbox.height, 0, 0, renderer)   # placement step
    ...
```

Lean impl (`implementation_resolveRenderContext`):
```lean
def implementation_resolveRenderContext
    (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
    Option RenderContext × Option RenderContext := Id.run do
  let mut ctx := suppliedContext
  if ctx.isNone then
    ctx := some surfaceContext
  let extentStepContext := ctx
  let placementStepContext := ctx
  return (extentStepContext, placementStepContext)
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `suppliedContext : Option RenderContext` (input) | the `renderer` parameter of `__call__` | **R** | an optional drawing/measurement context ↔ `Option RenderContext`; `None ↔ none`, a concrete renderer ↔ `some _`. mapping.md bijection. |
| 2 | `surfaceContext : RenderContext` (input) | `ax.figure._get_renderer()`, the renderer the axes' figure furnishes (always present) | **R** | the always-available surface context ↔ a present `RenderContext` value (modeled as a given, not `Option`, reflecting that `ax.figure` always yields a renderer). |
| 3 | `let mut ctx := suppliedContext` | `renderer` as received (initial state of the parameter binding) | **I** | start from whatever the caller supplied. |
| 4 | `if ctx.isNone then ctx := some surfaceContext` | `if renderer is None: renderer = ax.figure._get_renderer()` (the **added guard**, the fix) | **I** | the fallback assignment: when nothing was supplied, overwrite the binding with the surface's context. `Option.isNone` ↔ `is None`; `some surfaceContext` ↔ the assignment of `ax.figure._get_renderer()`. |
| 5 | `let extentStepContext := ctx` | the value `renderer` holds where it is read as the argument of `self.get_window_extent(renderer)` (`inset_locator.py:74` post-fix) | **I** | the renderer the EXTENT step is handed. In the real method this is a read of the (possibly rebound) parameter, so it is the settled value, not a fresh computation. |
| 6 | `let placementStepContext := ctx` | the value `renderer` holds where it is read as the argument of `self.get_offset(..., renderer)` (`inset_locator.py:75` post-fix) | **I** | the renderer the PLACEMENT step is handed. It reads the SAME parameter binding as row 5 — that sharing is precisely what rebinding the parameter (rather than resolving at one call site) buys, and it is the property the componentwise postcondition pins. |
| 7 | `return (extentStepContext, placementStepContext)` | the pair of renderers the two downstream calls receive, in source order | **R** | the tuple is the model's carrier for "what each step was handed"; there is no tuple in the Python, only two argument positions read in that order. mapping.md binds `.1`/`.2` to those positions. |

All impl-region ops are **R/I** — NO A-tagged (axiom) content. `RenderContext`
is declared `opaque` purely as the element TYPE of the optional carrier / the
surface value (so the context can appear in the executable impl); no `axiom
RenderContext_*` property is consumed by the proof, which closes structurally
(`problem_spec` pins both components to `some (suppliedContext.getD
surfaceContext)`, computed verbatim by the impl). Nothing about what the two
downstream steps COMPUTE is modeled or assumed — only which renderer each is
given. `conf_skip = false`; `conformance_check.py` differential-tests the R/I
shadow.

## Soundness check (verify ⟹ correct)

- `problem_spec_resolveRenderContext suppliedContext surfaceContext result :=
  result.1 = some (suppliedContext.getD surfaceContext) ∧ result.2 = some
  (suppliedContext.getD surfaceContext)` pins the result EXACTLY — directive 5
  (frame): the entire output is pinned to the two inputs, BOTH components, no
  part left free. Directive 8: the postcondition is grounded in the actual
  inputs (`suppliedContext`, `surfaceContext`), not an ungrounded oracle — it is
  dischargeable only by reproducing the fallback resolution.
- The load-bearing clause is the `none` case: a correct impl must hand `some
  surfaceContext` to EVERY step when `suppliedContext = none`. The prepatch hands
  `none` to both, so it violates `result.1 = some (none.getD surfaceContext) =
  some surfaceContext`. Its carried gold proof cannot close (G-DIFF / G-PANEL);
  the failing case is exactly `suppliedContext = none`.
- Pinning the SECOND component is independently load-bearing, not redundant with
  the first: an impl that resolves the extent step and hands the placement step
  the caller's original `none` satisfies the first conjunct and violates only the
  second. That shape is the recorded verify-does-not-imply-resolve break this
  revision repairs, and it is now a shipped G-PBT reject case
  (`reject-unresolved-at-later-step`) with a refutation witness that goes through
  `result.2` alone.
- The `some r` case is also pinned (both components `= some r`), so an impl may
  not, e.g., always substitute the surface context — it must keep a supplied
  renderer, at every step.
- The `none` case is pinned to the SURFACE's context, not merely to some present
  context, so an impl may not resolve from a substitute source
  (`reject-substitute-present-source`).
- This discriminating case is precisely what the FAIL_TO_PASS test
  (`test_inset_axes_tight`) exercises: `fig.savefig(f, bbox_inches="tight")`
  drives the tight-bbox path, which calls the locator with `renderer=None`;
  pre-fix the unresolved `None` propagated downstream and raised
  `AttributeError`, post-fix the resolved surface renderer lets the save succeed.
  Note that the F2P raises at whichever step is reached FIRST with an unresolved
  renderer, which is why resolving for only one step is not enough to pass it.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  resolution over the full optional-context domain plus ≥1e5 fuzzed inputs,
  compared componentwise by identity, with the real method driven to completion
  and BOTH renderer consumers intercepted (so the second component is genuinely
  observed, not assumed). It additionally asserts, from the method's own AST, that
  those two call arguments and the `is None` test are the only reads of `renderer`
  in the method, so the pair is the whole observable.

## Sibling sites — none

`patch.diff` adds only the two lines above (one guard) in the one method; there
are no other edits. The modeled function covers it. `patch.diff == gold`
verbatim.
