# mapping.md — astropy__astropy-14539

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c0a24c1dc957a3b565294213f435fefb2ec99714`, states the type
abstraction, and gives the provenance of each deep-model reference (callee
source + the exact behaviour validated by G-AX). There are NO consumed axioms.

Repo file under change: `astropy/io/fits/diff.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `count_differing_rows(fmt, row_mismatches)` | the per-column body of `TableDataDiff._diff` — `astropy/io/fits/diff.py:1429-1465` (the changed `elif` at line 1452; the `diffs`/`set(diffs[0])` accumulation at 1453-1465) | the modeled changed behaviour: how many rows of one column differ |
| `is_vla_descriptor(fmt)` *(deep model — A-reference)* | the layout-string test `"P" in col.format or "Q" in col.format` (`diff.py:1452`, post-patch) | pure spec: does the column's layout descriptor mark a variable-length array |
| `contains_cp(s, cp)` | the Python `in` substring/membership test on `col.format` | pure spec helper: code-point membership |
| `row_granular_count(m)` *(deep model — A-reference)* | the per-column accumulation `self.diff_total += len(set(diffs[0]))` (`diff.py:1465`), which is row-granular on BOTH branches | pure spec: number of rows with ≥1 differing element |
| `compare_row_aware(fmt, m)` | the variable-length `elif` body `diffs = ([idx for idx in range(len(arra)) if not np.allclose(arra[idx], arrb[idx], rtol, atol)],)` then `len(set(diffs[0]))` (`diff.py:1453-1461,1465`) | the row-aware comparator; applicable only to a VLA column (its invocation domain — its per-row closeness inspection raises on non-numeric fixed-width columns, so it is NOT applicable to an arbitrary column); returns the row-granular count |
| `compare_elementwise(fmt, m)` | the ordinary `else` body `diffs = np.where(arra != arrb)` then `len(set(diffs[0]))` (`diff.py:1462-1465`) | the element-wise comparator; ALSO row-granular; applicable only to a non-VLA (regular ndarray) column — raises on a VLA object array |
| `row_mismatches` (parameter) | the per-row element-mismatch summary of the two columns `arra = self.a[col.name]`, `arrb = self.b[col.name]` (`diff.py:1445-1446`) at `rtol=atol=0` | carrier: `row_mismatches[i]` = #positions where the two sub-arrays of row i differ |

The pre-patch repo symbol the change widens: the `elif "P" in col.format`
guard (`diff.py:1452`, pre-patch), which omitted `"Q"`. `P`/`Q` are the FITS
variable-length-array descriptor letters (`_FormatP`, code `"P"`,
`astropy/io/fits/column.py:429-437`; `_FormatQ`, code `"Q"`, 64-bit,
`astropy/io/fits/column.py:474-479`); the column-format regex admits both:
`[LXBIJKAEDCMPQ]` (`column.py:201`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `col.format` (a `str`, e.g. `"PI(2)"`, `"QJ(2)"`, `"D"`) | `fmt: List[int]` of Unicode code points | `ch ∈ s` ↔ `ord(ch) ∈ fmt`; specifically `"P" → 80`, `"Q" → 81` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) via `ToSeq` | `ToSeq(fmt)` materialises the list; `PSeq` `len`/`[i]`/`drop` mirror `str` `len`/index/slice |
| a VLA column = `arra`/`arrb` object arrays of sub-arrays (`self.a[col.name]`) | per-row mismatch summary `row_mismatches: List[int]` | `row_mismatches[i]` = number of positions of row i that the per-position verdict of the comparator APPLICABLE to the column rejects, counted under the SAME alignment that comparator uses (numpy's own), NOT a length penalty; so `row_mismatches[i] == 0` iff the real comparator judges row i close. The grounding is BRANCH-RELATIVE because the two real branches do not share a per-position verdict: row-aware uses `np.isclose` (whose conjunction IS `np.allclose`), element-wise uses the plain `arra != arrb`. Unequal-length sub-arrays that still align are in-domain and a length difference alone is not a difference; a pair with no alignment is out of domain (the real comparator raises, and the grounding raises identically) |
| `np.allclose(arra[idx], arrb[idx], rtol=0.0, atol=0.0)` | rejection by the comparator's own per-position closeness verdict at every aligned position | at the constructor defaults `rtol=atol=0.0` (`diff.py:221-222`, `TableDataDiff.__init__`) `allclose` reduces to `all(isclose(...))`, i.e. per-position closeness — which is NOT exact equality on the integer domain. `allclose` evaluates `abs(a-b) <= atol + rtol*abs(b)` in float64 whatever the tolerances, so its significand is narrower than the int64 range: at and above `2**53` it cannot separate neighbouring int64 values and reports them close where `!=` reports a difference (`float(2**53) == float(2**53+1)`). The bridge therefore grounds this row in `~np.isclose(...)`, not in `!=`, so `row_mismatches[i] == 0` means exactly what `np.allclose` means. This degeneracy is a property of the real comparator on the 64-bit magnitudes the `Q` descriptor exists to carry, so it is modelled rather than excluded, and no `--float-encoding` is needed (the model never reasons about the float arithmetic itself — only the per-row verdicts it produces are carried) |
| `self.diff_total += len(set(diffs[0]))` (per-column) | `count_differing_rows` returns the single column's contribution | the column's contribution to the running total; F2P tests observe `diff_total` and `diff_ratio = diff_total / total_values` |

`str` indexing/iteration is banned in Nagini, so the layout descriptor is
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model references (kind A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms** (`axioms` region empty). The
two changed operations are modelled deeply and validated against the real
callees out-of-band.

### 3.1 `is_vla_descriptor` ↔ `"P" in col.format or "Q" in col.format` (A-reference)
**Callee:** Python `str.__contains__` on `col.format`, exactly as written at
`astropy/io/fits/diff.py:1452` (post-patch). The model encodes the membership of
code points `80` ('P') and `81` ('Q') in the format's code-point sequence. The
descriptor letters are uppercase in the materialised format string (`_FormatP`
`_format_code = "P"`, `column.py:437`; `_FormatQ` derives from it with code
`"Q"`, `column.py:474-479`), and the test is the case-sensitive substring `in`,
so uppercase `P`/`Q` is the correct configuration (cf. an `html.escape`-style
flag dependency). **G-AX:** `axiom_check.py` asserts
`is_vla_descriptor(fmt) == ("P" in fmt or "Q" in fmt)` on 25 boundary FITS
formats (every scalar code `LXBIJKAEDCM`, both VLA descriptors with options,
empty) + 20000 randomized format strings.

### 3.2 `row_granular_count` ↔ the `diff_total` accumulation on BOTH branches; comparator applicability (A-reference)
**Callee:** the per-column accumulation in `TableDataDiff._diff`
(`astropy/io/fits/diff.py:1452-1465`):
```python
elif "P" in col.format or "Q" in col.format:
    diffs = ([idx for idx in range(len(arra))
              if not np.allclose(arra[idx], arrb[idx],
                                 rtol=self.rtol, atol=self.atol)],)
else:
    diffs = np.where(arra != arrb)
self.diff_total += len(set(diffs[0]))
```
**Both branches feed the identical `self.diff_total += len(set(diffs[0]))`**,
which is row-granular: `set(diffs[0])` is the set of distinct differing ROWS.
There is only ONE discipline in the real code, modelled by `row_granular_count`
(a row contributes 1 iff `row_mismatches[i] > 0`) — *not* an element sum.

* **Row-aware path** (`compare_row_aware`, used when the descriptor designates
  variable length): after `set(diffs[0])` it is the rows that are not
  close — rows with ≥1 disagreeing aligned position == `row_granular_count`
  (closeness is judged under `np.allclose`'s own alignment of the two
  sub-arrays, so a mere length difference is not a difference; §2).
  **Applicability:** this comparator's per-row `np.allclose` inspection is
  defined only on its invocation domain (VLA columns); handed an ordinary
  column whose stored values are non-numeric it raises, so an arbitrary
  column must NOT be routed here. model.py encodes it as `compare_row_aware`'s
  precondition `Requires(is_vla_descriptor(...))`.
* **Element-wise path** (`compare_elementwise`, the `else`): `np.where(arra !=
  arrb)` returns per-element index tuples; `set(diffs[0])` collapses them to
  distinct rows, so this is ALSO row-granular — even on a multi-dimensional
  fixed-width column where a partial-row diff would make a naive element sum
  diverge. **Applicability:** this comparator is valid only on a regular
  (non-object) ndarray column; handed a genuine VLA column (an object array of
  multi-element sub-arrays) `arra != arrb` yields an array of arrays and
  `np.where`/the truth test RAISES `ValueError`. This is why a VLA column must
  be recognised and routed to the row-aware path; model.py encodes it as
  `compare_elementwise`'s precondition `Requires(not is_vla_descriptor(...))`.

**G-AX:** `axiom_check.py` (a) grounds `row_mismatches` from real sub-arrays and
asserts `row_granular_count == real row-aware np.allclose path` on the F2P data
(identical `QJ(2)` → 0; differing `QJ(2)` → 2; the issue's ragged `QD` identical
→ 0), 7 pinned unequal-length-but-aligning boundary rows, and 20000 randomized
integer VLA columns whose per-side sub-array widths are drawn INDEPENDENTLY, so
unequal-length rows are inside the validated domain and the run fails if that
class is never exercised (A-ref 2a); (b) asserts
`row_granular_count == real element-wise np.where path` on multi-element
fixed-width columns, requiring that some column genuinely distinguishes a row
count from an element sum so the check is non-vacuous (A-ref 2b); (c) asserts the
element-wise `np.where` path RAISES on multi-element VLA object-array columns
(A-ref 2c, grounding the applicability precondition). numpy is a core astropy
dependency present in the evaluation container; `axiom_check.py` imports only the
standard library and numpy.

## G-CONF — differential conformance (`conformance_check.py`)

**Pinned seed: `SEED = 14539`.** Input count: 37 boundary columns + seeded fuzz
to **100000 checked** column pairs (`N_TARGET = 100_000`). Generator is a
`random.Random(SEED)` (no hypothesis), so the verdict is reproducible from the
seed alone.

**Shadow (provenance `direct` — on nagini the model IS Python).** The
`# impl-start`/`# impl-end` regions of all three contracted functions
(`count_differing_rows`, `compare_row_aware`, `compare_elementwise`), copied
verbatim with only the contract calls deleted (`Requires`/`Ensures`/`Invariant`/
`Assert`/`MustTerminate`/`Acc` and the `# invariants-start|end` markers). The two
comparator bodies are kept as two separate byte-identical copies exactly as
model.py has them. Dependencies come across contract-free: the whole
`# pure-start`/`# pure-end` region (`contains_cp`, `is_vla_descriptor`,
`row_granular_count`) plus a `PSeq`/`ToSeq` shim realizing the Nagini carriers as
an immutable tuple sequence. No `@ContractOnly` callee exists in this bundle
(§3), so nothing is axiomatized-and-assumed.

**Oracle: CALLED, not transliterated.** The real gold-patched per-column body of
`TableDataDiff._diff` (`astropy/io/fits/diff.py:1429-1465`, §1) is driven on two
real one-column tables built with `fits.BinTableHDU.from_columns` /
`fits.Column`; the single common column makes `TableDataDiff(...).diff_total`
exactly that column's contribution — the quantity `count_differing_rows`
returns. The format test, route choice, per-row `np.allclose`, `np.where` and the
`len(set(diffs[0]))` accumulation are all the patched repo's own code.
`numdiffs=0` only skips the `diff_values` bookkeeping at 1467-1485, which runs
after the modeled accumulation at 1465.

**Type bridge (§2, inverted).** Generation runs in the concrete direction —
build the real column pair, then abstract it — so every input is a genuine FITS
column and satisfies the `Requires` by construction:
`fmt = [ord(c) for c in str(ta.columns["K"].format)]` (read off the REAL
materialized column, so FITS's own padding/dtype choices cannot manufacture a
disagreement); `row_mismatches[i] = int(np.count_nonzero(asarray(arra[i]).reshape(-1)
!= asarray(arrb[i]).reshape(-1)))` over `arra/arrb = ta.data["K"]/tb.data["K"]`,
the arrays `_diff` binds at 1445-1446, at the default exact tolerances
`rtol=atol=0.0` where closeness degenerates to element equality (same grounding
as `axiom_check.py`'s `row_mismatches_of`).

**Two legs.** Each input checks BOTH the copied impl region's return value AND
the postcondition's fold `row_granular_count(ToSeq(row_mismatches))` against the
real `diff_total`, so a green G-CONF underwrites the spec, not just the impl.

**Domain exclusions** (each is a branch model.py does not model; all counted in
the report, never silently dropped):
* `nrows_a == nrows_b` — unequal row counts make `_diff` set `diff_rows` and
  return before the column loop (1409-1411), so there is no oracle.
* non-VLA **floating**-dtype columns (`E`, `D`, `2E`, ...) — they take the
  earlier, UNCHANGED `where_not_allclose` branch (1447-1451), upstream of the
  patched `elif`, so they never reach line 1452 in either the pre- or post-patch
  code. Variable-length float columns (`PD`/`QD`/`PE`/`QE`) have `object` dtype
  and are NOT excluded (exercised heavily, incl. NaN/inf).
* variable-length columns whose two sub-arrays in some row have **different
  lengths** are IN-DOMAIN whenever those lengths still align positionally: the
  real row-aware `np.allclose` judges such a row by that alignment, so a length
  difference alone is not a difference, and the bridge grounds the summary under
  the same alignment. Only a row with NO alignment is excluded (the real
  `np.allclose` raises a broadcast error, so the patched code has no defined
  value); such an input is counted (`n_skipped_ragged`), never silently dropped.
  Ragged *across* rows (the issue's own `QD` repro) is likewise in-domain and
  pinned in the boundary list.
* character variable-length columns (`PA`/`QA`) — the real row-aware comparator
  raises `DTypePromotionError` on bytes, so the patched code has no defined value
  there. Ordinary character columns `A`/`5A`/`10A` ARE included.

**Non-vacuity, enforced at runtime** (the run FAILS, not passes, if any counter
is 0): both dispatcher branches; inside each comparator the differing-row,
equal-row and zero-trip paths; at least one column per route where a naive
element SUM diverges from the row count (recorded run: 18156 VLA + 4554
element-wise); and both a Q-only and a P-only descriptor (36555 / 31497).

**Recorded verdict.** `G-CONF=pass`, exit 0, 0 disagreements over 100000 checked
column pairs (`shadow_provenance: direct`). Negative control: with the gold patch
NOT applied the same script exits 1 and reports disagreements on exactly the
Q-marked variable-length columns (the real `np.where` path raising
`ValueError: The truth value of an array with more than one element is
ambiguous`), confirming the check is capable of refuting the refinement.
