# mapping.md — matplotlib__matplotlib-24570

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8f0003ae902952372824c9917975fb372c026a42`, states the type
abstraction, and gives the provenance of the (single) deep-model reference.

Repo file under change: `lib/matplotlib/offsetbox.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `aligned_offsets(heights, descents, total, code)` | `_get_aligned_offsets(hd_list, height, align)` — `lib/matplotlib/offsetbox.py:130` | the modeled changed function (box alignment offsets); models its third return value `offsets` |
| `offset_for(h, d, total, code)` *(deep model — A-reference)* | the per-branch offset expression in `_get_aligned_offsets` (`offsetbox.py:164-177`) | pure spec: the per-box offset arithmetic for one anchor; the deeply-modeled changed operation, validated `== _get_aligned_offsets`'s offsets by axiom_check.py (G-AX), NOT consumed as an axiom |
| `CODE_BASELINE/CODE_LOWER/CODE_UPPER/CODE_CENTER` | the `align` string groups `"baseline"`, `{"left","bottom"}`, `{"right","top"}`, `"center"` (post-patch grouping; `offsetbox.py:164,169,172,175`) | pure spec: the six public anchor names collapsed to four offset-formula classes |

The two consumers that read the modeled output (not themselves changed):
`HPacker.get_extent_offsets` (`offsetbox.py:459`, calls `_get_aligned_offsets`
at line 478 with `self.align`) and `VPacker.get_extent_offsets`
(`offsetbox.py:418`, call at line 440). The F2P test `test_packers`
(`lib/matplotlib/tests/test_offsetbox.py`) drives both and asserts the per-box
offset each anchor produces.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `hd_list : list[(height, descent)]` of floats | two parallel `List[int]` `heights`, `descents` (`heights[i] == 2·h_i`, `descents[i] == 2·d_i`) | one `(h, d)` pair ↔ `(heights[i], descents[i])`; `len(hd_list)` ↔ `len(heights) == len(descents)` |
| `height` (total track height; `float` or `None`) | `total : int` (= `2·height`) | the helper sets `height = max(h)` when `None`; the F2P packers pass `self.height is None`, so `total` is the scaled `max(h)`. The slack term `height - h` ↔ `(total - heights[i])/2`. |
| `align : str` (one of six names) | `code : int` in `{0,1,2,3}` | `"baseline"→0`; `{"left","bottom"}→1`; `{"right","top"}→2`; `"center"→3` (the post-patch grouping). |
| `offsets : list[float]` (the returned per-box offset) | `Result() : List[int]` (= `2·offset`) | `offsets[i]` ↔ `Result()[i] / 2`; uniform ×2 positive scaling. |

**Why the ×2 scale (precision-independence).** The bug is not about floating
point precision — it is about *which* offset formula a given anchor selects.
Five of the six anchors yield integer offsets on integer inputs; only `center`
halves the slack (`(height - h) · 0.5`). Scaling every height/descent/offset by
2 makes the centre halving exact in integer arithmetic while preserving every
positional relationship (which anchor, and the low-edge vs high-edge contrast)
the alignment expresses and the test observes. `assert_allclose` in the F2P
test compares the genuine (un-scaled) float offsets; axiom_check.py undoes the
scale (`real_offset == model_offset / 2`) before comparing, so the deep model
is checked against the real float output, not a scaled surrogate.

`float` indexing/iteration over the helper's branch comprehensions is modeled
by the explicit per-element loop over `heights`/`descents`; `str` `align` is
banned in Nagini so it is refined to the integer `code`.

## 3. Deep-model provenance (the A-reference — checked by G-AX / axiom_check.py)

### 3.1 `offset_for` deep model ↔ `_get_aligned_offsets` offsets (A-reference)
**Callee:** the offset arithmetic inside `matplotlib.offsetbox._get_aligned_offsets`
**after** the patch. There is **no `@ContractOnly` axiom** the proof consumes;
the changed operation (the offset formula per anchor) is modeled **deeply** by
the `@Pure` `offset_for` (and the verified `aligned_offsets` loop). The deep
model is validated equal to the real callee out-of-band by axiom_check.py
(G-AX). Post-patch source (`offsetbox.py:164-179`):

```python
if align == "baseline":
    ...
    offsets = [0. for h, d in hd_list]
elif align in ["left", "bottom"]:
    descent = 0.
    offsets = [d for h, d in hd_list]
elif align in ["right", "top"]:
    descent = 0.
    offsets = [height - h + d for h, d in hd_list]
elif align == "center":
    descent = 0.
    offsets = [(height - h) * .5 + d for h, d in hd_list]
```

Under the §2 refinement this is exactly

  baseline → 0; {left,bottom} → d; {right,top} → (total−h)+d;
  center → (total−h)/2 + d,

which `offset_for` encodes (×2-scaled). The behavioural content the F2P test
observes is the contrast between the low-edge anchor group (offset = own
descent, independent of the track height) and the high-edge anchor group
(offset = track excess over the box + descent): the two differ exactly by the
box's slack `(total − h)`. The `descent`/`height` return values are unchanged
by the patch and irrelevant to the F2P discriminator, so the model pins the
`offsets` return only.

**Soundness check (G-AX):** `axiom_check.py` imports the real (post-patch)
`matplotlib.offsetbox._get_aligned_offsets`, runs it on boundary layouts
(including the F2P geometry `[(30,0),(60,0)]`, reversed order, single box,
equal heights, three boxes, nonzero descents, a zero-height box) and 20 000
randomized layouts, for all six anchors, and asserts every returned offset
equals `offset_for` (un-scaled). It calls the helper with `height=None`,
mirroring the packers' `self.height is None` call so the helper computes
`max(h)` itself. Imports only matplotlib (the repo under test) + stdlib;
exit 0 iff sound.
