# P2 adversarial audit — django__django-16950

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,8 @@
                     instance.key is Old(instance.key)))
     # post-conditions-end
     # impl-start
+    # PREPATCH: drops the (key_is_primary or not form_data_present) conjunct
     if adding:
-        if key_has_default and (key_is_primary or not form_data_present):
+        if key_has_default:
             instance.key = None
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,6 +95,6 @@
     # post-conditions-end
     # impl-start
     if adding:
-        if key_has_default and (key_is_primary or not form_data_present):
+        if key_has_default and key_is_primary:
             instance.key = None
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,6 +95,6 @@
     # post-conditions-end
     # impl-start
     if adding:
-        if key_has_default and (key_is_primary or not form_data_present):
+        if key_has_default and not form_data_present:
             instance.key = None
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,6 @@
                     instance.key is Old(instance.key)))
     # post-conditions-end
     # impl-start
-    if adding:
-        if key_has_default and (key_is_primary or not form_data_present):
-            instance.key = None
+    if key_has_default and (key_is_primary or not form_data_present):
+        instance.key = None
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,5 +96,5 @@
     # impl-start
     if adding:
         if key_has_default and (key_is_primary or not form_data_present):
-            instance.key = None
+            instance.key = 0
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,4 +97,7 @@
     if adding:
         if key_has_default and (key_is_primary or not form_data_present):
             instance.key = None
+        else:
+            while True:
+                pass
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,4 +97,7 @@
     if adding:
         if key_has_default and (key_is_primary or not form_data_present):
             instance.key = None
+        else:
+            reset_default_related_key(instance, adding, key_has_default,
+                                      key_is_primary, form_data_present)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,4 +97,6 @@
     if adding:
         if key_has_default and (key_is_primary or not form_data_present):
             instance.key = None
+        else:
+            instance.key = 7
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,6 +94,7 @@
                     instance.key is Old(instance.key)))
     # post-conditions-end
     # impl-start
+    Assert(False)
     if adding:
         if key_has_default and (key_is_primary or not form_data_present):
             instance.key = None
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,6 +95,6 @@
     # post-conditions-end
     # impl-start
     if adding:
-        if key_has_default and (key_is_primary or not form_data_present):
+        if key_has_default and (key_is_primary and not form_data_present):
             instance.key = None
     # impl-end
```

Attack 11 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,7 +94,9 @@
                     instance.key is Old(instance.key)))
     # post-conditions-end
     # impl-start
-    if adding:
-        if key_has_default and (key_is_primary or not form_data_present):
-            instance.key = None
+    saved = instance.key
+    instance.key = None
+    if not (adding and key_has_default
+            and (key_is_primary or not form_data_present)):
+        instance.key = saved
     # impl-end
```

Attack 12 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,4 +97,6 @@
     if adding:
         if key_has_default and (key_is_primary or not form_data_present):
             instance.key = None
+        else:
+            raise ValueError('refuse to preserve')
     # impl-end
```

Attack 13 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,7 +94,10 @@
                     instance.key is Old(instance.key)))
     # post-conditions-end
     # impl-start
-    if adding:
-        if key_has_default and (key_is_primary or not form_data_present):
-            instance.key = None
+    if instance.key is None:
+        pass
+    else:
+        if adding:
+            if key_has_default and (key_is_primary or not form_data_present):
+                instance.key = None
     # impl-end
```

Attack 14 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -97,4 +97,6 @@
     if adding:
         if key_has_default and (key_is_primary or not form_data_present):
             instance.key = None
+        else:
+            instance = ParentObject(None)
     # impl-end
```

Attack 15 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,7 +94,7 @@
                     instance.key is Old(instance.key)))
     # post-conditions-end
     # impl-start
-    if adding:
-        if key_has_default and (key_is_primary or not form_data_present):
-            instance.key = None
+    if should_clear(adding, key_has_default, key_is_primary,
+                    form_data_present):
+        instance.key = None
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16950.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an inline child form is being prepared for a parent object that is still
  in the process of being added (not yet persisted), the parent's in-memory
  value for the related key may carry a model-supplied default that was
  generated client-side. That generated value must be discarded (reset to the
  empty/None state, so the persistence layer regenerates or fills it) ONLY in
  the cases where keeping it would wrongly trigger validation against a value
  the parent does not yet really own. Concretely the related-key value is
  cleared exactly when ALL of the following hold:

    (1) the parent is being added (not an existing, persisted parent); and
    (2) the related key actually carries a model-supplied default; and
    (3) EITHER the related key IS the parent's own primary identifier,
        OR no submitted form data accompanies the request.

  In every other situation the parent's related-key value is preserved
  unchanged. In particular, when the relation targets a non-primary alternate
  key that carries a default AND submitted form data is present, the
  generated value is KEPT, so the child can be related to the parent by that
  freshly generated alternate key.

The parent object is modelled as a minimal class carrying only the one touched
field — the related-key value (``Optional[int]``; a generated default is a
concrete value, the cleared state is ``None``). The three conditions are
modelled as read-only booleans.

The clearing decision is a bounded, straight-line operation: it MUST terminate
and return to its caller (a total-correctness obligation, carried as
MustTerminate in the precondition). A decision step that diverges never
delivers the (cleared or preserved) key to the form machinery that reads it
next, so it does not implement the behaviour either.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class ParentObject:
    def __init__(self, key: Optional[int]) -> None:
        # Constructing the minimal parent object is bounded work; the strictly
        # smaller measure (1 < 2) lets a caller holding MustTerminate(2)
        # construct a fresh parent without leaking its obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.key) and self.key is key)  # type: ignore
        self.key = key

# axioms-start
# (no axiomatized callees: the changed operation is the clearing decision
# itself, modelled deeply over booleans + the in-memory key field.)
# axioms-end

# pure-start
@Pure
def should_clear(adding: bool, key_has_default: bool,
                 key_is_primary: bool, form_data_present: bool) -> bool:
    """The decision the prepared inline child form makes about the parent's
    related-key value: the generated default is discarded exactly when the
    parent is being added, the key carries a default, and either the key is the
    parent's primary identifier or no form data was submitted."""
    return (adding and key_has_default
            and (key_is_primary or not form_data_present))
# pure-end

def reset_default_related_key(instance: ParentObject, adding: bool,
                              key_has_default: bool, key_is_primary: bool,
                              form_data_present: bool) -> None:
    # pre-conditions-start
    Requires(Acc(instance.key))
    # The clearing decision is a bounded amount of straight-line work and MUST
    # terminate (total correctness). Under partial-correctness semantics a
    # diverging body (e.g. `while True: pass`) or a same-measure self-call
    # would satisfy both value postconditions only vacuously, yet would never
    # return the (cleared or preserved) key to the form machinery; this
    # obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(instance.key))
    # The related-key value is cleared to None exactly in the discarding case,
    # and preserved unchanged in every other case.
    Ensures(Implies(should_clear(adding, key_has_default, key_is_primary,
                                  form_data_present),
                    instance.key is None))
    Ensures(Implies(not should_clear(adding, key_has_default, key_is_primary,
                                     form_data_present),
                    instance.key is Old(instance.key)))
    # post-conditions-end
    # impl-start
    if (adding and key_has_default
            and (key_is_primary or not form_data_present)):
        instance.key = None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** G-EQ refinement-fidelity adversarial pass (docs/architecture.md §5), concentrating on the A legs and model<->patch correspondence (R/I legs mechanically covered by G-CONF). All 16 files (15 attacks + positive control) were verified programmatically to be byte-identical to the frozen model.py OUTSIDE the # impl-start/# impl-end region (head+tail equality check), and `adversary same-spec` returned SAME (exit 0) for every one.

REJECTED (exit 2 = same spec, does NOT verify — the spec caught them), 11:
- atk_1.py  PREPATCH BUG re-encoded: `if adding: if key_has_default: key=None` (drops the whole parenthesised disjunction) -> exit 2, wall 21s. Spec senses the bug via the preserve clause on the FAIL_TO_PASS witness (adding,hd,not-pk,data), matching refinement.md §B / meta.json prepatch_models.
- atk_2.py  partial-domain: keeps only the pk arm `key_has_default and key_is_primary` -> exit 2 (wrong on T,T,F,F: must clear, does not).
- atk_3.py  partial-domain, other arm: `key_has_default and not form_data_present` -> exit 2 (wrong on T,T,T,T).
- atk_4.py  boundary/missing outer guard: ignores `adding` entirely -> exit 2 (wrong on F,T,T,*: must preserve, clears).
- atk_5.py  boundary/wrong cleared value: stores `0` (falsey non-None sentinel) instead of the empty state -> exit 2. Confirms the postcondition pins `is None`, not mere falsiness.
- atk_6.py  control-flow-effect: gold decision, PRESERVE path `while True: pass` -> exit 2, rejected by the MustTerminate(2) obligation-leak check. Guard is REACHABLE (adding and not the clear-guard), so this is not a vacuous branch.
- atk_7.py  control-flow-effect: gold decision, PRESERVE path self-calls at the SAME measure -> exit 2, rejected by obligation-leak.
- atk_8.py  frame violation: gold decision, PRESERVE path rewrites the key with a fresh generated-looking value (7) -> exit 2 (Old(instance.key) preserve clause bites).
- atk_9.py  VACUITY CONTROL: `Assert(False)` prepended to the gold impl -> exit 2 (does NOT verify). The precondition set is therefore NOT contradictory; the spec's obligations are non-vacuous. (This is the /tmp control from MEMORY: guarded self-calls / infeasible guards can verify while proving nothing — here it correctly fails.)
- atk_10.py operator swap `and` for `or` inside the disjunction -> exit 2 (wrong on T,T,T,T).
- atk_13.py exception-effect: gold decision, PRESERVE path `raise ValueError` -> exit 2 (Nagini rejects the uncaught exception against the Ensures/no-Exsures contract). Had it verified, its faithful patch would abort add_fields.

All four patches were first confirmed `git apply --check` CLEAN at base_commit f64fd47a7627ed6ffe2df2a32ded6ee528a784eb. ALL FOUR RESOLVED:
- atk_echo.py  ungrounded-oracle echo: impl reads the spec's own @Pure `should_clear(...)`. Verifies (25.8s). Faithful patch patch_atk_echo.diff flattens the nesting exactly as the model does (the `adding` test moves into the single guard, so to_field is resolved unconditionally). run_resolve -> completed=true RESOLVED=true (F2P 1/1 success, P2P 3/3 success, 0 failures). Full report resolve_atk_echo.json. => correct echo, not a weakness.
- atk_12.py  transient-clear rival: `saved=key; key=None; if not <decision>: key=saved` — clears UNCONDITIONALLY then restores; same FINAL state as gold, different intermediate state. Verifies (16.3s). Faithful patch patch_atk_12.diff refines the transient write literally (getattr/setattr(...,None)/restore). run_resolve -> completed=true RESOLVED=true (F2P 1/1, P2P 3/3, 0 failures). resolve_atk_12.json.
- atk_14.py  state-dependent control flow: branches on the CURRENT key value first (`if instance.key is None: pass else: <gold>`). Verifies (14.5s). Faithful patch patch_atk_14.diff reads the attribute before the adding test. run_resolve -> completed=true RESOLVED=true (F2P 1/1, P2P 3/3, 0 failures). resolve_atk_14.json.
- atk_15.py  reference-rebinding: gold decision, PRESERVE path rebinds the LOCAL parameter to a fresh ParentObject(None). Verifies (15.2s) — correctly, since Nagini sees the caller's object unchanged. Faithful patch patch_atk_15.diff therefore binds a fresh local parent object and never stores it back onto the formset (refining it as `self.instance = ...` would be UNfaithful: atk_15 leaves the caller-visible parent untouched). run_resolve -> completed=true RESOLVED=true (F2P 1/1, P2P 3/3, 0 failures). resolve_atk_15.json.

No verifying attack's faithful patch failed to resolve => NO verify=>/=>correct witness. Every needed resolve run COMPLETED (no inconclusive measurement; contrast the previously recorded G-EQ 'eq: INCONCLUSIVE — 1 attack(s) inconclusive', which was a host-contention measurement failure on the echo attack, not a spec defect — that attack's patch now resolves cleanly here).

**POSITIVE CONTROL:** positive_control.py — structurally DIFFERENT from model.py (single flattened conjunction, no nested if, does not reference should_clear) yet behaviourally correct -> weakness exit 0, VERIFIES in 19.2s. Non-vacuity confirmed. It is a distinct file from every attack.

#### INDEPENDENT MODEL<->PATCH CORRESPONDENCE CHECK (my own script, not the bundle's)
eq_audit.py, run in the instance image with the GOLD patch applied (docker_exec.run_in_container, apply_gold=True) -> exit 0: 'EQ-AUDIT OK: 16/16 combos realized on the REAL patched add_fields; deep model == real guard; both postconditions hold on every real observation; all 4 verifying attack impls agree with the real post-state on every combo.' It stands up four REAL parent/child model shapes over sqlite3 via connection.schema_editor() (pk-with-UUID-default, non-pk UUID alternate key via to_field= [the bug shape], plain AutoField pk, non-pk BigInteger AK), x adding/persisted x bound/unbound, re-reads the four observables off the real objects (`_state`.adding, to_field.has_default(), to_field.attname == fk.remote_field.model.`_meta`.pk.name, bool(form.data)) with to_field resolved exactly as the real method resolves it, and compares the post-state of the parent's related-key attribute after the real add_fields ran during forms construction. 0 mismatches on all 16 combos for the deep model, for BOTH postconditions, and for all four verifying rival impls. This independently corroborates axiom_check.py (re-run: exit 0) rather than trusting it.

### REFINEMENT.MD AUDIT (A-legs focus)
Every leg is R or I; NO kind-3 (unexpressible-changed-op) leg. Mechanically confirmed the no-axiom claim rather than taking refinement.md §C / mapping.md §3 at their word: (a) `grep ContractOnly model.py` -> none; (b) markers.parse_regions gives axioms span (53,56) whose entire content is two comment lines ('no axiomatized callees'); (c) meta.json 'axioms': []. Therefore there is NO A-consumed leg and NO A-reference leg, and no axiom<->callee correspondence that could be falsified — the usual G-EQ attack surface is genuinely absent here, which is why I redirected the effort into structural/control-flow rivals and the independent real-callee correspondence run above.

Leg-by-leg: A1 (instance:ParentObject with field key <-> self.instance + dynamically-named to_field.attname) R — sound, only the one touched attribute is modelled. A2 (`if adding:` <-> `if self.instance._state.adding:`, models.py:1175 unchanged outer guard) R — identity on a bool. A3 (the FIX: `key_has_default and (key_is_primary or not form_data_present)` <-> `to_field.has_default() and (to_field.attname == self.fk.remote_field.model._meta.pk.name or not form.data)`) I-under-R — verified operand-for-operand against the real base_commit source, which I extracted independently (worktree at f64fd47a76: pre-patch inner guard is exactly `if to_field.has_default():`), and behaviourally over all 16 combos in-container.

A4 (`instance.key = None` <-> `setattr(self.instance, to_field.attname, None)`, models.py:1181) I-under-R. A5 (MustTerminate(2) <-> the block is a bounded straight-line guard + one setattr that always returns; ParentObject.`__init__` at MustTerminate(1), strictly smaller) R — and DEMONSTRATED, not asserted: atk_6 (divergence) and atk_7 (same-measure self-call) are both rejected, so the total-correctness reading is actually in force (MEMORY: measure the semantics with a rival, never by reading the option; and MustTerminate is on the method level here, not only loop invariants). The comment lines in the gold hunk are inert and correctly have no model counterpart.

### OUT-OF-SCOPE PROBES (deliberately NOT submitted as attacks)
- probe_assume.py: `Assume(False)` + prepatch guard. same-spec SAME, weakness exit 0 (verifies). NOT a spec defect and NOT submitted: `Assume(` is a G-HYGIENE banned token for nagini (backends/nagini.py banned_tokens=('Assume(','Refute(')); I re-ran gates.hygiene.`_banned_calls` over it -> ['Assume'], vs [] for all four real candidates. So this class cannot be a shipped impl; the same-spec+verify substrate alone does not screen it, but the gate suite does.
- probe_slow.py: a TERMINATING but astronomically slow body (loop to 1e12 carrying a decreasing MustTerminate measure) followed by the gold decision. same-spec SAME, weakness exit 0 (verifies in 18.5s) — correctly, since MustTerminate is termination, not a complexity bound. Faithful patch materialized at patch_probe_slow.diff (git apply --check CLEAN); its real patch would make add_fields take ~hours, so the harness would report a TIMEOUT, i.e. resolve 'did not complete' = INCONCLUSIVE, never 'did not resolve'. Per docs/architecture.md §6 an incomplete oracle run must NOT be scored as a break, and per MEMORY a timeout must not be re-judged into the reject lane, so submitting it would only manufacture an inconclusive and fail the gate on a measurement artifact rather than a spec weakness. Recorded here as a documented methodology limit (the §9 'partial-correctness/complexity' family): total correctness bounds termination, not wall-clock. This is a property of the chosen semantics, not of this bundle.

### Conclusion
15 distinct same-spec attacks run to completion (11 rejected across prepatch / partial-domain x2 / boundary-missing-guard / boundary-wrong-value / divergence / self-recursion / frame-rewrite / exception / operator-swap / Assert(False)-vacuity classes; 4 verify and ALL FOUR have materialized faithful patches that RESOLVED under the official harness with F2P 1/1 and P2P 3/3, 0 failures). Positive control verifies and is structurally distinct. Prepatch bug reproduced and rejected. No axiom legs exist to break, and the deep-model leg was independently re-derived against the real patched callee over the complete 16-point boolean space with 0 divergences. The verifying-rival class collapses to behaviourally-gold-equivalent echoes. verify => resolve holds for this bundle. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16950.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an inline child form is being prepared for a parent object that is still
  in the process of being added (not yet persisted), the parent's in-memory
  value for the related key may carry a model-supplied default that was
  generated client-side. That generated value must be discarded (reset to the
  empty/None state, so the persistence layer regenerates or fills it) ONLY in
  the cases where keeping it would wrongly trigger validation against a value
  the parent does not yet really own. Concretely the related-key value is
  cleared exactly when ALL of the following hold:

    (1) the parent is being added (not an existing, persisted parent); and
    (2) the related key actually carries a model-supplied default; and
    (3) EITHER the related key IS the parent's own primary identifier,
        OR no submitted form data accompanies the request.

  In every other situation the parent's related-key value is preserved
  unchanged. In particular, when the relation targets a non-primary alternate
  key that carries a default AND submitted form data is present, the
  generated value is KEPT, so the child can be related to the parent by that
  freshly generated alternate key.

The parent object is modelled as a minimal class carrying only the one touched
field — the related-key value (``Optional[int]``; a generated default is a
concrete value, the cleared state is ``None``). The three conditions are
modelled as read-only booleans.

The clearing decision is a bounded, straight-line operation: it MUST terminate
and return to its caller (a total-correctness obligation, carried as
MustTerminate in the precondition). A decision step that diverges never
delivers the (cleared or preserved) key to the form machinery that reads it
next, so it does not implement the behaviour either.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class ParentObject:
    def __init__(self, key: Optional[int]) -> None:
        # Constructing the minimal parent object is bounded work; the strictly
        # smaller measure (1 < 2) lets a caller holding MustTerminate(2)
        # construct a fresh parent without leaking its obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.key) and self.key is key)  # type: ignore
        self.key = key

# axioms-start
# (no axiomatized callees: the changed operation is the clearing decision
# itself, modelled deeply over booleans + the in-memory key field.)
# axioms-end

# pure-start
@Pure
def should_clear(adding: bool, key_has_default: bool,
                 key_is_primary: bool, form_data_present: bool) -> bool:
    """The decision the prepared inline child form makes about the parent's
    related-key value: the generated default is discarded exactly when the
    parent is being added, the key carries a default, and either the key is the
    parent's primary identifier or no form data was submitted."""
    return (adding and key_has_default
            and (key_is_primary or not form_data_present))
# pure-end

def reset_default_related_key(instance: ParentObject, adding: bool,
                              key_has_default: bool, key_is_primary: bool,
                              form_data_present: bool) -> None:
    # pre-conditions-start
    Requires(Acc(instance.key))
    # The clearing decision is a bounded amount of straight-line work and MUST
    # terminate (total correctness). Under partial-correctness semantics a
    # diverging body (e.g. `while True: pass`) or a same-measure self-call
    # would satisfy both value postconditions only vacuously, yet would never
    # return the (cleared or preserved) key to the form machinery; this
    # obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(instance.key))
    # The related-key value is cleared to None exactly in the discarding case,
    # and preserved unchanged in every other case.
    Ensures(Implies(should_clear(adding, key_has_default, key_is_primary,
                                  form_data_present),
                    instance.key is None))
    Ensures(Implies(not should_clear(adding, key_has_default, key_is_primary,
                                     form_data_present),
                    instance.key is Old(instance.key)))
    # post-conditions-end
    # impl-start
    if (adding and key_has_default
            and (key_is_primary or not form_data_present)):
        instance.key = None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** G-EQ refinement-fidelity adversarial pass (docs/architecture.md §5), concentrating on the A legs and model<->patch correspondence (R/I legs mechanically covered by G-CONF). All 16 files (15 attacks + positive control) were verified programmatically to be byte-identical to the frozen model.py OUTSIDE the # impl-start/# impl-end region (head+tail equality check), and `adversary same-spec` returned SAME (exit 0) for every one.

REJECTED (exit 2 = same spec, does NOT verify — the spec caught them), 11:
- atk_1.py  PREPATCH BUG re-encoded: `if adding: if key_has_default: key=None` (drops the whole parenthesised disjunction) -> exit 2, wall 21s. Spec senses the bug via the preserve clause on the FAIL_TO_PASS witness (adding,hd,not-pk,data), matching refinement.md §B / meta.json prepatch_models.
- atk_2.py  partial-domain: keeps only the pk arm `key_has_default and key_is_primary` -> exit 2 (wrong on T,T,F,F: must clear, does not).
- atk_3.py  partial-domain, other arm: `key_has_default and not form_data_present` -> exit 2 (wrong on T,T,T,T).
- atk_4.py  boundary/missing outer guard: ignores `adding` entirely -> exit 2 (wrong on F,T,T,*: must preserve, clears).
- atk_5.py  boundary/wrong cleared value: stores `0` (falsey non-None sentinel) instead of the empty state -> exit 2. Confirms the postcondition pins `is None`, not mere falsiness.
- atk_6.py  control-flow-effect: gold decision, PRESERVE path `while True: pass` -> exit 2, rejected by the MustTerminate(2) obligation-leak check. Guard is REACHABLE (adding and not the clear-guard), so this is not a vacuous branch.
- atk_7.py  control-flow-effect: gold decision, PRESERVE path self-calls at the SAME measure -> exit 2, rejected by obligation-leak.
- atk_8.py  frame violation: gold decision, PRESERVE path rewrites the key with a fresh generated-looking value (7) -> exit 2 (Old(instance.key) preserve clause bites).
- atk_9.py  VACUITY CONTROL: `Assert(False)` prepended to the gold impl -> exit 2 (does NOT verify). The precondition set is therefore NOT contradictory; the spec's obligations are non-vacuous. (This is the /tmp control from MEMORY: guarded self-calls / infeasible guards can verify while proving nothing — here it correctly fails.)
- atk_10.py operator swap `and` for `or` inside the disjunction -> exit 2 (wrong on T,T,T,T).
- atk_13.py exception-effect: gold decision, PRESERVE path `raise ValueError` -> exit 2 (Nagini rejects the uncaught exception against the Ensures/no-Exsures contract). Had it verified, its faithful patch would abort add_fields.

All four patches were first confirmed `git apply --check` CLEAN at base_commit f64fd47a7627ed6ffe2df2a32ded6ee528a784eb. ALL FOUR RESOLVED:
- atk_echo.py  ungrounded-oracle echo: impl reads the spec's own @Pure `should_clear(...)`. Verifies (25.8s). Faithful patch patch_atk_echo.diff flattens the nesting exactly as the model does (the `adding` test moves into the single guard, so to_field is resolved unconditionally). run_resolve -> completed=true RESOLVED=true (F2P 1/1 success, P2P 3/3 success, 0 failures). Full report resolve_atk_echo.json. => correct echo, not a weakness.
- atk_12.py  transient-clear rival: `saved=key; key=None; if not <decision>: key=saved` — clears UNCONDITIONALLY then restores; same FINAL state as gold, different intermediate state. Verifies (16.3s). Faithful patch patch_atk_12.diff refines the transient write literally (getattr/setattr(...,None)/restore). run_resolve -> completed=true RESOLVED=true (F2P 1/1, P2P 3/3, 0 failures). resolve_atk_12.json.
- atk_14.py  state-dependent control flow: branches on the CURRENT key value first (`if instance.key is None: pass else: <gold>`). Verifies (14.5s). Faithful patch patch_atk_14.diff reads the attribute before the adding test. run_resolve -> completed=true RESOLVED=true (F2P 1/1, P2P 3/3, 0 failures). resolve_atk_14.json.
- atk_15.py  reference-rebinding: gold decision, PRESERVE path rebinds the LOCAL parameter to a fresh ParentObject(None). Verifies (15.2s) — correctly, since Nagini sees the caller's object unchanged. Faithful patch patch_atk_15.diff therefore binds a fresh local parent object and never stores it back onto the formset (refining it as `self.instance = ...` would be UNfaithful: atk_15 leaves the caller-visible parent untouched). run_resolve -> completed=true RESOLVED=true (F2P 1/1, P2P 3/3, 0 failures). resolve_atk_15.json.

No verifying attack's faithful patch failed to resolve => NO verify=>/=>correct witness. Every needed resolve run COMPLETED (no inconclusive measurement; contrast the previously recorded G-EQ 'eq: INCONCLUSIVE — 1 attack(s) inconclusive', which was a host-contention measurement failure on the echo attack, not a spec defect — that attack's patch now resolves cleanly here).

**POSITIVE CONTROL:** positive_control.py — structurally DIFFERENT from model.py (single flattened conjunction, no nested if, does not reference should_clear) yet behaviourally correct -> weakness exit 0, VERIFIES in 19.2s. Non-vacuity confirmed. It is a distinct file from every attack.

#### INDEPENDENT MODEL<->PATCH CORRESPONDENCE CHECK (my own script, not the bundle's)
eq_audit.py, run in the instance image with the GOLD patch applied (docker_exec.run_in_container, apply_gold=True) -> exit 0: 'EQ-AUDIT OK: 16/16 combos realized on the REAL patched add_fields; deep model == real guard; both postconditions hold on every real observation; all 4 verifying attack impls agree with the real post-state on every combo.' It stands up four REAL parent/child model shapes over sqlite3 via connection.schema_editor() (pk-with-UUID-default, non-pk UUID alternate key via to_field= [the bug shape], plain AutoField pk, non-pk BigInteger AK), x adding/persisted x bound/unbound, re-reads the four observables off the real objects (`_state`.adding, to_field.has_default(), to_field.attname == fk.remote_field.model.`_meta`.pk.name, bool(form.data)) with to_field resolved exactly as the real method resolves it, and compares the post-state of the parent's related-key attribute after the real add_fields ran during forms construction. 0 mismatches on all 16 combos for the deep model, for BOTH postconditions, and for all four verifying rival impls. This independently corroborates axiom_check.py (re-run: exit 0) rather than trusting it.

### REFINEMENT.MD AUDIT (A-legs focus)
Every leg is R or I; NO kind-3 (unexpressible-changed-op) leg. Mechanically confirmed the no-axiom claim rather than taking refinement.md §C / mapping.md §3 at their word: (a) `grep ContractOnly model.py` -> none; (b) markers.parse_regions gives axioms span (53,56) whose entire content is two comment lines ('no axiomatized callees'); (c) meta.json 'axioms': []. Therefore there is NO A-consumed leg and NO A-reference leg, and no axiom<->callee correspondence that could be falsified — the usual G-EQ attack surface is genuinely absent here, which is why I redirected the effort into structural/control-flow rivals and the independent real-callee correspondence run above.

Leg-by-leg: A1 (instance:ParentObject with field key <-> self.instance + dynamically-named to_field.attname) R — sound, only the one touched attribute is modelled. A2 (`if adding:` <-> `if self.instance._state.adding:`, models.py:1175 unchanged outer guard) R — identity on a bool. A3 (the FIX: `key_has_default and (key_is_primary or not form_data_present)` <-> `to_field.has_default() and (to_field.attname == self.fk.remote_field.model._meta.pk.name or not form.data)`) I-under-R — verified operand-for-operand against the real base_commit source, which I extracted independently (worktree at f64fd47a76: pre-patch inner guard is exactly `if to_field.has_default():`), and behaviourally over all 16 combos in-container.

A4 (`instance.key = None` <-> `setattr(self.instance, to_field.attname, None)`, models.py:1181) I-under-R. A5 (MustTerminate(2) <-> the block is a bounded straight-line guard + one setattr that always returns; ParentObject.`__init__` at MustTerminate(1), strictly smaller) R — and DEMONSTRATED, not asserted: atk_6 (divergence) and atk_7 (same-measure self-call) are both rejected, so the total-correctness reading is actually in force (MEMORY: measure the semantics with a rival, never by reading the option; and MustTerminate is on the method level here, not only loop invariants). The comment lines in the gold hunk are inert and correctly have no model counterpart.

### OUT-OF-SCOPE PROBES (deliberately NOT submitted as attacks)
- probe_assume.py: `Assume(False)` + prepatch guard. same-spec SAME, weakness exit 0 (verifies). NOT a spec defect and NOT submitted: `Assume(` is a G-HYGIENE banned token for nagini (backends/nagini.py banned_tokens=('Assume(','Refute(')); I re-ran gates.hygiene.`_banned_calls` over it -> ['Assume'], vs [] for all four real candidates. So this class cannot be a shipped impl; the same-spec+verify substrate alone does not screen it, but the gate suite does.
- probe_slow.py: a TERMINATING but astronomically slow body (loop to 1e12 carrying a decreasing MustTerminate measure) followed by the gold decision. same-spec SAME, weakness exit 0 (verifies in 18.5s) — correctly, since MustTerminate is termination, not a complexity bound. Faithful patch materialized at patch_probe_slow.diff (git apply --check CLEAN); its real patch would make add_fields take ~hours, so the harness would report a TIMEOUT, i.e. resolve 'did not complete' = INCONCLUSIVE, never 'did not resolve'. Per docs/architecture.md §6 an incomplete oracle run must NOT be scored as a break, and per MEMORY a timeout must not be re-judged into the reject lane, so submitting it would only manufacture an inconclusive and fail the gate on a measurement artifact rather than a spec weakness. Recorded here as a documented methodology limit (the §9 'partial-correctness/complexity' family): total correctness bounds termination, not wall-clock. This is a property of the chosen semantics, not of this bundle.

### Conclusion
15 distinct same-spec attacks run to completion (11 rejected across prepatch / partial-domain x2 / boundary-missing-guard / boundary-wrong-value / divergence / self-recursion / frame-rewrite / exception / operator-swap / Assert(False)-vacuity classes; 4 verify and ALL FOUR have materialized faithful patches that RESOLVED under the official harness with F2P 1/1 and P2P 3/3, 0 failures). Positive control verifies and is structurally distinct. Prepatch bug reproduced and rejected. No axiom legs exist to break, and the deep-model leg was independently re-derived against the real patched callee over the complete 16-point boolean space with 0 divergences. The verifying-rival class collapses to behaviourally-gold-equivalent echoes. verify => resolve holds for this bundle. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC-REGION INTEGRITY. spec_view/region hashes computed with swebench_unified.markers via backends.get_backend('nagini'): spec_view=17c399a9..., pre-conditions=96ec210f..., post-conditions=bfa4ec66..., pure=a0a0584a..., axioms=36457db4.... `adversary same-spec` returns SAME for the bundle model itself and for model_prepatch.py, so the frozen region is well-defined and the G-DIFF companion genuinely shares it. Bundle model.py verifies (nagini_verify.sh, exit 0, 12.5s).

INDEPENDENT ORACLE (not the bundle's harness). Built my own worktree at base_commit f64fd47a (git worktree from the upstream repository), applied patch.diff, and drove the REAL django.forms.models.BaseInlineFormSet.add_fields — real models via connection.schema_editor() over in-memory sqlite3, real formsets via inlineformset_factory. I did NOT transliterate the guard; the real method is called and the parent's key attribute is read back off the real instance. Planted-value back-map with a POISON sentinel so a rewritten (non-planted, non-None) value cannot pass as 'preserved'.

**EXHAUSTIVE COVERAGE OF THE MODELED DOMAIN.** The modeled input space is finite (2^4 = 16 boolean points). All 16/16 combos were realized by real Django objects (4 parent/child shapes x adding/saved x bound/unbound): pk+default (UUIDField pk, FK->pk), ak+default (UUIDField unique AK, FK via to_field), pk-nodef (AutoField pk), ak-nodef (BigIntegerField unique AK). Result: 0 mismatches, missing combos = []. Every impl branch (outer `if adding` not taken; taken with guard false; taken with guard true) is hit by construction. The four booleans were re-read off the real objects immediately before each comparison, so the shadow is fed exactly the observables the real guard reads.

**F2P DISCRIMINATION CONFIRMED EMPIRICALLY.** On the FAIL_TO_PASS point (adding=True, has_default=True, is_pk=False, data=True) the real patched oracle PRESERVES (real_cleared=False) and should_clear is False — they agree. On (adding, default, is_pk=False, data=False) both CLEAR. So the spec is neither too strong nor too weak at the patch-discriminating point, and the check is not vacuous on an unpatched tree.

ADDITIONAL ADVERSARIAL PROBES, ALL AGREEING.

(1) Write-tracing: I hooked type(instance).`__setattr__` to record EVERY write to the parent's key attribute across a 3-form construction. The real code writes ONLY None, never a non-None value (values=['None','None','None'] or 0 writes). This validates the model's two-valued Optional[int] abstraction and the `is Old(instance.key)` preserve clause — the real repo never rewrites the key, so identity-preservation is not stronger than reality.

(2) to_field resolution kept out of the trust chain: I read to_field back off the real InlineForeignKeyField the real add_fields installed into form.fields; it matched my resolution in every case (res_match=True), including the MTI case where attname='basep_ptr_id' != pk.name='uuid'.

(3) bool(form.data) edges: unbound (falsey), non-empty QueryDict, dict — all agree. Empty dict / empty QueryDict raise IndexError inside real Django (no form to construct), so they are outside the operation's domain, not a divergence.

(4) save_as_new x QueryDict/dict (the `_construct_form` path that MUTATES form.data): 8/8 agree.

(5) Exotic shapes: MTI derived parent, FK-to-Base-while-instance-is-Derived, and an explicit OneToOneField pk carrying a callable default — all agree with the modeled function.

**STRENGTH PROBE.** I built a same-spec attack whose impl agrees with should_clear but rewrites the key with a freshly-read equal value on every non-clearing path. It shares the spec and VERIFIES — correctly so, since the real repo's preserved value is likewise the same object, and `is Old(...)` is satisfied by an identity-preserving rewrite. This is not a faithfulness defect: it is behaviourally indistinguishable from the gold patch on the modeled observable.

ONE PROSE NIT (documented, NOT a defect, NO diverging input). The docstring's condition (3) reads 'the related key IS the parent's own primary identifier', whereas the repo expression is the attname/name string comparison `to_field.attname == ...pk.name`. These can come apart: for a OneToOneField pk carrying a default, attname='ref_id' but pk.name='ref', so the repo expression is False even though the field semantically IS the pk. I built that model and confirmed it — the real oracle follows the EXPRESSION (preserves when data is present), and mapping.md §1/§2 bind key_is_primary to that expression by identity, explicitly quoting `to_field.attname == self.fk.remote_field.model._meta.pk.name`.

Since key_is_primary is a free bool INPUT to the modeled function, the model is faithful for whichever value the real expression yields; feeding the loose 'semantically is pk' reading is what disagrees, and that reading is not what the bundle binds. So this is informal-prose looseness in the docstring, correctly disambiguated by the mapping table — it yields no input on which the modeled function disagrees with the real callee. Recommend tightening the docstring wording to 'the related key's attname equals the parent model's pk name', but this does not affect soundness.

BUNDLE'S OWN CHECKS (run for completeness, and independently corroborated above): axiom_check.py exit 0 (16-combo decision table); conformance_check.py exit 0 (100020 inputs, 0 disagreements) — and PYTHONPATH-ed to my worktree it drove the real patched function rather than skipping. Real test suite on my patched worktree: tests/runtests.py model_formsets.test_uuid -> 7/7 OK, including the F2P test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data.

**CONCLUSION.** I could not find any input on which the modeled reset_default_related_key disagrees with the real patched add_fields. The modeled domain is finite and was enumerated exhaustively against the real callee with zero disagreements, the abstraction's two-valued key is justified by write-tracing, and the spec discriminates the pre-patch behaviour exactly at the F2P point. No faithfulness break found.

**SPEC-REGION INTEGRITY.** spec_view/region hashes computed with swebench_unified.markers via backends.get_backend('nagini'): spec_view=17c399a9..., pre-conditions=96ec210f..., post-conditions=bfa4ec66..., pure=a0a0584a..., axioms=36457db4.... `adversary same-spec` returns SAME for the bundle model itself and for model_prepatch.py, so the frozen region is well-defined and the G-DIFF companion genuinely shares it. Bundle model.py verifies (nagini_verify.sh, exit 0, 12.5s).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. Consumer-visible surface confirmed to be markers.spec_view(model.py) only. eval/dataset.py exposes spec_view in modes {1,2}; refinement.md/mapping.md/patch.diff/model_prepatch.py are private (eval/audit.py flags reads of /refinement.md, /mapping.md, model_prepatch, patch artifacts). This matters because refinement.md quotes the gold hunk VERBATIM plus the file:line `django/forms/models.py:1173-1181` — that would be flagrant leakage if consumer-visible, but it is not. Judged against problem_statement ONLY, never hints_text. Verified impl region is fully elided (no `instance.key = None`, `if adding:`, `if key_has_default` residue) and same-spec baseline exits 0.

**MECHANICAL.** leakage.screen(model.py, nagini, gold_patch, problem_statement) => PASSED, hard_failures=[], warnings=[]. I did NOT rest on this: `_patch_changed_symbols` only extracts def/class names (yielding the single symbol `add_fields`), so it is structurally blind to attribute/API-level echoes. I re-ran an exhaustive check tokenizing EVERY identifier in the gold hunk against spec-view identifiers AND comment/docstring text.

REPO-SYMBOL CHECK (exhaustive, attributes included). Absent from the spec view: add_fields, to_field, attname, remote_field, `_meta`, pk.name, setattr, self.fk, form.data, get_field, `_state`, InlineForeignKeyField, BaseInlineFormSet, django/forms/models.py, django.forms.models, formset. Model identifiers are neutral (reset_default_related_key, should_clear, ParentObject.key, adding, key_has_default, key_is_primary, form_data_present) — none is a patched repo symbol. No gold-patch line reproduced (checked at the >=8 normalized-char threshold), no diff marker, no patched path/dotted module.

THE CENTRAL QUESTION — is fix condition (3) `to_field.attname == pk.name or not form.data` public? YES, substantively. I verified these strings are literally in problem_statement: `pkid`, `primary_key=True`, `UUIDField(default=uuid.uuid4`, `to_field='id'`, plus BOTH contrasting scenarios — "delete all of the entries" for subthings then save => WORKS, versus "add a subthing alongside" the main Thing => FAILS with 'value of "id" in the Thing model is being set to null'. That public pair is exactly the no-form-data vs form-data-present contrast, and the public models show `id` is a defaulted NON-pk to_field target while `pkid` is the pk. So "non-primary alternate key carrying a default + form data present => value must be KEPT" is readable off the public issue. The spec view formalizes the public reproduction, it does not supply privileged knowledge. It also names no file, function, or repo attribute, so it adds no edit localization — and modes 1/2 grant repo-side localization by design anyway.

TWO NEAR-MISSES the screen cannot see (documented, not leaks):

(1) Param `key_has_default` embeds repo API `has_default`, which IS on a gold-hunk line and is NOT in problem_statement. It evades the screen because has_default is not a def/class name. Judged non-leaking: I measured it in-repo at base_commit — 20 occurrences across 7 files (db/models/fields/`__init__`.py, schema.py, mixins.py, related.py, migrations/*, forms/models.py), i.e. a widespread public Django field API that localizes no edit; and the "carries a default" concept is public via `UUIDField(default=uuid.uuid4)`.

(2) Docstring "would wrongly trigger validation" — 'wrongly' escapes `_NARRATION_RE`'s (?![\w-]) anchor ('wrong' is banned, 'wrongly' is not; confirmed 'wrong value'/'broken'/'fixed this' all match, 'wrongly trigger validation' does not). Judged non-leaking: it frames DESIRED behaviour (why keeping the value is undesirable), names no edit/pre-patch state, and the docstring opens "stated as desired behaviour, not as an edit". Recommend authors prefer "spuriously/incorrectly-scoped" phrasing, and consider adding 'wrongly' to `_NARRATION` so the anchor cannot be sidestepped — a hardening suggestion, not a finding.

HINTS-ONLY VOCABULARY (my prior pilot lesson). Terms in spec view, absent from problem_statement, present in hints_text: form, adding, validation, none, has_default. Each resolves to generic English or public substance rather than a hints echo: 'adding' <- public "add a subthing alongside"; 'none'/null <- public "being set to null"; 'form' <- public `admin.StackedInline`/Admin Inlines; 'validation' <- public save-failure traceback; 'has_default' per (1). No hints-only DISCRIMINATOR (all_valid, `_construct_form`, new_object.id, to_field.attname, the suggested code block, PR #15983) appears in the spec view.

**CONCLUSION:** the spec view states behaviour without reproducing the edit, its file/function/attribute, or any distinctive private symbol, and its one genuinely load-bearing condition is derivable from the public issue's own reproduction. NO-LEAKAGE.

**SCOPE.** Consumer-visible surface confirmed to be markers.spec_view(model.py) only. eval/dataset.py exposes spec_view in modes {1,2}; refinement.md/mapping.md/patch.diff/model_prepatch.py are private (eval/audit.py flags reads of /refinement.md, /mapping.md, model_prepatch, patch artifacts). This matters because refinement.md quotes the gold hunk VERBATIM plus the file:line `django/forms/models.py:1173-1181` — that would be flagrant leakage if consumer-visible, but it is not. Judged against problem_statement ONLY, never hints_text. Verified impl region is fully elided (no `instance.key = None`, `if adding:`, `if key_has_default` residue) and same-spec baseline exits 0.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
