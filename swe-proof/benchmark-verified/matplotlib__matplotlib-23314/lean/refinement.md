# refinement.md — matplotlib__matplotlib-23314

Maps every op in `implementation_render` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom property),
**A-reference** (deep/opaque model validated == real callee by G-AX), **I**
(identical concrete op).

`implementation_render : m Unit` denotes the ACTION `Axes3D.draw` carries out;
`draw` returns `None`, so there is no return value to map — an op below is a step
of that action, and "the same op" means the same drawing performed.

| # | `implementation_render` op | `patch.diff` counterpart | tag | note |
|---|---|---|---|---|
| 1 | `if !self.visible then return` | `if not self.get_visible():` + `return` (the two added lines) | R | The behavior under specification. `self.get_visible()` (Python bool) ↔ `self.visible` (Lean `Bool`); `not` ↔ `!`. The Lean early `return` is `pure ()` — the action that performs no drawing — ↔ Python bare `return`, which leaves `draw` having drawn nothing. |
| 2 | `renderContents` | the entire pre-existing body of `draw` (lines `self._unstale_viewLim()` … `super().draw(renderer)`) | A-reference | The unchanged remainder of `draw`, bundled into ONE action and taken as a universally quantified parameter. No `_prop` axiom is consumed; the spec fixes only that the shown case performs this action. G-AX has no property to validate (see meta.json: G-AX skip). |

No changed op is inexpressible. The single changed behavior — perform no drawing
when hidden — is modeled exactly by op #1 (an R refinement). The unchanged body
(op #2) is held abstract and contributes no proof obligation.

## What "carried out" means at the Lean level

The obligation is an equation between ACTIONS in an arbitrary lawful monad, so the
correspondence with Python is at the level of what runs, not of a value that comes
back:

- `result = pure ()` (hidden) holds of a Lean implementation only if that
  implementation never sequences `renderContents`. Sequencing it and then trying to
  get back to `pure ()` requires proving `renderContents >>= f = pure ()` for an
  arbitrary action, which is false; and the abstract `m` supplies no other
  operation — no read-back, no undo — with which to erase it. This is the faithful
  reading of a write-only renderer: Python `draw` likewise has no way to un-emit
  what it has emitted.
- `result = renderContents` (shown) holds only if the implementation performs that
  action exactly once. Performing it twice is not provably equal to performing it
  once for an arbitrary action, which matches the reality that drawing the contents
  twice is a different figure.
- The one Lean phrasing that verifies without performing the action is binding it
  as a VALUE and discarding it (`let _ := renderContents`), which is not a call.
  Its Python counterpart is naming the bound method without invoking it, and that
  leaves `draw` having drawn nothing — the behavior the hidden case requires. So
  the residual admits no counterpart that draws.

## Soundness check
- The R leg (op #1) is mechanically differential-tested by G-CONF at the concrete
  instance `m := StateM (List RenderOp)`: for every `visible`, the action leaves the
  operation log untouched element for element iff `visible = false`, and appends the
  surrogate body's operations exactly once iff `visible = true`, matching the patch's
  early-return guard.
- No A-consumed axioms ⇒ G-AX has nothing to validate (skip stub). The bundle
  declares no `axiom` and no `opaque`.
- G-DIFF: the prepatch drops op #1, so its action is `renderContents`
  unconditionally, and `correct_render`'s first conjunct
  (`visible = false → result = pure ()`) becomes unprovable — exactly the reported
  behavior, an invisible 3D axes that still draws itself.
