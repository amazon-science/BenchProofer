# mapping.md — matplotlib__matplotlib-26113

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5ca694b38d861c0e24cd8743753427dda839b90b`, states the type
abstraction, and gives the provenance of the deep-model reference.

Repo file under change: `lib/matplotlib/axes/_axes.py` (the `hexbin` method).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `populated_bins(occupancies, threshold)` | the `accum` list comprehension over per-hexagon value lists, `Axes.hexbin`, `lib/matplotlib/axes/_axes.py:5016-5020` (the `C is not None` branch) | the modeled changed code: the per-bin populated/cleared decision in the value-aggregation regime |
| `decision_agg(occ, t)` | `len(acc) >= mincnt` (post-patch) / `len(acc) > mincnt` (pre-patch), `_axes.py:5017` | pure spec: the per-bin populated decision in the value-aggregation regime |
| `decision_count(occ, t)` | the per-bin keep predicate of the bare-count regime, `accum[accum < mincnt] = np.nan` at `_axes.py:5002-5003` (a bin is populated iff `count >= mincnt`, i.e. iff `not (count < mincnt)`) | pure spec: the per-bin populated decision in the bare-count regime, used as the oracle the value-aggregation regime must match |

The per-bin decision is applied over the full list of bins by the index-wise
postcondition of `populated_bins` (`Forall(k: 0<=k<len ==> Result()[k] ==
decision_agg(occupancies[k], threshold) and Result()[k] ==
decision_count(occupancies[k], threshold))`), which models the whole `accum`
list comprehension `[reduce_C_function(acc) if len(acc) >= mincnt else np.nan
for ... for acc in Cs_at_i[1:]]` (`_axes.py:5016-5020`) reduced to its
populated/cleared pattern, and folds in the cross-regime consistency the F2P
test observes. *(deep model — A-reference, checked by G-AX.)*

The aggregated value `reduce_C_function(acc)` and the missing marker `np.nan`
are abstracted: only *whether a bin is populated* (a real value) versus
*cleared* (NaN, later dropped by `good_idxs = ~np.isnan(accum)` at
`_axes.py:5022`) is observable in the tested behaviour, so the model carries a
`bool` per bin instead of a `float`-or-NaN.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| one hexagon's accumulated C-value list `acc` (a Python `list`) | its occupancy `occ: int` | `occ == len(acc)`; on the modeled domain (`mincnt >= 1`, §2a) the decision depends on `acc` **only** through `len(acc)` (the comparison `len(acc) >= mincnt`; every kept bin is nonempty so its aggregate is a real value), so the list is faithfully abstracted by its length |
| the per-bin `mincnt` threshold, a **positive** `int` (the docstring documents `mincnt : int > 0`, `_axes.py:4850-4852`) | `threshold: int` with `Requires(threshold >= 1)` | identity on the positive integer threshold; the unset default (`None` → `0` at `_axes.py:5014-5015`) is **outside the modeled boundary** (§2a) |
| the full sequence of per-hexagon lists `[acc for ... for acc in Cs_at_i[1:]]` | `occupancies: List[int]` of their lengths | elementwise `occupancies[k] == len(acc_k)`; `len(occupancies)` ↔ number of in-range bins; specification carried by `PSeq[int]` via `ToSeq` |
| `accum` entry `reduce_C_function(acc)` (a real `float`) vs `np.nan` | `bool` populated-flag: `True` ↔ a real reduced value, `False` ↔ `np.nan` | the only observable per the F2P test is which bins survive `~np.isnan(accum)`; a populated bin (real value) ↔ `True`, a cleared bin (NaN) ↔ `False` — a faithful abstraction on the modeled domain because a nonempty finite-payload bin's aggregate is never NaN (§2a) |

No floats are modeled: the changed operation is an integer comparison
(`len(acc)` vs `mincnt`); on the modeled domain the reduced value is an opaque
passthrough whose numeric content is irrelevant to the populated/cleared
decision the test observes. `float_encoding` is therefore `null`.

### 2a. Modeled domain boundary: `threshold >= 1` (why `mincnt = 0` is excluded)

The model's precondition `Requires(threshold >= 1)` pins the modeled domain to
the **documented positive-threshold regime**: the library's docstring specifies
`mincnt : int > 0` (`_axes.py:4850-4852`), and the F2P test
`test_hexbin_mincnt_behavior_upon_C_parameter[png]` observes `mincnt=1`.

At `mincnt = 0` (the resolved unset default) the occupancy-only abstraction is
**not faithful to the real code**: an *empty* bin (`len(acc) == 0`) passes the
changed comparison `len(acc) >= 0`, so the comprehension evaluates
`reduce_C_function([])` — and whether the bin is observably populated then
depends on the **aggregator's value on an empty list**, not on the occupancy
comparison at all.  With the library default `reduce_C_function=np.mean`,
`np.mean([])` is NaN, so the bin is *cleared* by `~np.isnan(accum)` even though
the comparison kept it (end-to-end: `ax.hexbin(x=[0.0], y=[0.0], C=[5.0],
gridsize=3, mincnt=0)` draws 1 bin while the bare-count
`ax.hexbin(x=[0.0], y=[0.0], gridsize=3, mincnt=0)` draws 11); with
`reduce_C_function=sum`, `sum([]) == 0.0` is a real value and the same bin is
*populated*.  A `bool = f(occ, t)` carrier cannot express that
aggregator-dependence, and the cross-regime equality the postcondition pins
(`decision_agg == decision_count`) is genuinely **false** there with the
default aggregator.

On `threshold >= 1` every bin passing `len(acc) >= mincnt` is **nonempty**, the
aggregate of a nonempty list of finite C-values is a real number (never NaN),
and the populated decision in both regimes is exactly the occupancy comparison
— the abstraction is faithful.  The excluded sub-domain is irrelevant to the
gold change's observable behaviour: at `mincnt = 0`, pre-patch `len(acc) > 0`
vs post-patch `len(acc) >= 0` differ **only** on empty bins, where the default
aggregator's NaN restores the identical cleared outcome (the gold patch is
observation-equivalent at `mincnt=0` under the default; the fixed, tested
behaviour lives at `mincnt >= 1`).  axiom_check.py (G-AX) checks the deep model
on the modeled domain with **both** the default `np.mean` and `sum`, and
additionally *witnesses* the `mincnt=0` aggregator-dependence out of domain,
so the boundary is demonstrably load-bearing rather than a convenience.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `decision_agg` / `decision_count` deep model ↔ the real `hexbin` accum decision

**Callee / code modeled:** the `accum` list comprehension in `Axes.hexbin`,
`lib/matplotlib/axes/_axes.py:5016-5020`. The changed per-bin decision is
modeled **deeply** by the `@Pure` predicate `decision_agg` in the `pure` region
(applied element-wise by the verified loop and pinned by the index-wise
postcondition); there is **no consumed `@ContractOnly` axiom**. The deep model
is validated equal to the real decision out-of-band by axiom_check.py (G-AX).

Post-patch source (the gold change is `>` → `>=` on line 5017):

```python
if mincnt is None:
    mincnt = 0
accum = np.array(
    [reduce_C_function(acc) if len(acc) >= mincnt else np.nan
     for Cs_at_i in [Cs_at_i1, Cs_at_i2]
     for acc in Cs_at_i[1:]],   # [1:] drops out-of-range points.
    float)
```

A bin is **populated** (carries `reduce_C_function(acc)`, a real value) iff
`len(acc) >= mincnt`; otherwise it is **cleared** (`np.nan`). With
`occ = len(acc)` and `t = mincnt` this is exactly `decision_agg(occ, t)` ==
`occ >= t`.

The oracle this must match is the bare-count regime, `_axes.py:5002-5003`:

```python
if mincnt is not None:
    accum[accum < mincnt] = np.nan
```

Here `accum` holds the integer bin counts; a bin is cleared iff
`count < mincnt`, i.e. populated iff `not (count < mincnt)` == `count >= mincnt`
== `decision_count(count, mincnt)`. (The unset default — `mincnt is None`,
resolved to `0` in the value-aggregation branch — is **outside the modeled
domain** `threshold >= 1`, see §2a: there the empty-bin outcome depends on the
aggregator's value on `[]`, not on the occupancy comparison, and the two
regimes genuinely differ under the default `np.mean`.)

**The behavioural change.** Pre-patch the value-aggregation regime used
`len(acc) > mincnt` (`decision_agg_pre(occ,t) == occ > t`), so with
`mincnt = 1` it kept only bins with `count >= 2`, whereas the bare-count regime
(and the user's intuition) keeps `count >= 1`. The fix `>` → `>=` makes
`decision_agg == decision_count` for every occupancy and threshold — exactly
the consistency the F2P test
`test_hexbin_mincnt_behavior_upon_C_parameter[png]` asserts (it renders the
`C`-given hexbin with `mincnt=1` equal to the `C`-absent hexbin with
`mincnt=1`).

**Soundness check (G-AX):** `axiom_check.py` re-implements both regimes'
decision exactly as the source computes them (the value-aggregation regime via
`len(acc) >= mincnt` with the library's **default** `reduce_C_function=np.mean`
and, to pin aggregator-independence, with `sum`; the bare-count regime via the
`accum[accum < mincnt] = np.nan` mask) and asserts, over boundary thresholds
and occupancies plus randomized fuzz **on the modeled domain `mincnt >= 1`**,
that (a) the deep model `decision_agg` equals the real value-aggregation
decision, and (b) the two regimes' decisions coincide for every
occupancy/threshold pair (the consistency the postcondition `Forall` encodes).
It additionally witnesses, **out of domain**, the `mincnt = 0` empty-bin
aggregator-dependence (default `np.mean` clears, `sum` keeps, bare-count
keeps) that motivates the `threshold >= 1` precondition (§2a). It imports only
`numpy` (the library `hexbin` itself uses) and the standard library; nothing
repo-specific. Exit 0 iff sound.

## 4. G-CONF (conformance_check.py)

The differential gate runs the contract-stripped impl region of
`populated_bins` (shadow) against the REAL patched `Axes.hexbin` (oracle)
in-container: each (occupancies, threshold) input is realized as a concrete
hexbin call (slot `k` of the first `(G+1)x(G+1)` lattice gets
`occupancies[k]` samples with constant payload `k+1`), and the populated set
is read back from the surviving offsets/values after the NaN filter, in BOTH
regimes (`C` given and `C` absent, same `mincnt`) plus a `sum`-aggregator
slice. >= 1e5 Requires-satisfying inputs: boundary + exhaustive (lengths
1..4 over {0..3} x thresholds 1..4) + 100000 fuzz. **Pinned fuzz seed: 26113**
(the instance number).
