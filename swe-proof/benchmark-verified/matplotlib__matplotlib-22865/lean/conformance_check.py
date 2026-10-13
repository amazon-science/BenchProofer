#!/usr/bin/env python3
"""G-CONF for matplotlib__matplotlib-22865.

The changed behavior is the choice of which separator rows of `np.dstack([X, Y])`
are handed to `dividers.set_segments(...)`. The gold patch replaces the fixed
`[1:-1]`-when-drawedges slice with:

    if self.drawedges:
        start_idx = 0 if self._extend_lower() else 1
        end_idx   = len(X) if self._extend_upper() else -1
        self.dividers.set_segments(np.dstack([X, Y])[start_idx:end_idx])
    else:
        self.dividers.set_segments([])

We differential-test the R/I Python shadow of
`implementation_colorbarEdgeSegments` (the Lean impl, transliterated op-for-op
per refinement.md) against the REAL patched slice expression, evaluated with
real numpy arrays, over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Type bijection (mapping.md):
  drawEdges  : Bool          <->  self.drawedges
  openLower  : Bool          <->  self._extend_lower()  (lower end open)
  openUpper  : Bool          <->  self._extend_upper()  (upper end open)
  segs       : List a        <->  np.dstack([X, Y])  (rows along axis 0)
  result     : List a        <->  the array passed to set_segments

Rows carry their original index so the selected sub-sequence is recoverable:
X[i] = Y[i] = [i, i], so dstack row i has row[0][0] == i.

stdlib-only besides numpy (a hard matplotlib dependency, present in-container).
"""
import random
import sys

import numpy as np


def oracle(draw_edges, open_lower, open_upper, n):
    """Real patched slice, evaluated with real numpy arrays.

    Returns the list of original row indices selected for set_segments.
    """
    # X, Y encode the row index so the selection is recoverable.
    X = np.array([[i, i] for i in range(n)], dtype=float) if n else np.empty((0, 2))
    Y = np.array([[i, i] for i in range(n)], dtype=float) if n else np.empty((0, 2))
    if draw_edges:
        start_idx = 0 if open_lower else 1
        end_idx = len(X) if open_upper else -1
        segments = np.dstack([X, Y])[start_idx:end_idx]
    else:
        segments = []
    return [int(round(row[0][0])) for row in segments]


def shadow(draw_edges, open_lower, open_upper, n):
    """R/I transliteration of implementation_colorbarEdgeSegments (Lean).

    segs := list(range(n))  (the row-index carrier)
    """
    segs = list(range(n))
    if not draw_edges:                       # if !drawEdges then return []
        return []
    start_idx = 0 if open_lower else 1       # if openLower then 0 else 1
    end_idx = n if open_upper else n - 1     # if openUpper then len else len-1
    # (segs.take end_idx).drop start_idx ; Lean take/drop clamp at 0/len.
    end_idx = max(0, end_idx)
    return segs[:end_idx][start_idx:]


def main():
    rng = random.Random(20220422)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        draw_edges = rng.random() < 0.5
        open_lower = rng.random() < 0.5
        open_upper = rng.random() < 0.5
        # cover empty / singleton boundaries plus larger meshes
        if rng.random() < 0.25:
            n = rng.randint(0, 2)
        else:
            n = rng.randint(0, 40)
        o = oracle(draw_edges, open_lower, open_upper, n)
        s = shadow(draw_edges, open_lower, open_upper, n)
        if o != s:
            disagreements += 1
            if first is None:
                first = (draw_edges, open_lower, open_upper, n, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
