# mapping.md — matplotlib__matplotlib-23314

## Symbol binding (file:line @ base_commit 97fc1154)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_render` | `Axes3D.draw(self, renderer)` | `lib/mpl_toolkits/mplot3d/axes3d.py:389` |
| `Drawable.visible` | `self.get_visible()` (reads `Artist._visible`) | inherited from `matplotlib.artist.Artist` |
| `renderContents` | the entire body of `draw` after the new guard (background patch, aspect, projection matrix, collections/patches z-ordering, axis panes/axes, `super().draw`), as ONE action | `axes3d.py:390-447` |
| `m` (the effect monad) | drawing onto `renderer` — the only effect `draw` has | `matplotlib.backend_bases.RendererBase` |
| `pure ()` | `draw` returning having drawn nothing | the bare `return` of the guard |

## What is being modeled, and why it is an action rather than a value

`Axes3D.draw` returns `None`. Its entire observable content is the drawing it
performs on the renderer it is handed, so the modeled object is the ACTION `draw`
carries out, not a value it computes. Lean states that action in an ARBITRARY
monad `m` over an ARBITRARY `renderContents : m Unit`, and the postcondition is an
equation between actions: hidden ⇒ the action is `pure ()`, shown ⇒ the action is
`renderContents`.

Holding `m` abstract is load-bearing for the refinement, not decoration. A
renderer is write-only from `draw`'s side: `draw` has no operation that reads back
what has already been emitted and none that removes it. An abstract `m` has
exactly that shape — the only action available in it is `renderContents`, composed
with `pure`/`>>=` — so a Lean implementation cannot do anything a real `draw`
cannot: it cannot snapshot the renderer, cannot restore it, and cannot rebuild the
prior output after emitting. Consequently `result = pure ()` on the hidden path
says what it is meant to say: nothing was drawn. Any implementation that carries
out `renderContents` on that path leaves `renderContents >>= _ = pure ()` to be
proved for an arbitrary action, which is false.

`[LawfulMonad m]` is assumed in `correct_render` (and in every variant, since the
theorem statement is fixed). It is what keeps the obligation an obligation about
BEHAVIOR rather than syntax: an implementation that sequences the same single
action differently (`renderContents >>= pure`, `pure () >>= fun _ => …`) is
provably the same action and verifies, while one that carries the action out a
different NUMBER of times, or on the wrong branch, does not. That the hypothesis
is load-bearing rather than decorative was measured, not asserted: with
`[LawfulMonad m]` deleted from `correct_render`, the shipped proof no longer
closes, and neither do the two behavioural positives in `properties.py`
(`pos-shown-discarded-result`, `pos-lawful-resequence`), while the three
control-flow positives — which reduce to the shipped action — still do.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Lean type | Python reality | bijection |
|---|---|---|
| `Drawable` (`{ visible : Bool }`) | the `Axes3D` instance, projected to its visibility flag | `self.get_visible()` ↔ `Drawable.visible` (`True↔true`, `False↔false`) |
| `m Unit` (arbitrary lawful monad) | a drawing effect on `renderer`, returning `None` | an action; equality of actions ↔ same drawing performed |
| `renderContents : m Unit` | running the unchanged remainder of `draw(renderer)` | emits the operations the unchanged body emits |
| `pure () : m Unit` | returning without touching `renderer` | emits nothing |

For any mechanical check that needs to EXECUTE an action, `m` is instantiated at
the lawful monad `StateM (List RenderOp)` — state over the log of primitive draw
operations accumulated on the renderer — with `pure ()` the identity on the log
and `renderContents` an append. This instance is what `conformance_check.py`
runs; nothing in the spec depends on it, since the spec quantifies over all
lawful `m`.

## Callee provenance + flag deps

- `Axes3D.get_visible()` — UNCHANGED callee (inherited `Artist.get_visible`); returns
  the boolean `self._visible`. Pure read, no flag dependency. Modeled directly as the
  `Drawable.visible` field rather than an opaque callee, since its value IS the branch
  input.
- `renderContents` — A-REFERENCE for the unchanged body of `draw`. A universally
  quantified PARAMETER of both the specification and the implementation rather than an
  `opaque` constant, and **no `_prop` axiom is asserted on it**: the specification
  consumes no property of it, only its identity as the action the shown case must
  perform. A parameter is the stronger of the two forms here — an `opaque` constant
  admits whatever definitional unfolding the ambient theory allows, whereas a
  parameter admits none, which is exactly the write-only renderer being modeled.
- The bundle declares no `axiom` and no `opaque` (`meta.json: axioms: []`).

## G-CONF fuzz seed

Pinned seed: `23314`. Fuzz domain: `visible ∈ {True, False}` × arbitrary prior
operation logs (length 0..8 of opaque tokens) × the deterministic
`renderContents` surrogate action. The only R-modeled logic is the visibility
guard; `renderContents` is held as the A-tagged callee on both legs, and the
hidden case is checked as "the log is untouched element for element", the
executable reading of `result = pure ()`.
