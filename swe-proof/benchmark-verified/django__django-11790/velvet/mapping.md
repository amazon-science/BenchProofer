# mapping.md — django__django-11790

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b1d6b35e146aea83b171c1b921178bbaae2795ed`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo file under change: `django/contrib/auth/forms.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `configureFieldLimit (field) (modelLimit)` | the length-configuration block of `AuthenticationForm.__init__` — `django/contrib/auth/forms.py:193-194` (post-patch 193-196) | the modeled changed function |
| `resolveLimit (modelLimit : Option Nat)` | the expression `self.username_field.max_length or 254` — `django/contrib/auth/forms.py:194` | pure spec: the effective limit ("configured value, else default 254") |
| `BoundedField.maxLength` | `self.fields['username'].max_length` (a `forms.Field.max_length`, `int` or `None`) | the limit the field itself enforces |
| `BoundedField.widgetMaxLength` | `self.fields['username'].widget.attrs['maxlength']` (post-patch insertion) | the limit advertised on the rendered control |

The single value the routine reads, `modelLimit`, is
`self.username_field.max_length`, where `self.username_field =
UserModel._meta.get_field(UserModel.USERNAME_FIELD)`
(`forms.py:193`). `_meta.get_field(...)` is an **unchanged** accessor the patch
does not touch; it returns the account model's username field, whose
`max_length` is a `PositiveInteger` or `None`. No axiom is taken on it (it is a
plain field read, not a behavioral callee); its value is supplied as the free
input `modelLimit` and its provenance is exercised by G-CONF + G-RESOLVE
(section 3).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (section 4.1) uses to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.username_field.max_length` (`int >= 0`, or `None`) | `Option Nat` | `None` ↔ `none`; a non-negative `int n` ↔ `some n`. `CharField.max_length` is a `PositiveIntegerField`-style non-negative integer or `None`, so `Nat` is faithful. |
| `x or 254` over an `int`/`None` `x` | `resolveLimit` | Python truthiness: `None or 254 == 254`; `0 or 254 == 254`; any positive `n`, `n or 254 == n`. Modeled by `resolveLimit`: `none ↦ 254`, `some 0 ↦ 254`, `some n (n>0) ↦ n`. |
| `self.fields['username'].max_length` (assigned `int`) | `BoundedField.maxLength : Option Nat` | the field's enforced limit; after the routine it is `some (resolveLimit modelLimit)`. |
| `self.fields['username'].widget.attrs['maxlength']` (assigned `int`) | `BoundedField.widgetMaxLength : Option Nat` | the rendered-control limit; after the routine it is `some (resolveLimit modelLimit)`. `none` models the attribute being absent from `widget.attrs` (the pre-patch state). |

Other `AuthenticationForm` field attributes (label, the unrelated widget attrs
`autofocus`/`autocapitalize`/`autocomplete`) are untouched by this block and are
not carried in `BoundedField` (directive 5: only the mutated facets are
modeled). The `label`-setting `if` that follows the modeled block in
`__init__` is independent of the length facets and behaviorally unchanged by the
patch, so it is outside the modeled region.

## 3. Callee provenance — no axioms, no A-references (G-AX skip)

There are **no axiomatized callees** and **no deep-model A-references**: the
patch is a pure assignment block whose only input is the already-read
`max_length` value. `meta.json` records `axioms = []`,
`deep_model_references = []`, `conf_skip = false`.

`axiom_check.py` therefore prints `status=skip` and exits 0: there is no callee
contract to validate. The fidelity of the single input observation
(`self.username_field.max_length`) and of the `x or 254` selection is exercised
by:

* **G-CONF** (`conformance_check.py`): runs the patched assignment block
  verbatim — `username_max_length = model_limit or 254`, then both target
  assignments — over the full configured-limit domain (`None`, `0`, the default
  254, the F2P value 255, and 100 000 fuzzed non-negative ints) and confirms the
  R/I shadow `(resolveLimit, set both facets)` agrees on every input.
* **G-RESOLVE**: the gold `patch.diff` makes the official harness `resolved`
  end-to-end, exercising the real `_meta.get_field(...).max_length` read.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan section 4.1, 11.3)

`conformance_check.py` seeds its `random.Random` with **`11790`** so the
consumer-side verdict is reproducible. The shadow transliterates `resolveLimit`
and the two facet assignments (all R/I-tagged ops) to Python; there are no
A-tagged callees to leave as real callees.
