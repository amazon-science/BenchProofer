# mapping.md — matplotlib__matplotlib-22865

## Symbol binding (file:line @ base_commit c6c7ec1978c22ae2c704555a873d0ec6e1e2eaa8)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_colorbarEdgeSegments` | `Colorbar._add_solids` (the `dividers.set_segments(...)` decision) | `lib/matplotlib/colorbar.py:651-660` |
| `problem_spec_colorbarEdgeSegments` | the segment list handed to `self.dividers.set_segments(...)` | `lib/matplotlib/colorbar.py:658-660` |
| arg `drawEdges : Bool` | `self.drawedges` | `lib/matplotlib/colorbar.py` (instance flag) |
| arg `extendLower : Bool` | `self._extend_lower()` | `lib/matplotlib/colorbar.py:1352-1355` |
| arg `extendUpper : Bool` | `self._extend_upper()` | `lib/matplotlib/colorbar.py:1357-1360` |
| arg `segs : List α` | `np.dstack([X, Y])` (rows along axis 0; `len == len(X)`) | `lib/matplotlib/colorbar.py:659` |
| result `List α` | the array passed to `set_segments` | — |

## Lean ↔ Python type bijection (used by G-CONF, G-AX)

- `np.dstack([X, Y])` is an array of shape `(len(X), 2, 2)`; the *slice* that the
  fix changed operates on **axis 0** only and never inspects element values. We
  therefore model the carrier as a generic `List α` of opaque rows; element type
  is irrelevant to the changed behavior. In the conformance bridge a row is an
  `int` (a stand-in identity for a `dstack` row).
- Python slice `seq[a:b]` ↔ `(seq.take b).drop a` (with `b = len` for the
  open-upper case, `b = len-1` for the `-1` case; `a ∈ {0,1}`).
- `self.drawedges`, `self._extend_lower()`, `self._extend_upper()` are `bool` ↔
  Lean `Bool`. These are **inputs** to the model: `_extend_lower`/`_extend_upper`
  are UNCHANGED callees whose return values gate the slice; the fix did not touch
  them, so we pass their results in rather than axiomatize them.

## Callee provenance + flag deps

- `_extend_lower()` / `_extend_upper()` (colorbar.py:1352/1357): unchanged;
  return `self.extend in ('both', 'min'/'max')` (modulo axis inversion). Lifted to
  the boolean inputs `extendLower`/`extendUpper`. NOT axiomatized (not called as an
  opaque op inside the model — their *results* are the inputs).
- `np.dstack([X, Y])`: unchanged; produces the per-edge segment rows. Modeled as
  the input list `segs` (an A-reference at the data level — identity carrier; G-CONF
  treats it as identity, no behavioral claim).
- `dividers.set_segments`: unchanged sink; the model's *result* is exactly its
  argument. No behavioral claim.
- Flag dependency: the discriminating configuration is `drawEdges = true` with
  `extendLower`/`extendUpper` toggled — covered exhaustively (3 bools) plus fuzzed
  segment lengths in conformance_check.py.

## No opaque callees / no consumed axioms

The changed op is a pure index-and-slice computation over the input list; it is
modeled deeply (`take`/`drop`). There are therefore **no** `opaque` callee decls
and **no** `_prop` axioms. axiom_check.py is a skip stub (G-AX skip).

## G-CONF fuzz seed

Pinned seed: `20220422` (issue date). ≥10⁵ fuzzed `(drawEdges, extendLower,
extendUpper, len(segs))` tuples; see conformance_check.py.
