# refinement.md — django__django-14608

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildNonFormErrors` `do` block and the `cssClassFor` deep model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change — `BaseFormSet.full_clean` (`django/forms/formsets.py:336,383`)

Gold hunks (two construction sites of the non-form-error collection):
```
- self._non_form_errors = self.error_class()
+ self._non_form_errors = self.error_class(error_class='nonform')
  ...
- self._non_form_errors = self.error_class(e.error_list)
+ self._non_form_errors = self.error_class(e.error_list, error_class='nonform')
```

`self.error_class` is `django.forms.utils.ErrorList`. The change is: the
collection of non-form errors is constructed with the modifier label `'nonform'`
so it renders under the two-token CSS class `errorlist nonform` instead of the
bare `errorlist`. The messages it holds are unchanged.

| # | Solution.lean impl op (`buildNonFormErrors`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `errors : List (List Char)` | `e.error_list` (validation-error site) / `[]` (empty site) — the messages passed to `self.error_class(...)` | R | a Python list of message `str` ↔ `List (List Char)` (mapping.md §2). G-CONF bridges by reading the formset's reported messages. |
| 2 | `out.data = errors` (messages preserved) | the `initlist` argument the constructor stores (`super().__init__(initlist)`) | I | the construction stores exactly the messages passed; the patch does not alter them. G-CONF checks `list(non_form_errors()) == messages`. |
| 3 | `cssClassFor (some "nonform".toList)` attached as `out.cssClass` | the `error_class='nonform'` keyword argument → `ErrorList.__init__` computing `'errorlist {}'.format('nonform')` | A-reference + I | the modifier label `'nonform'` (I — the literal the patch adds) is fed to the **unchanged** class-string computation, modeled deeply by `cssClassFor`. The equality `cssClassFor == ErrorList(...).error_class` is the **A-reference** G-AX validates (mapping.md §3.1). No consumed axiom. |
| 4 | result `out : ErrorBox` | the `ErrorList` object assigned to `self._non_form_errors` | R | `ErrorList` ↔ `ErrorBox`, restricted to the two observed fields (messages, rendered class) — mapping.md §2. `as_ul`/`__str__` render `<ul class="{error_class}">`, the F2P observable. |

Discriminating content of the change — the modifier `'nonform'` is supplied, so
the rendered class is `errorlist nonform` rather than `errorlist`. This lives in
`out.cssClass = cssClassFor (some "nonform".toList)` (model) ⇔ the
`error_class='nonform'` argument (real). `Solution_prepatch.lean` supplies
`cssClassFor none` (the pre-patch no-argument construction) and **fails**
`out.cssClass = cssClassFor (some "nonform".toList)` (G-DIFF) — the exact clause
the F2P tests assert.

## On the two construction sites

The patch edits two `_non_form_errors = self.error_class(...)` lines (the
empty-init at the top of `full_clean` and the validation-error case in the
`except` block). Both apply the SAME behavioral delta: supply the `'nonform'`
modifier so the non-form-error collection renders under the modified class. They
are not independently-observable fixed behaviors — the F2P tests observe the
single rendered class on `non_form_errors()` — so a single `method`
(`buildNonFormErrors`) and a single `Solution_prepatch.lean` model the shared
delta. `conformance_check.py` exercises both sites (the validation-error path via
`oracle_build`, the empty path via `oracle_empty`).

## No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The class-string rendering — the only computation the
construction depends on — is **unchanged** by the patch (it is `ErrorList`'s own
`__init__`), modeled **deeply** as `cssClassFor` (an A-reference validated by
G-AX), not hidden behind an axiom about the function under change. The function
under change (`full_clean`'s construction site) is modeled directly by the
`do` block; what changed (supplying the `'nonform'` modifier) is the I literal in
step 3.

## verify(Solution) ⇒ resolved

`buildNonFormErrors` verifies only if `out.data = errors` (messages preserved,
step 2/I) and `out.cssClass = cssClassFor (some "nonform")` (the modified class,
step 3). By R (`ErrorList ↔ ErrorBox`, `str ↔ List Char`, message-list bijection)
the verified construction equals `self.error_class(messages, error_class='nonform')`
on the tested inputs; by G-AX the deep model `cssClassFor` equals the real
`ErrorList.__init__` class string (A-reference); by G-CONF the R/I transliteration
agrees with `patch.diff`'s behaviour (the messages and `errorlist nonform` class
read back from a real bound formset) on ≥10⁵ inputs. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited A-reference — and the gold patch resolves (G-RESOLVE). Trust points
are exactly the two of plan §1.1: A-reference soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
