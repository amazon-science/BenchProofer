# properties.py — PBT falsification battery for django__django-11179. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   remove_single_independent(instance: PersistentObject, db: Database) -> int
#     Requires(MustTerminate(2))              # the path must actually RETURN
#     Requires(Acc(instance.pk))              # FULL permission — the fix WRITES it
#     Requires(instance.pk is not None)       # a stored (persisted) object
#     Requires(-(2 ** 63) <= instance.pk and instance.pk < 2 ** 63)
#                                             # the identifier a PERSISTENT object
#                                             #   carries is one the store can
#                                             #   represent (signed 64-bit)
#     Requires(RemovalBudget(LEDGER))         # (7) the ENTITLEMENT to spend the
#                                             #     ONE row-removal statement the
#                                             #     path is allowed, drawn against
#                                             #     the module-wide total so no
#                                             #     second handle escapes it. It is
#                                             #     HELD, not READ: there is nothing
#                                             #     in it to consult. Note what is
#                                             #     ABSENT and used to be here: read
#                                             #     access to the store's own record
#                                             #     (removal_statements,
#                                             #     last_removal_target,
#                                             #     last_removal_report,
#                                             #     completed_removals) and to
#                                             #     LEDGER.total_removal_statements.
#                                             #     Those are the store's, not the
#                                             #     path's — the optimized branch
#                                             #     holds no such tally and could
#                                             #     only learn one by ASKING, which
#                                             #     is itself a statement. A model
#                                             #     that handed them over for free
#                                             #     licensed impls whose faithful
#                                             #     form pays a SELECT per read.
#     Ensures(Acc(instance.pk))               # permission preserved
#     Ensures(CarriedOutRemoval(db, Old(instance.pk), Result()))
#                                             # (1)+(2)+(3)+(4)+(6a) as ONE fact the
#                                             #     path cannot arrange for itself:
#                                             #     the store's RECEIPT for a removal
#                                             #     it CARRIED OUT — this handle,
#                                             #     the object's STORED identifier,
#                                             #     and the count THAT STATEMENT
#                                             #     itself reported. Only the
#                                             #     primitive being answered mints
#                                             #     one; a path can neither write one
#                                             #     nor alter the handle, identifier
#                                             #     or count on one. So: the
#                                             #     statement was really issued (1),
#                                             #     on the stored identifier (2), the
#                                             #     surfaced count is that
#                                             #     statement's OWN report and not a
#                                             #     number read off the record
#                                             #     afterwards (3), the store applied
#                                             #     it (6a) — and it was the one
#                                             #     statement the entitlement bought,
#                                             #     so one against the handle and one
#                                             #     in TOTAL across every handle (4).
#     Ensures(Result() >= 0)                  # a reported row count is non-negative
#     Ensures(instance.pk is None)            # (5) the cleared identifier
#     Exsures(RemovalRefused,                 # (6b) the path may end WITHOUT a
#             Acc(instance.pk)                #      count only where the store
#             and RefusedRemoval(db, Old(instance.pk))
#                                             #      really REFUSED: that needs the
#                                             #      store's REFUSAL RECEIPT, which
#                                             #      only a refusal mints — so the
#                                             #      exit cannot be manufactured, and
#                                             #      the receipt exists only because
#                                             #      the statement was ISSUED, so it
#                                             #      was still spent, on the object's
#                                             #      STORED identifier.
#             and instance.pk is Old(instance.pk))
#                                             #      the object is left as found:
#                                             #      the identifier is given up
#                                             #      only once the row is gone
#   remove_rows(db, identifier) -> int  is the sole @ContractOnly primitive (the
#   unchanged DeleteQuery.delete_batch on a one-element pk list). It is EFFECTFUL
#   and it is the only thing that SPENDS the entitlement and the only thing that
#   MINTS a receipt: each invocation issues exactly one row-removal statement,
#   consumes RemovalBudget(LEDGER) (whichever handle the statement goes through,
#   since every handle reaches the same stored data) and hands back the store's
#   receipt for what it did, leaving the in-memory object untouched. Its Requires
#   names the domain it is defined on: -(2 ** 63) <= identifier < 2 ** 63, the
#   identifiers the store can represent. Handed a value outside that range the
#   real primitive reports no count at all, so the axiom claims nothing there
#   (the caller's own Requires keeps every reachable identifier inside the range).
#   There is NO pure twin of this primitive and no readable tally either: the
#   RECEIPT is the only handle on what a removal reported and what it cost, and a
#   receipt cannot be obtained except by issuing a statement and being answered.
#   The primitive can also end WITHOUT a count: the store may REFUSE the removal,
#   which it signals as RemovalRefused, and its axiom mirrors the caller's clause
#   (6) — a reported count comes with CarriedOutRemoval(db, identifier, Result()),
#   the receipt for a removal the store applied that reports that count; a refusal
#   comes with RefusedRemoval(db, identifier) and no count, there being none to
#   report. Because the refusal is what the store answers a statement WITH, the
#   refused invocation still SPENT the entitlement and its receipt still names the
#   identifier that statement targeted. WHICH of the two answers the store gives
#   is left OPEN by the axiom, as it is in reality: nothing a caller holds is a
#   function of it, so handed the same handle and identifier the primitive may
#   report a count or refuse — and, critically, there is now nothing a caller
#   holds that it could consult to guess, because the store's record is no longer
#   in the caller's read set at all.
#
# What the spec defends (the load-bearing facts):
#   * (5) instance.pk is None — the single added gold statement. Dropping it is
#     EXACTLY model_prepatch.py / the pre-patch bug the F2P observes.
#   * (1)+(4) the removal COST, now carried by the single-use ENTITLEMENT
#     RemovalBudget(LEDGER) rather than by a readable tally. The optimized path
#     exists to spend ONE row-removal statement; the number of statements a delete
#     costs is observable behaviour (the P2P query-count tests assert an exact
#     statement count for a fast-deletable delete). The entitlement is consumed by
#     the primitive and nothing mints another, so an impl that invokes the
#     primitive twice (or three times, or makes an extra unused invocation to
#     obtain a value it already had) has no budget for the second call and REJECTS
#     on its precondition; an impl that never invokes it holds no receipt and
#     cannot discharge the postcondition. Because the entitlement is drawn against
#     the module-wide LEDGER rather than against the handle passed in, this is one
#     statement counted across EVERY handle — a handle is a thing an impl can
#     OBTAIN for itself, and a removal routed through a handle of the impl's own
#     making is just as much a statement and leaves the rows just as gone. That is
#     the verify-but-not-resolve shape (one accounted-for statement, TWO real
#     removals) the P2P exact-statement-count test observes; no per-handle tally
#     can see it, because the extra statement is not ON that handle. Making the
#     entitlement the ONLY currency, and module-wide, closes both at once
#     (`uniq-duplicate-removal`, `uniq-extra-removal`, `uniq-offbooks-*`).
#   * (2)+(3)+(6a) the statement TARGET and the count PROVENANCE, now carried by
#     the store's RECEIPT CarriedOutRemoval(db, Old(instance.pk), Result()). The
#     one statement the path paid for must have targeted the object's STORED
#     identifier, and the count surfaced must be the report THAT STATEMENT itself
#     returned — not a literal, not a value obtained some other way, and not a
#     number read back off the store's record afterwards. A receipt is minted only
#     by the primitive being answered and names the handle, the identifier and the
#     count together, so an impl cannot hold one for the stored identifier while
#     having spent its statement on a decoy, cannot hold one at all without having
#     issued a statement, and cannot hold one naming a count other than the one its
#     own statement reported. This is what makes the provenance pin independent of
#     any equation over readable state: there IS no readable state to equate
#     against, so the "return the record instead of the primitive's own value"
#     echo has nothing to echo (`uniq-fabricate-count`, `uniq-wrong-identifier`,
#     `uniq-echo-*`, `uniq-stale-report`, and the recorded atk_5/atk_13 shapes).
#   * (6) the REFUSAL clauses — which of the two outcomes the path is entitled to.
#     A removal is something the store can refuse: with a live row protecting the
#     target the real DELETE raises IntegrityError out of the fast branch
#     (deletion.py:274-280 -> subqueries.py:27-42, surfaced through
#     sqlite3/base.py:387-391), so the path can genuinely end without a count, and
#     a spec that only said what a returning path must do would leave that outcome
#     ungoverned. Clause (6a) (Ensures(db.completed_removals ==
#     Old(db.completed_removals) + 1)) says a count
#     comes back only from a removal the store carried OUT, so a refusal cannot be
#     swallowed and answered with a number — not a literal, and not the record's
#     own report field either, which is what makes it independent of clause (3).
#     Clause (6b) (the Exsures) says the reverse: the path may end without a count
#     only by passing on a refusal the store really MADE, and even then it has
#     still spent its one statement on the object's stored identifier. Together
#     they leave an impl no free exit: `uniq-manufacture-refusal`,
#     `uniq-refuse-after-removing`, `uniq-swallow-refusal`,
#     `uniq-swallow-stale-report`, `uniq-refuse-without-asking`,
#     `uniq-guess-refusal-arm` and `uniq-preempt-refusal-order` below are the
#     shapes, each rejected by a different half.
#   * Termination: Requires(MustTerminate(2)) makes this TOTAL rather than partial
#     correctness. Without it an impl could satisfy every clause above and then
#     diverge, verifying vacuously while its faithful patch hangs the suite.
#   * (7) Permission: instance.pk is held at FULL Acc (the path writes it), and
#     that is the ONLY state the path is given. The store's record — its statement
#     tally, the last target, the last report, the carried-out count — and the
#     ledger's total are held by the path at NO permission at all: they are not
#     merely unwritable, they are unreadable. That is the load-bearing asymmetry,
#     and it is the one this repair introduces. Read-only was not enough: reading
#     is free in a model and is not free in a database, so a rival that consulted
#     the record to decide anything — which order to do its work in, which outcome
#     to take, what number to surface — verified for nothing while its faithful
#     refinement pays a real SELECT to ask the store, landing 2 statements where
#     the P2P assertNumQueries(1) test asserts 1. Every part of that record is
#     something the optimized branch genuinely does not hold and can only learn by
#     asking. Removing the read entirely is what closes the class rather than one
#     field at a time: the rivals below that consult it (`uniq-freeread-*`, and the
#     recorded atk_4/atk_14/atk_5/atk_13) now fail with "insufficient permission"
#     at the point of the read, so the shape cannot be WRITTEN, not merely cannot
#     be proved. Forging is closed a level up: the entitlement and the receipts are
#     ABSTRACT (bodyless) predicates, so an impl cannot Fold one into existence to
#     buy a second statement or to mint provenance it did not earn — that fails at
#     TRANSLATION (`abstract.predicate.fold`), not at a clause.
#
# Note on the OFF-BOOKS-HANDLE class (the hole clauses (1)-(3) could not see).
# Every one of those clauses quantifies over the handle the path was HANDED, and
# nothing stopped an impl from constructing a further handle and issuing removals
# through that. Two such rivals VERIFIED against the per-handle-only spec: one
# that paid a decoy removal on a fresh handle before doing the real work, and one
# that did the real work correctly and then paid an extra removal on a fresh
# handle only on part of the input domain. Their faithful patches issue TWO real
# DELETEs, which the P2P exact-statement-count test catches, so both were
# verify-but-not-resolve. Neither could be closed by any postcondition over `db`:
# the second statement is not on `db` at all, so the defect was in the MODEL —
# total cost was simply not an observable. Clause (4) makes it one. Both shapes,
# and the mutations they suggest, are in the reject lane below
# (`uniq-offbooks-*`).
#
# Note on the ungrounded-oracle-echo class. An earlier form of this spec pinned
# the count to a @Pure @ContractOnly function of the identifier alone
# (`Result() == removed_row_count(Old(instance.pk))`) ALONGSIDE the effectful
# primitive, with both modelling the same real callee. That admitted the echo
# cheat: the pure twin carried no cost, so an impl could apply it to obtain the
# surfaced count for FREE while spending its one accounted-for statement
# elsewhere (or on the right identifier, redundantly) — one modelled statement,
# TWO real DELETEs, and the P2P assertNumQueries(1) test caught the difference.
# Both shapes VERIFIED with non-resolving faithful patches (verdict.md atk_3 /
# atk_4). A first repair removed the effect-free path and pinned the count to the
# RECORD the paid-for statement wrote (`Result() == db.last_removal_report`). That
# was not enough, and the reason is instructive: an equation between the return
# value and a READABLE record is satisfiable by an impl that DISCARDS what its own
# statement returned and surfaces the record instead. The record agrees by
# construction, so the clause held while the behaviour was the excluded one — the
# faithful refinement must consult the store a second time to re-derive the count,
# which is exactly what guarantee (3)'s prose forbids, and it does not resolve
# (recorded atk_5, atk_13). The current repair removes the record from the read set
# altogether and pins the count to the store's RECEIPT instead. A receipt is minted
# only by the primitive being answered and carries the count that statement itself
# reported, so there is no longer any value in the model naming a row count that a
# path could obtain without having issued the statement that produced it — and no
# readable field for an echo to read. The echo's other escape — obtain the count
# from a statement issued through a handle nothing accounts for — is closed by the
# entitlement being drawn against the module-wide LEDGER. All four recorded shapes
# are in the reject lane below.
#
# Note on the REFUSAL class (why clause (6) is shaped the way it is). A panel
# reproduced an input on which the real fast branch does NOT return a count at
# all: with a live row protecting the target the DELETE at deletion.py:274-280
# (via subqueries.py:27-42, surfaced through sqlite3/base.py:387-391) is refused
# and IntegrityError propagates. The target row is still fast-deletable — a
# DO_NOTHING back-reference keeps can_fast_delete true — so this is a case
# remove_single_independent genuinely reaches, and axiom_check.py section (c)
# reproduces it executably. The model was silent about it: clauses (1)-(5) only
# said what a returning path must do, so an impl could have taken that exit at
# will. It is fixed by MODELLING the outcome, not by narrowing the domain: the
# handle records how many issued statements the store CARRIED OUT and the
# primitive signals RemovalRefused for one it did not. Four shaping decisions are
# load-bearing:
#   * What the record carries is a POST-state fact — what the store did with a
#     statement that was ISSUED — and never a pre-state predictor of what it will
#     do with one that has not been. This is the decision the whole clause rests
#     on, and it is forced by the real callee twice over. (i) In real code there
#     is no free way to learn in advance what a DELETE will do: the only way is to
#     ask the store, and a rival that consults it first pays a query on EVERY
#     delete, refused or not, which the P2P exact-statement-count assertion
#     (test_do_nothing_qscount, a fast-deletable delete inside
#     assertNumQueries(1)) catches. (ii) The answer is not even a function of what
#     the store holds: the constraint the real refusal comes from is emitted
#     DEFERRABLE INITIALLY DEFERRED, so the same stored rows yield a refusal or a
#     count depending on the transaction context the statement is issued in.
#     A carrier that let an impl read the coming answer off the handle would
#     therefore be claiming something the real callee does not offer, and it would
#     hand every rival a decision procedure the real code cannot have. Two such
#     rivals were measured VERIFYING against exactly that carrier — one that read
#     the predictor once and used it only to order the pk-clearing relative to the
#     statement, one that did the same as an if/else — and their faithful patches
#     do not resolve. Nothing readable now predicts the next answer, so there is
#     nothing of that shape left to branch on: `uniq-guess-refusal-arm` is the
#     partial-domain form in the reject lane.
#   * (6a) is needed as well as (6b), because the two halves close different
#     escapes. Without (6a) an impl could CATCH the refusal and return a number:
#     `uniq-swallow-refusal` returns a literal (clause (3) still catches that one)
#     but `uniq-swallow-stale-report` returns db.last_removal_report itself, which
#     satisfies clause (3) by construction, satisfies the tally/target/total
#     clauses out of the Exsures, and was measured VERIFYING before (6a) was
#     added. Its faithful patch swallows a foreign-key error and reports a count
#     for rows the store never removed.
#   * (6b) says the end-without-a-count outcome is the one where the store carried
#     NOTHING out, which is what makes it unavailable to an impl that got its
#     removal applied and ended that way anyway. Unconditioned it would be a free
#     exit — `uniq-manufacture-refusal` (raise always) and
#     `uniq-refuse-after-removing` / `uniq-preempt-refusal-order` (do the work,
#     then throw the count away and report a refusal) all take it, and they are
#     rejected only because the carried-out count is pinned there.
#   * The Exsures still PINS the tally, the total and the target. A refusal is
#     what the store answers a statement WITH, so the statement was issued —
#     measured, not assumed (axiom_check.py section c.1, conformance_check.py's
#     refusal trials). Without those pins `uniq-refuse-without-asking` (take the
#     exit before issuing anything) VERIFIED, and it is
#     verify-but-not-resolve: in real code the only way to learn what the store
#     will do is to ask it, so its faithful patch
#     pays an extra query on every ordinary delete and fails the P2P
#     exact-statement-count assertions.
#   * Clause (6b) ALSO pins instance.pk on the refused path: the object is left
#     as it was found, still carrying the stored identifier it came in with
#     (instance.pk is Old(instance.pk)). This is measured, not assumed --
#     axiom_check.py section (c.1) asserts `protected.pk is not None` after the
#     store refuses, and conformance_check.py compares the pk after a refusal.
#     With (5) it says the identifier is surrendered EXACTLY when the row it
#     names has been removed: cleared on the carried-out outcome, intact on the
#     refused one. That pairing is what removes the last free observable on this
#     path. While instance.pk was unpinned on the refused path, the returning
#     and refused outcomes were separately satisfiable by clearing the pk EARLY
#     (before the store's answer is in) and by clearing it LATE, so a rival could
#     branch that choice on anything it could read -- including the handle's own
#     record -- and satisfy every clause in both arms. That is exactly what the
#     recorded counterexamples did, and their faithful patches pay a real query
#     to learn what the model let them read for free, failing the P2P
#     exact-statement-count assertion. Clearing early is NOT a faithful reshape:
#     the real path clears the identifier only after the removal has come back,
#     so on a refusal it never clears at all, which is why the clear-then-remove
#     shapes moved from positive controls to rejected rivals below.
from pathlib import Path

INSTANCE = "django__django-11179"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl
# MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================

# uniq-clear-before-asking (was a positive control while instance.pk was
# unpinned on the refused path): capture the stored pk, CLEAR it FIRST, then
# issue the removal for the captured identifier. On the outcome the store
# carries out it is indistinguishable from the reference — same single
# statement, same target, same report, pk cleared at return. It differs on the
# OTHER outcome: it has already surrendered the identifier before the store's
# answer is in, so where the store refuses, it returns an object with no
# identifier though its row is still there. The real path clears the identifier
# only after the removal has come back, so on a refusal it never clears at all
# (axiom_check.py c.1 measures the refused pk surviving). Now expected REJECT.
_POS_REORDER = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    instance.pk = None
    count = remove_rows(db, identifier)
    return count
    # impl-end"""

# uniq-clear-before-asking-inline: the same premature surrender of the
# identifier in a different local-variable shape — drop the `count` temporary
# and return the primitive's report directly. Same defect as
# uniq-clear-before-asking: the identifier is given up before the store has
# said whether the row is gone. Now expected REJECT.
_POS_INLINE = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    instance.pk = None
    return remove_rows(db, identifier)
    # impl-end"""

# pos-control-rethrow: HANDLE the store's refusal explicitly and pass it on,
# instead of letting it propagate implicitly. Behaviourally identical to the
# reference impl on both outcomes (the same one statement on the same identifier;
# a count when the store carried the removal out, the same refusal when it did
# not), which is exactly what a `try/except IntegrityError: raise` around the real
# DELETE would be. Its purpose is to show clause (6b) is ESTABLISHABLE by an impl
# that reaches the exceptional exit deliberately, not only by one that never
# mentions it: if catching and re-signalling the store's own refusal could not
# verify, the Exsures would be demanding something no faithful impl can prove and
# the exceptional clause would be SPEC-TOO-STRONG.
_POS_RETHROW = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = 0  # type: int
    try:
        count = remove_rows(db, identifier)
    except RemovalRefused:
        raise RemovalRefused()
    instance.pk = None
    return count
    # impl-end"""


# pos-control-guarded-clear: a structurally-DIFFERENT but CORRECT impl that
# clears the identifier only after the removal has come back, guarded on the
# report the store returned. Behaviourally identical to the reference on both
# outcomes: one statement on the stored identifier, the count returned is that
# statement's own report, the identifier is surrendered on the carried-out
# outcome and left intact where the store refuses (the guard is unreachable on
# that outcome, since a refusal returns no count at all). If a faithful correct
# impl cannot verify => SPEC-TOO-STRONG.
_POS_GUARDED_CLEAR = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    if count >= 0:
        instance.pk = None
    return count
    # impl-end"""

# pos-control-late-name: a local-variable reshape that keeps the faithful order
# (ask, then surrender the identifier) under a different name for the report.
# Must verify (else SPEC-TOO-STRONG).
_POS_LATE_NAME = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    reported = remove_rows(db, identifier)  # type: int
    instance.pk = None
    return reported
    # impl-end"""

# uniq-refused-clear: do the reference work, but on the refused outcome catch
# the store's rejection and surrender the identifier anyway before passing the
# rejection on. Every cost pin in the exceptional case holds (one statement,
# right identifier, one in total, nothing carried out), so this isolates the new
# left-as-found pin. Its faithful patch tells user code the delete failed while
# marking the object as though its row were gone.
_UNIQ_REFUSED_CLEAR = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    try:
        count = remove_rows(db, identifier)
    except RemovalRefused:
        instance.pk = None
        raise RemovalRefused()
    instance.pk = None
    return count
    # impl-end"""

# uniq-refused-corrupt: the same shape, but the identifier is replaced with a
# DIFFERENT stored value rather than cleared. The object comes back naming a row
# it never named, so a later save or delete would target the wrong row.
_UNIQ_REFUSED_CORRUPT = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    try:
        count = remove_rows(db, identifier)
    except RemovalRefused:
        instance.pk = 0
        raise RemovalRefused()
    instance.pk = None
    return count
    # impl-end"""

# uniq-freeread-clear-order: THE RECORDED COUNTEREXAMPLE FAMILY. Read a part of
# the handle's record BEFORE issuing anything and use it to choose between
# surrendering the identifier early and surrendering it late. Both arms do the
# reference work on the carried-out outcome, so while the refused outcome left
# the identifier free this verified. The read is free in the model but not in
# reality: the branch holds no such counter, so learning it costs a real query
# on every delete, and the exact-statement-count assertion fails.
_UNIQ_FREEREAD_CLEAR_ORDER = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    if db.completed_removals > 0:
        instance.pk = None
        count = remove_rows(db, identifier)
        return count
    count2 = remove_rows(db, identifier)
    instance.pk = None
    return count2
    # impl-end"""

# uniq-freeread-clear-order-ledger: the same defect through the module-wide
# total instead of the handle's own carried-out count.
_UNIQ_FREEREAD_CLEAR_ORDER_LEDGER = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    if LEDGER.total_removal_statements > 0:
        instance.pk = None
        count = remove_rows(db, identifier)
        return count
    count2 = remove_rows(db, identifier)
    instance.pk = None
    return count2
    # impl-end"""

# uniq-clear-early-partial-domain: surrender the identifier early on only PART
# of the domain (small identifiers), keeping the faithful order elsewhere. The
# partial-domain form of uniq-clear-before-asking: a clause that only pinned the
# identifier for some inputs would admit it.
_UNIQ_CLEAR_EARLY_PARTIAL = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    if identifier is not None and identifier < 1000:
        instance.pk = None
        count = remove_rows(db, identifier)
        return count
    count2 = remove_rows(db, identifier)
    instance.pk = None
    return count2
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (soundness/verify) — confirm the precondition admits a normal
# F2P-shaped input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller
# function: a new module-level def changes the projected spec view and breaks
# same_spec. Instead we inject the admissibility witness INSIDE the impl region
# (elided from the spec view), as a leading block that constructs a concrete
# F2P-shaped persisted object (a fast-deletable User has an integer pk; modelled
# as PersistentObject(7)) together with a fresh database handle, and asserts that
# the pair satisfies the function's exact Requires: Acc(adm.pk) from the
# constructor's Ensures, adm.pk is not None, adm.pk inside the representable
# identifier range, and READ access to each of the
# handle's three removal-record fields and its refusal fact. The real impl then
# runs unchanged over
# the actual params. If the precondition could not be established for this
# legitimate input the Assert would fail => PRECOND-TOO-STRONG. This case also
# witnesses that the record's 1/2 permissions are OBTAINABLE — that the read-only
# framing which makes the record unforgeable has not made the precondition
# unsatisfiable for an ordinary caller.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    adm = PersistentObject(7)
    admdb = Database()
    # the function's Requires is establishable for this concrete stored object
    # and a fresh handle: Acc(adm.pk) (from the constructor Ensures), adm.pk is
    # not None, an identifier the store can represent, and the entitlement to
    # spend the one row-removal statement the path is allowed. Note what is NOT
    # asserted here and is no longer askable: read access to the store's own
    # record of what it has done. That record is the store's, not the path's
    # (guarantee (7)); the entitlement plus the receipt the primitive hands back
    # carry the same cost and provenance facts in the forward direction.
    Assert(Acc(adm.pk))
    Assert(adm.pk is not None)
    Assert(-(2 ** 63) <= adm.pk and adm.pk < 2 ** 63)
    Assert(Acc(admdb.removal_statements, 1 / 2))
    Assert(Acc(admdb.last_removal_target, 1 / 2))
    Assert(Acc(admdb.last_removal_report, 1 / 2))
    Assert(Acc(admdb.completed_removals, 1 / 2))
    Assert(RemovalBudget(LEDGER))
    # --- end admissibility witness; the real impl follows unchanged ---
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain — rivals that share the spec exactly and change
# ONLY the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-drop-clear: THE BUG. Omit `instance.pk = None` (exactly model_prepatch.py
# / the pre-patch fast branch). Clauses (1)-(3) still hold, but the cleared-
# identifier guarantee (4) fails. Must be rejected by Ensures(instance.pk is None).
_UNIQ_DROP_CLEAR = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    return count
    # impl-end"""

# uniq-fabricate-count: return a hard-coded literal (1) instead of the removal's
# report. Issues the one row-removal statement for the stored identifier (clauses
# (1) and (2) hold) and clears the pk (clause (4) holds), so the ONLY defect is
# the fabricated count and the rejection is attributable to the count-provenance
# pin alone. The record's report is an opaque non-negative value; the verifier
# cannot prove the literal 1 equals db.last_removal_report.
_UNIQ_FABRICATE_COUNT = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    ignored = remove_rows(db, identifier)  # type: int
    instance.pk = None
    count = 1  # type: int
    return count
    # impl-end"""

# uniq-fabricate-zero: the supporting near-miss — return 0. Same defect as above
# (a literal cannot be proven equal to the opaque recorded report), with clauses
# (1), (2) and (4) satisfied so the rejection isolates the count-provenance pin.
_UNIQ_FABRICATE_ZERO = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    ignored = remove_rows(db, identifier)  # type: int
    instance.pk = None
    count = 0  # type: int
    return count
    # impl-end"""

# uniq-wrong-identifier: issue the removal for the WRONG identifier (the literal
# 0 instead of the object's stored pk) — the model analogue of asking the
# primitive to remove a row keyed by something other than this object's stored
# identifier. Exactly one statement is issued (clause (1) holds), the pk is
# cleared (clause (4) holds), and the returned value IS that statement's own
# report (clause (3) holds) — so the rejection isolates the TARGET pin (2):
# db.last_removal_target is 0, which the verifier cannot prove equal to
# Old(instance.pk).
_UNIQ_WRONG_IDENTIFIER = """    # impl-start
    count = remove_rows(db, 0)
    instance.pk = None
    return count
    # impl-end"""

# uniq-duplicate-removal: issue the row-removal statement TWICE, keeping the
# second report. Clauses (2), (3) and (4) all hold (the last statement targeted
# the stored pk, the returned count is its own report, the pk is cleared) — the
# defect is the COST: the optimized single-object path spends two row-removal
# statements where one suffices. This is EXACTLY the counterexample class an
# earlier spec admitted, when the primitive was modelled as a @Pure function of
# the identifier alone and re-invoking it was mathematically invisible. Rejected
# by the single-statement pin (1): the tally lands on Old+2.
_UNIQ_DUPLICATE_REMOVAL = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end"""

# uniq-extra-removal: keep the FIRST report (so the returned count is textually
# the reference one) but make a second, unused invocation. Clauses (2) and (4)
# hold; the extra statement is pure cost. Rejected by the single-statement pin
# (1) — the tally reaches Old+2. (The provenance pin (3) also no longer holds,
# since the record now carries the SECOND statement's report; the cost pin is the
# one that sees the defect the P2P statement-count test observes.)
_UNIQ_EXTRA_REMOVAL = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    extra = remove_rows(db, identifier)  # type: int
    instance.pk = None
    return count
    # impl-end"""

# uniq-triple-removal: the supporting near-miss at multiplicity three — three
# statements where one suffices. Rejected by the single-statement pin (1).
_UNIQ_TRIPLE_REMOVAL = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    count = remove_rows(db, identifier)
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end"""

# uniq-count-after-clear: read the identifier for the removal AFTER clearing it.
# After `instance.pk = None` the value read is None, not the stored Old pk, so the
# one statement the path pays for targets the post-clear value. This is the
# order-of-operations attack: clearing before capturing the stored identifier
# destroys the value the removal must target. Rejected on the identifier the
# primitive is handed (None where a stored int identifier is required); it can
# never establish db.last_removal_target == Old(instance.pk) (clause 2).
_UNIQ_COUNT_AFTER_CLEAR = """    # impl-start
    instance.pk = None
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    return count
    # impl-end"""

# uniq-echo-count-wrong-target: THE RECORDED ATTACK (verdict.md atk_3). Spend the
# one accounted-for row-removal statement on a DIFFERENT identifier (the literal
# 0), clear the pk, and then surface a row count for the object's stored
# identifier obtained WITHOUT issuing a statement for it. Clause (1) holds (one
# statement) and clause (4) holds (the pk is cleared), and under an earlier spec
# that pinned the count to an effect-free function of the identifier this VERIFIED
# — while its faithful patch issued a SECOND real DELETE to get that count, which
# the P2P exact-statement-count test observes. Under the repaired spec there is no
# value in the model naming a row count for an identifier no statement targeted:
# the only readable count is the record of the statement actually issued. Written
# in the only form that is now expressible (read the record after paying on the
# wrong identifier), it is rejected by the TARGET pin (2).
_UNIQ_ECHO_COUNT_WRONG_TARGET = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    paid = remove_rows(db, 0)  # type: int
    instance.pk = None
    return db.last_removal_report
    # impl-end"""

# uniq-echo-count-extra-statement: the second recorded shape (verdict.md atk_4).
# Pay the accounted-for statement on the RIGHT identifier but surface a count
# obtained by a separate consultation. The only way to obtain a second count is to
# issue a second statement, which the cost pin (1) sees: the tally lands on Old+2.
# Under the earlier spec the second consultation was free (an effect-free function
# of the identifier), so this verified with a faithful patch that issued two real
# DELETEs.
_UNIQ_ECHO_COUNT_EXTRA_STATEMENT = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    paid = remove_rows(db, identifier)  # type: int
    consulted = remove_rows(db, identifier)  # type: int
    instance.pk = None
    return consulted
    # impl-end"""

# uniq-stale-report: return the record's report value read BEFORE any statement is
# issued — i.e. surface a count that predates the removal this path performed.
# Exactly one statement is issued for the stored identifier (clauses (1), (2)
# hold) and the pk is cleared (clause (4) holds), so the rejection isolates the
# count-provenance pin (3): the pre-call report is not the report of the statement
# this path paid for.
_UNIQ_STALE_REPORT = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    stale = db.last_removal_report  # type: int
    ignored = remove_rows(db, identifier)  # type: int
    instance.pk = None
    return stale
    # impl-end"""

# uniq-forge-tally: attempt to satisfy the cost pin (1) by WRITING the handle's
# statement tally instead of issuing a statement. The record is held at 1/2
# permission (read-only to the caller), so the write itself is refused for
# insufficient permission. This probes the framing that makes the whole record
# credible: if an impl could write the record, every one of clauses (1)-(3) could
# be forged without doing any work.
_UNIQ_FORGE_TALLY = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    db.removal_statements = db.removal_statements + 1
    instance.pk = None
    return 0
    # impl-end"""

# uniq-forge-target: same forgery aimed at the TARGET pin (2) — issue the one
# statement on the wrong identifier and then overwrite the recorded target with
# the stored pk. Refused for insufficient permission on the 1/2-held field.
_UNIQ_FORGE_TARGET = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, 0)
    db.last_removal_target = identifier
    instance.pk = None
    return count
    # impl-end"""

# uniq-forge-report: same forgery aimed at the count-provenance pin (3) — issue
# the statement, then overwrite the recorded report with a fabricated value and
# return it. Refused for insufficient permission on the 1/2-held field.
_UNIQ_FORGE_REPORT = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    ignored = remove_rows(db, identifier)  # type: int
    db.last_removal_report = 1
    instance.pk = None
    return 1
    # impl-end"""

# ---------------------------------------------------------------------------
# REFUSAL family. The real fast branch has a second outcome: with a live row
# protecting the target the DELETE is refused and IntegrityError propagates
# (deletion.py:274-280 -> subqueries.py:27-42, surfaced through
# sqlite3/base.py:387-391), on a row that is still fast-deletable. Clause (6)
# governs that outcome from both sides — (6a) a count only from a carried-out
# removal, (6b) a refusal only from a real one, still paid for. These five rivals
# are the ways an impl could otherwise abuse the exit; each is rejected by a
# DIFFERENT half, which is what shows both halves are needed.
# ---------------------------------------------------------------------------

# uniq-manufacture-refusal: take the exceptional exit unconditionally — report a
# refusal the store never made, and do no work at all. Under an unconditioned
# Exsures this would be the perfect cheat (every clause about a returning path is
# vacuous on a path that never returns). Rejected by the exceptional case's COST
# pins: nothing was issued, so the tally is still at Old.
_UNIQ_MANUFACTURE_REFUSAL = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    raise RemovalRefused()
    # impl-end"""

# uniq-refuse-after-removing: do the reference work — one statement, right
# identifier, count in hand — and then throw the count away and report a refusal
# instead. Every cost/target clause in the Exsures IS satisfied here, so this
# isolates the carried-out clause: the count came back, which means the store
# APPLIED the removal, so the outcome where it applied nothing is provably not the
# one reached. Rejected by db.completed_removals == Old(db.completed_removals) in
# the Exsures.
_UNIQ_REFUSE_AFTER_REMOVING = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    raise RemovalRefused()
    # impl-end"""

# uniq-refuse-without-asking: take the end-without-a-count exit on part of the
# domain WITHOUT asking the store — decide from what the record already shows and
# skip the work. Nothing a caller can read says which answer a statement not yet
# issued will get, so no reading licenses this exit; the probe is that the
# exceptional exit is unavailable to an impl that never issued the statement,
# whatever it based the decision on. This isolates the cost half of the Exsures.
_UNIQ_REFUSE_WITHOUT_ASKING = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    if db.completed_removals >= 0:
        raise RemovalRefused()
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end"""

# uniq-swallow-refusal: catch the store's refusal and return a count anyway (the
# literal 0). The returning path's clauses now have to hold on an input where the
# store removed nothing. Rejected by the count-provenance pin (3) — a literal
# cannot be proven equal to the opaque recorded report — and independently by (6a).
_UNIQ_SWALLOW_REFUSAL = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = 0  # type: int
    try:
        count = remove_rows(db, identifier)
    except RemovalRefused:
        count = 0
    instance.pk = None
    return count
    # impl-end"""

# uniq-swallow-stale-report: the SAME swallow, but returning db.last_removal_report
# rather than a literal — so clause (3) is satisfied by construction, and the
# tally, target and total clauses are satisfied out of the Exsures the refusal
# carries. This is the near-miss that isolates clause (6a): it was measured
# VERIFYING with (6a) absent, and it is the exact shape (6a) exists to reject.
_UNIQ_SWALLOW_STALE_REPORT = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = 0  # type: int
    try:
        count = remove_rows(db, identifier)
    except RemovalRefused:
        count = db.last_removal_report
    instance.pk = None
    return count
    # impl-end"""

# uniq-forge-completed: satisfy the carried-out clause by WRITING the record of
# what the store did instead of getting the store to do it — the uniq-forge-*
# frame probe aimed at clause (6). db.completed_removals is held at 1/2
# (read-only to the caller), so the write is refused for insufficient permission.
# Without that framing the clause would be worthless: any impl could book a
# removal the store never carried out and then surface a count for it.
_UNIQ_FORGE_COMPLETED = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    db.completed_removals = db.completed_removals + 1
    instance.pk = None
    return 0
    # impl-end"""

# uniq-guess-refusal-arm: the PARTIAL-DOMAIN form of the same free-exit probe.
# Rather than taking the exceptional exit everywhere, take it only where a
# readable part of the record happens to look a certain way — i.e. try to split
# the domain and serve the end-without-a-count outcome on one side of the split
# without asking the store on that side. There is nothing to split on: which
# answer a statement gets is settled by the store when the statement is issued,
# so an impl cannot arrange to be right about it in advance.
_UNIQ_GUESS_REFUSAL_ARM = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    if db.removal_statements > 0:
        raise RemovalRefused()
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end"""

# uniq-preempt-refusal-order: the CONTROL-FLOW-EFFECT form. Issue the statement,
# but decide from the record — before the store's answer is in — that this is the
# end-without-a-count case, and take that exit even though the removal was
# carried out. The cost pins in the exceptional case are all satisfied (the
# statement really was issued, for the right identifier, one against the handle
# and one in total), so this isolates the carried-out clause: an exit taken where
# the store DID apply the removal is an exit that was not the path's to take.
_UNIQ_PREEMPT_REFUSAL_ORDER = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    instance.pk = None
    if count >= 0:
        raise RemovalRefused()
    return count
    # impl-end"""


# ---------------------------------------------------------------------------
# OFF-BOOKS-HANDLE family. Each of these does the reference work correctly on
# the handle it was given — one statement, right target, own report returned, pk
# cleared, so clauses (1), (2), (3) and (5) ALL hold — and additionally issues a
# row-removal statement through a handle it obtained for itself. The rows that
# second statement removes are just as gone and the statement was just as issued,
# so the faithful patch of each is a fast branch that performs TWO real removals
# and the P2P exact-statement-count assertion fails: verify-but-not-resolve. Each
# must be rejected by the TOTAL cost pin (4), which is the only clause that can
# see a statement that is not on `db`.
# ---------------------------------------------------------------------------

# uniq-offbooks-decoy-first: pay a decoy removal on a fresh handle BEFORE doing
# the reference work. Everything about `db` is textually identical to the
# reference impl, so clauses (1)-(3) and (5) are untouched; only the total moves
# to Old+2. Rejected by (4).
_UNIQ_OFFBOOKS_DECOY_FIRST = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    decoy = Database()
    extra = remove_rows(decoy, identifier)  # type: int
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end"""

# uniq-offbooks-decoy-after: the same defect with the off-books removal issued
# AFTER the reference work and the clear, so no data-flow from it reaches the
# returned value at all — it is pure extra cost, invisible to every per-handle
# clause. Rejected by (4).
_UNIQ_OFFBOOKS_DECOY_AFTER = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    instance.pk = None
    spare = Database()
    extra = remove_rows(spare, identifier)  # type: int
    return count
    # impl-end"""

# uniq-offbooks-partial-domain: correct on part of the precondition's domain and
# off-books elsewhere — the reference work always runs, but a second handle is
# used only when the stored identifier is positive. A spec that pinned only the
# handful of inputs the other clauses constrain would miss this; the total pin
# holds on the WHOLE domain, so the branch cannot be hidden in a sub-domain.
# Rejected by (4).
_UNIQ_OFFBOOKS_PARTIAL_DOMAIN = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    instance.pk = None
    if identifier > 0:
        other = Database()
        extra = remove_rows(other, identifier)  # type: int
    return count
    # impl-end"""

# uniq-offbooks-echo-count: the ungrounded-oracle echo rebuilt on top of the
# off-books handle — spend the accounted-for statement on the WRONG identifier
# (so `db`'s record is a decoy) and obtain the surfaced count from a statement
# issued through a handle of the impl's own making for the RIGHT identifier. This
# is the shape the per-handle spec admitted with the count coming from a free
# effect-free twin; with the twin gone the only source of a count is a statement,
# and clause (4) counts it. Rejected by (4) (and by (2)/(3) on `db`'s decoy
# record), so no count can be sourced off the books.
_UNIQ_OFFBOOKS_ECHO_COUNT = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    paid = remove_rows(db, 0)  # type: int
    shadow = Database()
    echoed = remove_rows(shadow, identifier)  # type: int
    instance.pk = None
    return echoed
    # impl-end"""

# uniq-forge-ledger: attempt to satisfy the TOTAL cost pin (4) by WRITING the
# module-wide ledger instead of issuing a statement — the ledger analogue of the
# uniq-forge-* record probes. The ledger is held at 1/2 (read-only to the
# caller), so the write is refused for insufficient permission. Without that
# framing an impl could pay any number of off-books removals and then decrement
# the total back to Old+1.
_UNIQ_FORGE_LEDGER = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    spare = Database()
    extra = remove_rows(spare, identifier)  # type: int
    LEDGER.total_removal_statements = LEDGER.total_removal_statements - 1
    instance.pk = None
    return count
    # impl-end"""

# uniq-offbooks-only: do ALL the work off the books — the reference handle `db`
# is never touched at all, while a handle of the impl's own making receives the
# one removal. The total lands on Old+1, so clause (4) alone is satisfied; the
# per-handle clauses (1)-(3) are what reject it. Included as the CONVERSE probe:
# it confirms clause (4) has not made the per-handle clauses redundant, so the
# two together mean "exactly one removal, and it was on the handle you passed".
_UNIQ_OFFBOOKS_ONLY = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    elsewhere = Database()
    count = remove_rows(elsewhere, identifier)
    instance.pk = None
    return count
    # impl-end"""

# uniq-diverge: satisfy every value clause and then fail to RETURN — a non-
# terminating tail after the removal. Partial correctness would admit this
# vacuously while the faithful patch hangs the suite. Rejected by the
# MustTerminate obligation the precondition carries.
_UNIQ_DIVERGE = """    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    instance.pk = None
    while count >= 0:
        Invariant(count >= 0)
        count = count + 1
    return count
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "uniq-clear-before-asking",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "refinement": "surrender the identifier BEFORE issuing the removal. On the "
                      "outcome the store carries out this is indistinguishable from "
                      "the reference, which is why it is a rival and not obviously "
                      "wrong: it differs only where the store REFUSES, and there it "
                      "hands back an object carrying no identifier though its row is "
                      "still in the table. Its faithful patch clears the attribute "
                      "before the DELETE comes back, so a constraint failure leaves a "
                      "live row modelled by an object that no longer names it — the "
                      "object cannot be re-saved or re-deleted onto its own row.",
        "rationale": "rejected by the left-as-found half of the exceptional case: "
                     "'Assertion (instance.pk is Old(instance.pk)) might not hold.' "
                     "The real path reaches its clear only after the removal has come "
                     "back, so on a refusal it never clears (measured: axiom_check.py "
                     "section c.1 asserts the refused object's pk survives). This case "
                     "and pos-control-guarded-clear together bracket the clause: "
                     "clearing LATE must verify, clearing EARLY must not.",
    },
    {
        "id": "uniq-clear-before-asking-inline",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _POS_INLINE),
        "refinement": "the same premature surrender of the identifier in a different "
                      "local-variable shape (no `count` temporary). Included so the "
                      "clause is shown to bite on the BEHAVIOUR rather than on one "
                      "syntactic arrangement of it.",
        "rationale": "rejected for the same reason as uniq-clear-before-asking: "
                     "'Assertion (instance.pk is Old(instance.pk)) might not hold.'",
    },
    {
        "id": "pos-control-guarded-clear",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_GUARDED_CLEAR),
        "rationale": "structurally-different CORRECT impl that keeps the faithful "
                     "order: ask the store first, surrender the identifier only after "
                     "the removal has come back, under a guard on the report. "
                     "Behaviourally identical to the reference on BOTH outcomes — one "
                     "statement on the stored identifier, that statement's own report "
                     "returned, the identifier cleared where the row is gone and left "
                     "intact where the store refuses. This is the positive control the "
                     "new left-as-found pin must NOT break: if a faithful impl that "
                     "clears late cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-late-name",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_LATE_NAME),
        "rationale": "local-variable reshape preserving the faithful order (ask, then "
                     "surrender the identifier) under a different name for the report. "
                     "Must satisfy the cost, target, provenance, cleared-identifier "
                     "and left-as-found clauses. If it cannot verify => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-rethrow",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_RETHROW),
        "rationale": "positive control for the EXCEPTIONAL half of clause (6). Catch "
                     "the store's refusal and pass it on explicitly instead of letting "
                     "it propagate — behaviourally identical to the reference impl on "
                     "both outcomes, and exactly what `try: ... except IntegrityError: "
                     "raise` around the real delete_batch would be. It must verify: the "
                     "refusal it re-signals is the store's own, so the Exsures' "
                     "carried-out pin db.completed_removals == Old(db.completed_"
                     "removals) is available from the "
                     "primitive's own Exsures, as are the tally, target and total. If "
                     "an impl that reaches the exceptional exit deliberately could not "
                     "verify, clause (6b) would be demanding something no faithful impl "
                     "can prove => SPEC-TOO-STRONG. It also keeps the real order (it "
                     "clears the identifier only after the removal came back), so with "
                     "uniq-clear-before-asking on the other side it brackets the "
                     "left-as-found pin: clearing LATE must verify, clearing EARLY must "
                     "not.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "(elided from the spec view, so same_spec holds) builds a "
                     "concrete F2P-shaped persisted object PersistentObject(7) (a "
                     "fast-deletable object with an integer pk) plus a fresh handle "
                     "Database(), and asserts the pair satisfies the function's exact "
                     "Requires: Acc(adm.pk) (from the constructor Ensures), adm.pk is "
                     "not None, and 1/2 (read) access to each of the handle's three "
                     "removal-record fields. The real impl then runs unchanged. If "
                     "the precondition could not be established for this legitimate "
                     "input the Assert fails => PRECOND-TOO-STRONG. This also "
                     "witnesses that the read-only framing which makes the record "
                     "unforgeable has NOT made the precondition unsatisfiable for an "
                     "ordinary caller.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-drop-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_CLEAR),
        "refinement": "this IS the pre-patch behaviour that model_prepatch.py "
                      "reproduces and G-DIFF flags: the fast single-object branch "
                      "removes the row and returns the count but never runs "
                      "setattr(instance, model._meta.pk.attname, None). The sole F2P "
                      "test_fast_delete_instance_set_pk_none creates a fast-deletable "
                      "User, deletes it, and asserts self.assertIsNone(u.pk); with the "
                      "clearing statement absent u.pk keeps its stored value and the "
                      "assertIsNone fails. Its faithful real patch (the un-patched "
                      "fast branch) is exactly what does NOT resolve.",
        "rationale": "rejected by Ensures(instance.pk is None): with the clear "
                     "dropped, instance.pk is still the non-None stored pk at return, "
                     "violating the cleared-identifier guarantee (postcondition clause "
                     "(4)).",
    },
    {
        "id": "uniq-fabricate-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FABRICATE_COUNT),
        "refinement": "returning a hard-coded 1 fabricates the surfaced deleted-row "
                      "count. The real delete_batch returns the DB-reported rowcount "
                      "(1 for a live single row, but 0 when no row matches). P2P "
                      "test_model_delete_returns_num_rows / "
                      "test_queryset_delete_returns_num_rows observe the actual count; "
                      "a faithful patch that returned a constant 1 would report a "
                      "deletion when nothing was deleted and would not resolve those "
                      "count-observing tests. The one row-removal statement is still "
                      "issued and the pk still cleared, so the rejection isolates the "
                      "count pin.",
        "rationale": "rejected by Ensures(Result() == db.last_removal_report): the "
                     "report of the statement that was issued is an opaque non-"
                     "negative value; the verifier cannot prove the literal 1 equals "
                     "it.",
    },
    {
        "id": "uniq-wrong-identifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_WRONG_IDENTIFIER),
        "refinement": "issuing the removal for an identifier other than the object's "
                      "stored pk corresponds to a patch that asked delete_batch to "
                      "remove a row keyed by the wrong identifier — it would "
                      "query/delete the wrong row (or none), surfacing a count for the "
                      "wrong object. The F2P/P2P count and deletion-order tests observe "
                      "the count of the object actually deleted; this does not resolve. "
                      "Exactly one statement is still issued, so the rejection is "
                      "attributable to the target pin and not to the cost pin.",
        "rationale": "rejected by Ensures(db.last_removal_target == Old(instance.pk)): "
                     "the one statement the path paid for recorded target 0, and the "
                     "verifier cannot prove 0 equals the object's stored identifier.",
    },
    {
        "id": "uniq-count-after-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_COUNT_AFTER_CLEAR),
        "refinement": "clearing instance.pk BEFORE reading it for the count "
                      "corresponds to a patch that moved the setattr above the "
                      "delete_batch call: it would then pass the now-cleared pk "
                      "(None) to delete_batch and remove nothing / raise, surfacing a "
                      "wrong (zero) count for a live object — failing the count- and "
                      "deletion-observing F2P/P2P tests. The order matters: the "
                      "stored identifier must be captured before it is cleared.",
        "rationale": "rejected because after instance.pk = None the identifier read is "
                     "None, not Old(instance.pk): the primitive requires a stored int "
                     "identifier, and even were it accepted the recorded target could "
                     "not be proven equal to Old(instance.pk) (clause 2).",
    },
    {
        "id": "uniq-duplicate-removal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DUPLICATE_REMOVAL),
        "refinement": "invoking the row-removal primitive twice corresponds to a patch "
                      "whose fast branch runs "
                      "sql.DeleteQuery(model).delete_batch([instance.pk], self.using) "
                      "twice. A one-element pk list is removed by exactly ONE SQL "
                      "statement (delete_batch loops over "
                      "range(0, len(pk_list), GET_ITERATOR_CHUNK_SIZE), i.e. one "
                      "iteration for one pk), so a second invocation issues a second "
                      "DELETE. The surfaced count and the cleared pk are both still "
                      "right, so the F2P passes — but P2P test_do_nothing_qscount wraps "
                      "a fast-deletable b.delete() in self.assertNumQueries(1) and sees "
                      "two queries. This shape VERIFIED against an earlier spec and "
                      "its faithful patch did NOT resolve (recorded in verdict.md); "
                      "the cost clause is what closes it.",
        "rationale": "rejected by Ensures(db.removal_statements == Old("
                     "db.removal_statements) + 1): each remove_rows invocation advances "
                     "the tally by exactly 1, so two invocations land on Old+2 and the "
                     "single-statement postcondition fails. Note this is NOT reachable "
                     "via the count-provenance pin: the second statement's report IS "
                     "the recorded one, which is precisely why a purely functional "
                     "model of the primitive could not reject it.",
    },
    {
        "id": "uniq-extra-removal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_EXTRA_REMOVAL),
        "refinement": "keeping the first report but making a second, unused invocation "
                      "corresponds to a patch whose fast branch issues an extra "
                      "delete_batch whose result it discards — the returned count is "
                      "textually the gold one, yet the delete costs two SQL statements. "
                      "test_do_nothing_qscount (assertNumQueries(1)) observes the extra "
                      "query. This shape too VERIFIED against an earlier spec with "
                      "a non-resolving faithful patch (verdict.md).",
        "rationale": "rejected by Ensures(db.removal_statements == Old("
                     "db.removal_statements) + 1): the tally reaches Old+2. The count-"
                     "provenance pin cannot see this defect at all — the returned value "
                     "is unchanged — so the cost clause is load-bearing here.",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-triple-removal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_TRIPLE_REMOVAL),
        "refinement": "three delete_batch invocations where one suffices: three SQL "
                      "DELETEs for a single fast-deletable object, so "
                      "test_do_nothing_qscount's assertNumQueries(1) fails. Supporting "
                      "near-miss at multiplicity three for the duplicate-removal "
                      "attack.",
        "rationale": "rejected by Ensures(db.removal_statements == Old("
                     "db.removal_statements) + 1): the tally reaches Old+3.",
    },
    {
        "id": "uniq-fabricate-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FABRICATE_ZERO),
        "refinement": "returning a hard-coded 0 always reports 'no rows deleted'. A "
                      "faithful patch returning a constant 0 would tell user code "
                      "nothing was deleted even when a live row was removed, failing "
                      "test_model_delete_returns_num_rows (which asserts the count of "
                      "the deleted object). Supporting near-miss for the fabricated-"
                      "count attack.",
        "rationale": "rejected by Ensures(Result() == db.last_removal_report): the "
                     "literal 0 cannot be proven equal to the opaque report the issued "
                     "statement recorded (only >= 0 is known).",
    },

    # ---- the recorded verify-but-not-resolve counterexample classes ----
    {
        "id": "uniq-echo-count-wrong-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ECHO_COUNT_WRONG_TARGET),
        "refinement": "this is the recorded counterexample (verdict.md atk_3): the one "
                      "accounted-for row-removal statement is spent on a DIFFERENT "
                      "identifier, and the count surfaced for the object's own "
                      "identifier is obtained by a separate consultation. Its faithful "
                      "patch's fast branch calls "
                      "sql.DeleteQuery(model).delete_batch(...) twice — once for the "
                      "decoy identifier and once to get the count it returns — because "
                      "the only real way to learn a row count for an identifier is to "
                      "issue a statement for it. It was EXECUTED through the official "
                      "harness: F2P test_fast_delete_instance_set_pk_none PASSES while "
                      "P2P test_do_nothing_qscount (delete.tests.OnDeleteTests) FAILS "
                      "on assertNumQueries(1), resolved=false, completed=true, 2/2 "
                      "attempts, consistent-not-flaky.",
        "rationale": "rejected by Ensures(db.last_removal_target == Old(instance.pk)): "
                     "the model no longer contains any value naming a row count for an "
                     "identifier that no statement targeted — the only readable count "
                     "is the record of the statement actually issued — so the echo has "
                     "nothing to echo, and paying the statement on the literal 0 leaves "
                     "db.last_removal_target == 0, which cannot be proven equal to the "
                     "stored identifier.",
    },
    {
        "id": "uniq-echo-count-extra-statement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ECHO_COUNT_EXTRA_STATEMENT),
        "refinement": "the second recorded shape (verdict.md atk_4): pay the "
                      "accounted-for statement on the RIGHT identifier, then obtain the "
                      "count by consulting the database again. Its faithful patch also "
                      "issues two DELETEs for one fast-deletable object; executed "
                      "through the harness it gave the identical signature — F2P passes, "
                      "P2P failure=[test_do_nothing_qscount], resolved=false, "
                      "completed=true, 2/2 attempts. Independent confirmation of the "
                      "same hole.",
        "rationale": "rejected by Ensures(db.removal_statements == Old("
                     "db.removal_statements) + 1): a second consultation now costs a "
                     "second statement (the only source of a row count is the effectful "
                     "primitive), so the tally lands on Old+2. Both the cost pin and "
                     "the count-provenance pin are needed: the cost pin alone was "
                     "satisfiable while the count came from an effect-free path.",
    },
    {
        "id": "uniq-stale-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_STALE_REPORT),
        "refinement": "surfacing a count read BEFORE the removal corresponds to a patch "
                      "that returns a row count belonging to some earlier statement "
                      "rather than the one it just issued — the caller's reported "
                      "deleted-row count would be unrelated to this delete, failing the "
                      "count-observing tests (test_model_delete_returns_num_rows / "
                      "test_queryset_delete_returns_num_rows). Exactly one statement is "
                      "issued for the stored identifier and the pk is cleared, so the "
                      "rejection isolates the count-provenance pin.",
        "rationale": "rejected by Ensures(Result() == db.last_removal_report): the "
                     "pre-call value is not provably equal to the report the issued "
                     "statement recorded. This is the class that makes provenance, not "
                     "mere non-negativity, the load-bearing property of the count.",
    },

    # ---- the record must be unforgeable (frame/permission probes) ----
    {
        "id": "uniq-forge-tally",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FORGE_TALLY),
        "refinement": "no real fast branch can make the database report a statement it "
                      "never executed; a patch that 'accounted for' a DELETE without "
                      "issuing it removes no row at all, so the F2P deletion itself "
                      "would not happen. The observable statement count belongs to the "
                      "database, not to the caller.",
        "rationale": "rejected for insufficient permission: the handle's removal record "
                     "is held at 1/2 (read-only to the caller), so an impl cannot write "
                     "db.removal_statements. This probe is what makes the cost pin "
                     "credible — were the record writable, clauses (1)-(3) could all be "
                     "forged without doing any work.",
    },
    {
        "id": "uniq-forge-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FORGE_TARGET),
        "refinement": "same impossibility aimed at the target pin: spend the statement "
                      "on the wrong identifier and then claim it targeted the right "
                      "one. A real removal targets whatever identifier it was given; "
                      "the wrong row (or no row) is deleted regardless of what the "
                      "caller asserts afterwards.",
        "rationale": "rejected for insufficient permission on db.last_removal_target "
                     "(held at 1/2). The target pin cannot be satisfied by relabelling "
                     "the statement, only by issuing it for the stored identifier.",
    },
    {
        "id": "uniq-forge-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FORGE_REPORT),
        "refinement": "same impossibility aimed at the count-provenance pin: issue the "
                      "statement, then overwrite what it reported. A real delete's "
                      "rowcount comes from the database cursor; user code sees that "
                      "number, and a patch substituting its own would misreport "
                      "deletions (0 rows reported as 1).",
        "rationale": "rejected for insufficient permission on db.last_removal_report "
                     "(held at 1/2). Provenance is therefore not restatable by the "
                     "impl: the returned count must be the number the issued statement "
                     "itself produced.",
    },

    # ---- the refusal must be neither manufacturable nor swallowable ----
    # Clause (6) has two halves and these six rivals split across them: three are
    # rejected by the Exsures' condition or its cost pins (6b), two by the returning
    # clause (6a) / the count pin (3), and one by the permission framing that makes
    # the condition unforgeable. Rejecting each by a DIFFERENT clause is what shows
    # neither half is redundant.
    {
        "id": "uniq-manufacture-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_MANUFACTURE_REFUSAL),
        "refinement": "raising unconditionally corresponds to a fast branch that reports "
                      "an IntegrityError without ever running the DELETE — no row is "
                      "removed, no count reaches user code and the pk is never cleared. "
                      "The sole F2P test_fast_delete_instance_set_pk_none deletes a "
                      "fast-deletable User and asserts assertIsNone(u.pk); a raise "
                      "propagates out of Collector.delete() and the test errors before "
                      "the assertion, so this does not resolve. It is the sharpest test "
                      "of the exceptional clause because EVERY clause about a returning "
                      "path is vacuous on a path that never returns: under an "
                      "unconditioned Exsures this impl would verify while doing no work "
                      "at all.",
        "rationale": "rejected by the Exsures' COST pins: 'Postcondition of "
                     "remove_single_independent might not hold. Assertion "
                     "(db.removal_statements == (Old(db.removal_statements) + 1)) might "
                     "not hold.' Nothing in the impl issued anything — it never asked — "
                     "so the exceptional exit is not available to it. This is why the "
                     "exceptional case pins what the outcome COST rather than being "
                     "stated unconditionally.",
    },
    {
        "id": "uniq-refuse-after-removing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_REFUSE_AFTER_REMOVING),
        "refinement": "do the whole job — issue the one DELETE for the stored pk, take "
                      "the rowcount — and then discard it and raise IntegrityError "
                      "anyway. A real patch shaped like this deletes the row but reports "
                      "failure, so the caller never gets its count and never sees the pk "
                      "cleared; the F2P errors out. Note the contrast with "
                      "uniq-manufacture-refusal: here the tally, target and total pins "
                      "in the Exsures are all genuinely satisfied (the statement really "
                      "was issued for the right identifier), so this rival isolates the "
                      "condition from the cost.",
        "rationale": "rejected by the carried-out pin, for the opposite reason: "
                     "'Assertion (db.completed_removals == Old(db.completed_removals)) "
                     "might not hold.' remove_rows RETURNED a "
                     "count, and the axiom's Ensures(db.completed_removals == "
                     "Old(db.completed_removals) + 1) means "
                     "a returned count is itself proof the store applied the removal — "
                     "so the impl has, at that point, proved it may NOT take the "
                     "exceptional exit.",
    },
    {
        "id": "uniq-refuse-without-asking",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_REFUSE_WITHOUT_ASKING),
        "refinement": "take the end-without-a-count exit without issuing the "
                      "statement — a patch that pre-checks for "
                      "protecting rows and short-circuits. The outcome it reports is "
                      "truthful, so the condition holds; what it skips is the work. Its "
                      "faithful real form cannot resolve either: learning in advance "
                      "what the store will do with a DELETE costs a query of its own, "
                      "and P2P test_do_nothing_qscount wraps "
                      "a fast-deletable delete() in assertNumQueries(1), which the "
                      "pre-check would break on EVERY delete, refused or not. That is "
                      "why this is a reject case and not a positive control.",
        "rationale": "rejected by the cost half of the Exsures: 'Assertion "
                     "(db.removal_statements == (Old(db.removal_statements) + 1)) might "
                     "not hold.' The exceptional exit is not a licence to do less — the "
                     "only way to find out what the store will do is to ask it, so the "
                     "statement was issued and cost exactly one against the "
                     "handle (and one in total). Without these pins on the exceptional "
                     "path a rival could take the free exit on part of the domain.",
    },
    {
        "id": "uniq-swallow-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SWALLOW_REFUSAL),
        "refinement": "catch the store's refusal and answer it with a number anyway "
                      "(0) — a patch wrapping delete_batch in `except IntegrityError: "
                      "return 0`. It reports 'nothing deleted, no error' where Django "
                      "propagates the IntegrityError, and it clears the pk of an object "
                      "whose row is still there. P2P "
                      "test_fast_delete_instance_set_pk_none's sibling behaviour and the "
                      "count-observing tests (test_model_delete_returns_num_rows) both "
                      "see the difference: a swallowed constraint failure is a silently "
                      "wrong answer, not a slower one.",
        "rationale": "rejected by the count-provenance pin (3): 'Assertion (Result() == "
                     "db.last_removal_report) might not hold.' On the caught path the "
                     "recorded report is whatever an earlier statement left there — the "
                     "refused statement reported nothing — so the literal 0 cannot be "
                     "proven equal to it. Clause (6a) rejects it independently.",
    },
    {
        "id": "uniq-swallow-stale-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SWALLOW_STALE_REPORT),
        "refinement": "the same swallow, made verifier-proof: return db.last_removal_"
                      "report rather than a literal, so the count-provenance pin is "
                      "satisfied by construction and the tally/target/total pins come "
                      "free out of the refusal's own Exsures. Behaviourally it is the "
                      "worst of the family — it converts a constraint violation into a "
                      "plausible-looking count belonging to some earlier statement, and "
                      "clears the pk of a row that is still in the table. This case is "
                      "the reason clause (6a) exists: with (6a) absent it was measured "
                      "VERIFYING, i.e. pinning the refused path's cost had opened a hole "
                      "on the returning path.",
        "rationale": "rejected by clause (6a): 'Assertion (db.completed_removals == "
                     "(Old(db.completed_removals) + 1)) "
                     "might not hold.' Returning at all is something only a carried-out "
                     "removal entitles the path to, so no reading — however well-sourced "
                     "— can be passed off as this removal's count. (6a) and (6b) are "
                     "therefore both load-bearing: (6b) alone admits this rival, and "
                     "(6a) alone admits uniq-refuse-without-asking.",
    },
    {
        "id": "uniq-forge-completed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FORGE_COMPLETED),
        "refinement": "the uniq-forge-* frame probe aimed at clause (6): book a "
                      "carried-out removal by WRITING the record of what the store did, "
                      "rather than getting the store to do it. No real fast branch can "
                      "make the database report having applied a DELETE it never "
                      "applied; whether a removal was carried out is a fact about what "
                      "happened at the store, exactly like the statement count.",
        "rationale": "rejected for insufficient permission on db.completed_removals "
                     "(held at 1/2, read-only to the caller). This probe is what makes "
                     "clause (6) credible: were the carried-out record writable, an "
                     "impl could book a removal the store never applied and then "
                     "surface a count for it, and both halves of (6) would be free.",
    },
    {
        "id": "uniq-guess-refusal-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_GUESS_REFUSAL_ARM),
        "refinement": "the PARTIAL-DOMAIN form of the free-exit probe: serve the "
                      "end-without-a-count outcome on one part of the domain, chosen by "
                      "what a readable part of the record happens to show, without "
                      "asking the store on that part. Its faithful patch is a fast "
                      "branch that reports a constraint failure for deletes the store "
                      "would have carried out — the F2P's own object among them — so "
                      "the delete raises where Django returns a count and it does not "
                      "resolve. It is the shape that is only available if something a "
                      "caller can read predicts the store's answer.",
        "rationale": "rejected by the exceptional case's cost pins: the exit is taken "
                     "with no statement issued, so 'Assertion (db.removal_statements == "
                     "(Old(db.removal_statements) + 1)) might not hold.' Nothing "
                     "readable licenses the exit, because nothing readable says what "
                     "the store will do with a statement not yet issued — which is the "
                     "reason the record carries only what has ALREADY happened.",
    },
    {
        "id": "uniq-preempt-refusal-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_PREEMPT_REFUSAL_ORDER),
        "refinement": "the CONTROL-FLOW-EFFECT form: issue the one statement, have the "
                      "store carry the removal out, and still end without a count. Its "
                      "faithful patch deletes the row and then raises anyway, so user "
                      "code is told the delete failed while the row is gone and the "
                      "count never surfaces — the F2P errors out. Every COST pin in the "
                      "exceptional case is genuinely satisfied here (one statement, "
                      "right identifier, one in total), so this rival isolates the "
                      "carried-out clause from the cost clauses.",
        "rationale": "rejected by the carried-out half of the exceptional case: "
                     "'Assertion (db.completed_removals == Old(db.completed_removals)) "
                     "might not hold.' The store applied the removal, which the record "
                     "shows, so the end-without-a-count outcome — the outcome where "
                     "nothing was applied — is provably not the one this path reached.",
    },

    # ---- off-books-handle: the total-cost hole (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-offbooks-decoy-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OFFBOOKS_DECOY_FIRST),
        "refinement": "its faithful patch is a fast branch that issues a row-removal "
                      "for the object's identifier through a second connection/query "
                      "before doing the accounted-for removal — two real DELETEs where "
                      "the optimized path promises one. The F2P still passes (the pk is "
                      "cleared) but the P2P exact-statement-count assertion on a fast-"
                      "deletable delete sees two statements and fails, so it does NOT "
                      "resolve. This is the recorded verify-but-not-resolve shape the "
                      "per-handle-only spec admitted.",
        "rationale": "rejected by Ensures(LEDGER.total_removal_statements == Old(...) "
                      "+ 1): the decoy advances the module-wide total, so it reaches "
                      "Old+2. Everything about `db` is identical to the reference impl, "
                      "so clauses (1), (2), (3) and (5) all still hold — the TOTAL pin "
                      "is the only clause that can see a statement issued through a "
                      "handle other than the one passed in.",
    },
    {
        "id": "uniq-offbooks-decoy-after",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OFFBOOKS_DECOY_AFTER),
        "refinement": "the same two-real-DELETE faithful patch with the extra removal "
                      "issued after the accounted-for one, so no value flows out of it "
                      "— pure extra cost. Same P2P statement-count failure, so it does "
                      "NOT resolve.",
        "rationale": "rejected by Ensures(LEDGER.total_removal_statements == Old(...) "
                      "+ 1): the total reaches Old+2. No per-handle clause is violated "
                      "at all here, which is precisely why the total pin is needed.",
    },
    {
        "id": "uniq-offbooks-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OFFBOOKS_PARTIAL_DOMAIN),
        "refinement": "the partial-domain variant: its faithful patch performs the "
                      "extra removal only for objects whose stored identifier is "
                      "positive — i.e. for every ordinary auto-increment primary key, "
                      "which is exactly what the P2P statement-count test deletes. Two "
                      "real DELETEs on that input, so it does NOT resolve.",
        "rationale": "rejected by Ensures(LEDGER.total_removal_statements == Old(...) "
                      "+ 1): the clause holds over the WHOLE precondition domain, so "
                      "the verifier cannot discharge it on the identifier > 0 branch "
                      "where the total reaches Old+2. A rival cannot hide the extra "
                      "removal in a sub-domain the other clauses happen not to pin.",
    },
    {
        "id": "uniq-offbooks-echo-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OFFBOOKS_ECHO_COUNT),
        "refinement": "the ungrounded-oracle echo rebuilt over an unaccounted handle: "
                      "its faithful patch spends one DELETE on the wrong identifier and "
                      "obtains the surfaced count from a SECOND DELETE for the right "
                      "one. Two real statements and the wrong row removed by the first, "
                      "so both the statement-count P2P and the deletion itself are "
                      "wrong; it does NOT resolve.",
        "rationale": "rejected by Ensures(LEDGER.total_removal_statements == Old(...) "
                      "+ 1) — the total reaches Old+2 — and independently by the TARGET "
                      "pin (2) and provenance pin (3) on `db`'s decoy record. With no "
                      "effect-free twin in the model and the total counted, there is no "
                      "way to source a row count that no accounted-for statement "
                      "produced.",
    },
    {
        "id": "uniq-forge-ledger",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FORGE_LEDGER),
        "refinement": "a fast branch that issues two real DELETEs and then 'corrects' "
                      "the books. The correction is not something real code can do — "
                      "the number of statements the database received is a fact about "
                      "the database — so the faithful patch is just the two-DELETE "
                      "branch, which fails the P2P statement-count assertion and does "
                      "NOT resolve.",
        "rationale": "rejected for insufficient permission: the module-wide ledger is "
                      "held at 1/2 (read-only to the caller), so the write itself is "
                      "refused — 'Assignment might fail. There might be insufficient "
                      "permission to access LEDGER.total_removal_statements.' This is "
                      "the frame probe for clause (4): if an impl could write the "
                      "ledger it could pay any number of off-books removals and then "
                      "restore the total, making the total pin forgeable.",
    },
    {
        "id": "uniq-offbooks-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OFFBOOKS_ONLY),
        "refinement": "its faithful patch removes the row through a connection other "
                      "than the one the delete was asked to use (`self.using`), so the "
                      "row targeted by the caller's database is never removed while a "
                      "row elsewhere is. The deletion tests observe the object on the "
                      "alias they deleted through, so it does NOT resolve.",
        "rationale": "rejected by the PER-HANDLE clauses: db.removal_statements stays "
                      "at Old (clause 1), and nothing establishes db.last_removal_target "
                      "or db.last_removal_report (clauses 2, 3). Included as the CONVERSE "
                      "probe for clause (4): the total here IS Old+1, so it confirms the "
                      "new total pin has not made the per-handle clauses redundant. The "
                      "two together say 'exactly one removal in total, and it was issued "
                      "against the handle you were given'.",
    },

    # ---- total, not partial, correctness ----
    {
        "id": "uniq-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DIVERGE),
        "refinement": "a fast branch that removes the row, clears the pk and then never "
                      "returns satisfies every value guarantee while hanging the caller: "
                      "the faithful patch never completes a single delete() call, so the "
                      "whole delete test module times out rather than resolving. Under "
                      "partial correctness this rival verified vacuously (recorded in "
                      "verdict.md as the diverging-tail candidate); the resolve run for "
                      "it did not complete, which is exactly the symptom.",
        "rationale": "rejected by the termination obligation the precondition carries "
                     "(Requires(MustTerminate(2))): the unbounded loop cannot discharge "
                     "it — 'Obligation leak check failed. Loop might not take all "
                     "unsatisfied obligations from the context.' The spec therefore "
                     "claims TOTAL correctness; without this an impl could meet every "
                     "clause above and still diverge.",
    },
    {
        "id": "uniq-refused-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_REFUSED_CLEAR),
        "refinement": "catch the store's rejection and surrender the identifier anyway "
                      "before passing the rejection on. Every COST pin in the "
                      "exceptional case is genuinely satisfied (one statement, right "
                      "identifier, one in total, nothing carried out), so this rival "
                      "isolates the left-as-found pin from the cost pins. Its faithful "
                      "patch reports the delete as failed while marking the object as "
                      "though its row were gone.",
        "rationale": "rejected by the left-as-found half of the exceptional case: "
                     "'Assertion (instance.pk is Old(instance.pk)) might not hold.'",
    },
    {
        "id": "uniq-refused-corrupt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_REFUSED_CORRUPT),
        "refinement": "the BOUNDARY form: on the refused outcome replace the identifier "
                      "with a different stored value (zero) instead of clearing it, so "
                      "the object comes back naming a row it never named. Shows the pin "
                      "is 'left as found', not merely 'not cleared'.",
        "rationale": "rejected by the left-as-found half of the exceptional case: "
                     "'Assertion (instance.pk is Old(instance.pk)) might not hold.'",
    },
    {
        "id": "uniq-freeread-clear-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FREEREAD_CLEAR_ORDER),
        "refinement": "THE RECORDED COUNTEREXAMPLE FAMILY. Read the handle's "
                      "carried-out count BEFORE issuing anything and use it to choose "
                      "between surrendering the identifier early and surrendering it "
                      "late. Both arms do the reference work on the carried-out "
                      "outcome, so while the refused outcome left the identifier free "
                      "this VERIFIED and its faithful patch did not resolve: the branch "
                      "holds no such counter, so learning it costs a real query before "
                      "the removal and the exact-statement-count assertion fails.",
        "rationale": "rejected once the identifier is pinned on the refused path: the "
                     "early-clearing arm gives 'Assertion (instance.pk is "
                     "Old(instance.pk)) might not hold.' The free read no longer buys "
                     "the rival anything, because the difference it was branching onto "
                     "is no longer a difference the spec permits.",
    },
    {
        "id": "uniq-freeread-clear-order-ledger",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FREEREAD_CLEAR_ORDER_LEDGER),
        "refinement": "the same defect through the module-wide total instead of the "
                      "handle's own carried-out count — the second shape the recorded "
                      "counterexample took. Registered separately so the family is "
                      "covered through every readable part of the record.",
        "rationale": "rejected for the same reason: 'Assertion (instance.pk is "
                     "Old(instance.pk)) might not hold' in the early-clearing arm.",
    },
    {
        "id": "uniq-clear-early-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_CLEAR_EARLY_PARTIAL),
        "refinement": "the PARTIAL-DOMAIN form: keep the faithful order on most of the "
                      "domain and surrender the identifier early only for small "
                      "identifiers. A clause that pinned the identifier for only part "
                      "of the domain would admit it.",
        "rationale": "rejected because the exceptional clause covers the WHOLE "
                     "precondition domain: 'Assertion (instance.pk is Old(instance.pk)) "
                     "might not hold.'",
    },
]


# ===========================================================================
# AXIOM LANE — one A-consumed axiom: remove_rows(db, identifier: int) -> int,
# effectful over the Database carrier, modelling the UNCHANGED callee
# django.db.models.sql.subqueries.DeleteQuery.delete_batch. Its Ensures are the
# cost (one statement per invocation), the target (that statement removes by the
# identifier it was handed), and the report (the value returned is that
# statement's own non-negative rowcount). There is deliberately no @Pure twin of
# this callee. Probes run in the instance Docker image (the real Django lives
# there). We embed the bundle's own axiom_check.py soundness logic for the
# soundness probe (the runner mounts ONLY the probe at /work, so we cannot import
# axiom_check.py in-container — but its logic imports only Django, which IS
# present).
# ===========================================================================

# axiom-soundness: execute the REAL DeleteQuery.delete_batch on a configured
# in-memory sqlite DB over live single rows (count must be 1, >= 0) and absent
# identifiers (count must be 0, >= 0), OBSERVING through the connection's
# execute_wrapper that each invocation issues exactly ONE row-removal statement
# and that the statement's real bind parameters carry the identifier it was
# handed, and assert the primitive NEVER clears the in-memory object's pk (the
# refinement-load-bearing property — only the patch's setattr does). Any negative
# count, non-int, statement count other than one, mismatched removal target, or
# in-memory pk mutation => AXIOM-UNSOUND. The two clauses about the outcome the
# STORE forces are measured on the same real callee: a still-fast-deletable row a
# live foreign key protects is answered with NO count (and the row survives, and
# the refused invocation still issued exactly one statement carrying the
# identifier it was handed), the same identifier unprotected IS answered with a
# count, and a dependent row behind a constraint-free reference does not refuse —
# so both directions of the outcome the two halves of clause (6) are stated on —
# a count means the store applied the removal, no count means it applied nothing —
# are measured on the real callee, not an escape hatch. The axiom is
# flag-independent
# (delete_batch's return is the DB-reported rowcount regardless of backend);
# exercised on the default sqlite3 backend the harness uses.
_AX_SOUNDNESS_PROBE = r'''
import os, sys

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        # NOTE: register ONLY apps that are actually importable. A throwaway
        # `app_label` (e.g. "axcheck") must NOT appear in INSTALLED_APPS — Django
        # 3.0's django.setup() eagerly imports every INSTALLED_APPS entry and
        # raises ModuleNotFoundError for a non-existent package, so the probe
        # would never reach the real callee. We host the throwaway model under an
        # already-installed app's label ("auth") instead.
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        print("AXIOM-SOUNDNESS FAIL: Django not configurable: %r" % (exc,))
        return 1

    from django.db import connection, connections, models
    from django.db.models import sql
    from django.db.models.deletion import Collector

    class FastDeletable(models.Model):
        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(FastDeletable)

    def _observed_target(params):
        # the identifier the real statement was parameterized with (one-element
        # pk list -> one bind parameter); None if not observable here.
        if params is None:
            return None
        try:
            seq = list(params)
        except TypeError:
            return None
        return seq[0] if len(seq) == 1 else None

    def remove_rows_outcome(identifier):
        # ONE invocation of the real primitive, with the statements it issues and
        # their bind parameters OBSERVED rather than assumed, and reporting HOW it
        # ended: ("returned", count, statements, target) / ("raised", exc,
        # statements, target). The execute_wrapper sees a statement as it is
        # issued, i.e. BEFORE the store accepts or refuses it — which is what
        # makes the cost/target halves of the exceptional clause measurable.
        issued = []

        def _tally(execute, sql_text, params, many, context):
            issued.append((sql_text, params))
            return execute(sql_text, params, many, context)

        try:
            with connections["default"].execute_wrapper(_tally):
                count = sql.DeleteQuery(FastDeletable).delete_batch([identifier],
                                                                   "default")
        except Exception as exc:
            target = _observed_target(issued[-1][1]) if issued else None
            return ("raised", exc, len(issued), target)
        target = _observed_target(issued[-1][1]) if issued else None
        return ("returned", count, len(issued), target)

    def remove_rows(identifier):
        outcome = remove_rows_outcome(identifier)
        if outcome[0] == "raised":
            raise outcome[1]
        return outcome[1], outcome[2], outcome[3]

    counts_seen = []
    targets_observed = []

    def check_axiom(identifier, count, statements, target, expect_count):
        assert isinstance(count, int), "delete_batch returned non-int %r" % (count,)
        assert count >= 0, "AXIOM-UNSOUND: negative count %r" % (count,)
        assert count == expect_count, (
            "delete_batch removed %r rows, expected %r" % (count, expect_count))
        assert statements == 1, (
            "AXIOM-UNSOUND: one invocation issued %r row-removal statement(s), "
            "but the axiom claims exactly 1" % (statements,))
        if target is not None:
            assert target == identifier, (
                "AXIOM-UNSOUND: the real statement removed by %r, but was handed "
                "identifier %r" % (target, identifier))
            targets_observed.append(1)

    # (a) live single rows: delete_batch reports exactly 1 (>= 0) via exactly one
    #     statement targeting the given identifier, and must NOT clear the
    #     in-memory pk.
    for _ in range(50):
        obj = FastDeletable.objects.create()
        stored_pk = obj.pk
        assert stored_pk is not None, "freshly created object has no pk"

        collector = Collector(using="default")
        assert collector.can_fast_delete(obj), "expected a fast-deletable object"

        count, statements, target = remove_rows(stored_pk)
        check_axiom(stored_pk, count, statements, target, 1)
        # refinement-load-bearing: the primitive never touches the in-memory pk
        assert obj.pk == stored_pk, (
            "AXIOM-UNSOUND: delete_batch mutated the in-memory pk: was %r now %r"
            % (stored_pk, obj.pk))
        counts_seen.append(count)

    # (b) absent identifiers (raise/sentinel boundary): count must be 0 (>= 0),
    #     still one statement, still targeting the given identifier.
    for _ in range(25):
        obj = FastDeletable.objects.create()
        stored_pk = obj.pk
        remove_rows(stored_pk)
        count, statements, target = remove_rows(stored_pk)
        check_axiom(stored_pk, count, statements, target, 0)
        counts_seen.append(count)

    # (c) THE REFUSAL — both directions of the outcome the two halves of clause
    #     (6) are stated on (a reported count means the store CARRIED the removal
    #     OUT; a refusal means it carried nothing out), plus the cost and target the
    #     exceptional clause claims for the refused statement. Measured on the
    #     MODELED path: the protected row is still fast-deletable, so this is an
    #     input remove_single_independent genuinely reaches.
    class Protector(models.Model):
        # a row whose FK the store keys to a FastDeletable row; with DO_NOTHING
        # Django asks the database for nothing, so the database's own FOREIGN KEY
        # constraint is what refuses the removal.
        target = models.ForeignKey(FastDeletable, models.DO_NOTHING)

        class Meta:
            app_label = "auth"

    class LooseProtector(models.Model):
        # the same reference with NO database constraint behind it: a dependent
        # row exists, but the store holds nothing protecting the target.
        target = models.ForeignKey(FastDeletable, models.DO_NOTHING,
                                   db_constraint=False)

        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(Protector)
        editor.create_model(LooseProtector)
    with connection.cursor() as cur:
        cur.execute("PRAGMA foreign_keys")
        fk_row = cur.fetchone()
    fk_enforced = bool(fk_row and fk_row[0])
    refusals_observed = 0
    if fk_enforced:
        from django.db.utils import IntegrityError
        # (c.1) the store REFUSES: no count at all, the row survives, the
        #       in-memory pk is untouched — and the refusal was still the answer
        #       to exactly ONE statement carrying the identifier handed in.
        protected = FastDeletable.objects.create()
        Protector.objects.create(target=protected)
        collector = Collector(using="default")
        assert collector.can_fast_delete(protected), (
            "expected the protected row to still be fast-deletable: the refusal "
            "must be reachable on the path under specification")
        outcome = remove_rows_outcome(protected.pk)
        assert outcome[0] == "raised", (
            "AXIOM-UNSOUND: the primitive RETURNED %r for the identifier of a row "
            "the store protects; model.py claims a count only for a removal the "
            "store carried out" % (outcome[1:],))
        refusal, refused_statements, refused_target = outcome[1:]
        assert isinstance(refusal, IntegrityError), (
            "the refusal reached the caller as %r, not the IntegrityError "
            "RemovalRefused stands for" % (refusal,))
        assert FastDeletable.objects.filter(pk=protected.pk).exists(), (
            "the refused removal removed the row anyway")
        assert protected.pk is not None, (
            "the refused removal cleared the in-memory pk")
        assert refused_statements == 1, (
            "AXIOM-UNSOUND: the refused invocation issued %r row-removal "
            "statement(s); model.py's Exsures claims the tally and the total each "
            "still advance by exactly 1 on that path" % (refused_statements,))
        if refused_target is not None:
            assert refused_target == protected.pk, (
                "AXIOM-UNSOUND: the refused statement carried identifier %r "
                "though the primitive was handed %r" % (refused_target,
                                                        protected.pk))
        refusals_observed += 1
        # (c.2) the other direction: with the protecting row gone the SAME
        #       identifier is answered with a count, so the refusal is conditioned
        #       on what the store holds and is not something the primitive may
        #       always do.
        Protector.objects.all().delete()
        outcome = remove_rows_outcome(protected.pk)
        assert outcome[0] == "returned", (
            "AXIOM-UNSOUND: no count for the now-unprotected identifier (%r) — "
            "the refusal would then not be conditioned on the store refusing"
            % (outcome[1:],))
        check_axiom(protected.pk, outcome[1], outcome[2], outcome[3], 1)
        counts_seen.append(outcome[1])
        # (c.3) what the carrier means: a dependent row ALONE does not refuse —
        #       only something the store holds protecting the target does.
        loose = FastDeletable.objects.create()
        LooseProtector.objects.create(target=loose)
        outcome = remove_rows_outcome(loose.pk)
        assert outcome[0] == "returned", (
            "no count for a row referenced through a constraint-free FK (%r); "
            "the refusal is then not the store's own refusal"
            % (outcome[1:],))
        check_axiom(loose.pk, outcome[1], outcome[2], outcome[3], 1)
        counts_seen.append(outcome[1])
        LooseProtector.objects.all().delete()

    # (d) DOMAIN BOUNDARY. The axiom's Requires is
    #     -(2 ** 63) <= identifier < 2 ** 63, so the boundary identifiers must be
    #     exercised INSIDE it (the axiom must hold there) and the first values
    #     OUTSIDE it must be confirmed to be genuinely outside the callee's
    #     domain -- i.e. the axiom is not merely unchecked there but would be
    #     UNSOUND if its Requires had been left wider.
    for edge in (2 ** 63 - 1, -(2 ** 63), 0, -1, 2 ** 62):
        assert -(2 ** 63) <= edge < 2 ** 63, "test bug: %r not in domain" % (edge,)
        count, statements, target = remove_rows(edge)
        check_axiom(edge, count, statements, target, 0)
        counts_seen.append(count)

    for outside in (2 ** 63, -(2 ** 63) - 1, 2 ** 64, 2 ** 100):
        assert not (-(2 ** 63) <= outside < 2 ** 63), "test bug"
        try:
            sql.DeleteQuery(FastDeletable).delete_batch([outside], "default")
        except Exception:
            pass  # outside the domain: the axiom deliberately claims nothing
        else:
            print("AXIOM DOMAIN TOO NARROW: delete_batch returned normally for "
                  "identifier %r, which the axiom's Requires excludes. The "
                  "Requires should be widened to cover it." % (outside,))
            return 1

    if not targets_observed:
        print("AXIOM-SOUNDNESS SKIP: the real statement's bind parameters were "
              "never observable on this backend, so the removal-target clause "
              "could not be checked executably.")
        return 0

    print("AXIOM-SOUNDNESS OK: the remove_rows axiom holds for the real "
          "DeleteQuery.delete_batch over %d observations: exactly ONE row-removal "
          "statement per invocation, that statement removed by the identifier it "
          "was handed (%d observations with observable bind parameters), and the "
          "returned value was its own non-negative report (counts in {0,1}); the "
          "primitive never clears the in-memory pk. The refusal clauses are "
          "measured too (%d observation(s), foreign keys enforced=%r): a still-"
          "fast-deletable row the store protects is answered with NO count and "
          "survives, that refused invocation still issued exactly ONE statement "
          "carrying the identifier it was handed, the same identifier unprotected "
          "is answered with a count, and a dependent row behind a constraint-free "
          "reference does not refuse."
          % (len(counts_seen), len(targets_observed), refusals_observed,
             fk_enforced))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# axiom-containment: the model can only ever pass `identifier = instance.pk` to
# remove_rows, and the precondition guarantees instance.pk is a non-None
# stored pk (an int). The axiom's Requires domain is `identifier: int` plus read
# access to the handle's removal record (no further constraint on the
# identifier), so EVERY caller-reachable identifier (a stored int pk)
# lies inside the axiom domain — containment holds trivially. We confirm
# operationally that the identifiers the model produces (the real stored pks of
# fast-deletable objects) are exactly the int identifiers the real callee
# accepts and reports a non-negative count for; i.e. the caller never reaches an
# input outside the axiom's domain. (Covering more — e.g. any int, including
# absent ids — is SOUND, not a defect; the model reaches only a subset.)
_AX_CONTAINMENT_PROBE = r'''
import os, sys

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        # NOTE: register ONLY importable apps (see _AX_SOUNDNESS_PROBE). A bare
        # `app_label` like "axcheck" in INSTALLED_APPS makes django.setup() raise
        # ModuleNotFoundError before the real callee runs; host the throwaway
        # model under the already-installed "auth" app instead.
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        print("AXIOM-CONTAINMENT FAIL: Django not configurable: %r" % (exc,))
        return 1

    from django.db import connection, models
    from django.db.models import sql

    class FastDeletable(models.Model):
        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(FastDeletable)

    # The model passes `identifier = instance.pk` under the precondition
    # `instance.pk is not None`, i.e. a stored int pk. Enumerate the identifiers
    # the model can actually reach (real stored pks of fast-deletable objects)
    # and confirm each is an int the callee accepts within the axiom domain.
    reached = []
    for _ in range(50):
        obj = FastDeletable.objects.create()
        stored_pk = obj.pk
        # model-reachable identifier: a non-None stored pk
        assert stored_pk is not None, "precondition guarantees a stored pk"
        assert isinstance(stored_pk, int), (
            "AXIOM-TOO-WEAK-FOR-CALLER: model-reachable identifier %r is not the "
            "int the axiom domain constrains" % (stored_pk,))
        assert -(2 ** 63) <= stored_pk < 2 ** 63, (
            "AXIOM-TOO-WEAK-FOR-CALLER: model-reachable identifier %r is outside "
            "the axiom's representable-identifier Requires domain" % (stored_pk,))
        # the axiom domain is the representable range; this reachable identifier
        # is in it. Confirm the callee accepts it and reports a non-negative count.
        count = sql.DeleteQuery(FastDeletable).delete_batch([stored_pk], "default")
        assert isinstance(count, int) and count >= 0, (
            "real callee on a model-reachable identifier returned %r" % (count,))
        reached.append(stored_pk)

    print("AXIOM-CONTAINMENT OK: every model-reachable identifier (a non-None "
          "stored int pk; %d sampled) lies inside remove_rows' int "
          "Requires domain and is accepted by the real DeleteQuery.delete_batch "
          "(non-negative count). The caller reaches a subset of the axiom domain; "
          "no reachable input is outside it." % (len(reached),))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-remove_rows",
        "axiom": "remove_rows",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # callee is UNCHANGED by the patch; apply_gold is harmless
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "if the real DeleteQuery.delete_batch ever returns a negative / "
                     "non-int count, issues a number of row-removal statements other "
                     "than one for a one-element identifier list, removes by an "
                     "identifier other than the one it was handed, or clears the "
                     "in-memory pk itself, one of the axiom's Ensures (cost, target, "
                     "report >= 0) or the refinement's no-pk-mutation claim is "
                     "violated => AXIOM-UNSOUND. Live rows (count 1) and absent "
                     "identifiers (count 0) cover the boundary; the statement count "
                     "and the statement's bind parameters are OBSERVED through the "
                     "connection's execute_wrapper, not assumed.",
    },
    {
        "id": "ax-cover-remove_rows",
        "axiom": "remove_rows",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "every identifier the model can pass to remove_rows is a "
                     "non-None stored int pk inside the representable identifier "
                     "range (preconditions instance.pk is not None and "
                     "-(2 ** 63) <= instance.pk < 2 ** 63); the axiom's Requires "
                     "domain is exactly that range (plus read access to the "
                     "handle's removal record, which the caller's own precondition "
                     "supplies), so each reachable identifier is inside it. The two "
                     "ranges coincide, which is what makes the axiom claim nothing "
                     "on identifiers the store cannot represent while still covering "
                     "every identifier the caller can reach. A reachable identifier "
                     "outside the domain would be AXIOM-TOO-WEAK-FOR-CALLER; the "
                     "probe confirms each sampled stored pk is inside the range and "
                     "that the real callee returns a count for it.",
    },
]
