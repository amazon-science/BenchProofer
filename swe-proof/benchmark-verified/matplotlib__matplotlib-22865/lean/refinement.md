# refinement.md — matplotlib__matplotlib-22865

Maps every op in `implementation_colorbarEdgeSegments` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed**, **A-reference**,
**I** (identical concrete op).

| # | Lean impl op | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `if !drawEdges then return []` | `else: self.dividers.set_segments([])` | I | the disabled branch yields the empty selection |
| 2 | `let startIdx := if openLower then 0 else 1` | `start_idx = 0 if self._extend_lower() else 1` | R | `self._extend_lower()` (unchanged callee) lifted to the boolean input `openLower`; literal 0/1 identical |
| 3 | `let endIdx := if openUpper then segs.length else segs.length - 1` | `end_idx = len(X) if self._extend_upper() else -1` | R | `self._extend_upper()` lifted to `openUpper`; `len(X)` ↔ `segs.length`; Python `-1` (one-before-end) ↔ `segs.length - 1` as an absolute upper bound |
| 4 | `return (segs.take endIdx).drop startIdx` | `self.dividers.set_segments(np.dstack([X, Y])[start_idx:end_idx])` | R | `np.dstack([X, Y])` ↔ input `segs` (identity carrier of rows along axis 0); Python slice `seq[a:b]` ↔ `(seq.take b).drop a`; `set_segments` sink ↔ returning the list |

## Notes on the R legs

- **Slice ↔ take/drop.** Python `seq[a:b]` with `0 ≤ a ≤ b ≤ len` equals
  `(seq.take b).drop a`. The fix uses `a ∈ {0,1}` and `b ∈ {len, len-1}`, so
  `a ≤ b` holds whenever `len ≥ 1`; for `len = 0` both the patched numpy slice
  (`[..:-1]` on an empty array) and Lean `take`/`drop` (which clamp) yield the
  empty list. The `-1` → `len-1` rewrite reproduces numpy's "one before the end"
  semantics as an absolute index because the carrier is finite and indexed from
  the front. All of this is mechanically refuted by G-CONF over ≥10⁵ inputs,
  including `len ∈ {0,1,2}` and every `(drawEdges, openLower, openUpper)` combo —
  0 disagreements.
- **`_extend_lower()` / `_extend_upper()` are NOT axiomatized.** They are
  unchanged callees, but the fix consumes only their *boolean results* to gate
  the slice; those results are the model's inputs. No `opaque`/`axiom` is needed
  (no callee is invoked as an op inside the model), so there are no A-consumed or
  A-reference rows and axiom_check.py is a G-AX skip stub.

No changed op is left inexpressible; every op is I or a declared R bijection.
