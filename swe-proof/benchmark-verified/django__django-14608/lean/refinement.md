# refinement.md — django__django-14608

Operation correspondence between `implementation_nonFormErrors` (Solution.lean)
and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Modeled function: the non-form error collection produced by `full_clean`

The patch adds `error_class='nonform'` to the two `self.error_class(...)`
constructions of `self._non_form_errors` in `full_clean` (the initial empty
collection at `:336` and the validation-error reconstruction at `:383`). The
observable effect is that the non-form error collection renders under the CSS
class `errorlist nonform` instead of the bare `errorlist`. The carried messages
are unchanged by the patch.

| # | `implementation_nonFormErrors` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | inputs `isBound mgmtValid : Bool`, `mgmtError : String`, `raised : Option (List String)` | `self.is_bound`, `self.management_form.is_valid()`, the management error message, and the `e.error_list` of a raised `ValidationError` | R | type bijection in mapping.md; these are the bound inputs that drive which production path `full_clean` takes |
| 2 | `let mut nonForm := mkErrorList [] (some "nonform")` | `self._non_form_errors = self.error_class(error_class='nonform')` (`:336`, POST-patch) | R / A-reference | the `ErrorList` constructor's class-string behavior is modeled deeply as `mkErrorList`; `some "nonform"` ↔ `error_class='nonform'`. G-AX validates `mkErrorList`'s `cssClass` field == the real constructor over fuzzed inputs. This is the FIRST changed site. |
| 3 | `if !isBound then return nonForm` | `if not self.is_bound: return` (`:339`) | I | identical early return; the already-constructed (nonform-classed, empty) collection is what `non_form_errors()` returns |
| 4 | `if !mgmtValid then nonForm := nonForm.append mgmtError` | `if not self.management_form.is_valid(): ... self._non_form_errors.append(error)` (`:341-353`) | I | append one management message; CSS class unchanged by `append`. UNCHANGED by the patch, modeled to keep the spec a faithful input→output relation (frame discipline, directive 5) |
| 5 | `if let some errs := raised then nonForm := mkErrorList errs (some "nonform")` | `except ValidationError as e: self._non_form_errors = self.error_class(e.error_list, error_class='nonform')` (`:382-383`, POST-patch) | R / A-reference | the SECOND changed site: wholesale reconstruction from `e.error_list` with `error_class='nonform'`. `errs` ↔ `e.error_list` (R, message-list bijection); the class string via the deeply-modeled `mkErrorList` (A-reference, G-AX). Reconstruction discards any appended management message — matches Python reassignment. |
| 6 | `return nonForm` | the value subsequently read by `non_form_errors()` | I | identical: the produced collection is the function output |

No op in `implementation_nonFormErrors` is changed-inexpressible. The two changed
sites are the addition of the `nonform` class string; that string behavior is
modeled deeply via `mkErrorList` (A-reference, G-AX-validated), not axiomatized.
There is **no consumed axiom** and **no opaque callee** (the `axioms` region is
empty); the proof discharges by case analysis on `isBound`, `mgmtValid`, `raised`.

## Why the spec sees the bug (G-DIFF)

The pre-patch impl constructs the collection with `none` (no extra class) at both
sites, so its `cssClass` is `"errorlist"`. The `problem_spec_nonFormErrors`
conjunct `result.cssClass = "errorlist nonform"` is therefore unsatisfiable for
the pre-patch impl on every input — `correct_nonFormErrors` is unclosable
(verified: prepatch fails G-VERIFY on the discriminating clause).
