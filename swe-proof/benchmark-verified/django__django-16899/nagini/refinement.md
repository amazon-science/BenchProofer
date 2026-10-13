# refinement.md — django__django-16899

The operation-by-operation correspondence between `model.py`'s implementation
(the `check_reference` impl region, building the message via the deep
`diagnostic_message` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == the real construct by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `_check_readonly_fields_item` error branch

Gold hunk (`django/contrib/admin/checks.py`, `except FieldDoesNotExist:`):
```
- "The value of '%s' is not a callable, an attribute of "
- "'%s', or an attribute of '%s.'"            % (label,          cls, model_label)
+ "The value of '%s' refers to '%s', which is not a callable, "
+ "an attribute of '%s', or an attribute of '%s.'" % (label, field_name, cls, model_label)
```

| # | model.py impl op (`check_reference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `label, value, cls, model_label: List[int]` | the `str`s `label`, `field_name`, `obj.__class__.__name__`, `obj.model._meta.label` | R | `str` ↔ `List[int]` code points (mapping.md §2). `value` ↔ `field_name`. |
| A2 | guard `resolves: bool`; `if resolves: return []` | the four unchanged early `return []` paths (`callable` / `hasattr(obj,·)` / `hasattr(obj.model,·)` / `get_field` succeeds) | R | `resolves` ≡ the disjunction of the four UNCHANGED lookups (mapping.md §2). The patch does not touch them; abstracting them as one boolean is sound because the tested behaviour does not depend on which path resolves, only on the error-branch message. |
| A3 | `result + [1]` then `+ label` then `+ [2]` then `+ value` then `+ [3]` then `+ cls` then `+ [4]` then `+ model_label` then `+ [5]` (= `diagnostic_message(...)`) | `"The value of '%s' refers to '%s', which is not a callable, an attribute of '%s', or an attribute of '%s.'" % (label, field_name, cls, model_label)` | R + I | The `%`-template is the interleaving of FIVE fixed prose pieces with FOUR `%s` substitutions, in the order intro, label, refers-prose, **field_name**, which-not-prose, cls, or-attr-prose, model_label, end-prose. Each fixed prose piece ↔ a distinct marker token `[1..5]` (**R**, the marker↔literal bijection of mapping.md §2; the prose is constant so its characters are immaterial to the discriminating behaviour). Each `%s` ↔ the corresponding code-point carrier spliced at the same position (**I**, identical concatenation order). The inserted `value`-segment (marker `[2] + value`) is exactly the added `' refers to '%s'` piece + the new `field_name` argument. |
| A4 | `result` returned as a `List[int]` (empty ⟺ no error) | wrapped by `checks.Error(msg, obj=obj.__class__, id="admin.E035")` inside `[ ... ]`, or `[]` | R | the `checks.Error` wrapper's `obj=`/`id=` fields are UNCHANGED and immaterial; the F2P tests compare the Error's MESSAGE (and the unchanged `obj`/`id`). Empty vs non-empty result ↔ no-error vs one-error list (mapping.md §2). |

The discriminating content of the change — the offending reference VALUE is now
named in the message, as its own interpolated segment immediately after the
label — lives in the `seg_refers() + value` term of `diagnostic_message`
(model) ⇔ the inserted `' refers to '%s'` prose + `field_name` argument (real).
The pre-patch template had no value slot; `model_prepatch.py` reproduces that
(it concatenates `[1] + label + [6] + cls + [4] + model_label + [5]`, marker
`[6]` standing for the old combined `"' is not a callable, an attribute of '"`
prose, with NO `value`) and **fails** the postcondition
`ToSeq(Result()) == diagnostic_message(...)` — which requires the value to be
present — exactly the spec sensing the change (G-DIFF).

## B. The discriminating value-position postcondition

`check_reference` additionally `Ensures`, on the error path, that the value
appears as a contiguous segment at the offset `len(seg_intro)+len(label)+
len(seg_refers)`:
```
ToSeq(Result()).drop(len(seg_intro())+len(label)+len(seg_refers())).take(len(value)) == ToSeq(value)
```
This is the structural witness that the message NAMES the value (not merely its
position): an implementation that drops the value, or that places `cls` where
the value belongs (the pre-patch shape), cannot satisfy it. It is grounded
entirely in the input carrier `value` (directive 8: no oracle echo — the
result must be *produced by* concatenating the actual `value`, not equal to a
constant). It is a consequence of A3 and is tagged **I** (a structural identity
of the same concatenation).

## C. No consumed axioms; the message construction is the A-reference

There is no `@ContractOnly` axiom the proof consumes. The one operation that
changed — the message template — is modelled **deeply** (the spelled-out
`diagnostic_message` concatenation, consumed in `check_reference`). It is
validated **== the real Python `%`-formatting of the post-patch template** by
axiom_check.py (G-AX), under the marker↔literal bijection of mapping.md §2: that
is the **A-reference**. The unchanged resolution lookups are abstracted by the
free boolean `resolves` (no Ensures-bearing contract), so there is no axiom to
over-claim and nothing live for G-AX to fuzz beyond the message-shape
equivalence.

## D. No kind-3 (unexpressible-changed-op) steps
Every step above is R, I, or A-reference. The changed operation (the message
template) is modelled deeply, not hidden behind an axiom about the function
under change.

## E. verify(model) ⇒ resolved
`check_reference` verifies only if, on the error path, its output equals
`diagnostic_message(label, value, cls, model_label)` (A3) — the template with
the value interpolated after the label — and only if the value occupies its own
segment there (B). By R (str ↔ List[int], the marker↔literal-prose bijection,
the `checks.Error`/list-wrapper identities, and `resolves` ≡ the unchanged
lookups) the verified construction equals the gold
`"...refers to '%s'..." % (label, field_name, cls, model_label)` on the tested
inputs; G-AX confirms the deep model reproduces the real `%`-formatting
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this document,
G-EQ) plus the A-reference message-shape check (G-AX); there is no consumed
callee axiom.
