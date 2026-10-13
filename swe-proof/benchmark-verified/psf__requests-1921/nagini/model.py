"""Twin-artifact model for psf__requests-1921.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two collections of per-key settings are combined into one effective
  collection for a single use. The per-request collection takes precedence over
  the standing per-session collection: where both provide a key, the
  per-request value wins; where only one provides it, that one is used.

  A key may be given the distinguished "unset" value to mean "do not carry this
  key into the effective collection at all". The behaviour that matters: a key
  whose EFFECTIVE value (after precedence) is the unset value must be ABSENT
  from the combined collection -- regardless of WHICH side contributed that
  unset value. In particular a key carried only by the standing per-session
  collection and given the unset value there (never mentioned by the per-request
  collection) must be dropped, not carried through still holding the unset
  value. Every key whose effective value is a real (non-unset) value is carried
  through with exactly that value.

  Consequently the combined collection contains no key mapping to the unset
  value: looking up any key either yields a real value or finds the key absent.

  Combining always COMPLETES: for every admissible pair of collections the
  combination delivers the collection described above after finitely many
  steps. A computation that never delivers one has not met the guarantees --
  they are claims about a result that is actually produced.

Modelling choices (Nagini fragment):
  * Each collection is modelled as a ``List[int]`` indexed by key position: the
    universe of keys is the index set ``0 .. n-1``, common to both inputs and
    the output, and position ``k`` carries the value held for key ``k``. Only
    membership ("is key k carried, and with what value") is observed, so integer
    identity is the faithful carrier (mapping.md S2); string keys are irrelevant
    to the tested behaviour and are banned from indexing in Nagini anyway.
  * Two distinguished values: ``ABSENT`` means "key not carried by this
    collection / dropped from the result", and ``NONE_VAL`` means "the explicit
    unset value a caller may store under a key". Any other (real) value is an
    ordinary setting. ``NONE_VAL`` is modelled as a value distinct from
    ``ABSENT`` precisely so that a key explicitly set to the unset value is
    distinguishable from a key that was simply never provided -- the
    distinction the behaviour under specification turns on.
  * The two inputs are read only (held at fractional permission, required and
    ensured); the output collection is freshly built and fully owned. No string
    indexing is used (Nagini bans it).
  * Delivery of a result is an obligation of the contract, not an assumption:
    the method carries ``MustTerminate``, so the postconditions are guarantees
    about a collection that is handed back. The decreasing measure that
    discharges it for THIS body lives in the (elided) impl region, so any other
    implementation supplies whatever measure its own control flow needs.

The behaviour is modelled deeply (the precedence merge and the unset-value drop
are spelled out in the impl region); there is no axiomatised callee. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: combining two key/value collections with precedence and dropping
# keys whose effective value is the unset value is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def absent() -> int:
    # The distinguished value meaning "key not carried by this collection" (an
    # input position) / "key dropped from the combined collection" (an output
    # position): a lookup finds the key absent.
    return 0


@Pure
def none_val() -> int:
    # The distinguished explicit "unset" value a caller may store under a key.
    # A key whose effective value is this must be dropped from the result.
    return -1


@Pure
def effective(sv: int, rv: int) -> int:
    # The effective value for a key before the unset-drop: the per-request value
    # wins where the per-request collection carries the key (rv != absent()),
    # otherwise the standing per-session value is used.
    if rv != absent():
        return rv
    return sv


@Pure
def combined(sv: int, rv: int) -> int:
    # The value the combined collection holds for a key: the effective value,
    # except that an effective value equal to the unset value drops the key
    # (it becomes absent). This is the per-key behaviour the result must realise.
    if effective(sv, rv) == none_val():
        return absent()
    return effective(sv, rv)
# pure-end


def effective_collection(session: List[int], request: List[int],
                         n: int) -> List[int]:
    # pre-conditions-start
    # The two input collections are read only: fractional permission.
    Requires(Acc(list_pred(session), 1 / 2))
    Requires(Acc(list_pred(request), 1 / 2))
    # The shared key universe is positions 0 .. n-1.
    Requires(0 <= n and n <= len(session) and n <= len(request))
    # Combining is obliged to COMPLETE and hand back a collection: on every
    # admissible input the guarantees below are owed about a result that is
    # actually delivered, so a computation that never delivers one does not
    # satisfy them. (MustTerminate in a Requires transfers the obligation TO
    # this operation; it does not shrink the set of admissible inputs.)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Inputs unchanged (returned at the same fractional permission).
    Ensures(Acc(list_pred(session), 1 / 2))
    Ensures(Acc(list_pred(request), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The combined collection spans the same key universe.
    Ensures(len(Result()) == n)
    # The key universe still fits inside both inputs (carried so the per-key
    # reads below are in bounds).
    Ensures(n <= len(session) and n <= len(request))
    # (1) Faithful precedence-merge-and-drop: position k of the result is the
    #     per-key combined value -- the per-request value where present else the
    #     per-session value, dropped to absent when that effective value is the
    #     unset value.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < n and
        k < len(session) and k < len(request),
        Result()[k] == combined(session[k], request[k])),
        [[Result()[k]]])))
    # (2) The headline guarantee: no key in the combined collection maps to the
    #     unset value -- every lookup yields a real value or finds the key
    #     absent. This is the clause a drop that only inspects the per-request
    #     side (leaving a session-side unset value in place) violates.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < n,
        Result()[k] != none_val()),
        [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(session), 1 / 2))
        Invariant(Acc(list_pred(request), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n <= len(session) and n <= len(request))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and
            k < len(session) and k < len(request),
            result[k] == combined(session[k], request[k])),
            [[result[k]]])))
        # One key of the universe is settled per step, so the number of keys
        # still to settle strictly decreases: this body's measure for the
        # delivery obligation the contract states.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        sv = session[i]
        rv = request[i]
        # Precedence: the per-request value wins where the per-request
        # collection carries the key, else the per-session value.
        if rv != absent():
            ev = rv
        else:
            ev = sv
        Assert(ev == effective(sv, rv))
        # Drop the key (absent) when its effective value is the unset value,
        # regardless of which side contributed it; otherwise carry it through.
        if ev == none_val():
            val = absent()
        else:
            val = ev
        Assert(val == combined(sv, rv))
        old_result = result
        result = result + [val]
        Assert(len(result) == len(old_result) + 1)
        Assert(result[i] == val)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old_result),
            result[k] == old_result[k]), [[result[k]]])))
        i = i + 1
    return result
    # impl-end
