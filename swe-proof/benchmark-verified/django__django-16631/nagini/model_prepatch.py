"""Twin-artifact model for django__django-16631.

Behaviour under specification (stated as the desired observable behaviour of a
session-authentication check, not as an edit):

A request carries a stored session authentication token. The server holds a
current verification token for the user (an HMAC of the user's password under
the active signing secret) and, during a secret-rotation window, a sequence of
previous verification tokens (the same HMAC under each previous signing secret).
The check decides, from the stored token alone, one of three outcomes:

  * outcome 1 -- ACCEPT-CURRENT: the stored token is present and equals the
    current verification token. The user stays authenticated and the stored
    session is left untouched.

  * outcome 2 -- ACCEPT-PREVIOUS: the stored token is present, does NOT equal
    the current verification token, but equals one of the previous verification
    tokens. The user stays authenticated.

  * outcome 0 -- REJECT: the stored token is absent, or present but matching
    neither the current nor any previous verification token. The session is
    discarded and the user is de-authenticated.

The current outcome takes priority over the previous outcomes: if the stored
token equals the current token the result is 1 even if it also coincides with a
previous token.

The per-secret verification token itself is a keyed hash of the password; for
any given password the token is a deterministic function of the signing secret
(`token_for_secret`, an axiomatised unchanged callee). The previous-token
sequence is exactly that token computed under each previous secret, in order.

Tokens are modelled as `List[int]` / `PSeq[int]` of code points (Nagini bans
`str` indexing). An empty token models an absent stored session value. The
sequence of previous tokens is `PSeq[PSeq[int]]`; secrets and passwords are
`PSeq[int]`. `matches_any` is the front-recursive membership predicate.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def token_for_secret(password: PSeq[int], secret: PSeq[int]) -> PSeq[int]:
    """The per-secret verification token: a keyed hash of `password` under
    `secret`. Unchanged callee (the keyed-hash primitive). The only property
    the proof consumes is functional determinism -- equal (password, secret)
    pairs yield equal tokens -- which holds for any deterministic hash and is
    implied automatically by purity. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def matches_any(token: PSeq[int], candidates: PSeq[PSeq[int]]) -> bool:
    """True iff `token` equals some element of `candidates`. Front-recursive so
    a single unfold is available per loop step."""
    if len(candidates) == 0:
        return False
    return candidates[0] == token or matches_any(token, candidates.drop(1))


@Pure
def tokens_under(password: PSeq[int], secrets: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The verification tokens for `password` under each secret in `secrets`,
    in order. Front-recursive fold mirroring the previous-token generator."""
    if len(secrets) == 0:
        return PSeq(PSeq(0)).take(0)
    return PSeq(token_for_secret(password, secrets[0])) + tokens_under(password, secrets.drop(1))
# pure-end


def session_outcome(session_token: List[int],
                    current_token: List[int],
                    previous_tokens: PSeq[PSeq[int]]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(session_token), 1 / 2))
    Requires(Acc(list_pred(current_token), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(session_token), 1 / 2))
    Ensures(Acc(list_pred(current_token), 1 / 2))
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # ACCEPT-CURRENT: present stored token equal to the current token.
    Ensures((Result() == 1) ==
            (len(session_token) > 0
             and ToSeq(session_token) == ToSeq(current_token)))
    # ACCEPT-PREVIOUS: present stored token that does not match the current
    # token but does match one of the previous tokens.
    Ensures((Result() == 2) ==
            (len(session_token) > 0
             and ToSeq(session_token) != ToSeq(current_token)
             and matches_any(ToSeq(session_token), previous_tokens)))
    # REJECT: everything else (absent, or matching neither).
    Ensures((Result() == 0) ==
            (len(session_token) == 0
             or (ToSeq(session_token) != ToSeq(current_token)
                 and not matches_any(ToSeq(session_token), previous_tokens))))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the stored token is verified only against the current
    # verification token; if that fails the session is discarded outright. The
    # previous-token sequence is never consulted, so the upgrade outcome (2) is
    # never produced -- a rotated session that matches a previous secret is
    # wrongly rejected.
    if len(session_token) == 0:
        return 0
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    return 0
    # impl-end


def fallback_auth_hashes(password: List[int],
                         default_secret: List[int],
                         fallback_secrets: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(password), 1 / 2))
    Requires(Acc(list_pred(default_secret), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(password), 1 / 2))
    Ensures(Acc(list_pred(default_secret), 1 / 2))
    # The produced sequence is exactly the verification token computed under
    # each PREVIOUS secret, in order -- each entry keyed by its own previous
    # secret, NOT by the active signing secret.
    Ensures(Result() == tokens_under(ToSeq(password), fallback_secrets))
    # post-conditions-end
    # impl-start
    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        result = PSeq(token_for_secret(ToSeq(password), s)) + result
        i = i - 1
    return result
    # impl-end
