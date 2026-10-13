# refinement.md — astropy__astropy-14539

Maps every operation in `implementation_columnDiffRows` (Solution.lean impl
region) to its `patch.diff` / base-source counterpart. Tags: **R** (type-only
refinement, bijection in mapping.md), **A-consumed** (proof uses an axiom),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op). The patch's net effect on `TableDataDiff._diff` is a single one:
widen the branch predicate that selects the row-wise variable-length-array (VLA)
comparison so that BOTH VLA format markers route to it
(`elif "P" in col.format:` → `elif "P" in col.format or "Q" in col.format:`,
diff.py:1452). The VLA branch body itself is unchanged.

| # | Lean op (impl region) | patch.diff / base-source counterpart | tag | note |
|---|---|---|---|---|
| 1 | `if fmt.contains 'P' \|\| fmt.contains 'Q'` | `elif "P" in col.format or "Q" in col.format:` (diff.py:1452, POST-PATCH) | R | the patched predicate verbatim; `fmt : List Char` ↔ `col.format : str`, membership of the two VLA markers. This row encodes the entire patch. |
| 2 | `for i in List.finRange arra.length do …` | `for idx in range(len(arra))` (diff.py:1456, inside the VLA comprehension) | R | `List.finRange arra.length` ↔ `range(len(arra))`; the same row indices in the same increasing order. The positions are typed as positions OF the first column (`Fin arra.length`), which is what lets each of them carry its own in-bounds fact into row 3's call; erased, the loop is the plain index walk. |
| 3 | `if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then acc := acc ++ [i.val]` | `if not np.allclose(arra[idx], arrb[idx], rtol=self.rtol, atol=self.atol)` keep `idx` (diff.py:1457-1459) | R | the CONDITIONAL APPEND is refined (each row's index is kept exactly when the per-row test does not accept it, appended in increasing order); the TEST is abstracted, not refined. `rowsAgree` is the unchanged `np.allclose` callee as an `opaque` signature: the patch does not touch it, the proof consumes no property of it, and the spec makes no claim about which pairs it accepts. What IS named about it is not a property but its DOMAIN — the pair of row lengths on which it answers at all — and that domain is an ARGUMENT of the callee, supplied at the call site out of the reporter's own argument (row 6). The argument is a proof and erases: the compiled loop performs one unguarded call per row, exactly as the branch does. |
| 4 | `return acc` | `diffs = ([ … ],)` then `diff_values`/`diff_total` consume `diffs[0]` (diff.py:1453-1465) | I | the differing-row index list, in order, is the branch's result |
| 5 | `return elementwiseDiff arra arrb (hfix …)` (else) | `diffs = np.where(arra != arrb)` (diff.py:1463) | R | the UNCHANGED fixed-shape comparison. The patch does not touch this arm, and the spec pins the fixed-shape report to be exactly this routine's result — WHICH columns reach it, not what it computes. So no property of `elementwiseDiff` is consumed (opaque signature only, no axiom) while the branch is nonetheless constrained: an impl may not re-route a fixed-shape column to the row-wise comparison, nor answer it with anything else. The domain argument is discharged from `hfix` by the very format test that took this branch (row 7), so the arm needs no shape check of its own — matching the base source, which has none. |
| 6 | reporter argument `hcmp : ∀ idx < arra.length, rowsComparable arra[idx]! arrb[idx]! = true` | “`np.allclose(arra[idx], arrb[idx])` returns rather than raising” (diff.py:1457) | R | the per-row callee is PARTIAL: on two 1-D rows it answers exactly when their lengths are equal or one of them is 1, and raises `ValueError` otherwise. `rowsComparable` is that predicate. It enters as an ARGUMENT of the reporter and of `rowDiffIndices`, and is threaded from there into every call of the test, so the demand is narrowed at exactly the columns where no report exists AND a call outside the domain is not expressible at all — a report may not be built out of a row the real branch would have crashed on. See the admissibility case, which discharges the postcondition at a RAGGED point to show the narrowing did not empty it. Measured exhaustively over row lengths 0..4 (25 length pairs / 900 row pairs, 0 mismatches) and over the G-CONF grammar (359 994 rows, 0 mismatches). |
| 7 | reporter argument `hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true` | “`np.where(arra != arrb)` returns rather than raising” (diff.py:1463) | R | the flat callee is PARTIAL in the same way and it is the OTHER half of the routing. The arm that consults it is the arm the format has already declared NOT variable-length, so the storage it faces is the storage astropy gives an ORDINARY FIXED-SHAPE column — a rectangular numeric block, one row per table row and the same number of stored values in each — and not the object array of per-row arrays that variable-length storage uses. On two such blocks the elementwise `!=` is elementwise and `np.where` reports, however many values a row holds; two blocks whose widths differ are related when one of the widths is 1, which numpy broadcasts across the row. What has no answer is a RAGGED pair — no block exists (`np.asarray` refuses it: `ValueError: setting an array element with a sequence. The requested array has an inhomogeneous shape`) — or two widths numpy cannot relate (`operands could not be broadcast together`). `rowsAreFixedShape` is that predicate: equal row counts, each column of ONE width, and the two widths related by the same rule `rowsComparable` states. It is likewise an argument, and it is guarded by the format: it is owed only where the format is not variable-length, which is exactly the arm that consults the flat comparison. Measured: EXHAUSTIVELY over every column pair of 1-3 rows with per-row widths 0-3 at equal row counts — the modeled domain, since `TableDataDiff._diff` returns before the per-column loop when the two tables' row counts differ and `columnDiffRowsContract` hypothesizes `arra.length = arrb.length` — 4 368 pairs, 0 mismatches, 30 of them in domain; and over the G-CONF `flat-domain` leg's grammar with NO shape excluded, 36 015 non-VLA column pairs, 0 mismatches, 10 858 in domain, of which 16 516 hold an empty row (a shape no FITS format realizes, counted rather than fenced off, since a width-0 block's comparison answers or raises like any other and never takes an array's truth value). Both figures were measured TWICE and agree to the digit: in the instance image, numpy 1.25.2 (the gate prints `numpy_version` beside the counts), and out of it on numpy 2.2.6. One gap is counted and not claimed away: at UNEQUAL row counts (2 688 exhaustive pairs) numpy broadcasts a one-row block across the other column's rows and answers on 40 pairs the predicate refuses. That is outside the modeled domain — the routine never reaches the loop there — so no demand is lost, but the predicate is narrower than the routine there and the count says by how much. |

No A-consumed and no A-reference rows ⇒ no consumed callee axiom ⇒ G-AX is a skip
stub. No changed operation is inexpressible: the only changed op is the branch
predicate (row 1, modeled exactly), and everything the branch it enables computes
ON TOP of the unchanged per-row callee — the row domain, the order, the
accumulation — is modeled deeply on `List (List Int)`. The R rows are what
`conformance_check.py` differential-tests against the real post-patch
`numpy.allclose` branch over 120k fuzzed integer-VLA inputs (leg `report` for rows
1-4, leg `domain` for row 6, leg `flat-domain` for row 7).

Rows 6 and 7 enter through `columnDiffRowsContract`, the demand the impl is proved
against: it quantifies over EVERY declared format and every pair of columns of
equal row count, hands the reporter those two facts as its own arguments, and then
requires `problem_spec_columnDiffRows` of whatever it returns. So the facts are
available to the reporter (and to anything it calls) exactly where a report is
demanded, and nowhere else.

Rows 6 and 7 are arguments rather than side conditions on purpose. A partial
callee's domain stated as a hypothesis of the postcondition still leaves the call
EXPRESSIBLE: an impl may ask the test about a row the real routine would raise on,
and because the answer is an opaque atom the fabricated value cancels out of any
comparison, so the verifier rejects nothing. Carried as an argument of the callee,
the same impl cannot be written down — the fact simply is not available at that
row.

That shape has a price, and it is why row 7's predicate has to be measured and not
merely plausible: a domain carried as an implication ARGUMENT is also what gates the
postcondition, so wherever the predicate is decidably FALSE the argument
`isVariableLengthFormat fmt = false → …` is uninhabitable and `∀ hfix, problem_spec
…` demands NOTHING. An earlier revision of this bundle wrote row 7's predicate as
"one stored value per row in both columns", which is false at every ordinary
multi-valued fixed-shape column — a `4I` column with `dim='(2,2)'`, the very column
the FAIL_TO_PASS tests assert on — and so left the flat arm unconstrained there: a
reporter answering `[]` at that column satisfied the contract. Widening the
predicate to the real routine's measured domain re-inhabits the argument and
re-pins the demand. A predicate that is too NARROW does not merely under-specify,
it silently deletes the obligation. The two `(by decide)` domain arguments that appear throughout `properties.py`
are these facts being supplied at concrete columns; they carry no content beyond
what the pure predicates already decide.

## Why the per-row test is abstracted rather than refined

An earlier revision of this bundle refined row 3's test to whole-sequence
inequality — `arra[idx]! ≠ arrb[idx]!` — and defended it on a domain of "rows
holding sequences of equal length in the two columns". That is not the domain a
variable-length column lives in: its rows are stored at whatever length each row
needs, the instance's own reproducer is
`fits.Column('a', format='QD', array=[[0], [0, 0]])`, and on a row where one side
stores a single value `np.allclose` broadcasts it against every value on the other
side and reports AGREEMENT. So the old model demanded a differing-row report where
the real post-patch code reports none: unfaithful in the direction that makes the
spec reject correct code. Measured on the widened G-CONF grammar: 13 538 rows and
12 170 whole columns on which sequence equality and the real test disagree, e.g.
row `[0, 0]` vs `[0]`.

Abstracting the callee removes the claim instead of restating it more carefully,
which is the right move for a routine the patch does not modify — and it costs the
spec nothing on the patch's own subject matter, since the patch changes only which
columns reach this test. Two consequences are recorded honestly:

- the old model is now an `expect="reject"` case
  (`compare-rows-by-structural-equality` in `properties.py`), refuted at the ragged
  row `[[1, 1]]` vs `[[1]]` under the callee's measured value there;
- an implementation calling the callee with its two arguments SWAPPED is
  behaviorally identical in the repository (the real test is symmetric at these
  tolerances) but is NOT admitted by this spec, because `rowsAgree x y` and
  `rowsAgree y x` are distinct opaque atoms. Assuming the symmetry would be an
  unfounded property claimed of an unchanged callee. Measured and recorded in
  `properties.py`; not carried as a rival, since it is correct code.

## Granularity & composition note

The modeled function is the per-column differing-row computation, which is
exactly where the patch acts (the branch predicate at diff.py:1452). Its output —
the list of differing row indices — flows directly into `self.diff_total`,
`self.diff_values` and `self.diff_ratio` (diff.py:1465-1488) and thence into
`diff.identical` and the report. The patch changes ONLY which branch a Q-format
column takes; everything downstream is unchanged and applied identically to the
gold and pre-patch outputs. So the discriminating difference already exists at
this routine's output: on a Q-format VLA column the gold takes the row-wise
branch (correct empty/row-granular diff), whereas the pre-patch routes it to the
flat `np.where(arra != arrb)` branch (the wrong computation that yields the
spurious differences the problem statement reproduces). Modeling this routine
alone is therefore sufficient both to make the spec see the bug (G-DIFF) and to
pin the fixed behavior (verify ⟹ correct on the declared domain). The two domain
equivalences of rows 6 and 7 — `np.allclose`'s and `np.where`'s — are validated
empirically by G-CONF; they are not separately formalized, the standard way R-legs
are judged in this bundle.

## Prepatch (G-DIFF) correspondence

`Solution_prepatch.lean` keeps spec + pure + axioms regions byte-identical and
changes only the impl region: the branch predicate is the PRE-PATCH
`if fmt.contains 'P'` (only one VLA marker recognized), reproducing
`elif "P" in col.format:` (diff.py:1452, pre-patch). A column whose format carries
`'Q'` but not `'P'` (e.g. `"QJ(2)"`, `"QD"` — exactly the F2P columns and the
`fits.Column('a', format='QD', …)` reproducer) then falls through to the opaque
fixed-shape branch instead of the row-wise computation. The twin reaches that
branch the only way a `'Q'`-format column can be made to reach it — by testing the
flat comparison's shape requirement for itself
(`if hg : rowsAreFixedShape arra arrb = true then return elementwiseDiff arra arrb hg else return []`),
since at a variable-length format `hfix` owes it nothing. That test is the
pre-patch mis-routing made writable, not an extra demand: it is what a reporter
that believes a `'Q'` column is fixed-shape has to do to consult the flat routine
at all. Since `elementwiseDiff` is opaque (no defining equation), no
proof can show its result equals `rowDiffIndices arra arrb` for all such inputs,
so `correct_columnDiffRows` is unprovable for the pre-patch impl: at a `Q`-only
format the specification classifies the column as variable-length and demands the
row-wise difference set, while the pre-patch impl hands back the opaque
fixed-shape result. Measured, not merely argued, and re-measured against the
current model:

- the prepatch file does not verify (exit 1), and the failure is the missing
  defining equation and not a tactic slip — the row-wise pattern the proof rewrites
  with is simply absent from the twin's `'P'`-only body, and the fixed-shape arm it
  reaches instead cannot be closed by `rfl`:

  ```
  error: Tactic `rewrite` failed: Did not find an occurrence of the pattern
    (do let r ← forIn (List.finRange arra.length) [] fun i r =>
            if (!rowsAgree arra[↑i]! arrb[↑i]! ⋯) = true then … ).run
  in the target expression
    (if fmt.contains 'P' = true then … )
  error: Tactic `rfl` failed: The left-hand side
    fun (h : false = true) =>
      (if fmt.contains 'P' = true then … else if hg : rowsAreFixedShape arra arrb = true
          then pure (elementwiseDiff arra arrb hg) else pure []).run =
        List.map Fin.val (List.filter (fun i => !rowsAgree arra[↑i]! arrb[↑i]! ⋯) …)
  is not definitionally equal to the right-hand side
    fun (h : ¬false = true) =>
      (if fmt.contains 'P' = true then … else if hg : rowsAreFixedShape arra arrb = true
          then pure (elementwiseDiff arra arrb hg) else pure []).run =
        elementwiseDiff arra arrb ⋯
  ```

- the refutation
  `(h0 : rowsAgree [1] [3] (by decide) = false) → (elementwiseDiff [[1]] [[3]] (by decide) ≠ [0]) → ¬ problem_spec_columnDiffRows ['Q'] [[1]] [[3]] (by decide) (by decide) (implementation_columnDiffRows ['Q'] [[1]] [[3]] (by decide) (by decide))`
  ELABORATES against `Solution_prepatch.lean` (exit 0), FAILS against
  `Solution.lean` (exit 1 — which computes `[0]` there and satisfies the spec),
  and `False` is not derivable from that hypothesis group (consistency probe, exit
  1). `rowsAgree [1] [3] = false` is the REAL routine's value at that row
  (`np.allclose([1],[3], rtol=0, atol=0)` is `False`), so the refutation is stated
  at an input that actually occurs. It is stated at a pair of columns of one stored
  value per row deliberately: that shape is inside the flat comparison's domain, so
  the discriminating input is one where the twin's mis-routing produces a WRONG
  report rather than one where it could produce no report at all.

So the spec discriminates the bug (G-DIFF) at a named input and not by a tactic
mismatch. This mirrors the real regression — the pre-patch code reports spurious
differences (in reality via a `ValueError`/mis-comparison) for Q-format VLA
columns that are in fact identical.
