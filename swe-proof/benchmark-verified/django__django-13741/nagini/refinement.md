# refinement.md — django__django-13741

The operation-by-operation correspondence between `model.py`'s implementation
(the `make_field` and `differs` impl regions, the deep `norm_seq` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

This change has two independently-fixed behaviours, each with its own failing
`model_prepatch` (G-DIFF needs one per independently-observable fixed
behaviour).

## A. The constructor default — `ReadOnlyPasswordHashField.__init__` (`django/contrib/auth/forms.py:57`)

Gold hunk (added line):
```
     def __init__(self, *args, **kwargs):
         kwargs.setdefault("required", False)
+        kwargs.setdefault('disabled', True)
         super().__init__(*args, **kwargs)
```

| # | model.py impl op (`make_field`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `required_kw, disabled_kw : Optional[bool]` (`None` = flag not named by caller) | the `**kwargs` keys `"required"` / `"disabled"` (present-or-absent) | R | `kwargs.setdefault(k, d)` ⇔ "`d` if key absent else caller value"; `None` ⇔ key absent (mapping.md §2). |
| A2 | `required = False if required_kw is None else required_kw` | `kwargs.setdefault("required", False)` | I | the pre-existing default, unchanged by the patch (kept identical so the prepatch isolates the disabled default). |
| A3 | `disabled = True if disabled_kw is None else disabled_kw` | `kwargs.setdefault('disabled', True)` | I | **the change**: an unnamed `disabled` defaults to `True`; an explicit value is preserved (setdefault only fills an absent key). |
| A4 | `return Field(required, disabled)` (stores both flags verbatim) | `super().__init__(*args, **kwargs)` → `Field.__init__` sets `self.required`, `self.disabled` | A-reference | the base constructor stores the two flags verbatim (`fields.py:84,87`); modelled deeply (the `Field` twin) and validated == the real `ReadOnlyPasswordHashField` construction by G-AX (mapping.md §3.1). |

The discriminating content of this hunk — `disabled` defaults to `True` rather
than the base `False` — lives in A3. `model_prepatch.py` reverts A3 to the
pre-patch behaviour (no `disabled` setdefault ⇒ base default `False`) and
**fails** the postcondition `Implies(disabled_kw is None, Result().disabled ==
True)`, which is exactly the F2P assertion `field.disabled is True` (G-DIFF).

## B. The change decision — removal of `ReadOnlyPasswordHashField.has_changed`

Gold hunk (removed lines):
```
-    def has_changed(self, initial, data):
-        return False
```
(plus the now-redundant `bound_data` override, same deletion block).

Removing the override makes the field inherit the base `Field.has_changed`,
whose disabled short-circuit gives the same `False` for this field (it is now
`disabled` by default, hunk A) WITHOUT a hard-coded override.

| # | model.py impl op (`differs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `self : Field` (reads `self.disabled`) | the bound field instance (reads `self.disabled`) | R | `Field` twin ↔ `forms.Field`; `self.disabled` ↔ `self.disabled` (mapping.md §2). |
| B2 | `initial, data : Optional[List[int]]` | the `initial` / `data` arguments (`str` or `None`) | R | `str` ↔ `List[int]` code points; `None` ↔ `None` (mapping.md §2). |
| B3 | `if self.disabled: return False` | the inherited `Field.has_changed` disabled short-circuit (`fields.py:179-180`) | A-reference | the unchanged base behaviour, modelled deeply and validated == the real `Field.has_changed` by G-AX (mapping.md §3.2). The deleted override's `return False` is subsumed by this base path once the field is `disabled`. |
| B4 | `return norm_seq(initial) != norm_seq(data)` | the inherited `Field.has_changed` enabled path: `initial_value != data_value` with `None`→`''` (`fields.py:190-192`); `to_python` is the identity for the base field | A-reference + R | the base comparison, modelled deeply (`norm_seq` carries the `None`→empty normalisation); `str` inequality ↔ `PSeq[int]` inequality (mapping.md §2, §3.2). |

`model_prepatch_2.py` reverts `differs` to the deleted override's body
(`return False` unconditionally, ignoring `self.disabled`) and **fails** the
postcondition `Implies(not self.disabled, Result() == (norm_seq(initial) !=
norm_seq(data)))`: an enabled field with differing values must report a change,
which the hard-coded override cannot. This is the spec sensing that the removed
override was unsound as the general field behaviour — the fix relies on the
base method, not on a constant.

## C. The `UserChangeForm.clean_password` removal

Gold hunk (`django/contrib/auth/forms.py:166-170`, removed): the
`clean_password` method that returned `self.initial.get('password')`.

This is the documented work-around the issue retires. It is rendered redundant
purely by hunk A: once the password field is `disabled` by default, the form
framework ignores any submitted password value in favour of the form's initial
data, so `cleaned_data['password']` already equals the initial value without a
bespoke `clean_password`. The behaviour is fully determined by the `disabled`
default (hunk A, modelled in `make_field`) and the disabled change-decision
(hunk B, modelled in `has_changed`); there is no separate operation to model
and no F2P test isolates it (the P2P test "The change form does not return the
password value" continues to pass under the disabled default). It therefore
carries no additional model construct — it is a *consequence* of A+B, not an
independent behaviour. (Documented here so the audit sees every gold hunk
accounted for; no kind-3 step.)

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* — the `disabled` default and the reliance on the base change-decision
— are modelled **deeply** (`make_field` spelling out the `setdefault` defaults;
`has_changed` spelling out the disabled short-circuit + the `None`-normalised
comparison), not hidden behind an axiom about the function under change. There
are **no consumed `@ContractOnly` axioms**: the only opaque elements are the
unchanged base field's flag storage and base change-decision, which appear as
**A-reference** deep models that G-AX validates against the real `forms.Field`.

## E. Termination obligations (totality)

Both contracted functions carry a `MustTerminate` precondition (and the
`Field` twin constructor carries one so the return statement can discharge
it). This makes the contracts TOTAL: an implementation that never returns
(an unbounded loop or self-recursion on either branch) cannot discharge any
postcondition clause vacuously under partial correctness. The real
counterparts are straight-line bounded work (a `setdefault` pair plus a
constructor call; a flag test plus one string comparison), so the obligation
is faithful — it excludes no behaviour the real patched code exhibits.

## F. verify(model) ⇒ resolved

`make_field` verifies only if an unnamed `disabled` yields `disabled == True`
(A3) while preserving the existing `required` default and any explicit values;
`has_changed` verifies only if a disabled field never reports a change (B3) and
an enabled field reports exactly the value inequality (B4). By R (kwargs ↔
`Optional[bool]`, `str` ↔ `List[int]`, the `Field` twin) the verified
constructor equals `ReadOnlyPasswordHashField.__init__` with the added
`setdefault('disabled', True)`, and the verified decision equals the inherited
base `Field.has_changed`. By G-AX the deep models equal the real base field
(both A-references). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited base callees — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom/deep-model soundness (G-AX) and refinement fidelity (this
document, G-EQ); there are no consumed axioms, so the first reduces to the two
A-reference validations.
