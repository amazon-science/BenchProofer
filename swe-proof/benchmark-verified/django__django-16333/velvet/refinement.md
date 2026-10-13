# refinement.md — django__django-16333

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`commitForm` `do` block over `FormState`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized / deep-model
callee — **A-consumed** where the proof uses an axiom's `ensures`, **A-reference**
where a deep model is validated == the real callee by G-AX), or **I** (identical
concrete op).

This fix is a CONTROL-FLOW / side-effect change.  The R/I legs would be refuted
by **G-CONF**, but there is no R/I *data* content (see §C and `conformance_check.py`,
which records `status=skip`); the A-reference legs + this narrative are audited
by **G-AX** + **G-EQ**.  Claim: any impl verifying against this frozen spec,
refined per the map below, persists exactly what the gold patch persists, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The commit step — `UserCreationForm.save` (`django/contrib/auth/forms.py:139`)

Gold hunk (the entire change):
```
         user.set_password(self.cleaned_data["password1"])
         if commit:
             user.save()
+            if hasattr(self, "save_m2m"):
+                self.save_m2m()
         return user
```

The pre-patch body and its `Solution_prepatch.lean` image:
```
def save(self, commit=True):              | st := prepareDeferred st     -- super().save(commit=False)
    user = super().save(commit=False)     | st := applyCredential st     -- user.set_password(...)
    user.set_password(...)                | if commit then
    if commit:                            |   st := persistObject st     -- user.save()
        user.save()                       | else st := st
    return user                           |
```

| # | Solution.lean impl op (`commitForm`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `st : FormState` (mut), `commit : Bool` | `self`/`self.instance`(`user`) state + `commit` kwarg of `save` | R | the form's and its target object's observable state ↔ ten components (nine `Bool` + the `Nat` announcement count); `commit` ↔ `commit` (mapping.md §2). No data carrier — only observable facts: what validated, what was written, what is still outstanding, how many times the credential change was announced, and which of the two persistence writes storage will accept — the last two read-only, since a database enforces integrity rules the form's validation does not see, so a write on validated data can still be declined. |
| A2 | `st := prepareDeferred st`  (`deferredSaveReady := true`) | `user = super().save(commit=False)` | A-reference | builds the object un-persisted and installs the deferred `save_m2m` capability; G-AX validates against `BaseModelForm.save(commit=False)` (mapping.md §3.1). |
| A3 | `st := applyCredential st`  (`passwordApplied := true`, `credentialPending := true`) | `user.set_password(self.cleaned_data["password1"])` | A-reference | writes the credential AND arms the latch `self._password = raw_password` (`django/contrib/auth/base_user.py:106-108`, attribute declared at `:65-66`), announcing nothing — the change it creates is left outstanding for an object write to announce; G-AX validates against `set_password` (mapping.md §3.2). |
| A4 | `if commit then …`  (outer branch) | `if commit:` | I | identical control-flow guard on the same boolean. |
| A5 | `st := persistObject st`  (`objectPersisted := true`, `credentialChanges += credentialPending`, `credentialPending := false`) | `user.save()` | A-reference | persists the object row and then, iff the latch is armed, announces the credential change once and disarms it (`AbstractBaseUser.save`, `django/contrib/auth/base_user.py:74` with the announcement at `:76-78`); G-AX validates against the real `save()` (mapping.md §3.3). |
| A6 | `if st.deferredSaveReady then st := persistRelated st else st := st` | `if hasattr(self, "save_m2m"): self.save_m2m()` | I + A-reference | **the added fix.** The guard `st.deferredSaveReady` ↔ `hasattr(self,"save_m2m")` is **I** over the boolean G-AX proves true after A2; the guarded `persistRelated` (`relatedPersisted := true`) is the **A-reference** for `self.save_m2m()` (mapping.md §3.4). The `else st := st` is the Velvet spelling of the absent `else` (no-op). |
| A7 | `return` (Unit) | `return user` | R | the modeled return carries no observable beyond `st`; `user` is `self.instance`, whose persistence state is `st` (mapping.md §2). |

Discriminating content of the change — on `commit=True`, the related
collection-valued data IS persisted (`relatedPersisted = true`) — lives in step
A6.  `Solution_prepatch.lean` reproduces the pre-patch body (A6 absent) and
**fails** the frozen postcondition `commit = true → st.relatedPersisted = true`
(G-DIFF), exactly the bug the F2P test
`test_custom_form_saves_many_to_many_field` exercises.

## A′. The announcement-multiplicity leg (steps A3 + A5, jointly)

A3 and A5 are not independent: A3 arms the latch and A5 is the only step that
consumes it.  The ORDER of the two, and how many times each runs, is therefore
observable in `credentialChanges`, and the spec pins that observable directly:

```
ensures commit = true  → st.credentialChanges = stOld.credentialChanges + 1
ensures commit = true  → st.credentialPending = false
ensures commit = false → st.credentialChanges = stOld.credentialChanges
ensures commit = false → st.credentialPending = true
```

Justification, clause by clause, against the real patched source:

* `+ 1` on commit — the gold body writes the credential (`forms.py:141`) and then
  performs exactly one object write (`forms.py:143`), which finds the latch armed
  and announces once (`base_user.py:76-78`).  The repo's own
  `tests/auth_tests/test_forms.py:113-127` asserts this multiplicity: it saves the
  same form twice and requires the announcement to have been made once per save,
  which is only true if each save announces exactly one change.
* `credentialPending = false` on commit — `base_user.py:78` sets
  `self._password = None` after announcing.
* the two `commit = false` clauses — the non-committing path never reaches an
  object write, so nothing is announced and the change written by A3 stays
  outstanding; the immediately following clause of the same form is what makes
  "announced nothing" a *stated* post-state rather than an unconstrained one.

Together these four clauses close the ordering freedom that the persistence-only
postconditions left: an impl that writes the credential AFTER the object write
announces zero times, one that follows a second credential write with a second
object write announces twice, and one that re-writes the object between two
credential writes lands the count somewhere else again.  All three verify against
the persistence-only postconditions and are refuted here.  This is exactly the
recorded break (`atk_12`): a rival that re-armed the latch between two object
writes, satisfying every persistence clause while announcing the credential change
twice, which the F2P/P2P suite refuses.

## B. mut-frame discipline (directive 5)

`st` is the only `mut` parameter.  The non-commit path performs neither
persistence; the spec pins this explicitly with
`ensures commit = false → st.objectPersisted = stOld.objectPersisted` and the
same for `relatedPersisted` (post-state stated exactly, not left unconstrained),
and pins the announcement observable the same way with
`ensures commit = false → st.credentialChanges = stOld.credentialChanges` (a
relative frame, since the count is an absolute trajectory count — see mapping.md
§2).  An impl that silently persisted on `commit=False`, that announced on
`commit=False`, or that failed to persist either on `commit=True`, cannot
verify.

## C. No kind-3 (inexpressible-changed-op) steps; no consumed axioms

Every step is R, A-reference, or I.  The operation that genuinely *changed* —
adding the guarded `save_m2m()` call (A6) — is modeled with its control-flow
guard as **I** (over a boolean G-AX establishes) and the persistence effect as
an **A-reference** callee, NOT hidden behind a consumed axiom about the function
under change.  There are **no consumed axioms**: the four callees are all
unchanged and deep-modeled as A-reference state transformers (G-AX).

There is no R/I *data* content to differentially fuzz: the only **I** ops (A4,
A6 guard) are boolean control flow, and the only **R** ops (A1, A7) are the
state abstraction itself, not a transliterable computation.  Hence
`conformance_check.py` records `status="skip", reason="no-RI-content"` (plan
§4.1); the cross-language weight rests on G-AX (§A callees) + G-EQ + G-PANEL.

## D. verify(Solution) ⇒ resolved

`commitForm` verifies only if, on `commit=True`, BOTH `objectPersisted` and
`relatedPersisted` become true (A5, A6) while the credential is applied (A3) and
the deferred capability prepared (A2); on `commit=True` the credential change is
announced EXACTLY ONCE with none left outstanding (§A′, so the credential write
precedes the single object write that consumes it); and on `commit=False` neither
persistence fires and nothing is announced (§B).  By R (the FormState abstraction
of mapping.md §2) and the A-reference legs (G-AX: each callee effects exactly its
modeled state change on all ten components after every step, over four model configurations that between them exercise both accepted and declined writes), the verified
skeleton persists exactly what the gold patch persists — both the object and its
related m2m data on commit — and notifies the surrounding system exactly as often
as the gold patch does.  The gold patch resolves (G-RESOLVE).
Trust points are plan §1.1's: callee soundness (G-AX) and refinement fidelity
(this doc, audited by G-EQ; no mechanical G-CONF leg exists because there is no
R/I data content).
