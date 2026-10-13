"""Twin-artifact model for django__django-11451.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A credential-checking authentication routine is handed an identifier and a
  secret, either of which may be absent. The routine answers with the matching
  account when (and only when) it can establish one, and otherwise with nothing.
  Establishing an account costs two observable, externally-expensive
  operations: a directory lookup (a database round trip) and one invocation of
  the secret-verification primitive (a deliberately costly hash). The
  verification primitive is run once whenever both credentials are present —
  regardless of whether the identifier is recognised — so that the response
  time of an unrecognised identifier is indistinguishable from a recognised
  one.

  The behaviour required of the routine:

    (1) When EITHER the identifier OR the secret is absent, the routine
        answers with nothing AND performs neither expensive operation: the
        directory is not consulted and the verification primitive is not run.
        (The caller offered credentials shaped for some other checker; this
        checker has nothing to contribute and must not spend the cost.)

    (2) When BOTH are present, the directory is consulted exactly once and the
        verification primitive is run exactly once. If the directory recognises
        the identifier and the secret verifies for an account that is permitted
        to authenticate, the routine answers with that recognised account
        (exactly the account carrying that identifier); otherwise it answers
        with nothing.

  An absent identifier may first be recovered from a side channel of extra
  keyword arguments; only if it is still absent after that does clause (1)
  apply.

The identifier and the secret are modelled as ``Optional[int]`` (absent is
``None``; present is an opaque code). The checker carries two non-negative
counters recording how many times each expensive operation has run, so the
"performs neither expensive operation" guarantee is stated exactly. The
directory's recognition test and the secret verification are unchanged opaque
primitives, axiomatized as pure decisions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def directory_recognises(identifier: int) -> bool:
    """The unchanged directory-lookup decision: whether an account with this
    natural identifier exists. A pure decision over the current directory; it
    has no side effects of its own — the cost of consulting the directory is
    accounted for separately by the checker's lookup counter. Provenance +
    executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def secret_verifies(identifier: int, secret: int) -> bool:
    """The unchanged secret-verification-and-permission decision for a
    recognised account: whether the supplied secret matches the stored secret
    AND the account is permitted to authenticate. A pure decision; the cost of
    the verification primitive is accounted for separately by the checker's
    verification counter. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


class Checker:
    def __init__(self) -> None:
        # Level 1: the constructor is straight-line (two field stores, no loop
        # and no obligated callee), so it needs no room beneath itself. Being
        # obligated at all is what leaves level 6 in authenticate room to
        # construct a Checker without an obligation leak.
        Requires(MustTerminate(1))
        Ensures(Acc(self.lookups) and self.lookups == 0)  # type: ignore
        Ensures(Acc(self.verifications) and self.verifications == 0)  # type: ignore
        self.lookups = 0  # type: int
        self.verifications = 0  # type: int


def authenticate(self: Checker, identifier: Optional[int], secret: Optional[int],
                 fallback_identifier: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(self.lookups) and Acc(self.verifications))
    Requires(self.lookups >= 0 and self.verifications >= 0)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.lookups) and Acc(self.verifications))
    # (1) Either credential absent (after recovery) => answer nothing, and
    #     NEITHER expensive operation runs (both counters unchanged).
    Ensures(Implies((identifier is None and fallback_identifier is None) or secret is None,
                    Result() is None
                    and self.lookups == Old(self.lookups)
                    and self.verifications == Old(self.verifications)))
    # (2) Both present => the directory is consulted exactly once AND the
    #     verification primitive is run exactly once (on every both-present
    #     path: recognised-correct, recognised-wrong, and unrecognised alike).
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None,
                    self.lookups == Old(self.lookups) + 1
                    and self.verifications == Old(self.verifications) + 1))
    # (2a) Recognised => answer that account iff the secret verifies, and the
    #      answer is exactly the recognised account (the one carrying that
    #      identifier); otherwise nothing.
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None
                    and directory_recognises(identifier if identifier is not None else fallback_identifier),  # type: ignore
                    ((Result() is not None) ==
                        secret_verifies(identifier if identifier is not None else fallback_identifier, secret))  # type: ignore
                    and Implies(Result() is not None,
                                Result() == (identifier if identifier is not None else fallback_identifier))))
    # (2b) Unrecognised => answer nothing.
    Ensures(Implies((identifier is not None or fallback_identifier is not None) and secret is not None
                    and not directory_recognises(identifier if identifier is not None else fallback_identifier),  # type: ignore
                    Result() is None))
    # post-conditions-end
    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    # The verification primitive runs exactly once on every both-present path:
    # on the recognised path it is the secret check; on the unrecognised path
    # it is the timing-defence invocation.
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff
        return None
    # impl-end
