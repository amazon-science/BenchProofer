# mapping.md — astropy__astropy-14539

## Modeled function

| Lean | Python |
|---|---|
| `implementation_columnDiffRows` / `problem_spec_columnDiffRows` / `correct_columnDiffRows` | the per-column differing-row computation inside `TableDataDiff._diff`, for the variable-length-array (VLA) branch |

Symbol binding (file:line @ base_commit `c0a24c1dc957a3b565294213f435fefb2ec99714`):

- `astropy/io/fits/diff.py:1227` — `class TableDataDiff(_BaseDiff)`.
- `astropy/io/fits/diff.py:1344` — `def _diff(self)`.
- `astropy/io/fits/diff.py:1429-1485` — the per-common-column loop. For each
  column it picks one of three comparison branches and stores the resulting
  differing-row indices into `self.diff_values` / `self.diff_total`.
- `astropy/io/fits/diff.py:1448-1451` — floating-point branch
  (`np.issubdtype(... np.floating)` → `where_not_allclose`). Outside the modeled
  integer-VLA domain.
- `astropy/io/fits/diff.py:1452` — **the patched line**: `elif "P" in col.format:`
  (pre-patch) → `elif "P" in col.format or "Q" in col.format:` (post-patch). This
  is the branch predicate the model abstracts as `isVariableLengthFormat`.
- `astropy/io/fits/diff.py:1453-1461` — the VLA branch body the predicate guards:
  `diffs = ([idx for idx in range(len(arra)) if not np.allclose(arra[idx], arrb[idx], rtol=self.rtol, atol=self.atol)],)`.
  The `range(len(arra))` row domain, the increasing order and the list
  construction are modeled deeply; the per-row `np.allclose` test itself is the
  UNCHANGED callee abstracted by `opaque rowsAgree` (see below).
- `astropy/io/fits/diff.py:1462-1463` — the `else` branch: `diffs = np.where(arra != arrb)`,
  the flat element-by-element comparison for ordinary fixed-shape columns. This is
  the UNCHANGED routine abstracted by `opaque elementwiseDiff`; the VLA branch
  never reaches it. (For an object-array of ragged/multi-value rows it raises a
  truth-value-ambiguous `ValueError` — empirically the root of the spurious-diff
  bug — but the model only needs that it is a DIFFERENT computation than the
  row-wise one, never satisfying the row-wise spec on a Q-format column.)

## What the spec view discloses (leakage boundary)

`P` / `Q` are FITS column-format markers for 32-bit / 64-bit variable-length array
descriptors. They appear IN THE SPEC VIEW, as the body of `isVariableLengthFormat`
in the pure region, and again in the elided impl region. An earlier revision of
this file claimed they appear "only inside the elided impl region and the elided
precondition (never in the spec view)"; that was wrong on both counts and is
corrected here. What is disclosed, measured against the public
`problem_statement` (`hints_text` is NOT public and is not used anywhere in this
bundle):

- **`Q` is PUBLIC, verbatim.** The problem statement's reproducer is
  `fits.Column('a', format='QD', array=[[0], [0, 0]])`, and its Description says
  the cause "may be caused by improper handling of VLAs (variable-length
  arrays)". So the gold's tested discriminator — that a `Q`-format column is a
  variable-length column and must be compared as one — is stated publicly.
- **The RAGGED row shape is PUBLIC too**: `array=[[0], [0, 0]]` is a column whose
  two rows store one and two values. That is the input class `rowsComparable` and
  the ragged admissibility point are about, so the faithfulness repair rests on
  public information.
- **`P` is the residual**, and it is not the discriminator: it is the marker the
  PRE-patch code already handled. It is in the spec view because
  `isVariableLengthFormat` must be TRUE of a `P`-format column — that is
  pre-existing behavior the PASS_TO_PASS suite exercises, and a spec naming only
  `Q` would demand the FLAT routine for a `P`-format column and so be wrong about
  the gold code. Measured, both halves: with `isVariableLengthFormat fmt =
  fmt.contains 'Q'`, the gold implementation does NOT verify (exit 1), and the
  refutation `(rowsAgree [1, 2] [3, 4] = false) → (elementwiseDiff [[1,2]]
  [[3,4]] ≠ [0]) → ¬ problem_spec ['P'] [[1,2]] [[3,4]] (implementation ['P']
  [[1,2]] [[3,4]])` ELABORATES against it (exit 0) — i.e. the rejection is the
  spec contradicting the real behavior at a named `P`-format input, not a tactic
  mismatch. Nor can the marker test be abstracted away: it IS the operation the
  patch changes. The only shape that keeps the letters out of the spec while
  staying faithful is to take the selector as an abstract `isVarLen : Bool` INPUT
  — and then the pre-patch and post-patch functions are the SAME function (`if
  isVarLen then row-wise else flat`), so `Solution_prepatch.lean` would differ from
  `Solution.lean` in no region at all and would verify exactly as gold does,
  leaving G-DIFF with nothing to discriminate. Abstracting the changed operation is
  what the spec guide forbids, and this is the concrete reason.
- The spec view is SYMMETRIC in the two markers and says nothing about which of
  them the pre-patch code was missing, nor that anything was added. The narration
  that did — "the format vocabulary provides two such markers, one per descriptor
  width it supports, and they are equal in force: carrying EITHER marker makes the
  column variable-length" — was in the earlier revision's
  `isVariableLengthFormat` docstring and has been removed; the docstring now says
  only that a variable-length format carries a variable-length descriptor marker.

No relaxed-leakage disposition is claimed, and there is deliberately no
`RELAXED_LEAKAGE.md` in this bundle. Relaxation is for a `problem_statement ↔
gold` MISMATCH, where the tested discriminator exists only in `hints_text` or gold
internals so a faithful spec must name a private token. That is not this instance:
the discriminator (`Q` / VLA) is public, so there is nothing to relax. G-LEAK
passes mechanically.

## Lean ↔ Python type bijection (used by G-CONF; no axioms ⇒ G-AX is a skip)

| Python | Lean | notes |
|---|---|---|
| `col.format` (a `str`) | `fmt : List Char` | per-code-point; only membership of `'P'`/`'Q'` is tested |
| `arra = self.a[col.name]` (a column's stored data) | `arra : List (List Int)` | one inner list per table row. The one type covers BOTH storages the two branches face: the object array of per-row integer sequences a variable-length column holds (ragged lengths allowed, and the two columns' rows may be ragged AGAINST EACH OTHER) and the rectangular numeric block a fixed-shape column holds (every row the same width, a width of 1 for the ordinary scalar column) |
| `arrb = self.b[col.name]` | `arrb : List (List Int)` | the other column's rows |
| `range(len(arra))` | `List.finRange arra.length` | the same row indices in the same order, typed as positions OF the first column so each carries its own in-bounds fact; erased, an index walk |
| `"P" in col.format or "Q" in col.format` | `isVariableLengthFormat fmt` | the patched branch predicate |
| `np.allclose(arra[idx], arrb[idx], rtol=0, atol=0)` | `rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt)` (**opaque**) | the per-row closeness test: an UNCHANGED callee, applied once per row to the two WHOLE stored sequences. No property of it is stated or assumed. The third argument is its DOMAIN, supplied by the caller and erased at runtime — the call itself is the two-argument one the branch makes; see "Refinement domain" |
| “`np.allclose` has an answer on this pair of rows (does not raise)” | `rowsComparable xs ys`, carried by the reporter argument `hcmp` | equal lengths, or one side of length 1 — numpy's 1-D broadcast domain, measured |
| the differing-row index list `diffs[0]` | `result : List Nat` | increasing list of differing row indices |
| `np.where(arra != arrb)` (fixed-shape else branch) | `elementwiseDiff arra arrb (hfix …)` (**opaque**) | UNCHANGED routine; not taken on the VLA branch. Its second argument is its own domain, likewise supplied and erased |
| “`np.where(arra != arrb)` has an answer on this pair of columns (does not raise)” | `rowsAreFixedShape arra arrb`, carried by the reporter argument `hfix` | each column a rectangular block (the same number of stored values in every one of its rows), the two of the same number of rows, and the two block widths ones the comparison relates (equal, or one of them 1, which it broadcasts) — the shape of column pair the flat comparison reports on, owed only where the format is not variable-length, measured |

## Refinement domain (faithfulness boundary — pinned)

The per-row test is ABSTRACTED, not refined, so there is no
`np.allclose ↔ some Lean predicate` equation to defend and the model claims
nothing about tolerances, magnitudes or `float64` rounding. Two facts about it
ARE claimed, and both are measured at `rtol=atol=0` (G-CONF legs `report` and
`domain`, run INSIDE the instance image, whose numpy is 1.25.2; the exhaustive
length sweep was also run on numpy 2.2.6 and agrees, so the domain claim is not
a one-version accident). A third fact, of the OTHER callee, is claimed the same
way and measured by the `flat-domain` leg:

1. **Applicability.** `np.allclose` on two 1-D integer rows answers exactly when
   their lengths are equal or one of them is 1, and raises `ValueError` otherwise.
   `rowsComparable` is that predicate, and the contract demands a report only for
   columns all of whose rows are comparable. Exhaustively checked over every pair
   of row lengths 0..4 (900 pairs, 0 mismatches) and again over the G-CONF grammar
   (359 994 rows, 0 mismatches). Confirmed once more against the REAL routine
   rather than a replica: `TableDataDiff` on a `QJ` column whose row is `[1, 2]`
   against `[3, 4, 5]` raises
   `ValueError: operands could not be broadcast together with shapes (2,) (3,)`,
   so on an incomparable row the routine has no output to be faithful to.
2. **Report shape.** Given the test's verdicts, the report is
   `[idx for idx in range(len(arra)) if not verdict(idx)]` — the full row domain,
   increasing order, nothing dropped or added. This is what the `report` leg
   checks, with the opaque callee instantiated by the real test (72 752 columns,
   0 mismatches).
3. **Applicability of the FLAT comparison.** The branch that consults
   `np.where(arra != arrb)` is the one the format has already declared NOT
   variable-length, so the storage it faces is the storage astropy gives an
   ordinary fixed-shape column: a rectangular numeric BLOCK, one row per table row
   and the same number of stored values in each — not the object array of per-row
   arrays that variable-length storage uses. On two such blocks the elementwise
   `!=` is elementwise and `np.where` reports, however many values a row holds;
   numpy also relates a block of width 1 to one of width *n*, broadcasting the
   single value across the row. What it has no answer for is a RAGGED pair, which
   has no block at all (`np.asarray` refuses it: `ValueError: setting an array
   element with a sequence. The requested array has an inhomogeneous shape`), or
   two blocks of widths it cannot relate (`operands could not be broadcast
   together`). `rowsAreFixedShape` is that predicate — equal row counts, each
   column of one width, and the two widths related by the same rule
   `rowsComparable` states — and the contract demands the flat report only where
   the format already says the column is not variable-length. A `dim=`-shaped
   column (the FAIL_TO_PASS fixture's `Column('C', format='4I', dim='(2,2)', …)`)
   is such a block with its per-row values arranged in further axes; the model's
   `List Int` row is that row's stored values, flattened. Flattening cannot change
   whether the comparison ANSWERS — both columns are reshaped by the same declared
   `dim`, so the two blocks have the same shape either way — and it cannot change
   what the report is, because the report is pinned to be the opaque routine's own
   result rather than described. Measured over the
   G-CONF `flat-domain` leg on EVERY non-VLA column pair its grammar generates,
   with no shape excluded: 36 015 pairs, 0 mismatches, 10 858 of them in domain.
   Run twice, and the two runs agree to the digit: IN the instance image, whose
   numpy is 1.25.2 (the gate prints `numpy_version` with the counts), and out of it
   on numpy 2.2.6 — so no count here is a one-version accident. Of those pairs
   16 516 hold an empty row — a shape no FITS format realizes, counted rather than
   excluded, since a width-0 block's comparison answers or raises like any other
   and never takes an array's truth value. The same leg also runs an EXHAUSTIVE
   sub-check over every column pair of 1-3 rows with per-row widths 0-3
   (`flat_domain_exhaustive`): at equal row counts, which is the modeled domain
   because `TableDataDiff._diff` returns before the per-column loop when the two
   tables' row counts differ, 4 368 pairs and 0 mismatches; at unequal row counts,
   2 688 pairs of which 40 are ones numpy answers on (it broadcasts a one-row block
   across the other column's rows) and the predicate refuses. That last figure is a
   real gap and is reported rather than argued away: it costs the spec no strength,
   since `columnDiffRowsContract` hypothesizes `arra.length = arrb.length` and so
   demands nothing at unequal row counts, but the predicate is narrower than the
   routine there.

   An earlier revision of this predicate said instead "one stored value per row in
   both columns", justified by the `ValueError: The truth value of an array with
   more than one element is ambiguous` that the instance's own reproducer shape
   `[[0], [0, 0]]` raises. That measurement was taken against the WRONG storage:
   object arrays of per-row arrays, which is how a variable-length column is held,
   not a fixed-shape one. It made the predicate false at every ordinary
   multi-valued column — a `4I` column with `dim='(2,2)'`, for instance — and since
   the predicate is the domain argument `hfix` supplies, `∀ hfix, …` demanded
   NOTHING there: the postcondition it gates was unreachable, and a reporter
   answering `[]` on such a column satisfied the contract. That is the hole this
   revision closes.

An earlier revision of this bundle instead refined the per-row test to
whole-sequence inequality, `arra[idx]! ≠ arrb[idx]!`, and asserted that this was
EXACT on "integer VLA columns whose row `idx` holds sequences of equal length in
the two columns (the shape FITS produces for a common column)". That domain claim
was the defect: a variable-length column's whole point is that its rows are stored
at different lengths, the instance's own problem statement uses
`array=[[0], [0, 0]]`, and on such a row `np.allclose` broadcasts a single stored
value against the other side and reports AGREEMENT where sequence inequality
reports a difference. Measured on the widened grammar: 13 538 rows and 12 170
whole columns where the two disagree (G-CONF leg `abstraction-necessary`, e.g.
row `[0, 0]` vs `[0]` — sequence-unequal, `allclose`-agreeing). Abstracting the
test and moving its applicability into `rowsComparable` is what removed that
claim; the old model is now carried as the reject case
`compare-rows-by-structural-equality` in `properties.py`.

Floating VLA data is handled by the separate floating branch (diff.py:1448) and is
outside this model. G-CONF draws the integer-VLA grammar, now with per-row lengths
drawn independently for the two columns.

## Callee provenance / flag deps

No unchanged callee is consumed as an axiom. Two `opaque` declarations, both for
routines this patch does not modify and neither carrying any stated property:

- `rowsAgree` — the per-row `np.allclose` closeness test, called once per row by
  the branch the patch enables;
- `elementwiseDiff` — the flat `np.where(arra != arrb)` comparison on the
  fixed-shape branch, which the modeled VLA domain never takes.

Each takes its own DOMAIN as a further argument (`rowsComparable` per row,
`rowsAreFixedShape` per column pair). That is not a property of the callee and
not an assumption about it: it is a fact the caller must already hold to have a
question to ask, and holding it is what the reporter's own `hcmp` / `hfix`
arguments provide. Both are `Prop`s, so both erase — the emitted calls are the
two-argument ones the repository makes. The point of siting them here rather than
as side conditions on the postcondition is that a call outside a partial callee's
domain then cannot be written at all, whereas a side condition leaves it writable
and its opaque value cancels out of the comparison.

The proof consumes no property of either, so there is no `axiom`, no `sorry` and
no assumption declaration anywhere in the bundle, and G-AX is a skip stub. Where a
falsification witness needs one of these callees' values it states it as a local
hypothesis of that witness and pays for it with the gate's consistency probe. No
flag dependencies.

## G-CONF fuzz seed

`SEED = 14539`, `N = 120_000` (also pinned in `conformance_check.py`). Four legs:
`report` (report shape), `domain` (`rowsComparable` ⟺ the real per-row test
answers), `flat-domain` (`rowsAreFixedShape` ⟺ the real flat comparison answers on the
two columns as fixed-shape storage holds them, over the non-VLA formats that reach
it and with no shape excluded; the leg also FAILS unless the sample holds both
kinds of pair, so it cannot pass vacuously) and `abstraction-necessary` (the
rows where the previous revision's sequence-equality model diverges from the real
test — the leg FAILS if the grammar stops reaching them, so the evidence for the
abstraction cannot go stale unnoticed).
