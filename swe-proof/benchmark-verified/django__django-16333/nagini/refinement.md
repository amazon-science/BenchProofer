# refinement.md — django__django-16333

The operation-by-operation correspondence between `model.py`'s implementation
(the `save_form` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The save site — `UserCreationForm.save` (`django/contrib/auth/forms.py:139`)

Pre-patch body (lines 140-144):
```python
user = super().save(commit=False)
user.set_password(self.cleaned_data["password1"])
if commit:
    user.save()
return user
```

Gold hunk (the two added lines):
```
         if commit:
             user.save()
+            if hasattr(self, "save_m2m"):
+                self.save_m2m()
         return user
```

| # | model.py impl op (`save_form`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `base_form_save_deferred(self)` | `user = super().save(commit=False)` | A-consumed | the base-form save in deferred mode: installs the deferred relational save handle and writes nothing (mapping.md §3.1). The proof consumes `Ensures(deferred_save_ready is True)` and the no-write clauses. It HANDS BACK the record object (`return self.instance`, bound to `user`) that A4 and A6 operate on; it does not create it — the form built `self.instance` from the submitted data while validating, before the routine was entered. The model carries that object as `record_available(self)`, which `save_form` already `Requires` at entry and which every callee both `Requires` and `Ensures`, so A1 is NOT its producer and the capability forbids no ordering (mapping.md §2.2). |
| A2 | (no node) | `user.set_password(self.cleaned_data["password1"])` | R | the password assignment touches credential state, not record/relational persistence; it reads/writes none of the three observed booleans, so under the type abstraction (mapping.md §2) it is the identity on the modeled state. |
| A3 | `if commit:` | `if commit:` | I | identical concrete boolean branch on the same parameter. |
| A4 | `persist_record(self)` | `user.save()` | A-consumed | the primary-record write: sets `record_persisted` True, does NOT grant the relational-data capability `relations_done(self)` (mapping.md §3.2). The proof consumes its `Ensures` to discharge `Implies(commit, get_record())`; the record write never earns the relational-data capability — the fact that makes A6 necessary. It writes the form's record object, so it `Requires(record_available(self))` — the capability NAMES that object rather than ordering the steps: the form holds it from entry, so `user.save()` may run at any point in the routine (mapping.md §2.2). |
| A5 | `if self.get_ready():` | `if hasattr(self, "save_m2m"):` | R | `deferred_save_ready: bool` (read via `get_ready()`) ⇔ `hasattr(self, "save_m2m")` (mapping.md §2). The added guard. Here it is provably True — established by A1's `Ensures` on a form entered fresh, and already true at entry on a form that was asked to defer earlier — exactly mirroring that `super().save(commit=False)` always installs `save_m2m` and that an earlier deferred request leaves it installed. |
| A6 | `run_deferred_save(self)` | `self.save_m2m()` | A-consumed | the deferred relational save: it is the SOLE producer of the abstract per-form capability `relations_done(self)` (mapping.md §3.3 / §3.4). The proof consumes its `Ensures(relations_done(self))` to discharge the discriminating postcondition `Implies(commit, relations_done(self))` — and only it can, because `relations_done` is a body-less predicate (cannot be folded by fiat) bound to `self` (a capability for any other form does not discharge it). Its `Requires(get_record() is True)` is discharged because A4 (`persist_record`) ran first in the impl — so this step is reachable ONLY after the record write, mirroring that the real `save_m2m` needs the record's primary key. It likewise `Requires(record_available(self))` — it attaches the associations to the form's record object, which the form holds throughout, so that clause names the object and adds no ordering of its own (mapping.md §2.2). This is the operation the gold patch ADDS. |
| A7 | `return self` | `return user` | R | the routine returns the form's instance; the model returns the same `Form` (`Result() is self`) carrying the instance's persistence state (mapping.md §2). |

The model adds a `Requires(MustTerminate(2))` termination obligation to
`save_form` (and `Requires(MustTerminate(1))` to each `@ContractOnly` callee).
This is NOT an impl step in `patch.diff` — it is a **verification-scaffolding
obligation** (mapping.md §2.1) that pins that the routine terminates, which the
real `UserCreationForm.save` trivially does (a straight-line body of bounded
calls, no recursion). It refines to "the routine terminates," which holds for the
gold patch; it adds no behaviour. Its purpose is purely to close the
function-under-spec self-echo (see §C, DEFECT-5): without it Nagini's
partial-correctness semantics would let a non-terminating self-recursive body
vacuously satisfy the postcondition. So it does not create a kind-3 step — there
is no gold operation it corresponds to; it is the termination side-condition of
the single modeled function, mirroring that `UserCreationForm.save` terminates.

### A.1 The entry states the map is claimed on

The map above is claimed on every entry state `save_form`'s precondition admits,
and that domain is chosen from the repo's own call sites rather than from the gold
body's shape:

* `Requires(get_record() is False)` — the primary record has not been written yet.
  This routine is what writes it, which is what makes the record clauses claims
  about a write it performed; and it is what keeps
  `Ensures(Implies(not commit, get_record() is False))` TRUE of the real function,
  since a deferred request cannot un-write a row an earlier immediate request
  already wrote. No test in the instance's scope re-enters the routine on an
  already-saved instance (`tests/auth_tests/test_forms.py` has no
  `form.save()`-then-`form.save()` sequence for this form).
* The deferred-save fact is **unconstrained at entry**. Asking for deferred
  persistence is exactly what installs the handle, so a form asked to defer and
  then asked to persist is entered with `get_ready()` already True — the repo's own
  passing suite drives precisely that sequence (`test_success` in
  `auth_tests.test_forms.UserCreationFormTest`: `form.save(commit=False)` and then
  `form.save()`, requiring the second call to have really persisted). Every clause
  of the map holds on that entry state for the gold-patched routine: A1 re-installs
  the handle (`self.save_m2m = self._save_m2m`), A4 writes the record, A5's guard
  is true, A6 writes the associations, A7 returns `self.instance`. Leaving the
  entry fact free is therefore not a weakening but the opposite — the guarantees
  are claimed on strictly more inputs, including the half of the domain the
  PASS_TO_PASS test occupies. Pinning it to False instead left that half unreached
  by any clause (no postcondition mentions the ENTRY value of `get_ready()`), where
  an implementation could branch on it and persist nothing while discharging every
  clause: measured, `if self.get_ready(): return self` VERIFIED, and its faithful
  refinement failed `test_success` with `FAIL_TO_PASS 1/1 pass` (recorded in §C).

## B. Type refinement of the carrier

The form instance and its model object are collapsed into one minimal `Form`
carrying the persistence facts (mapping.md §2): `record_persisted` (the primary
row exists), `deferred_save_ready` (`hasattr(self, "save_m2m")`), and the
relational-data fact (the deferred relational save has been run for this form).
The first two are plain booleans behind the abstraction predicate `form_pred()`.
The relational-data fact is grounded MORE STRONGLY (directive 8 / control-flow
effect token): it is NOT a value the impl can read, write or copy but the
abstract per-form CAPABILITY `relations_done(self)` — a `@ContractOnly`
predicate with NO body. An implementation therefore cannot establish it:
- it cannot get it from any other step: no callee's postcondition but
  `run_deferred_save(self)`'s grants it, however many times the others are
  invoked (`weak-fiat-no-producer` FAILS on `Ensures(Implies(commit,
  relations_done(self)))` for insufficient permission — a Viper verdict), and
  there is no relational field at all to assign. Folding it by hand is closed a
  level earlier still, statically by the front end (`abstract.predicate.fold`,
  which also covers `Unfold`/`Unfolding`) — an encoding fact rather than a
  verdict, so nothing in the battery is scored on it, AND
- it cannot transfer a capability earned for another form: running the real
  `run_deferred_save(scratch)` on a throwaway `Form()` grants
  `relations_done(scratch)`, which is a DIFFERENT predicate instance from
  `relations_done(self)` and does NOT discharge the postcondition for `self`
  (closes the recover re-audit's surviving token-transfer / echo-the-oracle
  counterexample — the prior `rel_written(token: int)` grounding was an
  identity-blind global on a copyable int; the capability predicate is bound to
  the form object, not a transferable value).
The capability `relations_done(self)` is granted ONLY by A6 / `run_deferred_save`
run on `self`, whose `Ensures(relations_done(self))` is its sole producer.

The record OBJECT the two persistence steps act on is grounded the same way, as the
body-less per-form capability `record_available(self)` (mapping.md §2.2) — but it is
held from ENTRY rather than produced by a step. In the repo the form builds
`self.instance` from the submitted data while validating, so the object exists
before the routine is entered and `super().save(commit=False)` merely returns it;
there is no moment inside the routine at which it is missing. Accordingly
`save_form` `Requires(record_available(self))`, every callee both `Requires` and
`Ensures` it, and the routine `Ensures` it — so the capability constrains NO order
of the steps and states only that one and the same object is what all of them, and
the returned value, are about. The order the model does constrain is the one the
repo constrains: A6's `Requires(get_record() is True)`, i.e. the deferred
relational save may run only after the record write has really happened. Attributing
production of the record object to A1 instead would forbid an order the repo
permits — writing the primary record before invoking the base-form save, whose
faithful refinement passes the F2P and 796 tests across `auth_tests` +
`model_forms` — which is why that shape is a positive control (properties.py
`pos-control-record-write-before-base-save`, expect="verify").

The repo's `super().save(commit=False)` returns the instance and sets `self.save_m2m`;
the model folds both effects onto the one `Form` via A1. `Result() is self`
matches `return user` because the returned instance and the form that saved it
are the single tracked object under the abstraction (the F2P test reads the
persisted associations off the returned `user` via `user.orgs.all()`).

## C. The discriminating clause (G-DIFF)

The behaviour the change introduces is: when committing, the deferred relational
data must end up persisted. This lives in the postcondition
`Ensures(Implies(commit, relations_done(self)))`, discharged ONLY by the A6 call
(`run_deferred_save` on `self`) — and ONLY by it, because `relations_done` is an
abstract (body-less) per-form capability predicate and `run_deferred_save` is the
sole operation whose `Ensures` produces it (no implementation can satisfy the
clause by `Fold(relations_done(self))` — abstract predicates cannot be folded —
and there is no relational field to assign; nor by running the deferred save on a
scratch form, whose capability `relations_done(scratch)` is a different predicate
instance that does not discharge `relations_done(self)`; directive-8 /
control-flow grounding).
`model_prepatch.py` is the pre-patch skeleton — byte-identical spec, but the
`if self.get_ready(): run_deferred_save(self)` block (A5+A6) is absent (exactly
the pre-patch body, which stops after `user.save()`). It **fails** verification on
`Implies(commit, relations_done(self))` ("insufficient permission to access
relations_done(self)", `model_prepatch.py:303`), which is precisely the spec
sensing the missing deferred relational save (G-DIFF). This is the single
independently-fixed behaviour, so one `model_prepatch.py` suffices.

**Adversarial robustness (G-EQ, post-refinement).** The attack classes from all
four adversarial verdicts (batch04 + recover re-audit pass 1 [Unfold/Fold] +
recover re-audit pass 2 [token transfer] + recover re-audit pass 3 [self-echo])
were re-checked against the frozen spec on the real verifier:
- *Function-under-spec self-echo* (the recover re-audit pass-3 decisive
  counterexample `atk_selfrecurse`: impl body `return save_form(self, commit)`,
  which under partial-correctness semantics would re-derive `relations_done(self)`
  from this routine's own contract while its faithful refinement is non-
  terminating self-recursion that never persists): FAILS — "Obligation leak check
  failed. Callee save_form might not take all unsatisfied obligations from the
  caller." The `Requires(MustTerminate(2))` on `save_form` vs `MustTerminate(1)`
  on the callees forbids a self-call (no strictly smaller measure). [DEFECT-5,
  termination-obligation fix; mapping.md §2.1]
- *Token-transfer / echo-the-oracle* (the recover re-audit's decisive surviving
  counterexample `atk_echo_min`: run the real `run_deferred_save` on a scratch
  `Form()`, then try to use `relations_done(scratch)` for `self`): FAILS —
  "insufficient permission to access relations_done(self)" (the scratch
  capability is a different predicate instance). [DEFECT-4, capability-predicate fix]
- *Fiat without the producer* (`weak-fiat-no-producer`: on commit, invoke every
  axiom EXCEPT `run_deferred_save`, twice over): FAILS on the discriminating
  clause — "Postcondition of save_form might not hold. There might be
  insufficient permission to access `relations_done(self)`" at `model.py:303`,
  19.4s. It is the ONLY error reported, so the rival is right about everything
  else and is turned down for the fiat alone: no callee but the sole producer
  hands the capability over, however often the others run. Non-vacuity control:
  `Assert(False)` inside that body's `if commit:` branch FAILS, so the branch is
  reachable. This subsumes the prior DEFECT-1 (direct field assign) and DEFECT-3
  (Unfold/assign/Fold) fiats: there is no relational field to assign, and an impl
  that unfolds `form_pred` and pokes `record_persisted`/`deferred_save_ready`
  likewise FAILS — those fields do not earn the capability.
  The literal fiat `Fold(relations_done(self))` is closed one level earlier, by
  the FRONT END: Nagini rejects a fold of a body-less predicate statically
  (`abstract.predicate.fold`, and likewise `Unfold`/`Unfolding`), so it never
  reaches Viper. That is a property of the encoding, not a verdict on the spec,
  and no reject case is scored on it — `weak-fiat-no-producer` is the
  translatable form of the attack, which is why the fold body was replaced by it.
- *Deferred save before record write* (`run_deferred_save` then `persist_record`):
  FAILS — `run_deferred_save`'s `Requires(get_record() is True)` does not hold,
  mirroring the in-container `ValueError` (no primary key yet). [DEFECT-2, ordering fix]
- *Unconditional persist* (`persist_record`/`run_deferred_save` outside the
  commit guard): FAILS on `Implies(not commit, get_record() is False)`.
- *Prepatch shape* (no deferred save at all): FAILS on the discriminating
  postcondition above (= `model_prepatch.py`).
- *Re-entered entry state* — the family the entry domain of §A.1 exists to reach,
  each one measured on the real verifier against this frozen spec:
  - short-circuit on the entry fact (`if self.get_ready(): return self`, then the
    gold body): FAILS — "Postcondition of save_form might not hold. Assertion
    Implies(commit, (self.get_record() is True)) might not hold." Its faithful
    refinement (an early `if hasattr(self, "save_m2m"): return self.instance`) was
    run through the real harness: **FAIL_TO_PASS 1/1 pass, PASS_TO_PASS fails 1/87 —
    `test_success (auth_tests.test_forms.UserCreationFormTest)`; did not resolve in
    3 attempts (consistent, not flaky)**. This is the P2P half of `does not
    resolve`: it fixes the reported bug and destroys behaviour that worked.
  - divergence on that half (`if self.get_ready(): while True: ...`): FAILS —
    "Obligation leak check failed. Loop might not take all unsatisfied obligations
    from the context." (`Requires(MustTerminate(2))` reaches the loop only because
    the entry fact is free; under the narrower domain the loop was dead code.)
  - partial domain (`if not self.get_ready():` around the whole body): FAILS on the
    same record clause.
  - the prepatch bug restricted to that half (run the deferred save only when the
    handle was not already installed): FAILS — "insufficient permission to access
    relations_done(self)".
  - ignoring `commit` on that half, laundering the capability from a scratch form on
    that half, forging the record fact on that half, and self-echoing on that half:
    all FAIL (record clause / `relations_done(self)` permission / read-only
    assignment / obligation leak respectively).
A gold-faithful control (record write, then deferred save, guard optionally
dropped since A1 always establishes `get_ready()`) VERIFIES, as does the
gold-faithful impl (with the guard).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation the gold patch ADDS — the
guarded deferred relational save — is modeled with **I** (the `commit` branch),
**R** (the `hasattr` guard ⇔ `deferred_save_ready`), and an **A-consumed** call
to an UNCHANGED callee (`save_m2m` == `_save_m2m`, A6). No callee under change is
axiomatized: `_save_m2m` and `BaseModelForm.save` and `Model.save` are all
unchanged framework callees; the change is purely that `UserCreationForm.save`
now *calls* the deferred relational save. The one **A-reference** symbol is the
abstract capability predicate `relations_done` (mapping.md §3.4): it is not a
consumed axiom over a repo callee but the directive-8 / control-flow grounding
device that ties the relational-data fact to the effect-producing step so it
cannot be fabricated by fiat or laundered across forms; its single real-world
claim (relations unwritten before `save_m2m`, written by it) is validated == the
real callees' behaviour by axiom_check.py (G-AX). The three consumed axioms are
likewise validated against their real callees by axiom_check.py. The
`MustTerminate` obligations are not impl operations at all — they are the
termination side-condition of the single modeled function (and the matching
side-condition on its callees), refining to "these operations terminate," which
the real callees do (axiom_check.py runs each to completion). There is no
kind-3 (unexpressible-changed-op) step.

## E. verify(model) ⇒ resolved

`save_form` verifies only if, when `commit` is True, BOTH `get_record()`
(A4) and the capability `relations_done(self)` (A6) hold at return — the latter
obtainable only by invoking the deferred relational save on `self` after the
record write (the abstract per-form capability predicate makes A6 the sole
producer, unforgeable and non-transferable). By R (the carrier folding and the
`hasattr`⇔`deferred_save_ready`/`commit` identities) the verified routine equals
the gold patch on the tested input; by A-consumed (G-AX) the three real callees
meet their axioms — in particular `Model.save()` does NOT write the m2m data, so
the deferred save is genuinely required, and `save_m2m` writes exactly the
submitted associations. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and audited callees — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN
§1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
