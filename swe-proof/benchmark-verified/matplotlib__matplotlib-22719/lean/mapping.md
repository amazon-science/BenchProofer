# mapping.md — matplotlib__matplotlib-22719

## Symbol binding (file:line @ base_commit a2a1b0a11b993fe5f8fab64b6161e99243a6393c)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_numericPassthrough` / `problem_spec_numericPassthrough` | the `is_numlike` guard governing the numeric-passthrough deprecation warning inside `StrCategoryConverter.convert` | `lib/matplotlib/category.py:55-66` |
| `implementation_parsableInfo` / `problem_spec_parsableInfo` | the `convertible` guard governing the info-log inside `UnitData.update` | `lib/matplotlib/category.py:222-237` |
| `looksNumeric` (opaque) | `UnitData._str_is_convertible(val)` (parsable as `float` or a date) | `lib/matplotlib/category.py:194-207` |
| `Element` / `isNumeric` (pure) | per-element predicate `units.ConversionInterface.is_numlike(v) and not isinstance(v, (str, bytes))` over `np.atleast_1d(np.array(value, dtype=object))` | `category.py:55-60` |

## What the two functions do (base_commit)

### `StrCategoryConverter.convert` (the numeric-passthrough warning)
```python
values = np.atleast_1d(np.array(value, dtype=object))
with _api.suppress_matplotlib_deprecation_warning():
    is_numlike = all(units.ConversionInterface.is_numlike(v)
                     and not isinstance(v, (str, bytes))
                     for v in values)
if is_numlike:                         # <-- base_commit
    _api.warn_deprecated("3.5", message="Support for passing numbers ...")
    return np.asarray(values, dtype=float)
unit.update(values)
return np.vectorize(unit._mapping.__getitem__, otypes=[float])(values)
```
`is_numlike` is computed by `all(...)` over the elements of `values`. For an
EMPTY array `all(...)` is vacuously `True`, so the deprecation warning fires even
though there is nothing to convert. The fix adds a `values.size` guard:
`if values.size and is_numlike:`.

### `UnitData.update` (the parsable-strings info-log)
```python
data = np.atleast_1d(np.array(data, dtype=object))
convertible = True
for val in OrderedDict.fromkeys(data):
    _api.check_isinstance((str, bytes), value=val)
    if convertible:
        convertible = self._str_is_convertible(val)
    if val not in self._mapping:
        self._mapping[val] = next(self._counter)
if convertible:                        # <-- base_commit
    _log.info('Using categorical units to plot a list of strings ...')
```
`convertible` starts `True` and stays `True` for an empty `data` (the loop never
runs), so the info-log fires on empty input. The fix adds a `data.size` guard:
`if data.size and convertible:`.

The **bug** in both: a per-element conjunction is vacuously `True` on an empty
sequence, so a side notification fires when there is nothing to convert. The
reproduction (`ax.plot([], [])` on a categorically-united axis) drives `convert`
with an empty array; the spurious `MatplotlibDeprecationWarning` is then turned
into a `ConversionError`. The **fix** is the same in both sites: gate the
notification on the sequence being non-empty AND the flag holding.

## Lean modeling

- The modeled OUTPUT is the boolean decision *whether the notification fires* —
  exactly the value the patch changes (`is_numlike` → `values.size and
  is_numlike`; `convertible` → `data.size and convertible`). Everything else in
  the two functions (the actual warning text, the float cast, the mapping update,
  the type checks) is unchanged by the patch and orthogonal to the decision, so
  it is not modeled.
- `convert`'s site: the elements are pre-classified into `Element.numeric`
  (a non-string numeric value: `is_numlike(v) and not isinstance(v,(str,bytes))`)
  vs `Element.categorical` (everything else). `values : List Element` ≅ the
  object array `np.atleast_1d(np.array(value, dtype=object))`. The per-element
  predicate is `isNumeric`; the `all(...)` over it is `values.all isNumeric`;
  `values.size` ≅ `!values.isEmpty`.
- `update`'s site: `data : List String` ≅ the unique values iterated by
  `OrderedDict.fromkeys(np.atleast_1d(...))`. The per-element predicate
  `_str_is_convertible` is the opaque `looksNumeric`. `convertible` after the loop
  ≅ `data.all looksNumeric` (the accumulator stays `True` iff every element is
  convertible — `_str_is_convertible` is called for each element so long as the
  accumulator is still `True`, and a single `False` latches it off; this is
  equivalent to the conjunction over all elements). `data.size` ≅ `!data.isEmpty`.

  *Modeling note on `OrderedDict.fromkeys`:* the real loop deduplicates the data
  before testing `_str_is_convertible`, but `data.size` (the guard) is the size of
  the FULL (non-deduplicated) `data` array, and `all(_str_is_convertible(v) for v
  in unique(data))` has the same truth value as `all(... for v in data)` (a
  conjunction is invariant under duplicate removal). The empty-vs-nonempty
  distinction is likewise invariant: `data` is empty iff its set of unique values
  is empty. So modeling the post-dedup conjunction as `data.all looksNumeric` over
  the (already-unique) input list and `data.size` as `!data.isEmpty` is faithful
  for the decision being computed.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `np.atleast_1d(np.array(value, dtype=object))` | `values : List Element` | ordered elements; each element classified numeric/categorical |
| `is_numlike(v) and not isinstance(v,(str,bytes))` | `isNumeric v` | per-element numeric-passthrough predicate |
| `all(pred(v) for v in values)` | `values.all isNumeric` | conjunction over the list |
| `values.size` | `!values.isEmpty` | nonempty iff size > 0 |
| `bool(values.size and is_numlike)` | result of `implementation_numericPassthrough` | the decision to warn |
| `np.atleast_1d(np.array(data, dtype=object))` (unique iter) | `data : List String` | ordered (unique) names |
| `self._str_is_convertible(val)` | `looksNumeric val` | parsable-as-number-or-date predicate (opaque) |
| `convertible` after the loop | `data.all looksNumeric` | conjunction over the list |
| `data.size` | `!data.isEmpty` | nonempty iff size > 0 |
| `bool(data.size and convertible)` | result of `implementation_parsableInfo` | the decision to info-log |

## Callee provenance + flag dependencies

- **`looksNumeric` (= `UnitData._str_is_convertible`)** is an UNCHANGED callee of
  `update` (it is not touched by the patch). It is declared `opaque` and consumed
  only structurally: the decision rule depends on the per-element conjunction of
  its results, never on HOW it decides for any specific string. The proof does NOT
  consume any `looksNumeric_prop` axiom (the proof obligation is purely the
  loop-equals-conjunction reduction plus the non-empty guard), so it is an
  **A-reference signature only** — declared so it can appear in the executable
  impl, with no consumed contract. There is therefore nothing for G-AX to
  validate beyond "the callee is a total `String → Bool`", which is its declared
  Lean type; G-AX is a skip stub.
- `is_numlike` / `isinstance` (in `convert`'s predicate) are modeled by the
  data-side classification `Element.numeric` vs `Element.categorical`; the
  classification is the input, not a callee the proof reasons about.
- **No flag-dependent callee.** Both predicates are evaluated unconditionally per
  element; there is no quote-style flag to fuzz.

## G-CONF fuzz seed

Pinned LCG seed: **22719** (see `conformance_check.py` `SEED`). Corpus: randomized
`List Element` (numeric/categorical mixes including the empty list and all-numeric
lists) for the `convert` site, and randomized `List String` drawn from a pool of
parsable (`"1"`, `"3.5"`, date-like) and non-parsable (`"a"`, `"foo"`) names
including the empty list for the `update` site. The R/I shadow of each
`implementation_*` is diffed against an in-process replica of the POST-PATCH
decision (`bool(size and flag)`). The discriminating edge cases are pinned:
the empty list (decision must be `False` post-patch, `True` pre-patch) and a
non-empty all-flag list (decision `True` in both).
