# mapping.md — astropy__astropy-14539

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c0a24c1dc957a3b565294213f435fefb2ec99714`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `astropy/io/fits/diff.py` — the per-column comparison
loop of `TableDataDiff._diff` (body around line 1437–1465 @ base_commit).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `diffVLAColumn (fmt) (col) (rows)` | one iteration of the `for col in self.common_columns:` body that computes `diffs` for a single column (`astropy/io/fits/diff.py:1437–1465`) | the modeled changed function: choose the comparison route for one column (by its format) and produce its per-row difference verdict — or let the failure escape when the route does not match the column's element kind |
| `isVLA (fmt : List Char)` *(deep model — A-reference)* | the format test `"P" in col.format or "Q" in col.format` (`diff.py:1452` post-patch) | pure spec: the format-based classification that CHOOSES the route (row-wise iff a VLA marker is present) |
| `Column.varLength` | whether the column is intrinsically variable-length — its elements are themselves sequences, i.e. **object dtype** (`arra.dtype == object`) | pure spec: the intrinsic kind that determines whether the generic route can complete (`varLength && anyMulti` makes `np.where` raise) |
| `Column.numComparable` | whether the column's elements are comparable by numeric closeness — a numeric/bool dtype, or an object-VLA column whose sub-arrays are numeric (NOT a text/byte `"*A"` column) | pure spec: the intrinsic kind that determines whether the **row-wise** numeric-closeness route can run (`np.allclose` raises on non-numComparable elements) |
| `rowResult (rows : List Row)` | the row-wise difference list the VLA branch builds: `[idx for idx in range(len(arra)) if not np.allclose(arra[idx], arrb[idx], rtol, atol)]` reduced to the per-row `differs` flags (`diff.py:1453–1461`) | pure spec: the per-row difference verdict either completing route produces |
| `anyMulti (rows : List Row)` | whether some row holds >1 element — together with intrinsic VLA-ness (object dtype, `varLength`) it is the property that makes `np.where(arra != arrb)` raise (`diff.py:1463`, the `else` branch) | pure spec: the multi-element half of the generic route's failure condition (`varLength && anyMulti rows`) |
| `rowWiseOutcome col rows` | the VLA branch's `np.allclose` row-wise comparison and the `DTypePromotionError` it raises on a non-numeric (text) column | pure spec: the row-wise route's outcome — `ok(rowResult)` iff `numComparable`, else the escaping failure |
| `genericOutcome col rows` | the `else`-branch generic route `np.where(arra != arrb)` and the `ValueError` it raises on an object-dtype multi-element column | pure spec: the generic route's outcome — the escaping failure iff `varLength && anyMulti`, else `ok(rowResult)` |
| `DiffErr.ambiguous` *(outcome model)* | EITHER the `ValueError("…truth value…ambiguous…")` `np.where(arra != arrb)` raises on an object-dtype (VLA) multi-element row, OR the `DTypePromotionError` `np.allclose` raises on a non-numeric (text) column | the failure that escapes when a column is sent down a route its element kind does not support (the spurious-difference symptom the public issue reports) |

The pre-patch repo behavior the change fixes (refinement audit only, not in the
consumer spec view): the format test was `"P" in col.format` only, so a column
whose format carries `Q` but not `P` (e.g. `QJ`, `QD`) fell through to the
generic `np.where(arra != arrb)` route, which raises on multi-element VLA rows.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `col.format` (a FITS format descriptor string, e.g. `"QJ(2)"`, `"PI(2)"`, `"D"`) | `fmt : List Char` | `s` (Python str) ↔ `s.toList`; `"P" in s` ↔ `s.contains 'P'`; `"Q" in s` ↔ `s.contains 'Q'` (substring-of-a-single-char ≡ membership) |
| the column's intrinsic element kind (its numpy dtype class) | `col : Column` with `varLength`, `numComparable` | `col.varLength` ↔ `arra.dtype == object` (the elements are themselves variable-length sub-arrays — the intrinsic VLA-ness, distinct from the format-based `isVLA fmt` classifier); `col.numComparable` ↔ the elements are comparable by numeric closeness (a numeric/bool dtype, or an object column whose sub-arrays are numeric) — i.e. `np.allclose` does NOT raise on them (a `"*A"` text column has `numComparable = false`). G-AX checks both bijections. |
| one column-row of `arra`/`arrb` (a VLA element: a 1-D numpy array, possibly length 0/1/≥2) | `Row` with `differs`, `multiElem` | `r.differs` ↔ `not np.allclose(arra[i], arrb[i], rtol, atol)` (the row's contents differ); `r.multiElem` ↔ `len(arra[i]) > 1` (the row holds more than one element) |
| the column's two arrays `arra`, `arrb` aligned row-by-row | `rows : List Row` | row `i` ↔ `rows[i]`; `len(arra)` ↔ `rows.length` |
| `diffs` = the set of differing row indices, OR the `ValueError` the generic route raises | `Except DiffErr (List Bool)` | `Except.ok v` ↔ a completed comparison whose per-row `differs` verdict is `v` (the differing indices are `{i | v[i]}`); `Except.error DiffErr.ambiguous` ↔ the generic route raising the "truth value … ambiguous" `ValueError` |

Notes that fix the abstraction boundary (so the model is neither too strong nor
too weak):

* **Why object/VLA columns and not the floating branch.** The patched `elif`
  (`"P" in col.format or "Q" in col.format`) is reached only when the *prior*
  `if np.issubdtype(arra.dtype, np.floating) and np.issubdtype(arrb.dtype, …)`
  is false. VLA (`P`/`Q`) columns have **object** dtype (confirmed in-container:
  `_VLF([...], dtype=object)`), so they never satisfy the floating guard; the
  patch does not touch that guard and the floating branch is out of scope. The
  model abstracts a column to `(fmt, rows)` and the dispatch begins at the
  `isVLA` test, faithfully (refinement.md §A).
* **The generic route's outcome is observed, not assumed.** `np.where(arra !=
  arrb)` raises the "truth value … ambiguous" `ValueError` exactly when the column
  is intrinsically variable-length (object dtype — `col.varLength`) AND some row
  holds >1 element (`anyMulti rows`). A column that is NOT object dtype —
  including a regular fixed-multidim block such as `2J`/`3I` whose rows hold >1
  element — never raises; its element-wise comparison completes and yields the
  same differing-index set as the row-wise route. The failure guard is therefore
  `col.varLength && anyMulti rows`, NOT `anyMulti rows` alone (confirmed
  in-container; `2J`-multi completes). Both halves — the raising case on VLA
  multi-element columns and the completing case on non-VLA multidim columns — are
  G-AX–checked against real numpy (axiom_check.py fact 3).
* **The row-wise route's outcome is observed, not assumed.** The row-wise branch's
  `np.allclose(arra[idx], arrb[idx], …)` RAISES (a `DTypePromotionError`) on a
  column whose elements are not comparable by numeric closeness — a text/byte
  `"*A"` column (`col.numComparable = false`); on every numerically-comparable
  column (numeric/bool, or an object-VLA column whose sub-arrays are numeric) it
  completes with the per-row `differs` verdict. The row-wise-route guard is
  therefore `col.numComparable` (G-AX fact 2). This is WHY the route choice
  matters and why "compare every column row-wise" is wrong: a text column MUST
  take the generic route. Every intrinsically-VLA (object) column is numComparable
  (its sub-arrays are numeric), so the columns the classifier sends row-wise all
  complete.
* **Why no failure escapes post-patch.** The classifier `isVLA fmt` equals the
  intrinsic `col.varLength` (object dtype) — G-AX fact 4 — so every VLA column is
  sent row-wise (and is numComparable, so completes) and every non-VLA column is
  sent generic (and is non-object, so `varLength && anyMulti` is false, so
  completes). Each column is sent down a route its element kind supports; the
  comparison always completes.
* `rtol`/`atol` and the `numdiffs`/`islice` reporting cap are unchanged by the
  patch and observationally irrelevant to WHICH route is taken or whether the
  generic route raises; they are folded into the per-row `differs` flag (the
  row-wise verdict) and omitted from the model carrier.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There is **no consumed axiom** in this bundle (directive 7): the changed control
flow (the route choice) is modeled directly and the two route behaviors are
**deep models** validated against the real numpy operations. What G-AX
establishes are the **A-reference** facts that make those deep models faithful
and the modeled failure non-vacuous.

### 3.1 `isVLA` deep model ↔ the real format test; `Column.varLength` ↔ object dtype (A-reference)
**Callee:** the unchanged Python expression `"P" in col.format or "Q" in
col.format`. `isVLA fmt = fmt.contains 'P' || fmt.contains 'Q'` transliterates it
verbatim under the `str ↔ List Char` bijection (§2). G-AX builds real columns of
many formats and asserts `isVLA(col.format) == ("P" in col.format or "Q" in
col.format)` and, additionally (**fact 4**), that the classifier equals the
column's intrinsic kind: `isVLA(col.format) == (arra.dtype == object) ==
col.varLength`. This equality is what makes the route faithful to the element
kind, so every column is sent down a route it supports.

### 3.2 `rowWiseOutcome` / `genericOutcome` / `DiffErr.ambiguous` ↔ the two routes (A-reference)
**Callees:** the two unchanged comparison routes:
  * row-wise: `[idx for idx in range(len(arra)) if not np.allclose(arra[idx],
    arrb[idx], rtol, atol)]`;
  * generic: `np.where(arra != arrb)`.

G-AX runs BOTH routes on real columns (VLA `P`/`Q`, non-VLA scalar/fixed-multidim,
and text `"*A"`) over boundary + fuzzed data and asserts:
  1. **row-wise completes iff `col.numComparable`** (`fact 2`): on a numerically-
     comparable column (numeric/bool, or an object-VLA column with numeric
     sub-arrays) `np.allclose` completes and its differing-index set equals
     `{i | rows[i].differs}` (the `rowResult` model); on a non-numComparable
     **text** column it RAISES (`DTypePromotionError`) — the `DiffErr.ambiguous`
     outcome of `rowWiseOutcome`. Every intrinsically-VLA column is numComparable,
     so the columns the classifier sends row-wise all complete. This is what makes
     "compare every column row-wise" wrong: a text column must take the generic
     route.
  2. **generic raises iff the column is intrinsically VLA (object dtype) AND some
     row is multi-element** (`col.varLength && anyMulti rows`) (`fact 3`): on a
     non-object column — scalar, fixed-multidim (e.g. `2J`), or text — it
     completes and yields the SAME differing-index set as the row-wise route (when
     that route also completes); only on an object-dtype column with a length-≥2
     row does it raise `ValueError` (the `DiffErr.ambiguous` outcome of
     `genericOutcome` — exactly the spurious-difference failure the public problem
     statement reports, modeled as `error` so the spec pins that a VLA column
     NEVER takes this failing route). G-AX exercises both legs, including non-VLA
     fixed-multidim columns that must complete.

Imports only `numpy` + the astropy under test. Exit 0 iff every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14539`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`isVLA` (route choice) to Python and runs the REAL row-wise (`np.allclose`) and
generic (`np.where`) routes for the chosen branch, comparing the outcome against
the gold-patched real `TableDataDiff._diff` behaviour on real FITS columns of
every relevant format — VLA (`P`/`Q`), non-VLA scalar/fixed-multidim, and text
(`"*A"`) columns that must be routed generic.
