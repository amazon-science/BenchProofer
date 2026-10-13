# mapping.md — symbol binding & type bijection (matplotlib__matplotlib-25311)

## Symbol binding (file:line @ base_commit)

- `DraggableBase.__init__` — `lib/matplotlib/offsetbox.py:1503-1515` @ base_commit.
  Modeled by `initHandlerState` (the persisted instance state it builds).
  Changed line removed: `self.canvas = self.ref_artist.figure.canvas`
  (was line 1508).
- `DraggableBase.canvas` (new class-level property) —
  `lib/matplotlib/offsetbox.py:1517-1518` @ post-patch
  (`canvas = property(lambda self: self.ref_artist.figure.canvas)`).
  Modeled by `accessDisplayHandle`.

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)

| Python | Lean | note |
|---|---|---|
| an attribute retained in `self.__dict__` | `Attr` | `flag`/`serial`/`liveHandle` cases |
| a serializable datum (object ref, list of picklable cids) | `Attr.serial` | identity of value irrelevant to picklability |
| a `bool` instance attribute | `Attr.flag (b : Bool)` | `got_artist`, `_use_blit` |
| a live backend canvas handle stored in state | `Attr.liveHandle` | the non-serializable object; pre-patch only |
| `use_blit and self.canvas.supports_blit` | `useBlit && blitSupported` | both flags fuzzed |
| pickle-able(state) | `stateSerializable : List Attr → Prop` | `∀ a ∈ st, a ≠ liveHandle` |
| the owning figure's current canvas | `Container.displayHandle : Nat` | object identity ↦ a `Nat` tag |
| `self.ref_artist.figure.canvas` (property body) | `owner.displayHandle` | recomputed per access |

## Callee provenance + flag deps

- No UNCHANGED callee is abstracted behind an axiom or deep-model reference.
  `ref_artist.figure.canvas`, `canvas.supports_blit`, and
  `callbacks._connect_picklable` are not modeled at the value level; only their
  *picklability contribution* to the persisted state is modeled (serial vs live
  handle), which is reproduced concretely. Hence `axioms` region is empty and
  G-AX is a skip stub.
- Flag dependency: the effective fast-redraw flag is `use_blit AND
  supports_blit`; `conformance_check.py` fuzzes all four `(use_blit,
  supports_blit)` combinations plus 120k random draws.

## G-CONF fuzz seed

Pinned seed = **25311** (`conformance_check.py` `SEED`).
