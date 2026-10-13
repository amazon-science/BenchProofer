"""Twin-artifact model for pallets__flask-5014.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A blueprint object is constructed from a textual *name*. Construction
  validates that name before the object is usable. The name is rejected — the
  constructor signals the caller with a name-validation error instead of
  building the object — in exactly two situations:

    (1) the name is the empty text (no code points at all), and
    (2) the name contains the dot code point U+002E ('.').

  In every other case (a non-empty name with no dot) construction proceeds
  normally. The empty-name rejection is the behaviour pinned here: a name with
  zero code points must raise the validation error rather than yielding a
  usable object.

The name is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The dot-membership predicate is carried by a pure fold over
`PSeq[int]`. The validation error is a user-defined exception class (a builtin
exception in an `Exsures` crashes the translator). The base construction that
runs before name validation is axiomatised as an opaque callee that does not
touch the name: it either completes or fails as a unit before any name check,
so it cannot turn a rejected name into an accepted one or vice versa. WHICH of
the two happens is not a function of that callee's own argument: it also turns
on ambient state the callee reads (and can itself change) and on a further
optional argument of the construction, neither of which this specification
carries. So each exit hands back its own independent WITNESS over the base
callee's argument — `base_init_can_complete` on normal completion,
`base_init_can_fail` on failure-as-a-unit — and neither witness is the negation
of the other. The two exit channels are still pinned: a name rejection can
arise only once the base init has already completed, so it carries the SUCCESS
witness, while the base-init channel demands the FAILURE witness, obtainable
only from a base call that actually failed — so the base-init channel cannot
absorb a name rejection.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NameValidationError(Exception):
    """Signals that the supplied construction name is not acceptable. Stands in
    for the `ValueError` the desired behaviour requires (a builtin exception in
    an `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class BaseInitError(Exception):
    """Signals that the base construction performed before name validation
    failed as a unit. User-defined stand-in for the exception the opaque base
    callee may raise on some inputs (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


# axioms-start
@Pure
@ContractOnly
def base_init_can_complete(import_name: PSeq[int]) -> bool:
    """WITNESS for the base callee's normal-completion channel: the base
    initialisation is able to complete as a unit on this `import_name`. Stated
    over the base callee's OWN argument — it says nothing about, and never
    reads, the blueprint `name`, faithful to the real base init, which is not
    even handed the name. It is deliberately an ATTAINABILITY claim rather than
    a decision procedure: for one `import_name` the real base init can complete
    on one call and fail on another, because it also consults an ambient table
    it may itself populate and an optional root-path argument that skips the
    consultation entirely (mapping.md §3.2). Nothing here says this witness and
    `base_init_can_fail` exclude each other; both can hold for the same
    argument. The proof relies only on where the fact comes FROM — a base call
    that actually completed — never on its truth-value, which is opaque on every
    concrete `import_name` (checked against the real callee by G-AX /
    axiom_check.py). Provenance: mapping.md §3."""
    Ensures(True)


@Pure
@ContractOnly
def base_init_can_fail(import_name: PSeq[int]) -> bool:
    """WITNESS for the base callee's failure-as-a-unit channel: the base
    initialisation is able to fail as a unit on this `import_name`, before any
    name check runs. Same shape as `base_init_can_complete` — an attainability
    claim over the base callee's own argument, silent about the blueprint
    `name`, opaque on every concrete argument, obtainable only from a base call
    that actually failed — and it is NOT the negation of the success witness:
    the real outcome for one `import_name` also turns on ambient state and on
    the optional root-path argument, so the two witnesses can both hold.
    Provenance: mapping.md §3."""
    Ensures(True)


@ContractOnly
def init_base(import_name: List[int]) -> None:
    """The base initialisation performed before the name is validated. It is
    independent of the `name` argument and performs no name validation. It is
    an opaque callee that either completes normally or, on some inputs in some
    ambient states, fails as a unit before any name check runs. Provenance:
    mapping.md §3."""
    Requires(Acc(list_pred(import_name), 1 / 2))
    # Normal completion: hands back the import_name permission together with the
    # SUCCESS witness for this argument — the only way to obtain that witness.
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(import_name), 1 / 2))
    Ensures(base_init_can_complete(ToSeq(import_name)))
    # Failure as a unit: hands back the import_name permission together with the
    # FAILURE witness for this argument — the only way to obtain that one. The
    # two witnesses are independent, so a call that ended one way says nothing
    # about how a different call ends: this contract is not stronger than a
    # callee whose outcome also depends on state and on arguments the model does
    # not carry.
    Exsures(BaseInitError,
            Acc(list_pred(import_name), 1 / 2)
            and base_init_can_fail(ToSeq(import_name)))
# axioms-end


# pure-start
@Pure
def contains_dot(s: PSeq[int]) -> bool:
    """True iff the sequence contains the dot code point U+002E (46).
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == 46 or contains_dot(s.drop(1))
# pure-end


def validate_name(name: List[int], import_name: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(import_name), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs: returned at the same fractional permission they were
    # required at (directive 5) — the validator mutates nothing observable.
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(import_name), 1 / 2))
    # Normal return is reachable ONLY for an accepted name: non-empty AND
    # dot-free. (An empty name must NOT return normally — it must raise.) A
    # normal return also carries the base callee's SUCCESS witness, so it is
    # reachable only once the base init has actually completed.
    Ensures(len(name) > 0)
    Ensures(not contains_dot(ToSeq(name)))
    Ensures(base_init_can_complete(ToSeq(import_name)))
    # The validation error is raised on EXACTLY the rejected names: empty, or
    # containing a dot — AND only once the base init has already COMPLETED (the
    # name guards run strictly after `init_base` returns). So a name rejection
    # carries the base callee's SUCCESS witness. This pins the reject set to
    # THIS channel: the base-init channel below demands the FAILURE witness,
    # which is obtainable only from a base call that actually failed and never
    # from one that returned, so a name rejection cannot be routed through it.
    # The read-only inputs are held at their fractional permission in the
    # exceptional post-state too (so the value constraint can mention
    # `name`/`import_name`).
    Exsures(NameValidationError,
            Acc(list_pred(name), 1 / 2) and Acc(list_pred(import_name), 1 / 2)
            and base_init_can_complete(ToSeq(import_name))
            and (len(name) == 0 or contains_dot(ToSeq(name))))
    # The base construction runs first and may fail as a unit; that failure
    # aborts construction BEFORE any name check, so it propagates unchanged and
    # says nothing about the name (no len/dot constraint). It carries the base
    # callee's FAILURE witness for `import_name` — the fact only a base call
    # that failed hands out — which is what keeps this channel from absorbing a
    # name rejection. It is NOT the negation of the success witness the other
    # two channels carry: both witnesses may hold for one `import_name`, which
    # is what the real callee does when ambient state or the optional root-path
    # argument decides the outcome. The read-only input permissions are returned
    # so the value side is well-formed.
    Exsures(BaseInitError,
            Acc(list_pred(name), 1 / 2) and Acc(list_pred(import_name), 1 / 2)
            and base_init_can_fail(ToSeq(import_name)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: the constructor as it stood before the change — it
    # validates only the dot, never the empty name. An empty, dot-free name
    # falls through to a normal return, violating Ensures(len(name) > 0). This
    # module MUST FAIL verification (G-DIFF).
    init_base(import_name)
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return
    # impl-end
