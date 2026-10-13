# mapping.md — django__django-16569

Binding between the model symbols (`tasks/django__django-16569/model.py`) and
the real repository symbols at `base_commit`
`278881e37619278789942513916acafaa88d26f3`.

## 1. Modeled function

| model symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `configure_optional_fields` | `BaseFormSet.add_fields` | `django/forms/formsets.py:475-498` |

`add_fields(self, form, index)` is a hook that conditionally augments a single
form's `fields` mapping with two optional fields: an ordering field
(`ORDERING_FIELD_NAME`) when `self.can_order` is set, and a deletion field
(`DELETION_FIELD_NAME`) when `self.can_delete` is set. Both decisions consult
`index` and `self.initial_form_count()`.

Real source (base_commit), the two decision sites:
```
475  def add_fields(self, form, index):
477      initial_form_count = self.initial_form_count()
478      if self.can_order:
480          if index is not None and index < initial_form_count:
481              form.fields[ORDERING_FIELD_NAME] = IntegerField(... initial=index+1 ...)
487          else:
488              form.fields[ORDERING_FIELD_NAME] = IntegerField(...)        # no initial
493      if self.can_delete and (self.can_delete_extra or index < initial_form_count):
494          form.fields[DELETION_FIELD_NAME] = BooleanField(...)
```

The ordering site (line 480) ALREADY guards `index is not None` before the
comparison. The deletion site (line 493) does NOT — `index < initial_form_count`
is evaluated whenever `self.can_delete and not self.can_delete_extra`, which
raises when `index is None`. The change adds the same `index is not None` guard
the ordering site already has, to the deletion decision.

## 2. Type abstraction (refinement carriers)

| repo reality | model carrier | note |
|---|---|---|
| `self.can_order: bool` | `can_order: bool` param | I (identical bool) |
| `self.can_delete: bool` | `can_delete: bool` param | I |
| `self.can_delete_extra: bool` | `can_delete_extra: bool` param | I |
| `index: int \| None` (callers pass an int per-form, or `None` from `empty_form`) | `index: Optional[int]` param | I — the `None` case is the bug |
| `self.initial_form_count(): int` (count of initial forms, `>= 0`) | `initial_form_count: int` param, `Requires(>= 0)` | R — the unchanged count is a non-negative int read-only input; passed as a value, not recomputed (it is `self.initial_form_count()` captured once at line 477) |
| `form.fields` mapping; whether `ORDERING_FIELD_NAME` key is present | `form.has_order_field: bool` | R — the *presence* of the ordering key (added in both arms of the unchanged ordering `if/else`) |
| `form.fields[ORDERING_FIELD_NAME]` built with `initial=index+1` (guarded arm) vs without `initial` (else arm) | `form.order_field_prefilled: bool` | R — whether the ordering field carries a non-`None` `initial`; True only in the guarded arm (an initial-position form). Models the only observable difference between the two arms of the unchanged ordering `if/else`, keeping the ordering comparison load-bearing in the skeleton |
| `form.fields` mapping; whether `DELETION_FIELD_NAME` key is present | `form.has_delete_field: bool` | R — only the *presence* of the deletion key is observable (the F2P test asserts `"DELETE" in/ not in formset.empty_form.fields`); the `BooleanField(...)` construction is unchanged |
| the call COMPLETES: `add_fields` returns its augmented form (ordinary Python evaluation of a loop-free prologue over scalars) | `Requires(MustTerminate(2))` on `configure_optional_fields` (and measure 1 on the `Form` constructor) | the real hook is loop-free straight-line code, so every call terminates; the obligation pins that an implementation may not DIVERGE instead of answering (without it a non-terminating body — e.g. bare self-recursion — satisfies every `Ensures` vacuously and would verify while its faithful real patch hangs the F2P/P2P suite) |

`form` is modeled as a minimal mutable object carrying only the booleans the
hook's decisions write. `form` is the only mutated object → full permission
(`Acc(form.has_*)` / `Acc(form.order_field_prefilled)`), with the exact
post-state stated. All other inputs are read-only scalars (passed by value; no
`list_pred`/object permission needed).

## 3. Callees

`add_fields`'s body, under the abstraction above, performs only boolean
algebra, an `Optional[int]` None-check, and an integer `<` comparison, then
sets dict keys. No library/utility callee participates in the *changed*
decision logic:

- `self.initial_form_count()` — read once at line 477 into a local; modeled as
  a read-only `int` parameter (its value is not changed by this fix). NOT
  axiomatized: it is consumed only as an opaque non-negative integer.
- `IntegerField(...)` / `BooleanField(...)` / `self.get_ordering_widget()` /
  `self.get_deletion_widget()` — construct the field objects placed under the
  keys. The *presence* of the key is what the decision controls and what the
  test observes; the constructed widget/label are unchanged by the fix and are
  abstracted to "the key is now present" (`has_*_field = True`). NOT
  axiomatized — they do not participate in the changed condition.

**No `@ContractOnly` axioms.** The changed operation is pure control flow over
scalars (a None-guard added to a `<` comparison inside a boolean `or`), modeled
deeply and exactly. There is therefore no axiom inventory and `axiom_check.py`
performs the A-reference / behavioural check described in §4.

## 4. Behavioural soundness check (axiom_check.py, G-AX)

Even with no consumed axioms, `axiom_check.py` validates the deep model against
the real Python semantics it abstracts: it imports the real
`django.forms.formsets.BaseFormSet`, builds formsets across the full cross
product of `can_order × can_delete × can_delete_extra ∈ {T,F}^3` and `index ∈
{None, 0, 1, …, initial_form_count-1, initial_form_count, …}`, calls the real
`add_fields` (post-gold), and asserts that the presence of `DELETION_FIELD_NAME`
in `form.fields` equals the model's decision
`can_delete and (can_delete_extra or (index is not None and index <
initial_form_count))`, likewise that `ORDERING_FIELD_NAME` is present iff
`can_order` and that its `initial` is non-`None`
(`order_field_prefilled`) iff `can_order and at_initial_position(...)`. It also
confirms the
pre-patch raises `TypeError` exactly on the `(can_delete, not can_delete_extra,
index is None)` configuration. stdlib + Django only; exit 0 iff every
observation matches.

## 5. Differential conformance (conformance_check.py, G-CONF)

Shadow = the impl region of `configure_optional_fields` verbatim (it contains
no contract calls) plus the `at_initial_position` pure helper as an internal
cross-check; oracle = the real patched `BaseFormSet.add_fields` in-container
(real formsets via `formset_factory`, initial-form count driven through real
initial data). Bridge per §2 (flag/position identity; form post-state raised
to the three key-presence/prefill booleans). >= 1e5 inputs: full flag cross
product x counts {0,1,2,3,5} x positions spanning the comparison boundary
incl. `None`, plus 100000 fuzz tuples. **Pinned fuzz seed: 16569.**
