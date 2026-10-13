# mapping.md — django__django-13741

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d746f28949c009251a8741ba03d156964050717f`, states the type
abstraction, and gives the provenance of each deep-model reference (the
unchanged base callees the modelled functions compose / inherit).

Repo file under change: `django/contrib/auth/forms.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `make_field(required_kw, disabled_kw)` | `ReadOnlyPasswordHashField.__init__` — `django/contrib/auth/forms.py:57-59` | the modeled changed constructor: the keyword defaults the read-only-hash field installs before delegating to the base field |
| `Field` (model class, fields `required`, `disabled`) | `django.forms.fields.Field` — `django/forms/fields.py:57` | minimal twin of the base field: only the two flags the change touches |
| `differs(self, initial, data)` | `django.forms.fields.Field.has_changed` — `django/forms/fields.py:175-192` | the generic change decision the field now INHERITS (the bespoke override is removed by the patch) |
| `norm_seq(v)` | the `None`→`''` normalisation inside `Field.has_changed` (`django/forms/fields.py:190-191`) + `Field.to_python` identity (`fields.py:123-124`) | pure spec: an absent value is the empty value |

Pre-patch repo symbols the change removes (referenced by the refinement audit,
NOT by the consumer spec view): `ReadOnlyPasswordHashField.bound_data`
(`forms.py:61-64`), `ReadOnlyPasswordHashField.has_changed` (`forms.py:66-67`,
the unconditional `return False` override), and `UserChangeForm.clean_password`
(`forms.py:166-170`). The first two are subsumed by the base `Field.bound_data`
/ `Field.has_changed` once `disabled=True` is the default; the third is the
documented work-around the issue asks to retire.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `kwargs.setdefault(k, default)` over a `**kwargs` dict (`forms.py:58-59`) | an explicit `Optional[bool]` parameter per flag, `None` ⇔ "key absent from kwargs" | `kwargs.setdefault('disabled', True)` then `Field.__init__(disabled=...)` ⇔ `disabled = disabled_kw if disabled_kw is not None else True`; likewise `required` |
| `self.disabled` / `self.required` attributes set by `Field.__init__` (`fields.py:84,87`) | the `Field` twin's `disabled` / `required` bool fields | `self.disabled` ↔ `Field.disabled`; `self.required` ↔ `Field.required` |
| the text values `initial`, `data` (`str` or `None`) of `has_changed` | `Optional[List[int]]` of Unicode code points (`None` = absent) | `s` ↔ list of `ord(s[k])`; `None` ↔ `None`; specification content via `PSeq[int]` (`ToSeq`) |
| `initial_value != data_value` string inequality with `None`→`''` (`fields.py:190-192`) | `norm_seq(initial) != norm_seq(data)` (PSeq inequality, `None`→empty) | `str` `!=` ↔ `PSeq[int]` `!=`; empty `str` ↔ empty `PSeq` |

`str` indexing/iteration is banned in Nagini, so text is carried as
`List[int]`; the change-decision content is phrased over `PSeq[int]` via
`ToSeq`. `**kwargs`/defaults are made explicit positional `Optional[bool]`
params per the type-modeling table (SPEC_GUIDE §2).

The much larger remainder of `Field.__init__` (widget construction,
`error_messages`, `validators`, localization) does not read or write the two
flags the change concerns and is omitted from the twin (only the touched
fields are modelled).

## 3. Deep-model references (kind A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**. The two unchanged base
behaviours the modelled functions compose are spelled out DEEPLY in `model.py`
and validated `== the real base field` out-of-band by `axiom_check.py`.

### 3.1 `make_field` ↔ `ReadOnlyPasswordHashField.__init__` + `Field.__init__` (A-reference)
**Callee:** the base field constructor `Field.__init__` (`django/forms/fields.py:57`),
which stores `self.required = required` and `self.disabled = disabled`
(`fields.py:84,87`) verbatim — there is no further defaulting or coercion of
these two flags. The subclass constructor installs the two presentation
defaults via `setdefault` (post-patch: `required→False`, `disabled→True`)
before delegating. Because `setdefault` only fills an ABSENT key, an explicitly
passed flag is preserved. The deep model `make_field` reproduces exactly this:
default `required=False`, default `disabled=True`, explicit value kept.
G-AX constructs the REAL `ReadOnlyPasswordHashField` over all kwarg
combinations (each flag unnamed / True / False) and asserts the resulting
`.required` / `.disabled` equal the model. The decisive default the F2P test
`test_readonly_field_has_changed` pins — `ReadOnlyPasswordHashField().disabled
is True` — is asserted directly.

### 3.2 `has_changed` ↔ `Field.has_changed` (A-reference)
**Callee:** the base `Field.has_changed(self, initial, data)`
(`django/forms/fields.py:175-192`). Source at base_commit:

```python
def has_changed(self, initial, data):
    # Always return False if the field is disabled since self.bound_data
    # always uses the initial value in this case.
    if self.disabled:
        return False
    try:
        data = self.to_python(data)
        ...
    except ValidationError:
        return True
    initial_value = initial if initial is not None else ''
    data_value = data if data is not None else ''
    return initial_value != data_value
```

For the base `Field`, `to_python` is the identity (`fields.py:123-124`) and the
field defines no `_coerce`, so the body reduces to: return `False` when
disabled; otherwise compare `initial` against `data` with `None` treated as
`''`. The deep model `has_changed` encodes exactly that (the disabled
short-circuit, then `norm_seq(initial) != norm_seq(data)`). `ReadOnlyPasswordHashField`
extends `forms.Field` directly, so this inherited method is precisely what the
patched field uses once its bespoke override is removed. The model symbol for
this method is named `differs` (behavioural). G-AX runs the REAL base
`Field.has_changed` over disabled/enabled fields and a battery of
`(initial, data)` pairs (including `None`↔`''` boundaries) and asserts every
observation equals the model.

**Soundness check (G-AX):** `axiom_check.py` configures a minimal Django, then
(1) constructs the REAL `ReadOnlyPasswordHashField` over 9 kwarg combinations
and asserts `.required`/`.disabled` match `make_field`, including the headline
`ReadOnlyPasswordHashField().disabled is True`; (2) drives the REAL base
`Field.has_changed` over 14 value pairs × {disabled, enabled} and asserts each
result matches `has_changed`; (3) confirms the composed
`ReadOnlyPasswordHashField().has_changed('aaa','bbb') is False`. It imports only
Django (the repo under test, importable in-container) and the stdlib. Exit 0
iff sound. Verified: exit 0 against the patched tree; it correctly FAILS
against the pre-patch tree (`.disabled` is `False` there) — i.e. the deep model
is tight to the fix.
