# refinement.md — matplotlib__matplotlib-22719

Operation-by-operation correspondence between the two `implementation_*` regions
(Solution.lean) and `patch.diff` (the POST-PATCH `category.py`). Tags: **R** type
refinement, **A-consumed** proof uses an axiom, **A-reference** deep model
validated == real callee, **I** identical concrete op.

## `implementation_numericPassthrough` ↔ `StrCategoryConverter.convert` guard

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut isNumlike := true` | `is_numlike = all(... for v in values)` (accumulator seed) | R |
| 2 | `for v in values do if !isNumeric v then isNumlike := false` | the `all(units.ConversionInterface.is_numlike(v) and not isinstance(v,(str,bytes)) for v in values)` conjunction | R |
| 3 | `return (!values.isEmpty && isNumlike)` | `if values.size and is_numlike:` — **the fix** (added `values.size and`) | R |

## `implementation_parsableInfo` ↔ `UnitData.update` guard

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 4 | `let mut convertible := true` | `convertible = True` | I |
| 5 | `for val in data do if !looksNumeric val then convertible := false` | `for val in OrderedDict.fromkeys(data): if convertible: convertible = self._str_is_convertible(val)` | R |
| 5a | `looksNumeric` | `UnitData._str_is_convertible` (unchanged callee) | A-reference |
| 6 | `return (!data.isEmpty && convertible)` | `if data.size and convertible:` — **the fix** (added `data.size and`) | R |

Notes:

- **The fix is steps 3 and 6**, identical in shape at both sites: the decision to
  emit a side notification is changed from `flag` to `size and flag`. The
  pre-patch impls (`Solution_prepatch_1.lean` returns bare `isNumlike`;
  `Solution_prepatch_2.lean` returns bare `convertible`) are the two actual bugs.
  Each prepatch isolates ONE site so G-DIFF observes each fixed behavior
  independently; both share the identical frozen spec (G-DIFF `same_spec`).
- **R vs I.** Step 4 is **I** (`convertible = True` transliterates literally).
  The remaining steps are **R**: the numpy object array / `OrderedDict.fromkeys`
  iteration are refined to `List Element` / `List String` per the mapping.md
  bijection, the `all(...)`/early-latch loop to a `for` + `let mut` accumulator,
  and `values.size`/`data.size` to `!_.isEmpty`.
- **Step 2 — the latch loop = the conjunction.** The real `all(...)` short-
  circuits; the Lean `for` loop visits every element and latches `isNumlike`
  to `false` on the first failing element. Both compute the conjunction
  `values.all isNumeric`; the spec pins the result to that conjunction, and the
  proof agent discharges loop = conjunction by the PROOF_PLAYBOOK accumulator
  induction (`List.forIn_cons`). Same for step 5 (`update`'s `if convertible:`
  guard only re-tests while still `True`, which is exactly the conjunction).
- **Step 5a — `looksNumeric` is an A-reference, declared `opaque`, NOT a consumed
  axiom.** `_str_is_convertible` is an unchanged callee; the decision rule depends
  only on the sequence-level conjunction of its per-element results, never on its
  value for any particular string. The proof consumes no `looksNumeric_prop`
  property, so the `axioms` region declares the signature only. Because the
  predicate appears IDENTICALLY in both the conformance oracle and shadow legs (it
  cancels in the decision equality), there is no callee contract for G-AX to
  validate beyond totality; **G-AX is a skip stub** (mapping.md).
- **No changed op is axiomatized.** The thing that changed (the `size and …`
  guard) is modeled DEEPLY as `!_.isEmpty && …` over the observable inputs, per
  SPEC_GUIDE §3.
- **G-CONF** mechanically refutes the R/I legs: the in-process replica of the
  POST-PATCH decision (`bool(size and flag)`) for each site is diffed against the
  op-for-op shadow of the corresponding `implementation_*` over ≥1e5 fuzzed
  inputs, including the empty-sequence discriminator. No A-consumed legs.
