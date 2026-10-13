# refinement.md — operation correspondence (matplotlib__matplotlib-25311)

Stack: vanilla Lean 4 + Mathlib. Tags: **R** type refinement · **A-consumed**
proof uses axiom · **A-reference** deep model validated == real callee (G-AX) ·
**I** identical concrete op.

The gold patch makes two coordinated edits to `DraggableBase` in
`lib/matplotlib/offsetbox.py`:

1. `__init__` no longer executes `self.canvas = self.ref_artist.figure.canvas`
   — the persisted instance state stops retaining the (non-serializable) backend
   canvas handle, so the figure pickles.
2. A class-level `canvas = property(lambda self: self.ref_artist.figure.canvas)`
   restores `self.canvas` read access by recomputing it on each access.

## Function 1 — `initHandlerState` ↔ `DraggableBase.__init__` persisted state

| # | impl op (`implementation_initHandlerState`) | patch.diff counterpart | tag |
|---|---|---|---|
| 1 | `st := []` (start empty) | constructor begins with empty instance `__dict__` | I |
| 2 | `st ++ [Attr.serial]` (dragged object ref) | `self.ref_artist = ref_artist` retained | R (object ref ↦ `Attr.serial`) |
| 3 | `st ++ [Attr.flag false]` (drag-in-progress) | `self.got_artist = False` | R (Python `bool` ↦ `Attr.flag`) |
| 4 | `st ++ [Attr.flag (useBlit && blitSupported)]` | `self._use_blit = use_blit and self.canvas.supports_blit` | R (`bool` ↦ `Attr.flag`; `and` ↦ `&&`) |
| 5 | `st ++ [Attr.serial]` (callback ids) | `self.cids = [...]` (picklable connection ids) | R (id list ↦ `Attr.serial`) |
| — | (no `Attr.liveHandle` ever appended) | **removed line** `self.canvas = self.ref_artist.figure.canvas` is absent from persisted state | I (the deleted op = the bug; prepatch appends `Attr.liveHandle`) |

The `stateSerializable` conjunct in `problem_spec_initHandlerState` is the
abstract picklability property: serializable iff no `Attr.liveHandle` is
retained. The post-patch state has none ⇒ serializable; the pre-patch state
retains one ⇒ both the serializability conjunct AND the exact-list conjunct
fail, so `correct_initHandlerState` is unclosable on the prepatch (G-DIFF).

## Function 2 — `accessDisplayHandle` ↔ the `canvas` property

| # | impl op (`implementation_accessDisplayHandle`) | patch.diff counterpart | tag |
|---|---|---|---|
| 1 | `return owner.displayHandle` | `property(lambda self: self.ref_artist.figure.canvas)` — recompute the current canvas from the owning figure | R (figure/canvas object ↦ `Container.displayHandle : Nat` identity) |

The property dereferences the owner each call rather than reading a stored
snapshot; the spec pins the result to the owner's *current* handle. This leg has
no pre/post difference at the value level (read access is preserved), so its
prepatch proof closes — only function 1 discriminates the bug.

No changed op is inexpressible; nothing is axiomatized. `conf_skip=false`
(every op is R/I and is exercised by `conformance_check.py`).
