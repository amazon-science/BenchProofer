# refinement.md — django__django-14608

The operation-by-operation correspondence between `model.py`'s implementation
(the `finish_group_clean` impl region + the deep `class_attr` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The whole-clean step — `BaseFormSet.full_clean()` (`django/forms/formsets.py:330-383`)

Gold hunks (the two changes):
```
# init site (formsets.py:336)
-        self._non_form_errors = self.error_class()
+        self._non_form_errors = self.error_class(error_class='nonform')

# exception site (formsets.py:383)
-            self._non_form_errors = self.error_class(e.error_list)
+            self._non_form_errors = self.error_class(
+                e.error_list,
+                error_class='nonform'
+            )
```

Both hunks add the keyword `error_class='nonform'` to a `self.error_class(...)`
construction (the formset's `ErrorList`). The pre-patch code constructed the
collection with no marker tag, so it rendered `class="errorlist"`; the fix makes
it render `class="errorlist nonform"`.

| # | model.py impl op (`finish_group_clean`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `collection: MessageCollection` with fields `css_class`, `items` | `self._non_form_errors` (an `ErrorList`); its `.error_class` (rendered class attr) and held messages | R | the message collection with only its two touched/observed fields modelled; `ErrorList.error_class` (a `str`) ↔ `collection.css_class : List[int]` of code points (mapping.md §2). |
| A2 | init site: `collection.css_class = [...'errorlist nonform']`; `collection.items = []` | `self._non_form_errors = self.error_class(error_class='nonform')` | A-reference + R | the changed construction is modeled **deeply**: the rendered class attribute is `class_attr(nonform_tag())` (the spelled-out `'errorlist ' + 'nonform'` rule in the `pure` region) and the freshly-constructed collection has no items **yet**. There is no consumed `error_list` axiom. The deep model `class_attr` is validated **== the real `ErrorList` class-attribute rule** out-of-band by G-AX (axiom_check.py asserts `ErrorList(error_class='nonform').error_class == 'errorlist nonform'`, and the rendered `str(...)`). Constructing a fresh `ErrorList` and binding it ↔ overwriting the collection's two fields (R, mapping.md §2). |
| A2b | `if group_flagged: collection.items = collection.items + [group_message]` | the **unchanged** `if not self.management_form.is_valid(): … self._non_form_errors.append(error)` step (`formsets.py:333-345`), executed AFTER the init site and BEFORE the rejection `try:` block | I + R | an UNCHANGED in-domain operation that the patch does not touch but that writes the same spec-observed `items` field on the accepted path. It is modeled (not scoped out) so the accepted-path post-state is faithful (verdict DEFECT 1): the control flag `group_flagged` ↔ `not self.management_form.is_valid()`, and the single appended `group_message` ↔ the one `missing_management_form` `ValidationError` appended. The collection is **appended to in place** (NOT rebuilt), so the marker class set at the init site is preserved — matching the real `.append(error)`. R: `e` (a `ValidationError`) ↔ one `int` code-point, since this change only observes the held-items count/identity structurally, not message text. |
| A3 | `if rejected:` branch | the `except ValidationError as e:` handler entered when the max/min/`clean()` checks raise (`formsets.py:382`) | R | the abstract control flag `rejected` selects the exception assignment site; whether the `try:` block raised ↔ `rejected` (mapping.md §1). |
| A4 | exception site: copy `rejection_messages` into `collection.items` (the loop) then `collection.css_class = [...'errorlist nonform']` | `self._non_form_errors = self.error_class(e.error_list, error_class='nonform')` | A-reference + R | same deep-model construction as A2, now carrying the rejection messages: the held items are exactly `e.error_list` (the loop refines list construction from `e.error_list`, element-for-element — R), and the rendered class is again `class_attr(nonform_tag())`. This site **rebuilds** the collection (binds a fresh `ErrorList`), so it **replaces** any group-wide message appended at A2b — matching the spec clause `Implies(rejected, ToSeq(items) == ToSeq(rejection_messages))`, independent of `group_flagged`. The `error_class='nonform'` keyword is the FIX; `class_attr` (A-reference, G-AX) is the real `ErrorList` rule it drives. |

The discriminating content of the change — the marker tag `'nonform'` making
the rendered class `'errorlist nonform'` rather than the bare `'errorlist'` —
lives in `class_attr(nonform_tag()) == generic_class() + PSeq(32) + nonform_tag()`
(model) ⇔ the `error_class='nonform'` keyword driving
`'errorlist {}'.format('nonform')` in the real `ErrorList` (A-reference). The
pre-patch sites pass no marker; `model_prepatch.py` / `model_prepatch_2.py`
reproduce that (`css_class = [...'errorlist']`) and **fail** the postcondition
`ToSeq(collection.css_class) == class_attr(nonform_tag())` — exactly the spec
sensing the change (G-DIFF).

## B. Two independently-fixed behaviours (G-DIFF, one prepatch each)

The gold patch fixes **two** independently-observable sites. Each prepatch
reverts exactly one (keeping the other patched and the shared spec
byte-identical):

| prepatch | site reverted | observed on path | fails on |
|---|---|---|---|
| `model_prepatch.py` | exception site (line 383): `self.error_class(e.error_list)` — no marker | `rejected == True` (the max/min/`clean()` rejection path the F2P `test_formset_validate_max_flag` / `test_formset_validate_min_flag` / `test_non_form_errors` exercise) | `ToSeq(collection.css_class) == class_attr(nonform_tag())` (`model_prepatch.py:102`) |
| `model_prepatch_2.py` | init site (line 336): `self.error_class()` — no marker | `rejected == False` (the default collection — empty, or holding a single missing-management-form message — which is what renders when there is no rejection) | `ToSeq(collection.css_class) == class_attr(nonform_tag())` (`model_prepatch_2.py:102`) |

Both fail on the same discriminating clause, on disjoint control paths — the
spec is strong enough that no implementation omitting the marker at **either**
site can verify.

Note on the held-items clause (verdict DEFECT 1): the spec's items
post-condition is the three-way `Implies(not rejected and not group_flagged,
len(items)==0) ∧ Implies(not rejected and group_flagged, ToSeq(items) ==
PSeq(group_message)) ∧ Implies(rejected, ToSeq(items) == ToSeq(rejection_
messages))`. This is faithful on **every** reachable path of the real
`full_clean`, including the in-domain accepted path where the unchanged
management-form-invalid `append` (A2b) leaves exactly one group-wide message in
the collection. An implementation that omits that append (the narrowed model
that previously masked the defect) fails the second conjunct, so the spec is
strictly stronger than before, never weaker — no ungrounded oracle is
introduced (the clause is pinned to the actual `group_message`/`rejection_
messages` carriers, directive 8). The css_class spine is byte-identical to the
pre-refinement bundle.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I (A2b is the unchanged
management-form-invalid `append`, an I+R step — an in-domain operation that is
modeled rather than dropped, per the verdict's DEFECT 1 root-cause lesson, so no
spec-observed field is left unmodeled on a reachable path). The one operation
that genuinely *changed* — tagging the constructed collection with the
`'nonform'` marker so its rendered class becomes `'errorlist nonform'` — is
modeled **deeply** (the spelled-out `class_attr`/`nonform_tag` rule consumed in
`finish_group_clean`, steps A2/A4, an **A-reference**), not hidden behind an
axiom about the function under change. There is **no consumed `error_list`
axiom**: the only callee, the unchanged `ErrorList` class-attribute rule,
appears only as the **A-reference** that G-AX validates the deep model against.
We never axiomatize the function under change (`full_clean`) nor the changed
operation.

## D. verify(model) ⇒ resolved

`finish_group_clean` verifies only if, on **every** outcome (`rejected` or not,
group-flagged or not), the collection's rendered class attribute equals
`class_attr(nonform_tag())` (A2/A4) and its held items are exactly the step's
product (empty; or the single group-wide message appended at A2b on the accepted
path; or the rejection messages on the rejected path). By R
(`ErrorList.error_class` ↔ `css_class : List[int]`;
constructing-and-binding a fresh `ErrorList` ↔ overwriting the modeled fields;
the items list ↔ `e.error_list` element-for-element) the verified step equals
the gold `full_clean`'s two `self.error_class(..., error_class='nonform')`
constructions on the tested inputs; by G-AX the deep model `class_attr` equals
the real `ErrorList` class-attribute rule (A-reference) and the rendered
`str(...)` is `<ul class="errorlist nonform">…</ul>`. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
