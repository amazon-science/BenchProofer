# refinement.md — matplotlib__matplotlib-23412

Operation correspondence between `implementation_dashRender` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the changed operation (the in-`draw` dash
pattern passed to the renderer) is modeled DEEPLY as a verbatim carry-through of
the configured `(offset, dashes)` pair. Every row is **R**, **A-reference**, or
**I**. The R/I/A-reference legs are differential-tested by G-CONF; G-AX is a
skip stub (no consumed callee axiom).

## `implementation_dashRender` ↔ `Patch.draw`

The gold patch turns

```python
if not self.get_visible():
    return
# Patch has traditionally ignored the dashoffset.
with cbook._setattr_cm(
         self, _dash_pattern=(0, self._dash_pattern[1])), \      # PRE-PATCH
     self._bind_draw_path_function(renderer) as draw_path:
    ...
```

into

```python
if not self.get_visible():
    return

with cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern)), \  # POST-PATCH
     self._bind_draw_path_function(renderer) as draw_path:
    ...
```

i.e. the dash pattern temporarily installed for the duration of the draw is the
full stored `self._dash_pattern = (offset, dashes)` rather than `(0, dashes)`
(offset forced to zero). The surrounding visibility guard and the rest of the
draw body are unchanged.

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `if !visible then return none` | `if not self.get_visible(): return` | I | visibility short-circuit; no stroke style applied when invisible. `get_visible()` ↦ `visible : Bool` |
| `let used := (offset, dashes)` (then `return some used`) | `cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern))` — the EDITED op | A-reference | the temporarily-applied pattern carries the full configured `(offset, dashes)`; the offset is honored, not replaced by `0`. Modeled deeply as the identity carry-through; validated == real in-`draw` `self._dash_pattern` by G-CONF |
| `(offset, dashes)` pair | `self._dash_pattern` = `(offset, onoffseq)` (scaled) | R | the scaled dash pattern tuple ↦ `Int × Option (List Int)`; `None` on/off ↦ `none` |
| `return some used` | the pattern in effect through the `with` block (consumed by `draw_path` via `gc.set_dashes`) | R | the produced stroke style ↦ `some (offset, dashes)` |

The result is the precise observable the F2P test depends on: the dash offset
applied while the patch edge is stroked. With the pre-patch `(0, dashes)`, the
offset is silently dropped, so two rectangles with linestyles `(0,[6,6])` and
`(6,[6,6])` render identically (the reported bug); the F2P
`test_dash_offset_patch_draw` asserts that a `(6,[6,6])`-offset patch matches the
zero-offset equivalent `(0,[0,6,6,0])`, which only holds once the offset is
honored.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the in-draw pattern uses the constant `0` offset
  (`let used := (0, dashes)`) instead of the configured `offset`. The carried
  gold proof of `correct_dashRender` fails to close on the
  `visible = true → result = some (offset, dashes)` clause (the buggy impl yields
  `some (0, dashes)`, which differs whenever `offset ≠ 0`). This is the single
  fixed behavior.
  (FAIL_TO_PASS: `lib/matplotlib/tests/test_patches.py::test_dash_offset_patch_draw[png]`.)
