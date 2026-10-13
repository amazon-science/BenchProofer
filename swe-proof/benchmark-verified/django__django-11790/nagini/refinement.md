# refinement.md — django__django-11790

The operation-by-operation correspondence between `model.py`'s implementation
(the `configure_username_field` impl region and the `resolve_limit` deep model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated `==` the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The username-field configuration — `AuthenticationForm.__init__` (`django/contrib/auth/forms.py:194`)

Gold hunk:
```
-        self.fields['username'].max_length = self.username_field.max_length or 254
+        username_max_length = self.username_field.max_length or 254
+        self.fields['username'].max_length = username_max_length
+        self.fields['username'].widget.attrs['maxlength'] = username_max_length
```

| # | model.py impl op (`configure_username_field`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | precondition: `dict_pred(widget_attrs)` ONLY — no restriction on what the widget already carries | the gold write `self.fields['username'].widget.attrs['maxlength'] = username_max_length` is a TOTAL single-key assignment: it is valid and behaves identically in every pre-state of `widget.attrs` | R + I | the operation's DOMAIN, assigned a leg here rather than left unstated. The real call site does not occupy only a restricted set of pre-states: a subclass declaring its own `username` field changes `widget.attrs` at the hunk — `CharField(max_length=75)` yields `{'maxlength': '75'}` (a length limit already present) and `CharField()` / `IntegerField()` yield `{}` (no other attribute), both via `forms.Field.__init__` applying `widget_attrs()` (`django/forms/fields.py:57-60`, `CharField.widget_attrs` at `fields.py:231-235`). The spec therefore states no membership precondition, so every postcondition below binds on EVERY reachable pre-state. See §F. |
| A1 | parameter `declared_max_length: Optional[int]` | `self.username_field.max_length` (read at the hunk; `self.username_field = UserModel._meta.get_field(UserModel.USERNAME_FIELD)`) | R | `Optional[int]` ↔ a model field's `max_length` (`None` ⇔ no declared maximum, else the int). mapping.md §2. |
| A2 | `username_max_length = resolve_limit(declared_max_length)` = `default_limit()` if `declared is None or declared == 0` else `declared` | `username_max_length = self.username_field.max_length or 254` | R | EXACT mirror of Python truthiness on the `int`/`None` domain: both `None` and `0` are falsy and select 254. `0` is reachable (measured: a `TextField`/`BinaryField(unique=True, max_length=0)` `USERNAME_FIELD` passes the full check registry cleanly and the real patched form yields 254 in both places — mapping.md §2 note), so this is a genuine branch of the repo expression rather than an excluded input. The two F2P branches (255 / 254-default) are both witnessed. |
| A3 | `field_max_length = username_max_length`; `return field_max_length` | `self.fields['username'].max_length = username_max_length` | R | the form field's `max_length` attribute ↔ the returned `int`; the same resolved value (`Result() == resolve_limit(...)`). mapping.md §2. |
| A4 | `widget_attrs[attr_maxlength()] = username_max_length` (in-place dict write) | `self.fields['username'].widget.attrs['maxlength'] = username_max_length` | R + I | the widget's attribute `dict` ↔ `Dict[str, object]` with key `'maxlength'` ↔ `attr_maxlength()` (R) — and that binding is now the IDENTITY on the key, not an encoding of it: the model's name domain is text, so the index expression can only be the name itself or something equal to it as text, and no number can inhabit it. That is what makes the (I) claim below hold as stated. Under the earlier `Dict[int, ...]` carrier a name was an int and therefore the same kind of thing as a LENGTH, so an index expression built out of the length domain (`default_limit() + 746 == 1000 == attr_maxlength()`) was int-equal to the token and satisfied every clause while denoting a different real key — the (I) claim silently assumed the index expression WAS the token and did not hold for every int-equal expression. The in-place write with the *same* `username_max_length` under the *same* attribute name is the identical concrete operation (I). This is the line the regression dropped; the spec pins `widget_attrs[attr_maxlength()] == resolve_limit(...)` and `Result() == widget_attrs[attr_maxlength()]` (the field and widget carry the same resolved value). |
| A5 | frame: no widget attribute other than `attr_maxlength()` changes | the write touches only the `'maxlength'` key; all other entries of `widget.attrs` (`autofocus`, `autocapitalize`, `autocomplete`) are untouched | I | a single-key dict assignment leaves every other key and value unchanged, and the spec now states this as a machine-enforced FRAME: (i) membership equality — `Forall(a: a != maxlength ⟹ (a ∈ widget_attrs) == Old(a ∈ widget_attrs))` — no other key is added *or* dropped (Nagini proves it for the single-key write and refutes it for any impl that inserts a spurious extra key or drops one), and (ii) value preservation — `Forall(a: a != maxlength ∧ Old(a ∈ widget_attrs) ⟹ widget_attrs[a] == Old(widget_attrs[a]))` — every pre-existing attribute keeps its exact value (`Old` applied to the whole indexing expression is well-defined here; the guard `Old(a ∈ widget_attrs)` plus the membership frame gives the indexing precondition). A constant-witness instance `widget_attrs[attr_other()] == Old(widget_attrs[attr_other()])` is kept as a concrete readable witness. This frame is what closed the G-EQ spurious-extra-key break: a rival performing the gold write PLUS `widget.attrs['autocomplete'] = username_max_length` (clobbering the UsernameField hint, failing PASS_TO_PASS `test_html_autocomplete_attributes`) verified under the old no-key-dropped-only clause and is now rejected by (i). See §E. |

The discriminating content of the change — the *second* write that hoists the
resolved limit into `widget.attrs['maxlength']` — lives in step A4. The
pre-patch code performs only A2/A3 (field-level limit) and never A4;
`model_prepatch.py` reproduces that (it omits the
`widget_attrs[attr_maxlength()] = username_max_length` line) and **fails** the
postcondition `attr_maxlength() in widget_attrs` — exactly the spec sensing the
change (G-DIFF). That is also exactly what the F2P tests observe:
`form.fields['username'].widget.attrs.get('maxlength')` is `None` pre-patch and
the resolved limit (255 / 254) post-patch.

## B. Deep-model reference (A-reference), no consumed axiom

This bundle consumes **no axiom**. The changed operation is the field/widget
configuration itself, modeled **deeply** (`resolve_limit` + the two writes in
the impl region). The single **A-reference** is that this deep model equals the
real `AuthenticationForm.__init__` configuration.

| # | model.py construct | real operation | tag | justification |
|---|---|---|---|---|
| B1 | `resolve_limit` + the two writes in `configure_username_field` | `username_max_length = self.username_field.max_length or 254`; `field.max_length = username_max_length`; `widget.attrs['maxlength'] = username_max_length` (`forms.py:193-195` post-patch) | A-reference | the deep model is validated `==` the real gold-patched form configuration by `axiom_check.py` (G-AX): it instantiates the real `AuthenticationForm` against user models with varying declared `max_length` (incl. `None → 254`) and asserts `field.max_length` and `widget.attrs['maxlength']` both equal `resolve_limit(declared)`, plus that the other widget attributes survive. There is **no `@ContractOnly` axiom** the proof depends on. mapping.md §3.1. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — establishing the widget `maxlength` attribute equal to the resolved
field limit (A4) — is modeled **deeply** (an explicit dict write under full
permission, with the post-state pinned by the spec), not hidden behind an axiom
about the function under change: there is no consumed axiom at all. The
`resolve_limit` "declared-or-default" expression (A2) is a type/branch
refinement of `x or 254`, not an opaque callee.

## D. verify(model) ⇒ resolved

`configure_username_field` verifies only if (0) it does so from EVERY starting
state of the widget attribute map (A0: the sole precondition is
`dict_pred(widget_attrs)`, so no pre-state is exempt and no clause below can be
discharged vacuously), (1) it returns the resolved limit
`resolve_limit(declared_max_length)` (A2/A3), (2) the widget attribute map now
contains `attr_maxlength()` carrying that same resolved limit
(`widget_attrs[attr_maxlength()] == resolve_limit(...)` and
`Result() == widget_attrs[attr_maxlength()]`, A4), and (3) it changes NOTHING
else in the widget attribute map — the machine-enforced frame of A5: every
other key's membership is exactly preserved (no key added or dropped) and every
pre-existing key's value is exactly preserved. By R (Optional[int] ↔ model `max_length`,
`x or 254` ↔ the falsy-test (`None` or `0`), the widget attr `dict` ↔ `Dict[str, object]` with a textual name domain and an opaque value domain,
`'maxlength'` ↔ `attr_maxlength()`) the verified operation equals the gold
patch's three lines on the tested inputs; by G-AX the deep model equals the real
`AuthenticationForm` configuration (the A-reference, B1). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The only trust point is
refinement fidelity (this document, G-EQ) plus the deep-model A-reference
soundness check (G-AX); there is no consumed-axiom trust point.

## E. The machine-enforced frame — "no other key changed" as postconditions

An earlier revision of this bundle claimed the "no NEW key added" facet was not
expressible in Nagini's Dict fragment and carried it only by the single-key
impl structure. That was WRONG, and the G-EQ audit exploited it: a rival that
performed the gold write PLUS a spurious extra widget-attribute write verified
under the old spec, and its faithful patch — e.g.
`widget.attrs['autocomplete'] = username_max_length`, clobbering the
`UsernameField` autocomplete hint — fails PASS_TO_PASS
`test_html_autocomplete_attributes` / `test_inactive_user`
(`auth_tests.test_forms.AuthenticationFormTest`), so the spec admitted a
non-resolving implementation. The spec now ships a full frame, checked live
against Nagini (both directions verified on the gold impl and refuted on the
attack shapes):

1. **Membership frame (no key added OR dropped)** — `Forall(int, lambda a:
   Implies(a != attr_maxlength(), (a in widget_attrs) == Old(a in
   widget_attrs)))`. **Enforceable in both directions.** Nagini proves the
   equality for the single-key write and REFUTES it for an impl that inserts a
   spurious extra key (fresh token, before or after the gold write,
   unconditionally or on one branch) or drops a key. This closes the G-EQ
   spurious-key class outright.
2. **Value frame (every pre-existing key keeps its value)** — `Forall(int,
   lambda a: Implies(a != attr_maxlength() and Old(a in widget_attrs),
   widget_attrs[a] == Old(widget_attrs[a])))`. **Enforceable.** The guard form
   matters: with `Old` applied to the whole membership expression
   (`Old(a in widget_attrs)`), the indexing precondition inside the body is
   discharged by the membership frame (facet 1), and Nagini both proves the
   clause for the gold impl and refutes it for an impl that overwrites a real
   pre-existing attribute (e.g. `widget.attrs['autocomplete'] = ...`). (The
   variant guard `a in Old(widget_attrs)` does NOT discharge the indexing
   precondition and fails to verify — that syntactic dead end is what the
   earlier revision over-generalised into "not expressible".)
3. **Constant witness** — `widget_attrs[attr_other()] ==
   Old(widget_attrs[attr_other()])`. A concrete, readable instance of facet 2;
   kept for spec legibility.

Under the refinement, the frame states exactly what the gold patch's single
`widget.attrs['maxlength'] = username_max_length` line does: it touches the
`'maxlength'` key and nothing else. Two facets carry that, and both are needed.
The frame above says WHICH keys may change; the textual name domain (mapping.md
§2) is what makes "which key" mean the same thing in the model as in the repo,
so that the key the frame permits to change is the key the browser honours.
With a numeric name carrier the frame constrained the changed key only up to
int-equality of the token, so a rival could satisfy both frame facets — no key
added, none dropped, no value disturbed — while writing a real key that is not
`'maxlength'`; the misdirected-gold-key class was open even though the
spurious-EXTRA-key class was closed. It is the disjointness of the name and
length domains that closes it. Any impl performing extra widget-attribute
writes — which under a faithful translation would touch real attributes such
as `autocomplete`/`autocapitalize`/`autofocus` that PASS_TO_PASS tests pin —
now fails verification. The six LIVE clause groups (field value A2/A3,
maxlength presence + value A4, membership frame, value frame, constant witness)
each reject a distinct wrong impl; the positive control verifies (non-vacuous).

## F. Domain totality — the operation is specified from EVERY starting state

An earlier revision of this bundle carried two membership **preconditions**:
`Requires(attr_maxlength() not in widget_attrs)` and
`Requires(attr_other() in widget_attrs)`. They were an unstated DOMAIN
RESTRICTION, and the G-EQ audit exploited it. The defect is structural, not a
missing output clause: inside the excluded region Nagini discharges every
postcondition **vacuously**, so a rival could deviate arbitrarily there and
still verify, while under a faithful refinement that deviation is real
behaviour on states the caller genuinely reaches.

The states were reachable. The gold write is a TOTAL single-key assignment,
but the modeled domain was not total, and any subclass overriding the
identifier field lands outside it: `forms.Field.__init__` applies
`widget_attrs()` (`django/forms/fields.py:57-60`) and `CharField.widget_attrs`
sets `'maxlength'` (`fields.py:231-235`), so
`username = CharField(max_length=75)` arrives with `{'maxlength': '75'}` — a
length limit ALREADY present, violating the first precondition — while
`CharField()` / `CharField(label='')` / `IntegerField()` arrive with `{}` — no
other attribute at all, violating the second. Four PASS_TO_PASS tests
(`test_username_field_label`, `test_username_field_label_empty_string`,
`test_username_field_label_not_set`, `test_integer_username`, all
`auth_tests.test_forms.AuthenticationFormTest`) call the modeled operation
from exactly those pre-states. The witnessing rivals did the gold thing
in-domain and something else off-domain — one indexed the
formerly-guaranteed key inside a branch the precondition proved infeasible,
raising `KeyError` under a faithful refinement — and verified.

The repair makes the domain TOTAL rather than closing one path through it:

1. **Both membership preconditions are DROPPED.** The only remaining
   precondition is `dict_pred(widget_attrs)` (permission to mutate). No
   pre-state is excluded, so no branch is vacuously dischargeable and the
   clause groups of §D/§E bind everywhere. This is a STRENGTHENING: the claim
   is now made about strictly more inputs. It is also what the real operation
   satisfies — the gold assignment is unconditional and pre-state-independent.
2. **The two `attr_other()` witness postconditions are GUARDED** by
   `Old(attr_other() in widget_attrs)` instead of assuming presence. Guarding
   is required for faithfulness, not convenience: the real operation does NOT
   establish an unrelated attribute on a widget that lacked one, so an
   unguarded `attr_other() in widget_attrs` would be a clause the real patched
   function fails. The guarded form still refutes a rival that clobbers a
   pre-existing attribute (`atk_8`/W5) while permitting the real bare-widget
   behaviour, and the membership frame independently forbids inventing one.
3. **`attr_maxlength() in widget_attrs` and its value clause now bind on the
   already-present pre-state**, which is what makes "a stale length limit is
   REPLACED, not left standing" an obligation rather than an accident. A rival
   that writes only when the attribute is absent (W8) now fails C3/C4.

Newly load-bearing reject cases in the battery, each one a rival that verified
VACUOUSLY under the old domain and is refuted now (verifier output cited):

| case | rival | rejecting clause |
|---|---|---|
| W8 | widget write guarded by "length limit not already present" — leaves a STALE limit standing, so the rendered cap and the returned validation cap disagree | C3 `widget_attrs[attr_maxlength()] == resolve_limit(...)` |
| W9 | widget write guarded by "some other attribute already present" — the regression survives on the bare widget | C2 `attr_maxlength() in widget_attrs` |
| W10 | gold write PLUS inventing an unrelated attribute on a bare widget | C5 membership frame |
| W11 | indexes the formerly-guaranteed key inside a formerly-infeasible branch (the cleanest prior break; no Assert, no loop, no extra key) | the dict-read precondition itself no longer discharges |

The `admissibility` case correspondingly witnesses BOTH formerly-excluded
pre-states as in-domain and pins the required post-state on each. §E's frame
claim stands as written for output shape; §F is what makes it apply to the
whole reachable domain rather than to a restricted slice of it — a postcondition
frame cannot constrain a state the precondition excludes.
