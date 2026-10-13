"""Twin-artifact model for django__django-13297.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A mapping entry may be built so that the entry's value is not produced up
  front but computed later, on demand, by a deferred computation the entry
  carries. Running that deferred computation is NOT a silent read: it also
  raises a user-visible advisory notice about the entry, and the caller's
  configuration may escalate that notice into an error. Building such an entry
  must therefore satisfy THREE obligations at once:

    (1) RESOLUTION SOURCE, in two halves. (1a) PROVENANCE, on every value: the
        deferred computation the entry carries must be the one captured for THAT
        value. An entry built around some OTHER value never discharges this, at
        any value, so the operation may never substitute a stand-in for
        something else it happens to have to hand. (1b) ROUND-TRIP, off the
        value family named under PARTIALITY: running the entry's deferred
        computation yields exactly the original value — resolution does not
        alter it. The two halves are separate because on that family the entry is
        still built from THIS value's deferred computation, while what running
        that computation hands back need not be the value itself. Facet (1) in
        either half does NOT make the entry usable by a type-directed binder —
        an entry can faithfully resolve to the value and still be unbindable.

    (2) BINDER-USABILITY, in two halves. (2a) RECOGNITION, on every value: a
        type-directed parameter binder, presented the entry, must RECOGNISE it as
        something to resolve. The entry must therefore expose the resolution hook
        such a binder uses; a deferred stand-in that lacks that hook is rejected
        out of hand by the binder ("unsupported type") even though it would
        resolve to the same value through other access paths. (2b) RESOLUTION,
        off the value family named under PARTIALITY: the binder's resolution of
        the entry must yield the original value at its own real type. The two are
        separate because exposing the hook is what the binder checks, while what
        resolution then produces carries no guarantee on that family — see
        PARTIALITY.

    (3) DEFERRAL PRESERVED: building the entry must leave the deferred
        computation UNRUN. The whole purpose of deferring is that the advisory
        notice is raised at the moment a consumer actually reaches for the
        value, attributed to that access — not while the mapping is being
        assembled, where no consumer has asked for anything and where an
        escalating configuration would turn the notice into an error that
        aborts the assembly before any entry exists. So the build step must
        run NO entry's deferred computation, not the one it is building and
        not any other: the count of deferred computations run must be exactly
        what it was on entry. An entry that is built binder-resolvable but is
        also resolved on the spot is not a deferred entry at all.

        Obligation (3) is a claim about an EFFECT, so it is only meaningful if
        the model admits no free route to a deferred entry's value. There is
        none: what an entry resolves to is recorded ONLY as an abstract
        capability that no operation can inspect, read, evaluate or take apart.
        The single operation that yields the value charges the ledger for doing
        so. An implementation therefore cannot learn the value — not to test
        it, not to branch on it, not to rebuild from it — without the ledger
        recording that a deferred computation was run.

  (2) is the guarantee that makes the entry usable downstream; (3) is the
  guarantee that it is still deferred. Both are needed: an entry that fails
  (2) cannot be bound, and an entry built in violation of (3) discloses its
  notice at assembly time instead of at the consumer's access (and, under an
  escalating configuration, never gets built at all). Together with (1) they
  make the entry a faithful, transparent, still-deferred stand-in for the value
  in every downstream position, INCLUDING a type-directed parameter-binding one.

  PARTIALITY. A construction that exposes the binder's hook need not be able to
  produce a resolving entry for every value: there is a family of values on which
  it has no resolution guarantee to give. This specification names that family
  ONLY abstractly, as ``own_type_unpreparable``, and says nothing whatever about
  which values are in it: membership is settled out of band (mapping.md /
  axiom_check.py), it is uninterpreted here, and no encoding of or arithmetic on
  a value-tag can decide it, so a proof can only use it as an opaque case split.

  On that family the contract states the two outcomes the operation is permitted
  to have, and permits BOTH: it may ABORT with an exception instead of returning
  an entry, and it may instead return an entry that the binder RECOGNISES and
  then cannot resolve to the value. Two things it may never do there: hand back a
  stand-in the binder refuses outright, and hand back an entry built around some
  other value. Off the family it must return normally with the full guarantees
  above.

  Aborting is PERMITTED, never REQUIRED — a construction with no such family at
  all would return normally, and resolve faithfully, for every value, and is
  equally admissible. Obligation (3) holds on the aborting exit too: an abort
  reports that no entry could be built, and it is not a licence to have run a
  deferred computation on the way out.

Modelling choices (Nagini fragment):
  * A value is modelled as an integer value-tag; its real runtime type is the
    deep, definite function ``type_of`` over that tag (the model of the value's
    own runtime type; mapping.md §2/§3).
  * The deferred entry is modelled as a minimal class ``Wrapped``. It carries NO
    readable field, and there is NO function from an entry to the value it
    resolves to. WHICH value's deferred computation an entry carries is recorded
    by the abstract, unforgeable capability ``deferral_of(w, value)``, and what
    running that computation yields is recorded by the abstract, unforgeable
    capability ``resolves_to(w, value)`` (both ``@ContractOnly @Predicate``s with
    no body). This is what makes obligation (3) expressible at
    all, and it is stronger than a projection: a readable field, and equally a
    ``@Pure`` projection over the entry, can be EVALUATED by an implementation,
    which makes the value available for free and silently — so running the
    deferred computation early and not running it would be indistinguishable.
    A bodiless predicate can be held, passed and handed back, but never
    evaluated, unfolded or inspected: it cannot be turned into the value. The
    ONLY operation that yields the value is ``run_deferral`` below, and it
    charges the ledger.
  * The effect of running a deferred computation — one advisory notice raised —
    is carried by the abstract ledger ``deferrals_run(n)``: an unforgeable
    ``@ContractOnly @Predicate`` (no body) meaning "exactly ``n`` deferred
    computations have been run so far". Running one deferred computation
    consumes ``deferrals_run(n)`` and yields ``deferrals_run(n + 1)``, and there
    is no way back: the predicate has no body to ``Fold``, so a count once
    advanced cannot be restored, and the ledger cannot be reset or fabricated.
    It is not indexed by an entry either, so running the deferred computation of
    ANY entry — the one being handed on or a throwaway built on the side — is
    charged to the one ledger the contract constrains. Requiring the build step
    to hand back the ledger at its ENTRY count is therefore a genuine
    no-deferral-run obligation on every path, not a stylistic one.
  * Binder-usability is likewise NOT a stored field an implementation can set.
    Its whole-domain half is the abstract, unforgeable capability
    ``binder_accepts(w)`` (a ``@ContractOnly @Predicate`` with no body) recording
    that a type-directed binder recognises THIS entry rather than refusing it as
    an unsupported type; the hook-exposing construction grants it on every entry
    it returns, and the hookless one never grants it. Its per-value half is an
    abstract, unforgeable capability
    ``binder_castable(w, cast_to, cast_t)`` (a ``@ContractOnly @Predicate`` with
    no body) recording, for THIS entry, that a type-directed binder can resolve
    it and the value/real-type that resolution yields. Its SOLE producer is the
    deferred-entry construction that builds a binder-resolvable entry
    (``wrap_resolvable`` below); a construction that produces a non-resolvable
    deferred stand-in does NOT grant it (``wrap_opaque`` below). An
    implementation cannot ``Fold`` it into existence (abstract, no body), and it
    names the specific entry, so a capability for some other entry does not
    discharge it (directive-8 capability grounding — the binder-resolvability
    fact is tied to the effect-producing construction step, not to a copyable
    field or an answer-key oracle on the result value).
  * ``own_type_unpreparable(value)`` is the deep, abstract model of the value
    family on which the hook-exposing construction carries no per-value
    resolution guarantee — neither that running the entry's deferred computation
    yields the value (facet 1b) nor that a binder can resolve the entry to it
    (facet 2b). It is a bare abstract marker: this specification asserts nothing
    at all about which values it holds of, it is uninterpreted so no arithmetic
    on the value-tag can decide it, and a proof can only use it as an opaque case
    split and cannot smuggle in a domain restriction by another name. It is in
    particular NOT a synonym for any property a reader could compute from the
    value here. The partition it names is settled out of band (mapping.md
    §2/§3) and checked against reality by axiom_check.py.
  * The per-entry construction is the only changed operation; the surrounding
    rebuild of the mapping (iterate the entries, carry each key through, store
    the built entry) is unchanged control flow and is the same before and after
    (refinement.md). The single contracted function models that one per-value
    construction operation, and the ledger it must preserve is the mapping-wide
    count of deferred computations run while the rebuild is in progress.

The value is an immutable integer (no permission carrier); the entry is freshly
allocated and returned. No string indexing is used (Nagini bans it). Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Wrapped:
    """A deferred entry for a single value. It carries NO readable field, and no
    function maps it to the value it resolves to: that fact is held only as the
    abstract capability ``resolves_to``, which cannot be evaluated. Obtaining the
    value at runtime requires RUNNING the deferred computation (an effectful
    step that charges the ledger, see ``run_deferral``)."""

    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(True)
        pass


# axioms-start
@Pure
def type_of(value: int) -> int:
    """The real runtime type of a value (the model of the value's own runtime
    type): a deep, definite, value-dependent type-tag. Distinct values may share
    a type-tag (same-typed values), distinct types map to distinct tags.
    Validated == the value's real runtime type out-of-band (axiom_check.py)."""
    if value < 0:
        return 0
    return value + 1


# Deep model (A-reference) of the value family on which the hook-exposing
# construction carries no per-value resolution guarantee: neither that running the
# entry's deferred computation yields the value (facet 1b) nor that a binder can
# resolve the entry to it (facet 2b). Two outcomes are permitted on it and the
# contract states both — the construction may produce no entry at all and abort,
# or it may produce an entry a binder RECOGNISES and then cannot resolve to the
# value — so membership does NOT coincide with "no entry is produced".
# This specification asserts NOTHING about which values are in the family.
# Abstract and UNINTERPRETED on purpose: no encoding of, or arithmetic on, the
# value-tag can decide it, so a proof can only use it as an opaque case split and
# cannot smuggle in a domain restriction by another name; in particular it is not
# a synonym for any property a reader could compute from the value here. The
# partition is settled out of band and validated == reality over the whole family
# (mapping.md / axiom_check.py).
@Pure
@ContractOnly
def own_type_unpreparable(value: int) -> bool:
    pass


# Abstract, unforgeable capability recording WHAT a deferred entry resolves to:
# holding `resolves_to(w, value)` means that running `w`'s deferred computation
# yields exactly `value`. It is the ROUND-TRIP half of facet (1) and is therefore
# granted only OFF the `own_type_unpreparable` family by the hook-exposing
# construction (on that family, running the entry's deferred computation carries
# no guarantee of handing the value back); the PROVENANCE half, which holds on
# every value, is `deferral_of` below.
# It is an opaque predicate with NO body, and — the point
# — there is deliberately no function from an entry to its value anywhere in this
# specification. Consequences:
#   - it can be held, threaded through and handed back, but it cannot be
#     EVALUATED: an implementation cannot turn it into the value, cannot test the
#     value against anything, and cannot branch on it;
#   - it has no body to Unfold, so the value cannot be extracted from it (an
#     attempt is rejected outright, not merely unprovable);
#   - it is therefore NOT a readable field and NOT a pure projection in
#     disguise. Both of those are free and silent, whereas in the modelled
#     reality the value is reachable only by running the deferred computation,
#     which raises the advisory notice. Making the resolution fact an
#     inert capability is what closes the free-read side channel and leaves
#     `run_deferral` as the ONLY route from an entry to its value.
# It is granted by BOTH constructions — unconditionally by the hookless one,
# which has no such family, and off the `own_type_unpreparable` family by the
# hook-exposing one: it is the SHARED faithfulness fact (facet 1b), never a
# discriminator. Provenance + executable soundness check:
# mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def resolves_to(w: 'Wrapped', value: int) -> bool:
    pass


# Abstract, unforgeable capability recording WHICH value's deferred computation a
# deferred entry carries: holding `deferral_of(w, value)` means the computation
# `w` defers is the one captured for `value`, so whatever running it hands back is
# determined by `value` and by nothing else. It is an opaque predicate with NO
# body, with the same consequences as `resolves_to`: it can be held, threaded
# through and handed back, but never EVALUATED, so it is not a second, free,
# silent route from an entry to its value and it cannot be Folded into existence.
# It names the specific entry AND the specific value, so a capability obtained for
# a different value does not discharge a required `deferral_of(w, value)`.
#   - This is the WHOLE-DOMAIN half of facet (1), and it is granted
#     unconditionally by BOTH constructions, so like `resolves_to` it is a SHARED
#     faithfulness fact and never a discriminator between them.
#   - Keeping it apart from `resolves_to` is what lets the contract stay honest on
#     the `own_type_unpreparable` family without going silent there: an entry
#     built for such a value still carries THAT value's deferred computation, so
#     an implementation may NOT hand back an entry built around some other value
#     on that family and call it equivalent, even though no round-trip is
#     promised there.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def deferral_of(w: 'Wrapped', value: int) -> bool:
    pass


# Abstract, unforgeable capability marking a deferred entry that a type-directed
# parameter binder CAN RESOLVE: holding `binder_castable(w, cast_to, cast_t)`
# means that, presented `w`, the binder resolves it to a concrete value `cast_to`
# whose real runtime type is `cast_t`, and so binds it successfully. It is an
# opaque predicate with NO body. Consequences:
#   - an implementation cannot Fold it into existence (no body to fold), so
#     binder-resolvability cannot be fabricated by fiat;
#   - it names the specific entry `w` together with the resolved value and its
#     real type, so a capability obtained for a different entry / value / type
#     does NOT discharge a required `binder_castable(w, value, type_of(value))`
#     — it cannot be laundered across entries or across value-equal copies.
# Its SOLE producer is the binder-resolvable construction `wrap_resolvable`,
# which grants it, off the `own_type_unpreparable` family, on the entry it built,
# for the value it wrapped and that value's real type. The non-resolvable
# construction `wrap_opaque` does NOT
# grant it. This is the directive-8 / control-flow grounding of the
# binder-resolvability fact: an unforgeable capability tied to the effect-
# producing construction step, not an answer-key oracle on a result value and
# not a copyable field. Provenance + executable soundness check: mapping.md /
# axiom_check.py.
@ContractOnly
@Predicate
def binder_castable(w: 'Wrapped', cast_to: int, cast_t: int) -> bool:
    pass


# Abstract, unforgeable capability marking a deferred entry that a type-directed
# parameter binder RECOGNISES as one it must resolve, rather than rejecting out of
# hand as an unsupported type: holding `binder_accepts(w)` means the binder, shown
# `w`, takes the resolution route instead of refusing the entry. It is an opaque
# predicate with NO body, so it cannot be Folded into existence, and it names the
# specific entry.
#   - This is the WHOLE-DOMAIN half of downstream usability. The deferred-entry
#     construction that exposes the binder's resolution hook grants it for EVERY
#     value it returns an entry for — including a value in the
#     `own_type_unpreparable` family for which it returns an entry that cannot be
#     resolved to the value, where the binder still recognises and attempts the
#     entry. The construction that produces a
#     stand-in without that hook NEVER grants it, at any value: such a stand-in is
#     refused by the binder as an unsupported type.
#   - `binder_castable` below is the stronger, per-value half: recognised AND
#     resolution actually yields the original value at its real type. Keeping the
#     two apart is what lets the contract stay honest on the
#     `own_type_unpreparable` family without going silent there: an entry built
#     for such a value is still recognised by the binder, so an implementation may
#     NOT hand back an unrecognised stand-in on that family and call it
#     equivalent.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def binder_accepts(w: 'Wrapped') -> bool:
    pass


# Abstract, unforgeable LEDGER of the effect that running a deferred computation
# has: `deferrals_run(n)` means exactly `n` deferred computations have been run
# so far, i.e. `n` advisory notices have been raised. It is an opaque predicate
# with NO body. Consequences:
#   - running one deferred computation consumes `deferrals_run(n)` and yields
#     `deferrals_run(n + 1)` (`run_deferral` below), so the count is monotone;
#   - there is no body to Fold, so a count once advanced cannot be restored and
#     the ledger can neither be reset nor fabricated: an operation that has run
#     a deferred computation cannot hand the ledger back at its entry count;
#   - it is NOT indexed by an entry, so running the deferred computation of ANY
#     entry — the one handed on, or a throwaway built on the side — is charged
#     to the same ledger.
# It is therefore the carrier for obligation (3): "this operation ran no
# deferred computation" is expressed as "the ledger comes back at exactly the
# count it went in at". Provenance + executable soundness check: mapping.md /
# axiom_check.py.
@ContractOnly
@Predicate
def deferrals_run(n: int) -> bool:
    pass


@ContractOnly
def run_deferral(w: 'Wrapped', value: int, n: int) -> int:
    """Run a deferred entry's computation — the effectful step a consumer
    performs when it actually reaches for the value. It yields the value the
    entry resolves to AND raises one advisory notice about the entry, so it
    advances the ledger from `n` to `n + 1`. The ledger counts RUNS of a
    deferred computation, not accesses to an entry: every run raises its own
    notice, while an entry that has kept the value it already produced may
    serve it again without performing a further run. This is the ONLY
    operation in this specification that yields a deferred entry's value, and
    it is never free: the caller must present the resolution capability for the
    entry (which it keeps) and must pay one unit of ledger for the run.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(4))
    Requires(resolves_to(w, value))
    Requires(deferrals_run(n))
    Ensures(resolves_to(w, value))
    Ensures(deferrals_run(n + 1))
    Ensures(Result() == value)


@ContractOnly
def wrap_resolvable(value: int) -> Wrapped:
    """The deferred-entry construction that exposes the resolution hook a
    type-directed parameter binder uses. Every entry it returns (1a) carries the
    deferred computation captured for the value it was called on — it grants
    `deferral_of` on every entry it returns — and (2a) is RECOGNISED by such a
    binder — it grants `binder_accepts` on every entry it returns. OFF the
    `own_type_unpreparable` family it additionally (1b) resolves to the original
    value and (2b) is the SOLE producer of the `binder_castable` capability,
    granting it for the wrapped value and that value's own real runtime type, so
    the binder resolves the entry to the value at its real type. Constructing the
    entry does NOT run its deferred computation, so it touches no ledger.

    On the `own_type_unpreparable` family this construction gives NO per-value
    resolution guarantee at all: it is permitted to abort with an exception
    instead of returning, and it is permitted instead to return an entry that a
    binder recognises and then cannot resolve to the value. Either way the entry
    it returns is still recognised by a binder and still carries THAT value's
    deferred computation. OUTSIDE that family it always returns normally with the
    full guarantees above. Aborting is permitted, never required. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(6))
    Ensures(deferral_of(Result(), value))
    Ensures(binder_accepts(Result()))
    Ensures(Implies(not own_type_unpreparable(value),
                    resolves_to(Result(), value)))
    Ensures(Implies(not own_type_unpreparable(value),
                    binder_castable(Result(), value, type_of(value))))
    Exsures(Exception, own_type_unpreparable(value))


@ContractOnly
def wrap_opaque(value: int) -> Wrapped:
    """The deferred-entry construction that does NOT expose the resolution hook a
    type-directed parameter binder uses. It builds a fresh deferred entry that
    carries the deferred computation captured for the value and resolves to the
    original value, but a binder shown this entry REJECTS it out of hand as an
    unsupported type rather than resolving it: it grants neither `binder_accepts`
    nor `binder_castable`, at any value, even though the entry resolves to the
    same value through other access paths. Constructing it does NOT run its
    deferred computation either, so it touches no ledger. It has no
    `own_type_unpreparable` family of its own, so it is TOTAL and its resolution
    guarantee is UNCONDITIONAL — it returns an entry that resolves to the value
    for EVERY value, including every value in that family. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(6))
    Ensures(deferral_of(Result(), value))
    Ensures(resolves_to(Result(), value))
# axioms-end


# pure-start
# (no consumed pure helper beyond type_of, the deep model of the value's real
# runtime type, and own_type_unpreparable, the abstract marker of the value family
# on which the hook-exposing construction carries no per-value resolution
# guarantee; both live in the axioms region as A-references. There is deliberately
# NO pure helper from an entry to the value it resolves to: such a helper would be
# a free, silent read of the value and would make obligation (3) unenforceable.)
# pure-end


def wrap_kwarg_value(value: int) -> Wrapped:
    # pre-conditions-start
    # The value is an immutable integer value-tag: it carries no permission and
    # is never mutated (the construction only reads it to capture its facets).
    # The ledger of deferred computations run enters this operation at 0: no
    # deferred computation has been run yet at the point the entry is built.
    # The value domain is UNRESTRICTED — every value-tag is admissible,
    # including every value-tag in the `own_type_unpreparable` family on which
    # the hook-exposing construction carries no per-value resolution guarantee.
    Requires(MustTerminate(14))
    Requires(deferrals_run(0))
    # pre-conditions-end
    # post-conditions-start
    # (3) DEFERRAL PRESERVED (the preservation obligation): the ledger comes
    # back at exactly the count it went in at, so this operation ran NO deferred
    # computation — not the entry's own and not any other's. The advisory notice
    # is therefore still owed to whoever eventually reaches for the value, and
    # an escalating configuration cannot turn it into an error here, while the
    # mapping is being assembled. The ledger is abstract and monotone (no body
    # to Fold, no way back from n + 1 to n), so an operation that ran a deferred
    # computation on ANY path cannot discharge this. And because no operation
    # yields a deferred entry's value except the one that charges the ledger,
    # this cannot be satisfied while still having consulted the value: there is
    # no free read to hide behind.
    Ensures(deferrals_run(0))
    # (1a) RESOLUTION PROVENANCE (the whole-domain half of the shared
    # faithfulness clause): the entry carries the deferred computation captured
    # for THIS value, so whatever running it hands back is determined by this
    # value and nothing else. Unconditional, on the whole admissible domain,
    # BECAUSE the real operation never builds an entry around a value other than
    # the one it was given — not even on the family where it promises no
    # round-trip. It is what forbids substituting an entry built for some other
    # value, and the capability is abstract (no body to Fold) and names both the
    # entry and the value, so it cannot be laundered across values.
    Ensures(deferral_of(Result(), value))
    # (1b) RESOLUTION ROUND-TRIP (the per-value half of the shared faithfulness
    # clause): off the `own_type_unpreparable` family, running the entry's
    # deferred computation yields exactly the original value. This is guarded for
    # the same reason (2b) is: on that family the real operation may return an
    # entry whose deferred computation hands back a value DERIVED from this value
    # rather than the value itself, and it does so SILENTLY — no abort, and the
    # entry is still binder-recognised. A contract that promised the round-trip
    # there would predict an outcome the operation does not produce, and would
    # oblige an implementation to deliver a faithfully-resolving entry where the
    # real operation delivers a derived one. Off the family the clause is
    # unconditional. NOT the discriminator either way — a non-resolvable entry
    # also resolves to the value, and does so on the whole domain.
    Ensures(Implies(not own_type_unpreparable(value),
                    resolves_to(Result(), value)))
    # (2a) BINDER RECOGNITION (the whole-domain half of downstream usability): a
    # type-directed parameter binder, shown the entry, RECOGNISES it as one to
    # resolve rather than refusing it as an unsupported type. This holds for EVERY
    # admissible value — there is no value family on which handing back a stand-in
    # the binder refuses is acceptable — and it is the unforgeable capability
    # granted only by the construction that exposes the binder's resolution hook.
    # A stand-in without that hook cannot discharge it, because the capability is
    # abstract (no body to Fold) and tied to this entry.
    Ensures(binder_accepts(Result()))
    # (2b) BINDER RESOLUTION (the per-value half): off the
    # `own_type_unpreparable` family, the binder resolves the entry to the
    # original value AT the value's OWN real runtime type. This is guarded because
    # the real operation genuinely gives no such guarantee on that family — there
    # the entry is still recognised (2a) but resolution may fail, or may hand back
    # a value derived from this one — and a contract that promised resolution
    # there would predict an outcome the operation does not produce. Outside that
    # family the clause is unconditional, so it remains the discriminator: on
    # every value off the family, an entry that merely resolves to the value
    # cannot discharge it.
    Ensures(Implies(not own_type_unpreparable(value),
                    binder_castable(Result(), value, type_of(value))))
    # PARTIALITY (propagated, permitted — never required): the operation may abort
    # with an exception instead of returning an entry, and ONLY for a value in the
    # `own_type_unpreparable` family — the abstract family on which the
    # hook-exposing construction carries no per-value resolution guarantee. The
    # marker is uninterpreted, so this clause licenses the abort on exactly that
    # family and on nothing a proof can compute for itself. Because aborting is
    # only permitted, a construction with no such family still satisfies this by
    # returning normally for every value.
    # Obligation (3) holds on this exit too: the ledger comes back at its entry
    # count on BOTH exits, so aborting is not a route by which a deferred
    # computation could have been run unobserved.
    Exsures(Exception, own_type_unpreparable(value))
    Exsures(Exception, deferrals_run(0))
    # post-conditions-end
    # impl-start
    # Pre-patch: the value is given the NON-resolvable deferred stand-in, which
    # resolves to the original value but does NOT expose the resolution hook a
    # type-directed parameter binder uses. It does not grant the
    # `binder_castable` capability, so this impl cannot discharge the
    # binder-resolvability postcondition (the binder rejects it as an unsupported
    # type) — exactly the spec sensing the change (G-DIFF).
    w = wrap_opaque(value)  # type: Wrapped
    return w
    # impl-end
