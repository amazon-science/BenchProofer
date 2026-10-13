# mapping.md — symbol binding & type bijection (django__django-16333)

## Modeled function
- **Lean** `implementation_persistForm : FormData → Bool → SaveOutcome`
- **Python** `UserCreationForm.save(self, commit=True)` —
  `django/contrib/auth/forms.py:139-145 @ 60a7bd89860e504c0c33b02c78edcac87f6d1b5a`
  (post-patch body):
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

The function under spec persists a model form's built instance and, post-patch,
also persists the instance's pending multi-valued related-field selections when
the save is committed. Pre-patch the related selections were silently dropped on
a committed save.

### Control-flow facts used by the model
- `super().save(commit=False)` (`django/forms/models.py:457-480 @ base_commit`)
  builds `self.instance` from the cleaned data and, **because `commit=False`**,
  installs the deferred relation writer as `self.save_m2m = self._save_m2m`. So
  after this call the form ALWAYS carries `save_m2m` ⇒ `hasattr(self,
  "save_m2m")` is True on this code path. The added `hasattr` guard is defensive
  (a subclass could delete it); on the real `UserCreationForm.save` path it is
  always satisfied. Modeled by `hasRelatedWriter`, set true by the
  `super().save(commit=False)` step.
- `user.set_password(self.cleaned_data["password1"])` always runs (unchanged by
  the patch) ⇒ the returned instance always has its password applied. Modeled by
  `UserObj.passwordSet = true`.
- `if commit: user.save()` persists the instance row (unchanged by the patch).
  Modeled by `instanceSaved = commit`.
- `self.save_m2m()` writes exactly the form's cleaned multi-valued selections to
  the relation; absent commit it is deferred (not run here). Modeled by
  `relatedSaved = if commit then f.m2m else []`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| the form's cleaned multi-valued (ManyToMany) selections | `f.m2m : List Int` | the set of related-object identities chosen in the form; order/identity only |
| `self.cleaned_data["password1"]` (raw password) | `f.password : String` | the raw password string the instance's password is derived from |
| `commit` argument | `commit : Bool` | True ⇒ persist immediately; False ⇒ defer |
| returned `user` instance | `SaveOutcome.user : UserObj` | only the touched fact `passwordSet` is carried |
| `user.set_password(...)` applied | `UserObj.passwordSet = true` | password handling unchanged by the patch |
| `user.save()` having persisted the row | `SaveOutcome.instanceSaved : Bool` | instance row persistence |
| relations persisted by `save_m2m()` | `SaveOutcome.relatedSaved : List Int` | the multi-valued selections now in the relation |

## Callee provenance
- `super().save(commit=False)` (`forms/models.py:457`), `user.save()`
  (`db/models/base.py` Model.save), and `self.save_m2m`/`self._save_m2m`
  (`forms/models.py:447` — `save_instance`'s deferred m2m writer) are all
  UNCHANGED real ORM operations the patch merely re-routes. They are
  **A-reference** deep models (the produce-instance / persist-row /
  persist-relations behavior is carried into the model as the `SaveOutcome`
  transformation), validated against the real ORM. Exercising them requires a
  live ORM + database + a model with an m2m field; there is no consumed
  callee-`opaque`/`axiom` property — the axioms region is empty.

## Flag dependency
The relation-write step is conditioned on `commit` (only on a committed save) and
on the relation writer being installed (always, via `super().save(commit=False)`).
No other configuration flag affects the modeled behavior.

## G-CONF fuzz seed
Pinned seed: **16333**. (G-CONF is a skip: `conf_skip=true` — see meta.json /
conformance_check.py; the impl is all A-reference ORM-persistence ops with no
standalone stdlib-shadowable R/I data transformation.)
