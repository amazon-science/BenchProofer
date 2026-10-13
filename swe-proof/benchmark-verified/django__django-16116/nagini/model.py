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
