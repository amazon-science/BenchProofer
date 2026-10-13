# mapping.md — matplotlib__matplotlib-23412

## Symbol binding (file:line @ base_commit f06c2c3abd)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_dashRender` / `problem_spec_dashRender` / `correct_dashRender` | `Patch.draw` — the dash stroke style temporarily applied while the patch outline is rendered | `lib/matplotlib/patches.py:584-601` @ base_commit (edited lines `589-591` of the hunk) |
| the produced `(offset, dashes)` / the in-draw pattern clause | `cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern))` (post-patch; pre-patch: `_dash_pattern=(0, self._dash_pattern[1])`) | `lib/matplotlib/patches.py:590-591` |
| `if !visible then return none` | `if not self.get_visible(): return` | `lib/matplotlib/patches.py:587-588` |

The modeled function is `Patch.draw`. The only behaviorally-relevant edit is the
dash pattern installed via `cbook._setattr_cm` for the duration of the draw:

```python
def draw(self, renderer):
    if not self.get_visible():
        return
    with cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern)), \   # POST-PATCH
         self._bind_draw_path_function(renderer) as draw_path:
        ...   # get_path / transform / draw_path -- unchanged
```

`self._dash_pattern` is the `(offset, dashes)` tuple computed by
`set_linestyle` / `set_linewidth` (via `mlines._get_dash_pattern` then
`mlines._scale_dashes`). The PRE-PATCH code replaced the offset with the constant
`0` (`(0, self._dash_pattern[1])`), so any user-supplied dash offset was silently
discarded at render time — that is the reported bug. The POST-PATCH code passes
the stored pattern through unchanged, honoring the offset.

The observable is the dash pattern handed to the graphics context during draw
(`gc.set_dashes(*self._dash_pattern)` in `Patch._draw_paths_with_artist_properties`,
called inside the same `with` block). The F2P test `test_dash_offset_patch_draw`
renders a `(6,[6,6])`-offset rectangle and asserts it matches the zero-offset
workaround `(0,[0,6,6,0])`; this holds only once the offset is applied.

## Modeled branch / configuration

`draw` has exactly two paths: the early `return` when `get_visible()` is false
(no stroke style), and the visible path that installs the dash pattern. Both are
modeled (`visible : Bool`). The dash pattern is always a `(offset, dashes)` tuple
where `dashes` is `None` for solid/None styles or a tuple of on/off lengths for a
dash tuple linestyle; `Option (List Int)` covers both.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.get_visible()` (bool) | `visible : Bool` | `True ↦ true`, `False ↦ false` |
| `self._dash_pattern[0]` (scaled offset, float) | `offset : Int` | G-CONF fuzzes integer offsets and integer linewidths so the scaled offset `offset*lw` is integral; `float v ↦ int(round(v))` |
| `self._dash_pattern[1]` (scaled on/off seq, tuple or None) | `dashes : Option (List Int)` | `None ↦ none`; tuple `(d0,d1,…) ↦ some [round d0, round d1, …]` |
| the in-draw applied pattern / `draw`'s effect | `result : Option (Int × Option (List Int))` | `none` when invisible; `some (offset, dashes)` when visible |

## Callee provenance + flag dependencies

- No callee axiom is consumed. The changed op (the `_dash_pattern` value passed
  to `cbook._setattr_cm`) is the operation the patch introduces, so it is modeled
  DEEPLY (an A-reference validated by G-CONF against real `Patch.draw`), never
  axiomatized (§0.7).
- `cbook._setattr_cm` (unchanged) is a temporary-attribute context manager; its
  only effect on the observable is to install the given pattern for the draw — so
  the modeled value IS the configured `(offset, dashes)`, reproduced concretely.
  No axiom needed.
- `mlines._get_dash_pattern` / `mlines._scale_dashes` (unchanged) compute
  `self._dash_pattern` from the linestyle; G-CONF feeds the Lean model the exact
  scaled pattern they produce, so they need no separate contract.
- No flag dependency: the offset is honored unconditionally in the post-patch
  code (independent of rcParams `lines.scale_dashes`, which only affects the
  magnitude of the scaled values, applied identically to both legs).

## G-CONF fuzz seed

`SEED = 20240629` (pinned in `conformance_check.py`).
