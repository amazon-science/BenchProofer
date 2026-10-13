# refinement.md — matplotlib__matplotlib-26208

The operation-by-operation correspondence between `model.py`'s implementation
(the two builder functions `build_companion_sharing_horizontal` /
`build_companion_sharing_vertical`) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**,
proof uses the axiom's `Ensures`, vs **A-reference**, a deep model validated ==
the real callee by `axiom_check.py` / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This is a genuine **multi-site** change: two independently-fixed behaviours
(the horizontal-share builder and the vertical-share builder). Each is modeled
as its own contracted+implemented function with its own differential witness
(`model_prepatch.py` reverts site A; `model_prepatch_2.py` reverts site B).

## A. The horizontal-share site — `twinx()` (`lib/matplotlib/axes/_base.py:4416`)

Gold hunk:
```
         ax2.patch.set_visible(False)
+        ax2.xaxis.units = self.xaxis.units
         return ax2
```

| # | model.py impl op (`build_companion_sharing_horizontal`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| H0 | (no node) the unchanged builder body: `self._make_twin_axes(sharex=self)` and the tick/label/offset/visibility/autoscale calls | the unchanged lines of `twinx` above the inserted line | I | these operations are untouched by the patch and do not affect the unit descriptor or the observed behaviour; the skeleton models the changed hunk only (mapping.md §2). |
| H1 | `companion_horizontal = CoordinateAxis()` (a fresh axis whose `descriptor is None`) | the new companion Axes' `ax2.xaxis`, a brand-new `Axis` with `units = None` (built by `_make_twin_axes` → `add_subplot`/`add_axes`; `Axis.__init__` sets `self.units = None`, `axis.py:898`) | R | `Axis` ↔ `CoordinateAxis` (single touched field `units` ↔ `descriptor`); a freshly built companion axis starts with `units is None`, modeled by the constructor postcondition `descriptor is None`. |
| H2 | `companion_horizontal.descriptor = source_horizontal.descriptor` | `ax2.xaxis.units = self.xaxis.units` | R | the **inserted** line. Field-reference copy: `units` ↔ `descriptor`, `ax2.xaxis` ↔ `Result()`, `self.xaxis` ↔ `source_horizontal`. A reference assignment (Python `=`) in both; the model's `is`-identity postcondition pins exactly the object-identity the assignment establishes. |
| H3 | `return companion_horizontal` | `return ax2` | R | returns the companion axis (R: `Axis` ↔ `CoordinateAxis`). |

## B. The vertical-share site — `twiny()` (`lib/matplotlib/axes/_base.py:4446`)

Gold hunk:
```
         ax2.patch.set_visible(False)
+        ax2.yaxis.units = self.yaxis.units
         return ax2
```

| # | model.py impl op (`build_companion_sharing_vertical`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| V0 | (no node) the unchanged builder body | the unchanged lines of `twiny` above the inserted line | I | as H0, for the vertical-share builder. |
| V1 | `companion_vertical = CoordinateAxis()` (fresh, `descriptor is None`) | `ax2.yaxis`, a brand-new `Axis` with `units = None` | R | as H1, with the y-axis as the shared one. |
| V2 | `companion_vertical.descriptor = source_vertical.descriptor` | `ax2.yaxis.units = self.yaxis.units` | R | the **inserted** line for the vertical site; field-reference copy `units`↔`descriptor`, `ax2.yaxis`↔`Result()`, `self.yaxis`↔`source_vertical`. |
| V3 | `return companion_vertical` | `return ax2` | R | as H3. |

## C. The discriminating clause and the differential witnesses

The discriminating content of the change is the **identity propagation** of the
unit descriptor onto the companion's shared axis. It lives in the postcondition
`Result().descriptor is source.descriptor` (model) ⇔ the inserted
`ax2.<axis>.units = self.<axis>.units` (real).

- `model_prepatch.py` reverts site A (omits H2): the companion axis keeps
  `descriptor is None`, so `Result().descriptor is source_horizontal.descriptor`
  **fails** (Nagini: postcondition might not hold) — the spec sensing the bug at
  the horizontal site (G-DIFF).
- `model_prepatch_2.py` reverts site B (omits V2): symmetric failure on
  `Result().descriptor is source_vertical.descriptor` — the vertical site
  (G-DIFF).

This matches reality: pre-patch, `twin.<axis>.units is None` (verified locally:
the pre-patch builder leaves the descriptor unset), which fails both the
`is not None` and the `is source.units` assertions of the F2P tests
`test_twin_units[x]` / `test_twin_units[y]`. `axiom_check.py` (G-AX) confirms
this discrimination directly against the real builders: it classifies each real
build as `patched` (descriptor propagated, identity holds) or `prepatch`
(descriptor stays None) and is self-validating against either tree (panel
DEFECT-2 fix — it no longer asserts the post-fix invariant unconditionally and
so does not spuriously fail on the `base_commit` image).

## D. No kind-3 (unexpressible-changed-op) steps; no consumed axioms

Every step above is R or I. The one operation that genuinely *changed* — the
descriptor propagation — is modeled **deeply** (the fresh-axis `None` start +
the explicit reference copy, steps H1–H2 / V1–V2), an **A-reference** validated
== the real `twinx`/`twiny` by G-AX (`axiom_check.py`), **not** hidden behind an
axiom about the function under change. There is **no consumed `@ContractOnly`
axiom** (the `axioms` region is empty): nothing the proof relies on is opaque —
object construction, field read/write, and reference identity are all directly
expressible in Nagini.

## E. verify(model) ⇒ resolved

Each builder verifies only if its returned companion axis references the **same**
descriptor object as the source axis (H2/V2 identity postcondition) and is
non-None — and only because the companion axis starts with no descriptor
(H1/V1). By R (`Axis` ↔ `CoordinateAxis`, `units` ↔ `descriptor`, the unchanged
builder body H0/V0) the verified builders equal the gold-patched `twinx`/`twiny`
on the tested inputs; by G-AX the deep model equals the real builders'
observable behaviour (the A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ) plus the A-reference soundness (G-AX); there is no consumed-axiom
trust point.
