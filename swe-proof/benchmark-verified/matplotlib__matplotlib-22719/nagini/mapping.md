# mapping.md — matplotlib__matplotlib-22719

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a2a1b0a11b993fe5f8fab64b6161e99243a6393c`, states the type
abstraction, and documents the per-element classifier callees the model
abstracts into its input flags.

Repo file under change: `lib/matplotlib/category.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `should_warn_numeric_passthrough(flags)` | `StrCategoryConverter.convert(value, unit, axis)` — `lib/matplotlib/category.py:28` (decision at body line 61) | modeled changed function: decides whether the numeric-pass-through deprecation advisory is emitted |
| `should_log_numeric_strings(flags)` | `UnitData.update(self, data)` — `lib/matplotlib/category.py:209` (decision at body line 233) | modeled changed function: decides whether the all-parsable-as-numbers informational advisory is logged |
| `all_classify(s)` | the whole-sequence universal property `all(... for v in values)` (convert, `category.py:58-60`) / the `convertible` left-fold over unique values (update, `category.py:224-230`) | pure spec: every element satisfies the per-element classifier (vacuously `True` on the empty sequence) |
| `flags` parameter | `values = np.atleast_1d(np.array(value, dtype=object))` (convert, line 55) / `data = np.atleast_1d(np.array(data, dtype=object))` (update, line 222) | the value sequence, each element abstracted to its per-element classification flag |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `values` / `data`: a numpy object array (`np.atleast_1d(np.array(.., dtype=object))`) of arbitrary Python values | `List[int]` of per-element classification flags | element `v_k` ↔ `flags[k]` where `flags[k] != 0` iff `v_k` satisfies the site's per-element predicate (see §3); `values.size`/`data.size` ↔ `len(flags)`; an empty input array ↔ `[]` |
| the per-element predicate result for one value | the sign of one `int` flag (0 = predicate false, non-zero = predicate true) | a single classification bit, computed by the unchanged classifier of §3 |
| the whole-sequence "every element classifies" verdict (`all(...)` in convert / the `convertible` accumulator in update) | `all_classify(ToSeq(flags))` | universal quantification over the flag sequence; `True` on the empty sequence in BOTH the model and numpy/Python (`all([])` is `True`; an unentered loop leaves `convertible` at its `True` seed) |
| `values.size and is_numlike` (convert, post-patch line 61) / `data.size and convertible` (update, post-patch line 233) | `len(flags) > 0 and all_classify(ToSeq(flags))` (the return of each decision function) | the booleanised emit decision; `np.ndarray.size > 0` ↔ `len(flags) > 0` |

`str` indexing / numpy arrays are not expressible in Nagini's fragment, so the
value sequence is carried as `List[int]` flags and the specification is phrased
over `PSeq[int]` via `ToSeq`.

## 3. Per-element classifier provenance (abstracted into the input flags — R)

The per-element predicate is an **unchanged** classifier at each site; the patch
does not touch it. The model abstracts each element's classifier result into the
input flag (`flags[k] != 0`), so there is **no consumed `@ContractOnly` axiom**:
the only operation the patch changes — the non-emptiness guard — is modelled
deeply (`len(flags) > 0 and ...`), and the universal "all classify" property is
spelled out by the front-recursive fold `all_classify`. The classifiers are
documented here for the G-AX behavioural check (`axiom_check.py`), which
confirms the *vacuous-truth* property the model relies on against the real
Python/NumPy semantics.

### 3.1 convert — per-element numeric classification
**Classifier:** `units.ConversionInterface.is_numlike(v) and not isinstance(v, (str, bytes))`
(`lib/matplotlib/category.py:58-60`, calling `is_numlike` at
`lib/matplotlib/units.py:136`). `is_numlike` is itself `@_api.deprecated("3.5")`
and is invoked inside `with _api.suppress_matplotlib_deprecation_warning():`.
The whole-sequence verdict is `is_numlike = all(<predicate> for v in values)`.
For the **empty** `values` array, `all(<empty generator>)` is `True` (Python
semantics) — the source of the spurious advisory the patch fixes by adding the
`values.size` conjunct.

### 3.2 update — per-element string-parsability classification
**Classifier:** `UnitData._str_is_convertible(val)` (`lib/matplotlib/category.py:194-207`),
true iff `val` parses as a `float` or, failing that, as a date
(`dateutil.parser.parse`). The whole-sequence verdict is the `convertible`
accumulator: seeded `True`, updated to `_str_is_convertible(val)` while still
`True`, over the unique values `OrderedDict.fromkeys(data)`
(`category.py:224-230`). For **empty** `data` the loop never runs, leaving
`convertible == True` — the source of the spurious info advisory the patch fixes
by adding the `data.size` conjunct. (Length-non-emptiness of `data` equals
length-non-emptiness of its unique set, so `data.size` is the faithful guard.)

## 4. G-AX behavioural check

`axiom_check.py` imports only the standard library (`numpy`, the very array
layer the patched code uses, plus `random`). It confirms the load-bearing
semantic facts the deep model rests on, against the real runtime:

  * `all(<predicate> for v in values)` and the `convertible` left-fold are both
    `True` on the empty input (the vacuous-truth fact `all([]) == True`), so the
    pre-patch decision `is_numlike` / `convertible` alone would emit the
    advisory on empty input;
  * the patched decision `values.size and is_numlike` / `data.size and
    convertible` is `False` on empty input and equals
    `len(flags) > 0 and all_classify(flags)` (the model's `Ensures`) on a fuzz
    of non-empty inputs;
  * `np.atleast_1d(np.array([], dtype=object)).size == 0` ↔ `len(flags) == 0`,
    confirming the `values.size`/`data.size` ↔ `len(flags) > 0` bijection.

Exit 0 iff every observation matches the model.
