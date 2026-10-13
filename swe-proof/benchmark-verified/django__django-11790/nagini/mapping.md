# mapping.md — django__django-11790

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b1d6b35e146aea83b171c1b921178bbaae2795ed`, states the type
abstraction, and gives the provenance of the deep-model reference (there are no
consumed axioms in this bundle).

Repo file under change: `django/contrib/auth/forms.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `configure_username_field(declared_max_length, widget_attrs)` | the username-field configuration block inside `AuthenticationForm.__init__` — `django/contrib/auth/forms.py:192-194` (body lines 193-194; post-patch 193-195) | the modeled changed behaviour (configure the login identifier field's length limit and the rendered widget attribute) |
| `resolve_limit(declared)` | the expression `self.username_field.max_length or 254` — `django/contrib/auth/forms.py:194` (post-patch line 193) | pure spec: declared-maximum-or-default resolution |
| `default_limit()` | the literal `254` in `... or 254` | pure spec: the default length limit when the model declares no maximum |
| `attr_maxlength()` | the widget-attribute key `'maxlength'` written by `self.fields['username'].widget.attrs['maxlength'] = username_max_length` — post-patch `django/contrib/auth/forms.py:195` | pure spec: the dedicated length-limit attribute NAME, carried as that same string (identity, not an encoding) |
| `attr_other()` | the pre-existing key `'autofocus'` in `self.fields['username'].widget.attrs`, set on the `UsernameField` widget at `forms.py:168` (`'autocapitalize'`/`'autocomplete'` from `UsernameField.widget_attrs`, `forms.py:65-69`, are further such keys) | pure spec: a witness that unrelated, pre-configured widget attributes survive the operation; carried as that same string |

`self.username_field` is `UserModel._meta.get_field(UserModel.USERNAME_FIELD)`
(`forms.py:193`); its `.max_length` is the model field's declared maximum
(`None` for an `IntegerField` such as `IntegerUsernameUser.username`; an int
for a `CharField` such as `CustomEmailField.username = CharField(max_length=255)`).

The pre-patch repo line the change augments (for the refinement audit):
`self.fields['username'].max_length = self.username_field.max_length or 254`
(`forms.py:194`) — it sets only the field-level limit; the widget's `maxlength`
attribute is never written. The gold patch hoists the resolved value into a
local `username_max_length` and adds the widget write.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.username_field.max_length` — an `Optional[int]` (`None` ⇔ "no declared maximum"; an int ⇔ the declared maximum) | `declared_max_length: Optional[int]` | `None ↔ None`; int ↔ the same int |
| `x or 254` (Python truthiness: `None`/0 → `254`, else `x`) on a model-field `max_length` | `resolve_limit(declared)` = `default_limit()` if `declared is None or declared == 0` else `declared` | exact: the model mirrors Python truthiness on the `int`/`None` domain. A declared `max_length` of `0` is falsy, so `or 254` selects 254 there just as it does for `None`, and `resolve_limit` now selects the default on BOTH. See the note below: `0` is REACHABLE and measured. |
| `self.fields['username'].max_length` (the form field's length-limit attribute, read by server-side validation) | `Result()` (the returned `int`) | identity on the integer value |
| `self.fields['username'].widget.attrs` (a `dict` mapping attribute-name **strings** to values of MIXED runtime types) | `widget_attrs: Dict[str, object]` mapping an attribute NAME to its value; the length limit's own value is injected by `limit_value(n)` | membership and per-key value are observed. The NAME domain is carried as `str`, the identity on the real keys: `'maxlength' ↔ attr_maxlength()` and `'autofocus' ↔ attr_other()` are literally the same strings. This is what makes the name axis faithful. Under the former `Dict[int, ...]` carrier a name was an int and so was a LENGTH, and the two were interchangeable: `default_limit() + 746 == 1000 == attr_maxlength()`, so an implementation could publish the limit under a key computed out of the length domain and the model would call that key the maxlength attribute, while in the repo `widget.attrs[1000]` leaves `widget.attrs.get('maxlength')` as `None`. Text and lengths are disjoint domains here, so no arithmetic on numbers can ever produce an attribute name and a name may only be written down or compared for equality (no `str` indexing, which Nagini bans anyway). The VALUE domain is **opaque** (`object`) for the matching reason on the other axis: the real values are heterogeneous, so nothing may be computed from a value read out of the map. MEASURED on the real gold-patched stock form: `{'autofocus': True (bool), 'autocapitalize': 'none' (str), 'autocomplete': 'username' (str), 'maxlength': 150 (int)}` — every key a `str`. Equality/identity (`==`, `is`) remain expressible on both axes because they are total on the real names and values as well. |
| `self.fields['username'].widget.attrs['maxlength'] = username_max_length` (an in-place dict write) | `widget_attrs[attr_maxlength()] = username_max_length` (in-place dict write under full permission) | identity on the dict mutation |

**Note on `or 254`.** A declared `max_length` of `0` IS reachable for a
`USERNAME_FIELD`, and the earlier claim that it is not was wrong. MEASURED:
`fields.E121` ("'max_length' must be a positive integer") is raised by
`CharField._check_max_length_attribute`, so it fires only for `CharField` and
its subclasses. With a real installed `AUTH_USER_MODEL` whose
`USERNAME_FIELD` is `TextField(unique=True, max_length=0)` or
`BinaryField(unique=True, max_length=0)`, the FULL registry
`django.core.checks.run_checks()` returns CLEAN (no errors, no warnings), and
the real gold-patched form yields `field.max_length == 254` and
`widget.attrs['maxlength'] == 254` — because `0 or 254` is `254`.
`IntegerField(unique=True, max_length=0)` is likewise error-free (only the
`fields.W122` warning). `resolve_limit` therefore mirrors truthiness, sending
`None` AND `0` to the default; this is what the real expression does, so the
leg stays an exact R-refinement rather than a domain assumption. The F2P tests
exercise two of the branches: `CustomEmailField` (`max_length=255` → 255) and
`IntegerUsernameUser` (`max_length is None` → 254).

`str`/object attribute access is not modeled directly; the widget attribute map
is the `Dict[str, object]` carrier (names textual, values opaque — see the row above) and the
field's `max_length` is the returned int. No `str` indexing is used (Nagini
bans it).

## 3. Callee provenance / deep-model reference (checked by G-AX / axiom_check.py)

### 3.1 The whole operation is the A-reference (no consumed axiom)
There is **no `@ContractOnly` axiom** in this bundle: the changed behaviour is
the field/widget configuration itself, which is modeled **deeply** (the length
resolution `resolve_limit` and the two writes — the returned `field.max_length`
and `widget_attrs[attr_maxlength()]` — spelled out in `model.py`'s impl region).

The single **A-reference** is therefore the claim that this deep model equals
the real repository operation. `axiom_check.py` (G-AX) validates it by executing
the REAL gold-patched `AuthenticationForm.__init__`
(`django/contrib/auth/forms.py:183-196`) against a range of user models whose
`USERNAME_FIELD` declares varying `max_length` (including `None`), and asserting
for each that

  `form.fields['username'].max_length == resolve_limit(declared)`  and
  `form.fields['username'].widget.attrs.get('maxlength') == resolve_limit(declared)`,

i.e. both the field-level limit and the widget attribute carry the resolved
value, with `None` resolving to the default `254`. It also checks that the
pre-existing widget attributes (`autocapitalize`, `autocomplete`, `autofocus`)
survive. It imports only the standard library and the Django package under
evaluation (the very module the gold patch edits). Exit 0 iff every observation
matches the deep model. No flag dependency.

The behavioural delta the F2P tests observe lives entirely in the second write:
pre-patch, `widget.attrs.get('maxlength')` is `None` (the regression — the
attribute is never set); post-patch it equals the resolved limit. This is
exactly what `attr_maxlength() in widget_attrs` (and its value) pins in the
spec, and exactly the clause `model_prepatch.py` fails on (G-DIFF).
