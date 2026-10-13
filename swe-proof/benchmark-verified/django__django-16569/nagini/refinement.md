# refinement.md — django__django-16569

Operation-by-operation correspondence between `model.py`'s implementation
(`configure_optional_fields`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof consumes an axiom's
`Ensures`), **A-reference** (a deep model is validated == the real callee by
`axiom_check.py` / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`
`278881e37619278789942513916acafaa88d26f3` and is the real correctness oracle,
G-RESOLVE).

## The changed site — `BaseFormSet.add_fields` (`django/forms/formsets.py:493`)

Gold hunk:
```
-        if self.can_delete and (self.can_delete_extra or index < initial_form_count):
+        if self.can_delete and (
+            self.can_delete_extra or (index is not None and index < initial_form_count)
+        ):
             form.fields[DELETION_FIELD_NAME] = BooleanField(...)
```

| # | model.py impl op (`configure_optional_fields`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `can_delete` param | `self.can_delete` | R | the formset bool flag is read-only and passed as a scalar; identical truth value (mapping.md §2). |
| 2 | `can_delete_extra` param | `self.can_delete_extra` | R | likewise; read-only bool scalar (mapping.md §2). |
| 3 | `index: Optional[int]` param | `index` (int or `None`) | R | the per-form position; `None` for a positionless form (the `empty_form` call site `add_fields(form, None)`). The `Optional[int]` carrier is the type that makes the bug visible. |
| 4 | `initial_form_count` param, `Requires(>= 0)` | `initial_form_count = self.initial_form_count()` (captured once at line 477) | R | the unchanged count of initial forms, a non-negative int read-only input (mapping.md §2). |
| 5 | `index is not None and index < initial_form_count` (the added None-guard, also factored into `at_initial_position`) | `index is not None and index < initial_form_count` | **I** | the literal new guarded comparison — the heart of the fix, character-for-character. |
| 6 | `can_delete_extra or (... step 5 ...)` | `self.can_delete_extra or (index is not None and index < initial_form_count)` | I | identical boolean disjunction. |
| 7 | `can_delete and (... step 6 ...)` | `self.can_delete and (...)` | I | identical boolean conjunction guarding the field insert. |
| 8 | `form.has_delete_field = True` (only when step 7 holds) | `form.fields[DELETION_FIELD_NAME] = BooleanField(...)` | R | the model abstracts "the deletion key becomes present on the form" to a boolean; the F2P test observes exactly `"DELETE" in / not in formset.empty_form.fields`. The `BooleanField(...)` construction is unchanged by the fix (mapping.md §2). |

The ordering branch (`if can_order:` … the `index is not None and index <
initial_form_count` guard at line 480) is reproduced in the impl exactly as it
stands at `base_commit` — it ALREADY contained the `index is not None` guard
before this change (it is `I`/`R` and unchanged). Both arms set the ordering key
present, so `has_order_field == can_order`; they differ only in the
`initial=index+1` widget argument present in the guarded arm. That single
observable difference is modeled by `order_field_prefilled` (True only in the
guarded arm), so the ordering comparison is load-bearing in the skeleton (its
mutation is observable) — `order_field_prefilled == (can_order and
at_initial_position(index, initial_form_count))`. The `IntegerField`/widget
construction itself is unchanged by this fix and abstracted to the key's
presence + the prefilled flag.

## The discriminating clause (G-DIFF)

The fix's content lives in step 5: guarding `index < initial_form_count` with
`index is not None`. `model_prepatch.py` reproduces the pre-patch delete branch
`can_delete and (can_delete_extra or index < initial_form_count)` — i.e. step 5
WITHOUT the None-guard. It **fails verification** at exactly that comparison:
Nagini cannot discharge the precondition of `index < initial_form_count` because
`index: Optional[int]` may be `None` (error: *"The precondition of (index <
initial_form_count) might not hold"* at the `index < initial_form_count`
sub-expression). This is the formal image of the real runtime fault
`TypeError: '<' not supported between instances of 'NoneType' and 'int'`. The
postcondition clause that pins the corrected behaviour is
`form.has_delete_field == (can_delete and (can_delete_extra or
at_initial_position(index, initial_form_count)))`, with
`at_initial_position(None, n) == False` — so for the bug configuration
(`can_delete`, `not can_delete_extra`, `index is None`) the deletion field is
required ABSENT, exactly what the F2P
`assertNotIn("DELETE", formset.empty_form.fields)` checks.

## No consumed axioms / no kind-3 steps

Every step above is R or I. There is no `@ContractOnly` axiom: the changed
operation is pure scalar control flow, modeled deeply and exactly (step 5). The
abstractions in steps 1–4 and 8 (formset flags / count → scalars, dict-key
presence → bool) are type refinements R whose Python semantics are validated
against the real `BaseFormSet.add_fields` out-of-band by `axiom_check.py` (G-AX,
**A-reference**): it asserts, across the full `can_order × can_delete ×
can_delete_extra × index∈{None,0..n}` cross product, that the real post-gold
`add_fields` makes `DELETION_FIELD_NAME` present iff the model decision holds
(and `ORDERING_FIELD_NAME` present iff `can_order`), and that the pre-patch
raises `TypeError` precisely on the positionless deletion configuration.

## Termination (total correctness)

The precondition additionally carries `Requires(MustTerminate(2))` (the `Form`
constructor carries the strictly smaller measure 1). Nagini is a
partial-correctness verifier by default, so without this obligation a
non-terminating implementation — e.g. a bare self-recursion of the contracted
routine, whose every `Ensures` is discharged vacuously by the recursive call's
own contract — verifies while its faithful real patch (an `add_fields` that
never returns) hangs the F2P/P2P suite and does NOT resolve. The real
`add_fields` is a loop-free, straight-line prologue over scalars and always
returns, so the obligation is faithful (it excludes no real behaviour). This
closes the vacuity hole the audit exhibited (its P1 witness verified under the
pre-fix, partial-correctness-only contract); `properties.py`
`uniq-selfrec-diverge` pins the rejection ("Obligation leak check failed.
Callee configure_optional_fields might not take all unsatisfied obligations
from the caller.").

## verify(model) ⇒ resolved

`configure_optional_fields` verifies only if it TERMINATES on every input
(`MustTerminate(2)`: the call actually answers) and `has_delete_field` equals
the guarded decision (postcondition), which forces the `index is not None` guard
(without it the impl does not even verify — the prepatch witnesses this). By the
R refinements (formset flags/count ↔ scalars, dict-key presence ↔ bool, all
validated by G-AX as A-reference) the verified decision equals the gold
`add_fields` deletion-field decision on every tested input; the gold patch
resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ) plus the A-reference behavioural check (G-AX); there is no axiom
soundness obligation since no axiom is consumed.
