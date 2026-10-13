# refinement.md — django__django-14725

The operation-by-operation correspondence between `model.py`'s implementation
(the `persist` impl region and the two axiomatized persistence callees) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The save site — `BaseModelFormSet.save()` (`django/forms/models.py:679`)

Gold hunk:
```
- return self.save_existing_objects(commit) + self.save_new_objects(commit)
+ if self.edit_only:
+     return self.save_existing_objects(commit)
+ else:
+     return self.save_existing_objects(commit) + self.save_new_objects(commit)
```

| # | model.py impl op (`persist`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `self.restrict_to_existing` (bool field read) | `self.edit_only` (bool class attribute read) | R | bool ↔ bool, identity (mapping.md §2). The flag is read at fractional permission (read-only). |
| A2 | `if self.restrict_to_existing:` … `else:` | `if self.edit_only:` … `else:` | I | identical control flow (a two-armed branch on the flag). |
| A3 | `persist_existing_objects(self, commit)` (the restricted arm) | `self.save_existing_objects(commit)` | A-consumed | the unchanged existing-group primitive; its list content equals the opaque report `existing_report(commit)` and each run advances the existing-group invocation count by exactly one (mapping.md §3.1). The proof consumes `ToSeq(Result()) == existing_report(commit)` plus the count bump. |
| A4 | `persist_existing_objects(self, commit) + persist_new_objects(self, commit)` (the default arm) | `self.save_existing_objects(commit) + self.save_new_objects(commit)` | A-consumed + I | the two unchanged primitives (A-consumed, mapping.md §3.1/§3.2), each bumping its own invocation count once; the list `+` is the identical concrete concatenation (I). |
| A5 | `return result` (a `List[int]`) | `return …` (a `list` of instances) | R | `list` of instances ↔ `List[int]` of identifiers (mapping.md §2); the F2P tests observe which records are persisted and in what order, which the identifier sequence captures. |
| A6 | the invocation counts (`existing_runs` / `new_runs` behind `run_counts_pred`) | the DB side effect of each primitive invocation (rows saved / created) | R | one real invocation ↔ one count increment (mapping.md §2). The F2P tests observe the ABSENCE of the new-group effect under the restricting mode (`Author.objects.all()` gains no rows); "new-group count unchanged" is exactly that observation, and the abstraction predicate makes the count advanceable only by running the primitive. |

The discriminating content of the change — that the new group's primitive is
**never run** when the flag is set — lives in TWO paired postcondition clauses:
the content clause (1)
`Implies(self.restrict_to_existing, ToSeq(Result()) == existing_report(commit))`
and the effect clause (1e)
`Implies(self.restrict_to_existing, self.get_new_runs() == Old(self.get_new_runs()))`.
Clause (1e) is load-bearing: the callees are effectful (running
`save_new_objects` creates rows regardless of what the caller does with its
return value), so pinning only the returned sequence would admit an
implementation that runs the new-group primitive for its effect and discards
the report. The invocation counts, advanceable only through the primitives'
contracts (abstraction predicate `run_counts_pred`), rule that out. The
pre-patch code unconditionally runs both primitives and returns
`existing + new`; `model_prepatch.py` reproduces that (drops the branch,
always concatenates) and **fails** clause (1) — and would equally fail (1e) —
(G-DIFF). Clauses (2)
`Implies(not self.restrict_to_existing, ToSeq(Result()) == existing_report +
new_report)` and (2e) `… get_new_runs() == Old(…) + 1` pin the unchanged
default behaviour so a verifying impl can neither drop the new group when the
flag is *not* set (preserving the P2P tests) nor persist it more than once
(duplicate rows). The unconditional clause `get_existing_runs() == Old(…) + 1`
pins the existing-group primitive to exactly one run in both modes, and
`persist` carries `MustTerminate(2)` so no postcondition is discharged
vacuously by a non-terminating body.

## B. The factory sites — `modelformset_factory` / `inlineformset_factory`

Gold hunks add the keyword parameter `edit_only=False` to both factories and:
```
+ FormSet.edit_only = edit_only          # modelformset_factory
…
+ 'edit_only': edit_only,                # inlineformset_factory threads it through
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the `CollectionEditor.restrict_to_existing` field (the flag the operation reads) | `FormSet.edit_only = edit_only` and the kwarg threading | R | pure wiring: the factories only *place the flag on the FormSet class* (and `inlineformset_factory` forwards it to `modelformset_factory` unchanged). This introduces no behaviour beyond setting the field, which is modeled as the constructed value of `restrict_to_existing`. No own contract is needed (mapping.md §1). |

Why no separate failing `model_prepatch` for site B: the factory change is pure
plumbing — it merely makes the flag *settable*; it has no observable behaviour
of its own beyond the field it sets, which the save site (A) already exercises.
A `model_prepatch` must keep the spec byte-identical (G-DIFF `same_spec`); the
single differential witness at site A (the flag being ignored) is exactly the
fixed behaviour the factory plumbing enables. G-AX exercises the factory path
end-to-end (it constructs both factories with `edit_only=True/False`), so the
plumbing's correctness is audited against the real framework.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
`save`'s decision of whether to RUN the new-group primitive at all — is modeled
**directly** as the two-armed branch on the flag (step A2, I) over the two
**unchanged** callees (A3/A4, A-consumed). The primitives' report CONTENT stays
opaque (nothing about the *contents* of either group changed, so their
contracts assert nothing about content — never stronger than the real callees
exhibit). But the primitives are NOT pure report producers: each invocation is
an effect (rows saved / brought into existence), and the tested behaviour
observes precisely whether that effect occurred. That effect is therefore part
of the axiomatization — each callee's contract advances its own monotone
invocation count by exactly one (step A6, R), and the postconditions pin the
counts per mode. The changed operation is NOT axiomatized — it is the branch
itself, spelled out in the impl and pinned by the paired content+effect
postcondition implications.

## D. verify(model) ⇒ resolved

`persist` verifies only if (content) its result equals `existing_report(commit)`
when the flag forbids new records (A3, clause 1) and `existing_report(commit) +
new_report(commit)` otherwise (A4, clause 2), AND (effect) the existing-group
primitive ran exactly once, the new-group primitive never when the flag is set
(clause 1e) and exactly once otherwise (clause 2e) — the counts advance only
through the primitives' contracts (A6), so an implementation cannot obtain the
required counts without performing exactly those invocations, cannot invoke the
new-group primitive covertly for its record-creating effect, and (by
`MustTerminate`) cannot discharge any of this vacuously. By R (bool ↔ bool,
instance ↔ identifier, `list` `+` ↔ list `+`, invocation ↔ count increment) the
verified `persist` performs exactly `self.save_existing_objects(commit)` /
`… + self.save_new_objects(commit)` under the same branch as the gold `save`,
with the same invocation multiset per mode. By G-AX the two real primitives are
the unchanged callees the axioms abstract (no `edit_only` reference), and the
end-to-end FAIL_TO_PASS behaviour holds against the real framework. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited callees — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
