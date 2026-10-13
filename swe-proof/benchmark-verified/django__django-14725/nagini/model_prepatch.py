"""Twin-artifact model for django__django-14725.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection editor persists a batch of submitted forms and returns the list
  of records it persisted. It distinguishes two groups of records:

    * the records that already exist (drawn from the editor's bound set), and
    * the records that would be brought into existence from the remaining
      submitted forms.

  The editor carries a per-collection mode flag governing whether bringing new
  records into existence is permitted:

    (1) When the flag forbids new records, persisting returns ONLY the persisted
        already-existing records, in their order, and the new-record primitive
        is NEVER run — so no new record is brought into existence, regardless
        of how many new-record forms were submitted.

    (2) When the flag permits new records (the default), persisting returns the
        persisted already-existing records followed by the persisted new
        records, i.e. the concatenation of the two groups in that order, each
        primitive having run exactly once.

The editor is modelled as a minimal class carrying the touched field — the mode
flag (`restrict_to_existing: bool`) — plus, because persisting is an EFFECT
(each run of a primitive persists its whole group), one monotone invocation
count per primitive. The counts are held behind an abstraction predicate and
read only through pure accessors, so a count can advance ONLY by running its
primitive — it cannot be fabricated by writing the field directly. The two
unchanged persistence primitives are axiomatized: each reports a sequence of
record identifiers (carried as `PSeq[int]`) and advances its own count by
exactly one per run. The specification pins, per mode, both the returned
sequence AND the exact number of times each primitive ran, so an
implementation cannot run the new-record primitive for its effect while
discarding its report, nor run either primitive more often than once.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CollectionEditor:
    """Carries the mode flag and, behind an abstraction predicate, the two
    primitives' monotone invocation counts (observable but not directly
    writable by holders of the predicate)."""

    # pure-start
    @Predicate
    def run_counts_pred(self) -> bool:
        # Abstraction over the two primitives' invocation counts: a holder may
        # observe the counts (via the pure accessors below) but cannot write
        # them without going through the corresponding primitive, which is the
        # only operation permitted to advance its count.
        return Acc(self.existing_runs) and Acc(self.new_runs)

    @Pure
    def get_existing_runs(self) -> int:
        # Read the existing-group primitive's invocation count through the
        # abstraction (fractional, so the count can be observed in a
        # postcondition without granting the power to change it).
        Requires(Acc(self.run_counts_pred(), 1 / 2))
        return Unfolding(Acc(self.run_counts_pred(), 1 / 2), self.existing_runs)

    @Pure
    def get_new_runs(self) -> int:
        # Read the new-group primitive's invocation count through the
        # abstraction (fractional, read-only observation).
        Requires(Acc(self.run_counts_pred(), 1 / 2))
        return Unfolding(Acc(self.run_counts_pred(), 1 / 2), self.new_runs)
    # pure-end

    def __init__(self, restrict_to_existing: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.restrict_to_existing) and  # type: ignore
                self.restrict_to_existing == restrict_to_existing)  # type: ignore
        Ensures(self.run_counts_pred())  # type: ignore
        Ensures(self.get_existing_runs() == 0 and self.get_new_runs() == 0)  # type: ignore
        self.restrict_to_existing = restrict_to_existing
        self.existing_runs = 0  # type: int
        self.new_runs = 0  # type: int
        Fold(self.run_counts_pred())


# axioms-start
@Pure
@ContractOnly
def existing_report(commit: bool) -> PSeq[int]:
    """Identifiers reported by the unchanged primitive that persists the
    already-existing records of the collection, in order. It operates only on
    the bound (already-existing) records and never brings a new record into
    existence. Provenance + executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def new_report(commit: bool) -> PSeq[int]:
    """Identifiers reported by the unchanged primitive that persists the new
    records derived from the remaining submitted forms, in order — one per
    record it brings into existence (empty when none). Provenance + executable
    soundness: mapping.md / axiom_check.py.
    """


@ContractOnly
def persist_existing_objects(self: CollectionEditor, commit: bool) -> List[int]:
    """The unchanged callee that persists the already-existing records and
    returns them as a list; its content is exactly the reported sequence. Each
    run is an EFFECT: it advances the editor's existing-group invocation count
    by exactly one (and leaves the new-group count unchanged). It performs
    bounded work, so it promises termination to its callers."""
    Requires(MustTerminate(1))
    Requires(self.run_counts_pred())
    Ensures(self.run_counts_pred())
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()) + 1)
    Ensures(self.get_new_runs() == Old(self.get_new_runs()))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == existing_report(commit))


@ContractOnly
def persist_new_objects(self: CollectionEditor, commit: bool) -> List[int]:
    """The unchanged callee that persists the new records and returns them as a
    list; its content is exactly the reported sequence. Each run is an EFFECT:
    it brings the new group's records into existence and advances the editor's
    new-group invocation count by exactly one (leaving the existing-group count
    unchanged). It performs bounded work, so it promises termination to its
    callers."""
    Requires(MustTerminate(1))
    Requires(self.run_counts_pred())
    Ensures(self.run_counts_pred())
    Ensures(self.get_new_runs() == Old(self.get_new_runs()) + 1)
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == new_report(commit))
# axioms-end


def persist(self: CollectionEditor, commit: bool) -> List[int]:
    # pre-conditions-start
    # The mode flag is read-only for this operation: fractional permission,
    # required AND ensured, so the operation observes the flag without
    # altering it. The invocation counts ARE advanced -> full predicate.
    Requires(Acc(self.restrict_to_existing, 1 / 2))
    Requires(self.run_counts_pred())
    # Persisting is bounded work (at most one run of each primitive), so it
    # must TERMINATE: without this obligation the postconditions could be
    # discharged vacuously by a body that never returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.restrict_to_existing, 1 / 2))
    Ensures(self.run_counts_pred())
    Ensures(Acc(list_pred(Result())))
    # In BOTH modes the existing-group primitive runs exactly once (the counts
    # are observed through the abstraction, so these clauses are dischargeable
    # only by running the primitives, never by writing a count).
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()) + 1)
    # (1) When the flag forbids new records, the persisted list is EXACTLY the
    # already-existing group, in order — and the new-record primitive is NEVER
    # run, so no new record is brought into existence.
    Ensures(Implies(self.restrict_to_existing,
                    ToSeq(Result()) == existing_report(commit)))
    Ensures(Implies(self.restrict_to_existing,
                    self.get_new_runs() == Old(self.get_new_runs())))
    # (2) When the flag permits new records, the persisted list is the
    # already-existing group followed by the new group, in that order — the
    # new-record primitive having run exactly once.
    Ensures(Implies(not self.restrict_to_existing,
                    ToSeq(Result()) == existing_report(commit) + new_report(commit)))
    Ensures(Implies(not self.restrict_to_existing,
                    self.get_new_runs() == Old(self.get_new_runs()) + 1))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: always persists both groups, ignoring the mode flag —
    # so new records are brought into existence even when forbidden.
    result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end
