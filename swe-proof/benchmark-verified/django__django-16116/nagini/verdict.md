# P2 adversarial audit — django__django-16116

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.py`, `atk_5.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl survived: 9 of 11 attacks failed to verify, and the 2 that DID verify (atk_4, atk_5 — guarded oracle echoes on the A-legs) had their faithful refined patches materialized and EXECUTED through the official harness, and BOTH RESOLVED (resolved=True, attempts=1, flaky=False, F2P 'makemigrations --check should exit with a non-zero status when' success, 137/137 P2P success). A verifying impl whose faithful patch resolves is not a counterexample — it is a legitimate alternative implementation, so verify⇏correct is NOT demonstrated.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -445,10 +445,10 @@
                                                + fresh_artifact_yield()))
     # post-conditions-end
     # impl-start
-    if check_mode:
-        raise CheckFailureExit()
     if update_variant:
         write_update_artifacts(store)
     else:
         write_fresh_artifacts(store)
+    if check_mode:
+        raise CheckFailureExit()
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -448,7 +448,13 @@
     if check_mode:
         raise CheckFailureExit()
     if update_variant:
-        write_update_artifacts(store)
+        try:
+            write_update_artifacts(store)
+        except ProducingStepFailed:
+            write_update_artifacts(store)
     else:
-        write_fresh_artifacts(store)
+        try:
+            write_fresh_artifacts(store)
+        except ProducingStepFailed:
+            write_fresh_artifacts(store)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -448,7 +448,13 @@
     if check_mode:
         raise CheckFailureExit()
     if update_variant:
-        write_update_artifacts(store)
+        try:
+            write_update_artifacts(store)
+        except ProducingStepFailed:
+            pass
     else:
-        write_fresh_artifacts(store)
+        try:
+            write_fresh_artifacts(store)
+        except ProducingStepFailed:
+            pass
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -448,7 +448,11 @@
     if check_mode:
         raise CheckFailureExit()
     if update_variant:
+        if update_step_fails():
+            raise ProducingStepFailed()
         write_update_artifacts(store)
     else:
+        if fresh_step_fails():
+            raise ProducingStepFailed()
         write_fresh_artifacts(store)
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -448,6 +448,8 @@
     if check_mode:
         raise CheckFailureExit()
     if update_variant:
+        if update_step_declines():
+            raise ProducingStepDeclined()
         write_update_artifacts(store)
     else:
         write_fresh_artifacts(store)
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -450,5 +450,6 @@
     if update_variant:
         write_update_artifacts(store)
     else:
+        store.append(0)
         write_fresh_artifacts(store)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -445,7 +445,7 @@
                                                + fresh_artifact_yield()))
     # post-conditions-end
     # impl-start
-    if check_mode:
+    if check_mode and update_artifact_yield() >= 2 and fresh_artifact_yield() >= 2:
         raise CheckFailureExit()
     if update_variant:
         write_update_artifacts(store)
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -450,5 +450,7 @@
     if update_variant:
         write_update_artifacts(store)
     else:
+        if update_step_fails():
+            raise ProducingStepFailed()
         write_fresh_artifacts(store)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -450,5 +450,6 @@
     if update_variant:
         write_update_artifacts(store)
     else:
-        write_fresh_artifacts(store)
+        while True:
+            Invariant(list_pred(store) and Acc(LEDGER.produced, 1 / 2))
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -446,6 +446,12 @@
     # post-conditions-end
     # impl-start
     if check_mode:
+        if update_variant:
+            if update_step_fails():
+                raise ProducingStepFailed()
+        else:
+            if fresh_step_fails():
+                raise ProducingStepFailed()
         raise CheckFailureExit()
     if update_variant:
         write_update_artifacts(store)
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -445,7 +445,7 @@
                                                + fresh_artifact_yield()))
     # post-conditions-end
     # impl-start
-    if check_mode:
+    if check_mode and not update_variant:
         raise CheckFailureExit()
     if update_variant:
         write_update_artifacts(store)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16116.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A management command detects that an application has pending model changes
  for which migration files would need to be produced. The command supports a
  scriptable "check" mode: the caller only wants to learn WHETHER pending
  changes exist, without the command producing any artefact on the side.

  The behaviour pinned here is the interaction between that check mode and the
  artefact-producing step, in the branch where pending changes DO exist:

    * In check mode the command must report the pending-changes condition to
      its caller by terminating with a failure outcome, and it must do so
      WITHOUT producing any migration artefact ANYWHERE: nothing is committed
      to the durable medium migration files live on, and the command's own
      record of the files it produced is left exactly as it was. (This matches
      the check mode of the sibling commands, which merely report and exit.)
    * Outside check mode the command really does produce the migration
      artefacts for the pending changes — either by folding them into the most
      recent migration (the "update" variant) or by emitting fresh migration
      files — and then returns normally. It produces them EXACTLY ONCE: the
      count of artefacts committed to the durable medium grows by precisely
      the number one run of the requested producing step yields for those
      pending changes, and the command's record of produced files grows by the
      same amount. So every pending migration is materialised a single time,
      none is materialised over again on top of itself, and none is merely
      recorded as produced without actually being committed.
    * The "update" producing step may find the most recent migration
      unsuitable to fold into, in which case it declines the whole request:
      it terminates with a refusal outcome, having committed nothing to the
      durable medium and having left the record of produced files as it was.
      The command reports that refusal to its caller unchanged. Only the
      "update" step has a most-recent migration to judge, so only that variant
      can refuse in this way, and only outside check mode.
    * EITHER producing step may instead be unable to carry the request
      through: the pending changes may contain something it cannot render into
      a migration artefact, or the medium may not admit the artefacts at all.
      Then it stops partway and reports that to the caller, and what it has
      done to the medium by then is bounded: it has committed AT MOST the
      artefacts of the single run it was asked for, each of the kind that step
      produces, it has recorded no artefact it did not commit, and every
      artefact already recorded is still recorded. This outcome, too, belongs
      to the non-check mode only, because in check mode no producing step is
      reached at all.

  In other words: when check mode is requested, the failure-exit happens FIRST,
  before anything is committed to the durable medium; the artefact-producing
  step is reached only when check mode is NOT requested, and then it is
  performed once — or it declines and commits nothing, or it stops partway and
  reports having got no further than the artefacts it recorded.

Modelling choices (Nagini fragment):
  * Producing an artefact and RECORDING that an artefact was produced are two
    DIFFERENT observables, and both are carried, because an implementation can
    have one without the other:
      - ``store: List[int]`` is the command's own record of the files it
        produced: one token per recorded artefact, appended in order. The
        token VALUE encodes the KIND of producing step that emitted it (a
        fresh-file artefact as ``0``, a fold-into-most-recent artefact as
        ``1``): the two steps have observably different on-disk outcomes, so
        WHICH kind of artefact was recorded is itself part of the observable.
        The record is genuinely mutated by the writers, so it is held at full
        permission and its exact post-state is stated.
      - ``LEDGER.produced`` is the AMBIENT tally of artefact-producing acts
        actually committed to the durable medium migration files live on — it
        counts artefact writes performed, over the whole medium, not the size
        of any one record and not the net number of files left behind. It is
        held at HALF permission throughout, so this specification's subject may
        READ it but can never advance it by hand: only a genuine producing step
        does that. That is what makes "an artefact was really produced" a
        distinct, unforgeable observable rather than a bookkeeping entry, and
        it is ambient because the medium is shared: an artefact committed to it
        counts however the producing step chose to record the fact, including
        into some other record entirely.
  * The check-mode failure outcome, the update step's refusal outcome and a
    producing step's non-completion are user-defined exception classes (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2).
  * ``check_mode`` and ``update_variant`` are plain booleans.
  * The two artefact writers are unchanged callees the command invokes; each is
    axiomatised as committing its artefact yield to the durable medium AND
    recording that same yield of produced-file tokens (mapping.md §3); the
    proof consumes those Ensures (A-consumed).
  * "how many artefacts one run of a producing step yields for these pending
    changes" is itself an opaque quantity of the pending changes (one artefact
    per pending migration), not a number this specification pins: it is named
    by a per-step artefact-yield symbol (``update_artifact_yield`` /
    ``fresh_artifact_yield``), known only to be positive. Stating both the
    committed count and the recorded growth in terms of that yield says "the
    producing step's own output, once" without pinning any particular number
    of pending changes.
  * whether the "update" step finds the most recent migration foldable is
    likewise an opaque condition of the repository state, named by
    ``update_step_declines()``; a run that returns normally establishes it was
    false. It is not a value the subject may choose: nothing lets an
    implementation prove it, so declining is available only by really invoking
    the step and having it decline.
  * whether a producing step can carry the pending changes through to artefacts
    at all is a further opaque condition of the repository state, one per step
    (``update_step_fails()`` / ``fresh_step_fails()``), for the same reason and
    with the same consequence: a run that returns normally establishes its
    step's condition was false, and no implementation can establish it except
    by really invoking that step and having it stop partway. The two steps get
    their own symbols because they consult different things: only the update
    step has a most-recent migration to fold into, and the artefacts they
    render differ, so one can be unable to proceed where the other is not.
  * A step that stops partway leaves a state this specification bounds rather
    than pins: how far it got is not an observable this specification predicts,
    so what is stated is the envelope the caller can rely on (at most one run's
    artefacts committed, each of that step's kind, nothing recorded that was
    not committed, the artefacts already recorded still recorded), not an exact
    count.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class CheckFailureExit(Exception):
    """The failure outcome the command terminates with in check mode when
    pending changes exist. User-defined stand-in for the process-exit the
    command performs to report missing migrations to its caller (a builtin
    exception in an ``Exsures`` crashes the Nagini translator; mapping.md §2)."""
    pass

class ProducingStepDeclined(Exception):
    """The refusal outcome the "update" producing step terminates with when the
    most recent migration is not something it can fold the pending changes
    into. Nothing has been committed to the durable medium when it is raised.
    User-defined stand-in for the command-level error the step reports."""
    pass

class ProducingStepFailed(Exception):
    """The outcome a producing step terminates with when it cannot carry the
    pending changes through to artefacts and stops partway. What it had
    committed to the durable medium by then is whatever it had recorded, and no
    more than one run of that step yields. User-defined stand-in for the
    error the step reports to the caller."""
    pass

class ArtefactLedger:
    """The durable medium migration artefacts are committed to, observed only
    through ``produced``: a monotone tally of artefact-producing acts actually
    carried out on it (one per artefact written). Ambient rather than a
    parameter, because the medium is shared by every producing step regardless
    of which record that step chose to note the artefact in."""

    def __init__(self) -> None:
        self.produced = 0  # type: int
        Ensures(Acc(self.produced) and self.produced == 0)

LEDGER = ArtefactLedger()

# axioms-start
@Pure
@ContractOnly
def update_artifact_yield() -> int:
    """How many migration artefacts ONE run of the fold-into-most-recent
    producing step yields for the pending changes at hand: one artefact per
    pending migration. An opaque positive quantity of those pending changes —
    this specification does NOT pin its value (a one-app change set yields one
    artefact, a two-app change set two), only that a run of that step is
    genuinely artefact-producing. It exists so both the committed-artefact
    count and the produced-file record's growth can be stated as "that step's
    own output, once" without pinning how many pending migrations there are.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(Result() >= 1)

@Pure
@ContractOnly
def fresh_artifact_yield() -> int:
    """How many migration artefacts ONE run of the fresh-migration-file
    producing step yields for the pending changes at hand: one artefact per
    pending migration. An opaque positive quantity of those pending changes,
    left unpinned exactly as above.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(Result() >= 1)

@Pure
@ContractOnly
def update_step_fails() -> bool:
    """Whether the fold-into-most-recent step is unable to carry the pending
    changes at hand through to artefacts, so that it stops partway instead of
    completing. An opaque condition of the repository state (what the pending
    changes contain and what the medium will admit): nothing in this
    specification lets it be established, so that outcome is reachable only by
    really invoking that step and having it stop. A run of the step that
    returns normally establishes this was false.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    pass

@Pure
@ContractOnly
def fresh_step_fails() -> bool:
    """Whether the fresh-migration-file step is unable to carry the pending
    changes at hand through to artefacts, so that it stops partway instead of
    completing. An opaque condition of the repository state, left unpinned
    exactly as above, and a SEPARATE condition from the update step's: the two
    steps consult different things, so either can be unable to proceed where
    the other is not.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    pass

@Pure
@ContractOnly
def update_step_declines() -> bool:
    """Whether the most recent migration is unsuitable for the
    fold-into-most-recent step to fold the pending changes into, so that the
    step declines the whole request instead of producing anything. An opaque
    condition of the repository state: nothing in this specification lets it be
    established, so the refusal outcome is reachable only by really invoking
    that step and having it decline. A run of the step that returns normally
    establishes this was false.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    pass

@ContractOnly
def write_update_artifacts(store: List[int]) -> None:
    """The "update" artefact writer (unchanged callee): folds the pending
    changes into the most recent migration, committing at least one migration
    artefact to the durable medium and recording it. The facts the proof needs:
    ONE run of it commits its own artefact yield of artefacts to the medium
    (advancing the ambient tally by that positive count, one per pending
    migration — the count itself is not pinned here, only that it is this
    step's yield) and appends that same yield of produced-file tokens to the
    record, leaving the tokens already recorded intact (so calling it is
    observably an artefact-producing step, and calling it twice is observably
    twice as much production). Every token it appends carries the
    fold-into-most-recent kind (``1``): this writer's artefacts are observably
    of that kind and of no other. It holds only READ access to the ambient
    tally's carrier and yet advances it, which is the modelling of "the act
    happens out in the shared medium, not in a variable the caller owns".
    Alternatively it declines: it may find the most recent migration unsuitable
    to fold into, and then it terminates with the refusal outcome having
    committed NOTHING to the medium and recorded nothing. Alternatively again it
    stops partway: it may be unable to render the pending changes into
    artefacts at all, and then it terminates with the non-completion outcome
    having committed no more than this one run's artefacts, all of its own kind,
    having recorded no artefact it did not commit, and having kept the tokens
    already recorded.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(list_pred(store))
    Requires(Acc(LEDGER.produced, 1 / 2))
    Requires(MustTerminate(2))
    Ensures(list_pred(store))
    Ensures(Acc(LEDGER.produced, 1 / 2))
    Ensures(not update_step_declines())
    Ensures(not update_step_fails())
    Ensures(len(store) == len(Old(ToSeq(store))) + update_artifact_yield())
    Ensures(ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))
    Ensures(Forall(int, lambda i: Implies(
        len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 1)))
    Ensures(LEDGER.produced == Old(LEDGER.produced) + update_artifact_yield())
    Exsures(ProducingStepDeclined, update_step_declines()
            and list_pred(store) and Acc(LEDGER.produced, 1 / 2)
            and ToSeq(store) == Old(ToSeq(store))
            and LEDGER.produced == Old(LEDGER.produced))
    Exsures(ProducingStepFailed, update_step_fails()
            and list_pred(store) and Acc(LEDGER.produced, 1 / 2)
            and len(store) <= len(Old(ToSeq(store))) + update_artifact_yield()
            and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store))
            and Forall(int, lambda i: Implies(
                len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 1))
            and LEDGER.produced >= Old(LEDGER.produced)
                                  + len(store) - len(Old(ToSeq(store)))
            and LEDGER.produced <= Old(LEDGER.produced)
                                  + update_artifact_yield())

@ContractOnly
def write_fresh_artifacts(store: List[int]) -> None:
    """The fresh-migration artefact writer (unchanged callee): emits new
    migration files for the pending changes, committing at least one migration
    artefact to the durable medium and recording it. The facts the proof needs:
    ONE run of it commits its own artefact yield of artefacts to the medium
    (advancing the ambient tally by that positive count, one per pending
    migration — the count itself is not pinned here, only that it is this
    step's yield) and appends that same yield of produced-file tokens to the
    record, leaving the tokens already recorded intact (so calling it is
    observably an artefact-producing step, and calling it twice is observably
    twice as much production). Every token it appends carries the fresh-file
    kind (``0``): this writer's artefacts are observably of that kind and of no
    other. It holds only READ access to the ambient tally's carrier and yet
    advances it, as above. Alternatively it stops partway: it may be unable to
    render the pending changes into artefacts at all, and then it terminates
    with the non-completion outcome having committed no more than this one run's
    artefacts, all of its own kind, having recorded no artefact it did not
    commit, and having kept the tokens already recorded.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(list_pred(store))
    Requires(Acc(LEDGER.produced, 1 / 2))
    Requires(MustTerminate(2))
    Ensures(list_pred(store))
    Ensures(Acc(LEDGER.produced, 1 / 2))
    Ensures(not fresh_step_fails())
    Ensures(len(store) == len(Old(ToSeq(store))) + fresh_artifact_yield())
    Ensures(ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))
    Ensures(Forall(int, lambda i: Implies(
        len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 0)))
    Ensures(LEDGER.produced == Old(LEDGER.produced) + fresh_artifact_yield())
    Exsures(ProducingStepFailed, fresh_step_fails()
            and list_pred(store) and Acc(LEDGER.produced, 1 / 2)
            and len(store) <= len(Old(ToSeq(store))) + fresh_artifact_yield()
            and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store))
            and Forall(int, lambda i: Implies(
                len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 0))
            and LEDGER.produced >= Old(LEDGER.produced)
                                  + len(store) - len(Old(ToSeq(store)))
            and LEDGER.produced <= Old(LEDGER.produced)
                                  + fresh_artifact_yield())
# axioms-end

# pure-start
# (no module-level pure helpers required: the decision is stated inline over the
# two boolean flags, the produced-file record and the ambient artefact tally.)
# pure-end

def produce_changes_or_report(
    store: List[int], check_mode: bool, update_variant: bool
) -> None:
    # pre-conditions-start
    # The produced-file record is mutated in place (a writer may append to it);
    # full permission, post-state stated exactly. The ambient artefact tally is
    # held at HALF permission: this subject may READ how many artefacts have
    # been committed to the durable medium but may never advance the count
    # itself — only a genuine producing step does that. This function is the
    # changes-present branch: pending changes have been detected.
    Requires(list_pred(store))
    Requires(Acc(LEDGER.produced, 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # Normal return is reachable ONLY when check mode is NOT requested: in check
    # mode the command must terminate with the failure outcome, never return.
    Ensures(not check_mode)
    Ensures(list_pred(store))
    Ensures(Acc(LEDGER.produced, 1 / 2))
    # Outside check mode an artefact is REALLY PRODUCED, not merely recorded:
    # the ambient count of artefacts committed to the durable medium grows by at
    # least one. This is the observable no bookkeeping can forge — the tally is
    # read-only here, so it advances only because a genuine producing step ran.
    Ensures(LEDGER.produced >= Old(LEDGER.produced) + 1)
    # And the record of produced files grows in step with it, keeping every
    # token already recorded: what the command reports having produced is what
    # it actually committed, neither more nor less.
    Ensures(len(store) >= len(Old(ToSeq(store))) + 1)
    Ensures(ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))
    # The KIND of every newly-recorded artefact matches the requested producing
    # variant: fold-into-most-recent tokens (``1``) exactly when the update
    # variant is requested, fresh-file tokens (``0``) otherwise. This pins
    # WHICH producing step ran to the variant flag (the two steps have
    # observably different on-disk outcomes).
    Ensures(Implies(update_variant, Forall(int, lambda i: Implies(
        len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 1))))
    Ensures(Implies(not update_variant, Forall(int, lambda i: Implies(
        len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 0))))
    # The pending changes are materialised EXACTLY ONCE, and materialised for
    # real: the count of artefacts committed to the durable medium grows by
    # precisely the artefact yield of ONE run of the requested producing step,
    # and the produced-file record grows by that same amount. No more (a pending
    # migration is never written a second time over the artefact just written
    # for it), no less, and nothing is recorded as produced that was not
    # committed. This pins HOW MANY TIMES the producing step is performed —
    # which the growth lower bounds above cannot see — and pins the record to
    # the acts, so a run that fabricates record entries without committing
    # anything, or commits artefacts while recording them somewhere else, is
    # excluded.
    Ensures(Implies(update_variant,
                    LEDGER.produced == Old(LEDGER.produced) + update_artifact_yield()))
    Ensures(Implies(not update_variant,
                    LEDGER.produced == Old(LEDGER.produced) + fresh_artifact_yield()))
    Ensures(Implies(update_variant,
                    len(store) == len(Old(ToSeq(store))) + update_artifact_yield()))
    Ensures(Implies(not update_variant,
                    len(store) == len(Old(ToSeq(store))) + fresh_artifact_yield()))
    # In check mode the command terminates with the failure outcome AND produces
    # NO artefact AT ALL: nothing is committed to the durable medium (the
    # ambient tally is untouched, so no producing step ran ANYWHERE — not on
    # some other record either) and the produced-file record is left exactly as
    # it was. The failure-exit happens before any artefact-producing step. This
    # is the clause that pins "exit first, produce nothing".
    Exsures(CheckFailureExit, check_mode and list_pred(store)
            and Acc(LEDGER.produced, 1 / 2)
            and ToSeq(store) == Old(ToSeq(store))
            and LEDGER.produced == Old(LEDGER.produced))
    # The refusal outcome is reported to the caller unchanged, and is available
    # ONLY where the real producing step can raise it: for the update variant,
    # outside check mode, and only when that step genuinely declines. Nothing
    # has been committed to the durable medium and nothing recorded when it
    # surfaces. So a run cannot escape producing by declining on its own.
    Exsures(ProducingStepDeclined, not check_mode and update_variant
            and update_step_declines() and list_pred(store)
            and Acc(LEDGER.produced, 1 / 2)
            and ToSeq(store) == Old(ToSeq(store))
            and LEDGER.produced == Old(LEDGER.produced))
    # A producing step that cannot carry the pending changes through stops
    # partway, and the command reports that to its caller as well. This is
    # again available ONLY where the requested step can really stop — outside
    # check mode, for the step the variant flag selects, and only when that
    # step genuinely cannot proceed — so a run cannot escape producing by
    # claiming it could not. What it has done to the durable medium by then is
    # BOUNDED, not pinned: at most the artefacts of the single run that was
    # requested, every artefact it recorded carrying the kind of the requested
    # step, no artefact recorded that was not committed (the tally has advanced
    # at least as far as the record has grown), and every artefact already
    # recorded still recorded. So stopping partway can neither over-produce nor
    # be used to book artefacts that were never committed.
    Exsures(ProducingStepFailed, not check_mode and list_pred(store)
            and Acc(LEDGER.produced, 1 / 2)
            and Implies(update_variant, update_step_fails())
            and Implies(not update_variant, fresh_step_fails())
            and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store))
            and LEDGER.produced >= Old(LEDGER.produced)
                                  + len(store) - len(Old(ToSeq(store)))
            and Implies(update_variant, Forall(int, lambda i: Implies(
                len(Old(ToSeq(store))) <= i and i < len(store),
                store[i] == 1)))
            and Implies(not update_variant, Forall(int, lambda i: Implies(
                len(Old(ToSeq(store))) <= i and i < len(store),
                store[i] == 0)))
            and Implies(update_variant,
                        len(store) <= len(Old(ToSeq(store)))
                                      + update_artifact_yield()
                        and LEDGER.produced <= Old(LEDGER.produced)
                                               + update_artifact_yield())
            and Implies(not update_variant,
                        len(store) <= len(Old(ToSeq(store)))
                                      + fresh_artifact_yield()
                        and LEDGER.produced <= Old(LEDGER.produced)
                                               + fresh_artifact_yield()))
    # post-conditions-end
    # impl-start
    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — django__django-16116 / nagini.

**REGION INTEGRITY.** Every attack was built by copying the bundle model.py and editing ONLY the impl region. Verified mechanically via swebench_unified.markers.region_hashes(src, get_backend('nagini')): for all 11 attacks the ONLY differing region is 'impl' (axioms/pure/pre-conditions/post-conditions/spec_view hashes byte-identical to base, spec_view=6501f3e07183...). pos_control differs in NO region (byte-identical to model.py). All 12 files also pass `adversary same-spec` -> exit 0 'SAME'.

**COMMANDS.** Same-spec: `python -m swebench_unified.adversary same-spec nagini django__django-16116 <path>` (all 12 -> rc=0). Weakness (same-spec AND verifies): `python -m swebench_unified.adversary weakness nagini django__django-16116 <path>`. Run 3-concurrent as background jobs (each spawns JVM+Z3), 4 batches. Resolve: run_resolve('django__django-16116', <patch text>, run_id='sbu-eqaudit-16116-<tag>') via resolve.py, atk_4 and atk_5 concurrently.

### PER-ATTACK RESULTS (path / weakness rc / observed):
1. atk_1.py — THE PREPATCH BUG re-encoded (writers first, then `if check_mode: raise`). rc=2 NOT-A-COUNTEREXAMPLE, does not verify. PREPATCH REPRODUCED: this is exactly model_prepatch.py's order and it fails the Exsures(CheckFailureExit, ... ToSeq(store)==Old(ToSeq(store))) conjunct, matching the recorded G-DIFF.
2. atk_2.py — control-flow-effect on the A-leg envelope: RETRY the same producing step after it stops partway (`except ProducingStepFailed: write_*_artifacts(store)` again). rc=2, rejected. The one-run envelope (len(store) <= len(Old)+yield, LEDGER.produced <= Old+yield) catches the over-production.
3. atk_3.py — SWALLOW the non-completion and return normally (abnormal outcome laundered into success). rc=2, rejected (LEDGER.produced >= Old+1 / the exact yield equality on normal return).
4. atk_4.py — UNGROUNDED-ORACLE ECHO of the per-step non-completion condition, GUARDED inside the matching branch (`if update_step_fails(): raise ProducingStepFailed()` before the writer; symmetrically for fresh). rc=0 CANDIDATE (verifies in 17.6s). => patch materialized (patch_atk_4.diff, 60 lines, sha256 d80177d28d19f051..., applies cleanly at base_commit via git apply --check) as a pre-flight render probe (`_step_fails` renders every artefact and discards it, so an unrenderable change set reports before any commit) + the gold reorder. HARNESS: RESOLVED=True, attempts=1, flaky=False, F2P success, 137/137 P2P success. DOES NOT BREAK THE SPEC.
5. atk_5.py — UNGROUNDED-ORACLE ECHO of the REFUSAL condition, GUARDED inside the update branch (`if update_step_declines(): raise ProducingStepDeclined()` before the writer). This is the variant the PRIOR PASS DID NOT TEST: its attack 11 hoisted the echo ABOVE `if update_variant`, which is why it was rejected; guarding it makes it verify. rc=0 CANDIDATE (18.3s). => patch materialized (patch_atk_5.diff, 66 lines, sha256 d4258fb0802fe3af..., applies cleanly) hoisting the writer's own foldability guards ahead of it. HARNESS: RESOLVED=True, attempts=1, flaky=False, F2P success, 137/137 P2P success. DOES NOT BREAK THE SPEC.
6. atk_6.py — FABRICATE a record token without committing an artefact (store.append(0) then the writer). rc=2, rejected by LEDGER.produced >= Old + record growth (the half-permission ambient tally is the unforgeable observable — it works).
7. atk_7.py — PARTIAL-DOMAIN/BOUNDARY on the opaque yield: exit only when both yields >= 2, so a one-migration change set in check mode falls through to the writers. rc=2, rejected (yields are only known >= 1, so the guard is not provable).
8. atk_8.py — CROSS-STEP predicate confusion: report a non-completion in the FRESH branch on the strength of update_step_fails(). rc=2, rejected — confirms the two A-reference symbols are NOT interchangeable, which is the load-bearing claim of mapping.md §1's 'ONE PER STEP'.
9. atk_9.py — control-flow-effect: diverge (`while True`) instead of producing. rc=2, rejected (MustTerminate(3) at the method level).
10. atk_10.py — report the render failure INSTEAD of exiting 1, in CHECK mode: precisely the SECOND differential refinement.md names (at base_commit, `--check` + unserializable default reports ValueError instead of exiting 1). rc=2, rejected by the `not check_mode` conjunct on the ProducingStepFailed leg. This confirms that conjunct is load-bearing, not decorative.
11. atk_11.py — PARTIAL-DOMAIN on the F2P observable itself: check mode exits only for the fresh variant, so `--check --update` really writes. rc=2, rejected.
POSITIVE CONTROL: pos_control.py (gold impl, byte-identical, region hashes all match) -> weakness rc=0, VERIFIES in ~18s. Confirms the spec is satisfiable and the attacks' rejections are not a broken-harness artefact.

**WHY THE TWO CANDIDATES ARE NOT COUNTEREXAMPLES.** Both echo an opaque @Pure @ContractOnly oracle (update_step_fails / update_step_declines) and then still dispatch the matching writer. The spec's abnormal-outcome legs require the oracle to be TRUE when the outcome is reported, so an echo can only report the outcome in states where the real step would also have failed/declined — and it commits nothing extra. Refined faithfully, that is 'consult the condition, then do the same thing', i.e. behaviour-preserving on the graded suite; the harness confirms it (both resolve, 137/137 P2P). The A-legs are therefore SOUND in the direction G-EQ cares about: the echo cannot manufacture an abnormal exit the real repo would not take. Worth recording for future passes: an oracle echo VERIFYING is expected here and is not by itself spec weakness — the resolve run is what settles it, and it did.

REFINEMENT.MD LEG AUDIT (§5). All 6 main-table legs are R (1,2,3), R+I (4), A-consumed (5,6); the 3 abnormal-outcome legs are A-consumed / R+A-consumed. NO kind-3 leg, NO A-reference leg, and meta.json deep_model_references == [] consistently (nothing to validate as a deep model, so no G-AX deep-model obligation is dodged). The genuinely CHANGED operation — the exit's ORDER relative to the writers — is modeled DEEPLY in the impl region (spelled-out `if check_mode: raise` ahead of the dispatch), not hidden behind an axiom about the function under change; the two axioms cover only the UNCHANGED writer callees. That is the correct shape and atk_1/atk_10 confirm the order is really sensed.

A-LEG CORRESPONDENCE spot-checked line-by-line against the real base_commit source (git show 5d36a826...:django/core/management/commands/makemigrations.py): :250-256 is the changes-present else-branch with the pre-patch order (writers then exit) exactly as mapping.md §1 quotes; :258 write_to_last_migration_files; :264-292 the four foldability CommandError guards, all BEFORE the build/write, which licenses the 'nothing committed, nothing recorded' conjuncts on the decline leg; :328 the delegation to write_migration_files (so the update step really does inherit the fresh step's failure leg, as claimed); :330 write_migration_files; :360 writer.as_string() (the raise site); :361-363 open(...,'w') / fh.write / written_files.append IN THAT ORDER inside the same `with` — which is exactly what makes the leg's `LEDGER.produced >= Old + record growth` sound; :378 os.remove (a deletion, correctly excluded from the tally); :390 run_formatters (whole-container, produces nothing, correctly no observable); :103 written_files = []. writer.path -> basedir raising ValueError for MIGRATION_MODULES None is at writer.py:205-216 as cited. Every line reference in mapping.md §1/§3 and refinement.md that I checked resolves to what the document says it does.

SCOPE / HONEST CAVEATS. (a) I did NOT re-litigate G-PANEL-2, which is independently recorded FAIL on a spec-TOO-STRONG argument (the fresh writer's ValueError on graded P2P test_failing_migration is arguably not covered by the three-outcome disjunction as the axioms pin it). That is the opposite direction from G-EQ (too-strong drifts from the repo; G-EQ asks whether the spec is too WEAK to force correctness) and it is out of this gate's scope — but a reader should not take this SOUND verdict as agreement that the bundle is defect-free overall. Note the current model.py DOES carry a ProducingStepFailed leg on both writers, so the artifact has moved since that role ran; I did not re-audit whether that fully answers it. (b) My two patches are my own faithful refinements; a different faithful refinement of the same impl could conceivably differ, though both of mine resolved on the first attempt with no flakiness. (c) Cleanup: I removed only my own three git worktrees (wt, wt4, wt5); other /tmp worktrees from other passes were left untouched.

**VERDICT:** SOUND — 11 distinct same-spec wrong impls run (>= the required 5, spanning prepatch-bug, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo guarded and cross-step, record-fabrication, divergence, and both differentials), 9 rejected by the verifier; both verifying candidates had their faithful patches materialized and EXECUTED through the official harness and both RESOLVED, so no verify⇏correct witness exists. Positive control verifies. Prepatch bug reproduced and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.py`, `atk_5.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl survived: 9 of 11 attacks failed to verify, and the 2 that DID verify (atk_4, atk_5 — guarded oracle echoes on the A-legs) had their faithful refined patches materialized and EXECUTED through the official harness, and BOTH RESOLVED (resolved=True, attempts=1, flaky=False, F2P 'makemigrations --check should exit with a non-zero status when' success, 137/137 P2P success). A verifying impl whose faithful patch resolves is not a counterexample — it is a legitimate alternative implementation, so verify⇏correct is NOT demonstrated.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16116.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A management command detects that an application has pending model changes
  for which migration files would need to be produced. The command supports a
  scriptable "check" mode: the caller only wants to learn WHETHER pending
  changes exist, without the command producing any artefact on the side.

  The behaviour pinned here is the interaction between that check mode and the
  artefact-producing step, in the branch where pending changes DO exist:

    * In check mode the command must report the pending-changes condition to
      its caller by terminating with a failure outcome, and it must do so
      WITHOUT producing any migration artefact ANYWHERE: nothing is committed
      to the durable medium migration files live on, and the command's own
      record of the files it produced is left exactly as it was. (This matches
      the check mode of the sibling commands, which merely report and exit.)
    * Outside check mode the command really does produce the migration
      artefacts for the pending changes — either by folding them into the most
      recent migration (the "update" variant) or by emitting fresh migration
      files — and then returns normally. It produces them EXACTLY ONCE: the
      count of artefacts committed to the durable medium grows by precisely
      the number one run of the requested producing step yields for those
      pending changes, and the command's record of produced files grows by the
      same amount. So every pending migration is materialised a single time,
      none is materialised over again on top of itself, and none is merely
      recorded as produced without actually being committed.
    * The "update" producing step may find the most recent migration
      unsuitable to fold into, in which case it declines the whole request:
      it terminates with a refusal outcome, having committed nothing to the
      durable medium and having left the record of produced files as it was.
      The command reports that refusal to its caller unchanged. Only the
      "update" step has a most-recent migration to judge, so only that variant
      can refuse in this way, and only outside check mode.
    * EITHER producing step may instead be unable to carry the request
      through: the pending changes may contain something it cannot render into
      a migration artefact, or the medium may not admit the artefacts at all.
      Then it stops partway and reports that to the caller, and what it has
      done to the medium by then is bounded: it has committed AT MOST the
      artefacts of the single run it was asked for, each of the kind that step
      produces, it has recorded no artefact it did not commit, and every
      artefact already recorded is still recorded. This outcome, too, belongs
      to the non-check mode only, because in check mode no producing step is
      reached at all.

  In other words: when check mode is requested, the failure-exit happens FIRST,
  before anything is committed to the durable medium; the artefact-producing
  step is reached only when check mode is NOT requested, and then it is
  performed once — or it declines and commits nothing, or it stops partway and
  reports having got no further than the artefacts it recorded.

Modelling choices (Nagini fragment):
  * Producing an artefact and RECORDING that an artefact was produced are two
    DIFFERENT observables, and both are carried, because an implementation can
    have one without the other:
      - ``store: List[int]`` is the command's own record of the files it
        produced: one token per recorded artefact, appended in order. The
        token VALUE encodes the KIND of producing step that emitted it (a
        fresh-file artefact as ``0``, a fold-into-most-recent artefact as
        ``1``): the two steps have observably different on-disk outcomes, so
        WHICH kind of artefact was recorded is itself part of the observable.
        The record is genuinely mutated by the writers, so it is held at full
        permission and its exact post-state is stated.
      - ``LEDGER.produced`` is the AMBIENT tally of artefact-producing acts
        actually committed to the durable medium migration files live on — it
        counts artefact writes performed, over the whole medium, not the size
        of any one record and not the net number of files left behind. It is
        held at HALF permission throughout, so this specification's subject may
        READ it but can never advance it by hand: only a genuine producing step
        does that. That is what makes "an artefact was really produced" a
        distinct, unforgeable observable rather than a bookkeeping entry, and
        it is ambient because the medium is shared: an artefact committed to it
        counts however the producing step chose to record the fact, including
        into some other record entirely.
  * The check-mode failure outcome, the update step's refusal outcome and a
    producing step's non-completion are user-defined exception classes (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2).
  * ``check_mode`` and ``update_variant`` are plain booleans.
  * The two artefact writers are unchanged callees the command invokes; each is
    axiomatised as committing its artefact yield to the durable medium AND
    recording that same yield of produced-file tokens (mapping.md §3); the
    proof consumes those Ensures (A-consumed).
  * "how many artefacts one run of a producing step yields for these pending
    changes" is itself an opaque quantity of the pending changes (one artefact
    per pending migration), not a number this specification pins: it is named
    by a per-step artefact-yield symbol (``update_artifact_yield`` /
    ``fresh_artifact_yield``), known only to be positive. Stating both the
    committed count and the recorded growth in terms of that yield says "the
    producing step's own output, once" without pinning any particular number
    of pending changes.
  * whether the "update" step finds the most recent migration foldable is
    likewise an opaque condition of the repository state, named by
    ``update_step_declines()``; a run that returns normally establishes it was
    false. It is not a value the subject may choose: nothing lets an
    implementation prove it, so declining is available only by really invoking
    the step and having it decline.
  * whether a producing step can carry the pending changes through to artefacts
    at all is a further opaque condition of the repository state, one per step
    (``update_step_fails()`` / ``fresh_step_fails()``), for the same reason and
    with the same consequence: a run that returns normally establishes its
    step's condition was false, and no implementation can establish it except
    by really invoking that step and having it stop partway. The two steps get
    their own symbols because they consult different things: only the update
    step has a most-recent migration to fold into, and the artefacts they
    render differ, so one can be unable to proceed where the other is not.
  * A step that stops partway leaves a state this specification bounds rather
    than pins: how far it got is not an observable this specification predicts,
    so what is stated is the envelope the caller can rely on (at most one run's
    artefacts committed, each of that step's kind, nothing recorded that was
    not committed, the artefacts already recorded still recorded), not an exact
    count.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class CheckFailureExit(Exception):
    """The failure outcome the command terminates with in check mode when
    pending changes exist. User-defined stand-in for the process-exit the
    command performs to report missing migrations to its caller (a builtin
    exception in an ``Exsures`` crashes the Nagini translator; mapping.md §2)."""
    pass

class ProducingStepDeclined(Exception):
    """The refusal outcome the "update" producing step terminates with when the
    most recent migration is not something it can fold the pending changes
    into. Nothing has been committed to the durable medium when it is raised.
    User-defined stand-in for the command-level error the step reports."""
    pass

class ProducingStepFailed(Exception):
    """The outcome a producing step terminates with when it cannot carry the
    pending changes through to artefacts and stops partway. What it had
    committed to the durable medium by then is whatever it had recorded, and no
    more than one run of that step yields. User-defined stand-in for the
    error the step reports to the caller."""
    pass

class ArtefactLedger:
    """The durable medium migration artefacts are committed to, observed only
    through ``produced``: a monotone tally of artefact-producing acts actually
    carried out on it (one per artefact written). Ambient rather than a
    parameter, because the medium is shared by every producing step regardless
    of which record that step chose to note the artefact in."""

    def __init__(self) -> None:
        self.produced = 0  # type: int
        Ensures(Acc(self.produced) and self.produced == 0)

LEDGER = ArtefactLedger()

# axioms-start
@Pure
@ContractOnly
def update_artifact_yield() -> int:
    """How many migration artefacts ONE run of the fold-into-most-recent
    producing step yields for the pending changes at hand: one artefact per
    pending migration. An opaque positive quantity of those pending changes —
    this specification does NOT pin its value (a one-app change set yields one
    artefact, a two-app change set two), only that a run of that step is
    genuinely artefact-producing. It exists so both the committed-artefact
    count and the produced-file record's growth can be stated as "that step's
    own output, once" without pinning how many pending migrations there are.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(Result() >= 1)

@Pure
@ContractOnly
def fresh_artifact_yield() -> int:
    """How many migration artefacts ONE run of the fresh-migration-file
    producing step yields for the pending changes at hand: one artefact per
    pending migration. An opaque positive quantity of those pending changes,
    left unpinned exactly as above.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(Result() >= 1)

@Pure
@ContractOnly
def update_step_fails() -> bool:
    """Whether the fold-into-most-recent step is unable to carry the pending
    changes at hand through to artefacts, so that it stops partway instead of
    completing. An opaque condition of the repository state (what the pending
    changes contain and what the medium will admit): nothing in this
    specification lets it be established, so that outcome is reachable only by
    really invoking that step and having it stop. A run of the step that
    returns normally establishes this was false.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    pass

@Pure
@ContractOnly
def fresh_step_fails() -> bool:
    """Whether the fresh-migration-file step is unable to carry the pending
    changes at hand through to artefacts, so that it stops partway instead of
    completing. An opaque condition of the repository state, left unpinned
    exactly as above, and a SEPARATE condition from the update step's: the two
    steps consult different things, so either can be unable to proceed where
    the other is not.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    pass

@Pure
@ContractOnly
def update_step_declines() -> bool:
    """Whether the most recent migration is unsuitable for the
    fold-into-most-recent step to fold the pending changes into, so that the
    step declines the whole request instead of producing anything. An opaque
    condition of the repository state: nothing in this specification lets it be
    established, so the refusal outcome is reachable only by really invoking
    that step and having it decline. A run of the step that returns normally
    establishes this was false.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    pass

@ContractOnly
def write_update_artifacts(store: List[int]) -> None:
    """The "update" artefact writer (unchanged callee): folds the pending
    changes into the most recent migration, committing at least one migration
    artefact to the durable medium and recording it. The facts the proof needs:
    ONE run of it commits its own artefact yield of artefacts to the medium
    (advancing the ambient tally by that positive count, one per pending
    migration — the count itself is not pinned here, only that it is this
    step's yield) and appends that same yield of produced-file tokens to the
    record, leaving the tokens already recorded intact (so calling it is
    observably an artefact-producing step, and calling it twice is observably
    twice as much production). Every token it appends carries the
    fold-into-most-recent kind (``1``): this writer's artefacts are observably
    of that kind and of no other. It holds only READ access to the ambient
    tally's carrier and yet advances it, which is the modelling of "the act
    happens out in the shared medium, not in a variable the caller owns".
    Alternatively it declines: it may find the most recent migration unsuitable
    to fold into, and then it terminates with the refusal outcome having
    committed NOTHING to the medium and recorded nothing. Alternatively again it
    stops partway: it may be unable to render the pending changes into
    artefacts at all, and then it terminates with the non-completion outcome
    having committed no more than this one run's artefacts, all of its own kind,
    having recorded no artefact it did not commit, and having kept the tokens
    already recorded.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(list_pred(store))
    Requires(Acc(LEDGER.produced, 1 / 2))
    Requires(MustTerminate(2))
    Ensures(list_pred(store))
    Ensures(Acc(LEDGER.produced, 1 / 2))
    Ensures(not update_step_declines())
    Ensures(not update_step_fails())
    Ensures(len(store) == len(Old(ToSeq(store))) + update_artifact_yield())
    Ensures(ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))
    Ensures(Forall(int, lambda i: Implies(
        len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 1)))
    Ensures(LEDGER.produced == Old(LEDGER.produced) + update_artifact_yield())
    Exsures(ProducingStepDeclined, update_step_declines()
            and list_pred(store) and Acc(LEDGER.produced, 1 / 2)
            and ToSeq(store) == Old(ToSeq(store))
            and LEDGER.produced == Old(LEDGER.produced))
    Exsures(ProducingStepFailed, update_step_fails()
            and list_pred(store) and Acc(LEDGER.produced, 1 / 2)
            and len(store) <= len(Old(ToSeq(store))) + update_artifact_yield()
            and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store))
            and Forall(int, lambda i: Implies(
                len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 1))
            and LEDGER.produced >= Old(LEDGER.produced)
                                  + len(store) - len(Old(ToSeq(store)))
            and LEDGER.produced <= Old(LEDGER.produced)
                                  + update_artifact_yield())

@ContractOnly
def write_fresh_artifacts(store: List[int]) -> None:
    """The fresh-migration artefact writer (unchanged callee): emits new
    migration files for the pending changes, committing at least one migration
    artefact to the durable medium and recording it. The facts the proof needs:
    ONE run of it commits its own artefact yield of artefacts to the medium
    (advancing the ambient tally by that positive count, one per pending
    migration — the count itself is not pinned here, only that it is this
    step's yield) and appends that same yield of produced-file tokens to the
    record, leaving the tokens already recorded intact (so calling it is
    observably an artefact-producing step, and calling it twice is observably
    twice as much production). Every token it appends carries the fresh-file
    kind (``0``): this writer's artefacts are observably of that kind and of no
    other. It holds only READ access to the ambient tally's carrier and yet
    advances it, as above. Alternatively it stops partway: it may be unable to
    render the pending changes into artefacts at all, and then it terminates
    with the non-completion outcome having committed no more than this one run's
    artefacts, all of its own kind, having recorded no artefact it did not
    commit, and having kept the tokens already recorded.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(list_pred(store))
    Requires(Acc(LEDGER.produced, 1 / 2))
    Requires(MustTerminate(2))
    Ensures(list_pred(store))
    Ensures(Acc(LEDGER.produced, 1 / 2))
    Ensures(not fresh_step_fails())
    Ensures(len(store) == len(Old(ToSeq(store))) + fresh_artifact_yield())
    Ensures(ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))
    Ensures(Forall(int, lambda i: Implies(
        len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 0)))
    Ensures(LEDGER.produced == Old(LEDGER.produced) + fresh_artifact_yield())
    Exsures(ProducingStepFailed, fresh_step_fails()
            and list_pred(store) and Acc(LEDGER.produced, 1 / 2)
            and len(store) <= len(Old(ToSeq(store))) + fresh_artifact_yield()
            and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store))
            and Forall(int, lambda i: Implies(
                len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 0))
            and LEDGER.produced >= Old(LEDGER.produced)
                                  + len(store) - len(Old(ToSeq(store)))
            and LEDGER.produced <= Old(LEDGER.produced)
                                  + fresh_artifact_yield())
# axioms-end

# pure-start
# (no module-level pure helpers required: the decision is stated inline over the
# two boolean flags, the produced-file record and the ambient artefact tally.)
# pure-end

def produce_changes_or_report(
    store: List[int], check_mode: bool, update_variant: bool
) -> None:
    # pre-conditions-start
    # The produced-file record is mutated in place (a writer may append to it);
    # full permission, post-state stated exactly. The ambient artefact tally is
    # held at HALF permission: this subject may READ how many artefacts have
    # been committed to the durable medium but may never advance the count
    # itself — only a genuine producing step does that. This function is the
    # changes-present branch: pending changes have been detected.
    Requires(list_pred(store))
    Requires(Acc(LEDGER.produced, 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # Normal return is reachable ONLY when check mode is NOT requested: in check
    # mode the command must terminate with the failure outcome, never return.
    Ensures(not check_mode)
    Ensures(list_pred(store))
    Ensures(Acc(LEDGER.produced, 1 / 2))
    # Outside check mode an artefact is REALLY PRODUCED, not merely recorded:
    # the ambient count of artefacts committed to the durable medium grows by at
    # least one. This is the observable no bookkeeping can forge — the tally is
    # read-only here, so it advances only because a genuine producing step ran.
    Ensures(LEDGER.produced >= Old(LEDGER.produced) + 1)
    # And the record of produced files grows in step with it, keeping every
    # token already recorded: what the command reports having produced is what
    # it actually committed, neither more nor less.
    Ensures(len(store) >= len(Old(ToSeq(store))) + 1)
    Ensures(ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))
    # The KIND of every newly-recorded artefact matches the requested producing
    # variant: fold-into-most-recent tokens (``1``) exactly when the update
    # variant is requested, fresh-file tokens (``0``) otherwise. This pins
    # WHICH producing step ran to the variant flag (the two steps have
    # observably different on-disk outcomes).
    Ensures(Implies(update_variant, Forall(int, lambda i: Implies(
        len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 1))))
    Ensures(Implies(not update_variant, Forall(int, lambda i: Implies(
        len(Old(ToSeq(store))) <= i and i < len(store), store[i] == 0))))
    # The pending changes are materialised EXACTLY ONCE, and materialised for
    # real: the count of artefacts committed to the durable medium grows by
    # precisely the artefact yield of ONE run of the requested producing step,
    # and the produced-file record grows by that same amount. No more (a pending
    # migration is never written a second time over the artefact just written
    # for it), no less, and nothing is recorded as produced that was not
    # committed. This pins HOW MANY TIMES the producing step is performed —
    # which the growth lower bounds above cannot see — and pins the record to
    # the acts, so a run that fabricates record entries without committing
    # anything, or commits artefacts while recording them somewhere else, is
    # excluded.
    Ensures(Implies(update_variant,
                    LEDGER.produced == Old(LEDGER.produced) + update_artifact_yield()))
    Ensures(Implies(not update_variant,
                    LEDGER.produced == Old(LEDGER.produced) + fresh_artifact_yield()))
    Ensures(Implies(update_variant,
                    len(store) == len(Old(ToSeq(store))) + update_artifact_yield()))
    Ensures(Implies(not update_variant,
                    len(store) == len(Old(ToSeq(store))) + fresh_artifact_yield()))
    # In check mode the command terminates with the failure outcome AND produces
    # NO artefact AT ALL: nothing is committed to the durable medium (the
    # ambient tally is untouched, so no producing step ran ANYWHERE — not on
    # some other record either) and the produced-file record is left exactly as
    # it was. The failure-exit happens before any artefact-producing step. This
    # is the clause that pins "exit first, produce nothing".
    Exsures(CheckFailureExit, check_mode and list_pred(store)
            and Acc(LEDGER.produced, 1 / 2)
            and ToSeq(store) == Old(ToSeq(store))
            and LEDGER.produced == Old(LEDGER.produced))
    # The refusal outcome is reported to the caller unchanged, and is available
    # ONLY where the real producing step can raise it: for the update variant,
    # outside check mode, and only when that step genuinely declines. Nothing
    # has been committed to the durable medium and nothing recorded when it
    # surfaces. So a run cannot escape producing by declining on its own.
    Exsures(ProducingStepDeclined, not check_mode and update_variant
            and update_step_declines() and list_pred(store)
            and Acc(LEDGER.produced, 1 / 2)
            and ToSeq(store) == Old(ToSeq(store))
            and LEDGER.produced == Old(LEDGER.produced))
    # A producing step that cannot carry the pending changes through stops
    # partway, and the command reports that to its caller as well. This is
    # again available ONLY where the requested step can really stop — outside
    # check mode, for the step the variant flag selects, and only when that
    # step genuinely cannot proceed — so a run cannot escape producing by
    # claiming it could not. What it has done to the durable medium by then is
    # BOUNDED, not pinned: at most the artefacts of the single run that was
    # requested, every artefact it recorded carrying the kind of the requested
    # step, no artefact recorded that was not committed (the tally has advanced
    # at least as far as the record has grown), and every artefact already
    # recorded still recorded. So stopping partway can neither over-produce nor
    # be used to book artefacts that were never committed.
    Exsures(ProducingStepFailed, not check_mode and list_pred(store)
            and Acc(LEDGER.produced, 1 / 2)
            and Implies(update_variant, update_step_fails())
            and Implies(not update_variant, fresh_step_fails())
            and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store))
            and LEDGER.produced >= Old(LEDGER.produced)
                                  + len(store) - len(Old(ToSeq(store)))
            and Implies(update_variant, Forall(int, lambda i: Implies(
                len(Old(ToSeq(store))) <= i and i < len(store),
                store[i] == 1)))
            and Implies(not update_variant, Forall(int, lambda i: Implies(
                len(Old(ToSeq(store))) <= i and i < len(store),
                store[i] == 0)))
            and Implies(update_variant,
                        len(store) <= len(Old(ToSeq(store)))
                                      + update_artifact_yield()
                        and LEDGER.produced <= Old(LEDGER.produced)
                                               + update_artifact_yield())
            and Implies(not update_variant,
                        len(store) <= len(Old(ToSeq(store)))
                                      + fresh_artifact_yield()
                        and LEDGER.produced <= Old(LEDGER.produced)
                                               + fresh_artifact_yield()))
    # post-conditions-end
    # impl-start
    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — django__django-16116 / nagini.

**REGION INTEGRITY.** Every attack was built by copying the bundle model.py and editing ONLY the impl region. Verified mechanically via swebench_unified.markers.region_hashes(src, get_backend('nagini')): for all 11 attacks the ONLY differing region is 'impl' (axioms/pure/pre-conditions/post-conditions/spec_view hashes byte-identical to base, spec_view=6501f3e07183...). pos_control differs in NO region (byte-identical to model.py). All 12 files also pass `adversary same-spec` -> exit 0 'SAME'.

**COMMANDS.** Same-spec: `python -m swebench_unified.adversary same-spec nagini django__django-16116 <path>` (all 12 -> rc=0). Weakness (same-spec AND verifies): `python -m swebench_unified.adversary weakness nagini django__django-16116 <path>`. Run 3-concurrent as background jobs (each spawns JVM+Z3), 4 batches. Resolve: run_resolve('django__django-16116', <patch text>, run_id='sbu-eqaudit-16116-<tag>') via resolve.py, atk_4 and atk_5 concurrently.

### PER-ATTACK RESULTS (path / weakness rc / observed):
1. atk_1.py — THE PREPATCH BUG re-encoded (writers first, then `if check_mode: raise`). rc=2 NOT-A-COUNTEREXAMPLE, does not verify. PREPATCH REPRODUCED: this is exactly model_prepatch.py's order and it fails the Exsures(CheckFailureExit, ... ToSeq(store)==Old(ToSeq(store))) conjunct, matching the recorded G-DIFF.
2. atk_2.py — control-flow-effect on the A-leg envelope: RETRY the same producing step after it stops partway (`except ProducingStepFailed: write_*_artifacts(store)` again). rc=2, rejected. The one-run envelope (len(store) <= len(Old)+yield, LEDGER.produced <= Old+yield) catches the over-production.
3. atk_3.py — SWALLOW the non-completion and return normally (abnormal outcome laundered into success). rc=2, rejected (LEDGER.produced >= Old+1 / the exact yield equality on normal return).
4. atk_4.py — UNGROUNDED-ORACLE ECHO of the per-step non-completion condition, GUARDED inside the matching branch (`if update_step_fails(): raise ProducingStepFailed()` before the writer; symmetrically for fresh). rc=0 CANDIDATE (verifies in 17.6s). => patch materialized (patch_atk_4.diff, 60 lines, sha256 d80177d28d19f051..., applies cleanly at base_commit via git apply --check) as a pre-flight render probe (`_step_fails` renders every artefact and discards it, so an unrenderable change set reports before any commit) + the gold reorder. HARNESS: RESOLVED=True, attempts=1, flaky=False, F2P success, 137/137 P2P success. DOES NOT BREAK THE SPEC.
5. atk_5.py — UNGROUNDED-ORACLE ECHO of the REFUSAL condition, GUARDED inside the update branch (`if update_step_declines(): raise ProducingStepDeclined()` before the writer). This is the variant the PRIOR PASS DID NOT TEST: its attack 11 hoisted the echo ABOVE `if update_variant`, which is why it was rejected; guarding it makes it verify. rc=0 CANDIDATE (18.3s). => patch materialized (patch_atk_5.diff, 66 lines, sha256 d4258fb0802fe3af..., applies cleanly) hoisting the writer's own foldability guards ahead of it. HARNESS: RESOLVED=True, attempts=1, flaky=False, F2P success, 137/137 P2P success. DOES NOT BREAK THE SPEC.
6. atk_6.py — FABRICATE a record token without committing an artefact (store.append(0) then the writer). rc=2, rejected by LEDGER.produced >= Old + record growth (the half-permission ambient tally is the unforgeable observable — it works).
7. atk_7.py — PARTIAL-DOMAIN/BOUNDARY on the opaque yield: exit only when both yields >= 2, so a one-migration change set in check mode falls through to the writers. rc=2, rejected (yields are only known >= 1, so the guard is not provable).
8. atk_8.py — CROSS-STEP predicate confusion: report a non-completion in the FRESH branch on the strength of update_step_fails(). rc=2, rejected — confirms the two A-reference symbols are NOT interchangeable, which is the load-bearing claim of mapping.md §1's 'ONE PER STEP'.
9. atk_9.py — control-flow-effect: diverge (`while True`) instead of producing. rc=2, rejected (MustTerminate(3) at the method level).
10. atk_10.py — report the render failure INSTEAD of exiting 1, in CHECK mode: precisely the SECOND differential refinement.md names (at base_commit, `--check` + unserializable default reports ValueError instead of exiting 1). rc=2, rejected by the `not check_mode` conjunct on the ProducingStepFailed leg. This confirms that conjunct is load-bearing, not decorative.
11. atk_11.py — PARTIAL-DOMAIN on the F2P observable itself: check mode exits only for the fresh variant, so `--check --update` really writes. rc=2, rejected.
POSITIVE CONTROL: pos_control.py (gold impl, byte-identical, region hashes all match) -> weakness rc=0, VERIFIES in ~18s. Confirms the spec is satisfiable and the attacks' rejections are not a broken-harness artefact.

**WHY THE TWO CANDIDATES ARE NOT COUNTEREXAMPLES.** Both echo an opaque @Pure @ContractOnly oracle (update_step_fails / update_step_declines) and then still dispatch the matching writer. The spec's abnormal-outcome legs require the oracle to be TRUE when the outcome is reported, so an echo can only report the outcome in states where the real step would also have failed/declined — and it commits nothing extra. Refined faithfully, that is 'consult the condition, then do the same thing', i.e. behaviour-preserving on the graded suite; the harness confirms it (both resolve, 137/137 P2P). The A-legs are therefore SOUND in the direction G-EQ cares about: the echo cannot manufacture an abnormal exit the real repo would not take. Worth recording for future passes: an oracle echo VERIFYING is expected here and is not by itself spec weakness — the resolve run is what settles it, and it did.

REFINEMENT.MD LEG AUDIT (§5). All 6 main-table legs are R (1,2,3), R+I (4), A-consumed (5,6); the 3 abnormal-outcome legs are A-consumed / R+A-consumed. NO kind-3 leg, NO A-reference leg, and meta.json deep_model_references == [] consistently (nothing to validate as a deep model, so no G-AX deep-model obligation is dodged). The genuinely CHANGED operation — the exit's ORDER relative to the writers — is modeled DEEPLY in the impl region (spelled-out `if check_mode: raise` ahead of the dispatch), not hidden behind an axiom about the function under change; the two axioms cover only the UNCHANGED writer callees. That is the correct shape and atk_1/atk_10 confirm the order is really sensed.

A-LEG CORRESPONDENCE spot-checked line-by-line against the real base_commit source (git show 5d36a826...:django/core/management/commands/makemigrations.py): :250-256 is the changes-present else-branch with the pre-patch order (writers then exit) exactly as mapping.md §1 quotes; :258 write_to_last_migration_files; :264-292 the four foldability CommandError guards, all BEFORE the build/write, which licenses the 'nothing committed, nothing recorded' conjuncts on the decline leg; :328 the delegation to write_migration_files (so the update step really does inherit the fresh step's failure leg, as claimed); :330 write_migration_files; :360 writer.as_string() (the raise site); :361-363 open(...,'w') / fh.write / written_files.append IN THAT ORDER inside the same `with` — which is exactly what makes the leg's `LEDGER.produced >= Old + record growth` sound; :378 os.remove (a deletion, correctly excluded from the tally); :390 run_formatters (whole-container, produces nothing, correctly no observable); :103 written_files = []. writer.path -> basedir raising ValueError for MIGRATION_MODULES None is at writer.py:205-216 as cited. Every line reference in mapping.md §1/§3 and refinement.md that I checked resolves to what the document says it does.

SCOPE / HONEST CAVEATS. (a) I did NOT re-litigate G-PANEL-2, which is independently recorded FAIL on a spec-TOO-STRONG argument (the fresh writer's ValueError on graded P2P test_failing_migration is arguably not covered by the three-outcome disjunction as the axioms pin it). That is the opposite direction from G-EQ (too-strong drifts from the repo; G-EQ asks whether the spec is too WEAK to force correctness) and it is out of this gate's scope — but a reader should not take this SOUND verdict as agreement that the bundle is defect-free overall. Note the current model.py DOES carry a ProducingStepFailed leg on both writers, so the artifact has moved since that role ran; I did not re-audit whether that fully answers it. (b) My two patches are my own faithful refinements; a different faithful refinement of the same impl could conceivably differ, though both of mine resolved on the first attempt with no flakiness. (c) Cleanup: I removed only my own three git worktrees (wt, wt4, wt5); other /tmp worktrees from other passes were left untouched.

**VERDICT:** SOUND — 11 distinct same-spec wrong impls run (>= the required 5, spanning prepatch-bug, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo guarded and cross-step, record-fabrication, divergence, and both differentials), 9 rejected by the verifier; both verifying candidates had their faithful patches materialized and EXECUTED through the official harness and both RESOLVED, so no verify⇏correct witness exists. Positive control verifies. Prepatch bug reproduced and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE DISCIPLINE. Compared against the worktree WITH patch.diff APPLIED (verified: `git diff --cached` shows exactly the two gold hunks -- the `sys.exit(1)` moved ahead of the writer dispatch at makemigrations.py:251-258, plus the docstring-only --check help rewording). I did NOT judge the base-commit exit-after-write order as a divergence; the base copy was used only as a patch-state control. Base commit 5d36a8266c confirmed.

**METHOD.** 34 live invocations of the REAL patched `Command.handle` via `call_command`, each in a FRESH subprocess with a FRESH app tree (no cross-case contamination -- an early stateful harness gave a false 'check mode writes nothing' reading that I discarded and re-measured in isolation). Every case asserts the modelled branch is genuinely entered (spy on the real `MigrationAutodetector.changes` for a non-empty dict + the real writer actually invoked), so no result comes from an input that missed the branch. Observables read exactly as mapping.md defines them: store = `Command.written_files` with the model prefix pre-seeded; LEDGER.produced = instrumented count of `open(<...>/migrations/<name>.py, "w")` artefact commits, excluding the `__init__.py` marker. Token KIND read off the OUTERMOST writer in progress (the update writer delegates to the fresh one at :328), matching conformance_check.py's type bridge. Contaminated update probes (the questioner's `sys.exit(3)` on a non-nullable added field masquerading as an exit) were identified via questioner.py:184/210/264 and re-run with a nullable added field.

EVERY SPEC LEG CHECKED AGAINST THE REAL CALLEE, ALL AGREE (non-dry-run domain):
1. Normal return, fresh variant: 1 app -> growth 1, kinds [0], ledger 1; 2 apps -> growth 2, kinds [0,0], ledger 2. Matches `Implies(not update_variant, ledger == Old + fresh_yield)` + `len(store) == len(Old)+fresh_yield` + kind-0 clause. Confirms the yield is rightly OPAQUE: a `== +1` axiom would be unsound (mapping.md §3.1's own claim, reproduced).
2. Normal return, update variant: 1 app -> growth 1, kinds [1], ledger 1; 2 apps -> growth 2, kinds [1,1], ledger 2; a forced two-pending-migration app -> growth 2, kinds [1,1], ledger 2. Matches the kind-1 clause and the update-yield equalities. No case produced MIXED kinds, so the variant-binding clauses are not over-strong.
3. `Ensures(not check_mode)` / CheckFailureExit leg: every check_mode=True run (fresh, 2-app, update, and unserializable) raised SystemExit with code EXACTLY 1, growth 0, ledger 0, prefix intact -- matching `ToSeq(store) == Old` and `LEDGER.produced == Old`. No check-mode run ever returned normally.
4. ProducingStepDeclined leg (nothing committed, nothing recorded): triggered all three real guards -- squashed leaf ('Cannot update squash migration'), applied leaf ('Cannot update applied migration', via MigrationRecorder), and no-leaf ('App aaa has no migration'). All growth 0 / ledger 0. Critically I probed the leg's strongest claim: an app tree where app 'aaa' IS foldable but app 'bbb' has no migration, so the refusal fires MID-LOOP after 'aaa' was already folded in memory -> still growth 0 / ledger 0, because the real guards all precede the single terminal `write_migration_files(new_changes)` at :328. The 'nothing committed' conjunct is therefore sound, not merely untested. Also verified this leg is unreachable in check mode and for the fresh variant.
5. ProducingStepFailed envelope (bounded, not pinned): unserializable lambda default -> ValueError with growth 0/ledger 0 of yield 1; good-app-then-bad-app -> growth 1, kinds [0], ledger 1, of yield 2; update variant good-then-bad -> growth 1, kinds [1], ledger 1, of yield 2; MIGRATION_MODULES=None (writer.py:213 basedir ValueError) -> growth 0/ledger 0. Every observation satisfies ledger >= Old + record-growth (no token booked without a commit), ledger <= Old + yield and len(store) <= len(Old) + yield (one-run envelope), prefix kept, new tokens of the requested step's kind. The order-dependence mapping.md §3.3 tabulates is real, which is exactly why the leg states an envelope -- stating an equality here WOULD have been too strong, and the spec correctly does not.
6. Prefix preservation is prefix-length independent: re-ran the four representative shapes at prefix lengths 0, 1, 2, 5 -- `prefix_kept` True in all 16, growth/kinds/ledger unchanged, so the append-only claim is not an artefact of one seeding.

MODELLING CHOICES I PROBED AND ACCEPT AS DISCLOSED, NOT DRIFT: (a) `os.remove(prev_path)` on the update path (:378) excluded from the tally -- LEDGER counts artefact-producing ACTS, not net files left behind, stated in both model.py's docstring and mapping.md §2; (b) `run_formatters` (:390) excluded -- it reformats artefacts already committed AND already recorded, so counting its rewrite would double the tally against a definition mapping.md pins to the writers' own `open(writer.path,"w")`; (c) the `__init__.py` package marker excluded -- not a migration artefact; (d) CheckFailureExit / ProducingStepDeclined / ProducingStepFailed as user-defined classes -- a builtin in an `Exsures` crashes the translator, and the exit STATUS is still pinned to exactly 1 by conformance_check.py, which I reproduced live; (e) the opaque `update_step_declines()/update_step_fails()/fresh_step_fails()` predicates are unprovable by any implementation, so they gate the abnormal legs rather than handing an impl a free escape.

**CONCLUSION:** no input in the declared domain makes the spec stronger than the real patched callee, and the single out-of-domain boundary (`--dry-run`) is disclosed in mapping.md §2, orthogonal to the fix, and patch-state-independent as measured. FAITHFUL.

Counterexample / evidence:

```
None. No admissible input (store, check_mode, update_variant) was found on which the frozen spec is stronger than the real patched callee. Artifact identity: model.py sha256 d450fb19ad83563159b356efffd55e94df96026b7cbd62b7dacaf91cead5dd9b == meta.json G-AX/G-CONF/G-DIFF 'sources.model.py', so the audited bytes are the gated ones; `bash scripts/nagini_verify.sh model.py` => 'Verification successful' (28.94s, rc=0), so the spec is non-vacuous on its own impl.
```

**REFERENCE DISCIPLINE.** Compared against the worktree WITH patch.diff APPLIED (verified: `git diff --cached` shows exactly the two gold hunks -- the `sys.exit(1)` moved ahead of the writer dispatch at makemigrations.py:251-258, plus the docstring-only --check help rewording). I did NOT judge the base-commit exit-after-write order as a divergence; the base copy was used only as a patch-state control. Base commit 5d36a8266c confirmed.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ROLE: attacker 3 (leakage / gold-reconstruction). Judged the CONSUMER-VISIBLE spec view against the SOLVER-VISIBLE problem_statement ONLY; hints_text ('I think this makes sense.') was never used as a screening baseline.

WHAT I JUDGED (byte-exact provenance). Rebuilt the view two independent ways: swebench_unified.markers.spec_view(model.py, nagini) and the real consumer path eval.adapter.get_adapter('nagini').spec_view(model_src). Byte-identical, 26012 bytes, sha256 6501f3e07183914e..., which EQUALS meta.json gates['G-HYGIENE'].data.region_hashes.spec_view — so I audited the artifact the harness actually ships. Confirmed the impl region is truly elided (only `...  # implementation elided — supplied by the consumer` survives between impl-start/impl-end), so the gold control flow (`if check_changes: sys.exit(1)` ahead of the writer dispatch) is not present in the view at all. Toolkit sanity: `adversary same-spec nagini django__django-16116 <copy of model.py>` -> exit 0 ('SAME'), so my spec-region reads are against the frozen spec the harness enforces. I also built the full mode-1 agent prompt via eval.dataset.build_task + eval.prompts.initial_user and screened THAT, not just model.py.

**MECHANICAL SCREEN.** leakage.screen(model.py, nagini, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. Reproduced its inputs and checked each rule by hand:
  * Reproduced gold lines: all 9 added/removed lines of patch.diff normalized and searched in the normalized view. ABSENT: 'if check_changes:', 'sys.exit(1)' (x2 each), and all four help-text lines ('help=(', '"Exit with a non-zero status if model changes are missing migrations "', "'and don't actually write them.'", the pre-edit one-line help=). The ONLY normalized hit is the 3-char fragment '),' — content-free, below the screen's len>=8 threshold, and it localizes nothing.
  * Diff markers: zero occurrences of '@@', 'diff --git', '+++ ', '--- ', 'index ' in the view.
  * Patched file path: 'django/core/management/commands/makemigrations.py' absent; token 'makemigrations' occurs 0 times in the view; the only 'django' occurrence is the instance id in the module docstring title line (`Twin-artifact model for django__django-16116.`), which is the instance identifier the solver already has, not a path or an edit.
  * Symbol collision: patch-changed def/class names are {add_arguments, handle}. AST-enumerated every def/class in the view (CheckFailureExit, ProducingStepDeclined, ProducingStepFailed, ArtefactLedger, update_artifact_yield, fresh_artifact_yield, update_step_fails, fresh_step_fails, update_step_declines, write_update_artifacts, write_fresh_artifacts, produce_changes_or_report, `__init__`) — none embeds either. Also grepped the view for repo symbols: check_changes 0, sys.exit 0, written_files 0, write_to_last_migration_files 0, write_migration_files 0, MigrationLoader 0, Command 0, add_arguments 0, handle 0, '--check'/'--update'/'--dry-run' 0, 'non-zero' 0.
  * Bug/fix narration: ran the screen's full `_NARRATION` vocabulary (bug, buggy, fix/fixed/fixes, patch/patched/pre-patch/prepatch/post-patch, regression, previously, incorrectly, wrong, broken, off-by-one) case-insensitively over the view — ZERO hits. I then extended past the screen with my own edit-narration list (moved, move, reorder, 'order of', 'no longer', 'used to', 'instead of', 'anymore', 'rather than', swap, placed, 'ahead of'). Every hit is benign: 'instead of' only describes a step stopping partway instead of completing; 'used to' only in 'be used to book artefacts'; nothing says the exit is MOVED, nothing describes a prior/current ordering, nothing references the pre-patch code.

SEMANTIC / GOLD-RECONSTRUCTION ANALYSIS (the half the lexer cannot do).
  * The discriminating content the view does state — 'when check mode is requested, the failure-exit happens FIRST, before anything is committed' (docstring), 'The failure-exit happens before any artefact-producing step', 'exit first, produce nothing' (post-condition comments), and the operative clause `Exsures(CheckFailureExit, check_mode and ... ToSeq(store) == Old(ToSeq(store)) and LEDGER.produced == Old(LEDGER.produced))` — is ENTAILED BY THE PUBLIC problem_statement, which says verbatim: 'I'm suggesting that makemigrations --check should just exit without making migrations' and complains that today one must combine --check with --dry-run. 'Exit, and write nothing' IS the issue's own request. Stating it as desired behaviour is spec faithfulness, not leakage. The sibling-command aside ('This matches the check mode of the sibling commands, which merely report and exit') mirrors the statement's own 'inconsistent with migrate --check and optimizemigration --check, which just exit'. No clause tells the solver the exit CURRENTLY sits after the writers — that is the one fact the gold diff carries and the view withholds.
  * DECISIVE MACHINE FACT on 'does the view display the gold edit': markers.same_spec(model.py, model_prepatch.py) is True AND their spec views are BYTE-IDENTICAL. The pre-patch impl (writers first, then raise) and the gold impl (raise first) project to the SAME consumer view. So the view provably contains zero bits distinguishing the two orderings as text; the ordering is recoverable only by REASONING about the contract, which is exactly what the mode is meant to require, and the reasoning premise is public.
  * Content beyond the problem_statement that I checked and cleared: the view names an 'update' variant (fold into the most recent migration) vs fresh-file emission, plus the decline/stop-partway outcomes. None of this is in the issue text, so I tested it as candidate leakage and rejected it — the gold patch does NOT change any of it. `if self.update:` and both writer calls appear in the hunk only as UNCHANGED CONTEXT, and the decline guards (makemigrations.py:264-292) and render failures (:352-360) are pre-existing base_commit behaviour readable by anyone who opens the file. Knowing the branch has an update variant tells a solver nothing about what to edit; it is repo structure, not diff content. It is also load-bearing for the spec (the variant->token-kind clauses), so its presence is necessity, not hinting.
  * The gold's second hunk (rewording the --check `help=` string) is not modeled and not alluded to anywhere in the view — no leak by omission or by paraphrase.
  * Withheld-field check on the real prompt: meta.json's modeled_functions entry contains a `role` that DOES narrate the edit ('the check-mode failure-exit is moved ahead of the artefact writers') and a `carrier_type` mapping `sys.exit(1) -> raise CheckFailureExit`. I confirmed eval.prompts.`_spec_block` renders ONLY model_symbol and repo_symbol, and grepped the assembled mode-1 prompt: 'carrier_type' 0 hits, 'moved ahead' 0 hits, 'sys.exit' 0 hits outside the issue text. The single rendered localization line is 'Modeled function(s): produce_changes_or_report (↔ django.core.management.commands.makemigrations.Command.handle (the changes-present else-branch))' — file+function localization that the harness grants BY DESIGN and identically to mode 0 (dataset.py MODES_WITH_LOCALIZATION, `_localization_block`: 'the SAME information the spec modes get'). It is a where-to-edit pointer with no direction of change, so it is not leakage under this gate's standard.
  * Relaxation check: meta.relaxed_leakage is None and no RELAXED_LEAKAGE.md exists, so there is no recorded semantic relaxation I would be papering over by passing; recorded G-LEAK status is 'pass' / 'spec view clean' and my independent re-run agrees.

**CONCLUSION:** no reproduced gold line, no diff marker, no patched path, no repo-symbol echo, no bug/fix or edit-order narration, and the view is invariant under the gold-vs-prepatch impl swap. Every discriminating statement in the view is entailed by the public problem_statement. NO-LEAKAGE.

**ROLE:** attacker 3 (leakage / gold-reconstruction). Judged the CONSUMER-VISIBLE spec view against the SOLVER-VISIBLE problem_statement ONLY; hints_text ('I think this makes sense.') was never used as a screening baseline.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
