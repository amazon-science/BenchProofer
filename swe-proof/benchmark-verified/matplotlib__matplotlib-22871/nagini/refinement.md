# refinement.md — matplotlib__matplotlib-22871

The operation-by-operation correspondence between `model.py`'s implementation
(the `determine_level` impl region + the deep `col_varies` / `col_has_one`
structural models) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The labelling-level scan — `ConciseDateFormatter.format_ticks` (`lib/matplotlib/dates.py:798-806`)

Gold hunk:
```
 for level in range(5, -1, -1):
-    if len(np.unique(tickdate[:, level])) > 1:
-        if level < 2:
+    unique = np.unique(tickdate[:, level])
+    if len(unique) > 1:
+        # if 1 is included in unique, the year is shown in ticks
+        if level < 2 and np.any(unique == 1):
             show_offset = False
         break
     elif level == 0:
         level = 5
```

| # | model.py impl op (`determine_level`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `c0..c5: List[int]`, equal length `N >= 1` | the `N x 6` integer array `tickdate`; `tickdate[:, level]` ↔ column `c{level}` | R | numpy `N x 6` int array ↔ six parallel `List[int]` columns (mapping.md §2). |
| A2 | `col_varies(c{level})` — `∃ i<j. col[i] != col[j]` | `len(np.unique(tickdate[:, level])) > 1` | A-reference | the unchanged numpy reduction is modeled **deeply** by the structural predicate; there is no consumed axiom. G-AX (axiom_check.py) runs the real `np.unique` and asserts `col_varies == (len(np.unique) > 1)` (mapping.md §3.1). |
| A3 | `col_has_one(c{level})` — `∃ i. col[i] == 1` | `np.any(unique == 1)` (the clause the patch ADDS) | A-reference | the added numpy reduction is modeled **deeply** by the structural membership predicate; G-AX asserts `col_has_one == np.any(unique == 1)` (mapping.md §3.2). |
| A4 | the descending cascade `if col_varies(c5): … elif col_varies(c1): … elif col_varies(c0): … else 5` selecting the highest-indexed varying column, breaking on the first hit | `for level in range(5, -1, -1): if len(unique) > 1: … break elif level == 0: level = 5` | I | the real loop has a literal constant trip count `range(5,-1,-1)`; the straight-line cascade is a semantics-preserving unrolling (mapping.md §2). The `break` ↔ the cascade returning at the first varying level; the `elif level == 0: level = 5` (no varying level found) ↔ the final `return TickLevel(5, 1)`. |
| A5 | `show_offset = 1` default; set to `0` only when `level < 2 and col_has_one(c{level})` (the nested `if col_has_one` inside the level-1 / level-0 branches) | `show_offset` initialized `True`; `if level < 2 and np.any(unique == 1): show_offset = False` | I + A-reference | identical control structure; the discriminating conjunct `np.any(unique == 1)` is the A-reference `col_has_one` (A3). `True`/`False` ↔ `1`/`0` (R, mapping.md §2). |

## B. The discriminating clause (G-DIFF)

The single behavioural change is the added conjunct `np.any(unique == 1)` on the
offset-suppression guard. It lives in step A5 / A3 (`col_has_one(c{level})`).

- **Post-patch:** at a month-level labelling (level 1) the offset is suppressed
  iff the tick months include `1` (January). When the months do NOT include
  January, `show_offset` stays `1` → the offset (`offsetfmts[1] == '%Y'`) shows
  the year. This is the F2P case: `set_xlim(d1 + 7 weeks, d1 + 30 weeks)` spans
  Feb–Jul 1997, so `get_offset() == '1997'`.
- **Pre-patch:** `if level < 2:` suppresses the offset unconditionally at level
  0/1, so the year-bearing offset disappears even when January is absent — the
  bug.

`model_prepatch.py` reproduces the pre-patch guard (returns `TickLevel(1, 0)` /
`TickLevel(0, 0)` whenever `level < 2`, with NO `col_has_one` check) and **fails**
the postcondition

```
Ensures(Implies(col_varies(c1) and not col_varies(c5) and not col_varies(c4)
                and not col_varies(c3) and not col_varies(c2),
                (Result().show_offset == 0) == col_has_one(c1)))
```

(reported by Nagini at the month-level clause) — exactly the spec sensing the
change (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding the `np.any(unique == 1)` membership test to the
offset-suppression guard — is modeled **deeply** (the structural predicate
`col_has_one`, consumed directly in `determine_level`, step A3/A5), not hidden
behind an axiom about the function under change. There are **no consumed
`@ContractOnly` axioms** at all: both numpy reductions (`np.unique`, `np.any`)
are unchanged callees the changed code composes, and both are modeled as
A-reference deep structural predicates that G-AX validates against the real numpy
functions. A `np.unique`/`np.any` axiom would be a dead axiom; instead the deep
models carry the proof and G-AX carries their soundness.

## D. verify(model) ⇒ resolved

`determine_level` verifies only if (i) `level` equals the highest-indexed varying
column (or 5 when none varies) — pinning the labelling level that selects
`offsetfmts[level]`; and (ii) `show_offset == 0` **exactly** when the labelling
level is coarse (year/month) and that column contains `1` — pinning the year-in-
offset behaviour. By R (numpy `N x 6` int array ↔ six `List[int]` columns;
`bool` ↔ `{0,1}`; constant-bound loop ↔ cascade) the verified scan equals the
post-patch `format_ticks` scan; by G-AX the deep models `col_varies` /
`col_has_one` equal the real `np.unique`/`np.any` reductions (A-reference) and
the whole `determine_level` equals the real loop body on 40000+ fuzz tick tables.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and validated numpy reductions — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: callee
soundness (G-AX, here the numpy reductions) and refinement fidelity (this
document, G-EQ).
