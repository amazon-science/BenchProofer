# mapping.md — matplotlib__matplotlib-24177

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 493d608e39d32a67173c23a7bbc47d6bfedcef61`, states the type
abstraction, and gives the provenance of the axiomatized callee (source + the
exact behaviour the axiom encodes).

Repo file under change: `lib/matplotlib/axes/_base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `enclosing_upper_bound(verts)` | `Axes._update_patch_limits(self, patch)` — `lib/matplotlib/axes/_base.py:2420` (the changed gather loop at `:2437`, the extent fed to `update_datalim` at `:2457`) | the modeled changed function: the vertex gather whose extent must enclose the path |
| `seq_max(s)` *(deep model — A-reference)* | the per-axis maximum of the gathered vertices that `update_datalim`/`Bbox.update_from_data_xy` forms into the data-limit extent (`lib/matplotlib/axes/_base.py:2457`; `lib/matplotlib/transforms.py` Bbox) | pure spec: largest coordinate over the gathered sequence; the upper end of the enclosing extent. Validated `== max(full gather)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `subsel_len(verts)`, `subsel_at(verts, idx)` *(axiom — A-consumed by the prepatch)* | `Path.iter_bezier(**kwargs)` with the default `simplify=None` — `lib/matplotlib/path.py:420`, which forwards to `Path.iter_segments` (`:354`) → `Path.cleaned(..., simplify=...)` (`:467`) → `_path.cleanup_path` (C extension) | the appearance-preserving path condensation the PRE-patch gather iterates; unchanged callee. The axiom encodes only its weakest sound property: membership (every retained value occurs among the path vertices) and `0 <= count <= len` |

The single edit (`patch.diff`): at `_base.py:2437` the gather changes from
`for curve, code in p.iter_bezier():` to
`for curve, code in p.iter_bezier(simplify=False):`. Passing `simplify=False`
disables the condensation, so the gather visits EVERY path vertex; the default
`simplify=None` lets `Path.cleaned` apply `should_simplify` (True for a long
MOVETO/LINETO path: `path.py:202-207`, `len(vertices) >= 128` and all codes
≤ LINETO), which drops interior vertices and can omit the extremes.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the gathered vertices' per-axis coordinate values (`np.ndarray` of `float`, one axis at a time) | `List[int]` (`verts`), specified over `PSeq[int]` via `ToSeq` | `verts[k]` ↔ the k-th gathered coordinate on one axis; `len(verts)` ↔ the gather count. The TESTED behaviour is WHICH vertices are gathered (inclusion of the extreme-bearing vertex), not floating-point precision, so integer coordinates are a faithful carrier (refinement.md A2). |
| the data-limit extent's upper end (max of the gathered x or y), fed to `update_datalim` (`_base.py:2457`) and ultimately to `ax.get_{x,y}lim()` | `seq_max(ToSeq(verts))` and the `Result()` of `enclosing_upper_bound` | the autoscaled limit ≥ every datum ⇔ `Result() >= verts[k]` for all k, AND the limit is attained ⇔ `Result() == verts[j]` for some j (the extent is the max OF the gathered data, never a padded value). The F2P test asserts `get_xlim()[1] >= maxx`, `get_ylim()[1] >= maxy` (and the symmetric lower bounds); the attained clause additionally excludes a `max+padding` over-approximation (SPEC_GUIDE directive 8). |
| iterating Bézier curves and sampling each at `[0, *dzeros, 1]` (`_base.py:2438-2441`) | gathering the vertex sequence directly | for a step-histogram outline every segment is a MOVETO/LINETO (degree ≤ 1), so `axis_aligned_extrema` is empty (`bezier.py:275-279`) and `curve([0,1])` returns the segment endpoints — the gathered points ARE the path vertices. The model abstracts the gather to "the sequence of vertex coordinates" (axiom_check.py validates this). |

`str`/array indexing is banned in Nagini, so the carrier is `List[int]`; the
specification is phrased over `PSeq[int]` via `ToSeq`. Only the upper-bound
(maximum) direction is modeled; the lower bound is symmetric (negate), so a
single modeled clause discriminates the bug without redundancy.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `seq_max` deep model ↔ the gathered-vertex maximum (A-reference)
The enclosing extent is the maximum coordinate over the gathered vertices. The
changed gather is modeled **deeply**: `seq_max` (the front-recursive `@Pure`
fold) and the verified loop in `enclosing_upper_bound` ARE that maximum, the
dominance lemma `lemma_seq_max_dominates` proves it bounds every gathered
element (enclosing), and `lemma_seq_max_attained` proves it equals one gathered
element (tightness — a max/min IS attained at some vertex). There is **no
consumed axiom** for the maximum. G-AX validates the deep model out-of-band:
`axiom_check.py` runs the real `Path.iter_bezier(simplify=False)` gather
(exactly as `_update_patch_limits` does) and asserts that the gathered max ≥ the
maximum coordinate of EVERY path vertex (and min ≤ every vertex) — the enclosing
property `enclosing_upper_bound` proves. (The attained clause is a structural
property of a max/min and needs no separate in-container check.)

### 3.2 `subsel_len` / `subsel_at` ↔ `Path.iter_bezier()` default (A-consumed)
**Callee:** `Path.iter_bezier(**kwargs)` (`path.py:420`) with the DEFAULT
`simplify=None`, forwarding to `iter_segments`→`cleaned`→`_path.cleanup_path`.
For a long MOVETO/LINETO path, `should_simplify` is True (`path.py:202-207`), so
the C routine `cleanup_path` produces an **appearance-preserving condensation**:
it DROPS interior vertices lying on near-collinear runs, keeping a SUBSET of the
original vertices. It never invents coordinate values. Docs:
https://matplotlib.org/stable/api/path_api.html#matplotlib.path.Path.iter_bezier
and `path.simplify` / `path.simplify_threshold` rcParams.

The axiom encodes only the obligations the PRE-patch gather relies on, and the
**weakest** ones that are sound:
- `subsel_len(verts) ∈ [0, len(verts)]` — a sub-selection never invents
  vertices (`cleanup_path` only drops).
- `subsel_at(verts, idx) == verts[j]` for some in-bounds `j` — every retained
  value already occurs among the path's vertices (MEMBERSHIP).

It deliberately promises **nothing** about preserving the extremes — because the
condensation legitimately does not (that omission is the regression). This is
why a gather over the condensation cannot prove the enclosing postcondition
(G-DIFF: `model_prepatch.py` fails on exactly that clause).

**Flag dependency:** the condensation only fires under the default `simplify=
None` together with `path.simplify=True`, `path.simplify_threshold>0`,
`len(vertices) >= 128`, and all codes ≤ LINETO (`path.py:202-207`). The fix
sidesteps it unconditionally by passing `simplify=False`. axiom_check.py builds
paths long enough to trigger `should_simplify` and pins this configuration.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`Path.iter_bezier(simplify=None)` and `iter_bezier(simplify=False)` gathers on
boundary outlines, the EXACT F2P regression fixture (`test_small_autoscale`, the
132-vertex array #24097), and 4000 randomized fuzz outlines. It asserts (a)
membership + count bound for the condensed gather (the A-consumed axioms), (b)
the full gather encloses every vertex (the A-reference deep model), and (c) the
discriminating witness: on the F2P fixture (`should_simplify` True) the
condensation's y-max is strictly below the true y-max (0.25 < 0.33) while the
full gather captures it (0.33). It imports only `matplotlib.path` /
`matplotlib.bezier` (the modules the gather uses) and `numpy`. Exit 0 iff sound
— confirmed rc 0 in-container (matplotlib 3.7.0.dev358+g3a7e550ebf at
base_commit).
