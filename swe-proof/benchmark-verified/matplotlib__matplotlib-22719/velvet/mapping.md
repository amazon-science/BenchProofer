# mapping.md — matplotlib__matplotlib-22719

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a2a1b0a11b993fe5f8fab64b6161e99243a6393c`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the unchanged per-element tests the modeled decisions observe.

Repo file under change: `lib/matplotlib/category.py` (two independent sites).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `numericNoticeFires (numlikeFlags : List Bool)` | `StrCategoryConverter.convert` — `lib/matplotlib/category.py:28` (decision at body line 61) | site A: whether the converter emits its number-passthrough advisory notice |
| `numericLabelNoticeFires (parsableFlags : List Bool)` | `UnitData.update` — `lib/matplotlib/category.py:209` (decision at body line 233) | site B: whether the mapping-update routine emits its all-labels-look-numeric advisory notice |
| `allTrue (flags : List Bool)` | the builtin `all(<gen>)` aggregating the per-element test over the supplied collection (both sites) | pure spec: the universal-quantifier aggregate |
| `noticeFires (flags : List Bool)` | the post-patch guard expression `<collection>.size and <all-aggregate>` (both sites) | pure spec: the notice-emission decision |

The per-element tests themselves are UNCHANGED callees; they are not modeled —
they are observed only through their per-element boolean RESULT, which is the
input carrier (see §2/§3). This is the same treatment as the widget-kind /
blank-flag tests in the django__django-12406 bundle (booleans observed as
inputs, no axioms).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the per-element boolean `is_numlike(v) and not isinstance(v, (str, bytes))` over `values` (site A) | one `Bool` per element, in input order: `List Bool` | element `v` ↔ its test result `b`; `len(values)` ↔ `flags.length`; empty collection ↔ `[]` |
| the per-(unique-)element boolean `self._str_is_convertible(val)` over the iterated unique values (site B) | one `Bool` per iterated unique value: `List Bool` | unique value `val` ↔ its test result `b`; `bool(data.size)` ↔ `!flags.isEmpty` (see note) |
| `values.size` / `data.size` (numpy array length truthiness) | `!flags.isEmpty` | a numpy `atleast_1d(array(x, dtype=object))` has `size == 0` iff `x` is empty; its truthiness is exactly non-emptiness, which `!flags.isEmpty` mirrors |
| `is_numlike` / `convertible` (the `all(...)` aggregate) | `allTrue flags` | `all(t(v) for v in coll)` ↔ the front-recursive conjunction `allTrue` over the per-element results; `all([]) = True` ↔ `allTrue [] = true` |
| the boolean decision controlling notice emission | `out : Bool` | `True` ↔ notice emitted; `False` ↔ notice suppressed |

**Note on site B's `data.size` vs unique count.** The patched guard tests
`data.size` (raw element count, counting duplicates), while `convertible`
aggregates the test over *unique* values (`OrderedDict.fromkeys(data)`). The
guard only consumes `data.size` for its TRUTHINESS, and `bool(data.size) ==
(len(data) > 0) == (number of unique values > 0)`. So modeling the carrier as
the per-unique-value flag list and testing `!flags.isEmpty` is faithful for the
only thing the guard observes (non-emptiness). G-CONF derives the flags from the
real unchanged `_str_is_convertible` and drives the real `update`, so any
divergence here would surface as a disagreement.

## 3. Per-element test provenance (observed-as-input, NOT axiomatized)

Neither modeled decision axiomatizes a callee. The two unchanged per-element
tests are observed only through their boolean results, which are the input
carriers — exactly the django__django-12406 treatment of an unchanged predicate
whose only observable contribution is a `Bool`.

### 3.1 Site A — `is_numlike(v) and not isinstance(v, (str, bytes))`
`units.ConversionInterface.is_numlike(v)` (unchanged) combined with the
str/bytes exclusion. Each element of the converter's `value` argument yields one
flag; the converter's notice fires (post-patch) iff the collection is non-empty
AND every flag is true. The `all(...)` over an EMPTY collection is vacuously
`True` — the defect: pre-patch the notice fired on empty input.

### 3.2 Site B — `UnitData._str_is_convertible(val)`
`_str_is_convertible` (unchanged: `float(val)` succeeds, else `dateutil.parser`
parses) is applied to each unique value. The update routine's notice fires
(post-patch) iff `data` is non-empty AND every unique value is convertible. Same
vacuous-`all([])` defect pre-patch.

There is **no `axiom`** in this bundle and **no `axiom_check.py`** (G-AX skip):
the changed behavior at both sites is pure boolean dataflow whose only inputs
are the per-element test results, modeled deeply as closed `Bool` expressions.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`22719`**. It does NOT
transliterate the patched guard tautologically: it derives the per-element flags
by calling the REAL unchanged tests (`is_numlike` for site A, `_str_is_convertible`
for site B) on randomly constructed inputs, then drives the REAL patched
`StrCategoryConverter.convert` / `UnitData.update` in-container and observes
whether the advisory (the `MatplotlibDeprecationWarning` for site A, the INFO log
for site B) actually fires. SHADOW = `noticeFires flags` from `Solution.lean`;
ORACLE = the real notice-fired observation. They must agree on every input
(boundary: empty, all-true, mixed, all-false; plus ≥10⁵ fuzz). Exit 0 iff zero
disagreements.
