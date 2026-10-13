"""Twin-artifact model for django__django-13410.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A pair of advisory file-locking helpers wrap a low-level kernel locking
  primitive and report their outcome as a boolean.

  The primitive itself signals its result by control flow, NOT by a return
  value: when the requested operation is granted it completes normally and
  yields NO INFORMATIVE VALUE AT ALL — its result is THE EMPTY VALUE, the one
  value that carries no information; when the request cannot be granted — for
  instance a non-blocking acquisition of a lock that another holder already
  owns — it does not complete normally but signals the refusal out of band.

  THAT THE VALUE IS EMPTY IS ITSELF A LOAD-BEARING OBLIGATION, and it is stated
  as an obligation rather than left as a modelling detail because the whole
  reported outcome turns on it. The value a granted request hands back is not
  merely "some value that happens to differ from zero": it is the empty value,
  which supports NO informative interrogation whatever. It cannot be compared
  against a number, ordered against one, or combined with one arithmetically,
  and asking whether it is "set" or "unset" is not a question it answers — the
  only thing a caller can learn from it is that there was nothing to learn.
  Consequently the boolean a helper reports is NOT derivable from the value at
  all, and any body that tries to derive it from the value is reading an outcome
  out of something that does not carry one. The outcome lives ENTIRELY in the
  control flow: whether the request completed normally, or signalled out of band.
  A specification that instead let the value stand in for a definite number would
  license exactly the mistake this behaviour exists to rule out — a caller
  deciding "granted or refused" by inspecting a value that says nothing —
  because a definite number does answer the questions the empty value does not,
  and it answers them in whatever way that particular number happens to fall.

  SCOPE of the abstraction. The modelled datum distinguishes the two ways a
  request is ANSWERED — granted, or refused out of band — because those are the
  two outcomes the helper can translate into a boolean at all. A request the
  primitive leaves PENDING (a caller that asked to wait for a lock another
  holder keeps, so the primitive neither completes nor signals until the holder
  yields) is not one of the two answered outcomes and is outside what the
  boolean report can describe; the abstraction and the termination obligations
  below range over answered requests, in both of the two answered forms.

  An answered acquisition request is furthermore one the world SETTLES OUTRIGHT:
  it is decided at the moment it is made, with no rival request for the same lock
  still waiting to be decided behind it. A request decided while another party's
  claim on the same lock is still outstanding is not settled outright in this
  sense, and is neither of the two answered forms, so it is outside the
  abstraction. Every request a caller makes for a lock nobody else is contending
  for, and every request for an immediate answer decided against an
  already-settled world, is inside it.

  What a refusal does and does not leave alone is stated narrowly, and
  deliberately so. Being told "not available" leaves the caller's standing IN THE
  LOCK IT ASKED FOR exactly as it was — it did not get that lock, and it did not
  lose a claim on that same lock by asking. It is NOT a promise that nothing else
  whatever moved: a request that would have superseded some earlier, different
  claim of the caller's own may cost that earlier claim even when it is turned
  down, because the earlier claim can be given up before the new request is
  adjudicated. So the modelled non-event is scoped to the requested lock, which
  is the only standing the boolean report is about.

  The two operations are NOT symmetric in this respect, and the asymmetry is a
  real property of the primitive, not a modelling convenience. ACQUIRING a lock
  is a request another holder can keep pending indefinitely, so an acquisition
  delivers one of the two answers only when the request is in fact answered.
  RELEASING a lock the caller already holds is answered unconditionally: there
  is no one to wait for, so it always completes. Consequently the release
  helper's promise to report back is unconditional, while the acquisition
  helper's is a promise about answered requests. An implementation of the
  RELEASE helper that issues an ACQUISITION request has therefore taken on a
  step that can be left pending forever, and can no longer keep the
  unconditional promise the release helper makes — a caller that asks to drop a
  lock it holds must never be made to wait for a lock instead.

  HOW THAT ASYMMETRY IS MODELLED, and why it is a capability rather than a fact.
  The standing that an acquisition request has to be answered at all is not
  something a body can find out about the world; it is something a body must be
  GIVEN, and it is USED UP by the request it authorises. It is therefore modelled
  as an expendable capability, ``answerable_acquisition()``: an opaque resource
  with no body, which cannot be created, duplicated, re-derived, or arrived at by
  inspecting the world, and which the acquisition primitive TAKES AND DOES NOT
  RETURN. Three behavioural consequences follow, and each is a claim about what
  the helpers may do rather than about how they are written:

    * ONE ANSWERED ACQUISITION PER AUTHORISATION. A body holding one such
      capability may make exactly one acquisition request that the world is
      obliged to answer. It may not make a second, because the standing for the
      first is spent on the first. A helper that issues repeated acquisition
      requests for the same lock is claiming an entitlement it was never handed:
      the caller's request was for one lock, answered once.

    * THE RELEASE HELPER MAY NOT ACQUIRE. The release helper is handed no such
      capability, because a release of a lock the caller already holds needs
      none — it is answered unconditionally. A release body therefore has nothing
      with which to pay for an acquisition step, which is exactly the intended
      behavioural reading: dropping a lock the caller holds must not be carried
      out by first taking a lock, since that step may be left pending forever
      while the caller waits for a release that was always available. Because the
      capability is a resource and not a proposition, a body cannot obtain it by
      testing for it, asking whether it holds, or branching on it — there is
      nothing to test; either it was handed over or it was not.

    * THE ACQUISITION HELPER MAY ACQUIRE ONCE. That helper IS handed one,
      because its own promise to report back is scoped to answered requests in
      exactly the same way, and it spends it on the single acquisition whose
      outcome it reports.

  The behaviour pinned here is the faithful translation of that control-flow
  signal into the boolean the helpers promise, TOGETHER WITH the lock state
  each helper must leave behind when it returns:

    * The acquisition helper must report TRUE exactly when the primitive
      granted the acquisition (completed normally), and FALSE exactly when the
      primitive signalled that the lock was not available. A caller using the
      non-blocking mode relies on this boolean to learn whether it actually
      obtained the lock, so a normal completion must never be reported as
      failure.

    * A reported acquisition must still be in force AT THE MOMENT THE HELPER
      RETURNS. The boolean is a claim about the world the caller is handed, not
      a claim about something that merely happened at some point inside the
      helper: a caller told TRUE goes on to do protected work and then to
      release, so the lock must be held on exit. An implementation that takes
      the lock and then gives it up again before returning TRUE hands its
      caller a lock it does not have, and a competing non-blocking request
      would then be granted where it must be refused.

    * A reported failure must leave the REQUESTED lock's standing ALONE. A
      caller told FALSE learns only that it did not get the lock it asked for,
      and its standing in that lock is exactly what it was before it asked: a
      refusal does not hand the caller the lock it was refused, and it does not
      take away a claim on that same lock the caller already had. The report is
      about the requested lock and nothing wider; a caller told FALSE is not
      promised anything about a DIFFERENT lock it may separately hold, because a
      request that supersedes an earlier claim of the caller's own is not
      required to reinstate that earlier claim when it is turned down.

    * The release helper drops the caller's OWN claim on the lock; that release
      completes normally, so the helper must report TRUE, and THE CALLER must no
      longer hold the lock when the helper returns — a release that ends with the
      caller still (or again) holding it has not released it. What the helper
      promises is about the caller's own standing, not about the lock being
      unclaimed by everybody: a compatible claim another party holds on the same
      lock is untouched by this caller's release and is none of this helper's
      business, so "released" means "this caller has let go", not "nobody holds
      it". Because a release of a held claim is always answered, this helper must
      report back UNCONDITIONALLY: it may not implement dropping a claim by way
      of an operation that another holder could leave pending, which would turn a
      guaranteed answer into an indefinite wait.

The low-level primitive is an unchanged library callee; it is axiomatized as a
contract-only function whose normal-completion value is THE EMPTY VALUE ITSELF,
carried as the empty value of the model language rather than as a stand-in
number, and whose refusal signal is a user-defined exception (a builtin
exception in an ``Exsures`` crashes the Nagini translator). Carrying it as the
genuine empty value is deliberate and is the point of this part of the model: a
stand-in number would be a STRICTLY STRONGER claim about the callee than the
callee makes, and stronger in the one direction that matters. Every number
answers questions the empty value refuses — is it zero, is it negative, does it
count as "set" — so a body handed a number can read a definite answer off it and
present that answer as the outcome, while the same body handed the real empty
value has nothing to read. The two therefore disagree precisely where the
reported boolean is decided, which is why the value is modelled as empty and why
no obligation here pins it to any number. Whether the request is granted is the
abstract discriminating datum the helper must reflect, and it is observable ONLY
as control flow.

The helpers' promise is therefore not only the reported boolean but the
WORLD STATE that boolean describes. That state is invisible to a plain value
abstraction — a helper that merely returns the right boolean without ever
touching the primitive, or one that touches it and then undoes the effect,
returns the very same value. It is modelled here as an explicit, SINGLE-VALUED
abstract observable: ``lock_state()`` is an opaque `@ContractOnly @Predicate`
with NO body that frames the abstract lock world, and ``holds_lock()`` is a
contract-only pure observation of that world — "does THIS CALLER hold the lock it
requested, right now". Two things about WHOSE standing it reports are
load-bearing, because the whole divergence between a faithful and an over-strong
reading lives here. It is indexed to the CALLER: it says whether the party that
invoked the helper has the claim, and it is silent about compatible claims other
parties may hold on the same lock at the same time — those are neither created
nor destroyed by this caller's operations, so an obligation about this caller's
standing is not an assertion that the lock is unclaimed by everybody. And it is
indexed to the lock THIS REQUEST NAMED: it reports on the standing the request
was about, not on some other claim the caller may separately hold. An
observation confers KNOWLEDGE, not POWER: consulting it can tell a
body how the world already stands, but consulting it never MOVES the world, so an
obligation about the state at a return point is still dischargeable only by
performing the operation that moves the state there. The two primitives are the only operations that MOVE this caller's standing, and
each pins it in BOTH directions: a granted acquisition leaves this caller holding
the requested lock, a release leaves this caller not holding it. Because the
observable is single-valued at
each program state rather than an accumulating record of things that once
happened, the state a helper leaves behind at its return point is fully
determined by which primitive it invoked LAST — so the helpers' obligations
below constrain the world the caller actually receives, and neither a helper
that never performs the operation nor a helper that performs it and then
reverses it can discharge them (directive-8 / control-flow grounding: the
claim is tied to the effect-producing step and to the state at exit, not to a
copyable value). ``lock_state()`` is a framing resource, not a domain
restriction: it is threaded unchanged through every operation and constrains no
input value, so every boolean input remains admissible.

Total correctness: each helper is a bounded, loop-free wrapper around one
primitive invocation and must actually ANSWER (return its boolean or, for the
primitive, signal out of band). Nagini checks partial correctness by default —
a diverging body would satisfy every postcondition vacuously while never
delivering the report its caller waits on — so every function carries a
``MustTerminate`` obligation (with strictly smaller measures for the callees)
to reject non-terminating implementations.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class LockUnavailable(Exception):
    """Out-of-band signal that the requested lock could not be acquired (the
    refusal path of the low-level primitive, e.g. a non-blocking request for a
    lock another holder owns). User-defined stand-in for the operating-system
    error the primitive raises (a builtin exception in an ``Exsures`` crashes
    the Nagini translator; mapping.md §2)."""
    pass


# axioms-start
# THE EMPTY VALUE. A normal completion of either primitive yields the model
# language's own empty value, and the axioms below say exactly that and nothing
# more. There is deliberately no numeric sentinel here: the obligation is that
# the value is EMPTY, not that it equals some particular number. That is the
# weakest claim about the value that is true of the real callee, and it is also
# the claim that leaves the value uninformative, which is the behaviour being
# specified. A number would answer questions the empty value does not answer at
# all -- ordering, arithmetic, whether it counts as "set" -- and a body could
# then decide the outcome it reports by asking the value one of those questions
# instead of by observing the control flow. Because the value is empty, those
# questions are not merely unhelpful, they are not askable of it, so the outcome
# cannot be derived from the value by any route.


# The abstract LOCK WORLD the two primitives operate on: an opaque
# `@ContractOnly @Predicate` with NO body, threaded unchanged through every
# operation. It is a FRAMING resource (it is what makes the state observation
# below well-defined and lets the verifier know a primitive call may move that
# state); it restricts no input value, so every boolean input to the helper
# remains admissible. Nothing can `Fold` it into existence, so it can only be
# obtained from a caller. Provenance: mapping.md §3.3.
@ContractOnly
@Predicate
def lock_state() -> bool:
    pass


# The abstract STATE OBSERVABLE of that world, at the program point where it is
# read: TRUE iff THIS CALLER holds the lock IT REQUESTED, right now. Both
# indices matter. It is the CALLER's standing, not a census of the lock: a
# compatible claim some other party holds on the same lock at the same time is
# not this caller's and is not reported here, since this caller's operations
# neither create nor destroy it. And it is the standing in the lock THIS REQUEST
# NAMED, not in some other claim the caller may separately hold. It is a
# contract-only pure observation (usable in contracts, never callable from an
# implementation, so no implementation can compute or echo it) and it is
# SINGLE-VALUED at each state: the two primitives below pin it in both
# directions, so it records what this caller's standing currently IS, not merely
# which operations once ran. That is what lets a postcondition speak about the
# standing a helper hands back AT ITS RETURN POINT.
# Provenance + executable soundness check: mapping.md / axiom_check.py.
@Pure
@ContractOnly
def holds_lock() -> bool:
    Requires(lock_state())


# The EXPENDABLE CAPABILITY to make ONE acquisition request that the world will
# ANSWER — grant, or refuse out of band — rather than leave PENDING, and will
# settle outright rather than decide against an unresolved rival claim (module
# docstring, SCOPE). Only an acquisition can be left pending at all, so only an
# acquisition needs this standing.
#
# It is a RESOURCE, not a proposition: an opaque `@ContractOnly @Predicate` with
# NO body. That choice is load-bearing and behavioural, not stylistic. A
# proposition is something a body could interrogate — it could ask whether the
# standing happens to hold and proceed on the strength of the answer — which
# would let any body help itself to an entitlement nobody granted it. A resource
# can only be RECEIVED and SPENT: there is nothing to interrogate, no way to
# conjure it (nothing establishes it, and it has no body to unfold), and no way
# to duplicate it. The acquisition primitive below CONSUMES it and does not hand
# it back, so it authorises exactly one answered acquisition and is then gone.
#
# The distribution of the capability is the model's statement of the two
# operations' asymmetry: the ACQUISITION helper receives one and spends it on the
# single acquisition it reports on; the RELEASE helper and the release primitive
# receive none, because a release of a held lock is answered unconditionally.
# A release body consequently cannot pay for an acquisition step at all, which is
# the intended behavioural reading — a caller asking to drop a lock it holds must
# not be made to wait for a lock instead. Provenance: mapping.md §3.2b.
@ContractOnly
@Predicate
def answerable_acquisition() -> bool:
    pass


@ContractOnly
def primitive_lock(available: bool) -> Optional[int]:
    """Unchanged low-level locking primitive. Signals its outcome by control
    flow: on a normal completion (the request was granted) it yields the
    empty-value sentinel; on a refusal (the lock was not available) it does not
    complete normally but raises. Provenance + executable soundness check:
    mapping.md / axiom_check.py.

    ``available`` is the abstract world-state datum: whether the requested lock
    operation is granted rather than refused out of band. It is not a value the
    caller inspects directly; the caller observes ONLY whether this primitive
    completed normally or raised. Both of those are ANSWERS, and this contract
    describes exactly the answered requests (module docstring, SCOPE): it does
    not claim that every conceivable request is answered, only that an answered
    one takes one of these two forms, and that such a request is settled
    outright, so a refusal is a non-event.

    Making this request SPENDS the caller's standing to have an acquisition
    answered: the capability is taken and not returned, so one authorisation buys
    exactly one answered acquisition."""
    # pre-conditions-start
    # Terminates: on an answered request (the modelled scope) this is one
    # bounded kernel-level operation that delivers its answer — it completes
    # normally or raises. Measure 2 — strictly smaller than either helper's
    # measure, so a helper may invoke it without leaking the obligation.
    Requires(MustTerminate(2))
    # Operates on the abstract lock world (framing; the operation may move the
    # state observation below).
    Requires(lock_state())
    # ANSWERABILITY, SPENT HERE. This operation delivers one of the two answers
    # below only for a request the world answers and settles outright; a request
    # left pending, or decided against an unresolved rival claim, is neither of
    # the two answered forms. An acquisition is precisely the operation that CAN
    # be left pending (another holder may keep it waiting indefinitely), so this
    # obligation is what confines the two-answer contract below — including the
    # refusal case's non-event guarantee — to the requests it truly describes.
    #
    # The capability is CONSUMED and is NOT re-established by any postcondition
    # below, which is what makes one authorisation buy exactly ONE answered
    # acquisition. A caller can only spend what it was handed: the acquisition
    # helper is handed one, the release helper is handed none because a release
    # needs none, and nothing can create or interrogate one.
    Requires(answerable_acquisition())
    # pre-conditions-end
    # post-conditions-start
    # The world is handed back to the caller on BOTH exits.
    Ensures(lock_state())
    # A normal completion is reachable ONLY when the request was granted, and it
    # yields the empty-value sentinel (which is not the integer zero).
    Ensures(available is True)
    # THE VALUE IS EMPTY. A granted request hands back the empty value, which is
    # the whole of what this operation reports by value: nothing. Deliberately no
    # numeric fact is claimed -- not an exact number, and not even the weaker
    # "differs from zero" -- because the real operation hands back no number at
    # all, and any numeric fact would be a claim the operation does not make.
    # Stating emptiness instead is what makes the value USELESS for deciding the
    # outcome: an empty value cannot be ordered, cannot enter arithmetic, and
    # does not answer whether it is "set", so a body cannot read granted-or-
    # refused off it and must observe the control flow instead, which is where
    # the outcome actually is.
    Ensures(Result() is None)
    # STATE, first direction: a granted acquisition leaves THIS CALLER HOLDING
    # the lock it requested. This is the acquisition's real world effect,
    # recorded as the caller's own standing rather than as an accumulating fact,
    # so a later release by this caller genuinely UNDOES it.
    Ensures(holds_lock())
    # A refusal (the lock was not available) is signalled out of band, on
    # EXACTLY the unavailable case; the world is handed back. The refusal does not
    # move THIS CALLER'S STANDING IN THE REQUESTED LOCK: a request that was
    # refused did not obtain that lock, and did not cost a claim on that same lock
    # the caller already had. Scoped deliberately to the requested lock — a
    # refused request that would have superseded a DIFFERENT earlier claim of the
    # caller's own is not promised to reinstate it, so nothing wider is asserted.
    Exsures(LockUnavailable, lock_state() and available is False and holds_lock() == Old(holds_lock()))
    # post-conditions-end


@ContractOnly
def primitive_release() -> Optional[int]:
    """Unchanged low-level primitive used to RELEASE a lock the caller already
    holds. A release the caller is entitled to make completes normally and
    yields the empty-value sentinel; it does not signal a refusal. Provenance
    + executable soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # Terminates: one bounded kernel-level operation that completes — a release
    # the caller is entitled to make is never left pending. Measure 6 — strictly
    # smaller than the release helper's measure, so the helper may invoke it
    # without leaking the obligation.
    Requires(MustTerminate(6))
    # Operates on the abstract lock world (framing).
    Requires(lock_state())
    # Deliberately NO answerability capability is required or produced here:
    # unlike an acquisition, a release of a lock the caller holds has nobody to
    # wait for and is always answered, so it needs no standing to be answered and
    # it does not confer any. That is why the release helper needs none, and why a
    # release body has nothing with which to pay for an acquisition step.
    # pre-conditions-end
    # post-conditions-start
    Ensures(lock_state())
    # THE VALUE IS EMPTY, exactly as for the acquisition: a completed release
    # reports nothing by value. The same reasoning applies and applies
    # independently here -- this operation's outcome, too, is carried by the fact
    # that it completed and not by anything a caller could extract from what it
    # returned.
    Ensures(Result() is None)
    # STATE, second direction: after this operation THIS CALLER no longer holds
    # the lock. It asserts only that this caller has let go — a compatible claim
    # another party holds on the same lock is untouched by this operation and is
    # not asserted away here. Together with the acquisition clause above this
    # makes the observable single-valued and REVERSIBLE, so the standing at any
    # program point reflects the operation performed LAST rather than every
    # operation ever performed.
    Ensures(holds_lock() is False)
    # post-conditions-end
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required beyond the state observation in
#  the axioms region: the helpers' decision is the faithful translation of the
#  primitive's control-flow signal, stated inline.)
# pure-end


def acquire(available: bool) -> bool:
    # pre-conditions-start
    # ``available`` is the abstract world-state: whether the requested lock
    # operation is granted rather than refused out of band. A plain boolean;
    # BOTH values are admissible and nothing constrains it.
    # TERMINATION: the helper is one bounded primitive invocation plus a
    # constant-time translation of its answer and MUST actually deliver its
    # boolean whenever the request is answered (total correctness, over the
    # modelled scope). Under partial-correctness semantics a
    # diverging body (e.g. an endless loop before the return) satisfies every
    # Ensures clause only vacuously yet never reports to the caller waiting to
    # learn whether it holds the lock; the real helper always answers. Measure
    # 10: the impl may invoke the smaller-measure primitives but may NOT
    # re-invoke itself.
    Requires(MustTerminate(10))
    # FRAMING (not a domain restriction): the helper operates on the abstract
    # lock world, which it hands back unchanged as a resource. Every boolean
    # input remains admissible.
    Requires(lock_state())
    # SCOPE, as ONE EXPENDABLE AUTHORISATION (not a value restriction): the
    # acquisition this helper reports on is one the world answers and settles
    # outright — exactly the domain in which a boolean report is meaningful at
    # all (docstring, SCOPE), and exactly what this helper's own promise to
    # answer is conditioned on. It constrains no value: BOTH booleans remain
    # admissible and both control-flow paths stay live.
    #
    # It is a single expendable capability, so it authorises the ONE acquisition
    # request whose outcome this helper reports and no more — a body that issues
    # repeated acquisition requests for the lock is claiming standing it was
    # never handed, since the caller asked for one lock and is owed one answer.
    # It is stated here because this helper is the one whose operation can be
    # left pending; the release helper carries no such capability, so the
    # asymmetry between the two promises is visible in the contract rather than
    # assumed.
    Requires(answerable_acquisition())
    # pre-conditions-end
    # post-conditions-start
    Ensures(lock_state())
    # VALUE: the helper reports the outcome FAITHFULLY: TRUE exactly when the
    # request was granted (the primitive completed the acquisition normally),
    # FALSE exactly when it was not (the primitive signalled a refusal). This is
    # the discriminating obligation: a normal completion must be reported as
    # TRUE, never as FALSE. No Exsures clause => the helper never propagates the
    # primitive's refusal signal; it absorbs it into the FALSE result.
    Ensures(Result() == available)
    # STATE AT THE RETURN POINT: when the helper reports a successful
    # acquisition, THIS CALLER must actually hold the requested lock at the moment
    # it returns — that is the standing the caller is promised and goes on to rely
    # on. Because
    # the observation is single-valued and the release operation drives it back
    # to FALSE, this obligation is discharged only by a body whose LAST
    # state-moving step is the acquisition itself: a helper that never performs
    # the acquisition cannot establish it, and a helper that performs the
    # acquisition and then gives the lock up again before returning TRUE
    # actively falsifies it. (Guarded by `Result() is True`: on the refusal path
    # the helper reports FALSE and promises the caller no lock.)
    Ensures(Implies(Result() is True, holds_lock()))
    # STATE AT THE RETURN POINT, the other half: when the helper reports FAILURE
    # it must have left THIS CALLER'S STANDING IN THE REQUESTED LOCK exactly as it
    # found it. Reporting FALSE is a claim that the caller did not obtain that
    # lock — not licence to change what the caller already had in it. This makes
    # the failure path an obligation too, so a body cannot buy its FALSE report by
    # moving that standing (for instance by giving up the very lock it reports
    # having failed to take).
    Ensures(Implies(Result() is False, holds_lock() == Old(holds_lock())))
    # post-conditions-end
    # impl-start
    try:
        primitive_lock(available)
        return True
    except LockUnavailable:
        return False
    # impl-end


def release() -> bool:
    # pre-conditions-start
    # The caller holds the lock being released; no input values are observed.
    # TERMINATION: one bounded primitive invocation plus a constant-time
    # report; the helper MUST actually deliver its boolean (total
    # correctness). A diverging body would satisfy the Ensures clauses only
    # vacuously; the real helper always answers. Measure 14: the impl may
    # invoke the smaller-measure primitives but may NOT re-invoke itself.
    Requires(MustTerminate(14))
    # FRAMING (not a domain restriction): the helper operates on the abstract
    # lock world, which it hands back as a resource.
    Requires(lock_state())
    # NOTE the deliberate absence of any answerability capability here.
    # Releasing a lock the caller holds is answered unconditionally, so this
    # helper's promise to report back is UNCONDITIONAL — strictly stronger than
    # the acquisition helper's, which is scoped to answered requests. Having been
    # handed no such capability, this helper has nothing with which to pay for an
    # acquisition step, and it cannot obtain one by asking whether it has one:
    # the capability is a resource, so there is no fact to test. A body that
    # performs an operation which can be left pending cannot keep this helper's
    # promise: a caller asking to drop a lock it holds must not be made to wait
    # for a lock.
    # pre-conditions-end
    # post-conditions-start
    Ensures(lock_state())
    # VALUE: releasing a held lock completes normally, so the helper reports
    # TRUE unconditionally (no Exsures clause => it never raises).
    Ensures(Result() is True)
    # STATE AT THE RETURN POINT: when the helper returns, THIS CALLER must NOT
    # hold the lock — the caller is promised that its own claim is gone. It is not
    # promised that the lock is unclaimed by everybody: a compatible claim another
    # party holds on the same lock survives this caller's release untouched, and
    # asserting otherwise would be a claim about parties this helper never acts
    # for. This is unconditional and is discharged only by a body whose LAST
    # state-moving step is the release: a helper that never performs the release
    # cannot establish it, and a helper that releases and then re-takes the lock
    # before returning TRUE actively falsifies it.
    Ensures(holds_lock() is False)
    # post-conditions-end
    # impl-start
    primitive_release()
    return True
    # impl-end
