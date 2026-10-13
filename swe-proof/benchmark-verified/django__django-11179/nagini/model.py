"""Twin-artifact model for django__django-11179.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single persistent object that has no dependent relations is removed
  through the optimized single-object removal path, five things must hold once
  the path returns:

    (1) the path issues exactly ONE row-removal statement against the handle it
        was given — no more than the one it already needed, and not zero. This is
        the whole point of the optimized path (it exists to spend one statement
        where the general path would spend several), and callers observe the
        number of statements a removal costs, so a path that meets the other
        guarantees but pays extra statements to do it has not met this one, and

    (2) that one statement targets the object's STORED identifier — the
        identifier the object carried on entry — and not some other identifier,
        and

    (3) the count the path returns is the number of rows THAT statement itself
        reported as removed (the caller surfaces this count to user code). The
        count must therefore be produced by the removal the path paid for; a
        count obtained by consulting the database a second time, or invented
        outright, is not the same behaviour even when the number happens to
        agree, and

    (4) the path issues exactly ONE row-removal statement IN TOTAL — that is,
        one counted across every handle in existence and not merely one counted
        against the handle it was passed. The cost a caller observes is the
        number of removal statements the stored data actually received, and the
        stored data is one shared thing; a path that keeps its accounted-for
        handle at one statement while routing further removals through some
        further handle it obtained for itself has removed rows twice over and has
        spent two statements, whatever the accounting on any single handle says.
        Guarantees (1) and (4) coincide for a path that touches only the handle
        it was given, which is what the behaviour under specification does, and

    (5) the in-memory object no longer carries a stored identifier: its
        primary-key attribute is cleared to ``None`` once the row is gone,
        matching the behaviour of the general multi-object removal path so an
        unsaved object is observably distinguishable from a persisted one.

Removing a row is something the store can REJECT: the store may answer the
row-removal statement by refusing to apply it, and then no row is removed and
there is no count to report. Which answer a given statement gets is the STORE'S
to decide, and a caller cannot determine it, or discover it, before asking: the
only way to find out is to issue the statement and see what comes back. The five
guarantees above are the guarantees of a removal the store carried OUT; where it
rejects the removal, that rejection is what reaches the caller instead of a
count, and

    (6) a count comes back ONLY from a removal the store carried out — the one
        statement this path paid for is the one the store applied, and the
        surfaced count is that removal's count. The path may end without a count
        ONLY where the store really did reject the removal, which is to say only
        where nothing was carried out for it at all; and even then it has still
        SPENT its one row-removal statement on the object's STORED identifier.
        Neither outcome is an implementation's to choose — it is settled by what
        the store did with the statement, which is why neither can be arranged in
        advance: a manufactured rejection is no more admissible than a count with
        no statement behind it, a rejection may not be passed off as a completed
        removal by answering it with a number (any number, however it was come
        by, since the store removed nothing and there is nothing to count), and a
        completed removal may not be passed off as a rejection either. Nor is a
        rejection a licence to do less: the statement was issued to find out, so
        it cost exactly one against the handle and exactly one in total, and it
        asked about this object's identifier and no other. And because no row
        was removed, the in-memory object is left as it was found: it still
        carries the STORED identifier it came in with. Clearing that identifier
        is what marks an object whose row is GONE, so it is not something a
        rejected removal may do, nor something that may be done in advance of
        knowing the store's answer — the identifier is given up only once the
        row it names has actually been removed. This is guarantee (5)'s
        counterpart on the other outcome: the two together say the identifier
        is cleared exactly when the row is gone and not otherwise, which is why
        an implementation cannot pick the moment to clear it and let the store's
        answer decide afterwards whether that was allowed.

The object under removal is a PERSISTENT one: the identifier it carries is an
identifier the stored data actually holds. Identifiers are therefore drawn from
the range the store can represent — the signed 64-bit range
``-2**63 <= identifier < 2**63``. This is a property of the domain, not an extra
demand on the removal path: a value outside that range is not an identifier any
stored row can be keyed by, so no persistent object can carry one, and the
row-removal primitive is defined (issues its statement, reports a count, returns
normally) exactly on identifiers inside it. The guarantees below are stated for
that domain and are the guarantees the primitive genuinely offers there.

    (7) NOTHING ABOUT WHAT THE STORE HAS ALREADY DONE IS AVAILABLE TO THE PATH
        FOR NOTHING. The number of row-removal statements the store has received,
        which identifier the most recent one named, what count it reported, how
        many of them the store carried out — all of that is a real record and it
        is exactly what an outside observer of the connection measures, but it is
        the STORE'S record and not the path's. The optimized path holds no such
        tally: the only way for it to learn any part of that record is to ASK the
        store, and asking is itself a statement. So a path that decides ANYTHING
        by consulting that record — which order to do its work in, whether to
        take one outcome or the other, what number to surface — has paid a
        statement it was not entitled to, and the cost a caller observes is
        higher than the one statement guarantee (1) allows. This is why the
        guarantees above are not merely a matter of the record ending up with the
        right numbers in it: the same numbers reached by consulting the record
        are a DIFFERENT behaviour with a different observable cost. Consulting
        the record is therefore not something the path may do at all, and in
        particular the count in guarantee (3) is the count the removal ITSELF
        reported back, not a number read off the record afterwards — a path that
        throws away what its own statement returned and reports what it can see
        in the record instead has consulted the store a second time, which
        guarantee (3) already excludes.

HOW THE COST AND THE PROVENANCE ARE CARRIED. Both are observable behaviour, not
implementation detail, so both are carried as state — but they are carried on the
side the observation really lives on, which by (7) is not the path's side. What
a caller of the removal path holds is a HANDLE and an ENTITLEMENT: the
entitlement to spend one row-removal statement against the stored data,
``RemovalBudget(LEDGER)``. There is exactly one such entitlement per removal and
exactly one ledger it is drawn against, because there is exactly one body of
stored data behind every handle: a statement issued through a handle a path
obtained for itself removes rows and costs a statement just the same, so an
entitlement drawn against the total is the only accounting a second handle
cannot escape. Issuing a statement SPENDS the entitlement, whatever handle it
goes through and whichever answer the store gives — a refusal is the store's
answer TO a statement, so it costs the same one — and nothing mints another.
Guarantees (1) and (4) are therefore the same fact stated once: the path may
issue no more than the one statement it was entitled to, and it holds no way to
buy a second.

What the store gives back is a RECEIPT, and receipts are the only evidence of a
removal there is. A statement the store CARRIED OUT yields
``CarriedOutRemoval(db, identifier, count)``: this handle, this identifier, this
reported count — so a receipt witnesses at once that a statement was really
issued (guarantee 1), which identifier it targeted (guarantee 2), which count
that statement itself reported (guarantee 3) and that the store applied it
(guarantee 6). A statement the store REFUSED yields
``RefusedRemoval(db, identifier)`` instead: the statement was issued and targeted
that identifier, and there is no count, because nothing was carried out.
Receipts are the store's to mint and no one else's: a path cannot write one,
cannot alter the handle, the identifier or the count on one, and cannot obtain
one except by issuing a statement and being answered. That is what makes a
returned count credible — it is the count ON the receipt, which is to say the
count the path's own statement reported — and what makes the
end-without-a-count outcome unavailable on a path's own initiative: it requires
a refusal receipt, which only a refusal produces.

The object under removal is modelled as a minimal class carrying only the one
touched field — its primary-key value (``Optional[int]``). The database handle is
modelled as a carrier for the store's own record of what has been done through
it; the module-wide ledger the entitlement is drawn against stands for the single
record of the total, since all handles reach the same stored data. By (7) that
record is the store's and a removal path running against the handle is given no
access to any part of it: reading a quantity is free in a model and is not free
in a database, so a model that let the path read the store's tallies for nothing
would license implementations whose real form pays a statement per read. The
entitlement and the receipts carry the same facts, and carry them in the only
direction a caller really has them — forward, out of statements actually issued.
The unchanged row-removal primitive is axiomatized accordingly: it spends the one
entitlement, issues one statement for the identifier it was handed, and is
answered either with a receipt for a removal the store carried out that reports
a non-negative row count, or with a refusal receipt and no count. It does NOT
touch the in-memory object. Which of the two answers the store gives is left
open by the axiom, as it is in reality: the primitive is not a function of
anything the caller holds, so an implementation cannot arrange, or foresee,
which outcome it will meet.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class PersistentObject:
    def __init__(self, pk: Optional[int]) -> None:
        Requires(MustTerminate(1))  # type: ignore
        Ensures(Acc(self.pk) and self.pk is pk)  # type: ignore
        self.pk = pk


class RemovalRefused(Exception):
    """The store refused the row-removal statement: something the stored data
    holds protects the targeted row, so no row is removed and there is no count
    to report."""
    pass


class Database:
    """The database handle a removal runs against, carrying the STORE'S own
    record of the row-removal statements issued through it:
    ``removal_statements`` is the running tally (the observable cost of a
    removal), ``last_removal_target`` is the identifier the most recent
    row-removal statement targeted, ``last_removal_report`` is how many rows that
    statement reported removed, and ``completed_removals`` is how many of those
    statements the store actually CARRIED OUT rather than rejected. That record
    is what an outside observer of the connection measures, and it is the store's
    — a removal path running against the handle is given no access to any part of
    it, because the optimized path holds no such tally and could not consult one
    without issuing a statement to ask (guarantee (7)). What a path gets instead
    is the receipt of the statement it issued (see ``CarriedOutRemoval`` /
    ``RefusedRemoval``), which is the same information in the only direction a
    caller really has it.
    """

    def __init__(self) -> None:
        Requires(MustTerminate(1))  # type: ignore
        Ensures(Acc(self.removal_statements, 1 / 2))  # type: ignore
        Ensures(Acc(self.last_removal_target, 1 / 2))  # type: ignore
        Ensures(Acc(self.last_removal_report, 1 / 2))  # type: ignore
        Ensures(Acc(self.completed_removals, 1 / 2))  # type: ignore
        Ensures(self.removal_statements == 0)  # type: ignore
        self.removal_statements = 0
        self.last_removal_target = 0
        self.last_removal_report = 0
        self.completed_removals = 0


class RemovalLedger:
    """The module-wide record of how many row-removal statements have been
    issued IN TOTAL — across every handle, since all handles reach the same
    stored data. ``total_removal_statements`` is that total, and it is the
    quantity an entitlement to remove is drawn against: see ``RemovalBudget``.
    Like a handle's own record it is the store's and not a path's to consult.
    """

    def __init__(self) -> None:
        Requires(MustTerminate(1))  # type: ignore
        Ensures(Acc(self.total_removal_statements, 1 / 2))  # type: ignore
        Ensures(self.total_removal_statements == 0)  # type: ignore
        self.total_removal_statements = 0  # type: int


# The single ledger: one body of stored data, hence one total.
LEDGER = RemovalLedger()  # type: RemovalLedger


# axioms-start
# The entitlement to spend ONE row-removal statement against the stored data the
# ledger accounts for — the cost the optimized path is allowed. It is HELD, not
# read: an entitlement is a thing a path spends, and it says nothing whatever
# about what the store has done or will do, so consulting it can tell an
# implementation nothing (there is nothing in it to consult). Issuing a statement
# through ANY handle spends it — a refusal spends it too, being the store's
# answer TO a statement that was issued — and nothing mints another, which is
# what makes "exactly one statement, counted across every handle" (guarantees (1)
# and (4)) a property of the path rather than of any single tally.
# Provenance + executable soundness: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def RemovalBudget(ledger: RemovalLedger) -> bool:
    pass


# The store's receipt for a row-removal statement it CARRIED OUT: one statement
# was issued against ``db``, it targeted ``identifier``, the store applied it,
# and THAT STATEMENT reported ``count`` rows removed. Only the store mints one —
# it comes out of the row-removal primitive being answered, and a path can
# neither write one nor change the handle, the identifier or the count on one —
# so holding it is proof that this exact removal happened and that this exact
# count is that removal's own report (guarantees (1), (2), (3), (6)).
# Provenance + executable soundness: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def CarriedOutRemoval(db: Database, identifier: int, count: int) -> bool:
    pass


# The store's receipt for a row-removal statement it REFUSED: one statement was
# issued against ``db`` and targeted ``identifier``, and the store did not apply
# it, so no row was removed and there is no count to report. Only the store mints
# one, and only by refusing — so a path cannot manufacture the
# end-without-a-count outcome, and cannot reach it without having spent its one
# statement on this object's stored identifier (guarantee (6)).
# Provenance + executable soundness: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def RefusedRemoval(db: Database, identifier: int) -> bool:
    pass


@ContractOnly
def remove_rows(db: Database, identifier: int) -> int:
    """Issue ONE row-removal statement for ``identifier`` against ``db`` and
    report how many rows it removed. Exactly one statement is issued per
    invocation (a one-element identifier list is removed by a single statement),
    so it spends the one entitlement to remove — ``RemovalBudget(LEDGER)``,
    whichever handle the statement goes through, since every handle reaches the
    same stored data — and nothing mints another. Being answered yields the
    store's receipt for what it did: the reported count is the non-negative row
    count for that identifier, and the receipt carries the handle, the identifier
    the statement targeted and the count that statement itself reported. The
    in-memory object is untouched, and the store's own record of what it has done
    is not handed to the caller (guarantee (7)): what comes back is the receipt
    for this statement and nothing else.
    ``identifier`` must be one the store can represent (the signed 64-bit
    range): that is the domain on which the primitive is defined and on which it
    issues its statement and returns a count. Handed a value the store cannot
    represent it does not report a count at all, so the guarantees below are
    stated only for the representable range.
    A removal the store REJECTS is not reported either: the store may answer the
    statement by refusing to apply it (``RemovalRefused``) rather than by
    reporting a count. Which of the two answers a given statement gets is the
    STORE'S to decide and is not something a caller can determine, or discover,
    in advance: the only way to find out is to issue the statement and see. So
    this primitive is not a function of anything a caller can read — handed the
    same handle and identifier it may report a count or refuse, and nothing a
    caller holds settles which beforehand. What the answer does settle is what
    HAPPENED: a reported count comes with the carried-out receipt for this
    statement, a refusal with the refusal receipt for it. Either way the
    statement was ISSUED — a refusal is what the store answers a statement WITH —
    so the one entitlement is spent either way and the receipt names the
    identifier that statement targeted. Only the count is missing on a refusal,
    because there is no count to report.
    Provenance + executable soundness: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(1))
    Requires(-(2 ** 63) <= identifier and identifier < 2 ** 63)
    # spends the one entitlement to remove: one statement, counted across every
    # handle. It is not returned on either exit, and nothing mints another.
    Requires(RemovalBudget(LEDGER))
    # a reported count comes with the store's receipt for the removal it carried
    # out: this handle, this identifier, and the count THIS statement reported.
    Ensures(CarriedOutRemoval(db, identifier, Result()))
    Ensures(Result() >= 0)
    # ... and on a refusal there is no count, only the receipt that the statement
    # was issued for this identifier and the store did not apply it. The
    # entitlement is spent all the same — a refusal is the store's answer TO a
    # statement. Which answer comes back is the store's, not something a caller
    # can read off anything it holds beforehand.
    Exsures(RemovalRefused, RefusedRemoval(db, identifier))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def remove_single_independent(instance: PersistentObject, db: Database) -> int:
    # pre-conditions-start
    Requires(MustTerminate(2))
    Requires(Acc(instance.pk))
    Requires(instance.pk is not None)
    # the object is PERSISTENT: the identifier it carries is one the stored data
    # can represent (the signed 64-bit range). Outside that range no stored row
    # can be keyed by the value, so no persistent object carries one.
    Requires(-(2 ** 63) <= instance.pk and instance.pk < 2 ** 63)
    # the cost the optimized path is allowed: ONE row-removal statement against
    # the stored data, counted across every handle. Nothing mints another. By
    # guarantee (7) this is ALL the path is given on the subject of what the
    # store has done — the store's own record of its statements, targets, reports
    # and carried-out removals is not handed over, because a path that could read
    # it for nothing would in reality be paying a statement to ask.
    Requires(RemovalBudget(LEDGER))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(instance.pk))
    # (1)+(2)+(3)+(4)+(6a) in one fact the path cannot arrange for itself: it
    # holds the store's receipt for a removal the store CARRIED OUT against the
    # handle it was given, targeting the object's STORED identifier (the value it
    # carried on entry), reporting exactly the count being surfaced. Only being
    # answered by the store mints that receipt, so the statement was really
    # issued (1) for that identifier (2), the count returned is that statement's
    # OWN report rather than a number read off the store's record afterwards (3),
    # and the store applied it (6a); and the statement was the one the path was
    # entitled to, so it cost one against the handle and one in total across every
    # handle (1)+(4) — the entitlement is spent and nothing mints another.
    Ensures(CarriedOutRemoval(db, Old(instance.pk), Result()))
    Ensures(Result() >= 0)
    # (5) the cleared-identifier guarantee: the object no longer carries a pk.
    Ensures(instance.pk is None)
    # (6b) The path may end WITHOUT a count only when the store REALLY rejected
    # the removal it was asked for: that outcome requires the store's refusal
    # receipt, which only a refusal produces, so a rejection cannot be
    # manufactured and the path is not entitled to end this way on its own
    # initiative. It is not a licence to do LESS either: the receipt exists only
    # because the statement was issued, so it was still spent — one against the
    # handle and one in total — and it still targeted the object's STORED
    # identifier. A path that ends this way having had a removal carried out for
    # it has taken an exit that was not its to take: what it holds then is the
    # carried-out receipt, not this one.
    # And because no row was removed, the in-memory object is left as it was
    # found, still carrying the STORED identifier it came in with: giving up that
    # identifier is what marks an object whose row is GONE, so a rejected removal
    # may not do it, and neither may a path that does it before the store's
    # answer is in. With (5) this says the identifier is surrendered exactly when
    # the row it names has been removed and at no other time.
    Exsures(RemovalRefused, Acc(instance.pk)
            and RefusedRemoval(db, Old(instance.pk))
            and instance.pk is Old(instance.pk))
    # post-conditions-end
    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end
