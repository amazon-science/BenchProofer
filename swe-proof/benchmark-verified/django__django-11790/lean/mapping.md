# mapping.md — symbol binding & type bijection (django__django-11790)

## Modeled function
- **Lean** `implementation_authUsernameField : Option Nat → List (String × Nat) → UField`
- **Python** `django.contrib.auth.forms.AuthenticationForm.__init__`
  — `django/contrib/auth/forms.py:182-196 @ b1d6b35` (the username-field
  configuration block at the end of `__init__`).

The block under spec computes a single integer from the bound user model's
USERNAME_FIELD descriptor and applies it to the rendered username input. The
patch hoists `self.username_field.max_length or 254` into a local
`username_max_length` and assigns it to BOTH the bound field's `max_length`
AND the field widget's `maxlength` HTML attribute. Pre-patch, only the field's
`max_length` was set; the widget attribute was never populated, so the rendered
`<input>` lost its `maxlength`. The F2P tests assert
`form.fields['username'].widget.attrs.get('maxlength') == <expected>` where
`<expected>` is `255` (custom model) or `254` (default/None).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `self.username_field.max_length` (`int` or `None`) | `Option Nat` | `None → none`; a positive int `n → some n` |
| `max_length or 254` (truthiness) | `usernameMaxLength : Option Nat → Nat` | `or` is falsy on `None` AND `0`; both map to `254` |
| `self.fields['username'].max_length` (`int`) | `UField.maxLength : Nat` | the bound field's effective max length |
| `self.fields['username'].widget.attrs` (`dict`) | `UField.attrs : List (String × Nat)` | the integer-valued attribute map; `maxlength` is the touched key |
| `widget.attrs.get('maxlength')` (`int` or `None`) | `attrLookup result.attrs "maxlength" : Option Nat` | dict membership/get |
| `widget.attrs['maxlength'] = v` | `setAttr attrs "maxlength" v` | dict key assignment (overwrite/insert) |

`self.fields['username'].widget.attrs` in reality also holds the boolean
`autofocus` attribute (set on the `UsernameField` widget declaration). Booleans
are outside the integer-valued projection modeled here; `autofocus` is an
untouched non-integer attribute and is not part of the bijection. The frame
clause (`∀ k ≠ "maxlength", lookup unchanged`) ranges over the integer-valued
attribute map only. In every F2P path the integer attribute map starts empty
(no preexisting `maxlength`), which is what makes the pre-patch lookup `none`.

The `if self.fields['username'].label is None:` label-defaulting lines that
follow are unchanged by the patch and lie outside the modeled structure (only
the touched fields are modeled, per SPEC_GUIDE §2).

## Callee provenance
- `max_length or 254` — the changed expression, modeled DEEPLY as
  `usernameMaxLength` (a total `Option Nat → Nat` function). It is not a callee;
  it is plain control flow, tagged R/I in refinement.md. NOT axiomatized.
- The dict assignment `widget.attrs['maxlength'] = v` and field assignment
  `field.max_length = v` are concrete I-ops (`setAttr` / record update).
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.
  `axiom_check.py` is therefore a skip stub.

## Flag dependency
None. The behavior depends only on `username_field.max_length` being a positive
int vs falsy (None/0).

## G-CONF fuzz seed
Pinned seed: **11790**. ≥10^5 fuzzed inputs over `max_length ∈ {None, 0, small
ints, boundary ints}` × preexisting integer attribute maps (including empty and
maps already carrying a `maxlength`, to exercise overwrite + frame).
