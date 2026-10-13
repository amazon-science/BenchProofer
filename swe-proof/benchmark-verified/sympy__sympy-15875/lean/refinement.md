# refinement.md — sympy__sympy-15875

Maps every op in `implementation_zeroStatus` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses callee axiom ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

Modeled function: `Add._eval_is_zero(self)` (`sympy/core/add.py:531-568`),
commutative path. The return is the three-valued zero verdict
(`True`/`False`/`None` ↔ `some true`/`some false`/`none`).

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `for a in terms do match a with …` | `for a in self.args:` with the `is_real`/`is_zero`/`is_imaginary`/`(I*a).is_real` ladder | R | each Python argument's assumption-query ladder ↔ one `Summand` constructor (type bijection, mapping.md). `self.args` (post-eval arg tuple) ↔ `terms : List Summand` |
| 2 | `.realZero => z := z + 1` | `if a.is_zero: z += 1` | I | real-zero count |
| 3 | `.realNonzero => nz := nz + 1` | `elif a.is_zero is False: nz.append(a)` | R | `nz` modeled as a count (`nz := nz + 1`) since only `len(nz)` and `self.func(*nz).is_zero` are observed; the sub-sum's zero-test is supplied as input `realSumZero` |
| 4 | `.realUnknown => return none` | `else: return` (real, undecidable-zero arm) | I | early undetermined |
| 5 | `.imaginary => im := true` | `elif a.is_imaginary: im = True` | I | imaginary flag |
| 6 | `.imagOrZero => imOrZ := true` | `elif (S.ImaginaryUnit*a).is_real: im_or_z = True` | I | imaginary-or-zero flag |
| 7 | `.indeterminate => return none` | final `else: return` | I | unclassifiable ⟹ undetermined |
| 8 | `if z == terms.length then return some true` | `if z == len(self.args): return True` | I | all-zero ⟹ zero |
| 9 | `if nz == 0 \|\| nz == terms.length then return none` | `if len(nz) == 0 or len(nz) == len(self.args): return None` | I | **the fixed line** (`len(nz) == 0 or` added). `nz`(count) ↔ `len(nz)`, `terms.length` ↔ `len(self.args)` |
| 10 | `match realSumZero with some true => …` | `b = self.func(*nz); if b.is_zero:` | R | `b.is_zero` (the recursive zero-test of the real-nonzero sub-sum) supplied as input `realSumZero : Option Bool`; `some true` ↔ truthy `b.is_zero` |
| 11 | `if !imOrZ && !im then return some true` | `if not im_or_z and not im: return True` | I | real anchor cancels, no imaginary content ⟹ zero |
| 12 | `if im && !imOrZ then return some false` | `if im and not im_or_z: return False` | I | real anchor cancels, pure-imaginary remainder ⟹ nonzero |
| 13 | `some false => return some false` | `if b.is_zero is False: return False` | I | real anchor definitely nonzero ⟹ whole sum nonzero |
| 14 | fallthrough `return none` | implicit Python `return None` (no explicit return reached) | I | undetermined default |

Every op is R or I — no A-tagged rows. The verdict is modeled deeply: the
per-summand assumption ladder is folded into the `Summand` classification
(exercised end-to-end by G-CONF on the real expressions), and the only callee
result the function consumes — `self.func(*nz).is_zero` — is supplied as the
three-valued input `realSumZero` (grounded in the inputs, not axiomatized).

Because the impl region is entirely R/I (no A-tagged content), `conf_skip =
false`: G-CONF mechanically differential-tests this impl against the patched
`Add._eval_is_zero`.

## Prepatch (the real bug)

`Solution_prepatch.lean` drops the `nz == 0 ||` disjunct from op #9 (the exact
pre-fix line `if len(nz) == len(self.args): return None`). When there is **no**
definitely-nonzero real term (`nz == 0`) but at least one imaginary/imaginary-
or-zero term, the buggy impl skips the early `none` and falls into the
`realSumZero` match. With `nz == 0` the real-anchor sub-sum is the empty sum
(`self.func()` = `0`, `realSumZero = some true`): for a purely-imaginary
remainder (`im && !imOrZ`) the prepatch returns `some false` — wrongly declaring
a nonzero verdict — exactly the issue's `(-2*I + (1+I)**2).is_zero` returning
`False` instead of `None`.

The discriminating clause is `problem_spec`'s `result = zeroVerdict …`: on
`terms = [imaginary, imaginary]`, `realSumZero = some true`, the spec demands
`none` while the prepatch impl yields `some false`, so `correct_zeroStatus` is
unprovable for the prepatch impl (G-DIFF).
