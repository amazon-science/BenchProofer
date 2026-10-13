# refinement.md — operation correspondence (django__django-16333)

Maps every op in `implementation_persistForm` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

Post-patch Python (`UserCreationForm.save`):
```python
def save(self, commit=True):
    user = super().save(commit=False)
    user.set_password(self.cleaned_data["password1"])
    if commit:
        user.save()
        if hasattr(self, "save_m2m"):
            self.save_m2m()
    return user
```
The gold patch adds the two lines `if hasattr(self, "save_m2m"): self.save_m2m()`
inside the `if commit:` block. The rest of `save` is unchanged.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut user := buildInstance f` | `user = super().save(commit=False)` | A-reference | builds the instance from cleaned data AND (because `commit=False`) installs the deferred related writer `self.save_m2m`. Real `BaseModelForm.save` (`forms/models.py:457`); modeled deeply as producing an unsaved `UserObj` and (next line) asserting the writer is present. Unchanged by the patch. |
| 2 | `let hasRelatedWriter := true` | the fact that `super().save(commit=False)` set `self.save_m2m`, making `hasattr(self, "save_m2m")` true | A-reference | the `hasattr` guard's value on this code path. `super().save(commit=False)` always installs `save_m2m`, so the guard is always satisfied here (it is defensive against a subclass deleting it). Models the truth value the patch's new `hasattr` test reads. |
| 3 | `user := { user with passwordSet := true }` | `user.set_password(self.cleaned_data["password1"])` | A-reference | derives & applies the stored password; unchanged by the patch. Modeled deeply as setting the only touched fact `passwordSet`. |
| 4 | `if commit then instanceSaved := true` | `if commit: user.save()` | A-reference | persists the instance row iff committing; unchanged by the patch. Modeled deeply as `instanceSaved = commit`. |
| 5 | `if hasRelatedWriter then relatedSaved := f.m2m` (inside the `commit` branch) | `if hasattr(self, "save_m2m"): self.save_m2m()` (the ADDED lines) | A-reference | **the changed op.** `self.save_m2m()` writes exactly the form's collected multi-valued related selections to the relation. Modeled deeply as `relatedSaved := f.m2m`. Validated == the real deferred m2m writer by G-AX (skip — needs live ORM). NOT axiomatized. |
| 6 | `return { user, instanceSaved, relatedSaved }` | `return user` (+ the persisted side effects) | I | returns the built instance; the model additionally carries the observable persistence facts the test inspects. |

No A-consumed rows: the proof discharges the `SaveOutcome` transformation
structurally; no UNCHANGED-callee `axiom` property is consumed (axioms region
empty). No changed-inexpressible op.

The discriminating clause is row 5: on a committed save of a form carrying a
non-empty multi-valued selection, the spec demands
`relatedSaved = f.m2m`. The prepatch impl never writes the selections
(`relatedSaved = []` even when `commit = true`), so its carried `correct_persistForm`
cannot close against the frozen `problem_spec_persistForm`. That is the G-DIFF
signal, and it is exactly what the F2P test
`test_custom_form_saves_many_to_many_field` exercises.
