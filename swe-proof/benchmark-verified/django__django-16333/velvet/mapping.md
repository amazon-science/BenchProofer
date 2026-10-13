# mapping.md — django__django-16333

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 60a7bd89860e504c0c33b02c78edcac87f6d1b5a`, states the type
abstraction (the bijection G-AX uses to bridge Lean↔Python), and gives the
provenance of each deep-model reference.

Repo file under change: `django/contrib/auth/forms.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `commitForm (mut st) (commit)` | `UserCreationForm.save(self, commit=True)` — `django/contrib/auth/forms.py:139` (body 140-144) | the modeled changed function (creation-form commit step) |
| `FormState` | the observable persistence state of the form's target object (`self`, `self.instance`/`user`) | type abstraction (see §2) |
| `prepareDeferred` *(A-reference)* | `super().save(commit=False)` = `BaseModelForm.save` non-commit branch — `django/forms/models.py:526` (branch at 544-547) | builds the in-memory object without persisting it and installs the deferred `save_m2m` capability |
| `applyCredential` *(A-reference)* | `user.set_password(self.cleaned_data["password1"])` — `AbstractBaseUser.set_password`, `django/contrib/auth/base_user.py:106` | writes the secret credential onto the in-memory object |
| `persistObject` *(A-reference)* | `user.save()` — `AbstractBaseUser.save`, `django/contrib/auth/base_user.py:74` (announcement at 76-78), over model `save` | writes the object itself to storage AND announces an outstanding credential change, exactly one and only if one is outstanding, clearing it |
| `persistRelated` *(A-reference)* | `self.save_m2m()` (= `BaseModelForm._save_m2m`) — `django/forms/models.py:505`, exposed as `self.save_m2m` at 547 | writes the related collection-valued form data to storage |

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): `UserCreationForm.save` commit branch called only
`user.save()` and **omitted** `self.save_m2m()`, so related (`ManyToManyField`)
form data was silently dropped on commit (the public issue).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The modeled function is a CONTROL-FLOW / side-effect change; there is no
type-refined *data carrier* (no `str`/`list`/`dict`).  We abstract the observable
state of the form and of its target object as ten components — nine `Bool` and
one `Nat` counter:

| repo reality (observable on the form / its target object) | Lean carrier | bijection |
|---|---|---|
| "the bound data passed the form's own validation" — `form.is_valid()` / `not form.errors` (`django/forms/models.py:532` raises otherwise) | `FormState.dataValidated : Bool` | True ↔ the save is allowed to proceed |
| "the secret credential has been written onto the in-memory object" — `user.check_password(password1)` is True | `FormState.passwordApplied : Bool` | True ↔ credential verifies |
| "the object row has been persisted" — `user.pk is not None` after the modeled call | `FormState.objectPersisted : Bool` | True ↔ object stored |
| "the related collection-valued data has been persisted" — `set(user.<m2m>.all())` equals the cleaned selection | `FormState.relatedPersisted : Bool` | True ↔ related data stored |
| "the deferred related-data save capability is prepared" — `hasattr(self, "save_m2m")` | `FormState.deferredSaveReady : Bool` | True ↔ `save_m2m` attribute present |
| "a written credential's change is still OUTSTANDING — written but not yet announced" — `user._password is not None` (the latch declared at `django/contrib/auth/base_user.py:65-66`) | `FormState.credentialPending : Bool` | True ↔ the latch is armed |
| "how many times the credential change has been ANNOUNCED to the surrounding system" — the number of `password_validation.password_changed(...)` calls made on this trajectory (`django/contrib/auth/base_user.py:76-78`) | `FormState.credentialChanges : Nat` | n ↔ n announcements so far |
| "storage ACCEPTS the object write this step would make" — `user.save()` on this object completes instead of raising a database-integrity error | `FormState.objectWriteAccepted : Bool` | True ↔ storage takes the object row |
| "storage ACCEPTS the related collection-valued write this step would make" — `save_m2m()` completes instead of raising a database-integrity error | `FormState.relatedWriteAccepted : Bool` | True ↔ storage takes the related rows |
| "the step asked storage for an operation it declines, so it ended in an error having written nothing further" — the modeled call raised | `FormState.stepRefused : Bool` | True ↔ the step ended in a declined operation |

The `commit` parameter ↔ the `commit` keyword argument of `save` (Python
`bool`).  Booleans are exact across the bridge and the counter is exact as a call
count.  The announcement count is an ABSOLUTE trajectory count, not a per-call
one, which is why the postconditions constrain it RELATIVE to the entry state
(`st.credentialChanges = stOld.credentialChanges + 1` on commit): the caller's
earlier calls have already contributed, exactly as
`tests/auth_tests/test_forms.py:113-127` counts across two consecutive `save`
calls.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

All four state transformers are **A-reference**: each is a deep model of an
UNCHANGED repository callee the modeled `save` calls but does not modify.
`axiom_check.py` stands the repo's own `UserCreationForm` + the F2P test's
`auth_tests.models.with_many_to_many.CustomUserWithM2M` model up in a real
in-memory Django project and asserts each callee effects exactly the
state-component change its deep model claims.

### 3.1 `prepareDeferred` ↔ `super().save(commit=False)` (A-reference)
The generic `BaseModelForm.save(commit=False)` (`django/forms/models.py:526`,
branch 544-547) builds `self.instance` WITHOUT writing it (`pk is None`) and
sets `self.save_m2m = self._save_m2m`.  Model effect: `deferredSaveReady := True`
(objectPersisted / relatedPersisted / credentialPending / credentialChanges
untouched).  This is exactly the `hasattr(self, "save_m2m")` predicate the
patched inner `if` tests — G-AX asserts the attribute is present after the
non-commit save.

### 3.2 `applyCredential` ↔ `user.set_password(...)` (A-reference)
`AbstractBaseUser.set_password` (`django/contrib/auth/base_user.py:106-108`)
writes `self.password = make_password(raw)` **and arms the latch**
`self._password = raw_password` (line 108; the attribute is declared at
`base_user.py:65-66`).  It announces nothing: the credential change it creates is
left OUTSTANDING for a later object write to announce.  Model effect:
`passwordApplied := True`, `credentialPending := True`, `credentialChanges`
untouched.  G-AX asserts `user.check_password("testclient")` holds afterwards,
that `user._password is not None`, that the announcement callee has not been
called, and that the call persists nothing.

### 3.3 `persistObject` ↔ `user.save()` (A-reference)
`AbstractBaseUser.save` (`django/contrib/auth/base_user.py:74`) calls
`super().save(*args, **kwargs)` to write the object row, then — at lines 76-78 —
announces the credential change **iff the latch is armed**, and disarms it:

```python
if self._password is not None:
    password_validation.password_changed(self._password, self)
    self._password = None
```

So one object write announces exactly the one outstanding change and clears it;
a second object write with nothing outstanding announces nothing.

The write is a DATABASE write, so storage may DECLINE it: the model row's own
integrity constraints are enforced by the database and are not all visible to the
form's validation, so `user.save()` on data the form accepted can still raise
(`django.db.utils.IntegrityError`).  A declined write stores nothing and announces
nothing, and the latch stays armed, because the announcement at :76-78 is
sequenced AFTER `super().save(...)` returns.  Model effect: when
`objectWriteAccepted`, `objectPersisted := True`,
`credentialChanges += credentialPending`, `credentialPending := False`; otherwise
`stepRefused := True` and every other component untouched.  G-AX asserts
`user.pk is not None` afterwards, that the announcement count moved by exactly
the modeled amount, that the latch is disarmed, that `user.save()` does NOT
itself persist the m2m data (relatedPersisted stays False until save_m2m), and —
on a model carrying a required column the form does not supply — that a declined
write leaves all of `objectPersisted` / `credentialChanges` / `credentialPending`
exactly as the model says.

### 3.4 `persistRelated` ↔ `self.save_m2m()` (A-reference)
`BaseModelForm._save_m2m` (`django/forms/models.py:505`), exposed as
`self.save_m2m`, persists the cleaned related-field data.  It touches neither the
credential nor the latch, so it announces nothing and clears nothing.

Its write is likewise a DATABASE write and can be DECLINED, and it has THREE
refusal conditions, not two.  It walks `chain(opts.many_to_many,
opts.private_fields)` and consults three tables per field — `self._meta.fields`,
`self._meta.exclude` and `cleaned_data` — writing only the fields all three admit
(`models.py:505-521`); a field the form does not expose is skipped and cannot be
declined.  For each field it writes, `ManyToManyField.save_form_data` →
`ManyRelatedManager.set` → `_add_items` bulk-creates the through rows
(`related_descriptors.py:1386-1445`).  So it declines when (a) the deferred
capability was never prepared — there is no `save_m2m` attribute to call
(`AttributeError`); (b) the object is not yet stored — `_add_items` needs the
source primary key (`ValueError`, measured); or (c) storage refuses the through-row
insert, which happens whenever the through model carries a required column the
form does not supply: `Field._get_default` returns `return_None` for a field with
no default and `empty_strings_allowed=False`
(`django/db/models/fields/__init__.py:934-947`), so the insert hits the column's
NOT NULL constraint and raises `IntegrityError`.  Model effect: when
`deferredSaveReady && objectPersisted && relatedWriteAccepted`,
`relatedPersisted := True` (credentialPending / credentialChanges untouched);
otherwise `stepRefused := True`.  G-AX asserts `set(user.<m2m>.all())` equals the
selected organizations after an accepted call, that the announcement count did not
move, and — on a through model with a required extra column — that a declined call
leaves `relatedPersisted` False and announces nothing.

**Soundness check (G-AX):** `axiom_check.py` carries a Python mirror of all four
transformers alongside the real objects and, after EVERY real call, asserts that
all EIGHT modeled components agree with what the real form / object /
announcement stream shows (`credentialPending` read as
`user._password is not None`, `credentialChanges` as the call count of
`django.contrib.auth.password_validation.password_changed`).  It runs 12 boundary
trajectories — the three related-row configurations (single / pair / all orgs)
under the gold step sequence, the two announcement-multiplicity sequences (two
credentials + two object writes must announce TWICE; one credential + two object
writes must announce ONCE), and a non-committing sequence that must announce
nothing while leaving the change outstanding — each entered both with and without
an already-outstanding credential change, plus 500 randomized fuzz trajectories
(seed `16333`) over the related-row selection, the step sequence and the entry
latch.  Django + stdlib only (the repo under test).  Exit 0 iff sound.

## 4. G-CONF — skip (no R/I content)

`conformance_check.py` records `status="skip", reason="no-RI-content"`.  The fix
is a control-flow/side-effect change: the impl region's value-carrying ops are
all A-reference callees (left as the real callee by G-CONF, §4.1 step 1), and
the residual content is the pure boolean control-flow skeleton, which has no
cross-language data to differentially fuzz.  The cross-language weight falls on
G-AX (§3) and the agentic gates.  No fuzz seed is needed (no fuzzing); the G-AX
seed is `16333`.
