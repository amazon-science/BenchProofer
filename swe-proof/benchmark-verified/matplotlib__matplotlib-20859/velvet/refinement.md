# refinement.md — matplotlib__matplotlib-20859

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `anchorToParent` `do` block, the deep `isRegion`/`isCanvas` models, and the
`anchorSpec` dispatch) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses an axiom's `ensures`, **A-reference** where a deep model is validated
== the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The parent-dispatch site — `Legend.__init__` (`lib/matplotlib/legend.py:433-442`)

Gold hunk (the load-bearing line):
```
- elif isinstance(parent, Figure):
+ elif isinstance(parent, FigureBase):
        self.isaxes = False
        self.set_figure(parent)
    else:
-       raise TypeError("Legend needs either Axes or Figure as parent")
+       raise TypeError("Legend needs either Axes or FigureBase as parent")
```
(plus the matching import `from matplotlib.figure import Figure` →
`from matplotlib.figure import FigureBase`).

| # | Solution.lean impl op (`anchorToParent`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `parent : Container` | `parent` arg of `Legend.__init__` | R | the parent object ↔ `Container` (mapping.md §2): an `Axes` ↔ `.region`, a figure-like canvas ↔ `.canvas _ topLevel`, anything else ↔ `.other`. G-CONF bridges via real objects. |
| A2 | `parentIsRegion := isRegion parent`; first branch `if parentIsRegion then .ok {fromRegion := true, canvas := regionCanvas parent}` | `if isinstance(parent, Axes): self.isaxes = True; self.set_figure(parent.figure)` | A-reference + I | the region test is `isinstance(parent, Axes)`, modeled deeply by `isRegion` (A-reference, validated == real `isinstance` by G-AX). The branch's consequence — bind to `parent.figure`, set `isaxes` — is **I** (concrete, transliterated by G-CONF). |
| A3 | `parentIsCanvas := isCanvas parent`; second branch `if parentIsCanvas then .ok {fromRegion := false, canvas := canvasId parent}` | `elif isinstance(parent, FigureBase): self.isaxes = False; self.set_figure(parent)` | A-reference + I | the canvas test is the **BROAD** `isinstance(parent, FigureBase)` (post-patch), modeled deeply by `isCanvas` (A-reference, validated == real `isinstance` by G-AX). The consequence — bind directly to `parent`, clear `isaxes` — is **I**. This is the changed line: `isCanvas` accepts a nested sub-canvas (`topLevel = false`) that the pre-patch narrow `isTopCanvas` rejects. |
| A4 | `else .error .unsupportedParent` | `else: raise TypeError("Legend needs either Axes or FigureBase as parent")` | R + I | the rejection of an unsupported parent ↔ `Except.error .unsupportedParent` (mapping.md §2; tests observe the raised `TypeError` type). The message-text edit is observationally irrelevant (no test asserts the string) — pure I. |

Discriminating content of the change — a nested sub-canvas (`.canvas i false`)
is **accepted** (bound to itself), not rejected — lives in `isCanvas` being the
broad membership test in A3. The pre-patch used the narrow `isTopCanvas`, which
maps a nested sub-canvas to the `else` branch (`unsupportedParent`);
`Solution_prepatch.lean` reproduces that and **fails** `out = anchorSpec parent`
on exactly the goal `topLevel = true` (the nested sub-canvas case) — G-DIFF.

## B. No consumed axioms, one A-reference

The only callee this slice invokes that the patch does NOT change is the builtin
`isinstance` against the unchanged classes `Axes` / `FigureBase` / `Figure`. It
is modeled **deeply** (`isRegion`/`isCanvas`/`isTopCanvas` + the
`isTopCanvas → isCanvas` lemma) and validated == the real `isinstance` by G-AX
(mapping.md §3.1) — an **A-reference**, not a consumed axiom. There is no
module-level `axiom` in this bundle.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
membership test the second dispatch arm uses — is modeled **deeply** (the broad
`isCanvas` predicate, A3, an A-reference + I), not hidden behind an axiom about
the function under change: there is no consumed axiom. The function under spec
(`anchorToParent` ↔ the dispatch block) is never axiomatized.

## D. verify(Solution) ⇒ resolved

`anchorToParent` verifies only if its output equals `anchorSpec parent`, which
binds a region to its owning canvas (A2), binds **any** figure-like canvas —
top-level OR nested — directly to itself (A3, the broadened test), and rejects
everything else (A4). By R (`parent ↔ Container`, identity tags for the bound
canvas, `set_figure`/`isaxes` as the observable post-state) the verified dispatch
equals the patched `Legend.__init__` parent-dispatch on the tested parents; by
G-AX the deep models `isRegion`/`isCanvas`/`isTopCanvas` equal the real
`isinstance` and the `isTopCanvas → isCanvas` hierarchy fact holds (A-reference);
by G-CONF the R/I transliteration of the dispatch agrees with `patch.diff`'s
behaviour on ≥10⁵ real parent objects. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: callee-model soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
