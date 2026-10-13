# mapping.md — django__django-16569

## Instance
- repo: django/django
- base_commit: 278881e37619278789942513916acafaa88d26f3
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`BaseFormSet.add_fields` (django/forms/formsets.py:472) is a hook that decides,
per form instance, which extra fields to attach. The relevant decision is whether
to attach the deletion field: it is attached when the formset allows deletion AND
either extra (template) forms may also be deleted, OR the form sits within the
"initial" forms (its positional index is below the initial-form count).

The positional `index` argument is `None` for a form that has no position in the
formset — e.g. the formset's template/empty form. At `base_commit` the deletion
guard compares `index` to `initial_form_count` WITHOUT first checking that
`index` is present:

```python
-        if self.can_delete and (self.can_delete_extra or index < initial_form_count):
+        if self.can_delete and (
+            self.can_delete_extra or (index is not None and index < initial_form_count)
+        ):
```

When deletion is allowed, extra-form deletion is disallowed, and `index is None`
(the template/empty-form case), evaluating `index < initial_form_count` raises
`TypeError: '<' not supported between instances of 'NoneType' and 'int'`. The fix
treats a positionless form as "not within the initial set" (so its deletion field
is omitted) instead of crashing.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_addFields` | `BaseFormSet.add_fields` (django/forms/formsets.py:472) — specifically the deletion-field decision at :493-499 |
| `problem_spec_addFields`   | the post-condition this decision must satisfy |
| `withinInitial` (helper)   | the sub-expression `index is not None and index < initial_form_count` |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `canDelete : Bool` | `self.can_delete` (bool) | whether the formset allows deletion |
| `canDeleteExtra : Bool` | `self.can_delete_extra` (bool) | whether extra/template forms may also be deleted |
| `index : Option Nat` | `index` argument (int or None) | `none ↔ None` (positionless form, e.g. the template/empty form); `some i ↔ i` (a non-negative positional index) |
| `ifc : Nat` | `initial_form_count = self.initial_form_count()` (int ≥ 0) | count of initial forms |
| result `: Option Bool` | observable outcome | `none ↔` `add_fields` raised `TypeError`; `some b ↔` `add_fields` completed and `b = (DELETION_FIELD_NAME in form.fields)` |

`Option Nat ↔ (int | None)`: Python formset indices are non-negative ints produced
by `enumerate`/`range`, or `None`. `Nat` is the faithful carrier.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The deletion-field decision is
  a pure boolean computation over `(can_delete, can_delete_extra, index,
  initial_form_count)`; the field-construction side effect
  (`BooleanField(...)` assigned into `form.fields[DELETION_FIELD_NAME]`) is
  abstracted to the boolean "was the deletion field attached". `axiom_check.py` is
  a skip stub.
- The unchanged `can_order` block (django/forms/formsets.py:478-490) already guards
  its own index comparison with `index is not None` at `base_commit`, so it is NOT
  part of the modeled change and is not modeled.
- Flag dependency: the deletion decision short-circuits — the index comparison is
  reached only when `can_delete` is true and `can_delete_extra` is false. G-CONF
  fuzzes all of `(can_delete, can_delete_extra, index∈{None}∪[0..n], initial_form_count)`.

## G-CONF fuzz seed
- pinned seed: `16569`
- ≥10^5 fuzzed `(can_delete, can_delete_extra, index, initial_form_count)` tuples,
  index drawn from `None` plus `0..12`, counts `0..12`, exercising the
  positionless (`None`) boundary that triggered the crash.
