# mapping.md — matplotlib__matplotlib-22871

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a7b7260bf06c20d408215d95ce20a1a01c12e5b1`, states the type
abstraction, and gives the provenance of the deep-model references (the numpy
reductions, validated by axiom_check.py / G-AX).

Repo file under change: `lib/matplotlib/dates.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `determine_level(c0..c5)` | the labelling-level scan inside `ConciseDateFormatter.format_ticks` — `lib/matplotlib/dates.py:798-806` (the `for level in range(5, -1, -1):` loop computing `level` and `show_offset`) | the modeled changed code: it computes the labelling `level` and the `show_offset` flag |
| `col_varies(col)` *(deep model — A-reference)* | `len(np.unique(tickdate[:, level])) > 1` — `dates.py:799` (post-patch `dates.py:800`) | structural model of the "column is not constant" numpy reduction |
| `col_has_one(col)` *(deep model — A-reference)* | `np.any(unique == 1)` where `unique = np.unique(tickdate[:, level])` — added by the patch at `dates.py:800` (post-patch) | structural model of the "value 1 occurs in the column" numpy reduction |
| `TickLevel.level` | the loop variable `level` (the index into `offsetfmts`/`fmts`) | the chosen labelling level |
| `TickLevel.show_offset` | the local `show_offset` (initialized from `self.show_offset`, default `True`) consumed at `dates.py:841` to decide the offset string | the 0/1 offset-shown flag |

The pre-patch repo code the change replaces (for the refinement audit, not
referenced from the consumer spec view):

```python
for level in range(5, -1, -1):
    if len(np.unique(tickdate[:, level])) > 1:
        if level < 2:
            show_offset = False
        break
    elif level == 0:
        level = 5
```

The gold patch turns the inner guard `if level < 2:` into
`if level < 2 and np.any(unique == 1):` (and hoists `unique`), so the offset is
suppressed only when the labelling column also contains the value `1`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `tickdate` — an `N x 6` numpy integer array (`np.array([tdt.timetuple()[:6] …])`, `dates.py:779`) | six parallel `List[int]` columns `c0..c5` | `tickdate[k, level]` ↔ `c{level}[k]`; `tickdate[:, level]` ↔ the column `c{level}`; `N = tickdate.shape[0]` ↔ `len(c0) == … == len(c5) >= 1` |
| the loop variable `level` (an `int`) | `TickLevel.level: int` in `0..5` | identity on the integer level |
| `show_offset` (a `bool`, default `True`) | `TickLevel.show_offset: int` in `{0,1}` | `True` ↔ `1`, `False` ↔ `0` |
| `for level in range(5, -1, -1): …` (fixed 6-iteration descending loop) | straight-line cascade of six `if col_varies(c{level})` tests, finest→coarsest | the loop trip count is the literal constant range `range(5, -1, -1)`; unrolling a constant-bound loop is a semantics-preserving transcription (no data-dependent bound) — refinement.md step I |

The downstream consumption of `(level, show_offset)` — selecting
`offsetfmts[level]` and emitting `tickdatetime[-1].strftime(offsetfmts[level])`
only when `show_offset` (`dates.py:841-847`) — is unchanged by the patch and is
not modeled; the patch changes ONLY the `(level, show_offset)` computation, which
is exactly what `determine_level` captures. `offsetfmts[1] == '%Y'`
(`dates.py:763`), so a level-1 labelling with `show_offset` true renders the
year as the offset — the behaviour the issue demands.

## 3. Deep-model reference provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `col_varies` deep model ↔ `len(np.unique(col)) > 1` (A-reference)
**Callee:** `numpy.unique` + `len(...) > 1` (numpy ≥ 1.x; the instance image
ships numpy in the matplotlib 3.5 env). `np.unique(col)` returns the sorted
distinct values of the column. `len(np.unique(col)) > 1` is therefore exactly
"the column has at least two distinct values", i.e. the column is not constant
across the ticks. The structural predicate

  `col_varies(col) ⇔ ∃ i<j. col[i] ≠ col[j]`

is precisely this property (both are false for length-0/1 columns and for any
constant column; both are true iff two entries differ). NOT a consumed axiom:
modeled deeply and validated `col_varies == (len(np.unique) > 1)` by
axiom_check.py. Docs: https://numpy.org/doc/stable/reference/generated/numpy.unique.html

### 3.2 `col_has_one` deep model ↔ `np.any(np.unique(col) == 1)` (A-reference)
**Callee:** `numpy.any` over the boolean array `np.unique(col) == 1` — the
condition the gold patch ADDS. `np.unique(col) == 1` is the element-wise equality
of the distinct values to `1`; `np.any(...)` is true iff `1` is one of the
distinct values, i.e. iff `1` occurs somewhere in `col`. The structural predicate

  `col_has_one(col) ⇔ ∃ i. col[i] == 1`

is exactly this (membership of `1` is invariant under deduplication). NOT a
consumed axiom: modeled deeply and validated `col_has_one == np.any(unique == 1)`
by axiom_check.py. Docs: https://numpy.org/doc/stable/reference/generated/numpy.any.html

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `np.unique`/`np.any`
on 19 boundary columns (singletons, constants, January-present/absent month
columns, year columns, negatives) + 20000 randomized fuzz columns and asserts
`col_varies`/`col_has_one` match. It additionally transcribes the full post-patch
`format_ticks` scan (the real `for level in range(5,-1,-1)` loop body verbatim)
and asserts the whole `determine_level` deep model equals it on 7 boundary +
20000 fuzz 6-column tick tables. It imports only `numpy` (the library the changed
code uses); nothing repo-specific. Exit 0 iff sound.
