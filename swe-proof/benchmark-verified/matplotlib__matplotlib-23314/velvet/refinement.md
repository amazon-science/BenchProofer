# refinement.md — matplotlib__matplotlib-23314

Operation-by-operation correspondence between `Solution.lean`'s `renderStep`
impl region and `patch.diff` (the gold patch adds a visibility short-circuit to
the top of the 3-D subplot renderer: `if not self.get_visible(): return`). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — A-consumed
or A-reference), or **I** (identical concrete op). EVERY step is R, A, or I.

`patch.diff` is the gold patch **verbatim** (applies at base_commit, resolves —
G-RESOLVE).

## A. The visibility short-circuit — `Axes3D.draw`

Gold hunk (context + added lines):
```
     @martist.allow_rasterization
     def draw(self, renderer):
+        if not self.get_visible():
+            return
         self._unstale_viewLim()
         # draw the background patch
         self.patch.draw(renderer)
         ...
```

| # | Solution.lean impl op (`renderStep`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `if visible = false then ...` | `if not self.get_visible():` (the added guard) | **I** | identical concrete op: the CHANGED op, modeled deeply as the conditional. Python `not self.get_visible()` ↔ Lean `visible = false`; `get_visible()` (a `bool`) ↔ `visible : Bool` (mapping.md §2). |
| A2 | `return { emitted := false, scene := blank }` (guard taken) | `return` (the added early return — emits nothing, touches `renderer` not at all) | **I** | the early return performs NONE of the emission work and places nothing on the output target. `emitted := false` ↔ "no `patch.draw`, no projection pass, no axis draws, no `super().draw` — `renderer` is never touched"; `scene := blank` ↔ the canvas is left empty (the `@check_figures_equal` vs. empty-reference observable, mapping.md §2). |
| A3 | `return { emitted := true, scene := renderedScene }` (guard not taken) | falls through to `self._unstale_viewLim()` … `super().draw(renderer)` (`axes3d.py:390-446`, UNCHANGED) | **R** + free input | the visible path runs the UNCHANGED full emission body; `emitted := true` ↔ "the draw body was entered and drew to `renderer`"; the content it places ↔ the free input `renderedScene : Scene` (mapping.md §3). The body is unchanged by the fix, so its cumulative effect is taken as a given input, not re-derived or axiomatized. |

No A (axiom) steps; no A-reference deep models; no kind-3 (changed
inexpressible) steps. The single changed op (A1/A2) is the early-return guard,
modeled deeply and tagged **I**. The unchanged fallthrough (A3) carries the
unchanged body's effect as a free input (**R**).

## B. verify(Solution) ⇒ resolved; prepatch fails on the right clause

`renderStep` verifies only if `out = renderDecision …` AND the explicit
discriminating clause `(visible = false) → (out.emitted = false ∧ out.scene =
blank)`, i.e. both:
- when the element is hidden (`visible = false`): `emitted = false` AND `scene =
  blank` (forced by A1/A2); and
- otherwise: `emitted = true` AND `scene = renderedScene` (A3).

By R (mapping.md §2) this is exactly: the patched `Axes3D.draw` performs NO
rendering work and emits nothing to `renderer` when `get_visible()` is `False`;
otherwise it behaves as the unchanged emission body dictates. The F2P test
`test_invisible_axes[png]` (the new entry in `lib/mpl_toolkits/tests/
test_mplot3d.py`) asserts precisely this: a figure containing one
`set_visible(False)` 3-D subplot is `check_figures_equal` to an empty reference
figure — i.e. nothing is rendered (`emitted = false` ∧ `scene = blank`). The
PASS_TO_PASS suite requires the visible path to be unperturbed when the element
is visible — the A3 leg.

The prepatch (`Solution_prepatch.lean`) omits the guard: it always proceeds
(`emitted := true`) and emits `renderedScene`. With a hidden element the frozen
spec demands `emitted = false` ∧ `scene = blank`, so `prove_correct` fails on
exactly the discriminating clause:
```
case «ensures_1: (visible = false) → (out.emitted = false ∧ out.scene = blank)»
⊢ visible = true            -- unprovable: the element may be hidden
case «ensures_2: out = renderDecision visible renderedScene»
⊢ visible = true            -- unprovable for the same reason
```
This is the precise bug the issue describes ("`set_visible()` not working for 3d
projection — the subplot remains visible"). G-DIFF passes.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
visibility short-circuit — is modeled **deeply** (the `renderDecision`
conditional / the `if … then … else` impl, A1/A2, **I**), not hidden behind an
axiom. There are no consumed axioms: the only callee the visible path touches
(the unchanged emission body: `patch.draw`, the projection/zorder pass, the axis
draws, `super().draw`) is folded into the free input `renderedScene`, about
which the spec claims nothing (mapping.md §3), so there is nothing for G-AX to
check.

## D. G-CONF — conf_skip=true

The fix's only DISCRIMINATING observable is a side effect (nothing is drawn to
the renderer) on a live matplotlib figure + Agg backend — there is no
backend-free, input-dependent R/I shadow to differential-test, and the
visible-path scene is the free input `renderedScene`. `conformance_check.py` is
a documented `status=skip` stub (`meta.json conf_skip=true`; precedent:
django__django-11451, django__django-11179). Soundness is carried by G-VERIFY
(spec forces `emitted = false` ∧ `scene = blank` on a hidden element) and
G-DIFF (the prepatch fails exactly that clause). See mapping.md §4.
