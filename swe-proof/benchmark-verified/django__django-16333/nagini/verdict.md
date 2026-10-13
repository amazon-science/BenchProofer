# P2 adversarial audit — django__django-16333

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies (3 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1_fiat_record.py`, `atk_2_prepatch.py`, `atk_3_shortcircuit_ready.py`, `atk_5_scratch_launder.py`, `atk_6_selfecho.py`, `atk_8_m2m_before_record.py`, `atk_9_uncond_persist.py`, `atk_10_prepatch_on_ready_half.py`, `atk_12_diverge_not_commit.py`, `atk_14_raise_after_commit.py`, `atk_15_no_base_save_ever.py`, +2 more |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 3 | `atk_4_fiat_fold.py`, `atk_7_raise_on_ready.py`, `atk_11_raise_not_commit.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_13_skip_base_when_ready.py`, `atk_18_double_effects.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl found. 18 same-spec attacks run on the real Nagini verifier: 16 REJECTED, 2 CANDIDATEs (verify + share spec), and BOTH candidates' materialized faithful patches RESOLVED under the official harness (F2P 1/1, P2P 87/87, patch applied, 1 attempt each), so neither is a verify-but-incorrect witness. atk_13_skip_base_when_ready (skip the base-form save when the m2m handle is already installed, leaning on the free entry fact for Ensures(get_ready())) is a genuinely correct alternative implementation: refinement.md §B's claim that base_form_save_deferred BINDS but does not PRODUCE the record object is factually right (BaseModelForm._post_clean -> construct_instance builds self.instance during validation), so `user = self.instance` on the already-ready branch is the faithful refinement and it persists both parts. atk_18_double_effects (duplicated base save / record write / deferred save) is admitted because the boolean+capability abstraction is idempotent, and the real callees are idempotent on the tested inputs too (Model.save() re-UPDATEs the same row; _save_m2m re-sets the same association set) — it resolved.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_fiat_record.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,14 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 1 (prior-pass counterexample, re-encoded): forge the primary-record
+    # fact by fiat (Unfold / assign / Fold) instead of performing the write, then
+    # run the real deferred relational save. Faithful patch omits `user.save()`.
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
-        persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        Unfold(self.form_pred())
+        self.record_persisted = True
+        Fold(self.form_pred())
+        run_deferred_save(self)
     return self
     # impl-end
```

Attack 2 — `atk_2_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,9 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 2 (prepatch bug): never run the deferred relational save.
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
     return self
     # impl-end
```

Attack 3 — `atk_3_shortcircuit_ready.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,8 +307,11 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 3 (partial domain / boundary on the free entry fact): a form that
+    # already has a deferred save set up is returned untouched -- persists nothing.
+    if self.get_ready():
+        return self
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
         if self.get_ready():
```

Attack 4 — `atk_4_fiat_fold.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -307,11 +307,11 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 4 (ungrounded-oracle fiat): conjure the relational-data capability by
+    # folding the abstract predicate instead of running the deferred save.
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        Fold(relations_done(self))
     return self
     # impl-end
```

Attack 5 — `atk_5_scratch_launder.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,15 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 5 (ungrounded-oracle echo / token transfer): run the real deferred
+    # relational save on a THROWAWAY form and try to pass its capability off as
+    # this form's. Faithful patch never writes THIS form's associations.
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        other = Form()
+        base_form_save_deferred(other)
+        persist_record(other)
+        run_deferred_save(other)
     return self
     # impl-end
```

Attack 6 — `atk_6_selfecho.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,7 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
-    base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
-    if commit:
-        persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
-    return self
+    # ATTACK 6 (function-under-spec self-echo): re-derive the postcondition from
+    # this routine's own contract. Faithful patch is non-terminating recursion.
+    return save_form(self, commit)
     # impl-end
```

Attack 7 — `atk_7_raise_on_ready.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -307,11 +307,14 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 7 (control-flow effect: exceptional exit on the re-entered half).
+    # A form that already has a deferred save set up gets an exception instead of
+    # persistence; the normal postcondition is then vacuous on that half.
+    if self.get_ready():
+        raise ValueError()
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
     return self
     # impl-end
```

Attack 8 — `atk_8_m2m_before_record.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,10 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 8 (ordering): write the relational data before the primary record.
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
+        run_deferred_save(self)
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
     return self
     # impl-end
```

Attack 9 — `atk_9_uncond_persist.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,10 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 9 (ignore `commit` for the record write): persist unconditionally.
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
+    persist_record(self)
     if commit:
-        persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
     return self
     # impl-end
```

Attack 10 — `atk_10_prepatch_on_ready_half.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,13 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 10 (partial domain, prepatch bug restricted to the re-entered half):
+    # run the deferred relational save only when no handle was already installed.
+    was_ready = self.get_ready()
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
+        if not was_ready:
             run_deferred_save(self)
     return self
     # impl-end
```

Attack 11 — `atk_11_raise_not_commit.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -307,11 +307,14 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 11 (control-flow effect: exceptional exit on the deferred request).
+    # Asked NOT to persist immediately, blow up instead of setting the deferred
+    # save up. Faithful patch raises on `form.save(commit=False)`.
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
+    else:
+        raise ValueError()
     return self
     # impl-end
```

Attack 12 — `atk_12_diverge_not_commit.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,13 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 12 (control-flow effect: divergence on the deferred request).
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
+    else:
+        while True:
+            Invariant(True)
     return self
     # impl-end
```

Attack 13 — `atk_13_skip_base_when_ready.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -307,11 +307,12 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
-    base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
+    # ATTACK 13: skip the base-form save entirely whenever the handle is already
+    # installed -- lean on the entry fact to discharge Ensures(get_ready()).
+    if not self.get_ready():
+        base_form_save_deferred(self)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
     return self
     # impl-end
```

Attack 14 — `atk_14_raise_after_commit.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,12 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    # ATTACK 14 (control-flow effect): do the gold work, then exit exceptionally
+    # so the normal postcondition is vacuous -- caller never receives the user.
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
+        raise Exception()
     return self
     # impl-end
```

Attack 15 — `atk_15_no_base_save_ever.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,10 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
-    base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
+    # ATTACK 15 (partial domain / boundary): never call the base-form save at all;
+    # rely purely on the entry deferred-save fact.
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
     return self
     # impl-end
```

Attack 16 — `atk_16_spurious_extra_record.py` → rejected (same spec, does not verify — good)

```diff
@@ -308,10 +308,12 @@
     # post-conditions-end
     # impl-start
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
+        other = Form()
+        base_form_save_deferred(other)
+        persist_record(other)
+        run_deferred_save(other)
     return self
     # impl-end
```

Attack 17 — `atk_17_no_handle_when_deferred.py` → rejected (same spec, does not verify — good)

```diff
@@ -307,11 +307,10 @@
     Ensures(Implies(not commit, self.get_record() is False))
     # post-conditions-end
     # impl-start
+    if not commit:
+        return self
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
-    if commit:
-        persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+    persist_record(self)
+    run_deferred_save(self)
     return self
     # impl-end
```

Attack 18 — `atk_18_double_effects.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -308,10 +308,11 @@
     # post-conditions-end
     # impl-start
     base_form_save_deferred(self)
-    # (the password assignment of the routine has no tracked persistence effect)
+    base_form_save_deferred(self)
     if commit:
         persist_record(self)
-        if self.get_ready():
-            run_deferred_save(self)
+        run_deferred_save(self)
+        persist_record(self)
+        run_deferred_save(self)
     return self
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16333.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A user-creation routine persists a submitted form. Persisting a form happens
  in two parts: the primary record itself, and the form's deferred relational
  data (the many-to-many associations, whose persistence the underlying
  base-form save defers so it can be run after the primary record exists).

  When the routine is asked to persist immediately, BOTH parts must end up
  persisted once it returns:

    (1) the primary record is written, and

    (2) whenever a deferred relational save was set up for this form, that
        deferred save is run too, so the many-to-many associations are written.

  When the routine is NOT asked to persist immediately, nothing is written, but
  the deferred relational save is still set up so a later caller can run it.

  Those two guarantees hold whatever a caller did to the form before. Deferring
  is exactly what leaves a deferred relational save set up, so a caller that
  first asks for deferred persistence and afterwards asks for immediate
  persistence enters the routine on a form that ALREADY has one set up. That
  entry state is ordinary, and the routine owes the same thing on it: asked to
  persist immediately it must still write the primary record and must still
  leave the deferred relational data written for the form, exactly as when it is
  entered on a form nobody has persisted through yet. How the form arrived is
  not a reason for either part of the persistence to be missing.

  Both persistence steps act on the form's model RECORD OBJECT. That object is
  already available when the routine is entered -- the form holds it, having
  built it from the submitted data while validating -- so every step of the
  routine may act on it, and the object the routine hands back is that same
  one. The base-form save returns it; it is not what brings it into existence.

  Nothing the routine can say makes either part of the persistence true. The
  primary record counts as written only once the primary record write has
  actually been performed on the record object, and a deferred relational save
  counts as set up only once the base-form save has actually set one up.
  Whoever holds the form may READ those two facts but cannot set them: each
  changes only by performing the step that brings it about. The relational-data
  fact is grounded the same way, and more strongly still (below). So
  "persisted" here always means the persisting step ran -- never that the
  routine declared it so.

The form is modelled as a minimal object carrying only the persistence facts
the behaviour observes: whether the primary record has been written, whether a
deferred relational save was set up, and -- crucially -- whether the deferred
relational data has been written for THIS form. The first two are plain
booleans behind an abstraction predicate. The third is NOT a value an
implementation can compute or copy: it is an abstract per-form CAPABILITY
`relations_done(self)` -- an opaque predicate with no body. Because it has no
body, it cannot be folded into existence by fiat; because it names the specific
form `self`, a capability obtained for some OTHER form cannot stand in for it.
The ONLY producer of `relations_done(self)` is the deferred relational save's
contract: it grants the capability for the very form it ran on. So the
relational-data fact can become true for `self` ONLY by running the deferred
relational save on `self`. Three unchanged callees are axiomatized: the
base-form save (which sets up the deferred relational save and writes nothing),
the primary record write, and the deferred relational save itself. None of them
is the function under specification; each is the weakest contract the proof
needs. The deferred relational save additionally requires the primary record to
already exist, mirroring that the relational associations can be written only
once the record has a primary key -- and because the primary-record fact is
read-only to the routine, that condition is met only by having really performed
the record write, never by asserting it. The record object itself is tracked by
a second abstract per-form capability `record_available(self)`, which the form
already holds when the routine is entered: it identifies the one object every
persistence step acts on and that the routine hands back. Every step requires
it and every step preserves it, so it constrains no order -- the object is
there throughout -- it only records that all the steps and the returned value
concern that same object.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Form:
    """The form together with its model instance, folded into one object. The
    primary-record and deferred-save facts are held behind `form_pred` and are
    READ-ONLY to whoever holds it: the accessors below observe them, and no
    holder of the form has the write access needed to set either one. They move
    only when a step whose contract claims that effect is actually performed --
    the primary record write for the first, the base-form save for the second --
    so neither fact can be brought about by declaring it. The relational-data
    fact is grounded the same way and further still: it is not even a
    readable value but an abstract per-form capability
    `relations_done(self)`: a holder may carry it (in a postcondition) but can
    never bring it into existence by writing a field or folding a predicate, and
    a capability held for a DIFFERENT form does not discharge it for this one.
    Only the deferred relational save's contract grants `relations_done(self)`,
    so the relational-data fact for `self` can become true only by running the
    deferred relational save on `self`."""

    # pure-start
    @Predicate
    def form_pred(self) -> bool:
        # Abstraction over the observable persistence facts: the primary-record
        # and deferred-save booleans. Each is held at READ-ONLY permission, so a
        # holder of the form can observe both facts and set NEITHER: the only way
        # either becomes true is that the step which brings it about is actually
        # performed (the primary record write; the base-form save). This is what
        # makes "the primary record is written" mean the write happened rather
        # than that the routine said so -- and, because the deferred relational
        # save may run only once the record exists, it is also what stops that
        # ordering condition from being met by assertion instead of by the write.
        # The relational-data fact is NOT held here at all (it is the abstract
        # capability relations_done(self), produced solely by the deferred
        # relational save).
        return Acc(self.record_persisted, 1 / 2) and \
            Acc(self.deferred_save_ready, 1 / 2)

    @Pure
    def get_record(self) -> bool:
        Requires(Acc(self.form_pred(), 1 / 2))
        return Unfolding(Acc(self.form_pred(), 1 / 2), self.record_persisted)

    @Pure
    def get_ready(self) -> bool:
        Requires(Acc(self.form_pred(), 1 / 2))
        return Unfolding(Acc(self.form_pred(), 1 / 2), self.deferred_save_ready)
    # pure-end

    def __init__(self) -> None:
        Ensures(self.form_pred())                          # type: ignore
        Ensures(self.get_record() is False)                # type: ignore
        Ensures(self.get_ready() is False)                 # type: ignore
        self.record_persisted = False                      # type: bool
        self.deferred_save_ready = False                   # type: bool
        Fold(self.form_pred())

# axioms-start
@ContractOnly
@Predicate
def relations_done(self: Form) -> bool:
    # Abstract per-form capability: holding `relations_done(self)` means the
    # deferred relational data (the many-to-many associations) has been written
    # for THIS form. It is an opaque predicate with NO body. Consequences:
    # - an implementation cannot Fold it into existence (an abstract predicate
    #   has no body to fold), so the relational-data fact cannot be fabricated
    #   by fiat;
    # - it names the specific form `self`, so a capability obtained for some
    #   other (e.g. scratch) form is `relations_done(that_form)`, which does NOT
    #   discharge `relations_done(self)` -- it cannot be laundered across forms.
    # The SOLE producer is the deferred relational save's `Ensures` (it grants
    # the capability for the form it ran on). This is the directive-8 /
    # control-flow grounding of the relational-data fact: an unforgeable
    # capability token tied to the effect-producing step, not an answer-key
    # oracle on a result value and not a copyable field. Provenance + soundness
    # check: mapping.md / axiom_check.py.
    True

@ContractOnly
@Predicate
def record_available(self: Form) -> bool:
    # Abstract per-form capability naming this form's model RECORD OBJECT --
    # the object that the primary record write writes, that the deferred
    # relational save attaches the associations to, and that the routine hands
    # back. The form ALREADY HOLDS it on entry: it built that object from the
    # submitted data while validating, well before this routine runs, so there
    # is never a moment inside the routine at which the object is missing.
    # Accordingly every step requires it and every step preserves it, and the
    # routine both requires and returns it. It therefore forbids NO ordering of
    # the steps -- an implementation may act on the record object at any point --
    # it states only that one and the same object is what all of them, and the
    # returned value, are about. Like the relational-data capability it is an
    # opaque predicate with NO body and names the specific form `self`, so it
    # cannot be folded into existence and a capability held for some other form
    # does not stand in for it. Provenance: mapping.md / axiom_check.py.
    True

@ContractOnly
def base_form_save_deferred(self: Form) -> None:
    """The unchanged base-form save invoked in deferred mode: it hands back this
    form's model record object -- the object the form already holds, which it
    does not create -- and it sets up the deferred relational save for this
    form; it writes NOTHING (neither the primary record nor the relational
    data). It is the SOLE step whose contract claims the deferred relational
    save becomes set up, so `get_ready()` becomes true only by really running
    it. After it returns the deferred relational save is available to be run
    later. It does not grant the relational-data capability. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(self.get_ready() is True)
    Ensures(self.get_record() == Old(self.get_record()))

@ContractOnly
def persist_record(self: Form) -> None:
    """The unchanged write of the primary record. It writes the form's record
    object (`record_available(self)`) and leaves that object in place. It is the
    SOLE step whose contract claims the primary record becomes written, so
    `get_record()` becomes true only by really performing this write. It writes
    the primary record only; it does NOT write the deferred relational data (it
    does not grant the relational-data capability) and does NOT alter the
    deferred-save availability. Provenance + soundness check: mapping.md /
    axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(self.get_record() is True)
    Ensures(self.get_ready() == Old(self.get_ready()))

@ContractOnly
def run_deferred_save(self: Form) -> None:
    """The unchanged deferred relational save. It writes the deferred relational
    data (the many-to-many associations) for this form -- it is the SOLE
    producer of the per-form relational-data capability `relations_done(self)`.
    It attaches the associations to the form's record object
    (`record_available(self)`) and leaves that object in place. It may be run
    only when a deferred relational save was really set up AND the primary
    record has really been written (the relational associations are attached to
    the record's primary key) -- and because both of those facts are read-only
    to the routine, this condition can be reached only by having performed
    those steps, not by claiming them. Provenance + soundness check: mapping.md /
    axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(self.get_ready() is True)
    Requires(self.get_record() is True)
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(relations_done(self))
    Ensures(self.get_record() == Old(self.get_record()))
    Ensures(self.get_ready() == Old(self.get_ready()))
# axioms-end

# (the pure spec functions for this behaviour — the abstraction predicate
# form_pred and the accessors get_record/get_ready — live in the single `pure`
# region on the Form class above; the relational-data fact is the abstract
# capability relations_done declared in the axioms region.)

def save_form(self: Form, commit: bool) -> Form:
    # pre-conditions-start
    Requires(self.form_pred())
    # Entry state: the primary record has not been written yet -- this is the
    # routine that writes it, and it is what makes the record clauses below
    # claims about a write this routine performed.
    Requires(self.get_record() is False)
    # Whether a deferred relational save is ALREADY set up for the form on entry
    # is deliberately NOT constrained: both entry states are ordinary (deferring
    # is what leaves one set up, and the same form may afterwards be asked to
    # persist immediately), so every guarantee below is owed on both. In
    # particular the routine may not read the entry state as a licence to skip
    # either part of the persistence.
    # The form already holds its model record object when the routine is
    # entered -- it built that object from the submitted data while validating.
    # So the object every persistence step acts on, and that the routine hands
    # back, is available throughout; the routine is free to act on it whenever.
    Requires(record_available(self))
    # The routine performs a bounded amount of work and does NOT re-invoke
    # itself; this termination obligation pins that. It forbids discharging the
    # postcondition "for free" by echoing this routine's own contract: a self
    # call would have to take the very same obligation without a strictly
    # smaller measure and is rejected. So the relational-data guarantee can be
    # obtained only by actually running the deferred relational save on self,
    # never by re-deriving the contract from itself. The callees the routine
    # invokes carry a strictly smaller measure (1), so they are allowed.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(self.form_pred())
    Ensures(Result() is self)
    # The record object is handed back intact: every persistence step the
    # routine performs acts on the form's one record object, and that same
    # object is what the routine returns.
    Ensures(record_available(self))
    # A deferred relational save is always set up for the form.
    Ensures(self.get_ready() is True)
    # (1) Immediate persistence writes the primary record -- and this is a
    # claim about the write having happened, not a flag the routine may set: the
    # primary-record fact is read-only to the routine, so the only way to leave
    # it true is to have really performed the primary record write on the record
    # object. (It is also what the deferred relational save's own
    # already-written condition tests, so that condition too can be met only by
    # the real write.)
    Ensures(Implies(commit, self.get_record() is True))
    # (2) ... AND writes the deferred relational data (the discriminating
    # guarantee: committing must leave the relational associations persisted for
    # THIS form — dischargeable ONLY by running the deferred relational save on
    # self, since the relational-data fact is the abstract per-form capability
    # relations_done(self) and there is no other way to obtain it: it cannot be
    # folded by fiat and a capability for another form does not stand in for it).
    Ensures(Implies(commit, relations_done(self)))
    # Without immediate persistence nothing is written -- and, the fact being
    # read-only, an implementation that did perform the write cannot get back
    # under this clause by resetting the fact afterwards.
    Ensures(Implies(not commit, self.get_record() is False))
    # post-conditions-end
    # impl-start
    base_form_save_deferred(self)
    # (the password assignment of the routine has no tracked persistence effect)
    if commit:
        persist_record(self)
        if self.get_ready():
            run_deferred_save(self)
    return self
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** A-legs (axioms / deep-model refs) + model<->patch correspondence; R/I legs left to G-CONF as instructed.

**POSITIVE CONTROL:** pos_control.py (gold impl region verbatim) -> `bash scripts/nagini_verify.sh` => "Verification successful" (9.42s), exit 0.

### VACUITY CONTROLS (my own, beyond protocol):
- ctl_vacuity.py = gold impl + trailing Assert(False) -> FAILS "Assert might fail. Assertion False might not hold." So the postcondition is discharged on a live path, not vacuously.
- ctl_atk13_branch_live.py = atk_13 with Assert(False) in the already-ready branch -> FAILS at 313:16. Confirms atk_13's skipped-base-save branch is REACHABLE, i.e. it did not verify by an infeasible guard (cf. the guarded-self-call vacuity trap).

ALL 18 ATTACKS: same-spec exit 0 (byte-identical spec view) for every file, incl. pos_control. Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-16333 <path>`; raw reasons via `bash scripts/nagini_verify.sh <path>`. Verifications were run 3-at-a-time as background jobs (JVM+Z3 per check); schedule only, every attack fully verified.

1 atk_1_fiat_record (prior-pass BROKEN counterexample, re-encoded: Unfold/assign record_persisted/Fold + real deferred save) -> exit 2. "Assignment might fail. There might be insufficient permission to access self.record_persisted." The Acc(...,1/2) read-only split repaired the exact defect the last G-EQ recorded as BROKEN. 2 atk_2_prepatch (prepatch bug; no deferred save) -> exit 2. "Postcondition ... insufficient permission to access relations_done(self)" = PREPATCH BUG REPRODUCED (matches G-DIFF's model_prepatch.py failure).

3 atk_3_shortcircuit_ready (partial domain: return early if already ready) -> exit 2. "Implies(commit, (self.get_record() is True)) might not hold." 4 atk_4_fiat_fold (Fold(relations_done(self))) -> exit 2. Translation failed: "Invalid program: abstract.predicate.fold" — the front end refused the program, so the spec never ruled on it and it counts in neither tally. A body-less predicate cannot be conjured, which closes the forgery below the clause level rather than by one of them. 5 atk_5_scratch_launder (run real deferred save on a throwaway Form, reuse its capability) -> exit 2, but NOTE the reason is "Obligation leak check failed.

Callee `__init__` might not take all unsatisfied obligations from the caller" — i.e. MustTerminate blocks Form() construction BEFORE the capability-binding argument is reached. Rejected, but not for the reason refinement.md §C credits ("insufficient permission to access relations_done(self)"). Same for atk_16. Documentation imprecision, not a spec hole: atk_4 independently shows relations_done cannot be forged, and the per-form parameterisation is structurally sound. 6 atk_6_selfecho (return save_form(self, commit)) -> exit 2. "Obligation leak check failed. Callee save_form might not take all unsatisfied obligations from the caller." MustTerminate(2) vs (1) closes the self-echo exactly as documented (DEFECT-5).

7 atk_7_raise_on_ready -> exit 2, Translation failed "Unsupported builtin function" (Nagini cannot translate bare `raise ValueError()`). TOOLING LIMIT, not a spec rejection — covered instead by atk_14 below. 8 atk_8_m2m_before_record (deferred save then record write) -> exit 2. "precondition of run_deferred_save might not hold. Assertion (self.get_record() is True)" — mirrors the real ValueError (no pk yet), validated by axiom_check.py's trial-0 negative observation. 9 atk_9_uncond_persist -> exit 2. "Implies((not commit), (self.get_record() is False)) might not hold." 10 atk_10_prepatch_on_ready_half (prepatch bug restricted to the re-entered half) -> exit 2. "insufficient permission to access relations_done(self)".

This is the leg the free entry fact exists to reach; it is genuinely reached. 11 atk_11_raise_not_commit -> exit 2, Translation failed "Unsupported builtin function" (same raise limitation). Superseded by atk_14. 12 atk_12_diverge_not_commit (while True on the deferred half) -> exit 2. "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." Confirms MustTerminate reaches the loop only because the entry fact is free (matches refinement.md §C).

13 atk_13_skip_base_when_ready -> exit 0 CANDIDATE (12.0s) -> MANDATORY RESOLVE RUN: patch patch_atk_13.diff (git apply --check clean at base_commit 60a7bd89), `run_resolve('django__django-16333', patch, run_id='sbu-eq-audit-atk13')` => RESOLVED=True, COMPLETED=True, ATTEMPTS=1, note="resolved", patch_successfully_applied=true, FAIL_TO_PASS 1/1 success 0 failures, PASS_TO_PASS 87/87 success 0 failures. DOES NOT BREAK THE SPEC — correct alternative impl. 14 atk_14_raise_after_commit (control-flow effect via Nagini-translatable `raise Exception()` after the gold work) -> exit 2. "Exhale might fail. Assertion \"method raises no exceptions\" might not hold." The exceptional-exit family IS closed by the spec; attacks 7/11 only hit a translator limit.

15 atk_15_no_base_save_ever -> exit 2. "precondition of run_deferred_save ... (self.get_ready() is True) might not hold." 16 atk_16_spurious_extra_record (gold work + spurious extra persisted record) -> exit 2, via the same `__init__` obligation-leak route as atk_5. 17 atk_17_no_handle_when_deferred (return before base save when not committing) -> exit 2. "Postcondition ... (self.get_ready() is True) might not hold." The always-set-up-the-handle clause bites. 18 atk_18_double_effects (every effect performed twice) -> exit 0 CANDIDATE (12.7s) -> MANDATORY RESOLVE RUN: patch patch_atk_18.diff (applies clean), `run_resolve(..., run_id='sbu-eq-audit-atk18')` => RESOLVED=True, COMPLETED=True, ATTEMPTS=1, note="resolved", FAIL_TO_PASS 1/1, PASS_TO_PASS 87/87, 0 failures. DOES NOT BREAK THE SPEC.

REFINEMENT.MD LEG AUDIT (kind-3 check): legs A1..A7 are tagged A-consumed/R/I with no kind-3 — confirmed against the gold hunk. meta.json['axioms'] declares 5 symbols: base_form_save_deferred / persist_record / run_deferred_save (A-consumed) + relations_done / record_available (A-reference); deep_model_references is []. Every tag is one of R / A-consumed / A-reference / I. Correspondence of the A-consumed legs checked against the real repo at base_commit: A1 <-> BaseModelForm.save commit=False else-branch (django/forms/models.py:544-547 `self.save_m2m = self._save_m2m; return self.instance`) — installs the handle, writes nothing: axiom matches, and the flag_dependency on commit=False is correctly recorded (the commit=True branch would itself persist).

A4 <-> Model.save() / AbstractBaseUser.save — writes the row, never the m2m through-rows: matches. A6 <-> save_m2m == BaseModelForm.`_save_m2m` (iterates opts.many_to_many + private_fields, calls f.save_form_data(self.instance, cleaned_data[f.name])) — writes exactly the submitted associations: matches, and its Requires(get_record() is True) is the weakest precondition excluding the raising (pk-is-None) configuration, exercised as a negative observation by axiom_check.py trial 0. A-reference relations_done/record_available have no separate callee and are grounded structurally (body-less, per-form); their single real-world claim (m2m unwritten until save_m2m runs) is asserted by axiom_check.py's relations_written() observations across all three steps.

A2 (`user.set_password(...)`) is tagged R with no model node; verified harmless to the modeled state — set_password only sets self.password/self.`_password`, and the password_changed hook fires inside AbstractBaseUser.save, so it touches none of the three persistence facts. Its position relative to `user.save()` is preserved in both materialized patches, so test_success's password_changed.call_count assertion is unaffected.

### DISCREPANCIES FOUND (documentation-level, no spec weakness; both machine-checked above):
(a) refinement.md §C credits the token-transfer defence with "insufficient permission to access relations_done(self)", but on the frozen spec that shape (atk_5/atk_16) is actually rejected earlier, by a MustTerminate obligation leak on Form.`__init__`. The claimed defence is never exercised by that attack. Recommend re-wording, or re-measuring with a pre-existing scratch form.
(b) refinement.md §C lists exceptional-exit variants as covered; on this Nagini build bare `raise ValueError()` does not translate at all (atk_7/atk_11), so that family is only genuinely tested by the `raise Exception()` shape (atk_14), which does fail correctly.

**VERDICT SOUND:** >=5 distinct wrong impls run (18 total, spanning partial-domain, boundary, control-flow-effect/divergence/exception, ungrounded-oracle fiat and echo, ordering, unconditional-persist, self-echo, extra-object and repeated-effect classes); the prepatch bug reproduced; the prior pass's BROKEN counterexample now rejected; positive control verifies; vacuity controls fail as they must; and every CANDIDATE's faithful patch was ACTUALLY RUN through the official harness and RESOLVED. No verify-but-not-resolve witness exists among these attacks.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies (3 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1_fiat_record.py`, `atk_2_prepatch.py`, `atk_3_shortcircuit_ready.py`, `atk_5_scratch_launder.py`, `atk_6_selfecho.py`, `atk_8_m2m_before_record.py`, `atk_9_uncond_persist.py`, `atk_10_prepatch_on_ready_half.py`, `atk_12_diverge_not_commit.py`, `atk_14_raise_after_commit.py`, `atk_15_no_base_save_ever.py`, +2 more |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 3 | `atk_4_fiat_fold.py`, `atk_7_raise_on_ready.py`, `atk_11_raise_not_commit.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_13_skip_base_when_ready.py`, `atk_18_double_effects.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl found. 18 same-spec attacks run on the real Nagini verifier: 16 REJECTED, 2 CANDIDATEs (verify + share spec), and BOTH candidates' materialized faithful patches RESOLVED under the official harness (F2P 1/1, P2P 87/87, patch applied, 1 attempt each), so neither is a verify-but-incorrect witness. atk_13_skip_base_when_ready (skip the base-form save when the m2m handle is already installed, leaning on the free entry fact for Ensures(get_ready())) is a genuinely correct alternative implementation: refinement.md §B's claim that base_form_save_deferred BINDS but does not PRODUCE the record object is factually right (BaseModelForm._post_clean -> construct_instance builds self.instance during validation), so `user = self.instance` on the already-ready branch is the faithful refinement and it persists both parts. atk_18_double_effects (duplicated base save / record write / deferred save) is admitted because the boolean+capability abstraction is idempotent, and the real callees are idempotent on the tested inputs too (Model.save() re-UPDATEs the same row; _save_m2m re-sets the same association set) — it resolved.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_fiat_record.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_prepatch.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_shortcircuit_ready.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_fiat_fold.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 5 — `atk_5_scratch_launder.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_selfecho.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_raise_on_ready.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 8 — `atk_8_m2m_before_record.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_uncond_persist.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_prepatch_on_ready_half.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_raise_not_commit.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 12 — `atk_12_diverge_not_commit.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_skip_base_when_ready.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14_raise_after_commit.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_no_base_save_ever.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_spurious_extra_record.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_no_handle_when_deferred.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18_double_effects.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16333.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A user-creation routine persists a submitted form. Persisting a form happens
  in two parts: the primary record itself, and the form's deferred relational
  data (the many-to-many associations, whose persistence the underlying
  base-form save defers so it can be run after the primary record exists).

  When the routine is asked to persist immediately, BOTH parts must end up
  persisted once it returns:

    (1) the primary record is written, and

    (2) whenever a deferred relational save was set up for this form, that
        deferred save is run too, so the many-to-many associations are written.

  When the routine is NOT asked to persist immediately, nothing is written, but
  the deferred relational save is still set up so a later caller can run it.

  Those two guarantees hold whatever a caller did to the form before. Deferring
  is exactly what leaves a deferred relational save set up, so a caller that
  first asks for deferred persistence and afterwards asks for immediate
  persistence enters the routine on a form that ALREADY has one set up. That
  entry state is ordinary, and the routine owes the same thing on it: asked to
  persist immediately it must still write the primary record and must still
  leave the deferred relational data written for the form, exactly as when it is
  entered on a form nobody has persisted through yet. How the form arrived is
  not a reason for either part of the persistence to be missing.

  Both persistence steps act on the form's model RECORD OBJECT. That object is
  already available when the routine is entered -- the form holds it, having
  built it from the submitted data while validating -- so every step of the
  routine may act on it, and the object the routine hands back is that same
  one. The base-form save returns it; it is not what brings it into existence.

  Nothing the routine can say makes either part of the persistence true. The
  primary record counts as written only once the primary record write has
  actually been performed on the record object, and a deferred relational save
  counts as set up only once the base-form save has actually set one up.
  Whoever holds the form may READ those two facts but cannot set them: each
  changes only by performing the step that brings it about. The relational-data
  fact is grounded the same way, and more strongly still (below). So
  "persisted" here always means the persisting step ran -- never that the
  routine declared it so.

The form is modelled as a minimal object carrying only the persistence facts
the behaviour observes: whether the primary record has been written, whether a
deferred relational save was set up, and -- crucially -- whether the deferred
relational data has been written for THIS form. The first two are plain
booleans behind an abstraction predicate. The third is NOT a value an
implementation can compute or copy: it is an abstract per-form CAPABILITY
`relations_done(self)` -- an opaque predicate with no body. Because it has no
body, it cannot be folded into existence by fiat; because it names the specific
form `self`, a capability obtained for some OTHER form cannot stand in for it.
The ONLY producer of `relations_done(self)` is the deferred relational save's
contract: it grants the capability for the very form it ran on. So the
relational-data fact can become true for `self` ONLY by running the deferred
relational save on `self`. Three unchanged callees are axiomatized: the
base-form save (which sets up the deferred relational save and writes nothing),
the primary record write, and the deferred relational save itself. None of them
is the function under specification; each is the weakest contract the proof
needs. The deferred relational save additionally requires the primary record to
already exist, mirroring that the relational associations can be written only
once the record has a primary key -- and because the primary-record fact is
read-only to the routine, that condition is met only by having really performed
the record write, never by asserting it. The record object itself is tracked by
a second abstract per-form capability `record_available(self)`, which the form
already holds when the routine is entered: it identifies the one object every
persistence step acts on and that the routine hands back. Every step requires
it and every step preserves it, so it constrains no order -- the object is
there throughout -- it only records that all the steps and the returned value
concern that same object.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Form:
    """The form together with its model instance, folded into one object. The
    primary-record and deferred-save facts are held behind `form_pred` and are
    READ-ONLY to whoever holds it: the accessors below observe them, and no
    holder of the form has the write access needed to set either one. They move
    only when a step whose contract claims that effect is actually performed --
    the primary record write for the first, the base-form save for the second --
    so neither fact can be brought about by declaring it. The relational-data
    fact is grounded the same way and further still: it is not even a
    readable value but an abstract per-form capability
    `relations_done(self)`: a holder may carry it (in a postcondition) but can
    never bring it into existence by writing a field or folding a predicate, and
    a capability held for a DIFFERENT form does not discharge it for this one.
    Only the deferred relational save's contract grants `relations_done(self)`,
    so the relational-data fact for `self` can become true only by running the
    deferred relational save on `self`."""

    # pure-start
    @Predicate
    def form_pred(self) -> bool:
        # Abstraction over the observable persistence facts: the primary-record
        # and deferred-save booleans. Each is held at READ-ONLY permission, so a
        # holder of the form can observe both facts and set NEITHER: the only way
        # either becomes true is that the step which brings it about is actually
        # performed (the primary record write; the base-form save). This is what
        # makes "the primary record is written" mean the write happened rather
        # than that the routine said so -- and, because the deferred relational
        # save may run only once the record exists, it is also what stops that
        # ordering condition from being met by assertion instead of by the write.
        # The relational-data fact is NOT held here at all (it is the abstract
        # capability relations_done(self), produced solely by the deferred
        # relational save).
        return Acc(self.record_persisted, 1 / 2) and \
            Acc(self.deferred_save_ready, 1 / 2)

    @Pure
    def get_record(self) -> bool:
        Requires(Acc(self.form_pred(), 1 / 2))
        return Unfolding(Acc(self.form_pred(), 1 / 2), self.record_persisted)

    @Pure
    def get_ready(self) -> bool:
        Requires(Acc(self.form_pred(), 1 / 2))
        return Unfolding(Acc(self.form_pred(), 1 / 2), self.deferred_save_ready)
    # pure-end

    def __init__(self) -> None:
        Ensures(self.form_pred())                          # type: ignore
        Ensures(self.get_record() is False)                # type: ignore
        Ensures(self.get_ready() is False)                 # type: ignore
        self.record_persisted = False                      # type: bool
        self.deferred_save_ready = False                   # type: bool
        Fold(self.form_pred())

# axioms-start
@ContractOnly
@Predicate
def relations_done(self: Form) -> bool:
    # Abstract per-form capability: holding `relations_done(self)` means the
    # deferred relational data (the many-to-many associations) has been written
    # for THIS form. It is an opaque predicate with NO body. Consequences:
    # - an implementation cannot Fold it into existence (an abstract predicate
    #   has no body to fold), so the relational-data fact cannot be fabricated
    #   by fiat;
    # - it names the specific form `self`, so a capability obtained for some
    #   other (e.g. scratch) form is `relations_done(that_form)`, which does NOT
    #   discharge `relations_done(self)` -- it cannot be laundered across forms.
    # The SOLE producer is the deferred relational save's `Ensures` (it grants
    # the capability for the form it ran on). This is the directive-8 /
    # control-flow grounding of the relational-data fact: an unforgeable
    # capability token tied to the effect-producing step, not an answer-key
    # oracle on a result value and not a copyable field. Provenance + soundness
    # check: mapping.md / axiom_check.py.
    True

@ContractOnly
@Predicate
def record_available(self: Form) -> bool:
    # Abstract per-form capability naming this form's model RECORD OBJECT --
    # the object that the primary record write writes, that the deferred
    # relational save attaches the associations to, and that the routine hands
    # back. The form ALREADY HOLDS it on entry: it built that object from the
    # submitted data while validating, well before this routine runs, so there
    # is never a moment inside the routine at which the object is missing.
    # Accordingly every step requires it and every step preserves it, and the
    # routine both requires and returns it. It therefore forbids NO ordering of
    # the steps -- an implementation may act on the record object at any point --
    # it states only that one and the same object is what all of them, and the
    # returned value, are about. Like the relational-data capability it is an
    # opaque predicate with NO body and names the specific form `self`, so it
    # cannot be folded into existence and a capability held for some other form
    # does not stand in for it. Provenance: mapping.md / axiom_check.py.
    True

@ContractOnly
def base_form_save_deferred(self: Form) -> None:
    """The unchanged base-form save invoked in deferred mode: it hands back this
    form's model record object -- the object the form already holds, which it
    does not create -- and it sets up the deferred relational save for this
    form; it writes NOTHING (neither the primary record nor the relational
    data). It is the SOLE step whose contract claims the deferred relational
    save becomes set up, so `get_ready()` becomes true only by really running
    it. After it returns the deferred relational save is available to be run
    later. It does not grant the relational-data capability. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(self.get_ready() is True)
    Ensures(self.get_record() == Old(self.get_record()))

@ContractOnly
def persist_record(self: Form) -> None:
    """The unchanged write of the primary record. It writes the form's record
    object (`record_available(self)`) and leaves that object in place. It is the
    SOLE step whose contract claims the primary record becomes written, so
    `get_record()` becomes true only by really performing this write. It writes
    the primary record only; it does NOT write the deferred relational data (it
    does not grant the relational-data capability) and does NOT alter the
    deferred-save availability. Provenance + soundness check: mapping.md /
    axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(self.get_record() is True)
    Ensures(self.get_ready() == Old(self.get_ready()))

@ContractOnly
def run_deferred_save(self: Form) -> None:
    """The unchanged deferred relational save. It writes the deferred relational
    data (the many-to-many associations) for this form -- it is the SOLE
    producer of the per-form relational-data capability `relations_done(self)`.
    It attaches the associations to the form's record object
    (`record_available(self)`) and leaves that object in place. It may be run
    only when a deferred relational save was really set up AND the primary
    record has really been written (the relational associations are attached to
    the record's primary key) -- and because both of those facts are read-only
    to the routine, this condition can be reached only by having performed
    those steps, not by claiming them. Provenance + soundness check: mapping.md /
    axiom_check.py.
    """
    Requires(self.form_pred())
    Requires(record_available(self))
    Requires(self.get_ready() is True)
    Requires(self.get_record() is True)
    Requires(MustTerminate(1))
    Ensures(self.form_pred())
    Ensures(record_available(self))
    Ensures(relations_done(self))
    Ensures(self.get_record() == Old(self.get_record()))
    Ensures(self.get_ready() == Old(self.get_ready()))
# axioms-end

# (the pure spec functions for this behaviour — the abstraction predicate
# form_pred and the accessors get_record/get_ready — live in the single `pure`
# region on the Form class above; the relational-data fact is the abstract
# capability relations_done declared in the axioms region.)

def save_form(self: Form, commit: bool) -> Form:
    # pre-conditions-start
    Requires(self.form_pred())
    # Entry state: the primary record has not been written yet -- this is the
    # routine that writes it, and it is what makes the record clauses below
    # claims about a write this routine performed.
    Requires(self.get_record() is False)
    # Whether a deferred relational save is ALREADY set up for the form on entry
    # is deliberately NOT constrained: both entry states are ordinary (deferring
    # is what leaves one set up, and the same form may afterwards be asked to
    # persist immediately), so every guarantee below is owed on both. In
    # particular the routine may not read the entry state as a licence to skip
    # either part of the persistence.
    # The form already holds its model record object when the routine is
    # entered -- it built that object from the submitted data while validating.
    # So the object every persistence step acts on, and that the routine hands
    # back, is available throughout; the routine is free to act on it whenever.
    Requires(record_available(self))
    # The routine performs a bounded amount of work and does NOT re-invoke
    # itself; this termination obligation pins that. It forbids discharging the
    # postcondition "for free" by echoing this routine's own contract: a self
    # call would have to take the very same obligation without a strictly
    # smaller measure and is rejected. So the relational-data guarantee can be
    # obtained only by actually running the deferred relational save on self,
    # never by re-deriving the contract from itself. The callees the routine
    # invokes carry a strictly smaller measure (1), so they are allowed.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(self.form_pred())
    Ensures(Result() is self)
    # The record object is handed back intact: every persistence step the
    # routine performs acts on the form's one record object, and that same
    # object is what the routine returns.
    Ensures(record_available(self))
    # A deferred relational save is always set up for the form.
    Ensures(self.get_ready() is True)
    # (1) Immediate persistence writes the primary record -- and this is a
    # claim about the write having happened, not a flag the routine may set: the
    # primary-record fact is read-only to the routine, so the only way to leave
    # it true is to have really performed the primary record write on the record
    # object. (It is also what the deferred relational save's own
    # already-written condition tests, so that condition too can be met only by
    # the real write.)
    Ensures(Implies(commit, self.get_record() is True))
    # (2) ... AND writes the deferred relational data (the discriminating
    # guarantee: committing must leave the relational associations persisted for
    # THIS form — dischargeable ONLY by running the deferred relational save on
    # self, since the relational-data fact is the abstract per-form capability
    # relations_done(self) and there is no other way to obtain it: it cannot be
    # folded by fiat and a capability for another form does not stand in for it).
    Ensures(Implies(commit, relations_done(self)))
    # Without immediate persistence nothing is written -- and, the fact being
    # read-only, an implementation that did perform the write cannot get back
    # under this clause by resetting the fact afterwards.
    Ensures(Implies(not commit, self.get_record() is False))
    # post-conditions-end
    # impl-start
    base_form_save_deferred(self)
    # (the password assignment of the routine has no tracked persistence effect)
    if commit:
        persist_record(self)
        if self.get_ready():
            run_deferred_save(self)
    return self
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** A-legs (axioms / deep-model refs) + model<->patch correspondence; R/I legs left to G-CONF as instructed.

**POSITIVE CONTROL:** pos_control.py (gold impl region verbatim) -> `bash scripts/nagini_verify.sh` => "Verification successful" (9.42s), exit 0.

### VACUITY CONTROLS (my own, beyond protocol):
- ctl_vacuity.py = gold impl + trailing Assert(False) -> FAILS "Assert might fail. Assertion False might not hold." So the postcondition is discharged on a live path, not vacuously.
- ctl_atk13_branch_live.py = atk_13 with Assert(False) in the already-ready branch -> FAILS at 313:16. Confirms atk_13's skipped-base-save branch is REACHABLE, i.e. it did not verify by an infeasible guard (cf. the guarded-self-call vacuity trap).

ALL 18 ATTACKS: same-spec exit 0 (byte-identical spec view) for every file, incl. pos_control. Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-16333 <path>`; raw reasons via `bash scripts/nagini_verify.sh <path>`. Verifications were run 3-at-a-time as background jobs (JVM+Z3 per check); schedule only, every attack fully verified.

1 atk_1_fiat_record (prior-pass BROKEN counterexample, re-encoded: Unfold/assign record_persisted/Fold + real deferred save) -> exit 2. "Assignment might fail. There might be insufficient permission to access self.record_persisted." The Acc(...,1/2) read-only split repaired the exact defect the last G-EQ recorded as BROKEN. 2 atk_2_prepatch (prepatch bug; no deferred save) -> exit 2. "Postcondition ... insufficient permission to access relations_done(self)" = PREPATCH BUG REPRODUCED (matches G-DIFF's model_prepatch.py failure).

3 atk_3_shortcircuit_ready (partial domain: return early if already ready) -> exit 2. "Implies(commit, (self.get_record() is True)) might not hold." 4 atk_4_fiat_fold (Fold(relations_done(self))) -> exit 2. Translation failed: "Invalid program: abstract.predicate.fold" — the front end refused the program, so the spec never ruled on it and it counts in neither tally. A body-less predicate cannot be conjured, which closes the forgery below the clause level rather than by one of them. 5 atk_5_scratch_launder (run real deferred save on a throwaway Form, reuse its capability) -> exit 2, but NOTE the reason is "Obligation leak check failed.

Callee `__init__` might not take all unsatisfied obligations from the caller" — i.e. MustTerminate blocks Form() construction BEFORE the capability-binding argument is reached. Rejected, but not for the reason refinement.md §C credits ("insufficient permission to access relations_done(self)"). Same for atk_16. Documentation imprecision, not a spec hole: atk_4 independently shows relations_done cannot be forged, and the per-form parameterisation is structurally sound. 6 atk_6_selfecho (return save_form(self, commit)) -> exit 2. "Obligation leak check failed. Callee save_form might not take all unsatisfied obligations from the caller." MustTerminate(2) vs (1) closes the self-echo exactly as documented (DEFECT-5).

7 atk_7_raise_on_ready -> exit 2, Translation failed "Unsupported builtin function" (Nagini cannot translate bare `raise ValueError()`). TOOLING LIMIT, not a spec rejection — covered instead by atk_14 below. 8 atk_8_m2m_before_record (deferred save then record write) -> exit 2. "precondition of run_deferred_save might not hold. Assertion (self.get_record() is True)" — mirrors the real ValueError (no pk yet), validated by axiom_check.py's trial-0 negative observation. 9 atk_9_uncond_persist -> exit 2. "Implies((not commit), (self.get_record() is False)) might not hold." 10 atk_10_prepatch_on_ready_half (prepatch bug restricted to the re-entered half) -> exit 2. "insufficient permission to access relations_done(self)".

This is the leg the free entry fact exists to reach; it is genuinely reached. 11 atk_11_raise_not_commit -> exit 2, Translation failed "Unsupported builtin function" (same raise limitation). Superseded by atk_14. 12 atk_12_diverge_not_commit (while True on the deferred half) -> exit 2. "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." Confirms MustTerminate reaches the loop only because the entry fact is free (matches refinement.md §C).

13 atk_13_skip_base_when_ready -> exit 0 CANDIDATE (12.0s) -> MANDATORY RESOLVE RUN: patch patch_atk_13.diff (git apply --check clean at base_commit 60a7bd89), `run_resolve('django__django-16333', patch, run_id='sbu-eq-audit-atk13')` => RESOLVED=True, COMPLETED=True, ATTEMPTS=1, note="resolved", patch_successfully_applied=true, FAIL_TO_PASS 1/1 success 0 failures, PASS_TO_PASS 87/87 success 0 failures. DOES NOT BREAK THE SPEC — correct alternative impl. 14 atk_14_raise_after_commit (control-flow effect via Nagini-translatable `raise Exception()` after the gold work) -> exit 2. "Exhale might fail. Assertion \"method raises no exceptions\" might not hold." The exceptional-exit family IS closed by the spec; attacks 7/11 only hit a translator limit.

15 atk_15_no_base_save_ever -> exit 2. "precondition of run_deferred_save ... (self.get_ready() is True) might not hold." 16 atk_16_spurious_extra_record (gold work + spurious extra persisted record) -> exit 2, via the same `__init__` obligation-leak route as atk_5. 17 atk_17_no_handle_when_deferred (return before base save when not committing) -> exit 2. "Postcondition ... (self.get_ready() is True) might not hold." The always-set-up-the-handle clause bites. 18 atk_18_double_effects (every effect performed twice) -> exit 0 CANDIDATE (12.7s) -> MANDATORY RESOLVE RUN: patch patch_atk_18.diff (applies clean), `run_resolve(..., run_id='sbu-eq-audit-atk18')` => RESOLVED=True, COMPLETED=True, ATTEMPTS=1, note="resolved", FAIL_TO_PASS 1/1, PASS_TO_PASS 87/87, 0 failures. DOES NOT BREAK THE SPEC.

REFINEMENT.MD LEG AUDIT (kind-3 check): legs A1..A7 are tagged A-consumed/R/I with no kind-3 — confirmed against the gold hunk. meta.json['axioms'] declares 5 symbols: base_form_save_deferred / persist_record / run_deferred_save (A-consumed) + relations_done / record_available (A-reference); deep_model_references is []. Every tag is one of R / A-consumed / A-reference / I. Correspondence of the A-consumed legs checked against the real repo at base_commit: A1 <-> BaseModelForm.save commit=False else-branch (django/forms/models.py:544-547 `self.save_m2m = self._save_m2m; return self.instance`) — installs the handle, writes nothing: axiom matches, and the flag_dependency on commit=False is correctly recorded (the commit=True branch would itself persist).

A4 <-> Model.save() / AbstractBaseUser.save — writes the row, never the m2m through-rows: matches. A6 <-> save_m2m == BaseModelForm.`_save_m2m` (iterates opts.many_to_many + private_fields, calls f.save_form_data(self.instance, cleaned_data[f.name])) — writes exactly the submitted associations: matches, and its Requires(get_record() is True) is the weakest precondition excluding the raising (pk-is-None) configuration, exercised as a negative observation by axiom_check.py trial 0. A-reference relations_done/record_available have no separate callee and are grounded structurally (body-less, per-form); their single real-world claim (m2m unwritten until save_m2m runs) is asserted by axiom_check.py's relations_written() observations across all three steps.

A2 (`user.set_password(...)`) is tagged R with no model node; verified harmless to the modeled state — set_password only sets self.password/self.`_password`, and the password_changed hook fires inside AbstractBaseUser.save, so it touches none of the three persistence facts. Its position relative to `user.save()` is preserved in both materialized patches, so test_success's password_changed.call_count assertion is unaffected.

### DISCREPANCIES FOUND (documentation-level, no spec weakness; both machine-checked above):
(a) refinement.md §C credits the token-transfer defence with "insufficient permission to access relations_done(self)", but on the frozen spec that shape (atk_5/atk_16) is actually rejected earlier, by a MustTerminate obligation leak on Form.`__init__`. The claimed defence is never exercised by that attack. Recommend re-wording, or re-measuring with a pre-existing scratch form.
(b) refinement.md §C lists exceptional-exit variants as covered; on this Nagini build bare `raise ValueError()` does not translate at all (atk_7/atk_11), so that family is only genuinely tested by the `raise Exception()` shape (atk_14), which does fail correctly.

**VERDICT SOUND:** >=5 distinct wrong impls run (18 total, spanning partial-domain, boundary, control-flow-effect/divergence/exception, ungrounded-oracle fiat and echo, ordering, unconditional-persist, self-echo, extra-object and repeated-effect classes); the prepatch bug reproduced; the prior pass's BROKEN counterexample now rejected; positive control verifies; vacuity controls fail as they must; and every CANDIDATE's faithful patch was ACTUALLY RUN through the official harness and RESOLVED. No verify-but-not-resolve witness exists among these attacks.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: find an input where the modeled save_form disagrees with the REAL gold-patched UserCreationForm.save (spec too strong / drifted). NONE FOUND across every admitted entry state.

**SETUP.** Bundle model.py verifies on the pinned verifier (scripts/nagini_verify.sh, exit 0, 10.7s). same-spec on the unmodified model.py => SAME. Spec region hashes present in meta.json. Reference used for the modeled function = repo with the gold patch APPLIED (per instructions): I applied the gold hunk (the two added lines `if hasattr(self,"save_m2m"): self.save_m2m()`) inside the real testbed container swebench/sweb.eval.x86_64.django_1776_django-16333 (git apply OK, verified by sed of forms.py:139-146). Base commit worktree 60a7bd8986 used as the reference for the three untouched callees (what the axioms model).

PROBE 1 - all four postconditions vs the real patched function, fresh entry (get_record False, get_ready False): commit=True and commit=False, m2m-required and blank-m2m shapes. Checked Result() is self <=> (user is form.instance); Ensures(get_ready() is True) <=> hasattr(form,'save_m2m'); Implies(commit, get_record()) <=> row exists; Implies(commit, relations_done(self)) <=> real `_save_m2m` invoked for THIS form (counter in an override delegating to the real BaseModelForm.`_save_m2m`); Implies(not commit, get_record() is False). 0 divergences.

PROBE 2 - the RE-ENTERED entry state, which is the half the precondition deliberately leaves free (get_ready() already True at entry). Drove save(commit=False) then save(commit=True); also commit=False on a re-entered form; blank-m2m re-entered; and triple re-entry (defer, defer, commit). Every clause held on the real patched function, and the associations were genuinely persisted (user.orgs == [org]). 0 divergences. This is exactly the state auth_tests.test_forms.UserCreationFormTest.test_success drives (test_forms.py:123-125: form.save(commit=False) then form.save()), so leaving it free makes the spec claim MORE, not less.

PROBE 3 - is Requires(get_record() is False) a faithful narrowing or gratuitous over-fitting? Measured: after save(commit=True), a subsequent save(commit=False) leaves get_record()==True on the real function, which would VIOLATE Ensures(Implies(not commit, get_record() is False)). So the precondition is LOAD-BEARING for faithfulness (a deferred request cannot un-write an existing row) rather than a domain trimmed to dodge a clause. It also cannot hide the bug: the discriminating clause sits on commit=True, and the F2P test calls save(commit=True) on a fresh form, squarely inside the domain.

PROBE 4 - axiom faithfulness against the real UNPATCHED callees (the patch does not touch them), each Ensures re-checked on live ORM state: base_form_save_deferred -> get_ready True, get_record unchanged, grants no relational capability; persist_record -> get_record True, get_ready unchanged, m2m associations STILL unwritten (the load-bearing asymmetry); run_deferred_save -> sole producer of the capability, get_record/get_ready unchanged, associations now written. Negative control on the ordering Requires(get_record() is True): calling save_m2m() BEFORE the record write raises ValueError, so that precondition is faithful and not an over-claim. 0 divergences.

**NO-OVER-STRENGTH ON THE EMPTY-M2M EDGE.** relations_done is modeled as 'the deferred relational save was invoked for this form', not 'the association set is non-empty' (mapping.md §2 states the two coincide on the F2P input and diverge on empty-m2m). I probed exactly that divergence point: on an m2m-LESS user model and on a blank-m2m form with 0 submitted associations, the real patched function still enters the guard (the base save always installs save_m2m) and invokes save_m2m, so Implies(commit, relations_done(self)) holds. The unconditional Ensures(get_ready() is True) likewise held on every shape, including commit=False and m2m-less.

ABSTRACTION BOUNDARY EXAMINED, NOT A DEFECT. On an INVALID (unvalidated) form the real save raises ValueError ('the data didn't validate') while the model claims normal return. This is not a faithfulness break: (a) record_available(self) is bound in mapping.md §1/§2.2 to self.instance as built from submitted data WHILE VALIDATING, and G-CONF's stated domain is live validated bound forms, so the boundary is documented rather than hidden; (b) the axiomatized callee BaseModelForm.save(commit=False) raises identically on that input, so it is outside every axiom's Requires too; (c) it cannot mask the fix - pre-patch and post-patch behave identically (both raise) on an invalid form, so no invalid form is a discriminating input.

**SCAFFOLDING CHECKED.** MustTerminate(2)/MustTerminate(1) add no behaviour: the real save is a straight-line body of bounded calls with no recursion, and all three real callees ran to completion in every observation.

INDEPENDENT GATE REPRODUCTION in the real container on the gold-patched tree: axiom_check.py exit 0 (50 observations incl. the empty-m2m boundary and the pre-pk negative); conformance_check.py exit 0 - 100000 Requires-satisfying trials, seed 16333, 24 cells enumerated exhaustively, 0 disagreements, oracle = the real gold-patched UserCreationForm.save CALLED (not transliterated), shadow = the impl region verbatim with the @ContractOnly callees bound to the real repo functions. (Note: the two checks SKIP/pass trivially outside the container - 'Django not configurable... No module named django' - so the in-container run is the load-bearing evidence.)

BUNDLE NOTE (not a defect): the task prompt names patch.diff, which is not a file in this bundle; the gold patch is carried in meta.json['patch_diff'] and matches the SWE-bench dataset patch byte-for-byte (I diffed against data/swe_bench_verified/test.jsonl), and it is what I applied.

**CONCLUSION:** no admitted input separates the modeled function from the real patched callee. The only domain restriction (get_record() is False) is provably required for the spec to be TRUE of the real function, and the one entry fact left unconstrained (get_ready()) strengthens the spec over the P2P-relevant half. Verdict FAITHFUL; no diverging input to cite.

**ATTACK GOAL:** find an input where the modeled save_form disagrees with the REAL gold-patched UserCreationForm.save (spec too strong / drifted). NONE FOUND across every admitted entry state.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL(3) leakage / gold-reconstruction audit of django__django-16333 nagini spec view.

**BASELINE.** Public problem_statement (title 'UserCreationForm should save data from ManyToMany form fields') already states, in the solver's own view: (a) the symbol UserCreationForm.save and its commit=True path; (b) that data in ManyToMany form fields is not saved; (c) that unlike the parent django.forms.ModelForm, save(commit=True) 'omits to call self.save_m2m()'; (d) the file's owning module (contrib.auth.forms). The public statement therefore already names the exact call to add and the exact method to add it to. The residual gold content NOT in the problem statement is only the `if hasattr(self, "save_m2m"):` guard. Gold patch = 2 added lines in django/contrib/auth/forms.py:141.

SPEC VIEW GENERATED, not eyeballed: markers.spec_view(model.py, nagini backend) -> 311 lines, impl region replaced by the elision placeholder; sole impl region is save_form's, and the elided body is the only place the gold-analogue control flow lives.

### MECHANICAL EVIDENCE (all run, not asserted):
1. leakage.screen(model.py, nagini, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[]. Matches the recorded meta.json G-LEAK stamp ('pass', 'spec view clean', harness fb403a771a83, model.py digest fe187a86..) -- no relaxed_leakage flag, no RELAXED_LEAKAGE.md, so the pass is not a documented semantic-leak waiver being papered over.
2. Gold-line reproduction: every added/removed/context gold line normalized (whitespace-stripped) and searched in the spec view -- 'if hasattr(self, "save_m2m"):', 'self.save_m2m()', 'user = super().save(commit=False)', 'user.set_password(self.cleaned_data["password1"])', 'user.save()', 'return user', 'def save(self, commit=True):' -- ALL not present.
3. Diff markers: '@@', 'diff --git', '+++ ', '--- ', '\nindex ' -- all absent.
4. Identifier/path scan: 'save_m2m', 'hasattr', 'UserCreationForm', 'contrib', 'auth', 'forms.py', 'set_password', 'password1', 'cleaned_data', 'ModelForm', 'super', 'm2m', 'M2M', 'ManyToMany', 'user.save', 'commit=True/False', and the test-patch-only names 'orgs'/'Organization'/'pk' -- all absent from the spec view. Only 'django' appears, in the instance-id header line 1 ('Twin-artifact model for django__django-16333.'), which is the uniform header across all bundles (verified: every benchmark-verified/*/nagini/model.py opens with the same 'Twin-artifact model for <instance_id>' line) and is the instance identity the harness already gives the solver -- not edit localization beyond it. patch changed-symbol set is {'save'}, and 'save' is in the problem statement, so no symbol-collision leak either.
5. Vocabulary: no bug/fix narration -- `_NARRATION` scan clean; grep for 'fix/patch/bug/regression/previously/broken/incorrectly/wrong' over the spec view returns only innocuous English ('before', 'missing', 'after the primary record exists') in behaviour prose, none of it narrating an edit.
6. Naming is deliberately de-Djangoized throughout: save_form / Form / persist_record / base_form_save_deferred / run_deferred_save / relations_done / record_available / get_ready. A solver reading only the spec view learns 'a save routine must also run the deferred relational save when committing' -- which is exactly claim (c) already in the public statement -- and learns no file, no method name, and no call site.

NO OVER-CONSTRAINT INTO THE GOLD SHAPE (the subtle leak channel I specifically probed). The one gold element absent from the problem statement is the hasattr guard. I built unguarded.py: same spec, impl with the guard REMOVED (base_form_save_deferred; if commit: persist_record; run_deferred_save -- the model analogue of a bare unguarded self.save_m2m()). adversary same-spec -> exit 0 ('SAME -- attack shares the bundle's exact specification'), and nagini_verify.sh -> exit 0 ('Verification successful', 7.74s). So the spec does NOT force the guard: it admits the unguarded implementation. The spec view therefore cannot be read backwards to recover the `if hasattr(...)` line -- the residual gold content is exactly the part the spec leaves free. (This same fact is a spec-strength observation for panel 1/2 to weigh against the real repo's contract, where super().save(commit=False) always sets save_m2m so the guard is defensive; it is not a leakage finding, and if anything it is the opposite of one.)
7. Bundle-file provenance pointers ('Provenance + soundness check: mapping.md / axiom_check.py') survive into the spec view, but mapping.md and axiom_check.py are bundle-side only -- confirmed absent from the solver worktree at base_commit 60a7bd89860e -- and the consumer prompt (eval/prompts.py `_spec_block`/initial_user) ships only spec_view + problem_statement + modeled-function model_symbol<->repo_symbol pairs. Note the modeled-functions line IS localization ('save_form (<-> django.contrib.auth.forms.UserCreationForm.save)', forms.py:139), but it is delivered by the harness's own localization channel that mode 0 gets identically and with no spec detail, and it merely repeats UserCreationForm.save which the problem statement names; it is not a spec-view line, so it is out of scope for this gate and leaks nothing beyond the public statement.

**CONCLUSION:** no gold line, no diff marker, no patched path, no identifier echoing a patched repo symbol beyond the public statement, no bug/fix narration, and the spec provably does not pin the one gold detail the problem statement omits. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
