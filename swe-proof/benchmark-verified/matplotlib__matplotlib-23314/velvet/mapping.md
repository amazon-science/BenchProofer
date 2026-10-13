# mapping.md — matplotlib__matplotlib-23314

Binds `Solution.lean` symbols to the repo at
`base_commit = 97fc1154992f64cfb2f86321155a7404efeb2d8a`.

Repo file under change: `lib/mpl_toolkits/mplot3d/axes3d.py`
(a visibility short-circuit added at the top of the 3-D subplot's renderer).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderStep (visible : Bool) (renderedScene : Scene)` | `Axes3D.draw(self, renderer)` — `lib/mpl_toolkits/mplot3d/axes3d.py:389-446` | the modeled changed function (the renderer for one 3-D subplot element) |
| `visible` | `self.get_visible()` — `matplotlib/artist.py:809-811` (returns `self._visible`, set by `set_visible`, `artist.py:1008-1016`) | the element's own visibility flag: `true` ↔ `get_visible()` is `True`, `false` ↔ `False` |
| `renderedScene` | the cumulative effect on `renderer` of the UNCHANGED body (`self.patch.draw`, the projection/zorder pass over `self._children`, the axis pane/axis draws, and `super().draw(renderer)`) — `axes3d.py:390-446` | FREE INPUT: the content the full emission would place on the output target. Unchanged by the fix; see §3. |
| `out.emitted` (`RenderResult` field) | whether control reaches the body that touches `renderer` at all | the SIDE-EFFECT observable: `true` ↔ the body ran and drew to `renderer`; `false` ↔ the early `return` was taken and `renderer` was never touched |
| `out.scene` (`RenderResult` field) | the resulting content on the `renderer` / output canvas | what ends up rendered; `blank` ↔ nothing placed |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.get_visible()` : a `bool` | `Bool` (`visible`) | `True` ↔ `true`; `False` ↔ `false`. Only the boolean is observed; nothing else of the element's state enters the decision. |
| "the full body ran and emitted artists to `renderer`" | `Bool` (`emitted`) | `true` ↔ control entered the body (≥1 draw call against `renderer`); `false` ↔ the early `return` ran with NO draw call. The F2P image-comparison observable "the hidden subplot's pixels are absent" ⇔ `emitted = false`. |
| the pixels / artist content placed on the output canvas | `Scene` (`Scene := Nat`), `blank := 0` | a present rendering ↔ some `Scene` value (taken from the free input `renderedScene`); an untouched canvas ↔ `blank`. Only "empty vs. some content" is observed; `Scene`'s internal structure is irrelevant to the modeled decision. |

`Scene` is modeled as an opaque `Nat` because the guard observes only whether the
emission happened (`emitted`) and whether anything was placed (`blank` vs. not);
the concrete pixel content is produced entirely by the unchanged body and is
carried untouched through the free input `renderedScene`.

## 3. Callee provenance

No axioms and no A-reference deep models.

- The full emission body — `self.patch.draw(renderer)`, the
  `apply_aspect`/projection/`zorder` pass over `self._children`, the per-axis
  `draw_pane`/`draw` calls, and `super().draw(renderer)` — is **UNCHANGED** by
  the fix. The patch does not alter WHAT that body draws; it only decides
  WHETHER to run it. Its cumulative effect on the output target is therefore
  taken as the **free input** `renderedScene : Scene`. The spec makes no
  behavioural claim about it and holds for EVERY value, so there is nothing to
  check against a real callee — hence **no G-AX** (mirrors
  django__django-11451's free-input `backendOutcome`).
- The CHANGED op is the visibility guard itself
  (`if not self.get_visible(): return`), modeled **deeply** as the conditional
  that (a) suppresses the entire emission (`emitted := false`) and (b) leaves the
  output target untouched (`scene := blank`). No outside contract is consumed
  (I-tagged, refinement.md).

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub. The fix's only DISCRIMINATING
observable is a **side effect** — that the 3-D subplot's full draw body is NOT
run, so nothing is emitted to the renderer, when the element is hidden. This is
exactly what the F2P test asserts: `test_invisible_axes[png]` uses
`@check_figures_equal` to compare a figure with one `set_visible(False)` 3-D
subplot against an empty reference figure — an **image-level** comparison that
materializes only by actually rendering through a real matplotlib `Figure` +
`Axes3D` + Agg backend.

There is no backend-free, input-dependent R/I shadow to differential-test:

- The side effect (`emitted`) and the emitted pixels (`scene`) materialize only
  against a live matplotlib figure with a real renderer/backend: to observe
  "nothing was drawn" one must drive `Axes3D.draw(renderer)` through the actual
  rendering stack and compare rasterized output — i.e. the F2P image-comparison
  test itself, not a pure transliteration this gate can fuzz over ≥10⁵ inputs.
- The visible-path's emitted content is the free input `renderedScene` (the
  unchanged body, §3); its R/I shadow is a constant pass-through with no
  input-dependent computation to refute. The changed op's content is the boolean
  guard `not get_visible()`, whose only shadow is a constant decision over a
  presence bit — diffing it carries no information the spec (G-VERIFY) does not
  already pin.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the modeled op's only observable is a
side effect on a live rendering backend with no backend-free R/I shadow, set
`meta.json conf_skip=true` and ship a `status=skip` stub (precedent:
django__django-11451, django__django-11179). Soundness of the modeled behaviour
is carried instead by **G-VERIFY** (the spec provably forces `emitted = false`
∧ `scene = blank` when the element is hidden) and **G-DIFF** (the prepatch,
which lacks the guard and always emits, fails exactly the hidden-case clause —
refinement.md §B).

## 5. Notes

The two FAIL_TO_PASS / PASS_TO_PASS additions named `test_invisible_axes[png]`
(one in `lib/mpl_toolkits/tests/test_mplot3d.py`, the new F2P; one renamed in
`lib/matplotlib/tests/test_axes.py`) exercise the SAME single fixed behavior —
a `set_visible(False)` subplot must produce no rendered content — for the 3-D
and 2-D axes respectively. The 2-D `Axes.draw` already had this guard at
base_commit; only the 3-D `Axes3D.draw` override lacked it, which is the bug.
One modeled function + one prepatch covers the fixed behavior; the gold-verbatim
`patch.diff` resolves it (G-RESOLVE).

`visible` and `renderedScene` are both read-only inputs — neither is declared
`mut` (directive 5): the guard reads them and produces a fresh `RenderResult`,
mutating nothing it is handed.
