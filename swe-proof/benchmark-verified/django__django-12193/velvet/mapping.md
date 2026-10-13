# mapping.md — django__django-12193

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3fb7c12158a2402f0f80824f6778112071235803`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of every callee. `spec_provenance: cold`.

Repo file under change: `django/forms/widgets.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `computeContextAttrs (mut attrs : List (String × Bool)) (checked : Bool)` | the body of `CheckboxInput.get_context` — `django/forms/widgets.py:524` (def), the affirmative-branch block at lines 525–528 that decides the `attrs` mapping handed to `super().get_context(name, value, attrs)` | the modeled changed operation: deriving the attribute mapping a checkbox-style control passes onward, when it has determined the control is affirmative |
| `attrs` (mut param) | the `attrs` parameter of `CheckboxInput.get_context` — the attribute mapping the caller owns and supplies (`django/forms/widgets.py:524`). For a multi-element control this **same `dict`** value is reused across the repeated `get_context(...)` calls (e.g. `SplitArrayWidget.get_context` builds one `final_attrs` and passes it to each sub-widget, `django/contrib/postgres/forms/array.py:133`). | the caller-owned mapping the operation must leave **unchanged** (the preserved frame, directive 5) |
| `checked` (read-only param) | `self.check_test(value)` — the boolean observation of whether this element's backing value makes the control affirmative (`django/forms/widgets.py:525`). Default `check_test` is module-level `boolean_check` (`django/forms/widgets.py:516`: `not (v is False or v is None or v == '')`). | read-only input: whether the affirmative state flag must be recorded; never altered |
| `effective` (return) | the value of `attrs` actually passed to `super().get_context(name, value, attrs)` at `django/forms/widgets.py:529` — post-patch the freshly-built `{**(attrs or {}), 'checked': True}` on the affirmative branch, or the caller's mapping on the negative branch | the onward attribute mapping whose entries drive this rendering's widget context |
| `setFlag m k v` / `withChecked attrs` (pure) | installing the `'checked': True` entry into a mapping (overwrite if present, add if absent) — the `{**(attrs or {}), 'checked': True}` dict literal | pure spec: the onward mapping when the control is affirmative |

The pre-patch repo behaviour the change overrides (refinement audit only, NOT in
the consumer spec view): the block was

```python
if self.check_test(value):
    if attrs is None:
        attrs = {}
    attrs['checked'] = True
return super().get_context(name, value, attrs)
```

`attrs['checked'] = True` is an **in-place item assignment on the caller's
`dict`**. Because that very `dict` object is reused across the repeated
renderings of a multi-element control, the affirmative flag set during one
element's rendering persists into the mapping the next element sees, so every
element rendered after the first affirmative one is also marked checked even when
its own backing value is negative. The patched code rebinds `attrs` to a FRESH
dict (`{**(attrs or {}), 'checked': True}`), so the caller's `dict` is never
written and the leak is removed.

## 2. Type abstraction (R-refinement) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the caller's `attrs` dict (HTML attribute mapping) | `List (String × Bool)` (an association list of attribute key → flag) | `attrs` ↔ `list(d.items())` over the touched key space; the `'checked'` key ↔ the `"checked"` association; missing key ↔ key absent from the list. `attrs = attrsOld` ↔ the caller's `dict` object is byte-equal to its entry value after the call |
| `self.check_test(value)` truth value | `checked : Bool` | `checked` ↔ `bool(self.check_test(value))`; for the default `check_test = boolean_check`, `True` ↔ `not (value is False or value is None or value == '')` |
| `attrs['checked'] = True` / `{**attrs, 'checked': True}` | `withChecked attrs = setFlag attrs "checked" true` | installing/overwriting the `"checked"` entry to `true`; `setFlag` is front-recursive so a present key is overwritten in place and an absent key appended — the same final mapping as the dict-spread `{**attrs, 'checked': True}` (key set is `keys(attrs) ∪ {'checked'}`, `'checked' ↦ True`, every other key unchanged) |
| the value passed to `super().get_context(...)` | `effective : List (String × Bool)` | `effective` ↔ the onward `attrs`; on the affirmative branch the dict-spread result, on the negative branch the caller's mapping verbatim |
| `attrs is None` default-to-`{}` | (absorbed) | the model carries `attrs` as a concrete mapping; the `None ⇒ {}` normalization is value-preserving for the touched key space (an absent caller mapping ↔ the empty list `[]`) and is not an observable distinct from "no entries", so it is not modeled as a separate branch — see refinement.md A4 note. The bool-value abstraction is faithful because the only entry the operation reads or writes is `'checked'`, whose value is `True`. |

A widget attribute `dict` carries arbitrary HTML attribute values; per SPEC_GUIDE
§2 it is abstracted to the touched key space with `Bool` values (the only entry
the operation reads or writes is `'checked' ↦ True`). G-CONF restricts the fuzz
to bool-valued attribute dicts over a small key pool including `'checked'`, so
the abstraction is exercised exactly where the operation is observable.

## 3. Callee provenance

The modeled operation is the **changed** code itself: the affirmative-branch
attribute-mapping assembly inside `CheckboxInput.get_context`. Under the
abstraction it reads one observation of the element's value (whether the control
is affirmative, `checked`) and the caller's attribute mapping, and produces the
onward mapping while leaving the caller's mapping unchanged. It calls no other
function whose contract the proof must consume, and it deep-models no foreign
callee:

- `self.check_test(value)` (default `boolean_check`, `django/forms/widgets.py:516`)
  is **not** axiomatized: its truth value is taken directly as the read-only
  input `checked : Bool`. The proof consumes no contract about it; G-CONF
  computes the same observation (`boolean_check`) on the Python side to bridge
  `checked`, so the observation is checked against the real callee rather than
  assumed.
- The dict-spread `{**(attrs or {}), 'checked': True}` is modeled directly as the
  pure `withChecked` (install the `"checked"` entry into a fresh mapping). The
  fact that it produces a SEPARATE value — leaving the caller's `dict` untouched
  — is the frame the spec pins (`attrs = attrsOld`), not an axiom.
- `super().get_context(name, value, attrs)` (`Widget.get_context`,
  `django/forms/widgets.py:223`) is unchanged and downstream of the modeled
  operation. The bug and fix are entirely about WHICH `attrs` value reaches it
  and whether the caller's `dict` was mutated to get there; the base method
  itself reads `attrs` through `build_attrs(self.attrs, attrs)` (merging the
  widget's own attrs) without mutating the caller's dict. It is therefore not on
  the modeled boundary — `effective` is exactly the `attrs` argument handed to
  it, which is the observable G-CONF reads back from the produced context
  (`ctx['widget']['attrs']`; the base widget's own attrs are empty, so the merge
  is the identity on the touched key space).

There is therefore **no axiomatized callee** in this bundle (no consumed axiom,
no A-reference): `axiom_check.py` is omitted and **G-AX is skipped** (cf. the
no-axiom exemplar `django__django-11490`).

The grounding the spec relies on (validated by G-CONF / G-RESOLVE, not assumed):

- a checkbox control rendered for an affirmative element must hand the base
  renderer a mapping carrying `'checked': True`, AND must leave the caller's
  attribute mapping unchanged so that a later element rendered from the same
  mapping is not forced affirmative;
- a checkbox control rendered for a negative element hands the base renderer the
  caller's mapping verbatim (no `'checked'` flag added) and likewise leaves the
  caller's mapping unchanged.

Both observations are executed directly against the real repo code by
`conformance_check.py` (it builds a real `CheckboxInput`, hands it a
caller-owned `attrs` dict, reads back both the onward mapping it produced and the
caller's dict after the call, and compares against the modeled rule), so the R/I
shadow is checked against the genuine operation, not a hand-copied rule.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12193`** so the
consumer-side verdict (§11.3) is reproducible. The input space (bool-valued
attribute dicts over the key pool `{"checked","class","id","foo"}` × the value
pool `{True, False, None, "", "x", 0, 1}` driving `check_test`) is enumerated for
the boundary combinations (every dict up to the full key set × every value,
including the F2P case `{"checked": False}` + `True`) and then sampled by the
seed during the ≥10⁵ fuzz loop.
