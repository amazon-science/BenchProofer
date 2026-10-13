# mapping.md — scikit-learn__scikit-learn-14087

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a5743ed36fbd3fbc8e351bdab16561fbfca7dfa1`, states the type
abstraction, and gives the provenance of each modeled operation.

Repo file under change: `sklearn/linear_model/logistic.py`.
Changed function: `LogisticRegressionCV.fit(self, X, y, sample_weight=None)`
(`sklearn/linear_model/logistic.py:1936`), specifically the `else:` branch of
`if self.refit:` (the "no-refit" branch, body lines 2169–2184 @ base_commit).

## 1. Symbol ↔ repo binding

| model.py symbol | repo construct (file:line @ base_commit) | role |
|---|---|---|
| `table_rank(resolved_strategy)` | the layout-rank of the per-class `coefs_paths` array, set by the reshape at `logistic.py:2086-2106` (which keys on the *resolved* local `multi_class`) | pure spec: how many leading index axes `coefs_paths` carries |
| `gather_arity(use_joint_layout)` | the literal index-axis count of the read expression: `coefs_paths[i, best_indices[i], :]` (3) vs `coefs_paths[:, i, best_indices[i], :]` (4) | pure spec: how many axes the across-folds read addresses |
| `read_across_folds(use_joint_layout, table_axes, summary_token)` + `read_admissible(rank)` + `summary_table(actual_rank)` | the across-folds read `w = np.mean([coefs_paths[...] for i in range(len(folds))], axis=0)` (`logistic.py:2172-2178`), performed against the single `coefs_paths` bound at `logistic.py:2084` and reshaped at `:2086-2106` / rebound per class at `:2124` | **A-consumed axiom**: every read is performed against the ONE table the caller holds (`summary_table(rank)`, an abstract resource carrying the array's real `ndim`, required and returned by the read), and grants the unforgeable in-range capability AT that table's rank iff the read arity equals it; the consumer holds and returns the resource at the array's actual axis rank and demands the capability there. So the arity of EVERY read the block performs — not only the one whose value becomes `w` — is checked against the real layout, which is the real "no out-of-range index anywhere in the block" observable |
| `gather_per_class(resolved_strategy, unresolved_form, table_axes, summary_token)` | the coefficient-gather block `logistic.py:2172-2178` (`best_indices = np.argmax(...)` + the `if ... 'ovr'` / `else` `w = np.mean([... coefs_paths ...])`) | modeled changed function (site 1): selects the read expression whose arity matches the array layout |
| `mixing_record(family_has_mixing, selected_index, candidates_len, mixing_value)` | the l1-ratio recording block `logistic.py:2183-2184` (`best_indices_l1 = ...`; `self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))`) | modeled changed function (site 2): the value appended to `self.l1_ratio_` per class, AND whether the candidate table is averaged at all |
| `select_mixing_value(...)` + `candidate_table(holds_mixing_values, actual_len)` + `mixing_selected()` | the averaged lookup `np.mean(l1_ratios_[best_indices_l1])` (`logistic.py:2184`) against the one `l1_ratios_` table (`logistic.py:1971`/`:1978`) | **A-consumed axiom**: the lookup is performed against the ONE candidate table the caller holds (`candidate_table(r, n)`, an abstract resource carrying BOTH whether its entries are real mixing values AND how many entries it has, required and returned by the lookup), is admissible only when that table holds real mixing values and only at a position within its actual extent, and grants the unforgeable `mixing_selected()` capability which the consumer demands whenever it records a value. So EVERY selection the block performs — not only the one whose value is appended — is a selection of an entry the table actually holds, which is the real "the placeholder table is never averaged, and no lookup reaches past the end of the ratio table" observable |
| `INDEPENDENT/JOINT/UNRESOLVED` (0/1/2) | the string values `'ovr'`, `'multinomial'`, `'auto'` taken by `self.multi_class` and the resolved local `multi_class` | categorical encoding |
| `family_has_mixing` flag | `self.penalty == 'elasticnet'` (`logistic.py:1964,2183`) | categorical encoding |
| the `None` sentinel (modeled as `Optional` `None`) | the literal `None` appended to `self.l1_ratio_` when penalty is not elasticnet (post-patch `logistic.py:2187`); and the `l1_ratios_ = [None]` sentinel set at `logistic.py:1978` | "no mixing value applies" |

The unresolved attribute `self.multi_class` vs the resolved local `multi_class`
(the two operands of the site-1 branch): the local `multi_class` is computed by
`multi_class = _check_multi_class(self.multi_class, solver, len(classes))`
(`logistic.py:2004`), which maps `'auto'` to a concrete `'ovr'`/`'multinomial'`
(`_check_multi_class`, `logistic.py:457-471`). The per-class `coefs_paths`
array layout (its axis rank) is built from the resolved local `multi_class`
(reshape `logistic.py:2086-2106`), so only the resolved value indexes it
correctly.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.multi_class` / resolved `multi_class` (`str` in `{'ovr','multinomial','auto'}`) | `int` tag in `{INDEPENDENT=0, JOINT=1, UNRESOLVED=2}` | string-equality `== 'ovr'` ↔ `== INDEPENDENT`; the resolved value never equals `UNRESOLVED` (it is resolved away by `_check_multi_class`) |
| `self.penalty == 'elasticnet'` (`bool`) | `bool` `family_has_mixing` | identical truth value |
| `coefs_paths` per-class numpy array; its number of leading index axes (3 for the ovr layout `(n_folds, n_Cs·n_l1, n_features)`, 4 for the multinomial layout `(n_classes, n_folds, n_Cs·n_l1, n_features)`) | `int` `table_axes` ∈ {3,4} carried alongside the read | `coefs_paths[i, best_indices[i], :]` is in-bounds iff `table_axes == 3`; `coefs_paths[:, i, best_indices[i], :]` is in-bounds iff `table_axes == 4`. Indexing with too many axes is the reported `IndexError: too many indices for array`. |
| the across-folds read `w = np.mean([coefs_paths[...] for folds], axis=0)` and its success | the `read_across_folds` **A-consumed axiom** returning a `summary_token` and granting the unforgeable `read_admissible(rank)` capability at the checked rank iff `gather_arity == rank`; the consumer demands `read_admissible(table_axes)` (the actual layout rank) | the read either succeeds in-bounds (granting the capability) or raises `IndexError`; the gathered vector's numeric value is value-irrelevant (F2P asserts shape), so it is the identity token `summary_token` |
| the single `coefs_paths` array in scope for the iteration (bound once at `logistic.py:2084`, its `ndim` fixed by the reshape at `:2086-2106` and the per-class rebinding at `:2124`) — the thing every index expression in the block addresses | the abstract resource `summary_table(actual_rank)`, held by the modeled step at `table_axes` and required/returned by each `read_across_folds` call at the rank that read is checked against | holding `summary_table(r)` ↔ having the one array in scope with `ndim == r`. A read is performable only against a held table, so a rank the implementation names for itself corresponds to no array the block has: the arity of every read is compared against the real `ndim`. Returning the resource ↔ indexing does not consume the array, so a repeated in-bounds read is still legal |
| `l1_ratios_` (a Python list; `[None]` sentinel when penalty≠elasticnet, else the real ratios) | `int` length `candidates_len` + the categorical `family_has_mixing` flag, BOTH carried by the held resource `candidate_table(family_has_mixing, candidates_len)` | `len(l1_ratios_)` ↔ `candidates_len`; the `[None]` sentinel ↔ `family_has_mixing == False`. Because the length is a parameter of the held resource rather than a bare argument, `candidates_len` is the real table's extent at every selection: `l1_ratios_[i]` is in-bounds iff `0 <= i < len(l1_ratios_)`, and indexing past the end is `IndexError: index N is out of bounds for axis 0 with size N`. The real post-patch index satisfies it: `best_indices // len(self.Cs_) < len(l1_ratios_)` because `scores.shape[1] == len(self.Cs_) * len(l1_ratios_)` (reshape at `logistic.py:2108`) |
| `np.mean(l1_ratios_[best_indices_l1])` (the appended value) | `Optional[int]`-style sentinel: a real mixing token (its index `selected_index`) when the family carries a mixing parameter, else `None` | the F2P observes `self.l1_ratio_.shape == (n_classes,)`; a per-class entry is well-formed iff it is a number OR `None` — never `np.mean([None,...])` (which the bug computes) |
| the averaged lookup `np.mean(l1_ratios_[idx])` itself, and the one `l1_ratios_` table it addresses (the real ratios, or the one-element placeholder set at `logistic.py:1978`) | the `select_mixing_value` **A-consumed axiom** guarded by the abstract resource `candidate_table(holds_mixing_values, actual_len)`, granting the unforgeable `mixing_selected()` capability | holding `candidate_table(True, n)` ↔ having the real ratio table of `n` ratios in scope; `candidate_table(False, 1)` ↔ having the one-element placeholder table. The lookup is admissible only against a held table holding real values, matching that the average over the placeholder yields no mixing value (axiom_check.py R3), and only at a position within the held table's extent, matching that indexing `l1_ratios_` past its end raises. A position or an extent the selector names for itself corresponds to no table the block has, so the extent every lookup is checked against is the real `len(l1_ratios_)`. Returning the resource ↔ the lookup does not consume the table, so a repeated legitimate lookup — including one at another in-range position — stays expressible |

`numpy` arrays cannot be expressed in Nagini's fragment; the array *shape /
index arity* and the *categorical branch selection* — which is exactly where
both bugs live — are modeled directly over `int`/`bool`/`Optional` (site 1's
read additionally goes through the `read_across_folds` axiom, whose precondition
IS the arity-match in-bounds condition). The numeric values inside `w` and the
averaging are precision-irrelevant to the tested behavior (the F2P tests assert
attribute *shapes* and absence of `IndexError`, not coefficient values), so they
are modeled as identity tokens (see refinement.md, tags R/I/A).

Both modeled functions additionally carry a `MustTerminate` obligation
(measure 2 on the functions, measure 1 on the consumed axiom): the real
record-keeping steps are bounded, loop-free work that always completes, and
Nagini's default partial-correctness semantics would otherwise let a diverging
implementation discharge every postcondition vacuously (refinement.md §C.1).

## 3. Callee provenance

The proof consumes TWO axioms, one per site, built to the same shape (see
refinement.md §C for the full inventory):

* `read_across_folds` (with its two abstract predicates: the capability
  `read_admissible` and the held-table resource `summary_table`), modeling the
  across-folds coefficient read whose only bug-relevant behaviour is its index
  arity (site 1); it is the weakest contract sufficient (it constrains only the
  arity-match case, and returns the table so repeated in-bounds reads stay
  expressible).
* `select_mixing_value` (with its two abstract predicates: the capability
  `mixing_selected` and the held-table resource `candidate_table`), modeling the
  averaged lookup of the per-class candidate-mixing table, whose bug-relevant
  behaviours are whether it is performed against a table holding no mixing
  values at all and whether the position it addresses exists; it too is the
  weakest contract sufficient (it constrains only the admissible case — real
  entries, in-extent position — and returns the table so repeated legitimate
  lookups, including at another in-range position, stay expressible).

Site 2's absent-marker branch is otherwise modeled **deeply** over
`int`/`bool`/`Optional` (the absent-marker selection IS the fix), with the
`[None]` sentinel as an A-reference fact. The unchanged numeric
primitives the real code calls in this block — `np.argmax` (per-fold best index),
`np.mean` (averages the read coefficients / the C values), `//` and `%`
(decompose the flat best index) — are not changed by the patch and do not bear
on the tested observables (shape + no-IndexError); they are carried as
already-computed inputs / inside the `read_across_folds` axiom and validated
against the real callees out-of-band by `axiom_check.py` (G-AX). See
refinement.md §A/§B/§C for the operation-by-operation correspondence and the
axiom inventory.

### 3.1 The resolved-vs-unresolved `multi_class` (site 1)
`_check_multi_class(multi_class, solver, n_classes)` (`logistic.py:457-471`):
maps `'auto'` → `'ovr'` if `solver == 'liblinear'` or `n_classes <= 2`, else
`'multinomial'`; leaves `'ovr'`/`'multinomial'` unchanged; raises on anything
else. Hence the resolved local `multi_class` is always in `{'ovr','multinomial'}`
— NEVER `'auto'`. The `coefs_paths` layout (and thus its index arity / rank) is
keyed on this resolved value (reshape `logistic.py:2086-2106`). `axiom_check.py`
checks this resolution table and the resulting array-rank mapping against the
real `_check_multi_class` and `np.reshape`.

### 3.2 The `l1_ratios_` sentinel (site 2)
When `self.penalty != 'elasticnet'`, `l1_ratios_` is set to the one-element
sentinel `[None]` (`logistic.py:1972-1978`); only when penalty is `'elasticnet'`
is it the user's real ratios (`logistic.py:1971`). `axiom_check.py` checks that
`np.mean(np.asarray([None])[idx])` does NOT produce a valid float (it raises /
yields a non-number), so the per-class `l1_ratio_` entry must be the literal
`None` in the non-elasticnet case, exactly as the post-patch code appends.
