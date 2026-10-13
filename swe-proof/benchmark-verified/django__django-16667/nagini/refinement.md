# refinement.md — django__django-16667

The operation-by-operation correspondence between `model.py`'s implementation
(the `value_from_components` impl region and the live `construct_date` /
`render_success` / `render_out_of_range` axioms) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses the axiom's `Ensures`/`Exsures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The widget site — `SelectDateWidget.value_from_datadict` (`django/forms/widgets.py:1149`)

Gold hunk (after line 1163):
```
                 return "%s-%s-%s" % (y or 0, m or 0, d or 0)
+            except OverflowError:
+                return "0-0-0"
             return date_value.strftime(input_format)
```

The surrounding (unchanged) body of the function:
```
y = data.get(...); m = data.get(...); d = data.get(...)
if y == m == d == "":                       return None                # all-blank
if y is not None and m is not None and d is not None:                  # all-present
    try:
        date_value = datetime.date(int(y), int(m), int(d))             # construct_date
    except ValueError:
        return "%s-%s-%s" % (y or 0, m or 0, d or 0)                   # out-of-range fallback
    except OverflowError:        # <-- THE PATCH
        return "0-0-0"                                                 # overflow sentinel
    return date_value.strftime(input_format)                          # success render
return data.get(name)                                                 # not-all-present fallback
```

| # | model.py impl op (`value_from_components`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `all_blank`, `all_present`, `kind: int` | `y, m, d = data.get(...)` and the outcome of `datetime.date(int(y),int(m),int(d))` | R | `value`-shape ↔ classifiers (mapping.md §2): `all_blank ↔ y==m==d==""`, `all_present ↔ all three not None`, `kind ↔` the constructor's outcome. The only observable of the pinned behaviour is which outcome the widget produces. |
| A2 | `if all_blank: return []` | `if y == m == d == "": return None` (line 1153-1154) | R + I | the all-blank fast path, unchanged by the patch; `None` ↔ the empty code-point list (mapping.md §2). |
| A3 | `if all_present:` … else `return retrieve_raw()` | `if y is not None and m is not None and d is not None:` … else `return data.get(name)` (lines 1155, 1165) | R + A-consumed | the all-present guard, unchanged. The not-all-present `else` branch defers to the unchanged raw-retrieval callee: the model returns EXACTLY `retrieve_raw()` (content `raw_value()`, fully abstract) ↔ the real `return data.get(name)`, whose value may be `None` (the shape the gold tests observe) or arbitrary raw submitted text (e.g. `'2008-4-1'` posted under the bare field name) — the model assumes nothing about it (mapping.md §2, §3.4). |
| A4 | `date_token = construct_date(kind)` inside the `try` | `date_value = datetime.date(int(y), int(m), int(d))` inside the `try` (line 1159) | A-consumed | `construct_date` is the WEAKEST contract on `datetime.date` the proof needs: returns normally iff kind 0, raises `DateOutOfRange` (↔ `ValueError`) iff kind 1, raises `DateCapacityOverflow` (↔ `OverflowError`) iff kind 2 — and these two are the only rejections (mapping.md §3.1). The proof consumes its `Ensures(kind==0)` and both `Exsures`. G-AX confirms exhaustiveness/precedence against the real `datetime.date`. |
| A5 | `return render_success()` (after the call) | `return date_value.strftime(input_format)` (line 1164, post-patch) | R + A-consumed | the success-path render, unchanged by the patch; reached only when `construct_date` returns (kind 0). `render_success` returns a fresh non-empty code-point list whose content is `success_text()` (mapping.md §3.2); the success branch returns EXACTLY that callee's text (`ToSeq(Result()) == success_text()`), pinning the value to the callee, not a literal (directive 8). |
| A6 | `except DateOutOfRange: return render_out_of_range()` | `except ValueError: return "%s-%s-%s" % (y or 0, m or 0, d or 0)` (lines 1160-1163) | R + A-consumed | the out-of-range handler, unchanged by the patch. `DateOutOfRange ↔ ValueError`; `render_out_of_range` returns a fresh non-empty code-point list whose content is `out_of_range_text()` (mapping.md §3.3); the branch returns EXACTLY that callee's text. |
| A7 | `except DateCapacityOverflow: return [48,45,48,45,48]` | `except OverflowError: return "0-0-0"` (THE PATCH) | R + I | the patched handler. `DateCapacityOverflow ↔ OverflowError`; returning the code points `[48,45,48,45,48]` ↔ returning the literal `"0-0-0"` (mapping.md §1,§2). This is the single hunk the gold patch adds, modeled directly. |

The discriminating content of the change — a capacity-overflow failure
(`OverflowError`, kind 2) must be HANDLED (return the `"0-0-0"` sentinel,
returning normally), not allowed to escape and crash the request — lives in
`value_from_components` having an `except DateCapacityOverflow` clause that
returns the sentinel (model) ⇔ the added `except OverflowError: return "0-0-0"`
(real). The pre-patch caught only `ValueError`; `model_prepatch.py` reproduces
that (omits the `except DateCapacityOverflow` clause) and **fails** verification
on *"method raises no exceptions"* — because on kind 2 it lets the constructor's
`DateCapacityOverflow` escape, an exception the frozen spec never declares
(no `Exsures` on `value_from_components`). That is exactly the spec sensing the
change (G-DIFF), and the exact F2P observation: `value_from_datadict({year:
str(sys.maxsize+1), month:"12", day:"1"}) == "0-0-0"` (and the form is then
invalid, raising the field's `ValidationError`) rather than a 500-crashing
`OverflowError`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— adding a handler so the capacity-overflow rejection is funneled to the fixed
`"0-0-0"` sentinel instead of escaping — is modeled **directly** by the
`except DateCapacityOverflow` clause in `value_from_components` (step A7), driven
by the `construct_date` axiom's `Exsures(DateCapacityOverflow, kind==2)` (step
A4). The constructor itself, `datetime.date`, is UNCHANGED by the patch; it is an
**A-consumed** axiom whose two-class rejection behaviour (and exhaustiveness)
G-AX validates against the real callee. The two rendering callees (`strftime`
pseudo-success, `%`-format fallback) are also UNCHANGED **A-consumed** axioms,
present only to pin the success / out-of-range results to their callees rather
than to fabricated literals (G-AX validates each returns a non-empty rendering).
The not-all-present raw retrieval (`data.get(name)`) is likewise an UNCHANGED
**A-consumed** axiom (`retrieve_raw` / `raw_value`, mapping.md §3.4), fully
abstract so the branch can only echo the real callee's value — whether `None`
or arbitrary raw submitted text — never a hard-coded absent or fabricated text.
There is no axiom about the function under change
(`value_from_datadict`), and no A-reference deep model (the change is not a value
computation but the addition of an exception handler, modeled directly).

## C. verify(model) ⇒ resolved

`value_from_components` verifies only if it NEVER raises (its contract has no
`Exsures`) and, on a capacity-overflow outcome (kind 2), returns EXACTLY the
`"0-0-0"` sentinel (`ToSeq(Result()) == zero_zero_zero()`); and only if the
unchanged branches keep their behaviour (all-blank → empty rendering;
not-all-present → EXACTLY the raw-retrieval callee's value `raw_value()`, which
being fully abstract can only be produced by calling `retrieve_raw()` itself;
kind 0 → the success callee's text; kind 1 → the out-of-range callee's
text, both non-empty). By R (the value-shape classifiers ↔ `y/m/d` + the
constructor outcome; `DateOutOfRange`/`DateCapacityOverflow` ↔
`ValueError`/`OverflowError`; the code points `[48,45,48,45,48]` ↔ `"0-0-0"`;
`[]` ↔ `None` on the all-blank branch; `retrieve_raw()` ↔ `data.get(name)`)
the verified widget equals `value_from_datadict` with the added
`except OverflowError: return "0-0-0"` on the tested inputs; by G-AX (A-consumed)
the real `datetime.date`'s integer rejections are exactly `ValueError` /
`OverflowError` and nothing else escapes (so the two-handler `try` is complete),
and the two renderings are non-empty. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
callees — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
