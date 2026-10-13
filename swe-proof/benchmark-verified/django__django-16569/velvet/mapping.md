# mapping.md — django__django-16569

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 278881e37619278789942513916acafaa88d26f3`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/forms/formsets.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deletionFieldDecision (enabled offerOnExtra : Bool) (position : Option Nat) (initialCount : Nat)` | the per-row removal-control decision computed inside `add_fields(self, form, index)` — `django/forms/formsets.py:474` (decision expression at line 493) | the modeled changed function (the boolean decision whether to attach the removal control) |
| `enabled` | `self.can_delete` (`formsets.py:493`) | whether the removal control is enabled for the collection |
| `offerOnExtra` | `self.can_delete_extra` (`formsets.py:493`) | whether the control is also offered on surplus (non-prepopulated) rows |
| `position` | `index` argument of `add_fields` (`formsets.py:474`); `None` on the standalone template row (`empty_form` passes `index=None`, `formsets.py:264`) | the row's ordinal position, or absent |
| `initialCount` | local `initial_form_count = self.initial_form_count()` (`formsets.py:476`, def at `:190`) | count of pre-populated rows |
| `shouldOfferDeletion` *(deep model — R/I)* | the decision expression `self.can_delete and (self.can_delete_extra or (index is not None and index < initial_form_count))` (`formsets.py:493-495` post-patch) | pure spec: the desired guarded decision |
| `positionWithinInitial` *(deep model — R/I)* | the guarded comparison `index is not None and index < initial_form_count` (`formsets.py:494` post-patch) | pure spec: the position test, undefined-comparison guarded |

The downstream effect the positive decision triggers — `form.fields[DELETION_FIELD_NAME] = BooleanField(...)` (`formsets.py:494-498`) — is a shared continuation that does not influence the decision; it is not modeled and owed no contract.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.can_delete : bool` | `enabled : Bool` | `True ↔ true`, `False ↔ false` |
| `self.can_delete_extra : bool` | `offerOnExtra : Bool` | `True ↔ true`, `False ↔ false` |
| `index : int | None` | `position : Option Nat` | a non-negative `int i ↔ some i`; `None ↔ none`. `add_fields` is only ever called with `index` either `None` (the template row) or a non-negative enumeration index (`0..len-1`, from `enumerate(self.forms)`), so the carrier is `Option Nat`. |
| `initial_form_count : int` (≥ 0) | `initialCount : Nat` | `n ↔ n`. `initial_form_count()` returns `len(self.initial)` (≥0) or a management-form count (≥0); never negative. |
| the decision (whether to attach the deletion field) | `Except ControlErr Bool` | the boolean verdict `b ↔ Except.ok b`; the Python `TypeError: '<' not supported between instances of 'NoneType' and 'int'` raised by the pre-patch unguarded comparison ↔ `Except.error ControlErr.positionComparisonUndefined`. The patched code never raises ⇒ always `Except.ok`. |

`index` is non-negative in every real call site, so `Option Nat` is a faithful
carrier; the only distinction the behaviour reacts to is present-vs-absent and
the `<` comparison, both exact on `Nat`.

## 3. Callee provenance

No unchanged callee is axiomatized or deeply referenced. The changed operation
is a language-level short-circuiting boolean expression with a guarded integer
comparison — there is no foreign callee whose behaviour the decision consumes.
`self.can_delete`, `self.can_delete_extra`, `index`, and `initial_form_count`
are scalar inputs (R-abstracted); `initial_form_count()` is evaluated once
*before* the decision (`formsets.py:476`) and only its already-computed value
enters the comparison, so it is an input, not a callee under contract. Hence
there is **no `axiom`, no deep-model reference, and no `axiom_check.py`** (G-AX
skips).

The single behavioural change is the **guard** `index is not None and`
introduced into the comparison: pre-patch, `index < initial_form_count` is
attempted unconditionally and raises `TypeError` when `index is None`; post-patch
the guard short-circuits to `False` for an absent index. This is modeled deeply
in `positionWithinInitial` (the `none ⇒ false` branch) and exercised by the
prepatch (which omits the guard and produces `Except.error`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16569`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`shouldOfferDeletion`/`positionWithinInitial` (R/I-tagged ops) to Python and
compares against `patch.diff`'s behaviour: the patched `add_fields` observed
through whether `DELETION_FIELD_NAME` is added to `form.fields`. There are no
A-tagged callees in the impl region, so the shadow is pure R/I.
