# refinement.md — matplotlib__matplotlib-22871

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`offsetSelection` `do` block and the deep `offsetDecision` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The offset-decision site — `ConciseDateFormatter.format_ticks` (`lib/matplotlib/dates.py:797-806`)

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
```

| # | Solution.lean impl op (`offsetSelection`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `initShow : Bool` parameter | `show_offset` local (set from `self.show_offset`, `dates.py:795`) | R | `bool` ↔ `Bool` (mapping.md §2). Read-only carrier of the pre-suppression display flag. |
| A2 | `stats : List (Nat × List Int)`, scanned finest→coarsest | the loop `for level in range(5, -1, -1)` over `tickdate[:, level]` | R | components in the SAME order; each column `tickdate[:, level]` ↔ `List Int` (mapping.md §2). The column producer (`num2date`/`timetuple`/`np.array`) is unchanged upstream (I-reference, mapping.md §3), run by the real repo in G-CONF. |
| A3 | `colVaries col` (`col.any (· != col.headD 0)`) | `len(np.unique(tickdate[:, level])) > 1` | I | "more than one distinct value across the ticks". `np.unique` only deduplicates; `>1 distinct` ⇔ some entry differs from the first. Transliterated by G-CONF. |
| A4 | `colHasOne col` (`col.contains 1`) | `np.any(unique == 1)` (added by the patch) | I | "the value one appears among the column's values". `unique` is the set of column values, so `1 ∈ unique ⇔ 1 ∈ col`. The discriminating new factor. Transliterated by G-CONF. |
| A5 | `suppressOffset lvl col = decide (lvl < 2) && colHasOne col` | `level < 2 and np.any(unique == 1)` | I | the offset-suppression guard, conjunction of the level test and the new boundary-value test. |
| A6 | first `colVaries`-true component fixes `chosenLevel`; offset hidden iff `suppressOffset`, else keeps `initShow`; scan stops (`break`) | the `if len(unique) > 1: … break` arm | I | the early-stop scan: at the first changing component, optionally clear `show_offset`, then `break`. |
| A7 | empty / no-changing-component case ⇒ `(5, initShow)` | the `elif level == 0: level = 5` fall-through (loop ends with `level` left at its last value, `show_offset` untouched) | I | when no component changes over the ticks, the loop reaches `level == 0`, sets `level = 5`, and never enters the suppression arm — exactly `offsetDecision _ [] = (5, initShow)` and the all-constant scan. |
| A8 | result `(chosenLevel, showOffset)` | the `(level, show_offset)` locals consumed at `dates.py:840-846` (`strftime(offset_formats[level])` else `''`) | R | the downstream renderer is unchanged (I-reference, mapping.md §3); G-CONF applies the SAME real `strftime` to the shadow's decision and compares `get_offset()`. |

Discriminating content of the change — at one of the two coarsest components
(`level < 2`) the offset is suppressed ONLY when the column contains the
boundary value `1` — lives in the `colHasOne` factor of `suppressOffset` (A4/A5)
⇔ the `and np.any(unique == 1)` the patch adds. The pre-patch suppressed whenever
`level < 2`; `Solution_prepatch.lean` reproduces that (`suppressOffset` replaced
by `decide (lvl < 2)`) and **fails** `out = offsetDecision initShow stats` exactly
when `level < 2` and the column lacks `1` (G-DIFF) — the case the F2P
`test_offset_changes` weeks-7..30 span exercises (`get_offset() == '1997'`).

## B. The unchanged surrounding computation (not modeled, I-reference)

- **Column producer** — `tickdatetime = [num2date(v) for v in values]`,
  `tickdate = np.array([tdt.timetuple()[:6] …])` (`dates.py:778-779`): unchanged
  upstream of the modeled boundary. Not modeled; the SAME real call produces the
  integer columns the G-CONF shadow consumes (mapping.md §3).
- **Offset renderer** — `tickdatetime[-1].strftime(offset_formats[level])` else
  `''` (`dates.py:840-846`): unchanged downstream. Not modeled; the SAME real
  `strftime` renders the shadow's `(level, show_offset)` in G-CONF.
- **The per-tick label construction** (`dates.py:809-838`): unchanged and
  independent of the offset decision; not observed by the F2P test (which checks
  `get_offset()` only). Out of scope of the modeled operation.

No separate prepatch is needed for site B: there is no site B change — the patch
touches only the offset-decision guard (site A).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the
offset-suppression guard gaining the `np.any(unique == 1)` factor — is modeled
**deeply** (the spelled-out `colHasOne`/`suppressOffset`/`offsetDecision`, A4/A5,
all I), not hidden behind an axiom about the function under change. There are no
consumed axioms and no A-reference deep models of an outside callee: `np.unique`,
`num2date`, and `strftime` are unchanged callees exercised by the real repo in
G-CONF (mapping.md §3), not contracts the proof consumes.

## D. verify(Solution) ⇒ resolved

`offsetSelection` verifies only if its output equals `offsetDecision initShow
stats` (A3-A7): the early-stop finest→coarsest scan whose suppression guard is
`level < 2 AND the column contains 1` (A4/A5). By R (`bool ↔ Bool`,
`tickdate[:, level] ↔ List Int`, mapping.md §2) and the unchanged upstream
(column producer) and downstream (`strftime` renderer, A2/A8/§B), the verified
decision drives the SAME offset string the patched `format_ticks` produces. By
G-CONF the R/I transliteration of `offsetDecision`, rendered through the real
`strftime`, agrees with the real patched `get_offset()` on ≥10⁵ inputs (incl. the
three F2P spans). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc + G-CONF);
there is no axiom-soundness trust point (no axioms ⇒ G-AX skipped).
