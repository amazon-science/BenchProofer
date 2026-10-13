# mapping.md — django__django-16333

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 60a7bd89860e504c0c33b02c78edcac87f6d1b5a`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/contrib/auth/forms.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `save_form(self, commit)` | `UserCreationForm.save(self, commit=True)` — `django/contrib/auth/forms.py:139` (body lines 140-144) | the modeled changed function (the user-creation save) |
| `Form` (class) | the bound `UserCreationForm` instance `self` together with its `instance` (the model object built by the base form) | minimal object carrying only the three observed persistence facts |
| `Form.form_pred()` *(@Predicate)* | (no repo symbol — verification scaffolding) | abstraction predicate holding the two observable persistence booleans (record/ready). The relational-data fact is NOT held here: it is the abstract per-form capability `relations_done(self)`, so it cannot be fabricated by unfolding this predicate and assigning a field (SPEC_GUIDE directive 8 / control-flow grounding, hardened against both the Unfold/assign/Fold fiat and the cross-instance token transfer) |
| `Form.get_record()` / `get_ready()` *(@Pure accessors)* | the observable facts `instance` row exists / `hasattr(self,"save_m2m")` | read the underlying booleans through `form_pred`; used in pre/post-conditions |
| `relations_done(self)` *(axiom — A-reference, @ContractOnly @Predicate)* | the observable fact "the m2m through-rows are written for `self`'s instance" (`instance.<m2m>.exists()` for the tested non-empty input) | abstract per-form capability with NO body: holding it means the deferred relational save has run for THIS form. It cannot be folded by fiat (a body-less predicate has nothing to fold) and a capability for another form (`relations_done(scratch)`) does not discharge it; only `run_deferred_save(self)`'s `Ensures` grants it. Validated by axiom_check's relations-unwritten-until-save_m2m observations (§3.4) |
| `record_available(self)` *(axiom — A-reference, @ContractOnly @Predicate)* | the observable fact "this form's model record object exists" — `self.instance`, built from the submitted data while validating and handed back by `user = super().save(commit=False)` | abstract per-form capability with NO body: holding it means the record object the two persistence steps operate on exists. Unforgeable and non-transferable on the same grounds as `relations_done`. The form HOLDS it on entry (it built `self.instance` while validating), so `save_form` Requires it and every callee both Requires and Ensures it: it names the one object every step acts on and constrains no order (§2.2) |
| `base_form_save_deferred(self)` *(axiom — A-consumed)* | `super().save(commit=False)` → `BaseModelForm.save(commit=False)` — `django/forms/models.py:526` (the `commit=False` else-branch, lines 544-547) | unchanged base-form save in deferred mode; it returns the record object the form already holds (`return self.instance`) rather than creating it |
| `persist_record(self)` *(axiom — A-consumed)* | `user.save()` → `Model.save()` — invoked at `django/contrib/auth/forms.py:143` | unchanged write of the primary record |
| `run_deferred_save(self)` *(axiom — A-consumed)* | `self.save_m2m()` (the handle `self.save_m2m = self._save_m2m`, `BaseModelForm._save_m2m` — `django/forms/models.py:505`) invoked by the patch at `django/contrib/auth/forms.py` (the added lines) | unchanged deferred relational save |

The control-flow element the change introduces (the refinement audit, not a
consumer-spec symbol): the guard `if hasattr(self, "save_m2m")` and the call
`self.save_m2m()` inside the `commit` branch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `commit` (bool kwarg of `save`) | `commit: bool` (explicit positional) | identity |
| "the primary record has been written to the database" (the row for `self.instance` exists) | `self.record_persisted: bool`, read via `get_record()` | True ⇔ `Model.objects.filter(pk=instance.pk).exists()` |
| "the deferred relational save has been run for this form" (the deferred many-to-many persistence step `save_m2m()` has executed) | the abstract per-form capability predicate `relations_done(self)` | holding `relations_done(self)` ⇔ `self.save_m2m()` has been invoked (which, for the tested non-empty-m2m input, writes the m2m through-rows so `instance.<m2m>.exists()`). It is a body-less per-form capability, not a value, so it is neither fiat-foldable nor transferable across forms — see the grounding note below. |
| "a deferred relational save was set up for this form" (the attribute `save_m2m` exists, i.e. `hasattr(self, "save_m2m")`) | `self.deferred_save_ready: bool`, read via `get_ready()` | True ⇔ `hasattr(self, "save_m2m")` |
| `user = super().save(commit=False)` returning the instance; the routine then returns `user` | `save_form` returns `self` (the same `Form`); the instance state is carried on the `Form` object | `Result() is self`; the returned model instance's persistence state is exactly the tracked facts |
| `user.set_password(self.cleaned_data["password1"])` | (no tracked node) | the password assignment changes credential state, not record/relational persistence — irrelevant to the tested behaviour; omitted (it never reads or writes any of the three observed facts) |

The two observable facts are held behind the abstraction predicate
`Form.form_pred()` and read only through the pure accessors. The `record` and
`ready` facts are plain booleans (`record_persisted`, `deferred_save_ready`).
The **relational-data fact** is grounded more strongly (directive 8 /
control-flow effect token): it is NOT a readable/writable value but the abstract
per-form CAPABILITY `relations_done(self)` — a `@ContractOnly` predicate with NO
body. Consequently:

- A wrong implementation cannot fabricate it by writing a field — there is no
  relational field at all; the capability lives only in the proof state (this
  closes the original DEFECT-1 direct-fiat path).
- Nor can it fabricate it by `Fold(relations_done(self))` — an abstract
  (body-less) predicate has nothing to fold, so the fold is rejected at
  translation (`abstract.predicate.fold`). This closes the recover re-audit's
  DEFECT-3 `Unfold/assign/Fold` bypass (no field to assign, no foldable body).
- Nor can it launder a capability earned for another form: running the real
  `run_deferred_save(scratch)` on a throwaway `Form()` grants
  `relations_done(scratch)`, a DIFFERENT predicate instance that does not
  discharge `relations_done(self)` (this closes the recover re-audit's decisive
  DEFECT-4 token-transfer / echo-the-oracle counterexample — the prior
  `rel_written(token: int)` grounding was an identity-blind global over a
  copyable integer; binding the fact to the form object instead of a value
  removes the transferable handle).
- `relations_done(self)` is granted ONLY by `run_deferred_save(self)`'s `Ensures`
  (⇔ `save_m2m`).

This is a directive-8 / control-flow grounding, not an answer-key oracle:
`relations_done` is an unforgeable capability predicate over the actual form
object, not a `@Pure`-in-Ensures lookup pinned to `Result()` and not a copyable
value, so there is no echo-the-oracle cheat. The relational-data fact tracks
*the deferred relational save executed for this form*, not *the m2m set is
non-empty* — these coincide on the tested (non-empty-m2m) F2P input and diverge
only on an empty-m2m form, which the F2P test does not use.

`run_deferred_save` (⇔ `save_m2m`) additionally requires `get_record() is True`
(the primary record already written). This mirrors the real callee: `save_m2m`
attaches the associations to `self.instance` via its primary key, so it MUST run
after `user.save()` — calling it before the record write raises
`ValueError: … needs to have a value for field "id" before this many-to-many
relationship can be used` (verified by axiom_check.py's pre-pk negative
observation, §3.3). This ordering precondition is what makes a deferred-save-
before-record-write implementation fail verification.

`commit=True` is the default and the only value the F2P test uses
(`form.save(commit=True)`); the `commit=False` postcondition clauses document
the unchanged deferred path (still set up, nothing written) for completeness and
to pin the base-form contract.

### 2.2 The record object — one named object, no ordering claim

Both persistence steps operate on ONE object: the form's model record,
`self.instance`. `user.save()` writes that object's row and `save_m2m()` attaches
the associations to it, and `user = super().save(commit=False)` is what binds the
name — but not what brings the object into existence. The form built
`self.instance` from the submitted data while validating (`BaseModelForm._post_clean`
→ `construct_instance`), before this routine is entered, and the base-form save's
`commit=False` branch just returns it. So there is no moment inside the routine at
which the object is missing, and no step has to wait for another to produce it.

The model expresses that as a second body-less per-form capability,
`record_available(self)`, grounded exactly like `relations_done` — unforgeable (a
`@Pure` boolean could be flipped by unfolding `form_pred` and assigning) and
non-transferable (a capability for another form does not discharge it). What it
claims is IDENTITY, not order: `save_form` `Requires` it at entry, every callee
`Requires` and `Ensures` it, and the routine `Ensures` it, so every step and the
returned value are about that same one object and any order of the steps is
permitted by this clause alone.

Attributing PRODUCTION of the object to `base_form_save_deferred` would over-fit:
it would forbid writing the primary record before invoking the base-form save,
which the repo permits. Measured — the faithful refinement of that order passes the
F2P test and 796 tests across `auth_tests` + `model_forms`, and agrees with the
gold patch on every observable over the whole finite modeled domain — so that shape
is a positive control the spec MUST admit (properties.py
`pos-control-record-write-before-base-save`, expect="verify").

The order the model does constrain is the one the repo constrains, and it lives
elsewhere: `run_deferred_save`'s `Requires(get_record() is True)` (§3.3), i.e. the
deferred relational save may run only after the primary record write has really
happened, because the associations attach to the record's primary key. Since the
record fact is read-only to the routine, that condition can be met only by
performing the write, never by claiming it.

### 2.1 Termination obligation — closing the function-under-spec self-echo (DEFECT-5)

`save_form`'s precondition carries `Requires(MustTerminate(2))` and each of the
three `@ContractOnly` callees carries `Requires(MustTerminate(1))`. This is the
directive-grounding device against the **function-under-spec self-echo** (the
recover re-audit pass-3 counterexample `return save_form(self, commit)`): Nagini
verifies only *partial* correctness for impure methods (no termination is
required by default), so a non-terminating body — here unbounded self-recursion —
vacuously satisfies every postcondition, letting an implementation re-derive
`relations_done(self)` from this very routine's own contract without doing any
work. The faithful refinement of that impl is `def save(self, commit=True):
return self.save(commit)`, which `RecursionError`s before persisting anything and
fails the F2P test. The termination obligation pins that the routine actually
terminates: `MustTerminate(2)` on `save_form` permits calling the three callees
(each `MustTerminate(1)` — a strictly smaller measure) but FORBIDS a self-call
`save_form(self, commit)`, which would have to take the same `MustTerminate(2)`
obligation without a strictly smaller measure (the obligation-leak check rejects
it). `Decreases` (the @Pure-only measure clause) is not usable here because
`save_form` is impure — Nagini 1.2.0 raises `invalid.contract.position` for
`Decreases` on an impure method — so the obligation system (`MustTerminate`) is
the equivalent mechanism. The callee `MustTerminate(1)` is sound and weakest-
sufficient: the real Django callees (`BaseModelForm.save(commit=False)`,
`Model.save()`, `save_m2m`/`_save_m2m`) all terminate on Requires-satisfying
inputs (axiom_check.py runs each to completion over 50 observations — direct
evidence of termination), and `MustTerminate` is a precondition obligation, not a
value/exception claim, so it does not alter the axioms' observable behaviour or
the executable G-AX check.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

All three axioms describe callees the routine INVOKES but does NOT change. None
is the function under specification. Each is the WEAKEST contract the proof
needs.

### 3.1 `base_form_save_deferred` ↔ `BaseModelForm.save(commit=False)` (A-consumed)
**Callee:** `django.forms.models.BaseModelForm.save` (`django/forms/models.py:526`).
The routine's first line is `user = super().save(commit=False)`. With
`commit=False` the base save takes the else-branch (lines 544-547):

```python
else:
    # If not committing, add a method to the form to allow deferred
    # saving of m2m data.
    self.save_m2m = self._save_m2m
return self.instance
```

So it (a) installs the deferred relational save handle (`self.save_m2m`), and
(b) writes NOTHING — neither `self.instance.save()` nor `self._save_m2m()` runs
on this branch. Axiom encodes exactly that: `deferred_save_ready` becomes True;
`record_persisted` is unchanged and the relational-data capability
`relations_done(self)` is NOT granted. **Flag dependency:**
this contract holds only for the `commit=False` call the routine makes (the
`commit=True` branch of the base save would itself persist) — recorded so G-AX
fuzzes the right configuration.

### 3.2 `persist_record` ↔ `Model.save()` (A-consumed)
**Callee:** `django.db.models.Model.save` (invoked as `user.save()`,
`django/contrib/auth/forms.py:143`). It writes the primary record's row. It does
NOT write the many-to-many through-rows (those are written separately, by the
deferred relational save) and does not touch the deferred-save handle. Axiom:
`record_persisted` becomes True; the relational-data capability
`relations_done(self)` is NOT granted and `deferred_save_ready` is unchanged.
This non-writing-of-m2m is the load-bearing fact that makes the deferred
relational save necessary.

### 3.3 `run_deferred_save` ↔ `save_m2m` (== `BaseModelForm._save_m2m`) (A-consumed)
**Callee:** `django.forms.models.BaseModelForm._save_m2m` (`django/forms/models.py:505`),
exposed on the form as `self.save_m2m` by 3.1. It iterates the model's
many-to-many (and private) fields and calls `f.save_form_data(self.instance,
cleaned_data[f.name])`, writing the submitted associations. Axiom: it grants the
per-form relational-data capability `relations_done(self)` (it is the SOLE
producer); `record_persisted` and `deferred_save_ready` unchanged. Its
`Requires(deferred_save_ready is True)` mirrors that the handle must have been
installed (3.1) before it can be called.

**Ordering precondition `Requires(get_record() is True)` (weakest sufficient,
faithful to the callee).** `save_m2m` writes the m2m through-rows against
`self.instance`'s primary key (`save_form_data` materialises the relation via
the descriptor, which dereferences `instance.pk`). If the primary record has not
been written, `instance.pk is None` and the real callee RAISES
`ValueError: … needs to have a value for field "id" before this many-to-many
relationship can be used`. So the axiom may claim its success postcondition only
when `get_record() is True`; without this precondition the axiom would
over-claim (success regardless of record state), and a deferred-save-before-
record-write implementation would verify yet raise in-container. The precondition
is the weakest one that excludes the raising configuration.

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory sqlite
database and a minimal model with one `ManyToManyField`, then drives a real
`django.forms.ModelForm` exactly as the routine does: `ModelForm.save(form,
commit=False)` (3.1), `instance.save()` (3.2), `form.save_m2m()` (3.3). Over 50
observations (40 with a submitted association + 10 empty-m2m boundary) it
asserts: after the deferred save the handle exists and nothing is written; after
the record write the row exists but the m2m associations are still NOT written;
after the deferred save the m2m associations are written (and exactly the
submitted ones) without disturbing the record. It ALSO includes a **negative
observation** (trial 0) that exercises the ordering precondition: calling
`form.save_m2m()` BEFORE `instance.save()` (no primary key yet) must FAIL — the
checker asserts it raises and writes nothing, confirming
`Requires(get_record() is True)` is faithful rather than an over-claim. Exit
0 iff every observation (positive and negative) holds. It imports only the
standard library + Django (the framework the patch lives in). Pinned to the
`commit=False` base-save configuration the routine uses (§3.1).

### 3.4 `relations_done` — directive-8 / control-flow capability grounding of the relational-data fact (A-reference)
**No separate real callee.** `relations_done(self)` is the verification device
that grounds the relational-data fact so it cannot be fabricated by fiat nor
laundered across forms (closing the recover re-audit's surviving counterexamples:
the Unfold/assign/Fold fiat of pass 1, and the decisive cross-instance token
transfer `atk_echo_min` of pass 2, which ran the real deferred save on a scratch
form and copied its `rel_token` value onto `self`). It is a `@ContractOnly`
`@Predicate` with NO body. Two structural consequences make it unforgeable:
- **Not foldable:** an abstract (body-less) predicate cannot be `Fold`ed, so an
  implementation cannot conjure `relations_done(self)` by hand (Nagini rejects it
  at translation, `abstract.predicate.fold`); and there is no relational field to
  assign, so the value-level fiats have nothing to write.
- **Not transferable:** the predicate is parameterised by the form object, so a
  capability earned for a scratch form is `relations_done(scratch)` — a different
  predicate instance that does NOT discharge `relations_done(self)`.
`run_deferred_save(self)`'s `Ensures(relations_done(self))` is the sole producer.
This is a control-flow / capability grounding tied to the effect-producing step,
not an answer-key oracle pinned to `Result()` and not a copyable value — there is
no echo-the-oracle cheat (directive 8).

**Soundness check (G-AX):** `relations_done` has no separate callee, so its single
real-world claim — the m2m associations are NOT written before the deferred
relational save runs and ARE written by it — is validated by `axiom_check.py`'s
`relations_written(instance)` observations: after `ModelForm.save(commit=False)`
and after `instance.save()` the relations are unwritten, and only
`form.save_m2m()` writes them. No observation can ever show the relational data
written without `save_m2m`, which is exactly the asymmetry `relations_done`
encodes (granted solely by the deferred relational save).

## G-CONF (differential conformance — `conformance_check.py`)

**Pinned seed: `SEED = 16333`** (module constant in `conformance_check.py`).
**Input count: 100000** Requires-satisfying trials (25 boundary trials covering
the 24 distinct enumerated cells — the F2P cell is run first and then again in
enumeration order — followed by seeded fuzz over that same space to the target);
each trial drives BOTH legs end to end against a live in-memory sqlite ORM.

| leg | what it is |
|---|---|
| SHADOW | the `# impl-start`/`# impl-end` region of `save_form` copied **verbatim** (the region contains no contract calls — the `Requires`/`Ensures`/`MustTerminate` clauses all sit above `# impl-start` — so nothing needed stripping), plus the two `@Pure` accessors from the `pure` region minus their `Requires`/`Unfolding`. All three `@ContractOnly` callees are body-less axioms, so the shadow **calls the real** repo functions they axiomatize (§3): `BaseModelForm.save(form, commit=False)`, `instance.save()`, `form.save_m2m()`. The axioms are exercised, not assumed. |
| ORACLE | the **real patched** `UserCreationForm.save(self, commit=True)` (§1, `django/contrib/auth/forms.py:139`), **called** — not transliterated. Each trial builds a live validated `UserCreationForm` subclass over a custom user model with `ManyToManyField`(s) (the structural twin of the F2P test's `CustomUserWithM2M` + `Organization`) and calls `form.save(commit=…)`. |

**Observables diffed** (all five per trial): `get_record()` ⇔ the row exists;
`get_ready()` ⇔ `hasattr(form,"save_m2m")`; `relations_done(self)` ⇔ the real
`_save_m2m` ran for THIS form; `Result() is self` ⇔ `user is form.instance`; and
— as the concrete cross-check on the capability — the persisted association pks
per m2m field. The capability can therefore never be observed as held on one leg
while the written associations differ.

**Bridge (§2, inverted).** The `Form` carrier wraps a real bound
`UserCreationForm` plus the `instance` the base save builds. The two `@Pure`
accessors are the inversion point: rather than returning bookkeeping booleans the
axioms' `Ensures` would have set, they read the live repo facts
(`Model._default_manager.filter(pk=instance.pk).exists()` /
`hasattr(form,"save_m2m")`). Storing the booleans would have made the shadow's
guard `if self.get_ready()` depend on the axioms' *claims* — i.e. assume them;
reading live state means that guard is decided by exactly the fact the real
patched guard `if hasattr(self, "save_m2m")` tests. `relations_done(self)` is
observed by a per-form counter in a `_save_m2m` override that immediately
delegates to the REAL `BaseModelForm._save_m2m` (an observation of the
effect-producing step, symmetric across both legs, reimplementing nothing).

**Axiom `Ensures` re-asserted in situ.** So that the bridged accessors cannot
mask a divergence, each of the three callee wrappers checks its own axiom against
the live state where it is discharged: the base save must leave `get_ready()`
True with `get_record()` unchanged and grant no capability; the record write must
leave `get_record()` True with `get_ready()` unchanged and grant no capability;
the deferred relational save must be entered only with both facts True
(`Requires(get_record() is True)`, §3.3) and must leave both unchanged while
granting the capability. A violation is reported as a disagreement, exit 1.

**Input domain: inside the `Requires`.** Every counted trial passes a live bound
form whose entry state satisfies `save_form`'s precondition — `get_record() is
False`, and (the stronger of the two admitted deferred-save states)
`get_ready() is False`: a fresh, never-saved, never-deferred form, asserted
through the bridge on BOTH legs before each call — and both legs are driven to
completion, which is direct evidence for `MustTerminate(2)`. The precondition also
admits the re-entered state (`get_ready()` already True — refinement.md §A.1):
the conformance fixtures do not drive it, so what G-CONF attests is agreement on
the fresh entry state, and agreement on the re-entered one rests on the axioms
instead — the base-form save's `Ensures(get_ready() is True)` holds whichever
value it started from (`self.save_m2m = self._save_m2m` is an assignment, not a
toggle), the record write and the deferred save read only the facts the axioms
pin, and no step of the impl region reads the ENTRY value of `get_ready()` at
all (the guard reads it after the base-form save). The MODELED input space is **finite** (the only
modeled input is `commit: bool`), so the concrete degrees of freedom the bridge
exposes are enumerated **exhaustively** as the boundary set: {commit True,False} ×
{form shape: required-m2m F2P twin, blank-m2m, two-m2m-fields, m2m-less} ×
{0..3 submitted associations, where the shape admits it} = 24 cells, the F2P cell
(commit=True, required-m2m, one association) checked first; the fuzz then samples
that same space. Exhaustive enumeration of the finite modeled space plus fuzz
over it is a stronger check than 1e5 samples of a subset.

**Unmodeled node checked, not ignored.** §2 records
`user.set_password(cleaned_data["password1"])` as having no tracked node, so it is
absent from the impl region and hence from the shadow. Every trial asserts the
legs' credential divergence is EXACTLY that documented one (real leg carries a
hash, shadow carries none) and that it moves none of the tracked facts. The raw
`password` field is compared rather than `check_password`, which can trigger a
hash-upgrade write and would perturb the tracked record state.

**Vacuity guards (the check is built to be capable of failing).**
1. Success is refused unless the live `UserCreationForm.save` source actually
   contains the deferred relational save (i.e. the gate's patch-apply took
   effect); otherwise the differential would be vacuous.
2. Success is refused unless every branch of the impl region was taken:
   `(commit, ready, relations_done)` must include `(True, True, True)` — the
   committing arm with the guarded deferred relational save, the arm the change
   introduces — and `(False, True, False)`. Verified to fire: a mutated run whose
   space omits `commit=True` exits 1 with `branch coverage incomplete`.
3. **Falsifiability confirmed empirically:** run against unpatched `/testbed`
   (with only the patch-presence guard bypassed) the check fails on its FIRST
   input, the F2P cell, reporting `relations_saved shadow=True real=False` and
   `association_pks shadow=((1,),) real=((),)`, exit 1. So the check discriminates
   exactly the behaviour under specification.

Exit 0 iff zero disagreements. stdlib + Django (the framework the patch lives in)
only.
