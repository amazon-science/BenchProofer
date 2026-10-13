# mapping.md — django__django-14725

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0af9a5fc7d765aa05ea784e2c3237675f3bb4b49`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `CollectionEditor.restrict_to_existing` | `BaseModelFormSet.edit_only` (set on the FormSet class by the factory: `django/forms/models.py:899` post-patch `FormSet.edit_only = edit_only`) | the modeled changed state — the new per-formset mode flag |
| `persist(self, commit)` | `BaseModelFormSet.save(self, commit=True)` — `django/forms/models.py:667` (body line 679, the changed `return`) | the modeled changed function (the formset save) |
| `persist_existing_objects(self, commit)` *(axiom callee, A-consumed)* | `BaseModelFormSet.save_existing_objects(self, commit=True)` — `django/forms/models.py:788` | unchanged callee: persists the already-existing (initial) forms and returns the list of saved instances; each run is an EFFECT (modeled as +1 on the editor's existing-group invocation count) |
| `persist_new_objects(self, commit)` *(axiom callee, A-consumed)* | `BaseModelFormSet.save_new_objects(self, commit=True)` — `django/forms/models.py:814` | unchanged callee: persists the new (extra) forms and returns the list of created instances; each run is an EFFECT that brings the new group into existence (modeled as +1 on the editor's new-group invocation count) |
| `existing_report(commit)` *(axiom, A-consumed)* | the *content* of `save_existing_objects`'s return — the sequence of already-existing saved-instance identifiers | pure spec: report of the existing-group primitive |
| `new_report(commit)` *(axiom, A-consumed)* | the *content* of `save_new_objects`'s return — the sequence of new saved-instance identifiers | pure spec: report of the new-group primitive |
| `CollectionEditor.existing_runs` / `CollectionEditor.new_runs` (behind `run_counts_pred`, read via `get_existing_runs` / `get_new_runs`) | the *fact of invoking* `save_existing_objects` / `save_new_objects` — i.e. the persistence side effect each invocation performs (rows saved / created in the DB) | effect footprint: a monotone per-primitive invocation count, advanceable ONLY by running the corresponding primitive (abstraction predicate), so the spec can pin whether and how many times each primitive runs per mode |

The factory plumbing the gold patch also touches —
`modelformset_factory` (`django/forms/models.py:872`, gains the `edit_only=False`
kwarg and `FormSet.edit_only = edit_only`) and `inlineformset_factory`
(`django/forms/models.py`, gains `edit_only=False` and threads it through the
`kwargs` dict to `modelformset_factory`) — is pure wiring that places the flag
on the FormSet class. It is observed in `model.py` only as the
`CollectionEditor.restrict_to_existing` field the flag becomes; it introduces no
behaviour beyond setting that field, so it has no own contract (refinement.md §B).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.edit_only` (a `bool` class attribute on the FormSet) | `self.restrict_to_existing: bool` field | identity on booleans |
| return of `save` / `save_existing_objects` / `save_new_objects`: a Python `list` of model instances | `List[int]` of record identifiers | a saved instance ↔ its integer identifier; `list` concatenation `a + b` ↔ list `+`; an empty list ↔ `[]` |
| `list` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`len`/`[i]` mirror `list` `+`/`len`/index |
| the `commit` argument (a `bool`) | `commit: bool` | identity on booleans (passed through unchanged to both primitives, exactly as in the repo) |
| the DB-visible side effect of one invocation of a persistence primitive (rows saved / brought into existence) | `+1` on that primitive's monotone invocation count (`existing_runs` / `new_runs`, behind `run_counts_pred`) | one real invocation ↔ one count increment; "the primitive never ran" ↔ count unchanged; the F2P tests observe exactly this effect (`Author.objects.all()` gains no rows iff `save_new_objects` never ran) |

The instances the F2P tests observe are compared by identity / database row
(e.g. `assertSequenceEqual(Author.objects.all(), [charles])`), so abstracting
each saved instance to its identifier and the result to the *sequence of
identifiers* is faithful: the tested property is which records are persisted and
in what order, which the identifier sequence captures exactly.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

Both axioms abstract callees the changed `save` invokes but **does not change**.
The gold patch's three hunks edit `save`'s `return`, `modelformset_factory`'s
signature/body, and `inlineformset_factory`'s signature/kwargs — none touches
`save_existing_objects` or `save_new_objects`. So treating their returns as
opaque reports is faithful, and the only behaviour the proof relies on is:

### 3.1 `existing_report` ↔ `save_existing_objects` (A-consumed)
**Callee:** `BaseModelFormSet.save_existing_objects(self, commit=True)`
(`django/forms/models.py:788-812`). It iterates `self.initial_forms` only,
persisting the already-existing rows (calling `save_existing` / `delete_existing`
on the bound objects) and returning the list of saved instances. It never
constructs a new object — `obj = form.instance` is an *existing* bound instance,
and forms whose `obj.pk is None` (an object outside the formset's queryset) are
*skipped* (`continue`), never created. The report axiom is the weakest the
proof needs for CONTENT: `existing_report(commit)` is an opaque `PSeq[int]` —
the contract asserts nothing about its content, only that
`persist_existing_objects`'s list content equals it
(`ToSeq(Result()) == existing_report(commit)`). Additionally the callee's
contract records its EFFECT: each run advances the editor's existing-group
invocation count by exactly one (and leaves the new-group count unchanged),
and it promises termination (`MustTerminate(1)`, bounded per-form work). The
proof uses that this list IS the existing group's report and that the
primitive ran exactly once.

### 3.2 `new_report` ↔ `save_new_objects` (A-consumed)
**Callee:** `BaseModelFormSet.save_new_objects(self, commit=True)`
(`django/forms/models.py:814-826`). It iterates `self.extra_forms` only,
creating one new object per changed extra form (`self.save_new(form, ...)`) and
returning the list of new instances (empty when none changed). Likewise opaque
for CONTENT: `new_report(commit)` is an opaque `PSeq[int]`; `persist_new_objects`'s
list content equals it. Its EFFECT — bringing the new group's records into
existence — is recorded by its contract advancing the editor's new-group
invocation count by exactly one per run (existing-group count unchanged;
`MustTerminate(1)`). This is the discriminating effect the tested behaviour
observes: under the restricting mode the primitive must never run at all.

**Why opaque reports suffice for CONTENT — and why the effect counts are also
needed:** the *only* behaviour the gold change introduces is **whether the new
group's primitive runs at all**. The existing/new split, the per-form
persistence, and the contents of each group are entirely unchanged by the patch
— they live in the two unchanged primitives. So the spec needs no knowledge of
the reports' values, only (a) the structural fact that `save` returns the
existing report when the flag forbids new records, and the existing report
**followed by** the new report otherwise, and (b) the EFFECT fact that the
new-group primitive runs exactly once in the default mode and **never** when
the flag forbids new records (and the existing-group primitive exactly once in
both modes). Fact (b) is carried by the per-primitive invocation counts: each
callee is effectful (its dominant observable is the rows it saves/creates), so
its contract advances its own count by exactly one per run, and `persist`'s
postconditions pin the counts per mode. Constraining only the returned sequence
would leave an implementation free to run the new-group primitive for its
record-creating effect while discarding its report — the counts close exactly
that gap. The counts live behind an abstraction predicate (`run_counts_pred`)
with pure accessors, so they can be advanced ONLY by running the primitives,
never fabricated by a direct field write. Pinning the result to the
concatenation of the two reports (not a hardcoded answer) still forces the
result to be *produced by* invoking the right primitives (SPEC_GUIDE directive
8); pinning the counts forces them to be invoked the right NUMBER OF TIMES.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL Django formset
machinery inside the official container. It (i) asserts via `inspect.getsource`
that neither `save_existing_objects` nor `save_new_objects` references
`edit_only` (they are the unchanged primitives the axioms abstract); (ii) drives
`modelformset_factory(..., edit_only=True/False)` and
`inlineformset_factory(..., edit_only=True)` through the exact three FAIL_TO_PASS
scenarios plus a default-mode scenario, asserting end-to-end that `save()`
returns the existing group alone under restriction (creating no new rows) and
the existing group followed by the new group otherwise. Exit 0 iff every
obligation holds. It imports only Django (the framework under test) and stdlib
`inspect` — nothing bundle-specific.

## 4. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl region of `persist`
(its two @ContractOnly callees delegating to the REAL unchanged primitives on
a real bound formset, each delegation advancing the shadow's own invocation
count by one) differentially against the real patched
`BaseModelFormSet.save(commit)` in the instance container. Per probe it
compares the returned identifier sequence (instances lowered per §2) and both
per-primitive invocation counts (the oracle side instrumented with counters).
>= 1e5 Requires-satisfying checks: boundary + fuzz scenarios, each crossed
with both flag values and both `commit` values. **Pinned fuzz seed: 14725.**
