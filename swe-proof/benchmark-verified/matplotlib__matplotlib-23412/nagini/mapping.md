# mapping.md — matplotlib__matplotlib-23412

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f06c2c3abdaf4b90285ce5ca7fedbb8ace715911`, states the type
abstraction, and records callee provenance.

Repo file under change: `lib/matplotlib/patches.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_dash_pattern(phase, onoff)` | `Patch.draw(self, renderer)` — `lib/matplotlib/patches.py:585` (the `cbook._setattr_cm(self, _dash_pattern=...)` site, body lines 589-591) | the modeled changed function: it constructs the dash pattern that is in effect for the duration of the draw and is handed to the renderer |
| `phase` parameter | `self._dash_pattern[0]` — the scalar dash offset of the patch's (scaled) dash pattern (`patches.py:88`, set by `set_linewidth`/`set_linestyle` via `mlines._scale_dashes`, `patches.py:394,429`) | the stored dash offset |
| `onoff` parameter | `self._dash_pattern[1]` — the on/off ink-length sequence of the patch's (scaled) dash pattern | the stored dash on/off sequence |
| `Result()` (a `List[int]`) | the `_dash_pattern` tuple temporarily installed by `cbook._setattr_cm` for the body of `draw`, subsequently consumed by `gc.set_dashes(*self._dash_pattern)` (`patches.py:552`, reached through `self._bind_draw_path_function(renderer)`) | the dash pattern actually handed to the drawing back end |

The change is the single expression that builds the `_dash_pattern` value passed
to `cbook._setattr_cm`:

```
- _dash_pattern=(0, self._dash_pattern[1])       # pre-patch: offset forced to 0
+ _dash_pattern=(self._dash_pattern)             # post-patch: offset preserved
```

`(self._dash_pattern)` is just `self._dash_pattern` (the parenthesis is not a
tuple) — i.e. `(self._dash_pattern[0], self._dash_pattern[1])`, the patch's own
offset and on/off sequence unchanged.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self._dash_pattern` — a 2-tuple `(offset, onoffseq)` | the pair `(phase, onoff)` plus the result `List[int]` whose head is the rendered offset and whose tail is the rendered on/off sequence | tuple component 0 (offset) ↔ `phase` / `Result()[0]`; tuple component 1 (`onoffseq`, an even-length sequence) ↔ `onoff` / `Result()[1:]` |
| `offset` — a scaled `float` (`offset * lw`, `lines.py:65`) | `int` | The tested behaviour is solely *whether the stored offset is carried through to the renderer unchanged versus dropped to zero*. That property is a discrete value-vs-zero distinction, independent of the offset's floating-point magnitude or scaling; an exact integer carrier therefore faithfully exhibits the same observable (offset preserved ⇔ `Result()[0] == phase`; offset dropped ⇔ `Result()[0] == 0`). The F2P test (`test_dash_offset_patch_draw`) compares a patch with offset `6` against an offset-`0` patch with an on/off sequence rearranged to be visually equivalent — i.e. it tests that a nonzero offset has the rendering effect of a phase shift, which holds iff the offset is passed through. No precision is involved; `--float-encoding` is NOT used. |
| `onoffseq` — a sequence of scaled `float`s (or `None` for a solid line) | `List[int]` | element-wise; an empty `onoff` models both the empty/solid case and is the degenerate boundary. The behaviour under spec (offset passthrough) is uniform over the on/off sequence, which is copied verbatim in both pre- and post-patch code, so its element type is immaterial to the discriminator. |

## 3. Callee provenance

None. The changed expression is pure tuple construction from values already
held on the patch (`self._dash_pattern[0]`, `self._dash_pattern[1]`). It calls
no library/utility function, so there is **no `@ContractOnly` axiom** and **no
A-reference deep model** — and therefore no `axiom_check.py` is required for this
bundle (there is nothing for G-AX to execute against a real callee).

`cbook._setattr_cm` (the context manager that installs the value) and
`gc.set_dashes` (the back-end consumer) are unchanged by the patch and are not
part of the modeled construction; they merely transport the constructed
`_dash_pattern` value to the renderer. The modeled function is exactly the
value-construction the patch edits.
