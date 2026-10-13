# mapping.md — matplotlib__matplotlib-13989

## Instance
- repo: matplotlib/matplotlib
- base_commit: a3e2897bfaf9eaac1d6649da535c4e721c89fa69
- changed function: `Axes.hist`
- file: `lib/matplotlib/axes/_axes.py`

## Symbol binding (file:line @ base_commit)

| Python symbol | location | role |
|---|---|---|
| `hist_kwargs = dict()` | `lib/matplotlib/axes/_axes.py:6654` | the keyword-argument mapping passed to `np.histogram`, initially empty |
| `hist_kwargs['range'] = bin_range` | `lib/matplotlib/axes/_axes.py:6685` | sets the `range` entry (only on the `else` branch — single/empty dataset path) |
| `hist_kwargs = dict(density=density)` | `lib/matplotlib/axes/_axes.py:6689` | **the changed line** (pre-patch / buggy): REBINDS the whole mapping to a fresh one carrying only `density`, discarding any `range` entry set above |
| `hist_kwargs['density'] = density` | gold patch | **the fix**: mutates the existing mapping in place, preserving a prior `range` entry |
| `np.histogram(x[i], bins, weights=w[i], **hist_kwargs)` | `lib/matplotlib/axes/_axes.py:6698` | the consumer; bin edges it returns depend on whether `range` survived in `hist_kwargs` |

## Behaviour modeled

The fix concerns the assembly of the `hist_kwargs` mapping, which has at most two
entries the patch context touches:

- a `range` entry, set iff the single/empty-dataset branch is taken
  (`not input_empty and len(x) > 1` is **false**); value is the resolved
  `bin_range` 2-tuple of floats;
- a `density` entry, set iff `density and not stacked`; value is the resolved
  `density` boolean (which is `True` whenever the branch is taken).

The two assignments are independent: setting the `density` entry must leave the
`range` entry exactly as it was. The pre-patch line rebinds the whole mapping and
therefore drops `range`, which is the reported bug (range ignored when
`density=True`).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `bool` flag deciding the `range` branch (`not (not input_empty and len(x) > 1)`) | `setRange : Bool` | identity |
| `bin_range` 2-tuple `(xmin, xmax)` of floats | `binRange : Rat × Rat` | tuple of exact rationals; value is only stored/passed through, never compared by magnitude, so any rational faithfully stands in for the float pair |
| resolved `density` bool (`bool(density) or bool(normed)`) | `densityFlag : Bool` | identity |
| `stacked` bool | `stacked : Bool` | identity |
| `hist_kwargs` dict with optional `'range'`/`'density'` keys | `HistKeywordArgs { range : Option (Rat × Rat), density : Option Bool }` | a missing key ↔ `none`; present key ↔ `some v` |

## Callee provenance + flag deps
None. The modeled behaviour is pure dictionary assembly (Python `dict` literal /
item assignment); no unchanged repo callee is consumed, so there are no `opaque`
declarations and no `axiom _prop` contracts. `np.histogram` is downstream of the
modeled boundary and is not part of the assembly logic, so it is not modeled.

## G-CONF fuzz seed
`seed = 13989` (pinned; used by conformance_check.py).
