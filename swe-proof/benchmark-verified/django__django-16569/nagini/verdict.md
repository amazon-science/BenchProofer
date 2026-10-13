# P2 adversarial audit — django__django-16569

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 11 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -174,9 +174,7 @@
         else:
             form.has_order_field = True
             form.aux_keys = form.aux_keys + PSeq(1)
-    if can_delete and (
-        can_delete_extra or (index is not None and index < initial_form_count)
-    ):
+    if can_delete and (can_delete_extra or index < initial_form_count):
         form.has_delete_field = True
         form.aux_keys = form.aux_keys + PSeq(2)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -166,17 +166,14 @@
     Ensures(form.aux_keys == placed_keys(form.has_order_field, form.has_delete_field))
     # post-conditions-end
     # impl-start
-    if can_order:
-        if index is not None and index < initial_form_count:
-            form.has_order_field = True
-            form.order_field_prefilled = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-        else:
-            form.has_order_field = True
-            form.aux_keys = form.aux_keys + PSeq(1)
     if can_delete and (
         can_delete_extra or (index is not None and index < initial_form_count)
     ):
         form.has_delete_field = True
         form.aux_keys = form.aux_keys + PSeq(2)
+    if can_order:
+        form.has_order_field = True
+        if index is not None and index < initial_form_count:
+            form.order_field_prefilled = True
+        form.aux_keys = form.aux_keys + PSeq(1)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,7 +175,8 @@
             form.has_order_field = True
             form.aux_keys = form.aux_keys + PSeq(1)
     if can_delete and (
-        can_delete_extra or (index is not None and index < initial_form_count)
+        can_delete_extra
+        or (index is not None and initial_form_count > 0 and index < initial_form_count)
     ):
         form.has_delete_field = True
         form.aux_keys = form.aux_keys + PSeq(2)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,7 +175,7 @@
             form.has_order_field = True
             form.aux_keys = form.aux_keys + PSeq(1)
     if can_delete and (
-        can_delete_extra or (index is not None and index < initial_form_count)
+        can_delete_extra or (index is not None and index <= initial_form_count)
     ):
         form.has_delete_field = True
         form.aux_keys = form.aux_keys + PSeq(2)
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -166,17 +166,10 @@
     Ensures(form.aux_keys == placed_keys(form.has_order_field, form.has_delete_field))
     # post-conditions-end
     # impl-start
-    if can_order:
-        if index is not None and index < initial_form_count:
-            form.has_order_field = True
-            form.order_field_prefilled = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-        else:
-            form.has_order_field = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-    if can_delete and (
-        can_delete_extra or (index is not None and index < initial_form_count)
-    ):
-        form.has_delete_field = True
-        form.aux_keys = form.aux_keys + PSeq(2)
+    form.has_order_field = can_order
+    form.order_field_prefilled = can_order and at_initial_position(index, initial_form_count)
+    form.has_delete_field = can_delete and (
+        can_delete_extra or at_initial_position(index, initial_form_count)
+    )
+    form.aux_keys = placed_keys(form.has_order_field, form.has_delete_field)
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -167,13 +167,9 @@
     # post-conditions-end
     # impl-start
     if can_order:
-        if index is not None and index < initial_form_count:
-            form.has_order_field = True
-            form.order_field_prefilled = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-        else:
-            form.has_order_field = True
-            form.aux_keys = form.aux_keys + PSeq(1)
+        form.has_order_field = True
+        form.order_field_prefilled = index is not None and index < initial_form_count
+        form.aux_keys = form.aux_keys + PSeq(1)
     if can_delete and (
         can_delete_extra or (index is not None and index < initial_form_count)
     ):
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -166,17 +166,6 @@
     Ensures(form.aux_keys == placed_keys(form.has_order_field, form.has_delete_field))
     # post-conditions-end
     # impl-start
-    if can_order:
-        if index is not None and index < initial_form_count:
-            form.has_order_field = True
-            form.order_field_prefilled = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-        else:
-            form.has_order_field = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-    if can_delete and (
-        can_delete_extra or (index is not None and index < initial_form_count)
-    ):
-        form.has_delete_field = True
-        form.aux_keys = form.aux_keys + PSeq(2)
+    configure_optional_fields(form, can_order, can_delete, can_delete_extra,
+                              index, initial_form_count)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,7 +175,7 @@
             form.has_order_field = True
             form.aux_keys = form.aux_keys + PSeq(1)
     if can_delete and (
-        can_delete_extra or (index is not None and index < initial_form_count)
+        can_delete_extra or index is None or index < initial_form_count
     ):
         form.has_delete_field = True
         form.aux_keys = form.aux_keys + PSeq(2)
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -178,5 +178,4 @@
         can_delete_extra or (index is not None and index < initial_form_count)
     ):
         form.has_delete_field = True
-        form.aux_keys = form.aux_keys + PSeq(2)
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -166,17 +166,11 @@
     Ensures(form.aux_keys == placed_keys(form.has_order_field, form.has_delete_field))
     # post-conditions-end
     # impl-start
-    if can_order:
-        if index is not None and index < initial_form_count:
-            form.has_order_field = True
-            form.order_field_prefilled = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-        else:
-            form.has_order_field = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-    if can_delete and (
-        can_delete_extra or (index is not None and index < initial_form_count)
-    ):
-        form.has_delete_field = True
-        form.aux_keys = form.aux_keys + PSeq(2)
+    form.has_order_field = can_order
+    form.order_field_prefilled = can_order and at_initial_position(index, initial_form_count)
+    form.has_delete_field = can_delete and (
+        can_delete_extra or at_initial_position(index, initial_form_count)
+    )
+    form.aux_keys = placed_keys(form.has_order_field, form.has_delete_field)
+    raise Exception()
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -167,16 +167,12 @@
     # post-conditions-end
     # impl-start
     if can_order:
+        form.has_order_field = True
         if index is not None and index < initial_form_count:
-            form.has_order_field = True
             form.order_field_prefilled = True
-            form.aux_keys = form.aux_keys + PSeq(1)
-        else:
-            form.has_order_field = True
-            form.aux_keys = form.aux_keys + PSeq(1)
     if can_delete and (
         can_delete_extra or (index is not None and index < initial_form_count)
     ):
         form.has_delete_field = True
-        form.aux_keys = form.aux_keys + PSeq(2)
+    form.aux_keys = placed_keys(form.has_delete_field, form.has_order_field)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16569.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A hook augments a single form with two optional auxiliary fields, governed by
  three boolean configuration flags and a per-form position. The position is
  OPTIONAL: a form rendered as a standalone blank template has no position
  (it is absent / ``None``), and the hook must behave gracefully in that case
  rather than failing.

  Two independent decisions are made, each recording only whether the
  corresponding auxiliary field becomes present on the form:

    (1) The ORDERING field is present iff ordering is enabled; its initial
        value is pre-filled ONLY for a form that occupies an initial position
        (one that HAS a position below the initial-form count), and is left
        blank otherwise.

    (2) The DELETION field is present iff deletion is enabled AND either extra
        (non-initial) forms are also allowed a deletion control, OR the form
        occupies one of the initial positions. A form occupies an initial
        position only when it HAS a position at all (a positionless form does
        not) and that position lies below the initial-form count.

  Equivalently, in both decisions the "is this an initial-position form?"
  predicate is FALSE for a positionless form: a present position below the
  initial count, and never for an absent position. The deletion decision must
  honour this just as the ordering decision does, so a positionless form with
  deletion enabled but extra-deletion disabled receives NO deletion field
  (and the hook does not fail).

  (3) A form's fields are an ORDERED collection, and the placement order is
      observable: it is the order in which the form renders its controls. The
      two auxiliary controls have an INVARIANT relative placement — the ordering
      control is placed on the form AHEAD of the deletion control — so a form
      granted both renders its ordering control first and its deletion control
      immediately after. Only the controls that the decisions above make
      present are placed at all, and the hook places nothing else.

The form is modeled as a minimal mutable object exposing the booleans the hook
writes (whether each auxiliary key is present, and whether the ordering key
carries a pre-filled initial value) together with the SEQUENCE of auxiliary
keys it has placed, in placement order (the ordering key is token 1, the
deletion key is token 2). The configuration flags and the initial-form count
are read-only scalars; the position is an ``Optional[int]``.

The hook is a bounded, loop-free prologue over scalars and MUST terminate (a
total-correctness obligation, carried as ``MustTerminate`` in the
precondition). Nagini is a partial-correctness verifier by default, so without
this obligation a non-terminating implementation (e.g. bare self-recursion)
satisfies every ``Ensures`` vacuously; the real hook always returns its
augmented form.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Form:
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.has_order_field) and self.has_order_field == False)  # type: ignore
        Ensures(Acc(self.order_field_prefilled) and self.order_field_prefilled == False)  # type: ignore
        Ensures(Acc(self.has_delete_field) and self.has_delete_field == False)  # type: ignore
        Ensures(Acc(self.aux_keys) and self.aux_keys == empty_key_sequence())  # type: ignore
        self.has_order_field = False  # type: bool
        self.order_field_prefilled = False  # type: bool
        self.has_delete_field = False  # type: bool
        self.aux_keys = empty_key_sequence()  # type: PSeq[int]

# axioms-start
# No consumed axioms. The changed operation is pure control flow over scalars
# (a None-guard added to an integer comparison inside a boolean disjunction),
# modeled deeply and exactly. The constructed field/widget objects and the
# initial-form count are unchanged by this behaviour and are abstracted to the
# presence of each auxiliary key plus the order in which the keys are placed;
# their real semantics are validated out-of-band by axiom_check.py (G-AX) as
# A-reference, not consumed here.
# axioms-end

# pure-start
@Pure
def at_initial_position(index: Optional[int], initial_form_count: int) -> bool:
    """Whether a form occupies an initial position: it must HAVE a position
    (a positionless form does not qualify) and that position lies below the
    initial-form count. This is exactly the predicate the ordering decision
    already uses; the deletion decision must honour it identically."""
    return index is not None and index < initial_form_count

@Pure
def empty_key_sequence() -> PSeq[int]:
    """A form that has been granted no auxiliary control at all: the empty
    placement sequence."""
    return PSeq(1).take(0)

@Pure
def placed_keys(has_order_field: bool, has_delete_field: bool) -> PSeq[int]:
    """The auxiliary keys a form carries, in the order they are placed on it.
    The ordering key (token 1) is always placed AHEAD of the deletion key
    (token 2); a control the decisions leave absent contributes nothing, and
    nothing else is ever placed. So a form granted both carries exactly
    ``PSeq(1, 2)`` — never ``PSeq(2, 1)`` — and one granted a single control
    carries just that control's key."""
    return ((PSeq(1) if has_order_field else empty_key_sequence())
            + (PSeq(2) if has_delete_field else empty_key_sequence()))
# pure-end

def configure_optional_fields(
    form: Form,
    can_order: bool,
    can_delete: bool,
    can_delete_extra: bool,
    index: Optional[int],
    initial_form_count: int,
) -> None:
    # pre-conditions-start
    # The form is the only mutated object: full permission to its flags.
    Requires(Acc(form.has_order_field) and Acc(form.order_field_prefilled) and Acc(form.has_delete_field))
    Requires(Acc(form.aux_keys))
    # The hook runs on a freshly built form: neither auxiliary field is present
    # yet and nothing has been placed. The hook only ever ADDS a field; it never
    # removes one.
    Requires(form.has_order_field == False and form.order_field_prefilled == False and form.has_delete_field == False)
    Requires(form.aux_keys == empty_key_sequence())
    # The initial-form count is a non-negative form-count (read-only scalar).
    Requires(initial_form_count >= 0)
    # TERMINATION: the hook must actually ANSWER (return the augmented form) —
    # it is a bounded, loop-free prologue over scalars, so every call
    # completes. Nagini checks partial correctness by default, so without this
    # obligation a non-terminating implementation (e.g. bare self-recursion of
    # this very routine, which discharges every Ensures vacuously) would be
    # accepted despite never delivering an answer. The measure (2) strictly
    # exceeds the Form() constructor's (1), so bounded construction stays
    # admitted but a self-call is rejected (no strictly smaller measure is
    # available).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(form.has_order_field) and Acc(form.order_field_prefilled) and Acc(form.has_delete_field))
    Ensures(Acc(form.aux_keys))
    # (1) The ordering field is present iff ordering is enabled; its initial
    # value is pre-filled only for an initial-position form (and only then).
    Ensures(form.has_order_field == can_order)
    Ensures(form.order_field_prefilled
            == (can_order and at_initial_position(index, initial_form_count)))
    # (2) The deletion field is present iff deletion is enabled AND (extra-form
    # deletion is allowed OR the form occupies an initial position). The
    # initial-position predicate is FALSE for a positionless form, so a
    # positionless form with deletion enabled and extra-deletion disabled
    # receives NO deletion field.
    Ensures(
        form.has_delete_field
        == (can_delete and (can_delete_extra or at_initial_position(index, initial_form_count)))
    )
    # (3) PLACEMENT ORDER. The form carries exactly the auxiliary keys the two
    # decisions grant it, and it carries them in the one placement order the
    # form's rendering exposes: the ordering control ahead of the deletion
    # control. A form granted both therefore renders Order before Delete.
    Ensures(form.aux_keys == placed_keys(form.has_order_field, form.has_delete_field))
    # post-conditions-end
    # impl-start
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Every attack built by copying the bundle model.py and editing ONLY the impl region (model.py lines 168-182); axioms/@Pure at_initial_position/empty_key_sequence/placed_keys/Requires/Ensures kept byte-identical. All 11 attacks + positive control confirmed `same-spec` exit 0. Command template: `python -m swebench_unified.adversary weakness nagini django__django-16569 <atk>`; run 3-at-a-time as background jobs. Positive control: `bash scripts/nagini_verify.sh pos_control.py` -> Verification successful, 15.66s, exit 0.

### PER-ATTACK RESULTS (11 distinct classes; 9 rejected, 2 CANDIDATEs, both resolve):
- atk_1.py PREPATCH BUG (unguarded `can_delete and (can_delete_extra or index < initial_form_count)`) -> NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Nagini cannot discharge `<` on Optional[int]. => PREPATCH REPRODUCED.
- atk_2.py CONTROL-FLOW-EFFECT (correct guarded decisions, but DELETE key placed AHEAD of ORDER key: aux_keys = PSeq(2)+PSeq(1)) -> does not verify (exit 2). Clause-3 (placement order) is load-bearing. FAITHFULNESS PROBE: I materialized its faithful patch anyway (work/patch_atk_2.diff, delete-block hoisted above the order block in the real add_fields) and ran run_resolve => RESOLVED=False, P2P failure ['FormSets with ordering + deletion.'] (F2P failures []). So the clause the spec uses to reject this impl corresponds to a REAL test-observable behaviour — the clause is grounded, not over-strong. This is the key A-leg check, since clause 3 is undocumented in refinement.md (see AUDIT below).
- atk_3.py PARTIAL-DOMAIN (extra `initial_form_count > 0` conjunct inside the delete guard; differs from gold only at a negative index) -> does not verify (exit 2). The postcondition pins the decision over the WHOLE input domain incl. index<0, so a partial-domain impl cannot verify even where the difference is repo-unreachable.
- atk_4.py BOUNDARY (off-by-one `index <= initial_form_count` in the delete guard) -> does not verify (exit 2).
- atk_5.py UNGROUNDED-ORACLE ECHO (no control flow at all: reads the three postconditions back through the frozen pure helpers at_initial_position/placed_keys) -> CANDIDATE, verifies 19.6s (exit 0). MATERIALIZED faithful patch work/patch_atk_5.diff (add_fields recomputed as at_initial_position/has_order_field/order_field_prefilled/has_delete_field locals, ORDER built once with initial=index+1 if prefilled else None, then DELETE) and EXECUTED run_resolve('django__django-16569', patch, timeout=1800) => RESOLVED=True; F2P both test_disable_delete_extra_formset_forms (Forms + Jinja2) success, all 111 P2P success, 0 failures. A resolving echo is not a weakness (unified G-EQ/G-PANEL-1 policy).
- atk_6.py COLLAPSED ORDERING ARMS (the unchanged two-arm ordering if/else fused into one placement whose prefill is a computed bool) -> CANDIDATE, verifies 14.6s (exit 0). MATERIALIZED faithful patch work/patch_atk_6.diff (single IntegerField construction with initial=(index+1) if prefill else None; gold guarded delete decision) and EXECUTED run_resolve => RESOLVED=True; F2P 2/2 success, 111/111 P2P success, 0 failures. Confirms the abstraction's order_field_prefilled carrier is faithful: `initial=None` is observationally identical to omitting `initial` in the real IntegerField (test_formset_with_ordering_and_deletion / 'Ordering works with blank fieldsets.' / test_formsets_with_ordering_custom_widget all still pass).
- atk_7.py VACUITY / NON-TERMINATION (bare self-recursion; every Ensures discharged from the recursive call's own contract) -> does not verify (exit 2). MustTerminate(2) obligation-leak closes the vacuity hole.
- atk_8.py SEMANTIC PREPATCH, TYPE-SAFE (`can_delete_extra or index is None or index < initial_form_count`: reproduces the BUG's observable behaviour — a positionless form DOES get DELETE — while avoiding any None-comparison, so it cannot be rejected merely on typing) -> does not verify (exit 2). This is the sharpest of the set: the spec rejects the bug BEHAVIOURALLY, not just via Optional typing.
- atk_9.py PRESENT-BUT-UNPLACED (correct presence booleans; deletion key never appended to aux_keys) -> does not verify (exit 2).
- atk_10.py FAILING HOOK (all three decisions correct, then `raise Exception()` instead of answering — the formal image of the real TypeError) -> does not verify (exit 2).
- atk_11.py CLAUSE-3 ARG SWAP (`placed_keys(has_delete_field, has_order_field)` — carriers transposed) -> does not verify (exit 2).

AUDIT of refinement.md legs (A-legs focus). Leg inventory: steps 1-4 R (formset bool flags / Optional[int] position / non-negative initial_form_count captured once at line 477 -> read-only scalars); step 5 I (the literal gold guard `index is not None and index < initial_form_count`, char-for-char — verified against `git show 278881e...:django/forms/formsets.py` line 493 and patch.diff); steps 6-7 I (identical boolean disjunction/conjunction); step 8 R (DELETION_FIELD_NAME dict-key presence -> bool); ordering branch I/R with order_field_prefilled modelling the sole observable difference (initial=index+1) between the two unchanged arms.

NO @ContractOnly axioms exist, so there are NO A-consumed legs and NO kind-3 legs; the single A-reference leg is axiom_check.py (G-AX), which drives the REAL django.forms.formsets.BaseFormSet across can_order x can_delete x can_delete_extra in {T,F}^3 x initial_form_count in {0,1,2,3} x index in {None, 0..initial+2}, asserting DELETION presence == the model decision, ORDERING presence == can_order, ORDERING.initial is not None == order_field_prefilled, plus the pre-patch TypeError differential and the issue's empty_form reproducer. I re-read the real callee at base_commit and the post-gold source: the A-reference correspondence HOLDS (the abstraction's three carriers are exactly what the F2P `assertNotIn('DELETE', formset.forms[i].fields)` and the ordering P2P HTML assertions observe).

DOCUMENTATION DEFECT (advisory, NOT a G-EQ break): model.py carries a THIRD spec clause — `form.aux_keys == placed_keys(has_order_field, has_delete_field)` with the pure helpers empty_key_sequence/placed_keys (spec docstring item (3), placement order ORDER-before-DELETE) — and refinement.md (dated Aug 9) / mapping.md (Aug 13) / axiom_check.py (Aug 5) all PREDATE model.py (Aug 14) and contain ZERO occurrences of aux_keys / placed_keys / 'placement'. So this clause has NO refinement leg (no R/A/I row) and no G-AX coverage. Refinement-fidelity risk assessed empirically rather than assumed: because the clause is a STRENGTHENING (it rejects impls), the failure mode would be over-strongness — a spec-rejected impl whose faithful patch nonetheless resolves.

I tested exactly that with atk_2's materialized patch and got RESOLVED=False with the P2P 'FormSets with ordering + deletion.' failure, i.e. the real Django field-insertion order into form.fields IS observable (rendered ORDER-then-DELETE in the as_ul assertions) and the clause faithfully reflects it. Clause 3 is therefore SOUND but UNDOCUMENTED: refinement.md should gain an R leg (ORDER/DELETE insertion order into the ordered form.fields dict -> PSeq[int] placement token sequence, tokens 1/2) and axiom_check.py should ideally assert list(form.fields).index(ORDERING) < index(DELETION) on the real object. Recommend a doc/G-AX top-up; it does not admit a non-resolving impl, so G-EQ does not break on it.

VERDICT SOUND: 11 distinct same-spec attacks encoded and fully run (>=5 required), spanning partial-domain (atk_3), boundary (atk_4), control-flow-effect (atk_2, atk_9, atk_11), ungrounded-oracle echo (atk_5, atk_6), vacuity/non-termination (atk_7), failing-hook (atk_10), and both the typing-level (atk_1) and behavioural (atk_8) prepatch bug. Prepatch reproduced and rejected. Both CANDIDATEs had their faithful refined patches MATERIALIZED and EXECUTED through the official harness (run_resolve) and both RESOLVED=True — no verifying wrong impl exists, so verify => correct holds on this bundle. Zero timeouts, zero infra caps hit; every needed resolve run completed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 11 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16569.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A hook augments a single form with two optional auxiliary fields, governed by
  three boolean configuration flags and a per-form position. The position is
  OPTIONAL: a form rendered as a standalone blank template has no position
  (it is absent / ``None``), and the hook must behave gracefully in that case
  rather than failing.

  Two independent decisions are made, each recording only whether the
  corresponding auxiliary field becomes present on the form:

    (1) The ORDERING field is present iff ordering is enabled; its initial
        value is pre-filled ONLY for a form that occupies an initial position
        (one that HAS a position below the initial-form count), and is left
        blank otherwise.

    (2) The DELETION field is present iff deletion is enabled AND either extra
        (non-initial) forms are also allowed a deletion control, OR the form
        occupies one of the initial positions. A form occupies an initial
        position only when it HAS a position at all (a positionless form does
        not) and that position lies below the initial-form count.

  Equivalently, in both decisions the "is this an initial-position form?"
  predicate is FALSE for a positionless form: a present position below the
  initial count, and never for an absent position. The deletion decision must
  honour this just as the ordering decision does, so a positionless form with
  deletion enabled but extra-deletion disabled receives NO deletion field
  (and the hook does not fail).

  (3) A form's fields are an ORDERED collection, and the placement order is
      observable: it is the order in which the form renders its controls. The
      two auxiliary controls have an INVARIANT relative placement — the ordering
      control is placed on the form AHEAD of the deletion control — so a form
      granted both renders its ordering control first and its deletion control
      immediately after. Only the controls that the decisions above make
      present are placed at all, and the hook places nothing else.

The form is modeled as a minimal mutable object exposing the booleans the hook
writes (whether each auxiliary key is present, and whether the ordering key
carries a pre-filled initial value) together with the SEQUENCE of auxiliary
keys it has placed, in placement order (the ordering key is token 1, the
deletion key is token 2). The configuration flags and the initial-form count
are read-only scalars; the position is an ``Optional[int]``.

The hook is a bounded, loop-free prologue over scalars and MUST terminate (a
total-correctness obligation, carried as ``MustTerminate`` in the
precondition). Nagini is a partial-correctness verifier by default, so without
this obligation a non-terminating implementation (e.g. bare self-recursion)
satisfies every ``Ensures`` vacuously; the real hook always returns its
augmented form.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Form:
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.has_order_field) and self.has_order_field == False)  # type: ignore
        Ensures(Acc(self.order_field_prefilled) and self.order_field_prefilled == False)  # type: ignore
        Ensures(Acc(self.has_delete_field) and self.has_delete_field == False)  # type: ignore
        Ensures(Acc(self.aux_keys) and self.aux_keys == empty_key_sequence())  # type: ignore
        self.has_order_field = False  # type: bool
        self.order_field_prefilled = False  # type: bool
        self.has_delete_field = False  # type: bool
        self.aux_keys = empty_key_sequence()  # type: PSeq[int]

# axioms-start
# No consumed axioms. The changed operation is pure control flow over scalars
# (a None-guard added to an integer comparison inside a boolean disjunction),
# modeled deeply and exactly. The constructed field/widget objects and the
# initial-form count are unchanged by this behaviour and are abstracted to the
# presence of each auxiliary key plus the order in which the keys are placed;
# their real semantics are validated out-of-band by axiom_check.py (G-AX) as
# A-reference, not consumed here.
# axioms-end

# pure-start
@Pure
def at_initial_position(index: Optional[int], initial_form_count: int) -> bool:
    """Whether a form occupies an initial position: it must HAVE a position
    (a positionless form does not qualify) and that position lies below the
    initial-form count. This is exactly the predicate the ordering decision
    already uses; the deletion decision must honour it identically."""
    return index is not None and index < initial_form_count

@Pure
def empty_key_sequence() -> PSeq[int]:
    """A form that has been granted no auxiliary control at all: the empty
    placement sequence."""
    return PSeq(1).take(0)

@Pure
def placed_keys(has_order_field: bool, has_delete_field: bool) -> PSeq[int]:
    """The auxiliary keys a form carries, in the order they are placed on it.
    The ordering key (token 1) is always placed AHEAD of the deletion key
    (token 2); a control the decisions leave absent contributes nothing, and
    nothing else is ever placed. So a form granted both carries exactly
    ``PSeq(1, 2)`` — never ``PSeq(2, 1)`` — and one granted a single control
    carries just that control's key."""
    return ((PSeq(1) if has_order_field else empty_key_sequence())
            + (PSeq(2) if has_delete_field else empty_key_sequence()))
# pure-end

def configure_optional_fields(
    form: Form,
    can_order: bool,
    can_delete: bool,
    can_delete_extra: bool,
    index: Optional[int],
    initial_form_count: int,
) -> None:
    # pre-conditions-start
    # The form is the only mutated object: full permission to its flags.
    Requires(Acc(form.has_order_field) and Acc(form.order_field_prefilled) and Acc(form.has_delete_field))
    Requires(Acc(form.aux_keys))
    # The hook runs on a freshly built form: neither auxiliary field is present
    # yet and nothing has been placed. The hook only ever ADDS a field; it never
    # removes one.
    Requires(form.has_order_field == False and form.order_field_prefilled == False and form.has_delete_field == False)
    Requires(form.aux_keys == empty_key_sequence())
    # The initial-form count is a non-negative form-count (read-only scalar).
    Requires(initial_form_count >= 0)
    # TERMINATION: the hook must actually ANSWER (return the augmented form) —
    # it is a bounded, loop-free prologue over scalars, so every call
    # completes. Nagini checks partial correctness by default, so without this
    # obligation a non-terminating implementation (e.g. bare self-recursion of
    # this very routine, which discharges every Ensures vacuously) would be
    # accepted despite never delivering an answer. The measure (2) strictly
    # exceeds the Form() constructor's (1), so bounded construction stays
    # admitted but a self-call is rejected (no strictly smaller measure is
    # available).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(form.has_order_field) and Acc(form.order_field_prefilled) and Acc(form.has_delete_field))
    Ensures(Acc(form.aux_keys))
    # (1) The ordering field is present iff ordering is enabled; its initial
    # value is pre-filled only for an initial-position form (and only then).
    Ensures(form.has_order_field == can_order)
    Ensures(form.order_field_prefilled
            == (can_order and at_initial_position(index, initial_form_count)))
    # (2) The deletion field is present iff deletion is enabled AND (extra-form
    # deletion is allowed OR the form occupies an initial position). The
    # initial-position predicate is FALSE for a positionless form, so a
    # positionless form with deletion enabled and extra-deletion disabled
    # receives NO deletion field.
    Ensures(
        form.has_delete_field
        == (can_delete and (can_delete_extra or at_initial_position(index, initial_form_count)))
    )
    # (3) PLACEMENT ORDER. The form carries exactly the auxiliary keys the two
    # decisions grant it, and it carries them in the one placement order the
    # form's rendering exposes: the ordering control ahead of the deletion
    # control. A form granted both therefore renders Order before Delete.
    Ensures(form.aux_keys == placed_keys(form.has_order_field, form.has_delete_field))
    # post-conditions-end
    # impl-start
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Every attack built by copying the bundle model.py and editing ONLY the impl region (model.py lines 168-182); axioms/@Pure at_initial_position/empty_key_sequence/placed_keys/Requires/Ensures kept byte-identical. All 11 attacks + positive control confirmed `same-spec` exit 0. Command template: `python -m swebench_unified.adversary weakness nagini django__django-16569 <atk>`; run 3-at-a-time as background jobs. Positive control: `bash scripts/nagini_verify.sh pos_control.py` -> Verification successful, 15.66s, exit 0.

### PER-ATTACK RESULTS (11 distinct classes; 9 rejected, 2 CANDIDATEs, both resolve):
- atk_1.py PREPATCH BUG (unguarded `can_delete and (can_delete_extra or index < initial_form_count)`) -> NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Nagini cannot discharge `<` on Optional[int]. => PREPATCH REPRODUCED.
- atk_2.py CONTROL-FLOW-EFFECT (correct guarded decisions, but DELETE key placed AHEAD of ORDER key: aux_keys = PSeq(2)+PSeq(1)) -> does not verify (exit 2). Clause-3 (placement order) is load-bearing. FAITHFULNESS PROBE: I materialized its faithful patch anyway (work/patch_atk_2.diff, delete-block hoisted above the order block in the real add_fields) and ran run_resolve => RESOLVED=False, P2P failure ['FormSets with ordering + deletion.'] (F2P failures []). So the clause the spec uses to reject this impl corresponds to a REAL test-observable behaviour — the clause is grounded, not over-strong. This is the key A-leg check, since clause 3 is undocumented in refinement.md (see AUDIT below).
- atk_3.py PARTIAL-DOMAIN (extra `initial_form_count > 0` conjunct inside the delete guard; differs from gold only at a negative index) -> does not verify (exit 2). The postcondition pins the decision over the WHOLE input domain incl. index<0, so a partial-domain impl cannot verify even where the difference is repo-unreachable.
- atk_4.py BOUNDARY (off-by-one `index <= initial_form_count` in the delete guard) -> does not verify (exit 2).
- atk_5.py UNGROUNDED-ORACLE ECHO (no control flow at all: reads the three postconditions back through the frozen pure helpers at_initial_position/placed_keys) -> CANDIDATE, verifies 19.6s (exit 0). MATERIALIZED faithful patch work/patch_atk_5.diff (add_fields recomputed as at_initial_position/has_order_field/order_field_prefilled/has_delete_field locals, ORDER built once with initial=index+1 if prefilled else None, then DELETE) and EXECUTED run_resolve('django__django-16569', patch, timeout=1800) => RESOLVED=True; F2P both test_disable_delete_extra_formset_forms (Forms + Jinja2) success, all 111 P2P success, 0 failures. A resolving echo is not a weakness (unified G-EQ/G-PANEL-1 policy).
- atk_6.py COLLAPSED ORDERING ARMS (the unchanged two-arm ordering if/else fused into one placement whose prefill is a computed bool) -> CANDIDATE, verifies 14.6s (exit 0). MATERIALIZED faithful patch work/patch_atk_6.diff (single IntegerField construction with initial=(index+1) if prefill else None; gold guarded delete decision) and EXECUTED run_resolve => RESOLVED=True; F2P 2/2 success, 111/111 P2P success, 0 failures. Confirms the abstraction's order_field_prefilled carrier is faithful: `initial=None` is observationally identical to omitting `initial` in the real IntegerField (test_formset_with_ordering_and_deletion / 'Ordering works with blank fieldsets.' / test_formsets_with_ordering_custom_widget all still pass).
- atk_7.py VACUITY / NON-TERMINATION (bare self-recursion; every Ensures discharged from the recursive call's own contract) -> does not verify (exit 2). MustTerminate(2) obligation-leak closes the vacuity hole.
- atk_8.py SEMANTIC PREPATCH, TYPE-SAFE (`can_delete_extra or index is None or index < initial_form_count`: reproduces the BUG's observable behaviour — a positionless form DOES get DELETE — while avoiding any None-comparison, so it cannot be rejected merely on typing) -> does not verify (exit 2). This is the sharpest of the set: the spec rejects the bug BEHAVIOURALLY, not just via Optional typing.
- atk_9.py PRESENT-BUT-UNPLACED (correct presence booleans; deletion key never appended to aux_keys) -> does not verify (exit 2).
- atk_10.py FAILING HOOK (all three decisions correct, then `raise Exception()` instead of answering — the formal image of the real TypeError) -> does not verify (exit 2).
- atk_11.py CLAUSE-3 ARG SWAP (`placed_keys(has_delete_field, has_order_field)` — carriers transposed) -> does not verify (exit 2).

AUDIT of refinement.md legs (A-legs focus). Leg inventory: steps 1-4 R (formset bool flags / Optional[int] position / non-negative initial_form_count captured once at line 477 -> read-only scalars); step 5 I (the literal gold guard `index is not None and index < initial_form_count`, char-for-char — verified against `git show 278881e...:django/forms/formsets.py` line 493 and patch.diff); steps 6-7 I (identical boolean disjunction/conjunction); step 8 R (DELETION_FIELD_NAME dict-key presence -> bool); ordering branch I/R with order_field_prefilled modelling the sole observable difference (initial=index+1) between the two unchanged arms.

NO @ContractOnly axioms exist, so there are NO A-consumed legs and NO kind-3 legs; the single A-reference leg is axiom_check.py (G-AX), which drives the REAL django.forms.formsets.BaseFormSet across can_order x can_delete x can_delete_extra in {T,F}^3 x initial_form_count in {0,1,2,3} x index in {None, 0..initial+2}, asserting DELETION presence == the model decision, ORDERING presence == can_order, ORDERING.initial is not None == order_field_prefilled, plus the pre-patch TypeError differential and the issue's empty_form reproducer. I re-read the real callee at base_commit and the post-gold source: the A-reference correspondence HOLDS (the abstraction's three carriers are exactly what the F2P `assertNotIn('DELETE', formset.forms[i].fields)` and the ordering P2P HTML assertions observe).

DOCUMENTATION DEFECT (advisory, NOT a G-EQ break): model.py carries a THIRD spec clause — `form.aux_keys == placed_keys(has_order_field, has_delete_field)` with the pure helpers empty_key_sequence/placed_keys (spec docstring item (3), placement order ORDER-before-DELETE) — and refinement.md (dated Aug 9) / mapping.md (Aug 13) / axiom_check.py (Aug 5) all PREDATE model.py (Aug 14) and contain ZERO occurrences of aux_keys / placed_keys / 'placement'. So this clause has NO refinement leg (no R/A/I row) and no G-AX coverage. Refinement-fidelity risk assessed empirically rather than assumed: because the clause is a STRENGTHENING (it rejects impls), the failure mode would be over-strongness — a spec-rejected impl whose faithful patch nonetheless resolves.

I tested exactly that with atk_2's materialized patch and got RESOLVED=False with the P2P 'FormSets with ordering + deletion.' failure, i.e. the real Django field-insertion order into form.fields IS observable (rendered ORDER-then-DELETE in the as_ul assertions) and the clause faithfully reflects it. Clause 3 is therefore SOUND but UNDOCUMENTED: refinement.md should gain an R leg (ORDER/DELETE insertion order into the ordered form.fields dict -> PSeq[int] placement token sequence, tokens 1/2) and axiom_check.py should ideally assert list(form.fields).index(ORDERING) < index(DELETION) on the real object. Recommend a doc/G-AX top-up; it does not admit a non-resolving impl, so G-EQ does not break on it.

VERDICT SOUND: 11 distinct same-spec attacks encoded and fully run (>=5 required), spanning partial-domain (atk_3), boundary (atk_4), control-flow-effect (atk_2, atk_9, atk_11), ungrounded-oracle echo (atk_5, atk_6), vacuity/non-termination (atk_7), failing-hook (atk_10), and both the typing-level (atk_1) and behavioural (atk_8) prepatch bug. Prepatch reproduced and rejected. Both CANDIDATEs had their faithful refined patches MATERIALIZED and EXECUTED through the official harness (run_resolve) and both RESOLVED=True — no verifying wrong impl exists, so verify => correct holds on this bundle. Zero timeouts, zero infra caps hit; every needed resolve run completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: configure_optional_fields <-> django.forms.formsets.BaseFormSet.add_fields (django/forms/formsets.py:474-497 at base_commit 278881e376). Spec exposes four observables: has_order_field == can_order; order_field_prefilled == (can_order and at_initial_position(index,n)); has_delete_field == (can_delete and (can_delete_extra or at_initial_position(index,n))); aux_keys == placed_keys(has_order_field, has_delete_field) = ordering token 1 ahead of deletion token 2. at_initial_position(index,n) := index is not None and index < n.

METHOD. Fresh git worktree of django/django at base_commit under /tmp, gold patch.diff applied so the oracle is the REAL post-gold callee. Bridge per mapping.md §2: ORDERING_FIELD_NAME presence -> has_order_field; that field's .initial is not None -> order_field_prefilled; DELETION_FIELD_NAME presence -> has_delete_field; iteration order of the two aux keys in form.fields -> aux_keys. Counts driven HONESTLY through real Django (unbound: len(initial); bound: INITIAL_FORMS in POST data) rather than monkeypatching initial_form_count, so the oracle path is the production one.

RESULTS — 0 divergences everywhere.

(1) Boundary block: can_order x can_delete x can_delete_extra in {T,F}^3, n in {0,1,2,3,5}, index in {None,-1000,-3,-1,0..n+2,1e6,1e30} = 448 cases: 0 mismatches, no TypeError.

(2) RENDERED placement order (clause 3 as the spec justifies it — 'the order in which the form renders its controls'): parsed str(form) HTML and compared the positions of name="ORDER" / name="DELETE"; ORDER precedes DELETE in every case a form is granted both. 0 mismatches. Note the spec's PSeq claim is not vacuous and not merely a dict-insertion artifact — it holds in the rendered output too.

(3) BOUND formset path (initial_form_count() from management-form cleaned_data, a code path the unbound-only harnesses in the bundle do not exercise): 264 cases, 0 mismatches.

(4) Mixed 150,000-case seeded fuzz (seed 16569) alternating bound/unbound, n in [-4,25], index in {None} u [-8,30]: 0 mismatches.

(5) F2P reproducer: empty_form of a can_delete=True/can_delete_extra=False formset carries no DELETE — matches the spec's required-absent.

(6) Reachability of the None carrier confirmed by spying on the real add_fields: callers pass exactly {None, 0, 1, 2, 3}; None comes from empty_form (line 267 self.add_fields(form, None)), so the Optional[int] carrier is faithful, not invented.

### OVER-STRENGTH PROBES (each returned a domain restriction, not a divergence):
- Requires(initial_form_count >= 0). I showed negative counts ARE reachable in reality: a bound formset with POST form-INITIAL_FORMS=-5 yields initial_form_count() == -5 (no clamping). So the precondition does exclude reachable real states. However this is a harmless domain narrowing, not unfaithfulness: I ran the full flag cross product x index in {None,-10,-6,-5,-4,-1,0,1,5} at n=-5 and the spec's own formula still agrees with the real callee on all of them (0 mismatches). The spec therefore never claims anything false about real behaviour there; it merely declines to speak. No solver can exploit it and no gold behaviour is excluded.
- Requires(form.aux_keys == empty_key_sequence()) (fresh form). I found the one input where the placement-order clause would be WRONG if the precondition were dropped: a form class that pre-declares DELETE (class PreDeclared(forms.Form): DELETE = BooleanField()) with can_order and can_delete both set yields real placement seq (2,1) — DELETE before ORDER — while placed_keys(True,True) == (1,2). This is genuinely outside the modeled domain: both real call sites (empty_form line 266-267 and _construct_form) build a fresh self.form(**kwargs) immediately before add_fields, so a form arriving with an aux key already present is not a state add_fields is ever called in by the repo. The precondition is thus faithful to the callers, and the clause-3 postcondition is exactly right on the whole reachable domain.
- order_field_prefilled bridge: verified IntegerField(label='Order', required=False).initial is None in the else-arm, and that the index=-1,n=0 corner (initial=index+1==0, a falsy but non-None value) is handled correctly — real gives prefilled True and the spec's 'is not None' bridge agrees, i.e. the bridge does not silently use truthiness.
- MustTerminate(2): the real add_fields is loop-free straight-line scalar code and always returns, so the total-correctness obligation excludes no real behaviour.

CONTROLS. same-spec on the unmodified bundle model: exit 0 (SAME). Direct pinned verifier on model.py: 'Verification successful' in 16.4s. Regions byte-identical.

CONCLUSION: no diverging input exists on the reachable domain — the modeled function agrees with the real post-gold callee on every one of ~151,000 probes across unbound, bound, negative-count, boundary, and rendered-order dimensions. The spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SPEC VIEW AUDITED: regenerated mechanically via swebench_unified.markers.spec_view(model.py, nagini.language) -> spec_view.py. Elision integrity confirmed: idempotent (spec_view(spec_view(x))==spec_view(x)), ELISION_IMPL present, regions parse clean (axioms/pure/pre-conditions/post-conditions/impl), and no impl body fragment survives ('form.has_delete_field = True', 'form.aux_keys + PSeq(2)', 'if can_delete and (' all absent). same-spec on an identity copy exits 0, confirming the region I audited is the frozen spec region.

MECHANICAL SCREEN: swebench_unified.leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> PASSED, zero hard failures, zero warnings. No diff markers (L1), no gold line reproduced (L1), no patched file/module path 'django/forms/formsets.py' or dotted 'django.forms.formsets' (L2), no spec-view identifier or comment echoing a patched repo symbol (L2/L5), no narration vocabulary (L3).

DECISIVE POINT — THE PUBLIC BASELINE IS MAXIMAL. This instance's problem_statement is an unusually complete issue report. Verified programmatically that it already discloses, verbatim: the buggy line ('if self.can_delete and (self.can_delete_extra or index < initial_form_count):'), THE ENTIRE FIXED LINE including the guard ('if self.can_delete and (self.can_delete_extra or (index is not None and index < initial_form_count)):'), the file (django.forms.formsets), the line number (493), the symbol (add_fields), the exact trigger configuration (can_delete == True, can_delete_extra == False), the None-index call site (empty_form), and the exception (TypeError: '<' not supported between NoneType and int). The gold patch is therefore fully public BEFORE any spec is shown. Nothing in the spec view can leak 'beyond' this baseline with respect to the edit itself.

PER-CANDIDATE ADJUDICATION of spec-view content NOT in the problem statement:

(a) at_initial_position's body 'index is not None and index < initial_form_count' (spec_view line 92) — this is literally the gold guard and would be the leaking line under any weaker baseline, BUT the normalized expression is present verbatim in the problem_statement (verified: normalized token IS in normalized PS). The gate's stated rule judges leakage against the solver-visible problem_statement ONLY (never hints_text; hints_text is empty here anyway), so this is public, not leaked. This is the single most important call in the audit and it turns entirely on the unusual completeness of the public issue.

(b) 'can_order' / the ordering branch / order_field_prefilled (initial=index+1) — 'can_order' is NOT in the problem statement, but it is not part of the gold edit. Verified against the real base_commit source (checked out 278881e37619278789942513916acafaa88d26f3, django/forms/formsets.py:475-498): the ordering branch and its pre-existing 'if index is not None and index < initial_form_count' guard and 'initial=index+1' are UNCHANGED code that any solver reads for free when they open the file the issue names. Modeling pre-existing context localizes no edit. Not leakage.

(c) aux_keys / placed_keys / PSeq(1,2) placement order — additive spec with no counterpart in the gold patch, derived from the pre-existing body order (ORDERING inserted before DELETION). It does not point at the changed line. Not leakage.

(d) MustTerminate(2) and the accompanying vacuity/self-recursion commentary — verifier mechanics (partial- vs total-correctness), not fix content. Not leakage.

HIDDEN-TEST LEAKAGE: clean. F2P is test_disable_delete_extra_formset_forms; the test patch adds one line, assertNotIn("DELETE", formset.empty_form.fields). The spec view names no test file, test symbol, or parametrization id. The spec-view prose that mirrors the assertion ('a positionless form with deletion enabled but extra-deletion disabled receives NO deletion field') restates the configuration and correct outcome the problem_statement itself already specifies, so it discloses no test identity.

PRIVATE ARTIFACTS NOT SHIPPED: refinement.md and mapping.md DO contain the gold hunk verbatim (refinement.md lines 18-25 quote the -/+ diff; mapping.md line 139 quotes the pre-patch line), but these are bundle-private and never reach the consumer. Confirmed the consumer surface is only EvalTask{problem_statement, spec_view, modeled_functions, localization, changed_files} rendered by eval/prompts._spec_block, with adapter.spec_view() hard-guarding against exposing an unelided view, and eval/audit.py actively screening agent shell reads of /refinement.md and model_prepatch. No path ships them.

SCOPE CAVEAT for panel routing: items (b) and (c) mean the spec view specifies MORE than the gold patch changes (the ordering-arm prefill distinction and the Order-before-Delete placement sequence). That is a spec-strength / refinement-fidelity question for the G-EQ / over-specification lane — an over-strong spec can reject a behaviourally-equivalent rival patch — and I flag it for that attacker. It is NOT leakage and does not change this gate's verdict.

CONCLUSION: NO-LEAKAGE. No spec-view line discloses the gold edit beyond the public problem_statement. Verdict rests on a machine-checked screen plus a per-line adjudication grounded in the real base_commit source, not on the screen alone.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
