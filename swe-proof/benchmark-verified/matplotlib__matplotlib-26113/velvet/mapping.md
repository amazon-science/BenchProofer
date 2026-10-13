# mapping.md — matplotlib__matplotlib-26113

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5ca694b38d861c0e24cd8743753427dda839b90b`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `lib/matplotlib/axes/_axes.py` (the `Axes.hexbin`
method).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `accumulateBins (reduceBin) (minPop) (bins)` | the `accum = np.array([...])` list-comprehension in `Axes.hexbin`'s `C is not None` branch — `lib/matplotlib/axes/_axes.py:5016-5020` | the modeled changed computation (per-bin aggregate selection) |
| `binAggregate reduceBin minPop bin` | one comprehension element `reduce_C_function(acc) if len(acc) >= mincnt else np.nan` — `lib/matplotlib/axes/_axes.py:5017` (post-patch) | pure spec: the aggregate (or empty) emitted for one bin |
| `aggregateSeq reduceBin minPop bins` | the whole comprehension `[binAggregate(acc) for ... for acc in Cs_at_i[1:]]` | pure spec: the aggregate sequence for the bin list |
| `reduceBin : List Float → Float` *(free input)* | `reduce_C_function` — the `hexbin` parameter (`numpy.mean` by default) | FREE INPUT: the user-supplied bin-reducer; the spec makes no claim about it |
| `minPop : Nat` *(free input)* | `mincnt` AFTER the `if mincnt is None: mincnt = 0` normalization (`lib/matplotlib/axes/_axes.py:5014-5015`) | FREE INPUT: the minimum bin population to aggregate |
| `bins : List (List Float)` *(free input)* | `[acc for Cs_at_i in [Cs_at_i1, Cs_at_i2] for acc in Cs_at_i[1:]]` — the per-hexagon C-value lists with index-0 (out-of-range) dropped (`lib/matplotlib/axes/_axes.py:5018-5019`) | FREE INPUT: the per-bin C-value populations |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a per-hexagon C-value list `acc` (`list`/`np.ndarray` of float) | `List Float` | `acc` ↔ `acc`-shaped `List Float`; `len(acc)` ↔ `bin.length` |
| the bin sequence `[acc for ... for acc in Cs_at_i[1:]]` (Python list of lists) | `List (List Float)` | element-wise + order-preserving; the `[1:]` drop and the two-group concatenation are UNCHANGED by the patch and produce this list, folded into the free input `bins` (§3) |
| `mincnt` (an `int`, `None`-normalized to `0`) | `Nat` | `mincnt` (a non-negative bin count) ↔ `minPop` |
| `reduce_C_function` (callable `array -> float`) | `List Float → Float` | the free function input; G-CONF instantiates it with concrete callables (sum/len/max/mean) |
| `np.nan` (bin not aggregated → dropped downstream by `~np.isnan(accum)`) | `Option.none` | `np.nan` ↔ `none`; a real aggregate float `x` ↔ `some x` |
| an aggregate value `reduce_C_function(acc)` (a `float`) | `Float` inside `some` | order-only / value identity; the F2P test only observes WHICH bins are present (non-NaN), so the carrier is order-faithful |

The choice carrier is `List` because the operation is per-bin and order-/
length-sensitive; `Option Float` is the faithful model of "a bin either yields a
real aggregate or is marked empty (NaN)", and downstream matplotlib selects the
non-empty bins via `good_idxs = ~np.isnan(accum)`.

## 3. Callee / free-input provenance

### 3.1 `reduceBin` — the bin reducer (FREE INPUT, no axiom)
`reduce_C_function` is a user-supplied callable (`numpy.mean` by default,
`numpy.sum`/`numpy.amax`/`len`/`lambda v: sum(v)` in tests). The patch does NOT
change it and does NOT change WHICH bins it is applied to in a way that depends
on its value — it only changes the population THRESHOLD that decides whether a
bin is reduced at all. So `reduceBin` is taken as a free input: the spec holds
for EVERY reducer, and there is no behavioural claim to check against a real
callee. Hence **no axiom and no G-AX** (analogous to django-11149's
`userHasPerm`). G-CONF still instantiates it with several concrete reducers to
exercise the R/I refinement.

### 3.2 `bins` — the per-bin populations (FREE INPUT)
The bin populations come from the binning/`[1:]`-drop/concatenation code ABOVE
the patched line (`Cs_at_i1`, `Cs_at_i2` filled by the `for i in range(len(x))`
loop; `Cs_at_i[1:]` drops the out-of-range index-0 bin). That code is UNCHANGED
by the patch (pre- and post-patch run it identically) and only determines WHICH
populations exist, not the selection rule under change. It is folded into the
free input `bins`. G-CONF fuzzes `bins` directly with random lists of random
float lists, covering empty bins, boundary-population bins (`len == minPop`),
and over-/under-population bins.

### 3.3 The single changed operation — the threshold comparison
The ONLY thing the patch changes is the comparison `len(acc) > mincnt` →
`len(acc) >= mincnt` (`lib/matplotlib/axes/_axes.py:5017`). This is modeled
DEEPLY and concretely by `binAggregate`'s `bin.length ≥ minPop` guard (an I/R
op, not an axiom). The discriminating input is a bin whose population EQUALS
`minPop`: post-patch it is aggregated (`some`), pre-patch it is dropped
(`none`).

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`26113`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`binAggregate`/`aggregateSeq` (R/I-tagged ops) to Python; there are no A-tagged
callees (the reducer and populations are free inputs supplied by the harness),
so `conf_skip=false`.
