# mapping.md — scikit-learn__scikit-learn-25747

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2c867b8f822eb7a684f0d5c4359e4426e1c9cfe0`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled operation.

Repo file under change: `sklearn/utils/_set_output.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `wrapContainer (mut frame : Frame) (colSupplied) (rowSupplied) return (out : Except WrapErr Frame)` | `_wrap_in_pandas_container(data_to_wrap, *, columns, index)` — `sklearn/utils/_set_output.py:10`, the branch `if isinstance(data_to_wrap, pd.DataFrame):` (body lines 55-60) | the modeled changed function, restricted to the already-a-container branch |
| `Frame { colLabels, rowLabels }` | a `pandas.DataFrame`'s two label axes (`df.columns`, `df.index`) | the touched observable state of the container |
| `frame` (the `mut` param) | `data_to_wrap` when it already is a `pd.DataFrame` (adjusted in place, then returned) | the container handed in and back |
| `colSupplied : Option (List Lbl)` | `columns` after the callable-resolution prologue (`columns()`/None-on-raise), lines 47-51 — `some` iff the resolved value is not `None` | the optional replacement column labels |
| `rowSupplied : Option (List Lbl)` | `index` keyword argument — `some` iff not `None` | the optional row labels offered by the caller |
| `WrapErr.sizeMismatch` | pandas' `ValueError: Length mismatch` escaping from `data_to_wrap.columns = columns` (line 56-57) when the supplied set does not hold one label per existing column | the size-mismatch failure of an ill-fitting replacement label set |
| `sizeFits (supplied) (current)` | pandas' axis-assignment length check: `df.columns = labels` succeeds iff `len(labels) == len(df.columns)`; an absent (`None`) offer trivially fits (no assignment attempted) | pure spec: whether an offered replacement set can be applied |
| `resolvedCols (supplied) (current)` | the effect of `if columns is not None: data_to_wrap.columns = columns` (line 56-57) when the set fits: take supplied else keep current | pure spec: the column axis a request settles on |
| `frameAfter (frame) (colSupplied)` | the container's `(columns, index)` after the branch runs: adjusted per `resolvedCols` when the offer fits, untouched when the escaping `ValueError` aborts the assignment before any label is written | pure spec: the container state after the request |
| `wrapResult (frame) (colSupplied)` | the branch outcome: `return data_to_wrap` (success) or the escaping `ValueError` (failure) | pure spec: the overall outcome |

The patched-out repo statement (refinement audit only, NOT in the consumer spec
view): `if index is not None: data_to_wrap.index = index` (lines 58-59 at
base_commit), which the gold patch deletes.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `pandas.DataFrame`'s label axes | `Frame { colLabels, rowLabels }` | `df` ↔ `⟨list(df.columns), list(df.index)⟩`; only the two label axes are observed (the F2P test asserts on `df.index`/`df.columns`), so cell content is dropped from the carrier |
| a single label (column name / row label) | `Lbl := Nat` | label value ↔ an opaque `Nat`; only `=` and ordering are observed, never the concrete spelling, so a totally-ordered opaque carrier is exact |
| `columns` argument (post callable-resolution) | `Option (List Lbl)` | `None` ↔ `none`; a concrete label sequence ↔ `some labels`; a callable is resolved by calling it (raise ⇒ `None` ⇒ `none`) BEFORE the bijection, exactly as the gold prologue does (lines 47-51) |
| `index` argument | `Option (List Lbl)` | `None` ↔ `none`; a concrete label sequence ↔ `some labels` |
| the branch outcome | `Except WrapErr Frame` | `return data_to_wrap` ↔ `Except.ok frame`; the escaping length-mismatch `ValueError` ↔ `Except.error WrapErr.sizeMismatch` (only the failure's occurrence is observed, not its message text) |
| pandas' axis-assignment length check | `sizeFits` | `df.columns = labels` raises iff `len(labels) != len(df.columns)`; `None` ↔ `none` never attempts the assignment, so it always "fits" |
| `df.columns = cols` (in-place set, fitting) | `frame := { frame with colLabels := cols }` | sets the column axis; identity on the row axis |
| `df.columns = cols` raising | no state write (`frameAfter` = identity) | pandas validates the length BEFORE mutating, so a raising assignment leaves both axes exactly as they were |
| returning `data_to_wrap` | `return Except.ok frame` | the same container, adjusted, handed back |

Lean has no aliasing; the in-place mutation of `data_to_wrap` is modeled by the
`mut frame` parameter, and the directive-5 frame obligation (`rowLabels`
unchanged) is pinned explicitly by `ensures frame.rowLabels = frameOld.rowLabels`
(implied by, but stated separately from, `ensures frame = frameAfter frameOld
colSupplied`, since `frameAfter` never writes the row axis).

## 3. Callee provenance (kind-A)

**None.** The branch under spec performs no call whose behaviour the proof must
assume: it sets the column axis (when a replacement is supplied and fits, else
the size-mismatch failure escapes) and returns the container. The
previously-present row-axis assignment is *deleted* by the change, not delegated
to a callee. The pandas length check guarding the column-axis assignment is
modeled **deeply** as `sizeFits` in the `pure` region (validated mechanically by
G-CONF against the real assignment), so there is no consumed axiom and no
deep-model reference — `axiom_check.py`/G-AX is **skipped** (no axioms), and
G-CONF carries the full soundness load for the R/I legs.

The callable-resolution prologue (lines 47-51) and the sparse/`check_pandas_support`
prologue (lines 44-45, 53) are UNCHANGED by the patch and are not part of the
modeled branch; G-CONF runs them as-is on the real function (the oracle is the
real patched `_wrap_in_pandas_container`), so they need no separate model.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`25747`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`sizeFits`/`resolvedCols`/`frameAfter`/`wrapResult` and the row-axis frame
(R/I-tagged ops) to Python over the real `pandas.DataFrame`, and diffs the
resulting outcome — `('ok', columns, index)` on success, `('error', columns,
index)` (the untouched axes) when the size-mismatch failure escapes — against
the real patched `_wrap_in_pandas_container` over ≥10⁵ fuzzed inputs, a quarter
of the supplied column-label sets (and row-label sets) deliberately ill-fitting.
