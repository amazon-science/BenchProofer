# mapping.md — django__django-14608

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7f33c1e22dbc34a7afae7967783725b10f1f13b1`, states the type
abstraction, and gives the provenance of the one deep-model reference (callee
source + the exact behaviour the deep model encodes).

Repo file under change: `django/forms/formsets.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `finish_group_clean(collection, rejected, rejection_messages)` | `BaseFormSet.full_clean(self)` — `django/forms/formsets.py:330` (the two `self._non_form_errors = self.error_class(...)` assignments at lines 336 and 383) | the modeled changed function (the formset whole-clean step that populates the non-form-error collection) |
| `MessageCollection` / `collection.css_class` / `collection.items` | the `ErrorList` instance bound to `self._non_form_errors` (`django/forms/formsets.py:336,383`); its rendered class attribute `ErrorList.error_class` and its held messages | the message collection the fix tags with the marker `nonform` |
| `class_attr(tag)` *(deep model — A-reference)* | `ErrorList.__init__` class-attribute rule — `django/forms/utils.py:84-90` (`'errorlist'` when `error_class is None`, else `'errorlist {}'.format(error_class)`) and the rendered class in `ErrorList.as_ul` (`utils.py:117-119`) | pure spec: the rendered class attribute the unchanged collection constructor assigns from an optional marker tag; deep model of the unchanged callee, validated `class_attr == ErrorList`’s rule by axiom_check.py (G-AX), NOT consumed as an axiom |
| `generic_class()` | the literal `'errorlist'` (`utils.py:88,90`) | pure spec: the generic list class as code points |
| `nonform_tag()` | the literal marker `'nonform'` the fix passes as `error_class='nonform'` (`formsets.py:336,383` post-patch) | pure spec: the marker tag as code points |
| `rejected` (bool) | whether the `try:` block at `formsets.py:365-383` raised `ValidationError` (the max/min/`clean()` cross-form checks) | abstract control flag selecting the exception assignment site |
| `rejection_messages` | `e.error_list` — the messages of the caught `ValidationError` (`formsets.py:383`) | the rejection messages the exception site rebuilds the collection from |
| `group_flagged` (bool) | whether `not self.management_form.is_valid()` held, causing the **unchanged** `self._non_form_errors.append(error)` step (`formsets.py:333-345`) to run AFTER the init site and BEFORE the `try:` block | abstract control flag for the in-domain management-form-invalid append; modeled (not scoped out) so the accepted-path held-items post-state is faithful (verdict DEFECT 1) |
| `group_message` (int) | the single `missing_management_form` `ValidationError` appended on that path (`formsets.py:337-344`) | the one group-wide message that append leaves in the collection; carried structurally as one code point (this change observes the held-items count/identity, not message text) |

The gold patch (two hunks) adds the keyword argument `error_class='nonform'` to
**both** `self.error_class(...)` constructions in `full_clean`:
`self.error_class()` → `self.error_class(error_class='nonform')` (init site,
line 336) and `self.error_class(e.error_list)` →
`self.error_class(e.error_list, error_class='nonform')` (exception site, line
383). Pre-patch, neither passes the marker.

`self.error_class` is the formset's `ErrorList` class (default
`django.forms.utils.ErrorList`, set at `formsets.py:76` from the constructor
argument `error_class=ErrorList`, `formsets.py:67`). The patch does not change
`ErrorList`; it only changes the argument the formset passes to it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `ErrorList` instance at `self._non_form_errors` | `MessageCollection` instance | a minimal class carrying only the two touched, observable fields |
| `ErrorList.error_class` (the rendered class attribute, a `str`) | `collection.css_class : List[int]` of Unicode code points | `s[k]` ↔ `css_class[k] == ord(s[k])`; the `str` `'errorlist nonform'` ↔ `[101,…,109]`; specification carried over `PSeq[int]` via `ToSeq` |
| the messages held in the `ErrorList` (`e.error_list`, a list of `ValidationError`/strings) | `collection.items : List[int]` | the per-message content is not what this change observes; the items are carried structurally (length / order preserved from `rejection_messages`) so the spec stays faithful to "the held messages are exactly the step’s product". Modeled as a `List[int]` whose elements mirror the rejection-message list element-for-element. |
| `self.error_class(...)` call (constructing a fresh `ErrorList`) | rebuilding `collection.css_class`/`collection.items` in place | constructing a new `ErrorList` and binding it to `self._non_form_errors` ↔ overwriting the modeled collection’s two fields; the observable post-state (rendered class + held items) is identical |
| the `str(text)`/`mark_safe`/template rendering downstream | omitted | the F2P tests observe `ErrorList.error_class` directly and the `str(...)`/`as_ul` rendering, both functions of `error_class`; `class_attr` models exactly that attribute (G-AX checks the rendered `<ul class="...">` too) |

`str` indexing/iteration is banned in Nagini, so the class attribute is carried
as `List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `class_attr` deep model ↔ `ErrorList`’s class-attribute rule (A-reference)
**Callee:** Django `ErrorList.__init__` (`django/forms/utils.py:84-90`) and the
rendered class in `ErrorList.as_ul`/`__str__` (`utils.py:113-127`). Source:

```python
def __init__(self, initlist=None, error_class=None):
    super().__init__(initlist)
    if error_class is None:
        self.error_class = 'errorlist'
    else:
        self.error_class = 'errorlist {}'.format(error_class)
...
def as_ul(self):
    ...
    return format_html('<ul class="{}">{}</ul>', self.error_class, ...)
def __str__(self):
    return self.as_ul()
```

The changed code does **not** change `ErrorList`; it only passes the marker tag
`'nonform'` as `error_class`. The class-attribute rule the proof relies on is
modeled **deeply** by the `@Pure` function `class_attr` (with `generic_class`
and `nonform_tag`) in the `pure` region — there is **no `error_list` axiom** the
proof consumes. The deep model is instead validated equal to the real callee
out-of-band by axiom_check.py (G-AX):

  `error_class is None / absent → 'errorlist'`,
  `error_class = t → 'errorlist ' + t` (single space separator).

Hence `class_attr(empty) == 'errorlist'` and `class_attr('nonform') ==
'errorlist nonform'`, which is what the F2P tests observe via
`str(formset.non_form_errors())` (`<ul class="errorlist nonform">…</ul>`) and
the admin `ErrorList([...], error_class='nonform')` comparison.

**Soundness check (G-AX):** `axiom_check.py` constructs the real
`django.forms.utils.ErrorList` with `error_class` None / absent / `'nonform'` /
2000 fuzzed marker tags and asserts `ErrorList(error_class=t).error_class ==
class_attr(t)` for every observation; it also asserts the rendered
`str(ErrorList(['Please submit at most 1 form.'], error_class='nonform'))`
equals `'<ul class="errorlist nonform"><li>Please submit at most 1 form.</li>
</ul>'` — the exact string an F2P test checks. It imports only Django itself
(the project the patch lives in); nothing test-private. Exit 0 iff sound.
(Outside the container Django is unavailable, so it prints `G-AX SKIP` and
returns 0; the orchestrator runs it in-container.)

The deep model is flag-independent: `ErrorList`'s class-attribute rule does not
depend on any setting (G-AX exercises it under a minimal `settings.configure`).
