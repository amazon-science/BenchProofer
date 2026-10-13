# mapping.md — matplotlib__matplotlib-22865

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c6c7ec1978c22ae2c704555a873d0ec6e1e2eaa8`, states the type
abstraction, and gives the provenance of the deep-model reference (the changed
slice-bound selection) that `axiom_check.py` (G-AX) validates.

Repo file under change: `lib/matplotlib/colorbar.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `drawn_separators(segments, lower_open, upper_open)` | the divider-segment selection inside `Colorbar._add_solids(self, X, Y, C)` — `lib/matplotlib/colorbar.py:634` (changed statement at body line 654-655) | the modeled changed behaviour: which contiguous run of candidate divider segments is drawn |
| `segments` (param) | `np.dstack([X, Y])` — the per-mesh-row candidate divider segments array (`colorbar.py:655`) | full ordered list of candidate separators (one per mesh row), length `n = len(X)` |
| `lower_open` (param) | `self._extend_lower()` — `colorbar.py:1352` | unchanged predicate: is the lower limit open ended |
| `upper_open` (param) | `self._extend_upper()` — `colorbar.py:1357` | unchanged predicate: is the upper limit open ended |
| `start_index(lower_open)` *(deep model — A-reference)* | `start_idx = 0 if self._extend_lower() else 1` (post-patch `colorbar.py`) | pure spec: first kept candidate index |
| `end_index(upper_open, n)` *(deep model — A-reference)* | `end_idx = len(X) if self._extend_upper() else -1` (post-patch) | pure spec: one-past-last kept candidate index |
| `Result()` | the array passed to `self.dividers.set_segments(...)` in the `drawedges` branch (`colorbar.py:655` pre-patch / the post-patch `np.dstack([X, Y])[start_idx:end_idx]`) | kept divider segments |

The pre-patch repo expression the change replaces (for the refinement audit,
not referenced from the consumer spec view): the unconditional slice
`np.dstack([X, Y])[1:-1]` guarded by `if self.drawedges` (`colorbar.py:654-655`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `np.dstack([X, Y])` — an `(n, 2, 2)` float array of candidate segments | `List[int]` of `n` distinct position ids | element `i` of the array is fully identified by its mesh-row position `y[i]` (each segment is `[[y[i], 0.], [y[i], 1.]]`); the model carries that identifying id as `segments[i]`. Basic first-axis slicing `arr[a:b]` ↔ list slice `segments[a:b]` ↔ the model copy loop over `[a, b)`. |
| `len(X)` (= `n`, the mesh-row count) | `len(segments)` | identical count |
| `self._extend_lower()` / `self._extend_upper()` (booleans) | `lower_open` / `upper_open` (bool params) | identical truth values; their internal derivation from `self.extend` + axis inversion is unchanged and irrelevant to the modeled selection |
| the `drawedges` guard (`if self.drawedges`) | omitted | the `drawedges=False` branch is unchanged (it always sets `[]`); the F2P tests all use `drawedges=True`, so the modeled behaviour is the `drawedges=True` branch only. The `else: []` branch is identical pre/post-patch (refinement.md C). |
| `self.dividers.set_segments(seq)` | `Result()` is `seq` | `set_segments` stores its argument; `cbar.dividers.get_segments()` (the F2P assertion) returns it back. Modeled as the identity on the segment sequence. |

`np.dstack` indexing is basic slicing along the first axis; the numeric content
of each segment is irrelevant to *which* segments are kept (the only changed
behaviour), so the carrier is `List[int]` of position ids.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `start_index` / `end_index` + slice loop ↔ the real slice-bound selection
**The changed operation is modeled DEEPLY**, not behind a consumed axiom: the
`@Pure` helpers `start_index` / `end_index` and the verified copy loop in
`drawn_separators` ARE the slice-bound selection. There is **no `@ContractOnly`
axiom the proof consumes**. The deep model is validated equal to the real
behaviour out-of-band by `axiom_check.py` (G-AX).

Post-patch repo expression (the gold hunk, `colorbar.py`):
```python
if self.drawedges:
    start_idx = 0 if self._extend_lower() else 1
    end_idx = len(X) if self._extend_upper() else -1
    self.dividers.set_segments(np.dstack([X, Y])[start_idx:end_idx])
else:
    self.dividers.set_segments([])
```

Mapping:
- `start_index(lower_open)` = `0 if lower_open else 1` == `start_idx`.
- `end_index(upper_open, n)` = `n if upper_open else n-1`. The real code
  uses `-1` for the not-open-ended upper case; for an array of length `n`,
  Python/numpy basic slicing treats `arr[start:-1]` identically to
  `arr[start:n-1]` (both drop exactly the last element). The model normalises
  to `n-1` so the kept count is an explicit non-negative integer.
- the copy loop materialises `segments[start:end]` == `np.dstack([X, Y])[start_idx:end_idx]`.

**The two predicates `_extend_lower` / `_extend_upper` are UNCHANGED** by the
patch; they are inputs to the selection. Their source (`colorbar.py:1352-1360`):
```python
def _extend_lower(self):
    minmax = "max" if self._long_axis().get_inverted() else "min"
    return self.extend in ('both', minmax)
def _extend_upper(self):
    minmax = "min" if self._long_axis().get_inverted() else "max"
    return self.extend in ('both', minmax)
```

**Soundness check (G-AX):** `axiom_check.py` reproduces `_extend_lower` /
`_extend_upper` verbatim and the real slice-bound selection, then asserts the
deep model (`start_index`/`end_index` + the slice loop) produces the identical
kept run on: the 4 canonical F2P configurations (`extend ∈
{both, min, max, neither}`, `bounds = arange(3)` ⇒ kept positions
`[0,1,2] / [0,1] / [1,2] / [1]`), all small sizes `n ∈ [2,8]` × 4 extends × 2
axis-inversions (56 exhaustive configs), and 20 000 randomized fuzz configs
(random `n`, distinct position ids, random extend + inversion). Exit 0 iff
sound. It imports only the standard library; the slicing it exercises is
exactly Python/numpy basic first-axis slicing. No consumed axiom exists to
over-claim.
