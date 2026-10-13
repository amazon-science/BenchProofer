# mapping.md — django__django-14725

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0af9a5fc7d765aa05ea784e2c3237675f3bb4b49`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled / deep-modeled construct and its flag deps.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `saveFormset (noCreate) (existing) (fresh) (mut stored)` | `BaseModelFormSet.save(self, commit=True)` — `django/forms/models.py:667` (return expression at `:683`) | the modeled changed function (the persistence pass that settles a collection of editable rows and reports their identities) |
| `noCreate : Bool` | `self.edit_only` — the per-formset flag the patch threads through (`modelformset_factory(..., edit_only=False)` `:881`, set on the class at `:903`; `inlineformset_factory(..., edit_only=False)` `:1085`, forwarded at `:1118`) | whether bringing brand-new rows into being is forbidden |
| `existing : List Nat` *(A-reference)* | the return value of `self.save_existing_objects(commit)` — `django/forms/models.py:788` (the identities of the already-known rows it settles) | free-input abstraction of the **unchanged** existing-row persistence step; validated by axiom_check.py (G-AX) |
| `fresh : List Nat` *(A-reference)* | the return value of `self.save_new_objects(commit)` — `django/forms/models.py:814` (the identities of the brand-new rows it produces, which it persists as a side effect) | free-input abstraction of the **unchanged** new-row persistence step; validated by axiom_check.py (G-AX) |
| `stored : List Nat` *(mut)* | the persistent set of brand-new rows reachable through the model's default manager (what `Model.objects.all()` exposes beyond the already-known rows) | the observable side effect the F2P tests assert on (`Author.objects.all() == [charles]` when edit-only): `mut` because the permit-new branch grows it and the forbid-new branch must leave it untouched (directive 5) |
| `reported (noCreate) (existing) (fresh)` *(deep model — R/I)* | the post-patch return expression `self.save_existing_objects(commit)` if `edit_only` else `... + self.save_new_objects(commit)` (`:680-683`) | pure spec: the identities the pass reports |
| `storedAfter (noCreate) (priorStored) (fresh)` *(deep model — R/I)* | the cumulative side effect of the (possibly skipped) `save_new_objects(commit)` call on the persisted set of brand-new rows | pure spec: the stored collection after the pass |

The `commit` argument and the `commit=False` deferred-`save_m2m` block
(`:668-679`) are **unchanged** by the patch and do not influence which branch is
taken; they are not modeled and owe no contract. The patch's only behavioural
edit is the `if self.edit_only:` guard on the return/side-effect at `:680-683`.

The pre-patch repo behaviour the change guards against (refinement audit only,
not in the consumer spec view): `save` unconditionally evaluated
`self.save_existing_objects(commit) + self.save_new_objects(commit)`
(`:683` pre-patch), so it ALWAYS ran the new-row producer — creating rows even
when the caller wanted an edit-only view (`Solution_prepatch.lean`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§3) and G-CONF (§4) use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF / G-AX disagreements (the falsifiability the plan §4 trust statement
refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.edit_only : bool` | `noCreate : Bool` | `True ↔ noCreate = true`, `False ↔ noCreate = false`. The fix branches only on this flag. |
| the return of `save_existing_objects(commit)` — a `list` of saved model instances | `existing : List Nat` | each saved instance ↔ its primary-key identity `Nat`; list order preserved; Python `list` concat `+` ↔ `List` `++`. |
| the return of `save_new_objects(commit)` — a `list` of created model instances | `fresh : List Nat` | each created instance ↔ its primary-key identity `Nat`; order preserved. |
| the persisted set of brand-new rows (the rows `save_new_objects` inserts, observable via `Model.objects.all()`) | `stored : List Nat` (entry `storedOld`, exit `stored`) | each persisted new row ↔ its identity `Nat`; `save_new_objects` appends exactly the `fresh` identities to this set (G-AX §3.2); empty side effect ↔ `stored = storedOld`. |
| the list `save()` returns | `out : List Nat` | the reported identities; order preserved; observed element-wise as primary keys. |

Identities are carried as `Nat` (not the rich model instance) because the only
operations the change performs on the two component results are
order-preserving concatenation (`++`) vs. total suppression of one component,
plus the membership/side-effect on the persisted set — all exact on `List Nat`.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

There are **no consumed axioms**. The two unchanged persistence steps the
changed `save` sits on top of are abstracted as **free inputs** (`existing`,
`fresh`); their relied-on reference behaviour is validated against the real
callees, driven by a live in-memory modelformset exactly as the F2P tests drive
it.

### 3.1 `existing` ↔ `save_existing_objects` (A-reference)
**Callee:** `BaseModelFormSet.save_existing_objects(commit)` (`django/forms/models.py:788`).
It iterates the `initial_forms` (the already-known rows), saves the changed
ones, and returns their saved instances. It is **unchanged** by the patch and
runs identically in both branches (it is always called). The reference property
the spec relies on: its result — the already-known identities — does **not**
depend on `edit_only`, and it never creates brand-new rows (it touches only the
`initial_forms`). Reached in both branches of the post-patch `save`.

**G-AX check:** build a real `modelformset_factory(...)` over an in-memory
SQLite model, submit POST data with both initial (edit) and extra (new) rows,
and assert that `save_existing_objects(commit)` returns the same set of
already-known identities whether the formset's `edit_only` is `True` or `False`,
and that calling it alone persists **no** brand-new rows.

### 3.2 `fresh` ↔ `save_new_objects` (A-reference)
**Callee:** `BaseModelFormSet.save_new_objects(commit)` (`django/forms/models.py:814`).
It iterates the `extra_forms` (the surplus rows), saves the changed/undeleted
ones as **brand-new** rows, and returns the created instances. It is
**unchanged** by the patch. The two reference properties the spec relies on:
(a) the identities it returns are exactly the brand-new rows it persists — so
its return value `fresh` and its side effect on the persisted set coincide
(`storedAfter` appends exactly `fresh`); and (b) it is the **only** source of
brand-new rows in `save`, so suppressing the call (the `edit_only` branch)
persists no new rows — the F2P-observable effect (`Author.objects.all()`
unchanged).

**G-AX check:** with the same live modelformset, assert that calling
`save_new_objects(commit)` creates exactly the rows whose identities it returns
(return value == newly-persisted identities), and that a full `save()` with
`edit_only=True` leaves the persisted-row set equal to its pre-`save()` contents
(no new rows), whereas `edit_only=False` adds exactly the `save_new_objects`
identities. This validates both the `existing`/`fresh` abstraction and the
`stored` side-effect frame.

### 3.3 Flag dependency (G-AX configuration)
The branch is taken on `self.edit_only`, a class attribute the patch adds to the
`FormSet` produced by `modelformset_factory` / `inlineformset_factory`
(`edit_only` kwarg, default `False`). G-AX fuzzes both `edit_only ∈ {True, False}`
configurations so the reference properties are checked under each flag value.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14725`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `reported` / `storedAfter` to Python (the `if noCreate then …
else …` branch over the two component lists) and leaves the A-tagged callees
(`save_existing_objects`, `save_new_objects`) as **stubs returning the supplied
free-input identity lists** while observing whether the new-row producer was
invoked — bridging to the real patched `BaseModelFormSet.save` driven over the
abstract `(edit_only, existing, fresh)` carrier. Both the reported list and the
"was the new-row producer run" side-effect flag are differentially tested; the
impl region's computed output is pure R/I, so `conf_skip = false`.
