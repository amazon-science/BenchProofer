# refinement.md — matplotlib__matplotlib-22719

The operation-by-operation correspondence between `model.py`'s implementation
(the two decision functions and the deep `all_classify` fold) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed**
(the proof uses an axiom's `Ensures`), **A-reference** (a deep model is
validated == a real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There is **no `@ContractOnly` axiom**: the only operation the patch changes —
the non-emptiness guard `X.size and ...` — is modelled **deeply**
(`len(flags) > 0 and ...`), and the unchanged universal "all elements classify"
property is spelled out by the front-recursive `@Pure` fold `all_classify`.
The per-element classifiers (`is_numlike`/`_str_is_convertible`) are unchanged
and are abstracted into the model's input flags (R), not consumed as axioms.

## A. The convert site — `StrCategoryConverter.convert` (`category.py:61`)

Gold hunk:
```
-        if is_numlike:
+        if values.size and is_numlike:
             _api.warn_deprecated("3.5", message="Support for passing numbers ...")
             return np.asarray(values, dtype=float)
```
where `is_numlike = all(units.ConversionInterface.is_numlike(v) and not
isinstance(v, (str, bytes)) for v in values)` and `values =
np.atleast_1d(np.array(value, dtype=object))`.

| # | model.py impl op (`should_warn_numeric_passthrough`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `flags: List[int]` | `values` (numpy object array) | R | each element abstracted to its per-element classification flag; `flags[k] != 0` ↔ `is_numlike(values[k]) and not isinstance(values[k], (str,bytes))` (mapping.md §2, §3.1). |
| A2 | the loop building `every == all_classify(ToSeq(flags))` | the comprehension `all(<predicate> for v in values)` bound to `is_numlike` (lines 58-60) | A-reference (deep) + R | the unchanged universal verdict is spelled out deeply by `all_classify` (front-recursive `@Pure` fold) and the matching backward loop; per-element predicate ↔ flag is R. `all_classify([]) == True` mirrors `all(<empty>) == True` — the vacuous truth at the heart of the issue. Validated against the real `all`/numpy semantics by axiom_check.py (G-AX). |
| A3 | `len(flags) > 0` | `values.size` (in the boolean position of `values.size and is_numlike`) | R | `np.ndarray.size > 0` ↔ `len(flags) > 0`; for `values = np.atleast_1d(np.array(value, dtype=object))`, `values.size == 0` iff the input carries no elements (mapping.md §4). **This is the changed conjunct.** |
| A4 | `len(flags) > 0 and every` returned | `values.size and is_numlike` (the `if` test deciding whether `warn_deprecated` runs) | I | the boolean `and` and the emit decision are the identical concrete operation; the returned bool ↔ "the `if` branch is taken / the advisory is emitted". |

The discriminating content of the change — the advisory must NOT fire on the
empty sequence — lives in the `len(flags) > 0` conjunct (A3). The pre-patch code
tested `is_numlike` alone; `model_prepatch.py` reproduces that (returns `every`
without the length conjunct) and **fails** the postcondition `Result() ==
(len(flags) > 0 and all_classify(ToSeq(flags)))` on the empty input (where
`every == all_classify([]) == True` but the required result is `False`) — exactly
the spec sensing the change (G-DIFF).

## B. The update site — `UnitData.update` (`category.py:233`)

Gold hunk:
```
-        if convertible:
+        if data.size and convertible:
             _log.info('Using categorical units to plot a list of strings ...')
```
where `convertible` is the left-fold (seeded `True`, set to
`_str_is_convertible(val)` while still `True`) over the unique values
`OrderedDict.fromkeys(data)`, and `data = np.atleast_1d(np.array(data,
dtype=object))`.

| # | model.py impl op (`should_log_numeric_strings`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `flags: List[int]` | `data` (numpy object array) | R | each element abstracted to its per-element classification flag; `flags[k] != 0` ↔ `_str_is_convertible(val_k)` (mapping.md §2, §3.2). |
| B2 | the loop building `classify == all_classify(ToSeq(flags))` | the `convertible` accumulator over `OrderedDict.fromkeys(data)` (lines 224-230) | A-reference (deep) + R + I | the short-circuited `if convertible:` left-fold computes the same boolean as the unconditional universal `all`; modelled deeply by `all_classify` + the matching loop. `all_classify([]) == True` mirrors the unentered loop leaving the `True` seed — the vacuous truth at the heart of the issue. Length-non-emptiness of `data` equals that of its unique set, so the dedup is observationally irrelevant to the guard (I). Validated by axiom_check.py (G-AX). |
| B3 | `len(flags) > 0` | `data.size` (in `data.size and convertible`) | R | `np.ndarray.size > 0` ↔ `len(flags) > 0` (mapping.md §4). **This is the changed conjunct.** |
| B4 | `len(flags) > 0 and classify` returned | `data.size and convertible` (the `if` test deciding whether `_log.info` runs) | I | identical boolean `and` and emit decision; returned bool ↔ "the advisory is logged". |

`model_prepatch_2.py` reverts B3/B4 (returns `classify` without the length
conjunct) and **fails** the same postcondition on the empty input — the
independent differential witness for site B (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the non-emptiness guard `X.size and ...` — is modelled **deeply**
(the `len(flags) > 0 and` conjunct, A3/B3), not hidden behind an axiom about the
function under change. The unchanged universal verdict (`all(...)` /
`convertible`) is modelled deeply by the front-recursive `all_classify` fold
(A2/B2, an A-reference validated by G-AX), and the unchanged per-element
classifiers are abstracted into the input flags (R). **There is no consumed
`@ContractOnly` axiom** — nothing the proof depends on is hidden, so there is no
A-consumed row and no dead axiom.

## D. verify(model) ⇒ resolved

Each decision function verifies only if its output equals `len(flags) > 0 and
all_classify(ToSeq(flags))` (A3/A4, B3/B4) AND yields `False` on the empty
sequence (the `Implies(len == 0, not Result())` clause). By R (numpy object
array ↔ `List[int]` flags, `ndarray.size` ↔ `len`, per-element classifier ↔
flag) the verified decision equals the patched `values.size and is_numlike` /
`data.size and convertible` on every input, and by G-AX the deep `all_classify`
fold equals the real `all`/`convertible` universal verdict (including the
vacuous truth on empty). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE): the F2P test `test_no_deprecation_on_empty_data` exercises exactly
the empty-input no-advisory behaviour both sites now enforce, and every P2P
non-empty case is unchanged (the universal verdict still governs there). The
trust points are exactly the two of PLAN §1.1: refinement fidelity (this
document, G-EQ) and the behavioural soundness of the deep universal model
(G-AX); there is no axiom-soundness trust point because there is no axiom.
