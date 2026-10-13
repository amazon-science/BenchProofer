# refinement.md — django__django-11880

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`deepCopyField` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (the proof
uses this unchanged callee's contract, carried as a `require` on the parameter
that stands for its return value — see §B), **A-reference** (a deep model validated
== the real callee by G-AX), or **I** (identical concrete op). EVERY step is R,
A, or I.

The R/I legs are mechanically refuted by **G-CONF** — but this bundle's impl
region is **all-A-tagged** (`meta.json conf_skip=true`; see §C), so G-CONF is a
documented skip and the A legs carry the soundness, audited by **G-AX**
(`axiom_check.py`) and the narrative by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The clone routine — `Field.__deepcopy__` (`django/forms/fields.py:198`)

Gold hunk:
```
 def __deepcopy__(self, memo):
     result = copy.copy(self)
     memo[id(self)] = result
     result.widget = copy.deepcopy(self.widget, memo)
+    result.error_messages = self.error_messages.copy()
     result.validators = self.validators[:]
     return result
```

| # | Solution.lean impl op (`deepCopyField`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `source : FormField` | `self` (the field being cloned) | R | a `Field` instance ↔ `FormField` carrying its three by-reference attributes as `Obj` (identity + contents). mapping.md §2. |
| A2 | `let mut result := source` | `result = copy.copy(self)` | R | a SHALLOW copy duplicates references, not referents: the clone initially shares every attribute object with the source. The Lean record value-copy reproduces exactly this pre-state (`result.X.ref = source.X.ref` for every attribute X). `copy.copy` is an unchanged callee; only its reference-sharing effect is relevant and it is modeled directly (mapping.md §1). |
| A3 | (no node) | `memo[id(self)] = result` | I-bookkeeping | the deepcopy memo (cycle guard) does not affect the modeled observable (object identity of the clone's attributes); unmodeled (mapping.md §1). |
| A4 | parameter `widgetCopy : Obj` with `require freshDistinct widgetCopy source.widget`; `result := { result with widget := widgetCopy }` | `result.widget = copy.deepcopy(self.widget, memo)` | A-consumed | `copy.deepcopy` is an UNCHANGED callee returning a NEW object. A Django widget defines NO value equality (default identity `__eq__`), so the only sound, observable guarantee is distinct identity: the weakest sufficient contract is `freshDistinct` (`new.ref ≠ old.ref`). Claiming content-equality here would OVER-CLAIM (SPEC_GUIDE §0.7) — measured at `base_commit`, `copy.deepcopy(w) == w` is False for **27/27** widget classes in `django.forms.widgets`. The object the callee returned is taken as a PARAMETER constrained by exactly that contract (§B), and the assignment is modeled by `ensures result.widget = widgetCopy`: the Python statement is an ASSIGNMENT, so the slot holds precisely the callee's return value, which is the only thing observable about an opaque component. G-AX checks the contract against real `copy.deepcopy` (identity only). |
| A5 | parameter `messagesCopy : Obj` with `require freshCopy messagesCopy source.errorMessages`; `result := { result with errorMessages := messagesCopy }` | `result.error_messages = self.error_messages.copy()` **(the added line — the fix)** | A-consumed | `dict.copy()` is an UNCHANGED builtin returning a NEW dict with equal entries; a dict DOES define value equality, so the weakest sufficient contract is `freshCopy` (`new.ref ≠ old.ref ∧ new.payload = old.payload`). This is the single line the patch ADDS; its absence is the bug. The returned dict is taken as a PARAMETER under that contract and the assignment modeled by `ensures result.errorMessages = messagesCopy`; the `ref ≠` clause discharges `freshCopy result.errorMessages source.errorMessages`. G-AX checks against real `dict.copy()` (identity + content). |
| A6 | parameter `validatorsCopy : Obj` with `require freshCopy validatorsCopy source.validators`; `result := { result with validators := validatorsCopy }` | `result.validators = self.validators[:]` | A-consumed | `list[:]` is an UNCHANGED builtin returning a NEW list with equal elements; a list defines value equality, so the weakest sufficient contract is `freshCopy`. Same parameter+assignment modeling; both clauses are consumed. G-AX checks against real `list[:]` (identity + content). |
| A8 | field `carried : Obj` with `ensures result.carried = source.carried` | the field's class and every attribute `copy.copy(self)` carries over that the routine never re-points (`required`, `label`, `help_text`, `initial`, …) | R | A2's shallow duplication is what supplies all of it, and the routine leaves it alone, so it is modeled as ONE aggregate object and the faithful observation is IDENTITY, not content equality: a shallow duplication hands the clone the source's OWN objects. Measured on the modeled callee `Field.__deepcopy__` at `base_commit`: the clone is a new object, its class is the source's, and ALL untouched attributes (8–14 per class) are the SAME objects — 14/14 field classes, zero divergences. Without this leg a routine that CONSTRUCTS a fresh field and fills in the three copies is admissible; the G-EQ audit built exactly that attack and measured it FAIL_TO_PASS 1/1 pass but **95/114** PASS_TO_PASS failures, and it is the F2P's own first assertion (`isinstance(field_copy, CustomCharField)`). An identity clause is what excludes it: a reconstruction can produce equal-looking state but cannot hand back the source's own aggregate. |
| A7 | `return result` | `return result` | I | identical. |

The discriminating content of the change — the clone's override-message table
must be a **distinct object** from the source's — lives in postcondition
`freshCopy result.errorMessages source.errorMessages` (the `ref ≠` clause). The
pre-patch routine omits A5 (no `dict.copy()`), so after A2's shallow share
`result.errorMessages = source.errorMessages` and the postcondition reduces to
`source.errorMessages.ref ≠ source.errorMessages.ref` — **false**.
`Solution_prepatch.lean` reproduces exactly this and **fails** on that clause
(G-DIFF), which is the F2P assertion `field_copy.error_messages is not
field.error_messages`.

### Why two contracts (`freshDistinct` vs `freshCopy`)

The three copy callees do NOT all guarantee the same observable, so they get the
weakest contract sound for EACH (SPEC_GUIDE §0.7 — never claim more than the real
callee delivers):

* the **widget** (`copy.deepcopy`) yields a distinct object, but a widget has no
  value equality — `deepcopy(w) == w` is **False** — so its sound contract is
  `freshDistinct` (identity only). Pinning content-equality here is an unsound
  over-claim (it is the exact defect that an earlier draft of this bundle was
  correctly BLOCKED on by G-AX: `copy.deepcopy(TextInput) != TextInput`).
* the **error-message table** (`dict.copy`) and the **validators** (`list[:]`)
  yield a distinct object that ALSO compares `==` to the source, so they get the
  stronger `freshCopy` (identity + content).

Both contracts include the `ref ≠` (distinct-identity) clause; only that clause
is the F2P discriminator, and it is the one the prepatch fails.

## B. No consumed module-level axiom; no A-reference

There is no module-level `axiom`. The three copy callees are unchanged
library/builtin behavior, and each is modeled by taking THE OBJECT IT RETURNED as
a parameter of the routine (`widgetCopy`, `messagesCopy`, `validatorsCopy`),
constrained by a `require` carrying exactly that callee's guarantee —
`freshDistinct` for the opaque widget, `freshCopy` for the value-typed
attributes — and by nothing else. Sound by construction and G-AX-checked:
A-consumed, not A-reference (no deep model of a changed op; the changed "op" is
the *addition* of a copy, modeled by the same `freshCopy` contract the validator
copy already uses).

This is the parameter form of a callee model rather than a demonic `:|` binding.
The two are equivalent in strength on the postcondition — the `require` is
universally quantified over every object the callee could return, so nothing is
assumed about *which* answer it gives, only that the answer meets its guarantee —
and the parameter form additionally makes the ASSIGNMENT observable. That
matters here and nowhere else: for the opaque widget there is no content clause
available (§"Why two contracts"), so `ensures result.widget = widgetCopy` is the
only statement that can distinguish installing the callee's answer from
installing some other distinct object. A spec carrying only the identity clause
admits an implementation that copies the widget and then wipes what it holds
(measured: F2P passes, **18** PASS_TO_PASS tests fail) or that substitutes an
unrelated component (**44** PASS_TO_PASS fail). Both are genuinely wrong and
neither is reachable by any content obligation, because the component has no
readable content — which is precisely why the widget leg is stated as derivation
plus identity rather than as content equality.

## C. All-A-tagged impl ⇒ G-CONF skip; no kind-3

Every impl op is R (A1–A2 type/pre-state, A8 the carried-over aggregate), I (A3,
A7), or A-consumed (A4–A6). The non-trivial behavior is entirely the three copy
callees, so there is no R/I computational content to differential-test:
`meta.json conf_skip=true` and `conformance_check.py` exits `status=skip`. There
is no kind-3 step: the one operation that genuinely changed — adding an
independent copy of the override-message table — is expressible (it is the same
`freshCopy` contract already used for the validator copy), not an inexpressible
changed op.

## D. verify(Solution) ⇒ resolved

`deepCopyField` verifies only if the clone's widget is a DISTINCT object that is
PRECISELY the one `copy.deepcopy` returned (`freshDistinct` + `result.widget =
widgetCopy`, A4); the clone's error-message table AND validator collection are
each a DISTINCT object holding EQUAL contents and are precisely the objects
`dict.copy()` / `list[:]` returned (`freshCopy` + the two derivation clauses,
A5–A6); and the attributes the shallow duplication carries over are the source's
(A8, the carried aggregate). By R (`Field` ↔ `FormField`, `copy.copy` ↔ the
shallow record value-copy, `id` ↔ `ref`, `==` ↔ `payload`) the verified routine
equals the gold `__deepcopy__` on the touched attributes; by G-AX the three real
copy callees meet their respective contracts (A-consumed). The F2P test asserts
precisely `field_copy.error_messages is not field.error_messages` (the `ref ≠`
clause of A5) and `isinstance(field_copy, CustomCharField)` (clone type preserved
by `copy.copy`, A2/A8). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited callees — and the gold
patch resolves (G-RESOLVE). The sole trust points are `freshDistinct` /
`freshCopy` soundness (G-AX); there is no refinement-fidelity surface beyond them
(G-CONF skip, all-A-tagged).
