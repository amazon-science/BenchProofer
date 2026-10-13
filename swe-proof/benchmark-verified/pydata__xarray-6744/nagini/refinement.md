# refinement.md — pydata__xarray-6744

The operation-by-operation correspondence between `model.py`'s implementation
(the `block_ends` / `block_begins` impl regions, plus the deep pure model
`end_shift` / `end_at` / `begin_at`) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, proof uses the axiom's `Ensures`, and **A-reference**, a deep
model validated == the real operation by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The change is a single function, `DataArrayRolling.__iter__`
(`xarray/core/rolling.py:270-282`). The patch replaces how the per-position
window index arrays `starts`/`stops` are built; the rest of `__iter__`
(`isel` slicing, `count`/`where` masking, `yield`) is unchanged. The two index
arrays are modelled as two functions, `block_ends` and `block_begins`
(SPEC_GUIDE §3: prefer one modeled function per site for more differential
witnesses), sharing one frozen spec (the pure region).

Gold hunk (the index computation):
```
-        stops = np.arange(1, len(self.window_labels) + 1)
-        starts = stops - int(self.window[0])
-        starts[: int(self.window[0])] = 0
+        dim0 = self.dim[0]
+        window0 = int(self.window[0])
+        offset = (window0 + 1) // 2 if self.center[0] else 1
+        stops = np.arange(offset, self.obj.sizes[dim0] + offset)
+        starts = stops - window0
+        starts[: window0 - offset] = 0
```

## A. The block-end array — `block_ends` ↔ gold `stops`

| # | model.py impl op (`block_ends`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `n: int` (`n >= 0`) | `self.obj.sizes[dim0]` (= `len(self.window_labels)`) | R | a dimension size; `int` ↔ the np int (mapping.md §1,§2). |
| A2 | param `w: int` (`w > 0`) | `window0 = int(self.window[0])` | R | window size; positivity is the `__init__` invariant (mapping.md §1). |
| A3 | param `center: bool` | `self.center[0]` | R | per-dim centred flag; `bool` ↔ `bool` (mapping.md §2). |
| A4 | `shift = end_shift(w, center)` (= `(w+1)//2` if center else `1`) | `offset = (window0 + 1) // 2 if self.center[0] else 1` | A-reference + I | identical integer formula; the deep model `end_shift` IS the patch's `offset`. Validated == the real operation by axiom_check.py (mapping.md §3.1). |
| A5 | build `[shift + 0, ..., shift + (n-1)]` (the loop, `end_at(i) = i + shift`) | `stops = np.arange(offset, n + offset)`, so `stops[i] = offset + i` | R | `np.arange(a, a+n)` ascending integer array ↔ the `List[int]` `[a, a+1, ...]` (mapping.md §2); element-wise equal. |

`block_ends`' frozen postcondition `Result()[i] == end_at(i, w, center)`
(with `end_at(i) = i + end_shift(w, center)`) pins each end to the
centre-aware shift. The pre-patch `stops = np.arange(1, n + 1)` has `stops[i] =
i + 1` (shift `1` always); `model_prepatch.py` reproduces that (`shift = 1`,
ignoring `center`) and **fails** the loop invariant
`ToSeq(stops) == ends_from(k, n, w, center)` (G-DIFF) — the spec sensing that
the centred shift `ceil(w/2)` is required.

## B. The block-start array — `block_begins` ↔ gold `starts`

| # | model.py impl op (`block_begins`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `shift = end_shift(w, center)` | `offset` (same local) | A-reference + I | as A4. |
| B2 | `raw = (shift + (k-1)) - w` per position (= `end_at(i) - w`) | `starts = stops - window0` (so `starts[i] = stops[i] - window0`) | R + I | element-wise integer subtraction; `np` int ↔ `int` (mapping.md §2). |
| B3 | `starts[i] = raw if raw > 0 else 0` (clamp to 0) | `starts[: window0 - offset] = 0` (leading clamp) | I (algebraically) | the leading slice-assign equals `max(0, ·)` on every entry: for `i >= window0 - offset` the value is already `>= 0`; for `i < window0 - offset` it is `< 0` and set to `0`. So both equal `max(0, end_at(i) - w) = begin_at(i)` (mapping.md §3.2). |

`block_begins`' frozen postcondition `Result()[i] == begin_at(i, w, center)`
pins each start to the clamped centre-aware value. The pre-patch
`starts = (np.arange(1, n+1)) - w; starts[:w] = 0` uses shift `1` and clamp
count `w`; `model_prepatch.py` reproduces `shift = 1` and **fails** the start
invariant for centred windows (G-DIFF), the same discriminator as site A.

## C. The unchanged tail (no model obligation)
The slice `self.obj.isel({dim0: slice(start, stop)})`, the per-window count
mask `window.where(counts >= self.min_periods)`, and `yield (label, window)`
are **unchanged** by the patch. They are the caller that consumes the index
ranges; the model specifies only the ranges. (The gold also renames the local
`self.dim[0]` to `dim0` and widens the return type annotation; both are
behaviour-preserving and carry no model node.)

## D. No kind-3 (unexpressible-changed-op) steps; no consumed axioms
Every step above is R, A-reference, or I. The one operation that *changed* —
the index arithmetic producing `starts`/`stops` — is modelled **deeply** (the
spelled-out integer helpers `end_shift`/`end_at`/`begin_at` and the verified
loops), not hidden behind an axiom. There is **no `@ContractOnly` axiom** in
this bundle: the changed operation calls no library function whose behaviour
the proof must assume. The deep model is validated **== the real changed
operation** (the gold patch's `np.arange`/subtract/slice-assign) by
axiom_check.py / G-AX (the lone A-reference, mapping.md §3). The proof-only
helpers (`ends_from`/`begins_from`/`*_unfold`/`*_index_lemma`) are verified
Nagini lemmas, not axioms.

## E. verify(model) ⇒ resolved
`block_ends`/`block_begins` verify only if each produced index equals the
centre-aware closed form (`end_at`/`begin_at`, A4/A5/B1-B3). By R (np int
array ↔ `List[int]`, `np.arange`/subtract/slice-assign ↔ the same integer
arithmetic) the verified arrays equal the gold patch's `stops`/`starts`
element-by-element, and by G-AX (axiom_check.py) the deep model equals the real
operation on the boundary sweep + 200 000 fuzz cases. Feeding those exact ranges
to the unchanged `isel`/`count`/`where`/`yield` tail (site C) reproduces the
centre-justified manual iteration the issue demands and the F2P
`test_rolling_iter[...-True-...]` cases assert (manual iteration ==
`rolling.mean()`). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited A-reference —
and the gold patch resolves (G-RESOLVE). The trust points reduce to the one of
PLAN §1.1 present here: A-reference fidelity (G-AX) and refinement fidelity
(this document, G-EQ); there is no consumed axiom to trust.
