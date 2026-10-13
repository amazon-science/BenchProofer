# refinement.md — django__django-16667

Maps every operation in `implementation_coerceDateEntry` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `coerceDateEntry` (the date-coercion block of `SelectDateWidget.value_from_datadict`)

Post-patch repo code (`patch.diff`, `widgets.py:1158-1164`):
```python
try:
    date_value = datetime.date(int(y), int(m), int(d))
except ValueError:
    # Return pseudo-ISO dates with zeros for any unselected values,
    # e.g. '2017-0-23'.
    return "%s-%s-%s" % (y or 0, m or 0, d or 0)
except OverflowError:            # <-- the added handler
    return "0-0-0"               # <-- the fix
return date_value.strftime(input_format)
```

Lean impl (`implementation_coerceDateEntry`):
```lean
def implementation_coerceDateEntry
    (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
  match c with
  | DateEntry.valid => return some rendered
  | DateEntry.malformed => return some (pseudoIso y m d)
  | DateEntry.unrepresentable => return some "0-0-0"
```

The result is `Option String`: `some s` = the value `s` is handed on; `none` = no
value is produced (an uncaught failure aborts the reduction). The post-patch
function is TOTAL — every outcome is `some …`. (The prepatch impl produces `none`
on the unrepresentable outcome, modeling the pre-fix uncaught `OverflowError`.)

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `c : DateEntry` (input carrier) | the outcome of `datetime.date(int(y), int(m), int(d))`: succeeds / raises `ValueError` / raises `OverflowError` | **R** | the trichotomy is produced by the UNCHANGED callees `int`/`datetime.date`; the patch does not change how the entry is classified, only what one outcome returns. `c` carries the classification; its binding to `(y,m,d)` via the real callees is differential-tested by G-CONF (mapping.md). |
| 2 | `match c with \| DateEntry.valid => return some rendered` | `return date_value.strftime(input_format)` (the no-exception path) | **R** | the success outcome passes on the canonical rendering, modeled by the input `rendered` (`date_value.strftime(input_format)`); `some` marks that a value is handed on. UNCHANGED by the patch. |
| 3 | `\| DateEntry.malformed => return some (pseudoIso y m d)` | `except ValueError: return "%s-%s-%s" % (y or 0, m or 0, d or 0)` | **R** | the `ValueError` outcome yields the pseudo-ISO fallback. `pseudoIso` (pure helper) models `"%s-%s-%s" % (y or 0, m or 0, d or 0)`: empty component ↦ `"0"`, else verbatim, joined by `"-"`. UNCHANGED by the patch. |
| 4 | `\| DateEntry.unrepresentable => return some "0-0-0"` | `except OverflowError: return "0-0-0"` | **I** (deep model of the changed op) | **the fixed operation.** The added `except OverflowError` handler makes the too-large-magnitude outcome HAND ON the literal `"0-0-0"` (`some "0-0-0"`), instead of letting the `OverflowError` propagate and crash the request (modeled pre-fix as `none`). The impl matches it with `some` of an identical literal. This is the heart of the fix: a value is now produced where previously none was. |
| 5 | `pseudoIso y m d` (pure helper) | `"%s-%s-%s" % (y or 0, m or 0, d or 0)` | **R** | per-component: `"" or 0 → 0 → "0"` (Python falsy empty string), any non-empty string is truthy and rendered verbatim; the three are joined with `"-"`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched date-coercion block (with `c`/`rendered` computed by running the real
`int`+`datetime.date`+`strftime`).

## Callee provenance (no consumed axiom)

- `int(...)` / `datetime.date(...)` — the UNCHANGED callees whose
  raise-or-succeed behavior classifies the entry into the `DateEntry` trichotomy.
  The patch adds a handler for an outcome they already produced; it does not
  change them. Captured by the input `c`; the binding `(y,m,d) ↦ c` is exercised
  by G-CONF (which runs the real callees), not assumed — so there is no callee
  axiom to consume.
- `date_value.strftime(input_format)` — the UNCHANGED canonical rendering, modeled
  by the input `rendered`. Passed through on the `valid` outcome.
- `get_format("DATE_INPUT_FORMATS")[0]` / `formats.sanitize_strftime_format` — the
  input-format lookup, UNCHANGED and orthogonal to the fix; not modeled (it only
  shapes the text of `rendered`, an opaque spec input; the same format is used in
  both G-CONF legs and cancels).

## Soundness check (verify ⟹ correct)

- `problem_spec_coerceDateEntry` pins the result EXACTLY in EVERY outcome
  (directive 5 frame: no case left unconstrained): `valid → result = some
  rendered`, `malformed → result = some (pseudoIso y m d)`, `unrepresentable →
  result = some "0-0-0"`. No output component is left free; the `some` wrapper
  additionally pins TOTALITY (a value IS produced — `none` is forbidden in every
  case). Each branch is grounded in the actual inputs (`rendered`,
  `pseudoIso y m d`, the literal `"0-0-0"`) — directive 8: no ungrounded oracle
  (the postcondition is dischargeable only by the real per-branch computation,
  not by echoing an answer key).
- The prepatch impl reproduces the PRE-FIX behavior faithfully: it has NO handler
  for the unrepresentable-magnitude outcome (the `OverflowError` was uncaught and
  aborted the reduction), so that outcome produces `none` — no value is handed
  on, the analogue of the crashing request. It violates the spec on the
  discriminating clause `c = DateEntry.unrepresentable`: the spec requires
  `result = some "0-0-0"`, but the prepatch yields `none`, reducing the third
  conjunct to the unprovable `none = some "0-0-0"` (`False`). Its carried gold
  proof cannot close (G-DIFF/G-PANEL — verified: `Solution_prepatch.lean` fails
  with unsolved goal `False`).
- This discriminating case is precisely the FAIL_TO_PASS assertions added by the
  test patch: a month of `str(sys.maxsize + 1)` must coerce to `"0-0-0"`
  (`test_value_from_datadict`) so the field then rejects the entry as
  `"Enter a valid date."` (`test_form_field`, and the `f.clean("0-0-0")` row in
  `test_datefield_1`) — instead of crashing with an uncaught `OverflowError`.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  date-coercion block over hand-picked edge cases (a component `> sys.maxsize`
  ⇒ `"0-0-0"`; impossible month/day and non-numeric text ⇒ pseudo-ISO; a
  representable date ⇒ the rendering) plus ≥1e5 fuzzed `(y, m, d)` triples.
