# refinement.md — django__django-11728

The operation-by-operation correspondence between `model.py`'s implementation
(`named_group_pattern_end`, `unnamed_group_pattern_end`, and the deep
`close_off`/`step_bal` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof uses an axiom's Ensures),
**A-reference** (a deep model validated == the real callee/operation by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, computes the same capture-group span end as the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). There are **no kind-3 steps** and **no
consumed axioms** (the `axioms` region is empty).

The gold patch makes the *same* two-part edit to two functions: (a) delete the
`if unmatched_open_brackets == 0:` check from the **top** of the inner loop,
and (b) add it at the **bottom** (after the depth update + `prev_char = val`),
with the captured end index advanced by one (`end + idx` → `end + idx + 1`;
`start + 1 + idx` → `start + 2 + idx`).

## A. Named site — `replace_named_groups` (`utils.py:153`, loop 168-182)

Gold hunk (lines 169-185 region):
```
  for idx, val in enumerate(pattern[end:]):
-     if unmatched_open_brackets == 0:
-         group_pattern_and_name.append((pattern[start:end + idx], group_name))
-         break
      if val == '(' and prev_char != '\\':  unmatched_open_brackets += 1
      elif val == ')' and prev_char != '\\': unmatched_open_brackets -= 1
      prev_char = val
+     if unmatched_open_brackets == 0:
+         group_pattern_and_name.append((pattern[start:end + idx + 1], group_name))
+         break
```

| # | model.py impl op (`named_group_pattern_end`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `region: List[int]`, `prev0: int` | the scanned slice `pattern[end:]` and the `prev_char` state at scan start | R | `str` slice ↔ `List[int]` code points; `prev_char` (`None`/char) ↔ `prev0: int` (mapping.md §2). The caller has already isolated the slice via `m.end(0)`. |
| A2 | `bal = 1; prev = prev0; i = 0` | `unmatched_open_brackets, prev_char = 1, None` and `idx` from `enumerate` | I + R | initial depth 1 (group already open); `i` ↔ `idx`. |
| A3 | per-char `nb = step_bal(region[i], prev, bal)` | the `if val=='(' ... elif val==')' ...` depth update with the `prev_char != '\\'` escape guard | A-reference | the changed scan is modeled **deeply** (`step_bal`/`close_off`), validated `== ` the real per-char update by G-AX (mapping.md §3.1). `'('`↔40, `')'`↔41, `'\\'`↔92. |
| A4 | `prev = val; bal = nb; i = i + 1` | `prev_char = val` then loop advance | I | identical state update/order (escape state then advance). |
| A5 | `if bal == 0: res = i` placed AFTER the update (loop guard `bal != 0` / break-on-zero at bottom) | the **moved** `if unmatched_open_brackets == 0:` now after the update, recording `end + idx + 1` | I | the fix's essence: detect depth-zero *after* processing the close, recording end `= idx + 1` relative to the slice = `Result()`. The caller adds base `end`: `end + Result() = end + idx + 1`. |
| A6 | postcondition `Result() == close_off(ToSeq(region),1,prev0) + 1` | the recorded slice end `end + idx + 1` (`idx == close_off` at the close) | A-reference + R | the span end the gold computes equals `close_off + 1` past the region start; G-AX confirms `close_off` == the real `idx`-at-close. |

## B. Unnamed site — `replace_unnamed_groups` (`utils.py:190`, loop 201-214)

Gold hunk (lines 203-216 region) — structurally identical, base offset `start+1`,
captured end `start + 2 + idx`:
```
  for idx, val in enumerate(pattern[start + 1:]):
-     if unmatched_open_brackets == 0:
-         group_indices.append((start, start + 1 + idx))
-         break
      ...depth update...
      prev_char = val
+     if unmatched_open_brackets == 0:
+         group_indices.append((start, start + 2 + idx))
+         break
```

| # | model.py impl op (`unnamed_group_pattern_end`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1-B6 | as A1-A6 | the same edit on the unnamed loop | R / I / A-reference | identical to site A; the only difference is the caller's base offset (`start + 1` instead of `end`) and that the recorded end is `start + 2 + idx = (start+1) + (idx+1)`, i.e. `(start+1) + Result()` (mapping.md §2). The scan-relative quantity `Result() == close_off + 1` is the same. |

`unnamed_group_pattern_end` is modeled as its own contracted function (not
collapsed into the named one) to provide an independent differential witness:
`model_prepatch_2.py` reverts only this site and fails on its postcondition,
matching the second gold hunk.

## C. No kind-3, no consumed axioms

Every step above is R, I, or A-reference. The one operation that *changed* —
the depth-zero-detection placement and the resulting span end — is modeled
**deeply** (`close_off`/`step_bal`, consumed inside both `*_pattern_end`
functions as the postcondition oracle), an **A-reference** validated `==` the
real Python scan by G-AX. There is **no `@ContractOnly` axiom** (the `axioms`
region is empty): `re.finditer` only enumerates group *start* positions and is
outside the modeled span computation (the model receives the isolated `region`),
so it is neither consumed nor referenced.

## D. verify(model) ⇒ resolved

`named_group_pattern_end` / `unnamed_group_pattern_end` verify only if their
result equals `close_off(region) + 1` for *every* group whose matching close
exists in the region — **including when that close is the final character**
(the precondition `close_off(region) < len(region)` admits exactly that case,
and the postcondition pins the answer there too). By R (str ↔ List[int], the
base-offset bookkeeping `end` / `start+1`) the verified span end equals the
gold patch's recorded capture index on the tested patterns; by G-AX (A-ref) the
deep `close_off` equals the real inner-loop `idx`-at-close. The pre-patch
top-check placement, reproduced in `model_prepatch.py` / `model_prepatch_2.py`,
fails the postcondition exactly on the trailing-group inputs the F2P test adds
(`r'^(?P<a>\w+)/b/(?P<c>\w+)'`, `r'^(?P<a>\w+)/b/(\w+)'`, …). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the G-AX-audited scan, and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: the A-reference scan
soundness (G-AX) and refinement fidelity (this document, G-EQ); there is no
axiom-soundness trust point because no axiom is consumed.
