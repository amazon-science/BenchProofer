# mapping.md — django__django-14608

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7f33c1e22dbc34a7afae7967783725b10f1f13b1`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference.

Repo file under change: `django/forms/formsets.py` (the `full_clean` method).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildNonFormErrors (errors : List (List Char))` | the `self._non_form_errors = self.error_class(...)` assignment in `BaseFormSet.full_clean` — `django/forms/formsets.py:336` (empty case) and `:383` (validation-error case) | the modeled changed behavior: constructing the non-form-error collection |
| `ErrorBox` (structure: `data`, `cssClass`) | `django.forms.utils.ErrorList` — `django/forms/utils.py:80` — restricted to the two touched fields: its message list (`.data`) and its rendered CSS class (`.error_class`) | the collection object the assignment produces |
| `cssClassFor (modifier : Option (List Char))` *(deep model — A-reference)* | `ErrorList.__init__`'s class-string computation — `django/forms/utils.py:84-90` | pure spec: the CSS class string the collection carries; deep model of the **unchanged** constructor, validated `cssClassFor == ErrorList(...).error_class` by axiom_check.py (G-AX), NOT consumed as an axiom |

The unchanged callee `ErrorList.__init__` computes:

```python
def __init__(self, initlist=None, error_class=None):
    super().__init__(initlist)
    if error_class is None:
        self.error_class = 'errorlist'
    else:
        self.error_class = 'errorlist {}'.format(error_class)
```

The modeled behavior the patch changes is *which* `error_class` argument the
`full_clean` assignment passes: pre-patch it passes none (the bare base class);
post-patch it passes the modifier label so the collection renders under the
two-token class. The rendered class is observable in `as_ul`
(`django/forms/utils.py:115-121`, `'<ul class="{}">'.format(self.error_class)`)
— exactly what the F2P tests assert (`<ul class="errorlist nonform">`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| an error message `str` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; empty `str` ↔ `[]`; `str` concat ↔ `List` `++` |
| the message list passed to / held by `ErrorList` (`e.error_list` / the `.data` it stores) | `List (List Char)` | a Python list of message strings ↔ a `List` of per-message `List Char`; order preserved; `len` ↔ `.length` |
| the modifier label `str` argument `error_class='nonform'` | `Option (List Char)` | `None` (no arg) ↔ `none`; a string label ↔ `some label.toList` |
| `ErrorList(...).error_class` (the rendered CSS class `str`) | `ErrorBox.cssClass : List Char` | the `'errorlist'` / `'errorlist {label}'` string ↔ its `List Char` |
| the `ErrorList` object itself | `ErrorBox` structure | only the two observed fields are modeled: stored messages (`.data`) and rendered class (`.error_class` ↔ `.cssClass`). Other `ErrorList` machinery (UserList behavior, `as_json`, etc.) is unchanged by the patch and not observed by the F2P tests. |

Lean `String`/`List Char` indexing is total and sound (no Nagini `List[int]`
workaround needed).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `cssClassFor` deep model ↔ `ErrorList.__init__` class string (A-reference)
**Callee:** `django.forms.utils.ErrorList.__init__`'s class-string branch
(`django/forms/utils.py:84-90`). The class-string computation is **unchanged**
by the patch — what changes is the *argument* `full_clean` supplies. The model
spells the computation out **deeply** as `cssClassFor` (pure region); there is
**no consumed axiom**. G-AX validates the deep model against the real
constructor: for `modifier = none`, `ErrorList(msgs).error_class == 'errorlist'`;
for `modifier = some label`, `ErrorList(msgs, error_class=label).error_class ==
'errorlist ' + label`. Boundary labels (`''`, `'nonform'`, `'nonfield'`,
multi-token) plus randomized fuzz.

Provenance note: the same `'errorlist {}'.format(error_class)` rendering is what
`Form`'s non-field errors already use via the `nonfield` label — the public
problem statement cites that precedent. The model is generic over the modifier
label and does not hardcode the rendering mechanism.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14608`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `buildNonFormErrors`'s impl (preserve the message list, attach
the `nonform`-modified class via `cssClassFor`) to Python and compares against
`patch.diff`'s behavior: a real bound `FormSet` whose `full_clean` raised
non-form errors, whose `non_form_errors()` collection's stored messages and
rendered `error_class` are read back. `cssClassFor` is R/I content (the
class-string computation is also exercised against the real constructor by G-AX
as the A-reference).
